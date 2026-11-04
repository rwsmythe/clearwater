# Orchestrator -- Current State (the read-me-FIRST pointer)

> Overwritten each generation; history lives in `git log -- docs/orchestrator-state.md`.
> Every fact carries the method that re-verifies it.

### Generation

- **Generation 41** (session `clearwater-orchestrator-20261103-2220`) LIVE from 2026-11-04 08:20Z; picked up gen 40's state at `3821a5d8`. CHARC is **gen 14 `clearwater-charc-20261103-0028`**; re-verify both names in `comms/.launch-sessions.json` before every cue. Seat folder `work/orch-g41/` (gate.sh / watch.sh / watch2.sh / fill_gate.py copied from g40 with sed `g40`->`g41`). Bash gauge at bring-up: 37 ms. State worktree `.worktrees/orch-state-g41`.
- **Disk:** C: 97 GB free at 08:21Z. `df -h /c` before every window, gate and footage run. STOP below 15 GB free; 25 GB before any window or gate.
- **Paces at 08:21Z:** Codex 23 % / 0.232 (resets 2026-11-04 10:07Z); Claude 23 % / 0.833 (resets 2026-11-09 10:00Z).
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

### Live board (RESUME HERE) -- gen 41, from 08:20Z

**LIVE (gen 41, 08:23Z):** WP6.1 round 0 = Claude opus-high cell `wp61-cell1` (Agent-tool subagent, read-only), worktree `.worktrees/wp6.1` branch `wp6.1` at `c051306f`, dispatch `clearwater-review-evidence\wp6.1\cell\dispatch-1.md`. WP6.2 round 0 = Codex turn 1 (read-only), worktree `.worktrees/wp6.2` branch `wp6.2` at `5671a927`, prompt `clearwater-review-evidence\wp6.2\cell\prompt-1.md`. A successor RE-DISPATCHES both from these files (a cell dies with the pane). Online post `f02c1100`. Gen 40's board follows (items 1-2 = the packages now live).

1. **WP6.1, packaging spike. FINAL at `223b33f4`** (`docs/briefs/wp6.1-brief.md`, gen 40's fill `dadf3013`).
   - Rulings: Q5 = the `--export-worker` argv, dispatched in `__main__` before any Qt import and built by `composition.py:461` when frozen (both files owned). Q6 = the pack root per platform (`None` on macOS).
   - Lane: **Claude opus-high** (`implementer-opus-high`, an Agent-tool subagent, FRESH).
   - Reviewers: A = Codex `codex exec -p strong -s read-only` (the WP5.7 A form); B = the WSL Codex script (the WP5.7 B form).
   - **Dispatch round 0, read-only**, in a NEW worktree `.worktrees/wp6.1` (branch `wp6.1` from main's head; copy `clearwater.local.toml`). Evidence `C:\Users\rwsmy\clearwater-review-evidence\wp6.1\`.
   - **PyInstaller in the dev group is a STOP to CHARC first** (the N13 row). The cell names the version in round 0.
   - Timing windows are EXCLUSIVE.
   - Read the cell's depth with the new `scripts/cell_depth.py --project <proj> --session=<id> --agent <name>`.
2. **WP6.2 (portability audit, Codex, read-only) and WP-T8 (tools / tests paydown, Codex): fills POSTED** at `7a8f5135` for CHARC's FINAL.
   - The fills set: ONE Codex cell at a time, WP6.2 first, WP-T8 after WP6.2 yields for its nets.
   - WP-T8's three gate legs never overlap a WP6.1 build or timing window.
   - Dispatch each only on its FINAL.
3. **Done this generation:**
   - **1.0.0:** tagged `v1.0.0` on `40d2ce04`. Pushed: `origin/main` was `f46e0d71`, then `8037995b` on the owner's word. Later main commits (`bf3a767d`, `031c7cb8`, the fills) are NOT pushed: a further push needs the owner's word.
   - **WP-H1:** ACCEPTED `5dc227dd`. Template branch `clearwater-upstream-2026-11-04` = `911e783`, PUSHED on the owner's word. CHARC opened PR #2; the merge is the owner's click.
   - **PRUNE DONE** (record `031c7cb8`): six worktrees and `work/wp5.3`, `wp5.7`, `wp-dr25` removed; branches kept; C: 97 GB.
- **Worktrees now:** main plus `orch-state-g40` only.
- **Paces** at 08:17Z: Codex 23 % / 0.233 (window resets 10:07Z); Claude 22 % / 0.799.

### Gen-40 lessons (WP-H1 additions)

- **A reviewer's mutation probes find untested guards that a green suite hides.** Both nets did it on WP-H1 (A r1 F1 MAJOR; B3). Ask every review prompt for mutation probes against a COPY of the code under the probe folder.
- **A re-port diff (instance → template) can carry hunks that predate the package.** WP-H1's would have put back a private identifier the template had deliberately removed. Before the accept, diff against `template/main` and scan the added lines for instance vocabulary.
- **The Codex sandbox's restricted token cannot list `tempfile.mkdtemp`'s 0o700 dirs.** Preload `scripts/sandbox_mkdir_shim.py` into unittest:
  `PYTHONPATH=scripts uv run --no-sync python -c "import sandbox_mkdir_shim, unittest, sys; ..."`
  The seat's unshimmed run is the suite of record.
- **A dispatch's command spelling can trip a doc guard.** `test_doc_acceptance` bans the literal `--session ` (with a space), so write `--session=<id>` in kernel docs.
- `tests/harness/test_cell_depth.py` imports a sibling `_loader`: run it with `discover -s tests/harness -p test_cell_depth.py`, not `-m unittest tests.harness...`.
- **Native Windows Python does not resolve `/c/...` paths.** Read the driver JSON with `grep`, or pass `C:\` paths.

### Gen-40 lessons

- **A new root-level or `docs/` file needs its harness registration** (`tests/harness/genericity_lists.py`, `INSTANCE_SURFACE_RELPATHS`). Only the harness leg catches it (the genericity guard + manifest accounting); gate `p55`'s harness leg failed on WP5.5's three release files after 70 minutes of green pytest legs. **Run the harness gate on the package head BEFORE Reviewer B**, and put the registration in the brief's owned files.
- **A Codex cell's licence-text copy must decode as UTF-8 bytes explicitly**: the locale default (cp1252) garbled two texts, and the self-check hashed the garbled copy. Ask for hashes of the SOURCE bytes and a marker scan (`Â`, `Ã`, `â€`, U+FFFD).
- **The Codex sandbox has no network**: anything needing an index (`uv run --with ...`, a lean sync with uncached packages) runs at the seat. Record the exact command in a `.record.txt` beside its log, or the reviewer cannot tell what ran.
- **The review driver appends the whole diff**: for a package with a large generated file, exclude it through `codex_cell` (`DIFF_EXCLUDES` patched by a `python -c` wrapper) and tell the reviewer to read it with tools.
- **A dispatcher's fill of a ruling into a cell's report can mis-scope it** (B re-run N-3: my fill made CHARC's concurrence cover a broader sentence): fill with a sentence of its own.
- A bare `cd` in a Bash call moved the session cwd twice this generation (no cell live): use `git -C` or a subshell.

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
