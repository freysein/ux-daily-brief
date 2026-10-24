from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from ux_daily_brief.article_pipeline import extract_from_inbox
from ux_daily_brief.collectors.rss import collect_rss
from ux_daily_brief.deduplication import deduplicate_articles
from ux_daily_brief.prioritization import prioritize_articles
from ux_daily_brief.ollama_scoring import assess_article
from ux_daily_brief.scoring import (
    QUALIFICATION_THRESHOLD,
    PRIORITY_THRESHOLD,
)
from ux_daily_brief.scoring_cache import (
    load_cached,
    save_cached,
)

ROOT = Path(__file__).resolve().parents[1]
INBOX = ROOT / "data/inbox/newsletters"
OUTPUT = ROOT / "data/reports/ux_scoring_incremental.json"


def qualification(entry):
    score = entry.get("score")
    if entry.get("status") == "scored" and score is not None:
        entry["qualified"] = score >= QUALIFICATION_THRESHOLD
        entry["priority"] = score >= PRIORITY_THRESHOLD
    else:
        entry["qualified"] = False
        entry["priority"] = False
    return entry


def save_report(results, source_status, total):
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "qualification_threshold": QUALIFICATION_THRESHOLD,
        "priority_threshold": PRIORITY_THRESHOLD,
        "total_articles": total,
        "processed_articles": len(results),
        "rss_status": source_status,
        "results": results,
    }

    temporary = OUTPUT.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    temporary.replace(OUTPUT)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit-per-feed", type=int, default=10)
    parser.add_argument("--max-new", type=int, default=0)
    args = parser.parse_args()

    if args.limit_per_feed < 1 or args.max_new < 0:
        parser.error("Invalid limits")

    newsletters = extract_from_inbox(INBOX)
    rss_articles, rss_status = collect_rss(args.limit_per_feed)

    combined = newsletters + rss_articles
    articles = prioritize_articles(
        deduplicate_articles(combined)
    )

    print("Newsletter articles:", len(newsletters), flush=True)
    print("RSS articles:", len(rss_articles), flush=True)
    print("Unique articles:", len(articles), flush=True)

    if any(x["status"] != "ok" for x in rss_status.values()):
        print("WARNING: One or more RSS feeds failed", flush=True)

    results = []
    new_assessments = 0

    for index, article in enumerate(articles, 1):
        cached = load_cached(article)

        if cached is not None:
            entry = article.to_dict()
            entry.update(cached)
            entry["cached"] = True

        elif args.max_new and new_assessments >= args.max_new:
            entry = article.to_dict()
            entry["status"] = "deferred"
            entry["cached"] = False

        else:
            new_assessments += 1
            entry = article.to_dict()
            entry["cached"] = False

            try:
                assessment = assess_article(article)
                entry["reason"] = assessment.reason
                entry["ux_impact"] = assessment.ux_impact
                entry["insufficient_context"] = (
                    assessment.insufficient_context
                )

                if assessment.score is None:
                    entry["status"] = "insufficient_context"
                else:
                    entry["status"] = "scored"
                    entry["score"] = assessment.score.total
                    entry["score_components"] = (
                        assessment.score.components
                    )

                    save_cached(article, {
                        "status": "scored",
                        "score": assessment.score.total,
                        "score_components": assessment.score.components,
                        "reason": assessment.reason,
                        "ux_impact": assessment.ux_impact,
                        "insufficient_context": False,
                    })

            except Exception as error:
                entry["status"] = "error"
                entry["error"] = str(error)

        qualification(entry)
        results.append(entry)

        score = entry.get("score")
        score_text = f"{score:.1f}" if score is not None else "N/A"

        print(
            f"[{index}/{len(articles)}] "
            f"{article.source} | {entry['status']} | "
            f"{score_text} | {article.title[:55]}",
            flush=True,
        )

        save_report(results, rss_status, len(articles))

    print("\n===== SUMMARY =====")
    for status in ("scored", "insufficient_context", "error", "deferred"):
        print(status, sum(x["status"] == status for x in results))

    print("Cached:", sum(x.get("cached", False) for x in results))
    print("Qualified:", sum(x["qualified"] for x in results))
    print("New assessments:", new_assessments)
    print("REPORT:", OUTPUT)
    print("INCREMENTAL SCORING: COMPLETE")


if __name__ == "__main__":
    main()
