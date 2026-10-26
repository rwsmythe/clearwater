"""WP3.17 Presets panel (G6, D37, D38, D90; V13 leg; DR-44 (b); DR-34 (a)).

Every operation runs against a real ``PresetStore`` under ``tmp_path`` with scripted dialogs, so
no test blocks on a modal dialog and the real app-data folder is never resolved.
"""

# The shared fixture ``make_window`` is imported from gui_support and used as a parameter.
# ruff: noqa: F401, F811

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import QDockWidget

import gui_support
from clearwater.config import PresetError, new_parameter_set
from clearwater.gui import Message, stub_engines
from clearwater.gui import preset_panel as pp
from clearwater.gui.parameter_panels import install_parameter_panels
from clearwater.gui.preset_panel import PresetPanel, QtPresetDialogs
from clearwater.interfaces import FormatError, Parameter, ParameterSet
from gui_support import ONE_STAGE, make_window, presenter_of

pytestmark = pytest.mark.gui


def _param(name: str, type_: Any, default: Any, lo: Any = None, hi: Any = None, **kw: Any):
    return Parameter(
        name, type_, default, lo, hi, kw.get("choices"), "basic", name, "", default,
        kw.get("nullable", False),
    )  # fmt: skip


C3 = (
    _param("gain", "float", 1.0, 0.0, 2.0),
    _param("mode", "enum", "a", choices=("a", "b")),
    _param("cap", "float", 2.0, 0.0, 10.0, nullable=True),
)
ANCUTI = (_param("gain", "float", 1.0, 0.0, 4.0),)


class Method:
    def __init__(self, method_id: str, parameters: tuple[Parameter, ...]) -> None:
        self.id = method_id
        self.label = method_id
        self.parameters = parameters
        self.stages = ONE_STAGE

    def analyze(self, *args: Any) -> Any:
        raise AssertionError("not rendered")

    def render(self, *args: Any) -> Any:
        raise AssertionError("not rendered")

    def closed_form(self, *args: Any) -> Any:
        return None


class ScriptedDialogs:
    """Dialogs answering from queues; an unscripted question fails the test."""

    def __init__(self) -> None:
        self.names: list[str | None] = []
        self.answers: list[bool] = []
        self.opens: list[Path | None] = []
        self.saves: list[Path | None] = []
        self.asked: list[tuple[str, str]] = []

    def _next(self, queue: list[Any], what: str) -> Any:
        if not queue:
            raise AssertionError(f"unscripted dialog: {what}")
        return queue.pop(0)

    def ask_name(self, title: str, initial: str) -> str | None:
        self.asked.append((title, initial))
        return self._next(self.names, f"ask_name {title}")

    def confirm(self, text: str) -> bool:
        self.asked.append(("confirm", text))
        return self._next(self.answers, f"confirm {text}")

    def open_file(self) -> Path | None:
        self.asked.append(("open", ""))
        return self._next(self.opens, "open_file")

    def save_file(self, initial_name: str) -> Path | None:
        self.asked.append(("save", initial_name))
        return self._next(self.saves, "save_file")

    def confirms(self) -> list[str]:
        return [text for kind, text in self.asked if kind == "confirm"]


class Setup:
    def __init__(self, window, panel, dialogs, store) -> None:
        self.window = window
        self.panel = panel
        self.dialogs = dialogs
        self.store = store
        self.presenter = presenter_of(window)

    def names(self) -> list[str]:
        return [self.panel.list.item(i).text() for i in range(self.panel.list.count())]

    def select(self, name: str) -> None:
        self.panel.select(name)
        assert self.panel.selected() == name

    def session_parameters(self) -> ParameterSet:
        return self.window.session.parameters()

    def own(self) -> list[Message]:
        return [m for m in self.presenter.messages if m.owner == "presets"]


def build(make_window, methods: Mapping[str, Any] | None = None) -> Setup:
    dialogs = ScriptedDialogs()
    window = make_window(stub_engines(methods=methods or {"c3": Method("c3", C3)}))
    presenter = presenter_of(window)
    plain_clear = presenter.clear

    def checked_clear(severity: str | None = None, *, owner: str | None = None) -> None:
        assert owner == "presets", "a clear without the panel's owner"
        plain_clear(severity, owner=owner)

    presenter.clear = checked_clear  # type: ignore[method-assign]
    install_parameter_panels(window, dialogs=dialogs)
    panel = window.findChildren(PresetPanel)[0]
    return Setup(window, panel, dialogs, window.context.presets)


def put(setup: Setup, name: str, method: str = "c3", **parameters: Any) -> None:
    setup.store.save(name, new_parameter_set(method, parameters))
    setup.panel.refresh()


def file_for(setup: Setup, name: str) -> Path:
    return setup.store.folder / f"{name}.json"


# Listing.


def test_the_panels_are_attached_in_the_parameters_area_in_order(make_window) -> None:
    setup = build(make_window)
    docks = [d for d in setup.window.findChildren(QDockWidget) if d.objectName()]
    assert [d.objectName() for d in docks] == [
        "parameters:Basic", "parameters:Advanced", "parameters:Presets",
    ]  # fmt: skip
    assert [d.windowTitle() for d in docks] == ["Basic", "Advanced", "Presets"]


def test_the_starter_presets_are_listed_and_loadable_with_the_c3_method(make_window) -> None:
    setup = build(make_window)
    assert setup.names() == ["Scuba (deep)", "Snorkel (shallow)"]
    setup.select("Snorkel (shallow)")
    setup.panel.load()
    assert setup.session_parameters().method == "c3"
    assert dict(setup.session_parameters().parameters) == {}
    assert setup.own() == [] and "Loaded" in setup.panel.status.text()


def test_a_starter_cannot_load_when_c3_is_not_available(make_window) -> None:
    setup = build(make_window, {"stub": Method("stub", ())})
    setup.select("Scuba (deep)")
    setup.panel.load()
    (error,) = setup.own()
    assert error.severity == "error" and "'c3'" in error.text and "stub" in error.text
    assert setup.session_parameters().method == "stub"


def test_buttons_act_on_a_selection_only(make_window) -> None:
    setup = build(make_window)
    setup.panel.list.setCurrentRow(-1)
    setup.panel.list.clearSelection()
    setup.panel.refresh()
    buttons = setup.panel.buttons
    assert [buttons[k].isEnabled() for k in ("load", "rename", "delete", "export")] == [False] * 4
    assert buttons["save"].isEnabled() and buttons["import"].isEnabled()
    setup.select("Scuba (deep)")
    assert all(buttons[k].isEnabled() for k in buttons)


def test_the_list_is_refreshed_when_the_panel_is_shown(make_window) -> None:
    setup = build(make_window)
    setup.store.save("Added elsewhere", new_parameter_set("c3", {}))
    assert "Added elsewhere" not in setup.names()
    setup.panel.showEvent(QShowEvent())
    assert "Added elsewhere" in setup.names()


def test_an_unreadable_and_a_newer_version_file_are_listed_disabled_and_untouched(
    make_window,
) -> None:
    setup = build(make_window)
    folder = setup.store.folder
    (folder / "bad.json").write_text("{not json", encoding="utf-8")
    future = json.dumps(
        {"format_version": 2, "method": "c3", "parameters": {}, "created": "x", "app_version": "9"}
    )
    (folder / "future.json").write_text(future, encoding="utf-8")
    before = {n: (folder / n).read_bytes() for n in ("bad.json", "future.json")}
    setup.panel.refresh()
    items = {
        setup.panel.list.item(i).text(): setup.panel.list.item(i)
        for i in range(setup.panel.list.count())
    }
    for name in ("bad", "future"):
        item = items[name]
        assert not item.flags() & Qt.ItemFlag.ItemIsEnabled
        setup.panel.list.setCurrentItem(item)
        assert setup.panel.selected() is None
    assert "newer Clearwater" in items["future"].toolTip()
    assert items["bad"].toolTip() and "newer" not in items["bad"].toolTip()
    # No operation reaches them: nothing is selected, so no button acts and no dialog is asked.
    for operation in (
        setup.panel.load, setup.panel.rename, setup.panel.delete, setup.panel.export,
    ):  # fmt: skip
        operation()
    assert setup.dialogs.asked == []
    # Save as with their name is refused by the store and the file stays as it was.
    setup.dialogs.names.append("BAD")
    setup.panel.save_as()
    (error,) = setup.own()
    assert "already exists" in error.text and setup.dialogs.confirms() == []
    assert {n: (folder / n).read_bytes() for n in before} == before


# Save as.


def test_save_as_writes_a_new_preset_and_selects_it(make_window) -> None:
    setup = build(make_window)
    setup.window.session.set_parameters(new_parameter_set("c3", {"gain": 0.7, "cap": None}))
    setup.dialogs.names.append("Mine")
    setup.panel.save_as()
    saved = setup.store.load("Mine")
    assert saved.method == "c3" and dict(saved.parameters) == {"gain": 0.7, "cap": None}
    assert saved.created == setup.session_parameters().created  # stored as the session has it
    assert setup.panel.selected() == "Mine" and "Saved" in setup.panel.status.text()
    assert setup.dialogs.confirms() == []


def test_save_as_offers_the_selected_name(make_window) -> None:
    setup = build(make_window)
    setup.select("Scuba (deep)")
    setup.dialogs.names.append(None)
    setup.panel.save_as()
    assert setup.dialogs.asked == [("Save preset", "Scuba (deep)")]


def _assert_save_over_needs_confirmation(make_window) -> None:
    setup = build(make_window)
    put(setup, "Mine", gain=0.1)
    original = file_for(setup, "Mine").read_bytes()
    setup.window.session.set_parameters(new_parameter_set("c3", {"gain": 1.9}))
    # Declined (the name matches case-insensitively): nothing is replaced.
    setup.dialogs.names.append("MINE")
    setup.dialogs.answers.append(False)
    setup.panel.save_as()
    assert len(setup.dialogs.confirms()) == 1, "the panel replaced a preset without asking"
    assert file_for(setup, "Mine").read_bytes() == original
    # Confirmed: replaced, and still one file.
    setup.dialogs.names.append("MINE")
    setup.dialogs.answers.append(True)
    setup.panel.save_as()
    assert len(setup.dialogs.confirms()) == 2
    assert dict(setup.store.load("Mine").parameters) == {"gain": 1.9}
    assert [e.name for e in setup.store.list_presets() if e.name.lower() == "mine"] == ["Mine"]


def test_save_over_an_existing_name_asks_and_replaces_only_when_confirmed(make_window) -> None:
    _assert_save_over_needs_confirmation(make_window)


def test_planted_save_that_overwrites_without_asking_fails(make_window, monkeypatch) -> None:
    def wrong(self: PresetPanel) -> None:
        name = self._dialogs.ask_name("Save preset", "")
        if name is not None:
            self._store.save(name, self._session.parameters(), overwrite=True)

    monkeypatch.setattr(PresetPanel, "save_as", wrong)
    with pytest.raises(AssertionError, match="without asking"):
        _assert_save_over_needs_confirmation(make_window)


def test_save_as_with_a_bad_name_is_an_error(make_window) -> None:
    setup = build(make_window)
    setup.dialogs.names.append("a/b")
    setup.panel.save_as()
    (error,) = setup.own()
    assert error.severity == "error" and "preset name" in error.text
    assert not any(n == "a/b" for n in setup.names())


# Load.


def test_load_applies_a_preset(make_window) -> None:
    setup = build(make_window)
    put(setup, "Gentle", gain=0.4, mode="b", cap=None)
    setup.select("Gentle")
    setup.panel.load()
    assert dict(setup.session_parameters().parameters) == {"gain": 0.4, "mode": "b", "cap": None}


def test_load_of_an_unknown_method_names_the_preset_and_the_method(make_window) -> None:
    setup = build(make_window)
    put(setup, "Alien", method="zeta")
    setup.select("Alien")
    setup.panel.load()
    (error,) = setup.own()
    assert "'Alien'" in error.text and "'zeta'" in error.text and "c3" in error.text
    assert setup.session_parameters().method == "c3"


def _assert_nothing_applied_after_a_schema_problem(make_window) -> None:
    setup = build(make_window)
    put(setup, "Broken", gain=5.0, mode="zz")
    before = setup.session_parameters()
    setup.select("Broken")
    setup.panel.load()
    assert setup.session_parameters() is before, "a preset was applied despite a schema problem"
    errors = setup.own()
    assert len(errors) == 1
    assert "gain" in errors[0].text and "mode" in errors[0].text  # every problem is listed


def test_load_with_schema_problems_lists_them_all_and_applies_nothing(make_window) -> None:
    _assert_nothing_applied_after_a_schema_problem(make_window)


def test_planted_load_that_skips_validation_fails(make_window, monkeypatch) -> None:
    monkeypatch.setattr(pp, "validate_parameter_set", lambda *args, **kwargs: [])
    with pytest.raises(AssertionError, match="despite a schema problem"):
        _assert_nothing_applied_after_a_schema_problem(make_window)


# Rename and delete.


def test_rename_moves_the_preset_and_selects_the_new_name(make_window) -> None:
    setup = build(make_window)
    put(setup, "Old", gain=0.3)
    setup.select("Old")
    setup.dialogs.names.append("New")
    setup.panel.rename()
    assert not file_for(setup, "Old").exists() and dict(setup.store.load("New").parameters) == {
        "gain": 0.3
    }
    assert setup.panel.selected() == "New" and setup.dialogs.asked == [("Rename preset", "Old")]


def test_rename_to_a_taken_or_bad_name_is_an_error_and_cancel_does_nothing(make_window) -> None:
    setup = build(make_window)
    put(setup, "Old")
    setup.select("Old")
    setup.dialogs.names.append("scuba (DEEP)")
    setup.panel.rename()
    assert "already exists" in setup.own()[0].text
    setup.dialogs.names.append("x*y")
    setup.panel.rename()
    assert len(setup.own()) == 2
    setup.dialogs.names.append(None)
    setup.panel.rename()
    setup.dialogs.names.append("Old")  # the same name: nothing to do
    setup.panel.rename()
    assert len(setup.own()) == 2 and file_for(setup, "Old").exists()


def test_delete_asks_first(make_window) -> None:
    setup = build(make_window)
    put(setup, "Doomed")
    setup.select("Doomed")
    setup.dialogs.answers.append(False)
    setup.panel.delete()
    assert file_for(setup, "Doomed").exists() and "Doomed" in setup.dialogs.confirms()[0]
    setup.dialogs.answers.append(True)
    setup.panel.delete()
    assert not file_for(setup, "Doomed").exists() and "Doomed" not in setup.names()


# Import and export.


def write_preset(folder: Path, name: str, parameter_set: ParameterSet) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{name}.json"
    path.write_text(parameter_set.to_json() + "\n", encoding="utf-8")
    return path


def test_import_of_a_valid_file_stores_it_under_its_stem(make_window, tmp_path) -> None:
    setup = build(make_window)
    path = write_preset(tmp_path / "in", "shared", new_parameter_set("c3", {"gain": 0.5}))
    setup.dialogs.opens.append(path)
    setup.panel.import_file()
    assert dict(setup.store.load("shared").parameters) == {"gain": 0.5}
    assert setup.panel.selected() == "shared" and setup.own() == []
    assert setup.panel.status.text() == "Imported 'shared'."
    setup.dialogs.opens.append(path)
    setup.panel.import_file()
    assert "shared (2)" in setup.names()
    assert setup.panel.status.text() == "Imported as 'shared (2)'."


def test_import_of_an_unknown_method_and_of_schema_problems_is_an_error(
    make_window, tmp_path
) -> None:
    setup = build(make_window)
    alien = write_preset(tmp_path / "in", "alien", new_parameter_set("zeta", {}))
    broken = write_preset(
        tmp_path / "in", "broken", new_parameter_set("c3", {"gain": 9.0, "mode": "q"})
    )
    for path in (alien, broken):
        setup.dialogs.opens.append(path)
        setup.panel.import_file()
    first, second = setup.own()
    assert "unknown method" in first.text and first.path == alien
    assert "gain" in second.text and "mode" in second.text and second.path == broken
    assert "alien" not in setup.names() and "broken" not in setup.names()


def test_import_of_garbage_a_newer_file_and_a_bad_stem_are_errors(make_window, tmp_path) -> None:
    setup = build(make_window)
    folder = tmp_path / "in"
    folder.mkdir()
    garbage = folder / "garbage.json"
    garbage.write_text("[1, 2", encoding="utf-8")
    newer = folder / "newer.json"
    newer.write_text(json.dumps({"format_version": 7}), encoding="utf-8")
    reserved = write_preset(folder, "CON", new_parameter_set("c3", {}))
    for path in (garbage, newer, reserved, folder / "missing.json"):
        setup.dialogs.opens.append(path)
        setup.panel.import_file()
    assert len(setup.own()) == 4 and all(m.severity == "error" for m in setup.own())
    assert any("format_version" in m.text for m in setup.own())
    assert setup.names() == ["Scuba (deep)", "Snorkel (shallow)"]


def test_import_of_a_provenance_sidecar_warns_naming_the_dropped_keys(
    make_window, tmp_path
) -> None:
    setup = build(make_window)
    sidecar = ParameterSet(
        "c3", {"gain": 0.6}, new_parameter_set("c3", {}).created, "1.0",
        source={"path": "clip.mp4", "size": 1}, settings={"encoder": "h264"},
    )  # fmt: skip
    path = write_preset(tmp_path / "in", "run", sidecar)
    setup.dialogs.opens.append(path)
    setup.panel.import_file()
    (warning,) = setup.own()
    assert warning.severity == "warning" and warning.path == path
    assert "source, settings" in warning.text and "run" in warning.text
    stored = json.loads(file_for(setup, "run").read_text(encoding="utf-8"))
    assert "source" not in stored and "settings" not in stored
    # The next success replaces the warning.
    setup.select("run")
    setup.panel.load()
    assert setup.own() == []


def test_cancelled_dialogs_change_nothing(make_window, tmp_path) -> None:
    setup = build(make_window)
    setup.presenter.present(Message("error", "earlier", owner="presets"))
    setup.select("Scuba (deep)")
    setup.dialogs.names.append(None)
    setup.panel.save_as()
    setup.dialogs.opens.append(None)
    setup.panel.import_file()
    setup.dialogs.saves.append(None)
    setup.panel.export()
    setup.dialogs.answers.append(False)
    setup.panel.delete()
    assert [m.text for m in setup.own()] == ["earlier"]
    assert setup.names() == ["Scuba (deep)", "Snorkel (shallow)"]


def test_export_writes_a_new_file(make_window, tmp_path) -> None:
    setup = build(make_window)
    put(setup, "Out", gain=1.5)
    setup.select("Out")
    target = tmp_path / "exported" / "out.json"
    target.parent.mkdir()
    setup.dialogs.saves.append(target)
    setup.panel.export()
    assert setup.dialogs.asked == [("save", "Out.json")]
    assert ParameterSet.from_json(target.read_text(encoding="utf-8")) == setup.store.load("Out")
    assert setup.dialogs.confirms() == [] and "Exported" in setup.panel.status.text()


def _assert_export_over_a_file_needs_confirmation(make_window, tmp_path) -> None:
    setup = build(make_window)
    put(setup, "Out", gain=1.5)
    setup.select("Out")
    target = tmp_path / "taken.json"
    target.write_text("precious", encoding="utf-8")
    setup.dialogs.saves.append(target)
    setup.dialogs.answers.append(False)
    setup.panel.export()
    assert len(setup.dialogs.confirms()) == 1, "an existing file was replaced without asking"
    assert target.read_text(encoding="utf-8") == "precious"
    setup.dialogs.saves.append(target)
    setup.dialogs.answers.append(True)
    setup.panel.export()
    assert ParameterSet.from_json(target.read_text(encoding="utf-8")).parameters == {"gain": 1.5}


def test_export_over_an_existing_file_asks_and_replaces_only_when_confirmed(
    make_window, tmp_path
) -> None:
    _assert_export_over_a_file_needs_confirmation(make_window, tmp_path)


def test_planted_export_that_overwrites_without_asking_fails(
    make_window, tmp_path, monkeypatch
) -> None:
    def wrong(self: PresetPanel) -> None:
        name = self.selected()
        target = self._dialogs.save_file(f"{name}.json")
        if name is not None and target is not None:
            self._store.export_preset(name, target, overwrite=True)

    monkeypatch.setattr(PresetPanel, "export", wrong)
    with pytest.raises(AssertionError, match="without asking"):
        _assert_export_over_a_file_needs_confirmation(make_window, tmp_path)


def test_export_to_a_folder_is_an_error(make_window, tmp_path) -> None:
    setup = build(make_window)
    setup.select("Scuba (deep)")
    setup.dialogs.saves.append(tmp_path)
    setup.dialogs.answers.append(True)
    setup.panel.export()
    (error,) = setup.own()
    assert "folder" in error.text and error.path == tmp_path


def test_v13_save_export_import_load_reproduces_the_set(make_window, tmp_path) -> None:
    setup = build(make_window)
    setup.window.session.set_parameters(
        new_parameter_set("c3", {"gain": 0.7, "mode": "b", "cap": None})
    )
    saved_from = setup.session_parameters()
    setup.dialogs.names.append("v13")
    setup.panel.save_as()
    exported = tmp_path / "carry" / "v13-copy.json"
    exported.parent.mkdir()
    setup.dialogs.saves.append(exported)
    setup.panel.export()
    setup.select("v13")
    setup.dialogs.answers.append(True)
    setup.panel.delete()
    setup.window.session.set_parameters(new_parameter_set("c3", {"gain": 2.0}))
    setup.dialogs.opens.append(exported)
    setup.panel.import_file()
    assert setup.panel.selected() == "v13-copy"
    setup.panel.load()
    loaded = setup.session_parameters()
    assert loaded.method == saved_from.method == "c3"
    assert dict(loaded.parameters) == dict(saved_from.parameters)
    assert loaded.app_version == saved_from.app_version
    assert loaded.created == saved_from.created


# Messages (DR-44 (b)) and robustness.


def _assert_a_foreign_error_survives_a_load(make_window) -> None:
    setup = build(make_window)
    put(setup, "Fine", gain=0.9)
    setup.presenter.present(Message("error", "preview broke", owner="shell.preview"))
    setup.select("Fine")
    setup.panel.load()
    assert [m.text for m in setup.presenter.messages] == ["preview broke"]
    assert dict(setup.session_parameters().parameters) == {"gain": 0.9}


def test_another_owners_error_survives_a_successful_load(make_window) -> None:
    _assert_a_foreign_error_survives_a_load(make_window)


def test_planted_clear_without_an_owner_fails(make_window, monkeypatch) -> None:
    def wrong(self: PresetPanel, text: str) -> None:
        self._context.messages.clear("error")
        self.status.setText(text)

    monkeypatch.setattr(PresetPanel, "_succeed", wrong)
    with pytest.raises(AssertionError, match="without the panel's owner"):
        _assert_a_foreign_error_survives_a_load(make_window)


def test_the_panels_own_error_is_cleared_by_its_next_success(make_window) -> None:
    setup = build(make_window)
    put(setup, "Alien", method="zeta")
    put(setup, "Fine")
    setup.presenter.present(Message("error", "preview broke", owner="shell.preview"))
    setup.select("Alien")
    setup.panel.load()
    assert [m.owner for m in setup.presenter.messages] == ["shell.preview", "presets"]
    setup.select("Fine")
    setup.panel.load()
    assert [m.owner for m in setup.presenter.messages] == ["shell.preview"]


@pytest.mark.parametrize(
    "error",
    [OSError("disk gone"), FormatError("bad shape"), PresetError("refused"), ValueError("plain")],
)
def test_no_exception_escapes_a_slot(make_window, tmp_path, monkeypatch, error) -> None:
    setup = build(make_window)
    put(setup, "Some")
    setup.select("Some")
    store = setup.store

    def boom(*args: Any, **kwargs: Any) -> Any:
        raise error

    for method in ("load", "save", "rename", "delete", "import_preset", "export_preset"):
        monkeypatch.setattr(store, method, boom)
    setup.dialogs.names += ["Other", "Other"]
    setup.dialogs.answers += [True, True, True]
    setup.dialogs.opens.append(tmp_path / "x.json")
    setup.dialogs.saves.append(tmp_path / "y.json")
    setup.panel.load()
    setup.panel.save_as()
    setup.panel.rename()
    setup.panel.delete()
    setup.panel.import_file()
    setup.panel.export()
    errors = setup.own()
    assert len(errors) == 6 and all(m.severity == "error" for m in errors)
    assert all(str(error) in m.text for m in errors)


def test_a_message_text_is_ascii_safe(make_window) -> None:
    setup = build(make_window)
    put(setup, "café", method="zeta")
    setup.select("café")
    setup.panel.load()
    (error,) = setup.own()
    assert error.text.isascii() and "caf\\xe9" in error.text


# The Qt dialogs.


def test_the_qt_dialogs_map_their_results(qtbot, monkeypatch, tmp_path) -> None:
    dialogs = QtPresetDialogs(None)
    monkeypatch.setattr(pp.QInputDialog, "getText", lambda *a, **k: ("Name", True))
    assert dialogs.ask_name("t", "i") == "Name"
    monkeypatch.setattr(pp.QInputDialog, "getText", lambda *a, **k: ("Name", False))
    assert dialogs.ask_name("t", "i") is None
    yes, no = pp.QMessageBox.StandardButton.Yes, pp.QMessageBox.StandardButton.No
    monkeypatch.setattr(pp.QMessageBox, "question", lambda *a, **k: yes)
    assert dialogs.confirm("?") is True
    monkeypatch.setattr(pp.QMessageBox, "question", lambda *a, **k: no)
    assert dialogs.confirm("?") is False
    monkeypatch.setattr(
        pp.QFileDialog, "getOpenFileName", lambda *a, **k: (str(tmp_path / "a.json"), "")
    )
    assert dialogs.open_file() == tmp_path / "a.json"
    monkeypatch.setattr(pp.QFileDialog, "getOpenFileName", lambda *a, **k: ("", ""))
    assert dialogs.open_file() is None
    monkeypatch.setattr(
        pp.QFileDialog, "getSaveFileName", lambda *a, **k: (str(tmp_path / "b"), "")
    )
    assert dialogs.save_file("b.json") == tmp_path / "b.json"
    monkeypatch.setattr(
        pp.QFileDialog, "getSaveFileName", lambda *a, **k: (str(tmp_path / "c.JSON"), "")
    )
    assert dialogs.save_file("c.json") == tmp_path / "c.JSON"
    monkeypatch.setattr(pp.QFileDialog, "getSaveFileName", lambda *a, **k: ("", ""))
    assert dialogs.save_file("c.json") is None


def test_the_default_dialogs_are_the_qt_ones(make_window) -> None:
    window = make_window(stub_engines())
    panel = pp.preset_panel(window.context)
    assert isinstance(panel._dialogs, QtPresetDialogs)


# Round-1 regressions (Reviewer A, findings 1-3).


def test_load_and_export_refresh_the_list(make_window, tmp_path) -> None:
    setup = build(make_window)
    put(setup, "Seen")
    setup.select("Seen")
    setup.store.save("Added outside", new_parameter_set("c3", {}))
    assert "Added outside" not in setup.names()
    setup.panel.load()
    assert "Added outside" in setup.names()
    setup.store.save("Added again", new_parameter_set("c3", {}))
    setup.dialogs.saves.append(tmp_path / "seen-copy.json")
    setup.panel.export()
    assert "Added again" in setup.names()


def test_a_listing_error_after_a_successful_operation_is_not_hidden(
    make_window, monkeypatch
) -> None:
    setup = build(make_window)
    put(setup, "Old")
    setup.select("Old")
    setup.dialogs.names.append("New")

    def unlistable() -> list[Any]:
        raise OSError("folder gone")

    monkeypatch.setattr(setup.store, "list_presets", unlistable)
    setup.panel.rename()
    assert file_for(setup, "New").exists()
    (error,) = setup.own()
    assert "folder gone" in error.text and error.severity == "error"


def test_a_case_only_save_over_selects_the_stored_preset(make_window) -> None:
    setup = build(make_window)
    put(setup, "Mine")
    put(setup, "Other")
    setup.select("Other")
    setup.dialogs.names.append("MINE")
    setup.dialogs.answers.append(True)
    setup.panel.save_as()
    assert setup.panel.selected() == "Mine"
