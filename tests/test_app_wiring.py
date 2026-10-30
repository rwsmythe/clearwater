"""WP4.3 task 10: the G-matrix on the running shell that ``build_application`` makes.

One or more tests per G row, on the real engines over ``tmp_path`` app data and the WP2.3
fixtures (light run: forced CPU and the software encoder unless a row needs otherwise):

- G1 open a photo, a video and the DNG refusal through File > Open; G2 the split view;
- G3 the c3 schema's Basic and Advanced panels, ``"c3"`` first, and the live preview;
- G4 scrubbing shows stored proxies while the slider is down, then the full-resolution frame
  with its smoothed statistics on release; G5 analysis progress, cancel and Analyse again;
- G6 presets: the starters, save, load, import; G7 a batch skips a failed item, logs it and goes
  on; G8 export and batch progress and cancel with no partial output, completed files kept;
- G9 the work runs off the interface thread (the 100 ms figures are V7's,
  ``tests/test_app_v7.py``);
- G10 the HLG/PQ refusal, the truncated and untagged warnings, the DNG refusal, DR-35 (a)'s
  reserved name through the real engine, DR-82's refused output name per route (photo and
  video, single and batch);
- G11 is deferred to v2 (spec 0.5.3): no test;
- G12 every setting through the dialog, force CPU giving ``CPU: forced``; G13 persistence over two
  window lifetimes.
"""

# ``make_app`` is imported from test_app_startup and used as a parameter.
# ruff: noqa: F401, F811

from __future__ import annotations

import dataclasses
import logging
import sys
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from PIL import Image as PILImage

import gui_support
from clearwater.analysis import AnalysisEngine
from clearwater.app.activity import RENAME_TEXT
from clearwater.app.main import Application
from clearwater.config import load_settings
from clearwater.gui.batch_panel import BatchPanel, ItemState
from clearwater.gui.export_panel import ExportPanel
from clearwater.gui.parameter_panels import AdvancedPanel, BasicPanel
from clearwater.gui.preset_panel import PresetPanel
from clearwater.gui.settings_dialog import SettingsDialog
from clearwater.gui.timeline import TimelinePanel
from clearwater.interfaces import Settings
from clearwater.jobs import TEMP_MARKER
from test_app_startup import (
    CLIP,
    cpu_settings,
    latest_analysis,
    make_app,
    open_source,
    presenter,
    wait_analysis,
    wait_started,
)

pytestmark = [pytest.mark.gui, pytest.mark.usefixtures("ffmpeg_tools")]


def panel(application: Application, kind: type) -> Any:
    """The one panel of ``kind`` the application attached."""
    (found,) = application.window.findChildren(kind)
    return found


def started(make_app: Any, qtbot: Any, settings: Any = "light", **kwargs: Any) -> Any:
    """Build and start an application; ``settings`` None keeps the app data's own file."""
    application = make_app(cpu_settings() if settings == "light" else settings, **kwargs)
    wait_started(qtbot, application)
    return application


def wait_rendered(qtbot: Any, application: Application, timeout_ms: int = 60000) -> None:
    qtbot.waitUntil(application.window.controller.idle, timeout=timeout_ms)
    qtbot.wait(30)


def no_temporaries(folder: Path) -> bool:
    return not [p for p in folder.rglob("*") if TEMP_MARKER in p.name]


class Chooser:
    """File > Open's chooser, answering from a queue."""

    def __init__(self) -> None:
        self.paths: list[Path] = []

    def __call__(self, parent: Any) -> Path | None:
        return self.paths.pop(0) if self.paths else None


class Dialogs:
    """The Presets panel's dialogs, answering from queues."""

    def __init__(self) -> None:
        self.names: list[str] = []
        self.opens: list[Path] = []
        self.saves: list[Path] = []

    def ask_name(self, title: str, initial: str) -> str | None:
        return self.names.pop(0)

    def confirm(self, text: str) -> bool:
        return True

    def open_file(self) -> Path | None:
        return self.opens.pop(0)

    def save_file(self, initial_name: str) -> Path | None:
        return self.saves.pop(0)


class Choosers:
    """The settings dialog's folder chooser and confirmation."""

    def __init__(self) -> None:
        self.folder: Path | None = None

    def choose_folder(self, initial: Path | None) -> Path | None:
        return self.folder

    def confirm(self, text: str) -> bool:
        return True


# G1, G2, G3.


def test_g1_file_open_opens_a_photo_and_a_video_and_refuses_a_dng(make_app, qtbot, sample) -> None:
    chooser = Chooser()
    application = started(make_app, qtbot, choose_file=chooser)
    window = application.window
    for sample_id, kind in (("jpeg-gradient-srgb", "photo"), (CLIP, "video")):
        chooser.paths.append(sample(sample_id))
        window.shell_actions.open.trigger()
        qtbot.waitUntil(lambda: not window.opening(), timeout=30000)
        source = window.session.source()
        assert source is not None and source.kind == kind and source.path == sample(sample_id)
    chooser.paths.append(sample("dng-by-extension"))
    window.shell_actions.open.trigger()
    qtbot.waitUntil(lambda: not window.opening(), timeout=30000)
    refusals = presenter(application).of("refusal")
    assert refusals and "dng-by-extension.dng" in refusals[-1].text
    assert window.session.source().kind == "video"  # a refusal keeps the previous source


def test_g2_the_split_view_shows_before_and_after(make_app, qtbot, sample) -> None:
    application = started(make_app, qtbot)
    open_source(qtbot, application, sample("jpeg-gradient-srgb"))
    wait_rendered(qtbot, application)
    widget = application.window.preview_widget
    assert widget.before_image() is not None and widget.after_image() is not None
    assert widget.split() == 0.5
    widget.set_split(0.25)
    assert widget.split() == 0.25
    application.window.view_actions["reset_split"].trigger()
    assert widget.split() == 0.5


def test_g3_the_c3_schema_panels_drive_a_live_preview(make_app, qtbot, sample) -> None:
    application = started(make_app, qtbot)
    window = application.window
    assert next(iter(window.context.engines.methods)) == "c3"
    basic, advanced = panel(application, BasicPanel), panel(application, AdvancedPanel)
    method = window.session.method()
    assert method.id == "c3"
    shown = set(basic.controls()) | set(advanced.controls())
    assert shown == {p.name for p in method.parameters}
    open_source(qtbot, application, sample("jpeg-lowred-srgb"))
    wait_rendered(qtbot, application)
    before = window.preview_widget.after_image()
    rendered: list[object] = []
    window.controller.rendered.connect(rendered.append)
    assert "blend_with_original" in basic.controls()
    blend = next(p for p in method.parameters if p.name == "blend_with_original")
    window.session.set_parameters(
        dataclasses.replace(
            window.session.parameters(), parameters={"blend_with_original": blend.maximum}
        )
    )
    wait_rendered(qtbot, application)
    assert rendered, "a parameter change did not re-render the preview"
    assert window.preview_widget.after_image() != before


# G4, G5.


def test_g4_scrubbing_shows_proxies_then_the_full_frame_with_smoothed_statistics(
    make_app, qtbot, sample, monkeypatch
) -> None:
    application = started(make_app, qtbot)
    window = application.window
    open_source(qtbot, application, sample(CLIP))
    wait_analysis(qtbot, application)
    timeline = panel(application, TimelinePanel)
    analysis = latest_analysis(application)
    ticks = analysis.pts()
    assert len(ticks) == 45 and timeline.pts() == ticks
    proxies: list[tuple[int, int]] = []
    real = window.preview_widget.set_proxy

    def spy(before: Any, after: Any) -> None:
        proxies.append((before.width(), before.height()))
        real(before, after)

    monkeypatch.setattr(window.preview_widget, "set_proxy", spy)
    slider = timeline.slider()
    slider.setSliderDown(True)
    slider.setValue(20)
    qtbot.waitUntil(lambda: bool(proxies), timeout=10000)
    assert window.session.position() != ticks[20]  # no full-resolution frame while dragging
    slider.setSliderDown(False)
    qtbot.waitUntil(lambda: window.session.position() == ticks[20], timeout=10000)
    wait_rendered(qtbot, application)
    shown = window.session.current_image()
    assert getattr(shown, "pts_ticks", None) == ticks[20]
    assert window.session.statistics() is not None  # the smoothed record (D108)


def test_g5_analysis_progress_cancel_and_analyse_again(make_app, qtbot, sample) -> None:
    application = started(make_app, qtbot)
    window = application.window
    states: list[Any] = []
    window.session.analysis_changed.connect(states.append)
    open_source(qtbot, application, sample(CLIP))
    timeline = panel(application, TimelinePanel)
    timeline.cancel_analysis()
    wait_analysis(qtbot, application, "cancelled")
    assert any(s.phase == "running" for s in states)
    assert window.shell_actions.export.unavailable_reason() is not None  # AD-15
    timeline.start_analysis()
    wait_analysis(qtbot, application)
    progress = [s for s in states if s.phase == "running" and s.done > 0]
    assert progress, "no progress was reported"
    assert window.shell_actions.export.isEnabled()


# G6, G7, G8.


def test_g6_presets_starters_save_load_import(make_app, qtbot, tmp_path) -> None:
    dialogs = Dialogs()
    application = started(make_app, qtbot, preset_dialogs=dialogs)
    window = application.window
    presets = panel(application, PresetPanel)
    names = [presets.list.item(i).text() for i in range(presets.list.count())]
    assert {"Snorkel (shallow)", "Scuba (deep)"} <= set(names)  # the starters (G6)
    store = window.context.presets

    def stored() -> list[str]:
        return [entry.name for entry in store.list_presets()]

    dialogs.names.append("Mine")
    presets.save_as()
    assert "Mine" in stored()
    dialogs.saves.append(tmp_path / "shared.json")
    presets.select("Mine")
    presets.export()
    assert (tmp_path / "shared.json").exists()
    presets.select("Scuba (deep)")
    presets.load()
    assert window.session.parameters().parameters == store.load("Scuba (deep)").parameters
    count = len(stored())
    dialogs.opens.append(tmp_path / "shared.json")
    presets.import_file()
    assert "shared" in stored() and len(stored()) == count + 1


def test_g7_a_batch_skips_a_failed_item_logs_it_and_goes_on(
    make_app, qtbot, sample, tmp_path, caplog
) -> None:
    out = tmp_path / "out"
    out.mkdir()
    damaged = tmp_path / "damaged.jpg"
    damaged.write_bytes(b"not a jpeg")
    application = started(make_app, qtbot, cpu_settings(output_folder=out))
    batch = panel(application, BatchPanel)
    batch.add_paths([sample("jpeg-gradient-srgb"), damaged, sample(CLIP)])
    with caplog.at_level(logging.WARNING):
        batch.start()
        qtbot.waitUntil(lambda: not batch.is_running(), timeout=180000)
    states = [item.state for item in batch.items()]
    assert states == [ItemState.DONE, ItemState.FAILED, ItemState.DONE]
    assert sorted(p.name for p in out.iterdir()) == [
        "hevc8-bt709-full_corrected.mp4",
        "jpeg-gradient-srgb_corrected.png",
    ]
    assert "damaged.jpg" in batch.report.toPlainText()
    assert "batch item failed" in caplog.text and "damaged.jpg" in caplog.text


def test_g8_export_cancel_leaves_no_partial_output(make_app, qtbot, sample, tmp_path) -> None:
    out = tmp_path / "out"
    out.mkdir()
    application = started(make_app, qtbot, cpu_settings(output_folder=out))
    window = application.window
    open_source(qtbot, application, sample(CLIP))
    wait_analysis(qtbot, application)
    export = panel(application, ExportPanel)
    window.shell_actions.export.trigger()
    qtbot.waitUntil(lambda: export.bar.maximum() > 0 and export.bar.value() > 0, timeout=60000)
    export.cancel()
    qtbot.waitUntil(lambda: not export.is_running(), timeout=60000)
    assert export.status.text().startswith("Export cancelled")
    assert list(out.iterdir()) == []
    assert application.journal.entries() == ()


def test_g8_batch_cancel_keeps_completed_files_and_stops_the_rest(
    make_app, qtbot, sample, tmp_path
) -> None:
    out = tmp_path / "out"
    out.mkdir()
    application = started(make_app, qtbot, cpu_settings(output_folder=out))
    batch = panel(application, BatchPanel)
    batch.add_paths([sample("jpeg-gradient-srgb"), sample(CLIP), sample("png16-gradient-srgb")])
    batch.start()
    qtbot.waitUntil(lambda: batch.items()[1].state is ItemState.RUNNING, timeout=60000)
    qtbot.waitUntil(lambda: batch.bar.value() > 0, timeout=60000)
    batch.cancel()
    qtbot.waitUntil(lambda: not batch.is_running(), timeout=60000)
    states = [item.state for item in batch.items()]
    assert states[0] is ItemState.DONE and states[1] is ItemState.CANCELLED
    assert states[2] is not ItemState.DONE
    assert [p.name for p in out.iterdir()] == ["jpeg-gradient-srgb_corrected.png"]
    assert no_temporaries(out)


# G9.


def test_g9_the_engines_run_off_the_interface_thread(make_app, qtbot, sample, monkeypatch) -> None:
    from clearwater.analysis import AnalysisEngine
    from clearwater.app.composition import DeferredProxyCache

    threads: list[threading.Thread] = []
    real_target = DeferredProxyCache._target

    def target(self: DeferredProxyCache) -> Any:
        threads.append(threading.current_thread())
        return real_target(self)

    monkeypatch.setattr(DeferredProxyCache, "_target", target)  # S1 condition 2: every member
    application = started(make_app, qtbot)
    open_source(qtbot, application, sample(CLIP))
    wait_analysis(qtbot, application)
    dialog_open(application, qtbot)
    assert threads and all(t is not threading.main_thread() for t in threads)


def dialog_open(application: Application, qtbot: Any) -> SettingsDialog:
    window = application.window
    window.shell_actions.settings.trigger()
    dialog = window._settings_dialog
    assert isinstance(dialog, SettingsDialog)
    qtbot.waitUntil(lambda: dialog.encoder_combo.isEnabled(), timeout=10000)
    return dialog


# G10.


@pytest.mark.parametrize(
    ("sample_id", "severity", "words"),
    [
        ("vid-hlg", "refusal", "HLG"),
        ("vid-pq", "refusal", "PQ"),
        ("vid-truncated", "warning", "cut short"),
        ("vid-untagged", "warning", ""),
        ("dng-by-tag", "refusal", ""),
    ],
    ids=["hlg", "pq", "truncated", "untagged", "dng"],
)
def test_g10_damaged_unsupported_and_untagged_inputs_get_a_readable_message(
    make_app, qtbot, sample, sample_id, severity, words
) -> None:
    application = started(make_app, qtbot)
    path = sample(sample_id)
    application.window.open_path(path)
    qtbot.waitUntil(lambda: not application.window.opening(), timeout=30000)
    shown = presenter(application).of(severity)
    assert shown, presenter(application).messages
    assert any(m.path == path or path.name in m.text for m in shown)
    assert all(m.text.isascii() for m in shown)
    assert any(words.lower() in m.text.lower() for m in shown)


def test_g10_dr35a_a_reserved_device_name_is_refused_readably(
    make_app, qtbot, sample, tmp_path
) -> None:
    """DR-35 (a): stem ``NU`` + suffix ``L`` -> ``NUL.png``; refused before any write."""
    out, source = tmp_path / "out", tmp_path / "NU.jpg"
    out.mkdir()
    source.write_bytes(sample("jpeg-gradient-srgb").read_bytes())
    application = started(make_app, qtbot, cpu_settings(output_folder=out, output_suffix="L"))
    open_source(qtbot, application, source)
    export = panel(application, ExportPanel)
    application.window.shell_actions.export.trigger()
    qtbot.waitUntil(lambda: not export.is_running(), timeout=60000)
    (error,) = [m for m in presenter(application).of("error") if m.owner == "export"]
    assert "NUL.png is a reserved device name on Windows; change the output suffix." in error.text
    assert list(out.iterdir()) == []


def _ads(folder: Path, name: str, data: bytes) -> Path:
    """An NTFS alternate data stream ``carrier:<name>`` holding ``data`` (Windows only)."""
    if sys.platform != "win32":
        pytest.skip("a source name the output rule refuses needs an NTFS stream here")
    carrier = folder / "carrier"
    carrier.write_bytes(b"carrier")
    path = Path(f"{carrier}:{name}")
    try:
        path.write_bytes(data)
    except OSError as exc:
        pytest.skip(f"alternate data streams unavailable: {type(exc).__name__}")
    return path


@pytest.mark.parametrize("kind", ["photo", "video"])
def test_g10_dr82_the_single_export_of_a_refused_name_says_to_rename_it(
    make_app, qtbot, sample, tmp_path, kind
) -> None:
    out = tmp_path / "out"
    out.mkdir()
    source_id, name = ("jpeg-gradient-srgb", "in.jpg") if kind == "photo" else (CLIP, "clip.mp4")
    source = _ads(tmp_path, name, sample(source_id).read_bytes())
    application = started(make_app, qtbot, cpu_settings(output_folder=out))
    open_source(qtbot, application, source)
    if kind == "video":
        wait_analysis(qtbot, application)
    export = panel(application, ExportPanel)
    application.window.shell_actions.export.trigger()
    qtbot.waitUntil(lambda: not export.is_running(), timeout=60000)
    errors = [m for m in presenter(application).of("error") if m.owner == "export"]
    assert len(errors) == 1  # item 2 of ruling 68d5b4c7: the panel's final text, the name once
    assert errors[0].text == (
        f"{source.name}: this file name cannot be used for an output file; rename the file."
    )
    assert list(out.iterdir()) == []


@pytest.mark.parametrize("kind", ["photo", "video"])
def test_g10_dr82_the_wrappers_refusal_on_every_os(
    make_app, qtbot, sample, tmp_path, monkeypatch, kind
) -> None:
    """Ruling 68d5b4c7: the PORTABLE form, ``final_output_path`` planted to refuse the name.

    The NTFS-stream test above is the real-name proof on Windows; this one proves the wrapper's
    branch on every OS: the panel's text names the source once, the engine never runs, nothing
    is written.
    """
    from clearwater.app import activity
    from clearwater.jobs import OutputNameError

    out = tmp_path / "out"
    out.mkdir()
    source = sample("jpeg-gradient-srgb" if kind == "photo" else CLIP)
    application = started(make_app, qtbot, cpu_settings(output_folder=out))
    open_source(qtbot, application, source)
    if kind == "video":
        wait_analysis(qtbot, application)

    def refuse(path: Path, settings: Settings, media: Any) -> Path:
        raise OutputNameError("planted")

    ran: list[str] = []
    real_job = application.exports._engine.job

    def job(request: Any) -> Any:
        inner = real_job(request)

        def run(progress: Any) -> Any:
            ran.append("engine")
            return inner(progress)

        return run

    monkeypatch.setattr(activity, "final_output_path", refuse)
    monkeypatch.setattr(application.exports._engine, "job", job)
    export = panel(application, ExportPanel)
    application.window.shell_actions.export.trigger()
    qtbot.waitUntil(lambda: not export.is_running(), timeout=60000)
    errors = [m for m in presenter(application).of("error") if m.owner == "export"]
    assert [m.text for m in errors] == [
        f"{source.name}: this file name cannot be used for an output file; rename the file."
    ]
    assert ran == [] and list(out.iterdir()) == []


def test_g10_dr82_a_batch_item_with_a_refused_name_is_failed_and_skipped(
    make_app, qtbot, sample, tmp_path
) -> None:
    out = tmp_path / "out"
    out.mkdir()
    photo, video = tmp_path / "carrier:in.jpg", tmp_path / "carrier:clip.mp4"
    application = started(make_app, qtbot, cpu_settings(output_folder=out))
    batch = panel(application, BatchPanel)
    batch.add_paths([photo, video, sample("jpeg-gradient-srgb")])
    batch.start()
    qtbot.waitUntil(lambda: not batch.is_running(), timeout=120000)
    items = batch.items()
    assert [i.state for i in items] == [ItemState.FAILED, ItemState.FAILED, ItemState.DONE]
    assert items[0].failure == RENAME_TEXT and items[1].failure == RENAME_TEXT
    assert [p.name for p in out.iterdir()] == ["jpeg-gradient-srgb_corrected.png"]


# G12, G13.


def test_g12_every_setting_through_the_dialog(
    make_app, qtbot, sample, tmp_path, monkeypatch
) -> None:
    from clearwater import core
    from clearwater.core.backend import NumpyBackend

    def select(settings: Settings, height: int, width: int, method_id: str) -> Any:
        return NumpyBackend(), "CPU: forced" if settings.force_cpu else "CPU: no CUDA device"

    monkeypatch.setattr(core, "select_backend", select)  # the light run stays on the CPU
    out = tmp_path / "chosen"
    out.mkdir()
    choosers = Choosers()
    application = started(make_app, qtbot, cpu_settings(force_cpu=False), choosers=choosers)
    window = application.window
    open_source(qtbot, application, sample(CLIP))
    wait_analysis(qtbot, application)  # an entry in the cache, for Clear cache
    assert application.cache.lookup(application.cache.key_for(sample(CLIP))) is not None
    dialog = dialog_open(application, qtbot)
    choosers.folder = out
    dialog.choose_folder_button.click()
    dialog.suffix_edit.setText("_g12")
    dialog.png_combo.setCurrentIndex(dialog.png_combo.findData(8))
    dialog.encoder_combo.setCurrentIndex(dialog.encoder_combo.findData("libx265"))
    dialog.quality_combo.setCurrentIndex(dialog.quality_combo.findData("draft"))
    dialog.ten_bit_check.setChecked(True)
    dialog.provenance_check.setChecked(False)
    dialog.cache_spin.setValue(3)
    dialog.force_cpu_check.setChecked(True)
    dialog.clear_button.click()
    qtbot.waitUntil(lambda: dialog.cache_note.text() == "Cache cleared.", timeout=30000)
    dialog.accept()
    settings = window.session.settings()
    assert (settings.output_folder, settings.output_suffix, settings.png_bit_depth) == (
        out,
        "_g12",
        8,
    )
    assert (settings.video_encoder, settings.quality_level) == ("libx265", "draft")
    assert settings.ten_bit_for_eight_bit and not settings.provenance and settings.force_cpu
    assert settings.cache_limit_bytes == 3 * 10**9
    qtbot.waitUntil(lambda: application.cache.limit_bytes() == 3 * 10**9, timeout=30000)
    assert application.cache.lookup(application.cache.key_for(sample(CLIP))) is None  # cleared
    assert load_settings(window.context.locations.config_dir) == settings  # saved (G13)
    wait_rendered(qtbot, application)
    assert window.device_label.text() == "Device: CPU: forced"  # AD-9
    photo = sample("jpeg-gradient-srgb")
    open_source(qtbot, application, photo)
    export = panel(application, ExportPanel)
    window.shell_actions.export.trigger()
    qtbot.waitUntil(lambda: not export.is_running(), timeout=60000)
    written = out / "jpeg-gradient-srgb_g12.png"
    assert written.exists()
    with PILImage.open(written) as png:
        assert png.mode == "RGB"  # 8-bit
        assert "clearwater-provenance" not in png.info  # provenance off (D91)


def test_g13_settings_and_last_parameters_persist_over_two_window_lifetimes(
    make_app, qtbot, tmp_path
) -> None:
    where = tmp_path / "home"
    first = started(make_app, qtbot, cpu_settings(output_suffix="_kept"), where=where)
    parameters = first.window.session.parameters()
    method = first.window.session.method()
    name = method.parameters[0].name
    changed = dataclasses.replace(parameters, parameters={name: method.parameters[0].maximum})
    first.window.session.set_parameters(changed)
    first.window.close()
    second = started(make_app, qtbot, None, where=where)
    assert second.window.session.settings().output_suffix == "_kept"
    assert second.window.session.parameters().parameters == changed.parameters


# DR-44 (c) (question 8 as ruled): measured with the real jobs at close.


class _ProgressSource:
    """A frame source that records how far its frames have been read (R3-5).

    Its first ``frames`` iterator holds after its first frame until ``release`` is set, so the
    close begins with the decode under way; every other call goes to ``inner``. The iterator has
    ended once it runs out, is closed or raises (R4-1).
    """

    def __init__(self, inner: Any, release: threading.Event) -> None:
        self._inner = inner
        self._release = release
        self.advanced = 0
        self.ended = False

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)

    def frames(self, probe: Any, **kwargs: Any) -> Any:
        try:
            for frame in self._inner.frames(probe, **kwargs):
                self.advanced += 1
                yield frame
                if self.advanced == 1:
                    self._release.wait(60)
        finally:
            self.ended = True

    def mid_decode(self) -> bool:
        """The frame iterator has advanced and has not ended."""
        return self.advanced > 0 and not self.ended


class _ProgressSink:
    """A video sink that records its progress (R3-5).

    Its first ``write`` holds after the frame is written until ``release`` is set, so the close
    begins with the encode under way; every other call goes to ``inner``.
    """

    def __init__(self, inner: Any, release: threading.Event) -> None:
        self._inner = inner
        self._release = release
        self.opened = False
        self.written = 0
        self.closed = False

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)

    def open(self, *args: Any, **kwargs: Any) -> Any:
        result = self._inner.open(*args, **kwargs)
        self.opened = True
        return result

    def write(self, frame: Any) -> None:
        self._inner.write(frame)
        self.written += 1
        if self.written == 1:
            self._release.wait(60)

    def close(self) -> Any:
        self.closed = True
        return self._inner.close()

    def abort(self) -> None:
        self.closed = True
        self._inner.abort()

    def mid_encode(self) -> bool:
        """The sink is open and has written frames, and neither its close nor its abort began."""
        return self.opened and self.written > 0 and not self.closed


def test_the_progress_source_has_ended_once_its_iterator_closes_or_runs_out() -> None:
    """R4-1: an iterator its consumer closes after frame 1 (a processing failure) is not mid-decode.

    Pure Python (no window): the R3-5 predicate must not stay True for a stopped decode.
    """

    class Inner:
        def frames(self, probe: Any, **kwargs: Any) -> Any:
            yield from range(5)

    release = threading.Event()
    source = _ProgressSource(Inner(), release)
    iterator = source.frames(None, hw_decode=False)
    next(iterator)
    assert source.mid_decode()
    iterator.close()  # what ``AnalysisEngine._decode`` does when processing a frame fails
    assert not source.mid_decode()
    release.set()
    exhausted = _ProgressSource(Inner(), release)
    assert list(exhausted.frames(None, hw_decode=False)) == [0, 1, 2, 3, 4]
    assert not exhausted.mid_decode()


@pytest.mark.slow
@pytest.mark.parametrize("job", ["analysis", "export", "batch"])
def test_dr44c_a_real_job_ends_within_the_shutdown_timeout_at_close(
    make_app, qtbot, sample, tmp_path, monkeypatch, job
) -> None:
    """From ``close()``: an analysis mid-decode, an export mid-encode, a batch item.

    "Mid-decode" and "mid-encode" are predicates read when the first job runner's ``close``
    begins (R3-5), not a timing: the analysis's frame source has yielded a frame, its iterator
    has not ended (run out, closed or raised; R4-1) and the analysis phase is ``running``; the
    export's sink is open and has written a frame, and neither its
    close nor its abort has begun. Each holds its job after the first frame until that moment,
    so the predicate cannot be missed; the hold is released as the close begins and the job then
    ends by its own cancel path.
    """
    from clearwater.gui.jobs import QtJobRunner
    from clearwater.gui.shell import SHUTDOWN_TIMEOUT_S

    out = tmp_path / "out"
    out.mkdir()
    release = threading.Event()
    progress: dict[str, Callable[[], bool]] = {}
    closes: list[tuple[bool, float]] = []
    at_close: list[bool] = []
    real_close = QtJobRunner.close

    def timed(self: QtJobRunner, timeout_s: float) -> bool:
        if not at_close:
            at_close.append(progress["predicate"]())
            release.set()
        began = time.perf_counter()
        ended = real_close(self, timeout_s)
        closes.append((ended, time.perf_counter() - began))
        return ended

    def engine_factory(**kwargs: Any) -> AnalysisEngine:
        source = _ProgressSource(kwargs["source"], release)
        progress["predicate"] = lambda: (
            source.mid_decode() and window.session.analysis().phase == "running"
        )
        return AnalysisEngine(**{**kwargs, "source": source})

    monkeypatch.setattr(QtJobRunner, "close", timed)
    try:
        if job == "analysis":
            application = started(
                make_app, qtbot, cpu_settings(output_folder=out), engine_factory=engine_factory
            )
            window = application.window
            window.open_path(sample(CLIP))
            qtbot.waitUntil(
                lambda: "predicate" in progress and progress["predicate"](), timeout=60000
            )
        elif job == "export":
            application = started(make_app, qtbot, cpu_settings(output_folder=out))
            window = application.window
            open_source(qtbot, application, sample(CLIP))
            wait_analysis(qtbot, application)
            # WP4.6: the export runs in a worker process, so the test worker holds its sink's
            # first write on marker files (mid-encode: a frame written, the call not returned);
            # the close's cancel releases it (ruling R0-STOP-1).
            import export_worker_hold as hold
            from clearwater.jobs.export_process import ProcessExportJobs

            engine = application.exports._engine
            assert isinstance(engine, ProcessExportJobs)
            markers = hold.fresh(tmp_path / "export-hold")
            progress["predicate"] = lambda: hold.in_write(markers)
            monkeypatch.setattr(engine, "_command", hold.command(markers))
            window.shell_actions.export.trigger()
            qtbot.waitUntil(
                lambda: "predicate" in progress and progress["predicate"](), timeout=60000
            )
        else:
            application = started(make_app, qtbot, cpu_settings(output_folder=out))
            window = application.window
            batch = panel(application, BatchPanel)
            batch.add_paths([sample(CLIP), sample("jpeg-gradient-srgb")])
            batch.start()
            qtbot.waitUntil(lambda: batch.items()[0].state is ItemState.RUNNING, timeout=60000)
            qtbot.waitUntil(lambda: batch.bar.value() > 0, timeout=60000)
            progress["predicate"] = lambda: batch.items()[0].state is ItemState.RUNNING
        window.close()
    finally:
        release.set()
    (ended, elapsed) = closes[0]
    print(f"DR-44 (c) {job}: ended {ended} in {elapsed * 1000:.0f} ms, at close {at_close}")
    if job != "batch":  # a batch item's state is printed, not asserted
        assert at_close == [True], f"the job was not under way when the close began ({job})"
    assert ended and elapsed < SHUTDOWN_TIMEOUT_S
    assert no_temporaries(out)


def test_dr49_the_shipped_schemas_resolve_at_six_decimals_or_fewer(make_app, qtbot) -> None:
    """DR-49's ground, on the running shell: every float control of both methods."""
    from clearwater.gui.parameter_panels import float_decimals

    application = started(make_app, qtbot)
    for method in application.window.context.engines.methods.values():
        floats = [p for p in method.parameters if p.type == "float"]
        assert floats, method.id
        assert max(float_decimals(p) for p in floats) <= 6, method.id


def test_s1_a_limit_and_a_clear_from_the_dialog_during_the_open_apply_after_it(
    make_app, qtbot, monkeypatch, sample
) -> None:
    """S1 conditions 2 and 3, on the running shell: queued behind the open, off the UI thread."""
    from clearwater.app import composition
    from clearwater.app.composition import DeferredProxyCache

    release = threading.Event()
    real_open = composition.proxy_cache

    def slow(folder: Path, limit: int = 0) -> Any:
        assert release.wait(60)
        return real_open(folder, limit)

    threads: list[threading.Thread] = []
    real_target = DeferredProxyCache._target

    def target(self: DeferredProxyCache) -> Any:
        threads.append(threading.current_thread())
        return real_target(self)

    monkeypatch.setattr(composition, "proxy_cache", slow)
    monkeypatch.setattr(DeferredProxyCache, "_target", target)
    application = make_app(cpu_settings(cache_limit_bytes=20 * 10**9), choosers=Choosers())
    window = application.window
    qtbot.waitUntil(lambda: not application.catalog.detecting(), timeout=30000)
    dialog = dialog_open(application, qtbot)
    assert not application.cache.wait_open(0)  # the open is still running
    dialog.clear_button.click()
    dialog.cache_spin.setValue(4)
    dialog.accept()
    qtbot.wait(200)
    assert window.jobs.active() >= 3  # the open, the clear and the limit wait on workers
    release.set()
    qtbot.waitUntil(lambda: window.jobs.active() == 0, timeout=60000)
    # The product's calls first: the test's own limit read below runs on this thread.
    assert threads and all(t is not threading.main_thread() for t in threads)
    assert application.cache.limit_bytes() == 4 * 10**9  # the dialog's, applied after the open
    open_source(qtbot, application, sample("jpeg-gradient-srgb"))  # the window stayed usable
