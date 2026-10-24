from ux_daily_brief.article_identity import normalize_url


def test_tracking_parameters_removed():
    assert normalize_url(
        "https://example.com/article?utm_source=email&fbclid=abc"
    ) == "https://example.com/article"


def test_www_removed():
    assert normalize_url(
        "https://www.example.com/article/"
    ) == "https://example.com/article"


def test_protocol_normalization():
    assert normalize_url(
        "http://example.com/article"
    ) == "https://example.com/article"


def test_query_parameters_preserved():
    assert normalize_url(
        "https://example.com/article?page=2&utm_medium=email"
    ) == "https://example.com/article?page=2"


def test_query_order_independent():
    first = normalize_url(
        "https://example.com/article?b=2&a=1"
    )
    second = normalize_url(
        "https://example.com/article?a=1&b=2"
    )
    assert first == second


def test_empty_url():
    assert normalize_url(None) == ""
    assert normalize_url("") == ""


def test_invalid_scheme():
    assert normalize_url("javascript:alert(1)") == ""
