"""Read-only preview of approved YouTube sources; never sends a newsletter."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ux_daily_brief.youtube_intelligence import (
    configured_channels, parse_feed, discover, inspect, ManualTranscriptProvider,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "config/sources.yml")
    parser.add_argument("--transcripts", type=Path,
                        default=ROOT / "data/inbox/youtube_transcripts")
    sources = parser.add_mutually_exclusive_group(required=True)
    sources.add_argument("--online", action="store_true")
    sources.add_argument("--feed-fixture", type=Path)
    parser.add_argument("--source", help="Approved source ID for a fixture")
    parser.add_argument("--seen-video-ids", type=Path,
                        help="Read-only JSON list of previously seen video IDs")
    parser.add_argument("--limit-per-channel", type=int, default=15)
    args = parser.parse_args()

    if args.online:
        videos, status = discover(args.config, args.limit_per_channel)
    else:
        cfg = configured_channels(args.config)
        if args.source not in cfg:
            parser.error("--source must identify a configured approved source")
        videos = parse_feed(args.source, cfg[args.source]["channel_id"],
                            args.feed_fixture.read_bytes())
        status = {args.source: {"status": "fixture", "discovered": len(videos)}}

    seen = set()
    if args.seen_video_ids:
        raw = json.loads(args.seen_video_ids.read_text(encoding="utf-8"))
        if not isinstance(raw, list) or not all(isinstance(x, str) for x in raw):
            parser.error("--seen-video-ids must be a JSON list of strings")
        seen = set(raw)

    result = inspect(videos, ManualTranscriptProvider(args.transcripts), seen)
    result["feed_status"] = status
    result["mode"] = "read_only"
    result["production_integration"] = "disabled"
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
