from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable
from datetime import datetime, timedelta
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
    fallback_max_age_hours: int | None = None,
    fallback_min_score: float = 55.0,
) -> DailySelectionResult:
    preliminary = select_articles(
        articles,
        now=now,
        max_articles=len(articles) or 1,
        max_per_source=max(len(articles), 1),
        max_age_hours=fallback_max_age_hours or 72,
    )

    result = DailySelectionResult(
        excluded=list(preliminary.excluded),
    )

    candidates = preliminary.selected

    def article_age(article: Article):
        timestamp = (
            article.published_at
            if article.origin == "rss"
            else article.received_at
        )

        if timestamp is None or timestamp.tzinfo is None:
            return None

        return now - timestamp

    if fallback_max_age_hours is not None:
        if fallback_max_age_hours <= 72:
            raise ValueError(
                "Fallback window must exceed 72 hours"
            )

        filtered = []

        for article in candidates:
            age = article_age(article)

            if age is None:
                result.review.append({
                    "article_id": article.article_id,
                    "reason": "fallback_timestamp_unverified",
                })
                continue

            if (
                age > timedelta(hours=72)
                and (
                    article.score is None
                    or article.score < fallback_min_score
                )
            ):
                result.excluded.append({
                    "article_id": article.article_id,
                    "reason": "fallback_score_too_low",
                })
                continue

            filtered.append(article)

        candidates = filtered

    if editorial_results is not None:
        ranks = {"core_ux": 0, "adjacent": 1, "weak": 2}

        candidates = sorted(
            candidates,
            key=lambda article: (
                (
                    1
                    if fallback_max_age_hours is not None
                    and article_age(article) > timedelta(hours=72)
                    else 0
                ),
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
