from __future__ import annotations

from html.parser import HTMLParser
from urllib.parse import urljoin
import urllib.request

from src.models import EventMeta


class _MetaTagParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.meta: dict[str, str] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "meta":
            return
        attributes = {key.lower(): value for key, value in attrs if value is not None}
        content = attributes.get("content")
        if not content:
            return
        if "property" in attributes:
            self.meta[attributes["property"].lower()] = content
        if "name" in attributes:
            self.meta[attributes["name"].lower()] = content


def _is_valid_image_url(url: str | None) -> bool:
    if not url:
        return False
    if len(url) > 2000:
        return False
    return url.startswith("http://") or url.startswith("https://")


def extract_event_meta(html: str, final_url: str) -> EventMeta:
    parser = _MetaTagParser()
    parser.feed(html)

    og_image = parser.meta.get("og:image") or parser.meta.get("twitter:image")
    if og_image and not _is_valid_image_url(og_image):
        og_image = urljoin(final_url, og_image)
    if not _is_valid_image_url(og_image):
        og_image = None

    og_title = parser.meta.get("og:title")
    og_description = parser.meta.get("og:description") or parser.meta.get("description")

    return EventMeta(
        final_url=final_url,
        og_title=og_title.strip() if og_title else None,
        og_description=og_description.strip() if og_description else None,
        og_image=og_image,
    )


def fetch_event_meta(url: str, *, timeout_seconds: int, user_agent: str) -> EventMeta:
    request = urllib.request.Request(url, headers={"User-Agent": user_agent})
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        content_type = response.headers.get_content_type()
        final_url = response.geturl()
        if "html" not in content_type:
            return EventMeta(final_url=final_url)
        body = response.read(512 * 1024)
        charset = response.headers.get_content_charset("utf-8")

    html = body.decode(charset, errors="replace")
    return extract_event_meta(html, final_url)
