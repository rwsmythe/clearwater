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
- **Orchestrator gen 14 ONLINE** `clearwater-orchestrator-20261026-2151` (launched by gen 13 at 07:51Z, picked up
  07:52Z at 69fce7a, msg `a7da60b8`; sole drainer; **cue THIS name**). Running: WP-T3 Reviewer B on `wp-t3-mc`
  0fbbe44; WP3.14 cell 3 with footage V4 leg then full suite then A R1. **HOST HOLD: no suite at this seat until
  gen 14 says the host is free; hold main from WP-T3's B to its merge when told.** Heavy queue: WP3.14 footage ->
  WP3.14 full -> WP-T4 parallel run -> WP3.20R candidate full suite.
- **WP-T3 ACCEPTED** by gen 14 2026-10-27 08:08Z at main 2aca60e (record `docs/proofs/wp-t3-accept.md`; candidate
  `wp-t3-mc` d5cda37 = `wp-t3` 296eb18 rebased; A R1 0/0/2 terminated; B clean 3 minor 4 advisory; candidate full pytest
  4,867 / 2 / 2874 s = main's figure by code identity). **CHARC QA CONFIRMED (static, msg `ffd53b16`):** patch-id
  e38fa930 both ranges; ff-ancestor; footprint owned files only; fixtures byte-identical (87); 0 CR; B md5s OK,
  assertions OK (strict succeeded 14 / raw 15); ruff/format 227/mypy 132/harness 379 at this seat; no suite (host
  hold). Register 284e868: DR-33 CLOSED, DR-59 (XMP encodings), DR-60 (checker robustness B1-B6) NEW. HD-1 Sonnet-half
  figures banked in the QA post: one seat 159,635; A 1 round 88,642 tokens; B 105,819; dispatch-to-accept 1 h 28 min.
  Pair ruling at WP3.20R's accept (its Claude B of record DONE clean, 5 advisories; Codex B head-to-head and full
  suite pending).
- **WP3.14 Q2 AMENDED** (orchestrator query `755fe8deb5073865` on Reviewer A R1 F1 MAJOR; CHARC ruling 2026-10-27 ~09:15Z):
  cancel stays live THROUGH `sink.close()`: check before `close`, watchdog alive through it and joined before the
  post-close check and `commit`; the post-close cancel check is MANDATORY and UNCONDITIONAL (verified at the code:
  `encode.py` `close` writes `"closed"` unconditionally and can overwrite the watchdog's `"aborted"`). Conditions:
  per-timing tests on a blocking double, one product-sink cancel-during-close test, no edit to `encode.py`, watchdog
  joined, V16 stamps kept. **Owed at WP3.14's accept: MINOR DR row on the sink's phase write and abort docstring
  window (trigger: next touch of `encode.py`).** Cell 3: 123K at R1; A R1 0/2/6 all in envelope; footage V4 leg SAME;
  `-m "not footage"` 4864 / 10 skipped / 2379 s.
- **WP3.20R ACCEPTED** by gen 14 2026-10-27 09:46Z at main dbb5858 (record `docs/proofs/wp3.20r-accept.md` with the lane
  head-to-head table; candidate `wp3.20r-mc` 3d01da3 = `wp3.20r` 32d30dc on base 528d865; A = Claude opus/high R1
  0/0/3+3 terminated; B of record Claude clean 5 advisories; Codex B head-to-head clean 2 minor 1 advisory; candidate
  full pytest 4,894 / 2 / 2786 s = main's figure by code identity over the owned files). **CHARC QA CONFIRMED (static,
  msg `d4130a37`):** patch-id 01c1b13a on the author range and both candidate ranges; ff-ancestor; owned files identical
  across reviewed/tested/merged trees; 0 CR; both B evidence sets md5 OK and assertions OK (Claude JSON: is_error False,
  modelUsage claude-opus-5-5, VERDICT anchored; Codex: banner, 0 ERROR, 18/18 succeeded, VERDICT anchored); static and
  harness 379 at this seat. Register e7fef3d: DR-53 (mechanism amended), DR-54, DR-55 CLOSED; DR-61 NEW.
- **CALIBRATION RULED 2026-10-27 ~09:50Z (HD-1 amended; design pass 4.3a): the Codex lane STAYS for the sonnet-high
  class** (A rounds 1 vs 1; B-upheld blocking 0 vs 0; no lock violation; 0 STOPs; 0 reverts). Pace tiebreak resumes
  after the pair. **Codex depth reading PINNED** (pass 3.3): `last_token_usage.input_tokens` of the last request in the
  session rollout jsonl, NOT the cumulative `tokens used` footer (WP-T4 turn 4: 536,544 footer vs 284,234 depth).
  Harness item DONE 17:40Z: `codex_cell.py turn` prints `depth_input_tokens` / `context_window` (`read_depth`; harness 382 OK; live reading 284,234 / 475,000 on the WP-T4 session).
- **WP-T4** (Codex, depth 284K, past evaluation): rung 3 done, zero violators, diagnostic parallel leg 3,882 passed in
  358 s (peak RSS 6.8 GB); E1 failed its bound serially in the sandbox (quiet-seat probe first; DR-58 (c) trigger
  fires if it fails quiet too: widen with reason, no skip). Rung 4 = TWO rounds (Q7), exclusive windows while WP3.14 is
  parked; OPEN/CLOSE to me. Session plan approved: under ~350K for rung 4, fresh session for report and reviews.
- **WP3.14 R2** (orchestrator `4f38492340043510`, 10:18Z): F1 (b) built c3a2fc9 meeting the five conditions; A R2 (Codex)
  1 MAJOR + 7 MINOR; G1 (a) KeyboardInterrupt/SystemExit skipping the post-close check ruled NOT A DEFECT by the
  orchestrator, **CHARC UPHELD** (unconditional = Exception or report, never BaseException; cleanup holds by repro);
  loop TERMINATES at R2; G3-G8 cleanup once. Cell 3 at 255,161: cleanup + report, then fresh cell 4 for the V16 rows
  and the return report. Host order agreed: E1 quiet probe -> WP3.14 V16 windows -> WP3.14 candidate gate -> WP-T4
  rung 4 (two rounds). OPEN/CLOSE per block come to me.
- **WP3.14 B pass 1 BLOCKED** (orchestrator `cc86ea6856e566a7`, 10:40Z; candidate `wp3.14-mc` b830412 = dc76d92 on
  dbb5858, patch-id 82236c64; Codex B 167,472 tokens): B1 MAJOR split: (a) cancel recognised from `progress.cancelled()`
  FIXED in owned code; (b) `analysis/engine.py:494-497` bare `close()` in a `finally` replaces the original failure --
  **CHARC GRANTED a one-line guarded-close fix in engine.py NOW (DR-20 (6) pattern), five conditions, no DR row**;
  B2 (V16 rows owed) declined as sequencing, upheld; B3 (raising progress after commit) and B4 (Fraction-exact
  QUALITY_RATIO) fixed. Cell 3 retired 302,881 at dc76d92; cell 4 `wp314-cell4` (38K) remediates then V16 rows.
  WP-T4 E1 quiet-seat probe PASSED (DR-58 (c) trigger not fired). Next: B pass 2, V16 exclusive blocks (OPEN/CLOSE to
  me), candidate full suite, WP-T4 rung 4.
- **WP3.14 ACCEPTED** by gen 14 2026-10-27 18:48Z at main ba6e923 (record `docs/proofs/wp3.14-accept.md`; candidate
  `wp3.14-mc` c9da9ce = `wp3.14` 1449a77 rebased twice; full pytest 5056 / 2 / 4568 s on 2b27454 = main's figure by code
  identity, `src tests tools` differ only by my harness test). **CHARC QA CONFIRMED (static):** patch-id 9ef47483 on all
  three ranges from the true bases; c9da9ce ff-ancestor; record docs only; footprint 16 owned files + granted engine.py
  block; interfaces / seam / naming / safe_write / pyproject / uv.lock / conftest / fixtures untouched since 9753b7b;
  17 blobs 0 CR; B pass 1 and 2 md5s OK, assertions OK (strict succeeded 19 / 36, VERDICT anchored 12166 / 14532),
  footage mentions = prompt withheld line + brief echoes; ruff / format 237 / mypy 136 / harness 382 at this seat; no
  suite (WP-T4 rung 4 windows next). **Register (this commit): DR-48, DR-28 CLOSED; DR-35 (b), DR-57 (b)(c), DR-20 (7)
  CLOSED, DR-35 (a) mechanism amended, DR-57 (a) ADDRESSED; NEW DR-62 (GUI recompute vs export, WP4.3), DR-63 (sink
  phase write window, next encode.py touch), DR-64 (N6 body erratum, owner's word).** Worktrees `wp3.14`, `wp3.14-mc`,
  `orch-state-g14` released. WP3.21 brief: orchestrator drafts from the V16 baseline, I approve FINAL.
- **WP-T4 RUNG 4 COMPLETE; WINDOW CLOSED 2026-10-28 00:43Z** (msgs `7bb7c019595a6e24`, `23cd376ed4fda4dd`,
  `837716adc8e9d3a8`). **No window open; seat free.** Head dd49a15 on ba6e923. Round 1: BASELINE 4,564.80 s / PARALLEL
  497.30 / SERIAL 3,335.36 (P+S 3,832.66, -16.0 %); round 2: 4,349.92 / 493.54 / 3,372.59 (P+S 3,866.13, -11.1 %);
  P+S differ 0.87 % = NO ROUND 3; counts 4,032 + 1,046 = 5,078 both rounds; 0 failures = 0 violators; GPU rise
  903 / 911 MiB in the non-GPU leg (import-time context FINDING, no marker change). D3 durations leg (diagnostic,
  junit under work/): serial wall 3,331 s; four WP3.14 / WP3.10 real-clip and synthetic-5.3K export tests = 2,276 s =
  68 % of the serial leg (`test_v4_synthetic_5k3_8_7_clip` 871 s the largest). **Owed at WP-T4's accept (my QA):**
  CLAUDE.md Conventions line (two-leg command, median P+S ~64 min vs baseline ~74 min with the spread); HD-1 third
  data point (Codex lane); NEW register row on suite-cost concentration (lever = the synthetic 5.3K clip's frame
  count and a shared GX011627 export fixture; trigger WP3.14 / WP3.10 next touch or an owner-commissioned suite-cost
  pass); orchestrator writes the fill's GATE_CHECKS line. Next at the orchestrator: Codex turn 6 (tabulation by
  marker, report, gate text, ledger; same session, depth 95,253), Reviewer A Claude opus/high, final two legs in
  their own window, B at its seat, accept; then WP3.21 dispatch (brief FINAL 43cc1ed).
- **WP-T4 turn 6 committed 5e6a8d3** (tabulation: medians P+S 3,849.40 s, -16.04 % / -11.12 %; D3 by marker gpu 586 /
  1,843 s, footage 17 / 2,001 s, gui 441 / 68 s, slow 20 / 2,932 s; de-duplicated 3,326.96 s = D3 wall within 0.13 %;
  gui is NOT the cost; E1 resolved; GPU finding stands). **Reviewer A R1 (Claude opus/high via `codex_cell.py review`,
  `wp-t4\r1\`): NO_NEW_CRITICAL_MAJOR, 6 minor 5 advisory; loop ENDS** (one round + one cleanup, my cap). Rulings
  (msg 22ab3c5a): Opus-high in place of the FAST tier ACCEPTED (ledger line, not a precedent); m2 stale lock up to 15 min
  = stated limit, message names the lock path; m5 worker-side refusal test if cheap else MINOR row; m1/m3/m4/m6
  fixed in cleanup turn 7. **Turn 7 committed 08e87f5** (report + ledger only; m1/m3/m4/m6 fixed, gate text runnable
  with collect-only set checks and --basetemp under work/; m2 LIMIT, lock messages name the path; m5 NOT taken = my
  MINOR row at the accept; CLAUDE.md pointer median P+S 3,849 s ~64 min; depth 212,913).
- **WP3.21 STOP RULED 2026-10-28 (cell 3 yield 5, msg `efd136c45e8f3940`): #2 (`3da1e6f`) and the #3 draft break plan 8.1 frame
  rule 5 (`test_core_deps::test_static_rule_over_src`: cupy imported in `color/samples.py`, `io/video/decode.py`, `analysis/proxy.py`).
  RULING (R) = AD-29:** device extension methods on `CoreBackend` only; one `runtime_checkable` Protocol per consumer with a
  satisfaction test; `device_backend=<backend or None>` replaces `device_frames=True`; host path = default and structural
  fallback; `color/samples.py` back to base; `*_deps` tests in the light set; oracle re-run on GX011627 + synth 4K in a new
  window BEFORE #3; WP4.2 row at the accept binds `device_backend=<GPU backend>`. Cell 3 STOOD DOWN at 251,077 (ledger RESUME
  HERE + draft patch `work/wp3.21/c3-draft-3-device-block-mean.patch`); **cell 4** (opus-high) takes the ruling. No window open.
  **Cell 4 DISPATCHED 07:31Z** (msg `94c72e704d83c247`) from `wp3.21` e6d27a0 (cell 3 handover, final 265,087), AD-29's eight
  conditions in its prompt; order #2 rework -> oracle WINDOW -> #3 -> unchanged. Brief names the four layering tests (b26b051;
  CRLF blob corrected within a minute by e6f7193; 0 CR at HEAD, verified at my seat).
- **EXCLUSIVE WINDOW OPEN 2026-10-28 ~08:14Z: WP3.21 INTERIM 2 (#1+#2+#3, device frames ON; ~30 min, head 0ed0672): export_bench
  GX011627 cold c3 (development timing), then oracle GX011627 c3, synthetic 4K, GX011627 ancuti2018, all `--require-tier1`**
  (msg `e09002e4eb2349ec`). **NOTHING HEAVY AT THIS SEAT until CLOSE.** Non-TIER1 = STOP. Cell 4 yield 8, depth 236,806: `05ee507`
  #3 under AD-29 as amended (`block_sums` float64 host sums or None at the bound, reductions only, no frame-sized temporary;
  `AnalysisDeviceBackend` Protocol; host fallback on None / k==1 / no extension; engine +2 lines); `6e504fe` export_bench records
  the configuration header; 21 tests (Protocol pair, device == host bit for bit and proxy byte for byte at 4K k4, 5.3K k5/k8, k2 odd
  edges, k1, 8/10-bit; planted NaN/inf/1.5/1e-30/1e-12 -> None, host bytes); light 1050 passed. CAVEAT: WP2.3 samples 320x180 =
  k 1, so k > 1 is pinned end to end ONLY by this window. Seat plan AGREED: cell 4 runs and records the window, writes RESUME HERE,
  stands down; **cell 5** takes the 4K micro-timing onward.
- **WP3.21 AD-29 #2 ORACLE WINDOW CLOSED 07:56Z: reworked #2 TIER1 on GX011627 (681 / 0 differing, max abs 0, mean abs 0) and
  synthetic 4K (120 / 0)** (msg `c6afcfc8bacaf5d5`; OPEN `1ec355e68f10ef7e`; head 867d5fb). AD-29 item 6 met before #3. The io.video
  Protocol pair asserts both directions (`test_wp321_device_frames.py:82` / `:92`); the analysis pair comes at #3. **No window open;
  seat free.** Cell 4 on #3 (tier 1 or STOP). **Cell 4 STOP at yield 7 (164,381) on AD-29 item 1 "block sums with their quantise":
  orchestrator ruled (a) at its seat, UPHELD and AD-29 amended: `CupyBackend.block_sums` returns float64 HOST sums (or None when
  the exactness bound fails); `_divide` and `quantise` stay single-sourced in `analysis/proxy.py`; None -> host reduction, same bytes;
  tests = Protocol pair both directions + planted bound failure giving identical bytes** (msg `f1cfe0996a95d0df`). Cell 4 yield 6, depth 148,982:
  #2 reworked under AD-29 as follow-up commits (`DeviceFrameBackend` Protocol in `decode.py`; `device_backend=None`; samples.py
  identical to d1e4537; interfaces/ no diff; 4 layering tests 28 passed; light 883 passed; WP2.3 oracle 10/10 TIER1 max abs 0).
  **Orchestrator reading ACCEPTED, AD-29 item 1 clarified: device methods on `CupyBackend(CoreBackend)`, not the shared base
  (NumpyBackend subclasses it too); the satisfaction test asserts CupyBackend satisfies and NumpyBackend does not.**
- **WP3.21 #2 ORACLE WINDOW CLOSED 07:17Z: TIER1 on GX011627 (681 frames, 0 differing, max abs 0; 1,362 analyze calls, proxies
  equal; sink_devices [cuda:0]) and synthetic 4K (120 / 0)** (msg `3a83d79a2b8fb7c9`; OPEN was `cb4ed7af11daf48a`). Oracle walls
  408.0 s vs #1 587.2 s and 89.0 vs 117.6 (development evidence, NOT V16). **No window open; seat free.** Ledger 29eff29. Cell 3
  on #3 (device block mean, tier 1 or STOP); next windows: #2+#3 interim, 4K micro-timing, each requested separately. Cell 3 at `wp3.21` 7696467,
  depth 192,330 at yield 4: `82c6d38` Q-R6 as ruled (entry sized via IF-7 `lookup(key).size_bytes`; extrapolation added to the
  D87 re-check; planted refusal before any render); `3da1e6f` #2 device frame conversions (`FFmpegVideoSource(device_frames=False)`
  opt-in; sink refusals unchanged; **DR-63 CLOSED at the accept** on this evidence; 25 tests; WP2.3 oracle TIER1 GPU + force_cpu;
  +0.13 GB at 4K, ~6.9 of 8 GB card at 5.3K before FFT). Orchestrator ruling `hw_decode = backend.device != "cpu"` (IF-5 carries
  no backend) ACCEPTED. **QUERY RULED (a) (my msg ack-devframes): task 10 V16 figure of record = `--device-frames` ON; record
  names the configuration; OFF row only if it fits the same window; default stays False (Q-R2). OWED AT WP3.21's ACCEPT (mine):
  register row binding WP4.2 to construct the product source with `device_frames=True` for GPU jobs, with a test; DR-63 CLOSED.**
- **ORCHESTRATOR GEN 15 = `clearwater-orchestrator-20261027-2047`** (launched 06:47:03Z from state 2e0ba30; gen 14 signed off
  at ~330K, msgs `02fcea331c6990a9` + cross-session note). **All cues go to gen 15 now**; re-read `comms/.launch-sessions.json`
  before every cue. Gen 15 dispatches cell 3 (Q-R6 first, then #2, #3, 4K micro-timing, task 6,
  task 7, reviews, suite, task 10) from ledger RESUME HERE `106b29f` (branch `wp3.21`, 13 commits on d1e4537; gen 14 corrected the count).
  **Gen 15 ONLINE 06:49Z** (msg `df928159ff567231`, picked up at 2e2f7e6, state 0f66ba2); **WP3.21 CELL 3 DISPATCHED**
  (`wp321-cell3`, opus-high, from `wp3.21` 106b29f, depth 0; my four readings + AD-1 breach = STOP rule in its prompt; order
  Q-R6 -> #2 -> oracle window -> #3 -> interim/micro-timing windows -> task 6 -> task 7 -> A -> suite -> task 10 last). No window
  open; the first WINDOW REQUEST is posted to me as OPEN before the grant. My ack msg e2eee35a.
- **WP3.21 INTERIM 1 CLOSED 06:43Z (msg `dad1555e109d85c7`): #1 OVERLAP MEETS D106's INTERIM AT 4K.** GX011627 cold c3
  0.8100 s/frame = **24.28 min/min** (WP3.14 1.061-1.065 = 31.8-31.9; -24 %); median 0.7735, p90 0.8208, max 2.858; lead
  18.8 s (3.4 % of 551.6 s); peak RSS 3,987 MiB, graphics 2,877 MiB; frames phase 0.778 vs serial frame path 0.714 (~0.06
  contention from the analysis thread, #3 should remove most). Oracle TIER1 x3 (GX011627 c3 681 frames 0 differing; synthetic
  4K 120 frames; ancuti2018 lead 91, 2,043 analyze calls equal). ONE run; figures of record = task 10 re-measure, made LAST.
  Cell 2 STOOD DOWN at 310,465. **No window open; seat free.**
- **(history) WP3.21 interim 1 window ~06:05Z** (msg `7c702bf6ba630948`). Cell 2 built #1: `333ad3f` (engine.py + export.py + `tests/test_wp321_overlap.py`), `62f1da6`
  (`export_bench --subdir`), `613024d` ledger; `analysis_job(stream=True)`, `RenderBeforeFinalError` by name, lead derived
  61 / 91 / 127, sink opens after the lead, analysis thread joined in `finally`, module `_LOG` (import-logging debt closed);
  21 new tests, 14 fail on base; existing WP3.14 / engine / export / GUI tests unchanged and green; oracle WP2.3 10/10 TIER1.
  Cell 2 depth 287,974 -> after this window it records results + handover and yields; **cell 3 re-seats for #2 and #3** (agreed).
  Q-R7 (lead marked by the analysis->open transition; task 10 reports end-to-end s/frame + lead, tool-side stamp) CONCURRED.
  **Q-R6 RULED (my msg ack-qr6): ACCEPT the D87 re-check after the LEAD, plus a cheap addition in `export.py`: measure the
  cache entry's growth over the lead, extrapolate per frame over the remaining frames, add it to the re-check's required
  figure (no `disk_space.py` change, no spec change); a planted small-free-space test shows the refusal before the first
  rendered frame. If the cache entry cannot be sized in one call = STOP to me.** Baseline for the interim: WP3.14 cold c3
  1.061-1.065 s/frame.
- **WP3.21 TASK 1+2 WINDOW CLOSED 05:18Z; ROUND 0 RECEIVED (`defa2a9`, 7 commits on d1e4537, no product code); CELL 1 STOOD
  DOWN at depth 359,040 (orchestrator's CLOSE post said 285,003, corrected); CELL 2 re-seats from R0.9 for the overlap build**
  (msgs `b8ee40b1c815008c`, `3e8434f28064c2b7`). **No window open; seat free.** Breakdown GX011627 c3: analysis 0.299 s/frame,
  `block_mean` HOST float64 = 50.9 % of the pass, device bound 20 %, SM 210 MHz idle clock (the GPU-idle cause NAMED: ~80 % host
  work starves the card, which also slows stage-1 analyze 46 ms vs 8 ms at boost); frame path 0.714 s/frame, render 70 %;
  replica == engine (2,724 records, 681 proxies); 13/13 oracle CONTROLS TIER1, refs 9.8 GB under work/wp3.21/oracle/. 33-min
  host-idle gap inside the window (cell idled on a background notice) -> recipe rule added (foreground poll-wait). Round 0 order:
  #1 overlap (lead derived 61 c3 / 91 ancuti2018), #2 device frame conversions (decode/encode/samples granted, DR-63 closes),
  #3 device block mean (exact float64 sum, proxy byte-identical), #4 FFT Gaussian (tier 2); #1-#3 projected ~0.53 s/frame
  = ~16 min/min (meets interim 25). Orchestrator's Q-R2..Q-R5 rulings CONCURRED. **Q-R1 RULED (my msg): the FFT gate lives in
  `core/backend.py`'s `gaussian_blur` implementation, BOTH backends, min(H, W) >= 1080 AND sigma >= 32 px (sigma threshold
  provisional until the micro-timing, never lower); IF-2 ABC untouched; a test derives the largest proxy short side from
  `analysis/proxy.py`'s rule and asserts the gate clears it; a planted analysis-sized blur (short side 1079, sigma 270) is
  bit-identical to the direct path; FFT vs direct max abs <= 1e-5 on [0,1] float32 at 1080p and 4K; AD-11 end to end.**
- **(history) EXCLUSIVE WINDOW OPEN 2026-10-28 ~03:50Z: WP3.21 task 1 breakdown (GX011627 c3, ~20-25 min) + task 2 oracle base (~55-60 min,
  13 CONTROL compares `--require-tier1`, a failing control = STOP)** (msg `013f59e50f2d97d2`). **NOTHING HEAVY AT THIS SEAT until CLOSE.**
  Yield 1: `wp3.21` 3 commits on d1e4537 (`a586be2` breakdown 11 tests, `c72507f` oracle 14 tests, `bc7b58e` ledger), 0 CR; dry-run
  residual 0.01-0.05 %, replica == engine bit for bit; cell depth 269,898 at yield 1 (past evaluation): orchestrator's plan = this
  cell runs the window and writes round 0, then RE-SEAT from the ledger for the build; I concur. Q-a (records under the owner's
  `work/wp3.21/`) and Q-b (synthetic 4K clip generated once, sha256 recorded, 120 frames, GPU only) AGREED. **Q-c RULED: the c3
  composed lead is 60 frames (+1 at_end) at 29.97 fps, DERIVED at run time; my 90 double-counted WP3.11's cumulative figures;
  corrected in AD-7 and the brief (dated); planted test = lead short by ONE at the derived bound.** (msg `8719064da5137bc3`): `implementer-opus-high` cell 1 (`wp321-cell1`), worktree
  `.worktrees/wp3.21` on d1e4537, brief FINAL 43cc1ed, both nets Codex `gpt-6.1-sol`/high (A at the cell's seat, B at the
  orchestrator's). First yield = task 1 WINDOW REQUEST (GX011627 breakdown; task 2 base reference may ride as a second leg);
  orchestrator posts OPEN/CLOSE to me. **No window open now; seat free.** Round-0 design table is a YIELD; open choice = STOP.
- **WP-T4 ACCEPTED main d1e4537 (patch-id of record 0984fd4b); CHARC QA DONE 2026-10-28** (msg `cdf86fe7f7af3a4c`; record
  `docs/proofs/wp-t4-accept.md`). My QA: patch-id 0984fd4b on `ba6e923..wp-t4`, `f467a20..217f1a0`, and main; ff from f467a20;
  9 package files + record + fill, all 0 CR; frozen interfaces untouched; code identity vs 08e87f5 empty; Reviewer B evidence
  `wp-t4/reviewB/` md5s OK, `review.json` is_error false, 76 turns, modelUsage `claude-opus-5-5`, one VERDICT line
  NO_NEW_CRITICAL_MAJOR; ruff / format 238 / mypy 136 / harness 382 OK at my seat. Fill GATE_CHECKS = the two-leg gate with my
  timing-bound qualifier verbatim. **Owed items WRITTEN:** CLAUDE.md Conventions Tests line (two-leg command, median ~64 min vs
  72-76); HD-1 third data point in `docs/decisions.md`; register DR-58 (c) CLOSED (E1 slow), NEW DR-65 (suite-cost concentration,
  four export bodies 68 % of the serial leg), NEW DR-66 (m5 MINOR, worker-side refusal unreachable in envelope). Worktrees
  `wp-t4`, `wp-t4-mc` released (branches kept).
- **WP-T4 final legs green; window CLOSED 2026-10-28 02:32Z** (msg `7d52d1b2d7af76a2`; OPEN was `3c3394e7d2adc0d2`,
  01:27-02:32Z). **No window open; seat free.** Head 08e87f5: PARALLEL 4,031 / 1 skip / 451.96 s; SERIAL 1,036 / 10 /
  3,405.58 s; counts 5,078; 0 failures; P+S 3,857.5 s (between the rounds' 3,832.7 and 3,866.1). Sampler: peak RSS
  6.91 GB, min available 6.78 GB, GPU rise 878 MiB (same import-time finding). Code identity: main moved docs-only
  since ba6e923 (`git diff --stat ba6e923 main -- src tests tools pyproject.toml uv.lock` empty), so these legs are
  the suite gate for the rebased candidate (orchestrator re-confirms after the rebase). Next at the orchestrator:
  `wp-t4-mc` rebase + patch-id + static + harness gate, Reviewer B (Claude pass at its seat), accept with the fill's
  GATE_CHECKS edit; then my QA (CLAUDE.md line, HD-1 third point, suite-cost row, m5 row, DR-58 (c)).
- **WP-T4 Reviewer B (Claude pass at the orchestrator's seat, Opus high, read-only; `wp-t4/reviewB/`, `review.txt`
  md5 f544e951...) = NO_NEW_CRITICAL_MAJOR, 4 minor 4 advisory** (msg `530d5027f50a7f2e`). Candidate `wp-t4-mc` ed7eca9
  = 7 commits on 7f4b80d, patch-id 3aafebff pre/post rebase, code diff vs 08e87f5 empty, 9 files, 0 CR, ruff/format/
  mypy/harness 382 OK. Lock and guard claims REASONED (sandbox refused work/ writes); A executed them. Adjudication
  ACCEPTED (my msg ack-revb): B1 -> RAISED GPU finding; B2 complete parallel-leg bound list as WATCH (encode_bench
  `1.0<=strays<1.5`, `<1.0` tightest); B3/B4/B5 -> GATE_CHECKS (quoted -rs skips vs previous gate, PYTEST_ADDOPTS
  unset + collection diff vs main, exit 0 + count match, run from Git Bash); B6 under m2 limit; B7/B8 docs-only turn 8
  (new patch-id of record; identity diff must stay empty). **Fill rule ACCEPTED with qualifier:** new wall-clock bound
  in a parallel-leg test = `slow` with a reason naming the bound (timing isolation, not duration); generous sanity
  ceilings (>=10x expected, anti-hang) exempt; NEW tests only. Both A and B = Claude Opus high (lane rule met). **Round 1 CLOSED 21:29Z** (msg
  `7bb7c019595a6e24`): BASELINE 5,067 passed / 11 env skips / 4,564.80 s; PARALLEL 4,031 / 1 / 497.30 s; SERIAL
  1,036 / 10 / 3,335.36 s; counts hold (5,078); 0 failures = 0 violators; P+S 3,832.66 s = -16.0 %. Sampler: peak RSS
  6.97 GB, min available 7.05 GB, GPU rise 903 MiB (the import-time context finding). **Reading sent for the report:
  the serial leg is 73 % of the baseline wall, so the two-leg suite is bounded by the marked set, not by workers;
  the report carries the serial wall BY MARKER and the ten longest serial tests; shrinking the set is a follow-on,
  not WP-T4's.** Third round only if the two P+S totals differ by more than 15 %. Turn 5: collection 4,032 parallel + 1,046 serial = 5,078 disjoint and exhaustive; 193
  IDs added since 2aca60e, 4 renamed; no violator; E1 the only exception; +1,036 MiB GPU rise in the non-GPU leg stays
  a FINDING (import-time probe), no marker change. Codex depth after turn 5 reads 95,253 / 475,000 (compacted inside
  Codex; the pinned reading is the live figure). WP3.21 brief FINAL at 43cc1ed (my rulings verbatim, 0 CR).
- **WP3.21 brief APPROVED FINAL** (draft 84b793c; my rulings msg in the Rulings section; AD-7 READING and the oracle
  tiers recorded in `docs/decisions.md`): Q1 grants as recommended (`memory.py` only by me; `encode.py` grant closes
  DR-63); Q2 AD-7 reading YES with the COMPOSED-reach lead (90 frames c3) and one thread per decoder; Q3 two tiers,
  records and proxy bytes tier 1 ALWAYS (the AD-5 1e-3 leg struck), Gaussian 1e-5 CONFIRMED; Q4 FFT of the same
  truncated kernel with scipy-`reflect` padding, float32, IIR excluded; Q5 a miss = YIELD to me (follow-on or WP5.2
  figure; D106 owner's; D109 no fallback); Q6 tool not timers, 5 % check on summed MEANS; Q7 whole V16_PLAN; Q8 DR-40
  (b) stays OPEN, ask at round 0 if >1 %; Q9 memory budget, formula change = STOP; Q10 interim windows. Dispatch
  `implementer-opus-high` after WP-T4 rung 4; both nets Codex. Owed at its accept: AD-11 tunable note stands; the
  N6 figure is WP5.2's (AD-21).
- **WP-T4 rebased onto ba6e923 (f8b8f4b, patch-id 525a84c8 unchanged): NO OBJECTION** (rung 4 measures main's suite,
  ~160 more tests incl. WP3.14's libx265 sinks; diagnostic parallel leg not a figure of record; Codex turn 5 accounts
  for test IDs by collection). Rung 4 round 1 OPEN comes as its own post; nothing heavy here while OPEN.
- **WP3.14 V16 BOTH BLOCKS CLOSED** (block 1 11:33-12:57Z, msg `8ce78d1c60253f08`; block 2 GX011625 13:05-17:25Z,
  CLOSE 17:26Z msg `7439db035704c44e`). **Seat free; no window open.** Block 2 row: 14,938 frames, 1.0429 s/frame =
  31.26 min/min MISS (within 2 % of GX011627 cold); analysis 4,638 s = 29.8 %; frames median steady 0.755 -> 0.726
  over 4 h; GPU 82/93 C; RSS 2.9 / GPU 2.4 GiB; close -> committed 1.87 s. **GPU at idle clocks (SM 210 MHz,
  5.1 W) through the 77-min analysis phase: WP3.21's first question** (where the analysis pass spends its
  0.31 s/frame; decode / host statistics / upload). Next at the orchestrator: cell 4 report fill + FINAL return,
  candidate full suite (non-exclusive; I run nothing heavier than the harness gate meanwhile), accept, CHARC QA,
  WP-T4 rung 4. Block 1 rows: GX011627 c3 cold 1.061-1.065 s/frame = 31.9
  min/min MISS of D106's interim 25 (analysis pass ~30 %, frames ~0.74 s/frame); c3 warm 23.2 meets; ancuti2018 cold
  21.6 meets; c3 libx265 cold 35.6 (14 s close); synthetic 5.3K 8:7 cold 136, 6.2 GiB RSS / 6.0 GiB GPU. **CHARC RULED
  (msg e1711557): the miss is WP3.21 DATA, not a stop, not a defect** (V16 "tunable"; D106 names WP3.21 and the WP5.2
  re-measure; brief item 10 "best effort", Done = row recorded). Accept record states the miss plainly; the split,
  the libx265 and 5.3K rows and the two "Not carried" warnings (D86 as designed) go into WP3.21's brief baseline.
- **WP3.14 B pass 2 BLOCKED (1 major), adjudicated AT THE GATE, CHARC UPHELD** (light checks: reviewB2 md5s OK,
  assertions OK, VERDICT BLOCKING anchored; candidate `wp3.14-mc` 2e9fd35 patch-id f21b6411 on 9753b7b..2e1dc11 and
  52ee9e2..2e9fd35; footprint owned + granted engine.py block). F1 MAJOR: photo path had no cancel check between the
  Writing report and the writer; gate fix bcc7fa3 verified by execution at the orchestrator's seat (pre-fix swap fails
  both tests). F2 D87 batch test pinned; F3 clean-path close-guard test; F4 report scope line. No B pass 3. Note for the
  record: the engine.py guard imports logging inside the except block (honours the one-block grant); style debt for
  WP3.11's next touch, no DR row. Next: V16 blocks, candidate full suite, accept, CHARC QA.
- Gen 13 `-2029` ROLLED 07:51Z at ~345K (state 930a78d, FYI `080ce65fb13768e9`): WP-T3 cell DONE
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
