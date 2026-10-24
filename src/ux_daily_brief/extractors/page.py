from __future__ import annotations

import re
from bs4 import BeautifulSoup

from ux_daily_brief.text_cleaning import clean_text


AD_MARKERS = re.compile(
    r"^\s*(ANZEIGE|WERBUNG|SPONSORED)\b",
    re.IGNORECASE
)


def extract_articles(html: str) -> list[dict]:
    """Extract editorial candidates from a received PAGE newsletter."""

    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    articles = []
    seen = set()

    for link in soup.find_all("a", href=True):
        if link.get_text(" ", strip=True).lower() != "mehr erfahren":
            continue

        tables = link.find_parents("table")

        if len(tables) < 2:
            continue

        # Smallest table contains the button only.
        # Second table contains the article content.
        article_table = tables[1]

        # Check the next surrounding table for advertising labels.
        outer_table = tables[2] if len(tables) > 2 else article_table

        outer_text = clean_text(
            outer_table.get_text(" ", strip=True)
        )

        if AD_MARKERS.search(outer_text):
            continue

        block = BeautifulSoup(str(article_table), "html.parser")

        for button in block.find_all("a"):
            if button.get_text(" ", strip=True).lower() == "mehr erfahren":
                button.decompose()

        # PAGE uses spans for article titles and descriptions.
        spans = [
            clean_text(span.get_text(" ", strip=True))
            for span in block.find_all("span")
            if not span.find("span")
        ]
        spans = [text for text in spans if text]

        if len(spans) >= 2:
            title = spans[0]
            excerpt = " ".join(spans[1:])
        else:
            # Fallback for other valid newsletter layouts.
            paragraphs = [
                clean_text(tag.get_text(" ", strip=True))
                for tag in block.find_all(["p", "h1", "h2", "h3"])
            ]
            paragraphs = [text for text in paragraphs if text]

            if len(paragraphs) < 2:
                continue

            title = paragraphs[0]
            excerpt = " ".join(paragraphs[1:])

        title = clean_text(title)
        excerpt = clean_text(excerpt)

        if not 15 <= len(title) <= 250:
            continue

        if len(excerpt) < 30:
            continue

        url = link["href"].strip()

        if not url.startswith(("https://", "http://")):
            continue

        key = (title.casefold(), url)

        if key in seen:
            continue

        seen.add(key)

        articles.append({
            "source": "page",
            "title": title,
            "excerpt": excerpt,
            "url": url,
            "origin": "newsletter",
            "review_status": "candidate",
        })

    return articles
