# WP3.20 — Settings (dispatch brief, FINAL)

**Status:** DRAFT 2026-10-21 for CHARC (orchestrator generation 9, wave 3 tranche B; drafted
against main `9364f8f` plus the DR-44 pre-dispatch contract members); base = the pre-dispatch
main commit named at dispatch. Owner decisions: none inside the package (G12's list and its
first-run defaults were approved with v0.5.4).
- Spec **v0.5.4** (approved by the owner 2026-10-20). Architecture FINAL 1.0 section 3 IF-5
  (`VideoSink.capabilities`, `EncoderCapability`), IF-7, IF-10; AD-9, AD-12, AD-20, AD-25 (a).
  Frame `docs/briefs/wp2.4-phase3-frame.md` sections 1, 2, 4, 5 (section 5 maps "G12
  force-CPU and defaults" to WP3.15, WP3.20 and "D75 names and mapping" to WP3.10, WP3.20).
  WP3.16 report `docs/reports/wp3.16-shell-preview.md` "Contract"; WP3.15 report
  `docs/reports/wp3.15-presets-settings-logging.md` "Public API"; WP3.12 report
  `docs/reports/wp3.12-proxy-cache.md` "Eviction rule (D71)".
- Cell: `implementer-sonnet-high`. Tier **STRONG**.
- Worktree `.worktrees/wp3.20`, branch `wp3.20`, base = the main commit named at dispatch.

**Why.** Plan Phase 3: "WP3.16 owns the main window and defines the places where the other
packages attach their widgets. Each other package owns only its own widget modules. All are
built against stubs of the engines." This package is the settings dialog behind Tools >
Settings: every G12 setting, the D74 encoder options, persistence (G13), and the force-CPU
toggle whose effect the shell's status bar already shows (AD-9).

**Wave-3 GUI file map (the same table is in all four briefs).** Each package creates only its
own modules and tests; none edits an existing file.

| Package | Product modules (NEW, `src/clearwater/gui/`) | Tests (NEW) | Attaches | Message owners |
|---|---|---|---|---|
| WP3.17 | `parameter_panels.py`, `preset_panel.py` | `tests/test_gui_parameter_panels.py`, `tests/test_gui_preset_panel.py` | `Area.PARAMETERS` x3 ("Basic", "Advanced", "Presets") by `install_parameter_panels(window)` | `"parameters"`, `"presets"` |
| WP3.18 | `timeline.py`, `analysis_service.py` | `tests/test_gui_timeline.py`, `tests/test_gui_analysis_service.py` | `Area.TIMELINE` ("Timeline") by `install_timeline(window, analysis=None)` | `"timeline"`, `"analysis"` |
| WP3.19 | `export_panel.py`, `batch_panel.py`, `export_service.py` | `tests/test_gui_export_panel.py`, `tests/test_gui_batch_panel.py` | `Area.JOBS` ("Export", "Batch") by `install_export_panels(window, exports=None)` | `"export"`, `"batch"` |
| WP3.20 | `settings_dialog.py` | `tests/test_gui_settings_dialog.py` | `ShellWindow.set_settings_dialog` by `install_settings_dialog(window)` | `"settings"` |

| Field | Content |
|---|---|
| ID and title | WP3.20 — Settings; plan section 6 Phase 3 row WP3.20 (size S, depends on WP3.16, spec "G12, G13; D74", feeds nothing); module `clearwater.gui` |
| Goal | A settings dialog that edits every G12 setting starting from the first-run defaults, shows unavailable encoder options disabled with a reason, clears the cache and sets its limit off the interface thread, saves the settings through `clearwater.config` (G13) unless the session refused the settings file, and applies them to the session. |
| Spec / decision clauses | Plan bullet "**WP3.20:** the settings listed in G12, with unavailable encoder options shown disabled with a reason." G12 "Settings: output folder, output suffix, PNG bit depth, video encoder, quality level, 10-bit-for-8-bit option, provenance on/off, cache size limit, clear cache, force CPU processing (Advanced; AD-9). First-run defaults (0.5.4): PNG 16-bit; encoder "auto" (NVENC when available, else the software encoder; provenance records the encoder actually used); quality Standard; cache 20 GB; provenance on; force CPU off." G13 "Settings and last-used parameters persist between sessions (D89)." D74 "Unavailable encoder options shown disabled with a reason"; D75 "Video quality set by named levels High / Standard / Draft, mapped per encoder (provisional mapping AD-12: NVENC HEVC cq 18 / 23 / 28, libx265 crf 18 / 23 / 28; verified at WP3.10)"; D76 "Optional 10-bit output for 8-bit sources, off by default"; D34 "Output location: source folder by default; user setting to choose a different output folder"; D36 "Output suffix defaults to `_corrected`, editable in settings"; D22 "Photo output: PNG, user-selectable 8-bit or 16-bit"; D26 "Video encoder: user choice of NVENC or software encoder"; D91 "Clearwater version and parameters embedded in output metadata; on by default, can be turned off"; D71 "Analysis proxies and source-only statistics cached in app data, keyed with a cache format version; default limit 20 GB, editable; oldest removed first; clear-cache button"; D89 "Settings and last-used parameters persist between sessions". Spec 8.2 "Encoder capabilities (including 10-bit support) are detected at startup; unavailable options are shown disabled with a reason (D74)." AD-9 "An Advanced setting "Force CPU processing" overrides device selection; no per-job override." |
| Depends on | WP3.16 merged (accept `a2685cb`): `clearwater.gui.contract` as frozen plus the DR-44 pre-dispatch members (`Message.owner`, `MessagePresenter.clear(..., owner=)`; sha named at dispatch); `ShellWindow.set_settings_dialog(factory)` (opens the dialog window-modally with `QDialog.open()`), `actions.settings`, `Session.settings()`, `set_settings` (re-selects the backend; the status bar shows `"CPU: forced"`), `settings_refusal()`; the shell saves the settings with `last_parameters` once at close (WP3.16 question 9). WP3.15 merged (accept `da54a47`): `save_settings(folder, settings) -> Path` (raises `FormatError`, `ValueError`, `OSError`), `Locations.config_dir`. WP3.13 merged (accept `6dd5a00`): `clearwater.jobs.validate_suffix(suffix)` (raises `ValueError`). IF-10 `Settings` and its defaults (`DEFAULT_OUTPUT_SUFFIX`, `DEFAULT_PNG_BIT_DEPTH` 16, `DEFAULT_VIDEO_ENCODER` "auto", `DEFAULT_QUALITY_LEVEL` "standard", `DEFAULT_CACHE_LIMIT_BYTES` 20 * 10**9; `provenance` True, `force_cpu` False). Stubs: `stubs.StubVideoSink.capabilities()` (one available software encoder `"stub"`, 8 and 10 bit), `stubs.StubProxyCache` (`clear`, `set_limit_bytes`, `limit_bytes`); WP3.10's real capabilities are unmerged (tranche A). |
| Files owned | NEW: `src/clearwater/gui/settings_dialog.py`, `tests/test_gui_settings_dialog.py`, `docs/reports/wp3.20-settings.md`, `docs/proofs/wp3.20-ledger.md`. NOT owned: every existing file under `src/clearwater/gui/` (WP3.16's, including `contract.py`, `__init__.py`, `shell.py`), `tests/gui_support.py` (imported read-only), WP3.16's tests, the WP3.17-3.19 files of the map, `src/clearwater/interfaces/`, `src/clearwater/config/` (DR-34's trigger is NOT met: this package changes no `settings_store.py`), `src/clearwater/jobs/`, `src/clearwater/cache/`, `pyproject.toml`, `uv.lock`, `tests/conftest.py`. |
| Interfaces provided | No frozen interface. `install_settings_dialog(window: ShellWindow) -> None` (registers the factory with `set_settings_dialog`; WP4.3 calls it) and the `SettingsDialogFactory` it registers; the chooser seam of task 3 (injectable folder chooser and confirmation). |
| Interfaces consumed | Contract: `ShellContext` (`session`, `engines.video_sink`, `engines.cache`, `locations`, `jobs`, `messages`, `window`), `Session` (`settings`, `set_settings`, `settings_refusal`, `analysis`, `analysis_changed`), `SettingsDialogFactory`, `ShellWindow.set_settings_dialog`, `Message`. IF-5 `VideoSink.capabilities() -> tuple[EncoderCapability, ...]`, `EncoderCapability` (`name`, `available`, `reason`, `bit_depths`, `hw`); IF-7 `ProxyCache.clear`, `limit_bytes`, `set_limit_bytes`; IF-10 `Settings`; IF-8 `JobResult`. |
| Hardware flags | `gui` on every test that creates a Qt object; no `gpu`, no `footage`, no timing figure. |
| Out of scope | Resolving `"auto"` for an export and recording the encoder used (WP3.14, WP3.10); the D75 per-encoder mapping and its verification (WP3.10, AD-12); detecting encoders at start-up (WP4.3; question 2); creating the real `DiskProxyCache` with the stored limit (WP4.3); `last_parameters` (the shell's, at close); window geometry; `QSettings` or any registry write (AD-25 (a)); a "restore defaults" button (not in G12); validating that the output folder will be writable at export (WP3.14: `MissingFolderError`); any edit to WP3.16's files or `clearwater.config`. |
| Debt and decided items | `Session.settings_refusal()` (WP3.16 accept: "WP3.20 must honour `Session.settings_refusal()`"; contract: "a panel (WP3.20's settings dialog) must not save the settings while this is not None") -- IMPLEMENTS -- question 1; a test that the refused file's bytes are unchanged. G12 force CPU (frame section 5 "G12 force-CPU and defaults | WP3.15, WP3.20") -- CLOSES the toggle (WP3.16 surfaced it in the status bar) -- an Advanced checkbox; a test that setting it makes the status bar show `"CPU: forced"`. G12 first-run defaults -- IMPLEMENTS -- the dialog starts from `Settings()` on first run; a test compares each control to G12's list. D75 names (frame section 5 "D75 names and mapping | WP3.10, WP3.20") -- IMPLEMENTS the names -- High / Standard / Draft shown, stored lower-case as IF-10 says; the mapping is WP3.10's. DR-35 ("WP3.20 validates the suffix when set") -- ADDRESSES its WP3.20 part -- `validate_suffix` on every edit, the reason shown, OK refused while invalid; (a) (a reserved device name formed with the stem) stays WP3.14's (not checkable without the stem). DR-44 (b) -- ADDRESSES (b) for this package -- owner `"settings"` on every present and clear. DR-44 (a), (c) -- not this package's. DR-34 (a)-(c) -- not this package's; must not reopen -- the trigger is "whichever first touches `presets.py`, `settings_store.py` or `log.py`", and this package touches none. DR-37 (a) -- not this package's (`clearwater.core`). DR-43 -- not this package's. V12 -- deferred to v2. |
| Done | Plan 4.5; frame section 2 rules 1-11 apply; ruff check, ruff format --check, mypy strict, full pytest green (in a dispatcher window) with the GUI tests headless; every G12 setting, the first-run defaults, D74, G13 and the settings refusal shown by named tests; Reviewer A converged. |

## Task ladder

1. **Round 0 yield: read and table.** Before product code, write in the ledger: the control
   table (each G12 setting -> `Settings` field -> widget -> displayed values -> stored values ->
   validation -> disabled-with-reason rule); the encoder list rule (question 3) and the
   10-bit rule; the accept sequence (validate, save or not, apply, cache limit job) and its
   failure paths; the clear-cache sequence; the test list; the answers to the open questions;
   the `scripts/cell_depth.py` reading. YIELD for the dispatcher. A choice the brief leaves
   open is a STOP.
2. **The dialog (`settings_dialog.py`).** `settings_dialog(context) -> QDialog`, a new dialog
   per trigger, initialised from `session.settings()`; OK and Cancel (Cancel changes nothing).
   Controls (G12 order):
   - Output folder (D34): "Same folder as the source" or a chosen folder (the chooser seam);
     `output_folder` None or the `Path`.
   - Output suffix (D36): a line edit; `clearwater.jobs.validate_suffix` on every edit; an
     invalid suffix shows the `ValueError` text beside the field and disables OK.
   - PNG bit depth (D22): 16 or 8 (`png_bit_depth`).
   - Video encoder (D26, D74): question 3; an unavailable option is shown disabled with its
     `EncoderCapability.reason` as the item's tool tip and in the text ("NVENC (unavailable:
     <reason>)").
   - Quality level (D75): High / Standard / Draft, stored `"high"`/`"standard"`/`"draft"`.
   - 10-bit output for 8-bit sources (D76): a checkbox, disabled with the reason "<encoder>
     cannot write 10-bit video." when the selected (or, for "auto", the resolved) encoder's
     `bit_depths` lacks 10; a stored True is kept but shown with that reason.
   - Provenance (D91): a checkbox.
   - Cache size limit (D71): whole SI gigabytes (1 GB = 10**9 bytes, as IF-10's
     `DEFAULT_CACHE_LIMIT_BYTES`), minimum 1; a stored value that is not a whole number of GB
     is shown rounded and written back unchanged unless edited.
   - Clear cache: a button (task 4).
   - Advanced group: "Force CPU processing" (AD-9; `force_cpu`).
3. **Accept, persistence and the refusal (G13).** On OK: build `dataclasses.replace(
   session.settings(), <the edited fields>)` (so `last_parameters` is kept as the session
   holds it; the shell writes the current parameters at close). Then:
   - `session.settings_refusal()` is None: `save_settings(context.locations.config_dir,
     new)`; a `FormatError`, `ValueError` or `OSError` becomes an error with owner
     `"settings"` naming the file (the new settings still apply to the session and the close
     save retries); a success clears this owner's errors.
   - not None: question 1.
   - `session.set_settings(new)` (the shell re-selects the backend; `force_cpu` shows as
     `"CPU: forced"`).
   - When `cache_limit_bytes` changed: `engines.cache.set_limit_bytes(n)` in a job through
     `context.jobs` (it may evict on disk); a failure is an error with owner `"settings"`.
   The chooser seam: `SettingsChoosers` (protocol) `choose_folder(initial: Path | None) -> Path
   | None` and `confirm(text) -> bool`, Qt defaults (`QFileDialog.getExistingDirectory`,
   `QMessageBox`), injectable so no test blocks on a modal dialog.
4. **Clear cache (D71).** The button asks for confirmation, then runs `engines.cache.clear()`
   in a job (the real cache may wait up to 5 s for readers, WP3.12 report); the button shows
   "Clearing..." and is disabled until `on_done`; success shows "Cache cleared." in the dialog
   when it is still open; a failure is an error with owner `"settings"`. While
   `session.analysis().phase == "running"` the button is disabled with the reason "The cache
   cannot be cleared while a clip is being analysed." (question 4), updated on
   `analysis_changed`.
5. **Tests** (headless, `gui`-marked, through `tests/gui_support.make_window`, a `Locations`
   under `tmp_path`, stub engines with a test `VideoSink` whose `capabilities()` returns a
   chosen tuple, e.g. an unavailable hardware `"hevc_nvenc"` with a reason and an available
   software `"libx265"` 8/10-bit; the real app-data folder never resolved):
   - first run: on `Settings()` every control shows G12's first-run default (PNG 16-bit,
     encoder "auto", quality Standard, cache 20 GB, provenance on, force CPU off; suffix
     `_corrected`, output folder "Same folder as the source", 10-bit off);
   - each G12 setting round-trips: edit, OK, the saved `settings.json` re-read by
     `load_settings` and `session.settings()` both carry it; `last_parameters` unchanged;
   - G13: a second `MainWindow` on the same `Locations` opens the dialog with the saved values;
   - D74: the unavailable encoder is disabled with its reason; the 10-bit checkbox is disabled
     with the reason for an 8-bit-only encoder and enabled for one with 10;
   - DR-35: an invalid suffix (a separator, `..`, a trailing dot, the temporary marker)
     disables OK with the `ValueError` text; a valid one enables it;
   - AD-9: force CPU on -> `session.backend()` and the status bar read `"CPU: forced"`;
   - the refusal: with a settings file of an unsupported `format_version` at start-up, OK
     applies to the session and leaves the file's bytes unchanged, and the dialog shows the
     refusal text;
   - D71: clear cache runs off the interface thread, calls `clear()` once after a confirmation,
     nothing on decline; disabled with the reason while an analysis runs; a limit change calls
     `set_limit_bytes(n)` with n in bytes;
   - DR-44 (b): an error with owner `"shell.preview"` survives a successful save;
   - planted wrong implementations fail by name: a save while `settings_refusal()` is not
     None; `last_parameters` dropped by the save; `clear()` on the interface thread; an
     unavailable encoder selectable;
   - dependency rule: WP3.16's `tests/test_gui_deps.py` covers the new module (run it, do not
     change it).

## Declared operating envelope

Windows 11; Python 3.12; PySide6-Essentials and pytest-qt as locked; one Clearwater window;
the settings file in the local app-data folder (`save_settings` is a small atomic write on the
interface thread); the cache operations through IF-7 off the interface thread; encoder
capabilities from the injected sink (the stub in tests); tests headless on `offscreen`. Out of
envelope: a settings folder on a slow network share; a real sink whose `capabilities()` blocks
(question 2); several windows or processes writing the settings file; other operating systems
(portable, N1, not run there).

## Review loop (Reviewer A), per `docs/review-gate-clearwater.md` Part 1

- Tier **STRONG**, run by you at your seat to convergence; five-round gate. Evidence
  `C:\Users\rwsmy\clearwater-review-evidence\wp3.20\rN\`; ledger `docs/proofs/wp3.20-ledger.md`.
  Copy the runner and prompt shape from `C:\Users\rwsmy\clearwater-review-evidence\wp3.16\r4\`
  (`run_review.sh`, `review-prompt.md`; the round also keeps `probe.txt`, `review-diff.txt`,
  `review.txt`, `adjudication.md`, `md5sums.txt`, `test-summary.txt` as there); the reviewer
  excludes `docs/proofs` with `--glob '!docs/proofs/**'`.
- **WHAT TO EXAMINE:**
  - every G12 field read from and written to the right `Settings` field, with the right unit
    and stored form (quality lower-case; cache bytes; folder None vs a path);
  - no settings write while `settings_refusal()` is not None; `last_parameters` never lost;
    writes only through `save_settings(locations.config_dir, ...)`; no `QSettings`;
  - D74: no unavailable option selectable; the reason shown; the 10-bit rule;
  - the cache calls off the interface thread and guarded during analysis;
  - message owners (DR-44 (b)); nothing in WP3.16's files, `config/` or `interfaces/` changed.
- Reviewer B is the orchestrator's seat pass on the merge candidate.

## Notes for the cell

- **Yields.** Round 0: read and table, then YIELD before product code. After each review
  round: END YOUR TURN as soon as round N's verdict is adjudicated, BEFORE remediating ("make
  NO change in the turn that adjudicates a round"). Report the `scripts/cell_depth.py` reading
  at every yield; ~250K is the evaluation point (past it, "REVIEW ONLY this turn" when told),
  ~400K STOP.
- **Full-pytest windows.** The full suite (about 3559 tests, about 15 min) runs ONLY in a
  window the dispatcher grants by message, in the background with `QT_QPA_PLATFORM=offscreen`
  and output to a file under `work/`; send `WINDOW RELEASED: <summary>` when it finishes. Never
  two heavy jobs at once. Inner loops run only your own tests and `tests/test_gui_deps.py`.
- **Return report** = your FINAL message, under about 70 lines (`docs/dispatch-recipe.md`
  section 4): the module and public names, the control table, the encoder and 10-bit rules,
  the accept sequence, the gates, the Reviewer A rounds and verdict, open items.
- **STOP for:** any change needed in `src/clearwater/interfaces/` (AD-20) or in
  `clearwater.gui.contract`; a change to any existing file (including `clearwater.config`); a
  dependency; any OS-specific code (`QSettings` included); a write outside the injected
  `Locations`; a test that cannot run headless; the round-0 table showing a choice the brief
  left open.
- **Working rules:** `uv sync`. Commit inside the worktree by pathspec with
  `git -c core.autocrlf=false commit -m "feat(wp3.20): ..." -- <paths>`, with a
  `Co-Authored-By:` footer naming your model; never `git stash` (use a WIP commit or a scratch
  copy). Never a bare `cd`. Never post to a mailbox. Gates: ruff check, ruff format --check,
  mypy strict, full pytest (in a window); no harness gate. Report `docs/reports/wp3.20-settings.md`
  (claims, evidence paths, limits, and "Consumer notes" for WP3.14 and WP4.3: the "auto"
  resolution rule the dialog assumes). The footage folder is never used. GoPro data is out of
  scope: no `gpmd`, IMU or GPS data.

## Rulings (CHARC `53d1d906e47fe2c9`, 2026-10-21)

Approved as drafted: every recommended answer below is the ruling, with these amendments and readings. Where a ruling here and the task ladder or a question differ, the ruling governs.

- **Q3 AMENDED:** WP3.10's `resolve_encoder` is the ONE "auto" rule. This dialog calls it (a stub with the same signature until WP3.10 is on main) and does not restate the rule; the remainder of Q3 (list order, disabled unavailable encoders with the reason, a stored encoder no longer reported kept and shown unavailable) stands.
- **Q5:** D75's names govern over the 8.2 example. **Q1:** OK while the settings file is refused is session-only. **Q4:** Clear cache is disabled while analysis runs.
- **DR-44 members** as landed on main (the pre-dispatch commit).

## Questions for CHARC (recommended answer first)

1. **OK while the settings file was refused.** The contract forbids saving while
   `settings_refusal()` is not None. Recommended: the dialog opens with the refusal's text at
   the top ("Changes apply to this session only; <file> was left unchanged."), OK applies the
   settings to the session with `set_settings` and writes nothing. Alternative: the dialog is
   read-only (OK disabled) for the session.
2. **When encoder capabilities are read.** Spec 8.2: "detected at startup"; start-up detection
   is WP4.3's ("encoder and graphics-card detection"); a real `capabilities()` may run FFmpeg.
   Recommended: `install_settings_dialog` starts one job that calls
   `engines.video_sink.capabilities()` and caches the tuple for the session; the dialog shows
   the cached list, or the encoder control disabled with "Detecting encoders..." until it
   arrives; a failure leaves only "auto" with the failure as the reason. Alternative: call it
   on the interface thread each time the dialog opens (fine for the stub, not for WP3.10's).
3. **The encoder list and "auto".** Recommended: "Automatic (NVENC when available)" first,
   stored `"auto"`; then one item per `EncoderCapability` in the order the sink returns,
   unavailable ones disabled with the reason (D74). For the 10-bit rule, "auto" resolves as
   IF-10 says ("NVENC HEVC when the D74 capability report says available, else libx265"): the
   first available capability with `hw` True, else the first available one with `hw` False;
   WP3.14's brief must use the same rule. A stored encoder that the sink no longer reports is
   kept, shown as unavailable ("not found on this computer"), and written back unchanged unless
   the user picks another. Alternative: a stored unavailable encoder is replaced by "auto" when
   the dialog opens.
4. **Clear cache during an analysis.** `ProxyCache.clear` removes every entry, including the one
   an analysis is writing. Recommended: disabled with a reason while the phase is "running"
   (task 4). Alternative: allowed, and WP3.18's analysis sees a store error.
5. **Quality names in spec 8.2.** 8.2 says "named levels (e.g., Standard / High / Very High)";
   D75 (v0.5.4) names High / Standard / Draft. Recommended: D75 governs (8.2 gives an example);
   no spec change from this package; noted for the next spec revision.
6. **Cross-brief items** (the same in WP3.17-3.20): `clearwater/gui/__init__.py` is not edited
   (X-W3a); the test helpers read-only (X-W3b); the capturing test presenter already takes
   `owner` (the DR-44 pre-dispatch commit). Recommended as in the WP3.17 brief,
   questions 1 and 3.
7. **Reviewer tier.** Recommended: STRONG (review-gate Part 1: "`strong` ... for every
   product-code package"), five-round gate.
