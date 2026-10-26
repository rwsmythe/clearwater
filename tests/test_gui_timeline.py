"""WP3.18 timeline and analysis: G4, G5, D70, D72, D108, V18, AD-15, DR-44 (a), V7.

Every test builds a real ``MainWindow`` on stub engines with several frames, installs the
timeline panel and drives it through the session and the slider. A scripted ``ClipAnalysis``
(blocking on events, publishing statistics that identify the pts and parameters they are for)
stands in for the analysis where a test needs control; the stub analysis is used for V7 and
the default install. The test method renders the statistics it is given, so what the preview
shows tells which statistics were supplied. Planted wrong panels fail the same scenarios by name.
"""

# The shared fixture ``make_window`` is imported from gui_support and used as a parameter.
# ruff: noqa: F401, F811

from __future__ import annotations

import dataclasses
import threading
import time
from collections import defaultdict
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from PySide6.QtCore import QElapsedTimer, QTimer
from PySide6.QtWidgets import QPushButton

import gui_support
from clearwater.config import new_parameter_set
from clearwater.gui import Area, FrameOutcome
from clearwater.gui.analysis_service import stub_analysis_factory
from clearwater.gui.engines import stub_probe
from clearwater.gui.shell import NEEDS_ANALYSIS_REASON, MainWindow
from clearwater.gui.timeline import (
    LABEL_UPDATING,
    OWNER_ANALYSIS,
    OWNER_TIMELINE,
    TimelinePanel,
    install_timeline,
)
from clearwater.interfaces import Frame, Image, Parameter, Statistics
from clearwater.interfaces.stubs import StubProgress
from gui_support import (
    META,
    ONE_STAGE,
    VIDEO_TAGS,
    busy_numpy,
    make_window,
    open_and_wait,
    photo_engines,
    presenter_of,
    video_engines,
)

pytestmark = pytest.mark.gui

PTS = (0, 3003, 6006, 9009, 12012)
VFR = (0, 1001, 3003, 4004, 7007)
FLAT = 0.2
BASE = Fraction(1, 90000)
V7_BOUND_MS = 100


def flat_frame(ticks: int, value: float = FLAT) -> Frame:
    """A small frame of one grey level at ``ticks`` on the 1/90000 time base."""
    pixels = np.full((12, 16, 3), value, np.float32)
    return Frame(pixels, "cpu", VIDEO_TAGS, True, ticks * BASE, ticks, BASE, 0)


def probe_for(count: int) -> Callable[[Path], Any]:
    """A probe whose ``nb_frames`` is exact."""

    def probe(path: Path) -> Any:
        base = stub_probe(path)
        return dataclasses.replace(base, video=dataclasses.replace(base.video, nb_frames=count))

    return probe


def smooth(pts: int, level: float = 0.5) -> float:
    """The smoothed statistic the scripted analysis publishes for a pts and a ``level``."""
    return 0.3 + 0.4 * level + pts * 1e-7


class StatMethod:
    """One stage; ``render`` fills the image with the stage's ``mean`` it was given."""

    label = "Stat"

    def __init__(self, method_id: str = "statm", busy: Callable[[], None] | None = None) -> None:
        self.id = method_id
        self.parameters = (
            Parameter("level", "float", 0.5, 0.0, 1.0, None, "basic", "Level", "", 0.5),
        )
        self.stages = ONE_STAGE
        self.busy = busy
        self.rendered: list[float] = []
        self.lock = threading.Lock()

    def analyze(
        self, stage: str, image: Image, params: Mapping[str, Any], earlier: Mapping[str, Statistics]
    ) -> Statistics:
        if self.busy is not None:
            self.busy()
        return {"mean": np.asarray(image.pixels).mean(axis=(0, 1))}

    def render(
        self, image: Image, params: Mapping[str, Any], statistics: Mapping[str, Statistics]
    ) -> Image:
        value = float(np.asarray(statistics["only"]["mean"])[0])
        with self.lock:
            self.rendered.append(value)
        out = np.full_like(np.asarray(image.pixels), value, dtype=np.float32)
        return Image(out, image.device, image.color, image.orientation_applied)

    def closed_form(
        self,
        stage: str,
        params: Mapping[str, Any],
        earlier: Mapping[str, Statistics],
        measured: Statistics,
    ) -> Statistics | None:
        return None


class ScriptedAnalysis:
    """A ``ClipAnalysis`` the test controls: gated runs, recorded calls, identifying statistics.

    Run ``k`` waits for ``release(k)`` when ``k`` is in ``gated``; a run that is cancelled
    returns early (unless ``ignore_cancel``) and publishes nothing. A run that completes
    publishes the parameters it ends under: its own, or the ones ``retarget`` accepted.
    """

    def __init__(
        self,
        method_id: str,
        ticks: Sequence[int],
        stored: Sequence[int] | None = None,
        *,
        gated: Sequence[int] = (0,),
        absorb: bool = False,
        ignore_cancel: bool = False,
        raise_on_cancel: bool = False,
        fail_runs: Sequence[int] = (),
        proxy_delay: float = 0.0,
        fail_proxy: Sequence[int] = (),
    ) -> None:
        self.method_id = method_id
        self.ticks = tuple(ticks)
        self.stored = tuple(stored if stored is not None else ticks)
        self.gated = set(gated)
        self.absorb = absorb
        self.ignore_cancel = ignore_cancel
        self.raise_on_cancel = raise_on_cancel
        self.fail_runs = set(fail_runs)
        self.proxy_delay = proxy_delay
        self.fail_proxy = set(fail_proxy)
        self.lock = threading.Lock()
        self.gates: dict[int, threading.Event] = {}
        self.runs: list[tuple[Any, int | None]] = []
        self.retargets: list[Any] = []
        self.cancelled_runs: list[int] = []
        self.published: Any = None
        self.target: Any = None
        self.threads: dict[str, set[threading.Thread]] = defaultdict(set)
        self.statistics_gate: threading.Event | None = None
        self.statistics_waiting = threading.Event()
        self.active_proxy = 0
        self.max_proxy = 0

    def gate(self, index: int) -> threading.Event:
        with self.lock:
            return self.gates.setdefault(index, threading.Event())

    def release(self, index: int = 0) -> None:
        self.gate(index).set()

    def run(self, parameters: Any, progress: Any, *, focus_pts: int | None = None) -> None:
        with self.lock:
            index = len(self.runs)
            self.runs.append((parameters, focus_pts))
            self.threads["run"].add(threading.current_thread())
            self.published = None
            self.target = parameters
        progress.report(1, len(self.ticks), "scripted")
        if index in self.gated:
            gate = self.gate(index)
            while not gate.wait(0.005):
                if progress.cancelled() and not self.ignore_cancel:
                    self.cancelled_runs.append(index)
                    if self.raise_on_cancel:  # an analysis that fails while it is stopping
                        raise RuntimeError("scripted failure while cancelling")
                    return
        if progress.cancelled() and not self.ignore_cancel:
            self.cancelled_runs.append(index)
            return
        if index in self.fail_runs:
            raise RuntimeError("scripted failure")
        with self.lock:
            self.published = self.target

    def retarget(self, parameters: Any, *, focus_pts: int | None = None) -> bool:
        self.threads["retarget"].add(threading.current_thread())
        self.retargets.append(parameters)
        if self.absorb:
            self.target = parameters
        return self.absorb

    def pts(self) -> tuple[int, ...]:
        self.threads["pts"].add(threading.current_thread())
        return self.stored

    def proxy(self, pts_ticks: int) -> Any:
        self.threads["proxy"].add(threading.current_thread())
        with self.lock:
            self.active_proxy += 1
            self.max_proxy = max(self.max_proxy, self.active_proxy)
        try:
            if self.proxy_delay:
                time.sleep(self.proxy_delay)
            if pts_ticks in self.fail_proxy or pts_ticks not in self.stored:
                raise KeyError(pts_ticks)
            return np.full((12, 16, 3), pts_ticks % 251, np.uint8)
        finally:
            with self.lock:
                self.active_proxy -= 1

    def statistics(self, pts_ticks: int) -> Any:
        self.threads["statistics"].add(threading.current_thread())
        published = self.published  # taken before any wait, as a slow real reader would
        gate = self.statistics_gate
        if gate is not None:
            self.statistics_waiting.set()
            gate.wait(5)
        if published is None or pts_ticks not in self.ticks:
            return None
        level = float(published.parameters.get("level", 0.5))
        return {"only": {"mean": np.full(3, smooth(pts_ticks, level))}}


class FlakySource:
    """Wraps a video source; a decode that starts at one of ``fail_ticks`` raises.

    A decode that starts at one of ``hold_ticks`` first waits for ``hold`` (``holding`` is set
    while it waits), so a test can change the parameters while that decode is pending.
    """

    def __init__(
        self, inner: Any, fail_ticks: Sequence[int], hold_ticks: Sequence[int] = ()
    ) -> None:
        self.inner = inner
        self.fail_starts = {Fraction(t, 90000) for t in fail_ticks}
        self.hold_starts = {Fraction(t, 90000) for t in hold_ticks}
        self.hold = threading.Event()
        self.holding = threading.Event()

    def probe(self, path: Path) -> Any:
        return self.inner.probe(path)

    def frames(self, probe: Any, *, hw_decode: bool, start_s: Any = None, end_s: Any = None) -> Any:
        if start_s is not None and start_s in self.hold_starts:
            self.holding.set()
            self.hold.wait(5)
        if start_s is not None and start_s in self.fail_starts:
            raise OSError("scripted disk read error")
        return self.inner.frames(probe, hw_decode=hw_decode, start_s=start_s, end_s=end_s)


@dataclass
class Env:
    """One built window with the timeline installed and its spies."""

    qtbot: Any
    tmp_path: Path
    window: MainWindow
    panel: TimelinePanel
    methods: dict[str, StatMethod]
    built: list[ScriptedAnalysis]
    source: Any = None
    positions: list[tuple[int, Any]] = field(default_factory=list)
    stat_calls: list[Any] = field(default_factory=list)
    shown: list[Any] = field(default_factory=list)
    display: list[str] = field(default_factory=list)
    states: list[Any] = field(default_factory=list)

    @property
    def method(self) -> StatMethod:
        return self.methods["statm"]

    @property
    def analysis(self) -> ScriptedAnalysis:
        return self.built[-1]

    @property
    def session(self) -> Any:
        return self.window.session

    @property
    def phases(self) -> list[str]:
        return [state.phase for state in self.states]

    def open(self, name: str = "clip.mp4") -> Path:
        path = self.tmp_path / name
        path.write_bytes(b"clip")
        open_and_wait(self.qtbot, self.window, path)
        return path

    def wait(self, condition: Callable[[], bool], ms: int = 4000) -> None:
        try:
            self.qtbot.waitUntil(lambda: bool(condition()), timeout=ms)
        except Exception as exc:
            raise AssertionError(f"timed out waiting for {condition}") from exc

    def phase_is(self, phase: str, ms: int = 4000) -> None:
        self.wait(lambda: self.session.analysis().phase == phase, ms)

    def rendered_is(self, value: float, method: str = "statm", ms: int = 4000) -> None:
        rendered = self.methods[method].rendered
        self.wait(lambda: bool(rendered) and abs(rendered[-1] - value) < 1e-5, ms)

    def slider(self) -> Any:
        return self.panel.slider()

    def button(self, name: str) -> QPushButton:
        button = self.panel.findChild(QPushButton, name)
        assert button is not None
        return button

    def set_level(self, level: float, method: str = "statm") -> None:
        self.session.set_parameters(new_parameter_set(method, {"level": level}))

    def statistics_mean(self) -> float:
        stats = self.session.statistics()
        assert stats is not None
        return float(np.asarray(stats["only"]["mean"])[0])


@pytest.fixture
def make_env(qtbot: Any, make_window: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    """Build an :class:`Env`; options configure the analysis, the frames and the panel class."""

    def build(
        *,
        ticks: Sequence[int] = PTS,
        stored: Sequence[int] | None = None,
        method_ids: Sequence[str] = ("statm",),
        methods: dict[str, StatMethod] | None = None,
        panel_class: type[TimelinePanel] | None = None,
        factory: Any = None,
        fail_decode: Sequence[int] = (),
        hold_decode: Sequence[int] = (),
        photos: dict[Path, Any] | None = None,
        **analysis_options: Any,
    ) -> Env:
        all_methods = methods or {mid: StatMethod(mid) for mid in method_ids}
        frames = [flat_frame(t) for t in ticks]
        engines = video_engines(
            frames, video_probe=probe_for(len(ticks)), methods=all_methods, photos=photos
        )
        if fail_decode or hold_decode:
            engines = dataclasses.replace(
                engines, video_source=FlakySource(engines.video_source, fail_decode, hold_decode)
            )
        window = make_window(engines)
        window.shell_actions.export.set_unavailable(None)  # as WP3.19 does when it connects
        built: list[ScriptedAnalysis] = []

        def scripted(source: Any, method: Any, engines: Any) -> ScriptedAnalysis:
            analysis = ScriptedAnalysis(method.id, ticks, stored, **analysis_options)
            built.append(analysis)
            return analysis

        use = factory or scripted
        if panel_class is None:
            install_timeline(window, use)
            panel = window.findChild(TimelinePanel)
        else:
            cls = panel_class
            window.attach(Area.TIMELINE, lambda ctx: cls(ctx, use), title="Timeline")
            panel = window.findChild(cls)
        assert panel is not None
        env = Env(qtbot, tmp_path, window, panel, all_methods, built, engines.video_source)
        session = window.session
        original_position = session.set_position
        original_statistics = session.set_statistics
        original_show = window.controller.show_proxy

        def spy_position(pts: int, *, statistics: Any = None) -> None:
            env.positions.append((pts, statistics))
            original_position(pts, statistics=statistics)

        def spy_statistics(statistics: Any) -> None:
            env.stat_calls.append(statistics)
            original_statistics(statistics)

        def spy_show(proxy: Any, corrected: Any = None) -> None:
            env.shown.append(np.array(proxy))
            original_show(proxy, corrected)

        widget = window.preview_widget
        original_proxy = widget.set_proxy
        original_result = widget.set_result

        def spy_set_proxy(before: Any, after: Any) -> None:
            env.display.append("proxy")
            original_proxy(before, after)

        def spy_set_result(before: Any, after: Any, k: int) -> None:
            env.display.append("result")
            original_result(before, after, k)

        monkeypatch.setattr(widget, "set_proxy", spy_set_proxy)
        monkeypatch.setattr(widget, "set_result", spy_set_result)
        monkeypatch.setattr(session, "set_position", spy_position)
        monkeypatch.setattr(session, "set_statistics", spy_statistics)
        monkeypatch.setattr(window.controller, "show_proxy", spy_show)
        session.analysis_changed.connect(env.states.append)
        return env

    return build


def drag_to(env: Env, index: int) -> None:
    """Press the slider if it is not down, then move it to ``index``."""
    slider = env.slider()
    if not slider.isSliderDown():
        slider.setSliderDown(True)
    slider.setValue(index)


def release(env: Env) -> None:
    """Release the slider."""
    env.slider().setSliderDown(False)


def complete(env: Env, *, index: int = 0) -> None:
    """Open the clip and let the (gated) analysis finish."""
    env.open()
    env.wait(lambda: len(env.analysis.runs) > index)
    env.analysis.release(index)
    env.phase_is("complete")
    env.wait(lambda: env.slider().isEnabled() and env.slider().maximum() == len(PTS) - 1)
    # the switch to the smoothed statistics (V18) is a commit of the open frame: let it land
    env.wait(lambda: any(p == 0 for p, _ in env.positions) and env.window.jobs.active() == 0)
    env.wait(lambda: env.session.current_image().pts_ticks == 0)
    env.qtbot.wait(100)


# Scenarios shared by the real tests and the planted ones.


def scenario_switch(env: Env, ms: int = 4000) -> None:
    """V18: provisional first, then the smoothed statistics after the analysis completes."""
    env.open()
    env.rendered_is(FLAT, ms=ms)  # a corrected frame is shown before the analysis completes
    assert env.session.analysis().phase == "running"
    assert env.session.statistics() is None
    env.analysis.release(0)
    env.phase_is("complete", ms)
    env.rendered_is(smooth(0), ms=ms)  # and it updates to the smoothed statistics


def scenario_decode_failure(env: Env, ms: int = 4000) -> None:
    """DR-44 (a): after a failed decode the last shown frame's statistics are restored."""
    complete(env)
    drag_to(env, 1)
    release(env)
    env.wait(lambda: env.session.current_image().pts_ticks == PTS[1], ms)
    env.rendered_is(smooth(PTS[1]), ms=ms)
    env.slider().setValue(2)  # the decode of PTS[2] fails
    env.wait(
        lambda: any(m.owner == "shell.frame" for m in presenter_of(env.window).of("error")), ms
    )

    def statistics_restored_to_the_last_shown_frame() -> bool:
        stats = env.session.statistics()
        return stats is not None and env.statistics_mean() == pytest.approx(smooth(PTS[1]))

    # asserted before the slider's rollback, so a panel that keeps the requested frame's
    # statistics fails on them, by this condition, and not on the slider
    env.wait(statistics_restored_to_the_last_shown_frame, ms)
    env.wait(lambda: env.slider().value() == 1, ms)
    assert env.session.current_image().pts_ticks == PTS[1]


def scenario_run_thread(env: Env, ms: int = 4000) -> None:
    """Nothing heavy on the interface thread: run, proxy and statistics run on workers."""
    main = threading.main_thread()
    env.open()
    env.wait(lambda: len(env.analysis.runs) > 0, ms)
    # asserted before anything waits for the completion, so a run on the interface thread
    # fails here, by this message, and not as a timeout further on
    assert main not in env.analysis.threads["run"], "run ran on the interface thread"
    env.analysis.release(0)
    env.phase_is("complete", ms)
    env.wait(lambda: env.slider().maximum() == len(PTS) - 1, ms)
    drag_to(env, 2)
    env.wait(lambda: bool(env.shown), ms)
    release(env)
    env.wait(lambda: any(p == PTS[2] for p, _ in env.positions), ms)
    for member in ("run", "proxy", "statistics"):
        assert env.analysis.threads[member], member
        assert main not in env.analysis.threads[member], f"{member} ran on the interface thread"


def scenario_drag(env: Env, ms: int = 4000) -> None:
    """D72: while dragging, proxies are shown and the position is never set."""
    complete(env)
    env.positions.clear()
    env.shown.clear()
    drag_to(env, 2)
    drag_to(env, 3)

    def proxy_shown() -> bool:
        return any(np.array_equal(s, np.full((12, 16, 3), PTS[3] % 251)) for s in env.shown)

    # whichever comes first: a position set during the drag is the failure, named as such, and
    # not a timeout waiting for a proxy that a planted panel never requests
    env.wait(lambda: bool(env.positions) or proxy_shown(), ms)
    assert env.positions == [], "set_position was called during the drag"
    env.wait(proxy_shown, ms)
    assert env.positions == []
    release(env)
    env.wait(lambda: any(p == PTS[3] for p, _ in env.positions), ms)


class NoSwitchPanel(TimelinePanel):
    """Planted: no switch to the smoothed statistics when the analysis completes."""

    def _switch(self) -> None:
        return


class KeepRequestedStatisticsPanel(TimelinePanel):
    """Planted: after a failed decode the requested pts's statistics stay supplied."""

    def _on_frame_decoded(self, outcome: object) -> None:
        if isinstance(outcome, FrameOutcome) and outcome.pts is None:
            return
        super()._on_frame_decoded(outcome)


class InlineRunPanel(TimelinePanel):
    """Planted: the analysis runs on the interface thread."""

    def _start_run(self, label: str) -> bool:
        assert self._analysis is not None
        self._analysis.run(self._session.parameters(), StubProgress(), focus_pts=None)
        return True


class DragSetsPositionPanel(TimelinePanel):
    """Planted: every slider value, also while dragging, sets the position."""

    def _on_slider_value(self, index: int) -> None:
        if 0 <= index < len(self._pts):
            self._request("commit", self._pts[index])


# V18, G5, D70.


def test_a_corrected_frame_is_shown_before_the_analysis_completes_and_then_updates(
    make_env,
) -> None:
    scenario_switch(make_env(gated=(0,)))


def test_planted_no_switch_after_completion_fails(make_env) -> None:
    env = make_env(panel_class=NoSwitchPanel)
    with pytest.raises(AssertionError):
        scenario_switch(env, ms=700)


def test_progress_reaches_the_session_and_export_names_it(make_env) -> None:
    env = make_env()
    env.open()
    env.wait(lambda: env.session.analysis().done == 1)
    state = env.session.analysis()
    assert (state.phase, state.done, state.total) == ("running", 1, len(PTS))
    reason = env.window.shell_actions.export.unavailable_reason()
    assert reason is not None and "1/5" in reason
    assert env.button("timeline.cancel").isEnabled()
    assert not env.button("timeline.analyse").isEnabled()


def test_cancel_gives_cancelled_drops_statistics_and_analyse_restarts(make_env) -> None:
    env = make_env(gated=(0,))
    env.open()
    env.wait(lambda: env.session.analysis().done == 1)
    env.button("timeline.cancel").click()
    env.phase_is("cancelled")
    assert env.analysis.cancelled_runs == [0]
    assert env.window.shell_actions.export.unavailable_reason() == NEEDS_ANALYSIS_REASON
    assert env.session.statistics() is None
    assert env.session.source() is not None  # the clip stays open (question 3)
    assert not env.button("timeline.cancel").isEnabled()
    assert env.button("timeline.analyse").isEnabled()
    env.button("timeline.analyse").click()  # run 1 is not gated
    env.phase_is("complete")
    assert len(env.analysis.runs) == 2
    assert env.window.shell_actions.export.unavailable_reason() is None


def test_a_cancelled_run_that_finished_anyway_is_still_cancelled(make_env) -> None:
    env = make_env(gated=(0,), ignore_cancel=True)
    env.open()
    env.wait(lambda: env.session.analysis().done == 1)
    env.button("timeline.cancel").click()
    env.analysis.release(0)  # the analysis completes although the user cancelled (DR-47's shape)
    env.phase_is("cancelled")
    assert "complete" not in env.phases
    assert env.session.statistics() is None


@pytest.mark.parametrize("ignore_cancel", [False, True])
def test_a_cancel_by_a_third_party_is_never_a_completion(make_env, ignore_cancel: bool) -> None:
    env = make_env(gated=(0,), ignore_cancel=ignore_cancel)
    env.open()
    env.wait(lambda: env.session.analysis().done == 1)
    env.window.jobs.cancel()  # not the panel's cancel: the runner's own (close does the same)
    env.analysis.release(0)  # an analysis that ignores the cancel finishes anyway
    env.phase_is("cancelled")
    assert "complete" not in env.phases
    assert env.session.statistics() is None
    assert env.button("timeline.analyse").isEnabled()


def test_an_exception_after_a_third_party_cancel_is_a_cancel_not_a_failure(make_env) -> None:
    env = make_env(gated=(0,), raise_on_cancel=True)
    env.open()
    env.wait(lambda: env.session.analysis().done == 1)
    env.window.jobs.cancel()  # the analysis raises while it stops
    env.phase_is("cancelled")
    assert "failed" not in env.phases and "complete" not in env.phases
    assert presenter_of(env.window).of("error") == []
    assert env.button("timeline.analyse").isEnabled()


def test_a_scrub_read_that_fails_after_a_cancel_shows_no_error(make_env) -> None:
    env = make_env(gated=(0,), proxy_delay=0.3, fail_proxy=(PTS[2],))
    complete(env)
    drag_to(env, 2)  # the proxy read sleeps, then raises KeyError
    env.wait(lambda: env.analysis.active_proxy == 1)
    env.window.jobs.cancel()
    env.wait(lambda: env.window.jobs.active() == 0)
    env.qtbot.wait(50)
    assert presenter_of(env.window).of("error") == []


def test_retarget_with_no_run_in_flight_raises_in_the_panel(make_env) -> None:
    env = make_env(gated=(0,))
    complete(env)  # the run ended and its on_done was delivered
    with pytest.raises(RuntimeError):
        env.panel._retarget()
    assert env.analysis.retargets == []


def test_a_failed_analysis_says_why_keeps_the_preview_and_clears_on_analyse(make_env) -> None:
    env = make_env(gated=(), fail_runs=(0,))
    env.open()
    env.phase_is("failed")
    presenter = presenter_of(env.window)
    assert [m.owner for m in presenter.of("error")] == [OWNER_ANALYSIS]
    assert "scripted failure" in presenter.of("error")[0].text
    reason = env.window.shell_actions.export.unavailable_reason()
    assert reason is not None and "scripted failure" in reason
    env.rendered_is(FLAT)  # the provisional preview stays
    env.button("timeline.analyse").click()
    env.phase_is("complete")
    assert presenter.of("error") == []


# D72, G4.


def test_dragging_shows_the_stored_proxy_and_never_sets_the_position(make_env) -> None:
    scenario_drag(make_env(gated=(0,)))


def test_planted_set_position_during_a_drag_fails(make_env) -> None:
    env = make_env(panel_class=DragSetsPositionPanel, gated=(0,))
    with pytest.raises(AssertionError, match="set_position was called during the drag"):
        scenario_drag(env, ms=700)


def test_release_sets_the_exact_pts_with_the_smoothed_statistics(make_env) -> None:
    env = make_env(gated=(0,))
    complete(env)
    env.positions.clear()
    drag_to(env, 3)
    release(env)
    env.wait(lambda: len(env.positions) == 1)
    pts, statistics = env.positions[0]
    assert pts == PTS[3] and pts in env.analysis.stored
    assert float(np.asarray(statistics["only"]["mean"])[0]) == pytest.approx(smooth(PTS[3]))
    env.wait(lambda: env.session.current_image().pts_ticks == PTS[3])
    env.rendered_is(smooth(PTS[3]))


def test_a_keyboard_step_commits_the_next_pts(make_env) -> None:
    env = make_env(gated=(0,))
    complete(env)
    env.positions.clear()
    env.slider().setValue(1)  # not down: a key or a click
    env.wait(lambda: any(p == PTS[1] for p, _ in env.positions))
    env.wait(lambda: env.session.current_image().pts_ticks == PTS[1])


def test_a_release_without_a_value_change_still_replaces_the_proxy(make_env) -> None:
    env = make_env(gated=(0,))
    complete(env)
    count = len(env.positions)
    env.slider().setSliderDown(True)
    env.slider().setSliderDown(False)
    env.wait(lambda: len(env.positions) == count + 1)


def test_latest_wins_runs_one_proxy_read_at_a_time(make_env) -> None:
    env = make_env(gated=(0,), proxy_delay=0.03)
    complete(env)
    env.shown.clear()
    for index in (1, 2, 3, 4):
        drag_to(env, index)
    last = np.full((12, 16, 3), PTS[4] % 251, np.uint8)
    env.wait(lambda: bool(env.shown) and np.array_equal(env.shown[-1], last))
    assert env.analysis.max_proxy == 1
    release(env)
    env.wait(lambda: any(p == PTS[4] for p, _ in env.positions))


def test_scrub_failures_are_owned_by_the_timeline_and_cleared_by_the_next_success(
    make_env,
) -> None:
    env = make_env(gated=(0,), fail_proxy=(PTS[2],))
    complete(env)
    presenter = presenter_of(env.window)
    drag_to(env, 2)
    env.wait(lambda: [m.owner for m in presenter.of("error")] == [OWNER_TIMELINE])
    drag_to(env, 3)
    env.wait(lambda: presenter.of("error") == [])
    release(env)


def test_the_failure_of_a_superseded_scrub_request_is_not_presented(
    make_env, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = make_env(gated=(0,), proxy_delay=0.15, fail_proxy=(PTS[2],))
    complete(env)
    presenter = presenter_of(env.window)
    seen: list[Any] = []
    original = presenter.present

    def record(message: Any) -> None:
        seen.append(message)
        original(message)

    monkeypatch.setattr(presenter, "present", record)
    drag_to(env, 2)  # this read fails after its delay ...
    env.wait(lambda: env.analysis.active_proxy == 1)
    drag_to(env, 3)  # ... when a newer request already exists
    last = np.full((12, 16, 3), PTS[3] % 251, np.uint8)
    env.wait(lambda: bool(env.shown) and np.array_equal(env.shown[-1], last))
    env.wait(lambda: env.window.jobs.active() == 0)
    assert [m for m in seen if m.severity == "error"] == []
    release(env)


def test_run_proxy_and_statistics_run_off_the_interface_thread(make_env) -> None:
    scenario_run_thread(make_env(gated=(0,)))


def test_planted_analysis_run_on_the_interface_thread_fails(make_env) -> None:
    env = make_env(panel_class=InlineRunPanel, gated=())
    with pytest.raises(AssertionError, match="ran on the interface thread"):
        scenario_run_thread(env, ms=700)


# DR-44 (a): every frame is shown with its own pts's statistics.


def test_a_decoded_pts_that_differs_from_the_request_gets_its_own_statistics(make_env) -> None:
    stored = (1000, 4000, 7000, 10000, 13000)  # between the frames; the shell shows the next one
    env = make_env(gated=(0,), stored=stored)
    env.open()
    env.wait(lambda: len(env.analysis.runs) > 0)
    env.analysis.release(0)
    env.phase_is("complete")
    env.wait(lambda: env.slider().maximum() == len(stored) - 1)
    env.positions.clear()
    env.stat_calls.clear()
    env.slider().setValue(1)  # requests 4000: statistics(4000) is None; the frame is 6006
    env.wait(lambda: env.positions and env.positions[0][0] == 4000)
    assert env.positions[0][1] is None
    env.wait(lambda: env.session.current_image().pts_ticks == PTS[2])
    env.rendered_is(smooth(PTS[2]))
    assert env.stat_calls[0] is None  # at once the frame's own, never another frame's
    assert env.statistics_mean() == pytest.approx(smooth(PTS[2]))


def test_a_decode_failure_restores_the_last_shown_frames_statistics_and_the_slider(
    make_env,
) -> None:
    scenario_decode_failure(make_env(gated=(0,), fail_decode=(PTS[2],)))


def test_planted_requested_statistics_kept_after_a_failed_decode_fails(make_env) -> None:
    env = make_env(panel_class=KeepRequestedStatisticsPanel, gated=(0,), fail_decode=(PTS[2],))
    with pytest.raises(AssertionError, match="statistics_restored_to_the_last_shown_frame"):
        scenario_decode_failure(env, ms=700)


def test_only_pts_from_the_analysis_are_requested(make_env) -> None:
    env = make_env(gated=(0,), ticks=VFR)
    env.open()
    env.wait(lambda: len(env.analysis.runs) > 0)
    env.analysis.release(0)
    env.phase_is("complete")
    env.wait(lambda: env.slider().maximum() == len(VFR) - 1)
    for index in (3, 1, 4, 2):
        env.slider().setValue(index)
        env.wait(lambda i=index: env.positions and env.positions[-1][0] == VFR[i])
        env.wait(lambda i=index: env.session.current_image().pts_ticks == VFR[i])
    assert {p for p, _ in env.positions} <= set(VFR)


def test_a_vfr_clip_scrubs_to_exact_pts_with_their_own_statistics(make_env) -> None:
    env = make_env(gated=(0,), ticks=VFR)
    env.open()
    env.wait(lambda: len(env.analysis.runs) > 0)
    env.analysis.release(0)
    env.phase_is("complete")
    env.wait(lambda: env.slider().maximum() == len(VFR) - 1)
    env.slider().setValue(2)  # irregular spacing: index 2 is pts 3003, not 2 * 1001
    env.wait(lambda: env.session.current_image().pts_ticks == VFR[2])
    env.rendered_is(smooth(VFR[2]))
    assert env.positions[-1][0] == 3003


# AD-15: parameter changes.


def test_a_change_during_the_run_not_absorbed_triggers_one_follow_up_before_complete(
    make_env,
) -> None:
    env = make_env(gated=(0, 1))
    env.open()
    env.wait(lambda: len(env.analysis.runs) == 1)
    env.set_level(0.8)
    assert len(env.analysis.retargets) == 1  # offered to the run in flight, which did not absorb
    assert env.session.statistics() is None  # the preview is provisional meanwhile
    env.analysis.release(0)
    env.wait(lambda: len(env.analysis.runs) == 2)  # one follow-up run under the new values
    assert env.session.analysis().phase == "running"
    assert env.window.shell_actions.export.unavailable_reason() is not None
    assert env.analysis.runs[1][0].parameters["level"] == 0.8
    env.analysis.release(1)
    env.phase_is("complete")
    assert len(env.analysis.runs) == 2 and "cancelled" not in env.phases
    env.rendered_is(smooth(0, 0.8))


def test_a_change_during_the_run_that_is_absorbed_completes_once_under_the_new_values(
    make_env,
) -> None:
    env = make_env(gated=(0,), absorb=True)
    env.open()
    env.wait(lambda: len(env.analysis.runs) == 1)
    env.set_level(0.8)
    assert len(env.analysis.retargets) == 1
    env.analysis.release(0)
    env.phase_is("complete")
    assert len(env.analysis.runs) == 1 and "cancelled" not in env.phases
    env.rendered_is(smooth(0, 0.8))


def test_after_completion_a_change_goes_provisional_then_smoothed_again(make_env) -> None:
    env = make_env(gated=(0, 1))
    complete(env)
    env.rendered_is(smooth(0))
    env.set_level(0.8)
    assert env.session.statistics() is None  # at once, before anything else
    state = env.session.analysis()
    assert (state.phase, state.message) == ("running", LABEL_UPDATING)
    assert env.window.shell_actions.export.unavailable_reason() is not None
    env.wait(lambda: len(env.analysis.runs) == 2)
    assert env.analysis.runs[1][1] == 0  # the displayed frame's pts is the focus (AD-7)
    env.rendered_is(FLAT)  # provisional again
    env.analysis.release(1)
    env.phase_is("complete")
    env.rendered_is(smooth(0, 0.8))
    assert env.window.shell_actions.export.unavailable_reason() is None


def test_a_commit_in_flight_when_the_parameters_change_carries_no_stale_statistics(
    make_env,
) -> None:
    env = make_env(gated=(0, 1))
    complete(env)
    env.positions.clear()
    gate = threading.Event()
    env.analysis.statistics_gate = gate
    env.slider().setValue(2)  # the lane job waits inside statistics(PTS[2])
    env.wait(env.analysis.statistics_waiting.is_set)
    env.set_level(0.8)
    gate.set()
    env.wait(lambda: any(p == PTS[2] for p, _ in env.positions))
    stale = next(s for p, s in env.positions if p == PTS[2])
    assert stale is None
    env.analysis.release(1)
    env.phase_is("complete")


def test_a_commit_in_flight_when_a_drag_starts_is_not_applied_before_the_release(
    make_env,
) -> None:
    env = make_env(gated=(0,))
    complete(env)
    env.positions.clear()
    env.shown.clear()
    gate = threading.Event()
    env.analysis.statistics_gate = gate
    env.slider().setValue(2)  # not down: a commit; its lane job waits inside statistics(PTS[2])
    env.wait(env.analysis.statistics_waiting.is_set)
    drag_to(env, 3)  # the slider goes down and moves: a newer request, a proxy
    gate.set()
    last = np.full((12, 16, 3), PTS[3] % 251, np.uint8)
    env.wait(lambda: bool(env.shown) and np.array_equal(env.shown[-1], last))
    assert env.positions == []  # the older commit was dropped, the drag shows proxies only
    release(env)
    env.wait(lambda: any(p == PTS[3] for p, _ in env.positions))
    assert [p for p, _ in env.positions] == [PTS[3]]


def test_a_frame_decoded_during_a_drag_does_not_leave_an_older_frame_over_the_proxy(
    make_env,
) -> None:
    env = make_env(gated=(0,), hold_decode=(PTS[2],))
    complete(env)
    env.slider().setValue(2)  # a click: committed, the shell's decode of PTS[2] is held
    env.wait(env.source.holding.is_set)
    drag_to(env, 3)  # the drag starts within the decode time: the proxy of PTS[3]
    last = np.full((12, 16, 3), PTS[3] % 251, np.uint8)
    env.wait(lambda: bool(env.shown) and np.array_equal(env.shown[-1], last))
    env.source.hold.set()  # the older frame arrives while the slider is still down
    env.wait(lambda: env.session.current_image().pts_ticks == PTS[2])
    env.qtbot.wait(300)  # the render of that frame and the proxy re-shown settle
    assert env.slider().isSliderDown()
    assert env.display[-1] == "proxy"  # the drag's proxy, not the older frame's render
    assert np.array_equal(env.shown[-1], last)
    release(env)
    env.wait(lambda: any(p == PTS[3] for p, _ in env.positions))


def test_a_failed_decode_after_a_parameter_change_restores_no_statistics(make_env) -> None:
    env = make_env(gated=(0, 1), fail_decode=(PTS[2],))
    complete(env)
    env.slider().setValue(1)
    env.wait(lambda: env.session.current_image().pts_ticks == PTS[1])
    env.rendered_is(smooth(PTS[1]))
    gate = threading.Event()
    env.analysis.statistics_gate = gate
    env.slider().setValue(2)  # the lane job waits inside statistics(PTS[2]); its decode will fail
    env.wait(env.analysis.statistics_waiting.is_set)
    env.set_level(0.8)  # the statistics of the shown frame are now the old parameters'
    gate.set()
    env.wait(lambda: any(m.owner == "shell.frame" for m in presenter_of(env.window).of("error")))
    env.wait(lambda: env.slider().value() == 1)  # the rollback follows the restore
    assert env.session.current_image().pts_ticks == PTS[1]
    assert env.session.statistics() is None  # not the mapping of the old parameters
    env.analysis.release(1)
    env.phase_is("complete")


def test_a_frame_decoded_after_a_parameter_change_is_not_remembered_with_old_statistics(
    make_env,
) -> None:
    env = make_env(gated=(0, 1), hold_decode=(PTS[2],), fail_decode=(PTS[3],))
    complete(env)
    env.slider().setValue(2)  # committed with the smoothed statistics; its decode is held
    env.wait(env.source.holding.is_set)
    env.set_level(0.8)  # the statistics supplied with that decode are the old parameters'
    env.source.hold.set()
    env.wait(lambda: env.session.current_image().pts_ticks == PTS[2])
    env.slider().setValue(3)  # a provisional commit (running again); its decode fails
    env.wait(lambda: any(m.owner == "shell.frame" for m in presenter_of(env.window).of("error")))
    env.wait(lambda: env.slider().value() == 2)
    assert env.session.statistics() is None
    env.analysis.release(1)
    env.phase_is("complete")


def test_a_method_change_while_running_rebuilds_the_analysis_as_superseded(make_env) -> None:
    env = make_env(method_ids=("statm", "other"), gated=(0,))
    env.open()
    env.wait(lambda: len(env.analysis.runs) == 1)
    first = env.analysis
    env.session.set_parameters(new_parameter_set("other", {}))
    env.wait(lambda: len(env.built) == 2)
    assert first.cancelled_runs == [0]
    assert env.built[1].method_id == "other"
    assert "cancelled" not in env.phases  # superseded, never the user's cancel
    assert env.session.analysis().phase == "running"
    env.wait(lambda: len(env.built[1].runs) == 1)
    env.built[1].release(0)
    env.phase_is("complete")


def test_a_method_change_after_completion_analyses_again(make_env) -> None:
    env = make_env(method_ids=("statm", "other"), gated=(0,))
    complete(env)
    env.session.set_parameters(new_parameter_set("other", {}))
    env.wait(lambda: len(env.built) == 2)
    env.wait(lambda: len(env.built[1].runs) == 1)
    assert env.session.statistics() is None
    env.built[1].release(0)
    env.phase_is("complete")


def test_analyse_after_a_cancel_and_a_method_change_builds_the_new_methods_analysis(
    make_env,
) -> None:
    env = make_env(method_ids=("statm", "other"), gated=(0,))
    env.open()
    env.wait(lambda: env.session.analysis().done == 1)
    env.button("timeline.cancel").click()
    env.phase_is("cancelled")
    env.session.set_parameters(new_parameter_set("other", {}))  # nothing runs: cancelled
    env.qtbot.wait(50)
    assert len(env.built) == 1 and env.session.analysis().phase == "cancelled"
    env.button("timeline.analyse").click()  # the lazy rebuild: a new analysis for the new method
    env.wait(lambda: len(env.built) == 2)
    env.wait(lambda: len(env.built[1].runs) == 1)
    assert env.built[1].method_id == "other"
    env.built[1].release(0)
    env.phase_is("complete")


def test_a_method_change_during_a_user_cancel_stays_cancelled_and_analyse_rebuilds(
    make_env,
) -> None:
    env = make_env(method_ids=("statm", "other"), gated=(0,), ignore_cancel=True)
    env.open()
    env.wait(lambda: env.session.analysis().done == 1)
    env.button("timeline.cancel").click()  # D70: the user's cancel, still being delivered
    env.session.set_parameters(new_parameter_set("other", {}))
    env.qtbot.wait(50)
    assert len(env.built) == 1  # not superseded: the analysis is not restarted
    env.analysis.release(0)
    env.phase_is("cancelled")
    assert len(env.built) == 1 and env.session.statistics() is None
    env.button("timeline.analyse").click()  # the next Analyse rebuilds for the new method
    env.wait(lambda: len(env.built) == 2 and len(env.built[1].runs) == 1)
    assert env.built[1].method_id == "other"
    env.built[1].release(0)
    env.phase_is("complete")


# Stale work, close.


def test_a_source_change_mid_analysis_leaves_no_state_or_statistics_from_the_old_job(
    make_env,
) -> None:
    env = make_env(gated=(0,))
    env.open("one.mp4")
    env.wait(lambda: len(env.analysis.runs) == 1)
    old = env.analysis
    env.open("two.mp4")
    env.wait(lambda: len(env.built) == 2)
    env.wait(lambda: len(env.built[1].runs) == 1)
    old.release(0)  # the old job ends; nothing of it may reach the session
    env.wait(lambda: old.cancelled_runs == [0])
    env.qtbot.wait(150)
    assert env.session.analysis().phase == "running"
    assert env.session.statistics() is None
    assert "complete" not in env.phases and "cancelled" not in env.phases
    env.built[1].release(0)
    env.phase_is("complete")
    assert env.phases.count("complete") == 1


def test_a_photo_opened_mid_analysis_cancels_the_run(make_env, tmp_path: Path) -> None:
    photo = tmp_path / "p.jpg"
    photo.write_bytes(b"x")
    env = make_env(gated=(0,), photos={photo: (gui_support.image(12, 16), META)})
    env.open()
    env.wait(lambda: len(env.analysis.runs) == 1)
    first = env.analysis
    open_and_wait(env.qtbot, env.window, photo)
    env.wait(lambda: first.cancelled_runs == [0])
    assert env.session.analysis().phase == "none"


def test_closing_the_window_mid_analysis_does_not_report_a_completion(make_env) -> None:
    env = make_env(gated=(0,))
    env.open()
    env.wait(lambda: len(env.analysis.runs) == 1)
    env.window.close()
    env.qtbot.wait(100)
    assert "complete" not in env.phases and env.analysis.cancelled_runs == [0]


# V7, the default install.


def test_the_default_install_uses_the_stub_analysis_and_completes(make_env) -> None:
    env = make_env(factory=stub_analysis_factory)
    env.open()
    env.phase_is("complete", 8000)
    assert env.window.shell_actions.export.unavailable_reason() is None
    env.wait(lambda: env.slider().maximum() == len(PTS) - 1)
    env.slider().setValue(3)
    env.wait(lambda: env.session.current_image().pts_ticks == PTS[3])


def test_v7_interface_never_waits_more_than_100_ms_during_analysis_and_a_drag(make_env) -> None:
    method = StatMethod(busy=busy_numpy(0.35))
    env = make_env(methods={"statm": method}, factory=stub_analysis_factory)
    path = env.tmp_path / "heavy.mp4"
    path.write_bytes(b"clip")
    clock = QElapsedTimer()
    clock.start()
    last = [clock.elapsed()]
    worst = [0]

    def tick() -> None:
        now = clock.elapsed()
        worst[0] = max(worst[0], now - last[0])
        last[0] = now

    probe = QTimer()
    probe.setInterval(10)
    probe.timeout.connect(tick)
    slider = env.slider()

    def drag_step() -> None:
        if slider.maximum() > 0 and env.session.analysis().phase == "running":
            if not slider.isSliderDown():
                slider.setSliderDown(True)
            slider.setValue((slider.value() + 1) % (slider.maximum() + 1))

    stepper = QTimer()
    stepper.setInterval(15)
    stepper.timeout.connect(drag_step)
    probe.start()
    QTimer.singleShot(30, lambda: env.window.open_path(path))
    stepper.start()
    try:
        env.qtbot.wait(60)
        env.wait(lambda: env.session.analysis().phase == "complete", 30000)
    finally:
        stepper.stop()
        probe.stop()
    tick()
    release(env)
    print(f"V7 observed maximum main-thread gap during analysis and a drag: {worst[0]} ms")
    assert worst[0] <= V7_BOUND_MS
