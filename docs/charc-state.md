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

- **Orchestrator generation 6** launching 2026-10-20 ~21:34Z (gen 5 `clearwater-orchestrator-20261020-0802`
  rolled at ~430K with no live cell, state 26b095d; gen 6 announces on pickup and is the sole drainer). Gen 4 rolled at ~300K before the wave-1 fan-out (CHARC upheld; the
  pre-dispatch exception is written in `docs/model-prompting-standard.md` s.9, 2bd9894). Always
  re-read `comms/.launch-sessions.json` before a cue.
- **WP2.3 fixtures ACCEPTED** 2026-10-20, main d605925 (record row e357e56; record
  `docs/proofs/wp2.3-accept.md`; DR-33 banked, B re-run majors adjudicated NOT BLOCKING, upheld).
  **CHARC QA CONFIRMED** at this seat (patch-id 6712360de3e5 on both ranges; B md5s both passes;
  five assertions; 87 fixtures `-text`; ruff/format/mypy clean; harness 366; full pytest 1138
  passed, 526 s). Worktrees `.worktrees/wp2.3`, `wp2.3-mc` released for removal (msg 3f6e1943).
- **Wave 1: three of four ACCEPTED** 2026-10-20 as one stack on main 4f122ec: WP3.15 presets/
  settings/logging (`clearwater.config`, da54a47, DR-34, DR-32 CLOSED at the config boundary),
  WP3.13 naming/safe writing (`clearwater.jobs`, 6dd5a00, DR-35; tokened temporaries after an R1
  critical), WP3.7 video probe (`clearwater.io.video`, 6e3417a, DR-36; all 35 owner clips probe
  with 0 faults). Records `docs/proofs/wp3.{15,13,7}-accept.md`. **CHARC QA CONFIRMED** at this
  seat (patch-ids on every named range; B md5s and assertions in four folders; the wp3.15 B2
  "Reconnecting" ERROR line adjudicated a recovered retry, upheld; ruff/format/mypy; harness
  366; full pytest 1671 passed, 676 s). Six worktrees released for removal (msg wave1-qa).
  CHARC rulings this wave: round-0 tables upheld with three additions (msg 232646a5); IF-5
  `duration_s` = container duration, exact, docstring tightened 4174484; WP3.13 per-write token
  in the temporary name upheld.
- **WP3.1 array backend ACCEPTED** 2026-10-20, main c1fd6ce (code) / f4acbd0 (record
  `docs/proofs/wp3.1-accept.md`); DR-37 banked (CuPy load-failure reason string, CoreBackend
  typing of core.ops, nested footage-in-working-folder config, two advisories). Reviewer A R2 over
  two cells (re-seat at 275K); B one pass clean. **CHARC QA CONFIRMED** (patch-id 392da34a1461
  both ranges; B md5s and assertions; ruff/format/mypy; harness 366; full pytest 1844 passed,
  539 s). Worktrees released (msg wp31-qa). Speed row: GPU leg contaminated by CHARC's QA pytest
  (op-mix row only; whole-core row is WP3.4's). **WAVE 1 CLOSED.**
- **Wave-2 briefs APPROVED** 2026-10-20 ~22:32Z (drafts ea6dee1; rulings msg 873ec3c8; decisions
  amended 718da66: AD-4 floor by symmetric widening; AD-5 admits lossy intra proxy candidates under
  the statistics criteria, G4 ground; AD-17 stdlib PNG16 decoder + `tifffile` for TIFF; AD-18
  tifffile BSD-3 and pytest-qt dev grant; AD-20 IF-7 `source_statistics`, `mark_complete`,
  `CacheEntry.complete`, IF-5 abort docstring D44/D85 -- applied by ONE orchestrator commit on main
  before tranche A, with `methods/__init__.py`). Other answers: WP3.5 re-sized S on sonnet-high;
  WP3.16 opus-high, `gui.contract` frozen at round 0; WP3.6P real-photo verification queued for
  the owner's photos. Spec 7.2 line 325 chapter-group remnant: owner's next-revision list.
- **Tranche-A rulings so far:** WP3.5 R0 STOP: V9 binds RGB-side legs only, the 8-bit 4:2:0
  swscale pair is a characterisation (AD-11 clarified 2ce4266; bounds final at 59e4281: footage
  mean <= 1.0/255 and share over 2/255 <= 1 %, testsrc2 mean <= 2.5/255). WP3.12 STOP on AD-5: no
  8-bit store meets the 1 % bounds criterion and no lossless store fits 10 GB; RULED option 1
  (AD-5 amended a6ba740): the analysis proxy IS the stored JPEG q75 4:4:4 proxy (q80 4:2:0 only
  on the read-cost row), measured at first analysis and reopen alike; codec identity in the cache
  version; means/gains <= 1e-3 gate, bounds deviation <= 10 % of range reported; **owner sees the
  proxy-bound effect at CP5** (AD-4 11-14 % + AD-5 ~8 % narrower = slightly stronger stretch);
  Pillow becomes a product dependency at WP3.12; WP3.11 measures on the stored proxy only.
- **Wave 2 tranche A LIVE** (dispatched ~22:45Z from main 2c5540a; IF-7 amendment landed f4cd1e4,
  verified at this seat against the ruling; architecture IF-7 block updated by CHARC): WP3.2
  `wp32-cell` opus-high `.worktrees/wp3.2`; WP3.3 `wp33-cell` opus-high `.worktrees/wp3.3`; WP3.5
  `wp35-cell` sonnet-high `.worktrees/wp3.5`; WP3.12 `wp312-cell` sonnet-high `.worktrees/wp3.12`
  -- all OCCUPIED. WP3.12's exclusive read-cost window: the orchestrator posts OPEN/CLOSE; no suite
  here while open. Tranche B (WP3.6, WP3.16) once two tranche-A cells return.
- **Wave 2 COMMISSIONED** (CHARC ruling 1ebfba54, 2026-10-20 ~22:07Z): orchestrator gen 6 drafts
  all six briefs (WP3.2, WP3.3, WP3.5 opus-high; WP3.6, WP3.12, WP3.16 sonnet-high) against the
  Phase 3 frame, sends them as one set for CHARC approval; tranche A = WP3.2/3.3/3.5/3.12 on
  approval, tranche B = WP3.6/3.16 once two tranche-A cells return. Per-package debt citations
  ruled in that message (WP3.2 D100/DR-19; WP3.3 DR-14/DR-13/float32 percentile; WP3.5 DR-20(1)
  D54 fallback + limited-range convention; WP3.6 AD-24, DR-33(c), DR-31(1), DR-6/7/11; WP3.12
  stale chapter-group cache sentences read single-clip; WP3.16 DR-37(a)(b) status bar, G12,
  AD-15). Consumer notes for wave 2+ are in `docs/orchestrator-state.md` item 3. Reviewer B
  prompt practice note: git is unavailable inside a worktree under WSL.
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
- Full pytest takes 8-15 min: run it in the background; **nothing heavy while an exclusive window
  (plan 4.3) is open -- the orchestrator posts window open/close from 2026-10-20 on; before any
  suite at this seat, check the last such post (CHARC's wave-1 QA pytest overlapped WP3.1's speed
  window; ruled no re-run, op-mix row only);** the host kills background runs under memory pressure, re-run only when asked.
- Bash heredocs with apostrophe-heavy Python fail at this seat: write scripts to the scratchpad
  with the Write tool and run them. `ruff format` excludes `*.md`.
- Cell depth: read at dispatch, every yield and before any ruling; ~250K is an evaluation point
  (owner 2026-10-20), ~400K STOP. Roll this seat only after the `[ctx]` hook names the 400K cap,
  at a boundary, with no cell in flight (charter 5.1); commit this file by pathspec first; the
  outgoing seat stops draining (peek only).
