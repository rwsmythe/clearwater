# WP3.3 -- Fusion inputs, weights and blending (report)

Brief `docs/briefs/wp3.3-brief.md` (FINAL, CHARC rulings `53b752a4d7fac4fc`); round-0 table
`docs/proofs/wp3.3-ledger.md` accepted by the orchestrator (generation 6), all five questions as
recommended. Branch `wp3.3`, base `2c5540a`. Stack as locked: NumPy 2.5.4, SciPy 1.18.1, CuPy
14.2.0.

## What was built

| Path | Content |
|---|---|
| `src/clearwater/methods/fusion.py` | the nine step functions below and `NORMALISATION_RANGE_FLOOR = 0.02` |
| `tests/test_methods_fusion_prototype.py` | every function against the read-only prototype on both devices; the measured path; CPU against GPU; DR-14's gap |
| `tests/test_methods_fusion.py` | the floor, supplied-statistic guards, input checks, X-1 signatures, V1, V9, the regularisation, X-4, planted wrong implementations, Gate 1, the dependency rule |

| Function (X-1 form) | Measure / render | Against the prototype (same supplied statistics) |
|---|---|---|
| `high_pass(backend, a, *, sharpen_blur_fraction)` | shared | bit-identical, CPU and GPU |
| `normalisation_bounds(backend, a, *, sharpen_blur_fraction, normalisation_low, normalisation_high) -> (float, float)` | MEASURE, sync point | = the prototype's float64 bounds rounded to float32, exactly (R0-8) |
| `fusion_inputs(backend, a, *, gamma, sharpen_strength, sharpen_blur_fraction, bounds) -> (input1, input2)` | RENDER | input 1 bit-identical; input 2 bit-identical to the prototype given the floored bounds, so to the prototype itself when the range is at least 0.02 |
| `saliency_reference(backend, a) -> (L, a, b)` | MEASURE, sync point | equal (float32-rounded float64 means) |
| `laplacian_weight(backend, a, *, laplacian_fraction)` | render | bit-identical |
| `saliency_weight(backend, a, *, saliency_blur_fraction, saliency_mean)` | render | bit-identical |
| `saturation_weight(backend, a)` | render | bit-identical |
| `weight_maps(backend, inputs, *, laplacian_fraction, saliency_blur_fraction, weight_delta, saliency_means) -> tuple` | render | normalised maps bit-identical |
| `multiscale_fusion(backend, inputs, weights, *, pyramid_min_level_size)` | render | bit-identical |

## Claims and evidence

1. **Prototype agreement per function** (`tests/test_methods_fusion_prototype.py`, 193 tests
   with the GPU): on two seeded noise images (one with near-zero red), a textured scene, the
   same scene white-balanced by the prototype's 3C and white balance, and the six WP2.3 stills
   (`png16-`/`png8-` `uniform`, `gradient`, `lowred` `-none`), at the AD-8 defaults and at a
   "wide" set whose sigmas span pixels at these sizes, every function is bit-identical to the
   prototype on its own device as tabled. The measure-then-render chain against the prototype's
   self-measuring path: within AD-11 on a 192 x 288 scene (test), and **0 difference** on a 4K
   white-balanced synthetic frame on both devices (input 1, input 2 and the fused image;
   `C:\Users\rwsmy\clearwater-review-evidence\wp3.3\measure\measure.txt`). The float32 bounds
   can change the stretch's divisor `high - low` by one float32 ulp (a probe with arbitrary
   bounds: 2.4e-7 on N{}); on that frame they did not.
2. **CPU against GPU within AD-11**, 4K white-balanced synthetic, each device measuring its own
   statistics (`measure.txt`): high-pass max 5.4e-7 / mean 5.4e-8; input 1 6.0e-8 / 1.8e-9;
   input 2 3.0e-6 / 4.3e-7; W_L 4.5e-6 / 3.9e-7; W_S 2.7e-7 / 2.7e-8; W_Sat 8.2e-8 / 4.3e-9;
   normalised weight 9.2e-6 / 8.7e-7; fused 1.7e-6 / 2.4e-7. The bounds differ by 6e-8 and
   9e-8; the saliency means by at most 4e-5 (L*). Pinned by `test_cpu_against_gpu_within_ad11`
   (noise, scene, near-flat; both parameter sets). Same device twice: bit-identical
   (`test_same_device_twice_bit_identical`).
3. **The floor (AD-4 as amended, ruling 3.1)**, in `fusion_inputs` on the supplied bounds:
   `high - low < 0.02` gives `mid -/+ 0.01`. Exactly flat input: 0.5, bit for bit on the CPU;
   on the GPU the cupyx blur leaves a high-pass of +/- 1 ulp, so input 2 lies within 1.5e-6 of
   `(I + 0.5) / 2` (`test_floor_flat_image` holds it within 1e-5). Near-flat (range 0.0017): the midpoint-widened stretch against a
   float64 formula within 2e-6 (`test_floor_near_flat_image`). Ranges of 0.02 or more:
   bit-identical to the prototype (`test_floor_leaves_wide_bounds_alone`).
4. **DR-14 closure evidence.** On WP1.1's near-flat synthetic (64 x 96, N{} range 0.0017, the
   WP1.2A F1 case) a perturbation of the input is amplified at most 50x into N{} (the
   prototype: over 400x; `test_floor_bounds_dr14_amplification`), and the input-2 CPU/GPU gap
   falls from 3.5e-5 / 8.5e-6 (prototype) to 3.0e-6 / 7.3e-7 (`test_floor_bounds_the_dr14_gap`,
   `measure.txt`). On such a frame the floor changes input 2 by design (against the prototype:
   max 0.23, mean 0.07); it binds on none of the measured real-footage ranges (0.028-0.64,
   WP1.4b claim 9), so the product equals the prototype there.
5. **V1 edge cases** (`test_v1_edge_cases`, both devices, both parameter sets): uniform, near-zero
   red, 16-bit- and 10-bit-quantised values at 1 x 1, 1 x 7, 5 x 1, 2 x 3, 30 x 45 (depth 1),
   31 x 45 (depth 2), 33 x 47 and 64 x 96: float32, finite, in [0, 1], shape kept; a uniform
   input fuses to a uniform output within 1e-6. The blend equals the prototype across the depth
   steps at 31 and 61 px (`test_fusion_across_depth_changes_matches_prototype`).
6. **V9.** `gamma = 1` and `sharpen_strength = 0` return input 1 and input 2 equal to the input
   bit for bit, flat or not (`test_v9_neutral_inputs_are_identity`). Fusing two identical inputs
   returns the input within V9's bound (max 2/255, mean 0.2/255) in the test; measured **0**
   (bit-identical) on the 4K frame on both devices (`measure.txt`).
7. **Regularisation**: `(W_k + delta) / (sum W + K delta)` with K the input count, against a
   float64 evaluation within 1e-6, sums to 1 within `K * 1.2e-7`, for K = 1, 2, 3
   (`test_regularisation`).
8. **Planted wrong implementations fail by name** (`test_planted_*`, both devices): N{} per
   channel instead of joint; bounds measured inside the render; no floor (the prototype's 1e-6
   rule); the floor as a plain max on the range (a flat image then gives 0, not 0.5); delta in
   the numerator only; K fixed at 1; weights applied at full resolution only; a fixed pyramid
   depth; saliency against the unblurred Lab image; a float64 leak (NumPy float64 parameters
   must still give float32 results: the steps take scalars as Python floats). From DR-19 item
   (5)'s list (WP1.2R Reviewer B, md5 `f1cc6cf8ae3da62a1b3765573320e7b7`), the ones touching
   these steps: the size-independent sigma rule (claim 10's size test) and unlocked reduction
   values (the bounds and saliency means are pinned to exact values, claims 1 and 3).
9. **Gate 1**: on the GPU every array result is a `cupy.ndarray` (float32); the render chain and
   every array function run under `cupyx.allow_synchronize(False)`; each measure does
   synchronise, and only through `backend.to_host` (the bounds) and `channel_means` (the saliency
   means), two reads in all (`test_gpu_sync_points_are_the_documented_ones`).
10. **X-4** (below): `test_x4_unusable_sigma_names_the_parameter` (0, negative, NaN, inf, 1e300
    for each of the three fractions through every function deriving it; no output, no log
    record, no array work before the refusal, shown by a counting backend and array);
    `test_x4_support_bound_depends_on_the_image_size` (350 of the short side refused at 48 MP,
    a broadcast view, accepted at 1 x 1 and inside the bound at 5.3K);
    `test_signatures_are_x1_form` (no step takes a compensation parameter).
11. **Dependency rule**: importing `clearwater.methods.fusion` loads no `clearwater.io`,
    `.jobs`, `.gui`, `.config`, `PIL`, `av`, `PySide6`, `cupy`, `cupyx` (subprocess test); the
    WP3.1 static rule (no `.xp`, no `cupy` import outside `clearwater.core`) passes over it.

## Deviations from the prototype (all ruled)

- **Input 1 is clipped to [0, 1]** (round-0 ruling 1; brief task 2 and the prototype's
  docstring). The prototype's CODE clips input 2 only. For `a` in [0, 1] and `gamma >= 0` the
  clip changes no value (`test_input1_clip_is_a_no_op`, gamma 0 to 3, with exact 0 and 1).
- **No value-range check of the image** (ruling 2): the prototype's per-step minimum and
  maximum reads (`_check_image`) are not carried; they would be host syncs (Gate 1). Inputs are
  checked for backend, dtype and shape (the core's `check_rgb` / `check_spatial`); IF-1 is the
  [0, 1] contract.
- **The floor replaces the 1e-6 flat rule** (ruling 3.1); on the GPU a flat image's input 2 lies
  within 1.5e-6 of the prototype's exact `(I + 0.5) / 2`.
- **`weight_maps` returns the normalised maps only** (brief question 6); the raw maps stay
  testable through their public functions. Supplied saliency means are guarded like the bounds
  (ruling 4); K is `len(inputs)` (ruling 5). `pyramid_min_level_size < 1` raises ValueError
  (the core's rule; the prototype loops to 1 px).
- **W_L keeps the prototype's deliberate adaptation of [A18]**: the 5-point Laplacian of the
  luma smoothed at `laplacian_fraction` of the short side, times sigma squared (D56; [A18] uses
  the pixel-scale Laplacian).

## DR-19 rule

X-4, as ruled (CHARC `53b752a4d7fac4fc`), the one rule shared with WP3.2:

(a) each step function validates only the values IT derives from its own parameters and the
image size (each spatial sigma: finite, positive, support within the core's bound), before any
array work, so validation is method-scoped by construction (a step never sees another method's
parameters; the prototype's method-agnostic `check_derived_values` is not ported); (b) a
failure is ONE `ValueError` whose message names the parameter, its value and the short side,
in the form `"<name>=<value> gives a sigma of <s> px at the short side <n> px; ..."` (the
prototype's wording), with no other output (no log line or print before it); (c) the support
bound is the core's: the step calls `clearwater.core.check_sigma` (integer radius) and
re-raises its ValueError, which does not name a parameter, as (b)'s message (`raise ... from`);
the bound is never restated; (d) a parameter's own range (negative strength, cap below 0) is
the schema's (WP3.4) and is not re-checked by the steps. WP3.4 then calls the same steps and
inherits the rule.

In WP3.3 the rule applies to `sharpen_blur_fraction` (`high_pass`, `normalisation_bounds`,
`fusion_inputs`), `laplacian_fraction` (`laplacian_weight`, `weight_maps`) and
`saliency_blur_fraction` (`saliency_weight`, `weight_maps`); the message is
`f"{name}={fraction!r} gives a sigma of {sigma:.6g} px at the short side {n} px; {exc}"`, with
`exc` the `check_sigma` error. Tests in claim 10. DR-19 stays OPEN until WP3.4's schema lands;
WP3.3 discharges items (1) and (2) for its own parameters; item (3) does not recur
(`check_sigma` bounds the integer radius); item (4) is held by the core's input checks (R0-3)
and R0-8; item (5) by claim 8.

## DR-13 record (not a gate)

DR-13: "At `laplacian_fraction` 0.001 the Laplacian contrast weight is about 1% of the
aggregated weight on textured content (saliency ~0.08, saturation ~0.19), so the contrast term
is nearly inert at the defaults." Measured at the default (`measure.txt`), share of W_L in the
aggregated weight (sums over the image):

| Input | mean W_L | mean W_S | mean W_Sat | W_L share |
|---|---|---|---|---|
| `png16-gradient-none`, input 1 | 1.3e-6 | 0.273 | 4.9e-10 | 0.000 % |
| `png16-gradient-none`, input 2 | 4.5e-5 | 0.132 | 3.4e-9 | 0.034 % |
| 4K textured synthetic (white-balanced), input 1 | 0.0022 | 0.085 | 0.017 | 2.1 % |
| 4K textured synthetic (white-balanced), input 2 | 0.010 | 0.076 | 0.057 | 7.3 % |

The term stays small at the default, as DR-13 says. `laplacian_fraction` keeps its default
0.001 and the scale-normalised form; no recalibration here. DR-13 stays OPEN.

## Sync points (for WP3.21)

Per frame of the measure path: one read of the two N{} bounds and one `channel_means` read
(three values) per fusion input. The render reads nothing back. On the measure path the
high-pass is computed twice (once for the bounds, once in `fusion_inputs` for input 2's
saliency reference), at the proxy size only.

## Limits

- `cupyx.allow_synchronize` is deprecated by CuPy because it cannot see every implicit
  synchronisation; the Gate 1 test pins the explicit host reads, not every stall.
- The 4K figures were measured once (`measure.py`, `measure.txt` in the evidence folder), not by
  a test; tests pin the same quantities at small sizes. No timing (not an exclusive package).
- Not run off the envelope: other GPUs, other operating systems, multi-GPU.
