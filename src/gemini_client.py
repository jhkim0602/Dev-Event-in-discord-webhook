from __future__ import annotations

import json
import logging
from typing import Any
import urllib.error
import urllib.request

from src.models import AiSummary, EventItem, EventMeta


logger = logging.getLogger(__name__)


def _truncate(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    return value[: limit - 1].rstrip() + "…"


def build_fallback_summary(event: EventItem) -> AiSummary:
    schedule_label = event.schedule_label or "일정"
    schedule_text = event.schedule_text or "상세 일정은 원문 링크를 확인해 주세요."
    categories = ", ".join(event.categories) or "-"
    return AiSummary(
        headline=_truncate(event.title, 80),
        summary="이 행사를 자동으로 정리했어요.",
        who_is_it_for="상세 참여 대상과 조건은 원문 링크에서 확인해 주세요.",
        key_points=[
            f"주최: {event.organizer or '-'}",
            f"분류: {categories}",
            f"{schedule_label}: {schedule_text}",
        ],
        cta="자세한 내용은 원문 링크를 확인해 주세요.",
        used_fallback=True,
    )


def _prompt(event: EventItem, meta: EventMeta, *, stricter: bool) -> str:
    retry_guard = (
        "반드시 JSON 객체만 응답하세요. 코드펜스, 설명문, 마크다운을 절대 추가하지 마세요."
        if stricter
        else "응답은 반드시 JSON 객체 하나로만 작성하세요."
    )
    return f"""
당신은 개발자 행사 정보를 안내하는 한국어 챗봇입니다.
과장하지 말고, 제공된 정보 안에서만 요약하세요.
없는 사실을 추측하지 마세요.
일정, 장소, 혜택, 참가 조건을 임의로 만들지 마세요.
{retry_guard}

출력 JSON 스키마:
{{
  "headline": "40자 이내",
  "summary": "120자 이내",
  "who_is_it_for": "60자 이내",
  "key_points": ["문장 1", "문장 2", "문장 3"],
  "cta": "50자 이내"
}}

입력 정보:
- 제목: {event.title}
- 분류: {", ".join(event.categories) if event.categories else "-"}
- 주최: {event.organizer or "-"}
- {event.schedule_label or "일정"}: {event.schedule_text or "-"}
- 행사 링크: {meta.final_url or event.url}
- og:title: {meta.og_title or "-"}
- og:description: {meta.og_description or "-"}
""".strip()


def _call_gemini(api_key: str, model: str, prompt: str, *, timeout_seconds: int) -> dict[str, Any]:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.3,
            "responseMimeType": "application/json",
        },
    }
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        return json.loads(response.read().decode("utf-8"))


def _extract_text(payload: dict[str, Any]) -> str:
    candidates = payload.get("candidates", [])
    if not candidates:
        raise ValueError("Gemini response contained no candidates")
    parts = candidates[0].get("content", {}).get("parts", [])
    if not parts:
        raise ValueError("Gemini response contained no parts")
    text = parts[0].get("text")
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Gemini response part did not include text")
    return text


def _call_json_generation(
    *,
    api_key: str,
    model: str,
    prompt: str,
    timeout_seconds: int,
) -> dict[str, Any]:
    response = _call_gemini(api_key, model, prompt, timeout_seconds=timeout_seconds)
    return json.loads(_extract_text(response))


def _parse_summary(text: str) -> AiSummary:
    payload = json.loads(text)
    key_points = payload.get("key_points")
    if not isinstance(key_points, list) or len(key_points) != 3:
        raise ValueError("Gemini key_points must contain exactly 3 items")
    cleaned_points = [_truncate(str(item).strip(), 180) for item in key_points]
    return AiSummary(
        headline=_truncate(str(payload.get("headline", "")).strip(), 80),
        summary=_truncate(str(payload.get("summary", "")).strip(), 240),
        who_is_it_for=_truncate(str(payload.get("who_is_it_for", "")).strip(), 180),
        key_points=cleaned_points,
        cta=_truncate(str(payload.get("cta", "")).strip(), 120),
        used_fallback=False,
    )


def generate_summary(
    event: EventItem,
    meta: EventMeta,
    *,
    api_key: str | None,
    model: str,
    timeout_seconds: int,
) -> AiSummary:
    if not api_key:
        logger.warning("GEMINI_API_KEY is not configured; using fallback summary for %s", event.title)
        return build_fallback_summary(event)

    last_error: Exception | None = None
    for stricter in (False, True):
        try:
            payload = _call_json_generation(
                api_key=api_key,
                model=model,
                prompt=_prompt(event, meta, stricter=stricter),
                timeout_seconds=timeout_seconds,
            )
            return _parse_summary(json.dumps(payload, ensure_ascii=False))
        except (json.JSONDecodeError, KeyError, ValueError, urllib.error.URLError) as exc:
            last_error = exc
            logger.warning("Gemini summary generation failed for %s: %s", event.title, exc)

    if last_error:
        logger.error("Falling back to template summary for %s after Gemini failure: %s", event.title, last_error)
    return build_fallback_summary(event)


def generate_tag_suggestions(
    event: EventItem,
    meta: EventMeta,
    *,
    allowed_tags: list[str],
    existing_tags: list[str],
    api_key: str | None,
    model: str,
    timeout_seconds: int,
) -> list[str]:
    if not api_key:
        return []

    prompt = f"""
당신은 개발자 행사 포럼 태그를 분류하는 도우미입니다.
아래 허용 태그 목록 안에서만 선택하세요.
기존에 이미 선택된 태그는 제외하고, 추가로 필요한 태그만 최대 2개 고르세요.
응답은 반드시 JSON 객체 하나여야 합니다.

허용 태그:
{", ".join(allowed_tags)}

이미 선택된 태그:
{", ".join(existing_tags) if existing_tags else "-"}

출력 JSON 스키마:
{{
  "tags": ["태그1", "태그2"]
}}

입력 정보:
- 제목: {event.title}
- 분류: {", ".join(event.categories) if event.categories else "-"}
- 주최: {event.organizer or "-"}
- {event.schedule_label or "일정"}: {event.schedule_text or "-"}
- og:title: {meta.og_title or "-"}
- og:description: {meta.og_description or "-"}
""".strip()

    try:
        payload = _call_json_generation(
            api_key=api_key,
            model=model,
            prompt=prompt,
            timeout_seconds=timeout_seconds,
        )
        tags = payload.get("tags", [])
        if not isinstance(tags, list):
            return []
        validated: list[str] = []
        for tag in tags:
            normalized = str(tag).strip()
            if normalized in allowed_tags and normalized not in existing_tags and normalized not in validated:
                validated.append(normalized)
        return validated[:2]
    except (json.JSONDecodeError, KeyError, ValueError, urllib.error.URLError) as exc:
        logger.warning("Gemini tag suggestion failed for %s: %s", event.title, exc)
        return []
