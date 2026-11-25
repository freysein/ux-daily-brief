from ux_daily_brief.extractors.nngroup import extract_articles as extract_nng
from ux_daily_brief.extractors.page_academy import extract_articles as extract_academy


def test_nng_articles_and_video_links():
    text = """
AI in UX: Work Is Faster, But Practitioners Have Mixed Feelings (https://www.nngroup.com/articles/ai-in-ux-survey-26/?utm_source=Alertbox)
UX Maps: Glossary (https://www.nngroup.com/articles/ux-disciplines-glossary/)
** 5 Design Principles in Context: Stripe (https://www.youtube.com/watch?v=qooOXNmdCH4)
** NN/G UX Podcast: Specs Are the Source Code (https://www.youtube.com/watch?v=YNe4dJxvT8U)
View in browser (https://mailchi.mp/nngroup/ai-in-ux)
"""
    found = extract_nng(text)
    titles = [item["title"] for item in found]
    assert len(found) == 4
    assert any("AI in UX" in title for title in titles)
    assert any("UX Maps" in title for title in titles)
    assert any("Stripe" in title for title in titles)
    assert any("Podcast" in title for title in titles)


def test_page_academy_course():
    html = """
<table><tr><td>
  <h3>KI-Tools: Wo fange ich an?</h3>
  <p>27. Oktober 2026</p>
  <div>Welche KI-Tools sind für Kreative wirklich interessant?
  In diesem zweistündigen Seminar gibt es praktische Einblicke.</div>
  <div><b><a href="https://click.cloud.ebnermedia.de/?qs=abc">→ Mehr erfahren</a></b></div>
</td></tr></table>
"""
    found = extract_academy(html)
    assert len(found) == 1
    assert found[0]["source"] == "page"
    assert found[0]["review_status"] == "review"
    assert "KI-Tools" in found[0]["title"]
    assert found[0]["url"].startswith("https://")


def test_page_academy_ignores_nav():
    html = '<a href="https://example.com">Impressum</a>'
    assert extract_academy(html) == []


def test_nng_markdown_form():
    found = extract_nng(
        "[AI in UX: Work Is Faster](https://www.nngroup.com/articles/ai-in-ux-survey-26/)"
    )
    assert len(found) == 1
    assert found[0]["title"] == "AI in UX: Work Is Faster"
