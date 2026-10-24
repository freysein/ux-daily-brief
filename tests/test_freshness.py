from datetime import datetime, timedelta, timezone

from ux_daily_brief.freshness import (
    article_timestamp,
    filter_fresh,
    is_fresh,
)
from ux_daily_brief.models import Article


NOW = datetime(2026, 10, 24, 12, 0, tzinfo=timezone.utc)


def make_article(published=None, received=None):
    return Article(
        source="techcrunch",
        title="UX Research Article",
        url="https://example.com/ux",
        excerpt="A relevant UX article.",
        origin="newsletter",
        published_at=published,
        received_at=received,
    )


def test_recent_rss_article():
    article = make_article(
        published=NOW - timedelta(hours=24)
    )
    assert is_fresh(article, now=NOW)


def test_recent_newsletter():
    article = make_article(
        received=NOW - timedelta(hours=48)
    )
    assert is_fresh(article, now=NOW)


def test_old_article():
    article = make_article(
        published=NOW - timedelta(hours=96)
    )
    assert not is_fresh(article, now=NOW)


def test_future_article():
    article = make_article(
        published=NOW + timedelta(hours=2)
    )
    assert not is_fresh(article, now=NOW)


def test_missing_date():
    assert not is_fresh(make_article(), now=NOW)


def test_published_date_preferred():
    article = make_article(
        published=NOW - timedelta(hours=100),
        received=NOW - timedelta(hours=2),
    )

    assert article_timestamp(article) == article.published_at
    assert not is_fresh(article, now=NOW)


def test_filter_fresh_articles():
    articles = [
        make_article(
            published=NOW - timedelta(hours=12)
        ),
        make_article(
            published=NOW - timedelta(hours=100)
        ),
    ]

    assert len(filter_fresh(articles, now=NOW)) == 1
