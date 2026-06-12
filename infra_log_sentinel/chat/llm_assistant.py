from __future__ import annotations

from collections import Counter
from typing import Any

import requests

from infra_log_sentinel.analysis.runbook import recommend_commands
from infra_log_sentinel.config import Settings
from infra_log_sentinel.models import LogEvent


def answer_with_llm(
    settings: Settings,
    events: list[LogEvent],
    question: str,
    alert_levels: tuple[str, ...],
) -> str | None:
    if not _llm_is_configured(settings):
        return None

    payload = {
        "model": settings.llm_model,
        "messages": [
            {
                "role": "system",
                "content": _system_prompt(),
            },
            {
                "role": "user",
                "content": _user_prompt(events=events, question=question, alert_levels=alert_levels),
            },
        ],
        "temperature": 0.2,
        "max_tokens": 1800,
    }
    headers = {
        "Authorization": f"Bearer {settings.llm_api_key}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            _chat_completions_url(settings.llm_api_base),
            headers=headers,
            json=payload,
            timeout=45,
        )
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError) as exc:
        return (
            "Mình chưa gọi được LLM để trả lời theo kiểu ChatGPT, nên đang dùng logic phân tích nội bộ.\n"
            f"LLM error: {type(exc).__name__}: {exc}"
        )

    answer = _extract_answer(data)
    if not answer:
        return None
    return answer.strip()


def _llm_is_configured(settings: Settings) -> bool:
    return all(
        [
            settings.llm_api_base.strip(),
            settings.llm_api_key.strip(),
            settings.llm_model.strip(),
        ]
    )


def _chat_completions_url(base_url: str) -> str:
    base = base_url.strip().rstrip("/")
    if base.endswith("/chat/completions"):
        return base
    if base.endswith("/v1"):
        return f"{base}/chat/completions"
    return f"{base}/v1/chat/completions"


def _extract_answer(data: dict[str, Any]) -> str:
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        return ""
    first = choices[0]
    if not isinstance(first, dict):
        return ""
    message = first.get("message")
    if isinstance(message, dict) and isinstance(message.get("content"), str):
        return message["content"]
    if isinstance(first.get("text"), str):
        return first["text"]
    return ""


def _system_prompt() -> str:
    return (
        "You are Infra Log Sentinel Agent, a senior infrastructure and network operations assistant. "
        "Answer in Vietnamese unless the user asks otherwise. Be conversational like ChatGPT, but stay grounded "
        "in the provided log context and runbook commands. Think like an SRE operator, not a keyword bot. "
        "Classify each user message first: informational question, log investigation, runtime action, or "
        "ambiguous/high-impact operational change. If the user asks to change, pause, resume, send, schedule, "
        "configure, escalate, or notify but omits the target, value, time window, channel, or confirmation, ask "
        "one concise clarifying question and offer 2-4 concrete options. Do not guess operational intent. "
        "If the exact log is not present, say that clearly, then provide the safest likely investigation path. "
        "Never invent alert counts, hosts, or commands that conflict with the context. For operational questions, "
        "include concrete verification commands and a short recommended next action. Do not use emoji. Use clear "
        "Markdown headings, bold emphasis for severity or impact, and fenced code blocks for commands so the UI "
        "can render copy buttons."
    )


def _user_prompt(events: list[LogEvent], question: str, alert_levels: tuple[str, ...]) -> str:
    alert_set = set(alert_levels)
    alert_events = [event for event in events if event.severity in alert_set]
    severity_counts = Counter(event.severity for event in events)
    domain_counts = Counter(event.domain for event in events)
    matching_events = _rank_relevant_events(events, question)
    context_events = matching_events[:8] if matching_events else alert_events[:8]

    lines = [
        f"User question: {question}",
        "",
        "Current log batch summary:",
        f"- Total parsed events: {len(events)}",
        f"- Severity counts: {dict(sorted(severity_counts.items()))}",
        f"- Domain counts: {dict(sorted(domain_counts.items()))}",
        "",
        "Relevant events and runbook context:",
    ]
    if not context_events:
        lines.append("- No parsed events available.")
    for index, event in enumerate(context_events, start=1):
        lines.extend(
            [
                f"{index}. [{event.severity.upper()}] {event.domain}/{event.source} - {event.event_type}",
                f"   Log: {event.message}",
                f"   Probable cause: {event.probable_cause}",
                f"   Impact: {event.impact}",
                f"   Recommended action: {event.recommended_action}",
                "   Commands:",
            ]
        )
        for command in recommend_commands(event)[:5]:
            lines.append(f"   - {command.phase}: {command.command} ({command.purpose})")

    lines.extend(
        [
            "",
            "Instructions for answer:",
            "- Start with the direct answer.",
            "- Keep the answer concise enough for a chat UI, usually under 900 Vietnamese words.",
            "- If the user asks for commands, provide commands grouped by Verify, Investigate, Remediate.",
            "- Put command examples inside fenced code blocks with language `powershell`, `bash`, or `text`.",
            "- If the user asks a broad question, summarize what the current logs suggest and what to do next.",
            "- If the user asks to change runtime behavior but misses target/value/time/channel, ask a concise clarification before recommending any action.",
            "- For ambiguous words like interval, schedule, threshold, pause, resume, send, report, alert, or it/that, explain what you need clarified.",
            "- If context does not contain an exact match, say so and provide a safe general approach.",
        ]
    )
    return "\n".join(lines)


def _rank_relevant_events(events: list[LogEvent], question: str) -> list[LogEvent]:
    q_terms = _keywords(question)
    if not q_terms:
        return []

    scored: list[tuple[int, LogEvent]] = []
    for event in events:
        haystack = " ".join(
            [
                event.domain,
                event.source,
                event.severity,
                event.event_type.replace("_", " "),
                event.message,
                event.probable_cause,
                event.impact,
                event.recommended_action,
            ]
        ).lower()
        score = sum(1 for term in q_terms if term in haystack)
        if "host memory usage" in question.lower() and "host memory usage" in haystack:
            score += 8
        if score:
            scored.append((score, event))
    return [event for _, event in sorted(scored, key=lambda item: (-item[0], item[1].domain, item[1].source))]


def _keywords(question: str) -> list[str]:
    raw_terms = [term.lower() for term in question.replace("_", " ").split()]
    stop_words = {
        "toi",
        "tôi",
        "hay",
        "cho",
        "can",
        "cần",
        "command",
        "xu",
        "xử",
        "ly",
        "lý",
        "loi",
        "lỗi",
        "the",
        "and",
        "is",
        "are",
        "what",
        "how",
    }
    terms = [term.strip(".,:;!?()[]{}\"'`") for term in raw_terms]
    terms = [term for term in terms if len(term) >= 3 and term not in stop_words]
    if "host memory usage" in question.lower():
        terms.append("host memory usage")
    return list(dict.fromkeys(terms))
