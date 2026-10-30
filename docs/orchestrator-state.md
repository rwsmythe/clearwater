# Orchestrator -- Current State (the read-me-FIRST pointer)

> Overwritten each generation; history lives in `git log -- docs/orchestrator-state.md`.
> Every fact carries the method that re-verifies it.

### Generation

- **Generation 26** (session `clearwater-orchestrator-20261029-1612`; CHARC gen 9 `clearwater-charc-20261029-1554`; re-verify in `comms/.launch-sessions.json`). Bash gauge at bring-up: 24 ms. **ROLLED OVER 2026-10-30 ~04:35Z at ~405K at a CLEAN boundary: WP4.3 accepted, no cell live, no Codex turn, no gate or window running.**
- **Disk:** C: 172 GB free at the last check (D: 2.3 TB). `df -h /c` before every window, gate and footage run; STOP below 15 GB free (20 GB for WP3.6P). A V7 (f) plant costs 19.96 GB (not sparse).
- The owner deleted the three kept basetemps (main `07c0f5a`): that owner action is DONE.

#### Done by gen 26

- **WP-DR87 ACCEPTED at main `f78e92c`** (record `docs/proofs/wp-dr87-accept.md`). DR-87 node 90.93 -> 25.24 s. A R1 and B (both Claude) clean. Gate `dr87g1`: one PRE-EXISTING serial failure, `tests/test_io_video_encode_bench.py::test_run_once_records_the_row_and_deletes_the_output` (`telemetry_origin` -0.066 / -0.104 / -0.092 s; fails alone on main too) = **DR-99** (CHARC `fbbab0bf`: at later gates, record it under DR-99 WITHOUT a STOP if it fails the same way AND alone on main; any OTHER serial failure is a STOP). CHARC owes its rows (DR-87/93/94 closed, DR-99 new) and QA. Worktrees `wp-dr87`, `wp-dr87-mc` kept until CHARC's QA.
- **WP4.3:** cell 11 (report, retired 138,331), Reviewer B (1/10/4; B-1 REJECTED BY RULING `775d0148`), cell 12 (cleanup, 133,481), narrow B re-run (0/0/4/2 clean), cell 13 (five fixes, 98,187; no third B, `b0d679b0`). **WP4.3 ACCEPTED at main `28c4a75`** (record `docs/proofs/wp4.3-accept.md`; gate `wp43g1` GREEN: parallel 6,043 / 1 skip, serial 1,207 / 11 skips / 0 failed; logs `clearwater-review-evidence\wp4.3\gate\`). CHARC owes its accept-side rows (the consolidated list in the release post and the record) and QA.

#### Live work at write (RESUME HERE, gen 27)

Nothing is live: no cell, Codex session, gate or window.

**NEXT (gen 27), in order:**
1. Drain the inbox: CHARC's WP4.3 QA and rows. On its QA CONFIRMED, remove the worktrees `wp4.3`, `wp4.3-mc` and `wp4.3-rev` (copy any `work/` logs you need first; branches kept).
2. **WP3.6P** (Codex lane, the brief FINAL). Read `docs/briefs/wp3.6p-brief.md` and its rulings. Read both paces. Dispatch a FRESH Codex session through `scripts/codex_cell.py turn` (`--worktree` as an ABSOLUTE path), with prompts in `clearwater-review-evidence\wp3.6p\cell\prompt-N.md` and the WP-DR87 turn prompts as the form. Its export and memory legs are EXCLUSIVE windows (OPEN/CLOSE to CHARC; >= 20 GB free). Both nets are the Claude pass (B by hand if the report must be excluded, see below).
3. **WP4.6** (Claude `implementer-opus-high`, design scope; nets Codex). Ask CHARC for the brief's FINAL first; it is DRAFT on main. It may run beside WP3.6P (one heavy job at a time on the host).


**Queued (after WP4.3's accept):**
- **WP3.6P** (Codex lane; brief FINAL `docs/briefs/wp3.6p-brief.md` at `afd83c6`, CHARC `056fb449`). Its export and memory legs need EXCLUSIVE windows (OPEN/CLOSE to CHARC; >= 20 GB free).
- **WP4.6 export process isolation** (Claude `implementer-opus-high`, design scope; Reviewer A and B Codex). CHARC's brief `docs/briefs/wp4.6-brief.md` is still DRAFT: ask CHARC for FINAL before dispatch.
- Paces at 03:12Z: Codex 0.368, Claude 1.45 (`scripts/usage_codex.py`, `scripts/usage_claude.py`). The owner's lane rule: lean on Codex where task fit allows; report the share at each commission.

**Kept worktrees:** `wp4.3` (author branch), `wp4.3-mc` (the candidate), `wp4.3-rev`, `wp-dr87`, `wp-dr87-mc`, `brief-wp4.4`, `brief-dr87`, `brief-wp3.6p`, `orch-state-g21..g26`. Remove the WP-DR87 and WP4.3 ones after CHARC's QA confirms (branches kept).

**Gen-26 practice and slips:**
- Bare-`cd` slips: three (into `wp-dr87`, `wp4.3-mc`, and a leading `cd` into the evidence folder); one happened with cell 11 live (I warned it, and it confirmed absolute paths throughout). EVERY worktree command goes in a `( cd <wt> && ... )` subshell or uses `git -C`; for `uv` from another directory, use `uv --directory <repo> run ...`.
- B prompt slip: WP4.3's B prompt omitted the brief's Q3 ruling from "Accepted by ruling", and B's major landed exactly there. Every B prompt's "Accepted by ruling" list must carry every brief ruling that fixes a behaviour B could flag (the owner-reserved ones above all).
- `codex_cell.py review` builds its diff excluding only `docs/proofs` and `uv.lock`. For a Reviewer B that must not see the author's report, run the same pass by hand: `clearwater-review-evidence\wp-dr87\reviewB\run_review_B.py` (imports `codex_cell`, adds `:!docs/reports/<report>`).
- A first `git rebase` in a fresh worktree can refuse with "unstaged changes" on a clean status (a stat refresh): run `git status` and retry.
- Reviewer B ran in parallel with a cell's report-only turn (B's diff withheld the report and the ledger, so the tree B saw = the code merged). That saved a full B cycle.
- A Codex cell's tests and a Claude cell's light runs beside a serial gate leg can flake timing nodes. Re-run a failed node ALONE, and on main, before classifying it.

### Standing operator rulings

- **Unattended operation** (owner, 2026-10-14; CLAUDE.md "Roles"): every operator-bound question goes `--to
  charc` (type query, recommended answer first, one cross-session cue after posting). CHARC answers in the
  operator's stead except plan s.3 owner-reserved items. Info-updates (`--type fyi`) to the operator after each
  accept. No AskUserQuestion from this seat.
- **RESUMED 2026-10-26** at the owner's word ("resume", relayed by CHARC `064e23c84876bdfd`) after the 2026-10-21 pause.
- **Owner word 2026-10-20:** spec **v0.5.4**, plan v1.2, architecture FINAL 1.0, interim N6 = 25 min/min (D106),
  gain caps KEPT (D100). Owner-pending list (CHARC carries it): photos (WP3.6P), an iPhone clip (DR-15's B-frame
  leg), the V3 ratio figures as information for CP5/WP4.2 (now also in the WP3.11 record).
- **GoPro IMU and GPS are OUT OF SCOPE**: nothing from a `gpmd` track, IMU or GPS is ever COMMITTED (the owner's rule;
  CHARC `b238bd27`: a byte hash in an uncommitted `work\` record is within it, kept out of evidence copies too); no product
  module decodes or parses `gpmd`; GPMF settings only from `moov/udta` (FMWR/PRTN/PTCL). Location tags never reach a
  committed record (WP3.10 R1 #2).
- **Cell depth:** read `uv run python scripts/cell_depth.py <cell>` at dispatch, every yield, before any ruling;
  ~250K evaluation, ~400K STOP. Opus cells re-grounding from a ledger with a TIGHT reading list started at 0 and
  reached 90-120K by their first yield this generation (much less than wave 3's 140-220K).
- **Kernel hazard (7)** (CHARC, 2026-10-21): never an uncommitted edit in the MAIN tree's working copy. Every edit --
  briefs, state, records, contract amendments -- in a worktree on its own branch, then `git merge --ff-only`.
- **Line endings (CHARC, 2026-10-26: "keep that blob check in the gate recipe for every accept"):** every committed
  blob is LF (main has 0 CR bytes everywhere, the debt register included). At every gate: for each file in
  `git diff --name-only <base>..<cand>`, `git cat-file -p <cand>:<f> | tr -cd '\r' | wc -c` must be 0.
