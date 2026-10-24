from __future__ import annotations

from dataclasses import dataclass


WEIGHTS = {
    "ux_relevance": 0.35,
    "practical_usefulness": 0.25,
    "novelty": 0.20,
    "credibility": 0.10,
    "business_impact": 0.10,
}

QUALIFICATION_THRESHOLD = 30
PRIORITY_THRESHOLD = 85


@dataclass(frozen=True)
class ScoreResult:
    total: float
    qualified: bool
    priority: bool
    components: dict[str, float]


def calculate_score(components: dict[str, float]) -> ScoreResult:
    if set(components) != set(WEIGHTS):
        raise ValueError("Score components must match scoring weights")

    normalized = {}

    for name, value in components.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"Invalid score for {name}")

        if not 0 <= value <= 100:
            raise ValueError(f"Score out of range: {name}")

        normalized[name] = float(value)

    total = sum(
        normalized[name] * WEIGHTS[name]
        for name in WEIGHTS
    )

    total = round(total, 2)

    return ScoreResult(
        total=total,
        qualified=total >= QUALIFICATION_THRESHOLD,
        priority=total >= PRIORITY_THRESHOLD,
        components=normalized,
    )
