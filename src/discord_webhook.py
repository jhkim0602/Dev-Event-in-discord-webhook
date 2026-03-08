from __future__ import annotations

import json
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
import urllib.request

from src.models import AiSummary, EventItem, EventMeta


def _truncate(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    return value[: limit - 1].rstrip() + "…"


def _field_value(value: str | None, *, limit: int = 1024) -> str:
    return _truncate((value or "-").strip(), limit)


def _thread_name(title: str) -> str:
    return _truncate(f"[신규] {title}", 90)


def build_discord_payload(
    event: EventItem,
    summary: AiSummary,
    meta: EventMeta,
    *,
    source_readme_page_url: str,
    tag_id: str,
) -> dict[str, Any]:
    schedule_name = event.schedule_label or "일정"
    categories = ", ".join(event.categories) if event.categories else "-"
    embed: dict[str, Any] = {
        "title": _truncate(summary.headline or event.title, 256),
        "url": meta.final_url or event.url,
        "description": _truncate(f"{summary.summary}\n\n{summary.cta}", 4096),
        "fields": [
            {
                "name": "누구에게 맞을까",
                "value": _field_value(summary.who_is_it_for),
                "inline": False,
            },
            {
                "name": "핵심 포인트",
                "value": _field_value("\n".join(f"• {point}" for point in summary.key_points)),
                "inline": False,
            },
            {
                "name": "주최",
                "value": _field_value(event.organizer),
                "inline": True,
            },
            {
                "name": "분류",
                "value": _field_value(categories),
                "inline": True,
            },
            {
                "name": schedule_name,
                "value": _field_value(event.schedule_text),
                "inline": False,
            },
            {
                "name": "출처",
                "value": _field_value(source_readme_page_url),
                "inline": False,
            },
        ],
        "footer": {
            "text": "Source: Dev-Event README",
        },
    }
    if meta.og_image:
        embed["image"] = {"url": meta.og_image}

    return {
        "thread_name": _thread_name(event.title),
        "applied_tags": [tag_id],
        "allowed_mentions": {"parse": []},
        "embeds": [embed],
    }


def _with_wait_true(webhook_url: str) -> str:
    split = urlsplit(webhook_url)
    query = dict(parse_qsl(split.query, keep_blank_values=True))
    query["wait"] = "true"
    return urlunsplit((split.scheme, split.netloc, split.path, urlencode(query), split.fragment))


def post_forum_thread(webhook_url: str, payload: dict[str, Any], *, timeout_seconds: int) -> dict[str, Any]:
    request = urllib.request.Request(
        _with_wait_true(webhook_url),
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        return json.loads(response.read().decode("utf-8"))
