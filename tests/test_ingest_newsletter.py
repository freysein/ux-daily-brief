import pytest

from ux_daily_brief import ingest_newsletter as module


@pytest.fixture
def inbox(tmp_path, monkeypatch):
    monkeypatch.setattr(module, "INBOX", tmp_path)
    return tmp_path


def payload(**overrides):
    data = {
        "source": "ux_inbox",
        "message_id": "test-message-001",
        "from": "test@example.org",
        "subject": "UX Newsletter Test",
        "received_at": "2026-10-18T12:00:00+02:00",
        "body_text": "A valid newsletter message.",
        "body_html": "",
    }
    data.update(overrides)
    return data


def test_store_newsletter(inbox):
    result = module.ingest(payload())

    assert result["status"] == "stored"
    assert len(list(inbox.glob("*.json"))) == 1


def test_duplicate_newsletter(inbox):
    first = module.ingest(payload())
    second = module.ingest(payload())

    assert first["status"] == "stored"
    assert second["status"] == "duplicate"
    assert first["path"] == second["path"]
    assert len(list(inbox.glob("*.json"))) == 1


def test_missing_subject(inbox):
    with pytest.raises(ValueError, match="Missing subject"):
        module.ingest(payload(subject=""))


def test_missing_body(inbox):
    with pytest.raises(ValueError, match="Missing newsletter body"):
        module.ingest(payload(body_text="", body_html=""))


def test_unknown_source(inbox):
    with pytest.raises(ValueError, match="Unsupported source"):
        module.ingest(payload(source="unknown_source"))


def test_known_newsletter_source(inbox):
    result = module.ingest(
        payload(source="nngroup", message_id="nngroup-test-001")
    )

    assert result["status"] == "stored"
    assert result["source"] == "nngroup"
