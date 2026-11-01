"""V6 and V18 acceptance on the running shell with real video sources.

The untagged clip is the unchanged committed fixture. The V18 source is the
guarded GX011627 session trim; only the orchestrator runs these GUI nodes.
App data, proxy caches and outputs stay under each node's ``tmp_path``.
"""

# The imported make_app fixture is requested by the test functions.
# ruff: noqa: F401, F811

from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from numpy.typing import NDArray

import gui_support
from acceptance_support import assert_names_only, file_md5
from clearwater.app.main import Application
from clearwater.gui.imaging import image_bytes
from test_app_startup import (
    cpu_settings,
    latest_analysis,
    make_app,
    open_source,
    presenter,
    wait_analysis,
    wait_started,
)
from test_app_v8_v18 import HeldEngines

type MakeApp = Callable[..., Application]
type RecordProperty = Callable[[str, object], None]

pytestmark = [pytest.mark.gui, pytest.mark.usefixtures("ffmpeg_tools")]


def _assert_assumption_warning(texts: Sequence[str]) -> None:
    assert any("BT.709" in text and "limited" in text for text in texts), (
        "V6: real untagged video must show a BT.709 / limited warning",
        texts,
    )


def test_v6_real_untagged_shell_warns_bt709_limited(
    make_app: MakeApp,
    qtbot: Any,
    tmp_path: Path,
    sample: Callable[[str], Path],
    record_property: RecordProperty,
) -> None:
    """Open the real untagged file and require both D54 words in its warning."""
    path = sample("vid-untagged")
    digest = file_md5(path)
    out = tmp_path / "out"
    out.mkdir()
    application = make_app(cpu_settings(output_folder=out))
    wait_started(qtbot, application)
    try:
        # Real build_application, real probe and open_path: no stub probe or frame.
        open_source(qtbot, application, path)
        shown = presenter(application).of("warning")
        assert shown, "V6: real untagged video showed no warning"
        assert any(message.path == path or path.name in message.text for message in shown)
        texts = [message.text for message in shown]
        assert all(text.isascii() for text in texts)
        assert_names_only(texts, folders=[path.parent, tmp_path])
        record_property("source", path.name)
        record_property("warning_texts", texts)
        _assert_assumption_warning(texts)

        for wrong in (
            [],
            ["BT.709 assumed"],
            ["limited range assumed"],
            ["BT.709 LIMITED range assumed"],
        ):
            with pytest.raises(AssertionError, match="V6: real untagged video"):
                _assert_assumption_warning(wrong)
        record_property(
            "mutation_probe",
            "absent warning, either missing word and uppercase-only LIMITED rejected",
        )
    finally:
        assert file_md5(path) == digest, f"source changed: {path.name}"


def _assert_corrected_provisional(
    original: NDArray[np.uint8], provisional: NDArray[np.uint8]
) -> int:
    assert provisional.shape == original.shape, "V18: provisional/original geometry differs"
    maximum = int(np.abs(provisional.astype(np.int16) - original.astype(np.int16)).max())
    assert maximum > 0, "V18: provisional corrected frame is identical to the original"
    return maximum


@pytest.mark.footage
@pytest.mark.slow(reason="real-trim analysis and FFmpeg decode")
def test_v18_real_trim_preview_precedes_analysis_and_updates(
    make_app: MakeApp,
    qtbot: Any,
    tmp_path: Path,
    gx011627_trim: tuple[Path, int],
    record_property: RecordProperty,
) -> None:
    """Show corrected pixels during the held real analysis, then smoothed pixels."""
    path, frame_count = gx011627_trim
    digest = file_md5(path)
    out = tmp_path / "out"
    out.mkdir()
    hook = HeldEngines()
    application = make_app(cpu_settings(output_folder=out), engine_factory=hook)
    wait_started(qtbot, application)
    window = application.window
    rendered: list[Any] = []
    window.controller.rendered.connect(rendered.append)
    try:
        try:
            open_source(qtbot, application, path)
            qtbot.waitUntil(hook.mid_decode, timeout=60000)
            qtbot.waitUntil(lambda: bool(rendered) and window.controller.idle(), timeout=30000)
            assert hook.mid_decode(), "V18: analysis completed before provisional preview"
            assert window.session.analysis().phase == "running"
            assert window.session.statistics() is None
            provisional = window.preview_widget.after_image()
            assert provisional is not None, "V18: no corrected provisional frame shown"
            before_pixels = image_bytes(provisional)
            original = window.preview_widget.before_image()
            assert original is not None, "V18: no original frame shown for provisional comparison"
            original_pixels = image_bytes(original)
            provisional_max = _assert_corrected_provisional(original_pixels, before_pixels)
            record_property("provisional_original_pixel_change_max_255", provisional_max)
            with pytest.raises(
                AssertionError, match="V18: provisional corrected frame is identical"
            ):
                _assert_corrected_provisional(original_pixels, original_pixels.copy())
            record_property("provisional_mutation_probe", "uncorrected provisional copy rejected")
            before_count = len(rendered)
            before_pts = getattr(window.session.current_image(), "pts_ticks", None)
            assert isinstance(before_pts, int)
            record_property("provisional_analysis_phase", window.session.analysis().phase)
            record_property("provisional_render_count", before_count)
        finally:
            # Match the existing V18 hook's bounded lifetime, including failures.
            hook.release.set()

        wait_analysis(qtbot, application)
        qtbot.waitUntil(lambda: window.session.statistics() is not None, timeout=30000)
        qtbot.waitUntil(lambda: len(rendered) > before_count, timeout=30000)
        qtbot.waitUntil(window.controller.idle, timeout=30000)
        assert hook.ended and hook.advanced == frame_count
        after = window.preview_widget.after_image()
        assert after is not None, "V18: corrected frame disappeared after analysis"
        after_pixels = image_bytes(after)
        assert after_pixels.shape == before_pixels.shape
        pts = getattr(window.session.current_image(), "pts_ticks", None)
        assert isinstance(pts, int)
        assert pts == before_pts, "V18: a different frame cannot prove a statistics update"
        delta = np.abs(after_pixels.astype(np.int16) - before_pixels.astype(np.int16))
        maximum, mean = int(delta.max()), float(delta.mean())
        record_property("source", path.name)
        record_property("analysis_frame_count", frame_count)
        record_property("shown_pts_ticks", pts)
        record_property("preview_pixel_change_max_255", maximum)
        record_property("preview_pixel_change_mean_255", mean)
        assert maximum > 0, "V18: shown corrected pixels did not update after analysis"

        engine = latest_analysis(application)._engine
        assert engine is not None
        supplied = window.session.statistics()
        assert supplied is not None
        record = engine.smoothed_record(pts)
        assert list(supplied) == list(record)
        for stage in record:
            for name in record[stage]:
                assert np.array_equal(supplied[stage][name], record[stage][name]), (stage, name)
        record_property("shown_statistics", "equal to smoothed_record at the unchanged pts")
    finally:
        assert file_md5(path) == digest, f"source changed: {path.name}"
