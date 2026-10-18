from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
INBOX = ROOT / "data" / "inbox" / "newsletters"
CONFIG = ROOT / "config" / "sources.yml"

MAX_PAYLOAD_BYTES = 2_000_000


def allowed_sources() -> set[str]:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    return {
        key
        for key, value in config["sources"].items()
        if value.get("access") == "newsletter"
    } | {"ux_inbox"}


def ingest(payload: dict) -> dict:
    if not isinstance(payload, dict):
        raise ValueError("Payload must be a JSON object")

    source = str(payload.get("source") or "ux_inbox").strip()

    if source not in allowed_sources():
        raise ValueError(f"Unsupported source: {source!r}")

    subject = str(payload.get("subject") or "").strip()
    body_text = str(payload.get("body_text") or "")
    body_html = str(payload.get("body_html") or "")

    if not subject:
        raise ValueError("Missing subject")

    if not body_text and not body_html:
        raise ValueError("Missing newsletter body")

    received_at = str(payload.get("received_at") or "").strip()
    if not received_at:
        received_at = datetime.now(timezone.utc).isoformat()

    message_id = str(payload.get("message_id") or "").strip()

    if not message_id:
        fingerprint = (
            source + "|" + subject + "|" + body_text + "|" + body_html
        ).encode("utf-8")
        message_id = hashlib.sha256(fingerprint).hexdigest()

    normalized = {
        "source": source,
        "message_id": message_id,
        "from": str(payload.get("from") or "").strip(),
        "subject": subject,
        "received_at": received_at,
        "source_url": str(payload.get("source_url") or "").strip(),
        "folder": str(payload.get("folder") or "").strip(),
        "body_text": body_text,
        "body_html": body_html,
        "ingested_at": datetime.now(timezone.utc).isoformat(),
    }

    encoded = json.dumps(
        normalized, ensure_ascii=False, indent=2
    ).encode("utf-8")

    if len(encoded) > MAX_PAYLOAD_BYTES:
        raise ValueError("Newsletter payload exceeds size limit")

    INBOX.mkdir(parents=True, exist_ok=True)

    digest = hashlib.sha256(
        f"{source}|{message_id}".encode("utf-8")
    ).hexdigest()

    target = INBOX / f"{source}_{digest[:24]}.json"

    if target.exists():
        return {
            "status": "duplicate",
            "source": source,
            "path": str(target),
        }

    # Prepare a complete temporary file before publishing it.
    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=INBOX,
            prefix=".ingest_",
            suffix=".tmp",
            delete=False,
        ) as tmp:
            temp_path = Path(tmp.name)
            os.chmod(temp_path, 0o600)
            tmp.write(encoded)

        # Atomic creation: an existing message is never overwritten.
        try:
            os.link(temp_path, target)
            status = "stored"
        except FileExistsError:
            status = "duplicate"

    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)

    return {
        "status": status,
        "source": source,
        "path": str(target),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--payload-b64", required=True)
    args = parser.parse_args()

    raw = base64.b64decode(args.payload_b64, validate=True)
    if len(raw) > MAX_PAYLOAD_BYTES:
        raise ValueError("Input payload exceeds size limit")

    payload = json.loads(raw.decode("utf-8"))
    result = ingest(payload)

    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
