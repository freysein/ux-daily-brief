
from ux_daily_brief.extractors.wired import clean_wired_title
from ux_daily_brief.article_pipeline import needs_editorial_review


def test_plus_prefix_removed():
    assert clean_wired_title(
        "✚ AI Lab: This startup is all in on recursive self-improvement"
    ) == "This startup is all in on recursive self-improvement"


def test_reply_all_truncation():
    title = (
        "An AI Agent Joined a Listserv of Top Internet Researchers. "
        "The Reply-All Chaos"
    )
    assert needs_editorial_review("wired", title, title)


def test_meta_truncation():
    title = (
        "A Design Flaw in Share Links Exposes Users’ Personal "
        "Conversations With Meta’s"
    )
    assert needs_editorial_review("wired", title, title)


def test_valid_headline_remains_candidate():
    title = "Encryption Is Getting Squeezed From All Sides"
    assert not needs_editorial_review("wired", title, title)
