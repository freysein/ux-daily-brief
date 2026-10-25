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
            # An embedded display ad is not article sponsorship.
            # Preserve explicit sponsorship labels elsewhere.
            if text == "anzeige":
                ad_classes = {
                    "c-ad-label",
                    "c-ad-placeholder",
                    "c-ad-container",
                    "c-ad",
                }
                inside_display_ad = any(
                    ad_classes.intersection(
                        ancestor.get("class", [])
                    )
                    for ancestor in [element, *element.parents]
                    if getattr(ancestor, "name", None)
                )
                if inside_display_ad:
                    continue

            return True

    return False
