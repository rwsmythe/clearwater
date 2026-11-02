"""Tests of the video fidelity instrument (``tools/video_fidelity.py``, WP3.10, V4 and DR-18).

The instrument's readings on real encodes are exercised by ``test_io_video_encode.py``; this
module covers its own guards: the sentinel positive control (CHARC round-0 ruling (a)), the
roster invariant, the missing-pts count, the telemetry redaction, the NVENC proof and the CLI.
"""

from __future__ import annotations

import json
import subprocess
import threading
import time
from dataclasses import replace
from fractions import Fraction
from pathlib import Path
from typing import Any

import pytest

import test_container_spike_compare_equivalences as pcm_cases
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


Row = tuple[float, float, str, int, str]


def _run(encoder: str, rows: list[Row], error: str | None = None) -> vf.EncodeRun:
    gpu = vf.GpuSamples({"0": "GPU-1234"}, rows, error)
    return vf.EncodeRun(SinkReport(1, (), ()), encoder, 8, 4242, 5000.0, 5010.0, gpu)


def test_the_nvenc_proof_ties_the_pid_gpu_and_window() -> None:
    inside: Row = (5001.0, 5002.0, "0", 4242, "37")
    tied = vf.nvenc_proof(_run("hevc_nvenc", [inside, (5002.0, 5003.0, "0", 999, "50")]))
    assert tied["tied"] and tied["gpu_uuid"] == ["GPU-1234"] and tied["pid"] == 4242
    assert tied["pid_samples_with_encoder_load"] == [[1.0, 2.0, "0", 4242, "37"]]
    overlapping: Row = (4999.5, 5000.5, "0", 4242, "12")  # the call ran across the start
    assert vf.nvenc_proof(_run("hevc_nvenc", [overlapping]))["tied"]
    for rows in (
        [(5001.0, 5002.0, "0", 999, "50")],
        [(5001.0, 5002.0, "0", 4242, "-")],
        [(5011.0, 5012.0, "0", 4242, "40")],  # after the window
        [(4990.0, 4999.0, "0", 4242, "40")],  # before it
        [(1.0, 2.0, "0", 4242, "40")],  # a time on another clock (round-1 finding 7)
    ):
        proof = vf.nvenc_proof(_run("hevc_nvenc", rows))
        assert not proof["tied"] and "no sample" in proof["reason"]
    assert vf.nvenc_proof(_run("hevc_nvenc", [], "nvidia-smi is not available")) == {
        "tied": False,
        "reason": "nvidia-smi is not available",
    }
    assert not vf.nvenc_proof(_run("libx265", []))["tied"]


def test_the_nvenc_proof_is_not_tied_without_a_resolved_gpu_uuid() -> None:
    # Round-2 #3: a hit on a GPU index with no UUID read "tied" with a "?" UUID.
    for gpus in ({}, {"0": ""}, {"1": "GPU-1234"}):
        gpu = vf.GpuSamples(gpus, [(5001.0, 5002.0, "0", 4242, "37")], None)
        run = vf.EncodeRun(SinkReport(1, (), ()), "hevc_nvenc", 8, 4242, 5000.0, 5010.0, gpu)
        proof = vf.nvenc_proof(run)
        assert not proof["tied"] and proof["gpu_uuid"] == [], proof
        assert "GPU index 0" in proof["reason"] and "no UUID" in proof["reason"]


def test_the_sampler_and_the_encode_window_share_one_clock(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Round-1 finding 7: samples were timed from the sampler's start, the window by wall clock,
    # so an encode that began after the sampler was judged against the wrong origin.
    running = threading.Event()

    def fake_smi(arguments: Any) -> str:
        if arguments[0] == "pmon":
            seen = "    0 4242 C 10 5 37 0 ffmpeg" + chr(10) if running.is_set() else ""
            return "# gpu pid type sm mem enc dec" + chr(10) + seen
        return "0, GPU-1234" + chr(10)

    monkeypatch.setattr(vf, "_nvidia_smi", fake_smi)
    monkeypatch.setattr(vf, "_PMON_PERIOD_S", 0.01)
    monkeypatch.setattr(FFmpegVideoSink, "_start", lambda self, command: running.set())
    sink = vf._RecordingSink()
    sampler = vf._Sampler()
    sampler.start()
    time.sleep(0.3)  # the encode window opens well after the sampler
    sink._start([])
    give_up = time.monotonic() + 10
    while time.monotonic() < give_up and len(sampler.samples.rows) < 3:
        time.sleep(0.01)
    sink.ended = vf._clock()
    samples = sampler.stop()
    run = vf.EncodeRun(
        SinkReport(1, (), ()), "hevc_nvenc", 8, 4242, sink.started, sink.ended, samples
    )
    proof = vf.nvenc_proof(run)
    assert proof["tied"] and proof["gpu_uuid"] == ["GPU-1234"], proof


def test_location_values_never_reach_the_record(tmp_path: Path) -> None:
    # Round-1 finding 2: tag items carried every tag value, a location included.
    clip = tmp_path / "located.mp4"
    subprocess.run(
        ["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "lavfi",
         "-i", "testsrc2=size=64x48:rate=30:duration=0.3", "-c:v", "libx264", "-bf", "0",
         "-metadata", "location=+27.9881+086.9250/", str(clip)],
        check=True, capture_output=True,
    )  # fmt: skip
    positive = json.dumps(compare.compare_files(clip, clip))
    assert "27.9881" in positive  # the plant reaches WP1.5's record (the positive control)
    record = vf.fidelity_record(clip, clip)
    text = json.dumps(record)
    assert "27.9881" not in text and "086.9250" not in text
    items = {item["name"]: item for item in record["items"]}
    tags = items["container tags other than creation_time"]
    assert tags["source"]["location"] == vf.LOCATION_WITHHELD and tags["status"] == "SAME"
    atoms = items["camera atoms: moov/udta children (type, bytes, MD5)"]["source"]
    assert any(atom[2] == vf.LOCATION_WITHHELD for atom in atoms)  # the xyz atom's digest
    assert vf.location_like("com.apple.quicktime.location.ISO6709")
    assert vf.location_like("\u00a9xyz") and not vf.location_like("encoder")


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


def test_colour_rows_compare_with_the_resolved_description_and_never_skip() -> None:
    from clearwater.interfaces.image import ColorDescription

    full = ColorDescription("bt709", "bt709", "bt709", "full", 8, False, None)
    info = replace(_probe_like(full))
    rows = [
        compare.Item("colour range", compare.REQUIRED, "x", "pc", "tv", compare.SAME),
        compare.Item("colour primaries", compare.REQUIRED, "x", None, "bt709", compare.DIFFERENT),
        compare.Item("colour matrix", compare.REQUIRED, "x", "bt709", "bt709", compare.SAME),
    ]
    out = {i.name: i for i in vf._colour_items(rows, info)}
    assert out["colour range"].status == compare.DIFFERENT  # yuvj420p source, tv output
    assert out["colour primaries"].status == compare.SAME  # raw tag absent, resolved bt709
    assert out["colour primaries"].source == {"resolved (D54)": "bt709", "source tag": None}
    unknown = replace(info, video=replace(info.video, color=replace(full, matrix="unknown")))
    skipped = {i.name: i for i in vf._colour_items(rows, unknown)}
    assert skipped["colour matrix"].status == compare.DIFFERENT
    assert "never skipped" in skipped["colour matrix"].note


def _probe_like(color: Any) -> Any:
    from clearwater.interfaces.video import ProbeResult, VideoStreamInfo

    video = VideoStreamInfo(
        "hevc", 16, 16, 8, "yuvj420p", "left", color, Fraction(30), Fraction(1, 30), 1, 0, False
    )
    return ProbeResult(Path("s"), "mp4", Fraction(1), Fraction(0), video, (), (), (), (), None)


@pytest.mark.parametrize("shape", pcm_cases._PCM_D86)
def test_pcm_d86_sample_extent_equivalence(shape: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """D86 normalizes only the readable source tail and discloses both PCM readings."""
    before, after, end = pcm_cases._pcm_pair(shape)
    source, output = pcm_cases._pcm_facts(before), pcm_cases._pcm_facts(after, output=True)
    assert end is not None
    items, notes = pcm_cases._pcm_fidelity_reading(monkeypatch, source, output, end)
    packet = next(i for i in items if i.name.startswith(vf.AUDIO_PACKETS))
    side = next(i for i in items if i.name == "audio priming and packet side data")
    note = pcm_cases._pcm_note(*pcm_cases._PCM_COUNTS[shape])
    assert (packet.item_class, packet.status) == (compare.MANDATORY, compare.SAME)
    assert packet.note == note
    assert (side.item_class, side.status) == (compare.MANDATORY, compare.SAME)
    assert note in side.note and f"{note} [soun#0]" in notes
    assert any(n.startswith("D86:") for n in notes)
    assert items[-1].name == vf._ROSTER_ITEM and items[-1].status == compare.SAME


@pytest.mark.parametrize("shape", ["earlier-source-partial", "output-partial"])
def test_pcm_d86_difference_control(shape: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """The final-source floor cannot excuse an earlier source or any output partial frame."""
    before, after, end = pcm_cases._pcm_pair(shape)
    source, output = pcm_cases._pcm_facts(before), pcm_cases._pcm_facts(after, output=True)
    assert end is not None
    items, _ = pcm_cases._pcm_fidelity_reading(monkeypatch, source, output, end)
    packet = next(i for i in items if i.name.startswith(vf.AUDIO_PACKETS))
    assert (packet.item_class, packet.status) == (compare.MANDATORY, compare.DIFFERENT)


@pytest.mark.parametrize("change", ["discard", "side-data"])
def test_pcm_side_data_control(change: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """A planted PCM discard flag or skip-samples payload must reach the per-packet rule."""
    table, _, _ = pcm_cases._pcm_pair("one-sample-fewer")
    source, output = pcm_cases._pcm_facts(table), pcm_cases._pcm_facts(table, output=True)
    items, _ = pcm_cases._pcm_fidelity_reading(monkeypatch, source, output, side_change=change)
    packet = next(i for i in items if i.name.startswith(vf.AUDIO_PACKETS))
    side = next(i for i in items if i.name == "audio priming and packet side data")
    assert packet.status == compare.SAME  # Packet payload/timing is deliberately unchanged.
    assert (side.item_class, side.status) == (compare.MANDATORY, compare.DIFFERENT)
    assert "PCM: compared by sample extent" not in side.note
