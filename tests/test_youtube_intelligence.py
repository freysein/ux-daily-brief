"""Offline synthetic tests: no network and no production state."""
from datetime import datetime, timezone
import json
from unittest.mock import Mock
import pytest

from ux_daily_brief.youtube_intelligence import (
    Video, Transcript, ManualTranscriptProvider, configured_channels,
    parse_feed, discover, inspect, ollama_synthesis,
)

CID = "UCsBjURrPoezykLs9EqgamOA"
VID = "AbCdEfGhI12"
VIDEO = Video(VID, "fireship", CID, "UX demo",
              "A synthetic description", datetime(2026, 11, 20, tzinfo=timezone.utc))
WORDS = " ".join("word" for _ in range(180))


def config(tmp_path):
    file = tmp_path / "sources.yml"
    file.write_text("sources:\n  fireship:\n    name: Fireship\n    access: youtube_rss\n"
                    "    processing: transcript_required\n"
                    f"    feed_url: https://www.youtube.com/feeds/videos.xml?channel_id={CID}\n"
                    "  iaap_dach:\n    access: newsletter\n")
    return file


def xml(channel=CID, video=VID):
    return (f'<feed xmlns="http://www.w3.org/2005/Atom" '
            f'xmlns:yt="http://www.youtube.com/xml/schemas/2015">'
            f'<yt:channelId>{channel}</yt:channelId>'
            f'<entry><yt:channelId>{channel}</yt:channelId>'
            f'<yt:videoId>{video}</yt:videoId><title>UX demo</title>'
            f'<published>2026-11-20T08:00:00Z</published></entry></feed>').encode()


def test_only_approved_configured_sources(tmp_path):
    assert list(configured_channels(config(tmp_path))) == ["fireship"]


def test_valid_feed_and_canonical_url():
    rows = parse_feed("fireship", CID, xml())
    assert len(rows) == 1 and rows[0].url.endswith(VID)
    assert rows[0].as_article().origin == "youtube"


def test_malformed_xml_rejected():
    with pytest.raises(ValueError):
        parse_feed("fireship", CID, b"no XML")


def test_wrong_channel_rejected():
    with pytest.raises(ValueError):
        parse_feed("fireship", CID, xml(channel="UC0000000000000000000000"))


def test_invalid_video_id_skipped():
    assert parse_feed("fireship", CID, xml(video="bad")) == []


def test_http_error_is_reported(tmp_path):
    import requests
    def timeout(*args, **kwargs):
        raise requests.Timeout()
    rows, status = discover(config(tmp_path), fetcher=timeout)
    assert rows == []
    assert status["fireship"]["status"] == "error"


@pytest.mark.parametrize("status", ["partial", "unavailable", "access_denied", "error"])
def test_incomplete_transcripts_not_usable(status):
    assert not Transcript(VID, status, "en", WORDS, "manual", True, "full").usable


def test_rights_and_completeness_are_required():
    assert not Transcript(VID, "complete", "en", WORDS, "manual", False, "full").usable
    assert not Transcript(VID, "complete", "en", WORDS, "manual", True, "").usable
    assert Transcript(VID, "complete", "de", WORDS, "manual", True, "verified").usable


def test_manual_import(tmp_path):
    (tmp_path / f"{VID}.json").write_text(json.dumps({
        "video_id": VID, "status": "complete", "language": "en",
        "text": WORDS, "rights_approved": True,
        "completeness_evidence": "Publisher verified entire video"}))
    assert ManualTranscriptProvider(tmp_path).get(VIDEO).usable


def test_manual_import_invalid_json(tmp_path):
    (tmp_path / f"{VID}.json").write_text("{")
    assert ManualTranscriptProvider(tmp_path).get(VIDEO).status == "error"


def test_duplicate_and_incremental_filter(tmp_path):
    result = inspect([VIDEO, VIDEO], ManualTranscriptProvider(tmp_path))
    assert result["total"] == 1
    assert inspect([VIDEO], ManualTranscriptProvider(tmp_path), {VID})["total"] == 0


def test_disallowed_transcript_is_link_only(tmp_path):
    assert inspect([VIDEO], ManualTranscriptProvider(tmp_path))["link_candidates"] == 1


def test_unapproved_transcript_cannot_be_synthesized():
    with pytest.raises(ValueError):
        ollama_synthesis(VIDEO, Transcript(VID, "partial"))


def test_large_transcript_is_chunked_and_synthesized():
    long = Transcript(VID, "complete", "de", " ".join(["word"] * 2700),
                      "approved", True, "Verified entire coverage")
    client = Mock()
    answer = {"summary": " ".join(["word"] * 80),
              "ux_impact": "Test UX impact", "evidence": "Excerpt evidence"}
    responses = iter([{"response": "facts"}] * 3 + [{"response": json.dumps(answer)}])
    def post(*args, **kwargs):
        response = Mock()
        response.json.return_value = next(responses)
        return response
    client.post.side_effect = post
    assert ollama_synthesis(VIDEO, long, session=client)["ux_impact"] == "Test UX impact"
    assert client.post.call_count == 4
