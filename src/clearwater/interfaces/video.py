"""IF-5: video source and sink.

A :class:`VideoSource` probes a file and yields exact-pts frames; a :class:`VideoSink`
writes corrected frames to a container that keeps the source's timing (D94, D105, AD-22).
The probe result types that architecture section 3 names but does not define were fixed by the
WP2.2 round-1 ruling.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any, Literal, Protocol, runtime_checkable

from .image import ColorDescription, Frame


@dataclass(frozen=True)
class VideoStreamInfo:
    """The video stream of a probed file (IF-5).

    Attributes:
        codec: The codec name, for example ``"hevc"``.
        width: Coded width in pixels.
        height: Coded height in pixels.
        bit_depth: Source bit depth (8 or 10).
        pix_fmt: The pixel format name, for example ``"yuv420p10le"``.
        chroma_siting: The chroma sample location the stream declares (AD-10), for example
            ``"left"``, or ``"unknown"``.
        color: The stream's colour tags (D54).
        frame_rate: The average frame rate in frames per second.
        time_base: The stream's time base.
        nb_frames: The container's frame count, or None when it does not say.
        rotation: The display-matrix rotation in degrees (D105), FFmpeg convention (counter-
            clockwise positive), normalised to 0, 90, 180 or 270; 0 when there is no matrix.
            ``tools/inventory.py`` reports the opposite sign (clockwise) in its report column.
        vfr: True when the frame times are not constant (D95).
    """

    codec: str
    width: int
    height: int
    bit_depth: int
    pix_fmt: str
    chroma_siting: str
    color: ColorDescription
    frame_rate: Fraction
    time_base: Fraction
    nb_frames: int | None
    rotation: int
    vfr: bool


@dataclass(frozen=True)
class AudioStreamInfo:
    """One audio stream of a probed file (IF-5).

    Attributes:
        index: The stream index in the container.
        codec: The codec name.
        sample_rate: Samples per second.
        channels: The channel count.
        start_s: The first audio presentation time in seconds (audio sync, D105).
    """

    index: int
    codec: str
    sample_rate: int
    channels: int
    start_s: Fraction


@dataclass(frozen=True)
class DataStreamInfo:
    """One data stream (``gpmd``, ``tmcd``) of a probed file (IF-5).

    Attributes:
        index: The stream index in the container.
        codec_tag: The stream's codec tag, for example ``"gpmd"`` or ``"tmcd"``.
    """

    index: int
    codec_tag: str


@dataclass(frozen=True)
class EditEntry:
    """One entry of the video track's edit list (IF-5; D94, AD-22).

    Attributes:
        segment_duration_s: The entry's duration in seconds.
        media_time_s: The media time the entry starts at, in seconds; None for an empty edit.
        media_rate: The playback rate of the entry (1 for normal speed).
    """

    segment_duration_s: Fraction
    media_time_s: Fraction | None
    media_rate: Fraction


type FaultKind = Literal[
    "truncated", "unreadable_tail", "missing_tags", "hlg", "pq", "gp_log", "sidecar"
]
"""The probe fault kinds listed at IF-5."""


@dataclass(frozen=True)
class Fault:
    """One problem the probe found in a file (IF-5).

    Attributes:
        kind: ``"truncated"`` or ``"unreadable_tail"`` (D86), ``"missing_tags"`` (assumed per
            D54), ``"hlg"`` or ``"pq"`` (refusal), ``"gp_log"`` (warn, AD-16), ``"sidecar"``
            (excluded, D83).
        severity: ``"refuse"`` (the file is not processed), ``"warn"`` (processed, the user is
            told) or ``"exclude"`` (not an input).
        message: A user-readable message.
    """

    kind: FaultKind
    severity: Literal["refuse", "warn", "exclude"]
    message: str


@dataclass(frozen=True)
class GoProInfo:
    """GoPro settings read from the GPMF track (IF-5; AD-16).

    Attributes:
        firmware: The camera firmware string, or None when absent.
        protune: Whether Protune is on (``PRTN``), or None when absent.
        color_profile: The colour profile (``PTCL``), for example ``"NATURAL"``, or None.
    """

    firmware: str | None
    protune: bool | None
    color_profile: str | None


@dataclass(frozen=True)
class ProbeResult:
    """What probing a video file found (IF-5).

    Attributes:
        path: The probed file.
        container: The container format name.
        duration_s: The CONTAINER duration in seconds, exact (``mvhd`` duration over its
            timescale, or the longest stream in integer ticks times its time base); the video
            track's own end comes from pts and frame durations, not from this field.
        start_offset_s: The container's start offset in seconds (D105).
        video: The video stream.
        audio: The audio streams.
        data: The data streams (``gpmd``, ``tmcd``).
        edit_list: The video track's edit list (D94).
        faults: Truncation, unreadable tail, missing tags (assumed per D54), HLG or PQ
            (refusal), GP-Log (warn, AD-16) and sidecar (excluded, D83).
        gopro: Firmware, Protune and colour profile (PTCL) from the GPMF settings, or None.
    """

    path: Path
    container: str
    duration_s: Fraction
    start_offset_s: Fraction
    video: VideoStreamInfo
    audio: tuple[AudioStreamInfo, ...]
    data: tuple[DataStreamInfo, ...]
    edit_list: tuple[EditEntry, ...]
    faults: tuple[Fault, ...]
    gopro: GoProInfo | None


@runtime_checkable
class VideoSource(Protocol):
    """Probes video files and yields their frames with exact pts (IF-5)."""

    def probe(self, path: Path) -> ProbeResult:
        """Probe a file.

        Args:
            path: The video file.

        Returns:
            What the probe found.
        """
        ...

    def frames(
        self,
        probe: ProbeResult,
        *,
        hw_decode: bool,
        start_s: Fraction | None = None,
        end_s: Fraction | None = None,
    ) -> Iterator[Frame]:
        """Yield the frames of a probed file with exact pts; stops at the readable end (D86).

        Args:
            probe: The probe result of the file.
            hw_decode: Whether to decode on the GPU.
            start_s: First time to yield, or None for the start.
            end_s: Time to stop before, or None for the end.

        Returns:
            An iterator over the frames in decode order.
        """
        ...


@dataclass(frozen=True)
class EncoderCapability:
    """Whether one encoder option is available (IF-5; D74).

    Attributes:
        name: The encoder name; the resolved name, never ``"auto"``, goes into provenance.
        available: Whether the option can be used.
        reason: Why it is unavailable, or None when available.
        bit_depths: The bit depths the encoder supports.
        hw: Whether the encoder is a hardware encoder.
    """

    name: str
    available: bool
    reason: str | None
    bit_depths: tuple[int, ...]
    hw: bool


@dataclass(frozen=True)
class SinkReport:
    """What a sink reports on close (IF-5).

    Attributes:
        frames_written: The number of frames written.
        warnings: Warnings raised while writing.
        not_carried: The best-effort items of the source that were not carried (D105).
    """

    frames_written: int
    warnings: tuple[str, ...]
    not_carried: tuple[str, ...]


@runtime_checkable
class VideoSink(Protocol):
    """Writes corrected frames to a video file (IF-5)."""

    def capabilities(self) -> tuple[EncoderCapability, ...]:
        """Return the encoder options and whether each is available (D74)."""
        ...

    def open(
        self,
        probe: ProbeResult,
        out_path: Path,
        *,
        encoder: str,
        quality: str,
        bit_depth: int,
        provenance: Mapping[str, Any] | None,
    ) -> None:
        """Open the output file (quality levels per AD-12).

        Args:
            probe: The probe result of the source.
            out_path: The output file.
            encoder: The encoder name.
            quality: The named quality level.
            bit_depth: The output bit depth.
            provenance: The provenance to embed, or None.
        """
        ...

    def write(self, frame: Frame) -> None:
        """Write one frame, in pts order.

        The sink preserves pts, start offset, edit list (AD-22), audio, gpmd, tmcd and
        rotation.

        Args:
            frame: The corrected frame.
        """
        ...

    def close(self) -> SinkReport:
        """Finish the file.

        Returns:
            Frames written, warnings, and the best-effort items not carried.
        """
        ...

    def abort(self) -> None:
        """Stop and remove the partial output (D44, D85)."""
        ...
