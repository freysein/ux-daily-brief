from .newsletter_links import URL_RE, clean_url, plausible_title, candidate

import re


def clean_wired_title(title: str) -> str:
    """Repair common newsletter encoding issues and labels."""

    title = title.strip()

    # Repair UTF-8 interpreted as Latin-1 or Windows-1252.
    if any(marker in title for marker in ("â", "Ã", "Â")):
        for encoding in ("latin-1", "cp1252"):
            try:
                repaired = title.encode(encoding).decode("utf-8")
            except (UnicodeError, ValueError):
                continue
            if repaired:
                title = repaired
                break

    title = re.sub(r"^[✓●•✚]\s*", "", title)

    title = re.sub(
        r"^(?:Also in the news|AI Lab):\s*",
        "",
        title,
        flags=re.IGNORECASE,
    )

    return title.strip()


def extract_articles(text):
    results = {}
    lines = [line.strip() for line in (text or "").splitlines()]

    for i, line in enumerate(lines):
        for match in URL_RE.finditer(line):
            url = clean_url(match.group(), "wired.com", "/story/")
            if not url:
                continue

            for distance in range(1, 7):
                found = False
                for j in (i + distance, i - distance):
                    if not 0 <= j < len(lines):
                        continue

                    title = clean_wired_title(lines[j].strip(" *#<>"))
                    if not 12 <= len(title) <= 160:
                        continue
                    if "http" in title or "@" in title:
                        continue
                    if not plausible_title(title, url):
                        continue

                    results.setdefault(
                        url, candidate("wired", title, url)
                    )
                    found = True
                    break

                if found:
                    break

    return list(results.values())
