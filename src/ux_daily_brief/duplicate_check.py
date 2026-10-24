from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from ux_daily_brief.models import Article
from ux_daily_brief.publication_history import (
    DEFAULT_DB_PATH,
    recently_published_stories,
    was_recently_published,
)
from ux_daily_brief.semantic_dedup import (
    compare_stories,
    is_confirmed_duplicate,
)


@dataclass(frozen=True)
class DuplicateDecision:
    status: str
    reason: str
    matched_article_id: str | None = None


def check_duplicate(
    article: Article,
    db_path: Path = DEFAULT_DB_PATH,
    now: datetime | None = None,
    max_semantic_checks: int = 20,
) -> DuplicateDecision:
    if max_semantic_checks < 1:
        raise ValueError("max_semantic_checks must be positive")

    if was_recently_published(
        article.article_id,
        article.url,
        days=7,
        db_path=db_path,
        now=now,
    ):
        return DuplicateDecision(
            "duplicate",
            "Already published within 7 days (ID or URL)",
        )

    history = recently_published_stories(
        days=14,
        db_path=db_path,
        now=now,
    )

    if len(history) > max_semantic_checks:
        return DuplicateDecision(
            "review",
            "Too many historical stories for complete comparison",
        )

    uncertain = False

    for previous in history:
        try:
            result = compare_stories(
                article.title,
                article.excerpt,
                previous["title"],
                previous["excerpt"],
            )
        except (ValueError, KeyError, TypeError, OSError, RuntimeError):
            uncertain = True
            continue
        except Exception:
            uncertain = True
            continue

        if is_confirmed_duplicate(result):
            return DuplicateDecision(
                "duplicate",
                result["reason"],
                previous["article_id"],
            )

        if result["same_story"]:
            uncertain = True

    if uncertain:
        return DuplicateDecision(
            "review",
            "Semantic comparison inconclusive or unavailable",
        )

    return DuplicateDecision(
        "unique",
        "No duplicate found in publication history",
    )
