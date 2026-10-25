from .newsletter_links import URL_RE, clean_url, plausible_title, candidate

def extract_articles(text):
    results = {}
    for line in (text or "").splitlines():
        for match in URL_RE.finditer(line):
            url = clean_url(match.group(), "nngroup.com", "/articles/")
            if not url:
                continue

            title = line[:match.start()].strip(" *([<")
            if not plausible_title(title, url):
                continue

            results.setdefault(url, candidate("nngroup", title, url))

    return list(results.values())
