# WP5.7 accept record (orchestrator generations 36-39, 2026-11-03)

**Package:** WP5.7, the halo investigation (DR-117): reproduce the six CP5 halo observations at the shipped defaults, localise the stage of spec 6.2 that produces them, measure the candidate changes on the six, and measure the chosen candidate over the 120 other CP5 items, with V3 and N6 for it.
- **Brief:** `docs/briefs/wp5.7-brief.md` (FINAL by CHARC on the fill `d7be07f6`). CHARC rulings carried by the ledger: the Part 2 scope ruling (candidates (e1)-(e3)); S1-S3 (step 2A); Q-d; C1-C6 (`f4ac346b1f9ce86b`); Q1 / Q2 (`fd7ad2b4858c8f04`); the C4 STOP ruling (`4c60bacc3de85d88`: the binding cost figure is N6 itself; no adopt-now); the texture-observation addendum (`61fa577714607f97`); the pts pre-ruling (`a366bb37423838ae`).
- **Lane: CLAUDE**, `implementer-opus-high`, nine cells (`wp57-cell1` .. `wp57-cell9`; depths with their moments in the ledger; the last three: cell7 221,426 at its Part 3 yield, cell8 331,770 at its round-5 final yield, cell9 170,131 at its round-7 yield). Both nets Codex (`gpt-6.1-sol` / high), the other model.
- **Report:** `docs/reports/wp5.7-halo-investigation.md`. **Ledger:** `docs/proofs/wp5.7-ledger.md`. **Evidence:** `C:\Users\rwsmy\clearwater-review-evidence\wp5.7\` (`cell\` dispatches 1-12; `A\r0`..`A\r8`; `B\`, `B\r2\`; `part3\`, `v3\`; `records\` (part1s, part2, part3, part3r: 898 files); `cell-scratch\`; `gate\`).

**Candidate:** branch `wp5.7` at `5eb92a51` (the last package commit), with main `c1ca6a71` merged in `--no-ff` as **`d4644511`** (gated) so every commit hash the report and ledger cite stays reachable (no rebase); then main `31c376e7` merged the same way as ``29af157f`` (docs-only commits between: `docs/charc-state.md`, `docs/debt-register.md`; the harness gate re-run on it). Instrument blobs at the candidate: `tools/halo_probe.py` `82fc3ca3bf41a71e0b53f57177ad2c87e78fb53d`, `tools/halo_part3.py` `3ca68535a6bf9b29415b89c91f2b57a3f6ff389e`. **Merge is FAST-FORWARD.**

**Footprint** (`git diff --name-only main...wp5.7`, 6 paths plus this record): NEW `tools/halo_probe.py` (Parts 1-2: the stage-by-stage probe, instrument-only candidate switches, edge-band statistics with the noise rule, staged publication), NEW `tools/halo_part3.py` (Part 3: V3 via WP4.2's legs, the N6 row on `tools/export_bench.py`, the whole-set batch, the scan, the sheet), NEW `tests/test_tools_halo_probe.py`, NEW `tests/test_tools_halo_part3.py`, the report, the ledger. **Outcome A-prime: no path under `src/`; no default changed; no dependency.** Every changed blob 0 CR, ASCII.

## Result (the report; nothing decided by the package)

- **Cause:** all six halos reproduce at the shipped defaults and first exceed 10 % of the edge contrast at INPUT 2: the whole-frame N{} stretch saturates the sharpened high-pass near strong edges on these low-range frames, and the Laplacian weight favours input 2 there. Shallow-pyramid hypothesis REJECTED. No product divergence from spec 6.2 / 6.6 (outcome B not found).
- **Candidates on the six** (three-way band / none / undecided splits over the decided lines; confirmed by Reviewer A r5): only (d) (input 2's overshoot clipped to the local range of the unsharpened reference, 1 sigma) brings the decided lines to `none` in number (photos 0/2/1, video 1/21/9); the parameter candidates scale the band with strength.
- **(d) on the 120 other items** (`part3r`, the re-render of record): scanned band sides video 963 -> 39, photo 248 -> 13; no item's scan rises by the sheet's rule (one side rises: IMG_6800 side 5, 0.11 -> 0.56 x C); clipped fraction 0 under (d); whole-frame std L* falls on 219 of 220 images; CHARC's sighting of texture softening (items 01 IMG_6762, 06 IMG_6751) stated as an observation with the measured columns; the contact sheet's 20 in `part3r\wholeset\sheet-20261103T213732053153Z\`.
- **V3:** (d) passes every asserted bound on WP4.2's two clips; the shipped leg reproduced the record; the ad14 contrast ratio rises (c3 0.072 -> 0.316), disclosed.
- **N6:** shipped 10.9467, (d) 12.4346 min/min (+13.59 %): (d) as measured is OVER N6 (about 12); the budget for any implementation is about +9.6 %.
- **Outcome A-prime:** nothing for v1.0.x; (d) stated as an amendment of spec 6.2 step 3 with a cache-version bump; the owner's two options as CHARC framed them (DEFER to Phase 6 with DR-117 open and an optimisation item, or OPTIMISE NOW as a Phase 6-class package); no adopt-now option.

## Nets

| Net | Result |
|---|---|
| Reviewer A r0-r4 (Codex, at the orchestrator's seat) | Parts 1-2: r0 9 findings fixed; r1-r3 staged publish, cache isolation, rollback; r4 NEW_CRITICAL_MAJOR (the flicker column was not V3; undecided counted as removal) remediated at step 3R (conclusions and tests only). |
| Reviewer A r5 (`A\r5\`) | Part 3 + report: **NEW_CRITICAL_MAJOR_FOUND**: MAJOR whole-set stills matched against relative time while CP5 stores absolute (GX011590 / GX011603 / GX011609, nine stills one frame late); MAJOR the sheet loaded staging records; four MINORs, one ADVISORY. All FIX (dispatch-11, `wp57-cell8`); the three items re-rendered at the seat into `part3r\` (117 copied byte-identical); CHARC's pts pre-ruling (Parts 1-2 frames of record stand, recorded by absolute pts). FIVE_ROUND_GATE: continue (instrument figures changed). |
| Reviewer A r6 (`A\r6\`) | **NO_NEW_CRITICAL_MAJOR = CONVERGED**: all 150 stills on CP5's times; 539 copied files SHA-256 identical; every claimed movement; one MINOR fixed at the seat (`faf592de`). |
| **Reviewer B** (the orchestrator's Codex pass, WSL, on `faf592de`; `B\`; five assertions PASS) | **NEW_CRITICAL_MAJOR_FOUND**: B1 MAJOR (introduced) N6 summary accepted invalid populations; B2 / B3 MINOR, B5 ADVISORY; B4 MINOR the shared `sample` fixture writes outside `--basetemp` (pre-existing: DR-120). **The single remediation** (dispatch-12, `wp57-cell9`): B1, B2, B3, B5 fixed; the delivered N6 summary unchanged. |
| Reviewer A r7 / r8 on the fix (`A\r7\`, `A\r8\`) | r7: MAJOR duplicate `started` stamps passed; MINOR a two-run guard test; both fixed. r8: **NO_NEW_CRITICAL_MAJOR**. |
| **Reviewer B re-run** (`B\r2\`, on `5eb92a51`; five assertions PASS: banner gpt-6.1-sol / high, `^ERROR` 0, footer 1, 23 succeeded, 0 NUL; md5s in `B\r2\md5sums.txt`, transcript `review-B.txt` md5 `2852c31dc38d932c59ded0b98daf8f9a`) | **NEW_CRITICAL_MAJOR_FOUND**: confirmed B1-B5; its MAJOR is `tools/export_bench.py:99`'s stale `D106_MIN_PER_MIN = 25.0` label = **DR-119 (a)**, pre-existing in a file the package does not own, no figure affected. **Adjudicated at the gate seat by irreversibility** (no third remediation), CHARC concurring (`21f92b6c81d8c978`): BANKED; minor 3 (the bench's torn JSON write) = DR-119 (c); minors 2 / 4 and advisory 5 (stage V3's output, refuse the cache / out overlap, the `build_sheet` docstring) = DR-119 (d). |

**Seat incidents (recorded in the ledger):** (1) `wp57-cell8` processed a relayed amendment after its yield and rewrote `run-part3r.sh` one minute into the seat's GPU piece; the seat killed the bash wrappers, let GX011590's render finish and ran the other two by hand with the original command (`records\part3r\logs\part3r_finish.sh`); the affected set re-derived from the records afterwards was the same. (2) The Part 3 photo batch's list pipe carried CRLF (seat fix `tr -d '\r'`; DR-119 (b)).

## Gate

The TWO-leg gate (GATE_CHECKS for outcome A: no `src/` path; `tests/test_tools_halo_probe.py` and `tests/test_tools_halo_part3.py` in the parallel junit; no fullclip), WP-T7's flags (`work/orch-g39/gate.sh`), run id `p57`, on **`d4644511`**, Git Bash, `PYTEST_ADDOPTS` unset, `QT_QPA_PLATFORM=offscreen`; stall watch armed; nothing heavy beside the serial leg. Summary `work/orch-g39/gate-p57/summary.txt` (copy in `...\wp5.7\gate\`).
- **Static:** `ruff check` exit 0; `ruff format --check` 316 files already formatted; `mypy` no issues in 158 source files.
- **Collection:** all **8,062** = parallel 6,782 + serial 1,273 + fullclip 7; no duplicates; union identical to collect-all.
- **PARALLEL:** **6,781 passed, 1 skipped, 0 failed**, EXIT 0, 542 s (the standing swscale refusal, `tests/test_color_roundtrip.py:123`). In the junit: `test_tools_halo_probe` 94 and `test_tools_halo_part3` 52, all green (the part3 module's one `slow` test runs in the serial leg). Log md5 `0d493a68b881325bcebb48c538491ba8`.
- **SERIAL:** **1,262 passed, 11 skipped, 0 failed**, EXIT 0, 1,995 s (the 11 standing look-check frames archived to D:). `test_tools_halo_part3`'s slow test green. Log md5 `c95e58c8d35e9412b3b8d5d822dfcd9e`.
- **Harness gate:** 382 tests OK (1 skipped) on `d4644511`; re-run on `29af157f` after the second docs-only merge: 382 OK (1 skipped), exit 0 (`work/orch-g39/gate-p57/harness-29af157f.txt`).
- C: 47 GB free at the start (22:29:34Z), 42 GB at the end (23:12:53Z). Junits, the summary and the log md5s copied to `...\wp5.7\gate\`.

## Dispositions (for CHARC at this accept)

- **DR-117** -- cause localised (input 2's N{} saturation), the proposal (candidate (d) as a spec 6.2 step 3 amendment, over N6 as measured), the whole-set effect; OPEN with the owner's decision pending (DEFER or OPTIMISE NOW).
- **DR-119 (a)-(d)** banked (tools labels and hardening; (a)-(b) WP5.5 if its fill admits, else Phase 6; (c)-(d) Phase 6). **DR-120** banked (Phase 6, WP-T class).
- Report Limits carried: the owner's eye is the only artifact oracle; the band metric is the instrument's; display and viewer differences; GX011627's last second cannot carry V3; the whole-frame diagnostic is not V3; the timed clip is unoptimised; the CRLF seat fix; the stale bench label; the write-path limits out of envelope; DR-120.

## Merge

`main` fast-forwarded to the merged package plus this record's commit, by the orchestrator. The worktree `.worktrees/wp5.7` is kept until the owner's word; `work\wp5.7\` (part1s, part2 7.6 GB, part3, part3r) likewise (durable copies of every record are in the evidence folder).
