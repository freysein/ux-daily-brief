from unittest.mock import patch

from ux_daily_brief.fulltext_smashing import (
    FulltextExtractionError,
)
from ux_daily_brief.models import Article
from ux_daily_brief.source_enrichment import enrich_article


def make_article(source="smashing"):
    return Article(
        source=source,
        title="Accordion Icons",
        url="https://www.smashingmagazine.com/example/",
        excerpt="An article about accordion interactions.",
        origin="rss",
    )


def test_approved_source_enriched():
    with patch(
        "ux_daily_brief.source_enrichment.fetch_smashing_text",
        return_value="Detailed article context",
    ) as fetch:
        result = enrich_article(make_article())

    assert result.status == "enriched"
    assert result.context == "Detailed article context"
    fetch.assert_called_once()


def test_unapproved_source_not_fetched():
    with patch(
        "ux_daily_brief.source_enrichment.fetch_smashing_text",
    ) as fetch:
        result = enrich_article(make_article("techcrunch"))

    assert result.status == "not_permitted"
    assert result.context is None
    fetch.assert_not_called()


def test_fetch_failure_falls_back():
    with patch(
        "ux_daily_brief.source_enrichment.fetch_smashing_text",
        side_effect=FulltextExtractionError("HTTP error"),
    ):
        result = enrich_article(make_article())

    assert result.status == "fetch_failed"
    assert result.context is None


def test_page_source_enriched():
    with patch(
        "ux_daily_brief.source_enrichment.fetch_page_text",
        return_value="Detailed PAGE article text",
    ) as fetch:
        result = enrich_article(make_article("page"))

    assert result.status == "enriched"
    assert result.context == "Detailed PAGE article text"
    fetch.assert_called_once()


def test_page_failure_falls_back():
    from ux_daily_brief.fulltext_page import PageExtractionError

    with patch(
        "ux_daily_brief.source_enrichment.fetch_page_text",
        side_effect=PageExtractionError("PAGE unavailable"),
    ):
        result = enrich_article(make_article("page"))

    assert result.status == "fetch_failed"
    assert result.context is None
