from __future__ import annotations

import json
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

from ux_daily_brief.models import Article
from ux_daily_brief.extractors.jakob_nielsen import (
    extract_articles as extract_jakob_nielsen,
)
from ux_daily_brief.source_identifier import identify_source
from ux_daily_brief.extractors.techcrunch import (
    extract_articles as extract_techcrunch,
)
from ux_daily_brief.extractors.page import (
    extract_articles as extract_page,
)


def parse_received_at(value: str | None) -> datetime | None:
    if not value:
        return None

    try:
        result = parsedate_to_datetime(value)
    except (ValueError, TypeError, IndexError):
        try:
            result = datetime.fromisoformat(value)
        except (ValueError, TypeError):
            return None

    if result.tzinfo is None:
        return None

    return result.astimezone(timezone.utc)


EXTRACTORS = {
    "techcrunch": extract_techcrunch,
    "page": extract_page,
    "jakob_nielsen": extract_jakob_nielsen,
}


def extract_from_newsletter(message: dict) -> list[Article]:
    source = str(message.get("source") or "").strip()

    # Identify generic inbox messages by their confirmed sender.
    if source in {"", "ux_inbox"}:
        identification = identify_source(
            str(message.get("from") or "")
        )
        source = identification["source"]

    # Unknown or unsupported sources are not analyzed.
    extractor = EXTRACTORS.get(source)
    if extractor is None:
        return []

    if source == "jakob_nielsen":
        candidates = extractor(
            str(message.get("body_text") or ""),
            str(message.get("subject") or ""),
        )
    else:
        html = message.get("body_html") or ""
        candidates = extractor(html)
    received_at = parse_received_at(message.get("received_at"))

    return [
        Article(
            source=item["source"],
            title=item["title"],
            url=item["url"],
            excerpt=item["excerpt"],
            origin="newsletter",
            received_at=received_at,
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
