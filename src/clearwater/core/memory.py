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
115, 246 and 261 MiB on the RTX 4070 Laptop GPU, the desktop's own use included; the largest
rounded up)."""

NVDEC_FLOOR_BYTES = 80 * _MIB
"""The fixed part of one FFmpeg NVDEC decoding session (see :func:`session_bytes`)."""

NVDEC_BYTES_PER_PIXEL = 51
"""The per-pixel part of one NVDEC session, bytes per pixel of the decoded frame."""

NVENC_FLOOR_BYTES = 368 * _MIB
"""The fixed part of one FFmpeg NVENC encoding session (see :func:`session_bytes`)."""

NVENC_BYTES_PER_PIXEL = 36
"""The per-pixel part of one NVENC session, bytes per pixel of the encoded frame."""

SESSION_KINDS: tuple[str, ...] = ("nvdec", "nvenc")
"""The hardware session kinds :func:`session_bytes` knows."""


def session_bytes(kind: str, height: int, width: int) -> int:
    """Estimate the device memory of one FFmpeg hardware session at a frame size.

    ``floor + per_pixel x (width x height)``, the line through two measured sizes, fitted
    EXACTLY (two sizes, two constants per kind; CHARC ruling ``3f17304438bc2555``). Both sizes
    are in-process attributions of one export job each on the RTX 4070 Laptop GPU (WP3.21 task
    10; ``docs/proofs/wp3.21-ledger.md``, "The task 10 fix"), read device-wide (``nvidia-smi``
    ``memory.used``) less the device-wide figure after the process's probe (its context) less the
    pool's reserved bytes read at the same instant: that REMAINDER is FFmpeg's (``nvidia-smi``
    reports no per-process figure under WDDM). The second decoder is the remainder's rise during
    the overlap over the frames-only plateau (max); NVENC is the frames-only remainder (max) less
    one decoder:

    - 5.3K 8:7 (5312 x 4648, synthetic, device frames ON and OFF, the larger of the two): NVDEC
      1,256.0 MiB, NVENC 1,192.3 MiB;
    - 4K (3840 x 2160, GX011627, c3 cold, device frames ON): NVDEC 472.0 MiB, NVENC 642.4 MiB.

    Solved: NVDEC 75.4 MiB + 50.14 B/px, NVENC 364.2 MiB + 35.17 B/px (both floors above 0, so no
    clamp); rounded UP to the constants (80 MiB + 51 B/px, 368 MiB + 36 B/px). Residual of the
    rounded line over the measured terms: NVDEC +11.4 MiB at 4K and +24.9 at 5.3K, NVENC +10.4
    and +23.4. A frame below 4K, 1080p included, is an extrapolation of the same line (1080p:
    NVDEC 181, NVENC 439 MiB), not a measurement.

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
    figure is compared with a device-wide peak; it never chooses the backend. At 5.3K the job
    total exceeds the card because its pool part is the selection bound (loose by design:
    measured 4,427 MiB against 6,281), so the binding 5.3K check is the pool's reserved peak
    against the pool estimate, with the covered-row tests; the device-wide check is recorded at
    5.3K and binds at 4K.

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
