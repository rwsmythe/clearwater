"""WP3.14 test support: doubles for the export engine (no FFmpeg, no GPU).

Imported by ``tests/test_jobs_export*.py`` and ``tests/test_jobs_batch.py``; holds no tests.
"""

from __future__ import annotations

import contextlib
import errno
import threading
import time
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

from clearwater.core.backend import backend_for
from clearwater.interfaces import (
    ArrayBackend,
    CacheKey,
    EncoderCapability,
    Frame,
    Image,
    ParameterSet,
    PhotoMetadata,
    ProbeResult,
    Settings,
    SinkReport,
)
from clearwater.interfaces.stubs import StubProgress, StubProxyCache
from clearwater.jobs import ExportEngine
from clearwater.jobs.export_seam import ExportRequest
from test_analysis_support import COLOR, GrayWorld, ListSource, make_probe, synthetic_frames

CPU = backend_for("cpu")
NOW = datetime(2026, 10, 27, tzinfo=UTC)

CAPABILITIES = (
    EncoderCapability("hevc_nvenc", False, "no NVIDIA encoder here", (8, 10), True),
    EncoderCapability("libx265", True, None, (8, 10), False),
)

CLOSE_GATES = ("before_flush", "flush", "finished", "closed")
"""Where :class:`FakeSink`'s ``close`` can stop: before the flush, in it, after the finish but
before the closed mark, after the mark (the four abort timings of CHARC `e7d25105`)."""


def parameter_set(method: str = "grayworld", **values: Any) -> ParameterSet:
    """Return a (partial) parameter set for ``method``."""
    return ParameterSet(method=method, parameters=values, created=NOW, app_version="test")


def cpu_selector(
    reason: str = "GPU",
) -> Callable[[Settings, int, int, str], tuple[ArrayBackend, str]]:
    """Return a backend selector that always picks the CPU backend with ``reason``."""

    def select(settings: Settings, height: int, width: int, method_id: str) -> tuple[Any, str]:
        if settings.force_cpu:
            return CPU, "CPU: forced"
        return CPU, reason

    return select


class FakeSink:
    """An IF-5 sink double: writes a byte per frame to ``out_path``; records every call.

    Options: ``block_at`` (a write that blocks until :meth:`abort`, or ``block_timeout_s``
    passes and it raises), ``fail_at`` (a write that raises ``fail_error``), ``close_error``,
    ``close_gate`` (``close`` stops at one of :data:`CLOSE_GATES`, sets ``at_gate`` and waits
    for ``release``; at ``"flush"`` an ``abort`` releases it instead, as killing FFmpeg ends a
    real flush). Like the product sink it deletes ``out_path`` on a failure and on ``abort``,
    and an ``abort`` after ``close`` has marked itself closed does nothing; an ``abort`` in the
    window after the finish and before that mark deletes the output while ``close`` still
    returns its report (WP3.10's sink, CHARC `e7d25105` condition 1).
    """

    def __init__(self, capabilities: Sequence[EncoderCapability] = CAPABILITIES) -> None:
        self._capabilities = tuple(capabilities)
        self.calls: list[str] = []
        self.frames: list[Frame] = []
        self.out_path: Path | None = None
        self.open_kwargs: dict[str, Any] = {}
        self.block_at: int | None = None
        self.block_timeout_s = 5.0
        self.blocked = threading.Event()
        self.aborted = threading.Event()
        self.fail_at: int | None = None
        self.fail_error: BaseException = OSError(errno.ENOSPC, "No space left on device")
        self.close_error: BaseException | None = None
        self.report = SinkReport(0, ("sink warning",), ("timecode track",))
        self.phase = "new"
        self.close_gate: str | None = None
        self.at_gate = threading.Event()
        self.release = threading.Event()
        self.gate_timeout_s = 10.0
        self.aborted_in_close = threading.Event()
        self._in_close = False

    def capabilities(self) -> tuple[EncoderCapability, ...]:
        self.calls.append("capabilities")
        return self._capabilities

    def open(self, probe: ProbeResult, out_path: Path, **kwargs: Any) -> None:
        self.calls.append("open")
        self.out_path = out_path
        self.open_kwargs = kwargs
        out_path.write_bytes(b"H")
        self.phase = "open"

    def write(self, frame: Frame) -> None:
        self.calls.append("write")
        assert frame.device == "cpu"
        if self.aborted.is_set():
            raise RuntimeError("encoder_failed: the encoder was stopped")
        if self.block_at is not None and len(self.frames) == self.block_at:
            self.blocked.set()
            if not self.aborted.wait(self.block_timeout_s):
                raise TimeoutError("the blocked write was never released")
            raise RuntimeError("encoder_failed: the encoder was stopped")
        if self.fail_at is not None and len(self.frames) == self.fail_at:
            self._delete()
            raise self.fail_error
        self.frames.append(frame)
        assert self.out_path is not None
        with self.out_path.open("ab") as handle:
            handle.write(b"f")

    def close(self) -> SinkReport:
        self.calls.append("close")
        self._in_close = True
        try:
            if self.close_error is not None:
                self._delete()
                raise self.close_error
            self._gate("before_flush")
            self._stopped()
            if self.close_gate == "flush":  # blocks like FFmpeg's flush: abort ends it
                self.at_gate.set()
                end = time.monotonic() + self.gate_timeout_s
                while not (self.aborted.is_set() or self.release.is_set()):
                    if time.monotonic() > end:
                        raise TimeoutError("the flush was never released")
                    time.sleep(0.01)
                self._stopped()
            report = SinkReport(len(self.frames), self.report.warnings, self.report.not_carried)
            self._gate("finished")
            self.phase = "closed"
            self._gate("closed")
            return report
        finally:
            self._in_close = False

    def abort(self) -> None:
        self.calls.append("abort")
        if self._in_close:
            self.aborted_in_close.set()
        self.aborted.set()
        if self.phase == "closed":
            return  # the output is the caller's after a close
        self.phase = "aborted"
        with contextlib.suppress(OSError):  # never raises, like the product's abort
            self._delete()

    def _gate(self, name: str) -> None:
        """Stop at ``name`` when it is the configured gate, until released."""
        if self.close_gate != name:
            return
        self.at_gate.set()
        if not self.release.wait(self.gate_timeout_s):
            raise TimeoutError(f"the close gate {name!r} was never released")

    def _stopped(self) -> None:
        """Raise as a real sink does once its encoder was stopped by ``abort``."""
        if self.aborted.is_set():
            # A concurrent abort may be deleting the same file (Windows: delete pending); the
            # stopped encoder's error stays the one raised, never the cleanup's.
            with contextlib.suppress(OSError):
                self._delete()
            raise RuntimeError("encoder_failed: the encoder was stopped")

    def _delete(self) -> None:
        if self.out_path is not None:
            self.out_path.unlink(missing_ok=True)


class FakePhotoReader:
    """An IF-6 reader double returning a fixed image."""

    def __init__(self, pixels: np.ndarray | None = None) -> None:
        rng = np.random.default_rng(3)
        self.pixels = pixels if pixels is not None else rng.uniform(0.1, 0.9, (24, 32, 3))

    def read(self, path: Path) -> tuple[Image, PhotoMetadata]:
        if not path.exists():
            raise FileNotFoundError(f"no such photo: {path.name}")
        image = Image(np.asarray(self.pixels, dtype=np.float32), "cpu", COLOR, True)
        return image, PhotoMetadata("png", None, 1)


class FakePhotoWriter:
    """An IF-6 writer double: writes the pixels' bytes; records the provenance it got."""

    def __init__(self) -> None:
        self.provenance: Mapping[str, Any] | None = None
        self.paths: list[Path] = []
        self.error: BaseException | None = None

    def write(
        self,
        image: Image,
        meta: PhotoMetadata,
        out_path: Path,
        *,
        bit_depth: int,
        provenance: Mapping[str, Any] | None,
    ) -> None:
        assert image.device == "cpu"
        self.paths.append(out_path)
        self.provenance = provenance
        if self.error is not None:
            with out_path.open("wb") as handle:
                handle.write(b"partial")
            raise self.error
        out_path.write_bytes(np.asarray(image.pixels).tobytes())


def product_engine(
    cache_folder: Path,
    *,
    methods: Mapping[str, Any] | None = None,
    select: Callable[[Settings, int, int, str], tuple[ArrayBackend, str]] | None = None,
    sink_factory: Callable[[], Any] | None = None,
    on_stage: Callable[[str], None] | None = None,
) -> ExportEngine:
    """Return the engine over the product collaborators (what WP4.3 will wire).

    Args:
        cache_folder: The analysis cache folder (under the test's temporary folder).
        methods: The methods by id; ``available_methods()`` when None.
        select: The backend selector; ``clearwater.core.select_backend`` when None.
        sink_factory: The sink factory; ``FFmpegVideoSink`` when None.
        on_stage: The phase hook.
    """
    from clearwater.cache import DiskProxyCache, cache_key
    from clearwater.core import select_backend
    from clearwater.io.photo import PhotoReader, PhotoWriter
    from clearwater.io.video import FFmpegVideoSink, FFmpegVideoSource
    from clearwater.methods import available_methods

    return ExportEngine(
        methods=methods if methods is not None else available_methods(),
        video_source=FFmpegVideoSource(),
        sink_factory=sink_factory or FFmpegVideoSink,
        photo_reader=PhotoReader(),
        photo_writer=PhotoWriter(),
        cache=DiskProxyCache(cache_folder),
        cache_key=cache_key,
        select_backend=select or select_backend,
        on_stage=on_stage,
    )


class Rig:
    """An engine over doubles, with a source file on disk and a fresh sink per job."""

    def __init__(
        self,
        tmp_path: Path,
        *,
        frames: int = 6,
        reason: str = "GPU",
        nb_frames: int | None = None,
        on_stage: Callable[[str], None] | None = None,
    ) -> None:
        self.folder = tmp_path
        self.video = tmp_path / "clip.mp4"
        self.video.write_bytes(b"source video bytes")
        self.photo = tmp_path / "shot.png"
        self.photo.write_bytes(b"source photo bytes")
        self.frames = synthetic_frames(frames)
        self.probe = make_probe(nb_frames=nb_frames if nb_frames is not None else frames)
        self.source = ListSource(self.frames, self.probe)
        self.cache = StubProxyCache()
        self.sinks: list[FakeSink] = []
        self.next_sink: Callable[[], FakeSink] = FakeSink
        self.reader = FakePhotoReader()
        self.writer = FakePhotoWriter()
        self.method = GrayWorld()
        self.engine = ExportEngine(
            methods={"grayworld": self.method},
            video_source=self.source,
            sink_factory=self._sink,
            photo_reader=self.reader,
            photo_writer=self.writer,
            cache=self.cache,
            cache_key=lambda path: CacheKey(size=1, mtime_ns=2, cache_version=3),
            select_backend=cpu_selector(reason),
            app_version="9.9.9",
            on_stage=on_stage,
        )

    def _sink(self) -> FakeSink:
        sink = self.next_sink()
        self.sinks.append(sink)
        return sink

    @property
    def sink(self) -> FakeSink:
        """The last sink made."""
        return self.sinks[-1]

    def request(
        self, kind: str = "video", source: Path | None = None, **settings: Any
    ) -> ExportRequest:
        """Return a request for the rig's video (or photo) with the given settings."""
        path = source if source is not None else (self.video if kind == "video" else self.photo)
        values: dict[str, Any] = {"video_encoder": "libx265", **settings}
        return ExportRequest(path, kind, parameter_set(), Settings(**values))  # type: ignore[arg-type]

    def run(self, request: ExportRequest, progress: StubProgress | None = None) -> Any:
        """Build and run the job."""
        return self.engine.job(request)(progress or StubProgress())

    def files(self) -> list[str]:
        """The names in the rig's folder, sorted."""
        return sorted(p.name for p in self.folder.iterdir())
