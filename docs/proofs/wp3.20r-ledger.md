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
- Dispatcher-supplied end-of-turn-1 token figure: **64,199**, supplied at the
  turn-2 gate; turn 1 committed as `c46eb1a`. Dispatcher-supplied end-of-turn-2
  figure: **92,340**, supplied at the turn-3 gate; turn 2 committed as `944b5d2`.
  Turn-3 figure not yet supplied.
  No reviewer has run; Reviewer A follows turn 5.

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
is claimed. Targeted pytest execution was unresolved at turn 1; the dispatcher
diagnosis and successful shim run are recorded under turn 2. The full suite was
not run.

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
| Not started | n/a | n/a | n/a | 0 | 0 / 0 | Scheduled after turn 5 | Turn 1: 64,199 |

Locks this turn: owned deliverable only; product/tests and frozen interfaces
untouched; no dependency or OS-specific product change; local configuration
unchanged; footage unused and untouched; explicit scratch output under `work/`
(pytest cache permission warnings disclosed above);
ledger ASCII and LF; no git writes, commits, reviewer or mailbox activity.

## Turn 2: DR-53

### Sandbox diagnosis and baseline

The dispatcher diagnosed the Windows Python 3.12 owner-only ACL created by
`os.mkdir(path, 0o700)` as incompatible with this sandbox's restricted token.
Its unsandboxed base run was `64 passed in 5.36s`, reported from
`work/wp3.20r/orch-base-pytest.log` (dispatcher evidence, not a cell rerun).
Read the supplied `work/sandbox/sandbox_mkdir_shim.py`: it wraps only `os.mkdir`,
mapping mode 0o700 to 0o777 and forwarding the other arguments. It was neither
edited nor added to the deliverables.

All turn-2 pytest runs used `QT_QPA_PLATFORM=offscreen`,
`PYTHONPATH=work/sandbox`, `-p sandbox_mkdir_shim -p no:cacheprovider`, both
targeted files and `--basetemp=work/wp3.20r/tmp-t2 -q`. The old inaccessible
temp/cache directories were left untouched. Gate runs at the dispatcher's seat
do not load this shim.

### Tests first, then product edit

The unchanged module passed the shim baseline: **64 passed in 5.17s**, exit 0
(`work/wp3.20r/turn2-baseline-pytest.log`). Added four test functions, five cases
(the real divergence scenario has an ASCII case and a long non-ASCII error
case), plus the shared refusal/correction helper and divergence scenario.
The product module was still unchanged during the red run.

| Test | Base with new tests | After product edit |
|---|---|---|
| `test_a_stored_suffix_that_fails_validation_in_its_last_character_is_refused` | FAILED: refusal already works, but zero error messages instead of one | PASSED |
| `test_a_stored_suffix_with_a_newline_is_refused` | FAILED: same missing settings-owned error | PASSED |
| `test_stored_suffix_scenario_passes_on_the_real_dialog[separator]` | FAILED: `invalid applied suffix was written` | PASSED |
| `test_stored_suffix_scenario_passes_on_the_real_dialog[non-ascii-error]` | FAILED: `invalid applied suffix was written` | PASSED |
| `test_planted_field_only_suffix_check_is_caught` | PASSED: planted dialog fails the scenario at the invalid-write assertion | PASSED: same named assertion catches the planted dialog |

Red summary: **4 failed, 65 passed in 6.72s**, exit 1, no setup errors
(`work/wp3.20r/turn2-red-pytest.log`). As ruled in Q1, the constructor behavior
already refused on base; the complete new tests fail there because they also
require the newly specified error message. The row's actual validation
regression is demonstrated by both divergence cases.

For constructor cases, load the stored settings and open the dialog normally,
then remove only the temporary fixture settings file before calling `accept()`.
Its continued absence proves no refusal-time write; the tests also check a
non-Accepted result, unchanged session settings, exactly one settings-owned error
and successful acceptance/save after a valid correction. The divergence uses
only the ruled `session.set_settings` route, leaving the displayed field intact.
The long non-ASCII detail verifies both ASCII escaping and the 200-character
limit without changing the existing suffix-error label.

Changed only `SettingsDialog.accept` in product code: build `edited_settings()`
once, validate its `output_suffix`, and on `ValueError` call `_check_suffix()`
then `_present_error` with `The output suffix is not valid: ` plus the ASCII
error detail cut to 200 characters, returning before save/apply/close. The
successful path reuses that same validated settings object. Updated its
docstring to describe the validated settings. Other settings behavior unchanged.

### Gates and verification

| Check | Result | Log under `work/wp3.20r/` |
|---|---|---|
| Targeted pytest after product edit, with sandbox shim | Exit 0; **69 passed in 7.97s** | `turn2-green-pytest.log` |
| `uv run ruff check .` | Exit 0; **All checks passed!**; two access-denied traversal warnings | `turn2-ruff-check.log` |
| `uv run ruff format --check .` | Exit 101; **Expected a ruff source file** (Ruff panic) | `turn2-ruff-format.log` |
| Format check of both changed Python files | Exit 0; **2 files already formatted** | `turn2-owned-format-check.log` |
| Format check with cache-name exclusion | Exit 101; same panic; exclusion did not resolve it | `turn2-ruff-format-excluding-inaccessible-cache.log` |
| Format check of every tracked Python path (diagnostic only) | Exit 1; **24 files would be reformatted, 233 files already formatted**; this explicit list includes files outside normal discovery, all unmodified | `turn2-tracked-format-check.log` |
| Format check of paths from `uv run ruff check . --show-files` | Exit 0; **227 files already formatted** | `turn2-discovered-format-check.log`; path list `turn2-discovered-ruff-paths.log` |
| `uv run mypy` | Exit 0; **Success: no issues found in 132 source files** | `turn2-mypy.log` |

The repository-wide formatter command remains a tool/sandbox limitation, not
a claimed green gate. Its exact cause is not established. Explicitly formatting
the 227 paths Ruff normally discovers passes without traversing directories.
The broader tracked-path diagnostic bypassed discovery exclusions and is not
the configured format gate; no unowned formatting was changed. The full suite
remains the orchestrator's task.

Verification loop: suspected field/applied-value divergence and missing refusal
messages; confirmed by the red run against the unchanged module; fixed in
`accept()`; repeated the whole targeted run with 69 passes. The planted
field-only implementation still fails by the invalid-write assertion, confirming
the scenario distinguishes the defect. Inspection confirms the failure returns
before `_save`, `set_settings`, cache-limit work and `super().accept()`, and
the successful path applies the same object it validated. No new DR-53 issue
found in the final pass. No Reviewer A round yet.

Turn-2 limits: configured formatter command crashes; supplemental discovered-file
format check passes. No scope deviation; extra parameterization covers the
required ASCII/length behavior. Only the three turn-2 owned files changed;
interfaces, dependencies, local configuration and footage untouched; no new
OS-specific product code. Sandbox plugin and all logs remain uncommitted.

## Turn 3: DR-54

### Carried gate evidence

The dispatcher confirmed the turn-2 tree outside the sandbox: formatter
**227 files already formatted**, exit 0; Ruff check **All checks passed!**.
It classifies the formatter crash as a sandbox artifact, likely related to the
old unreadable turn-1 temp root. This is dispatcher evidence, not a cell rerun.
Per direction, no broad tracked-file or discovery diagnostic was repeated.

### Tests first

Added six test functions, seven cases: the three required refusal/recovery/
pending-report tests; the two opposite disagreeing-resolver cases; and the
real-dialog/planted-dialog shared-scenario controls. The unchanged module for
this turn was `944b5d2` (DR-53 already applied). Both constructor-based refusal
scenarios load the real settings file and then remove only that fixture file,
so a refusal-time write is observable. No product edit preceded the red run.

| Test | Unchanged module | Final head |
|---|---|---|
| `test_a_stored_encoder_the_sink_reports_unavailable_is_refused` | FAILED: stored unavailable encoder left OK enabled | PASSED |
| `test_picking_another_encoder_after_the_refusal_accepts` | FAILED: initial refusal left OK enabled | PASSED; selecting `libx265` clears note/tool tip, enables OK, saves/applies it and clears the settings error |
| `test_a_stored_encoder_arriving_unavailable_after_detection_refuses_ok` | FAILED: OK still enabled after report arrival | PASSED; OK allowed while pending and disabled on arrival |
| `test_unavailable_stored_scenario_passes_on_the_real_dialog` | FAILED: stored unavailable encoder left OK enabled | PASSED; no write/apply/close and exactly one settings-owned error matching the note |
| `test_planted_stored_unavailable_accepted_is_caught` | PASSED: scenario catches the stored-equality bypass | PASSED; fails by the named `reported-unavailable stored encoder left OK enabled` assertion |
| `test_auto_is_resolved_by_a_rule_that_disagrees_with_the_interim_rule[injected-enables-ten-bit]` | PASSED | PASSED |
| `test_auto_is_resolved_by_a_rule_that_disagrees_with_the_interim_rule[injected-disables-ten-bit]` | PASSED | PASSED |

The injected-rule tests deliberately disagree in both directions: available
8-bit NVENC plus 10-bit x265 makes the interim rule choose NVENC while the
injected rule chooses x265, enabling 10-bit with an empty note. In the reverse
case, x265 plus an available named 8-bit test encoder makes the interim rule
choose x265 while the injected rule chooses the 8-bit encoder, disabling 10-bit
with `<name> cannot write 10-bit video.`. Both assert the spy saw only
`("auto", capabilities)` and check the enabled state, note and tool tip.
The existing agreeing injected-rule test remains unchanged.

### Product change and truth table

Changed `_encoder_unacceptable`, `_update_encoder_note`, `_on_encoder_changed`
and `accept`. `_encoder_unacceptable` now checks reported availability before
the stored-unreported exception; its docstring carries this table:

| Selected | Sink report | Stored? | OK |
|---|---|---|---|
| `auto` | any | any | allowed |
| any | still being read | any | allowed; control disabled, re-evaluate on arrival |
| name | reported unavailable | stored or picked | refused |
| name | reported available | any | allowed |
| name | absent, or report failed | stored | allowed (Q3) |
| name | not reported | picked | refused |

The refusal note uses the exact prescribed template and the capability reason,
or `not available`. The full sentence is ASCII-escaped. Encoder changes refresh
the note; an acceptable choice removes the refusal. A direct `accept()` refreshes
the note and presents that same sentence through `_present_error`, returning
before saving/applying/closing. `_refresh_ok` and catalog-arrival refresh reuse
the new refusal predicate. Detection and the injected 10-bit rule are unchanged.
Reason text is used verbatim, including a reason's own terminal punctuation.

### Gates, fixes and verification

Every pytest run used the supplied sandbox shim and disabled cacheprovider,
both targeted files, offscreen Qt and `--basetemp=work/wp3.20r/tmp-t3 -q`.

| Check | Observed result | Log under `work/wp3.20r/` |
|---|---|---|
| Tests before product edit | Exit 1; **4 failed, 72 passed in 7.16s**, no setup errors | `turn3-red-pytest.log` |
| First head run | Exit 0; **76 passed in 6.19s** | `turn3-green-pytest.log` |
| Initial mypy | Exit 1; `Returning Any from function declared to return "bool" [no-any-return]` at the new missing-capability comparison | `turn3-mypy.log` |
| Final targeted run after the type fix | Exit 0; **76 passed in 6.62s** | `turn3-final-pytest.log` |
| Final `uv run ruff check .` | Exit 0; **All checks passed!**; two access-denied traversal warnings | `turn3-final-ruff-check.log` |
| Final `uv run ruff format --check .` | Exit 101; **Expected a ruff source file** (same sandbox panic) | `turn3-final-ruff-format.log` |
| Format check of the two changed Python files | Exit 0; **2 files already formatted** | `turn3-final-owned-format-check.log` |
| Final `uv run mypy` | Exit 0; **Success: no issues found in 132 source files** | `turn3-final-mypy.log` |

Verification loop: suspected the stored-equality bypass; confirmed independently
by the four red failures on unchanged product code; fixed the predicate and both
message surfaces; the whole targeted run passed. Mypy confirmed an `Any` leak
from Qt's `currentData()` comparison; normalized the selected name to `str`,
then reran tests and static gates. The planted bypass still fails its named
scenario. Final code inspection confirms each truth-table branch and the early
return before save/apply/close. No new in-scope finding in the final pass.

`test_a_stored_encoder_this_computer_does_not_report_is_kept` and
`test_a_failed_detection_gives_a_stored_encoder_the_failure_as_its_reason`
pass in the final targeted run and remain unchanged. No DR-52 implementation
change. No reviewer yet; report-bullet replacement remains turn 5's task.
Limits: default formatter command needs dispatcher confirmation outside sandbox;
full suite remains the orchestrator's. Owned files only; no interface, dependency,
local-config or footage change; no OS-specific product code; no git writes,
reviewer or mailbox activity. LF and unchanged-test checks are recorded in
`work/wp3.20r/turn3-deliverable-check.log`.
