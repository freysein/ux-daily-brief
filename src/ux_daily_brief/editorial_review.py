from __future__ import annotations

import json
import requests

from ux_daily_brief.models import Article


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen3:8b"

SCHEMA = {
    "type": "object",
    "properties": {
        "classification": {
            "type": "string",
            "enum": ["core_ux", "adjacent", "weak", "review"],
        },
        "evidence": {"type": "string"},
        "reason": {"type": "string"},
    },
    "required": ["classification", "evidence", "reason"],
    "additionalProperties": False,
}


def review_article(article: Article) -> dict:
    prompt = f"""
You are the editorial quality reviewer for a professional
UX newsletter.

Judge whether the article is genuinely useful for UX
researchers, UX designers, interaction designers,
accessibility specialists or UX strategists.

Use ONLY the supplied title and description.

Classification:
core_ux: Direct, concrete connection to UX practice.
adjacent: Related discipline with a specific, evidenced
connection to UX work.
weak: Only speculative, generic or indirect UX relevance.
review: Insufficient information to decide safely.

Rules:
- Do not invent UX implications.
- AI, design, technology and business topics are NOT
  automatically UX-relevant.
- Generic statements such as "could influence UX"
  are insufficient evidence.
- Evidence must identify information actually present
  in the supplied article description.
- If that evidence is absent, use weak or review.
- Do not claim to have read the linked article.
- Answer in English.

TITLE:
{article.title}

DESCRIPTION:
{article.excerpt}

Return JSON matching the required schema.
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

    result = json.loads(response.json()["response"])

    if result.get("classification") not in {
        "core_ux", "adjacent", "weak", "review"
    }:
        raise ValueError("Invalid editorial classification")

    for field in ("evidence", "reason"):
        if not isinstance(result.get(field), str):
            raise ValueError(f"Invalid editorial {field}")

    return result


def editorial_eligible(result: dict) -> bool:
    return result.get("classification") in {
        "core_ux", "adjacent"
    }
