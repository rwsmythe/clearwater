"""A built-in sRGB ICC profile for HEIC files that carry only ``nclx`` BT.709/sRGB colour data.

The sibling of :mod:`clearwater.io.photo.p3_profile`, built by the same routine with the BT.709
(sRGB) primaries. It is given to a HEIC whose ``nclx`` box says BT.709 primaries and the sRGB
curve and which has no ICC profile, so the PNG output states its colour space instead of being
read as whatever a viewer assumes (D53). The only caller is
:mod:`clearwater.io.photo.color`; removing this module and its entry there restores "no profile"
for such a file.
"""

from __future__ import annotations

from clearwater.io.photo.p3_profile import build_rgb_profile

DESCRIPTION = "sRGB (Clearwater)"
"""The ``desc`` text; a valid PNG keyword, so it becomes the ``iCCP`` profile name."""

_SRGB = ((0.640, 0.330), (0.300, 0.600), (0.150, 0.060))


def srgb_profile() -> bytes:
    """Build the built-in sRGB profile (BT.709 primaries, sRGB tone curve).

    Returns:
        The profile's bytes (their md5 is pinned by a test).
    """
    return build_rgb_profile(DESCRIPTION, _SRGB)
