from __future__ import annotations

from collections import Counter
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

from infra_log_sentinel.analysis.runbook import recommend_commands
from infra_log_sentinel.analysis.time_window import filter_events_by_lookback
from infra_log_sentinel.chat.actions import try_execute_chat_action
from infra_log_sentinel.chat.llm_assistant import answer_with_llm
from infra_log_sentinel.chat.log_chat import answer_log_question
from infra_log_sentinel.config import Settings, load_settings
from infra_log_sentinel.ingestion.local_folder import SUPPORTED_EXTENSIONS, iter_log_lines
from infra_log_sentinel.models import LogEvent
from infra_log_sentinel.parsing.log_parser import parse_raw_lines
from infra_log_sentinel.scheduler.runner import run_scheduler_forever
from infra_log_sentinel.simulator.log_generator import DOMAINS, generate_log_lines, generate_one_log_line
from infra_log_sentinel.state.runtime_control import (
    CONTROL_LOG_GENERATION,
    VALUE_DEMO_LOG_INTERVAL_SECONDS,
    RuntimeControlStore,
)
from infra_log_sentinel.web_ui import render_chat_ui


SERVICE_NAME = "infra-log-sentinel-agent"


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
                        },
                    },
                )
                return

            self._write_error(HTTPStatus.NOT_FOUND, f"Unknown path: {path}")

        def do_POST(self) -> None:
            path = _normalized_path(self.path)
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
                answer = _answer_or_execute_chat(
                    settings=settings,
                    question=question,
                    dry_run=bool(payload.get("dry_run", False)),
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


def _answer_or_execute_chat(settings: Settings, question: str, dry_run: bool) -> str:
    raw_lines = list(iter_log_lines(settings.log_root_path))
    events = parse_raw_lines(raw_lines)
    action_result = try_execute_chat_action(
        settings=settings,
        events=events,
        question=question,
        dry_run=dry_run,
    )
    if action_result.handled:
        return action_result.message
    llm_answer = answer_with_llm(settings, events, question, settings.severity_alert_levels)
    if llm_answer:
        return llm_answer
    return answer_log_question(events, question, settings.severity_alert_levels)


def _build_status(settings: Settings) -> dict[str, Any]:
    try:
        raw_lines = list(iter_log_lines(settings.log_root_path))
        events = parse_raw_lines(raw_lines)
    except FileNotFoundError as exc:
        return {
            "status": "degraded",
            "service": SERVICE_NAME,
            "error": str(exc),
            "config": _safe_config(settings),
            "runtime_controls": RuntimeControlStore(settings.state_db_path).snapshot(),
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
        "runtime_controls": RuntimeControlStore(settings.state_db_path).snapshot(),
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
        "llm_provider": settings.llm_provider,
        "llm_model": settings.llm_model,
    }


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
    try:
        run_scheduler_forever(
            settings=settings,
            dry_run=settings.runtime_scheduler_dry_run,
            max_alerts=settings.runtime_scheduler_max_alerts,
            max_escalations=settings.runtime_scheduler_max_escalations,
        )
    except Exception:
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
