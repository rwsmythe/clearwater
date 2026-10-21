# WP3.17 — Parameter panels and presets (dispatch brief, FINAL)

**Status:** DRAFT 2026-10-21 for CHARC (orchestrator generation 9, wave 3 tranche B; drafted
against main `9364f8f` plus the DR-44 pre-dispatch contract members); base = the pre-dispatch
main commit named at dispatch. Owner decisions: none inside the package (the starter-preset
VALUES are the owner's at CP5, AD-13; this package shows whatever the store holds).
- Spec **v0.5.4** (approved by the owner 2026-10-20). Architecture FINAL 1.0 section 3 IF-3,
  IF-9, IF-10, section 7 ("PySide6 GUI with the Basic panel listing c3 first (6.3)"); AD-8,
  AD-13, AD-18, AD-20, AD-25 (a). Frame `docs/briefs/wp2.4-phase3-frame.md` sections 1, 2, 4, 5.
  WP3.16 report `docs/reports/wp3.16-shell-preview.md` "Contract"; WP3.15 report
  `docs/reports/wp3.15-presets-settings-logging.md` "Public API".
- Cell: `implementer-sonnet-high`. Tier **STRONG**.
- Worktree `.worktrees/wp3.17`, branch `wp3.17`, base = the main commit named at dispatch.

**Why.** Plan Phase 3: "WP3.16 owns the main window and defines the places where the other
packages attach their widgets. Each other package owns only its own widget modules. All are
built against stubs of the engines." This package gives the user the correction parameters
(G3) and the presets (G6). It runs in parallel with WP3.18, WP3.19 and WP3.20; the four touch
disjoint files (the file map below).

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
| ID and title | WP3.17 — Parameter panels and presets; plan section 6 Phase 3 row WP3.17 (size M, depends on WP3.16, spec "G3, G6; D17", feeds V13); module `clearwater.gui` (plan 8.1: "PySide6 interface", WP3.16–WP3.20) |
| Goal | A Basic and an Advanced panel generated from the selected method's IF-3 parameter schema, with the method selector, that change the session's parameters live; and a Presets panel that saves, loads, renames, deletes, imports and exports presets through WP3.15's `PresetStore`. |
| Spec / decision clauses | Plan bullet "**WP3.17:** Basic and Advanced panels generated from the method's parameter schema, including controls that hide by method (D49); preset save, load, rename, delete, import and export." G3 "Parameter controls (Section 6.7) generated from each method's parameter schema, in Basic and Advanced panels. Preview updates live at screen resolution while adjusting; exact at 1:1 zoom." G6 "Presets: save, load, rename, delete, import from file, export to file. Starter presets included." D17 "All parameters exposed; technical parameters in an Advanced panel"; D49 "Gain cap does not apply to 3C; cap controls hidden when 3C is selected"; D16 "Both channel-compensation methods (Ancuti 2018 and 3C) included, user-selectable; 3C is the default"; D37 "Presets stored in the user's app-data folder; can be exported and imported as files"; D38 "Clearwater ships with starter presets"; D90 "Preset files record their method and a format version"; D52 "Separate red and blue gain caps" (nullable, AD-20 amendment). Spec 10.1 "**Parameter schema:** names, types, ranges, defaults, and Basic/Advanced placement, so the GUI is method-agnostic." Spec 6.7 Basic panel item "Blend with original (0–100%; 0 = fully corrected, 100 = the original, 0.5.4 AD-8)" (question 4). AD-8 ""Blend with original": 0.0 = fully corrected, 1.0 = the original". Feeds V13 "export then import reproduces identical parameters, method and version." (plan: built in WP3.15, WP3.17; completed in WP5.1). |
| Depends on | WP3.16 merged (accept `a2685cb`): `clearwater.gui.contract` as frozen, plus the DR-44 pre-dispatch members (`Message.owner`, `MessagePresenter.clear(severity=None, *, owner=None)`; committed on main by the orchestrator before dispatch, sha named at dispatch). WP3.15 merged (accept `da54a47`): `PresetStore` (`list_presets`, `load`, `save(name, parameter_set, *, overwrite=False)`, `rename`, `delete`, `import_preset(source, schemas, *, name=None)`, `export_preset(name, destination, *, overwrite=False)`), `PresetEntry`, `PresetImportResult` (`dropped_keys`, `provenance_dropped`), `PresetError`, `PresetImportError` (`problems`), `UnsupportedPresetVersionError`, `validate_preset_name`, `new_parameter_set(method, parameters, *, now=None)`, `STARTER_METHOD = "c3"` (`src/clearwater/config/presets.py`). WP2.2 (IF-3, IF-9 frozen, `b288533`). The method schema: NO real method declares parameters on main (`stubs.StubCorrectionMethod.parameters` is empty; WP3.4 delivers the c3/ancuti2018 schema in this wave): every test uses test methods declared in the test modules (task 5). |
| Files owned | NEW: `src/clearwater/gui/parameter_panels.py`, `src/clearwater/gui/preset_panel.py`, `tests/test_gui_parameter_panels.py`, `tests/test_gui_preset_panel.py`, `docs/reports/wp3.17-parameter-panels-presets.md`, `docs/proofs/wp3.17-ledger.md`. NOT owned: every existing file under `src/clearwater/gui/` (WP3.16's, including `contract.py` and `__init__.py`, question 1), `tests/gui_support.py` (imported read-only), WP3.16's `tests/test_gui_*.py`, the WP3.18-3.20 files of the map, `src/clearwater/interfaces/`, `src/clearwater/config/` (DR-34's trigger is NOT met: this package changes no `presets.py`), `pyproject.toml`, `uv.lock` (no dependency grant: PySide6-Essentials and pytest-qt are already locked), `tests/conftest.py`. |
| Interfaces provided | No frozen interface. `install_parameter_panels(window: ShellWindow) -> None` (attaches the three panels; WP4.3 calls it) and the three factories `basic_panel`, `advanced_panel`, `preset_panel` (each a `PanelFactory`); the dialogs seam of task 4 (`PresetDialogs` protocol, a Qt default, injectable). |
| Interfaces consumed | Contract: `ShellContext` (`session`, `engines`, `presets`, `messages`, `window`), `Session` (`parameters`, `method`, `set_parameters`, `parameters_changed`), `Engines.methods`, `Area.PARAMETERS`, `ShellWindow.attach`, `Message`, `MessagePresenter`. IF-3 `CorrectionMethod` (`id`, `label`, `parameters`), `Parameter` (`name`, `type`, `default`, `minimum`, `maximum`, `choices`, `panel`, `label`, `help`, `nullable`). IF-9 `ParameterSet`, `validate_parameter_set(parameter_set, method_id, parameters) -> list[ParameterProblem]`. PySide6 QtWidgets/QtCore; pytest-qt in tests. |
| Hardware flags | `gui` on every test that creates a Qt object; no `gpu`, no `footage`, no timing figure. |
| Out of scope | The preview, its live re-render and 1:1 exactness (WP3.16 already re-renders on `parameters_changed`, latest wins); the real c3/ancuti2018 schema and its defaults (WP3.4; AD-8 values live there); the starter preset values (AD-13, CP5); changing `clearwater.config` (DR-34); a "reset to defaults" button (not in G3/G6); undo/redo; per-parameter units other than the schema's own values (question 4); saving settings or `last_parameters` (the shell saves at close, WP3.16 question 9; this package never calls `save_settings`); the timeline, export, batch and settings panels (WP3.18-3.20); any edit to WP3.16's files. |
| Debt and decided items | DR-44 (b) ("`MessagePresenter.clear(severity)` has no owner/identity, so one action's success clears other panels' errors"; trigger "before the WP3.17-3.20 briefs freeze (an additive message owner)") -- ADDRESSES (b) for this package -- every `Message` it presents carries owner `"parameters"` or `"presets"`, every `clear` passes its own owner, and a test shows another owner's error surviving this package's success. DR-44 (a), (c) -- not this package's (WP3.18; WP4.3). DR-34 (a)-(c) -- not this package's; must not reopen -- the trigger is "WP3.17 or WP3.20, whichever first touches `presets.py`, `settings_store.py` or `log.py`", and this package touches none; for (a) the panel calls `save(..., overwrite=True)` only after the user confirmed a listed same-name preset. DR-32 -- must not reopen -- keys are checked by the store. DR-43 -- not this package's (reader-side). V12 -- deferred to v2 (no chapter review). `Session.settings_refusal()` -- not used: this package writes no settings. |
| Done | Plan 4.5; frame section 2 rules 1-11 apply; ruff check, ruff format --check, mypy strict, full pytest green (in a dispatcher window) with the GUI tests headless; every G6 operation and every IF-3 parameter type shown by a named test; Reviewer A converged. |

## Task ladder

1. **Round 0 yield: read and table.** Before product code, write in the ledger: the widget
   table (each IF-3 `type`, bounded or not, nullable or not -> widget, range, step, decimals,
   the signal that commits a value); the method-switch rule (question 2); the preset operation
   table (operation -> `PresetStore` call -> each exception -> the `Message` text and severity
   -> what the list shows after); the `PresetDialogs` seam; the test list; the answers to the
   open questions; the `scripts/cell_depth.py` reading. YIELD for the dispatcher. A choice the
   brief leaves open is a STOP.
2. **The Basic and Advanced panels (`parameter_panels.py`).**
   - `basic_panel(context)` and `advanced_panel(context)` build a `QWidget` each. The Basic
     panel starts with a method selector: a `QComboBox` over `context.engines.methods` in
     mapping order (the first is the default, architecture 7 "listing c3 first"), showing each
     `method.label`, selecting `session.parameters().method`.
   - Below it, one control per `Parameter` of `session.method().parameters` whose `panel` is
     `"basic"` (Advanced: `"advanced"`), in declaration order, labelled `Parameter.label`, tool
     tip `Parameter.help`. Every parameter of the schema gets a control in exactly one panel
     (D17). An empty Advanced panel shows one line: "This method has no advanced parameters."
   - Widgets (fix the exact numbers in the round-0 table): `float` -> `QDoubleSpinBox`, plus a
     `QSlider` mapped linearly when both bounds are set; `int` -> `QSpinBox`, plus a slider when
     both bounds are set; `bool` -> `QCheckBox`; `enum` -> `QComboBox` over `choices`;
     `nullable` (or a None default) -> a leading `QCheckBox` "On" whose unchecked state is None
     and disables the value widget (D52 caps). Spin boxes use `setKeyboardTracking(False)`.
   - A user edit commits at once: `session.set_parameters(dataclasses.replace(current,
     parameters={**current.parameters, name: value}))` (the set stays partial: names never
     edited keep the method default, IF-9). Slider drags commit on every value (G3 "Preview
     updates live"; the shell's preview is latest-wins).
   - On `parameters_changed` the panels rebuild when the method changed (D49: controls hide by
     method because they come from the selected method's schema only) and otherwise update
     their widgets under `QSignalBlocker`, so a programmatic change never re-emits.
   - A method switch from the selector follows question 2.
3. **The Presets panel (`preset_panel.py`, G6).** A list of `context.presets.list_presets()`,
   refreshed after every operation and when the panel is shown. An entry with `error` set is
   shown disabled with the error as its tool tip ("made by a newer Clearwater" when
   `unsupported_version`); no operation here acts on it (the store refuses unreadable files and
   leaves them untouched).
   Buttons and their behaviour:
   - **Load:** `presets.load(name)`; a method not in `engines.methods` is an error naming the
     preset and the method (the starters are `"c3"`, `STARTER_METHOD`); then
     `validate_parameter_set(ps, ps.method, engines.methods[ps.method].parameters)`: any
     problem is an error listing every `ParameterProblem.message`, and nothing is applied;
     else `session.set_parameters(ps)`.
   - **Save as:** a name from the dialogs seam, checked by `validate_preset_name`; when a
     listed entry's name matches it case-insensitively (the store's rule: NFC then
     `casefold()`), ask to confirm and call `save(name, session.parameters(), overwrite=True)`,
     else `save(..., overwrite=False)`.
   - **Rename** (new name from the seam), **Delete** (after confirmation), **Import** (an
     open-file dialog filtered to `*.json`; `presets.import_preset(path, {mid:
     m.parameters for mid, m in engines.methods.items()})`; a `PresetImportResult` with
     `provenance_dropped` gives a warning naming `dropped_keys`; the stored name is shown when it
     differs from the file's stem), **Export** (a save-file dialog; when the target exists,
     confirm and pass `overwrite=True`).
   - Every `PresetError` (and `PresetImportError` with its `problems`, `OSError`,
     `FormatError`) becomes a `Message("error", text, path, owner="presets")`; a successful
     operation calls `context.messages.clear("error", owner="presets")`. No exception escapes
     a slot.
4. **The dialogs seam.** `PresetDialogs` (protocol): `ask_name(title, initial) -> str | None`,
   `confirm(text) -> bool`, `open_file() -> Path | None`, `save_file(initial_name) -> Path |
   None`; a Qt implementation (`QInputDialog`, `QMessageBox`, `QFileDialog`, parented to the
   window); `preset_panel` takes it as a keyword with the Qt default, so tests pass a scripted
   fake and no test ever blocks on a modal dialog.
5. **Tests** (headless, `gui`-marked, through `tests/gui_support.make_window` and a
   `Locations` under `tmp_path`; the real app-data folder never resolved):
   - test methods in the test module: one with every `type` (bounded and unbounded `float`
     and `int`, `bool`, `enum`, a nullable `float`) in both panels, and two methods with ids
     `"c3"` and `"ancuti2018"` where only the second declares the caps (D49 shape);
   - generation: one control per parameter, in the right panel, label and tool tip from the
     schema; the selector lists the methods in `engines.methods` order;
   - live: an edit calls `set_parameters` once with exactly the edited name added; a slider
     drag commits each value; an external `set_parameters` updates the widgets without
     re-emitting; a nullable unchecked gives None;
   - D49: switching to `"c3"` removes the cap controls, back to `"ancuti2018"` shows them;
     question 2's carry-over rule shown;
   - G6: each of save, save over (confirmed and declined), load, rename, delete, import
     (valid; unknown method; schema problems; a provenance sidecar), export (new, over an
     existing file) once; an unreadable and a newer-version file listed disabled; the starter
     presets listed and loadable with the `"c3"` test method;
   - V13 leg: save -> export -> import -> load gives a `ParameterSet` with the same `method`,
     `parameters` and `app_version`;
   - DR-44 (b): an error presented with owner `"shell.preview"` survives a successful preset
     load; this package's own error is cleared by its next success;
   - planted wrong implementations fail by name: a preset applied despite a schema problem;
     `overwrite=True` without a confirmation; a programmatic update that re-emits;
   - dependency rule: WP3.16's `tests/test_gui_deps.py` globs every module of
     `clearwater.gui` and so covers the two new modules; run it, do not change it.

## Declared operating envelope

Windows 11; Python 3.12; PySide6-Essentials and pytest-qt as locked; one Clearwater window;
methods with up to about 30 parameters; presets in the local app-data folder (each at most
1 MiB, the store's cap), so preset operations run on the interface thread; tests headless on
the `offscreen` platform. Out of envelope: a preset folder on a slow network share; several
windows; screen readers and accessibility (not in the spec); other operating systems
(portable, N1, not run there).

## Review loop (Reviewer A), per `docs/review-gate-clearwater.md` Part 1

- Tier **STRONG**, run by you at your seat to convergence; five-round gate. Evidence
  `C:\Users\rwsmy\clearwater-review-evidence\wp3.17\rN\`; ledger `docs/proofs/wp3.17-ledger.md`.
  Copy the runner and prompt shape from `C:\Users\rwsmy\clearwater-review-evidence\wp3.16\r4\`
  (`run_review.sh`, `review-prompt.md`; the round also keeps `probe.txt`, `review-diff.txt`,
  `review.txt`, `adjudication.md`, `md5sums.txt`, `test-summary.txt` as there); the reviewer
  excludes `docs/proofs` with `--glob '!docs/proofs/**'`.
- **WHAT TO EXAMINE:**
  - schema fidelity: every parameter shown once, in its panel, with its range, choices and
    nullability; no value outside the schema can be committed;
  - signal hygiene: no feedback loop between `parameters_changed` and the widgets; a method
    switch leaves no control of the old method;
  - every preset operation against `PresetStore`'s documented exceptions; no overwrite
    without a confirmation; nothing applied after a failed validation;
  - message owners on every present and clear (DR-44 (b));
  - the contract used as documented; nothing in WP3.16's files, `config/` or `interfaces/`
    changed; no `QSettings`; no write outside the injected `Locations` and the user's chosen
    export file.
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
  section 4): the module list and public names, the widget table, the method-switch rule, the
  preset operation table, the gates, the Reviewer A rounds and verdict, open items.
- **STOP for:** any change needed in `src/clearwater/interfaces/` (AD-20) or in
  `clearwater.gui.contract` (a CHARC ruling since the WP3.16 accept); a change to any existing
  file (WP3.16's modules and tests, `tests/gui_support.py`, `clearwater.config`); a dependency;
  any OS-specific code; a test that cannot run headless; the round-0 table showing a choice
  the brief left open.
- **Working rules:** `uv sync`. Commit inside the worktree by pathspec with
  `git -c core.autocrlf=false commit -m "feat(wp3.17): ..." -- <paths>`, with a
  `Co-Authored-By:` footer naming your model; never `git stash` (shared stack: use a WIP
  commit or a scratch copy). Never a bare `cd`. Never post to a mailbox. Gates: ruff check,
  ruff format --check, mypy strict, full pytest (in a window); no harness gate. Report
  `docs/reports/wp3.17-parameter-panels-presets.md` (claims, evidence paths, limits, and a
  "Consumer notes" section for WP3.4 and WP4.3). The footage folder is not used; outputs only
  under `tmp_path` or `work/`. GoPro data is out of scope: no `gpmd`, IMU or GPS data.

## Rulings (CHARC `53d1d906e47fe2c9`, 2026-10-21)

Approved as drafted: every recommended answer below is the ruling, with these amendments and readings. Where a ruling here and the task ladder or a question differ, the ruling governs.

- **Blend with original (WP3.4 and WP3.17):** the spec defines the control as 0-100 %. The SCHEMA value is the user-facing value: WP3.4 defines `blend_with_original` as a float 0..100, label "Blend with original (%)", neutral 0 (AD-8), and the method converts to 0-1 internally; presets store 0-100. No IF-3 unit field. WP3.17 shows the schema value with the label; nothing is special-cased.
- **DR-44 members** as landed on main (the pre-dispatch commit); the four GUI briefs are written against those names.

## Questions for CHARC (recommended answer first)

1. **`clearwater/gui/__init__.py` exports (X-W3a, cross-brief WP3.17-3.20).** The WP3.16 brief
   let the panel packages "append exports, nothing else"; four parallel worktrees appending
   to one `__all__` collide at every rebase. Recommended: none of the four edits
   `__init__.py`; consumers import by module path (`clearwater.gui.parameter_panels`); WP4.3
   adds the exports it wants. Alternative: each appends and the second to merge rebases.
2. **The method switch.** Recommended: switching method builds
   `new_parameter_set(new_id, carried)` where `carried` holds each current value whose name
   exists in the new method's schema and passes `validate_parameter_set` for it (for example
   the white-balance strength survives c3 -> ancuti2018 -> c3); every other name is dropped,
   so it takes the new method's default. Alternative: always the new method's defaults
   (`new_parameter_set(new_id, {})`).
3. **Reading WP3.16's helper modules (X-W3b, cross-brief).** Recommended: the panels may
   import, read-only, WP3.16's pure helpers that the contract does not carry
   (`clearwater.gui.messages.ascii_text` and `file_name` here; `sources.route`/`file_filter`
   for WP3.19; `imaging.downscale`/`statistics_factor` for WP3.18; `engines.stub_engines`/
   `stub_probe` in tests) and nothing else; state stays reachable only through the contract.
   Alternative: contract only, each package re-implements what it needs.
4. **"Blend with original (0–100%)".** Spec 6.7 shows a percentage; AD-8 and the IF-3 schema
   carry 0.0-1.0, and IF-3 has no unit field, so a method-agnostic GUI cannot know to show
   percent. Recommended: the panel shows the schema's value and range as declared (0.00-1.00
   with the schema's label); WP3.4's label may say "(0 = corrected, 1 = original)"; a percent
   display would need an IF-3 unit field (AD-20, a later ruling). Alternative: a rule
   "a float bounded exactly [0, 1] whose name starts with `blend` is shown as a percentage"
   (name-specific, against 10.1's "method-agnostic").
5. **The test presenter (cross-brief; settled, for the record).** The DR-44 pre-dispatch
   commit extends `tests/gui_support.CapturingPresenter.clear(severity=None, *, owner=None)`,
   so the four packages share one capturing presenter and import it read-only. No ruling
   needed unless that commit changes.
6. **Reviewer tier.** Recommended: STRONG (review-gate Part 1: "`strong` ... for every
   product-code package"), five-round gate, as in every wave-2 brief.
