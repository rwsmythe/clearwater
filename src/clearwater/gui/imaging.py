"""Downscale, statistics, render and display conversion for the preview (G2, D41, V8).

Pure functions on host NumPy arrays plus the conversion to a display ``QImage``. ``QImage`` and
``QColorSpace`` are value classes Qt documents as usable outside the GUI thread, so the preview
worker calls everything here; nothing here touches a ``QObject``.

The downscale rule (S3, RULED by CHARC 2026-10-21): :func:`downscale` is a block mean
by an integer factor ``k`` whose output is ``ceil(H / k) x ceil(W / k)``; each output pixel is
the mean of the source pixels its block covers, so the last row and column of blocks average
fewer pixels when ``k`` does not divide the size. The preview, the 1:1 path (``k == 1``) and
the V8 harness all use it, and the statistics proxy (question 5) is the same block mean with
:func:`statistics_factor`. This is the one owner of the rule: WP3.14 and WP4.1 cite it,
and V8's area average is this function.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import NDArray
from PySide6.QtCore import QByteArray
from PySide6.QtGui import QColorSpace, QImage

from clearwater.interfaces import (
    ArrayBackend,
    ColorDescription,
    CorrectionMethod,
    Image,
    ParameterSet,
    Statistics,
)

STATISTICS_SHORT_SIDE = 540
"""The short side the statistics proxy is reduced towards (AD-5's 540, question 5)."""

type Check = Callable[[], None]
"""Raises when the calling job has been superseded (the preview worker's cancellation point)."""


def _no_check() -> None:
    """A check that never raises."""


def downscale(pixels: NDArray[np.float32], k: int) -> NDArray[np.float32]:
    """Return the block mean of ``pixels`` by an integer factor (the S3 rule).

    Args:
        pixels: float32 ``(H, W, C)`` host array.
        k: The factor, at least 1; 1 returns ``pixels`` itself.

    Returns:
        float32 ``(ceil(H / k), ceil(W / k), C)``; each pixel is the mean of the source pixels
        its block covers (edge blocks cover fewer when ``k`` does not divide the size).

    Raises:
        ValueError: ``k`` is below 1.
    """
    if k < 1:
        raise ValueError(f"the downscale factor must be at least 1, got {k}")
    if k == 1:
        return pixels
    height, width = pixels.shape[0], pixels.shape[1]
    rows = np.arange(0, height, k)
    cols = np.arange(0, width, k)
    summed = np.add.reduceat(pixels, rows, axis=0, dtype=np.float64)
    summed = np.add.reduceat(summed, cols, axis=1)
    row_counts = np.minimum(k, height - rows).astype(np.float64)
    col_counts = np.minimum(k, width - cols).astype(np.float64)
    counts = row_counts[:, None, None] * col_counts[None, :, None]
    return np.asarray(summed / counts, dtype=np.float32)


def downscaled_size(height: int, width: int, k: int) -> tuple[int, int]:
    """Return the ``(height, width)`` :func:`downscale` produces for a factor.

    Args:
        height: Source height in pixels.
        width: Source width in pixels.
        k: The factor, at least 1.

    Returns:
        ``(ceil(height / k), ceil(width / k))``.
    """
    return -(-height // k), -(-width // k)


def view_factor(height: int, width: int, shown_height: float, shown_width: float) -> int:
    """Return the preview's downscale factor for a displayed size (question 7).

    The largest integer ``k`` for which the downscaled image still covers the displayed size in
    device pixels; Qt scales the remaining step for display only.

    Args:
        height: Source height in pixels.
        width: Source width in pixels.
        shown_height: The displayed height in device pixels.
        shown_width: The displayed width in device pixels.

    Returns:
        The factor, 1 when the image is shown at 1:1 or larger or the displayed size is empty;
        at most ``max(height, width)``, beyond which every factor gives the same 1 x 1 image (a
        displayed size of one device pixel or less on both axes is covered by every factor).
    """
    if shown_height <= 0 or shown_width <= 0:
        return 1
    limit = max(1, height, width)
    k = min(limit, max(1, math.floor(min(height / shown_height, width / shown_width))))
    while k < limit:
        h, w = downscaled_size(height, width, k + 1)
        if h < shown_height or w < shown_width:
            return k
        k += 1
    return k


def statistics_factor(height: int, width: int) -> int:
    """Return the block-mean factor of the statistics proxy (question 5, S3).

    Args:
        height: Source height in pixels.
        width: Source width in pixels.

    Returns:
        ``max(1, min(height, width) // 540)``: 4 for 4K (960x540), 5 for 5.3K (1063x598) and a
        12 MP photo (807x605), 11 for 48 MP (734x550).
    """
    return max(1, min(height, width) // STATISTICS_SHORT_SIDE)


def effective_parameters(method: CorrectionMethod, parameters: ParameterSet) -> dict[str, Any]:
    """Return the method defaults overlaid with the set's values (IF-9 sets may be partial).

    Args:
        method: The method whose schema applies.
        parameters: The parameter set.

    Returns:
        Parameter name -> value.
    """
    values: dict[str, Any] = {p.name: p.default for p in method.parameters}
    values.update(parameters.parameters)
    return values


def _on_backend(
    backend: ArrayBackend, pixels: NDArray[np.float32], color: ColorDescription
) -> Image:
    """Wrap host pixels as an IF-1 image on ``backend``."""
    return Image(
        pixels=backend.asarray(pixels, np.float32),
        device=backend.device,
        color=color,
        orientation_applied=True,
    )


def measure_statistics(
    method: CorrectionMethod,
    backend: ArrayBackend,
    image: Image,
    params: Mapping[str, Any],
    check: Check = _no_check,
) -> dict[str, Statistics]:
    """Measure every stage's statistics on the image's statistics proxy (D108, question 5).

    Args:
        method: The correction method.
        backend: The backend to measure on.
        image: The full-resolution host image.
        params: The effective parameter values.
        check: Called between stages; raises when the job is superseded.

    Returns:
        Stage name -> statistics, in stage order, each stage given the earlier results.
    """
    pixels = np.asarray(image.pixels, dtype=np.float32)
    k = statistics_factor(pixels.shape[0], pixels.shape[1])
    proxy = _on_backend(backend, downscale(pixels, k), image.color)
    results: dict[str, Statistics] = {}
    for stage in method.stages:
        check()
        results[stage.name] = method.analyze(stage.name, proxy, params, dict(results))
    return results


def render_host(
    method: CorrectionMethod,
    backend: ArrayBackend,
    pixels: NDArray[np.float32],
    color: ColorDescription,
    params: Mapping[str, Any],
    statistics: Mapping[str, Statistics],
) -> NDArray[np.float32]:
    """Render host pixels on ``backend`` and return the result on the host.

    Args:
        method: The correction method.
        backend: The backend to render on.
        pixels: float32 ``(H, W, 3)`` host pixels.
        color: The source colour description.
        params: The effective parameter values.
        statistics: The statistics of every stage.

    Returns:
        The corrected float32 host pixels.
    """
    rendered = method.render(_on_backend(backend, pixels, color), params, statistics)
    return np.asarray(backend.to_host(rendered.pixels), dtype=np.float32)


def to_display_uint8(pixels: NDArray[np.float32]) -> NDArray[np.uint8]:
    """Quantise float pixels for display: clip to [0, 1], ``round(x * 255)``.

    Args:
        pixels: float32 ``(H, W, 3)``.

    Returns:
        uint8 ``(H, W, 3)``, C-contiguous.
    """
    scaled = np.clip(pixels, 0.0, 1.0) * np.float32(255.0)
    return np.ascontiguousarray(np.rint(scaled).astype(np.uint8))


def display_image(rgb: NDArray[np.uint8], icc_profile: bytes | None) -> QImage:
    """Build the display copy of an 8-bit RGB array, converted to sRGB (question 8).

    The data is never changed: only this display copy is tagged with the source ICC profile and
    converted to sRGB. An untagged source, or a profile Qt cannot parse, is tagged as sRGB
    unchanged; the result is always tagged sRGB.

    Args:
        rgb: uint8 ``(H, W, 3)``.
        icc_profile: The source's embedded ICC profile, or None.

    Returns:
        An RGB888 ``QImage`` that owns its pixels.
    """
    data = np.ascontiguousarray(rgb)
    height, width = data.shape[0], data.shape[1]
    image = QImage(data.data, width, height, 3 * width, QImage.Format.Format_RGB888).copy()
    srgb = QColorSpace(QColorSpace.NamedColorSpace.SRgb)
    space = QColorSpace.fromIccProfile(QByteArray(icc_profile)) if icc_profile else QColorSpace()
    if not space.isValid():
        image.setColorSpace(srgb)
        return image
    image.setColorSpace(space)
    image = image.convertedToColorSpace(srgb)
    if image.format() != QImage.Format.Format_RGB888:
        image = image.convertToFormat(QImage.Format.Format_RGB888)
    return image


def image_bytes(image: QImage) -> NDArray[np.uint8]:
    """Return the RGB888 pixels of a ``QImage`` as a ``(H, W, 3)`` array copy.

    Args:
        image: Any ``QImage``; converted to RGB888 first when it is in another format.

    Returns:
        uint8 ``(H, W, 3)``.
    """
    rgb = image.convertToFormat(QImage.Format.Format_RGB888)
    height, width, stride = rgb.height(), rgb.width(), rgb.bytesPerLine()
    buffer = np.frombuffer(rgb.constBits(), dtype=np.uint8, count=stride * height)
    return buffer.reshape(height, stride)[:, : 3 * width].reshape(height, width, 3).copy()


@dataclass(frozen=True)
class V8Difference:
    """The V8 comparison of a preview against the export downscaled by the same rule.

    Attributes:
        k: The downscale factor compared at.
        mean_abs: Mean absolute difference, in [0, 1] units.
        max_abs: Maximum absolute difference, in [0, 1] units.
    """

    k: int
    mean_abs: float
    max_abs: float


def preview_export_difference(
    method: CorrectionMethod,
    backend: ArrayBackend,
    image: Image,
    params: Mapping[str, Any],
    statistics: Mapping[str, Statistics],
    k: int,
) -> V8Difference:
    """The V8 harness: ``render(downscale(image, k))`` against ``downscale(render(image), k)``.

    Uses the same :func:`downscale` and :func:`render_host` as the preview, so it measures the
    preview the user sees. AD-11's bound is mean <= 1/255 and max <= 3/255; WP4.x runs it with
    WP3.4's method.

    Args:
        method: Any IF-3 method.
        backend: The backend to render on.
        image: The full-resolution host image.
        params: The effective parameter values.
        statistics: The statistics both renders use (AD-4: the same for preview and export).
        k: The preview factor.

    Returns:
        The difference.
    """
    pixels = np.asarray(image.pixels, dtype=np.float32)
    preview = render_host(method, backend, downscale(pixels, k), image.color, params, statistics)
    export = downscale(render_host(method, backend, pixels, image.color, params, statistics), k)
    diff = np.abs(preview.astype(np.float64) - export.astype(np.float64))
    return V8Difference(k=k, mean_abs=float(diff.mean()), max_abs=float(diff.max()))
