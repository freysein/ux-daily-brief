from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

from ux_daily_brief import daily_selection
from ux_daily_brief.brief_pipeline import generate_brief
from ux_daily_brief.models import Article


NOW = datetime(2026, 10, 25, tzinfo=timezone.utc)


def article(status):
    return Article(
        source="jakob_nielsen",
        title="Forecasting",
        url="https://jakobnielsenphd.substack.com/p/ux-roundup-20261023",
        excerpt="Forecasting",
        origin="newsletter",
        received_at=NOW,
        review_status=status,
    )


def test_review_not_passed_to_editorial_selection(monkeypatch):
    captured = []

    def fake_select(items, **kwargs):
        captured.extend(items)
        return SimpleNamespace(selected=list(items), excluded=[])

    monkeypatch.setattr(
        daily_selection, "select_articles", fake_select
    )

    result = daily_selection.build_daily_selection(
        [article("review")],
        now=NOW,
        db_path=Path("/tmp/unused_review_gate.duckdb"),
    )

    assert captured == []
    assert result.selected == []
    assert len(result.review) == 1
    assert result.review[0]["reason"] == (
        "article_review_status_not_candidate"
    )


def test_other_non_candidate_status_is_blocked(monkeypatch):
    def fake_select(items, **kwargs):
        return SimpleNamespace(selected=list(items), excluded=[])

    monkeypatch.setattr(
        daily_selection, "select_articles", fake_select
    )

    result = daily_selection.build_daily_selection(
        [article("pending")],
        now=NOW,
    )

    assert result.selected == []
    assert len(result.review) == 1


def test_brief_generation_rejects_review():
    def fail(*args, **kwargs):
        raise AssertionError("Generation must not run")

    result = generate_brief(
        [(article("review"), "core_ux")],
        enrich=fail,
        generate=fail,
    )

    assert result.entries == []
    assert result.attempted == 0
    assert len(result.rejected) == 1
    assert result.rejected[0]["reason"] == (
        "article_review_status_not_candidate"
    )


def test_default_article_is_candidate():
    item = article("candidate")
    assert item.review_status == "candidate"
