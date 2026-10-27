# WP3.20R accept record (orchestrator generation 14, 2026-10-27)

**Package:** WP3.20R settings dialog hardening (debt rows DR-53, DR-54, DR-55), brief `docs/briefs/wp3.20r-brief.md`
(FINAL, CHARC `3c3c35d7e40b525e`; DR-54 disposition ruled in `6f725eee` item 2). Lane: **Codex**,
`implementer-codex-sol-high` (gpt-6.1-sol / high, `codex exec` turns driven by `scripts/codex_cell.py`), the Codex half
of the wave 4 CALIBRATION pair (the Sonnet half is WP-T3, accepted `2aca60e`). Both nets are the CLAUDE pass
(`codex_cell.py review`, opus/high, read-only). Report `docs/reports/wp3.20r-settings-hardening.md`; ledger
`docs/proofs/wp3.20r-ledger.md`; the ONE replaced bullet in `docs/reports/wp3.20-settings.md`.

**Candidate:** branch `wp3.20r-mc`, the author branch `wp3.20r` (`32d30dc`, base `528d865`) rebased with
`git -c core.autocrlf=false` onto main `70e316d` (`7749c6e`, reviewed by both Bs), `2fef00f` (`12b5e96`, full pytest)
and `2fea775` (`3d01da3`, this record); 6 commits; `git patch-id --stable` `01c1b13a` on `528d865..wp3.20r` and on
every candidate range. `git diff 7749c6e 12b5e96` and `git diff 12b5e96 3d01da3` over the owned files and
`src tests tools` are empty (main moved by WP-T3 and docs only), so both Bs and the suite ran on this code.

**Footprint (checked at this seat):** `src/clearwater/gui/settings_dialog.py`, `tests/test_gui_settings_dialog.py`,
the report, the one bullet, the ledger. Nothing under `src/clearwater/interfaces/`, `gui/contract.py`,
`pyproject.toml`, `uv.lock`. Every changed blob has 0 CR bytes. Each turn was committed at this seat from the turn's
FILES CHANGED block with the `GPT-6.1 Sol via Codex` footer; `ruff format --check` run at this seat (the sandbox's
exit 101 is an artifact).

## Nets

| Net | Result |
|---|---|
| Reviewer A (Claude pass, opus/high, `wp3.20r\r1\`) | R1 `NO_NEW_CRITICAL_MAJOR`: 0/0/3 minor + 3 advisory, all in envelope, all new; turn 6: minors 1, 3 fixed, 2 the authorised one-line fix, advisory 5 fixed, 4 declined (cosmetic), 6 banked (origin `54e2749`). R1 terminates. $2.03, 308 s, 33 turns. md5s in `r1\md5sums.txt` |
| Candidate full pytest (this seat, `12b5e96`, offscreen, FULL tier: shared GUI module) | 4894 passed, 2 skipped (the two standing skips: `test_color_roundtrip.py:121`, `test_photo_check.py:139`), 2785.94 s, EXIT=0 (08:58Z-09:44Z) |
| Static (this seat, `7749c6e`) | ruff clean; format 227; mypy 132 clean |
| Harness gate (this seat, `3d01da3`) | 379 OK (skipped 1) |
| **Reviewer B of record** (Claude pass, `codex_cell.py review --base 70e316d`, opus/high, `wp3.20r\reviewB\`) | `VERDICT: NO_NEW_CRITICAL_MAJOR`; model `claude-opus-5-5`; 26 turns; 5 permission denials (its own retries of a pytest form; worktree clean after); $1.86, 324 s. All six claims CONFIRMED by execution, including the new tests run against the base `src` (19 failed, 68 passed, 8 errors) and planted dialogs. 5 advisories. Prompt built from the brief, not from A's. md5s `reviewB\md5sums.txt` (`review.txt` `7ee14270152e594663a0de32828061b8`) |
| Codex B (head-to-head, `codex exec -m gpt-6.1-sol -c model_reasoning_effort=high -s read-only`, `wp3.20r\reviewB-codex\`) | `VERDICT: NO_NEW_CRITICAL_MAJOR`; banner gpt-6.1-sol / high / read-only; 0 `^ERROR`; 18 "succeeded in"; tokens 94,197; no withheld path read. 2 minor + 1 advisory. It could NOT run Qt (no `uv` in WSL): method-level probes via AST and doubles. md5s `reviewB-codex\md5sums.txt` |

## The lane head-to-head (same tree, same contract, prompts differing only in the git note)

| Item | Claude B (of record) | Codex B |
|---|---|---|
| Verdict | NO_NEW_CRITICAL_MAJOR | NO_NEW_CRITICAL_MAJOR |
| Execution | real Qt suite on head (91 passed) and on base; scratch probes on the shipped fixtures | AST-extracted method bodies with doubles; no Qt |
| Claim 3 (no chooser exception escapes) | CONFIRMED in envelope; an exception whose `__str__` raises escapes: ADVISORY, out of envelope | REFUTED: the same `__str__` case, MINOR, in envelope (injected choosers are unrestricted) |
| Claim 5 (new tests fail on the base) | CONFIRMED with the stated exceptions (9 pass on base by design, listed) | REFUTED "as universally stated" (the same base-passing controls), ADVISORY |
| Session-correction recovery | ADVISORY: retyping after the divergence re-enables OK, accept refuses again (out of envelope) | MINOR: correcting the session by `set_settings` leaves OK disabled (in envelope) |
| Unique to one side | duplicate banners on repeated direct `accept()`; empty exception text gives "...chosen: "; stale "Accept sequence" line in `wp3.20-settings.md` | none |
| Cost | $1.86, 324 s | 94,197 tokens |

Both found the same two real edges; the Codex pass rated both one step higher and in envelope. Neither is blocking.

**Adjudication at the gate:** no blocking finding. BANKED as one MINOR row (CHARC): (i) an injected chooser exception
whose `__str__` raises escapes the slot (format the detail with a fallback); (ii) after a refused applied suffix,
correcting the session leaves OK disabled until the field changes; (iii) the duplicate-banner and empty-detail
advisories (A's advisory 6 is the same family, origin `54e2749`). Trigger: the next settings-dialog touch (WP4.3).
The stale "Accept sequence" line in `docs/reports/wp3.20-settings.md` is outside the one bullet the brief granted;
the new report states the order; left as is.

**Debt:** DR-53, DR-54, DR-55 CLOSED by this package (register rows by CHARC at QA); the MINOR row above owed.

## Calibration figures (HD-1, the Codex half)

- Six cell turns. `tokens used` footers: 64,199 / 92,340 / 111,584 / 131,507 / 149,041 / 204,598. The session file's
  last request at the end: 202,061 input tokens (window 475,000).
- **Depth reading (found at WP-T4 turn 4, this generation):** the footer is NOT the context depth in general. WP-T4's
  turn-4 footer read 536,544 while its session's last request carried 284,234 input tokens. Read Codex depth from
  `last_token_usage.input_tokens` in `~/.codex/sessions/.../rollout-*-<session>.jsonl`.
- Tests: 44 -> 64 functions in the module test file (20 new, 1 changed, 3 planted controls); 64 -> 91 targeted cases.
- Claude review cost: A R1 $2.03, B $1.86.

## Main gates

Main after the ff merge = `3d01da3` + this record (docs only): the candidate's full pytest stands as main's figure by
code identity; harness gate re-run on main below.
