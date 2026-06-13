from __future__ import annotations

from collections import Counter
import re

from infra_log_sentinel.analysis.time_window import filter_events_by_lookback
from infra_log_sentinel.chat.actions import try_execute_chat_action
from infra_log_sentinel.chat.conversation import ConversationSnapshot, ConversationStore
from infra_log_sentinel.chat.intent import (
    INTENT_ASSISTANT_FEEDBACK,
    INTENT_GENERAL_QUESTION,
    classify_chat_intent,
    normalize_text,
)
from infra_log_sentinel.chat.llm_assistant import answer_with_llm
from infra_log_sentinel.chat.log_chat import answer_log_question, should_answer_with_rules_first
from infra_log_sentinel.config import Settings
from infra_log_sentinel.ingestion.local_folder import iter_log_lines
from infra_log_sentinel.models import LogEvent
from infra_log_sentinel.parsing.log_parser import parse_raw_lines


SEVERITY_ORDER = ("critical", "error", "warning", "info")
DOMAIN_ORDER = ("network", "linux", "windows", "vmware")


def answer_or_execute_chat(
    settings: Settings,
    question: str,
    dry_run: bool = False,
    channel: str = "default",
) -> str:
    conversation_channel = channel.strip() if channel.strip() else "default"
    conversation_store = ConversationStore(settings.state_db_path)
    context = conversation_store.get(conversation_channel)
    raw_lines = list(iter_log_lines(settings.log_root_path))
    events = parse_raw_lines(raw_lines)
    intent = classify_chat_intent(question)

    if intent.kind == INTENT_ASSISTANT_FEEDBACK:
        return _remember_and_return(
            conversation_store=conversation_store,
            channel=conversation_channel,
            question=question,
            answer=_answer_assistant_feedback(),
            intent=intent.kind,
        )

    command_explanation = _answer_command_explanation_if_requested(question)
    if command_explanation:
        return _remember_and_return(
            conversation_store=conversation_store,
            channel=conversation_channel,
            question=question,
            answer=command_explanation,
            intent=intent.kind,
            action="command_explanation",
        )

    inline_report = _answer_inline_report_if_requested(
        settings=settings,
        events=events,
        question=question,
        context=context,
    )
    if inline_report:
        return _remember_and_return(
            conversation_store=conversation_store,
            channel=conversation_channel,
            question=question,
            answer=inline_report,
            intent=intent.kind if intent.kind else INTENT_GENERAL_QUESTION,
            action="inline_report",
            artifact_path=context.last_artifact_path,
        )

    if intent.action_candidate:
        action_result = try_execute_chat_action(
            settings=settings,
            events=events,
            question=question,
            dry_run=dry_run,
        )
        if action_result.handled:
            action = _infer_action_name(question, action_result.message)
            return _remember_and_return(
                conversation_store=conversation_store,
                channel=conversation_channel,
                question=question,
                answer=action_result.message,
                intent=intent.kind,
                action=action,
                artifact_path=_extract_artifact_path(action_result.message),
            )

    if intent.rules_first or should_answer_with_rules_first(question):
        return _remember_and_return(
            conversation_store=conversation_store,
            channel=conversation_channel,
            question=question,
            answer=answer_log_question(events, question, settings.severity_alert_levels),
            intent=intent.kind,
        )

    llm_answer = answer_with_llm(settings, events, question, settings.severity_alert_levels)
    if llm_answer:
        return _remember_and_return(
            conversation_store=conversation_store,
            channel=conversation_channel,
            question=question,
            answer=llm_answer,
            intent=intent.kind,
        )

    return _remember_and_return(
        conversation_store=conversation_store,
        channel=conversation_channel,
        question=question,
        answer=_answer_general_fallback(),
        intent=intent.kind,
    )


def _answer_inline_report_if_requested(
    settings: Settings,
    events: list[LogEvent],
    question: str,
    context: ConversationSnapshot,
) -> str:
    if not _looks_like_inline_report_request(question):
        return ""
    return _inline_chat_report(settings, events, context)


def _answer_command_explanation_if_requested(question: str) -> str:
    q = normalize_text(question)
    if not _looks_like_command_explanation_request(q):
        return ""

    command = _extract_command_from_question(question)
    if not command:
        return ""
    return _explain_command(command)


def _looks_like_command_explanation_request(q: str) -> bool:
    explanation_terms = (
        "khong hieu lenh",
        "khong hieu command",
        "lenh nay dung de lam gi",
        "command nay dung de lam gi",
        "dung de lam gi",
        "giai thich y nghia",
        "giai thich lenh",
        "giai thich command",
        "y nghia cua",
        "what does",
        "explain command",
        "explain this command",
        "meaning of",
    )
    if not any(term in q for term in explanation_terms):
        return False
    return _extract_command_from_question(q) != "" or _extract_command_from_question(q.replace('"', "")) != ""


def _extract_command_from_question(question: str) -> str:
    for pattern in (r"`([^`]+)`", r'"([^"]+)"', r"'([^']+)'"):
        match = re.search(pattern, question)
        if match:
            candidate = match.group(1).strip()
            if _looks_like_shell_command(candidate):
                return candidate

    command_names = (
        "Get-Service",
        "Restart-Service",
        "Start-Service",
        "Stop-Service",
        "Get-WinEvent",
        "Get-EventLog",
        "Get-Process",
        "Get-Content",
        "Select-String",
        "Where-Object",
        "Test-NetConnection",
        "systemctl",
        "journalctl",
        "grep",
        "tail",
    )
    command_pattern = r"(?i)\b(" + "|".join(re.escape(name) for name in command_names) + r")\b[^\n`\"']*"
    match = re.search(command_pattern, question)
    if not match:
        return ""

    command = match.group(0).strip()
    command = re.sub(r"[.?!,;:]+$", "", command).strip()
    return command if _looks_like_shell_command(command) else ""


def _looks_like_shell_command(value: str) -> bool:
    normalized = value.strip().lower()
    return bool(
        re.match(
            r"^(get|restart|start|stop|set|new|remove|test)-[a-z0-9-]+\b",
            normalized,
        )
        or normalized.startswith(("systemctl ", "journalctl ", "grep ", "tail "))
    )


def _explain_command(command: str) -> str:
    command = command.strip()
    cmdlet = command.split()[0] if command.split() else command
    normalized_cmdlet = cmdlet.lower()
    args = command.split()[1:]
    target = " ".join(args).strip()

    intro = [
        "Mình hiểu câu này là yêu cầu giải thích command, không phải yêu cầu sinh thêm runbook.",
        "",
        f"Command: `{command}`",
        "",
    ]

    if normalized_cmdlet == "get-service":
        target_text = target or "<service-name>"
        lines = intro + [
            "Ý nghĩa:",
            "- `Get-Service` là PowerShell cmdlet dùng để xem thông tin Windows Service.",
            f"- `{target_text}` là tên service muốn kiểm tra.",
            "- Kết quả thường cho biết service đang `Running`, `Stopped`, hoặc không tồn tại.",
            "",
            "Dùng khi nào:",
            "- Kiểm tra nhanh service có đang chạy không trước khi điều tra hoặc restart.",
            "- Với SQL Server Agent, tên service thực tế có thể là `SQLSERVERAGENT` hoặc `SQLAgent$<instance>` tùy cách cài đặt.",
            "",
            "Cách kiểm tra rộng hơn nếu tên service chưa chắc:",
            "`Get-Service *SQL*Agent*`",
        ]
        return "\n".join(lines)

    if normalized_cmdlet == "restart-service":
        target_text = target or "<service-name>"
        return "\n".join(
            intro
            + [
                "Ý nghĩa:",
                "- `Restart-Service` dừng rồi khởi động lại một Windows Service.",
                f"- `{target_text}` là service bị restart.",
                "",
                "Lưu ý vận hành:",
                "- Đây là lệnh có tác động thật, có thể làm gián đoạn dịch vụ.",
                "- Chỉ chạy sau khi xác nhận dependency, change window và ảnh hưởng ứng dụng.",
            ]
        )

    if normalized_cmdlet == "get-winevent":
        return "\n".join(
            intro
            + [
                "Ý nghĩa:",
                "- `Get-WinEvent` đọc Windows Event Log.",
                "- `-FilterHashtable` lọc log theo điều kiện như log name, event id, thời gian.",
                "- Ví dụ `Id=7031` thường dùng để tìm sự kiện service bị crash/terminated.",
                "",
                "Dùng khi nào:",
                "- Điều tra service failure gần đây thay vì xem toàn bộ Event Viewer thủ công.",
            ]
        )

    if normalized_cmdlet == "get-eventlog":
        return "\n".join(
            intro
            + [
                "Ý nghĩa:",
                "- `Get-EventLog` đọc Windows Event Log kiểu cũ.",
                "- `-LogName Application` chọn log Application.",
                "- `-Newest 50` lấy 50 event mới nhất.",
                "- Nếu có `Where-Object`, phần sau dùng để lọc message theo từ khóa.",
                "",
                "Dùng khi nào:",
                "- Tìm lỗi ứng dụng liên quan tới service hoặc process cụ thể.",
            ]
        )

    return "\n".join(
        intro
        + [
            "Ý nghĩa tổng quát:",
            f"- `{cmdlet}` là command chính.",
            f"- Phần sau command (`{target}`) là tham số/đối tượng mà command thao tác." if target else "- Command này chưa có tham số cụ thể.",
            "",
            "Nếu anh muốn, hãy gửi thêm output của command đó; mình sẽ giải thích từng cột/kết quả cụ thể.",
        ]
    )


def _looks_like_inline_report_request(question: str) -> bool:
    q = normalize_text(question)
    if not any(term in q for term in ("report", "bao cao")):
        return False

    explicit_mail_delivery = any(term in q for term in ("gmail", "email", "mail")) and not any(
        term in q for term in ("khong gui", "dung gui", "khong can gui")
    )
    if explicit_mail_delivery:
        return False

    chat_surface_terms = (
        "giao dien chat",
        "trong chat",
        "o chat",
        "tai chat",
        "tren chat",
        "tai giao dien",
        "trong giao dien",
        "hien thi tai day",
        "hien thi o day",
        "hien thi tren chat",
        "tra loi tai day",
        "noi dung tai day",
        "inline",
        "in chat",
        "chat ui",
    )
    return any(term in q for term in chat_surface_terms)


def _inline_chat_report(
    settings: Settings,
    events: list[LogEvent],
    context: ConversationSnapshot,
) -> str:
    recent_events = filter_events_by_lookback(
        events,
        lookback_hours=settings.report_lookback_hours,
    )
    alert_levels = set(settings.severity_alert_levels)
    alert_events = _sort_events([event for event in recent_events if event.severity in alert_levels])
    priority_events = alert_events if alert_events else _sort_events(recent_events)

    if context.last_action in {"report", "email_report"}:
        lead = (
            "Đã hiểu đây là câu nối tiếp của report vừa rồi. "
            "Mình sẽ hiển thị report ngay trong chat, không tạo PDF mới và không gửi Gmail."
        )
    else:
        lead = "Đã hiểu: report sẽ hiển thị ngay trong chat, không tạo PDF và không gửi Gmail."

    lines = [
        lead,
        "",
        "INFRA-LOG-SENTINEL Chat Report",
        f"- Window: {settings.report_lookback_hours} giờ gần nhất",
        f"- Total events: {len(recent_events)}",
        f"- Severity: {_format_counts(Counter(event.severity for event in recent_events), SEVERITY_ORDER, upper=True)}",
        f"- Domain: {_format_counts(Counter(event.domain for event in recent_events), DOMAIN_ORDER)}",
    ]
    if context.last_artifact_path:
        lines.append(f"- File trước đó: {context.last_artifact_path}")

    lines.extend(["", "Top alert cần ưu tiên:"])
    if not priority_events:
        lines.append("- Không có event phù hợp trong cửa sổ report.")
    else:
        for index, event in enumerate(priority_events[:7], start=1):
            lines.append(
                f"{index}. [{event.severity.upper()}] {event.domain}/{event.source} "
                f"{event.event_type}: {event.message}"
            )

    lines.extend(
        [
            "",
            "Gợi ý tiếp theo:",
            "- Hỏi `command xử lý <domain/type>` nếu cần runbook cụ thể.",
            "- Hỏi `xuất PDF report` nếu thật sự muốn tạo file.",
            "- Hỏi `gửi report qua Gmail` nếu muốn delivery qua mail.",
        ]
    )
    return "\n".join(lines)


def _sort_events(events: list[LogEvent]) -> list[LogEvent]:
    severity_rank = {severity: index for index, severity in enumerate(SEVERITY_ORDER)}
    return sorted(
        events,
        key=lambda event: (
            severity_rank.get(event.severity, 99),
            event.domain,
            event.source,
            event.event_type,
        ),
    )


def _format_counts(counter: Counter[str], order: tuple[str, ...], upper: bool = False) -> str:
    parts = []
    for name in order:
        count = counter.get(name, 0)
        if count:
            label = name.upper() if upper else name
            parts.append(f"{label} {count}")
    for name, count in sorted(counter.items()):
        if name not in order and count:
            label = name.upper() if upper else name
            parts.append(f"{label} {count}")
    return " | ".join(parts) if parts else "none"


def _infer_action_name(question: str, answer: str) -> str:
    normalized = normalize_text(" ".join([question, answer]))
    if "runtime control" in normalized or "tam dung" in normalized or "bat lai" in normalized:
        return "runtime_control"
    if "gmail" in normalized or "email" in normalized or "mail" in normalized:
        return "email_report"
    if "csv" in normalized:
        return "export_csv"
    if "pdf" in normalized or "report" in normalized or "bao cao" in normalized:
        return "report"
    return ""


def _extract_artifact_path(answer: str) -> str:
    match = re.search(r"(?im)^-\s*File:\s*(.+?)\s*$", answer)
    return match.group(1).strip() if match else ""


def _remember_and_return(
    conversation_store: ConversationStore,
    channel: str,
    question: str,
    answer: str,
    intent: str,
    action: str = "",
    artifact_path: str = "",
) -> str:
    try:
        conversation_store.update(
            channel=channel,
            user_message=question,
            agent_message=answer,
            intent=intent,
            action=action,
            artifact_path=artifact_path,
        )
    except Exception:
        pass
    return answer


def _answer_assistant_feedback() -> str:
    return (
        "Bạn nói đúng. Đây là phản hồi về cách mình hiểu câu hỏi, không phải yêu cầu truy vấn hay xuất log.\n\n"
        "Mình sẽ xử lý theo nguyên tắc mới:\n"
        "- Chỉ liệt kê log khi bạn hỏi rõ về dữ liệu log, ví dụ `có warning nào hôm nay?`.\n"
        "- Nếu bạn đang hỏi hoặc góp ý với bot, mình trả lời trực tiếp vào ý đó.\n"
        "- Nếu câu có thể hiểu theo nhiều hướng, mình hỏi lại trước thay vì tự suy diễn.\n\n"
        "Bạn có thể hỏi lại câu muốn mình trả lời; mình sẽ không tự động xuất danh sách warning từ câu phản hồi này."
    )


def _answer_general_fallback() -> str:
    return (
        "Mình chưa đủ chắc đây là câu hỏi về log, runbook hay thao tác runtime, nên mình sẽ không tự xuất alert.\n\n"
        "Bạn có thể hỏi theo một trong ba hướng:\n"
        "- Hỏi log: `tóm tắt log hôm nay`, `có critical network nào không?`\n"
        "- Hỏi xử lý: `command xử lý vmware warning`\n"
        "- Thao tác: `xuất báo cáo PDF 24 giờ gần nhất`\n\n"
        "Nếu đây là câu hỏi hội thoại bình thường, hãy nói rõ nội dung bạn muốn mình trả lời."
    )
