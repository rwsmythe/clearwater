# WP-T1 -- pytest temp-root footage guard (closes DR-21; DR-9 cosmetic fix)

## The hook

`pytest_configure` in `tests/conftest.py`, `@pytest.hookimpl(tryfirst=True)`. It loads the local
configuration (`tools/local_config.load_local_config`); with no valid configuration (none, an
invalid one, no footage key) it returns silently (inert, N1). Otherwise it raises
`pytest.UsageError` (pytest exit code 4, message on stderr naming the footage folder and the
offending root) when the temp root would damage the footage folder. If a check it needs cannot be
made (an error resolving the temp root or pytest's own `pytest-of-<user>` folder) it refuses and
says so. A configured footage folder that does not exist is NOT inert (it may be a disconnected
drive): the guard stays active (fail safe); a test pins it.

## Scope of the guarantee (claim 1, CHARC ruling, DR-22)

The guard refuses before pytest creates or clears any temporary FOLDER; not the TEMP-variable file
writes. Pytest starts output capture, and `tempfile` probes for a writable directory, BEFORE it loads
any conftest. With `TMPDIR`/`TEMP`/`TMP` inside the footage folder (or with `TMP` there and no usable
earlier candidate, alongside `--basetemp` or `PYTEST_DEBUG_TEMPROOT`) [erratum at the gate], pytest creates and removes
short-lived, randomly named files there before the guard refuses. Measured with an audit hook on a
fake footage folder: one probe file created and removed, two capture temp files opened; nothing
existing touched, the planted files byte-identical. Closing it needs an early `-p` plugin (a
`pyproject.toml` addopts change plus a file under `tools/`), outside this package.

Ordering: the factory is built in `_pytest/tmpdir.py:211-220` without touching disk; removal and
creation happen in `getbasetemp()` (`tmpdir.py:139-`), on the first `tmp_path`/`tmpdir`/factory
request. The guard runs before even the factory exists. The cache provider's `--cache-clear` clears
the subfolders of the configured `cache_dir` (`.pytest_cache` by default; an explicit
`-o cache_dir=<footage>` is NOT guarded, DR-22) [erratum at the gate]; it runs after the guard (a conftest registers after the built-in
plugins and later-registered hooks run first). Tests pin both: the control runs the miniature
WITHOUT the guard and `--basetemp=<fake footage>` and pytest deletes the planted files; with the
guard, the `tmp_path`, `tmpdir`, session `tmp_path_factory` and direct `getbasetemp()` tests, `-s`,
`-p no:capture`, `--collect-only`, `--setup-plan` and `--cache-clear` (cache provider enabled) are
all refused with the footage byte-identical.

## The rule

All paths: `os.path.abspath` then `Path.resolve()` (symlinks and junctions followed; `..`, relative
paths, trailing separators and 8.3 names collapse), a Windows extended-length prefix before a drive
letter (the `\\?\C:` form, which `resolve()` keeps when the input has it) stripped, then
`os.path.normcase` (case-insensitive on Windows). "Inside" = equal to the footage folder or having
it as an ancestor, OR any existing ancestor of the candidate is the same file (`os.path.samefile`)
as the footage folder.

* `--basetemp` given: refused if inside or equal to the footage folder, or an ANCESTOR of it
  (pytest removes the whole tree).
* Otherwise `PYTEST_DEBUG_TEMPROOT` if set, else the ONE directory `tempfile.gettempdir()` would
  pick. `gettempdir()` probes by creating and deleting a file in each candidate, so calling it
  would write inside a footage folder named by `TMPDIR`. The guard mirrors the candidate list
  without touching disk and approximates the probe by "an existing directory `os.access` accepts
  for writing"; it checks every candidate up to and including that one (candidates before it are
  over-refused). [Erratum at the gate: on Windows `os.access` is not an ACL-accurate create
  probe, so a candidate it accepts but CPython's real write probe rejects can make the guard
  stop one candidate early and miss the root CPython then picks; DR-22.] If `tempfile.tempdir` is already cached (the normal case, because
  capture caches it) only that value is checked. With capture off (`-s`) a safe `TMPDIR` plus
  `TEMP=<footage>` passes; `TMPDIR=<footage>` is refused.
* A default root is also refused when the footage folder lies in `<root>/pytest-of-*`, or when
  pytest's own child (`pytest-of-<user>`, `pytest-of-unknown`, built exactly as pytest builds it)
  is, or links into, the footage folder. Those two children are checked directly, whether or not
  the root can be listed and whatever their case; other `pytest-of-*` entries are found by
  listing, best effort (`normcase` on the name; a listing error is not a refusal).

## Pytest lines mirrored (pytest 8.4.2, `.venv/Lib/site-packages/_pytest/`)

* `tmpdir.py:71` -- `Path(os.path.abspath(str(given_basetemp)))`: the basetemp derivation.
* `tmpdir.py:149-152` -- `if basetemp.exists(): rm_rf(basetemp)`: the deletion.
* `tmpdir.py:155-156` -- `PYTEST_DEBUG_TEMPROOT` or `tempfile.gettempdir()`, then `.resolve()`.
* `tmpdir.py:157,160,165` and `get_user` (`:199-206`) -- the `pytest-of-<user>` /
  `pytest-of-unknown` child names.
* `main.py:251-275` (`validate_basetemp`) refuses only a cwd ancestor; it does not protect footage.
* Python `tempfile.py:156` (`_candidate_tempdir_list`) and `:183` (`_get_default_tempdir`): the
  candidate order TMPDIR, TEMP, TMP, OS defaults, cwd, and the write probe.

## When the guard loads, and other limits

* **Accepted at the gate after Reviewer B's re-run (orchestrator, DR-22).** The guard does not
  cover these deliberately constructed states: a temp candidate whose ACL `os.access` misreads
  (above); a configured footage path reached through a junction whose resolution is denied
  (`Path.resolve()` is non-strict and degrades silently, and `samefile` errors are ignored); a
  footage folder placed inside `<root>/pytest-of-<user>/` under an aliased (volume-GUID) temp
  root; `--cache-clear` with `-o cache_dir=<footage>`. A stale `pytest-of-unknown` link into the
  footage folder over-refuses. See `docs/proofs/wp-t1-accept.md`.

* The guard runs only when `tests/conftest.py` is loaded. Pytest 8.4.2
  (`config/__init__.py`, `_set_initial_conftests` ~548-596, `_try_load_conftest`, `_is_in_confcutdir`
  ~598, `--noconftest` ~646) loads, for every existing path argument (`testpaths` when none is
  given), the conftest files found at or above it, up to `--confcutdir` (default the ini file's
  folder), and those in the `test*` subfolders of an argument that is a folder. So `pytest`,
  `pytest tests`, `pytest tests/x.py` and `pytest .` at the repository root load it; `pytest tools`
  does not. `--noconftest` suppresses it, and so does a `--confcutdir` below `tests/`; `--rootdir`
  alone and `-p no:conftest` do not.
* Out of envelope (banked, DR-22): other runners; plugins overriding `basetemp`; links changed
  mid-run; `-c <other ini>` without `pythonpath = ["tools"]` (the conftest's own import of
  `local_config` then fails, which is a loud failure rather than silent inertness).
* A configured footage path on a MAPPED or network drive is not protected against aliasing while
  that drive is unavailable (for example a disconnected `Z:` whose share is reachable as UNC): in
  that state the guard compares lexically. The deployed footage path is on the local disk.
* A default root that is an ancestor of the footage folder is not refused unless the footage
  folder lies in `<root>/pytest-of-*`; pytest touches nothing else below the root.
* The guard needs the local configuration; without footage configured there is nothing to guard.
  The test subprocesses never read the real `clearwater.local.toml`; the containing session's
  guard does, by design.

## Tests (`tests/test_conftest_guard.py`, 44 cases; 41 in a subprocess on a miniature repository, 3 in process
under `tmp_path` with fake footage and working folders, except the three in-process unit tests)

Control (no guard wipes the footage); `--basetemp` refused (equal, trailing separator, existing and
missing subfolders, `..`, relative, ancestor); ordering and modes (default, `-s`, `-p no:capture`,
`--collect-only`, `--setup-plan`, `--cache-clear` with the cache provider on); `TMPDIR`/`TEMP`/`TMP`
inside and equal; uncached tempdir derivation (`-s`, `-p no:capture`: safe `TMPDIR` plus
`TEMP=<footage>` passes, `TMPDIR=<footage>` refused, absent first candidate refused);
`PYTEST_DEBUG_TEMPROOT`; case variant, symlink or junction, extended-length prefix, 8.3 short name,
volume GUID (Windows); default root whose `pytest-of-*` is, or links to, the footage; mixed-case
`PYTEST-OF-<USER>` junction (Windows); root that cannot be listed (in process); a check that cannot
be made refuses (in process); passes (work folder, sibling `footage-other`); inert (no file, invalid
TOML, relative path, no keys, NUL path); configured-but-missing footage still guards; skip reasons
(not configured, absent folder, footage path is a file); the safety helper resolves volume GUID
forms (in process).
