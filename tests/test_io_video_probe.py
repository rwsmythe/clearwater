"""Tests of the video probe (WP3.7): every WP2.3 video sample against its manifest facts.

Fields are measured from the files by ``clearwater.io.video.probe`` and compared with the
manifest's recorded facts (which the fixtures' own tests measured independently with ffprobe).
Tests that need a changed ffprobe answer (missing tags, odd rotations, no frame count) edit the
real JSON of a real sample through ``_Spy`` rather than inventing a whole answer.
"""

from __future__ import annotations

import importlib
import json
import logging
import shutil
import subprocess
from collections.abc import Callable, Sequence
from fractions import Fraction
from pathlib import Path
from typing import Any

import pytest

from clearwater.io.video import VideoProbeError, filter_inputs, find_tool, probe
from clearwater.io.video.boxes import MovieBoxes, RawEdit

# The package attribute ``probe`` is the function (IF-5 name), which shadows the submodule.
probe_module = importlib.import_module("clearwater.io.video.probe")

VIDEO_IDS = [
    "vid-hevc8-bt709-full",
    "vid-hevc10",
    "vid-hlg",
    "vid-pq",
    "vid-untagged",
    "vid-truncated",
    "vid-vfr",
    "vid-rotated",
]
INTACT_IDS = [i for i in VIDEO_IDS if i != "vid-truncated"]

Sample = Callable[[str], Path]
Entry = Callable[[str], dict[str, Any]]


class _Spy:
    """Wraps ``probe._run_ffprobe``: records the argument lists and can rewrite the answers."""

    def __init__(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self.calls: list[list[str]] = []
        self.edit_streams: Callable[[dict[str, Any]], None] | None = None
        self.edit_stderr: Callable[[str], str] | None = None
        self.edit_packets: Callable[[list[dict[str, Any]]], None] | None = None
        self._real = probe_module._run_ffprobe
        monkeypatch.setattr(probe_module, "_run_ffprobe", self)

    def __call__(self, args: Sequence[str]) -> tuple[int, str, str]:
        self.calls.append(list(args))
        status, out, err = self._real(args)
        if any(a.startswith("format=") for a in args):
            if self.edit_streams is not None:
                data = json.loads(out)
                self.edit_streams(data)
                out = json.dumps(data)
        elif "packet=pts,duration,flags" in args:
            if self.edit_stderr is not None:
                err = self.edit_stderr(err)
            if self.edit_packets is not None:
                data = json.loads(out)
                self.edit_packets(data["packets"])
                out = json.dumps(data)
        return status, out, err

    def video(self, edit: Callable[[dict[str, Any]], None]) -> None:
        """Rewrite the first video stream of the stream answer."""

        def apply(data: dict[str, Any]) -> None:
            edit(next(s for s in data["streams"] if s["codec_type"] == "video"))

        self.edit_streams = apply


def _fraction(text: str) -> Fraction:
    return Fraction(text)


@pytest.mark.parametrize("sample_id", VIDEO_IDS)
def test_every_video_sample_probes_to_its_manifest_facts(
    sample_id: str, sample: Sample, sample_entry: Entry
) -> None:
    entry = sample_entry(sample_id)
    expected = entry["expect"]["probe"]
    facts = entry["facts"]
    result = probe(sample(sample_id))
    video = result.video
    want = expected["video"]
    assert result.container == expected["container"]
    assert video.codec == want["codec"]
    assert (video.width, video.height) == (want["width"], want["height"])
    assert video.bit_depth == want["bit_depth"]
    assert video.pix_fmt == facts["video"]["pix_fmt"]
    assert video.frame_rate == _fraction(want["frame_rate"])
    assert video.time_base == _fraction(want["time_base"])
    assert video.nb_frames == want["nb_frames"]
    assert video.rotation == want["rotation"]
    assert video.vfr is want["vfr"] is facts["pts"]["variable"]
    assert result.duration_s == Fraction(
        facts["pts"]["track_duration_ticks"], facts["pts"]["ticks_per_second"]
    )
    assert result.start_offset_s == 0
    assert [(a.codec, a.sample_rate, a.channels) for a in result.audio] == [
        (a["codec"], a["sample_rate"], a["channels"]) for a in expected["audio"]
    ]
    assert all(a.start_s == 0 for a in result.audio)
    assert len(result.data) == len(expected["data"]) == 0
    assert result.gopro is None
    assert [(f.kind, f.severity) for f in result.faults] == [
        (f["kind"], f["severity"]) for f in entry["expect"]["faults"]
    ]
    assert all(f.message and f.message.isascii() for f in result.faults)
    color = video.color
    if "color" in want:
        assert (color.primaries, color.transfer, color.matrix) == (
            want["color"]["primaries"],
            want["color"]["transfer"],
            want["color"]["matrix"],
        )
        assert (color.range, color.bit_depth, color.assumed) == (
            want["color"]["range"],
            want["color"]["bit_depth"],
            want["color"]["assumed"],
        )
    else:
        # HLG and PQ: refused, never decoded; the transfer is not claimed (ruling 7.6).
        assert (color.transfer, color.assumed) == ("unknown", False)


def test_every_time_is_an_exact_fraction(sample: Sample) -> None:
    result = probe(sample("vid-vfr"))
    for value in (result.duration_s, result.start_offset_s, result.video.frame_rate):
        assert type(value) is Fraction
    assert result.duration_s == Fraction(40040, 30000)
    assert result.video.frame_rate == Fraction(22500, 1001)
    assert all(type(a.start_s) is Fraction for a in result.audio)


def test_the_edit_list_of_a_sample_is_reported_as_written(sample: Sample) -> None:
    result = probe(sample("vid-hevc8-bt709-full"))
    assert len(result.edit_list) == 1
    edit = result.edit_list[0]
    assert (edit.media_time_s, edit.media_rate) == (0, 1)
    assert edit.segment_duration_s == Fraction(45045, 30000)


@pytest.mark.parametrize("sample_id", INTACT_IDS)
def test_no_intact_sample_is_reported_truncated(sample_id: str, sample: Sample) -> None:
    kinds = {f.kind for f in probe(sample(sample_id)).faults}
    assert not kinds & {"truncated", "unreadable_tail"}


def test_the_truncated_sample_is_truncated_and_nothing_else(sample: Sample) -> None:
    result = probe(sample("vid-truncated"))
    assert [f.kind for f in result.faults] == ["truncated"]
    assert "24 of 45" in result.faults[0].message


def test_truncation_is_found_without_a_frame_count(
    sample: Sample, monkeypatch: pytest.MonkeyPatch
) -> None:
    spy = _Spy(monkeypatch)
    spy.video(lambda s: s.pop("nb_frames"))
    result = probe(sample("vid-truncated"))
    assert result.video.nb_frames is None
    assert [f.kind for f in result.faults] == ["truncated"]


def _corrupt_last_packet(source: Path, target: Path) -> Path:
    """Copy a clip with the payload of its last video packet overwritten (container intact)."""
    packets = json.loads(
        subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-of",
                "json",
                "-select_streams",
                "v:0",
                "-show_entries",
                "packet=pos,size",
                str(source),
            ],
            capture_output=True,
            check=True,
        ).stdout
    )["packets"]
    data = bytearray(source.read_bytes())
    pos, size = int(packets[-1]["pos"]), int(packets[-1]["size"])
    data[pos + 8 : pos + size] = b"\xa5" * (size - 8)
    target.write_bytes(data)
    return target


def test_a_damaged_last_packet_is_an_unreadable_tail(sample: Sample, tmp_path: Path) -> None:
    source = sample("vid-hevc8-bt709-full")
    assert not probe(source).faults  # the same file undamaged is clean: the check distinguishes
    damaged = _corrupt_last_packet(source, tmp_path / "damaged.mp4")
    assert [f.kind for f in probe(damaged).faults] == ["unreadable_tail"]


def test_the_tail_decode_starts_at_the_last_keyframe(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    if shutil.which("ffmpeg") is None:
        pytest.skip("ffmpeg is not on the PATH")
    clip = tmp_path / "gop.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-f",
            "lavfi",
            "-i",
            "testsrc=size=64x64:rate=30",
            "-frames:v",
            "60",
            "-c:v",
            "libx264",
            "-g",
            "20",
            "-bf",
            "0",
            "-pix_fmt",
            "yuv420p",
            str(clip),
        ],
        check=True,
    )
    spy = _Spy(monkeypatch)
    result = probe(clip)
    assert not [f for f in result.faults if f.kind in ("truncated", "unreadable_tail")]
    tail = [c for c in spy.calls if "-read_intervals" in c]
    assert len(tail) == 1
    start = tail[0][tail[0].index("-read_intervals") + 1]
    # Keyframes at frames 0, 20 and 40 of 30 fps: the last is 40/30 s. The interval has an
    # explicit end because an open-ended one drops frames at random on ffprobe 9.0.2.
    assert start == "1.333334%+86400"


def test_no_command_decodes_everything_or_reads_the_data_streams(
    sample: Sample, monkeypatch: pytest.MonkeyPatch
) -> None:
    spy = _Spy(monkeypatch)
    probe(sample("vid-hevc8-bt709-full"))
    assert len(spy.calls) == 3
    for call in spy.calls:
        joined = " ".join(call)
        assert "-show_data" not in joined
        assert "-show_frames" not in joined
        assert "-count_frames" not in joined
        assert "-show_packets" not in joined
    assert all("-select_streams" in c and "v:0" in c for c in spy.calls[1:])
    assert "tags" not in spy.calls[0][spy.calls[0].index("-show_entries") + 1]


# --- colour (D54) -------------------------------------------------------------------------------


def _colour_of(
    sample: Sample, monkeypatch: pytest.MonkeyPatch, sample_id: str, edit: Callable[..., None]
) -> Any:
    spy = _Spy(monkeypatch)
    spy.video(edit)
    return probe(sample(sample_id))


def _drop(*keys: str) -> Callable[[dict[str, Any]], None]:
    def edit(stream: dict[str, Any]) -> None:
        for key in keys:
            stream.pop(key, None)

    return edit


def test_untagged_yuvj_is_full_range_and_raises_no_missing_tags(
    sample: Sample, monkeypatch: pytest.MonkeyPatch
) -> None:
    result = _colour_of(sample, monkeypatch, "vid-rotated", _drop("color_range"))
    assert result.video.pix_fmt == "yuvj420p"
    assert (result.video.color.range, result.video.color.assumed) == ("full", False)
    assert not result.faults


def test_untagged_range_without_a_j_format_defaults_to_limited_and_warns_once(
    sample: Sample, monkeypatch: pytest.MonkeyPatch
) -> None:
    result = _colour_of(sample, monkeypatch, "vid-untagged", _drop("color_range"))
    color = result.video.color
    assert (color.primaries, color.transfer, color.matrix, color.range) == (
        "bt709",
        "bt709",
        "bt709",
        "limited",
    )
    assert color.assumed
    (fault,) = result.faults
    assert (fault.kind, fault.severity) == ("missing_tags", "warn")
    for name in ("primaries", "transfer", "matrix", "range"):
        assert name in fault.message


def test_each_field_defaults_on_its_own(sample: Sample, monkeypatch: pytest.MonkeyPatch) -> None:
    result = _colour_of(sample, monkeypatch, "vid-hevc8-bt709-full", _drop("color_primaries"))
    assert result.video.color.assumed
    (fault,) = result.faults
    assert "primaries" in fault.message and "transfer" not in fault.message
    assert result.video.color.range == "full"  # the tagged range is kept


@pytest.mark.parametrize(
    ("key", "value", "field", "expected"),
    [
        ("color_primaries", "bt2020", "primaries", "bt709"),
        ("color_primaries", "smpte170m", "primaries", "bt709"),
        ("color_primaries", "bt470bg", "primaries", "bt709"),
        ("color_transfer", "linear", "transfer", "bt709"),
        ("color_space", "bt2020nc", "matrix", "bt709"),
    ],
)
def test_an_unexpected_tag_takes_the_d54_value_and_is_named(
    key: str,
    value: str,
    field: str,
    expected: str,
    sample: Sample,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def edit(stream: dict[str, Any]) -> None:
        stream[key] = value

    result = _colour_of(sample, monkeypatch, "vid-hevc8-bt709-full", edit)
    assert getattr(result.video.color, field) == expected
    assert result.video.color.assumed
    (fault,) = result.faults
    assert fault.kind == "missing_tags" and f"{field} {value} unexpected" in fault.message


@pytest.mark.parametrize(
    ("key", "value", "field", "expected"),
    [
        ("color_primaries", "smpte432", "primaries", "display-p3"),
        ("color_transfer", "iec61966-2-1", "transfer", "srgb"),
        ("color_space", "smpte170m", "matrix", "bt601"),
        ("color_space", "bt470bg", "matrix", "bt601"),
        ("color_space", "gbr", "matrix", "identity"),
        ("color_range", "tv", "range", "limited"),
    ],
)
def test_recognised_tags_map_without_a_warning(
    key: str,
    value: str,
    field: str,
    expected: str,
    sample: Sample,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def edit(stream: dict[str, Any]) -> None:
        stream[key] = value

    result = _colour_of(sample, monkeypatch, "vid-hevc8-bt709-full", edit)
    assert getattr(result.video.color, field) == expected
    assert not result.video.color.assumed and not result.faults


@pytest.mark.parametrize("sample_id", ["vid-hlg", "vid-pq"])
def test_hdr_is_refused_with_the_other_tags_kept_where_the_vocabulary_has_them(
    sample_id: str, sample: Sample
) -> None:
    result = probe(sample(sample_id))
    (fault,) = result.faults
    assert (fault.kind, fault.severity) == (sample_id[4:], "refuse")
    color = result.video.color
    assert (color.primaries, color.matrix, color.transfer) == ("unknown", "unknown", "unknown")
    assert (color.range, color.bit_depth, color.assumed) == ("limited", 10, False)


# --- rotation (AD-20) ---------------------------------------------------------------------------


def _with_rotation(angle: object, matrix: str | None = None) -> Callable[[dict[str, Any]], None]:
    def edit(stream: dict[str, Any]) -> None:
        item: dict[str, Any] = {"rotation": angle}
        if matrix is not None:
            item["displaymatrix"] = matrix
        stream["side_data_list"] = [item]

    return edit


def _matrix(a: int, b: int, c: int, d: int) -> str:
    return f"\n00000000: {a:12d} {b:12d} 0\n00000001: {c:12d} {d:12d} 0\n00000002: 0 0 1073741824\n"


@pytest.mark.parametrize(
    ("angle", "expected"), [(0, 0), (90, 90), (180, 180), (270, 270), (-90, 270), (-180, 180)]
)
def test_rotation_is_normalised_counter_clockwise_positive(
    angle: int, expected: int, sample: Sample, monkeypatch: pytest.MonkeyPatch
) -> None:
    result = _colour_of(sample, monkeypatch, "vid-hevc8-bt709-full", _with_rotation(angle))
    assert result.video.rotation == expected


def test_the_real_rotated_sample_reads_ninety(sample: Sample) -> None:
    assert probe(sample("vid-rotated")).video.rotation == 90


@pytest.mark.parametrize("angle", [45, -30, 89.5])
def test_a_rotation_that_is_not_a_multiple_of_90_is_refused(
    angle: float, sample: Sample, monkeypatch: pytest.MonkeyPatch
) -> None:
    spy = _Spy(monkeypatch)
    spy.video(_with_rotation(angle))
    with pytest.raises(VideoProbeError) as caught:
        probe(sample("vid-hevc8-bt709-full"))
    assert caught.value.kind == "unsupported"
    assert str(angle) in str(caught.value)


def test_a_mirrored_matrix_is_refused(sample: Sample, monkeypatch: pytest.MonkeyPatch) -> None:
    spy = _Spy(monkeypatch)
    spy.video(_with_rotation(0, _matrix(-65536, 0, 0, 65536)))
    with pytest.raises(VideoProbeError) as caught:
        probe(sample("vid-hevc8-bt709-full"))
    assert caught.value.kind == "unsupported" and "mirrored" in str(caught.value)


def test_a_plain_rotation_matrix_is_not_mirrored(
    sample: Sample, monkeypatch: pytest.MonkeyPatch
) -> None:
    result = _colour_of(
        sample,
        monkeypatch,
        "vid-hevc8-bt709-full",
        _with_rotation(90, _matrix(0, -65536, 65536, 0)),
    )
    assert result.video.rotation == 90


# --- refusals and tools -------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("edit", "needle"),
    [
        (lambda s: s.update(codec_name="vp9"), "vp9"),
        (lambda s: s.update(pix_fmt="yuv420p12le"), "yuv420p12le"),
        (lambda s: s.update(pix_fmt="rgb24"), "rgb24"),
    ],
)
def test_other_codecs_and_depths_are_unsupported(
    edit: Callable[[dict[str, Any]], Any],
    needle: str,
    sample: Sample,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spy = _Spy(monkeypatch)
    spy.video(edit)
    with pytest.raises(VideoProbeError) as caught:
        probe(sample("vid-hevc10"))
    assert caught.value.kind == "unsupported" and needle in str(caught.value)


def test_another_container_is_unsupported(sample: Sample, monkeypatch: pytest.MonkeyPatch) -> None:
    spy = _Spy(monkeypatch)

    def edit(data: dict[str, Any]) -> None:
        data["format"]["format_name"] = "matroska,webm"

    spy.edit_streams = edit
    with pytest.raises(VideoProbeError) as caught:
        probe(sample("vid-hevc10"))
    assert caught.value.kind == "unsupported"


def test_a_file_with_no_video_stream_is_unsupported(
    sample: Sample, monkeypatch: pytest.MonkeyPatch
) -> None:
    spy = _Spy(monkeypatch)
    spy.edit_streams = lambda data: data.update(streams=[])
    with pytest.raises(VideoProbeError) as caught:
        probe(sample("vid-hevc10"))
    assert caught.value.kind == "unsupported"


def test_unreadable_files_are_refused_with_a_clear_message(tmp_path: Path) -> None:
    garbage = tmp_path / "noise.mp4"
    garbage.write_bytes(b"this is not a video" * 50)
    empty = tmp_path / "empty.mp4"
    empty.write_bytes(b"")
    for path in (garbage, empty, tmp_path / "missing.mp4"):
        with pytest.raises(VideoProbeError) as caught:
            probe(path)
        assert caught.value.kind == "unreadable" and path.name in str(caught.value)


def test_a_missing_ffprobe_is_a_clear_error(
    sample: Sample, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(shutil, "which", lambda name: None)
    with pytest.raises(VideoProbeError) as caught:
        probe(sample("vid-hevc10"))
    assert caught.value.kind == "missing_tool" and "ffprobe" in str(caught.value)
    with pytest.raises(VideoProbeError):
        find_tool("ffmpeg")


def test_the_locator_finds_the_tools() -> None:
    assert find_tool("ffprobe").name.lower().startswith("ffprobe")


# --- sidecars (D83) -----------------------------------------------------------------------------


def test_sidecars_are_excluded_before_probing(
    sample: Sample, sample_ids: Callable[..., list[str]], sample_entry: Entry
) -> None:
    ids = [i for i in sample_ids("files") if i.startswith("gopro-")]
    assert len(ids) == 8
    paths = [sample(i) for i in ids]
    selection = filter_inputs(paths)
    for sample_id, path in zip(ids, paths, strict=True):
        facts = sample_entry(sample_id)["facts"]
        assert (path in selection.inputs) is (not facts["sidecar"])
    assert [p for p, _ in selection.excluded] == [p for p in paths if p not in selection.inputs]
    assert {p.suffix for p, _ in selection.excluded} == {".LRV", ".THM", ".lrv", ".thm"}
    for _, fault in selection.excluded:
        assert (fault.kind, fault.severity) == ("sidecar", "exclude")
        assert fault.message.isascii()
    assert list(selection.inputs) == [p for p in paths if p.suffix.lower() == ".mp4"]


def test_probe_refuses_a_sidecar_without_running_ffprobe(
    sample: Sample, monkeypatch: pytest.MonkeyPatch
) -> None:
    spy = _Spy(monkeypatch)
    with pytest.raises(VideoProbeError) as caught:
        probe(sample("gopro-upper-gl010001-lrv"))
    assert caught.value.kind == "sidecar"
    assert spy.calls == []


# --- GoPro settings through the probe (AD-16) ---------------------------------------------------


def _atom(*items: tuple[str, str, bytes]) -> bytes:
    """KLV bytes of ``(key, type, value)`` items: size 1, repeat = length, padded to four."""
    out = b""
    for key, kind, value in items:
        out += key.encode() + kind.encode() + bytes([1]) + len(value).to_bytes(2, "big")
        out += value + b"\0" * (-len(value) % 4)
    return out


def _with_gpmf(monkeypatch: pytest.MonkeyPatch, payload: bytes | None) -> None:
    monkeypatch.setattr(
        probe_module,
        "read_movie_boxes",
        lambda path: MovieBoxes(1000, 30000, (RawEdit(1502, 0, Fraction(1)),), payload),
    )


def test_settings_populate_gopro_and_a_natural_clip_has_no_gp_log(
    sample: Sample, monkeypatch: pytest.MonkeyPatch
) -> None:
    _with_gpmf(
        monkeypatch,
        _atom(("FMWR", "c", b"H24.01"), ("PRTN", "c", b"Y"), ("PTCL", "c", b"NATURAL")),
    )
    result = probe(sample("vid-hevc8-bt709-full"))
    assert result.gopro is not None
    assert (result.gopro.firmware, result.gopro.protune, result.gopro.color_profile) == (
        "H24.01",
        True,
        "NATURAL",
    )
    assert not result.faults
    assert result.edit_list[0].segment_duration_s == Fraction(1502, 1000)


@pytest.mark.parametrize("profile", [b"FLAT", b"VIBRANT", b"natural"])
def test_the_known_colour_profiles_do_not_warn(
    profile: bytes, sample: Sample, monkeypatch: pytest.MonkeyPatch
) -> None:
    _with_gpmf(monkeypatch, _atom(("PRTN", "c", b"Y"), ("PTCL", "c", profile)))
    assert not probe(sample("vid-hevc8-bt709-full")).faults


def test_another_colour_profile_is_treated_as_log(
    sample: Sample, monkeypatch: pytest.MonkeyPatch
) -> None:
    _with_gpmf(monkeypatch, _atom(("PRTN", "c", b"Y"), ("PTCL", "c", b"FLAT_LOG")))
    (fault,) = probe(sample("vid-hevc8-bt709-full")).faults
    assert (fault.kind, fault.severity) == ("gp_log", "warn")
    assert "FLAT_LOG" in fault.message and fault.message.isascii()


def test_protune_without_a_transfer_tag_is_log_and_missing_tags(
    sample: Sample, monkeypatch: pytest.MonkeyPatch
) -> None:
    _with_gpmf(monkeypatch, _atom(("PRTN", "c", b"Y"), ("PTCL", "c", b"NATURAL")))
    spy = _Spy(monkeypatch)
    spy.video(_drop("color_transfer"))
    result = probe(sample("vid-hevc8-bt709-full"))
    assert [f.kind for f in result.faults] == ["missing_tags", "gp_log"]


def test_no_transfer_tag_without_protune_is_only_missing_tags(
    sample: Sample, monkeypatch: pytest.MonkeyPatch
) -> None:
    _with_gpmf(monkeypatch, _atom(("PRTN", "c", b"N")))
    spy = _Spy(monkeypatch)
    spy.video(_drop("color_transfer"))
    assert [f.kind for f in probe(sample("vid-hevc8-bt709-full")).faults] == ["missing_tags"]


def test_a_malformed_settings_atom_gives_no_gopro_and_one_structural_warning(
    sample: Sample, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    secret = b"SERIAL-C3455"
    _with_gpmf(monkeypatch, b"FMWRc\x01\x00\xff" + secret)  # declares 255 bytes, has 12
    with caplog.at_level(logging.WARNING, logger="clearwater.io.video"):
        result = probe(sample("vid-hevc8-bt709-full"))
    assert result.gopro is None and not result.faults
    (record,) = caplog.records
    assert record.name.startswith("clearwater.io.video")
    assert "item length past atom end" in record.getMessage()
    assert secret.decode() not in record.getMessage()


def test_a_file_without_the_settings_atom_has_no_gopro(
    sample: Sample, monkeypatch: pytest.MonkeyPatch
) -> None:
    _with_gpmf(monkeypatch, None)
    assert probe(sample("vid-hevc8-bt709-full")).gopro is None


def test_unreadable_movie_boxes_do_not_fail_the_probe(
    sample: Sample, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    from clearwater.io.video.boxes import BoxError

    def fail(path: Path) -> MovieBoxes:
        raise BoxError("box size is inconsistent with its parent")

    monkeypatch.setattr(probe_module, "read_movie_boxes", fail)
    with caplog.at_level(logging.WARNING, logger="clearwater.io.video"):
        result = probe(sample("vid-hevc8-bt709-full"))
    assert result.edit_list == () and result.gopro is None
    assert len(caplog.records) == 1


# --- VFR on constructed packets (D95) -----------------------------------------------------------


@pytest.mark.parametrize(
    ("pts", "vfr"),
    [
        ([0, 1001, 2002, 3003], False),
        ([0, 2002, 1001, 3003], False),  # B-frame reordered, steps equal once sorted
        ([0, 1001, 3003], True),
        ([0], False),
        ([], False),
    ],
)
def test_vfr_is_decided_on_sorted_presentation_times(pts: list[int], vfr: bool) -> None:
    assert probe_module._is_variable(pts) is vfr


# --- round 1 remediation ------------------------------------------------------------------------


def test_the_container_duration_is_the_longest_stream_and_exact(
    sample: Sample, monkeypatch: pytest.MonkeyPatch
) -> None:
    plain = probe(sample("vid-hevc8-bt709-full"))
    video_s = Fraction(45045, 30000)
    assert plain.duration_s == video_s  # equal on the video-only samples (audio is shorter)
    spy = _Spy(monkeypatch)

    def longer_audio(data: dict[str, Any]) -> None:
        audio = next(s for s in data["streams"] if s["codec_type"] == "audio")
        audio["duration_ts"] = 96000  # two seconds at 1/48000

    spy.edit_streams = longer_audio
    longer = probe(sample("vid-hevc8-bt709-full"))
    assert longer.duration_s == 2 and type(longer.duration_s) is Fraction
    assert video_s <= longer.duration_s  # the video track is never longer than the container


def test_the_duration_fallback_uses_the_packet_with_the_highest_pts(
    sample: Sample, monkeypatch: pytest.MonkeyPatch
) -> None:
    spy = _Spy(monkeypatch)

    def no_stream_durations(data: dict[str, Any]) -> None:
        for stream in data["streams"]:
            stream.pop("duration_ts", None)

    def reorder(packets: list[dict[str, Any]]) -> None:
        for packet in packets:
            packet["duration"] = 1001
        packets[-1]["duration"] = 1500  # the highest pts
        packets[-2]["duration"] = 7777  # becomes the last in file order after the swap
        packets[-2], packets[-1] = packets[-1], packets[-2]  # file order: ..., 44044, 43043
        assert packets[-1]["pts"] == 43043 and packets[-2]["pts"] == 44044

    spy.edit_streams = no_stream_durations
    spy.edit_packets = reorder
    result = probe(sample("vid-hevc8-bt709-full"))
    assert result.duration_s == Fraction(44044 + 1500, 30000)


@pytest.mark.parametrize("sample_id", ["vid-hlg", "vid-pq"])
def test_a_refused_file_is_never_decoded_not_even_for_the_tail(
    sample_id: str, sample: Sample, monkeypatch: pytest.MonkeyPatch
) -> None:
    spy = _Spy(monkeypatch)
    result = probe(sample(sample_id))
    assert [f.severity for f in result.faults] == ["refuse"]
    assert len(spy.calls) == 2
    assert not any("-read_intervals" in call or "frame=pts" in call for call in spy.calls)


def _frames_answer(delivered: list[int], error: str = "") -> Callable[[Sequence[str]], Any]:
    def fake(args: Sequence[str]) -> tuple[int, str, str]:
        assert "-read_intervals" in args
        return 0, json.dumps({"frames": [{"pts": p} for p in delivered]}), error

    return fake


# File order of a B-frame stream: keyframe 0, then P at 2002, then the B at 1001 (decode order).
REORDERED = [(0, 1001, "K__"), (2002, 1001, "___"), (1001, 1001, "___")]


def test_a_dropped_last_packet_is_found_when_frames_are_reordered(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tail = probe_module._tail_unreadable
    base = Fraction(1, 30000)
    path = Path("clip.mp4")
    monkeypatch.setattr(probe_module, "_run_ffprobe", _frames_answer([0, 2002]))
    assert tail(path, REORDERED, base) is True  # the last packet's frame (pts 1001) is missing
    monkeypatch.setattr(probe_module, "_run_ffprobe", _frames_answer([0, 1001, 2002]))
    assert tail(path, REORDERED, base) is False  # all delivered, in any order
    monkeypatch.setattr(probe_module, "_run_ffprobe", _frames_answer([0, 1001, 2002], "boom"))
    assert tail(path, REORDERED, base) is True  # any error line


def test_frames_before_the_last_keyframe_are_not_required(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    packets = [(0, 1001, "K__"), (1001, 1001, "___"), (2002, 1001, "K__"), (3003, 1001, "___")]
    monkeypatch.setattr(probe_module, "_run_ffprobe", _frames_answer([2002, 3003]))
    assert probe_module._tail_unreadable(Path("clip.mp4"), packets, Fraction(1, 30000)) is False


def test_messages_are_ascii_even_for_non_ascii_names(
    sample: Sample, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cut = tmp_path / "caf\u00e9 \u89c6\u9891.mp4"
    shutil.copy(sample("vid-truncated"), cut)
    fault = probe(cut).faults[0]
    assert fault.kind == "truncated" and fault.message.isascii()
    assert "caf\\xe9" in fault.message
    for path in (tmp_path / "\u89c6\u9891.LRV", tmp_path / "\u89c6\u9891.mp4"):
        with pytest.raises(VideoProbeError) as caught:
            probe(path)
        assert str(caught.value).isascii()
    (side,) = filter_inputs([Path("caf\u00e9.THM")]).excluded
    assert side[1].message.isascii()
    _with_gpmf(monkeypatch, _atom(("PRTN", "c", b"Y"), ("PTCL", "c", b"\xe9LOG")))
    (gp,) = probe(sample("vid-hevc8-bt709-full")).faults
    assert gp.kind == "gp_log" and gp.message.isascii()


def test_a_repeated_pts_must_be_delivered_as_often_as_it_occurs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    packets = [(0, 1001, "K__"), (1001, 1001, "___"), (1001, 1001, "___")]
    base = Fraction(1, 30000)
    monkeypatch.setattr(probe_module, "_run_ffprobe", _frames_answer([0, 1001]))
    assert probe_module._tail_unreadable(Path("clip.mp4"), packets, base) is True
    monkeypatch.setattr(probe_module, "_run_ffprobe", _frames_answer([0, 1001, 1001]))
    assert probe_module._tail_unreadable(Path("clip.mp4"), packets, base) is False
