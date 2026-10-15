# CHARC -- Current State (the read-me-FIRST pointer)

> **Convention (CHARC-authored harness-architecture).** This file is the SINGLE
> current-state pointer for the director (CHARC). It is **OVERWRITTEN each
> session** -- it always reflects only the live now, never accumulated history.
> Narrative lives in `git log -- docs/charc-state.md`. **The bootstrap reads THIS
> file FIRST**, then the charter. Every fact below carries the method that
> re-verifies it; a successor re-runs the method rather than inheriting the fact.

---

### Phase / state

Phase 0 of the implementation plan (`docs/clearwater-implementation-plan.md`
section 6). Second CHARC generation, `clearwater-charc-20261014-1257`, the first
launched through `scripts/launch_role.ps1` (fable/medium). Bootstrap steps 1-4 were
done by the first generation; this generation re-verified comms (CHARC-side
round-trip 2026-10-14T22:57Z, both hooks import clean) and executed step 5.
Repository local + mirrored to private GitHub `rwsmythe/clearwater` (verify:
`git -C C:\Users\rwsmy\clearwater remote -v`; `git status -sb`).

**Bash-launch gauge (bootstrap step 2):** 47 ms for one `bash-cc.exe -c true`
(2026-10-14; re-measure with PowerShell
`Measure-Command { & $env:CLAUDE_CODE_GIT_BASH_PATH -c true }`). Under the 1 s flag.

### Live workstreams

- **Orchestrator generation** `clearwater-orchestrator-20261014-1258` (opus/high/auto,
  owner-confirmed; verify: `comms/.launch-sessions.json`, `ListAgents`).
- **WP0.1 ACCEPTED** (main c09f747; `docs/proofs/wp0.1-accept.md`). **WP0.2 ACCEPTED**
  (main 4863a90; `docs/proofs/wp0.2-accept.md`); CHARC QA re-ran all gates green at
  2d9c381 (pytest skips the ffprobe tests in THIS session because its PATH predates
  the FFmpeg install; the orchestrator's 182-pass run is the figure of record).
  Phase 0 code is complete; the REAL inventory run waits for the footage download.
- **Real-inventory mechanical pass**: approved in principle (implementer-sonnet-medium,
  no code); dispatch ONLY on CHARC's word after the owner reports the download
  complete (a partial inventory would seed CP1 wrongly, DR-6).
- **WP1.1 commissioned** 2026-10-15 ~00:35Z (draft `docs/briefs/wp1.1-brief.md`; cell
  `implementer-opus-high`; gate tier STRONG; grants numpy + scipy dev group; new
  `tools/prototype/` package). **DISPATCHED 2026-10-15T00:32Z**: cell in
  `.worktrees/wp1.1` (branch `wp1.1`, base 46a10b9), Reviewer A STRONG; five brief
  decisions ruled accepted ~00:35Z (+ one informal 4K run in the return report).
  Verify: `git worktree list`, `docs/orchestrator-state.md`; that tree is OCCUPIED
  until the orchestrator records the cell's return.
  **Author return in 2026-10-15T01:40Z** (branch head a222301; Reviewer A converged r3
  0/0/4; Reviewer B dispatched; informal 4K run re-engaged). CHARC RULED 01:41Z
  (orchestrator inbox, msg ece409ee): Q1 W_L = |sigma^2 Lap(G_sigma L)| ACCEPTED as a
  spec-driven (6.6/D56) departure from [A18], recorded in the open-values report;
  Q2 -> DR-11, Q3 -> DR-12 (35c4e72). `weight_maps(both inputs)` deviation accepted
  (no frozen interface before WP1.4).
  **ACCEPTED 2026-10-15T02:24Z**: main 9711faf, record 2e09203; A converged r3, B
  NO_BLOCKING x3; informal 4K run 14 s / 26 s. CHARC QA at this seat: all gates green.
  Reviewer B calibration point -> DR-13. Worktrees removed; branch wp1.1 kept.
- **WP1.2 Part A commissioned 2026-10-15T02:31Z** (draft `docs/briefs/wp1.2-brief.md`,
  b5c0979; cell implementer-opus-high; STRONG; EXCLUSIVE). CHARC rulings: package split
  A (synthetic, now) / B (real footage + WP1.5 path, later; Gate 1 closes on B); GPU
  library CuPy first (`cupy-cuda12x`, MIT, dev group), PyTorch only on a routed STOP, no
  CUDA toolkit install (STOP to CHARC if needed); agreement tolerance 2e-5/2e-6. Expected
  STOPs: toolkit needed, missing cupyx counterpart, unattributable agreement gap, >8 GB
  VRAM at 5.3K. **DISPATCHED 2026-10-15T02:33Z**: brief FINAL 809c9b2 (+ d27f909 working
  rules), base d27f909, cell wp12-cell in `.worktrees/wp1.2` (branch wp1.2); Reviewer B
  ORDERED after the author. CHARC 02:34Z: `cupy-cuda12x[ctk]` (uv-managed nvidia-* wheels
  in .venv) is within the grant; anything outside .venv stays a STOP. The real inventory
  pass is QUEUED behind the exclusive window. Verify: `git worktree list`.
  **STOP 03:01Z, RULED 03:02Z** (msg 7acff64e): install needs `[ctk]` (cuda-toolkit meta
  + 8 nvidia-*-cu12 wheels, in .venv); CPU path bit-identical to WP1.1. F1: Option A --
  float32 GPU filters kept, tolerance asserted on textured images, near-flat pair kept at
  1e-4/1e-5 with the cause in the docstring; DR-14 (N{} ill-conditioned on low texture).
  F2: run.py defaults to cpu. `correct(..., backend=None)` and `normalisation_bounds()`
  accepted. EARLY GATE 1 SIGNAL (dev figures, not exclusive): GPU core ~0.40 s / 0.69 s
  per 4K frame vs 0.111 s budget (3-6x over before decode/encode); raise to the owner at
  WP1.6 with Part B (plan Gate 1 row: owner tunes target or approves optimisation).
  **Author returned 05:13Z** (head 9408d18; A converged r1; 17 gpu tests run; exclusive
  figures: GPU 4K 0.416 s / 0.723 s = 3.7x / 6.5x N6; 5.3K 0.907 / 1.807 s; CPU 11-58 s;
  pool peak 1.7 GB 4K / 3.3 GB 5.3K). Reviewer B BLOCKING on F1 only: GPU c3 cells 14-17%
  faster than the author's (power-mode overlay / GPU clocks not recorded); orchestrator
  routed back to the author (ambient record extended, GPU cells re-measured, B2). No CHARC
  ruling needed. STRAY PROCESS: PID 33616 `C:\Python314\python.exe -`, hung since
  2026-10-14 13:31 (WP0.1 Reviewer B orphan), one core; the orchestrator's classifier
  blocked stopping it; CHARC verified and surfaced to the owner (owner stops it).
- Debt register `docs/debt-register.md`: DR-1..DR-14 (DR-3, DR-4 closed).
- No authority granted by `SendMessage` this generation (cues only).

### Pending items

1. **Owner decision request 2026-10-14T23:45Z** (`comms/operator/inbox/...-c4281ff7.md`):
   spec text amendments recording the measured CPU/GPU (D117, section 12, 14.2, Q1).
   Recommended: approve as written; CHARC applies. Debt register DR-5. Unanswered.
2. **Owner to report the footage download complete** -> CHARC tells the orchestrator to
   dispatch the real-inventory pass -> CP1 (owner sorts categories; owner-reserved).
3. **Next harness acts:** QA the WP1.2 Part A accept when it lands; then WP1.5 (container
   spike) and WP1.2 Part B once the footage exists; WP1.3 and WP1.4 need CP1.
4. Main is ~66 commits ahead of `origin/main`, unpushed; the owner has not asked for a push.

### Standing delegation (owner, 2026-10-14, chat to CHARC, verbatim)

"intent is for this development to run as unattended as possible. orchestrator
will send you operator related questions. Answer for operator unless the question
truly requires my input." Standing, not day-scoped (it superseded the ~23:12Z
"today" ruling given to the orchestrator). Recorded in CLAUDE.md "Roles". CHARC
answers in the operator's stead; the plan section 3 owner-reserved list is the
only trigger for a `decision_request` (the orchestrator HOLDS that item, continues
the rest). Read every answer back to the owner in the turn's recap so they can
override.

### Behavioral pointers

- Port **8775** is Clearwater's comms-UI port (`scripts/comms_ui.py` DEFAULT_PORT);
  the sibling harnesses (`coa-chess`, `swing-trading`) default to 8765 and one of
  them is usually listening there. psmux session name derives from the repo
  basename: `clearwater`; claude session names mint `clearwater-<role>-<stamp>`
  (read the live name from `comms/.launch-sessions.json` before any cue).
- The harness core here is the coa-chess lineage of the template (singular inboxes
  for every role, two hooks, depth-printing prompt hook, psmux launcher,
  `cell_depth.py`), with the second-director role removed. Comms changes route
  through CHARC's architecture pass; keep the core stdlib-only (the harness suite
  enforces it: `uv run python -m unittest discover -s tests/harness`, 366 tests).
- Clearwater's application toolchain is uv + Python 3.12 (`uv sync`, then
  `uv run pytest` / `ruff` / `mypy`); the harness suite is NOT run by pytest
  (`norecursedirs` excludes `tests/harness`). FFmpeg is not installed yet (WP0.1).
- Review gate: `docs/review-gate-clearwater.md` (Codex via WSL, tiers `strong` for
  product code, `fast` for docs/tools); the orchestrator runs it, CHARC QAs the
  orchestrator's product at the phase audit.
- Owner-reserved decisions (plan section 3) go to the operator as
  `decision_request`; put the recommended option FIRST, read the owner's word
  back verbatim with its time, and end every turn with the open owner decisions.
- Roll this seat only after ~400K context at a boundary (charter 5.1); commit
  this file by pathspec first; the outgoing seat stops draining (peek only).
