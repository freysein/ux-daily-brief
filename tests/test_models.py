import pytest

from ux_daily_brief.models import Article


def test_article_creation():
    article = Article(
        source="techcrunch",
        title="AI and User Experience",
        url="https://example.com/story",
        excerpt="How AI changes digital experiences.",
        origin="newsletter",
    )

    assert article.review_status == "candidate"
    assert article.score is None
    assert len(article.article_id) == 24


def test_stable_article_id():
    values = dict(
        source="page",
        title="New UX Research",
        url="https://example.com/ux",
        excerpt="A research article.",
        origin="newsletter",
    )

    assert Article(**values).article_id == Article(**values).article_id


def test_invalid_origin():
    with pytest.raises(ValueError, match="Invalid origin"):
        Article(
            source="page",
            title="Test Article",
            url="https://example.com",
            excerpt="Example",
            origin="unknown",
        )


def test_serialization():
    article = Article(
        source="page",
        title="Information Design",
        url="https://example.com/design",
        excerpt="A design story.",
        origin="newsletter",
    )

    data = article.to_dict()

    assert data["source"] == "page"
    assert data["published_at"] is None
    assert data["review_status"] == "candidate"
