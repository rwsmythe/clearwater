"""The colour description of a photo (spec 6.5, D53; WP3.6 questions 3 and 4).

The embedded ICC profile is carried byte-identical and never applied to pixel values; only the
``primaries`` and ``transfer`` labels are derived from it (or from the equivalent colour data of a
HEIC, its ``nclx`` box). Untagged photos are read as sRGB and flagged ``assumed`` (G10 warns).
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

from clearwater.interfaces.image import ColorDescription
from clearwater.io.photo import icc as icc_tools

_log = logging.getLogger(__name__)

_NCLX_PRIMARIES = {1: "bt709", 12: "display-p3"}
_NCLX_TRANSFER = {13: "srgb", 1: "bt709", 6: "bt709"}


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

    Order of evidence: an RGB ICC profile; a PNG ``sRGB`` chunk; a HEIC ``nclx`` box naming a
    primaries or a transfer code (a code left unspecified reads as ``unknown``); otherwise the
    photo is untagged and read as BT.709 primaries with the sRGB curve, ``assumed=True``.

    Args:
        depth: The source bit depth (8, 10 or 16).
        icc: The embedded ICC profile bytes, or None.
        srgb_chunk: True when a PNG carried an ``sRGB`` chunk and no profile.
        nclx: A HEIC ``nclx_profile`` mapping (``color_primaries``, ``transfer_characteristics``)
            or None.
        name: The file name for log messages.

    Returns:
        The description; ``icc_profile`` is the profile as embedded in the file, or None (the
        writer's built-in profiles are never put here).
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
    # An ``assumed=False`` description with no ICC profile comes only from the next two branches
    # (a PNG ``sRGB`` chunk, a HEIC ``nclx`` box). The writer (D53) gives the sRGB and Display P3
    # forms of the HEIC case a built-in profile (never the PNG, N-2); the IF-1 ``icc_profile``
    # stays None, as the file has none.
    if srgb_chunk:
        return _build("bt709", "srgb", depth, False, None)
    if nclx is not None:
        # nclx code 2 is "unspecified"; the photo is untagged only when both codes are.
        primaries_code = int(nclx.get("color_primaries", 2))
        transfer_code = int(nclx.get("transfer_characteristics", 2))
        if (primaries_code, transfer_code) != (2, 2):
            primaries = _NCLX_PRIMARIES.get(primaries_code, "unknown")
            transfer = _NCLX_TRANSFER.get(transfer_code, "unknown")
            return _build(primaries, transfer, depth, False, None)
    _log.info("%s: no colour profile; read as sRGB", name)
    return _build("bt709", "srgb", depth, True, None)
