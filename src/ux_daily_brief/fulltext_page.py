from __future__ import annotations

from urllib.parse import urlsplit

import requests
from bs4 import BeautifulSoup


MAX_CONTEXT_CHARS = 16000

STOP_HEADINGS = (
    "das könnte dich auch interessieren",
    "weitere artikel zu diesem thema",
)


class PageExtractionError(Exception):
    pass


def extract_page_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    article = soup.select_one("article")

    if article is None:
        raise PageExtractionError(
            "PAGE article container not found"
        )

    for element in article.select(
        "script, style, nav, aside, form, footer, "
        "iframe, figure, figcaption, "
        ".advertisement, .related-articles"
    ):
        element.decompose()

    blocks = []

    for element in article.find_all(
        ["h1", "h2", "h3", "h4", "p", "li"]
    ):
        if element.find_parent(["p", "li"]):
            continue

        text = " ".join(
            element.get_text(" ", strip=True).split()
        )

        if element.name in {"h1", "h2", "h3", "h4"}:
            if any(
                marker in text.casefold()
                for marker in STOP_HEADINGS
            ):
                break

        if text.casefold().strip(" :.!") in {
            "schreibe einen kommentar",
            "kommentar schreiben",
            "leave a comment",
        }:
            continue

        if len(text) >= 20:
            blocks.append(text)

    result = "\n\n".join(blocks)

    if len(result.split()) < 100:
        raise PageExtractionError(
            "Insufficient PAGE article content"
        )

    return result[:MAX_CONTEXT_CHARS]


def fetch_page_text(url: str) -> str:
    parsed = urlsplit(url)

    if (
        parsed.scheme != "https"
        or parsed.hostname not in {
            "page-online.de",
            "www.page-online.de",
        }
        or parsed.username is not None
        or parsed.password is not None
        or parsed.port not in (None, 443)
    ):
        raise PageExtractionError(
            "URL is not an approved PAGE URL"
        )

    try:
        response = requests.get(
            url,
            timeout=30,
            allow_redirects=False,
            headers={
                "User-Agent": "UXDailyBrief/1.0"
            },
        )

        if 300 <= response.status_code < 400:
            raise PageExtractionError(
                "PAGE redirect requires review"
            )

        response.raise_for_status()

    except requests.RequestException as exc:
        raise PageExtractionError(
            f"PAGE fetch failed: {type(exc).__name__}"
        ) from exc

    return extract_page_text(response.text)
