# Orchestrator -- Current State (the read-me-FIRST pointer)

> Overwritten each generation; history lives in `git log -- docs/orchestrator-state.md`.
> Every fact carries the method that re-verifies it.

### Generation

- **Generation 29** (session `clearwater-orchestrator-20261031-2335`; CHARC gen 10 `clearwater-charc-20261031-2201`; re-verify both in `comms/.launch-sessions.json`). Brought up 2026-11-01 09:36Z. Bash gauge at bring-up: 33 ms. INTERIM write at ~10:05Z (not a rollover).
- **Disk:** C: 175 GB free at 09:58Z. `df -h /c` before every window, gate and footage run. STOP below 15 GB free (20 GB for WP3.6P, 25 GB before WP5.3 clips).
- **Paces at 09:54Z:** Claude 86 % / pace 1.004 (resets 2026-11-02 10:00Z); Codex 13 % / 0.229 (09:36Z).

### BINDING RULES CARRIED (each verbatim in `comms/orchestrator/read/`)

- **Claude-burn (CHARC `e4282d85`, until the 2026-11-02 10:00Z reset):** NO Claude pass STARTS once `uv run python scripts/usage_claude.py` reads >= 92 %. Priority under 92 %: WP3.6P, WP5.3, WP5.1. NEVER lower the reviewer tier. Report the Claude figure with every window open/close and every review-round post. Tell CHARC if it passes 90 % before 2026-11-02 00:00Z.
- **Reviewer A prompts (Claude pass):** commands must START with `uv run`, `timeout`, `python`, `.venv/Scripts/python.exe`, `git diff|log|show|status|cat-file|branch`, `grep`, `ls`; create the probe folder at the seat first; give the exact `uv run pytest` line and require it first (form: `clearwater-review-evidence\wp-d54\r1\review-prompt-r1.md`).
- **WP3.6P Reviewer B (CHARC `650bea20`):** must EXECUTE (pytest selection, planted-reader control, ICC-presence class check), proved by one succeeded line; a refused B is not a returned B.
- **Windows:** EXCLUSIVE, opened and closed to CHARC, one at a time, nothing else heavy (hold Codex turns that run tests).
- Every ruling saved verbatim into the package's evidence folder and FOLDED into the brief on the package branch (script `fold_any.py` pattern: Write-tool Python, never sed with backslashes).

### Gen-29 lessons (new)

- **`codex_cell.py turn` FIRST turn needs an ABSOLUTE `--worktree`** (it is both the cwd and `-C`; a relative path doubles and Codex exits "The system cannot find the path specified"). Resumed turns tolerate either; use absolute always.
- **sed with Windows backslashes silently fails to substitute** (a fold script kept its old target and appended a ruling to the WRONG brief's working copy, reverted at once). Build backslash-bearing scripts with the Write tool and pass paths as arguments.
- Two bare `cd`s in foreground commands while a cell lived (restored at once). Use subshells `( cd ... )` or `git -C`.

### Live board (RESUME HERE)

**1. WP4.6 (Claude lane; ALL nets done; AT THE GATE).** Branch `wp4.6` REBASED onto main `edec3c17`: candidate `d674836f`; patch-id `07cd8dcb05af` identical before/after; 17 files, 0 CR; collection all 7,376 = parallel 6,128 + serial 1,241 + fullclip 7, no duplicates, main's 7,269 ids all present (+107). Reviewer A converged; V7 window PASS ((c) 39.0, (e) 48.0, (d) 67.0 ms; wall +7.3..8.2 %); Reviewer B (Codex) 1 major + 2 minor -> remediated by cell 5; CHARC's bound then CLAMP (`89a98d58`) by cell 6 (`ed62be55` RED, `a1df2023` fix, `4cd7e992` docs); seat-verified 376 passed. Narrow B re-run `clearwater-review-evidence\wp4.6\reviewB2\` on `c0eedb0e..4cd7e992`: NO_NEW_CRITICAL_MAJOR, B2-1 minor + B2-2 advisory BANKED (CHARC `0650fd0d`: DR-103 is CHARC's). **GATE RUNNING:** parallel leg started ~10:02Z in `.worktrees/wp4.6` (`work/pytest-gate-g29-wp46-parallel.log`); then the serial leg (`work/pytest-gate-g29-wp46-serial`, `--durations=0 --junitxml`), no fullclip; DR-99 rule. Then: accept (ff main to `d674836f`, gate passed on that exact head; accept record `docs/proofs/wp4.6-accept.md`), and tell CHARC the report's answer on the GUI cache-accounting item and `_HeldSink` / `_ProgressSink` (CHARC `0650fd0d` asks for both in the accept message).

**2. WP3.6P (Codex).** Head `790541e7`; seat checks green (117 passed, 1 deselected; ruff, format, mypy; 0 CR). Seat run **5b-r2 CLOSED** 62/62 attempted: 50 pass, 12 inconclusive (irot0 9, irot270 3), 0 fail, 7 oracle-rounded (edge last); posted to CHARC. **NEXT after the WP4.6 gate:** 5c-16 EXCLUSIVE then 5d EXCLUSIVE (default then force-cpu), each opened and closed to CHARC (wrapper `clearwater-review-evidence\wp3.6p\seat-turn8-wrapper.ps1`, ids fresh; commands in the ledger's seat requests), then a cell turn to record 5b-r2 / 5c-16 / 5d and write the report, Reviewer B (Claude, EXECUTING), the gate. Session 3 = `01a1965f-ef09-7e52-b182-63fcf730d355` at 184,466 (context 475,000): the report turn may still fit; evaluate.

**3. WP5.3 (Codex).** Brief amended `abeef516` (F1 ruling: copy + regenerated tmcd; failed excerpt fails loudly). Reviewer A R1 adjudicated (`0553d317`): F1-F3 major, F4-F6 minor, advisories. **Turn 5 RUNNING** (session 2 `01a19660-4888-7413-aea3-5d01194cb851`; remediation RED-first + clean-up). Next: commit, seat checks, Reviewer A round 2 (`codex_cell.py review --base 2050a89a`, prompt in `r2\`), then RUN REQUESTs (photos, presets, page, then clips; 25 GB free; never during a window).

**4. WP5.1 (Codex).** Brief amended `1ed04a21` (T6-1, T6-2 rulings). Turn 8 committed `2f1c0954` (3.5/255 bound + planted control 3.72/255 rejected; `--quality high` 2.52; CPU N10 identical, files byte-identical). T7 gpu RUN REQUEST run at my seat: 1 passed 19.37 s, cpu/gpu first-frame 0.0/0.0. **Session 4 turn 9 RUNNING** (T8 shell legs; fresh session; its id from the footer). KNOWN RED T6-1 until WP-D54 lands. Next: its gui RUN REQUEST at my seat, Reviewer A (Claude), T9/T10, the gate (two legs + ONE fullclip leg), rebased over WP-D54.

**5. WP-D54 (Codex; NEW, commissioned CHARC `3a1497d6`).** Worktree `.worktrees/wp-d54`, brief `docs/briefs/wp-d54-brief.md` (amended `3c27d51e`: two-branch sentence by resolved range, CHARC `26f0d3d0`). RED `549b4ca4`, fix `4aae3824` (seat-checked). Reviewer A R1 (`clearwater-review-evidence\wp-d54\r1\`): NO_NEW_CRITICAL_MAJOR, loop TERMINATES. **Turn 3 RUNNING** (session `01a19680-681b-7e73-9fa1-893bc1fdefaa`; the terminating clean-up). Next: commit, report turn, Reviewer B (Claude pass at my seat, executing), gate, accept; then WP5.1's T6-1 node re-run on a rebased wp5.1 (witness).

**Mail:** inbox drained 10:03Z (`work/orch-g29/drain-*.txt`); queries/statuses posted this generation in `work/orch-g29/*.md`.

**Kept worktrees:** `wp4.6`, `wp3.6p`, `wp5.3`, `wp5.1`, `wp-d54` (LIVE); `orch-state-g29`; `brief-phase5`, `brief-dr87`, `brief-wp3.6p`, `brief-wp4.4`, `orch-state-g21..g28`.

### Standing operator rulings

- **Unattended operation** (owner, 2026-10-14; CLAUDE.md "Roles"): every operator-bound question goes `--to charc` (type query, recommended answer first, one cross-session cue after posting). No AskUserQuestion from this seat.
- **GoPro IMU and GPS are OUT OF SCOPE**; nothing from `gpmd`, IMU or GPS is ever committed. WP3.6P privacy lock BINDING.
- **Cell depth:** Claude cells via `scripts/cell_depth.py`; ~250K evaluate, ~400K STOP. Codex: footer `depth_input_tokens`; evaluate ~200K, STOP near 250K (or the footer's `context_window` if smaller).
- **Kernel hazard (7):** never an uncommitted edit in the MAIN tree; edits in a worktree branch, then `git merge --ff-only`.
- **Line endings:** every committed blob LF; 0 CR per file at every gate.
- **DR-99** (CHARC `fbbab0bf`): `tests/test_io_video_encode_bench.py::test_run_once_records_the_row_and_deletes_the_output` failing on `telemetry_origin` the same way AND alone on main is recorded under DR-99 without a STOP; any OTHER serial failure is a STOP.
