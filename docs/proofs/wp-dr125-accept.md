# WP-DR125 accept record (orchestrator generation 45, 2026-11-04)

**Package:** WP-DR125, the export worker's standard input. The worker now isolates its own standard input in source and frozen runs alike.

- It reads the request pipe through a private, non-inheritable raw descriptor, with no `io` buffer.
- fd 0, and on Windows the Win32 `STD_INPUT_HANDLE`, point at the null device before anything that can spawn a child.
- It exits 0 after its result line on every run.
- The WP6.1 F-E shim in `__main__` (`isolate_worker_stdin`, `STDIN_REFUSAL`) is REMOVED. The frozen `--export-worker` branch is the loader, then the worker.

**The record:**
- **Brief:** `docs/briefs/wp-dr125-brief.md`, FINAL by CHARC (gen 15). Then the Round-0 rulings (R1-R3, (a)-(c)), the Turn-4 rulings, the Reviewer A r1 ruling, the A r2 grant (`_NO_GUI_PRELUDE`), and the B r1b note (M-1 revises a6), all by CHARC gen 16.
- **Lane: Codex `implementer-codex-sol-high`.** Codex is the lower weekly pace at commission.
  - Session `01a1a797-5f82-72f3-a27d-c30eab9dd816`: round 0 and the build, turns 1-3. Retired by the depth rule at 198,080 / 475,000, read at the turn-3 end.
  - Session `01a1a7b0-df46-7361-9f2e-1927e997b468`: turns 4-9. Its depth, read at each turn end, was 87,046 (t4), 115,137 (t5), 163,391 (t6), 178,877 (t7), 213,220 (t8) and 230,686 (t9), all of 475,000. Turns 7-9 were gen 45's.
- **Reviewers were the other model (Claude) in both nets,** each a read-only `claude -p` process at the seat (`codex_cell.py review`) on the detached copy `.worktrees/wp-dr125-rA`:
  - Reviewer A: r1 on `6ef67a19` was NEW_CRITICAL_MAJOR_FOUND (2 MAJOR and 3 MINOR, all in the tests), ruled by CHARC and folded in turn 6. r2 on `1ea45021` was NO_NEW_CRITICAL_MAJOR with 3 advisories, folded in turn 7. **Converged at r2.**
  - Reviewer B on `5da7aad7`:
    - r1 was NO_NEW_CRITICAL_MAJOR, with 1 MINOR. Its full list was lost to a driver defect: the reviewer backgrounded a command, and only its last message was kept.
    - r1b was the complete re-run, with a foreground-only rule: NO_NEW_CRITICAL_MAJOR, with 4 MINOR and 7 ADVISORY. These were folded in turns 7-8, except A-2 and A-7, which are banked.
  - The delta review of `5da7aad7..96c364f0` (turns 7-8) was NO_NEW_CRITICAL_MAJOR, with 1 MINOR (the behavioural source/frozen test did not see the Win32 slot under console Python) and 3 advisories. All were folded in turn 9, tests and docs only.
- **Report:** `docs/reports/wp-dr125-worker-stdin.md`.
- **Evidence:** `C:\Users\rwsmy\clearwater-review-evidence\wp-dr125\`:
  - `cell\`: dispatches 1-9, prompts, returns, turn transcripts, `t4-standin\`, `t5-records\`;
  - `A\r1`, `A\r2`;
  - `B\r1` (`review-final-message-only.txt`), `B\r1b`, `B\delta`;
  - `frozen\` (gen 44's check of `1ea45021`);
  - `frozen2\` (gen 45's re-check of `96c364f0`, the check of record);
  - `gate\`.

**Candidate:** branch `wp-dr125`, base `73453bdc`.
- The product code is FINAL at `96c364f0` (turn 8). Turn 9's `ee3877c1` changes tests and docs only; `git diff --stat 96c364f0..ee3877c1 -- src` is empty.
- The report's seat sections are `5da7aad7` and `ea97b8e3`.
- The merge of main is `15ee158d`; its second parent is `20afccd4`, CHARC's docs-only commit.
- The gate's head is `ee3877c1`. This record follows.

**Footprint** (`git diff --name-only main...wp-dr125`), every path owned by the brief or granted by a ruling:
- `src/clearwater/app/export_worker.py`: the isolation, the raw reader and the exit path;
- `src/clearwater/__main__.py`: the shim deleted;
- `src/clearwater/gpu_pack.py`: docstring only, ruling (a);
- `tests/test_app_export_worker.py`;
- `tests/test_frozen_entry.py`: R2's re-points and deletions, the A r2 grant, and two stale comments;
- `tools/package/README.md`: the stdin section rewritten;
- the report and this record.

## Nets

| Net | Head | Verdict | Disposition |
|---|---|---|---|
| A r1 | `6ef67a19` | NEW_CRITICAL_MAJOR_FOUND: M1 macOS fd count, M2 no positive `SetStdHandle` witness, m3-m5 | CHARC ruling (R2 widened); turn 6 |
| A r2 | `1ea45021` | NO_NEW_CRITICAL_MAJOR, 3 advisories | turn 7 (`_NO_GUI_PRELUDE` granted) |
| B r1 | `5da7aad7` | NO_NEW_CRITICAL_MAJOR, 1 MINOR (exit-path comment) | turn 7 |
| B r1b | `5da7aad7` | NO_NEW_CRITICAL_MAJOR, 4 MINOR + 7 ADVISORY | turn 8 (M-1 any-`Exception` fail-closed, M-2..M-4, A-1, A-3..A-6); A-2 and A-7 banked |
| Delta | `96c364f0` | NO_NEW_CRITICAL_MAJOR, 1 MINOR + 3 advisories | turn 9 (facts children under `pythonw.exe`, `sys.frozen` before import, stale comments, the README wording) |

Seat QA of every turn: the diff read against its dispatch; the owned files only; 0 CR in every changed blob; turn 7's product change comment-only; turn 9's `src` diff empty.

## The run series of record

- **Matched before/after records** (report, "Matched before/after records"; Codex sandbox, crash-report suppression):
  - at base `73453bdc`, the inherited child timed out at 10 s, and **20 of 20 worker exits were `0xC0000005`** after a successful result line;
  - on the candidate, the child printed `0` and exited 0, and **20 of 20 worker exits were 0** with empty stderr.
- **The frozen check of record** (seat, gen 45, 19:20-19:22Z, onedir rebuilt from `96c364f0`; report "Frozen check (seat)"):
  - handler check PASS: `__main__` 9/9, `gpu_pack` 53/53 and `export_worker` 26/26 equal to the source, and `isolate_worker_stdin` absent;
  - `--verify` PASS before and after;
  - **12 of 12 frozen `--export-worker` runs (6 heic + 6 video) exit 0, ok, on the GPU**, with CUDA files 59 from the pack, 8 from the driver and 0 other;
  - no window, no timeout kill, nothing left running;
  - the owner-log md5 unchanged, and the real `%LOCALAPPDATA%\Clearwater` absent.
- **Gen 44's earlier check of `1ea45021`** was the same: 12 of 12 GREEN.
- **Hard rule kept:** no seat or review run executed the DR-125 "before" shape. Every before-record ran in the sandbox only.

## Gate (`pdr125`, on `ee3877c1`, alone on the machine, the stall watch on every leg)

| Check | Result |
|---|---|
| `df -h /c` | 82 GB free at the start, 79 GB at the end |
| static | ruff exit 0; format exit 0 (323 files); mypy exit 0 (161 source files) |
| collection identity | 7,149 + 1,274 + 7 = 8,430 = all; 0 duplicates; 0 differences |
| parallel | exit 0, 642 s: 7,148 passed, 1 skipped (`test_color_roundtrip.py:123`, the by-design yuvj case) |
| serial (the brief's `slow` 20-run series and the serial worker tests) | exit 0, 2,259 s: 1,274 passed |
| harness | exit 0: Ran 423 tests, OK (skipped=1) |
| footprint | the owned paths only (above); 0 CR in every changed blob |
| the real `%LOCALAPPDATA%\Clearwater` | ABSENT after the gate |

The fullclip leg was not run: the brief names no fullclip check, and no correction, I/O or encode code changed.

Summary, verbatim:

```
head ee3877c1 start 19:33:59Z free 82G
leg static start 19:34:00Z free 82G
ruff exit 0
format exit 0 323 files already formatted
mypy exit 0 Success: no issues found in 161 source files
leg collect start 19:34:02Z free 82G
collect-all exit 0 ids 8430 uniq 8430: 8430 tests collected in 10.74s
collect-parallel exit 0 ids 7149 uniq 7149: 7149/8430 tests collected (1281 deselected) in 2.53s
collect-serial exit 0 ids 1274 uniq 1274: 1274/8430 tests collected (7156 deselected) in 2.33s
collect-fullclip exit 0 ids 7 uniq 7: 7/8430 tests collected (8423 deselected) in 2.32s
identity: union 8430 dup 0 diff-vs-all 0
leg parallel start 19:34:29Z free 82G
parallel exit 0 642 s: 7148 passed, 1 skipped, 5 warnings in 640.28s (0:10:40)
leg serial start 19:45:12Z free 80G
serial exit 0 2259 s: 1274 passed, 7156 deselected, 1 warning in 2254.85s (0:37:34)
leg harness start 20:22:50Z free 79G
harness exit 0 Ran 423 tests in 25.223s OK (skipped=1) 
end 20:23:19Z free 79G
```

Archive: `clearwater-review-evidence\wp-dr125\gate\`.

## Dispositions (for CHARC at this accept)

- **DR-125: CLOSE.**
  - Cause: the cancel watcher's daemon thread held a `BufferedReader` lock in `readline()` at interpreter finalisation (`_enter_buffered_busy`).
  - Fix: a raw `os.read` assembler over a private descriptor, so there is no buffer to finalise, together with the isolation.
  - Runs of record are as above.
- **AD-34:** amend. The shim is REMOVED; the one N1 Win32 call (`SetStdHandle`) is now in `app/export_worker.py`'s `_isolate_stdin`; the frozen worker branch is the loader, then the worker.
- **AD-31:** add a note on the worker's own isolation; it fails closed on any `Exception` with status 2.
- **Banked for the register:**
  - **B A-2:** the line assembler's remainder has no size cap. This is out of envelope (a hostile parent).
  - **B A-7:** the legacy `ProcessExportJobs` test path has no deadline of its own.
- **Ruled into WP6.3b** (CHARC `20afccd4`): `--disable-windowed-traceback` together with a product exception hook.
- **Owed prunes, on the owner's word:** the onedir build under `.worktrees/wp-dr125/work/wp6.1/` (668 MiB) and its working folders; `.worktrees/wp-dr125/work/wp-dr125/frozen-runs`.

## Merge

The harness gate was run with this record in the worktree (the package code unchanged since the gate head `ee3877c1`): `uv run python -m unittest discover -s tests/harness` -> Ran 423 tests, OK (skipped=1). No registration is needed (`docs/proofs/` is an instance-surface prefix). The record is committed on `wp-dr125` by pathspec, and `main` is fast-forwarded to `wp-dr125` by the orchestrator. Released after the merge: `.worktrees/wp-dr125-rA` (the detached review copy). `.worktrees/wp-dr125` is kept until the owner's word prunes its build. Main is ahead of `origin/main`; a push needs the owner's word.
