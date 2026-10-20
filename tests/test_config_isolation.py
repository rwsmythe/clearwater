"""WP3.15: nothing in config resolves or writes the real app-data folder; keys helper behaviour."""

from __future__ import annotations

import ast
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

import clearwater.config as config
from clearwater.config import paths
from clearwater.config.keys import check_parameter_set_keys, check_string_keys
from clearwater.interfaces import FormatError, Parameter, ParameterSet, Settings

CREATED = datetime(2026, 10, 20, tzinfo=UTC)
CONFIG_DIR = Path(config.__file__).parent


def test_every_store_operation_runs_without_resolving_the_real_locations(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def poisoned(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("the real app-data location was resolved")

    monkeypatch.setattr(paths, "app_locations", poisoned)
    monkeypatch.setattr(config, "app_locations", poisoned)
    monkeypatch.setattr(Path, "home", poisoned)
    for variable in ("APPDATA", "LOCALAPPDATA", "XDG_CONFIG_HOME", "XDG_CACHE_HOME", "HOME"):
        monkeypatch.delenv(variable, raising=False)

    config.save_settings(
        tmp_path / "cfg", Settings(last_parameters=ParameterSet("c3", {}, CREATED, "1"))
    )
    config.load_settings(tmp_path / "cfg")
    store = config.PresetStore(tmp_path / "presets")
    store.install_starters()
    store.save("a", ParameterSet("c3", {}, CREATED, "1"))
    store.rename("a", "b")
    source = store.export_preset("b", tmp_path / "b.json")
    schema = {"c3": (Parameter("x", "int", 1, 0, 5, None, "basic", "X", "h", 1),)}
    store.import_preset(source, schema)
    store.delete("b")
    config.configure_logging(tmp_path / "logs")
    config.shutdown_logging()
    assert {p.name for p in tmp_path.iterdir()} == {"cfg", "presets", "b.json", "logs"}


def test_only_paths_py_touches_the_environment_or_the_home_folder() -> None:
    forbidden_names = {"environ", "getenv", "expanduser", "home", "platform"}
    for source in sorted(CONFIG_DIR.glob("*.py")):
        if source.name == "paths.py":
            continue
        tree = ast.parse(source.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr in forbidden_names:
                pytest.fail(f"{source.name}:{node.lineno} uses .{node.attr}")
            if isinstance(node, ast.Name) and node.id in {"environ", "getenv"}:
                pytest.fail(f"{source.name}:{node.lineno} uses {node.id}")
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                for needle in ("APPDATA", "XDG_", "AppData"):
                    if needle in node.value:
                        pytest.fail(f"{source.name}:{node.lineno} names {needle}")


# --- the DR-32 helper ---------------------------------------------------------------------------


@pytest.mark.parametrize("bad_key", [float("nan"), 1, 2.5, True, None, b"k", (1,)], ids=repr)
def test_helper_refuses_every_non_string_key_type(bad_key: object) -> None:
    with pytest.raises(FormatError, match="non-string key"):
        check_string_keys({"a": {"b": [{bad_key: 1}]}}, "provenance")


def test_helper_names_the_path_and_the_key_type() -> None:
    with pytest.raises(FormatError) as raised:
        check_string_keys({"source": {"probe": {1: "x"}}}, "provenance")
    message = str(raised.value)
    assert "provenance.source.probe" in message and "int" in message and "1" in message


def test_helper_accepts_json_native_values() -> None:
    value: Any = {"a": [1, 2.5, "s", None, True, {"b": (1, 2)}], "c": {}}
    check_string_keys(value)
    json.dumps(value)


def test_helper_handles_non_dict_mappings_and_reuse_of_a_shared_child() -> None:
    from types import MappingProxyType

    shared = {"k": 1}
    check_string_keys({"x": shared, "y": shared, "z": MappingProxyType({"k": shared})})
    with pytest.raises(FormatError, match="non-string key"):
        check_string_keys(MappingProxyType({1: 1}))


def test_helper_refuses_a_reference_cycle() -> None:
    loop: dict[str, Any] = {}
    loop["me"] = [loop]
    with pytest.raises(FormatError, match="cycle"):
        check_string_keys(loop, "provenance")


def test_parameter_set_helper_covers_the_three_mappings() -> None:
    check_parameter_set_keys(ParameterSet("c3", {"a": 1}, CREATED, "1", {"p": 1}, {"q": 2}))
    for kwargs in (
        {"source": {1: 1}},
        {"settings": {float("nan"): 1}},
    ):
        with pytest.raises(FormatError, match="non-string key"):
            check_parameter_set_keys(ParameterSet("c3", {}, CREATED, "1", **kwargs))
    with pytest.raises(FormatError, match="non-string key"):
        check_parameter_set_keys(ParameterSet("c3", {1: 1}, CREATED, "1"))  # type: ignore[dict-item]
