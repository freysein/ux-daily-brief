from ux_daily_brief.extractors.newsletter_links import clean_url
from ux_daily_brief.extractors.wired import extract_articles


def test_wired_tracking_removed():
    url = clean_url(
        "https://www.wired.com/story/example?"
        "cndid=123&utm_source=newsletter",
        "wired.com",
        "/story/",
    )
    assert url == "https://wired.com/story/example"



def test_wired_duplicate_tracking_variants():
    text = chr(10).join([
        "https://www.wired.com/story/design-flaw-in-share-links?cndid=1",
        "Design Flaw in Share Links",
        "https://www.wired.com/story/design-flaw-in-share-links?cndid=2",
        "Design Flaw in Share Links",
    ])

    result = extract_articles(text)

    assert len(result) == 1
    assert result[0]["url"] == (
        "https://wired.com/story/design-flaw-in-share-links"
    )


def test_nngroup_url_unchanged():
    url = clean_url(
        "https://www.nngroup.com/articles/ux-maps-glossary/",
        "nngroup.com",
        "/articles/",
    )
    assert url == "https://nngroup.com/articles/ux-maps-glossary"
