from __future__ import annotations

from dataclasses import dataclass

from ux_daily_brief.article_identity import normalize_url
from ux_daily_brief.models import Article
from ux_daily_brief.semantic_dedup import (
    compare_stories,
    is_confirmed_duplicate,
)


@dataclass(frozen=True)
class EditionDuplicateDecision:
    status: str
    reason: str
    matched_article_id: str | None = None


def check_edition_duplicate(
    candidate: Article,
    selected: list[Article],
) -> EditionDuplicateDecision:
    candidate_url = normalize_url(candidate.url)

    for previous in selected:
        previous_url = normalize_url(previous.url)

        if candidate.article_id == previous.article_id:
            return EditionDuplicateDecision(
                "duplicate",
                "Same article ID",
                previous.article_id,
            )

        same_roundup = (
            candidate.source == previous.source == "jakob_nielsen"
            and "/p/ux-roundup-" in candidate_url
            and candidate_url == previous_url
        )

        if candidate_url and candidate_url == previous_url and not same_roundup:
            return EditionDuplicateDecision(
                "duplicate",
                "Same normalized URL",
                previous.article_id,
            )

    uncertain = False

    for previous in selected:
        try:
            result = compare_stories(
                candidate.title,
                candidate.excerpt,
                previous.title,
                previous.excerpt,
            )
        except Exception:
            uncertain = True
            continue

        if is_confirmed_duplicate(result):
            return EditionDuplicateDecision(
                "duplicate",
                result["reason"],
                previous.article_id,
            )

        if result["same_story"]:
            uncertain = True

    if uncertain:
        return EditionDuplicateDecision(
            "review",
            "Semantic comparison inconclusive or unavailable",
        )

    return EditionDuplicateDecision(
        "unique",
        "No duplicate found within current edition",
    )
