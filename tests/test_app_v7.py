"""WP4.3 task 12: V7 (D66, G9) on the running shell with the real engines (question 10 as ruled).

"UI responds within 100 ms during analysis, export and batch processing." The probe is WP3.16's:
a 10 ms ``QTimer`` on the interface thread; each scenario's figures are the longest gap between
two ticks, the gaps' p99 and the tick count. The six scenarios of question 10:

- (a) a clip's analysis while the timeline updates (F-2: the adapter's own pts list);
- (b) scrubbing the stored proxies during that analysis;
- (c) a File > Export of the clip;
- (d) a batch of 300 small synthetic stills under ``tmp_path`` (DR-50);
- (e) a 1:1 4K preview render (the FFT route on the GPU) during (c);
- (f) start-up, here with a slow cache open (S1 condition 5: a stub open that sleeps past
  100 ms; the first analysis waits for it on its worker while the interface responds).

These are the GATE forms, on the WP2.3 fixture clip (``gui`` and ``slow``: wall-clock bounds,
serial leg only). The figures of record come from the EXCLUSIVE window on GX011627, run by an
uncommitted driver in the evidence folder that imports the scenario functions here (ruling S7);
no committed test reads the footage folder.
"""

# ``make_app`` is imported from test_app_startup and used as a parameter.
# ruff: noqa: F401, F811

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from PySide6.QtCore import QElapsedTimer, QTimer

import gui_support
from clearwater.app import analysis_adapter, composition
from clearwater.app.main import Application
from clearwater.cache import DiskProxyCache
from clearwater.gui.batch_panel import BatchPanel, ItemState
from clearwater.gui.export_panel import ExportPanel
from clearwater.gui.timeline import TimelinePanel
from clearwater.interfaces import ColorDescription, Image, PhotoMetadata
from test_app_startup import CLIP, cpu_settings, make_app, open_source, wait_started

pytestmark = [pytest.mark.gui, pytest.mark.slow, pytest.mark.usefixtures("ffmpeg_tools")]

V7_BOUND_MS = 100.0
"""D66: the interface responds within 100 ms."""

PROBE_MS = 10
"""WP3.16's probe interval."""


@dataclass(frozen=True)
class Figures:
    """One scenario's V7 figures.

    Attributes:
        scenario: The scenario's letter and name.
        longest_ms: The longest gap between two probe ticks.
        p99_ms: The 99th percentile of the gaps.
        ticks: How many ticks the probe saw.
    """

    scenario: str
    longest_ms: float
    p99_ms: float
    ticks: int
    witness: dict[str, int] = field(default_factory=dict)

    def line(self) -> str:
        """The report line, with the workload's witness counts (R1-12)."""
        return (
            f"{self.scenario}: longest {self.longest_ms:.1f} ms, p99 {self.p99_ms:.1f} ms, "
            f"{self.ticks} ticks, witness {self.witness}"
        )


class GapProbe:
    """WP3.16's 10 ms interface-thread probe, keeping every gap."""

    def __init__(self) -> None:
        self._clock = QElapsedTimer()
        self._timer = QTimer()
        self._timer.setInterval(PROBE_MS)
        self._timer.timeout.connect(self._tick)
        self._gaps: list[int] = []
        self._last = 0

    def start(self) -> None:
        self._clock.start()
        self._last = 0
        self._timer.start()

    def _tick(self) -> None:
        now = self._clock.elapsed()
        self._gaps.append(now - self._last)
        self._last = now

    def stop(self, scenario: str) -> Figures:
        self._timer.stop()
        self._tick()
        gaps = np.asarray(self._gaps, dtype=np.float64)
        return Figures(scenario, float(gaps.max()), float(np.quantile(gaps, 0.99)), len(gaps))


def measured(qtbot: Any, scenario: str, start: Callable[[], None], until: Callable[[], bool],
             timeout_ms: int = 600000) -> Figures:  # fmt: skip
    """Probe from just before ``start`` until ``until()``; return the scenario's figures."""
    probe = GapProbe()
    probe.start()
    QTimer.singleShot(30, start)
    try:
        qtbot.wait(60)
        qtbot.waitUntil(until, timeout=timeout_ms)
    finally:
        figures = probe.stop(scenario)
    return figures


def _panel(application: Application, kind: type) -> Any:
    (found,) = application.window.findChildren(kind)
    return found


def scenario_a_analysis(qtbot: Any, application: Application, clip: Path) -> Figures:
    """(a) The clip's analysis while the timeline updates (F-2)."""
    window = application.window
    return measured(
        qtbot,
        "(a) analysis",
        lambda: window.open_path(clip),
        lambda: window.session.analysis().phase == "complete",
    )


def scenario_b_scrubbing(qtbot: Any, application: Application, clip: Path) -> Figures:
    """(b) Scrubbing the stored proxies while the analysis runs."""
    window = application.window
    timeline = _panel(application, TimelinePanel)
    slider = timeline.slider()
    state = {"value": 0, "down": False}
    moves = {"during_analysis": 0}

    def scrub() -> None:
        if window.session.analysis().phase != "running":
            return
        top = slider.maximum()
        if top <= 0:
            return
        if not state["down"]:
            slider.setSliderDown(True)
            state["down"] = True
        state["value"] = (state["value"] + 3) % (top + 1)
        slider.setValue(state["value"])
        moves["during_analysis"] += 1

    mover = QTimer()
    mover.setInterval(40)
    mover.timeout.connect(scrub)

    def start() -> None:
        window.open_path(clip)
        mover.start()

    try:
        figures = measured(
            qtbot, "(b) scrubbing", start, lambda: window.session.analysis().phase == "complete"
        )
    finally:
        mover.stop()
        slider.setSliderDown(False)
    figures.witness.update(moves)
    return figures


def scenario_c_export(qtbot: Any, application: Application) -> Figures:
    """(c) File > Export of the open, analysed clip."""
    window = application.window
    export = _panel(application, ExportPanel)
    started = {"seen": False}

    def running() -> bool:
        started["seen"] = started["seen"] or export.is_running()
        return started["seen"] and not export.is_running()

    return measured(qtbot, "(c) export", window.shell_actions.export.trigger, running)


def small_stills(folder: Path, count: int = 300) -> list[Path]:
    """``count`` small synthetic stills (8-bit PNGs, 96 x 64) for the batch scenario (DR-50)."""
    rng = np.random.default_rng(50)
    color = ColorDescription("bt709", "srgb", "identity", "full", 8, False, None)
    writer = composition.photo_writer()
    paths = []
    for index in range(count):
        pixels = rng.uniform(0.1, 0.9, (64, 96, 3)).astype(np.float32)
        path = folder / f"still_{index:03d}.png"
        writer.write(Image(pixels, "cpu", color, True), PhotoMetadata("png", None, 1), path,
                     bit_depth=8, provenance=None)  # fmt: skip
        paths.append(path)
    return paths


def scenario_d_batch(qtbot: Any, application: Application, stills: list[Path]) -> Figures:
    """(d) A batch of a few hundred stills (DR-50's queue)."""
    batch = _panel(application, BatchPanel)
    batch.add_paths(stills)
    started = {"seen": False}

    def ended() -> bool:
        started["seen"] = started["seen"] or batch.is_running()
        return started["seen"] and not batch.is_running()

    return measured(qtbot, f"(d) batch of {len(stills)}", batch.start, ended)


def scenario_e_full_render_during_export(
    qtbot: Any, application: Application, photo_4k: Path
) -> Figures:
    """(e) A 1:1 render of a 4K photo while the open clip's export runs.

    The fixture clip's export ends before a 1:1 4K render does, so the overlap is arranged
    (R1-12): the export job starts its encode once the 1:1 view is asked for, and returns only
    after a 1:1 render of the photo has arrived; the witness counts those renders.
    """
    window = application.window
    export = _panel(application, ExportPanel)
    overlap = {"renders_at_1_during_export": 0}
    asked, rendered_at_1 = threading.Event(), threading.Event()
    engine = application.exports._engine
    real_job = engine.job

    def held_job(request: Any) -> Any:
        inner = real_job(request)

        def run(progress: Any) -> Any:
            assert asked.wait(120), "the 1:1 view was never asked for"
            result = inner(progress)  # the encode runs while the 1:1 render does
            assert rendered_at_1.wait(120), "no 1:1 render arrived during the export"
            return result

        return run

    def on_rendered(result: object) -> None:
        source = window.session.source()
        if asked.is_set() and source is not None and source.path == photo_4k:
            if export.is_running():
                overlap["renders_at_1_during_export"] += 1
            rendered_at_1.set()

    engine.job = held_job  # type: ignore[method-assign]
    window.controller.rendered.connect(on_rendered)

    def start() -> None:
        window.shell_actions.export.trigger()
        window.open_path(photo_4k)

    def done() -> bool:
        source = window.session.source()
        if source is None or source.path != photo_4k:
            return False
        if window.preview_widget.is_fit():
            window.view_actions["one_to_one"].trigger()
            asked.set()
            return False
        return (
            not export.is_running()
            and window.controller.idle()
            and window.preview_widget.shown_factor() == 1
        )

    try:
        figures = measured(qtbot, "(e) 1:1 4K render during an export", start, done)
    finally:
        window.controller.rendered.disconnect(on_rendered)
        engine.job = real_job  # type: ignore[method-assign]
        asked.set()
        rendered_at_1.set()
    figures.witness.update(overlap)
    return figures


def photo_4k(folder: Path) -> Path:
    """A 2160 x 3840 16-bit PNG (the FFT route's short side) under ``folder``."""
    y, x = np.mgrid[0:2160, 0:3840].astype(np.float32)
    pixels = np.stack(
        [
            0.3 + 0.2 * np.sin(x / 400),
            0.5 + 0.2 * np.cos(y / 300),
            0.6 + 0.1 * np.sin((x + y) / 500),
        ],
        axis=-1,
    ).astype(np.float32)
    path = folder / "uhd.png"
    color = ColorDescription("bt709", "srgb", "identity", "full", 16, False, None)
    composition.photo_writer().write(
        Image(pixels, "cpu", color, True), PhotoMetadata("png", None, 1), path,
        bit_depth=16, provenance=None,
    )  # fmt: skip
    return path


def scenario_f_start_up(
    qtbot: Any, build: Callable[[], Application], clip: Path
) -> tuple[Figures, Application]:
    """(f) Start-up: build the application, open a clip at once, wait for its analysis."""
    box: dict[str, Application] = {}

    def start() -> None:
        application = build()
        box["app"] = application
        application.window.open_path(clip)

    def done() -> bool:
        application = box.get("app")
        return application is not None and application.window.session.analysis().phase == (
            "complete"
        )

    figures = measured(qtbot, "(f) start-up", start, done)
    return figures, box["app"]


# The gate forms on the fixture clip.


def _within(figures: Figures, *witnessed: str) -> None:
    """Assert the bound, and that each named witness count is positive (R1-12)."""
    print(figures.line())
    assert figures.longest_ms <= V7_BOUND_MS, figures.line()
    for name in witnessed:
        assert figures.witness.get(name, 0) > 0, f"the workload was not witnessed: {figures.line()}"


def test_v7_a_b_analysis_and_scrubbing(make_app, qtbot, sample, tmp_path) -> None:
    application = make_app(cpu_settings(), where=tmp_path / "a")
    wait_started(qtbot, application)
    _within(scenario_a_analysis(qtbot, application, sample(CLIP)))
    application.window.close()
    second = make_app(cpu_settings(), where=tmp_path / "b")  # a cold cache: the decode runs
    wait_started(qtbot, second)
    _within(scenario_b_scrubbing(qtbot, second, sample(CLIP)), "during_analysis")


def test_v7_c_e_export_and_a_full_render_during_it(make_app, qtbot, sample, tmp_path) -> None:
    out = tmp_path / "out"
    out.mkdir()
    application = make_app(cpu_settings(output_folder=out))
    wait_started(qtbot, application)
    open_source(qtbot, application, sample(CLIP))
    qtbot.waitUntil(
        lambda: application.window.session.analysis().phase == "complete", timeout=120000
    )
    _within(scenario_c_export(qtbot, application))
    for path in out.iterdir():
        path.unlink()
    open_source(qtbot, application, sample(CLIP))
    qtbot.waitUntil(
        lambda: application.window.session.analysis().phase == "complete", timeout=120000
    )
    _within(
        scenario_e_full_render_during_export(qtbot, application, photo_4k(tmp_path)),
        "renders_at_1_during_export",
    )


def test_v7_d_a_batch_of_300_stills(make_app, qtbot, tmp_path) -> None:
    folder, out = tmp_path / "stills", tmp_path / "out"
    folder.mkdir()
    out.mkdir()
    stills = small_stills(folder)
    application = make_app(cpu_settings(output_folder=out))
    wait_started(qtbot, application)
    _within(scenario_d_batch(qtbot, application, stills))
    batch = _panel(application, BatchPanel)
    assert [item.state for item in batch.items()] == [ItemState.DONE] * len(stills)


def test_v7_f_start_up_with_a_slow_cache_open(make_app, qtbot, sample, monkeypatch) -> None:
    """S1 condition 5: the open sleeps past 100 ms; the analysis waits on its worker."""
    real = composition.proxy_cache
    opened: list[float] = []

    def slow(folder: Path, limit: int = 0) -> DiskProxyCache:
        time.sleep(1.5)
        opened.append(time.monotonic())
        return real(folder, limit)

    waits: list[tuple[bool, float]] = []
    real_wait = analysis_adapter.wait_for_cache

    def witnessed_wait(cache: Any, progress: Any) -> bool:
        pending = not cache.wait_open(0)
        ended = real_wait(cache, progress)
        waits.append((pending, time.monotonic()))
        return ended

    monkeypatch.setattr(composition, "proxy_cache", slow)
    monkeypatch.setattr(analysis_adapter, "wait_for_cache", witnessed_wait)
    figures, application = scenario_f_start_up(
        qtbot, lambda: make_app(cpu_settings()), sample(CLIP)
    )
    figures.witness["analysis_waited_for_the_open"] = sum(
        1 for pending, returned in waits if pending and opened and returned >= opened[0]
    )
    _within(figures, "analysis_waited_for_the_open")
    assert opened, "the slow open did not run"
    wait_started(qtbot, application)
