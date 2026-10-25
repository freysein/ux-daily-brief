from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from ux_daily_brief.source_enrichment import enrich_article
from ux_daily_brief.brief_generation import (
    BriefGenerationError,
    generate_brief_entry,
)
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

    results = []

    for index, selected in enumerate(
        selection["selected"], start=1
    ):
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

        try:
            enrichment = enrich_article(article)

            print(
                f"Enrichment: {enrichment.status}"
            )

            entry = generate_brief_entry(
                article,
                editorial_classification=classification,
                source_context=enrichment.context,
            )

            results.append({
                "status": "generated",
                "article_id": article.article_id,
                "entry": asdict(entry),
            })

            print(
                f"[{index}] GENERATED | "
                f"{article.source} | {article.title}"
            )

        except (BriefGenerationError, ValueError, KeyError) as exc:
            results.append({
                "status": "rejected",
                "article_id": article.article_id,
                "title": article.title,
                "reason": str(exc),
            })

            print(
                f"[{index}] REJECTED | "
                f"{article.source} | {article.title}"
            )
            print("Reason:", str(exc))

    generated = sum(
        result["status"] == "generated"
        for result in results
    )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(
            {
                "mode": "generation_test",
                "selected": len(results),
                "generated": generated,
                "rejected": len(results) - generated,
                "results": results,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print("\n===== BRIEF GENERATION SUMMARY =====")
    print("Selected:", len(results))
    print("Generated:", generated)
    print("Rejected:", len(results) - generated)
    print("Output:", OUTPUT.resolve())
    print("NO EMAILS SENT")
    print("BRIEF GENERATION TEST: COMPLETE")


if __name__ == "__main__":
    main()
