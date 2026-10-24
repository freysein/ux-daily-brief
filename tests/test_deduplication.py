from ux_daily_brief.deduplication import (
    deduplicate_articles,
    normalized_title,
)
from ux_daily_brief.models import Article


def article(source, title, origin, url):
    return Article(
        source=source,
        title=title,
        url=url,
        excerpt="Example article description.",
        origin=origin,
    )


def test_normalized_title():
    assert normalized_title("UX: Research!") == "ux research"


def test_newsletter_rss_duplicate():
    newsletter = article(
        "page",
        "New Design Research",
        "newsletter",
        "https://click.example.com/abc",
    )
    rss = article(
        "page",
        "New Design Research",
        "rss",
        "https://page-online.de/research",
    )

    result = deduplicate_articles([newsletter, rss])

    assert len(result) == 1
    assert result[0].origin == "rss"


def test_different_sources_preserved():
    first = article(
        "page", "AI and UX", "rss", "https://page-online.de/ai"
    )
    second = article(
        "smashing", "AI and UX", "rss",
        "https://smashingmagazine.com/ai"
    )

    assert len(deduplicate_articles([first, second])) == 2


def test_different_titles_preserved():
    first = article(
        "page", "Design Research", "rss", "https://example.com/1"
    )
    second = article(
        "page", "Accessibility Research", "rss",
        "https://example.com/2"
    )

    assert len(deduplicate_articles([first, second])) == 2
