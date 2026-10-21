"""Tests of the photo reader (WP3.6): every WP2.3 still against its manifest ``expect``.

Covers the metadata, colour and orientation each sample promises (V5), the AD-24 HEIC cases, 16-
and 10-bit precision, TIFF at every depth through ``tifffile`` (built under ``tmp_path``: WP2.3
has no 16-bit TIFF), the DNG and truncation refusals (V6, spec 5.4) and the untagged defaults.
"""

from __future__ import annotations

import dataclasses
import hashlib
import io
import struct
import zlib
from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np
import pillow_heif
import pytest
import tifffile
from PIL import Image

from clearwater.interfaces.photo import PhotoSink, PhotoSource
from clearwater.io.photo import PhotoReader, PhotoReadError, PhotoWriter, read_photo
from clearwater.io.photo import exif as exif_tools
from clearwater.io.photo import png as png_tools
from clearwater.io.photo import reader as reader_module
from clearwater.io.photo.orientation import apply_orientation
from clearwater.io.photo.srgb_profile import srgb_profile
from fixture_plugin import load_manifest
from fixtures import stills
from spike_io import photo as spike

_MANIFEST = load_manifest()
STILL_IDS = [e["id"] for e in _MANIFEST["samples"] if e["group"] == "stills"]
LOSSLESS_IDS = [
    i for i in STILL_IDS if i.startswith(("png16-", "png8-", "tiff8-")) and "orient" not in i
]
ORIENT_IDS = [i for i in STILL_IDS if i.startswith("jpeg-orient-")]
AD24_IDS = [i for i in STILL_IDS if i.startswith("heic-ad24-")]
DNG_IDS = ["dng-by-extension", "dng-by-tag", "dng-extension-only"]


def _entry(sample_id: str) -> dict[str, Any]:
    return next(e for e in _MANIFEST["samples"] if e["id"] == sample_id)


def _upright(scene: str) -> np.ndarray:
    width, height = (stills.WIDTH, stills.HEIGHT)
    return (
        spike.upright_image(8, width, height)
        if scene == "landscape"
        else spike.upright_image(8, height, width)
    )


def _mean_abs(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.abs(a.astype(np.float64) - b.astype(np.float64)).mean())


def test_the_classes_satisfy_the_if6_protocols() -> None:
    assert isinstance(PhotoReader(), PhotoSource)
    assert isinstance(PhotoWriter(), PhotoSink)


@pytest.mark.parametrize("sample_id", STILL_IDS)
def test_every_still_meets_its_manifest_expectation(
    sample: Callable[[str], Path], sample_id: str
) -> None:
    entry = _entry(sample_id)
    expect = entry["expect"]["photo"]
    facts = entry["facts"]
    image, meta = read_photo(sample(sample_id))
    # metadata
    assert meta.source_format == expect["metadata"]["source_format"]
    assert (meta.exif is not None) == (expect["metadata"]["exif"] == "present")
    assert meta.orientation == expect["metadata"]["orientation"]
    if meta.exif is not None:
        assert meta.exif[:4] in (b"II*\x00", b"MM\x00*")
    # image and colour
    want = expect["image"]
    assert image.orientation_applied is want["orientation_applied"]
    assert image.device == "cpu"
    assert image.pixels.dtype == np.float32 and image.pixels.ndim == 3
    assert image.pixels.shape[2] == 3
    assert float(image.pixels.min()) >= 0.0 and float(image.pixels.max()) <= 1.0
    color = image.color
    assert (color.matrix, color.range, color.bit_depth) == (
        want["color"]["matrix"],
        want["color"]["range"],
        want["color"]["bit_depth"],
    )
    for key in ("primaries", "transfer"):
        if key in want["color"]:
            assert getattr(color, key) == want["color"][key]
    if want["color"]["icc_profile"] is None and meta.source_format == "heic":
        # The manifest records the file (no ICC profile, an nclx box). By the CHARC ruling of
        # 2026-10-20 the reader gives such a BT.709/sRGB file the built-in sRGB profile (D53).
        assert color.icc_profile == srgb_profile()
    elif want["color"]["icc_profile"] is None:
        assert color.icc_profile is None
    else:
        assert color.icc_profile is not None
        assert hashlib.md5(color.icc_profile).hexdigest() == facts["icc_md5"]
    # shape: the stored size, turned by whatever orientation was applied
    stored = (
        (facts["stored_width"], facts["stored_height"])
        if "stored_width" in facts
        else (
            facts["width"],
            facts["height"],
        )
    )
    height, width = image.pixels.shape[:2]
    assert {width, height} == set(stored)


@pytest.mark.parametrize("sample_id", LOSSLESS_IDS)
def test_lossless_samples_read_exactly_at_their_own_precision(
    sample: Callable[[str], Path], sample_id: str
) -> None:
    facts = _entry(sample_id)["facts"]
    bits = facts["bit_depth"]
    reference = stills.quantize(stills.unit_content(facts["content"]), bits)
    image, _ = read_photo(sample(sample_id))
    top = np.float32(255 if bits == 8 else 65535)
    assert np.array_equal(image.pixels, reference.astype(np.float32) / top)


@pytest.mark.parametrize("sample_id", [i for i in LOSSLESS_IDS if i.startswith("png16-")])
def test_a_16_bit_sample_is_not_read_as_8_bit(
    sample: Callable[[str], Path], sample_id: str
) -> None:
    image, _ = read_photo(sample(sample_id))
    codes = np.rint(image.pixels.astype(np.float64) * 65535)
    if _entry(sample_id)["facts"]["content"] != "uniform":
        assert (codes % 257 != 0).any(), "every sample is an 8-bit value widened: 8-bit read"
    assert image.color.bit_depth == 16


@pytest.mark.parametrize("sample_id", ORIENT_IDS)
def test_orientation_samples_come_out_upright(
    sample: Callable[[str], Path], sample_id: str
) -> None:
    entry = _entry(sample_id)
    image, meta = read_photo(sample(sample_id))
    tag = entry["facts"]["exif_orientation"]
    assert meta.orientation == tag
    upright = _upright(entry["facts"]["scene"])
    got = np.rint(image.pixels * 255)
    assert got.shape == upright.shape
    assert _mean_abs(got, upright) < 3.0
    # every other pose of the same image is clearly different (the check can fail)
    others = [
        apply_orientation(upright, k)
        for k in range(2, 9)
        if apply_orientation(upright, k).shape == upright.shape
    ]
    assert all(_mean_abs(got, o) > 10.0 for o in others if not np.array_equal(o, upright))


@pytest.mark.parametrize("sample_id", AD24_IDS)
def test_the_four_heic_layouts_rotate_exactly_once(
    sample: Callable[[str], Path], sample_id: str
) -> None:
    image, meta = read_photo(sample(sample_id))
    expected_tag = _entry(sample_id)["expect"]["photo"]["metadata"]["orientation"]
    assert meta.orientation == expected_tag
    upright = _upright("landscape")
    got = np.rint(image.pixels * 255)
    assert got.shape == upright.shape
    assert _mean_abs(got, upright) < 6.0, "the HEIC is not upright"
    for k in range(2, 9):
        other = apply_orientation(upright, k)
        if other.shape == upright.shape:
            assert _mean_abs(got, other) > 10.0


def test_the_ten_bit_samples_are_normalised_by_their_true_depth(
    sample: Callable[[str], Path],
) -> None:
    image, _ = read_photo(sample("heic10-uniform-srgb"))
    assert image.color.bit_depth == 10
    facts = _entry("heic10-uniform-srgb")["facts"]
    reference = stills.unit_content(facts["content"])
    assert _mean_abs(image.pixels, reference) < 0.01


def test_a_ten_bit_heic_reaches_one_at_its_maximum_code(tmp_path: Path) -> None:
    white = np.full((16, 16, 3), 1023, dtype=np.uint16)
    path = tmp_path / "white10.heic"
    pillow_heif.encode(
        "RGB;16", (16, 16), (white << 6).tobytes(), str(path), quality=-1, chroma=444
    )
    image, _ = read_photo(path)
    assert image.color.bit_depth == 10
    assert float(image.pixels.max()) == 1.0
    black = np.zeros((16, 16, 3), dtype=np.uint16)
    path = tmp_path / "black10.heic"
    pillow_heif.encode(
        "RGB;16", (16, 16), (black << 6).tobytes(), str(path), quality=-1, chroma=444
    )
    assert float(read_photo(path)[0].pixels.min()) == 0.0


# --- TIFF at every depth (tifffile; built here, WP2.3 has no 16-bit TIFF) -------------------


def _rgb16() -> np.ndarray:
    rng = np.random.default_rng(5)
    pixels = rng.integers(0, 65536, (24, 40, 3), dtype=np.uint16)
    pixels[0, 0] = 0
    pixels[0, 1] = 65535
    return pixels


def _write_tiff(path: Path, pixels: np.ndarray, **kwargs: Any) -> None:
    tifffile.imwrite(path, pixels, photometric="rgb", **kwargs)


@pytest.mark.parametrize(
    "kwargs",
    [
        {},
        {"compression": "zlib"},
        {"compression": "zlib", "predictor": True},
        {"tile": (16, 16)},
        {"tile": (16, 16), "compression": "zlib", "predictor": True},
    ],
    ids=["none", "deflate", "deflate-predictor", "tiled", "tiled-deflate-predictor"],
)
def test_a_16_bit_rgb_tiff_survives_at_full_precision(
    tmp_path: Path, kwargs: dict[str, Any]
) -> None:
    pixels = _rgb16()
    path = tmp_path / "rgb16.tif"
    _write_tiff(path, pixels, **kwargs)
    image, meta = read_photo(path)
    assert meta.source_format == "tiff"
    assert image.color.bit_depth == 16
    assert np.array_equal(image.pixels, pixels.astype(np.float32) / np.float32(65535))
    assert float(image.pixels[0, 0].max()) == 0.0 and float(image.pixels[0, 1].min()) == 1.0


def test_a_planar_16_bit_tiff_reads(tmp_path: Path) -> None:
    pixels = _rgb16()
    path = tmp_path / "planar.tif"
    tifffile.imwrite(path, pixels.transpose(2, 0, 1), photometric="rgb", planarconfig="separate")
    image, _ = read_photo(path)
    assert np.array_equal(image.pixels, pixels.astype(np.float32) / np.float32(65535))


def _packbits_literal(data: bytes) -> bytes:
    """PackBits-encode ``data`` as literal runs only (valid, if not compact)."""
    out = bytearray()
    for start in range(0, len(data), 128):
        run = data[start : start + 128]
        out += bytes([len(run) - 1]) + run
    return bytes(out)


def _baseline_tiff(pixels: np.ndarray, compression: int, strips: list[bytes]) -> bytes:
    """Write a little-endian baseline RGB TIFF by hand, one strip per row group.

    Independent of ``tifffile``, so the reader is checked against a second writer.
    """
    height, width = pixels.shape[:2]
    bits = pixels.dtype.itemsize * 8
    entries = 9
    ifd_size = 2 + 12 * entries + 4
    bps_at = 8 + ifd_size
    data_at = bps_at + 6
    offsets, at = [], data_at
    for strip in strips:
        offsets.append(at)
        at += len(strip)
    table_at = at
    rows_per_strip = -(-height // len(strips))

    def entry(tag: int, kind: int, count: int, value: int) -> bytes:
        return struct.pack("<HHII", tag, kind, count, value)

    one = len(strips) == 1
    tags = [
        entry(256, 4, 1, width),
        entry(257, 4, 1, height),
        entry(258, 3, 3, bps_at),
        entry(259, 3, 1, compression),
        entry(262, 3, 1, 2),
        entry(273, 4, len(strips), offsets[0] if one else table_at),
        entry(277, 3, 1, 3),
        entry(278, 4, 1, rows_per_strip),
        entry(279, 4, len(strips), len(strips[0]) if one else table_at + 4 * len(strips)),
    ]
    body = struct.pack("<2sHI", b"II", 42, 8) + struct.pack("<H", entries) + b"".join(tags)
    body += struct.pack("<I", 0) + struct.pack("<3H", bits, bits, bits) + b"".join(strips)
    if not one:
        body += struct.pack(f"<{len(strips)}I", *offsets)
        body += struct.pack(f"<{len(strips)}I", *[len(strip) for strip in strips])
    return body


def test_a_hand_written_uncompressed_tiff_agrees_with_the_reader(tmp_path: Path) -> None:
    pixels = _rgb16()
    raw = pixels.astype("<u2").tobytes()
    path = tmp_path / "hand.tif"
    path.write_bytes(_baseline_tiff(pixels, 1, [raw]))
    image, _ = read_photo(path)
    assert np.array_equal(image.pixels, pixels.astype(np.float32) / np.float32(65535))


def test_packbits_16_bit_tiffs_read_in_several_strips(tmp_path: Path) -> None:
    pixels = _rgb16()
    rows = [pixels[y : y + 6].astype("<u2").tobytes() for y in range(0, 24, 6)]
    path = tmp_path / "pb.tif"
    path.write_bytes(_baseline_tiff(pixels, 32773, [_packbits_literal(r) for r in rows]))
    image, _ = read_photo(path)
    assert np.array_equal(image.pixels, pixels.astype(np.float32) / np.float32(65535))


@pytest.mark.parametrize(
    ("code", "word"),
    [(5, "LZW"), (7, "JPEG"), (50000, "ZSTD"), (34712, "JPEG2000"), (12345, "12345")],
)
def test_undecoded_tiff_compressions_are_refused_by_name(
    tmp_path: Path, code: int, word: str
) -> None:
    pixels = (_rgb16() >> 8).astype(np.uint8)
    path = tmp_path / "c.tif"
    path.write_bytes(_baseline_tiff(pixels, code, [pixels.tobytes()]))
    with pytest.raises(PhotoReadError) as caught:
        read_photo(path)
    assert caught.value.kind == "unsupported"
    assert word.upper() in str(caught.value).upper() and "c.tif" in str(caught.value)


def test_a_16_bit_tiff_with_an_icc_profile_and_an_orientation_tag(
    tmp_path: Path, sample: Callable[[str], Path]
) -> None:
    icc = png_tools.scan_png(sample("png16-gradient-display-p3").read_bytes(), "x").icc
    assert icc is not None
    pixels = _rgb16()
    path = tmp_path / "tagged.tif"
    _write_tiff(
        path,
        pixels,
        extratags=[(34675, "B", len(icc), icc, True), (274, "H", 1, 6, True)],
    )
    image, meta = read_photo(path)
    assert meta.orientation == 6
    assert image.color.icc_profile == icc
    assert (image.color.primaries, image.color.transfer) == ("display-p3", "srgb")
    expected = apply_orientation(pixels, 6).astype(np.float32) / np.float32(65535)
    assert np.array_equal(image.pixels, expected)


def test_tiff_exif_keeps_descriptive_fields_and_drops_structure(tmp_path: Path) -> None:
    pixels = _rgb16()
    path = tmp_path / "exif.tif"
    _write_tiff(path, pixels, extratags=[(271, "s", 0, "MakerCo", True), (274, "H", 1, 3, True)])
    _, meta = read_photo(path)
    assert meta.exif is not None and meta.orientation == 3
    fields = exif_tools.describe(meta.exif)
    assert fields["IFD0.Make"] == "MakerCo"
    assert fields["IFD0.Orientation"] == "3"
    assert not any("StripOffsets" in k or "ImageWidth" in k for k in fields)


def test_unsupported_tiff_kinds_are_refused(tmp_path: Path) -> None:
    path = tmp_path / "float.tif"
    tifffile.imwrite(path, np.zeros((8, 8, 3), dtype=np.float32), photometric="rgb")
    with pytest.raises(PhotoReadError) as caught:
        read_photo(path)
    assert caught.value.kind == "unsupported"
    path = tmp_path / "cmyk.tif"
    tifffile.imwrite(path, np.zeros((8, 8, 4), dtype=np.uint8), photometric="separated")
    with pytest.raises(PhotoReadError) as caught:
        read_photo(path)
    assert caught.value.kind == "unsupported"


def test_grey_palette_and_rgba_tiffs_become_rgb(tmp_path: Path) -> None:
    grey = (np.arange(48, dtype=np.uint16) * 1000).reshape(6, 8)
    tifffile.imwrite(tmp_path / "g.tif", grey, photometric="minisblack")
    image, _ = read_photo(tmp_path / "g.tif")
    assert np.array_equal(image.pixels[:, :, 0], grey.astype(np.float32) / np.float32(65535))
    assert np.array_equal(image.pixels[:, :, 0], image.pixels[:, :, 2])
    rgba = np.dstack([_rgb16()[:6, :8], np.full((6, 8), 7, dtype=np.uint16)])
    tifffile.imwrite(tmp_path / "a.tif", rgba, photometric="rgb", extrasamples=["unassalpha"])
    image, _ = read_photo(tmp_path / "a.tif")
    assert np.array_equal(image.pixels, rgba[:, :, :3].astype(np.float32) / np.float32(65535))
    index = np.arange(48, dtype=np.uint8).reshape(6, 8)
    colormap = (np.arange(768).reshape(3, 256) * 80 % 65536).astype(np.uint16)
    tifffile.imwrite(tmp_path / "p.tif", index, photometric="palette", colormap=colormap)
    image, _ = read_photo(tmp_path / "p.tif")
    assert image.color.bit_depth == 8
    assert np.rint(image.pixels[0, 1, 0] * 255) == (colormap[0, 1] >> 8)


def test_a_multi_page_tiff_reads_page_one_with_a_warning(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    first, second = _rgb16(), _rgb16()[::-1].copy()
    with tifffile.TiffWriter(tmp_path / "m.tif") as writer:
        writer.write(first, photometric="rgb")
        writer.write(second, photometric="rgb")
    with caplog.at_level("WARNING", logger="clearwater.io.photo.tiff"):
        image, _ = read_photo(tmp_path / "m.tif")
    assert np.array_equal(image.pixels, first.astype(np.float32) / np.float32(65535))
    assert "2 pages" in caplog.text


# --- PNG variants ---------------------------------------------------------------------------


def _png16(pixels: np.ndarray, extra: bytes = b"", interlace: int = 0) -> bytes:
    height, width = pixels.shape[:2]
    rows = np.zeros((height, 1 + width * 6), dtype=np.uint8)
    rows[:, 1:] = pixels.astype(">u2").view(np.uint8).reshape(height, width * 6)
    return (
        png_tools.SIGNATURE
        + png_tools.chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 16, 2, 0, 0, interlace))
        + extra
        + png_tools.chunk(b"IDAT", zlib.compress(rows.tobytes()))
        + png_tools.chunk(b"IEND", b"")
    )


def test_an_interlaced_16_bit_png_is_refused_by_name(tmp_path: Path) -> None:
    path = tmp_path / "adam7.png"
    path.write_bytes(_png16(_rgb16()[:8, :8], interlace=1))
    with pytest.raises(PhotoReadError) as caught:
        read_photo(path)
    assert caught.value.kind == "unsupported"
    assert "adam7.png" in str(caught.value) and "Adam7" in str(caught.value)


def test_an_8_bit_png_reads_through_pillow(tmp_path: Path) -> None:
    pixels = (_rgb16() >> 8).astype(np.uint8)
    buffer = io.BytesIO()
    Image.fromarray(pixels).save(buffer, "PNG")
    path = tmp_path / "a8.png"
    path.write_bytes(buffer.getvalue())
    image, _ = read_photo(path)
    assert np.array_equal(np.rint(image.pixels * 255).astype(np.uint8), pixels)


def test_a_png_with_an_srgb_chunk_is_explicit_srgb(tmp_path: Path) -> None:
    path = tmp_path / "srgb.png"
    path.write_bytes(_png16(_rgb16()[:8, :8], extra=png_tools.chunk(b"sRGB", b"\0")))
    image, _ = read_photo(path)
    assert (image.color.primaries, image.color.transfer) == ("bt709", "srgb")
    assert image.color.assumed is False and image.color.icc_profile is None


def test_a_png_with_an_exif_orientation_is_rotated_once(tmp_path: Path) -> None:
    pixels = _rgb16()[:12, :20]
    source = Image.Exif()
    source[274] = 6
    chunk = png_tools.chunk(b"eXIf", exif_tools.strip_prefix(source.tobytes()))
    path = tmp_path / "o6.png"
    path.write_bytes(_png16(pixels, extra=chunk))
    image, meta = read_photo(path)
    assert meta.orientation == 6
    assert np.array_equal(image.pixels, apply_orientation(pixels, 6).astype(np.float32) / 65535)


def test_grey_and_palette_8_bit_pngs_become_rgb(tmp_path: Path) -> None:
    grey = Image.fromarray(np.arange(48, dtype=np.uint8).reshape(6, 8) * 5, "L")
    grey.save(tmp_path / "g.png")
    image, _ = read_photo(tmp_path / "g.png")
    assert image.color.bit_depth == 8
    assert np.array_equal(image.pixels[:, :, 0], image.pixels[:, :, 1])
    rgba = Image.new("RGBA", (6, 6), (10, 20, 30, 128))
    rgba.save(tmp_path / "a.png")
    image, _ = read_photo(tmp_path / "a.png")
    assert np.rint(image.pixels[0, 0] * 255).tolist() == [10, 20, 30]


# --- Untagged and colour --------------------------------------------------------------------


def test_an_untagged_photo_is_read_as_srgb_and_flagged_assumed(
    sample: Callable[[str], Path],
) -> None:
    for sample_id in ("png8-uniform-none", "png16-uniform-none", "tiff8-uniform-none"):
        image, _ = read_photo(sample(sample_id))
        assert (image.color.primaries, image.color.transfer) == ("bt709", "srgb")
        assert image.color.assumed is True
        assert image.color.icc_profile is None


def test_a_heic_with_nclx_colour_data_is_tagged_not_assumed(
    sample: Callable[[str], Path],
) -> None:
    image, _ = read_photo(sample("heic8-uniform-none"))
    assert (image.color.primaries, image.color.transfer) == ("bt709", "srgb")
    assert image.color.assumed is False
    assert (
        image.color.icc_profile == srgb_profile()
    )  # the built-in profile, CHARC ruling 2026-10-20


def test_a_profile_is_carried_byte_identical_and_never_applied(
    sample: Callable[[str], Path],
) -> None:
    p3, _ = read_photo(sample("png16-gradient-display-p3"))
    srgb, _ = read_photo(sample("png16-gradient-srgb"))
    assert p3.color.icc_profile != srgb.color.icc_profile
    assert np.array_equal(p3.pixels, srgb.pixels), "profiles differ but pixels must not"


# --- Refusals -------------------------------------------------------------------------------


@pytest.mark.parametrize("sample_id", DNG_IDS)
def test_dng_samples_are_refused_with_the_d116_message(
    sample: Callable[[str], Path], sample_id: str
) -> None:
    path = sample(sample_id)
    with pytest.raises(PhotoReadError) as caught:
        read_photo(path)
    assert caught.value.kind == "unsupported"
    assert path.name in str(caught.value)
    assert "DNG" in str(caught.value) and "ProRAW" in str(caught.value)


def test_the_dng_tag_is_found_by_content_in_a_file_with_another_extension(
    sample: Callable[[str], Path], tmp_path: Path
) -> None:
    copy = tmp_path / "renamed.tiff"
    copy.write_bytes(sample("dng-by-tag").read_bytes())
    with pytest.raises(PhotoReadError, match="DNG"):
        read_photo(copy)
    upper = tmp_path / "SHOUT.DNG"
    upper.write_bytes(sample("png8-uniform-none").read_bytes())
    with pytest.raises(PhotoReadError, match="DNG"):
        read_photo(upper)


def test_a_tiff_without_the_dng_tag_is_not_refused(sample: Callable[[str], Path]) -> None:
    assert read_photo(sample("tiff8-uniform-none"))[1].source_format == "tiff"


@pytest.mark.parametrize(
    ("sample_id", "keep"),
    [
        ("jpeg-uniform-none", 0.5),
        ("png8-gradient-none", 0.5),
        ("png16-gradient-srgb", 0.5),
        ("heic8-gradient-none", 0.7),
        ("tiff8-gradient-none", 0.7),
    ],
)
def test_a_truncated_file_is_refused_not_half_read(
    sample: Callable[[str], Path], tmp_path: Path, sample_id: str, keep: float
) -> None:
    source = sample(sample_id)
    data = source.read_bytes()
    cut = tmp_path / f"cut{source.suffix}"
    cut.write_bytes(data[: int(len(data) * keep)])
    with pytest.raises(PhotoReadError) as caught:
        read_photo(cut)
    assert caught.value.kind == "unreadable"
    assert cut.name in str(caught.value)


def test_a_missing_empty_and_unknown_file_each_have_a_kind_and_the_name(tmp_path: Path) -> None:
    with pytest.raises(PhotoReadError) as missing:
        read_photo(tmp_path / "nope.jpg")
    assert missing.value.kind == "unreadable" and "nope.jpg" in str(missing.value)
    (tmp_path / "empty.png").write_bytes(b"")
    with pytest.raises(PhotoReadError) as empty:
        read_photo(tmp_path / "empty.png")
    assert empty.value.kind == "unreadable"
    (tmp_path / "notes.txt").write_text("hello world, not a photo at all")
    with pytest.raises(PhotoReadError) as unknown:
        read_photo(tmp_path / "notes.txt")
    assert unknown.value.kind == "unsupported" and "notes.txt" in str(unknown.value)
    with pytest.raises(PhotoReadError) as folder:
        read_photo(tmp_path)
    assert folder.value.kind == "unreadable"


def test_detection_is_by_content_not_extension(
    sample: Callable[[str], Path], tmp_path: Path
) -> None:
    disguised = tmp_path / "really-a-png.jpg"
    disguised.write_bytes(sample("png8-uniform-none").read_bytes())
    assert read_photo(disguised)[1].source_format == "png"


def test_cmyk_jpeg_is_unsupported(tmp_path: Path) -> None:
    Image.new("CMYK", (8, 8)).save(tmp_path / "c.jpg")
    with pytest.raises(PhotoReadError) as caught:
        read_photo(tmp_path / "c.jpg")
    assert caught.value.kind == "unsupported"


def test_too_many_pixels_are_refused_before_decoding(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from clearwater.io.photo import reader

    monkeypatch.setattr(reader, "MAX_PIXELS", 100)
    Image.new("RGB", (20, 20)).save(tmp_path / "big.png")
    with pytest.raises(PhotoReadError) as caught:
        read_photo(tmp_path / "big.png")
    assert caught.value.kind == "unsupported"


def test_the_source_file_is_never_modified(sample: Callable[[str], Path]) -> None:
    path = sample("heic-ad24-both")
    before = (path.read_bytes(), path.stat().st_mtime_ns)
    read_photo(path)
    assert (path.read_bytes(), path.stat().st_mtime_ns) == before


def test_a_primary_size_that_disagrees_with_ispe_is_refused(
    sample: Callable[[str], Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    path = sample("heic-ad24-both")
    real = reader_module.read_layout
    monkeypatch.setattr(
        reader_module, "read_layout", lambda data: dataclasses.replace(real(data), ispe=(5, 5))
    )
    with pytest.raises(PhotoReadError) as caught:
        read_photo(path)
    assert caught.value.kind == "unreadable" and "does not match" in str(caught.value)


def test_a_heic_whose_layout_cannot_be_established_is_unreadable(tmp_path: Path) -> None:
    path = tmp_path / "bare.heic"
    path.write_bytes(struct.pack(">I", 24) + b"ftypheic" + b"\x00\x00\x00\x00heic" + b"mif1")
    with pytest.raises(PhotoReadError) as caught:
        read_photo(path)
    assert caught.value.kind == "unreadable" and "bare.heic" in str(caught.value)


def test_a_multi_picture_jpeg_reads_its_first_image_as_jpeg(tmp_path: Path) -> None:
    first, second = Image.new("RGB", (32, 24), (10, 200, 30)), Image.new("RGB", (16, 12))
    exif = Image.Exif()
    exif[274] = 6
    path = tmp_path / "mpo.jpg"
    first.save(path, format="MPO", save_all=True, append_images=[second], exif=exif.tobytes())
    image, meta = read_photo(path)
    assert meta.source_format == "jpeg" and meta.orientation == 6
    assert image.pixels.shape == (32, 24, 3)


def test_a_heic_with_alpha_drops_it(tmp_path: Path) -> None:
    rgba = np.zeros((16, 16, 4), dtype=np.uint8)
    rgba[..., 0], rgba[..., 3] = 200, 100
    path = tmp_path / "alpha.heic"
    pillow_heif.encode("RGBA", (16, 16), rgba.tobytes(), str(path), quality=90)
    image, _ = read_photo(path)
    assert image.pixels.shape == (16, 16, 3)
    assert abs(float(image.pixels[0, 0, 0]) * 255 - 200) < 3


def test_a_twelve_bit_heic_is_refused_as_unsupported(tmp_path: Path) -> None:
    samples = np.full((16, 16, 3), 4095, dtype=np.uint16) << 4
    path = tmp_path / "twelve.heic"
    pillow_heif.encode("RGB;16", (16, 16), samples.tobytes(), str(path), quality=-1, bit_depth=12)
    with pytest.raises(PhotoReadError) as caught:
        read_photo(path)
    assert caught.value.kind == "unsupported" and "12-bit" in str(caught.value)
