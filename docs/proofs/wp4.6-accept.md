# WP4.6 accept record (orchestrator generation 29, 2026-11-01)

**Package:** WP4.6, Export process isolation: every video export runs in a spawned Python worker process (the AD-23 spawn helper), the parent conversing with it over an ASCII JSON line protocol on binary pipes; photos stay in-process. The follow-on to WP4.3's open V7 STOPs (c) and (e) (DR-98).
- **Brief:** `docs/briefs/wp4.6-brief.md` (FINAL at `b6a31b5`).
- **Rulings** (each verbatim in the ledger or saved under `clearwater-review-evidence\wp4.6\`): round 0 `a265489d371695e2` (R0-STOP-1 exact scope, R0-STOP-2 no environment change, Q2, Q3, Q5, Q6, Q9, Q11, grants (b) (c), N6, (e)); R1 `e15d408a`; R2 `55959e2f` ((d): the stderr tail leaves the failure text) and the spawn rule `3ed8335f`; R3 `acc0255dbda23ae2` (THE CAP: R3 the last full round, a terminating clean-up); the V7 window `d42c9126` (main, CHARC's record); Reviewer B disposition `bc6847dd789bedd4` (B-1..B-3 one remediation; the parent's progress bound); the clamp `89a98d5847161adc` (final progress rule); the narrow B re-run `0650fd0d` (B2-1, B2-2 BANKED; gate now).
- **Lane: CLAUDE**, `implementer-opus-high`, six cells in sequence (cells 1-4 build and rounds 1-3; cell 5 the R3 clean-up, the report, the B remediation and the 2**31 bound; cell 6 the clamp). Both nets Codex `gpt-6.1-sol` / high, the other model. Depth readings per cell are in the ledger; cell 5 254,693 at the B return (09:31:35Z); cell 6 a bounded fresh load, retired at its yield.
- **Report:** `docs/reports/wp4.6-export-process.md`. **Ledger:** `docs/proofs/wp4.6-ledger.md`. **Evidence:** `C:\Users\rwsmy\clearwater-review-evidence\wp4.6\` (`r0`..`r3`, `windows`, `reviewB`, `reviewB2`, the cell prompts, the rulings).

**Candidate:** branch `wp4.6` rebased onto main `07e0db6b` = **`e3b53d68`** (57 commits on base `b6a31b5`). The gate ran on the same patch rebased onto `edec3c17` (`d674836f`); main's three later commits (`f02f9674`, `dfd855fa`, `07e0db6b`) are docs only (no `src`, `tests`, `tools`, `scripts`, `.claude`, `pyproject.toml` or `uv.lock` path). `git patch-id --stable` over `git diff main..wp4.6`: **`07cd8dcb05af`** on the author branch at `4cd7e992` (vs `b6a31b5`), on `d674836f` and on `e3b53d68`.

**Footprint** (`git diff --name-only main..e3b53d68`, 17 paths): `src/clearwater/app/` (`__init__.py`, `activity.py` grant (b), `composition.py` grant (c), `export_worker.py` NEW, `main.py` Q6); `src/clearwater/io/video/pipes.py`; `src/clearwater/jobs/export_process.py` NEW; tests `tests/export_worker_hold.py` NEW, `test_app_deps.py`, `test_app_export_worker.py` NEW, `test_app_startup.py`, `test_app_v7.py`, `test_app_wiring.py` (R0-STOP-1 (ii)), `test_io_video_spawn.py` (the AST pin 7 -> 8), `test_jobs_export_process.py` NEW; the report and the ledger; this record. No `src/clearwater/interfaces/`, `jobs/export.py`, `gui/`, `cache/`, `config/` or `tools/` change; no `pyproject.toml` or `uv.lock` change; no dependency. Every changed blob has 0 CR bytes (17 of 17 checked at `e3b53d68`).

## V7 of record (window 08:46-09:08Z, EXCLUSIVE, head `1563da2a`; CHARC `d42c9126`)

| Scenario | WP4.6 (process form) | WP4.3 (in-process) | Verdict |
|---|---|---|---|
| (c) File > Export | **39.0 / 11.0 ms** (longest / p99); export 226.2 s | 180.0 / 12.0 ms; export 209.1-210.9 s | **PASS** (DR-98's STOP closed) |
| (e) 1:1 4K render during (c) | **48.0 / 12.0 ms** | 182.0 / 12.0 ms | **PASS** |
| (d) 300-still batch (control) | 67.0 / 53.0 ms | 56.0 / 43.0 ms | PASS |
| DR-44 (c), export close | ended True in 509 ms, no temporaries | (in-process form) | PASS |

Export wall +7.3 % to +8.2 % against WP4.3's window (N6's STOP line is 10 %; the instrumented not-of-record run read +10.5 % to +11.5 %: the margin is thin and load-sensitive, the report's Limit 3 with its remedy candidate). (a), (b) and (f) not re-run (WP4.6 changes only the export path). The window ran on `1563da2a`; the later changes (B remediation, bound, clamp) touch malformed-line handling and set-up ordering only, not the export path's timing (CHARC `bc6847dd`: "nothing changes in the window figures").

## Nets

| Net | Result |
|---|---|
| Reviewer A, R1-R3 (cells 3-4; WSL codex-cli 0.162.1, `gpt-6.1-sol` / high) | R1: 8 major/critical-class reported, 5 confirmed blocking, 2 banked pre-existing (F4, F8), 1 reclassified minor; R2: 1 confirmed blocking (R2-2, closed by CHARC's design change (d)); R3 (the LAST full round under the cap): R3-1 confirmed, R3-2 reopened minor, R3-3/R3-5 out of envelope, R3-4 test-only; **the terminating clean-up** by cell 5 (R3-1 RED-first, verified at my seat), converged under `acc0255d`. |
| **Reviewer B** (my Codex pass at this seat, on `c0eedb0e`, base `b6a31b5`; neutral prompt; ledger and report WITHHELD; `clearwater-review-evidence\wp4.6\reviewB\`, `md5sums.txt`; `review-B.txt` md5 `ab9c2487f4ceee92d4772685a5303c2c`) | **NEW_CRITICAL_MAJOR_FOUND, 0 / 1 / 2**; banner `gpt-6.1-sol` / high; `^ERROR` 0; 26 `succeeded in` executions; 129,837 tokens. B-1 MAJOR (an overflowing progress integer forwarded), B-2 MINOR (set-up before the clean-up `try`), B-3 MINOR out of envelope (nested `OverflowError` in the settings decode). ONE remediation by cell 5 (RED `d5846415`; fixes `fc403cf3`, `1ab92604`, `aaf1f1fa`), CHARC's bound (RED `bf76ab00`, fix `1e3f5836`) and clamp (cell 6: RED `ed62be55`, fix `a1df2023`, docs `4cd7e992`). |
| **Reviewer B re-run** (narrow, on `c0eedb0e..4cd7e992`, ledger and report withheld; the three findings and the final progress rule as claims; `clearwater-review-evidence\wp4.6\reviewB2\`, `md5sums.txt`; `review-B2.txt` md5 `ff0faeee965856e15fc479eb0bd2f2c6`) | **NO_NEW_CRITICAL_MAJOR, 0 / 0 / 1 / 1**; probe READY; banner `gpt-6.1-sol` / high; `^ERROR` 0 in both streams; 15 executions; 65,807 tokens. Claims 2-6 HOLD (EXECUTED); claim 1 fails on the logging budget only: **B2-1 MINOR** (a non-finite or over-parse-limit count fails in `json.loads`, is queued as a generic invalid line and warned per line, not once per job; unreachable from the shipped worker, `export_worker.py:168` `allow_nan=False`) and **B2-2 ADVISORY** (the `_read_lines` docstring): both **BANKED** by CHARC `0650fd0d` (DR-103, CHARC's row). No third code change. |

**Verification QA at my seat:** R3-1's RED and fix (cell 5); the four-file targeted run at `52be44aa` (372 passed in 52.56 s) and at `4cd7e992` (376 passed in 55.57 s); ruff, format, mypy clean at both; 0 CR. The clamp diff read against CHARC's rule (bound before clamp; one WARNING per job at the first clamped line from the per-job stdout reader thread; the ignored-line budget separate).

## Gate

The ONE two-leg gate on `d674836f` (base main `edec3c17`), run id `g29-wp46`, Git Bash, `PYTEST_ADDOPTS` unset, `QT_QPA_PLATFORM=offscreen`, `clearwater.local.toml` copied (identical to the main tree's), at least 5 GiB available before each leg (14.7 GiB before the serial leg).
- **Static:** `ruff check` all passed; `ruff format --check` 292 files already formatted; `mypy` no issues in 148 source files (on `4cd7e992` and again on `e3b53d68`); 0 CR in every changed blob.
- **Collection:** all **7,376** = parallel 6,128 + serial 1,241 + fullclip 7; each exit 0 and each list's length equal to pytest's own count; no duplicates, pairwise disjoint, union = all. Against main `edec3c17`'s 7,269: **0 removed, +107** (the package's new nodes).
- **PARALLEL:** **6,127 passed, 1 skipped**, EXIT 0, 490.34 s (started 10:02Z). The skip is the standing swscale refusal (`tests/test_color_roundtrip.py:123`), as at WP4.3's gate. Log md5 `74fba13476629548076d33465d4809ef`.
- **SERIAL:** **1,230 passed, 11 skipped, 0 failed**, EXIT 0, 1,516.30 s (10:10:15Z-10:35:35Z). The 11 skips are the standing look-check frames archived to D: (`test_app_v8_v18.py:134` 1, `test_methods_assembly_v8.py:44` 5 + 4, `test_wp41_v8.py:193` 1), the same 11 as WP4.3's gate. The DR-99 node passed. Log md5 `3348b3b353a7792205277aa1b371f81a`; junit `work/pytest-gate-g29-wp46-serial.xml` in the worktree.
- **FULLCLIP:** not run (a per-package gate; the brief asks none).
- **Harness gate:** not required (no `scripts/`, `.claude/`, kernel doc or `tests/harness/` change).
- During the parallel leg two Codex turns (WP5.3 turn 5, WP-D54 turn 3) and one 81 s GUI run request (WP5.1 T8) ran on the host; the serial leg overlapped only WP5.3 turn 5's light tests. No timing figure of record is taken from this gate.

**WITNESS:** the V7 window above (the owner-free reality check of the claimed behaviour: GX011627 exported through the process form with the shell responsive, outputs inspected in `.worktrees/wp4.6/work/wp4.6-window/`); the export of record is one 86.0 MB output.

## Dispositions (follow-ons, gaps, deferred items)

- **BANKED, CHARC's rows at this accept:** F4 (engine failure texts can carry a path; `jobs/export.py` `_describe`, WP3.14) and F8 (the D87 re-check charges the scratch cache to the output folder's volume; `jobs/export.py:916`, WP3.21); DR-103 (B2-1 with B2-2).
- **Report Limits carried to CHARC:** the cold analysis in the worker (wall +7.3..8.2 %, remedy candidate: seed the scratch from the GUI cache's complete entry under the clip lock, touches `cache/`, NOT built); the one-hour stale sweep (a killed worker's scratch folder occupies disk outside the GUI cache's accounting until a later instance's first video job; 61.6 MiB for GX011627); Limit 12 (the clamp hides an over-count from the bar; one WARNING names the counts; nb_frames under-declaration NOT observed on GX011627, not checked).
- **GUI cache accounting (CHARC's ask):** MATERIAL ONLY AS A LIMIT. The worker's per-job scratch (`cache_dir/export/<uuid4 hex>`, 61.6 MiB for GX011627) is outside the GUI cache's size accounting for one job's length, removed after the result; a crash leaves it until the one-hour sweep (report sections "The scratch folder" and Limits 3-4). Ruling (e) already names it.
- **`_HeldSink` (`tests/test_app_v7.py:246`) and `_ProgressSink` (`tests/test_app_wiring.py:627`) (CHARC's ask):** both are NO LONGER USED by any committed test after R0-STOP-1's edits; `_ProgressSink` is still used by the uncommitted pinned window driver's `dr44c-export` mode (`clearwater-review-evidence\wp4.6\windows\s7_driver_wp46.py`). Removing them was outside the cell's exact grant (ledger, the Y2 notes). Disposition: CHARC's (a register row or a removal in the next package that owns those test files).
- **Persistent warm worker (Q1 (b))** and **the scratch seeding**: BANKED as follow-on candidates (report Limits 2-3), not commissioned.

## Merge

`main` fast-forwarded to `e3b53d68` plus this record's commit, by the orchestrator (the only role that merges). The worktree `.worktrees/wp4.6` is kept until CHARC's accept-side commit lands.
