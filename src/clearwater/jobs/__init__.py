"""Jobs: output naming and safe writing (architecture section 2, plan 8.1).

WP3.13 provides :mod:`clearwater.jobs.naming`, :mod:`clearwater.jobs.safe_write` and
:mod:`clearwater.jobs.disk_space`; WP3.14 adds export and batch beside them. This package
imports nothing from ``clearwater.gui`` or ``clearwater.methods`` and no GUI or GPU library.
"""

from __future__ import annotations

from .disk_space import (
    MARGIN,
    PHOTO_OVERHEAD_BYTES,
    QUALITY_RATIO,
    SpaceCheck,
    check_free_space,
    estimate_photo_bytes,
    estimate_video_bytes,
)
from .naming import (
    TEMP_MARKER,
    MediaKind,
    OutputPlan,
    Reservations,
    final_output_path,
    is_temporary_name,
    plan_output,
    temporary_path,
    validate_suffix,
)
from .safe_write import (
    LeftoverReport,
    MissingFolderError,
    SafeWrite,
    SafeWriteError,
    SafeWriteState,
    is_disk_full,
    remove_leftovers,
)

__all__ = [
    "MARGIN",
    "PHOTO_OVERHEAD_BYTES",
    "QUALITY_RATIO",
    "TEMP_MARKER",
    "LeftoverReport",
    "MediaKind",
    "MissingFolderError",
    "OutputPlan",
    "Reservations",
    "SafeWrite",
    "SafeWriteError",
    "SafeWriteState",
    "SpaceCheck",
    "check_free_space",
    "estimate_photo_bytes",
    "estimate_video_bytes",
    "final_output_path",
    "is_disk_full",
    "is_temporary_name",
    "plan_output",
    "remove_leftovers",
    "temporary_path",
    "validate_suffix",
]
