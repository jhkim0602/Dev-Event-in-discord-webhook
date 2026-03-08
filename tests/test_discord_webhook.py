from src.discord_webhook import build_discord_payload
from src.models import AiSummary, EventItem, EventMeta


def _event() -> EventItem:
    return EventItem(
        event_id="event",
        month_section="26년 03월",
        title="GitHub Copilot Dev Days (Seoul)",
        url="https://event-us.kr/powerplatform/event/121503",
        canonical_url="https://event-us.kr/powerplatform/event/121503",
        categories=["오프라인(서울 종로)", "유료", "AI"],
        organizer="AWSKRUG",
        schedule_label="접수",
        schedule_text="02. 15(수) ~ 03. 28(토)",
    )


def _summary() -> AiSummary:
    return AiSummary(
        headline="AI가 정리한 행사 안내",
        summary="GitHub Copilot과 AI 개발 생산성에 관심 있는 개발자에게 맞는 행사로 보여요.",
        who_is_it_for="AI 개발 도구를 실무에 쓰고 싶은 개발자",
        key_points=["오프라인 행사", "개발 생산성 주제", "상세 정보는 원문 참고"],
        cta="참가 전 원문 링크에서 세부 내용을 확인해 주세요.",
    )


def test_build_discord_payload_includes_single_tag_and_image() -> None:
    payload = build_discord_payload(
        _event(),
        _summary(),
        EventMeta(
            final_url="https://event-us.kr/powerplatform/event/121503",
            og_image="https://cdn.example.com/cover.png",
        ),
        source_readme_page_url="https://github.com/brave-people/Dev-Event/blob/master/README.md",
        tag_id="123",
    )

    assert payload["thread_name"] == "GitHub Copilot Dev Days (Seoul)"
    assert payload["applied_tags"] == ["123"]
    assert payload["embeds"][0]["image"]["url"] == "https://cdn.example.com/cover.png"


def test_build_discord_payload_omits_image_when_missing() -> None:
    payload = build_discord_payload(
        _event(),
        _summary(),
        EventMeta(final_url="https://event-us.kr/powerplatform/event/121503"),
        source_readme_page_url="https://github.com/brave-people/Dev-Event/blob/master/README.md",
        tag_id="123",
    )

    assert "image" not in payload["embeds"][0]
