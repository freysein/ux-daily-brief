from dataclasses import replace

from ux_daily_brief.brief_content import (
    BriefEntry,
    CATEGORIES,
    validate_entry,
    word_count,
)


def sample_entry():
    return BriefEntry(
        article_id="test-123",
        title="Accordion Icons and Interaction Design",
        summary=" ".join(["Example"] * 80),
        ux_impact="Potential implication: Review icon clarity.",
        category=CATEGORIES[3],
        source="smashing",
        url="https://example.com/article",
        editorial_classification="core_ux",
    )


def test_valid_entry():
    assert validate_entry(sample_entry()) == []


def test_summary_too_short():
    entry = replace(
        sample_entry(), summary=" ".join(["Word"] * 69)
    )
    assert "invalid_summary_length" in validate_entry(entry)


def test_summary_too_long():
    entry = replace(
        sample_entry(), summary=" ".join(["Word"] * 101)
    )
    assert "invalid_summary_length" in validate_entry(entry)


def test_invalid_category():
    entry = replace(
        sample_entry(), category="General Technology"
    )
    assert "invalid_category" in validate_entry(entry)


def test_missing_ux_impact():
    entry = replace(sample_entry(), ux_impact="")
    assert "missing_ux_impact" in validate_entry(entry)


def test_word_count_with_hyphens():
    assert word_count("Human-centered design matters.") == 3
