"""WP3.20 settings dialog (G12, G13, D74, D71, AD-9, DR-35, DR-44 (b)) and the refusal (S4).

WP4.3 deleted the stand-in rule and its mirror test (DR-52): WP3.10's ``resolve_encoder`` is the
default, ``install_settings_dialog`` takes the start-up's catalog, and the DR-61 cases are at the
end. Every test drives the dialog through the shell: ``Tools > Settings`` triggers the factory
that ``install_settings_dialog`` registered. The folder chooser and the confirmation are
injected, the sink reports a chosen capability list, the cache records the thread of every call,
and the locations are under ``tmp_path``.
"""

# The shared fixtures ``make_window`` (gui_support) and ``make_app`` (test_app_startup) are
# imported and used as parameters.
# ruff: noqa: F401, F811

from __future__ import annotations

import dataclasses
import logging
import threading
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog

from clearwater.config import load_settings, save_settings
from clearwater.gui import AnalysisState, Message, stub_engines
from clearwater.gui import settings_dialog as module
from clearwater.gui.settings_dialog import (
    AUTO_TEXT,
    CLEAR_BLOCKED_REASON,
    NO_ENCODER_REASON,
    NOT_FOUND_REASON,
    OWNER_SETTINGS,
    SAME_FOLDER_TEXT,
    SettingsDialog,
    install_settings_dialog,
)
from clearwater.gui.shell import MainWindow
from clearwater.interfaces import EncoderCapability, Settings
from clearwater.interfaces.stubs import StubProxyCache, StubVideoSink
from clearwater.io.video import capability
from clearwater.io.video.encode import VideoEncodeError
from clearwater.jobs import TEMP_MARKER, validate_suffix
from gui_support import image, make_window, open_and_wait, photo_engines, presenter_of, wait_idle
from test_app_startup import cpu_settings, make_app
from test_app_startup import presenter as startup_presenter

pytestmark = pytest.mark.gui

NVENC = EncoderCapability("hevc_nvenc", False, "No NVIDIA encoder was found.", (), True)
X265 = EncoderCapability("libx265", True, None, (8, 10), False)
CAPS = (NVENC, X265)


class CapsSink(StubVideoSink):
    """A sink reporting a chosen capability list (or raising)."""

    def __init__(self, caps: Sequence[EncoderCapability], fail: str | None = None) -> None:
        super().__init__()
        self.caps = tuple(caps)
        self.fail = fail
        self.threads: list[threading.Thread] = []

    def capabilities(self) -> tuple[EncoderCapability, ...]:
        self.threads.append(threading.current_thread())
        if self.fail is not None:
            raise RuntimeError(self.fail)
        return self.caps


class RecordingCache(StubProxyCache):
    """A cache recording the thread of every clear and every limit change."""

    def __init__(self, fail: bool = False) -> None:
        super().__init__()
        self.cleared: list[threading.Thread] = []
        self.limits: list[tuple[int, threading.Thread]] = []
        self.fail = fail
        self.first_limit_entered = threading.Event()
        self.release_first_limit: threading.Event | None = None  # set: the first call blocks on it

    def clear(self) -> None:
        self.cleared.append(threading.current_thread())
        if self.fail:
            raise OSError("disk is busy")
        super().clear()

    def set_limit_bytes(self, n: int) -> None:
        self.limits.append((n, threading.current_thread()))
        if len(self.limits) == 1 and self.release_first_limit is not None:
            self.first_limit_entered.set()
            assert self.release_first_limit.wait(10)
        if self.fail:
            raise OSError("disk is busy")
        super().set_limit_bytes(n)


class FakeChoosers:
    """Records the questions; never shows a dialog."""

    def __init__(self) -> None:
        self.folder: Path | None = None
        self.answer = True
        self.asked_folder: list[Path | None] = []
        self.confirms: list[str] = []
        self.while_open: Callable[[], None] | None = None
        self.raise_on_choose: Exception | None = None
        self.raise_on_confirm: Exception | None = None

    def choose_folder(self, initial: Path | None) -> Path | None:
        self.asked_folder.append(initial)
        if self.raise_on_choose is not None:
            raise self.raise_on_choose
        return self.folder

    def confirm(self, text: str) -> bool:
        self.confirms.append(text)
        if self.raise_on_confirm is not None:
            raise self.raise_on_confirm
        if self.while_open is not None:  # what happens while the modal box runs its event loop
            self.while_open()
        return self.answer


class Env:
    """One test's windows, engines and fakes."""

    def __init__(self, qtbot: Any, build: Callable[..., MainWindow], tmp_path: Path) -> None:
        self.qtbot = qtbot
        self.build = build
        self.config = tmp_path / "config"
        self.choosers = FakeChoosers()
        self.sink = CapsSink(CAPS)
        self.cache = RecordingCache()
        self.resolve_calls: list[tuple[str, tuple[EncoderCapability, ...]]] = []

    def start(
        self,
        *,
        caps: Sequence[EncoderCapability] = CAPS,
        fail: str | None = None,
        saved: Settings | None = None,
        raw: str | None = None,
        cache_fails: bool = False,
        resolve: Callable[[str, Sequence[EncoderCapability]], str] | None = None,
        photo: Path | None = None,
    ) -> MainWindow:
        """Build a window on this test's folders with the dialog installed."""
        if saved is not None:
            save_settings(self.config, saved)
        if raw is not None:
            self.config.mkdir(parents=True, exist_ok=True)
            (self.config / "settings.json").write_text(raw, encoding="utf-8")
        self.sink = CapsSink(caps, fail)
        self.cache = RecordingCache(cache_fails)
        base = photo_engines({photo: image(40, 60)}) if photo is not None else stub_engines()
        engines = dataclasses.replace(base, video_sink=self.sink, cache=self.cache)
        window = self.build(engines)
        if resolve is None:
            install_settings_dialog(window, choosers=self.choosers)
        else:

            def spy(setting: str, capabilities: Sequence[EncoderCapability]) -> str:
                self.resolve_calls.append((setting, tuple(capabilities)))
                return resolve(setting, capabilities)

            install_settings_dialog(window, choosers=self.choosers, resolve_encoder=spy)
        return window

    def open(self, window: MainWindow) -> SettingsDialog:
        """Trigger Tools > Settings and wait for the encoder list."""
        window.shell_actions.settings.trigger()
        dialog = window._settings_dialog
        assert isinstance(dialog, SettingsDialog)
        self.qtbot.waitUntil(lambda: dialog.encoder_combo.isEnabled(), timeout=5000)
        return dialog

    def idle(self, window: MainWindow) -> None:
        """Wait until every job has delivered its result."""
        self.qtbot.waitUntil(lambda: window.jobs.active() == 0, timeout=5000)
        self.qtbot.wait(20)

    def saved(self) -> Settings:
        """The settings file as ``load_settings`` reads it."""
        return load_settings(self.config)


@pytest.fixture
def env(qtbot: Any, make_window: Callable[..., MainWindow], tmp_path: Path) -> Env:
    return Env(qtbot, make_window, tmp_path)


def pick(combo: Any, data: object) -> None:
    """Choose the item holding ``data`` as a user would."""
    index = combo.findData(data)
    assert index >= 0, data
    combo.setCurrentIndex(index)


def items(combo: Any) -> list[tuple[Any, str, bool, str]]:
    """(data, text, enabled, tool tip) of every item of a combo."""
    model = combo.model()
    return [
        (
            combo.itemData(i),
            combo.itemText(i),
            model.item(i).isEnabled(),
            combo.itemData(i, Qt.ItemDataRole.ToolTipRole) or "",
        )
        for i in range(combo.count())
    ]


# First run (G12 defaults).


def test_first_run_shows_g12_defaults(env: Env) -> None:
    window = env.start()
    dialog = env.open(window)
    assert dialog.folder_label.text() == SAME_FOLDER_TEXT
    assert dialog.suffix_edit.text() == "_corrected"
    assert dialog.png_combo.currentData() == 16
    assert dialog.encoder_combo.currentData() == "auto"
    assert dialog.encoder_combo.currentText() == AUTO_TEXT
    assert dialog.quality_combo.currentData() == "standard"
    assert dialog.quality_combo.currentText() == "Standard"
    assert not dialog.ten_bit_check.isChecked()
    assert dialog.provenance_check.isChecked()
    assert dialog.cache_spin.value() == 20
    assert not dialog.force_cpu_check.isChecked()
    assert dialog.ok_button.isEnabled()
    assert not dialog.refusal_label.isVisibleTo(dialog)
    assert dialog.edited_settings() == Settings()


def test_quality_names_and_stored_forms(env: Env) -> None:
    window = env.start()
    dialog = env.open(window)
    assert [(d, t) for d, t, *_ in items(dialog.quality_combo)] == [
        ("high", "High"),
        ("standard", "Standard"),
        ("draft", "Draft"),
    ]
    assert [d for d, *_ in items(dialog.png_combo)] == [16, 8]


# Round trip (G12) and persistence (G13).


def _set_folder(env: Env, dialog: SettingsDialog) -> None:
    env.choosers.folder = Path("out")
    dialog.choose_folder_button.click()


def _set_suffix(env: Env, dialog: SettingsDialog) -> None:
    dialog.suffix_edit.setText("_clean")


def _set_png(env: Env, dialog: SettingsDialog) -> None:
    pick(dialog.png_combo, 8)


def _set_encoder(env: Env, dialog: SettingsDialog) -> None:
    pick(dialog.encoder_combo, "libx265")


def _set_quality(env: Env, dialog: SettingsDialog) -> None:
    pick(dialog.quality_combo, "draft")


def _set_ten_bit(env: Env, dialog: SettingsDialog) -> None:
    dialog.ten_bit_check.setChecked(True)


def _set_provenance(env: Env, dialog: SettingsDialog) -> None:
    dialog.provenance_check.setChecked(False)


def _set_cache(env: Env, dialog: SettingsDialog) -> None:
    dialog.cache_spin.setValue(5)


def _set_force_cpu(env: Env, dialog: SettingsDialog) -> None:
    dialog.force_cpu_check.setChecked(True)


ROUND_TRIPS = [
    (_set_folder, {"output_folder": Path("out")}),
    (_set_suffix, {"output_suffix": "_clean"}),
    (_set_png, {"png_bit_depth": 8}),
    (_set_encoder, {"video_encoder": "libx265"}),
    (_set_quality, {"quality_level": "draft"}),
    (_set_ten_bit, {"ten_bit_for_eight_bit": True}),
    (_set_provenance, {"provenance": False}),
    (_set_cache, {"cache_limit_bytes": 5 * 10**9}),
    (_set_force_cpu, {"force_cpu": True}),
]


@pytest.mark.parametrize(
    ("edit", "expected"), ROUND_TRIPS, ids=[e.__name__ for e, _ in ROUND_TRIPS]
)
def test_each_setting_round_trips(
    env: Env, edit: Callable[..., None], expected: dict[str, Any]
) -> None:
    window = env.start()
    parameters = window.session.parameters()
    window.session.set_settings(dataclasses.replace(Settings(), last_parameters=parameters))
    dialog = env.open(window)
    edit(env, dialog)
    dialog.accept()
    want = dataclasses.replace(Settings(), last_parameters=parameters, **expected)
    assert window.session.settings() == want
    assert env.saved() == want
    assert env.saved().last_parameters == parameters
    env.idle(window)


def test_second_window_opens_with_the_saved_values(env: Env, make_window: Any) -> None:
    window = env.start()
    dialog = env.open(window)
    _set_folder(env, dialog)
    _set_suffix(env, dialog)
    _set_png(env, dialog)
    _set_quality(env, dialog)
    _set_encoder(env, dialog)
    _set_ten_bit(env, dialog)
    _set_provenance(env, dialog)
    _set_cache(env, dialog)
    _set_force_cpu(env, dialog)
    dialog.accept()
    env.idle(window)
    window.close()
    again = env.start()
    second = env.open(again)
    assert second.folder_label.text() == str(Path("out"))
    assert second.suffix_edit.text() == "_clean"
    assert second.png_combo.currentData() == 8
    assert second.quality_combo.currentData() == "draft"
    assert second.encoder_combo.currentData() == "libx265"
    assert second.ten_bit_check.isChecked()
    assert not second.provenance_check.isChecked()
    assert second.cache_spin.value() == 5
    assert second.force_cpu_check.isChecked()


def test_cancel_changes_nothing(env: Env) -> None:
    window = env.start()
    dialog = env.open(window)
    dialog.suffix_edit.setText("_other")
    dialog.cache_spin.setValue(3)
    dialog.force_cpu_check.setChecked(True)
    dialog.reject()
    env.idle(window)
    assert window.session.settings() == Settings()
    assert not env.config.joinpath("settings.json").exists()
    assert env.cache.limits == []


def test_use_source_folder_and_cancelled_chooser(env: Env) -> None:
    window = env.start(saved=Settings(output_folder=Path("out")))
    dialog = env.open(window)
    assert dialog.folder_label.text() == str(Path("out"))
    env.choosers.folder = None  # the user cancelled the chooser
    dialog.choose_folder_button.click()
    assert env.choosers.asked_folder == [Path("out")]
    assert dialog.edited_settings().output_folder == Path("out")
    dialog.use_source_button.click()
    assert dialog.folder_label.text() == SAME_FOLDER_TEXT
    assert dialog.edited_settings().output_folder is None


def _chooser_scenario(
    env: Env, operation: str = "choose", *, analysing: bool = False
) -> tuple[MainWindow, SettingsDialog]:
    """A chooser failure becomes a settings error without changing dialog or cache state."""
    window = env.start(saved=Settings(output_folder=Path("original")))
    dialog = env.open(window)
    if analysing:
        window.session.set_analysis(AnalysisState(phase="running"))
    before = window.session.settings()
    before_file = (env.config / "settings.json").read_bytes()
    before_note = dialog.cache_note.text()
    if operation == "choose":
        env.choosers.raise_on_choose = OSError("injected chooser failed")
        button = dialog.choose_folder_button
        expected = "The output folder could not be chosen: injected chooser failed"
    else:
        assert operation == "confirm"
        env.choosers.raise_on_confirm = RuntimeError("injected chooser failed")
        button = dialog.clear_button
        expected = "The cache was not cleared: the confirmation failed: injected chooser failed"
    button.click()
    errors = presenter_of(window).of("error")
    assert len(errors) == 1, "chooser failure did not present exactly one settings error"
    assert errors[0].owner == OWNER_SETTINGS
    assert errors[0].text == expected
    assert errors[0].text.isascii()
    assert dialog.edited_settings().output_folder == Path("original")
    assert dialog.folder_label.text() == str(Path("original"))
    assert window.session.settings() == before
    assert (env.config / "settings.json").read_bytes() == before_file
    assert dialog.result() != QDialog.DialogCode.Accepted
    assert not dialog._clearing
    assert env.cache.cleared == []
    assert env.cache.limits == []
    assert dialog.clear_button.isEnabled() == (not analysing)
    assert dialog.clear_button.text() == "Clear cache"
    assert dialog.cache_note.text() == before_note
    return window, dialog


@pytest.mark.parametrize("analysing", [False, True], ids=["idle", "analysis-running"])
def test_a_raising_folder_chooser_is_a_settings_error(env: Env, analysing: bool) -> None:
    """Catch an OSError from a folder-button click and preserve the analysis button state."""
    _chooser_scenario(env, analysing=analysing)


def test_a_raising_confirmation_is_a_settings_error_and_clears_nothing(env: Env) -> None:
    """A raising confirmation must not launch a cache clear or escape its button slot."""
    _chooser_scenario(env, "confirm")


@pytest.mark.parametrize("operation", ["choose", "confirm"])
def test_a_dialog_still_works_after_a_chooser_failure(env: Env, operation: str) -> None:
    """The same dialog can retry a folder choice or cache confirmation successfully."""
    window, dialog = _chooser_scenario(env, operation)
    if operation == "choose":
        env.choosers.raise_on_choose = None
        env.choosers.folder = Path("chosen")
        dialog.choose_folder_button.click()
        assert dialog.edited_settings().output_folder == Path("chosen")
        assert dialog.folder_label.text() == str(Path("chosen"))
        assert env.choosers.asked_folder == [Path("original"), Path("original")]
        assert env.cache.cleared == []
    else:
        env.choosers.raise_on_confirm = None
        dialog.clear_button.click()
        env.qtbot.waitUntil(lambda: dialog.cache_note.text() == "Cache cleared.", timeout=5000)
        assert len(env.choosers.confirms) == 2
        assert len(env.cache.cleared) == 1
        assert dialog.clear_button.isEnabled()
        assert not dialog._clearing
    assert len(presenter_of(window).of("error")) == 1


@pytest.mark.parametrize("operation", ["choose", "confirm"])
def test_chooser_scenario_passes_on_the_real_dialog(env: Env, operation: str) -> None:
    """The shared chooser-failure scenario passes on both real slots."""
    _chooser_scenario(env, operation)


@pytest.mark.parametrize("operation", ["choose", "confirm"])
def test_planted_unwrapped_chooser_is_caught(
    env: Env, monkeypatch: pytest.MonkeyPatch, operation: str
) -> None:
    """Detect bare injected calls while capturing the deliberately escaped Qt exception."""

    def unwrapped(self: SettingsDialog) -> None:
        if operation == "choose":
            self._choosers.choose_folder(self._folder)
        else:
            self._choosers.confirm("Clear the cache?")

    method = "_on_choose_folder" if operation == "choose" else "_on_clear_clicked"
    monkeypatch.setattr(SettingsDialog, method, unwrapped)
    with (
        env.qtbot.captureExceptions() as exceptions,
        pytest.raises(
            AssertionError, match="chooser failure did not present exactly one settings error"
        ),
    ):
        _chooser_scenario(env, operation)
    assert len(exceptions) == 1
    assert isinstance(exceptions[0][1], OSError if operation == "choose" else RuntimeError)


# D74: encoders.


def test_unavailable_encoder_is_disabled_with_its_reason(env: Env) -> None:
    window = env.start()
    dialog = env.open(window)
    rows = {d: (t, enabled, tip) for d, t, enabled, tip in items(dialog.encoder_combo)}
    assert list(rows) == ["auto", "hevc_nvenc", "libx265"]
    text, enabled, tip = rows["hevc_nvenc"]
    assert not enabled
    assert text == f"hevc_nvenc (unavailable: {NVENC.reason})"
    assert tip == NVENC.reason
    assert rows["libx265"] == ("libx265", True, "")
    assert rows["auto"][1]


def test_an_unavailable_encoder_cannot_be_accepted(env: Env) -> None:
    window = env.start()
    dialog = env.open(window)
    dialog.encoder_combo.setCurrentIndex(dialog.encoder_combo.findData("hevc_nvenc"))
    assert not dialog.ok_button.isEnabled()
    dialog.accept()
    assert window.session.settings() == Settings()
    assert not env.config.joinpath("settings.json").exists()


def test_encoder_list_waits_for_the_sink_and_is_read_once(env: Env) -> None:
    window = env.start()
    window.shell_actions.settings.trigger()
    dialog = window._settings_dialog
    assert isinstance(dialog, SettingsDialog)
    assert not dialog.encoder_combo.isEnabled()
    assert dialog.encoder_note.text() == "Detecting encoders..."
    env.qtbot.waitUntil(lambda: dialog.encoder_combo.isEnabled(), timeout=5000)
    assert dialog.encoder_note.text() == ""
    assert env.sink.threads and env.sink.threads[0] is not threading.main_thread()
    dialog.reject()
    env.qtbot.wait(20)
    second = env.open(window)
    assert second.encoder_combo.isEnabled()
    assert len(env.sink.threads) == 1


def test_a_failed_detection_leaves_only_automatic(env: Env) -> None:
    window = env.start(fail="ffmpeg is missing")
    dialog = env.open(window)
    assert [d for d, *_ in items(dialog.encoder_combo)] == ["auto"]
    assert "ffmpeg is missing" in dialog.encoder_note.text()
    assert not dialog.ten_bit_check.isEnabled()
    assert dialog.ten_bit_note.text() == NO_ENCODER_REASON


def test_a_failed_detection_gives_a_stored_encoder_the_failure_as_its_reason(env: Env) -> None:
    window = env.start(fail="ffmpeg is missing", saved=Settings(video_encoder="libx265"))
    dialog = env.open(window)
    rows = {d: (t, enabled, tip) for d, t, enabled, tip in items(dialog.encoder_combo)}
    assert list(rows) == ["auto", "libx265"]
    text, enabled, tip = rows["libx265"]
    assert not enabled
    assert "ffmpeg is missing" in tip
    assert NOT_FOUND_REASON not in text
    assert text == f"libx265 (unavailable: {tip})"
    assert dialog.encoder_combo.currentData() == "libx265"
    dialog.accept()
    assert env.saved().video_encoder == "libx265"


def test_a_stored_encoder_this_computer_does_not_report_is_kept(env: Env) -> None:
    window = env.start(saved=Settings(video_encoder="old_encoder"))
    dialog = env.open(window)
    rows = {d: (t, enabled, tip) for d, t, enabled, tip in items(dialog.encoder_combo)}
    text, enabled, tip = rows["old_encoder"]
    assert (text, enabled, tip) == (
        f"old_encoder (unavailable: {NOT_FOUND_REASON})",
        False,
        NOT_FOUND_REASON,
    )
    assert dialog.encoder_combo.currentData() == "old_encoder"
    assert dialog.ok_button.isEnabled()
    dialog.accept()
    assert env.saved().video_encoder == "old_encoder"
    assert window.session.settings().video_encoder == "old_encoder"


def _unavailable_stored_scenario(env: Env) -> tuple[MainWindow, SettingsDialog]:
    """Refuse a reported-unavailable stored encoder without writing or applying."""
    stored = Settings(video_encoder="hevc_nvenc")
    window = env.start(saved=stored)
    dialog = env.open(window)
    path = env.config / "settings.json"
    path.unlink()  # The setting was loaded; any refusal-time write is now observable.
    assert not dialog.ok_button.isEnabled(), "reported-unavailable stored encoder left OK enabled"
    expected = "hevc_nvenc is unavailable: No NVIDIA encoder was found. Choose another encoder."
    assert dialog.encoder_note.text() == expected
    dialog.accept()
    assert not path.exists()
    assert dialog.result() != QDialog.DialogCode.Accepted
    assert window.session.settings() == stored
    (error,) = presenter_of(window).of("error")
    assert error.owner == OWNER_SETTINGS
    assert error.text == expected
    return window, dialog


def test_a_stored_encoder_the_sink_reports_unavailable_is_refused(env: Env) -> None:
    """A stored encoder must still satisfy the sink's current availability report."""
    _unavailable_stored_scenario(env)


def test_picking_another_encoder_after_the_refusal_accepts(env: Env) -> None:
    """Selecting an available encoder clears the refusal note and permits a save."""
    window, dialog = _unavailable_stored_scenario(env)
    pick(dialog.encoder_combo, "libx265")
    assert dialog.ok_button.isEnabled()
    assert dialog.encoder_note.text() == ""
    assert dialog.encoder_combo.toolTip() == ""
    dialog.accept()
    assert dialog.result() == QDialog.DialogCode.Accepted
    assert env.saved().video_encoder == "libx265"
    assert window.session.settings().video_encoder == "libx265"
    assert not presenter_of(window).of("error")
    env.idle(window)


def test_a_stored_encoder_arriving_unavailable_after_detection_refuses_ok(env: Env) -> None:
    """Defer encoder refusal until the pending capability report arrives."""
    window = env.start(saved=Settings(video_encoder="hevc_nvenc"))
    window.shell_actions.settings.trigger()
    dialog = window._settings_dialog
    assert isinstance(dialog, SettingsDialog)
    assert not dialog.encoder_combo.isEnabled()
    assert dialog.ok_button.isEnabled()
    assert dialog.encoder_note.text() == "Detecting encoders..."
    env.qtbot.waitUntil(lambda: dialog.encoder_combo.isEnabled(), timeout=5000)
    assert not dialog.ok_button.isEnabled()
    assert dialog.encoder_note.text() == (
        "hevc_nvenc is unavailable: No NVIDIA encoder was found. Choose another encoder."
    )


def test_a_reported_unavailable_encoder_from_the_current_session_is_refused(env: Env) -> None:
    """Validate the encoder actually applied when the unedited combo and session diverge."""
    window = env.start()
    dialog = env.open(window)
    stored = dataclasses.replace(Settings(), video_encoder="hevc_nvenc")
    window.session.set_settings(stored)
    assert dialog.encoder_combo.currentData() == "auto"
    dialog.accept()
    assert not (env.config / "settings.json").exists()
    assert window.session.settings() == stored
    assert dialog.result() != QDialog.DialogCode.Accepted
    assert not dialog.ok_button.isEnabled()
    expected = "hevc_nvenc is unavailable: No NVIDIA encoder was found. Choose another encoder."
    assert dialog.encoder_note.text() == expected
    (error,) = presenter_of(window).of("error")
    assert error.owner == OWNER_SETTINGS and error.text == expected
    pick(dialog.encoder_combo, "libx265")
    assert dialog.encoder_note.text() == ""
    dialog.accept()
    assert env.saved().video_encoder == "libx265"
    assert window.session.settings().video_encoder == "libx265"
    assert dialog.result() == QDialog.DialogCode.Accepted


@pytest.mark.parametrize("fail", [None, "ffmpeg is missing"], ids=["absent", "report-failed"])
def test_a_current_session_encoder_the_sink_does_not_report_is_kept(
    env: Env, fail: str | None
) -> None:
    """Preserve Q3 for the current session's unreported encoder on the same divergence route."""
    window = env.start(fail=fail)
    dialog = env.open(window)
    stored = dataclasses.replace(Settings(), video_encoder="old_encoder")
    window.session.set_settings(stored)
    dialog.accept()
    assert env.saved() == stored
    assert window.session.settings() == stored
    assert dialog.result() == QDialog.DialogCode.Accepted
    assert not presenter_of(window).of("error")


def test_return_saves_edits_after_an_unavailable_encoder_is_replaced(env: Env) -> None:
    """Re-enabling OK makes a direct Return event save after the refusal is corrected."""
    window = env.start(saved=Settings(video_encoder="hevc_nvenc"))
    first = env.open(window)
    first.reject()
    env.qtbot.wait(20)
    # The cached report makes OK disabled before this dialog is shown.
    dialog = env.open(window)
    env.qtbot.wait(20)
    pick(dialog.encoder_combo, "libx265")
    dialog.suffix_edit.setText("_keyboard")
    env.qtbot.keyClick(dialog.suffix_edit, Qt.Key.Key_Return)
    assert dialog.result() == QDialog.DialogCode.Accepted
    assert window.session.settings().output_suffix == "_keyboard"
    assert env.saved().output_suffix == "_keyboard"
    assert env.saved().video_encoder == "libx265"


def test_an_encoder_refusal_reason_has_one_sentence_ending(env: Env) -> None:
    """Reuse a reason's terminal full stop in the note and the settings error."""
    window = env.start(saved=Settings(video_encoder="hevc_nvenc"))
    dialog = env.open(window)
    expected = "hevc_nvenc is unavailable: No NVIDIA encoder was found. Choose another encoder."
    assert dialog.encoder_note.text() == expected
    dialog.accept()
    (error,) = presenter_of(window).of("error")
    assert error.owner == OWNER_SETTINGS and error.text == expected


def test_unavailable_stored_scenario_passes_on_the_real_dialog(env: Env) -> None:
    """The shared unavailable-stored scenario passes on the real dialog."""
    _unavailable_stored_scenario(env)


def test_planted_stored_unavailable_accepted_is_caught(
    env: Env, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Detect a planted bypass that treats every unchanged stored encoder as valid."""
    real = SettingsDialog._encoder_unacceptable

    def stored_bypass(self: SettingsDialog, name: str | None = None) -> bool:
        if self.encoder_combo.currentData() == self._initial.video_encoder:
            return False
        return real(self, name)

    monkeypatch.setattr(SettingsDialog, "_encoder_unacceptable", stored_bypass)
    with pytest.raises(AssertionError, match="reported-unavailable stored encoder left OK enabled"):
        _unavailable_stored_scenario(env)


def test_ten_bit_follows_the_encoder_and_keeps_a_stored_true(env: Env) -> None:
    only8 = EncoderCapability("libx265", True, None, (8,), False)
    window = env.start(caps=(NVENC, only8), saved=Settings(ten_bit_for_eight_bit=True))
    dialog = env.open(window)
    assert dialog.ten_bit_check.isChecked()
    assert not dialog.ten_bit_check.isEnabled()
    assert dialog.ten_bit_check.toolTip() == "libx265 cannot write 10-bit video."
    assert dialog.ten_bit_note.text() == "libx265 cannot write 10-bit video."
    dialog.accept()
    assert env.saved().ten_bit_for_eight_bit is True


def test_ten_bit_is_enabled_for_an_encoder_with_10(env: Env) -> None:
    window = env.start()
    dialog = env.open(window)
    assert dialog.ten_bit_check.isEnabled()
    assert dialog.ten_bit_note.text() == ""
    dialog.ten_bit_check.setChecked(True)
    pick(dialog.encoder_combo, "libx265")
    assert dialog.ten_bit_check.isEnabled()
    assert dialog.ten_bit_check.isChecked()


def test_auto_is_resolved_by_the_injected_rule(env: Env) -> None:
    nvenc8 = EncoderCapability("hevc_nvenc", True, None, (8,), True)
    window = env.start(caps=(nvenc8, X265), resolve=lambda setting, caps: "hevc_nvenc")
    dialog = env.open(window)
    assert env.resolve_calls
    assert all(call == ("auto", (nvenc8, X265)) for call in env.resolve_calls)
    assert not dialog.ten_bit_check.isEnabled()
    assert dialog.ten_bit_note.text() == "hevc_nvenc cannot write 10-bit video."
    pick(dialog.encoder_combo, "libx265")
    assert dialog.ten_bit_check.isEnabled()


@pytest.mark.parametrize(
    ("capabilities", "default", "resolved", "enabled", "note"),
    [
        (
            (EncoderCapability("hevc_nvenc", True, None, (8,), True), X265),
            "hevc_nvenc",
            "libx265",
            True,
            "",
        ),
        (
            (X265, EncoderCapability("eight_bit_encoder", True, None, (8,), False)),
            "libx265",
            "eight_bit_encoder",
            False,
            "eight_bit_encoder cannot write 10-bit video.",
        ),
    ],
    ids=["injected-enables-ten-bit", "injected-disables-ten-bit"],
)
def test_auto_is_resolved_by_a_rule_that_disagrees_with_the_default_rule(
    env: Env,
    capabilities: tuple[EncoderCapability, ...],
    default: str,
    resolved: str,
    enabled: bool,
    note: str,
) -> None:
    """The injected resolver, rather than a restated rule, controls 10-bit support."""
    assert capability.resolve_encoder("auto", capabilities) == default != resolved
    window = env.start(caps=capabilities, resolve=lambda setting, caps: resolved)
    dialog = env.open(window)
    assert env.resolve_calls
    assert all(call == ("auto", capabilities) for call in env.resolve_calls)
    assert dialog.ten_bit_check.isEnabled() == enabled
    assert dialog.ten_bit_note.text() == note
    assert dialog.ten_bit_check.toolTip() == note


# DR-35: the suffix.


@pytest.mark.parametrize(
    "suffix", ["a/b", "a\\b", "..", "x..y", "name.", "name ", f"x{TEMP_MARKER}", 'a"b', "a\x01"]
)
def test_an_invalid_suffix_disables_ok_with_the_error_text(env: Env, suffix: str) -> None:
    window = env.start()
    dialog = env.open(window)
    dialog.suffix_edit.setText(suffix)
    with pytest.raises(ValueError) as caught:
        validate_suffix(suffix)
    assert not dialog.ok_button.isEnabled()
    assert (
        dialog.suffix_error.text() == str(caught.value).encode("ascii", "backslashreplace").decode()
    )
    dialog.accept()  # refused: nothing applied
    assert window.session.settings() == Settings()
    dialog.suffix_edit.setText("_ok")
    assert dialog.ok_button.isEnabled()
    assert dialog.suffix_error.text() == ""


def test_an_empty_suffix_is_valid(env: Env) -> None:
    window = env.start()
    dialog = env.open(window)
    dialog.suffix_edit.setText("")
    assert dialog.ok_button.isEnabled()
    dialog.accept()
    assert env.saved().output_suffix == ""


def test_a_stored_invalid_suffix_disables_ok_until_fixed(env: Env) -> None:
    window = env.start(saved=Settings(output_suffix="bad/suffix"))
    dialog = env.open(window)
    assert not dialog.ok_button.isEnabled()
    assert "bad/suffix" in dialog.suffix_error.text()


def _assert_suffix_refusal_then_correction(
    env: Env, window: MainWindow, dialog: SettingsDialog, stored: Settings
) -> None:
    """Refuse the applied suffix without saving, then accept a corrected edit."""
    path = env.config / "settings.json"
    assert not path.exists()
    with pytest.raises(ValueError) as caught:
        validate_suffix(stored.output_suffix)
    detail = str(caught.value).encode("ascii", "backslashreplace").decode()[:200]
    dialog.accept()
    assert not path.exists(), "invalid applied suffix was written"
    assert dialog.result() != QDialog.DialogCode.Accepted
    assert window.session.settings() == stored
    (error,) = presenter_of(window).of("error")
    assert error.owner == OWNER_SETTINGS
    assert error.text == f"The output suffix is not valid: {detail}"
    assert error.text.isascii()

    dialog.suffix_edit.setText("_fixed")
    assert dialog.ok_button.isEnabled()
    assert dialog.suffix_error.text() == ""
    dialog.accept()
    expected = dataclasses.replace(stored, output_suffix="_fixed")
    assert dialog.result() == QDialog.DialogCode.Accepted
    assert env.saved() == expected
    assert window.session.settings() == expected
    assert not presenter_of(window).of("error")
    env.idle(window)


def test_a_stored_suffix_that_fails_validation_in_its_last_character_is_refused(
    env: Env,
) -> None:
    """Validate the last character even beyond the control's usual edit limit."""
    stored = Settings(output_suffix="a" * 32767 + "/")
    window = env.start(saved=stored)
    dialog = env.open(window)
    # It was loaded from disk; removing the fixture file makes any write observable.
    (env.config / "settings.json").unlink()
    _assert_suffix_refusal_then_correction(env, window, dialog, stored)


def test_a_stored_suffix_with_a_newline_is_refused(env: Env) -> None:
    """Refuse a newline in a loaded suffix and allow a valid correction."""
    stored = Settings(output_suffix="bad\nsuffix")
    window = env.start(saved=stored)
    dialog = env.open(window)
    (env.config / "settings.json").unlink()
    _assert_suffix_refusal_then_correction(env, window, dialog, stored)


def test_a_stored_suffix_refusal_shows_the_applied_value_error_in_the_dialog(env: Env) -> None:
    """Show the rejected stored value beside the field and disable OK until correction."""
    window = env.start()
    dialog = env.open(window)
    stored = dataclasses.replace(Settings(), output_suffix="bad/suffix")
    window.session.set_settings(stored)
    dialog.accept()
    assert "bad/suffix" in dialog.suffix_error.text()
    assert dialog.suffix_edit.toolTip() == dialog.suffix_error.text()
    assert not dialog.ok_button.isEnabled()
    assert not (env.config / "settings.json").exists()
    assert window.session.settings() == stored
    assert dialog.result() != QDialog.DialogCode.Accepted
    (error,) = presenter_of(window).of("error")
    assert error.owner == OWNER_SETTINGS
    dialog.suffix_edit.setText("_fixed")
    assert dialog.suffix_error.text() == ""
    assert dialog.ok_button.isEnabled()
    dialog.accept()
    assert env.saved().output_suffix == "_fixed"
    assert dialog.result() == QDialog.DialogCode.Accepted


def _stored_suffix_scenario(env: Env, suffix: str = "bad/suffix") -> None:
    """The session's current suffix must be validated when the field is unedited."""
    window = env.start()
    dialog = env.open(window)
    stored = dataclasses.replace(Settings(), output_suffix=suffix)
    window.session.set_settings(stored)
    assert dialog.suffix_edit.text() == "_corrected"
    assert dialog.edited_settings().output_suffix == suffix
    _assert_suffix_refusal_then_correction(env, window, dialog, stored)


@pytest.mark.parametrize(
    "suffix", ["bad/suffix", "\u00e9" * 100 + "/"], ids=["separator", "non-ascii-error"]
)
def test_stored_suffix_scenario_passes_on_the_real_dialog(env: Env, suffix: str) -> None:
    """Catch field-only validation, including escaping and limiting the error detail."""
    _stored_suffix_scenario(env, suffix)


def test_planted_field_only_suffix_check_is_caught(
    env: Env, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The shared scenario detects a save after validating only the displayed field."""

    def field_only(self: SettingsDialog) -> None:
        try:
            validate_suffix(self.suffix_edit.text())
        except ValueError:
            self._check_suffix()
            return
        if self._encoder_unacceptable():
            return
        new = self.edited_settings()
        if self._context.session.settings_refusal() is None:
            self._save(new)
        self._context.session.set_settings(new)
        QDialog.accept(self)

    monkeypatch.setattr(SettingsDialog, "accept", field_only)
    with pytest.raises(AssertionError, match="invalid applied suffix was written"):
        _stored_suffix_scenario(env)


# AD-9: force CPU.


def test_force_cpu_shows_cpu_forced_in_the_status_bar(env: Env, qtbot: Any) -> None:
    path = Path("p.png")
    window = env.start(photo=path)
    open_and_wait(qtbot, window, path)
    assert window.session.backend() == "CPU: stub"
    dialog = env.open(window)
    dialog.force_cpu_check.setChecked(True)
    dialog.accept()
    wait_idle(qtbot, window)
    assert window.session.backend() == "CPU: forced"
    assert window.device_label.text() == "Device: CPU: forced"
    env.idle(window)


# S4: the refused settings file.


UNSUPPORTED = '{"format_version": 999, "kept": true}\n'


def _refusal_scenario(env: Env) -> None:
    """OK applies to the session, writes nothing, says why."""
    window = env.start(raw=UNSUPPORTED)
    path = env.config / "settings.json"
    before = path.read_bytes()
    assert window.session.settings_refusal() is not None
    dialog = env.open(window)
    assert "this session only" in dialog.refusal_label.text()
    assert "settings.json" in dialog.refusal_label.text()
    assert window.session.settings_refusal().text in dialog.refusal_label.text()
    dialog.suffix_edit.setText("_fresh")
    dialog.accept()
    assert window.session.settings().output_suffix == "_fresh"
    assert path.read_bytes() == before
    env.idle(window)
    window.close()
    assert path.read_bytes() == before  # the close save is refused as well


def test_ok_while_the_file_is_refused_is_session_only(env: Env) -> None:
    _refusal_scenario(env)


# D71: the cache.


def test_clear_cache_runs_off_the_interface_thread_after_a_confirmation(env: Env) -> None:
    window = env.start()
    dialog = env.open(window)
    dialog.clear_button.click()
    assert len(env.choosers.confirms) == 1
    assert dialog.clear_button.text() == "Clearing..."
    assert not dialog.clear_button.isEnabled()
    env.qtbot.waitUntil(lambda: dialog.cache_note.text() == "Cache cleared.", timeout=5000)
    assert len(env.cache.cleared) == 1
    assert env.cache.cleared[0] is not threading.main_thread()
    assert dialog.clear_button.text() == "Clear cache"
    assert dialog.clear_button.isEnabled()
    assert not presenter_of(window).of("error")


def test_declined_confirmation_clears_nothing(env: Env) -> None:
    window = env.start()
    dialog = env.open(window)
    env.choosers.answer = False
    dialog.clear_button.click()
    env.idle(window)
    assert len(env.choosers.confirms) == 1
    assert env.cache.cleared == []
    assert dialog.clear_button.isEnabled()


def test_clear_cache_is_disabled_while_a_clip_is_analysed(env: Env) -> None:
    window = env.start()
    dialog = env.open(window)
    window.session.set_analysis(AnalysisState(phase="running", done=1, total=10))
    assert not dialog.clear_button.isEnabled()
    assert dialog.clear_button.toolTip() == CLEAR_BLOCKED_REASON
    assert dialog.cache_note.text() == CLEAR_BLOCKED_REASON
    dialog.clear_button.click()
    assert env.choosers.confirms == []
    window.session.set_analysis(AnalysisState(phase="complete"))
    assert dialog.clear_button.isEnabled()
    assert dialog.clear_button.toolTip() == ""
    assert dialog.cache_note.text() == ""


def test_an_analysis_that_starts_while_the_confirmation_is_open_blocks_the_clear(
    env: Env,
) -> None:
    window = env.start()
    dialog = env.open(window)
    env.choosers.while_open = lambda: window.session.set_analysis(AnalysisState(phase="running"))
    dialog.clear_button.click()
    env.idle(window)
    assert len(env.choosers.confirms) == 1
    assert env.cache.cleared == []
    assert not dialog.clear_button.isEnabled()
    assert dialog.clear_button.toolTip() == CLEAR_BLOCKED_REASON
    assert dialog.cache_note.text() == CLEAR_BLOCKED_REASON
    assert not presenter_of(window).of("error")


def test_clear_cache_disabled_from_the_start_when_analysis_is_running(env: Env) -> None:
    window = env.start()
    window.session.set_analysis(AnalysisState(phase="running"))
    dialog = env.open(window)
    assert not dialog.clear_button.isEnabled()


def test_clear_cache_failure_is_a_settings_error(env: Env) -> None:
    window = env.start(cache_fails=True)
    dialog = env.open(window)
    dialog.clear_button.click()
    env.qtbot.waitUntil(lambda: bool(presenter_of(window).of("error")), timeout=5000)
    (error,) = presenter_of(window).of("error")
    assert error.owner == OWNER_SETTINGS
    assert "disk is busy" in error.text
    assert dialog.clear_button.isEnabled()
    assert dialog.cache_note.text() == ""


def test_clear_cache_result_after_the_dialog_closed_is_safe(env: Env) -> None:
    window = env.start(cache_fails=True)
    dialog = env.open(window)
    dialog.clear_button.click()
    dialog.reject()
    env.qtbot.waitUntil(lambda: bool(presenter_of(window).of("error")), timeout=5000)
    env.idle(window)


def test_a_limit_change_sets_the_limit_in_bytes_off_the_interface_thread(env: Env) -> None:
    window = env.start()
    dialog = env.open(window)
    dialog.cache_spin.setValue(7)
    dialog.accept()
    env.idle(window)
    assert [n for n, _ in env.cache.limits] == [7 * 10**9]
    assert env.cache.limits[0][1] is not threading.main_thread()
    assert env.cache.limit_bytes() == 7 * 10**9


def test_an_unchanged_limit_calls_nothing_and_a_stored_odd_limit_is_kept(env: Env) -> None:
    window = env.start(saved=Settings(cache_limit_bytes=1_500_000_000))
    dialog = env.open(window)
    assert dialog.cache_spin.value() == 2
    dialog.suffix_edit.setText("_x")
    dialog.accept()
    env.idle(window)
    assert env.cache.limits == []
    assert env.saved().cache_limit_bytes == 1_500_000_000
    assert window.session.settings().cache_limit_bytes == 1_500_000_000


def test_a_huge_stored_limit_opens_clamped_and_is_written_back_unchanged(env: Env) -> None:
    huge = 10**400
    window = env.start(saved=Settings(cache_limit_bytes=huge))
    assert window.session.settings().cache_limit_bytes == huge
    dialog = env.open(window)
    assert dialog.cache_spin.value() == dialog.cache_spin.maximum() == 100_000
    dialog.suffix_edit.setText("_x")
    dialog.accept()
    env.idle(window)
    assert env.cache.limits == []
    assert env.saved().cache_limit_bytes == huge
    assert window.session.settings().cache_limit_bytes == huge


def test_the_last_accepted_limit_wins_whatever_order_the_jobs_run_in(env: Env) -> None:
    window = env.start()
    release = threading.Event()
    env.cache.release_first_limit = release  # the first set_limit_bytes call is held back
    try:
        first = env.open(window)
        first.cache_spin.setValue(5)
        first.accept()
        assert env.cache.first_limit_entered.wait(5)
        second = env.open(window)
        assert second.cache_spin.value() == 5
        second.cache_spin.setValue(7)
        second.accept()
        env.qtbot.wait(100)  # the second job is queued behind the first
        release.set()
        env.idle(window)
    finally:
        release.set()
    assert window.session.settings().cache_limit_bytes == 7 * 10**9
    assert env.cache.limit_bytes() == 7 * 10**9
    assert env.cache.limits[-1][0] == 7 * 10**9
    assert not presenter_of(window).of("error")


def test_a_limit_failure_is_a_settings_error(env: Env) -> None:
    window = env.start(cache_fails=True)
    dialog = env.open(window)
    dialog.cache_spin.setValue(4)
    dialog.accept()
    env.qtbot.waitUntil(lambda: bool(presenter_of(window).of("error")), timeout=5000)
    (error,) = presenter_of(window).of("error")
    assert error.owner == OWNER_SETTINGS
    assert "disk is busy" in error.text
    assert env.saved().cache_limit_bytes == 4 * 10**9


def test_cache_spin_has_a_minimum_of_one_gb(env: Env) -> None:
    window = env.start(saved=Settings(cache_limit_bytes=0))
    dialog = env.open(window)
    assert dialog.cache_spin.minimum() == 1
    assert dialog.cache_spin.value() == 1
    dialog.accept()
    assert env.saved().cache_limit_bytes == 0  # not edited: written back unchanged


# DR-44 (b): message owners.


def test_a_save_clears_only_the_settings_errors(env: Env) -> None:
    window = env.start()
    presenter = presenter_of(window)
    presenter.present(Message("error", "preview", owner="shell.preview"))
    presenter.present(Message("error", "earlier", owner=OWNER_SETTINGS))
    dialog = env.open(window)
    dialog.suffix_edit.setText("_x")
    dialog.accept()
    assert [m.owner for m in presenter.of("error")] == ["shell.preview"]


def test_a_failed_save_names_the_file_and_the_session_still_gets_the_settings(env: Env) -> None:
    window = env.start()
    path = env.config / "settings.json"
    path.mkdir(parents=True)  # a directory in the way: the atomic replace fails
    dialog = env.open(window)
    dialog.suffix_edit.setText("_x")
    dialog.accept()
    (error,) = presenter_of(window).of("error")
    assert error.owner == OWNER_SETTINGS
    assert "settings.json" in error.text
    assert error.path == path
    assert window.session.settings().output_suffix == "_x"
    path.rmdir()


def test_every_message_of_the_dialog_is_ascii(env: Env) -> None:
    window = env.start(cache_fails=True)
    dialog = env.open(window)
    dialog.clear_button.click()
    env.qtbot.waitUntil(lambda: bool(presenter_of(window).of("error")), timeout=5000)
    env.choosers.raise_on_choose = OSError("folder \u2603")
    dialog.choose_folder_button.click()
    env.choosers.raise_on_confirm = RuntimeError("confirm \u00e9")
    dialog.clear_button.click()
    errors = presenter_of(window).of("error")
    assert "The output folder could not be chosen: folder \\u2603" in [m.text for m in errors]
    assert "The cache was not cleared: the confirmation failed: confirm \\xe9" in [
        m.text for m in errors
    ]
    assert all(m.owner == OWNER_SETTINGS for m in errors)
    assert all(m.text.isascii() for m in presenter_of(window).messages)


# Planted wrong implementations: each scenario must fail on a wrong dialog.


def _save_while_refused(self: SettingsDialog) -> None:
    new = self.edited_settings()
    module.save_settings(self._context.locations.config_dir, new)
    self._context.session.set_settings(new)
    QDialog.accept(self)


def test_planted_save_while_refused_is_caught(env: Env, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(SettingsDialog, "accept", _save_while_refused)
    with pytest.raises(AssertionError):
        _refusal_scenario(env)


def _last_parameters_scenario(env: Env) -> None:
    window = env.start()
    parameters = window.session.parameters()
    window.session.set_settings(dataclasses.replace(Settings(), last_parameters=parameters))
    dialog = env.open(window)
    dialog.suffix_edit.setText("_x")
    dialog.accept()
    assert env.saved().last_parameters == parameters
    assert window.session.settings().last_parameters == parameters


def test_last_parameters_scenario_passes_on_the_real_dialog(env: Env) -> None:
    _last_parameters_scenario(env)


def test_planted_dropped_last_parameters_is_caught(
    env: Env, monkeypatch: pytest.MonkeyPatch
) -> None:
    real = SettingsDialog.edited_settings

    def dropping(self: SettingsDialog) -> Settings:
        return dataclasses.replace(real(self), last_parameters=None)

    monkeypatch.setattr(SettingsDialog, "edited_settings", dropping)
    with pytest.raises(AssertionError):
        _last_parameters_scenario(env)


def _clear_thread_scenario(env: Env) -> None:
    window = env.start()
    dialog = env.open(window)
    dialog.clear_button.click()
    env.qtbot.waitUntil(lambda: bool(env.cache.cleared), timeout=5000)
    assert env.cache.cleared[0] is not threading.main_thread()


def test_planted_clear_on_the_interface_thread_is_caught(
    env: Env, monkeypatch: pytest.MonkeyPatch
) -> None:
    def inline(self: SettingsDialog) -> None:
        if self._choosers.confirm("sure?"):
            self._context.engines.cache.clear()

    monkeypatch.setattr(SettingsDialog, "_on_clear_clicked", inline)
    with pytest.raises(AssertionError):
        _clear_thread_scenario(env)


def test_clear_thread_scenario_passes_on_the_real_dialog(env: Env) -> None:
    _clear_thread_scenario(env)


def _disabled_scenario(env: Env) -> None:
    window = env.start()
    dialog = env.open(window)
    rows = {d: enabled for d, _, enabled, _ in items(dialog.encoder_combo)}
    assert not rows["hevc_nvenc"]


def test_disabled_scenario_passes_on_the_real_dialog(env: Env) -> None:
    _disabled_scenario(env)


def test_planted_selectable_unavailable_encoder_is_caught(
    env: Env, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(SettingsDialog, "_disable_item", lambda self, index, reason: None)
    with pytest.raises(AssertionError):
        _disabled_scenario(env)


# WP4.3: DR-52 (WP3.10's rule, the catalog argument) and DR-61 (i)-(iii).


def test_the_default_rule_is_wp310s_and_the_stand_in_is_gone() -> None:
    assert not hasattr(module, "interim_resolve_encoder")
    assert module.wp310_resolve_encoder is capability.resolve_encoder


def test_wp310s_unavailable_error_is_shown_as_the_d74_reason(env: Env) -> None:
    """With neither encoder available, "auto" raises VideoEncodeError("unavailable") (WP3.10)."""
    none = (NVENC, EncoderCapability("libx265", False, "libx265 is missing.", (), False))
    with pytest.raises(VideoEncodeError) as caught:
        capability.resolve_encoder("auto", none)
    assert caught.value.kind == "unavailable"
    window = env.start(caps=none)
    dialog = env.open(window)
    assert not dialog.ten_bit_check.isEnabled()
    assert dialog.ten_bit_note.text() == NO_ENCODER_REASON
    assert dialog.ten_bit_check.toolTip() == NO_ENCODER_REASON
    rows = {d: (enabled, tip) for d, _, enabled, tip in items(dialog.encoder_combo)}
    assert rows["hevc_nvenc"] == (False, "No NVIDIA encoder was found.")
    assert rows["libx265"] == (False, "libx265 is missing.")
    assert dialog.ok_button.isEnabled()  # "auto" itself is allowed (Q3); export refuses it


def test_the_start_up_catalog_is_the_dialogs(env: Env, qtbot: Any) -> None:
    """DR-52: start-up detection runs once through the catalog the dialog then shows."""
    window = env.start()
    catalog = module.EncoderCatalog(window)
    install_settings_dialog(window, choosers=env.choosers, catalog=catalog)
    catalog.start(window.context)
    qtbot.waitUntil(lambda: not catalog.detecting(), timeout=5000)
    assert catalog.capabilities() == CAPS
    dialog = env.open(window)
    assert dialog.encoder_combo.isEnabled() and dialog.encoder_note.text() == ""
    assert len(env.sink.threads) == 1  # the dialog did not detect again


class _UnprintableError(OSError):
    def __str__(self) -> str:
        raise RuntimeError("no text")


@pytest.mark.parametrize(
    ("error", "detail"),
    [(_UnprintableError("x"), "_UnprintableError"), (OSError(), "OSError")],
    ids=["str-raises", "empty-text"],
)
def test_a_chooser_error_without_usable_text_is_named_by_its_type(
    env: Env, error: Exception, detail: str
) -> None:
    """DR-61 (i), (iii): the detail is formatted with a fallback; nothing escapes the slot."""
    window = env.start()
    dialog = env.open(window)
    env.choosers.raise_on_choose = error
    dialog._on_choose_folder()
    (shown,) = presenter_of(window).of("error")
    assert shown.text == f"The output folder could not be chosen: {detail}"
    assert shown.owner == OWNER_SETTINGS


def test_correcting_the_session_after_a_refused_applied_suffix_enables_ok(env: Env) -> None:
    """DR-61 (ii): OK is re-evaluated when the session's settings change."""
    window = env.start()
    dialog = env.open(window)
    window.session.set_settings(dataclasses.replace(Settings(), output_suffix="bad/suffix"))
    dialog.accept()
    assert not dialog.ok_button.isEnabled()
    window.session.set_settings(dataclasses.replace(Settings(), output_suffix="_ok"))
    assert dialog.suffix_error.text() == ""
    assert dialog.ok_button.isEnabled()
    dialog.accept()
    assert dialog.result() == QDialog.DialogCode.Accepted
    assert env.saved().output_suffix == "_ok"


def test_repeated_refused_accepts_show_one_banner(env: Env) -> None:
    """DR-61 (iii): the same refusal presented again does not stack a second banner."""
    window = env.start()
    dialog = env.open(window)
    window.session.set_settings(dataclasses.replace(Settings(), output_suffix="bad/suffix"))
    dialog.accept()
    dialog.accept()
    dialog.accept()
    errors = presenter_of(window).of("error")
    assert len(errors) == 1 and errors[0].text.startswith("The output suffix is not valid:")


# R2-3 (ruling 38a7c702): the cache jobs' errors and the main window's close.


@pytest.mark.parametrize("closing", [True, False], ids=["window-closing", "window-open"])
def test_cache_job_errors_are_not_presented_once_the_main_window_closes(
    make_app: Any, qtbot: Any, monkeypatch: pytest.MonkeyPatch, caplog: Any, closing: bool
) -> None:
    """A clear and a limit queued behind a slow, FAILING cache open (the R1-5 form).

    With the main window closed inside the wait, neither error is presented and both are logged;
    with the window open, both are presented as before. The closed signal is the application's
    one (``Application.closed``), the one its start-up callbacks read.
    """
    from clearwater.app import composition
    from clearwater.gui import shell

    opening, release = threading.Event(), threading.Event()

    def slow_failing_open(folder: Path, limit: int = 0) -> Any:
        opening.set()
        assert release.wait(30)
        raise OSError("the cache volume is not mounted")

    monkeypatch.setattr(composition, "proxy_cache", slow_failing_open)
    monkeypatch.setattr(shell, "SHUTDOWN_TIMEOUT_S", 0.2)
    choosers = FakeChoosers()
    application = make_app(cpu_settings(), choosers=choosers)
    window = application.window
    assert opening.wait(30)
    window.shell_actions.settings.trigger()
    dialog = window._settings_dialog
    assert isinstance(dialog, SettingsDialog)
    qtbot.waitUntil(lambda: dialog.encoder_combo.isEnabled(), timeout=60000)
    dialog.clear_button.click()  # the clear job waits for the open
    assert choosers.confirms
    dialog.cache_spin.setValue(dialog.cache_spin.value() + 1)
    dialog.ok_button.click()  # the limit job waits for the open
    assert window.jobs.active() >= 2
    texts = ("The cache could not be cleared:", "The cache limit could not be set:")
    with caplog.at_level(logging.WARNING, logger=module.__name__):
        if closing:
            window.close()
            assert application.closed()
        release.set()
        qtbot.waitUntil(lambda: application.cache.wait_open(0), timeout=30000)
        if not closing:
            qtbot.waitUntil(lambda: window.jobs.active() == 0, timeout=30000)
        qtbot.wait(300)  # a late completion is delivered by this loop
    errors = [m.text for m in startup_presenter(application).messages if m.owner == OWNER_SETTINGS]
    if closing:
        assert errors == []
        assert all(text in caplog.text for text in texts)
    else:
        assert sorted(text for text in texts if any(e.startswith(text) for e in errors)) == sorted(
            texts
        )
