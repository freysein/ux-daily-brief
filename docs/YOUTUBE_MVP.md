# YouTube Transcript Intelligence MVP

Status: opt-in, read-only preview only. Does not modify the 06:00 pipeline,
publication DuckDB, edition history, n8n, or production deployment configuration.

## Configured channels
The existing `config/sources.yml` defines YouTube Atom feeds for Fireship,
Two Minute Papers, and The Futur. IAAP DACH has no verified YouTube channel ID:
do not invent or activate it without verification.

## Features
- Discover and validate video ID, owner channel, title, publish time, canonical URL.
- Deduplicate videos by video ID. Read an optional externally supplied seen-ID list.
- Manually read publisher-supplied, approved complete transcripts from
  `data/inbox/youtube_transcripts/<video_id>.json` (never commit raw transcripts).
- Require status=complete, rights_approved=true, language en/de, sufficient
  content, and explicit completeness evidence before classifying as a Featured
  *candidate*. This is not publication approval.
- Videos without verified complete approved transcripts are metadata-only link
  candidates. No unauthorized transcript scraping, video download or ASR.
- Chunked Ollama synthesis is callable explicitly, not by the dry-run command.
- Does not currently retrieve creator captions automatically, and does not
  integrate video content into scoring, selection, newsletter rendering or n8n.

## Read-only command
```bash
PYTHONPATH=src .venv/bin/python scripts/youtube_mvp_preview.py --online --limit-per-channel 10
```

Optional local transcript file example (use real transcript only when authorized):
```json
{
  "video_id": "AbCdEfGhI12",
  "status": "complete",
  "language": "en",
  "text": "An actual full authorized transcript, not a summary",
  "rights_approved": true,
  "acquisition_source": "publisher_supplied",
  "completeness_evidence": "Publisher confirmed full caption coverage"
}
```
The example is illustrative only and too short to be eligible.

Offline tests:
```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_youtube_intelligence.py -q
```

The official YouTube Data API captions download requires OAuth and sufficient
rights on the video; an ordinary viewer cannot assume access to other creators'
captions. The safe default is an authorized manual transcript import and
metadata-only discovery.

## Release safety
Only merge after CI and review. Production activation requires a separate
change to the ingestion/scoring/selection pipeline and explicit approval.
