from __future__ import annotations

import hashlib
import logging
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from src.models import EventItem


logger = logging.getLogger(__name__)

TRACKING_KEYS = {"eventOrigin", "fbclid", "gclid", "igshid"}


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(value.strip().split()).casefold()


def canonicalize_url(url: str) -> str:
    parsed = urlsplit(url.strip())
    if not parsed.scheme or not parsed.netloc:
        return ""

    scheme = parsed.scheme.lower()
    host = parsed.netloc.lower()
    if host.startswith("www."):
        host = host[4:]

    path = parsed.path or "/"
    if path != "/":
        path = path.rstrip("/")

    query_items = []
    for key, value in parse_qsl(parsed.query, keep_blank_values=True):
        if key.startswith("utm_") or key in TRACKING_KEYS:
            continue
        query_items.append((key, value))

    query = urlencode(query_items, doseq=True)
    return urlunsplit((scheme, host, path, query, ""))


def build_event_id(title: str, url: str, organizer: str | None) -> tuple[str, str]:
    canonical_url = canonicalize_url(url)
    if canonical_url:
        digest = hashlib.sha256(canonical_url.encode("utf-8")).hexdigest()
        return digest, canonical_url

    fallback = f"{normalize_text(title)}|{normalize_text(organizer)}"
    digest = hashlib.sha256(fallback.encode("utf-8")).hexdigest()
    return digest, canonical_url


def dedupe_events(events: list[EventItem]) -> list[EventItem]:
    seen: set[str] = set()
    deduped: list[EventItem] = []
    for event in events:
        if event.event_id in seen:
            logger.info("Skipping duplicate event in README: %s (%s)", event.title, event.canonical_url or event.url)
            continue
        seen.add(event.event_id)
        deduped.append(event)
    return deduped
