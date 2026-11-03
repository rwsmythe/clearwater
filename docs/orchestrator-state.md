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

### Live board (RESUME HERE) -- gen 39, 2026-11-03 20:35Z

On pickup: drain the inbox; copy `work/orch-g39/` scripts to `work/orch-g40/`. A cell named below as LIVE dies with its dispatcher's pane: re-dispatch from the ledger.

1. **WP-DR25 ACCEPTED** (main `fa8eceab`; gate `pdr25` GREEN). CHARC: DR-25 CLOSED in full, AD-3 CONFIRMED (main `732f1da4`). Worktree `.worktrees/wp-dr25` + 7.1 GB `work\wp-dr25\` KEPT (owner's word to prune).
2. **WP5.7** (Claude lane; `.worktrees/wp5.7`, head `60357596`; evidence `C:\Users\rwsmy\clearwater-review-evidence\wp5.7\`; outputs `C:\Users\rwsmy\clearwater\work\wp5.7\`).
   - Part 2 + step 3R done; CHARC rulings C1-C6 (candidate (d) unsharpened 1 sigma), Q1 (no loop round 5), Q2 (V3 on WP4.2's two clips), the C4 STOP ruling (msg 4c60bacc3de85d88: the binding bound is N6 itself; no adopt-now; owner's choice = defer to Phase 6 with an optimisation item, or optimise now as a Phase 6-class package; headroom ~+9.6 %).
   - Part 3 built by wp57-cell6 (`tools/halo_part3.py` + tests, `1db00e58`; the cell is DONE and dies with this pane).
   - **THE EXCLUSIVE WINDOW RAN AND IS COMPLETE** (`work\wp5.7\part3\`, logs `part3\logs\runs.txt`; durable copies `...\wp5.7\part3\` and `\v3\`): v3 15:08-15:11Z exit 0 (shipped reproduces WP4.2's record; (d) passes every asserted bound; ad14 contrast ratio c3 0.072 -> 0.316); n6 15:11-15:40Z, six runs valid, **(d) +13.59 % (12.43 vs 10.95 min/min) = C4 STOP, ruled**; crops 15:40-15:49Z 6/6; photos 15:50-15:58Z 70/70 (after the CRLF seat fix in `run-part3.sh`, original `run-part3.sh.orig`); videos 15:59-20:27Z **50/50 exit 0** (IMG_6762 4,441 s); sheet 20:28Z exit 0: "SHEET 120 items; contact: IMG_6762, GX011601, GX011600, GX011590, GX011625, IMG_6751, IMG_6758, IMG_6753, IMG_6755, IMG_6754, IMG_6757, IMG_6746, IMG_6759, IMG_6756, IMG_6752, IMG_6768, IMG_6770, IMG_6767, IMG_6769, IMG_6761".
   - `wp57-cell7` DONE (stood down 20:56Z; depth 221,426 at yield, 237,390 at retirement): ledger Part 3 results `f7b987a4`, report `2041e0b2`, CHARC's texture addendum `d7ac41f3` / `203d1b1f`, my depth line `6b447b3f`. Durable copies MADE: `C:\Users\rwsmy\clearwater-review-evidence\wp5.7\records\` (862 files, 1.1 GB) + `\cell-scratch\`; NOT copied: the two 282 MB N6 exports, the 4.5 GB renders. CHARC opened DR-119 (stale D106 25 bench label + CRLF list; WP5.5 if its fill admits, else Phase 6).
   - **Reviewer A r5** (Codex, `...\wp5.7\A\r5\review.txt`, prompt `review-prompt.md` there): NEW_CRITICAL_MAJOR_FOUND: MAJOR 1 whole-set still selector uses pts relative to the first frame, CP5 stores absolute (GX011590 / GX011603 / GX011609 one frame late); MAJOR 2 the sheet loads dot-prefixed staging records; MINORs n6-summary self-glob, five report cells, durable index, render-equality wording; ADVISORY exact-count test. Confirmed: V3, N6, counts as recorded, every Part 2 three-way split, A-prime.
   - `wp57-cell8` DONE (331,770 at its final yield; stood down 21:43Z): fixes `3ba8f7a1`, docs `d515351d` / `8ab3b7ee` / `69c2dc72`. Re-render of record at my seat: `work\wp5.7\part3r\` (117 copied + GX011590 / GX011603 / GX011609 re-rendered; verify 0 affected; sheet `sheet-20261103T213732053153Z`, the same 20); durable `...\wp5.7\records\part3r\`. Incident: cell8 rewrote `run-part3r.sh` mid-run (a queued amendment processed after its yield); wrappers killed, renders finished by hand (`work\orch-g39\part3r_finish.sh`).
   - **Reviewer A r6** NO_NEW_CRITICAL_MAJOR = CONVERGED (rounds 0-6); its one MINOR fixed at my seat `faf592de`. **Reviewer B** (`...\wp5.7\B\`, WSL form `run_review_B.sh`, five assertions PASS) on `faf592de`: NEW_CRITICAL_MAJOR_FOUND: B1 MAJOR n6_summary validity (no figure moves); B2 / B3 MINOR, B5 ADVISORY fix; B4 (shared `sample` fixture writes outside basetemp) BANKED, DR row recommended to CHARC.
   - **LIVE: `wp57-cell9`** (FRESH `implementer-opus-high`, dispatched ~22:01Z with `...\wp5.7\cell\dispatch-12.md`, code only, no GPU). After its yield: Reviewer A r7 (Codex, read-only, on the fix diff; form `...\A\r6\review-prompt.md`), the ONE B re-run (`B\r2\`, same WSL form), then the gate. A second blocking B is adjudicated at my seat, never a third remediation.
   - **NEXT (2):** the gate on the merge head: MERGE main INTO `wp5.7` (keeps every hash the report / ledger cite; no rebase), then `gate.sh wp5.7 p57 static collect parallel serial harness` (outcome A: no src/ path; both halo test modules in the parallel junit; no fullclip); ff main; CHARC routes the owner's decision (defer / optimise).
3. **WP5.5** release prep (Codex) after WP5.7 merges (brief FINAL; tag `v1.0.0` on the owner's word, no push). **WP-H1** HELD by CHARC until WP5.5's accept.
- Mail drained through 21:01Z (`work/orch-g39/drain-3.txt`). No query open.
- Kept worktrees: `wp5.3`, `wp5.7`, `wp5.8`, `wp-dr25`, `orch-state-g39`.

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
