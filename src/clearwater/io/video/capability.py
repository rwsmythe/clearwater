"""Encoder capability detection (D74) and the one ``"auto"`` encoder rule (WP3.10).

:func:`detect_capabilities` reports, for the two HEVC encoders Clearwater offers (``hevc_nvenc``
on the graphics card and the software ``libx265``), whether each is usable and at which bit
depths, with a reason the settings dialog can show when it is not (D74: "unavailable options
are shown disabled with a reason"). It asks FFmpeg for its encoder list, then runs one
one-frame test encode per encoder and bit depth to FFmpeg's null muxer (the listing alone does
not tell whether an NVIDIA device is present); the four tests run at once and the result is
cached for the process.

:func:`resolve_encoder` is the single rule for the ``"auto"`` setting (G12: "NVENC when
available, else the software encoder"); the settings dialog and the export call it, and the
sink only ever receives the resolved name, which is what provenance records.

:func:`tool_env` is the environment of every FFmpeg and ffprobe process the detection and the sink
start (the encoder, the test encodes and the packet listings of :mod:`.verify`).
"""

from __future__ import annotations

import os
import subprocess
import threading
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from clearwater.interfaces.video import EncoderCapability
from clearwater.io.video.inputs import ascii_text
from clearwater.io.video.probe import VideoProbeError, find_tool

AUTO = "auto"
"""The encoder setting that :func:`resolve_encoder` resolves (IF-10 ``video_encoder``)."""

HARDWARE_ENCODER = "hevc_nvenc"
"""FFmpeg's NVIDIA HEVC encoder."""

SOFTWARE_ENCODER = "libx265"
"""FFmpeg's software HEVC encoder."""

ENCODERS = (HARDWARE_ENCODER, SOFTWARE_ENCODER)
"""The encoders Clearwater offers, in the order ``"auto"`` prefers them."""

BIT_DEPTHS = (8, 10)
"""The output bit depths tested per encoder (D25, D76)."""

TEST_TIMEOUT_S = 30
"""Seconds one test encode or the encoder listing may take before it counts as failed."""

_TEST_PIX_FMT = {
    (HARDWARE_ENCODER, 8): "yuv420p",
    (HARDWARE_ENCODER, 10): "p010le",
    (SOFTWARE_ENCODER, 8): "yuv420p",
    (SOFTWARE_ENCODER, 10): "yuv420p10le",
}
_PROFILE = {8: "main", 10: "main10"}
_NO_DEVICE_MARKERS = (
    "no capable devices found",
    "cannot load nvcuda",
    "cannot load libcuda",
    "cannot load libnvidia-encode",
    "nvenc api version",
    "unsupported device",
    "no nvenc capable devices",
    "cuinit",
)
"""Lower-case stderr fragments of an NVENC test that failed for want of a usable device."""

_cache: dict[str, tuple[EncoderCapability, ...]] = {}
_lock = threading.Lock()


def tool_env() -> dict[str, str]:
    """Return the environment for an FFmpeg or ffprobe process: this one without ``FFREPORT``.

    ``FFREPORT`` makes both tools write a log file of their own (by default into the current
    folder), which would be a file written beside ``out_path``; the sink writes ``out_path``
    only.

    Returns:
        A copy of ``os.environ`` without ``FFREPORT`` (in any letter case).
    """
    return {key: value for key, value in os.environ.items() if key.upper() != "FFREPORT"}


def _run(command: Sequence[str]) -> tuple[int, str]:
    """Run a short FFmpeg command and return its exit status and its output (stdout + stderr)."""
    try:
        done = subprocess.run(
            list(command),
            stdin=subprocess.DEVNULL,
            capture_output=True,
            timeout=TEST_TIMEOUT_S,
            check=False,
            env=tool_env(),
        )
    except subprocess.TimeoutExpired:
        return -1, f"timed out after {TEST_TIMEOUT_S} s"
    except OSError as error:
        return -1, str(error)
    return done.returncode, (done.stdout + done.stderr).decode("utf-8", errors="replace")


def _listed(ffmpeg: Path) -> tuple[set[str], str | None]:
    """Return the encoder names FFmpeg lists, or an empty set and the reason it failed."""
    status, text = _run([str(ffmpeg), "-hide_banner", "-encoders"])
    if status != 0:
        return set(), _tail(text)
    names = set()
    for line in text.splitlines():
        parts = line.split()
        if len(parts) >= 2 and len(parts[0]) == 6 and parts[0][0] == "V":
            names.add(parts[1])
    return names, None


def trial_encode_command(ffmpeg: Path, encoder: str, bit_depth: int) -> list[str]:
    """Return the one-frame test encode of one encoder at one bit depth (to the null muxer).

    Args:
        ffmpeg: The ``ffmpeg`` executable.
        encoder: ``"hevc_nvenc"`` or ``"libx265"``.
        bit_depth: 8 or 10.

    Returns:
        The command; it writes no file.
    """
    extra = ["-x265-params", "log-level=error"] if encoder == SOFTWARE_ENCODER else []
    return [
        str(ffmpeg),
        "-nostdin",
        "-hide_banner",
        "-loglevel",
        "error",
        "-f",
        "lavfi",
        "-i",
        "color=c=black:s=256x256:r=25:d=0.04",
        "-frames:v",
        "1",
        "-c:v",
        encoder,
        *extra,
        "-pix_fmt",
        _TEST_PIX_FMT[(encoder, bit_depth)],
        "-profile:v",
        _PROFILE[bit_depth],
        "-f",
        "null",
        "-",
    ]


def _tail(text: str, limit: int = 300) -> str:
    """Return the last non-empty lines of a tool's output, ASCII-safe and at most ``limit``."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return ascii_text(" | ".join(lines[-3:]))[-limit:]


def _reason(encoder: str, failures: Sequence[str]) -> str:
    """Return the user-readable reason an encoder failed every test encode."""
    joined = " ".join(failures).lower()
    if encoder == HARDWARE_ENCODER and any(marker in joined for marker in _NO_DEVICE_MARKERS):
        return (
            "No NVIDIA graphics card with a video encoder was found (or its driver is too old), "
            "so the NVENC encoder cannot be used."
        )
    detail = failures[0] if failures else "no detail"
    return f"The {encoder} test encode failed: {detail}"


def _detect(ffmpeg: Path) -> tuple[EncoderCapability, ...]:
    """Detect the capabilities with one listing and the test encodes (no cache)."""
    listed, listing_error = _listed(ffmpeg)
    if listing_error is not None:
        reason = f"FFmpeg could not list its encoders: {listing_error}"
        return tuple(
            EncoderCapability(name, False, reason, (), name == HARDWARE_ENCODER)
            for name in ENCODERS
        )
    tests = [(name, depth) for name in ENCODERS if name in listed for depth in BIT_DEPTHS]
    with ThreadPoolExecutor(max_workers=max(1, len(tests))) as pool:
        results = list(pool.map(lambda t: _run(trial_encode_command(ffmpeg, *t)), tests))
    outcome = dict(zip(tests, results, strict=True))
    capabilities = []
    for name in ENCODERS:
        hw = name == HARDWARE_ENCODER
        if name not in listed:
            reason = f"This FFmpeg build does not include the {name} encoder."
            capabilities.append(EncoderCapability(name, False, reason, (), hw))
            continue
        depths = tuple(d for d in BIT_DEPTHS if outcome[(name, d)][0] == 0)
        if depths:
            capabilities.append(EncoderCapability(name, True, None, depths, hw))
        else:
            failures = [_tail(outcome[(name, d)][1]) for d in BIT_DEPTHS]
            capabilities.append(EncoderCapability(name, False, _reason(name, failures), (), hw))
    return tuple(capabilities)


def detect_capabilities(*, refresh: bool = False) -> tuple[EncoderCapability, ...]:
    """Return whether each encoder is available and at which bit depths (D74).

    The first call runs the detection (under about two seconds: one listing and four one-frame
    test encodes in parallel); later calls return the cached result.

    Args:
        refresh: Detect again instead of returning the cached result.

    Returns:
        One entry per encoder in :data:`ENCODERS`, with ``reason`` set when it is unavailable.
        When ``ffmpeg`` itself is missing, every entry is unavailable with that reason.
    """
    try:
        ffmpeg = find_tool("ffmpeg")
    except VideoProbeError as error:
        return tuple(
            EncoderCapability(name, False, str(error), (), name == HARDWARE_ENCODER)
            for name in ENCODERS
        )
    key = str(ffmpeg)
    with _lock:
        if refresh or key not in _cache:
            _cache[key] = _detect(ffmpeg)
        return _cache[key]


def resolve_encoder(setting: str, capabilities: Sequence[EncoderCapability]) -> str:
    """Resolve the encoder setting to the encoder actually used (the one ``"auto"`` rule).

    ``"auto"`` becomes ``hevc_nvenc`` when it is available, else ``libx265`` (G12). An explicit
    encoder name is returned unchanged; the sink refuses it at ``open`` if it is unavailable.

    Args:
        setting: ``"auto"``, ``"hevc_nvenc"`` or ``"libx265"`` (IF-10 ``video_encoder``).
        capabilities: The result of :func:`detect_capabilities` (or the sink's
            ``capabilities()``).

    Returns:
        The encoder name, never ``"auto"``.

    Raises:
        VideoEncodeError: ``"refused"`` for an unknown setting; ``"unavailable"`` when the
            setting is ``"auto"`` and neither encoder is available.
    """
    from clearwater.io.video.encode import VideoEncodeError

    if setting in ENCODERS:
        return setting
    if setting != AUTO:
        raise VideoEncodeError(
            "refused",
            f"The video encoder setting {ascii_text(setting)!r} is not one of: auto, "
            + ", ".join(ENCODERS)
            + ".",
        )
    available = {c.name for c in capabilities if c.available}
    for name in ENCODERS:
        if name in available:
            return name
    reasons = "; ".join(f"{c.name}: {c.reason}" for c in capabilities if c.reason)
    raise VideoEncodeError(
        "unavailable", f"No HEVC encoder is available, so video cannot be exported. {reasons}"
    )
