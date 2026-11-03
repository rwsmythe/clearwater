# Orchestrator -- Current State (the read-me-FIRST pointer)

> Overwritten each generation; history lives in `git log -- docs/orchestrator-state.md`.
> Every fact carries the method that re-verifies it.

### Generation

- **Generation 38** (session `clearwater-orchestrator-20261103-0215`) LIVE 2026-11-03 from 12:15Z; picked up gen 37's state at `98a58c29` (gen 37 rolled at the 400K cap with nothing running). CHARC is **gen 14 `clearwater-charc-20261103-0028`**; re-verify both names in `comms/.launch-sessions.json` before every cue. Seat folder `work/orch-g38/` (gate.sh / watch.sh / watch2.sh / fill_gate.py from `work/orch-g37/`, sed `g37`->`g38`; next gen copies to `work/orch-g39/`). **`watch2.sh <run> <offset>`** reads only summary lines after line `<offset>`. Bash gauge at bring-up: 47 ms. State worktree `.worktrees/orch-state-g38` (gen 37's removed).
- **Disk:** C: 60 GB free at 13:40Z. `df -h /c` before every window, gate and footage run. STOP below 15 GB free; 25 GB before any window.
- **Paces at 12:17Z:** Codex 20 % (pace 0.23, resets 2026-11-04 10:07Z); Claude 13 % (pace 0.831, resets 2026-11-09 10:00Z). Codex is the lower pace.
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

### Live board (RESUME HERE) -- 2026-11-03 ~16:20Z

1. **WP-DR25 ACCEPTED** (main `fa8eceab`; record `docs/proofs/wp-dr25-accept.md`; gate `pdr25` GREEN: parallel 6,635 / 1, serial 1,261 / 11, harness 382). CHARC: DR-25 CLOSED in full, AD-3 CONFIRMED, WP1.4 erratum (main `732f1da4`). Worktree `.worktrees/wp-dr25` and 7.1 GB `work\wp-dr25\` KEPT (owner's word to prune).
2. **WP5.7** (Claude lane; `.worktrees/wp5.7`, head `60357596`; evidence `C:\Users\rwsmy\clearwater-review-evidence\wp5.7\`; outputs `C:\Users\rwsmy\clearwater\work\wp5.7\`).
   - Part 2 returned (wp57-cell5) -> Reviewer A r4 (Codex) NEW_CRITICAL_MAJOR (2 MAJOR on conclusions: whole-frame flicker is not V3; undecided counted as removal) -> step 3R fixed (three-way splits verified 11/11 against r4's own table). CHARC: C1-C6 (candidate (d) unsharpened 1 sigma), Q1 NO loop round 5, Q2 V3 on WP4.2's two clips.
   - Part 3 BUILT by wp57-cell6 (`tools/halo_part3.py` + tests, 121 green; depth 364,008 at yield; DONE, treat as stood down). **EXCLUSIVE WINDOW RUNNING at my seat** via `bash C:/Users/rwsmy/clearwater/work/wp5.7/part3/run-part3.sh <piece>`: v3 DONE (shipped reproduces WP4.2's record; (d) passes every asserted bound; ad14 contrast ratio 0.072 -> 0.316 to report); **n6 DONE = C4 STOP: (d) +13.59 % (12.43 vs 10.95 min/min), over N6 itself**; CHARC ruled (msg 4c60bacc3de85d88): continue the window; no adopt-now; owner's choice = defer to Phase 6 with an optimisation item, or optimise now; headroom ~+9.6 %. crops DONE (6/6). photos DONE (70, after a SEAT FIX: `| tr -d '\r'` on the list lines, `run-part3.sh.orig` kept). **videos RUNNING since 15:59Z** (50 items, IMG_6762 last; monitor on `part3\logs\runs.txt`); then `sheet`.
   - NEXT: when videos end, run `sheet`; copy key outputs durable; dispatch FRESH `wp57-cell7` with `...\wp5.7\cell\dispatch-10.md` (state videos + sheet outcome in the starting message) for the ledger Part 3 results + report `docs/reports/wp5.7-halo-investigation.md`; then Reviewer A (Codex; scope: Part 3 build `1db00e58`, the corrected Part 2 tables, the report), Reviewer B (Codex), gate (outcome A: no src/ path; no fullclip), accept; CHARC routes the owner's decision.
3. **WP5.5** release prep (Codex) after WP5.7 merges (brief FINAL; tag `v1.0.0` on the owner's word, no push). **WP-H1** HELD by CHARC until WP5.5's accept.
- Mail drained through 15:41Z (`work/orch-g38/drain-5.txt`). No query open.
- Kept worktrees: `wp5.3`, `wp5.7`, `wp5.8`, `wp-dr25`, `orch-state-g38` (mine).

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
