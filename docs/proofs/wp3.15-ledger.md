# WP3.15 ledger (presets, settings and logging)

Cell: implementer-sonnet-high (tier STRONG). Worktree `.worktrees/wp3.15`, branch `wp3.15`, base
`9735282`. Spec v0.5.4, architecture FINAL 1.0. Brief `docs/briefs/wp3.15-brief.md`; rulings
15.1 to 15.9 and X2 apply as written (recommended answers are the rulings).

## Cumulative round ledger

| Round | Date | Blocking (crit/maj) | Minor | In/out envelope | NEW/REOPENED | Fix kind | Transport | Depth |
|---|---|---|---|---|---|---|---|---|
| 0 (design) | 2026-10-20 | n/a | n/a | n/a | n/a | n/a | n/a | (dispatcher fills) |

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
