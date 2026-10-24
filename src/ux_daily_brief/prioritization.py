from __future__ import annotations

import re

from ux_daily_brief.models import Article


HIGH_RELEVANCE = {
    "ux": 6,
    "user experience": 6,
    "usability": 6,
    "accessibility": 6,
    "user research": 6,
    "interaction design": 5,
    "information architecture": 5,
    "design system": 5,
    "interface": 4,
    "product design": 4,
    "conversion": 4,
    "customer journey": 4,
    "data visualisation": 4,
    "data visualization": 4,
    "nutzererfahrung": 6,
    "barrierefreiheit": 6,
    "nutzerforschung": 6,
    "informationsdesign": 4,
}

MEDIUM_RELEVANCE = {
    "ai agents": 3,
    "agentic": 3,
    "ai adoption": 3,
    "product-market fit": 3,
    "research": 2,
    "design": 2,
    "customer": 2,
    "interface": 2,
    "ki-agenten": 3,
    "gestaltung": 2,
}


def keyword_score(article: Article) -> int:
    text = f"{article.title} {article.excerpt}".casefold()

    score = 0

    for keyword, weight in HIGH_RELEVANCE.items():
        if re.search(r"(?<!\w)" + re.escape(keyword) + r"(?!\w)", text):
            score += weight

    for keyword, weight in MEDIUM_RELEVANCE.items():
        if re.search(r"(?<!\w)" + re.escape(keyword) + r"(?!\w)", text):
            score += weight

    return score


def prioritize_articles(articles: list[Article]) -> list[Article]:
    return sorted(
        articles,
        key=lambda article: (
            -keyword_score(article),
            article.source,
            article.title.casefold(),
        ),
    )
