"""The PySide6 interface (plan 8.1 module ``gui``; WP3.16 to WP3.20).

WP3.16 provides the main window, the split-view preview and its worker, the G10 messages, the
AD-9 status bar and the Qt job runner; :mod:`clearwater.gui.contract` is the attachment contract
the WP3.17 to WP3.20 panels are written against. Those packages add sibling modules and may
append exports here, nothing else. This package reaches correction methods only through IF-3
and imports nothing from ``clearwater.methods`` and no GPU library.
"""

from __future__ import annotations

from .contract import (
    AnalysisPhase,
    AnalysisState,
    Area,
    Engines,
    JobHandle,
    JobRunner,
    Message,
    MessagePresenter,
    MessageSeverity,
    OpenedSource,
    PanelFactory,
    PreviewSurface,
    ReasonAction,
    SelectBackend,
    Session,
    SettingsDialogFactory,
    ShellActions,
    ShellContext,
    ShellWindow,
)
from .engines import default_engines, stub_engines
from .shell import MainWindow, run

__all__ = [
    "AnalysisPhase",
    "AnalysisState",
    "Area",
    "Engines",
    "JobHandle",
    "JobRunner",
    "MainWindow",
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
    "default_engines",
    "run",
    "stub_engines",
]
