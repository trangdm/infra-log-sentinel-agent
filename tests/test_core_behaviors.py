from __future__ import annotations

from pathlib import Path

from infra_log_sentinel.chat.actions import try_execute_chat_action
from infra_log_sentinel.config import Settings
from infra_log_sentinel.models import RawLogLine
from infra_log_sentinel.parsing.log_parser import parse_raw_line
from infra_log_sentinel.state.runtime_control import (
    VALUE_DEMO_LOG_INTERVAL_SECONDS,
    RuntimeControlStore,
)


def _settings(tmp_path: Path) -> Settings:
    return Settings(
        app_env="test",
        app_timezone="Asia/Ho_Chi_Minh",
        log_source_mode="runtime_folder",
        log_root_path=tmp_path / "logs",
        runtime_log_bootstrap_enabled=False,
        demo_log_bootstrap_count=0,
        demo_log_generator_enabled=False,
        demo_log_interval_seconds=30,
        demo_log_domain="all",
        demo_log_severity="abnormal",
        runtime_scheduler_enabled=False,
        runtime_scheduler_dry_run=True,
        runtime_scheduler_max_alerts=3,
        runtime_scheduler_max_escalations=1,
        report_time="09:00",
        report_lookback_hours=24,
        scan_interval_seconds=60,
        escalation_timeout_seconds=300,
        severity_alert_levels=("warning", "error", "critical"),
        state_db_path=tmp_path / "state.sqlite",
        report_output_dir=tmp_path / "reports",
        gmail_address="",
        gmail_app_password="",
        report_recipient_email="",
        telegram_bot_token="",
        telegram_chat_id="",
        telegram_ack_keywords=("ACK", "ack"),
        llm_provider="greennode",
        llm_api_base="",
        llm_api_key="",
        llm_model="minimax/minimax-m2.5",
    )


def test_parse_network_power_supply_failure_as_critical() -> None:
    event = parse_raw_line(
        RawLogLine(
            domain="network",
            source_file=Path("network-sample.log"),
            line_number=1,
            text=(
                "2026-06-12T10:00:00Z core-sw01.example.local "
                "%PLATFORM-2-PS_FAIL: Power supply 2 failed or removed"
            ),
        )
    )

    assert event.severity == "critical"
    assert event.event_type == "power_supply_failure"
    assert event.source == "core-sw01.example.local"


def test_ambiguous_interval_change_asks_for_clarification(tmp_path: Path) -> None:
    result = try_execute_chat_action(
        settings=_settings(tmp_path),
        events=[],
        question="doi interval thanh 120 giay",
        dry_run=False,
    )

    assert result.handled is True
    assert "interval" in result.message.lower()
    assert "sinh log" in result.message.lower()


def test_log_generator_interval_dry_run_does_not_mutate_state(tmp_path: Path) -> None:
    settings = _settings(tmp_path)

    result = try_execute_chat_action(
        settings=settings,
        events=[],
        question="doi interval sinh log 120 giay",
        dry_run=True,
    )

    assert result.handled is True
    assert "preview" in result.message.lower()
    assert RuntimeControlStore(settings.state_db_path).get_value(VALUE_DEMO_LOG_INTERVAL_SECONDS) is None
