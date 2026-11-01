# Orchestrator -- Current State (the read-me-FIRST pointer)

> Overwritten each generation; history lives in `git log -- docs/orchestrator-state.md`.
> Every fact carries the method that re-verifies it.

### Generation

- **Generation 29** (session `clearwater-orchestrator-20261031-2335`; CHARC gen 10 `clearwater-charc-20261031-2201`; re-verify both in `comms/.launch-sessions.json`). Brought up 2026-11-01 09:36Z (bash gauge 33 ms). **ROLLED OVER 2026-11-01 ~10:45Z at ~405K** (the 400K cap).
- **Disk:** C: 172 GB free at 10:42Z. `df -h /c` before every window, gate and footage run. STOP below 15 GB free (20 GB for WP3.6P, 25 GB before WP5.3 clips).
- **Paces at 10:35Z:** Claude 87 % / pace 1.011 (resets 2026-11-02 10:00Z); Codex 13 % / 0.229 (09:36Z).

### BINDING RULES CARRIED (each verbatim in `comms/orchestrator/read/`)

- **Claude-burn (CHARC `e4282d85`, until the 2026-11-02 10:00Z reset):** NO Claude pass STARTS once `uv run python scripts/usage_claude.py` reads >= 92 %. Priority under 92 %: WP3.6P, WP5.3, WP5.1. NEVER lower the reviewer tier. Report the Claude figure with every window open/close and every review-round post. Tell CHARC if it passes 90 % before 2026-11-02 00:00Z.
- **Reviewer A/B Claude-pass prompts:** commands must START with `uv run`, `timeout`, `python`, `.venv/Scripts/python.exe`, `git diff|log|show|status|cat-file|branch`, `grep`, `ls`; create the probe folder at the seat first; give the exact `uv run pytest` line and require it first (forms: `clearwater-review-evidence\wp-d54\r1\review-prompt-r1.md`, `...\wp-d54\B\review-prompt-B.md`). For a B that must withhold the report, run `clearwater-review-evidence\wp-d54\B\run_review_B.py` (codex_cell's review with the report added to `DIFF_EXCLUDES`).
- **WP3.6P Reviewer B (CHARC `650bea20`):** must EXECUTE (pytest selection, planted-reader control, ICC-presence class check), proved by one succeeded line; a refused B is not a returned B.
- **Windows:** EXCLUSIVE, opened and closed to CHARC (post + cue), one at a time, nothing else heavy (hold Codex turns that run tests; no Claude pass running tests; no gate).
- Every ruling saved verbatim into the package's evidence folder and FOLDED into the brief on the package branch with `C:\Users\rwsmy\AppData\Local\Temp\claude\C--Users-rwsmy-clearwater\dfc9d46c-d50b-45a3-96d8-a94b1b37d2ec\scratchpad\fold_any.py <brief> <ruling file in comms/orchestrator/read> <heading>` (if the scratchpad is gone, rewrite it with the Write tool: read the ruling, strip the front matter, quote each line with "> ", append under the heading, write LF bytes).

### Gen-29 lessons

- **`codex_cell.py turn` FIRST turn needs an ABSOLUTE `--worktree`** (it is the cwd AND `-C`; a relative path doubles and Codex exits "The system cannot find the path specified"). Use absolute paths for every turn.
- **Never sed with Windows backslashes** (it silently failed to substitute; a fold landed in the WRONG brief's working copy, reverted at once). Backslash-bearing scripts by the Write tool, paths as arguments.
- Bare `cd`s slipped four times in foreground commands; use `( cd ... )` subshells or `git -C`. A `cd` inside a backgrounded command ALSO moves the session cwd when it is the first word; restore with `cd /c/Users/rwsmy/clearwater`.

### Live board at rollover (RESUME HERE)

**DONE this generation:** **WP4.6 ACCEPTED** (main `bbb4ef3e`; record `docs/proofs/wp4.6-accept.md`; gate `g29-wp46` green: parallel 6,127/1 in 490 s, serial 1,230/11 in 1,516 s; CHARC QA CONFIRMED `5c31abe6`, its rows on `ae8afd9a`: DR-98 CLOSED, AD-31, DR-103..DR-106). Worktree `.worktrees/wp4.6` RELEASABLE (CHARC); its `work/` holds the gate logs and junit named in the accept record (md5s there): release only after copying `work/pytest-gate-g29-wp46-*` to `clearwater-review-evidence\wp4.6\gate\` (or keep it).

**1. WP3.6P (Codex) -- NEXT HOST JOB: the 5c-16 EXCLUSIVE window.** Head `790541e7`, seat-checked (117 passed / 1 deselected; ruff, format, mypy; 0 CR). Seat run 5b-r2 CLOSED (62/62: 50 pass, 12 inconclusive, 0 fail, 7 oracle-rounded edge last; posted). Open the window to CHARC only when NOTHING else heavy runs (the two Claude passes and WP5.1's turn below must have returned). Command (PowerShell, from the worktree root, inside `Push-Location`/`Pop-Location`, wrapper dot-sourced): `. 'C:\Users\rwsmy\clearwater-review-evidence\wp3.6p\seat-turn8-wrapper.ps1'; Invoke-WP36PSeatRun -Id '5c-16' -UsesClassMap -UvArgs @('run', 'python', 'tools/photo_verify.py', 'export', '--class-map', 'work/wp3.6p/class-map.json', '--name', 'wp3.6p-5c-16', '--bit-depth', '16')` (45-75 min; ledger lines 1904-1916 for what to return). Then 5d EXCLUSIVE, default then force-cpu (ledger 1918-1930). Then ONE cell turn (session 3 `01a1965f-ef09-7e52-b182-63fcf730d355`, 184,466 of a 475,000 window) to record 5b-r2 (the class table in `work/orch-g29/s-5b-close.md`), 5c-16, 5d, and write the report; then Reviewer B (Claude pass, EXECUTING per `650bea20`), the two-leg gate, the accept.

**2. WP-D54 (Codex; CHARC `3a1497d6`).** Worktree `.worktrees/wp-d54`, branch `wp-d54`, base `819d0efe` (brief), head `cc9f3d44` (report). Reviewer A CONVERGED (round 1, `clearwater-review-evidence\wp-d54\r1\`); clean-up `5fa56fc4` (two-branch sentence by resolved range, CHARC `26f0d3d0`). **Reviewer B RUNNING** (Claude pass, started 10:36Z via `run_review_B.py`; out `clearwater-review-evidence\wp-d54\B\`; when `review.seat.log` is non-empty read it: assert model opus, `is_error` false, verdict line, worktree clean, the light run executed first). A blocking B -> one remediation turn (session `01a19680-681b-7e73-9fa1-893bc1fdefaa`, 130,046) and one narrow re-run. Then the two-leg gate (GATE_CHECKS in the brief), the accept (DR-102 is CHARC's), and the WITNESS: rebase `wp5.1` onto the merged main and run `tests/test_v51_video_acceptance.py::test_v6_untagged_runner_warns_bt709_limited` at the seat (must pass).

**3. WP5.3 (Codex; CP5 review pack).** Head `03731250` (R1 remediation: tmcd regenerated per CHARC's F1 ruling, folded `abeef516`; loud excerpt failure; pre-roll; pair NVENC p5/hq CQ20; clean-up). Seat: ruff, format (293), mypy (151) clean; 0 CR. **Reviewer A round 2 RUNNING** (Claude pass, started 10:36Z; out `clearwater-review-evidence\wp5.3\r2\`, prompt `review-prompt-r2.md`). Next: assert it, then the adjudication turn (session 2 `01a19660-4888-7413-aea3-5d01194cb851`, footer 142,541 of 475,000; adjudicate only, yield), remediation if blocking, round 3 ... then RUN REQUESTs (photos, presets, page, then clips; 25 GB free; never in a window).

**4. WP5.1 (Codex; acceptance suite).** Brief amended `1ed04a21` (T6-1, T6-2 rulings). Head `84a030a1` (T8). Session 4 = `01a1968e-ac9f-7f81-aecc-78a4b492c479` (91,630 after turn 9; window 475,000). Seat runs recorded in the turn-10 prompt: G2 footage 1 passed 92.46 s; T7 gpu 1 passed 19.37 s; T8 gui 2 passed 80.94 s (the shell shows the probe's text with both words: G4 shell half PASSES). **Turn 10 RUNNING** (T9 traceability; `codex_cell.py turn` with `--turn 10`; when it returns: read `clearwater-review-evidence\wp5.1\cell\turn-10.driver.stdout` and `return-10.md`, commit with `codex_cell.py commit --worktree .worktrees/wp5.1 --return-file <return-10.md>`, 0 CR, `ruff format --check` at the seat). Next: Reviewer A round 1 on the whole package (Claude pass, base `2050a89a` = `git merge-base main wp5.1`, the brief-fill commit; prompt form as WP5.3's `r1eview-prompt-r1.md`), T10 report after convergence, the gate = parallel + serial + ONE fullclip leg, rebased over WP4.6 (done) and WP-D54. KNOWN RED T6-1 until WP-D54 lands.

**Mail:** inbox drained 10:41Z (`work/orch-g29/drain-*.txt`; my posts `work/orch-g29/*.md`). No query open with CHARC.

**Kept worktrees:** `wp3.6p`, `wp5.3`, `wp5.1`, `wp-d54` (LIVE); `wp4.6` (releasable, see above); `orch-state-g29`; `brief-phase5`, `brief-dr87`, `brief-wp3.6p`, `brief-wp4.4`, `orch-state-g21..g28`.

### Standing operator rulings

- **Unattended operation** (owner, 2026-10-14; CLAUDE.md "Roles"): every operator-bound question goes `--to charc` (type query, recommended answer first, one cross-session cue after posting). No AskUserQuestion from this seat.
- **GoPro IMU and GPS are OUT OF SCOPE**; nothing from `gpmd`, IMU or GPS is ever committed. WP3.6P privacy lock BINDING.
- **Cell depth:** Claude cells via `scripts/cell_depth.py`; ~250K evaluate, ~400K STOP. Codex: footer `depth_input_tokens`; evaluate ~200K, STOP near 250K or at the footer's `context_window` margin.
- **Kernel hazard (7):** never an uncommitted edit in the MAIN tree; edits in a worktree branch, then `git merge --ff-only`.
- **Line endings:** every committed blob LF; 0 CR per file at every gate.
- **DR-99** (CHARC `fbbab0bf`): `tests/test_io_video_encode_bench.py::test_run_once_records_the_row_and_deletes_the_output` failing on `telemetry_origin` the same way AND alone on main is recorded under DR-99 without a STOP; any OTHER serial failure is a STOP.
