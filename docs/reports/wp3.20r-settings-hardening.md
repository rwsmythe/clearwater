# WP3.20R: settings dialog hardening

Scope: DR-53, DR-54, DR-55 only; package diff base **528d865**; spec v0.5.5.
This report supersedes WP3.20 narrative for these rows, including accept order; only its authorized capability bullet changed.

Changes in `src/clearwater/gui/settings_dialog.py`:

- DR-53: `accept()` builds `edited_settings()` once and validates `new.output_suffix` before
  save/apply/close. Failure calls `_check_suffix()` and presents a settings-owned error with
  ASCII detail cut to 200 characters; a corrected suffix can then be saved.
- DR-54: `_encoder_unacceptable`, `_update_encoder_note`, `_on_encoder_changed`, `accept`:
  an encoder the sink reports unavailable is refused whether stored or picked; OK is disabled,
  its reason is visible in `encoder_note`, and direct accept presents the same settings error.
  A stored unreported encoder (including report failure) stays shown unavailable and is written
  back unchanged unless edited. Pending detection disables the control and defers refusal;
  report arrival re-evaluates OK. Acceptable selection clears the refusal note. Q3 stands.
- DR-55: `_on_choose_folder` and `_on_clear_clicked` catch `Exception` around injected calls,
  with the foreign-code comments. Failures present the specified settings-owned errors,
  ASCII-escape exception text, preserve folder/cache state and permit retry.

Encoder truth table (also in `_encoder_unacceptable`'s docstring; 10-bit rule unchanged):

| Selected | Sink report | Stored? | OK |
|---|---|---|---|
| `auto` | any | any | allowed |
| any | still being read | any | allowed; re-evaluate on arrival |
| name | reported unavailable | stored or picked | refused |
| name | reported available | any | allowed |
| name | absent or report failed | stored | allowed |
| name | not reported | picked | refused |

Tests ran before each row's product edit; names/logs: `docs/proofs/wp3.20r-ledger.md`. "Base" means that row's unchanged pre-fix module.

| Row / named evidence | Base result | Final head |
|---|---|---|
| DR-53: `test_a_stored_suffix_that_fails_validation_in_its_last_character_is_refused`, `test_a_stored_suffix_with_a_newline_is_refused` | Already refused, but complete tests FAILED for missing settings error | PASSED |
| DR-53: `test_stored_suffix_scenario_passes_on_the_real_dialog` (2 cases) | FAILED: invalid applied suffix written | PASSED |
| DR-54: stored-unavailable refusal, recovery, pending-report and `test_unavailable_stored_scenario_passes_on_the_real_dialog` | 4 FAILED: OK enabled for stored unavailable encoder | PASSED |
| DR-54: `test_auto_is_resolved_by_a_rule_that_disagrees_with_the_interim_rule` (both directions) | 2 PASSED; existing behavior tested more strongly | PASSED |
| DR-55: raising folder/confirmation, retry, `test_chooser_scenario_passes_on_the_real_dialog`, extended ASCII test | 8 FAILED plus 8 pytest-qt slot-exception errors | PASSED |

Planted controls: `test_planted_field_only_suffix_check_is_caught`, `test_planted_stored_unavailable_accepted_is_caught`, `test_planted_unwrapped_chooser_is_caught`.
All catcher tests pass on base/head; their wrong implementations fail the named shared scenarios.
DR-53 Q1 reproduction: constructor kept all 32768 characters and the newline; no truncation or
flattening occurred, so base already refused both. The positive control opens on defaults,
uses session `set_settings` to install `bad/suffix` with the field unedited, and catches the
base accepting/writing it. This deterministic divergence is fixed; no suffix length rule added.

HD-1: 44 -> 59 test functions: **15 new**, **1 changed** (ASCII test), no removals;
the 15 include **3 planted-control** and **3 real-scenario control** functions. New cases: 21.
Final targeted run: **85 passed in 9.00s** (81 dialog + 4 unchanged dependency cases); `PYTHONPATH=scripts`, committed mkdir shim, cacheprovider disabled, `tmp-t5`.
Static gates: Ruff check **All checks passed!**; mypy strict **Success: no issues found in 132
source files**. Sandbox `ruff format --check .`: exit 101, **Expected a ruff source file**;
owned-file format check: **2 files already formatted**. Dispatcher confirmed turn-4 global
formatting outside sandbox: **227 files already formatted**, exit 0. Turn-5 logs: `work/wp3.20r/turn5-*`.
Verification: red failures confirmed all three defects; fixes and planted controls verified;
final targeted pass found no new in-scope issue. Reviewer A: pending after this handoff.
Limits: global formatting needs seat confirmation; full suite is the orchestrator's; DR-52 and other historical report content unchanged.
Owned files/LF, interfaces, dependencies, local config and read-only footage locks honored. No OS-specific product code or open product question.
