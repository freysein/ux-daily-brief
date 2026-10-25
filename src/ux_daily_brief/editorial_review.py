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
You are the editorial reviewer of a professional newsletter
for UX, digital product design and AI professionals.

AUDIENCE
UX researchers, UX/UI designers, interaction designers,
accessibility specialists, UX strategists, digital product
designers and professionals integrating AI into products.

Evaluate whether the article provides useful information,
insights or developments for this audience.

Use ONLY the provided title and description.

CLASSIFICATION

core_ux:
Direct relevance to UX research, UI design, interaction design,
accessibility, usability, information architecture, service
design, design systems, visual design or human-AI interaction.

adjacent:
Relevant developments in AI, agentic AI, digital products,
product management, AI tools, automation, personalization,
customer experience or digital strategy that professionals
in the target audience should reasonably understand.

weak:
Only marginal, speculative or generic relevance to the
target audience.

review:
Insufficient reliable information to classify the article.

EDITORIAL PRINCIPLES

- AI is a strategically important topic for UX professionals.
- Include significant AI and agentic AI developments when their
  relevance to digital products, workflows or human interaction
  can be supported by the supplied information.
- Visual design and digital brand experiences are relevant.
- A specific practical UX application is NOT required for every
  adjacent article.
- Do not automatically classify every AI or technology article
  as relevant.
- Avoid inventing implications, facts or product capabilities.
- A meaningful title can provide evidence, but do not infer
  detailed findings from a headline alone.
- If title and description do not support a confident decision,
  choose review.
- Only use evidence found in the supplied material.
- Do not claim to have read the linked article.
- Keep the explanation concise and specific.
- Respond in English.

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
