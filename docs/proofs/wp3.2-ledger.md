# WP3.2 ledger -- channel compensation and white balance

Cell: wp32-cell (implementer, opus-high), tier STRONG. Worktree `.worktrees/wp3.2`, branch
`wp3.2`, base main `2c5540a`. Brief `docs/briefs/wp3.2-brief.md` (FINAL, rulings CHARC
`53b752a4d7fac4fc`). Worktree clean at dispatch (no foreign change).

## Round 0 -- function table (brief task 1)

Grounded on the installed stack at base: NumPy 2.5.4, SciPy 1.18.1, CuPy 14.2.0. Read:
IF-1 `Array` (float32 `(H, W, 3)` RGB in [0, 1], `interfaces/image.py:17`), IF-2,
`clearwater.core` (`backend.py`, `ops.py`), WP3.1 report "Conventions fixed here" and
"Consumer notes", AD-6, AD-7, AD-11, frame section 2, and the prototype
`compensate_ancuti2018` (`pipeline.py:395`), `compensate_c3` (`:478`), `white_balance`
(`:531`), `_channel_means` (`:1186`), `_cap_statistic` (`:1198`), `_mean_added` (`:1218`),
`check_statistics` (`:202`), `Statistics` (`:162`), `check_derived_values` (`:361`).

Facts measured on the stack (scratch probe, not product code):

- NEP 50: `cupy float32 * 2.0` (Python float) is float32; `* np.float64(2.0)` is **float64**
  (the "float64 leak" planted defect is real on both devices).
- `cupyx.allow_synchronize(False)` raises `DeviceSynchronized` on `float(a.mean())` and on
  `cupy.asnumpy`; it does NOT raise on a host-to-device `cupy.asarray(numpy)` nor on the
  elementwise kernels used here. Usable as the Gate 1 instrument for render functions (it warns
  that it is deprecated and "not reliable"; the test also counts calls to the core sync helpers).
- `rgb_to_ycbcr_matrix("bt709")` is built with the same expressions as the prototype's
  `RGB_TO_YCBCR` (`kg = 1 - kr - kb`), and `_conversion` casts `forward.T` to float32 as the
  prototype's `_constants`; the 3C forward conversion through IF-2 is the prototype's matmul.

### Proposed product functions (X-1)

All take the backend first (a `CoreBackend`, DR-37 b), the array second, every parameter
keyword-only with NO default, names = the prototype `Params` fields (X-1 a, b). Channel keys are
the prototype `Statistics.compensation_alpha` keys `"red"`, `"blue"`.

| # | Product function (module) | Kind | Prototype counterpart | Bit identity expected |
|---|---|---|---|---|
| F1 | `cap_statistics(backend, a, *, blue_compensation) -> dict[str, float]` (compensation) | measure; 1 sync point per channel (`core.mean`) | `_cap_statistic((1.0 - image[..., c]) * green)` per channel in `compensate_ancuti2018` | CPU yes, GPU yes (same expression, same `mean(dtype=float64)`) |
| F2 | `effective_alphas(*, means, cap_statistics, alpha, blue_compensation, red_gain_cap, blue_gain_cap) -> dict[str, float]` (compensation) | closed form, pure Python | the `added_per_alpha` / `min(alpha, cap * mean_c / added_per_alpha)` block, `pipeline.py:461-464`; red uses `red_gain_cap`, blue `blue_gain_cap` (D52); None disables (D100, AD-26) | exact (same float64 Python arithmetic) |
| F3 | `compensate_ancuti2018(backend, a, *, means, alphas) -> Array` (compensation) | render; no whole-frame read; compensates exactly the channels keyed in `alphas` (`"red"` required, `"blue"` iff blue is on, D51) | `compensate_ancuti2018(image, params, Statistics(compensation_means=..., compensation_alpha=...))` | CPU yes, GPU yes |
| F4 | `compensate_c3(backend, a, *, kappa, lambda_, c3_strength, c3_kernel_fraction, c3_mask_threshold, c3_mask_smooth_fraction) -> Array` (compensation) | render only (3C has no whole-frame statistic; no cap, D49); validates its two fractions (X-4) before array work | `compensate_c3(image, params)` (image part) | CPU yes, GPU yes |
| F5 | `gray_world_gains(means) -> tuple[float, float, float]` (white_balance) | closed form: `target / max(mean_c, 1e-6)`, `target = sum(means) / 3` | `white_balance` lines 567, 576 (and 573-574 for supplied means) | exact |
| F6 | `applied_gains(gray_world, *, white_balance_strength, max_white_balance_gain) -> tuple[tuple[float, float, float], tuple[bool, bool, bool]]` (white_balance) | closed form: requested `1 + s * (g - 1)`, applied `min(requested, max)`, clamped `requested > applied` (D99 after the strength; never inside a measure) | `white_balance` lines 577-578, 588 | exact |
| F7 | `apply_white_balance(backend, a, gains) -> Array` (white_balance) | render: `clip(a * gains_f32, 0, 1)` | `white_balance(image, params, Statistics(white_balance_gains=g))` with the strength 1 / no-clamp path, or directly lines 580-581 | CPU yes, GPU yes |

Measures with no product function of their own (X-1 c): the Ancuti compensation means and the
white-balance means are `clearwater.core.channel_means(backend, a)` (1 sync point, 3 scalars),
called by WP3.4 on the step's INPUT (the compensation input; the compensated image for white
balance). The prototype records (`CompensationInfo`, `WhiteBalanceInfo`, `_mean_added`) are not
ported (ruling 5); F6 returns the clamped flags.

### Elementwise operations and their `xp`-free replacement (X-3)

| Function | Prototype operation | Product operation | Same operation? |
|---|---|---|---|
| F1 | `(1.0 - image[..., c]) * green` | same operators | yes |
| F1 | `_accumulate_mean(shape)` = `shape.mean(dtype=float64)` | `clearwater.core.mean(backend, shape)` (same call, `ops.py:308`) | yes |
| F3 | `out = image.copy()` | `a.copy()` (array method) | yes |
| F3 | `(alpha * difference) * shape`, Python-float scalar times float32 | same operators | yes |
| F3 | `xp.clip(image[..., c] + ..., 0.0, 1.0)` | `(a[..., c] + ...).clip(0.0, 1.0)` | yes (`np.clip`/`cupy.clip` dispatch to the method) |
| F3 | `out[..., c] = ...` | same item assignment | yes |
| F4 | `rgb_to_ycbcr(image)` = `image @ RGB_TO_YCBCR.T.astype(f32)` | `backend.rgb_to_ycbcr(a, "bt709", "full")` (IF-2; D47 whatever the source matrix) | yes (same matrix construction, same matmul) |
| F4 | `image.mean(axis=2, dtype=np.float32) > thr` | same array method and comparison | yes |
| F4 | `xp.where(bright, 0.0, 1.0)` (float32) | `(~bright).astype(np.float32)` | yes (same 0.0 / 1.0 values, NaN maps to 1 in both) |
| F4 | `_gaussian(x, s)` = `ndimage.gaussian_filter(x, (s, s), reflect, truncate 4)` | `backend.gaussian_blur(x, s)` (same call, `backend.py:291`) | yes |
| F4 | `-lambda_ * mask * G{Cb}`, `-kappa * mask * G{Cr}` | same operators | yes |
| F4 | `to_rgb = _constants(xp).ycbcr_to_rgb` (cached device copy of `inv(RGB_TO_YCBCR).astype(f32)`) | host `np.linalg.inv(rgb_to_ycbcr_matrix("bt709")).astype(np.float32)` uploaded by `backend.asarray` per call, then `[:, 1]`, `[:, 2]` | yes in value (same float64 inverse, same cast); one 36-byte upload per call instead of once per process (note N-1) |
| F4 | `delta_cb[..., None] * to_rgb[:, 1] + delta_cr[..., None] * to_rgb[:, 2]` | same operators | yes |
| F4 | `xp.clip(image + delta, 0.0, 1.0).astype(f32, copy=False)` | `(a + delta).clip(0.0, 1.0).astype(np.float32, copy=False)` | yes |
| F7 | `xp.array(applied, dtype=np.float32)` | `backend.asarray(gains)` (IF-2, float32) | yes in value (same Python float -> float32 rounding) |
| F7 | `xp.clip(image * gains, 0.0, 1.0).astype(f32, copy=False)` | `(a * gains).clip(0.0, 1.0).astype(np.float32, copy=False)` | yes |

No operation needs `xp` or a new `clearwater.core` helper (X-3: none found, as expected). No
substitute changes the arithmetic, so bit identity with the prototype is expected on BOTH
devices for every function; CPU against GPU differs only through the cupyx float32 Gaussian
(F4) and the float64 reduction order of the means (F1, measures), within AD-11 (to be measured).

### X-4 (DR-19) in F4

`compensate_c3` derives `spatial_sigma(a.shape, f)` for `c3_kernel_fraction` and
`c3_mask_smooth_fraction`, calls `clearwater.core.check_sigma(sigma)` and re-raises its
ValueError `from` it as `"<name>=<value!r> gives a sigma of <sigma:.6g> px at the short side
<n> px; <core message>"`, before any array work, with no other output. F1-F3, F5-F7 derive no
spatial value, so they validate no fraction (method-scoped by construction). Parameter ranges
are WP3.4's schema.

### Notes (not STOPs)

- N-1: device uploads. F4 uploads the 3x3 inverse and F7 the 3 gains on every call
  (`backend.asarray`; the prototype caches F4's, uploads F7's per call as here). A pageable
  host-to-device copy may wait on the stream; listed for WP3.21. Caching would need
  `CoreBackend.constant`, which the brief does not list as consumed.
- N-2: D2H sync points: F1 one per compensated channel (`core.mean`); the two `channel_means`
  calls WP3.4 makes (1 each). F3, F4, F7 read nothing back (Gate 1 test with
  `cupyx.allow_synchronize(False)` plus a call count on the core helpers).
- N-3: the X-4 message helper is private to `compensation.py`; WP3.3 carries its own copy of
  the same rule (no shared module is owned by either cell; WP3.4 may consolidate).

### STOP items (recommended answer first)

- **S-1 (input checks, a choice the brief leaves open).** Recommended: every function taking
  an array first requires a `CoreBackend` (TypeError otherwise, as the core helpers) and checks
  the array with `CoreBackend.check_rgb` (TypeError wrong device kind; ValueError not float32
  or not `(H, W, 3)`), so a float64 or NumPy-on-GPU input is refused, not propagated. No
  value-range ([0, 1]) check: IF-1 makes [0, 1] the producer's contract, and the prototype's
  `_check_image` costs two device-to-host reads (min, max) per step, against Gate 1.
  `check_rgb` is a public `CoreBackend` method (no `xp`) but is not in the brief's consumed
  list. Alternative: no check (a float64 input then yields a float64 output silently).
- **S-2 (X-1 exact list differs from the brief's example).** Recommended: the plural F1/F2
  above taking `blue_compensation`, `red_gain_cap`, `blue_gain_cap` (X-1 b's Params names),
  instead of the example's singular `cap_statistic(..., channel)` /
  `effective_alpha(..., channel, cap, ...)`, whose `cap` is not a Params name and leaves the
  D52 red-cap/blue-cap wiring outside WP3.2 (so the "one cap shared by red and blue" planted
  test would test nothing of WP3.2's). F2 reads `cap_statistics[c]` for the channels
  `blue_compensation` selects and ignores extra keys (WP3.4 may cache both, AD-7).
- **S-3 (supplied values, left open).** Recommended: F2, F3, F5, F6, F7 refuse a supplied
  value of the wrong length or keys, or a non-finite number, with one ValueError naming the
  argument (the prototype's `check_statistics` / `_supplied_triple` on the supplied record),
  since in the product every render takes supplied (smoothed) values. Pure Python, no sync.
- **S-4 (reading of the planted defect "the means taken after clipping").** Recommended
  reading: a step whose whole-frame values are measured on its clipped OUTPUT instead of its
  input (Ancuti means / cap statistic of the compensated image; white-balance means of the
  balanced image). Test: on an image where the clip binds, the measured values must equal
  `channel_means` / the cap statistic of the input, and the rendered output must equal the
  prototype's; the defect version (planted in the test) differs and fails by name.

## Cumulative round ledger

| Round | Depth (dispatcher) | Critical | Major | Minor | Info | In / out envelope | New / reopened | Reverts | Product / test-only fixes | Transcript |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 116,822 (R0 yield) | table only | | | | | | | | -- |
| 1 | (dispatcher) | 0 | 0 | 4 | 0 | 3 in / 1 out | 4 new / 0 reopened | 0 | planned: 2 product (error paths), 2 test-only | `C:\Users\rwsmy\clearwater-review-evidence\wp3.2\r1\` (md5s in `md5sums.txt`) |

Round-0 ruling (orchestrator gen 6): table ACCEPTED as committed in 73b1fea; S-1 to S-4 as
recommended; N-1 a WP3.21 consumer note (no `CoreBackend.constant`); N-3 private X-4 helper per
module, wording identical to WP3.3's.

## Build

- e22709a compensation module and tests; 1b75b71 white balance module and tests; bda5397 report.
- Prototype identity: 54 / 54 per-function rows max |diff| 0 on CPU and GPU; CPU vs GPU worst
  3.58e-07 max / 6.44e-08 mean (3C); `work/wp3.2/ad11.txt`.
- Own tests 376 passed; 193 passed / 183 skipped with cupy unimportable. Full suite: window
  queued by the dispatcher (host busy), not yet run.

## Round 1 (Reviewer A, head bda5397)

Transport WSL, codex-cli 0.162.1, gpt-5.6-sol / high; probe 1 `succeeded in`; review 11
`succeeded in`, tokens footer present, `VERDICT: NO_NEW_CRITICAL_MAJOR`. One `Reconnecting...
2/5` before the model's first output (recovered; flagged). The reviewer could not run pytest
(read-only sandbox): all REASONED. Adjudication: `r1\adjudication.md`.

1. MINOR in-envelope, CONFIRMED: mixed-type keys in `alphas` / `cap_statistics` give a
   TypeError from `sorted(...)` in the message, not the S-3 ValueError. Fix: product.
2. MINOR OUT-OF-ENVELOPE, CONFIRMED: `c3_kernel_fraction=1e308` on 1 x 1 leaks OverflowError
   from `clearwater.core.check_sigma`. Fix: product (`_derived_sigma` converts it); core root
   flagged (not owned).
3. MINOR in-envelope, CONFIRMED (test gap): a render calling `a.mean()` would pass. Fix: tests
   (a reduction-recording ndarray subclass and a planted control).
4. MINOR in-envelope, CONFIRMED (test gap): X-4 "before any array work" not guarded. Fix: tests
   (same subclass, zero ufunc calls before the error, planted control).

No new blocking finding: round 1 terminates the loop (if it counts); minors fixed once in cleanup.
