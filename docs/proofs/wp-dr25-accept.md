# WP-DR25 accept record (orchestrator generation 38, 2026-11-03)

**Package:** WP-DR25, the DR-25 (3) re-measurement: the WP1.4 statistics instrument's `--long` path (20 s excerpts of GX011627 and GX011625, BOTH methods' smoothing-window study, staged interiors trimmed by each method's `staged_reach`) and the completion report on whether 2 s smoothing leaves less flicker than 1 s on the edge-free staged interior (AD-3's shipped default rests on c3).
- **Brief:** `docs/briefs/wp-dr25-brief.md` (FINAL by CHARC; round-0 rulings (a)-(d) at main `0f2d19c4`). CHARC ruling R1 (2026-11-03 09:52Z, msg e09d10970e1fcdfd): under `--long` only, a crossing `linear_trend` fit is recorded UNAVAILABLE with its crossing frames.
- **Lane: CODEX**, `implementer-codex-sol-high`, three sessions, eight turns (session 1 `01a1a02e-1dd5-72d0-8828-a473226c107c` turns 1-3, retired at 211,019 of 475,000; session 2 `01a1a0cb-94f7-71d2-a4c3-34ad022b488a` turns 4-5, 174,724 of 258,400 at turn 5; session 3 `01a1a157-6f2b-7391-9242-5fa191ebfca1` turns 6-8, **185,072 of 258,400** after turn 8). Both nets Claude (`claude -p --model opus --effort high`), the other model.
- **Report:** `docs/reports/wp-dr25-staged-run.md`. **Ledger:** `docs/proofs/wp-dr25-ledger.md`. **Evidence:** `C:\Users\rwsmy\clearwater-review-evidence\wp-dr25\` (`cell`, `A\r1`, `A\r2`, `B`, `B\r2`, `gate`, the first (failed) analyse's records `runs\`, the records of record `runs2\`).

**Candidate:** branch `wp-dr25`, rebased onto main `6393cb35` and gated as **`82b6eae2`**; then rebased onto main `ab5f59e0` (docs-only commits between: `docs/charc-state.md`, `docs/orchestrator-state.md`) as `4b96c1b6`, `git patch-id --stable` over the 7 package commits equal before and after (`work/orch-g38/dr25-patchid-gate.txt`, `-rebased.txt`). Final instrument blob `f7a4988f300006c878c4636e022a5336c83960c2`; the second analyse ran on blob `e346ca303cadf719c6b1f30eb9aaeaa80dcdbe61` (pre-rebase `68caf100`), which differs from the final blob by one docstring line only (report section 9). This record's commit adds this file only (docs). **Merge is FAST-FORWARD** (Reviewer B re-run F2: the test module loads the pre-R1 instrument by blob `5bada347...`, reachable only through this branch's history).

**Footprint** (`git diff --name-only main...wp-dr25`, 4 paths plus this record): `tools/statistics_experiments.py` (the `--long` path: both methods, staged-reach interiors, per-step arrays, the start clamp `min(fraction x duration, duration - 20)`, the duration source, R1's unavailable trend row; the DEFAULT path unchanged and pinned whole by golden tests against the base module, blob `74019b47...`); `tests/test_tools_statistics_experiments.py` (new, 27 tests, parallel leg); the report; the ledger. `tools/prototype/`, `src/` untouched; no dependency. Every changed blob 0 CR, ASCII.

## The runs (at the orchestrator's seat, alone on the GPU)

- `extract --long`: exit 0, 08:42:48Z-08:56:01Z (791 s); free C: 82 -> 72 GB; 7.1 GB kept under `work\wp-dr25\`.
- `analyse --long` (first, on pre-rebase `45bca4db`): exit 2 at 09:42:25Z, GX011625-long's `linear_trend` fit crossed (the prototype's `check_statistics` refused it); diagnosed in turn 4, ruled R1, fixed in turn 5.
- `analyse --long` (second, on pre-rebase `68caf100`): **exit 0**, 10:49:48Z-12:14:08Z (5,056 s); free C: 59 -> 64 GB. Records of record copied to `...\wp-dr25\runs2\`.

## Result (the report; nothing decided by the package)

2 s `median_gaussian` leaves less staged flicker than 1 s on each candidate's own edge-free interior, for both methods on both excerpts: **c3 23.24 % (GX011627) / 10.23 % (GX011625); ancuti2018 13.52 % / 8.07 %.** On the common 2 s interior: c3 24.62 % / 14.54 %, ancuti2018 15.03 % / 16.16 %. WP1.4's "about a fifth" was an Ancuti-only claim. GX011625-long's `linear_trend` row is UNAVAILABLE for both methods (57 crossing frames, indices 542..598; CHARC's wording in Limits). The orchestrator re-derived the four per cents and the common-slice control from `runs2\` independently.

## Nets

| Net | Result |
|---|---|
| Round 0 (turn 1) | a STOP on the scope (one method, the margin, the start): CHARC ruled (a)-(d) (`0f2d19c4`). |
| Turn 2 | the `--long` path and tests. |
| Reviewer A round 1 (Claude, `...\A\r1\`) | **NO_NEW_CRITICAL_MAJOR**: F1 MINOR (the `_signals` stub could not tell method / series: M5, M6, M8 survived) + advisories; fixed in turn 3 (F1, F2, F5, F6, F7); F3 / F4 / F8 report and seat obligations. |
| Reviewer A round 2 (Claude, `...\A\r2\`) | **NO_NEW_CRITICAL_MAJOR = CONVERGED**: all seven claims held by execution (default path identical to the base module; interiors reproduce in 48 of 48 records; 18 of 20 mutants killed); F1 MINOR (default-path tests checked absent keys only: Mj / Mk survived) fixed in turn 5 by golden comparisons; F3 fixed; F2 / F4 report obligations. |
| Turns 4-5 | the first analyse's failure diagnosed (the prototype's `check_statistics`, not product fusion); CHARC R1; R1 implemented (`--long` only, detected before the trend render; RED 2 / GREEN 22). |
| Turn 6 | the report from `runs2\` (a FRESH session). |
| **Reviewer B** (Claude pass at the orchestrator's seat, EXECUTING, on pre-rebase `83ad9d69`; `...\B\`, 48 turns, `is_error` false, worktree clean after) | **NEW_CRITICAL_MAJOR_FOUND.** Every report figure reproduced from `runs2\` with no mismatch (sections 2-8). **F1 MAJOR, introduced by the package (by the orchestrator's rebase):** a test loaded the pre-R1 instrument from commit `6dfccdfc`, unreachable from any ref after the rebase (a fresh clone or `git gc` would ERROR three tests); F2 MINOR the report cited unreachable pre-rebase hashes; F3-F7 advisories (Ancuti-only wording, a tie mutant, an unguarded `streams[0]` out of envelope, golden coverage, a docstring). **The single remediation** (turn 7): revision-loaded modules pinned by BLOB id with a missing-blob guard; the report names each run's instrument by blob id; the wording; a tie test (M8 now killed); the docstring; F5 a Limits line; F6 a ledger line. |
| **Reviewer B re-run** (`...\B\r2\`, on pre-rebase `d5650ea8`, 42 turns, `is_error` false, worktree clean after) | **NO_NEW_CRITICAL_MAJOR.** All seven earlier findings closed; every figure re-verified; 14 of 14 new mutants fail the module. F1 MINOR (report section 9 stale after turn 7) fixed in turn 8 (section 9 only); F2 advisory (fast-forward merge, honoured); F3 advisory (the crossing check runs after the method's other renders and before the trend render, as ruled; records identical across the two runs). |

## Gate

The TWO-leg gate (GATE_CHECKS: the importers `tests/test_footage_locator.py` and `tests/test_prototype_temporal.py` green by name; no fullclip-marked test added), WP-T7's flags (`work/orch-g38/gate.sh`), run id `pdr25`, on **`82b6eae2`**, Git Bash, `PYTEST_ADDOPTS` unset, `QT_QPA_PLATFORM=offscreen`; stall watch armed; nothing heavy beside the serial leg. Summary `work/orch-g38/gate-pdr25/summary.txt` (copy in `...\wp-dr25\gate\`).
- **Static:** `ruff check` exit 0; `ruff format --check` 312 files already formatted; `mypy` no issues in 156 source files.
- **Collection:** all **7,915** = parallel 6,636 + serial 1,272 + fullclip 7; no duplicates; union identical to collect-all.
- **PARALLEL** (13:41Z): **6,635 passed, 1 skipped, 0 failed**, EXIT 0, 525 s (the standing swscale refusal). In the junit: `test_tools_statistics_experiments` 27, `test_footage_locator` 30, `test_prototype_temporal` 55, all green. Log md5 `33f8fc55a8bd6f2d7c58397be2445807`.
- **SERIAL** (13:50Z): **1,261 passed, 11 skipped, 0 failed**, EXIT 0, 2,007 s (the 11 standing look-check frames archived to D:). `test_prototype_temporal` 4 serial cases green. Log md5 `05d41d11b93ec5415691b2bfa11c8b17`.
- **Harness gate:** 382 tests OK (1 skipped).
- C: 57 GB free at the end (14:24:04Z). Junits copied to `...\wp-dr25\gate\`.

## Dispositions (for CHARC at this accept)

- **DR-25 (3)** -- the evidence is in; CHARC rules (CLOSED, or with a note).
- **AD-3** (2.0 s smoothing default) -- CHARC rules CONFIRMED or a note: on the shipped method c3, 2 s beats 1 s on the edge-free staged interior on both chapters (23.24 % / 10.23 %; 24.62 % / 14.54 % on the common interior).
- **WP1.4 erratum pointer** -- WP1.4's ground-2 figures were Ancuti-only and boundary-influenced at 6 s; the report's section 6 gives the re-trims.
- Report Limits carried: under-20 s chapters out of envelope; GX011625-long's unavailable trend row (CHARC's wording); the 20 s vs 6 s reference; `_duration_source`'s unguarded `streams[0]` (out of envelope).

## Merge

`main` fast-forwarded to the rebased package plus this record's commit, by the orchestrator. The worktree `.worktrees/wp-dr25` is kept until the owner's word (its `work/` holds gate basetemps); the 7.1 GB of excerpts under `C:\Users\rwsmy\clearwater\work\wp-dr25\` likewise.
