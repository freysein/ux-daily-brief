from datetime import timezone

import pytest

from ux_daily_brief.collectors import rss


SAMPLE_RSS = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
<title>UX Feed</title>
<link>https://example.com</link>
<description>Example feed</description>
<item>
<title>New accessibility design patterns</title>
<link>https://example.com/accessibility</link>
<description><![CDATA[
<p>New techniques for improving accessible interfaces.</p>
]]></description>
<pubDate>Fri, 23 Oct 2026 10:00:00 GMT</pubDate>
</item>
</channel>
</rss>
"""


class FakeResponse:
    content = SAMPLE_RSS

    def raise_for_status(self):
        pass


def test_rss_article_extraction(monkeypatch):
    monkeypatch.setattr(
        rss.requests,
        "get",
        lambda *args, **kwargs: FakeResponse(),
    )

    articles = rss.fetch_feed(
        "smashing",
        "https://example.com/feed",
    )

    assert len(articles) == 1
    assert articles[0].source == "smashing"
    assert articles[0].origin == "rss"
    assert articles[0].title == "New accessibility design patterns"
    assert articles[0].excerpt.startswith("New techniques")
    assert articles[0].published_at.tzinfo == timezone.utc


def test_invalid_feed(monkeypatch):
    class InvalidResponse:
        content = b"not an xml feed"

        def raise_for_status(self):
            pass

    monkeypatch.setattr(
        rss.requests,
        "get",
        lambda *args, **kwargs: InvalidResponse(),
    )

    with pytest.raises(ValueError, match="Invalid RSS feed"):
        rss.fetch_feed("smashing", "https://example.com/feed")


def test_invalid_limit():
    with pytest.raises(ValueError, match="limit must be positive"):
        rss.fetch_feed("smashing", "https://example.com/feed", limit=0)


def test_configured_sources():
    feeds = rss.configured_feeds()

    assert "page" in feeds
    assert "smashing" in feeds
    assert "t3n_ai" in feeds
    assert len(feeds) == 3
