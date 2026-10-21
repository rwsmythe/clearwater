"""Unit tests of the photo helpers (WP3.6): orientation, ICC, PNG, EXIF and HEIF boxes.

Each helper is checked against an independent reference: Pillow's ``ImageOps.exif_transpose`` for
orientation, the WP2.3 profiles for ICC classification, a test-local forward PNG filter for the
decoder's inverse, Pillow's own EXIF reader for the D63 edit, and the WP2.3 HEIC samples (plus
bytes built here) for the box reader.
"""

from __future__ import annotations

import struct
import zlib
from collections.abc import Callable
from pathlib import Path

import numpy as np
import pytest
from PIL import ExifTags, Image, ImageOps

from clearwater.io.photo import exif as exif_tools
from clearwater.io.photo import icc as icc_tools
from clearwater.io.photo import png as png_tools
from clearwater.io.photo.errors import PhotoReadError
from clearwater.io.photo.heif_boxes import HeifLayoutError, read_layout
from clearwater.io.photo.orientation import apply_orientation
from spike_io import photo as spike


def _icc(sample_path: Path) -> bytes:
    scan = png_tools.scan_png(sample_path.read_bytes(), sample_path.name)
    assert scan.icc is not None
    return scan.icc


# --- orientation ----------------------------------------------------------------------------


@pytest.mark.parametrize("tag", range(1, 9))
def test_orientation_matches_pillows_exif_transpose(tag: int) -> None:
    upright = spike.upright_image(8, 40, 24)
    image = Image.fromarray(upright)
    exif = Image.Exif()
    exif[274] = tag
    image.info["exif"] = exif.tobytes()
    expected = np.asarray(ImageOps.exif_transpose(image))
    assert np.array_equal(apply_orientation(upright, tag), expected)


@pytest.mark.parametrize("tag", range(1, 9))
def test_orientation_swaps_the_shape_only_for_5_to_8(tag: int) -> None:
    out = apply_orientation(np.zeros((24, 40, 3), dtype=np.uint16), tag)
    assert out.shape == ((40, 24, 3) if tag >= 5 else (24, 40, 3))
    assert out.flags["C_CONTIGUOUS"]


@pytest.mark.parametrize("tag", [0, 9, -1])
def test_orientation_rejects_values_outside_1_to_8(tag: int) -> None:
    with pytest.raises(ValueError, match="1 to 8"):
        apply_orientation(np.zeros((2, 2, 3)), tag)


# --- ICC ------------------------------------------------------------------------------------


def test_the_fixture_profiles_classify_as_labelled(sample: Callable[[str], Path]) -> None:
    srgb = icc_tools.classify(_icc(sample("png16-gradient-srgb")))
    p3 = icc_tools.classify(_icc(sample("png16-gradient-display-p3")))
    assert (srgb.primaries, srgb.transfer) == ("bt709", "srgb")
    assert (p3.primaries, p3.transfer) == ("display-p3", "srgb")


def _profile_with(icc: bytes, tag: bytes, body: bytes) -> bytes:
    """Return ``icc`` with the tag ``tag`` replaced by ``body`` (same table, data appended)."""
    (count,) = struct.unpack(">I", icc[128:132])
    table = bytearray(icc[132 : 132 + 12 * count])
    data = bytearray(icc)
    for index in range(count):
        if bytes(table[12 * index : 12 * index + 4]) == tag:
            offset = len(data)
            data += body + b"\0" * (-len(body) % 4)
            table[12 * index + 4 : 12 * index + 12] = struct.pack(">II", offset, len(body))
    data[132 : 132 + 12 * count] = table
    return bytes(data)


def _xyz(x: float, y: float, z: float) -> bytes:
    return b"XYZ \0\0\0\0" + b"".join(struct.pack(">i", round(v * 65536)) for v in (x, y, z))


def test_adobe_rgb_like_primaries_are_unknown_and_the_profile_is_untouched(
    sample: Callable[[str], Path],
) -> None:
    base = _icc(sample("png16-gradient-srgb"))
    wide = _profile_with(base, b"gXYZ", _xyz(0.1852, 0.7683, 0.0706))
    result = icc_tools.classify(wide)
    assert result.primaries == "unknown"
    assert result.transfer == "srgb"


def test_a_pure_gamma_curve_is_an_unknown_transfer(sample: Callable[[str], Path]) -> None:
    base = _icc(sample("png16-gradient-srgb"))
    gamma = b"curv\0\0\0\0" + struct.pack(">IH", 1, int(2.2 * 256)) + b"\0\0"
    changed = base
    for tag in (b"rTRC", b"gTRC", b"bTRC"):
        changed = _profile_with(changed, tag, gamma)
    assert icc_tools.classify(changed).transfer == "unknown"


def test_a_garbage_profile_classifies_as_unknown() -> None:
    result = icc_tools.classify(b"not a profile")
    assert (result.primaries, result.transfer) == ("unknown", "unknown")
    assert icc_tools.read_tags(b"not a profile") == {}


def test_the_profile_description_and_colour_space(sample: Callable[[str], Path]) -> None:
    icc = _icc(sample("png16-gradient-display-p3"))
    assert icc_tools.description(icc) == "Clearwater synthetic Display P3"
    assert icc_tools.is_rgb_profile(icc)
    assert icc_tools.is_valid_profile(icc)
    assert not icc_tools.is_valid_profile(b"garbage")


# --- PNG keywords ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("name", "problem"),
    [
        ("", "1 to 79"),
        ("x" * 80, "1 to 79"),
        ("Display P3 ", "leading or trailing"),
        (" sRGB", "leading or trailing"),
        ("Display  P3", "consecutive"),
        ("bad\x01name", "control"),
        ("bad\x7fname", "control"),
        ("bad\x85name", "control"),
        ("€uro", "Latin-1"),
    ],
)
def test_keyword_rule_rejects_each_violation(name: str, problem: str) -> None:
    assert problem in (png_tools.keyword_problem(name) or "")
    with pytest.raises(ValueError, match="keyword"):
        png_tools.check_keyword(name)


@pytest.mark.parametrize("name", ["sRGB", "Display P3", "a", "x" * 79, "caf\xe9 profile"])
def test_keyword_rule_accepts_valid_names(name: str) -> None:
    assert png_tools.keyword_problem(name) is None


def test_profile_name_falls_back_when_the_description_breaks_the_rule(
    sample: Callable[[str], Path],
) -> None:
    icc = _icc(sample("png16-gradient-display-p3"))
    assert png_tools.profile_name(icc) == "Clearwater synthetic Display P3"
    assert png_tools.profile_name(b"junk") == "ICC profile"


# --- PNG filters ----------------------------------------------------------------------------


def _paeth(a: int, b: int, c: int) -> int:
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    return b if pb <= pc else c


def _forward_filter(rows: np.ndarray, types: list[int], bpp: int) -> bytes:
    """Apply PNG filters 0-4 to ``(H, W * bpp)`` bytes, row by row (the reference encoder)."""
    out = bytearray()
    previous = np.zeros(rows.shape[1], dtype=np.int64)
    for y, kind in enumerate(types):
        row = rows[y].astype(np.int64)
        coded = np.zeros_like(row)
        for i in range(len(row)):
            a = row[i - bpp] if i >= bpp else 0
            b = previous[i]
            c = previous[i - bpp] if i >= bpp else 0
            pred = (0, a, b, (a + b) // 2, _paeth(int(a), int(b), int(c)))[kind]
            coded[i] = (row[i] - pred) & 255
        out += bytes([kind]) + bytes(coded.astype(np.uint8).tolist())
        previous = row
    return bytes(out)


def _png16(width: int, height: int, color_type: int, raw: bytes, interlace: int = 0) -> bytes:
    return (
        png_tools.SIGNATURE
        + png_tools.chunk(
            b"IHDR", struct.pack(">IIBBBBB", width, height, 16, color_type, 0, 0, interlace)
        )
        + png_tools.chunk(b"IDAT", zlib.compress(raw))
        + png_tools.chunk(b"IEND", b"")
    )


@pytest.mark.parametrize("types_seed", range(6))
def test_the_decoder_undoes_every_filter_type_at_16_bit(types_seed: int) -> None:
    rng = np.random.default_rng(types_seed)
    height, width = 11, 13
    samples = rng.integers(0, 65536, (height, width, 3), dtype=np.uint16)
    rows = samples.astype(">u2").view(np.uint8).reshape(height, width * 6)
    types = [int(t) for t in rng.integers(0, 5, height)]
    data = _png16(width, height, 2, _forward_filter(rows, types, 6))
    scan = png_tools.scan_png(data, "x.png")
    assert np.array_equal(png_tools.read_png16(scan, "x.png"), samples)


@pytest.mark.parametrize("kind", [1, 2, 3, 4])
def test_each_single_filter_type_alone_round_trips(kind: int) -> None:
    rng = np.random.default_rng(kind)
    samples = rng.integers(0, 65536, (7, 9, 3), dtype=np.uint16)
    rows = samples.astype(">u2").view(np.uint8).reshape(7, 54)
    data = _png16(9, 7, 2, _forward_filter(rows, [kind] * 7, 6))
    scan = png_tools.scan_png(data, "x.png")
    assert np.array_equal(png_tools.read_png16(scan, "x.png"), samples)


def test_grey_and_alpha_colour_types_expand_or_drop(tmp_path: Path) -> None:
    rng = np.random.default_rng(3)
    for color_type, channels in ((0, 1), (4, 2), (6, 4)):
        samples = rng.integers(0, 65536, (5, 6, channels), dtype=np.uint16)
        rows = samples.astype(">u2").view(np.uint8).reshape(5, 6 * channels * 2)
        data = _png16(6, 5, color_type, _forward_filter(rows, [0] * 5, channels * 2))
        out = png_tools.read_png16(png_tools.scan_png(data, "x.png"), "x.png")
        first = samples[:, :, :1] if channels in (1, 2) else samples[:, :, :3]
        assert np.array_equal(out, np.repeat(first, 3, axis=2) if channels in (1, 2) else first)


def test_an_interlaced_16_bit_png_is_refused_by_name() -> None:
    data = _png16(4, 4, 2, b"\0" * (4 * (1 + 24)), interlace=1)
    with pytest.raises(PhotoReadError) as caught:
        png_tools.read_png16(png_tools.scan_png(data, "adam7.png"), "adam7.png")
    assert caught.value.kind == "unsupported"
    assert "Adam7" in str(caught.value) and "adam7.png" in str(caught.value)


def test_a_bad_checksum_a_missing_iend_and_short_data_are_unreadable() -> None:
    good = _png16(4, 4, 2, b"\0" * (4 * 25))
    flipped = bytearray(good)
    flipped[-20] ^= 0xFF  # inside IDAT
    for blob in (bytes(flipped), good[:-12], good[:40]):
        with pytest.raises(PhotoReadError) as caught:
            png_tools.read_png16(png_tools.scan_png(blob, "bad.png"), "bad.png")
        assert caught.value.kind == "unreadable"
    short = _png16(4, 4, 2, b"\0" * (4 * 25 - 1))
    with pytest.raises(PhotoReadError) as caught:
        png_tools.read_png16(png_tools.scan_png(short, "short.png"), "short.png")
    assert caught.value.kind == "unreadable"


def test_a_row_with_an_unknown_filter_type_is_unreadable() -> None:
    raw = (b"\x07" + b"\0" * 24) * 4
    with pytest.raises(PhotoReadError, match="filter"):
        png_tools.read_png16(png_tools.scan_png(_png16(4, 4, 2, raw), "f.png"), "f.png")


# --- EXIF (D63) -----------------------------------------------------------------------------


def test_d63_edit_changes_exactly_the_listed_fields() -> None:
    source = spike.source_exif(6, 96, 64, thumbnail=True)
    assert exif_tools.has_thumbnail(source)
    edited = exif_tools.edit(source, 64, 96)
    before, after = exif_tools.describe(source), exif_tools.describe(edited)
    changed = {k for k in set(before) | set(after) if before.get(k) != after.get(k)}
    assert changed == {
        "IFD0.Orientation",
        "IFD0.Software",
        "Exif.ExifImageWidth",
        "Exif.ExifImageHeight",
    }
    assert after["IFD0.Orientation"] == "1"
    assert after["IFD0.Software"] == "Clearwater"
    assert (after["Exif.ExifImageWidth"], after["Exif.ExifImageHeight"]) == ("64", "96")
    assert not exif_tools.has_thumbnail(edited)
    assert not edited.startswith(exif_tools.PREFIX)
    for kept in ("IFD0.Make", "IFD0.Model", "Exif.DateTimeOriginal", "GPS.GPSLatitudeRef"):
        assert after[kept] == before[kept]


def test_d63_edit_of_a_source_without_exif_is_a_minimal_block() -> None:
    edited = exif_tools.edit(None, 30, 20)
    assert exif_tools.describe(edited) == {
        "IFD0.Orientation": "1",
        "IFD0.Software": "Clearwater",
        "Exif.ExifImageWidth": "30",
        "Exif.ExifImageHeight": "20",
    }


def test_d63_edit_does_not_invent_a_gps_ifd() -> None:
    exif = Image.Exif()
    exif[271] = "Maker"
    edited = exif_tools.edit(exif.tobytes(), 4, 4)
    assert not any(name.startswith("GPS.") for name in exif_tools.describe(edited))
    assert exif_tools.load(edited).get(int(ExifTags.IFD.GPSInfo)) is None


def test_orientation_of_handles_absent_invalid_and_garbage() -> None:
    assert exif_tools.orientation_of(None) == 1
    exif = Image.Exif()
    exif[274] = 9
    assert exif_tools.orientation_of(exif.tobytes()) == 1
    exif[274] = 8
    assert exif_tools.orientation_of(exif.tobytes()) == 8
    assert exif_tools.orientation_of(exif_tools.strip_prefix(exif.tobytes())) == 8
    assert exif_tools.orientation_of(b"garbage bytes") == 1


# --- HEIF boxes -----------------------------------------------------------------------------


def _box(kind: bytes, body: bytes) -> bytes:
    return struct.pack(">I", 8 + len(body)) + kind + body


def _full(kind: bytes, body: bytes, version: int = 0, flags: int = 0) -> bytes:
    return _box(kind, bytes([version]) + flags.to_bytes(3, "big") + body)


def _heif(
    primary: int,
    properties: list[bytes],
    associations: dict[int, list[int]],
    types: dict[int, bytes],
) -> bytes:
    """A minimal HEIF meta box: pitm, iinf (v2 infe), iprp (ipco, ipma)."""
    infe = b"".join(
        _full(b"infe", struct.pack(">HH4s", item, 0, kind) + b"\0", version=2)
        for item, kind in types.items()
    )
    ipma = struct.pack(">I", len(associations)) + b"".join(
        struct.pack(">HB", item, len(indices)) + bytes(indices)
        for item, indices in associations.items()
    )
    meta = (
        _full(b"hdlr", b"\0" * 20)
        + _full(b"pitm", struct.pack(">H", primary))
        + _full(b"iinf", struct.pack(">H", len(types)) + infe)
        + _box(b"iprp", _box(b"ipco", b"".join(properties)) + _full(b"ipma", ipma))
    )
    return _box(b"ftyp", b"heic\0\0\0\0heic") + _full(b"meta", meta)


IROT_270 = _box(b"irot", bytes([3]))
IROT_90 = _box(b"irot", bytes([1]))
IMIR = _box(b"imir", bytes([1]))


def _ispe(width: int, height: int) -> bytes:
    return _full(b"ispe", struct.pack(">II", width, height))


def test_irot_comes_from_the_primary_items_ipma_not_from_ipco_alone() -> None:
    # Item 1 (the primary) has only ispe; item 2 (a thumbnail) carries the irot in ipco.
    data = _heif(
        1,
        [_ispe(96, 64), IROT_270, _ispe(24, 16)],
        {1: [1], 2: [3, 2]},
        {1: b"hvc1", 2: b"hvc1"},
    )
    layout = read_layout(data)
    assert layout.irot is None
    assert layout.ispe == (96, 64)
    assert layout.expected_size() == (96, 64)


def test_irot_associated_with_the_primary_turns_the_expected_size() -> None:
    data = _heif(7, [_ispe(64, 96), IROT_270], {7: [1, 2]}, {7: b"hvc1"})
    layout = read_layout(data)
    assert layout.irot == 270
    assert layout.expected_size() == (96, 64)


def test_a_primary_that_is_not_item_one_is_followed() -> None:
    data = _heif(
        2, [_ispe(10, 20), IROT_90, _ispe(30, 40)], {1: [1, 2], 2: [3]}, {1: b"hvc1", 2: b"grid"}
    )
    layout = read_layout(data)
    assert (layout.primary_id, layout.item_type, layout.irot, layout.ispe) == (
        2,
        "grid",
        None,
        (30, 40),
    )
    assert layout.is_grid


def test_imir_and_clap_are_read_for_the_primary() -> None:
    clap = _box(b"clap", struct.pack(">8I", 90, 1, 60, 1, 0, 1, 0, 1))
    data = _heif(1, [_ispe(96, 64), IMIR, clap], {1: [1, 2, 3]}, {1: b"hvc1"})
    layout = read_layout(data)
    assert layout.imir == 1
    assert layout.clap == (90, 60)
    assert layout.expected_size() == (90, 60)


def test_the_wide_ipma_form_with_32_bit_item_ids() -> None:
    infe = _full(b"infe", struct.pack(">IH4s", 5, 0, b"hvc1") + b"\0", version=3)
    ipma = (
        struct.pack(">I", 1)
        + struct.pack(">IB", 5, 2)
        + struct.pack(">HH", 0x8001, 0x0002)  # essential bit set on the first
    )
    meta = (
        _full(b"pitm", struct.pack(">I", 5), version=1)
        + _full(b"iinf", struct.pack(">I", 1) + infe, version=1)
        + _box(
            b"iprp",
            _box(b"ipco", _ispe(8, 6) + IROT_90) + _full(b"ipma", ipma, version=1, flags=1),
        )
    )
    layout = read_layout(_box(b"ftyp", b"heic\0\0\0\0heic") + _full(b"meta", meta))
    assert (layout.primary_id, layout.irot, layout.ispe) == (5, 90, (8, 6))


def test_auxiliary_and_thumbnail_references_are_listed() -> None:
    data = _heif(1, [_ispe(8, 8)], {1: [1]}, {1: b"hvc1"})
    # Append an iref (v0) with an auxl from item 3 and a thmb from item 2, inside meta.
    iref = _full(
        b"iref",
        _box(b"auxl", struct.pack(">HHH", 3, 1, 1)) + _box(b"thmb", struct.pack(">HHH", 2, 1, 1)),
    )
    meta_at = data.index(b"meta") - 4
    (meta_size,) = struct.unpack(">I", data[meta_at : meta_at + 4])
    patched = data[:meta_at] + struct.pack(">I", meta_size + len(iref)) + data[meta_at + 4 :] + iref
    layout = read_layout(patched)
    assert layout.auxiliary_ids == (3,)
    assert layout.thumbnail_ids == (2,)


def test_a_file_without_the_boxes_is_a_layout_error() -> None:
    for blob in (b"", b"\0" * 40, _box(b"ftyp", b"heic\0\0\0\0heic")):
        with pytest.raises(HeifLayoutError):
            read_layout(blob)
    no_ipma = _box(b"meta", b"\0\0\0\0" + _full(b"pitm", struct.pack(">H", 1)))
    with pytest.raises(HeifLayoutError):
        read_layout(no_ipma)


@pytest.mark.parametrize(
    ("sample_id", "irot", "size"),
    [
        ("heic-ad24-both", 270, (96, 64)),
        ("heic-ad24-irot-only", 270, (96, 64)),
        ("heic-ad24-exif-only", None, (64, 96)),
        ("heic-ad24-neither", None, (96, 64)),
    ],
)
def test_the_ad24_samples_layouts(
    sample: Callable[[str], Path], sample_id: str, irot: int | None, size: tuple[int, int]
) -> None:
    layout = read_layout(sample(sample_id).read_bytes())
    assert layout.irot == irot
    assert layout.primary_id == 1
    assert layout.expected_size() == size
