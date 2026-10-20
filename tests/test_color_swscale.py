"""WP3.5: the swscale argument pair, at argument level (AD-10, D54, D55, D76, DR-20 item 1).

Every WP2.3 video sample is probed with ``clearwater.io.video.probe`` and its resolved colour
description goes to the argument builders; the expected strings are written out here from the
sample facts, not computed by the code under test.
"""

from __future__ import annotations

import importlib
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

import pytest

from clearwater.color import (
    SWSCALE_FLAGS,
    ColorError,
    decode_filter,
    decode_pix_fmt,
    encode_filter,
    encode_pix_fmt,
    ffmpeg_color_names,
    rgb_pix_fmt,
)
from clearwater.interfaces.image import ColorDescription
from clearwater.interfaces.video import VideoStreamInfo
from clearwater.io.video import probe
from test_color_support import make_stream

probe_module = importlib.import_module("clearwater.io.video.probe")

FLAGS = "bicubic+accurate_rnd+full_chroma_int+bitexact"

# sample id -> (rgb fmt, yuv fmt, tv/pc, assumed)
SAMPLES = {
    "vid-hevc8-bt709-full": ("gbrp", "yuv420p", "pc", False),
    "vid-hevc10": ("gbrp10le", "yuv420p10le", "tv", False),
    "vid-untagged": ("gbrp", "yuv420p", "tv", True),
    "vid-rotated": ("gbrp", "yuv420p", "pc", False),
    "vid-vfr": ("gbrp", "yuv420p", "pc", False),
    "vid-truncated": ("gbrp", "yuv420p", "pc", False),
}


def expected_decode(rgb: str, rng: str, matrix: str = "bt709", loc: str = "left") -> str:
    return (
        f"scale=in_color_matrix={matrix}:in_range={rng}:in_chroma_loc={loc}"
        f":out_range=pc:flags={FLAGS},format={rgb}"
    )


def expected_encode(yuv: str, rng: str, matrix: str = "bt709", loc: str = "left") -> str:
    return (
        f"scale=in_range=pc:out_color_matrix={matrix}:out_range={rng}"
        f":out_chroma_loc={loc}:flags={FLAGS},format={yuv}"
    )


def stream_of(sample: Callable[[str], Path], sample_id: str) -> VideoStreamInfo:
    return probe(sample(sample_id)).video


def keywords(vf: str) -> dict[str, str]:
    """Parse ``scale=k=v:k=v:...,format=f`` into a dict (``format`` included)."""
    scale, fmt = vf.split(",")
    assert scale.startswith("scale=") and fmt.startswith("format=")
    pairs = (item.split("=", 1) for item in scale[len("scale=") :].split(":"))
    return {**dict(pairs), "format": fmt[len("format=") :]}


def check_pair(stream: VideoStreamInfo, decode: str, encode: str, *, depth: int) -> None:
    """Assert that a decode/encode pair is AD-10's, inverse, for the stream (raises on a defect)."""
    names = {"bt709": "bt709", "bt601": "smpte170m"}
    rng = {"limited": "tv", "full": "pc"}[stream.color.range]
    siting = "left" if stream.chroma_siting == "unknown" else stream.chroma_siting
    d, e = keywords(decode), keywords(encode)
    assert d["flags"] == e["flags"] == SWSCALE_FLAGS
    assert d["in_color_matrix"] == e["out_color_matrix"] == names[stream.color.matrix]
    assert d["in_range"] == e["out_range"] == rng
    assert d["out_range"] == e["in_range"] == "pc"
    assert d["in_chroma_loc"] == e["out_chroma_loc"] == siting
    assert d["format"] == rgb_pix_fmt(stream.bit_depth)
    assert e["format"] == {8: "yuv420p", 10: "yuv420p10le"}[depth]
    for vf in (d, e):
        assert not [k for k in vf if "primaries" in k or "transfer" in k or "trc" in k]
        assert set(vf) <= {
            "in_color_matrix", "out_color_matrix", "in_range", "out_range",
            "in_chroma_loc", "out_chroma_loc", "flags", "format",
        }  # fmt: skip


@pytest.mark.parametrize("sample_id", list(SAMPLES))
def test_arguments_per_sample(sample: Callable[[str], Path], sample_id: str) -> None:
    rgb, yuv, rng, _ = SAMPLES[sample_id]
    stream = stream_of(sample, sample_id)
    assert stream.chroma_siting == "left"
    assert decode_filter(stream) == expected_decode(rgb, rng)
    assert decode_pix_fmt(stream) == rgb
    assert encode_filter(stream, bit_depth=stream.bit_depth) == expected_encode(yuv, rng)
    assert encode_pix_fmt(stream, bit_depth=stream.bit_depth) == yuv
    check_pair(
        stream,
        decode_filter(stream),
        encode_filter(stream, bit_depth=stream.bit_depth),
        depth=stream.bit_depth,
    )


def test_yuvj_becomes_non_j_with_full_range(sample: Callable[[str], Path]) -> None:
    stream = stream_of(sample, "vid-hevc8-bt709-full")
    assert stream.pix_fmt == "yuvj420p"
    assert encode_pix_fmt(stream, bit_depth=8) == "yuv420p"
    assert "out_range=pc" in encode_filter(stream, bit_depth=8)


def test_d76_ten_bit_output_from_eight_bit_source() -> None:
    stream = make_stream(pix_fmt="yuv420p", range_="limited")
    assert decode_filter(stream) == expected_decode("gbrp", "tv")
    assert encode_filter(stream, bit_depth=10) == expected_encode("yuv420p10le", "tv")
    assert encode_pix_fmt(stream, bit_depth=10) == "yuv420p10le"
    check_pair(stream, decode_filter(stream), encode_filter(stream, bit_depth=10), depth=10)
    full = make_stream(pix_fmt="yuvj420p", range_="full")
    assert encode_filter(full, bit_depth=10) == expected_encode("yuv420p10le", "pc")


def test_bt601_uses_the_smpte170m_name_and_its_own_range() -> None:
    stream = make_stream(matrix="bt601", range_="limited")
    assert decode_filter(stream) == expected_decode("gbrp", "tv", matrix="smpte170m")
    assert encode_filter(stream, bit_depth=8) == expected_encode(
        "yuv420p", "tv", matrix="smpte170m"
    )


@pytest.mark.parametrize("siting", ["center", "topleft", "top", "bottomleft", "bottom", "left"])
def test_declared_siting_is_passed_both_ways(siting: str) -> None:
    stream = make_stream(siting=siting)
    assert decode_filter(stream) == expected_decode("gbrp", "tv", loc=siting)
    assert encode_filter(stream, bit_depth=8) == expected_encode("yuv420p", "tv", loc=siting)


def test_unknown_siting_is_left_in_both_directions() -> None:
    stream = make_stream(siting="unknown")
    assert "in_chroma_loc=left" in decode_filter(stream)
    assert "out_chroma_loc=left" in encode_filter(stream, bit_depth=8)


# --- planted wrong arguments, each failing by name ---------------------------------------------

PLANTS: dict[str, Callable[[str, str], tuple[str, str]]] = {
    "range read as full on a limited stream": lambda d, e: (
        d.replace("in_range=tv", "in_range=pc"),
        e,
    ),
    "range written as full on a limited stream": lambda d, e: (
        d,
        e.replace("out_range=tv", "out_range=pc"),
    ),
    "BT.601 for BT.709 (decode)": lambda d, e: (
        d.replace("in_color_matrix=bt709", "in_color_matrix=smpte170m"),
        e,
    ),
    "BT.601 for BT.709 (encode)": lambda d, e: (
        d,
        e.replace("out_color_matrix=bt709", "out_color_matrix=smpte170m"),
    ),
    "accurate_rnd dropped (decode)": lambda d, e: (d.replace("+accurate_rnd", ""), e),
    "accurate_rnd dropped (encode)": lambda d, e: (d, e.replace("+accurate_rnd", "")),
    "bitexact dropped": lambda d, e: (d.replace("+bitexact", ""), e),
    "full_chroma_int dropped": lambda d, e: (d, e.replace("+full_chroma_int", "")),
    "bilinear instead of bicubic": lambda d, e: (d, e.replace("bicubic", "bilinear")),
    "decode out_range not full": lambda d, e: (d.replace("out_range=pc", "out_range=tv"), e),
    "encode in_range not full": lambda d, e: (d, e.replace("in_range=pc", "in_range=tv")),
    "decode and encode siting differ": lambda d, e: (
        d,
        e.replace("out_chroma_loc=left", "out_chroma_loc=center"),
    ),
    "a primaries option present (decode)": lambda d, e: (
        d.replace(",format=", ":in_primaries=bt709,format="),
        e,
    ),
    "an output primaries option present": lambda d, e: (
        d,
        e.replace(":flags=", ":out_primaries=bt709:flags="),
    ),
    "a transfer option present": lambda d, e: (
        d.replace(":flags=", ":in_transfer=bt709:flags="),
        e,
    ),
    "decode delivers 16-bit RGB for an 8-bit source": lambda d, e: (
        d.replace("format=gbrp", "format=gbrp10le"),
        e,
    ),
}


@pytest.mark.parametrize("name", list(PLANTS))
def test_planted_wrong_argument_is_caught(name: str) -> None:
    stream = make_stream(pix_fmt="yuv420p", range_="limited")
    decode = decode_filter(stream)
    encode = encode_filter(stream, bit_depth=8)
    check_pair(stream, decode, encode, depth=8)  # the product's own pair passes
    wrong_decode, wrong_encode = PLANTS[name](decode, encode)
    assert (wrong_decode, wrong_encode) != (decode, encode)
    with pytest.raises((AssertionError, ValueError)):
        check_pair(stream, wrong_decode, wrong_encode, depth=8)


# --- refusals, by name -------------------------------------------------------------------------


@pytest.mark.parametrize("pix_fmt", ["yuv422p", "yuv444p", "yuv420p12le", "gbrp", "nv12", ""])
def test_unsupported_pixel_format_is_refused(pix_fmt: str) -> None:
    stream = replace(make_stream(), pix_fmt=pix_fmt)
    for call in (
        lambda: decode_filter(stream),
        lambda: decode_pix_fmt(stream),
        lambda: encode_filter(stream, bit_depth=8),
        lambda: encode_pix_fmt(stream, bit_depth=8),
    ):
        with pytest.raises(ColorError, match=r"pixel format .* not supported; supported: yuv420p"):
            call()


@pytest.mark.parametrize("matrix", ["identity", "unknown", "bt2020"])
def test_unsupported_matrix_is_refused(matrix: str) -> None:
    stream = make_stream(matrix=matrix)
    with pytest.raises(ColorError, match=r"matrix .* not supported; supported: bt709, bt601"):
        decode_filter(stream)
    with pytest.raises(ColorError, match="matrix"):
        encode_filter(stream, bit_depth=8)


def test_bit_depth_disagreement_is_refused() -> None:
    stream = make_stream(pix_fmt="yuv420p")
    with pytest.raises(ColorError, match="bit depth disagrees"):
        decode_filter(replace(stream, bit_depth=10))
    with pytest.raises(ColorError, match="bit depth disagrees"):
        decode_filter(replace(stream, color=replace(stream.color, bit_depth=10)))
    with pytest.raises(ColorError, match="bit depth disagrees"):
        decode_filter(replace(make_stream(pix_fmt="yuv420p10le"), bit_depth=8))


def test_unsupported_siting_range_and_output_depth_are_refused() -> None:
    with pytest.raises(ColorError, match="chroma siting"):
        decode_filter(make_stream(siting="somewhere"))
    with pytest.raises(ColorError, match="range"):
        decode_filter(make_stream(range_="studio"))
    ten = make_stream(pix_fmt="yuv420p10le")
    with pytest.raises(ColorError, match=r"output bit depth 8 .* 10-bit source"):
        encode_filter(ten, bit_depth=8)  # would truncate 10-bit data (spec 5.2)
    with pytest.raises(ColorError, match="output bit depth 12"):
        encode_pix_fmt(make_stream(), bit_depth=12)
    assert encode_pix_fmt(ten, bit_depth=10) == "yuv420p10le"
    with pytest.raises(ColorError, match="bit depth 16 is not supported"):
        rgb_pix_fmt(16)


def test_hdr_samples_never_reach_the_arguments(sample: Callable[[str], Path]) -> None:
    # The probe refuses HLG/PQ (a fault) and leaves the matrix unknown; the arguments refuse it too.
    for sample_id in ("vid-hlg", "vid-pq"):
        result = probe(sample(sample_id))
        assert any(f.severity == "refuse" for f in result.faults)
        with pytest.raises(ColorError, match="matrix 'unknown'"):
            decode_filter(result.video)


# --- the name table (D55, DR-17) ---------------------------------------------------------------


def test_name_table_values() -> None:
    def desc(p: str, t: str, m: str, r: str) -> ColorDescription:
        return ColorDescription(p, t, m, r, 8, False, None)

    assert ffmpeg_color_names(desc("bt709", "bt709", "bt709", "full")) == {
        "color_primaries": "bt709",
        "color_trc": "bt709",
        "colorspace": "bt709",
        "color_range": "pc",
    }
    assert ffmpeg_color_names(desc("display-p3", "srgb", "bt601", "limited")) == {
        "color_primaries": "smpte432",
        "color_trc": "iec61966-2-1",
        "colorspace": "smpte170m",
        "color_range": "tv",
    }
    assert ffmpeg_color_names(desc("unknown", "unknown", "unknown", "limited")) == {
        "color_range": "tv"
    }
    assert ffmpeg_color_names(desc("bt709", "bt709", "identity", "full"))["colorspace"] == "gbr"


def test_name_table_inverts_the_probes_tables() -> None:
    probe_tables = {
        "color_primaries": probe_module._PRIMARIES,
        "color_trc": probe_module._TRANSFER,
        "colorspace": probe_module._MATRIX,
        "color_range": probe_module._RANGE,
    }
    fields = {
        "color_primaries": ("primaries", ["bt709", "display-p3"]),
        "color_trc": ("transfer", ["bt709", "srgb"]),
        "colorspace": ("matrix", ["bt709", "bt601", "identity"]),
        "color_range": ("range", ["limited", "full"]),
    }
    for key, (attr, values) in fields.items():
        for value in values:
            kwargs = {"primaries": "bt709", "transfer": "bt709", "matrix": "bt709", "range": "full"}
            kwargs[attr] = value
            color = ColorDescription(bit_depth=8, assumed=False, icc_profile=None, **kwargs)
            name = ffmpeg_color_names(color)[key]
            assert probe_tables[key][name] == value


def test_assumed_values_pass_through_the_name_table(sample: Callable[[str], Path]) -> None:
    stream = stream_of(sample, "vid-untagged")
    assert stream.color.assumed
    assert dict(ffmpeg_color_names(stream.color)) == {
        "color_primaries": "bt709",
        "color_trc": "bt709",
        "colorspace": "bt709",
        "color_range": "tv",
    }


# --- D54 consumed, DR-20 item (1) --------------------------------------------------------------


def test_untagged_sample_decodes_as_assumed_bt709_limited(sample: Callable[[str], Path]) -> None:
    result = probe(sample("vid-untagged"))
    assert result.video.color.assumed
    assert (result.video.color.matrix, result.video.color.range) == ("bt709", "limited")
    assert [f.kind for f in result.faults] == ["missing_tags"]
    assert decode_filter(result.video) == expected_decode("gbrp", "tv")
    assert encode_filter(result.video, bit_depth=8) == expected_encode("yuv420p", "tv")


def test_untagged_yuvj_is_full_range_without_a_range_warning() -> None:
    # No tags at all on a yuvj stream: the probe resolves full range (WP3.7 ruling 7.3) and the
    # missing-tags message names the other three fields only; the arguments read the resolved range.
    color = probe_module._resolve_color({"pix_fmt": "yuvj420p"}, "yuvj420p", 8)
    assert color.description.range == "full"
    faults = probe_module._colour_faults(color)
    assert [f.kind for f in faults] == ["missing_tags"]
    assert "range" not in faults[0].message.split("(")[1].split(")")[0]
    stream = replace(make_stream(pix_fmt="yuvj420p"), color=color.description)
    assert stream.color.assumed
    assert decode_filter(stream) == expected_decode("gbrp", "pc")
    assert encode_filter(stream, bit_depth=8) == expected_encode("yuv420p", "pc")


def test_yuvj_with_limited_range_is_refused() -> None:
    # swscale ignores in_range on a yuvj format (it is full range by definition), so a
    # contradictory description would decode differently from how it encodes: refused by name.
    stream = make_stream(pix_fmt="yuvj420p", range_="limited")
    with pytest.raises(ColorError, match=r"yuvj420p.* full-range format"):
        decode_filter(stream)
    with pytest.raises(ColorError, match=r"full-range format"):
        encode_filter(stream, bit_depth=8)
