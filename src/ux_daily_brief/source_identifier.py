from __future__ import annotations

from email.utils import parseaddr
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
SENDERS_CONFIG = ROOT / "config" / "newsletter_senders.yml"
SOURCES_CONFIG = ROOT / "config" / "sources.yml"


def identify_source(sender: str) -> dict:
    """Identify a newsletter using its confirmed sender address."""

    _, address = parseaddr(sender or "")
    address = address.strip().lower()

    senders = yaml.safe_load(
        SENDERS_CONFIG.read_text(encoding="utf-8")
    )["senders"]

    sources = yaml.safe_load(
        SOURCES_CONFIG.read_text(encoding="utf-8")
    )["sources"]

    for source_id, entry in senders.items():
        addresses = [
            value.strip().lower()
            for value in entry.get("addresses", [])
        ]

        if address in addresses:
            source = sources[source_id]

            return {
                "source": source_id,
                "name": source["name"],
                "processing": source["processing"],
                "identified": True,
            }

    return {
        "source": "ux_inbox",
        "name": "Unidentified UX Newsletter",
        "processing": "pending",
        "identified": False,
    }
