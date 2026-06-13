from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from infra_log_sentinel.chat.actions import try_execute_chat_action
from infra_log_sentinel.chat.intent import (
    INTENT_AMBIGUOUS_OPERATIONAL_CHANGE,
    INTENT_ASSISTANT_FEEDBACK,
    INTENT_LOG_QUESTION,
    INTENT_SAFE_ACTION,
    classify_chat_intent,
    normalize_text,
)
from infra_log_sentinel.chat.responder import answer_or_execute_chat
from infra_log_sentinel.config import Settings
from infra_log_sentinel.models import LogEvent, RawLogLine
from infra_log_sentinel.notifications.telegram_format import format_chat_reply_for_telegram
from infra_log_sentinel.notifications.telegram_chat import process_telegram_chat_updates
from infra_log_sentinel.notifications.telegram_sender import (
    TelegramUpdate,
    check_ack_and_escalations,
)
from infra_log_sentinel.parsing.log_parser import parse_raw_line
from infra_log_sentinel.scheduler.runner import _run_job_safely
from infra_log_sentinel.server import (
    _build_status,
    _delivery_status,
    _extract_question,
    _prepare_runtime_storage,
    _reset_telegram_alert_counters,
    _update_runtime_control,
)
from infra_log_sentinel.simulator.log_generator import DOMAINS
from infra_log_sentinel.state.alert_store import AlertStore
from infra_log_sentinel.state.runtime_control import (
    CONTROL_TELEGRAM_ALERTS,
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
        telegram_chat_enabled=False,
        telegram_chat_poll_interval_seconds=3,
        telegram_chat_dry_run=False,
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
    assert (
        RuntimeControlStore(settings.state_db_path).get_value(VALUE_DEMO_LOG_INTERVAL_SECONDS)
        is None
    )


def test_summary_log_question_is_not_runtime_change_action(tmp_path: Path) -> None:
    result = try_execute_chat_action(
        settings=_settings(tmp_path),
        events=[],
        question="Tóm tắt log hôm nay",
        dry_run=False,
    )

    assert result.handled is False


def test_intent_router_separates_log_questions_from_actions() -> None:
    summary = classify_chat_intent("Tóm tắt log hôm nay")
    command = classify_chat_intent("command xử lý vmware warning")
    email = classify_chat_intent("gửi báo cáo hôm nay qua Gmail")
    ambiguous = classify_chat_intent("đổi interval thành 120 giây")
    feedback = classify_chat_intent(
        "Tôi đang hỏi bạn chứ không phải yêu cầu bạn xuất log warning"
    )
    correction = classify_chat_intent(
        "trong câu hỏi trên không đề cập đến việc thay đổi cấu hình gì cả"
    )

    assert summary.kind == INTENT_LOG_QUESTION
    assert summary.action_candidate is False
    assert summary.rules_first is True
    assert command.kind == INTENT_LOG_QUESTION
    assert command.rules_first is True
    assert email.kind == INTENT_SAFE_ACTION
    assert email.action_candidate is True
    assert ambiguous.kind == INTENT_AMBIGUOUS_OPERATIONAL_CHANGE
    assert ambiguous.action_candidate is True
    assert feedback.kind == INTENT_ASSISTANT_FEEDBACK
    assert feedback.action_candidate is False
    assert feedback.rules_first is False
    assert correction.kind == INTENT_ASSISTANT_FEEDBACK
    assert correction.action_candidate is False
    assert correction.rules_first is False


def test_action_layer_rejects_log_summary_and_user_corrections(tmp_path: Path) -> None:
    settings = _settings(tmp_path)

    summary = try_execute_chat_action(
        settings=settings,
        events=[],
        question="tóm tắt log hôm nay",
        dry_run=False,
    )
    correction = try_execute_chat_action(
        settings=settings,
        events=[],
        question="trong câu hỏi trên không đề cập đến việc thay đổi cấu hình gì cả",
        dry_run=False,
    )

    assert summary.handled is False
    assert correction.handled is False


def test_feedback_question_does_not_dump_warning_logs(tmp_path: Path, monkeypatch) -> None:
    settings = _settings(tmp_path)
    _prepare_runtime_storage(settings)
    log_file = settings.log_root_path / "linux" / "dynamic-linux.log"
    log_file.write_text(
        (
            "Jun 12 10:00:00 linux-web01.example.local sshd[1842]: "
            "Failed password for invalid user admin from 203.0.113.79 port 51520 ssh2\n"
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "infra_log_sentinel.chat.responder.answer_with_llm",
        lambda *args, **kwargs: None,
    )

    answer = answer_or_execute_chat(
        settings,
        "Tôi đang hỏi bạn chứ không phải yêu cầu bạn xuất log warning",
        dry_run=False,
    )

    assert "không phải yêu cầu truy vấn" in answer
    assert "Failed password" not in answer
    assert "[WARNING]" not in answer


def test_summary_log_question_uses_deterministic_answer_before_llm(
    tmp_path: Path,
    monkeypatch,
) -> None:
    settings = _settings(tmp_path)
    _prepare_runtime_storage(settings)
    log_file = settings.log_root_path / "network" / "dynamic-network.log"
    log_file.write_text(
        (
            "2026-06-12T10:00:00Z core-sw01.example.local "
            "%PLATFORM-2-PS_FAIL: Power supply 2 failed or removed\n"
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "infra_log_sentinel.chat.responder.answer_with_llm",
        lambda *args, **kwargs: "WRONG RUNTIME ACTION ANSWER",
    )
    def fail_if_action_layer_is_called(*args, **kwargs):
        raise AssertionError("summary log question should not enter action layer")

    monkeypatch.setattr(
        "infra_log_sentinel.chat.responder.try_execute_chat_action",
        fail_if_action_layer_is_called,
    )

    answer = answer_or_execute_chat(settings, "Tóm tắt log hôm nay", dry_run=False)

    assert "WRONG RUNTIME ACTION ANSWER" not in answer
    assert "Power supply 2 failed or removed" in answer


def test_report_requested_in_chat_stays_inline_without_pdf_or_mail(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _prepare_runtime_storage(settings)
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    log_file = settings.log_root_path / "network" / "dynamic-network.log"
    log_file.write_text(
        (
            f"{timestamp} core-sw01.example.local "
            "%PLATFORM-2-PS_FAIL: Power supply 2 failed or removed\n"
        ),
        encoding="utf-8",
    )

    answer = answer_or_execute_chat(
        settings,
        "hãy report tại giao diện chat",
        dry_run=False,
        channel="test-inline-report",
    )
    normalized = normalize_text(answer)

    assert "khong tao pdf" in normalized
    assert "khong gui gmail" in normalized
    assert "Power supply 2 failed or removed" in answer
    assert list(settings.report_output_dir.glob("*.pdf")) == []


def test_report_chat_followup_uses_previous_context_without_new_delivery(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _prepare_runtime_storage(settings)
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    log_file = settings.log_root_path / "network" / "dynamic-network.log"
    log_file.write_text(
        (
            f"{timestamp} core-sw01.example.local "
            "%PLATFORM-2-PS_FAIL: Power supply 2 failed or removed\n"
        ),
        encoding="utf-8",
    )

    first = answer_or_execute_chat(
        settings,
        "xuất PDF report 24 giờ qua",
        dry_run=False,
        channel="test-report-followup",
    )
    pdfs_after_first = list(settings.report_output_dir.glob("*.pdf"))
    second = answer_or_execute_chat(
        settings,
        "hãy report ở giao diện chat",
        dry_run=False,
        channel="test-report-followup",
    )
    normalized_second = normalize_text(second)

    assert "- File:" in first
    assert len(pdfs_after_first) == 1
    assert list(settings.report_output_dir.glob("*.pdf")) == pdfs_after_first
    assert "cau noi tiep" in normalized_second
    assert "khong tao pdf moi" in normalized_second
    assert "khong gui gmail" in normalized_second
    assert "Power supply 2 failed or removed" in second


def test_command_explanation_does_not_generate_runbook(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _prepare_runtime_storage(settings)
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    log_file = settings.log_root_path / "windows" / "dynamic-windows.log"
    log_file.write_text(
        (
            f"{timestamp} WIN-DB01.example.local "
            'System EventID=7031 Level=Critical Source=Service Control Manager '
            'Message="The SQLAgent service terminated unexpectedly. It has done this 3 time(s)"\n'
        ),
        encoding="utf-8",
    )

    answer = answer_or_execute_chat(
        settings,
        'tôi không hiểu lệnh này dùng để làm gì hay giải thích ý nghĩa "Get-Service SQLAgent"',
        dry_run=False,
        channel="test-command-explain",
    )
    normalized = normalize_text(answer)

    assert "giai thich command" in normalized
    assert "windows service" in normalized
    assert "running" in normalized
    assert "runbook command de xuat" not in normalized
    assert "restart-service sqlagent" not in normalized


def test_runtime_storage_prepares_self_contained_agentbase_folders(tmp_path: Path) -> None:
    settings = _settings(tmp_path)

    _prepare_runtime_storage(settings)

    assert settings.log_root_path.is_dir()
    assert settings.report_output_dir.is_dir()
    assert settings.state_db_path.parent.is_dir()
    for domain in DOMAINS:
        assert (settings.log_root_path / domain).is_dir()


def test_runtime_status_summarizes_recent_alerts(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _prepare_runtime_storage(settings)
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    log_file = settings.log_root_path / "network" / "dynamic-network.log"
    log_file.write_text(
        (
            f"{timestamp} core-sw01.example.local "
            "%PLATFORM-2-PS_FAIL: Power supply 2 failed or removed\n"
        ),
        encoding="utf-8",
    )

    status = _build_status(settings)

    assert status["status"] == "ok"
    assert status["raw_lines"] == 1
    assert status["parsed_events"] == 1
    assert status["severity_counts"]["critical"] == 1
    assert status["domain_counts"]["network"] == 1
    assert status["top_alerts"][0]["event_type"] == "power_supply_failure"


def test_runtime_status_includes_telegram_alert_metrics(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _prepare_runtime_storage(settings)
    alert_store = AlertStore(settings.state_db_path)
    now_ts = int(datetime.now(timezone.utc).timestamp())
    old_ts = now_ts - 8 * 24 * 60 * 60

    pending_id = alert_store.upsert_pending_alert(
        event=replace(_log_event(), line_number=1, message="pending alert"),
        telegram_message_id=10,
        sent_at_ts=now_ts,
        due_at_ts=now_ts + 300,
    )
    acked_id = alert_store.upsert_pending_alert(
        event=replace(_log_event(), line_number=2, message="acked alert"),
        telegram_message_id=11,
        sent_at_ts=now_ts,
        due_at_ts=now_ts + 310,
    )
    escalated_id = alert_store.upsert_pending_alert(
        event=replace(_log_event(), line_number=3, message="escalated alert"),
        telegram_message_id=12,
        sent_at_ts=now_ts,
        due_at_ts=now_ts + 320,
    )
    old_id = alert_store.upsert_pending_alert(
        event=replace(_log_event(), line_number=4, message="old acked alert"),
        telegram_message_id=13,
        sent_at_ts=old_ts,
        due_at_ts=old_ts + 300,
    )
    alert_store.mark_acknowledged(
        alert_id=acked_id,
        ack_text="ACK",
        acked_at_ts=now_ts,
        update_id=30,
    )
    alert_store.mark_escalated(
        alert_id=escalated_id,
        escalated_at_ts=now_ts,
        escalation_message_id=14,
    )
    alert_store.mark_acknowledged(
        alert_id=old_id,
        ack_text="ACK",
        acked_at_ts=old_ts + 60,
        update_id=31,
    )

    metrics = _build_status(settings)["telegram_alert_metrics"]

    assert alert_store.get_alert_status(pending_id) == "pending"
    assert metrics["default_window"] == "today"
    assert metrics["sent_total"] == 3
    assert metrics["pending"] == 1
    assert metrics["acknowledged"] == 1
    assert metrics["escalated"] == 1
    assert metrics["windows"]["today"] == {
        "sent_total": 3,
        "pending": 1,
        "acknowledged": 1,
        "escalated": 1,
    }
    assert metrics["windows"]["24h"] == metrics["windows"]["today"]
    assert metrics["windows"]["7d"] == metrics["windows"]["today"]
    assert metrics["windows"]["all"] == {
        "sent_total": 4,
        "pending": 1,
        "acknowledged": 2,
        "escalated": 1,
    }


def test_reset_telegram_alert_counters_clears_alert_records(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _prepare_runtime_storage(settings)
    alert_store = AlertStore(settings.state_db_path)
    now_ts = int(datetime.now(timezone.utc).timestamp())

    alert_store.upsert_pending_alert(
        event=replace(_log_event(), line_number=1, message="pending alert"),
        telegram_message_id=10,
        sent_at_ts=now_ts,
        due_at_ts=now_ts + 300,
    )

    result = _reset_telegram_alert_counters(settings)

    assert result["status"] == "ok"
    assert result["deleted_count"] == 1
    assert result["telegram_alert_metrics"]["windows"]["all"] == {
        "sent_total": 0,
        "pending": 0,
        "acknowledged": 0,
        "escalated": 0,
    }
    assert alert_store.status_counts() == {
        "sent_total": 0,
        "pending": 0,
        "acknowledged": 0,
        "escalated": 0,
    }


def test_runtime_status_exposes_telegram_delivery_state(tmp_path: Path) -> None:
    settings = replace(
        _settings(tmp_path),
        telegram_bot_token="123456:realish-token-for-test",
        telegram_chat_id="1234567890",
        runtime_scheduler_enabled=False,
        runtime_scheduler_dry_run=True,
    )
    _prepare_runtime_storage(settings)

    status = _build_status(settings)
    delivery = status["delivery"]["telegram_alerts"]

    assert delivery["state"] == "disabled"
    assert delivery["scheduler_enabled"] is False
    assert delivery["dry_run"] is True
    assert delivery["configured"] is True


def test_delivery_status_reports_scheduler_worker_down(tmp_path: Path) -> None:
    settings = replace(
        _settings(tmp_path),
        telegram_bot_token="123456:realish-token-for-test",
        telegram_chat_id="1234567890",
        runtime_scheduler_enabled=True,
        runtime_scheduler_dry_run=False,
    )
    runtime_controls = {
        "pauses": {
            CONTROL_TELEGRAM_ALERTS: {
                "paused": False,
                "paused_until": None,
                "manual_off": False,
            }
        }
    }

    delivery = _delivery_status(
        settings,
        runtime_controls,
        {"runtime_scheduler": {"state": "stopped", "detail": "boom"}},
    )["telegram_alerts"]

    assert delivery["state"] == "worker_down"
    assert delivery["label"] == "worker down"
    assert delivery["scheduler_worker_state"] == "stopped"


def test_control_status_distinguishes_pause_from_telegram_delivery(tmp_path: Path) -> None:
    settings = replace(
        _settings(tmp_path),
        telegram_bot_token="123456:realish-token-for-test",
        telegram_chat_id="1234567890",
        runtime_scheduler_enabled=False,
        runtime_scheduler_dry_run=True,
    )

    result = try_execute_chat_action(
        settings=settings,
        events=[],
        question="trang thai control",
        dry_run=False,
    )

    assert result.handled is True
    assert "telegram_alert_pause:" in result.message
    assert "telegram_alert_delivery: disabled" in result.message
    assert "scheduler_worker: disabled" in result.message
    assert "delivery_mode: dry_run" in result.message


def test_scheduler_job_errors_are_logged_without_raising(monkeypatch) -> None:
    messages = []
    monkeypatch.setattr(
        "infra_log_sentinel.scheduler.runner._print_job_result",
        lambda message: messages.append(message),
    )
    monkeypatch.setattr(
        "infra_log_sentinel.scheduler.runner.traceback.print_exc",
        lambda: None,
    )

    _run_job_safely(
        "ACK/escalation job",
        lambda: (_ for _ in ()).throw(RuntimeError("telegram 409")),
    )

    assert messages == ["ACK/escalation job failed: RuntimeError: telegram 409"]


def test_runtime_control_api_toggles_alerts_and_saves_interval(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _prepare_runtime_storage(settings)

    off_result = _update_runtime_control(
        settings,
        {"control": CONTROL_TELEGRAM_ALERTS, "enabled": False},
    )
    telegram_pause = off_result["status"]["runtime_controls"]["pauses"][CONTROL_TELEGRAM_ALERTS]

    assert telegram_pause["paused"] is True
    assert telegram_pause["manual_off"] is True
    assert "disabled until it is enabled again" in off_result["message"]

    on_result = _update_runtime_control(
        settings,
        {"control": CONTROL_TELEGRAM_ALERTS, "enabled": True},
    )
    telegram_pause = on_result["status"]["runtime_controls"]["pauses"][CONTROL_TELEGRAM_ALERTS]

    assert telegram_pause["paused"] is False
    assert telegram_pause["manual_off"] is False

    interval_result = _update_runtime_control(
        settings,
        {"setting": VALUE_DEMO_LOG_INTERVAL_SECONDS, "seconds": 17},
    )

    assert interval_result["message"] == "Generator interval saved: 17s."
    assert RuntimeControlStore(settings.state_db_path).get_value(VALUE_DEMO_LOG_INTERVAL_SECONDS) == "17"


def test_runtime_extracts_last_chat_message() -> None:
    question = _extract_question(
        {
            "messages": [
                {"role": "system", "content": "ignore system setup"},
                {"role": "user", "content": "tom tat log hom nay"},
            ]
        }
    )

    assert question == "tom tat log hom nay"


def test_telegram_chat_ack_only_marks_pending(tmp_path: Path, monkeypatch) -> None:
    settings = _settings(tmp_path)
    alert_store = AlertStore(settings.state_db_path)
    alert_id = alert_store.upsert_pending_alert(
        event=_log_event(),
        telegram_message_id=10,
        sent_at_ts=205,
        due_at_ts=400,
    )
    sent_messages = []
    responder_calls = []

    monkeypatch.setattr(
        "infra_log_sentinel.notifications.telegram_chat.send_telegram_message",
        lambda settings, text, parse_mode=None: sent_messages.append((text, parse_mode)) or 123,
    )

    result = process_telegram_chat_updates(
        settings=settings,
        alert_store=alert_store,
        updates=[TelegramUpdate(update_id=20, message_date_ts=200, text="ACK")],
        responder=lambda question: responder_calls.append(question) or "answer",
        dry_run=False,
    )

    assert result.processed_count == 1
    assert result.acked_count == 1
    assert result.answered_count == 0
    assert alert_store.get_alert_status(alert_id) == "acknowledged"
    assert alert_store.get_chat_update_id() == 20
    assert alert_store.get_ack_update_id() is None
    assert responder_calls == []
    assert len(sent_messages) == 1
    assert "INFRA-LOG-SENTINEL ACK" in sent_messages[0][0]
    assert sent_messages[0][1] == "HTML"


def test_telegram_chat_question_sends_responder_answer_and_advances_cursor(
    tmp_path: Path,
    monkeypatch,
) -> None:
    settings = _settings(tmp_path)
    alert_store = AlertStore(settings.state_db_path)
    sent_messages = []

    monkeypatch.setattr(
        "infra_log_sentinel.notifications.telegram_chat.send_telegram_message",
        lambda settings, text, parse_mode=None: sent_messages.append((text, parse_mode)) or 123,
    )

    result = process_telegram_chat_updates(
        settings=settings,
        alert_store=alert_store,
        updates=[TelegramUpdate(update_id=21, message_date_ts=200, text="tom tat log hom nay")],
        responder=lambda question: f"answer for: {question}",
        dry_run=False,
    )

    assert result.processed_count == 1
    assert result.acked_count == 0
    assert result.answered_count == 1
    assert alert_store.get_chat_update_id() == 21
    assert alert_store.get_ack_update_id() is None
    assert len(sent_messages) == 1
    assert "INFRA-LOG-SENTINEL" in sent_messages[0][0]
    assert "answer for: tom tat log hom nay" in sent_messages[0][0]
    assert sent_messages[0][1] == "HTML"


def test_ack_job_uses_separate_cursor_from_chat_bridge(tmp_path: Path, monkeypatch) -> None:
    settings = replace(
        _settings(tmp_path),
        telegram_bot_token="123456:realish-token-for-test",
        telegram_chat_id="1234567890",
    )
    alert_store = AlertStore(settings.state_db_path)
    alert_id = alert_store.upsert_pending_alert(
        event=_log_event(),
        telegram_message_id=10,
        sent_at_ts=1000,
        due_at_ts=9999999999,
    )
    alert_store.set_chat_update_id(30)
    offsets = []

    monkeypatch.setattr(
        "infra_log_sentinel.notifications.telegram_sender._fetch_updates",
        lambda token, chat_id, offset, timeout_seconds=0: offsets.append(offset)
        or [
            TelegramUpdate(
                update_id=20,
                message_date_ts=200,
                text="ACK",
                reply_to_message_id=10,
            )
        ],
    )
    monkeypatch.setattr(
        "infra_log_sentinel.notifications.telegram_sender._send_message",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("should not escalate")),
    )

    result = check_ack_and_escalations(settings=settings, alert_store=alert_store)

    assert offsets == [None]
    assert result.acked_count == 1
    assert result.escalated_count == 0
    assert alert_store.get_alert_status(alert_id) == "acknowledged"
    assert alert_store.get_chat_update_id() == 30
    assert alert_store.get_ack_update_id() == 20


def test_telegram_summary_formatter_adds_professional_sections() -> None:
    answer = "\n".join(
        [
            "Tóm tắt theo câu hỏi",
            "- Tổng số event phù hợp: 46",
            "- Theo severity: {'critical': 13, 'error': 16, 'warning': 17}",
            "- Theo domain: {'linux': 10, 'network': 13, 'vmware': 13, 'windows': 10}",
            "",
            "Top alert cần xem:",
            (
                "- [CRITICAL] network/core-rtr01.example.local routing_neighbor_down: "
                "%BGP-5-ADJCHANGE: neighbor 10.255.0.105 Down"
            ),
        ]
    )

    formatted = format_chat_reply_for_telegram("Tóm tắt log hôm nay", answer)

    assert "INFRA-LOG-SENTINEL" in formatted
    assert "Brief" in formatted
    assert "Overview" in formatted
    assert "Priority Findings" in formatted
    assert "Suggested Next Step" in formatted
    assert "🔴 CRITICAL" in formatted


def _log_event() -> LogEvent:
    return LogEvent(
        timestamp="2026-06-12T10:00:00Z",
        domain="network",
        source="core-sw01.example.local",
        severity="critical",
        event_type="power_supply_failure",
        message="Power supply 2 failed or removed",
        raw="raw",
        source_file=Path("network-sample.log"),
        line_number=1,
        probable_cause="Power module failure",
        impact="Redundancy degraded",
        recommended_action="Replace the failed PSU",
    )
