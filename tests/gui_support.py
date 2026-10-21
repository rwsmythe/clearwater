"""Shared helpers for the WP3.16 GUI tests: headless Qt, images, test methods, a capturing presenter.

Importing this module sets ``QT_QPA_PLATFORM=offscreen`` (unless the developer set another
platform) before any PySide6 import, so every GUI test runs headless (WP3.16 ruling 3). Every
``test_gui_*.py`` imports it first.
"""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import threading  # noqa: E402
import time  # noqa: E402
from collections.abc import Callable, Mapping, Sequence  # noqa: E402
from fractions import Fraction  # noqa: E402
from pathlib import Path  # noqa: E402
from typing import Any  # noqa: E402

import numpy as np  # noqa: E402
import pytest  # noqa: E402

from clearwater.config import Locations  # noqa: E402
from clearwater.gui import Engines, Message, stub_engines  # noqa: E402
from clearwater.gui.shell import MainWindow  # noqa: E402
from clearwater.interfaces import (  # noqa: E402
    ColorDescription,
    Frame,
    Image,
    Parameter,
    PhotoMetadata,
    Stage,
    Statistics,
)

SRGB = ColorDescription("bt709", "srgb", "identity", "full", 8, False, None)
UNTAGGED = ColorDescription("bt709", "srgb", "identity", "full", 8, True, None)
VIDEO_TAGS = ColorDescription("bt709", "bt709", "bt709", "limited", 8, False, None)
META = PhotoMetadata("jpeg", None, 1)


def pixels(height: int, width: int, seed: int = 0) -> np.ndarray:
    """Random float32 RGB pixels in [0, 1]."""
    rng = np.random.default_rng(seed)
    return rng.random((height, width, 3), dtype=np.float32)


def image(height: int, width: int, *, seed: int = 0, color: ColorDescription = SRGB) -> Image:
    """A host image of random pixels."""
    return Image(pixels(height, width, seed), "cpu", color, True)


def frame(
    height: int, width: int, *, ticks: int, seed: int = 0, color: ColorDescription = VIDEO_TAGS
) -> Frame:
    """A host frame at ``ticks`` on a 1/90000 time base."""
    base = Fraction(1, 90000)
    return Frame(pixels(height, width, seed), "cpu", color, True, ticks * base, ticks, base, 0)


def locations(tmp_path: Path) -> Locations:
    """App-data folders under ``tmp_path``."""
    return Locations(config_dir=tmp_path / "config", cache_dir=tmp_path / "cache")


class CapturingPresenter:
    """A MessagePresenter that records instead of showing a dialog."""

    def __init__(self) -> None:
        self.messages: list[Message] = []
        self.cleared: list[str | None] = []

    def present(self, message: Message) -> None:
        self.messages.append(message)

    def clear(self, severity: str | None = None) -> None:
        self.cleared.append(severity)
        self.messages = [
            m
            for m in self.messages
            if m.severity == "refusal" or (severity is not None and m.severity != severity)
        ]

    def of(self, severity: str) -> list[Message]:
        return [m for m in self.messages if m.severity == severity]


ONE_STAGE = (Stage("only", ("mean",), ("mean",), ("level",), (), False),)


class LevelMethod:
    """A test method: ``render`` fills the image with ``level`` after an optional delay.

    Records the thread of every ``analyze`` and ``render`` call and every rendered level.
    """

    def __init__(
        self,
        *,
        method_id: str = "level",
        delay_s: float = 0.0,
        busy: Callable[[], None] | None = None,
    ) -> None:
        self.id = method_id
        self.label = "Level"
        self.parameters = (
            Parameter("level", "float", 0.5, 0.0, 1.0, None, "basic", "Level", "", 0.5),
        )
        self.stages = ONE_STAGE
        self.delay_s = delay_s
        self.busy = busy
        self.threads: list[threading.Thread] = []
        self.rendered: list[float] = []
        self.analysed = 0
        self.lock = threading.Lock()

    def analyze(
        self, stage: str, image: Image, params: Mapping[str, Any], earlier: Mapping[str, Statistics]
    ) -> Statistics:
        with self.lock:
            self.threads.append(threading.current_thread())
            self.analysed += 1
        return {"mean": np.asarray(image.pixels).mean(axis=(0, 1))}

    def render(
        self, image: Image, params: Mapping[str, Any], statistics: Mapping[str, Statistics]
    ) -> Image:
        with self.lock:
            self.threads.append(threading.current_thread())
        if self.busy is not None:
            self.busy()
        if self.delay_s:
            time.sleep(self.delay_s)
        level = float(params["level"])
        with self.lock:
            self.rendered.append(level)
        out = np.full_like(np.asarray(image.pixels), level, dtype=np.float32)
        return Image(out, image.device, image.color, image.orientation_applied)

    def closed_form(
        self,
        stage: str,
        params: Mapping[str, Any],
        earlier: Mapping[str, Statistics],
        measured: Statistics,
    ) -> Statistics | None:
        return None


def busy_numpy(seconds: float) -> Callable[[], None]:
    """A CPU-heavy NumPy load of about ``seconds`` (BLAS releases the GIL)."""

    def work() -> None:
        matrix = np.random.default_rng(1).random((600, 600))
        end = time.perf_counter() + seconds
        while time.perf_counter() < end:
            matrix = np.tanh(matrix @ matrix / 600.0)

    return work


@pytest.fixture
def make_window(qtbot: Any, tmp_path: Path) -> Callable[..., MainWindow]:
    """Build a MainWindow on ``tmp_path`` folders with a capturing presenter; closed at teardown."""

    def build(
        engines: Engines | None = None,
        *,
        presenter: CapturingPresenter | None = None,
        size: tuple[int, int] = (800, 600),
        choose_file: Callable[[Any], Path | None] | None = None,
        where: Path | None = None,
    ) -> MainWindow:
        window = MainWindow(
            engines or stub_engines(),
            locations(where or tmp_path),
            presenter=presenter or CapturingPresenter(),
            choose_file=choose_file,
        )
        qtbot.addWidget(window)
        window.resize(*size)
        window.show()
        qtbot.waitExposed(window)
        return window

    return build


def presenter_of(window: MainWindow) -> CapturingPresenter:
    """The capturing presenter of a test window."""
    presenter = window.presenter
    assert isinstance(presenter, CapturingPresenter)
    return presenter


def open_and_wait(qtbot: Any, window: MainWindow, path: Path, timeout_ms: int = 10000) -> None:
    """Open a file and wait until the open finished and any render settled."""
    window.open_path(path)
    qtbot.waitUntil(lambda: not window.opening(), timeout=timeout_ms)
    wait_idle(qtbot, window, timeout_ms)


def wait_idle(qtbot: Any, window: MainWindow, timeout_ms: int = 10000) -> None:
    """Wait until the preview and frame workers are idle and their results delivered."""
    qtbot.waitUntil(window.controller.idle, timeout=timeout_ms)
    qtbot.wait(30)


def photo_engines(
    photos: Mapping[Path, Image], methods: Mapping[str, Any] | None = None, **kwargs: Any
) -> Engines:
    """Stub engines serving these photos."""
    return stub_engines(photos={p: (img, META) for p, img in photos.items()}, methods=methods, **kwargs)


def video_engines(frames: Sequence[Frame], **kwargs: Any) -> Engines:
    """Stub engines serving these frames for every probed path."""
    return stub_engines(frames=frames, **kwargs)
