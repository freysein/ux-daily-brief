from unittest.mock import Mock, patch

import pytest

from ux_daily_brief.fulltext_smashing import (
    FulltextExtractionError,
    extract_smashing_text,
    fetch_smashing_text,
)


CONTENT = " ".join(["Useful UX guidance."] * 60)

HTML = f"""
<html>
<body>
<nav>Site navigation</nav>
<article>
    <div class="article__content">
        <h2>Accordion interaction patterns</h2>
        <p>{CONTENT}</p>
        <aside>Unrelated promotion</aside>
        <p>Use clear labels alongside controls.</p>
    </div>
</article>
</body>
</html>
"""


def test_extract_article_content():
    text = extract_smashing_text(HTML)

    assert "Useful UX guidance" in text
    assert "Accordion interaction patterns" in text
    assert "Site navigation" not in text
    assert "Unrelated promotion" not in text


def test_missing_container():
    with pytest.raises(FulltextExtractionError):
        extract_smashing_text("<html><p>No article</p></html>")


def test_short_article_rejected():
    with pytest.raises(FulltextExtractionError):
        extract_smashing_text(
            '<div class="article__content">'
            "<p>Too short.</p></div>"
        )


def test_unapproved_domain_rejected():
    with pytest.raises(FulltextExtractionError):
        fetch_smashing_text(
            "https://example.com/article"
        )


def test_successful_fetch():
    response = Mock()
    response.status_code = 200
    response.text = HTML

    with patch(
        "ux_daily_brief.fulltext_smashing.requests.get",
        return_value=response,
    ) as getter:
        text = fetch_smashing_text(
            "https://www.smashingmagazine.com/article/"
        )

    assert "Useful UX guidance" in text
    getter.assert_called_once()




def test_approved_internal_redirect():
    redirect = Mock()
    redirect.status_code = 301
    redirect.headers = {
        "Location": "https://www.smashingmagazine.com/article/"
    }

    final = Mock()
    final.status_code = 200
    final.text = HTML

    with patch(
        "ux_daily_brief.fulltext_smashing.requests.get",
        side_effect=[redirect, final],
    ) as getter:
        text = fetch_smashing_text(
            "https://smashingmagazine.com/article/"
        )

    assert "Useful UX guidance" in text
    assert getter.call_count == 2


def test_external_redirect_rejected():
    redirect = Mock()
    redirect.status_code = 302
    redirect.headers = {
        "Location": "https://example.com/other"
    }

    with patch(
        "ux_daily_brief.fulltext_smashing.requests.get",
        return_value=redirect,
    ) as getter:
        with pytest.raises(
            FulltextExtractionError,
            match="Unapproved redirect",
        ):
            fetch_smashing_text(
                "https://www.smashingmagazine.com/article/"
            )

    getter.assert_called_once()


def test_redirect_without_location_rejected():
    redirect = Mock()
    redirect.status_code = 302
    redirect.headers = {}

    with patch(
        "ux_daily_brief.fulltext_smashing.requests.get",
        return_value=redirect,
    ) as getter:
        with pytest.raises(
            FulltextExtractionError,
            match="Redirect missing Location",
        ):
            fetch_smashing_text(
                "https://www.smashingmagazine.com/article/"
            )

    getter.assert_called_once()
