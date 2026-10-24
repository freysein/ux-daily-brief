from __future__ import annotations

import json
from pathlib import Path

from ux_daily_brief.models import Article
from ux_daily_brief.extractors.techcrunch import (
    extract_articles as extract_techcrunch,
)
from ux_daily_brief.extractors.page import (
    extract_articles as extract_page,
)


EXTRACTORS = {
    "techcrunch": extract_techcrunch,
    "page": extract_page,
}


def extract_from_newsletter(message: dict) -> list[Article]:
    source = str(message.get("source") or "").strip()

    # Unknown or unsupported sources are not analyzed.
    extractor = EXTRACTORS.get(source)
    if extractor is None:
        return []

    html = message.get("body_html") or ""
    candidates = extractor(html)

    return [
        Article(
            source=item["source"],
            title=item["title"],
            url=item["url"],
            excerpt=item["excerpt"],
            origin="newsletter",
        )
        for item in candidates
    ]


def extract_from_inbox(inbox: Path) -> list[Article]:
    articles = []

    for path in sorted(inbox.glob("*.json")):
        message = json.loads(path.read_text(encoding="utf-8"))
        articles.extend(extract_from_newsletter(message))

    # Deduplicate identical article IDs within this batch.
    unique = {}
    for article in articles:
        unique.setdefault(article.article_id, article)

    return list(unique.values())
