from __future__ import annotations

import dataclasses
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import zlib
from fractions import Fraction
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from PIL import Image as PILImage

import prototype.pipeline as pipeline
from local_config import LocalConfigError, load_local_config
from lookcheck import frames, pack
from lookcheck.frames import ExtractError, OutputPathError, OutputRoots, StreamTags
from prototype.backend import CPU, select_backend
from prototype.params import Params

pytestmark = pytest.mark.skipif(
    shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None,
    reason="ffmpeg/ffprobe not on PATH",
)

# Four flat colours (top left, top right, bottom left, bottom right), chosen so that the
# round trip RGB -> 8-bit YUV (BT.709) -> RGB stays within 0.25 of an 8-bit level in both
# the full and the limited range: the clips can then hold the SAME RGB in either range.
COLOURS = ((165, 107, 20), (22, 5, 191), (118, 193, 94), (42, 42, 42))
TOLERANCE = 1.0  # 8-bit levels, the brief's 1/255
_FULL_BT709 = "range=full:colorspace=bt709:color_primaries=bt709:color_trc=bt709"
_KR, _KB = 0.2126, 0.0722
_KG = 1.0 - _KR - _KB


def _rgb_to_yuv8(rgb: tuple[int, int, int], full: bool) -> tuple[int, int, int]:
    """Quantise an RGB colour to 8-bit BT.709 Y, Cb, Cr in the full or limited range."""
    r, g, b = (value / 255.0 for value in rgb)
    y = _KR * r + _KG * g + _KB * b
    cb = (b - y) / (2.0 * (1.0 - _KB))
    cr = (r - y) / (2.0 * (1.0 - _KR))
    if full:
        return round(y * 255), round(cb * 255 + 128), round(cr * 255 + 128)
    return round(16 + 219 * y), round(128 + 224 * cb), round(128 + 224 * cr)


def _yuv8_to_rgb(yuv: tuple[int, int, int], full: bool) -> tuple[float, float, float]:
    """Convert 8-bit BT.709 Y, Cb, Cr back to RGB in 8-bit levels (float, unrounded)."""
    y8, cb8, cr8 = yuv
    if full:
        y, cb, cr = y8 / 255.0, (cb8 - 128) / 255.0, (cr8 - 128) / 255.0
    else:
        y, cb, cr = (y8 - 16) / 219.0, (cb8 - 128) / 224.0, (cr8 - 128) / 224.0
    r = y + 2.0 * (1.0 - _KR) * cr
    b = y + 2.0 * (1.0 - _KB) * cb
    g = (y - _KR * r - _KB * b) / _KG
    return r * 255.0, g * 255.0, b * 255.0


def _quadrant_source(yuvs: list[tuple[int, int, int]]) -> str:
    """A lavfi source whose four quadrants hold the given 8-bit Y, Cb, Cr values."""

    def plane(index: int) -> str:
        a, b, c, d = (value[index] for value in yuvs)
        return f"if(lt(X,W/2),if(lt(Y,H/2),{a},{c}),if(lt(Y,H/2),{b},{d}))"

    return (
        "color=c=black:s=128x128:r=10:d=1,format=yuv420p,"
        f"geq=lum='{plane(0)}':cb='{plane(1)}':cr='{plane(2)}'"
    )


def _configured_footage() -> Path | None:
    """The footage folder of the local configuration, or ``None`` when it does not load."""
    try:
        return load_local_config().footage_path
    except LocalConfigError:
        return None


def _is_inside(path: Path, folder: Path) -> bool:
    """Whether ``path`` equals ``folder`` or lies inside it (links resolved, case folded)."""
    resolved = Path(os.path.normcase(path.resolve()))
    root = Path(os.path.normcase(folder.resolve()))
    return resolved == root or root in resolved.parents


def _assert_outside_footage(path: Path) -> None:
    """Fail the test at once when ``path`` lies inside the configured footage folder.

    The synthetic tests write below pytest's temporary folder; a ``--basetemp``, ``TMP`` or
    ``TEMP`` inside the real footage folder would make them write there.
    """
    footage = _configured_footage()
    if footage is not None and _is_inside(path, footage):
        pytest.fail(f"{path} lies inside the configured footage folder {footage}")


@pytest.fixture(autouse=True)
def _tmp_path_is_outside_the_footage_folder(tmp_path: Path) -> None:
    _assert_outside_footage(tmp_path)


def _footage(tmp_path: Path) -> Path:
    """The footage root of the test roots: the REAL configured folder, so that the production
    check refuses any write there; a folder that is never created when no local configuration
    loads."""
    return _configured_footage() or tmp_path / "footage"


def _roots(tmp_path: Path) -> OutputRoots:
    _assert_outside_footage(tmp_path)
    return OutputRoots(allowed=tmp_path / "work" / "wp1.3", footage=_footage(tmp_path))


def _scratch_roots(roots: OutputRoots) -> OutputRoots:
    """Roots whose allowed folder is ``roots.allowed.parent``: for a test's own inputs, which
    still go through the production check."""
    return OutputRoots(allowed=roots.allowed.parent, footage=roots.footage)


def _checked(tmp_path: Path, name: str) -> Path:
    """``tmp_path / name`` after the production check; its folder is created."""
    path = tmp_path / name
    OutputRoots(allowed=tmp_path, footage=_footage(tmp_path)).check(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _encode(roots: OutputRoots, output: Path, lavfi: str, *, tag_full: bool) -> Path:
    """Encode a lavfi source as lossless HEVC 8-bit 4:2:0 BT.709, tagged full or limited.

    The frames are flagged with the same range as the tag, so FFmpeg converts nothing on the
    way to the encoder: the stored values are the source's own.
    """
    roots.check(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    flag = "full" if tag_full else "limited"
    done = frames.run_tool(
        [
            *("ffmpeg", "-nostdin", "-hide_banner", "-y", "-loglevel", "error"),
            *(
                "-f",
                "lavfi",
                "-i",
                f"{lavfi},setparams=range={flag}:colorspace=bt709:color_primaries=bt709:color_trc=bt709",
            ),
            *("-c:v", "libx265", "-x265-params", "lossless=1:log-level=error"),
            *("-pix_fmt", "yuv420p", "-color_range", "pc" if tag_full else "tv"),
            *("-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709"),
            *("-video_track_timescale", "30000", "-tag:v", "hvc1", str(output)),
        ]
    )
    assert done.returncode == 0, f"cannot encode: {done.stderr.decode(errors='replace')[-300:]}"
    return output


QUADRANT_MARGIN = 8
"""Pixels kept away from every quadrant edge: chroma upsampling blends the colours there."""


def _quadrant_errors(png: Path) -> float:
    """The largest difference, in 8-bit levels, between the PNG and COLOURS over the whole
    interior of each quadrant (``QUADRANT_MARGIN`` pixels in from the quadrant's edges)."""
    image = frames.read_png16(png) * 255.0
    half, margin = image.shape[0] // 2, QUADRANT_MARGIN
    rows = ((margin, half - margin), (half + margin, image.shape[0] - margin))
    columns = ((margin, half - margin), (half + margin, image.shape[1] - margin))
    corners = ((0, 0), (0, 1), (1, 0), (1, 1))  # top left, top right, bottom left, bottom right
    worst = 0.0
    for (row, column), colour in zip(corners, COLOURS, strict=True):
        (top, bottom), (left, right) = rows[row], columns[column]
        interior = image[top:bottom, left:right]
        assert interior.size, "the quadrant interior is empty"
        worst = max(worst, float(np.abs(interior - np.array(colour)).max()))
    return worst


def _quadrant_clip(roots: OutputRoots, name: str, *, data_full: bool, tag_full: bool) -> Path:
    """A clip whose RGB is COLOURS, stored in the full or limited range, tagged as given."""
    yuvs = [_rgb_to_yuv8(colour, data_full) for colour in COLOURS]
    return _encode(roots, roots.allowed / f"{name}.mp4", _quadrant_source(yuvs), tag_full=tag_full)


# --- test 1: range correctness ----------------------------------------------------------


def test_the_colour_set_survives_8_bit_yuv_in_both_ranges() -> None:
    for full in (True, False):
        for colour in COLOURS:
            back = _yuv8_to_rgb(_rgb_to_yuv8(colour, full), full)
            assert max(abs(a - b) for a, b in zip(back, colour, strict=True)) <= 0.25


def test_full_and_limited_range_clips_extract_to_the_same_known_rgb(tmp_path: Path) -> None:
    roots = _roots(tmp_path)
    for name, full in (("full", True), ("limited", False)):
        clip = _quadrant_clip(roots, name, data_full=full, tag_full=full)
        info = frames.probe_stream(clip)
        assert info.tags.color_range == ("pc" if full else "tv")
        (frame,) = frames.extract(clip, [0.0], roots.allowed / f"png-{name}", roots=roots)
        assert frame.tags == info.tags
        assert _quadrant_errors(frame.path) <= TOLERANCE, name


def test_a_range_tag_that_lies_makes_the_control_fail(tmp_path: Path) -> None:
    """Limited-range data tagged full: the extraction trusts the tag, so the check must fail."""
    roots = _roots(tmp_path)
    honest = _quadrant_clip(roots, "honest", data_full=False, tag_full=False)
    clip = roots.allowed / "liar.mp4"
    roots.check(clip)
    # Relabel the bitstream's range flag and the container's range together, data untouched.
    done = frames.run_tool(
        [
            *("ffmpeg", "-nostdin", "-hide_banner", "-y", "-loglevel", "error", "-i", str(honest)),
            *("-c", "copy", "-bsf:v", "hevc_metadata=video_full_range_flag=1"),
            *("-color_range", "pc", str(clip)),
        ]
    )
    assert done.returncode == 0, done.stderr.decode(errors="replace")[-200:]
    (frame,) = frames.extract(clip, [0.0], roots.allowed / "png-liar", roots=roots)
    assert frame.tags.color_range == "pc"
    assert _quadrant_errors(frame.path) > 5 * TOLERANCE


def test_extraction_follows_the_tags_it_is_given(tmp_path: Path) -> None:
    """Decoding a correctly tagged limited-range clip with the wrong range fails the check."""
    roots = _roots(tmp_path)
    clip = _quadrant_clip(roots, "limited", data_full=False, tag_full=False)
    info = frames.probe_stream(clip)
    right = frames._decode(clip, info, [0], roots.allowed / "right", None, roots)
    assert _quadrant_errors(right[0].path) <= TOLERANCE
    wrong_tags = dataclasses.replace(info.tags, color_range="pc")
    wrong = frames._decode(clip, info, [0], roots.allowed / "wrong", None, roots, tags=wrong_tags)
    assert _quadrant_errors(wrong[0].path) > 5 * TOLERANCE


@pytest.mark.parametrize("data_full", [True, False])
def test_decoding_with_the_wrong_matrix_fails_the_check(tmp_path: Path, data_full: bool) -> None:
    """BT.601 coefficients on BT.709 data: the known-colour check must fail by a wide margin."""
    roots = _roots(tmp_path)
    clip = _quadrant_clip(roots, "m", data_full=data_full, tag_full=data_full)
    info = frames.probe_stream(clip)
    right = frames._decode(clip, info, [0], roots.allowed / "right", None, roots)
    assert _quadrant_errors(right[0].path) <= TOLERANCE
    wrong_tags = dataclasses.replace(info.tags, color_space="bt470bg")
    wrong = frames._decode(clip, info, [0], roots.allowed / "wrong", None, roots, tags=wrong_tags)
    assert _quadrant_errors(wrong[0].path) > 5 * TOLERANCE


def test_missing_tags_are_assumed_bt709_limited_and_said_so() -> None:
    tags = frames.tags_from_stream({"pix_fmt": "yuv420p"})
    assert (tags.color_range, tags.color_space) == ("tv", "bt709")
    assert tags.assumed == ("color_range", "color_space")
    tagged = frames.tags_from_stream(
        {"pix_fmt": "yuvj420p", "color_range": "pc", "color_space": "bt709"}
    )
    assert tagged.assumed == ()


@pytest.mark.parametrize(
    "stream",
    [
        {"pix_fmt": "yuvj420p", "color_range": "tv", "color_space": "bt709"},
        {"pix_fmt": "yuv420p", "color_range": "tv", "color_space": "ictcp"},
        {"pix_fmt": "rgb24"},
    ],
)
def test_streams_outside_the_envelope_are_refused(stream: dict[str, str]) -> None:
    with pytest.raises(ExtractError):
        frames.tags_from_stream(stream)


def test_a_stream_without_a_frame_rate_is_refused_not_a_traceback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stream = {
        "width": 64,
        "height": 64,
        "time_base": "1/30000",
        "avg_frame_rate": "0/0",
        "duration": "1.0",
        "pix_fmt": "yuv420p",
        "color_range": "tv",
        "color_space": "bt709",
    }
    monkeypatch.setattr(frames, "run_ffprobe", lambda _arguments: {"streams": [stream]})
    with pytest.raises(ExtractError, match="unusable stream properties"):
        frames.probe_stream(Path("x.mp4"))


# --- test 2: pts fidelity ---------------------------------------------------------------------

LEVELS = 12


def _ramp_clip(roots: OutputRoots) -> Path:
    """Twelve frames at 30000/1001 whose luma (limited range) is 40 + 12 * frame number."""
    source = (
        "color=c=black:s=128x128:r=30000/1001:d=0.5,format=yuv420p,geq=lum='40+12*N':cb=128:cr=128"
    )
    return _encode(roots, roots.allowed / "ramp.mp4", source, tag_full=False)


def _gray_level(png: Path) -> float:
    """The mean of a PNG in 8-bit levels, converted back to the limited-range luma."""
    return float(frames.read_png16(png).mean() * 255.0 * 219.0 / 255.0 + 16.0)


def _listed_pts(clip: Path) -> list[int]:
    document = frames.run_ffprobe(
        ["-select_streams", "v:0", "-show_frames", "-show_entries", "frame=pts", str(clip)]
    )
    return sorted(int(frame["pts"]) for frame in document["frames"])


def test_extracted_frames_carry_the_pts_the_probe_reports(tmp_path: Path) -> None:
    roots = _roots(tmp_path)
    clip = _ramp_clip(roots)
    listed = _listed_pts(clip)
    assert len(listed) >= 10
    info = frames.probe_stream(clip)
    wanted = [3, 7, 0, len(listed) - 1]
    stamps = [float(listed[k] * info.time_base) for k in wanted]
    got = frames.extract(clip, stamps, roots.allowed / "png", roots=roots)
    assert [f.pts_ticks for f in got] == [listed[k] for k in wanted]
    for frame, k in zip(got, wanted, strict=True):
        assert frame.time_base == info.time_base
        assert frame.path.name == frames.frame_stem(clip.stem, float(frame.pts)) + ".png"
        assert abs(_gray_level(frame.path) - (40 + 12 * k)) <= 1.5, "wrong frame content"


def test_an_excerpt_is_the_frames_of_the_range_in_order(tmp_path: Path) -> None:
    roots = _roots(tmp_path)
    clip = _ramp_clip(roots)
    listed = _listed_pts(clip)
    info = frames.probe_stream(clip)
    start, end = float(listed[2] * info.time_base), float(listed[9] * info.time_base)
    got = frames.excerpt(clip, start, end - start, roots.allowed / "exc", roots=roots)
    assert [f.pts_ticks for f in got] == listed[2:9]
    for frame, k in zip(got, range(2, 9), strict=True):
        assert abs(_gray_level(frame.path) - (40 + 12 * k)) <= 1.5
    numbered = frames.excerpt(
        clip, start, end - start, roots.allowed / "idx", roots=roots, naming="index"
    )
    assert [f.path.name for f in numbered] == [f"ramp_f{k:04d}.png" for k in range(7)]
    assert [f.pts_ticks for f in numbered] == listed[2:9]


def test_a_timestamp_past_the_last_frame_is_an_error(tmp_path: Path) -> None:
    roots = _roots(tmp_path)
    clip = _ramp_clip(roots)
    with pytest.raises(ExtractError, match="no frame"):
        frames.extract(clip, [99.0], roots.allowed / "png", roots=roots)


def test_short_side_resizes_and_keeps_the_aspect_ratio(tmp_path: Path) -> None:
    roots = _roots(tmp_path)
    clip = _quadrant_clip(roots, "q", data_full=False, tag_full=False)
    (frame,) = frames.extract(clip, [0.0], roots.allowed / "small", short_side=64, roots=roots)
    assert (frame.width, frame.height) == (64, 64)
    assert frames.read_png16(frame.path).shape == (64, 64, 3)


# --- output safety -----------------------------------------------------------------------------


def test_outputs_inside_the_footage_folder_or_outside_the_pack_are_refused(tmp_path: Path) -> None:
    roots = _roots(tmp_path)
    clip = _ramp_clip(roots)
    footage = tmp_path / "fabricated-footage"  # fabricated on purpose: it is checked for emptiness
    footage.mkdir()
    roots = OutputRoots(allowed=roots.allowed, footage=footage)
    with pytest.raises(OutputPathError, match="footage"):
        frames.extract(clip, [0.0], roots.footage / "png", roots=roots)
    with pytest.raises(OutputPathError, match="outside"):
        frames.extract(clip, [0.0], tmp_path / "elsewhere", roots=roots)
    assert list(roots.footage.iterdir()) == []
    assert not (tmp_path / "elsewhere").exists()


def test_a_file_with_more_than_one_hard_link_is_refused(tmp_path: Path) -> None:
    roots = _roots(tmp_path)
    original = roots.write_text(roots.allowed / "a.txt", "x")
    try:
        os.link(original, roots.check(roots.allowed / "b.txt"))
    except OSError:
        pytest.skip("hard links are not available here")
    with pytest.raises(OutputPathError, match="hard links"):
        roots.write_text(original, "y")
    assert original.read_text() == "x"


def test_tool_env_drops_ffreport(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FFREPORT", "file=x.log")
    assert "FFREPORT" not in frames.tool_env()


# --- extracted PNGs carry no colour chunk -------------------------------------------------------


def _chunk_kinds(data: bytes) -> list[str]:
    kinds, position = [], 8
    while position < len(data):
        (length,) = struct.unpack(">I", data[position : position + 4])
        kinds.append(data[position + 4 : position + 8].decode("ascii"))
        position += 12 + length
    return kinds


def test_extracted_frames_are_stripped_to_the_critical_chunks(tmp_path: Path) -> None:
    """FFmpeg writes cICP/cHRM/gAMA into its PNGs; the prototype writes none; both must match."""
    roots = _roots(tmp_path)
    clip = _quadrant_clip(roots, "chunks", data_full=True, tag_full=True)
    raw = roots.allowed / "raw.png"
    info = frames.probe_stream(clip)
    command = frames.decode_command(clip, info.tags, Fraction(0), 1, raw)
    assert frames.run_tool(command).returncode == 0
    raw_kinds = _chunk_kinds(raw.read_bytes())
    assert set(raw_kinds) - {"IHDR", "IDAT", "IEND"}, "control: FFmpeg's own PNG has extra chunks"
    (frame,) = frames.extract(clip, [0.0], roots.allowed / "png", roots=roots)
    kept = _chunk_kinds(frame.path.read_bytes())
    assert kept[0] == "IHDR" and kept[-1] == "IEND" and set(kept) == {"IHDR", "IDAT", "IEND"}
    assert np.array_equal(frames.read_png16(frame.path), frames.read_png16(raw))
    prototype_png = roots.allowed / "proto.png"
    pack.write_png16(prototype_png, np.zeros((4, 4, 3), np.float32))
    assert set(_chunk_kinds(prototype_png.read_bytes())) == set(kept)


def test_strip_ancillary_chunks_removes_the_colour_chunks_and_keeps_the_pixels() -> None:
    def chunk(kind: bytes, data: bytes) -> bytes:
        crc = zlib.crc32(kind + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", crc)

    plain = _png(2, 1, [bytes([0]) + bytes(range(12))])
    header_end = 8 + 12 + 13
    extras = b"".join(
        chunk(kind, bytes(body))
        for kind, body in (
            (b"cICP", [1, 1, 0, 1]),
            (b"cHRM", [0] * 32),
            (b"gAMA", [0, 0, 177, 143]),
        )
    )
    tagged = plain[:header_end] + extras + plain[header_end:]
    assert _chunk_kinds(tagged) == ["IHDR", "cICP", "cHRM", "gAMA", "IDAT", "IEND"]
    assert frames.strip_ancillary_chunks(tagged) == plain


def test_strip_ancillary_chunks_refuses_damaged_input() -> None:
    with pytest.raises(ValueError, match="not a PNG"):
        frames.strip_ancillary_chunks(b"nope")
    good = _png(1, 1, [bytes([0]) + bytes(6)])
    with pytest.raises(ValueError, match="ends inside"):
        frames.strip_ancillary_chunks(good[:-5])


# --- the PNG reader -----------------------------------------------------------------------------


def _png(width: int, height: int, filtered_rows: list[bytes]) -> bytes:
    def chunk(kind: bytes, data: bytes) -> bytes:
        crc = zlib.crc32(kind + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", crc)

    header = struct.pack(">IIBBBBB", width, height, 16, 2, 0, 0, 0)
    body = zlib.compress(b"".join(filtered_rows))
    return (
        frames.PNG_SIGNATURE + chunk(b"IHDR", header) + chunk(b"IDAT", body) + chunk(b"IEND", b"")
    )


def test_the_png_reader_unfilters_none_sub_and_up_rows(tmp_path: Path) -> None:
    rng = np.random.default_rng(3)
    width, height = 5, 4
    values = rng.integers(0, 65536, (height, width, 3), dtype=np.uint16)
    raw = values.astype(">u2").reshape(height, -1).view(np.uint8)
    rows = []
    for y in range(height):
        row = raw[y].astype(np.int64)
        kind = y % 3  # None, Sub, Up, None
        if kind == 1:
            filtered = (row - np.concatenate([np.zeros(6, np.int64), row[:-6]])) % 256
        elif kind == 2:
            filtered = (row - raw[y - 1].astype(np.int64)) % 256
        else:
            filtered = row
        rows.append(bytes([kind]) + filtered.astype(np.uint8).tobytes())
    path = _checked(tmp_path, "f.png")
    path.write_bytes(_png(width, height, rows))
    expected = values.astype(np.float32) / np.float32(65535.0)
    assert np.array_equal(frames.read_png16(path), expected)


def test_the_png_reader_refuses_paeth_and_other_formats(tmp_path: Path) -> None:
    path = _checked(tmp_path, "paeth.png")
    path.write_bytes(_png(1, 1, [bytes([4]) + bytes(6)]))
    with pytest.raises(ValueError, match="filter 4"):
        frames.read_png16(path)
    eight_bit = _checked(tmp_path, "eight.png")
    PILImage.new("RGB", (4, 4)).save(eight_bit)
    with pytest.raises(ValueError, match="16-bit RGB"):
        frames.read_png16(eight_bit)


def test_the_prototype_writer_and_the_reader_round_trip(tmp_path: Path) -> None:
    image = np.random.default_rng(1).random((6, 7, 3), dtype=np.float32)
    path = _checked(tmp_path, "p.png")
    pack.write_png16(path, image)
    assert np.abs(frames.read_png16(path) - image).max() <= 0.5 / 65535 + 1e-7


# --- test 3: the pack layout, 4: the statistics ----------------------------------------------


@pytest.fixture(scope="module")
def synthetic_pack(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Any]:
    """Build a pack from two frames of a synthetic clip, on the CPU."""
    root = tmp_path_factory.mktemp("pack")
    roots = _roots(root)
    clip = _checked(root, "work/synth.mp4")
    done = frames.run_tool(
        [
            *("ffmpeg", "-nostdin", "-hide_banner", "-y", "-loglevel", "error"),
            *("-f", "lavfi", "-i", "testsrc2=size=256x144:rate=30000/1001:duration=1"),
            *("-c:v", "libx265", "-crf", "12", "-x265-params", "log-level=error"),
            *("-pix_fmt", "yuv420p", "-color_range", "tv", "-colorspace", "bt709"),
            *("-color_primaries", "bt709", "-color_trc", "bt709", str(clip)),
        ]
    )
    assert done.returncode == 0, done.stderr.decode(errors="replace")[-300:]
    got = frames.extract(clip, [0.1, 0.6], roots.allowed / "frames", roots=roots)
    document = pack.build_pack(got, roots.allowed, roots, CPU)
    return {"roots": roots, "frames": got, "document": document, "clip": clip}


def _distance(a: np.ndarray[Any, Any], b: np.ndarray[Any, Any]) -> float:
    """Mean absolute difference of two 8-bit images, in levels."""
    return float(np.abs(a - b).mean())


def test_the_pack_has_its_layout_and_the_index_names_every_file(
    synthetic_pack: dict[str, Any],
) -> None:
    roots: OutputRoots = synthetic_pack["roots"]
    got: list[frames.FrameFile] = synthetic_pack["frames"]
    root = roots.allowed
    names = [v.name for v in pack.default_variants()]
    assert names == ["ancuti2018", "ancuti2018-blue", "c3"]
    for frame in got:
        stem = frame.path.stem
        assert (root / "frames" / f"{stem}.png").is_file()
        assert (root / "thumbs" / f"{stem}.jpg").is_file()
        for name in names:
            assert frames.read_png16(root / "frames" / f"{stem}-{name}.png").shape == (144, 256, 3)
            assert (root / "thumbs" / f"{stem}-{name}.jpg").is_file()
            with PILImage.open(root / "pairs" / f"{stem}-{name}.jpg") as pair:
                assert pair.size == (512, 144)  # source left, corrected right, not enlarged
                both = np.asarray(pair.convert("RGB")).astype(np.float64)
            source8 = frames.to_uint8(frames.read_png16(frame.path)).astype(np.float64)
            corrected8 = frames.to_uint8(
                frames.read_png16(root / "frames" / f"{stem}-{name}.png")
            ).astype(np.float64)
            left, right = both[:, :256], both[:, 256:]
            assert _distance(source8, corrected8) > 6, "control: source and corrected must differ"
            assert _distance(left, source8) < _distance(left, corrected8), "left is not the source"
            assert _distance(right, corrected8) < _distance(right, source8), (
                "right is not corrected"
            )
    for name in ("frames.json", "statistics.json", "index.html"):
        assert (root / name).is_file()
    page = (root / "index.html").read_text(encoding="utf-8")
    on_disk = sorted(
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and path.name != "index.html" and path.parent != root.parent
    )
    on_disk = [name for name in on_disk if not name.startswith("..")]
    pack_files = [name for name in on_disk if name.split("/")[0] in {"frames", "thumbs", "pairs"}]
    assert pack_files
    for name in [*pack_files, "frames.json", "statistics.json"]:
        assert f'"{name}"' in page, f"{name} is not named in index.html"
    assert not [p for p in (root / "frames").iterdir() if p.name.startswith(".")]
    assert "http://" not in page and "https://" not in page


def test_the_index_lists_variants_defaults_and_the_pending_cases(
    synthetic_pack: dict[str, Any],
) -> None:
    page = (synthetic_pack["roots"].allowed / "index.html").read_text(encoding="utf-8")
    for variant in pack.default_variants():
        assert variant.flags in page
    for field in dataclasses.fields(Params):
        assert f"<td>{field.name}</td>" in page
    for case, _why in pack.PENDING_CASES:
        assert case in page
    assert page.count("PENDING:") == len(pack.PENDING_CASES)


def test_resizing_hits_the_pack_sizes_and_never_enlarges() -> None:
    tall = np.zeros((2160, 3840, 3), np.uint8)
    assert pack.resized(tall, pack.THUMB_SHORT_SIDE).shape == (540, 960, 3)
    assert pack.resized(tall, pack.PAIR_SHORT_SIDE).shape == (1080, 1920, 3)
    small = np.zeros((144, 256, 3), np.uint8)
    assert pack.resized(small, 540) is small


def _jsonable(value: Any) -> Any:
    return json.loads(json.dumps(value))


def test_the_statistics_hold_every_field_of_the_result_and_are_per_frame(
    synthetic_pack: dict[str, Any],
) -> None:
    got: list[frames.FrameFile] = synthetic_pack["frames"]
    document = json.loads(
        (synthetic_pack["roots"].allowed / "statistics.json").read_text(encoding="utf-8")
    )
    assert document["device"] == "cpu"
    assert document["defaults"] == _jsonable(dataclasses.asdict(Params()))
    comp_fields = {f.name for f in dataclasses.fields(pipeline.CompensationInfo)}
    balance_fields = {f.name for f in dataclasses.fields(pipeline.WhiteBalanceInfo)}
    param_fields = {f.name for f in dataclasses.fields(Params)}
    assert [e["frame"] for e in document["frames"]] == [f.path.stem for f in got]
    seen_balances = []
    for entry, frame in zip(document["frames"], got, strict=True):
        image = frames.read_png16(frame.path)
        assert entry["pts_ticks"] == frame.pts_ticks
        for variant in pack.default_variants():
            record = entry["variants"][variant.name]
            assert set(record["compensation"]) == comp_fields
            assert set(record["white_balance"]) == balance_fields
            assert set(record["params"]) == param_fields
            # The record is the one the prototype produces on THIS frame at THIS variant.
            fresh = pipeline.correct(image, variant.params, CPU)
            assert record["compensation"] == _jsonable(dataclasses.asdict(fresh.compensation))
            assert record["white_balance"] == _jsonable(dataclasses.asdict(fresh.white_balance))
            assert record["params"] == _jsonable(dataclasses.asdict(variant.params))
            low, high = pipeline.normalisation_bounds(fresh.white_balanced, fresh.params)
            assert record["normalisation"]["low"] == low
            assert record["normalisation"]["high"] == high
        seen_balances.append(entry["variants"]["ancuti2018"]["white_balance"]["channel_means"])
    assert seen_balances[0] != seen_balances[1], "two different frames, one set of statistics"


def test_each_variant_is_labelled_with_the_parameters_actually_used(
    synthetic_pack: dict[str, Any],
) -> None:
    document = synthetic_pack["document"]
    for entry in document["frames"]:
        plain = entry["variants"]["ancuti2018"]["params"]
        blue = entry["variants"]["ancuti2018-blue"]["params"]
        c3 = entry["variants"]["c3"]["params"]
        assert (plain["method"], plain["blue_compensation"]) == ("ancuti2018", False)
        assert (blue["method"], blue["blue_compensation"]) == ("ancuti2018", True)
        assert c3["method"] == "c3"
        comp = entry["variants"]["ancuti2018-blue"]["compensation"]
        assert set(comp["effective"]) == {"red", "blue"}
        assert set(entry["variants"]["ancuti2018"]["compensation"]["effective"]) == {"red"}
        assert set(entry["variants"]["c3"]["compensation"]["effective"]) == {"cr", "cb"}
    assert document["variants"]["ancuti2018-blue"]["flags"] == "--method ancuti2018 --blue"


def test_the_collapse_threshold_is_the_prototypes() -> None:
    assert pack.NORMALISATION_COLLAPSE == pipeline._EPS


def test_bound_flags_report_a_gain_cap_the_clamp_and_a_collapsed_normalisation() -> None:
    red_starved = np.full((64, 64, 3), 0.5, np.float32)
    red_starved[..., 0] = 0.02
    result = pipeline.correct(red_starved, Params(), CPU)
    record = pack.statistics_record(result, CPU)
    assert record["bound"]["red_gain_cap"] is True
    assert record["bound"]["blue_gain_cap"] is False
    assert record["bound"]["white_balance_clamp"][0] is True
    assert record["bound"]["normalisation_collapsed"] is True  # a flat frame has no high-pass
    assert record["bound"]["any"] is True
    assert "red cap" in pack.summary_line(record) and "N{} collapsed" in pack.summary_line(record)
    rng = np.random.default_rng(2)
    busy = (0.4 + 0.2 * rng.random((64, 64, 3))).astype(np.float32)
    calm = pack.statistics_record(pipeline.correct(busy, Params(), CPU), CPU)
    assert calm["bound"]["any"] is False
    assert pack.summary_line(calm).endswith("bound: none")


def test_the_still_timestamps_run_from_5_to_95_percent() -> None:
    stamps = pack.still_timestamps(100.0)
    assert len(stamps) == 6
    assert stamps[0] == pytest.approx(5.0)
    assert stamps[-1] == pytest.approx(95.0)
    steps = np.diff(stamps)
    assert np.allclose(steps, steps[0])


# --- the flicker clip, end to end on a synthetic source ------------------------------------------


def test_series_summary_reports_the_largest_step() -> None:
    summary = pack.series_summary([1.0, 3.0, 2.0])
    assert summary["min"] == 1.0 and summary["max"] == 3.0
    assert summary["max_step"] == 2.0


@pytest.mark.gpu
@pytest.mark.slow
def test_the_flicker_clip_is_built_checked_and_pruned(tmp_path: Path) -> None:
    try:
        backend = select_backend("gpu")
    except RuntimeError as exc:
        pytest.skip(f"no usable graphics card: {exc}")
    roots = _roots(tmp_path)
    clip = _scratch_roots(roots).check(roots.allowed.parent / "flick.mp4")
    clip.parent.mkdir(parents=True, exist_ok=True)
    done = frames.run_tool(
        [
            *("ffmpeg", "-nostdin", "-hide_banner", "-y", "-loglevel", "error"),
            *("-f", "lavfi", "-i", "testsrc2=size=320x240:rate=30000/1001:duration=10"),
            *("-vf", f"format=yuv420p,setparams={_FULL_BT709}"),
            *("-c:v", "libx265", "-crf", "20", "-x265-params", "log-level=error"),
            *("-pix_fmt", "yuv420p", "-color_range", "pc", "-colorspace", "bt709"),
            *("-color_primaries", "bt709", "-color_trc", "bt709", str(clip)),
        ]
    )
    assert done.returncode == 0, done.stderr.decode(errors="replace")[-300:]
    flicker_dir = roots.allowed / "flicker"
    document = pack.run_flicker(clip, roots, backend, flicker_dir)
    count = document["excerpt"]["frames"]
    assert 179 <= count <= 180
    assert all(check["ok"] for check in document["checks"].values())
    # The source's full colour description reaches both encodes (not only range and matrix).
    assert document["tags"]["color_primaries"] == document["tags"]["color_transfer"] == "bt709"
    for label in ("unsmoothed", "source"):
        assert document["checks"][label]["color_primaries"] == "bt709", label
        assert document["checks"][label]["color_transfer"] == "bt709", label
    readback = document["checks"]["readback"]
    for label in ("unsmoothed", "source"):  # every frame of both clips was read back
        record = readback[label]
        assert record["frames_read"] == record["frames_expected"] == count
        assert len(record["frames"]) == count and record["failed_frames"] == []
        assert record["smallest_margin"] > 0 and record["worst_own"] <= pack.READBACK_MAX_OWN
    assert not list(flicker_dir.glob("*.partial.mp4")) and not (flicker_dir / "readback").exists()
    assert len(document["frames"]) == count
    assert document["smoothing"].startswith("none")
    for name in ("flick_unsmoothed.mp4", "flick_source.mp4", "statistics.json", "statistics.png"):
        assert (flicker_dir / name).is_file()
    for folder in ("source", "corrected"):
        assert len(list((flicker_dir / folder).glob("*.png"))) == 3  # first, middle, last
    reread = json.loads((flicker_dir / "statistics.json").read_text(encoding="utf-8"))
    assert [e["pts_ticks"] for e in reread["frames"]] == sorted(
        e["pts_ticks"] for e in reread["frames"]
    )
    ticks = {
        b["pts_ticks"] - a["pts_ticks"]
        for a, b in zip(reread["frames"], reread["frames"][1:], strict=False)
    }
    assert ticks == {1001}
    # The encoded frames are the kept frames, in place (a shifted, repeated or swapped
    # sequence would not match asymmetric indices 0, 90 and 179).
    kept = {
        index: (
            frames.to_uint8(
                frames.read_png16(flicker_dir / "source" / f"flick_f{index:04d}.png")
            ).astype(np.float64),
            frames.to_uint8(
                frames.read_png16(flicker_dir / "corrected" / f"flick_f{index:04d}-ancuti2018.png")
            ).astype(np.float64),
        )
        for index in (0, 90, 179)
    }
    assert _distance(kept[90][0], kept[90][1]) > 6, "control: the correction must change frames"
    assert _distance(kept[0][0], kept[90][0]) > 6, "control: frames must differ with the index"
    for clip_name, which in (("flick_source.mp4", 0), ("flick_unsmoothed.mp4", 1)):
        for index, pair_of_frames in kept.items():
            (got,) = frames.extract(
                flicker_dir / clip_name,
                [index * 1001 / 30000],
                tmp_path / f"decoded-{clip_name}-{index}",
                roots=OutputRoots(tmp_path, roots.footage),  # the real footage folder
            )
            decoded = frames.to_uint8(frames.read_png16(got.path)).astype(np.float64)
            assert got.pts_ticks == index * 1001
            nearest = min(kept, key=lambda other: _distance(decoded, kept[other][which]))
            assert nearest == index, f"{clip_name} frame {index} matches kept frame {nearest}"
            assert _distance(decoded, pair_of_frames[which]) < 8, (clip_name, index)
            assert _distance(decoded, pair_of_frames[1 - which]) > 6, (clip_name, index)


def _fake_probe(
    stream: dict[str, Any], steps: int = 1001, count: int = 5, order: list[int] | None = None
) -> Any:
    def run(arguments: Any) -> dict[str, Any]:
        if "-show_frames" in arguments:
            ticks = [k * steps for k in range(count)]
            return {"frames": [{"pts": ticks[k]} for k in (order or range(count))]}
        return {"streams": [stream]}

    return run


_GOOD_STREAM: dict[str, Any] = {
    "codec_type": "video",
    "codec_name": "hevc",
    "profile": "Main",
    "pix_fmt": "yuvj420p",
    "width": 3840,
    "height": 2160,
    "time_base": "1/30000",
    "color_range": "pc",
    "color_space": "bt709",
    "color_primaries": "bt709",
    "color_transfer": "bt709",
}


def test_verify_clip_accepts_the_right_stream_and_names_each_planted_defect(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tags = StreamTags("yuvj420p", "pc", "bt709", "bt709", "bt709")
    rate, size = Fraction(30000, 1001), (3840, 2160)

    def verdict(stream: dict[str, Any], **kwargs: Any) -> bool:
        monkeypatch.setattr(pack, "run_ffprobe", _fake_probe(stream, **kwargs))
        return bool(pack.verify_clip(Path("x.mp4"), 5, tags, rate, size)["ok"])

    assert verdict(_GOOD_STREAM) is True
    defects: dict[str, dict[str, Any]] = {
        "ten bit": {**_GOOD_STREAM, "pix_fmt": "yuv420p10le", "profile": "Main 10"},
        "pixel format": {**_GOOD_STREAM, "pix_fmt": "yuv444p"},
        "width": {**_GOOD_STREAM, "width": 1920},
        "primaries": {**_GOOD_STREAM, "color_primaries": "bt470bg"},
        "transfer": {**_GOOD_STREAM, "color_transfer": "smpte170m"},
        "range": {**_GOOD_STREAM, "color_range": "tv"},
        "matrix": {**_GOOD_STREAM, "color_space": "bt470bg"},
        "codec": {**_GOOD_STREAM, "codec_name": "h264"},
    }
    for name, stream in defects.items():
        assert verdict(stream) is False, name
    assert verdict(_GOOD_STREAM, steps=1000) is False, "timing"
    assert verdict(_GOOD_STREAM, count=4) is False, "frame count"
    assert verdict(_GOOD_STREAM, order=[0, 2, 1, 3, 4]) is False, "presentation order"


def test_a_failed_or_unverified_encode_leaves_no_clip_under_its_name(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    roots = _roots(tmp_path)
    flicker_dir = roots.allowed / "flicker"
    output = flicker_dir / "c.mp4"
    tags = StreamTags("yuvj420p", "pc", "bt709", "bt709", "bt709")
    info = frames.StreamInfo(3840, 2160, Fraction(1, 30000), Fraction(30000, 1001), 1.0, tags)

    def writes_then(code: int) -> Any:
        def run(command: list[str]) -> subprocess.CompletedProcess[bytes]:
            Path(command[-1]).write_bytes(b"partial")
            return subprocess.CompletedProcess(command, code, b"", b"boom")

        return run

    def encode() -> tuple[list[str], dict[str, Any]]:
        return pack.encode_clip(roots, Path("in_f%04d.png"), output, info, 5, flicker_dir)

    monkeypatch.setattr(pack, "run_tool", writes_then(1))
    with pytest.raises(ExtractError, match="ffmpeg failed"):
        encode()
    assert not output.exists()
    monkeypatch.setattr(pack, "run_tool", writes_then(0))
    monkeypatch.setattr(
        pack, "run_ffprobe", _fake_probe({**_GOOD_STREAM, "pix_fmt": "yuv420p10le"})
    )
    with pytest.raises(ExtractError, match="encode check failed"):
        encode()
    assert not output.exists()
    monkeypatch.setattr(pack, "run_ffprobe", _fake_probe(_GOOD_STREAM))
    command, record = encode()
    assert output.exists() and record["ok"] is True and command[-1] == str(output)


def test_the_encode_command_carries_the_source_tags_and_rate() -> None:
    tags = StreamTags("yuvj420p", "pc", "bt709", "bt709", "bt709")
    command = pack.encode_command(Path("a_f%04d.png"), Path("o.mp4"), tags, Fraction(30000, 1001))
    joined = " ".join(command)
    assert "-framerate 30000/1001" in joined
    assert "-color_range pc" in joined and "-colorspace bt709" in joined
    assert "out_range=full" in joined and "hevc_nvenc" in joined and "-an" in joined
    assert "setparams=range=pc:colorspace=bt709:color_primaries=bt709:color_trc=bt709" in joined
    untagged = StreamTags("yuv420p", "tv", "bt709", "unknown", "unknown")
    bare = " ".join(pack.encode_command(Path("a%04d.png"), Path("o.mp4"), untagged, Fraction(25)))
    assert "setparams=range=tv:colorspace=bt709 " in bare
    assert "color_trc" not in bare.replace("-color_trc", "")
    assert command[:5] == ["ffmpeg", "-nostdin", "-hide_banner", "-nostats", "-y"]


# --- the footage guard of these tests (B1) -----------------------------------------------------


def test_the_test_roots_use_the_configured_footage_folder(tmp_path: Path) -> None:
    configured = _configured_footage()
    if configured is None:
        pytest.skip("no local configuration: the test roots use a fabricated folder")
    roots = _roots(tmp_path)
    assert roots.footage == configured
    with pytest.raises(OutputPathError, match="footage"):
        roots.write_text(configured / "must-not-exist.txt", "no")
    assert not (configured / "must-not-exist.txt").exists()


def test_a_root_under_the_configured_footage_folder_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = tmp_path / "configured-footage"
    monkeypatch.setattr(sys.modules[__name__], "_configured_footage", lambda: fake)
    with pytest.raises(pytest.fail.Exception, match="footage folder"):
        _assert_outside_footage(fake / "pytest-of-user" / "test0")
    with pytest.raises(pytest.fail.Exception, match="footage folder"):
        _assert_outside_footage(fake)
    with pytest.raises(pytest.fail.Exception, match="footage folder"):
        _roots(fake / "tmp")
    _assert_outside_footage(tmp_path / "elsewhere")  # a sibling folder is fine
    # With roots built on that folder, the production check refuses every write below it,
    # even when the allowed folder itself lies inside it.
    roots = _roots(tmp_path / "elsewhere")
    assert roots.footage == fake
    for guarded in (
        roots,
        OutputRoots(allowed=fake / "work" / "wp1.3", footage=fake),
    ):
        with pytest.raises(OutputPathError, match="footage"):
            guarded.write_text(fake / "work" / "wp1.3" / "f.txt", "no")
    assert not fake.exists()


# --- the read-back of every frame (B2) -----------------------------------------------------------

READBACK_FRAMES = 8
READBACK_SIZE = (128, 96)  # multiples of the read-back factor 8


def _distinct_frames(roots: OutputRoots, directory: Path) -> Path:
    """Eight 16-bit PNGs, numbered ``s_f0000.png``..., whose content differs a lot.

    Each frame is a smooth random 4 x 4 colour field (linearly interpolated, so that 4:2:0
    chroma loses little), far from every other frame at any reduction. Returns the numbered
    pattern.
    """
    rng = np.random.default_rng(11)
    width, height = READBACK_SIZE
    for index in range(READBACK_FRAMES):
        field = rng.random((4, 4, 3))
        image = np.zeros((height, width, 3), np.float32)
        for channel in range(3):
            across = np.stack(
                [
                    np.interp(np.linspace(0, 3, width), range(4), field[row, :, channel])
                    for row in range(4)
                ]
            )
            image[:, :, channel] = np.stack(
                [
                    np.interp(np.linspace(0, 3, height), range(4), across[:, x])
                    for x in range(width)
                ],
                axis=1,
            )
        target = directory / f"s_f{index:04d}.png"
        roots.check(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        pack.write_png16(target, image)
    return directory / "s_f%04d.png"


def _reordered(roots: OutputRoots, pattern: Path, order: list[int], name: str) -> Path:
    """Copies of the frames of ``pattern`` renumbered so that copy ``i`` is frame ``order[i]``."""
    directory = pattern.parent / name
    for index, source in enumerate(order):
        target = directory / f"s_f{index:04d}.png"
        roots.check(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(pattern.parent / f"s_f{source:04d}.png", target)
    return directory / "s_f%04d.png"


def _encode_sequence(roots: OutputRoots, pattern: Path, output: Path) -> Path:
    """Encode a numbered PNG sequence as lossless HEVC 8-bit 4:2:0, limited range BT.709."""
    roots.check(output)
    done = frames.run_tool(
        [
            *("ffmpeg", "-nostdin", "-hide_banner", "-y", "-loglevel", "error"),
            *("-framerate", "30000/1001", "-start_number", "0", "-i", str(pattern)),
            *("-vf", "scale=out_color_matrix=bt709:out_range=limited,format=yuv420p"),
            *("-c:v", "libx265", "-x265-params", "lossless=1:log-level=error"),
            *("-color_range", "tv", "-colorspace", "bt709", "-color_primaries", "bt709"),
            *("-color_trc", "bt709", "-video_track_timescale", "30000", str(output)),
        ]
    )
    assert done.returncode == 0, done.stderr.decode(errors="replace")[-300:]
    return output


def _readback(
    roots: OutputRoots, pattern: Path, encoded_from: Path, count: int = READBACK_FRAMES
) -> dict[str, Any]:
    """Encode the sequence ``encoded_from`` and read the clip back against ``pattern``."""
    clip = _encode_sequence(roots, encoded_from, roots.allowed / f"{encoded_from.parent.name}.mp4")
    info = frames.probe_stream(clip)
    assert (info.width, info.height) == READBACK_SIZE
    return pack.readback_clip(clip, pattern, count, info, roots.allowed / "flicker", roots)


def _failed(record: dict[str, Any]) -> list[int]:
    return [item["index"] for item in record["failed_frames"]]


def test_distinct_frames_pass_the_full_readback_with_a_wide_margin(tmp_path: Path) -> None:
    roots = _roots(tmp_path)
    pattern = _distinct_frames(roots, roots.allowed / "seq")
    record = _readback(roots, pattern, pattern)
    assert record["ok"] is True and record["failed_frames"] == [] and record["problems"] == []
    assert record["frames_read"] == record["frames_expected"] == READBACK_FRAMES
    assert len(record["frames"]) == READBACK_FRAMES
    assert record["reduced_size"] == [16, 12] and record["factor"] == 8
    assert record["worst_own"] < pack.READBACK_MAX_OWN
    assert record["smallest_margin"] > 10, "control: the synthetic frames must be far apart"
    first, last = record["frames"][0], record["frames"][-1]
    assert first["previous"] is None and last["next"] is None
    for item in record["frames"]:
        assert item["ok"] is True and len(item["bias"]) == 3
        assert item["own"] < min(v for v in (item["previous"], item["next"]) if v is not None)
    assert len(record["channel_bias"]) == 3
    json.dumps(record, allow_nan=False)  # it goes into statistics.json
    assert not (roots.allowed / "flicker" / "readback").exists(), "scratch frames left behind"


def test_a_duplicated_frame_fails_the_readback_by_name(tmp_path: Path) -> None:
    """Frame 3 replaced by frame 2 (correct pts, correct count): the old checks passed this."""
    roots = _roots(tmp_path)
    pattern = _distinct_frames(roots, roots.allowed / "seq")
    order = [0, 1, 2, 2, 4, 5, 6, 7]
    record = _readback(roots, pattern, _reordered(roots, pattern, order, "dup"))
    assert record["ok"] is False
    assert _failed(record) == [3]
    assert "neighbour" in record["failed_frames"][0]["reason"]
    assert record["frames"][3]["margin"] <= 0 < record["frames"][2]["margin"]


def test_two_swapped_frames_fail_the_readback_by_name(tmp_path: Path) -> None:
    roots = _roots(tmp_path)
    pattern = _distinct_frames(roots, roots.allowed / "seq")
    order = [0, 1, 2, 3, 5, 4, 6, 7]
    record = _readback(roots, pattern, _reordered(roots, pattern, order, "swap"))
    assert record["ok"] is False
    assert _failed(record) == [4, 5]


def test_a_dropped_frame_fails_the_readback_on_the_count(tmp_path: Path) -> None:
    roots = _roots(tmp_path)
    pattern = _distinct_frames(roots, roots.allowed / "seq")
    order = [0, 1, 2, 4, 5, 6, 7]
    shorter = _reordered(roots, pattern, order, "drop")
    clip = _encode_sequence(roots, shorter, roots.allowed / "drop.mp4")
    info = frames.probe_stream(clip)
    record = pack.readback_clip(
        clip, pattern, READBACK_FRAMES, info, roots.allowed / "flicker", roots
    )
    assert record["ok"] is False
    assert any("7 frames, expected 8" in problem for problem in record["problems"])


def test_a_colour_shift_fails_the_readback_on_the_channel_bias(tmp_path: Path) -> None:
    """A clip encoded from brighter frames than the reference differs on every channel."""
    roots = _roots(tmp_path)
    pattern = _distinct_frames(roots, roots.allowed / "seq")
    directory = roots.allowed / "bright"
    for index in range(READBACK_FRAMES):
        image = frames.read_png16(roots.allowed / "seq" / f"s_f{index:04d}.png")
        target = directory / f"s_f{index:04d}.png"
        roots.check(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        pack.write_png16(target, np.clip(image + 6.0 / 255.0, 0.0, 1.0))
    record = _readback(roots, pattern, directory / "s_f%04d.png")
    assert record["ok"] is False
    assert any("bias" in problem for problem in record["problems"])


# --- no clip under a final name unless both are verified (B3) -----------------------------------


def _small_source(roots: OutputRoots) -> Path:
    """A 3 s full-range test clip of 128 x 72, the source of the run_flicker tests."""
    clip = _scratch_roots(roots).check(roots.allowed.parent / "flick.mp4")
    clip.parent.mkdir(parents=True, exist_ok=True)
    done = frames.run_tool(
        [
            *("ffmpeg", "-nostdin", "-hide_banner", "-y", "-loglevel", "error"),
            *("-f", "lavfi", "-i", "testsrc2=size=128x72:rate=30000/1001:duration=3"),
            *("-vf", f"format=yuv420p,setparams={_FULL_BT709}"),
            *("-c:v", "libx265", "-crf", "14", "-x265-params", "log-level=error"),
            *("-pix_fmt", "yuv420p", "-color_range", "pc", "-colorspace", "bt709"),
            *("-color_primaries", "bt709", "-color_trc", "bt709", str(clip)),
        ]
    )
    assert done.returncode == 0, done.stderr.decode(errors="replace")[-300:]
    return clip


class _FakeEncoder:
    """Stands in for ``pack.run_tool`` (the FFmpeg encode): writes the output, returns a code."""

    def __init__(self, codes: list[int]) -> None:
        self.codes = codes
        self.outputs: list[Path] = []

    def __call__(self, command: list[str]) -> subprocess.CompletedProcess[bytes]:
        self.outputs.append(Path(command[-1]))
        Path(command[-1]).write_bytes(b"clip")
        return subprocess.CompletedProcess(command, self.codes.pop(0), b"", b"boom")


def _flicker_setup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[OutputRoots, Path, Path]:
    roots = _roots(tmp_path)
    clip = _small_source(roots)
    monkeypatch.setattr(pack, "FLICKER_SECONDS", 0.5)
    flicker_dir = roots.allowed / "flicker"
    for stale in ("flick_unsmoothed.mp4", "flick_source.mp4"):  # clips of an earlier run
        roots.write_bytes(flicker_dir / stale, b"stale")
    return roots, clip, flicker_dir


def _no_clip_left(flicker_dir: Path) -> bool:
    return not list(flicker_dir.glob("*.mp4"))


@pytest.mark.parametrize("error", [ExtractError("ffprobe boom"), RuntimeError("unexpected")])
def test_a_raising_verification_leaves_no_clip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, error: Exception
) -> None:
    roots, clip, flicker_dir = _flicker_setup(tmp_path, monkeypatch)
    encoder = _FakeEncoder([0, 0])
    monkeypatch.setattr(pack, "run_tool", encoder)

    def raising(*args: Any, **kwargs: Any) -> dict[str, Any]:
        raise error

    monkeypatch.setattr(pack, "verify_clip", raising)
    with pytest.raises(type(error), match=str(error)):
        pack.run_flicker(clip, roots, CPU, flicker_dir)
    assert encoder.outputs, "control: the encode ran, so a clip existed before the failure"
    assert _no_clip_left(flicker_dir)
    assert list((flicker_dir / "source").glob("*.png")), "the frame PNGs are kept"


def test_a_failing_second_encode_leaves_neither_clip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    roots, clip, flicker_dir = _flicker_setup(tmp_path, monkeypatch)
    encoder = _FakeEncoder([0, 1])
    monkeypatch.setattr(pack, "run_tool", encoder)
    monkeypatch.setattr(pack, "verify_clip", lambda *args, **kwargs: {"ok": True})
    with pytest.raises(ExtractError, match="ffmpeg failed encoding"):
        pack.run_flicker(clip, roots, CPU, flicker_dir)
    assert len(encoder.outputs) == 2, "control: the first clip was encoded and verified"
    assert all(".partial." in output.name for output in encoder.outputs)
    assert _no_clip_left(flicker_dir)


def test_a_failed_readback_leaves_neither_clip_and_a_pass_names_both(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    roots, clip, flicker_dir = _flicker_setup(tmp_path, monkeypatch)
    encoder = _FakeEncoder([0, 0])
    monkeypatch.setattr(pack, "run_tool", encoder)
    monkeypatch.setattr(pack, "verify_clip", lambda *args, **kwargs: {"ok": True})
    good: dict[str, Any] = {"ok": True, "failed_frames": [], "problems": []}
    bad = {"ok": False, "failed_frames": [{"index": 4, "reason": "planted"}], "problems": []}
    calls: list[str] = []

    def fake_readback(*args: Any, **kwargs: Any) -> dict[str, Any]:
        calls.append(args[0].name)
        return bad if len(calls) == 2 else good  # the first clip passes, the second does not

    monkeypatch.setattr(pack, "readback_clip", fake_readback)
    with pytest.raises(ExtractError, match=r"read-back check failed.*planted"):
        pack.run_flicker(clip, roots, CPU, flicker_dir)
    assert _no_clip_left(flicker_dir)
    assert list((flicker_dir / "source").glob("*.png")), "the frame PNGs are kept"
    # A pass: both clips appear under their final names, and only then.
    encoder.codes = [0, 0]
    monkeypatch.setattr(
        pack, "readback_clip", lambda *a, **k: {"ok": True, "failed_frames": [], "problems": []}
    )
    document = pack.run_flicker(clip, roots, CPU, flicker_dir)
    assert sorted(path.name for path in flicker_dir.glob("*.mp4")) == [
        "flick_source.mp4",
        "flick_unsmoothed.mp4",
    ]
    assert document["checks"]["readback"]["ok"] is True
    assert document["encode_commands"]["source"][-1].endswith("flick_source.mp4")


# --- test 5: the footage smoke test --------------------------------------------------------------


@pytest.mark.footage
def test_extract_runs_on_the_shortest_shallow_chapter(tmp_path: Path) -> None:
    config = load_local_config()
    chapter = config.footage_path / "GX011628.MP4"
    if not chapter.is_file():
        pytest.skip("GX011628.MP4 is not in the footage folder")
    roots = OutputRoots(allowed=tmp_path / "wp1.3", footage=config.footage_path)
    (frame,) = frames.extract(chapter, [7.0], roots.allowed / "png", roots=roots)
    assert re.fullmatch(r"GX011628_\d{4}\.\d{3}\.png", frame.path.name)
    assert (frame.width, frame.height) == (3840, 2160)
    assert frame.tags.color_range == "pc" and frame.tags.color_space == "bt709"
    assert frame.tags.assumed == ()
    assert frame.pts_ticks * frame.time_base >= Fraction(7)
    assert frames.read_png16(frame.path).shape == (2160, 3840, 3)
