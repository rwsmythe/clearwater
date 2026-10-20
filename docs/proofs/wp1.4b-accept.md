# WP1.4b — Accept record (gain-cap noise test, deep-frame statistics, default flip to c3)

**Accepted 2026-10-20 by the orchestrator** (generation 2, session
`clearwater-orchestrator-20261018-1442`). Gate per `docs/review-gate-clearwater.md` Part 2. Tier
STRONG. Commission: CHARC `0fd7c88ad56a7083` (WP1.4b), `cb61a4e41f625d73` (go-ahead); the flip's
pin rule approved by CHARC `1cc08da6b265e2a6` with two guards; claim 2a from CHARC
`01500d3574412e69`; claim 10b from the deep CP2 (CHARC `1b7bc20ed511cdab`).

| Item | Value |
|---|---|
| Brief | `docs/briefs/wp1.4b-brief.md` (FINAL `c80725b`; guards `d68039b`; claim 2a `f183a11`; claim 10b `42662d2`). Spec v0.5.3. |
| Base SHA | `db751cb` |
| Author heads | Return `8b194e4`; after the authorised text edits `d0348ed`; final `8314247` (a ledger-only note). Each read twice across a turn boundary, unchanged and clean. |
| Cells and depth | `wp14b-cell` (implementer-opus-high): 32,865 at dispatch (05:57Z); 68,199 (06:14Z); 235,202 / 94 turns at its STOP, then 237,015 (06:44Z). Re-seated by evaluation (the grid, claims 7-10b, the report and the whole review loop remained). Stood down at 06:50Z after a collision (see Process deviations). `wp14b-cell2` (implementer-opus-high): 40,786 at dispatch (06:45Z); 318,197 / 139 turns, then 320,059 at the round-2 yield (08:21Z), continued by evaluation for one bounded round; 360,500 / 166 turns at return (08:43Z); 387,919 / 193 turns final (09:02Z), under the ~400K stop. Retired. |
| Merged head | `afaff0e` (`wp1.4b-mc` = `8314247` rebased onto main `9b6093f`; main fast-forwarded). |
| Byte identity | `git patch-id --stable` = `04bc9d18bfc668b02214b459eadef60ddf696770` on `db751cb..8314247`, on the B candidate `9b6093f..afaff0e`, and on main `9b6093f..afaff0e`. CHARC held main from B to the merge. |
| Reviewer A | STRONG (gpt-5.6-sol / high), WSL, codex-cli 0.162.1. R1 0/2/3 (all NEW; the flip had missed 3 temporal-test sites silently running c3 under an Ancuti label, now pinned with a registry guard); R2a VOID (killed at the 10-minute tool limit); R2 0/3/2; R3 0/1/2 (the major was the contested `clip.py` item, resolved by ruling); R4 0/0/1 (out of envelope, fixed). Converged. Evidence `clearwater-review-evidence\wp1.4b\r1`, `r2-void`, `r2`, `r3`, `r4`. |
| Reviewer B | One seat pass on `afaff0e`: `NO_NEW_CRITICAL_MAJOR`; 3 minor and 2 advisory. Report overstatements corrected as errata at the gate; the rest banked as DR-30. |
| Owned and touched files | Owned: `tools/prototype/params.py` (the flip and docstrings), `tools/noise_experiments.py` (new), `tools/camera_state.py` (new), `tests/test_noise_experiments.py` (new), the report, the ledger. Pins only (65 test sites: lookcheck 2, lookcheck_deep 1, backend 5, pipeline 9, clip 20, temporal 28). Authorised text-only edits: `tools/prototype/clip.py` `--method` help, `tools/statistics_experiments.py` `render_clips` docstring; `tools/prototype/run.py` help names c3 as the default (guard ii). No change to `pipeline.py`, `temporal.py`, `backend.py`, `tools/lookcheck/`, `pyproject.toml` or `src/`. |

## Orchestrator rulings during the package

1. **The noise measure (the cell's STOP, 06:44Z).** The brief's Donoho estimate read exactly 0 on
   all 8 deep frames: 63-99 % of the HH1 coefficients in the flattest tiles are exactly zero
   (8-bit HEVC flattening; evidence `work\wp1.4b\stop\`, md5 `be6c2ce0`, `3e3a008c`). The
   orchestrator had chosen Donoho in the brief. Ruling: Immerkær on the same fixed tiles is
   primary; Donoho is the cross-check; settings are compared on the absolute output `sigma_R`;
   the source ratio only where the source reads above 0; a red-lit tile set (source red mean
   >= 16/255) leads; a quantised-regime validation test. CHARC upheld it (`99fd817f74e4a428`)
   and added two report notes (the "below the quantisation floor" wording; the total red gain,
   camera WRGB red x ours, as a context column). Both are in the report.
2. **Three text-only edits outside the pin rule** (CR-02/CR-01): the `clip.py --method` help
   (its default stays `ancuti2018` so the WP1.2B report reproduces; the help says so and names c3
   as the product default; a guard test); the `statistics_experiments.py` `render_clips`
   docstring; the `Params.neutral()` docstring.

## Bit-identity witness (the flip, orchestrator seat)

`correct()` with the method given EXPLICITLY, from main `9b6093f` (default ancuti2018) and from
the candidate `afaff0e` (default c3), on a fixed synthetic 600 x 900 image (seed 12345), float32,
`np.array_equal`: **bit-identical in 6 of 6 cases** (Ancuti 2018 blue off and on, and 3C; CPU and
GPU). Only the default changed. Script `witness_flip.py` (orchestrator scratchpad; the WP1.4
`witness_r.py` was not found on disk, so the witness was re-written to the same specification).

## Reviewer B (seat, single pass), on candidate `afaff0e`

Transcript `clearwater-review-evidence\wp1.4b\reviewB\review-B.txt`, md5
`9e7e8e0707083be04fd4480bc368c3c7` (prompt `e9709257`, diff `3482e0de`, stderr `25bbfc93`, probe
`403e9637`). Assertions: banner gpt-5.6-sol / high / read-only; `^ERROR` 0; the one
`ERROR codex_core` hit is an echo of the brief's text; `tokens used` footer; 38 `succeeded in`;
VERDICT anchored. Withheld access: no command opened `docs/proofs/`, the evidence folder, the
footage folder or the GPMF tracks (its record listing excluded `*/gpmd/*`).
**VERDICT: NO_NEW_CRITICAL_MAJOR.**

Confirmed by B's executed record probes: the flip commit changed only `Params.method` and its
sentence, no pre-existing expected value changed; every render carries its labelled parameters
(25 settings per deep and shallow frame, all GPU); cap 2.0 differs from cap off by at most 0.0147
code values; cap 0.5 raises red-lit noise on all 8 deep frames and lowers flat-tile noise only on
the four below-floor frames; 3C is the lowest-noise setting on every deep frame; claims 10 and 10b
match their records; nothing under `work/` (no GPMF track) is committed.

| # | Finding | Disposition |
|---|---|---|
| 1 | MINOR: "it does not track the ISO" overstated (rank correlation 0.60, n = 8, five tied at ISO 100) | Erratum at the gate in the report |
| 2 | MINOR: "the bias does not distort amplifications" holds only for a scalar gain | Erratum at the gate: operational ratios; KEEP rests on absolute outputs |
| 3 | MINOR: the sharp-edge test pins Donoho only, not the primary Immerkær | BANKED, DR-30 |
| 4 | ADVISORY: "green noise carried in" is an inference, not directly measured | Erratum at the gate: labelled an inference |
| 5 | ADVISORY, out of envelope: the GPMF reader's nesting, padding and SCAL laxness | BANKED, DR-30 |

## Verification QA (orchestrator seat)

**Gate checks on the candidate `afaff0e`:** ruff clean; format 117 files; mypy 22 files clean;
pytest **771 passed, 0 skipped** (894 s; the suite now exceeds 10 minutes in one call); gpu 36
passed; harness 366 OK (1 skipped).

**Gate checks on main `afaff0e`** after `uv sync`: ruff "All checks passed!"; format "117 files
already formatted"; mypy "Success: no issues found in 22 source files"; pytest **771 passed**, 1
warning (475 s); gpu 36 passed, 735 deselected; harness Ran 366, OK (skipped=1).

## Results for WP1.6 (Gate result 4 and design evidence)

Red-lit tiles, median over the 8 deep frames (context: ISOE 100 [100-793]; camera WRGB red 3.73
[3.12-4.85]):

| Setting | sigma_R (code values) | amplification | our red gain | total red gain | R/G | bound |
|---|---|---|---|---|---|---|
| Ancuti, cap off | 0.736 | 2.43 | 1.52 | 5.98 | 1.00 | 0/8 |
| Ancuti, cap 2.0 (default) | 0.736 | 2.43 | 1.54 | 5.98 | 1.00 | 1/8 |
| Ancuti, cap 1.0 | 0.783 | 2.50 | 1.72 | 6.55 | 1.01 | 3/8 |
| Ancuti, cap 0.5 | 0.938 | 2.84 | 1.97 | 7.60 | 1.02 | 8/8 |
| c3 (default method) | 0.481 | 1.53 | 1.05 | 3.95 | 1.00 | n/a |
| shallow reference | 0.565 | 1.20 | 1.03 | 2.61 | 1.01 | 0/1 |

- **Gate result 4: KEEP the caps.** The default cap is nearly inert on deep footage (binds on
  1 of 8). A tighter cap raises red noise wherever the source red has a baseline (8 of 8), as
  D100 expects.
- **The one-frame signal against D100 did NOT hold across the grid.** A tighter cap lowers red
  noise only on flat tiles whose source red is below the quantisation floor (4 of 8 frames),
  where the output red is, by inference, green noise carried in by the compensation term. The
  report reads this as an exception, not a contradiction, so not spec-bearing.
- **Clamp (D99):** keep 3.0. It never binds under either method; 1.5 binds on 5 of 8, leaves a
  cast down to R/G 0.80 and cuts noise by under 1 %.
- **N{} range floor (DR-14):** 0.02 proposed (largest stretch 50x); the measured deep ranges are
  0.028-0.64, so it binds on none. A higher floor is a look decision.
- **Claim 10 (smoothing the capped alpha):** keep (A), alpha smoothed as a value. Flicker 0.388
  against 0.483 for (B); the per-frame cap binds on 46 of 179 clip frames.
- **Claim 10b: the lighting step is a GENUINE scene change at 0.90 s, NOT an excerpt edge
  effect.** A 3 s lead-in (more than the 87-frame staged reach) moves no applied gain by more
  than 0.014; the recomputed 2 s series equals WP1.3D's record exactly. Neither a reset at the
  step nor a 0.5 s window shrinks it, and both add flicker (0.5 s: +23 % to +68 %). Keep 2 s,
  PROVISIONAL per DR-25(3); evidence for the Phase 2 temporal design.
- **c3** has the lowest red noise on every deep frame (total red gain about 4x against about 6x
  for Ancuti at the default).

## Process deviations (the orchestrator's)

- **Two writers in one worktree (~5 min).** The claim 10b amendment was sent to `wp14b-cell`
  mid-work (06:15Z). It STOPped at 06:44Z and was re-seated as `wp14b-cell2`; the queued message
  then woke the old cell, which ran claim 10 and began 10b while cell2 edited
  `tools/noise_experiments.py`. The old cell noticed the foreign edits and halted; it was stood
  down at 06:50Z with nothing reverted or committed. Its claim 10 records were handed over and
  reproduced exactly by cell2's code. Practice added: at a re-seat, stand the old cell down
  explicitly before dispatching the successor.
- **A ruling that landed late.** The 08:21Z ruling (three text edits plus one round) reached
  cell2 only after it had run round 3 and returned; it then woke the cell, which ran the
  authorised round as round 4 (converged). A superseding message (no further round) arrived after
  the work was done. Round 4 is counted.
- **The brief's noise measure** (Donoho as primary) was the orchestrator's choice and did not
  survive real deep footage; see ruling 1.

## Follow-ons

- **WP1.6 gate report:** Gate result 4 KEEP; the clamp, N{} floor, claim 10 and 10b evidence
  above; the two answers CHARC asked to put plainly to the owner (the anti-D100 signal did not
  hold in general; the lighting step is a genuine scene change).
- **DR-30** (new, OPEN): the Immerkær edge-case test; the GPMF reader's structural laxness.
- Branches kept: `wp1.4b` (`8314247`).
