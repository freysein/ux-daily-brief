from ux_daily_brief.extractors.nngroup import extract_articles as nng
from ux_daily_brief.extractors.wired import extract_articles as wired
from ux_daily_brief.article_pipeline import extract_from_newsletter

def test_nng_article():
    text = (
        "UX Maps: Glossary "
        "(https://www.nngroup.com/articles/ux-maps-glossary/)"
    )
    assert len(nng(text)) == 1

def test_nng_excludes_courses():
    text = (
        "Designing AI Experiences "
        "(https://www.nngroup.com/courses/designing-ai-experiences/)"
    )
    assert nng(text) == []

def test_wired_article():
    text = (
        "<https://www.wired.com/story/"
        "a-design-flaw-in-share-links-exposes-users-personal-conversations-with-meta-muse"
        "?utm_source=newsletter>\n"
        "A Design Flaw in Share Links Exposes Users Personal "
        "Conversations With Meta Muse\n"
    )
    result = wired(text)
    assert len(result) == 1
    assert "utm_" not in result[0]["url"]

def test_wired_synthetic_message():
    assert wired("This is a synthetic test message.") == []

def test_pipeline_integration():
    result = extract_from_newsletter({
        "source": "nngroup",
        "body_text": (
            "UX Maps: Glossary "
            "(https://www.nngroup.com/articles/ux-maps-glossary/)"
        ),
        "body_html": "",
    })
    assert len(result) == 1
    assert result[0].source == "nngroup"
