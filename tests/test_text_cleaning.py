from ux_daily_brief.text_cleaning import clean_text


def test_utf8_mojibake():
    assert clean_text("Anthropicâs") == "Anthropic's"


def test_orphaned_character():
    assert clean_text("right nowÂ") == "right now"


def test_whitespace():
    assert clean_text("UX \n research   matters") == "UX research matters"


def test_preserve_valid_text():
    assert clean_text("UX research & design") == "UX research & design"
