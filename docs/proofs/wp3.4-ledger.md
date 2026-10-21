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

## Round-0 rulings (orchestrator, FINAL, 2026-10-20)

1. Schema ranges R0-3 APPROVED exactly as proposed (blend 0..100 per the brief's Rulings); the
   one X-4 cross check is `normalisation_low < normalisation_high`.
2. R0-Q1..R0-Q5 and Q2-Q8 RULED as recommended in R0-4 / R0-5. P-2: the detecting DR-40 (a)
   form (`alpha=np.float32(1.0)`, a binding cap just under it) RULED; `compensation.py`
   unchanged. P-4: `cast(CoreBackend, backend)` in `fusion.py` only (lines 202, 286, 503, 512
   at `de206e2`), type-only, RULED. P-3 and P-5 noted.
3. P-1 (V8): the bound is AD-11's (CHARC's); referred to CHARC. ONLY the V8 test is held.

### P-1 figures for CHARC (round-0 final task)

Script `C:\Users\rwsmy\clearwater-review-evidence\wp3.4\r0\v8_percentiles.py` (md5
`24d8b3c6a6dca23a6108714d0d1995e5`), output `v8_percentiles.txt` beside it (md5
`342f329b24b1c97093c96dae43283c13`), `md5sums.txt`. Prototype `correct()` on the CPU (the product
mirrors it), centre 1080 x 1920 crops of two real GX011625 look-check frames, the crop's own
statistics supplied to both renders; preview = `correct(downscale(I, k))`, export =
`downscale(correct(I), k)` (`gui.imaging.downscale`). Values in /255; "inner-B" excludes a
border of B preview pixels. k = 1 is exactly 0 in every row (all methods, both crops).

| crop | method | k | region | mean | p99 | p99.5 | p99.9 | max | frac > 3/255 |
|---|---|---|---|---|---|---|---|---|---|
| 0024.925 | c3 | 2 | all | 0.086 | 0.929 | 2.705 | 8.411 | 29.426 | 0.456 % |
| 0024.925 | c3 | 2 | inner-4 / inner-16 | 0.087 / 0.091 | 0.960 / 1.057 | 2.764 / 2.956 | 8.514 / 8.731 | 29.426 | 0.465 / 0.493 % |
| 0024.925 | c3 | 4 | all | 0.246 | 3.253 | 5.991 | 12.175 | 25.964 | 1.069 % |
| 0024.925 | c3 | 4 | inner-4 / inner-16 | 0.251 / 0.266 | 3.392 / 3.789 | 6.143 / 6.600 | 12.357 / 12.835 | 25.964 | 1.113 / 1.239 % |
| 0024.925 | ancuti2018 | 2 | all | 0.086 | 0.892 | 2.455 | 7.737 | 28.930 | 0.411 % |
| 0024.925 | ancuti2018 | 2 | inner-4 / inner-16 | 0.087 / 0.091 | 0.916 / 0.994 | 2.506 / 2.676 | 7.844 / 8.059 | 28.930 | 0.418 / 0.444 % |
| 0024.925 | ancuti2018 | 4 | all | 0.250 | 2.883 | 5.416 | 11.306 | 24.733 | 0.968 % |
| 0024.925 | ancuti2018 | 4 | inner-4 / inner-16 | 0.255 / 0.270 | 3.029 / 3.409 | 5.574 / 5.987 | 11.495 / 11.936 | 24.733 | 1.009 / 1.123 % |
| 0114.648 | c3 | 2 | all | 0.116 | 0.896 | 2.079 | 4.439 | 32.783 | 0.273 % |
| 0114.648 | c3 | 2 | inner-4 / inner-16 | 0.116 / 0.118 | 0.910 / 0.969 | 2.104 / 2.183 | 4.450 / 4.500 | 32.783 | 0.276 / 0.289 % |
| 0114.648 | c3 | 4 | all | 0.359 | 2.055 | 3.282 | 6.545 | 27.108 | 0.578 % |
| 0114.648 | c3 | 4 | inner-4 / inner-16 | 0.362 / 0.374 | 2.080 / 2.225 | 3.327 / 3.599 | 6.574 / 6.916 | 27.108 | 0.591 / 0.662 % |
| 0114.648 | ancuti2018 | 2 | all | 0.122 | 0.886 | 1.960 | 4.327 | 30.975 | 0.255 % |
| 0114.648 | ancuti2018 | 2 | inner-4 / inner-16 | 0.122 / 0.124 | 0.893 / 0.940 | 1.977 / 2.053 | 4.333 / 4.403 | 30.975 | 0.257 / 0.268 % |
| 0114.648 | ancuti2018 | 4 | all | 0.372 | 1.995 | 3.125 | 6.279 | 26.547 | 0.531 % |
| 0114.648 | ancuti2018 | 4 | inner-4 / inner-16 | 0.374 / 0.387 | 2.012 / 2.135 | 3.172 / 3.399 | 6.340 / 6.544 | 26.547 | 0.544 / 0.608 % |

Reading: on real content the mean bound (1/255) holds with 2.7-12x margin; p99 is at most
1.06/255 at k = 2 and up to 3.8/255 at k = 4; the max (25-33/255) and p99.9 (4.3-12.8/255)
miss 3/255 at every k > 1. Excluding the border does NOT help (every interior figure is equal
or slightly worse; the maximum sits inside): the difference is content (fine detail the
preview cannot sharpen), not edge handling. (On the synthetic smooth texture of R0-7 the
maxima were at the border; real footage behaves differently.)

## RESUME HERE (for the fresh cell, cell 3)

**Status at hand-off (cell 2, 2026-10-21, depth 346,044 per the dispatcher):** the build is
COMPLETE and every ruling is applied; full pytest GREEN (below); NO Reviewer A round has run.
Branch `wp3.4` (worktree `C:\Users\rwsmy\clearwater\.worktrees\wp3.4`), base `de206e2`, head =
the commit carrying this section. Design: the brief (incl. its Rulings), R0-1..R0-7 and the
round-0 rulings above, the cell-2 rulings in "Build" below (B-1, B-2 option A, V8). Do not
re-derive them; do not re-run round 0 or the probes.

**Done (commits `937d842`..this one):** core fixes + `backend_for` (DR-37 a, b; DR-38 c, d);
`methods/schema.py`, `methods/ancuti_fusion.py`, `methods/__init__.py` (`available_methods`);
`tools/core_speed.py --whole / --memory` (DR-37 d, e; smoke-run on the 320 x 180 fixture clip
only); tests `test_core_wp34.py`, `test_methods_assembly.py` (76), `test_methods_assembly_
prototype.py` (169), `test_methods_assembly_v8.py` (9; reads the MAIN tree's working folder
`wp1.3/frames` through the local config, skips when absent -- reachable without the footage
folder, so not marked `footage`), `test_core_speed.py` (21); the granted edits outside the owned
list (`test_core_select.py` one token; the two `__cause__` lines in `test_methods_compensation.py`
and `test_methods_fusion.py`); report draft `docs/reports/wp3.4-method-assembly.md` (stage and
schema tables, Y-1 verbatim, DR-19 rule, claims 1-14, V8 table, consumer notes, debt). Static
gates green (ruff check, ruff format --check, mypy strict 109 files). Targeted tests green on
CPU and GPU, incl. the core and WP3.2/WP3.3 files (571 + 565).

**Full pytest (window granted 2026-10-21, cell 2, depth 368,709):** at `84ad0ef` (code
identical to `79661c1`; only the ledger differs), CuPy importable, `QT_QPA_PLATFORM=offscreen`,
`--basetemp=work/pt-full`: **3868 passed, 2 skipped, 2 warnings in 975.80s (0:16:15)**, exit 0,
no FAILED or ERROR line (`work/full-pytest.txt` in the worktree).

**Remaining, in order:**
1. **Reviewer A from round 1** (STRONG, `docs/review-gate-clearwater.md` Part 1; runner and
   prompt shape from `C:\Users\rwsmy\clearwater-review-evidence\wp3.1\r2\`; evidence to
   `C:\Users\rwsmy\clearwater-review-evidence\wp3.4\rN\`; `--glob '!docs/proofs/**'`; diff
   `de206e2..HEAD`). Yield at every verdict BEFORE remediating; commit the ledger row per round.
2. **EXCLUSIVE windows**, each on the dispatcher's grant, one at a time, when the code is
   final: first `uv run python tools/core_speed.py GX011627 --memory`, then
   `uv run python tools/core_speed.py GX011627 --whole --cpu-frames 10` (outputs under the
   working folder's `wp3.4/`; grep the `MEMORY`, `ROW`, `BAR`, `RECORD` lines). STOP with the
   figures if a pool reserved peak exceeds `memory_estimate_bytes` or a core median exceeds
   D106's 0.834 s/frame.
3. **Full pytest without CuPy importable** (the brief's Done line; one more window), and the
   with-CuPy run again on the final head after any Reviewer A fix.
4. **Report**: fill the speed and memory sections (and DR-40 b's upload count/timing from the
   record), remove "DRAFT", update the status line; final return report per the recipe.

## Build (cell 2, 2026-10-21)

Commits `937d842`..`e5e2a93` on `wp3.4` (DR-37 b; core fixes + `backend_for`; the WP3.1
fixture line; methods + schema + registry; prototype/CPU-GPU/N10/V9 tests; `core_speed`
`--whole`/`--memory`; report draft). Static gates green (ruff check, ruff format --check, mypy
strict, 109 files). Targeted tests green: `test_methods_assembly.py` 76, `..._prototype.py` 169,
`test_core_speed.py` 21, core + WP3.2/WP3.3 files 571 + 899 (CPU and GPU).

Raised to the dispatcher in chat (answers arrive at the next yield):

- **B-1 (DR-37 a):** `tests/test_core_select.py::test_cupy_not_installed` raises a nameless
  `ModuleNotFoundError`; under the DR-37 (a) rule it reads "failed to load". Fixed by
  `name="cupy"` in that fixture (commit `ce8a436`, droppable); a WP3.1 test file outside the
  owned list.
- **B-2 (DR-38 d, FINDING):** five WP3.2/WP3.3 tests assert `__cause__` is OverflowError
  (`test_methods_compensation.py:839`, `test_methods_fusion.py:693`); with `check_sigma`
  raising ValueError they fail (messages unchanged). Options: (A) amend the two assertion lines
  (recommended), (B) a dual-class exception, (C) re-bank (d). The fix is in `c99debb`.

Rulings received (orchestrator, FINAL, 2026-10-21):

- **B-1 GRANTED:** the `name="cupy"` fixture token (commit `ce8a436`); the `exc.name is None`
  alternative declined.
- **B-2 OPTION A:** exactly the two `__cause__` lines (+ the docstring line beside each) to
  ValueError, one commit (`495a26b`); B and C declined.
- **V8 RELEASED (CHARC; AD-11 amended on main `df21ab0`):** k = 1 EXACT; k > 1 on real-sized
  content (>= 1080p): mean abs <= 1/255; p99 <= 2/255 at k = 2, <= 4/255 at k = 4; p99.9 and
  max recorded, never asserted; small stills and synthetic noise outside V8's domain; both k,
  both crops (GX011625 24.925 s and 114.648 s), both methods. Test `6102c6c`
  (`tests/test_methods_assembly_v8.py`), table in the report (tightest: p99 3.25/255 at k = 4,
  0024.925, c3). Note: on the 114.648 crop the AD-4 floor binds at full resolution (range
  0.0165), so its product rows differ from round-0's unfloored prototype rows.

Probe-derived figures for the report: `C:\Users\rwsmy\clearwater-review-evidence\wp3.4\figures\`
(`figures.py`, `figures.txt`).

## Cumulative round ledger

| round | depth (dispatcher) | critical | major | minor | in / out envelope | NEW / REOPENED | reverts | fixes: product / test-only | transport, CLI |
|---|---|---|---|---|---|---|---|---|---|
| 0 (design) | 192,064 | -- | -- | -- | -- | -- | -- | -- | -- (no review round; design table + rulings) |
| build (cell 2) | 346,044 | -- | -- | -- | -- | -- | -- | -- | -- (no review round; build + rulings applied; re-seat) |
| full pytest (cell 2) | 368,709 | -- | -- | -- | -- | -- | -- | -- | -- (3868 passed, 2 skipped; hand-off to cell 3) |
| 1 (cell 3) | 98,061 | 0 | 0 | 3 | 2 in / 1 out (F1) | 3 NEW / 0 | 0 | F1 product + test `c21ae64`; F2 docstring-only (granted) `7089198`; F3 report `fdc9f94` | WSL, codex-cli 0.162.1, gpt-5.6-sol high; 17 succeeded; VERDICT NO_NEW_CRITICAL_MAJOR -> TERMINATES |

### Round 1 (cell 3, 2026-10-21) -- verdict NO_NEW_CRITICAL_MAJOR (ROUND_TERMINATION)

Head `dd8bfa4`; evidence `C:\Users\rwsmy\clearwater-review-evidence\wp3.4\r1\` (prompt, diff,
transcript, `adjudication.md`, `md5sums.txt`). One echoed `ERROR` (the sandbox could not launch the
Windows venv), not transport. Findings (all MINOR, all CONFIRMED):

- **F1** (OUT of envelope): `_checked_record` lets OverflowError escape for a huge Python int
  (reproduced: `[10**400, .5, .5]` -> OverflowError). Cleanup: catch it as the Y-2 ValueError + test.
- **F2**: the WP3.2/WP3.3 `_derived_sigma` docstrings (`compensation.py:271`, `fusion.py:428`)
  still describe an OverflowError from `check_sigma`, false since DR-38 (d). Outside the granted
  lines: recommend a docstring-only grant; else bank.
- **F3**: the report's status line is stale (full pytest ran green). Cleanup.

No change made in the adjudicating turn.

Rulings (orchestrator, FINAL): convergence at round 1 CONFIRMED; F1 and F3 fixed as proposed; F2
GRANTED docstring-only. Cleanup commits `c21ae64` (F1; the Y-2 test fails on the unfixed code with
the OverflowError, passes after), `7089198` (F2), `fdc9f94` (F3). Static gates green (ruff check,
ruff format --check, mypy 109 files); `test_methods_assembly.py` 76 passed; the step files'
`-k "overflow or sigma"` 20 passed.

Self-found (test-only, ruled FINAL by the orchestrator): 12 `assert a.tobytes() == b.tobytes()`
made pytest diff ~580 KB byte strings at `-v` whenever a planted test expected the failure (one
test > 100 s at `-v`, 2 s at `-q`; the six package files 35 min at `-v`). Replaced by
`assert_same_bits` (dtype, shape, bytes; short message with the count of differing elements and
the max abs difference): the six files at `-v` now 323 passed in 93 s.
