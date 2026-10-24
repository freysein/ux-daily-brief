import pytest

from ux_daily_brief.topic_similarity import (
    compare_titles,
    normalize_title,
    title_tokens,
)


def test_identical_titles():
    match = compare_titles(
        "The Future of UX Research",
        "The Future of UX Research",
    )
    assert match.similarity == 1.0
    assert match.candidate


def test_punctuation_does_not_matter():
    assert normalize_title("AI Agents: A New Era!") == (
        "ai agents a new era"
    )


def test_different_topics():
    match = compare_titles(
        "How to Improve Website Accessibility",
        "Venture Capital Funding in Robotics",
    )
    assert not match.candidate


def test_stopwords_removed():
    assert title_tokens("The Future of Design") == {
        "future", "design"
    }


def test_invalid_threshold():
    with pytest.raises(ValueError):
        compare_titles("UX", "UX", threshold=1.5)


def test_empty_title():
    match = compare_titles("", "UX Research")
    assert not match.candidate
    assert match.similarity == 0.0
