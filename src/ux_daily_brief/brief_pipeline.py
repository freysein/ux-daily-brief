from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import requests

from ux_daily_brief.brief_content import BriefEntry
from ux_daily_brief.brief_generation import (
    BriefGenerationError,
    generate_brief_entry,
)
from ux_daily_brief.models import Article
from ux_daily_brief.source_enrichment import (
    EnrichmentResult,
    enrich_article,
)


@dataclass
class BriefPipelineResult:
    entries: list[BriefEntry] = field(default_factory=list)
    rejected: list[dict] = field(default_factory=list)
    attempted: int = 0
    target_reached: bool = False
    status: str = "empty"


def generate_brief(
    candidates: list[tuple[Article, str]],
    *,
    max_articles: int = 9,
    min_articles: int = 6,
    enrich: Callable[[Article], EnrichmentResult] = enrich_article,
    generate: Callable[..., BriefEntry] = generate_brief_entry,
) -> BriefPipelineResult:
    """
    Generate entries from candidates already approved by
    the editorial selection pipeline.

    This function does not establish editorial eligibility.
    """
    if max_articles < 1:
        raise ValueError("max_articles must be positive")

    if not 1 <= min_articles <= max_articles:
        raise ValueError("Invalid minimum article count")

    result = BriefPipelineResult()
    seen_ids = set()

    for article, classification in candidates:
        if len(result.entries) >= max_articles:
            break

        if article.article_id in seen_ids:
            raise ValueError(
                f"Duplicate candidate ID: {article.article_id}"
            )
        seen_ids.add(article.article_id)

        result.attempted += 1

        try:
            enrichment = enrich(article)

            entry = generate(
                article,
                editorial_classification=classification,
                source_context=enrichment.context,
            )

            if entry.article_id != article.article_id:
                raise BriefGenerationError(
                    "Generated article identity mismatch"
                )

            result.entries.append(entry)

        except (
            BriefGenerationError,
            requests.RequestException,
            ValueError,
            KeyError,
        ) as exc:
            result.rejected.append({
                "article_id": article.article_id,
                "source": article.source,
                "title": article.title,
                "reason": str(exc),
            })

    result.target_reached = (
        len(result.entries) >= max_articles
    )

    if len(result.entries) >= min_articles:
        result.status = "complete"
    elif result.entries:
        result.status = "partial"
    else:
        result.status = "empty"

    return result
