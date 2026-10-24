from unittest.mock import patch

from ux_daily_brief.edition_duplicates import (
    check_edition_duplicate,
)
from ux_daily_brief.models import Article


def make_article(source, title, url):
    return Article(
        source=source,
        title=title,
        url=url,
        excerpt="Article description.",
        origin="rss",
    )


def test_empty_edition():
    candidate = make_article(
        "page", "UX Article", "https://example.com/1"
    )

    assert check_edition_duplicate(
        candidate, []
    ).status == "unique"


def test_same_url():
    first = make_article(
        "page", "Article A",
        "https://example.com/story?utm_source=email",
    )
    second = make_article(
        "smashing", "Article B",
        "https://example.com/story",
    )

    assert check_edition_duplicate(
        second, [first]
    ).status == "duplicate"


def test_cross_language_same_story():
    first = make_article(
        "techcrunch", "AI Agents on an Island",
        "https://example.com/1",
    )
    second = make_article(
        "t3n_ai", "KI-Agenten auf einer Insel",
        "https://example.com/2",
    )

    with patch(
        "ux_daily_brief.edition_duplicates.compare_stories",
        return_value={
            "same_story": True,
            "confidence": 0.95,
            "reason": "Same experiment",
        },
    ):
        result = check_edition_duplicate(
            second, [first]
        )

    assert result.status == "duplicate"


def test_different_stories():
    first = make_article(
        "page", "Brand Design",
        "https://example.com/1",
    )
    second = make_article(
        "smashing", "Accessibility",
        "https://example.com/2",
    )

    with patch(
        "ux_daily_brief.edition_duplicates.compare_stories",
        return_value={
            "same_story": False,
            "confidence": 0.98,
            "reason": "Different topics",
        },
    ):
        result = check_edition_duplicate(
            second, [first]
        )

    assert result.status == "unique"


def test_ollama_failure_requires_review():
    first = make_article(
        "page", "Brand Design",
        "https://example.com/1",
    )
    second = make_article(
        "smashing", "Accessibility",
        "https://example.com/2",
    )

    with patch(
        "ux_daily_brief.edition_duplicates.compare_stories",
        side_effect=RuntimeError("Ollama unavailable"),
    ):
        result = check_edition_duplicate(
            second, [first]
        )

    assert result.status == "review"
