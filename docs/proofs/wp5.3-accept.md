# WP5.3 accept record (orchestrator generation 33, 2026-11-02)

**Package:** WP5.3, the CP5 visual review pack: the committed, re-runnable instrument `tools/reviewpack/` (selects the CP5 test set by name, drives every item through `tools/headless_export.py` at the shipped defaults, writes pairs, thumbnails, side-by-side clips, `index.html`, the review sheet and the D65 tally, shows both starter presets as exported) and its real build at the orchestrator's seat.
- **Brief:** `docs/briefs/wp5.3-brief.md` (FINAL; round-0 ruling `f99fca74` and the Reviewer A round 1-4 rulings folded on the branch).
- **Lane: CODEX**, `implementer-codex-sol-high`, seven sessions, twenty turns (session 7 `01a19ace-0e2d-7fd1-b019-5d505692919b` at 106,986 after turn 20). Both nets Claude (`claude -p --model opus --effort high`), the other model.
- **Report:** `docs/reports/wp5.3-review-pack.md`. **Ledger:** `docs/proofs/wp5.3-ledger.md`. **Evidence:** `C:\Users\rwsmy\clearwater-review-evidence\wp5.3\` (`cell`, `r1`-`r4`, `B`, the rulings).

**Candidate:** branch `wp5.3`, rebased onto main `ef64c7b8`'s successors and gated as **`b6521664`**, then rebased with this record onto the current main (main's later commits touch only CHARC's and the orchestrator's state files and the kernel docs; no file this package owns or reads). `git patch-id --stable`: the 25 package commits carry the same 25 patch ids before the rebase (tag `wp5.3-pre-rebase-g33`, `1ca46689`) and on `b6521664`.

**Footprint** (`git log --name-only main..wp5.3`, 9 paths plus this record): NEW `tools/reviewpack/__init__.py`, `select.py`, `build.py`, `page.py`, `sheet.py`; `tests/test_reviewpack.py`; `docs/reports/wp5.3-review-pack.md`, `docs/proofs/wp5.3-ledger.md`; `docs/briefs/wp5.3-brief.md` (ruling folds). No `src/` file, no frozen interface, no existing test, no dependency, no fixture. Every changed blob has 0 CR bytes.

## Nets

| Net | Result |
|---|---|
| Round 0 (turn 1) | 3 MAJOR + 1 MINOR mapping disputes; R0-1..R0-3 granted (CHARC `f99fca74`), R0-4 resolved. |
| Reviewer A rounds 1-3 | NEW_CRITICAL_MAJOR_FOUND each (A1 0/3/3, A2 0/1/4, A3 0/1/3, critical/major/minor); each adjudicated, ruled by CHARC and remediated in instrument code and tests only. |
| Reviewer A round 4 | **NO_NEW_CRITICAL_MAJOR**, CONVERGED (CHARC `e4d56665`); 0/0/4 and 6 advisory; terminating clean-up turn 10. |
| **Reviewer B** (Claude pass at the orchestrator's seat; `...\wp5.3\B\`) | **NO_NEW_CRITICAL_MAJOR**, 27 turns, `is_error` false; findings remediated in turns 11-12 (sheet conflicts named on the page with both outputs; no numbered output ever deleted); B-F4 (two nodes near the 5 s parallel line) MEASURE ONLY, see the gate. |

## The real build (RUN REQUESTS at the orchestrator's seat; informal receipts, not figures of record)

Receipts `work/orch-g32/wp53-runs/` (photos, presets, first page, V-P, the lost V-S attempt) and `work/orch-g33/wp53-runs/` (V-S re-run, V-D, V-Z, V-R, page, page --check, tally); every piece read back by a Codex turn (14-19). Pack: **128 items = 117 done (P-A 64, P-Z 9, V-S 26, V-D 8, V-Z 2, V-P 8), 9 V-P FAILED with the product's own text (DR-112, OPEN), 2 V-R expected HLG refusals, pending 0**; 603 published targets resolve; privacy lock held. `page` EXIT 1 (failures recorded), `page --check` EXIT 0, tally EXIT 0 (headline expected 115 / available 106 / missing 9 / unjudged 106).
- The first `clips V-S` attempt died with orchestrator generation 32's pane (~00:36:53Z, no exit line; the group's records are written only when the group returns, so it recorded nothing). Its 33 orphan files were MOVED to `work/orch-g33/vs-orphans/` (pruned only on the owner's word) and V-S re-ran clean (EXIT 0, 8,740 s). Owner rule from it: no generation rolls over while a job it started runs (kernel `215b1fd6`). The report carries "a killed group run leaves its finished outputs unrecorded" as a Limit.

## Gate

The ONE two-leg gate the brief asks (no fullclip leg: the package adds no fullclip node), WITH WP-T7's flags and redirects (`work/orch-g33/gate.sh`), on `b6521664`, run id `w53`, Git Bash, `PYTEST_ADDOPTS` unset, `QT_QPA_PLATFORM=offscreen`; no EXCLUSIVE window open, no WP5.3 build piece and no Claude reviewer pass running during either leg; C: 154 GB free at the start, 93 GB at the end (below); logs `work/orch-g33/gate-w53/`; junits `work/g33-w53-parallel.xml`, `work/g33-w53-serial.xml` in the worktree.
- **Static:** `ruff check` passed; `ruff format --check` 306 files already formatted; `mypy` no issues in 154 source files; 0 CR in every changed blob.
- **Collection:** all **7,720** = parallel 6,447 + serial 1,266 + fullclip 7; no duplicates; union identical to collect-all.
- **PARALLEL** (`-n 4 --timeout 600`, stall-watched): **6,446 passed, 1 skipped**, EXIT 0, 699 s (05:58Z-06:11Z). The skip is the standing swscale refusal (`test_color_roundtrip.py:123`). Log md5 `9c1ecfe2fa7661a68a4b06d9d681ea83`. The package's 176 parallel nodes sum to 73.8 s.
- **SERIAL** (`--timeout 1200`, ALONE on the host, stall-watched; no stall reported): **1,255 passed, 11 skipped, 0 failed**, EXIT 0, 2,752 s (to 06:56Z). The 11 skips are the standing look-check frames archived to D: (as at WP5.1's `g32-w51`). The DR-99 node passed. No timeout fired. Log md5 `b82686a09aad8ec5a19b8c45db7f0b5e`. The package's one serial node (`test_all_tiny_set`) took 31.3 s. **The leg ran +713 s over WP5.1's 2,039 s**, with no Claude pass or build piece beside it; the package's own serial time is 31 s of it, so the rest is host load or disk (CHARC `d4224524`: if WP-D112's serial leg comes in near 2,000 s it was load; if it repeats, a DR row at the Phase 5 gate report).
- **Harness gate:** 382 tests OK (1 skipped), 47 s.
- **B-F4, measured:** under `-n 4`, `test_missing_starter_presets_are_pending_until_both_tables_exist[0]` 5.751 s and `[1]` 5.626 s, over the brief's "a parallel node over 5 s is slow" sizing line (103 parallel nodes on the suite sit over 5 s today; neither node asserts a wall clock). **NAMED TEST-ONLY ITEM (CHARC `d4224524`):** `@pytest.mark.slow(reason="5.6-5.75 s under -n 4 at WP5.3 gate w53 (B-F4)")` on both parametrisations in the post-witness read-back turn (the `clips V-P` re-run read-back after WP-D112 merges), covered by WP5.2's gate.
- **Disk:** C: free fell 154 -> 93 GB during the gate while the gate's basetemps hold about 1.9 GB; the source is being traced before any window opens (CHARC `d4224524`).

## Dispositions (CHARC's at this accept)

- AD-13 NOTE (both starter presets value-identical in v1).
- The pack's 9 V-P rows stay OPEN until WP-D112's accept and the `clips V-P` re-run witness; CP5 goes to the owner only at pending 0 AND failed 0 (then `page`, `page --check`, tally).

## Merge

`main` fast-forwarded to the rebased package plus this record's commit, by the orchestrator. The worktree `.worktrees/wp5.3` is KEPT LIVE: the V-P re-run and its read-back (with the B-F4 marker) run from it after WP-D112 merges.
