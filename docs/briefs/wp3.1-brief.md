# WP3.1 — Array backend and image operations (dispatch brief, APPROVED)

**Status:** APPROVED by CHARC `871a371855bb1630` with rulings (section "Rulings"); draft `6611b3d`, written by
the orchestrator (generation 4) at CHARC's commission (`a05f065e53e696d7`). FINAL at dispatch,
once WP2.3 has merged (X4); if the owner's Gate 1 word is still pending then, it dispatches
WITHOUT a Gate 1 section, which is added by amendment when the owner rules. Owner decisions: none
inside the package.
- Spec **v0.5.3**; v0.5.4 items cited as "proposed (v0.5.4, CP4)". Architecture DRAFT 0.1
  section 3 IF-2 and section 4; AD-1, AD-9, AD-11, AD-18, AD-20, AD-21. Frame
  `docs/briefs/wp2.4-phase3-frame.md` (sections 1-4). Gate report `docs/reports/wp1.6-gate-report.md`.
- Cell: `implementer-opus-high`. Tier **STRONG**.
- Worktree `.worktrees/wp3.1`, branch `wp3.1`, base = the main commit named at dispatch.

**Why.** Plan WP3.1 is the first link of the critical path (plan 11.1: CP4 → WP3.1 → WP3.2 and
WP3.3 → WP3.4). Every array operation of the correction core goes through it, on CPU or GPU, by
one code path (D107, N3). WP3.2, WP3.3 and WP3.5 cannot test numerics until it merges: the
WP2.2 `StubArrayBackend` raises `NotImplementedError` for every image operation.

| Field | Content |
|---|---|
| ID and title | WP3.1 — Array backend and image operations; plan section 6 Phase 3 row WP3.1 (size L); module `clearwater.core` (plan 8.1) |
| Goal | A NumPy backend and a CuPy backend that both satisfy IF-2 `ArrayBackend`, a working `select_backend`, and the memory estimate of AD-1, with tests that pin CPU against GPU (AD-11) and the product against the prototype's recorded numerics. |
| Spec / decision clauses | D39 "Internal processing in 32-bit float; quantization only at export"; 6.4 "All processing in 32-bit floating point, normalized to [0, 1]"; D56 / 6.6 "All spatial parameters ... a fraction of the image's short side" and "Pyramid depth is set by a minimum coarsest-level size"; D107 / N3 "the same code runs on CPU or GPU from the start"; D111 "Automatic CPU fallback when an image or frame is estimated not to fit in graphics memory; no tiled processing in v1"; N4 "if an image or frame is estimated not to fit in graphics memory, it is processed on CPU automatically"; N10 / D92 reproducibility. Feeds V1 (primitives' unit tests, edge cases "uniform images, near-zero red channel, 10-bit input") and V15 ("the CPU fallback engages when an image does not fit in graphics memory"). AD-1 (backend, device rule, the estimate "1.16x the pool's reserved peak at 4K"); AD-9 ("Force CPU processing" overrides device selection; G12 force-CPU proposed (v0.5.4, CP4) item 6); AD-11 (tolerances); AD-18 (CUDA runtime files never redistributed); AD-21 (N6 PENDING; D106 proposed (v0.5.4, CP4) item 1). |
| Depends on | WP2.2 merged (`b288533`, IF-2 frozen). WP2.3 merged for the stills used by the reference tests (group 1, "Stills": uniform, horizontal gradient, near-zero red, 8- and 16-bit), by their manifest ids. No other Phase 3 package. |
| Files owned | `src/clearwater/core/` (NEW: `__init__.py`, `backend.py` (the two backends and `select_backend`), `memory.py` (the estimate), plus any helper modules ruled under open question 1); `tests/test_core_*.py` (NEW); `docs/reports/wp3.1-array-backend.md`; `docs/proofs/wp3.1-ledger.md`. `pyproject.toml`: ONLY the two grant lines of frame section 4 (numpy to `[project] dependencies`; `cupy-cuda12x` as `[project.optional-dependencies] gpu`; SciPy as a product dependency only if task 3's evidence keeps it), and `uv.lock` as `uv lock` regenerates it. The speed-row instrument's home is open question 4. NOT owned: `src/clearwater/interfaces/`, `tools/prototype/` (read-only reference), `tests/conftest.py`, `tests/fixture_plugin.py`, every other module. |
| Interfaces provided | IF-2: classes satisfying `clearwater.interfaces.backend.ArrayBackend` (`name`, `device`, `asarray`, `to_host`, `gaussian_blur`, `pyramid_reduce`, `pyramid_expand`, `rgb_to_ycbcr`, `ycbcr_to_rgb`, `percentile`, `memory_estimate_bytes`, `free_device_bytes`), and `clearwater.core.select_backend(settings: Settings, height: int, width: int, method_id: str) -> tuple[ArrayBackend, str]` with the interface's signature. The interface-level `clearwater.interfaces.backend.select_backend` stays as it is (it raises `NotImplementedError` naming WP3.1, and `tests/test_interfaces.py` pins that). |
| Interfaces consumed | IF-1 `Array` (`NDArray[np.float32]`, `(H, W, 3)`, RGB, `[0, 1]`); IF-10 `Settings.force_cpu` (read only). |
| Wave-2 consumers | WP3.2 and WP3.3 (opus-high, "after WP3.1", frame section 3) and WP3.5 colour (opus-high, after WP3.1). Later: WP3.4, WP3.11, WP3.14 (`select_backend`, the AD-9 reason string), WP3.16 (device shown in the status bar, AD-9). Stubs they use until this merges: `stubs.StubArrayBackend` (NumPy identity for `asarray`/`to_host`; every image operation raises) and `stubs.select_backend` (returns the stub with `"CPU: forced"` or `"CPU: stub"`). WP3.16 builds against those two. |
| Hardware flags | `gpu` on every CuPy test (skips when no CUDA device or CuPy is absent). `footage` and **EXCLUSIVE** on the speed row (task 7) only: plan 4.3 and frame rule 7, best effort on a shared laptop (owner 2026-10-19), strays and clocks recorded, contaminated rows kept as spread. Footage read-only, through `tools/local_config.find_footage_file`; tests skip when it is absent. |
| Out of scope | Any correction step (compensation, white balance, fusion weights, the blend: WP3.2-3.4); video colour conversion and chroma resampling (WP3.5, AD-10: FFmpeg swscale); decode, encode, I/O of any kind in `src/`; tiled processing (D111 "no tiled processing in v1"); the Phase 3 optimisation package and any optimisation candidate of the gate report (FFT or recursive Gaussian, device-resident pipeline) unless CHARC widens scope at Gate 1 (open question 5); multi-GPU (DR-2); reading any GPMF, IMU or GPS data (owner ruling); importing `tools/prototype` from `src/`. |
| Done | Plan 4.5; frame section 2 rules 1-11 apply; ruff check, ruff format --check, mypy strict (`src/clearwater`, `tools`), the full pytest green with and without CuPy importable; AD-11 agreement shown; the speed row recorded or its absence stated; Reviewer A converged. |

## Task ladder

1. **Read and table (round 0 yield).** Read IF-2, `tools/prototype/backend.py` and the
   prototype functions each IF-2 method mirrors (`_gaussian`, `_binomial_blur`,
   `gaussian_pyramid`, `expand`, `rgb_to_ycbcr`, `ycbcr_to_rgb`, `normalisation_bounds`,
   `memory_estimate_bytes`, `spatial_sigma`, `pyramid_levels`). Write a ledger table: each IF-2
   method, its prototype counterpart, the border mode, the truncation radius rule, the
   accumulation dtype, and whether bit identity with the prototype is expected. YIELD for the
   dispatcher before writing product code. Anything the table cannot settle is a STOP.
2. **NumPy backend** (`name = "numpy"`, `device = "cpu"`). float32 in and out of every method;
   `asarray` refuses any dtype but float32 (as the stub does).
3. **Gaussian blur.** Symmetric borders and 4-sigma truncation (IF-2 docstring). The radius
   rule must equal the prototype's (SciPy: `int(4 * sigma + 0.5)`; DR-19 item 3 records the
   prototype's half-pixel mismatch in its bound check). SciPy versus own kernels is the cell's
   measured choice (frame section 4 "prefer own kernels"): record speed and identity for both
   on a 4K plane at the c3 kernel sigma (AD-8: 0.05 of the short side) and at the sharpen sigma
   (0.005). Whichever is kept, CPU and GPU use the same radius rule and border mode.
4. **Pyramids, YCbCr, percentile.** `pyramid_reduce` and `pyramid_expand` as IF-2 says ([1 4
   6 4 1]/16; even rows and columns kept; zero-insert, same filter, normalised) and as the
   prototype computes them, odd sizes included. `rgb_to_ycbcr` / `ycbcr_to_rgb` for the
   matrices and ranges of open question 2; a name outside that set raises `ValueError`.
   `percentile` R-7 (linear), taken over the whole array (AD-4 takes N{} bounds jointly over
   channels).
5. **CuPy backend** (`name = "cupy"`, `device = "cuda:0"`). CuPy is imported only inside
   `clearwater.core`, lazily, so `import clearwater.core` works with CuPy absent.
   `free_device_bytes` reports free device memory; the reasoning about the memory pool versus
   the driver's free figure goes in the report.
6. **Memory estimate and selection.** `memory_estimate_bytes(height, width, method_id)` per AD-1
   from the prototype's counted formula (`tools/prototype/backend.py`: 50 1/12 float32 planes x
   1.25 + 1 MiB), per open question 3. `select_backend`: CPU with `"CPU: forced"` when
   `settings.force_cpu`; GPU (`"GPU"`) when a CUDA device is present and the estimate is below
   free device memory; else CPU with the reason in the IF-2 format (`"CPU: estimate 1,982 MiB
   exceeds free 1,200 MiB"`); a reason for "no CUDA device" and "CuPy not installed" in the
   same `"CPU: ..."` form, listed in the round 0 table.
7. **Speed row (EXCLUSIVE, best effort).** On GX011627 frames (681 frames, 4K, 30000/1001): the
   IF-2 operations at the AD-8 sigmas and pyramid depth, product against prototype, GPU and
   CPU, over the full clip per plan 4.3, with GPU clocks, temperature and stray processes
   recorded before, during and after. What exactly is timed is open question 4. The
   dispatcher grants the exclusive window; do not start it unasked.
8. **Tests.**
   - CPU against GPU on every method within AD-11 (max 2e-3 absolute per channel, mean 2e-4);
     same device run twice bit-identical (AD-11, N10).
   - Product against prototype outputs (DR-19 per the frame and architecture section 4):
     bit-identical where the same routine is used, else within AD-11's bound, the measured
     maximum reported (open question 6 on how references are recorded).
   - Edge cases (V1): uniform image, near-zero red channel, 1 x 1 and odd sizes, sigma under
     1/8 px (kernel `[1]`), 16-bit-derived input values.
   - `select_backend`: forced, fits, does not fit (free memory mocked), no device, CuPy absent
     (import mocked); the reason strings exactly.
   - A planted wrong implementation fails by name: a wrong radius rule, a `wrap` border, a
     float64 leak, a wrong matrix row.
   - Dependency rule (plan 8.1, frame rule 5): a subprocess test that importing
     `clearwater.core` loads nothing from `clearwater.io`, `.jobs`, `.gui`, `.methods`, nor
     `PIL`, `av`, `PySide6`; and a static check that no module outside `clearwater.core`
     imports `cupy` or `cupyx`.

## Declared operating envelope

Windows 11; Python 3.12; NumPy and CuPy (`cupy-cuda12x` 14.x) as locked; one NVIDIA RTX 4070
Laptop GPU, 8 GB (D117); images up to 4K video frames and 48 MP photos for the estimate (D117,
spec 12 "Memory"). Out of envelope: multi-GPU (DR-2), non-NVIDIA devices, other operating
systems (the code is portable, N1, but not run there), sustained thermal behaviour (gate report
Result 1 row 7).

## Review loop (Reviewer A), per `docs/review-gate-clearwater.md` Part 1

- Tier **STRONG**. Evidence `C:\Users\rwsmy\clearwater-review-evidence\wp3.1\rN\`; ledger
  `docs/proofs/wp3.1-ledger.md`. Copy the runner and prompt shape from
  `C:\Users\rwsmy\clearwater-review-evidence\wp2.2\r3\run_review.sh` and `review-prompt.md`;
  the reviewer excludes `docs/proofs` with `--glob '!docs/proofs/**'`. Five-round gate.
- **WHAT TO EXAMINE:**
  - each IF-2 method against its docstring and the prototype (radius, borders, odd sizes,
    the expand normalisation, matrix coefficients, R-7);
  - float32 throughout; no silent float64 result; no host round trip inside a GPU method;
  - CPU against GPU and product against prototype, measured not asserted;
  - `select_backend` reasons and the fallback rule (D111, AD-1, AD-9);
  - the estimate's derivation and its use as a bound;
  - CuPy optional: the package imports and the CPU suite passes without it;
  - the pyproject lines exactly as granted; no other dependency;
  - the speed row's exclusivity record and its limits.
- Reviewer B is the orchestrator's seat pass on the merge candidate.

## Notes for the cell

- **Return report** = your FINAL message, under about 70 lines (`docs/dispatch-recipe.md`
  section 4): the method table (IF-2 method, implementation, identity or measured deviation),
  the AD-11 figures, the `select_backend` reason list, the pyproject diff, the speed row (or
  why it was not run), the gates, the Reviewer A rounds and verdict, open items.
- **STOP for:** any IF-2 signature or docstring that cannot be met as written (AD-20); a
  tolerance looser than AD-11; a dependency beyond the frame section 4 grant; any OS-specific
  code (AD-23 approves only the pipe buffer, which is not this package's); a prototype
  numeric that disagrees with the spec; the round 0 table showing a choice the brief left open.
- **Working rules:** `uv sync`. Commit by pathspec, `feat(wp3.1): ...`, with a
  `Co-Authored-By:` footer naming your model. Never a bare `cd`. Never post to a mailbox. The
  full pytest (8-15 min, 892+ tests) runs in the background with output to a file under
  `work/`. Gates: ruff check, ruff format --check, mypy strict, full pytest; the harness gate
  only if you touch `scripts/`, `.claude/`, kernel docs or `tests/harness/` (you should not).
  Report `docs/reports/wp3.1-array-backend.md` (claims, evidence paths, limits). Yield at every
  round boundary; the dispatcher reads your depth (~250K evaluation, ~400K stop).

## Rulings (CHARC `871a371855bb1630`, 2026-10-20)

The questions below were raised as drafted. **Every recommended answer is the ruling**
unless a line here amends it. Cross-brief rulings: X1 (owned files outside the module path,
below), X2 (WP3.15 ships `clearwater.config.paths` at its round-0 yield), X3 (manifest ids filled
at dispatch from the merged WP2.3 manifest), X5 (parallel cells allowed; the dispatcher
serialises full-pytest runs at gate windows; inner loops run only the cell's own tests).
- **X1:** WP3.1 owns `tools/core_speed.py` (the speed-row instrument).
- **1.1 amended (addition):** an elementwise array-module accessor (`backend.xp`) is ALLOWED and
  used ONLY inside `clearwater.core`; a dependency test fails if any module outside `core`
  touches it or imports `cupy`/`cupyx`.
- **1.5 / X4:** this brief is the base scope; any Gate 1 growth (owner option B or C, AD-21) is
  added as a named section by amendment.

### Questions as drafted (recommended answer = ruling unless amended above)


1. **Operations the plan names beyond IF-2.** Plan WP3.1 lists "Gaussian and Laplacian
   pyramids with depth set by minimum level size", "the conversion saliency needs" (the
   prototype's `srgb_to_lab`, `luminance`, and a Laplacian via `ndimage.laplace`), "whole-frame
   statistics", and the D56 fraction-to-pixels conversion ("the backend converts to pixels",
   architecture section 3). IF-2 carries none of these, and methods may not import CuPy.
   Recommended: WP3.1 provides them as plain functions in `clearwater.core` that take an
   `ArrayBackend` (`spatial_sigma`, `pyramid_levels`, Gaussian/Laplacian pyramid build and
   collapse, `rgb_to_lab`, `laplacian`, channel means), with no change to IF-2 (AD-20 intact);
   WP3.2/3.3 import them. Also say whether an elementwise array-module accessor is allowed.
2. **Matrices and ranges of `rgb_to_ycbcr`.** The plan says "RGB↔YCbCr (BT.709)"; D47 fixes
   BT.709 for 3C; IF-2 takes `matrix` and `range_`; video YCbCr is FFmpeg's (AD-10).
   Recommended: support `bt709` full (the prototype's convention, Cb/Cr in [-0.5, 0.5]) and
   limited, and `bt601` full and limited; refuse `identity` and `unknown`.
3. **The estimate before the product pipeline exists.** AD-1 adopts the prototype's formula;
   the product core (WP3.2-3.4) may hold a different peak. Recommended: implement the formula
   for both method ids now, and put the re-check of the product peak (a counting allocator, as
   WP1.2) in WP3.4's brief.
4. **What the speed row times, and where its instrument lives.** WP3.1 has no correction
   method, so "the gate report's core figures" (0.395 s ancuti2018 / 0.639 s c3 per 4K frame)
   cannot be re-measured whole. Frame rule 1 owns no `tools/` file. Recommended: time the IF-2
   operations as the c3 and ancuti2018 paths call them, product against prototype on the same
   frames, and own one instrument `tools/core_speed.py` (mypy-checked, decoding through the
   FFmpeg CLI); the whole-core row waits for WP3.4.
5. **Gate 1 scope growth.** AD-21: if the owner picks B or C, "the optimisation package ... is
   WP3.1's scope growth plus a named Phase 3 package". Recommended: this brief stays the base
   scope; CHARC adds any growth as a named section before dispatch.
6. **How prototype references are recorded.** Recommended: computed in the test by calling the
   read-only `tools/prototype` on seeded synthetic inputs and the WP2.3 stills (tests may
   import `tools/`, `src/` may not); no committed arrays.
7. **The `[gpu]` extra.** AD-18 names `cupy-cuda12x[ctk]`; the commission says
   `cupy-cuda12x`. Moving CuPy out of the `dev` group drops it from `uv sync` (extras are not in
   `default-groups`), so GPU tests and the prototype GPU tests would skip. Recommended: extra
   `gpu = ["cupy-cuda12x[ctk]>=14.2,<15"]`, and keep the `dev` group line so the developer
   environment still has CuPy; the install instructions (WP5.5) name the extra.
8. **DR-19 scope.** DR-19 lists five prototype-validation items for "the product's parameter
   schema and validation package". Recommended: WP3.1 closes none of them; it adopts the SciPy
   radius rule so item 3 does not recur in the product, and WP3.4 owns the rest.
