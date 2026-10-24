from datetime import datetime, timedelta, timezone

from ux_daily_brief.editorial_selection import select_articles
from ux_daily_brief.models import Article


NOW = datetime(2026, 10, 24, 12, tzinfo=timezone.utc)


def make_article(index, source="smashing", score=70, hours=12):
    article = Article(
        source=source,
        title=f"UX Article {index}",
        url=f"https://example.com/article/{index}",
        excerpt="A practical UX development.",
        origin="rss",
        published_at=NOW - timedelta(hours=hours),
    )
    article.score = score
    return article


def test_highest_score_first():
    articles = [
        make_article(1, score=50),
        make_article(2, score=90),
    ]

    result = select_articles(articles, now=NOW)

    assert result.selected[0].score == 90


def test_low_score_excluded():
    articles = [make_article(1, score=20)]
    result = select_articles(articles, now=NOW)

    assert result.selected == []


def test_old_article_excluded():
    articles = [make_article(1, hours=96)]
    result = select_articles(articles, now=NOW)

    assert result.selected == []


def test_max_two_per_source():
    articles = [
        make_article(i, score=90 - i)
        for i in range(5)
    ]

    result = select_articles(articles, now=NOW)

    assert len(result.selected) == 2


def test_multiple_sources():
    articles = [
        make_article(1, source="smashing"),
        make_article(2, source="page"),
        make_article(3, source="techcrunch"),
    ]

    result = select_articles(articles, now=NOW)

    assert len(result.selected) == 3


def test_no_filler_articles():
    articles = [make_article(1)]
    result = select_articles(articles, now=NOW)

    assert len(result.selected) == 1


def test_missing_score_excluded():
    articles = [make_article(1, score=None)]
    result = select_articles(articles, now=NOW)

    assert len(result.selected) == 0
