from __future__ import annotations

import struct
import zlib
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from PIL import Image, ImageOps

from spike_io import photo

# --- An independent PNG reader for files Pillow wrote ---------------------------------------
# Written for this test, separately from photo.py (it shares no code with the stdlib writer
# or with photo.png_chunks). Used only on files Pillow wrote (brief, claim 2).


def _test_chunks(data: bytes) -> list[tuple[bytes, bytes]]:
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    out = []
    view = memoryview(data)[8:]
    while view:
        length = int.from_bytes(view[:4], "big")
        kind = bytes(view[4:8])
        body = bytes(view[8 : 8 + length])
        assert int.from_bytes(view[8 + length : 12 + length], "big") == zlib.crc32(kind + body)
        out.append((kind, body))
        view = view[12 + length :]
    return out


def _test_decode_rgb8(data: bytes) -> np.ndarray[Any, Any]:
    """Decode an 8-bit RGB, non-interlaced PNG with every filter type (stdlib + NumPy)."""
    chunks = _test_chunks(data)
    width, height, depth, colour, _, _, interlace = struct.unpack(">IIBBBBB", chunks[0][1])
    assert (depth, colour, interlace) == (8, 2, 0)
    raw = zlib.decompress(b"".join(body for kind, body in chunks if kind == b"IDAT"))
    stride = width * 3
    rows = np.zeros((height, stride), dtype=np.int32)
    for y in range(height):
        line = np.frombuffer(raw, np.uint8, stride, y * (stride + 1) + 1).astype(np.int32)
        kind = raw[y * (stride + 1)]
        up = rows[y - 1] if y else np.zeros(stride, np.int32)
        out = np.zeros(stride, np.int32)
        for x in range(stride):
            left = out[x - 3] if x >= 3 else 0
            corner = up[x - 3] if x >= 3 else 0
            if kind == 0:
                predictor = 0
            elif kind == 1:
                predictor = left
            elif kind == 2:
                predictor = up[x]
            elif kind == 3:
                predictor = (left + up[x]) // 2
            else:
                p = left + up[x] - corner
                pa, pb, pc = abs(p - left), abs(p - up[x]), abs(p - corner)
                predictor = left if pa <= pb and pa <= pc else (up[x] if pb <= pc else corner)
            out[x] = (line[x] + predictor) & 0xFF
        rows[y] = out
    return rows.astype(np.uint8).reshape(height, width, 3)


@pytest.fixture(scope="module")
def icc() -> bytes:
    return photo.display_p3_profile()


@pytest.fixture(scope="module")
def source() -> bytes:
    # A portrait camera frame (stored HEIGHT x WIDTH turned) with a thumbnail.
    return photo.source_exif(6, photo.HEIGHT, photo.WIDTH, thumbnail=True)


@pytest.fixture(scope="module")
def edited(source: bytes) -> bytes:
    return photo.edit_exif(source, photo.WIDTH, photo.HEIGHT)


# --- The profile ----------------------------------------------------------------------------


def test_profile_opens_in_imagecms_with_display_p3_primaries(icc: bytes) -> None:
    profile = photo.open_profile(icc).profile
    assert profile.profile_description == photo.PROFILE_DESCRIPTION
    assert profile.version == pytest.approx(4.3)
    # Undo LittleCMS's reading of the chad tag to recover the D65 primaries.
    chad = np.array(profile.chromatic_adaptation[0])
    for name, (x, y) in zip(("red", "green", "blue"), photo.DISPLAY_P3_PRIMARIES, strict=True):
        xyz = np.linalg.solve(chad, np.array(getattr(profile, f"{name}_colorant")[0]))
        assert xyz[0] / xyz.sum() == pytest.approx(x, abs=1e-3)
        assert xyz[1] / xyz.sum() == pytest.approx(y, abs=1e-3)


# --- Orientation helpers --------------------------------------------------------------------


@pytest.mark.parametrize("orientation", range(1, 9))
def test_apply_orientation_matches_pillow_exif_transpose(orientation: int) -> None:
    stored = photo.upright_image(8)
    image = Image.fromarray(stored)
    exif = image.getexif()
    exif[photo.ORIENTATION] = orientation
    image.info["exif"] = exif.tobytes()
    expected = np.asarray(ImageOps.exif_transpose(image))
    assert np.array_equal(photo.apply_orientation(stored, orientation), expected)


def test_pose_tells_upright_stored_twice_and_other_apart() -> None:
    upright = photo.upright_image(8)
    stored = photo.stored_image(upright, 6)
    assert photo.pose(upright, 8, upright, 8, 6) == "upright"
    assert photo.pose(stored, 8, upright, 8, 6) == "stored"
    assert photo.pose(photo.apply_orientation(upright, 6), 8, upright, 8, 6) == "twice"
    assert photo.pose(np.zeros_like(upright), 8, upright, 8, 6) == "other"
    assert photo.pose(upright, 8, upright, 8, 1) == "upright"


# --- EXIF (D63) -----------------------------------------------------------------------------


def test_source_exif_carries_a_thumbnail_pillow_can_read(source: bytes) -> None:
    assert photo.has_ifd1(source)
    assert photo.load_exif(source)[photo.ORIENTATION] == 6


def test_edit_exif_applies_d63(source: bytes, edited: bytes) -> None:
    assert photo.exif_problems(edited, source, photo.WIDTH, photo.HEIGHT) == []
    fields = photo.exif_fields(edited)
    assert fields["IFD0.Orientation"] == "1"
    assert fields["IFD0.Software"] == photo.SOFTWARE
    assert fields["Exif.ExifImageWidth"] == str(photo.WIDTH)
    assert fields["Exif.ExifImageHeight"] == str(photo.HEIGHT)
    for kept in ("IFD0.Make", "IFD0.Model", "Exif.DateTimeOriginal", "Exif.FNumber"):
        assert fields[kept] == photo.exif_fields(source)[kept]
    assert fields["GPS.GPSLatitudeRef"] == "N"
    assert not photo.has_ifd1(edited)


def test_planted_stale_orientation_fails_by_name(source: bytes, edited: bytes) -> None:
    stale = photo.load_exif(edited)
    stale[photo.ORIENTATION] = 6
    assert photo.exif_problems(stale.tobytes(), source, photo.WIDTH, photo.HEIGHT) == [
        "Orientation"
    ]


def test_unedited_source_exif_fails_every_d63_edit(source: bytes) -> None:
    problems = photo.exif_problems(source, source, photo.WIDTH, photo.HEIGHT)
    assert problems == ["Orientation", "IFD1", "PixelXDimension", "PixelYDimension", "Software"]


# --- PNG: Pillow's 16-bit path (AD-17) ------------------------------------------------------


def test_pillow_cannot_write_16bit_rgb_png(icc: bytes, edited: bytes) -> None:
    record = photo.pillow_png16_attempt(photo.upright_image(16), icc, edited)
    assert record["fromarray"].startswith("TypeError")
    assert record["frombytes_mode"] == "RGB"
    assert record["png_bit_depth"] == 8
    assert record["writes_16bit_rgb"] is False


# --- PNG: the stdlib 16-bit writer, verified by Pillow and PyAV -----------------------------


def test_png16_stdlib_write_verified_by_pillow_and_pyav(
    tmp_path: Path, icc: bytes, source: bytes, edited: bytes
) -> None:
    pixels = photo.upright_image(16)
    assert np.count_nonzero(pixels & 0xFF)  # low bytes in use: a truncation would show
    path = tmp_path / "rgb16.png"
    path.write_bytes(photo.encode_png16(pixels, icc, edited))
    record = photo.verify_png16(path, pixels, icc, edited)
    assert photo.failures(record) == []
    assert record["values_exact_pyav"] is True
    assert record["pixel_format_pyav"] == "rgb48be"
    assert record["iccp_identical_pillow"] is True
    assert record["exif_identical_pillow"] is True
    assert record["pillow_finds_exif"] is True
    assert record["chunk_order_pillow"] == ["IHDR", "iCCP", "eXIf", "IDAT", "IEND"]
    # Pillow reads the file but not its 16-bit samples: it returns 8-bit RGB.
    assert record["pillow_mode"] == "RGB"
    with Image.open(path) as image:
        assert photo.exif_problems(image.info["exif"], source, photo.WIDTH, photo.HEIGHT) == []


def test_planted_wrong_icc_byte_fails_by_name_png16(
    tmp_path: Path, icc: bytes, edited: bytes
) -> None:
    pixels = photo.upright_image(16)
    wrong = bytearray(icc)
    wrong[200] ^= 0x01
    path = tmp_path / "wrong-icc.png"
    path.write_bytes(photo.encode_png16(pixels, bytes(wrong), edited))
    assert photo.failures(photo.verify_png16(path, pixels, icc, edited)) == [
        "iccp_identical_pillow"
    ]


def test_planted_8bit_truncation_fails_by_name(tmp_path: Path, icc: bytes, edited: bytes) -> None:
    pixels = photo.upright_image(16)
    truncated = (pixels >> 8 << 8).astype(np.uint16)
    path = tmp_path / "truncated.png"
    path.write_bytes(photo.encode_png16(truncated, icc, edited))
    record = photo.verify_png16(path, pixels, icc, edited)
    assert photo.failures(record) == ["values_exact_pyav"]
    assert record["differing_samples_pyav"] > 0


# --- PNG: Pillow's 8-bit writer, verified by PyAV and stdlib readers ------------------------


def test_png8_pillow_write_verified_by_pyav_and_stdlib(
    tmp_path: Path, icc: bytes, source: bytes, edited: bytes
) -> None:
    pixels = photo.upright_image(8)
    path = tmp_path / "rgb8.png"
    photo.write_png8_pillow(path, pixels, icc, edited)
    record = photo.verify_png8(path, pixels, icc, edited)
    assert photo.failures(record) == []
    assert record["chunk_order_stdlib"] == ["IHDR", "iCCP", "eXIf", "IDAT", "IEND"]
    # The test's own reader agrees, on every property.
    data = path.read_bytes()
    chunks = _test_chunks(data)
    assert [kind for kind, _ in chunks] == [b"IHDR", b"iCCP", b"eXIf", b"IDAT", b"IEND"]
    iccp = dict(chunks)[b"iCCP"]
    assert zlib.decompress(iccp[iccp.index(b"\0") + 2 :]) == icc
    exif = dict(chunks)[b"eXIf"]
    assert exif == edited.removeprefix(photo.EXIF_PREFIX)
    assert photo.exif_problems(exif, source, photo.WIDTH, photo.HEIGHT) == []
    assert np.array_equal(_test_decode_rgb8(data), pixels)


def test_planted_wrong_icc_byte_fails_by_name_png8(
    tmp_path: Path, icc: bytes, edited: bytes
) -> None:
    pixels = photo.upright_image(8)
    wrong = bytearray(icc)
    wrong[-3] ^= 0x10
    path = tmp_path / "wrong-icc8.png"
    photo.write_png8_pillow(path, pixels, bytes(wrong), edited)
    assert photo.failures(photo.verify_png8(path, pixels, icc, edited)) == ["iccp_identical_stdlib"]


def test_encode_png16_refuses_8bit_input(icc: bytes, edited: bytes) -> None:
    with pytest.raises(photo.PhotoError):
        photo.encode_png16(photo.upright_image(8), icc, edited)  # type: ignore[arg-type]


# --- HEIC (pillow-heif) ---------------------------------------------------------------------


def _heic(tmp_path: Path, icc: bytes, bits: int, orientation: int, mode: str) -> dict[str, Any]:
    upright = photo.upright_image(bits)
    path = tmp_path / f"{bits}-{mode}-{orientation}.heic"
    photo.write_heic(path, upright, bits, orientation, mode, icc)
    return photo.read_heic(path, upright, bits, orientation, icc)


@pytest.mark.parametrize("bits", [8, 10])
@pytest.mark.parametrize(("orientation", "irot"), [(1, None), (6, 270), (8, 90)])
def test_heic_public_save_writes_irot_and_keeps_the_tag(
    tmp_path: Path, icc: bytes, bits: int, orientation: int, irot: int | None
) -> None:
    case = _heic(tmp_path, icc, bits, orientation, "public")
    assert case["container_transform"] == {"irot": irot, "imir": None}
    assert case["file_exif_orientation"] == orientation
    assert case["icc_identical_raw"] is True
    assert case["icc_identical_plugin"] is True
    # libheif applies irot: the pixels come back upright on both read paths.
    assert case["raw_pose"] == "upright"
    assert case["plugin_pose"] == "upright"
    # The plugin resets the tag (old value kept aside), so honouring it is harmless...
    assert case["plugin_exif_orientation"] == 1
    assert case["plugin_original_orientation"] == (orientation if orientation != 1 else None)
    assert case["plugin_pose_after_exif"] == "upright"
    # ...but open_heif hands over the file's tag: honouring it rotates twice.
    assert case["raw_pose_after_exif"] == ("twice" if orientation != 1 else "upright")


def test_heic_exif_only_is_not_rotated_and_the_plugin_drops_the_tag(
    tmp_path: Path, icc: bytes
) -> None:
    case = _heic(tmp_path, icc, 8, 6, "exif-only")
    assert case["container_transform"] == {"irot": None, "imir": None}
    assert case["file_exif_orientation"] == 6
    assert case["raw_pose"] == "stored"  # libheif does not apply EXIF
    assert case["raw_pose_after_exif"] == "upright"
    assert case["plugin_exif_orientation"] == 1  # reset although nothing was rotated
    assert case["plugin_original_orientation"] == 6
    assert case["plugin_pose_after_exif"] == "stored"  # the rotation is lost


def test_heic_irot_only_comes_back_upright(tmp_path: Path, icc: bytes) -> None:
    case = _heic(tmp_path, icc, 8, 6, "irot-only")
    assert case["container_transform"] == {"irot": 270, "imir": None}
    assert case["file_exif_orientation"] == 1
    assert case["raw_pose"] == case["raw_pose_after_exif"] == "upright"
    assert case["plugin_pose"] == case["plugin_pose_after_exif"] == "upright"


def test_heic_exif_fields_read(tmp_path: Path, icc: bytes) -> None:
    case = _heic(tmp_path, icc, 8, 6, "public")
    assert set(case["exif_fields_plugin"]) >= {
        "IFD0.Make",
        "IFD0.Model",
        "IFD0.Orientation",
        "Exif.DateTimeOriginal",
        "Exif.ExifImageWidth",
        "GPS.GPSLatitudeRef",
    }


@pytest.mark.parametrize("bits", [8, 10])
def test_heic_bit_depth_returned(tmp_path: Path, icc: bytes, bits: int) -> None:
    case = _heic(tmp_path, icc, bits, 1, "public")
    assert case["file_bit_depth"] == bits
    assert case["default_mode"] == "RGB"  # convert_hdr_to_8bit=True (the default)
    if bits == 10:
        assert case["hdr_mode"] == "RGB;16"
        assert case["hdr_dtype"] == "uint16"
        assert case["hdr_max"] == 1023 << 6  # 10-bit samples shifted left by 6
    else:
        assert case["hdr_mode"] == "RGB"
    assert case["hdr_pose"] == "upright"


def test_heif_transforms_without_meta_is_empty() -> None:
    assert photo.heif_transforms(b"\0\0\0\x08free") == {"irot": None, "imir": None}
