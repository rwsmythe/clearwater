# WP-T1 -- pytest temp-root footage guard (closes DR-21; DR-9 cosmetic fix)

## The hook

`pytest_configure` in `tests/conftest.py`, `@pytest.hookimpl(tryfirst=True)`. It loads the local
configuration (`tools/local_config.load_local_config`); with no valid configuration it returns
silently (inert, N1). Otherwise it raises `pytest.UsageError` (pytest exit code 4, message on
stderr naming the footage folder and the offending root) when the temp root would damage the
footage folder.

Why it runs in time: pytest creates or clears nothing at configure time. `TempPathFactory` is built
in `_pytest/tmpdir.py:211-220` without touching disk; the removal and creation happen in
`getbasetemp()` (`tmpdir.py:139-`), on the first `tmp_path` request, during a test's setup. The
guard runs before even the factory exists. This is proved by tests, not assumed: the control test
runs the miniature repository WITHOUT the guard and `--basetemp=<fake footage>`, and pytest deletes
the planted files; every refused case with the guard leaves the footage byte-identical.

## The rule

All paths: `os.path.abspath` then `Path.resolve()` (symlinks and junctions followed; `..`, relative
paths, trailing separators and 8.3 names collapse), then `os.path.normcase` (case-insensitive on
Windows). "Inside" = equal to the footage folder or having it as an ancestor.

* `--basetemp` given: refused if inside or equal to the footage folder, or an ANCESTOR of it
  (see Deviations).
* Otherwise `PYTEST_DEBUG_TEMPROOT` if set, else the directory `tempfile.gettempdir()` would pick.
  Because `gettempdir()` probes by creating and deleting a file in each candidate (so calling it
  would write inside a footage folder named by `TMPDIR`), the guard mirrors its candidate list
  without touching disk and refuses if ANY candidate is inside or equal to the footage folder,
  unless `tempfile.tempdir` is already cached (then only that value is checked).

## Pytest lines mirrored (pytest 8.4.2, `.venv/Lib/site-packages/_pytest/`)

* `tmpdir.py:71` -- `Path(os.path.abspath(str(given_basetemp)))`: the basetemp derivation.
* `tmpdir.py:149-152` -- `if basetemp.exists(): rm_rf(basetemp)`: the deletion that makes an
  equal or ancestor basetemp destructive.
* `tmpdir.py:155-156` -- `from_env = os.environ.get("PYTEST_DEBUG_TEMPROOT")`;
  `Path(from_env or tempfile.gettempdir()).resolve()`: the default root.
* `main.py:251-275` (`validate_basetemp`) refuses only a cwd ancestor; it does not protect footage.
* Python `tempfile.py:156` (`_candidate_tempdir_list`) and `:183` (`_get_default_tempdir`): the
  candidate order TMPDIR, TEMP, TMP, OS defaults, cwd, and the write probe.

## Limits

* The guard runs only when `tests/conftest.py` is loaded: pytest arguments (or `testpaths` when
  none are given) at or below `tests/`, from this repository's rootdir. `pytest tools/`, a path
  outside `tests/`, `--noconftest`, `--confcutdir` above `tests/`, or another rootdir does not
  load it. In scope: `uv run pytest`, `pytest tests/...`.
* Out of envelope: other runners, plugins overriding `basetemp`, links changed mid-run.
* A default root that is an ANCESTOR of the footage folder is not refused (pytest only touches
  `pytest-of-<user>/` below it); a footage folder inside `pytest-of-<user>/` is not guarded.
* The guard needs the local configuration; without footage configured there is nothing to guard.

## Tests (`tests/test_conftest_guard.py`, 24 cases, each in a subprocess on a miniature repository
under `tmp_path`; fake footage and working folders; no real path named)

control without guard wipes the footage; `--basetemp` refused (equal, trailing separator, existing
subfolder, missing subfolder, missing nested, `..` inside, relative inside, relative equal,
ancestor); `TMPDIR`/`TEMP`/`TMP` inside and equal; `PYTEST_DEBUG_TEMPROOT` inside; case variant
(Windows); symlink or junction (`--basetemp` and temp variables); passes: `--basetemp` and temp
variables in the working folder, sibling `footage-other`; inert (no file, invalid TOML, relative
path, no keys); DR-9 skip reasons (absent versus not configured).
