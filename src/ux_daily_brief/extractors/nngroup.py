from __future__ import annotations

import re
from urllib.parse import urlsplit

from ux_daily_brief.article_identity import normalize_url
from .newsletter_links import candidate

# Mailchimp HTML links are redirects. The plaintext newsletter carries
# original URLs in Markdown-style links.
MARKDOWN_LINK = re.compile(r"\\[([^\\]\\n]{5,220})\\]\\((https?://[^\\s)]+)\\)")
PLAIN_LINK = re.compile(r"^\\s*(?:\\*+\\s*)?(.{12,220}?)\\s*\\((https?://[^\\s)]+)\\)", re.M)
ALLOWED_NNG_PREFIXES = (
    "/articles/", "/videos/", "/podcasts/", "/contents/",
)
YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "youtu.be"}


def _clean(raw: str) -> str:
    return normalize_url(raw.replace("\\", "").rstrip(".,;"))


def extract_articles(text: str) -> list[dict]:
    results: dict[str, dict] = {}
    # Handle both "[Title](URL)" and the emails' "Title (URL)" text.
    matches = list(PLAIN_LINK.finditer(text or "")) + list(MARKDOWN_LINK.finditer(text or ""))
    for match in matches:
        title = re.sub(r"^\\*+\\s*", "", match.group(1).strip()).strip()
        url = _clean(match.group(2))
        parsed = urlsplit(url)
        host = (parsed.hostname or "").lower()

        if host == "www.nngroup.com":
            host = "nngroup.com"

        if host == "nngroup.com":
            if not parsed.path.startswith(ALLOWED_NNG_PREFIXES):
                continue
            if parsed.path.startswith("/contents/self-paced-courses/"):
                continue
        elif host in YOUTUBE_HOSTS:
            if not (parsed.path == "/watch" or parsed.path.startswith("/shorts/")
                    or host == "youtu.be"):
                continue
            if not ("podcast" in title.lower() or "design principles" in title.lower()):
                continue
        else:
            continue

        # Discard raw URLs, campaign metadata and short navigation labels.
        if title.startswith("http") or len(title) < 12:
            continue
        if title.lower().startswith(("related course", "explore ", "find your")):
            continue

        result = candidate("nngroup", title, url)
        results.setdefault(url, result)
    return list(results.values())
