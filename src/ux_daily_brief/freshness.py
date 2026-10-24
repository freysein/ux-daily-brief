from __future__ import annotations

from datetime import datetime, timedelta, timezone

from ux_daily_brief.models import Article


DEFAULT_MAX_AGE_HOURS = 72


def article_timestamp(article: Article) -> datetime | None:
    return article.published_at or article.received_at


def is_fresh(
    article: Article,
    now: datetime | None = None,
    max_age_hours: int = DEFAULT_MAX_AGE_HOURS,
) -> bool:
    if max_age_hours <= 0:
        raise ValueError("max_age_hours must be positive")

    if now is None:
        now = datetime.now(timezone.utc)

    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")

    timestamp = article_timestamp(article)

    if timestamp is None or timestamp.tzinfo is None:
        return False

    age = now - timestamp

    return timedelta(0) <= age <= timedelta(hours=max_age_hours)


def filter_fresh(
    articles: list[Article],
    now: datetime | None = None,
    max_age_hours: int = DEFAULT_MAX_AGE_HOURS,
) -> list[Article]:
    return [
        article
        for article in articles
        if is_fresh(article, now=now, max_age_hours=max_age_hours)
    ]
