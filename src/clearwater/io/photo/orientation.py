"""EXIF orientation applied to pixels (D63, spec 8.1)."""

from __future__ import annotations

from typing import Any

import numpy as np
from numpy.typing import NDArray


def apply_orientation(pixels: NDArray[Any], tag: int) -> NDArray[Any]:
    """Return ``pixels`` physically rotated or flipped so the EXIF ``tag`` reads as normal.

    The eight values follow the EXIF table: 2 mirrors left to right, 3 rotates 180 degrees, 4
    mirrors top to bottom, 5 transposes, 6 rotates 90 degrees clockwise, 7 transposes across
    the anti-diagonal and 8 rotates 90 degrees anticlockwise (the same as Pillow's
    ``ImageOps.exif_transpose``, which a test compares against).

    Args:
        pixels: An array shaped ``(H, W)`` or ``(H, W, C)``, of any dtype.
        tag: The EXIF Orientation, 1 to 8.

    Returns:
        A C-contiguous array; for 5 to 8 its height and width are swapped.

    Raises:
        ValueError: ``tag`` is not 1 to 8.
    """
    if tag == 1:
        out = pixels
    elif tag == 2:
        out = pixels[:, ::-1]
    elif tag == 3:
        out = pixels[::-1, ::-1]
    elif tag == 4:
        out = pixels[::-1]
    elif tag == 5:
        out = pixels.swapaxes(0, 1)
    elif tag == 6:
        out = pixels.swapaxes(0, 1)[:, ::-1]
    elif tag == 7:
        out = pixels.swapaxes(0, 1)[::-1, ::-1]
    elif tag == 8:
        out = pixels.swapaxes(0, 1)[::-1]
    else:
        raise ValueError(f"EXIF orientation must be 1 to 8, got {tag}")
    return np.ascontiguousarray(out)
