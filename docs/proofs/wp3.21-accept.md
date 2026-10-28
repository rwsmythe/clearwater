# WP3.21 accept record (orchestrator generation 16, 2026-10-28)

**Package:** WP3.21 Optimisation, brief `docs/briefs/wp3.21-brief.md` (with its Rulings, and the later rulings Q-R1,
Q-C5a / (A), the quantise placement (a), Q-R2 / Q-R4, Q-R6 `6acded46`, Q-R7, abort-first, serial-leg (A) and the task 10
fix `cadc39fc8a199a57`; AD-1 Amendment 2026-10-28, AD-7 READING 2026-10-27, AD-29). Lane: **Claude**,
`implementer-opus-high`, eight seats (cells 1-8, generations 15-16). Both nets are the CODEX pass (gpt-6.1-sol / high,
read-only). Report `docs/reports/wp3.21-optimisation.md`; ledger `docs/proofs/wp3.21-ledger.md`.

**Candidate:** branch `wp3.21-mc`, which is the author branch `wp3.21` (`8a9b97a`, base `d1e4537`, never rebased by a
cell) rebased with `git -c core.autocrlf=false` onto main `9db55fa` (`0ca1970`). Then the B3 docs fix (`dc86cd0`), then
this record, then a re-rebase onto main's head before the ff-merge. `git patch-id --stable` is equal on
`d1e4537..wp3.21` and `main..wp3.21-mc`. **The last CODE commit is `227ed32`.** After it, every commit is docs only:
- ledger;
- report;
- V4 (`8a9b97a`);
- B3 (`dc86cd0`).

**Code identity (CHARC `1bd3eb2b`):** `git diff --stat wp3.21-mc 227ed32 -- src tests tools pyproject.toml uv.lock` is
EMPTY at this seat, and main has been docs only since `d1e4537`. So the two-leg suite run on `227ed32` (below) is the
candidate's figure by code identity, under the standing rule (WP3.10, WP3.14, WP-T4).

**Footprint (checked at this seat; 24 files):**
- **Package code, edited:** `src/clearwater/analysis/engine.py`, `proxy.py`; `core/backend.py`, `core/memory.py` (the
  task 10 ruling); `io/video/decode.py`, `io/video/encode.py` (Q-R2's grant); `jobs/export.py`; `tools/export_bench.py`.
- **Package code, new:** `tools/analysis_breakdown.py`, `tools/export_oracle.py`.
- **Tests, new:** `tests/test_analysis_breakdown.py`, `test_export_oracle.py` and `test_wp321_*.py` (bench,
  conftest_release, device_frames, device_proxy, fft_gaussian, fft_release, job_memory, overlap).
- **The ruled `tests/conftest.py` fixture** (serial-leg ruling (A), `57a7a2e`).
- The report and the ledger.

**Locks, all held:**
- `src/clearwater/interfaces/`, `jobs/export_seam.py`, `color/samples.py` (back at its base), `pyproject.toml` and
  `uv.lock` are UNCHANGED against main.
- No existing test was edited apart from the ruled fixture.
- `cupy` is imported only under `clearwater.core`.
- Every changed blob has 0 CR bytes.
- Nothing footage-derived is committed; no `gpmd`, IMU, GPS or location tag was read or committed.

**GRANTED retroactively (CHARC `407750217110613c`):** `src/clearwater/analysis/__init__.py` (`05ee507`). It holds six
additive re-exports of the AD-29 Protocol surface (`AnalysisDeviceBackend`, `frame_block_mean`, `frame_pixels_for_proxy`).
The file was outside the brief's owned list and was edited without a grant. **MINOR ledger finding:** it should have been
a STOP. It is not a register row. Reviewer B's prompt listed it as granted.

**IF-8 reporting deviation (ACCEPTED, CHARC `49b70b95`):** the GPU job does not report its device-wide job estimate
itself, because IF-8's `JobResult` is FROZEN. The bench record reports the figure and carries the two-instrument check.
Showing it in the GUI is CHARC's WP4.3 row.

## Nets

| Net | Result |
|---|---|
| Reviewer A R1 (Codex at the cell's seat, `wp3.21\r1\`) | `d1e4537..aa06584`: `NEW_CRITICAL_MAJOR_FOUND`, 0 / 6 / 5. F5 CONFIRMED BLOCKING (D87 growth 0 on a retry over an incomplete entry), fixed failing-first in `9d73fe4`. F2 ruled (a) (abort-first is the design; the order is pinned by a test). F1 / F4 rejected; F3 banked to Limits; F6-F9 went to cleanup. md5 `review.txt` `b2041e90e6246dbc949dcb7c8a58699d` |
| Reviewer A R2 (`wp3.21\r2\`) | `aa06584..9d73fe4`: `NO_NEW_CRITICAL_MAJOR`, 0 / 0 / 1 (a test-helper race, MINOR). The loop TERMINATED. Cleanup ran once (`1df2626`). md5 `review.txt` `48a7f239640c23b85977d27c53e80b15` |
| **Post-convergence change** (no Reviewer A round saw it) | `afad7af..227ed32`, plus the `57a7a2e` conftest fixture just before it. Changes: `jobs/export.py` (the analysis-end boundary pool free); `core/memory.py` (`session_bytes`, `job_device_memory_estimate_bytes`, the measured fit); `tools/export_bench.py` (the two-instrument `memory_check`); tests `test_wp321_fft_release.py`, `test_wp321_overlap.py`, `test_wp321_job_memory.py` (new). Given its own scrutiny in Reviewer B |
| **Reviewer B** (Codex at this seat, `wp3.21\reviewB\`, ONE pass) | On `0ca1970`, the whole package with the post-convergence range named: `VERDICT: BLOCKING (2 critical/major)`. Banner gpt-6.1-sol / high / read-only; 0 `^ERROR`; 16 "succeeded in"; tokens 330,349. All 20 exec commands checked: no withheld path, no git, no footage. md5s `reviewB\md5sums.txt` (`review-B.txt` `f00932176295355c6773ba88d8f35935`). **Adjudicated at the gate, CHARC UPHELD (A), `3c1478caceafdf28`; no B pass 2** |
| Two-leg suite (cell 8, granted windows, `227ed32`, Git Bash, `PYTEST_ADDOPTS` unset, offscreen) | PARALLEL `-n 4 -m "not gpu and not footage and not gui and not slow"`: 4,174 passed, 1 skipped (`test_color_roundtrip.py:121`), 488 s. SERIAL `-m "gpu or footage or gui or slow"`: 1,113 passed, 1 skipped (`test_photo_check.py:139`), 2,685.30 s. Collection 4,175 + 1,114 = 5,289, every new id explained. These are the candidate's figure by code identity (above) |
| Static (this seat, candidate `0ca1970`) | ruff clean; format 250 files; mypy 138 files clean |
| Harness gate (this seat, candidate) | 382 OK (skipped 1) |

**Reviewer B: adjudication (orchestrator; CHARC UPHELD `3c1478caceafdf28`):**
- **B1 MAJOR (EXECUTED), `jobs/export.py:361`.** On a partially extended retry, the D87 re-check scales the bytes the
  lead stored, not the entry's own rate. **NOT A DEFECT** against Q-R6 (`6acded46`: "measure the cache entry's growth
  over the lead, extrapolate per frame"). The own rate is A F5's fallback for a lead that stored nothing.
  - **The finding's source** is the orchestrator's prompt, which paraphrased Q-R6 in the fallback's words. That is a
    recorded gen-16 slip.
  - **B's input is not physical:** it needs a ~15x per-frame swing between proxies of one clip through one codec.
  - **The residue,** few new frames on a retry, is an estimate's noise on a check that refuses before writing; it is
    never a bad output. ADVISORY row.
- **B2 MAJOR (EXECUTED), `tools/export_bench.py:888`.** `memory_check.passes: false` does not stop the bench. **NOT A
  DEFECT** against the task 10 fix: the STOP test is a READING of the record (`passes`, the `OVER` row). That reading
  caught and ruled block 2's breach, and the tool's documented exit statuses (0 / 1 / 2) cover run outcomes only. MINOR
  row.
- **B3 MINOR (EXECUTED), the report.** "each asserted by a test" was false for the block 3 (3,277) and 5.3K re-run (7,901)
  rows. Both are covered (4,065.4 / 10,330.8; `passes` true). **FIXED** on the candidate, docs only (`dc86cd0`).
- **B4 MINOR (EXECUTED), `core/backend.py:684` docstring.** "38 bits at `k = 8`" holds for 8-bit; 10-bit needs 40. The
  bound itself is safe (40 <= 53). Row; not fixed, to keep code identity.
- **B5 ADVISORY (REASONED), `test_wp321_fft_release.py:117`.** The 45-frame sample is shorter than c3's 61-frame lead, so
  the GPU boundary free never runs during rendering. Row.
- **Claims:** CONFIRMED 2, 3, 4, 5, 7, 9; REFUTED 1, 6 (through B1) and 8 (through B2). All three refutations are
  adjudicated as above.
- **Proportionality** (CHARC): a fix would cost about 64 min of exclusive suite, a remediation cell and a second B, and
  neither finding changes an exported pixel or a figure of record.

## Results (figures of record; the report holds the evidence paths)

**V16 at 4K (D106 interim 25 min/min, aim ~10), before -> after:**

| Row | Before | After |
|---|---|---|
| GX011627 c3 cold x3 | 31.80-31.93 | **9.57 / 9.78 / 9.92** |
| GX011625 c3 cold, sustained (block 3, 14,938 frames) | 31.26 | **9.58** (0.3195 s/frame) |
| Warm | 23.21 | 9.06 |
| ancuti2018 | 21.58 | 8.74 |
| libx265 (the CPU fallback) | 35.60 | 14.59 |
| Device frames OFF | - | 17.25 |
| 5.3K 8:7 (best effort) | 136.03 | 36.65 (the block 2 re-run on `227ed32`) |

**Speed:** D106 is MET on every 4K NVENC row. The export is now analysis-bound (about 0.314 s/frame), so the slow frames
are the `STREAM_STEP` record waits (CHARC's register row). Block 3's thermals were a 95 C peak, the power cap, and the
last quarter's frames about 4 % slower; a stray `System` process ran at 26.8 % CPU. Both are recorded as spread, not as a
limit (`1bd3eb2b`).

**Oracle:**
- TIER 1 on every leg for #1-#3: the overlap, the device frames and the device block sums.
- #4 (FFT Gaussian): TIER 2 on renders (GX011627 max 7.06e-6, mean 7.95e-7), with the records, the proxies and the
  analysis bit-identical. The FFT is within 2.92e-6 of the direct filter, against the 1e-5 bound.

**N4 and memory (two instruments, task 10 fix):**
- GX011625: (i) device-wide 3,277.0 <= 4,065.4 (BINDING at 4K); (ii) pool 1,510.8 <= 2,173.8.
- 5.3K re-run: (ii) 4,311.7 <= 6,281.4 (BINDING at 5.3K); (i) 7,901 <= 10,330.8.
- Peak RSS at most 7,753 MiB.
- Fit (exact on four points, rounded up, no clamp): NVDEC 80 MiB + 51 B/px; NVENC 368 MiB + 36 B/px; context 272 MiB.
  `select_backend` is UNCHANGED.

**V4 SAME (granted window 17:58Z-18:05Z):**
- 13 compares, every MANDATORY and REQUIRED item SAME. They cover WP2.3 hevc8-bt709-full, hevc10, untagged, vfr, rotated
  and truncated (D86 notes) on the GPU device-frames and CPU legs, plus GX011627 c3.
- Only BEST-EFFORT container items differ: D86's not-carried set and the sink's mux.
- Records: `work\wp3.10\wp3.21-v4\` (the tool's own root). The 13 kept outputs are under `work\wp3.21\oracle\v4-*\out\`,
  uncommitted, and are not deleted without a grant naming them.

## Cell depths (dispatcher-read, `scripts/cell_depth.py`)

| Seat | Final depth |
|---|---|
| Cell 1 (task 1, task 2, round 0) | 359,040 |
| Cell 2 (#1 overlap, interim 1) | 310,465 |
| Cell 3 (Q-R6, #2; STOP on AD-29) | 251,077 |
| Cell 4 (#2 under AD-29, #3, interim 2) | 257,383 |
| Cell 5 (micro-timing, Q-R7, task 6 #4, oracle legs) | 326,666 |
| Cell 6 (Reviewer A R1 / R2, cleanup, suite; serial leg 1 STOP) | 257,959 |
| Cell 7 (ruling (A) fix, task 10 blocks 1-2, the 5.3K STOP, the task 10 fix) | 346,814 |
| Cell 8 (two-leg suite, block 3, report, V4) | 257,412 at stand-down |

## Debt and owed rows (CHARC at QA, `3c1478caceafdf28`)

- **ADVISORY (B1):** take the larger of the marginal and the own rate in `_Analysis.cache_growth_bytes`. Trigger: the
  next touch of `jobs/export.py` (WP5.2 or WP4.2).
- **MINOR (B2):** `export_bench` exits non-zero and stops the plan on `memory_check.passes: false`. Trigger: WP5.2's
  re-measure.
- **MINOR (B4 + the misnamed test):** the `core/backend.py` block-sums docstring (10-bit needs 40 bits), and the rename
  of `test_a_video_job_releases_at_the_analysis_end_and_after_every_frame`, which asserts two releases. Trigger: WP4.2's
  touch of `core/backend.py` / the next touch of `test_wp321_fft_release.py`.
- **ADVISORY (B5):** a boundary-free case longer than the c3 lead at a gated resolution (WP4.2 or WP5.2).
- **CHARC's four rows:**
  - WP4.2: `device_backend`.
  - WP4.3: the GUI preview's FFT-plan release, plus the IF-8 / IF-2 note (showing the job's device-wide figure).
  - DR-63: CLOSED.
  - The analysis-bound overlapped export: the `STREAM_STEP` waits.
- **Dispositions as the report states them:** DR-63 CLOSED; the WP3.11 in-block `import logging` style debt CLOSED;
  DR-40 (b) measured negligible (0.15 %); DR-62, DR-45 (a) and DR-47 not reached; DR-64 not this package's.
- **Next speed target:** the analysis pass (the job is analysis-bound).

## Main gates

Main after the ff-merge = the candidate re-rebased onto main's head, plus this record. Every commit since `227ed32` is
docs only. The two-leg suite on `227ed32` stands as main's figure by code identity, and the harness gate is re-run on
main.
