from ux_daily_brief.extractors.jakob_nielsen import extract_articles
from ux_daily_brief.article_pipeline import extract_from_newsletter


def test_extract_flow_article():
    result = extract_articles(
        "View this post on the web at "
        "https://jakobnielsenphd.substack.com/p/flow",
        "Flow in UX",
    )
    assert len(result) == 1
    assert result[0]["source"] == "jakob_nielsen"
    assert result[0]["url"].endswith("/p/flow")


def test_reject_missing_article_url():
    assert extract_articles("Unsubscribe here", "Flow in UX") == []


def test_generic_inbox_sender_and_text_only():
    articles = extract_from_newsletter({
        "source": "ux_inbox",
        "from": "Jakob Nielsen <jakobnielsenphd@substack.com>",
        "subject": "Flow in UX",
        "body_html": "",
        "body_text": (
            "View this post on the web at "
            "https://jakobnielsenphd.substack.com/p/flow"
        ),
        "received_at": "Mon, 19 Oct 2026 11:21:34 +0000",
    })

    assert len(articles) == 1
    assert articles[0].source == "jakob_nielsen"
    assert articles[0].origin == "newsletter"
