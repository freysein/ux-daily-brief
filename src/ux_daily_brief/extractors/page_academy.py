from __future__ import annotations

import re
from bs4 import BeautifulSoup, Tag
from ux_daily_brief.text_cleaning import clean_text

BUTTON = re.compile(r"(?:mehr erfahren|jetzt (?:noch )?anmelden)", re.I)
SKIP = re.compile(r"^\s*(?:anzeige|sponsored|werbung)\b", re.I)
DATE = re.compile(
    r"^(?:\d{1,2}[.]?\s*(?:&\s*\d{1,2}[.]?)?\s*(?:"
    r"januar|februar|märz|april|mai|juni|juli|august|september|"
    r"oktober|november|dezember|\d{1,2}\.)\b|"
    r"\d{1,2}[.]\s*\d{1,2}[.]\s*\d{4})", re.I
)
HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "strong", "b"}


def _title_near_button(anchor: Tag) -> str:
    """Choose only an explicit heading; never turn a date into a title."""
    # The PAGE Academy markup places titles before date/description/CTA.
    # Search backwards, stopping at the previous CTA to avoid using
    # a heading belonging to a different course.
    inspected = 0
    fallback = ""
    for previous in anchor.find_all_previous(True):
        inspected += 1
        if inspected > 180:
            break
        if previous.name == "a" and BUTTON.search(
            clean_text(previous.get_text(" ", strip=True))
        ):
            break
        if previous.name not in HEADING_TAGS:
            continue
        title = clean_text(previous.get_text(" ", strip=True))
        if (
            12 <= len(title) <= 130
            and not BUTTON.search(title)
            and not DATE.match(title)
            and not SKIP.search(title)
            and not title.startswith(("→", "»"))
        ):
            if previous.name in {"h1", "h2", "h3", "h4", "h5"}:
                return title
            if not fallback:
                fallback = title
    return fallback


def extract_articles(html: str) -> list[dict]:
    """Extract PAGE Academy course candidates for editorial review."""
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
        title = _title_near_button(anchor)
        # The hero course uses an inline quoted anchor rather than a heading.
        # Prefer that explicit title to a nearby promotional tagline.
        if "charakterideen" in title.casefold():
            for previous in anchor.find_all_previous("a", href=True, limit=15):
                label_text = clean_text(previous.get_text(" ", strip=True))
                if "Imaginary Friends" in label_text and "Character Lab" in label_text:
                    title = label_text.strip("»« ").strip()
                    break
        if not title:
            # Better zero questionable candidates than date-as-title errors.
            continue
        block = anchor.find_parent("td") or anchor.find_parent("div")
        if block is None:
            continue
        text = clean_text(block.get_text(" ", strip=True))
        if len(text) < 65 or SKIP.search(text[:50]):
            continue
        if url in seen:
            continue
        seen.add(url)
        results.append({
            "source": "page",
            "title": title,
            "url": url,
            "excerpt": text[:700],
            "origin": "newsletter",
            "review_status": "review",
        })
    return results
