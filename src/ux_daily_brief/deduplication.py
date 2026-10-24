from __future__ import annotations

import re
import unicodedata

from ux_daily_brief.models import Article


def normalized_title(title: str) -> str:
    text = unicodedata.normalize("NFKC", title).casefold()
    text = re.sub(r"[^\w\s]", " ", text)
    return " ".join(text.split())


def deduplicate_articles(articles: list[Article]) -> list[Article]:
    unique: dict[tuple[str, str], Article] = {}

    for article in articles:
        key = (article.source, normalized_title(article.title))

        if not key[1]:
            continue

        existing = unique.get(key)

        if existing is None:
            unique[key] = article
            continue

        # Prefer RSS links over newsletter tracking links.
        if existing.origin != "rss" and article.origin == "rss":
            unique[key] = article

    return list(unique.values())
