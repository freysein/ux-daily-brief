from __future__ import annotations

from bs4 import BeautifulSoup


SPONSORED_MARKERS = {
    "sponsored post",
    "sponsored content",
    "anzeige",
    "advertorial",
    "werbung",
}


def detect_sponsored_content(html: str) -> bool:
    """Detect explicit sponsorship labels inside an article."""

    if not html:
        return False

    soup = BeautifulSoup(html, "html.parser")
    article = soup.select_one("article")

    if article is None:
        return False

    for element in article.find_all(
        ["span", "div", "p", "label"]
    ):
        if element.find(["span", "div", "p", "label"]):
            continue

        text = " ".join(
            element.get_text(" ", strip=True).casefold().split()
        )

        if text in SPONSORED_MARKERS:
            return True

    return False
