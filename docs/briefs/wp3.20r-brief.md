# WP3.20R — Settings dialog hardening (dispatch brief, DRAFT)

**Status:** DRAFT 2026-10-27, written by a drafting helper for the orchestrator (generation 12) at
CHARC's ruling `6f725eee`. Not approved; base = the pre-dispatch main commit named at dispatch.
Owner decisions: none inside the package.
- Spec **v0.5.5**. Rows: `docs/debt-register.md` DR-53, DR-54, DR-55 (quoted below). Package
  hardened: WP3.20, brief `docs/briefs/wp3.20-brief.md`, report `docs/reports/wp3.20-settings.md`,
  accept `docs/proofs/wp3.20-accept.md`. Ruling: CHARC gen 4 `6f725eee` item 2.
- Cell: **`implementer-codex-sol-high`** (gpt-6.1-sol / high), the CALIBRATION package of the
  Codex lane (design pass `docs/proofs/harness-dual-model-implementers.md` section 4.3). Tier
  **STRONG**. Reviewer A and Reviewer B are the CLAUDE pass (`scripts/codex_cell.py review`,
  opus/high); both are run by the orchestrator, never by you.
- Worktree `.worktrees/wp3.20r`, branch `wp3.20r`, base = the main commit named at dispatch.
- **Calibration size facts** (for HD-1; counted at drafting): product module
  `src/clearwater/gui/settings_dialog.py` 851 lines; test file `tests/test_gui_settings_dialog.py`
  868 lines, 44 test functions; 3 register rows; planned about 15 test functions (9 primary, 6
  positive controls: a pass-on-the-real-dialog test and a planted-defect test per row). The ruling
  estimated 4 to 6 tests; the planted-defect rule of the fill (Part 3) accounts for the difference.

**Why.** WP3.20 was accepted with three minors that two reviewer passes found on the accepted
tree and that the accept left open: a stored value the dialog never validates (DR-53), a stored
encoder the sink reports unavailable that OK accepts (DR-54), and an injected chooser whose
exception escapes a slot (DR-55). All three are in one module with fixed tests. This package
closes them and nothing else.

| Field | Content |
|---|---|
| ID and title | WP3.20R — Settings dialog hardening; debt rows DR-53, DR-54, DR-55; module `clearwater.gui` |
| Goal | `accept()` refuses a stored suffix that fails `validate_suffix`; OK is refused, with a `settings`-owned message, for an encoder the sink reports as unavailable even when it is the stored value; an exception from `choose_folder()` or `confirm()` becomes a `settings`-owned error instead of escaping the slot. |
| Rows as the register reads | **DR-53:** "`accept()` validates the field text, not `new.output_suffix`, and the unedited stored value is saved and applied. In envelope (an accepted settings file); MINOR." Remedy: "validate `new.output_suffix` in `accept()`; a test with a stored 32768-char suffix." **DR-54:** "a stored `video_encoder` that the sink still REPORTS but as unavailable (a broken driver) is accepted unchanged because the selection equals the stored value; the WP3.20 Q3 ruling covered only a stored encoder no longer reported ... Also: `test_auto_is_resolved_by_the_injected_rule` injects a rule that agrees with the interim rule, so a dialog using a restated rule passes." Remedy: "refuse OK ... for a reported-unavailable stored encoder, with a test; the injected-rule test uses a DISAGREEING rule and asserts the 10-bit state." **DR-55:** "an exception from an injected chooser (`choose_folder()` raising `OSError`, `confirm()` raising) escapes the slot with no `settings`-owned message ... `FakeChoosers` never raises, so no test covers it." Remedy: "wrap the chooser calls in the slots' existing failure path; a test with a raising chooser." |
| Rulings that bind | CHARC `6f725eee` item 2: "Scope = DR-53, DR-54, DR-55 exactly as the register rows read; DR-52's `resolve_encoder` swap stays WP4.3's. DR-54 disposition RULED: REFUSE OK with a `settings`-owned message for a stored encoder the sink reports as unavailable (not a silent fall-back to auto); the injected-rule test uses a DISAGREEING rule and asserts the 10-bit state." WP3.20 brief Rulings: Q3 "a stored encoder no longer reported kept and shown unavailable" STANDS unchanged. |
| Corrected claim (DR-54) | The register says the WP3.20 report and the reviewers' claim 3 "conflict". The accepted text that must change: report "Encoder and 10-bit rules": "an unavailable encoder cannot be accepted (OK is disabled if one is selected by any route and was not the stored value)", and brief WHAT TO EXAMINE "D74: no unavailable option selectable". **Corrected claim, to be true on your head:** an encoder the sink REPORTS as unavailable is never accepted, whether the user picked it or it is the stored value (OK is refused with the reason). A stored encoder the sink does NOT report (absent, or the report failed) is kept, shown unavailable, and written back unchanged unless the user picks another (Q3, unchanged). While the report is being read the encoder control is disabled and nothing is refused on the encoder; when the report arrives OK is re-evaluated. |
| Files owned | EDIT: `src/clearwater/gui/settings_dialog.py`, `tests/test_gui_settings_dialog.py`, `docs/reports/wp3.20-settings.md` (ONE bullet only, the "unavailable capability" bullet of "Encoder and 10-bit rules", replaced by the corrected claim; question 4). NEW: `docs/reports/wp3.20r-settings-hardening.md`, `docs/proofs/wp3.20r-ledger.md`. NOT owned: every other file; in particular `src/clearwater/interfaces/` (FROZEN; nothing under it changes), `src/clearwater/gui/contract.py` and the other `gui/` modules, `tests/gui_support.py`, `tests/test_gui_deps.py` (run, never change), `src/clearwater/config/`, `src/clearwater/jobs/`, `pyproject.toml`, `uv.lock`, `tests/conftest.py`, `docs/debt-register.md` (CHARC closes the rows at the accept). |
| Out of scope | DR-52 and everything in it (the `resolve_encoder` swap, the stand-in's error behaviour, `test_interim_rule_matches_the_wp310_rule`, the report's stale SHAs): WP4.3's. Any other settings module. Any change to what OK does for the cache, the folder, the refusal of the settings file or `last_parameters`. Encoder detection at start-up. New widgets, new settings, new strings other than the messages named below. A dependency. |
| Hardware flags | `gui` on every test that creates a Qt object; no `gpu`, no `footage`, no timing figure. The footage folder is not used. |
| Done | Plan 4.5 and the gates under "Notes for the cell"; every row shown by a named test that FAILS on the base and PASSES on your head (or the exception recorded, question 1); a planted wrong implementation fails by name for each row; the corrected claim true on disk; Reviewer A (Claude pass) converged. |

## Task ladder (one rung per turn; a turn is one `codex exec` run)

1. **Turn 1: read, reproduce, table. NO product code, NO test change.** Read the module and the
   test file (the quoted facts are below). Create the ledger `docs/proofs/wp3.20r-ledger.md` with:
   - the baseline: the targeted test count on the base (`uv run pytest tests/test_gui_settings_dialog.py
     tests/test_gui_deps.py`, see "Running tests"; the WP3.20 accept records 60 module cases + 4
     deps cases) and ruff/mypy status;
   - for each row, the REPRODUCTION on the base: a scratch script or scratch test under
     `work/wp3.20r/` (never committed) that opens the dialog on the stored value and records what
     `accept()` does. Expected: DR-54 and DR-55 reproduce; DR-53 may NOT (question 1);
   - the change table: per row, the method changed, the new behaviour, the test names;
   - what you observed about the sandbox: does `uv run pytest ... --basetemp` work, do `ruff` and
     `mypy` run.
   End the turn. Final message: the ledger summary and the FILES CHANGED block (the ledger only).
2. **Turn 2: DR-53.** In `accept()` validate `new.output_suffix` (the settings that would be
   applied, from `edited_settings()`), not only the field text. A failure: the dialog stays open,
   nothing is saved or applied, `_check_suffix()` is called, and a `settings`-owned error is
   presented (`_present_error`) reading "The output suffix is not valid: <ValueError text,
   ASCII, cut to 200 characters>" (question 5). Tests (first, see them fail where they can):
   - `test_a_stored_suffix_that_fails_validation_in_its_last_character_is_refused`: a stored
     suffix of 32767 `"a"` followed by `"/"` (32768 characters; `QLineEdit.maxLength()` is 32767
     and `validate_suffix` has no length rule, so the offending character must be the last);
   - `test_a_stored_suffix_with_a_newline_is_refused`;
   - `_stored_suffix_scenario` + `test_stored_suffix_scenario_passes_on_the_real_dialog` +
     `test_planted_field_only_suffix_check_is_caught`: the field and the stored value DIVERGE
     deterministically, for example open the dialog on the default settings, then
     `window.session.set_settings(dataclasses.replace(Settings(), output_suffix="bad/suffix"))`
     with the field unedited, then `dialog.accept()`; assert nothing was written
     (`settings.json` absent), the dialog result is not Accepted, and exactly one `settings`-owned
     error is presented. The planted dialog (monkeypatched `accept`) validates only
     `self.suffix_edit.text()` and must fail the scenario. If a better divergence route exists,
     use it and say why in the ledger.
   Each refusal test asserts: no write, the session's settings unchanged, the `settings` error,
   and that a corrected suffix then accepts.
3. **Turn 3: DR-54.** Change `_encoder_unacceptable` and its callers by the truth table; keep the
   table in its docstring:

   | selected | sink report | stored? | OK |
   |---|---|---|---|
   | `"auto"` | any | any | allowed (10-bit rule unchanged) |
   | any | still being read | any | allowed (the control is disabled; re-evaluated on arrival) |
   | a name | reported, `available` False | stored or picked | **REFUSED (changed for the stored case)** |
   | a name | reported, `available` True | any | allowed |
   | a name | not reported (absent, or the report failed) | the stored value | allowed (Q3, unchanged) |
   | a name | not reported | picked | REFUSED (unchanged) |

   On a refusal: `_refresh_ok` keeps OK disabled; the dialog shows the reason where the user can
   see it (`encoder_note`: "<name> is unavailable: <reason>. Choose another encoder.", the
   capability's `reason` or "not available"; it is cleared when an acceptable encoder is
   selected; `_update_encoder_note` today is not called on an encoder change, fix that); and
   `accept()`, when called while the choice is refused, presents a `settings`-owned error with the
   same sentence and returns without saving, applying or closing (question 2). Tests:
   - `test_a_stored_encoder_the_sink_reports_unavailable_is_refused`: stored `hevc_nvenc`
     (reported unavailable in `CAPS`): OK disabled at open, the note names the reason, `accept()`
     writes nothing, the session keeps its settings, one `settings` error;
   - `test_picking_another_encoder_after_the_refusal_accepts`: pick `libx265`, OK enabled,
     `accept()` saves it, and the `settings` error is cleared by the successful save;
   - `test_a_stored_encoder_arriving_unavailable_after_detection_refuses_ok`: the dialog opens
     while the report is pending (OK not refused), the report arrives, OK becomes disabled;
   - `test_auto_is_resolved_by_a_rule_that_disagrees_with_the_interim_rule` (DISAGREEING rule):
     capabilities `(hevc_nvenc available with bit depths (8,), libx265 available with (8, 10))`
     make the interim rule return `hevc_nvenc` (10-bit disabled); the injected rule returns
     `"libx265"`; assert the 10-bit check box is ENABLED, its note empty, and the spy saw
     `("auto", capabilities)`. A second case reverses it: capabilities where the interim rule
     returns `libx265` (10-bit) and the injected rule returns the 8-bit encoder: 10-bit disabled
     with "<name> cannot write 10-bit video.". Keep the existing agreeing test;
   - `_unavailable_stored_scenario` + `..._passes_on_the_real_dialog` +
     `test_planted_stored_unavailable_accepted_is_caught`: the planted dialog restores the base
     behaviour (selection equals stored means acceptable) and must fail the scenario.
   The existing tests `test_a_stored_encoder_this_computer_does_not_report_is_kept` and
   `test_a_failed_detection_gives_a_stored_encoder_the_failure_as_its_reason` must still pass
   unchanged.
4. **Turn 4: DR-55.** The two slots that call an injected chooser, `_on_choose_folder` and
   `_on_clear_clicked` (around `confirm()`), catch `Exception` from the call and present a
   `settings`-owned error through `_present_error` (question 3): "The output folder could not be
   chosen: <error>" and "The cache was not cleared: the confirmation failed: <error>". After a
   failure the dialog state is as before the click: the folder unchanged, `_clearing` False, the
   cache untouched, the button enabled as the analysis phase says. Extend `FakeChoosers` with
   `raise_on_choose`/`raise_on_confirm` (an exception instance or None). Tests:
   - `test_a_raising_folder_chooser_is_a_settings_error` (`OSError`; click through the button so
     pytest-qt would report an escaped slot exception; folder unchanged; the cache not touched);
   - `test_a_raising_confirmation_is_a_settings_error_and_clears_nothing`;
   - `test_a_dialog_still_works_after_a_chooser_failure` (a second click with a chooser that
     answers normally succeeds);
   - `_chooser_scenario` + `..._passes_on_the_real_dialog` + `test_planted_unwrapped_chooser_is_caught`
     (the planted slot calls the chooser bare and must fail the scenario);
   - `test_every_message_of_the_dialog_is_ascii` still holds; add the new messages to it
     (a non-ASCII exception text is escaped).
5. **Turn 5: report and static gates.** Write `docs/reports/wp3.20r-settings-hardening.md` (under
   about 60 lines: what changed per row, the corrected claim, the truth table, the tests per row
   with the base/head result, the reproduction record for DR-53, limits). Replace the ONE bullet
   in `docs/reports/wp3.20-settings.md` (question 4). Run the gates on your head and quote their
   summary lines.
6. **After turn 5 the orchestrator runs Reviewer A** (the Claude pass) on the cumulative diff and
   resumes you with the findings file path. Each review turn: adjudicate EVERY finding (severity
   tag, EXECUTED or REASONED kept from the reviewer, confirm or reject with evidence), fix the
   in-envelope blocking ones, add the ledger row, end with the FILES CHANGED block. Round policy is
   the fill's (Part 1): a round with zero NEW blocking findings terminates; non-blocking findings
   are fixed once in that round; at round 5 STOP for approval.

## Declared operating envelope

Windows 11; Python 3.12; PySide6 6.12.0 and pytest-qt as locked; one Clearwater window; the
settings file in the app-data folder, which may have been edited by hand (an accepted settings file
is in envelope); the sink and cache are the injected ones; the choosers are injected (the shipped
Qt choosers rarely raise); tests headless on `offscreen`. Out of envelope: a settings folder on a
slow share, several windows or processes, other operating systems, a stored value changing under
an open dialog by any route other than the session's `set_settings` (the scenario of turn 2 uses
that route only to force the divergence the register describes).

## Review loop (Reviewer A, the CLAUDE pass), per `docs/review-gate-clearwater.md` Part 1

- The orchestrator runs `scripts/codex_cell.py review` (opus/high, read-only, JSON) on the
  pre-generated diff `git diff -U8 <base>..HEAD` between your turns and hands you the findings
  file. You do not run a reviewer. The ledger and your report are WITHHELD from it.
- **WHAT THE REVIEWER EXAMINES:** the claims of this package: (1) `accept()` validates what it
  applies; (2) the truth table of turn 3 on the running code; (3) no chooser or confirmation
  failure escapes a slot; (4) every new message has owner `"settings"` and is ASCII; (5) the
  tests fail on the base and pass on the head; each planted dialog fails its named scenario;
  (6) nothing outside the owned files changed, `interfaces/` untouched; (7) the corrected claim
  is true on disk and no sentence of the module docstring, the method docstrings or the reports
  contradicts the code.
- Severity is envelope-relative; a finding on code you did not introduce is banked with `git log
  -S` evidence, not fixed here.
- **Gate note (not your task):** the lane head-to-head is owed at this package's gate. The
  orchestrator runs BOTH a Codex B (`gpt-6.1-sol`) and the Claude B on the same finished tree. The
  Claude pass is the B of record; the Codex findings are tabled beside it. Nothing for you to do.

## Notes for the cell

- **How you run.** One `codex exec` process per turn; you cannot message mid-turn and cannot
  commit (`.git` is protected). END EVERY TURN with the return block: the report (under about 70
  lines on the last turn, shorter before), then
  ```
  FILES CHANGED:
  - <path relative to the worktree root>
  COMMIT: <conventional subject carrying wp3.20r>
  ```
  The orchestrator commits exactly those paths with the footer `Co-Authored-By: GPT-6.1 Sol via
  Codex <noreply@openai.com>`. One commit per turn; subjects `test(wp3.20r): ...`, `fix(wp3.20r):
  ...`, `docs(wp3.20r): ...`. A write outside the worktree is swallowed silently: never rely on one.
- **What each turn's final message contains.** Turn 1: the baseline, the three reproductions (what
  you ran, what you saw, inside the worktree), the change table, the sandbox findings. Turns 2-4:
  the rung's tests with their base result (write and run the tests BEFORE the product edit of the
  same turn and record FAILED or PASSED; never `git stash`) and head result, the
  targeted-run summary line, ruff and mypy summary lines. Turn 5: the full return report (the
  module's changed names, the truth table, the corrected claim, the tests, the gates, the
  verification-loop record suspected/confirmed/rejected/fixed, deviations, open items). Review
  turns: the adjudication table and the ledger row.
- **Running tests.** `QT_QPA_PLATFORM=offscreen uv run pytest tests/test_gui_settings_dialog.py
  tests/test_gui_deps.py --basetemp=work/wp3.20r/tmp -q` with output to a file under `work/wp3.20r/`;
  `work/` is gitignored and inside the worktree, so it is writable (the system temp folder is not).
  The dispatcher puts the uncommitted `clearwater.local.toml` in the worktree before turn 1; if a
  test run fails on `LocalConfigError`, that is a STOP. Never point a temp root at the footage
  folder. The FULL suite is NOT yours: it runs only at the orchestrator's gate (about 4,766 tests,
  27 to 45 minutes). Gates you run: `uv run ruff check .`, `uv run ruff format --check .`,
  `uv run mypy`. If a command cannot run in the sandbox, say so verbatim; do not infer a result.
- **Line endings.** Every committed blob is LF. Before ending a turn, check each changed file for
  CR bytes and convert any found to LF.
- **Locks.** The footage folder `C:\Users\rwsmy\clearwater-footage\` is read-only and not used;
  outputs go under `work\`; no dependency; no OS-specific code; user-facing strings ASCII-safe;
  GoPro IMU and GPS data are out of scope (nothing from a `gpmd` track, IMU or GPS is committed,
  and no location tag appears in a committed record).
- **STOP (end the turn with a reproduction) for:** a needed change in any file you do not own
  (including `interfaces/` and `contract.py`); a choice this brief leaves open; the base
  behaviour differing from the facts quoted here in a way that changes a row (question 1 is one);
  a request in a review finding that widens the scope (DR-52, any other setting).
- **Facts quoted from the code (re-ground them, line numbers drift):** `_encoder_unacceptable`
  (`settings_dialog.py:584`) returns False when `name == self._initial.video_encoder` or
  `AUTO` or the catalog is detecting, else True for an unreported or unavailable name;
  `_refresh_ok` (`:606`) enables OK only while `suffix_error` is empty and the encoder is
  acceptable; `accept()` (`:724`) validates `self.suffix_edit.text()`, then calls
  `_encoder_unacceptable()`, then builds `edited_settings()`; `edited_settings()` (`:711`)
  writes only the controls that differ from `self._shown`, on top of `session.settings()`;
  `_on_choose_folder` (`:614`) and `_on_clear_clicked` (`:652`) call `self._choosers`;
  `_present_error` (`:212`) presents an `"error"` `Message` with owner `OWNER_SETTINGS`;
  `_on_catalog_state` (`:525`) re-runs `_refresh_ok`. Probed at drafting with PySide6 6.12.0:
  `QLineEdit(text, parent)` keeps a 32768-character text and a newline; `setText` cuts to
  `maxLength()` (32767).

## Questions for CHARC (recommended answer first)

1. **DR-53's mechanism does not reproduce through the constructor.** The register says a stored
   over-long or newline suffix is "shown truncated/flattened". At drafting, with PySide6 6.12.0
   offscreen, the dialog's `QLineEdit(initial.output_suffix, self)` KEEPS 32768 characters and the
   newline, so the field text already fails `validate_suffix`, OK is disabled at open, and
   `accept()` already returns. Only `setText` (a user edit or paste) truncates, and then the field
   and the applied value agree. Recommended: keep the scope and the remedy as the register reads
   (validate `new.output_suffix` in `accept()`, defence in depth), have the cell record the
   reproduction result in turn 1, write the two register scenarios as tests that may PASS on the
   base (stated as such), and carry the real positive control through the divergence scenario
   (`edited_settings()` reads `session.settings()` at accept time, so the stored value can differ
   from the field). You then amend DR-53's mechanism text at the accept. Alternative: re-rule DR-53
   as BANKED-NOT-REPRODUCED and drop rung 2.
2. **"A settings-owned message" for the DR-54 refusal.** Recommended: BOTH an in-dialog reason
   (`encoder_note`, because the main window's banner is behind the window-modal dialog) and a
   `Message("error", ..., owner="settings")` presented when `accept()` refuses. OK stays disabled
   through `_refresh_ok`; the message covers a programmatic or keyboard `accept()`. Alternative:
   the in-dialog note only.
3. **How broad is the DR-55 catch.** Recommended: `except Exception` around the injected chooser
   call, with a comment that it is foreign injected code (as `_selected_capability` already does).
   Alternative: `OSError` and `RuntimeError` only.
4. **The one bullet in `docs/reports/wp3.20-settings.md`.** Recommended: the cell replaces that
   bullet (supersession by replacement), so the accepted report no longer states the behaviour the
   register calls wrong. Alternative: leave it and rely on the new report's corrected claim.
5. **Message length.** `validate_suffix`'s `ValueError` repeats the whole suffix, up to 32K
   characters. Recommended: the banner text cuts the `ValueError` text to 200 characters (the
   existing `suffix_error` label is unchanged, out of scope). Alternative: no cut.
6. **Reviewer A timing.** Recommended: ONE Reviewer A round after turn 5 on the cumulative diff
   (three small rows, one module), rounds after that as the fill says. Alternative: a pass after
   each rung (three extra Claude passes for a package this size).

## Return report

Your final turn's message, under about 70 lines, then the FILES CHANGED block: the changed names in
`settings_dialog.py`; the DR-53 reproduction result; the DR-54 truth table and the corrected claim;
the DR-55 behaviour; the tests per row with base/head results and the planted dialogs; the gates
(ruff check, ruff format --check, mypy strict, targeted pytest, with summary lines; the full
suite is the orchestrator's); the Reviewer A rounds and verdict (the ledger path); the
verification-loop record; deviations and open items; each lock stated as honored on disk
(owned files only, `interfaces/` untouched, no dependency, LF, footage untouched).
