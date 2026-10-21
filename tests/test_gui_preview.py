"""WP3.16 preview: the downscale rule, V8 harness, 1:1 exactness, latest wins, display colour.

Covers brief task 5, 6 and the task-8 rows "latest wins", "V8 harness", "1:1 exact" and the
planted "a stale render displayed" and "1:1 showing scaled pixels".
"""

# The shared fixture ``make_window`` is imported from gui_support and used as a parameter.
# ruff: noqa: F401, F811

from __future__ import annotations

import dataclasses
import math
import os
import subprocess
import sys
import threading
from pathlib import Path

import numpy as np
import pytest
from PySide6.QtGui import QColorSpace, QImage
from PySide6.QtWidgets import QWidget

import gui_support
from clearwater.config import new_parameter_set
from clearwater.gui import FrameOutcome, Message, imaging, render_worker
from clearwater.gui.imaging import (
    display_image,
    downscale,
    downscaled_size,
    image_bytes,
    preview_export_difference,
    statistics_factor,
    to_display_uint8,
    view_factor,
)
from clearwater.gui.messages import BannerWidget, DialogPresenter
from clearwater.gui.session import ShellSession
from clearwater.interfaces import ColorDescription, Image
from clearwater.interfaces.stubs import StubArrayBackend, StubCorrectionMethod
from gui_support import (
    LevelMethod,
    frame,
    image,
    make_window,
    open_and_wait,
    photo_engines,
    presenter_of,
    video_engines,
    wait_idle,
)

pytestmark = pytest.mark.gui


# The downscale rule (S3).


def test_downscale_divisible_is_the_block_mean() -> None:
    data = np.arange(4 * 6 * 3, dtype=np.float32).reshape(4, 6, 3)
    out = downscale(data, 2)
    assert out.shape == (2, 3, 3)
    assert out.dtype == np.float32
    expected = data.reshape(2, 2, 3, 2, 3).mean(axis=(1, 3))
    np.testing.assert_allclose(out, expected, rtol=0, atol=1e-6)


def test_downscale_edge_blocks_average_only_their_pixels() -> None:
    data = np.arange(5 * 7 * 3, dtype=np.float32).reshape(5, 7, 3)
    out = downscale(data, 3)
    assert out.shape == (2, 3, 3)
    np.testing.assert_allclose(out[1, 2], data[3:5, 6:7].mean(axis=(0, 1)), atol=1e-5)
    np.testing.assert_allclose(out[0, 2], data[0:3, 6:7].mean(axis=(0, 1)), atol=1e-5)
    np.testing.assert_allclose(out[1, 0], data[3:5, 0:3].mean(axis=(0, 1)), atol=1e-5)


def test_downscale_factor_one_is_the_input_and_zero_is_refused() -> None:
    data = np.zeros((3, 3, 3), dtype=np.float32)
    assert downscale(data, 1) is data
    with pytest.raises(ValueError, match="at least 1"):
        downscale(data, 0)


@pytest.mark.parametrize(
    ("height", "width", "k", "size"),
    [
        (2160, 3840, 4, (540, 960)),
        (2988, 5312, 5, (598, 1063)),
        (3024, 4032, 5, (605, 807)),
        (6048, 8064, 11, (550, 734)),
        (300, 400, 1, (300, 400)),
    ],
)
def test_statistics_proxy_figures(height: int, width: int, k: int, size: tuple[int, int]) -> None:
    assert statistics_factor(height, width) == k
    assert downscaled_size(height, width, k) == size


def test_view_factor_is_the_largest_that_still_covers_the_view() -> None:
    for height, width, shown_h, shown_w in [
        (3024, 4032, 600, 800),
        (2160, 3840, 540, 960),
        (2160, 3840, 541, 961.5),
        (1000, 1000, 333.3, 333.3),
        (100, 100, 100, 100),
        (100, 100, 250, 250),
    ]:
        k = view_factor(height, width, shown_h, shown_w)
        h, w = downscaled_size(height, width, k)
        assert k == 1 or (h >= shown_h and w >= shown_w)
        h2, w2 = downscaled_size(height, width, k + 1)
        assert h2 < shown_h or w2 < shown_w
    assert view_factor(2160, 3840, 540, 960) == 4
    assert view_factor(100, 100, 250, 250) == 1


# The V8 harness and the display conversion.


# view_factor at the boundaries (round-2 R2-2). Run in a child process with a timeout, so an
# unbounded loop fails the test instead of hanging the suite.

_VIEW_FACTOR_PROBE = """
import itertools, sys
from clearwater.gui import imaging
{plant}
images = [(1, 1), (1, 7), (16, 16), (4000, 6000), (6048, 8064)]
shown = (0.0, 0.5, 1.0, 2.0)
for (h, w), sh, sw in itertools.product(images, shown, shown):
    print(h, w, sh, sw, imaging.view_factor(h, w, sh, sw))
"""

_UNBOUNDED = """
import math
def unbounded(height, width, shown_height, shown_width):
    if shown_height <= 0 or shown_width <= 0:
        return 1
    k = max(1, math.floor(min(height / shown_height, width / shown_width)))
    while True:
        h, w = imaging.downscaled_size(height, width, k + 1)
        if h < shown_height or w < shown_width:
            return k
        k += 1
imaging.view_factor = unbounded
"""


def _view_factor_table(plant: str = "") -> list[list[str]]:
    code = _VIEW_FACTOR_PROBE.format(plant=plant)
    done = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, timeout=10, check=False
    )
    assert done.returncode == 0, done.stderr
    return [line.split() for line in done.stdout.splitlines()]


def _expected_factor(height: int, width: int, shown_h: float, shown_w: float) -> int:
    if shown_h <= 0 or shown_w <= 0:
        return 1

    def covers(k: int) -> bool:
        h, w = downscaled_size(height, width, k)
        return h >= shown_h and w >= shown_w

    return max((k for k in range(1, max(1, height, width) + 1) if covers(k)), default=1)


def test_view_factor_terminates_and_is_the_largest_covering_factor_at_the_boundaries() -> None:
    rows = _view_factor_table()
    assert len(rows) == 5 * 4 * 4
    for h, w, sh, sw, k in rows:
        assert int(k) == _expected_factor(int(h), int(w), float(sh), float(sw)), (h, w, sh, sw)
    assert view_factor(4000, 6000, 1.0, 1.0) == 6000  # one device pixel: the 1 x 1 image
    assert view_factor(0, 0, 1.0, 1.0) == 1  # a degenerate image


def test_planted_unbounded_view_factor_fails() -> None:
    with pytest.raises(subprocess.TimeoutExpired):
        _view_factor_table(_UNBOUNDED)


def test_v8_harness_with_the_identity_stub_is_exact() -> None:
    src = image(301, 457, seed=3)
    method = StubCorrectionMethod()
    backend = StubArrayBackend()
    stats = imaging.measure_statistics(method, backend, src, {})
    for k in (1, 2, 3, 7):
        diff = preview_export_difference(method, backend, src, {}, stats, k)
        assert (diff.mean_abs, diff.max_abs) == (0.0, 0.0)


def test_v8_harness_detects_a_resolution_dependent_method() -> None:
    class Sharpen(StubCorrectionMethod):
        def render(self, image: Image, params: object, statistics: object) -> Image:  # type: ignore[override]
            px = np.asarray(image.pixels)
            out = np.clip(2 * px - np.roll(px, 1, axis=1), 0, 1).astype(np.float32)
            return dataclasses.replace(image, pixels=out)

    src = image(120, 160, seed=5)
    diff = preview_export_difference(Sharpen(), StubArrayBackend(), src, {}, {}, 4)
    assert diff.max_abs > 3 / 255


def test_display_quantisation_and_owned_qimage() -> None:
    data = np.array([[[0.0, 0.5, 1.0], [-0.2, 1.4, 0.25]]], dtype=np.float32)
    rgb = to_display_uint8(data)
    assert rgb.tolist() == [[[0, 128, 255], [0, 255, 64]]]
    shown = display_image(rgb, None)
    del rgb
    assert image_bytes(shown).tolist() == [[[0, 128, 255], [0, 255, 64]]]


def test_display_converts_an_icc_tagged_copy_to_srgb() -> None:
    p3 = bytes(QColorSpace(QColorSpace.NamedColorSpace.DisplayP3).iccProfile().data())
    rgb = np.zeros((1, 1, 3), dtype=np.uint8)
    rgb[0, 0] = (255, 0, 0)
    original = rgb.copy()
    converted = image_bytes(display_image(rgb, p3))
    assert converted[0, 0, 0] == 255 and converted[0, 0, 1] < 60  # P3 red is outside sRGB: clipped
    np.testing.assert_array_equal(rgb, original)  # the data is never changed
    assert image_bytes(display_image(rgb, b"not an icc profile")).tolist() == original.tolist()
    green = np.full((1, 1, 3), (40, 200, 60), dtype=np.uint8)
    assert image_bytes(display_image(green, p3)).tolist() != green.tolist()


def test_every_display_copy_is_tagged_srgb() -> None:
    # Round-1 F7: an untagged source or an unparseable profile is tagged sRGB, not left invalid.
    srgb = QColorSpace(QColorSpace.NamedColorSpace.SRgb)
    p3 = bytes(QColorSpace(QColorSpace.NamedColorSpace.DisplayP3).iccProfile().data())
    rgb = np.full((2, 3, 3), (40, 200, 60), dtype=np.uint8)
    for icc in (None, b"", b"not an icc profile", p3):
        shown = display_image(rgb, icc)
        assert shown.colorSpace() == srgb, icc
        assert shown.format() == QImage.Format.Format_RGB888
    assert image_bytes(display_image(rgb, None)).tolist() == rgb.tolist()


# The preview in the window.


def _open_photo(build, qtbot, src: Image, method=None, size=(800, 600)):
    path = Path("photo.png")
    methods = None if method is None else {method.id: method}
    window = build(photo_engines({path: src}, methods=methods), size=size)
    open_and_wait(qtbot, window, path)
    return window


def _corrected_region(window, expected: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """The grabbed device pixels right of the divider over the image, and the same image pixels."""
    widget = window.preview_widget
    grabbed = image_bytes(widget.grab().toImage())
    ox, oy = (int(v) for v in widget.image_origin())
    x0 = math.ceil(widget.divider_x()) + 2
    gh, gw = grabbed.shape[0], grabbed.shape[1]
    eh, ew = expected.shape[0], expected.shape[1]
    ys, ye = max(0, oy), min(gh, oy + eh)
    xs, xe = max(x0, ox), min(gw, ox + ew)
    assert ye - ys > 50 and xe - xs > 50
    return grabbed[ys:ye, xs:xe], expected[ys - oy : ye - oy, xs - ox : xe - ox]


def test_one_to_one_corrected_pixels_equal_the_full_resolution_render(make_window, qtbot) -> None:
    src = image(600, 1800, seed=11)
    window = _open_photo(make_window, qtbot, src, size=(600, 400))
    widget = window.preview_widget
    assert widget.needed_factor() > 1
    window.view_actions["one_to_one"].trigger()
    wait_idle(qtbot, window)
    assert widget.shown_factor() == 1.0 and not widget.pending_full()
    region, crop = _corrected_region(window, to_display_uint8(np.asarray(src.pixels)))
    np.testing.assert_array_equal(region, crop)


def test_planted_one_to_one_with_scaled_pixels_fails(make_window, qtbot, monkeypatch) -> None:
    src = image(600, 1800, seed=11)
    window = _open_photo(make_window, qtbot, src, size=(600, 400))
    monkeypatch.setattr(type(window.preview_widget), "needed_factor", lambda self: 2)
    window.view_actions["one_to_one"].trigger()
    window.controller.request()
    wait_idle(qtbot, window)
    region, crop = _corrected_region(window, to_display_uint8(np.asarray(src.pixels)))
    assert not np.array_equal(region, crop)


# 1:1 at devicePixelRatio 2 (round-4 R4-3). The ratio is fixed when the QApplication starts, so
# the check runs in a child process started with QT_SCALE_FACTOR=2 on the offscreen platform.

_DPR_PROBE = """
import math, sys, time
from pathlib import Path
sys.path.insert(0, sys.argv[2])
import gui_support
import numpy as np
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from clearwater.gui.imaging import image_bytes, to_display_uint8
from clearwater.gui.preview import PreviewWidget
from clearwater.gui.shell import MainWindow
PLANT
app = QApplication([])

def wait(done):
    end = time.monotonic() + 20
    while not done():
        assert time.monotonic() < end, "timed out"
        QTest.qWait(10)

path = Path("photo.png")
src = gui_support.image(600, 1800, seed=11)
window = MainWindow(
    gui_support.photo_engines({path: src}),
    gui_support.locations(Path(sys.argv[1])),
    presenter=gui_support.CapturingPresenter(),
)
window.resize(600, 400)
window.show()
QTest.qWaitForWindowExposed(window)
window.open_path(path)
wait(lambda: not window.opening())
wait(window.controller.idle)
widget = window.preview_widget
window.view_actions["one_to_one"].trigger()
wait(window.controller.idle)
QTest.qWait(30)
grab = widget.grab()
dpr = grab.devicePixelRatio()
grabbed = image_bytes(grab.toImage())
ox, oy = (int(v) for v in widget.image_origin())
x0 = math.ceil(widget.divider_x() * dpr) + 2
expected = to_display_uint8(np.asarray(src.pixels))
ys, ye = max(0, oy), min(grabbed.shape[0], oy + expected.shape[0])
xs, xe = max(x0, ox), min(grabbed.shape[1], ox + expected.shape[1])
region = grabbed[ys:ye, xs:xe]
crop = expected[ys - oy : ye - oy, xs - ox : xe - ox]
print("DPR", dpr)
print("DEVICE", grabbed.shape[1] == round(widget.width() * dpr))
print("FACTOR", widget.shown_factor(), widget.pending_full())
print("REGION", ye - ys, xe - xs)
print("EXACT", region.shape == crop.shape and bool(np.array_equal(region, crop)))
window.close()
"""

_DPR_IGNORED = "PreviewWidget.devicePixelRatioF = lambda self: 1.0"


def _one_to_one_at_dpr_two(tmp_path: Path, plant: str = "") -> dict[str, list[str]]:
    env = dict(os.environ, QT_SCALE_FACTOR="2", QT_QPA_PLATFORM="offscreen")
    code = _DPR_PROBE.replace("PLANT", plant)
    tests_dir = str(Path(__file__).resolve().parent)
    done = subprocess.run(
        [sys.executable, "-c", code, str(tmp_path), tests_dir],
        capture_output=True,
        text=True,
        timeout=120,
        env=env,
        check=False,
    )
    assert done.returncode == 0, done.stderr
    return {line.split()[0]: line.split()[1:] for line in done.stdout.splitlines() if line}


def test_one_to_one_is_exact_in_device_pixels_at_device_pixel_ratio_two(tmp_path: Path) -> None:
    seen = _one_to_one_at_dpr_two(tmp_path)
    assert seen["DPR"] == ["2.0"] and seen["DEVICE"] == ["True"]
    assert seen["FACTOR"] == ["1.0", "False"]
    assert int(seen["REGION"][0]) > 50 and int(seen["REGION"][1]) > 50
    assert seen["EXACT"] == ["True"]


def test_planted_one_to_one_ignoring_the_device_pixel_ratio_fails(tmp_path: Path) -> None:
    seen = _one_to_one_at_dpr_two(tmp_path, _DPR_IGNORED)
    assert seen["DPR"] == ["2.0"]
    assert seen["EXACT"] == ["False"]


def test_preview_equals_the_export_downscaled_by_the_same_rule(make_window, qtbot) -> None:
    src = image(1200, 1600, seed=2)
    window = _open_photo(make_window, qtbot, src, size=(500, 400))
    widget = window.preview_widget
    k = widget.needed_factor()
    assert k > 1 and widget.shown_factor() == pytest.approx(1600 / math.ceil(1600 / k))
    export = to_display_uint8(downscale(np.asarray(src.pixels), k))
    np.testing.assert_array_equal(image_bytes(widget.after_image()), export)
    np.testing.assert_array_equal(image_bytes(widget.before_image()), export)


def test_one_to_one_shows_the_scaled_result_with_an_indicator_until_full_arrives(
    make_window,
    qtbot,
) -> None:
    method = LevelMethod(delay_s=0.0)
    src = image(400, 600, seed=1)
    window = _open_photo(make_window, qtbot, src, method=method, size=(300, 250))
    widget = window.preview_widget
    method.delay_s = 0.5
    window.view_actions["one_to_one"].trigger()
    assert widget.pending_full()
    assert widget.after_image() is not None and widget.shown_factor() > 1
    wait_idle(qtbot, window)
    assert not widget.pending_full() and widget.shown_factor() == 1.0


def test_leaving_one_to_one_before_the_full_render_clears_the_indicator(make_window, qtbot) -> None:
    # Round-1 F3: the superseded full render never arrives, so the k > 1 request clears it.
    method = LevelMethod(delay_s=0.0)
    window = _open_photo(
        make_window, qtbot, image(400, 600, seed=1), method=method, size=(300, 250)
    )
    widget = window.preview_widget
    method.delay_s = 0.5
    window.view_actions["one_to_one"].trigger()
    assert widget.pending_full()
    method.delay_s = 0.0
    widget.fit()
    wait_idle(qtbot, window)
    assert widget.shown_factor() > 1 and not widget.pending_full()


def _zoom_round_trip(window, qtbot) -> None:
    widget = window.preview_widget
    for _ in range(2):
        window.view_actions["one_to_one"].trigger()
        wait_idle(qtbot, window)
        assert widget.shown_factor() == 1.0
        widget.fit()
        wait_idle(qtbot, window)
        assert widget.shown_factor() > 1
    window.view_actions["one_to_one"].trigger()
    wait_idle(qtbot, window)


def test_full_resolution_is_rendered_once_per_parameter_state(make_window, qtbot) -> None:
    # Round-1 F2 (question 6): returning to 1:1 or to fit with unchanged parameters shows the
    # memoised render; a parameter change renders again.
    method = LevelMethod()
    src = image(400, 600, seed=3)
    window = _open_photo(make_window, qtbot, src, method=method, size=(300, 250))
    assert len(method.rendered) == 1  # the fit render
    _zoom_round_trip(window, qtbot)
    assert len(method.rendered) == 2  # plus exactly one full-resolution render
    assert window.preview_widget.shown_factor() == 1.0 and not window.preview_widget.pending_full()
    assert image_bytes(window.preview_widget.after_image()).shape[:2] == (400, 600)
    window.session.set_parameters(new_parameter_set("level", {"level": 0.25}))
    wait_idle(qtbot, window)
    assert len(method.rendered) == 3
    assert image_bytes(window.preview_widget.after_image())[0, 0, 0] == round(0.25 * 255)


def test_a_full_render_superseded_while_it_runs_is_not_rendered_again(make_window, qtbot) -> None:
    # Round-2 R2-1: the render that finished after the user left 1:1 is memoised anyway.
    method = LevelMethod()
    window = _open_photo(
        make_window, qtbot, image(400, 600, seed=3), method=method, size=(300, 250)
    )
    widget = window.preview_widget
    started = len(method.threads)
    method.delay_s = 0.4
    window.view_actions["one_to_one"].trigger()
    qtbot.waitUntil(lambda: len(method.threads) > started, timeout=5000)
    method.delay_s = 0.0
    widget.fit()
    wait_idle(qtbot, window)
    assert len(method.rendered) == 2  # the fit render and the superseded full one
    window.view_actions["one_to_one"].trigger()
    wait_idle(qtbot, window)
    assert len(method.rendered) == 2 and widget.shown_factor() == 1.0
    assert image_bytes(widget.after_image()).shape[:2] == (400, 600)


def test_show_proxy_clears_the_full_resolution_indicator(make_window, qtbot) -> None:
    # Round-2 R2-4: a scrub proxy supersedes the full render, so the indicator goes.
    method = LevelMethod()
    window = _open_photo(
        make_window, qtbot, image(400, 600, seed=3), method=method, size=(300, 250)
    )
    method.delay_s = 0.4
    window.view_actions["one_to_one"].trigger()
    assert window.preview_widget.pending_full()
    window.preview.show_proxy(np.zeros((90, 135, 3), dtype=np.uint8))
    assert not window.preview_widget.pending_full()
    wait_idle(qtbot, window)
    assert not window.preview_widget.pending_full()


def test_a_frame_error_banner_clears_at_the_next_decoded_frame(make_window, qtbot) -> None:
    # Round-2 R2-3: "a banner until ... the next success of that action" (Message).
    engines = video_engines([frame(48, 64, ticks=0), frame(48, 64, ticks=9000)])
    original = engines.video_source.frames
    failing = {"on": False}

    def frames(*args, **kwargs):
        if failing["on"]:
            raise RuntimeError("decode failed")
        return original(*args, **kwargs)

    object.__setattr__(engines.video_source, "frames", frames)
    window = make_window(engines)
    open_and_wait(qtbot, window, Path("clip.mp4"))
    failing["on"] = True
    window.session.set_position(9000)
    wait_idle(qtbot, window)
    assert len(presenter_of(window).of("error")) == 1
    failing["on"] = False
    window.session.set_position(9000)
    wait_idle(qtbot, window)
    assert presenter_of(window).of("error") == []
    assert window.session.current_image().pts_ticks == 9000


def test_frame_decoded_names_the_shown_frame_or_the_failure(make_window, qtbot) -> None:
    # DR-44 (a): a panel learns which frame is shown (the first at or after the request).
    engines = video_engines([frame(48, 64, ticks=0), frame(48, 64, ticks=9000)])
    original = engines.video_source.frames
    failing = {"on": False}

    def frames(*args, **kwargs):
        if failing["on"]:
            raise RuntimeError("decode failed")
        return original(*args, **kwargs)

    object.__setattr__(engines.video_source, "frames", frames)
    window = make_window(engines)
    open_and_wait(qtbot, window, Path("clip.mp4"))
    outcomes: list[object] = []
    window.session.frame_decoded.connect(outcomes.append)
    window.session.set_position(4000)
    wait_idle(qtbot, window)
    assert outcomes == [FrameOutcome(4000, 9000, None)]
    assert window.session.current_image().pts_ticks == 9000
    failing["on"] = True
    window.session.set_position(0)
    wait_idle(qtbot, window)
    assert len(outcomes) == 2 and outcomes[1].requested == 0 and outcomes[1].pts is None
    assert "decode failed" in outcomes[1].error
    assert window.session.current_image().pts_ticks == 9000  # unchanged after the failure


def test_frame_decoded_is_not_emitted_for_a_superseded_request(make_window, qtbot) -> None:
    engines = video_engines([frame(48, 64, ticks=0), frame(48, 64, ticks=9000)])
    window = make_window(engines)
    open_and_wait(qtbot, window, Path("clip.mp4"))
    outcomes: list[object] = []
    window.session.frame_decoded.connect(outcomes.append)
    window.session.set_position(0)
    window.session.set_position(9000)  # supersedes the first before it is delivered
    wait_idle(qtbot, window)
    assert outcomes[-1] == FrameOutcome(9000, 9000, None)
    assert all(o.requested == 9000 for o in outcomes)


def test_a_shell_success_clears_only_its_own_error(make_window, qtbot) -> None:
    # DR-44 (b): the next decoded frame clears the frame error, never a panel's error.
    engines = video_engines([frame(48, 64, ticks=0), frame(48, 64, ticks=9000)])
    original = engines.video_source.frames
    failing = {"on": False}

    def frames(*args, **kwargs):
        if failing["on"]:
            raise RuntimeError("decode failed")
        return original(*args, **kwargs)

    object.__setattr__(engines.video_source, "frames", frames)
    window = make_window(engines)
    open_and_wait(qtbot, window, Path("clip.mp4"))
    presenter = presenter_of(window)
    presenter.present(Message("error", "preset not saved", owner="presets"))
    failing["on"] = True
    window.session.set_position(9000)
    wait_idle(qtbot, window)
    assert len(presenter.of("error")) == 2
    failing["on"] = False
    window.session.set_position(9000)
    wait_idle(qtbot, window)
    assert [m.text for m in presenter.of("error")] == ["preset not saved"]
    presenter.clear("error", owner="presets")
    assert presenter.of("error") == []


class _GatedFrames:
    """Wraps a stub ``frames``: once armed, the next call blocks until released."""

    def __init__(self, original) -> None:
        self.original = original
        self.armed = False
        self.entered = threading.Event()
        self.release = threading.Event()

    def __call__(self, *args, **kwargs):
        if self.armed:
            self.armed = False
            self.entered.set()
            assert self.release.wait(10)
        return self.original(*args, **kwargs)


def _gated_window(make_window, qtbot):
    engines = video_engines([frame(48, 64, ticks=0), frame(48, 64, ticks=9000)])
    gate = _GatedFrames(engines.video_source.frames)
    object.__setattr__(engines.video_source, "frames", gate)
    window = make_window(engines)
    open_and_wait(qtbot, window, Path("clip.mp4"))
    outcomes: list[object] = []
    window.session.frame_decoded.connect(outcomes.append)
    return window, gate, outcomes


def test_frame_decoded_is_not_emitted_for_a_request_superseded_in_flight(make_window, qtbot):
    window, gate, outcomes = _gated_window(make_window, qtbot)
    gate.armed = True
    window.session.set_position(0)
    assert gate.entered.wait(10)  # the first decode is running
    window.session.set_position(9000)
    gate.release.set()
    wait_idle(qtbot, window)
    assert outcomes == [FrameOutcome(9000, 9000, None)]


def test_frame_decoded_is_not_emitted_after_preview_show_or_a_source_change(make_window, qtbot):
    window, gate, outcomes = _gated_window(make_window, qtbot)
    gate.armed = True
    window.session.set_position(9000)
    assert gate.entered.wait(10)
    window.preview.show(image(48, 64))
    gate.release.set()
    wait_idle(qtbot, window)
    assert outcomes == []
    gate.armed, gate.entered, gate.release = True, threading.Event(), threading.Event()
    window.session.set_position(9000)
    assert gate.entered.wait(10)
    window.open_path(Path("other.mp4"))
    gate.release.set()
    qtbot.waitUntil(lambda: not window.opening(), timeout=10000)
    wait_idle(qtbot, window)
    assert outcomes == []


def test_frame_decoded_reports_a_position_with_no_frame(make_window, qtbot) -> None:
    window, _, outcomes = _gated_window(make_window, qtbot)
    window.session.set_position(20000)  # after the last frame
    wait_idle(qtbot, window)
    assert len(outcomes) == 1 and outcomes[0].requested == 20000 and outcomes[0].pts is None
    assert outcomes[0].error and presenter_of(window).of("error")[0].owner == "shell.frame"


def test_a_newly_opened_source_clears_only_the_shells_banners(make_window, qtbot) -> None:
    # Reviewer B #1 (DR-44 (b)): opening a file clears the shell's own banners, not a panel's.
    window, _, _ = _gated_window(make_window, qtbot)
    presenter = presenter_of(window)
    presenter.present(Message("error", "preset not saved", owner="presets"))
    window.session.set_position(20000)
    wait_idle(qtbot, window)
    assert len(presenter.of("error")) == 2
    open_and_wait(qtbot, window, Path("other.mp4"))
    assert [m.text for m in presenter.of("error")] == ["preset not saved"]


def test_the_product_presenter_forwards_the_owner(qtbot) -> None:
    # Reviewer B #5: DialogPresenter.clear passes the owner to the banner.
    parent = QWidget()
    qtbot.addWidget(parent)
    banner = BannerWidget(parent)
    presenter = DialogPresenter(parent, banner)
    presenter.present(Message("error", "a", owner="presets"))
    presenter.present(Message("error", "b", owner="settings"))
    presenter.clear("error", owner="presets")
    assert banner.texts() == ["b"]


def test_the_banner_clears_by_owner(qtbot) -> None:
    banner = BannerWidget()
    qtbot.addWidget(banner)
    banner.add(Message("error", "a", owner="presets"))
    banner.add(Message("error", "b", owner="settings"))
    banner.add(Message("warning", "c", owner="presets"))
    banner.clear("error", owner="presets")
    assert banner.texts() == ["b", "c"]
    banner.clear(owner="presets")
    assert banner.texts() == ["b"]
    banner.clear("error")
    assert banner.texts() == []


class _StatisticsLevel(LevelMethod):
    """Renders the level its supplied statistics carry, so a statistics change is visible."""

    def render(self, image, params, statistics):
        out = super().render(image, params, statistics)
        level = float(statistics["only"].get("level", params["level"]))
        return dataclasses.replace(out, pixels=np.full_like(np.asarray(out.pixels), level))


def _mutate_statistics_in_place(make_window, qtbot) -> int:
    method = _StatisticsLevel()
    window = _open_photo(make_window, qtbot, image(60, 80), method=method)
    stats = {"only": {"mean": np.zeros(3), "level": 0.2}}
    window.session.set_statistics(stats)
    wait_idle(qtbot, window)
    assert image_bytes(window.preview_widget.after_image())[0, 0, 0] == round(0.2 * 255)
    stats["only"]["level"] = 0.8  # the same mapping, changed in place, set again
    window.session.set_statistics(stats)
    wait_idle(qtbot, window)
    return int(image_bytes(window.preview_widget.after_image())[0, 0, 0])


def test_statistics_changed_in_place_and_set_again_render_again(make_window, qtbot) -> None:
    # Round-3 R3-2: the memo key carries the session's statistics revision, not their identity.
    assert _mutate_statistics_in_place(make_window, qtbot) == round(0.8 * 255)


def test_planted_identity_only_render_memo_fails(make_window, qtbot, monkeypatch) -> None:
    monkeypatch.setattr(ShellSession, "statistics_revision", lambda self: 0)
    assert _mutate_statistics_in_place(make_window, qtbot) != round(0.8 * 255)


def test_the_indicator_shows_for_a_change_at_one_to_one(make_window, qtbot) -> None:
    # Round-3 R3-3: at 1:1 a parameter change renders the full resolution: the indicator is on.
    method = LevelMethod()
    window = _open_photo(
        make_window, qtbot, image(400, 600, seed=3), method=method, size=(300, 250)
    )
    window.view_actions["one_to_one"].trigger()
    wait_idle(qtbot, window)
    assert not window.preview_widget.pending_full()
    method.delay_s = 0.3
    window.session.set_parameters(new_parameter_set("level", {"level": 0.7}))
    assert window.preview_widget.pending_full()
    wait_idle(qtbot, window)
    assert not window.preview_widget.pending_full()


def test_a_position_change_clears_the_indicator_even_when_the_frame_fails(
    make_window, qtbot
) -> None:
    # Round-3 R3-3: the position change invalidates the full render; a decode failure follows.
    method = LevelMethod()
    engines = video_engines(
        [frame(400, 600, ticks=0), frame(400, 600, ticks=9000)], methods={method.id: method}
    )
    original = engines.video_source.frames
    failing = {"on": False}

    def frames(*args, **kwargs):
        if failing["on"]:
            raise RuntimeError("decode failed")
        return original(*args, **kwargs)

    object.__setattr__(engines.video_source, "frames", frames)
    window = make_window(engines, size=(300, 250))
    open_and_wait(qtbot, window, Path("clip.mp4"))
    method.delay_s = 0.4
    window.view_actions["one_to_one"].trigger()
    assert window.preview_widget.pending_full()
    failing["on"] = True
    window.session.set_position(9000)
    assert not window.preview_widget.pending_full()
    wait_idle(qtbot, window)
    assert not window.preview_widget.pending_full()
    assert len(presenter_of(window).of("error")) == 1


def test_planted_preview_without_the_render_memo_fails(make_window, qtbot, monkeypatch) -> None:
    monkeypatch.setattr(render_worker.PreviewMemo, "after", lambda self, *args: None)
    method = LevelMethod()
    window = _open_photo(
        make_window, qtbot, image(400, 600, seed=3), method=method, size=(300, 250)
    )
    _zoom_round_trip(window, qtbot)
    assert len(method.rendered) != 2  # the once-per-state test above would fail on this


def test_supplied_statistics_are_not_served_another_states_render(make_window, qtbot) -> None:
    method = LevelMethod()
    window = _open_photo(
        make_window, qtbot, image(400, 600, seed=3), method=method, size=(300, 250)
    )
    count = len(method.rendered)
    window.session.set_statistics({"only": {"mean": np.zeros(3)}})
    wait_idle(qtbot, window)
    window.session.set_statistics({"only": {"mean": np.ones(3)}})
    wait_idle(qtbot, window)
    assert len(method.rendered) == count + 2  # new statistics objects are new states


def test_latest_wins_three_quick_changes_show_only_the_last(make_window, qtbot) -> None:
    method = LevelMethod(delay_s=0.3)
    window = _open_photo(make_window, qtbot, image(60, 80), method=method)
    shown: list[float] = []
    window.controller.rendered.connect(
        lambda result: shown.append(image_bytes(result.after)[0, 0, 0] / 255)
    )
    for level in (0.1, 0.2, 0.9):
        window.session.set_parameters(new_parameter_set("level", {"level": level}))
    wait_idle(qtbot, window)
    assert shown == [pytest.approx(0.9, abs=1 / 255)]
    assert image_bytes(window.preview_widget.after_image())[0, 0, 0] == round(0.9 * 255)


def test_planted_stale_result_displayed_fails(make_window, qtbot, monkeypatch) -> None:
    method = LevelMethod(delay_s=0.3)
    window = _open_photo(make_window, qtbot, image(60, 80), method=method)
    shown: list[int] = []
    window.controller.rendered.connect(lambda r: shown.append(int(image_bytes(r.after)[0, 0, 0])))

    def no_drop(self, outcome) -> None:
        self._on_result(outcome)

    def run_all(self) -> None:
        while True:
            with self._lock:
                while self._pending is None and not self._stopping:
                    self._lock.wait()
                if self._stopping:
                    return
                generation, task = self._pending
                self._pending = None
                self._busy = True
            value = task(lambda: None)
            with self._lock:
                self._busy = False
            self._bridge.delivered.emit(render_worker.Outcome(generation, value, None))

    monkeypatch.setattr(render_worker.LatestWorker, "_deliver", no_drop)
    window.controller._renderer.stop(5)
    monkeypatch.setattr(render_worker.LatestWorker, "_run", run_all)
    window.controller._renderer = render_worker.LatestWorker(
        "planted", window.controller._on_render
    )
    for level in (0.1, 0.2, 0.9):
        window.session.set_parameters(new_parameter_set("level", {"level": level}))
        qtbot.wait(50)
    wait_idle(qtbot, window)
    assert shown != [round(0.9 * 255)]  # the latest-wins test above would fail on this


def test_statistics_measured_once_per_parameter_state_and_supplied_ones_used(
    make_window,
    qtbot,
) -> None:
    method = LevelMethod()
    window = _open_photo(make_window, qtbot, image(1200, 1600), method=method, size=(500, 400))
    measured = method.analysed
    assert measured == 1
    window.preview_widget.zoom_in()
    wait_idle(qtbot, window)
    window.preview_widget.fit()
    wait_idle(qtbot, window)
    assert method.analysed == measured  # zoom never re-measures
    window.session.set_statistics({"only": {"mean": np.zeros(3)}})
    wait_idle(qtbot, window)
    assert method.analysed == measured


class DeviceStatisticsMethod(LevelMethod):
    """Measures a backend-dependent statistic and renders it as the level."""

    def analyze(self, stage, image, params, earlier):  # type: ignore[override]
        super().analyze(stage, image, params, earlier)
        return {"mean": np.full(3, 0.2 if image.device == "cpu" else 0.8, dtype=np.float32)}

    def render(self, image, params, statistics):  # type: ignore[override]
        level = float(np.asarray(statistics["only"]["mean"])[0])
        out = np.full_like(np.asarray(image.pixels), level, dtype=np.float32)
        return Image(out, image.device, image.color, image.orientation_applied)


def test_a_force_cpu_change_measures_the_statistics_again(make_window, qtbot) -> None:
    # Reviewer B #6: statistics measured on one device are not reused on another.
    class GpuBackend(StubArrayBackend):
        device = "cuda:0"

    gpu, cpu = GpuBackend(), StubArrayBackend()

    def select(settings, height, width, method_id):
        return (cpu, "CPU: forced") if settings.force_cpu else (gpu, "GPU")

    method = DeviceStatisticsMethod()
    path = Path("photo.png")
    engines = photo_engines(
        {path: image(60, 80)}, methods={method.id: method}, select_backend=select
    )
    window = make_window(engines, size=(300, 250))
    open_and_wait(qtbot, window, path)
    after = window.preview_widget.after_image()
    assert after is not None and image_bytes(after)[0, 0, 0] == round(0.8 * 255)
    measured = method.analysed
    window.session.set_settings(dataclasses.replace(window.session.settings(), force_cpu=True))
    wait_idle(qtbot, window)
    assert method.analysed == measured + 1
    after = window.preview_widget.after_image()
    assert after is not None and image_bytes(after)[0, 0, 0] == round(0.2 * 255)


def test_a_new_source_drops_the_previous_sources_memo(make_window, qtbot) -> None:
    # Reviewer B #7: no statistics, originals or corrected images kept across opens.
    first, second = Path("a.png"), Path("b.png")
    window = make_window(photo_engines({first: image(60, 80), second: image(50, 70, seed=4)}))
    open_and_wait(qtbot, window, first)
    window.view_actions["one_to_one"].trigger()
    wait_idle(qtbot, window)
    open_and_wait(qtbot, window, second)
    token = window.session.image_token()
    memo = window.controller._memo
    kept = [key[0] for key in (*memo._statistics, *memo._before, *memo._after)]
    assert kept and set(kept) == {token}


def test_render_error_becomes_a_message_and_the_last_preview_stays(make_window, qtbot) -> None:
    method = LevelMethod()
    window = _open_photo(make_window, qtbot, image(60, 80), method=method)
    before = image_bytes(window.preview_widget.after_image())

    def explode() -> None:
        raise RuntimeError("boom")

    method.busy = explode
    window.session.set_parameters(new_parameter_set("level", {"level": 0.9}))
    wait_idle(qtbot, window)
    errors = presenter_of(window).of("error")
    assert len(errors) == 1 and "boom" in errors[0].text
    np.testing.assert_array_equal(image_bytes(window.preview_widget.after_image()), before)
    method.busy = None
    window.session.set_parameters(new_parameter_set("level", {"level": 0.2}))
    wait_idle(qtbot, window)
    assert presenter_of(window).of("error") == []


def test_icc_tagged_source_shows_a_converted_copy(make_window, qtbot) -> None:
    p3 = bytes(QColorSpace(QColorSpace.NamedColorSpace.DisplayP3).iccProfile().data())
    color = ColorDescription("display-p3", "srgb", "identity", "full", 8, False, p3)
    data = np.zeros((40, 40, 3), dtype=np.float32)
    data[..., 1] = 0.8
    src = Image(data, "cpu", color, True)
    window = _open_photo(make_window, qtbot, src, size=(200, 200))
    shown = image_bytes(window.preview_widget.before_image())
    assert shown[0, 0].tolist() != [0, 204, 0]
    assert np.asarray(window.session.current_image().pixels)[0, 0].tolist() == pytest.approx(
        [0.0, 0.8, 0.0]
    )


def test_split_divider_and_zoom_controls(make_window, qtbot) -> None:
    window = _open_photo(make_window, qtbot, image(300, 400), size=(400, 300))
    widget = window.preview_widget
    assert widget.is_fit() and widget.zoom_text().startswith("Fit (")
    widget.set_split(0.25)
    assert widget.split() == 0.25
    window.view_actions["reset_split"].trigger()
    assert widget.split() == 0.5
    window.view_actions["zoom_in"].trigger()
    assert not widget.is_fit()
    window.view_actions["zoom_out"].trigger()
    window.view_actions["fit"].trigger()
    assert widget.is_fit()
    window.view_actions["one_to_one"].trigger()
    assert widget.zoom_text() == "100%"
    assert isinstance(widget.grab().toImage(), QImage)
