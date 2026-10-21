"""ICC profile reading for classification (spec 6.5, D53; WP3.6 question 4).

A small stdlib reader of the tag table: the colorants (``rXYZ``, ``gXYZ``, ``bXYZ``, in the
D50 connection space) and the tone curves (``rTRC``, ``gTRC``, ``bTRC``; ``curv`` and ``para``)
decide whether a profile is BT.709/sRGB or Display P3. ``ImageCms`` exposes the colorants but no
curve, so this one reader decides both. No pixel value is ever converted: the profile is carried
byte-identical and only described here.
"""

from __future__ import annotations

import io
import struct
from collections.abc import Callable
from dataclasses import dataclass

from PIL import ImageCms

COLORANT_TOLERANCE = 0.001
"""Largest absolute XYZ difference of a colorant from a reference primary set."""

CURVE_TOLERANCE = 0.005
"""Largest absolute difference of a tone curve from a reference curve."""

_SRGB_COLORANTS = (
    (0.43604, 0.22248, 0.01392),
    (0.38511, 0.71691, 0.09707),
    (0.14305, 0.06061, 0.71391),
)
"""The sRGB/BT.709 primaries adapted from D65 to D50 (Bradford), as ICC colorants."""

_DISPLAY_P3_COLORANTS = (
    (0.51512, 0.24119, -0.00105),
    (0.29198, 0.69224, 0.04188),
    (0.15710, 0.06657, 0.78407),
)
"""The Display P3 primaries adapted from D65 to D50 (Bradford), as ICC colorants."""

_SAMPLES = tuple(i / 50 for i in range(1, 50))

Curve = Callable[[float], float]
Colorant = tuple[float, float, float]


@dataclass(frozen=True)
class ProfileColor:
    """What the colour tags of a profile say.

    Attributes:
        primaries: ``"bt709"``, ``"display-p3"`` or ``"unknown"``.
        transfer: ``"srgb"``, ``"bt709"`` or ``"unknown"``.
    """

    primaries: str
    transfer: str


def _srgb_eotf(v: float) -> float:
    return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4


def _bt709_eotf(v: float) -> float:
    return v / 4.5 if v < 0.081 else ((v + 0.099) / 1.099) ** (1 / 0.45)


def read_tags(icc: bytes) -> dict[str, bytes]:
    """Split a profile into its tags.

    Args:
        icc: The profile bytes.

    Returns:
        Signature (``"rXYZ"``) to the tag's bytes; empty when the header or the table is not an
        ICC profile's (a tag whose range lies outside the profile is skipped).
    """
    if len(icc) < 132 or icc[36:40] != b"acsp":
        return {}
    (count,) = struct.unpack(">I", icc[128:132])
    tags: dict[str, bytes] = {}
    for index in range(min(count, (len(icc) - 132) // 12)):
        signature, offset, size = struct.unpack(">4sII", icc[132 + 12 * index : 144 + 12 * index])
        if offset + size <= len(icc):
            tags[signature.decode("latin-1")] = icc[offset : offset + size]
    return tags


def _colorant(tag: bytes | None) -> Colorant | None:
    if tag is None or len(tag) < 20 or tag[:4] != b"XYZ ":
        return None
    x, y, z = struct.unpack(">3i", tag[8:20])
    return (x / 65536, y / 65536, z / 65536)


def _table_curve(table: tuple[int, ...]) -> Curve:
    count = len(table)

    def lookup(v: float) -> float:
        position = v * (count - 1)
        low = min(int(position), count - 2)
        frac = position - low
        return (table[low] * (1 - frac) + table[low + 1] * frac) / 65535

    return lookup


def _parametric_curve(kind: int, p: list[float]) -> Curve:
    """Return ICC parametric curve ``kind`` (0 to 4) with parameters ``p``."""
    g = p[0]
    if kind == 0:
        return lambda v: v**g
    a, b = p[1], p[2]
    if kind == 1:
        return lambda v: (a * v + b) ** g if a and v >= -b / a else 0.0
    if kind == 2:
        c = p[3]
        return lambda v: (a * v + b) ** g + c if a and v >= -b / a else c
    c, d = p[3], p[4]
    if kind == 3:
        return lambda v: (a * v + b) ** g if v >= d else c * v
    e, f = p[5], p[6]
    return lambda v: (a * v + b) ** g + e if v >= d else c * v + f


def _curve(tag: bytes | None) -> Curve | None:
    """Return a tone curve (encoded value to linear light, both 0 to 1), or None."""
    if tag is None or len(tag) < 12:
        return None
    if tag[:4] == b"curv":
        (count,) = struct.unpack(">I", tag[8:12])
        if count == 0:
            return lambda v: v
        if len(tag) < 12 + 2 * count:
            return None
        if count == 1:
            gamma = struct.unpack(">H", tag[12:14])[0] / 256
            return lambda v: v**gamma
        return _table_curve(struct.unpack(f">{count}H", tag[12 : 12 + 2 * count]))
    if tag[:4] == b"para":
        (kind,) = struct.unpack(">H", tag[8:10])
        sizes = {0: 1, 1: 3, 2: 4, 3: 5, 4: 7}
        if kind not in sizes or len(tag) < 12 + 4 * sizes[kind]:
            return None
        n = sizes[kind]
        values = [v / 65536 for v in struct.unpack(f">{n}i", tag[12 : 12 + 4 * n])]
        return _parametric_curve(kind, values)
    return None


def _near_colorants(
    found: list[Colorant | None],
    reference: tuple[Colorant, ...],
) -> bool:
    return all(
        c is not None and all(abs(a - b) <= COLORANT_TOLERANCE for a, b in zip(c, r, strict=True))
        for c, r in zip(found, reference, strict=True)
    )


def _near_curve(curve: Curve, reference: Callable[[float], float]) -> bool:
    try:
        return all(abs(curve(v) - reference(v)) <= CURVE_TOLERANCE for v in _SAMPLES)
    except (ArithmeticError, ValueError, TypeError):
        return False


def classify(icc: bytes) -> ProfileColor:
    """Classify an ICC profile as BT.709/sRGB, Display P3 or neither.

    Args:
        icc: The profile bytes.

    Returns:
        The primaries (each colorant within :data:`COLORANT_TOLERANCE` of the reference) and the
        transfer (all three curves within :data:`CURVE_TOLERANCE` of the sRGB or BT.709 curve);
        ``"unknown"`` for anything else, including an unreadable profile.
    """
    tags = read_tags(icc)
    found = [_colorant(tags.get(name)) for name in ("rXYZ", "gXYZ", "bXYZ")]
    if _near_colorants(found, _SRGB_COLORANTS):
        primaries = "bt709"
    elif _near_colorants(found, _DISPLAY_P3_COLORANTS):
        primaries = "display-p3"
    else:
        primaries = "unknown"
    curves = [_curve(tags.get(name)) for name in ("rTRC", "gTRC", "bTRC")]
    transfer = "unknown"
    for name, reference in (("srgb", _srgb_eotf), ("bt709", _bt709_eotf)):
        if all(c is not None and _near_curve(c, reference) for c in curves):
            transfer = name
            break
    return ProfileColor(primaries, transfer)


def is_valid_profile(icc: bytes) -> bool:
    """Return True when LittleCMS (through ``ImageCms``) opens the profile.

    Args:
        icc: The profile bytes.
    """
    try:
        ImageCms.ImageCmsProfile(io.BytesIO(icc))
    except (ImageCms.PyCMSError, OSError, ValueError):
        return False
    return True


def is_rgb_profile(icc: bytes) -> bool:
    """Return True when the profile's colour space (header bytes 16 to 20) is RGB.

    Args:
        icc: The profile bytes.
    """
    return len(icc) >= 20 and icc[16:20] == b"RGB "


def description(icc: bytes) -> str | None:
    """Return the profile's ``desc`` text, or None when absent or unreadable.

    Args:
        icc: The profile bytes.
    """
    tag = read_tags(icc).get("desc")
    if tag is None or len(tag) < 12:
        return None
    try:
        if tag[:4] == b"desc":
            (length,) = struct.unpack(">I", tag[8:12])
            return tag[12 : 12 + length].split(b"\0")[0].decode("latin-1") or None
        if tag[:4] == b"mluc":
            (records,) = struct.unpack(">I", tag[8:12])
            if records < 1 or len(tag) < 28:
                return None
            length, offset = struct.unpack(">II", tag[20:28])
            return tag[offset : offset + length].decode("utf-16-be") or None
    except (struct.error, UnicodeDecodeError):
        return None
    return None
