from __future__ import annotations

import json
import os
from dataclasses import dataclass

import requests

from ux_daily_brief.models import Article
from ux_daily_brief.scoring import ScoreResult, calculate_score


OLLAMA_URL = os.getenv(
    "UX_OLLAMA_URL",
    "http://localhost:11434/api/generate",
)
OLLAMA_MODEL = os.getenv("UX_OLLAMA_MODEL", "qwen3:8b")

CRITERIA = (
    "ux_relevance",
    "practical_usefulness",
    "novelty",
    "credibility",
    "business_impact",
)

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        **{
            name: {"type": "integer", "minimum": 0, "maximum": 100}
            for name in CRITERIA
        },
        "reason": {"type": "string"},
        "ux_impact": {"type": "string"},
        "insufficient_context": {"type": "boolean"},
    },
    "required": [
        *CRITERIA,
        "reason",
        "ux_impact",
        "insufficient_context",
    ],
}


@dataclass
class Assessment:
    score: ScoreResult | None
    reason: str
    ux_impact: str
    insufficient_context: bool


def assess_article(article: Article) -> Assessment:
    prompt = f"""
You are a senior UX research and digital experience editor.

Evaluate this article candidate for an internal daily UX newsletter
read by experienced UX, CX and digital product professionals.

Use ONLY the supplied newsletter title and excerpt.
Do not browse, invent facts, or assume the linked article's contents.

Score each dimension with an INTEGER from 0 to 100:

ux_relevance (35%):
Direct relevance to UX research, user behavior, interaction
design, accessibility or digital experiences.

practical_usefulness (25%):
Actionable insights for UX practitioners and product teams.

novelty (20%):
New perspectives, developments or techniques.
If freshness cannot be established, be conservative.

credibility (10%):
Strength of evidence and clarity in the supplied excerpt.
Do not assume the linked article contains further proof.

business_impact (10%):
Potential influence on product strategy, customers,
conversion, efficiency or business outcomes.

Also provide:
- reason: 1-2 concise English sentences explaining the scores.
- ux_impact: one concise English sentence following the rules below.
- insufficient_context: a boolean following the decision rule below.

## insufficient_context: decision rule

Read the title and excerpt. Answer two questions:
Q1: Can you say in one sentence what the article is about?
Q2: Can you decide whether this topic is UX-related or not?
    (Q2 asks if you CAN decide. "Not UX-related" is a valid answer.)

- Q1 = YES and Q2 = YES → insufficient_context = false
- Q1 = NO or Q2 = NO → insufficient_context = true

A short excerpt is enough if you can answer Q1 and Q2 with YES.
You do not need the full linked article.

Three cases:
- Topic clear, not about UX → insufficient_context = false, give low relevance.
- Topic clear, about UX, few details → insufficient_context = false,
  lower practical_usefulness, novelty and credibility.
- Topic unclear → insufficient_context = true.

## Mandatory decision check
Before producing JSON, apply Q1 and Q2 independently.

If you can describe the topic AND judge its UX relevance,
insufficient_context MUST be false.

IMPORTANT: Low practical usefulness, missing research data,
lack of actionable advice, or low UX relevance NEVER imply
insufficient_context=true when the topic is identifiable.

If you assign numeric scores and can explain what the article
is about and whether it relates to UX, set insufficient_context=false.

For the ux_impact field:
- If insufficient_context=false, use Demonstrated: or
  Potential implication:.
- If insufficient_context=true, use Missing information:.

## Evidence rules
- Base every score and every statement only on the title and excerpt.
- Mention methods, findings, numbers or recommendations only if they
  appear in the excerpt.
- When details are missing, lower the score. Leave the gap open.

## ux_impact: start with exactly one label
- "Demonstrated: " → the excerpt reports a result (study, test, data,
  measured effect). Restate only that result.
- "Potential implication: " → your own conclusion about what the topic
  could mean for UX.
- "Missing information: " → use only when insufficient_context = true.
  List what is missing (e.g. topic, method, result). Give no UX advice.
If unsure between "Demonstrated" and "Potential implication",
use "Potential implication: ".

## Examples
The examples show the decision only. Use the score scale and
JSON format defined in this prompt.

Example 1: clear, not UX-relevant
Title: "Q3 earnings: Retailer X beats forecasts"
Excerpt: "Retailer X reported 12% revenue growth, driven by new stores in Asia."
→ insufficient_context: false
→ relevance: very low
→ ux_impact: "Potential implication: No direct UX impact; the article covers financial results only."

Example 2: UX-relevant but thin
Title: "Why checkout forms still fail"
Excerpt: "A new article looks at common checkout form mistakes and how to fix them."
→ insufficient_context: false
→ relevance: high; practical_usefulness, novelty, credibility: low
→ ux_impact: "Potential implication: Checkout form design may affect completion rates; the excerpt names no specific mistakes or data."

Example 3: unclear
Title: "This week's picks"
Excerpt: "Three links we loved. Don't miss the second one!"
→ insufficient_context: true
→ ux_impact: "Missing information: article topic, subject area, any content beyond the teaser."

## Output
Return only the JSON object defined in this prompt.
No text before or after it. No markdown code fences.

SOURCE: {article.source}
TITLE: {article.title}
NEWSLETTER EXCERPT: {article.excerpt[:3500]}
""".strip()

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "think": False,
        "format": RESPONSE_SCHEMA,
        "options": {
            "temperature": 0.1,
            "num_predict": 500,
        },
    }

    def request_assessment(request_payload):
        response = requests.post(
            OLLAMA_URL,
            json=request_payload,
            timeout=(10, 180),
        )
        response.raise_for_status()

        raw = response.json()
        if raw.get("error"):
            raise ValueError(f"Ollama error: {raw['error']}")

        return json.loads(raw["response"])

    data = request_assessment(payload)

    def has_label_conflict(result):
        impact = str(result.get("ux_impact") or "").strip()
        insufficient = result.get("insufficient_context")

        if type(insufficient) is not bool:
            return False

        if insufficient:
            return not impact.startswith("Missing information: ")

        return impact.startswith("Missing information: ")

    if has_label_conflict(data):
        repair_payload = dict(payload)
        repair_payload["prompt"] = (
            prompt
            + "\\n\\nYour previous response was inconsistent with "
            "the insufficient_context and ux_impact rules. "
            "Re-evaluate Q1 and Q2 independently. "
            "A clearly identifiable non-UX topic is sufficient context. "
            "Return a complete, corrected JSON assessment. "
            "If insufficient_context is true, ux_impact MUST start "
            "with 'Missing information: '. Otherwise it MUST start "
            "with 'Demonstrated: ' or 'Potential implication: '. "
            "Use only the supplied title and excerpt. "
            "Previous response: "
            + json.dumps(data, ensure_ascii=False)
        )
        data = request_assessment(repair_payload)

    if set(data) != set(RESPONSE_SCHEMA["required"]):
        raise ValueError("Unexpected Ollama response fields")

    if type(data["insufficient_context"]) is not bool:
        raise ValueError("Invalid insufficient_context value")

    for field in ("reason", "ux_impact"):
        if not isinstance(data[field], str) or not data[field].strip():
            raise ValueError(f"Missing or invalid {field}")

    scores = {name: data[name] for name in CRITERIA}

    for name, value in scores.items():
        if type(value) is not int:
            raise ValueError(f"Invalid integer score: {name}")

    impact = data["ux_impact"].strip()

    valid_prefixes = (
        "Demonstrated: ",
        "Potential implication: ",
        "Missing information: ",
    )

    if not impact.startswith(valid_prefixes):
        raise ValueError("Invalid UX impact prefix")

    if data["insufficient_context"]:
        if not impact.startswith("Missing information: "):
            raise ValueError(
                "Insufficient context requires Missing information. "
                "Model response: "
                + json.dumps(data, ensure_ascii=False)
            )
    elif impact.startswith("Missing information: "):
        raise ValueError(
            "Missing information requires insufficient context"
        )

    score = calculate_score(scores)

    return Assessment(
        score=None if data["insufficient_context"] else score,
        reason=data["reason"].strip(),
        ux_impact=data["ux_impact"].strip(),
        insufficient_context=data["insufficient_context"],
    )
