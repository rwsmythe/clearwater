# Orchestrator -- Current State (the read-me-FIRST pointer)

> Overwritten each generation; history lives in `git log -- docs/orchestrator-state.md`.
> Every fact carries the method that re-verifies it.

### Generation

- **Generation 36** (session `clearwater-orchestrator-20261102-1050`) **LIVE since 2026-11-02 ~20:50Z**, picked up gen 35's state at `91d83a9e` (gen 35 rolled at ~380K at a clean gap). CHARC is **gen 13 `clearwater-charc-20261102-0046`**; re-verify both names in `comms/.launch-sessions.json` before every cue. Seat folder `work/orch-g36/` (gate.sh / watch.sh / watch2.sh / fill_gate.py copied from `work/orch-g35/`, sed `g35`->`g36`; next gen copies to `work/orch-g37/`). **`watch2.sh <run> <offset>`** reads only summary lines after line `<offset>` (the plain `watch.sh` exits at once on an OLD `end` line when a run id is reused across invocations). Bash gauge at bring-up: 26-38 ms.
- **Disk:** C: 93 GB free at 2026-11-03 05:51Z (after the prune) (WSL / VM virtual disks grow while mounted: CHARC `40eb646b`). `df -h /c` before every window, gate and footage run. STOP below 15 GB free; 25 GB before any window.
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
- **WP5.6 ACCEPTED** (main `ef31c68a`; record `docs/proofs/wp5.6-accept.md`). Codex lane, three turns; Reviewer A replaced per the brief (docs-only); Reviewer B Claude NO_NEW_CRITICAL_MAJOR; gate **p5b** on `1934bcbb` GREEN (P 6,597/1 515 s, S 1,261/11 2,046 s, F 7 1,569 s, harness 382; `clearwater-review-evidence\wp5.6\gate\`). CHARC acted on all five dispositions at `d156ed49` (DR-86 deferred to Phase 6, DR-116 opened, DR-25 (3) to WP-DR25, spec erratum).
- **PRUNE of Result 6 DONE** (owner "prune" 2026-11-03 ~03:20Z; record `docs/proofs/prune-2026-11-02.md`, main `c94326aa`): 112 cited items archived to `D:\clearwater-archive\` first (md5-verified, 10.32 GB); pytest temp root, 27 worktrees (branches kept) and the main `work/` candidates deleted; stages 3-4 run by the owner's hand (the auto-mode classifier refused them here). C: 53 -> 93 GB. Scripts `work/orch-g36/prune/` (reusable: `prune.py archive|delete|verified`). `work/` = keep list only.
- **CP5 tally of record** (2026-11-03 06:23Z, `.worktrees/wp5.3` @ `c935b869`): headline 111/115 = 96.5 %, halos 5, candidates 10/11, exit 0, identical to CHARC's preview; sheet md5 `71df4121...` unchanged; `clearwater-review-evidence\wp5.3\cp5\`. **CP5 / V2 PASS** (owner "Concur with your D65 recommendation"); DR-117 opened (halos, six items); **gate report FINAL, Phase 5 verification COMPLETE** (CHARC, main `05907a0e`).

**LIVE CELLS (Phase 5 close-out, CHARC commission 1c947c81 / FINAL briefs 717265c7; order WP5.8 + WP5.7 parallel, WP-DR25 between WP5.8 turns, WP5.5 LAST):**
1. **WP5.8 encoder watchdog** (Codex; worktree `.worktrees/wp5.8`; evidence `clearwater-review-evidence\wp5.8\`). Round 0 STOP -> CHARC ruled R1-R3 (`6f2a023a`: write+flush watched, watched close, flush witness, 36 MiB test sentinel). Turn 2 `5a957919` RED/GREEN (session `01a1a027...`, depth 202,018 of 475,000). Reviewer A r1 (Claude, `A1\`): NEW_CRITICAL_MAJOR (MAJOR: GetTickCount64 monotonic counts sleep -> suspend kills a healthy export). Turn 3 = FRESH Codex session, remediation per `cell\dispatch-3.md` (11 dispositions). Next: commit, Reviewer A r2, the report turn, Reviewer B, gate (parallel + serial; serial must carry test_app_export_worker / test_jobs_export_process).
2. **WP-DR25 staged run** (Codex; `.worktrees/wp-dr25`; evidence `...\wp-dr25\`). Round 0 STOP -> CHARC ruled (a)-(d) (`0f2d19c4`: both methods + staged-reach interiors under --long; start clamp). Turn 2 `71806c5e` RED/GREEN (session `01a1a02e...`, depth 176,708 of 475,000). Reviewer A r1 (Claude, `A1\`) running. Next: GPU runs AT MY SEAT (`uv run python tools/statistics_experiments.py extract --long` then `analyse --long`, outputs `work\wp-dr25\`), never beside WP5.7's batch or a gate; then report, B, gate (parallel + SERIAL + harness: test_footage_locator / test_prototype_temporal import the instrument; an importer run stalled once under GPU contention, passed with CUDA_VISIBLE_DEVICES=-1).
3. **WP5.7 halo investigation** (Claude Agent `wp57-cell`, implementer-opus-high; `.worktrees/wp5.7`; outputs `work\wp5.7\`; CP5 pack read in place; evidence `...\wp5.7\cell\dispatch-1.md`). PART 1 running (instrument, six reproductions, stage table) -> YIELD -> Reviewer A (Codex, `docs/codex-reviewer.md`) round 0 -> Part 2 -> Part 3 whole-set batch (~1 h, GPU, machine cleared). Read cell_depth.py at every yield. A Claude subagent dies with this pane: at rollover re-dispatch from its ledger `docs/proofs/wp5.7-ledger.md`.
4. **WP5.5 release prep** (Codex) after all three merge. **WP-H1** cell_depth.py second pass: DRAFT brief on main, HELD by CHARC.

**Mail:** inbox drained through 06:58Z (`work/orch-g36/drain-*.txt`; posts `work/orch-g36/*.md`). No query open with CHARC.

**Kept worktrees:** `wp5.3` (KEEP: CP5 pack is evidence of record until WP5.7 reproduces the halo items) and `orch-state-g36` (mine). All other worktrees were removed by the prune; their branches remain.

### Gen-36 lessons

- **A fresh worktree has no `work/`**: pytest's basetemp under `work/` fails at once (`INTERNALERROR ... WinError 3`). `work/orch-g36/gate.sh` now runs `mkdir -p work` after its `cd`.
- **`TaskStop` on a backgrounded `gate.sh` kills only the outer shell**: the script's bash and its pytest children keep going (the stopped run went on into serial, then fullclip). End the tree with PowerShell `taskkill /PID <gate.sh bash pid> /T /F` after finding it with `Get-CimInstance Win32_Process | ? CommandLine -match 'gate.sh|pytest.exe'`; confirm nothing is left before re-running.
- A CR check written as `"... $(git show ... | grep -c $'\r')"` inside a double-quoted printf miscounts (it matched every line). Count CR bytes with `git show HEAD:<f> | tr -cd '\r' | wc -c`.
- A Codex cell's report that cites `work/<pkg>/...` inputs (gitignored, worktree-local) needs their durable copies under `clearwater-review-evidence\<pkg>\` named in the report before merge.
- Codex driver footers: depth read 165K -> 200K -> 49K across one resumed session (turn 3's figure fell); record the figure as reported, with its moment.

- **The auto-mode classifier refuses bulk deletion under the main tree's `work/`** (as on 2026-10-29) even with the owner's prune word, while it allowed the pytest temp root and released worktrees' `work/`. Do not work around it: stage the deletion in a guarded script and give the owner the `! bash <script>` line to run in this session.
- **Archive with a citation scan** (`work/orch-g36/prune/cite_scan.py`): archive every item a tracked record names, delete the rest; a destination already holding an earlier archive (the WP3.21 oracle) shows as extras -- check set-equality against the old manifest, then mark the verify reviewed.

### Gen-35 lessons (carried)

- A window script that runs a tool by relative path (`tools/...`) must run with the PACKAGE worktree as cwd: `bash -c 'cd <worktree> && bash <script>'`.
- An NVENC encode fed slowly can hang inside NVENC (DR-115): diagnose with `Win32_Process` I/O counters sampled twice; end ONLY the encoder (your own child) so the product's failure path and D85 clean-up run; save the counters first.
- A window's length estimate in a brief can be badly wrong; post a corrected estimate to CHARC mid-window.
- Run the seat's own `bash -n` on every cell-written script and check it is byte-identical to its committed ledger block before saving it under the main tree's `work\`.
