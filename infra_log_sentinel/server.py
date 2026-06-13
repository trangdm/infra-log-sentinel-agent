from __future__ import annotations

from collections import Counter
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import sys
import threading
import time
import traceback
from typing import Any
from urllib.parse import urlparse
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from infra_log_sentinel.analysis.runbook import recommend_commands
from infra_log_sentinel.analysis.time_window import filter_events_by_lookback
from infra_log_sentinel.chat.responder import answer_or_execute_chat
from infra_log_sentinel.config import Settings, load_settings
from infra_log_sentinel.ingestion.local_folder import SUPPORTED_EXTENSIONS, iter_log_lines
from infra_log_sentinel.models import LogEvent
from infra_log_sentinel.parsing.log_parser import parse_raw_lines
from infra_log_sentinel.notifications.telegram_chat import run_telegram_chat_forever
from infra_log_sentinel.scheduler.runner import run_scheduler_forever
from infra_log_sentinel.simulator.log_generator import DOMAINS, generate_log_lines, generate_one_log_line
from infra_log_sentinel.state.runtime_control import (
    CONTROL_EMAIL_REPORTS,
    CONTROL_LOG_GENERATION,
    CONTROL_TELEGRAM_ALERTS,
    VALUE_DEMO_LOG_INTERVAL_SECONDS,
    RuntimeControlStore,
)
from infra_log_sentinel.state.alert_store import AlertStore
from infra_log_sentinel.web_ui import render_chat_ui


SERVICE_NAME = "infra-log-sentinel-agent"
MANUAL_CONTROL_OFF_UNTIL = datetime(9999, 12, 31, 23, 59, 59)
RUNTIME_CONTROL_LABELS = {
    CONTROL_TELEGRAM_ALERTS: "Telegram alerts",
    CONTROL_EMAIL_REPORTS: "Gmail reports",
    CONTROL_LOG_GENERATION: "Log generator",
}
WORKER_STATUS_LOCK = threading.Lock()
WORKER_STATUS: dict[str, dict[str, str]] = {}


def main() -> None:
    _configure_console_encoding()
    settings = load_settings()
    host = os.getenv("RUNTIME_HOST", "0.0.0.0")
    port = int(os.getenv("PORT", os.getenv("RUNTIME_PORT", "8080")))

    _prepare_runtime_storage(settings)
    _bootstrap_runtime_logs(settings)
    _start_background_workers(settings)

    server = ThreadingHTTPServer((host, port), _handler_for(settings))
    print(f"{SERVICE_NAME} runtime listening on {host}:{port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Runtime stopped.", flush=True)
    finally:
        server.server_close()


def _handler_for(settings: Settings) -> type[BaseHTTPRequestHandler]:
    class RuntimeHandler(BaseHTTPRequestHandler):
        server_version = "InfraLogSentinelHTTP/1.0"

        def do_GET(self) -> None:
            path = _normalized_path(self.path)
            if path == "/health":
                self._write_json(
                    HTTPStatus.OK,
                    {
                        "status": "ok",
                        "service": SERVICE_NAME,
                    },
                )
                return

            if path == "/status":
                self._write_json(HTTPStatus.OK, _build_status(settings))
                return

            if path in {"/", "/ui"}:
                self._write_html(HTTPStatus.OK, render_chat_ui(SERVICE_NAME))
                return

            if path == "/api":
                self._write_json(
                    HTTPStatus.OK,
                    {
                        "service": SERVICE_NAME,
                        "endpoints": {
                            "health": "GET /health",
                            "status": "GET /status",
                            "invocations": "POST /invocations",
                            "chat": "POST /chat",
                            "runtime_controls": "POST /runtime-controls",
                            "telegram_alert_counters_reset": "POST /telegram-alert-counters/reset",
                        },
                    },
                )
                return

            self._write_error(HTTPStatus.NOT_FOUND, f"Unknown path: {path}")

        def do_POST(self) -> None:
            path = _normalized_path(self.path)
            if path == "/telegram-alert-counters/reset":
                try:
                    result = _reset_telegram_alert_counters(settings)
                except Exception as exc:  # pragma: no cover - defensive API boundary
                    traceback.print_exc()
                    self._write_error(
                        HTTPStatus.INTERNAL_SERVER_ERROR,
                        f"{type(exc).__name__}: {exc}",
                    )
                    return
                self._write_json(HTTPStatus.OK, result)
                return

            if path == "/runtime-controls":
                payload = self._read_json()
                if payload is None:
                    return
                try:
                    result = _update_runtime_control(settings, payload)
                except ValueError as exc:
                    self._write_error(HTTPStatus.BAD_REQUEST, str(exc))
                    return
                except Exception as exc:  # pragma: no cover - defensive API boundary
                    traceback.print_exc()
                    self._write_error(
                        HTTPStatus.INTERNAL_SERVER_ERROR,
                        f"{type(exc).__name__}: {exc}",
                    )
                    return
                self._write_json(HTTPStatus.OK, result)
                return

            if path not in {"/invocations", "/chat"}:
                self._write_error(HTTPStatus.NOT_FOUND, f"Unknown path: {path}")
                return

            payload = self._read_json()
            if payload is None:
                return

            question = _extract_question(payload)
            if not question:
                self._write_error(
                    HTTPStatus.BAD_REQUEST,
                    "Request JSON must include one of: message, question, input, prompt, or messages.",
                )
                return

            try:
                channel = _extract_conversation_channel(payload)
                answer = _answer_or_execute_chat(
                    settings=settings,
                    question=question,
                    dry_run=bool(payload.get("dry_run", False)),
                    channel=channel,
                )
            except Exception as exc:  # pragma: no cover - defensive API boundary
                traceback.print_exc()
                self._write_error(
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                    f"{type(exc).__name__}: {exc}",
                )
                return

            self._write_json(
                HTTPStatus.OK,
                {
                    "service": SERVICE_NAME,
                    "question": question,
                    "answer": answer,
                },
            )

        def log_message(self, format: str, *args: Any) -> None:
            sys.stderr.write("%s - - [%s] %s\n" % (self.client_address[0], self.log_date_time_string(), format % args))

        def _read_json(self) -> dict[str, Any] | None:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0:
                self._write_error(HTTPStatus.BAD_REQUEST, "Request body must be valid JSON.")
                return None
            if length > 1_000_000:
                self._write_error(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "Request body is too large.")
                return None

            raw_body = self.rfile.read(length)
            try:
                payload = json.loads(raw_body.decode("utf-8"))
            except json.JSONDecodeError as exc:
                self._write_error(HTTPStatus.BAD_REQUEST, f"Invalid JSON: {exc}")
                return None

            if not isinstance(payload, dict):
                self._write_error(HTTPStatus.BAD_REQUEST, "Request JSON must be an object.")
                return None
            return payload

        def _write_json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
            body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
            self.send_response(status.value)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _write_html(self, status: HTTPStatus, html: str) -> None:
            body = html.encode("utf-8")
            self.send_response(status.value)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _write_error(self, status: HTTPStatus, message: str) -> None:
            self._write_json(status, {"error": status.phrase, "message": message})

    return RuntimeHandler


def _answer_or_execute_chat(
    settings: Settings,
    question: str,
    dry_run: bool,
    channel: str = "web",
) -> str:
    return answer_or_execute_chat(settings, question, dry_run=dry_run, channel=channel)


def _update_runtime_control(settings: Settings, payload: dict[str, Any]) -> dict[str, Any]:
    store = RuntimeControlStore(settings.state_db_path)
    control = payload.get("control")
    if isinstance(control, str) and control:
        if control not in RUNTIME_CONTROL_LABELS:
            raise ValueError("Unsupported runtime control.")
        enabled = _payload_bool(payload.get("enabled"))
        if enabled is None:
            raise ValueError("Runtime control update requires boolean field: enabled.")
        if enabled:
            store.resume(control)
            message = f"{RUNTIME_CONTROL_LABELS[control]} enabled."
        else:
            store.pause_until(control, MANUAL_CONTROL_OFF_UNTIL)
            message = f"{RUNTIME_CONTROL_LABELS[control]} disabled until it is enabled again."
        return {
            "service": SERVICE_NAME,
            "message": message,
            "status": _build_status(settings),
        }

    setting = payload.get("setting")
    if setting == VALUE_DEMO_LOG_INTERVAL_SECONDS:
        seconds = _payload_float(payload.get("seconds"))
        if seconds is None:
            raise ValueError("Generator interval update requires numeric field: seconds.")
        if seconds < 1 or seconds > 86400:
            raise ValueError("Generator interval must be between 1 and 86400 seconds.")
        stored_value = str(int(seconds)) if seconds.is_integer() else f"{seconds:g}"
        store.set_value(VALUE_DEMO_LOG_INTERVAL_SECONDS, stored_value)
        return {
            "service": SERVICE_NAME,
            "message": f"Generator interval saved: {stored_value}s.",
            "status": _build_status(settings),
        }

    raise ValueError("Request must include a supported control or setting.")


def _payload_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "y", "on", "enabled"}:
            return True
        if normalized in {"0", "false", "no", "n", "off", "disabled"}:
            return False
    return None


def _payload_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str) and value.strip():
        try:
            return float(value.strip())
        except ValueError:
            return None
    return None


def _build_status(settings: Settings) -> dict[str, Any]:
    runtime_controls = RuntimeControlStore(settings.state_db_path).snapshot()
    workers = _worker_status_snapshot()
    alert_metrics = _telegram_alert_metrics(settings)
    try:
        raw_lines = list(iter_log_lines(settings.log_root_path))
        events = parse_raw_lines(raw_lines)
    except FileNotFoundError as exc:
        return {
            "status": "degraded",
            "service": SERVICE_NAME,
            "error": str(exc),
            "config": _safe_config(settings),
            "runtime_controls": runtime_controls,
            "workers": workers,
            "delivery": _delivery_status(settings, runtime_controls, workers),
            "telegram_alert_metrics": alert_metrics,
            "raw_lines": 0,
            "parsed_events": 0,
            "severity_counts": {},
            "domain_counts": {},
            "top_alerts": [],
        }

    recent_events = filter_events_by_lookback(events, settings.report_lookback_hours)
    alert_levels = set(settings.severity_alert_levels)
    alert_events = sorted(
        [event for event in recent_events if event.severity in alert_levels],
        key=lambda event: (_severity_rank(event.severity), event.domain, event.source, event.event_type),
    )

    return {
        "status": "ok",
        "service": SERVICE_NAME,
        "config": _safe_config(settings),
        "runtime_controls": runtime_controls,
        "workers": workers,
        "delivery": _delivery_status(settings, runtime_controls, workers),
        "telegram_alert_metrics": alert_metrics,
        "raw_lines": len(raw_lines),
        "parsed_events": len(events),
        "report_window_events": len(recent_events),
        "severity_counts": dict(sorted(Counter(event.severity for event in recent_events).items())),
        "domain_counts": dict(sorted(Counter(event.domain for event in recent_events).items())),
        "top_alerts": [_event_summary(event) for event in alert_events[:5]],
    }


def _safe_config(settings: Settings) -> dict[str, Any]:
    return {
        "app_env": settings.app_env,
        "app_timezone": settings.app_timezone,
        "log_source_mode": settings.log_source_mode,
        "log_root_path": str(settings.log_root_path),
        "report_time": settings.report_time,
        "report_lookback_hours": settings.report_lookback_hours,
        "scan_interval_seconds": settings.scan_interval_seconds,
        "escalation_timeout_seconds": settings.escalation_timeout_seconds,
        "severity_alert_levels": list(settings.severity_alert_levels),
        "runtime_log_bootstrap_enabled": settings.runtime_log_bootstrap_enabled,
        "demo_log_bootstrap_count": settings.demo_log_bootstrap_count,
        "demo_log_generator_enabled": settings.demo_log_generator_enabled,
        "demo_log_interval_seconds": settings.demo_log_interval_seconds,
        "demo_log_domain": settings.demo_log_domain,
        "demo_log_severity": settings.demo_log_severity,
        "runtime_scheduler_enabled": settings.runtime_scheduler_enabled,
        "runtime_scheduler_dry_run": settings.runtime_scheduler_dry_run,
        "telegram_alerts_configured": _telegram_alerts_configured(settings),
        "telegram_chat_enabled": settings.telegram_chat_enabled,
        "telegram_chat_poll_interval_seconds": settings.telegram_chat_poll_interval_seconds,
        "telegram_chat_dry_run": settings.telegram_chat_dry_run,
        "llm_provider": settings.llm_provider,
        "llm_model": settings.llm_model,
    }


def _delivery_status(
    settings: Settings,
    runtime_controls: dict[str, Any],
    workers: dict[str, dict[str, str]] | None = None,
) -> dict[str, Any]:
    pauses = runtime_controls.get("pauses", {})
    telegram_pause = pauses.get(CONTROL_TELEGRAM_ALERTS, {}) if isinstance(pauses, dict) else {}
    paused = bool(telegram_pause.get("paused")) if isinstance(telegram_pause, dict) else False
    paused_until = telegram_pause.get("paused_until") if isinstance(telegram_pause, dict) else None
    manual_off = bool(telegram_pause.get("manual_off")) if isinstance(telegram_pause, dict) else False
    configured = _telegram_alerts_configured(settings)
    scheduler_worker = (workers or {}).get("runtime_scheduler", {})
    scheduler_worker_state = scheduler_worker.get("state", "unknown")

    if not configured:
        state = "misconfigured"
        label = "config missing"
        detail = "Telegram bot token or chat id is missing/placeholder."
    elif not settings.runtime_scheduler_enabled:
        state = "disabled"
        label = "scheduler off"
        detail = "Runtime scheduler is disabled, so realtime alert scans are not running."
    elif scheduler_worker_state not in {"running", "unknown"}:
        state = "worker_down"
        label = "worker down"
        detail = "Runtime scheduler worker is not running; alert scans are not executing."
    elif settings.runtime_scheduler_dry_run:
        state = "dry_run"
        label = "dry-run"
        detail = "Runtime scheduler is in preview mode and will not send Telegram alerts."
    elif paused and manual_off:
        state = "off"
        label = "off"
        detail = "Telegram alert delivery is off until it is enabled again."
    elif paused:
        state = "paused"
        label = "paused"
        detail = f"Telegram alert delivery is paused until {paused_until}."
    else:
        state = "live"
        label = "live"
        detail = "Runtime scheduler is scanning new logs and sending Telegram alerts."

    return {
        "telegram_alerts": {
            "state": state,
            "label": label,
            "detail": detail,
            "configured": configured,
            "scheduler_enabled": settings.runtime_scheduler_enabled,
            "scheduler_worker_state": scheduler_worker_state,
            "dry_run": settings.runtime_scheduler_dry_run,
            "paused": paused,
            "paused_until": paused_until,
            "manual_off": manual_off,
        }
    }


def _telegram_alerts_configured(settings: Settings) -> bool:
    return _has_real_secret(settings.telegram_bot_token) and _has_real_secret(settings.telegram_chat_id)


def _has_real_secret(value: str) -> bool:
    return value.strip() not in {
        "",
        "replace_with_telegram_bot_token",
        "replace_with_telegram_chat_id",
    }


def _telegram_alert_metrics(settings: Settings) -> dict[str, Any]:
    try:
        store = AlertStore(settings.state_db_path)
        window_starts = _telegram_metric_window_starts(settings.app_timezone)
        windows = {
            key: store.status_counts(since_ts=start_ts)
            for key, start_ts in window_starts.items()
        }
        default_window = "today"
        default_counts = windows[default_window]
        return {
            **default_counts,
            "default_window": default_window,
            "timezone": _metric_timezone_name(settings.app_timezone),
            "windows": windows,
            "window_starts": window_starts,
            "generated_at_ts": int(time.time()),
        }
    except Exception:
        return {
            "sent_total": 0,
            "pending": 0,
            "acknowledged": 0,
            "escalated": 0,
            "default_window": "today",
            "timezone": _metric_timezone_name(settings.app_timezone),
            "windows": {
                "today": _zero_alert_counts(),
                "24h": _zero_alert_counts(),
                "7d": _zero_alert_counts(),
                "all": _zero_alert_counts(),
            },
            "window_starts": {
                "today": None,
                "24h": None,
                "7d": None,
                "all": None,
            },
            "generated_at_ts": int(time.time()),
        }


def _telegram_metric_window_starts(app_timezone: str) -> dict[str, int | None]:
    now_ts = int(time.time())
    tz = _metric_timezone(app_timezone)
    local_now = datetime.fromtimestamp(now_ts, tz)
    today_start = int(
        local_now.replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
    )
    return {
        "today": today_start,
        "24h": now_ts - 24 * 60 * 60,
        "7d": now_ts - 7 * 24 * 60 * 60,
        "all": None,
    }


def _metric_timezone(app_timezone: str) -> ZoneInfo:
    try:
        return ZoneInfo(app_timezone)
    except ZoneInfoNotFoundError:
        return ZoneInfo("UTC")


def _metric_timezone_name(app_timezone: str) -> str:
    try:
        ZoneInfo(app_timezone)
    except ZoneInfoNotFoundError:
        return "UTC"
    return app_timezone


def _zero_alert_counts() -> dict[str, int]:
    return {
        "sent_total": 0,
        "pending": 0,
        "acknowledged": 0,
        "escalated": 0,
    }


def _reset_telegram_alert_counters(settings: Settings) -> dict[str, Any]:
    deleted_count = AlertStore(settings.state_db_path).reset_alerts()
    return {
        "status": "ok",
        "deleted_count": deleted_count,
        "telegram_alert_metrics": _telegram_alert_metrics(settings),
    }


def _mark_worker(name: str, state: str, detail: str = "") -> None:
    with WORKER_STATUS_LOCK:
        WORKER_STATUS[name] = {
            "state": state,
            "detail": detail,
            "updated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        }


def _worker_status_snapshot() -> dict[str, dict[str, str]]:
    with WORKER_STATUS_LOCK:
        return {name: dict(status) for name, status in WORKER_STATUS.items()}


def _event_summary(event: LogEvent) -> dict[str, Any]:
    return {
        "timestamp": event.timestamp,
        "domain": event.domain,
        "source": event.source,
        "severity": event.severity,
        "event_type": event.event_type,
        "message": event.message,
        "probable_cause": event.probable_cause,
        "impact": event.impact,
        "recommended_action": event.recommended_action,
        "commands": [
            {
                "phase": command.phase,
                "command": command.command,
                "purpose": command.purpose,
            }
            for command in recommend_commands(event)[:3]
        ],
    }


def _extract_question(payload: dict[str, Any]) -> str:
    for key in ("message", "question", "input", "prompt"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    messages = payload.get("messages")
    if isinstance(messages, list):
        for message in reversed(messages):
            if isinstance(message, dict):
                content = message.get("content")
                if isinstance(content, str) and content.strip():
                    return content.strip()
    return ""


def _extract_conversation_channel(payload: dict[str, Any]) -> str:
    for key in ("conversation_id", "session_id", "channel"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return "web"


def _normalized_path(raw_path: str) -> str:
    path = urlparse(raw_path).path.rstrip("/")
    return path or "/"


def _severity_rank(severity: str) -> int:
    return {"critical": 0, "error": 1, "warning": 2, "info": 3}.get(severity, 99)


def _prepare_runtime_storage(settings: Settings) -> None:
    settings.log_root_path.mkdir(parents=True, exist_ok=True)
    settings.report_output_dir.mkdir(parents=True, exist_ok=True)
    settings.state_db_path.parent.mkdir(parents=True, exist_ok=True)
    if settings.log_source_mode == "runtime_folder":
        for domain in DOMAINS:
            (settings.log_root_path / domain).mkdir(parents=True, exist_ok=True)
    print(f"Runtime log folder ready: {settings.log_root_path}", flush=True)


def _bootstrap_runtime_logs(settings: Settings) -> None:
    if not settings.runtime_log_bootstrap_enabled:
        return
    if settings.demo_log_bootstrap_count <= 0:
        return
    if _log_folder_has_files(settings):
        print("Runtime log bootstrap skipped: existing log files found.", flush=True)
        return

    generated = generate_log_lines(
        log_root_path=settings.log_root_path,
        count=settings.demo_log_bootstrap_count,
        interval_seconds=0,
        domain=settings.demo_log_domain,
        severity=settings.demo_log_severity,
    )
    print(
        f"Runtime log bootstrap generated {len(generated)} synthetic log line(s) "
        f"in {settings.log_root_path}.",
        flush=True,
    )


def _start_background_workers(settings: Settings) -> None:
    if settings.demo_log_generator_enabled:
        thread = threading.Thread(
            target=_run_demo_log_generator,
            args=(settings,),
            name="demo-log-generator",
            daemon=True,
        )
        thread.start()
        print(
            "Demo log generator started: "
            f"interval={settings.demo_log_interval_seconds}s "
            f"domain={settings.demo_log_domain} severity={settings.demo_log_severity}.",
            flush=True,
        )

    if settings.runtime_scheduler_enabled:
        thread = threading.Thread(
            target=_run_scheduler_background,
            args=(settings,),
            name="runtime-scheduler",
            daemon=True,
        )
        thread.start()
        print(
            "Runtime scheduler started: "
            f"dry_run={settings.runtime_scheduler_dry_run} "
            f"scan_interval={settings.scan_interval_seconds}s.",
            flush=True,
        )

    if settings.telegram_chat_enabled:
        thread = threading.Thread(
            target=_run_telegram_chat_background,
            args=(settings,),
            name="telegram-chat-bridge",
            daemon=True,
        )
        thread.start()
        print(
            "Telegram chat bridge enabled: "
            f"interval={settings.telegram_chat_poll_interval_seconds}s "
            f"dry_run={settings.telegram_chat_dry_run}.",
            flush=True,
        )


def _run_demo_log_generator(settings: Settings) -> None:
    control_store = RuntimeControlStore(settings.state_db_path)
    while True:
        interval_seconds = control_store.get_float_value(
            VALUE_DEMO_LOG_INTERVAL_SECONDS,
            settings.demo_log_interval_seconds,
        )
        pause_state = control_store.pause_state(CONTROL_LOG_GENERATION)
        if pause_state.paused:
            print(
                f"Demo log generator paused until {pause_state.paused_until:%Y-%m-%d %H:%M:%S}.",
                flush=True,
            )
            time.sleep(max(min(interval_seconds, 30.0), 1.0))
            continue

        try:
            generated = generate_one_log_line(
                log_root_path=settings.log_root_path,
                domain=settings.demo_log_domain,
                severity=settings.demo_log_severity,
            )
            print(
                "Generated runtime demo log: "
                f"[{generated.severity.upper()}] {generated.domain} -> {generated.path.name}",
                flush=True,
            )
        except Exception:
            traceback.print_exc()
        time.sleep(max(interval_seconds, 1.0))


def _run_scheduler_background(settings: Settings) -> None:
    _mark_worker("runtime_scheduler", "running")
    try:
        run_scheduler_forever(
            settings=settings,
            dry_run=settings.runtime_scheduler_dry_run,
            max_alerts=settings.runtime_scheduler_max_alerts,
            max_escalations=settings.runtime_scheduler_max_escalations,
        )
    except Exception as exc:
        _mark_worker("runtime_scheduler", "stopped", f"{type(exc).__name__}: {exc}")
        traceback.print_exc()


def _run_telegram_chat_background(settings: Settings) -> None:
    _mark_worker("telegram_chat_bridge", "running")
    try:
        run_telegram_chat_forever(
            settings=settings,
            responder=lambda question: _answer_or_execute_chat(
                settings=settings,
                question=question,
                dry_run=settings.telegram_chat_dry_run,
                channel="telegram",
            ),
            dry_run=settings.telegram_chat_dry_run,
        )
    except Exception as exc:
        _mark_worker("telegram_chat_bridge", "stopped", f"{type(exc).__name__}: {exc}")
        traceback.print_exc()


def _log_folder_has_files(settings: Settings) -> bool:
    return any(
        path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
        for path in settings.log_root_path.rglob("*")
    )


def _configure_console_encoding() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


if __name__ == "__main__":
    main()
