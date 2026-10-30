# WP-DR87 accept record (orchestrator generation 26, 2026-10-30)

**Package:** WP-DR87, the bench stray-check cost (DR-87) and two `from_tiff` debts (DR-93, DR-94).
- **Commission:** CHARC `d509a3c2` (gen 23's order), one package (CHARC `01a75bbc`). **Brief:** `docs/briefs/wp-dr87-brief.md`, FINAL on CHARC `ef92adc8a9a240b8` (Q1 = the test-side fixture, `bench.py` untouched; Q2 = 37724 + 50740).
- **Later rulings:** round 0, CHARC `492c000c93b33597`: the DR-94 list FINAL = 37724 ImageSourceData + 50740 DNGPrivateData (KEPT: 50341 PrintIM, 50255 Photoshop Annotations, the existing 700 / 33723 / 34377 / 34675); R0-C (`test_bench_works_as_a_script`, 33.83 s on the parallel leg) NO remedy. At the gate, CHARC `b0d679b06033a23b`: the DR-87 closure note's wording (below) and the B advisories as report text only.
- **Lane: CODEX**, `implementer-codex-sol-high` (`gpt-6.1-sol`/high), one session `01a18a83-594f-78a0-b28e-af293376b91b`, four turns, driven by `scripts/codex_cell.py`; commits made at this seat with the GPT-6.1 Sol footer. Depth (input tokens) after turns 1-4: 131,491 / 155,735 / 171,077 / 190,246 (window 475,000). Paces at dispatch: Codex 0.38 vs Claude 1.434 (01:52Z); at this accept 0.368 vs 1.45 (03:12Z).
- **Both nets** are the Claude pass (`claude-opus-5-5`/high, read-only), the other model.
- **Report:** `docs/reports/wp-dr87.md`. **Ledger:** `docs/proofs/wp-dr87-ledger.md`.

**Candidate:** `wp-dr87-mc` `80bd029` = the author branch `wp-dr87` `8b05e78` (base `00518bb`) rebased onto main `9ae9bf9` with `git -c core.autocrlf=false`. `git patch-id --stable` excluding the report: `b0e96790` on `00518bb..wp-dr87` and on `9ae9bf9..wp-dr87-mc`.

**Footprint:** `tests/test_prototype_backend.py` (one autouse fixture, copied with its docstring from `tests/test_prototype_clip.py`); `src/clearwater/io/photo/exif.py` (`MemoryError` in `from_tiff`'s one `except`; `_TIFF_STRUCTURE` += 37724, 50740 with its comment; the docstring sentence "left out of IFD0"); `tests/test_io_photo_exif_bytes.py` (two new tests); the report, the ledger, this record. `tools/prototype/bench.py` untouched (`STRAY_SAMPLE_S` stays 10.0); no `src/clearwater/interfaces/`, `pyproject.toml` or `uv.lock` change; no dependency. Every changed blob has 0 CR bytes.

**The changes, RED-first:** RED `51a90dd` (both new tests; at the seat's light run exactly these two failed: `MemoryError: synthetic rewrite exhaustion`; `AssertionError: private IFD0 blobs retained: [37724, 50740]`), fixture `4d066da`, GREEN `42309c0`; R1 cleanup `8a9ca70` (docstring only).

**DR-87 figures** (the node `tests/test_prototype_backend.py::test_bench_gpu_records_graphics_memory`, at this seat, nothing else heavy; a tools-cost figure, not a spec row):

| Run | Head | Call | pytest | Wall | EXIT |
|---|---|---|---|---|---|
| Before (R0-A, 02:08Z) | `00518bb` code | 87.01 s | 90.93 s | 96.684 s | 0 |
| After (02:23:03Z) | `d301d98` (fixture on, product unchanged) | 24.24 s | 25.24 s | 26.511 s | 0 |

R0-B (cProfile, 66.56 s profiled): `bench.py:1305(stray_processes)` 4 calls 63.24 s cumulative; `_PeakRssSampler.stop` 0.606 s. The ratio assertion passed in every node run.

## Nets

| Net | Result |
|---|---|
| Reviewer A R1 (on `wp-dr87` `5103ef9`, base `00518bb`; `clearwater-review-evidence\wp-dr87\r1\`, `md5sums.txt`) | **NO_NEW_CRITICAL_MAJOR**: 0 / 0 / 0 and 4 advisory; model `claude-opus-5-5`, 22 turns, `is_error` false, worktree clean after, 4 permission denials (a `mkdir` and the sandbox-shim form; it re-ran). Its light run 343 passed. A1 (docstring: "from IFD0") and A3 (a short line) FIXED in `8a9ca70`; A2 (the empty `MemoryError` message: the warning text is locked) and A4 (dead `source.tiff` writes, the sibling tests' form) DECLINED. **Converged at R1.** |
| **Reviewer B** (a process at this seat, `scripts/codex_cell.py`'s pinned pass run by hand so the author's report is excluded from the diff, on `wp-dr87-mc` `80bd029`, base `9ae9bf9`; prompt from the brief and the rulings, without A's findings; `clearwater-review-evidence\wp-dr87\reviewB\`, `md5sums.txt`, `run_review_B.py`) | **NO_NEW_CRITICAL_MAJOR**: 1 minor + 5 advisory; model `claude-opus-5-5`, 32 turns, `is_error` false, worktree clean after (tracked tree), 7 permission denials (`mkdir` / `New-Item`; it used `os.makedirs`). Its light run 343 passed. F1 MINOR: about 23 s of whole-system process scan remains on the node, so the closure note must not say the stray-check cost is gone; the report already says "the stray scan still enumerates the system's processes; the fixture shortens its sampling sleep"; CHARC's note wording below. F2-F6 advisory, banked as report text by CHARC (no rows): no test pins "bare `Exception` not caught" or "50255 kept" (both hold by B's probe); the empty `MemoryError` message; a malformed 37724 now dropped without its read warning; ruled tags outside IFD0 kept (out of envelope). |

## Gate

On `80bd029` (base `9ae9bf9`), run id `dr87g1`, Git Bash, `PYTEST_ADDOPTS` unset, offscreen, the local config copied; the candidate was then rebased onto main `954a1a4` (that range changed `docs/charc-state.md` only; patch-id unchanged) as `d5e84f8` for the merge.
- **Static:** `ruff check` clean; `ruff format --check` 273 files already formatted; `mypy` no issues in 141 source files; 0 CR bytes in every changed blob.
- **Collection:** all 7,119 = parallel 5,973 + serial 1,139 + fullclip 7; no duplicates, pairwise disjoint, union = all. Against main `9ae9bf9`'s 7,117: +2 (`test_from_tiff_drops_private_ifd0_blobs_and_keeps_metadata`, `test_from_tiff_memory_error_returns_none_with_warning`), none removed.
- **PARALLEL:** **5,972 passed, 1 skipped** (the standing swscale refusal, `tests/test_color_roundtrip.py:123`), EXIT 0, 804.82 s (02:53:15Z-03:06:42Z).
- **SERIAL:** 1 failed, **1,128 passed, 10 skipped** (the standing look-check frames, archived to D:), EXIT 1, 1,712.66 s (to 03:35:17Z). The one failure is PRE-EXISTING and outside the footprint (CHARC `fbbab0bf427f3a79`, NEW DR-99): `tests/test_io_video_encode_bench.py::test_run_once_records_the_row_and_deletes_the_output` (`:323`, `-0.05 < offsets["telemetry_origin"] <= 0`): -0.0663 s in the leg; -0.1041 s alone on the candidate (03:36:29Z); -0.0924 s alone on main `9ae9bf9` in the main tree. `tools/video_io_bench.py` stamps the telemetry origin before starting two sampler threads and the run's `started` after, so the offset is the threads' start cost on a loaded host (about 14 `claude.exe` and 2 `codex.exe` processes at the time); it passed at WP-T6's and WP4.4's gates.
- No harness gate (no harness file changed). No footage, `fullclip` or timing window was needed (the brief).
- **Lane share:** Codex-built package 9 (CHARC's count); both nets Claude.

## For CHARC at the release

DR-87 CLOSED with the note (CHARC `b0d679b0`): "the fixture removes the 10 s sampling sleeps of the stray-process check (90.93 -> 25.24 s on the node); the scan itself remains and still enumerates the system's processes (about 23 s); WP-T6's 'sampler stop 16.3 s' did not reproduce (`_GpuSampler` not built in core mode)", and the tool's real-run cost is unchanged by design (`bench.py` untouched). DR-93 CLOSED. DR-94 CLOSED (37724 ImageSourceData, 50740 DNGPrivateData). The bench-ratio mechanism stays an observation (no reproduced flake in this package's runs).
