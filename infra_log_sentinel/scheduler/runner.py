from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import time

import schedule

from infra_log_sentinel.config import Settings
from infra_log_sentinel.analysis.time_window import filter_events_by_lookback
from infra_log_sentinel.ingestion.local_folder import iter_log_lines, iter_new_log_lines
from infra_log_sentinel.notifications.gmail_sender import send_report_email
from infra_log_sentinel.notifications.telegram_sender import (
    check_ack_and_escalations,
    send_telegram_alerts,
)
from infra_log_sentinel.parsing.log_parser import parse_raw_lines
from infra_log_sentinel.reporting.pdf_report import build_pdf_report
from infra_log_sentinel.state.alert_store import AlertStore
from infra_log_sentinel.state.log_cursor import LogCursorStore
from infra_log_sentinel.state.runtime_control import (
    CONTROL_EMAIL_REPORTS,
    CONTROL_TELEGRAM_ALERTS,
    RuntimeControlStore,
)


@dataclass
class SchedulerRunResult:
    messages: list[str] = field(default_factory=list)

    def add(self, message: str) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.messages.append(f"{timestamp} | {message}")

    def as_text(self) -> str:
        return "\n".join(self.messages)


def run_scheduler_once(
    settings: Settings,
    dry_run: bool = False,
    max_alerts: int | None = None,
    max_escalations: int | None = None,
    force_escalate: bool = False,
) -> SchedulerRunResult:
    result = SchedulerRunResult()
    result.add("Starting one scheduler cycle.")
    result.add(run_daily_report(settings=settings, dry_run=dry_run))
    result.add(
        run_alert_scan(
            settings=settings,
            dry_run=dry_run,
            max_alerts=max_alerts,
        )
    )
    result.add(
        run_ack_check(
            settings=settings,
            dry_run=dry_run,
            max_escalations=max_escalations,
            force_escalate=force_escalate,
        )
    )
    result.add("Scheduler cycle complete.")
    return result


def run_scheduler_forever(
    settings: Settings,
    dry_run: bool = False,
    max_alerts: int | None = None,
    max_escalations: int | None = None,
) -> None:
    print(
        "Scheduler started. "
        f"Daily report at {settings.report_time}; "
        f"scan interval {settings.scan_interval_seconds}s."
    )

    schedule.every().day.at(settings.report_time).do(
        lambda: _print_job_result(run_daily_report(settings=settings, dry_run=dry_run))
    )
    schedule.every(settings.scan_interval_seconds).seconds.do(
        lambda: _print_job_result(
            run_alert_scan(settings=settings, dry_run=dry_run, max_alerts=max_alerts)
        )
    )
    schedule.every(settings.scan_interval_seconds).seconds.do(
        lambda: _print_job_result(
            run_ack_check(
                settings=settings,
                dry_run=dry_run,
                max_escalations=max_escalations,
                force_escalate=False,
            )
        )
    )

    while True:
        schedule.run_pending()
        time.sleep(1)


def run_daily_report(settings: Settings, dry_run: bool = False) -> str:
    pause_state = RuntimeControlStore(settings.state_db_path).pause_state(CONTROL_EMAIL_REPORTS)
    if pause_state.paused:
        return f"Daily report job skipped: Gmail reports paused until {pause_state.paused_until:%Y-%m-%d %H:%M:%S}."

    events = filter_events_by_lookback(
        _load_events(settings),
        lookback_hours=settings.report_lookback_hours,
    )
    report_path = build_pdf_report(
        events=events,
        output_dir=settings.report_output_dir,
        alert_levels=settings.severity_alert_levels,
        report_window_label=f"Last {settings.report_lookback_hours} hours",
    )
    email_result = send_report_email(
        settings=settings,
        report_path=report_path,
        dry_run=dry_run,
    )
    return (
        f"Daily report job: generated {report_path} "
        f"with {len(events)} event(s) in last {settings.report_lookback_hours}h. "
        f"{email_result.message}"
    )


def run_alert_scan(
    settings: Settings,
    dry_run: bool = False,
    max_alerts: int | None = None,
) -> str:
    cursor_store = LogCursorStore(settings.state_db_path)
    pause_state = RuntimeControlStore(settings.state_db_path).pause_state(CONTROL_TELEGRAM_ALERTS)
    if pause_state.paused:
        raw_lines = list(
            iter_new_log_lines(
                settings.log_root_path,
                cursor_store,
                update_cursor=not dry_run,
            )
        )
        cursor_note = "consumed" if not dry_run else "previewed"
        return (
            f"Alert scan job skipped: Telegram alerts paused until {pause_state.paused_until:%Y-%m-%d %H:%M:%S}. "
            f"Read and {cursor_note} {len(raw_lines)} new log line(s) without sending."
        )

    raw_lines = list(
        iter_new_log_lines(
            settings.log_root_path,
            cursor_store,
            update_cursor=not dry_run,
        )
    )
    events = parse_raw_lines(raw_lines)
    alert_store = None if dry_run else AlertStore(settings.state_db_path)
    telegram_result = send_telegram_alerts(
        settings=settings,
        events=events,
        dry_run=dry_run,
        max_alerts=max_alerts,
        alert_store=alert_store,
    )
    return f"Alert scan job: read {len(raw_lines)} new log line(s). {telegram_result.message}"


def run_ack_check(
    settings: Settings,
    dry_run: bool = False,
    max_escalations: int | None = None,
    force_escalate: bool = False,
) -> str:
    pause_state = RuntimeControlStore(settings.state_db_path).pause_state(CONTROL_TELEGRAM_ALERTS)
    if pause_state.paused:
        return f"ACK/escalation job skipped: Telegram alerts paused until {pause_state.paused_until:%Y-%m-%d %H:%M:%S}."

    ack_result = check_ack_and_escalations(
        settings=settings,
        alert_store=AlertStore(settings.state_db_path),
        dry_run=dry_run,
        max_escalations=max_escalations,
        force_escalate=force_escalate,
    )
    return f"ACK/escalation job: {ack_result.message}"


def _load_events(settings: Settings):
    raw_lines = list(iter_log_lines(settings.log_root_path))
    return parse_raw_lines(raw_lines)


def _print_job_result(message: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{timestamp} | {message}", flush=True)
