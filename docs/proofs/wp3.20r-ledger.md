# WP3.20R cumulative ledger

## Dispatch and scope

- Turn 1: read, reproduce, table; branch `wp3.20r`, base and observed HEAD
  `9753b7b`. The initial tracked working tree was clean.
- Read the dispatch recipe, application definition, CLAUDE.md, supplied FINAL
  brief and dispatch, settings-dialog module and tests, and DR-53..DR-55.
  Read only the shared GUI helpers needed to construct the scratch reproduction.
- No product code or test file changed. The only deliverable this turn is this
  ledger. Scratch scripts, logs and reproduction settings stay in ignored
  `work/wp3.20r/`.
- Token/depth figure: no numeric figure supplied yet; dispatcher fills it from
  this run's footer. No reviewer has run; Reviewer A follows turn 5.

## Baseline and sandbox observations

Every command ran from the worktree. Runner output is in the named log under
`work/wp3.20r/`; pytest and reproduction used `QT_QPA_PLATFORM=offscreen`.

| Command | Observed result | Log |
|---|---|---|
| `uv run pytest tests/test_gui_settings_dialog.py tests/test_gui_deps.py --basetemp=work/wp3.20r/tmp -q` | Exit 1; fixture errors and a session-finish traceback; no valid final summary. `PermissionError: [WinError 5] Access is denied: 'C:\Users\rwsmy\clearwater\.worktrees\wp3.20r\work\wp3.20r\tmp'`. No `LocalConfigError` observed. | `turn1-baseline-pytest.log` |
| `uv run pytest tests/test_gui_settings_dialog.py tests/test_gui_deps.py --collect-only -vv` | Exit 0; `64 tests collected in 0.61s`: 60 settings-dialog cases and 4 dependency cases. Collection is not a passing baseline execution. | `turn1-collection.log` |
| `uv run ruff check .` | Exit 0; `All checks passed!` | `turn1-ruff-check.log` |
| `uv run ruff format --check .` | Exit 0; `227 files already formatted` | `turn1-ruff-format.log` |
| `uv run mypy` | Exit 0; `Success: no issues found in 132 source files` | `turn1-mypy.log` |
| `uv run python work/wp3.20r/turn1_reproduce.py` | Exit 0; `REPRODUCTION SUMMARY: 6 cases matched the base observations` | `turn1-reproductions.log` |

`uv run` created the worktree environment and ran all three static tools. It
warned that the inherited `VIRTUAL_ENV` differs from this project's `.venv`.
The prescribed pytest `--basetemp` did not work in this sandbox: reading that
directory's ACL also returned an unauthorized-operation error. The cause of the
permissions is not established. No permissions, runner infrastructure or test
fixtures were changed. Standalone reproduction directories created normally
under `work/wp3.20r/` were writable and readable. No effect outside the worktree
is claimed. The dispatcher must resolve the targeted pytest execution limit
before relying on a green package gate; the full suite was not run.

Final `git status` also warned that root-level `pytest-cache-files-ggmfethz/`
and `pytest-cache-files-_hwil4rn/` could not be opened (permission denied).
These runner cache artifacts were left untouched; they are not deliverables.
PowerShell redirection wrote the logs as UTF-16; a scratch validation read first
using UTF-8 failed, then was corrected to read UTF-16. The ledger itself is ASCII.

## Reproductions on the base

Scratch script: `work/wp3.20r/turn1_reproduce.py`. It reuses `Env`, the injected
sink/cache/choosers, `MainWindow`, the capturing presenter and locations helper;
a small event pump replaces the pytest temp/widget fixture. It opens each real
dialog through the shell action and waits for encoder detection. Settings and
cache locations are within this worktree's scratch directory. All six cases
assert their stated base observations; long suffix content is never logged.
The initial scratch launch had an incorrect import-root calculation and failed
with `ModuleNotFoundError`; corrected in scratch, then all cases ran successfully.

| Row / scenario | Observed behavior before and after the action | Disposition |
|---|---|---|
| DR-53 / stored `"a" * 32767 + "/"` | Constructor field length 32768 despite `maxLength()` 32767; field exactly equals stored suffix. OK disabled. `accept()` refused; settings bytes and session unchanged; zero error messages. | Constructor mechanism NOT reproduced, as anticipated by adopted Q1. New settings-owned refusal message is still required. |
| DR-53 / stored `"bad\nsuffix"` | Constructor field length 10, newline preserved; field exactly equals stored suffix. OK disabled. `accept()` refused; settings bytes and session unchanged; zero error messages. | Same Q1 disposition; no truncation/flattening observed. |
| DR-53 / session divergence | Open on defaults, then `session.set_settings(dataclasses.replace(Settings(), output_suffix="bad/suffix"))`; field remains `_corrected`. `accept()` returned Accepted, created `settings.json` containing `bad/suffix`, and left that invalid suffix in the session; zero errors. | CONFIRMED: the value applied can escape the field-only validation. This is the ruled positive control. |
| DR-54 / stored `hevc_nvenc`, unavailable in `CAPS` | After detection: OK enabled, encoder note empty, `_encoder_unacceptable()` False. `accept()` returned Accepted and wrote back `hevc_nvenc`; session and existing settings bytes unchanged; zero errors. | CONFIRMED: stored equality bypasses reported unavailability. Same bytes do not prove no save; acceptance and saved encoder establish the defect. |
| DR-55 / raising `choose_folder` | Button click routed `OSError: injected chooser failed` to a temporary capturing `sys.excepthook`; zero settings errors. Folder unchanged, `_clearing` False, no cache clear, Clear cache enabled. | CONFIRMED escaped slot exception. |
| DR-55 / raising `confirm` | Same exception through a real Clear cache button click; zero settings errors. Folder unchanged, `_clearing` False, no cache clear, Clear cache enabled. | CONFIRMED escaped slot exception. |

The temporary exception hook is restored immediately after each click. It
records what Qt would send to pytest-qt's exception capture, without hiding the
escape or changing the slot. Reproduction settings are not deliverables.

## Change table for later turns (no implementation this turn)

| Row | Methods to change | Required behavior | Named evidence below |
|---|---|---|---|
| DR-53, turn 2 | `SettingsDialog.accept` | Build `edited_settings()`, validate `new.output_suffix`; on failure call `_check_suffix()`, keep dialog/session/file unchanged, and present `The output suffix is not valid: <ValueError text>` via `_present_error`, ASCII-safe with error detail cut to 200 characters. | S53 |
| DR-54, turn 3 | `_encoder_unacceptable`, `_update_encoder_note`, `_on_encoder_changed`, `accept` and their callers as needed | Refuse every reported-unavailable named encoder, including stored; disable OK, show the reason in `encoder_note`, and present the same settings-owned sentence on direct `accept()`. Clear the refusal note when selection becomes acceptable. Preserve detection-pending, auto and stored-unreported allowances and the injected 10-bit rule. | S54 |
| DR-55, turn 4 | `_on_choose_folder`, `_on_clear_clicked`; test `FakeChoosers` | Catch `Exception` only around injected calls, with the foreign-code comment. Present the two brief-specified settings errors, escaped to ASCII; preserve state and allow retry. | S55 |

S53 roster:

- `test_a_stored_suffix_that_fails_validation_in_its_last_character_is_refused`
- `test_a_stored_suffix_with_a_newline_is_refused`
- `_stored_suffix_scenario`
- `test_stored_suffix_scenario_passes_on_the_real_dialog`
- `test_planted_field_only_suffix_check_is_caught`

Use the ruled session `set_settings` divergence: deterministic, preserves the
real constructor, exercises the actual `edited_settings()` source, and reproduces
on the base. The constructor cases already refuse on base, but lack the required
settings-owned error. Refusal tests must check no write, unchanged session, error
ownership and successful correction; the planted field-only implementation must
fail the shared scenario.

S54 roster:

- `test_a_stored_encoder_the_sink_reports_unavailable_is_refused`
- `test_picking_another_encoder_after_the_refusal_accepts`
- `test_a_stored_encoder_arriving_unavailable_after_detection_refuses_ok`
- `test_auto_is_resolved_by_a_rule_that_disagrees_with_the_interim_rule`
  (both directions, asserting 10-bit state, note and spy arguments)
- `_unavailable_stored_scenario`
- `test_unavailable_stored_scenario_passes_on_the_real_dialog`
- `test_planted_stored_unavailable_accepted_is_caught`

Keep the agreeing injected-rule test and both stored-unreported/failed-detection
tests unchanged. Keep the truth table in `_encoder_unacceptable`'s docstring:

| Selected | Sink report | Stored? | OK |
|---|---|---|---|
| `auto` | any | any | allowed |
| any | being read | any | allowed; re-evaluate on arrival |
| name | reported unavailable | either | refused |
| name | reported available | either | allowed |
| name | absent or report failed | stored | allowed (Q3) |
| name | not reported | picked | refused |

Corrected claim for turn 5: a reported-unavailable encoder is never accepted,
stored or picked; refusal shows the reason. A stored encoder not reported
(including report failure) stays shown unavailable and writes back unchanged
unless edited. Detection disables the control and defers encoder refusal until
the result arrives. Replace only the designated existing report bullet.

S55 roster:

- `test_a_raising_folder_chooser_is_a_settings_error`
- `test_a_raising_confirmation_is_a_settings_error_and_clears_nothing`
- `test_a_dialog_still_works_after_a_chooser_failure`
- `_chooser_scenario`
- `test_chooser_scenario_passes_on_the_real_dialog`
- `test_planted_unwrapped_chooser_is_caught`
- Extend `test_every_message_of_the_dialog_is_ascii` for the new messages and
  non-ASCII exception text; extend only the owned file's `FakeChoosers`.

## Verification loop and round ledger

| Turn | Suspected | Independently confirmed / rejected | Fixed | Open |
|---|---|---|---|---|
| 1 | DR-53 constructor truncation; value divergence; DR-54 stored bypass; DR-55 chooser escape | Constructor truncation rejected by both runtime measurements; divergence, stored bypass and both slot escapes confirmed by six asserted scratch cases, consistent with code paths. | Scratch import-root slip only; no product/test fixes authorized this turn. | Targeted pytest cannot complete with prescribed basetemp; later implementation and all review rounds pending. |

| Reviewer A round | Severity counts | In / out of envelope | NEW / REOPENED | Reverts | Product / test-only fixes | Verdict | Dispatcher token figure |
|---|---|---|---|---|---|---|---|
| Not started | n/a | n/a | n/a | 0 | 0 / 0 | Scheduled after turn 5 | Not supplied |

Locks this turn: owned deliverable only; product/tests and frozen interfaces
untouched; no dependency or OS-specific product change; local configuration
unchanged; footage unused and untouched; explicit scratch output under `work/`
(pytest cache permission warnings disclosed above);
ledger ASCII and LF; no git writes, commits, reviewer or mailbox activity.
