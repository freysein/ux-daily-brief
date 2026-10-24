from __future__ import annotations

import re
from bs4 import BeautifulSoup
from ux_daily_brief.text_cleaning import clean_text


def extract_articles(html: str) -> list[dict]:
    """Extract article candidates from a received TechCrunch newsletter."""

    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    articles = []
    seen = set()

    for link in soup.find_all("a", href=True):
        if link.get_text(" ", strip=True).lower() != "read more":
            continue

        url = link["href"].strip()

        if not url.startswith(("https://", "http://")):
            continue

        container = link.find_parent("div")

        if container is None:
            continue

        # Work on a copy: do not modify the original HTML tree.
        block = BeautifulSoup(str(container), "html.parser")

        for button in block.find_all("a"):
            if button.get_text(" ", strip=True).lower() == "read more":
                button.decompose()

        content = " ".join(block.stripped_strings)
        content = clean_text(content)

        # TechCrunch currently separates headlines and summaries by " : ".
        if " : " not in content:
            continue

        title, description = content.split(" : ", 1)
        title = title.strip(" :-")
        description = description.strip()

        if not (15 <= len(title) <= 250):
            continue

        if len(description) < 30:
            continue

        key = (title.casefold(), url)

        if key in seen:
            continue

        seen.add(key)

        articles.append({
            "source": "techcrunch",
            "title": title,
            "excerpt": description,
            "url": url,
            "origin": "newsletter",
            "review_status": "candidate",
        })

    return articles
