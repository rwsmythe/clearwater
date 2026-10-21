"""Tests of the photo writer (WP3.6): the PNG, its chunks, ICC, EXIF (D63), provenance, V9, N8.

Written files are verified by readers other than the writer: the FFmpeg CLI for samples, Pillow
for ``eXIf``, a stdlib chunk walker for order and checksums.
"""

from __future__ import annotations

import json
import struct
import subprocess
import zlib
from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from PIL import Image as PILImage

from clearwater.interfaces import FormatError
from clearwater.interfaces.image import ColorDescription, Image
from clearwater.interfaces.photo import PhotoMetadata
from clearwater.interfaces.settings import Settings
from clearwater.io.photo import PhotoWriter, read_photo, write_photo
from clearwater.io.photo import exif as exif_tools
from clearwater.io.photo import png as png_tools
from clearwater.io.photo.writer import built_in_profile
from clearwater.io.video import find_tool
from clearwater.jobs import MediaKind, SafeWrite, plan_output
from fixture_plugin import load_manifest
from spike_io import photo as spike

STILL_IDS = [e["id"] for e in load_manifest()["samples"] if e["group"] == "stills"]


def _color(icc: bytes | None = None, depth: int = 16) -> ColorDescription:
    # no profile means an untagged source (assumed), which the writer leaves without an iCCP
    return ColorDescription("bt709", "srgb", "identity", "full", depth, icc is None, icc)


def _image(pixels: np.ndarray, icc: bytes | None = None, device: str = "cpu") -> Image:
    return Image(pixels=pixels, device=device, color=_color(icc), orientation_applied=True)


def _meta(exif: bytes | None = None) -> PhotoMetadata:
    return PhotoMetadata("jpeg", exif, 1)


def _random(h: int = 12, w: int = 20, seed: int = 0) -> np.ndarray:
    return np.random.default_rng(seed).random((h, w, 3), dtype=np.float32)


def _chunks(path: Path) -> list[tuple[str, bytes]]:
    """Walk a PNG with the stdlib, checking the signature and every CRC."""
    data = path.read_bytes()
    assert data[:8] == png_tools.SIGNATURE
    at, found = 8, []
    while at < len(data):
        (size,) = struct.unpack(">I", data[at : at + 4])
        kind, body = data[at + 4 : at + 8], data[at + 8 : at + 8 + size]
        (crc,) = struct.unpack(">I", data[at + 8 + size : at + 12 + size])
        assert zlib.crc32(kind + body) & 0xFFFFFFFF == crc, f"bad CRC in {kind!r}"
        found.append((kind.decode("latin-1"), body))
        at += 12 + size
    return found


def _ffmpeg_samples(path: Path, pix_fmt: str, shape: tuple[int, int]) -> np.ndarray:
    result = subprocess.run(
        [
            str(find_tool("ffmpeg")),
            "-v",
            "error",
            "-i",
            str(path),
            "-f",
            "rawvideo",
            "-pix_fmt",
            pix_fmt,
            "-",
        ],
        capture_output=True,
        check=True,
    )
    dtype = ">u2" if pix_fmt == "rgb48be" else np.uint8
    return np.frombuffer(result.stdout, dtype=dtype).reshape(*shape, 3)


def _profile(sample: Callable[[str], Path]) -> bytes:
    scan = png_tools.scan_png(sample("png16-gradient-display-p3").read_bytes(), "p3.png")
    assert scan.icc is not None
    return scan.icc


# --- samples as another reader sees them -----------------------------------------------------


@pytest.mark.parametrize("bit_depth", [8, 16])
def test_samples_are_exact_through_the_ffmpeg_cli(
    tmp_path: Path, ffmpeg_tools: None, bit_depth: int
) -> None:
    pixels = _random()
    out = tmp_path / "out.png"
    write_photo(_image(pixels), _meta(), out, bit_depth=bit_depth)
    top = (1 << bit_depth) - 1
    expected = np.rint(pixels.astype(np.float64) * top)
    fmt = "rgb48be" if bit_depth == 16 else "rgb24"
    got = _ffmpeg_samples(out, fmt, pixels.shape[:2])
    assert np.array_equal(got.astype(np.float64), expected)


def test_the_8_bit_file_is_exact_through_pillow(tmp_path: Path) -> None:
    pixels = _random()
    out = tmp_path / "out.png"
    write_photo(_image(pixels), _meta(), out, bit_depth=8)
    with PILImage.open(out) as image:
        assert image.mode == "RGB"
        assert np.array_equal(np.asarray(image), np.rint(pixels * 255).astype(np.uint8))


def test_every_code_value_survives_quantise_and_read_exactly(tmp_path: Path) -> None:
    for bits, top in ((16, 65535), (8, 255)):
        codes = np.arange(top + 1, dtype=np.float64)
        pixels = np.repeat((codes / top).astype(np.float32).reshape(-1, 1, 1), 3, axis=2)
        out = tmp_path / f"all{bits}.png"
        write_photo(_image(pixels), _meta(), out, bit_depth=bits)
        again, _ = read_photo(out)
        assert np.array_equal(
            np.rint(again.pixels.astype(np.float64) * top), codes[:, None, None] + 0 * pixels
        )
        assert np.array_equal(again.pixels, pixels)


def test_quantisation_clips_rounds_to_nearest_and_does_not_dither(tmp_path: Path) -> None:
    pixels = np.array([[[-0.5, 1.5, 0.6 / 255], [0.4 / 255, 254.6 / 255, 0.0]]], dtype=np.float32)
    out = tmp_path / "q.png"
    write_photo(_image(pixels), _meta(), out, bit_depth=8)
    with PILImage.open(out) as image:
        assert np.asarray(image).tolist() == [[[0, 255, 1], [0, 255, 0]]]


# --- chunks ----------------------------------------------------------------------------------


def test_chunk_order_and_checksums_with_everything(
    tmp_path: Path, sample: Callable[[str], Path]
) -> None:
    out = tmp_path / "out.png"
    write_photo(
        _image(_random(), icc=_profile(sample)),
        _meta(spike.source_exif(6, 20, 12)),
        out,
        bit_depth=16,
        provenance={"version": "0.0.0"},
    )
    names = [name for name, _ in _chunks(out)]
    assert names[:4] == ["IHDR", "iCCP", "eXIf", "iTXt"]
    assert names[-1] == "IEND"
    assert set(names[4:-1]) == {"IDAT"}


def test_without_a_profile_or_provenance_those_chunks_are_absent(tmp_path: Path) -> None:
    out = tmp_path / "out.png"
    write_photo(_image(_random()), _meta(), out, bit_depth=8, provenance=None)
    assert [name for name, _ in _chunks(out)] == ["IHDR", "eXIf", "IDAT", "IEND"]


def test_ihdr_states_the_depth_the_size_and_rgb(tmp_path: Path) -> None:
    out = tmp_path / "out.png"
    write_photo(_image(_random(7, 11)), _meta(), out, bit_depth=16)
    width, height, depth, colour, comp, filt, interlace = struct.unpack(
        ">IIBBBBB", _chunks(out)[0][1]
    )
    assert (width, height, depth, colour, comp, filt, interlace) == (11, 7, 16, 2, 0, 0, 0)


def test_the_iccp_profile_is_byte_identical_and_validly_named(
    tmp_path: Path, sample: Callable[[str], Path]
) -> None:
    icc = _profile(sample)
    out = tmp_path / "out.png"
    write_photo(_image(_random(), icc=icc), _meta(), out, bit_depth=16)
    body = dict(_chunks(out))["iCCP"]
    name, rest = body.split(b"\0", 1)
    assert png_tools.keyword_problem(name.decode("latin-1")) is None
    assert rest[0] == 0, "compression method must be 0"
    assert zlib.decompress(rest[1:]) == icc
    again, _ = read_photo(out)
    assert again.color.icc_profile == icc
    assert (again.color.primaries, again.color.transfer) == ("display-p3", "srgb")


def test_a_profile_with_a_bad_description_gets_a_valid_default_name(
    tmp_path: Path, sample: Callable[[str], Path]
) -> None:
    icc = bytearray(_profile(sample))
    start = bytes(icc).index("Clearwater synthetic Display P3".encode("utf-16-be"))
    icc[start : start + 4] = "  ".encode("utf-16-be")  # leading spaces in the description
    out = tmp_path / "out.png"
    write_photo(_image(_random(), icc=bytes(icc)), _meta(), out, bit_depth=8)
    name = dict(_chunks(out))["iCCP"].split(b"\0", 1)[0].decode("latin-1")
    assert name == "ICC profile"


def test_exif_is_readable_by_pillow_and_follows_d63(tmp_path: Path) -> None:
    source = spike.source_exif(6, 96, 64, thumbnail=True)
    out = tmp_path / "out.png"
    write_photo(_image(_random(12, 20)), _meta(source), out, bit_depth=16)
    with PILImage.open(out) as image:
        exif = image.getexif()
        sub = exif.get_ifd(0x8769)
        assert exif[274] == 1
        assert exif[305] == "Clearwater"
        assert (sub[40962], sub[40963]) == (20, 12)
        assert exif[271] == "Apple" and sub[36867] == "2026:10:20 10:00:00"
        assert exif.get_ifd(0x8825)[1] == "N"
    block = dict(_chunks(out))["eXIf"]
    assert not exif_tools.has_thumbnail(block)
    assert block[:4] in (b"II*\x00", b"MM\x00*")


def test_a_source_without_exif_gets_the_minimal_block(tmp_path: Path) -> None:
    out = tmp_path / "out.png"
    write_photo(_image(_random(5, 9)), _meta(None), out, bit_depth=8)
    fields = exif_tools.describe(dict(_chunks(out))["eXIf"])
    assert fields == {
        "IFD0.Orientation": "1",
        "IFD0.Software": "Clearwater",
        "Exif.ExifImageWidth": "9",
        "Exif.ExifImageHeight": "5",
    }


# --- provenance (D91) ------------------------------------------------------------------------


def test_provenance_is_present_and_parseable_when_given(tmp_path: Path) -> None:
    provenance = {"clearwater": "0.1", "settings": {"b": [1, 2.5, None], "a": "é"}}
    out = tmp_path / "out.png"
    write_photo(_image(_random()), _meta(), out, bit_depth=16, provenance=provenance)
    body = dict(_chunks(out))["iTXt"]
    keyword, rest = body.split(b"\0", 1)
    assert keyword == b"clearwater-provenance"
    flag, method = rest[0], rest[1]
    assert (flag, method) == (0, 0)
    language, rest = rest[2:].split(b"\0", 1)
    translated, text = rest.split(b"\0", 1)
    assert language == b"" and translated == b""
    assert json.loads(text.decode("utf-8")) == provenance
    with PILImage.open(out) as image:
        assert json.loads(image.text["clearwater-provenance"]) == provenance


def test_provenance_refuses_non_string_keys_nan_and_unserialisable_values(tmp_path: Path) -> None:
    out = tmp_path / "out.png"
    writer = PhotoWriter()
    for bad, error in (
        ({"a": {1: "x"}}, FormatError),
        ({"a": float("nan")}, ValueError),
        ({"a": object()}, ValueError),
    ):
        with pytest.raises(error):
            writer.write(_image(_random()), _meta(), out, bit_depth=8, provenance=bad)
        assert not out.exists()


# --- refusals --------------------------------------------------------------------------------


@pytest.mark.parametrize("bad", [0, 1, 10, 12, 24, 32, -8])
def test_any_other_bit_depth_is_a_value_error(tmp_path: Path, bad: int) -> None:
    out = tmp_path / "out.png"
    with pytest.raises(ValueError, match="8 or 16"):
        write_photo(_image(_random()), _meta(), out, bit_depth=bad)
    assert not out.exists()


def test_a_gpu_image_is_refused_naming_the_device(tmp_path: Path) -> None:
    out = tmp_path / "out.png"
    with pytest.raises(ValueError, match="cuda:0"):
        write_photo(_image(_random(), device="cuda:0"), _meta(), out, bit_depth=8)
    assert not out.exists()


@pytest.mark.parametrize("name", ["out.jpg", "out", "out.png.tmp", "out.tif"])
def test_a_non_png_suffix_is_refused_and_nothing_is_written(tmp_path: Path, name: str) -> None:
    with pytest.raises(ValueError, match=r"\.png"):
        write_photo(_image(_random()), _meta(), tmp_path / name, bit_depth=8)
    assert list(tmp_path.iterdir()) == []


def test_an_upper_case_png_suffix_is_accepted(tmp_path: Path) -> None:
    write_photo(_image(_random()), _meta(), tmp_path / "OUT.PNG", bit_depth=8)
    assert (tmp_path / "OUT.PNG").exists()


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
def test_non_finite_samples_are_a_value_error_before_the_file_exists(
    tmp_path: Path, value: float
) -> None:
    pixels = _random()
    pixels[3, 4, 1] = value
    with pytest.raises(ValueError, match="NaN"):
        write_photo(_image(pixels), _meta(), tmp_path / "out.png", bit_depth=16)
    assert list(tmp_path.iterdir()) == []


def test_wrong_pixel_types_and_shapes_are_value_errors(tmp_path: Path) -> None:
    for bad in (
        _random().astype(np.float64),
        _random()[:, :, :2],
        _random()[:, :, 0],
        np.zeros((0, 4, 3), dtype=np.float32),
    ):
        with pytest.raises(ValueError):
            write_photo(_image(bad), _meta(), tmp_path / "out.png", bit_depth=8)
    assert list(tmp_path.iterdir()) == []


def test_only_the_named_file_is_written(tmp_path: Path) -> None:
    folder = tmp_path / "out"
    folder.mkdir()
    write_photo(_image(_random()), _meta(), folder / "only.png", bit_depth=16, provenance={"a": 1})
    assert [p.name for p in folder.iterdir()] == ["only.png"]
    assert list(tmp_path.iterdir()) == [folder]


def test_a_large_image_streams_in_several_idat_chunks(tmp_path: Path) -> None:
    pixels = np.random.default_rng(1).random((700, 900, 3), dtype=np.float32)
    out = tmp_path / "big.png"
    write_photo(_image(pixels), _meta(), out, bit_depth=16)
    idats = [body for name, body in _chunks(out) if name == "IDAT"]
    assert len(idats) >= 2 and all(len(b) <= png_tools._IDAT_SIZE for b in idats)
    again, _ = read_photo(out)
    assert np.array_equal(
        np.rint(again.pixels.astype(np.float64) * 65535), np.rint(pixels.astype(np.float64) * 65535)
    )


# --- V9 input/output legs --------------------------------------------------------------------


@pytest.mark.parametrize("sample_id", STILL_IDS)
def test_read_write_16_bit_read_is_within_v9_for_every_sample(
    tmp_path: Path, sample: Callable[[str], Path], sample_id: str
) -> None:
    image, meta = read_photo(sample(sample_id))
    out = tmp_path / "rt.png"
    write_photo(image, meta, out, bit_depth=16)
    again, again_meta = read_photo(out)
    diff = np.abs(again.pixels.astype(np.float64) - image.pixels.astype(np.float64))
    assert diff.max() <= 2 / 255 and diff.mean() <= 0.2 / 255  # AD-11 V9
    assert diff.max() <= 0.5 / 65535 + 1e-7, "the only loss is the 16-bit quantisation"
    if image.color.bit_depth in (8, 16):
        assert np.array_equal(again.pixels, image.pixels), "an 8- or 16-bit source is exact"
    chosen = built_in_profile(image.color)  # a tagged source with no ICC gets a built-in (D53)
    assert again.color.icc_profile == (image.color.icc_profile if chosen is None else chosen[1])
    assert (again.color.primaries, again.color.transfer) == (
        image.color.primaries,
        image.color.transfer,
    )
    assert again_meta.orientation == 1
    assert again_meta.exif is not None, "the written PNG always carries the D63 EXIF"


@pytest.mark.parametrize(
    "sample_id", ["png8-gradient-srgb", "tiff8-lowred-none", "heic8-uniform-none"]
)
def test_an_8_bit_source_written_at_8_bit_is_exact(
    tmp_path: Path, sample: Callable[[str], Path], sample_id: str
) -> None:
    image, meta = read_photo(sample(sample_id))
    out = tmp_path / "rt8.png"
    write_photo(image, meta, out, bit_depth=8)
    assert np.array_equal(read_photo(out)[0].pixels, image.pixels)


# --- the product composition with SafeWrite (X-B1, N8) ----------------------------------------


def _plan(source: Path) -> Any:
    return plan_output(source, Settings(), MediaKind.PHOTO)


def test_the_safe_write_composition_commits_and_leaves_the_source_untouched(
    tmp_path: Path, sample: Callable[[str], Path]
) -> None:
    source = tmp_path / "IMG_0001.heic"
    source.write_bytes(sample("heic-ad24-both").read_bytes())
    before = (source.read_bytes(), source.stat().st_mtime_ns)
    image, meta = read_photo(source)
    plan = _plan(source)
    with SafeWrite(plan) as w:
        PhotoWriter().write(image, meta, w.temp_path, bit_depth=16, provenance=None)
        final = w.commit()
    assert final.suffix == ".png" and final.parent == tmp_path
    assert sorted(p.name for p in tmp_path.iterdir()) == sorted([source.name, final.name])
    assert (source.read_bytes(), source.stat().st_mtime_ns) == before
    assert read_photo(final)[0].pixels.shape == image.pixels.shape


def test_an_exception_inside_write_leaves_no_partial_and_no_final(
    tmp_path: Path, sample: Callable[[str], Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "IMG_0002.jpg"
    source.write_bytes(sample("jpeg-gradient-srgb").read_bytes())
    before = (source.read_bytes(), source.stat().st_mtime_ns)
    image, meta = read_photo(source)
    plan = _plan(source)
    seen: list[int] = []
    real = png_tools._quantise

    def failing(block: np.ndarray, depth: int) -> Any:
        seen.append(len(list(tmp_path.iterdir())))
        raise RuntimeError("the disk went away")

    monkeypatch.setattr(png_tools, "_quantise", failing)
    with pytest.raises(RuntimeError, match="disk went away"), SafeWrite(plan) as w:
        PhotoWriter().write(image, meta, w.temp_path, bit_depth=16, provenance=None)
        w.commit()
    monkeypatch.setattr(png_tools, "_quantise", real)
    assert seen == [2], "the partial file existed (source plus temporary) when the write failed"
    assert [p.name for p in tmp_path.iterdir()] == [source.name]
    assert not plan.path.exists()
    assert (source.read_bytes(), source.stat().st_mtime_ns) == before
