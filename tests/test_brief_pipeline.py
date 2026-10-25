from unittest.mock import Mock

import pytest

from ux_daily_brief.brief_generation import BriefGenerationError
from ux_daily_brief.brief_pipeline import generate_brief
from ux_daily_brief.models import Article
from ux_daily_brief.source_enrichment import EnrichmentResult


def article(number):
    return Article(
        source=f"source_{number}",
        title=f"UX research article {number}",
        url=f"https://example.com/article/{number}",
        excerpt="Research into digital user experiences.",
        origin="rss",
    )


def no_enrichment(_article):
    return EnrichmentResult(
        context=None,
        status="not_permitted",
    )


def test_rejected_article_triggers_replacement():
    items = [article(i) for i in range(3)]
    calls = []

    def generate(item, **kwargs):
        calls.append(item.article_id)
        if item.article_id == items[0].article_id:
            raise BriefGenerationError("Insufficient context")
        return Mock(article_id=item.article_id)

    result = generate_brief(
        [(item, "core_ux") for item in items],
        max_articles=2,
        min_articles=2,
        enrich=no_enrichment,
        generate=generate,
    )

    assert len(result.entries) == 2
    assert result.attempted == 3
    assert len(result.rejected) == 1
    assert result.target_reached
    assert calls == [item.article_id for item in items]


def test_insufficient_candidates_reported():
    items = [article(1), article(2)]

    def generate(item, **kwargs):
        if item.article_id == items[0].article_id:
            raise BriefGenerationError("Too little context")
        return Mock(article_id=item.article_id)

    result = generate_brief(
        [(item, "core_ux") for item in items],
        max_articles=2,
        min_articles=2,
        enrich=no_enrichment,
        generate=generate,
    )

    assert len(result.entries) == 1
    assert result.attempted == 2
    assert not result.target_reached


def test_stops_after_reaching_target():
    items = [article(i) for i in range(4)]
    generate = Mock(
        side_effect=lambda item, **kwargs: Mock(
            article_id=item.article_id
        )
    )

    result = generate_brief(
        [(item, "core_ux") for item in items],
        max_articles=2,
        min_articles=2,
        enrich=no_enrichment,
        generate=generate,
    )

    assert len(result.entries) == 2
    assert result.attempted == 2
    assert generate.call_count == 2


def test_duplicate_candidate_rejected():
    item = article(1)

    with pytest.raises(ValueError, match="Duplicate candidate"):
        generate_brief(
            [(item, "core_ux"), (item, "core_ux")],
            max_articles=2,
            min_articles=2,
            enrich=no_enrichment,
            generate=lambda item, **kwargs: Mock(
                article_id=item.article_id
            ),
        )


def test_complete_status_when_minimum_reached():
    items = [article(i) for i in range(6)]

    result = generate_brief(
        [(item, "core_ux") for item in items],
        min_articles=6,
        max_articles=9,
        enrich=no_enrichment,
        generate=lambda item, **kwargs: Mock(
            article_id=item.article_id
        ),
    )

    assert result.status == "complete"
    assert not result.target_reached


def test_partial_status_below_minimum():
    items = [article(i) for i in range(3)]

    result = generate_brief(
        [(item, "core_ux") for item in items],
        min_articles=6,
        max_articles=9,
        enrich=no_enrichment,
        generate=lambda item, **kwargs: Mock(
            article_id=item.article_id
        ),
    )

    assert result.status == "partial"


def test_empty_status_without_candidates():
    result = generate_brief(
        [],
        min_articles=6,
        max_articles=9,
        enrich=no_enrichment,
    )

    assert result.status == "empty"
    assert result.attempted == 0


def test_invalid_minimum_rejected():
    with pytest.raises(ValueError):
        generate_brief(
            [],
            min_articles=10,
            max_articles=9,
            enrich=no_enrichment,
        )
