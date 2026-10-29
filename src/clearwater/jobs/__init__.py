"""Jobs: naming, safe writing, export and batch (architecture section 2, plan 8.1).

WP3.13 provides :mod:`clearwater.jobs.naming`, :mod:`clearwater.jobs.safe_write` and
:mod:`clearwater.jobs.disk_space`; WP3.14 adds export and batch beside them:
:mod:`clearwater.jobs.export` (the engine behind the WP3.19 seam in
:mod:`clearwater.jobs.export_seam`), :mod:`clearwater.jobs.provenance` and
:mod:`clearwater.jobs.batch`. This package imports nothing from ``clearwater.gui`` or
``clearwater.methods`` and no GUI or GPU library.
"""

from __future__ import annotations

from .batch import BatchItem, BatchReport, run_batch
from .disk_space import (
    MARGIN,
    PHOTO_OVERHEAD_BYTES,
    QUALITY_RATIO,
    SpaceCheck,
    check_free_space,
    estimate_photo_bytes,
    estimate_video_bytes,
)
from .export import (
    RESERVED_DEVICE_NAMES,
    BackendSelector,
    ExportEngine,
    effective_parameters,
    expected_frames,
    is_reserved_device_name,
)
from .naming import (
    TEMP_MARKER,
    MediaKind,
    OutputNameError,
    OutputPlan,
    Reservations,
    final_output_path,
    is_temporary_name,
    new_token,
    plan_output,
    scan_temporaries,
    temporaries_of,
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
    "RESERVED_DEVICE_NAMES",
    "TEMP_MARKER",
    "BackendSelector",
    "BatchItem",
    "BatchReport",
    "ExportEngine",
    "LeftoverReport",
    "MediaKind",
    "MissingFolderError",
    "OutputNameError",
    "OutputPlan",
    "Reservations",
    "SafeWrite",
    "SafeWriteError",
    "SafeWriteState",
    "SpaceCheck",
    "check_free_space",
    "effective_parameters",
    "estimate_photo_bytes",
    "estimate_video_bytes",
    "expected_frames",
    "final_output_path",
    "is_disk_full",
    "is_reserved_device_name",
    "is_temporary_name",
    "new_token",
    "plan_output",
    "remove_leftovers",
    "run_batch",
    "scan_temporaries",
    "temporaries_of",
    "temporary_path",
    "validate_suffix",
]
