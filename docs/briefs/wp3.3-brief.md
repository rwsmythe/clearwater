# WP3.3 — Fusion inputs, weights and blending (dispatch brief, FINAL)

**Status:** FINAL 2026-10-20, approved by CHARC 53b752a4d7fac4fc with rulings; base = the pre-dispatch main commit named at dispatch. Drafted by the
orchestrator (gen 6, drafting helper). Owner decisions: none inside the package (the N{} floor's
form is ruled, AD-4 as amended 2026-10-20; a higher floor would be a look decision, WP1.4b claim
9).
- Spec **v0.5.4**. Architecture FINAL 1.0 section 3 IF-2 and IF-3, section 4; AD-1, AD-4 (as amended 2026-10-20), AD-6,
  AD-8, AD-11, AD-20. Frame `docs/briefs/wp2.4-phase3-frame.md` (sections 1-5; section 5 maps
  "6.3 defaults" to WP3.2, WP3.3, WP3.4). WP3.1 report `docs/reports/wp3.1-array-backend.md`
  ("Conventions fixed here", "Consumer notes"). DR-14 (closes), DR-13, DR-19, DR-37 (b) (row "Debt and decided items").
- Cell: `implementer-opus-high`. Tier **STRONG**.
- Worktree `.worktrees/wp3.3`, branch `wp3.3`, base = the main commit named at dispatch.

**Why.** Plan 11.1's critical path runs WP3.1 → WP3.2 and WP3.3 → WP3.4. Spec 6.2 steps 3-5
are shared by both IF-3 methods (`c3` and `ancuti2018` "sharing the fusion code", architecture
section 3); they are most of the per-frame cost (gate report Result 1) and carry the two
whole-frame statistics of the last stage (N{} bounds and saliency means, AD-6). This package
builds them on the merged `clearwater.core` backend with `tools/prototype/pipeline.py` as the
numerical reference (DR-19) and closes DR-14 with AD-4's floor.

| Field | Content |
|---|---|
| ID and title | WP3.3 — Fusion inputs, weights and blending; plan Phase 3 row WP3.3 (size M); module `clearwater.methods` (plan 8.1, built by WP3.2–WP3.4) |
| Goal | Step functions on an IF-2 backend for the gamma input, the sharpened input with its normalisation N{} (AD-4, with the 0.02 floor), the Laplacian, saliency and saturation weights with the paper's regularisation, and the multiscale Laplacian-pyramid blend; the two whole-frame statistics measured by their own functions and supplied to the render; bit-identical to the prototype on the same device or within AD-11, with the measured maximum reported. |
| Spec / decision clauses | 6.2 step 3 "**Derive two fusion inputs** from the white-balanced image: Input 1: gamma-corrected version. Input 2: sharpened version, `S = (I + N{I − G∗I}) / 2`, where N{} is a linear normalization (histogram stretch) whose bounds are whole-frame statistics (Section 7)." Step 4 "**Compute weight maps** for each input: Laplacian contrast, saliency (Achanta et al.), and saturation. Normalize across inputs with the paper's regularization, `W̄k = (Wk + δ) / (ΣWk + K·δ)`, δ = 0.1, K = 2." Step 5 "**Multiscale fusion** — Laplacian pyramid of inputs blended with Gaussian pyramid of weights, then collapsed." 6.1 "The formulas in the reference papers are authoritative over the summaries below. Where a paper leaves a value unspecified (e.g., the gamma for fusion input 1), the chosen default is documented in the design." 6.6 "All spatial parameters (sharpening blur, Laplacian, saliency blur, 3C kernels and mask smoothing) are expressed as a fraction of the image's short side (D56)"; "Pyramid depth is set by a minimum coarsest-level size rather than a fixed count; the Advanced "pyramid" control adjusts that size." D39 "Internal processing in 32-bit float; quantization only at export"; D56 "All spatial parameters size-relative (fraction of short side); pyramid depth set by minimum level size"; D57 "*(amended by D97)* All whole-frame statistics (incl. sharpening normalization, saliency reference) are analyzed and smoothed, in dependency order"; D107 "Core is written so the same code runs on CPU or GPU from the start". Feeds V1 "unit tests for each stage (... normalization, weights, pyramid fusion ...), including edge cases: uniform images, near-zero red channel, 10-bit input" and V9 "with every stage set to its neutral value (... sharpening 0, gamma 1 ...) each stage reduces to identity". AD-4 "Normalisation bounds N{}: 0.5 and 99.5 percentiles of the high-pass, taken jointly over channels, with a floor of 0.02 on the range (collapse guard, DR-14)", "Measured on the analysis proxy (AD-5) and used unchanged for preview and export, so V8 (preview = export) holds by construction". AD-6 (last stage: "N{} bounds and the two saliency Lab means"). AD-8 defaults: gamma 1.5, sharpen blur 0.005, Laplacian 0.001, saliency blur 0.003, delta 0.1, pyramid min level 16 px, N{} floor 0.02. |
| Depends on | WP3.1 merged (accept `f4acbd0`: `clearwater.core` on main; no stub needed). WP2.2 (IF-1, IF-2, IF-3 frozen, `b288533`). WP2.3 stills: `png16-uniform-none`, `png16-gradient-none`, `png16-lowred-none`, `png8-uniform-none`, `png8-gradient-none`, `png8-lowred-none`. Runs in parallel with WP3.2; its input is "the white-balanced image", which tests build with the prototype's `white_balance` or take as a still directly; no WP3.2 code is needed. `src/clearwater/methods/__init__.py` (docstring only) exists at the base (ruling X-2). |
| Files owned | `src/clearwater/methods/fusion.py` (NEW); `tests/test_methods_fusion*.py` (NEW); `docs/reports/wp3.3-fusion.md`; `docs/proofs/wp3.3-ledger.md`. NOT owned: `src/clearwater/methods/__init__.py` (orchestrator, then WP3.4; ruling X-2), `compensation.py` and `white_balance.py` (WP3.2), `ancuti_fusion.py` (WP3.4), `src/clearwater/core/` (WP3.1; read only), `src/clearwater/interfaces/`, `tools/prototype/`, `pyproject.toml`, `tests/conftest.py`, `tests/fixture_plugin.py`. |
| Interfaces provided | No frozen interface. The step functions of X-1 (names and signatures tabled at round 0 for CHARC; WP3.4 builds on them). |
| Interfaces consumed | IF-1 `Array`; IF-2 `ArrayBackend` methods `asarray`, `to_host`, `gaussian_blur`, `percentile` (R-7, `q` in 0-100, over the whole array: AD-4's joint bounds); `clearwater.core` helpers `spatial_sigma`, `pyramid_levels`, `gaussian_pyramid`, `laplacian_pyramid`, `collapse_pyramid`, `luminance`, `rgb_to_lab`, `laplacian`, `channel_means`, `check_sigma`. The helpers require a `clearwater.core` backend (`CoreBackend`; DR-37 b): tests use `NumpyBackend` / `CupyBackend`, never a protocol-only double. `channel_means` returns Python floats (a sync point); `percentile` returns a float32 array on the device ("R-7 in float64, cast once", WP3.1 report claim 5), so reading the bounds as floats is a further sync point to list. `CoreBackend.xp` is NOT available outside `clearwater.core` (WP3.1 ruling 1.1). |
| Consumers | WP3.4 (wave 3), which owns the `Parameter` schema and its range validation, the stage and statistic names (the frozen `stubs.C3_STAGES` names `"bounds"`, `"saliency_means"`), the order of measurement inside the fusion stage (the saliency mean of input 2 depends on that frame's N{} bounds), smoothing, "blend with original" (plan WP3.4), the method-level V9 test, the product memory-peak re-check and the whole-core speed row. WP3.3 owns the per-step numerics and the measure / render split. WP3.21 (optimisation; FFT or recursive Gaussian) later replaces kernels, not these functions' contracts. |
| Hardware flags | `gpu` on every CuPy test. No footage, no timing. |
| Out of scope | Compensation and white balance (WP3.2); the IF-3 method objects, schema, stages, smoothing and "blend with original" (WP3.4); any change to `clearwater.core` (X-3); a weight-map smoothing or caching scheme (spec 7.4 is conditional scope, not v1 here); any optimisation candidate of the gate report (WP3.21); importing `tools/prototype` from `src/`; GoPro IMU/GPS (owner: out of scope). |
| Debt and decided items | **DR-14 (OPEN) — CLOSES:** the ill-conditioned N{} stretch gets AD-4's floor of 0.02 on the range (AD-4: bounds "Measured on the analysis proxy (AD-5)", the 540-line proxy; the value from WP1.4b claim 9, binding on none of the measured ranges 0.028-0.64), applied by widening the bounds symmetrically about their midpoint to a range of 0.02, never by a plain max on the range, so a flat image keeps the prototype's 0.5 (AD-4 as amended 2026-10-20; ruling 3.1); DR-14 CLOSES on WP3.3's accept. **WP3.1 round-0 ruling R0-8 (percentile float32 out) — carried, not a defect:** `percentile` is computed at native precision (float64) and cast once to float32 (`docs/proofs/wp3.1-ledger.md` R0-8, "Consequence flagged for WP3.3"; WP3.1 report claim 5), so the bounds and input 2 agree with the prototype within AD-11, not bit for bit; the report states the measured maximum. **DR-13 (OPEN) — must not reopen, not closed here:** DR-13 reads "At `laplacian_fraction` 0.001 the Laplacian contrast weight is about 1% of the aggregated weight on textured content (saliency ~0.08, saturation ~0.19), so the contrast term is nearly inert at the defaults", with the trigger "calibrate `laplacian_fraction` or the weight normalisation on real footage". `laplacian_fraction` (default 0.001, AD-8) is that calibration knob and stays a parameter with that default and the scale-normalised form, the calibration knob the owner can see through the parameter set (whether it is exposed in a panel is WP3.4's schema; spec 6.7's Advanced list does not name it); no recalibration in this package; the report quotes DR-13 and the measured weight share on one still. **DR-19 (OPEN) — PARTLY DISCHARGES, for this package's parameters only:** items (1) and (2) under the shared rule X-4 (also carried by WP3.2), stated in the report; item (3) does not recur (`check_sigma` bounds the integer radius); item (4) is held by the core's input checks (R0-3) and R0-8; item (5) by the planted-defect tests that concern fusion. DR-19 stays OPEN until WP3.4's schema lands. **DR-37 (b) — must not reopen:** the core helpers take a `CoreBackend`; no protocol-only double. |
| Done | Plan 4.5; frame section 2 rules 1-11; ruff check, ruff format --check, mypy strict, full pytest green with and without CuPy importable (in a granted window, X5); prototype agreement measured per function; DR-14's floor in and tested; V1 and V9 items covered; the X-4 rule stated in the report with its tests; Reviewer A converged. |

## Task ladder

1. **Read and table (round 0 yield).** Read IF-2, `clearwater.core` (`ops.py`, the WP3.1
   report's conventions and consumer notes) and the prototype functions this package mirrors:
   `fusion_inputs`, `normalisation_bounds`, `high_pass_of`, `_high_pass_and_bounds`,
   `saliency_reference`, `weight_maps`, `_laplacian_weight`, `_saliency_weight`,
   `_saturation_weight`, `_lab_mean`, `multiscale_fusion`. Write in the ledger: each product
   function (X-1), its prototype counterpart, measure or render, every prototype `xp.` call and
   its replacement (X-3), the floor as ruled (ruling 3.1), and whether bit identity is expected
   on each device. YIELD before product code. Anything the table cannot settle is a STOP.
2. **Fusion inputs (step 3).** Input 1 `I ** gamma` (float32 exponent). Input 2: the high-pass
   `I - G*I` (`sharpen_blur_fraction` through `spatial_sigma`); the bounds are supplied, never
   measured here; when `high - low < 0.02` the bounds are widened symmetrically about their
   midpoint to `mid -/+ 0.01` (AD-4 as amended; a module constant, applied to the supplied
   bounds); the stretch `clip((hp - low) / (high - low), 0, 1)`; `S = (I + stretched) / 2`; `sharpen_strength` s gives
   `clip(I + s * (S - I), 0, 1)`. Both clipped to [0, 1].
3. **Measured statistics.** N{} bounds: the `normalisation_low` / `normalisation_high`
   percentiles of the high-pass over all pixels and channels (AD-4) through IF-2 `percentile`.
   The saliency reference of each input: its mean Lab vector (`rgb_to_lab`, float64-accumulated
   mean, as the prototype's `_lab_mean`).
4. **Weights (step 4).** Per input: W_L = `|sigma^2 * laplacian(G_sigma * luma)|` with sigma =
   `laplacian_fraction` of the short side, the prototype's documented, deliberate adaptation of
   [A18]'s pixel-scale Laplacian to D56 (kept as is; the report names it); W_S = the Euclidean
   distance in Lab between the supplied mean and the Lab image blurred by
   `saliency_blur_fraction`, divided by 100; W_Sat = the RMS deviation of R, G, B from the
   BT.709 luma. `W_k = W_L + W_S + W_Sat`; `W̄_k = (W_k + delta) / (sum_k W_k + K * delta)`,
   K = the number of inputs (2).
5. **Multiscale blend (step 5).** Depth from `pyramid_levels(shape, pyramid_min_level_size)`;
   Laplacian pyramid of each input, Gaussian pyramid of its weight; `R_l = sum_k G_l{W̄_k} *
   L_l{I_k}`; collapse; clip to [0, 1].
6. **Tests.**
   - Product against prototype (architecture section 4, WP3.1 ruling 6 form: the read-only prototype called in
     the test on seeded synthetic inputs and the WP2.3 stills; no committed arrays): each
     function alone, the render through the prototype's `Statistics` hook
     (`normalisation_bounds`, `saliency_means`) with the same supplied values; bit-identical
     where the round-0 table says so, else within AD-11 with the maximum reported. Input 2 is
     expected within AD-11, not bit for bit: the bounds are float32 (WP3.1 consumer note) where
     the prototype carries float64 Python floats.
   - The floor: a near-flat input (range below 0.02) and an exactly flat input (range 0) give
     the ruled result (0.5 for the flat input, the midpoint-widened stretch for the near-flat one); a
     range of 0.02 or more is untouched by the floor (equal to the
     prototype); DR-14's amplification case (WP1.2A F1, range 0.0018) stays bounded.
   - CPU against GPU within AD-11 (max 2e-3 absolute per channel, mean 2e-4); same device twice
     bit-identical (N10). Name the inputs where the stretch amplifies the CPU/GPU gap (DR-14) and
     show the floor keeps it inside AD-11.
   - V1 edge cases: uniform image, near-zero red, 1 x 1 and odd sizes (pyramid depth 1), sizes
     where the pyramid depth changes, 16-bit-derived values.
   - V9 neutrality: `gamma = 1` and `sharpen_strength = 0` give input 1 and input 2 equal to the
     input bit for bit; fusing two identical inputs returns the input within AD-11's V9 bound
     (max 2/255, mean 0.2/255), the measured figure reported.
   - Weights sum to 1 at every pixel within float32 round-off; delta and K as the spec says.
   - DR-19 under X-4: an unusable derived sigma (`sharpen_blur_fraction`, `laplacian_fraction`,
     `saliency_blur_fraction` at the given image size) raises one ValueError whose message
     names the parameter; no fusion step validates a compensation parameter.
   - DR-13 record (not a pass/fail gate): the share of W_L in the aggregated weight at the
     default `laplacian_fraction` on `png16-gradient-none` and a textured synthetic input, in
     the report beside DR-13's figure.
   - Planted wrong implementations fail by name: N{} per channel instead of joint; bounds
     measured inside the render; no floor; the floor as a plain max on the range (a flat
     image then gives 0, not 0.5); delta added to the numerator only; K fixed at 1; weights not pyramided (applied at
     full resolution only); a fixed pyramid depth; saliency against the unblurred Lab image; a
     float64 leak.
   - Gate 1 discipline (as WP3.1's Gate 1 section): on the GPU every function returning an
     array returns a `cupy.ndarray`; the only device-to-host reads are the documented sync
     points (`channel_means`, reading the bounds).
   - Dependency rule (plan 8.1, frame rule 5): a subprocess test that importing your module loads
     nothing from `clearwater.io`, `.jobs`, `.gui`, `.config`, nor `PIL`, `av`, `PySide6`, `cupy`.

## Declared operating envelope

Windows 11; Python 3.12; NumPy, SciPy and CuPy (`cupy-cuda12x[ctk]` 14.x) as locked; one NVIDIA
RTX 4070 Laptop GPU, 8 GB (D117); images from 1 x 1 to 4K frames and 48 MP photos; parameter
values inside the ranges WP3.4's schema will set (the AD-8 defaults and the V9 neutral set
exercised); bounds supplied with `low <= high` and finite (the prototype's `check_statistics`
rule; who enforces it is question 2). Out of envelope: values a schema would refuse (range
validation is WP3.4's schema, derived values are X-4's), non-NVIDIA devices, other operating systems (portable, N1, not run there), multi-GPU
(DR-2).

## Review loop (Reviewer A), per `docs/review-gate-clearwater.md` Part 1

- Tier **STRONG**, run by you at your seat to convergence; five-round gate. Evidence
  `C:\Users\rwsmy\clearwater-review-evidence\wp3.3\rN\`; ledger `docs/proofs/wp3.3-ledger.md`.
  Copy the runner and prompt shape from `C:\Users\rwsmy\clearwater-review-evidence\wp3.1\r2\`
  (`run_review.sh`, `review-prompt.md`; the round also keeps `review-diff.txt`, `review.txt`,
  `adjudication.md`, `md5sums.txt` as there); the reviewer excludes `docs/proofs` with
  `--glob '!docs/proofs/**'`.
- **WHAT TO EXAMINE:**
  - each formula against spec 6.2 steps 3-5, [A18] where the spec defers to it (6.1), and the
    prototype;
  - N{} joint over channels, from supplied bounds only, with the floor widened about the
    midpoint (AD-4 as amended);
  - the regularisation `(W_k + delta) / (sum W_k + K delta)` with K the input count;
  - pyramid depth from the minimum level size (6.6, D56); every spatial sigma through
    `spatial_sigma`;
  - float32 image data; no silent float64 result; no host round trip beyond the sync points;
  - product against prototype and CPU against GPU, measured not asserted; the input-2
    deviation explained by the float32 bounds, not by something else;
  - render never measures a whole-frame value (AD-4: preview = export by construction);
  - nothing outside the owned files changed.
- Reviewer B is the orchestrator's seat pass on the merge candidate.

## Notes for the cell

- **Yields.** Round 0: read and table, then YIELD before product code. After each review
  round: END YOUR TURN as soon as round N's verdict is adjudicated, BEFORE remediating. Yield
  at every round boundary; the dispatcher reads your depth (~250K evaluation point, ~400K
  stop).
- **Full-pytest windows (X5).** The full suite (about 1844 tests, 9-11 min) runs ONLY in a
  window the dispatcher grants by message, in the background with output to a file under
  `work/`; send `WINDOW RELEASED: <summary>` when it finishes and carry on. Inner loops run only
  your own tests.
- **Return report** = your FINAL message, under about 70 lines (`docs/dispatch-recipe.md`
  section 4): the function table (name, signature, measure or render, prototype identity or
  measured deviation per device), the floor and its tests, the AD-11 and V9 figures, the
  gates, the Reviewer A rounds and verdict, open items (DR-14's closure evidence).
- **STOP for:** any change needed in `src/clearwater/interfaces/` (AD-20) or in
  `clearwater.core` (X-3); a tolerance looser than AD-11; any dependency; OS-specific code; a
  prototype numeric that disagrees with the spec; a default or name X-1 leaves to WP3.4; the
  round-0 table showing a choice the brief left open.
- **Working rules:** `uv sync`. Commit by pathspec, `feat(wp3.3): ...` (conventional commits
  carrying the WP id), with a `Co-Authored-By:` footer naming your model. Never a bare `cd`.
  Never post to a mailbox. Gates: ruff check, ruff format --check, mypy strict, full pytest (in
  a window); no harness gate. Report `docs/reports/wp3.3-fusion.md` (claims, evidence paths,
  limits, a "DR-19 rule" section stating X-4 as ruled, word for word the same as WP3.2's, and
  the DR-13 record). DR-19 item (5)'s list is in the WP1.2R Reviewer B transcript `C:\Users\rwsmy\clearwater-review-evidence\prototype-retroB\rerun\review-B.txt`
  (md5 `f1cc6cf8ae3da62a1b3765573320e7b7`, as recorded in `docs/proofs/wp1.2r-accept.md`): read its
  wrong-implementation list and cover the ones that touch your steps. GoPro IMU/GPS data is out of scope everywhere.

## Rulings (CHARC `53b752a4d7fac4fc`, 2026-10-20)

CHARC `53b752a4d7fac4fc`, 2026-10-20: every recommended answer is the ruling unless amended here.
- **3.1 (floor form):** widen the bounds symmetrically about their midpoint to a range of 0.02
  (AD-4 as amended 2026-10-20); DR-14 CLOSES on WP3.3's accept.
Cross-brief rulings:
- **X-2:** the orchestrator commits a docstring-only `src/clearwater/methods/__init__.py` on main
  before dispatch (it exists at the base); WP3.4 owns it afterwards; WP3.2 and WP3.3 do not edit
  it.
- **X-4 (DR-19 rule):** as drafted; DR-19 stays OPEN until WP3.4.
- CHARC accepted the drafter's corrections to its debt list (`laplacian_fraction` panel placement
  is WP3.4's schema; WP3.7 ruling 7.3 is the `yuvj` citation); no line here changes.

### Questions as drafted (recommended answer = ruling unless amended above)

1. **The form of AD-4's floor (DR-14).** AD-4 says "a floor of 0.02 on the range"; the prototype
   has none (its rule is `high - low < 1e-6` → N{} = 0.5 everywhere), and WP1.4b claim 9
   proposed the value, not the form. A plain `range = max(high - low, 0.02)` with `low` kept
   makes an exactly flat image stretch to 0, so input 2 becomes `I / 2` at sharpening 1, where
   the prototype gives `(I + 0.5) / 2`. Recommended: widen the bounds symmetrically about their
   midpoint when `high - low < 0.02` (`low' = mid - 0.01`, `high' = mid + 0.01`). It is
   continuous with the prototype's flat rule (a flat image still gives 0.5), binds on none of
   the measured frames (ranges 0.028-0.64, WP1.4b claim 9), so the product equals the
   prototype on all of them, and it retires the 1e-6 rule. The floor is a module constant (spec
   6.7 lists no control for it), applied in the render to the supplied bounds, so preview and
   export apply it identically. DR-14 is recorded CLOSED at the accept.
2. **X-1 (cross-brief, WP3.2 and WP3.3): the step-function signatures and the WP3.4
   boundary.** As WP3.2 question 1: backend first, array second, keyword-only parameters
   without defaults, names equal to the prototype `Params` fields (`gamma`, `sharpen_strength`,
   `sharpen_blur_fraction`, `normalisation_low`, `normalisation_high`, `laplacian_fraction`,
   `saliency_blur_fraction`, `weight_delta`, `pyramid_min_level_size`), measure and render
   split. For WP3.3, for example: `high_pass(backend, a, *, sharpen_blur_fraction)`,
   `normalisation_bounds(backend, a, *, sharpen_blur_fraction, normalisation_low,
   normalisation_high)` (two Python floats), `fusion_inputs(backend, a, *, gamma,
   sharpen_strength, sharpen_blur_fraction, bounds)`, `saliency_reference(backend, a)` (three
   Python floats), `laplacian_weight`, `saliency_weight`, `saturation_weight` (public, so tests
   compare each to the prototype), `weight_maps(backend, inputs, *, laplacian_fraction,
   saliency_blur_fraction, weight_delta, saliency_means)` (the normalised maps), and
   `multiscale_fusion(backend, inputs, weights, *, pyramid_min_level_size)`. Supplied
   statistics are required arguments (no measure-inside fallback). The finite / `low <= high`
   check on supplied bounds is a cheap guard kept in `fusion_inputs` (a ValueError naming the
   field); range validation of a parameter's own value is WP3.4's (the schema); derived values
   are X-4's.
3. **X-2 (cross-brief): who creates `src/clearwater/methods/__init__.py`.** As WP3.2 question 2:
   the orchestrator commits a docstring-only file on main before dispatch; WP3.4 owns it later.
4. **X-3 (cross-brief): elementwise operations without `xp`.** As WP3.2 question 3: array
   methods and operators, each substitution tabled; bit identity only where the substitute is
   the same operation, AD-11 elsewhere with the maximum reported; an operation that cannot be
   written so is a STOP. WP3.3 is the package where this bites: the prototype calls
   `xp.sqrt` (saliency, saturation), `xp.power` (input 1), `xp.full_like` (the weight
   denominator, which `(K * delta + W_0) + W_1` reproduces in the same order) and `xp.abs`
   (the builtin `abs` is the same ufunc). Recommended in addition: if `** 0.5` differs from
   `sqrt` on CuPy, accept the AD-11 deviation rather than add a core helper now; WP3.4 or
   WP3.21, which touch `clearwater.core` next (DR-37's trigger), may add elementwise helpers.
5. **X-4 (cross-brief, WP3.2 and WP3.3): the one shared DR-19 rule.** As WP3.2 question 4,
   word for word in both reports: each step validates only the values it derives from its own
   parameters and the image size (here the three fusion sigmas), before any array work, so
   validation is method-scoped by construction; a failure is ONE `ValueError` naming the
   parameter, its value and the short side (the prototype's wording), with no output before
   it; the support bound is `clearwater.core.check_sigma`'s, re-raised with the parameter
   named, never restated; a parameter's own range is the schema's (WP3.4).
6. **Returned weight records.** The prototype returns a `Weights` record (raw, aggregated and
   normalised maps). Recommended: `weight_maps` returns the normalised maps only (what the blend
   consumes, and what holds device memory for a 4K frame); the three raw weights stay testable
   through their public functions.
