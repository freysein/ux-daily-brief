import pytest
from ux_daily_brief.pilot_editorial import (
    CATEGORIES, WEIGHTS, PilotAssessment, select_pilot,
)


def test_weights_total_one():
    assert sum(WEIGHTS.values()) == pytest.approx(1.0)
    assert len(CATEGORIES) == 6


def test_pilot_scoring_range():
    high = PilotAssessment(CATEGORIES[0], 5, 5, 5, 5, 5)
    low = PilotAssessment(CATEGORIES[5], 0, 0, 0, 0, 0)
    assert high.score() == 100
    assert low.score() == 0


def test_no_minimum_cutoff():
    low = PilotAssessment(CATEGORIES[5], 1, 0, 0, 2, 0)
    assert len(select_pilot([("training-1", low)])) == 1


def test_pilot_order_stable():
    high = PilotAssessment(CATEGORIES[0], 5, 5, 5, 5, 5)
    low = PilotAssessment(CATEGORIES[5], 1, 1, 1, 1, 1)
    assert select_pilot([("b", low), ("a", high)])[0][0] == "a"


def test_invalid_scores_rejected():
    bad = PilotAssessment(CATEGORIES[0], 6, 0, 0, 0, 0)
    with pytest.raises(ValueError):
        bad.score()
