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
| `import cupy` raises anything else (a DLL, a driver), or `import cupyx.scipy.ndimage` raises anything | numpy | `CPU: CuPy failed to load` (R0-6) |
| `getDeviceCount()` is 0 or raises a CUDA runtime error | numpy | `CPU: no CUDA device` |
| `CupyBackend()` cannot bind the current device (`getDevice()` raises), or a one-off probe kernel fails (missing NVRTC / headers) | numpy | `CPU: CUDA device unusable` (R0-6; R1 F3) |
| after the cached probe, reading free memory raises (driver reset, TDR) | numpy | `CPU: CUDA device unusable` (R1 F2) |
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
| pre-review (build, CHARC additions) | 228,618 (74 turns) at the window-request yield; 237,795 (81 turns) at the queue yield | - | - | - | - | - | - | - | - | full-pytest window queued; round 1 to adjudicated verdict, then depth decision |
| 1 | first cell retired at 275K; successor 182,305 (68 turns) at the remediation / window-request yield | 0 | 3 | 4 | 7 in / 0 out | 7 NEW / 0 REOPENED | 0 | pending: product F1 F2 F3 F5, tool F4 F7, test-only F6 | WSL, codex-cli 0.162.1, gpt-5.6-sol high | NEW_CRITICAL_MAJOR_FOUND (adjudicated, not remediated) |
| 2 | 205,771 (88 turns) at the round-2 yield | 0 | 1 | 2 | 3 in / 0 out | 1 NEW (minor) / 2 REOPENED (F4 major, F6 minor) | 0 | pending: tool+test+report R2-1, test-only R2-2, test+report R2-3 | WSL, codex-cli 0.162.1, gpt-5.6-sol high | NEW_CRITICAL_MAJOR_FOUND; zero NEW blocking (the major is a REOPENED F4 residual); adjudicated, not remediated |

## Gate windows

- Full pytest at `f8bd077` (window granted by the dispatcher, held alone): normal run 1294 passed,
  0 skipped, exit 0, 9:03; with `cupy`/`cupyx` unimportable 1191 passed, 103 skipped, exit 0, 6:15
  (all 103 skips are CuPy/GPU: 69 WP3.1, 34 prototype/lookcheck/noise). No non-WP3.1 test assumes
  CuPy. Logs: worktree `work/full1.log`, `work/full2.log`.

## Round 1 (Reviewer A) -- summary

Evidence `C:\Users\rwsmy\clearwater-review-evidence\wp3.1\r1\` (prompt, diff, transcript, probe,
`adjudication.md`, `r1_repro.py`, `md5sums.txt`; transcript md5 `7501908fb9a3b4f112fbd68da5dc757e`,
verdict file `ac341934a3d719383b3509b652f6007f`). Diff `9735282..f8bd077` minus `uv.lock` and
`docs/proofs` (12 files, no ledger line). Assertions all pass; 2 ERROR lines of subprocess
provenance (sandbox mktemp rejection; WSL interop on python.exe). Every finding REASONED by the
reviewer (read-only FS, no uv in WSL); the cell reproduced F1, F2, F5 and confirmed the rest in code.

| # | Sev | Where | Finding | Planned fix |
|---|---|---|---|---|
| F1 | MAJOR | `core/ops.py` `collapse_pyramid` | only the coarsest level is checked; a (3,3,1) band broadcasts, a float64 band promotes the result (repro) | check each band: backend, float32, shape equal to the expanded level; test |
| F2 | MAJOR | `core/backend.py` `select_backend` | `free_device_bytes()` raising after a cached probe escapes (repro) | catch, return `CPU: CUDA device unusable`; test |
| F3 | MINOR | `core/backend.py` `_probe_gpu` | `getDevice()` failure in `CupyBackend()` reported as `CuPy failed to load` | import cupyx separately; device acquisition -> `CPU: CUDA device unusable`; test |
| F4 | MAJOR | `tools/core_speed.py` op mix + report | omits compensation means, `_mean_added` (2), white-balance means, Ancuti cap mean, the saturation luma | complete the op mix per method (pipeline.py 439/461/473/523/526/566/1112/1138) |
| F5 | MINOR | `core/backend.py` `to_host` | accepts float64 (repro) | full `check()`; test |
| F6 | MINOR | `tests/test_core_deps.py` | static rule misses bare `import_module`, `__import__`, `getattr(x, "xp")` | widen rule and planted control |
| F7 | MINOR | `tools/core_speed.py` `gpu_snapshot` | ignores returncode; IndexError on empty stdout | return `{}` on failure |

## Round-1 rulings (orchestrator gen 5, at the successor's dispatch)

The first cell was retired at 275K depth after round 1's adjudication (before remediating);
the successor cell (opus-high, fresh context) took the worktree at `c6314e9`, clean. Rulings,
received as one packet: every planned fix ACCEPTED, one commit per logical change, each with a
test that fails on the unfixed code. F1 MAJOR check every band (shape and float32). F2 MAJOR a
`free_device_bytes()` exception after the cached probe gives `CPU: CUDA device unusable`. F3
minor a `getDevice()` failure gives `CUDA device unusable`. F4 MAJOR (tool and report) complete
the op mix per method; the report's sentence exactly true or narrowed. F5 minor `to_host`
refuses non-float32. F6 minor (test only) the static rule catches `importlib.import_module`,
`__import__`, `getattr(x, "xp")`. F7 minor (tool) `gpu_snapshot` degrades cleanly, the record
says so. Full-pytest windows serialised by the dispatcher (X5).

## Round-1 remediation (successor cell)

Each test was run against the unfixed code first (red), then the fix (green). Logs in the
worktree `work/r2-f*-{red,green}.log`.

| # | Commit | Kind | Red on unfixed code | Fix |
|---|---|---|---|---|
| F1 | `312b31e` | product + test | `test_collapse_checks_every_band` [numpy, cupy]: DID NOT RAISE | `collapse_pyramid` runs `check_spatial` on every level and refuses a band whose channel layout differs from the coarser level's; the spatial fit stays `pyramid_expand`'s check |
| F2 | `1f38687` | product + test + report | `test_free_memory_failure_after_the_probe`, `test_pool_failure_after_the_probe`: RuntimeError escaped | `select_backend` catches any exception from `free_device_bytes()` -> `CPU: CUDA device unusable`; the next call reads again |
| F3 | `761bf51` | product + test + report | `test_device_acquisition_fails`: got `CPU: CuPy failed to load` | `_probe_gpu` imports `cupyx.scipy.ndimage` on its own (failure -> `CuPy failed to load`, regression test `test_cupyx_failed_to_load`), then a `CupyBackend()` failure -> `CUDA device unusable` |
| F5 | `804d7db` | product + test | `test_methods_refuse_non_float32[*-to_host]`: DID NOT RAISE | `to_host` runs the full `check()` |
| F6 | `e999076` | test only | planted control: 5 of 9 spellings found | AST rule: `import_module` / `__import__` bare or as an attribute (string arguments), `getattr(x, "xp")`; report claim 8 reworded (`7e29ece`) |
| F7 | `00dfe98` | tool + test | `tests/test_core_speed.py` gpu_snapshot cases: IndexError / an error line taken for a reading | non-zero exit or no output -> `{"unavailable": "nvidia-smi exit N: <why>"}`; not run -> `{"unavailable": "nvidia-smi did not run: <Error>"}` |
| F4 | `a46dac0` | tool + test + report | `test_op_mix_is_one_correct_call` [c3, ancuti2018]: `_channel_means` 1 vs 4, `luminance` 2 vs 4, `_cap_statistic` 0 vs 1 | op mix adds the compensation means, the two mean-added reads, the Ancuti cap mean per compensated channel, the saturation luma; the test counts the prototype path against a real `correct()` and maps the product path call for call; report sentence rewritten to what is timed and what is not (per-pixel arithmetic, the prototype's `_check_image` min/max) |
| - | `fd173b5` | style | ruff format caught a missing blank line in the F2 fake device | formatted |

Inner loop at `7e29ece`: `tests/test_core_*.py` 172 passed (GPU present); ruff check, ruff
format --check (76 files), mypy (51 files) clean.

## Gate window 2 (successor, granted by the dispatcher, held alone)

Full pytest at `4e8d57a`: normal 1310 passed, 0 skipped, exit 0, 8:44 (`work/full3.log`);
`cupy`/`cupyx` set to None in `sys.modules` (a `python -c` wrapper around `pytest.main`, the
first cell's mechanism) 1204 passed, 106 skipped, exit 0, 5:48 (`work/full4.log`). Every skip
carries a CuPy/CUDA reason (103 as before plus 3 new GPU cases from F1 and F5).

## Round 2 (Reviewer A) -- summary

Evidence `C:\Users\rwsmy\clearwater-review-evidence\wp3.1\r2\` (prompt with a THIS IS ROUND 2
section, diff `9735282..4e8d57a` minus `uv.lock` and `docs/proofs`, the pre-run
`test-summary.txt` the reviewer was allowed to read, transcript, `adjudication.md`,
`md5sums.txt`; transcript md5 `befe56dbfc5fe2844fca568079f918b1`, verdict file
`2b8dca98bc977170986edfc33845c721`). Assertions all pass; 1 ERROR line of subprocess provenance
(WSL interop on python.exe). The reviewer still could not run pytest (read-only /tmp). F1, F2,
F3, F5, F7 verified fixed.

| # | Sev | Where | Finding | NEW/REOPENED | Planned fix |
|---|---|---|---|---|---|
| R2-1 | MAJOR | `tools/core_speed.py` prototype path | host reads differ from `correct()`: percentile without `.tolist()` (correct has it), `_lab_mean(...).tolist()` twice (correct keeps it on device) | REOPENED (F4) | call `proto._high_pass_and_bounds`; `_lab_mean` without tolist; test counts it against `correct()`; docstring and report name each path's host reads |
| R2-2 | MINOR | `tests/test_core_deps.py` | `import_module(name='cupy')`, `__import__(name=...)` missed (reviewer EXECUTED, cell reproduced) | REOPENED (F6) | keyword string arguments too; planted control |
| R2-3 | MINOR | report claim 2 / `test_cpu_against_gpu_within_ad11` | the test pins the IF-2 methods at small sizes only; the helpers and the 4K figures are not pinned as claimed | NEW | add the helpers to `all_methods`; claim 2 says the 4K figures were measured once |

## Round-2 ruling and terminating cleanup

Ruling (orchestrator gen 5): the loop TERMINATES at round 2 -- zero NEW in-envelope blocking
findings (R2-1 is a REOPENED F4 residual, in the instrument, not product code). R2-1..R2-3 fixed
as the terminating round's cleanup, each red-first; the cleanup opens no round. R2-1 must be
right before the speed row (it times that path).

| # | Commit | Kind | Red on the code before the fix | Fix |
|---|---|---|---|---|
| R2-1 | `142566e` | tool + test + report | `test_op_mix_is_one_correct_call` [c3, ancuti2018]: prototype host reads 6 vs 5 / 7 vs 6, `_high_pass_and_bounds` 0 vs 1 | prototype path calls `proto._high_pass_and_bounds` (blur, percentiles, their read) and keeps `_lab_mean` on the device; the test counts host reads (`tolist` / `float` of every `_accumulate_mean` and percentile result) against a real `correct()`; docstring and report name each path's host reads |
| R2-2 | `adcd922` | test only + report | planted control: the two keyword spellings not found | keyword string arguments read too |
| R2-3 | `7293766` | test + report | `test_ad11_roster_covers_every_method_and_helper`: collapse_pyramid, gaussian/laplacian_pyramid, laplacian, luminance, rgb_to_lab missing | `all_methods` gains every array-returning helper (GPU comparison passes at all three sizes); claim 2 says the 4K figures were measured once |

Inner loop at the cleanup head: `tests/test_core_*.py` 173 passed (GPU present); ruff check,
ruff format --check (76 files), mypy (51 files) clean. Logs `work/r2c-*.log`.

## Gate window 3 -- final head (granted by the dispatcher, held alone)

Full pytest at `ea60356`: normal 1311 passed, 0 skipped, exit 0, 8:47 (`work/full5.log`);
`cupy`/`cupyx` unimportable 1205 passed, 106 skipped, exit 0, 5:50 (`work/full6.log`); every skip
carries a CuPy/CUDA reason.

## Successor handoff (if re-seated)

State at round 1's yield: code at `f8bd077` plus this ledger commit; no remediation started.
Remediate F1-F7 above, one commit per logical change, re-run the inner loop
(`tests/test_core_*.py`, ruff, format, mypy), request a full-pytest window (the two runs above),
then run round 2 with `C:\Users\rwsmy\clearwater-review-evidence\wp3.1\r1\run_review.sh` and
`review-prompt.md` copied to `r2` (round number updated; base `9735282`). After the loop: the
exclusive speed row (`uv run python tools/core_speed.py GX011627`: GPU 681 frames, CPU 10
frames; granted window only, merge-candidate code), its figures into the report, then the final
return report (under about 70 lines).
