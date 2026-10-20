"""IF-6: photo source and sink."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from .image import Image


@dataclass(frozen=True)
class PhotoMetadata:
    """The metadata a photo carries from source to output (IF-6; D63). PROPOSED (WP2.2 round 1).

    Attributes:
        source_format: The source format, ``"heic"``, ``"jpeg"``, ``"png"`` or ``"tiff"``.
        exif: The source EXIF block as bytes, or None when the source has none.
        orientation: The source EXIF Orientation tag (1 to 8; 1 when absent). The pixels of
            the :class:`~clearwater.interfaces.image.Image` already carry it (D63).
    """

    source_format: str
    exif: bytes | None
    orientation: int


@runtime_checkable
class PhotoSource(Protocol):
    """Reads photos (IF-6)."""

    def read(self, path: Path) -> tuple[Image, PhotoMetadata]:
        """Read a photo: HEIC, JPEG, PNG or TIFF.

        Orientation is applied and the ICC profile kept; DNG and ProRAW are refused (D116).

        Args:
            path: The photo file.

        Returns:
            The image and its metadata.
        """
        ...


@runtime_checkable
class PhotoSink(Protocol):
    """Writes corrected photos (IF-6)."""

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

        Args:
            image: The corrected image.
            meta: The source photo's metadata.
            out_path: The output file.
            bit_depth: The PNG bit depth, 8 or 16.
            provenance: The provenance to embed, or None.
        """
        ...
