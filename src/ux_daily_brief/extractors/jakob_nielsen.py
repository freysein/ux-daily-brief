from __future__ import annotations

import re

URL_RE = re.compile(
    r"https://jakobnielsenphd\.substack\.com/p/[a-zA-Z0-9-]+"
)


def extract_articles(text: str, subject: str) -> list[dict]:
    """Create a title-and-link candidate from a newsletter."""

    if not isinstance(text, str) or not isinstance(subject, str):
        return []

    title = subject.strip()
    if not title:
        return []

    match = URL_RE.search(text)
    if not match:
        return []

    url = match.group(0)

    return [{
        "source": "jakob_nielsen",
        "title": title,
        "url": url,
        "excerpt": title,
    }]
