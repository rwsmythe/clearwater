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

### Live board (RESUME HERE) -- 2026-11-03 ~13:55Z

1. **WP-DR25** (Codex; `.worktrees/wp-dr25`, branch `wp-dr25`; evidence `C:\Users\rwsmy\clearwater-review-evidence\wp-dr25\`). Final candidate **`82b6eae2`** (rebased onto main `6393cb35`; turns 6 report `83ad9d69`, 7 B remediation `d5650ea8`, 8 report section 9 `82b6eae2`; session `01a1a157-6f2b-7391-9242-5fa191ebfca1`, depth 185,072 of 258,400 at turn-8 end). Reviewer A CONVERGED r2. **Reviewer B** (`...\B\`, on `83ad9d69`): NEW_CRITICAL_MAJOR_FOUND, F1 MAJOR = a test pinned pre-rebase commit `6dfccdfc` (unreachable after MY rebase) -> the single remediation pinned the revision-loaded modules by BLOB id (`5bada347...` pre-R1, `74019b47...` base); **B re-run** (`...\B\r2\`, on `d5650ea8`): **NO_NEW_CRITICAL_MAJOR** (all figures re-verified from `runs2\`; 14/14 mutants killed); its F1 MINOR (stale report section 9) fixed in turn 8 (report section 9 only); F2 advisory: merge must be FAST-FORWARD (blob `5bada347` is reachable only through the branch history); F3 advisory as ruled. My own QA: the four ground-2 per cents and the common-slice control reproduce from `runs2\` (c3 23.24 / 10.23 %; ancuti 13.52 / 8.07 %). **GATE `pdr25` RUNNING** on `82b6eae2` (static + collect + parallel + serial + harness; summary `work/orch-g38/gate-pdr25/summary.txt`): static clean (312 formatted, mypy 156 files), collect 7,915 = 6,636 + 1,272 + 7 identity holds, **parallel 6,635 passed / 1 skipped EXIT 0 525 s**; serial started ~13:50Z (GATE_CHECKS: the importers `tests/test_footage_locator.py`, `tests/test_prototype_temporal.py` green by name in the junits). NEXT: harness, copy junits to `...\wp-dr25\gate\`, accept record `docs/proofs/wp-dr25-accept.md` (form `docs/proofs/wp5.8-accept.md`), ff-merge, then CHARC rules DR-25 (3), AD-3 and the WP1.4 erratum pointer.
2. **WP5.7** (Claude lane; `.worktrees/wp5.7`, head `94416785`; evidence `...\wp5.7\`; outputs `C:\Users\rwsmy\clearwater\work\wp5.7\`). Video batch DONE at my seat (12:17-13:40Z, 36/36 exit 0, 64 -> 60 GB). **Part 2 RETURNED** by `wp57-cell5` (dispatch `cell\dispatch-7.md`; depth 207,413 at return, read twice; ledger `5ecefea1`, my depth fill + featured-frame ruling `94416785`; the cell is DONE, treat as stood down). Result: no STOP; every band attributed input 2; **(d) unsharpened clears 3/3 photo and 30/31 video decided bands** (residual 0.15 x C), whole-image change photo mean abs 0.032-0.060, video 0.014-0.024, flicker 1.02 / 1.11, render cost untimed; parameter candidates leave 1/3 photo and 10-13/31 video; (e2)/(d) change cached statistics without a hash change. Posted to CHARC 13:51Z (body `work/orch-g38/wp57-p2-return.md`). NEXT: **Reviewer A round 4 (Codex, read-only)** with prompt `...\wp5.7\A\r4\review-prompt.md` + `review-diff.txt` (built: `git diff 1bd99a4e..HEAD -- tools tests`) -- START ONLY AFTER the pdr25 serial leg ends; then CHARC's candidate ruling (any default / algorithm change = owner decision through CHARC); Part 3 whole-set batch (~1 h GPU, alone) per the ruling.
3. **WP5.5** release prep (Codex) after WP-DR25 and WP5.7 merge (brief FINAL; tag `v1.0.0` on the owner's word, no push). **WP-H1** HELD by CHARC until WP5.5's accept.
- Mail: drained through 12:18Z (`work/orch-g38/drain-1.txt`). No query open.
- Kept worktrees: `wp5.3` (CP5 pack evidence), `wp5.7`, `wp5.8` (owner's word to prune), `wp-dr25`, `orch-state-g38` (mine).

### Gen-38 lessons

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
