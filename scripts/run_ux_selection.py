from __future__ import annotations

import json
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from ux_daily_brief.article_pipeline import extract_from_inbox
from ux_daily_brief.daily_selection import build_daily_selection
from ux_daily_brief.models import Article
from ux_daily_brief.sponsorship_review import check_article_sponsorship


REPORT = Path("data/reports/ux_scoring_incremental.json")
EDITORIAL = Path("data/reports/ux_editorial_review.json")
OUTPUT = Path("data/reports/ux_daily_selection_dry_run.json")


def main():
    snapshot = json.loads(REPORT.read_text(encoding="utf-8"))
    rows = snapshot["results"]

    editorial_report = json.loads(
        EDITORIAL.read_text(encoding="utf-8")
    )
    editorial_rows = editorial_report["results"]

    editorial_results = {
        row["article_id"]: row
        for row in editorial_rows
    }

    if len(editorial_results) != len(editorial_rows):
        raise RuntimeError("Duplicate editorial article IDs")

    newsletters = extract_from_inbox(
        Path("data/inbox/newsletters")
    )
    newsletter_by_id = {
        article.article_id: article
        for article in newsletters
    }

    if len(newsletter_by_id) != len(newsletters):
        raise RuntimeError("Duplicate newsletter article IDs")

    articles = []
    seen_ids = set()

    for row in rows:
        article_id = row["article_id"]

        if article_id in seen_ids:
            raise RuntimeError(f"Duplicate report ID: {article_id}")
        seen_ids.add(article_id)

        published = (
            datetime.fromisoformat(row["published_at"])
            if row.get("published_at")
            else None
        )

        original = newsletter_by_id.get(article_id)

        if row["origin"] == "newsletter" and original is None:
            raise RuntimeError(
                f"Newsletter not found: {article_id}"
            )

        article = Article(
            source=row["source"],
            title=row["title"],
            url=row["url"],
            excerpt=row.get("excerpt") or "",
            origin=row["origin"],
            published_at=published,
            received_at=(
                original.received_at if original else None
            ),
        )

        if article.article_id != article_id:
            raise RuntimeError(
                f"Article identity mismatch: {article_id}"
            )

        if row["status"] == "scored":
            article.score = row["score"]

        articles.append(article)

    now = datetime.now(timezone.utc)

    with tempfile.TemporaryDirectory(
        prefix="ux-selection-dry-run-"
    ) as temp:
        db_path = Path(temp) / "publications.duckdb"

        result = build_daily_selection(
            articles,
            now=now,
            db_path=db_path,
            max_articles=9,
            max_per_source=2,
            editorial_results=editorial_results,
            min_articles=6,
            sponsorship_check=check_article_sponsorship,
        )

    selected = [
        {
            "article_id": article.article_id,
            "source": article.source,
            "title": article.title,
            "url": article.url,
            "score": article.score,
            "editorial_classification": editorial_results.get(
                article.article_id, {}
            ).get("classification", "unknown"),
            "published_at": (
                article.published_at.isoformat()
                if article.published_at else None
            ),
            "received_at": (
                article.received_at.isoformat()
                if article.received_at else None
            ),
        }
        for article in result.selected
    ]

    output = {
        "generated_at": now.isoformat(),
        "mode": "dry_run",
        "history_mode": "isolated_empty_database",
        "scoring_report": str(REPORT),
        "editorial_report": str(EDITORIAL),
        "selection_policy": "core_ux_adjacent_then_weak_fallback",
        "total_candidates": len(articles),
        "selected": selected,
        "review": result.review,
        "excluded": result.excluded,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    temporary = OUTPUT.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(output, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    temporary.replace(OUTPUT)

    print("===== UX DAILY SELECTION DRY RUN =====")
    print("Candidates:", len(articles))
    print("Selected:", len(selected))
    print("Review:", len(result.review))
    print("Excluded:", len(result.excluded))

    print("\n===== SELECTED ARTICLES =====")
    for index, article in enumerate(selected, 1):
        print(
            f"{index:02d}. "
            f"{article['score']:5.1f} | "
            f"{article['source']:12} | "
            f"{article['title']}"
        )

    print("\n===== EXCLUSION REASONS =====")
    for reason, count in sorted(
        Counter(
            item["reason"] for item in result.excluded
        ).items()
    ):
        print(f"{reason}: {count}")

    print("\n===== REVIEW CASES =====")
    for item in result.review:
        print(item["article_id"], item["reason"])

    print("\nREPORT:", OUTPUT.resolve())
    print("NO PUBLICATIONS RECORDED")
    print("DRY RUN: COMPLETE")


if __name__ == "__main__":
    main()
