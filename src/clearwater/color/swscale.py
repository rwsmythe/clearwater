"""The swscale argument pair: stream Y'CbCr to working RGB and back (WP3.5, AD-10).

FFmpeg's ``scale`` filter does the Y'CbCr conversion and the chroma resampling (AD-10). This
module only builds its arguments, so that the decode half (WP3.9) and the encode half (WP3.10)
are inverse to each other by construction:

* decode: the stream's Y'CbCr to full-range planar RGB at the source bit depth, matrix, range and
  chroma siting taken from the stream;
* encode: full-range planar RGB back to the stream's matrix, range, chroma format and siting
  (``bit_depth`` 10 for an 8-bit source is the optional D76 output).

Both directions use AD-10's flags (``bicubic+accurate_rnd+full_chroma_int+bitexact``). Primaries
and transfer are never passed to ``scale``: the pipeline keeps the source's primaries and works
on display-encoded values (spec 6.5), so the stream's primaries and transfer are not read by the
arguments. They reach the output only as tags, through :func:`ffmpeg_color_names`.

The colour description is consumed as WP3.7's probe resolved it (D54 defaults and the ``assumed``
flag included); nothing here re-reads tags. The supported set is 4:2:0 ``yuv420p``,
``yuvj420p`` and ``yuv420p10le`` with matrix BT.709 or BT.601; anything else is refused by name
(:class:`ColorError`).
"""

from __future__ import annotations

from collections.abc import Mapping

from clearwater.interfaces.image import ColorDescription
from clearwater.interfaces.video import VideoStreamInfo

SWSCALE_FLAGS = "bicubic+accurate_rnd+full_chroma_int+bitexact"
"""AD-10's swscale flags, used in both directions."""

SUPPORTED_PIX_FMTS = ("yuv420p", "yuvj420p", "yuv420p10le")
"""The source pixel formats this module handles (the declared envelope)."""

SUPPORTED_MATRICES = ("bt709", "bt601")
"""The Y'CbCr matrices this module handles."""

DEFAULT_SITING = "left"
"""The chroma siting used when the stream declares none (the H.264 / HEVC 4:2:0 default)."""

_SITINGS = frozenset({"left", "center", "topleft", "top", "bottomleft", "bottom"})
_PIX_FMT_DEPTH = {"yuv420p": 8, "yuvj420p": 8, "yuv420p10le": 10}
_RGB_PIX_FMT = {8: "gbrp", 10: "gbrp10le"}
_YUV_PIX_FMT = {8: "yuv420p", 10: "yuv420p10le"}
_MATRIX_NAMES = {"bt709": "bt709", "bt601": "smpte170m", "identity": "gbr"}
_PRIMARIES_NAMES = {"bt709": "bt709", "bt601": "smpte170m", "display-p3": "smpte432"}
_TRANSFER_NAMES = {"bt709": "bt709", "srgb": "iec61966-2-1"}
_RANGE_NAMES = {"limited": "tv", "full": "pc"}


class ColorError(ValueError):
    """An input outside what this module handles; the message names it and the supported set."""


def rgb_pix_fmt(bit_depth: int) -> str:
    """Return the planar RGB pixel format FFmpeg uses at a bit depth.

    Args:
        bit_depth: 8 or 10.

    Returns:
        ``"gbrp"`` or ``"gbrp10le"`` (planes in G, B, R order).

    Raises:
        ColorError: The bit depth is neither 8 nor 10.
    """
    try:
        return _RGB_PIX_FMT[bit_depth]
    except KeyError:
        raise ColorError(f"bit depth {bit_depth} is not supported; supported: 8, 10") from None


def _check(stream: VideoStreamInfo) -> tuple[str, str, str]:
    """Validate a stream and return its ``(matrix, range, siting)`` swscale names.

    Raises:
        ColorError: The pixel format, bit depth, matrix, range or siting is outside the
            supported set.
    """
    color = stream.color
    if stream.pix_fmt not in SUPPORTED_PIX_FMTS:
        raise ColorError(
            f"pixel format {stream.pix_fmt!r} is not supported; supported: "
            + ", ".join(SUPPORTED_PIX_FMTS)
        )
    if _PIX_FMT_DEPTH[stream.pix_fmt] != stream.bit_depth or color.bit_depth != stream.bit_depth:
        raise ColorError(
            f"bit depth disagrees: pixel format {stream.pix_fmt!r}, stream {stream.bit_depth}, "
            f"colour description {color.bit_depth}"
        )
    if color.matrix not in SUPPORTED_MATRICES:
        raise ColorError(
            f"matrix {color.matrix!r} is not supported; supported: " + ", ".join(SUPPORTED_MATRICES)
        )
    if color.range not in _RANGE_NAMES:
        raise ColorError(f"range {color.range!r} is not supported; supported: full, limited")
    if stream.pix_fmt == "yuvj420p" and color.range != "full":
        # swscale reads a yuvj format as full range whatever in_range says, so the decode would
        # silently disagree with the encode; refuse rather than guess which one is right.
        raise ColorError("pixel format 'yuvj420p' is a full-range format, but the range is limited")
    siting = DEFAULT_SITING if stream.chroma_siting == "unknown" else stream.chroma_siting
    if siting not in _SITINGS:
        raise ColorError(
            f"chroma siting {stream.chroma_siting!r} is not supported; supported: unknown, "
            + ", ".join(sorted(_SITINGS))
        )
    return _MATRIX_NAMES[color.matrix], _RANGE_NAMES[color.range], siting


def decode_pix_fmt(stream: VideoStreamInfo) -> str:
    """Return the planar RGB format the decode filter delivers (the source bit depth, AD-10).

    Args:
        stream: The probed video stream.

    Returns:
        ``"gbrp"`` for an 8-bit source, ``"gbrp10le"`` for a 10-bit source.

    Raises:
        ColorError: The stream is outside the supported set.
    """
    _check(stream)
    return rgb_pix_fmt(stream.bit_depth)


def decode_filter(stream: VideoStreamInfo) -> str:
    """Return the ``-vf`` filter that decodes the stream's Y'CbCr to full-range planar RGB.

    One ``scale`` filter takes the matrix, range and chroma siting from the stream's resolved
    colour description and delivers full-range RGB; the following ``format`` names the planar
    RGB format at the source bit depth. The same filter serves software decode and
    ``-hwaccel cuda`` (frames downloaded to system memory first).

    Args:
        stream: The probed video stream (colour as resolved by the probe, D54 included).

    Returns:
        The filter string.

    Raises:
        ColorError: The stream is outside the supported set.
    """
    matrix, range_name, siting = _check(stream)
    return (
        f"scale=in_color_matrix={matrix}:in_range={range_name}:in_chroma_loc={siting}"
        f":out_range=pc:flags={SWSCALE_FLAGS},format={rgb_pix_fmt(stream.bit_depth)}"
    )


def _output_depth(stream: VideoStreamInfo, bit_depth: int) -> int:
    """Validate the output bit depth against the source: the source's own, or 10 for 8-bit."""
    if bit_depth == stream.bit_depth or (stream.bit_depth == 8 and bit_depth == 10):
        return bit_depth
    raise ColorError(
        f"output bit depth {bit_depth} is not supported for a {stream.bit_depth}-bit source; "
        "supported: the source's own, or 10 for an 8-bit source (D76)"
    )


def encode_pix_fmt(stream: VideoStreamInfo, *, bit_depth: int) -> str:
    """Return the Y'CbCr pixel format of the encoded frames.

    The source's chroma format with a ``yuvj`` format becoming its non-``j`` form (the range is
    carried by the filter and the output tags, as WP1.5 fed NVENC).

    Args:
        stream: The probed video stream.
        bit_depth: The output bit depth: the source's own, or 10 for an 8-bit source (D76).

    Returns:
        ``"yuv420p"`` or ``"yuv420p10le"``.

    Raises:
        ColorError: The stream or the bit depth is outside the supported set.
    """
    _check(stream)
    return _YUV_PIX_FMT[_output_depth(stream, bit_depth)]


def encode_filter(stream: VideoStreamInfo, *, bit_depth: int) -> str:
    """Return the ``-vf`` filter that encodes full-range planar RGB back to the source's Y'CbCr.

    The inverse of :func:`decode_filter`: full-range RGB (at ``bit_depth``, see
    :func:`rgb_pix_fmt`) to the stream's matrix, range, chroma subsampling and siting, with
    AD-10's flags, then the Y'CbCr pixel format of :func:`encode_pix_fmt`.

    Args:
        stream: The probed video stream the output matches (D55, D114).
        bit_depth: The output bit depth: the source's own, or 10 for an 8-bit source (D76).

    Returns:
        The filter string.

    Raises:
        ColorError: The stream or the bit depth is outside the supported set.
    """
    matrix, range_name, siting = _check(stream)
    pix_fmt = _YUV_PIX_FMT[_output_depth(stream, bit_depth)]
    return (
        f"scale=in_range=pc:out_color_matrix={matrix}:out_range={range_name}"
        f":out_chroma_loc={siting}:flags={SWSCALE_FLAGS},format={pix_fmt}"
    )


def ffmpeg_color_names(color: ColorDescription) -> Mapping[str, str]:
    """Return FFmpeg's names for a colour description, for the output tags (D55).

    The inverse of the probe's tables. The resolved values are passed through unchanged, the D54
    assumed ones included (the output of an untagged source is tagged with them, DR-17); the
    ``assumed`` flag itself is read from the description by the caller. A value with no FFmpeg
    name (``"unknown"``) is left out, so the caller writes no tag for it.

    Args:
        color: A colour description.

    Returns:
        A mapping with the keys ``color_primaries``, ``color_trc``, ``colorspace`` and
        ``color_range`` (the names of FFmpeg's output options), for those fields that have a
        name.
    """
    names = {
        "color_primaries": _PRIMARIES_NAMES.get(color.primaries),
        "color_trc": _TRANSFER_NAMES.get(color.transfer),
        "colorspace": _MATRIX_NAMES.get(color.matrix),
        "color_range": _RANGE_NAMES.get(color.range),
    }
    return {key: value for key, value in names.items() if value is not None}
