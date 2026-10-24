import json

import pytest

from ux_daily_brief.models import Article
from ux_daily_brief.ollama_scoring import assess_article


def example_article():
    return Article(
        source="techcrunch",
        title="AI and user experience research",
        url="https://example.com/article",
        excerpt="A study describes practical UX research methods.",
        origin="newsletter",
    )


def model_answer(**overrides):
    result = {
        "ux_relevance": 90,
        "practical_usefulness": 80,
        "novelty": 75,
        "credibility": 85,
        "business_impact": 70,
        "reason": "Relevant UX research with practical implications.",
        "ux_impact": "Potential implication: Teams can examine these methods.",
        "insufficient_context": False,
    }
    result.update(overrides)
    return result


def mock_response(monkeypatch, data):
    class Response:
        def raise_for_status(self):
            pass

        def json(self):
            return {"response": json.dumps(data)}

    def fake_post(*args, **kwargs):
        return Response()

    monkeypatch.setattr(
        "ux_daily_brief.ollama_scoring.requests.post",
        fake_post,
    )


def test_valid_assessment(monkeypatch):
    mock_response(monkeypatch, model_answer())

    result = assess_article(example_article())

    assert result.score is not None
    assert result.score.total == 82.0
    assert result.score.qualified
    assert not result.insufficient_context


def test_insufficient_context(monkeypatch):
    mock_response(
        monkeypatch,
        model_answer(
            insufficient_context=True,
            ux_impact="Missing information: Specific research findings.",
        ),
    )

    result = assess_article(example_article())

    assert result.score is None
    assert result.insufficient_context


def test_invalid_score_rejected(monkeypatch):
    mock_response(
        monkeypatch,
        model_answer(ux_relevance=120),
    )

    with pytest.raises(ValueError):
        assess_article(example_article())


def test_missing_reason_rejected(monkeypatch):
    mock_response(
        monkeypatch,
        model_answer(reason=""),
    )

    with pytest.raises(ValueError):
        assess_article(example_article())


def test_invalid_boolean_rejected(monkeypatch):
    mock_response(
        monkeypatch,
        model_answer(insufficient_context="false"),
    )

    with pytest.raises(ValueError):
        assess_article(example_article())


def test_invalid_ux_impact_prefix(monkeypatch):
    mock_response(
        monkeypatch,
        model_answer(ux_impact="UX teams should change their process."),
    )

    with pytest.raises(ValueError, match="Invalid UX impact prefix"):
        assess_article(example_article())


def test_missing_information_requires_insufficient_context(monkeypatch):
    mock_response(
        monkeypatch,
        model_answer(
            insufficient_context=False,
            ux_impact="Missing information: Research details.",
        ),
    )

    with pytest.raises(ValueError, match="Missing information requires"):
        assess_article(example_article())


def test_label_conflict_triggers_repair(monkeypatch):
    responses = [
        model_answer(
            insufficient_context=True,
            ux_impact="Potential implication: Not enough details.",
        ),
        model_answer(
            insufficient_context=False,
            ux_impact="Potential implication: UX teams may investigate.",
        ),
    ]

    calls = []

    class Response:
        def __init__(self, data):
            self.data = data

        def raise_for_status(self):
            pass

        def json(self):
            return {"response": json.dumps(self.data)}

    def fake_post(*args, **kwargs):
        calls.append(kwargs["json"])
        return Response(responses[len(calls) - 1])

    monkeypatch.setattr(
        "ux_daily_brief.ollama_scoring.requests.post",
        fake_post,
    )

    result = assess_article(example_article())

    assert len(calls) == 2
    assert result.insufficient_context is False
    assert result.score is not None
    assert result.ux_impact.startswith("Potential implication: ")


def test_persistent_label_conflict_raises(monkeypatch):
    responses = [
        model_answer(
            insufficient_context=True,
            ux_impact="Potential implication: Unclear topic.",
        ),
        model_answer(
            insufficient_context=True,
            ux_impact="Potential implication: Still unclear.",
        ),
    ]

    calls = []

    class Response:
        def __init__(self, data):
            self.data = data

        def raise_for_status(self):
            pass

        def json(self):
            return {"response": json.dumps(self.data)}

    def fake_post(*args, **kwargs):
        calls.append(kwargs["json"])
        return Response(responses[len(calls) - 1])

    monkeypatch.setattr(
        "ux_daily_brief.ollama_scoring.requests.post",
        fake_post,
    )

    with pytest.raises(
        ValueError,
        match="Insufficient context requires Missing information",
    ):
        assess_article(example_article())

    assert len(calls) == 2
