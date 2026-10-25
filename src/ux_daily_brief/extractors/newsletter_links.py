import re
from urllib.parse import urlsplit
from ux_daily_brief.article_identity import normalize_url

URL_RE = re.compile(r"https?://[^\s<>\])]+", re.I)

def clean_url(raw, domain, prefix):
    raw = raw.replace("\\", "").rstrip(".,;")
    url = normalize_url(raw)
    parsed = urlsplit(url)
    if parsed.hostname != domain:
        return ""
    if not parsed.path.startswith(prefix):
        return ""

    # WIRED newsletter query parameters are tracking metadata.
    if domain == "wired.com":
        return f"https://wired.com{parsed.path}"

    return url

def plausible_title(title, url):
    def tokens(value):
        return set(re.findall(r"[a-z0-9]{3,}", value.lower()))

    slug = urlsplit(url).path.rstrip("/").split("/")[-1]
    a = tokens(title)
    b = tokens(slug.replace("-", " "))
    common = a & b
    return len(common) >= 2 and len(common) / max(len(b), 1) >= 0.4

def candidate(source, title, url):
    return {
        "source": source,
        "title": title,
        "url": url,
        "excerpt": title,
    }
