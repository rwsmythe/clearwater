# WP3.4 — Method assembly: stages and parameter schema (dispatch brief, FINAL)

**Status:** DRAFT 2026-10-21 for CHARC (commission `e7745b2be6fdd55c`, tranche A); drafted by a
drafting helper of the orchestrator (gen 9). Owner decisions: none inside the package (the
defaults are AD-8 as recorded in v0.5.4; D100 caps KEPT, AD-26).
- Spec **v0.5.4** (approved by the owner 2026-10-20, AD-27). Architecture FINAL 1.0 sections 2
  (data flow), 3 (IF-1, IF-2, IF-3, IF-4, IF-9) and 4 ("Correction core (WP3.1-3.4)"); AD-1,
  AD-4, AD-6, AD-7, AD-8, AD-11, AD-20, AD-21, AD-26. Frame `docs/briefs/wp2.4-phase3-frame.md`
  (section 5 maps "D98 one stage permitted" and "6.3 defaults" here). Reports
  `docs/reports/wp3.1-array-backend.md` ("Speed row (task 7)", "Consumer notes"),
  `docs/reports/wp3.2-compensation-white-balance.md` ("Consumer notes", "DR-19 rule"),
  `docs/reports/wp3.3-fusion.md` ("DR-19 rule", "Sync points (for WP3.21)"),
  `docs/reports/wp3.16-shell-preview.md` (claim 4, the V8 harness). DR-13, DR-19, DR-37, DR-38,
  DR-40 (row "Debt and decided items").
- Cell: `implementer-opus-high`. Tier **STRONG**.
- Worktree `.worktrees/wp3.4`, branch `wp3.4`, base = the main commit named at dispatch.

**Why.** Plan 11.1's critical path runs WP3.1 → WP3.2 and WP3.3 → WP3.4. Everything above the
core reaches a method only through IF-3 (spec 10.1; architecture section 1). WP3.2 and WP3.3
delivered the per-step numerics as step functions with a measure / closed-form / render split;
this package turns them into the two registered methods, owns the parameter schema (where
DR-19 closes), and takes the whole-core speed row and the product memory-peak re-check that
WP3.1 deferred to it (WP3.1 brief questions 3 and 4; WP3.1 accept "Follow-ons").

| Field | Content |
|---|---|
| ID and title | WP3.4 — Method assembly: stages and parameter schema; plan section 6 Phase 3 row WP3.4 (size M); module `clearwater.methods` (plan 8.1: "Correction method plug-ins; v1 has one, Ancuti fusion with selectable compensation", built by WP3.2–WP3.4) |
| Goal | The IF-3 methods `c3` and `ancuti2018` in `clearwater.methods.ancuti_fusion`, assembled from the merged WP3.2/WP3.3 steps: ordered stages with their dependencies, `analyze` per stage, `closed_form`, `render` from supplied statistics with "blend with original", and the parameter schema with Basic/Advanced placement and its validation (DR-19 closes); the method-level V1, V8 and V9 tests; the banked core fixes; and, in EXCLUSIVE windows, the whole-core speed row and the memory-peak re-check. |
| Spec / decision clauses | Plan bullet "**WP3.4** assembles the plug-in (IF-3): the ordered statistic stages with their dependencies, `analyze` per stage, `render` from supplied statistics, the parameter schema with Basic/Advanced placement, and "blend with original". Includes the neutral-parameter identity test at method level." 10.1 "**Statistic stages:** an ordered list. Each stage declares: the whole-frame statistics it produces; which of them are temporally smoothed; which parameters they depend on; which earlier stages they depend on."; "**analyze(stage, frame, params, earlier statistics) → statistics:** the per-frame statistics for one stage, given the smoothed results of earlier stages."; "**render(frame, params, statistics) → frame:** correction using externally supplied (e.g., smoothed) statistics."; "**Parameter schema:** names, types, ranges, defaults, and Basic/Advanced placement, so the GUI is method-agnostic."; "A method with one stage is valid; this is the flat scheme. Dependencies let the host redo only the affected work when a parameter changes." 6.7 Basic: "Compensation method (3C, the default / Ancuti 2018)", "Compensation strength (α for Ancuti 2018; combined κ/λ for 3C)", "Blue compensation on/off (Ancuti 2018 only)", "White balance strength", "Sharpening strength (fusion input 2)", "Blend with original (0–100%; 0 = fully corrected, 100 = the original, 0.5.4 AD-8)"; Advanced: "Red gain cap and blue gain cap (Ancuti 2018 only; subject to D100)", "κ and λ individually (3C only)", "Maximum white-balance gain (D99)", "Gamma (fusion input 1)", "Pyramid minimum level size". 6.2 step 2: the clamp applies "to the gains actually used for rendering (the smoothed gains for video)". 6.6 "Consequently, a screen-resolution preview closely approximates the full-resolution result, and a 1:1 view is exact (verified by V8)." D16 "Both channel-compensation methods (Ancuti 2018 and 3C) included, user-selectable; 3C is the default"; D17 "All parameters exposed; technical parameters in an Advanced panel"; D49 "Gain cap does not apply to 3C; cap controls hidden when 3C is selected"; D61 "*(amended by D97)* Plug-in interface: ordered statistic stages, analyze per stage, smoothing declaration, parameter and stage dependencies, render, parameter schema"; D97 "Whole-frame statistics are analyzed in ordered stages; each stage is measured using the smoothed results of the stages before it. A method may declare a single stage"; D98 "Staged analysis is the v1 default; ... a method may declare one stage; the plug-in interface stays staged"; D106 "interim, about 25 minutes of processing per minute of 4K footage on the owner's laptop"; N4 "graphics memory is measured and treated as a second limit". Feeds V1 "unit tests for each stage (both compensation methods, red/blue compensation, gain caps, 3C mask and kernels, white balance and its gain clamp, normalization, weights, pyramid fusion, staged statistics ordering), including edge cases: uniform images, near-zero red channel, 10-bit input"; V8 "screen-resolution preview vs downsampled full-resolution output differ by less than a threshold set at design; 1:1 view exact."; V9 "with every stage set to its neutral value (compensation and white balance strength 0, sharpening 0, gamma 1, and blend fully toward the corrected result), each stage reduces to identity and the output matches the input within a small color-difference tolerance for photos and video." AD-6 (Ancuti "(1) compensation means and effective alpha; (2) white-balance means and gains; (3) N{} bounds and the two saliency Lab means"; 3C "(1) white-balance means and gains; (2) N{} bounds and saliency means"; "the capped alpha is smoothed as a value; strength and the D99 clamp apply after smoothing (closed form)"; "a one-stage method is permitted (D98, Gate result 5)"). AD-7 ("closed-form dependencies (alpha from the means and caps; gains from means, strength and clamp) are updated without touching the proxy"). AD-8 (defaults; "**"Blend with original": 0.0 = fully corrected, 1.0 = the original**, linear in display-encoded values; the neutral set for V9 is WP1.1 section 4 (`Params.neutral()`)"). AD-11 (N10 bit-identical on one device; CPU vs GPU 2e-3 max / 2e-4 mean; V9 "max abs diff ≤ 2/255, mean ≤ 0.2/255"; V8 "mean abs ≤ 1/255, max ≤ 3/255"). AD-1 ("The estimate is the Part A/B formula (1.16x the pool's reserved peak at 4K)"). |
| Depends on | WP3.2 merged (accept `4b4da9b`): `clearwater.methods.compensation` `cap_statistics`, `effective_alphas`, `compensate_ancuti2018`, `compensate_c3`; `clearwater.methods.white_balance` `gray_world_gains`, `applied_gains`, `apply_white_balance`. WP3.3 merged (accept `09d1d11`): `clearwater.methods.fusion` `high_pass`, `normalisation_bounds`, `fusion_inputs`, `saliency_reference`, `laplacian_weight`, `saliency_weight`, `saturation_weight`, `weight_maps`, `multiscale_fusion`, `NORMALISATION_RANGE_FLOOR`. WP3.1 merged (accept `f4acbd0`): `clearwater.core`. WP2.2 (`b288533`, IF-1..IF-10 frozen, with the AD-20 amendments). WP3.16 merged (`a2685cb`; tests only): `clearwater.gui.imaging.measure_statistics`, `preview_export_difference`, `downscale`, `statistics_factor`. WP2.3 stills `png16-{uniform,gradient,lowred}-none`, `png8-{uniform,gradient,lowred}-none`. No stub needed. Parallel with WP3.9, WP3.10 and WP3.11; WP3.11 builds against `stubs.StubCorrectionMethod` and the shared contract of Y-1. |
| Files owned | `src/clearwater/methods/ancuti_fusion.py` (NEW: the two methods); `src/clearwater/methods/schema.py` (NEW, only if the round-0 table splits the schema out); `src/clearwater/methods/__init__.py` (owned from now on, X-2: exports and the registry of question 3). In `clearwater.core`, ONLY the banked items: `backend.py` (DR-37 (a); DR-38 (d); DR-38 (c) per question 6; the device-to-backend function of question 2), `ops.py` (DR-37 (b), question 5), `__init__.py` (one export, question 2). The type-only call-site lines of question 5 in `compensation.py`, `white_balance.py`, `fusion.py` (no numeric change). X1-style: `tools/core_speed.py` (extended, question 7; DR-37 (d), (e)). Tests `tests/test_methods_assembly*.py`, `tests/test_core_wp34*.py` (NEW), the extension of `tests/test_core_speed.py`. `docs/reports/wp3.4-method-assembly.md`; `docs/proofs/wp3.4-ledger.md`. NOT owned: `src/clearwater/interfaces/` (AD-20), everything else in `compensation.py`, `white_balance.py`, `fusion.py` and their test files (a numeric change there is a STOP), `core/memory.py` (task 8), `src/clearwater/gui/`, `tools/prototype/` (read-only reference), `pyproject.toml` (no dependency), `tests/conftest.py`, `tests/fixture_plugin.py`. |
| Interfaces provided | IF-3 exactly as frozen (`src/clearwater/interfaces/method.py`): two objects satisfying `CorrectionMethod` (`id`, `label`, `parameters`, `stages`, `analyze`, `render`, `closed_form`), ids `"c3"` and `"ancuti2018"` (architecture section 3: "registers two `CorrectionMethod` instances sharing the fusion code"; `clearwater.core.METHOD_IDS` is the same pair). c3's stages equal the frozen `stubs.C3_STAGES` (names, statistics, smoothed, dependencies, `source_only`); WP3.11 builds against them, so a needed difference is a STOP. Outside the IFs: the registry (question 3) and the device-to-backend function (question 2). |
| Interfaces consumed | IF-1 `Image`; IF-2 through `clearwater.core` (`NumpyBackend`, `CupyBackend`, `CoreBackend`, `channel_means`, `mean`, `check_sigma`, `spatial_sigma`; `channel_means` and `mean` return Python floats and are host sync points); IF-3 `Parameter` (with `nullable`), `Stage`, `Statistics`; IF-9 `validate_parameter_set(parameter_set, method_id, parameters)` (inclusive minimum/maximum, enum choices, None where `nullable`: what the schema can say). The WP3.2/WP3.3 steps carry the X-4 rule (one ValueError naming the parameter; the report sections "DR-19 rule"). `CoreBackend.xp` stays inside `clearwater.core` (WP3.1 ruling 1.1; `tests/test_core_deps.py`). |
| Consumers | WP3.11 (wave 3, parallel; Y-1), WP3.17 (panels generated from `parameters`, D49 by construction), WP3.14 (export render), WP4.1-WP4.3, WP3.21 (the speed row and the sync-point list). On main today: `clearwater.gui.imaging.measure_statistics` calls `analyze` per stage in order with the frame's own raw earlier results and passes the result to `render` (the D108 provisional path); the methods must work under that call pattern. |
| Hardware flags | `gpu` on every CuPy test. **EXCLUSIVE** (plan 4.3 "Any package that records a timing or a memory figure is flagged **exclusive**", frame rule 7): the whole-core speed row and the memory re-check (task 8), each in a window the dispatcher grants; `footage` (read only, GX011627 through `tools/local_config.find_footage_file`) on the speed row only. |
| Out of scope | The per-step numerics (WP3.2, WP3.3); the analysis engine, the statistics store, smoothing and recompute (WP3.11); video and photo I/O; the panels (WP3.17); optimisation (WP3.21, including the DR-40 (b) per-call uploads); the AD-1 formula in `core/memory.py`; D61's optional context inputs ("in a future version", IF-3 docstring); weight-map smoothing (D96, WP5.4); any method id or stage beyond the two methods; GoPro data (no `gpmd`, IMU or GPS data anywhere). |
| Debt and decided items | **DR-19 (OPEN) — CLOSES:** items (1) and (2) at method level through the schema and question 4, inheriting X-4 from WP3.2/WP3.3 (rule text in the report word for word); (3) does not recur (the core's bound); (4) held by the core's input checks; (5) the transcript's wrong implementations that concern the schema, stages or assembly, as planted tests. **DR-37 (a), (b) — CLOSES** (task 7, question 5); (c) — not this package's (the next touch of `tools/local_config.py`); (d), (e) — CLOSES if question 7 extends `tools/core_speed.py`. **DR-38:** (a) and (b) — ADDRESSES (the register's trigger is "WP3.4's brief"): a per-frame host-read COUNT test on each measure path, and the all-black / all-white grey weight test at method level; (c) — question 6; (d) — CLOSES: `check_sigma` raises ValueError, never OverflowError. **DR-40:** (a) — CLOSES by a test in this package's own file (cap None so alpha reaches the result, alpha as `np.float64`); `compensation.py` is changed only if that test fails (then STOP); (b) — ADDRESSES (question 6): the speed row records the per-call uploads; the fix stays WP3.21's. **DR-13 — must not reopen, placement only:** `laplacian_fraction` in Advanced, default 0.001 (AD-8); no recalibration (question 8). **D98 — IMPLEMENTS** the staged default; nothing in the assembly assumes more than one stage. **6.3 defaults (AD-8) — IMPLEMENTS:** every default stated once, in the schema. **D100 / AD-26 — must not reopen:** the caps are nullable in `ancuti2018`'s schema and absent from `c3`'s (D49 by construction). **DR-25 (2), (5), method side** — Y-2. DR-43, DR-44 — not this package's. |
| Done | Plan 4.5; frame section 2 rules 1-11; ruff check, ruff format --check, mypy strict, full pytest green with and without CuPy importable (in granted windows); V1 (staged statistics ordering), V8 and V9 at method level shown by named tests; product against prototype measured per method; DR-19 closed; the speed row and the memory re-check recorded in EXCLUSIVE windows; Reviewer A converged. |

## Task ladder

1. **Round 0 yield: the design table.** Before product code, write in the ledger:
   - per method, the stage table (name, statistics with each array's shape, smoothed,
     `depends_on_parameters`, `depends_on_stages`, `source_only`); c3's equal to
     `stubs.C3_STAGES`; Ancuti's compensation record per Y-1 (c), (e);
   - the schema table: every parameter (names = the prototype `Params` fields, X-1 (b), plus
     `blend_with_original`), type, default (AD-8), minimum, maximum, choices, panel, label,
     help, neutral (`Params.neutral()` for the six V9 controls, the default for the rest),
     `nullable`, per method (question 4);
   - each stage's `analyze` chain and `render`'s chain as calls of the WP3.2/WP3.3 steps, with
     every host read (the DR-38 (a) count);
   - every check the schema cannot express (question 4), in the X-4 form;
   - the answers to Y-1, Y-2 and questions 2-8, and the speed and memory plan (task 8).
   YIELD for the dispatcher. Anything the table cannot settle is a STOP.
2. **Stages and `analyze` (AD-6, D97).** Ancuti: (1) `compensation` measures the input's
   `channel_means` and `cap_statistics` for BOTH channels (WP3.2 consumer note:
   "`effective_alphas` ignores extra `cap_statistics` keys, so both channels' statistics can be
   cached (AD-7)") and derives the capped alpha per frame with `effective_alphas` (AD-6: smoothed
   as a value); (2) `white_balance` measures the means of the input compensated with the
   SUPPLIED stage-1 record and returns them with `gray_world_gains` (Y-1 (b)); (3) `fusion`
   white-balances with `applied_gains` on the supplied gains, measures `normalisation_bounds`,
   builds `fusion_inputs` with those bounds and measures `saliency_reference` per input (WP3.3
   consumer note: input 2's saliency mean depends on that frame's bounds). c3: (1)
   `white_balance` on `compensate_c3`; (2) `fusion` as above. `analyze` measures only its own
   stage, uses `earlier` exactly as given, and refuses an unknown stage or a missing earlier
   stage by name.
3. **`closed_form` (AD-7, Y-1 (d)).** Ancuti `compensation`: the record with alpha recomputed
   from the measured means and cap statistics and the current `alpha`, caps and
   `blue_compensation`; None for every stage whose measurement depends on parameters or earlier
   stages. Bit-identical to `analyze` on the same frame and parameters.
4. **`render` (10.1, AD-4).** From supplied statistics only; it never measures a whole-frame
   value, so preview and export agree by construction: compensation from the supplied record
   (Ancuti) or `compensate_c3`; `applied_gains` on the supplied gray-world gains (the D99
   clamp on "the gains actually used for rendering"); `fusion_inputs` with the supplied bounds;
   `weight_maps` with the supplied saliency means; `multiscale_fusion`; then
   `(1 - b) * fused + b * input` with `b = blend_with_original / 100` (AD-8; the schema value is 0..100 per the rulings). Output float32 in
   [0, 1], same device and colour description; refuses a missing stage (IF-3).
5. **Schema and validation (6.7, D17, D49, question 4).** One schema per method; c3 has no
   cap, `alpha` or `blue_compensation`; ancuti2018 has no `kappa`, `lambda_`, `c3_*`. Basic per
   6.7; every other parameter Advanced (D17), `laplacian_fraction` included (DR-13). Defaults
   AD-8, stated once. `validate_parameter_set` accepts every default and neutral set and refuses
   each out-of-range value; the method refuses what the schema cannot express (question 4).
6. **Registry and backend (questions 2, 3).** The registry with c3 first; `analyze` and
   `render` resolve the backend from `image.device` (question 2) and refuse an image whose
   pixels are not that backend's.
7. **Core fixes.** DR-37 (a): `_probe_gpu` reports `"CPU: CuPy not installed"` only for a
   `ModuleNotFoundError` naming `cupy`, every other import failure `"CPU: CuPy failed to load"`
   (no new reason string; the WP3.1 report's list stands). DR-37 (b) per question 5. DR-38 (d):
   `check_sigma` raises ValueError for an overflowing radius (WP3.2/WP3.3 messages unchanged,
   their tests still green). DR-38 (c) per question 6.
8. **EXCLUSIVE: whole-core speed row and memory re-check (question 7).** Speed: GX011627 full
   clip on the GPU, a 10-frame CPU subsample (WP3.1's ruled practice), both methods at the AD-8
   defaults: `render` at 4K with supplied statistics, `analyze` of every stage on the 540
   proxy, and the prototype `correct()` on the same frames (the gate's 0.639 / 0.395 s); GPU
   clocks, temperature and busy processes recorded; contaminated rows kept as spread. The bar is
   D106's interim figure: at 30000/1001 fps, 25 min/min is about 0.834 s per frame for the
   whole export; the row reports the core's share and its min/min. Memory: a counting allocator
   (as WP1.2A) on `render` and `analyze` at 4K and 5.3K 16:9 (5312 x 2988), both methods; the
   CuPy pool's used and reserved peaks and process RSS against `memory_estimate_bytes`. STOP
   with the figures if the product peak exceeds the estimate (AD-1's formula is not this
   package's to change) or the core alone exceeds the D106 per-frame budget.
9. **Tests.**
   - IF conformance: `isinstance(m, CorrectionMethod)` and mypy assignments as in `stubs.py`;
     c3's stages equal to `stubs.C3_STAGES`.
   - V1 staged ordering: each stage measured on the image corrected with the SUPPLIED earlier
     stages (a planted "earlier ignored" fails); `analyze` of a later stage refuses a missing
     earlier one.
   - Product against prototype (WP3.1 ruling 6 form, computed in the test, no committed
     arrays): `analyze`'s flat chain against `prototype.temporal.statistics_of`; `render`
     against `pipeline.correct` with the same `Statistics` hook record; bit-identical where the
     round-0 table says so, else AD-11 with the maximum reported. CPU against GPU within AD-11;
     same device twice bit-identical (N10).
   - V9 at method level: `Params.neutral()` values give the input within AD-11 V9 for both
     methods on every listed still (maximum and mean reported); blend 100 returns the input.
   - V8 at method level: `clearwater.gui.imaging.preview_export_difference` at k = 1, 2, 4 on
     the stills and on a synthetic 4K-sized texture: k = 1 exact; mean ≤ 1/255, max ≤ 3/255
     (a miss is a STOP with the figures).
   - Closed form equal to re-analysis; `render` on the GPU makes no host read; each measure
     path's host reads COUNTED per frame (DR-38 (a)); grey all-black / all-white inputs give
     weights `1/K` (DR-38 (b)); the DR-40 (a) test.
   - Schema: every default and neutral set valid; each bound refused by `validate_parameter_set`
     or by the method's check (question 4) with one ValueError naming the parameter; c3's schema
     has no cap (D49).
   - Planted wrong implementations fail by name: strength or clamp applied before smoothing
     (inside `analyze`'s stored gains); alpha re-derived from smoothed means (WP1.4b claim 10's
     B); the clamp skipped in `render`; blend direction inverted; `render` measuring a statistic;
     a stage measured on the uncorrected image; a schema default differing from AD-8; the cap
     present in c3's schema; and the DR-19 transcript's items that touch the schema.
   - Core: the DR-37 (a) reason under a planted `ImportError` that is not a
     `ModuleNotFoundError`; DR-38 (d) ValueError; DR-38 (c) if ruled.
   - Dependency rule (plan 8.1, frame rule 5): importing `clearwater.methods` loads nothing
     from `clearwater.io`, `.jobs`, `.gui`, `.config`, `.analysis`, nor `PIL`, `av`, `PySide6`,
     `cupy`.

## Declared operating envelope

Windows 11; Python 3.12; NumPy, SciPy and CuPy (`cupy-cuda12x[ctk]` 14.x) as locked; one NVIDIA
RTX 4070 Laptop GPU, 8 GB (D117); images from 1 x 1 to 4K frames and 48 MP photos; parameter
values inside the schema's ranges; statistics records as `analyze` or the WP3.11 store produce
them. Out of envelope: values the schema refuses, hand-made statistics records of other shapes
(refused, Y-2), non-NVIDIA devices, other operating systems (portable, N1, not run there),
multi-GPU (DR-2). The speed and memory figures are best effort on a shared laptop (frame rule
7, the owner's 2026-10-19 ruling).

## Review loop (Reviewer A), per `docs/review-gate-clearwater.md` Part 1

- Tier **STRONG**, run by you at your seat to convergence; five-round gate. Evidence
  `C:\Users\rwsmy\clearwater-review-evidence\wp3.4\rN\`; ledger `docs/proofs/wp3.4-ledger.md`.
  Copy the runner and prompt shape from `C:\Users\rwsmy\clearwater-review-evidence\wp3.1\r2\`
  (`run_review.sh`, `review-prompt.md`; the round also keeps `probe.txt`, `review-diff.txt`,
  `review.txt`, `adjudication.md`, `md5sums.txt`, `test-summary.txt` as there); the reviewer
  excludes `docs/proofs` with `--glob '!docs/proofs/**'`.
- **WHAT TO EXAMINE:**
  - each stage against AD-6 and 7.1's chain: what is measured on which image, with which
    earlier record; the stage tables against `stubs.C3_STAGES` and the dependencies complete
    (every parameter that changes a stage's statistics is in its `depends_on_parameters`);
  - `render` never measures; the D99 clamp and the strength applied after smoothing, to the
    gains used; blend direction and neutrality;
  - the schema against 6.7, D17, D49 and AD-8; the checks it cannot express; DR-19's items;
  - product against prototype and CPU against GPU, measured not asserted; V8, V9 figures;
  - the core fixes change nothing else (the reason list, the bound, the estimate);
  - the speed and memory rows: conditions recorded, contamination kept, the bar quoted right;
  - nothing outside the owned files and lines changed.
- Reviewer B is the orchestrator's seat pass on the merge candidate.

## Notes for the cell

- **Yields.** Round 0: read and table, then YIELD before product code. After each review
  round: END YOUR TURN as soon as round N's verdict is adjudicated, BEFORE remediating; make NO
  change in the turn that adjudicates a round. Report `scripts/cell_depth.py`'s reading at
  every yield (~250K evaluation point; past it, "REVIEW ONLY this turn"; ~400K STOP).
- **Windows.** Full pytest (about 3559 tests, about 15 min) runs ONLY in a window the
  dispatcher grants by message, in the background with `QT_QPA_PLATFORM=offscreen` and output
  to a file under `work/`; send `WINDOW RELEASED: <summary>` when it finishes. The EXCLUSIVE
  speed and memory runs are separate grants, one at a time (the dispatcher posts OPEN/CLOSE);
  never two heavy jobs at once; do not start one unasked. Inner loops run only your own tests.
- **Return report** = your FINAL message, under about 70 lines (`docs/dispatch-recipe.md`
  section 4): the stage tables, the schema table, the public API, prototype and CPU/GPU
  figures, V8 and V9 figures, the speed row and memory table against the bars, the debt
  dispositions, the gates, the Reviewer A rounds and verdict, open items.
- **STOP for:** any change needed in `src/clearwater/interfaces/` (AD-20), including c3's
  stages differing from `stubs.C3_STAGES`; a numeric change in WP3.2's or WP3.3's modules; a
  core change beyond the banked items and question 2; a tolerance looser than AD-11 or a V8/V9
  miss; the product memory peak above the estimate; the core alone above D106's per-frame
  budget; any dependency (frame section 4 grants none here); OS-specific code; a default that
  differs from AD-8; the round-0 table showing a choice the brief left open.
- **Working rules:** `uv sync`. Commit inside the worktree with `git -c core.autocrlf=false`,
  by pathspec, `feat(wp3.4): ...`, with a `Co-Authored-By:` footer naming your model. NEVER
  `git stash` (the stash stack is shared by every worktree; use a WIP commit or a scratch
  copy). Never a bare `cd`. Never post to a mailbox. Gates: ruff check, ruff format --check,
  mypy strict, full pytest with and without CuPy importable (in windows); no harness gate.
  Report `docs/reports/wp3.4-method-assembly.md` (claims, evidence paths, limits, a "DR-19
  rule" section, a "Schema" table and a "Consumer notes" section for WP3.11, WP3.17, WP3.14
  and WP3.21). Outputs of the instrument under `work/wp3.4/`. The footage folder is read only.
  No `gpmd`, IMU or GPS data.

## Rulings (CHARC `53d1d906e47fe2c9`, 2026-10-21)

Approved as drafted: every recommended answer below is the ruling, with these amendments and readings. Where a ruling here and the task ladder or a question differ, the ruling governs.

- **Q1 (Y-1) RULED as recommended**, and it is an IF-3 READING, not an amendment: `closed_form` is non-None only for the `source_only` compensation stage; WB `gains` are pre-strength/pre-clamp, applied in `render` after smoothing; Ancuti `alpha` is capped per frame and smoothed as a value. The report states it in ONE text identical to WP3.11's report.
- **Q2 granted:** `clearwater.core.backend_for(device)`, one additive public function; WP3.4 owns that one addition to `clearwater.core`, and WP3.1's tests are extended for it.
- **Q4:** DR-19 closes in WP3.4. **Q5 granted, type-only:** DR-37 (b) call-site edits in the WP3.2/WP3.3 modules.
- **Q6 per the register:** DR-38 (a)(b)(c) in WP3.4; DR-40 (b) to WP3.4's whole-core row or WP3.21.
- **Q7:** `tools/core_speed.py --whole --memory`, in an EXCLUSIVE window (OPEN/CLOSE posted; one at a time with WP3.10's). The bar is D106's interim figure; the real target is WP3.21's.
- **Q8:** DR-13 placement only.
- **Blend with original (WP3.4 and WP3.17):** the spec defines the control as 0-100 %. The SCHEMA value is the user-facing value: WP3.4 defines `blend_with_original` as a float 0..100, label "Blend with original (%)", neutral 0 (AD-8), and the method converts to 0-1 internally; presets store 0-100. No IF-3 unit field. WP3.17 shows the schema value with the label; nothing is special-cased.

## Questions for CHARC (recommended answer first)

1. **Y-1 (cross-brief, WP3.4 and WP3.11): the statistics contract.** IF-3 fixes the signatures,
   not what a record holds or who calls `closed_form`. Recommended (identical text in WP3.11's
   brief): (a) `analyze` returns every name of the stage's `Stage.statistics` for that frame,
   render-ready (as `clearwater.gui.imaging.measure_statistics` on main already relies on), as
   float64 host arrays of a fixed shape per name; (b) white balance `gains` are the gray-world
   gains BEFORE the strength and the D99 clamp (the prototype `Statistics.white_balance_gains`;
   WP3.2 consumer note "`applied_gains` takes the smoothed gray-world gains"); strength and clamp
   are applied inside `render` and inside later stages' `analyze`, after smoothing (AD-6), which
   is why the frozen `C3_STAGES` lists them only under `fusion`; (c) Ancuti `alpha` is the
   capped alpha per frame, smoothed as a value (AD-6, WP1.4b claim 10); (d) `closed_form`
   returns the full record with every parameter-dependent name recomputed from the measured
   names, or None when the stage's measurement depends on parameters or earlier stages: in v1
   non-None only for Ancuti `compensation`; (e) Ancuti `compensation` is the only `source_only`
   stage; the engine caches the record `analyze` returned and never uses a cached record without
   passing it through `closed_form` with the current parameters. Alternative for (e), if D113
   ("the cache holds only results that depend on the source file alone") is read strictly
   against a cached alpha: an AD-20 amendment adding a `Stage` field naming the measured
   (cacheable) statistics.
2. **Which backend `analyze` and `render` use.** IF-3 passes an `Image` (with `device`), not a
   backend; `clearwater.core` has no public device-to-backend function (`_NUMPY_BACKEND` and
   `_probe_gpu()` are private). Recommended: a core function `backend_for(device: str) ->
   CoreBackend` (the process's `NumpyBackend` for `"cpu"`, the probed `CupyBackend` for its
   `cuda:<n>`, ValueError otherwise), exported from `clearwater.core`; the methods refuse an
   image whose pixels are not that backend's arrays. Alternative: the method infers the backend
   from the array type (string checks on the type's module; fragile).
3. **Registry and ids.** Recommended: `clearwater.methods.available_methods() -> dict[str,
   CorrectionMethod]` with `"c3"` first (D16; `gui.contract.Engines.methods`: "the first entry is
   the default method"), new instances per call; ids exactly `"c3"` and `"ancuti2018"`
   (architecture: "two `CorrectionMethod` instances"); "ancuti2018-blue" is `ancuti2018` with
   `blue_compensation=True`, not an id (the WP3.2 brief's three-name list reads that way); 6.7's
   "Compensation method" is the method choice (IF-9 `ParameterSet.method`), never a `Parameter`.
4. **Ranges and the checks the schema cannot say (DR-19).** IF-9 checks inclusive bounds only,
   and WP3.17's sliders need finite ones. Recommended: every float and int parameter gets a
   finite minimum and maximum, proposed in the round-0 table and ruled by the dispatcher (a
   positive minimum where the prototype requires `> 0`; `max_white_balance_gain` minimum 1.0;
   caps `nullable`, minimum 0; `blend_with_original` 0 to 100 (AMENDED by the rulings; the method converts to 0-1), the percent display
   being WP3.17's); what bounds cannot express (`normalisation_low < normalisation_high`, the
   float32-range products the prototype checks) is checked by the method at the start of
   `analyze` and `render`, one ValueError naming the parameter in the X-4 form. The rule text of
   X-4 goes into the report word for word; DR-19 closes at this accept.
5. **DR-37 (b): the helpers' typing.** Recommended: annotate the `clearwater.core.ops` helpers'
   backend as `CoreBackend` (the truth), and change the call sites in `compensation.py`,
   `white_balance.py` and `fusion.py` to pass the narrowed backend (type-only lines; the
   prototype-agreement tests re-run). Alternative: keep `ArrayBackend` and document the
   TypeError under "Raises".
6. **Scope of the other banked items.** Recommended: DR-38 (c) fixed here in the same core
   touch (`check_rgb` refuses an empty spatial size, as `check_spatial` already does); DR-40 (b)
   recorded by the speed row and left to WP3.21 (the gen-7 consumer note names WP3.21; the
   register allows either); DR-38 (a) and (b) as tests here (the register names this brief).
7. **The speed and memory instrument.** Frame section 3 places exclusive timing in WP3.1's and
   WP3.10's reports; the commission gives WP3.4 the whole-core row. Recommended: extend
   `tools/core_speed.py` (owned X1-style; closes DR-37 (d) `IndexError` and (e) the first
   `nvidia-smi` row, by selecting the CuPy device's row) with a `--whole` mode for task 8's
   rows and a `--memory` leg; outputs under `work/wp3.4/`; the bar quoted from D106 as task 8
   states. Alternative: a new `tools/method_speed.py`.
8. **DR-13.** Recommended: placement only (Advanced, 0.001); DR-13 stays OPEN for CHARC to
   close or keep at the accept (the look check passed at the defaults, CP2).
9. **Y-2 (cross-brief, WP3.4 and WP3.11): validating supplied records (DR-25 (2), (5)).**
   Recommended: `render` and `analyze` refuse a supplied record that lacks a declared name,
   carries an unexpected one, or holds a wrong shape or a non-finite value, with one ValueError
   naming the stage and statistic; the WP3.11 store checks the same at `put` (its own side).
