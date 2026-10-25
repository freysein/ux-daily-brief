from __future__ import annotations

from dataclasses import dataclass

from ux_daily_brief.fulltext_smashing import (
    FulltextExtractionError,
    fetch_smashing_text,
)
from ux_daily_brief.fulltext_page import (
    PageExtractionError,
    fetch_page_text,
)
from ux_daily_brief.models import Article


FULLTEXT_SOURCES = {"smashing", "page"}


@dataclass(frozen=True)
class EnrichmentResult:
    context: str | None
    status: str
    reason: str | None = None


def enrich_article(article: Article) -> EnrichmentResult:
    if article.source not in FULLTEXT_SOURCES:
        return EnrichmentResult(
            context=None,
            status="not_permitted",
            reason="Source not approved for fulltext retrieval",
        )

    try:
        if article.source == "smashing":
            context = fetch_smashing_text(article.url)
        elif article.source == "page":
            context = fetch_page_text(article.url)
        else:
            raise ValueError("Unsupported fulltext source")
    except (FulltextExtractionError, PageExtractionError) as exc:
        return EnrichmentResult(
            context=None,
            status="fetch_failed",
            reason=str(exc),
        )

    return EnrichmentResult(
        context=context,
        status="enriched",
    )
