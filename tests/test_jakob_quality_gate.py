
from ux_daily_brief.article_pipeline import (
    extract_from_newsletter,
    needs_editorial_review,
)


def test_ambiguous_topics_require_review():
    assert needs_editorial_review(
        "jakob_nielsen", "Forecasting", "Forecasting"
    )
    assert needs_editorial_review(
        "jakob_nielsen", "Notifications", "Notifications"
    )


def test_specific_topics_remain_candidates():
    assert not needs_editorial_review(
        "jakob_nielsen",
        "Product Managers vs. Designers",
        "Product Managers vs. Designers",
    )


def test_other_sources_unaffected():
    assert not needs_editorial_review(
        "techcrunch", "Notifications", "Notifications"
    )


def test_real_article_review_status():
    articles = extract_from_newsletter({
        "source": "jakob_nielsen",
        "subject": "UX Roundup: Forecasting | AI by Design Phase",
        "body_text": (
            "View post: "
            "https://jakobnielsenphd.substack.com/p/ux-roundup-20261023"
        ),
        "body_html": "",
    })
    statuses = {article.title: article.review_status for article in articles}
    assert statuses["Forecasting"] == "review"
    assert statuses["AI by Design Phase"] == "candidate"
