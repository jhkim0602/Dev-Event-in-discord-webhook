from datetime import datetime
from zoneinfo import ZoneInfo

from src.main import current_month_label, seed_unposted_events, select_events_to_post
from src.models import EventItem, State


KST = ZoneInfo("Asia/Seoul")


def _event(month_section: str, suffix: str) -> EventItem:
    return EventItem(
        event_id=f"event-{suffix}",
        month_section=month_section,
        title=f"행사 {suffix}",
        url=f"https://example.com/{suffix}",
        canonical_url=f"https://example.com/{suffix}",
        categories=["온라인"],
        organizer="테스트",
        schedule_label="접수",
        schedule_text="03. 01(일) ~ 03. 10(화)",
    )


def test_bootstrap_posts_only_current_month_and_seeds_rest() -> None:
    now = datetime(2026, 3, 8, 12, 0, tzinfo=KST)
    events = [_event("26년 03월", "march"), _event("26년 04월", "april")]
    state = State()

    to_post, baseline_only = select_events_to_post(events, state, now)
    seed_unposted_events(state, baseline_only)

    assert current_month_label(now) == "26년 03월"
    assert [event.event_id for event in to_post] == ["event-march"]
    assert [event.event_id for event in baseline_only] == ["event-april"]
    assert state.events["event-april"].posted is False
