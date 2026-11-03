# WP5.8 — Encoder-progress watchdog (dispatch brief, DRAFT for the orchestrator's fill)

**Status:** DRAFT 2026-11-03 by CHARC (generation 13, session `clearwater-charc-20261102-0046`), on the owner's DR-115 scope ruling (2026-11-03 ~06:45Z, verbatim: "watchdog" = the watchdog is in v1; the encoder preference on the CPU-forced / fallback route is UNCHANGED). The orchestrator fills the dispatch section (base commit, lane paces, yields) and CHARC marks it FINAL. Spec v0.5.8; no spec clause changes. Owner decisions inside the package: none.

| Field | Content |
|---|---|
| ID and title | WP5.8 — Encoder-progress watchdog: a video export whose encoder stops consuming frames fails within a bounded time, with the D85 clean-up and a message naming the encoder (DR-115 paydown (2), owner-scoped) |
| Lane | **CODEX**: `implementer-codex-sol-high` (well-specified: one module touched, one constant, one watcher thread, a fake-encoder test; no frozen interface). Reviewer A = the Claude pass at the cell's seat, to convergence, five-round gate. Reviewer B = the Claude pass at the orchestrator's seat. Evidence `C:\Users\rwsmy\clearwater-review-evidence\wp5.8\`. |
| Tier and size | STANDARD. Size S (one module, one test file; no window). Codex evaluate at about 200K, STOP near 250K. |
| Base | main at dispatch (at or after `5cfe1bb4`). Worktree `.worktrees/wp5.8`, branch `wp5.8`. |
| Goal | When FFmpeg (the encoder process) is alive but has stopped reading the frame pipe, the export fails within about `STALL_TIMEOUT_S` seconds instead of sitting forever: the encoder is ended, the output deleted (the sink's failure path, D85 / D44), and the job's failure text names the encoder and the stall. Today the W52-2 shape (DR-115 (a)) blocks `stdin.write` on a full 32 MiB pipe with no timeout; left alone the GUI shows a stuck export. |
| Spec / decision clauses | D85 (temporary name, leftovers cleaned); D44 / V11 (no partial output); D81 (a failed batch item is logged, the batch continues); D26 (encoder selection unchanged); AD-23 (the 32 MiB pipe); AD-31 (the export runs in the worker process; the parent's conversation is untouched); DR-115 (the finding; the owner's scope). |
| Files owned | `src/clearwater/io/video/encode.py` (`FFmpegVideoSink` only: the watcher, `STALL_TIMEOUT_S`, the new `VideoEncodeError` kind text); `tests/test_io_video_encode_units.py` (new tests; existing tests unchanged); `docs/reports/wp5.8-watchdog.md` (the completion report). |
| NOT owned | `src/clearwater/interfaces/` (IF-5 FROZEN: `write` / `close` / `abort` signatures and the `VideoEncodeError` kinds already named there stay; a NEW kind is a CHARC ruling: see Q1); `jobs/export.py`, `jobs/export_process.py`, `app/export_worker.py`; `io/video/pipes.py`, `decode.py`; any GUI file; `tools/`. |
| Locks | No frozen interface. No dependency. No change to the encoder command line, the pipe size or the encoder choice (owner: unchanged). No write under the footage folder; tests write under `tmp_path`. The watcher must never end a HEALTHY slow encoder: the threshold is measured from the last byte the encoder ACCEPTED, not from the last frame the renderer produced. |
| Markers | All new tests parallel-leg (no marker): the fake encoder is a `sys.executable -c` script that reads N bytes then sleeps; each test under 5 s with a test-only short threshold (the constant is a module attribute the test monkeypatches). No `gpu`, `footage` or `slow` test. |
| Hardware flags | None. No EXCLUSIVE window: the stall cannot be provoked on demand (DR-115: intermittent, one in two). A real `--force-cpu` export is NOT part of the gate; the fake encoder is the witness. |
| Out of scope | A software-encoder preference on the CPU route (owner: unchanged; revisit only on a recurrence under the watchdog); encoder progress parsing (`-progress`), encoder restart or retry; a GUI change (the existing failure path already shows the job's failure text); the analysis or decode side; DR-114. |
| Debt and decided items | At the accept CHARC writes: DR-115 paydown (2) DONE, the row CLOSED if Q1 (a) stands with the trigger "any export whose progress stops while the encoder lives" now caught by the watchdog, else OPEN with the remaining part named; **NEW AD-32** "encoder-progress watchdog" (the design below as built); a note on AD-23 (the pipe's fullness is now observed). |
| Done | Plan 4.5. ruff check, ruff format --check, mypy strict clean; the new tests green in the parallel leg; every existing encode test green and unchanged; `tests/test_app_export_worker.py` and `tests/test_jobs_export_process.py` unchanged and green (serial leg at the gate); the completion report with the fake-encoder timeline; Reviewer A converged; Reviewer B clean or its single remediation done. |

## Why

WP5.2's W52-2 R2 (2026-11-02, `--force-cpu` export of the whole GX011627, `--encoder auto` = hevc_nvenc, about 9.9 s per frame): at about frame 670 the encoder's main thread sat at 100 % of one core with zero I/O for 35 minutes, the 32 MiB pipe full, the renderer blocked in `stdin.write`, the job never failing. The seat ended the encoder; the product then failed the job correctly by its own path (`encoder_failed`, the partial output removed). The same command re-run once (W52-3) completed in 109 min 45 s: intermittent. A real D111 CPU fallback at 4K feeds NVENC at exactly this rate, so a user on the fallback path can meet it, and the GUI would show an export that never ends. The owner scoped the fix: the watchdog in v1, the encoder choice unchanged.

## The design (CHARC's pass; the cell builds this unless round 0 disputes it with evidence)

1. **What is observed.** `FFmpegVideoSink._send` is the only writer to FFmpeg's stdin. A blocking `write` that returns means the kernel accepted the bytes (the pipe had room because the encoder read). So "progress" = the monotonic time at which the last `_send` RETURNED (`_last_accepted`), updated inside `_send` after the write. While a `_send` is in flight the sink is "waiting" (`_waiting_since` set before the write, cleared after). No `-progress` parsing, no file-size polling.
2. **The watcher.** A daemon thread started at `open` beside the stderr drain. Every `POLL_S` (0.2 s, the existing constant) it checks: process alive AND `_waiting_since` set AND `now - _waiting_since > STALL_TIMEOUT_S` → the stall. The default `STALL_TIMEOUT_S` = **300 s** (module constant; a healthy NVENC accepts a 4K frame in milliseconds and libx265 at 4K in well under 10 s; 300 s is 30 times the slowest healthy per-frame feed WP5.2 measured and 1,000 times the GPU route's). The watcher ends at `close` / `abort` / any failure.
3. **The action.** On the stall the watcher records `_stalled = (seconds, bytes_in_flight)` and calls `process.kill()` (the encoder has no state worth saving: the output is deleted on any failure). The kill makes the blocked `stdin.write` raise `BrokenPipeError` / `OSError` on Windows and POSIX alike, so the EXISTING failure path runs on the writer's thread: `_send` → `_encoder_failed` → `_fail` → output deleted. `_encoder_failed` consults `_stalled` first and, when set, builds the message: `"The video encoder (<encoder name>) stopped accepting frames for <N> s while <M> frames waited; the export was stopped."` with kind `"encoder_failed"` (Q1 (a)). The stderr tail is appended as today. Nothing else in the sink changes.
4. **The end of the stream.** `_end_stream` already bounds the wait after the sentinel with `FINISH_TIMEOUT_S` (1800 s); the watcher also covers the sentinel's own `_send`. No change to `FINISH_TIMEOUT_S`.
5. **Where it surfaces.** The worker process (AD-31) reports the job's failure text over the line protocol as it does for any `encoder_failed`; the parent and the GUI show it unchanged. A batch continues (D81). The D85 journal entry is cleaned by the job's existing path. No file outside `encode.py` changes.
6. **Threads and locks.** The watcher reads two timestamps and one process handle: set them under the existing `_phase_lock` or as single-assignment attributes (document which). `process.kill()` on an already-ended process is caught (`ProcessLookupError` / `OSError`). The watcher must not run after `_fail` has finished (join it with a short timeout in `_fail` / `abort`, as the stderr thread is joined).

## Tests (the cell writes these; Reviewer A checks they discriminate)

- **Stall caught.** Fake encoder: reads exactly K bytes from stdin then sleeps 60 s without reading. With `STALL_TIMEOUT_S` monkeypatched to 1.0 s and a pipe-filling frame size, `write` raises `VideoEncodeError("encoder_failed")` whose text contains the encoder name and "stopped accepting frames"; the output file is gone; the process is dead; elapsed under 5 s.
- **Healthy slow encoder not killed.** Fake encoder reads one frame every 0.3 s; threshold 1.0 s; six frames complete; no failure; the watcher's `_stalled` stays None.
- **Stall at the sentinel.** Fake encoder reads every frame, then stops reading before the sentinel; the sentinel's `_send` is caught by the watcher within the threshold (not by `FINISH_TIMEOUT_S`).
- **Normal exit race.** Encoder exits non-zero mid-stream: the existing `encoder_failed` text (exit status + stderr tail) is produced, not the stall text; the watcher does not double-report.
- **Abort while waiting.** `abort()` during a blocked write ends the process and returns; no exception escapes the watcher thread (its exceptions are logged, never raised).
- Every existing test in `tests/test_io_video_encode*.py` passes unchanged.

## Questions (CHARC's recommended answers; a round-0 dispute with evidence is a STOP to CHARC)

- **Q1 error kind.** Recommended (a): REUSE `"encoder_failed"` with the stall text (IF-5's kinds unchanged; every consumer already handles it). Alternative (b): a new kind `"encoder_stalled"` = a frozen-interface change, NOT in this lane; it would be a CHARC ruling and a Claude-lane package.
- **Q2 threshold.** Recommended: 300 s as a module constant, not a setting (no G-requirement asks for it; a setting would need the settings schema, out of scope). The report records the slowest healthy per-frame acceptance WP5.2 measured (about 9.9 s on the CPU route) against it.
- **Q3 kill versus terminate.** Recommended: `kill()`. The output is deleted on any failure, so a graceful `q` to FFmpeg buys nothing and a hung main thread may ignore it (W52-2's thread was spinning).

## Completion report (`docs/reports/wp5.8-watchdog.md`)

The design as built (any divergence from the section above, with the reason); the five tests and their timings; the fake-encoder timeline for the stall case (when the write blocked, when the watcher fired, when the writer's exception surfaced, when the output was deleted); the W52-2 evidence re-read against the new path (which line would have fired, after how long); limits (the stall cannot be provoked on real hardware on demand; the real witness waits for a recurrence, which now has a bounded end and a message).

## Yields and depth

Turn 1 = round 0 (the design read against `encode.py` as it stands, the test list, any Q1-Q3 dispute = STOP) and YIELD; turn 2 = RED tests then GREEN, ruff / mypy, committed, YIELD for Reviewer A; later turns = remediation rounds; the report; the nets. Codex evaluate at about 200K, STOP near 250K.

## Orchestrator dispatch fill (for CHARC to finalise)

- Lane paces at dispatch; base commit; worktree; evidence folder.
- Order: WP5.8 and WP5.7 may run in parallel on different lanes (WP5.7 is Claude-lane, opus-high); WP-DR25 (tools-only, Codex) queues behind WP5.8 on the Codex lane; WP5.5 (release prep) is LAST, after both product packages have merged, because it sets the version and the notices against the final tree.
- GATE_CHECKS: `docs/review-gate-clearwater.md` Part 2 on the final candidate rebased onto main: ruff, format, mypy; the two-leg gate with fresh basetemps under `work/`, collection identity; the serial leg's `tests/test_app_export_worker.py` and `tests/test_jobs_export_process.py` must be green (the real worker exercises the sink).
