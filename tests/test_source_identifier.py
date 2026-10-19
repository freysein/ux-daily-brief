from ux_daily_brief.source_identifier import identify_source


def test_wired():
    result = identify_source(
        "WIRED Daily <wired@newsletters.wired.com>"
    )
    assert result["source"] == "wired"
    assert result["processing"] == "newsletter_only"


def test_techcrunch():
    result = identify_source("newsletters@techcrunch.com")
    assert result["source"] == "techcrunch"


def test_nngroup():
    result = identify_source(
        "Nielsen Norman Group <alertbox@nngroup.com>"
    )
    assert result["source"] == "nngroup"


def test_page():
    result = identify_source("page@cloud.ebnermedia.de")
    assert result["source"] == "page"
    assert result["processing"] == "full_analysis"


def test_case_insensitive():
    result = identify_source(
        "WIRED <WIRED@NEWSLETTERS.WIRED.COM>"
    )
    assert result["source"] == "wired"


def test_unknown_sender():
    result = identify_source("unknown@example.org")
    assert result["source"] == "ux_inbox"
    assert result["identified"] is False
