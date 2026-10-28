"""The composition root: the one product place that builds the real engines (WP4.1).

Each function returns a fresh real component. Importing this module builds none of the root's
components and probes no device (``clearwater.core`` builds its module-level CPU backend when it
is imported and probes CUDA on the first selection that is not forced).
WP4.1 builds the photo legs: the IF-6 reader and writer of :mod:`clearwater.io.photo`, the IF-3
methods of :mod:`clearwater.methods` (``"c3"`` first, D16), the IF-2 selection of
:mod:`clearwater.core` and the export engine of :mod:`clearwater.jobs` behind the WP3.19
``ExportJobs`` seam. A video request reaching :func:`export_jobs` fails with
:data:`~clearwater.jobs.export_seam.UNAVAILABLE_TEXT` and writes nothing; WP4.2 builds the video
legs here and removes that routing.

This module imports nothing from ``clearwater.gui``, no PySide6 and no ``cupy``/``cupyx``
(AD-29), and never resolves the app-data folder: the caller passes settings in.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from fractions import Fraction
from pathlib import Path

import clearwater
from clearwater import core
from clearwater.interfaces import (
    CacheKey,
    ColorDescription,
    CorrectionMethod,
    JobResult,
    PhotoSink,
    PhotoSource,
    ProbeResult,
    Progress,
    VideoStreamInfo,
)
from clearwater.interfaces.stubs import StubProxyCache, StubVideoSink, StubVideoSource
from clearwater.io.photo import PhotoReader, PhotoWriter
from clearwater.jobs import BackendSelector, ExportEngine
from clearwater.jobs.export_seam import ExportJobs, ExportRequest, unavailable_exports
from clearwater.methods import available_methods


def photo_reader() -> PhotoSource:
    """Return a new photo reader (IF-6 ``PhotoSource``; HEIC, JPEG, PNG, TIFF; D116 refusals).

    Returns:
        A :class:`~clearwater.io.photo.PhotoReader`.
    """
    return PhotoReader()


def photo_writer() -> PhotoSink:
    """Return a new photo writer (IF-6 ``PhotoSink``; PNG at 8 or 16 bit, ICC, EXIF, provenance).

    Returns:
        A :class:`~clearwater.io.photo.PhotoWriter`.
    """
    return PhotoWriter()


def correction_methods() -> dict[str, CorrectionMethod]:
    """Return new instances of the registered correction methods, the default first (D16).

    Returns:
        Method id -> method: ``"c3"`` then ``"ancuti2018"``.
    """
    return available_methods()


def backend_selector() -> BackendSelector:
    """Return the IF-2 backend selection (AD-1, AD-9, D111).

    Returns:
        ``clearwater.core.select_backend`` itself.
    """
    return core.select_backend


class _PhotoExports:
    """The root's ``ExportJobs`` in WP4.1: photos to the engine, videos unavailable (WP4.2 removes).

    A photo request gets the export engine's job. A video request gets the job of
    :func:`~clearwater.jobs.export_seam.unavailable_exports`, which fails with ``UNAVAILABLE_TEXT``
    and opens no file. Any other request is passed to the engine, which refuses it as malformed.
    """

    def __init__(self, engine: ExportEngine) -> None:
        """Hold the engine.

        Args:
            engine: The photo export engine.
        """
        self._engine = engine
        self._unavailable = unavailable_exports()

    def job(self, request: ExportRequest) -> Callable[[Progress], JobResult]:
        """Return the IF-8 job for ``request`` (the ``ExportJobs`` contract).

        Args:
            request: What to export.

        Returns:
            The job.

        Raises:
            ValueError: The request is malformed in itself (raised by the engine).
        """
        if isinstance(request, ExportRequest) and request.kind == "video":
            return self._unavailable.job(request)
        return self._engine.job(request)


def _no_video_probe() -> ProbeResult:
    """Return the probe result of the never-reached stub video source (no file is probed)."""
    video = VideoStreamInfo(
        codec="none",
        width=1,
        height=1,
        bit_depth=8,
        pix_fmt="none",
        chroma_siting="unspecified",
        color=ColorDescription("bt709", "bt709", "bt709", "limited", 8, False, None),
        frame_rate=Fraction(1),
        time_base=Fraction(1),
        nb_frames=0,
        rotation=0,
        vfr=False,
    )
    return ProbeResult(
        path=Path("none"),
        container="none",
        duration_s=Fraction(0),
        start_offset_s=Fraction(0),
        video=video,
        audio=(),
        data=(),
        edit_list=(),
        faults=(),
        gopro=None,
    )


def _no_cache_key(path: Path) -> CacheKey:
    """Refuse: video export is not built in WP4.1, so no cache key is ever needed."""
    raise RuntimeError("video export is not available in this build")


def export_jobs(
    *,
    app_version: str = clearwater.__version__,
    reader: PhotoSource | None = None,
    writer: PhotoSink | None = None,
    methods: Mapping[str, CorrectionMethod] | None = None,
    select_backend: BackendSelector | None = None,
    on_stage: Callable[[str], None] | None = None,
) -> ExportJobs:
    """Return a new export engine for photos behind the WP3.19 seam (videos fail, WP4.2 adds them).

    The engine reads with :func:`photo_reader`, renders with :func:`correction_methods`, selects
    with :func:`backend_selector` and writes with :func:`photo_writer` through
    ``clearwater.jobs.SafeWrite``. A video request's job fails with ``UNAVAILABLE_TEXT`` and writes
    nothing; the engine's video collaborators are interface stubs that no job reaches. The
    overrides exist for tests and for the V8 recording sink only.

    Args:
        app_version: The version recorded in provenance (D91).
        reader: The photo reader; :func:`photo_reader` when None.
        writer: The photo writer; :func:`photo_writer` when None.
        methods: The methods by id, default first; :func:`correction_methods` when None.
        select_backend: The backend selection; :func:`backend_selector` when None.
        on_stage: The engine's phase hook (the V16 instrument's); none when None.

    Returns:
        The export jobs.
    """
    engine = ExportEngine(
        methods=correction_methods() if methods is None else methods,
        video_source=StubVideoSource((), _no_video_probe()),
        sink_factory=StubVideoSink,
        photo_reader=photo_reader() if reader is None else reader,
        photo_writer=photo_writer() if writer is None else writer,
        cache=StubProxyCache(),
        cache_key=_no_cache_key,
        select_backend=backend_selector() if select_backend is None else select_backend,
        app_version=app_version,
        on_stage=on_stage,
    )
    return _PhotoExports(engine)
