"""The attachment contract of the application shell (WP3.16 task 2).

WP3.17 (parameter panels and presets), WP3.18 (timeline and analysis), WP3.19 (batch queue and
export progress) and WP3.20 (settings) attach their widgets through these names and reach the
shell's state only through them. Types and signatures only: :class:`Session`,
:class:`ReasonAction` and :class:`ShellWindow` are Qt classes whose methods the shell implements
(``clearwater.gui.shell``); the protocols are implemented by the shell's own modules. Frozen at
the WP3.16 round-0 yield; additive only until the WP3.16 accept, then a change is a CHARC ruling.

Threading: every name here is used on the interface (main) thread only, except
:class:`Engines` members, which the shell calls from its worker threads, and the job callables a
panel passes to :meth:`JobRunner.run`, which run on a worker thread.
"""

from __future__ import annotations

import enum
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol

import numpy as np
from numpy.typing import NDArray
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QDialog, QMainWindow, QWidget

from clearwater.config import Locations, PresetStore
from clearwater.interfaces import (
    ArrayBackend,
    CorrectionMethod,
    Image,
    JobResult,
    ParameterSet,
    PhotoMetadata,
    PhotoSource,
    ProbeResult,
    Progress,
    ProxyCache,
    Settings,
    Statistics,
    VideoSink,
    VideoSource,
)


class Area(enum.Enum):
    """Where a panel attaches in the main window.

    Attributes:
        PARAMETERS: The right dock: WP3.17's Basic and Advanced panels (several panels in this
            area are tabbed in attach order).
        TIMELINE: Below the preview, inside the central area, shown only while a video is open:
            WP3.18 (several panels are stacked in attach order).
        JOBS: The bottom dock: WP3.19's queue and progress (tabbed in attach order).
    """

    PARAMETERS = "parameters"
    TIMELINE = "timeline"
    JOBS = "jobs"


type AnalysisPhase = Literal["none", "running", "complete", "cancelled", "failed"]
"""The phase of the open clip's analysis (AD-15)."""


@dataclass(frozen=True)
class AnalysisState:
    """The analysis state of the open source (AD-15), set by WP3.18 through the session.

    Export of a video is unavailable unless the phase is ``"complete"``; the export action's
    reason names the phase and, while running, the progress. A photo needs no analysis pass, so
    its phase stays ``"none"`` and does not block export.

    Attributes:
        phase: ``"none"`` (not started, or the source changed), ``"running"``, ``"complete"``,
            ``"cancelled"`` (export unavailable as before the analysis) or ``"failed"``.
        done: Units analysed so far (frames), while running.
        total: Total units, or None when unknown.
        message: A short status text, or the failure message when ``"failed"``.
    """

    phase: AnalysisPhase = "none"
    done: int = 0
    total: int | None = None
    message: str = ""


type MessageSeverity = Literal["refusal", "warning", "error"]
"""How a message is presented (G10): a refusal is modal; a warning or error is a banner."""


@dataclass(frozen=True)
class Message:
    """A user-facing message (G10).

    Attributes:
        severity: ``"refusal"`` (the file was not opened; a modal message naming the file),
            ``"warning"`` (the file is open and the user is told; a non-modal banner above the
            preview while the file stays open) or ``"error"`` (an action failed; a banner until
            it is cleared or the next success of that action).
        text: The message, ASCII-safe, naming the file where there is one.
        path: The file concerned, or None.
    """

    severity: MessageSeverity
    text: str
    path: Path | None = None


@dataclass(frozen=True)
class OpenedSource:
    """The photo or video the shell has open.

    One instance per successful open; it does not change while the file stays open (the frame
    at the current position is :meth:`Session.current_image`).

    Attributes:
        path: The file.
        kind: ``"photo"`` or ``"video"``.
        image: The full-resolution host image of a photo, or the first frame of a video, as
            decoded at open (device ``"cpu"``).
        metadata: The photo's metadata (IF-6), or None for a video.
        probe: The video's probe result (IF-5), or None for a photo.
        warnings: The G10 warnings shown for the file at open, in order.
    """

    path: Path
    kind: Literal["photo", "video"]
    image: Image
    metadata: PhotoMetadata | None
    probe: ProbeResult | None
    warnings: tuple[str, ...]


type SelectBackend = Callable[[Settings, int, int, str], tuple[ArrayBackend, str]]
"""IF-2 ``select_backend(settings, height, width, method_id) -> (backend, reason)``."""


@dataclass(frozen=True)
class Engines:
    """The engines the shell and the panels use, injected at start-up (stubs until WP4.3).

    Every member may be called from a worker thread and must not touch a Qt object.

    Attributes:
        photo_source: IF-6 photo reader (WP3.6).
        video_probe: Probes a video file (``clearwater.io.video.probe``, WP3.7).
        video_source: IF-5 frame source (WP3.9); only ``frames`` is used.
        video_sink: IF-5 sink; its ``capabilities`` feed WP3.20's encoder choice (D74).
        cache: IF-7 proxy cache (WP3.12), for WP3.18 and WP3.20; the shell does not use it.
        methods: Method id -> method (IF-3); the first entry is the default method.
        select_backend: IF-2 backend selection (WP3.1).
    """

    photo_source: PhotoSource
    video_probe: Callable[[Path], ProbeResult]
    video_source: VideoSource
    video_sink: VideoSink
    cache: ProxyCache
    methods: Mapping[str, CorrectionMethod]
    select_backend: SelectBackend


class Session(QObject):
    """The shell's state: the only place panels read and change it (main thread only).

    Every setter emits its signal synchronously when the value is set, also when it is equal to
    the previous one. Signals:

    - ``source_changed(object)``: the new :class:`OpenedSource`, or None when closed.
    - ``parameters_changed(object)``: the new :class:`~clearwater.interfaces.ParameterSet`.
    - ``settings_changed(object)``: the new :class:`~clearwater.interfaces.Settings`.
    - ``position_changed(object)``: the new position in pts ticks (a Python ``int``; declared
      ``object`` because pts ticks can exceed a C ``int``), video only.
    - ``statistics_changed()``: the supplied statistics were set or cleared.
    - ``backend_changed(str)``: the AD-9 reason of the latest full-resolution selection.
    - ``analysis_changed(object)``: the new :class:`AnalysisState`.
    """

    source_changed = Signal(object)
    parameters_changed = Signal(object)
    settings_changed = Signal(object)
    position_changed = Signal(object)
    statistics_changed = Signal()
    backend_changed = Signal(str)
    analysis_changed = Signal(object)

    def source(self) -> OpenedSource | None:
        """Return the open source, or None."""
        raise NotImplementedError

    def parameters(self) -> ParameterSet:
        """Return the current parameter set (IF-9)."""
        raise NotImplementedError

    def settings(self) -> Settings:
        """Return the current settings (IF-10)."""
        raise NotImplementedError

    def method(self) -> CorrectionMethod:
        """Return the method named by ``parameters().method`` (IF-3)."""
        raise NotImplementedError

    def analysis(self) -> AnalysisState:
        """Return the analysis state of the open source (AD-15)."""
        raise NotImplementedError

    def statistics(self) -> Mapping[str, Statistics] | None:
        """Return the supplied statistics, or None when the preview measures its own (D108)."""
        raise NotImplementedError

    def position(self) -> int | None:
        """Return the current position in pts ticks, or None when no video is open."""
        raise NotImplementedError

    def backend(self) -> str:
        """Return the AD-9 reason of the latest full-resolution selection; ``"-"`` before any."""
        raise NotImplementedError

    def current_image(self) -> Image | None:
        """Return the full-resolution host image the preview shows, or None.

        For a photo, ``source().image``; for a video, the frame at :meth:`position` once
        decoded.
        """
        raise NotImplementedError

    def set_parameters(self, parameters: ParameterSet) -> None:
        """Replace the parameter set; the preview re-renders (latest wins).

        Args:
            parameters: The new set; ``parameters.method`` must be a key of
                ``Engines.methods``.

        Raises:
            ValueError: The method is not one of ``Engines.methods``.
        """
        raise NotImplementedError

    def set_settings(self, settings: Settings) -> None:
        """Replace the settings; the backend is selected again (``force_cpu``, AD-9).

        The shell saves the settings once at close (with ``last_parameters``, D89); a panel
        that must persist a change at once (WP3.20's dialog) saves it itself.

        Args:
            settings: The new settings.
        """
        raise NotImplementedError

    def set_position(
        self, pts_ticks: int, *, statistics: Mapping[str, Statistics] | None = None
    ) -> None:
        """Move to a video frame; the shell decodes it off the interface thread and shows it.

        Args:
            pts_ticks: The frame's presentation time in stream ticks (D95); the first frame at
                or after it is shown.
            statistics: The statistics to render that frame with (WP3.18's smoothed ones), or
                None for the frame's own unsmoothed statistics (D108). Replaces the supplied
                statistics, as :meth:`set_statistics` does.

        Raises:
            RuntimeError: No video is open.
        """
        raise NotImplementedError

    def set_analysis(self, state: AnalysisState) -> None:
        """Set the analysis state (WP3.18); the shell updates ``actions.export`` from it (AD-15).

        Args:
            state: The new state. The shell resets it to ``AnalysisState()`` when the source
                changes.
        """
        raise NotImplementedError

    def set_statistics(self, statistics: Mapping[str, Statistics] | None) -> None:
        """Supply the statistics the current image is rendered with.

        Args:
            statistics: Stage name -> statistics for every stage of :meth:`method`, or None to
                return to the image's own unsmoothed statistics (D108). Cleared when the source
                changes.
        """
        raise NotImplementedError


class ReasonAction(QAction):
    """An action that is disabled with a reason shown as its tool tip and status tip (AD-15).

    ``actions.export`` is one. It is enabled only while no reason holds: the shell's own (no
    source open; a video whose analysis is not complete, with the progress) and the one set
    through :meth:`set_unavailable`. Call :meth:`set_unavailable`, never ``setEnabled``.
    """

    def set_unavailable(self, reason: str | None) -> None:
        """Set or clear the caller's reason; the export action starts with one (WP3.19 clears it).

        Args:
            reason: Why the action is unavailable, or None to clear it.
        """
        raise NotImplementedError

    def unavailable_reason(self) -> str | None:
        """Return the reason shown now, or None when the action is enabled."""
        raise NotImplementedError


@dataclass(frozen=True)
class ShellActions:
    """The shell's menu actions panels may use or connect to.

    Attributes:
        open: File > Open (G1); the shell handles it.
        export: File > Export; WP3.19 connects ``triggered`` and clears its reason.
        settings: Tools > Settings; opens the dialog of :meth:`ShellWindow.set_settings_dialog`.
        quit: File > Quit; closes the window (the close path saves the settings).
    """

    open: QAction
    export: ReasonAction
    settings: QAction
    quit: QAction


class PreviewSurface(Protocol):
    """The split-view preview (G2, D27, D41), as panels may drive it (main thread)."""

    def show(self, image: Image, statistics: Mapping[str, Statistics] | None = None) -> None:
        """Make ``image`` the current image and render it (latest wins).

        Equivalent to the shell's own display of a decoded frame: ``image`` becomes
        :meth:`Session.current_image` and ``statistics`` the supplied statistics.

        Args:
            image: A full-resolution host image (device ``"cpu"``).
            statistics: The statistics to render with, or None for the image's own unsmoothed
                statistics (D108).
        """
        ...

    def show_proxy(
        self, proxy: NDArray[np.uint8], corrected: NDArray[np.uint8] | None = None
    ) -> None:
        """Show a scrub proxy at once, scaled to the view, until the next rendered result (D72).

        Args:
            proxy: ``(H, W, 3)`` RGB, 8-bit: the original side of the split.
            corrected: The corrected side at the same size, or None to show ``proxy`` on both.
        """
        ...


class JobHandle(Protocol):
    """One job started by :meth:`JobRunner.run`."""

    def cancel(self) -> None:
        """Ask the job to stop: its ``Progress.cancelled()`` returns True from now on."""
        ...

    def is_running(self) -> bool:
        """Return True until the job's ``on_done`` has been called."""
        ...


class JobRunner(Protocol):
    """Runs IF-8 jobs on worker threads and reports back on the main thread (G9)."""

    def run(
        self,
        job: Callable[[Progress], JobResult],
        *,
        on_done: Callable[[JobResult], None],
        on_progress: Callable[[int, int | None, str], None] | None = None,
    ) -> JobHandle:
        """Start ``job`` on its own worker thread.

        Reports are coalesced: ``on_progress`` receives the latest undelivered report, at most
        once per job per delivery interval (the shell's runner: 50 ms), and the last report
        before completion always arrives before ``on_done``. An exception in ``job`` becomes a
        failed ``JobResult`` (``ok`` False, ``failure`` the exception text). Both callbacks run
        on the main thread; ``on_done`` runs exactly once.

        Args:
            job: The job; it must not touch a Qt object.
            on_done: Receives the result.
            on_progress: Receives ``(done, total, message)``, or None.

        Returns:
            The job's handle.
        """
        ...

    def cancel(self) -> None:
        """Cancel every running job."""
        ...

    def active(self) -> int:
        """Return how many jobs have not yet delivered ``on_done``."""
        ...

    def wait(self, timeout_s: float) -> bool:
        """Wait for every job thread to end, at most ``timeout_s`` seconds.

        Args:
            timeout_s: The longest wait.

        Returns:
            True when no job thread is left running.
        """
        ...


class MessagePresenter(Protocol):
    """Presents G10 messages; injectable so tests capture them without a blocking dialog."""

    def present(self, message: Message) -> None:
        """Show a message: a refusal modally, a warning or an error as a banner.

        Args:
            message: The message.
        """
        ...

    def clear(self, severity: MessageSeverity | None = None) -> None:
        """Remove banner messages.

        Args:
            severity: Only messages of this severity, or None for all.
        """
        ...


class ShellWindow(QMainWindow):
    """The main window, as panels see it (implemented by ``clearwater.gui.shell``).

    The menu actions are ``ShellContext.actions`` (``QWidget.actions()`` keeps its Qt meaning).
    """

    @property
    def preview(self) -> PreviewSurface:
        """The split-view preview."""
        raise NotImplementedError

    def attach(self, area: Area, factory: PanelFactory, *, title: str) -> QWidget:
        """Create a panel with ``factory(context)`` and place it in ``area``.

        Args:
            area: Where the panel goes.
            factory: Builds the panel; called once, on the main thread, with the shell context.
            title: The dock or group title.

        Returns:
            The panel the factory built.
        """
        raise NotImplementedError

    def set_settings_dialog(self, factory: SettingsDialogFactory) -> None:
        """Register the settings dialog (WP3.20); ``actions.settings`` opens it window-modally.

        Args:
            factory: Builds a new dialog each time the action is triggered.
        """
        raise NotImplementedError


@dataclass(frozen=True)
class ShellContext:
    """Everything a panel factory receives.

    Attributes:
        window: The main window.
        session: The shell's state.
        engines: The injected engines.
        locations: The app-data folders (``clearwater.config.Locations``, AD-25 (a)).
        presets: The preset store over ``locations.presets_dir``.
        jobs: The IF-8 job runner.
        messages: The G10 presenter.
        actions: The shell's menu actions.
    """

    window: ShellWindow
    session: Session
    engines: Engines
    locations: Locations
    presets: PresetStore
    jobs: JobRunner
    messages: MessagePresenter
    actions: ShellActions


type PanelFactory = Callable[[ShellContext], QWidget]
"""Builds a panel for :meth:`ShellWindow.attach`."""

type SettingsDialogFactory = Callable[[ShellContext], QDialog]
"""Builds the settings dialog for :meth:`ShellWindow.set_settings_dialog`."""
