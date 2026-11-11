"""Portable controls for the test-only DR-163 timing recorder (no native/GPU encodes)."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import shutil
import struct
import subprocess
from fractions import Fraction
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _helpers():
    path = Path(os.environ.get("WP65_MACOS_TEST_SCRIPT", ROOT / "tests/test_macos_portability.py"))
    spec = importlib.util.spec_from_file_location("wp65_timing_helpers", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _movie(path, *, version=0, ctts_version=0):
    """Make known raw timing, with an audio track BEFORE the video track."""
    import test_io_video_probe_boxes as b

    offset = -3 if ctts_version else 2**31 + 3
    ctts_form = ">IIIi" if ctts_version else ">IIII"
    stbl = b.box("stts", struct.pack(">II4I", 0, 2, 2, 1001, 1, 2002))
    stbl += b.box("ctts", struct.pack(ctts_form, ctts_version << 24, 1, 3, offset))
    stbl += b.box("stsz", struct.pack(">III", 0, 16, 3))
    tkhd = struct.pack(">Bxxx", version) + b"\0" * (24 if version else 16)
    tkhd += struct.pack(">Q" if version else ">I", 4004)
    video = b.box(
        "trak",
        b.box("tkhd", tkhd)
        + b.box("edts", b.elst([(500, -1, 1, 0), (4004, 0, 1, 0)], version=version))
        + b.box(
            "mdia",
            b.header_box("mdhd", 30000, version=version)
            + b.hdlr("vide")
            + b.box("minf", b.box("stbl", stbl)),
        ),
    )
    path.write_bytes(
        b.FTYP + b.moov(b.header_box("mvhd", 1000, version=version), b.trak("soun", 48000), video)
    )
    return path


def _record(text, prefix):
    matches = [line.removeprefix(prefix) for line in text.splitlines() if line.startswith(prefix)]
    assert len(matches) == 1, f"Missing or ambiguous evidence field: {prefix}"
    return json.loads(matches[0])


@pytest.mark.parametrize(("version", "ctts_version"), [(0, 0), (1, 1)])
def test_timing_writer_retains_full_raw_tables_and_header_durations(
    tmp_path, monkeypatch, version, ctts_version
):
    """Last-only stts, signed v0 ctts, or the audio tkhd would lose decisive raw evidence."""
    import clearwater.io.video as video

    module = _helpers()
    output = _movie(tmp_path / "output.mp4", version=version, ctts_version=ctts_version)
    monkeypatch.setattr(video, "find_tool", lambda name: Path("ffprobe-not-executed"))
    monkeypatch.setattr(
        module,
        "_run",
        lambda argv: SimpleNamespace(
            returncode=0, stdout="packet|pts=2002|duration=2002", stderr=""
        ),
    )
    destination = tmp_path / "evidence.txt"
    module._write_vt_failure(
        output, destination, first=0, end=4004, time_base=Fraction(1, 30000), error="test"
    )
    raw = _record(destination.read_text(), "output boxes: ")
    assert raw["stts"] == [[2, 1001], [1, 2002]]
    assert raw["ctts"] == {
        "version": ctts_version,
        "entries": [[3, -3 if ctts_version else 2**31 + 3]],
    }
    assert raw["sample_count"] == 3
    assert raw["stsz_sample_count"] == 3
    assert raw["movie_timescale"] == 1000 and raw["media_timescale"] == 30000
    assert raw["elst_version"] == version
    assert raw["elst"] == [
        {"segment_duration": 500, "media_time": -1, "rate": "1"},
        {"segment_duration": 4004, "media_time": 0, "rate": "1"},
    ]
    assert raw["durations"] == {
        "mvhd": {"version": version, "ticks": 99},
        "mdhd": {"version": version, "ticks": 99},
        "tkhd": {"version": version, "ticks": 4004},
    }


def test_timing_writer_preserves_source_identity_recipe_packets_and_written_sequence(
    tmp_path, monkeypatch
):
    """Source timing, the sink's actual frame rate and argv must survive in the evidence."""
    import clearwater.io.video as video

    module = _helpers()
    source = _movie(tmp_path / "source.mp4")
    output = _movie(tmp_path / "output.mp4")
    monkeypatch.setattr(video, "find_tool", lambda name: Path("ffprobe-not-executed"))
    monkeypatch.setattr(
        module,
        "_run",
        lambda argv: SimpleNamespace(
            returncode=0,
            stdout=f"packet|pts=2002|duration=2002\nstream|time_base=1/30000|avg_frame_rate=22500/1001|r_frame_rate=30000/1001\nformat|filename={argv[-1]}",
            stderr="",
        ),
    )
    destination = tmp_path / "evidence.txt"
    module._write_vt_failure(
        output,
        destination,
        first=0,
        end=4004,
        time_base=Fraction(1, 30000),
        error="test",
        source=source,
        recipe="sample:vid-vfr (tools/fixtures/video.py)",
        written_pts=[0, 1001, 2002],
        frame_rate=Fraction(22500, 1001),
        encode_argv=["ffmpeg", "-i", "pipe:0", str(output)],
    )
    text = destination.read_text()
    assert _record(text, "source identity: ") == {
        "path": str(source),
        "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "size_bytes": source.stat().st_size,
        "recipe": "sample:vid-vfr (tools/fixtures/video.py)",
    }
    assert _record(text, "source boxes: ")["stts"] == [[2, 1001], [1, 2002]]
    assert _record(text, "written pts: ") == [0, 1001, 2002]
    assert "sentinel pts: 4004" in text and "source probe.video.frame_rate: 22500/1001" in text
    assert _record(text, "encode argv: ") == ["ffmpeg", "-i", "pipe:0", str(output)]
    assert f"format|filename={source}" in text and f"format|filename={output}" in text
    assert "avg_frame_rate=22500/1001|r_frame_rate=30000/1001" in text


@pytest.mark.parametrize("fails", [False, True])
def test_interception_records_x265_success_or_original_failure_before_cleanup(
    tmp_path, monkeypatch, fails
):
    """The same hook captures controls, observes argv unchanged and preserves exception identity."""
    from clearwater.io.video import FFmpegVideoSink, VideoEncodeError

    module = _helpers()
    source = _movie(tmp_path / "source.mp4")
    output = _movie(tmp_path / "finished.mp4")
    failure = VideoEncodeError("verify_failed", "original duration refusal")
    result = object()
    original_bytes = output.read_bytes()
    forwarded = []
    monkeypatch.setattr(FFmpegVideoSink, "_start", lambda sink, argv: forwarded.append(list(argv)))

    def verify(sink, end):
        if fails:
            raise failure
        return result

    monkeypatch.setattr(FFmpegVideoSink, "_verify", verify)
    monkeypatch.setattr(
        module,
        "_run",
        lambda argv: SimpleNamespace(returncode=0, stdout="packet|duration=2002", stderr=""),
    )
    import clearwater.io.video as video

    monkeypatch.setattr(video, "find_tool", lambda name: Path("ffprobe-not-executed"))
    module._capture_vt_failure(
        monkeypatch,
        "clip:vfr-gap-libx265-10",
        tmp_path / "evidence",
        source=source,
        recipe="clip:vfr-gap (test_io_video_encode.Clips)",
    )
    sink = SimpleNamespace(
        _out_path=output,
        _written=[0, 1001, 2002],
        _probe=SimpleNamespace(
            video=SimpleNamespace(time_base=Fraction(1, 30000), frame_rate=Fraction(22500, 1001))
        ),
    )
    argv = ["ffmpeg", "-i", "pipe:0", str(output)]
    FFmpegVideoSink._start(sink, argv)
    try:
        if fails:
            with pytest.raises(VideoEncodeError) as caught:
                FFmpegVideoSink._verify(sink, 4004)
            assert caught.value is failure
        else:
            assert FFmpegVideoSink._verify(sink, 4004) is result
        assert output.read_bytes() == original_bytes
    finally:
        output.unlink()  # model the sink's subsequent safe-write cleanup
    text = (tmp_path / "evidence/f8-3-clip_vfr-gap-libx265-10.txt").read_text()
    assert "original duration refusal" in text if fails else "verification passed" in text
    assert _record(text, "encode argv: ") == argv and forwarded == [argv]
    assert _record(text, "output boxes: ")["stts"][-1] == [1, 2002]
    assert _record(text, "written pts: ") == [0, 1001, 2002]


def test_timing_writer_on_real_vfr_x265_mp4(tmp_path, monkeypatch):
    """Exercise the recorder against actual muxed VFR bytes with external PATH tools only."""
    import clearwater.io.video as video

    tools = {name: shutil.which(name) for name in ("ffmpeg", "ffprobe")}
    if not all(tools.values()):
        pytest.skip("ffmpeg and ffprobe are not on the PATH (timing recorder control)")
    for path in tools.values():
        if Path(path).resolve().is_relative_to(ROOT / "bin"):
            pytest.skip("timing recorder control needs external PATH tools")
    source = tmp_path / "vfr.mp4"
    # The vid-vfr recipe's 1001/1001/2002 PTS pattern, small geometry, no audio.
    argv = [
        tools["ffmpeg"],
        "-nostdin",
        "-v",
        "error",
        "-y",
        "-f",
        "lavfi",
        "-i",
        "testsrc2=size=64x48:rate=30000/1001",
        "-frames:v",
        "30",
        "-vf",
        "settb=1/30000,setpts=1001*(4*floor(N/3)+mod(N\\,3))",
        "-fps_mode",
        "passthrough",
        "-c:v",
        "libx265",
        "-x265-params",
        "log-level=error:bframes=0",
        "-video_track_timescale",
        "30000",
        "-bsf:v",
        r"setts=duration=if(eq(N\,29)\,2\,DURATION)",
        str(source),
    ]
    done = subprocess.run(argv, capture_output=True, text=True, timeout=60)
    assert done.returncode == 0, done.stderr
    monkeypatch.setattr(video, "find_tool", lambda name: Path(tools[name]))
    module = _helpers()
    dest = tmp_path / "evidence.txt"
    module._write_vt_failure(
        source,
        dest,
        first=0,
        end=40040,
        time_base=Fraction(1, 30000),
        error="real x265 recorder control",
        source=source,
        recipe="vid-vfr PTS pattern (small x265 control)",
        written_pts=[1001 * (4 * (k // 3) + k % 3) for k in range(30)],
        frame_rate=Fraction(30000, 1001),
        encode_argv=argv,
    )
    text = dest.read_text()
    raw = _record(text, "output boxes: ")
    assert raw["sample_count"] == 30 and raw["stsz_sample_count"] == 30
    assert raw["media_timescale"] == 30000
    assert {delta for _, delta in raw["stts"]} >= {1001, 2002}
    assert raw["stts"][-1] == [1, 2002]
    assert "packet|" in text and "avg_frame_rate=" in text and "r_frame_rate=" in text
    assert "evidence read failed" not in text
    assert dest.stat().st_size < 200_000


@pytest.mark.parametrize("source_id", ["sample:vid-vfr", "clip:vfr-gap"])
@pytest.mark.parametrize("depth", [8, 10])
@pytest.mark.parametrize("encoder", ["libx265", "hevc_videotoolbox"])
def test_corpus_writes_evidence_on_success(tmp_path, monkeypatch, source_id, depth, encoder):
    """The corpus body must capture all EIGHT successful controls and watched VT encodes."""
    import clearwater.io.video as video
    import video_fidelity as vf
    from clearwater.io.video import FFmpegVideoSink, verify

    module = _helpers()
    source = _movie(tmp_path / "source.mp4")
    report = SimpleNamespace(frames_written=3, warnings=())
    # No native codec/decode here: supply finished, known boxes at the verify boundary.
    monkeypatch.setattr(FFmpegVideoSink, "_start", lambda sink, argv: None)
    monkeypatch.setattr(FFmpegVideoSink, "_verify", lambda sink, end: report)

    def encode(source, output, **kwargs):
        output.write_bytes(source.read_bytes())
        sink = SimpleNamespace(
            _out_path=output,
            _written=[0, 1001, 2002],
            _probe=SimpleNamespace(
                video=SimpleNamespace(
                    time_base=Fraction(1, 30000),
                    frame_rate=Fraction(22500, 1001),
                )
            ),
        )
        FFmpegVideoSink._start(sink, ["ffmpeg", "-i", "pipe:0", str(output)])
        return SimpleNamespace(report=FFmpegVideoSink._verify(sink, 4004))

    monkeypatch.setattr(vf, "encode_file", encode)
    monkeypatch.setattr(vf, "fidelity_record", lambda *a, **kw: {"bit_depth": depth})
    monkeypatch.setattr(module, "v4_failures", lambda *a, **kw: [])
    # This control tests capture wiring; the full raw contract is exercised below.
    monkeypatch.setattr(module, "_assert_vt_vfr_timing", lambda *a: None)
    monkeypatch.setattr(module, "_v4_source", lambda *a: source)
    monkeypatch.setattr(
        module, "_capability", lambda *a: SimpleNamespace(available=True, bit_depths=(8, 10))
    )
    monkeypatch.setattr(module, "REPO", tmp_path)
    monkeypatch.setattr(
        module,
        "_run",
        lambda argv: SimpleNamespace(returncode=0, stdout="packet|duration=2002", stderr=""),
    )
    monkeypatch.setattr(video, "find_tool", lambda name: Path("ffprobe-not-executed"))
    monkeypatch.setattr(
        video,
        "probe",
        lambda path: SimpleNamespace(
            video=SimpleNamespace(vfr=True, bit_depth=depth, time_base=Fraction(1, 30000))
        ),
    )
    monkeypatch.setattr(
        verify, "read_packet_table", lambda path: SimpleNamespace(video_pts=[0, 1001, 2002])
    )
    module.test_macos_videotoolbox_v4_corpus(
        source_id, encoder, depth, None, tmp_path, None, monkeypatch
    )
    filename = f"f8-3-{source_id.replace(':', '_')}-{encoder}-{depth}.txt"
    evidence = tmp_path / "work/evidence" / filename
    assert evidence.is_file(), "Passing corpus case did not capture evidence"
    text = evidence.read_text()
    assert "verification passed" in text
    assert _record(text, "source identity: ")["recipe"].startswith(source_id)
    assert _record(text, "written pts: ") == [0, 1001, 2002]


def test_interception_success_capture_failure_warns_and_preserves_report(tmp_path, monkeypatch):
    """Evidence I/O must warn once without failing a verified x265 control."""
    from clearwater.io.video import FFmpegVideoSink

    module = _helpers()
    report = object()
    case_id = "clip:vfr-gap-libx265-10"
    monkeypatch.setattr(FFmpegVideoSink, "_verify", lambda sink, end: report)

    def unwritable(*args, **kwargs):
        raise OSError("evidence disk full")

    monkeypatch.setattr(module, "_write_vt_failure", unwritable)
    module._capture_vt_failure(monkeypatch, case_id, tmp_path, source=tmp_path / "source.mp4")
    sink = SimpleNamespace(
        _out_path=tmp_path / "finished.mp4",
        _written=[0],
        _probe=SimpleNamespace(
            video=SimpleNamespace(time_base=Fraction(1, 30000), frame_rate=Fraction(30))
        ),
    )
    with pytest.warns(UserWarning) as caught:
        assert FFmpegVideoSink._verify(sink, 2002) is report
    assert len(caught) == 1
    assert case_id in str(caught[0].message)
    assert "evidence disk full" in str(caught[0].message)


def test_interception_diagnostic_failure_preserves_original_encode_error(tmp_path, monkeypatch):
    """An evidence I/O error must never turn a watched encode refusal into a different error."""
    from clearwater.io.video import FFmpegVideoSink, VideoEncodeError

    module = _helpers()
    failure = VideoEncodeError("verify_failed", "original edit-list refusal")

    def refuse(*args, **kwargs):
        raise failure

    def unwritable(*args, **kwargs):
        raise OSError("evidence destination unavailable")

    monkeypatch.setattr(FFmpegVideoSink, "_verify", refuse)
    monkeypatch.setattr(module, "_write_vt_failure", unwritable)
    module._capture_vt_failure(monkeypatch, "sample:vid-vfr-hevc_videotoolbox-8", tmp_path)
    sink = SimpleNamespace(
        _out_path=tmp_path / "finished.mp4",
        _written=[0],
        _probe=SimpleNamespace(video=SimpleNamespace(time_base=Fraction(1, 30000))),
    )
    with pytest.raises(VideoEncodeError) as caught:
        FFmpegVideoSink._verify(sink, 2002)
    assert caught.value is failure
    assert "evidence destination unavailable" in failure.__notes__[0]


def test_timing_writer_bounds_diagnostic_size_and_names_truncation(tmp_path, monkeypatch):
    """An unexpectedly large ffprobe tag cannot produce an unbounded evidence upload."""
    import clearwater.io.video as video

    module = _helpers()
    output = _movie(tmp_path / "output.mp4")
    monkeypatch.setattr(video, "find_tool", lambda name: Path("ffprobe-not-executed"))
    monkeypatch.setattr(
        module,
        "_run",
        lambda argv: SimpleNamespace(
            returncode=0,
            stdout="tag=" + "x" * 210_000,
            stderr="",
        ),
    )
    dest = tmp_path / "evidence.txt"
    module._write_vt_failure(
        output,
        dest,
        first=0,
        end=4004,
        time_base=Fraction(1, 30000),
        error="original refusal",
    )
    assert dest.stat().st_size <= 192 * 1024
    assert "EVIDENCE TRUNCATED" in dest.read_text()


def _vfr_boxes(tmp_path, source_id):
    """Build independently specified video boxes for the two corrected VT outputs."""
    import test_io_video_probe_boxes as b

    if source_id == "sample:vid-vfr":
        runs, media, movie, span, end = [(2, 1001), (1, 2002)] * 10, 30000, 240000, 40040, 320320
        edits = [(320320, 0, 1, 0)]
        pts = [1001 * (4 * (n // 3) + n % 3) for n in range(30)]
        sentinel = 40040
    else:
        runs, media, movie, span, end = (
            [(9, 512), (1, 3072), (45, 512)],
            15360,
            384000,
            30720,
            960000,
        )
        edits = [(192000, -1, 1, 0), (768000, 0, 1, 0)]
        pts = [7680 + 512 * n for n in range(60) if n not in range(10, 15)]
        sentinel = 38400
    stts = struct.pack(">II", 0, len(runs)) + b"".join(struct.pack(">II", *r) for r in runs)
    stbl = b.box("stts", stts) + b.box("stsz", struct.pack(">III", 0, 16, len(pts)))
    tkhd = b.box("tkhd", b"\0" * 20 + struct.pack(">I", end))
    mdhd = b.box("mdhd", b"\0" * 12 + struct.pack(">II", media, span))
    mvhd = b.box("mvhd", b"\0" * 12 + struct.pack(">II", movie, end))
    video = b.box(
        "trak",
        tkhd
        + b.box("edts", b.elst(edits))
        + b.box(
            "mdia",
            mdhd + b.hdlr("vide") + b.box("minf", b.box("stbl", stbl)),
        ),
    )
    path = tmp_path / "correct.mp4"
    path.write_bytes(b.FTYP + b.moov(mvhd, b.trak("soun", 48000), video))
    evidence = (
        "error: verification passed\nwritten pts: "
        + json.dumps(pts)
        + f"\nsentinel pts: {sentinel}\n"
    )
    return _helpers()._timing_boxes(path), pts, Fraction(1, media), evidence


@pytest.mark.parametrize("source_id", ["sample:vid-vfr", "clip:vfr-gap"])
def test_corrected_vt_raw_contract_reads_video_boxes(tmp_path, source_id):
    """The complete corrected raw contract accepts known boxes with audio preceding video."""
    _helpers()._assert_vt_vfr_timing(source_id, *_vfr_boxes(tmp_path, source_id))


@pytest.mark.parametrize("source_id", ["sample:vid-vfr", "clip:vfr-gap"])
@pytest.mark.parametrize(
    "damage",
    ["run9", "ctts", "clock", "mdhd", "edit", "tkhd", "mvhd", "pts", "sentinel", "written"],
)
def test_corrected_vt_contract_rejects_duration_or_written_timing_damage(
    tmp_path, source_id, damage
):
    """A green verifier alone cannot conceal a bad last sample, header, edit or written span."""
    raw, pts, tb, evidence = _vfr_boxes(tmp_path, source_id)
    if damage == "run9":
        count, _ = raw["stts"][-1]
        if count > 1:
            raw["stts"][-1] = (count - 1, 512)
            raw["stts"].append((1, 559))
        else:
            raw["stts"][-1] = (1, 1335)
    elif damage == "ctts":
        raw["ctts"] = {"version": 1, "entries": [(len(pts), 1)]}
    elif damage == "clock":
        raw["movie_timescale"] *= 2
    elif damage in {"mdhd", "tkhd", "mvhd"}:
        raw["durations"][damage]["ticks"] += 1
    elif damage == "edit":
        raw["elst"][-1]["segment_duration"] += 1
    elif damage == "pts":
        pts[-1] += 1
    elif damage == "sentinel":
        evidence = evidence.replace("sentinel pts: ", "sentinel pts: 1")
    else:
        evidence = evidence.replace("written pts: [", "written pts: [1,")
    with pytest.raises(AssertionError):
        _helpers()._assert_vt_vfr_timing(source_id, raw, pts, tb, evidence)


def test_expected_timing_uses_presentation_end_not_last_decode_packet():
    """A reordered greatest-PTS packet can precede the final packet in decode order."""
    expected = _helpers()._expected_timing([(110, 80, 30), (100, 90, 10)], Fraction(1, 100))
    assert expected == {
        "pts": [Fraction(1), Fraction(11, 10)],
        "first": Fraction(1),
        "end": Fraction(7, 5),
        "span": Fraction(2, 5),
    }


@pytest.mark.parametrize("packets", [[], [(0, 0, 0)], [(0, 0, -1)], [(0, 0, 1), (0, 1, 1)]])
def test_expected_timing_rejects_unusable_source_packets(packets):
    """Missing, nonpositive and duplicated source timing cannot supply an expected span."""
    with pytest.raises(AssertionError):
        _helpers()._expected_timing(packets, Fraction(1, 30))


def test_packet_timing_selects_video_and_retains_clock(tmp_path, monkeypatch):
    """An interleaved audio packet must never become the terminal-video assertion."""
    import clearwater.io.video as video

    module = _helpers()
    commands = []
    monkeypatch.setattr(video, "find_tool", lambda name: Path("ffprobe-not-executed"))

    def run(argv):
        commands.append(argv)
        return SimpleNamespace(
            returncode=0,
            stderr="",
            stdout=json.dumps(
                {
                    "streams": [{"time_base": "1/30000"}],
                    "packets": [{"pts": 38038, "dts": 36036, "duration": 2002}],
                }
            ),
        )

    monkeypatch.setattr(module, "_run", run)
    assert module._packet_timing(tmp_path / "in.mp4") == (
        [(38038, 36036, 2002)],
        Fraction(1, 30000),
    )
    assert commands[0][3:5] == ["-select_streams", "v:0"]


def _encoder_log(rows):
    """Representative single-video-stream debug_ts/benchmark log, with unrelated noise."""
    return "\n".join(
        f"bench: 1 user 2 sys 3 real {'flush' if flush else 'encode'}_video 0.0\n"
        "[aost] encoder -> type:audio pkt_pts:999 duration:1024\n"
        f"[vost] encoder -> type:video pkt_pts:{pts} pkt_pts_time:0 pkt_dts:0 "
        f"pkt_dts_time:0 duration:{duration} duration_time:0\n"
        "muxer <- type:video pkt_pts:999 duration:999"
        for pts, duration, flush in rows
    )


def test_encoder_boundary_parser_retains_zero_and_flush_association():
    """Only the encoder's pre-mux video durations count, with flush attached to each packet."""
    rows = [(0, 0, False), (2, 5, True), (7, 1, True), (8, 4, True)]
    assert _helpers()._encoder_packets(_encoder_log(rows)) == rows


def test_encoder_boundary_zero_duration_red_message():
    """Name the exact RED from the unpatched VT wrapper, without running it at this seat."""
    expected = [(0, 2), (2, 5), (7, 1), (8, 4)]
    log = _encoder_log([(pts, 0, True) for pts, _ in expected])
    with pytest.raises(AssertionError) as failure:
        _helpers()._assert_encoder_durations(log, expected)
    assert str(failure.value) == (
        "DR-163 encoder boundary: expected [(0, 2), (2, 5), (7, 1), (8, 4)]; "
        "got [(0, 0), (2, 0), (7, 0), (8, 0)]"
    )


@pytest.fixture(
    params=[(name, depth) for name in ("sample:vid-vfr", "clip:vfr-gap") for depth in (8, 10)]
)
def run9_duration_replay(request, tmp_path):
    """Replay the ruled DR-163 RED, distinguishing inferred pre-mux zeros from measured tails.

    CHARC 6688c6fd names run 9 as the RED of record. Zero-duration encoder lines
    model the unpatched wrapper; they were NOT captured at that boundary in run 9.
    The measured post-mux tails are f8-3-sample_vid-vfr-hevc_videotoolbox-{8,10}.txt:101
    and f8-3-clip_vfr-gap-hevc_videotoolbox-{8,10}.txt:159. Raw tables are :108/:167;
    written PTS and sentinel are :4-5. Fixture bytes are test-side, with no work/ dependency.
    """
    source_id, depth = request.param
    corrected, pts, tb, evidence = _vfr_boxes(tmp_path, source_id)
    runs = corrected["stts"]
    deltas = [d for n, d in runs for _ in range(n)]
    expected = list(zip(pts, deltas, strict=True))
    old = copy.deepcopy(corrected)
    if source_id == "sample:vid-vfr":
        measured_last = (38038, 38038, 1335)
        old["stts"][-1] = (1, 1335)
        media_ticks, movie_ticks = 39373, 314984
    else:
        measured_last = (37888, 37888, 559)
        old["stts"][-1] = (44, 512)
        old["stts"].append((1, 559))
        media_ticks, movie_ticks = 30767, 961175
    old["durations"]["mdhd"]["ticks"] = media_ticks
    old["durations"]["tkhd"]["ticks"] = movie_ticks
    old["durations"]["mvhd"]["ticks"] = movie_ticks
    old["elst"][-1]["segment_duration"] = movie_ticks - (
        192000 if source_id == "clip:vfr-gap" else 0
    )
    zero_packets = [(p, 0, n == len(pts) - 1) for n, p in enumerate(pts)]
    log = _encoder_log(zero_packets) + (
        f"\nmuxer <- type:video pkt_pts:{measured_last[0]} "
        f"pkt_dts:{measured_last[1]} duration:{measured_last[2]}"
    )
    return source_id, depth, old, corrected, pts, tb, evidence, expected, zero_packets, log


def test_run9_replay_is_red_before_mux_guess_and_green_with_restored_durations(
    run9_duration_replay,
):
    """The four recorded terminal defects and ruled zero-duration replay fail exact assertions."""
    source_id, depth, old, corrected, pts, tb, evidence, expected, zeros, log = run9_duration_replay
    assert depth in (8, 10)
    module = _helpers()
    assert module._encoder_packets(log) == zeros  # post-mux 1335/559 must not be used
    with pytest.raises(AssertionError) as failure:
        module._assert_encoder_durations(log, expected)
    assert str(failure.value) == (
        f"DR-163 encoder boundary: expected {expected}; got {[(p, 0) for p, _ in expected]}"
    )
    with pytest.raises(
        AssertionError, match="DR-163: raw video stts differs from source durations"
    ):
        module._assert_vt_vfr_timing(source_id, old, pts, tb, evidence)
    module._assert_vt_vfr_timing(source_id, corrected, pts, tb, evidence)
    module._assert_encoder_durations(
        _encoder_log([(p, d, n == len(expected) - 1) for n, (p, d) in enumerate(expected)]),
        expected,
    )


def test_encoder_boundary_requires_positive_associated_durations_and_flush():
    """Zero, swapped and missing flush output are distinct failures of the boundary proof."""
    module = _helpers()
    expected = [(0, 2), (2, 5), (7, 1), (8, 4)]
    module._assert_encoder_durations(_encoder_log([(p, d, True) for p, d in expected]), expected)
    for rows in (
        [(0, 5, True), (2, 2, True), (7, 1, True), (8, 4, True)],
        [(p, d, False) for p, d in expected],
        [(p, d, True) for p, d in expected[:-1]],
    ):
        with pytest.raises(AssertionError):
            module._assert_encoder_durations(_encoder_log(rows), expected)


@pytest.mark.parametrize(
    "log",
    [
        "",
        "encoder -> type:video pkt_pts:0 duration:1",
        "bench: 1 real flush_video 0.0\nencoder -> type:video pkt_pts:NOPTS duration:1",
    ],
)
def test_encoder_boundary_parser_fails_closed_on_absent_or_malformed_lines(log):
    """No duration can be inferred from a mux line, a missing action or absent PTS."""
    with pytest.raises(AssertionError):
        _helpers()._encoder_packets(log)


def test_long_early_interval_rejects_last_only_endpoint_repair():
    """An earlier guessed packet end can exceed the real end after the last is fixed."""
    module = _helpers()
    packets = [(p, p, d) for p, d in [(0, 100), (100, 1), (101, 1), (102, 1), (103, 1), (104, 1)]]
    expected = module._expected_timing(packets, Fraction(1, 30))
    assert expected["end"] == Fraction(7, 2)
    guessed = expected["span"] / 6
    endpoint = max(
        p * Fraction(1, 30) + (Fraction(d, 30) if p == 104 else guessed) for p, _, d in packets
    )
    assert endpoint == Fraction(241, 60) > expected["end"]
    raw = {
        "media_timescale": 60,
        "movie_timescale": 60,
        "stts": [(1, 200), (5, 2)],
        "sample_count": 6,
        "stsz_sample_count": 6,
        "durations": {h: {"ticks": 210} for h in ("mdhd", "tkhd", "mvhd")},
        "elst": [{"segment_duration": 210, "media_time": 0, "rate": "1"}],
    }
    module._assert_timing_span(raw, expected)
    broken = copy.deepcopy(raw)
    broken["elst"][0]["segment_duration"] = 241
    broken["durations"]["tkhd"]["ticks"] = broken["durations"]["mvhd"]["ticks"] = 241
    with pytest.raises(AssertionError):
        module._assert_timing_span(broken, expected)


@pytest.mark.parametrize("name", ["regular-final", "early-long"])
@pytest.mark.parametrize("depth", [8, 10])
def test_new_duration_fixtures_with_real_x265_control(
    tmp_path, tmp_path_factory, monkeypatch, name, depth, ffmpeg_tools
):
    """Run new test-side designs and their presentation checks with external x265 on Windows."""
    module = _helpers()
    monkeypatch.setattr(
        module, "_capability", lambda encoder: SimpleNamespace(available=True, bit_depths=(8, 10))
    )
    monkeypatch.setattr(module, "REPO", tmp_path)
    if name == "regular-final":
        with pytest.raises(
            module._DR164DurationMismatchError, match="V4 video stream duration differs"
        ):
            module.test_macos_duration_regression(
                name, "libx265", depth, tmp_path, tmp_path_factory, monkeypatch
            )
    else:
        module.test_macos_duration_regression(
            name, "libx265", depth, tmp_path, tmp_path_factory, monkeypatch
        )
    evidence = tmp_path / "work/evidence" / f"f8-3-clip_{name}-libx265-{depth}.txt"
    text = evidence.read_text(encoding="utf-8")
    assert text.startswith("error: verification passed\n")
    record = _record(text, "V4 record: ")
    failures = _record(text, "V4 failures: ")
    if name == "regular-final":
        assert len(failures) == 1
        assert [
            i["name"]
            for i in record["items"]
            if i["class"] == "MANDATORY" and i["status"] == "DIFFERENT"
        ] == ["video stream duration"]
        assert _record(text, "source boxes: ")["stts"] == [[29, 512], [1, 2048]]
        assert _record(text, "output boxes: ")["stts"] == [[30, 512]]
        assert _record(text, "output boxes: ")["durations"]["mdhd"]["ticks"] == 15360
    else:
        assert failures == []


@pytest.mark.parametrize(
    "damage", ["none", "extra-item", "extra-failure", "wrong-message", "unwatched", "green"]
)
def test_dr164_exception_only_covers_the_watched_duration_mismatch(damage):
    """An unrelated failure must fail normally; only the named V4 duration error may xfail."""
    module = _helpers()
    record = {
        "items": [
            {
                "name": "video stream duration",
                "class": "MANDATORY",
                "status": "DIFFERENT",
                "source": "1.100000 (11/10)",
                "output": "1.000000 (1/1)",
            }
        ]
    }
    failures = ["V4: video stream duration"]
    if damage == "extra-item":
        record["items"].append({"name": "video pts", "class": "MANDATORY", "status": "DIFFERENT"})
    elif damage == "extra-failure":
        failures.append("V4: the frame count differs from the frames written")
    elif damage == "wrong-message":
        failures = ["V4: the frame count differs from the frames written"]
    elif damage == "green":
        module._assert_duration_v4(record, [], watched=True)
        return
    if damage == "none":
        with pytest.raises(module._DR164DurationMismatchError) as caught:
            module._assert_duration_v4(record, failures, watched=True)
        assert str(caught.value) == (
            "DR-164: V4 video stream duration differs: "
            "source=1.100000 (11/10); output=1.000000 (1/1)"
        )
    else:
        with pytest.raises(AssertionError) as caught:
            module._assert_duration_v4(record, failures, watched=damage != "unwatched")
        assert not isinstance(caught.value, module._DR164DurationMismatchError)
