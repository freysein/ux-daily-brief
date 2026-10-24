import pytest

from ux_daily_brief.scoring import (
    WEIGHTS,
    calculate_score,
)


def test_weights_sum_to_one():
    assert sum(WEIGHTS.values()) == pytest.approx(1.0)


def test_perfect_score():
    result = calculate_score({name: 100 for name in WEIGHTS})

    assert result.total == 100
    assert result.qualified
    assert result.priority


def test_zero_score():
    result = calculate_score({name: 0 for name in WEIGHTS})

    assert result.total == 0
    assert not result.qualified


def test_weighted_score():
    result = calculate_score({
        "ux_relevance": 90,
        "practical_usefulness": 80,
        "novelty": 75,
        "credibility": 85,
        "business_impact": 70,
    })

    assert result.total == 82.0
    assert result.qualified
    assert not result.priority


def test_invalid_components():
    with pytest.raises(ValueError):
        calculate_score({"ux_relevance": 90})


def test_invalid_range():
    with pytest.raises(ValueError):
        calculate_score({name: 120 for name in WEIGHTS})


def test_qualification_threshold_30():
    from ux_daily_brief.scoring import (
        QUALIFICATION_THRESHOLD,
        PRIORITY_THRESHOLD,
    )

    assert QUALIFICATION_THRESHOLD == 30
    assert PRIORITY_THRESHOLD == 85

    scores_30 = {
        name: 30 for name in WEIGHTS
    }
    scores_29 = {
        name: 29 for name in WEIGHTS
    }

    assert calculate_score(scores_30).qualified is True
    assert calculate_score(scores_29).qualified is False
