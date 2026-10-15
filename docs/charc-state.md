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
  (no frozen interface before WP1.4). Awaiting the accept report.
- Debt register `docs/debt-register.md`: DR-1..DR-12 (DR-3, DR-4 closed).
- No authority granted by `SendMessage` this generation (cues only).

### Pending items

1. **Owner decision request 2026-10-14T23:45Z** (`comms/operator/inbox/...-c4281ff7.md`):
   spec text amendments recording the measured CPU/GPU (D117, section 12, 14.2, Q1).
   Recommended: approve as written; CHARC applies. Debt register DR-5. Unanswered.
2. **Owner to report the footage download complete** -> CHARC tells the orchestrator to
   dispatch the real-inventory pass -> CP1 (owner sorts categories; owner-reserved).
3. **Next harness acts:** QA the WP1.1 accept; then commission WP1.2 (CPU/GPU variant;
   `gpu`, exclusive; the GPU-library ruling is CHARC's at that brief) and WP1.5
   (container spike; needs footage). WP1.3 and WP1.4 need CP1.
4. Main is ~58 commits ahead of `origin/main`, unpushed; the owner has not asked for a push.

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
