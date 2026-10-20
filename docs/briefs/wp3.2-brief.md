# WP3.2 — Channel compensation and white balance (dispatch brief, DRAFT)

**Status:** DRAFT (orchestrator gen 6, drafting helper), for CHARC approval. Owner decisions:
none inside the package (D100 was decided by the owner at CP4: caps KEPT, AD-26).
- Spec **v0.5.4**. Architecture FINAL 1.0 section 3 IF-2 and IF-3, section 4; AD-1, AD-6, AD-7,
  AD-8, AD-11, AD-20, AD-26. Frame `docs/briefs/wp2.4-phase3-frame.md` (sections 1-5; section 5
  maps "D100 caps kept, nullable" and "6.3 defaults" to this package). WP3.1 report
  `docs/reports/wp3.1-array-backend.md` ("Conventions fixed here", "Consumer notes"). D100,
  DR-19, DR-37 (b) (row "Debt and decided items").
- Cell: `implementer-opus-high`. Tier **STRONG**.
- Worktree `.worktrees/wp3.2`, branch `wp3.2`, base = the main commit named at dispatch.

**Why.** Plan 11.1's critical path runs WP3.1 → WP3.2 and WP3.3 → WP3.4. WP3.4 assembles the
IF-3 methods `c3` and `ancuti2018` (architecture section 3) from step functions; this package
provides the first two steps of spec 6.2 (channel compensation, white balance with the D99
clamp) on the merged `clearwater.core` backend, re-implemented against IF-2 with
`tools/prototype/pipeline.py` as the numerical reference (DR-19, architecture section 4).

| Field | Content |
|---|---|
| ID and title | WP3.2 — Channel compensation and white balance; plan Phase 3 row WP3.2 (size M); module `clearwater.methods` (plan 8.1: "Correction method plug-ins; v1 has one, Ancuti fusion with selectable compensation", built by WP3.2–WP3.4) |
| Goal | Step functions on an IF-2 backend for Ancuti 2018 red and optional blue compensation with separate, nullable gain caps, 3C with its mask, and gray-world white balance with the D99 clamp; each split into what is measured on a frame, what follows in closed form from parameters (AD-6, AD-7), and the per-pixel render from supplied values; bit-identical to the prototype on the same device or within AD-11, with the measured maximum reported. |
| Spec / decision clauses | 6.2 step 1 "**Channel compensation** (user-selectable; Section 6.3)"; step 2 "**White balance** — gray-world style balancing of the compensated image. **Gain clamp (D99):** each channel's white-balance gain is limited to a maximum (default 3.0, 0.5.4), set in the Advanced panel. The clamp applies with either compensation method, and to the gains actually used for rendering (the smoothed gains for video)." 6.3.1 "**Red:** `Irc = Ir + α·(Ḡ − R̄)·(1 − Ir)·Ig` (additive; channel values in [0, 1])"; "**Blue (optional, off by default; for turbid or plankton-rich water):** `Ibc = Ib + α·(Ḡ − B̄)·(1 − Ib)·Ig`"; "α is the compensation strength (paper default 1)"; "**Gain cap (global strength cap):** per image/frame, the effective strength is reduced so that the mean added amount does not exceed a set multiple of the channel's original mean. Red and blue have separate caps (D50, D52), default 2.0 each, disabled by an empty value (0.5.4, AD-8). Because the cap is computed from whole-frame statistics, it is smoothed over time along with them." 6.3.2 "**Working space:** YCbCr using a fixed BT.709 matrix, applied to the display-encoded working image (D47)"; "**Equations:** `Cr' = Cr − κ·M·G{Cr}`, `Cb' = Cb − λ·M·G{Cb}`, where G{} is a Gaussian local mean with large spatial support"; "**Mask M:** 0 where mean(R, G, B) > 0.85, 1 elsewhere, smoothed with a Gaussian; protects bright regions"; "**Kernel sizes:** expressed relative to image size (Section 6.6)"; "**Strength controls:** one Basic slider scales κ and λ together from the 1.0/0.7 ratio; κ and λ are individually adjustable in the Advanced panel (D48)"; "**Gain cap:** does not apply; cap controls are hidden when 3C is selected (D49). The white-balance gain clamp (Section 6.2) still applies." D16 "3C is the default"; D39 "Internal processing in 32-bit float; quantization only at export"; D47 "3C works in YCbCr using a fixed BT.709 matrix (internal only)"; D50 "Ancuti 2018 gain cap is a global strength cap: per image/frame, the mean added amount is limited to a set multiple of the channel's original mean"; D51 "Ancuti 2018 blue compensation included as an option, off by default"; D52 "Separate red and blue gain caps"; D56 "All spatial parameters size-relative (fraction of short side)"; D99 "White-balance gain clamp: a maximum per-channel white-balance gain, in the Advanced panel, applying with either compensation method"; D100 "*(decided 0.5.4)* Gain caps (D40, D50, D52) are a fidelity-versus-noise control, not a noise mitigation; **KEPT**"; D107 "Core is written so the same code runs on CPU or GPU from the start". Feeds V1 "unit tests for each stage (both compensation methods, red/blue compensation, gain caps, 3C mask and kernels, white balance and its gain clamp ...), including edge cases: uniform images, near-zero red channel, 10-bit input" and V9 "with every stage set to its neutral value (compensation and white balance strength 0 ...) each stage reduces to identity". AD-8 defaults: alpha 1.0, caps 2.0 (KEEP), blue off, kappa 1.0 / lambda 0.7, c3_strength 1.0, c3 kernel 0.05, mask threshold 0.85, mask smooth 0.01, white-balance strength 1.0, max white-balance gain 3.0. AD-6 (stages: Ancuti "(1) compensation means and effective alpha; (2) white-balance means and gains"; 3C "(1) white-balance means and gains"; "the capped alpha is smoothed as a value; strength and the D99 clamp apply after smoothing (closed form)"). AD-7 (source-only: "Ancuti stage 1 means and the cap statistic `mean((1 - I_c) I_g)`"; closed form: "alpha from the means and caps; gains from means, strength and clamp"). AD-20 amendment (`Parameter.nullable`, "None is legal ... (the gain caps, D52)"); AD-26 ("WP3.2 builds the caps as nullable parameters"). |
| Depends on | WP3.1 merged (accept `f4acbd0`: `clearwater.core` on main; no stub needed). WP2.2 (IF-1, IF-2, IF-3 frozen, `b288533`). WP2.3 stills: `png16-uniform-none`, `png16-gradient-none`, `png16-lowred-none`, `png8-uniform-none`, `png8-gradient-none`, `png8-lowred-none`. Runs in parallel with WP3.3 (no build dependency between them); the `clearwater.methods` package file is cross-brief question X-2. |
| Files owned | `src/clearwater/methods/compensation.py` (NEW), `src/clearwater/methods/white_balance.py` (NEW); `tests/test_methods_compensation*.py`, `tests/test_methods_white_balance*.py` (NEW); `docs/reports/wp3.2-compensation-white-balance.md`; `docs/proofs/wp3.2-ledger.md`. NOT owned: `src/clearwater/methods/__init__.py` (X-2), `src/clearwater/methods/fusion.py` (WP3.3), `src/clearwater/methods/ancuti_fusion.py` (WP3.4), `src/clearwater/core/` (WP3.1; read only, DR-37 b's trigger is WP3.4 or WP3.21), `src/clearwater/interfaces/`, `tools/prototype/` (read-only reference), `pyproject.toml` (no dependency), `tests/conftest.py`, `tests/fixture_plugin.py`. |
| Interfaces provided | No frozen interface. The step functions of X-1 (their names and signatures are tabled at round 0 for CHARC; WP3.4 builds on them). |
| Interfaces consumed | IF-1 `Array` (float32 `(H, W, 3)` RGB in [0, 1]); IF-2 `ArrayBackend` methods `asarray`, `to_host`, `gaussian_blur`, `rgb_to_ycbcr` (`"bt709"`, `"full"`: D47's fixed matrix whatever the stream's), `ycbcr_to_rgb`; `clearwater.core` helpers `spatial_sigma`, `channel_means`, `mean`, `rgb_to_ycbcr_matrix`, `check_sigma`. The helpers require a `clearwater.core` backend (`CoreBackend`; DR-37 b): tests use `NumpyBackend` / `CupyBackend`, never a protocol-only double. `channel_means` and `mean` return Python floats and are device-to-host sync points (the WP3.21 list in `docs/proofs/wp3.1-ledger.md`). `CoreBackend.xp` is NOT available outside `clearwater.core` (WP3.1 ruling 1.1; the static test in `tests/test_core_deps.py` scans all of `src/clearwater`). |
| Consumers | WP3.4 (wave 3: the IF-3 methods `c3`, `ancuti2018`, `ancuti2018-blue`, their stages, `analyze` / `render` / `closed_form`, the parameter schema). Boundary: WP3.4 owns the `Parameter` schema (names, ranges, `nullable`, panels, labels, neutral values) and its range validation, the stage and statistic names (the frozen `stubs.C3_STAGES` already names `"means"`, `"gains"`), smoothing and closed-form wiring, "blend with original", the method-level V9 test, the product memory-peak re-check and the whole-core speed row. WP3.2 owns the per-step numerics and their measure / closed-form / render split. Note: the `stubs.StubCorrectionMethod` docstring says "the schema is WP3.2's"; plan WP3.4 ("the parameter schema with Basic/Advanced placement") governs. |
| Hardware flags | `gpu` on every CuPy test (skips without a CUDA device or CuPy). No footage, no timing (the whole-core speed row is WP3.4's). |
| Out of scope | Fusion inputs, weights, the blend (WP3.3); the IF-3 method objects, the parameter schema and its validation, stages, smoothing, "blend with original" (WP3.4); any change to `clearwater.core` (a missing operation is a STOP, X-3); the info records of the prototype (`CompensationInfo`, `WhiteBalanceInfo`) beyond what X-1 rules; video colour conversion (WP3.5); optimisation (WP3.21); importing `tools/prototype` from `src/`; GoPro IMU/GPS (owner: out of scope). |
| Debt and decided items | **D100 / AD-26 — IMPLEMENTS, must not reopen:** the caps are KEPT; each cap is a separate value (D52) that may be None (disabled; AD-20 amendment `Parameter.nullable`, "None is legal ... (the gain caps, D52)"); dropping or merging them is a STOP. **DR-19 (OPEN) — PARTLY DISCHARGES, for this package's parameters only:** items (1) method-scoped validation of derived values and (2) the error-line contract are decided here under the one shared rule X-4 (also carried by WP3.3), stated in the report; item (3), the support bound, does not recur (WP3.1 bounds the integer radius `int(4 sigma + 0.5)` in `check_sigma`, WP3.1 report "Conventions fixed here"); item (4) is held by the core's input checks (WP3.1 R0-3) and the float32 percentile (R0-8); item (5), the named wrong implementations, is answered by this package's planted-defect tests where they concern compensation or white balance. DR-19 stays OPEN until WP3.4's schema lands; the accept record names what WP3.2 discharged. **DR-37 (b) — must not reopen:** the `clearwater.core.ops` helpers take a `CoreBackend`; tests never pass a protocol-only double. DR-37 (a) is WP3.16's / the next core touch, not this package's. |
| Done | Plan 4.5; frame section 2 rules 1-11; ruff check, ruff format --check, mypy strict (`src/clearwater`, `tools`), full pytest green with and without CuPy importable (in a granted window, X5); prototype agreement measured per function; V1 and V9 items covered; the X-4 rule stated in the report with its tests; Reviewer A converged. |

## Task ladder

1. **Read and table (round 0 yield).** Read IF-2, `clearwater.core` (`ops.py`, the
   "Conventions fixed here" of the WP3.1 report) and the prototype functions this package
   mirrors: `compensate_ancuti2018`, `compensate_c3`, `white_balance`, `_channel_means`,
   `_cap_statistic`, `_mean_added`, `check_statistics`, and the `Statistics` hook. Write in the
   ledger: each product function you propose (X-1), its prototype counterpart, which part is
   measure / closed form / render, every elementwise operation and the operator or array
   method that replaces each prototype `xp.` call (X-3), and whether bit identity with the
   prototype is expected on each device. YIELD for the dispatcher before product code. Anything
   the table cannot settle is a STOP.
2. **Ancuti 2018 (6.3.1, D50-D52, D100).** The measured values (channel means; the cap
   statistic `mean((1 - I_c) * I_g)` per compensated channel, float64-accumulated through
   `clearwater.core.mean`); the closed form (effective alpha per channel: `min(alpha, cap *
   mean_c / added_per_alpha)` when the cap is not None and `added_per_alpha > 0`, the
   prototype's rule; None disables the cap); the render from supplied means and alphas, green
   unchanged, clipped to [0, 1]. Blue only when asked (D51). Separate caps (D52).
3. **3C (6.3.2, D47-D49).** BT.709 full-range YCbCr by IF-2 regardless of the source's matrix
   (D47); `kappa = c3_strength * kappa`, `lambda = c3_strength * lambda_` (D48); mask 0 where
   `mean(R, G, B) > c3_mask_threshold`, smoothed by a Gaussian of `c3_mask_smooth_fraction`;
   G{} of `c3_kernel_fraction` (both through `spatial_sigma`, D56); Y unchanged and the output
   formed as `RGB + YCbCr_to_RGB @ (0, dCb, dCr)` as the prototype does, so a pixel with
   `M = 0` is bit-identical to its input. No cap (D49). 3C has no whole-frame statistic.
4. **White balance and the D99 clamp (6.2 step 2).** Measured: channel means of the
   compensated image. Closed form: gray-world gains `target / max(mean_c, 1e-6)`, requested
   `1 + s * (g - 1)`, applied `min(requested, max_white_balance_gain)` with the clamped flags.
   Render: `clip(I * gains, 0, 1)` with float32 gains. The clamp is applied to whatever gains
   reach the closed form (smoothed for video, AD-6), never inside the measure.
5. **Tests.**
   - Product against prototype (architecture section 4, WP3.1 ruling 6 form: computed in the test by calling the
     read-only `tools/prototype` on seeded synthetic inputs and the WP2.3 stills; no committed
     arrays): measure, closed form and render separately, the render through the prototype's
     `Statistics` hook (`compensation_means`, `compensation_alpha`, `white_balance_gains`);
     bit-identical where the round-0 table says so, else within AD-11 with the maximum
     reported.
   - CPU against GPU within AD-11 (max 2e-3 absolute per channel, mean 2e-4); same device twice
     bit-identical (N10).
   - V1 edge cases: uniform image, near-zero red channel (the 1e-6 floor; the clamp binds),
     1 x 1 and odd sizes, 16-bit-derived values (`png16-*`); the cap binding, not binding, and
     None; blue on and off; the 3C mask at, above and below the threshold.
   - V9 neutrality per step: `alpha = 0`, `c3_strength = 0`, `white_balance_strength = 0` each
     return the input bit for bit.
   - DR-19 under X-4: an unusable derived value (a 3C fraction whose sigma is not finite and
     positive, or whose support exceeds the core's bound, at the given image size) raises one
     ValueError whose message names the parameter; an Ancuti step never validates a 3C
     fraction and vice versa (method-scoped).
   - Planted wrong implementations fail by name: one cap shared by red and blue; the cap applied
     to 3C; the clamp applied before the strength; the gains clamped below 1; the BT.601 matrix
     in 3C; the mask threshold inverted; a float64 leak into the output; the means taken after
     clipping.
   - Gate 1 discipline (as WP3.1's Gate 1 section): on the GPU every function returning an
     array returns a `cupy.ndarray`; the only device-to-host reads are the documented sync
     points.
   - Dependency rule (plan 8.1, frame rule 5): a subprocess test that importing your modules
     loads nothing from `clearwater.io`, `.jobs`, `.gui`, `.config`, nor `PIL`, `av`, `PySide6`,
     `cupy`.

## Declared operating envelope

Windows 11; Python 3.12; NumPy, SciPy and CuPy (`cupy-cuda12x[ctk]` 14.x) as locked; one NVIDIA
RTX 4070 Laptop GPU, 8 GB (D117); images from 1 x 1 to 4K frames and 48 MP photos; parameter
values inside the ranges WP3.4's schema will set (the AD-8 defaults and the V9 neutral set
exercised). Out of envelope: parameter values a schema would refuse (negative caps, NaN
strengths; range validation is WP3.4's schema, derived values are X-4's), non-NVIDIA devices, other operating systems (portable, N1, not
run there), multi-GPU (DR-2).

## Review loop (Reviewer A), per `docs/review-gate-clearwater.md` Part 1

- Tier **STRONG**, run by you at your seat to convergence; five-round gate. Evidence
  `C:\Users\rwsmy\clearwater-review-evidence\wp3.2\rN\`; ledger `docs/proofs/wp3.2-ledger.md`.
  Copy the runner and prompt shape from `C:\Users\rwsmy\clearwater-review-evidence\wp3.1\r2\`
  (`run_review.sh`, `review-prompt.md`; the round also keeps `review-diff.txt`, `review.txt`,
  `adjudication.md`, `md5sums.txt` as there); the reviewer excludes `docs/proofs` with
  `--glob '!docs/proofs/**'`.
- **WHAT TO EXAMINE:**
  - each equation against spec 6.3.1, 6.3.2 and 6.2 step 2, and against the prototype;
  - the cap: per channel, None disables it, never applied to 3C, from whole-frame values only;
  - the clamp after the strength and outside the measure; it binds as D99 says;
  - D47: BT.709 full in 3C whatever the input's colour description;
  - float32 image data, float64 scalar reductions as the prototype (D39 reading, WP1.1 report
    section 6); no silent float64 result; no host round trip beyond the sync points;
  - product against prototype and CPU against GPU, measured not asserted;
  - the measure / closed-form / render split is complete: render never measures a whole-frame
    value (AD-4's preview = export depends on it);
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
  section 4): the function table (name, signature, measure / closed form / render, prototype
  identity or measured deviation per device), the AD-11 figures, the edge cases, the gates, the
  Reviewer A rounds and verdict, open items.
- **STOP for:** any change needed in `src/clearwater/interfaces/` (AD-20) or in
  `clearwater.core` (X-3); a tolerance looser than AD-11; any dependency (frame section 4
  grants none here); OS-specific code; a prototype numeric that disagrees with the spec; a
  parameter default or name you would have to fix that X-1 leaves to WP3.4; the round-0 table
  showing a choice the brief left open.
- **Spec text.** 6.3.1's "**Status:** the caps are kept for now. The prototype gate measures
  ..." predates the CP4 result; D100 (decided 0.5.4, KEPT) governs and agrees.
- **Working rules:** `uv sync`. Commit by pathspec, `feat(wp3.2): ...` (conventional commits
  carrying the WP id), with a `Co-Authored-By:` footer naming your model. Never a bare `cd`.
  Never post to a mailbox. Gates: ruff check, ruff format --check, mypy strict, full pytest (in
  a window); no harness gate (you touch no `scripts/`, `.claude/`, kernel doc or
  `tests/harness/`). Report `docs/reports/wp3.2-compensation-white-balance.md` (claims,
  evidence paths, limits, and a "DR-19 rule" section stating X-4 as ruled, word for word the
  same as WP3.3's). DR-19 item (5)'s list of wrong implementations is in the WP1.2R Reviewer B
  transcript `C:\Users\rwsmy\clearwater-review-evidence\prototype-retroB\rerun\review-B.txt` (md5
  `f1cc6cf8ae3da62a1b3765573320e7b7`, as recorded in `docs/proofs/wp1.2r-accept.md`): read its
  wrong-implementation list and cover the ones that touch your steps. GoPro IMU/GPS data is out of scope everywhere.

## Rulings (CHARC, pending)

_Placeholder: CHARC's rulings on the questions below._

### Questions as drafted (recommended answer first)

1. **X-1 (cross-brief, WP3.2 and WP3.3): the step-function signatures and the WP3.4
   boundary.** The architecture fixes IF-3 only; it does not say what the WP3.2/WP3.3 functions
   look like. Recommended: (a) plain functions taking the backend first, the array second, and
   every parameter as a keyword-only argument with NO default (the defaults live once, in
   WP3.4's schema); (b) keyword names equal to the prototype `Params` field names
   (`alpha`, `blue_compensation`, `red_gain_cap`, `blue_gain_cap`, `kappa`, `lambda_`,
   `c3_strength`, `c3_kernel_fraction`, `c3_mask_threshold`, `c3_mask_smooth_fraction`,
   `white_balance_strength`, `max_white_balance_gain`), which the frozen `stubs.C3_STAGES`
   already uses in `depends_on_parameters`; (c) each step split into measure (returns Python
   floats), closed form (pure Python, no arrays) and render (array in, array out, never
   measures). For WP3.2 that is, for example: `cap_statistic(backend, a, *, channel)`,
   `effective_alpha(*, alpha, means, channel, cap, cap_statistic)`,
   `compensate_ancuti2018(backend, a, *, means, alphas)`, `compensate_c3(backend, a, *, kappa,
   lambda_, c3_strength, c3_kernel_fraction, c3_mask_threshold, c3_mask_smooth_fraction)`,
   `gray_world_gains(means)`, `applied_gains(gray_world, *, white_balance_strength,
   max_white_balance_gain)` (gains and clamped flags), `apply_white_balance(backend, a, gains)`;
   the means come from `clearwater.core.channel_means` directly. The round-0 table confirms the
   exact list. (d) Range validation of a parameter's own value is WP3.4's (the schema); the
   validation of values derived from parameters and the image size is X-4's.
2. **X-2 (cross-brief): who creates `src/clearwater/methods/__init__.py`.** WP3.2 and WP3.3 run
   in parallel and both need the package. Recommended: the orchestrator commits a
   docstring-only `src/clearwater/methods/__init__.py` (no imports) on main before dispatching
   either; neither cell edits it; WP3.4 owns it afterwards (exports, registration).
   Alternative: WP3.2 owns it and WP3.3 builds on WP3.2's branch (serialises them).
3. **X-3 (cross-brief): elementwise operations without `xp`.** WP3.1 ruling 1.1 keeps
   `CoreBackend.xp` inside `clearwater.core`, so `xp.clip`, `xp.where`, `xp.full_like`,
   `xp.sqrt`, `xp.power` are unavailable here. Recommended: use array methods and operators
   (`.clip`, `.astype`, `.mean(axis, dtype)`, `.sum(axis)`, comparisons, `**`, `abs`), list
   each substitution in the round-0 table, and demand bit identity with the prototype only
   where the substitute is the same operation (`a.clip(0, 1)` is `xp.clip`; a comparison cast
   to float32 replaces `xp.where(bright, 0, 1)`); where it is not (for example `** 0.5` for
   `sqrt` on CuPy), AD-11 applies and the maximum is reported. An operation that cannot be
   written this way is a STOP to CHARC (a `clearwater.core` helper is a change to WP3.1's
   module). For WP3.2 the round-0 table is expected to find none.
4. **X-4 (cross-brief, WP3.2 and WP3.3): the one shared DR-19 rule.** DR-19 asks the product to
   "decide method-scoped validation, the error-line contract and the bound"; CHARC (2026-10-20)
   assigns items (1) and (2) to WP3.2 and WP3.3 for their own parameters, with one rule stated
   in both reports. Recommended rule: (a) each step function validates only the values IT
   derives from its own parameters and the image size (each spatial sigma: finite, positive,
   support within the core's bound), before any array work, so validation is method-scoped by
   construction (a step never sees another method's parameters; the prototype's
   method-agnostic `check_derived_values` is not ported); (b) a failure is ONE `ValueError`
   whose message names the parameter, its value and the short side, in the form
   `"<name>=<value> gives a sigma of <s> px at the short side <n> px; ..."` (the prototype's
   wording), with no other output (no log line or print before it); (c) the support bound is
   the core's: the step calls `clearwater.core.check_sigma` (integer radius) and re-raises its
   ValueError, which does not name a parameter, as (b)'s message (`raise ... from`); the bound
   is never restated; (d) a parameter's own range
   (negative strength, cap below 0) is the schema's (WP3.4) and is not re-checked by the steps.
   WP3.4 then calls the same steps and inherits the rule.
5. **Measured-statistic records.** The prototype returns `CompensationInfo` /
   `WhiteBalanceInfo` records (means, requested and effective strengths, mean added, clamped
   flags). Recommended: no record types in WP3.2; the clamped flags are returned by the closed
   form (a later status or log line may want them) and everything else is recomputable by
   WP3.4 from the stage statistics.
