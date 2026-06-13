from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
import time

from infra_log_sentinel.config import Settings
from infra_log_sentinel.notifications.telegram_format import (
    TELEGRAM_PARSE_MODE,
    format_ack_reply_for_telegram,
    format_chat_reply_for_telegram,
    format_help_for_telegram,
)
from infra_log_sentinel.notifications.telegram_sender import (
    TelegramConfigError,
    TelegramSendError,
    TelegramUpdate,
    fetch_telegram_updates,
    send_telegram_message,
)
from infra_log_sentinel.state.alert_store import AlertRecord, AlertStore


TELEGRAM_MESSAGE_LIMIT = 4096
REPLY_LIMIT = 3800
ACK_TIME_GRACE_SECONDS = 120


@dataclass
class TelegramChatResult:
    processed_count: int = 0
    answered_count: int = 0
    acked_count: int = 0
    dry_run: bool = False
    previews: list[str] = field(default_factory=list)

    @property
    def message(self) -> str:
        action = "would answer" if self.dry_run else "answered"
        ack_action = "would ACK" if self.dry_run else "ACKed"
        preview = ""
        if self.previews:
            preview = "\n\nPreview:\n" + "\n\n".join(self.previews[:2])
        return (
            f"Telegram chat check complete. Processed {self.processed_count} update(s), "
            f"{action} {self.answered_count}, {ack_action} {self.acked_count}.{preview}"
        )


def run_telegram_chat_once(
    settings: Settings,
    responder: Callable[[str], str],
    dry_run: bool = False,
    max_updates: int | None = None,
) -> TelegramChatResult:
    alert_store = AlertStore(settings.state_db_path)
    last_update_id = alert_store.get_chat_update_id()
    updates = fetch_telegram_updates(
        settings=settings,
        offset=None if last_update_id is None else last_update_id + 1,
        timeout_seconds=0,
    )
    if max_updates is not None:
        updates = updates[:max_updates]
    return process_telegram_chat_updates(
        settings=settings,
        alert_store=alert_store,
        updates=updates,
        responder=responder,
        dry_run=dry_run,
    )


def run_telegram_chat_forever(
    settings: Settings,
    responder: Callable[[str], str],
    dry_run: bool = False,
) -> None:
    print(
        "Telegram chat bridge started. "
        f"poll_interval={settings.telegram_chat_poll_interval_seconds}s dry_run={dry_run}.",
        flush=True,
    )
    while True:
        try:
            result = run_telegram_chat_once(
                settings=settings,
                responder=responder,
                dry_run=dry_run,
            )
            if result.processed_count:
                print(result.message, flush=True)
        except (TelegramConfigError, TelegramSendError) as exc:
            print(f"Telegram chat bridge error: {exc}", flush=True)
        time.sleep(max(settings.telegram_chat_poll_interval_seconds, 1.0))


def initialize_telegram_update_cursor(settings: Settings) -> int:
    alert_store = AlertStore(settings.state_db_path)
    updates = fetch_telegram_updates(settings=settings, offset=None, timeout_seconds=0)
    if not updates:
        return 0
    max_update_id = max(update.update_id for update in updates)
    alert_store.set_chat_update_id(max_update_id)
    alert_store.set_ack_update_id(max_update_id)
    return len(updates)


def process_telegram_chat_updates(
    settings: Settings,
    alert_store: AlertStore,
    updates: list[TelegramUpdate],
    responder: Callable[[str], str],
    dry_run: bool = False,
) -> TelegramChatResult:
    result = TelegramChatResult(processed_count=len(updates), dry_run=dry_run)
    if not updates:
        return result

    pending_by_id = {alert.alert_id: alert for alert in alert_store.list_pending_alerts()}
    acked_ids: set[str] = set()
    max_update_id: int | None = None

    for update in updates:
        max_update_id = (
            update.update_id if max_update_id is None else max(max_update_id, update.update_id)
        )
        target_ids = _target_alert_ids_for_ack(
            update.text,
            update.message_date_ts,
            pending_by_id,
            reply_to_message_id=update.reply_to_message_id,
        )
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

        if not _should_answer(update.text, settings):
            if target_ids and not dry_run:
                send_telegram_message(
                    settings=settings,
                    text=format_ack_reply_for_telegram(len(target_ids)),
                    parse_mode=TELEGRAM_PARSE_MODE,
                )
            continue

        if _is_help(update.text):
            answer = format_help_for_telegram()
            if target_ids:
                answer = f"{format_ack_reply_for_telegram(len(target_ids))}\n\n{answer}"
        else:
            answer = _answer_for_update(update.text, responder)
            answer = format_chat_reply_for_telegram(
                question=update.text,
                answer=answer,
                ack_count=len(target_ids),
            )
        result.answered_count += 1
        if dry_run:
            result.previews.append(_trim(answer, 700))
            continue

        for chunk in _split_telegram_text(answer):
            send_telegram_message(settings=settings, text=chunk, parse_mode=TELEGRAM_PARSE_MODE)

    result.acked_count = len(acked_ids)
    if max_update_id is not None and not dry_run:
        alert_store.set_chat_update_id(max_update_id)
    return result


def _answer_for_update(text: str, responder: Callable[[str], str]) -> str:
    return responder(text)


def _should_answer(text: str, settings: Settings) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    if _is_help(stripped):
        return True
    return not _is_ack_only(stripped, settings)


def _is_help(text: str) -> bool:
    return text.strip().lower() in {"/start", "/help", "help"}


def _is_ack_only(text: str, settings: Settings) -> bool:
    normalized = text.strip().lower()
    ack_keywords = {
        keyword.strip().lower()
        for keyword in settings.telegram_ack_keywords
        if keyword.strip()
    }
    if normalized in ack_keywords:
        return True
    return normalized.startswith("ack ") and len(normalized.split()) <= 2


def _target_alert_ids_for_ack(
    text: str,
    message_date_ts: int,
    pending_by_id: dict[str, AlertRecord],
    reply_to_message_id: int | None = None,
) -> list[str]:
    lowered = text.lower()
    explicit_ids = [alert_id for alert_id in pending_by_id if alert_id.lower() in lowered]
    if explicit_ids:
        return explicit_ids
    if reply_to_message_id is not None:
        reply_matches = [
            alert.alert_id
            for alert in pending_by_id.values()
            if alert.telegram_message_id == reply_to_message_id
        ]
        if reply_matches:
            return reply_matches
    return [
        alert.alert_id
        for alert in pending_by_id.values()
        if alert.sent_at_ts - ACK_TIME_GRACE_SECONDS <= message_date_ts
    ]


def _split_telegram_text(text: str) -> list[str]:
    text = _trim(text, REPLY_LIMIT)
    if len(text) <= TELEGRAM_MESSAGE_LIMIT:
        return [text]

    chunks = []
    remaining = text
    while remaining:
        chunk = remaining[:TELEGRAM_MESSAGE_LIMIT]
        split_at = chunk.rfind("\n")
        if split_at < TELEGRAM_MESSAGE_LIMIT // 2:
            split_at = len(chunk)
        chunks.append(remaining[:split_at].strip())
        remaining = remaining[split_at:].strip()
    return [chunk for chunk in chunks if chunk]


def _trim(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    return value[: limit - 3] + "..."
