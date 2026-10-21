"""WP3.16 attachment contract (task 2): panels in each Area, the session, the settings dialog.

Covers the task-8 row "the contract": a dummy panel attached to each ``Area`` receives a
``ShellContext``, reacts to ``parameters_changed`` and calls ``set_parameters``; a dummy
settings dialog opens from ``actions.settings``. Also the Session contract and ``preview.show``.
"""

# The shared fixture ``make_window`` is imported from gui_support and used as a parameter.
# ruff: noqa: F401, F811

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from PySide6.QtWidgets import QDialog, QDockWidget, QLabel, QWidget

import clearwater.gui as gui
import gui_support
from clearwater.config import new_parameter_set
from clearwater.gui import (
    AnalysisState,
    Area,
    JobRunner,
    MessagePresenter,
    PreviewSurface,
    ReasonAction,
    Session,
    ShellContext,
    ShellWindow,
)
from clearwater.gui.imaging import image_bytes
from clearwater.interfaces import ParameterSet
from gui_support import (
    LevelMethod,
    frame,
    image,
    make_window,
    open_and_wait,
    photo_engines,
    video_engines,
    wait_idle,
)

pytestmark = pytest.mark.gui

CONTRACT_NAMES = {
    "AnalysisPhase",
    "AnalysisState",
    "Area",
    "Engines",
    "JobHandle",
    "JobRunner",
    "Message",
    "MessagePresenter",
    "MessageSeverity",
    "OpenedSource",
    "PanelFactory",
    "PreviewSurface",
    "ReasonAction",
    "SelectBackend",
    "Session",
    "SettingsDialogFactory",
    "ShellActions",
    "ShellContext",
    "ShellWindow",
}


def test_the_contract_names_are_exported() -> None:
    assert set(gui.__all__) >= CONTRACT_NAMES
    assert {a.name for a in Area} == {"PARAMETERS", "TIMELINE", "JOBS"}
    signals = (
        "source_changed",
        "parameters_changed",
        "settings_changed",
        "position_changed",
        "statistics_changed",
        "backend_changed",
        "analysis_changed",
    )
    for name in signals:
        assert hasattr(Session, name)


class DummyPanel(QLabel):
    def __init__(self, context: ShellContext) -> None:
        super().__init__("dummy")
        self.context = context
        self.seen: list[ParameterSet] = []
        context.session.parameters_changed.connect(self.seen.append)


def test_a_panel_in_each_area_gets_the_context_and_drives_the_session(make_window, qtbot) -> None:
    method = LevelMethod()
    window = make_window(
        photo_engines({}, methods={"level": method}, frames=[frame(48, 64, ticks=0)])
    )
    panels: dict[Area, DummyPanel] = {}
    for area in Area:
        panel = window.attach(area, DummyPanel, title=f"{area.value} panel")
        assert isinstance(panel, DummyPanel)
        panels[area] = panel
    second = window.attach(Area.PARAMETERS, DummyPanel, title="advanced")
    for panel in (*panels.values(), second):
        ctx = panel.context
        assert isinstance(ctx, ShellContext)
        assert ctx.window is window and ctx.session is window.session
        assert ctx.locations.config_dir.is_dir() and ctx.presets.folder == ctx.locations.presets_dir
        for protocol, obj in (
            (JobRunner, ctx.jobs),
            (MessagePresenter, ctx.messages),
            (PreviewSurface, window.preview),
        ):
            missing = [n for n in dir(protocol) if not n.startswith("_") and not hasattr(obj, n)]
            assert missing == [], (protocol.__name__, missing)
        assert isinstance(ctx.actions.export, ReasonAction)
        assert isinstance(window, ShellWindow)
    docks = window.findChildren(QDockWidget)
    assert {d.windowTitle() for d in docks} == {"parameters panel", "advanced", "jobs panel"}
    advanced = next(d for d in docks if d.windowTitle() == "advanced")
    qtbot.waitUntil(lambda: bool(window.tabifiedDockWidgets(advanced)), timeout=2000)
    timeline = panels[Area.TIMELINE]
    assert not timeline.isVisibleTo(window)
    open_and_wait(qtbot, window, Path("clip.mp4"))
    assert timeline.isVisibleTo(window)

    new = new_parameter_set("level", {"level": 0.75})
    panels[Area.PARAMETERS].context.session.set_parameters(new)
    for panel in (*panels.values(), second):
        assert panel.seen == [new]
    assert window.session.parameters() is new
    with pytest.raises(ValueError, match="not available"):
        window.session.set_parameters(new_parameter_set("nope", {}))


def test_settings_dialog_opens_from_the_action(make_window, qtbot) -> None:
    window = make_window()
    assert not window.shell_actions.settings.isEnabled()
    opened: list[QDialog] = []

    def factory(context: ShellContext) -> QDialog:
        dialog = QDialog(context.window)
        opened.append(dialog)
        return dialog

    window.set_settings_dialog(factory)
    assert window.shell_actions.settings.isEnabled()
    window.shell_actions.settings.trigger()
    assert len(opened) == 1 and opened[0].isVisible() and opened[0].isModal()
    opened[0].reject()


def test_session_setters_emit_and_reset_on_a_new_source(make_window, qtbot) -> None:
    frames = [frame(48, 64, ticks=t * 3000, seed=t) for t in range(4)]
    window = make_window(video_engines(frames))
    session = window.session
    with pytest.raises(RuntimeError, match="open video"):
        session.set_position(0)
    open_and_wait(qtbot, window, Path("clip.mp4"))
    events: list[tuple[str, object]] = []
    session.position_changed.connect(lambda v: events.append(("position", v)))
    session.statistics_changed.connect(lambda: events.append(("statistics", None)))
    session.analysis_changed.connect(lambda v: events.append(("analysis", v)))
    stats = {"white_balance": {"means": np.zeros(3), "gains": np.ones(3)}, "fusion": {}}
    session.set_position(2**40)
    assert events[:2] == [("position", 2**40), ("statistics", None)]
    events.clear()
    session.set_position(6000, statistics=stats)
    wait_idle(qtbot, window)
    assert session.position() == 6000 and session.statistics() is stats
    assert session.current_image() is frames[2]
    session.set_analysis(AnalysisState("running", 1, 4))
    assert session.analysis().done == 1
    open_and_wait(qtbot, window, Path("other.mp4"))
    assert session.analysis() == AnalysisState() and session.statistics() is None
    assert session.position() == 0


def test_preview_show_and_show_proxy(make_window, qtbot) -> None:
    method = LevelMethod()
    path = Path("p.png")
    window = make_window(photo_engines({path: image(40, 60)}, methods={"level": method}))
    open_and_wait(qtbot, window, path)
    other = image(40, 60, seed=9)
    window.preview.show(other)
    wait_idle(qtbot, window)
    assert window.session.current_image() is other
    proxy = np.full((20, 30, 3), 10, dtype=np.uint8)
    corrected = np.full((20, 30, 3), 200, dtype=np.uint8)
    window.preview.show_proxy(proxy, corrected)
    widget = window.preview_widget
    assert image_bytes(widget.before_image())[0, 0].tolist() == [10, 10, 10]
    assert image_bytes(widget.after_image())[0, 0].tolist() == [200, 200, 200]
    window.preview.show_proxy(proxy)
    assert image_bytes(widget.after_image())[0, 0].tolist() == [10, 10, 10]


def test_shell_window_base_methods_are_abstract() -> None:
    base = QWidget  # ShellWindow and Session are Qt classes whose methods the shell implements
    assert issubclass(ShellWindow, base)
    session = Session()
    with pytest.raises(NotImplementedError):
        session.source()
