# WP3.20R: settings dialog hardening

Scope: DR-53..DR-55; spec v0.5.5; diff base **528d865**. This report supersedes WP3.20
narrative for these rows, including accept order; only its authorized capability bullet changed.

Product methods changed: `accept`, `_encoder_unacceptable`, `_update_encoder_note`,
`_on_encoder_changed`, `_refresh_ok`, `_on_choose_folder`, `_on_clear_clicked`.

- DR-53: validate the one `edited_settings()` object subsequently saved/applied. A suffix
  refusal calls `_check_suffix`, shows the applied-value error beside the field and in its
  tooltip, disables OK, and presents a settings-owned error with ASCII detail cut to 200 chars.
- DR-54: validate the encoder actually applied, including session/unedited-control divergence.
  A reported-unavailable encoder is refused whether stored or picked: OK disabled, reason
  visible, direct accept presents the same settings error. A reason's terminal full stop is
  reused. An acceptable choice clears the refusal note; enabled OK is made the default.
- DR-55: catch `Exception` only around injected chooser calls, with foreign-code comments.
  Settings errors escape non-ASCII details; folder/cache state is preserved and retries work.

Encoder truth table (also in `_encoder_unacceptable`'s docstring; 10-bit rule unchanged):

| Encoder to apply | Sink report | Stored in current session? | OK |
|---|---|---|---|
| `auto` | any | any | allowed |
| any | still being read | any | allowed; disabled control, re-evaluate on arrival |
| name | reported unavailable | stored or picked | refused |
| name | reported available | any | allowed |
| name | absent or report failed | stored | allowed; kept unchanged unless edited (Q3) |
| name | not reported | picked | refused |

Tests ran before each fix; "base" below is the unchanged pre-fix module. Full names/logs:
`docs/proofs/wp3.20r-ledger.md`; reviewer r1 separately compared its 81 input dialog cases with base 528d865.

| Evidence | Base / pre-cleanup result | Final head |
|---|---|---|
| DR-53 constructor suffixes: final-character slash at length 32768; newline | Already refused; new complete tests FAILED for missing settings error | PASSED |
| `_stored_suffix_scenario` (2 cases) | FAILED: invalid applied suffix written | PASSED |
| DR-54 stored unavailable, recovery, pending report, real scenario | 4 FAILED: OK left enabled | PASSED |
| Disagreeing injected resolver, both 10-bit directions | 2 PASSED already; spy and enabled state prove rule use | PASSED |
| DR-55 chooser failures, retry, real scenarios, extended ASCII test | 8 FAILED + 8 pytest-qt escaped-slot errors | PASSED |
| R1 applied encoder, visible suffix reason, direct Return, single punctuation | Each new regression FAILED without its fix; current-unreported controls already PASSED | PASSED |

Planted catchers: `test_planted_field_only_suffix_check_is_caught`, `test_planted_stored_unavailable_accepted_is_caught`, `test_planted_unwrapped_chooser_is_caught`.
Their wrong implementations fail named shared scenarios; all catcher tests pass on final head.
DR-53 Q1: constructor kept all 32768 characters/newline, so truncation was NOT reproduced.
The positive control opens defaults, installs `bad/suffix` through session `set_settings`
without editing the field, then catches base accepting/writing it. No suffix length rule added.

HD-1: 44 -> 64 test functions: **20 new** (15 build + 5 cleanup), **1 changed**, no removals;
new functions include **3 planted** and **3 real-scenario controls**; 27 added cases, 64 -> 91.
Final shim run: **91 passed in 9.60s** (87 dialog + 4 unchanged dependency cases), offscreen,
`PYTHONPATH=scripts`, cacheprovider disabled, `tmp-t6`. Ruff: **All checks passed!**; strict mypy:
**Success: no issues found in 132 source files**. Global format: exit 101, **Expected a ruff
source file** (sandbox artifact); owned format: **2 files already formatted**. Logs: `work/wp3.20r/turn6-*`.
Reviewer A r1: **0 critical, 0 major, 3 minor, 3 advisory; NO_NEW_CRITICAL_MAJOR**; loop terminated.
Cleanup fixes 1, 3, 5; finding 2's narrower direct-Return failure gets the authorized one-line fix.
Own probe did not reproduce Cancel/closing: without focus Return left dialog open; with focus it saved.
Limits: advisory 4's cosmetic split escape at the 200-char cut is declined; advisory 6's duplicate
and stale session-only banners are banked (pre-existing save-only clearing). DR-52 unchanged.
Global formatting needs seat confirmation; full suite is the orchestrator's. Owned files/LF,
interfaces, dependencies, local config and read-only footage locks honored; no OS-specific code.
