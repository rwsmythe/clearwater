# WP3.1 ledger -- array backend and image operations

Cell: implementer (opus-high), tier STRONG. Worktree `.worktrees/wp3.1`, branch `wp3.1`, base
main `9735282`. Brief `docs/briefs/wp3.1-brief.md` (FINAL, rulings CHARC `871a371855bb1630`).

## Round 0 -- method table (brief task 1)

Grounded on the installed stack (`uv sync` at base): NumPy 2.5.4, SciPy 1.18.1, CuPy 14.2.0.
Facts read from the code, not assumed:

- SciPy `ndimage` filters run their line buffers in **float64** (C `NI_LineBuffer`), output in
  the input dtype; `gaussian_filter` builds its kernel in float64.
- `cupyx.scipy.ndimage` correlates with `W sum = (W)0; sum += cast<W>(x) * w` where
  `W = _get_weights_dtype(input, weights) = promote(float32, float32)` = **float32** for float32
  input (`cupyx/scipy/ndimage/_util.py:36-42`, `_filters.py:204-206`); the Gaussian kernel is
  built in float32 (`_init_weights_dtype`).
- `np.percentile` and `cupy.percentile` on a float32 array with `method="linear"` return
  **float64** (measured).
- `float32 @ float32` stays float32 (BLAS sgemm / cuBLAS).
- CPU vs GPU, prototype calls, measured: Gaussian sigma 3.3 on 64x48x3, max 1.8e-7; binomial
  5-tap both axes, max 1.2e-7; tiny / odd sizes with the radius larger than the image (1x1x3
  s=5, 3x2x3 s=5, 2x5 s=40, 7x1x3 s=0.6), max 4.8e-7. All far inside AD-11 (2e-3 / 2e-4).
- SciPy radius `int(4 * sigma + 0.5)`: sigma 0.124 -> 0, 0.125 -> 1; at sigma 0.12 the
  output is byte-identical to the input (kernel `[1]`).

### IF-2 methods

| IF-2 method | Prototype counterpart | Border mode | Truncation radius | Accumulation dtype | Bit identity with prototype |
|---|---|---|---|---|---|
| `asarray(a, dtype=float32)` | `Backend.to_device` / `xp.asarray` | n/a | n/a | n/a (cast to float32; any other `dtype` argument -> ValueError, as the stub) | yes (same `xp.asarray(..., float32)`) |
| `to_host(a)` | `Backend.to_host` (`cupy.asnumpy`) | n/a | n/a | n/a | yes; the ONLY device-to-host transfer (Gate 1 section) |
| `gaussian_blur(a, sigma_px)` | `pipeline._gaussian` (`ndimage.gaussian_filter`, sigmas `(s, s, 0)`) | `"reflect"` (symmetric, `d c b a \| a b c d`) | `int(4 * sigma + 0.5)` (SciPy's own rule, `truncate=4.0`); the product's bound check uses the same integer radius (DR-19 item 3 does not recur) | CPU float64 (SciPy) -> float32 out; GPU float32 (cupyx) | CPU yes and GPU yes IF SciPy/cupyx is kept (task 3 measures own kernels: then within AD-11, max reported) |
| `pyramid_reduce(a)` | `gaussian_pyramid` step: `_binomial_blur(a)[::2, ::2]` | `"reflect"` | fixed 5 taps `[1 4 6 4 1]/16` (float32 kernel) | CPU float64 -> float32; GPU float32 | yes (same `correlate1d` calls), odd n -> `(n + 1) / 2` |
| `pyramid_expand(a, shape)` | `expand(image, shape)`: zero-insert at even rows/cols, binomial blur, divide by the blurred indicator | `"reflect"` | fixed 5 taps | CPU float64 -> float32 per pass, division float32; GPU float32 | yes; `shape` must satisfy `h == ceil(H/2)`, `w == ceil(W/2)` (else ValueError; the prototype fails only by a broadcast error) |
| `rgb_to_ycbcr(a, matrix, range_)` | `pipeline.rgb_to_ycbcr` (`a @ RGB_TO_YCBCR.T.astype(float32)`), bt709 full only | n/a | n/a | float32 matmul | bt709 full: yes (same matrix construction and expression). bt709 limited, bt601 full/limited: no prototype counterpart (see R0-1) |
| `ycbcr_to_rgb(a, matrix, range_)` | `pipeline.ycbcr_to_rgb` (`inv(RGB_TO_YCBCR)` in float64, cast float32), unclipped | n/a | n/a | float32 matmul | bt709 full: yes; others: no counterpart |
| `percentile(a, q)` | `_high_pass_and_bounds`: `xp.percentile(a, q, method="linear")` over the whole array | n/a | n/a | float64 interpolation (both devices) -> **cast to float32** (brief: float32 out of every method) | yes after the cast: `product == prototype.astype(float32)` bit for bit (see R0-8) |
| `memory_estimate_bytes(h, w, method_id)` | `backend.memory_estimate_bytes`: `ceil(50 1/12 * 1.25 * 4 * h * w) + 1 MiB` | n/a | n/a | Python float -> int | yes (same constants and expression); 4K -> 1,982 MiB (AD-1). Same formula on both backends (ruling 3) |
| `free_device_bytes()` | none (prototype never queried free memory) | n/a | n/a | n/a | n/a. NumPy -> None; CuPy -> see R0-7 |

Matrices: bt709 `K_R = 0.2126, K_B = 0.0722` (ITU-R BT.709-6, as the prototype); bt601
`K_R = 0.299, K_B = 0.114` (ITU-R BT.601-7). Built in float64 as the prototype builds
`RGB_TO_YCBCR`, inverse by `np.linalg.inv` in float64, both cast to float32 once. Matrix names
other than `bt709`, `bt601` (including `identity`, `unknown`) and ranges other than `full`,
`limited` -> ValueError (ruling 2).

### Plain functions in `clearwater.core` (ruling 1; module `core/ops.py`, re-exported)

| Function | Prototype counterpart | Notes | Identity |
|---|---|---|---|
| `spatial_sigma(shape, fraction)` | `pipeline.spatial_sigma` | `fraction * min(h, w)`, no floor | yes |
| `pyramid_levels(shape, min_level_size)` | `pipeline.pyramid_levels` | ceil halving | yes |
| `gaussian_pyramid(backend, a, levels)` | `pipeline.gaussian_pyramid` | through `backend.pyramid_reduce` | yes |
| `laplacian_pyramid(backend, a, levels)` | `pipeline.laplacian_pyramid` | through `backend.pyramid_expand` | yes |
| `collapse_pyramid(backend, pyramid)` | `pipeline.collapse_pyramid` | | yes |
| `luminance(backend, a)` | `pipeline.luminance` (`a @ luma`, float32) | needed by W_L and W_Sat (WP3.3) | yes |
| `rgb_to_lab(backend, a)` | `pipeline.srgb_to_lab` | float32 throughout, same expression | yes |
| `laplacian(backend, a)` | `ndimage.laplace(..., mode="reflect")` | `[1 -2 1]` per axis; CPU float64 per pass, GPU float32 | yes |
| `channel_means(backend, a)` | `pipeline._channel_means` (`mean(dtype=float64)`) | returns 3 Python floats (a 3-scalar device-to-host read, outside IF-2) | yes |
| `mean(backend, a)` | `pipeline._cap_statistic` / `_accumulate_mean` | float64 accumulation -> Python float | yes |

`backend.xp` (amended 1.1): an attribute on both concrete backends (not on the IF-2 protocol),
used only inside `clearwater.core`; a dependency test fails if any module outside `core` reads
it or imports `cupy`/`cupyx`.

### `select_backend(settings, height, width, method_id)` reasons (task 6)

Order of checks; first match wins. MiB figures: estimate rounded UP, free rounded DOWN, both
with thousands separators; GPU only when `estimate < free` (strictly).

| Condition | Backend | Reason string |
|---|---|---|
| `settings.force_cpu` | numpy | `CPU: forced` |
| `import cupy` raises ImportError | numpy | `CPU: CuPy not installed` |
| `import cupy` raises anything else (a DLL, a driver) | numpy | `CPU: CuPy failed to load` (R0-6) |
| `getDeviceCount()` is 0 or raises a CUDA runtime error | numpy | `CPU: no CUDA device` |
| a one-off probe kernel fails (missing NVRTC / headers) | numpy | `CPU: CUDA device unusable` (R0-6) |
| `estimate >= free` | numpy | `CPU: estimate 1,982 MiB exceeds free 1,200 MiB` |
| otherwise | cupy | `GPU` |

The probe result is cached per process; free memory is read on every call.

### Items the table cannot settle (STOP; recommended answer first)

- **R0-1 "limited" range has no float convention in the spec or the prototype.** D54/D55 name
  limited range only for stream tags; the prototype's full range has no offsets (Cb, Cr in
  [-0.5, 0.5]). Recommended: limited = studio swing over 8-bit codes normalised by 255, chroma
  kept centred on 0 like the full convention: `Y' = 16/255 + (219/255) Y`,
  `Cb' = (224/255) Cb`, `Cr' = (224/255) Cr`, the exact affine inverse, unclipped. Alternative:
  FFmpeg's normalised code values (chroma offset +128/255). No product consumer is known
  (video conversion is FFmpeg's, AD-10; 3C uses bt709 full, D47).
- **R0-2 helper list.** Ruling 1 names the helpers; the table adds `luminance` and `mean`
  (both in the prototype's W_L / W_Sat / gain-cap paths). `channel_means` and `mean` return
  Python floats, i.e. a scalar device-to-host read outside IF-2 (the prototype's precision
  contract: float64 accumulation). Recommended: as tabled.
- **R0-3 input checks.** Recommended: every IF-2 image method refuses a non-float32 input
  (ValueError) and an array of the other backend's kind (TypeError) rather than casting or
  uploading silently; `asarray` is the only entry point.
- **R0-4 `sigma_px` domain.** IF-2 is silent. Recommended: ValueError when not finite or
  `<= 0`, or when the radius `int(4 * sigma + 0.5)` exceeds 2 ** 23 px (the prototype's
  `_MAX_KERNEL_RADIUS`, now on the integer radius).
- **R0-5 unknown `method_id`.** Recommended: `memory_estimate_bytes` and `select_backend`
  raise ValueError for an id other than `c3` / `ancuti2018` (IF-3's two ids), so a new method
  must register its own count instead of being under-estimated.
- **R0-6 two extra reasons** (`CPU: CuPy failed to load`, `CPU: CUDA device unusable`) beyond
  the brief's list, same `CPU: ...` form. Recommended: adopt.
- **R0-7 `free_device_bytes` (CuPy).** Recommended: driver free (`cudaMemGetInfo`) PLUS the
  default pool's `free_bytes()` (blocks CuPy freed but still holds; the driver counts them as
  used, so on the second frame of a clip the driver figure alone would fall by the first
  frame's working set and flip the clip to CPU). Fragmentation of pooled blocks is covered by
  the estimate's 1.25 margin; reasoning recorded in the report.
- **R0-8 percentile is float32 out** (brief task 2). Consequence flagged for WP3.3: the
  prototype carries the N{} bounds as float64 Python floats; `high - low` formed from float32
  bounds can differ from the prototype in the last float32 ulp, so WP3.3's input-2 comparison
  may be within-AD-11 rather than bit-identical. Recommended: keep float32 (the brief's rule);
  no change to IF-2.
- **R0-9 maps.** IF-1 `Array` is `(H, W, 3)`; WP3.3 needs Gaussian pyramids and blurs of
  `(H, W)` weight maps. Recommended: `gaussian_blur`, `pyramid_reduce`, `pyramid_expand`
  accept 2-D and 3-D arrays and filter the two spatial axes only (as the prototype).
- **R0-10 SciPy versus own kernels** is task 3's measured choice. Note: a NumPy own kernel at
  the c3 sigma (0.05 x 2160 = 108 px, radius 432, 865 taps) is a direct 865-tap correlation per
  axis (FFT is out of scope); identity with the prototype holds only if SciPy/cupyx is kept.

## Round-0 rulings and CHARC additions

All ten recommended answers adopted (orchestrator gen 5); CHARC upheld them
(`799b83d4fe11bed8`) and added: R0-8 percentile computed at native precision (float64) and cast
to float32 once, at the return, pinned by `test_percentile_cast_point` with the planted
`EarlyCast` control; R0-7 planted frame-2 case (`test_planted_driver_only_free_flips_frame_two`);
R0-2 the sync-point list below, carried to the WP3.21 brief (wave 4).

### Device-to-host sync points (for WP3.21)

| Where | What is read back | Why |
|---|---|---|
| `clearwater.core.ops.channel_means` | 3 float64 means as Python floats | prototype precision contract (`_channel_means`); WP3.2 white balance and compensation |
| `clearwater.core.ops.mean` | 1 float64 mean as a Python float | prototype `_cap_statistic` (Ancuti gain cap) |
| `clearwater.core.backend._probe_gpu` | 1 probe-kernel sum | once per process, at the first `select_backend` |
| `CoreBackend.to_host` | the array | the IF-2 way out, by design |

No other IF-2 method or helper reads back to the host (Gate 1 tests).

## Cumulative round ledger

| Round | Depth (dispatcher) | Crit | Major | Minor | In/out envelope | NEW/REOPENED | Reverts | Fix kind | Transport / CLI | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 (table) | 108,729 (24 turns) at the round-0 yield | - | - | - | - | - | - | - | - | yield for ruling |
