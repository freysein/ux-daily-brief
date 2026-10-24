from ux_daily_brief.models import Article
from ux_daily_brief.prioritization import (
    keyword_score,
    prioritize_articles,
)


def make_article(title, excerpt=""):
    return Article(
        source="smashing",
        title=title,
        url="https://example.com/article",
        excerpt=excerpt,
        origin="rss",
    )


def test_ux_article_prioritized():
    ux = make_article("A practical guide to UX research")
    finance = make_article("Quarterly financial results")

    result = prioritize_articles([finance, ux])

    assert result[0] is ux


def test_scoring_does_not_change_article():
    article = make_article("Accessibility and usability research")

    original_score = article.score
    keyword_score(article)

    assert article.score == original_score


def test_priority_is_deterministic():
    articles = [
        make_article("Design systems"),
        make_article("UX research"),
    ]

    first = prioritize_articles(articles)
    second = prioritize_articles(articles)

    assert [x.title for x in first] == [x.title for x in second]
