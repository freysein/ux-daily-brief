from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from ux_daily_brief.article_pipeline import extract_from_inbox
from ux_daily_brief.ollama_scoring import assess_article


ROOT = Path(__file__).resolve().parents[1]
INBOX = ROOT / "data/inbox/newsletters"
OUTPUT = ROOT / "data/reports/ux_scoring_test.json"


def main():
    articles = extract_from_inbox(INBOX)
    results = []

    print("ARTICLES FOUND:", len(articles), flush=True)

    for index, article in enumerate(articles, 1):
        print(
            f"[{index}/{len(articles)}] {article.source}: "
            f"{article.title[:75]}",
            flush=True,
        )

        entry = article.to_dict()

        try:
            assessment = assess_article(article)

            entry["insufficient_context"] = (
                assessment.insufficient_context
            )
            entry["reason"] = assessment.reason
            entry["ux_impact"] = assessment.ux_impact

            if assessment.score is not None:
                entry["score"] = assessment.score.total
                entry["score_components"] = (
                    assessment.score.components
                )
                entry["qualified"] = assessment.score.qualified
                entry["priority"] = assessment.score.priority
                entry["status"] = "scored"

                print(
                    f"  Score: {assessment.score.total:.2f} "
                    f"| Qualified: {assessment.score.qualified}",
                    flush=True,
                )
            else:
                entry["qualified"] = False
                entry["priority"] = False
                entry["status"] = "insufficient_context"
                print("  Insufficient context", flush=True)

        except Exception as error:
            entry["status"] = "error"
            entry["qualified"] = False
            entry["priority"] = False
            entry["error"] = str(error)
            print(f"  ERROR: {error}", flush=True)

        results.append(entry)

        OUTPUT.parent.mkdir(parents=True, exist_ok=True)

        OUTPUT.write_text(
            json.dumps(
                {
                    "generated_at": datetime.now(
                        timezone.utc
                    ).isoformat(),
                    "total_articles": len(articles),
                    "results": results,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    print("\n===== SUMMARY =====")
    print("Scored:", sum(
        x["status"] == "scored" for x in results
    ))
    print("Qualified:", sum(
        x["qualified"] for x in results
    ))
    print("Insufficient context:", sum(
        x["status"] == "insufficient_context" for x in results
    ))
    print("Errors:", sum(
        x["status"] == "error" for x in results
    ))
    print("REPORT:", OUTPUT)
    print("BATCH SCORING: COMPLETE")


if __name__ == "__main__":
    main()
