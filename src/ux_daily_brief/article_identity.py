from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


TRACKING_PARAMETERS = {
    "fbclid",
    "gclid",
    "dclid",
    "msclkid",
    "mc_cid",
    "mc_eid",
    "igshid",
    "ref_src",
}


def normalize_url(url: str | None) -> str:
    if not url or not url.strip():
        return ""

    url = url.strip()
    parsed = urlsplit(url)

    if parsed.scheme.lower() not in {"http", "https"}:
        return ""

    hostname = (parsed.hostname or "").lower()

    if not hostname:
        return ""

    if hostname.startswith("www."):
        hostname = hostname[4:]

    try:
        port = parsed.port
    except ValueError:
        return ""

    if port and not (
        (parsed.scheme.lower() == "http" and port == 80)
        or (parsed.scheme.lower() == "https" and port == 443)
    ):
        hostname = f"{hostname}:{port}"

    path = parsed.path.rstrip("/") or "/"

    parameters = [
        (key, value)
        for key, value in parse_qsl(
            parsed.query, keep_blank_values=True
        )
        if not key.lower().startswith("utm_")
        and key.lower() not in TRACKING_PARAMETERS
    ]

    parameters.sort()

    return urlunsplit(
        ("https", hostname, path, urlencode(parameters), "")
    )
