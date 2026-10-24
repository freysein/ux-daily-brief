from datetime import datetime, timezone

from ux_daily_brief.article_pipeline import parse_received_at


def test_imap_date():
    result = parse_received_at("Fri, 23 Oct 2026 23:53:34 -0600")

    assert result == datetime(
        2026, 10, 24, 5, 53, 34,
        tzinfo=timezone.utc,
    )


def test_iso_date():
    result = parse_received_at("2026-10-24T10:30:00+02:00")

    assert result == datetime(
        2026, 10, 24, 8, 30,
        tzinfo=timezone.utc,
    )


def test_missing_date():
    assert parse_received_at(None) is None


def test_invalid_date():
    assert parse_received_at("not a date") is None


def test_naive_date_rejected():
    assert parse_received_at("2026-10-24T10:30:00") is None
