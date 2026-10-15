# WP1.2 — CPU/GPU variant, speed and memory (CHARC draft brief, Part A)

**Status:** DRAFT by CHARC 2026-10-15; the orchestrator issues the FINAL in section 4.6 format
and dispatches. Cell: `implementer-opus-high`. Worktree `.worktrees/wp1.2`, branch `wp1.2`,
base = the main commit carrying the final brief. **Exclusive** (plan section 4.3): no other cell
runs while this package's timing or memory runs execute; the orchestrator schedules nothing in
parallel from dispatch to return.

**Why Part A.** Plan section 6 WP1.2 measures on the inventory's recording modes, a full real
clip and the largest real photo. The footage folder does not exist yet (owner download in
progress) and WP1.5 (the decode/encode path) has not run. CHARC splits the package: **Part A
(this brief)** settles the GPU mechanism and library, confirms installation on Windows under
Python 3.12, and measures per-frame time and peak memory on synthetic 4K and 5.3K frames;
**Part B** (a later brief, after the footage and WP1.5) measures the real modes, the full-clip
end-to-end timing, the largest photo and analysis speed with decode and `.LRV`. Part A's
figures are labelled SYNTHETIC in the report and are not the Gate 1 result; Gate 1 closes on
Part B. This is a plan-structure decision within CHARC's authority; nothing in the spec is
relaxed.

| Field | Content |
|---|---|
| ID and title | WP1.2 Part A — CPU/GPU variant, synthetic speed and memory |
| Goal | The WP1.1 pipeline runs unchanged in logic on the CPU (NumPy) and on the graphics card from one code path (D107, D30), with CPU-versus-GPU agreement tested; the GPU library is chosen and its Windows/Python 3.12 installation confirmed (PD9); per-frame time and peak RAM and graphics memory are measured on synthetic 4K and 5.3K frames against the N6 budget, with the proxy-resolution effect on the whole-frame statistics reported. |
| Spec clauses | D30, D107 (one core for CPU and GPU); D106 / N6 (0.11 s per frame at 30 fps, 0.056 s at 60 fps, end to end including decode and encode, measured at 4K); D68 / D110 (peak RAM <= 16 GB; graphics memory measured as a second limit); 14.2 "CPU/GPU mechanism, library, and graphics memory estimate"; N1 (no OS-specific code); N13 (licenses). Plan section 6 WP1.2; section 8.3 candidate table; section 9 Gate 1. |
| Depends on | WP1.1 (merged, main `9711faf`). Not on WP0.2, CP1 or WP1.5. |
| Files owned | `tools/prototype/backend.py` (new), `tools/prototype/pipeline.py` and `tools/prototype/params.py` (backend-agnostic edits only; every WP1.1 test must still pass unchanged), `tools/prototype/run.py` (one `--device` option), `tools/prototype/bench.py` (new: the timing and memory instrument), `tests/test_prototype_backend.py` (new), `docs/reports/wp1.2a-speed-memory.md`, `docs/proofs/wp1.2-ledger.md`, `uv.lock`, and in `pyproject.toml` ONLY the dependency grant below plus, if mypy strict needs it, one `[[tool.mypy.overrides]]` entry naming the module. `tests/test_prototype_pipeline.py` is NOT owned: it must pass unchanged on the CPU path. |
| Interfaces consumed | `prototype.pipeline` and `prototype.params` as merged at `9711faf`. Must not import `tools/local_config.py`, `tools/inventory.py` or `tools/environment_report.py`. |
| Interfaces provided | See "Interfaces" below. Prototype interfaces, not frozen; WP2.1 and WP3.1 (IF-2) freeze the product's. |
| Dependencies | **CHARC ruling (GPU library):** `cupy-cuda12x` (MIT) in the `dev` group, the primary candidate. PyTorch (BSD-3) is the fallback candidate, evaluated ONLY if CuPy fails the installation or agreement claims below; adopting it needs a fresh CHARC grant (STOP and route). No OpenCV, Numba, JAX or CUDA toolkit install. See "Decisions fixed at issue". |
| Tests | `tests/test_prototype_backend.py`: CPU-only tests unmarked; GPU tests marked `gpu` and skipped (not failed) when no CUDA device is usable. No `footage` or `slow` marks. |
| Hardware flags | `gpu`; **exclusive** for the `bench.py` runs. The figures this package records ARE results (synthetic, labelled), so plan section 4.3 applies in full: nothing else heavy running, each timing taken on a sustained run (see claim 5), not a single frame. |
| Out of scope | Real footage, recording modes, full-clip end-to-end timing, the largest real photo, analysis-pass speed with decode or `.LRV` (all Part B); decode and encode (WP1.5); any change to the pipeline's mathematics or defaults (WP1.1's open values stand; any numerical change beyond float32 reordering is a finding to route, not a fix); the product's device-selection and fallback policy (WP3.1 designs it from this report); any file under `src/clearwater/`. |
| Done | Plan section 4.5; the four gates and the harness gate green on the final head, with the `gpu` tests RUN (not skipped) at the gate on this machine; the report complete; the return report carries the figures table. |

## Interfaces

`tools/prototype/backend.py`

- `class Backend` (or an equivalent small object) wrapping an array namespace: `xp` (numpy or
  cupy), `ndimage` (`scipy.ndimage` or `cupyx.scipy.ndimage`), `name` (`"cpu"` / `"gpu"`),
  `to_device(array)` and `to_host(array)`, and `synchronize()` (a no-op on CPU).
- `select_backend(device: str = "auto") -> Backend` — `"cpu"`, `"gpu"`, or `"auto"` (GPU if
  `cupy` imports and a CUDA device answers, else CPU). A request for `"gpu"` without a usable
  device raises a clear `RuntimeError`; `"auto"` never raises.
- `of(array) -> Backend` — the backend an existing array belongs to (by array type).
- `memory_estimate_bytes(image_shape, params) -> int` — a documented upper-bound estimate of
  the working-set bytes the pipeline needs for an image of that shape (the input to the spec's
  fallback rule, D68/D110); the report compares it with the measured peak.

`tools/prototype/pipeline.py` and `params.py`

- Every function keeps its WP1.1 signature and semantics and gains the backend by ONE
  mechanism, fixed at issue (below). `correct(image, params)` on a NumPy input returns NumPy
  output whatever the backend; intermediates in `Result` are host arrays (`to_host`).

`tools/prototype/run.py`

- One new option `--device {auto,cpu,gpu}` (default `auto`); the info record names the backend
  used.

`tools/prototype/bench.py`

- `uv run python tools/prototype/bench.py --device {cpu,gpu} --size {4k,5.3k,WxH} --frames N
  --method {ancuti2018,c3} --out <dir>`: generates ONE synthetic textured frame (seeded; a
  blue-green cast over a noise-plus-gradient pattern, the generator documented), runs
  `correct()` on it N times in sequence (a sustained run, host-to-device and device-to-host
  transfers included in the per-frame time), and writes a JSON record: per-frame times (all N,
  plus median and p95 after discarding the first frame as warm-up), peak RSS, peak graphics
  memory (CuPy's pool high-water mark AND the `nvidia-smi` process figure if available), the
  `memory_estimate_bytes` figure, backend, library versions, driver, and machine. A
  `--proxy S` option runs the whole-frame statistics at short side S (D60/D109 lead-in) and
  records the channel means and normalisation bounds against the full-size ones.

## Decisions fixed at issue (CHARC)

- **GPU library: CuPy first.** Grounds: the WP1.1 code is NumPy plus `scipy.ndimage`, and
  CuPy with `cupyx.scipy.ndimage` is a near drop-in, so "one code path" (D107) is a namespace
  switch rather than an abstraction layer; MIT license (N13 clear); the owner's driver 610.62
  supports CUDA 12. The `cupy-cuda12x` wheel must install from `pyproject.toml` through
  `uv sync` alone with NO CUDA toolkit installation on the machine (the wheel carries or
  pip-pulls its runtime). If a toolkit install turns out to be required, STOP and route to
  CHARC with the exact missing library: a system install on the owner's machine is not the
  cell's to make. PyTorch becomes the candidate only on that STOP's answer or if CuPy fails
  claim 2 or claim 3.
- **One mechanism for backend-agnosticism.** The pipeline functions obtain the namespace from
  the input array (`backend.of(array)`), never from a global or a parameter. Functions keep
  taking and returning arrays of the caller's kind; `correct()` moves the input to the selected
  device once and the results back once. No `if gpu:` branches in the mathematics; a
  difference that cannot be expressed through the namespace (a missing `cupyx` function) is
  implemented once in `backend.py` for both kinds, with the reason in its docstring.
- **Agreement tolerance.** CPU and GPU `correct()` outputs on the same input agree within
  max-abs 2e-5 and mean-abs 2e-6 in float32 (the fusion collapse accumulates), measured on
  the two WP1.1 synthetic sizes and on one 1024 px short-side textured image; the figures go in
  the report. A larger discrepancy is a finding (route), not a tolerance to raise.
- **Timing method.** Wall-clock per frame via `time.perf_counter()` around `correct()` with
  `synchronize()` inside the timed region; N = 60 frames at 4K and N = 30 at 5.3K (sustained
  enough to show thermal settling on a laptop; report the median of the first ten against the
  last ten as drift). Sizes: 4K = 3840x2160; 5.3K = 5312x2988 (GoPro 16:9 5.3K). Run each
  (device x size x method) cell ONCE in the exclusive window and record the ambient: nothing
  else heavy, plugged in, Windows power mode as found (record it).
- **Memory.** Peak RSS via `psutil` (already a dev dependency) sampled by a thread at 50 ms;
  graphics memory via CuPy's memory pool high-water mark plus the `nvidia-smi --query-gpu`
  reading before and after. Report in MB with the sampling method named.
- **Budget comparison.** N6 is end to end INCLUDING decode and encode, which Part A does not
  have. Report the core's share of the budget (per-frame median over 0.111 s at 30 fps and
  over 0.056 s at 60 fps) and state that the remainder is what WP1.5's path must fit in. Do
  not declare Gate 1 passed or failed; CHARC does at WP1.6 with Part B.
- **Spec reading.** Spec sections 6.4, 6.6, 7.2, 12 and the D-rows named above, plus 14.2's
  "CPU/GPU mechanism" item. Plan section 6 WP1.2 and section 8.3.
- **mypy.** `cupy` ships type hints; `cupyx.scipy.ndimage` may need the permitted override.
  Keep `mypy` green on the CPU path when `cupy` is absent (guard the import; the module is
  optional at import time).

## Required end state (the claim list)

1. `uv sync` on a clean `.venv` installs `cupy-cuda12x` on this machine under Python 3.12 with
   no toolkit install; `python -c "import cupy; print(cupy.cuda.runtime.getDeviceCount())"`
   prints 1; the versions (CuPy, CUDA runtime, driver) are in the report.
2. `correct()` runs on the GPU for both methods at 4K and 5.3K with `--device gpu`, and the
   CPU path is unchanged: `tests/test_prototype_pipeline.py` passes with no edits.
3. CPU-versus-GPU agreement within the fixed tolerance (test, `gpu`-marked; figures in the
   report).
4. `select_backend("auto")` falls back to CPU, with a logged reason, when `cupy` is missing or no
   device answers (test by monkeypatching the import or the device count; CPU-only, unmarked).
5. The figures table in `docs/reports/wp1.2a-speed-memory.md`: for each of CPU/GPU x
   4K/5.3K x ancuti2018/c3: per-frame median and p95 (s), drift, peak RSS (MB), peak graphics
   memory (MB), the estimate (MB) and the estimate's ratio to the measured peak. Each row
   SYNTHETIC-labelled, with the JSON record's path under `work/wp1.2a/` (the working folder).
6. Proxy effect: the whole-frame statistics (channel means, normalisation bounds) at short
   sides 2160 (full), 1080, 720, 540 and 360 on the synthetic frame, with the relative error of
   each against full size, in the report (D60/D109 input; Part B repeats it on real frames).
7. `memory_estimate_bytes` is documented (what it counts) and is never below the measured peak
   graphics memory in claim 5 (if it is, fix the estimate, not the measurement).
8. Docstrings complete; ruff, ruff format, mypy strict and pytest (with `gpu` tests running)
   green; harness gate green; `pyproject.toml` changes limited to the grant and an optional
   override.

## Test roster (`tests/test_prototype_backend.py`)

- `select_backend("cpu")` returns NumPy; `"auto"` with `cupy` absent returns NumPy and records
  the reason; `"gpu"` with no device raises `RuntimeError` (monkeypatched).
- `of()` on a NumPy array is CPU; round trip `to_device`/`to_host` is identity.
- `memory_estimate_bytes` is monotone in pixel count and positive for the smallest shape.
- (`gpu`) `correct()` on GPU equals CPU within the fixed tolerance on 64x96, 97x65 and a
  1024-short-side textured image, both methods.
- (`gpu`) every public pipeline function accepts a CuPy input and returns a CuPy output of the
  same shape and dtype (no silent host round trip: assert the output type).
- `bench.py` on a tiny size (128x72, 3 frames, CPU) writes a JSON record with the documented
  keys; bad arguments exit 2.

## Declared operating envelope

Windows 11, Python 3.12 under uv, this one machine (RTX 4070 Laptop 8 GB, driver 610.62).
Synthetic frames only, one frame at a time. Decode, encode, real footage, multi-GPU, other
vendors, and the product's fallback policy are out of envelope.

## Review loop (Reviewer A) -- per `docs/review-gate-clearwater.md` Part 1

- Tier **STRONG** (the mechanism this chooses becomes IF-2's basis). Transport, flags, probe,
  per-round assertions, convergence, evidence (`C:/Users/rwsmy/clearwater-review-evidence/wp1.2/rN/`)
  and ledger (`docs/proofs/wp1.2-ledger.md`) exactly as in the WP1.1 brief, with the worktree
  path changed. WHAT TO EXAMINE: the backend mechanism (no hidden host round trips, no
  duplicated mathematics), the agreement test's strength, the timing method's soundness
  (synchronisation inside the timed region, warm-up discarded, transfers included), and the
  memory measurement's provenance. The report is in the diff. Withheld paths named in the
  prompt (the orchestrator's standing rule after WP1.1).
- Reviewer B: recommended, as for WP1.1 (an independent cell re-runs `bench.py` once in the
  exclusive window and checks the figures reproduce within 10%); the orchestrator decides per
  the fill.

## Notes for the cell

- Return report = your FINAL message, under about 70 lines, per `docs/dispatch-recipe.md`
  section 4: per-commit change list; validation lines from the final head; verification-loop
  record; review rounds, ledger and evidence paths; each lock honored; the figures table;
  the installation record; deviations and open questions.
- Keep WP1.1's mathematics byte-for-byte where the namespace switch allows; where CuPy's
  `ndimage` differs in a default (boundary mode, truncation), pass the parameter explicitly on
  both paths so the CPU result does not move (claim 2 is the check).
- A STOP is for: a required toolkit install; a CuPy function with no counterpart that would
  need a second implementation of a pipeline step; an agreement failure you cannot attribute;
  a measured peak above 8 GB graphics memory at 5.3K (report it; do not change the pipeline to
  fit). Do not stop for a slow result: a slow result is a result.
