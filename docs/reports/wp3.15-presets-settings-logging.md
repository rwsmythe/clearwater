# WP3.15 report: presets, settings and logging

Package `clearwater.config` (`src/clearwater/config/`), tests `tests/test_config_*.py`. Spec v0.5.4
(D37, D38, D88, D89, D90; G6, G12, G13; N9, N11), architecture FINAL 1.0 (IF-9, IF-10, AD-8, AD-9,
AD-13, AD-20, AD-25). Base `9735282`. Nothing under `src/clearwater/interfaces/` was changed and no
dependency was added. The review ledger is `docs/proofs/wp3.15-ledger.md`.

## Public API (what WP3.12, WP3.14, WP3.16, WP3.17, WP3.20 consume)

All names are exported from `clearwater.config`. Every store and the log take their FOLDER as an
argument; only `paths.app_locations` reads the environment.

| Area | Names |
|---|---|
| Locations (WP3.12, WP3.16) | `app_locations(*, environ=None, platform=None, home=None) -> Locations`; `Locations(config_dir, cache_dir)` with `settings_file`, `presets_dir`, `log_dir`, `log_file`; `ensure_directory(path)`; name constants `SETTINGS_FILE_NAME`, `PRESETS_FOLDER_NAME`, `LOG_FOLDER_NAME`, `LOG_FILE_NAME`, `CACHE_FOLDER_NAME`, `WINDOWS_FOLDER_NAME`, `POSIX_FOLDER_NAME` |
| Settings (WP3.16, WP3.20) | `load_settings(folder, *, migrations=None) -> Settings`; `save_settings(folder, settings) -> Path` |
| Presets (WP3.17) | `PresetStore(folder, *, migrations=None)` with `list_presets()`, `load(name)`, `save(name, parameter_set, *, overwrite=False)`, `rename(old, new)`, `delete(name)`, `import_preset(source, schemas, *, name=None) -> PresetImportResult`, `export_preset(name, destination, *, overwrite=False)`, `install_starters(*, now=None)`; `PresetEntry(name, path, parameter_set, error, unsupported_version)`; `PresetImportResult(name, path, parameter_set, dropped_keys)` with `provenance_dropped`; `validate_preset_name`, `new_parameter_set(method, parameters, *, now=None)`, `starter_presets(now=None)` |
| Errors | `PresetError`; `PresetImportError(message, problems)`; `UnsupportedPresetVersionError` (also an `UnsupportedFormatVersionError`); `UnsupportedPresetImportError` |
| DR-32 (WP3.14) | `check_string_keys(value, where="value")`, `check_parameter_set_keys(parameter_set, where=...)` |
| Migration | `MigrationRegistry`, `DEFAULT_MIGRATIONS` (empty), `migrate(kind, data, registry=None)` |
| Files | `atomic_write_text(path, text)` |
| Log (WP3.16) | `configure_logging(folder, *, level=INFO, max_bytes=1 MiB, backup_count=5) -> Path`; `shutdown_logging()` |

Callers: the shell (WP3.16) calls `load_settings(locs.config_dir)`, `configure_logging(locs.log_dir)`
and `PresetStore(locs.presets_dir).install_starters()` at start; nothing creates folders on a read.
WP3.12 takes `app_locations().cache_dir` and `Settings.cache_limit_bytes`. WP3.14 calls
`check_string_keys` on a provenance object before embedding it, and writes the AD-9 device line itself.

## Claims and evidence

| Claim | Evidence (tests are in `tests/`) |
|---|---|
| App-data locations per OS (Windows `%APPDATA%\Clearwater`, `%LOCALAPPDATA%\Clearwater\cache`; XDG elsewhere; fallbacks; relative values ignored; nothing created) | `test_config_paths.py` |
| First run equals the five ruled defaults field by field, and the rest; defaults are never restated in config | `test_config_settings.py::test_first_run_equals_the_five_ruled_defaults_field_by_field` |
| Atomic save: a failed replace or sync keeps the old file and removes the temporary; a hard crash (child process `os._exit`) leaves the old file and a `.tmp` that is never read | `test_config_settings.py` (three tests) |
| Migration: a fake 0 to 1 step runs for settings, nested `last_parameters` and presets; a future version is refused by name, the file byte- and mtime-unchanged; a step must return the integer n + 1 | `test_config_settings.py`, `test_config_presets.py` |
| Corrupt settings file is set aside as `settings.json.bad-<UTC stamp>` (distinct names), never overwritten, defaults returned; out-of-range values take their defaults with a warning | `test_config_settings.py` |
| V13: export then import reproduces method, parameters, `format_version`, `created`, `app_version`; a saved file never holds `source` or `settings`; a sidecar imports with `dropped_keys` naming them | `test_config_presets.py` |
| Every G6 operation; starters installed once, renamable, deletable, not re-created; a same-named user preset is never overwritten | `test_config_presets.py` |
| Names safe on every OS (reserved device names, forbidden characters, trailing dot or space, 100 characters, 237 UTF-8 bytes); rename and delete cannot reach a non-preset file, a symlink or a path outside the folder | `test_config_presets.py` |
| Import validation with a hand-built schema, every `ProblemKind` reachable through import (`not_finite` cannot occur: non-finite numbers fail at parse); unknown method reported, all problems reported together; 1 MiB read cap names size and cap | `test_config_presets.py` |
| DR-32 closed at the config boundary, one test per entry point with a NaN key and an int key (settings save and load, preset save, load, list, import, export, the public helper) | `test_config_settings.py`, `test_config_presets.py`, `test_config_isolation.py` |
| Log: UTF-8, ISO line, INFO, idempotent, replaces on another folder, rotation at the limit with the backup count kept, unbounded settings refused | `test_config_log.py` |
| No code or test resolves the real app-data folder; only `paths.py` touches the environment (AST scan); importing `clearwater.config` loads no `gui`, `jobs`, `methods`, `core`, `io`, PySide6 or cupy | `test_config_isolation.py`, `test_config_paths.py` |

## Gates

Own tests: 218 passed (after the Reviewer B remediation). `uv run ruff check .`, `ruff format --check .` and `mypy` clean. Full pytest:
see the ledger (1336 passed on `01591af`; the final-head run is recorded there). Reviewer A: round 1
(2 major, 3 minor, remediated), round 2 (no blocking, four minors fixed in the terminating cleanup).
Reviewer B ran at the orchestrator's seat on the merge candidate and found 2 major and 3 minor; remediated (ledger "Reviewer B").

## Limits and decisions (for the accept record)

- DR-32 is closed at the config boundary; a direct `ParameterSet.from_dict` or `to_dict` caller is
  unguarded because the interfaces are frozen.
- If renaming a corrupt settings file fails, the code warns and returns defaults; a later save then
  overwrites the corrupt file.
- Name-collision checks and exists-then-write sequences are not race-free against a second process
  (outside the envelope). A hard crash can leave a `*.tmp` beside the target; no store reads it.
- A migrated older file is not rewritten on load; the next save writes the current format.
- Starters use one marker (`presets/.starters-installed`); a future starter needs a new marker version.
- The rotating log counts the new record in characters against a byte position: a file may pass the
  limit by the last record's surplus bytes, and one record over the limit is written whole to its own
  file. The log therefore holds at most six files (`log.py` docstring; `test_config_log.py` pins both).
- Name length is 100 characters and 237 UTF-8 bytes (a 255-byte file-name limit less `.json` and the
  13-byte tail of the atomic temporary); the byte cap was an out-of-envelope reviewer finding fixed
  anyway.
- macOS uses the XDG branch (ruling 15.1); the non-Windows branch is tested by injection, never run
  on another OS. No developer override of the app-data root exists (ruling answer 7).
- A preset whose saved text would exceed the 1 MiB read cap is refused at save and export (one constant, `MAX_PRESET_BYTES`), so the store never writes a file it cannot read back.
- Export to a caller-chosen path with `overwrite=True` replaces that file by design (the GUI's confirmed save-as); a dangling symlink at the destination counts as existing.
- Provenance keys are dropped, not refused, on preset save and import (CHARC ruling), and named in
  `PresetImportResult.dropped_keys`. Every other unknown key is still refused.
- The store method is `list_presets()` (a method named `list` would shadow the builtin).
- Starter values are empty (`ParameterSet("c3", {})`); explicit values wait for the owner at CP5.
