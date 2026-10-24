from unittest.mock import Mock, patch

from ux_daily_brief.semantic_dedup import (
    compare_stories,
    is_confirmed_duplicate,
)


def test_confirmed_duplicate():
    assert is_confirmed_duplicate({
        "same_story": True,
        "confidence": 0.95,
    })


def test_low_confidence_not_duplicate():
    assert not is_confirmed_duplicate({
        "same_story": True,
        "confidence": 0.70,
    })


def test_same_topic_not_duplicate():
    assert not is_confirmed_duplicate({
        "same_story": False,
        "confidence": 0.99,
    })


def test_mocked_ollama_response():
    response = Mock()
    response.json.return_value = {
        "response": (
            '{"same_story":true,'
            '"confidence":0.91,'
            '"reason":"Both describe the same study."}'
        )
    }

    with patch(
        "ux_daily_brief.semantic_dedup.requests.post",
        return_value=response,
    ) as post:
        result = compare_stories(
            "AI Agents on an Island",
            "Researchers observed AI agents in isolation.",
            "KI-Agenten auf einsamer Insel",
            "Forscher beobachteten isolierte KI-Agenten.",
        )

    assert result["same_story"] is True
    assert is_confirmed_duplicate(result)
    post.assert_called_once()
