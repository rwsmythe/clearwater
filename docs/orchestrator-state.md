# Orchestrator -- Current State (the read-me-FIRST pointer)

> Overwritten each generation; history lives in `git log -- docs/orchestrator-state.md`.
> Every fact carries the method that re-verifies it.

### Generation

- **Generation 32** (session `clearwater-orchestrator-20261101-0959`; CHARC gen 11 `clearwater-charc-20261101-0727`; re-verify both in `comms/.launch-sessions.json`). Brought up 2026-11-01 19:59Z (bash gauge 37 ms). LIVE (this is a mid-generation checkpoint, written 21:05Z).
- **Disk:** C: 161 GB free at 20:58Z. `df -h /c` before every window, gate and footage run. STOP below 15 GB free (25 GB before any WP5.3 `clips` piece).
- **Paces at 20:42Z:** Claude **91.0 %** / pace 0.988 (resets 2026-11-02 10:00Z); Codex 15 % / 0.238.

### BINDING RULES CARRIED (each verbatim in `comms/orchestrator/read/`)

- **92 % rule (CHARC `e4282d85`, until the 2026-11-02 10:00Z reset):** NO Claude pass STARTS once `uv run python scripts/usage_claude.py` reads >= 92 %; Codex turns continue. NEVER lower the reviewer tier.
- **NO PYTEST DURING A SERIAL OR FULLCLIP LEG** (Codex light suites and Claude review passes included), and no WP5.3 build piece beside any gate leg or window. One heavy job at a time.
- **Gates carry WP-T7's flags** (`--timeout 600 / 1200 / 2400`, `> log 2>&1`) and the STALL WATCH as GATE_CHECKS defines it. Scripts: `work/orch-g32/gate.sh <worktree> <run-id> <legs...>` (legs `static collect parallel serial fullclip harness`; summary `work/orch-g32/gate-<run>/summary.txt`) + Monitor `bash work/orch-g32/watch.sh <run-id>` (30 min cap; re-arm).
- **Codex turns:** `uv run python scripts/codex_cell.py turn --worktree <ABS> --prompt <p> --evidence <dir> --turn N [--session <id>] > <dir>\turn-N.driver.stdout 2>&1` (run_in_background); commit with `codex_cell.py commit --worktree <ABS> --return-file <return-N.md>`; blob-check 0 CR; `ruff format --check` at the seat. A FRESH session's prompt = `.claude/agents/implementer-codex-sol-high.md` + the brief at HEAD + `dispatch-N.md`.
- **Release of worktrees:** a released worktree with a gitignored `work/` (gate basetemps) is NOT removed by this seat: `work/` is pruned only on the owner's word (`wp-t7` 1.8 GB, `wp3.6p`, `wp-d54/work` wait for the owner's prune).

### Live board (RESUME HERE)

**DONE this generation:** **WP3.6P ACCEPTED** (main `f1733802`; record `docs/proofs/wp3.6p-accept.md`; gate parallel 6,255/1 481 s, serial ALONE 1,231/11 1,823 s; CHARC confirmed `79a4f1c7`, rows on `0785e0a7`). WP5.3 Reviewer B asserted (NO_NEW_CRITICAL_MAJOR, executed); its remediation turns 11-12 committed.

**1. WP5.1 (Codex; acceptance suite). GATE IN PROGRESS** on `232e4af5` (rebased onto `f1733802`, 19 patch ids identical, `.venv` synced): static clean, collection 7,543 = 6,271 + 1,265 + 7, PARALLEL 6,270/1 (491 s, `work/orch-g32/gate-w51/`); **SERIAL ALONE running since 20:58:26Z** (`gate-w51s/`); then FULLCLIP ALONE (`gate.sh wp5.1 w51f fullclip`, ~26 min). Then the accept commit fills the report's 74 `(gate)` cells: `uv run python work/orch-g32/fill_gate.py .worktrees/wp5.1/docs/reports/wp5.1-acceptance.md g32-w51 P=.worktrees/wp5.1/work/g32-w51-parallel.xml S=.worktrees/wp5.1/work/g32-w51s-serial.xml F=.worktrees/wp5.1/work/g32-w51f-fullclip.xml` (lists NOT-PASS / UNMATCHED rows). CHARC's accept-side items: plan section 7 completion pointer, AD-11 NOTE (post-encode 3.5/255), AD-30 NOTE, the serial-leg delta, G2 creation-time Limit if undocumented.

**2. WP5.3 (Codex; CP5 review pack).** Head **`6d470028`** (session 5 `01a198d8-7f1b-7b73-a517-22d109cd3dab` at 159,243). B-F1 fixed per CHARC `79a4f1c7` (conflicts on the page with both outputs; no numbered output deleted). MY RULING (posted to CHARC `9dcebe1d`): the failed-excerpt clean-up at `build.py:724` is EXEMPT (fresh name from `_fresh()` in the same call); the NEXT turn adds one assertion that an EARLIER excerpt survives a failed re-run. NEXT: the RUN REQUESTs from the worktree root (`( cd .worktrees/wp5.3 && uv run python -m tools.reviewpack.build <piece> )`, ledger lines 290-310): photos (~1 h GPU), presets, page --check, clips V-P, V-S, V-D, V-Z, V-R, page --check, tally; outputs under the MAIN tree's `work/wp5.3/`; 25 GB free before each clips piece; never beside a gate leg; after each piece a Codex read-back turn per the brief's yields. Then the report turn, the two-leg gate (B-F4: time the two preset nodes under `-n 4`), the accept, the pack + sheet to the OWNER for CP5 (via CHARC).

**3. WP5.2** after the danglers (CHARC; carry the 5d estimate figure 6.13 vs 4.11 GB into its brief).

**Mail:** inbox drained 20:52Z (`work/orch-g32/drain-*.txt`; posts `work/orch-g32/*.md`). No query open with CHARC. Last post: WP5.3 turns 11-12 + ruling (20:59Z, `9dcebe1d`).

**Kept worktrees:** `wp5.3`, `wp5.1` (LIVE); `wp3.6p`, `wp-t7` (released, owner prune); `wp4.6` (releasable; copy its gate logs first); `orch-state-g32`; older `brief-*`, `orch-state-g21..g31`.

### Standing operator rulings

- **Unattended operation** (owner, 2026-10-14; CLAUDE.md "Roles"): every operator-bound question goes `--to charc` (type query, recommended answer first, one cross-session cue after posting). No AskUserQuestion from this seat.
- **GoPro IMU and GPS are OUT OF SCOPE**; nothing from `gpmd`, IMU or GPS is ever committed.
- **Cell depth:** Claude cells via `scripts/cell_depth.py`; ~250K evaluate, ~400K STOP. Codex: footer `depth_input_tokens`; evaluate ~200K, STOP near 250K.
- **Kernel hazard (7):** never an uncommitted edit in the MAIN tree; edits in a worktree branch, then `git merge --ff-only`.
- **Line endings:** every committed blob LF; 0 CR per file at every gate.
- **DR-99** (CHARC `fbbab0bf`): the bench test's `telemetry_origin` failure alone on main is recorded under DR-99 without a STOP; any OTHER serial failure is a STOP.
