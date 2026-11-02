# Orchestrator -- Current State (the read-me-FIRST pointer)

> Overwritten each generation; history lives in `git log -- docs/orchestrator-state.md`.
> Every fact carries the method that re-verifies it.

### Generation

- **Generation 36** (session `clearwater-orchestrator-20261102-1050`) **LIVE since 2026-11-02 ~20:50Z**, picked up gen 35's state at `91d83a9e` (gen 35 rolled at ~380K at a clean gap). CHARC is **gen 13 `clearwater-charc-20261102-0046`**; re-verify both names in `comms/.launch-sessions.json` before every cue. Seat folder `work/orch-g36/` (gate.sh / watch.sh / watch2.sh / fill_gate.py copied from `work/orch-g35/`, sed `g35`->`g36`; next gen copies to `work/orch-g37/`). **`watch2.sh <run> <offset>`** reads only summary lines after line `<offset>` (the plain `watch.sh` exits at once on an OLD `end` line when a run id is reused across invocations). Bash gauge at bring-up: 26-38 ms.
- **Disk:** C: 52 GB free at 22:06Z (end of gate p5b) (WSL / VM virtual disks grow while mounted: CHARC `40eb646b`). `df -h /c` before every window, gate and footage run. STOP below 15 GB free; 25 GB before any window.
- **Paces at 20:50Z:** Codex 19 % (pace 0.244, resets 2026-11-04 10:07Z); Claude 5 % (pace 0.774, resets 2026-11-09 10:00Z). Codex is the lower pace. Re-read both before the next commission.
- **CHARC subjects: under 100 characters.**

### BINDING RULES CARRIED (each verbatim in `comms/orchestrator/read/`)

- **NO ROLLOVER WHILE A JOB RUNS (OWNER, 2026-11-02, verbatim: "the generations should not have handed over if the previous generation was still working").** Roll in the gap between pieces; never start a long piece the depth cannot see finish.
- **NO PYTEST DURING A SERIAL OR FULLCLIP LEG** or a window (Codex light suites and Claude passes included); one heavy job at a time.
- **Gates carry WP-T7's flags** and the STALL WATCH: `bash work/orch-g36/gate.sh <worktree> <run-id> <legs...>` (legs `static collect parallel serial fullclip harness`; summary `work/orch-g36/gate-<run>/summary.txt`) + Monitor `bash work/orch-g36/watch2.sh <run-id> <summary line count before the start>` (30 min cap; re-arm with the current count).
- **Codex turns:** `uv run python scripts/codex_cell.py turn --worktree <ABS> --prompt <p> --evidence <dir> --turn N [--session <id>] > <dir>\turn-N.driver.stdout 2>&1` with **run_in_background** (never a `( ... &)` detach: no notification comes back); commit with `codex_cell.py commit --worktree <ABS> --return-file <return-N.md>`; fill the ledger's `DISPATCHER TO FILL` depth lines first; blob-check 0 CR; `ruff format --check`. FRESH session prompt = `.claude/agents/implementer-codex-sol-high.md` + the brief at HEAD + `dispatch-N.md` joined with blank lines (form `clearwater-review-evidence\wp5.2\cell\prompt-7.md`).
- **Reviewer passes (Claude):** `uv run python scripts/codex_cell.py review --worktree <abs> --base <sha> --prompt <p> --out <dir> > <dir>\review.seat.log 2>&1` (background; the diff is appended automatically). Forms: A `clearwater-review-evidence\wp5.2\r2\review-prompt-r2.md`; B executing `...\wp5.2\B\review-prompt-B.md`; B for a V4/PCM package `...\wp-dr113\B\review-prompt-B.md`. Assert model opus, `is_error` false, verdict line, worktree clean.
- **Rulings folded** with `C:\Users\rwsmy\AppData\Local\Temp\claude\C--Users-rwsmy-clearwater\08801258-a62c-4e7b-b28c-70f4138fdb5c\scratchpad\fold_any.py <brief abs> <ruling file in comms/orchestrator/read> "## <heading>"`, committed by pathspec in the worktree with `-c core.autocrlf=false`.
- **Backslash-bearing Python helpers are written with the Write tool**, never a heredoc (it collapses `\\` and breaks `\U` paths: twice in gen 35).
- **`rm` takes literal absolute paths** (a variable path is refused by the safety check).
- **Worktree release:** a released worktree's `work/` is pruned only on the owner's word; junits are copied to `clearwater-review-evidence\<pkg>\gate\` first (done for wp-dr113 and wp5.2).

### Live board (RESUME HERE)

**DONE gen 36:**
- **WP5.6 ACCEPTED** (main `ef31c68a`; record `docs/proofs/wp5.6-accept.md`; report `docs/reports/wp5.6-gate-report.md`, **DRAFT with ONE pending field: CP5 / V2**; N6 written SET = 12 min/min at 4K, spec 0.5.8 `1db84842`, owner "Concur with 12"). Codex lane, one session, three turns; Reviewer A replaced per the brief (docs-only); Reviewer B Claude NO_NEW_CRITICAL_MAJOR. Gate **p5b** on `1934bcbb` GREEN: P 6,597/1 515 s, S 1,261/11 2,046 s, F 7 1,569 s, harness 382 (files `C:\Users\rwsmy\clearwater-review-evidence\wp5.6\gate\`). Accept post to CHARC 22:25Z with five dispositions (DR-86 trigger fired; CHARC condition `d4224524` due; DR-25 (3) absent from WP5.2; spec 0.5.8 "GX011627 4K 60" is really 29.97 fps; two brief slips).

**OPEN / WAITING:**
1. **CP5 is WITH THE OWNER** (pack `work\wp5.3\index.html`, sheet `work\wp5.3\review-sheet.csv`, 126 rows). After the owner fills the sheet (through CHARC): `uv run python -m tools.reviewpack.build tally C:\Users\rwsmy\clearwater\work\wp5.3\review-sheet.csv` from `.worktrees/wp5.3`. CHARC then fills V2 in the WP5.6 report and marks it FINAL; the Phase 5 close is CHARC's.
2. **CHARC's answer to the WP5.6 accept post** (the five dispositions). Nothing for the orchestrator unless CHARC commissions.
3. **Next commissions named by CHARC (after the Phase 5 close):** WP5.5 release prep; the DR-115 watchdog scope question to the owner; a `cell_depth.py` second-pass brief. None in hand.

**Mail:** inbox drained through 22:15Z (`work/orch-g36/drain-*.txt`; posts `work/orch-g36/*.md`). No query open with CHARC.

**Kept worktrees:** `wp5.6` (the p5b gate tree, released; `work/` holds the basetemps and junits, already copied to evidence) and `wp5.6r` (released); `wp5.3` (CP5 tally later); `wp5.2`, `wp-dr113`, `wp-d112`, `wp5.1` (released; `work/` kept until the owner's prune word); `brief-*`; `orch-state-g21..g36`. The prune-candidate list with sizes is the WP5.6 report's Result 6 (seat inventory `work/orch-g36/prune-inventory.txt`, copy in the evidence folder). V-S orphans `work/orch-g33/vs-orphans/` measure **3.0 GB** (not ~2.0).

### Gen-36 lessons

- **A fresh worktree has no `work/`**: pytest's basetemp under `work/` fails at once (`INTERNALERROR ... WinError 3`). `work/orch-g36/gate.sh` now runs `mkdir -p work` after its `cd`.
- **`TaskStop` on a backgrounded `gate.sh` kills only the outer shell**: the script's bash and its pytest children keep going (the stopped run went on into serial, then fullclip). End the tree with PowerShell `taskkill /PID <gate.sh bash pid> /T /F` after finding it with `Get-CimInstance Win32_Process | ? CommandLine -match 'gate.sh|pytest.exe'`; confirm nothing is left before re-running.
- A CR check written as `"... $(git show ... | grep -c $'\r')"` inside a double-quoted printf miscounts (it matched every line). Count CR bytes with `git show HEAD:<f> | tr -cd '\r' | wc -c`.
- A Codex cell's report that cites `work/<pkg>/...` inputs (gitignored, worktree-local) needs their durable copies under `clearwater-review-evidence\<pkg>\` named in the report before merge.
- Codex driver footers: depth read 165K -> 200K -> 49K across one resumed session (turn 3's figure fell); record the figure as reported, with its moment.

### Gen-35 lessons (carried)

- A window script that runs a tool by relative path (`tools/...`) must run with the PACKAGE worktree as cwd: `bash -c 'cd <worktree> && bash <script>'`.
- An NVENC encode fed slowly can hang inside NVENC (DR-115): diagnose with `Win32_Process` I/O counters sampled twice; end ONLY the encoder (your own child) so the product's failure path and D85 clean-up run; save the counters first.
- A window's length estimate in a brief can be badly wrong; post a corrected estimate to CHARC mid-window.
- Run the seat's own `bash -n` on every cell-written script and check it is byte-identical to its committed ledger block before saving it under the main tree's `work\`.
