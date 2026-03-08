from __future__ import annotations

import re

from src.identity import build_event_id
from src.models import EventItem


MONTH_PATTERN = re.compile(r"^##\s+`([^`]+)`\s*$")
EVENT_PATTERN = re.compile(r"^-\s+__\[(.+?)\]\((.+?)\)__\s*$")
COMMENT_PATTERN = re.compile(r"<!--.*?-->", re.DOTALL)


def _clean_metadata_value(value: str) -> str:
    return value.replace("`", "").strip()


def _parse_categories(value: str) -> list[str]:
    return [part.strip() for part in _clean_metadata_value(value).split(",") if part.strip()]


def _finalize_event(month_section: str | None, current: dict[str, object] | None) -> EventItem | None:
    if not month_section or not current:
        return None
    title = str(current["title"])
    url = str(current["url"])
    organizer = current.get("organizer")
    event_id, canonical_url = build_event_id(title, url, organizer if isinstance(organizer, str) else None)
    return EventItem(
        event_id=event_id,
        month_section=month_section,
        title=title,
        url=url,
        canonical_url=canonical_url,
        categories=list(current.get("categories", [])),
        organizer=organizer if isinstance(organizer, str) else None,
        schedule_label=current.get("schedule_label") if isinstance(current.get("schedule_label"), str) else None,
        schedule_text=current.get("schedule_text") if isinstance(current.get("schedule_text"), str) else None,
    )


def parse_events(readme_text: str) -> list[EventItem]:
    cleaned = COMMENT_PATTERN.sub("", readme_text)
    source = cleaned.split("## 지난 행사 기록", 1)[0]

    events: list[EventItem] = []
    current_month: str | None = None
    current_event: dict[str, object] | None = None

    for raw_line in source.splitlines():
        line = raw_line.rstrip()
        month_match = MONTH_PATTERN.match(line.strip())
        if month_match:
            finalized = _finalize_event(current_month, current_event)
            if finalized:
                events.append(finalized)
            current_event = None
            current_month = month_match.group(1).strip()
            continue

        event_match = EVENT_PATTERN.match(line.strip())
        if event_match:
            finalized = _finalize_event(current_month, current_event)
            if finalized:
                events.append(finalized)
            current_event = {
                "title": event_match.group(1).strip(),
                "url": event_match.group(2).strip(),
                "categories": [],
            }
            continue

        if not current_event:
            continue

        stripped = line.strip()
        if stripped.startswith("- 분류:"):
            current_event["categories"] = _parse_categories(stripped.split(":", 1)[1])
        elif stripped.startswith("- 주최:"):
            current_event["organizer"] = _clean_metadata_value(stripped.split(":", 1)[1]) or None
        elif stripped.startswith("- 접수:"):
            current_event["schedule_label"] = "접수"
            current_event["schedule_text"] = _clean_metadata_value(stripped.split(":", 1)[1]) or None
        elif stripped.startswith("- 일시:"):
            current_event["schedule_label"] = "일시"
            current_event["schedule_text"] = _clean_metadata_value(stripped.split(":", 1)[1]) or None

    finalized = _finalize_event(current_month, current_event)
    if finalized:
        events.append(finalized)

    return events
