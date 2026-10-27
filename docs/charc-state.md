# CHARC -- Current State (the read-me-FIRST pointer)

> **Convention (CHARC-authored harness-architecture).** This file is the SINGLE
> current-state pointer for the director (CHARC). It is **OVERWRITTEN each
> session** -- it always reflects only the live now, never accumulated history.
> Narrative lives in `git log -- docs/charc-state.md`. **The bootstrap reads THIS
> file FIRST**, then the charter. Every fact below carries the method that
> re-verifies it; a successor re-runs the method rather than inheriting the fact.

---

### Phase / state

**Phase 3 (build), wave 3 COMPLETE, wave 4 being commissioned (2026-10-27).** Plan
`docs/clearwater-implementation-plan.md` v1.2. **CHARC generation 4** = `clearwater-charc-20261026-2007`
(fable/medium), launched by gen 3 at 06:07Z, picked up 2026-10-27 ~06:10Z from main 08a14ee; bash gauge
44 ms; inbox empty at pickup (gen 3 acked the wave 4 query while reading). Main ~1136 commits ahead of
`origin/main`, unpushed; no push asked (verify `git status -sb`).

### Generation 4 so far (2026-10-27 06:10Z onward)

- **Wave 4 RULED** (msg `6f725eee`, 2026-10-27 06:11Z, answering orchestrator query `280fb7a08b5e5cfc`):
  wave 4 = WP3.14 (opus-high, Claude) + the calibration pair NOW; **WP3.21 opens AFTER WP3.14's accept**
  (plan row dependency; V16 end-to-end row is the baseline; one GPU) with its brief draftable meanwhile.
  Pair: **WP3.20R settings dialog hardening (DR-53/54/55; DR-52 out) -> `implementer-codex-sol-high`**, A and
  B = the Claude pass (`codex_cell.py review`); DR-54 = REFUSE OK with a settings-owned message, disagreeing
  injected rule. **WP-T3 fixture checker hardening (DR-33 (a)-(d), no regeneration) -> `implementer-sonnet-high`**,
  B = Codex `gpt-6.1-sol`/high. Size ratio recorded for HD-1: WP-T3 ~1.3-1.5x larger (6 tool modules + 1,382-line
  test file vs 1 module 851 + 868); the new lane got the smaller package. Lane head-to-head (both Bs on one tree)
  owed at WP3.20R's gate. Briefs: one drafting helper each, CHARC approves FINAL; WP3.14's brief carries the
  recorded consumer notes (listed in the ruling). Orchestrator gen 12 (~300K) drafts, dispatches helpers, rolls.
- **WP-T4 parallel test workers COMMISSIONED** (owner 2026-10-27, verbatim "commission it", after asking
  whether the full suite runs with parallel workers; it did not: no xdist, serial, 4,766 tests, 27-45 min).
  AD-28 on main e2b471d (`pytest-xdist` dev group, MIT; two-leg suite: parallel leg `-n <=4` over tests with
  none of gpu/footage/gui/slow, serial leg over the marked tests; figures of record from serial runs only).
  Commission msg `f0741947` to orchestrator gen 12: Sonnet-class, THIRD after the calibration pair, lane by
  pace tiebreak, figures to HD-1 flagged outside the pair; brief by one helper, CHARC approves FINAL; at its
  accept the fill's GATE_CHECKS suite line becomes the two-leg command and CHARC QA uses the same.
- **Spec v0.5.5** applied (owner 2026-10-27 verbatim "Apply D75 erratum"; main a5f9245, text only; FYI `e414d7d0`).
- **Wave 4 briefs FINAL** (msg `b83526ce`, 2026-10-27 06:34Z, answering gen 12's `4b2d7b2e92048eaf`; drafts on
  `wave4-briefs` b7764c5): WP3.14, WP3.20R, WP-T3, WP-T4 all APPROVED, 36 questions ruled (helper recommendations
  adopted except: WP-T3 Q1 Reviewer A = Codex, my earlier "Claude" line was WRONG and is corrected; WP-T4 Q3 the
  fixture-cache race is reproduced with a slowed generator and LOCKED, not left to luck; WP-T4 Q6 the orchestrator's
  reviewer form (FAST Codex for a Claude cell, the pinned opus/high Claude pass for a Codex cell); WP-T4 Q7 two
  interleaved rounds, a third only on >15 % disagreement; WP3.14 Q12 GX011625 sustained row KEPT, last, OWED if
  not granted). WP3.14 Q8 D87 = REFUSE before writing (reading of record: stricter than 8.4's "warned", no owner
  decision). **IF-9 docstring amended ba28175**: provenance `source` = file NAME never the path (AD-13 amended,
  AD-20 record). At accepts I owe: DR rows (WP3.14 Q5 cache serialisation; WP-T3 Q3 XMP encodings), DR-53
  mechanism text (WP3.20R turn-1 record), the CLAUDE.md two-leg pointer (WP-T4), HD-1 calibration figures.
- **Orchestrator gen 14** `clearwater-orchestrator-20261026-2151` (launched by gen 13 at 07:51Z; **cue THIS name**;
  announce expected). Gen 13 `-2029` ROLLED 07:51Z at ~345K (state 930a78d, FYI `080ce65fb13768e9`): WP-T3 cell DONE
  (A converged R1, candidate `wp-t3-mc` 0fbbe44 on 528d865, full pytest 4,867 passed / 2 skipped / 2873 s, fixtures
  byte-identical; B staged for gen 14); WP3.20R build DONE in 6 Codex turns (64K-205K tokens; Claude A R1
  NO_NEW_CRITICAL_MAJOR, 3 minors 3 advisories, 4 fixed 1 declined 1 banked `54e2749`; candidate gate and the B
  head-to-head next); WP3.14 items 1-3 built on two seats (cell 1 238K, cell 2 ~208K; head 7bb5d85; cell 3 from
  the ledger: footage V4 leg, full suite, A R1; V16 windows later); WP-T4 three turns done (lock = xdist + execnet;
  guard holds on workers, 16 cases; cold-cache race REPRODUCED and locked; awaiting its first PARALLEL run). Gen 13
  was launched by gen 12 at 06:29Z (state 1217443). Gen 12 rolled at ~380K. Gen 13's plan: apply the FINALs on
  `wave4-briefs`, ff main, dispatch WP3.14 (opus-high), then WP3.20R (Codex) + WP-T3 (sonnet-high), then WP-T4.
- **WAVE 4 DISPATCHED** (orchestrator msg `9f91fedce40aaaf1`, 2026-10-27 06:35-06:40Z, from main 9753b7b; briefs FINAL
  on main; harness 379 OK): WP3.14 `wp314-cell1` opus-high (A/B Codex gpt-6.1-sol); WP3.20R Codex cell (A/B Claude
  opus/high; head-to-head at its gate); WP-T3 `wpt3-cell1` sonnet-high (A/B Codex STRONG); WP-T4 Codex cell by pace
  (Codex 1.71 vs Claude 2.115 at 06:38Z). All depths 0 at dispatch. `tests/fixture_plugin.py` fenced: WP-T3 edits
  `verify_generated` only, WP-T4 edits `SampleProvider.path` + helpers after the class; sequential merges with a
  patch-id check (no objection). V16 exclusive windows OPEN/CLOSE come to me; nothing heavy at this seat while open.
- **WP3.14 R0** (orchestrator FYI `e1387fa8`, 06:46Z): DR-35 (a) premise FALSE on Windows 11 26300 (`NUL.MP4` is an
  ordinary file); orchestrator ruled a portable reserved-name guard (option A), CHARC UPHELD; DR-35 (a) mechanism text
  to amend at the accept. Cell depth 165K at R0 (re-seat expected after the build).
- **HARNESS: Codex sandbox pytest shim LANDED** main 542bc11 (orchestrator gen 13 finding on WP3.20R turn 1: Python
  3.12 `os.mkdir(0o700)` = owner-only ACL, the sandbox token cannot list pytest's own temp dirs, every `tmp_path`
  errored). `scripts/sandbox_mkdir_shim.py` (INSTANCE SURFACE in `genericity_lists.py`, not core: the guard bans the
  runner's name in core, manifest stays 22); preamble command `PYTHONPATH=scripts uv run pytest ... -p
  sandbox_mkdir_shim -p no:cacheprovider`; design pass 4.1a entry. Gate runs never load it. Harness 379 OK. HD-1 note
  owed at the calibration ruling. WP3.20R turn 1: 64,199 tokens, all three rows reproduce on the base.

### Generation 3 (2026-10-21 07:30Z to 2026-10-27 05:50Z; rolled at 420K; kept as record)

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
  none); CHARC's full pytest on main 47235b6 was STOPPED at ~93 % by Claude Code's low-memory reaper (no failure
  seen, one skip; NOT a result; not restarted on CHARC's own initiative, the owner may ask). **RULED: main's figure
  of record is the f1c1bd8 run by code identity** (0 lines differ in src/tests/tools/pyproject/uv.lock, verified
  here); hold lifted, orchestrator's window queue proceeds one suite at a time. **Tranche A: WP3.9, WP3.4, WP3.11 accepted; WP3.10 remains** (seat 6
  stood down at d389269, RESUME HERE complete; seat 7: full-pytest window, footage legs, EXCLUSIVE floor row, report).
- **Orchestrator gen 12 ONLINE** `clearwater-orchestrator-20261026-1223` (launched 2026-10-26 ~22:23Z; state
  2bb9bba; sole drainer; **cue THIS name**). Gen 11 `clearwater-orchestrator-20261026-0844` rolled at ~415K at
  the tranche-B B-gate boundary. **Gen 12 is the first role session spawned with the reaper OFF** (launcher
  60b2642).
- **Tranche B / WP3.10 at gen 11's rollover (2026-10-26 22:23Z):** WP3.17 (`wp3.17-mc` 0f7b5cd), WP3.19
  (`wp3.19-mc` 1be0a99), WP3.20 (`wp3.20-mc` e47c8d2): Reviewer B blocked twice each, pass 2 ADJUDICATED AT THE
  GATE by the orchestrator (one fix commit per finding, tests, docs; verified by execution at its seat); **CHARC
  looked and UPHELD all three** (evidence `reviewB2\` md5s OK, five assertions OK). WP3.18: loop terminated at the
  five-round gate, B pass 1 BLOCKED (A->B->A burst between run return and on_done with the adapter's kept job);
  ONE remediation at a fresh seat 3 then one B re-run. WP3.10 seat 7 footage window DONE: full suite on the
  rebased head 4434 passed / 2 skipped (also the candidate run); GX011627 all MANDATORY/REQUIRED SAME, tied True
  (DR-18 (1) closes AT WP3.10's accept); Edits compilation accepted with the 0.79 ms coarse-timescale limit.
  **PRODUCT DEFECT found: NVENC level cap** -- `-rc vbr -b:v 0 -cq N` without `-maxrate` lets NVENC pick HEVC
  level 5.0, whose bitrate cap overrides cq, so High/Standard/Draft are the same ~21.7 Mb/s encode on busy 4K.
  CHARC RULED round 9: `-maxrate`/`-bufsize` derived from the source's video bit rate (not a fixed 300M), test
  that the three levels differ, NVENC table re-run, then the AD-12 cq/crf mapping comes to CHARC on fixed
  figures (libx265 busy ratios 1.54 / 0.80 / 0.34 vs targets 1 / 0.5 / 0.25). DR-48 NEW (disk estimate
  under-estimates on calm clips; 10-bit doubling wrong). Owed at accepts: WP3.17 float-resolution debt row;
  WP3.14 brief notes (ok result names >= 1 output; per-item D87 check; DR-48). Next: WP3.18 remediation, WP3.10
  seat 8 (round 9, NVENC re-run, EXCLUSIVE floor row LAST with OPEN/CLOSE), orchestrator B on WP3.10, then ONE
  stacked suite over five packages (CHARC HOLDS main first), five accepts, CHARC QA on each.
 Gen 10 rolled at ~395K at the WP3.11 accept boundary and stopped draining.
  Gen 11's first acts: WP3.10 seat 7 and tranche B dispatch (WP3.17-3.20), one heavy job at a time. No live cells
  at rollover.
- **Tranche B seam rulings 2026-10-26 (gen 11 dispatched WP3.17-3.20 and WP3.10 seat 7 from main 718324b):**
  WP3.19 C1 GRANTED: the export seam (`ExportRequest`, `ExportJobs`, `CANCELLED`, `unavailable_exports`) lives in
  the new PySide-free `src/clearwater/jobs/export_seam.py` (owned by WP3.19), `gui/export_service.py` re-exports and
  keeps `ActivityGate`; `jobs/__init__.py` not edited; architecture note 42f8d70; seam approved as committed d286b8d
  with three docstring notes. WP3.18 Q-A RULED (C): additive `ClipAnalysis.retarget(parameters, *, focus_pts=None)
  -> bool` mapping to `AnalysisEngine.set_parameters` absorb (None while running = True), (B) finish-then-rerun as
  the False fallback, (A) cancel-and-restart withdrawn; AD-7 amended 8c67a6d; seam approved as committed 9f7c981;
  the retarget race (set_parameters returns a job) handled by the adapter keeping it for the next run. The
  orchestrator's own rulings (WP3.19 C2-C7; WP3.18 Q-B/D/E; WP3.20 capability job at first dialog open; WP3.17
  `normalisation_low < high` as a limit with an AD-20 consumer note) stand. Window queue agreed: (1) WP3.10 seat 7
  full pytest, (2) WP3.10 footage legs, (3) tranche B suites one at a time, (4) WP3.10 EXCLUSIVE floor row last.
- **Tranche B GUI packages WP3.17, WP3.18, WP3.19, WP3.20 ACCEPTED** by orchestrator gen 12 2026-10-26, main d31dd0f
  (one ff of `stackB-acc` = ccaecd7 + the four cherry-picked ranges, 101 commits; records `docs/proofs/wp3.1{7,8,9,20}-accept.md`;
  B-reviewed candidates kept as branches `wp3.17-mc1/mc2`, `wp3.18-mc1`, `wp3.19-mc1/mc2`, `wp3.20-mc1/mc2`). **CHARC
  QA CONFIRMED, static half:** per package, `git diff <mc> d31dd0f -- <owned files>` = 0 lines and the whole-diff
  patch-id of `base..mc` equals that of `ccaecd7..d31dd0f` restricted to the package's files (wp3.17 d4f1d179,
  wp3.18 b5055c32, wp3.19 4fba55dc, wp3.20 39f8b137); footprint = owned files only (interfaces, contract, gui/__init__,
  jobs/__init__, pyproject, uv.lock untouched; file sets disjoint); every changed blob LF (cat-file, 0 CR); all eight B
  passes: md5sums.txt OK, five assertions OK (gpt-5.6-sol/high; 0 ^ERROR; strict "succeeded in" 16/24, 14/16, 17/19,
  18/19; tokens footers; VERDICT anchored), every review-diff regenerates byte-identical from its prompt's range;
  ruff/format/mypy clean (217 formatted, 126 files); harness 366 OK. Full pytest: orchestrator's stack-top d71d994 run
  4501 passed / 2 skipped / 1579 s is main's figure by code identity (main differs in the four records only; verified
  here); CHARC ran no suite (WP3.10's footage window holds the host). Second blocking B adjudicated at the gate for
  WP3.17/19/20 (UPHELD earlier); WP3.18 B pass 2 CLEAN. Register: DR-49 (WP3.17 15-decimal limit), DR-50 (WP3.19 V7 at
  batch size), DR-51 (WP3.18 test-only limits), DR-52 (WP3.20 interim resolve_encoder stand-in) NEW. **For WP3.14's
  brief (wave 4):** an ok `JobResult` names at least one output; per-item D87 check (no batch-wide); DR-48 estimate
  floor; `CANCELLED` returned as the constant; non-ok outputs list files committed before the stop. **For WP4.3:**
  WP3.18 adapter mapping (kept job takes priority; own pts list; live Settings closure), DR-50/51/52 swaps, V7
  re-measure. WP3.18's R3 procedural breach: disclosed, not voided (accepted). WP3.20 B "succeeded in" strict counts
  18/19 (raw 20/21 include prompt echoes) -- the strict pattern `^\s*succeeded in [0-9]` is the standing count.
- **HARNESS CHANGE IN FLIGHT: dual-model implementers (owner-directed 2026-10-26/27).** Design pass
  `docs/proofs/harness-dual-model-implementers.md` (CHARC, 2026-10-27). Rules: R1 task fit first (Opus-class
  packages stay Claude; Sonnet-class eligible for Claude or a Codex `gpt-6.1-sol`/high cell); R2 the reviewer (A and
  B) is always the OTHER model from the implementer (B stays the orchestrator's own PROCESS at its seat: `codex exec`
  or `claude -p`, never a subagent); R3 tiebreak on weekly PACE (used % / elapsed fraction of the window), both
  readouts confirmed live 2026-10-27 (Claude 21 % at ~10 % elapsed = pace 2.1x; Codex 22 % at ~11 % = pace ~2.0x, CORRECTED 03:49Z from a mis-converted 1.0x; both lanes near 2x). Owner:
  "Start calibration this phase, write up the harness change." Stages: 0 probes (codex exec write mode in a
  worktree, resume, depth, the `claude -p` read-only reviewer with assertions, usage scripts) -> 1 operative edits
  (new cell `.claude/agents/implementer-codex-sol-high.md`, fill Parts 1-2, orchestrator-context, codex-reviewer,
  dispatch-recipe sentence, `scripts/usage_{codex,claude}.py` + tests, .gitignore, CLAUDE.md line, HD-1) -> 2
  CALIBRATION on the first two Sonnet-class wave 4 packages (one per lane, CHARC assigns at brief time; metrics and
  decision rule in the pass 4.3) -> 3 template port (owner). Owner DECIDED 2026-10-27 (pass section 5): footer `Co-Authored-By: GPT-6.1 Sol via Codex
  <noreply@openai.com>`; Claude readout under a standing project permission rule for `scripts/usage_claude.py`;
  review pin upgrade `gpt-5.6-sol` -> `gpt-6.1-sol` at the wave 4 boundary (one-time head-to-head); template
  port AFTER calibration experience. Stage 0 DONE 2026-10-27 04:11Z (pass sections 4.1a/4.1b): Codex lane works under the UNELEVATED Windows
  sandbox (`-c windows.sandbox="unelevated"`), `.git` is sandbox-protected so the ORCHESTRATOR commits per turn, resume
  needs `-c model=... -c windows.sandbox=... -c sandbox_workspace_write.writable_roots=[...]` every turn; the Claude
  reviewer pass (`claude -p --model opus --effort high`, no `--bare`) is credible: on accepted WP3.20 it found DR-53,
  DR-54 and DR-52 errata that two Codex passes missed. Readouts committed 9c15d0c. **Stage 1 LANDED (one harness commit after 68e3a2c; harness gate 379 OK):** cell
  `.claude/agents/implementer-codex-sol-high.md` (the staged preamble; not a subagent), driver `scripts/codex_cell.py`
  (`turn` = pinned codex exec / resume with the four `-c` overrides + banner assertions; `commit` = the FILES CHANGED
  block by pathspec with the owner's footer; `review` = the Claude `-p` read-only pass with model/clean-tree
  assertions), fill Parts 1-2 lane-dependent reviewer, orchestrator-context two-net + lane rule, codex-reviewer
  implementer section, dispatch-recipe process-turn sentence, HD-1 in decisions.md, CLAUDE.md line, manifest 22.
  NEXT: Stage 2 calibration at the wave 4 briefs (the orchestrator names the pair; CHARC assigns lanes; the pace
  tiebreak is suspended for the pair); the review pin upgrade is DONE 2026-10-27 at the owner's word (`strong` = `gpt-6.1-sol`/high, `fast` =
  `gpt-6-luna`/medium, both `~/.codex` sides; fill + codex-reviewer banner value updated; WP3.10's B passes on the old
  pin stand); head-to-head on WP3.20 bbf44e2 DONE (pass 4.6): gpt-6.1-sol found both old-pin majors in ONE pass plus
  DR-53/54 and a new DR-55, at 99K tokens vs 160K; the pin move stands on evidence. Sibling CHARCs notified (coa
  confirmed its driver passes `-m gpt-6-astra` per call and is unaffected; `wsl.exe bash -lc` resolves codex to the
  dead Windows shim, only `-ilc` reaches the WSL binary). Codex catalog at this
  login: 6.1-sol (default), 6-astra, 6.1-terra, 6-sol, 6-luna, 5.6-sol/terra/luna. Research notes (owner-supplied,
  untracked) in `research/multi-model development/`.
- **CHARC GENERATION 3 (`clearwater-charc-20261020-2115`) ROLLED OVER 2026-10-27 ~05:50Z at 420K (depth cap).**
  Gen 4 = `clearwater-charc-20261026-2007` (launched BY GEN 3 via `scripts/launch_role.ps1 -Role charc` at 06:07Z; the rolling CHARC always launches its successor -- owner rule). It reads this file first, then `docs/charc-charter.md`, then drains its inbox. **FIRST ITEM
  OWED: the orchestrator's QUERY `280fb7a08b5e5cfc` (2026-10-27 05:44Z, in `comms/charc/read/` -- gen 3 acked it
  while reading, so it is NOT in the inbox; open the file by name): wave 4 composition and the calibration pair.**
  The orchestrator reports wave 4 as framed has NO Sonnet-class package and recommends WP3.14 + WP3.21 (Opus-class,
  Claude lane) plus two small debt packages as the calibration pair: WP3.20R (settings dialog, DR-53/54/55) and WP-T3
  (fixture checkers, DR-33); it asks for a ruling on the set, the lanes and who drafts the briefs. **Gen 3's
  preliminary view (not a ruling; the successor rules after reading the full post):** the pair is sound in kind --
  both are well-specified remediation packages with fixed tests, the right class for `implementer-codex-sol-high`
  and `implementer-sonnet-high`; check they are comparable in size (ladder rungs, owned files, test roster) before
  assigning lanes, prefer WP3.20R -> Codex (the DR rows are precise, the findings came from the Claude pass so
  Claude reviewing Codex closes the loop) and WP-T3 -> Sonnet; the pace tiebreak is suspended for the pair (design
  pass 4.3); briefs drafted by the orchestrator, CHARC rules on them as usual; WP3.14 and WP3.21 stay Claude
  (Opus-class, frozen-interface adjacent). Reviewer B for WP3.20R = the Claude pass (`codex_cell.py review`); B for
  the others = Codex at the NEW pin `gpt-6.1-sol`. The LANE head-to-head (Codex B and Claude B on ONE finished
  tree) is owed at WP3.20R's gate.
- **Gen 3's last state:** wave 3 COMPLETE (WP3.10 accepted 47bc6d6, CHARC QA confirmed d834993). Harness: the
  dual-model lane landed (3c230e4), the Reviewer B pin moved to `gpt-6.1-sol`/high (fac53e9; head-to-head ceec6b9),
  the weekly readouts live (9c15d0c), owner decisions recorded (7681dcd). Owner-pending: D75 parenthetical erratum
  (v0.5.5), photos (WP3.6P), the iPhone clip (DR-15). Nothing heavy runs at the CHARC seat. The Codex discussion
  with the owner is CLOSED (all four decisions taken 2026-10-27).
- **WP3.10 ACCEPTED 2026-10-27 at main 47bc6d6 (orchestrator gen 12; wave 3 COMPLETE).** Candidate `wp3.10-mc`
  7f98848 (= `wp3.10` 2b8cd29 rebased onto 59049a9; 72 commits; accept chain 831fb8d on ceec6b9); record
  `docs/proofs/wp3.10-accept.md`; B trees kept as `wp3.10-mc1` 78ae77a / `wp3.10-mc2` da33e63. **CHARC QA CONFIRMED
  (static):** `git diff 7f98848 47bc6d6 -- src tests tools pyproject.toml uv.lock` = 0 lines; whole-diff patch-id of
  base..mc = base..main restricted to the 14 package files (63c56241); footprint owned files only (interfaces,
  pyproject, uv.lock untouched); every changed blob LF by cat-file; both B passes md5 OK, five assertions OK
  (gpt-5.6-sol/high, the pin of the day; 0 ^ERROR; 31/32 succeeded; 318,111 / 242,942 tokens; VERDICTs anchored);
  ruff/format (227)/mypy (132)/harness 379 clean on main at this seat. Full pytest: the candidate's run 7f98848
  4766 passed / 2 skipped / 2715 s is main's figure by code identity (verified here); the first candidate run was
  VOID (no `clearwater.local.toml` in the gate worktree) -- rule added to the fill's GATE_CHECKS. Register: DR-17,
  DR-18, DR-26 CLOSED; DR-20 (4)(6) CLOSED; DR-39 (a) CLOSED, (c) PARTLY; DR-56 (audio edit-list tail not compared),
  DR-57 (sink limits a-d), DR-58 (several GPUs; probe.py FFREPORT; timing-bound test) NEW; DR-15's iPhone leg
  OPEN (owner clip). **For WP3.14's brief:** QUALITY_RATIO figures (report 7.2) with DR-48 as ruled; cancel goes
  through `abort`; a `close` after a partial write is refused by design; provenance < 16 KiB; `resolve_encoder` is
  the ONE "auto" rule (WP3.20's stub swapped at WP4.3, DR-52); the V16 end-to-end row. Owner: D75 parenthetical
  erratum (v0.5.5). Orchestrator process note: five bare `cd`s this generation, all reverted, no cell affected.
- **WP3.10 floor row DONE (seat 9, EXCLUSIVE window 2026-10-27 01:09Z-02:02Z, CLOSE c02b6a47c057f2e4):** on
  e04a7cb (mapping commit, values-only CONFIRMED at this seat: NVENC_CQ 22/26/30, X265_CRF 21/26/30, one selection
  line in `_encoder_options`). NVENC 8-bit 4K 0.154-0.156 s/frame (3 runs GX011627; GX011625 all 14,938 frames
  0.1552), 10-bit 0.1742, libx265 0.2792; peak RSS 2.0-3.5 GiB. FITS D106: 0.4392 (c3 core) + 0.155 = 0.594 of
  0.834 s/frame, ~0.24 spare (sum of separate timings; end-to-end is WP3.14's V16 row). Strays-pause: only the
  first frame after a pause runs fast. Record `clearwater-review-evidence\wp3.10\s9-floor\`. Seat 9 head
  4dbb2d5, report FINAL. Disclosed: leg (a) M+R fidelity check ran on 0b76301 (cq 23), not e04a7cb; CHARC RULED no
  re-run (M+R items are container/timing/metadata, independent of the cq value; note in the accept record).
  QUALITY_RATIO measured (busy Standard file ratio 0.495/0.498/0.486) feeds DR-48's rule. Next: orchestrator B on a
  rebased candidate, candidate gate (full suite -- host free), accept, release post, CHARC QA; DR-18 (1) row.
- **WP3.10 AD-12 mapping RULED 2026-10-27 (orchestrator query 71bc572ed8981978):** ADOPT libx265 crf 21/26/30,
  NVENC cq 22/26/30, 0.24 bit/pixel FINAL; AD-12 amended in `docs/decisions.md` with the measured figures (seat 8
  footage window 23:29Z-00:52Z, ledger `docs/proofs/wp3.10-ledger.md` on `wp3.10` df055c2, product head 0b76301,
  evidence `s8-footage\ad12alt.log`). D75 READ as deferring to AD-12 ("provisional mapping AD-12 ... verified at
  WP3.10"): no decision_request; the stale parenthetical is an OWNER spec-errata item (next edition, v0.5.5). No
  Reviewer A round for the mapping commit PROVIDED it is values-only: two tables (NVENC cq, x265 crf) replacing
  `QUALITY_VALUE`, `_video_options` picks by encoder, PROVISIONAL dropped from the docstrings, AD-12 tests
  updated; any other logic change owes a round. Reviewer B at the orchestrator's seat covers it. Seat 8 STANDS DOWN
  (305K); seat 9 fresh (implementer-opus-high) from RESUME HERE: mapping commit, five video modules, EXCLUSIVE
  floor row LAST on the final code (OPEN/CLOSE to CHARC; nothing heavy at this seat), report, return report; then
  orchestrator B, candidate gate, CHARC QA. DR-48 disposition RULED (max(ratio x source, ceiling x duration) x
  margin; no 10-bit doubling) for WP3.14's brief. DR-18 (1) closes at the accept.
- **WP3.10 (seat 8, 252K at R10):** R10 at the five-round gate 0/0/2, termination accepted; O3 remediation 5cc94e4 as
  ruled (0.24 bpp; explicit `-tier main -level L`; min() edge; hvcC source level; SinkReport warning); orchestrator's
  out-of-envelope choices ACCEPTED by CHARC: a ceiling above every Main-tier cap is cut to 6.2's 240 Mb/s, a picture no
  level holds is refused at `open`. Footage window GRANTED (leg b NVENC re-run, leg a M+R). Then the AD-12 proposal
  (cq, 0.24 constant, libx265 crf) to CHARC; EXCLUSIVE floor row LAST (seat 8 or fresh seat 9); then its own gate.
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

- Spec `docs/underwater-correction-spec.md` **v0.5.5** (text only, owner 2026-10-27 verbatim
  "Apply D75 erratum": D75 parenthetical = AD-12 final mapping; v0.5.4 owner-approved 2026-10-20
  ~16:00Z, verbatim "Gate 1: Option C.  2. Keep.  3. approve 0.5.4"; applied 9cf16c5). D106 interim N6
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
provisional until then; WP3.6P runs on them), an iPhone video clip (DR-15 B-frame edit-list leg), and ONE spec
text erratum for v0.5.6: section 10.2's N6 body still says "about 3.3 minutes per minute" where D106/V16 read the
interim 25 min/min (found by the WP3.14 brief helper 2026-10-27; nothing blocks on it). D75 erratum APPLIED (v0.5.5). Owner-reserved items (plan s.3): footage categories, look check and V2
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
