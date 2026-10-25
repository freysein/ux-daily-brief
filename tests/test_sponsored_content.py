from ux_daily_brief.sponsored_content import (
    detect_sponsored_content,
)


def test_t3n_sponsored_post():
    html = """
    <article>
        <span>Sponsored Post</span>
        <h1>Security und Compliance</h1>
        <p>Content about enterprise compliance.</p>
    </article>
    """
    assert detect_sponsored_content(html)


def test_t3n_anzeige():
    html = """
    <article>
        <span class="c-badge">Anzeige</span>
        <h1>Commercial content</h1>
    </article>
    """
    assert detect_sponsored_content(html)


def test_normal_editorial_article():
    html = """
    <article>
        <h1>Accessibility in Design Systems</h1>
        <p>Research into inclusive interface design.</p>
    </article>
    """
    assert not detect_sponsored_content(html)


def test_keyword_inside_editorial_text():
    html = """
    <article>
        <h1>Advertising and UX</h1>
        <p>Werbung beeinflusst die Nutzererfahrung.</p>
    </article>
    """
    assert not detect_sponsored_content(html)


def test_advertisement_outside_article():
    html = """
    <aside><span>Anzeige</span></aside>
    <article>
        <h1>Independent UX research</h1>
        <p>Research findings about navigation.</p>
    </article>
    """
    assert not detect_sponsored_content(html)


def test_empty_html():
    assert not detect_sponsored_content("")
