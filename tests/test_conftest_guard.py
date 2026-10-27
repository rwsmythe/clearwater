"""Tests of the temp-root footage guard in ``tests/conftest.py`` (WP-T1, DR-21).

Every test builds a MINIATURE repository under ``tmp_path`` (real copies of
``tools/local_config.py`` and ``tests/conftest.py``, a fake footage folder with
planted files, a fake working folder) and runs pytest on it in a subprocess.
The subprocesses never read the real ``clearwater.local.toml`` and no test names the
real footage folder; every path a test sets lies under its own ``tmp_path``. (The
containing pytest session loads the real ``tests/conftest.py``, whose guard reads the
real configuration by design, as for every run of this repository.)
"""

from __future__ import annotations

import getpass
import importlib.util
import json
import os
import subprocess
import sys
from dataclasses import dataclass, replace
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRUBBED_ENV = ("PYTEST_ADDOPTS", "TMP", "TEMP", "TMPDIR", "PYTEST_DEBUG_TEMPROOT")
_PLANTED = {"a.txt": b"alpha\x00bytes", "sub/b.bin": bytes(range(256))}
_BASETEMP_TARGETS = (
    pytest.param("{footage}", id="equal"),
    pytest.param("{footage}" + os.sep, id="trailing-separator"),
    pytest.param("{footage}/sub", id="existing-subfolder"),
    pytest.param("{footage}/not-yet-there", id="missing-subfolder"),
    pytest.param("{footage}/not-yet-there/deeper", id="missing-nested"),
    pytest.param("{footage}/sub/../a-sibling", id="dotdot-inside"),
    pytest.param("../area/footage/sub", id="relative-inside"),
    pytest.param("../area/footage", id="relative-equal"),
    pytest.param("{area}", id="ancestor"),
)
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
_MINI_EXTRA_TESTS = (
    "import pytest\n\n\n"
    "@pytest.fixture(scope='session')\n"
    "def shared(tmp_path_factory):\n"
    "    return tmp_path_factory.mktemp('shared')\n\n\n"
    "def test_tmpdir(tmpdir):\n"
    "    tmpdir.join('y.txt').write('y')\n\n\n"
    "def test_session_factory(shared):\n"
    "    (shared / 'z.txt').write_text('z')\n\n\n"
    "def test_direct_factory(tmp_path_factory):\n"
    "    tmp_path_factory.getbasetemp()\n"
)


@dataclass
class Mini:
    """A miniature repository and its fake folders, all under one ``tmp_path``."""

    root: Path
    area: Path
    footage: Path
    work: Path
    safe_tmp: Path


def _plain(path: Path) -> Path:
    """Drop a Windows extended-length prefix before a drive letter; leave every other form."""
    text = str(path)
    extended = "\\\\?\\"
    if os.name == "nt" and text.startswith(extended) and text[4:5].isalpha() and text[5:6] == ":":
        return Path(text[len(extended) :])
    return path


def _assert_under(tmp_path: Path, *paths: Path | str) -> None:
    """Assert every path, fully resolved, lies in ``tmp_path``.

    A volume-GUID form is resolved like any other; if it does not resolve to a drive
    path under ``tmp_path`` the assertion fails (it never passes unchecked).
    """
    base = _plain(tmp_path.resolve())
    for path in paths:
        resolved = _plain(Path(os.path.abspath(os.path.join(base, os.fspath(path)))).resolve())
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
    (root / "tests" / "test_extra.py").write_text(_MINI_EXTRA_TESTS, encoding="utf-8")
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
    cache: bool = False,
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
        [
            sys.executable,
            "-m",
            "pytest",
            *([] if cache else ["-p", "no:cacheprovider"]),
            "-q",
            "tests",
            *args,
        ],
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


@pytest.mark.parametrize("target", _BASETEMP_TARGETS)
def test_basetemp_in_footage_is_refused(tmp_path: Path, target: str) -> None:
    mini = _build(tmp_path)
    before = _snapshot(mini.footage)
    arg = target.format(footage=mini.footage, area=mini.area)
    result = _run(tmp_path, mini, f"--basetemp={arg}")
    _assert_refused(result, mini, before)


def test_workers_without_the_guard_wipe_the_footage(tmp_path: Path) -> None:
    """Demonstrate the worker run's destructive effect without the guard (w1)."""
    mini = _build(tmp_path, guard=False)
    before = _snapshot(mini.footage)
    result = _run(tmp_path, mini, "-n", "2", f"--basetemp={mini.footage}")
    assert result.returncode == 0, result.stdout + result.stderr
    assert _snapshot(mini.footage) != before
    assert not (mini.footage / "a.txt").exists()
    assert not (mini.footage / "sub" / "b.bin").exists()


@pytest.mark.parametrize("target", _BASETEMP_TARGETS)
def test_workers_basetemp_in_footage_is_refused(tmp_path: Path, target: str) -> None:
    """Refuse worker startup for equal, contained and ancestor temp roots (w2)."""
    mini = _build(tmp_path)
    before = _snapshot(mini.footage)
    arg = target.format(footage=mini.footage, area=mini.area)
    result = _run(tmp_path, mini, "-n", "2", f"--basetemp={arg}")
    _assert_refused(result, mini, before)
    assert not list(mini.footage.rglob("popen-gw*"))


@pytest.mark.parametrize("variable", ["PYTEST_DEBUG_TEMPROOT", "TMPDIR", "TEMP", "TMP", "all"])
def test_workers_temp_environment_in_footage_is_refused(tmp_path: Path, variable: str) -> None:
    """Refuse worker startup when an environment-selected root is unsafe (w3)."""
    mini = _build(tmp_path)
    before = _snapshot(mini.footage)
    inside = str(mini.footage / "sub")
    if variable == "PYTEST_DEBUG_TEMPROOT":
        env = {variable: inside}
    elif variable == "all":
        env = dict.fromkeys(("TMPDIR", "TEMP", "TMP"), inside)
    else:
        env = dict.fromkeys(("TMPDIR", "TEMP", "TMP"), "")
        env[variable] = inside
    result = _run(tmp_path, mini, "-n", "2", env_extra=env)
    _assert_refused(result, mini, before)
    assert not list(mini.footage.rglob("popen-gw*"))


def test_workers_basetemp_in_working_folder_passes(tmp_path: Path) -> None:
    """Observe both workers' safe temp roots and registered guard plugin (w4)."""
    mini = _build(tmp_path)
    before = _snapshot(mini.footage)
    controller_basetemp = mini.work / "bt"
    probe = mini.root / "tests" / "test_workers.py"
    _assert_under(tmp_path, controller_basetemp, probe)
    probe.write_text(
        """import json
import os
from pathlib import Path

import pytest


@pytest.mark.parametrize("slot", [0, 1])
def test_records_worker(tmp_path, pytestconfig, slot):
    worker = os.environ["PYTEST_XDIST_WORKER"]
    guard_path = Path(__file__).with_name("conftest.py").resolve()
    guard_registered = any(
        Path(plugin.__file__).resolve() == guard_path
        for plugin in pytestconfig.pluginmanager.get_plugins()
        if getattr(plugin, "__file__", None)
    )
    record = {
        "worker": worker,
        "basetemp": str(pytestconfig.option.basetemp),
        "guard_registered": guard_registered,
    }
    output = pytestconfig.rootpath.parent / "work" / f"worker-{worker}.json"
    output.write_text(json.dumps(record), encoding="utf-8")
""",
        encoding="utf-8",
    )
    result = _run(
        tmp_path, mini, "-n", "2", f"--basetemp={controller_basetemp}", "-k", "records_worker"
    )
    assert result.returncode == 0, result.stdout + result.stderr
    paths = list(mini.work.glob("worker-gw*.json"))
    _assert_under(tmp_path, *paths)
    records = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
    assert len(records) == 2
    assert {record["worker"] for record in records} == {"gw0", "gw1"}
    for record in records:
        assert record["guard_registered"] is True
        worker_basetemp = Path(record["basetemp"])
        _assert_under(controller_basetemp, worker_basetemp)
        assert worker_basetemp.name == f"popen-{record['worker']}"
        assert _plain(worker_basetemp.resolve()).parent == _plain(controller_basetemp.resolve())
    assert _snapshot(mini.footage) == before


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
        ("absent", "configured but not an existing folder"),
        ("file", "configured but not an existing folder"),
        (None, "not configured"),
    ],
)
def test_footage_skip_reason_distinguishes_absent_from_unconfigured(
    tmp_path: Path, config: str | None, expected: str
) -> None:
    text = None
    if config == "absent":
        text = _toml(tmp_path / "area" / "missing-footage", tmp_path / "work")
    elif config == "file":
        (tmp_path / "area").mkdir()
        (tmp_path / "area" / "a-file").write_text("not a folder", encoding="utf-8")
        text = _toml(tmp_path / "area" / "a-file", tmp_path / "work")
    mini = _build(tmp_path, config=text)
    # The fake footage folder from _build is not the configured one in the absent case.
    result = _run(tmp_path, mini, "-rs")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "SKIPPED" in result.stdout
    assert expected in result.stdout


@pytest.mark.skipif(os.name != "nt", reason="volume GUID paths exist only on Windows")
def test_basetemp_through_a_volume_guid_path_is_refused(tmp_path: Path) -> None:
    import ctypes

    mini = _build(tmp_path)
    drive = mini.footage.resolve().anchor
    buffer = ctypes.create_unicode_buffer(1024)
    found = ctypes.windll.kernel32.GetVolumeNameForVolumeMountPointW(drive, buffer, 1024)  # type: ignore[attr-defined]
    if not found or not buffer.value.startswith("\\\\?\\Volume{"):
        pytest.skip("no volume GUID path for the fake footage's drive")
    guid_root = buffer.value
    relative = str(mini.footage.resolve())[len(drive) :]
    before = _snapshot(mini.footage)
    for tail in ("", "\\sub", "\\not-yet-there"):
        _assert_refused(
            _run(tmp_path, mini, f"--basetemp={guid_root}{relative}{tail}"), mini, before
        )


def test_pytest_of_entry_linked_into_footage_is_refused(tmp_path: Path) -> None:
    mini = _build(tmp_path)
    root = tmp_path / "temproot"
    root.mkdir()
    # Any user name pytest may derive: the guard checks every pytest-of-* entry of the root.
    _make_dir_link(root / "pytest-of-someone", mini.footage)
    before = _snapshot(mini.footage)
    env = {"TEMP": str(root), "TMP": str(root), "TMPDIR": str(root)}
    _assert_refused(_run(tmp_path, mini, env_extra=env), mini, before)
    result = _run(tmp_path, mini, env_extra={"PYTEST_DEBUG_TEMPROOT": str(root)})
    _assert_refused(result, mini, before)


def test_guard_is_inert_when_the_configured_path_is_not_a_usable_path(tmp_path: Path) -> None:
    mini = _build(tmp_path)
    good = _toml(mini.footage / "nul", mini.work).splitlines()[0]
    bad = good.rstrip('"') + '\\u0000x"'  # TOML escape for an embedded NUL
    (mini.root / "clearwater.local.toml").write_text(
        bad + f"\nworking_path = '{mini.work}'\n", encoding="utf-8"
    )
    result = _run(tmp_path, mini, f"--basetemp={mini.work / 'bt'}")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "footage guard" not in result.stdout + result.stderr


# --- Reviewer B round 1 remediation -------------------------------------------------


def _load_guard() -> ModuleType:
    """Import the repository's ``tests/conftest.py`` as a plain module for in-process tests."""
    spec = importlib.util.spec_from_file_location(
        "wp_t1_guard_conftest", REPO_ROOT / "tests" / "conftest.py"
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    "extra",
    [
        [],
        ["-s"],
        # pytest-qt 4.5.0's pytest_configure raises "ValueError: no option named 'capture'"
        # without the capture plugin, so the child also disables pytest-qt (WP3.16 F1 grant).
        ["-p", "no:capture", "-p", "no:pytest-qt"],
        ["--collect-only"],
        ["--setup-plan"],
    ],
    ids=["default", "no-capture-s", "no-capture-plugin", "collect-only", "setup-plan"],
)
def test_refused_before_any_fixture_or_mode_touches_a_temp_folder(
    tmp_path: Path, extra: list[str]
) -> None:
    # The miniature has tmpdir, tmp_path, session tmp_path_factory and direct getbasetemp tests.
    mini = _build(tmp_path)
    before = _snapshot(mini.footage)
    result = _run(tmp_path, mini, f"--basetemp={mini.footage}", *extra)
    _assert_refused(result, mini, before)
    assert sorted(before) == sorted(_snapshot(mini.footage))


def test_cache_clear_with_the_cache_provider_enabled_is_refused_unchanged(tmp_path: Path) -> None:
    mini = _build(tmp_path)
    before = _snapshot(mini.footage)
    result = _run(tmp_path, mini, f"--basetemp={mini.footage}", "--cache-clear", cache=True)
    _assert_refused(result, mini, before)
    # The same run, harmless, still works with the cache provider on.
    result = _run(tmp_path, mini, f"--basetemp={mini.work / 'bt'}", "--cache-clear", cache=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert _snapshot(mini.footage) == before


# "-p no:pytest-qt": pytest-qt 4.5.0's pytest_configure raises "ValueError: no option named
# 'capture'" without the capture plugin (WP3.16 F1 grant).
@pytest.mark.parametrize(
    "extra",
    [["-s"], ["-p", "no:capture", "-p", "no:pytest-qt"]],
    ids=["no-capture-s", "no-capture-plugin"],
)
def test_uncached_tempdir_checks_the_one_root_cpython_would_pick(
    tmp_path: Path, extra: list[str]
) -> None:
    mini = _build(tmp_path)
    before = _snapshot(mini.footage)
    # TMPDIR (first, existing, writable) is safe; TEMP, never chosen, names the fake footage.
    env = {"TEMP": str(mini.footage), "TMP": str(mini.footage)}
    result = _run(tmp_path, mini, *extra, env_extra=env)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "footage guard" not in result.stdout + result.stderr
    assert _snapshot(mini.footage) == before
    # The first candidate names the footage: refused.
    result = _run(tmp_path, mini, *extra, env_extra={"TMPDIR": str(mini.footage)})
    _assert_refused(result, mini, before)
    # Earlier candidate unusable (absent), later one the footage: refused (over-refuse is safe).
    env = {"TMPDIR": str(tmp_path / "no-such-dir"), "TEMP": str(mini.footage)}
    _assert_refused(_run(tmp_path, mini, *extra, env_extra=env), mini, before)


@pytest.mark.skipif(
    os.name != "nt", reason="a differently cased name is the same entry only on NTFS"
)
def test_mixed_case_pytest_of_junction_is_refused(tmp_path: Path) -> None:
    mini = _build(tmp_path)
    root = tmp_path / "temproot"
    root.mkdir()
    _make_dir_link(root / ("PYTEST-OF-" + getpass.getuser().upper()), mini.footage)
    before = _snapshot(mini.footage)
    result = _run(tmp_path, mini, env_extra={"PYTEST_DEBUG_TEMPROOT": str(root)})
    _assert_refused(result, mini, before)


def test_pytests_own_child_decides_when_the_root_cannot_be_listed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    guard = _load_guard()
    footage = tmp_path / "footage"
    footage.mkdir()
    (footage / "keep.txt").write_bytes(b"keep")
    root = tmp_path / "root"
    root.mkdir()
    _make_dir_link(root / f"pytest-of-{guard._pytest_user()}", footage)

    def refuse_listing(self: Path) -> None:
        raise PermissionError("listing denied")

    monkeypatch.setattr(Path, "iterdir", refuse_listing)
    canonical_root, canonical_footage = guard._canonical(root), guard._canonical(footage)
    found = guard._pytest_of_child_in(canonical_root, canonical_footage)
    assert found is not None
    # A listing that fails with no dangerous direct child is not a refusal.
    other = tmp_path / "other"
    other.mkdir()
    assert guard._pytest_of_child_in(guard._canonical(other), canonical_footage) is None


def test_a_check_that_cannot_be_made_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    guard = _load_guard()
    footage = tmp_path / "footage"
    footage.mkdir()
    root = tmp_path / "root"
    root.mkdir()
    original = guard._canonical

    def canonical(path: str | os.PathLike[str]) -> Path:
        if os.path.basename(os.fspath(path)).startswith("pytest-of-"):
            raise PermissionError("cannot resolve")
        return original(path)  # type: ignore[no-any-return]

    monkeypatch.setattr(guard, "_canonical", canonical)
    monkeypatch.setattr(guard, "load_local_config", lambda: SimpleNamespace(footage_path=footage))
    monkeypatch.setenv("PYTEST_DEBUG_TEMPROOT", str(root))
    config = SimpleNamespace(option=SimpleNamespace(basetemp=None))
    with pytest.raises(pytest.UsageError, match="could not be made"):
        guard.pytest_configure(config)


def test_configured_but_missing_footage_still_guards(tmp_path: Path) -> None:
    # Pinned by design (fail safe): a missing folder may be a disconnected drive, so the
    # guard is inert only without a valid configuration, not for a missing folder.
    missing = tmp_path / "area" / "missing-footage"
    (tmp_path / "area").mkdir()
    mini = _build(tmp_path, config=_toml(missing, tmp_path / "work"))
    mini = replace(mini, footage=missing)
    result = _run(tmp_path, mini, f"--basetemp={missing}")
    _assert_refused(result, mini, {})
    assert not missing.exists()


@pytest.mark.skipif(os.name != "nt", reason="volume GUID paths exist only on Windows")
def test_the_safety_helper_resolves_volume_guid_paths(tmp_path: Path) -> None:
    import ctypes

    drive = tmp_path.resolve().anchor
    buffer = ctypes.create_unicode_buffer(1024)
    found = ctypes.windll.kernel32.GetVolumeNameForVolumeMountPointW(drive, buffer, 1024)  # type: ignore[attr-defined]
    if not found or not buffer.value.startswith("\\\\?\\Volume{"):
        pytest.skip("no volume GUID path for the temp drive")
    guid_root = buffer.value
    inside = guid_root + str(tmp_path.resolve())[len(drive) :]
    outside = guid_root + str(tmp_path.resolve().parent)[len(drive) :]
    _assert_under(tmp_path, inside)  # a real path under tmp_path passes
    with pytest.raises(AssertionError):
        _assert_under(tmp_path, outside)  # one above it must not pass as a relative path
