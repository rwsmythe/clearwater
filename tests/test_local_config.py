from __future__ import annotations

from pathlib import Path

import pytest

from local_config import (
    TEMPLATE_NAME,
    LocalConfigError,
    default_config_path,
    footage_available,
    load_local_config,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


def _write(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def _toml(footage: Path | str, working: Path | str) -> str:
    # TOML literal strings keep Windows backslashes intact.
    return f"footage_path = '{footage}'\nworking_path = '{working}'\n"


def test_template_parses_once_placeholders_replaced(tmp_path: Path) -> None:
    template = (REPO_ROOT / TEMPLATE_NAME).read_text(encoding="utf-8")
    footage, working = tmp_path / "footage", tmp_path / "work"
    text = template.replace("REPLACE-WITH-ABSOLUTE-PATH-TO-FOOTAGE-FOLDER", footage.as_posix())
    text = text.replace("REPLACE-WITH-ABSOLUTE-PATH-TO-WORKING-FOLDER", working.as_posix())
    assert "REPLACE-WITH" not in text
    config = load_local_config(_write(tmp_path / "cfg.toml", text))
    assert config.footage_path == footage
    assert config.working_path == working


def test_template_placeholders_are_rejected_as_relative(tmp_path: Path) -> None:
    template = (REPO_ROOT / TEMPLATE_NAME).read_text(encoding="utf-8")
    with pytest.raises(LocalConfigError, match=TEMPLATE_NAME):
        load_local_config(_write(tmp_path / "cfg.toml", template))


def test_missing_file(tmp_path: Path) -> None:
    with pytest.raises(LocalConfigError, match=TEMPLATE_NAME):
        load_local_config(tmp_path / "absent.toml")


def test_invalid_toml(tmp_path: Path) -> None:
    with pytest.raises(LocalConfigError, match=TEMPLATE_NAME):
        load_local_config(_write(tmp_path / "cfg.toml", "footage_path = = ["))


@pytest.mark.parametrize("missing", ["footage_path", "working_path"])
def test_missing_key(tmp_path: Path, missing: str) -> None:
    lines = _toml(tmp_path / "f", tmp_path / "w").splitlines()
    text = "\n".join(line for line in lines if not line.startswith(missing))
    with pytest.raises(LocalConfigError, match=TEMPLATE_NAME):
        load_local_config(_write(tmp_path / "cfg.toml", text))


def test_non_string_value(tmp_path: Path) -> None:
    text = f"footage_path = 5\nworking_path = '{tmp_path / 'w'}'\n"
    with pytest.raises(LocalConfigError, match=TEMPLATE_NAME):
        load_local_config(_write(tmp_path / "cfg.toml", text))


def test_relative_path(tmp_path: Path) -> None:
    text = _toml("footage", tmp_path / "w")
    with pytest.raises(LocalConfigError, match=TEMPLATE_NAME):
        load_local_config(_write(tmp_path / "cfg.toml", text))


@pytest.mark.parametrize(
    "suffix", ["", "work", "work/deeper", "../footage/x", "work/", "a/../work"]
)
def test_working_inside_footage(tmp_path: Path, suffix: str) -> None:
    footage = tmp_path / "footage"
    working = footage / suffix if suffix else footage
    with pytest.raises(LocalConfigError, match=TEMPLATE_NAME):
        load_local_config(_write(tmp_path / "cfg.toml", _toml(footage, working)))


def test_sibling_with_common_prefix_is_allowed(tmp_path: Path) -> None:
    config = load_local_config(
        _write(tmp_path / "cfg.toml", _toml(tmp_path / "footage", tmp_path / "footage-work"))
    )
    assert config.working_path == tmp_path / "footage-work"


def test_default_config_path_is_repo_root() -> None:
    assert default_config_path() == REPO_ROOT / "clearwater.local.toml"


def test_footage_available_missing_config(tmp_path: Path) -> None:
    assert footage_available(tmp_path / "absent.toml") is False


def test_footage_available_missing_directory(tmp_path: Path) -> None:
    cfg = _write(tmp_path / "cfg.toml", _toml(tmp_path / "footage", tmp_path / "work"))
    assert footage_available(cfg) is False


def test_footage_available_existing_directory(tmp_path: Path) -> None:
    (tmp_path / "footage").mkdir()
    cfg = _write(tmp_path / "cfg.toml", _toml(tmp_path / "footage", tmp_path / "work"))
    assert footage_available(cfg) is True
