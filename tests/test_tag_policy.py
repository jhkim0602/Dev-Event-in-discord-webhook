from datetime import datetime
from zoneinfo import ZoneInfo

from src.models import EventItem
from src.tag_policy import extract_schedule_end, resolve_tag


KST = ZoneInfo("Asia/Seoul")


def _event(*, month_section: str, schedule_label: str | None, schedule_text: str | None) -> EventItem:
    return EventItem(
        event_id="event",
        month_section=month_section,
        title="테스트 행사",
        url="https://example.com",
        canonical_url="https://example.com",
        categories=["온라인"],
        organizer="테스트",
        schedule_label=schedule_label,
        schedule_text=schedule_text,
    )


def test_resolve_tag_uses_reception_end_date() -> None:
    event = _event(month_section="26년 03월", schedule_label="접수", schedule_text="02. 04(수) ~ 03. 09(월)")
    now = datetime(2026, 3, 8, 12, 0, tzinfo=KST)
    assert resolve_tag(event, now) == "모집중"


def test_resolve_tag_marks_closed_after_event_end() -> None:
    event = _event(month_section="26년 04월", schedule_label="일시", schedule_text="02. 06(금) ~ 04. 21(화)")
    now = datetime(2026, 4, 22, 0, 0, tzinfo=KST)
    assert resolve_tag(event, now) == "모집종료"


def test_extract_schedule_end_preserves_explicit_time() -> None:
    event = _event(month_section="26년 03월", schedule_label="접수", schedule_text="02. 13(금) ~ 03. 12(목) 17:00")
    now = datetime(2026, 3, 1, 0, 0, tzinfo=KST)
    end_at = extract_schedule_end(event, now)
    assert end_at == datetime(2026, 3, 12, 17, 0, tzinfo=KST)
