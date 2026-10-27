# WP3.20R cumulative ledger

## Dispatch and scope

- Current package diff base: **`528d865`**, after the dispatcher rebase before
  turn 4. Use this base for review and the final report.
- Historical turn 1: read, reproduce, table; branch `wp3.20r`, base and observed HEAD
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
  Dispatcher-supplied end-of-turn-3 figure: **111,584**, supplied at the turn-4
  gate; turn 3 originally committed as `26b8ff5`, now rebased as `7c43b65`.
  Dispatcher-supplied end-of-turn-4 figure: **131,507**, supplied at the turn-5
  gate; turn 4 committed as `d80a921`. Dispatcher-supplied end-of-turn-5 figure:
  **149,041**, supplied at the round-1 gate; turn 5 committed as `a0de531`.
  Turn-6 figure not yet supplied. Reviewer A round 1 terminated; see its
  adjudication and cleanup record below.

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

| Reviewer A round | Severity counts | In / out of envelope | NEW / REOPENED | Reverts | Product / test-only fixes | Transport / CLI | Verdict | Dispatcher token figure |
|---|---|---|---|---|---|---|---|---|
| 1 | critical 0; major 0; minor 3; advisory 3 | 6 / 0 | 6 / 0 | 0 | 4 finding cleanups / 1 planted-test signature adaptation; 5 new regression/control functions | `claude -p` opus/high via `scripts/codex_cell.py review`; local CLI 2.1.300 | `NO_NEW_CRITICAL_MAJOR`; TERMINATED, one cleanup; no round 2 | 149,041 |

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

## Turn 4: DR-55

### Rebase and carried gate evidence

The dispatcher rebased the branch onto main **`528d865`**, the new package diff
base. Main added harness files only; the three package commits' content is
unchanged. Historical run records above retain the original hashes; mapping:

| Turn | Original commit | Rebased commit |
|---|---|---|
| 1 | `c46eb1a` | `ea22295` |
| 2 | `944b5d2` | `db71de3` |
| 3 | `26b8ff5` | `7c43b65` |

The dispatcher confirmed the turn-3 tree's repository formatter outside the
sandbox: **227 files already formatted**, exit 0. The cell's exit 101 remains
a sandbox artifact. No broad formatting diagnostic was repeated.

Read the newly committed `scripts/sandbox_mkdir_shim.py` (introduced on main
at `542bc11`). It wraps `os.mkdir`, widening only 0o700 to 0o777, with typed
arguments and otherwise unchanged forwarding. All turn-4 pytest runs used
`QT_QPA_PLATFORM=offscreen`, `PYTHONPATH=scripts`,
`-p sandbox_mkdir_shim -p no:cacheprovider`, both targeted files and
`--basetemp=work/wp3.20r/tmp-t4 -q`. The old `work/sandbox/`, inaccessible temp
root and cache directories were left untouched. The committed harness shim was
read only and is not a package change. Seat gate runs never load it.

### Tests first and observed red results

Extended the owned test file's `FakeChoosers` with `raise_on_choose` and
`raise_on_confirm`, each an exception instance or None. Added five test
functions, nine parameterized cases, plus `_chooser_scenario`; extended the
existing ASCII-message test. All were run before editing the slots, on
unchanged product code at `7c43b65`.

| Test | Unchanged module | Final head |
|---|---|---|
| `test_a_raising_folder_chooser_is_a_settings_error[idle]` | FAILED and Qt teardown ERROR: OSError escapes, settings error missing | PASSED |
| `test_a_raising_folder_chooser_is_a_settings_error[analysis-running]` | FAILED and Qt teardown ERROR: same escape | PASSED; Clear cache remains disabled for analysis |
| `test_a_raising_confirmation_is_a_settings_error_and_clears_nothing` | FAILED and Qt teardown ERROR: RuntimeError escapes | PASSED; no cache call, `_clearing` False, button enabled |
| `test_a_dialog_still_works_after_a_chooser_failure[choose]` | FAILED and Qt teardown ERROR at initial chooser failure | PASSED; second click chooses the folder |
| `test_a_dialog_still_works_after_a_chooser_failure[confirm]` | FAILED and Qt teardown ERROR at initial confirmation failure | PASSED; second click clears the cache once |
| `test_chooser_scenario_passes_on_the_real_dialog[choose]` | FAILED and Qt teardown ERROR | PASSED |
| `test_chooser_scenario_passes_on_the_real_dialog[confirm]` | FAILED and Qt teardown ERROR | PASSED |
| `test_planted_unwrapped_chooser_is_caught[choose]` | PASSED | PASSED; scenario detects missing settings error and capture records the deliberately escaped OSError |
| `test_planted_unwrapped_chooser_is_caught[confirm]` | PASSED | PASSED; same, with RuntimeError |
| Extended `test_every_message_of_the_dialog_is_ascii` | FAILED and Qt teardown ERROR: new errors absent and non-ASCII exceptions escape | PASSED; both new texts have escaped non-ASCII details and settings ownership |

The red summary was **8 failed, 77 passed, 8 errors in 8.85s**, exit 1. The
eight errors were pytest-qt reporting the intended escaped slot exceptions,
not setup failures. Normal regression cases click real buttons without capturing
exceptions. Only the planted cases capture their deliberately escaped exception
with `qtbot.captureExceptions`, then verify the shared scenario fails by the
named `chooser failure did not present exactly one settings error` assertion.

The shared scenario checks unchanged output folder/label, session and settings
file bytes, non-Accepted result, `_clearing` False, no cache clear/limit calls,
and the clear-button/cache-note state for the analysis phase. Both retry paths
reuse the same dialog; successful choosing/clearing does not claim to clear the
earlier settings banner (that is successful save's existing behavior).

### Product behavior

Changed only `_on_choose_folder` and `_on_clear_clicked` this turn. Each catches
`Exception` around its injected chooser call, with the foreign-injected-code
comment, and reports through `_present_error`:

- `The output folder could not be chosen: <error>`
- `The cache was not cleared: the confirmation failed: <error>`

Both return before changing the folder or launching cache work. Confirmation
failure also refreshes the button for the current analysis phase. The cache
clearing flag remains False. The existing presenter escapes non-ASCII text;
tests exercise a snowman in the folder error and an accented character in the
confirmation error, asserting their literal ASCII escapes and owner `settings`.
Updated the two slot docstrings to reflect the behavior.

### Gates and verification loop

| Check | Observed result | Log under `work/wp3.20r/` |
|---|---|---|
| Tests before product edit | Exit 1; **8 failed, 77 passed, 8 errors in 8.85s** | `turn4-red-pytest.log` |
| First head run | Exit 0; **85 passed in 6.26s** | `turn4-green-pytest.log` |
| Initial Ruff check | Exit 1; `SIM117` on nested capture/assertion contexts in the planted test | `turn4-ruff-check.log` |
| Final targeted run after combining the contexts | Exit 0; **85 passed in 6.68s** | `turn4-final-pytest.log` |
| Final `uv run ruff check .` | Exit 0; **All checks passed!**; two access-denied traversal warnings | `turn4-final-ruff-check.log` |
| Final `uv run ruff format --check .` | Exit 101; **Expected a ruff source file** (sandbox artifact) | `turn4-final-ruff-format.log` |
| Owned Python file format check | Exit 0; **2 files already formatted** | `turn4-final-owned-format-check.log` |
| Final `uv run mypy` | Exit 0; **Success: no issues found in 132 source files** | `turn4-final-mypy.log` |

Verification loop: suspected unguarded injected calls; confirmed by the red
assertions and independent pytest-qt exception reports for both slots; fixed
with narrowly placed catches and the specified settings messages; all targeted
tests passed. Ruff confirmed a test-only context-style slip; combined the
contexts and repeated the whole targeted run and gates. Both planted unwrapped
slots still fail their scenario by name. Final code inspection confirms no
folder assignment or cache-job scheduling precedes the injected call's success.
No new DR-55 issue found in the final pass. Reviewer A is still pending turn 5.

No scope deviation or open product question. Default repository formatting
needs seat confirmation; full suite remains the orchestrator's. Scope, LF,
ASCII-ledger and protected-test source checks are recorded in
`work/wp3.20r/turn4-deliverable-check.log`. Only the three owned files changed;
frozen interfaces, dependencies, local config, harness shim and footage are
untouched. No OS-specific product code, git writes, reviewer or mailbox activity.

## Turn 5: report and static gates

Starting HEAD `d80a921`; cumulative package diff base remains **528d865**.
Dispatcher-supplied end-of-turn-4 token figure **131,507** recorded above.
The dispatcher confirmed turn-4 global formatting outside the sandbox:
**227 files already formatted**, exit 0 (seat evidence, not a cell rerun).

Wrote `docs/reports/wp3.20r-settings-hardening.md`: changes per row, corrected
encoder claim and full truth table, pre-fix/head evidence, the ruled DR-53
constructor non-reproduction and actual divergence reproduction, planted
controls, HD-1 counts, gate results and limits. It supersedes historical
WP3.20 narrative for these rows, explicitly including the suffix accept order;
the old report's other historical content remains outside the authorized edit.
Replaced only the unavailable-capability bullet under "Encoder and 10-bit rules"
in `docs/reports/wp3.20-settings.md`, with the reported-unavailable refusal,
stored-unreported allowance and pending-detection behavior. No product/test edit.

### HD-1 count

AST/source comparison against `528d865` in `work/wp3.20r/turn5-test-counts.log`:
base 44 and head 59 test functions; **15 new**, **1 changed**, no removed tests.
The changed function is `test_every_message_of_the_dialog_is_ascii`. New tests
include **3 planted-control functions** (4 cases) and **3 real-scenario control
functions** (5 cases), leaving 9 primary new functions. This matches the brief's
15-function estimate; parameterization adds 21 cases overall, 64 -> 85 targeted
cases (81 dialog plus 4 unchanged dependency cases).

### Final turn-5 gates

Pytest used `QT_QPA_PLATFORM=offscreen`, `PYTHONPATH=scripts`,
`-p sandbox_mkdir_shim -p no:cacheprovider`, both targeted files and
`--basetemp=work/wp3.20r/tmp-t5 -q`. Gate runs at the seat never load the shim.

| Command | Observed result | Log under `work/wp3.20r/` |
|---|---|---|
| Targeted pytest | Exit 0; **85 passed in 9.00s** | `turn5-pytest.log` |
| `uv run ruff check .` | Exit 0; **All checks passed!**; two access-denied traversal warnings | `turn5-ruff-check.log` |
| `uv run ruff format --check .` | Exit 101; **Expected a ruff source file** (sandbox artifact) | `turn5-ruff-format.log` |
| Owned Python file format check | Exit 0; **2 files already formatted** | `turn5-owned-format-check.log` |
| `uv run mypy` | Exit 0; **Success: no issues found in 132 source files** | `turn5-mypy.log` |

Verification loop: DR-53 field/applied divergence confirmed on unchanged code,
constructor truncation rejected by runtime measurements, actual applied-value
validation and missing settings error fixed; DR-54 bypass confirmed then fixed,
the stronger disagreeing resolver tests already passed; DR-55 escaped calls
confirmed by assertions plus pytest-qt and fixed. Planted implementations still
fail all named shared scenarios; catcher tests pass. The complete targeted
turn-5 run found no new in-scope issue. Compared report claims with those measured
paths, the product diff and gate results. No product/test correction this turn.

Review status: **Reviewer A not yet run**; dispatcher runs it after this handoff.
No convergence verdict is claimed. No open product question or scope deviation.
Global formatting awaits turn-5 seat confirmation; the full suite remains the
orchestrator's. Only owned docs changed this turn; cumulative owned-file scope,
one-bullet-only replacement, LF and report length are checked in
`work/wp3.20r/turn5-deliverable-check.log`. Interfaces, dependencies, local config,
committed shim and footage untouched; no OS-specific code, git writes, reviewer
or mailbox activity.

## Reviewer A round 1: terminating adjudication and cleanup (turn 6)

Input: `528d865..a0de531`. Read all of
`C:/Users/rwsmy/clearwater-review-evidence/wp3.20r/r1/review.txt` and its md5
manifest. Review text md5 **baf1eaf2fdf36ee030eb2dd49af75c57** independently
verified. Durable prompt, diff, input, JSON and review text are in that same
external evidence folder; it was read only. Dispatcher assertions: requested
`claude-opus-5-5` high; `is_error` false; 33 turns; worktree clean afterwards;
8 read-only-policy permission denials (not defects or transport failures).
Transport: `claude -p --model opus --effort high`, driven by
`scripts/codex_cell.py review`. Local `claude --version` reads **2.1.300 (Claude
Code)** (`work/wp3.20r/turn6-claude-version.log`); the version of the completed
review invocation was not separately asserted by the dispatcher.

Verdict: **NO_NEW_CRITICAL_MAJOR**, 0 critical, 0 major, 3 minor, 3 advisory;
ZERO NEW BLOCKING terminates under fill Part 1. No round 2, no new reviewer,
no reverts and no reopened findings. All six findings are NEW and within the
declared operating envelope; cleanup scope is narrower than operating envelope,
as specified for the declined/banked advisories below. Findings retain the
reviewer's **EXECUTED** tag; none was tagged REASONED.

### Every finding adjudicated

| # | Severity / envelope / tag | Independent confirmation or rejection | Disposition |
|---|---|---|---|
| 1 | MINOR; IN; EXECUTED; NEW | New applied-encoder regression FAILED on unchanged `a0de531`: default combo plus current-session `hevc_nvenc` wrote settings. | CONFIRMED, FIXED: `accept` passes `new.video_encoder` into the predicate/note. Their default queries use edited settings, and Q3 compares the current session's stored value. Refusal disables OK, shows the actual reason and returns before save/apply/close. Added unavailable-current-session test and two current-unreported controls. |
| 2 | MINOR; IN; EXECUTED; NEW | PARTIALLY CONFIRMED: direct Return without explicit focus did not accept; own probe showed NO default button, result 0, dialog still visible/open. Explicitly focusing the suffix gave default OK and Accepted. The claimed Cancel default / silent close was NOT reproduced and is rejected on this measured surface. | Applied the expressly authorized ONE-LINE default restoration in `_refresh_ok`. The direct-Return regression FAILED without it and now PASSES. Mechanism predates package (`54e2749`); owner explicitly authorized this one-line cleanup despite the fill's normal provenance banking rule. |
| 3 | MINOR; IN; EXECUTED; NEW | New in-dialog suffix-reason regression FAILED on unchanged code: `suffix_error` empty after applied stored suffix `bad/suffix` was refused. | CONFIRMED, FIXED: after `_check_suffix`, `accept` shows the actual validation reason in label/tool tip and refreshes OK. A different valid edit clears it and saves. The existing unchanged-control writeback rule was not redesigned. |
| 4 | ADVISORY; IN; EXECUTED; NEW | Scratch run confirmed ASCII detail length 200 with a trailing lone backslash for 100 accented characters plus `/`; repeated after cleanup with same result. | CONFIRMED, DECLINED as cosmetic. Preserve Q5's ASCII 200-character bound; complete-escape truncation would add a formatting rule beyond the literal cut. No acceptance/state failure; disclosed in report and final handoff. |
| 5 | ADVISORY; IN; EXECUTED; NEW | New punctuation regression and four adjusted note/scenario cases FAILED on unchanged code for `found.. Choose`. | CONFIRMED, FIXED trivially in `_update_encoder_note`: reuse one terminal full stop. Note and settings message match, fallback reason unchanged. |
| 6 | ADVISORY; IN; EXECUTED; NEW | Scratch run confirmed two identical errors after two direct accepts, and one chooser error left after a successful session-only accept with a refused settings file; file bytes unchanged. Repeated after cleanup. | CONFIRMED, BANKED: message deduplication and clearing on session-only acceptance are outside DR-53..55 cleanup; brief explicitly excludes changing OK's refused-settings-file behavior. Save-only clearing/presentation predates package at `54e2749`; no banner lifecycle redesign. |

Independent advisory/default probes: `work/wp3.20r/turn6_advisory_probe.py`,
logs `turn6-advisory-probe.log` (unchanged code) and
`turn6-advisory-after-cleanup.log`. The latter confirms direct Return now has
default OK after encoder correction and accepts whether explicit focus is set
or not. It also confirms advisories 4, 6a and 6b remain exactly as disclosed.

Provenance evidence: `git log -S 'context.messages.clear(owner=OWNER_SETTINGS)'`,
`git log -S 'context.messages.present'`, and
`git log -S 'self.ok_button.setEnabled(not self.suffix_error.text()'` over the
owned module each identify **54e2749**, WP3.20's original dialog. Logs:
`turn6-banner-origin.log`, `turn6-present-origin.log`, `turn6-default-origin.log`.

### Red / green / verification record

All pytest runs used offscreen Qt, `PYTHONPATH=scripts`, the committed mkdir
shim, disabled cacheprovider, both targeted files and `tmp-t6`; the keyboard
confirmation filtered those same files with `-k return_saves_edits`.

| Check | Observed result | Log under `work/wp3.20r/` |
|---|---|---|
| Initial regression run before product edit | Exit 1; **7 failed, 84 passed in 9.47s**: applied encoder, missing local suffix reason, punctuation/new expected-note cases; explicit-focus Return variant already passed | `turn6-red-pytest.log` |
| Revised direct-Return regression before product edit | Exit 1; **1 failed, 90 deselected in 1.02s**; result 0, not Accepted | `turn6-default-red-pytest.log` |
| First head run | Exit 1; **1 failed, 90 passed in 7.28s**; only planted stored-bypass adapter rejected the new optional argument with TypeError | `turn6-green-pytest.log` |
| Final targeted run after adapter correction | Exit 0; **91 passed in 9.60s** | `turn6-final-pytest.log` |
| `uv run ruff check .` | Exit 0; **All checks passed!**; two old access-denied traversal warnings | `turn6-ruff-check.log` |
| `uv run ruff format --check .` | Exit 101; **Expected a ruff source file** (same sandbox artifact) | `turn6-ruff-format.log` |
| Owned-file format check | Exit 0; **2 files already formatted** | `turn6-owned-format-check.log` |
| `uv run mypy` | Exit 0; **Success: no issues found in 132 source files** | `turn6-mypy.log` |

The initial explicit-focus keyboard variant passing was investigated rather
than reported as a failing check. Cached-report setup plus an unfocused direct
key event confirmed the narrower default-restoration issue before implementation.
All four changed product behaviors have a regression that failed without the
fix. Two extra current-unreported controls already passed and protect Q3 from
over-refusal. The planted adapter now accepts the optional argument while still
restoring the wrong stored-equality bypass; it fails the same named assertion,
not a TypeError. No review finding was reopened by this test-only adaptation.

Verification loop: suspect -> independent red/probe -> classify -> fix 1/2/3/5
once -> repeat whole targeted run and statics. Final inspection confirms one
edited settings snapshot is applied; encoder refusal uses that snapshot's name;
both refusal branches return before saving/applying/closing; suffix label/tool
tip show the actual reason; optional encoder arguments retain Q3's current
stored value; default restoration is one line. The final pass found no new
in-scope issue. Retained cosmetic/banner limits are explicit rather than silently
counted as fixed. Review input's independent original-base run was also recorded
by Reviewer A: **16 failed, 65 passed, 8 errors**, the 81 input dialog cases.

### Final report, counts and scope

Updated the hardening report by replacement for actual-value encoder validation,
local suffix reason, default restoration, punctuation, current-session Q3
controls, final counts/gates and Reviewer A's terminating verdict/retained limits.
The old WP3.20 report is untouched this turn; its one-bullet correction still
stands, now also true for the session-divergence encoder route.

AST/source comparison with package base `528d865`: **44 -> 64 test functions**,
**20 new**, **1 changed original** (ASCII test), no removals; 3 planted and
3 real-scenario control functions remain. Cleanup adds 5 functions / 6 cases;
the new total is **91 cases**, 87 dialog plus 4 unchanged deps, 27 above base.
Two previously added functions changed during cleanup (punctuation expectation
and planted adapter); no original Q3 or agreeing-resolver test changed. Counts
and review md5 check: `work/wp3.20r/turn6-test-counts.log`.

Reviewer A is **TERMINATED at round 1**, with one non-blocking cleanup. No extra
round or approval request. Outstanding gate work belongs to the orchestrator:
seat confirmation of global formatting, full suite, Reviewer B and acceptance.
No scope deviation; declined/banked advisories 4 and 6 are the disclosed limits.
Final LF, one-bullet-only historical-report preservation, protected test sources,
four-file turn scope and five-file package scope are checked in
`work/wp3.20r/turn6-deliverable-check.log`. Interfaces, contract, shared fixtures,
dependencies, shim, local config and footage untouched; no OS-specific product
code, git writes, reviewer run or mailbox activity by this cell.
