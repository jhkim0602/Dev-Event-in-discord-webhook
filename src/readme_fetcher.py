from __future__ import annotations

import urllib.request


def fetch_readme(url: str, *, timeout_seconds: int, user_agent: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": user_agent})
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        body = response.read()
        charset = response.headers.get_content_charset("utf-8")
    return body.decode(charset, errors="replace")
