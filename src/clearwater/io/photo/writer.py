"""Photo output: an 8- or 16-bit PNG with the source ICC profile, D63 EXIF and provenance.

Spec 8.1 and D22, D53, D63, D91. The sink writes only the path it is given, opened ``"wb"`` and
closed before it returns, so the caller (WP3.14) can open ``SafeWrite``, pass its temporary path
and commit afterwards (X-B1, N8).
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from clearwater.config import check_string_keys
from clearwater.interfaces.image import Image
from clearwater.interfaces.photo import PhotoMetadata
from clearwater.io.photo import exif as exif_tools
from clearwater.io.photo import png as png_tools
from clearwater.io.photo.color import built_in_profile_name

PROFILE_KEY = "profile"
"""The provenance key that records a built-in ICC profile (``built-in <name>``)."""


def provenance_text(provenance: Mapping[str, Any], icc: bytes | None = None) -> str:
    """Serialise a provenance mapping as the JSON the ``iTXt`` chunk holds (D91).

    When ``icc`` is one of the built-in profiles (given to a source that carried no profile of
    its own, D53), the text also records ``"profile": "built-in <name>"``.

    Args:
        provenance: The provenance mapping.
        icc: The profile that is embedded in the PNG, or None.

    Returns:
        JSON text with sorted keys and no NaN.

    Raises:
        clearwater.interfaces.FormatError: A mapping key is not a string.
        ValueError: A value is not JSON-serialisable or is NaN or infinite, or the mapping
            already has a ``profile`` key while a built-in profile is embedded.
    """
    check_string_keys(provenance, "provenance")
    built_in = built_in_profile_name(icc)
    if built_in is not None:
        if PROFILE_KEY in provenance:
            raise ValueError(f"provenance already has a {PROFILE_KEY!r} key")
        provenance = {**provenance, PROFILE_KEY: f"built-in {built_in}"}
    try:
        return json.dumps(provenance, allow_nan=False, sort_keys=True)
    except TypeError as error:
        raise ValueError(f"provenance is not JSON-serialisable: {error}") from error


class PhotoWriter:
    """Writes corrected photos (IF-6 ``PhotoSink``) as PNG."""

    def write(
        self,
        image: Image,
        meta: PhotoMetadata,
        out_path: Path,
        *,
        bit_depth: int,
        provenance: Mapping[str, Any] | None,
    ) -> None:
        """Write a PNG, 8 or 16 bit, with the ICC profile embedded and EXIF per D63.

        The profile is embedded byte-identical when the image has one (none otherwise, so the
        output reads as the untagged source did). EXIF follows D63: Orientation 1, thumbnail
        dropped, pixel dimensions updated, Software ``Clearwater``, every other field kept.
        Provenance (D91) goes into one ``iTXt`` chunk when given; a built-in profile (a source
        with nclx colour data and no ICC profile, D53) is recorded in it as ``profile``.

        Args:
            image: The corrected image: float32 ``(H, W, 3)`` in [0, 1] on the CPU.
            meta: The source photo's metadata.
            out_path: The output file (suffix ``.png``); it is the only file written.
            bit_depth: The PNG bit depth, 8 or 16.
            provenance: The provenance to embed, or None for none.

        Raises:
            ValueError: ``bit_depth`` is not 8 or 16, the image is not on the CPU, not float32
                ``(H, W, 3)`` or holds NaN, ``out_path`` is not ``.png``, or the provenance
                cannot be serialised.
        """
        if image.device != "cpu":
            raise ValueError(
                f"the photo writer needs a host image, got device {image.device!r}; "
                "copy it to the host first"
            )
        text = (
            provenance_text(provenance, image.color.icc_profile) if provenance is not None else None
        )
        height, width = image.pixels.shape[:2]
        block = exif_tools.edit(meta.exif, width, height)
        png_tools.write_png(
            Path(out_path),
            image.pixels,
            bit_depth=bit_depth,
            icc=image.color.icc_profile,
            exif=block,
            provenance_json=text,
        )


def write_photo(
    image: Image,
    meta: PhotoMetadata,
    out_path: Path,
    *,
    bit_depth: int,
    provenance: Mapping[str, Any] | None = None,
) -> None:
    """Write a photo with a default :class:`PhotoWriter`.

    Args:
        image: The corrected image.
        meta: The source photo's metadata.
        out_path: The output file.
        bit_depth: 8 or 16.
        provenance: The provenance to embed, or None.
    """
    PhotoWriter().write(image, meta, out_path, bit_depth=bit_depth, provenance=provenance)
