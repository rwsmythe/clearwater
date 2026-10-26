"""The timeline panel (WP3.18): analysis on clip open, AD-15's states, the scrubber, the switch.

:func:`install_timeline` attaches one panel in ``Area.TIMELINE``. For an opened video the panel
builds a :class:`~clearwater.gui.analysis_service.ClipAnalysis`, runs it in the background
through the shell's job runner (G5, D70: progress, cancel), sets the AD-15 state on the session,
gives the scrubber (G4, D72: the stored proxy while the slider is down, the full-resolution
corrected frame when it stops), and switches the preview from the provisional to the smoothed
statistics when the analysis completes (D108, V18). Every frame it asks the shell to show is
paired with its own pts's statistics (DR-44 (a)); no index is ever a key (AD-6, DR-23).

Whoever cancels a job, its result is "cancelled", never complete (the job callable checks the
IF-8 progress after the seam call returns). Main thread only, except the job callables, which
run ``ClipAnalysis.run``, ``proxy`` and ``statistics`` on worker threads. A parameter change
never cancels a run (CHARC ruling on Q-A): it is offered to the run in flight with
``ClipAnalysis.retarget``; when that does not absorb it, the run finishes and a follow-up run
with the latest parameters starts from its done callback, always (the analysis may hold a job
for the refused parameters, even if they were changed back to the run's own). The GUI itself
cancels only for the user (D70), a method change and a source change.

The position lane obeys ONE rule, "the latest intent". Every user event (press, value change,
release, and the completion switch) and nothing else takes the next number of one sequence and
becomes the newest intent; a fix request (the statistics of a frame the shell decoded at another
pts) and the re-show of the drag's proxy take numbers too but are not intents. A lane result is
applied only if it belongs to the newest intent: a commit if it IS the newest intent, a fix if
the commit whose frame it repairs is, a proxy if the slider is still down in the drag it was
asked for and it is the proxy of the handle's value (the one the newest intent needs; a proxy
of a value the hand has passed is dropped). Hence ``set_position`` is called only for a commit
that is the newest intent, so never while the slider is down, and release always commits
``pts()[value]``. While the slider is down the handle belongs to the hand: each value shows the
stored proxy of its pts, a frame the shell decodes meanwhile only makes the same proxy be shown
again, and nothing moves the handle.
"""

from __future__ import annotations

import bisect
import logging
import time
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Literal

from PySide6.QtCore import QSignalBlocker, Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from clearwater.interfaces import JobResult, Progress, Statistics

from . import messages
from .analysis_service import AnalysisFactory, ClipAnalysis, stub_analysis_factory
from .contract import (
    AnalysisState,
    Area,
    FrameOutcome,
    JobHandle,
    Message,
    OpenedSource,
    ShellContext,
    ShellWindow,
)
from .imaging import effective_parameters

_LOG = logging.getLogger(__name__)

PANEL_TITLE = "Timeline"
"""The title the panel attaches under (the panel's object name in ``Area.TIMELINE``)."""

OWNER_ANALYSIS = "analysis"
"""The message owner of analysis failures (DR-44 (b))."""

OWNER_TIMELINE = "timeline"
"""The message owner of scrubber failures (DR-44 (b))."""

LABEL_ANALYSING = "Analysing the clip"
"""The status text of the first run of an analysis."""

CANCELLED = "cancelled"
"""The ``JobResult.failure`` of a job the runner cancelled, whoever cancelled it."""

LABEL_UPDATING = "Updating statistics"
"""The status text of a run that follows a parameter change (AD-15)."""

type StatsMap = Mapping[str, Statistics]


@dataclass(frozen=True)
class _Target:
    """What a run analyses under: the method id and the effective parameter values."""

    method_id: str
    values: dict[str, Any]


@dataclass
class _Run:
    """The run in flight."""

    ticket: int
    handle: JobHandle
    target: _Target
    label: str
    reason: Literal["user", "superseded"] | None = None
    done: int = 0
    total: int | None = None
    kept: bool = False
    """A ``retarget`` returned False: the analysis may hold a job for later parameters."""


@dataclass(frozen=True)
class _Request:
    """One request of the position lane: a proxy to show, a frame to commit, or a fix."""

    seq: int
    kind: Literal["proxy", "commit", "fix"]
    pts: int
    epoch: int
    ref: int
    """What the request belongs to: its commit (or the one it repairs), or its drag (a proxy)."""


@contextmanager
def _blocked(widget: QWidget) -> Iterator[None]:
    """Block a widget's signals for the duration (``QSignalBlocker``)."""
    blocker = QSignalBlocker(widget)
    try:
        yield
    finally:
        blocker.unblock()


class TimelinePanel(QWidget):
    """The timeline: scrubber, progress, Cancel and Analyse for the open video.

    Args:
        context: The shell context (session, engines, jobs, messages).
        factory: Builds the :class:`ClipAnalysis` of each opened video.
        parent: The Qt parent.
    """

    def __init__(
        self, context: ShellContext, factory: AnalysisFactory, parent: QWidget | None = None
    ) -> None:
        """Build the widgets and connect to the session."""
        super().__init__(parent)
        self._context = context
        self._session = context.session
        self._jobs = context.jobs
        self._messages = context.messages
        self._factory = factory

        self._generation = 0
        self._ticket = 0
        self._seq = 0
        self._epoch = 0
        self._source: OpenedSource | None = None
        self._analysis: ClipAnalysis | None = None
        self._analysis_method = ""
        self._run: _Run | None = None
        self._rebuild_pending = False
        self._done_target: _Target | None = None
        self._pts: tuple[int, ...] = ()
        self._slider_pts: int | None = None
        self._dragging = False
        self._lane: JobHandle | None = None
        self._wanted: _Request | None = None
        self._intent = 0
        self._drag = 0
        self._shown_proxy_seq = 0
        self._requested_seq = 0
        self._wanted_pts: int | None = None
        self._requested: int | None = None
        self._supplied: StatsMap | None = None
        self._shown_pts: int | None = None
        self._shown_statistics: StatsMap | None = None
        self._scrub_error_shown = False

        self._slider = QSlider(Qt.Orientation.Horizontal, self)
        self._slider.setObjectName("timeline.slider")
        self._time = QLabel("", self)
        self._time.setObjectName("timeline.time")
        self._bar = QProgressBar(self)
        self._bar.setObjectName("timeline.progress")
        self._status = QLabel("", self)
        self._status.setObjectName("timeline.status")
        self._cancel = QPushButton("Cancel", self)
        self._cancel.setObjectName("timeline.cancel")
        self._analyse = QPushButton("Analyse", self)
        self._analyse.setObjectName("timeline.analyse")
        top = QHBoxLayout()
        top.addWidget(self._slider, 1)
        top.addWidget(self._time)
        bottom = QHBoxLayout()
        bottom.addWidget(self._bar, 1)
        bottom.addWidget(self._status)
        bottom.addWidget(self._cancel)
        bottom.addWidget(self._analyse)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.addLayout(top)
        layout.addLayout(bottom)

        self._slider.sliderPressed.connect(self._on_pressed)
        self._slider.sliderReleased.connect(self._on_released)
        self._slider.valueChanged.connect(self._on_slider_value)
        self._cancel.clicked.connect(self.cancel_analysis)
        self._analyse.clicked.connect(self.start_analysis)
        self._session.source_changed.connect(self._on_source)
        self._session.parameters_changed.connect(self._on_parameters)
        self._session.analysis_changed.connect(self._update_controls)
        self._session.frame_decoded.connect(self._on_frame_decoded)
        self._reset_scrubber()
        self._update_controls()
        current = self._session.source()
        if current is not None:
            self._on_source(current)

    # Public controls (the buttons call these).

    def slider(self) -> QSlider:
        """Return the scrubber slider (its range is the index range of ``ClipAnalysis.pts()``)."""
        return self._slider

    def pts(self) -> tuple[int, ...]:
        """Return the pts ticks the slider ranges over."""
        return self._pts

    def cancel_analysis(self) -> None:
        """Cancel the analysis (D70); the clip stays open and the state becomes ``cancelled``."""
        run = self._run
        if run is None or run.reason is not None:
            return
        run.reason = "user"
        run.handle.cancel()
        self._update_controls()

    def start_analysis(self) -> None:
        """Start the analysis again after a cancel or a failure (the Analyse button)."""
        source = self._source
        if source is None or self._run is not None:
            return
        if self._session.analysis().phase not in ("none", "cancelled", "failed"):
            return
        self._messages.clear(owner=OWNER_ANALYSIS)
        if self._analysis is None or self._analysis_method != self._session.method().id:
            self._build_and_run()
            return
        self._session.set_analysis(self._running_state(LABEL_ANALYSING))
        self._start_run(LABEL_ANALYSING)

    # Source and analysis.

    def _on_source(self, source: object) -> None:
        """A new source (or none): drop everything of the old one, start the new analysis.

        The one-job-in-flight rule of the position lane is per ``ClipAnalysis``: a lane job of
        the old source may still be running on the old object while the new source's first lane
        job starts on the new one. The old job is cancelled and its result is dropped by the
        generation check; it never reaches the session.
        """
        self._generation += 1
        if self._run is not None:
            self._run.handle.cancel()
        if self._lane is not None:
            self._lane.cancel()
        self._run = None
        self._lane = None
        self._wanted = None
        self._analysis = None
        self._analysis_method = ""
        self._rebuild_pending = False
        self._done_target = None
        self._epoch += 1
        self._requested = None
        self._requested_seq = 0
        self._supplied = None
        self._shown_statistics = None
        self._scrub_error_shown = False
        self._source = None
        self._messages.clear(owner=OWNER_ANALYSIS)
        self._messages.clear(owner=OWNER_TIMELINE)
        self._reset_scrubber()
        if isinstance(source, OpenedSource) and source.kind == "video" and source.probe:
            self._source = source
            ticks = getattr(source.image, "pts_ticks", None)
            self._shown_pts = ticks if isinstance(ticks, int) else None
            self._wanted_pts = self._shown_pts
            self._slider_pts = self._shown_pts
            self._build_and_run()
        self._update_controls()

    def _build_and_run(self) -> None:
        """Build the analysis for the session's method and start its first run."""
        source = self._source
        assert source is not None
        method = self._session.method()
        try:
            self._analysis = self._factory(source, method, self._context.engines)
        except Exception as exc:  # a factory failing is a failed analysis, never a crash
            self._analysis = None
            self._fail(f"The analysis could not be started: {exc}")
            return
        self._analysis_method = method.id
        self._pts = ()
        self._reset_slider_range()
        self._session.set_analysis(self._running_state(LABEL_ANALYSING))
        self._start_run(LABEL_ANALYSING)

    def _running_state(self, label: str) -> AnalysisState:
        """The state a run starts in: zero done of the container's frame count."""
        source = self._source
        total = None if source is None or source.probe is None else source.probe.video.nb_frames
        return AnalysisState("running", 0, total, label)

    def _current_target(self) -> _Target:
        """The session's method id and effective parameter values."""
        method = self._session.method()
        return _Target(method.id, effective_parameters(method, self._session.parameters()))

    def _start_run(self, label: str) -> bool:
        """Start ``ClipAnalysis.run`` under the session's parameters; False when not started."""
        analysis = self._analysis
        assert analysis is not None
        parameters = self._session.parameters()
        target = self._current_target()
        self._ticket += 1
        ticket = self._ticket
        generation = self._generation
        focus = self._shown_pts
        began = time.perf_counter()

        def job(progress: Progress) -> JobResult:
            try:
                analysis.run(parameters, progress, focus_pts=focus)
            except Exception:
                if not progress.cancelled():  # a failure of its own; after a cancel it is not one
                    raise
            # Whoever cancelled (the user, a method change, a source change, the runner's own
            # cancel at close), a cancelled job is never complete, even if the analysis finished
            # first (DR-47's shape; conservative: "Analyse" then costs the engine nothing).
            ok = not progress.cancelled()
            failure = None if ok else CANCELLED
            return JobResult(ok, (), (), failure, "analysis", time.perf_counter() - began)

        try:
            handle = self._jobs.run(
                job,
                on_done=lambda result: self._on_done(generation, ticket, result),
                on_progress=lambda done, total, text: self._on_progress(
                    generation, ticket, done, total, text
                ),
            )
        except RuntimeError as exc:  # the job runner is closed (the window is closing)
            _LOG.info("analysis not started: %s", exc)
            # No job will ever end this state: the terminal phase an ordinary close gives.
            self._session.set_analysis(AnalysisState("cancelled", message="Analysis cancelled"))
            return False
        self._run = _Run(ticket, handle, target, label)
        self._update_controls()
        return True

    def _on_progress(
        self, generation: int, ticket: int, done: int, total: int | None, text: str
    ) -> None:
        """Main thread: a progress report of the current run; its text is the label (ASCII)."""
        run = self._run
        if generation != self._generation or run is None or run.ticket != ticket:
            return
        if run.reason is not None:
            return
        run.done, run.total = done, total
        label = messages.ascii_text(text) if text else run.label
        self._session.set_analysis(AnalysisState("running", done, total, label))
        self._refresh_pts()

    def _on_done(self, generation: int, ticket: int, result: JobResult) -> None:
        """Main thread: the run ended; cancelled, failed, followed up or complete."""
        run = self._run
        if generation != self._generation or run is None or run.ticket != ticket:
            return
        self._run = None
        self._refresh_pts()
        if run.reason == "superseded" and self._rebuild_pending:
            self._rebuild_pending = False
            self._build_and_run()
            return
        cancelled = run.reason is not None or result.failure == CANCELLED
        if cancelled:  # the user's cancel (D70), or a third party's: either way not complete
            self._statistics_stale()
            self._session.set_statistics(None)
            self._session.set_analysis(AnalysisState("cancelled", message="Analysis cancelled"))
            return
        if not result.ok:
            self._statistics_stale()
            self._session.set_statistics(None)
            self._fail(result.failure or "The analysis failed.")
            return
        now = self._current_target()
        # AD-15: restart the dependent stages when the analysis completes. A kept job is run by
        # ``run`` whatever the values are now: a burst that returned to the run's own values (A,
        # B, A) still leaves the analysis holding the job of B, so it is never complete.
        if run.kept or now != run.target:
            self._session.set_statistics(None)
            self._session.set_analysis(AnalysisState("running", 0, run.total, LABEL_UPDATING))
            self._start_run(LABEL_UPDATING)
            return
        self._messages.clear(owner=OWNER_ANALYSIS)
        self._done_target = run.target
        self._session.set_analysis(
            AnalysisState("complete", run.done, run.total, "Analysis complete")
        )
        self._switch()

    def _statistics_stale(self) -> None:
        """The statistics a commit could carry stop being right: new epoch, nothing to restore.

        Bumps the epoch (a lane result fetched before is supplied as None) and forgets both the
        statistics of the shown frame and those supplied with a decode still pending, so a
        failed or late decode never remembers or re-supplies the mapping of the old parameters
        (DR-44 (a)).
        """
        self._epoch += 1
        self._supplied = None
        self._shown_statistics = None

    def _fail(self, text: str) -> None:
        """Set the failed state and present the failure (owner ``analysis``)."""
        shown = messages.ascii_text(text)
        self._session.set_analysis(AnalysisState("failed", message=shown))
        source = self._source
        self._messages.present(
            Message(
                "error",
                f"The analysis failed: {shown}",
                source.path if source else None,
                OWNER_ANALYSIS,
            )
        )

    def _on_parameters(self, _parameters: object) -> None:
        """Main thread: offer a change to the run in flight, or recompute when complete (AD-15)."""
        if self._analysis is None or self._source is None:
            return
        if self._session.method().id != self._analysis_method:
            self._on_method_changed()
            return
        target = self._current_target()
        run = self._run
        if run is not None:
            if run.reason is not None or target == run.target:
                return
            self._statistics_stale()
            if self._retarget():
                run.target = target
            else:
                run.kept = True  # from now on this run's done-ok never declares complete
            return
        if self._session.analysis().phase == "complete" and target != self._done_target:
            self._statistics_stale()
            self._session.set_statistics(None)
            state = self._session.analysis()
            self._session.set_analysis(AnalysisState("running", 0, state.total, LABEL_UPDATING))
            self._start_run(LABEL_UPDATING)

    def _retarget(self) -> bool:
        """Offer the session's parameters to the run in flight (a run must be in flight)."""
        run = self._run
        analysis = self._analysis
        if run is None or analysis is None or not run.handle.is_running():
            raise RuntimeError("retarget needs a run in flight")
        return analysis.retarget(self._session.parameters(), focus_pts=self._shown_pts)

    def _on_method_changed(self) -> None:
        """The method changed under an open clip: a new analysis (superseded, Q-B)."""
        self._statistics_stale()
        self._session.set_statistics(None)
        run = self._run
        if run is not None:
            if run.reason is None:
                run.reason = "superseded"
                run.handle.cancel()
                self._rebuild_pending = True
                self._update_controls()  # Cancel does nothing now: do not offer it
            return  # a user cancel in flight: Analyse builds the new analysis
        if self._session.analysis().phase == "complete":
            self._build_and_run()

    # The scrubber (G4, D72).

    def _reset_scrubber(self) -> None:
        """Forget the pts list and disable the slider."""
        self._pts = ()
        self._slider_pts = None
        self._dragging = False
        self._reset_slider_range()
        self._time.setText("")

    def _reset_slider_range(self) -> None:
        """Empty the slider (no proxy yet) without emitting."""
        with _blocked(self._slider):
            self._slider.setRange(0, 0)
            self._slider.setValue(0)
        self._slider.setEnabled(bool(self._pts))

    def _index_of(self, pts: int | None) -> int:
        """The slider index of the stored frame at or before ``pts`` (0 when none)."""
        if pts is None or not self._pts:
            return 0
        return max(0, bisect.bisect_right(self._pts, pts) - 1)

    def _refresh_pts(self) -> None:
        """Main thread: re-read ``ClipAnalysis.pts()`` and keep the handle on its frame."""
        analysis = self._analysis
        if analysis is None:
            return
        fresh = analysis.pts()
        if fresh == self._pts:
            return
        self._pts = fresh
        if self._slider_pts is None and fresh:
            self._slider_pts = fresh[0]
        with _blocked(self._slider):
            self._slider.setRange(0, max(0, len(fresh) - 1))
            self._slider.setValue(self._index_of(self._slider_pts))
        self._slider.setEnabled(bool(fresh))
        self._update_time(self._slider_pts)

    def _update_time(self, pts: int | None) -> None:
        """Show the time of ``pts`` (``pts_ticks * time_base``)."""
        source = self._source
        if pts is None or source is None or source.probe is None:
            self._time.setText("")
            return
        seconds = float(pts * source.probe.video.time_base)
        self._time.setText(f"{seconds:.3f} s")

    def _on_pressed(self) -> None:
        """The slider went down: a new drag, proxies only until it is released (a new intent)."""
        self._dragging = True
        self._drag += 1
        index = self._slider.value()
        if 0 <= index < len(self._pts):
            self._request("proxy", self._pts[index])  # the proxy of the value under the hand
        else:
            self._take_intent()

    def _on_released(self) -> None:
        """The slider was released: the full-resolution corrected frame (D72), always."""
        self._dragging = False
        index = self._slider.value()
        if 0 <= index < len(self._pts):
            self._request("commit", self._pts[index])
        else:
            self._take_intent()

    def _on_slider_value(self, index: int) -> None:
        """A slider value (drag, key, click): a proxy while down, else a commit."""
        if not 0 <= index < len(self._pts):
            return
        pts = self._pts[index]
        self._slider_pts = pts
        self._update_time(pts)
        self._request("proxy" if self._dragging else "commit", pts)

    # The position lane: at most one job in flight, the latest request kept.

    def _take_intent(self) -> int:
        """Take the next number of the one sequence for a user event: the newest intent."""
        self._seq += 1
        self._intent = self._seq
        return self._seq

    def _request(self, kind: Literal["proxy", "commit", "fix"], pts: int) -> None:
        """Queue a request; the lane runs the latest one when it is free.

        A proxy or a commit is a user event and becomes the newest intent; a fix repairs the
        frame of the last applied commit and is never an intent.
        """
        if kind == "fix":
            self._seq += 1
            ref = self._requested_seq
        else:
            ref = self._take_intent()
            if kind == "proxy":
                ref = self._drag
            else:
                self._wanted_pts = pts
        self._wanted = _Request(self._seq, kind, pts, self._epoch, ref)
        self._pump()

    def _reshow_proxy(self) -> None:
        """Ask for the proxy of the slider's value again (not an intent: the drag's own need)."""
        index = self._slider.value()
        if self._dragging and 0 <= index < len(self._pts):  # a pts the analysis stores
            self._seq += 1
            self._wanted = _Request(self._seq, "proxy", self._pts[index], self._epoch, self._drag)
            self._pump()

    def _current(self, request: _Request) -> bool:
        """True when the request's result still belongs to the newest intent."""
        if request.kind == "proxy":  # the proxy of the value under the hand, nothing it passed
            index = self._slider.value()
            return (
                self._dragging
                and request.ref == self._drag
                and 0 <= index < len(self._pts)
                and request.pts == self._pts[index]
            )
        return request.ref == self._intent  # the commit itself, or the commit a fix repairs

    def _pump(self) -> None:
        """Start the wanted request when no lane job is in flight."""
        analysis = self._analysis
        request = self._wanted
        if self._lane is not None or request is None or analysis is None:
            return
        self._wanted = None
        want_statistics = request.kind != "proxy" and self._session.analysis().phase == "complete"
        box: dict[str, Any] = {}
        generation = self._generation

        def job(progress: Progress) -> JobResult:
            began = time.perf_counter()
            try:
                if request.kind == "proxy":
                    box["proxy"] = analysis.proxy(request.pts)
                elif want_statistics:
                    box["statistics"] = analysis.statistics(request.pts)
            except Exception:
                if not progress.cancelled():  # a read failure of its own, not a cancelled read
                    raise
            ok = not progress.cancelled()
            failure = None if ok else CANCELLED
            return JobResult(ok, (), (), failure, "analysis", time.perf_counter() - began)

        try:
            self._lane = self._jobs.run(
                job, on_done=lambda result: self._on_lane_done(generation, request, box, result)
            )
        except RuntimeError as exc:  # the job runner is closed
            _LOG.info("position request not started: %s", exc)

    def _on_lane_done(
        self, generation: int, request: _Request, box: dict[str, Any], result: JobResult
    ) -> None:
        """Main thread: a lane job ended; act on it if it is still wanted, then run the next."""
        if generation != self._generation:
            return
        self._lane = None
        if result.failure == CANCELLED:  # cancelled by anyone (close included): not a result
            self._pump()
            return
        if not result.ok:
            if request.seq == self._seq and self._current(request):  # a superseded one: no news
                self._scrub_failed(result.failure or "The frame could not be read.")
        elif request.kind == "proxy":
            if self._current(request) and request.seq > self._shown_proxy_seq:
                self._shown_proxy_seq = request.seq
                self._context.window.preview.show_proxy(box["proxy"])
                self._scrub_ok()
        else:
            self._apply(request, box.get("statistics"))
        self._pump()

    def _apply(self, request: _Request, fetched: StatsMap | None) -> None:
        """Supply a fetched statistics set with its frame, if the request is the newest intent."""
        if not self._current(request):  # a newer intent (a drag, a later commit) supersedes it
            return
        fresh = request.epoch == self._epoch
        statistics = fetched if fresh else None
        if request.kind == "commit":
            self._requested = request.pts
            self._requested_seq = request.seq
            self._supplied = statistics
            try:
                self._session.set_position(request.pts, statistics=statistics)
            except RuntimeError as exc:  # no video open any more
                _LOG.info("set_position refused: %s", exc)
                self._requested = None
                self._requested_seq = 0
                return
            self._scrub_ok()
        elif fresh:  # a fix for the shown frame
            self._session.set_statistics(statistics)
            self._shown_statistics = statistics

    def _scrub_failed(self, text: str) -> None:
        """Present a scrubber failure (owner ``timeline``)."""
        source = self._source
        self._messages.present(
            Message(
                "error",
                messages.ascii_text(f"The frame could not be read: {text}"),
                source.path if source else None,
                OWNER_TIMELINE,
            )
        )
        self._scrub_error_shown = True

    def _scrub_ok(self) -> None:
        """A scrubber success clears the scrubber's own error."""
        if self._scrub_error_shown:
            self._messages.clear("error", owner=OWNER_TIMELINE)
            self._scrub_error_shown = False

    # Pairing frames and statistics (DR-44 (a), V18).

    def _on_frame_decoded(self, outcome: object) -> None:
        """Main thread: pair the frame the shell now shows with its own statistics.

        A decode started by an earlier commit can finish while the slider is down; the shell
        then renders that older frame over the drag's proxy, so the proxy of the slider's value
        is asked for again. The release commits.
        """
        if not isinstance(outcome, FrameOutcome) or self._analysis is None:
            return
        self._pair_frame(outcome)
        self._reshow_proxy()

    def _pair_frame(self, outcome: FrameOutcome) -> None:
        """Pair a decoded frame with its statistics (DR-44 (a)); see :meth:`_on_frame_decoded`."""
        if self._requested is None or outcome.requested != self._requested:
            return
        self._requested = None
        if outcome.pts is None:  # the decode failed; the shell shows its error (owner shell.frame)
            self._session.set_statistics(self._shown_statistics)
            if self._shown_pts is not None:
                self._wanted_pts = self._shown_pts
                self._follow(self._shown_pts)
            return
        self._shown_pts = outcome.pts
        if outcome.pts == outcome.requested:
            self._shown_statistics = self._supplied
            return
        self._session.set_statistics(None)  # never another frame's statistics
        self._shown_statistics = None
        self._wanted_pts = outcome.pts
        self._follow(outcome.pts)
        if self._session.analysis().phase == "complete" and self._requested_seq == self._intent:
            self._request("fix", outcome.pts)  # only for the frame of the newest intent

    def _follow(self, pts: int) -> None:
        """Move the handle and the time label to the frame the shell shows (not under a drag)."""
        if self._dragging:  # the hand holds the handle: it stays where the user put it
            return
        self._slider_pts = pts
        if self._pts:
            with _blocked(self._slider):
                self._slider.setValue(self._index_of(pts))
        self._update_time(pts)

    def _switch(self) -> None:
        """Completion: switch the shown frame from the provisional to the smoothed statistics."""
        if self._dragging or self._wanted_pts is None:
            return
        self._request("commit", self._wanted_pts)

    # Controls.

    def _update_controls(self, *_: object) -> None:
        """Set the buttons, the bar and the status text from the session's analysis state."""
        state = self._session.analysis()
        run = self._run
        source_is_video = self._source is not None
        self._cancel.setEnabled(run is not None and run.reason is None and state.phase == "running")
        self._analyse.setEnabled(
            source_is_video and run is None and state.phase in ("none", "cancelled", "failed")
        )
        if state.phase == "running":
            if state.total:
                self._bar.setRange(0, state.total)
                self._bar.setValue(min(state.done, state.total))
            else:
                self._bar.setRange(0, 0)
            text = state.message or LABEL_ANALYSING
            self._status.setText(
                f"{text}: {state.done}/{'?' if state.total is None else state.total}"
            )
        else:
            self._bar.setRange(0, 1)
            self._bar.setValue(1 if state.phase == "complete" else 0)
            self._status.setText(state.message if source_is_video else "")


def install_timeline(window: ShellWindow, analysis: AnalysisFactory | None = None) -> None:
    """Attach the timeline panel to ``Area.TIMELINE`` (WP4.3 passes the adapter over WP3.11).

    Args:
        window: The main window.
        analysis: Builds the analysis of each opened video; the stub analysis when None.
    """
    factory = analysis or stub_analysis_factory
    window.attach(Area.TIMELINE, lambda context: TimelinePanel(context, factory), title=PANEL_TITLE)
