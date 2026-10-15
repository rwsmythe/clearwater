# CHARC -- Current State (the read-me-FIRST pointer)

> **Convention (CHARC-authored harness-architecture).** This file is the SINGLE
> current-state pointer for the director (CHARC). It is **OVERWRITTEN each
> session** -- it always reflects only the live now, never accumulated history.
> Narrative lives in `git log -- docs/charc-state.md`. **The bootstrap reads THIS
> file FIRST**, then the charter. Every fact below carries the method that
> re-verifies it; a successor re-runs the method rather than inheriting the fact.

---

### Phase / state

Phase 1 (prototype gate) of the implementation plan
(`docs/clearwater-implementation-plan.md` section 6). Second CHARC generation,
`clearwater-charc-20261014-1303` (fable/medium, launched through
`scripts/launch_role.ps1`). Bootstrap steps 1-5 done. Repository local + mirrored to
private GitHub `rwsmythe/clearwater`; main is ~150 commits ahead of `origin/main`,
unpushed, and the owner has not asked for a push (verify: `git status -sb`).

**Bash-launch gauge (bootstrap step 2):** 47 ms for one `bash-cc.exe -c true`
(2026-10-14; re-measure with PowerShell
`Measure-Command { & $env:CLAUDE_CODE_GIT_BASH_PATH -c true }`). Under the 1 s flag.

### Accepted (all on main; records in `docs/proofs/`)

| WP | Main | Record | Note |
|---|---|---|---|
| WP0.1 | c09f747 | wp0.1-accept.md | local config, env report, FFmpeg dev tools |
| WP0.2 | 4863a90 | wp0.2-accept.md | `tools/inventory.py` |
| WP1.1 | 9711faf | wp1.1-accept.md (2e09203) | reference pipeline `tools/prototype/`; W_L ruling; DR-11..13 |
| WP1.2A | f6d998a | wp1.2-accept.md (7048fd7) | CuPy backend + `bench.py`; synthetic GPU 4K 0.389/0.652 s (3.5x/5.9x N6); DR-14 |
| WP1.5 | 3242679 | wp1.5-accept.md (371f19d) | container spike: SIMPLE; MANDATORY+REQUIRED 0 DIFFERENT, 8 best-effort lost; NVENC/libx265 8/10-bit proven; HERO13 HEVC 8-bit BT.709 FULL range; no .LRV (D60 open); DR-15..17 |

CHARC QA at this seat re-ran ruff/format/mypy/pytest green on every accept (pytest
skips the ffprobe tests here because this seat's PATH lacks ffprobe; the
orchestrator's 398-pass run is the figure of record). Spec at v0.5.2 (D60 closed 2026-10-15,
owner-approved; v0.5.1 073ca1f). Debt register `docs/debt-register.md`: DR-1, DR-2, DR-6..DR-17 OPEN;
DR-3, DR-4, DR-5 CLOSED; DR-18 ordered 2026-10-15T09:5xZ (WP1.5 B pass-2 minors,
owner WP3.10) -- verify it landed.

### Reviewer B form (owner catch 2026-10-15 07:25Z)

Reviewer B is ONE Codex pass the ORCHESTRATOR runs at its own seat on the merge
candidate, never an implementer cell (`docs/review-gate-clearwater.md` Part 2 item 2,
corrected at 30483f2; memory `clearwater-reviewer-b-form.md`). WP1.5 was the first
accept in that form; its pass 1 caught B3 (an H.264 output passing as SAME) that
neither Reviewer A nor the QA cell caught. Every accept record names the transcript
path, md5, five assertions and verdict, or there is no accept.

### Live workstreams

- **Orchestrator generation** `clearwater-orchestrator-20261014-1258` (opus/high/auto;
  verify `comms/.launch-sessions.json`, `ListAgents`). All `wp1.5*` worktrees removed;
  branches `wp1.1`, `wp1.2`, `wp1.5` kept for the reviewed SHAs (`git worktree list`).
- **Retroactive Reviewer B** (ordered 2b6dae230aa9749a; GO given 2026-10-15 ~09:5xZ):
  one seat pass on main over `git diff -U8 46a10b9..f6d998a -- tools/prototype
  tests/test_prototype_pipeline.py tests/test_prototype_backend.py`; not exclusive;
  introduced crit/major -> a NAMED bounded remediation package (not folded into Part B),
  else banked; addenda to `docs/proofs/wp1.1-accept.md` AND `wp1.2-accept.md`.
  **Result 09:41Z: BLOCKING** (M1 `_probe_gpu` catches only ImportError; M2 derived sigma
  overflow gives a traceback; M3 float64 scalar accumulators vs spec 6.4; M4 128 px floor
  rejected as pre-ruled; m5-m7 minors). **CHARC RULED 09:42Z: M3 = option (a)** -- 6.4/D39
  governs image data and per-pixel ops; scalar reductions may accumulate in float64 if cast
  to float32 before use, same dtype on both backends, documented in open-values and
  docstrings; interpretation note, not a spec change (read back to the owner).
  **WP1.2R CONFIRMED** (prototype remediation; implementer-sonnet-high; STRONG; M1, M2, m5,
  m7 + M3 record; one A round, one seat B; not exclusive; worktree `.worktrees/wp1.2r`).
  Addenda (both transcripts), the M4 envelope note and DR-18 land in one commit after the
  WP1.2R accept. Verify: `git worktree list`; `docs/proofs/wp1.2r-ledger.md`; the addenda.
- **Real-inventory mechanical pass** (implementer-sonnet-medium, no code: `uv run python
  tools/inventory.py` with the main-tree local config; report counts, modes, chaptered
  recordings, LRV coverage, error rows, uncovered GoPro names): QUEUED; dispatch ONLY on
  CHARC's word after the owner reports the download complete (DR-6) -> CP1 (owner sorts
  categories; owner-reserved).
- **WP1.2 Part B** (real modes, full-clip end-to-end incl. decode/encode via the WP1.5
  SIMPLE path, largest photo, analysis speed with decode/LRV; EXCLUSIVE) after the
  inventory. WP1.3 and WP1.4 need CP1. **WP1.6** gate report after all six results;
  Gate 1 (N6 speed: core 3.5-13.5x over budget before decode/encode, unoptimised by
  ruling) goes to the owner there with measured options. Gate 6 is CHARC's at WP1.6.

### Footage (owner, read-only, never committed; verify `ls C:\Users\rwsmy\clearwater-footage`)

Owner 2026-10-15 ~05:25Z in chat: four shallow snorkel chapters GX011625-GX011628.MP4
(HERO13 Black; no .LRV/.THM); scuba (~20 m) clips and shallow still photos still to
come. At 2026-10-15 ~09:45Z: `SCUBA/` holds six real files (GX011589-93, GX011601;
49 MB-4.4 GB), one growing `.crswap`, and THREE zero-byte files (`GX011598.mp4`,
`GX011600.mp4`, `GX011598 (1).mp4`) -- raise the zero-byte files with the owner before
the inventory dispatch. **Owner 2026-10-15 (verbatim): "There will be no .lrv or .thm files,
those were apparently deleted off of the camera when the cloud upload was completed several
days ago"** -> D60 LRV leg untestable (Clearwater generates its own proxy, spec 7.3); Part B
drops the LRV column; a one-line D60 closure proposed to the owner (spec change, owner-
reserved; OPEN until approved). The download is NOT reported complete.

### Standing delegation (owner, 2026-10-14, chat to CHARC, verbatim)

"intent is for this development to run as unattended as possible. orchestrator
will send you operator related questions. Answer for operator unless the question
truly requires my input." Standing, not day-scoped. Recorded in CLAUDE.md "Roles".
CHARC answers in the operator's stead; the plan section 3 owner-reserved list is
the only trigger for a `decision_request` (the orchestrator HOLDS that item,
continues the rest). Read every answer back to the owner in the turn's recap.

### Behavioral pointers

- Port **8775** is Clearwater's comms-UI port; sibling harnesses use 8765. psmux
  session `clearwater`; session names `clearwater-<role>-<stamp>` (read the live
  name from `comms/.launch-sessions.json` before any cue). After every
  `role_mail.py post`, one `SendMessage` cue. Subjects under 120 chars; bodies via
  `--body-file`; re-list before posting.
- Harness core is the coa-chess lineage (stdlib-only; `uv run python -m unittest
  discover -s tests/harness`, 366 tests, run whenever `scripts/`, `.claude/`, kernel
  docs or `tests/harness/` change; new tracked doc prefixes go into
  `tests/harness/genericity_lists.py`). pytest excludes `tests/harness`.
- Toolchain uv + Python 3.12; FFmpeg 9.0.2 installed (not on THIS seat's PATH);
  CuPy `cupy-cuda12x[ctk]` in .venv (anything outside .venv is a STOP).
- Review gate `docs/review-gate-clearwater.md` (Codex via WSL, codex-cli 0.162.1;
  STRONG for product code, fast for docs/tools); evidence at
  `C:\Users\rwsmy\clearwater-review-evidence\<wp>\`.
- Working folder `work/` (gitignored); NEVER `git clean -x`. Commit by pathspec;
  footer `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>` only.
- Plan 4.3 exclusivity: timing/memory packages run alone; the harness gate counts as
  HEAVY inside an exclusive window.
- Roll this seat only after the `[ctx]` hook names the 400K cap, at a boundary
  (charter 5.1); commit this file by pathspec first; the outgoing seat stops
  draining (peek only).
