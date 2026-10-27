"""WP3.14 test support: doubles for the export engine (no FFmpeg, no GPU).

Imported by ``tests/test_jobs_export*.py`` and ``tests/test_jobs_batch.py``; holds no tests.
"""

from __future__ import annotations

import errno
import threading
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
    passes and it raises), ``fail_at`` (a write that raises ``fail_error``), ``close_error``.
    Like the product sink it deletes ``out_path`` on a failure and on ``abort``.
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

    def capabilities(self) -> tuple[EncoderCapability, ...]:
        self.calls.append("capabilities")
        return self._capabilities

    def open(self, probe: ProbeResult, out_path: Path, **kwargs: Any) -> None:
        self.calls.append("open")
        self.out_path = out_path
        self.open_kwargs = kwargs
        out_path.write_bytes(b"H")

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
        if self.close_error is not None:
            self._delete()
            raise self.close_error
        return SinkReport(len(self.frames), self.report.warnings, self.report.not_carried)

    def abort(self) -> None:
        self.calls.append("abort")
        self.aborted.set()
        self._delete()

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
