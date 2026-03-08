from pathlib import Path

from src.identity import dedupe_events
from src.readme_parser import parse_events


FIXTURE = Path(__file__).parent / "fixtures" / "sample_readme.md"


def test_parse_events_ignores_comments_and_past_section() -> None:
    events = parse_events(FIXTURE.read_text(encoding="utf-8"))

    assert [event.month_section for event in events] == ["26년 03월", "26년 03월", "26년 03월", "26년 04월"]
    assert events[0].title == "월간 해커톤: 바이브 코딩 개선 AI 아이디어 공모전"
    assert events[0].categories == ["온라인", "무료", "대회"]
    assert events[0].schedule_label == "접수"
    assert all("과거 행사" != event.title for event in events)


def test_dedupe_events_keeps_first_duplicate() -> None:
    events = parse_events(FIXTURE.read_text(encoding="utf-8"))
    deduped = dedupe_events(events)

    assert len(deduped) == 3
    assert deduped[1].title == "AWSKRUG 데브옵스 #DevOps 소모임 21번째 밋업"
