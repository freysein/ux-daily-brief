from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch

from ux_daily_brief.daily_selection import build_daily_selection
from ux_daily_brief.models import Article


NOW = datetime.now(timezone.utc)


def article(source, title, score):
    item = Article(
        source=source,
        title=title,
        url=f"https://example.com/{source}/{score}",
        excerpt="Detailed information about a relevant UX topic.",
        origin="rss",
        published_at=NOW,
    )
    item.score = score
    return item


def run_selection(items, checker, tmp_path):
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
            db_path=tmp_path / "publications.duckdb",
            editorial_results=editorial,
            sponsorship_check=checker,
            max_articles=2,
            min_articles=2,
        )


def test_sponsored_article_excluded_and_next_candidate_selected(
    tmp_path,
):
    sponsored = article(
        "t3n_ai", "Sponsored compliance article", 95
    )
    first = article(
        "smashing", "Independent UX research article", 80
    )
    replacement = article(
        "page", "Independent design research article", 70
    )

    def check(item):
        return (
            "sponsored"
            if item.article_id == sponsored.article_id
            else "not_sponsored"
        )

    result = run_selection(
        [sponsored, first, replacement],
        check,
        tmp_path,
    )

    assert [a.article_id for a in result.selected] == [
        first.article_id,
        replacement.article_id,
    ]
    assert any(
        row["article_id"] == sponsored.article_id
        and row["reason"] == "sponsored_content"
        for row in result.excluded
    )


def test_unverified_sponsorship_requires_review(tmp_path):
    uncertain = article(
        "t3n_ai", "Unverified editorial article", 95
    )
    replacement = article(
        "page", "Verified design research article", 80
    )

    result = run_selection(
        [uncertain, replacement],
        lambda item: (
            "review"
            if item.article_id == uncertain.article_id
            else "not_sponsored"
        ),
        tmp_path,
    )

    assert [a.article_id for a in result.selected] == [
        replacement.article_id
    ]
    assert any(
        row["article_id"] == uncertain.article_id
        and row["reason"] == "sponsorship_unverified"
        for row in result.review
    )
