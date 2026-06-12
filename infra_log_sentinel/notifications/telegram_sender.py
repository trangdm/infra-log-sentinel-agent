from __future__ import annotations

from dataclasses import dataclass
from html import escape
import time

import requests
from requests import Response
from requests import exceptions as requests_exceptions

from infra_log_sentinel.analysis.runbook import recommend_commands
from infra_log_sentinel.config import Settings
from infra_log_sentinel.models import LogEvent
from infra_log_sentinel.state.alert_store import AlertRecord, AlertStore, build_alert_id


TELEGRAM_API_BASE = "https://api.telegram.org"
TELEGRAM_TIMEOUT = (10, 45)
TELEGRAM_RETRIES = 2
PLACEHOLDER_VALUES = {
    "",
    "replace_with_telegram_bot_token",
    "replace_with_telegram_chat_id",
}
SEVERITY_ORDER = {"critical": 0, "error": 1, "warning": 2, "info": 3}
SEVERITY_BADGE = {
    "critical": "🔴 CRITICAL",
    "error": "🟠 ERROR",
    "warning": "🟡 WARNING",
    "info": "🔵 INFO",
}
DOMAIN_BADGE = {
    "network": "🌐 Network",
    "linux": "🐧 Linux",
    "windows": "🪟 Windows",
    "vmware": "🧱 VMware",
}


class TelegramConfigError(ValueError):
    """Raised when required Telegram settings are missing or invalid."""


class TelegramSendError(RuntimeError):
    """Raised when Telegram accepts config but cannot send the message."""


@dataclass(frozen=True)
class TelegramSendResult:
    sent_count: int
    dry_run: bool
    message: str


@dataclass(frozen=True)
class TelegramUpdate:
    update_id: int
    message_date_ts: int
    text: str


@dataclass(frozen=True)
class AckEscalationResult:
    acked_count: int
    escalated_count: int
    pending_count: int
    dry_run: bool
    message: str


def check_telegram_health(settings: Settings) -> str:
    token = settings.telegram_bot_token.strip()
    chat_id = settings.telegram_chat_id.strip()
    config_errors = _config_errors(token, chat_id)
    if config_errors:
        raise TelegramConfigError("Invalid Telegram configuration: " + ", ".join(config_errors))

    response = _telegram_post(
        token=token,
        method="getMe",
        json_payload={},
    )
    if not response.ok:
        raise TelegramSendError(_telegram_error("Telegram getMe failed", response))

    payload = response.json()
    bot = payload.get("result", {})
    username = bot.get("username", "<unknown>")

    response = _telegram_post(
        token=token,
        method="sendMessage",
        json_payload={
            "chat_id": chat_id,
            "text": "✅ Telegram health check OK from Infrastructure Log Sentinel Agent.",
            "disable_web_page_preview": True,
        },
    )
    if not response.ok:
        raise TelegramSendError(_telegram_error("Telegram health message failed", response))

    return f"Telegram health check OK. Bot @{username} can send messages to the configured chat."


def send_telegram_alerts(
    settings: Settings,
    events: list[LogEvent],
    dry_run: bool = False,
    max_alerts: int | None = None,
    alert_store: AlertStore | None = None,
) -> TelegramSendResult:
    token = settings.telegram_bot_token.strip()
    chat_id = settings.telegram_chat_id.strip()
    config_errors = _config_errors(token, chat_id)
    if config_errors and not dry_run:
        raise TelegramConfigError("Invalid Telegram configuration: " + ", ".join(config_errors))

    alert_events = select_alert_events(events, settings.severity_alert_levels)
    if max_alerts is not None:
        alert_events = alert_events[:max_alerts]

    if dry_run:
        preview = "\n\n".join(
            format_alert_message(event, index, len(alert_events), build_alert_id(event))
            for index, event in enumerate(alert_events[:3], start=1)
        )
        warning_text = f" Config warnings: {', '.join(config_errors)}." if config_errors else ""
        return TelegramSendResult(
            sent_count=0,
            dry_run=True,
            message=(
                f"Telegram dry run OK. Would send {len(alert_events)} alert message(s)."
                f"{warning_text}\n\nPreview:\n{preview}"
            ),
        )

    sent_count = 0
    skipped_count = 0
    for index, event in enumerate(alert_events, start=1):
        alert_id = build_alert_id(event)
        if alert_store is not None and alert_store.get_alert_status(alert_id) is not None:
            skipped_count += 1
            continue
        message_id = _send_message(
            token=token,
            chat_id=chat_id,
            text=format_alert_message(event, index, len(alert_events), alert_id),
        )
        if alert_store is not None:
            sent_at_ts = int(time.time())
            alert_store.upsert_pending_alert(
                event=event,
                telegram_message_id=message_id,
                sent_at_ts=sent_at_ts,
                due_at_ts=sent_at_ts + settings.escalation_timeout_seconds,
            )
        sent_count += 1

    tracking_note = " Tracking pending ACK state." if alert_store is not None else ""
    skipped_note = f" Skipped {skipped_count} previously tracked alert(s)." if skipped_count else ""
    return TelegramSendResult(
        sent_count=sent_count,
        dry_run=False,
        message=(
            f"Telegram alert delivery complete. Sent {sent_count} alert message(s)."
            f"{skipped_note}{tracking_note}"
        ),
    )


def check_ack_and_escalations(
    settings: Settings,
    alert_store: AlertStore,
    dry_run: bool = False,
    max_escalations: int | None = None,
    force_escalate: bool = False,
) -> AckEscalationResult:
    token = settings.telegram_bot_token.strip()
    chat_id = settings.telegram_chat_id.strip()
    config_errors = _config_errors(token, chat_id)
    if config_errors and not dry_run:
        raise TelegramConfigError("Invalid Telegram configuration: " + ", ".join(config_errors))

    pending_alerts = alert_store.list_pending_alerts()
    if not pending_alerts:
        return AckEscalationResult(
            acked_count=0,
            escalated_count=0,
            pending_count=0,
            dry_run=dry_run,
            message="No pending alerts found.",
        )

    last_update_id = alert_store.get_last_update_id()
    updates = _fetch_updates(
        token=token,
        chat_id=chat_id,
        offset=None if last_update_id is None else last_update_id + 1,
    )

    pending_by_id = {alert.alert_id: alert for alert in pending_alerts}
    acked_ids: set[str] = set()
    max_update_id = last_update_id

    for update in updates:
        if max_update_id is None or update.update_id > max_update_id:
            max_update_id = update.update_id
        target_ids = _target_alert_ids_for_ack(update.text, update.message_date_ts, pending_by_id)
        for alert_id in target_ids:
            if alert_id in acked_ids:
                continue
            acked_ids.add(alert_id)
            if not dry_run:
                alert_store.mark_acknowledged(
                    alert_id=alert_id,
                    ack_text=update.text,
                    acked_at_ts=update.message_date_ts,
                    update_id=update.update_id,
                )

    now_ts = int(time.time())
    remaining_pending = (
        [alert for alert in alert_store.list_pending_alerts() if alert.alert_id not in acked_ids]
        if not dry_run
        else [alert for alert in pending_alerts if alert.alert_id not in acked_ids]
    )
    expired_alerts = [
        alert for alert in remaining_pending if force_escalate or alert.due_at_ts <= now_ts
    ]
    if max_escalations is not None:
        expired_alerts = expired_alerts[:max_escalations]

    escalation_preview = ""
    escalated_count = 0
    for alert in expired_alerts:
        escalation_text = format_escalation_message(alert)
        if dry_run:
            if not escalation_preview:
                escalation_preview = f"\n\nEscalation preview:\n{escalation_text}"
        else:
            message_id = _send_message(token=token, chat_id=chat_id, text=escalation_text)
            alert_store.mark_escalated(
                alert_id=alert.alert_id,
                escalated_at_ts=now_ts,
                escalation_message_id=message_id,
            )
        escalated_count += 1

    if max_update_id is not None and not dry_run:
        alert_store.set_last_update_id(max_update_id)

    pending_count = (
        max(0, len(pending_alerts) - len(acked_ids))
        if dry_run
        else max(0, len(pending_alerts) - len(acked_ids) - escalated_count)
    )
    ack_word = "would ACK" if dry_run else "ACKed"
    escalation_word = "would escalate" if dry_run else "escalated"
    return AckEscalationResult(
        acked_count=len(acked_ids),
        escalated_count=escalated_count,
        pending_count=pending_count,
        dry_run=dry_run,
        message=(
            f"ACK/escalation check complete. {ack_word} {len(acked_ids)}, "
            f"{escalation_word} {escalated_count}, still pending {pending_count}."
            f"{escalation_preview}"
        ),
    )


def select_alert_events(events: list[LogEvent], alert_levels: tuple[str, ...]) -> list[LogEvent]:
    alert_set = set(alert_levels)
    return sorted(
        [event for event in events if event.severity in alert_set],
        key=lambda event: (SEVERITY_ORDER.get(event.severity, 99), event.domain, event.source),
    )


def format_alert_message(event: LogEvent, index: int, total: int, alert_id: str) -> str:
    commands = recommend_commands(event)[:3]
    command_lines = [
        f"{idx}. <b>{escape(item.phase)}</b>: <code>{escape(item.command)}</code>\n   {escape(item.purpose)}"
        for idx, item in enumerate(commands, start=1)
    ]
    severity_badge = SEVERITY_BADGE.get(event.severity, event.severity.upper())
    domain_badge = DOMAIN_BADGE.get(event.domain, event.domain)
    return "\n".join(
        [
            f"🚨 <b>INFRA-LOG-SENTINEL Alert {index}/{total}</b>",
            f"<b>Alert ID:</b> <code>{escape(alert_id)}</code>",
            f"<b>Severity:</b> {severity_badge}",
            f"<b>Domain:</b> {domain_badge}",
            f"<b>Source:</b> <code>{escape(event.source)}</code>",
            f"<b>Type:</b> <code>{escape(event.event_type)}</code>",
            f"<b>Timestamp:</b> {escape(event.timestamp)}",
            "",
            f"📌 <b>Summary</b>\n{escape(_trim(event.message, 650))}",
            f"🧠 <b>Analysis</b>\n{escape(event.probable_cause)}",
            f"💥 <b>Impact</b>\n{escape(event.impact)}",
            f"🛠 <b>Solution</b>\n{escape(event.recommended_action)}",
            "",
            "🔎 <b>Commands to run</b>",
            *command_lines,
            "",
            "✅ Reply <b>ACK</b>, or any message, to acknowledge before escalation timeout.",
        ]
    )


def format_escalation_message(alert: AlertRecord) -> str:
    return "\n".join(
        [
            "🔴 <b>[ESCALATE] Infrastructure Log Sentinel</b>",
            f"<b>Alert ID:</b> <code>{escape(alert.alert_id)}</code>",
            f"<b>Severity:</b> {SEVERITY_BADGE.get(alert.severity, alert.severity.upper())}",
            f"<b>Domain:</b> {DOMAIN_BADGE.get(alert.domain, alert.domain)}",
            f"<b>Source:</b> <code>{escape(alert.source)}</code>",
            f"<b>Type:</b> <code>{escape(alert.event_type)}</code>",
            "",
            f"📌 <b>Summary</b>\n{escape(_trim(alert.message, 650))}",
            f"💥 <b>Impact</b>\n{escape(alert.impact)}",
            f"🛠 <b>Solution</b>\n{escape(alert.recommended_action)}",
            "",
            "⏱ No ACK was received within the escalation timeout. Immediate review is recommended.",
        ]
    )


def _send_message(token: str, chat_id: str, text: str) -> int | None:
    response = _telegram_post(
        token=token,
        method="sendMessage",
        json_payload={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        },
    )
    if response.ok:
        try:
            payload = response.json()
        except ValueError:
            return None
        result = payload.get("result", {})
        message_id = result.get("message_id")
        return int(message_id) if message_id is not None else None

    raise TelegramSendError(_telegram_error("Telegram API failed", response))


def _fetch_updates(token: str, chat_id: str, offset: int | None) -> list[TelegramUpdate]:
    payload: dict[str, object] = {
        "timeout": 0,
        "allowed_updates": ["message"],
    }
    if offset is not None:
        payload["offset"] = offset

    response = _telegram_post(token=token, method="getUpdates", json_payload=payload)
    if not response.ok:
        raise TelegramSendError(_telegram_error("Telegram getUpdates failed", response))

    payload = response.json()
    updates: list[TelegramUpdate] = []
    for item in payload.get("result", []):
        message = item.get("message")
        if not message:
            continue
        message_chat = message.get("chat", {})
        if str(message_chat.get("id")) != str(chat_id):
            continue
        text = str(message.get("text") or message.get("caption") or "").strip()
        if not text:
            continue
        updates.append(
            TelegramUpdate(
                update_id=int(item["update_id"]),
                message_date_ts=int(message.get("date", 0)),
                text=text,
            )
        )
    return updates


def _target_alert_ids_for_ack(
    text: str,
    message_date_ts: int,
    pending_by_id: dict[str, AlertRecord],
) -> list[str]:
    lowered = text.lower()
    explicit_ids = [
        alert_id for alert_id in pending_by_id if alert_id.lower() in lowered
    ]
    if explicit_ids:
        return explicit_ids

    # Requirement: any reply in the Telegram chat counts as acknowledgement.
    return [
        alert.alert_id
        for alert in pending_by_id.values()
        if alert.sent_at_ts <= message_date_ts
    ]


def _config_errors(token: str, chat_id: str) -> list[str]:
    errors = []
    if token in PLACEHOLDER_VALUES:
        errors.append("TELEGRAM_BOT_TOKEN is missing")
    elif ":" not in token:
        errors.append("TELEGRAM_BOT_TOKEN does not look like a bot token")

    if chat_id in PLACEHOLDER_VALUES:
        errors.append("TELEGRAM_CHAT_ID is missing")

    return errors


def _telegram_post(token: str, method: str, json_payload: dict[str, object]) -> Response:
    url = f"{TELEGRAM_API_BASE}/bot{token}/{method}"
    last_error: Exception | None = None
    for attempt in range(1, TELEGRAM_RETRIES + 2):
        try:
            return requests.post(url, json=json_payload, timeout=TELEGRAM_TIMEOUT)
        except requests_exceptions.Timeout as exc:
            last_error = exc
        except requests_exceptions.ConnectionError as exc:
            last_error = exc
        except requests_exceptions.RequestException as exc:
            last_error = exc

        if attempt <= TELEGRAM_RETRIES:
            time.sleep(attempt * 2)

    raise TelegramSendError(
        "Telegram network connection failed after retries. "
        "The workstation could not complete HTTPS/TLS connection to api.telegram.org. "
        "Check corporate proxy/firewall/VPN, then retry. "
        f"Last error: {last_error}"
    )


def _telegram_error(prefix: str, response: Response) -> str:
    try:
        error_payload = response.json()
        description = error_payload.get("description", response.text)
    except ValueError:
        description = response.text
    return f"{prefix} with HTTP {response.status_code}: {description}"


def _trim(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    return value[: limit - 3] + "..."
