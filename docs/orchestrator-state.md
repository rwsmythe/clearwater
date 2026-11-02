# Orchestrator -- Current State (the read-me-FIRST pointer)

> Overwritten each generation; history lives in `git log -- docs/orchestrator-state.md`.
> Every fact carries the method that re-verifies it.

### Generation

- **Generation 35** (session `clearwater-orchestrator-20261102-0104`) **ROLLED OVER 2026-11-02 ~20:50Z at ~380K**, at a CLEAN GAP: NOTHING of gen 35's is running (no Codex turn, no reviewer pass, no gate leg, no window, no Monitor). CHARC is **gen 13 `clearwater-charc-20261102-0046`**; re-verify both names in `comms/.launch-sessions.json` before every cue. Seat folder `work/orch-g35/` (gate.sh / watch.sh / watch2.sh / fill_gate.py on `orch-g35` and `g35-` basetemps; copy to `work/orch-g36/` and sed `g35`->`g36`). **`watch2.sh <run> <offset>`** reads only summary lines after line `<offset>` (the plain `watch.sh` exits at once on an OLD `end` line when a run id is reused across invocations).
- **Disk:** C: 57 GB free at 20:48Z (WSL / VM virtual disks grow while mounted: CHARC `40eb646b`). `df -h /c` before every window, gate and footage run. STOP below 15 GB free; 25 GB before any window.
- **Paces at 11:05Z:** Codex 18 % (pace 0.25, resets 2026-11-04 10:07Z); Claude 3 % (week reset 2026-11-02 10:00Z). Re-read both before the next commission.
- **CHARC subjects: under 100 characters.**

### BINDING RULES CARRIED (each verbatim in `comms/orchestrator/read/`)

- **NO ROLLOVER WHILE A JOB RUNS (OWNER, 2026-11-02, verbatim: "the generations should not have handed over if the previous generation was still working").** Roll in the gap between pieces; never start a long piece the depth cannot see finish.
- **NO PYTEST DURING A SERIAL OR FULLCLIP LEG** or a window (Codex light suites and Claude passes included); one heavy job at a time.
- **Gates carry WP-T7's flags** and the STALL WATCH: `bash work/orch-g35/gate.sh <worktree> <run-id> <legs...>` (legs `static collect parallel serial fullclip harness`; summary `work/orch-g35/gate-<run>/summary.txt`) + Monitor `bash work/orch-g35/watch2.sh <run-id> <summary line count before the start>` (30 min cap; re-arm with the current count).
- **Codex turns:** `uv run python scripts/codex_cell.py turn --worktree <ABS> --prompt <p> --evidence <dir> --turn N [--session <id>] > <dir>\turn-N.driver.stdout 2>&1` with **run_in_background** (never a `( ... &)` detach: no notification comes back); commit with `codex_cell.py commit --worktree <ABS> --return-file <return-N.md>`; fill the ledger's `DISPATCHER TO FILL` depth lines first; blob-check 0 CR; `ruff format --check`. FRESH session prompt = `.claude/agents/implementer-codex-sol-high.md` + the brief at HEAD + `dispatch-N.md` joined with blank lines (form `clearwater-review-evidence\wp5.2\cell\prompt-7.md`).
- **Reviewer passes (Claude):** `uv run python scripts/codex_cell.py review --worktree <abs> --base <sha> --prompt <p> --out <dir> > <dir>\review.seat.log 2>&1` (background; the diff is appended automatically). Forms: A `clearwater-review-evidence\wp5.2\r2\review-prompt-r2.md`; B executing `...\wp5.2\B\review-prompt-B.md`; B for a V4/PCM package `...\wp-dr113\B\review-prompt-B.md`. Assert model opus, `is_error` false, verdict line, worktree clean.
- **Rulings folded** with `C:\Users\rwsmy\AppData\Local\Temp\claude\C--Users-rwsmy-clearwater\08801258-a62c-4e7b-b28c-70f4138fdb5c\scratchpad\fold_any.py <brief abs> <ruling file in comms/orchestrator/read> "## <heading>"`, committed by pathspec in the worktree with `-c core.autocrlf=false`.
- **Backslash-bearing Python helpers are written with the Write tool**, never a heredoc (it collapses `\\` and breaks `\U` paths: twice in gen 35).
- **`rm` takes literal absolute paths** (a variable path is refused by the safety check).
- **Worktree release:** a released worktree's `work/` is pruned only on the owner's word; junits are copied to `clearwater-review-evidence\<pkg>\gate\` first (done for wp-dr113 and wp5.2).

### Live board (RESUME HERE)

**DONE gen 35:**
- **WP-DR113 ACCEPTED** (main `6ff6f5d3`; record `docs/proofs/wp-dr113-accept.md`): the V4 instrument reads raw PCM by sample extent and timeline runs; the IMG_6731 GREEN witness (`work\wp3.10\dr113-green`: MANDATORY + REQUIRED all SAME). **DR-113 CLOSED by CHARC** (`d5cd3da2`).
- **WP5.2 ACCEPTED** (main `2da5d0c7`; record `docs/proofs/wp5.2-accept.md`; report `docs/reports/wp5.2-performance-memory.md`): W52-1 (V16: GX011627 cold median 10.889 min/min, GX011625 sustained 10.779), W52-2 (R2 held on the GPU = DR-114 on a real export; the force-cpu export HUNG in NVENC = **DR-115**, opened by CHARC; R3 = the **D111 engagement witness** "CPU: estimate 11,649 MiB exceeds free 7,064 MiB"), W52-3 (force-cpu re-run completed, no hang; post-encode mean 3.329/255 passes). Accept post to CHARC 20:48Z; CHARC writes the N6 proposal to the owner and closes DR-72.

**OPEN / WAITING:**
1. **CP5 is WITH THE OWNER** (pack `work\wp5.3\index.html`, sheet `work\wp5.3\review-sheet.csv`, 126 rows). After the owner fills the sheet (through CHARC): `uv run python -m tools.reviewpack.build tally C:\Users\rwsmy\clearwater\work\wp5.3\review-sheet.csv` from `.worktrees/wp5.3`.
2. **CHARC's answer to the WP5.2 accept post** (N6 proposal, DR-72 close, any row). Nothing for the orchestrator unless CHARC commissions.
3. **Next commission:** none in hand. The Phase 5 gate report and anything from the N6 ruling or CP5 come from CHARC.

**Mail:** inbox drained through 20:10Z (`work/orch-g35/drain-*.txt`; posts `work/orch-g35/*.md`). No query open with CHARC. Last post: the gen-35 rollover announcement; gen 35 does not drain after it.

**Kept worktrees:** `wp5.2` and `wp-dr113` (released after merge; their `work/` kept until the owner's word: `wp5.2/work/wp5.2/tmp/*.sh` are the scripts' seat copies), `wp5.3` (CP5 tally later), `brief-*`, `orch-state-g21..g35`, `wp-d112`, `wp5.1` (released). Seat-run window records live in the MAIN tree's `work\wp5.2\` (1.1 GB; the 158 MB whole-clip copy `W52-2\attempt-...\W52-2-GX011627-whole.mp4` awaits a prune ruling). Orphans `work/orch-g33/vs-orphans/` (~2.0 GB) prune only on the owner's word.

### Gen-35 lessons

- A window script that runs a tool by relative path (`tools/...`) must run with the PACKAGE worktree as cwd: `bash -c 'cd <worktree> && bash <script>'` (a child shell's `cd` leaves the session's directory alone).
- An NVENC encode fed slowly (~10 s/frame on the CPU route) can hang inside NVENC (DR-115): the encoder's main thread spins at 100 % with zero I/O and the product never fails the job. Diagnose with `Win32_Process` I/O counters sampled twice (decoder / exporter / encoder transfer totals locate the stuck stage); end ONLY the encoder (your own child) so the product's failure path and D85 clean-up run; save the counters first.
- A window's length estimate in a brief can be badly wrong (the CPU leg was ~10 s/frame, not ~2); post a corrected estimate to CHARC mid-window rather than waiting.
- Run the seat's own `bash -n` on every cell-written script (the Codex sandbox cannot start Git Bash) and check it is byte-identical to its committed ledger block before saving it under the main tree's `work\`.
