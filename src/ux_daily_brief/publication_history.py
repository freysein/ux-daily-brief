from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import duckdb


DEFAULT_DB_PATH = Path("data/state/ux_publications.duckdb")


def initialize_db(db_path: Path = DEFAULT_DB_PATH) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with duckdb.connect(str(db_path)) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS published_articles (
                article_id VARCHAR NOT NULL,
                source VARCHAR NOT NULL,
                title VARCHAR NOT NULL,
                url VARCHAR,
                edition_date DATE NOT NULL,
                published_at TIMESTAMPTZ NOT NULL,
                PRIMARY KEY (article_id, edition_date)
            )
        """)


def record_publication(
    article_id: str,
    source: str,
    title: str,
    url: str,
    edition_date: str,
    db_path: Path = DEFAULT_DB_PATH,
    published_at: datetime | None = None,
) -> None:
    initialize_db(db_path)

    timestamp = published_at or datetime.now(timezone.utc)

    if timestamp.tzinfo is None:
        raise ValueError("published_at must be timezone-aware")

    with duckdb.connect(str(db_path)) as con:
        con.execute(
            """
            INSERT INTO published_articles
            (article_id, source, title, url, edition_date, published_at)
            VALUES (?, ?, ?, ?, CAST(? AS DATE), ?)
            ON CONFLICT (article_id, edition_date) DO NOTHING
            """,
            [
                article_id,
                source,
                title,
                url,
                edition_date,
                timestamp,
            ],
        )


def recently_published_ids(
    days: int = 7,
    db_path: Path = DEFAULT_DB_PATH,
    now: datetime | None = None,
) -> set[str]:
    if days <= 0:
        raise ValueError("days must be positive")

    initialize_db(db_path)

    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        raise ValueError("now must be timezone-aware")

    cutoff = current.timestamp() - days * 86400
    cutoff_datetime = datetime.fromtimestamp(cutoff, timezone.utc)

    with duckdb.connect(str(db_path), read_only=True) as con:
        rows = con.execute(
            """
            SELECT DISTINCT article_id
            FROM published_articles
            WHERE published_at >= ?
              AND published_at <= ?
            """,
            [cutoff_datetime, current],
        ).fetchall()

    return {row[0] for row in rows}


def recently_published_urls(
    days: int = 7,
    db_path: Path = DEFAULT_DB_PATH,
    now: datetime | None = None,
) -> set[str]:
    from ux_daily_brief.article_identity import normalize_url

    if days <= 0:
        raise ValueError("days must be positive")

    initialize_db(db_path)

    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        raise ValueError("now must be timezone-aware")

    from datetime import timedelta

    cutoff = current - timedelta(days=days)

    with duckdb.connect(str(db_path), read_only=True) as con:
        rows = con.execute(
            """
            SELECT url
            FROM published_articles
            WHERE published_at >= ?
              AND published_at <= ?
            """,
            [cutoff, current],
        ).fetchall()

    return {
        normalized
        for (url,) in rows
        if (normalized := normalize_url(url))
    }


def was_recently_published(
    article_id: str,
    url: str,
    days: int = 7,
    db_path: Path = DEFAULT_DB_PATH,
    now: datetime | None = None,
) -> bool:
    from ux_daily_brief.article_identity import normalize_url

    if article_id in recently_published_ids(
        days=days, db_path=db_path, now=now
    ):
        return True

    normalized = normalize_url(url)

    return bool(
        normalized
        and normalized in recently_published_urls(
            days=days, db_path=db_path, now=now
        )
    )
