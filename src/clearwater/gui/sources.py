"""Open a photo or a video (G1, G10): routing by extension, reading, probing, frame decode.

:func:`route` is cheap and runs on the main thread (it looks at the extension only). Everything
else reads files and runs on the loader or frame worker; nothing here touches a Qt object.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Literal

import numpy as np

from clearwater.interfaces import Frame, Image, ProbeResult
from clearwater.io.video import VideoProbeError, is_sidecar, sidecar_fault

from . import messages
from .contract import Engines, Message, OpenedSource

PHOTO_SUFFIXES = frozenset({".heic", ".heif", ".jpg", ".jpeg", ".png", ".tif", ".tiff", ".dng"})
"""Photo extensions (spec 5.1). ``.dng`` is routed to the reader so its refusal is shown (D116)."""

VIDEO_SUFFIXES = frozenset({".mp4"})
"""Video extensions (spec 5.2: the MP4 container)."""

type SourceKind = Literal["photo", "video"]
"""What a path is opened as."""


def file_filter() -> str:
    """Return the open-dialog filter: photos and videos, each kind, and all files (G1).

    Returns:
        A ``QFileDialog`` name filter string.
    """
    photos = " ".join(f"*{s}" for s in sorted(PHOTO_SUFFIXES))
    videos = " ".join(f"*{s}" for s in sorted(VIDEO_SUFFIXES))
    return (
        f"Photos and videos ({photos} {videos});;Photos ({photos});;Videos ({videos});;"
        "All files (*)"
    )


def route(path: Path) -> SourceKind | Message:
    """Decide how a path is opened, by its extension (case-insensitive); never opens the file.

    Args:
        path: The chosen file.

    Returns:
        ``"photo"`` or ``"video"``, or the refusal for a sidecar (D83) or an unknown extension.
    """
    if is_sidecar(path):
        return messages.refusal(path, sidecar_fault(path).message)
    suffix = path.suffix.lower()
    if suffix in PHOTO_SUFFIXES:
        return "photo"
    if suffix in VIDEO_SUFFIXES:
        return "video"
    return messages.unsupported_extension(path)


@dataclass(frozen=True)
class OpenOutcome:
    """The result of opening a file.

    Attributes:
        source: The opened source, or None when the file was refused.
        messages: The refusals (when ``source`` is None) or the warnings, in order.
    """

    source: OpenedSource | None
    messages: tuple[Message, ...]


def _host(image: Image) -> Image:
    """Return ``image`` with host float32 pixels (the shell's images live on the host)."""
    pixels = np.asarray(image.pixels, dtype=np.float32)
    if pixels is image.pixels and image.device == "cpu":
        return image
    if isinstance(image, Frame):
        return Frame(
            pixels=pixels,
            device="cpu",
            color=image.color,
            orientation_applied=image.orientation_applied,
            pts=image.pts,
            pts_ticks=image.pts_ticks,
            time_base=image.time_base,
            index=image.index,
        )
    return Image(
        pixels=pixels,
        device="cpu",
        color=image.color,
        orientation_applied=image.orientation_applied,
    )


def open_photo(path: Path, engines: Engines) -> OpenOutcome:
    """Read a photo through ``engines.photo_source`` (worker thread).

    Args:
        path: The photo.
        engines: The engines.

    Returns:
        The source and its warnings, or the refusal.
    """
    try:
        image, metadata = engines.photo_source.read(path)
    except Exception as exc:  # every read failure is a refusal (spec 5.4, D116)
        return OpenOutcome(None, (messages.photo_read_failure(path, exc),))
    found: list[Message] = []
    if image.color.assumed:
        found.append(messages.assumed_colour(path, "photo"))
    source = OpenedSource(
        path=path,
        kind="photo",
        image=_host(image),
        metadata=metadata,
        probe=None,
        warnings=tuple(m.text for m in found),
    )
    return OpenOutcome(source, tuple(found))


def first_frame(engines: Engines, probe: ProbeResult, start_s: Fraction | None) -> Frame | None:
    """Decode the first frame at or after ``start_s`` (worker thread; ``hw_decode`` off, S7).

    Args:
        engines: The engines.
        probe: The video's probe result.
        start_s: The time to start at, or None for the start.

    Returns:
        The frame on the host, or None when the source yields none.
    """
    frames = engines.video_source.frames(probe, hw_decode=False, start_s=start_s)
    try:
        frame = next(iter(frames), None)
    finally:
        close = getattr(frames, "close", None)
        if callable(close):
            close()
    if frame is None:
        return None
    host = _host(frame)
    assert isinstance(host, Frame)
    return host


def frame_at(engines: Engines, probe: ProbeResult, pts_ticks: int) -> Frame | None:
    """Decode the first frame at or after a position in pts ticks (worker thread; S5).

    Args:
        engines: The engines.
        probe: The video's probe result.
        pts_ticks: The position in stream ticks.

    Returns:
        The frame, or None when there is none at or after the position.
    """
    return first_frame(engines, probe, pts_ticks * probe.video.time_base)


def open_video(path: Path, engines: Engines) -> OpenOutcome:
    """Probe a video and decode its first frame (worker thread; spec 5.2-5.4, D54, D108).

    Args:
        path: The video.
        engines: The engines.

    Returns:
        The source and its warnings, or the refusals.
    """
    try:
        probe = engines.video_probe(path)
    except VideoProbeError as exc:  # every kind carries a user-readable message (G10)
        text = str(exc) or f"{messages.file_name(path)} could not be read."
        return OpenOutcome(None, (messages.refusal(path, text),))
    except Exception as exc:  # an injected probe failing otherwise is shown as unreadable
        text = f"{messages.file_name(path)} could not be read: {exc}"
        return OpenOutcome(None, (messages.refusal(path, text),))
    refusals, warnings = messages.fault_messages(path, probe.faults)
    if refusals:
        return OpenOutcome(None, tuple(refusals))
    try:
        frame = first_frame(engines, probe, None)
    except Exception as exc:  # a decode failure of the first frame refuses the file
        return OpenOutcome(
            None, (messages.refusal(path, f"{messages.file_name(path)} could not be read: {exc}"),)
        )
    if frame is None:
        return OpenOutcome(None, (messages.no_frame(path),))
    tags_warned = any(f.kind == "missing_tags" for f in probe.faults)
    if frame.color.assumed and not tags_warned:
        warnings.append(messages.assumed_colour(path, "video"))
    source = OpenedSource(
        path=path,
        kind="video",
        image=frame,
        metadata=None,
        probe=probe,
        warnings=tuple(m.text for m in warnings),
    )
    return OpenOutcome(source, tuple(warnings))


def open_source(path: Path, kind: SourceKind, engines: Engines) -> OpenOutcome:
    """Open a routed path (worker thread).

    Args:
        path: The file.
        kind: What :func:`route` returned.
        engines: The engines.

    Returns:
        The outcome.
    """
    if kind == "photo":
        return open_photo(path, engines)
    return open_video(path, engines)
