"""The colour description of a photo (spec 6.5, D53; WP3.6 questions 3 and 4).

The embedded ICC profile is carried byte-identical and never applied to pixel values; only the
``primaries`` and ``transfer`` labels are derived from it (or from the equivalent colour data of a
HEIC, its ``nclx`` box). Untagged photos are read as sRGB and flagged ``assumed`` (G10 warns).
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Mapping
from typing import Any

from clearwater.interfaces.image import ColorDescription
from clearwater.io.photo import icc as icc_tools
from clearwater.io.photo.p3_profile import display_p3_profile

_log = logging.getLogger(__name__)

_NCLX_PRIMARIES = {1: "bt709", 12: "display-p3"}
_NCLX_TRANSFER = {13: "srgb", 1: "bt709", 6: "bt709"}

_BUILT_IN_PROFILES: tuple[tuple[str, Callable[[], bytes]], ...] = (
    ("Display P3", display_p3_profile),
)
"""The built-in profiles as (name, builder); the name is what provenance records."""


def built_in_profile_name(icc: bytes | None) -> str | None:
    """Name the built-in profile that ``icc`` is, if it is one.

    A profile the reader took from the file is never a built-in; the one exception is a file
    that was itself written by Clearwater and carries the same bytes.

    Args:
        icc: A profile as carried in ``ColorDescription.icc_profile``, or None.

    Returns:
        The name (``"Display P3"``), or None when ``icc`` is None or not a built-in.
    """
    if icc is None:
        return None
    for name, build in _BUILT_IN_PROFILES:
        if icc == build():
            return name
    return None


def _build(
    primaries: str, transfer: str, depth: int, assumed: bool, icc: bytes | None
) -> ColorDescription:
    return ColorDescription(
        primaries=primaries,
        transfer=transfer,
        matrix="identity",
        range="full",
        bit_depth=depth,
        assumed=assumed,
        icc_profile=icc,
    )


def describe_color(
    depth: int,
    icc: bytes | None,
    *,
    srgb_chunk: bool = False,
    nclx: Mapping[str, Any] | None = None,
    name: str = "the photo",
) -> ColorDescription:
    """Build the :class:`ColorDescription` of a decoded photo.

    Order of evidence: an RGB ICC profile; a PNG ``sRGB`` chunk; a HEIC ``nclx`` box; otherwise
    the photo is untagged and read as BT.709 primaries with the sRGB curve, ``assumed=True``.

    Args:
        depth: The source bit depth (8, 10 or 16).
        icc: The embedded ICC profile bytes, or None.
        srgb_chunk: True when a PNG carried an ``sRGB`` chunk and no profile.
        nclx: A HEIC ``nclx_profile`` mapping (``color_primaries``, ``transfer_characteristics``)
            or None.
        name: The file name for log messages.

    Returns:
        The description; ``icc_profile`` is the profile as embedded, or None.
    """
    if icc is not None:
        if not icc_tools.read_tags(icc):
            _log.warning(
                "%s: the embedded colour profile is not a valid ICC profile; ignored", name
            )
        elif not icc_tools.is_rgb_profile(icc):
            _log.warning("%s: the embedded profile is not an RGB profile; not carried", name)
        else:
            if not icc_tools.is_valid_profile(icc):
                _log.warning("%s: the embedded colour profile does not open cleanly", name)
            found = icc_tools.classify(icc)
            return _build(found.primaries, found.transfer, depth, False, icc)
    if srgb_chunk:
        return _build("bt709", "srgb", depth, False, None)
    if nclx is not None and int(nclx.get("color_primaries", 2)) != 2:
        primaries = _NCLX_PRIMARIES.get(int(nclx["color_primaries"]), "unknown")
        transfer = _NCLX_TRANSFER.get(int(nclx.get("transfer_characteristics", 2)), "unknown")
        # D53: an nclx-only Display P3 photo with the sRGB curve gets the built-in profile (its
        # tone curve is sRGB), so the PNG output is not read as sRGB. Anything else, and every
        # source that carries an ICC profile, keeps the profile it has (none here).
        profile = display_p3_profile() if (primaries, transfer) == ("display-p3", "srgb") else None
        return _build(primaries, transfer, depth, False, profile)
    _log.info("%s: no colour profile; read as sRGB", name)
    return _build("bt709", "srgb", depth, True, None)
