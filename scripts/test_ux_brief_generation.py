from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from ux_daily_brief.brief_pipeline import generate_brief
from ux_daily_brief.models import Article


SELECTION = Path("data/reports/ux_daily_selection_dry_run.json")
SCORING = Path("data/reports/ux_scoring_incremental.json")
OUTPUT = Path("data/reports/ux_brief_generation_test.json")


def main():
    selection = json.loads(
        SELECTION.read_text(encoding="utf-8")
    )
    scoring = json.loads(
        SCORING.read_text(encoding="utf-8")
    )

    source_rows = {
        row["article_id"]: row
        for row in scoring["results"]
    }

    candidates = []

    for selected in selection["selected"]:
        source = source_rows[selected["article_id"]]

        article = Article(
            source=source["source"],
            title=source["title"],
            url=source["url"],
            excerpt=source.get("excerpt") or "",
            origin=source["origin"],
        )

        if article.article_id != selected["article_id"]:
            raise RuntimeError("Article identity mismatch")

        classification = selected.get(
            "editorial_classification", "weak"
        )

        candidates.append((article, classification))

    result = generate_brief(
        candidates,
        max_articles=9,
    )

    output = {
        "mode": "generation_test",
        "candidates": len(candidates),
        "attempted": result.attempted,
        "generated": len(result.entries),
        "rejected": len(result.rejected),
        "target_reached": result.target_reached,
        "status": result.status,
        "entries": [
            asdict(entry) for entry in result.entries
        ],
        "rejections": result.rejected,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(
            output,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print("===== BRIEF PIPELINE DRY RUN =====")
    print("Candidates:", len(candidates))
    print("Attempted:", result.attempted)
    print("Generated:", len(result.entries))
    print("Rejected:", len(result.rejected))
    print("Target reached:", result.target_reached)
    print("Quality status:", result.status)

    print("\n===== GENERATED ARTICLES =====")
    for index, entry in enumerate(result.entries, 1):
        print(
            f"{index:02d}. {entry.source:12} | "
            f"{entry.title}"
        )

    print("\n===== REJECTED ARTICLES =====")
    for rejected in result.rejected:
        print(
            f"{rejected['source']:12} | "
            f"{rejected['title']}"
        )
        print("Reason:", rejected["reason"])

    print("\nREPORT:", OUTPUT.resolve())
    print("NO EMAILS SENT")
    print("NO PUBLICATIONS RECORDED")
    print("BRIEF PIPELINE DRY RUN: COMPLETE")


if __name__ == "__main__":
    main()
