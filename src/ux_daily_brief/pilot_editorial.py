"""Exploratory editorial scoring for the three-week UX Daily Brief pilot.

Scoring ranks candidates but does not impose a minimum relevance threshold.
Source rights, duplicate checks and publication policy remain separate gates.
"""
from __future__ import annotations

from dataclasses import dataclass

CATEGORIES = (
    "UX Research & Human Behavior",
    "AI & Emerging Experiences",
    "Design, Branding & Creativity",
    "Digital Products & Technology",
    "Strategy, Business & Society",
    "Learn & Grow",
)
WEIGHTS = {
    "relevance": 0.30,
    "novelty": 0.25,
    "practical_value": 0.20,
    "source_quality": 0.15,
    "diversity": 0.10,
}


@dataclass(frozen=True)
class PilotAssessment:
    category: str
    relevance: float
    novelty: float
    practical_value: float
    source_quality: float
    diversity: float

    def score(self) -> float:
        if self.category not in CATEGORIES:
            raise ValueError(f"Unknown editorial category: {self.category}")
        values = {
            "relevance": self.relevance,
            "novelty": self.novelty,
            "practical_value": self.practical_value,
            "source_quality": self.source_quality,
            "diversity": self.diversity,
        }
        if any(not 0 <= value <= 5 for value in values.values()):
            raise ValueError("Pilot score components must be between 0 and 5")
        return round(sum(values[key] * WEIGHTS[key] for key in WEIGHTS) * 20, 2)


def select_pilot(
    assessments: list[tuple[str, PilotAssessment]],
    *,
    target: int = 12,
) -> list[tuple[str, float]]:
    """Rank all qualified candidates. No hard score cut-off in pilot mode.

    Caller must apply rights, ad, broken-link, stale-event and duplicate
    policies independently before invoking this function.
    """
    if target < 0:
        raise ValueError("target must be non-negative")
    scored = [(article_id, assessment.score()) for article_id, assessment in assessments]
    scored.sort(key=lambda pair: (-pair[1], pair[0]))
    return scored[:target]
