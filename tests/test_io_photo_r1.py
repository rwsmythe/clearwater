"""Tests of the WP3.6 round-1 remediation (Reviewer A findings #1, #3, #4, #5, #9, #10).

Each test fails on the code at round-1 head ``983bff1`` (the fail-before evidence is in the
ledger) and passes on the remediated code.
"""

from __future__ import annotations

import io
import struct
import zlib
from collections.abc import Callable
from pathlib import Path

import numpy as np
import pillow_heif
import pytest
import tifffile
from PIL import Image

from clearwater.io.photo import PhotoReadError, read_photo, write_photo
from clearwater.io.photo import exif as exif_tools
from clearwater.io.photo import png as png_tools


def _patched(source: Path, out: Path, old: bytes, new: bytes) -> Path:
    """Copy ``source`` to ``out`` with ``old`` replaced by the same-length ``new``."""
    data = source.read_bytes()
    assert len(old) == len(new)
    at = data.find(old)
    assert at >= 0, f"{old!r} not found"
    out.write_bytes(data[:at] + new + data[at + len(old) :])
    return out


# --- #1: a HEIC colour box of type rICC is a profile too ----------------------------------------


def test_a_heic_ricc_colour_box_is_carried_like_prof(
    sample: Callable[[str], Path], tmp_path: Path
) -> None:
    source = sample("heic8-uniform-display-p3")
    plain, _ = read_photo(source)
    assert plain.color.icc_profile is not None
    patched = _patched(source, tmp_path / "ricc.heic", b"colrprof", b"colrrICC")
    image, _ = read_photo(patched)
    assert image.color.icc_profile == plain.color.icc_profile
    assert (image.color.primaries, image.color.transfer) == ("display-p3", "srgb")
    assert image.color.assumed is False


def test_a_heic_with_neither_prof_nor_ricc_keeps_the_nclx_route(tmp_path: Path) -> None:
    pixels = np.full((16, 16, 3), 128, dtype=np.uint8)
    nclx = {
        "color_primaries": 12,
        "transfer_characteristics": 13,
        "matrix_coefficients": 6,
        "full_range_flag": 1,
    }
    path = tmp_path / "nclx.heic"
    pillow_heif.encode("RGB", (16, 16), pixels.tobytes(), str(path), quality=90, nclx_profile=nclx)
    image, _ = read_photo(path)
    assert image.color.icc_profile is None
    assert image.color.primaries == "display-p3"


# --- #5: a TIFF source's Interop IFD is carried, not left as a dangling pointer ------------------

_INTEROP_POINTER = 40965
_NUL = bytes(1)


def _entry(tag: int, kind: int, count: int, value: int | bytes) -> bytes:
    raw = value if isinstance(value, bytes) else struct.pack("<I", value)
    return struct.pack("<HHI", tag, kind, count) + raw.ljust(4, _NUL)


def _ifd(entries: list[bytes]) -> bytes:
    return struct.pack("<H", len(entries)) + b"".join(entries) + struct.pack("<I", 0)


def _tiff_with_interop(interop_at: int | None = None) -> bytes:
    """A 1x1 grey TIFF whose IFD0 points to an Exif IFD that points to an Interop IFD.

    Offsets are absolute in the file, as a TIFF has them. ``interop_at`` overrides the Interop
    pointer (to plant an unreadable one).
    """
    ifd0_at, pixel_at = 9, 8
    ifd0_size = 2 + 9 * 12 + 4
    exif_at = ifd0_at + ifd0_size
    real_interop_at = exif_at + 2 + 2 * 12 + 4
    exif_ifd = _ifd(
        [
            _entry(36864, 7, 4, b"0230"),
            _entry(_INTEROP_POINTER, 4, 1, real_interop_at if interop_at is None else interop_at),
        ]
    )
    interop_ifd = _ifd([_entry(1, 2, 4, b"R98" + _NUL)])
    ifd0 = _ifd(
        [
            _entry(256, 3, 1, 1),
            _entry(257, 3, 1, 1),
            _entry(258, 3, 1, 8),
            _entry(262, 3, 1, 1),
            _entry(273, 4, 1, pixel_at),
            _entry(277, 3, 1, 1),
            _entry(278, 3, 1, 1),
            _entry(279, 4, 1, 1),
            _entry(34665, 4, 1, exif_at),
        ]
    )
    head = b"II*" + _NUL + struct.pack("<I", ifd0_at)
    return head + b"\x80" + ifd0 + exif_ifd + interop_ifd


def _interop_view(block: bytes) -> tuple[dict[int, object], dict[int, object]]:
    """The Exif IFD and the Interop IFD of a block, as the next reader sees them."""
    exif = Image.Exif()
    exif.load(block)
    exif_ifd = dict(exif.get_ifd(0x8769))
    return exif_ifd, dict(exif.get_ifd(0xA005)) if _INTEROP_POINTER in exif_ifd else {}


def test_a_tiff_interop_ifd_is_carried_into_the_exif_block(tmp_path: Path) -> None:
    path = tmp_path / "interop.tif"
    path.write_bytes(_tiff_with_interop())
    _, meta = read_photo(path)
    assert meta.exif is not None
    for block in (meta.exif, exif_tools.edit(meta.exif, 4, 4)):
        exif_ifd, interop = _interop_view(block)
        assert interop == {1: "R98"}, "the Interop field survives, not an empty IFD"
        pointer = exif_ifd[_INTEROP_POINTER]
        assert isinstance(pointer, int) and pointer < len(block), "an offset inside the block"


def test_an_unreadable_tiff_interop_pointer_is_dropped_not_left_dangling(
    tmp_path: Path,
) -> None:
    path = tmp_path / "dangling.tif"
    path.write_bytes(_tiff_with_interop(interop_at=0x00FFFFF0))
    _, meta = read_photo(path)
    assert meta.exif is not None
    exif_ifd, interop = _interop_view(meta.exif)
    assert _INTEROP_POINTER not in exif_ifd and interop == {}
    assert exif_ifd[36864] == b"0230", "the rest of the Exif IFD is kept"


# --- #3: a primary item with no ispe is refused ---------------------------------------------------


def test_a_heic_primary_without_ispe_is_refused_as_unreadable(
    sample: Callable[[str], Path], tmp_path: Path
) -> None:
    source = sample("heic8-uniform-none")  # libheif itself still decodes this one without ispe
    read_photo(source)
    patched = tmp_path / "noispe.heic"
    patched.write_bytes(source.read_bytes().replace(b"ispe", b"xspe"))
    with pytest.raises(PhotoReadError) as caught:
        read_photo(patched)
    assert caught.value.kind == "unreadable"
    assert "noispe.heic" in str(caught.value) and "ispe" in str(caught.value)


# --- #4: nclx primaries "unspecified" with a specified transfer ---------------------------


def _nclx_heic(path: Path, primaries: int, transfer: int) -> Path:
    pixels = np.full((16, 16, 3), 128, dtype=np.uint8)
    nclx = {
        "color_primaries": primaries,
        "transfer_characteristics": transfer,
        "matrix_coefficients": 6,
        "full_range_flag": 1,
    }
    pillow_heif.encode("RGB", (16, 16), pixels.tobytes(), str(path), quality=90, nclx_profile=nclx)
    return path


@pytest.mark.parametrize(
    ("primaries", "transfer", "expected"),
    [
        (2, 1, ("unknown", "bt709", False)),
        (2, 13, ("unknown", "srgb", False)),
        (1, 2, ("bt709", "unknown", False)),
        (2, 2, ("bt709", "srgb", True)),
    ],
)
def test_nclx_codes_are_read_one_at_a_time(
    tmp_path: Path, primaries: int, transfer: int, expected: tuple[str, str, bool]
) -> None:
    image, _ = read_photo(_nclx_heic(tmp_path / "n.heic", primaries, transfer))
    color = image.color
    assert (color.primaries, color.transfer, color.assumed) == expected
    assert color.icc_profile is None


# --- #9: a message naming a non-ASCII file is still ASCII ----------------------------------------


def test_a_non_ascii_file_name_gives_an_ascii_message(tmp_path: Path) -> None:
    missing = tmp_path / ("caf" + chr(0xE9) + " " + chr(0x6F5C) + chr(0x6C34) + ".jpg")
    with pytest.raises(PhotoReadError) as caught:
        read_photo(missing)
    message = str(caught.value)
    assert message.isascii()
    assert "caf\\xe9" in message and "\\u6f5c" in message, "the name is escaped"
    assert caught.value.kind == "unreadable"


def test_an_ascii_message_is_unchanged() -> None:
    assert (
        str(PhotoReadError("unsupported", "a.dng is not supported.")) == "a.dng is not supported."
    )


# --- #10: the 16-bit PNG path warns when it drops an alpha channel --------------------------------


def _png16_with_alpha(color_type: int) -> bytes:
    """A 4x4 16-bit PNG of colour type 6 (RGBA) or 4 (grey+alpha), non-interlaced."""
    channels = 4 if color_type == 6 else 2
    samples = np.arange(4 * 4 * channels, dtype=">u2").reshape(4, 4 * channels) * 1000
    rows = np.zeros((4, 1 + 4 * channels * 2), dtype=np.uint8)
    rows[:, 1:] = samples.view(np.uint8).reshape(4, -1)
    header = struct.pack(">IIBBBBB", 4, 4, 16, color_type, 0, 0, 0)
    return (
        png_tools.SIGNATURE
        + png_tools.chunk(b"IHDR", header)
        + png_tools.chunk(b"IDAT", zlib.compress(rows.tobytes()))
        + png_tools.chunk(b"IEND", b"")
    )


@pytest.mark.parametrize("color_type", [6, 4])
def test_a_16_bit_png_with_alpha_warns_that_alpha_is_dropped(
    tmp_path: Path, caplog: pytest.LogCaptureFixture, color_type: int
) -> None:
    path = tmp_path / "alpha16.png"
    path.write_bytes(_png16_with_alpha(color_type))
    with caplog.at_level("WARNING", logger="clearwater.io.photo.reader"):
        image, _ = read_photo(path)
    assert image.pixels.shape == (4, 4, 3)
    assert "alpha16.png: alpha channel dropped" in caplog.text


def test_a_16_bit_png_without_alpha_does_not_warn(
    sample: Callable[[str], Path], caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level("WARNING", logger="clearwater.io.photo.reader"):
        read_photo(sample("png16-gradient-srgb"))
    assert "alpha" not in caplog.text


# --- R2 #1: a WhiteIsZero grey TIFF is read, inverted ------------------------------------------


@pytest.mark.parametrize("dtype", [np.uint8, np.uint16])
def test_a_white_is_zero_grey_tiff_is_inverted_to_the_same_picture(
    tmp_path: Path, dtype: type[np.unsignedinteger]
) -> None:
    top = int(np.iinfo(dtype).max)
    grey = np.array([[0, top // 4, top // 2, top]] * 4, dtype=dtype)  # what the viewer shows
    black_is_zero, white_is_zero = tmp_path / "bz.tif", tmp_path / "wz.tif"
    tifffile.imwrite(black_is_zero, grey, photometric="minisblack")
    tifffile.imwrite(white_is_zero, top - grey, photometric="miniswhite")  # stored inverted
    want, _ = read_photo(black_is_zero)
    got, _ = read_photo(white_is_zero)
    assert got.color.bit_depth == (16 if dtype is np.uint16 else 8)
    assert np.array_equal(got.pixels, want.pixels)
    assert float(got.pixels[0, 0, 0]) == 0.0 and float(got.pixels[0, 3, 0]) == 1.0


# --- R2 #4: the byte order of a TIFF source's EXIF block is the source's -------------------------


@pytest.mark.parametrize(("order", "head"), [("<", b"II*"), (">", b"MM")])
def test_a_tiff_exif_block_keeps_the_source_byte_order(
    tmp_path: Path, order: str, head: bytes
) -> None:
    path = tmp_path / "order.tif"
    tifffile.imwrite(
        path,
        np.zeros((4, 4, 3), dtype=np.uint8),
        photometric="rgb",
        byteorder=order,
        extratags=[(271, "s", 0, "Maker", True), (272, "s", 0, "Model", True)],
    )
    _, meta = read_photo(path)
    assert meta.exif is not None and meta.exif.startswith(head)
    assert exif_tools.edit(meta.exif, 4, 4).startswith(head)
    assert exif_tools.describe(meta.exif)["IFD0.Make"] == "Maker"


# --- Reviewer B B2: associated (premultiplied) alpha is undone before it is dropped ---------------


def test_a_premultiplied_rgba_tiff_is_un_premultiplied(tmp_path: Path) -> None:
    half_red = np.zeros((2, 2, 4), dtype=np.uint16)
    half_red[..., 0], half_red[..., 3] = 32768, 32768  # full red, premultiplied by alpha 0.5
    half_red[1, 1] = (0, 0, 0, 0)  # alpha 0: colour stays 0, no division by zero
    path = tmp_path / "premul.tif"
    tifffile.imwrite(path, half_red, photometric="rgb", extrasamples=["assocalpha"])
    image, _ = read_photo(path)
    assert image.pixels[0, 0].tolist() == [1.0, 0.0, 0.0]
    assert image.pixels[1, 1].tolist() == [0.0, 0.0, 0.0]


def test_an_unassociated_alpha_tiff_keeps_its_colour_untouched(tmp_path: Path) -> None:
    rgba = np.zeros((2, 2, 4), dtype=np.uint8)
    rgba[..., 0], rgba[..., 3] = 128, 128
    path = tmp_path / "straight.tif"
    tifffile.imwrite(path, rgba, photometric="rgb", extrasamples=["unassalpha"])
    image, _ = read_photo(path)
    assert round(float(image.pixels[0, 0, 0]) * 255) == 128


def test_a_premultiplied_grey_alpha_tiff_is_un_premultiplied(tmp_path: Path) -> None:
    grey_alpha = np.zeros((2, 2, 2), dtype=np.uint8)
    grey_alpha[..., 0], grey_alpha[..., 1] = 64, 128  # grey 128 at alpha 128/255, premultiplied
    path = tmp_path / "premul-grey.tif"
    tifffile.imwrite(path, grey_alpha, photometric="minisblack", extrasamples=["assocalpha"])
    image, _ = read_photo(path)
    assert round(float(image.pixels[0, 0, 1]) * 255) in (127, 128), "64 * 255 / 128 = 127.5"


# --- Reviewer B B3: a damaged EXIF block is dropped at read, never met by the writer -----------

_GARBAGE_EXIF = b"this is not an exif block"


def _png8_with_exif(garbage: bytes) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (8, 8), (10, 20, 30)).save(buffer, format="PNG")
    data = buffer.getvalue()
    split = 8 + 25  # signature, then the 25-byte IHDR chunk
    return data[:split] + png_tools.chunk(b"eXIf", garbage) + data[split:]


def _damaged_exif_files(tmp_path: Path) -> dict[str, Path]:
    files = {}
    files["png16"] = tmp_path / "bad16.png"
    files["png16"].write_bytes(
        png_tools.SIGNATURE
        + png_tools.chunk(b"IHDR", struct.pack(">IIBBBBB", 2, 2, 16, 2, 0, 0, 0))
        + png_tools.chunk(b"eXIf", _GARBAGE_EXIF)
        + png_tools.chunk(b"IDAT", zlib.compress(bytes(2 * (1 + 12))))
        + png_tools.chunk(b"IEND", b"")
    )
    files["png8"] = tmp_path / "bad8.png"
    files["png8"].write_bytes(_png8_with_exif(_GARBAGE_EXIF))
    files["jpeg"] = tmp_path / "bad.jpg"
    Image.new("RGB", (8, 8), (10, 20, 30)).save(
        files["jpeg"], exif=b"Exif" + bytes(2) + _GARBAGE_EXIF
    )
    files["heic"] = tmp_path / "bad.heic"
    pixels = np.full((16, 16, 3), 128, dtype=np.uint8)
    pillow_heif.encode(
        "RGB",
        (16, 16),
        pixels.tobytes(),
        str(files["heic"]),
        quality=90,
        exif=b"Exif" + bytes(2) + _GARBAGE_EXIF,
    )
    return files


@pytest.mark.parametrize("kind", ["png16", "png8", "jpeg", "heic"])
def test_a_damaged_exif_block_is_dropped_with_a_warning_and_the_write_succeeds(
    tmp_path: Path, caplog: pytest.LogCaptureFixture, kind: str
) -> None:
    path = _damaged_exif_files(tmp_path)[kind]
    with caplog.at_level("WARNING", logger="clearwater.io.photo"):
        image, meta = read_photo(path)
    assert meta.exif is None and meta.orientation == 1
    assert f"{path.name}: the EXIF block is damaged" in caplog.text
    out = tmp_path / "out.png"
    write_photo(image, meta, out, bit_depth=16)
    written = png_tools.scan_png(out.read_bytes(), "out.png").exif
    assert written is not None
    assert exif_tools.describe(written)["IFD0.Software"] == "Clearwater"


def test_a_usable_exif_block_is_still_carried(sample: Callable[[str], Path]) -> None:
    _, meta = read_photo(sample("heic-ad24-both"))
    assert meta.exif is not None


def test_a_tiff_with_an_unreadable_gps_ifd_keeps_its_other_fields(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    # Pillow reads every malformed GPS IFD this test could build as an empty one, so the failure
    # is injected: the GPS IFD raises, Make must survive.
    path = tmp_path / "gps.tif"
    tifffile.imwrite(
        path,
        np.zeros((4, 4, 3), dtype=np.uint8),
        photometric="rgb",
        extratags=[(271, "s", 0, "Maker", True)],
    )
    real = Image.Exif.get_ifd

    def get_ifd(self: Image.Exif, tag: int) -> dict[int, object]:
        if tag == exif_tools.GPS_IFD and getattr(self, "fp", None) is not None:  # the source
            raise ValueError("planted GPS failure")
        return real(self, tag)

    monkeypatch.setattr(Image.Exif, "get_ifd", get_ifd)
    with caplog.at_level("WARNING", logger="clearwater.io.photo.exif"):
        _, meta = read_photo(path)
    monkeypatch.undo()
    assert "GPS IFD cannot be read" in caplog.text
    assert meta.exif is not None
    assert exif_tools.describe(meta.exif)["IFD0.Make"] == "Maker"


# --- Reviewer B B4: a file cut inside a known signature is unreadable, not an unknown format ------


@pytest.mark.parametrize(
    ("name", "data"),
    [
        ("cut.jpg", b"\xff\xd8"),
        ("cut.png", png_tools.SIGNATURE[:7]),
        ("cut.tif", b"II*"),
        ("cut.heic", struct.pack(">I", 24) + b"ftyp"),
    ],
)
def test_a_file_cut_inside_a_known_signature_is_unreadable(
    tmp_path: Path, name: str, data: bytes
) -> None:
    path = tmp_path / name
    path.write_bytes(data)
    with pytest.raises(PhotoReadError) as caught:
        read_photo(path)
    assert caught.value.kind == "unreadable" and name in str(caught.value)


@pytest.mark.parametrize("data", [b"\xff", b"zz", b"hello world, not a photo"])
def test_other_short_or_unknown_files_stay_unsupported_or_unreadable_as_before(
    tmp_path: Path, data: bytes
) -> None:
    path = tmp_path / "x.bin"
    path.write_bytes(data)
    with pytest.raises(PhotoReadError) as caught:
        read_photo(path)
    assert caught.value.kind == "unsupported"
