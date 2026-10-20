# CHARC -- Current State (the read-me-FIRST pointer)

> **Convention (CHARC-authored harness-architecture).** This file is the SINGLE
> current-state pointer for the director (CHARC). It is **OVERWRITTEN each
> session** -- it always reflects only the live now, never accumulated history.
> Narrative lives in `git log -- docs/charc-state.md`. **The bootstrap reads THIS
> file FIRST**, then the charter. Every fact below carries the method that
> re-verifies it; a successor re-runs the method rather than inheriting the fact.

---

### Phase / state

**Phase 2 (architecture and interfaces), closing; Phase 3 (build) about to open.**
Plan `docs/clearwater-implementation-plan.md` v1.2. **CHARC generation 2**
`clearwater-charc-20261020-0636` (fable/medium, `scripts/launch_role.ps1`), picked up
2026-10-20 ~16:50Z from generation 1 (`clearwater-charc-20261014-1303`, rolled at the 400K cap,
hand-off commit edd1e88; its narrative is in `git log -- docs/charc-state.md`). Bootstrap
steps 1-5 were done by generation 1; this seat re-read the kernel docs, drained the inbox and
announced itself. Main ~500 commits ahead of `origin/main`, unpushed; the owner has not asked
for a push (verify `git status -sb`).

**Bash-launch gauge:** 35.5 ms (2026-10-20, this seat; PowerShell
`Measure-Command { & $env:CLAUDE_CODE_GIT_BASH_PATH -c true }`). Under the 1 s flag.

### Frozen inputs (verify each at its path)

- Spec `docs/underwater-correction-spec.md` **v0.5.4** (owner-approved 2026-10-20 ~16:00Z,
  verbatim "Gate 1: Option C.  2. Keep.  3. approve 0.5.4"; applied 9cf16c5). D106 interim N6
  25 min/min; D100 caps KEPT; chapter handling deferred to v2 (v0.5.3).
- Architecture `docs/architecture.md` **FINAL 1.0**; decisions `docs/decisions.md` AD-1..AD-27.
- Interfaces **IF-1..IF-10 FROZEN** in `src/clearwater/interfaces/` (WP2.2, main b288533); any
  change is a STOP to CHARC (AD-20).
- Gate report `docs/reports/wp1.6-gate-report.md` CLOSED; records `docs/proofs/cp3-prototype-gate.md`,
  `cp4-design-freeze.md`. Phase 3 frame `docs/briefs/wp2.4-phase3-frame.md` (waves 1-4, grants,
  spec-to-package map).
- Accept records for every closed WP in `docs/proofs/` (WP0.1 .. WP2.2); debt register
  `docs/debt-register.md` DR-1..DR-32 (OPEN unless marked CLOSED; CLOSED: 3, 4, 5, 9, 21, 24).

### Live workstreams (verify `git worktree list`, `docs/orchestrator-state.md`, `ListAgents`)

- **Orchestrator generation 4** `clearwater-orchestrator-20261020-0524` (opus/high/auto; online
  15:30Z; sole drainer). Always re-read `comms/.launch-sessions.json` before a cue.
- **Live cell: WP2.3 fixtures, `wp23-cell2`** (sonnet-high) in `.worktrees/wp2.3`, branch
  `wp2.3`, from d495b57 (R1 closed 11/11), dispatched ~16:37Z at depth 0. Applies CHARC ruling
  ef7b272564ddeb9d (AD-14 centre track; one readable conditional `pytest_plugins` line in
  conftest; `.gitattributes` `tests/fixtures/** -text` with raw-byte regeneration compare), then
  Reviewer A R2; yields at R2's verdict BEFORE any remediation. The first cell (`wp23-cell`)
  retired at 406,816 past the cap after remediating R1 without a yield; the accept record must
  say so. **That worktree is OCCUPIED: do not touch it** (charter 5.1 incoming precondition).
- **On WP2.3's return:** CHARC QA at this seat (git patch-id on author head, candidate and main;
  B transcript md5s; the five assertions; DR entries; harness gate 366 at this seat). Then the
  orchestrator dispatches **wave 1** in parallel: WP3.1 core (opus-high), WP3.7 probe, WP3.13
  naming, WP3.15 presets/settings (sonnet-high); briefs `docs/briefs/wp3.{1,7,13,15}-brief.md`
  APPROVED 47b9738. At FINAL each cites v0.5.4 and architecture 1.0 (no "proposed" markers),
  fills WP2.3's manifest ids, and WP3.1 carries a one-line Gate 1 section (IF-2 ops
  device-resident-ready, no implicit host copies). Full-pytest gate windows serialised across
  parallel cells.
- **Then:** waves 2-4 per the Phase 3 frame (orchestrator drafts, CHARC approves each; WP3.21
  optimisation package drafted at wave 4, target 10 min/min, re-measure at WP5.2). CP5 shows the
  owner the starter preset values. Close DR items in the register as packages close them.

### Owner

**No owner decision open.** Photos still pending (memory-test photo leg; AD-24 HEIC rule
provisional until then). Owner-reserved items (plan s.3): footage categories, look check and V2
visual review, anything relaxing a mandatory requirement, any spec change. Everything else CHARC
rules in the operator's stead (standing direction 2026-10-14, verbatim in CLAUDE.md "Roles";
memory `clearwater-unattended-rule.md`); read the owner's words back verbatim with their time;
end every owner-facing turn with the open owner decisions.

### Footage (owner, read-only, never committed; verify `ls C:\Users\rwsmy\clearwater-footage`)

`Snorkel/` 26 clips GX011603-GX011628, `SCUBA/` 8 clips, `Edits/compilation-20261010-1080p60.mp4`
(35 files; inventory `docs/reports/inventory-2026-10-18.md`). No `.LRV`/`.THM` (D60 closed). No
photos yet. Categories per CP1 (`docs/proofs/cp1-footage-sorting.md`): Snorkel=shallow,
SCUBA=deeper, Edits=stress case. GoPro IMU/GPS out of scope; nothing from a `gpmd` track is ever
committed (dive sites); camera-state streams (WBAL/WRGB/ISO/SHUT) are fair evidence inputs.

### Behavioral pointers (this seat)

- Port **8775** comms UI; psmux session `clearwater`; session names `clearwater-<role>-<stamp>`.
  After every `role_mail.py post`, ONE `SendMessage` cue to the exact live session name.
  Subjects under 120 chars (the poster refuses longer); bodies via `--body-file`; re-list before
  posting.
- Harness core is the coa-chess lineage (stdlib-only; `uv run python -m unittest discover -s
  tests/harness`, 366 tests; run whenever `scripts/`, `.claude/`, kernel docs or `tests/harness/`
  change; new tracked doc prefixes go into `tests/harness/genericity_lists.py`).
- Toolchain uv + Python 3.12; FFmpeg 9.0.2 installed (NOT on this seat's PATH, so the ffprobe
  tests skip here; the orchestrator's figure is the one of record); CuPy in .venv.
- Review gate `docs/review-gate-clearwater.md` (Codex via WSL, codex-cli 0.162.1; STRONG for
  product code, fast for docs/tools); evidence `C:\Users\rwsmy\clearwater-review-evidence\<wp>\`.
  Reviewer B is ONE Codex pass the ORCHESTRATOR runs at its own seat, never a cell.
- Working folder `work/` (gitignored); NEVER `git clean -x`. Commit by pathspec; footer
  `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>` only.
- Full pytest takes 8-15 min: run it in the background; nothing heavy while an exclusive window
  (plan 4.3) is open; the host kills background runs under memory pressure, re-run only when asked.
- Bash heredocs with apostrophe-heavy Python fail at this seat: write scripts to the scratchpad
  with the Write tool and run them. `ruff format` excludes `*.md`.
- Cell depth: read at dispatch, every yield and before any ruling; ~250K is an evaluation point
  (owner 2026-10-20), ~400K STOP. Roll this seat only after the `[ctx]` hook names the 400K cap,
  at a boundary, with no cell in flight (charter 5.1); commit this file by pathspec first; the
  outgoing seat stops draining (peek only).
