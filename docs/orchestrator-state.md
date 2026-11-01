# Orchestrator -- Current State (the read-me-FIRST pointer)

> Overwritten each generation; history lives in `git log -- docs/orchestrator-state.md`.
> Every fact carries the method that re-verifies it.

### Generation

- **Generation 30** (session `clearwater-orchestrator-20261101-0043`; CHARC gen 11 `clearwater-charc-20261101-0727`; re-verify both in `comms/.launch-sessions.json`). Brought up 2026-11-01 10:44Z (bash gauge 38 ms). **ROLLED OVER 2026-11-01 ~18:12Z at ~385K** (clean boundary: every Codex turn returned and committed; ONE Claude pass in flight, below).
- **Disk:** C: ~170 GB free at 17:55Z. `df -h /c` before every window, gate and footage run. STOP below 15 GB free (20 GB for WP3.6P, 25 GB before WP5.3 clips).
- **Paces at 18:02Z:** Claude 89 % / pace 0.983 (resets 2026-11-02 10:00Z); Codex 14 % / 0.228 (resets 2026-11-04 10:07Z).

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

**DONE this generation:** **WP-D54 ACCEPTED** (main `4ece5183`; record `docs/proofs/wp-d54-accept.md`; CHARC CONFIRMED, DR-102 CLOSED / DR-107 at `44c8633f`; worktree released, branch kept). DR-108 / DR-109 opened by CHARC (the hang). WP-T7 commissioned and drafted.

**1. WP-T7 (Codex; gate hygiene, closes DR-109).** Worktree `.worktrees/wp-t7`, branch `wp-t7`, brief `a9fa11cd` + folds `facd98ee`; RED `aa88d12d`; partial build `53b4e4b2` (pytest-timeout 2.4.0 in `dev`, uv.lock +14, three ini lines). Session `01a1983a-45de-7530-8ca2-8d53963ad4c7` (108,375 after turn 2). Turn 3 committed **`e4938910`** (session at 147,790): proof GREEN (3.05 s at my seat); facts per the cell: thread = stacks then `os._exit`; under xdist the crashed worker is REPLACED and the leg continues; func-only leaves fixtures un-timed; faulthandler dumps without failing. The cell's harness-gate STOP is ANSWERED: at my seat in the worktree `Ran 382 tests ... OK (skipped=1)`. **Reviewer A round 1 (Claude pass) IN FLIGHT at roll** (started ~18:08Z; prompt and output `clearwater-review-evidence\wp-t7\r1\`; if `review.seat.log` stays empty and no `claude -p` process runs, it died with gen 30's pane: re-run the same command). Next: assert it; adjudication turn (resume the session); report turn; Reviewer B; the gate WITH the new flags (no fullclip) + the harness gate; accept (DR-109 CHARC's).

**2. WP5.3 (Codex; CP5 review pack).** Head **`a14a25ed`** (turn 8: R3 adjudicated, all seven ACCEPTED per `c25ff7a9`, which is folded at `4d5922eb`; code at `ed787934`). Session 3 `01a196ca-bf8b-7533-8a65-e61fa8aef47e` RETIRES at 182,934 (evaluation point, seven-item remediation ahead). Reviewer A: R1, R2, R3 each found a MAJOR (silent-loss paths); R3 ruled ALL SEVEN items (F1 manifest never prunes state, audit every `state["items"]` write with a "cannot shrink" table; F2/F3 in the round-2 viewing_aid_failed form; F4 item error; F5 page exit 2 while pending; F6 sanitiser collapses to the last component and survives spaces; F7 a README/page sentence). **A fourth silent-loss finding in round 4 = STOP to CHARC.** NEXT: turn 9 = remediation per `c25ff7a9` in a FRESH session 4 (prompt = preamble + brief + a `dispatch-9.md` in the form of `wp5.3\cell\dispatch-7.md`: the ledger's `## Reviewer A round 3 (adjudicated)`, the r3 findings file, the ruling's audit table of every `state["items"]` write), Reviewer A round 4 (prompt: copy `r3\review-prompt-r3.md` with head/round/probe-folder updated), round 5 is the cap. Then RUN REQUESTs (photos, presets, page, clips; 25 GB free; never in a window or during a serial leg).

**3. WP5.1 (Codex; acceptance suite).** REBASED onto main `4ece5183` (head `f059b2e0`, patch-id `b82a2353de70` unchanged); **T6-1 GREEN** (witness 1 passed). Session 5 `01a196ca-bef4-73a3-bf82-98d429e96768` (158,027 after turn 13). **Reviewer A CONVERGED at round 2** (NO_NEW_CRITICAL_MAJOR). Turn 13 committed **`d44db8d1`** (the terminating clean-up: crash node pins pid + `__file__`, the launcher mutant now FAILS; 15/15; V17 row; advisories; light 34 passed; format 297 clean; 0 CR). It changed `tests/test_v51_video_acceptance.py` (+11/-3): check whether the gpu node changed; a seat re-run of the gpu + gui nodes ONLY if turn 13 touched them (form: `t12-seat` command in `cell\prompt-13.md`), T10 report turn, Reviewer B (Claude pass, executing), the gate = parallel + serial + ONE fullclip leg (each with the stall watch, nothing else on the host during serial and fullclip), the accept (CHARC: AD-11 / AD-30 notes).

**4. WP3.6P (Codex) -- the 5c-16 EXCLUSIVE window is OWED** (head `790541e7`; the command and ledger lines 1904-1930 as in the gen-29 state: `git show f4dc507d:docs/orchestrator-state.md`). Open it to CHARC only when NOTHING else runs (no Codex turn running tests, no Claude pass, no gate). Then 5d EXCLUSIVE (default then force-cpu), then one cell turn (session `01a1965f-ef09-7e52-b182-63fcf730d355`), Reviewer B (executing, `650bea20`), gate, accept.

**5. WP5.2** after the windows (CHARC).

**Mail:** inbox drained 18:00Z (last post 18:07Z, status batch) (`work/orch-g30/drain-*.txt`; my posts `work/orch-g30/*.md`). No query open with CHARC.

**Kept worktrees:** `wp3.6p`, `wp5.3`, `wp5.1`, `wp-t7` (LIVE); `wp4.6` (releasable per gen 29; copy its gate logs first); `orch-state-g30`; older `brief-*` and `orch-state-g21..g29`. Leftover dir `.worktrees/wp-d54/work` (1.8 GB, unregistered; owner prune).

### Standing operator rulings

- **Unattended operation** (owner, 2026-10-14; CLAUDE.md "Roles"): every operator-bound question goes `--to charc` (type query, recommended answer first, one cross-session cue after posting). No AskUserQuestion from this seat.
- **GoPro IMU and GPS are OUT OF SCOPE**; nothing from `gpmd`, IMU or GPS is ever committed. WP3.6P privacy lock BINDING.
- **Cell depth:** Claude cells via `scripts/cell_depth.py`; ~250K evaluate, ~400K STOP. Codex: footer `depth_input_tokens`; evaluate ~200K, STOP near 250K.
- **Kernel hazard (7):** never an uncommitted edit in the MAIN tree; edits in a worktree branch, then `git merge --ff-only`.
- **Line endings:** every committed blob LF; 0 CR per file at every gate.
- **DR-99** (CHARC `fbbab0bf`): the bench test's `telemetry_origin` failure alone on main is recorded under DR-99 without a STOP; any OTHER serial failure is a STOP.
