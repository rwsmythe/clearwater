"""The working-set estimate that drives the CPU fallback (AD-1, D111, N4).

The estimate is the prototype's counted formula (``tools/prototype/backend.py``, WP1.2 Part A
and Part B): the peak of the correction core in float32 planes of the frame size, located with a
counting allocator at the finest EXPAND of the fusion pyramid collapse,

- 25 planes of results still alive (the device copy of the input, the compensated and
  white-balanced images and the two fusion inputs, 15; the ten weight maps, 10);
- 13 1/3 planes of fusion pyramids (the fused pyramid, the last input's Laplacian and blended
  pyramids, 4 each; its weight's Gaussian pyramid, 4/3);
- 11 3/4 planes of EXPAND temporaries at the finest level (the zero-stuffed image 3, its blur's
  row pass and result 3 + 3, the sample indicator and its blur 1 + 1, the coarser level 3/4);

50 1/12 planes in all, times 1.25 for the memory pool's rounding and fragmentation and for odd
pyramid sizes, plus 1 MiB for constant arrays and per-allocation rounding. At 4K
(3840 x 2160) that is 1,982 MiB, 1.16x the pool's reserved peak measured in WP1.2 Part B
(AD-1). The CUDA context and library workspaces are not counted: they already exist when the
decision is taken, so the figure is compared with the device's free memory.

Both built-in methods (``c3`` and ``ancuti2018``, IF-3) share the count (WP3.1 brief ruling 3;
the product peak is re-checked by WP3.4). Any other method id is refused, so that a new method
registers its own count instead of being under-estimated (WP3.1 round-0 ruling R0-5).

The device-wide figure of a GPU export job (:func:`job_device_memory_estimate_bytes`, WP3.21
task 10, CHARC rulings ``cadc39fc8a199a57`` and ``7f58cfc1``) is a second, separate figure: what
the whole card holds while the job runs, against which a measured device-wide peak
(``nvidia-smi`` ``memory.used``) is checked. It does NOT drive the backend choice
(``select_backend`` stays on the estimate above). It adds to the pool estimate (the GPU
backend's, base plus the FFT bound) the CUDA context and, per hardware session, FFmpeg's NVDEC
decoders and its NVENC encoder, each ``floor + bytes per pixel x (width x height)``.
"""

from __future__ import annotations

import math

METHOD_IDS: tuple[str, ...] = ("c3", "ancuti2018")
"""The method ids the estimate knows (IF-3 ``CorrectionMethod.id``)."""

_PEAK_PLANES = 25.0 + 40.0 / 3.0 + 11.75
_ESTIMATE_MARGIN = 1.25
_FIXED_BYTES = 1024 * 1024


def memory_estimate_bytes(height: int, width: int, method_id: str) -> int:
    """Estimate, as an upper bound, the device memory one frame of this size needs.

    Args:
        height: Frame height in pixels, at least 1.
        width: Frame width in pixels, at least 1.
        method_id: The correction method id, one of :data:`METHOD_IDS`.

    Returns:
        The estimate in bytes.

    Raises:
        ValueError: A size is under 1, or ``method_id`` is not one of :data:`METHOD_IDS`.
    """
    if method_id not in METHOD_IDS:
        raise ValueError(
            f"no memory estimate for method {method_id!r}; known: {', '.join(METHOD_IDS)}"
        )
    if height < 1 or width < 1:
        raise ValueError(f"frame size must be at least 1 x 1, got {height} x {width}")
    pixels = int(height) * int(width)
    return math.ceil(_PEAK_PLANES * _ESTIMATE_MARGIN * 4 * pixels) + _FIXED_BYTES


_MIB = 1024 * 1024

CUDA_CONTEXT_BYTES = 272 * _MIB
"""The device-wide memory this process holds after the GPU probe, before any frame (measured
246 and 261 MiB on the RTX 4070 Laptop GPU, the desktop's own use included; rounded up)."""

NVDEC_FLOOR_BYTES = 416 * _MIB
"""The fixed part of one FFmpeg NVDEC decoding session (see :func:`session_bytes`)."""

NVDEC_BYTES_PER_PIXEL = 37
"""The per-pixel part of one NVDEC session, bytes per pixel of the decoded frame."""

NVENC_FLOOR_BYTES = 384 * _MIB
"""The fixed part of one FFmpeg NVENC encoding session (see :func:`session_bytes`)."""

NVENC_BYTES_PER_PIXEL = 35
"""The per-pixel part of one NVENC session, bytes per pixel of the encoded frame."""

SESSION_KINDS: tuple[str, ...] = ("nvdec", "nvenc")
"""The hardware session kinds :func:`session_bytes` knows."""


def session_bytes(kind: str, height: int, width: int) -> int:
    """Estimate the device memory of one FFmpeg hardware session at a frame size.

    ``floor + per_pixel x (width x height)``, the line through two measured sizes, both read
    device-wide (``nvidia-smi`` ``memory.used``) during an export job on the RTX 4070 Laptop GPU
    (WP3.21 task 10; ``docs/proofs/wp3.21-ledger.md``, "The task 10 fix"):

    - 5.3K 8:7 (5312 x 4648), in-process attribution: the second decoder = the overlap's rise over
      the frames-only plateau, max 1,256 MiB (1,237 with device frames); NVENC = the frames-only
      remainder (device-wide - context - pool), max 2,448, less one decoder = 1,192 MiB.
    - 4K (3840 x 2160): the cold c3 rows' device-wide peak 3,244 MiB (two decoders and NVENC) less
      the 4K render pool peak 947 MiB (WP3.21 task 6 memory re-read, the only measured 4K pool
      figure) and the context 261 = 2,036 MiB, split between the kinds in the 5.3K proportion
      (1,256 : 1,256 : 1,192): NVDEC 690, NVENC 655 MiB.

    Solved: NVDEC 404.3 MiB + 36.17 B/px, NVENC 383.7 MiB + 34.33 B/px; rounded UP to the
    constants (416 MiB + 37 B/px, 384 MiB + 35 B/px). Residual of the rounded line over the
    measured terms: NVDEC +31 MiB at 5.3K and +18 at 4K, NVENC +16 and +6. The 4K split rests on
    the 5.3K proportion and on the render-only pool figure (a larger measured 4K job pool would
    lower the floors). A frame below 4K, 1080p included, is an extrapolation of the same line
    (1080p: NVDEC 489, NVENC 453 MiB), not a measurement.

    Args:
        kind: ``"nvdec"`` or ``"nvenc"``.
        height: Frame height in pixels, at least 1.
        width: Frame width in pixels, at least 1.

    Returns:
        The estimate in bytes.

    Raises:
        ValueError: An unknown kind or a size under 1.
    """
    if kind not in SESSION_KINDS:
        raise ValueError(f"no session estimate for {kind!r}; known: {', '.join(SESSION_KINDS)}")
    if height < 1 or width < 1:
        raise ValueError(f"frame size must be at least 1 x 1, got {height} x {width}")
    pixels = int(height) * int(width)
    if kind == "nvdec":
        return NVDEC_FLOOR_BYTES + NVDEC_BYTES_PER_PIXEL * pixels
    return NVENC_FLOOR_BYTES + NVENC_BYTES_PER_PIXEL * pixels


def job_device_memory_estimate_bytes(
    height: int, width: int, pool_estimate_bytes: int, *, decoders: int, nvenc: bool
) -> int:
    """Estimate the device-wide memory a GPU export job of this frame size holds (WP3.21).

    The pool estimate (the GPU backend's ``memory_estimate_bytes``: the base above plus the FFT
    Gaussian's bound, passed in so this module stays free of the backend) + the CUDA context
    (:data:`CUDA_CONTEXT_BYTES`) + ``decoders`` NVDEC sessions + one NVENC session when the job
    encodes with NVENC (:func:`session_bytes`). A cold video job has TWO decoders during the
    overlap (the export's and the analysis's); a job over a complete cache entry has one. The
    figure is compared with a device-wide peak; it never chooses the backend.

    Args:
        height: Frame height in pixels, at least 1.
        width: Frame width in pixels, at least 1.
        pool_estimate_bytes: The GPU backend's pool estimate for this frame, at least 0.
        decoders: NVDEC sessions open at once, at least 0.
        nvenc: Whether the job encodes with NVENC.

    Returns:
        The estimate in bytes.

    Raises:
        ValueError: A size under 1, or a negative pool estimate or decoder count.
    """
    if pool_estimate_bytes < 0 or decoders < 0:
        raise ValueError(
            f"pool estimate and decoders must be at least 0, got {pool_estimate_bytes}, {decoders}"
        )
    total = (
        pool_estimate_bytes + CUDA_CONTEXT_BYTES + decoders * session_bytes("nvdec", height, width)
    )
    if nvenc:
        total += session_bytes("nvenc", height, width)
    return total
