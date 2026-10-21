"""Photo input: HEIC, JPEG, PNG and TIFF to an IF-1 ``Image`` and IF-6 ``PhotoMetadata`` (WP3.6).

Spec 5.1: embedded profiles are honoured (carried, never applied), orientation is applied by
rotating the pixels on load (D63, AD-24 for HEIC), ProRAW and DNG are refused (D116), the full
image is decoded so a truncated file is refused rather than returned half-decoded (5.4).
"""

from __future__ import annotations

import io
import logging
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pillow_heif
from numpy.typing import NDArray
from PIL import Image as PILImage

from clearwater.interfaces.image import Image
from clearwater.interfaces.photo import PhotoMetadata
from clearwater.io.photo import exif as exif_tools
from clearwater.io.photo import png as png_tools
from clearwater.io.photo import tiff as tiff_tools
from clearwater.io.photo.color import describe_color
from clearwater.io.photo.errors import PhotoReadError
from clearwater.io.photo.heif_boxes import HeifLayout, HeifLayoutError, read_layout
from clearwater.io.photo.orientation import apply_orientation

_log = logging.getLogger(__name__)

MAX_PIXELS = 150_000_000
"""The largest pixel count read (spec 12 / D117 asks for 48 MP; Pillow's own limit is 179 MP)."""

DNG_VERSION_TAG = 50706
_HEIC_BRANDS = {"heic", "heix", "heim", "heis", "hevc", "hevx"}
_JPEG = b"\xff\xd8\xff"


@dataclass
class _Decoded:
    """Samples and metadata from a format reader, before orientation and normalisation."""

    format: str
    samples: NDArray[Any]
    depth: int
    exif: bytes | None
    icc: bytes | None
    orientation: int
    apply_tag: int
    srgb_chunk: bool = False
    nclx: dict[str, Any] | None = None


def detect_format(data: bytes) -> str | None:
    """Name the photo format of a file's bytes by its magic numbers.

    Args:
        data: The file's bytes (or at least its first 64 KiB).

    Returns:
        ``"jpeg"``, ``"png"``, ``"tiff"``, ``"heic"``, or None for anything else.
    """
    if data[:3] == _JPEG:
        return "jpeg"
    if data[:8] == png_tools.SIGNATURE:
        return "png"
    if data[:4] in (b"II*\x00", b"MM\x00*", b"II+\x00", b"MM\x00+"):
        return "tiff"
    if data[4:8] == b"ftyp" and len(data) >= 12:
        (size,) = struct.unpack(">I", data[:4])
        brands = {data[8:12].decode("latin-1")}
        for at in range(16, min(size, len(data)) - 3, 4):
            brands.add(data[at : at + 4].decode("latin-1"))
        if brands & _HEIC_BRANDS or ("mif1" in brands and "avif" not in brands):
            return "heic"
    return None


def has_dng_tag(data: bytes) -> bool:
    """Return True when IFD0 of a classic TIFF-structured file carries DNGVersion (50706).

    A bounded walk of IFD0 only; a malformed or out-of-range IFD0 is "not DNG" (the decode
    that follows then refuses the file as unreadable).

    Args:
        data: The file's bytes.
    """
    if data[:4] not in (b"II*\x00", b"MM\x00*"):
        return False
    order = "<" if data[:2] == b"II" else ">"
    try:
        (offset,) = struct.unpack(order + "I", data[4:8])
        (count,) = struct.unpack(order + "H", data[offset : offset + 2])
        for index in range(count):
            at = offset + 2 + 12 * index
            (tag,) = struct.unpack(order + "H", data[at : at + 2])
            if tag == DNG_VERSION_TAG:
                return True
    except struct.error:
        return False
    return False


def _normalise(samples: NDArray[Any], depth: int) -> NDArray[np.float32]:
    """Scale integer samples to float32 [0, 1] by their true bit depth (6.4)."""
    if depth == 8:
        return samples.astype(np.float32) / np.float32(255)
    if depth == 10:
        return (samples >> 6).astype(np.float32) / np.float32(1023)
    return samples.astype(np.float32) / np.float32(65535)


def _unreadable(name: str, why: str) -> PhotoReadError:
    return PhotoReadError("unreadable", f"{name} cannot be read: {why}.")


def _to_rgb(image: PILImage.Image, name: str) -> NDArray[np.uint8]:
    """Return an 8-bit RGB array from a decoded Pillow image, converting other modes."""
    if image.mode == "RGB":
        return np.asarray(image, dtype=np.uint8)
    if image.mode in ("CMYK", "YCCK") or image.mode not in (
        "1",
        "L",
        "LA",
        "P",
        "PA",
        "RGBA",
        "YCbCr",
    ):
        raise PhotoReadError(
            "unsupported", f"{name} is not supported: {image.mode} pixel data is not read."
        )
    _log.warning("%s: %s pixels converted to RGB", name, image.mode)
    return np.asarray(image.convert("RGB"), dtype=np.uint8)


def _read_pillow(data: bytes, name: str, kind: str) -> _Decoded:
    """Decode a JPEG or an 8-bit PNG fully with Pillow."""
    scan = png_tools.scan_png(data, name) if kind == "png" else None
    try:
        with PILImage.open(io.BytesIO(data)) as image:
            if image.width * image.height > MAX_PIXELS:
                raise PhotoReadError("unsupported", f"{name} is not supported: too many pixels.")
            image.load()
            samples = _to_rgb(image, name)
            info = dict(image.info)
    except PhotoReadError:
        raise
    except Exception as error:  # Pillow raises OSError, SyntaxError, ValueError, ...
        raise _unreadable(name, f"the {kind.upper()} is damaged or truncated ({error})") from error
    if scan is not None:
        block, icc, srgb = scan.exif, scan.icc, scan.srgb
    else:
        raw = info.get("exif")
        block, icc, srgb = (raw if isinstance(raw, bytes) else None), info.get("icc_profile"), False
    block = exif_tools.strip_prefix(block) if block else None
    tag = exif_tools.orientation_of(block)
    return _Decoded(kind, samples, 8, block, icc, tag, tag, srgb_chunk=srgb)


def _read_png16(scan: png_tools.PngScan, name: str) -> _Decoded:
    samples = png_tools.read_png16(scan, name)
    if scan.color_type in (4, 6):
        _log.warning("%s: alpha channel dropped", name)
    block = exif_tools.strip_prefix(scan.exif) if scan.exif else None
    tag = exif_tools.orientation_of(block)
    return _Decoded("png", samples, 16, block, scan.icc, tag, tag, srgb_chunk=scan.srgb)


def _read_tiff(data: bytes, name: str) -> _Decoded:
    picture = tiff_tools.read_tiff(data, name, MAX_PIXELS)
    block = exif_tools.from_tiff(data)
    stored = picture.orientation_tag
    tag = stored if stored is not None and 1 <= stored <= 8 else 1
    if stored is not None and tag != stored:
        _log.warning("%s: TIFF Orientation %r is not 1 to 8; taken as 1", name, stored)
    return _Decoded("tiff", picture.samples, picture.bit_depth, block, picture.icc, tag, tag)


def heic_tag_to_apply(tag: int, layout: HeifLayout) -> int:
    """Apply AD-24: the EXIF tag is applied only when the primary item has no ``irot``.

    Args:
        tag: The EXIF Orientation of the file (1 to 8).
        layout: The primary item's layout.

    Returns:
        The orientation still to apply to the decoded pixels (1 when none).
    """
    return tag if layout.irot is None else 1


def _read_heic(data: bytes, name: str) -> _Decoded:
    try:
        layout = read_layout(data)
    except HeifLayoutError as error:
        raise _unreadable(name, f"the HEIC layout cannot be established ({error})") from error
    if layout.ispe is None:
        # ``ispe`` is mandatory for an image item (ISO 23008-12); AD-24's size check needs it.
        raise _unreadable(name, "the primary image has no size property (ispe) in the HEIC")
    if layout.ispe[0] * layout.ispe[1] > MAX_PIXELS:
        raise PhotoReadError("unsupported", f"{name} is not supported: too many pixels.")
    try:
        heif = pillow_heif.open_heif(io.BytesIO(data), convert_hdr_to_8bit=False)
        depth = int(heif.info.get("bit_depth", 8))
        array = np.asarray(heif)
        mode = heif.mode
        info = dict(heif.info)
    except Exception as error:  # pillow-heif raises HeifError, OSError, ValueError, ...
        raise _unreadable(name, f"the HEIC is damaged or truncated ({error})") from error
    if depth not in (8, 10) or array.dtype not in (np.dtype(np.uint8), np.dtype(np.uint16)):
        raise PhotoReadError(
            "unsupported", f"{name} is not supported: {depth}-bit HEIC samples are not read."
        )
    if mode.startswith("RGBA"):
        _log.warning("%s: alpha channel dropped", name)
    elif not mode.startswith("RGB"):
        raise PhotoReadError("unsupported", f"{name} is not supported: HEIC mode {mode}.")
    samples = array[:, :, :3]
    expected = layout.expected_size() or layout.ispe  # ispe is present: checked above
    if (samples.shape[1], samples.shape[0]) != expected:
        raise _unreadable(
            name,
            f"the decoded size {samples.shape[1]}x{samples.shape[0]} does not match the "
            f"primary image size {expected[0]}x{expected[1]}",
        )
    raw_exif = info.get("exif")
    block = exif_tools.strip_prefix(raw_exif) if isinstance(raw_exif, bytes) and raw_exif else None
    tag = exif_tools.orientation_of(block)
    # ``prof`` is an ICC profile; ``rICC`` is the restricted form (ISO 14496-12), the same bytes.
    profile_type = info.get("icc_profile_type")
    icc = info.get("icc_profile") if profile_type in ("prof", "rICC") else None
    nclx = info.get("nclx_profile") if icc is None else None
    return _Decoded(
        "heic", samples, depth, block, icc, tag, heic_tag_to_apply(tag, layout), nclx=nclx
    )


class PhotoReader:
    """Reads photos (IF-6 ``PhotoSource``): HEIC, JPEG, PNG and TIFF, orientation applied."""

    def read(self, path: Path) -> tuple[Image, PhotoMetadata]:
        """Read a photo.

        The embedded ICC profile is kept byte-identical in ``image.color.icc_profile`` and never
        applied to the pixels; the EXIF Orientation is applied to the pixels (for a HEIC per
        AD-24) and ``PhotoMetadata.orientation`` is the source tag. DNG and ProRAW are refused
        before any decode (D116). The whole image is decoded, so a damaged file is refused.

        Args:
            path: The photo file.

        Returns:
            The image (float32 ``(H, W, 3)`` RGB in [0, 1] on the CPU) and its metadata.

        Raises:
            PhotoReadError: ``"unsupported"`` for DNG/ProRAW, CMYK, an unknown format, an
                interlaced 16-bit PNG, a TIFF compression that is not decoded, or too many
                pixels; ``"unreadable"`` for a missing, truncated or corrupt file.
        """
        path = Path(path)
        name = path.name
        try:
            data = path.read_bytes()
        except FileNotFoundError as error:
            raise _unreadable(name, "the file does not exist") from error
        except OSError as error:
            raise _unreadable(
                name, f"the file cannot be opened ({error.strerror or error})"
            ) from error
        if not data:
            raise _unreadable(name, "the file is empty")
        if path.suffix.lower() == ".dng" or has_dng_tag(data):
            raise PhotoReadError(
                "unsupported",
                f"{name} is not supported: ProRAW and DNG files are not read in this version; "
                "export a JPEG, HEIC or TIFF from the camera app instead.",
            )
        kind = detect_format(data)
        if kind is None:
            raise PhotoReadError(
                "unsupported",
                f"{name} is not supported: it is not a HEIC, JPEG, PNG or TIFF photo.",
            )
        if kind == "png":
            scan = png_tools.scan_png(data, name)
            if scan.bit_depth == 16:
                decoded = _read_png16(scan, name)
            else:
                decoded = _read_pillow(data, name, "png")
        elif kind == "jpeg":
            decoded = _read_pillow(data, name, "jpeg")
        elif kind == "tiff":
            decoded = _read_tiff(data, name)
        else:
            decoded = _read_heic(data, name)
        samples = apply_orientation(decoded.samples, decoded.apply_tag)
        pixels = _normalise(samples, decoded.depth)
        color = describe_color(
            decoded.depth,
            decoded.icc,
            srgb_chunk=decoded.srgb_chunk,
            nclx=decoded.nclx,
            name=name,
        )
        image = Image(pixels=pixels, device="cpu", color=color, orientation_applied=True)
        return image, PhotoMetadata(decoded.format, decoded.exif, decoded.orientation)


def read_photo(path: Path) -> tuple[Image, PhotoMetadata]:
    """Read a photo with a default :class:`PhotoReader`.

    Args:
        path: The photo file.

    Returns:
        The image and its metadata (see :meth:`PhotoReader.read`).
    """
    return PhotoReader().read(path)
