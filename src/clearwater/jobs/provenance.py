"""Provenance objects for exported files (D90, D91, AD-13 as amended 2026-10-27, IF-9).

The object is AD-13's parameter-set object plus ``"source"`` and ``"settings"``. The source is
named by its file NAME only, never its path (a path carries the owner's folder names into every
shared output). Only probe facts are recorded: no tag dictionary, no GoPro settings, no location
value and nothing read from the camera's telemetry track.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from clearwater.interfaces import ParameterSet, ProbeResult


def _source_file(path: Path, stat: os.stat_result) -> dict[str, Any]:
    """Return the file part of ``"source"``: name, size and modification time (UTC)."""
    mtime = datetime.fromtimestamp(stat.st_mtime_ns / 1e9, tz=UTC)
    return {"name": path.name, "size": stat.st_size, "mtime": mtime.isoformat()}


def video_source_summary(probe: ProbeResult, stat: os.stat_result) -> dict[str, Any]:
    """Return the ``"source"`` object of a video: file facts plus a probe summary.

    Args:
        probe: The source's probe result.
        stat: The source file's ``os.stat`` result.

    Returns:
        JSON-native values: ``name``, ``size``, ``mtime``, ``container``, ``codec``, ``width``,
        ``height``, ``bit_depth``, ``frame_rate`` and ``duration_s`` (exact fractions as
        strings), ``nb_frames`` and ``color`` (primaries, transfer, matrix, range).
    """
    video = probe.video
    color = video.color
    return {
        **_source_file(probe.path, stat),
        "container": probe.container,
        "codec": video.codec,
        "width": video.width,
        "height": video.height,
        "bit_depth": video.bit_depth,
        "frame_rate": str(video.frame_rate),
        "duration_s": str(probe.duration_s),
        "nb_frames": video.nb_frames,
        "color": {
            "primaries": color.primaries,
            "transfer": color.transfer,
            "matrix": color.matrix,
            "range": color.range,
        },
    }


def photo_source_summary(
    path: Path, stat: os.stat_result, width: int, height: int
) -> dict[str, Any]:
    """Return the ``"source"`` object of a photo: file facts plus the decoded size.

    Args:
        path: The source photo.
        stat: The source file's ``os.stat`` result.
        width: The decoded width in pixels (orientation applied).
        height: The decoded height in pixels (orientation applied).

    Returns:
        JSON-native values: ``name``, ``size``, ``mtime``, ``width``, ``height``.
    """
    return {**_source_file(path, stat), "width": width, "height": height}


def provenance_object(
    *,
    method: str,
    parameters: Mapping[str, Any],
    app_version: str,
    source: Mapping[str, Any],
    settings: Mapping[str, Any],
    created: datetime | None = None,
) -> dict[str, Any]:
    """Build the provenance object (AD-13 plus ``"source"`` and ``"settings"``).

    Args:
        method: The method id rendered with.
        parameters: The effective parameter values rendered with (defaults overlaid).
        app_version: The Clearwater version.
        source: The ``"source"`` object (:func:`video_source_summary` or
            :func:`photo_source_summary`).
        settings: The ``"settings"`` object (the resolved encoder, never ``"auto"``, quality and
            bit depth for a video; the PNG bit depth for a photo; the device for both).
        created: The export moment (timezone-aware); now, in UTC, when None.

    Returns:
        The JSON-native object.
    """
    return ParameterSet(
        method=method,
        parameters=dict(parameters),
        created=created if created is not None else datetime.now(UTC),
        app_version=app_version,
        source=dict(source),
        settings=dict(settings),
    ).to_dict()
