# WP3.1 -- Array backend and image operations (report)

Brief `docs/briefs/wp3.1-brief.md` (FINAL, CHARC rulings `871a371855bb1630`); round-0 rulings
from the orchestrator (generation 5), all ten recommended answers adopted. Branch `wp3.1`,
base `9735282`. Stack as locked: NumPy 2.5.4, SciPy 1.18.1, CuPy 14.2.0 (`cupy-cuda12x[ctk]`).

## What was built

| Path | Content |
|---|---|
| `src/clearwater/core/backend.py` | `CoreBackend` (one IF-2 implementation over `xp` and `ndimage`), `NumpyBackend`, `CupyBackend` (lazy CuPy import), `select_backend`, `check_sigma`, `rgb_to_ycbcr_matrix` |
| `src/clearwater/core/memory.py` | `memory_estimate_bytes` (the AD-1 counted formula), `METHOD_IDS` |
| `src/clearwater/core/ops.py` | `spatial_sigma`, `pyramid_levels`, `gaussian_pyramid`, `laplacian_pyramid`, `collapse_pyramid`, `luminance`, `rgb_to_lab`, `laplacian`, `channel_means`, `mean` (ruling 1, R0-2) |
| `tools/core_speed.py` | the speed-row instrument (X1, ruling 4) |
| `tests/test_core_{backend,ops,prototype,select,deps}.py` | 152 tests (with GPU) |
| `pyproject.toml`, `uv.lock` | the frame section 4 grant lines (below) |

## Claims and evidence

1. **Every IF-2 method and helper is bit-identical to the prototype on its own device**, CPU
   and GPU, on seeded synthetic inputs and the six WP2.3 stills (`png16-` and `png8-` `uniform`,
   `gradient`, `lowred` `-none`): `tests/test_core_prototype.py` (37 passed, none skipped).
   `percentile` equals the prototype's float64 R-7 result cast to float32. The `-srgb` and
   `-display-p3` variants were not added: the backend does no colour management, so a profile
   changes no value it computes.
2. **CPU against GPU within AD-11** (2e-3 max, 2e-4 mean), measured on a 4K synthetic frame
   with weak red (`clearwater-review-evidence/wp3.1/task3/ad11.txt`): Gaussian at the c3 sigma
   (108 px) max 1.31e-6 / mean 1.14e-7; at the sharpen sigma (10.8 px) 4.77e-7 / 3.95e-8;
   `pyramid_reduce` 1.19e-7; `pyramid_expand` 1.79e-7; Laplacian pyramid and collapse 1.19e-7;
   `laplacian` 1.85e-6; `rgb_to_lab` 1.22e-4 (in L* units, 0-100) / 6.58e-6; `percentile` and all
   eight YCbCr conversions 0. Worst 1.22e-4. Pinned by `test_cpu_against_gpu_within_ad11`.
   The same device run twice is bit-identical (`test_same_device_twice_is_bit_identical`).
3. **Independent references**: Gaussian (radius `int(4 sigma + 0.5)`, symmetric borders),
   REDUCE, EXPAND (normalised) against float64 implementations in the test, odd sizes and 1 x 1
   included; YCbCr rows against the published BT.709 / BT.601 values; percentile against R-7
   computed in the test.
4. **Planted defects fail by name** (`test_core_backend.py`, bottom): a ceil radius rule, a
   `wrap` border (blur and reduce), a float64 leak from `percentile`, an unnormalised EXPAND,
   and swapped Cb/Cr matrix rows.
5. **float32 throughout, no silent cast or upload** (R0-3): a float64 input raises ValueError
   and an array of the other device raises TypeError on every image method; `asarray` refuses
   any `dtype` but float32.
6. **Gate 1 (device-resident)**: on the GPU every IF-2 method typed `-> Array` (the set is read
   from the protocol, so a new method fails the test until listed) and every array-returning
   helper returns a `cupy.ndarray`; `to_host` is the only device-to-host transfer of IF-2.
7. **CuPy optional**: `import clearwater.core` loads no `cupy`, `cupyx`, `PIL`, `av`,
   `PySide6`, nor `clearwater.io/.jobs/.gui/.methods` (subprocess test); with `cupy` made
   unimportable the CPU path runs and `select_backend` answers `CPU: CuPy not installed`. A
   static AST check over `src/clearwater` refuses any `cupy`/`cupyx` import and any `.xp` read
   outside `clearwater.core`, and any import of `prototype`/`tools` (with a planted control).

## Conventions fixed here

- **Gaussian**: SciPy's rule, radius `int(4 sigma + 0.5)`; under 1/8 px the kernel is `[1]`
  (byte-identical output, tested). `sigma_px` must be finite, positive and give a radius of at
  most 2 ** 23 px (R0-4); the bound is on the integer radius, so DR-19 item 3's half-pixel
  mismatch does not recur here.
- **Maps** (R0-9): the filters accept `(H, W)` and `(H, W, C)` and filter the spatial axes only.
- **YCbCr "limited"** (R0-1): `Y' = 16/255 + (219/255) Y`, `Cb' = (224/255) Cb`,
  `Cr' = (224/255) Cr`, chroma centred on 0 as in the full convention; exact inverse in float64,
  unclipped. Round trips pass for both matrices and both ranges. Names other than `bt709`,
  `bt601` / `full`, `limited` raise ValueError.
- **Accumulation**: SciPy filters accumulate in float64 and return float32; cupyx accumulates in
  float32 (`cupyx/scipy/ndimage/_util.py` `_get_weights_dtype`). This is the CPU/GPU difference
  in claim 2.

## SciPy versus own kernels (task 3)

Measured on a 4K plane, float32, `work/task3/measure.py` (evidence copied to
`clearwater-review-evidence/wp3.1/task3/`), 2026-10-20 18:10-18:11Z, NOT exclusive (other cells
running; the GPU showed 0-43 % utilisation from other processes around the run), so the figures
are indicative:

| sigma | device | SciPy / cupyx | own (xp-generic separable) | own vs library |
|---|---|---|---|---|
| 108 (c3, 0.05) | GPU | 0.068 s | 1.266 s | max 1.8e-7, not identical |
| 108 | CPU | 4.92 s | 16.0 s | max 1.3e-6, not identical |
| 10.8 (sharpen, 0.005) | GPU | 0.079 s | 0.147 s | max 1.8e-7 |
| 10.8 | CPU | 0.376 s | 1.53 s | max 4.8e-7 |

The library is 2-19x faster and the only route to bit identity with the prototype, so **SciPy is
kept** and becomes a product dependency under the frame section 4 grant.

## `free_device_bytes` and the memory pool (R0-7)

`CupyBackend.free_device_bytes()` = `cudaMemGetInfo` free + the default pool's `free_bytes()`.
CuPy keeps freed blocks in its pool; the driver counts them as used, but CuPy serves the next
frame's allocations from them first. With the driver figure alone, the second frame of a clip
would see the first frame's working set as taken and fall back to the CPU (pinned by
`test_second_frame_stays_on_gpu`). Fragmented pool blocks may not satisfy a large request; the
estimate's 1.25 margin covers that (WP1.2: 8 % measured). The figure does not count the CUDA
context, which already exists when the decision is taken.

## `select_backend` reasons (exact strings, first match wins)

`CPU: forced` (settings.force_cpu); `CPU: CuPy not installed` (ImportError); `CPU: CuPy failed
to load` (any other import failure, or cupyx missing); `CPU: no CUDA device` (count 0 or a
runtime error); `CPU: CUDA device unusable` (the probe kernel fails); `CPU: estimate N MiB
exceeds free M MiB` (estimate rounded up, free rounded down, thousands separators; GPU only
when estimate < free, strictly); `GPU`. The probe runs once per process; free memory is read on
every call. An unknown method id or a size under 1 raises ValueError (R0-5), even when forced.
The estimate at 4K is 1,982 MiB, equal to the prototype's for every size tested.

## Speed row (task 7)

PENDING the dispatcher's exclusive window. Instrument `tools/core_speed.py GX011627`: the GPU
pass covers all 681 frames; the CPU pass covers 10 frames spread over the clip (the WP1.2 Part B
practice; a 4K CPU op mix takes tens of seconds). It times the op mix one `correct()` call makes
through IF-2 (listed in the tool's docstring), product against prototype, both methods, with GPU
clocks, temperature, utilisation and busy processes recorded before, during and after.

## Consumer notes

- **WP3.3**: `percentile` returns float32 (R-7 in float64, cast once). The prototype carries the
  N{} bounds as float64 Python floats, so `high - low` formed from the float32 bounds can differ
  from the prototype by about one float32 ulp; input 2 may then match within AD-11 rather than
  bit for bit.
- **Sync points for WP3.21**: `ops.channel_means` and `ops.mean` return Python floats (float64
  accumulation, the prototype's precision contract) and so read back to the host;
  `select_backend`'s one-off probe kernel does too. No IF-2 method does.
- **`CoreBackend.xp`** is for `clearwater.core` only (ruling 1.1); the static test enforces it.
  Consumers do elementwise work with array operators and the core helpers.

## Deviations and limits

- `pyproject.toml`: besides the grant lines, the comment on the dev-group CuPy line was
  corrected (it said product adoption was WP2.1's); the dev line itself is kept (ruling 7).
- `pyramid_reduce` returns a contiguous copy where the prototype kept a strided view (values
  identical).
- `pyramid_levels` raises ValueError for `min_level_size < 1` (the prototype loops to 1 px).
- Not run off the envelope: other GPUs, other operating systems, multi-GPU.
