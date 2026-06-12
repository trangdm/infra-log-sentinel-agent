from __future__ import annotations

from datetime import datetime, timedelta

from infra_log_sentinel.models import LogEvent


LINUX_SYSLOG_FORMAT = "%b %d %H:%M:%S"


def filter_events_by_lookback(
    events: list[LogEvent],
    lookback_hours: int,
    reference_time: datetime | None = None,
) -> list[LogEvent]:
    reference_time = reference_time or datetime.now().astimezone()
    start_time = reference_time - timedelta(hours=lookback_hours)
    return [
        event
        for event in events
        if _event_in_window(event, start_time=start_time, end_time=reference_time)
    ]


def parse_event_timestamp(event: LogEvent, reference_time: datetime | None = None) -> datetime | None:
    reference_time = reference_time or datetime.now().astimezone()
    timestamp = event.timestamp.strip()
    if not timestamp or timestamp == "unknown":
        return None

    try:
        parsed = datetime.fromisoformat(timestamp)
        if parsed.tzinfo is None and reference_time.tzinfo is not None:
            parsed = parsed.replace(tzinfo=reference_time.tzinfo)
        return parsed
    except ValueError:
        pass

    try:
        parsed = datetime.strptime(timestamp, LINUX_SYSLOG_FORMAT)
        parsed = parsed.replace(year=reference_time.year)
        if reference_time.tzinfo is not None:
            parsed = parsed.replace(tzinfo=reference_time.tzinfo)
        return parsed
    except ValueError:
        return None


def _event_in_window(event: LogEvent, start_time: datetime, end_time: datetime) -> bool:
    event_time = parse_event_timestamp(event, reference_time=end_time)
    if event_time is None:
        return False

    if start_time.tzinfo is not None and event_time.tzinfo is None:
        event_time = event_time.replace(tzinfo=start_time.tzinfo)
    if start_time.tzinfo is None and event_time.tzinfo is not None:
        start_time = start_time.replace(tzinfo=event_time.tzinfo)
        end_time = end_time.replace(tzinfo=event_time.tzinfo)

    return start_time <= event_time <= end_time
