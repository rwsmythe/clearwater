"""WP4.3 task 10: V8 and V18 on the running shell (question 12 and Q24 as ruled; DR-75).

V8 (AD-11 AS AMENDED 2026-10-21, CHARC addendum (1)): k = 1 EXACT; k > 1 mean <= 1/255, p99 <=
2/255 at k = 2 and <= 4/255 at k = 4; p99.9 and the max are recorded as characterisation, never
asserted (R4-2).

- Photo: the corrected preview the shell shows at 1:1, k = 2 and k = 4 against the exported
  16-bit PNG read back and ``imaging.downscale``d by the same k.
- DR-75's REQUIRED test (the photo leg): a chromatic nclx-only Display P3 HEIC built under
  ``tmp_path`` (WP4.1 R3's recipe) is previewed and compared with its export; the expected
  display colour comes from the exported PNG's EMBEDDED profile read back, never from the
  production chooser. It fails on the base, where the display copy is not converted.
- Video, pre-encode: the shell's rendered frame at a pts against
  ``downscale(render(full frame))`` with the engine's smoothed record at that pts, through
  ``imaging.preview_export_difference`` on the real method and backend.

V18 (gate form, Q24): on ``hevc8-bt709-full`` with the analysis held inside its decode by a test
hook (B-4), a corrected frame is shown while the analysis is still running, and after it the
shown statistics equal the engine's ``smoothed_record`` of the shown frame. The GX011627 leg is
exclusive window evidence.
"""

# ``make_app`` is imported from test_app_startup and used as a parameter.
# ruff: noqa: F401, F811

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from PIL import Image as PILImage

import gui_support
from clearwater.analysis import AnalysisEngine
from clearwater.app import composition
from clearwater.app.main import Application
from clearwater.config import new_parameter_set
from clearwater.core import backend_for
from clearwater.gui.export_panel import ExportPanel
from clearwater.gui.imaging import (
    display_image,
    downscale,
    effective_parameters,
    image_bytes,
    preview_export_difference,
    render_host,
    to_display_uint8,
)
from clearwater.interfaces import ColorDescription, Image, PhotoMetadata
from test_app_startup import (
    CLIP,
    cpu_settings,
    latest_analysis,
    make_app,
    open_source,
    wait_analysis,
    wait_started,
)

pytestmark = [pytest.mark.gui, pytest.mark.usefixtures("ffmpeg_tools")]

MEAN_BOUND = 1.0 / 255.0
P99_BOUND = {2: 2.0 / 255.0, 4: 4.0 / 255.0}
HALF_STEP_16 = 0.5 / 65535.0
BT709_16 = ColorDescription("bt709", "bt709", "bt709", "full", 16, False, None)


def started(make_app: Any, qtbot: Any, out: Path, **kwargs: Any) -> Application:
    application = make_app(cpu_settings(output_folder=out, png_bit_depth=16), **kwargs)
    wait_started(qtbot, application)
    return application


def rendered_at(qtbot: Any, application: Application, zoom: float | None) -> np.ndarray:
    """Set the zoom (None: fit), wait for the render, return the corrected side shown (uint8)."""
    window = application.window
    widget = window.preview_widget
    widget._set_zoom(zoom)
    qtbot.waitUntil(window.controller.idle, timeout=60000)
    qtbot.wait(30)
    shown = widget.after_image()
    assert shown is not None
    return image_bytes(shown)


def export_open_source(qtbot: Any, application: Application, out: Path) -> Path:
    """File > Export of the open source; return the one file written."""
    (panel,) = application.window.findChildren(ExportPanel)
    application.window.shell_actions.export.trigger()
    qtbot.waitUntil(lambda: not panel.is_running(), timeout=120000)
    (written,) = list(out.iterdir())
    return written


def png16(folder: Path, pixels: np.ndarray, name: str) -> Path:
    """Write ``pixels`` as a 16-bit PNG with no profile (displayed unconverted)."""
    path = folder / name
    composition.photo_writer().write(
        Image(np.ascontiguousarray(pixels, dtype=np.float32), "cpu", BT709_16, True),
        PhotoMetadata("png", None, 1),
        path,
        bit_depth=16,
        provenance=None,
    )
    return path


def smooth_scene(height: int = 1128, width: int = 1700) -> np.ndarray:
    """A photo-like test scene: low-frequency colour fields, a horizon, a red-depleted cast."""
    y, x = np.mgrid[0:height, 0:width].astype(np.float32)
    u, v = x / width, y / height
    red = 0.25 + 0.15 * np.sin(2.1 * np.pi * u) * np.cos(1.3 * np.pi * v)
    green = 0.45 + 0.25 * np.cos(1.7 * np.pi * (u + 0.3 * v))
    blue = 0.55 + 0.3 * np.sin(1.1 * np.pi * v + 0.5) * (1.0 - 0.4 * u)
    scene = np.stack([red, green, blue], axis=-1)
    scene[int(height * 0.6) :] *= 0.75  # a soft step: the sea floor
    return np.clip(scene, 0.02, 0.98)


def look_check_crop() -> np.ndarray:
    """The centre 1080 x 1920 crop of a WP1.3 look-check frame, or skip when it is absent."""
    from local_config import load_local_config
    from lookcheck.frames import read_png16

    try:
        frames = load_local_config().working_path / "wp1.3" / "frames"
    except Exception as exc:  # no local configuration: the frames cannot be found
        pytest.skip(f"no local configuration: {exc}")
    path = Path(frames) / "GX011625_0024.925.png"
    if not path.is_file():
        pytest.skip("the look-check frame is absent")
    frame = read_png16(path)
    top, left = frame.shape[0] // 2 - 540, frame.shape[1] // 2 - 960
    return np.ascontiguousarray(frame[top : top + 1080, left : left + 1920])


def k1_mismatch(preview: np.ndarray, expected: np.ndarray) -> np.ndarray:
    """Return where a k = 1 preview breaks EXACT (B-3): True at each pixel V8 refuses.

    EXACT is the display quantisation of the same full-resolution render. A value within the
    16-bit step of a rounding boundary may round either way, so there the preview may differ by
    one display step and no more; everywhere else it must be equal.

    Args:
        preview: The corrected preview the shell shows (uint8).
        expected: The exported image read back (float, 0..1), the same shape.

    Returns:
        A boolean array of ``preview``'s shape.
    """
    gap = np.abs(preview.astype(np.int16) - to_display_uint8(expected).astype(np.int16))
    near = np.abs((expected * 255.0) % 1.0 - 0.5) <= 255.0 * HALF_STEP_16 + 1e-4
    return np.where(near, gap > 1, gap > 0)


def _v8_photo(
    make_app: Any, qtbot: Any, tmp_path: Path, pixels: np.ndarray, ks: tuple[int, ...]
) -> dict[int, tuple[float, float, float, float]]:
    """Preview ``pixels`` on the shell at each k, export, compare; return (mean, p99, p99.9, max).

    p99.9 and max are AD-11's characterisation: recorded, never asserted (R4-2).
    """
    sources, out = tmp_path / "src", tmp_path / "out"
    sources.mkdir()
    out.mkdir()
    source = png16(sources, pixels, "scene.png")
    application = started(make_app, qtbot, out)
    open_source(qtbot, application, source)
    widget = application.window.preview_widget
    shown = {k: rendered_at(qtbot, application, 1.0 / k) for k in ks}
    assert widget.shown_factor() == ks[-1]
    written = export_open_source(qtbot, application, out)
    exported, _ = composition.photo_reader().read(written)
    full = np.asarray(exported.pixels, dtype=np.float32)
    figures: dict[int, tuple[float, float, float, float]] = {}
    for k, preview in shown.items():
        expected = full if k == 1 else downscale(full, k)
        assert preview.shape == expected.shape, k
        diff = np.abs(preview.astype(np.float64) / 255.0 - expected.astype(np.float64))
        figures[k] = (
            float(diff.mean()),
            float(np.quantile(diff, 0.99)),
            float(np.quantile(diff, 0.999)),
            float(diff.max()),
        )
        if k == 1:  # EXACT: the display quantisation of the same full-resolution render
            assert not k1_mismatch(preview, expected).any(), f"k = 1 is not exact: {figures[1]}"
        else:
            mean, p99, _, _ = figures[k]
            assert mean <= MEAN_BOUND and p99 <= P99_BOUND[k], f"k = {k}: {figures[k]}"
    return figures


def test_v8_photo_preview_at_1_1_and_k_2_and_4_against_the_downscaled_export(
    make_app, qtbot, tmp_path
) -> None:
    figures = _v8_photo(make_app, qtbot, tmp_path, smooth_scene(), (1, 2, 4))
    print(f"V8 photo, smooth scene (mean, p99, p99.9, max) by k: {figures}")


@pytest.mark.slow
def test_v8_photo_k_above_1_on_real_sized_content(make_app, qtbot, tmp_path) -> None:
    """The WP1.3 look-check crop (working folder; skipped without it), as WP4.1's V8 (c)."""
    figures = _v8_photo(make_app, qtbot, tmp_path, look_check_crop(), (1, 2, 4))
    print(f"V8 photo, look-check crop (mean, p99, p99.9, max) by k: {figures}")


def p3_nclx_heic(folder: Path) -> Path:
    """WP4.1 R3's sample: a 16 x 16 chromatic nclx-only Display P3 HEIC (no ICC profile)."""
    import pillow_heif

    path = folder / "p3-nclx.heic"
    pixels = np.zeros((16, 16, 3), dtype=np.uint8)
    pixels[..., 0], pixels[..., 1], pixels[..., 2] = 200, 40, 60
    pillow_heif.encode(
        "RGB",
        (16, 16),
        pixels.tobytes(),
        str(path),
        quality=95,
        nclx_profile={
            "color_primaries": 12,
            "transfer_characteristics": 13,
            "matrix_coefficients": 6,
            "full_range_flag": 1,
        },
    )
    return path


def _dr75_scenario(make_app: Any, qtbot: Any, tmp_path: Path) -> None:
    """Preview and export the nclx-only P3 sample; the preview must show the export's colour.

    Raises:
        AssertionError: "preview ... vs export ..." when the display copy is not the export's.
    """
    sources, out = tmp_path / "src", tmp_path / "out"
    sources.mkdir()
    out.mkdir()
    source = p3_nclx_heic(sources)
    image, _ = composition.photo_reader().read(source)
    assert image.color.icc_profile is None and image.color.primaries == "display-p3"
    application = started(make_app, qtbot, out)
    open_source(qtbot, application, source)
    session = application.window.session
    neutral = {p.name: p.neutral for p in session.method().parameters if p.neutral is not None}
    session.set_parameters(new_parameter_set("c3", neutral))  # the colour stays chromatic (V9)
    shown = rendered_at(qtbot, application, None)
    written = export_open_source(qtbot, application, out)
    with PILImage.open(written) as png:
        embedded = png.info.get("icc_profile")
    assert embedded, "the export embeds no profile"  # D53: the built-in Display P3
    exported, _ = composition.photo_reader().read(written)
    raw = to_display_uint8(np.asarray(exported.pixels, dtype=np.float32))
    expected = image_bytes(display_image(raw, embedded))
    unconverted = raw  # what the base shows: the P3-encoded values as if they were sRGB
    assert int(np.abs(expected.astype(int) - unconverted.astype(int)).max()) > 8  # chromatic
    worst = int(np.abs(shown.astype(int) - expected.astype(int)).max())
    assert worst <= 1, f"preview {shown[0, 0].tolist()} vs export {expected[0, 0].tolist()}"
    print(f"DR-75: preview {shown[0, 0].tolist()}, export {expected[0, 0].tolist()}")


def test_dr75_an_nclx_only_p3_photo_is_displayed_through_the_profile_its_export_embeds(
    make_app, qtbot, tmp_path
) -> None:
    """REQUIRED (DR-75, Q19). The expected colour: the export's embedded profile, read back."""
    _dr75_scenario(make_app, qtbot, tmp_path)


def test_dr75_the_base_display_rule_fails_the_required_test(
    make_app, qtbot, tmp_path, monkeypatch
) -> None:
    """The base's rule (only ``icc_profile`` reaches the display copy) is caught by name."""
    from clearwater.gui import preview as preview_module

    monkeypatch.setattr(
        preview_module,
        "display_profile",
        lambda source: None if source is None else source.image.color.icc_profile,
    )
    with pytest.raises(AssertionError, match=r"preview \[.*\] vs export \["):
        _dr75_scenario(make_app, qtbot, tmp_path)


def test_dr75_a_photo_with_an_icc_profile_or_untagged_is_displayed_as_before(
    make_app, qtbot, tmp_path, sample
) -> None:
    out = tmp_path / "out"
    out.mkdir()
    application = started(make_app, qtbot, out)
    window = application.window
    for sample_id in ("jpeg-gradient-display-p3", "jpeg-gradient-none"):
        source = sample(sample_id)
        open_source(qtbot, application, source)
        shown = rendered_at(qtbot, application, None)
        session = window.session
        image = session.current_image()
        method = session.method()
        params = effective_parameters(method, session.parameters())
        backend = backend_for("cpu")
        from clearwater.gui.imaging import measure_statistics

        statistics = measure_statistics(method, backend, image, params)
        k = round(window.preview_widget.shown_factor())
        corrected = render_host(
            method, backend, downscale(np.asarray(image.pixels), k), image.color, params, statistics
        )
        expected = image_bytes(display_image(to_display_uint8(corrected), image.color.icc_profile))
        assert np.array_equal(shown, expected), sample_id


def test_v8_video_pre_encode_through_the_harness_on_the_shells_frame(
    make_app, qtbot, tmp_path, sample
) -> None:
    out = tmp_path / "out"
    out.mkdir()
    application = started(make_app, qtbot, out)
    window = application.window
    open_source(qtbot, application, sample(CLIP))
    wait_analysis(qtbot, application)
    ticks = latest_analysis(application).pts()
    window.session.set_position(ticks[10], statistics=None)
    qtbot.waitUntil(lambda: window.session.position() == ticks[10], timeout=10000)
    analysis = latest_analysis(application)
    engine = analysis._engine
    assert engine is not None
    record = engine.smoothed_record(ticks[10])
    window.session.set_position(ticks[10], statistics=record)
    shown = rendered_at(qtbot, application, 0.5)
    k = round(window.preview_widget.shown_factor())
    assert k == 2
    frame = window.session.current_image()
    assert getattr(frame, "pts_ticks", None) == ticks[10]
    method = window.session.method()
    params = effective_parameters(method, window.session.parameters())
    backend = backend_for("cpu")
    difference = preview_export_difference(method, backend, frame, params, record, k)
    print(f"V8 video k=2: mean {difference.mean_abs:.6f}, max {difference.max_abs:.6f}")
    assert difference.mean_abs <= MEAN_BOUND
    preview = render_host(
        method, backend, downscale(np.asarray(frame.pixels), k), frame.color, params, record
    )
    expected = image_bytes(display_image(to_display_uint8(preview), frame.color.icc_profile))
    assert np.array_equal(shown, expected)  # the shell shows the harness's preview side
    # R1-13: AD-11 as amended also bounds p99 at k = 2 (the harness reports mean and max only).
    # AD-11 sets that bound on real-sized content (at least 1080p), so at the fixture's 320 x 180
    # (p99 about 10/255) the figure is RECORDED here, not asserted (CHARC ruling ace08fbb); the
    # GX011627 window leg is the V8 video figure of record.
    export_side = downscale(
        render_host(method, backend, np.asarray(frame.pixels, dtype=np.float32), frame.color,
                    params, record),
        k,
    )  # fmt: skip
    gaps = np.abs(preview.astype(np.float64) - export_side.astype(np.float64))
    p99 = float(np.quantile(gaps, 0.99))
    print(f"V8 video k=2: p99 {p99:.6f} (fixture 320 x 180; a real-size frame is window evidence)")
    assert abs(float(gaps.mean()) - difference.mean_abs) < 1e-9  # the harness's own comparison


# V18 (gate form): a corrected frame before the analysis completes, the smoothed one after.


class HeldEngines:
    """The engine factory hook: the analysis's decode holds after its first frame until released.

    The hold is inside the engine's frame iteration (the DR-44 (c) test's form, B-4): while it
    holds, the analysis is running with its decode under way, and its statistics, smoothing and
    completion are all still to come. Every other call goes to the real frame source.
    """

    def __init__(self) -> None:
        self.release = threading.Event()
        self.advanced = 0
        self.ended = False

    def __call__(self, **kwargs: Any) -> AnalysisEngine:
        hook, inner = self, kwargs["source"]

        class Source:
            def __getattr__(self, name: str) -> Any:
                return getattr(inner, name)

            def frames(self, probe: Any, **options: Any) -> Any:
                try:
                    for frame in inner.frames(probe, **options):
                        hook.advanced += 1
                        yield frame
                        if hook.advanced == 1:
                            assert hook.release.wait(60)
                finally:
                    hook.ended = True

        return AnalysisEngine(**{**kwargs, "source": Source()})

    def mid_decode(self) -> bool:
        """The frame iterator has advanced and has not ended."""
        return self.advanced > 0 and not self.ended


def test_v18_a_corrected_frame_shows_before_the_analysis_completes_and_updates_after(
    make_app, qtbot, tmp_path, sample
) -> None:
    out = tmp_path / "out"
    out.mkdir()
    hook = HeldEngines()
    application = started(make_app, qtbot, out, engine_factory=hook)
    window = application.window
    rendered: list[Any] = []
    window.controller.rendered.connect(rendered.append)
    open_source(qtbot, application, sample(CLIP))
    qtbot.waitUntil(hook.mid_decode, timeout=60000)
    qtbot.waitUntil(lambda: bool(rendered) and window.controller.idle(), timeout=30000)
    assert hook.mid_decode()  # held inside the decode: the analysis is substantively unfinished
    assert window.session.analysis().phase == "running"
    assert window.preview_widget.after_image() is not None  # a corrected frame is shown
    assert window.session.statistics() is None  # its own provisional statistics (D108)
    before = len(rendered)
    hook.release.set()
    wait_analysis(qtbot, application)
    qtbot.waitUntil(lambda: window.session.statistics() is not None, timeout=30000)
    qtbot.waitUntil(lambda: len(rendered) > before, timeout=30000)
    qtbot.waitUntil(window.controller.idle, timeout=30000)
    shown = window.session.current_image()
    pts = getattr(shown, "pts_ticks", None)
    assert isinstance(pts, int)
    engine = latest_analysis(application)._engine
    assert engine is not None
    supplied = window.session.statistics()
    record = engine.smoothed_record(pts)
    assert list(supplied) == list(record)
    for stage in record:
        for name in record[stage]:
            assert np.array_equal(supplied[stage][name], record[stage][name]), (stage, name)
