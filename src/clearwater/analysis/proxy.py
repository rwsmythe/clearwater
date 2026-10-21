"""The analysis proxy (AD-5): a block mean towards a 540-line short side, quantised to uint8.

The rule is the twin of :func:`clearwater.gui.imaging.downscale` and
:func:`clearwater.gui.imaging.statistics_factor` (CHARC ruling Q3: ``clearwater.analysis`` may
not import ``gui``, so the rule is restated here and a test asserts the two agree). The block
mean is kept in float64 and quantised from there: quantising the float32 mean the GUI returns
misrounds about half of the exact ties of 8-bit data (WP3.11 ledger, premise P2).
"""

from __future__ import annotations

from typing import Any

import numpy as np
from numpy.typing import NDArray

from clearwater.interfaces import ArrayBackend, ColorDescription, Frame, Image

PROXY_SHORT_SIDE = 540
"""The short side the proxy is reduced towards (AD-5)."""


def proxy_factor(height: int, width: int) -> int:
    """Return the block-mean factor of the proxy: ``max(1, min(height, width) // 540)``.

    Args:
        height: Source height in pixels.
        width: Source width in pixels.

    Returns:
        The factor: 4 for 4K (960 x 540), 5 for 5.3K, 1 below 1080 lines.
    """
    return max(1, min(height, width) // PROXY_SHORT_SIDE)


def block_mean(pixels: NDArray[Any], k: int) -> NDArray[np.float64]:
    """Return the block mean of ``pixels`` by an integer factor, in float64 (the S3 rule).

    Each output pixel is the mean of the source pixels its ``k x k`` block covers; the output is
    ``ceil(H / k) x ceil(W / k)`` and the last row and column of blocks average fewer pixels
    when ``k`` does not divide the size. Cast to float32 it equals
    ``clearwater.gui.imaging.downscale(pixels, k)`` bit for bit.

    Args:
        pixels: ``(H, W, C)`` host array.
        k: The factor, at least 1.

    Returns:
        float64 ``(ceil(H / k), ceil(W / k), C)``.

    Raises:
        ValueError: ``k`` is below 1.
    """
    if k < 1:
        raise ValueError(f"the block-mean factor must be at least 1, got {k}")
    if k == 1:
        return np.asarray(pixels, dtype=np.float64)
    height, width = pixels.shape[0], pixels.shape[1]
    rows = np.arange(0, height, k)
    cols = np.arange(0, width, k)
    summed = np.add.reduceat(pixels, rows, axis=0, dtype=np.float64)
    summed = np.add.reduceat(summed, cols, axis=1)
    row_counts = np.minimum(k, height - rows).astype(np.float64)
    col_counts = np.minimum(k, width - cols).astype(np.float64)
    counts = row_counts[:, None, None] * col_counts[None, :, None]
    mean: NDArray[np.float64] = summed / counts
    return mean


def quantise(mean: NDArray[np.float64]) -> NDArray[np.uint8]:
    """Quantise a [0, 1] mean to uint8, rounding half up: ``floor(x * 255 + 0.5)``, clipped.

    Args:
        mean: float64 values, nominally in [0, 1].

    Returns:
        The uint8 levels.
    """
    levels = np.floor(np.asarray(mean, dtype=np.float64) * 255.0 + 0.5)
    return np.clip(levels, 0, 255).astype(np.uint8)


def make_proxy(pixels: NDArray[Any]) -> NDArray[np.uint8]:
    """Return the uint8 proxy of a full-resolution host image (AD-5).

    Args:
        pixels: float ``(H, W, 3)`` RGB in [0, 1], on the host.

    Returns:
        uint8 ``(ceil(H / k), ceil(W / k), 3)`` with ``k = proxy_factor(H, W)``.

    Raises:
        ValueError: ``pixels`` is not an ``(H, W, 3)`` array.
    """
    if pixels.ndim != 3 or pixels.shape[2] != 3:
        raise ValueError(f"a frame must be (H, W, 3), got shape {tuple(pixels.shape)}")
    k = proxy_factor(pixels.shape[0], pixels.shape[1])
    return quantise(block_mean(pixels, k))


def frame_pixels_on_host(frame: Frame, backend: ArrayBackend) -> NDArray[Any]:
    """Return a frame's pixels as a host array.

    Args:
        frame: The decoded frame.
        backend: The backend that converts device arrays to the host.

    Returns:
        The pixels on the host.
    """
    if frame.device == "cpu":
        return np.asarray(frame.pixels)
    return backend.to_host(frame.pixels)


def proxy_image(
    proxy: NDArray[np.uint8],
    backend: ArrayBackend,
    color: ColorDescription,
    orientation_applied: bool,
) -> Image:
    """Wrap a STORED uint8 proxy as the float32 image every statistic is measured on (AD-5).

    Args:
        proxy: The proxy as read back from the cache.
        backend: The backend to place the pixels on.
        color: The source's colour description.
        orientation_applied: Carried from the frame.

    Returns:
        float32 ``proxy / 255`` on ``backend``.
    """
    pixels = np.asarray(proxy, dtype=np.float32) / np.float32(255.0)
    return Image(
        pixels=backend.asarray(pixels, np.float32),
        device=backend.device,
        color=color,
        orientation_applied=orientation_applied,
    )
