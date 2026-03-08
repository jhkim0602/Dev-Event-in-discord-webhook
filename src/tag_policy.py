from __future__ import annotations

import re
from datetime import datetime, time

from src.models import EventItem


DATE_PATTERN = re.compile(r"(\d{2})\.\s*(\d{2})\([^)]+\)(?:\s*(\d{1,2}:\d{2}))?")
MONTH_SECTION_PATTERN = re.compile(r"(?P<year>\d{2})년\s+(?P<month>\d{2})월")


def _infer_base_year(month_section: str) -> int:
    match = MONTH_SECTION_PATTERN.search(month_section)
    if not match:
        raise ValueError(f"Unable to infer year from month section: {month_section}")
    return 2000 + int(match.group("year"))


def extract_schedule_end(event: EventItem, now: datetime) -> datetime | None:
    if not event.schedule_text:
        return None

    matches = DATE_PATTERN.findall(event.schedule_text)
    if not matches:
        return None

    start_month = int(matches[0][0])
    end_month, end_day, end_time = matches[-1]

    year = _infer_base_year(event.month_section)
    end_month_int = int(end_month)
    if end_month_int < start_month:
        year += 1

    if end_time:
        hour, minute = map(int, end_time.split(":"))
        schedule_time = time(hour=hour, minute=minute)
    else:
        schedule_time = time(hour=23, minute=59, second=59)

    return datetime(
        year=year,
        month=end_month_int,
        day=int(end_day),
        hour=schedule_time.hour,
        minute=schedule_time.minute,
        second=schedule_time.second,
        tzinfo=now.tzinfo,
    )


def resolve_tag(event: EventItem, now: datetime) -> str:
    end_at = extract_schedule_end(event, now)
    if end_at is None:
        return "모집중"
    return "모집중" if end_at >= now else "모집종료"
