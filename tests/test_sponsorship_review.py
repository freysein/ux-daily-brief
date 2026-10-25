from unittest.mock import Mock, patch

from ux_daily_brief.models import Article
from ux_daily_brief.sponsorship_review import (
    check_article_sponsorship,
)


def make_article(source="t3n_ai", url=None):
    return Article(
        source=source,
        title="Security and Compliance",
        url=url or "https://t3n.de/news/example-123",
        excerpt="Information about enterprise compliance.",
        origin="rss",
    )


def response(status, html=""):
    result = Mock()
    result.status_code = status
    result.text = html
    return result


def test_sponsored_t3n_rejected():
    html = """
    <article>
      <span>Sponsored Post</span>
      <h1>Security and Compliance</h1>
    </article>
    """
    with patch(
        "ux_daily_brief.sponsorship_review.requests.get",
        return_value=response(200, html),
    ) as fetch:
        assert check_article_sponsorship(
            make_article()
        ) == "sponsored"

    assert fetch.call_args.args[0].endswith("/")


def test_editorial_t3n_allowed():
    html = "<article><h1>UX Research</h1></article>"
    with patch(
        "ux_daily_brief.sponsorship_review.requests.get",
        return_value=response(200, html),
    ):
        assert check_article_sponsorship(
            make_article()
        ) == "not_sponsored"


def test_http_error_requires_review():
    with patch(
        "ux_daily_brief.sponsorship_review.requests.get",
        return_value=response(403),
    ):
        assert check_article_sponsorship(
            make_article()
        ) == "review"


def test_external_domain_requires_review():
    with patch(
        "ux_daily_brief.sponsorship_review.requests.get",
    ) as fetch:
        assert check_article_sponsorship(
            make_article(url="https://example.com/article")
        ) == "review"
        fetch.assert_not_called()


def test_newsletter_source_not_fetched():
    with patch(
        "ux_daily_brief.sponsorship_review.requests.get",
    ) as fetch:
        assert check_article_sponsorship(
            make_article(source="techcrunch")
        ) == "not_sponsored"
        fetch.assert_not_called()


def test_missing_article_requires_review():
    with patch(
        "ux_daily_brief.sponsorship_review.requests.get",
        return_value=response(200, "<html>No article</html>"),
    ):
        assert check_article_sponsorship(
            make_article()
        ) == "review"
