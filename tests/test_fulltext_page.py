from unittest.mock import Mock, patch

import pytest

from ux_daily_brief.fulltext_page import (
    PageExtractionError,
    extract_page_text,
    fetch_page_text,
)


BODY = " ".join(
    ["The design system connects several visual elements."]
    * 35
)

HTML = f"""
<html>
<body>
<article>
    <h1>Design Doha Biennial</h1>
    <p>{BODY}</p>
    <h2>Schriftsysteme, die eins werden</h2>
    <p>{BODY}</p>
    <h2>Das könnte dich auch interessieren</h2>
    <p>Unrelated recommended article content.</p>
    <h2>Weitere Artikel zu diesem Thema</h2>
    <p>More unrelated recommendations.</p>
</article>
</body>
</html>
"""


def test_extract_page_article():
    result = extract_page_text(HTML)

    assert "design system connects" in result
    assert "Schriftsysteme" in result
    assert "Unrelated recommended" not in result
    assert "More unrelated" not in result


def test_missing_article_rejected():
    with pytest.raises(PageExtractionError):
        extract_page_text("<html><p>No article</p></html>")


def test_short_content_rejected():
    with pytest.raises(PageExtractionError):
        extract_page_text(
            "<article><p>Too short.</p></article>"
        )


def test_external_url_rejected():
    with pytest.raises(PageExtractionError):
        fetch_page_text(
            "https://example.com/article"
        )


def test_page_fetch():
    response = Mock()
    response.status_code = 200
    response.text = HTML

    with patch(
        "ux_daily_brief.fulltext_page.requests.get",
        return_value=response,
    ) as getter:
        result = fetch_page_text(
            "https://page-online.de/kreation/example/"
        )

    assert "design system connects" in result
    getter.assert_called_once()


def test_redirect_rejected():
    response = Mock()
    response.status_code = 302

    with patch(
        "ux_daily_brief.fulltext_page.requests.get",
        return_value=response,
    ):
        with pytest.raises(
            PageExtractionError,
            match="redirect requires review",
        ):
            fetch_page_text(
                "https://page-online.de/kreation/example/"
            )


def test_comment_prompt_excluded():
    html = f"""
    <article>
        <h1>Design Doha Biennial</h1>
        <p>{BODY}</p>
        <p>Schreibe einen Kommentar</p>
    </article>
    """

    result = extract_page_text(html)

    assert "Schreibe einen Kommentar" not in result
