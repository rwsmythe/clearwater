"""Portable controls for the test-only DR-163 timing recorder (no native/GPU encodes)."""

from __future__ import annotations

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
def test_corpus_x265_controls_write_evidence_on_success(tmp_path, monkeypatch, source_id, depth):
    """The actual corpus body must install capture for all four passing software controls."""
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
        lambda path: SimpleNamespace(video=SimpleNamespace(vfr=True, bit_depth=depth)),
    )
    monkeypatch.setattr(
        verify, "read_packet_table", lambda path: SimpleNamespace(video_pts=[0, 1001, 2002])
    )
    module.test_macos_videotoolbox_v4_corpus(
        source_id, "libx265", depth, None, tmp_path, None, monkeypatch
    )
    filename = f"f8-3-{source_id.replace(':', '_')}-libx265-{depth}.txt"
    evidence = tmp_path / "work/evidence" / filename
    assert evidence.is_file(), "Passing x265 corpus control did not capture evidence"
    text = evidence.read_text()
    assert "verification passed" in text
    assert _record(text, "source identity: ")["recipe"].startswith(source_id)
    assert _record(text, "written pts: ") == [0, 1001, 2002]


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
