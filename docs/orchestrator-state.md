# Orchestrator -- Current State (the read-me-FIRST pointer)

> Overwritten each generation; history lives in `git log -- docs/orchestrator-state.md`.
> Every fact carries the method that re-verifies it.

### Generation

- **Generation 32** (session `clearwater-orchestrator-20261101-0959`; CHARC gen 11 `clearwater-charc-20261101-0727`; re-verify both in `comms/.launch-sessions.json`). Brought up 2026-11-01 19:59Z (bash gauge 37 ms). LIVE (mid-generation checkpoint, written 23:20Z).
- **Disk:** C: 163 GB free at 23:14Z. `df -h /c` before every window, gate and footage run. STOP below 15 GB free (25 GB before any WP5.3 `clips` piece).
- **Paces at 22:01Z:** Claude **92.0 %** = THE LINE: no Claude pass of any kind starts before the 2026-11-02 10:00Z reset; Codex 15 % / 0.238.

### BINDING RULES CARRIED (each verbatim in `comms/orchestrator/read/`)

- **92 % rule (CHARC `e4282d85`):** NO Claude pass STARTS at >= 92 %; Codex turns and WP5.3 run requests continue. NEVER lower the reviewer tier.
- **NO PYTEST DURING A SERIAL OR FULLCLIP LEG** (Codex light suites and Claude passes included); no WP5.3 build piece beside any gate leg or window; one heavy job at a time. Codex light runs (non-slow) beside a build piece are allowed.
- **Gates carry WP-T7's flags** and the STALL WATCH. Scripts: `work/orch-g32/gate.sh <worktree> <run-id> <legs...>` (legs `static collect parallel serial fullclip harness`) + Monitor `bash work/orch-g32/watch.sh <run-id>` (30 min cap; re-arm). Junit report fill: `work/orch-g32/fill_gate.py <report> <label> P=<xml> S=<xml> F=<xml>`.
- **Codex turns:** `uv run python scripts/codex_cell.py turn --worktree <ABS> --prompt <p> --evidence <dir> --turn N [--session <id>] > <dir>\turn-N.driver.stdout 2>&1` (run_in_background); commit with `codex_cell.py commit --worktree <ABS> --return-file <return-N.md>`; blob-check 0 CR; `ruff format --check` at the seat. FRESH session prompt = `.claude/agents/implementer-codex-sol-high.md` + the brief at HEAD + `dispatch-N.md`.
- **Rulings folded** with `fold_any.py` (gen-31 scratchpad path in git history of this file); pass the heading WITH its `## `.
- **Worktree release:** a released worktree's `work/` is pruned only on the owner's word; copy its junits to `clearwater-review-evidence\<pkg>\gate\` first.

### Live board (RESUME HERE)

**DONE this generation:** WP3.6P ACCEPTED (`f1733802`); WP5.1 ACCEPTED (`0e8f0e00`; junits copied to evidence `wp5.1\gate\`); both confirmed by CHARC (rows `0785e0a7`, `5af18d9d`). Owner prune ran (CHARC, `f5af9d95`): wp-t7, wp3.6p, wp4.6 worktrees removed.

**1. WP5.3 (Codex; CP5 review pack).** Head **`0b04e372`** (session 6 `01a1995b-0d16-75e1-a8fc-45fff4e2eac4` at 81,940). Run requests from the worktree root (`( cd .worktrees/wp5.3 && uv run python -m tools.reviewpack.build <piece> )`; receipts `work/orch-g32/wp53-runs/summary.txt` + per-piece logs): photos EXIT 0 (73 done), presets EXIT 0, `page` EXIT 2 (pending, by design) then `page --check` EXIT 0 (NOTE: `page --check` ALONE only checks an existing page), tally 0/0; **clips V-P EXIT 1: 8 done, 9 PRODUCT refusals (DR-112)**; **clips V-S RUNNING since 23:03:35Z**. Next: V-D, V-Z, V-R (25 GB floor), `page`, `page --check`, tally; a Codex read-back turn after each piece (session 6; non-slow light runs only while a piece runs); the report turn; the two-leg gate (B-F4: time the two preset nodes under `-n 4`); the accept may land with the 9 V-P rows loud (CHARC). **CP5 pack goes to the owner only at pending 0 AND failed 0** = after WP-D112 merges and `clips V-P` is re-run (witness), then `page`, `page --check`, tally.

**2. WP-D112 (Codex; product fix for DR-112).** Brief FINAL `docs/briefs/wp-d112-brief.md` (worktree `.worktrees/wp-d112`, head `7d48e26a`; CHARC fold `4bff0b93`). The seat experiment (outcome A: samples byte-identical, the check is wrong for raw PCM; no `encode.py` change) is in the brief; probe files `work/orch-g32/pcm/` (the `sitecustomize` hook there is seat-only, never committed). **Turn 1 (round 0) RUNNING** in a FRESH session (dispatch `clearwater-review-evidence\wp-d112\cell\dispatch-1.md`). Then RED (turn 2), GREEN + fixture (turn 3), Reviewer A after 10:00Z, B, the two-leg gate, accept, then WP5.3's V-P re-run.

**3. WP5.2** after CP5 opens (CHARC drafts; carries the 5d estimate figure 6.13 vs 4.11 GB).

**Mail:** inbox drained 23:14Z (`work/orch-g32/drain-*.txt`; posts `work/orch-g32/*.md`). No query open with CHARC. Last post: WP-D112 experiment + draft (23:12Z, `ef9b4ee7`).

**Kept worktrees:** `wp5.3`, `wp-d112` (LIVE); `wp5.1` (released; junits copied; owner prune); `orch-state-g32`; older `brief-*`, `orch-state-g21..g31`.

### Standing operator rulings

- **Unattended operation** (owner, 2026-10-14; CLAUDE.md "Roles"): every operator-bound question goes `--to charc` (type query, recommended answer first, one cross-session cue after posting). No AskUserQuestion from this seat.
- **GoPro IMU and GPS are OUT OF SCOPE**; nothing from `gpmd`, IMU or GPS is ever committed.
- **Cell depth:** Claude cells via `scripts/cell_depth.py`; ~250K evaluate, ~400K STOP. Codex: footer `depth_input_tokens`; evaluate ~200K, STOP near 250K.
- **Kernel hazard (7):** never an uncommitted edit in the MAIN tree; edits in a worktree branch, then `git merge --ff-only`.
- **Line endings:** every committed blob LF; 0 CR per file at every gate.
- **DR-99** (CHARC `fbbab0bf`): the bench test's `telemetry_origin` failure alone on main is recorded under DR-99 without a STOP; any OTHER serial failure is a STOP.
