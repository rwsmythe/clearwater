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
| WP1.2R | 996274e | wp1.2r-accept.md (aac4674) | prototype remediation after the retroactive seat-run B (M1 probe catch-all, M2 derived-value validation, M3 float64 accumulators ruled (a), m5, m7); 2nd-B major adjudicated NOT BLOCKING, upheld by CHARC -> DR-19; arithmetic bit-identical in 6 witness cases |
| WP1.5 | 3242679 | wp1.5-accept.md (371f19d) | container spike: SIMPLE; MANDATORY+REQUIRED 0 DIFFERENT, 8 best-effort lost; NVENC/libx265 8/10-bit proven; HERO13 HEVC 8-bit BT.709 FULL range; no .LRV (D60 closed v0.5.2); DR-15..17 |
| WP1.3 (shallow) | 7178540 | wp1.3-accept.md (bc97a19) | look-check instrument `tools/lookcheck/`; pack `work/wp1.3/index.html` (24 stills x 3 variants, 180-frame unsmoothed flicker pair) READY FOR CP2; seat B pass 1 BLOCKING (3 introduced majors, ONE remediation `wp13-fix`), re-run BLOCKING again -> adjudicated at the gate (CRITICAL pytest basetemp exposure = DR-21, repo-wide; 2 majors instrument-only = DR-20); CHARC md5s verified, QA green at this seat 2026-10-15 13:3xZ |
| WP-T1 | f6a34a4 | wp-t1-accept.md (3f40a85) | pytest temp-root footage guard in `tests/conftest.py` (CHARC-commissioned, DR-21 CLOSED, DR-9 CLOSED); seat B pass 1 BLOCKING (C1 case, C3 fail-open, M4, M6; ONE remediation), re-run BLOCKING again -> adjudicated at the gate (4 crafted-state aliasing cases, DR-22(4)-(7)); DR-22 OPEN (9 limits incl. CHARC's accepted pre-conftest capture writes); CHARC md5s verified, QA at this seat 14:5xZ |

CHARC QA at this seat re-ran ruff/format/mypy/pytest green on every accept (pytest
skips the ffprobe tests here because this seat's PATH lacks ffprobe; the
orchestrator's 398-pass run is the figure of record). Spec at v0.5.2 (D60 closed 2026-10-15,
owner-approved; v0.5.1 073ca1f). Debt register `docs/debt-register.md`: DR-1, DR-2, DR-6..DR-8, DR-10..DR-20, DR-22 OPEN;
DR-3, DR-4, DR-5, DR-9, DR-21 CLOSED (verify `docs/debt-register.md`).

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
- **Retroactive Reviewer B over tools/prototype: CLOSED** (addenda in `wp1.1-accept.md` and
  `wp1.2-accept.md`; WP1.1 envelope formally short side > 128 px; DR-18, DR-19). No cell is
  live (verify `git worktree list`).
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

- **Partial CP1 (owner, 2026-10-15 ~10:50Z, verbatim: "shallow confirmed")** on the four
  chapters: `docs/proofs/cp1-footage-sorting.md` (living record). WP1.3 shallow part ACCEPTED
  (table above); its pack awaits the owner's CP2 look (owner-reserved; CHARC proposes the owner
  view it together with WP1.4's staged/flat renders). **WP1.4 (shallow part) DISPATCHED**
  2026-10-15 ~13:28Z (FINAL `docs/briefs/wp1.4-brief.md` 9ed1a1c; `wp14-cell`, opus-high;
  STRONG; `tools/prototype/temporal.py` + additive `correct(..., statistics=)` hook; reuses the
  WP1.3 instrument with `roots`, no D54 re-implementation; staged vs flat D98, smoothing
  candidates, robust N{} bounds; gain-cap noise test deferred to WP1.4b on the scuba footage).
  **WP-T1 ACCEPTED** (table above; the guard is live in `tests/conftest.py`; CLAUDE.md
  Conventions line added). WP1.4 is not exclusive and may not overlap Part B's bench window. Verify: `git worktree
  list`, `docs/debt-register.md` DR-20/DR-21.
- Drafted by CHARC on main: `docs/briefs/wp1.2b-brief.md` (Part B; three dispatch conditions)
  and `docs/reports/wp1.6-gate-report.md` (template; Gate 1 options A/B/C framed).

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
