# WP3.15 — Presets, settings and logging (dispatch brief, DRAFT)

**Status:** DRAFT 2026-10-20 by the orchestrator (generation 4) at CHARC's commission
(`a05f065e53e696d7`), for CHARC approval. Not dispatched before approval; may dispatch once
WP2.3 has merged (no v0.5.4 item changes it; see open question 9). Owner decisions: none inside
the package (the starter presets' values are the owner's to see at CP5, AD-13).
- Spec **v0.5.3**; v0.5.4 items cited as "proposed (v0.5.4, CP4)". Architecture DRAFT 0.1
  section 3 IF-9 and IF-10, section 7; AD-8, AD-9, AD-13, AD-20. Frame
  `docs/briefs/wp2.4-phase3-frame.md`. WP2.2 round-1 ruling (CHARC `b7b012f7c6d5a1e6`, ledger
  `docs/proofs/wp2.2-ledger.md`); WP2.2 accept `docs/proofs/wp2.2-accept.md` ("WP3.15 owns the
  settings file paths, `format_version` migration, and DR-32").
- Cell: `implementer-sonnet-high`. Tier **STRONG**.
- Worktree `.worktrees/wp3.15`, branch `wp3.15`, base = the main commit named at dispatch.

**Why.** WP2.2 froze the JSON forms of `ParameterSet` (IF-9) and `Settings` (IF-10) with no
file I/O: "where the document lives (the platform app-data folder) and the migration of other
format versions belong to WP3.15" (`interfaces/settings.py` module docstring). The preset panel
(WP3.17), the settings panel (WP3.20), export (WP3.14) and the photo path end to end (WP4.1,
plan "Depends on ... WP3.15") all need the files this package keeps.

| Field | Content |
|---|---|
| ID and title | WP3.15 — Presets, settings and logging; plan Phase 3 row WP3.15 (size M); module `clearwater.config` (plan 8.1: "Presets, settings, logging") |
| Goal | The app-data locations; a settings store that loads and saves IF-10 `Settings` (first run = the WP2.2 defaults) with `format_version` migration; a preset store (save, load, rename, delete, import, export, the two AD-13 starter presets) on IF-9 `ParameterSet`; DR-32's key check at the config boundary; and the rotating log (N9). |
| Spec / decision clauses | D37 "Presets stored in the user's app-data folder; can be exported and imported as files"; D38 "Clearwater ships with starter presets"; D88 "Rotating log file in app data"; D89 "Settings and last-used parameters persist between sessions"; D90 "Preset files record their method and a format version"; N9 "rotating log file in app data (D88)"; N11 "preset files record their method and a format version (D90)"; G6 "Presets: save, load, rename, delete, import from file, export to file. Starter presets included." (the store side; the panel is WP3.17); G12 settings list; G13 "Settings and last-used parameters persist between sessions (D89)". Feeds V13 "export then import reproduces identical parameters, method and version". AD-13 (format; starter presets "Snorkel (shallow)" and "Scuba (deep)", "both the defaults of AD-8 in v1"); AD-9 (`force_cpu`); proposed (v0.5.4, CP4) item 6: G12 gains "force CPU processing (Advanced)" and "the first-run defaults: PNG 16-bit, encoder auto ..., quality Standard, cache 20 GB"; item 7 (D75 level names High / Standard / Draft). DR-32 (closes here). |
| Depends on | WP2.2 merged (IF-9, IF-10 frozen). WP2.3 merged (the frame's dispatch order); no WP2.3 sample is needed. |
| Files owned | `src/clearwater/config/` (NEW: `__init__.py`, `paths.py` (app-data locations), `settings_store.py`, `presets.py` (store and starter presets), `migration.py`, `keys.py` (DR-32 check), `log.py` (named so it does not shadow stdlib `logging`)); `tests/test_config_*.py` (NEW); `docs/reports/wp3.15-presets-settings-logging.md`; `docs/proofs/wp3.15-ledger.md`. NOT owned: `src/clearwater/interfaces/` (frozen; `parameters.py` and `settings.py` are read, never changed), `pyproject.toml` (no dependency), `tools/local_config.py`, `tests/conftest.py`. |
| Interfaces provided | No frozen interface; the stores' public names become WP3.17/WP3.20/WP3.14 inputs, so the round 0 yield tables them for CHARC (task 1). |
| Interfaces consumed | IF-10 `Settings` (`to_json`, `from_json`; fields `output_folder`, `output_suffix`, `png_bit_depth`, `video_encoder`, `quality_level`, `ten_bit_for_eight_bit`, `provenance`, `cache_limit_bytes`, `force_cpu`, `last_parameters`) and its constants `DEFAULT_OUTPUT_SUFFIX`, `DEFAULT_PNG_BIT_DEPTH`, `DEFAULT_VIDEO_ENCODER`, `DEFAULT_QUALITY_LEVEL`, `DEFAULT_CACHE_LIMIT_BYTES`. IF-9 `ParameterSet` (`to_dict`, `from_dict`, `to_json`, `from_json`), `FORMAT_VERSION`, `FormatError`, `UnsupportedFormatVersionError`, `loads_object`, `check_format_version`, `validate_parameter_set`, `ParameterProblem`. IF-3 `Parameter` (a schema passed in by the caller for import validation; config imports no method). Python stdlib only (`json`, `os`, `pathlib`, `logging.handlers.RotatingFileHandler`). |
| Wave-2 consumers | WP3.12 (proxy cache, wave 2: the cache's app-data location, D71 "Stored in app data", and `Settings.cache_limit_bytes`); WP3.16 (shell, wave 2: settings at start, the log). Wave 3: WP3.17 (presets panel, G6), WP3.20 (settings panel, G12/G13). Wave 4: WP3.14 (the AD-9 device line in each job's log, last-used parameters, provenance keys). Phase 4: WP4.1, WP4.3. Stubs: `stubs.py` has none for config (IF-9/IF-10 are concrete dataclasses, not protocols). Until this merges consumers use `Settings()` in memory and `ParameterSet` directly; `stubs.StubProxyCache` starts at `DEFAULT_CACHE_LIMIT_BYTES`. WP3.12 has no stub for the app-data path (open question 1). |
| Hardware flags | None. No footage, no GPU, no timing. |
| Out of scope | Changing anything in `src/clearwater/interfaces/` (AD-20; a needed change is a STOP); the settings and preset GUI (WP3.17, WP3.20); the method parameter schema and the parameter names (WP3.2-3.4); the proxy cache itself (WP3.12); provenance embedding in outputs (WP3.6, WP3.10; D91); export and batch (WP3.14); reading `clearwater.local.toml` (open question 7); encoder name validation (WP3.10's capability report, D74); writing to the real app-data folder from any test. |
| Done | Plan 4.5; frame section 2 rules 1-11 apply; ruff check, ruff format --check, mypy strict, full pytest green; V13's round trip proven; DR-32 closed with a test per entry point; Reviewer A converged. |

## Task ladder

1. **Round 0 yield: the design table.** Before product code, write in the ledger: the app-data
   locations per platform (open question 1); file names and layout; the public functions of
   each store; the migration rule; the corrupt-file rule (open question 3); the preset file
   naming rule (open question 5); the log rotation figures (open question 6); the answers to the
   other open questions. YIELD for the dispatcher.
2. **Locations (`paths.py`).** One function resolves the app-data root; it is the only code
   that reads the environment for a location. Every store and the log take their folder as an
   argument, so tests pass `tmp_path` and never touch the real app-data folder. Folders are
   created on first use.
3. **Settings store (D89, G13).**
   - Load: no file → `Settings()` (the WP2.2 round-1 defaults: `png_bit_depth` 16,
     `video_encoder` "auto", `quality_level` "standard", `cache_limit_bytes` 20 * 10**9,
     `force_cpu` False; plus `output_folder` None, `output_suffix` "_corrected",
     `ten_bit_for_eight_bit` False, `provenance` True, `last_parameters` None). The defaults
     come from the frozen dataclass and are not restated in config.
   - Save: written to a temporary file in the same folder, then `os.replace`, so a crash leaves
     either the old or the new file, never a half-written one.
   - `last_parameters` round trips (D89).
4. **Migration (`format_version`).** A stepwise registry (version n → n+1 on the decoded
   object) applied before `Settings.from_json` / `ParameterSet.from_dict`, which accept only 1.
   Today only 1 exists, so the registry is empty and the code path is proven with a test-only
   step (a fake version 0 → 1). A version above `FORMAT_VERSION` is refused by name and the file
   is left untouched.
5. **Preset store (D37, D38, D90, G6).** Save, load, list, rename, delete, import from a file,
   export to a file. Every preset file is the AD-13 object (`format_version`, `method`,
   `parameters`, `created`, `app_version`; no provenance keys). Import validates with
   `validate_parameter_set` against the schema the caller passes for the preset's method, and
   reports every `ParameterProblem`; an unknown method is reported, not guessed.
6. **Starter presets (AD-13).** "Snorkel (shallow)" and "Scuba (deep)", method `c3` (D16, the
   default), "both the defaults of AD-8 in v1", in the form open question 4 settles; installed
   so the user sees them on first run.
7. **DR-32 at the boundary (`keys.py`).** Refuse a non-string mapping key at any depth with
   `FormatError` naming the path, on every config entry point: settings load and save, preset
   save, load, import and export, and a public helper WP3.14 can call on a provenance object
   before it is embedded. One test per entry point, with a `float("nan")` key and an `int` key
   (the silent `json.dumps` coercion DR-32 names).
8. **Rotating log (D88, N9).** `RotatingFileHandler` in the app-data log folder, UTF-8, one
   `clearwater` logger hierarchy (`clearwater.<module>`), a line format with ISO time, level,
   logger and message; configured once, idempotent on a second call; the figures of open
   question 6.
9. **Tests.**
   - First run equals the five ruled defaults field by field; save, load and equality.
   - Crash during save (the temporary left, the old file intact).
   - Migration: the fake step runs; version 2 refused, file unchanged; corrupt JSON per open
     question 3.
   - V13: export then import gives an equal `ParameterSet` (method, parameters,
     `format_version`); `created` and `app_version` kept.
   - Every G6 operation, including rename and delete of a starter preset per open question 4.
   - Name rule: Windows-reserved and non-portable names refused on every OS (N1).
   - Import validation with a hand-built `Parameter` schema, each `ProblemKind` once.
   - DR-32: every entry point.
   - Log: rotation at the size limit, backup count kept, UTF-8 text round trip.
   - No test writes outside `tmp_path`: a test monkeypatches the app-data root and asserts the
     real one is never resolved.
   - Dependency rule (plan 8.1, frame rule 5): importing `clearwater.config` loads nothing from
     `clearwater.gui`, `.jobs`, `.methods`, `.core`, `.io`, nor `PySide6` or `cupy`.

## Declared operating envelope

Windows 11, a local user profile; one Clearwater process at a time; settings and preset files
written by Clearwater or hand-edited by the owner. Out of envelope: two processes writing the
settings file at once, roaming or network profiles, other operating systems (portable, N1, not
run there), preset files from an untrusted source beyond the validation of task 5.

## Review loop (Reviewer A), per `docs/review-gate-clearwater.md` Part 1

- Tier **STRONG**. Evidence `C:\Users\rwsmy\clearwater-review-evidence\wp3.15\rN\`; ledger
  `docs/proofs/wp3.15-ledger.md`. Copy the runner and prompt shape from
  `C:\Users\rwsmy\clearwater-review-evidence\wp2.2\r3\run_review.sh` and `review-prompt.md`;
  exclude `docs/proofs` with `--glob '!docs/proofs/**'`. Five-round gate.
- **WHAT TO EXAMINE:**
  - defaults come from the frozen dataclass, never restated;
  - the save is atomic and a failure never destroys the previous file;
  - migration refuses the future and never rewrites what it refused;
  - V13 equality is real (method, parameters, version);
  - DR-32 refused at every entry point, at any depth, for every non-string key type;
  - preset names safe on every OS; rename and delete cannot touch a non-preset file;
  - the log rotates and cannot grow without bound;
  - no test or code path writes to the real app-data folder;
  - nothing in `interfaces/` changed.
- Reviewer B is the orchestrator's seat pass on the merge candidate.

## Notes for the cell

- **Return report** = your FINAL message, under about 70 lines (`docs/dispatch-recipe.md`
  section 4): the public API, the file layout, the defaults test, the DR-32 entry-point table,
  the gates, the Reviewer A rounds and verdict, open items.
- **STOP for:** any change needed in `src/clearwater/interfaces/`; a default that differs from
  the frozen `Settings`; a parameter name you would have to invent for a starter preset; a
  dependency (for example a platform-directories library); OS-specific code beyond what CHARC
  rules under open question 1.
- **Working rules:** `uv sync`. Commit by pathspec, `feat(wp3.15): ...`, with a
  `Co-Authored-By:` footer naming your model. Never a bare `cd`. Never post to a mailbox. The
  full pytest (8-15 min, 892+ tests) runs in the background with output to a file under
  `work/`. Gates: ruff check, ruff format --check, mypy strict, full pytest; no harness gate.
  Report `docs/reports/wp3.15-presets-settings-logging.md` (claims, evidence paths, limits).
  Yield at every round boundary; the dispatcher reads your depth (~250K evaluation, ~400K stop).

## Open questions for CHARC

1. **The app-data location is OS-specific.** Architecture IF-10 says "the platform app-data
   folder"; frame rule 11 makes "an OS-specific path not in AD-23" a STOP; no library is
   granted. Recommended: CHARC approves one resolver in `config/paths.py`: Windows
   `%APPDATA%\Clearwater` (settings, presets, log) and `%LOCALAPPDATA%\Clearwater\cache` for the
   20 GB proxy cache (D71; not roamed); elsewhere `$XDG_CONFIG_HOME` / `$XDG_CACHE_HOME` with the
   home-folder fallbacks. WP3.12 consumes the cache location from this module.
2. **Who closes DR-32, and where.** DR-32 says "refuse non-string keys at any depth in
   `to_dict`/`from_dict`", which live in the frozen `interfaces/parameters.py` (AD-20).
   Recommended: WP3.15 closes it at the config boundary (task 7) without touching interfaces;
   DR-32 is recorded CLOSED for every config and provenance path, with a residual note that a
   direct `ParameterSet.from_dict` caller is unguarded. Alternative: a CHARC decision allowing a
   behaviour-only change in `parameters.py`.
3. **A corrupt or unreadable settings file.** Recommended: rename it beside itself
   (`settings.json.bad-<UTC stamp>`), start from `Settings()`, log a warning; never overwrite it
   silently. A corrupt preset file is listed as unreadable and left untouched.
4. **Starter preset content.** AD-13: both are "the defaults of AD-8 in v1"; the parameter
   names are WP3.2-3.4's and not frozen (the stub's `parameters` is empty). Recommended: each is
   `ParameterSet(method="c3", parameters={})` (IF-9: "a set may be partial and the method
   default applies"), built in code, copied into the user preset folder on first run, renamable
   and deletable like any preset, and not re-created after deletion. Explicit values wait for
   the owner at CP5.
5. **Preset identity.** AD-13's object has no name key and `ParameterSet.from_dict` refuses
   unknown keys, so the name can only be the file stem. Recommended: name = stem; names that are
   not portable file names refused; an import whose name exists gets " (2)", " (3)" ...; export
   to an existing file only when the caller says overwrite (the GUI's confirmation).
6. **Log rotation figures.** N9 gives none. Recommended: 1 MiB per file, 5 backups, level INFO
   by default.
7. **`clearwater.local.toml`.** IF-10 keeps it as "the developer-only override for folders".
   Recommended: the product does not read it in WP3.15 (it is `tools/local_config.py`'s file);
   any developer override of the app-data root is an environment variable read by `paths.py`,
   if CHARC wants one at all.
8. **Value checks beyond types.** `Settings.from_json` checks types only. Recommended: on load,
   `png_bit_depth` in {8, 16}, `quality_level` in {high, standard, draft} (proposed (v0.5.4, CP4)
   item 7; spec 8.2 still says "Standard / High / Very High" as an example), `cache_limit_bytes`
   >= 0; an out-of-range value takes its default with a logged warning; encoder names are not
   checked here (D74, WP3.10).
9. **Dispatch before CP4.** Frame section 5 maps "G12 force-CPU and defaults" (v0.5.4 item 6)
   to WP3.15. The values already live in the frozen `Settings` (WP2.2 round 1), so a CP4 change
   would be an interface change in any case. Recommended: dispatch after WP2.3 as commissioned.
