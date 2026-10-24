from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from ux_daily_brief.freshness import is_fresh
from ux_daily_brief.models import Article


@dataclass
class SelectionResult:
    selected: list[Article] = field(default_factory=list)
    excluded: list[dict] = field(default_factory=list)


def select_articles(
    articles: list[Article],
    *,
    now: datetime,
    min_score: float = 30.0,
    max_age_hours: int = 72,
    max_articles: int = 9,
    max_per_source: int = 2,
) -> SelectionResult:
    if max_articles < 1 or max_per_source < 1:
        raise ValueError("Article limits must be positive")

    result = SelectionResult()
    eligible = []

    for article in articles:
        if article.score is None or article.score < min_score:
            result.excluded.append({
                "article_id": article.article_id,
                "reason": "low_score_or_unscored",
            })
            continue

        if not is_fresh(
            article,
            now=now,
            max_age_hours=max_age_hours,
        ):
            result.excluded.append({
                "article_id": article.article_id,
                "reason": "not_fresh",
            })
            continue

        eligible.append(article)

    eligible.sort(
        key=lambda article: (
            -article.score,
            article.source,
            article.title.casefold(),
        )
    )

    source_counts = {}

    for article in eligible:
        if len(result.selected) >= max_articles:
            result.excluded.append({
                "article_id": article.article_id,
                "reason": "article_limit",
            })
            continue

        count = source_counts.get(article.source, 0)

        if count >= max_per_source:
            result.excluded.append({
                "article_id": article.article_id,
                "reason": "source_limit",
            })
            continue

        result.selected.append(article)
        source_counts[article.source] = count + 1

    return result
