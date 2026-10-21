# WP3.4 -- Method assembly: stages and parameter schema (report)

Brief `docs/briefs/wp3.4-brief.md` (FINAL, CHARC rulings `53d1d906e47fe2c9`); round-0 table and
rulings in `docs/proofs/wp3.4-ledger.md` (orchestrator, generation 9). Branch `wp3.4`, base
`de206e2`. Stack as locked: NumPy, SciPy and CuPy 14.x per `uv.lock`.

**Status: DRAFT for Reviewer A round 1.** Open: the EXCLUSIVE speed row and memory re-check
(task 8, windows not yet granted) and full pytest (in a window).

## What was built

| Path | Content |
|---|---|
| `src/clearwater/methods/ancuti_fusion.py` | `AncutiFusionMethod` (IF-3; one class, two instances), `C3_STAGES`, `ANCUTI2018_STAGES`, `STATISTIC_SHAPES`, `blend_with_original` |
| `src/clearwater/methods/schema.py` | `C3_PARAMETERS`, `ANCUTI2018_PARAMETERS`, `resolve_parameters` |
| `src/clearwater/methods/__init__.py` | `available_methods()` (c3 first), `AncutiFusionMethod` |
| `src/clearwater/core/backend.py`, `core/__init__.py` | `backend_for(device)` (question 2); DR-37 (a); DR-38 (c), (d) |
| `src/clearwater/core/ops.py`; `methods/fusion.py` (four lines) | DR-37 (b): helpers typed `CoreBackend`; `cast(CoreBackend, backend)` at the four call sites (type-only) |
| `tools/core_speed.py` | `--whole` and `--memory` legs (question 7); DR-37 (d), (e) |
| `tests/test_methods_assembly.py` | contract: IF-3, stages, dependencies, V1, Y-2, closed form, render, D99, blend, DR-38 (a), (b), DR-40 (a), schema, DR-19, planted wrong implementations, dependency rule |
| `tests/test_methods_assembly_prototype.py` | analyze and render against the prototype; CPU against GPU; N10; V9 |
| `tests/test_methods_assembly_v8.py` | V8 at method level (AD-11 as amended 2026-10-21) |
| `tests/test_core_wp34.py`; `tests/test_core_speed.py` (extended) | the core fixes and `backend_for`; the instrument |
| GRANTED outside the owned list (orchestrator rulings 2026-10-21) | `tests/test_core_select.py`: `name="cupy"` in `test_cupy_not_installed`'s fixture (DR-37 a); `tests/test_methods_compensation.py` and `tests/test_methods_fusion.py`: the two `__cause__` assertion lines and the docstring line beside each, OverflowError -> ValueError (DR-38 d, option A) |

Public API: `clearwater.methods.available_methods() -> dict[str, CorrectionMethod]`
(`{"c3": ..., "ancuti2018": ...}`, new instances per call); `AncutiFusionMethod("c3" |
"ancuti2018")`; `clearwater.core.backend_for(device: str) -> CoreBackend`.

## Stage tables

Records are float64 host `numpy` arrays (Y-1 a), shapes in `STATISTIC_SHAPES`.

| method | stage | statistics (shape) | smoothed | depends_on_parameters | depends_on_stages | source_only |
|---|---|---|---|---|---|---|
| c3 | white_balance | means (3,), gains (3,) | both | kappa, lambda_, c3_strength, c3_kernel_fraction, c3_mask_threshold, c3_mask_smooth_fraction | () | False |
| c3 | fusion | bounds (2,), saliency_means (2, 3) | both | white_balance_strength, max_white_balance_gain, sharpen_blur_fraction, normalisation_low, normalisation_high, gamma, sharpen_strength | white_balance | False |
| ancuti2018 | compensation | means (3,), cap_statistics (2,) [red, blue], alpha (2,) [red, blue] | means, alpha | alpha, blue_compensation, red_gain_cap, blue_gain_cap | () | True |
| ancuti2018 | white_balance | means (3,), gains (3,) | both | () | compensation | False |
| ancuti2018 | fusion | bounds (2,), saliency_means (2, 3) | both | as c3's fusion | compensation, white_balance | False |

c3's stages equal the frozen `stubs.C3_STAGES` (test). Dependencies follow the frozen tuple's
transitive convention: a parameter reaches a stage through the stages it depends on
(`test_dependencies_are_complete` measures it: with the earlier records fixed, every declared
parameter changes its stage, every parameter that changes a stage is declared by it or
upstream, and the five render-only parameters -- `laplacian_fraction`,
`saliency_blur_fraction`, `weight_delta`, `pyramid_min_level_size`, `blend_with_original` --
change none). `alpha[1]` is 0.0 when blue compensation is off.

## Y-1 statistics contract (text identical to WP3.11's report)

> **Q1 (Y-1) RULED as recommended**, and it is an IF-3 READING, not an amendment:
> `closed_form` is non-None only for the `source_only` compensation stage; WB `gains` are
> pre-strength/pre-clamp, applied in `render` after smoothing; Ancuti `alpha` is capped per
> frame and smoothed as a value.
>
> (a) `analyze` returns every name of the stage's `Stage.statistics` for that frame,
> render-ready (as `clearwater.gui.imaging.measure_statistics` on main already relies on), as
> float64 host arrays of a fixed shape per name; (b) white balance `gains` are the gray-world
> gains BEFORE the strength and the D99 clamp (the prototype `Statistics.white_balance_gains`;
> WP3.2 consumer note "`applied_gains` takes the smoothed gray-world gains"); strength and clamp
> are applied inside `render` and inside later stages' `analyze`, after smoothing (AD-6), which
> is why the frozen `C3_STAGES` lists them only under `fusion`; (c) Ancuti `alpha` is the
> capped alpha per frame, smoothed as a value (AD-6, WP1.4b claim 10); (d) `closed_form`
> returns the full record with every parameter-dependent name recomputed from the measured
> names, or None when the stage's measurement depends on parameters or earlier stages: in v1
> non-None only for Ancuti `compensation`; (e) Ancuti `compensation` is the only `source_only`
> stage; the engine caches the record `analyze` returned and never uses a cached record without
> passing it through `closed_form` with the current parameters.

(Quoted from the brief's ruling and question 1; the dispatcher relays it to WP3.11 for
identity.) Y-2: `analyze` (the consumed earlier records), `render` (every stage) and
`closed_form` (`measured`) refuse a record that lacks a declared name, carries another, holds
another shape, a non-finite value or no numbers, with one ValueError naming the stage and the
statistic; a missing stage is a KeyError naming it (stub parity); a key that is not a stage of
the method is a ValueError.

## Schema

Order: Basic in spec 6.7 order, Advanced in 6.7 order, then the rest. Ranges as ruled at round 0
(R0-3). Every default is the prototype `Params()` (AD-8); neutral = `Params.neutral()` for the
six V9 controls, the default elsewhere. A = ancuti2018 only, c3 = c3 only.

| name | type | default | min | max | panel | method | neutral | nullable | label |
|---|---|---|---|---|---|---|---|---|---|
| alpha | float | 1.0 | 0 | 2 | basic | A | 0.0 | | Compensation strength |
| c3_strength | float | 1.0 | 0 | 2 | basic | c3 | 0.0 | | Compensation strength |
| blue_compensation | bool | False | - | - | basic | A | False | | Blue compensation |
| white_balance_strength | float | 1.0 | 0 | 1 | basic | both | 0.0 | | White balance strength |
| sharpen_strength | float | 1.0 | 0 | 2 | basic | both | 0.0 | | Sharpening strength |
| blend_with_original | float | 0.0 | 0 | 100 | basic | both | 0.0 | | Blend with original (%) |
| red_gain_cap | float | 2.0 | 0 | 10 | advanced | A | 2.0 | yes | Red gain cap |
| blue_gain_cap | float | 2.0 | 0 | 10 | advanced | A | 2.0 | yes | Blue gain cap |
| kappa | float | 1.0 | 0 | 3 | advanced | c3 | 1.0 | | Kappa (red-green) |
| lambda_ | float | 0.7 | 0 | 3 | advanced | c3 | 0.7 | | Lambda (blue-yellow) |
| max_white_balance_gain | float | 3.0 | 1 | 10 | advanced | both | 3.0 | | Maximum white balance gain |
| gamma | float | 1.5 | 0.1 | 4 | advanced | both | 1.0 | | Gamma |
| pyramid_min_level_size | int | 16 | 1 | 256 | advanced | both | 16 | | Pyramid minimum level size |
| c3_kernel_fraction | float | 0.05 | 0.005 | 0.25 | advanced | c3 | 0.05 | | 3C local mean size |
| c3_mask_threshold | float | 0.85 | 0 | 1 | advanced | c3 | 0.85 | | 3C highlight threshold |
| c3_mask_smooth_fraction | float | 0.01 | 0.001 | 0.1 | advanced | c3 | 0.01 | | 3C mask smoothing |
| sharpen_blur_fraction | float | 0.005 | 0.0005 | 0.05 | advanced | both | 0.005 | | Sharpening blur size |
| normalisation_low | float | 0.5 | 0 | 100 | advanced | both | 0.5 | | Stretch low percentile |
| normalisation_high | float | 99.5 | 0 | 100 | advanced | both | 99.5 | | Stretch high percentile |
| laplacian_fraction | float | 0.001 | 0.0001 | 0.02 | advanced | both | 0.001 | | Contrast weight scale |
| saliency_blur_fraction | float | 0.003 | 0.0005 | 0.05 | advanced | both | 0.003 | | Saliency blur size |
| weight_delta | float | 0.1 | 0.001 | 1 | advanced | both | 0.1 | | Weight regularisation |

D49 by construction: c3's schema has no `alpha`, `blue_compensation` or cap; ancuti2018's no
`kappa`, `lambda_`, `c3_*`. "Compensation method" (6.7) is the method choice (IF-9
`ParameterSet.method`), not a parameter. DR-13: `laplacian_fraction` placed in Advanced at
0.001; no recalibration.

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

At method level (WP3.4) the schema completes it: `resolve_parameters` runs at the start of
`analyze`, `render` and `closed_form`, before any array work. A missing name takes its default
(IF-9 sets may be partial; a `float` given as an `int` becomes a `float`); then IF-9
`validate_parameter_set` against the method's own schema, whose first problem is ONE ValueError
`"<method>: <IF-9 message>"` naming the parameter (an unknown name -- another method's
parameter included --, a wrong type, None where not nullable, a non-finite value, a value
outside the inclusive bounds); then the one relation bounds cannot say, `normalisation_low <
normalisation_high`, as ONE ValueError naming `normalisation_low` with both values. Under the
ruled bounds every derived sigma is positive and its radius far inside the core's bound for
any image from 1 x 1 to 48 MP (0.25 x 8000 px x 4 = 8000 px), and no product of controls
leaves the float32 range, so X-4's step errors are unreachable from a valid set.

DR-19 items: (1) validation is method-scoped (each method's schema; `test_types_and_unknown_
names_refused` refuses the other method's names) -- CLOSES; (2) one ValueError, no other output
-- CLOSES (`test_every_bound_refused_with_one_error_naming_the_parameter`); (3) does not recur
(`check_sigma` bounds the integer radius); (4) held by the core's input checks; (5) the
transcript's wrong implementations that concern the schema, as tests: over-range `kappa`,
`lambda_`, `c3_strength` (every bound of every number, both methods); ints accepted for EVERY
float, not special-cased; legal large values and both inclusive bounds accepted and rendered;
the spatial bounds checked at 1 x 1, 4K, 5.3K and 48 MP (`test_dr19_spatial_bounds_hold_at_
every_size`); the blue cap shown on the rendered pixels (the render equals the step composition
from a record with capped blue alpha). DR-19 closes at this accept.

## Claims and evidence

1. **IF-3 conformance and registry** (`test_registry_c3_first_new_instances`,
   `test_c3_stages_equal_the_frozen_stub`, `test_ancuti_stage_table`, mypy on the stubs'
   form): both instances satisfy `CorrectionMethod`; ids `c3`, `ancuti2018`; c3 first.
2. **V1 staged ordering**: each later stage is measured on the image corrected with the
   SUPPLIED earlier records (`test_v1_stage_measured_with_the_supplied_earlier_records`, an
   altered compensation record and altered gains change the measured means and bounds exactly
   as the step composition says); a missing earlier stage is refused by name. Planted "earlier
   ignored" and "stage on the uncorrected image" fail.
3. **Closed form** bit-identical to re-analysis for six parameter sets (cap binding, caps None,
   blue on, alpha 0, cap 0); None for every other stage. Planted "closed form from stale
   parameters" fails.
4. **Render measures nothing and uses the supplied records**: equal bit for bit to the WP3.2/
   WP3.3 step composition on records unlike the frame's own (gains above the D99 clamp, alpha
   not the closed form of the means, shifted bounds and saliency means); no host read on the
   CPU counter; on the GPU under `cupyx.allow_synchronize(False)`. Planted "clamp skipped",
   "alpha from smoothed means", "render measuring the bounds" (with a host read the product
   never makes) and "strength or clamp before smoothing" fail.
5. **Blend**: 100 % returns the input bit for bit, 0 % the corrected image, 50 % the midpoint;
   planted inversion fails. Output float32 in [0, 1], same device and colour description, a
   `Frame` keeps its pts.
6. **Host reads per frame (DR-38 a)**: counted per stage on the CPU and on the GPU (with every
   other read made impossible): ancuti2018 compensation 3, white_balance 1, fusion 3 (7); c3
   white_balance 1, fusion 3 (4); render 0.
7. **Grey inputs (DR-38 b)**: all-black and all-white images give both weight maps 1/2 within
   1e-6 at method level, both methods; the output stays flat.
8. **Against the prototype** (`tests/test_methods_assembly_prototype.py`, both methods, four
   parameter sets, two scenes and the six WP2.3 stills): `analyze` against
   `prototype.temporal.statistics_of` -- means, cap statistics, alpha, white-balance means and
   gains bit-identical; bounds = the prototype's float64 bounds rounded to float32 exactly;
   saliency means equal to the prototype's chain given the bounds the product stretches over.
   `render` against `pipeline.correct` with the same `Statistics` hook record: **bit-identical
   in every case**, the floor-binding stills included (the prototype given the floored bounds,
   as WP3.3). Against the UNFLOORED prototype at the defaults the stills differ where the
   AD-4/DR-14 floor binds (their sharpening sigma is 0.32 px): max 25.7-61.7/255 (c3) and
   25.7-45.6/255 (ancuti2018) on the gradient and low-red stills, 0 on the uniform stills and on
   the textured scene (`C:\Users\rwsmy\clearwater-review-evidence\wp3.4\figures\figures.txt`).
9. **CPU against GPU (AD-11)**: render from the same records, max 1.8e-6 and mean 1.5e-6 at
   worst over the stills and scene (bound 2e-3 / 2e-4); statistics (non-Lab) within 6e-8.
   Same device twice bit-identical on each device (N10).
10. **V9 at method level**: `Params.neutral()` values give the input with **max 0 and mean 0**
    (exactly) on all six stills and the scene, both methods, CPU and GPU (bound 2/255, 0.2/255);
    a control off its neutral value misses the bound (planted). Blend 100 returns the input.
11. **Schema** (claims in "Schema" and "DR-19 rule"); planted default off AD-8, cap in c3's
    schema, neutral off `Params.neutral()`, `laplacian_fraction` in Basic all fail by name.
12. **Core fixes**: `backend_for` (cpu without importing CuPy; the probed GPU; ValueError
    naming the device and the probe's reason otherwise). DR-37 (a): "not installed" only for a
    `ModuleNotFoundError` with `name == "cupy"`; every other import failure "failed to load"; no
    new reason string. DR-38 (c): `check_rgb` refuses an empty spatial size. DR-38 (d):
    `check_sigma` raises ValueError for a radius that overflows. DR-37 (b): helpers typed
    `CoreBackend`.
13. **V8** (section below): k = 1 exact; k = 2, 4 within the amended AD-11 on both crops.
14. **Dependency rule**: importing `clearwater.methods` and building the methods loads nothing
    from `clearwater.io`, `.jobs`, `.gui`, `.config`, `.analysis`, nor PIL, av, PySide6, cupy.

## V8 at method level

AD-11 as amended 2026-10-21 (CHARC, main `df21ab0`): k = 1 EXACT; for k > 1 on real-sized
content, mean abs within 1/255 and p99 within 2/255 at k = 2, 4/255 at k = 4; p99.9 and max
are characterisation. `tests/test_methods_assembly_v8.py` asserts both k on both crops (the
centre 1080 x 1920 crops of the GX011625 look-check frames at 24.925 s and 114.648 s, from the
working folder's `wp1.3/frames`; skipped when absent), both methods, CPU and GPU, through
`gui.imaging`'s `downscale` and `render_host` with the crop's own records for both renders; the
GUI's `preview_export_difference` gives the same figures; a planted limited-range preview
fails. Product, CPU, values in /255
(`C:\Users\rwsmy\clearwater-review-evidence\wp3.4\figures\v8.txt`):

| crop | method | k | mean | p99 | p99.9 | max | bound (mean / p99) |
|---|---|---|---|---|---|---|---|
| 0024.925 | c3 | 1 | 0 | 0 | 0 | 0 | exact |
| 0024.925 | c3 | 2 | 0.086 | 0.929 | 8.411 | 29.426 | 1 / 2 |
| 0024.925 | c3 | 4 | 0.246 | 3.253 | 12.176 | 25.964 | 1 / 4 |
| 0024.925 | ancuti2018 | 1 | 0 | 0 | 0 | 0 | exact |
| 0024.925 | ancuti2018 | 2 | 0.086 | 0.892 | 7.737 | 28.930 | 1 / 2 |
| 0024.925 | ancuti2018 | 4 | 0.250 | 2.883 | 11.306 | 24.733 | 1 / 4 |
| 0114.648 | c3 | 1 | 0 | 0 | 0 | 0 | exact |
| 0114.648 | c3 | 2 | 0.085 | 0.471 | 2.781 | 29.376 | 1 / 2 |
| 0114.648 | c3 | 4 | 0.292 | 1.363 | 4.438 | 22.642 | 1 / 4 |
| 0114.648 | ancuti2018 | 1 | 0 | 0 | 0 | 0 | exact |
| 0114.648 | ancuti2018 | 2 | 0.091 | 0.505 | 2.732 | 27.437 | 1 / 2 |
| 0114.648 | ancuti2018 | 4 | 0.305 | 1.359 | 4.166 | 23.576 | 1 / 4 |

The 0024.925 rows equal round-0's prototype figures. The 0114.648 rows differ from them because
the AD-4 floor binds on that crop at full resolution (N{} range 0.0165 < 0.02; the round-0 probe
ran the unfloored prototype); the product's rows are the V8 figures. The tightest margin is
p99 3.25/255 against 4/255 (0024.925, c3, k = 4).

## Speed row and memory re-check -- PENDING (EXCLUSIVE windows)

Instrument ready (`tools/core_speed.py --whole`, `--memory`; smoke-run on the 320 x 180 fixture
clip only). Bar: D106's interim figure, 25 min/min = 0.834 s per frame at 30000/1001 fps for
the whole export; the row reports the core's share.

## Consumer notes

- **WP3.11.** Call `analyze` per stage in order with the SMOOTHED records of the stages before
  (D97); store what it returns (Y-1 a); smooth exactly `Stage.smoothed` (Ancuti's
  `cap_statistics` is not smoothed and render does not read it). Before using a cached
  `compensation` record, pass it through `closed_form` with the current parameters (Y-1 e); for
  every other stage `closed_form` returns None. Invalidate transitively: a parameter reaches a
  stage through `depends_on_stages`. The five render-only parameters invalidate no stage.
- **WP3.17.** Panels from `parameters` in their order; Basic then Advanced. `blend_with_original`
  is a percent (0..100, label "Blend with original (%)"). The caps are `nullable` (a disable
  control); c3 has none (D49). `pyramid_min_level_size` is an int. Errors arrive as one
  ValueError `"<method>: <name>: ..."`.
- **WP3.14.** `render(image, params, statistics)` returns a new `Image` (a `Frame` stays a
  `Frame`) on the image's device; the backend is `backend_for(image.device)`, so upload the
  pixels with that backend. Params may be partial.
- **WP3.21.** Sync points: the measuring steps only (claim 6); render makes none. Render
  uploads per call (DR-40 b): white-balance gains 1, saliency references 2, and c3's YCbCr
  inverse 1 (c3 4, ancuti2018 3). Intermediates are dropped as consumed.

## Debt dispositions

DR-19 CLOSES (above). DR-37 (a), (b) CLOSE; (d), (e) CLOSE (`tools/core_speed.py`); (c) not
this package's. DR-38 (a), (b) ADDRESSED by tests; (c) CLOSES; (d) CLOSES -- the WP3.2/WP3.3
tests pinned the root cause the fix removes (two `__cause__` assertions expected the
OverflowError); they now expect the core's ValueError (granted, option A). DR-40 (a)
CLOSES by `test_dr40a_np_float_alpha_reaches_the_result` (`compensation.py` unchanged); (b)
recorded by the speed row (pending), the fix stays WP3.21's. DR-13 placement only, stays OPEN.

## Limits

- Product against prototype is shown on 64 x 96 stills and synthetic scenes up to 180 x 270;
  the 4K agreement of the steps is WP3.2's and WP3.3's (their evidence).
- The memory and speed figures are pending.
- V8 is shown on two 1080 x 1920 crops of one clip (the ruled content); the frames live in the
  working folder, so the test skips on a machine without them.
