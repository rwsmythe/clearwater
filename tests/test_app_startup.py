"""WP4.3 task 3: the entry point and start-up on the running shell (Q4, Q5, Q11, Q17, S1, S3).

``python -m clearwater`` reaches the event loop and exits 0; ``build_application`` builds the
wholly real engines (ruling Q17), cleans leftovers before any panel or job exists (S-order,
DR-35 (c)), and runs its three start-up jobs off the interface thread: the cache's open with the
settings' limit, the encoder detection into the settings dialog's catalog, and the
graphics-card detection whose AD-9 reason the status bar shows before a file is open (S3). A
failed cache open is shown once and the photo path keeps working (S1 condition 2). A settings
file that fails to decode is set aside (DR-85: ``xfail(strict)`` until WP4.3a's fix is on main).
Nothing in start-up writes outside app data.

The helpers here (``make_app`` and the waits) are shared by the other ``tests/test_app_*.py``
GUI files. Headless on ``offscreen``, app data under ``tmp_path``.
"""

# Other test files import ``make_app`` and use it as a parameter.
# ruff: noqa: F401

from __future__ import annotations

import gc
import json
import os
import subprocess
import sys
import threading
import weakref
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import pytest

import gui_support
from clearwater import core
from clearwater.app import composition
from clearwater.app import main as app_main
from clearwater.app.analysis_adapter import EngineClipAnalysis
from clearwater.app.composition import DeferredProxyCache
from clearwater.app.main import OWNER_STARTUP, Application, build_application
from clearwater.cache import DiskProxyCache
from clearwater.config import Locations, new_parameter_set, save_settings
from clearwater.core.backend import NumpyBackend
from clearwater.gui.jobs import QtJobRunner
from clearwater.interfaces import Settings
from clearwater.io.photo import PhotoReader
from clearwater.io.video import FFmpegVideoSink, FFmpegVideoSource
from clearwater.jobs import ExportEngine
from gui_support import CapturingPresenter

pytestmark = pytest.mark.gui

CLIP = "vid-hevc8-bt709-full"
"""The fixture clip of the light video legs (WP2.3, 45 frames)."""


def app_data(where: Path) -> Locations:
    """App-data folders under ``where``."""
    return Locations(config_dir=where / "config", cache_dir=where / "cache")


def cpu_settings(**changes: Any) -> Settings:
    """Settings for a light run: forced CPU and the software encoder, unless changed."""
    values: dict[str, Any] = {"force_cpu": True, "video_encoder": "libx265"}
    values.update(changes)
    return Settings(**values)


@pytest.fixture
def make_app(qtbot: Any, tmp_path: Path) -> Iterator[Callable[..., Application]]:
    """Build applications over ``tmp_path`` app data; each window is closed at teardown."""
    built: list[Application] = []

    def build(
        settings: Settings | None = None,
        *,
        where: Path | None = None,
        presenter: CapturingPresenter | None = None,
        **kwargs: Any,
    ) -> Application:
        locations = app_data(where or tmp_path)
        if settings is not None:
            save_settings(locations.config_dir, settings)
        application = build_application(
            locations, presenter=presenter or CapturingPresenter(), **kwargs
        )
        built.append(application)
        qtbot.addWidget(application.window)
        qtbot.waitExposed(application.window)
        return application

    yield build
    for application in built:
        application.window.close()


def presenter(application: Application) -> CapturingPresenter:
    """The capturing presenter of a test application."""
    found = application.window.presenter
    assert isinstance(found, CapturingPresenter)
    return found


def wait_started(qtbot: Any, application: Application, timeout_ms: int = 60000) -> None:
    """Wait until the three start-up jobs have delivered their results."""
    window = application.window
    qtbot.waitUntil(lambda: application.cache.wait_open(0), timeout=timeout_ms)
    qtbot.waitUntil(lambda: not application.catalog.detecting(), timeout=timeout_ms)
    qtbot.waitUntil(lambda: window.device_label.text() != "Device: -", timeout=timeout_ms)
    qtbot.waitUntil(lambda: window.jobs.active() == 0, timeout=timeout_ms)


def open_source(qtbot: Any, application: Application, path: Path, timeout_ms: int = 30000) -> None:
    """Open a file and wait until it is the session's source."""
    window = application.window
    window.open_path(path)
    qtbot.waitUntil(lambda: not window.opening(), timeout=timeout_ms)
    source = window.session.source()
    assert source is not None and source.path == path, presenter(application).messages


def wait_analysis(
    qtbot: Any, application: Application, phase: str = "complete", timeout_ms: int = 120000
) -> None:
    """Wait until the open clip's analysis reaches ``phase``."""
    session = application.window.session
    qtbot.waitUntil(lambda: session.analysis().phase == phase, timeout=timeout_ms)


def latest_analysis(application: Application) -> EngineClipAnalysis:
    """The adapter the timeline built last (the only one the application keeps, R1-8)."""
    assert application.analysis is not None, "no analysis was built"
    return application.analysis


@pytest.mark.gui
def test_the_application_keeps_only_the_latest_analysis(make_app, qtbot, tmp_path, sample) -> None:
    """R1-8: opening a second clip leaves the first clip's adapter to the garbage collector."""
    application = make_app(cpu_settings())
    wait_started(qtbot, application)
    clips = []
    for name in ("a.mp4", "b.mp4"):
        clip = tmp_path / name
        clip.write_bytes(sample("vid-hevc8-bt709-full").read_bytes())
        clips.append(clip)
    open_source(qtbot, application, clips[0])
    wait_analysis(qtbot, application)
    first = weakref.ref(latest_analysis(application))
    open_source(qtbot, application, clips[1])
    wait_analysis(qtbot, application)
    assert latest_analysis(application)._path == clips[1]
    gc.collect()
    assert first() is None


# python -m clearwater


QUIT_SCRIPT = """
import runpy, sys
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
original = QApplication.exec
def exec_and_quit():
    QTimer.singleShot(1500, QApplication.instance().quit)
    print("event loop reached", flush=True)
    return original()
QApplication.exec = staticmethod(exec_and_quit)
sys.argv = ["clearwater"]
runpy.run_module("clearwater", run_name="__main__", alter_sys=True)
"""


def test_python_m_clearwater_starts_the_shell_and_exits_0(tmp_path: Path) -> None:
    """The real entry point under offscreen QPA, app data redirected under ``tmp_path``."""
    env = dict(os.environ)
    env.update(
        QT_QPA_PLATFORM="offscreen",
        APPDATA=str(tmp_path / "roaming"),
        LOCALAPPDATA=str(tmp_path / "local"),
        XDG_CONFIG_HOME=str(tmp_path / "xdg-config"),
        XDG_CACHE_HOME=str(tmp_path / "xdg-cache"),
    )
    env.pop("PYTEST_ADDOPTS", None)
    done = subprocess.run(
        [sys.executable, "-c", QUIT_SCRIPT],
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
        cwd=tmp_path,
    )
    assert done.returncode == 0, done.stderr[-2000:]
    assert "event loop reached" in done.stdout
    written = sorted(p.relative_to(tmp_path).parts[0] for p in tmp_path.rglob("settings.json"))
    assert written in (["roaming"], ["xdg-config"])  # the close saved the settings in app data


# The engines and the order (Q11, Q17, S-order, DR-35 (c)).


def test_the_applications_engines_are_wholly_real(make_app, qtbot) -> None:
    application = make_app(cpu_settings())
    engines = application.window.context.engines
    assert isinstance(engines.photo_source, PhotoReader)
    assert isinstance(engines.video_source, FFmpegVideoSource)
    assert isinstance(engines.video_sink, FFmpegVideoSink)
    assert engines.cache is application.cache and isinstance(engines.cache, DeferredProxyCache)
    assert engines.select_backend is core.select_backend
    assert list(engines.methods) == ["c3", "ancuti2018"]
    exports = application.exports._engine
    assert isinstance(exports, ExportEngine) and exports._cache is application.cache
    for member in (engines.photo_source, engines.video_source, engines.video_sink, engines.cache):
        assert not type(member).__module__.startswith("clearwater.interfaces.stubs")
    wait_started(qtbot, application)
    assert isinstance(application.cache.opened(), DiskProxyCache)


def test_the_cleanup_ends_before_any_panel_or_job(make_app, qtbot, monkeypatch) -> None:
    events: list[str] = []
    real_clean = app_main.clean_leftovers

    def clean(settings: Settings, journal: Any) -> Any:
        events.append("cleanup")
        return real_clean(settings, journal)

    monkeypatch.setattr(app_main, "clean_leftovers", clean)
    for name in (
        "install_parameter_panels",
        "install_timeline",
        "install_export_panels",
        "install_settings_dialog",
    ):
        real = getattr(app_main, name)

        def spy(*args: Any, _name: str = name, _real: Any = real, **kwargs: Any) -> Any:
            events.append(_name)
            return _real(*args, **kwargs)

        monkeypatch.setattr(app_main, name, spy)
    real_run = QtJobRunner.run

    def run(self: QtJobRunner, *args: Any, **kwargs: Any) -> Any:
        events.append("job")
        return real_run(self, *args, **kwargs)

    monkeypatch.setattr(QtJobRunner, "run", run)
    application = make_app(cpu_settings())
    assert events[:5] == [
        "cleanup",
        "install_parameter_panels",
        "install_timeline",
        "install_export_panels",
        "install_settings_dialog",
    ]
    assert events[5:] == ["job", "job", "job"]  # the three start-up jobs, after the installs
    wait_started(qtbot, application)


def test_the_start_up_jobs_run_off_the_interface_thread(make_app, qtbot, monkeypatch) -> None:
    threads: dict[str, threading.Thread] = {}
    limits: list[int] = []
    real_open = DeferredProxyCache.open
    real_caps = FFmpegVideoSink.capabilities
    real_select = core.select_backend

    def opening(self: DeferredProxyCache, limit: int) -> str | None:
        threads["open"] = threading.current_thread()
        limits.append(limit)
        return real_open(self, limit)

    def capabilities(self: FFmpegVideoSink) -> Any:
        threads.setdefault("detect", threading.current_thread())
        return real_caps(self)

    def select(settings: Settings, height: int, width: int, method_id: str) -> Any:
        threads.setdefault("probe", threading.current_thread())
        return real_select(settings, height, width, method_id)

    monkeypatch.setattr(DeferredProxyCache, "open", opening)
    monkeypatch.setattr(FFmpegVideoSink, "capabilities", capabilities)
    monkeypatch.setattr(core, "select_backend", select)
    application = make_app(cpu_settings(cache_limit_bytes=7 * 10**9))
    wait_started(qtbot, application)
    assert set(threads) == {"open", "detect", "probe"} and limits == [7 * 10**9]
    assert all(t is not threading.main_thread() for t in threads.values())
    assert application.cache.limit_bytes() == 7 * 10**9  # the one settings read's limit
    assert application.catalog.capabilities()  # the first dialog opens on a known result


def test_the_device_reason_shows_before_a_file_is_open_and_follows_force_cpu(
    make_app, qtbot, monkeypatch
) -> None:
    """AD-9, question 5, S3: the verbatim reason; a settings change detects again."""

    def select(settings: Settings, height: int, width: int, method_id: str) -> Any:
        if settings.force_cpu:
            return NumpyBackend(), "CPU: forced"
        return NumpyBackend(), "CPU: no CUDA device"

    monkeypatch.setattr(core, "select_backend", select)
    application = make_app(cpu_settings(force_cpu=False))
    window = application.window
    wait_started(qtbot, application)
    assert window.device_label.text() == "Device: CPU: no CUDA device"
    window.session.set_settings(cpu_settings(force_cpu=True))
    qtbot.waitUntil(lambda: window.device_label.text() == "Device: CPU: forced", timeout=10000)


def test_a_failed_cache_open_is_shown_once_and_photos_still_work(
    make_app, qtbot, monkeypatch, sample, tmp_path
) -> None:
    """S1 condition 2: members refuse readably, the reason is shown once, photos export."""

    def refuse(folder: Path, limit: int = 0) -> DiskProxyCache:
        raise OSError("the cache volume is not mounted")

    monkeypatch.setattr(composition, "proxy_cache", refuse)
    out = tmp_path / "out"
    out.mkdir()
    application = make_app(cpu_settings(output_folder=out))
    wait_started(qtbot, application)
    warnings = [m for m in presenter(application).of("warning") if m.owner == OWNER_STARTUP]
    assert [m.text for m in warnings] == [
        "Videos cannot be analysed or exported in this session: the analysis cache could not be "
        "opened: the cache volume is not mounted."
    ]
    photo = sample("jpeg-gradient-srgb")
    open_source(qtbot, application, photo)
    job = application.exports.job(_photo_request(photo, application))
    result = job(_Progress())
    assert result.ok, result.failure
    open_source(qtbot, application, sample(CLIP))
    wait_analysis(qtbot, application, "failed")
    assert "the cache volume is not mounted" in application.window.session.analysis().message
    assert len([m for m in presenter(application).messages if m.owner == OWNER_STARTUP]) == 1


def test_no_start_up_callback_reaches_the_window_after_its_close(
    make_app, qtbot, monkeypatch
) -> None:
    """R1-5 (DR-44 (c)): a start-up job ending during or after the close delivers nothing.

    The cache's open outlives the shell's close wait (made 0.2 s here; 5 s in the program,
    against a first open of 16 s), then fails: its queued completion arrives while this event
    loop still runs. The device probe ends during the close, whose wait delivers it.
    """
    from clearwater.gui import shell

    opening, release = threading.Event(), threading.Event()

    def slow_failing_open(folder: Path, limit: int = 0) -> DiskProxyCache:
        opening.set()
        assert release.wait(30)
        raise OSError("the cache volume is not mounted")

    calls: list[str] = []
    for name in ("_on_cache_open", "_on_probe"):
        real = getattr(Application, name)

        def spy(self: Application, *args: Any, _name: str = name, _real: Any = real) -> Any:
            calls.append(_name)
            return _real(self, *args)

        monkeypatch.setattr(Application, name, spy)
    probe_gate = threading.Event()
    real_select = core.select_backend

    def held_select(settings: Settings, height: int, width: int, method_id: str) -> Any:
        assert probe_gate.wait(30)
        return real_select(settings, height, width, method_id)

    monkeypatch.setattr(composition, "proxy_cache", slow_failing_open)
    monkeypatch.setattr(core, "select_backend", held_select)
    monkeypatch.setattr(shell, "SHUTDOWN_TIMEOUT_S", 0.2)
    application = make_app(cpu_settings())
    assert opening.wait(30)
    threading.Timer(0.05, probe_gate.set).start()  # the probe ends inside the close's wait
    application.window.close()
    assert application.closed()
    release.set()
    qtbot.waitUntil(lambda: application.cache.wait_open(0), timeout=30000)
    qtbot.wait(300)  # the open's queued completion is delivered by this loop
    assert calls == []
    assert not [m for m in presenter(application).messages if m.owner == OWNER_STARTUP]


class _Progress:
    """A minimal IF-8 progress for a job run on the test's thread."""

    def __init__(self) -> None:
        self.reports: list[tuple[int, int | None, str]] = []
        self.cancel = False

    def report(self, done: int, total: int | None, message: str) -> None:
        self.reports.append((done, total, message))

    def cancelled(self) -> bool:
        return self.cancel


def _photo_request(path: Path, application: Application) -> Any:
    from clearwater.jobs.export_seam import ExportRequest

    session = application.window.session
    return ExportRequest(path, "photo", session.parameters(), session.settings())


# DR-85 (ruling Q21): the start-up sibling of DR-77.


@pytest.mark.xfail(
    strict=True,
    raises=OverflowError,
    reason="DR-85: OverflowError escapes load_settings until WP4.3a's fix is on main",
)
def test_a_settings_file_that_fails_to_decode_is_set_aside_and_start_up_goes_on(
    make_app, qtbot, tmp_path
) -> None:
    config = app_data(tmp_path).config_dir
    save_settings(config, cpu_settings(last_parameters=new_parameter_set("c3", {})))
    path = config / "settings.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["last_parameters"]["created"] = "0001-01-01T00:00:00+01:00"
    path.write_text(json.dumps(data), encoding="utf-8")
    application = make_app()
    assert application.window.isVisible()
    assert not path.exists()
    assert any(p.name.startswith("settings.json.bad-") for p in config.iterdir())
    assert application.window.session.settings() == Settings()
    wait_started(qtbot, application)


# Nothing in start-up writes outside app data.


def test_start_up_and_close_write_only_app_data(make_app, qtbot, tmp_path) -> None:
    where = tmp_path / "home"
    application = make_app(cpu_settings(), where=where)
    wait_started(qtbot, application)
    application.window.close()
    roots = {p.relative_to(where).parts[0] for p in where.rglob("*")}
    assert roots <= {"config", "cache"}
    assert sorted(p.name for p in (where / "config").iterdir()) == [
        "logs",
        "presets",
        "settings.json",
    ]
