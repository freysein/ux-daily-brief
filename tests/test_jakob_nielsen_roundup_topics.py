from ux_daily_brief.extractors.jakob_nielsen import extract_articles
from ux_daily_brief.models import Article


URL = "https://jakobnielsenphd.substack.com/p/ux-roundup-20261019"


def test_roundup_splits_topics():
    result = extract_articles(
        f"View post: {URL}",
        "UX Roundup: AI by Design Phase | Text Labels | Thumbnai…",
    )
    assert [item["title"] for item in result] == [
        "AI by Design Phase",
        "Text Labels",
    ]
    assert all(item["url"] == URL for item in result)


def test_distinct_topics_have_distinct_ids():
    result = extract_articles(
        f"View post: {URL}",
        "UX Roundup: AI Design | UX Research",
    )
    articles = [
        Article(
            source=item["source"],
            title=item["title"],
            url=item["url"],
            excerpt=item["excerpt"],
            origin="newsletter",
        )
        for item in result
    ]
    assert len({a.article_id for a in articles}) == 2


def test_single_article_remains_single():
    result = extract_articles(
        "https://jakobnielsenphd.substack.com/p/flow",
        "Flow in UX",
    )
    assert len(result) == 1
    assert result[0]["title"] == "Flow in UX"


def test_missing_url_is_rejected():
    assert extract_articles(
        "Newsletter without article link",
        "UX Roundup: AI | Design",
    ) == []


def test_incomplete_roundup_is_rejected():
    assert extract_articles(
        f"View post: {URL}",
        "UX Roundup: AI | Incomplete…",
    ) == []
