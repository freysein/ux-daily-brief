import pytest

from ux_daily_brief import scoring_cache
from ux_daily_brief.models import Article


def make_article(excerpt="A UX research finding."):
    return Article(
        source="page",
        title="New UX Research",
        url="https://example.com/article",
        excerpt=excerpt,
        origin="rss",
    )


def test_cache_key_stable():
    assert (
        scoring_cache.cache_key(make_article())
        == scoring_cache.cache_key(make_article())
    )


def test_changed_content_changes_key():
    assert (
        scoring_cache.cache_key(make_article("First version"))
        != scoring_cache.cache_key(make_article("Updated version"))
    )


def test_cache_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(scoring_cache, "CACHE_DIR", tmp_path)

    article = make_article()
    result = {
        "status": "scored",
        "score": 55.5,
        "qualified": True,
    }

    scoring_cache.save_cached(article, result)

    assert scoring_cache.load_cached(article) == result


def test_do_not_cache_errors(tmp_path, monkeypatch):
    monkeypatch.setattr(scoring_cache, "CACHE_DIR", tmp_path)

    with pytest.raises(ValueError):
        scoring_cache.save_cached(
            make_article(),
            {"status": "error", "score": None},
        )
