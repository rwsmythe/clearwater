"""WP3.15: the preset store (G6; D37, D38, D90), V13, names, import validation, starters, DR-32."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from clearwater import __version__
from clearwater.config import (
    PresetError,
    PresetImportError,
    PresetStore,
    UnsupportedPresetImportError,
    UnsupportedPresetVersionError,
    check_string_keys,
    new_parameter_set,
    starter_presets,
    validate_preset_name,
)
from clearwater.config.presets import MAX_NAME_BYTES, MAX_PRESET_BYTES
from clearwater.interfaces import (
    FormatError,
    Parameter,
    ParameterSet,
    UnsupportedFormatVersionError,
)

CREATED = datetime(2026, 10, 20, 12, 30, 15, 123456, tzinfo=UTC)

SCHEMA = (
    Parameter("strength", "float", 0.5, 0.0, 1.0, None, "basic", "S", "h", 0.0),
    Parameter("steps", "int", 3, 1, 10, None, "basic", "N", "h", 1),
    Parameter("enabled", "bool", True, None, None, None, "basic", "E", "h", False),
    Parameter("mode", "enum", "a", None, None, ("a", "b"), "advanced", "M", "h", "a"),
    Parameter("cap", "float", None, 0.0, 9.0, None, "advanced", "C", "h", None, nullable=True),
)
SCHEMAS = {"c3": SCHEMA}


def _set(**kwargs: Any) -> ParameterSet:
    return ParameterSet(
        "c3", {"strength": 0.25, "steps": 4, "enabled": False}, CREATED, "1.2.3", **kwargs
    )


def _store(tmp_path: Path) -> PresetStore:
    return PresetStore(tmp_path / "presets")


def _file(tmp_path: Path, name: str, data: object) -> Path:
    path = tmp_path / name
    path.write_text(data if isinstance(data, str) else json.dumps(data), encoding="utf-8")
    return path


# --- save / load / list -------------------------------------------------------------------------


def test_save_load_and_list(tmp_path: Path) -> None:
    store = _store(tmp_path)
    assert store.list_presets() == []
    path = store.save("My look", _set())
    assert path == tmp_path / "presets" / "My look.json"
    assert store.load("My look") == _set()
    entries = store.list_presets()
    assert [(e.name, e.error) for e in entries] == [("My look", None)]
    assert entries[0].parameter_set == _set()


def test_reads_do_not_create_the_folder(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.list_presets()
    with pytest.raises(PresetError):
        store.load("nothing")
    assert not (tmp_path / "presets").exists()


def test_saved_file_is_the_ad13_object_without_provenance(tmp_path: Path) -> None:
    store = _store(tmp_path)
    path = store.save("p", _set(source={"path": "a.mp4"}, settings={"encoder": "libx265"}))
    data = json.loads(path.read_text(encoding="utf-8"))
    assert set(data) == {"format_version", "method", "parameters", "created", "app_version"}
    assert data["format_version"] == 1
    assert data["created"] == "2026-10-20T12:30:15.123456+00:00"
    assert store.load("p").source is None
    assert store.load("p").settings is None


def test_save_refuses_an_existing_name_unless_overwrite(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.save("Look", _set())
    with pytest.raises(PresetError, match="already exists"):
        store.save("look", _set())  # case-insensitive
    other = ParameterSet("c3", {"steps": 9}, CREATED, "1.2.3")
    path = store.save("look", other, overwrite=True)
    assert path.name == "Look.json"  # the existing spelling is kept
    assert [e.name for e in store.list_presets()] == ["Look"]
    assert store.load("Look") == other


def test_overwrite_never_replaces_an_unreadable_file(tmp_path: Path) -> None:
    store = _store(tmp_path)
    bad = tmp_path / "presets" / "Broken.json"
    bad.parent.mkdir()
    bad.write_text("{nope", encoding="utf-8")
    with pytest.raises(PresetError, match="not a readable preset"):
        store.save("Broken", _set(), overwrite=True)
    assert bad.read_text(encoding="utf-8") == "{nope"


def test_list_reports_unreadable_files_and_leaves_them_untouched(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.save("good", _set())
    folder = tmp_path / "presets"
    (folder / "bad.json").write_text("{nope", encoding="utf-8")
    future = _set().to_dict()
    future["format_version"] = 2
    (folder / "future.json").write_text(json.dumps(future), encoding="utf-8")
    (folder / "notes.txt").write_text("hi", encoding="utf-8")
    (folder / "sub.json").mkdir()
    entries = {e.name: e for e in store.list_presets()}
    assert set(entries) == {"bad", "future", "good"}
    assert entries["good"].error is None
    assert entries["bad"].parameter_set is None and entries["bad"].error
    assert "format_version" in (entries["future"].error or "")
    assert (folder / "bad.json").read_text(encoding="utf-8") == "{nope"


def test_list_is_sorted_case_insensitively(tmp_path: Path) -> None:
    store = _store(tmp_path)
    for name in ("b", "A", "c"):
        store.save(name, _set())
    assert [e.name for e in store.list_presets()] == ["A", "b", "c"]


# --- V13 ----------------------------------------------------------------------------------------


def test_v13_export_then_import_reproduces_the_set(tmp_path: Path) -> None:
    store = _store(tmp_path)
    original = _set()
    store.save("Round", original)
    exported = store.export_preset("Round", tmp_path / "out" / "Round.json")
    assert json.loads(exported.read_text(encoding="utf-8"))["format_version"] == 1
    other = PresetStore(tmp_path / "other")
    result = other.import_preset(exported, SCHEMAS)
    assert result.parameter_set == original
    assert result.parameter_set.method == "c3"
    assert result.parameter_set.parameters == original.parameters
    assert result.parameter_set.created == CREATED
    assert result.parameter_set.app_version == "1.2.3"
    assert result.provenance_dropped is False
    assert result.dropped_keys == ()
    assert other.load("Round") == original
    # the file carries the version, and equality compares the dict form including it
    assert other.load("Round").to_dict() == original.to_dict()


def test_export_refuses_existing_destination_unless_overwrite(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.save("p", _set())
    target = tmp_path / "p.json"
    target.write_text("keep", encoding="utf-8")
    with pytest.raises(PresetError, match="already exists"):
        store.export_preset("p", target)
    assert target.read_text(encoding="utf-8") == "keep"
    store.export_preset("p", target, overwrite=True)
    assert ParameterSet.from_json(target.read_text(encoding="utf-8")) == _set()
    with pytest.raises(PresetError, match="folder"):
        store.export_preset("p", tmp_path)


# --- rename / delete ----------------------------------------------------------------------------


def test_rename_keeps_content_and_refuses_taken_names(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.save("one", _set())
    store.save("two", _set())
    path = store.rename("one", "uno")
    assert path.name == "uno.json"
    assert store.load("uno") == _set()
    with pytest.raises(PresetError):
        store.load("one")
    with pytest.raises(PresetError, match="already exists"):
        store.rename("uno", "TWO")
    assert {e.name for e in store.list_presets()} == {"uno", "two"}


def test_case_only_rename_is_allowed(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.save("look", _set())
    store.rename("look", "Look")
    assert [e.name for e in store.list_presets()] == ["Look"]


def test_rename_to_the_same_name_is_a_noop(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.save("look", _set())
    assert store.rename("look", "look").name == "look.json"
    assert [e.name for e in store.list_presets()] == ["look"]


def test_delete_removes_only_the_named_preset(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.save("a", _set())
    store.save("b", _set())
    store.delete("a")
    assert [e.name for e in store.list_presets()] == ["b"]
    with pytest.raises(PresetError, match="no preset"):
        store.delete("a")


def test_rename_and_delete_cannot_touch_non_preset_files(tmp_path: Path) -> None:
    store = _store(tmp_path)
    folder = tmp_path / "presets"
    folder.mkdir()
    (folder / "bad.json").write_text("{nope", encoding="utf-8")
    (folder / "notes.txt").write_text("keep", encoding="utf-8")
    (folder / ".starters-installed").write_text("1\n", encoding="utf-8")
    outside = tmp_path / "secret.json"
    outside.write_text(_set().to_json(), encoding="utf-8")
    for name in ("bad", "notes.txt", ".starters-installed", "../secret", "..\\secret"):
        with pytest.raises(PresetError):
            store.delete(name)
        with pytest.raises(PresetError):
            store.rename(name, "target")
    store.save("ok", _set())
    with pytest.raises(PresetError):
        store.rename("ok", "../escape")
    assert (folder / "bad.json").read_text(encoding="utf-8") == "{nope"
    assert (folder / "notes.txt").read_text(encoding="utf-8") == "keep"
    assert outside.exists()
    assert not (tmp_path / "escape.json").exists()


def test_a_symlinked_preset_is_not_acted_on(tmp_path: Path) -> None:
    store = _store(tmp_path)
    folder = tmp_path / "presets"
    folder.mkdir()
    real = tmp_path / "real.json"
    real.write_text(_set().to_json(), encoding="utf-8")
    try:
        (folder / "link.json").symlink_to(real)
    except OSError:
        pytest.skip("symlinks are not available here")
    with pytest.raises(PresetError):
        store.delete("link")
    assert real.exists()


# --- names --------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "name",
    [
        "Snorkel (shallow)",
        "Scuba (deep)",
        "a",
        "with.dot",
        "café プリセット",
        "x" * 100,
        "console",  # not a device name
        "CONSOLE.txt",
    ],
)
def test_portable_names_are_accepted(name: str) -> None:
    assert validate_preset_name(name) == name


@pytest.mark.parametrize(
    "name",
    [
        "",
        " ",
        " lead",
        "trail ",
        "dot.",
        ".",
        "..",
        "a/b",
        "a\\b",
        "a:b",
        'a"b',
        "a<b",
        "a>b",
        "a|b",
        "a?b",
        "a*b",
        "a\x00b",
        "a\tb",
        "a\x7fb",
        "x" * 101,
        "CON",
        "con",
        "Prn",
        "AUX",
        "NUL",
        "COM1",
        "com9",
        "LPT1",
        "lpt0",
        "COM¹",
        "CON.txt",
        "nul.tar.gz",
        "CON .x",
        "CONIN$",
        "bad\ud800name",
    ],
)
def test_non_portable_names_are_refused_on_every_os(name: str, tmp_path: Path) -> None:
    with pytest.raises(PresetError):
        validate_preset_name(name)
    store = _store(tmp_path)
    with pytest.raises(PresetError):
        store.save(name, _set())
    assert not (tmp_path / "presets").exists()


# --- import validation: each ProblemKind --------------------------------------------------------


def _import_with(tmp_path: Path, parameters: dict[str, Any], method: str = "c3") -> Path:
    data = _set().to_dict()
    data["method"] = method
    data["parameters"] = parameters
    return _file(tmp_path, "in.json", data)


def _problems(tmp_path: Path, parameters: dict[str, Any], method: str = "c3") -> dict[str, str]:
    source = _import_with(tmp_path, parameters, method)
    with pytest.raises(PresetImportError) as raised:
        PresetStore(tmp_path / "presets").import_preset(source, SCHEMAS)
    assert not (tmp_path / "presets").exists()  # a refused import stores nothing
    return {str(problem.name): problem.kind for problem in raised.value.problems}


def test_import_reports_unknown_method_without_guessing(tmp_path: Path) -> None:
    source = _import_with(tmp_path, {}, method="zz")
    with pytest.raises(PresetImportError) as raised:
        PresetStore(tmp_path / "presets").import_preset(source, SCHEMAS)
    assert [p.kind for p in raised.value.problems] == ["method_mismatch"]
    assert "zz" in str(raised.value)
    with pytest.raises(PresetImportError):
        PresetStore(tmp_path / "presets").import_preset(source, {})


def test_import_reports_unknown_name(tmp_path: Path) -> None:
    assert _problems(tmp_path, {"nope": 1}) == {"nope": "unknown_name"}


def test_import_reports_wrong_type(tmp_path: Path) -> None:
    assert _problems(tmp_path, {"steps": "three"}) == {"steps": "wrong_type"}


def test_import_reports_below_and_above_minimum_and_maximum(tmp_path: Path) -> None:
    assert _problems(tmp_path, {"strength": -1.0, "steps": 99}) == {
        "strength": "below_minimum",
        "steps": "above_maximum",
    }


def test_import_reports_not_a_choice(tmp_path: Path) -> None:
    assert _problems(tmp_path, {"mode": "zzz"}) == {"mode": "not_a_choice"}


def test_import_reports_every_problem_together(tmp_path: Path) -> None:
    found = _problems(tmp_path, {"strength": 5.0, "mode": "q", "who": 1, "enabled": 1})
    assert found == {
        "strength": "above_maximum",
        "mode": "not_a_choice",
        "who": "unknown_name",
        "enabled": "wrong_type",
    }


def test_non_finite_numbers_never_reach_validation(tmp_path: Path) -> None:
    source = _file(tmp_path, "nan.json", _set().to_json().replace("0.25", "NaN"))
    with pytest.raises(PresetImportError, match="non-finite") as raised:
        PresetStore(tmp_path / "presets").import_preset(source, SCHEMAS)
    assert raised.value.problems == ()  # the not_finite kind is unreachable through import


def test_import_accepts_nullable_and_partial_sets(tmp_path: Path) -> None:
    source = _import_with(tmp_path, {"cap": None})
    result = PresetStore(tmp_path / "presets").import_preset(source, SCHEMAS)
    assert result.parameter_set.parameters == {"cap": None}


@pytest.mark.parametrize(
    "content",
    ["{nope", "[]", json.dumps({"format_version": 1}), json.dumps({**_set().to_dict(), "x": 1})],
)
def test_import_wraps_unreadable_and_malformed_files(tmp_path: Path, content: str) -> None:
    source = _file(tmp_path, "x.json", content)
    with pytest.raises(PresetImportError):
        PresetStore(tmp_path / "presets").import_preset(source, SCHEMAS)


def test_import_of_a_missing_file_and_a_future_version(tmp_path: Path) -> None:
    store = _store(tmp_path)
    with pytest.raises(PresetImportError):
        store.import_preset(tmp_path / "missing.json", SCHEMAS)
    future = _set().to_dict()
    future["format_version"] = 2
    with pytest.raises(PresetImportError, match="format_version"):
        store.import_preset(_file(tmp_path, "f.json", future), SCHEMAS)
    assert not (tmp_path / "presets").exists()


def test_import_cap_names_the_size_and_the_cap(tmp_path: Path) -> None:
    big = _file(tmp_path, "big.json", " " * (MAX_PRESET_BYTES + 1))
    with pytest.raises(PresetImportError) as raised:
        _store(tmp_path).import_preset(big, SCHEMAS)
    assert str(MAX_PRESET_BYTES + 1) in str(raised.value)
    assert str(MAX_PRESET_BYTES) in str(raised.value)


# --- import naming and provenance ---------------------------------------------------------------


def test_import_names_default_to_the_stem_and_clashes_get_a_counter(tmp_path: Path) -> None:
    store = _store(tmp_path)
    source = _file(tmp_path, "Shared.json", _set().to_dict())
    assert store.import_preset(source, SCHEMAS).name == "Shared"
    assert store.import_preset(source, SCHEMAS).name == "Shared (2)"
    assert store.import_preset(source, SCHEMAS).name == "Shared (3)"
    assert store.import_preset(source, SCHEMAS, name="shared").name == "shared (4)"
    assert store.import_preset(source, SCHEMAS, name="Other").name == "Other"
    assert len(store.list_presets()) == 5


def test_import_with_an_unsafe_name_is_refused(tmp_path: Path) -> None:
    source = _file(tmp_path, "ok.json", _set().to_dict())
    with pytest.raises(PresetError):
        _store(tmp_path).import_preset(source, SCHEMAS, name="a/b")
    with pytest.raises(PresetError):
        _store(tmp_path).import_preset(_file(tmp_path, "CON.json", _set().to_dict()), SCHEMAS)


def test_sidecar_import_drops_provenance_and_says_so(tmp_path: Path) -> None:
    sidecar = _set(source={"path": "dive.mp4", "size": 7}, settings={"encoder": "libx265"})
    source = _file(tmp_path, "dive.json", sidecar.to_dict())
    store = _store(tmp_path)
    result = store.import_preset(source, SCHEMAS)
    assert result.provenance_dropped is True
    assert result.dropped_keys == ("source", "settings")
    assert result.parameter_set.source is None and result.parameter_set.settings is None
    assert result.parameter_set.method == sidecar.method
    assert result.parameter_set.parameters == sidecar.parameters
    assert result.parameter_set.to_dict()["format_version"] == 1
    stored = json.loads(result.path.read_text(encoding="utf-8"))
    assert "source" not in stored and "settings" not in stored


def test_sidecar_with_only_source_names_only_source(tmp_path: Path) -> None:
    source = _file(tmp_path, "s.json", _set(source={"path": "a.jpg"}).to_dict())
    result = _store(tmp_path).import_preset(source, SCHEMAS)
    assert result.dropped_keys == ("source",)
    assert result.provenance_dropped is True
    assert result.parameter_set.source is None and result.parameter_set.settings is None
    only_settings = _file(tmp_path, "t.json", _set(settings={"encoder": "x"}).to_dict())
    assert _store(tmp_path).import_preset(only_settings, SCHEMAS).dropped_keys == ("settings",)


def test_other_unknown_keys_are_still_refused(tmp_path: Path) -> None:
    data = _set(source={"a": 1}).to_dict()
    data["extra"] = 1
    with pytest.raises(PresetImportError, match="unknown keys"):
        _store(tmp_path).import_preset(_file(tmp_path, "e.json", data), SCHEMAS)


# --- starters -----------------------------------------------------------------------------------


def test_starter_presets_are_c3_with_no_explicit_values() -> None:
    starters = starter_presets(CREATED)
    assert list(starters) == ["Snorkel (shallow)", "Scuba (deep)"]
    for parameter_set in starters.values():
        assert parameter_set == ParameterSet("c3", {}, CREATED, __version__)


def test_first_run_installs_the_starters_once(tmp_path: Path) -> None:
    store = _store(tmp_path)
    assert store.install_starters(now=CREATED) == ["Snorkel (shallow)", "Scuba (deep)"]
    assert {e.name for e in store.list_presets()} == {"Snorkel (shallow)", "Scuba (deep)"}
    assert store.install_starters(now=CREATED) == []
    assert store.load("Scuba (deep)").method == "c3"


def test_starters_can_be_renamed_and_deleted_and_are_not_recreated(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.install_starters()
    store.rename("Snorkel (shallow)", "Shallow")
    store.delete("Scuba (deep)")
    assert store.install_starters() == []
    assert [e.name for e in store.list_presets()] == ["Shallow"]
    again = PresetStore(tmp_path / "presets")  # a new process: the marker file remembers
    assert again.install_starters() == []


def test_install_never_overwrites_a_user_preset_of_the_same_name(tmp_path: Path) -> None:
    store = _store(tmp_path)
    mine = ParameterSet("c3", {"steps": 2}, CREATED, "1.0")
    store.save("scuba (deep)", mine)
    assert store.install_starters() == ["Snorkel (shallow)"]
    assert store.load("scuba (deep)") == mine


def test_new_parameter_set_stamps_time_and_version() -> None:
    made = new_parameter_set("c3", {"steps": 2})
    assert made.method == "c3" and made.parameters == {"steps": 2}
    assert made.app_version == __version__
    assert made.created.utcoffset() is not None
    assert new_parameter_set("c3", {}, now=CREATED).created == CREATED


# --- DR-32 at every preset entry point ----------------------------------------------------------

BAD_KEYS = [float("nan"), 1]


@pytest.mark.parametrize("bad_key", BAD_KEYS, ids=repr)
def test_save_refuses_non_string_keys(tmp_path: Path, bad_key: object) -> None:
    store = _store(tmp_path)
    for where in ("parameters", "source", "settings"):
        nested = {"deep": [{bad_key: 1}]}
        kwargs: dict[str, Any] = {"source": None, "settings": None}
        params: dict[str, Any] = {}
        if where == "parameters":
            params = nested
        else:
            kwargs[where] = nested
        with pytest.raises(FormatError, match="non-string key"):
            store.save("k", ParameterSet("c3", params, CREATED, "1", **kwargs))
    assert not (tmp_path / "presets").exists()


@pytest.mark.parametrize("bad_key", BAD_KEYS, ids=repr)
def test_export_refuses_non_string_keys(
    tmp_path: Path, bad_key: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = _store(tmp_path)
    store.save("k", _set())
    poisoned = ParameterSet("c3", {"deep": {bad_key: 1}}, CREATED, "1")  # type: ignore[dict-item]
    monkeypatch.setattr(PresetStore, "load", lambda self, name: poisoned)
    with pytest.raises(FormatError, match="non-string key"):
        store.export_preset("k", tmp_path / "out.json")
    assert not (tmp_path / "out.json").exists()


def _poisoning_registry(bad_key: object) -> Any:
    from clearwater.config import MigrationRegistry

    registry = MigrationRegistry()

    def step(data: dict[str, Any]) -> dict[str, Any]:
        data["format_version"] = 1
        data["parameters"] = {"deep": {bad_key: 1}}
        return data

    registry.register("preset", 0, step)
    return registry


@pytest.mark.parametrize("bad_key", BAD_KEYS, ids=repr)
def test_load_and_list_refuse_keys_a_migration_step_introduces(
    tmp_path: Path, bad_key: object
) -> None:
    folder = tmp_path / "presets"
    folder.mkdir()
    old = _set().to_dict()
    old["format_version"] = 0
    (folder / "old.json").write_text(json.dumps(old), encoding="utf-8")
    store = PresetStore(folder, migrations=_poisoning_registry(bad_key))
    with pytest.raises(PresetError, match="non-string key"):
        store.load("old")
    (entry,) = store.list_presets()
    assert "non-string key" in (entry.error or "")


@pytest.mark.parametrize("bad_key", BAD_KEYS, ids=repr)
def test_import_refuses_keys_a_migration_step_introduces(tmp_path: Path, bad_key: object) -> None:
    old = _set().to_dict()
    old["format_version"] = 0
    source = _file(tmp_path, "old.json", old)
    store = PresetStore(tmp_path / "presets", migrations=_poisoning_registry(bad_key))
    with pytest.raises(PresetImportError, match="non-string key"):
        store.import_preset(source, SCHEMAS)
    assert not (tmp_path / "presets").exists()


def test_migration_fake_step_is_applied_by_load_and_import(tmp_path: Path) -> None:
    from clearwater.config import MigrationRegistry

    registry = MigrationRegistry()

    def step(data: dict[str, Any]) -> dict[str, Any]:
        data["format_version"] = 1
        data["app_version"] = "migrated"
        return data

    registry.register("preset", 0, step)
    old = _set().to_dict()
    old["format_version"] = 0
    source = _file(tmp_path, "old.json", old)
    raw = source.read_bytes()
    store = PresetStore(tmp_path / "presets", migrations=registry)
    result = store.import_preset(source, SCHEMAS)
    assert result.parameter_set.app_version == "migrated"
    assert store.load("old").app_version == "migrated"
    assert source.read_bytes() == raw  # the source is never rewritten
    with pytest.raises(PresetImportError):
        _store(tmp_path).import_preset(source, SCHEMAS)  # no step registered: refused


def test_public_check_helper_names_the_path() -> None:
    with pytest.raises(FormatError, match=r"provenance\.source\[0\]"):
        check_string_keys({"source": [{1: 2}]}, "provenance")


# --- round 1 remediation ------------------------------------------------------------------------


def _upper_suffix_preset(tmp_path: Path, name: str = "Foo", **params: Any) -> Path:
    folder = tmp_path / "presets"
    folder.mkdir(exist_ok=True)
    path = folder / f"{name}.JSON"
    path.write_text(ParameterSet("c3", params, CREATED, "1.2.3").to_json(), encoding="utf-8")
    return path


def test_upper_case_suffix_is_listed_and_loaded(tmp_path: Path) -> None:
    path = _upper_suffix_preset(tmp_path, steps=1)
    store = _store(tmp_path)
    assert [(e.name, e.path.name, e.error) for e in store.list_presets()] == [
        ("Foo", "Foo.JSON", None)
    ]
    assert store.load("Foo").parameters == {"steps": 1}
    assert path.exists()


def test_save_never_overwrites_an_upper_case_suffix_file_unless_told(tmp_path: Path) -> None:
    path = _upper_suffix_preset(tmp_path, steps=1)
    before = path.read_bytes()
    store = _store(tmp_path)
    with pytest.raises(PresetError, match="already exists"):
        store.save("Foo", _set())
    assert path.read_bytes() == before
    written = store.save("foo", _set(), overwrite=True)
    assert written.name == "Foo.JSON"  # the existing spelling is replaced in place
    assert store.load("Foo") == _set()
    assert sorted(p.name.casefold() for p in path.parent.iterdir()) == ["foo.json"]


def test_import_never_overwrites_an_upper_case_suffix_file(tmp_path: Path) -> None:
    path = _upper_suffix_preset(tmp_path, steps=1)
    before = path.read_bytes()
    source = _file(tmp_path, "Foo.json", _set().to_dict())
    result = _store(tmp_path).import_preset(source, SCHEMAS)
    assert result.name == "Foo (2)"
    assert path.read_bytes() == before


def test_starters_never_overwrite_an_upper_case_suffix_file(tmp_path: Path) -> None:
    path = _upper_suffix_preset(tmp_path, "Snorkel (shallow)", steps=1)
    before = path.read_bytes()
    store = _store(tmp_path)
    assert store.install_starters() == ["Scuba (deep)"]
    assert path.read_bytes() == before


def test_rename_delete_and_export_work_on_an_upper_case_suffix_file(tmp_path: Path) -> None:
    _upper_suffix_preset(tmp_path, steps=1)
    store = _store(tmp_path)
    exported = store.export_preset("Foo", tmp_path / "out.json")
    assert ParameterSet.from_json(exported.read_text(encoding="utf-8")).parameters == {"steps": 1}
    store.rename("Foo", "Bar")
    assert [e.name for e in store.list_presets()] == ["Bar"]
    store.delete("Bar")
    assert store.list_presets() == []


def _future_preset(tmp_path: Path, name: str = "Fut") -> tuple[Path, bytes]:
    folder = tmp_path / "presets"
    folder.mkdir(exist_ok=True)
    data = _set().to_dict()
    data["format_version"] = 2
    path = folder / f"{name}.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path, path.read_bytes()


def test_future_version_keeps_its_identity_on_every_store_operation(tmp_path: Path) -> None:
    path, raw = _future_preset(tmp_path)
    store = _store(tmp_path)
    operations = [
        lambda: store.load("Fut"),
        lambda: store.rename("Fut", "Other"),
        lambda: store.delete("Fut"),
        lambda: store.save("Fut", _set(), overwrite=True),
        lambda: store.export_preset("Fut", tmp_path / "out.json"),
    ]
    for operation in operations:
        with pytest.raises(UnsupportedFormatVersionError) as raised:
            operation()
        assert isinstance(raised.value, UnsupportedPresetVersionError)
        assert isinstance(raised.value, PresetError)
        assert "format_version 2" in str(raised.value)
    assert path.read_bytes() == raw
    assert [p.name for p in path.parent.iterdir()] == ["Fut.json"]
    assert not (tmp_path / "out.json").exists()


def test_future_version_import_is_catchable_both_ways(tmp_path: Path) -> None:
    future = _set().to_dict()
    future["format_version"] = 2
    source = _file(tmp_path, "f.json", future)
    raw = source.read_bytes()
    with pytest.raises(UnsupportedFormatVersionError) as raised:
        _store(tmp_path).import_preset(source, SCHEMAS)
    assert isinstance(raised.value, UnsupportedPresetImportError)
    assert isinstance(raised.value, PresetImportError)
    assert raised.value.problems == ()
    assert source.read_bytes() == raw
    assert not (tmp_path / "presets").exists()


def test_list_flags_unsupported_versions_but_not_other_errors(tmp_path: Path) -> None:
    _future_preset(tmp_path)
    (tmp_path / "presets" / "bad.json").write_text("{nope", encoding="utf-8")
    entries = {e.name: e for e in _store(tmp_path).list_presets()}
    assert entries["Fut"].unsupported_version is True and entries["Fut"].error
    assert entries["bad"].unsupported_version is False and entries["bad"].error


def test_ordinary_corruption_is_not_an_unsupported_version(tmp_path: Path) -> None:
    folder = tmp_path / "presets"
    folder.mkdir()
    (folder / "bad.json").write_text("{nope", encoding="utf-8")
    with pytest.raises(PresetError) as raised:
        _store(tmp_path).load("bad")
    assert not isinstance(raised.value, UnsupportedFormatVersionError)


def test_numbering_a_maximum_length_name_truncates_the_base(tmp_path: Path) -> None:
    store = _store(tmp_path)
    base = "x" * 100
    source = _file(tmp_path, "src.json", _set().to_dict())
    assert store.import_preset(source, SCHEMAS, name=base).name == base
    second = store.import_preset(source, SCHEMAS, name=base).name
    third = store.import_preset(source, SCHEMAS, name=base).name
    assert second == "x" * 96 + " (2)" and len(second) == 100
    assert third == "x" * 96 + " (3)"
    assert validate_preset_name(second) == second


def test_truncation_does_not_leave_trailing_space_or_dot(tmp_path: Path) -> None:
    source = _file(tmp_path, "src.json", _set().to_dict())
    for index, cut_character in enumerate((" ", ".")):
        store = PresetStore(tmp_path / f"presets{index}")
        base = "a" * 95 + cut_character + "bbbb"
        assert len(base) == 100
        store.import_preset(source, SCHEMAS, name=base)
        again = store.import_preset(source, SCHEMAS, name=base).name
        assert again == "a" * 95 + " (2)"
        assert validate_preset_name(again) == again


# --- terminating cleanup (round 2) --------------------------------------------------------------


def test_name_byte_cap_leaves_room_for_the_suffix_and_the_temporary_file() -> None:
    emoji = "\U0001f600"  # 4 bytes in UTF-8
    assert MAX_NAME_BYTES == 237
    assert validate_preset_name(emoji * 59 + "x")  # 237 bytes, 60 characters
    for name in (emoji * 60, emoji * 59 + "xy", "\u30d7" * 80):  # 240, 238 and 240 bytes
        with pytest.raises(PresetError, match="bytes"):
            validate_preset_name(name)
    assert validate_preset_name("\u00e9" * 100)  # 200 bytes, 100 characters: within both limits
    with pytest.raises(PresetError, match="characters"):
        validate_preset_name("a" * 101)


def test_the_temporary_file_of_the_longest_name_fits_a_255_byte_component(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: list[str] = []

    def capture(source: Path, target: Path) -> None:
        seen.append(Path(source).name)
        raise OSError("stop before the replace")

    monkeypatch.setattr("clearwater.config.atomic.os.replace", capture)
    name = "\U0001f600" * 59 + "x"  # the longest allowed name: 237 bytes
    assert len(name.encode("utf-8")) == MAX_NAME_BYTES
    with pytest.raises(OSError, match="stop"):
        _store(tmp_path).save(name, _set())
    assert len(seen[0].encode("utf-8")) <= 255
    assert len((name + ".json").encode("utf-8")) <= 255 - 13


def test_numbering_respects_the_byte_cap_for_multibyte_names(tmp_path: Path) -> None:
    store = _store(tmp_path)
    source = _file(tmp_path, "src.json", _set().to_dict())
    base = "\u00e9" * 100  # 200 bytes, within both limits
    assert store.import_preset(source, SCHEMAS, name=base).name == base
    second = store.import_preset(source, SCHEMAS, name=base).name
    assert second == base[:96] + " (2)"
    emoji_base = "\U0001f600" * 59 + "x"  # 237 bytes, 60 characters
    assert store.import_preset(source, SCHEMAS, name=emoji_base).name == emoji_base
    numbered = store.import_preset(source, SCHEMAS, name=emoji_base).name
    assert numbered.endswith(" (2)") and len(numbered.encode("utf-8")) <= MAX_NAME_BYTES
    assert numbered.startswith("\U0001f600" * 58)


def test_list_skips_symbolic_links(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.save("real", _set())
    outside = tmp_path / "outside.json"
    outside.write_text(_set().to_json(), encoding="utf-8")
    try:
        (tmp_path / "presets" / "link.json").symlink_to(outside)
    except OSError:
        pytest.skip("symlinks are not available here")
    assert [e.name for e in store.list_presets()] == ["real"]
    with pytest.raises(PresetError):
        store.load("link")
