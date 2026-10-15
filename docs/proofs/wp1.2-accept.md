# WP1.2 Part A — Accept record

**Accepted 2026-10-15 by the orchestrator** (session `clearwater-orchestrator-20261014-1258`),
on CHARC's commission `f1a60e57e0668069`. Gate per `docs/review-gate-clearwater.md` Part 2.
Part A only: Gate 1 is NOT declared here (CHARC, at WP1.6, with Part B).

| Item | Value |
|---|---|
| Brief | `docs/briefs/wp1.2-brief.md` (FINAL `809c9b2` + `d27f909`). CHARC rulings: `22f68342748b43f2` (ctk extra stands; record the install footprint) and `4db6db642c117b1e` (F1 Option A with near-flat bound 1e-4 / 1e-5; F2 `--device` default cpu; two interface deviations accepted; DR-14). CHARC disposition of the window slip: `122f9a10cf1323f5` |
| Base SHA | `d27f909` |
| Author head | `a2e3d52` (branch `wp1.2`, implementer-opus-high; depth 230K at the STOP, 319K at first return) |
| Merged head | `f6d998a` (branch `wp1.2-mc` = `wp1.2` rebased onto main `b4a397b`; main fast-forwarded) |
| Byte identity | `git patch-id --stable` = `3e72fec5fb623fbab65b1b404b33fdef6fb74340` before (d27f909..a2e3d52) and after (b4a397b..f6d998a) |
| Merge integration | Main's intervening commits are docs only: briefs, state pointers, the debt register, `CLAUDE.md`, and spec v0.5.1 (`073ca1f`, text only). No file overlaps the arc. Both gate surfaces ran on the merged head. |
| Reviewer A | Codex STRONG (gpt-5.6-sol / high), WSL, codex-cli 0.162.1. r1 on `9274651`: 0/0/3 (2 in envelope, 1 out), NO_NEW_CRITICAL_MAJOR, converged; minors fixed in `dd93979`. Ledger `docs/proofs/wp1.2-ledger.md`, with addenda for the stray stop and the overlap discard. The depth column is dispatcher-read and recorded here. |
| Reviewer B | Independent implementer-opus-high cell, brief `docs/briefs/wp1.2-review-brief.md`; depth 160K after pass 1. |
| Evidence | `C:\Users\rwsmy\clearwater-review-evidence\wp1.2\`: `probe`, `r1` and `analysis` (A); `B` and `B2` (B). Bench records: `C:\Users\rwsmy\clearwater\work\wp1.2a\` (author), `...\work\wp1.2a-B\` and `...\work\wp1.2a-B2\` (B). |

## Reviewer B passes

- **Pass 1** on `9408d18`: **BLOCKING**, on F1 only.
  - F1: the two GPU c3 cells did not reproduce within 10% of the author's first window
    (-14.0% and -16.6%). Every other cell reproduced within 4.9%; memory matched to the byte.
  - Claims 1–4 and 6–8 PASS; the mechanism is sound.
  - Minors:
    - F2: context-figure arithmetic.
    - F3: a host round trip that returns a CuPy array was not caught.
    - F4: memory readings labelled against the wrong loop.
  - Codex pass valid (0 withheld-path accesses). Prompt md5 `90ecf1eace901f83be1a4ebc3cc3479e`,
    transcript md5 `15ae3af650657b10c67618989f9ab260`.
- **Author fixes:**
  - `bench.py`'s `ambient` now records the power-mode overlay and the GPU state (clocks,
    temperature, power, P-state, throttle reasons) at the start and end of each loop.
  - The GPU cells were re-measured with no stray process (window 3, head `72c19cc`). The first
    window is kept in a spread table.
  - F3 guard and 2-D `expand` GPU test added. F2 and F4 corrected.
- **B2** on `873ae6d`: **NO_BLOCKING**.
  - All four GPU cells reproduce the report's rows within 4.1% (+0.6%, -4.1%, +0.2%, -0.2%).
  - F2–F4 resolved by reproduction; the F3 guard catches both round-trip mutants.
  - The timed path is unchanged (empty pipeline/backend/params diff; bench additions sit
    outside the timed region).
  - `-m gpu`: 17 passed, 0 skipped. No Codex pass was needed (the mathematics is unchanged).
  - One minor, N1: 3C spread wording. Fixed in `a2e3d52`, report only.

## Gate checks (orchestrator seat, merged head `f6d998a`, main tree, after `uv sync`)

```
uv run ruff check .            -> All checks passed!
uv run ruff format --check .   -> 52 files already formatted
uv run mypy                    -> Success: no issues found in 10 source files
uv run pytest -q -rs           -> 331 passed, 1 warning in 64.68s   (0 skipped: footage folder present, ffmpeg on PATH)
uv run pytest -q -m gpu        -> 17 passed, 314 deselected
python -m unittest discover -s tests/harness -> Ran 366 tests ... OK (skipped=1)
```

The one warning is CuPy's "CUDA path could not be detected" notice, documented in the report;
it is harmless with the `[ctk]` wheels. The same gates, plus `-m gpu`, were green on the merge
candidate before the fast-forward.

- **Witness (orchestrator, main):**
  - On a synthetic 900x600 image, `run.py --method c3 --device cpu` and `--device gpu` both exit
    0.
  - `correct()` CPU against GPU on that image: max-abs 2.80e-6, mean-abs 2.61e-7 (tolerance
    2e-5 / 2e-6). NumPy in gives NumPy out.
  - `--help` gives `--device` default cpu, "for the same result on every machine; gpu is
    opt-in" (F2 ruling).
  - `bench.py --device cpu --size 128x72 --frames 3` writes its JSON record.
  - CuPy 14.2.0 sees 1 device.
- **Locks (B pass 1, re-checked by B2):**
  - Only owned files changed. `tests/test_prototype_pipeline.py` and `tests/conftest.py` are
    untouched; nothing under `src/`.
  - The only `pyproject.toml` change is `cupy-cuda12x[ctk]>=14.2,<15` in the dev group, with no
    mypy override.
  - `uv.lock` adds cupy-cuda12x, cuda-pathfinder, cuda-toolkit and 8 `nvidia-*-cu12` wheels.
  - No machine-wide environment change; no toolkit install.

## Figures (SYNTHETIC; full table and ambients in `docs/reports/wp1.2a-speed-memory.md`)

| Cell | Median s/frame | 30 fps budget share | Peak graphics memory (pool reserved) | Head measured |
|---|---|---|---|---|
| GPU 4K ancuti2018 | 0.389 | 3.5x | 1712 MiB | `651146b` (timed code = `72c19cc`) |
| GPU 4K c3 | 0.652 | 5.9x | 1712 MiB | `72c19cc` |
| GPU 5.3K ancuti2018 | 0.836 | 7.5x | 3275 MiB | `72c19cc` |
| GPU 5.3K c3 | 1.503 | 13.5x | 3275 MiB | `72c19cc` |
| CPU 4K ancuti2018 / c3 | 10.97 / 23.39 | 99x / 211x | n/a (RSS 1.6 GB) | `d3d9555`, stray process present |
| CPU 5.3K ancuti2018 / c3 | 24.55 / 57.99 | 221x / 522x | n/a (RSS 3.1 GB) | `d3d9555`, stray process present |

- The memory estimate is 1.16x the pool's reserved peak.
- The GPU c3 cells measured 10–18% slower in the first window (overlay and clocks not recorded
  then). The spread table carries all three windows.

## Dispositions

| Item | Disposition |
|---|---|
| GPU core 3.5–13.5x over the N6 per-frame budget, before decode/encode | RECORDED as a SYNTHETIC result. Gate 1 is CHARC's at WP1.6 with Part B; the owner decides the target or approves optimisation work. Not optimised here (CHARC). |
| CPU/GPU agreement on the near-flat `_synthetic` pair exceeds 2e-5 / 2e-6 | RULED (Option A): kept as a test with its own bound (1e-4 / 1e-5) and the cause documented. N{} ill-conditioning banked as DR-14. |
| `[ctk]` extra: 8 `nvidia-*-cu12` wheels, LicenseRef-NVIDIA-Proprietary; cuda-toolkit meta-package without license metadata | Dev group only, within the grant (CHARC). The N13 adoption question goes to WP2.1. Plain cupy failed on "Failed to find CUDA headers". |
| Partial CUDA 12.4 folder on the machine (`include`/`lib` only); CuPy "CUDA path could not be detected" warning | Recorded in the report; harmless. |
| B2 N2: `bench.py` `_windows_power()` is Windows-only `ctypes`/`powrprof` code (guarded by `sys.platform`, returns nothing elsewhere) | ACCEPTED at this seat, SUBJECT TO CHARC QA (CLAUDE.md: OS-specific code needs approval). Instrument-only, in `tools/prototype/bench.py`, never product code; it records the power-mode overlay that B's F1 showed matters. |
| Remaining F3 blind spot: `ndarray.get` / `set` / `tolist` cannot be patched | Stated in the report; no such round trip exists in the code. |
| `--note` and `--seed` options on `bench.py`; a supplementary device-resident timing | Additive; labelled as not the brief's figure. |
| Stray PID 33616 (a hung `python -` from WP0.1 Reviewer B) | It was present during the CPU rows and GPU windows 1–2. Stopped about 05:20Z on the owner's direction. The GPU rows come from the clean window 3; the CPU rows are labelled. |
| Orchestrator harness run overlapped the window-3 GPU 4K ancuti2018 cell (05:29:30–05:30:15Z) | That record was discarded and kept as `DISCARDED-overlapped-harness-run-...json.txt`, then re-run (0.389 s against 0.391 s). CHARC: the harness gate counts as heavy inside a bench window. |
