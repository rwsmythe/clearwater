# Orchestrator -- Current State (the read-me-FIRST pointer)

> Overwritten each generation; history lives in `git log -- docs/orchestrator-state.md`.
> Every fact carries the method that re-verifies it.

### Generation

- **Generation 40** (session `clearwater-orchestrator-20261103-1316`) LIVE from 2026-11-03 23:17Z; picked up gen 39's state at `6f8cc6c1`. CHARC is **gen 14 `clearwater-charc-20261103-0028`**; re-verify both names in `comms/.launch-sessions.json` before every cue. Seat folder `work/orch-g40/` (gate.sh / watch.sh / watch2.sh / fill_gate.py copied from g39 with sed `g39`->`g40`). Bash gauge at bring-up: 35 ms. State worktree `.worktrees/orch-state-g40` (the successor removes it and adds its own).
- **Disk:** C: 43 GB free at 23:17Z. `df -h /c` before every window, gate and footage run. STOP below 15 GB free; 25 GB before any window or gate; the fullclip leg needs its basetemp.
- **Paces at 23:17Z:** Codex 22 % (pace 0.235, resets 2026-11-04 10:07Z); Claude 17 % (pace 0.766, resets 2026-11-09 10:00Z). Codex is the lower pace.
- **CHARC subjects: under 100 characters.**

### BINDING RULES CARRIED (each verbatim in `comms/orchestrator/read/`)

- **NO ROLLOVER WHILE A JOB RUNS (OWNER, 2026-11-02, verbatim: "the generations should not have handed over if the previous generation was still working").** Roll in the gap between pieces; never start a long piece the depth cannot see finish.
- **NO PYTEST DURING A SERIAL OR FULLCLIP LEG** or a window (Codex light suites and Claude passes included); one heavy job at a time. CHARC 2026-11-03 12:18Z: a light Codex / Claude turn beside an IMAGE batch (no figures of record) is fine; "keep the rule for anything timed: nothing beside a serial leg, a fullclip leg or a window".
- **Gates carry WP-T7's flags** and the STALL WATCH: `bash work/orch-g40/gate.sh <worktree> <run-id> <legs...>` (legs `static collect parallel serial fullclip harness`; summary `work/orch-g40/gate-<run>/summary.txt`) + Monitor `bash work/orch-g40/watch2.sh <run-id> <summary line count before the start>` (30 min cap; re-arm with the current count).
- **Codex turns:** `uv run python scripts/codex_cell.py turn --worktree <ABS> --prompt <p> --evidence <dir> --turn N [--session <id>] > <dir>\turn-N.driver.stdout 2>&1` with **run_in_background**; commit with `codex_cell.py commit --worktree <ABS> --return-file <return-N.md>`; fill the ledger's `DISPATCHER TO FILL` depth lines first (read `depth_input_tokens` / `context_window` from the footer's LAST line); blob-check 0 CR; `ruff format --check`. FRESH session prompt = `.claude/agents/implementer-codex-sol-high.md` + the brief at HEAD + `dispatch-N.md` joined with blank lines; a RESUMED session's prompt = `dispatch-N.md` alone.
- **Reviewer passes (Claude, for a Codex cell):** `uv run python scripts/codex_cell.py review --worktree <abs> --base <sha> --prompt <p> --out <dir> > <dir>\review.seat.log 2>&1` (background; the diff is appended automatically). Forms: B executing `clearwater-review-evidence\wp-dr25\B\review-prompt-B.md` (report-bearing), B re-run `...\wp-dr25\B\r2\review-prompt-B2.md`. Assert model opus, `is_error` false, verdict line, worktree clean (the seat log's JSON line).
- **Codex review of a Claude cell:** from the worktree, `cat prompt diff | codex exec -p strong -s read-only --skip-git-repo-check -c 'windows.sandbox="unelevated"' -` (form `clearwater-review-evidence\wp5.7\A\r3\`; r4 prompt `...\A\r4\review-prompt.md`); the final answer follows the transcript's last line reading `codex`.
- **Backslash-bearing Python helpers are written with the Write tool**, never a heredoc. **`rm` takes literal absolute paths.** **Worktree release:** a released worktree's `work/` is pruned only on the owner's word; junits copied to `clearwater-review-evidence\<pkg>\gate\` first.
- **A bare `cd` moves the session's cwd** (it carries between Bash calls, and a live Claude cell shares the process): use `git -C`, absolute paths, or `( cd X && ... )`.

### Live board (RESUME HERE) -- gen 40, 2026-11-04 ~01:20Z

1. **OWNER RULED DEFER on DR-117** (CHARC `56d6a473`). Owner-pending: NONE except the word "tag 1.0.0" (to CHARC).
2. **WP5.5 release preparation: BOTH NETS DONE; RELEASE GATE `p55` RUNNING** on the merge head `4742f69f` (main merged INTO `wp5.5` `--no-ff`).
   - Run: `bash work/orch-g40/gate.sh wp5.5 p55 static collect parallel serial fullclip harness`; summary `work/orch-g40/gate-p55/summary.txt`. gate.sh now logs free space per leg and STOPs below 25 GB.
   - Package commits:
     - `e7876912`: build.
     - `6135c496`: A r1 fixes (F1 cp1252 mojibake in 2 texts, F2 Tools > Settings).
     - `51afce88`: A r2 minors and the report.
     - `795a496c`: B remediation (B1 MSVC runtime + opengl32sw notices, CHARC concurred `df16a115aec924ca`; B3 CPU wording).
     - `61b1fd58`: B re-run minors (4 upstream text hashes verified at the seat against the live URLs).
   - Nets:
     - A: r1 NEW_CRITICAL_MAJOR, r2 NO_NEW_CRITICAL_MAJOR (converged).
     - B: first pass on `51afce88` 1 MAJOR (B1); re-run on `795a496c` NO_NEW_CRITICAL_MAJOR.
     - All evidence under `clearwater-review-evidence\wp5.5\` (`cell\`, `A\r1`, `A\r2`, `B\`, `B\r2`).
   - Rulings carried:
     - CHARC R1-R4 (`ce6094d108b9546f`), with the `uv.lock` one-line grant;
     - DR-119 (a)-(b) paid down here;
     - B4 = DR-119 (e) on main `02aac236`.
   - Codex sessions: `01a1a3b6` (turn 1), `01a1a3bf` (turns 2-3), `01a1a3eb` (turns 4-6; ended at 196,594 of 258,400). No cell live.
   - **AT GATE GREEN:**
     - fill the report's gate section with the figures;
     - archive logs and junits to `clearwater-review-evidence\release-1.0.0\`;
     - write the accept record `docs/proofs/wp5.5-accept.md`;
     - ff main to the branch head, re-running the harness if main moved;
     - post to CHARC (N13 / release record are CHARC's);
     - the tag `git tag -a v1.0.0 <merge commit> -m "Clearwater 1.0.0"` ONLY on the owner's "tag 1.0.0" relayed by CHARC; no push.
3. **WP-H1** HELD by CHARC until WP5.5's accept.
- Kept worktrees: `wp5.3`, `wp5.7`, `wp5.8`, `wp-dr25`, `wp5.5`, `orch-state-g40`. Prunes of `work\wp5.7\` and `work\wp-dr25\` only on the owner's word.

### Gen-39 lessons

- **A relayed amendment is processed AFTER the cell's yield** (third time across generations): wp57-cell8 rewrote `run-part3r.sh` one minute into the seat's GPU piece (bash reads a script as it runs). Before running ANY cell-written script after a yield, send HOLD and wait for the reply, or copy the script into the seat folder and run the copy. Memory updated.
- **Kill only the wrappers** when a running script is compromised: `taskkill /PID <bash> /F` without `/T` left the render (python) running to completion; finish the remaining pieces by hand with the original command and log it in runs.txt.
- **Merge main INTO the package branch (`--no-ff`) instead of rebasing** when the report / ledger cite commit hashes; gate the merge head; a later docs-only main commit gets a second merge plus a harness re-run; then ff main.
- **Reviewer B form for a Claude cell** = the WSL script `clearwater-review-evidence\wp5.7\B\run_review_B.sh probe|review` (gpt-6.1-sol / high per call); assert banner, `^ERROR`, footer, `^ succeeded in`, verdict, NUL; a re-run lists the first pass's table (form `B\r2\`).
- **The harness suite prints "acked 1 message(s); moved inbox -> read."** from its own temp mailbox: not the real inbox (check `ls -t comms/orchestrator/read | head -1`). Capture the harness run to a file and grep `^Ran|^OK|^FAILED`.
- I moved the session cwd with a bare `cd` three times while cells were live (absolute paths saved them): use `( cd X && ... )` or `git -C` ONLY.

### Gen-38 lessons

- **A work addendum queued to a cell is processed BEFORE a later stand-down** (wp57-cell5 committed `368b02d2` after its successor was dispatched): never queue work to a cell you may re-seat; send the stand-down, wait for its reply, then dispatch.
- **Python on Windows prints CRLF into a pipe**: a bash `mapfile` of a tool's list keeps the CR (the Part 3 photo batch refused all 70 ids); strip with `tr -d '\r'` and check cell-written window scripts for list pipes before a window.
- **A rebase orphans every commit hash a test or report pins** (WP-DR25: `6dfccdfc` -> Reviewer B MAJOR). Pin revision-loaded code by BLOB id (rebase-stable) and cite runs by instrument blob id plus subject; merge fast-forward.
- When a Codex report turn is running beside an image batch, CHARC confirmed it is fine (not timed).
- A dispatch's "featured frame" list must be copied from the ledger's table of record, not retyped (gen 37 wrote compilation line 1; Part 1's is line 3).

### Gen-37 lessons (carried)

- Edits made with the Edit tool on a CRLF checkout commit CRs with `-c core.autocrlf=false`: write state edits with a Write-tool script that normalises to LF, then blob-check 0 CR.
- A Codex read-only reviewer on a seat-run instrument keeps finding write-path hardening: declare a hostile local actor OUT OF ENVELOPE in the review prompt up front.
- The WP-DR25 `analyse --long` takes about 85 min; plan the GPU queue around such runs.
- A cell's mid-build yield before GPU work is what lets the seat serialise heavy jobs.

### Gen-36 / 35 lessons (carried)

- A fresh worktree has no `work/` (gate.sh does `mkdir -p work`).
- `TaskStop` on a backgrounded `gate.sh` kills only the outer shell: `taskkill /PID <pid> /T /F` the script's bash (find with `Get-CimInstance Win32_Process | ? CommandLine -match 'gate.sh|pytest.exe'`); confirm nothing is left.
- Count CR bytes with `git show HEAD:<f> | tr -cd '\r' | wc -c`.
- A Codex cell's report that cites `work/<pkg>/...` needs durable copies under `clearwater-review-evidence\<pkg>\` before merge.
- The Codex driver footer's `context_window` changes mid-session (258,400 <-> 475,000): record depth with its window and moment.
- The auto-mode classifier refuses bulk deletion under the main tree's `work/`: stage it in a guarded script and give the owner the `! bash <script>` line.
- A window script that runs a tool by relative path must run with the PACKAGE worktree as cwd.
- An NVENC encode fed slowly can hang (DR-115, now watched by AD-32): diagnose with `Win32_Process` I/O counters sampled twice.
- Run the seat's own `bash -n` on every cell-written script.
