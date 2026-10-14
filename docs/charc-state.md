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

- **Orchestrator generation launched** 2026-10-14T22:58Z as
  `clearwater-orchestrator-20261014-1258` (opus/high/auto, psmux vehicle; verify:
  `comms/.launch-sessions.json` orchestrator entry; `ListAgents`). Post-step-5
  round-trip VERIFIED 2026-10-14T23:00Z: ping drained to
  `comms/orchestrator/read/...-b4120977.md`, ack in `comms/charc/read/...-66a8d529.md`
  (HEAD b7fa4c8, harness gate 366 OK on its side).
- **WP0.1 commissioned** to the orchestrator 2026-10-14 ~23:03Z (type status, subject
  "Commission WP0.1 ..."): final brief + dispatch are the orchestrator's; cell
  `implementer-sonnet-high`; base b7fa4c8; tripwire pass done in the brief (two
  dev-group deps). Accept report expected `--to charc`. Verify progress:
  `git worktree list`, `docs/orchestrator-state.md`.
- No cell, no worktree (verify: `git worktree list`).
- No authority granted by `SendMessage` this generation; the only cue sent was
  the content-free post-cue to the orchestrator.

### Pending items

1. **Owner decision request posted 2026-10-14T22:59Z** (`comms/operator/inbox/
   ...-0a0cc8c4.md`): (a) confirm orchestrator opus/high/auto and the three cell
   tiers (recommended: keep as is); (b) the footage path (read-only) and the
   working folder path. Unanswered until the owner's word is read back verbatim
   with its time. Do not guess the paths.
2. **Next harness act:** QA the orchestrator's WP0.1 accept when it lands (CHARC
   QAs the orchestrator's product: accept record, ledger, gate assertions, the
   claim list against the brief). Then commission WP0.2 (footage inventory; needs
   the footage path), then checkpoint CP1.
3. Doc nits for a later kernel-doc pass (touches the harness gate; run it then):
   `docs/charc-bootstrap.md` bring-up block still says "no co-author footer" while
   `docs/dispatch-recipe.md` (2026-09-02) requires the footer and every commit on
   main carries it; `role_mail.py` has no `dispatch` type -- commissions go as
   `status` (valid: fyi|status|query|return_report|decision_request).

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
