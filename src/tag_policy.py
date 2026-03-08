from __future__ import annotations

from typing import Iterable

from src.gemini_client import generate_tag_suggestions
from src.models import EventItem, EventMeta


ALLOWED_TAGS = [
    "온라인",
    "오프라인",
    "해커톤",
    "공모전/대회",
    "교육/부트캠프",
    "컨퍼런스/세미나",
    "커리어",
    "AI",
    "클라우드",
    "보안",
]

FORMAT_TAGS = {"온라인", "오프라인"}
TYPE_TAGS = {"해커톤", "공모전/대회", "교육/부트캠프", "컨퍼런스/세미나", "커리어"}
TOPIC_TAGS = {"AI", "클라우드", "보안"}


def _contains_any(haystack: str, needles: Iterable[str]) -> bool:
    return any(needle in haystack for needle in needles)


def _normalize(value: str) -> str:
    return " ".join(value.casefold().split())


def _merged_text(event: EventItem) -> str:
    return _normalize(" ".join([event.title, *event.categories, event.organizer or ""]))


def _format_tag(event: EventItem) -> str | None:
    for category in event.categories:
        normalized = _normalize(category)
        if normalized.startswith("온라인"):
            return "온라인"
        if normalized.startswith("오프라인"):
            return "오프라인"
    return None


def _type_tag(event: EventItem) -> str | None:
    text = _merged_text(event)
    if _contains_any(text, ["해커톤", "빌더톤", "hackathon"]):
        return "해커톤"
    if _contains_any(text, ["공모전", "대회", "competition", "contest", "챌린지"]):
        return "공모전/대회"
    if _contains_any(text, ["부트캠프", "교육", "아카데미", "연수생", "캠프", "풀스택", "프론트엔드", "백엔드"]):
        return "교육/부트캠프"
    if _contains_any(text, ["커리어", "취업", "채용", "멘토단", "리쿠르팅"]):
        return "커리어"
    if _contains_any(text, ["컨퍼런스", "세미나", "포럼", "conf", "서밋", "summit", "설명회", "dev days", "데브데이"]):
        return "컨퍼런스/세미나"
    return None


def _topic_tags(event: EventItem) -> list[str]:
    text = _merged_text(event)
    selected: list[str] = []
    if _contains_any(text, ["ai", "copilot", "llm", "agent", "gpt"]):
        selected.append("AI")
    if _contains_any(text, ["클라우드", "cloud", "aws", "serverless", "devops", "kubernetes", "k8s"]):
        selected.append("클라우드")
    if _contains_any(text, ["보안", "security", ".hack", "hack ", "사이버"]):
        selected.append("보안")
    return selected


def select_rule_tags(event: EventItem) -> list[str]:
    tags: list[str] = []
    format_tag = _format_tag(event)
    if format_tag:
        tags.append(format_tag)

    type_tag = _type_tag(event)
    if type_tag and type_tag not in tags:
        tags.append(type_tag)

    for tag in _topic_tags(event):
        if tag not in tags:
            tags.append(tag)

    return tags[:3]


def resolve_tags(
    event: EventItem,
    meta: EventMeta,
    *,
    api_key: str | None,
    model: str,
    timeout_seconds: int,
) -> list[str]:
    selected = select_rule_tags(event)
    if len(selected) >= 3:
        return selected[:3]

    ai_tags = generate_tag_suggestions(
        event,
        meta,
        allowed_tags=ALLOWED_TAGS,
        existing_tags=selected,
        api_key=api_key,
        model=model,
        timeout_seconds=timeout_seconds,
    )

    for tag in ai_tags:
        if tag not in selected:
            selected.append(tag)
        if len(selected) == 3:
            break

    return selected[:3]
