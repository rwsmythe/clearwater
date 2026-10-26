# WP3.17 report: parameter panels and presets

Package `clearwater.gui`, modules `parameter_panels.py` and `preset_panel.py`, tests
`tests/test_gui_parameter_panels.py` and `tests/test_gui_preset_panel.py`. Spec v0.5.4 (G3, G6; D16,
D17, D37, D38, D49, D52, D90), architecture FINAL 1.0 (IF-3, IF-9, IF-10; AD-8, AD-13, AD-20;
DR-44 (b)). Base `718324b`. Nothing existing was changed: no WP3.16 module or test,
`gui/__init__.py`, `config/`, `interfaces/`, `pyproject.toml` or `uv.lock`; no dependency was added.
The review ledger is `docs/proofs/wp3.17-ledger.md`; review evidence is in
`C:\Users\rwsmy\clearwater-review-evidence\wp3.17\r1\`.

## Public API

| Module | Names |
|---|---|
| `parameter_panels` | `install_parameter_panels(window, *, dialogs=None)` (attaches "Basic", "Advanced", "Presets" in `Area.PARAMETERS`; WP4.3 calls it), `basic_panel(context)`, `advanced_panel(context)` (each a `PanelFactory`), `BasicPanel` (has `selector`), `AdvancedPanel`, `ParameterRow`, `controls()` on both panels (name -> row), `float_decimals`, `float_step`, constants `OWNER_PARAMETERS = "parameters"`, `SLIDER_STEPS = 1000` |
| `preset_panel` | `preset_panel(context, *, dialogs=None)` (a `PanelFactory` when called with the context), `PresetPanel` (`list`, `status`, `buttons`; `refresh`, `selected`, `select`, `load`, `save_as`, `rename`, `delete`, `import_file`, `export`), `PresetDialogs` (Protocol: `ask_name`, `confirm`, `open_file`, `save_file`), `QtPresetDialogs(parent)`, `OWNER_PRESETS = "presets"` |

## Widget table

Everything comes from the selected method's IF-3 schema; a parameter is in exactly one panel (D17).

| Type | Widget | Range, step, decimals | Commit signal |
|---|---|---|---|
| `float`, both bounds | `QDoubleSpinBox` + `QSlider` 0..1000, linear | `[min, max]`; decimals: the largest of those of the default and of both bounds in their shortest `repr` (shown exactly, maximum reachable) and, with a slider, those that make its 1000 steps distinct; 2..15; step a power of ten near span/100 | spin `valueChanged` (keyboard tracking off) and slider `valueChanged` (every value of a drag) |
| `float`, fewer bounds, or a span below 1e-12 | `QDoubleSpinBox` only | missing side +/-1e9; decimals from the default and bounds, 3..15 | spin `valueChanged` |
| `int`, both bounds | `QSpinBox` + `QSlider` over `[min, max]` | clamped to +/-(2^31-1) both sides | both |
| `int`, fewer bounds | `QSpinBox` | missing side +/-(2^31-1) | spin |
| `bool` | `QCheckBox` | | `toggled` |
| `enum` | `QComboBox` over `choices` | | `currentIndexChanged` (blocked on programmatic updates) |
| `nullable`, or default None | leading "On" `QCheckBox` + the type's widgets; unchecked = None, value widgets disabled | | "On" `toggled` |

A committed number is also clamped to the schema range. Real-schema coverage (`methods/schema.py`):
bounded float, bounded nullable float (the gain caps), bounded int, bool; enum and unbounded numbers
occur only in the test methods. `blend_with_original` is shown as declared, 0..100, nothing
special-cased (CHARC blend ruling).

Decimals rule (Reviewer B #1): Qt rounds a `QDoubleSpinBox`'s bounds and value to its decimals, so
`float_decimals` takes the shortest-`repr` decimals of the default and both bounds, raised to make the
slider's 1000 steps distinct when there is a slider, clamped to 2..15 (3..15 without both bounds). A
range whose 1000 steps would need more than 15 decimals (span below 1e-12) gets no slider
(`float_has_slider`). Only a value that needs more than 15 decimals is rounded, and a committed number
is clamped to `[minimum, maximum]` regardless. Test: a 1e-7..2e-7 schema with default 1.5e-7 keeps its
bounds and default and reaches its maximum.

## The method-switch rule

Switching the method in the selector builds `new_parameter_set(new_id, carried)`; `carried` holds each
currently set value (not the defaults) whose name exists in the new schema and for which
`validate_parameter_set` reports no problem naming it. Other names take the new method's defaults.
Both panels see `parameters_changed` with another method id and rebuild their rows (D49: the caps of
`ancuti2018` are absent under `c3`); the selector is only re-pointed, never rebuilt. A change from
outside (a loaded preset) rebuilds the same way and commits nothing.

## Preset operations

| Operation | Store calls | Failure -> message (error, owner `"presets"`) |
|---|---|---|
| Load | `load`; method known; `validate_parameter_set`; `session.set_parameters` | any `PresetError`, an unknown method (names the preset, the method, the available ones), every schema problem listed; nothing applied |
| Save as | `validate_preset_name`; `confirm` when a readable listed entry matches NFC + casefold; `save(..., overwrite=<confirmed>)` | bad name, an unreadable entry of that name ("already exists") |
| Rename | `rename` | bad or taken name |
| Delete | `confirm`; `delete` | `PresetError`, `OSError` |
| Import | `import_preset(path, schemas of engines.methods)` | `PresetImportError` (all problems), newer version, bad stem, `OSError`; a provenance sidecar gives a warning naming the dropped keys; the stored name is shown when it differs from the stem |
| Export | `confirm` when the target exists; `export_preset(..., overwrite=<confirmed>)` | target is a folder, `OSError` |

Every success clears the panel's `error` and `warning` messages (owner `"presets"`) before the list is
refreshed; a cancelled dialog or a declined confirmation changes nothing; no exception escapes a
slot. An unreadable entry is a disabled item (tool tip "made by a newer Clearwater" for an
unsupported version) that nothing acts on. The panel never calls `save_settings`.

## Claims and evidence

| Claim | Evidence (tests are in `tests/`) |
|---|---|
| One control per parameter in its panel, labels and tool tips from the schema, empty-Advanced line, selector order | `test_gui_parameter_panels.py::test_one_control_per_parameter_in_its_own_panel_only`, `..._label_and_tool_tip_...`, `..._widget_kinds_...`, `..._empty_advanced_panel_...`, `..._selector_lists_...`; the real c3 and ancuti2018 schemas: `..._the_real_schemas_get_one_control_per_parameter` |
| Ranges, decimals, slider mapping; nothing outside the schema is committed | `test_float_decimals_step_and_slider_mapping`, `test_int_range_and_slider`, `test_one_sided_and_unbounded_...`, `test_no_committed_value_is_outside_the_schema`, `test_int_bounds_beyond_the_spin_box_limit_...` |
| Live edit: one `set_parameters` with exactly the edited name; slider drag commits each value; external update does not commit | `test_an_edit_commits_once_...`, `test_a_slider_drag_commits_every_value`, `test_an_external_set_parameters_updates_...`; planted blocker-free update fails: `test_planted_programmatic_update_that_re_emits_fails` |
| Nullable: unchecked is None, re-check restores the value | `test_nullable_unchecked_is_none_...`, `test_a_none_default_gets_an_on_box_...` |
| D49 and the switch rule; no control of the old method; planted switch without validation fails | `test_switching_the_method_removes_and_restores_the_cap_controls`, `test_the_switch_carries_over_only_values_valid_for_the_new_method`, `test_planted_switch_without_validation_fails`, `test_an_external_method_change_rebuilds_...` |
| A refused edit becomes an error with owner `"parameters"`, cleared by the next success, controls restored | `test_a_refused_set_becomes_an_error_...`, `test_a_refused_edit_puts_the_session_value_back_in_the_control` |
| A relation between two parameters reaches the user as the preview's `shell.preview` error, never as an exception of a slot | `test_a_relation_between_two_parameters_reaches_the_user_as_the_preview_error` |
| Every G6 operation, cancel, bad input | `test_gui_preset_panel.py` (save, save over confirmed and declined, load, rename, delete, import valid / unknown method / schema problems / garbage / sidecar, export new / over a file / to a folder) |
| Unreadable and newer-version files listed disabled and untouched; starters listed and loadable with `"c3"` | `test_an_unreadable_and_a_newer_version_file_...`, `test_the_starter_presets_are_listed_and_loadable_...`, `test_a_starter_cannot_load_when_c3_is_not_available` |
| V13 leg: save -> export -> import -> load keeps `method`, `parameters`, `app_version`, `created` | `test_v13_save_export_import_load_reproduces_the_set` |
| DR-44 (b): every message has an owner, every clear passes it, another owner's error survives | `build()` wraps `clear` to demand `owner="presets"`; `test_another_owners_error_survives_...`, `test_the_panels_own_error_is_cleared_...`; planted ownerless clear fails: `test_planted_clear_without_an_owner_fails` |
| No overwrite without a confirmation (DR-34 (a)) | `test_save_over_an_existing_name_asks_...`, `test_export_over_an_existing_file_asks_...`; planted overwrites fail: `test_planted_save_that_overwrites_without_asking_fails`, `test_planted_export_that_overwrites_without_asking_fails` |
| Nothing applied after a failed validation | `test_load_with_schema_problems_...`, `test_planted_load_that_skips_validation_fails` |
| No exception escapes a slot | `test_no_exception_escapes_a_slot` (OSError, FormatError, PresetError, ValueError) |
| Dependency rule (no `clearwater.methods` import in `gui/`, no `QSettings`) | `tests/test_gui_deps.py`, unchanged, green |

## Gates

Own tests with `test_gui_deps.py`: 73 passed (headless, targeted). `uv run ruff check .`, `ruff
format --check .` and `mypy` clean. Full pytest: run by the orchestrator on the merge candidate (stacked gate). Reviewer A (STRONG, at the cell's seat): round 1 reported 7 findings (3 tagged MAJOR);
the dispatcher upheld the proposed severities (0 blocking), so the loop ended at round 1 and its
fixes are the terminating cleanup (one regression test per finding, red on `b2822d3`).

## Decisions and deviations

- `install_parameter_panels(window, *, dialogs=None)` takes a keyword the brief's signature lacks, so a
  test can inject the scripted dialogs through the installer.
- A status `QLabel` under the preset list shows success texts (including the stored name of an import
  when it differs from the file's stem; there is no info severity).
- A successful operation clears `error` and `warning` messages of owner `"presets"`, the second so an
  earlier import warning is replaced.
- Save as stores `session.parameters()` unchanged (it keeps that set's `created` and `app_version`; no
  restamp).
- Tests import `clearwater.methods.schema` read-only in one test (STOP-3 ruling); `gui/` never does.
- Test-first: the product code and its first tests were written under the host's test hold, so the
  first 67 tests were never shown red on unfixed code; their planted-wrong-implementation partners were
  shown to catch the wrong code. The round-1 regression tests were shown red on `b2822d3` (5 failures,
  one passing test is a test-gap addition) and green after their fixes.
- Round-1 fixes #2 and #3 are in one commit (`2dc845a`), because both rewrite the same operation tails.

## Limits (for the accept record)

- **A relation between two parameters is not enforced.** `resolve_parameters` also requires
  `normalisation_low < normalisation_high`; the schema bounds cannot say it and a method-agnostic panel
  cannot see it. The panel commits any value the schema allows; the method refuses the pair at render
  and the shell presents that as its `shell.preview` error (shown by a test). An IF-3 `constraints`
  field would be an AD-20 matter.
- A float needing more than 15 decimals (or a span below 1e-12) is shown without a slider and rounded to 15 decimals.
- #5 (round 1, accepted limitation): a number whose minimum equals its maximum gets no slider (a
  zero span has no meaning); no real schema has one.
- A number with no bound on a side is shown in +/-1e9 (float) or +/-(2^31-1) (int); a schema bound
  beyond that is clamped. The real schemas have small finite bounds.
- A method switch drops, without telling the user, the values that do not carry over.
- The Basic and Advanced panels each clear their `"parameters"` error only after they presented one.
- Every store call and the list refresh are synchronous on the interface thread (envelope: a local
  folder, presets up to 1 MiB).
- No undo and no "reset to defaults" (not in G3/G6). `Parameter.neutral` is not used.

## Consumer notes

**WP3.4 (methods).** The real schema is shown as declared; nothing special-cased. Every `Parameter`
needs a finite `minimum`/`maximum` for a slider, and a label and `help` for the row. A relation between
parameters (`normalisation_low < normalisation_high`) is only caught when the method renders; the user
sees the preview error, not a refused edit. If that is not acceptable, the relation needs an interface
field (AD-20) or a method that resolves the pair instead of raising.

**WP4.3 (assembly).** Call `install_parameter_panels(window)` once after the window is built (it attaches
the three panels; pass `dialogs=` only in tests). Import by module path:
`clearwater.gui.parameter_panels` (`gui/__init__.py` exports nothing from this package, by ruling).
`engines.methods` must list `"c3"` first (the Basic panel's selector lists methods in mapping order, and
the starter presets are `"c3"`). The panels read and change only `Session.parameters`, `Session.method`
and `Session.set_parameters`; preset files live in `locations.presets_dir`.
