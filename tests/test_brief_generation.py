import json
from unittest.mock import Mock, patch

import pytest

from ux_daily_brief.brief_generation import (
    BriefGenerationError,
    generate_brief_entry,
)
from ux_daily_brief.models import Article


def make_article():
    return Article(
        source="smashing",
        title="Accordion Icons: Which Work Best?",
        url="https://example.com/accordion",
        excerpt="A comparison of accordion icon patterns.",
        origin="rss",
    )


def mock_response(data):
    response = Mock()
    response.json.return_value = {
        "response": json.dumps(data)
    }
    return response


def valid_result():
    return {
        "title": "Choosing Better Accordion Icons",
        "summary": " ".join(["Design"] * 80),
        "ux_impact": "Potential implication: Review icon clarity.",
        "category": "Design Practice & Technology",
        "insufficient_context": False,
    }


def test_successful_generation():
    with patch(
        "ux_daily_brief.brief_generation.requests.post",
        return_value=mock_response(valid_result()),
    ):
        entry = generate_brief_entry(
            make_article(), "core_ux"
        )

    assert entry.source == "smashing"
    assert len(entry.summary.split()) == 80


def test_insufficient_context_rejected():
    data = valid_result()
    data["insufficient_context"] = True

    with patch(
        "ux_daily_brief.brief_generation.requests.post",
        return_value=mock_response(data),
    ):
        with pytest.raises(BriefGenerationError):
            generate_brief_entry(make_article(), "core_ux")


def test_short_summary_rejected():
    data = valid_result()
    data["summary"] = "Too short."

    with patch(
        "ux_daily_brief.brief_generation.requests.post",
        return_value=mock_response(data),
    ):
        with pytest.raises(BriefGenerationError):
            generate_brief_entry(make_article(), "core_ux")


def test_invalid_category_rejected():
    data = valid_result()
    data["category"] = "General Technology"

    with patch(
        "ux_daily_brief.brief_generation.requests.post",
        return_value=mock_response(data),
    ):
        with pytest.raises(BriefGenerationError):
            generate_brief_entry(make_article(), "core_ux")


def test_short_summary_repaired_successfully():
    initial = valid_result()
    initial["summary"] = "A short factual summary."

    repaired = {
        "summary": " ".join(["Design"] * 80),
        "insufficient_context": False,
    }

    with patch(
        "ux_daily_brief.brief_generation.requests.post",
        side_effect=[
            mock_response(initial),
            mock_response(repaired),
        ],
    ) as post:
        entry = generate_brief_entry(
            make_article(), "core_ux"
        )

    assert len(entry.summary.split()) == 80
    assert post.call_count == 2


def test_repair_rejects_insufficient_context():
    initial = valid_result()
    initial["summary"] = "Too short."

    repaired = {
        "summary": "Still too short.",
        "insufficient_context": True,
    }

    with patch(
        "ux_daily_brief.brief_generation.requests.post",
        side_effect=[
            mock_response(initial),
            mock_response(repaired),
        ],
    ):
        with pytest.raises(
            BriefGenerationError,
            match="Insufficient source information",
        ):
            generate_brief_entry(make_article(), "core_ux")


def test_repair_rejects_invalid_word_count():
    initial = valid_result()
    initial["summary"] = "Too short."

    repaired = {
        "summary": "Still too short.",
        "insufficient_context": False,
    }

    with patch(
        "ux_daily_brief.brief_generation.requests.post",
        side_effect=[
            mock_response(initial),
            mock_response(repaired),
        ],
    ):
        with pytest.raises(
            BriefGenerationError,
            match="Summary repair failed validation",
        ):
            generate_brief_entry(make_article(), "core_ux")


def test_valid_summary_needs_no_repair():
    with patch(
        "ux_daily_brief.brief_generation.requests.post",
        return_value=mock_response(valid_result()),
    ) as post:
        generate_brief_entry(make_article(), "core_ux")

    assert post.call_count == 1


def test_editorial_rules_in_generation_prompt():
    with patch(
        "ux_daily_brief.brief_generation.requests.post",
        return_value=mock_response(valid_result()),
    ) as post:
        generate_brief_entry(make_article(), "core_ux")

    prompt = post.call_args.kwargs["json"]["prompt"]

    assert "Target 85 English words" in prompt
    assert "Mention each finding or recommendation only once" in prompt
    assert "The UX impact explains what practitioners should do" in prompt


def test_editorial_rules_in_repair_prompt():
    initial = valid_result()
    initial["summary"] = "Too short."

    repaired = {
        "summary": " ".join(["Design"] * 85),
        "insufficient_context": False,
    }

    with patch(
        "ux_daily_brief.brief_generation.requests.post",
        side_effect=[
            mock_response(initial),
            mock_response(repaired),
        ],
    ) as post:
        generate_brief_entry(make_article(), "core_ux")

    repair_prompt = post.call_args_list[1].kwargs["json"]["prompt"]

    assert "TARGET 85 English words" in repair_prompt
    assert "Mention each finding or recommendation only once" in repair_prompt
    assert "Do not repeat summary sentences in the UX impact" in repair_prompt
