"""Video probe and input validation (WP3.7).

``probe`` turns one video file into an IF-5 ``ProbeResult``; ``filter_inputs`` drops the camera
sidecars (D83); ``find_tool`` locates ``ffprobe`` and ``ffmpeg`` for the decode and encode
packages. Decoding and encoding are other work packages (WP3.9, WP3.10).
``FFmpegVideoSource`` is the IF-5 video source: it decodes a probed file to exact-pts frames
(WP3.9, raising ``VideoDecodeError``).
"""

from __future__ import annotations

from clearwater.io.video.decode import FFmpegVideoSource, VideoDecodeError
from clearwater.io.video.inputs import InputSelection, filter_inputs, is_sidecar, sidecar_fault
from clearwater.io.video.probe import VideoProbeError, find_tool, probe

__all__ = [
    "FFmpegVideoSource",
    "InputSelection",
    "VideoDecodeError",
    "VideoProbeError",
    "filter_inputs",
    "find_tool",
    "is_sidecar",
    "probe",
    "sidecar_fault",
]
