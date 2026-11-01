# Orchestrator -- Current State (the read-me-FIRST pointer)

> Overwritten each generation; history lives in `git log -- docs/orchestrator-state.md`.
> Every fact carries the method that re-verifies it.

### Generation

- **Generation 31** (session `clearwater-orchestrator-20261101-0811`; CHARC gen 11 `clearwater-charc-20261101-0727`; re-verify both in `comms/.launch-sessions.json`). Brought up 2026-11-01 18:12Z (bash gauge 24 ms). LIVE (mid-generation snapshot 18:40Z).
- **Disk:** C: ~166 GiB free at 18:30Z. `df -h /c` before every window, gate and footage run. STOP below 15 GB free (20 GB for WP3.6P, 25 GB before WP5.3 clips).
- **Paces at 18:28Z:** Claude 90.0 % / pace 0.992 (resets 2026-11-02 10:00Z); Codex 14 % / 0.226 (resets 2026-11-04 10:07Z).

### BINDING RULES CARRIED (each verbatim in `comms/orchestrator/read/`)

- **92 % rule (CHARC `e4282d85`, until the 2026-11-02 10:00Z reset):** NO Claude pass STARTS once `uv run python scripts/usage_claude.py` reads >= 92 %; Codex turns continue. Priority: WP3.6P's passes before WP5.x. NEVER lower the reviewer tier. Report the Claude figure with every window open/close and every review-round post.
- **NO PYTEST DURING A SERIAL LEG (CHARC `97d5abbf` item 3, STANDING):** while a gate's SERIAL (or fullclip) leg runs, NO other pytest of any size runs on the host (Codex light suites and Claude review passes included). Hold those turns.
- **STALL WATCH ON EVERY GATE (CHARC gen 10 roll `97d7981b`, STANDING):** every gate leg runs with a Monitor that emits on completion OR on the log unchanged for 5 min. A hang anywhere = STOP to CHARC with the node (DR-108). Form: `work/orch-g30/serial-d54.sh` + the Monitor in this generation's history. Find a hung node from the basetemp's newest dirs and `--collect-only` order.
- **Reviewer A/B Claude-pass prompts:** commands must START with `uv run`, `timeout`, `python`, `.venv/Scripts/python.exe`, `git diff|log|show|status|cat-file|branch`, `grep`, `ls`; create the probe folder at the seat first; give the exact `uv run pytest` line and require it first. Forms: `clearwater-review-evidence\wp5.1\r2\review-prompt-r2.md`, `...\wp5.3\r3\review-prompt-r3.md`; B withholding the report: `...\wp-d54\B\run_review_B.py`. Launch: `uv run python scripts/codex_cell.py review --worktree <abs> --base <sha> --prompt <p> --out <dir> > <dir>\review.seat.log 2>&1` (background).
- **WP3.6P Reviewer B (CHARC `650bea20`):** must EXECUTE (pytest selection, planted-reader control, ICC-presence class check), proved by one succeeded line.
- **Windows:** EXCLUSIVE, opened and closed to CHARC (post + cue), one at a time, nothing else heavy.
- Every ruling saved into the package's evidence folder and FOLDED into the brief on the package branch: `uv run python <scratchpad>\fold_any.py <brief abs path> <ruling file name in comms/orchestrator/read> "<heading>"`, then `git -C <wt> -c core.autocrlf=false commit -q -m ... -- <brief>`. Script copy: `C:\Users\rwsmy\AppData\Local\Temp\claude\C--Users-rwsmy-clearwater\08801258-a62c-4e7b-b28c-70f4138fdb5c\scratchpad\fold_any.py` (if gone: read the ruling, strip the front matter, quote each line with "> ", append under the heading, write LF bytes; use the Write tool).
- **Codex turns:** `uv run python scripts/codex_cell.py turn --worktree <ABS> --prompt <p> --evidence <dir> --turn N [--session <id>] > <dir>\turn-N.driver.stdout 2>&1` (background); commit with `codex_cell.py commit --worktree <ABS> --return-file <return-N.md>`; blob-check 0 CR; `ruff format --check` at the seat. A FRESH session's prompt = `.claude/agents/implementer-codex-sol-high.md` + the brief + a `dispatch-N.md` (forms: `wp5.1\cell\dispatch-12.md`, `wp5.3\cell\dispatch-7.md`). Re-seat a Codex session at ~200K when a multi-finding remediation is ahead.
- **Codex sandbox has NO network:** a new dependency needs the orchestrator to `uv sync` (online) in the cell's worktree (WP-T7 precedent).

### Gen-30 lessons

- **A wait must watch for a STALL, not only the end line** (6 h lost on the D54 serial hang). Memory `gate-wait-needs-stall-watch`.
- `codex_cell.py turn` creates `turn-N.driver.stdout` EMPTY at start: watch the PID or a non-empty size, never `-e`.
- Bare `cd` in a foreground Bash call moved the session cwd TWICE; use `( cd ... )` or `git -C`.
- `git worktree remove` cannot delete a worktree's ignored `work/` basetemps (1.8 GB left at `.worktrees/wp-d54/work`): owner prune list.

### Live board (RESUME HERE)

**DONE this generation:** WP3.6P EXCLUSIVE windows 5c-16 (EXIT 0, 487.7 s, 73/73, V5/D53/V9 pass in all seven classes) and 5d (default GPU peak 4.11 GB, 11.3 s; force-CPU RSS 3.14 GB, 58.4 s; both EXIT 0) CLOSED to CHARC; hold released. WP-T7 Reviewer A r1 asserted and converged; clean-up `e78d9bfb`, F3 redirect `1d541378`. WP5.1 T10 report `7ab7bd39`.

Claude-pass queue (CHARC order, 92 % rule): WP3.6P B -> WP-T7 B -> WP5.3 A R4 -> WP5.1 B. Prompts ready: `clearwater-review-evidence\<pkg>\B\review-prompt-B.md` + `run_review_B.py` (launch: `uv run python <run_review_B.py> review --worktree <abs> --base <sha> --prompt <p> --out <dir> > <dir>\review.seat.log 2>&1`, background). WP3.6P's prompt has `HEADSHA` placeholders (sed them to the final head). Probe folders `work/<pkg>/rB-tmp` created.

1. **WP3.6P** (session 3 `01a1965f-ef09-7e52-b182-63fcf730d355`, 184,466 before turn 10). Turn 10 (seat runs recorded + report) RUNNING since 18:31Z. NEXT: turn 11 = CHARC `dbf02ad7` items (saved `clearwater-review-evidence\wp3.6p\report-items-dbf02ad7.md`; fold into the brief first): item 1 CORRECTED by my query `4224e6af` (the quant field IS /255, x255 at `photo_verify.py:1037`; 7.57e-06 /255 = exact to float32), RULED by CHARC `e0c7b856` (turn 11 carries that form verbatim); items 2 (classes separate, 9 assumed named) and 3 (5d estimate 6.13 vs 4.11 GB a Limit; CPU leg as characterisation). Then B (EXECUTING E1-E3), the two-leg gate (new timeout flags only after WP-T7 lands), accept.
2. **WP5.3** turn 9 RUNNING since 18:30Z in a FRESH session 4 (prompt `wp5.3\cell\prompt-9.md`; read the session id from `turn-9.driver.stdout`). Then Reviewer A round 4 (copy `r3\review-prompt-r3.md`, head/round/probe updated); a fourth silent-loss finding = STOP to CHARC; round 5 is the cap.
3. **WP-T7** head `1d541378` (session `01a1983a-...` at 180,712). Next: B (prompt ready), the two-leg gate WITH the new flags + redirects + the harness gate, accept (DR-109 CHARC's).
4. **WP5.1** head `7ab7bd39` (session 5 at 238,374: any remediation goes to a FRESH session). Next: B (prompt ready, base `4ece5183`), rebase onto main after WP-T7 lands, the gate = parallel + serial + ONE fullclip (with flags), the accept (fill the report's `(gate)` figures in the accept commit).
5. WP5.2 after the danglers (CHARC).

**Mail:** drained 18:31Z (`work/orch-g31/drain-*.txt`; posts `work/orch-g31/*.md`). No query open with CHARC.

### Standing operator rulings

- **Unattended operation** (owner, 2026-10-14; CLAUDE.md "Roles"): every operator-bound question goes `--to charc` (type query, recommended answer first, one cross-session cue after posting). No AskUserQuestion from this seat.
- **GoPro IMU and GPS are OUT OF SCOPE**; nothing from `gpmd`, IMU or GPS is ever committed. WP3.6P privacy lock BINDING.
- **Cell depth:** Claude cells via `scripts/cell_depth.py`; ~250K evaluate, ~400K STOP. Codex: footer `depth_input_tokens`; evaluate ~200K, STOP near 250K.
- **Kernel hazard (7):** never an uncommitted edit in the MAIN tree; edits in a worktree branch, then `git merge --ff-only`.
- **Line endings:** every committed blob LF; 0 CR per file at every gate.
- **DR-99** (CHARC `fbbab0bf`): the bench test's `telemetry_origin` failure alone on main is recorded under DR-99 without a STOP; any OTHER serial failure is a STOP.
