from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from ux_daily_brief.daily_selection import build_daily_selection
from ux_daily_brief.duplicate_check import DuplicateDecision
from ux_daily_brief.models import Article


NOW = datetime(2026, 10, 24, 12, tzinfo=timezone.utc)


def make_article(number, score, source):
    article = Article(
        source=source,
        title=f"Article {number}",
        url=f"https://example.com/{number}",
        excerpt="UX-related article",
        origin="rss",
        published_at=NOW - timedelta(hours=12),
    )
    article.score = score
    return article


def test_core_ux_preferred_over_higher_scoring_weak(tmp_path):
    articles = [
        make_article(1, 90, "page"),
        make_article(2, 50, "smashing"),
    ]

    editorial = {
        articles[0].article_id: {"classification": "weak"},
        articles[1].article_id: {"classification": "core_ux"},
    }

    with (
        patch(
            "ux_daily_brief.daily_selection.check_duplicate",
            return_value=DuplicateDecision("unique", "OK"),
        ),
        patch(
            "ux_daily_brief.daily_selection.check_edition_duplicate",
            return_value=DuplicateDecision("unique", "OK"),
        ),
    ):
        result = build_daily_selection(
            articles,
            now=NOW,
            db_path=tmp_path / "history.duckdb",
            editorial_results=editorial,
            min_articles=2,
        )

    assert result.selected[0].title == "Article 2"
    assert len(result.selected) == 2


def test_weak_fills_to_minimum(tmp_path):
    sources = ["page", "smashing", "t3n_ai", "techcrunch"]
    articles = [
        make_article(i, 80 - i, sources[i % 4])
        for i in range(8)
    ]

    editorial = {
        article.article_id: {
            "classification": (
                "core_ux" if i < 2 else "weak"
            )
        }
        for i, article in enumerate(articles)
    }

    with (
        patch(
            "ux_daily_brief.daily_selection.check_duplicate",
            return_value=DuplicateDecision("unique", "OK"),
        ),
        patch(
            "ux_daily_brief.daily_selection.check_edition_duplicate",
            return_value=DuplicateDecision("unique", "OK"),
        ),
    ):
        result = build_daily_selection(
            articles,
            now=NOW,
            db_path=tmp_path / "history.duckdb",
            editorial_results=editorial,
        )

    assert len(result.selected) == 6
    assert result.selected[0].article_id == articles[0].article_id
    assert result.selected[1].article_id == articles[1].article_id
