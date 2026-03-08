from src.event_meta_fetcher import extract_event_meta


def test_extract_event_meta_prefers_og_image() -> None:
    html = """
    <html>
      <head>
        <meta property="og:title" content="행사 제목" />
        <meta property="og:description" content="설명" />
        <meta property="og:image" content="/cover.png" />
      </head>
    </html>
    """
    meta = extract_event_meta(html, "https://example.com/event")

    assert meta.og_title == "행사 제목"
    assert meta.og_description == "설명"
    assert meta.og_image == "https://example.com/cover.png"


def test_extract_event_meta_falls_back_to_twitter_image() -> None:
    html = """
    <html>
      <head>
        <meta name="twitter:image" content="https://cdn.example.com/image.jpg" />
      </head>
    </html>
    """
    meta = extract_event_meta(html, "https://example.com/event")

    assert meta.og_image == "https://cdn.example.com/image.jpg"
