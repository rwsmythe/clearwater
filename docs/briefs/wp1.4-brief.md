# WP1.4 — Noise and statistics experiments, shallow part (dispatch brief, DRAFT by CHARC)

**Status:** DRAFT by CHARC 2026-10-15 for the orchestrator to finalise and dispatch AFTER
WP1.3 merges (it imports WP1.3's `tools/lookcheck/frames.py`). Spec **v0.5.2**. Released on
the owner's partial CP1 ("shallow confirmed", 2026-10-15; `docs/proofs/cp1-footage-sorting.md`).
Cell: `implementer-opus-high` (the mismatch measure, the smoothing comparison and the
robust-statistics study are reasoning-dense). Worktree `.worktrees/wp1.4`, branch `wp1.4`,
base = the main commit named in the dispatch. Needs footage: `GX011627.MP4` (and
`GX011625.MP4` for a second clip). Footage READ-ONLY; outputs under `work/wp1.4/`. Uses the
GPU; records no timing or memory figure; NOT exclusive; must not overlap WP1.2 Part B's bench
window.

**The gain-cap noise test (D100) is NOT in this part.** It needs a deep frame (the scuba
clips, ~20 m). It is commissioned as WP1.4b the day the owner sorts that footage, reusing
this part's tools. Gate result 4 stays PENDING until then; this part delivers result 5 and the
design evidence of plan section 9 rows "Smoothing filter type and default window", "Robust
statistics for normalization bounds" and "Stage definitions per compensation method".

| Field | Content |
|---|---|
| ID and title | WP1.4 — Noise and statistics experiments (shallow part); plan section 6 WP1.4; Gate result 5 (and the design items above) |
| Goal | On a short real clip: (a) compute the whole-frame statistics STAGED (D97: each stage measured on the frame corrected with the SMOOTHED results of the stages before it) and FLAT (every statistic measured once on the raw frame, then smoothed independently), with the same temporal smoothing, measure the mismatch, and render both versions for the owner to compare at CP2 (D98); (b) try candidate smoothing filters and window lengths and report which flicker measure they achieve at what cost in responsiveness; (c) try candidate robust statistics for the N{} normalisation bounds and report their frame-to-frame stability and their effect on the result. |
| Spec clauses | D97, D98, 7.1, 7.2 (staged statistics; centred time-based window, D95; the four statistic families); D99 (clamp); 14.1 "Temporal smoothing filter type and default window", "Robust statistic choices for normalization bounds", "Stage definitions for each compensation method"; D108 (provisional preview = unsmoothed per-frame statistics, so the unsmoothed render is also what the user first sees); D112 and V3 (flicker on a synthetic clip is a LATER test; here the measure is on real footage and is evidence, not V3); 6.4; 7.3 (statistics from proxies). Plan section 10 row 5. |
| Depends on | WP1.3 (merged: `tools/lookcheck/frames.py`, the flicker excerpt's pts range), WP1.1/WP1.2A (merged), partial CP1 (done). |
| Files owned | `tools/prototype/temporal.py` (NEW: per-frame statistic extraction, the staged and flat analyses, the smoothing filters, the render-from-supplied-statistics path), `tools/prototype/pipeline.py` ONLY for an additive hook that lets `correct()` take supplied statistics (see decisions), `tools/statistics_experiments.py` (the runner), `tests/test_prototype_temporal.py`, `docs/reports/wp1.4-statistics.md`, `docs/proofs/wp1.4-ledger.md`. NO change to `params.py`, `backend.py`, `bench.py`, `run.py`; NO `pyproject.toml` change; nothing under `src/`. |
| Interfaces consumed | `tools.lookcheck.frames.excerpt` (frames as 16-bit PNG with exact pts); `tools.prototype` by import; `ffmpeg` for re-assembly; `tools/local_config.py`. |
| Interfaces provided | None frozen. The `Statistics` record (the per-frame values of every whole-frame statistic, per stage) and the `correct(..., statistics=...)` hook are the prototype's first draft of IF-3's `analyze`/`render` split; WP2.1 reads them. Document the record in the report. |
| Dependencies | None new (NumPy/SciPy/CuPy already granted). |
| Tests | `tests/test_prototype_temporal.py`, synthetic: (1) IDENTITY: `correct(frame, params, statistics=statistics_of(frame))` is bit-identical to `correct(frame, params)` on CPU and GPU (the hook changes nothing when fed the frame's own statistics); (2) every existing prototype test passes unchanged (additions only); (3) a synthetic 3-frame sequence where frame 2 has a shifted channel mean: staged and flat differ in the documented direction (white-balance gain measured on the compensated frame versus the raw frame), flat-minus-staged mismatch nonzero and equal to the hand-computed value; (4) each smoothing filter is centred (a symmetric impulse response, zero phase: a step input's smoothed output is symmetric about the step), with the window given in SECONDS converted by the clip's frame rate; (5) the flicker measure is zero on a constant sequence and positive on an alternating one; (6) the robust-statistic candidates return the documented values on a known array (incl. the flat-image case of DR-14); (7) `footage`: the runner on 10 frames of `GX011628.MP4` writes its record. |
| Hardware flags | `footage`, `gpu`. Not exclusive. |
| Out of scope | The gain-cap noise test (WP1.4b, deep frame); changing any default (report, do not retune); V3 itself (WP5.1 on the synthetic clip of WP2.3); scene cuts and chapter spans (7.2: inputs are continuous; spanning is WP3.11's); the product's analysis engine; timing. |
| Done | Plan section 4.5; the four gates green with `footage` and `gpu` RUN; harness gate untouched; the two rendered clips and every record under `work/wp1.4/`; the report complete with the three result sections and the design recommendations. |

## What the package does (claims)

1. **Statistics per frame.** On the WP1.3 flicker excerpt of `GX011627.MP4` (same pts range;
   ~180 frames) and on a second 6 s excerpt of `GX011625.MP4` at 50 % of its duration, compute
   per frame, on a PROXY (short side 540, area-averaged from the full frame; the 7.3 path) AND
   on the full frame for the first excerpt only (to record the proxy-versus-full statistic gap
   on real footage, extending WP1.2A's synthetic finding): the chained statistics of spec 7.1
   for `ancuti2018` (blue off, the default): compensation channel means and effective alpha
   (stage 1); white-balance means and gains (stage 2); N{} bounds (stage 3); saliency
   reference Lab means (stage 3). For `c3` the chain starts at white balance (7.1). Record
   everything to `work/wp1.4/<excerpt>/statistics-{raw,staged,flat}.json` with pts.
2. **Staged versus flat (D98).** With ONE smoothing filter fixed for the comparison (centred
   Gaussian, window 1.0 s, defined as the full width at which the kernel falls to 1 %; the
   cell states the exact definition): STAGED = smooth stage 1, re-measure stage 2 on frames
   corrected with smoothed stage 1, smooth, re-measure stage 3 likewise, smooth; FLAT = measure
   all stages once on the raw frame, smooth each independently. Report the mismatch per
   statistic (flat minus staged, per frame; its mean, max and the frame of the max) and the
   RESIDUAL FLICKER each leaves (claim 4's measure on the rendered frames). Render both
   versions of the first excerpt at full resolution through the supplied-statistics hook,
   assemble with FFmpeg as WP1.3 did (`GX011627_staged.mp4`, `GX011627_flat.mp4`, plus
   `GX011627_unsmoothed.mp4` = WP1.3's clip re-rendered here so all three come from one code
   path), for the owner at CP2. Say in one paragraph whether the cell expects the difference
   to be visible, from the numbers; the owner decides (plan section 10 row 5).
3. **Smoothing candidates (14.1).** On the raw per-frame statistics of both excerpts: centred
   moving average, centred Gaussian, and a centred median followed by a Gaussian (robust to a
   single bad frame), each at windows 0.5, 1.0, 2.0 and 4.0 s. For each, report the residual
   flicker (claim 4) and the lag/attenuation on a step: the response to a synthetic step of
   the statistic (how many seconds to reach 90 %), so CP2/WP2.1 can trade flicker against
   responsiveness to a real change (a diver turning from sand to blue water). Recommend one
   filter and one default window, with the grounds.
4. **Flicker measure.** Defined by the cell, documented with its limits, and USED CONSISTENTLY:
   the suggested form is the mean absolute frame-to-frame difference of the corrected frame's
   per-channel mean and of its luma mean, minus the same quantity on the SOURCE frames (so
   camera motion and content change cancel to first order), on the proxy frames. Report also
   the per-frame series so a spike can be seen. Note explicitly that V3 (D112) is measured
   differently, on the synthetic clip, later.
5. **Robust statistics for the N{} bounds (14.1, DR-14).** Candidates on the raw high-pass of
   each frame: min/max ([A18]); percentiles 0.5/99.5 (the current default), 1/99, 2/98; a
   trimmed-standard-deviation form (mean ± k·sigma, k = 2.5 and 3). For each: the frame-to-
   frame stability of the bounds (coefficient of variation over the excerpt, before
   smoothing), the fraction of pixels clipped by the stretch, and the behaviour on a
   near-flat frame (DR-14: state the smallest range seen and whether the 1e-6 flat floor
   triggered). Recommend one with grounds; the default is NOT changed in this package.
6. **Stage definitions.** From the measurements, the report states the stage list the cell
   recommends each method declare under IF-3 (ancuti2018: compensation → white balance →
   fusion statistics; c3: white balance → fusion statistics), which statistics are smoothable,
   and what a parameter change in each stage invalidates (7.3), as the evidence for the
   plan-section-9 row "Stage definitions per compensation method; live-preview recompute scheme".
7. Docstrings complete; ruff, ruff format, mypy strict and pytest green with `footage` and
   `gpu` RUN; the identity test (1) green on both devices; every existing test unchanged.

## Decisions fixed at issue (CHARC)

- **The supplied-statistics hook is additive and identity-preserving.** `correct(image, params,
  backend=None, statistics=None)`: with `statistics=None` the code path is the one WP1.2R
  accepted, bit for bit (test 1 and the orchestrator's witness protect this). The hook feeds
  the recorded scalars where the pipeline would have measured them; it does not restructure
  `correct()`. Any larger refactor is a STOP.
- **Statistics are measured on proxies** (short side 540, area average) because that is the
  product's path (7.3) and the 4K full-frame path costs ~0.4 s/frame on the GPU; the full-frame
  series is recorded ONCE (first excerpt) to quantify the proxy gap on real footage. Renders are
  full resolution.
- **One method for the renders** (`ancuti2018`, blue off, the default); the statistics study
  runs for both methods because the stage structure differs.
- **No default changes.** Recommendations go to the report; WP2.1 and CP2 decide.
- **The flicker measure is an instrument of this package, not V3.** Said in the report.
- **Outputs.** `work/wp1.4/` only; nothing large committed; the report cites paths.
- **ffmpeg invocation** as WP1.3: inside `work/wp1.4/` only, with the output-path assertion.

## Declared operating envelope

Windows 11, FFmpeg 9.0.2, the shallow HERO13 chapters (HEVC 8-bit, BT.709 full range,
30000/1001), the prototype at defaults on the RTX 4070, continuous excerpts without scene
cuts. Deep frames (the noise test), photos, chapter spans, HDR/GP-Log, V3's synthetic clip
and any default change are out of envelope.

## Review loop (Reviewer A) -- per `docs/review-gate-clearwater.md` Part 1

- Tier **STRONG** (touches `tools/prototype/pipeline.py`; the result decides D98 and the
  smoothing design). Transport, flags, probe, diff, prompt, per-round assertions, evidence
  `clearwater-review-evidence/wp1.4/rN/`, ledger `docs/proofs/wp1.4-ledger.md`, exactly as the
  WP1.5 brief states them with `wp1.4` substituted.
- WHAT TO EXAMINE: whether the hook is identity-preserving on both devices; whether STAGED
  really re-measures each stage on frames corrected with the SMOOTHED earlier stages (not the
  raw ones), and FLAT really measures everything on the raw frame; whether the filters are
  centred and the window is in seconds; whether the flicker measure cancels content motion as
  claimed and is applied identically to every candidate; whether every number in the report
  is in a record under `work/wp1.4/`; whether any ffmpeg flag could write outside the working
  folder.
- Reviewer B is the orchestrator's own seat pass on the merge candidate (fill Part 2 item 2).

## Notes for the cell

- Return report = your FINAL message, under about 70 lines, per `docs/dispatch-recipe.md`
  section 4: per-commit change list; validation lines; verification-loop record; review
  rounds, ledger and evidence paths; locks honoured; the three result tables in brief
  (mismatch, smoothing candidates, robust statistics) with the record paths; the three
  recommendations with one-paragraph grounds each; the stage-definition proposal; deviations
  and open questions.
- STOP for: a refactor of `correct()` beyond the additive hook; an identity-test failure you
  cannot attribute; a GPU failure; any output outside `work/wp1.4/`; a need for a new
  dependency.
- Working rules as the WP1.5 brief: `uv sync` in the worktree; commit by pathspec with
  `feat(wp1.4): ...` and the `Co-Authored-By:` footer; never a bare `cd`; never post to a
  mailbox; the footage folder is input-only; the local config is copied into the worktree by
  the orchestrator and never committed.
