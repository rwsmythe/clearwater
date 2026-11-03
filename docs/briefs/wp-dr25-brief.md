# WP-DR25 — The staged smoothing run on a long excerpt (dispatch brief, DRAFT for the orchestrator's fill)

**Status:** DRAFT 2026-11-03 by CHARC (generation 13), the DR-25 (3) paydown re-assigned at the WP5.6 accept (`d156ed49`: assigned to WP5.2 by the register, omitted from WP5.2's brief; CHARC's miss). Tools-only; no product code; no spec change. Owner decisions inside the package: none (AD-3's confirmation is a CHARC decision from the figures).

| Field | Content |
|---|---|
| ID and title | WP-DR25 — The WP1.4 staged smoothing experiment re-run on excerpts long enough to have edge-free frames at the 2 s and 4 s windows, so ground 2 of AD-3's `median_gaussian` 2.0 s default is measured, not provisional (DR-25 (3)) |
| Lane | **CODEX**: `implementer-codex-sol-high` (a committed instrument run to a fixed plan with one parameterisation change; no frozen interface). Reviewer A = the Claude pass at the cell's seat; Reviewer B = the Claude pass at the orchestrator's seat. Evidence `C:\Users\rwsmy\clearwater-review-evidence\wp-dr25\`. |
| Tier and size | STANDARD. Size S (one instrument change, two runs, a short report). Codex evaluate at about 200K, STOP near 250K. |
| Base | main at dispatch (at or after `5cfe1bb4`). Worktree `.worktrees/wp-dr25`, branch `wp-dr25`. |
| Goal | The WP1.4 report's ground 2 for the 2 s default ("0.106 and 0.053 flicker levels against 0.236 and 0.151 unsmoothed") was measured STAGED on two 6 s excerpts whose staged reach at 2 s (3 stages x 30 frames = 90 frames) exceeds half the excerpt, so no staged 2 s frame was edge-free (Reviewer B at WP1.4; DR-25 (3)). Re-measure the staged 1 s, 2 s and 4 s figures on excerpts with at least 182 edge-free frames at the 2 s window (and the edge-free count at 4 s stated), on the same two chapters at the same positions, and state whether ground 2 holds (the 2 s level within the report's claimed margin below 1 s). |
| Spec / decision clauses | 7.2 (temporal smoothing over pts, D95); AD-3 (`median_gaussian` 2.0 s PROVISIONAL, DR-25 (3)); D98 (staged versus flat: no visible difference; one stage permitted); DR-25 (3) text in the register. |
| Files owned | `tools/statistics_experiments.py` (ONLY: `EXCERPTS` gains a length parameter or a second tuple `LONG_EXCERPTS` selected by a new `--long` flag; `staged_reach` and the edge-free accounting already exist: use them; nothing else in the instrument changes); `docs/reports/wp-dr25-staged-run.md`; a unit test in `tests/test_tools_statistics_experiments.py` for the new selection (if that file exists; else a new small test module). |
| NOT owned | `src/clearwater/` entirely (the product smoother `analysis/smoothing.py` is not touched; the instrument uses the read-only prototype as it did at WP1.4); `tools/prototype/`; `tools/step_aware_eval.py`; the WP1.4 report (an erratum pointer is added by CHARC at the accept, not by the cell). |
| Locks | No frozen interface. No dependency. Footage read-only through `tools.local_config.find_footage_file`; outputs under `work/wp-dr25/` (NOT under `work/wp1.4/`, which is archived on D:). |
| Markers | The instrument run is not a test. The selection test is parallel-leg, synthetic. |
| Hardware flags | GPU, light (the WP1.4 extract and analyse phases on two excerpts of about 20 s each: minutes, not hours). Not EXCLUSIVE; no timing figure. `df -h /c` before (STOP below 25 GB free). |
| Out of scope | Changing the smoother, its default or AD-3 (CHARC rules from the figures); the step-aware variants (WP3.11 evaluated them; `tools/step_aware_eval.py` records the span and edge-free counts for ITS excerpt of GX011600 and is cited, not re-run); the render phase (the flicker clips: the figures come from `analyse`); the WP1.4b noise test. |
| Debt and decided items | At the accept CHARC writes: DR-25 (3) CLOSED (ground 2 measured edge-free, whichever way it falls); AD-3 PROVISIONAL → CONFIRMED (if the 2 s level stays below 1 s's by the claimed margin) or an AD-3 note with the measured gap and a recommendation (if not; a default change would then be a spec 7.2 decision for the owner); the WP1.4 report gets a one-line erratum pointer to the new report. |
| Done | Plan 4.5. ruff, format, mypy clean; the selection test green; `extract` and `analyse` run on both long excerpts with the records under `work/wp-dr25/`; the report; Reviewer A converged; Reviewer B clean or its single remediation done. |

## The plan (fixed)

1. **Excerpt length.** The staged reach at 4 s is 3 x 60 = 180 frames at 29.97 fps; to have at least 182 edge-free frames at the 2 s window (reach 90) the excerpt needs 90 + 182 + 90 = 362 frames = 12.1 s, and to have edge-free frames at 4 s as well, 180 + 182 + 180 = 542 frames = 18.1 s. Use **20.0 s** excerpts (about 600 frames), same chapters and the same start fractions as `EXCERPTS` (GX011627 at 0.30, GX011625 at 0.50) so the long excerpt contains the original 6 s one. If a chapter's remaining duration is shorter at that start, move the start back so the excerpt fits and record it; keep `expected_ticks` None for the long specs (the instrument records the actual ticks).
2. **The change.** `--long` selects `LONG_EXCERPTS` (names `GX011627-long`, `GX011625-long`, `duration_s=20.0`, `full_frame=False`, `render=False`) and the output root `wp-dr25` instead of `wp1.4` (the `WORK_SUBDIR`). Nothing else changes; the default run stays the WP1.4 run.
3. **Runs.** `uv run python tools/statistics_experiments.py extract --long` then `analyse --long` on the GPU. Record `results.json`, `statistics-staged.json`, `statistics-flat.json` per excerpt, and the edge-free frame counts the instrument already prints for 1 s, 2 s and 4 s (`staged_reach`).
4. **The reading.** For each excerpt and each method (`c3`, `ancuti2018`): the staged flicker level at 1 s, 2 s and 4 s on the edge-free interior ONLY, beside the flat interior figure (the WP1.4 report's edge-free comparison: 0.168 / 0.036 at 2 s against 0.183 / 0.048 at 1 s), and the unsmoothed level. State: does 2 s leave less flicker than 1 s on the edge-free staged interior, by how much (per cent), and is the 6 s excerpt's staged figure (0.106 / 0.053) biased by its boundary (the new figure at the same window on the same frames' interior).
5. **Nothing is decided by the cell.** The report states the figures and the comparison; AD-3's status is CHARC's ruling at the accept.

## Questions (CHARC's recommended answers)

- **Q1 the edge-free definition.** Recommended: the instrument's `staged_reach` (stages x radius) from BOTH span ends, as WP3.11's `step_aware_eval.py` records it; state the count per window.
- **Q2 both methods.** Recommended: yes, `c3` (the default) and `ancuti2018`, as WP1.4 did.
- **Q3 the step-aware kinds.** Recommended: NOT re-evaluated here (WP3.11 did, on its own widened excerpt); cite its span and edge-free counts in the report's context section.

## Completion report (`docs/reports/wp-dr25-staged-run.md`)

The two long excerpts (chapter, start, ticks, frame count, edge-free counts per window); the staged and flat levels per method and window with the WP1.4 figures beside them; the ground-2 reading; the exact commands; limits (two chapters, snorkel only; the deep step case is WP3.11's).

## Yields and depth

Turn 1 = round 0 (the `LONG_EXCERPTS` definition and the output root, the expected edge-free counts; any Q dispute = STOP) and YIELD; turn 2 = the change, the test, `extract` and `analyse`, committed, YIELD for Reviewer A; the report; the nets.

## Orchestrator dispatch fill (for CHARC to finalise)

- Lane paces at dispatch; base commit; worktree; evidence folder.
- Order: on the Codex lane after WP5.8 (or interleaved between WP5.8's turns: its runs are light); before WP5.5.
- GATE_CHECKS: `docs/review-gate-clearwater.md` Part 2 on the final candidate (tools-only: the parallel leg and the harness gate suffice unless a serial-leg test touches `statistics_experiments`; check collection identity).
