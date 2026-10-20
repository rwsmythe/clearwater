# WP3.3 ledger -- fusion inputs, weights and blending

Cell: wp33-cell (implementer, opus-high), tier STRONG. Worktree `.worktrees/wp3.3`, branch
`wp3.3`, base main `2c5540a` (clean at dispatch, no foreign change). Brief
`docs/briefs/wp3.3-brief.md` (FINAL, rulings CHARC `53b752a4d7fac4fc`).

## Round 0 -- function table (brief task 1)

Grounded on the code at the base (`tools/prototype/pipeline.py`, `src/clearwater/core/`) and
the installed stack (NumPy 2.5.4, SciPy 1.18.1, CuPy 14.2.0). Facts measured, not assumed
(probe on a seeded 512 x 512 x 3 float32 image, both devices; script in the session scratchpad):

- `a ** np.float32(1.5)` == `xp.power(a, np.float32(1.5))` bit for bit, NumPy and CuPy;
  `a ** np.float32(1.0)` == `a` on both.
- `a ** 0.5` == `xp.sqrt(a)` bit for bit, NumPy and CuPy, float32 out.
- builtin `abs`, `.clip(lo, hi)`, `.mean(axis=)`, `.sum(axis=)` == `xp.abs`, `xp.clip`,
  `xp.mean`, `xp.sum` bit for bit on both.
- `(W_0 + 2 * 0.1) + W_1` == `full_like(W_0, 2 * 0.1); += W_0; += W_1` bit for bit on both.
- CuPy `a ** 2` != `cupy.power(a, 2)` (max 6e-8): irrelevant, the prototype writes `** 2` too,
  and the product keeps the same operator.
- The stretch `(hp - low) / (high - low)` with float64 bounds against the same bounds rounded
  to float32: max 2.4e-7 on both devices (the WP3.1 consumer note, measured).

### Product functions (X-1)

Module `src/clearwater/methods/fusion.py`. Backend first, array second, keyword-only parameters
without defaults, names = prototype `Params` fields. Every function takes a `CoreBackend`
(DR-37 b); arrays stay on its device.

| Product function | Prototype counterpart | Measure / render | Bit identity expected |
|---|---|---|---|
| `high_pass(backend, a, *, sharpen_blur_fraction) -> Array` | `high_pass_of` | shared by both | yes, CPU and GPU (same `a - gaussian_filter(...)`) |
| `normalisation_bounds(backend, a, *, sharpen_blur_fraction, normalisation_low, normalisation_high) -> tuple[float, float]` | `normalisation_bounds` / `_high_pass_and_bounds` | MEASURE (sync: reads 2 floats) | no: = float32(prototype bound) exactly (R0-8); prototype keeps float64. Within one float32 ulp of the bound |
| `fusion_inputs(backend, a, *, gamma, sharpen_strength, sharpen_blur_fraction, bounds) -> tuple[Array, Array]` | `fusion_inputs(image, params, Statistics(normalisation_bounds=...))` | RENDER (never measures) | input 1: yes. Input 2 with the SAME supplied bounds: yes when `high - low >= 0.02`; differs by design below (the floor). Measure-then-render against the prototype's measured path: within AD-11 (the float32 bounds), max reported |
| `saliency_reference(backend, a) -> tuple[float, float, float]` | `saliency_reference` (`_lab_mean(srgb_to_lab(.))`) | MEASURE (sync: `channel_means`) | yes: `float(np.float32(channel_means(rgb_to_lab(a))))` = the prototype's float32-cast float64 mean |
| `laplacian_weight(backend, a, *, laplacian_fraction) -> Array` | `_laplacian_weight` | render | yes |
| `saliency_weight(backend, a, *, saliency_blur_fraction, saliency_mean) -> Array` | `_saliency_weight(image, params, reference)` | render (mean supplied) | yes (supplied mean uploaded as float32, as the prototype) |
| `saturation_weight(backend, a) -> Array` | `_saturation_weight` | render | yes |
| `weight_maps(backend, inputs, *, laplacian_fraction, saliency_blur_fraction, weight_delta, saliency_means) -> tuple[Array, ...]` | `weight_maps(...).normalised` with `Statistics(saliency_means=...)` | render | yes |
| `multiscale_fusion(backend, inputs, weights, *, pyramid_min_level_size) -> Array` | `multiscale_fusion` | render | yes (core pyramids are bit-identical, WP3.1 claim 1) |

Module constant: `NORMALISATION_RANGE_FLOOR = 0.02` (AD-4, ruling 3.1; spec 6.7 lists no
control for it).

### Prototype `xp.` calls and their replacements (X-3)

| Prototype call (function) | Product replacement | Same operation? |
|---|---|---|
| `xp.power(image, float32(gamma))` (`fusion_inputs`) | `a ** np.float32(gamma)` | yes (measured, both devices) |
| `xp.full_like(image, 0.5)` (flat rule, `fusion_inputs`) | removed: the floor replaces the 1e-6 rule; a flat input gives `(0 + 0.01) / 0.02` = exactly 0.5 (float32(0.02) = 2 float32(0.01)) | n/a (retired rule) |
| `xp.clip(x, 0.0, 1.0)` (`fusion_inputs`, `multiscale_fusion`) | `x.clip(0.0, 1.0)` | yes (measured) |
| `xp.percentile(hp, [lo, hi], method="linear")` | IF-2 `backend.percentile(hp, [lo, hi])` + `backend.to_host(...).tolist()` | no: cast to float32 once (R0-8) |
| `xp.asarray(_supplied_triple(ref), float32)` (`_saliency_weight`) | `backend.asarray(np.asarray(ref, np.float32))` | yes (host-to-device upload, not a read) |
| `_lab_mean(lab)` (float64 mean, `.astype(float32)` on device) | `channel_means(backend, lab)` then `np.float32` on host | yes (same float64 reduction, same IEEE rounding); one sync per input |
| `xp.sqrt(xp.sum((blurred - mean) ** 2, axis=2))` (`_saliency_weight`) | `(((blurred - mean) ** 2).sum(axis=2)) ** 0.5` | yes (measured) |
| `xp.mean((image - luma[..., None]) ** 2, axis=2)`, `xp.sqrt(.)` (`_saturation_weight`) | `.mean(axis=2)`, `** 0.5` | yes (measured) |
| `backend.xp.abs(xp.asarray(log, float32) * float32(sigma ** 2))` (`_laplacian_weight`) | `abs(log * np.float32(sigma ** 2))` (`core.laplacian` already returns float32) | yes |
| `backend.ndimage.laplace(..., mode="reflect")` | `clearwater.core.laplacian` | yes (WP3.1) |
| `_gaussian(.)` (`gaussian_filter`, reflect, truncate 4) | IF-2 `backend.gaussian_blur` | yes (WP3.1) |
| `luminance`, `srgb_to_lab`, `pyramid_levels`, `gaussian_pyramid`, `laplacian_pyramid`, `collapse_pyramid` | the `clearwater.core` helpers of the same names (`rgb_to_lab`) | yes (WP3.1) |
| `xp.full_like(W_0, K * delta); += W_k` (`weight_maps`) | `(W_0 + K * delta) + W_1 + ...` | yes (measured) |
| `of(weight).xp.asarray(weight, float32)` (`multiscale_fusion`) | none needed: the weight is checked float32 | yes |
| `_check_image` (`float(image.min())`, `float(image.max())`, every step) | NOT ported: dtype, shape and device checks only (core `check_rgb` / `check_spatial`); a value-range read is a host sync (Gate 1). IF-1 states the [0, 1] contract | n/a |

No operation needs `xp`; no STOP under X-3.

### The floor as ruled (3.1)

In `fusion_inputs`, on the SUPPLIED bounds: if `high - low < 0.02`, `mid = (low + high) / 2`,
`low' = mid - 0.01`, `high' = mid + 0.01`; else unchanged. Then
`stretched = ((hp - low') / (high' - low')).clip(0, 1)`, `S = (a + stretched) / 2`,
`input2 = (a + s * (S - a)).clip(0, 1)`. Exactly flat input: 0.5 (as the prototype); near-flat
(e.g. DR-14's 0.0018): amplification bounded to 1 / 0.02 = 50x instead of about 540x; range
>= 0.02: untouched, bit-identical to the prototype on the same supplied bounds. The bounds
guard (two finite values, `low <= high`, ValueError naming `bounds`) runs before any array work.

### Validation (X-4)

Each function validates the sigmas it derives, before any array work: `high_pass`,
`normalisation_bounds`, `fusion_inputs` -> `sharpen_blur_fraction`; `laplacian_weight` ->
`laplacian_fraction`; `saliency_weight` -> `saliency_blur_fraction`; `weight_maps` -> both of
the latter. `spatial_sigma` then `check_sigma`, its ValueError re-raised as
`"<name>=<value> gives a sigma of <s> px at the short side <n> px; <check_sigma message>"`
(`from` the original). Parameter ranges (gamma, strengths, percentiles, delta, min level size)
are the schema's (WP3.4); the core's own refusals (percentile outside 0-100,
`min_level_size < 1`) stand as they are.

### Sync points (Gate 1)

`normalisation_bounds`: one read of two float32 values. `saliency_reference`: one
`channel_means` read (three values) per input. Nothing else reads the device.

### Round-0 questions (recommended answer first)

1. **Input 1 clipping.** Brief task 2 says "Both clipped to [0, 1]"; the prototype's docstring
   says so but its code clips only input 2. Recommended: clip input 1 too, as the brief says;
   for `a` in [0, 1] and `gamma >= 0` the clip is a no-op, so input 1 stays bit-identical.
2. **No value-range check of the image.** Recommended: dtype, shape and device only (above);
   the prototype's min/max read per step would be four or more host syncs per frame, which
   Gate 1 forbids. Out-of-range input is outside IF-1.
3. **Names X-1 leaves open in this module.** Recommended: `saliency_mean` (one input's triple)
   on `saliency_weight`; `saliency_means` (one triple per input, in input order) on
   `weight_maps`; `bounds` (low, high) on `fusion_inputs`; constant
   `NORMALISATION_RANGE_FLOOR`. None is a WP3.4 schema or stage name.
4. **Supplied saliency means guard.** Recommended: `weight_maps` / `saliency_weight` refuse a
   wrong count (one per input), a triple of the wrong length or a non-finite value with a
   ValueError naming the field, host-side, before any array work (the prototype's
   `check_statistics` / `_supplied_triple` rule; brief question 2 names only the bounds).
5. **K.** Recommended: K = `len(inputs)`, at least 1, all inputs the same shape (the
   prototype's rule); WP3.4 always passes 2.

No STOP item: no interface, core, dependency or tolerance change is needed.

## Cumulative round ledger

| Round | Critical | Major | Minor | Nit | In / out envelope | NEW / REOPENED | Reverts | Product / test-only fixes | Depth (dispatcher) |
|---|---|---|---|---|---|---|---|---|---|
| 0 (table) | - | - | - | - | - | - | - | - | 119,733 (dispatcher) |
| 1 (head 8643ba1) | 0 | 1 | 3 | 0 | 3 in / 1 out (F4) | 4 NEW / 0 | 0 | planned: F1 test+report, F2 test, F3 product+test, F4 product+test | (dispatcher) |

Round-0 ruling (orchestrator gen 6): table accepted as committed (c80393f); questions 1-5 as
recommended.

### Round 1 (Reviewer A, STRONG, gpt-5.6-sol high)

Evidence `C:\Users\rwsmy\clearwater-review-evidence\wp3.3\r1\` (review-prompt.md, review-diff.txt,
review.txt, review.stderr.txt, adjudication.md, tests-8643ba1.txt, md5sums.txt). Verdict
NEW_CRITICAL_MAJOR_FOUND.

- F1 MAJOR, CONFIRMED, NEW: the CPU/GPU test compares only input 1, input 2 and the fused image,
  yet the report says it pins the per-function figures. Plan: compare every intermediate; report
  wording exact.
- F2 MINOR, CONFIRMED, NEW: the supplied-statistic guard tests do not show "before array work".
  Plan: run them on the counting backend and array.
- F3 MINOR, CONFIRMED (cell repro: bounds (1e308, 1e308) give NaN), NEW: finite bounds beyond the
  float32 range overflow. Plan: the guard refuses a bound or range not finite in float32.
- F4 MINOR, OUT-OF-ENVELOPE, CONFIRMED (cell repro: AttributeError), NEW: `weight_maps` /
  `multiscale_fusion` read `.shape` before the array checks. Plan: check first.

Pre-round incident: the first summary run (pytest -v, 232c17a) stalled in pytest's byte-wise
diff of a planted failure; fixed in 8643ba1 (tests only), the head reviewed. The stalled process
(pid 37676) was not stopped (classifier denial at this seat; the dispatcher left it). Its
background chain may later write a stale `r1/test-summary.txt` (232c17a, not reviewed); the
reviewer read `r1/tests-8643ba1.txt`. md5s of the round-1 files as they stood at adjudication
are in `r1/md5sums.txt` (tests-8643ba1.txt `18a7d7f8efec2450c1f28f3aa734e41e`, review.txt
`84519aed9ed6b6482ddead299b3b67cd`).

Round-1 ruling (orchestrator gen 6; depth 257,103 at the yield, the ~250K evaluation point):
CONTINUE; F1-F4 accepted as planned; add the `check_sigma` OverflowError guard (WP3.2's
finding); round 2 on the remediated head.

Remediation, one commit each, each test failing on the unfixed code where a product change is
made:
- be0b145 F1 (test + report): every intermediate compared CPU/GPU and same-device.
- aa5c003 F2 (test): guards on the counting backend/array; planted late guard fails.
- d637dcc F3 (product + test): bounds and range beyond float32 refused (4 cases failed before).
- 66220b0 F4 (product + test): arrays checked before `.shape` (AttributeError before).
- 0f4121f X-4 OverflowError (product + test; dispatcher heads-up, WP3.2's wording): 3 failed
  before.
- ec5d2e5 NEW, found by the cell while fixing F3 (product + test): equal bounds near 3e38 passed
  the float32 guard but the floor's widening rounded away and the stretch divided by zero;
  now refused naming `bounds` (1 failed before). Recorded for round 2.
- 25180d9 report updates.
