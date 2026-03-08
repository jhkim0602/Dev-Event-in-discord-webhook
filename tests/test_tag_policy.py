from src.models import EventItem, EventMeta
from src.tag_policy import resolve_tags, select_rule_tags


def _event(*, title: str, categories: list[str]) -> EventItem:
    return EventItem(
        event_id="event",
        month_section="26년 03월",
        title=title,
        url="https://example.com",
        canonical_url="https://example.com",
        categories=categories,
        organizer="테스트 주최",
        schedule_label="접수",
        schedule_text="03. 01(일) ~ 03. 10(화)",
    )


def test_select_rule_tags_picks_format_type_and_topic() -> None:
    event = _event(
        title="GitHub Copilot Dev Days (Seoul)",
        categories=["오프라인(서울 종로)", "유료", "AI"],
    )

    assert select_rule_tags(event) == ["오프라인", "컨퍼런스/세미나", "AI"]


def test_select_rule_tags_detects_hackathon() -> None:
    event = _event(
        title="월간 해커톤: 바이브 코딩 개선 AI 아이디어 공모전",
        categories=["온라인", "무료", "대회"],
    )

    assert select_rule_tags(event) == ["온라인", "해커톤", "AI"]


def test_resolve_tags_uses_ai_as_secondary_step(monkeypatch) -> None:
    event = _event(
        title="STK 스마트테크 코리아",
        categories=["오프라인(서울 코엑스)", "무료", "기술일반"],
    )

    def _fake_ai_tags(*args, **kwargs):
        return ["컨퍼런스/세미나"]

    monkeypatch.setattr("src.tag_policy.generate_tag_suggestions", _fake_ai_tags)

    tags = resolve_tags(
        event,
        EventMeta(final_url="https://example.com"),
        api_key="token",
        model="gemini-test",
        timeout_seconds=3,
    )

    assert tags == ["오프라인", "컨퍼런스/세미나"]
