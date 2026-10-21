# WP3.4 ledger -- method assembly: stages and parameter schema

Cell: implementer-opus-high (Opus 5.5). Branch `wp3.4` from main `de206e2`. Brief
`docs/briefs/wp3.4-brief.md` (FINAL, rulings CHARC `53d1d906e47fe2c9`).

## Round 0 -- design table (2026-10-20, before product code)

Anchors re-grounded against `de206e2`: IF-3 `method.py`, `stubs.C3_STAGES`, IF-9
`validate_parameter_set`, `methods/{compensation,white_balance,fusion}.py`, `core/{backend,ops,
memory}.py`, `tools/core_speed.py`, `prototype/{params,pipeline,temporal}.py`,
`gui/imaging.py` (`measure_statistics`, `preview_export_difference`, `downscale`). Probe
scripts in the session scratchpad (`dr40a.py`, `v8probe*.py`); outputs quoted below.

### R0-1 Stage tables

Records (Y-1 (a)): every declared name, float64 host `numpy` arrays of the fixed shape below.

**c3** -- equal to `stubs.C3_STAGES` field for field (asserted by a test):

| stage | statistics (shape) | smoothed | depends_on_parameters | depends_on_stages | source_only |
|---|---|---|---|---|---|
| white_balance | means (3,), gains (3,) | both | kappa, lambda_, c3_strength, c3_kernel_fraction, c3_mask_threshold, c3_mask_smooth_fraction | () | False |
| fusion | bounds (2,), saliency_means (2, 3) | both | white_balance_strength, max_white_balance_gain, sharpen_blur_fraction, normalisation_low, normalisation_high, gamma, sharpen_strength | white_balance | False |

**ancuti2018**:

| stage | statistics (shape) | smoothed | depends_on_parameters | depends_on_stages | source_only |
|---|---|---|---|---|---|
| compensation | means (3,), cap_statistics (2,) [red, blue], alpha (2,) [red, blue] | means, alpha | alpha, blue_compensation, red_gain_cap, blue_gain_cap | () | True |
| white_balance | means (3,), gains (3,) | both | () | compensation | False |
| fusion | bounds (2,), saliency_means (2, 3) | both | (c3's fusion tuple, same order) | compensation, white_balance | False |

- `cap_statistics` is measured for BOTH channels always (WP3.2 note), so `closed_form` can
  answer a `blue_compensation` toggle. It is not smoothed (AD-6 smooths means and alpha only;
  render does not read it).
- `alpha[1]` (blue) is the effective strength applied to blue: 0.0 when blue compensation is
  off (finite, smoothable, Y-2-valid); render/analyze pass `{"red"}` or `{"red", "blue"}` to
  `compensate_ancuti2018` by the `blue_compensation` parameter.
- Dependency convention: the TRANSITIVE one the frozen `C3_STAGES` fixes (its fusion stage
  omits kappa..c3_* although fusion's `analyze` re-runs `compensate_c3`; they reach it through
  `depends_on_stages`). Ancuti follows it: white_balance lists no parameter (blue_compensation
  reaches it via compensation). WP3.11 step 6 invalidates transitively, so this is complete.
- Render-only parameters (no stage): laplacian_fraction, saliency_blur_fraction, weight_delta,
  pyramid_min_level_size, blend_with_original. (`saliency_reference` uses no parameter.)

### R0-2 Chains and host reads (DR-38 (a) counts, per frame)

`b = backend_for(image.device)`; `b.check_rgb(image.pixels)` first (TypeError on a foreign
array). `comp(I)` = `compensate_ancuti2018(b, I, means=E.means, alphas=E.alpha by flag)`
(Ancuti, E = SUPPLIED compensation record) or `compensate_c3(b, I, **c3 params)`.

| path | chain | host reads |
|---|---|---|
| A compensation | `channel_means(b, I)`; `cap_statistics(b, I, blue_compensation=True)`; `effective_alphas(...)` | 3 (1 triple + 2 scalars) |
| white_balance (both) | `channel_means(b, comp(I))`; `gray_world_gains` | 1 |
| fusion (both) | `applied_gains(earlier gains, strength, clamp)`; `W = apply_white_balance(b, comp(I), g)`; `normalisation_bounds(b, W, ...)`; `fusion_inputs(b, W, ..., bounds=measured)`; `saliency_reference` x2 | 3 |
| render | `comp(I)`; `applied_gains(record gains)`; `apply_white_balance`; `fusion_inputs(bounds=record)`; `weight_maps(saliency_means=record)`; `multiscale_fusion`; `(1 - b)*F + b*I`, `b = blend/100` | 0 |

Per frame: ancuti2018 7 reads, c3 4. Render uploads (DR-40 (b)): WB gains 1, saliency
references 2, c3 matrix 1 (c3 only). Intermediates dropped as soon as consumed (memory peak).
Render returns `dataclasses.replace(image, pixels=out)`: same device, colour, and a `Frame`
stays a `Frame` (pts kept) -- R0-Q3.

### R0-3 Schema (proposed ranges for the dispatcher's ruling, Q4)

Order: Basic in 6.7 order, then Advanced in 6.7 order, then the rest. Neutral = `Params.neutral()`
for the six V9 controls, the default elsewhere. Labels ASCII.

| name | type | default | min | max | panel | method | neutral | nullable |
|---|---|---|---|---|---|---|---|---|
| alpha | float | 1.0 | 0 | 2 | basic | A | 0.0 | |
| c3_strength | float | 1.0 | 0 | 2 | basic | c3 | 0.0 | |
| blue_compensation | bool | False | - | - | basic | A | False | |
| white_balance_strength | float | 1.0 | 0 | 1 | basic | both | 0.0 | |
| sharpen_strength | float | 1.0 | 0 | 2 | basic | both | 0.0 | |
| blend_with_original | float | 0.0 | 0 | 100 | basic | both | 0.0 | |
| red_gain_cap | float | 2.0 | 0 | 10 | advanced | A | 2.0 | yes |
| blue_gain_cap | float | 2.0 | 0 | 10 | advanced | A | 2.0 | yes |
| kappa | float | 1.0 | 0 | 3 | advanced | c3 | 1.0 | |
| lambda_ | float | 0.7 | 0 | 3 | advanced | c3 | 0.7 | |
| max_white_balance_gain | float | 3.0 | 1 | 10 | advanced | both | 3.0 | |
| gamma | float | 1.5 | 0.1 | 4 | advanced | both | 1.0 | |
| pyramid_min_level_size | int | 16 | 1 | 256 | advanced | both | 16 | |
| c3_kernel_fraction | float | 0.05 | 0.005 | 0.25 | advanced | c3 | 0.05 | |
| c3_mask_threshold | float | 0.85 | 0 | 1 | advanced | c3 | 0.85 | |
| c3_mask_smooth_fraction | float | 0.01 | 0.001 | 0.1 | advanced | c3 | 0.01 | |
| sharpen_blur_fraction | float | 0.005 | 0.0005 | 0.05 | advanced | both | 0.005 | |
| normalisation_low | float | 0.5 | 0 | 100 | advanced | both | 0.5 | |
| normalisation_high | float | 99.5 | 0 | 100 | advanced | both | 99.5 | |
| laplacian_fraction | float | 0.001 | 0.0001 | 0.02 | advanced | both | 0.001 | |
| saliency_blur_fraction | float | 0.003 | 0.0005 | 0.05 | advanced | both | 0.003 | |
| weight_delta | float | 0.1 | 0.001 | 1 | advanced | both | 0.1 | |

c3 has no alpha, blue_compensation or caps (D49 by construction); ancuti2018 no kappa,
lambda_, c3_*. Defaults are the prototype `Params()` fields (AD-8). With these finite bounds
the prototype's float32-range and product checks are unreachable, and every spatial sigma is
positive and its radius far below the core bound for any image from 1 x 1 to 48 MP
(0.25 x 8000 px x 4 = 8000 px << 2**23).

**Checks the schema cannot express (X-4 form, method level, before any array work in
`analyze`, `render`, `closed_form`):** `normalisation_low < normalisation_high`, one ValueError
naming `normalisation_low` with both values. Nothing else remains under the proposed bounds.

### R0-4 Questions the brief leaves to this table (recommendation first)

- **R0-Q1 params mapping.** The method resolves `params`: a missing name takes the default
  (IF-9: sets may be partial), an unknown name is one ValueError naming it, then
  `validate_parameter_set` against its own schema (first problem -> one ValueError naming the
  parameter), then R0-3's cross check. Alternative: cross check only (out-of-range is out of
  envelope).
- **R0-Q2 error types.** Unknown `stage` -> ValueError (stub parity); a stage missing from
  `render`'s statistics or `analyze`'s `earlier` -> KeyError naming it (stub parity; WP3.11
  builds against the stub); a record's content (Y-2) -> ValueError naming stage and
  statistic; an `earlier` key that is not a stage of the method -> ValueError.
- **R0-Q3** render returns `dataclasses.replace(image, pixels=out)` (a Frame keeps pts).
- **R0-Q4 schema split.** `methods/schema.py` holds both parameter tuples and the resolver;
  `ancuti_fusion.py` the stages and the method class (one class, two instances).
- **R0-Q5 blend.** Prototype form `(1 - b) * fused + b * input`, no extra clip (bit-identity);
  a test asserts the output stays in [0, 1].

### R0-5 Answers: Y-1, Y-2, questions 2-8

- **Y-1** as ruled; c3 by `C3_STAGES`; Ancuti compensation per R0-1 ((c) capped alpha per
  frame, smoothed as a value; (d) non-None only for compensation: means and cap_statistics
  passed through, alpha recomputed with current params, bit-identical to `analyze`; (e) the
  only `source_only` stage). The report's Y-1 text is to be identical to WP3.11's (relay).
- **Y-2** as recommended, in `analyze` (the consumed earlier records), `render` (every stage)
  and `closed_form` (measured + earlier): exact name set, shape per R0-1, finite.
- **Q2** `clearwater.core.backend_for(device)`: "cpu" -> the process NumpyBackend; the probed
  GPU's own `cuda:<n>` -> that CupyBackend; anything else ValueError. WP3.1 tests extended.
- **Q3** `clearwater.methods.available_methods() -> dict[str, CorrectionMethod]`, c3 first,
  new instances per call; ids exactly c3, ancuti2018.
- **Q5** ops helpers annotated `CoreBackend` (`_core` keeps its run-time TypeError). Call
  sites needing a line: ONLY `fusion.py` (202, 286, 503, 512 pass the `ArrayBackend`-typed
  argument); `compensation.py` already passes the narrowed `core`, `white_balance.py` calls no
  ops helper -- premise mismatch P-4. Edit form: `cast(CoreBackend, backend)` (zero run-time
  change; the helper's own `_core` still raises the same TypeError).
- **Q6** DR-38 (c): `check_rgb` refuses H or W < 1 as `check_spatial` does. DR-38 (d):
  `check_sigma` catches the overflow and raises ValueError (radius computed only for finite
  `4 * sigma`). DR-37 (a): "not installed" only for `ModuleNotFoundError` with `name == "cupy"`
  (keeps `sys.modules["cupy"] = None`, which raises exactly that). DR-40 (b): recorded by the
  speed row, fix stays WP3.21's.
- **Q7** `tools/core_speed.py --whole [--memory]`, outputs `work/wp3.4/` (via the config's
  working path). DR-37 (d): no video stream -> SpeedError. (e): the GPU row selected by
  matching CuPy's device PCI bus id to `nvidia-smi --query-gpu=pci.bus_id,...`.
- **Q8** DR-13 placement only (Advanced, 0.001).

### R0-6 Speed and memory plan (task 8, EXCLUSIVE windows)

- **Speed:** GX011627 full clip on the GPU, 10 evenly spread frames on the CPU; per frame,
  both methods at the AD-8 defaults, alternating order: the 4K upload (apart); `analyze` of
  every stage in order on the 960 x 540 block-mean proxy (proxy built untimed; the frame's own
  raw earlier records, as `measure_statistics`); `render` at 4K with that record; the
  prototype `correct()` on the same frame. Conditions (clocks, temperature, busy processes)
  before, every N frames and after; contaminated rows kept as spread. Reported: medians and
  spread; the core's share (analyze + render) against D106's interim bar (25 min/min =
  0.834 s/frame at 30000/1001 fps, whole export) and its own min/min; render uploads counted
  and a 3-value upload timed (DR-40 (b)).
- **Memory:** a counting allocator on the CuPy pool (used high-water, reserved after every
  allocation; WP1.2A form) and sampled RSS, on `render` and `analyze` (on the full frame and
  on its proxy) at 3840 x 2160 and 5312 x 2988, both methods, against
  `memory_estimate_bytes`. STOP with the figures if a product peak exceeds the estimate or
  the core alone exceeds 0.834 s/frame.

### R0-7 Premises that do not match reality (each with its reproduction)

- **P-1 (STOP: V8 at AD-11's max bound is not met by the algorithm).** Prototype `correct()`
  (the product mirrors it), CPU, statistics of the full image supplied to both renders,
  `gui.imaging.downscale`, scratch `v8probe2.py` / `v8probe3.py`, values in /255:

  | image | method | k | mean | p99 | p99.9 | max |
  |---|---|---|---|---|---|---|
  | GX011625_0024.925 centre 1080 x 1920 crop (work/wp1.3/frames) | c3 | 2 | 0.086 | 0.93 | 8.4 | 29.4 |
  | same | c3 | 4 | 0.246 | 3.25 | 12.2 | 26.0 |
  | GX011625_0114.648 crop | c3 | 2 | 0.116 | 0.90 | 4.4 | 32.8 |
  | same | c3 | 4 | 0.359 | 2.06 | 6.5 | 27.1 |
  | same, ancuti2018 | A | 2 / 4 | 0.122 / 0.372 | | | 31.0 / 26.5 |
  | png16-lowred-none (64 x 96) | c3 | 2 / 4 | 6.8 / 6.6 | | | 23.9 / 12.7 |
  | png16-gradient-none (64 x 96) | both | 2 / 4 | 0.57 / 0.63 | | | 12.4 / 5.7 |
  | png16-uniform-none | both | 2 / 4 | 0 | | | 0 |
  | synthetic smooth 540 x 960 | c3 | 2 / 4 | 0.02 / 0.16 | | | 15.2 / 26.2 (all at borders; interior <= 0.41) |
  | synthetic + 1 % noise | c3 | 2 / 4 | 2.1 / 3.0 | | | 10.3 / 8.0 |

  k = 1 is exact everywhere. Real content meets mean <= 1/255 but misses max <= 3/255 by
  8-11x (0.3-1 % of values above 3/255: fine detail the preview cannot sharpen, borders); the
  64 x 96 stills are too small for k > 1 and miss the mean too; pixel-scale noise misses the
  mean. Needs a ruling on AD-11's V8 bound and on the test's images (e.g. mean <= 1/255 plus a
  high percentile, on real-sized content; or interior-only; or per-k bounds). V8 test held
  until ruled; everything else proceeds.
- **P-2 (DR-40 (a) test form cannot detect the defect).** Mutant `effective_alphas` without
  the early `float(alpha)` (scratch `dr40a.py`): with cap None and `alpha` `np.float64` or
  `np.float32`, original and mutant return identical values and types (the final
  `float(effective)` normalises). Detecting form: `alpha=np.float32(1.0)` with a BINDING cap
  whose value is within float32 rounding below alpha (`red_gain_cap=(1 - 1e-9) / (0.1 / 0.12)`,
  means (0.1, 0.5, 0.4), cap statistic 0.3): original 0.9999999990000001, mutant 1.0 (NEP 50
  compares in float32). Proposed: the test uses that form; `compensation.py` unchanged.
- **P-3 (confirmed as the register says):** `check_sigma(1e308)` -> OverflowError;
  `NumpyBackend().check_rgb(zeros((0, 1, 3)))` accepted; `sys.modules["cupy"] = None` ->
  ModuleNotFoundError with `name == "cupy"`.
- **P-4:** Q5's call-site lines exist only in `fusion.py` (above).
- **P-5 (process note):** product against prototype is bit-identical on the same device
  except where the N{} floor binds (the uniform stills: WP3.3 ruling 3.1); there AD-11.

## Cumulative round ledger

| round | depth (dispatcher) | critical | major | minor | in / out envelope | NEW / REOPENED | reverts | fixes: product / test-only | transport, CLI |
|---|---|---|---|---|---|---|---|---|---|
| 0 (design) | -- | -- | -- | -- | -- | -- | -- | -- | -- |
