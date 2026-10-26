"""WP3.18 analysis seam: the stub analysis honours the ``ClipAnalysis`` contract.

Covers brief task 2 and the task-6 rows "pts keys" (DR-23, VFR), "D98" (one stage), the stub's
thread and cancel rules and the dependency rule for the two new modules.
"""

from __future__ import annotations

import ast
import dataclasses
import threading
import time
from collections.abc import Mapping
from fractions import Fraction
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from clearwater.cache import cache_key
from clearwater.config import new_parameter_set
from clearwater.gui import OpenedSource, imaging
from clearwater.gui.analysis_service import (
    ClipAnalysis,
    StubClipAnalysis,
    stub_analysis_factory,
)
from clearwater.gui.engines import stub_engines, stub_probe
from clearwater.interfaces import Frame, Image, Parameter, ProbeResult, Statistics
from clearwater.interfaces.stubs import StubCorrectionMethod, StubProgress
from gui_support import ONE_STAGE, VIDEO_TAGS

VFR = (0, 1001, 3003, 4004, 7007)
BASE = Fraction(1, 90000)


def _frame(ticks: int, level: float) -> Any:
    pixels = np.full((12, 16, 3), level, np.float32)
    return Frame(pixels, "cpu", VIDEO_TAGS, True, ticks * BASE, ticks, BASE, 0)


def _level(index: int) -> float:
    return round((0.1 + 0.15 * index) * 255) / 255


class ParamMethod:
    """One stage; ``analyze`` is the frame mean times ``level`` and may wait on a gate."""

    id = "pm"
    label = "Param"

    def __init__(self, gate: threading.Event | None = None) -> None:
        self.parameters = (
            Parameter("level", "float", 1.0, 0.0, 2.0, None, "basic", "Level", "", 1.0),
        )
        self.stages = ONE_STAGE
        self.gate = gate
        self.entered = threading.Event()
        self.threads: set[threading.Thread] = set()

    def analyze(
        self, stage: str, image: Image, params: Mapping[str, Any], earlier: Mapping[str, Statistics]
    ) -> Statistics:
        self.threads.add(threading.current_thread())
        self.entered.set()
        if self.gate is not None:
            self.gate.wait(5)
        return {"mean": np.asarray(image.pixels).mean(axis=(0, 1)) * float(params["level"])}

    def render(
        self, image: Image, params: Mapping[str, Any], statistics: Mapping[str, Statistics]
    ) -> Image:
        return image

    def closed_form(
        self,
        stage: str,
        params: Mapping[str, Any],
        earlier: Mapping[str, Statistics],
        measured: Statistics,
    ) -> Statistics | None:
        return None


def _setup(tmp_path: Path, method: Any, ticks: tuple[int, ...] = VFR, **kwargs: Any):
    clip = tmp_path / "clip.mp4"
    clip.write_bytes(b"clip")
    frames = [_frame(t, _level(i)) for i, t in enumerate(ticks)]
    calls: list[int] = []
    base_probe = stub_probe(clip)
    probe: ProbeResult = dataclasses.replace(
        base_probe, video=dataclasses.replace(base_probe.video, nb_frames=len(ticks))
    )
    engines = stub_engines(frames=frames, methods={method.id: method}, **kwargs)
    original = engines.video_source.frames

    def counting(*args: Any, **kw: Any) -> Any:
        calls.append(1)
        return original(*args, **kw)

    object.__setattr__(engines.video_source, "frames", counting)
    source = OpenedSource(clip, "video", frames[0], None, probe, ())
    return source, engines, calls


def _params(level: float = 1.0) -> Any:
    return new_parameter_set("pm", {"level": level})


def _mean(stats: Mapping[str, Statistics] | None) -> float:
    assert stats is not None
    return float(np.asarray(stats["only"]["mean"])[0])


class CancelAfter:
    """Progress that reports cancelled once ``n`` reports have been made."""

    def __init__(self, n: int) -> None:
        self.n = n
        self.reports: list[tuple[int, int | None, str]] = []

    def report(self, done: int, total: int | None, message: str) -> None:
        self.reports.append((done, total, message))

    def cancelled(self) -> bool:
        return len(self.reports) >= self.n


def test_the_stub_decodes_stores_proxies_and_publishes_statistics_by_pts(tmp_path: Path) -> None:
    method = ParamMethod()
    source, engines, _ = _setup(tmp_path, method)
    analysis = stub_analysis_factory(source, method, engines)
    assert isinstance(analysis, StubClipAnalysis)
    assert analysis.pts() == () and analysis.statistics(VFR[0]) is None
    progress = StubProgress()
    analysis.run(_params(), progress)
    assert analysis.pts() == VFR
    assert progress.reports[0] == (1, len(VFR), "Analysing")
    key = cache_key(source.path)
    for index, ticks in enumerate(VFR):  # DR-23: keyed by pts, irregular spacing
        proxy = analysis.proxy(ticks)
        assert proxy.dtype == np.uint8 and proxy.shape == (12, 16, 3)
        assert np.array_equal(proxy, engines.cache.proxy(key, ticks))
        assert _mean(analysis.statistics(ticks)) == pytest.approx(_level(index), abs=1e-6)
    assert analysis.statistics(12345) is None
    with pytest.raises(KeyError):
        analysis.proxy(12345)


def test_the_proxy_is_the_statistics_proxy_quantised(tmp_path: Path) -> None:
    method = ParamMethod()
    source, engines, _ = _setup(tmp_path, method)
    analysis = stub_analysis_factory(source, method, engines)
    analysis.run(_params(), StubProgress())
    first = source.image.pixels
    k = imaging.statistics_factor(first.shape[0], first.shape[1])
    expected = imaging.to_display_uint8(imaging.downscale(np.asarray(first, np.float32), k))
    assert np.array_equal(analysis.proxy(VFR[0]), expected)


def test_statistics_are_none_until_a_run_completes_and_after_a_cancel(tmp_path: Path) -> None:
    method = ParamMethod()
    source, engines, calls = _setup(tmp_path, method)
    analysis = stub_analysis_factory(source, method, engines)
    cancelling = CancelAfter(2)
    analysis.run(_params(), cancelling)
    assert analysis.pts() == VFR[:2]  # the proxies stored so far stay
    assert analysis.statistics(VFR[0]) is None
    analysis.run(_params(), StubProgress())  # restarts after the cancel
    assert analysis.pts() == VFR and analysis.statistics(VFR[0]) is not None
    assert len(calls) == 2  # the decode pass restarted: the first never completed


def test_a_second_run_skips_the_decode_and_recomputes_under_the_new_parameters(
    tmp_path: Path,
) -> None:
    method = ParamMethod()
    source, engines, calls = _setup(tmp_path, method)
    analysis = stub_analysis_factory(source, method, engines)
    analysis.run(_params(1.0), StubProgress())
    before = _mean(analysis.statistics(VFR[2]))
    analysis.run(_params(0.5), StubProgress(), focus_pts=VFR[2])
    assert len(calls) == 1
    assert _mean(analysis.statistics(VFR[2])) == pytest.approx(before * 0.5, abs=1e-5)


def test_pts_and_statistics_never_wait_for_a_run_in_flight(tmp_path: Path) -> None:
    gate = threading.Event()
    method = ParamMethod(gate)
    source, engines, _ = _setup(tmp_path, method)
    analysis = stub_analysis_factory(source, method, engines)
    worker = threading.Thread(target=analysis.run, args=(_params(), StubProgress()))
    worker.start()
    assert method.entered.wait(5)  # the run is inside the measurement pass
    started = time.perf_counter()
    assert analysis.pts() == VFR and analysis.statistics(VFR[0]) is None
    assert analysis.proxy(VFR[1]).shape == (12, 16, 3)  # proxy may run while run does
    assert time.perf_counter() - started < 0.2
    gate.set()
    worker.join(5)
    assert analysis.statistics(VFR[0]) is not None
    assert method.threads == {worker}


def test_retarget_false_leaves_the_run_under_the_old_parameters(tmp_path: Path) -> None:
    gate = threading.Event()
    method = ParamMethod(gate)
    source, engines, _ = _setup(tmp_path, method)
    analysis = stub_analysis_factory(source, method, engines)
    worker = threading.Thread(target=analysis.run, args=(_params(1.0), StubProgress()))
    worker.start()
    assert method.entered.wait(5)
    assert analysis.retarget(_params(0.5)) is False
    gate.set()
    worker.join(5)
    assert _mean(analysis.statistics(VFR[0])) == pytest.approx(_level(0), abs=1e-5)


def test_retarget_true_makes_the_run_complete_under_the_new_parameters(tmp_path: Path) -> None:
    gate = threading.Event()
    method = ParamMethod(gate)
    source, engines, _ = _setup(tmp_path, method)
    analysis = StubClipAnalysis(source, method, engines, absorb=True)
    worker = threading.Thread(target=analysis.run, args=(_params(1.0), StubProgress()))
    worker.start()
    assert method.entered.wait(5)
    assert analysis.retarget(_params(0.5)) is True
    gate.set()
    worker.join(5)
    assert not worker.is_alive()
    assert _mean(analysis.statistics(VFR[0])) == pytest.approx(_level(0) * 0.5, abs=1e-5)


def test_retarget_with_no_run_in_flight_is_false_not_a_state_change(tmp_path: Path) -> None:
    method = ParamMethod()
    source, engines, _ = _setup(tmp_path, method)
    analysis = StubClipAnalysis(source, method, engines, absorb=True)
    assert analysis.retarget(_params(0.5)) is False
    analysis.run(_params(1.0), StubProgress())
    assert analysis.retarget(_params(0.5)) is False
    assert _mean(analysis.statistics(VFR[0])) == pytest.approx(_level(0), abs=1e-5)


def test_a_second_concurrent_run_is_refused(tmp_path: Path) -> None:
    gate = threading.Event()
    method = ParamMethod(gate)
    source, engines, _ = _setup(tmp_path, method)
    analysis = stub_analysis_factory(source, method, engines)
    worker = threading.Thread(target=analysis.run, args=(_params(), StubProgress()))
    worker.start()
    assert method.entered.wait(5)
    with pytest.raises(RuntimeError):
        analysis.run(_params(), StubProgress())
    gate.set()
    worker.join(5)


def test_a_three_stage_method_and_a_one_stage_method_both_complete(tmp_path: Path) -> None:
    stub = StubCorrectionMethod()
    source, engines, _ = _setup(tmp_path, stub)
    analysis = stub_analysis_factory(source, stub, engines)
    analysis.run(new_parameter_set("stub", {}), StubProgress())
    stats = analysis.statistics(VFR[0])
    assert stats is not None and tuple(stats) == tuple(s.name for s in stub.stages)
    one = ParamMethod()  # D98: a single stage
    source1, engines1, _ = _setup(tmp_path, one)
    analysis1 = stub_analysis_factory(source1, one, engines1)
    analysis1.run(_params(), StubProgress())
    assert tuple(analysis1.statistics(VFR[0]) or ()) == ("only",)


def test_the_factory_only_builds_and_a_photo_is_refused(tmp_path: Path) -> None:
    method = ParamMethod()
    source, engines, calls = _setup(tmp_path, method)
    analysis = stub_analysis_factory(source, method, engines)  # no decode, no stat
    assert calls == [] and analysis.pts() == ()
    photo = OpenedSource(tmp_path / "p.jpg", "photo", source.image, None, None, ())
    with pytest.raises(ValueError):
        stub_analysis_factory(photo, method, engines)


def test_a_protocol_conforming_object_is_accepted_by_the_type() -> None:
    def accepts(analysis: ClipAnalysis) -> ClipAnalysis:
        return analysis

    assert callable(accepts)


# The dependency rule for the two new modules.

GUI_DIR = Path(imaging.__file__).parent


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            names.add(node.module)
            names.update(f"{node.module}.{alias.name}" for alias in node.names)
    return names


@pytest.mark.parametrize("module", ["analysis_service.py", "timeline.py"])
def test_the_new_modules_import_neither_the_analysis_engine_nor_the_methods(module: str) -> None:
    for name in _imports(GUI_DIR / module):
        assert not name.startswith(("clearwater.analysis", "clearwater.methods", "cupy"))


def test_the_seam_module_imports_no_qt() -> None:
    assert not any(name.startswith("PySide6") for name in _imports(GUI_DIR / "analysis_service.py"))
