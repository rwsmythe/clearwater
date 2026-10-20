# WP3.2 -- Channel compensation and white balance (report)

Cell wp32-cell (implementer, opus-high), tier STRONG. Branch `wp3.2`, base main `2c5540a`.
Brief `docs/briefs/wp3.2-brief.md` (FINAL, CHARC `53b752a4d7fac4fc`); round-0 table and
rulings in `docs/proofs/wp3.2-ledger.md` (orchestrator ruling: table accepted, S-1 to S-4 as
recommended). Spec v0.5.4: 6.2 steps 1-2, 6.3.1, 6.3.2; D16, D39, D47-D52, D56, D99, D100,
D107; AD-6, AD-7, AD-8, AD-11, AD-20, AD-26.

## What was built

`src/clearwater/methods/compensation.py` and `src/clearwater/methods/white_balance.py`: step
functions on a `clearwater.core` backend, split into measure / closed form / render (X-1).
Every parameter is keyword-only with no default, named as the prototype `Params` field.

| Function | Kind | Prototype counterpart |
|---|---|---|
| `cap_statistics(backend, a, *, blue_compensation) -> dict[str, float]` | measure (source-only, AD-7); 1 sync point per channel | `_cap_statistic((1 - I_c) * I_g)` in `compensate_ancuti2018` |
| `effective_alphas(*, means, cap_statistics, alpha, blue_compensation, red_gain_cap, blue_gain_cap) -> dict[str, float]` | closed form; separate caps (D52), None disables (D100, AD-26) | `pipeline.py:461-464` |
| `compensate_ancuti2018(backend, a, *, means, alphas) -> Array` | render; channels = the keys of `alphas` (`"red"`, plus `"blue"` iff D51 is on) | `compensate_ancuti2018` with `Statistics(compensation_means, compensation_alpha)` |
| `compensate_c3(backend, a, *, kappa, lambda_, c3_strength, c3_kernel_fraction, c3_mask_threshold, c3_mask_smooth_fraction) -> Array` | render only (no statistic, no cap, D49); BT.709 full always (D47) | `compensate_c3` |
| `gray_world_gains(means) -> tuple[float, float, float]` | closed form, `target / max(mean_c, 1e-6)` | `white_balance` |
| `applied_gains(gray_world, *, white_balance_strength, max_white_balance_gain) -> (gains, clamped)` | closed form: strength, then the D99 clamp (upper only) | `white_balance` |
| `apply_white_balance(backend, a, gains) -> Array` | render, `clip(a * gains_f32, 0, 1)` | `white_balance` with `Statistics(white_balance_gains)` |

The compensation and white-balance means are `clearwater.core.channel_means` (1 sync point),
called by WP3.4 on each step's input. No record types (ruling 5); `applied_gains` returns the
clamped flags.

Consumed beyond the brief's list: `CoreBackend.check_rgb` (ruling S-1). Every function taking
an array requires a `CoreBackend` (TypeError otherwise) and checks dtype, shape and device kind.
**Not carried:** the prototype's `_check_image` [0, 1] range check (two host reads per step;
IF-1 makes the range the producer's contract), `check_derived_values` (replaced by X-4),
`CompensationInfo`, `WhiteBalanceInfo`, `_mean_added`.

## Claims and evidence

1. **Bit-identical to the prototype on both devices.** Measured per function (Ancuti chain,
   3C, white balance after 3C) on 9 inputs (two seeded synthetics, a 540 x 960 synthetic, the
   six WP2.3 stills `png16-*`, `png8-*`), blue off and on: 54 of 54 rows max |diff| = 0 on CPU
   and 0 on GPU (`work/wp3.2/ad11.txt`, script `work/wp3.2/measure_ad11.py`, uncommitted). The
   measures and closed forms equal the prototype's values exactly (`==` on Python floats).
   Tests: `test_*_match_prototype*` in both test files, including the render on supplied
   values through the prototype's `Statistics` hook.
2. **CPU against GPU within AD-11:** worst per-channel max / mean over the same 54 rows:
   Ancuti 0 / 0; 3C 3.58e-07 / 6.44e-08; white balance after 3C 3.58e-07 / 5.66e-08
   (AD-11: 2e-3 / 2e-4). The 3C deviation is the cupyx float32 Gaussian (WP3.1 claim 2).
   Same device twice: bit-identical (N10).
3. **V1 edge cases:** uniform images (gray: unchanged; coloured: uniform output equal to the
   prototype), near-zero red (mean 0: a cap of 2 * 0 stops compensation, None compensates;
   white balance hits the 1e-6 floor and the clamp binds at 3.0), 1 x 1, 1 x 7, 7 x 1, 7 x 5,
   2 x 3, 16-bit stills; the cap binding, not binding, None, and inert when `mean_g <=
   mean_c`; blue on and off (green, and blue when off, bit-unchanged); the 3C mask below, at
   (not bright) and above (bit-identical pixel) the threshold.
4. **V9 neutrality:** `alpha = 0`, `c3_strength = 0`, `white_balance_strength = 0` each return
   the input bit for bit on every input, both devices.
5. **Planted wrong implementations fail by name** (each check also passes the product): one
   cap shared by red and blue; the cap applied to 3C; the clamp before the strength; the gains
   clamped below 1 (floor at 1 and a symmetric `[1/max, max]` clamp); BT.601 in 3C; the mask
   threshold inverted; a float64 leak (Ancuti and white balance); the means taken after
   clipping (Ancuti on an image where the clip at 0 binds; white balance where the clip at 1
   binds). DR-19 item 5's list (WP1.2R Reviewer B, md5 `f1cc6cf8...`): the blue-cap item is
   covered on the rendered pixels (`test_capped_render_is_capped_on_the_pixels`); the
   size-independent fraction rule is defeated by a fraction usable at 10 px and refused at a
   6000 px short side (`test_support_bound_depends_on_the_short_side`); the other items are
   the schema's (WP3.4), the core's or the prototype's.
6. **Gate 1:** on the GPU the renders return `cupy.ndarray` float32 and run under
   `cupyx.allow_synchronize(False)` without a device synchronisation (the instrument is shown
   to fire on `cap_statistics`); call counts show `cap_statistics` reads one scalar per
   channel through `clearwater.core.mean` and the renders call no reduction helper.
7. **Dependency rule:** a subprocess import of both modules loads nothing from
   `clearwater.io`, `.jobs`, `.gui`, `.config`, nor `PIL`, `av`, `PySide6`, `cupy`, `cupyx`. The
   static test in `tests/test_core_deps.py` (no `xp`, no `cupy` outside `clearwater.core`)
   covers the new modules.
8. **Gates** (on the branch head): ruff check clean, ruff format --check clean, mypy strict
   clean; own tests 376 passed (CuPy importable), 193 passed / 183 skipped with `cupy` and
   `cupyx` unimportable. Full suite: see the ledger (granted window).

## DR-19 rule

X-4, as ruled (CHARC `53b752a4d7fac4fc`), the one rule shared with WP3.3:

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

In WP3.2 the rule applies to `compensate_c3` only (`c3_kernel_fraction`,
`c3_mask_smooth_fraction`); the message is
`f"{name}={fraction!r} gives a sigma of {sigma:.6g} px at the short side {n} px; {exc}"`, with
`exc` the `check_sigma` error. The Ancuti and white-balance steps derive no spatial value and
validate none. Tests: `test_unusable_fraction_raises_one_error_naming_it` (0, negative, NaN,
inf; no stdout, stderr or log record; `__cause__` is the core's error),
`test_support_bound_depends_on_the_short_side`, `test_validation_is_method_scoped`. Supplied
values (S-3): wrong length or keys, or non-finite, raise one ValueError naming the argument.
DR-19 stays OPEN until WP3.4's schema lands; WP3.2 discharges items (1) and (2) for its
parameters and item (5) for its steps.

## Consumer notes

- **WP3.4:** call `channel_means` on the step's input (never its output: the planted
  "means after clipping" tests show the difference). `effective_alphas` ignores extra
  `cap_statistics` keys, so both channels' statistics can be cached (AD-7). The capped alpha
  is the value AD-6 smooths; `applied_gains` takes the smoothed gray-world gains. The X-4
  message helper is private per module (also in WP3.3); WP3.4 may consolidate.
- **WP3.21 (N-1):** `compensate_c3` uploads the 3 x 3 inverse matrix and `apply_white_balance`
  the 3 gains on every call (`backend.asarray`, a host-to-device copy that may wait on the
  stream); the prototype caches the first. Sync points: `cap_statistics` (1 per channel),
  `channel_means` (1 per call).

## Deviations and limits

- None from the brief. `_compensated_channels` is a private helper (not in the round-0 table).
- `cupyx.allow_synchronize` is deprecated and "not reliable" by CuPy's own warning; the Gate 1
  test pairs it with call counts on the core reduction helpers.
- Not run off the envelope: other GPUs, other operating systems, multi-GPU.
