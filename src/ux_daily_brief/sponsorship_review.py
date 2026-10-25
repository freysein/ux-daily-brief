from __future__ import annotations

from urllib.parse import urlsplit

import requests
from bs4 import BeautifulSoup

from ux_daily_brief.models import Article
from ux_daily_brief.sponsored_content import detect_sponsored_content


def check_article_sponsorship(article: Article) -> str:
    # Initial scope: t3n RSS articles only.
    # Other sources retain their existing selection behavior.
    if article.source != "t3n_ai":
        return "not_sponsored"

    parsed = urlsplit(article.url)

    if (
        parsed.scheme != "https"
        or parsed.hostname not in {"t3n.de", "www.t3n.de"}
        or parsed.username is not None
        or parsed.password is not None
        or parsed.port not in (None, 443)
    ):
        return "review"

    # t3n uses a trailing slash as its canonical article URL.
    url = parsed._replace(
        path=parsed.path.rstrip("/") + "/",
        fragment="",
    ).geturl()

    try:
        response = requests.get(
            url,
            timeout=20,
            allow_redirects=False,
            headers={"User-Agent": "UXDailyBrief/1.0"},
        )
        if response.status_code != 200:
            return "review"

        soup = BeautifulSoup(response.text, "html.parser")
        if soup.select_one("article") is None:
            return "review"

        if detect_sponsored_content(response.text):
            return "sponsored"

        return "not_sponsored"

    except (requests.RequestException, ValueError):
        return "review"
