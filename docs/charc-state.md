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
  blocked stopping it; CHARC verified and surfaced to the owner; STOPPED ~05:20Z on the owner's direction (taskkill typed by the owner, run via PowerShell by CHARC); orchestrator told.
- Debt register `docs/debt-register.md`: DR-1..DR-15 (DR-3, DR-4, DR-5 closed).
- No authority granted by `SendMessage` this generation (cues only).

### Pending items

1. **Owner decision request 2026-10-14T23:45Z** (spec text, measured CPU/GPU): APPROVED by
   the owner 2026-10-15 in chat ("approve the spec amendments as written"); applied as spec
   v0.5.1 (D117, section 12, 14.2 closed, 15.2 Q1; changelog line); DR-5 CLOSED. DONE.
2. **Footage PARTIAL (owner, 2026-10-15 ~05:25Z in chat):** four GoPro chapters
   GX011625-GX011628.MP4 (406/1390/151/17 MB; all shallow snorkel; no .LRV/.THM) are in the
   footage folder (it now exists). Still to come: deeper (~20 m) scuba clips and shallow still
   photos. The real-inventory pass stays QUEUED until the owner says the download is
   complete (DR-6) -> then CP1. **WP1.5 commissioned 2026-10-15T05:28Z** on the four
   chapters (draft `docs/briefs/wp1.5-brief.md` a0c1a96; opus-high; STRONG; FFmpeg-as-
   process only, PyAV not granted; identity re-encode; primary GX011627, fast GX011628);
   dispatch sequenced AFTER WP1.2A closes (after B2). DISPATCHED ~06:00Z; **author
   returned 07:10Z** (head 97d40df; A converged r2): recommends SIMPLE -- every MANDATORY item
   SAME (full pts exact, start offset, elst by presentation effect, audio byte-identical);
   lost best-effort: udta atoms (FIRM, LENS, global GPMF), firmware tag; kept GPMF track,
   tmcd, creation time. Capability proven: NVENC 8/10-bit, libx265 8/10-bit, cuda decode.
   Camera: HERO13 Black, HEVC Main 8-bit, BT.709, FULL range. No .LRV (D60 open). Reviewer
   B in flight. CHARC PRE-RULED 07:12Z: (1) MANDATORY = video-track elst as written +
   presentation effect; muxer-added identity edits on audio/data = best-effort; (2) REQUIRED
   (D55/D114) class accepted; (3) D54 no conflict, WP2.1 must honour full range; (4) udta
   repair -> debt item at the accept (trigger WP3.10). Footage snapshot test failing on
   .crswap files = download in progress; environmental.
   **REVIEWER B CORRECTION (owner catch, 2026-10-15 07:25Z, verbatim to the orchestrator:
   "You should be running reviewer B yourself, it is a specific codex review agent that
   you run, not a subagent").** CHARC confirmed against orchestrator-context.md line 53 and
   the coa-chess / swing-trading fills; the error was in my bootstrap fill. Fill corrected
   at 30483f2 (Part 2 item 2: B = ONE Codex pass the orchestrator runs at its seat on the
   merge candidate, whole-artifact, claims first, dispositioned, transcript in the accept
   record; cells may only do mechanical QA reproductions). Ruled 07:28Z: wp15-revb finishes
   as QA evidence, then the orchestrator runs B itself on the WP1.5 candidate; one
   retroactive B pass over tools/prototype (46a10b9..f6d998a) after the WP1.5 accept,
   addenda to the WP1.1 and WP1.2A accept records. No more Reviewer B cells.
   07:31Z: pre-ruling 1 STANDS (video elst as written identical on the GoPro chapters;
   SIMPLE holds). B-frame sources (iPhone) would be encode-then-repair under it -> DR-15,
   trigger WP2.1, with CHARC's lean recorded (presentation-effect reading where only the
   composition-offset convention differs). Roster plan accepted; GO after wp15-revb. FINAL issued 8ad93b8 (05:30Z);
   local config copied into the worktree so the footage test runs; Reviewer B ordered.
   Orchestrator self-reported a harness-gate overlap with the GPU re-measure start; the
   overlapped cell is discarded and re-run.
  **ACCEPTED 2026-10-15T05:56Z**: main f6d998a, record 7048fd7; A r1 0/0/3; B BLOCKING (c3
  reproduction) -> re-measured clean -> B2 NO_BLOCKING (within 4.1%). CHARC QA at this seat:
  all gates green. SYNTHETIC figures: GPU 4K 0.389 s (3.5x N6) / 0.652 s (5.9x); 5.3K 0.836
  / 1.503 s; pool 1712 MiB 4K / 3275 MiB 5.3K; CPU 11-58 s. Card power-capped at loop end.
  Proxies: means and WB gains hold; N{} bounds shrink 9-19%. CHARC rulings: `_windows_power()`
  APPROVED instrument-only (N1 exception, bench.py only); [ctk] N13 list -> WP2.1; Gate 1
  held for WP1.6. Exclusive window CLOSED; WP1.5 dispatched by the orchestrator.
3. **Next harness acts:** QA the WP1.2 Part A accept when it lands (B2 reproduction
   pending); QA the WP1.5 accept; WP1.2 Part B after the footage is complete and WP1.5
   reports; WP1.3 and WP1.4 need CP1; WP1.6 gate report after all six results.
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
