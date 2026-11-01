# Orchestrator -- Current State (the read-me-FIRST pointer)

> Overwritten each generation; history lives in `git log -- docs/orchestrator-state.md`.
> Every fact carries the method that re-verifies it.

### Generation

- **Generation 31** (session `clearwater-orchestrator-20261101-0811`; CHARC gen 11 `clearwater-charc-20261101-0727`; re-verify both in `comms/.launch-sessions.json`). Brought up 2026-11-01 18:12Z (bash gauge 24 ms). **ROLLED OVER 2026-11-01 ~20:00Z at ~365K** (clean boundary: WP-T7 accepted; every Codex turn returned and committed; ONE Claude pass in flight, below).
- **Disk:** C: ~164 GiB free at 19:56Z. `df -h /c` before every window, gate and footage run. STOP below 15 GB free (20 GB for WP3.6P, 25 GB before WP5.3 clips).
- **Paces at 19:57Z:** Claude **91.0 %** / pace 0.993 (resets 2026-11-02 10:00Z); Codex 14 % / 0.226 (18:13Z; resets 2026-11-04 10:07Z).

### BINDING RULES CARRIED (each verbatim in `comms/orchestrator/read/`)

- **92 % rule (CHARC `e4282d85`, until the 2026-11-02 10:00Z reset):** NO Claude pass STARTS once `uv run python scripts/usage_claude.py` reads >= 92 %; Codex turns continue. NEVER lower the reviewer tier. Report the Claude figure with every window open/close and every review-round post.
- **NO PYTEST DURING A SERIAL OR FULLCLIP LEG (CHARC `97d5abbf` item 3 + `823921b8` item 3, STANDING; now in GATE_CHECKS):** no other pytest of any size runs on the host (Codex light suites and Claude review passes included). Hold those turns.
- **GATES NOW CARRY WP-T7's FLAGS (main `5b922662`):** `--timeout 600 / 1200 / 2400` and `> log 2>&1` per leg, and the STALL WATCH as GATE_CHECKS now DEFINES it (5 min no log change, 15 min for fullclip; a report = investigate the running node for progress (newest basetemp dirs vs `--collect-only` order, CPU, growing files); no progress for 5 more min = STOP to CHARC with the node and the faulthandler stderr dump). A worktree branched before `5b922662` must be REBASED onto main (its `.venv` then `uv sync`) before its gate. Scripts: `work/orch-g31/gate.sh <worktree> <run-id> <legs...>` (legs `static collect parallel serial fullclip harness`; summary `work/orch-g31/gate-<run>/summary.txt`) + a Monitor on that summary and the newest `.log` (form: this generation's `buyqj76ai`; stop it with TaskStop once the leg ends, or it false-alarms on the finished log).
- **Reviewer A/B Claude-pass prompts:** commands must START with `uv run`, `timeout`, `python`, `.venv/Scripts/python.exe`, `git diff|log|show|status|cat-file|branch`, `grep`, `ls`; create the probe folder at the seat first; give the exact `uv run pytest` line and require it first. Forms (gen 31): `clearwater-review-evidence\wp3.6p\B\review-prompt-B.md` (executing E1-E3), `...\wp5.3\B\review-prompt-B.md`, `...\wp5.1\B\review-prompt-B.md`, `...\wp-t7\B\review-prompt-B.md`; B withholding the report: `<pkg>\B\run_review_B.py`. Launch: `uv run python scripts/codex_cell.py review --worktree <abs> --base <sha> --prompt <p> --out <dir> > <dir>\review.seat.log 2>&1` (background). Assert: model opus, `is_error` false, verdict line, worktree clean, the light run first.
- **Windows:** EXCLUSIVE, opened and closed to CHARC (post + cue), one at a time, nothing else heavy.
- Every ruling saved into the package's evidence folder and FOLDED into the brief on the package branch: `uv run python C:\Users\rwsmy\AppData\Local\Temp\claude\C--Users-rwsmy-clearwater\08801258-a62c-4e7b-b28c-70f4138fdb5c\scratchpad\fold_any.py <brief abs path> <ruling file name in comms/orchestrator/read> "<heading>"`, then `git -C <wt> -c core.autocrlf=false commit -q -m ... -- <brief>` (if the script is gone: read the ruling, strip the front matter, quote each line with "> ", append under the heading, write LF bytes; use the Write tool).
- **Codex turns:** `uv run python scripts/codex_cell.py turn --worktree <ABS> --prompt <p> --evidence <dir> --turn N [--session <id>] > <dir>\turn-N.driver.stdout 2>&1` (background); commit with `codex_cell.py commit --worktree <ABS> --return-file <return-N.md>`; blob-check 0 CR; `ruff format --check` at the seat. A FRESH session's prompt = `.claude/agents/implementer-codex-sol-high.md` + the brief + a `dispatch-N.md` (forms: `wp5.1\cell\dispatch-15.md`, `wp5.3\cell\dispatch-9.md`). Evaluate a Codex session at ~200K; a multi-finding remediation past that goes to a fresh session.
- **Codex sandbox has NO network:** a new dependency needs the orchestrator to `uv sync` (online) in the cell's worktree.

### Gen-31 lessons

- **A heredoc collapses `\\` to `\`**: `\r`, `\t` in Windows paths became control characters in the state file (caught by the CR count, fixed by `work/orch-g31/fix_ctrl.py`). Write any backslash-bearing file with the Write tool; count CR and tabs before every commit.
- A bare `cd <worktree> && ...` as the first word MOVES the session cwd (four times this generation); use `( cd ... )` or `git -C`, and re-`cd /c/Users/rwsmy/clearwater` when the harness reports a moved cwd.
- A background command launched with `&` inside a foreground Bash call gives no notification: use `run_in_background` (or an until-loop watch on the driver file).
- `git commit -- <new file>` fails for an untracked file: `git add -N <file>` first.
- Codex may AUTO-COMPACT a long session (WP3.6P session 3: 234,009 -> 68,484 footer, window 475,000 -> 258,400); read the footer's `context_window` too.
- CHARC's figure readings can be wrong: verify a unit against the code before passing a ruling to a cell (the /255 correction, `e0c7b856`).

### Live board (RESUME HERE)

**DONE this generation:** WP3.6P EXCLUSIVE windows 5c-16 (EXIT 0, 487.7 s, 73/73, V5/D53/V9 pass in all seven classes) and 5d (default GPU peak 4.11 GB / RSS 1.93 GB, 11.3 s; force-CPU RSS 3.14 GB, 58.4 s) CLOSED; **WP-T7 ACCEPTED** (main `5b922662`; record `docs/proofs/wp-t7-accept.md`; gate `t7` green WITH its own flags: parallel 6,133 / 1 in 476 s, serial 1,230 / 11 in 1,723 s; DR-109 CHARC's to close; main tree `.venv` synced with pytest-timeout 2.4.0; worktree kept until CHARC's accept-side commit).

**1. WP5.3 (Codex; CP5 review pack). Reviewer B IN FLIGHT** (Claude pass started 19:58Z at Claude 91 %, on `2a1e15b1`, base `2050a89a`; prompt and output `clearwater-review-evidence\wp5.3\B\`; it must EXECUTE the two-manifest sequence of CHARC `e4d56665` condition (b)). If `review.seat.log` stays empty and no `claude -p` process runs, it died with gen 31's pane: re-run the same command (check the 92 % line first; a pass that cannot start waits for the 10:00Z reset). Reviewer A CONVERGED at round 4 (`r4\`); the terminating clean-up `2a1e15b1` (turn 10, session 4 `01a19860-839a-7750-9710-a43a65457ede` at **217,380**: any B remediation goes to a FRESH session 5, prompt = preamble + brief + a `dispatch-N.md` in the form of `wp5.3\cell\dispatch-9.md`). Next after B: the RUN REQUESTs in Q8 order (photos, presets, page, then clips; 25 GB free; never in a window or a serial / fullclip leg; one heavy job at a time); then the report turn; then the two-leg gate (rebased onto main first) and the accept.

**2. WP3.6P (Codex) -- GATE NEXT.** Head **`775a0697`** (turn 12: Reviewer B's B-1 primary-size check in both branches, B-2 EXIF parses quiet under DEBUG, B-3 own labels, B-4/B-5 Limits). Reviewer B (EXECUTING, `650bea20` met: E1 117 passed; E2 18/18 planted readers fail by name; E3 class check fails by name) returned NO_NEW_CRITICAL_MAJOR on `bf29c8a3`. Seat-verified at `775a0697`: the three new tests FAIL on `bf29c8a3`'s tool (B-1 "product crop matching FFmpeg escaped independent primary-size check"; B-2 "DEBUG EXIF sentinels reached caplog, raw stderr"; B-3 two failures), then `122 passed, 1 deselected`, ruff, format, mypy (147) clean; the 5b-r2 records show `decoded_size` = `ispe` on all 62 (the seat runs stand). No second B (CHARC informed). NEXT: rebase onto main `5b922662` (`uv sync` its `.venv`), patch-id check, then the two-leg gate WITH the flags (`gate.sh wp3.6p <run> static collect parallel` then `serial` ALONE), the accept record (form `docs/proofs/wp-t7-accept.md` / `wp-d54-accept.md`: the windows' figures, the AD-24 statement for CHARC, B's executions), merge, post. The serial leg cannot run while WP5.3's B or any Codex test turn runs. Session 3 `01a1965f-...` compacted (footer 129,440 of 258,400 after turn 12).

**3. WP5.1 (Codex; acceptance suite).** Head **`88850ad2`** (turn 15, FRESH session 6 `01a19886-ba62-7931-85d1-286dff762225` at 102,897: Reviewer B's B-2..B-7 fixed, crash node 15/15; B-1 no change (CHARC `f6252e0b` lists "case-insensitive" among the defects); B-8 a Limit). Reviewer B (on `7ab7bd39`) NO_NEW_CRITICAL_MAJOR, executed (34 passed; four product mutants caught). NEXT: rebase onto main (`uv sync`), then the gate = parallel + serial + ONE fullclip leg (each stall-watched, serial and fullclip ALONE), the accept commit fills the report's `(gate)` figures, post (CHARC: AD-11 / AD-30 notes).

**4. WP5.2** after the danglers (CHARC; carry the 5d estimate figure 6.13 vs 4.11 GB into its brief).

**Mail:** inbox drained 19:10Z (`work/orch-g31/drain-*.txt`; posts `work/orch-g31/*.md`). No query open with CHARC. Last post: the WP-T7 return report (19:58Z, `6a0b9051`).

**Kept worktrees:** `wp3.6p`, `wp5.3`, `wp5.1` (LIVE); `wp-t7` (accepted; release after CHARC's accept-side commit); `wp4.6` (releasable; copy its gate logs first); `orch-state-g31`; older `brief-*`, `orch-state-g21..g30`. Leftover dir `.worktrees/wp-d54/work` (1.8 GB; owner prune).

### Standing operator rulings

- **Unattended operation** (owner, 2026-10-14; CLAUDE.md "Roles"): every operator-bound question goes `--to charc` (type query, recommended answer first, one cross-session cue after posting). No AskUserQuestion from this seat.
- **GoPro IMU and GPS are OUT OF SCOPE**; nothing from `gpmd`, IMU or GPS is ever committed. WP3.6P privacy lock BINDING.
- **Cell depth:** Claude cells via `scripts/cell_depth.py`; ~250K evaluate, ~400K STOP. Codex: footer `depth_input_tokens`; evaluate ~200K, STOP near 250K.
- **Kernel hazard (7):** never an uncommitted edit in the MAIN tree; edits in a worktree branch, then `git merge --ff-only`.
- **Line endings:** every committed blob LF; 0 CR per file at every gate.
- **DR-99** (CHARC `fbbab0bf`): the bench test's `telemetry_origin` failure alone on main is recorded under DR-99 without a STOP; any OTHER serial failure is a STOP.
