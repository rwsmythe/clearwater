"""Disk-space estimate and check (spec 8.4, D87).

The estimate is deliberately simple and errs high: the user is warned before an export if the
destination volume looks too small. Running out of space anyway is handled by the safe write
(:mod:`clearwater.jobs.safe_write`), which deletes the partial output.

The ratios are the AD-12 targets (High about the camera's rate, Standard about half, Draft about a
quarter) and are PROVISIONAL until WP3.10 verifies the quality levels; they live here, in one
place.
"""

from __future__ import annotations

import math
import os
import shutil
from dataclasses import dataclass
from pathlib import Path

from clearwater.interfaces.settings import Settings

QUALITY_RATIO: dict[str, float] = {"high": 1.0, "standard": 0.5, "draft": 0.25}
"""Output size over source size per quality level (AD-12, PROVISIONAL until WP3.10)."""

MARGIN = 1.25
"""Safety margin multiplied into the video estimate."""

PHOTO_OVERHEAD_BYTES = 1024 * 1024
"""Allowance for the embedded colour profile and metadata of a photo."""


@dataclass(frozen=True)
class SpaceCheck:
    """The result of a free-space check.

    Attributes:
        folder: The destination folder that was measured.
        needed: Bytes the planned outputs are estimated to need.
        free: Bytes free on the destination volume.
        ok: True if ``free >= needed``.
    """

    folder: Path
    needed: int
    free: int
    ok: bool

    def message(self) -> str:
        """Describe the shortfall (or the room) with both figures, in ASCII.

        Returns:
            A one-line message naming the folder, the bytes needed and the bytes free.
        """
        verdict = "Enough" if self.ok else "Not enough"
        return (
            f"{verdict} free space in {self.folder}: "
            f"need {self.needed:,} bytes, {self.free:,} free."
        )


def estimate_video_bytes(source_size: int, settings: Settings, source_bit_depth: int) -> int:
    """Estimate the bytes a video output needs (D87).

    ``source_size x QUALITY_RATIO[level] x MARGIN``, doubled when 10-bit output is requested for
    an 8-bit source (D76).

    Args:
        source_size: Size of the source file in bytes.
        settings: The settings (``quality_level``, ``ten_bit_for_eight_bit``).
        source_bit_depth: The source bit depth, 8 or 10.

    Returns:
        The estimated output size in bytes, rounded up.

    Raises:
        ValueError: If the quality level is unknown or the size is negative.
    """
    if source_size < 0:
        raise ValueError(f"source size must be >= 0, got {source_size}")
    try:
        ratio = QUALITY_RATIO[settings.quality_level]
    except KeyError:
        raise ValueError(f"unknown quality level {settings.quality_level!r}") from None
    estimate = source_size * ratio * MARGIN
    if settings.ten_bit_for_eight_bit and source_bit_depth == 8:
        estimate *= 2
    return math.ceil(estimate)


def estimate_photo_bytes(width: int, height: int, bit_depth: int) -> int:
    """Estimate the bytes a photo PNG needs: the uncompressed size plus profile allowance.

    Args:
        width: Image width in pixels.
        height: Image height in pixels.
        bit_depth: PNG bit depth per channel, 8 or 16.

    Returns:
        ``width * height * 3 * bit_depth / 8 + PHOTO_OVERHEAD_BYTES``.

    Raises:
        ValueError: If a dimension is not positive or the bit depth is not 8 or 16.
    """
    if width <= 0 or height <= 0:
        raise ValueError(f"image size must be positive, got {width}x{height}")
    if bit_depth not in (8, 16):
        raise ValueError(f"PNG bit depth must be 8 or 16, got {bit_depth}")
    return width * height * 3 * bit_depth // 8 + PHOTO_OVERHEAD_BYTES


def check_free_space(folder: Path, needed: int) -> SpaceCheck:
    """Compare the bytes needed with the free space of the folder's volume.

    The nearest existing ancestor of ``folder`` is measured, so a folder that does not exist yet
    still gives its volume's figure. A batch sums its estimates per volume and checks once.

    Args:
        folder: The destination folder.
        needed: The estimated bytes needed.

    Returns:
        The check, with both figures.
    """
    probe = Path(os.path.abspath(folder))
    while not probe.exists() and probe.parent != probe:
        probe = probe.parent
    free = shutil.disk_usage(probe).free
    return SpaceCheck(folder=folder, needed=needed, free=free, ok=free >= needed)
