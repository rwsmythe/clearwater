"""Tests of the temp-root footage guard in ``tests/conftest.py`` (WP-T1, DR-21).

Every test builds a MINIATURE repository under ``tmp_path`` (real copies of
``tools/local_config.py`` and ``tests/conftest.py``, a fake footage folder with
planted files, a fake working folder) and runs pytest on it in a subprocess.
Nothing here reads the real ``clearwater.local.toml`` or names the real footage
folder, and every path a test sets lies under its own ``tmp_path``.
"""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass, replace
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRUBBED_ENV = ("PYTEST_ADDOPTS", "TMP", "TEMP", "TMPDIR", "PYTEST_DEBUG_TEMPROOT")
_PLANTED = {"a.txt": b"alpha\x00bytes", "sub/b.bin": bytes(range(256))}
_MINI_PYPROJECT = (
    "[tool.pytest.ini_options]\n"
    'pythonpath = ["tools"]\n'
    'markers = ["footage: needs the footage folder"]\n'
)
_MINI_TEST = (
    "import pytest\n\n\n"
    "def test_uses_tmp_path(tmp_path):\n"
    "    (tmp_path / 'x.txt').write_text('x')\n\n\n"
    "@pytest.mark.footage\n"
    "def test_needs_footage():\n"
    "    pass\n"
)


@dataclass
class Mini:
    """A miniature repository and its fake folders, all under one ``tmp_path``."""

    root: Path
    area: Path
    footage: Path
    work: Path
    safe_tmp: Path


def _assert_under(tmp_path: Path, *paths: Path | str) -> None:
    base = tmp_path.resolve()
    for path in paths:
        text = os.fspath(path)
        # An extended-length prefix (a deliberate test input) is the same place; drop it to compare.
        text = text.removeprefix("\\\\?\\") if os.name == "nt" else text
        resolved = Path(os.path.abspath(os.path.join(base, text))).resolve()
        assert resolved == base or base in resolved.parents, f"{path} escapes {tmp_path}"


def _toml(footage: Path, work: Path) -> str:
    # TOML basic strings, escaped, so any legal Windows path (apostrophes, backslashes) survives.
    def quote(path: Path) -> str:
        return '"' + str(path).replace("\\", "\\\\").replace('"', '\\"') + '"'

    return f"footage_path = {quote(footage)}\nworking_path = {quote(work)}\n"


def _build(tmp_path: Path, *, config: str | None = "fake", guard: bool = True) -> Mini:
    root = tmp_path / "mini"
    area = tmp_path / "area"
    footage = area / "footage"
    work = tmp_path / "work"
    safe_tmp = tmp_path / "safe-tmp"
    for folder in (root / "tools", root / "tests", footage / "sub", work, safe_tmp):
        folder.mkdir(parents=True)
    (area / "footage-other").mkdir()
    for rel, data in _PLANTED.items():
        (footage / rel).write_bytes(data)
    (root / "tools" / "local_config.py").write_bytes(
        (REPO_ROOT / "tools" / "local_config.py").read_bytes()
    )
    conftest = root / "tests" / "conftest.py"
    if guard:
        conftest.write_bytes((REPO_ROOT / "tests" / "conftest.py").read_bytes())
    else:
        conftest.write_text("", encoding="utf-8")
    (root / "pyproject.toml").write_text(_MINI_PYPROJECT, encoding="utf-8")
    (root / "tests" / "test_trivial.py").write_text(_MINI_TEST, encoding="utf-8")
    if config == "fake":
        (root / "clearwater.local.toml").write_text(_toml(footage, work), encoding="utf-8")
    elif config is not None:
        (root / "clearwater.local.toml").write_text(config, encoding="utf-8")
    _assert_under(tmp_path, root, footage, work, safe_tmp)
    return Mini(root, area, footage, work, safe_tmp)


def _snapshot(footage: Path) -> dict[str, bytes | None]:
    """Map every entry under ``footage`` to its bytes (None for a folder)."""
    entries: dict[str, bytes | None] = {}
    for path in sorted(footage.rglob("*")):
        entries[path.relative_to(footage).as_posix()] = (
            path.read_bytes() if path.is_file() else None
        )
    return entries


def _run(
    tmp_path: Path,
    mini: Mini,
    *args: str,
    env_extra: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    env = {k: v for k, v in os.environ.items() if k not in _SCRUBBED_ENV}
    # Keep the miniature's own default temp root away from the machine's.
    env.update(TMP=str(mini.safe_tmp), TEMP=str(mini.safe_tmp), TMPDIR=str(mini.safe_tmp))
    env.update(env_extra or {})
    _assert_under(tmp_path, *(env[k] for k in _SCRUBBED_ENV if k in env))
    for arg in args:
        if arg.startswith("--basetemp="):
            _assert_under(tmp_path, mini.root / arg.partition("=")[2])
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-p", "no:cacheprovider", "-q", "tests", *args],
        cwd=mini.root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def _assert_refused(
    result: subprocess.CompletedProcess[str], mini: Mini, before: dict[str, bytes | None]
) -> None:
    assert result.returncode == 4, result.stdout + result.stderr
    assert "footage guard" in result.stderr
    assert str(mini.footage) in result.stderr
    assert _snapshot(mini.footage) == before


def test_control_without_the_guard_pytest_wipes_the_footage(tmp_path: Path) -> None:
    mini = _build(tmp_path, guard=False)
    result = _run(tmp_path, mini, f"--basetemp={mini.footage}")
    assert result.returncode == 0, result.stdout + result.stderr
    # The harm is real without the guard, so the refusals below prove something.
    assert not (mini.footage / "a.txt").exists()
    assert not (mini.footage / "sub" / "b.bin").exists()


@pytest.mark.parametrize(
    "target",
    [
        "{footage}",
        "{footage}" + os.sep,
        "{footage}/sub",
        "{footage}/not-yet-there",
        "{footage}/not-yet-there/deeper",
        "{footage}/sub/../a-sibling",
        "../area/footage/sub",
        "../area/footage",
        "{area}",
    ],
    ids=[
        "equal",
        "trailing-separator",
        "existing-subfolder",
        "missing-subfolder",
        "missing-nested",
        "dotdot-inside",
        "relative-inside",
        "relative-equal",
        "ancestor",
    ],
)
def test_basetemp_in_footage_is_refused(tmp_path: Path, target: str) -> None:
    mini = _build(tmp_path)
    before = _snapshot(mini.footage)
    arg = target.format(footage=mini.footage, area=mini.area)
    result = _run(tmp_path, mini, f"--basetemp={arg}")
    _assert_refused(result, mini, before)


def test_temp_variables_in_footage_are_refused(tmp_path: Path) -> None:
    mini = _build(tmp_path)
    before = _snapshot(mini.footage)
    inside = str(mini.footage / "sub")
    env = {"TEMP": inside, "TMP": inside, "TMPDIR": inside}
    _assert_refused(_run(tmp_path, mini, env_extra=env), mini, before)
    # Each variable alone decides the root when the ones tempfile reads before it
    # are empty (order: TMPDIR, TEMP, TMP).
    _assert_refused(_run(tmp_path, mini, env_extra={"TMPDIR": inside}), mini, before)
    env = {"TMPDIR": "", "TEMP": inside}
    _assert_refused(_run(tmp_path, mini, env_extra=env), mini, before)
    env = {"TMPDIR": "", "TEMP": "", "TMP": inside}
    _assert_refused(_run(tmp_path, mini, env_extra=env), mini, before)


def test_temp_variable_equal_to_footage_is_refused(tmp_path: Path) -> None:
    mini = _build(tmp_path)
    before = _snapshot(mini.footage)
    env = {"TEMP": str(mini.footage), "TMP": str(mini.footage), "TMPDIR": str(mini.footage)}
    _assert_refused(_run(tmp_path, mini, env_extra=env), mini, before)


def test_debug_temproot_in_footage_is_refused(tmp_path: Path) -> None:
    mini = _build(tmp_path)
    before = _snapshot(mini.footage)
    for value in (str(mini.footage), str(mini.footage / "sub"), str(mini.footage / "nope")):
        result = _run(tmp_path, mini, env_extra={"PYTEST_DEBUG_TEMPROOT": value})
        _assert_refused(result, mini, before)


@pytest.mark.skipif(os.name != "nt", reason="letter case matters only on case-insensitive Windows")
def test_basetemp_differing_only_in_case_is_refused(tmp_path: Path) -> None:
    mini = _build(tmp_path)
    before = _snapshot(mini.footage)
    for variant in (str(mini.footage).swapcase(), str(mini.footage / "sub").upper()):
        _assert_refused(_run(tmp_path, mini, f"--basetemp={variant}"), mini, before)


@pytest.mark.skipif(os.name != "nt", reason="extended-length prefixes exist only on Windows")
def test_basetemp_with_extended_length_prefix_is_refused(tmp_path: Path) -> None:
    mini = _build(tmp_path)
    before = _snapshot(mini.footage)
    for tail in ("", "\\sub", "\\not-yet-there"):
        variant = "\\\\?\\" + str(mini.footage) + tail
        _assert_refused(_run(tmp_path, mini, f"--basetemp={variant}"), mini, before)


@pytest.mark.skipif(os.name != "nt", reason="8.3 short names exist only on Windows")
def test_basetemp_through_a_short_name_is_refused(tmp_path: Path) -> None:
    import ctypes

    mini = _build(tmp_path)
    buffer = ctypes.create_unicode_buffer(1024)
    ctypes.windll.kernel32.GetShortPathNameW(str(mini.footage / "sub"), buffer, 1024)  # type: ignore[attr-defined]
    short = buffer.value
    if not short or short.lower() == str(mini.footage / "sub").lower():
        pytest.skip("this volume has no 8.3 short name for the fake footage path")
    before = _snapshot(mini.footage)
    _assert_refused(_run(tmp_path, mini, f"--basetemp={short}"), mini, before)


def test_default_root_whose_pytest_of_folder_is_the_footage_is_refused(tmp_path: Path) -> None:
    mini = _build(tmp_path)
    root = tmp_path / "temproot"
    footage = root / "pytest-of-someone"
    (footage / "sub").mkdir(parents=True)
    (footage / "keep.txt").write_bytes(b"keep")
    (mini.root / "clearwater.local.toml").write_text(_toml(footage, mini.work), encoding="utf-8")
    mini = replace(mini, footage=footage)
    before = _snapshot(footage)
    env = {"TEMP": str(root), "TMP": str(root), "TMPDIR": str(root)}
    _assert_refused(_run(tmp_path, mini, env_extra=env), mini, before)
    result = _run(tmp_path, mini, env_extra={"PYTEST_DEBUG_TEMPROOT": str(root)})
    _assert_refused(result, mini, before)


def _make_dir_link(link: Path, target: Path) -> None:
    """Create a symlink to ``target``; on Windows without the right, a junction."""
    try:
        os.symlink(target, link, target_is_directory=True)
        return
    except OSError as exc:
        if os.name != "nt":
            pytest.skip(f"this OS refuses to create a symlink here: {exc}")
    made = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(link), str(target)],
        capture_output=True,
        text=True,
        check=False,
    )
    if made.returncode != 0:
        pytest.skip(f"this OS refuses both symlink and junction creation: {made.stdout}")


def test_basetemp_through_a_link_is_refused(tmp_path: Path) -> None:
    mini = _build(tmp_path)
    link = tmp_path / "link-to-footage"
    _make_dir_link(link, mini.footage)
    _assert_under(tmp_path, link)
    before = _snapshot(mini.footage)
    for variant in (link, link / "sub", link / "not-yet-there"):
        _assert_refused(_run(tmp_path, mini, f"--basetemp={variant}"), mini, before)
    # A link used as the default temp root is followed too.
    env = {"TEMP": str(link), "TMP": str(link), "TMPDIR": str(link)}
    _assert_refused(_run(tmp_path, mini, env_extra=env), mini, before)


def test_basetemp_in_working_folder_passes(tmp_path: Path) -> None:
    mini = _build(tmp_path)
    before = _snapshot(mini.footage)
    result = _run(tmp_path, mini, f"--basetemp={mini.work / 'bt'}")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "footage guard" not in result.stdout + result.stderr
    assert _snapshot(mini.footage) == before


def test_temp_variables_in_working_folder_pass(tmp_path: Path) -> None:
    mini = _build(tmp_path)
    before = _snapshot(mini.footage)
    inside = str(mini.work)
    env = {"TEMP": inside, "TMP": inside, "TMPDIR": inside}
    result = _run(tmp_path, mini, env_extra=env)
    assert result.returncode == 0, result.stdout + result.stderr
    result = _run(tmp_path, mini, env_extra={"PYTEST_DEBUG_TEMPROOT": inside})
    assert result.returncode == 0, result.stdout + result.stderr
    assert _snapshot(mini.footage) == before


def test_sibling_with_footage_name_prefix_passes(tmp_path: Path) -> None:
    mini = _build(tmp_path)
    before = _snapshot(mini.footage)
    other = mini.area / "footage-other"
    assert str(other).startswith(str(mini.footage))
    result = _run(tmp_path, mini, f"--basetemp={other / 'bt'}")
    assert result.returncode == 0, result.stdout + result.stderr
    result = _run(tmp_path, mini, env_extra={"PYTEST_DEBUG_TEMPROOT": str(other)})
    assert result.returncode == 0, result.stdout + result.stderr
    assert _snapshot(mini.footage) == before


@pytest.mark.parametrize(
    "config",
    [None, "this is = not [valid toml", "footage_path = 'relative'\nworking_path = 'x'\n", ""],
    ids=["no-file", "invalid-toml", "relative-path", "no-keys"],
)
def test_guard_is_inert_without_usable_configuration(tmp_path: Path, config: str | None) -> None:
    mini = _build(tmp_path, config=config)
    # Even a basetemp that would be inside the fake footage folder passes: no config, no guard.
    result = _run(tmp_path, mini, f"--basetemp={mini.footage / 'bt'}")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "footage guard" not in result.stdout + result.stderr


@pytest.mark.parametrize(
    ("config", "expected"),
    [
        ("absent", "configured but absent"),
        (None, "not configured"),
    ],
)
def test_footage_skip_reason_distinguishes_absent_from_unconfigured(
    tmp_path: Path, config: str | None, expected: str
) -> None:
    text = None
    if config == "absent":
        text = _toml(tmp_path / "area" / "missing-footage", tmp_path / "work")
    mini = _build(tmp_path, config=text)
    # The fake footage folder from _build is not the configured one in the absent case.
    result = _run(tmp_path, mini, "-rs")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "SKIPPED" in result.stdout
    assert expected in result.stdout
