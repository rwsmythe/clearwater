# WP3.15 ledger (presets, settings and logging)

Cell: implementer-sonnet-high (tier STRONG). Worktree `.worktrees/wp3.15`, branch `wp3.15`, base
`9735282`. Spec v0.5.4, architecture FINAL 1.0. Brief `docs/briefs/wp3.15-brief.md`; rulings
15.1 to 15.9 and X2 apply as written (recommended answers are the rulings).

## Cumulative round ledger

| Round | Date | Blocking (crit/maj) | Minor | In/out envelope | NEW/REOPENED | Fix kind | Transport | Depth |
|---|---|---|---|---|---|---|---|---|
| 0 (design) | 2026-10-20 | n/a | n/a | n/a | n/a | n/a | n/a | 83,816 (dispatcher, 15 turns) |
| build yield | 2026-10-20 | n/a | n/a | n/a | n/a | product + tests | n/a | 145,492 (dispatcher, 34 turns) |
| 1 | 2026-10-20 | 2 major, 0 critical | 3 | all in | 5 NEW, 0 REOPENED | PRODUCT + tests (01591af) | WSL, codex-cli, gpt-5.6-sol high; head 703f7d9 | 176,725 (dispatcher, 57 turns) |
| 2 | 2026-10-20 | 0 | 4 (3 in, 1 out) | 3 in, 1 out | 4 NEW (1 a refinement of round-1 #4), 0 REOPENED | cleanup (product + comment + tests), no further round | WSL, codex-cli, gpt-5.6-sol high; head 01591af | 217,080 (dispatcher, 87 turns) |

## Round 0: the design table (brief task 1)

Round-0 code shipped with this yield (X2): `config/__init__.py`, `config/paths.py`,
`tests/test_config_paths.py`. No other product code before the ruling.

### 1. Locations (`paths.py`; ruling 15.1, AD-25(a)) - SHIPPED

| Platform | config_dir (settings, presets, log) | cache_dir (WP3.12) |
|---|---|---|
| Windows (`sys.platform == "win32"`) | `%APPDATA%\Clearwater` | `%LOCALAPPDATA%\Clearwater\cache` |
| elsewhere (Linux, macOS) | `$XDG_CONFIG_HOME/clearwater` | `$XDG_CACHE_HOME/clearwater` |

Unset, empty or relative variables are ignored; fallbacks are `~/AppData/Roaming`,
`~/AppData/Local` (Windows) and `~/.config`, `~/.cache` (elsewhere). macOS uses the XDG branch
(not `~/Library`; the brief rules only Windows and XDG). Layout under `config_dir`:
`settings.json`, `presets/<name>.json`, `presets/.starters-installed`, `logs/clearwater.log[.N]`.

Public API (WP3.12 and WP3.16 consume): `app_locations(*, environ=None, platform=None,
home=None) -> Locations` (the only function that reads the environment, platform or home);
`Locations(config_dir, cache_dir)` with properties `settings_file`, `presets_dir`, `log_dir`,
`log_file`; `ensure_directory(path) -> Path` (mkdir -p, the first-use rule); name constants
(`SETTINGS_FILE_NAME`, `PRESETS_FOLDER_NAME`, `LOG_FOLDER_NAME`, `LOG_FILE_NAME`,
`CACHE_FOLDER_NAME`, `WINDOWS_FOLDER_NAME`, `POSIX_FOLDER_NAME`). Load never creates folders;
save, preset writes and log set-up do. Every store and the log take their folder as an argument.
No developer environment override is added (answer 7).

### 2. Files and modules (one extra file proposed)

| File | Contents |
|---|---|
| `paths.py` | above |
| `atomic.py` (PROPOSED, extra to the brief's list, same owned folder) | `atomic_write_text(path, text)`: temp file in the same folder, flush + fsync, `os.replace`; the temp is removed if the write or replace raises. Shared by settings save, preset save and preset export. |
| `keys.py` | DR-32: `check_string_keys(value, where)`, `check_parameter_set_keys(parameter_set, where)` |
| `migration.py` | `MigrationRegistry`, `DEFAULT_MIGRATIONS` (empty today), `migrate(kind, data, registry=...)` |
| `settings_store.py` | `load_settings(folder, *, migrations=None) -> Settings`, `save_settings(folder, settings) -> Path`, `SETTINGS_FILE_NAME` re-used from `paths` |
| `presets.py` | `PresetStore(folder)`, `PresetEntry`, `PresetImportResult`, `PresetError`, `PresetImportError`, `validate_preset_name`, `starter_presets`, `new_parameter_set` |
| `log.py` | `configure_logging(folder, *, level=INFO, max_bytes=1 MiB, backup_count=5) -> Path`, `shutdown_logging()` |

### 3. Settings store (D89, G13)

- `load_settings(folder)`: no file -> `Settings()` (nothing restated: the defaults come from the
  frozen dataclass). File present: decode with `loads_object`, `migrate("settings", ...)`,
  migrate the nested `last_parameters` with kind `"preset"`, `check_string_keys` on the migrated
  object, then re-dump and `Settings.from_json`. Then the ruling-8 value checks, per field:
  `png_bit_depth` in {8, 16}, `quality_level` in {high, standard, draft}, `cache_limit_bytes`
  >= 0; an out-of-range field takes `Settings()`'s value for that field with a logged warning.
  Encoder names are not checked (D74).
- `save_settings(folder, settings)`: `check_parameter_set_keys` on `last_parameters`, then
  `settings.to_json()` and `atomic_write_text`; creates the folder. Returns the file path.
- Corrupt or unreadable (ruling 3): `FormatError` (bad JSON, missing/unknown/wrong-type field,
  non-UTF-8 bytes, a refused key) or an `OSError` on read -> rename beside itself to
  `settings.json.bad-<UTC yyyymmddThhmmssZ>` (a `-N` suffix on collision), log a warning, return
  `Settings()`; the bad file is never overwritten silently. If the rename itself fails, warn and
  return `Settings()` (the next save would then overwrite; documented limit).
- Future version: `UnsupportedFormatVersionError` propagates, the file is not renamed, moved or
  rewritten (migration rule below). Version 0 / absent / non-integer with no step also raises it.
  A migrated old file is NOT rewritten on load; the next save writes the current format.

### 4. Migration rule (`migration.py`)

`MigrationRegistry` maps `(kind, from_version) -> step`, `kind` in {"settings", "preset"}; a step
takes the decoded object and returns the object at version n+1 (it sets `format_version`).
`migrate(kind, data, registry)`: version above `FORMAT_VERSION` (or a non-integer, boolean or
absent version) -> `UnsupportedFormatVersionError` before any step runs, input never mutated
(steps get a deep copy); below it -> apply steps n -> n+1 until `FORMAT_VERSION`, a missing step
-> `UnsupportedFormatVersionError`. Loaders take an optional `migrations=` registry so the test-only
fake 0 -> 1 step proves the whole load path; the default registry is empty.

### 5. Preset store (D37, D38, D90, G6; rulings 15.4 and answer 5)

`PresetStore(folder)`; all methods take names, never paths; the folder is created on first write.

| Method | Behaviour |
|---|---|
| `list() -> list[PresetEntry]` | every `*.json` in the folder, sorted by `casefold` name; `PresetEntry(name, path, parameter_set | None, error | None)`; a corrupt or future-version file is listed with `error` set and left untouched |
| `load(name) -> ParameterSet` | migrate + `check_string_keys` + `ParameterSet.from_dict`; `PresetError` if missing / unreadable |
| `save(name, parameter_set, *, overwrite=False) -> Path` | name rule, key check, atomic write; provenance keys are STRIPPED (a preset carries none, AD-13); an existing name (case-insensitive) is `PresetError` unless `overwrite` |
| `rename(old, new) -> Path` | both names validated; `old` must be a readable preset; `new` must not exist (case-insensitive), except a case-only change of the same preset; `os.rename`, content untouched |
| `delete(name)` | `old` must be a readable preset file; then unlink |
| `import_preset(source, schemas, *, name=None) -> PresetImportResult` | read (cap 1 MiB), migrate, keys check, `ParameterSet.from_dict`, unknown method -> `PresetImportError([ParameterProblem("method_mismatch", None, "unknown method ...")])`, else `validate_parameter_set` against `schemas[method]` and `PresetImportError(problems)` carrying EVERY problem; name defaults to the source stem; a taken name becomes "name (2)", "(3)", ...; provenance keys on the source (a sidecar imported as a preset) are stripped, not refused |
| `export_preset(name, destination, *, overwrite=False) -> Path` | existing destination -> `PresetError` unless `overwrite`; atomic write of the AD-13 JSON |
| `install_starters(*, now=None) -> list[str]` | first-run installation, below |

`schemas` is `Mapping[str, Sequence[Parameter]]` (method id -> parameters) passed by the caller;
config imports no method. Name rule (`validate_preset_name`, every OS): 1 to 100 characters after
no leading/trailing whitespace; none of `<>:"/\|?*` or control characters; no trailing dot; not
`.` or `..`; the part before the first dot not a Windows reserved device name
(CON PRN AUX NUL COM0-9 LPT0-9, superscript digits, case-insensitive); the file is
`<name>.json` and the name is matched case-insensitively against existing files. Rename and
delete only ever build `folder / (validated name + ".json")` and require it to be a regular,
parseable preset, so neither can reach a non-preset file or leave the folder.

### 6. Starter presets (answer 4, ruling 15.4)

`starter_presets(now) -> dict[str, ParameterSet]` builds "Snorkel (shallow)" and "Scuba (deep)",
each `ParameterSet("c3", {}, created=now, app_version=clearwater.__version__)`. `install_starters`
writes each that does not already exist as a file, then writes the marker
`presets/.starters-installed` LAST; if the marker exists nothing is done, so a deleted starter is
not re-created. Starters rename and delete like any preset (the marker is the only memory).
A future added starter would need a new marker version (noted, not built).
`new_parameter_set(method, parameters, *, now=None)` stamps `created` (UTC) and `app_version`
for the GUI's "save preset".

### 7. DR-32 (`keys.py`; answer 2)

`check_string_keys(value, where)`: recursive over `Mapping`, list, tuple; a non-`str` key
(int, float incl. NaN, bool, None, bytes, tuple) -> `FormatError` naming the path and the key's
type; a reference cycle -> `FormatError`. `check_parameter_set_keys(ps, where)` applies it to
`parameters`, `source` and `settings`. Entry points guarded: `save_settings`, `load_settings`
(after migration, so a migration step cannot smuggle a key in), `PresetStore.save`, `.load`,
`.import_preset`, `.export_preset`, and the public helper for WP3.14's provenance object. One test
per entry point with a `float("nan")` key and an `int` key. DR-32 closes for every config and
provenance path; residual: a direct `ParameterSet.from_dict` / `to_dict` caller is unguarded.

### 8. Log (`log.py`; answer 6)

`configure_logging(folder, ...)`: creates the folder, attaches one `RotatingFileHandler`
(`logs/clearwater.log`, UTF-8, 1 MiB, 5 backups, level INFO) to the `clearwater` logger, line
`2026-10-20T12:30:15.123+02:00 INFO clearwater.config message` (local ISO time with offset,
level, logger, message). Marked handler; a second call with the same file is a no-op returning
the path; with another folder it replaces the handler (old one closed). `propagate` stays True.
`shutdown_logging()` removes and closes the handler (tests, and so Windows can delete the folder).
Bound on disk: at most 6 files of 1 MiB.

### 9. Other open questions

- Q5/Q8/Q9: as drafted. Q7: `clearwater.local.toml` not read. Q2: closed at the config boundary.
- Added decisions (the brief is silent): provenance keys stripped on save/import (not refused);
  1 MiB cap on a preset file read; STOP-free (no interface change, no dependency, no default
  restated).
- Test isolation: tests use `tmp_path`; one test poisons `paths.app_locations` and runs every
  operation, and scans the sources so only `paths.py` touches the environment or home.

## Round 0 verification (shipped files)

`uv run ruff check .`, `ruff format --check .`, `mypy` clean; `tests/test_config_paths.py`
11 passed (Windows and XDG resolution, fallbacks, relative values ignored, creates nothing,
`ensure_directory`, dependency rule in a clean interpreter).

## Round-0 ruling (orchestrator gen 5, 2026-10-20) as applied

Atomic helper, provenance stripping, 1 MiB cap, macOS on XDG and no environment override all
ACCEPTED. Conditions applied: only `source` and `settings` are stripped (every other unknown key is
still refused by IF-9); `PresetImportResult.provenance_dropped` tells the GUI; the cap refusal names
the size and the cap; V13 and sidecar-import tests exist; a saved file never contains either key.
One deviation from the table: the store method is `list_presets()` (a method named `list` would
shadow the builtin inside the class body for mypy).

## Build record (before the first window)

Commit `987206b`: all modules and tests. Own tests (`tests/test_config_*.py`) 181 passed; ruff check,
ruff format --check and mypy clean. A defect found by the case-only rename test and fixed in the same
commit: `Path` equality is case-insensitive on Windows, so the rename was skipped (now compares
`.name`). Not yet run: full pytest (window requested), Reviewer A.

CHARC addition applied (252e847): `PresetImportResult.dropped_keys` names the dropped provenance
keys (`source`, `settings`); `provenance_dropped` is a derived bool. The `list_presets()` name was
accepted by the dispatcher.

## Full pytest (window granted 18:30Z) on head 703f7d9

1320 passed, 1 warning (cupy CUDA path), 582 s, exit 0 (`work/pytest-full.txt` in the worktree).

## Round 1 (Reviewer A, head 703f7d9, verdict NEW_CRITICAL_MAJOR_FOUND)

Evidence: `C:/Users/rwsmy/clearwater-review-evidence/wp3.15/r1/` (prompt, diff, `full-transcript.txt`,
`review.txt`, `adjudication.md`, `adjudication-probe.py`, md5s). Probe `READY` passed first; model and
effort match the STRONG tier; the only ERROR lines were a sandbox-rejected `rm -f` and WSL vsock noise.
All findings REASONED (the reviewer could not run uv); each reproduced or confirmed by reading by the cell.

| # | Sev | Where | Finding | Adjudication | Fix plan |
|---|---|---|---|---|---|
| 1 | MAJOR | presets.py `_matches`, `list_presets` | `.json` suffix compared case-sensitively; on Windows `Foo.JSON` is the same file as `Foo.json`, so save/import/starters overwrite it and list hides it | CONFIRMED by probe (listed `[]`, save replaced it); in-envelope; NEW | compare the suffix case-insensitively everywhere; a `.JSON` file is listed and collides; tests with `Foo.JSON` for list, save, import, starters |
| 2 | MAJOR | presets.py `_read_preset`, import wrap, list | a future-version preset loses its `UnsupportedFormatVersionError` identity (only `__cause__`) | CONFIRMED by probe; in-envelope; NEW | `UnsupportedPresetVersionError(PresetError, UnsupportedFormatVersionError)` raised by load/rename/delete/save-overwrite and by import (as a `PresetImportError` subclass); `PresetEntry.unsupported_version` flag; tests |
| 3 | MINOR | presets.py import numbering | a 100-character name cannot get " (2)" | CONFIRMED by reading | truncate the base to fit the 100-character limit; test |
| 4 | MINOR | log.py docstring | "at most six files of 1 MiB" is false for one record over 1 MiB | CONFIRMED by reading | state the bound as six files of max_bytes plus the largest record; test with an oversized record documents it |
| 5 | MINOR | migration.py | a step may return `1.0` as the new version | CONFIRMED by probe | require an `int` that is not bool, exactly n + 1; test |

Fix kind of the coming remediation: PRODUCT code (1, 2, 3, 4 docstring, 5) plus tests.

### Round 1 remediation (dispatcher rulings: all five ACCEPTED)

PRODUCT code plus tests; interfaces untouched. (1) one helper `_is_preset_file` (suffix compared
case-insensitively) used by list, find/collision, and a new `_existing(name)` used by load, rename,
delete (and so export); a `.JSON` file is listed, collides on save/import/starters and is replaced
in place only with `overwrite`. (2) `UnsupportedPresetVersionError(PresetError,
UnsupportedFormatVersionError)` raised by load/rename/delete/save-overwrite/export, and
`UnsupportedPresetImportError(PresetImportError, UnsupportedPresetVersionError)` by import;
`PresetEntry.unsupported_version`; the file stays byte-unchanged. (3) numbering truncates the base to
fit 100 characters, strips trailing space and dot, and re-validates the result. (4) `log.py`
docstring: the bound is per rollover; one record over the limit is written whole to its own file; a
test pins it. While pinning, a true detail surfaced: the handler counts characters, so on Windows a
file may exceed the limit by one byte per line (CRLF); the docstring and the rotation test say so
(the round-0 test had a 200-byte slack that hid this). (5) a migration step must return the integer
n + 1 (not 1.0, not True).

Regression tests written against the unfixed source (a scratch copy of HEAD with only the two
exception classes added so the file imports): 10 of the new tests FAIL there (4 `.JSON`, 3
version-identity, 2 truncation, 1 float version) and pass on the fixed code. Inner loop: 198
passed; ruff check, ruff format --check, mypy clean.

## Full pytest (window 2) on head 01591af

1336 passed, 1 warning (cupy CUDA path), 522 s, exit 0 (`work/pytest-full-2.txt`).

## THIS IS ROUND 2 (Reviewer A, head 01591af, verdict NO_NEW_CRITICAL_MAJOR)

Evidence: `C:/Users/rwsmy/clearwater-review-evidence/wp3.15/r2/` (prompt with the round-1 findings and
rulings listed, diff, `full-transcript.txt`, `review.txt`, `adjudication.md`, md5s). The reviewer could
not run uv but read the pre-run summaries in the worktree (`work/test-summary.txt`,
`work/config-tests-verbose.txt`) and ran two probes itself (EXECUTED). Probe READY passed; gpt-5.6-sol
high; footer present; 12 `^ succeeded in`; the reviewer opened no ledger file. Round 1's five fixes
were verified: no reopened findings.

| # | Sev | Tag | Where | Finding | Adjudication |
|---|---|---|---|---|---|
| 1 | MINOR | EXECUTED | log.py:46 | UTF-8 multibyte records can exceed the rotation threshold by more than a byte per line (the handler counts characters) | VALID refinement of round-1 #4, in-envelope; cleanup: say it in the docstring and pin with a test |
| 2 | MINOR | EXECUTED, OUT-OF-ENVELOPE | presets.py:168 | name length counts code points; 100 CJK characters give a 305-byte file name, over the 255-byte POSIX component limit | VALID, banked (non-Windows, not run); cheap cleanup: also cap the UTF-8 byte length |
| 3 | MINOR | REASONED | presets.py:282 | `list_presets` follows symlinks that `load/rename/delete/export` refuse | VALID, in-envelope; cleanup: list skips symlinks |
| 4 | MINOR | REASONED | presets.py:360 | a comment says Windows paths compare case-insensitively but the code compares `.name` strings | VALID, comment wrong; cleanup: fix the comment |

Convergence: zero NEW blocking findings, so the loop terminates. The four non-blocking findings are
fixed once in the terminating cleanup (not yet applied; waiting on the dispatcher's go).

## Terminating cleanup (dispatcher approved; no round opened)

All four minors fixed in one commit, with tests. #2 (out of envelope, fixed not banked): a UTF-8 byte
cap of 237 on the name, i.e. 255 less `.json` (5) less the 13-byte tail of the atomic temporary
(`.` + 8 random + `.tmp`), so a name that passes can always be saved even by its temporary file; the
dispatcher said 255 and the stricter figure is what makes the temporary fit (test captures the temporary
name of the longest allowed name: 255 bytes); numbering truncation now also respects the byte cap.
#1: investigating the probe showed the handler adds the new record's length in characters to the file's
size in BYTES, so the overshoot is only the last record's surplus (multibyte extra bytes, one CR on
Windows), not "four times" and not "one byte per line"; the `log.py` docstring says exactly that and
two tests pin it (ASCII: size <= limit; accented text: size <= limit + that record's 101 surplus).
#3: `list_presets` skips symlinks (test). #4: comment corrected.

Dispatcher ruling on the figure: the 237-byte cap is ACCEPTED as the corrected figure of the "255"
in the cleanup ruling (255 less `.json` less the 13-byte atomic-temporary tail).

## Final-head run before Reviewer B

Head 51c0e9e: 1341 passed, 1 warning, 517 s (`work/pytest-full-3.txt`).

## Reviewer B (orchestrator seat, merge candidate b051c3d = 51c0e9e rebased on 4f122ec)

Verdict NEW_CRITICAL_MAJOR_FOUND, all five findings EXECUTED. Evidence
`C:/Users/rwsmy/clearwater-review-evidence/wp3.15/reviewB/review-B.txt`. Dispatcher depth when sent: 237,714.

| # | Reviewer sev | Adjudicated | Finding | Fix |
|---|---|---|---|---|
| 2 | MAJOR | UPHELD, introduced, in envelope | `save` wrote presets above the 1 MiB read cap that every later read rejected, stranding them | one serialiser `_serialise` refuses text over `MAX_PRESET_BYTES` with `PresetError` naming size and cap, used by save, overwrite, import, starters and export; tests: over-cap refused with nothing written, exactly-at-cap round trips, over-cap overwrite keeps the old file |
| 1 | MAJOR | DOWNGRADED to MINOR: export with `overwrite=True` to a caller-chosen path is the GUI's confirmed save-as (replacing it is intended, not a G6 breach); the real defect is the existence check | `os.path.lexists`, so a dangling symlink at the destination counts as existing when `overwrite=False`; test skips with a reason where symlinks cannot be made |
| 3 | MINOR | VALID | decoder `ValueError` (5000-digit integer) and `RecursionError` (deep nesting) escaped the recovery paths | settings: set aside; preset `_read` wraps them as `FormatError` (so import is refused, list shows the file unreadable, load is a `PresetError`); one test per path |
| 4 | MINOR | VALID | a migration step returning a non-object raised `AttributeError` | `FormatError` naming the kind and the from-version; test (4 values) |
| 5 | MINOR | VALID | C1 controls U+0080-U+009F were accepted in names | name rule refuses Unicode category Cc (C0, DEL, C1); test (5 values) |

Regression checks: with `src/` stashed (tests kept) 14 of the new tests FAIL; on the fixed code the
inner loop is 218 passed, ruff check, ruff format --check and mypy clean. No Reviewer A round (dispatcher).
