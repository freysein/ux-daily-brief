from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable
from datetime import datetime
from pathlib import Path

from ux_daily_brief.duplicate_check import check_duplicate
from ux_daily_brief.edition_duplicates import check_edition_duplicate
from ux_daily_brief.editorial_selection import select_articles
from ux_daily_brief.models import Article
from ux_daily_brief.publication_history import DEFAULT_DB_PATH


@dataclass
class DailySelectionResult:
    selected: list[Article] = field(default_factory=list)
    excluded: list[dict] = field(default_factory=list)
    review: list[dict] = field(default_factory=list)


def build_daily_selection(
    articles: list[Article],
    *,
    now: datetime,
    db_path: Path = DEFAULT_DB_PATH,
    max_articles: int = 9,
    max_per_source: int = 2,
    editorial_results: dict[str, dict] | None = None,
    min_articles: int = 6,
    sponsorship_check: Callable[[Article], str] | None = None,
) -> DailySelectionResult:
    preliminary = select_articles(
        articles,
        now=now,
        max_articles=len(articles) or 1,
        max_per_source=max(len(articles), 1),
    )

    result = DailySelectionResult(
        excluded=list(preliminary.excluded),
    )

    candidates = preliminary.selected

    if editorial_results is not None:
        ranks = {"core_ux": 0, "adjacent": 1, "weak": 2}

        candidates = sorted(
            candidates,
            key=lambda article: (
                ranks.get(
                    editorial_results.get(
                        article.article_id, {}
                    ).get("classification"),
                    3,
                ),
                -article.score,
                article.source,
                article.title.casefold(),
            ),
        )

    source_counts: dict[str, int] = {}

    for article in candidates:
        if editorial_results is not None:
            classification = editorial_results.get(
                article.article_id, {}
            ).get("classification")

            if classification not in {
                "core_ux", "adjacent", "weak"
            }:
                result.review.append({
                    "article_id": article.article_id,
                    "reason": "editorial_review_required",
                })
                continue

            if (
                classification == "weak"
                and len(result.selected) >= min_articles
            ):
                result.excluded.append({
                    "article_id": article.article_id,
                    "reason": "weak_fallback_not_needed",
                })
                continue

        if len(result.selected) >= max_articles:
            result.excluded.append({
                "article_id": article.article_id,
                "reason": "article_limit",
            })
            continue

        if source_counts.get(article.source, 0) >= max_per_source:
            result.excluded.append({
                "article_id": article.article_id,
                "reason": "source_limit",
            })
            continue

        decision = check_duplicate(
            article,
            db_path=db_path,
            now=now,
        )

        if decision.status == "duplicate":
            result.excluded.append({
                "article_id": article.article_id,
                "reason": "duplicate",
                "detail": decision.reason,
            })
            continue

        if decision.status == "review":
            result.review.append({
                "article_id": article.article_id,
                "reason": decision.reason,
            })
            continue

        edition_decision = check_edition_duplicate(
            article,
            result.selected,
        )

        if edition_decision.status == "duplicate":
            result.excluded.append({
                "article_id": article.article_id,
                "reason": "edition_duplicate",
                "detail": edition_decision.reason,
            })
            continue

        if edition_decision.status == "review":
            result.review.append({
                "article_id": article.article_id,
                "reason": edition_decision.reason,
            })
            continue

        if sponsorship_check is not None:
            sponsorship = sponsorship_check(article)

            if sponsorship == "sponsored":
                result.excluded.append({
                    "article_id": article.article_id,
                    "reason": "sponsored_content",
                })
                continue

            if sponsorship == "review":
                result.review.append({
                    "article_id": article.article_id,
                    "reason": "sponsorship_unverified",
                })
                continue

            if sponsorship != "not_sponsored":
                raise ValueError(
                    f"Invalid sponsorship result: {sponsorship}"
                )

        result.selected.append(article)
        source_counts[article.source] = (
            source_counts.get(article.source, 0) + 1
        )

    return result
