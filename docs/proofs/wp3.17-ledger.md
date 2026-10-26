# WP3.17 ledger (parameter panels and presets)

Cell: implementer-sonnet-high, seat 1 (tier STRONG). Worktree `.worktrees/wp3.17`, branch `wp3.17`,
base `718324b`. Spec v0.5.4, architecture FINAL 1.0. Brief `docs/briefs/wp3.17-brief.md` (FINAL;
CHARC rulings `53d1d906e47fe2c9`: every recommended answer is the ruling; blend ruling: the schema
value is the user-facing value, shown as declared).

## Cumulative round ledger

| Round | Date | Blocking (crit/maj) | Minor | In/out envelope | NEW/REOPENED | Reverts | Fix kind | Transport | Depth |
|---|---|---|---|---|---|---|---|---|---|
| 0 (design) | 2026-10-26 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 123,285 (dispatcher, round-0 yield) |

## Round 0: the design table (brief task 1)

No product code exists. Everything below is what I will build unless the dispatcher rules otherwise.

### 1. Anchors re-grounded at `718324b`

All brief anchors hold. Checked against the files: `Session.parameters/method/set_parameters/
parameters_changed`, `Engines.methods` (mapping order, first = default), `Area.PARAMETERS`,
`ShellWindow.attach(area, factory, *, title)` (several PARAMETERS panels are tabified in attach
order), `Message(severity, text, path, owner)`, `MessagePresenter.clear(severity=None, *, owner=None)`;
`Parameter` (+ `neutral`, which the panels do not use); `validate_parameter_set(ps, method_id,
parameters) -> list[ParameterProblem]`; `PresetStore` methods, `PresetEntry`, `PresetImportResult`,
the four error classes, `validate_preset_name`, `new_parameter_set`, `STARTER_METHOD`;
`tests/gui_support.CapturingPresenter.clear(severity, *, owner)` already honours the owner;
`messages.ascii_text` and `messages.file_name` exist (ruling Q3). Notes:
- `ShellSession.set_parameters` raises ValueError only for a method not in `engines.methods`.
- `tests/test_gui_deps.py` forbids, in every `clearwater.gui` module, an import of
  `clearwater.methods`/`cupy`, the name `QSettings`, and the code names `home`/`environ`/`APPDATA`
  and the like; the two new modules use none of them.
- `normalisation_low < normalisation_high` is a relation no `Parameter` bound can say; see STOP-1.

### 2. Modules and public names

| Module | Public names |
|---|---|
| `parameter_panels.py` | `BasicPanel`, `AdvancedPanel` (QWidget subclasses; `controls()` -> name -> row, for tests and WP4.3), `basic_panel(context)`, `advanced_panel(context)` (PanelFactory), `install_parameter_panels(window, *, dialogs=None)` (attaches "Basic", "Advanced", "Presets" in `Area.PARAMETERS`; the `dialogs` keyword is an addition to the brief's signature so a test can inject the scripted fake through the installer), constants `OWNER_PARAMETERS = "parameters"`, `SLIDER_STEPS = 1000` |
| `preset_panel.py` | `PresetPanel` (QWidget), `preset_panel(context, *, dialogs=None)` (PanelFactory when called with the context alone), `PresetDialogs` (Protocol), `QtPresetDialogs(parent)`, constant `OWNER_PRESETS = "presets"` |

Nothing else is created or edited. `clearwater/gui/__init__.py` is not touched (Q1).

### 3. Widget table (each IF-3 `type`; commit signal)

Range = the schema's. "Both bounds" = `minimum` and `maximum` both not None. A missing bound of a
bounded-on-one-side or unbounded number becomes the display limit +/-1e9 (float) or +/-(2^31-1)
(int, `QSpinBox`'s own limit); a schema bound beyond the display limit is clamped to it (limit,
never reached by the real schemas). A programmatic update never commits.

| Type | Bounds | Widget(s) | Range | Step | Decimals | Commit signal |
|---|---|---|---|---|---|---|
| `float` | both | `QDoubleSpinBox` + `QSlider` (horizontal, 0..1000, linear: `value = min + pos*(max-min)/1000`) | `[min, max]` | `10**round(log10(span/100))`, at least `10**-decimals` (span 2 -> 0.01; span 100 -> 1) | `max(ceil(-log10(span/1000)), decimals of repr(default), repr(min), repr(max))` clamped to 2..6 | spin `valueChanged` (keyboard tracking off: Enter, focus out, arrows, wheel) and slider `valueChanged` (every value of a drag; tracking on); the slider sets the spin (blocked) and the commit reads `spin.value()`, so a committed value is always inside `[min, max]` and rounded to the decimals |
| `float` | one or none | `QDoubleSpinBox` only | `[min or -1e9, max or 1e9]` | `10**(floor(log10(abs(default)))-1)` for a nonzero default, else 0.1; at least `10**-decimals` | `max(3, decimals of repr(default))` clamped to 3..6 | spin `valueChanged` |
| `int` | both | `QSpinBox` + `QSlider` over `[min, max]` directly | `[min, max]` | 1 (slider page step: `max(1, span//10)`) | n/a | spin and slider `valueChanged` (as float) |
| `int` | one or none | `QSpinBox` only | `[min or -(2^31-1), max or 2^31-1]` | 1 | n/a | spin `valueChanged` |
| `bool` | n/a | `QCheckBox` (empty text; the label is the form label) | n/a | n/a | n/a | `toggled` |
| `enum` | n/a | `QComboBox` over `choices` (item text = choice; no choices = an empty, disabled box) | n/a | n/a | n/a | `currentIndexChanged` (blocked on programmatic updates) |
| any, `nullable` or `default is None` | as its type | a leading `QCheckBox` "On" plus the type's widgets; unchecked = value `None` and the value widgets disabled; checking it commits the value widget's last value (the current value if it was set, else the default, else the minimum / first choice / False) | as its type | | | "On" `toggled` |

Every row: label = `Parameter.label`; tool tip = `Parameter.help` on the label and every widget of
the row; the form is a `QFormLayout` in declaration order. A Basic parameter is in the Basic panel
only and an Advanced one in the Advanced panel only (D17); the Advanced panel with none shows the
one line "This method has no advanced parameters." The Basic panel starts with the method selector
(a `QComboBox` over `engines.methods` in mapping order, item text = `method.label`, item data = the
id, current = `session.parameters().method`).

The widget never shows a stale value: rows hold a `_shown` value; `show(value)` returns at once if it
equals `_shown` (so a commit that comes back through `parameters_changed` does not move the widget
under the user's mouse), else it sets the widgets under `QSignalBlocker`.

Commit: `set_parameters(dataclasses.replace(current, parameters={**current.parameters, name:
value}))` where `current = session.parameters()`. A ValueError from the session becomes
`Message("error", ..., owner="parameters")`; the next successful commit calls
`clear("error", owner="parameters")` (only after this panel presented one).

### 4. The real-schema coverage line (`methods/schema.py`)

| Real parameter type | Where | Shown by |
|---|---|---|
| `float`, both bounds, not nullable | every numeric parameter except the caps (for example `white_balance_strength` 0..1, `blend_with_original` 0..100, `gamma` 0.1..4, `laplacian_fraction` 0.0001..0.02) | spin + slider; decimals 2..5 per the formula above |
| `float`, both bounds, nullable | `red_gain_cap`, `blue_gain_cap` (default 2.0, 0..10; D52, D100) | "On" + spin + slider; None = off |
| `int`, both bounds | `pyramid_min_level_size` 1..256 | spin + slider |
| `bool` | `blue_compensation` | checkbox |
| `enum`, unbounded `float`/`int`, `bool` nullable | none in the real schemas | table above (covered by the test methods); no real parameter is outside the table, so no STOP |

Two real parameters share the label "Compensation strength" (`alpha`, `c3_strength`): they belong to
different methods, so one panel never shows both. `blend_with_original` is shown as declared (0..100,
label "Blend with original (%)"); nothing is special-cased.

### 5. The method-switch rule (question 2, ruled: carry over)

The selector's `currentIndexChanged(new_id)` builds `new_parameter_set(new_id, carried)`; `carried`
holds each entry of `session.parameters().parameters` (the names the user or a preset set, not the
defaults) whose name exists in the new method's schema and for which
`validate_parameter_set(ParameterSet(new_id, {name: value}, ...), new_id, new_schema)` reports no
problem naming it (type, bounds, choices, nullability). Every other name is dropped and so takes the
new method's default. Then `session.set_parameters(...)`. The panels see `parameters_changed` with a
different method id and rebuild their rows (D49: the controls come from the selected method's schema
alone, so ancuti2018's caps vanish on `c3` and return on the way back); the selector stays and is
only re-pointed (blocked). Old rows are detached at once (`setParent(None)`) and `deleteLater`'d.
Test: `white_balance_strength = 0.3` survives c3 -> ancuti2018 -> c3; `kappa` (c3 only) is dropped; a
value invalid for the target (a test float 5.0 with maximum 2 in the target) is dropped.

### 6. The preset operation table (`PresetPanel`)

The list shows `presets.list_presets()` (store order), refreshed after every operation (any outcome
that touched the store) and in `showEvent`. An entry with `error` is a disabled item, tool tip the
error ("made by a newer Clearwater" when `unsupported_version`), never selectable, so no operation
reaches it. Buttons: Load, Save as..., Rename..., Delete, Import..., Export...; Load, Rename, Delete,
Export are enabled while a readable item is selected. A status label under the list holds the last
success text ("Loaded 'X'", "Imported as 'X (2)'"), ASCII-safe. Every error is `Message("error",
ascii_text(text), path, owner="presets")`; every success calls `clear("error", owner="presets")` and
`clear("warning", owner="presets")` first (the second so an earlier import warning is replaced). A
cancelled dialog or a declined confirmation does nothing and clears nothing. Every slot is wrapped:
`PresetError` (incl. `PresetImportError`, `UnsupportedPresetVersionError`), `FormatError`,
`OSError`, `ValueError` become the error message; nothing escapes.

| Operation | Calls | Exceptions -> text (severity error unless noted) | List / state after |
|---|---|---|---|
| Load | `presets.load(name)`; method in `engines.methods`?; `validate_parameter_set(ps, ps.method, engines.methods[ps.method].parameters)`; `session.set_parameters(ps)` | `PresetError`/`UnsupportedPresetVersionError`: "Cannot load preset 'X': <store text>"; unknown method: "Preset 'X' is for method 'm', which is not available (available: a, b)"; problems: "Preset 'X' does not match method 'm': <every message joined by '; '>" and NOTHING applied; `ValueError` from `set_parameters`: its text | refreshed; parameters applied only on the full pass |
| Save as | `ask_name("Save preset", selected name or "")` -> None = cancel; `validate_preset_name`; a listed entry whose `NFC(name).casefold()` equals the new name's: readable -> `confirm("A preset named 'X' already exists. Replace it?")`, declined = cancel, accepted -> `save(name, session.parameters(), overwrite=True)`; else (no match, or the match is an unreadable entry) `save(..., overwrite=False)` | `PresetError` (bad name: the store's own text; exists/unreadable: "a preset named 'X' already exists"), `FormatError`, `OSError` | refreshed, the saved name selected |
| Rename | `ask_name("Rename preset", old)` -> None or the same name = cancel; `rename(old, new)` | `PresetError` (bad name, taken, not readable) | refreshed, the new name selected |
| Delete | `confirm("Delete preset 'X'?")`, declined = cancel; `delete(name)` | `PresetError`, `OSError` | refreshed |
| Import | `open_file()` -> None = cancel; `import_preset(path, {id: m.parameters for id, m in engines.methods.items()})` | `PresetImportError` (unreadable, unknown method, schema problems: the store text already lists every problem), `UnsupportedPresetImportError` (a `PresetError` and `PresetImportError`: "made by a newer Clearwater"), `PresetError` (the file's stem is not a valid name), `OSError`; `path` = the file | refreshed, the stored name selected; the status label says "Imported as 'N'" when `result.name != path.stem`; a `PresetImportResult.provenance_dropped` presents `Message("warning", "<file>: the provenance sidecar's <dropped_keys> were not kept ...", path, owner="presets")` |
| Export | `save_file(f"{name}.json")` -> None = cancel; when `os.path.lexists(target)`: `confirm("<file> already exists. Replace it?")`, declined = cancel; `export_preset(name, target, overwrite=exists)` | `PresetError` (target is a folder, preset unreadable), `FormatError`, `OSError` | refreshed |

DR-34 (a): `overwrite=True` is passed only after a confirmed, listed, readable same-name preset
(Save as) or a confirmed existing target (Export). The panel never calls `save_settings`.

### 7. The `PresetDialogs` seam

```
class PresetDialogs(Protocol):
    def ask_name(self, title: str, initial: str) -> str | None: ...
    def confirm(self, text: str) -> bool: ...
    def open_file(self) -> Path | None: ...
    def save_file(self, initial_name: str) -> Path | None: ...
```

`QtPresetDialogs(parent)`: `QInputDialog.getText`, `QMessageBox.question` (default No),
`QFileDialog.getOpenFileName` with filter "Preset files (*.json)", `QFileDialog.getSaveFileName`
with `DontConfirmOverwrite` (the panel asks itself) and `.json` appended when the chosen name has no
suffix; each returns None on cancel. `preset_panel(context, *, dialogs=None)` defaults to
`QtPresetDialogs(context.window)`. Tests pass a scripted fake (a class whose answers are queued; an
unscripted call fails the test, so nothing can block).

### 8. The test list (all `gui`-marked, headless, `tmp_path` locations)

`tests/test_gui_parameter_panels.py` (test methods declared in the module: `ALL_TYPES` with bounded
and unbounded float and int, bool, enum, nullable bounded float, nullable bool; `c3` and
`ancuti2018` where only the second has the caps, `kappa` only in the first):
- generation: one control per parameter in its own panel only; label and tool tip from the schema;
  empty Advanced line; selector order = `engines.methods` order and selects the session's method;
  the real `C3_PARAMETERS`/`ANCUTI2018_PARAMETERS` each get one control per parameter (imported from
  `clearwater.methods.schema` in the TEST only: `test_gui_deps` scans `src/` modules, tests are free
  to import it; checked below in STOP-3);
- ranges: spin range, decimals and slider mapping for a bounded float and int; clamped unbounded
  display limits; no committed value is outside the schema (slider at both ends, spin beyond a bound);
- live: one edit = one `set_parameters`, exactly the edited name added, other names and `created`
  kept; a partial set stays partial; slider drag commits each value; external `set_parameters`
  updates widgets with no emission and no `set_parameters` call back; the commit round trip does not
  move the widget; nullable unchecked = None, re-checked = the last value; enum and bool;
- D49 and the switch rule (section 5), a rebuild leaves no old control (`findChildren` of the old
  names empty), the selector only re-pointed; an external method change (as by a preset) rebuilds;
- messages: a `set_parameters` ValueError becomes an error with owner "parameters", cleared by the
  next success; another owner's error survives;
- planted wrong implementations that must fail by name: programmatic update that re-emits (planted
  subclass without the blocker), a commit that drops the method-switch validation.

`tests/test_gui_preset_panel.py` (scripted fake dialogs; real `PresetStore` under `tmp_path`):
- each G6 operation once: save (new), save over (confirmed; declined leaves the file and the
  parameters), load, rename, delete (confirmed; declined), import (valid; unknown method; schema
  problems all listed; provenance sidecar -> warning naming the dropped keys; stored name differs),
  export (new; over an existing file confirmed and declined); cancelled dialogs do nothing;
- an unreadable and a newer-version file listed disabled with the tool tips, untouched by every
  operation; a name clash case-insensitively; an invalid name; the starter presets
  ("Snorkel (shallow)", "Scuba (deep)") listed and loadable with the `"c3"` test method;
- V13: save -> export -> import -> load gives a `ParameterSet` with the same `method`, `parameters`
  and `app_version` (and `created`);
- DR-44 (b): a `"shell.preview"` error survives a successful load, the panel's own error is cleared
  by its next success, and its warning is replaced; every message presented has owner "presets" and
  every clear passes owner "presets";
- nothing escapes a slot (store monkeypatched to raise `OSError`, `FormatError`, `PresetError`);
- planted wrong implementations that must fail by name: a preset applied despite a schema problem;
  `overwrite=True` without a confirmation (Save as and Export); a panel that clears without an owner;
- dependency: `tests/test_gui_deps.py` run unchanged (it globs the new modules).

### 9. Answers to the brief's questions

1. No edit to `gui/__init__.py`; consumers import by module path (ruled).
2. Carry-over (section 5; ruled).
3. Imports from WP3.16's helpers: `clearwater.gui.messages.ascii_text` and `file_name` only (ruled).
4. Superseded by the blend ruling: the schema's value, range and label as declared.
5. The shared `CapturingPresenter` (settled; it already honours `owner`).
6. STRONG, five-round gate.

### 10. STOPs and choices for the dispatcher (each with my recommendation)

- **STOP-1, cross-parameter relation.** `resolve_parameters` also demands
  `normalisation_low < normalisation_high`; the schema bounds (both 0..100) allow a pair that breaks
  it, and a panel generated from IF-3 cannot know the relation (10.1: "method-agnostic"). Reproduction:
  with the real c3 schema, `resolve_parameters("c3", C3_PARAMETERS, {"normalisation_low": 60.0})`
  raises ValueError ("normalisation_low=60.0 must be below normalisation_high=99.5"); the preview
  would show its own error banner (`shell.preview`) until the user lowers it. Recommendation: the
  panel commits any schema-valid value (as the brief says, "no value outside the schema"), and this
  is reported as a limit and a consumer note for WP3.4/WP4.3 (a later IF-3 `constraints` field is an
  AD-20 matter). If you prefer, ask CHARC to have WP3.4 widen the real schema's ordering in the
  method's own resolution to a clamp instead of a raise; not this package's.
- **STOP-2, additions to the brief's literal text** (all inside my files, all additive): the keyword
  `dialogs=None` on `install_parameter_panels`; a status `QLabel` in the preset panel for the
  success texts the brief says to "show" (stored name when it differs; there is no info severity);
  `clear("warning", owner="presets")` beside the brief's `clear("error", owner="presets")` so an
  old import warning does not linger; Save as stores `session.parameters()` as the brief says
  (it keeps that set's `created` and `app_version`; I do not restamp). Recommendation: accept all.
- **STOP-3, the dependency-rule test and the real schema.** `test_gui_deps` forbids `gui` modules
  from importing `clearwater.methods`; my test modules would import `clearwater.methods.schema` to
  show the real parameters. The scan covers `src/clearwater/gui/*.py` only, so a TEST import is
  allowed; the brief (task 5) asks for test methods declared in the test modules, and the dispatch
  note asks for the real-schema table. Recommendation: the tests keep their own test methods, plus
  one test per file section that imports the real tuples read-only to prove coverage
  (`C3_PARAMETERS`, `ANCUTI2018_PARAMETERS` are plain `Parameter` tuples with no array code). If you
  rule that no test may import `clearwater.methods`, I replace it with a hand copy of the real
  parameter types.

### 11. `scripts/cell_depth.py`

A cell cannot read its own depth (recipe section 5); the dispatcher fills the Depth column (round 0: 123,285).

Round-0 ruling (dispatcher, FINAL): table approved; STOP-1, STOP-2 (all four) and STOP-3 accepted as recommended. STOP-1 additionally requires a test with a test method that has the same kind of relation, showing the ValueError reaches the user as the preview's `shell.preview` error, and a named limit / consumer note (an IF-3 constraints field would be an AD-20 matter).
