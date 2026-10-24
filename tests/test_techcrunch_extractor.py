from ux_daily_brief.extractors.techcrunch import extract_articles


def test_extract_article():
    html = """
    <div>
      <p>How AI changes product design : Researchers explore
      practical approaches to user-centered design in AI products.</p>
      <p><a href="https://link.techcrunch.com/story123">Read More</a></p>
    </div>
    """

    articles = extract_articles(html)

    assert len(articles) == 1
    assert articles[0]["source"] == "techcrunch"
    assert articles[0]["title"] == "How AI changes product design"
    assert "user-centered design" in articles[0]["excerpt"]
    assert articles[0]["review_status"] == "candidate"


def test_ignore_navigation():
    html = """
    <div>
      <p><a href="https://example.com">Unsubscribe</a></p>
    </div>
    """

    assert extract_articles(html) == []


def test_ignore_incomplete_article():
    html = """
    <div>
      <p>Short title : Too short.</p>
      <p><a href="https://example.com">Read More</a></p>
    </div>
    """

    assert extract_articles(html) == []


def test_ignore_duplicate_links():
    html = """
    <div>
      <p>Interesting UX research findings : A detailed investigation
      of how people interact with modern interfaces.</p>
      <p>
        <a href="https://example.com/story">Read More</a>
        <a href="https://example.com/story">Read More</a>
      </p>
    </div>
    """

    assert len(extract_articles(html)) == 1
