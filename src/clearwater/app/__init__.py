"""The application: the composition root (WP4.1) and, from WP4.3, the entry point and start-up.

WP4.1 puts the Qt-free composition root here, :mod:`clearwater.app.composition`, the one product
place that builds the real engines (photo legs in WP4.1, video legs in WP4.2). WP4.3 adds the
entry point and start-up beside it; those modules may import ``clearwater.gui``, but this file
imports only the root, so importing ``clearwater.app`` never loads the GUI, PySide6 or CuPy and
``clearwater.gui.engines`` can import the root without a cycle.
"""

from __future__ import annotations

from .composition import (
    backend_selector,
    correction_methods,
    export_jobs,
    photo_reader,
    photo_writer,
    proxy_cache,
    video_sink,
    video_source,
)

__all__ = [
    "backend_selector",
    "correction_methods",
    "export_jobs",
    "photo_reader",
    "photo_writer",
    "proxy_cache",
    "video_sink",
    "video_source",
]
