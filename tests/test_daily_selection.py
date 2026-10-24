from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from ux_daily_brief.daily_selection import build_daily_selection
from ux_daily_brief.duplicate_check import DuplicateDecision
from ux_daily_brief.models import Article


@pytest.fixture(autouse=True)
def mock_edition_check():
    with patch(
        "ux_daily_brief.daily_selection.check_edition_duplicate",
        return_value=mock_decision("unique"),
    ):
        yield


NOW = datetime(2026, 10, 24, 12, tzinfo=timezone.utc)


def make_article(index, source="smashing", score=70):
    article = Article(
        source=source,
        title=f"UX Article {index}",
        url=f"https://example.com/{index}",
        excerpt="A relevant UX development.",
        origin="rss",
        published_at=NOW - timedelta(hours=12),
    )
    article.score = score
    return article


def mock_decision(status):
    return DuplicateDecision(status, "Test decision")


def test_unique_articles_selected(tmp_path):
    articles = [
        make_article(1, source="smashing"),
        make_article(2, source="page"),
    ]

    with patch(
        "ux_daily_brief.daily_selection.check_duplicate",
        return_value=mock_decision("unique"),
    ):
        result = build_daily_selection(
            articles, now=NOW,
            db_path=tmp_path / "test.duckdb",
        )

    assert len(result.selected) == 2


def test_duplicate_excluded(tmp_path):
    with patch(
        "ux_daily_brief.daily_selection.check_duplicate",
        return_value=mock_decision("duplicate"),
    ):
        result = build_daily_selection(
            [make_article(1)], now=NOW,
            db_path=tmp_path / "test.duckdb",
        )

    assert result.selected == []
    assert result.excluded[0]["reason"] == "duplicate"


def test_uncertain_article_needs_review(tmp_path):
    with patch(
        "ux_daily_brief.daily_selection.check_duplicate",
        return_value=mock_decision("review"),
    ):
        result = build_daily_selection(
            [make_article(1)], now=NOW,
            db_path=tmp_path / "test.duckdb",
        )

    assert result.selected == []
    assert len(result.review) == 1


def test_source_limit(tmp_path):
    articles = [
        make_article(i, source="smashing", score=90-i)
        for i in range(5)
    ]

    with patch(
        "ux_daily_brief.daily_selection.check_duplicate",
        return_value=mock_decision("unique"),
    ):
        result = build_daily_selection(
            articles, now=NOW,
            db_path=tmp_path / "test.duckdb",
        )

    assert len(result.selected) == 2


def test_review_does_not_consume_source_slot(tmp_path):
    articles = [
        make_article(1, source="page", score=90),
        make_article(2, source="page", score=80),
    ]

    def decide(article, **kwargs):
        if article.title.endswith("1"):
            return mock_decision("review")
        return mock_decision("unique")

    with patch(
        "ux_daily_brief.daily_selection.check_duplicate",
        side_effect=decide,
    ):
        result = build_daily_selection(
            articles, now=NOW,
            db_path=tmp_path / "test.duckdb",
        )

    assert len(result.selected) == 1
    assert len(result.review) == 1


def test_edition_duplicate_allows_next_article(tmp_path):
    articles = [
        make_article(1, source="page", score=90),
        make_article(2, source="page", score=80),
        make_article(3, source="page", score=70),
    ]

    def edition_decision(article, selected):
        if article.title.endswith("2"):
            return mock_decision("duplicate")
        return mock_decision("unique")

    with (
        patch(
            "ux_daily_brief.daily_selection.check_duplicate",
            return_value=mock_decision("unique"),
        ),
        patch(
            "ux_daily_brief.daily_selection.check_edition_duplicate",
            side_effect=edition_decision,
        ),
    ):
        result = build_daily_selection(
            articles,
            now=NOW,
            db_path=tmp_path / "test.duckdb",
        )

    assert [a.title for a in result.selected] == [
        "UX Article 1",
        "UX Article 3",
    ]
    assert any(
        item["reason"] == "edition_duplicate"
        for item in result.excluded
    )


def test_edition_review_does_not_consume_source_slot(tmp_path):
    articles = [
        make_article(1, source="page", score=90),
        make_article(2, source="page", score=80),
        make_article(3, source="page", score=70),
    ]

    def edition_decision(article, selected):
        if article.title.endswith("2"):
            return mock_decision("review")
        return mock_decision("unique")

    with (
        patch(
            "ux_daily_brief.daily_selection.check_duplicate",
            return_value=mock_decision("unique"),
        ),
        patch(
            "ux_daily_brief.daily_selection.check_edition_duplicate",
            side_effect=edition_decision,
        ),
    ):
        result = build_daily_selection(
            articles,
            now=NOW,
            db_path=tmp_path / "test.duckdb",
        )

    assert [a.title for a in result.selected] == [
        "UX Article 1",
        "UX Article 3",
    ]
    assert len(result.review) == 1
