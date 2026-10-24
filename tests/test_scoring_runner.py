import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "scripts" / "run_ux_scoring.py"

spec = importlib.util.spec_from_file_location(
    "run_ux_scoring", RUNNER_PATH
)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def test_qualifies_at_30():
    entry = {
        "status": "scored",
        "score": 30.0,
        "qualified": False,
        "priority": False,
    }

    result = runner.qualification(entry)

    assert result["qualified"] is True
    assert result["priority"] is False


def test_cached_qualification_recalculated():
    entry = {
        "status": "scored",
        "score": 20.0,
        "qualified": True,
        "priority": True,
    }

    result = runner.qualification(entry)

    assert result["qualified"] is False
    assert result["priority"] is False


def test_priority_threshold():
    entry = {"status": "scored", "score": 85.0}

    result = runner.qualification(entry)

    assert result["qualified"] is True
    assert result["priority"] is True


def test_unscored_article_not_qualified():
    entry = {
        "status": "insufficient_context",
        "score": None,
        "qualified": True,
    }

    result = runner.qualification(entry)

    assert result["qualified"] is False
    assert result["priority"] is False
