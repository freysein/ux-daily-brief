from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from ux_daily_brief.editorial_review import (
    editorial_eligible,
    review_article,
)
from ux_daily_brief.freshness import is_fresh
from ux_daily_brief.models import Article


INPUT = Path("data/reports/ux_scoring_incremental.json")
OUTPUT = Path("data/reports/ux_editorial_review.json")


def parse_date(value):
    return datetime.fromisoformat(value) if value else None


def main():
    report = json.loads(INPUT.read_text(encoding="utf-8"))

    newsletter_dates = {}

    from ux_daily_brief.article_pipeline import extract_from_inbox

    for article in extract_from_inbox(
        Path("data/inbox/newsletters")
    ):
        newsletter_dates[article.article_id] = article.received_at

    now = datetime.now(timezone.utc)
    candidates = []

    for row in report["results"]:
        if row.get("status") != "scored":
            continue

        score = row.get("score")
        if score is None or score < 30:
            continue

        article = Article(
            source=row["source"],
            title=row["title"],
            url=row["url"],
            excerpt=row.get("excerpt") or "",
            origin=row["origin"],
            published_at=parse_date(row.get("published_at")),
            received_at=newsletter_dates.get(row["article_id"]),
        )

        if article.article_id != row["article_id"]:
            raise RuntimeError(
                f"Article identity mismatch: {row['article_id']}"
            )

        article.score = score

        if is_fresh(article, now=now):
            candidates.append(article)

    candidates.sort(key=lambda a: (-a.score, a.source, a.title))

    results = []

    for index, article in enumerate(candidates, 1):
        try:
            review = review_article(article)
            status = review["classification"]
            eligible = editorial_eligible(review)
        except Exception as exc:
            review = {
                "classification": "review",
                "evidence": "",
                "reason": f"Review failed: {type(exc).__name__}",
            }
            status = "review"
            eligible = False

        entry = {
            "article_id": article.article_id,
            "source": article.source,
            "title": article.title,
            "score": article.score,
            "classification": status,
            "eligible": eligible,
            "evidence": review["evidence"],
            "reason": review["reason"],
        }
        results.append(entry)

        print(
            f"[{index}/{len(candidates)}] "
            f"{article.source:12} | "
            f"{article.score:5.1f} | "
            f"{status:8} | "
            f"{article.title[:65]}"
        )

    output = {
        "generated_at": now.isoformat(),
        "mode": "editorial_dry_run",
        "candidate_count": len(candidates),
        "results": results,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    temporary = OUTPUT.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(output, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    temporary.replace(OUTPUT)

    print("\n===== EDITORIAL REVIEW SUMMARY =====")
    print("Candidates:", len(results))
    for status in ("core_ux", "adjacent", "weak", "review"):
        print(
            f"{status}:",
            sum(x["classification"] == status for x in results),
        )
    print("Editorially eligible:", sum(x["eligible"] for x in results))
    print("Report:", OUTPUT.resolve())
    print("EDITORIAL REVIEW: COMPLETE")


if __name__ == "__main__":
    main()
