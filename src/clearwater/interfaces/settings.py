"""IF-10: the application settings and their JSON form.

``Settings`` carries the G12 fields and the AD-9 ``force_cpu`` override. It serialises to a JSON
string and back; where the document lives (the platform app-data folder) and the migration of
other format versions belong to WP3.15, so no file I/O is here. ``clearwater.local.toml`` stays
the developer-only override for folders.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .parameters import (
    FORMAT_VERSION,
    FormatError,
    ParameterSet,
    check_format_version,
    loads_object,
)

DEFAULT_OUTPUT_SUFFIX = "_corrected"
"""The default output suffix (D36)."""

DEFAULT_CACHE_LIMIT_BYTES = 20 * 10**9
"""The default proxy-cache limit: 20 GB (D71), read as SI gigabytes."""

DEFAULT_PNG_BIT_DEPTH = 16
"""The default PNG bit depth (D22, D53): keeps the corrected precision; 8 is selectable."""

DEFAULT_VIDEO_ENCODER = "auto"
"""The default video encoder: NVENC HEVC when available (D74), else libx265."""

DEFAULT_QUALITY_LEVEL = "standard"
"""The default named quality level (D75, AD-12), stored lower-case."""

_FIELDS = (
    "output_folder",
    "output_suffix",
    "png_bit_depth",
    "video_encoder",
    "quality_level",
    "ten_bit_for_eight_bit",
    "provenance",
    "cache_limit_bytes",
    "force_cpu",
    "last_parameters",
)


def _field_error(name: str, expected: str, value: object) -> FormatError:
    """Build the error for a settings field of the wrong type."""
    return FormatError(f"{name} must be {expected}, got {value!r}")


@dataclass(frozen=True, kw_only=True)
class Settings:
    """The application settings (IF-10; G12, AD-9).

    Attributes:
        output_folder: Where outputs go; None means the source folder (D34).
        output_suffix: The output name suffix (D36).
        png_bit_depth: The PNG bit depth, 8 or 16 (D22).
        video_encoder: The video encoder name (D26): ``"auto"`` (the default: NVENC HEVC when
            the D74 capability report says available, else libx265) or an
            :class:`~clearwater.interfaces.video.EncoderCapability` name. Provenance records the
            resolved encoder, never ``"auto"``.
        quality_level: The named video quality level (D75, AD-12): ``"high"``, ``"standard"``
            or ``"draft"``, lower-case.
        ten_bit_for_eight_bit: Write 10-bit video from 8-bit sources (D76); off by default.
        provenance: Embed provenance in outputs (D91); on by default.
        cache_limit_bytes: The proxy-cache size limit in bytes (D71).
        force_cpu: The Advanced "Force CPU processing" override (AD-9).
        last_parameters: The parameters in use when the application last closed (D89), or None.
    """

    output_folder: Path | None = None
    output_suffix: str = DEFAULT_OUTPUT_SUFFIX
    png_bit_depth: int = DEFAULT_PNG_BIT_DEPTH
    video_encoder: str = DEFAULT_VIDEO_ENCODER
    quality_level: str = DEFAULT_QUALITY_LEVEL
    ten_bit_for_eight_bit: bool = False
    provenance: bool = True
    cache_limit_bytes: int = DEFAULT_CACHE_LIMIT_BYTES
    force_cpu: bool = False
    last_parameters: ParameterSet | None = None

    def to_json(self) -> str:
        """Return the settings as JSON text, with ``format_version`` 1.

        Returns:
            The JSON text. ``last_parameters`` is nested in its AD-13 form.
        """
        data: dict[str, Any] = {
            "format_version": FORMAT_VERSION,
            "output_folder": None if self.output_folder is None else str(self.output_folder),
            "output_suffix": self.output_suffix,
            "png_bit_depth": self.png_bit_depth,
            "video_encoder": self.video_encoder,
            "quality_level": self.quality_level,
            "ten_bit_for_eight_bit": self.ten_bit_for_eight_bit,
            "provenance": self.provenance,
            "cache_limit_bytes": self.cache_limit_bytes,
            "force_cpu": self.force_cpu,
            "last_parameters": (
                None if self.last_parameters is None else self.last_parameters.to_dict()
            ),
        }
        return json.dumps(data, indent=2, allow_nan=False)

    @classmethod
    def from_json(cls, text: str) -> Settings:
        """Parse settings JSON text.

        Args:
            text: The JSON text.

        Returns:
            The settings; ``from_json(s.to_json()) == s``.

        Raises:
            UnsupportedFormatVersionError: ``format_version`` is not 1.
            FormatError: A field is missing, unknown or of the wrong type.
        """
        data = loads_object(text)
        check_format_version(data)
        unknown = sorted(set(data) - set(_FIELDS) - {"format_version"})
        if unknown:
            raise FormatError(f"unknown keys: {', '.join(unknown)}")
        missing = [name for name in _FIELDS if name not in data]
        if missing:
            raise FormatError(f"missing keys: {', '.join(missing)}")
        folder = data["output_folder"]
        if folder is not None and not isinstance(folder, str):
            raise _field_error("output_folder", "a string or null", folder)
        for name in ("output_suffix", "video_encoder", "quality_level"):
            if not isinstance(data[name], str):
                raise _field_error(name, "a string", data[name])
        for name in ("png_bit_depth", "cache_limit_bytes"):
            value = data[name]
            if isinstance(value, bool) or not isinstance(value, int):
                raise _field_error(name, "an integer", value)
        for name in ("ten_bit_for_eight_bit", "provenance", "force_cpu"):
            if not isinstance(data[name], bool):
                raise _field_error(name, "a boolean", data[name])
        last = data["last_parameters"]
        if last is not None and not isinstance(last, dict):
            raise _field_error("last_parameters", "an object or null", last)
        return cls(
            output_folder=None if folder is None else Path(folder),
            output_suffix=data["output_suffix"],
            png_bit_depth=data["png_bit_depth"],
            video_encoder=data["video_encoder"],
            quality_level=data["quality_level"],
            ten_bit_for_eight_bit=data["ten_bit_for_eight_bit"],
            provenance=data["provenance"],
            cache_limit_bytes=data["cache_limit_bytes"],
            force_cpu=data["force_cpu"],
            last_parameters=None if last is None else ParameterSet.from_dict(last),
        )
