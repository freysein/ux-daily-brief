from ux_daily_brief.article_pipeline import (
    extract_from_newsletter,
    extract_from_inbox,
)
from ux_daily_brief.models import Article


def test_unknown_source_is_skipped():
    result = extract_from_newsletter({
        "source": "ux_inbox",
        "body_html": "<p>Unknown newsletter</p>",
    })

    assert result == []


def test_empty_newsletter():
    result = extract_from_newsletter({
        "source": "techcrunch",
        "body_html": "",
    })

    assert result == []


def test_returns_article_objects():
    html = """
    <div>
      <p>How AI changes user experience : A detailed look at
      how AI-driven systems influence digital product design.</p>
      <p>
        <a href="https://example.com/story">Read More</a>
      </p>
    </div>
    """

    result = extract_from_newsletter({
        "source": "techcrunch",
        "body_html": html,
    })

    assert len(result) == 1
    assert isinstance(result[0], Article)
    assert result[0].origin == "newsletter"


def test_empty_inbox(tmp_path):
    assert extract_from_inbox(tmp_path) == []
