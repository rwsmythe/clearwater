# WP4.2 accept record (orchestrator generation 19, 2026-10-29)

**Package:** WP4.2, Video path end to end (Phase 4, size L).
- Brief: `docs/briefs/wp4.2-brief.md` (FINAL, CHARC `c8340144a8e87c09`), with its "Rulings" (CHARC `2c4476d9869df056`) and "Revision 1 rulings" sections.
- Governing rulings, each recorded verbatim in the ledger:
  - round 0: CHARC `881cc956f1335e7e` plus the generation-18 seat rulings;
  - build: CHARC `91c2c22f4b6edd18`;
  - Y4: CHARC `2a336830303f3a2d`;
  - V3: CHARC ruling (a), equality on the 24 deciding rows only;
  - CHARC `d0ba2d12` (Reviewer B dispositions concurred).
- Lane: **CLAUDE**, `implementer-opus-high`, four cells in sequence:
  - cell 1: round 0, stood down at 209,438;
  - cell 2: the build;
  - cell 3: build rulings, Reviewer A R1, the V3 CPU/GPU record and the suite, re-seated at 278,978;
  - cell 4: task 10, the Reviewer B remediation, R2 and the docs turns.
- Both nets: Codex `gpt-6.1-sol` / high in WSL, STRONG tier.
- Report: `docs/reports/wp4.2-video-path.md`. Ledger: `docs/proofs/wp4.2-ledger.md`.

**Candidate:**
- Branch `wp4.2-mc`: the author branch `wp4.2` (head `a74fb6d`) rebased onto main `f716417` with `git -c core.autocrlf=false`. Main's moves since `38f291e` (the author branch's base) are CHARC docs only: state pointers, AD-30, the fill's Order bullet.
- The GATED tree is `8bc927a` (`798af0c` rebased onto `246052b`). The merged tree is `922d1c6` (`a74fb6d`, the FINAL docs turn, rebased onto `f716417`), then this record.
- **`git patch-id --stable` `7dfc431f`** on `38f291e..798af0c` and on `246052b..8bc927a`.
- **Code identity with the gated tree:** `git diff 8bc927a 922d1c6 -- src tests tools` is EMPTY, and the code patch-id (`-- src tests tools`) is `af839429` on `246052b..8bc927a` and on `f716417..922d1c6`. `a74fb6d` touches only the report and the ledger.
- **The Reviewer B tree vs the gated tree:** B's re-run read `33f13e5` (= `9aa2783` rebased). The gated tree adds `798af0c` only, which I read at this seat: two docstring paragraphs (`app/composition.py` `_NoCacheFolder`; `tools/headless_export.py` the video-facts paragraph) and the `_parser()` description string. No logic change, and no test pins the old text. CHARC CONCURRED (`a5decb35fcbf75eb`, 09:42:27Z), having read the same diff at `8bc927a`: "no statement outside a string literal changed".

**Footprint (checked at this seat): 15 code and test paths plus the report, the ledger and this record.**
- EDIT:
  - `src/clearwater/app/composition.py` (the real video engine and the builders; `export_jobs()` returns the engine);
  - `src/clearwater/app/__init__.py` (the R0-Q4 re-export; three builders in `__all__`);
  - `src/clearwater/jobs/export.py` (the per-job device-backend hook, `_expected_frames`, DR-71);
  - `src/clearwater/analysis/engine.py` (G1: the frame-count check and DR-47 (a)'s one-shot guard);
  - `src/clearwater/core/backend.py` (ONE docstring line at `block_sums`, DR-73 (a));
  - `tools/headless_export.py` (the video legs, `--cache-dir` through `write_target_refusal`, the record's `"video"` object; `"schema": 1` kept).
- Tests:
  - `tests/test_app_composition.py` and `tests/test_headless_export.py`: the three ruled router pins, R1-Q3's in-place edit, the docstrings and unused imports, and the additive `__all__` names;
  - `tests/test_wp321_fft_release.py`: DR-74's case, with its R2-1 observation window, and DR-73 (b)'s rename;
  - NEW: `tests/test_wp42_composition.py`, `test_wp42_device_backend.py`, `test_wp42_runner_video.py`, `test_wp42_v3_product.py`, `test_wp42_v3_figures.py` (seat-granted at the B remediation), `test_wp42_video_path.py`.
- The rebase collision fix `0109c39`: two `match=` strings, for WP4.2b's earlier naming refusal; granted at this seat.

**Locks, all held:**
- `src/clearwater/interfaces/` is unchanged. So are `jobs/naming.py`, `export_seam.py`, `io/video/`, `cache/`, `methods/`, `config/`, `gui/`, the `tools/` instruments, `pyproject.toml`, `uv.lock` and `tests/conftest.py`.
- WP4.2a's guards and WP4.2b's `except OutputNameError` branch are intact.
- No new dependency. Every changed blob has 0 CR bytes.
- Every write in the tests and windows was under `tmp_path` or `work/`. GX011627 was reached only through `find_footage_file` and its path was never logged. No `gpmd`, IMU, GPS or location tag was read or committed.

## Nets

| Net | Result |
|---|---|
| Reviewer A R1 (Codex, `1fa33a8`; `wp4.2\r1\`) | 0 critical / 0 major / 4 minor, `NO_NEW_CRITICAL_MAJOR`. F1 tool code (`_ObservedSink` records the encoder after a successful open); F2-F4 test-only (plants, the alias static check). Terminating cleanup. md5 `review.txt` `afff4213`. |
| **Reviewer B** (Codex at this seat, `wp4.2-mc` `ab9ea83`, base `38f291e`; `wp4.2\reviewB\`) | **`NEW_CRITICAL_MAJOR_FOUND`**: 2 MAJOR / 4 MINOR / 4 ADVISORY. B1: the test-only `CLEARWATER_WP42_V3_FIGURES` destination reached `mkdir`/`write_bytes` with no footage check. B2: its new-file rule was not atomic. Both introduced here, so ONE bounded remediation (fill Part 2), with dispositions CONCURRED by CHARC `d0ba2d12`. B3-B6 fixed (B5/B6 docs). B7 banked (a CHARC row); B8/B9 report Limits; B10 a DR-58 (b) re-sighting. md5 `review-B.txt` `b1865ba2`. |
| Remediation `5e74d01` (cell 4) | The figures path goes through `write_target_refusal(path, configured_footage_folder())` BEFORE any `mkdir`. The switch is refused when no footage folder is configured. The file is created with `open("xb")` on ONE module-held handle. New `tests/test_wp42_v3_figures.py` (RED first on a scratch stand-in). B2's premise was corrected and reproduced: on Windows, `"xb"` on a dangling link succeeds, so the predicate's rule (ii) is what refuses it. |
| **Reviewer A R2** (Codex, diff `265251f..5e74d01`; `wp4.2\r2\`) | 0 / 0 / 3 minor, `NO_NEW_CRITICAL_MAJOR`; **TERMINATED**. All three were FIXED in cleanup `9aa2783`, test-only. R2-1: DR-74's observation window is deterministic by construction (the sink holds the second write until the drop; 30 s bounds); GREEN 3x, both plants fail, neither hangs. R2-2: the handle closes on a failed first line. R2-3: the exclusive-creation and one-open rows. md5 `review.txt` `010afb87`. |
| **Reviewer B re-run** (Codex at this seat, `wp4.2-mc` `33f13e5`, base `246052b`; `wp4.2\reviewB2\`) | **`NO_NEW_CRITICAL_MAJOR`**: 4 MINOR. Checks: probe READY, exit 0, `gpt-6.1-sol`, the worktree clean after, no withheld path read. B'1 BANKED as a DR-81 (c) candidate: a packet-listing timeout text from `io/video/verify.py:234` carries the FFprobe path; reachable only on a 120 s timeout. B'2-B'4 fixed, docs and help text (`798af0c`). md5 `review-B.txt` `cabd2c51`. |
| Task 10, V4 SAME (cell 4, EXCLUSIVE, 08:42:01Z-08:48:18Z, `ab9ea83`) | **13 of 13 compares SAME** on every MANDATORY and REQUIRED item: GX011627 on the GPU (681/681 frames; the same 8 best-effort items as WP3.21), and the six WP2.3 clips on the GPU and with `--force-cpu`. Record md5s `4922fd54` / `4d892589` / `99294d0a`. GX011627 job elapsed 218.9 s (information only). `vid-hlg` and `vid-pq` were refused by design and are covered by the suite. |
| V3 (cell 3) | The AD-14 bound is asserted pre-encode. CPU/GPU equality is by the 24-row md5 `b72d9e7b` (ruling (a)); the encoded rows are characterisation. |
| **Two-leg gate** (this seat, `wp4.2-mc` `8bc927a`, main `work/` config, own `.venv` from the lock; Git Bash, `PYTEST_ADDOPTS` unset, offscreen; 10.99 GiB free; the ONE gate under the fill's Order bullet) | PARALLEL `uv run pytest -q -rs -n 4 -m "not gpu and not footage and not gui and not slow" --basetemp=work/wp4.2-gate-parallel`: **5312 passed, 1 skipped** (`test_color_roundtrip.py:121`), 659.60 s, EXIT 0 (09:41:40Z-09:52:48Z). SERIAL `uv run pytest -q -rs -m "gpu or footage or gui or slow" --durations=40 --basetemp=work/wp4.2-gate-serial`: **1135 passed, 1 skipped** (`test_photo_check.py:139`), 5313 deselected, 2,621.32 s, EXIT 0 (-10:36:31Z). 5312 = the `401521e` suite's 5304 + the 8 rows of `test_wp42_v3_figures.py`; both skips are the standard gate's. Logs `work\wp4.2\gate-logs\`. |
| Static (this seat, on `8bc927a`) | `ruff check .` all checks passed; `ruff format --check .` 267 files already formatted; `mypy` no issues in 141 source files. Harness gate `uv run python -m unittest discover -s tests/harness`: 382 tests OK (skipped=1). |
| Question 9 | The new serial-leg tests take at most about 207 s by `--durations` (at `401521e`), inside 300 s. At the gate: V3 ad14 28.45 s + 27.48 s, DR-74 19.64 s, V3 jitter 12.56 s + 12.15 s (100.28 s in the top 40); the other four each under the 6.58 s cut-off: **at most about 127 s**. |

**Owed to CHARC's register at this accept:**
- **CLOSE:** DR-67, DR-71, DR-73 (a)+(b), DR-74, DR-45 (b) (both halves; the `unreadable_tail` residual is a Limit), DR-47 (a).
- **Stay open:** DR-47 (b)/(c), triggered by the next `analysis/engine.py` touch.
- **NEW:**
  - the R1-Q4 cache-interior row: `DiskProxyCache` skips a link entry at discovery (`cache/store.py:573`), then writes through it (`:660-666`); trigger: the next `cache/` touch;
  - the B7 row (the import-time witness does not instrument the video constructors; trigger: WP4.3's `test_app_composition.py` touch);
  - DR-81 (c) (B'1).
- **DR-58 (b)** re-sighting (B10, `FFREPORT` inherited by the decoder and test launches).
- **DR-81:** not touched; its trigger moves to WP4.3.
- **WP-T6** (commissioned, AD-30) dispatches after this ff. Its owned test files overlap this package.

**Evidence:**
- `C:\Users\rwsmy\clearwater-review-evidence\wp4.2\`: `r1\`, `r2\`, `reviewB\` and `reviewB2\`, each with `md5sums.txt`.
- Task 10: `work\wp4.2\v4\` (driver `window.sh` md5 `85ca41d6`, `logs\steps.txt`) and `work\wp3.10\wp4.2-v4\`.
- The suite at `401521e`: `work\wp4.2-mc1-*.log`.
- The gate: `work\wp4.2\gate-logs\`.
- The V3 record: `work\wp4.2\v3\window\`.
