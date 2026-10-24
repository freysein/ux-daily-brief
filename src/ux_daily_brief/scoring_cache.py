from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ux_daily_brief.models import Article
from ux_daily_brief import ollama_scoring


ROOT = Path(__file__).resolve().parents[2]
CACHE_DIR = ROOT / "data" / "state" / "scoring_cache"


def cache_key(article: Article) -> str:
    scoring_code = Path(
        ollama_scoring.__file__
    ).read_bytes()

    revision = hashlib.sha256(scoring_code).hexdigest()

    payload = {
        "source": article.source,
        "title": article.title,
        "excerpt": article.excerpt[:3500],
        "model": ollama_scoring.OLLAMA_MODEL,
        "scoring_revision": revision,
    }

    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
    ).encode("utf-8")

    return hashlib.sha256(encoded).hexdigest()


def load_cached(article: Article) -> dict | None:
    path = CACHE_DIR / f"{cache_key(article)}.json"

    if not path.exists():
        return None

    data = json.loads(path.read_text(encoding="utf-8"))

    if data.get("status") != "scored":
        return None

    if not isinstance(data.get("score"), (int, float)):
        return None

    return data


def save_cached(article: Article, result: dict) -> Path:
    if result.get("status") != "scored":
        raise ValueError("Only successful scores may be cached")

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    target = CACHE_DIR / f"{cache_key(article)}.json"

    from tempfile import NamedTemporaryFile
    import os

    temporary = None
    try:
        with NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=CACHE_DIR,
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            json.dump(result, handle, ensure_ascii=False, indent=2)

        os.replace(temporary, target)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)

    return target
