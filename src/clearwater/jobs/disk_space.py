"""Disk-space estimate and check (spec 8.4, D87).

The estimate is deliberately simple and errs high: the user is warned before an export if the
destination volume looks too small. Running out of space anyway is handled by the safe write
(:mod:`clearwater.jobs.safe_write`), which deletes the partial output.

A video estimate is the larger of a source-relative term and the AD-12 pixel-rate ceiling for the
quality level, times :data:`MARGIN` (DR-48, ruled 2026-10-27). The ratios are WP3.10's measured
file ratios (report section 7.2: busy libx265 about 1.07 / 0.486 / 0.25, rounded up); the ceiling
comes from ``clearwater.io.video.encode`` (``NVENC_BITS_PER_PIXEL``, ``NVENC_RATE_SHARE``), read at
call time so the constants have one source. Both live here, in one place.
"""

from __future__ import annotations

import math
import os
import shutil
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path

from clearwater.interfaces.settings import Settings
from clearwater.io.video import encode as _encode

QUALITY_RATIO: dict[str, Fraction] = {
    "high": Fraction(11, 10),
    "standard": Fraction(1, 2),
    "draft": Fraction(1, 4),
}
"""Output size over source size per quality level (WP3.10 report 7.2, busy libx265; DR-48).

Exact decimals 1.10 / 0.50 / 0.25: a binary float such as ``1.10`` would add a byte to the
estimate at some sizes (Reviewer B B4)."""

MARGIN = Fraction(5, 4)
"""Safety margin multiplied into the video estimate (1.25, exact)."""

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
        folder = str(self.folder).encode("ascii", "backslashreplace").decode("ascii")
        return f"{verdict} free space in {folder}: need {self.needed:,} bytes, {self.free:,} free."


def estimate_video_bytes(
    source_size: int,
    settings: Settings,
    *,
    width: int,
    height: int,
    frame_rate: Fraction,
    duration_s: Fraction,
) -> int:
    """Estimate the bytes a video output needs (D87, DR-48).

    ``max(QUALITY_RATIO[level] x source_size, ceiling x duration_s / 8) x MARGIN``, where the
    ceiling in bits per second is ``NVENC_BITS_PER_PIXEL / NVENC_RATE_SHARE[level] x width x
    height x frame_rate`` (AD-12; WP3.10 report 7.2). The same for both encoders: the ceiling
    bounds NVENC by construction and lies above every measured libx265 output; the ratio term
    binds on high-rate sources. A 10-bit output is not doubled (measured 0-1 % over 8-bit).

    Args:
        source_size: Size of the source file in bytes.
        settings: The settings (``quality_level``).
        width: The source's coded width in pixels.
        height: The source's coded height in pixels.
        frame_rate: The source's average frame rate in frames per second.
        duration_s: The source's duration in seconds.

    Returns:
        The estimated output size in bytes, rounded up.

    Raises:
        ValueError: If the quality level is unknown, the size or duration is negative, or a
            dimension or the frame rate is not positive.
    """
    if source_size < 0:
        raise ValueError(f"source size must be >= 0, got {source_size}")
    if duration_s < 0:
        raise ValueError(f"duration must be >= 0, got {duration_s}")
    if width <= 0 or height <= 0 or frame_rate <= 0:
        raise ValueError(
            f"size and frame rate must be positive, got {width}x{height} @ {frame_rate}"
        )
    try:
        ratio = QUALITY_RATIO[settings.quality_level]
        share = _encode.NVENC_RATE_SHARE[settings.quality_level]
    except KeyError:
        raise ValueError(f"unknown quality level {settings.quality_level!r}") from None
    ceiling_bits_per_s = (
        Fraction(_encode.NVENC_BITS_PER_PIXEL) / share * width * height * Fraction(frame_rate)
    )
    ceiling_bytes = ceiling_bits_per_s * Fraction(duration_s) / 8
    relative_bytes = ratio * source_size
    return math.ceil(max(relative_bytes, ceiling_bytes) * MARGIN)


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
        still gives its volume's figure. Each export job checks its own item, inside the job, just
    before writing (CHARC ruling on WP3.14: per item, never batch-wide).

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
