from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import patch

from ux_daily_brief.daily_selection import build_daily_selection
from ux_daily_brief.models import Article


NOW = datetime(2026, 10, 25, 10, 0, tzinfo=timezone.utc)


def make_article(title, score, age_hours, source="smashing"):
    item = Article(
        source=source,
        title=title,
        url=f"https://example.com/{title.replace(' ', '-')}",
        excerpt="Useful information about UX design practices.",
        origin="rss",
        published_at=NOW - timedelta(hours=age_hours),
    )
    item.score = score
    return item


def select(items, tmp_path, **kwargs):
    editorial = {
        item.article_id: {"classification": "core_ux"}
        for item in items
    }

    with (
        patch(
            "ux_daily_brief.daily_selection.check_duplicate",
            return_value=SimpleNamespace(status="new"),
        ),
        patch(
            "ux_daily_brief.daily_selection.check_edition_duplicate",
            return_value=SimpleNamespace(status="new"),
        ),
    ):
        return build_daily_selection(
            items,
            now=NOW,
            db_path=tmp_path / "test.duckdb",
            editorial_results=editorial,
            fallback_max_age_hours=168,
            fallback_min_score=55.0,
            max_articles=2,
            max_per_source=2,
            min_articles=2,
            **kwargs,
        )


def test_fresh_article_prioritized(tmp_path):
    fresh = make_article("Fresh Article", 55, 24)
    older = make_article("Older Article", 90, 120)

    result = select([older, fresh], tmp_path)

    assert [a.article_id for a in result.selected] == [
        fresh.article_id,
        older.article_id,
    ]


def test_five_day_article_can_be_selected(tmp_path):
    older = make_article("Five Day UX Research", 72, 120)

    result = select([older], tmp_path)

    assert len(result.selected) == 1
    assert result.selected[0].article_id == older.article_id


def test_low_score_fallback_excluded(tmp_path):
    older = make_article("Low Score Article", 50, 120)

    result = select([older], tmp_path)

    assert result.selected == []
    assert any(
        item["reason"] == "fallback_score_too_low"
        for item in result.excluded
    )


def test_older_than_seven_days_excluded(tmp_path):
    older = make_article("Very Old Article", 90, 200)

    result = select([older], tmp_path)

    assert result.selected == []
    assert any(
        item["reason"] == "not_fresh"
        for item in result.excluded
    )
