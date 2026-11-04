"""Encoder capability detection (D74) and the one ``"auto"`` encoder rule (WP3.10).

:func:`detect_capabilities` reports, for the two HEVC encoders Clearwater offers on this platform
(:func:`encoder_roster`, AD-35: the hardware encoder, ``hevc_nvenc`` on Windows and Linux or
``hevc_videotoolbox`` on macOS, then the software ``libx265``), whether each is usable and at
which bit depths, with a reason the settings dialog can show when it is not (D74: "unavailable
options are shown disabled with a reason"). It asks FFmpeg for its encoder list, then runs one
one-frame test encode per encoder and bit depth to FFmpeg's null muxer (the listing alone does
not tell whether a hardware encoder can run here); the four tests run at once and the result is
cached for the process. A VideoToolbox test passes ``-allow_sw 0``, so Apple's software
fallback never reads as the hardware encoder.

:func:`resolve_encoder` is the single rule for the ``"auto"`` setting (G12 v0.6.1: the
platform's hardware HEVC encoder when available, else libx265); the settings dialog and the
export call it, and the sink only ever receives the resolved name, which is what provenance
records.

:func:`tool_env` retains the environment-only API and delegates to the shared launch policy
in :mod:`.pipes`, which every product FFmpeg and ffprobe launch uses.
"""

from __future__ import annotations

import subprocess
import sys
import threading
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from clearwater.interfaces.video import EncoderCapability
from clearwater.io.video.inputs import ascii_text
from clearwater.io.video.pipes import tool_spawn_kwargs
from clearwater.io.video.probe import VideoProbeError, find_tool

AUTO = "auto"
"""The encoder setting that :func:`resolve_encoder` resolves (IF-10 ``video_encoder``)."""

HARDWARE_ENCODER = "hevc_nvenc"
"""FFmpeg's NVIDIA HEVC encoder (the hardware encoder on Windows and Linux)."""

VIDEOTOOLBOX_ENCODER = "hevc_videotoolbox"
"""FFmpeg's Apple VideoToolbox HEVC encoder (the hardware encoder on macOS, AD-35)."""

SOFTWARE_ENCODER = "libx265"
"""FFmpeg's software HEVC encoder (on every platform)."""

KNOWN_ENCODERS = (HARDWARE_ENCODER, VIDEOTOOLBOX_ENCODER, SOFTWARE_ENCODER)
"""Every encoder name Clearwater knows; a name outside this set is refused as unknown."""

HARDWARE_ENCODERS = frozenset({HARDWARE_ENCODER, VIDEOTOOLBOX_ENCODER})
"""The names whose capability carries the hardware flag (``EncoderCapability.hw``)."""


def encoder_roster(platform: str | None = None) -> tuple[str, ...]:
    """Return the encoders Clearwater offers on a platform, in the order ``"auto"`` prefers them.

    macOS offers ``hevc_videotoolbox`` then ``libx265`` (AD-35); every other platform offers
    ``hevc_nvenc`` then ``libx265`` (Windows as 1.0.0; on Linux an absent NVENC costs one
    failed test encode, CHARC's WP6.4 round-0 ruling). Availability is never decided here:
    the test encodes of :func:`detect_capabilities` decide it.

    Args:
        platform: A ``sys.platform`` value; the running one when None.

    Returns:
        The roster, hardware encoder first.
    """
    kind = sys.platform if platform is None else platform
    if kind == "darwin":
        roster = (VIDEOTOOLBOX_ENCODER, SOFTWARE_ENCODER)
    else:
        roster = (HARDWARE_ENCODER, SOFTWARE_ENCODER)
    return roster


ENCODERS = encoder_roster()
"""The encoders Clearwater offers on the running platform, in the order ``"auto"`` prefers
them (:func:`encoder_roster`)."""

BIT_DEPTHS = (8, 10)
"""The output bit depths tested per encoder (D25, D76)."""

TEST_TIMEOUT_S = 30
"""Seconds one test encode or the encoder listing may take before it counts as failed."""

_TEST_PIX_FMT = {
    (HARDWARE_ENCODER, 8): "yuv420p",
    (HARDWARE_ENCODER, 10): "p010le",
    (VIDEOTOOLBOX_ENCODER, 8): "yuv420p",
    (VIDEOTOOLBOX_ENCODER, 10): "p010le",
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

_VT_NO_SESSION_MARKERS = (
    "cannot create compression session",
    "try -allow_sw 1",
    "hardware encoder may be busy",
)
"""Lower-case stderr fragments of a VideoToolbox test that failed because no hardware
compression session could be made. From FFmpeg's ``videotoolboxenc.c`` error texts as the
WP6.2 audit recorded them (DOC [FF], unverified offline); WP6.5 checks them against a Mac
capture (``tests/ffmpeg_text/README.md``)."""

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
    return tool_spawn_kwargs()["env"]


def _run(command: Sequence[str]) -> tuple[int, str]:
    """Run a short FFmpeg command and return its exit status and its output (stdout + stderr)."""
    try:
        done = subprocess.run(
            list(command),
            stdin=subprocess.DEVNULL,
            capture_output=True,
            timeout=TEST_TIMEOUT_S,
            check=False,
            **tool_spawn_kwargs(),
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
        encoder: ``"hevc_nvenc"``, ``"hevc_videotoolbox"`` or ``"libx265"``.
        bit_depth: 8 or 10.

    Returns:
        The command; it writes no file. A VideoToolbox test carries ``-allow_sw 0`` (AD-35).
    """
    extra: list[str] = []
    if encoder == SOFTWARE_ENCODER:
        extra = ["-x265-params", "log-level=error"]
    elif encoder == VIDEOTOOLBOX_ENCODER:
        extra = ["-allow_sw", "0"]
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
    if encoder == VIDEOTOOLBOX_ENCODER and any(m in joined for m in _VT_NO_SESSION_MARKERS):
        return (
            "The VideoToolbox hardware encoder could not start on this Mac (it may be busy or "
            "may not support this format), so the hevc_videotoolbox encoder cannot be used."
        )
    detail = failures[0] if failures else "no detail"
    return f"The {encoder} test encode failed: {detail}"


def _detect(ffmpeg: Path, roster: Sequence[str] | None = None) -> tuple[EncoderCapability, ...]:
    """Detect the capabilities with one listing and the test encodes (no cache).

    ``roster`` is a platform's :func:`encoder_roster` (the running one when None); tests pass
    another platform's.
    """
    names = ENCODERS if roster is None else tuple(roster)
    listed, listing_error = _listed(ffmpeg)
    if listing_error is not None:
        reason = f"FFmpeg could not list its encoders: {listing_error}"
        return tuple(
            EncoderCapability(name, False, reason, (), name in HARDWARE_ENCODERS) for name in names
        )
    tests = [(name, depth) for name in names if name in listed for depth in BIT_DEPTHS]
    with ThreadPoolExecutor(max_workers=max(1, len(tests))) as pool:
        results = list(pool.map(lambda t: _run(trial_encode_command(ffmpeg, *t)), tests))
    outcome = dict(zip(tests, results, strict=True))
    capabilities = []
    for name in names:
        hw = name in HARDWARE_ENCODERS
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
        One entry per encoder in :data:`ENCODERS` (this platform's roster), with ``reason`` set
        when it is unavailable. When ``ffmpeg`` itself is missing, every entry is unavailable
        with that reason.
    """
    try:
        ffmpeg = find_tool("ffmpeg")
    except VideoProbeError as error:
        return tuple(
            EncoderCapability(name, False, str(error), (), name in HARDWARE_ENCODERS)
            for name in ENCODERS
        )
    key = str(ffmpeg)
    with _lock:
        if refresh or key not in _cache:
            _cache[key] = _detect(ffmpeg)
        return _cache[key]


def resolve_encoder(
    setting: str,
    capabilities: Sequence[EncoderCapability],
    *,
    roster: Sequence[str] | None = None,
) -> str:
    """Resolve the encoder setting to the encoder actually used (the one ``"auto"`` rule).

    ``"auto"`` becomes the roster's first available encoder: the platform's hardware encoder
    when it is available, else ``libx265`` (G12 v0.6.1). An explicit encoder name Clearwater
    knows is returned unchanged, even one this platform does not offer (D26: a saved choice is
    kept, never silently replaced); the sink refuses it at ``open`` as unavailable, with the
    reason.

    Args:
        setting: ``"auto"`` or an encoder name (IF-10 ``video_encoder``).
        capabilities: The result of :func:`detect_capabilities` (or the sink's
            ``capabilities()``).
        roster: The preference order (:func:`encoder_roster`); this platform's when None.

    Returns:
        The encoder name, never ``"auto"``.

    Raises:
        VideoEncodeError: ``"refused"`` for an unknown setting; ``"unavailable"`` when the
            setting is ``"auto"`` and no encoder of the roster is available.
    """
    from clearwater.io.video.encode import VideoEncodeError

    names = ENCODERS if roster is None else tuple(roster)
    if setting in KNOWN_ENCODERS:
        return setting
    if setting != AUTO:
        raise VideoEncodeError(
            "refused",
            f"The video encoder setting {ascii_text(setting)!r} is not one of: auto, "
            + ", ".join(names)
            + ".",
        )
    available = {c.name for c in capabilities if c.available}
    for name in names:
        if name in available:
            return name
    reasons = "; ".join(f"{c.name}: {c.reason}" for c in capabilities if c.reason)
    raise VideoEncodeError(
        "unavailable", f"No HEVC encoder is available, so video cannot be exported. {reasons}"
    )


def not_offered_reason(name: str) -> str:
    """Return why a known encoder this platform does not offer cannot be used (D26).

    Args:
        name: An encoder name in :data:`KNOWN_ENCODERS` but not in :data:`ENCODERS`.

    Returns:
        The reason, naming the encoders this platform offers.
    """
    return f"it is not offered on this platform (this platform offers: {', '.join(ENCODERS)})"
