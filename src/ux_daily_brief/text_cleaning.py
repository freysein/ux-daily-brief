import re

from ftfy import fix_text


def clean_text(value: str) -> str:
    if not value:
        return ""

    text = fix_text(value)

    # Remove an orphaned Â before whitespace or punctuation.
    text = re.sub(r"Â(?=\s|$|[,.!?;:])", "", text)

    # Normalize whitespace, including non-breaking spaces.
    text = re.sub(r"\s+", " ", text)

    return text.strip()
