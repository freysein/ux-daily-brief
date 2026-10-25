
from ux_daily_brief.extractors.wired import (
    clean_wired_title,
    extract_articles,
)


def test_repair_mojibake():
    original = "Here’s Exactly How Tesla Made Its Car ‘Fly’"
    broken = original.encode("utf-8").decode("latin-1")
    assert clean_wired_title(broken) == original


def test_remove_newsletter_prefix():
    assert clean_wired_title(
        "✓ Also in the news: GM wants your car to do your chores"
    ) == "GM wants your car to do your chores"


def test_preserve_long_correct_title():
    title = (
        "A Design Flaw in Share Links Exposes Users' "
        "Personal Conversations With Meta's Muse"
    )
    assert clean_wired_title(title) == title


def test_extractor_uses_clean_title():
    text = chr(10).join([
        "https://www.wired.com/story/"
        "gm-wants-your-car-to-do-your-chores",
        "✓ Also in the news: GM wants your car to do your chores",
    ])
    result = extract_articles(text)
    assert len(result) == 1
    assert result[0]["title"] == (
        "GM wants your car to do your chores"
    )
