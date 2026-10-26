# CHARC -- Current State (the read-me-FIRST pointer)

> **Convention (CHARC-authored harness-architecture).** This file is the SINGLE
> current-state pointer for the director (CHARC). It is **OVERWRITTEN each
> session** -- it always reflects only the live now, never accumulated history.
> Narrative lives in `git log -- docs/charc-state.md`. **The bootstrap reads THIS
> file FIRST**, then the charter. Every fact below carries the method that
> re-verifies it; a successor re-runs the method rather than inheriting the fact.

---

### Phase / state

**Phase 3 (build), wave 3 tranche A in flight (paused 2026-10-21 09:15Z to 2026-10-26 at the owner's word, RESUMED 2026-10-26).** Plan
`docs/clearwater-implementation-plan.md` v1.2. **CHARC generation 3** = `clearwater-charc-20261020-2115`
(fable/medium), picked up 2026-10-21 ~07:30Z from 6533d8f; bash gauge 44 ms. Main ~815 commits ahead
of `origin/main`, unpushed; no push asked (verify `git status -sb`).

### Generation 3 so far (2026-10-21 07:30Z onward)

- **WP3.9 video decode ACCEPTED** by orchestrator gen 9, main 09ab408 (record `docs/proofs/wp3.9-accept.md`;
  B clean NO_NEW_CRITICAL_MAJOR; DR-45 NEW; DR-36 (a)(b) CLOSED by CHARC 1d1ead6). **CHARC QA CONFIRMED,
  static half** at this seat: patch-id set 70bbf36b on `de206e2..wp3.9` and `b9f3d09..09ab408~1` (19 each),
  021c8dd ff-ancestor; B md5s all OK, five assertions (one WSL vsock line classified environment noise);
  ruff/format/mypy clean; harness 366 OK. Orchestrator's main full pytest on 09ab408: 3670 passed, 2 skipped,
  1562 s (figure of record). CHARC's own full pytest on main (09ab408 tree + docs): **3670 passed, 2 skipped, 1267 s**, host
  quiet (orchestrator paused). **WP3.9 CHARC QA CONFIRMED in full.**
- **WP3.4 method assembly ACCEPTED** by orchestrator gen 10 2026-10-26, main ad15ab4 (record
  `docs/proofs/wp3.4-accept.md`; candidate 5ec4442 + erratum c1bf077; B pass 1 BLOCKED on B1 dtype coercion,
  one remediation, B pass 2 NO_NEW_CRITICAL_MAJOR; DR-46 NEW). **CHARC QA CONFIRMED, static half** at this
  seat: whole-diff patch-id 6b661264 and per-commit set md5 308e0113 identical on `de206e2..wp3.4` and
  `ac4be92..5ec4442` (31 each); 5ec4442 ff-ancestor of ad15ab4, the two commits above it docs-only; both B
  review-diffs regenerate byte-identical (`git diff -U8` minus docs/proofs and uv.lock: B1 vs 1dcfdaf, B2 vs
  5ec4442); five assertions on both passes (gpt-5.6-sol/high; 0 ^ERROR; 18/26 succeeded; tokens footer;
  VERDICT anchored); evidence md5s recorded in CHARC's QA post (no md5s.txt was banked by the orchestrator,
  noted); ruff/format/mypy clean; harness 366 OK. Register rows DR-19 CLOSED, DR-37 (a)(b)(d)(e), DR-38
  CLOSED, DR-40 (a), DR-13 placement note (this commit). Orchestrator's candidate pytest c1bf077: CuPy 3970/2,
  no-CuPy 3418/554 (figures of record); main's full pytest runs once after WP3.11 stacks. **No suite at this
  seat** until the orchestrator posts WP3.11's return. Second tranche-A return: tranche B (WP3.17-3.20)
  dispatchable after WP3.11's accept. Exclusive window figures: c3 0.4392 s/frame (53 % of the 4K budget),
  ancuti2018 0.1987; memory 1044/1998 MiB.
- **WP3.11 analysis engine ACCEPTED** by orchestrator gen 10 2026-10-26, main 47235b6 (record
  `docs/proofs/wp3.11-accept.md`; candidate 228285a, author branch wp3.11 fb6fa5a on base de206e2, gated STACKED on
  WP3.4's c1bf077; B pass 1 and pass 2 both BLOCKING, the second adjudicated at the gate (signed-zero hash fixed
  ef6c24d and verified by execution; cancel-race limits to DR-47 NEW); CHARC UPHELD the adjudication). **CHARC QA
  CONFIRMED, static half** at this seat: whole-diff patch-id 4088add4 and set md5 e764d40f identical on
  `de206e2..wp3.11` and `6b58619..228285a` (51 each); 228285a ff-ancestor of 47235b6 (record commit docs-only);
  both B review-diffs regenerate byte-identical from the stack base (`git diff -U8 c1bf077 0916646|fe64c75` minus
  docs/proofs, uv.lock = banked md5s 09e9dd7d / f9d39876); md5sums.txt banked and all OK; five assertions both
  passes (gpt-5.6-sol/high; 0 ^ERROR; 15/12 succeeded; tokens footer; VERDICT anchored 23/21); ruff/format/mypy
  clean (201 formatted, mypy 117); harness 366 OK; analysis imports none of io/cache/methods/gui/cupy. Register
  rows DR-23 CLOSED (product), DR-25 (1)(2)(4)-(7) CLOSED (3) open, DR-45 note (this commit). **Main's full pytest
  is OWED and is CHARC's run**: the orchestrator's stack-top f1c1bd8 CuPy 4200 passed / 2 skipped / 1935 s stands
  for the candidate (code identical to 47235b6); its no-CuPy leg was reaped at ~5 % (not a result; the brief needs
  none); CHARC's full pytest on main 47235b6 RUNNING in the background (`work/charc-qa/wp311-pytest.log`), its figure
  becomes main's figure of record and goes here. **Tranche A: WP3.9, WP3.4, WP3.11 accepted; WP3.10 remains** (seat 6
  stood down at d389269, RESUME HERE complete; seat 7: full-pytest window, footage legs, EXCLUSIVE floor row, report).
- **Orchestrator gen 11 ONLINE** `clearwater-orchestrator-20261026-0844` (launched 2026-10-26 18:44Z; state 02ac918;
  sole drainer; **cue THIS name**). Gen 10 rolled at ~395K at the WP3.11 accept boundary and stopped draining.
  Gen 11's first acts: WP3.10 seat 7 and tranche B dispatch (WP3.17-3.20), one heavy job at a time. No live cells
  at rollover.
- **Rulings this generation (all recorded durably):** WP3.10 round-0 Q-C upheld, AD-22 extended (absent
  edit list = identity presentation; 09ac181); Q-A/B/D no objection with build notes (1-byte sentinel
  invariant; nothing NUT/setts leaks into IF-5; unreadable-tail warning in SinkReport; 16 KiB provenance
  limit in IF-9 docstring); P8 non-square SAR refused at open by name, no IF change (msg 39ff5f6a); WP3.11
  V3-1 ruled: AD-14 clip tests the absolute bound only, V3's 25 % ratio asserted on a test-local
  jittering-patch clip, xfails become recorded-figure tests, ratios (ad14 0.39-0.49; WP1.4 real 0.35-0.45)
  go to the owner as INFORMATION at CP5 under V3 "tunable" (AD-14 extended b9f3d09); step-aware default
  stands (both candidates worse; AD-3 PROVISIONAL to WP5.2); **WP3.10 S1 ruled** (posted to the
  orchestrator inbox for gen 10 at pickup): fix from the source's own sample table, fold #2's exact
  head-trim refusal (media_time != earliest composition time), #3 cleanup, then round 3.
- **Orchestrator gen 10** `clearwater-orchestrator-20261021-0004` (launched 2026-10-21 10:04Z; state
  74b9bd8; ROLLED 2026-10-26 18:44Z, superseded by gen 11 above). Gen 9 PAUSED and stopped draining at 05dd68a.
  **RESUMED 2026-10-26: owner word in CHARC chat, verbatim "resume"**; relayed to gen 10 (RESUME post); gen 10 re-dispatches WP3.10/3.11/3.4 from their ledgers, tranche B after the second tranche-A return. Parked
  (cells dead with gen 9; worktrees intact with RESUME HERE ledgers, treat as OCCUPIED until gen 10 says
  otherwise): WP3.4 `.worktrees/wp3.4` 3fae1d5 (A converged; EXCLUSIVE --memory/--whole windows, two full
  pytests, report remain); WP3.10 `.worktrees/wp3.10` 98ee54a (R2 adjudicated; S1 ruling above; footage
  legs unblocked by WP3.9); WP3.11 `.worktrees/wp3.11` e82aa2b (R1 adjudicated 0/3/5; V3-1 ruling in its
  ledger). Tranche B (WP3.17-3.20) waits for two tranche-A returns: WP3.9 and WP3.4 are in; dispatch after WP3.11's accept.
- **On resume:** the owner launches orchestrator gen 10; it drains the S1 ruling, re-dispatches the three
  parked cells from their ledgers (depth read at dispatch), and WP3.10's exclusive windows resume one at
  a time. CHARC QA on each accept as the standing rules below.

## Hand-off record (generation 2 -> 3, 2026-10-21 ~07:20Z; kept as the pickup method)

**A successor: read this file first, then `docs/charc-charter.md`, `docs/charc-bootstrap.md`
(bring-up only; steps 1-5 done), `docs/orchestrator-context.md` (hazards 1-7),
`docs/dispatch-recipe.md`, `docs/review-gate-clearwater.md`, `docs/model-prompting-standard.md`
(section 9 carries the pre-dispatch rollover exception). Then measure the bash gauge, drain the
charc inbox (`uv run python scripts/role_mail.py read --role charc --all`), announce yourself to
the orchestrator (`--to orchestrator`, then ONE SendMessage cue to the exact name in
`comms/.launch-sessions.json`; gen 9 = `clearwater-orchestrator-20261020-1959` at the gen-3 pickup),
rewrite the Phase / state block with your own generation line and commit by pathspec.** Memory files under
`~/.claude/projects/C--Users-rwsmy-clearwater/memory/` hold the owner's rulings verbatim.

What generation 2 did (2026-10-20 16:50Z to 2026-10-21 07:20Z): QA-confirmed WP2.3, wave 1
(WP3.1/3.7/3.13/3.15), wave 2 (WP3.2/3.3/3.5/3.6/3.12/3.16) = 12 of 15 Phase 3 packages on main,
3559 tests; approved the wave-2 and wave-3 briefs; ruled the IF-7 amendment (AD-20), AD-5
stored-JPEG proxy, AD-11 V9 reading and V8 k > 1 bound, AD-17 16-bit readers + tifffile, AD-18
PySide6-Essentials + pytest-qt, AD-23 CREATE_NO_WINDOW extension, the pre-dispatch rollover
exception, kernel hazard (7); corrected the architecture (IF-7 block, provenance embedded).

**Standing rules this generation learned (add to the predecessor's list):** every CHARC QA =
patch-id (or sorted patch-id set when the record says so) on every range the accept record names,
Reviewer B md5s recomputed against md5s.txt with the five assertions (banner in stderr; "succeeded
in" lines are in the stderr file; a "Reconnecting" ERROR line BEFORE the first `codex` line is a
recovered retry), DR entries present, ruff/format/mypy/harness at this seat, ONE full pytest in
the background with nothing else heavy (the host reaps under memory pressure; a reaped run is
reported, not restarted, and the orchestrator's main run is the figure of record); never a suite
while an exclusive or heavy window is posted OPEN; Bash heredocs lose non-ASCII (U+2264) -- write
Python edit scripts to the scratchpad with the Write tool and run `python -X utf8`; apostrophe-heavy
heredocs also fail; the orchestrator rolls at ~400K every 3-4 accepts (gen 9 live at hand-off);
subjects under 120 chars; hold main when asked and commit nothing (including this file) until the
release post.

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

- **Orchestrator generation 9** `clearwater-orchestrator-20261020-1959` online 2026-10-21 ~06:00Z, sole
  drainer (gen 8 rolled at ~400K at a clean boundary, state 9364f8f; read
  `comms/.launch-sessions.json` before any cue).
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
- **Tranche A: WP3.3, WP3.5, WP3.2 ACCEPTED** 2026-10-21 as one stacked gate, main 68a8d93
  (records `docs/proofs/wp3.{3,5,2}-accept.md`; DR-38/39/40 banked; DR-14 CLOSED, DR-20(1)
  CLOSED; WP3.2 took ONE B remediation: float64 leak from NumPy-scalar parameters). Candidate
  gates 2904 passed / cupy-unimportable 2386 + 519 skipped; main 2904 passed. **CHARC QA
  CONFIRMED** (patch-ids on every named range; B md5s and assertions in four folders; static
  gates and harness 366 here; my own full pytest was host-killed at ~39 % for memory pressure and
  NOT re-run; the orchestrator's main run is the figure of record). Nine worktrees released.
- **WP3.12 proxy cache and WP3.6 photo I/O ACCEPTED** 2026-10-21 as one stacked gate, main
  4ec835d (records `docs/proofs/wp3.12-accept.md` 3aaf395, `wp3.6-accept.md` d0f00ee; DR-41,
  DR-42 banked; both packages: B pass 1 blocking, one remediation, pass 2 blocking adjudicated at
  the gate, upheld). Gates 3440 passed / cupy-unimportable 2922 + 520 skipped; the first stack
  run was host-reaped at ~91 % and restarted one job at a time on CHARC's word. **CHARC QA
  CONFIRMED** (identity sets, B md5s in four folders, static gates, harness 366, full pytest
  3440 passed at this seat, 798 s). Five worktrees released. WP3.12 facts: JPEG q75 4:4:4 store,
  codec identity in the cache version, two yield breaches and git stash use recorded. WP3.6
  facts: built-in P3/sRGB ICC in the WRITER for HEIC nclx sources only; untagged keeps no iCCP;
  stdlib PNG16 decoder; tifffile; WP3.6P queued for the owner's photos.
- **WP3.16 GUI shell ACCEPTED** 2026-10-21, main 0c41615 (record `docs/proofs/wp3.16-accept.md`;
  DR-43 reader-side G10 signal gap, DR-44 (a) decode-completion pairing, (b) message owner, (c)
  late job callbacks; B pass 2 adjudicated at the gate, upheld). Gates 3559 passed /
  cupy-unimportable 3040 + 521 skipped. **CHARC QA CONFIRMED** (patch-id set 7f42009d both
  ranges; B md5s both passes; static gates; harness 366; full pytest 3559 passed here, 838 s; GUI
  witness 41 passed on clean main after the orchestrator's uncommitted-edit slip, now kernel
  hazard (7) ca3eaea). Worktrees released. PySide6-Essentials on main without a reinstall.
  **WAVE 2 CLOSED: 12 of 15 Phase 3 build packages on main.**
- **Wave-3 briefs APPROVED** 2026-10-21 ~06:21Z (drafts on branch `wave3-briefs` 5d37ddb; rulings
  msg e78b0175): provenance EMBEDDED per D91 (architecture line corrected 7087e4f; MP4 `comment`
  tag carries the IF-9 JSON); WP3.10 round-0 timing spike (NUT framing), STOP if no exact carrier;
  DR-15's iPhone leg waits on an owner iPhone clip (owner-pending list); Y-1 statistics contract
  is an IF-3 READING written identically in WP3.4 and WP3.11; `core.backend_for` granted; DR-19
  closes in WP3.4; blend is a 0-100 schema value with a percent label (no IF-3 unit field);
  `resolve_encoder` in WP3.10 is the one "auto" rule; `ClipAnalysis` and `ExportJobs` seams frozen
  at round 0. DR-44 contract commit (branch `dr44` 5e95e0c, both nets at the orchestrator's seat)
  lands on main before tranche A dispatches.
- **DR-44 contract commit LANDED** on main (701055d members, 7bee620 B remediation, de206e2 B
  pass-2 minors; both nets at the orchestrator's seat; B pass 1 caught the shell's open path
  clearing panels' messages; shell clears only `shell.*` banners on a new source, panels clear
  theirs on `source_changed`). Briefs FINAL on main 0f51822. **Wave 3 tranche A LIVE** (dispatched
  ~07:05Z from de206e2; four opus-high cells, all OCCUPIED): WP3.4 `wp34-cell1` `.worktrees/wp3.4`,
  WP3.9 `wp39-cell1` `.worktrees/wp3.9`, WP3.10 `wp310-cell1` `.worktrees/wp3.10` (round 0 =
  timing spike, STOP if no exact pts carrier), WP3.11 `wp311-cell1` `.worktrees/wp3.11`. Exclusive
  windows (WP3.4 whole-core + memory, WP3.10 export floor) posted OPEN/CLOSE, one at a time; no
  suite here while any window or the orchestrator's gate run is open. Tranche B (WP3.17-3.20)
  after two tranche-A returns. On each accept: CHARC QA as before.
- **Wave 3 COMMISSIONED** (CHARC msg a10045b6, 2026-10-21 ~06:01Z): eight briefs drafted by gen 9's
  helpers for CHARC approval; tranche A = WP3.4 assembly, WP3.9 decode, WP3.10 encode/mux, WP3.11
  analysis (opus-high); tranche B = WP3.17-3.20 GUI panels (sonnet-high) after two tranche-A
  returns. Pre-dispatch commit (f4cd1e4 form, in `.worktrees/dr44`, both nets): additive
  `gui.contract` members for DR-44 (b) message owner and (a) decode-completion signal. Per-package
  debt citations ruled in that message (WP3.4 closes DR-19, exclusive whole-core speed row and
  memory peak; WP3.10 DR-15/17/18 and the exclusive export row; WP3.11 DR-23/25, stored proxy
  only, 2 s PROVISIONAL + step-aware task; WP3.20 settings_refusal, G12, D75).
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

**No owner decision open.** Owner-pending inputs: photos (memory-test photo leg; AD-24 HEIC rule
provisional until then; WP3.6P runs on them) and an iPhone video clip (DR-15 B-frame edit-list leg). Owner-reserved items (plan s.3): footage categories, look check and V2
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
