from __future__ import annotations

import calendar
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import feedparser
import requests
import yaml

from ux_daily_brief.models import Article
from ux_daily_brief.text_cleaning import clean_text

ROOT = Path(__file__).resolve().parents[3]
SOURCES_FILE = ROOT / "config/sources.yml"


def configured_feeds() -> dict[str, str]:
    config = yaml.safe_load(
        SOURCES_FILE.read_text(encoding="utf-8")
    )

    feeds = {}

    for source_id, source in config["sources"].items():
        if source.get("access") != "rss":
            continue

        url = source.get("feed_url", "")
        parsed = urlparse(url)

        if parsed.scheme != "https" or not parsed.netloc:
            raise ValueError(f"Invalid RSS URL for {source_id}")

        feeds[source_id] = url

    return feeds


def fetch_feed(source_id: str, url: str, limit: int = 20) -> list[Article]:
    if limit < 1:
        raise ValueError("limit must be positive")

    response = requests.get(
        url,
        timeout=(10, 30),
        headers={"User-Agent": "UXDailyBrief/0.1 RSS Reader"},
    )
    response.raise_for_status()

    feed = feedparser.parse(response.content)

    if feed.bozo and not feed.entries:
        raise ValueError(f"Invalid RSS feed: {source_id}")

    articles = []

    for entry in feed.entries[:limit]:
        title = clean_text(entry.get("title", ""))
        link = entry.get("link", "").strip()

        if not title or not link.startswith(("https://", "http://")):
            continue

        description = entry.get("summary", "")
        if description:
            from bs4 import BeautifulSoup
            description = BeautifulSoup(
                description, "html.parser"
            ).get_text(" ", strip=True)

        excerpt = clean_text(description)

        published_at = None
        parsed_date = (
            entry.get("published_parsed")
            or entry.get("updated_parsed")
        )

        if parsed_date:
            published_at = datetime.fromtimestamp(
                calendar.timegm(parsed_date),
                tz=timezone.utc,
            )

        articles.append(
            Article(
                source=source_id,
                title=title,
                url=link,
                excerpt=excerpt,
                origin="rss",
                published_at=published_at,
            )
        )

    return articles


def collect_rss(limit_per_feed: int = 20) -> tuple[list[Article], dict]:
    articles = []
    status = {}

    for source_id, url in configured_feeds().items():
        try:
            collected = fetch_feed(
                source_id, url, limit=limit_per_feed
            )
            articles.extend(collected)
            status[source_id] = {
                "status": "ok",
                "articles": len(collected),
            }
        except (requests.RequestException, ValueError) as error:
            status[source_id] = {
                "status": "error",
                "error": str(error),
            }

    return articles, status
