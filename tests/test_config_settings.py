"""WP3.15: the settings store (D89, G13), atomic save, migration, value checks, DR-32."""

from __future__ import annotations

import dataclasses
import json
import logging
import subprocess
import sys
import textwrap
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from clearwater.config import (
    SETTINGS_FILE_NAME,
    MigrationRegistry,
    atomic_write_text,
    load_settings,
    save_settings,
)
from clearwater.interfaces import (
    DEFAULT_CACHE_LIMIT_BYTES,
    DEFAULT_OUTPUT_SUFFIX,
    DEFAULT_PNG_BIT_DEPTH,
    DEFAULT_QUALITY_LEVEL,
    DEFAULT_VIDEO_ENCODER,
    FormatError,
    ParameterSet,
    Settings,
    UnsupportedFormatVersionError,
)

CREATED = datetime(2026, 10, 20, 12, 0, 0, tzinfo=UTC)


def _last(**kwargs: Any) -> ParameterSet:
    return ParameterSet("c3", {"strength": 0.5, "enabled": True}, CREATED, "0.0.0", **kwargs)


def _document(**overrides: Any) -> dict[str, Any]:
    data = json.loads(Settings().to_json())
    data.update(overrides)
    return data


def _write(folder: Path, data: object) -> Path:
    path = folder / SETTINGS_FILE_NAME
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


# --- first run and round trip -------------------------------------------------------------------


def test_first_run_equals_the_five_ruled_defaults_field_by_field(tmp_path: Path) -> None:
    settings = load_settings(tmp_path)
    assert settings == Settings()
    assert settings.png_bit_depth == 16 == DEFAULT_PNG_BIT_DEPTH
    assert settings.video_encoder == "auto" == DEFAULT_VIDEO_ENCODER
    assert settings.quality_level == "standard" == DEFAULT_QUALITY_LEVEL
    assert settings.cache_limit_bytes == 20 * 10**9 == DEFAULT_CACHE_LIMIT_BYTES
    assert settings.force_cpu is False
    assert settings.output_folder is None
    assert settings.output_suffix == "_corrected" == DEFAULT_OUTPUT_SUFFIX
    assert settings.ten_bit_for_eight_bit is False
    assert settings.provenance is True
    assert settings.last_parameters is None


def test_first_run_creates_nothing(tmp_path: Path) -> None:
    folder = tmp_path / "not-yet"
    assert load_settings(folder) == Settings()
    assert not folder.exists()


def test_save_then_load_is_equal_and_creates_the_folder(tmp_path: Path) -> None:
    folder = tmp_path / "cfg"
    settings = Settings(
        output_folder=tmp_path / "out",
        output_suffix="_fixed",
        png_bit_depth=8,
        video_encoder="libx265",
        quality_level="high",
        ten_bit_for_eight_bit=True,
        provenance=False,
        cache_limit_bytes=5 * 10**9,
        force_cpu=True,
        last_parameters=_last(),
    )
    path = save_settings(folder, settings)
    assert path == folder / "settings.json"
    assert load_settings(folder) == settings


def test_last_parameters_round_trips_with_provenance_free_form(tmp_path: Path) -> None:
    settings = Settings(last_parameters=_last())
    save_settings(tmp_path, settings)
    loaded = load_settings(tmp_path)
    assert loaded.last_parameters == settings.last_parameters
    assert loaded.last_parameters is not None
    assert loaded.last_parameters.created == CREATED


def test_save_leaves_no_temporary_file(tmp_path: Path) -> None:
    save_settings(tmp_path, Settings())
    assert [p.name for p in tmp_path.iterdir()] == ["settings.json"]


# --- atomic save --------------------------------------------------------------------------------


def test_failed_replace_keeps_the_old_file_and_removes_the_temporary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    save_settings(tmp_path, Settings(force_cpu=True))
    before = (tmp_path / "settings.json").read_bytes()

    def boom(*_args: object) -> None:
        raise OSError("disk full")

    monkeypatch.setattr("clearwater.config.atomic.os.replace", boom)
    with pytest.raises(OSError, match="disk full"):
        save_settings(tmp_path, Settings(force_cpu=False))
    assert (tmp_path / "settings.json").read_bytes() == before
    assert [p.name for p in tmp_path.iterdir()] == ["settings.json"]


def test_failed_write_keeps_the_old_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = tmp_path / "x.txt"
    atomic_write_text(target, "old")

    def boom(_fd: int) -> None:
        raise OSError("sync failed")

    monkeypatch.setattr("clearwater.config.atomic.os.fsync", boom)
    with pytest.raises(OSError, match="sync failed"):
        atomic_write_text(target, "new")
    assert target.read_text(encoding="utf-8") == "old"
    assert [p.name for p in tmp_path.iterdir()] == ["x.txt"]


def test_hard_crash_before_the_replace_leaves_old_file_and_a_temporary(tmp_path: Path) -> None:
    save_settings(tmp_path, Settings(force_cpu=True))
    before = (tmp_path / "settings.json").read_bytes()
    child = textwrap.dedent(
        """
        import os, sys
        from pathlib import Path
        from clearwater.config import atomic, save_settings
        from clearwater.interfaces import Settings
        atomic.os.replace = lambda *a: os._exit(3)
        save_settings(Path(sys.argv[1]), Settings(force_cpu=False))
        """
    )
    done = subprocess.run(
        [sys.executable, "-I", "-c", child, str(tmp_path)], capture_output=True, check=False
    )
    assert done.returncode == 3
    assert (tmp_path / "settings.json").read_bytes() == before
    leftovers = [p.name for p in tmp_path.iterdir() if p.name != "settings.json"]
    assert len(leftovers) == 1 and leftovers[0].endswith(".tmp")
    assert load_settings(tmp_path).force_cpu is True  # the leftover is never read


# --- migration ----------------------------------------------------------------------------------


def _registry() -> MigrationRegistry:
    registry = MigrationRegistry()

    def settings_step(data: dict[str, Any]) -> dict[str, Any]:
        data["format_version"] = 1
        data.setdefault("force_cpu", True)  # a field the fake version 0 lacked
        return data

    def preset_step(data: dict[str, Any]) -> dict[str, Any]:
        data["format_version"] = 1
        data["method"] = "c3"
        return data

    registry.register("settings", 0, settings_step)
    registry.register("preset", 0, preset_step)
    return registry


def test_fake_version_0_settings_are_migrated_in_memory_and_not_rewritten(tmp_path: Path) -> None:
    old = _document(format_version=0)
    del old["force_cpu"]
    path = _write(tmp_path, old)
    raw = path.read_bytes()
    loaded = load_settings(tmp_path, migrations=_registry())
    assert loaded == Settings(force_cpu=True)
    assert path.read_bytes() == raw


def test_nested_last_parameters_are_migrated_with_the_preset_steps(tmp_path: Path) -> None:
    nested = _last().to_dict()
    nested["format_version"] = 0
    del nested["method"]
    _write(tmp_path, _document(last_parameters=nested))
    loaded = load_settings(tmp_path, migrations=_registry())
    assert loaded.last_parameters is not None
    assert loaded.last_parameters.method == "c3"


def test_without_a_step_version_0_is_refused_and_left_alone(tmp_path: Path) -> None:
    path = _write(tmp_path, _document(format_version=0))
    raw = path.read_bytes()
    with pytest.raises(UnsupportedFormatVersionError):
        load_settings(tmp_path)
    assert path.read_bytes() == raw
    assert [p.name for p in tmp_path.iterdir()] == ["settings.json"]


@pytest.mark.parametrize("version", [2, 99])
def test_future_version_is_refused_by_name_and_the_file_is_unchanged(
    tmp_path: Path, version: int
) -> None:
    path = _write(tmp_path, _document(format_version=version))
    raw = path.read_bytes()
    stamp = path.stat().st_mtime_ns
    with pytest.raises(UnsupportedFormatVersionError, match=str(version)):
        load_settings(tmp_path, migrations=_registry())
    assert path.read_bytes() == raw
    assert path.stat().st_mtime_ns == stamp
    assert [p.name for p in tmp_path.iterdir()] == ["settings.json"]


def test_future_nested_version_is_refused_and_left_alone(tmp_path: Path) -> None:
    nested = _last().to_dict()
    nested["format_version"] = 7
    path = _write(tmp_path, _document(last_parameters=nested))
    with pytest.raises(UnsupportedFormatVersionError):
        load_settings(tmp_path)
    assert [p.name for p in tmp_path.iterdir()] == ["settings.json"]
    assert path.exists()


def test_a_step_that_does_not_advance_the_version_is_a_format_error(tmp_path: Path) -> None:
    registry = MigrationRegistry()
    registry.register("settings", 0, lambda data: data)
    _write(tmp_path, _document(format_version=0))
    load_settings(tmp_path, migrations=registry)  # corrupt rule: set aside, defaults
    assert list(tmp_path.glob("settings.json.bad-*"))


def test_duplicate_step_registration_is_refused() -> None:
    registry = _registry()
    with pytest.raises(ValueError, match="registered"):
        registry.register("settings", 0, lambda data: data)


# --- corrupt files ------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "content",
    [
        b"{not json",
        b"[]",
        b"\xff\xfe\x00bad bytes",
        b"",
        json.dumps({"format_version": 1}).encode(),  # missing keys
        json.dumps(_document(extra=1)).encode(),  # unknown key
        json.dumps(_document(png_bit_depth="16")).encode(),  # wrong type
        json.dumps({k: v for k, v in _document().items() if k != "format_version"}).encode(),
        json.dumps(_document(format_version="1")).encode(),
        json.dumps(_document(format_version=True)).encode(),
    ],
)
def test_corrupt_file_is_set_aside_and_defaults_returned(
    tmp_path: Path, content: bytes, caplog: pytest.LogCaptureFixture
) -> None:
    path = tmp_path / "settings.json"
    path.write_bytes(content)
    with caplog.at_level(logging.WARNING, logger="clearwater"):
        loaded = load_settings(tmp_path)
    assert loaded == Settings()
    assert not path.exists()
    aside = list(tmp_path.glob("settings.json.bad-*"))
    assert len(aside) == 1
    assert aside[0].read_bytes() == content
    assert any("moved to" in r.getMessage() for r in caplog.records)


def test_two_corrupt_files_in_a_row_get_distinct_names(tmp_path: Path) -> None:
    for text in ("{a", "{b"):
        (tmp_path / "settings.json").write_text(text, encoding="utf-8")
        load_settings(tmp_path)
    contents = sorted(p.read_text(encoding="utf-8") for p in tmp_path.glob("settings.json.bad-*"))
    assert contents == ["{a", "{b"]


def test_corrupt_file_is_never_overwritten_by_the_next_save(tmp_path: Path) -> None:
    (tmp_path / "settings.json").write_text("{broken", encoding="utf-8")
    assert load_settings(tmp_path) == Settings()
    save_settings(tmp_path, Settings(force_cpu=True))
    aside = list(tmp_path.glob("settings.json.bad-*"))
    assert [p.read_text(encoding="utf-8") for p in aside] == ["{broken"]


def test_failed_rename_still_returns_defaults(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    (tmp_path / "settings.json").write_text("{broken", encoding="utf-8")

    def refuse(self: Path, target: object) -> Path:
        raise PermissionError("locked")

    monkeypatch.setattr(Path, "rename", refuse)
    with caplog.at_level(logging.WARNING, logger="clearwater"):
        assert load_settings(tmp_path) == Settings()
    assert any("could not be set aside" in r.getMessage() for r in caplog.records)
    assert (tmp_path / "settings.json").read_text(encoding="utf-8") == "{broken"


def test_unreadable_file_is_set_aside(tmp_path: Path) -> None:
    (tmp_path / "settings.json").mkdir()  # reading a folder raises an OSError
    assert load_settings(tmp_path) == Settings()
    assert list(tmp_path.glob("settings.json.bad-*"))


# --- value checks (ruling 8) --------------------------------------------------------------------


def test_out_of_range_values_take_their_defaults_with_a_warning(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    _write(
        tmp_path,
        _document(png_bit_depth=12, quality_level="Standard", cache_limit_bytes=-1, force_cpu=True),
    )
    with caplog.at_level(logging.WARNING, logger="clearwater"):
        loaded = load_settings(tmp_path)
    assert loaded == dataclasses.replace(Settings(), force_cpu=True)
    messages = " ".join(r.getMessage() for r in caplog.records)
    for name in ("png_bit_depth", "quality_level", "cache_limit_bytes"):
        assert name in messages


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("png_bit_depth", 8),
        ("png_bit_depth", 16),
        ("quality_level", "high"),
        ("quality_level", "draft"),
        ("cache_limit_bytes", 0),
        ("video_encoder", "some_encoder_not_checked_here"),
    ],
)
def test_in_range_values_are_kept(tmp_path: Path, field: str, value: object) -> None:
    _write(tmp_path, _document(**{field: value}))
    assert getattr(load_settings(tmp_path), field) == value


# --- DR-32 at the settings entry points ---------------------------------------------------------

BAD_KEYS = [float("nan"), 1, True, None, (1, 2)]


@pytest.mark.parametrize("bad_key", BAD_KEYS, ids=repr)
@pytest.mark.parametrize("where", ["parameters", "source", "settings"])
def test_save_settings_refuses_non_string_keys_at_depth(
    tmp_path: Path, bad_key: object, where: str
) -> None:
    nested: dict[Any, Any] = {"deep": [{bad_key: 1}]}
    kwargs: dict[str, Any] = {"source": None, "settings": None}
    params: dict[str, Any] = {"x": 1}
    if where == "parameters":
        params = nested
    else:
        kwargs[where] = nested
    last = ParameterSet("c3", params, CREATED, "0.0.0", **kwargs)
    with pytest.raises(FormatError, match=r"non-string key"):
        save_settings(tmp_path, Settings(last_parameters=last))
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("bad_key", [float("nan"), 1], ids=repr)
def test_load_settings_refuses_keys_a_migration_step_introduces(
    tmp_path: Path, bad_key: object
) -> None:
    registry = MigrationRegistry()

    def step(data: dict[str, Any]) -> dict[str, Any]:
        data["format_version"] = 1
        data["last_parameters"] = {
            **_last().to_dict(),
            "source": {bad_key: 1},
        }
        return data

    registry.register("settings", 0, step)
    _write(tmp_path, _document(format_version=0))
    # a refused key makes the file corrupt: set aside, never silently coerced by json.dumps
    assert load_settings(tmp_path, migrations=registry) == Settings()
    assert list(tmp_path.glob("settings.json.bad-*"))


@pytest.mark.parametrize("bad_version", [1.0, True, "1", None])
def test_a_step_must_return_the_integer_next_version(tmp_path: Path, bad_version: object) -> None:
    from clearwater.config import migrate

    registry = MigrationRegistry()
    registry.register("settings", 0, lambda data: {**data, "format_version": bad_version})
    with pytest.raises(FormatError, match="migration"):
        migrate("settings", {"format_version": 0}, registry)
    _write(tmp_path, _document(format_version=0))
    assert load_settings(tmp_path, migrations=registry) == Settings()  # set aside as corrupt
    assert list(tmp_path.glob("settings.json.bad-*"))


def test_a_huge_integer_or_deep_nesting_sets_the_file_aside(tmp_path: Path) -> None:
    text = json.dumps(_document())
    huge = text.replace('"cache_limit_bytes": 20000000000', '"cache_limit_bytes": ' + "9" * 5000)
    assert "9" * 5000 in huge
    (tmp_path / "settings.json").write_text(huge, encoding="utf-8")
    assert load_settings(tmp_path) == Settings()
    assert len(list(tmp_path.glob("settings.json.bad-*"))) == 1
    nest = "[" * 100000 + "]" * 100000
    deep = text.replace('"force_cpu": false', '"force_cpu": ' + nest)
    (tmp_path / "settings.json").write_text(deep, encoding="utf-8")
    assert load_settings(tmp_path) == Settings()
    assert len(list(tmp_path.glob("settings.json.bad-*"))) == 2


@pytest.mark.parametrize("bad_result", [None, [1], "x", 1])
def test_a_step_returning_a_non_object_is_a_format_error_naming_the_step(
    tmp_path: Path, bad_result: object
) -> None:
    from clearwater.config import migrate

    registry = MigrationRegistry()
    registry.register("settings", 0, lambda data: bad_result)  # type: ignore[arg-type,return-value]
    with pytest.raises(FormatError, match="settings migration from version 0 returned"):
        migrate("settings", {"format_version": 0}, registry)
    _write(tmp_path, _document(format_version=0))
    assert load_settings(tmp_path, migrations=registry) == Settings()  # set aside as corrupt
    assert list(tmp_path.glob("settings.json.bad-*"))
