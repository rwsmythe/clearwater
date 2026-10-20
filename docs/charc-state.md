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
| WP1.4 (shallow) | 91f5775 | wp1.4-accept.md (36535bf) | statistics and smoothing experiments: `tools/prototype/temporal.py`, `statistics_experiments.py`, additive `correct(..., statistics=)` hook; D98 staged vs flat: no visible difference; seat B pass 1 BLOCKING (4 majors, ONE remediation `wp14-fix`), re-run BLOCKING again -> adjudicated at the gate (finding 3 result-bearing: 2 s default PROVISIONAL, re-measure per DR-25(3)); DR-23 (VFR by index), DR-24 (footage-layout skips -> WP-T2), DR-25 (B re-run 1-7, WP2.1), DR-26 (spike root paths, banked); CHARC md5s verified, QA CONFIRMED at this seat 2026-10-19 01:1xZ |
| WP-T2 | 8c9d780 | wp-t2-accept.md (f7e4cac) | footage locator `find_footage_file` in `tools/local_config.py` (VIDEO_EXTENSIONS relocated there); gate 628 passed 0 skipped; DR-24 CLOSED, DR-27 opened; seat B major (root junction walked) REJECTED by the orchestrator, upheld by CHARC; CHARC QA on the cheap checks 2026-10-19 (patch-id e5354e8d, md5s OK); suite re-run at this seat done 2026-10-19 ~14:10Z after Part B's window closed: 628 passed 0 skipped on main 5e3aa33; **QA CONFIRMED** |

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

- **Orchestrator generation 2** `clearwater-orchestrator-20261018-1442` (opus/high/auto; online
  2026-10-19T00:42Z; gen 1 rolled at 411K with no live cell; verify `comms/.launch-sessions.json`,
  `ListAgents`). All `wp1.5*` worktrees removed;
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
- **2026-10-19 live: WP1.2 Part B DISPATCHED (EXCLUSIVE)** -- `wp12b-cell`, brief
  `docs/briefs/wp1.2b-brief.md` FINAL f7e4cac. CHARC ruling 748d2835: long full clip = GX011625
  (not GX011600; 13 h buys nothing per-frame), GX011627 short clip, 4 h cap per exclusive window
  (cell records the estimate first, stops and reports if over). NO pytest, harness gate or Codex at
  this seat until Part B returns (plan 4.3). **CP1 COMPLETE** 2026-10-19 (`docs/proofs/
  cp1-footage-sorting.md`: Snorkel=shallow, SCUBA=deeper, edits=stress case; no open-water or
  static clips; chapter handling DEFERRED to v2). **Shallow CP2 COMPLETE** 2026-10-19
  (`docs/proofs/cp2-look-check.md`; sheet in the WP1.3 report section 9): no cast, halo, noise,
  clipping or flicker; Ancuti variants push red (skin, white boat); **owner: c3 default, Ancuti
  variants kept as options**; staged vs flat: no visible difference (D98 input). **Spec revision
  v0.5.3 APPROVED by the owner** ("approved as 0.5.3", 2026-10-19) and applied b3fcd86 (c3 default:
  D16 amended; chapter handling deferred to v2: 5.5, D21, D33, D80, D82, D83, D64 seam, G7, G11,
  V3 seam, V12, 8.2/8.3, UC2/UC3, 14.2 closed); CLAUDE.md spec line bumped; **plan v1.1** 51da4b0
  (WP3.8 removed, WP3.19 = batch queue + export progress, V12 deferred). Two cache sentences still
  mention chapter groups (spec line ~339, V17); moot in v1, untouched. Orchestrator told to cite
  v0.5.3 in every brief (17a0d287); prototype default flips to c3 in the next package touching
  tools/prototype, not inside Part B. **Part B idle ruling 2026-10-19 ~03:38Z** (msg d69d8e1f):
  cell's first window W1 discarded for sibling-harness load (16 python.exe, MsMpEng, WmiPrvSE);
  CHARC measured the machine idle (CPU 10-21 %, GPU 0 %) and ruled PROCEED NOW W1-W5 under the
  orchestrator's contamination rule plus: pre-window idle gate, no CIM samplers, drift baseline =
  clean W1 median (not Part A synthetic), stop after a second contamination -> only then ask the
  owner for a quiet block, no Defender exclusion, 4 h cap. Cell acknowledged the GX011625
  amendment (3c5f73b); GX011600 dropped; block ~3 h. Condition 4 then triggered (W1 contaminated
  twice by the swing-trading orchestrator's 16-worker pytest loop every 15-20 min); decision
  request e2c53e6a to the owner. **OWNER 2026-10-19 ~04:30Z: "I am not concerned about
  contaminated figures as the actual program itself will run in a non-ideal state. Best effort
  is fine."** Relayed c42d103e: no quiet block; cell released for W1-W5; each window once (short
  windows may re-run once; W2/W5 never); contaminated windows labelled and reported as measured
  spread with stray readings, clocks, pstate, power; report carries the shared non-idle laptop
  caveat; Gate 1 decided on these figures with that caveat. Report round proceeds after W5. **Part B RETURNED 2026-10-19 ~14:00Z** (head 2fa0ac8, candidate
  6e538d7; gates 672 passed; B #1 BLOCKING 4 major 5 minor, one remediation under way, no
  re-timing, brief docs/briefs/wp1.2b-remediation-brief.md). Headline: core 4K GPU ancuti2018
  0.395 s (3.6x N6 0.1101 s), c3 0.639 s; GX011627 end-to-end 4.41x N6 (resident 3.25x);
  GX011625 full clip 7.62x (contaminated, thermal 91 C); analysis pipe-bound (32 KB Windows raw
  pipe, 93.6 ms/frame vs 4-5 ms at >=1 MB blocks -> WP2.1 transport); memory 3,682 MiB process,
  2,860 MiB graphics; photo leg PENDING. Claim 7: no candidate reaches N6 -> Gate 1 needs CHARC
  options or an owner N6 decision at WP1.6. Exclusive window CLOSED; seat free. **Part B ACCEPTED
  2026-10-19 main 2dd06cf** (bundle 7e14b19; record docs/proofs/wp1.2b-accept.md; B #2 6 minor +
  1 advisory banked DR-28 + report errata; cell depth breach 932K recorded, orchestrator
  corrective: depth read at dispatch/yield/ruling, no multi-finding remediation >250K, STOP at
  ~400K). **CHARC QA CONFIRMED** (patch-id 3c25c656 on author head, candidate and main; accept
  record's 4781bbe0 is an erratum; md5s and verdicts OK; errata present; harness 366 OK).
  **Main re-gate DONE** at the CHARC seat on 83fd9c4 per the owner ("Go ahead and run the pytest
  and gpu re-gates", ~22:00Z): 690 passed 0 skipped, gpu 34, harness 366 OK; debt cleared.
  WP1.3D dispatched 22:03Z (deep look-check pack on SCUBA/; stills, case scan -> 4 candidates per
  section-12 case, 6 s deep clip, CP2 deep sheet); WP1.4b queued (noise test + Params() flip to
  c3; explicit-method pinning approved with two guards, msg cf95afbc). **Owner 2026-10-19 ~22:30Z:**
  GoPro accelerometer/gyroscope analysis is "out of scope for this project" (parked as a separate
  future project). The gpmd track on the owner's clips carries ACCL/GYRO ~200 Hz, GRAV/CORI/IORI
  30 Hz, GPS9, and camera state WBAL/WRGB 10 Hz, SHUT/ISOE 30 Hz (probed GX011627 at the CHARC
  seat); the camera-state streams are fair evidence inputs (ISO and WB gains per frame proposed
  for WP1.4b), the IMU is not. Owner ~22:45Z: "Camera state is fine"; the parked project is motion
  reconstruction (depth/time curves, geoplots). WP1.4b brief f183a11 carries claim 2a (camera
  state); synthetic KLV test, nothing from gpmd committed (GPS9 = dive sites). **Owner
  2026-10-20 ~02:15Z to the orchestrator: "You don't need to replace the cell at 240k, that
  should just be an evaluation point"** -> docs/orchestrator-context.md hazard (6) added 5692485
  (read depth at dispatch/yield/ruling; ~250K evaluate; ~400K stop); harness 366 OK. WP1.3D was
  re-seated twice (244K, 240K) before the correction; wp13d-cell3 continues from round 3.
  **WP1.3D ACCEPTED 2026-10-20 main 7f9fea1** (bundle db751cb; record docs/proofs/wp1.3d-accept.md;
  B #1 blocking -> one remediation at 130K in the same cell; B #2 NO_NEW_CRITICAL_MAJOR; DR-29
  banked; gates 734 passed 0 skipped, gpu 35, harness 366). **CHARC QA CONFIRMED** (patch-id
  039db285 on all three ranges; md5s; harness 366 at my seat). Deep CP2 pack: work/wp1.3d/
  index.html (48 stills + 12 candidates in c3 / ancuti2018 / ancuti2018-blue; 6 s clip
  GX011600 at the deepest candidate, 2 s staged smoothing). Candidates: noise GX011600_0665.031
  (D 0.209) + 3; open water GX011593_0255.021 (W 0.954) + 3; haze GX011589_0005.005 (H 0.050) + 3.
  c3 bound nothing; ancuti2018 red cap bound on one still and 104/179 clip frames. **Deep CP2
  COMPLETE 2026-10-20 ~06:25Z** (record docs/proofs/cp2-deep-look-check.md; sheet filled 169356f;
  WP1.3 sheet deep rows closed): owner "c3 throughout showed the best performance ... No halo or
  clipping ... No grain ... No flicker ... The cast is fairly well greyed"; c3 default CONFIRMED on
  deep; FINDING: 2 s smoothing does not hide a rock-to-open-water lighting step (clip ~1 s), routed
  to WP1.4b (msg de4dc755) and the Phase 2 temporal design; 2 s default stays PROVISIONAL.
  WP1.4b: claim 10b = that finding with an edge-effect check first (the clip is a 6 s excerpt;
  the centred 2 s window is one-sided in its first second); Params() flip landed alone b23bad9,
  62 test sites pinned + guards fddc4e3. **WP1.4b STOP 06:44Z**: Donoho reads 0 on all 8 deep
  frames (8-bit HEVC flattens the flat tiles; 63-99 % zero HH1). Orchestrator ruling upheld by
  CHARC: Immerkaer primary on the same tiles, Donoho cross-check, red-baseline tile set (source
  red >= 16/255), absolute sigma_R, quantised-regime test, report says "below the quantisation
  floor" where both read ~0. Early one-frame signal: a tighter cap LOWERS red noise, against
  D100's expectation; if the grid confirms, it is spec-bearing -> owner at WP1.6 result 4. Camera
  WB red gain 4.85 on GX011600@665 s: report total red gain (camera x ours). Re-seated by
  evaluation at 235K (wp14b-cell2, 06:45Z) with the grid, claims 7-10b and review ahead.
  **WP1.4b ACCEPTED 2026-10-20 main afaff0e** (bundle 5e1f3c3; record docs/proofs/wp1.4b-accept.md;
  A converged R4; B single pass NO_NEW_CRITICAL_MAJOR, 3 minor + 2 advisory -> errata + DR-30;
  gates 771 passed 0 skipped (suite now ~8-15 min, past one 10-min call), gpu 36, harness 366;
  cell2 retired at 388K). **CHARC QA CONFIRMED** (patch-id 04bc9d18 x3; md5; flip in tree;
  harness 366). Results: **Gate result 4 KEEP the caps** (red-lit tiles median sigma_R: off 0.736,
  cap 2.0 0.736, 1.0 0.783, 0.5 0.938; c3 0.481 lowest on every deep frame; default binds 1/8;
  clamp 3.0 never binds; N{} floor 0.02 binds none; alpha smoothed as value). Anti-D100 signal did
  NOT hold (only on crushed-red tiles below the quantisation floor; inference, not spec-bearing).
  Claim 10b: GENUINE scene step at 0.90 s, not an excerpt edge; neither reset nor 0.5 s window
  shrinks it, both add flicker; 2 s stays PROVISIONAL, evidence for the Phase 2 temporal design.
  Total red gain camera x ours ~6x Ancuti default, ~4x c3. **PHASE 1 INPUTS COMPLETE. WP1.6 gate
  report is CHARC's next task** (template docs/reports/wp1.6-gate-report.md); no package in
  flight; Gate 1 options go to the owner. WP1.4b dispatched (opus-high; flip guards + gpmd claim 2a). Next: WP1.3-deep / WP1.4b brief on SCUBA/ (c3 primary, Params() flips to c3), then
  WP1.6 gate report (Gate 1: core 3.6x, production export 4.4x over N6). **Footage-layout skips:** the owner's Snorkel/SCUBA/edits layout makes 3
  footage tests skip (root `GX011628.MP4` paths in `tests/test_container_spike.py:902`,
  `tests/test_lookcheck.py:1289`, WP1.4 test 7; also `tools/lookcheck/pack.py:94` and the WP1.4
  runner). CHARC ruling 2026-10-19 (msgs 35b13416 scope + 68fe376c-answer sequencing): WP1.4
  merges first with the skips recorded with cause in its accept; then **WP-T2** (sonnet-high,
  fast tier) adds `find_footage_file(stem)` to `tools/local_config.py` (additive, case-insensitive,
  recursive, unique-or-error, reuses inventory VIDEO_EXTENSIONS) and switches all five surfaces;
  gate back to 0 skipped; then Part B (exclusive). **Inventory DONE** b1fd289
  (`docs/reports/inventory-2026-10-18.md`): 35 videos 26/8/1, 0 errors, 0 chaptered, CHARC
  re-derived counts from the CSV, match. **CP1 handed to the owner 2026-10-19 ~00:30Z:** categories
  (recommended folder-wise: Snorkel=shallow, SCUBA=deeper, edits=stress case) and chapter handling
  in v1 (CHARC recommends DEFER to v2: removes WP3.8, WP3.19 chapter review, V12, V3 seam; spec
  5.5 + D21/D33/D80/D82/D83 revision to draft on the owner's word). OPEN until the owner's word.
- Drafted by CHARC on main: `docs/briefs/wp1.2b-brief.md` (Part B; three dispatch conditions)
  and `docs/reports/wp1.6-gate-report.md` (template; Gate 1 options A/B/C framed).

### Footage (owner, read-only, never committed; verify `ls C:\Users\rwsmy\clearwater-footage`)

**Download COMPLETE (owner 2026-10-18, chat to CHARC, verbatim: "The videos are downloaded. I
placed snorkel videos in the snorkel folder and scuba videos in the scuba folder.")** CHARC's
read-only listing 2026-10-18 ~23:40Z: `Snorkel/` 26 clips GX011603-GX011628 (HEVC 4K 29.97,
3.6-498 s, shot 2026-10-10 05:21-06:33Z); `SCUBA/` 8 clips GX011589-93, GX011598, GX011600,
GX011601 (49 MB-8.9 GB); the 2026-10-15 zero-byte files and the `(1)` duplicate are GONE. NO
photos, NO .LRV/.THM (owner 2026-10-15, verbatim: "There will be no .lrv or .thm files, those
were apparently deleted off of the camera when the cloud upload was completed several days
ago"; D60 closed v0.5.2). Photos: pending (owner 2026-10-18).
One misnamed file `Snorkel/6aca1cf5db06c242d9d53130.json` (318 MB) is an MP4: H.264 1080p59.94,
180 s, Lavf61.7.100, created 2026-10-10T11:12Z; owner (verbatim): "It looks like it is a
compilation video. We can rename it and potentially use it as a stress test since it has
transitions." Owner renamed it 2026-10-18 (verbatim: "renamed to
Edits\compilation-20261010-1080p60.mp4, no photos for now they are still pending, go.");
CHARC verified `Edits/compilation-20261010-1080p60.mp4`, 35 files (Snorkel 26, SCUBA 8, Edits 1).
Photos PENDING (owner adds stills later; photo-side checks stay queued). The compilation clip
is kept as a smoothing stress case (hard transitions) for a later WP. **Inventory pass
commissioned** (msg 2d809944), held (114f9cea), **RELEASED 2026-10-18T23:55Z (msg 858f79a4)**.
Then: inventory report -> CHARC -> owner for CP1 (categories,
owner-reserved) -> Part B (after WP1.4 lands or pauses).

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
