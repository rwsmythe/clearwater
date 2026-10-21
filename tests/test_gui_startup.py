"""WP3.16 start-up and close through the clearwater.config API (brief task 3, question 9, S4).

Covers the task-8 rows "start-up" and the planted "a write to the real app-data folder". The real
app-data folder is never resolved: every window gets ``Locations`` under ``tmp_path``.
"""

# The shared fixture ``make_window`` is imported from gui_support and used as a parameter.
# ruff: noqa: F401, F811

from __future__ import annotations

import logging
from pathlib import Path

import pytest

import gui_support
from clearwater.config import (
    PresetStore,
    app_locations,
    load_settings,
    new_parameter_set,
    save_settings,
)
from clearwater.gui import shell
from clearwater.interfaces import Settings
from gui_support import (
    LevelMethod,
    image,
    locations,
    make_window,
    open_and_wait,
    photo_engines,
    presenter_of,
)

pytestmark = pytest.mark.gui


def test_start_up_creates_the_log_and_installs_the_starters_once(
    make_window, qtbot, tmp_path
) -> None:
    locs = locations(tmp_path)
    window = make_window()
    assert locs.log_file.is_file()
    names = [entry.name for entry in PresetStore(locs.presets_dir).list_presets()]
    assert names == ["Scuba (deep)", "Snorkel (shallow)"]
    window.close()
    assert "Clearwater closed" in locs.log_file.read_text(encoding="utf-8")
    PresetStore(locs.presets_dir).delete("Scuba (deep)")
    make_window()
    names = [entry.name for entry in PresetStore(locs.presets_dir).list_presets()]
    assert names == ["Snorkel (shallow)"]  # a deleted starter is not brought back


def test_settings_are_loaded_and_saved_with_the_last_parameters_at_close(
    make_window, qtbot, tmp_path
) -> None:
    locs = locations(tmp_path)
    save_settings(locs.config_dir, Settings(force_cpu=True, output_suffix="_x"))
    method = LevelMethod()
    window = make_window(photo_engines({}, methods={"level": method}))
    assert window.session.settings().force_cpu and window.session.settings().output_suffix == "_x"
    assert window.session.parameters().method == "level"
    window.session.set_parameters(new_parameter_set("level", {"level": 0.25}))
    window.close()
    stored = load_settings(locs.config_dir)
    assert stored.force_cpu and stored.output_suffix == "_x"
    assert stored.last_parameters is not None
    assert stored.last_parameters.method == "level"
    assert dict(stored.last_parameters.parameters) == {"level": 0.25}
    reopened = make_window(photo_engines({}, methods={"level": LevelMethod()}))
    assert dict(reopened.session.parameters().parameters) == {"level": 0.25}


def test_last_parameters_for_an_unknown_method_fall_back_with_a_warning(
    make_window, qtbot, tmp_path, caplog
) -> None:
    locs = locations(tmp_path)
    save_settings(locs.config_dir, Settings(last_parameters=new_parameter_set("gone", {"x": 1})))
    with caplog.at_level(logging.INFO, logger="clearwater"):
        window = make_window()
    assert window.session.parameters().method == "stub"
    assert dict(window.session.parameters().parameters) == {}
    warnings = [
        r for r in caplog.records if r.levelno == logging.WARNING and "gone" in r.getMessage()
    ]
    assert len(warnings) == 1


def test_first_run_uses_the_default_method_without_a_warning(make_window, qtbot, caplog) -> None:
    with caplog.at_level(logging.INFO, logger="clearwater"):
        window = make_window()
    assert window.session.parameters().method == "stub"
    assert not [r for r in caplog.records if r.levelno >= logging.WARNING]


def test_a_newer_settings_file_is_refused_and_left_untouched(make_window, qtbot, tmp_path) -> None:
    locs = locations(tmp_path)
    locs.config_dir.mkdir(parents=True)
    text = '{"format_version": 99, "anything": true}\n'
    locs.settings_file.write_text(text, encoding="utf-8")
    window = make_window()
    refusals = presenter_of(window).of("refusal")
    assert len(refusals) == 1 and "newer Clearwater" in refusals[0].text
    assert window.session.settings() == Settings()
    window.close()
    assert locs.settings_file.read_text(encoding="utf-8") == text


def test_a_failing_save_at_close_is_logged_not_raised(
    make_window, qtbot, tmp_path, monkeypatch, caplog
) -> None:
    window = make_window()

    def fail(folder: Path, settings: Settings) -> Path:
        raise OSError("read-only")

    monkeypatch.setattr(shell, "save_settings", fail)
    with caplog.at_level(logging.WARNING, logger="clearwater"):
        window.close()
    assert any("read-only" in r.getMessage() for r in caplog.records)


def _sentinel_environment(monkeypatch: pytest.MonkeyPatch, root: Path) -> None:
    """Point every app-data and home variable at ``root``."""
    for name in ("APPDATA", "LOCALAPPDATA", "XDG_CONFIG_HOME", "XDG_CACHE_HOME"):
        monkeypatch.setenv(name, str(root / name))
    monkeypatch.setenv("HOME", str(root / "home"))
    monkeypatch.setenv("USERPROFILE", str(root / "home"))


def _written_under(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*") if p.is_file()) if root.exists() else []


def _session(make_window, qtbot) -> None:
    path = Path("p.png")
    window = make_window(photo_engines({path: image(20, 20)}))
    open_and_wait(qtbot, window, path)
    window.session.set_settings(Settings(force_cpu=True))
    window.close()


def test_nothing_is_written_outside_the_injected_locations(
    make_window, qtbot, tmp_path, monkeypatch
) -> None:
    sentinel = tmp_path / "real-app-data"
    _sentinel_environment(monkeypatch, sentinel)
    _session(make_window, qtbot)
    assert _written_under(sentinel) == []
    assert (tmp_path / "config" / "settings.json").is_file()


def test_planted_write_to_the_real_app_data_folder_fails(
    make_window, qtbot, tmp_path, monkeypatch
) -> None:
    sentinel = tmp_path / "real-app-data"
    _sentinel_environment(monkeypatch, sentinel)
    real_start_up = shell.start_up

    def planted(locs, engines):
        return real_start_up(app_locations(), engines)

    monkeypatch.setattr(shell, "start_up", planted)
    _session(make_window, qtbot)
    assert _written_under(sentinel) != []  # the test above would fail on this implementation


def test_run_uses_the_given_engines_and_locations(qtbot, tmp_path, monkeypatch) -> None:
    from PySide6.QtWidgets import QApplication

    seen: list[object] = []

    def fake_exec() -> int:
        window = next(
            w
            for w in QApplication.topLevelWidgets()
            if isinstance(w, shell.MainWindow) and w.isVisible()
        )
        seen.append(window.context.locations)
        window.close()
        return 7

    monkeypatch.setattr(QApplication.instance(), "exec", fake_exec)
    locs = locations(tmp_path)
    assert shell.run(photo_engines({}), locs) == 7
    assert seen == [locs]
