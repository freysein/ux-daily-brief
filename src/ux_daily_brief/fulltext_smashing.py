from __future__ import annotations

from urllib.parse import urlsplit

import requests
from bs4 import BeautifulSoup


MAX_CONTEXT_CHARS = 16000


class FulltextExtractionError(Exception):
    pass


def extract_smashing_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    content = soup.select_one(".article__content")

    if content is None:
        raise FulltextExtractionError(
            "Smashing article content container not found"
        )

    for element in content.select(
        "script, style, nav, aside, form, "
        "footer, iframe, figure, figcaption, "
        ".advertisement, .ad, .newsletter, "
        ".related-articles"
    ):
        element.decompose()

    blocks = []

    for element in content.select("h2, h3, h4, p, li"):
        if element.find_parent(["p", "li"]):
            continue

        text = element.get_text(" ", strip=True)
        text = " ".join(text.split())

        if len(text) >= 20:
            blocks.append(text)

    intro_markers = (
        "So what icon is the most reliable",
        "The findings aren’t very surprising",
    )

    start = next(
        (
            index
            for index, block in enumerate(blocks)
            if any(marker in block for marker in intro_markers)
        ),
        None,
    )

    if start is not None:
        blocks = blocks[start:]

    text = "\n\n".join(blocks)

    if len(text.split()) < 100:
        raise FulltextExtractionError(
            "Insufficient extracted article content"
        )

    return text[:MAX_CONTEXT_CHARS]


def fetch_smashing_text(url: str) -> str:
    parsed = urlsplit(url)

    if (
        parsed.scheme != "https"
        or (parsed.hostname or "").lower()
        not in {"smashingmagazine.com", "www.smashingmagazine.com"}
        or not parsed.path.startswith("/")
    ):
        raise FulltextExtractionError(
            "URL is not an approved Smashing Magazine URL"
        )

    try:
        response = requests.get(
            url,
            timeout=30,
            headers={
                "User-Agent": "UXDailyBrief/1.0"
            },
            allow_redirects=False,
        )

        if 300 <= response.status_code < 400:
            from urllib.parse import urljoin

            location = response.headers.get("Location")

            if not isinstance(location, str) or not location.strip():
                raise FulltextExtractionError(
                    "Redirect missing Location header"
                )

            redirected_url = urljoin(url, location)
            redirected = urlsplit(redirected_url)

            if (
                redirected.scheme != "https"
                or (redirected.hostname or "").lower()
                not in {
                    "smashingmagazine.com",
                    "www.smashingmagazine.com",
                }
                or redirected.username is not None
                or redirected.password is not None
                or redirected.port not in (None, 443)
            ):
                raise FulltextExtractionError(
                    "Unapproved redirect destination"
                )

            response = requests.get(
                redirected_url,
                timeout=30,
                headers={
                    "User-Agent": "UXDailyBrief/1.0"
                },
                allow_redirects=False,
            )

            if 300 <= response.status_code < 400:
                raise FulltextExtractionError(
                    "Additional redirects are not followed"
                )

        response.raise_for_status()

    except requests.RequestException as exc:
        raise FulltextExtractionError(
            f"Article fetch failed: {type(exc).__name__}"
        ) from exc

    return extract_smashing_text(response.text)
