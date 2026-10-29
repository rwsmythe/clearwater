"""WP4.3 task 5: one activity per clip (DR-62, question 8: WAIT) and the export wrapper (DR-82).

``ClipLocks`` lets one activity per cache key run its engine; the other waits on its worker,
cancellably, reporting "Waiting for the other job on this clip". ``GuardedExports`` runs, on
the worker and in this order: the DR-82 pre-plan name check (a failed item naming the source
and saying to rename it, before any read or probe), the journal entry (D85; a journal that
cannot be written fails the export, before any read or probe), the clip's lock for a video, the
preview's FFT plan release (DR-68), the engine's job, the AD-9 log line; the entry stays while
its folder holds a temporary (R1-2, R1-3, ruling d530b564). Both
orders of a real export and a real GUI analysis of one fixture clip are driven, the cache entry
is complete and consistent afterwards (V17: a reopen skips the decode pass), and a cancel while
waiting returns ``CANCELLED`` with nothing written.
"""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Any

import pytest

from clearwater import core
from clearwater.analysis import AnalysisEngine
from clearwater.app import activity, composition
from clearwater.app.activity import RENAME_TEXT, WAITING_TEXT, ClipLocks, GuardedExports
from clearwater.app.analysis_adapter import EngineClipAnalysis
from clearwater.app.startup import WriteJournal, clean_leftovers
from clearwater.config import new_parameter_set
from clearwater.interfaces import JobResult, Progress, Settings
from clearwater.interfaces.stubs import StubProgress
from clearwater.io.photo import PhotoReader
from clearwater.io.video import FFmpegVideoSource
from clearwater.jobs import MediaKind, final_output_path, new_token, temporary_path
from clearwater.jobs.export_seam import CANCELLED, ExportRequest

CLIP = "vid-hevc8-bt709-full"


def settings(out: Path, **changes: Any) -> Settings:
    values: dict[str, Any] = {
        "output_folder": out,
        "force_cpu": True,
        "video_encoder": "libx265",
    }
    values.update(changes)
    return Settings(**values)


def request(source: Path, out: Path, kind: Any = "video") -> ExportRequest:
    return ExportRequest(source, kind, new_parameter_set("c3", {}), settings(out))


class Rig:
    """The application's export side over a real engine, one opened cache and a journal."""

    def __init__(self, tmp_path: Path, config: Path | None = None) -> None:
        self.out = tmp_path / "out"
        self.out.mkdir()
        self.cache = composition.proxy_cache_opener(tmp_path / "cache")
        assert self.cache.open(10**10) is None
        self.locks = ClipLocks()
        self.journal = WriteJournal(tmp_path / "config" if config is None else config)
        self.events: list[str] = []
        self.exports = GuardedExports(
            composition.export_jobs(cache=self.cache),
            cache=self.cache,
            locks=self.locks,
            journal=self.journal,
            release_device_plans=lambda: self.events.append("release"),
        )


def run_in_thread(call: Any, *args: Any) -> tuple[threading.Thread, dict[str, Any]]:
    box: dict[str, Any] = {}

    def body() -> None:
        try:
            box["value"] = call(*args)
        except Exception as exc:
            box["error"] = exc

    thread = threading.Thread(target=body, daemon=True)
    thread.start()
    return thread, box


def wait_for(condition: Any, timeout_s: float = 30.0) -> None:
    deadline = threading.Event()
    for _ in range(int(timeout_s / 0.02)):
        if condition():
            return
        deadline.wait(0.02)
    raise AssertionError("condition not reached")


# ClipLocks.


def test_a_second_activity_waits_cancellably_for_the_first() -> None:
    locks = ClipLocks()
    key = object()
    first = StubProgress()
    assert locks.acquire(key, first)  # type: ignore[arg-type]
    assert first.reports == []
    waiting = StubProgress()
    thread, box = run_in_thread(locks.acquire, key, waiting)
    wait_for(lambda: waiting.reports == [(0, None, WAITING_TEXT)])
    assert thread.is_alive()
    locks.release(key)  # type: ignore[arg-type]
    thread.join(5)
    assert box == {"value": True} and locks.held(key)  # type: ignore[arg-type]
    cancelled = StubProgress()
    thread, box = run_in_thread(locks.acquire, key, cancelled)
    wait_for(lambda: bool(cancelled.reports))
    cancelled.cancel()
    thread.join(5)
    assert box == {"value": False}
    locks.release(key)  # type: ignore[arg-type]
    assert not locks.held(key)  # type: ignore[arg-type]


# DR-82 (ruling Q22): the pre-plan name check, before any read or probe.


@pytest.mark.parametrize("kind", ["photo", "video"])
def test_a_refused_output_name_fails_before_any_read_or_probe(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    rig = Rig(tmp_path)
    touched: list[str] = []
    monkeypatch.setattr(PhotoReader, "read", lambda self, path: touched.append("read"))
    monkeypatch.setattr(FFmpegVideoSource, "probe", lambda self, path: touched.append("probe"))
    source = tmp_path / ("carrier:input.jpg" if kind == "photo" else "carrier:clip.mp4")
    result = rig.exports.job(request(source, rig.out, kind))(StubProgress())
    assert not result.ok
    assert result.failure == RENAME_TEXT.format(name=source.name)
    assert result.failure == (
        f"{source.name}: this file name cannot be used for an output file; rename the file."
    )
    assert touched == [] and rig.events == [] and rig.journal.entries() == ()
    assert list(rig.out.iterdir()) == []


def test_any_other_planning_error_is_left_to_the_engine(sample: Any, tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    bad = ExportRequest(
        sample("jpeg-gradient-srgb"),
        "photo",
        new_parameter_set("c3", {}),
        settings(rig.out, output_suffix="a/b"),
    )
    result = rig.exports.job(bad)(StubProgress())
    assert not result.ok and "suffix" in (result.failure or "")
    assert rig.journal.entries() == () and list(rig.out.iterdir()) == []


# The journal (D85, question 3): written before a temporary exists, cleared after.


@pytest.mark.usefixtures("ffmpeg_tools")
@pytest.mark.parametrize("ending", ["commit", "failure", "cancel"])
def test_the_journal_holds_the_folder_while_the_engine_runs(
    sample: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, ending: str
) -> None:
    rig = Rig(tmp_path)
    seen: list[tuple[tuple[str, Path], ...]] = []
    temporaries: list[list[str]] = []
    real = rig.exports._engine.job

    def job(req: ExportRequest) -> Any:
        inner = real(req)

        def run(progress: Progress) -> JobResult:
            seen.append(rig.journal.entries())
            temporaries.append([p.name for p in rig.out.iterdir()])
            if ending == "failure":
                return JobResult(False, (), (), "planted failure", "cpu", 0.0)
            if ending == "cancel":
                progress.cancel()  # type: ignore[attr-defined]
            return inner(progress)

        return run

    monkeypatch.setattr(rig.exports._engine, "job", job)
    photo = sample("jpeg-gradient-srgb")
    result = rig.exports.job(request(photo, rig.out, "photo"))(StubProgress())
    assert len(seen) == 1 and [folder for _, folder in seen[0]] == [rig.out.absolute()]
    assert temporaries == [[]]  # the entry exists before any temporary does
    assert rig.journal.entries() == ()
    assert rig.events == ["release"]  # DR-68: before the engine selects
    if ending == "commit":
        assert result.ok and [p.name for p in rig.out.iterdir()] == [
            "jpeg-gradient-srgb_corrected.png"
        ]
    else:
        assert not result.ok and list(rig.out.iterdir()) == []
        if ending == "cancel":
            assert result.failure is CANCELLED


@pytest.mark.parametrize("kind", ["photo", "video"])
def test_an_unwritable_journal_fails_the_export_before_any_read_or_probe(
    sample: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    """R1-2 (ruling d530b564): no clean-up record, no export; nothing is read or written."""
    blocked = tmp_path / "config"
    blocked.write_text("a file where the configuration folder should be", encoding="utf-8")
    rig = Rig(tmp_path, config=blocked)
    sources = tmp_path / "sources"
    sources.mkdir()
    name = "IMG_1.jpg" if kind == "photo" else "clip.mp4"
    source = sources / name
    source.write_bytes(sample("jpeg-gradient-srgb" if kind == "photo" else CLIP).read_bytes())
    touched: list[str] = []
    monkeypatch.setattr(PhotoReader, "read", lambda self, path: touched.append("read"))
    monkeypatch.setattr(FFmpegVideoSource, "probe", lambda self, path: touched.append("probe"))
    monkeypatch.setattr(rig.cache, "key_for", lambda path: touched.append("key"))
    real = rig.exports._engine.job

    def job(req: ExportRequest) -> Any:
        inner = real(req)

        def run(progress: Progress) -> JobResult:
            touched.append("engine")
            return inner(progress)

        return run

    monkeypatch.setattr(rig.exports._engine, "job", job)
    result = rig.exports.job(request(source, None, kind))(StubProgress())  # type: ignore[arg-type]
    assert not result.ok and result.failure is not None
    assert result.failure.startswith(
        "the export was not started because its clean-up record could not be written in "
        f"{blocked} ("
    )
    assert touched == [] and rig.events == []
    assert [p.name for p in sources.iterdir()] == [name] and list(rig.out.iterdir()) == []


class _Crash(BaseException):
    """A planted process death mid-job: nothing runs after it but the ``finally`` blocks."""


@pytest.mark.parametrize("ending", ["crash", "locked"])
def test_an_entry_stays_while_its_folder_holds_a_temporary(
    sample: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, ending: str
) -> None:
    """R1-3 (ruling d530b564): the entry stays until that folder's clean-up has succeeded.

    A crash after the temporary is written, and a job that returns with its temporary left (the
    engine's "it is removed at the next start"), both keep the source folder's entry, so the
    next start with no output folder set removes the temporary (D85 at the default placement).
    """
    rig = Rig(tmp_path)
    sources = tmp_path / "sources"
    sources.mkdir()
    photo = sources / "IMG_1.jpg"
    photo.write_bytes(sample("jpeg-gradient-srgb").read_bytes())
    planted: list[Path] = []

    def job(req: ExportRequest) -> Any:
        def run(progress: Progress) -> JobResult:
            final = final_output_path(req.source, req.settings, MediaKind.PHOTO)
            planted.append(temporary_path(final, new_token()))
            planted[0].write_bytes(b"partial")
            if ending == "crash":
                raise _Crash
            return JobResult(True, (), ("its temporary could not be removed",), None, "cpu", 0.0)

        return run

    monkeypatch.setattr(rig.exports._engine, "job", job)
    run = rig.exports.job(request(photo, None, "photo"))  # type: ignore[arg-type]
    if ending == "crash":
        with pytest.raises(_Crash):
            run(StubProgress())
    else:
        assert run(StubProgress()).ok
    assert [folder for _, folder in rig.journal.entries()] == [sources.absolute()]
    report = clean_leftovers(settings(None), WriteJournal(tmp_path / "config"))  # type: ignore[arg-type]
    assert report.removed == (planted[0],) and not planted[0].exists()
    assert rig.journal.entries() == ()


def test_the_ad9_log_line_names_the_jobs_device(
    sample: Any, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    rig = Rig(tmp_path)
    with caplog.at_level(logging.INFO, logger=activity.__name__):
        result = rig.exports.job(request(sample("jpeg-gradient-srgb"), rig.out, "photo"))(
            StubProgress()
        )
    assert result.ok and result.device == "CPU: forced"
    assert "export job jpeg-gradient-srgb.jpg: ok; device CPU: forced" in caplog.text


# DR-62 in both orders, on the real engines and a fixture clip.


class HeldFactory:
    """Builds real engines whose jobs wait on ``release`` once their work is done."""

    def __init__(self) -> None:
        self.release = threading.Event()
        self.done = threading.Event()
        self.engines: list[AnalysisEngine] = []

    def __call__(self, **kwargs: Any) -> AnalysisEngine:
        factory = self

        class Held(AnalysisEngine):
            def _once(self) -> Any:
                job = super()._once()

                def held(progress: Any) -> Any:
                    result = job(progress)
                    factory.done.set()
                    assert factory.release.wait(60)
                    return result

                return held

        engine = Held(**kwargs)
        self.engines.append(engine)
        return engine


def gui_analysis(rig: Rig, clip: Path, factory: Any = AnalysisEngine) -> EngineClipAnalysis:
    """The GUI's adapter over the real engine, as the application builds it."""
    return EngineClipAnalysis(
        path=clip,
        probe=FFmpegVideoSource().probe(clip),
        method=composition.correction_methods()["c3"],
        cache=rig.cache,
        select_backend=core.select_backend,
        settings=lambda: Settings(force_cpu=True),
        locks=rig.locks,
        engine_factory=factory,
    )


def decoded_by_a_reopen(rig: Rig, clip: Path) -> int:
    """Frames a fresh GUI analysis decodes on the shared entry (0: V17's reopen skips it)."""
    counted: list[int] = []

    def source_for(device: Any) -> Any:
        source = composition.video_source(device)
        real = source.frames

        def frames(probe: Any, **kwargs: Any) -> Any:
            for frame in real(probe, **kwargs):
                counted.append(1)
                yield frame

        source.frames = frames  # type: ignore[method-assign]
        return source

    adapter = EngineClipAnalysis(
        path=clip,
        probe=FFmpegVideoSource().probe(clip),
        method=composition.correction_methods()["c3"],
        cache=rig.cache,
        select_backend=core.select_backend,
        settings=lambda: Settings(force_cpu=True),
        locks=rig.locks,
        source_for=source_for,
    )
    adapter.run(new_parameter_set("c3", {}), StubProgress())
    return len(counted)


@pytest.mark.usefixtures("ffmpeg_tools")
def test_an_export_waits_for_the_gui_analysis_of_its_clip(sample: Any, tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    clip = sample(CLIP)
    held = HeldFactory()
    adapter = gui_analysis(rig, clip, held)
    analysing, analysis_box = run_in_thread(
        adapter.run, new_parameter_set("c3", {}), StubProgress()
    )
    assert held.done.wait(60)
    progress = StubProgress()
    exporting, export_box = run_in_thread(rig.exports.job(request(clip, rig.out)), progress)
    wait_for(lambda: (0, None, WAITING_TEXT) in progress.reports)
    assert exporting.is_alive() and list(rig.out.iterdir()) == []
    held.release.set()
    analysing.join(60)
    exporting.join(120)
    assert analysis_box == {"value": None}
    result = export_box["value"]
    assert result.ok, result.failure
    entry = rig.cache.lookup(rig.cache.key_for(clip))
    assert entry is not None and entry.complete
    assert decoded_by_a_reopen(rig, clip) == 0  # V17: one decode pass


@pytest.mark.usefixtures("ffmpeg_tools")
def test_a_gui_recompute_waits_for_the_export_of_its_clip(
    sample: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    rig = Rig(tmp_path)
    clip = sample(CLIP)
    adapter = gui_analysis(rig, clip)
    adapter.run(new_parameter_set("c3", {}), StubProgress())  # complete
    in_export = threading.Event()
    leave_export = threading.Event()
    real = rig.exports._engine.job

    def job(req: ExportRequest) -> Any:
        inner = real(req)

        def run(progress: Progress) -> JobResult:
            in_export.set()
            assert leave_export.wait(60)
            return inner(progress)

        return run

    monkeypatch.setattr(rig.exports._engine, "job", job)
    exporting, export_box = run_in_thread(rig.exports.job(request(clip, rig.out)), StubProgress())
    assert in_export.wait(30)
    progress = StubProgress()
    recompute, recompute_box = run_in_thread(
        adapter.run, new_parameter_set("c3", {"strength": 0.5}), progress
    )
    wait_for(lambda: (0, None, WAITING_TEXT) in progress.reports)
    assert recompute.is_alive()
    leave_export.set()
    exporting.join(120)
    recompute.join(60)
    assert export_box["value"].ok, export_box["value"].failure
    assert recompute_box == {"value": None}
    pts = adapter.pts()[0]
    assert adapter.statistics(pts) is not None
    entry = rig.cache.lookup(rig.cache.key_for(clip))
    assert entry is not None and entry.complete
    assert decoded_by_a_reopen(rig, clip) == 0


@pytest.mark.usefixtures("ffmpeg_tools")
def test_a_cancel_while_waiting_returns_cancelled_with_nothing_written(
    sample: Any, tmp_path: Path
) -> None:
    rig = Rig(tmp_path)
    clip = sample(CLIP)
    key = rig.cache.key_for(clip)
    assert rig.locks.acquire(key, StubProgress())
    progress = StubProgress()
    exporting, box = run_in_thread(rig.exports.job(request(clip, rig.out)), progress)
    wait_for(lambda: (0, None, WAITING_TEXT) in progress.reports)
    progress.cancel()
    exporting.join(30)
    result = box["value"]
    assert not result.ok and result.failure is CANCELLED
    assert list(rig.out.iterdir()) == [] and rig.journal.entries() == ()
    assert rig.events == []  # the engine never ran: no plan release, no selection
    rig.locks.release(key)
