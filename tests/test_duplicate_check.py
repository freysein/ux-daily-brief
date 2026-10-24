from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from ux_daily_brief.duplicate_check import check_duplicate
from ux_daily_brief.models import Article
from ux_daily_brief.publication_history import record_publication


NOW = datetime(2026, 10, 24, 12, tzinfo=timezone.utc)


def article():
    return Article(
        source="t3n_ai",
        title="KI-Agenten auf einer Insel",
        url="https://example.com/new",
        excerpt="Agenten erfanden gemeinsame Spiele.",
        origin="rss",
    )


def publish(db, article_id, url, days_ago):
    record_publication(
        article_id,
        "techcrunch",
        "AI Agents on an Island",
        url,
        "2026-10-23",
        db_path=db,
        published_at=NOW - timedelta(days=days_ago),
        excerpt="Agents invented games together.",
    )


def test_empty_history_is_unique(tmp_path):
    result = check_duplicate(
        article(), db_path=tmp_path / "history.duckdb",
        now=NOW,
    )
    assert result.status == "unique"


def test_same_url_is_duplicate_without_ollama(tmp_path):
    db = tmp_path / "history.duckdb"
    publish(db, "old-id", "https://example.com/new?utm_source=email", 1)

    with patch(
        "ux_daily_brief.duplicate_check.compare_stories"
    ) as compare:
        result = check_duplicate(article(), db_path=db, now=NOW)

    assert result.status == "duplicate"
    compare.assert_not_called()


def test_cross_language_duplicate(tmp_path):
    db = tmp_path / "history.duckdb"
    publish(db, "old-id", "https://example.com/other", 10)

    with patch(
        "ux_daily_brief.duplicate_check.compare_stories",
        return_value={
            "same_story": True,
            "confidence": 0.95,
            "reason": "Same experiment",
        },
    ):
        result = check_duplicate(article(), db_path=db, now=NOW)

    assert result.status == "duplicate"
    assert result.matched_article_id == "old-id"


def test_similar_topic_not_automatically_blocked(tmp_path):
    db = tmp_path / "history.duckdb"
    publish(db, "old-id", "https://example.com/other", 10)

    with patch(
        "ux_daily_brief.duplicate_check.compare_stories",
        return_value={
            "same_story": False,
            "confidence": 0.97,
            "reason": "Different experiments",
        },
    ):
        result = check_duplicate(article(), db_path=db, now=NOW)

    assert result.status == "unique"


def test_uncertain_case_requires_review(tmp_path):
    db = tmp_path / "history.duckdb"
    publish(db, "old-id", "https://example.com/other", 10)

    with patch(
        "ux_daily_brief.duplicate_check.compare_stories",
        return_value={
            "same_story": True,
            "confidence": 0.65,
            "reason": "Possible overlap",
        },
    ):
        result = check_duplicate(article(), db_path=db, now=NOW)

    assert result.status == "review"


def test_comparison_limit_requires_review(tmp_path):
    db = tmp_path / "history.duckdb"
    publish(db, "old-id", "https://example.com/other", 10)

    result = check_duplicate(
        article(),
        db_path=db,
        now=NOW,
        max_semantic_checks=0 + 1,
    )
    assert result.status in {"unique", "duplicate", "review"}


def test_comparison_limit_exceeded(tmp_path):
    db = tmp_path / "history.duckdb"

    publish(db, "old-1", "https://example.com/old-1", 2)
    publish(db, "old-2", "https://example.com/old-2", 3)

    with patch(
        "ux_daily_brief.duplicate_check.compare_stories"
    ) as compare:
        result = check_duplicate(
            article(),
            db_path=db,
            now=NOW,
            max_semantic_checks=1,
        )

    assert result.status == "review"
    compare.assert_not_called()


def test_ollama_failure_requires_review(tmp_path):
    db = tmp_path / "history.duckdb"
    publish(db, "old-id", "https://example.com/other", 2)

    with patch(
        "ux_daily_brief.duplicate_check.compare_stories",
        side_effect=RuntimeError("Ollama unavailable"),
    ):
        result = check_duplicate(
            article(),
            db_path=db,
            now=NOW,
        )

    assert result.status == "review"


def test_empty_history_does_not_call_ollama(tmp_path):
    db = tmp_path / "history.duckdb"

    with patch(
        "ux_daily_brief.duplicate_check.compare_stories"
    ) as compare:
        result = check_duplicate(
            article(),
            db_path=db,
            now=NOW,
        )

    assert result.status == "unique"
    compare.assert_not_called()
