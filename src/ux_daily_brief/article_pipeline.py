from __future__ import annotations

import json
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

from ux_daily_brief.models import Article
from ux_daily_brief.extractors.nngroup import extract_articles as extract_nngroup
from ux_daily_brief.extractors.wired import extract_articles as extract_wired
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
    "nngroup": extract_nngroup,
    "wired": extract_wired,
    "jakob_nielsen": extract_jakob_nielsen,
}



# Conservative editorial review gate for newsletter-only topics.
AMBIGUOUS_JAKOB_TITLES = frozenset({
    "forecasting",
    "notifications",
})


def needs_editorial_review(
    source: str, title: str, excerpt: str
) -> bool:
    title = title.strip()
    excerpt = excerpt.strip()

    if source == "wired":
        # Conservative guard: flag clearly dangling headlines.
        dangling = {
            "a", "an", "and", "at", "by", "for", "from",
            "in", "into", "of", "on", "or", "than",
            "the", "to", "with", "own", "its",
        }

        words = title.casefold().split()
        if not title or not excerpt:
            return True
        if len(title) >= 60 and words and words[-1] in dangling:
            return True

        # Confirmed incomplete headings from newsletter extraction.
        incomplete_prefixes = (
            "An AI Agent Joined a Listserv of Top Internet Researchers. "
            "The Reply-All Chaos",
            "A Design Flaw in Share Links Exposes Users’ Personal "
            "Conversations With Meta’s",
            "This startup is all in on recursive self-improvement. "
            "Its latest",
        )

        if any(title.casefold() == value.casefold()
               for value in incomplete_prefixes):
            return True

        return False

    if source != "jakob_nielsen":
        return False

    if not title or not excerpt:
        return True

    if title.casefold() in AMBIGUOUS_JAKOB_TITLES:
        return True

    return False


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
    elif source in {"nngroup", "wired"}:
        candidates = extractor(str(message.get("body_text") or ""))
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
            review_status=(
                "review"
                if needs_editorial_review(
                    item["source"], item["title"], item["excerpt"]
                )
                else "candidate"
            ),
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
