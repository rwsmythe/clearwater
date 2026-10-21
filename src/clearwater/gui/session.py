"""The shell's session: the state panels read and change (main thread only).

:class:`ShellSession` implements :class:`clearwater.gui.contract.Session`. The public setters
are the contract's; the underscore methods are the shell's own (open a source, show a decoded
frame, report the backend) and are not for panels.
"""

from __future__ import annotations

from collections.abc import Mapping

from PySide6.QtCore import QObject, Signal

from clearwater.interfaces import CorrectionMethod, Image, ParameterSet, Settings, Statistics

from .contract import AnalysisState, Engines, OpenedSource, Session


class ShellSession(Session):
    """The session of one main window.

    Besides the contract's signals it has one internal signal, ``image_changed()``, emitted when
    the current image changes (a new source, a decoded frame, ``preview.show``).

    Args:
        engines: The injected engines (``methods`` resolves ``parameters.method``).
        settings: The settings loaded at start-up.
        parameters: The parameter set chosen at start-up; its method is in ``engines.methods``.
        parent: The Qt parent.
    """

    image_changed = Signal()

    def __init__(
        self,
        engines: Engines,
        settings: Settings,
        parameters: ParameterSet,
        parent: QObject | None = None,
    ) -> None:
        """Create the session."""
        super().__init__(parent)
        if parameters.method not in engines.methods:
            raise ValueError(f"method {parameters.method!r} is not available")
        self._engines = engines
        self._settings = settings
        self._parameters = parameters
        self._source: OpenedSource | None = None
        self._analysis = AnalysisState()
        self._statistics: Mapping[str, Statistics] | None = None
        self._position: int | None = None
        self._backend = "-"
        self._preview_backend = "-"
        self._image: Image | None = None
        self._image_token = 0
        self._statistics_revision = 0

    # The contract's getters.

    def source(self) -> OpenedSource | None:
        """Return the open source, or None."""
        return self._source

    def parameters(self) -> ParameterSet:
        """Return the current parameter set (IF-9)."""
        return self._parameters

    def settings(self) -> Settings:
        """Return the current settings (IF-10)."""
        return self._settings

    def method(self) -> CorrectionMethod:
        """Return the method named by ``parameters().method`` (IF-3)."""
        return self._engines.methods[self._parameters.method]

    def analysis(self) -> AnalysisState:
        """Return the analysis state of the open source (AD-15)."""
        return self._analysis

    def statistics(self) -> Mapping[str, Statistics] | None:
        """Return the supplied statistics, or None when the preview measures its own (D108)."""
        return self._statistics

    def position(self) -> int | None:
        """Return the current position in pts ticks, or None when no video is open."""
        return self._position

    def backend(self) -> str:
        """Return the AD-9 reason of the latest full-resolution selection; ``"-"`` before any."""
        return self._backend

    def current_image(self) -> Image | None:
        """Return the full-resolution host image the preview shows, or None."""
        return self._image

    # The contract's setters.

    def set_parameters(self, parameters: ParameterSet) -> None:
        """Replace the parameter set and emit ``parameters_changed``.

        Args:
            parameters: The new set.

        Raises:
            ValueError: The method is not one of ``Engines.methods``.
        """
        if parameters.method not in self._engines.methods:
            raise ValueError(f"method {parameters.method!r} is not available")
        self._parameters = parameters
        self.parameters_changed.emit(parameters)

    def set_settings(self, settings: Settings) -> None:
        """Replace the settings and emit ``settings_changed``.

        Args:
            settings: The new settings.
        """
        self._settings = settings
        self.settings_changed.emit(settings)

    def set_position(
        self, pts_ticks: int, *, statistics: Mapping[str, Statistics] | None = None
    ) -> None:
        """Move to a video frame and set the statistics it is rendered with.

        Emits ``position_changed`` then ``statistics_changed``; the shell decodes the frame and
        renders it with these statistics (never the previous frame with them).

        Args:
            pts_ticks: The frame's presentation time in stream ticks.
            statistics: The statistics for that frame, or None for its own (D108).

        Raises:
            RuntimeError: No video is open.
        """
        if self._source is None or self._source.kind != "video":
            raise RuntimeError("set_position needs an open video")
        self._position = int(pts_ticks)
        self._set_statistics(statistics)
        self.position_changed.emit(self._position)
        self.statistics_changed.emit()

    def set_analysis(self, state: AnalysisState) -> None:
        """Set the analysis state and emit ``analysis_changed``.

        Args:
            state: The new state.
        """
        self._analysis = state
        self.analysis_changed.emit(state)

    def set_statistics(self, statistics: Mapping[str, Statistics] | None) -> None:
        """Supply the statistics of the current image and emit ``statistics_changed``.

        Args:
            statistics: Stage name -> statistics, or None for the image's own (D108).
        """
        self._set_statistics(statistics)
        self.statistics_changed.emit()

    # The shell's own.

    def image_token(self) -> int:
        """Return a number that changes with every new current image."""
        return self._image_token

    def statistics_revision(self) -> int:
        """Return a number that changes with every statistics update, also to the same object.

        A caller may change a mapping in place and set it again; the revision, not the object's
        identity, tells the preview's render memo that the statistics changed.
        """
        return self._statistics_revision

    def _set_statistics(self, statistics: Mapping[str, Statistics] | None) -> None:
        """Record supplied statistics and bump the revision (no signal)."""
        self._statistics = statistics
        self._statistics_revision += 1

    def preview_backend(self) -> str:
        """Return the reason of the latest preview-size selection; ``"-"`` before any."""
        return self._preview_backend

    def _open(self, source: OpenedSource | None) -> None:
        """Make ``source`` the open source; reset analysis, statistics, position and backend."""
        self._source = source
        self._analysis = AnalysisState()
        self._set_statistics(None)
        self._backend = self._preview_backend = "-"
        frame_ticks = getattr(source.image, "pts_ticks", None) if source is not None else None
        self._position = frame_ticks if isinstance(frame_ticks, int) else None
        self._set_image(None if source is None else source.image)
        self.source_changed.emit(source)
        self.analysis_changed.emit(self._analysis)
        self.statistics_changed.emit()

    def _set_image(self, image: Image | None) -> None:
        """Make ``image`` the current image and emit ``image_changed``."""
        self._image = image
        self._image_token += 1
        self.image_changed.emit()

    def _show(self, image: Image, statistics: Mapping[str, Statistics] | None) -> None:
        """Set the current image and its statistics together (``preview.show``)."""
        self._set_statistics(statistics)
        self._set_image(image)
        self.statistics_changed.emit()

    def _set_backend(self, full_reason: str, preview_reason: str) -> None:
        """Record the latest selections; emit ``backend_changed`` with the full-size reason."""
        self._preview_backend = preview_reason
        self._backend = full_reason
        self.backend_changed.emit(full_reason)
