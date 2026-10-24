import json
from unittest.mock import Mock, patch

from ux_daily_brief.editorial_review import (
    editorial_eligible,
    review_article,
)
from ux_daily_brief.models import Article


def test_core_ux_eligible():
    assert editorial_eligible({
        "classification": "core_ux"
    })


def test_adjacent_eligible():
    assert editorial_eligible({
        "classification": "adjacent"
    })


def test_weak_not_eligible():
    assert not editorial_eligible({
        "classification": "weak"
    })


def test_review_not_eligible():
    assert not editorial_eligible({
        "classification": "review"
    })


def test_mocked_ollama_review():
    article = Article(
        source="smashing",
        title="Accordion Icons: Which Work Best?",
        url="https://example.com/accordion",
        excerpt="A comparison of accordion icon patterns.",
        origin="rss",
    )

    expected = {
        "classification": "core_ux",
        "evidence": "Accordion icon patterns",
        "reason": "Direct interaction design topic",
    }

    response = Mock()
    response.json.return_value = {
        "response": json.dumps(expected)
    }

    with patch(
        "ux_daily_brief.editorial_review.requests.post",
        return_value=response,
    ):
        result = review_article(article)

    assert result == expected
    assert editorial_eligible(result)
