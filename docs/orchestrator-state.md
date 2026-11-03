# Orchestrator -- Current State (the read-me-FIRST pointer)

> Overwritten each generation; history lives in `git log -- docs/orchestrator-state.md`.
> Every fact carries the method that re-verifies it.

### Generation

- **Generation 39** (session `clearwater-orchestrator-20261103-1029`) LIVE 2026-11-03 20:29Z; picked up gen 38's state at `561ceb2a` (gen 38 `clearwater-orchestrator-20261103-0215` rolled clean at 400K with nothing running). CHARC is **gen 14 `clearwater-charc-20261103-0028`**; re-verify both names in `comms/.launch-sessions.json` before every cue. Seat folder `work/orch-g39/` (gate.sh / watch.sh / watch2.sh / fill_gate.py, copied from g38 with sed `g38`->`g39`; the successor does the same to g40). **`watch2.sh <run> <offset>`** reads only summary lines after line `<offset>`. Bash gauge at bring-up: 34 ms. State worktree `.worktrees/orch-state-g39` (the successor removes it and adds its own).
- **Disk:** C: 46 GB free at 20:30Z. `df -h /c` before every window, gate and footage run. STOP below 15 GB free; 25 GB before any window.
- **Paces at 20:30Z:** Codex 21 % (pace 0.229, resets 2026-11-04 10:07Z); Claude 15 % (pace 0.73, resets 2026-11-09 10:00Z). Codex is the lower pace.
- **CHARC subjects: under 100 characters.**

### BINDING RULES CARRIED (each verbatim in `comms/orchestrator/read/`)

- **NO ROLLOVER WHILE A JOB RUNS (OWNER, 2026-11-02, verbatim: "the generations should not have handed over if the previous generation was still working").** Roll in the gap between pieces; never start a long piece the depth cannot see finish.
- **NO PYTEST DURING A SERIAL OR FULLCLIP LEG** or a window (Codex light suites and Claude passes included); one heavy job at a time. CHARC 2026-11-03 12:18Z: a light Codex / Claude turn beside an IMAGE batch (no figures of record) is fine; "keep the rule for anything timed: nothing beside a serial leg, a fullclip leg or a window".
- **Gates carry WP-T7's flags** and the STALL WATCH: `bash work/orch-g38/gate.sh <worktree> <run-id> <legs...>` (legs `static collect parallel serial fullclip harness`; summary `work/orch-g38/gate-<run>/summary.txt`) + Monitor `bash work/orch-g38/watch2.sh <run-id> <summary line count before the start>` (30 min cap; re-arm with the current count).
- **Codex turns:** `uv run python scripts/codex_cell.py turn --worktree <ABS> --prompt <p> --evidence <dir> --turn N [--session <id>] > <dir>\turn-N.driver.stdout 2>&1` with **run_in_background**; commit with `codex_cell.py commit --worktree <ABS> --return-file <return-N.md>`; fill the ledger's `DISPATCHER TO FILL` depth lines first (read `depth_input_tokens` / `context_window` from the footer's LAST line); blob-check 0 CR; `ruff format --check`. FRESH session prompt = `.claude/agents/implementer-codex-sol-high.md` + the brief at HEAD + `dispatch-N.md` joined with blank lines; a RESUMED session's prompt = `dispatch-N.md` alone.
- **Reviewer passes (Claude, for a Codex cell):** `uv run python scripts/codex_cell.py review --worktree <abs> --base <sha> --prompt <p> --out <dir> > <dir>\review.seat.log 2>&1` (background; the diff is appended automatically). Forms: B executing `clearwater-review-evidence\wp-dr25\B\review-prompt-B.md` (report-bearing), B re-run `...\wp-dr25\B\r2\review-prompt-B2.md`. Assert model opus, `is_error` false, verdict line, worktree clean (the seat log's JSON line).
- **Codex review of a Claude cell:** from the worktree, `cat prompt diff | codex exec -p strong -s read-only --skip-git-repo-check -c 'windows.sandbox="unelevated"' -` (form `clearwater-review-evidence\wp5.7\A\r3\`; r4 prompt `...\A\r4\review-prompt.md`); the final answer follows the transcript's last line reading `codex`.
- **Backslash-bearing Python helpers are written with the Write tool**, never a heredoc. **`rm` takes literal absolute paths.** **Worktree release:** a released worktree's `work/` is pruned only on the owner's word; junits copied to `clearwater-review-evidence\<pkg>\gate\` first.
- **A bare `cd` moves the session's cwd** (it carries between Bash calls, and a live Claude cell shares the process): use `git -C`, absolute paths, or `( cd X && ... )`.

### Live board (RESUME HERE) -- gen 39, 2026-11-03 23:16Z, NOTHING RUNNING (no cell live, no job)

On pickup: drain the inbox; copy `work/orch-g39/` scripts to `work/orch-g40/`. A cell named below as LIVE dies with its dispatcher's pane: re-dispatch from the ledger.

1. **WP-DR25 ACCEPTED** (main `fa8eceab`; gate `pdr25` GREEN). CHARC: DR-25 CLOSED in full, AD-3 CONFIRMED (main `732f1da4`). Worktree `.worktrees/wp-dr25` + 7.1 GB `work\wp-dr25\` KEPT (owner's word to prune).
2. **WP5.7 ACCEPTED** (main `ce20a176`; record `docs/proofs/wp5.7-accept.md`; gate `p57` GREEN on `d4644511`: parallel 6,781 / serial 1,262 / harness 382; main merged INTO the branch `--no-ff` twice so every cited hash stays reachable, then ff). Nets: A r0-r8 (r6 converged on the package, r8 on the B fix); B on `faf592de` (B1 MAJOR fixed by wp57-cell9); B re-run on `5eb92a51` (MAJOR = DR-119 (a), adjudicated at my seat, CHARC concurring `21f92b6c81d8c978`). Banked: DR-119 (a)-(d), DR-120. DR-117 OPEN: CHARC sends the owner the DEFER / OPTIMISE-NOW decision request (posted 23:15Z). Kept until the owner's word: `.worktrees/wp5.7`, `work\wp5.7\` (part1s, part2 7.6 GB, part3, part3r). Every record durable under `C:\Users\rwsmy\clearwater-review-evidence\wp5.7\`.
3. **WP5.5** release prep (Codex) after WP5.7 merges (brief FINAL; tag `v1.0.0` on the owner's word, no push). **WP-H1** HELD by CHARC until WP5.5's accept.
- Mail drained through 22:30Z (`work/orch-g39/drain-5.txt`); 0 unread at 23:14Z. No query open; WP5.5 awaits CHARC's go.
- Kept worktrees: `wp5.3`, `wp5.7`, `wp5.8`, `wp-dr25`, `orch-state-g39`.

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
