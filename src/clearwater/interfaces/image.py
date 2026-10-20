"""IF-1: the image and frame types (architecture section 3).

An :class:`Image` is a float32 RGB array in ``[0, 1]`` with its colour description; a
:class:`Frame` is an image with its exact source presentation time. Every other interface
passes these types around; this module imports nothing else from the package.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

import numpy as np
from numpy.typing import NDArray

type Array = NDArray[np.float32]
"""The backend's array type: always float32, shape (H, W, 3), RGB, display-encoded, in [0, 1].

Typed as a NumPy array. A CuPy ``ndarray`` is accepted structurally at run time (AD-1): the
product runs one code path on NumPy or CuPy, and CuPy is never imported by this package.
"""


@dataclass(frozen=True)
class ColorDescription:
    """How the pixel values of an image or video stream are to be read (IF-1).

    Attributes:
        primaries: ``"bt709"``, ``"display-p3"`` or ``"unknown"``.
        transfer: ``"bt709"``, ``"srgb"`` or ``"unknown"``; HLG and PQ never reach here (they
            are refused at probe).
        matrix: ``"bt709"``, ``"bt601"``, ``"identity"`` (photos) or ``"unknown"``.
        range: ``"full"`` or ``"limited"``.
        bit_depth: Source bit depth: 8, 10 or 16.
        assumed: True when the D54 defaults were applied (warn once per source).
        icc_profile: Photos: the embedded ICC profile, carried to the output; otherwise None.
    """

    primaries: str
    transfer: str
    matrix: str
    range: str
    bit_depth: int
    assumed: bool
    icc_profile: bytes | None


@dataclass(frozen=True)
class Image:
    """A float32 RGB image on a device, with its colour description (IF-1).

    Attributes:
        pixels: float32 ``(H, W, 3)`` RGB in [0, 1], on ``device``.
        device: ``"cpu"`` or ``"cuda:0"``.
        color: The colour description of the source.
        orientation_applied: Photos: the EXIF orientation is already applied to the pixels.
    """

    pixels: Array
    device: str
    color: ColorDescription
    orientation_applied: bool


@dataclass(frozen=True)
class Frame(Image):
    """A decoded video frame: an :class:`Image` with its exact presentation time (IF-1).

    Attributes:
        pts: Exact source presentation time in seconds (``pts_ticks / time_base``).
        pts_ticks: The presentation time in stream ticks; the key statistics are stored under
            (D95).
        time_base: The stream's time base.
        index: Decode order position; informational only, never a key.
    """

    pts: Fraction
    pts_ticks: int
    time_base: Fraction
    index: int
