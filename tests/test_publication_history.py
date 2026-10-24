from datetime import datetime, timedelta, timezone

from ux_daily_brief.publication_history import (
    record_publication,
    recently_published_ids,
)


NOW = datetime(2026, 10, 24, 12, 0, tzinfo=timezone.utc)


def test_empty_history(tmp_path):
    db = tmp_path / "history.duckdb"
    assert recently_published_ids(db_path=db, now=NOW) == set()


def test_recent_article_is_blocked(tmp_path):
    db = tmp_path / "history.duckdb"

    record_publication(
        "article-1",
        "smashing",
        "UX Article",
        "https://example.com/1",
        "2026-10-23",
        db_path=db,
        published_at=NOW - timedelta(days=1),
    )

    assert "article-1" in recently_published_ids(
        db_path=db, now=NOW
    )


def test_old_article_is_not_blocked(tmp_path):
    db = tmp_path / "history.duckdb"

    record_publication(
        "article-1",
        "smashing",
        "UX Article",
        "https://example.com/1",
        "2026-10-10",
        db_path=db,
        published_at=NOW - timedelta(days=14),
    )

    assert "article-1" not in recently_published_ids(
        db_path=db, now=NOW
    )


def test_duplicate_record_is_idempotent(tmp_path):
    db = tmp_path / "history.duckdb"

    args = (
        "article-1",
        "smashing",
        "UX Article",
        "https://example.com/1",
        "2026-10-23",
    )

    record_publication(
        *args, db_path=db,
        published_at=NOW - timedelta(days=1),
    )
    record_publication(
        *args, db_path=db,
        published_at=NOW - timedelta(days=1),
    )

    assert recently_published_ids(
        db_path=db, now=NOW
    ) == {"article-1"}


def test_same_url_with_tracking_is_blocked(tmp_path):
    from ux_daily_brief.publication_history import was_recently_published

    db = tmp_path / "history.duckdb"

    record_publication(
        "original-id",
        "techcrunch",
        "An Article About UX",
        "https://www.example.com/article?utm_source=newsletter",
        "2026-10-23",
        db_path=db,
        published_at=NOW - timedelta(days=1),
    )

    assert was_recently_published(
        "different-id",
        "https://example.com/article?utm_source=rss",
        db_path=db,
        now=NOW,
    )


def test_different_url_is_not_blocked(tmp_path):
    from ux_daily_brief.publication_history import was_recently_published

    db = tmp_path / "history.duckdb"

    record_publication(
        "original-id",
        "techcrunch",
        "An Article About UX",
        "https://example.com/first",
        "2026-10-23",
        db_path=db,
        published_at=NOW - timedelta(days=1),
    )

    assert not was_recently_published(
        "different-id",
        "https://example.com/second",
        db_path=db,
        now=NOW,
    )


def test_old_url_not_blocked(tmp_path):
    from ux_daily_brief.publication_history import was_recently_published

    db = tmp_path / "history.duckdb"

    record_publication(
        "old-id",
        "techcrunch",
        "Old Article",
        "https://example.com/old",
        "2026-10-10",
        db_path=db,
        published_at=NOW - timedelta(days=14),
    )

    assert not was_recently_published(
        "new-id",
        "https://example.com/old?utm_source=rss",
        db_path=db,
        now=NOW,
    )


def test_recent_stories_include_titles(tmp_path):
    from ux_daily_brief.publication_history import (
        recently_published_stories,
    )

    db = tmp_path / "history.duckdb"

    record_publication(
        "article-123",
        "techcrunch",
        "AI Agents Started Playing",
        "https://example.com/agents",
        "2026-10-23",
        db_path=db,
        published_at=NOW - timedelta(days=1),
    )

    stories = recently_published_stories(
        db_path=db,
        now=NOW,
    )

    assert len(stories) == 1
    assert stories[0]["article_id"] == "article-123"
    assert stories[0]["source"] == "techcrunch"
    assert stories[0]["title"] == "AI Agents Started Playing"


def test_stories_older_than_14_days_excluded(tmp_path):
    from ux_daily_brief.publication_history import (
        recently_published_stories,
    )

    db = tmp_path / "history.duckdb"

    record_publication(
        "old-article",
        "smashing",
        "Old UX Article",
        "https://example.com/old",
        "2026-10-01",
        db_path=db,
        published_at=NOW - timedelta(days=20),
    )

    assert recently_published_stories(
        db_path=db,
        now=NOW,
    ) == []


def test_stories_in_future_excluded(tmp_path):
    from ux_daily_brief.publication_history import (
        recently_published_stories,
    )

    db = tmp_path / "history.duckdb"

    record_publication(
        "future-article",
        "smashing",
        "Future UX Article",
        "https://example.com/future",
        "2026-10-25",
        db_path=db,
        published_at=NOW + timedelta(days=1),
    )

    assert recently_published_stories(
        db_path=db,
        now=NOW,
    ) == []


def test_publication_excerpt_roundtrip(tmp_path):
    from ux_daily_brief.publication_history import (
        recently_published_stories,
    )

    db = tmp_path / "history.duckdb"

    record_publication(
        "article-excerpt",
        "techcrunch",
        "AI Agents Started Playing",
        "https://example.com/agents",
        "2026-10-23",
        db_path=db,
        published_at=NOW - timedelta(days=1),
        excerpt="Researchers observed 13 AI agents on an island.",
    )

    stories = recently_published_stories(
        db_path=db,
        now=NOW,
    )

    assert len(stories) == 1
    assert stories[0]["excerpt"] == (
        "Researchers observed 13 AI agents on an island."
    )


def test_existing_database_migration(tmp_path):
    import duckdb
    from ux_daily_brief.publication_history import initialize_db

    db = tmp_path / "legacy.duckdb"

    with duckdb.connect(str(db)) as con:
        con.execute("""
            CREATE TABLE published_articles (
                article_id VARCHAR NOT NULL,
                source VARCHAR NOT NULL,
                title VARCHAR NOT NULL,
                url VARCHAR,
                edition_date DATE NOT NULL,
                published_at TIMESTAMPTZ NOT NULL,
                PRIMARY KEY (article_id, edition_date)
            )
        """)

    initialize_db(db)

    with duckdb.connect(str(db), read_only=True) as con:
        columns = {
            row[1]
            for row in con.execute(
                "PRAGMA table_info('published_articles')"
            ).fetchall()
        }

    assert "excerpt" in columns
