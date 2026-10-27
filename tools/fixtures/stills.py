"""Synthetic still-image fixtures (WP2.3 item 1).

Three contents (uniform, horizontal gradient, near-zero red channel) at 96 x 64, each in
8-bit and 16-bit where the format allows, with no profile, an sRGB profile and a Display P3
profile; PNG, JPEG, TIFF and HEIC; the EXIF Orientation cases on JPEG; and the AD-24 HEIC
orientation cases. Everything is built from numbers: the Display P3 profile by
:func:`spike_io.photo.display_p3_profile` (WP2.1S's construction), the sRGB profile by Pillow's
``ImageCms``, the 16-bit PNG by the WP2.1S stdlib writer. No file carries a GPS block.

What Pillow cannot write is not substituted: a 16-bit RGB TIFF (Pillow reads ``RGB;16B``
data down to 8 bits) is listed in the manifest's ``omitted`` block.
"""

from __future__ import annotations

import hashlib
import re
import struct
import sys
import zlib
from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import Any

import numpy as np
import pillow_heif
from numpy.typing import NDArray
from PIL import ExifTags, Image, ImageCms
from pillow_heif.constants import HeifCompressionFormat
from pillow_heif.misc import CtxEncode

if not __package__:
    # Script mode: sys.path[0] is tools/fixtures; put tools first for the sibling packages.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fixtures import manifest
from spike_io import photo
from spike_io.guard import WriteGuard

WIDTH = 96
"""Width of a landscape still."""

HEIGHT = 64
"""Height of a landscape still."""

CONTENTS = ("uniform", "gradient", "lowred")
"""The three contents: a uniform colour, a horizontal gradient, a near-zero red channel."""

ICC_KINDS = ("none", "srgb", "display-p3")
"""The profiles a still may carry."""

LOW_RED_LEVELS = 2
"""The largest red level (of 255) of the ``lowred`` content in a lossless sample."""

LOSSY_RED_LEVELS = 0
"""The red level of the ``lowred`` content before a lossy codec: JPEG and HEIC spread the other
channels' energy into red (measured: up to 2 levels from a red of 0, 3 from a red of 1), so the
source red is 0 and the decoded red still stays at or below 2/255."""

LOW_RED_SEED = 20261020
"""The seed of the red-channel noise."""

HEIC_QUALITY = 95
"""The pillow-heif quality of the HEIC samples."""

JPEG_QUALITY = 95
"""The JPEG quality of the JPEG samples."""

ORIENTATIONS = (1, 3, 6, 8)
"""The EXIF Orientation values on the JPEG orientation samples."""

AD24_CASES = ("both", "irot-only", "exif-only", "neither")
"""The AD-24 HEIC orientation cases: where the rotation is recorded."""

OMITTED = (
    {
        "what": "tiff16-*: 16-bit RGB TIFF",
        "reason": "Pillow 12.3.0 cannot write a 16-bit-per-channel RGB TIFF: Image.fromarray "
        "rejects uint16 RGB and Image.frombytes(RGB;16B) yields an 8-bit RGB image. "
        "Only the single-channel I;16 mode is written, which is not a colour photo.",
    },
)
"""Samples asked for that this environment cannot produce (the brief: say so, do not substitute)."""

_ICC_DATE = (2026, 10, 20, 0, 0, 0)
"""The fixed creation date pinned into the sRGB profile header (LittleCMS stamps the clock)."""


def srgb_profile() -> bytes:
    """Return Pillow's sRGB profile with its creation date pinned.

    ``ImageCms.createProfile`` stamps the current time into the header (bytes 24 to 36), which
    would make every run differ; the date is replaced with a fixed one. The profile ID is zero,
    so no checksum depends on the date.

    Returns:
        The profile's bytes.
    """
    data = bytearray(ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes())
    data[24:36] = struct.pack(">6H", *_ICC_DATE)
    return bytes(data)


def icc_bytes(kind: str) -> bytes | None:
    """Return the profile of a kind.

    Args:
        kind: One of :data:`ICC_KINDS`.

    Returns:
        The profile bytes, or None for ``"none"``.

    Raises:
        ValueError: Unknown kind.
    """
    if kind == "none":
        return None
    if kind == "srgb":
        return srgb_profile()
    if kind == "display-p3":
        return photo.display_p3_profile()
    raise ValueError(f"unknown profile kind {kind!r}")


def unit_content(
    name: str,
    width: int = WIDTH,
    height: int = HEIGHT,
    red_levels: int = LOW_RED_LEVELS,
) -> NDArray[np.float64]:
    """Return a content as float64 RGB in [0, 1], shape ``(height, width, 3)``.

    - ``uniform``: one blue-green colour.
    - ``gradient``: a grey ramp, black at the left edge to white at the right.
    - ``lowred``: a blue-green scene (green rising to the right, blue rising downwards) whose
      red channel is seeded noise no larger than ``red_levels`` / 255.

    Args:
        name: One of :data:`CONTENTS`.
        width: Width in pixels.
        height: Height in pixels.
        red_levels: The largest red level (of 255) of ``lowred``.

    Returns:
        The content.

    Raises:
        ValueError: Unknown content.
    """
    x = np.linspace(0.0, 1.0, width)[None, :] * np.ones((height, 1))
    y = np.linspace(0.0, 1.0, height)[:, None] * np.ones((1, width))
    if name == "uniform":
        return np.broadcast_to(np.array([0.25, 0.50, 0.60]), (height, width, 3)).copy()
    if name == "gradient":
        return np.stack([x, x, x], axis=-1)
    if name == "lowred":
        red = np.random.default_rng(LOW_RED_SEED).random((height, width)) * red_levels / 255
        return np.stack([red, 0.35 + 0.30 * x, 0.45 + 0.30 * y], axis=-1)
    raise ValueError(f"unknown content {name!r}")


def quantize(unit: NDArray[np.float64], bits: int) -> NDArray[Any]:
    """Quantize a unit-range image to 8 (``uint8``), 10 (``uint16`` 0..1023) or 16 bits."""
    if bits == 8:
        return np.round(unit * 255).astype(np.uint8)
    if bits in (10, 16):
        return np.round(unit * ((1 << bits) - 1)).astype(np.uint16)
    raise ValueError(f"unsupported bit depth {bits}")


def camera_exif(orientation: int) -> bytes:
    """Build a small camera-like EXIF block with Pillow, without any GPS block.

    Args:
        orientation: The EXIF Orientation value (1 to 8).

    Returns:
        ``Exif`` and two NUL bytes, then the TIFF bytes (Pillow's ``Image.Exif.tobytes``).
    """
    exif = Image.Exif()
    exif[int(ExifTags.Base.Make)] = "Clearwater"
    exif[int(ExifTags.Base.Model)] = "synthetic fixture"
    exif[int(ExifTags.Base.DateTime)] = "2026:10:20 10:00:00"
    exif[int(ExifTags.Base.Orientation)] = orientation
    return exif.tobytes()


# --- Writers ------------------------------------------------------------------------------


def _chunk(kind: bytes, data: bytes) -> bytes:
    """Encode one PNG chunk."""
    crc = zlib.crc32(kind + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", crc)


def png16_bytes(pixels: NDArray[np.uint16], icc: bytes | None, profile_name: str) -> bytes:
    """Encode a 16-bit RGB PNG through the WP2.1S writer, without EXIF and optionally without ICC.

    The WP2.1S writer always emits ``iCCP`` and ``eXIf`` chunks; those a fixture does not want
    are cut out here and the rest re-emitted unchanged, in order.

    Args:
        pixels: A ``(height, width, 3)`` ``uint16`` array.
        icc: The profile to embed, or None for a PNG without ``iCCP``.
        profile_name: The ``iCCP`` profile name.

    Returns:
        The PNG file's bytes.
    """
    encoded = photo.encode_png16(
        pixels, icc if icc is not None else photo.display_p3_profile(), b"", profile_name
    )
    drop = {"eXIf"} | ({"iCCP"} if icc is None else set())
    out = [photo.PNG_SIGNATURE]
    for kind, body in photo.png_chunks(encoded):
        if kind not in drop:
            out.append(_chunk(kind.encode("latin-1"), body))
    return b"".join(out)


_PROFILE_NAMES = {"srgb": "sRGB", "display-p3": "Display P3"}


def write_heic(
    path: Path,
    stored: NDArray[Any],
    bits: int,
    *,
    tag: int,
    transform: int,
    icc: bytes | None,
    guard: WriteGuard,
) -> None:
    """Write a HEIC with pillow-heif's x265 encoder, choosing the tag and the ``irot`` separately.

    Uses pillow-heif's ``misc.CtxEncode`` (private API, as in WP2.1S) because the public
    ``encode`` cannot write an EXIF Orientation without the matching ``irot`` or the reverse.

    Args:
        path: The output file.
        stored: The pixels as stored (``uint8``; or ``uint16`` 0..1023 for 10 bits).
        bits: 8 or 10. Ten-bit data is passed as ``RGB;16`` shifted left by 6.
        tag: The EXIF Orientation to write (1 to 8).
        transform: The orientation the ``irot``/``imir`` boxes carry (1 writes none).
        icc: The profile to embed, or None.
        guard: The write guard; ``path`` is checked before the write.

    Raises:
        ValueError: Unsupported bit depth.
    """
    height, width = stored.shape[:2]
    if bits == 8:
        mode, data = "RGB", np.ascontiguousarray(stored, dtype=np.uint8).tobytes()
    elif bits == 10:
        mode, data = "RGB;16", (stored.astype(np.uint16) << 6).tobytes()
    else:
        raise ValueError(f"unsupported HEIC bit depth {bits}")
    guard.check(path)
    encoder = CtxEncode(HeifCompressionFormat.HEVC, quality=HEIC_QUALITY)
    encoder.add_image(
        (width, height),
        mode,
        data,
        image_orientation=transform,
        primary=True,
        icc_profile=icc,
        exif=camera_exif(tag),
    )
    encoder.save(str(path))


# --- Measurement (reads the written file back) ----------------------------------------------


def _exif_facts(exif: Image.Exif | None) -> dict[str, Any]:
    """Return the Orientation tag and whether a GPS block exists, from a parsed EXIF."""
    if not exif:
        return {"exif_orientation": None, "has_gps": False}
    orientation = exif.get(int(ExifTags.Base.Orientation))
    return {
        "exif_orientation": int(orientation) if orientation is not None else None,
        "has_gps": bool(exif.get_ifd(ExifTags.IFD.GPSInfo)) or int(ExifTags.Base.GPSInfo) in exif,
    }


def tiff_bits_per_sample(data: bytes) -> tuple[int, ...]:
    """Read BitsPerSample (TIFF tag 258) from the first IFD of a TIFF's own bytes.

    Args:
        data: The whole TIFF file.

    Returns:
        The bits of each sample (``(8, 8, 8)`` for an 8-bit RGB TIFF).

    Raises:
        ValueError: Not a classic TIFF, or it has no BitsPerSample entry.
    """
    order = {b"II": "<", b"MM": ">"}.get(data[:2])
    if order is None or struct.unpack(order + "H", data[2:4])[0] != 42:
        raise ValueError("not a classic TIFF")
    ifd = struct.unpack(order + "I", data[4:8])[0]
    (count,) = struct.unpack(order + "H", data[ifd : ifd + 2])
    for k in range(count):
        at = ifd + 2 + 12 * k
        tag, kind, n = struct.unpack(order + "HHI", data[at : at + 8])
        if tag != 258:
            continue
        if kind != 3:
            raise ValueError(f"BitsPerSample has TIFF type {kind}, not SHORT")
        start = at + 8 if n * 2 <= 4 else struct.unpack(order + "I", data[at + 8 : at + 12])[0]
        return struct.unpack(f"{order}{n}H", data[start : start + 2 * n])
    raise ValueError("no BitsPerSample entry")


XMP_MARKERS = (
    b"http://ns.adobe.com/xap/1.0/",
    b"adobe:ns:meta/",
    b"http://ns.adobe.com/exif/1.0/",
    b"<?xpacket",
)
"""Byte strings that mark an XMP packet in any container: the APP1 packet header, the
``x:xmpmeta`` namespace, the EXIF namespace and the packet processing instruction. Namespace
URIs, not the prefixes a writer happens to choose."""

_GPS_NAME = re.compile(rb"GPS[A-Za-z]+")


def xmp_gps_findings(data: bytes) -> list[str]:
    """Name the XMP markers and ``GPS*`` properties found anywhere in a file's raw bytes.

    A ``GPS`` property is any run ``GPS`` + letters, as an element or an attribute, with any
    namespace prefix or none. Only names are returned: the scan exists to refuse location
    data, so no value is ever read out, printed or logged.

    Args:
        data: The whole file, of any container.

    Returns:
        The markers present (from :data:`XMP_MARKERS`, as text) and the GPS property names
        (for example ``GPSLongitude``), sorted and without duplicates; empty for a clean file.
        Only ASCII or UTF-8 text is scanned: UTF-16 and compressed XMP are not.
    """
    found = {marker.decode("ascii") for marker in XMP_MARKERS if marker in data}
    found.update(match.decode("ascii") for match in _GPS_NAME.findall(data))
    return sorted(found)


def _boxes(data: bytes, start: int, end: int) -> Iterator[tuple[str, int, int]]:
    """Yield ``(type, body_start, box_end)`` for each ISO-BMFF box in ``data[start:end]``."""
    at = start
    while at + 8 <= end:
        (size,) = struct.unpack(">I", data[at : at + 4])
        kind = data[at + 4 : at + 8].decode("latin-1")
        header = 8
        if size == 1:
            (size,) = struct.unpack(">Q", data[at + 8 : at + 16])
            header = 16
        elif size == 0:
            size = end - at
        if size < header or at + size > end:
            raise ValueError(f"the {kind!r} box at byte {at} does not fit its parent")
        yield kind, at + header, at + size
        at += size


def _child(data: bytes, kind: str, start: int, end: int) -> tuple[int, int]:
    """Return ``(body_start, box_end)`` of the first ``kind`` box in ``data[start:end]``."""
    for name, body, stop in _boxes(data, start, end):
        if name == kind:
            return body, stop
    raise ValueError(f"no {kind!r} box")


def heif_primary_properties(data: bytes) -> dict[str, Any]:
    """Read the primary image item's transform and extent properties from a HEIF file.

    Walks ``meta``: ``pitm`` names the primary item, every ``ipma`` box in ``iprp`` gives the
    item's property indices (1-based into the ``ipco`` list; index 0 means none; the
    essential bit is masked off), and only the properties so associated count. A property
    that sits in ``ipco`` without an association to the primary item is ignored.

    Args:
        data: The whole HEIF file.

    Returns:
        ``item``: the primary item id; ``irot``: its rotation in degrees anticlockwise
        (``(byte & 3) * 90``) or None; ``imir``: its mirror axis (``byte & 1``) or None;
        ``ispe``: its ``(width, height)`` before any transform.

    Raises:
        ValueError: A box is missing or malformed, ``pitm`` or the primary's ``ipma`` entry
            is absent, the primary has no ``ispe``, or it has two properties of one type.
    """
    meta, meta_end = _child(data, "meta", 0, len(data))
    inner = meta + 4  # meta is a full box: version and flags first
    pitm, _ = _child(data, "pitm", inner, meta_end)
    if data[pitm] == 0:
        (item,) = struct.unpack(">H", data[pitm + 4 : pitm + 6])
    else:
        (item,) = struct.unpack(">I", data[pitm + 4 : pitm + 8])
    iprp, iprp_end = _child(data, "iprp", inner, meta_end)
    ipco, ipco_end = _child(data, "ipco", iprp, iprp_end)
    properties = list(_boxes(data, ipco, ipco_end))
    indices: list[int] | None = None
    for kind, body, stop in _boxes(data, iprp, iprp_end):
        if kind != "ipma":
            continue
        version, flags = data[body], int.from_bytes(data[body + 1 : body + 4], "big")
        (count,) = struct.unpack(">I", data[body + 4 : body + 8])
        at = body + 8
        for _ in range(count):
            if version < 1:
                (entry,) = struct.unpack(">H", data[at : at + 2])
                at += 2
            else:
                (entry,) = struct.unpack(">I", data[at : at + 4])
                at += 4
            n = data[at]
            at += 1
            if entry == item and indices is None:
                indices = []
            for _ in range(n):
                if flags & 1:
                    (assoc,) = struct.unpack(">H", data[at : at + 2])
                    at += 2
                    index = assoc & 0x7FFF
                else:
                    index = data[at] & 0x7F
                    at += 1
                if at > stop:
                    raise ValueError("an 'ipma' entry runs past its box")
                if entry == item and indices is not None and index:
                    indices.append(index)
    if indices is None:
        raise ValueError(f"no 'ipma' entry for the primary item {item}")
    result: dict[str, Any] = {"item": item, "irot": None, "imir": None}
    ispe: tuple[int, int] | None = None
    seen: set[str] = set()
    for index in indices:
        if index > len(properties):
            raise ValueError(f"'ipma' index {index} is beyond the {len(properties)} properties")
        kind, body, stop = properties[index - 1]
        if kind not in ("irot", "imir", "ispe"):
            continue
        if kind in seen:
            raise ValueError(f"the primary item {item} has two {kind!r} properties")
        seen.add(kind)
        needed = 12 if kind == "ispe" else 1  # ispe: version/flags, width, height
        if stop - body < needed:
            raise ValueError(f"the {kind!r} property is {stop - body} bytes, needs {needed}")
        if kind == "irot":
            result["irot"] = (data[body] & 3) * 90
        elif kind == "imir":
            result["imir"] = data[body] & 1
        else:
            ispe = struct.unpack(">II", data[body + 4 : body + 12])
    if ispe is None:
        raise ValueError(f"the primary item {item} has no 'ispe' property")
    result["ispe"] = ispe
    return result


def check_heif_extents(facts: dict[str, Any], props: dict[str, Any]) -> list[str]:
    """Compare a HEIC's ``ispe`` with the sizes the manifest facts claim.

    ``ispe`` is the stored size, before ``irot``. It must equal ``stored_width`` x
    ``stored_height`` when the facts carry them, and, turned by an ``irot`` of 90 or 270, the
    ``width`` x ``height`` that libheif reports after applying ``irot``.

    Args:
        facts: The measured facts, with ``width`` and ``height`` and optionally the stored size.
        props: The result of :func:`heif_primary_properties`.

    Returns:
        One message per disagreement; empty when the sizes agree.
    """
    problems = []
    ispe = tuple(props["ispe"])
    if "stored_width" in facts and "stored_height" in facts:
        stored = (facts["stored_width"], facts["stored_height"])
        if ispe != stored:
            problems.append(f"ispe is {ispe}, the stored size is {stored}")
    turned = ispe[::-1] if props["irot"] in (90, 270) else ispe
    decoded = (facts["width"], facts["height"])
    if turned != decoded:
        problems.append(
            f"ispe after irot {props['irot']} is {turned}, the decoded size is {decoded}"
        )
    return problems


_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_HEIC_BRANDS = (b"heic", b"heix")
"""Major brands of the committed HEICs; a video ``ftyp`` or an AVIF is not one of them."""

_FORMAT_NAMES = {"png": "PNG", "jpeg": "JPEG", "tiff": "TIFF", "heic": "HEIC"}
"""The manifest's ``format`` spelling of each :func:`container_format` result."""


def container_format(data: bytes) -> str | None:
    """Name a still's container from its first bytes alone.

    Nothing here comes from Pillow, the file name or the manifest.

    Args:
        data: The whole file (or at least its first 12 bytes).

    Returns:
        ``"png"`` (the 8-byte signature), ``"jpeg"`` (``FF D8 FF``), ``"tiff"`` (``II*`` or
        ``MM`` + a zero byte + ``*``), ``"heic"`` (an ISO-BMFF ``ftyp`` box whose major brand is
        ``heic`` or ``heix``), else None.
    """
    if data.startswith(_PNG_SIGNATURE):
        return "png"
    if data.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if data[:4] in (b"II*\x00", b"MM\x00*"):
        return "tiff"
    if data[4:8] == b"ftyp" and data[8:12] in _HEIC_BRANDS:
        return "heic"
    return None


def check_still_format(data: bytes, kind: str) -> str | None:
    """Compare a still's container, read from its bytes, with the kind it is meant to be.

    Args:
        data: The whole file.
        kind: The manifest ``kind`` the file is recorded under (``png``, ``jpeg``, ``tiff``,
            ``heic``).

    Returns:
        None when :func:`container_format` equals ``kind``, else a message naming both.
    """
    actual = container_format(data)
    if actual == kind:
        return None
    found = "no known still container" if actual is None else f"a {actual!r} container"
    return f"the bytes are {found}, the requested kind is {kind!r}"


def measure(path: Path, expected_icc: bytes | None) -> dict[str, Any]:
    """Measure a written still: format, size, depth, profile, Orientation, GPS.

    Reads the file back with Pillow, pillow-heif, the stdlib PNG walker and the TIFF
    BitsPerSample tag; nothing here comes from how the file was written.

    Args:
        path: The still.
        expected_icc: The profile the file should carry, or None.

    Returns:
        The facts: ``format``, ``width``, ``height``, ``bit_depth``, ``icc`` (``"none"``, or
        ``"match"`` when the embedded profile equals ``expected_icc``, else ``"differs"``),
        ``icc_md5``, ``exif_orientation``, ``has_gps`` and, for HEIC, ``irot`` and ``imir``.
    """
    data = path.read_bytes()
    container = container_format(data)
    if container is None:
        raise ValueError(f"{path.name}: not a PNG, JPEG, TIFF or HEIC container by its bytes")
    facts: dict[str, Any] = {"format": _FORMAT_NAMES[container]}
    embedded: bytes | None
    if container == "png":
        chunks = photo.png_chunks(data)
        ihdr = dict(chunks)["IHDR"]
        width, height = struct.unpack(">II", ihdr[:8])
        facts.update(width=width, height=height, bit_depth=ihdr[8])
        embedded = photo.stdlib_iccp(data)
        exif = None
        facts["chunks"] = [kind for kind, _ in chunks]
    elif container == "heic":
        heif = pillow_heif.open_heif(str(path))
        facts.update(width=heif.size[0], height=heif.size[1], bit_depth=heif.info["bit_depth"])
        props = heif_primary_properties(data)
        facts.update(irot=props["irot"], imir=props["imir"])
        embedded = heif.info.get("icc_profile")
        raw = heif.info.get("exif")
        exif = photo.load_exif(raw) if raw else None
    else:
        with Image.open(path) as image:
            depth = 8  # a JPEG's sample precision
            if container == "tiff":
                bits = tiff_bits_per_sample(data)  # the file's own BitsPerSample
                depth = bits[0] if len(set(bits)) == 1 else 0
            facts.update(width=image.width, height=image.height, bit_depth=depth)
            embedded = image.info.get("icc_profile")
            exif = image.getexif()
    facts.update(_exif_facts(exif))
    if embedded is None:
        facts["icc"] = "none"
    else:
        facts["icc"] = "match" if embedded == expected_icc else "differs"
        facts["icc_md5"] = hashlib.md5(embedded, usedforsecurity=False).hexdigest()
    return facts


def red_max(path: Path) -> int:
    """Return the largest red sample of a still: 0..65535 for a 16-bit PNG, else 0..255.

    The 16-bit PNG is decoded by PyAV's bundled FFmpeg decoder (Pillow would reduce it to 8
    bits); the others by Pillow or pillow-heif, which hand a 10-bit HEIC over as 8-bit RGB.

    Args:
        path: The still.

    Returns:
        The largest red value.
    """
    data = path.read_bytes()
    if data.startswith(photo.PNG_SIGNATURE) and dict(photo.png_chunks(data))["IHDR"][8] == 16:
        pixels, _ = photo.pyav_png(path)
        return int(pixels[..., 0].max())
    pillow_heif.register_heif_opener()
    with Image.open(path) as image:
        return int(np.asarray(image.convert("RGB"))[..., 0].max())


# --- The samples --------------------------------------------------------------------------


def _record(
    guard: WriteGuard,
    out: Path,
    *,
    sample_id: str,
    relative: str,
    kind: str,
    serves: Sequence[str],
    exercises: str,
    expected: dict[str, Any],
    icc: bytes | None,
    extra: dict[str, Any],
) -> manifest.Entry:
    """Measure the file at ``out / relative`` and build its manifest entry."""
    file = guard.check(out / relative)
    data = file.read_bytes()
    wrong = check_still_format(data, kind)
    if wrong:
        raise ValueError(f"{relative}: {wrong}")
    facts = measure(file, icc)
    facts.update(extra)
    if kind == "heic":
        problems = check_heif_extents(facts, heif_primary_properties(data))
        if problems:
            raise ValueError(f"{relative}: {'; '.join(problems)}")
    return manifest.entry(
        sample_id=sample_id,
        group="stills",
        kind=kind,
        storage="committed",
        path=relative,
        serves=serves,
        exercises=exercises,
        expected=expected,
        facts=facts,
        file=file,
        byte_reproducible=True,
    )


def _color(icc_kind: str, bits: int) -> dict[str, Any]:
    """Return the ``ColorDescription`` fields a reader should give a still.

    The primaries and transfer are stated only for a file with a profile; the spec does not say
    what a photo without one is read as.
    """
    color: dict[str, Any] = {
        "matrix": "identity",
        "range": "full",
        "bit_depth": bits,
        "icc_profile": None if icc_kind == "none" else icc_kind,
    }
    if icc_kind == "srgb":
        color.update(primaries="bt709", transfer="srgb")
    elif icc_kind == "display-p3":
        color.update(primaries="display-p3", transfer="srgb")
    return color


def _photo_expect(
    source_format: str, orientation: int, bits: int, icc_kind: str, *, exif: bool
) -> dict[str, Any]:
    """Return the ``expect`` block of a readable photo (IF-6 ``PhotoMetadata``, IF-1 ``Image``).

    ``icc_profile`` names the profile whose bytes must come back unchanged; ``bit_depth`` is the
    source bit depth (a 10-bit HEIC is 10, though its samples arrive as 16-bit, AD-17).
    """
    return manifest.expect(
        photo={
            "metadata": {
                "source_format": source_format,
                "exif": "present" if exif else None,
                "orientation": orientation,
            },
            "image": {"orientation_applied": True, "color": _color(icc_kind, bits)},
        }
    )


def build(guard: WriteGuard, out: Path) -> list[manifest.Entry]:
    """Write every still under ``out`` and return their manifest entries.

    Args:
        guard: The write guard whose root is ``out``.
        out: The output folder.

    Returns:
        One entry per file, in generation order.
    """
    entries: list[manifest.Entry] = []
    pillow_heif.register_heif_opener()
    upright = {
        "land": photo.upright_image(8, WIDTH, HEIGHT),
        "port": photo.upright_image(8, HEIGHT, WIDTH),
    }

    def target(relative: str) -> Path:
        path = guard.check(out / relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    for content in CONTENTS:
        unit = unit_content(content)
        unit_lossy = unit_content(content, red_levels=LOSSY_RED_LEVELS)
        for icc_kind in ICC_KINDS:
            icc = icc_bytes(icc_kind)
            suffix = f"{content}-{icc_kind}"
            meta = {"content": content, "icc_kind": icc_kind}
            serves = ["V5", "D53", "D63", "V9 (inputs)"]

            pixels8 = quantize(unit, 8)
            lossy8 = quantize(unit_lossy, 8)
            relative = f"stills/png/png8-{suffix}.png"
            Image.fromarray(pixels8).save(target(relative), "PNG", icc_profile=icc)
            entries.append(
                _record(
                    guard,
                    out,
                    sample_id=f"png8-{suffix}",
                    relative=relative,
                    kind="png",
                    serves=serves,
                    exercises=f"8-bit PNG, {content} content, {icc_kind} profile: read, profile "
                    "kept, bit depth honoured.",
                    expected=_photo_expect("png", 1, 8, icc_kind, exif=False),
                    icc=icc,
                    extra={**meta, "lossless": True},
                )
            )

            pixels16 = quantize(unit, 16)
            relative = f"stills/png/png16-{suffix}.png"
            png = png16_bytes(pixels16, icc, _PROFILE_NAMES.get(icc_kind, "none"))
            target(relative).write_bytes(png)
            entries.append(
                _record(
                    guard,
                    out,
                    sample_id=f"png16-{suffix}",
                    relative=relative,
                    kind="png",
                    serves=serves,
                    exercises=f"16-bit PNG (stdlib writer), {content} content, {icc_kind} "
                    "profile: 16-bit samples survive the read; profile kept.",
                    expected=_photo_expect("png", 1, 16, icc_kind, exif=False),
                    icc=icc,
                    extra={**meta, "lossless": True},
                )
            )

            relative = f"stills/jpeg/jpeg-{suffix}.jpg"
            Image.fromarray(lossy8).save(
                target(relative), "JPEG", quality=JPEG_QUALITY, subsampling=0, icc_profile=icc
            )
            entries.append(
                _record(
                    guard,
                    out,
                    sample_id=f"jpeg-{suffix}",
                    relative=relative,
                    kind="jpeg",
                    serves=serves,
                    exercises=f"8-bit JPEG, {content} content, {icc_kind} profile (lossy, "
                    "4:4:4, quality 95).",
                    expected=_photo_expect("jpeg", 1, 8, icc_kind, exif=False),
                    icc=icc,
                    extra={**meta, "lossless": False},
                )
            )

            relative = f"stills/tiff/tiff8-{suffix}.tif"
            Image.fromarray(pixels8).save(target(relative), "TIFF", icc_profile=icc)
            entries.append(
                _record(
                    guard,
                    out,
                    sample_id=f"tiff8-{suffix}",
                    relative=relative,
                    kind="tiff",
                    serves=[*serves, "D116 (control: a TIFF that is not a DNG)"],
                    exercises=f"8-bit TIFF, {content} content, {icc_kind} profile; also the "
                    "control for the DNG refusal (a TIFF without the DNG tag is read).",
                    expected=_photo_expect("tiff", 1, 8, icc_kind, exif=False),
                    icc=icc,
                    extra={**meta, "lossless": True},
                )
            )

            for bits in (8, 10):
                stored = quantize(unit_lossy, bits)
                relative = f"stills/heic/heic{bits}-{suffix}.heic"
                write_heic(target(relative), stored, bits, tag=1, transform=1, icc=icc, guard=guard)
                entries.append(
                    _record(
                        guard,
                        out,
                        sample_id=f"heic{bits}-{suffix}",
                        relative=relative,
                        kind="heic",
                        serves=[*serves, "AD-17"],
                        exercises=f"{bits}-bit HEIC, {content} content, {icc_kind} profile "
                        "(lossy)."
                        + (" Its samples arrive as 16-bit values (AD-17)." if bits == 10 else ""),
                        expected=_photo_expect("heic", 1, bits, icc_kind, exif=True),
                        icc=icc,
                        extra={**meta, "lossless": False},
                    )
                )

    for shape, display in upright.items():
        for orientation in ORIENTATIONS:
            stored = photo.stored_image(display, orientation)
            relative = f"stills/jpeg/jpeg-orient-{shape}-o{orientation}.jpg"
            Image.fromarray(stored).save(
                target(relative),
                "JPEG",
                quality=JPEG_QUALITY,
                subsampling=0,
                exif=camera_exif(orientation),
            )
            entries.append(
                _record(
                    guard,
                    out,
                    sample_id=f"jpeg-orient-{shape}-o{orientation}",
                    relative=relative,
                    kind="jpeg",
                    serves=["V5", "D63"],
                    exercises=f"JPEG of a {'landscape' if shape == 'land' else 'portrait'} "
                    f"scene stored for EXIF Orientation {orientation}: after the read the "
                    "pixels are upright and the tag is applied once.",
                    expected=_photo_expect("jpeg", orientation, 8, "none", exif=True),
                    icc=None,
                    extra={
                        "content": "ramp",
                        "scene": "landscape" if shape == "land" else "portrait",
                        "stored_width": stored.shape[1],
                        "stored_height": stored.shape[0],
                        "lossless": False,
                    },
                )
            )

    for case in AD24_CASES:
        orientation = 1 if case == "neither" else 6
        stored = photo.stored_image(upright["land"], orientation)
        tag = {"both": 6, "exif-only": 6, "irot-only": 1, "neither": 1}[case]
        transform = {"both": 6, "exif-only": 1, "irot-only": 6, "neither": 1}[case]
        relative = f"stills/heic/heic-ad24-{case}.heic"
        write_heic(target(relative), stored, 8, tag=tag, transform=transform, icc=None, guard=guard)
        entries.append(
            _record(
                guard,
                out,
                sample_id=f"heic-ad24-{case}",
                relative=relative,
                kind="heic",
                serves=["AD-24", "D63", "V5"],
                exercises="HEIC orientation rule: "
                + {
                    "both": "irot and EXIF Orientation 6 together (the iPhone layout); rotated "
                    "once, not twice.",
                    "irot-only": "irot only, EXIF Orientation 1; libheif rotates, nothing else.",
                    "exif-only": "EXIF Orientation 6 and no irot; the tag must be applied.",
                    "neither": "no irot and Orientation 1; no rotation.",
                }[case],
                expected=_photo_expect("heic", tag, 8, "none", exif=True),
                icc=None,
                extra={
                    "content": "ramp",
                    "scene": "landscape",
                    "ad24_case": case,
                    "intended_irot_orientation": transform,
                    "stored_width": stored.shape[1],
                    "stored_height": stored.shape[0],
                    "lossless": False,
                },
            )
        )

    for entry in entries:
        if entry["facts"].get("content") == "lowred":
            entry["facts"]["red_max"] = red_max(guard.check(out / entry["path"]))
    return entries
