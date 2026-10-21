"""Video probe, input validation, decode and encode (WP3.7, WP3.9, WP3.10).

``probe`` turns one video file into an IF-5 ``ProbeResult``; ``filter_inputs`` drops the camera
sidecars (D83); ``find_tool`` locates ``ffprobe`` and ``ffmpeg`` for the decode and encode
packages. ``FFmpegVideoSource`` is the IF-5 video source: it decodes a probed file to exact-pts
frames (WP3.9, raising ``VideoDecodeError``). ``FFmpegVideoSink`` is the IF-5 ``VideoSink``
(WP3.10); ``detect_capabilities`` and ``resolve_encoder`` answer D74 and the one ``"auto"``
encoder rule.
"""

from __future__ import annotations

from clearwater.io.video.capability import detect_capabilities, resolve_encoder
from clearwater.io.video.decode import FFmpegVideoSource, VideoDecodeError
from clearwater.io.video.encode import (
    QUALITY_LEVELS,
    FFmpegVideoSink,
    VideoEncodeError,
)
from clearwater.io.video.inputs import InputSelection, filter_inputs, is_sidecar, sidecar_fault
from clearwater.io.video.probe import VideoProbeError, find_tool, probe

__all__ = [
    "QUALITY_LEVELS",
    "FFmpegVideoSink",
    "FFmpegVideoSource",
    "InputSelection",
    "VideoDecodeError",
    "VideoEncodeError",
    "VideoProbeError",
    "detect_capabilities",
    "filter_inputs",
    "find_tool",
    "is_sidecar",
    "probe",
    "resolve_encoder",
    "sidecar_fault",
]
