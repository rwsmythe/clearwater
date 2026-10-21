"""A built-in Display P3 ICC profile for HEIC files that carry only ``nclx`` colour data.

A HEIC may describe its colour by an ``nclx`` box and no ICC profile. When that box says Display
P3 (primaries code 12), a PNG written without an ``iCCP`` would be read as sRGB by every viewer,
which breaks D53 ("Photos keep source primaries end to end"). The reader therefore carries this
profile in ``ColorDescription.icc_profile`` for that one case, so the writer needs no special
case. The build is a stdlib port of the synthetic-fixture builder of WP2.1S (reference reading
only; ``src/`` never imports ``tools/``). This module is isolated so it can be removed cleanly:
the only callers are :mod:`clearwater.io.photo.color` and the sRGB sibling, which reuses
:func:`build_rgb_profile`.
"""

from __future__ import annotations

import struct

DESCRIPTION = "Display P3 (Clearwater)"
"""The ``desc`` text; a valid PNG keyword, so it becomes the ``iCCP`` profile name."""

_D50 = (0.9642, 1.0, 0.8249)
_D65_WHITE = (0.3127, 0.3290)
_DISPLAY_P3 = ((0.680, 0.320), (0.265, 0.690), (0.150, 0.060))
_BRADFORD = (
    (0.8951, 0.2664, -0.1614),
    (-0.7502, 1.7135, 0.0367),
    (0.0389, -0.0685, 1.0296),
)
Primaries = tuple[tuple[float, float], tuple[float, float], tuple[float, float]]
Matrix = tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]
Vector = tuple[float, float, float]


def _mul(m: Matrix, v: Vector) -> Vector:
    return (
        m[0][0] * v[0] + m[0][1] * v[1] + m[0][2] * v[2],
        m[1][0] * v[0] + m[1][1] * v[1] + m[1][2] * v[2],
        m[2][0] * v[0] + m[2][1] * v[1] + m[2][2] * v[2],
    )


def _matmul(a: Matrix, b: Matrix) -> Matrix:
    cols = [_mul(a, (b[0][j], b[1][j], b[2][j])) for j in range(3)]
    return (
        (cols[0][0], cols[1][0], cols[2][0]),
        (cols[0][1], cols[1][1], cols[2][1]),
        (cols[0][2], cols[1][2], cols[2][2]),
    )


def _inverse(m: Matrix) -> Matrix:
    (a, b, c), (d, e, f), (g, h, i) = m
    det = a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)
    return (
        ((e * i - f * h) / det, (c * h - b * i) / det, (b * f - c * e) / det),
        ((f * g - d * i) / det, (a * i - c * g) / det, (c * d - a * f) / det),
        ((d * h - e * g) / det, (b * g - a * h) / det, (a * e - b * d) / det),
    )


def _xyz(xy: tuple[float, float]) -> Vector:
    x, y = xy
    return (x / y, 1.0, (1.0 - x - y) / y)


def _colorants(chromaticities: Primaries) -> tuple[Vector, Vector, Vector, Matrix]:
    """Return the colorants of D65 primaries adapted to D50 (Bradford) and the adaptation matrix."""
    primaries = [_xyz(p) for p in chromaticities]
    columns: Matrix = (
        (primaries[0][0], primaries[1][0], primaries[2][0]),
        (primaries[0][1], primaries[1][1], primaries[2][1]),
        (primaries[0][2], primaries[1][2], primaries[2][2]),
    )
    scale = _mul(_inverse(columns), _xyz(_D65_WHITE))
    to_xyz: Matrix = (
        (columns[0][0] * scale[0], columns[0][1] * scale[1], columns[0][2] * scale[2]),
        (columns[1][0] * scale[0], columns[1][1] * scale[1], columns[1][2] * scale[2]),
        (columns[2][0] * scale[0], columns[2][1] * scale[1], columns[2][2] * scale[2]),
    )
    source = _mul(_BRADFORD, _xyz(_D65_WHITE))
    target = _mul(_BRADFORD, _D50)
    ratio = (target[0] / source[0], target[1] / source[1], target[2] / source[2])
    diagonal: Matrix = ((ratio[0], 0.0, 0.0), (0.0, ratio[1], 0.0), (0.0, 0.0, ratio[2]))
    adapt = _matmul(_matmul(_inverse(_BRADFORD), diagonal), _BRADFORD)
    adapted = _matmul(adapt, to_xyz)
    cols = [(adapted[0][j], adapted[1][j], adapted[2][j]) for j in range(3)]
    return cols[0], cols[1], cols[2], adapt


def _s15(value: float) -> bytes:
    return struct.pack(">i", round(value * 65536))


def _xyz_tag(xyz: Vector) -> bytes:
    return b"XYZ \x00\x00\x00\x00" + b"".join(_s15(v) for v in xyz)


def _text_tag(text: str) -> bytes:
    encoded = text.encode("utf-16-be")
    return (
        b"mluc\x00\x00\x00\x00"
        + struct.pack(">II2s2sII", 1, 12, b"en", b"US", len(encoded), 28)
        + encoded
    )


def build_rgb_profile(description: str, chromaticities: Primaries) -> bytes:
    """Build an ICC v4.3 display profile with D65 primaries and the sRGB tone curve.

    The colorants are the primaries adapted from D65 to the D50 connection space with the
    Bradford matrix, which the ``chad`` tag records; the profile ID is left zero (not computed).

    Args:
        description: The ``desc`` text.
        chromaticities: The red, green and blue CIE xy chromaticities.

    Returns:
        The profile's bytes; the same arguments always give the same bytes.
    """
    red, green, blue, adapt = _colorants(chromaticities)
    parameters = (2.4, 1 / 1.055, 0.055 / 1.055, 1 / 12.92, 0.04045)
    curve = b"para\x00\x00\x00\x00" + struct.pack(">HH", 3, 0) + b"".join(map(_s15, parameters))
    chad = b"sf32\x00\x00\x00\x00" + b"".join(_s15(v) for row in adapt for v in row)
    tags = [
        (b"desc", _text_tag(description)),
        (b"cprt", _text_tag("No copyright; built in")),
        (b"wtpt", _xyz_tag(_D50)),
        (b"chad", chad),
        (b"rXYZ", _xyz_tag(red)),
        (b"gXYZ", _xyz_tag(green)),
        (b"bXYZ", _xyz_tag(blue)),
        (b"rTRC", curve),
        (b"gTRC", curve),
        (b"bTRC", curve),
    ]
    offset = 128 + 4 + 12 * len(tags)
    table, data = struct.pack(">I", len(tags)), b""
    for signature, body in tags:
        table += struct.pack(">4sII", signature, offset + len(data), len(body))
        data += body + b"\x00" * (-len(body) % 4)
    header = (
        struct.pack(
            ">I4sI4s4s4s", offset + len(data), b"\x00" * 4, 0x04300000, b"mntr", b"RGB ", b"XYZ "
        )
        + struct.pack(">6H", 2026, 10, 20, 0, 0, 0)
        + b"acsp"
        + b"\x00" * 24
        + struct.pack(">I", 0)
        + b"".join(map(_s15, _D50))
        + b"\x00" * 48
    )
    return header + table + data


def display_p3_profile() -> bytes:
    """Build the built-in Display P3 profile (Display P3 primaries, sRGB tone curve).

    Returns:
        The profile's bytes (620; their md5 is pinned by a test).
    """
    return build_rgb_profile(DESCRIPTION, _DISPLAY_P3)
