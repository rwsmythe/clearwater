"""The application: the composition root, the entry point, start-up and the export worker.

- :mod:`clearwater.app.composition`: the Qt-free composition root, the one product place that
  builds the real engines (photo legs in WP4.1, video legs in WP4.2, the application's one proxy
  cache in WP4.3).
- :mod:`clearwater.app.main`: the entry point (``main``, ``python -m clearwater``) and
  ``build_application``; the ONLY module here that imports ``clearwater.gui`` or loads Qt.
- :mod:`clearwater.app.startup`: the write journal, the leftover clean-up, the start-up jobs.
- :mod:`clearwater.app.analysis_adapter`: the GUI's analysis over WP3.11's engine.
- :mod:`clearwater.app.activity`: one activity per clip and the export wrapper.
- :mod:`clearwater.app.export_worker`: the export worker process (WP4.6, Qt-free); ``python -m
  clearwater.app.export_worker`` runs one video export job for the composition root's
  ``process_export_jobs``, which the export wrapper wraps.

The worker aside, the four Qt-free modules meet the GUI's seams by structure. This file imports
only the root, so importing ``clearwater.app`` never loads the GUI, PySide6 or CuPy and
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
