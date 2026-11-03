# WP5.8 accept record (orchestrator generation 37, 2026-11-03)

**Package:** WP5.8, the encoder-progress watchdog in `FFmpegVideoSink` (DR-115 (2): a GUI export no longer hangs forever when the encoder stops reading its input; W52-2 sat 35 minutes).
- **Brief:** `docs/briefs/wp5.8-brief.md` (FINAL by CHARC; round-0 rulings R1-R3 at main `6f2a023a`: write + flush inside the watched window, the watched `stdin.close()`, a flush witness, a test-only 36 MiB sentinel; the encoder's stdin stays the OS default pipe, not AD-23's).
- **Lane: CODEX**, `implementer-codex-sol-high`, two sessions, five turns (session 1 `01a1a027-6504-7872-aa79-0932f8584d08` turns 1-2, retired at 202,018; session 2 `01a1a049-871e-7ab2-a47e-aab7fd77055d` turns 3-5, at **166,833** after turn 5). Both nets Claude (`claude -p --model opus --effort high`), the other model.
- **Report:** `docs/reports/wp5.8-watchdog.md`. **Ledger:** `docs/proofs/wp5.8-ledger.md`. **Evidence:** `C:\Users\rwsmy\clearwater-review-evidence\wp5.8\` (`cell`, `A\r1`, `A\r2`, `B`, `gate`, and the W52-2 hang record `w52-2-cpu-hang.txt`).

**Candidate:** branch `wp5.8`, rebased onto main `2633b31d` and gated as **`d98f9ce6`**; then rebased onto main `5fa88694` (docs-only commits between) as `570fcf83`, `git patch-id --stable` over the 4 package commits equal before and after (`work/orch-g37/wp58-patchid-gate.txt`, `-rebased.txt`). This record's commit adds this file only (docs); the harness leg re-ran on it (below).

**Footprint** (`git diff --name-only main...wp5.8`, 4 paths plus this record): `src/clearwater/io/video/encode.py` (the watchdog: module constants `STALL_TIMEOUT_S` = 300 s and `SUSPEND_GAP_S` = 5 s, the daemon thread `video-encoder-watchdog`, `_send` = write + flush in one watched window, the watched close, a warning then `process.kill()` on a stall, the stall text through the existing `encoder_failed`); `tests/test_io_video_encode_units.py` (additions only; 11 watchdog tests, parallel leg); the report and the ledger. No change to the encoder command, the pipe, `FINISH_TIMEOUT_S` or the encoder choice; no frozen interface, no dependency. Every changed blob 0 CR.

## Nets

| Net | Result |
|---|---|
| Round 0 (turn 1) | a STOP on the watched window (write vs flush), the close, the pipe: CHARC ruled R1-R3 (`6f2a023a`). |
| Turn 2 (`5a957919`) | the watchdog and six tests, RED 4 fail / 2 pass then GREEN 132 + 115. |
| Reviewer A round 1 (Claude, on `5a957919`; `...\A\r1\`, 26 turns) | **NEW_CRITICAL_MAJOR_FOUND**: 1 MAJOR (`time.monotonic()` here is `GetTickCount64`, which counts sleep: a pending send across a > 300 s suspend killed a healthy encoder on wake) + minors; the rest held by execution (12 abort-race and 16 exit-race timings, one error each). Fixed in turn 3 (`cca85d8a`, fresh session 2): stall time accrues per poll capped at `SUSPEND_GAP_S`; render-gap and exit-race witnesses; message and start-failure texts; byte counters removed. Items 7, 8, 11 accepted as report limits. |
| Reviewer A round 2 (Claude, on `cca85d8a`; `...\A\r2\`, 28 turns) | **NO_NEW_CRITICAL_MAJOR = CONVERGED**; 2 MINOR (no witness for the first-observation cap; stale docstrings) fixed in turn 4 (docstrings only in `encode.py`, the cap witness RED with the cap removed, and the report); 4 ADVISORY to the report. |
| **Reviewer B** (Claude pass at the orchestrator's seat, EXECUTING, on `56b0deeb`; `...\B\`, 45 turns, `is_error` false, worktree clean after) | **NO_NEW_CRITICAL_MAJOR.** All seven claims held; every report figure it checked equals its source (137 tests and timings; the W52-2 counters; line references). Executed: the units file alone and under `-n 4` (green), a 40-iteration abort-vs-stall race (0 hang, 0 leak, one error each), mutations (6 of 8 caught). 2 MINOR + 4 ADVISORY, all dispositioned in turn 5 (the package's single B remediation, `9ebf7268`): (1) healthy-path tests failed 2 of 5 runs under a 16-core CPU burn -> child readiness before the watched sends, wider test margins; the cell's 5 loaded runs + 1 unloaded all green (max watchdog test 3.892 s loaded); (2) no log line when the watcher fires -> one warning before the kill, naming the encoder and the seconds (caplog test, RED with the line removed); (3) timestamp identity coarse at 15.625 ms -> report corrected; (4) two surviving harmless mutations -> stated in the report's test notes; (5) the W52-2 blocked write is an inference -> report says so; (6) the thread is named. The turn-5 product diff was read at the seat: thread name, docstrings, the warning (emitted under `_phase_lock`, as the existing exception log is); no production constant, command or pipe change. |

## Gate

The TWO-leg gate (GATE_CHECKS: the serial junit carries `tests/test_app_export_worker.py`; no fullclip-marked test added), WP-T7's flags (`work/orch-g37/gate.sh`), run id `p58`, Git Bash, `PYTEST_ADDOPTS` unset, `QT_QPA_PLATFORM=offscreen`; stall watch armed on each heavy leg; nothing heavy beside the serial leg. Summary `work/orch-g37/gate-p58/summary.txt` (copy in `...\gate\`).
- **Static** (on `3e96fd94`, the same package content, patch-id equal): `ruff check` exit 0; `ruff format --check` 311 files already formatted; `mypy` no issues in 156 source files.
- **Collection** (same head): all **7,888** = parallel 6,609 + serial 1,272 + fullclip 7; no duplicates; union identical to collect-all.
- **PARALLEL** (on `d98f9ce6`, `-n 4 --timeout 600`, 10:05:35Z): **6,608 passed, 1 skipped, 0 failed**, EXIT 0, 532 s. The skip is the standing swscale refusal. The 11 watchdog tests and `tests/test_jobs_export_process.py` (84 cases) green in the junit. Log md5 `5472b2106da2c4631cece4d570e8ff85`.
- **SERIAL** (on `d98f9ce6`, `--timeout 1200`, 10:14:48Z): **1,261 passed, 11 skipped, 0 failed**, EXIT 0, 2,076 s. The 11 skips are the standing look-check frames archived to D:. `tests/test_app_export_worker.py` 23 cases green. Log md5 `edaed1e684e3d4bb0937eb2acd9ced81`. C: 59 GB free at the end (10:49:24Z).
- **Harness gate:** 382 tests OK (1 skipped) on `3e96fd94`; re-run on this record's commit below.
- Junits copied to `...\wp5.8\gate\`.

## Dispositions (for CHARC at this accept)

- **AD-32** (the watchdog: awake-time stall accounting, 300 s, kill through the existing failure path) -- CHARC writes it.
- **DR-115 (2)** CLOSED by this package (an encoder that stops reading is detected and the export fails with `encoder_failed` instead of hanging); DR-115's remaining items as CHARC holds them. The W52-2 hang itself is not reproducible on demand; the fake encoder is the witness (report Limits).
- **AD-23 note:** the encoder's stdin is the OS default pipe, not AD-23's 32 MiB pipe (the brief's R1 / DR-115 text correction).
- Report Limits carried: stall text may replace an exit status during `_exit_status()`'s wait; a kill that does not end the process leaves the writer blocked (now with a warning in the log); the pre-existing closed-file `ValueError` race on abort; a starved watcher detects later by gap / 5 s; timestamp identity coarse at one 15.625 ms tick; POSIX untested.

## Merge

`main` fast-forwarded to the rebased package plus this record's commit, by the orchestrator. The worktree `.worktrees/wp5.8` is released after the merge (its `work/` pruned only on the owner's word).
