from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from typing import Optional


@dataclass
class Article:
    source: str
    title: str
    url: str
    excerpt: str
    origin: str

    published_at: Optional[datetime] = None
    review_status: str = "candidate"
    score: Optional[float] = None
    ux_impact: str = ""
    article_id: str = field(init=False)

    def __post_init__(self) -> None:
        if self.origin not in {"newsletter", "rss", "youtube"}:
            raise ValueError(f"Invalid origin: {self.origin}")

        if not self.source.strip():
            raise ValueError("Article source is required")

        if not self.title.strip():
            raise ValueError("Article title is required")

        self.article_id = sha256(
            f"{self.source}|{self.url}|{self.title}".encode("utf-8")
        ).hexdigest()[:24]

    def to_dict(self) -> dict:
        return {
            "article_id": self.article_id,
            "source": self.source,
            "title": self.title,
            "url": self.url,
            "excerpt": self.excerpt,
            "origin": self.origin,
            "published_at": (
                self.published_at.isoformat()
                if self.published_at else None
            ),
            "review_status": self.review_status,
            "score": self.score,
            "ux_impact": self.ux_impact,
        }
