from __future__ import annotations

import requests


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen3:8b"

SCHEMA = {
    "type": "object",
    "properties": {
        "same_story": {"type": "boolean"},
        "confidence": {"type": "number"},
        "reason": {"type": "string"},
    },
    "required": ["same_story", "confidence", "reason"],
    "additionalProperties": False,
}


def compare_stories(
    first_title: str,
    first_excerpt: str,
    second_title: str,
    second_excerpt: str,
) -> dict:
    prompt = f"""
You are checking whether two news articles describe the SAME
specific real-world event, announcement, study, or development.

Articles may be written in different languages.

Do NOT label them duplicates merely because they discuss
the same broad subject, technology, company, or industry.

If evidence is insufficient, return same_story=false
and a low confidence.

ARTICLE A
Title: {first_title}
Description: {first_excerpt}

ARTICLE B
Title: {second_title}
Description: {second_excerpt}

Return JSON matching the required schema.
Confidence must be a number between 0 and 1.
Explain your decision briefly in English.
"""

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "think": False,
            "format": SCHEMA,
            "options": {"temperature": 0},
        },
        timeout=120,
    )
    response.raise_for_status()

    import json

    result = json.loads(response.json()["response"])

    if not isinstance(result.get("same_story"), bool):
        raise ValueError("Invalid same_story")

    confidence = result.get("confidence")

    if (
        isinstance(confidence, bool)
        or not isinstance(confidence, (int, float))
        or not 0 <= confidence <= 1
    ):
        raise ValueError("Invalid confidence")

    if not isinstance(result.get("reason"), str):
        raise ValueError("Invalid reason")

    return result


def is_confirmed_duplicate(result: dict) -> bool:
    return (
        result.get("same_story") is True
        and result.get("confidence", 0) >= 0.85
    )
