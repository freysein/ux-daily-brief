from datetime import datetime, timezone

from ux_daily_brief.models import Article
from ux_daily_brief import duplicate_check
from ux_daily_brief.edition_duplicates import check_edition_duplicate


NOW = datetime(2026, 10, 25, tzinfo=timezone.utc)
URL = "https://jakobnielsenphd.substack.com/p/ux-roundup-20261023"


def article(title, source="jakob_nielsen", url=URL):
    return Article(
        source=source,
        title=title,
        url=url,
        excerpt=title,
        origin="newsletter",
    )


def test_distinct_roundup_topics_same_edition(monkeypatch):
    monkeypatch.setattr(
        "ux_daily_brief.edition_duplicates.compare_stories",
        lambda *args: {
            "same_story": False,
            "confidence": 1.0,
            "reason": "Different topics",
        },
    )
    result = check_edition_duplicate(
        article("Notifications"),
        [article("Boomerang Browsing")],
    )
    assert result.status == "unique"


def test_identical_roundup_topic_same_edition():
    result = check_edition_duplicate(
        article("Notifications"),
        [article("Notifications")],
    )
    assert result.status == "duplicate"


def test_other_sources_still_deduplicate_same_url():
    result = check_edition_duplicate(
        article("Headline B", source="techcrunch"),
        [article("Headline A", source="techcrunch")],
    )
    assert result.status == "duplicate"


def test_roundup_different_id_allowed_against_history(monkeypatch):
    previous = article("Boomerang Browsing")
    monkeypatch.setattr(
        duplicate_check, "recently_published_ids",
        lambda **kwargs: {previous.article_id},
    )
    monkeypatch.setattr(
        duplicate_check, "recently_published_stories",
        lambda **kwargs: [],
    )
    result = duplicate_check.check_duplicate(
        article("Notifications"), now=NOW
    )
    assert result.status == "unique"


def test_roundup_same_id_blocked_against_history(monkeypatch):
    previous = article("Boomerang Browsing")
    monkeypatch.setattr(
        duplicate_check, "recently_published_ids",
        lambda **kwargs: {previous.article_id},
    )
    result = duplicate_check.check_duplicate(previous, now=NOW)
    assert result.status == "duplicate"
