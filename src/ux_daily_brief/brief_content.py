from __future__ import annotations

from dataclasses import dataclass
import re


CATEGORIES = (
    "UX & Research",
    "AI & Emerging Experiences",
    "Accessibility & Inclusive Design",
    "Design Practice & Technology",
    "Strategy & Business Impact",
)


@dataclass(frozen=True)
class BriefEntry:
    article_id: str
    title: str
    summary: str
    ux_impact: str
    category: str
    source: str
    url: str
    editorial_classification: str


def word_count(text: str) -> int:
    return len(re.findall(r"\b[\w]+(?:[-'][\w]+)*\b", text))


def validate_entry(entry: BriefEntry) -> list[str]:
    errors = []

    if not entry.article_id.strip():
        errors.append("missing_article_id")

    if not entry.title.strip():
        errors.append("missing_title")

    if not entry.source.strip():
        errors.append("missing_source")

    if not entry.url.startswith(("https://", "http://")):
        errors.append("invalid_url")

    if entry.category not in CATEGORIES:
        errors.append("invalid_category")

    if entry.editorial_classification not in {
        "core_ux", "adjacent", "weak"
    }:
        errors.append("invalid_editorial_classification")

    if not 70 <= word_count(entry.summary) <= 100:
        errors.append("invalid_summary_length")

    if not entry.ux_impact.strip():
        errors.append("missing_ux_impact")

    return errors
