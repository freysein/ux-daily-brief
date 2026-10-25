
from ux_daily_brief.article_pipeline import needs_editorial_review


def test_wired_truncated_headline_requires_review():
    title = (
        "Katie Zacharia Was Linked to an AI Rare-Earths "
        "Startup. It's Even Weirder Than"
    )
    assert needs_editorial_review("wired", title, title)


def test_wired_complete_headline_allowed():
    title = (
        "Split Tunneling Is Your VPN's Best Feature. "
        "Here's How to Make the Most of It"
    )
    assert not needs_editorial_review("wired", title, title)


def test_wired_short_headline_allowed():
    assert not needs_editorial_review(
        "wired", "AI and Design", "AI and Design"
    )


def test_jakob_quality_gate_preserved():
    assert needs_editorial_review(
        "jakob_nielsen", "Forecasting", "Forecasting"
    )
