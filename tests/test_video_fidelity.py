"""Tests of the video fidelity instrument (``tools/video_fidelity.py``, WP3.10, V4 and DR-18).

The instrument's readings on real encodes are exercised by ``test_io_video_encode.py``; this
module covers its own guards: the sentinel positive control (CHARC round-0 ruling (a)), the
roster invariant, the missing-pts count, the telemetry redaction, the NVENC proof and the CLI.
"""

from __future__ import annotations

import json
from dataclasses import replace
from fractions import Fraction
from pathlib import Path
from typing import Any

import pytest

import video_fidelity as vf
from clearwater.interfaces.video import SinkReport
from clearwater.io.video import FFmpegVideoSink, VideoEncodeError, nut, probe
from container_spike import compare, spike

pytestmark = pytest.mark.usefixtures("ffmpeg_tools")


class _OneByteFrame(FFmpegVideoSink):
    """Sends the third frame as a one-byte payload, bypassing the carrier's guard."""

    def __init__(self, *, skip_verify: bool = False) -> None:
        super().__init__()
        self._skip_verify = skip_verify

    def write(self, frame: Any) -> None:
        if len(self._written) == 2:
            self._send(nut._header(frame.pts_ticks, 1) + b"\x01")
            self._written.append(frame.pts_ticks)
            return
        super().write(frame)

    def _verify(self, end: int) -> SinkReport:
        if self._skip_verify:
            return SinkReport(len(self._written), (), ())
        return super()._verify(end)


def _encode(sink: FFmpegVideoSink, source: Path, out: Path) -> SinkReport:
    info = probe(source)
    out.write_bytes(b"")
    sink.open(info, out, encoder="libx265", quality="draft", bit_depth=8, provenance=None)
    for frame in vf.decode_frames(source, info):
        sink.write(frame)
    return sink.close()


def test_a_one_byte_real_frame_is_caught_by_the_sink_and_the_instrument(
    sample: Any, tmp_path: Path
) -> None:
    source = sample("vid-vfr")
    with pytest.raises(VideoEncodeError) as caught:
        _encode(_OneByteFrame(), source, tmp_path / "checked.mp4")
    assert caught.value.kind == "verify_failed"
    assert "29 video frames in the output where 30 were written" in str(caught.value)
    out = tmp_path / "unchecked.mp4"
    _encode(_OneByteFrame(skip_verify=True), source, out)
    record = vf.fidelity_record(source, out)
    items = {item["name"]: item for item in record["items"]}
    assert items["video frame count"]["status"] == "DIFFERENT"
    assert items["video frame count"]["output"] == 29
    assert not record["summary"]["mandatory_and_required_all_same"]


def _item(name: str, status: str = compare.SAME) -> compare.Item:
    return compare.Item(name, compare.MANDATORY, "x", 1, 1, status)


def test_the_roster_fails_on_a_missing_or_unexpected_item() -> None:
    full = [_item(name) for name in vf.ROSTER]
    assert vf.roster_item(full).status == compare.SAME
    missing = vf.roster_item(full[1:])
    assert missing.status == compare.DIFFERENT
    assert missing.output["missing"] == [vf.ROSTER[0]]
    keyed = [_item(f"{n} [soun#0]") if n == vf.AUDIO_PACKETS else _item(n) for n in vf.ROSTER]
    assert vf.roster_item(keyed).status == compare.SAME
    extra = vf.roster_item([*full, _item("something new")])
    assert extra.status == compare.DIFFERENT and extra.output["unexpected"] == ["something new"]


def test_a_missing_item_fails_the_summary(
    sample: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = sample("vid-vfr")
    out = tmp_path / "out.mp4"
    _encode(FFmpegVideoSink(), source, out)
    real = compare.compare_facts
    monkeypatch.setattr(
        compare, "compare_facts", lambda s, o: [i for i in real(s, o) if i.name != "bit depth"]
    )
    record = vf.fidelity_record(source, out)
    assert not record["summary"]["mandatory_and_required_all_same"]
    assert vf._ROSTER_ITEM in record["summary"]["different_items"][compare.MANDATORY]


def _facts(pts: list[Fraction | None]) -> compare.Facts:
    movie = compare.Movie((), "isom", (), 1000, 0, (), ())
    return compare.Facts(Path("f"), {}, movie, 0, pts, {}, {})


def test_frames_without_pts_are_counted_in_both_files() -> None:
    good = _facts([Fraction(0), Fraction(1, 30)])
    assert vf._missing_pts_item(good, good).status == compare.SAME
    bad = vf._missing_pts_item(good, _facts([Fraction(0), None]))
    assert bad.status == compare.DIFFERENT and (bad.source, bad.output) == (0, 1)
    assert vf._missing_pts_item(_facts([None]), good).status == compare.DIFFERENT


def test_the_telemetry_track_keeps_only_packet_counts() -> None:
    summary = {"count": 23, "first": ["0.0", "1.0", 100, "MD5:abc"], "sha256": "f" * 64}
    item = compare.Item(
        vf.TELEMETRY_ITEM + " (pts, duration, size, MD5) [meta#0]",
        compare.BEST_EFFORT,
        "x",
        summary,
        summary,
        compare.SAME,
        "note",
    )
    redacted = vf._redact(item)
    assert (redacted.source, redacted.output, redacted.status) == ({"count": 23},) * 2 + (
        compare.SAME,
    )
    assert "MD5" not in json.dumps([redacted.source, redacted.output, redacted.note])
    other = _item("audio streams present")
    assert vf._redact(other) is other


def _run(
    encoder: str, rows: list[tuple[float, str, int, str]], error: str | None = None
) -> vf.EncodeRun:
    gpu = vf.GpuSamples({"0": "GPU-1234"}, rows, error)
    return vf.EncodeRun(SinkReport(1, (), ()), encoder, 8, 4242, 100.0, 110.0, gpu)


def test_the_nvenc_proof_ties_the_pid_gpu_and_window() -> None:
    tied = vf.nvenc_proof(_run("hevc_nvenc", [(1.0, "0", 4242, "37"), (2.0, "0", 999, "50")]))
    assert tied["tied"] and tied["gpu_uuid"] == ["GPU-1234"] and tied["pid"] == 4242
    assert tied["pid_samples_with_encoder_load"] == [[1.0, "0", 4242, "37"]]
    for rows in ([(1.0, "0", 999, "50")], [(1.0, "0", 4242, "-")], [(11.0, "0", 4242, "40")]):
        proof = vf.nvenc_proof(_run("hevc_nvenc", rows))
        assert not proof["tied"] and "no sample" in proof["reason"]
    assert vf.nvenc_proof(_run("hevc_nvenc", [], "nvidia-smi is not available")) == {
        "tied": False,
        "reason": "nvidia-smi is not available",
    }
    assert not vf.nvenc_proof(_run("libx265", []))["tied"]


def test_the_cli_compares_into_the_working_folder_only(sample: Any, tmp_path: Path) -> None:
    working, footage = tmp_path / "work", tmp_path / "footage"
    working.mkdir()
    footage.mkdir()
    config = tmp_path / "local.toml"
    config.write_text(
        f"footage_path = {json.dumps(str(footage))}\nworking_path = {json.dumps(str(working))}\n"
    )
    source = sample("vid-vfr")
    out = tmp_path / "out.mp4"
    _encode(FFmpegVideoSink(), source, out)
    assert vf.main(["compare", str(source), str(out), "--config", str(config)]) == 0
    record = json.loads((working / vf.SUBDIR / "out.compare.json").read_text())
    assert record["summary"]["mandatory_and_required_all_same"]
    refused = ["compare", str(source), str(out), "--config", str(config), "--out", str(footage)]
    assert vf.main(refused) == 2


def test_an_effect_of_an_absent_edit_list_is_the_identity_from_zero() -> None:
    track = compare.Track(1, 3, "vide", "", "avc1", (), 30000, 60060, (), None, 2002)
    rows = vf.effect(compare.Movie((), "isom", (), 1000, 0, (track,), ()), track)
    assert rows == [
        {"duration": compare.exact(Fraction(2002, 30000)), "media_start": "empty", "rate": "1"},
        {
            "duration": compare.exact(Fraction(60060, 30000)),
            "media_start": compare.exact(Fraction(0)),
            "rate": "1",
        },
    ]
    at_zero = replace(track, earliest_composition=0)
    assert len(vf.effect(compare.Movie((), "isom", (), 1000, 0, (at_zero,), ()), at_zero)) == 1


# --- DR-26: the WP1.5 spike finds chapters in subfolders --------------------------------------


def test_the_spike_resolves_chapters_through_the_footage_locator(tmp_path: Path) -> None:
    footage = tmp_path / "footage"
    (footage / "Snorkel").mkdir(parents=True)
    (footage / "Snorkel" / "GX000001.MP4").write_bytes(b"x")
    (footage / "SCUBA").mkdir()
    (footage / "SCUBA" / "GX000002.mp4").write_bytes(b"x")
    (footage / "SCUBA" / "GX000002.LRV").write_bytes(b"x")
    expected = footage / "Snorkel" / "GX000001.MP4"
    assert spike._chapter(footage, "GX000001.MP4") == expected
    assert spike._chapter(footage, "GX000001") == expected
    assert spike._default_chapters(footage) == ["GX000001", "GX000002"]
    for bad in ("GX000009.MP4", "Snorkel/GX000001.MP4", "..", "GX000001.MOV"):
        with pytest.raises(spike.SpikeError):
            spike._chapter(footage, bad)
