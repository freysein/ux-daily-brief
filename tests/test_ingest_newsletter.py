import json
from pathlib import Path

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
    assert result["source"] == "ux_inbox"
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


def test_unknown_sender(inbox):
    result = module.ingest(
        payload(source="wired", **{"from": "unknown@example.org"})
    )

    assert result["source"] == "ux_inbox"
    assert result["status"] == "stored"


@pytest.mark.parametrize(
    "sender,expected",
    [
        ("WIRED Daily <wired@newsletters.wired.com>", "wired"),
        ("TechCrunch <newsletters@techcrunch.com>", "techcrunch"),
        ("Nielsen Norman Group <alertbox@nngroup.com>", "nngroup"),
        ("PAGE <page@cloud.ebnermedia.de>", "page"),
    ],
)
def test_known_newsletter_sources(inbox, sender, expected):
    result = module.ingest(
        payload(
            message_id=f"test-{expected}",
            **{"from": sender},
        )
    )

    assert result["status"] == "stored"
    assert result["source"] == expected

    saved = json.loads(Path(result["path"]).read_text(encoding="utf-8"))
    assert saved["source"] == expected
    assert saved["from"] == sender


def test_duplicate_cannot_overwrite_original(inbox):
    original = payload(body_text="Original newsletter content")
    first = module.ingest(original)

    changed = payload(body_text="Modified newsletter content")
    second = module.ingest(changed)

    assert first["status"] == "stored"
    assert second["status"] == "duplicate"

    saved = json.loads(Path(first["path"]).read_text(encoding="utf-8"))
    assert saved["body_text"] == "Original newsletter content"
