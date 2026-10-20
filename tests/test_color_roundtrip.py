"""WP3.5: the AD-10 pair through FFmpeg (V9 on the decoded-RGB side, encoder excluded).

Two families, both with real FFmpeg and no encoder (raw Y'CbCr in the source pixel format):

* decode truth: flat colours whose Y'CbCr codes are computed from the matrix definition with NumPy
  (``test_color_support.flat_yuv420``), decoded with the product's arguments and compared with the
  RGB they came from; the planted range / matrix / rounding / plane-order defects must exceed the
  bound. This catches CONSISTENT errors, which a round trip cannot (an error made the same way in
  both directions cancels).
* round trip: decode -> ``samples.py`` -> encode -> decode, on every in-envelope WP2.3 sample, a
  generated BT.601 clip, the D76 path (8-bit source, 10-bit out) and, when the footage is there,
  30 frames of GX011627. The planted asymmetric defects must exceed the bound.

AD-11's V9 bound (max 2/255, mean 0.2/255) is met by the RGB-side legs
(``test_rgb_side_legs_meet_ad11``). It cannot be met by the swscale pair through 8-bit 4:2:0
Y'CbCr (WP3.5 ledger, STOP 1: quantisation alone gives a mean of 0.6/255 with no chroma
resampling at all). The constants below are measured regression bounds for that pair, PENDING
THE CHARC RULING on STOP 1; the ruling is applied by editing them.
"""

from __future__ import annotations

import subprocess
from collections.abc import Callable
from pathlib import Path

import numpy as np
import pytest

from clearwater.color import decode_filter, encode_filter, planes_to_rgb, rgb_to_planes
from clearwater.io.video import find_tool, probe
from local_config import FootageLookupError, find_footage_file
from test_color_support import (
    Figures,
    decode_file_frames,
    decode_raw,
    flat_yuv420,
    make_stream,
    measure_roundtrip,
)

pytestmark = pytest.mark.usefixtures("ffmpeg_tools")

# --- PENDING CHARC RULING on WP3.5 STOP 1 (AD-11 V9 bound): measured regression bounds ----------
# Units are 1/255. Measured on the day (FFmpeg 9.0.2, bitexact, so deterministic):
#   GX011627 30 frames: mean 0.687, share over 2/255 0.72 %;
#   testsrc2 samples (45 frames): mean 1.45 (10-bit) to 2.02 (8-bit); D76 8 -> 10 bit 1.59.
PAIR_MEAN_REAL = 1.0
PAIR_SHARE_OVER_2_REAL = 0.01
PAIR_MEAN_SYNTHETIC = 2.5
# AD-11 itself, which binds the RGB-side legs (not pending):
AD11_MAX = 2.0
AD11_MEAN = 0.2

FRAMES = 45  # every frame of a WP2.3 sample
FOOTAGE_FRAMES = 30

Sample = Callable[[str], Path]

# sample id -> expected pix_fmt (the samples that pass through the pair)
ROUNDTRIP_SAMPLES = ["vid-hevc8-bt709-full", "vid-hevc10", "vid-untagged"]
REGRESSION_SAMPLES = ["vid-rotated", "vid-vfr", "vid-truncated"]

COLOURS = [
    (200, 40, 40),
    (30, 120, 160),
    (128, 128, 128),
    (250, 250, 250),
    (12, 12, 12),
    (90, 160, 60),
]
TRUTH_CASES = [
    ("yuv420p", "bt709", "limited"),
    ("yuvj420p", "bt709", "full"),
    ("yuv420p10le", "bt709", "limited"),
    ("yuv420p", "bt601", "limited"),
    ("yuv420p", "bt601", "full"),
]


def worst_error(stream_pix: tuple[str, str, str], vf_edit: Callable[[str], str] | None) -> float:
    """The largest |decoded - truth| over the flat colours, in 1/255 units."""
    pix_fmt, matrix, range_ = stream_pix
    stream = make_stream(pix_fmt=pix_fmt, matrix=matrix, range_=range_)
    vf = decode_filter(stream)
    vf = vf_edit(vf) if vf_edit is not None else vf
    worst = 0.0
    for colour in COLOURS:
        raw = flat_yuv420(colour, stream)
        rgb = planes_to_rgb(
            decode_raw(raw, stream, vf),
            width=stream.width,
            height=stream.height,
            bit_depth=stream.bit_depth,
        )
        worst = max(worst, float(np.abs(rgb * 255 - np.array(colour)).max()))
    return worst


# --- decode truth --------------------------------------------------------------------------------


@pytest.mark.parametrize("case", TRUTH_CASES)
def test_decode_matches_the_matrix_definition(case: tuple[str, str, str]) -> None:
    # Measured: 1.0 (8-bit), 0.73 (10-bit); the quantisation of the integer codes.
    assert worst_error(case, None) <= 1.0


@pytest.mark.parametrize("case", [c for c in TRUTH_CASES if c[2] == "limited"])
def test_planted_range_read_as_full_is_caught(case: tuple[str, str, str]) -> None:
    worst = worst_error(case, lambda vf: vf.replace("in_range=tv", "in_range=pc"))
    assert worst >= 10  # AD-11: range errors show as >= 10/255 (measured 19-20)


@pytest.mark.parametrize("case", TRUTH_CASES)
def test_planted_matrix_swap_is_caught(case: tuple[str, str, str]) -> None:
    other = {"smpte170m": "bt709", "bt709": "smpte170m"}
    name = "smpte170m" if case[1] == "bt601" else "bt709"

    def swap(vf: str) -> str:
        return vf.replace(f"in_color_matrix={name}", f"in_color_matrix={other[name]}")

    assert worst_error(case, swap) >= 10  # measured 15-17


def test_planted_accurate_rnd_dropped_is_caught() -> None:
    # Limited-range 8-bit decodes 1-2 levels off without accurate_rnd (WP1.3 accept: 2-3 on
    # real content); the product's own error is 1.0, the planted one 2.0 on these colours.
    for case in (("yuv420p", "bt709", "limited"), ("yuv420p", "bt601", "limited")):
        assert worst_error(case, lambda vf: vf.replace("+accurate_rnd", "")) >= 2.0
        assert worst_error(case, None) <= 1.0


def test_planted_plane_order_is_caught() -> None:
    stream = make_stream(pix_fmt="yuv420p")
    colour = (200, 40, 40)
    rgb = planes_to_rgb(
        decode_raw(flat_yuv420(colour, stream), stream),
        width=stream.width,
        height=stream.height,
        bit_depth=8,
    )
    assert np.abs(rgb * 255 - np.array(colour)).max() <= 1.0
    in_rgb_order = rgb[..., [1, 2, 0]]  # the G, B, R planes taken as R, G, B
    assert np.abs(in_rgb_order * 255 - np.array(colour)).max() >= 100


def test_out_range_is_an_argument_level_check_only() -> None:
    # swscale ignores out_range for an RGB destination: a planted out_range=tv decodes the same,
    # so the argument-level test (test_color_swscale) is where it is caught.
    case = ("yuv420p", "bt709", "limited")
    assert worst_error(case, lambda vf: vf.replace("out_range=pc", "out_range=tv")) <= 1.0


# --- the RGB-side legs: AD-11's bound ------------------------------------------------------------


@pytest.mark.parametrize("sample_id", ROUNDTRIP_SAMPLES + REGRESSION_SAMPLES)
def test_rgb_side_legs_meet_ad11(sample: Sample, sample_id: str) -> None:
    """Decode -> float -> quantise -> float on the decoded-RGB side, encoder excluded."""
    path = sample(sample_id)
    stream = probe(path).video
    figures = Figures()
    for raw in decode_file_frames(path, stream, 10):
        a = planes_to_rgb(raw, width=stream.width, height=stream.height, bit_depth=stream.bit_depth)
        again = rgb_to_planes(a, bit_depth=stream.bit_depth)
        assert again == raw
        b = planes_to_rgb(
            again, width=stream.width, height=stream.height, bit_depth=stream.bit_depth
        )
        figures.add(a, b)
    assert figures.frames == 10
    assert figures.max <= AD11_MAX and figures.mean <= AD11_MEAN
    assert figures.max == 0.0  # in fact exact


# --- the pair, sample by sample ------------------------------------------------------------------


@pytest.mark.parametrize("sample_id", ROUNDTRIP_SAMPLES)
def test_pair_round_trip_per_sample(
    sample: Sample, sample_id: str, record_property: Callable[[str, object], None]
) -> None:
    path = sample(sample_id)
    stream = probe(path).video
    figures = measure_roundtrip(path, stream, frames=FRAMES)
    record_property("figures", str(figures))
    assert figures.frames == FRAMES
    assert figures.mean <= PAIR_MEAN_SYNTHETIC, str(figures)


@pytest.mark.parametrize("sample_id", REGRESSION_SAMPLES)
def test_pair_round_trip_regression_rows(sample: Sample, sample_id: str) -> None:
    path = sample(sample_id)
    stream = probe(path).video
    figures = measure_roundtrip(path, stream, frames=12)
    assert figures.frames > 0
    assert figures.mean <= PAIR_MEAN_SYNTHETIC, str(figures)


def test_pair_round_trip_d76_eight_bit_source_ten_bit_output(sample: Sample) -> None:
    path = sample("vid-hevc8-bt709-full")
    stream = probe(path).video
    figures = measure_roundtrip(path, stream, frames=FRAMES, out_depth=10)
    assert figures.mean <= PAIR_MEAN_SYNTHETIC, str(figures)


def test_pair_round_trip_bt601_generated_clip(tmp_path: Path) -> None:
    path = tmp_path / "bt601.mp4"
    command = [
        str(find_tool("ffmpeg")), "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "lavfi", "-i", "testsrc2=size=320x180:rate=30:duration=1.5",
        "-vf", "scale=out_color_matrix=smpte170m:out_range=tv,format=yuv420p",
        "-c:v", "libx264", "-crf", "12", "-pix_fmt", "yuv420p",
        "-colorspace", "smpte170m", "-color_primaries", "smpte170m",
        "-color_trc", "smpte170m", "-color_range", "tv", str(path),
    ]  # fmt: skip
    subprocess.run(command, check=True, capture_output=True, timeout=300)
    stream = probe(path).video
    assert (stream.color.matrix, stream.color.range) == ("bt601", "limited")
    assert "in_color_matrix=smpte170m" in decode_filter(stream)
    figures = measure_roundtrip(path, stream, frames=45)
    assert figures.mean <= PAIR_MEAN_SYNTHETIC, str(figures)
    wrong = encode_filter(stream, bit_depth=8).replace("smpte170m", "bt709")
    planted = measure_roundtrip(path, stream, frames=45, encode_vf=wrong)
    assert planted.mean > PAIR_MEAN_SYNTHETIC, str(planted)  # BT.709 for BT.601 (measured ~7)


# --- planted asymmetric defects in the round trip ------------------------------------------------


def encode_with(sample: Sample, sample_id: str, edit: Callable[[str], str]) -> Figures:
    path = sample(sample_id)
    stream = probe(path).video
    encode = encode_filter(stream, bit_depth=stream.bit_depth)
    assert edit(encode) != encode
    return measure_roundtrip(path, stream, frames=FRAMES, encode_vf=edit(encode))


@pytest.mark.parametrize("sample_id", ["vid-hevc8-bt709-full", "vid-hevc10", "vid-untagged"])
def test_planted_encode_range_is_caught(sample: Sample, sample_id: str) -> None:
    def flip(vf: str) -> str:
        return (
            vf.replace("out_range=tv", "out_range=@").replace("out_range=pc", "out_range=tv")
        ).replace("out_range=@", "out_range=pc")

    figures = encode_with(sample, sample_id, flip)
    assert figures.mean > PAIR_MEAN_SYNTHETIC, str(figures)  # measured 5.6 - 13.4


@pytest.mark.parametrize("sample_id", ["vid-hevc8-bt709-full", "vid-hevc10", "vid-untagged"])
def test_planted_encode_matrix_is_caught(sample: Sample, sample_id: str) -> None:
    figures = encode_with(
        sample,
        sample_id,
        lambda vf: vf.replace("out_color_matrix=bt709", "out_color_matrix=smpte170m"),
    )
    assert figures.mean > PAIR_MEAN_SYNTHETIC, str(figures)  # measured 7.5 - 8.8


@pytest.mark.parametrize("sample_id", ["vid-hevc8-bt709-full", "vid-untagged"])
def test_planted_accurate_rnd_dropped_in_both_halves_is_caught(
    sample: Sample, sample_id: str
) -> None:
    path = sample(sample_id)
    stream = probe(path).video
    figures = measure_roundtrip(
        path,
        stream,
        frames=FRAMES,
        decode_vf=decode_filter(stream).replace("+accurate_rnd", ""),
        encode_vf=encode_filter(stream, bit_depth=8).replace("+accurate_rnd", ""),
    )
    assert figures.mean > PAIR_MEAN_SYNTHETIC, str(figures)  # measured 2.79 - 2.84


def test_planted_siting_mismatch_is_argument_level_only(sample: Sample) -> None:
    # A siting mismatch moves the mean by 1-20 % on test content (2.02 -> 2.45) and is hidden
    # in the bound; test_color_swscale plants it at argument level. Pinned here so a change shows.
    path = sample("vid-hevc8-bt709-full")
    stream = probe(path).video
    base = measure_roundtrip(path, stream, frames=FRAMES)
    encode = encode_filter(stream, bit_depth=8).replace(
        "out_chroma_loc=left", "out_chroma_loc=center"
    )
    planted = measure_roundtrip(path, stream, frames=FRAMES, encode_vf=encode)
    assert planted.mean > base.mean  # visible against the product's own figure
    assert planted.mean <= PAIR_MEAN_SYNTHETIC


# --- the footage row -----------------------------------------------------------------------------


@pytest.mark.footage
@pytest.mark.slow
def test_pair_round_trip_on_the_owners_main_case() -> None:
    """GX011627: 4K, 8-bit, BT.709 full range; read-only; untimed; the first 30 frames."""
    try:
        path = find_footage_file("GX011627")
    except FootageLookupError as error:
        if error.matches:  # an ambiguous footage folder is a defect, never a skip
            raise
        pytest.skip("GX011627 is not in the footage folder")
    stream = probe(path).video
    assert (stream.width, stream.height, stream.pix_fmt) == (3840, 2160, "yuvj420p")
    figures = measure_roundtrip(path, stream, frames=FOOTAGE_FRAMES)
    assert figures.frames == FOOTAGE_FRAMES
    assert figures.mean <= PAIR_MEAN_REAL, str(figures)
    assert figures.share_over_2 <= PAIR_SHARE_OVER_2_REAL, str(figures)
    encode = encode_filter(stream, bit_depth=8)
    flat_range = measure_roundtrip(
        path,
        stream,
        frames=FOOTAGE_FRAMES,
        encode_vf=encode.replace("out_range=pc", "out_range=tv"),
    )
    assert flat_range.mean > PAIR_MEAN_REAL, str(flat_range)  # measured 5.3
    matrix = measure_roundtrip(
        path,
        stream,
        frames=FOOTAGE_FRAMES,
        encode_vf=encode.replace("out_color_matrix=bt709", "out_color_matrix=smpte170m"),
    )
    assert matrix.mean > PAIR_MEAN_REAL, str(matrix)  # measured 2.98
    siting = measure_roundtrip(
        path,
        stream,
        frames=FOOTAGE_FRAMES,
        encode_vf=encode.replace("out_chroma_loc=left", "out_chroma_loc=center"),
    )
    assert siting.share_over_2 > PAIR_SHARE_OVER_2_REAL, str(siting)  # measured 1.67 %
