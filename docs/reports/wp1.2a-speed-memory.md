# WP1.2 Part A -- CPU/GPU variant, synthetic speed and memory

**Every figure in this report is SYNTHETIC**: measured on one generated frame per size, not on
the owner's footage, and without decode or encode. It is not the prototype gate's speed or
memory result (N5 items 1 and 2); WP1.2 Part B measures the real recording modes, a full clip
end to end and the largest photo, and CHARC rules Gate 1 at WP1.6. Machine: RTX 4070 Laptop
GPU 8188 MiB, driver 610.62; AMD Ryzen 9 7940HS, 16 logical CPUs, 32 GB RAM; Windows 11;
Python 3.12 under uv. MiB = 2^20 bytes throughout.

## 1. Installation (claim 1, PD9)

`cupy-cuda12x` installs from `pyproject.toml` through `uv sync` alone under Python 3.12 on
Windows, with no CUDA toolkit installation, no driver change and no machine-wide variable,
**but only with CuPy's `[ctk]` extra**:

- **Plain `cupy-cuda12x` (14.2.0) did not suffice.** It installs and imports, and
  `cupy.cuda.runtime.getDeviceCount()` returns 1, but the first kernel (`cupy.arange`, which
  CuPy compiles at run time with NVRTC) fails in `assemble_cupy_compiler_options` with
  `RuntimeError: Failed to find CUDA headers. Please install CUDA toolkit headers (e.g., pip
  install cupy-cuda12x[ctk]) or specify CUDA_PATH environment variable.` The missing piece
  observed was the CUDA **header set**, not a DLL; whether NVRTC's DLL was also missing could
  not be observed, because the header check fails first.
- **With `cupy-cuda12x[ctk]`** (the orchestrator's grant), `uv sync` adds NVIDIA's CUDA 12
  runtime wheels to `.venv`, and kernels, `cupyx.scipy.ndimage`, `percentile` and `matmul`
  all run. `python -c "import cupy; print(cupy.cuda.runtime.getDeviceCount())"` prints 1.
- Versions: CuPy 14.2.0; CUDA runtime 12.9 (`runtimeGetVersion` 12090); the driver supports
  CUDA 13.3 (`driverGetVersion` 13030); NVIDIA driver 610.62; NumPy 2.5.4, SciPy 1.18.1.

The install footprint (all in the `dev` group; product adoption is WP2.1's, and the
proprietary licences below are an N13 question for it):

| Package | Version | Licence (wheel metadata) |
|---|---|---|
| `cupy-cuda12x` | 14.2.0 | MIT |
| `cuda-pathfinder` (CuPy dependency) | 1.8.3 | Apache-2.0 |
| `cuda-toolkit` (meta-package, `[ctk]`) | 12.9.2.0 | none stated |
| `nvidia-cublas-cu12` | 12.9.2.10 | LicenseRef-NVIDIA-Proprietary |
| `nvidia-cuda-nvrtc-cu12` | 12.9.86 | LicenseRef-NVIDIA-Proprietary |
| `nvidia-cuda-runtime-cu12` | 12.9.79 | LicenseRef-NVIDIA-Proprietary |
| `nvidia-cufft-cu12` | 11.4.1.4 | LicenseRef-NVIDIA-Proprietary |
| `nvidia-curand-cu12` | 10.3.10.19 | NVIDIA Proprietary Software |
| `nvidia-cusolver-cu12` | 11.7.5.82 | LicenseRef-NVIDIA-Proprietary |
| `nvidia-cusparse-cu12` | 12.5.10.65 | LicenseRef-NVIDIA-Proprietary |
| `nvidia-nvjitlink-cu12` | 12.9.86 | LicenseRef-NVIDIA-Proprietary |

Machine notes. A partial CUDA 12.4 folder exists at
`C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.4` (only `include` and `lib`, no
`bin`), and `CUDA_PATH` is not set. CuPy did not use it: plain CuPy found no headers, and
CuPy warns at import, with `[ctk]` too, `UserWarning: CUDA path could not be detected. Set
CUDA_PATH environment variable if CuPy fails to load.` The warning is harmless here (CuPy
locates the wheels' libraries itself) and shows once in the pytest warnings summary. No
variable was set for any run.

## 2. The mechanism (D30, D107, 14.1 "mechanism for running the core on CPU or GPU")

One code path. `tools/prototype/backend.py` holds the `Backend` (an array module `xp`,
`numpy` or `cupy`; a filter module, `scipy.ndimage` or `cupyx.scipy.ndimage`; `to_device`,
`to_host`, `synchronize`), `select_backend(device)`, `of(array)` and
`memory_estimate_bytes`. Every function in `tools/prototype/pipeline.py` takes its backend
from its input with `of(array)` and returns arrays of the input's kind; there is no device
branch in the mathematics. The constant matrices and the binomial kernel are built once per
array module, exactly as WP1.1 built them, so on NumPy they are the same arrays. Filter mode
(`reflect`) and truncation (4 sigma) are passed explicitly on both devices. No CuPy function
was missing: nothing is implemented twice.

- **CPU path unchanged.** On 15 cases (64x96, 97x65 and 720x1024 inputs; default, 3C, blue
  compensation, neutral and blended parameter sets), every array of `Result` and both info
  records hash identically (SHA-256) under WP1.1's pipeline (main `d27f909`) and this one;
  `tests/test_prototype_pipeline.py` passes unedited (claim 2).
- **`select_backend`**: `"cpu"`; `"gpu"`, which raises `RuntimeError` with the reason when
  CuPy is missing, the CUDA runtime does not answer, it reports no device, or a 4-element
  test kernel fails (this catches the missing-header case of section 1), or
  `cupyx.scipy.ndimage` does not import; `"auto"`,
  which never raises and falls back to the CPU with the reason logged at INFO and stored
  in `Backend.reason` (claim 4).
- **Accepted interface deviations** (CHARC ruling 4db6db642c117b1e):
  `correct(image, params, backend=None)` gains an optional backend: the input is moved to
  its device once and every array of the result is moved back once, to the input's kind
  (`None` runs where the input is, which is WP1.1's call). And a public
  `normalisation_bounds(image, params)` returns the N{} bounds that `fusion_inputs` applies
  (both use one private helper), for the proxy statistics of section 6.
- `run.py --device {cpu,gpu,auto}` defaults to **`cpu`** (CHARC ruling, finding 2): a GPU
  result agrees with the CPU only within float32 tolerance, which moved 5 (ancuti2018) and
  12 (3C) of 6720 16-bit values by one LSB on WP1.1's CLI test image, so the default keeps
  the runner's PNG the same on every machine. `--dump` records the backend in
  `<stem>-weights.json`.

## 3. CPU versus GPU agreement (claim 3)

`correct()` output, |CPU - GPU|, float32, default parameters. Fixed tolerance (brief): max-abs
2e-5, mean-abs 2e-6. Per the CHARC ruling on finding 1 the tolerance binds on WP1.1's textured
scene (`_textured_scene` in `tests/test_prototype_pipeline.py`); WP1.1's near-flat
`_synthetic` pair has its own bound, max-abs 1e-4 and mean-abs 1e-5, so that a regression
there is still caught. Both are `gpu`-marked tests in `tests/test_prototype_backend.py`.

| Image | ancuti2018 max / mean | 3C max / mean | Bound |
|---|---|---|---|
| textured scene 64x96 | 9.60e-6 / 1.08e-6 | 8.64e-6 / 1.06e-6 | 2e-5 / 2e-6 |
| textured scene 97x65 | 7.15e-6 / 9.80e-7 | 7.21e-6 / 9.01e-7 | 2e-5 / 2e-6 |
| textured scene 1024x1536 | 2.68e-6 / 3.45e-7 | 8.11e-6 / 5.34e-7 | 2e-5 / 2e-6 |
| near-flat `_synthetic` 64x96 | 2.72e-5 / 4.00e-6 | 3.58e-5 / 4.59e-6 | 1e-4 / 1e-5 |
| near-flat `_synthetic` 97x65 | 2.24e-5 / 3.32e-6 | 2.36e-5 / 4.04e-6 | 1e-4 / 1e-5 |
| bench frame 3840x2160 (not a test) | 1.67e-6 / 1.58e-7 | 4.41e-6 / 3.00e-7 | -- |

The table's figures come from `agree.py` and `agree3.py` (the scripts and their logs are in
`C:\Users\rwsmy\clearwater-review-evidence\wp1.2\analysis\`, beside the CPU hash comparison of
section 2); the tests assert the same quantities.

Cause of the near-flat figures (attributed and reproduced): `cupyx.scipy.ndimage` accumulates
a float32 input in float32, `scipy.ndimage` in float64, so the high-pass `I - G*I` of the
sharpened fusion input differs by about one float32 ulp (1.2e-7). The stretch N{} divides it
by the span of its percentile bounds, about 0.0018 at 64x96 and 0.0021 at 97x65 on these
near-flat images, which amplifies the difference about 500-fold into input 2 and from there
into the output. On the textured scene the span is 0.005-0.006 at the same sizes and 0.035 at
1024x1536. A float64-accumulating Gaussian on the GPU closed the gap (at most 4.2e-7 /
3.3e-8 on every image above) but cost 0.12 s (ancuti2018) and 0.32 s (3C) per 4K frame; CHARC
rejected it (option B) and banked the ill-conditioning of N{} on low-texture frames as DR-14.

## 4. Method of measurement

`tools/prototype/bench.py` (its module docstring is the full description):

- **Frame.** One seeded synthetic frame per size: a blue-green cast (red `0.05 + 0.15x`,
  green `0.35 + 0.35y`, blue `0.45 + 0.25xy`), modulated by +/-30 % by a band-limited texture
  (uniform noise smoothed at sigma 0.004 of the short side) plus per-pixel Gaussian noise of
  standard deviation 0.01, clipped to [0, 1]. Sizes 4K = 3840x2160 and 5.3K = 5312x2988.
- **Timing.** `time.perf_counter()` around `correct(frame, params, backend)` on the NumPy
  frame followed by `backend.synchronize()`, so each frame's time includes the host-to-device
  copy of the input, every kernel, and the device-to-host copy of **every** array of the
  `Result` (six images and ten weight maps, 28 planes, about 0.87 GiB at 4K). N = 60 at 4K and 30 at 5.3K,
  in sequence; the first frame (kernel compilation, pool growth) is discarded; median and
  p95 over the rest; drift = median of the last ten over the median of the first ten.
- **Supplementary, GPU only: device-resident.** A second loop of N frames times what a
  renderer needs: the input copied to the device, `correct()` on the device array, and only
  the output copied back. It is not the brief's figure; it shows the cost of copying every
  intermediate back.
- **Memory.** Peak RSS: `psutil` samples by a thread every 50 ms over the timed loop (the OS
  peak working set is recorded beside it and agrees). Graphics memory: CuPy's default pool,
  its cache emptied before the loop, behind a counting allocator that records the pool's used
  bytes after every allocation (peak used); the pool's reserved bytes after the loop (it
  returns nothing during the run, so this is its high-water mark) is the **peak graphics
  memory** column. `nvidia-smi --query-gpu=memory.used` before the backend starts and after
  the loop, and the CUDA runtime's device-wide used memory after the context exists and after
  the loop, are in the records; the per-process `nvidia-smi` figure is `[N/A]` under Windows'
  WDDM driver model.
- **Ambient.** Each window exclusive (no Codex or other cell running), each cell run once,
  plugged in (`psutil.sensors_battery`: power plugged, battery 80-81 %), machine settings as
  found and not changed. Windows 11 has two layers: the power **scheme** (`powercfg
  /getactivescheme`) and the power-mode **overlay** set by the Settings slider. The scheme was
  Balanced (381b4222-f694-41f0-9685-ff5bb260df2e) in both windows. The overlay was **not
  recorded in the first window** (the record held only the scheme, which the first version of
  this report wrongly called the power mode); in the second window it was **Best performance**
  (ded574b5-45a0-4f42-8737-46345c09c238), read through `powrprof` without changing anything.
  From the second window on, `bench.py` also records the card's clocks, temperature, power
  draw, P-state and clock-limit reasons just before and just after the timed loop (outside
  it). A stray `python.exe` left by an earlier session (PID 33616) kept one of the 16 logical
  CPUs busy in both windows (present at the GPU re-measurement too, `tasklist /FI "PID eq
  33616"`); it was not this package's to stop, and every record's `ambient.note` says so.

## 5. Figures (claim 5)

All rows **SYNTHETIC**. Records under `C:\Users\rwsmy\clearwater\work\wp1.2a\` (the working
folder; not committed). Two exclusive windows on 2026-10-14 (local time, UTC-10):

- **CPU rows: head `d3d9555`**, 17:11-18:27. The timed path has not changed since: from
  `d3d9555` to `f234dbf` the pipeline is untouched, `backend.py` changed only in
  `select_backend`'s probe (run before the loop) and `bench.py` only in ambient readings
  taken outside the timed region. Ambient: scheme Balanced, overlay not recorded, PID 33616
  present.
- **GPU rows: head `f234dbf`**, 19:17-19:22, re-measured after Reviewer B's run did not
  reproduce the first window's 3C cells within 10 %. Ambient: scheme Balanced, overlay Best
  performance, PID 33616 present; GPU state per cell in the spread table below.

"Peak graphics memory" is the CuPy pool's reserved high-water mark, with the pool's peak
used bytes in brackets; "Estimate / peak" is `memory_estimate_bytes` over that figure on the
GPU (and over the peak RSS in brackets, and alone on the CPU). Drift is the median of the
first ten steady frames -> the median of the last ten.

| Device | Size | Method | N | Median (s) | p95 (s) | Drift | Share of 0.111 s | Share of 0.056 s | Peak RSS (MiB) | Peak graphics memory (MiB) | Estimate (MiB) | Estimate / peak | Head | Record |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CPU | 4k | ancuti2018 | 60 | 10.971 | 11.285 | 11.233 -> 11.008 (-2.0%) | 98.8x | 195.9x | 1647 | n/a | 1982 | RSS 1.20 | `d3d9555` | `bench-cpu-4k-ancuti2018-20261014-172225.json` |
| CPU | 4k | c3 | 60 | 23.394 | 24.021 | 21.573 -> 23.701 (+9.9%) | 210.8x | 417.8x | 1646 | n/a | 1982 | RSS 1.20 | `d3d9555` | `bench-cpu-4k-c3-20261014-174552.json` |
| GPU | 4k | ancuti2018 | 60 | 0.385 | 0.419 | 0.400 -> 0.401 (+0.2%) | 3.5x | 6.9x | 1673 | 1712 (used 1585) | 1982 | 1.16 (RSS 1.18) | `f234dbf` | `bench-gpu-4k-ancuti2018-20261014-191823.json` |
| GPU | 4k | c3 | 60 | 0.626 | 0.658 | 0.630 -> 0.617 (-2.2%) | 5.6x | 11.2x | 1672 | 1712 (used 1585) | 1982 | 1.16 (RSS 1.19) | `f234dbf` | `bench-gpu-4k-c3-20261014-191937.json` |
| CPU | 5.3k | ancuti2018 | 30 | 24.548 | 25.159 | 24.932 -> 24.477 (-1.8%) | 221.2x | 438.4x | 3090 | n/a | 3792 | RSS 1.23 | `d3d9555` | `bench-cpu-5.3k-ancuti2018-20261014-175817.json` |
| CPU | 5.3k | c3 | 30 | 57.985 | 58.502 | 58.058 -> 58.147 (+0.2%) | 522.4x | 1035.4x | 3094 | n/a | 3792 | RSS 1.23 | `d3d9555` | `bench-cpu-5.3k-c3-20261014-182722.json` |
| GPU | 5.3k | ancuti2018 | 30 | 0.835 | 0.870 | 0.831 -> 0.842 (+1.3%) | 7.5x | 14.9x | 2696 | 3275 (used 3032) | 3792 | 1.16 (RSS 1.41) | `f234dbf` | `bench-gpu-5.3k-ancuti2018-20261014-192027.json` |
| GPU | 5.3k | c3 | 30 | 1.479 | 1.682 | 1.454 -> 1.499 (+3.1%) | 13.3x | 26.4x | 2687 | 3275 (used 3032) | 3792 | 1.16 (RSS 1.41) | `f234dbf` | `bench-gpu-5.3k-c3-20261014-192200.json` |

**GPU spread between the two windows (a result in itself).** The first window's GPU records
(head `d3d9555`, 17:06-17:11, overlay not recorded, no GPU state recorded) are kept beside
the second's; the memory figures were identical to the byte. The 3C cells moved by more than
10 %, the ancuti2018 cells by 7-8 %. 3C's sigma-108 Gaussian is compute-bound and the most
clock-sensitive step. At the end of every second-window loop the card was in P0 at
1995-2400 MHz, power-capped (reason 0x04) and, after 5.3K 3C, in software thermal slowdown
(0x20) at 83 C; what clocks and overlay held in the first window is not known, so the
spread is not attributed further. On a laptop, sustained GPU speed varies by this much
between runs (spec 12).

| Size | Method | Median, window 1 (s) | Median, window 2 (s) | Change | Device-resident 1 -> 2 (s) | GPU state at loop start | GPU state at loop end |
|---|---|---|---|---|---|---|---|
| 4k | ancuti2018 | 0.416 | 0.385 | -7.3% | 0.305 -> 0.274 | 1980 MHz, 57 C, 21 W, P0 | 2280 MHz, 70 C, 57 W, P0, reasons 0x04 |
| 4k | c3 | 0.723 | 0.626 | -13.3% | 0.613 -> 0.506 | 1980 MHz, 67 C, 22 W, P0 | 2355 MHz, 86 C, 98 W, P0, reasons 0x04 |
| 5.3k | ancuti2018 | 0.907 | 0.835 | -8.0% | 0.643 -> 0.574 | 1980 MHz, 74 C, 26 W, P0 | 2400 MHz, 83 C, 75 W, P0, reasons 0x04 |
| 5.3k | c3 | 1.807 | 1.479 | -18.1% | 1.624 -> 1.263 | 1980 MHz, 75 C, 24 W, P0 | 1995 MHz, 83 C, 73 W, P0, reasons 0x20 |

Supplementary (GPU, not the brief's figure, second window): the device-resident path, the
input copied in and only the output copied back, same frame and N, run after the main loop
in the same process. The difference to the main table is the device-to-host copy of the other
fifteen result arrays.

| Size | Method | Device-resident median (s) | p95 (s) | Drift | Share of 0.111 s |
|---|---|---|---|---|---|
| 4k | ancuti2018 | 0.274 | 0.288 | +1.5% | 2.5x |
| 4k | c3 | 0.506 | 0.538 | +3.4% | 4.6x |
| 5.3k | ancuti2018 | 0.574 | 0.602 | -4.6% | 5.2x |
| 5.3k | c3 | 1.263 | 1.378 | +1.9% | 11.4x |

Graphics memory readings of the **main** timed loop (second window; they are taken before the
device-resident loop runs). The context column is the `nvidia-smi` growth over the run (after
less before) less the pool's reserved bytes: the CUDA context and library workspaces.

| Size | Method | `nvidia-smi` used before -> after (MiB) | Pool reserved (MiB) | Context and libraries (MiB) | CUDA used after context -> after loop (MiB) | Estimate (ratio to `nvidia-smi` growth) |
|---|---|---|---|---|---|---|
| 4k | ancuti2018 | 160 -> 2017 | 1712 | 145 | 1122 -> 2864 | 1982 (1.07) |
| 4k | c3 | 219 -> 2037 | 1712 | 106 | 1122 -> 2864 | 1982 (1.09) |
| 5.3k | ancuti2018 | 162 -> 3593 | 3275 | 156 | 1122 -> 4420 | 3792 (1.11) |
| 5.3k | c3 | 178 -> 3672 | 3275 | 219 | 1122 -> 4424 | 3792 (1.09) |

Readings. The `nvidia-smi` figure before a GPU run was 160-219 MiB; before some CPU runs it
read 0 MiB (the discrete card idles). The highest graphics memory peak, 3275 MiB at 5.3K, is
40 % of the card's 8188 MiB. Peak RSS stays under 3.1 GiB everywhere (N4 limit 16 GB).
Warm-up (discarded) first frames: GPU 0.66-1.70 s (1.15 to 1.72 times the steady median);
CPU 0.93 to 1.02 times the steady median (no compilation on the CPU). Drift is within
+/-3.1 % on the GPU; on the CPU, 3C at 4K slowed by 9.9 % over the run (21.6 -> 23.7 s), the
only cell with a drift above 3.1 %.

## 6. Budget comparison (N6, D106)

N6 is end to end, decode and encode included, which Part A does not have; the share is the
core's per-frame median over the budget (0.111 s at 30 fps, 0.056 s at 60 fps), and whatever
is left is what WP1.5's decode and encode path must fit in.

- **GPU, 4K:** the core alone takes 3.5x (ancuti2018) and 5.6x (3C) of the 30 fps budget,
  6.9x and 11.2x of the 60 fps budget (second window; 3.7x and 6.5x in the first). Nothing
  is left for decode and encode; even the device-resident path (2.5x and 4.6x at 30 fps) is
  over the whole budget.
- **GPU, 5.3K** (best effort per D106): 7.5x and 13.3x at 30 fps (8.2x and 16.3x in the
  first window).
- **CPU:** 99x to 522x of the 30 fps budget (11.0 to 58.0 s per frame), as spec 12 expects.

This package does not declare Gate 1 passed or failed and does not optimise the pipeline
(CHARC). For WP2.1 and WP3.1, observed but not acted on: 3C's large Gaussian (sigma 0.05 of
the short side, 108 px at 4K, 865 taps per axis as a direct convolution) took about 97 ms per
4K channel on the GPU in a development measurement and is the main difference between the
two methods; copying all intermediates back costs about 0.11-0.12 s per 4K frame (section 5,
supplementary table); the fusion keeps the last input's pyramids referenced during the
collapse (13 1/3 of the 50 1/12 peak planes, section 7).

## 7. Memory estimate (claim 7; D68, D110, N4)

`memory_estimate_bytes(image_shape, params)` counts the working set in float32 planes of the
image size (4 bytes per pixel; an RGB image is 3 planes) at the peak of `correct()` on a
device, which a counting allocator located at the finest EXPAND of the pyramid collapse at
the end of the multiscale fusion: 25 planes of results still alive (the device copy of the
input, the compensated and white-balanced images and the two fusion inputs; the ten weight
maps), 13 1/3 planes of fusion pyramids (the fused pyramid, and the last input's Laplacian
and blended pyramids and its weight's Gaussian pyramid, still referenced), and 11 3/4 planes
of EXPAND temporaries. That is 50 1/12 planes; the measured peak used is 50.1 planes at every
size from 128x72 to 5.3K. The estimate multiplies by 1.25 (pool rounding and fragmentation,
measured at 8 %, and pyramids of odd sizes) and adds 1 MiB (constant arrays and the pool's
512-byte rounding, which dominate only for tiny images). It excludes the CUDA context and
library workspaces, 106-219 MiB here (the `nvidia-smi` growth over the run less the pool's
reserved bytes, section 5; the spread is the `nvidia-smi` reading's own), because they exist
before the decision is taken: compare the estimate with the device's free memory.

Measured: the estimate is 1.16x the pool's reserved peak and 1.25x its used peak in every
GPU row; it also covers the whole-card `nvidia-smi` growth (1.07-1.09x at 4K, 1.09-1.11x at
5.3K) and the CPU rows' peak RSS (1.20x at 4K, 1.23x at 5.3K). A `gpu` test asserts
estimate >= reserved >= used, and estimate <= 1.5x reserved, at 1024x1536 for both methods.
The CPU rows' RSS includes the interpreter and libraries (156-242 MiB at start).

## 8. Proxy resolution and the whole-frame statistics (claim 6; D60, D109)

The whole-frame statistics of the 4K synthetic frame on proxies area-averaged (Pillow BOX) to
short sides 1080, 720, 540 and 360, computed on the CPU, against full size (2160). "Rel.
error" is `|proxy - full| / |full|`.

ancuti2018:

| Short side | Shape | Input means R, G, B | Rel. error (max over channels) | WB gains R, G, B | Rel. error (max) | N{} bounds low, high | Rel. error low, high |
|---|---|---|---|---|---|---|---|
| 2160 | 3840x2160 | 0.12402, 0.52107, 0.50866 | 0.0e+00 | 1.4581, 0.8539, 0.8748 | 0.0e+00 | -0.04753, 0.04702 | 0.0%, 0.0% |
| 1080 | 1920x1080 | 0.12402, 0.52107, 0.50866 | 3.1e-11 | 1.4581, 0.8539, 0.8748 | 9.7e-07 | -0.04172, 0.04144 | 12.2%, 11.9% |
| 720 | 1280x720 | 0.12402, 0.52107, 0.50866 | 7.8e-11 | 1.4581, 0.8539, 0.8748 | 2.5e-06 | -0.04049, 0.04024 | 14.8%, 14.4% |
| 540 | 960x540 | 0.12402, 0.52107, 0.50866 | 1.0e-10 | 1.4581, 0.8539, 0.8748 | 4.7e-06 | -0.03981, 0.03961 | 16.2%, 15.8% |
| 360 | 640x360 | 0.12402, 0.52107, 0.50866 | 5.3e-09 | 1.4581, 0.8539, 0.8748 | 1.1e-05 | -0.03866, 0.03846 | 18.6%, 18.2% |

3C (same input means; the white-balance gains follow the 3C-compensated means):

| Short side | Shape | Input means R, G, B | Rel. error (max over channels) | WB gains R, G, B | Rel. error (max) | N{} bounds low, high | Rel. error low, high |
|---|---|---|---|---|---|---|---|
| 2160 | 3840x2160 | 0.12402, 0.52107, 0.50866 | 0.0e+00 | 1.0150, 1.0202, 0.9665 | 0.0e+00 | -0.05020, 0.05039 | 0.0%, 0.0% |
| 1080 | 1920x1080 | 0.12402, 0.52107, 0.50866 | 3.1e-11 | 1.0150, 1.0202, 0.9665 | 7.1e-11 | -0.04576, 0.04592 | 8.9%, 8.9% |
| 720 | 1280x720 | 0.12402, 0.52107, 0.50866 | 7.8e-11 | 1.0150, 1.0202, 0.9665 | 3.9e-11 | -0.04464, 0.04484 | 11.1%, 11.0% |
| 540 | 960x540 | 0.12402, 0.52107, 0.50866 | 1.0e-10 | 1.0150, 1.0202, 0.9665 | 6.3e-11 | -0.04404, 0.04423 | 12.3%, 12.2% |
| 360 | 640x360 | 0.12402, 0.52107, 0.50866 | 5.3e-09 | 1.0150, 1.0202, 0.9665 | 6.3e-12 | -0.04286, 0.04306 | 14.6%, 14.5% |

Channel means and white-balance gains are unaffected for practical purposes (relative errors
at most 1.1e-5): area averaging preserves means. The normalisation bounds of N{} shrink, by
9-12 % at 1080 and 15-19 % at 360: they are the 0.5th and 99.5th percentiles of the high-pass
`I - G*I`, and the frame's per-pixel noise (standard deviation 0.01, not scaled with the frame)
is averaged down by the proxy while the band-limited texture is not. A tighter N{} stretches
input 2 more, so proxy-computed bounds would sharpen more than full-size ones on noisy footage;
this is spec 12's "statistics on downscaled frames" risk, measured here on a synthetic noise
model only. Part B repeats it on real frames, where the noise and texture spectra decide the
size of the effect.

## 9. Test and gate record

`tests/test_prototype_backend.py`: CPU tests unmarked; `gpu` tests skip with "no CUDA device
usable: <reason>" when `select_backend("auto")` falls back, and ran on this machine. The
agreement, round-trip, device-type, estimate and `bench.py` tests are listed in that file;
each guard was checked against a planted defect (a host round trip in `luminance`, a GPU-only
border mode, weights left on the device, an estimate margin of 0.9, the warm-up frame kept, a
`run.py` default of `auto`), and each planted defect failed its test.

The device test also runs with a transfer guard (Reviewer B F3): while the pipeline functions
run, `cupy.asnumpy` (behind `Backend.to_host`) and `cupy.asarray` / `cupy.array` given a NumPy
array raise when called from `prototype.pipeline` or `prototype.backend` with more than 16
values, so a step that computes on the host and returns a CuPy array fails even though its
output type is right. On a copy of the tree, a `white_balance` that computed on the host
(through `to_host`, and through `ndarray.get()`) and returned `xp.asarray(...)` failed the
test both times. Blind spot: the Cython methods `ndarray.get`, `ndarray.set` and
`ndarray.tolist` cannot be patched, so a round trip made only of those would pass; none
exists in the code, and the scalar statistics (channel means, percentile bounds) use
`tolist()` on at most 3 values. The test now also exercises the 2-D (single-channel) branch of
`expand` on the GPU, which the pipeline itself reaches only with RGB levels.
