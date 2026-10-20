"""Video colour handling and chroma resampling (WP3.5, AD-10, AD-19).

``swscale`` builds the FFmpeg arguments that take a stream's Y'CbCr to the working RGB and back;
``samples`` converts FFmpeg's planar integer samples to the IF-1 float32 array and back. The
transports (WP3.9 decode, WP3.10 encode) run FFmpeg; this package starts no process and imports
only :mod:`clearwater.interfaces`, the standard library and NumPy.
"""

from __future__ import annotations

from clearwater.color.samples import planes_to_rgb, rgb_frame_bytes, rgb_to_planes
from clearwater.color.swscale import (
    DEFAULT_SITING,
    SUPPORTED_MATRICES,
    SUPPORTED_PIX_FMTS,
    SWSCALE_FLAGS,
    ColorError,
    decode_filter,
    decode_pix_fmt,
    encode_filter,
    encode_pix_fmt,
    ffmpeg_color_names,
    rgb_pix_fmt,
)

__all__ = [
    "DEFAULT_SITING",
    "SUPPORTED_MATRICES",
    "SUPPORTED_PIX_FMTS",
    "SWSCALE_FLAGS",
    "ColorError",
    "decode_filter",
    "decode_pix_fmt",
    "encode_filter",
    "encode_pix_fmt",
    "ffmpeg_color_names",
    "planes_to_rgb",
    "rgb_frame_bytes",
    "rgb_pix_fmt",
    "rgb_to_planes",
]
