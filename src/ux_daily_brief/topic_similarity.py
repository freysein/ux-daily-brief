from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher


STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "by", "for",
    "from", "in", "is", "of", "on", "or", "the",
    "to", "with", "why", "how", "what",
    "am", "an", "auf", "aus", "bei", "das", "den",
    "der", "die", "ein", "eine", "für", "im",
    "ist", "mit", "und", "von", "was", "wie",
    "zu", "zum",
}


@dataclass(frozen=True)
class TitleMatch:
    similarity: float
    candidate: bool


def normalize_title(title: str) -> str:
    text = unicodedata.normalize("NFKC", title).casefold()
    text = re.sub(r"[^\w\s]", " ", text)
    return " ".join(text.split())


def title_tokens(title: str) -> set[str]:
    return {
        token
        for token in normalize_title(title).split()
        if len(token) >= 3 and token not in STOPWORDS
    }


def compare_titles(
    first: str,
    second: str,
    threshold: float = 0.65,
) -> TitleMatch:
    if not 0 <= threshold <= 1:
        raise ValueError("threshold must be between 0 and 1")

    left = normalize_title(first)
    right = normalize_title(second)

    if not left or not right:
        return TitleMatch(0.0, False)

    left_tokens = title_tokens(first)
    right_tokens = title_tokens(second)

    union = left_tokens | right_tokens
    overlap = (
        len(left_tokens & right_tokens) / len(union)
        if union else 0.0
    )

    character_similarity = SequenceMatcher(
        None, left, right
    ).ratio()

    similarity = max(overlap, character_similarity)

    return TitleMatch(
        similarity=round(similarity, 4),
        candidate=similarity >= threshold,
    )
