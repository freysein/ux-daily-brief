from __future__ import annotations

import re

URL_RE = re.compile(
    r"https://jakobnielsenphd\.substack\.com/p/[a-zA-Z0-9-]+"
)

ROUNDUP_RE = re.compile(
    r"^UX Roundup:\s*",
    re.IGNORECASE,
)


def extract_articles(text: str, subject: str) -> list[dict]:
    """Extract verified subject topics with the original article URL."""

    if not isinstance(text, str) or not isinstance(subject, str):
        return []

    subject = subject.strip()
    if not subject:
        return []

    match = URL_RE.search(text)
    if not match:
        return []

    url = match.group(0)

    if not ROUNDUP_RE.match(subject):
        return [{
            "source": "jakob_nielsen",
            "title": subject,
            "url": url,
            "excerpt": subject,
        }]

    # Only split newsletters explicitly identified as UX Roundups.
    # Avoid inventing titles from incomplete subject fragments.
    raw_topics = ROUNDUP_RE.sub("", subject, count=1).split("|")
    topics = []
    seen = set()

    for raw in raw_topics:
        title = raw.strip()

        if not title or title.endswith(("…", "...")):
            continue

        key = title.casefold()
        if key in seen:
            continue

        seen.add(key)
        topics.append(title)

    # Do not turn an unclear or incomplete subject into articles.
    if len(topics) < 2:
        return []

    return [
        {
            "source": "jakob_nielsen",
            "title": topic,
            "url": url,
            "excerpt": topic,
        }
        for topic in topics
    ]
