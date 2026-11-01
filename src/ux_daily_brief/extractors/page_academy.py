from __future__ import annotations

import re
from bs4 import BeautifulSoup

from ux_daily_brief.text_cleaning import clean_text

BUTTON = re.compile(r"(?:mehr erfahren|jetzt (?:noch )?anmelden)", re.I)
SKIP = re.compile(r"\b(?:anzeige|sponsored|werbung)\b", re.I)


def extract_articles(html: str) -> list[dict]:
    """PAGE Academy emails: collect course blocks, not site navigation."""
    if not html:
        return []
    soup = BeautifulSoup(html, "html.parser")
    results = []
    seen = set()
    for anchor in soup.find_all("a", href=True):
        label = clean_text(anchor.get_text(" ", strip=True))
        if not BUTTON.search(label):
            continue
        url = anchor["href"].strip()
        if not url.startswith(("https://", "http://")):
            continue
        # The nearest table cell is generally the course card; fallback to
        # surrounding div for layouts without tables.
        block = anchor.find_parent("td") or anchor.find_parent("div")
        if block is None:
            continue
        text = clean_text(block.get_text(" ", strip=True))
        if len(text) < 65 or SKIP.search(text[:50]):
            continue
        # Title is often in a preceding sibling/adjacent cell. Look up to
        # two table levels without swallowing the entire newsletter.
        parent = block
        for _ in range(2):
            if len(text) >= 140:
                break
            outer = parent.find_parent("td")
            if outer is None:
                break
            candidate_text = clean_text(outer.get_text(" ", strip=True))
            if len(candidate_text) > 1800:
                break
            text = candidate_text
            parent = outer

        text = BUTTON.sub("", text).strip(" →:–-")
        if len(text) < 65:
            continue
        # Prefer a prominent header when the card contains one.
        heading = block.find(["h1", "h2", "h3", "h4", "strong", "b"])
        title = clean_text(heading.get_text(" ", strip=True)) if heading else ""
        if len(title) < 12 or BUTTON.search(title):
            title = text[:110].rsplit(" ", 1)[0]
        if len(title) < 12:
            continue
        key = url
        if key in seen:
            continue
        seen.add(key)
        results.append({
            "source": "page",
            "title": title,
            "url": url,
            "excerpt": text[:700],
            "origin": "newsletter",
            "review_status": "review",
        })
    return results
