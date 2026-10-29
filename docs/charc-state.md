# CHARC -- Current State (the read-me-FIRST pointer)

> **Convention (CHARC-authored harness-architecture).** This file is the SINGLE
> current-state pointer for the director (CHARC). It is **OVERWRITTEN each
> session** -- it always reflects only the live now, never accumulated history.
> Narrative lives in `git log -- docs/charc-state.md`. **The bootstrap reads THIS
> file FIRST**, then the charter. Every fact below carries the method that
> re-verifies it; a successor re-runs the method rather than inheriting the fact.

---

### RESUME HERE (CHARC generation 6 `clearwater-charc-20261028-1443`, fable/medium, ONLINE 2026-10-29 00:45Z from main 47f270f; gen 5 `clearwater-charc-20261028-0647` rolled ~00:45Z at ~402K)

- **Gen 6 pickup facts:** bash gauge 45 ms; inbox 0 unread at pickup; announce posted to the orchestrator (gen 17, shell-busy in the WP4.1 gate) with ONE cue; the two register scripts copied from gen 5's scratchpad (18c10a55...) into this session's scratchpad (6687b6c9-eacd-4ffc-995e-51c9195391d1) as `edit_register_p4a.py` (drop its DR-65 block before running: already applied at 3114d23) and `edit_register_p4b.py`.

- **Orchestrator = gen 19 `clearwater-orchestrator-20261028-1931`** (launched 05:31Z by gen 18, which rolled at ~405K, state b394e7b;
  ONLINE 05:33Z at b394e7b, msg `ad06ad7d0f6f044f`, gauge 53 ms; gen 18 was `clearwater-orchestrator-20261028-1555`; re-read `comms/.launch-sessions.json` before every cue; every post
  gets ONE SendMessage cue). Subjects under 120 chars (the poster refuses longer; two refusals this generation at 123-125); bodies via
  `--body-file`; edit docs with a scratchpad Python script (`newline="\n"`); `tr -cd '\r' | wc -c` = 0 before every commit; commit by
  pathspec; never an uncommitted edit left in the main tree (hazard 7); HOLD MAIN when the orchestrator asks (no commit, state included,
  until its ff post).
- **WP4.1 ACCEPTED main `f30e00e` (2026-10-29 ~01:36Z; msg `9cc6790b39144767`; record `docs/proofs/wp4.1-accept.md`). CHARC QA
  CONFIRMED (static, this seat ~01:50Z):** patch-id 8ff10e7b on `3aa3c51..3b8b43b` as the record says; code-only patch-id cafa7c45
  equal on the author range and on `d1d812b..f30e00e`; `git diff 0986b8d f30e00e` over src tests tools pyproject uv.lock EMPTY (= the
  Reviewer B pass-2 tree); footprint 13 files all owned or granted (S4 `tests/test_app_deps.py`); interfaces / export_seam / fixtures
  untouched; 0 CR in every changed blob; Reviewer B md5s recomputed = record (pass 1 bc970e45..., 23 succeeded; pass 2 ab4c5c69...,
  31 succeeded; gpt-6.1-sol banner; VERDICT anchored; pass-2 Reconnecting at stderr 4243 before the first turn = recovered retry);
  ruff / format 259 / mypy 141 / harness 382 OK (1 skipped) here. No suite at this seat (the orchestrator's own two-leg gate 4486/1 +
  1126/1 is the figure of record; the orchestrator is rolling at ~385K and waited only on this QA). **Register rows WRITTEN: DR-75
  (H1 nclx-only P3 preview, BINDING WP4.3), DR-76 (G5 writer `profile` vs `import_preset`, WP4.3), DR-77 (`import_preset`
  OverflowError, WP4.3), DR-78 (B2-1 stream syntax in planned output FILE names, BINDING WP4.2), DR-79 (B2-2..B2-4 minors, WP4.2).**
  Worktrees `wp4.1`, `wp4.1-mc`, `wp4.1-mc2`, `wp4.1-mc3` may be removed by the orchestrator (logs copied first; branches kept).
- **Owner direction 2026-10-29 (Codex lane balance; memory `clearwater-codex-lane-balance.md`):** tally at this seat = Codex
  implementer 20 turns / 3 packages (WP3.20R, WP-T4, WP-T5) ~8.7 M tokens vs Codex Reviewer A 109 rounds + Reviewer B 54 passes
  ~28 M. Owner: monitor and evaluate before changing; wants to lean on Codex more for development to equalise burn, never at the
  expense of quality. No lane-rule change. At each commission / brief revision CHARC names the packages eligible for the Codex lane
  under the existing rule and reports the Codex development share with the pace readout.
- **WP4.2 REVISION 1 RULED 2026-10-29 02:13Z (my post ruling-wp42r1, answering query `3511951ee31e51c9`; branch `brief-wp4.2r`
  f794033): R1-Q1 (a) predicate (i) factored into a named helper applied to `final_output_path` (ONE predicate); R1-Q2 (a) grant of FOUR
  `np.array_equal` sites (photo_path 514/528, v8 74 AND 162); R1-Q3 (a) mixed pin edited in place; R1-Q4 (a) round 0 reads `cache/store.py`,
  Limit + my register row at WP4.2's accept if a reparse-point entry is not refused; DR-79 (b) NOT REPRODUCED at my seat (self-loop
  junction: `resolve()` returns, no raise) -> defensive wrap + monkeypatched test, CLOSES as 'defensive; not reproduced'; R1-Q5 (a)
  **WP4.2a runner hardening on the Codex lane** (existing lane rule, paces 0.424 vs 1.313; owns `tools/headless_export.py` + new
  `tests/test_wp42a_runner_hardening.py` + the four lines; nets A and B = Claude passes; standard two-leg gate in a window) concurrent
  with WP4.2 ROUND 0 only (opus-high); WP4.2's build waits for WP4.2a's merge with a CAP = WP4.2 round-0 yield + 3 h, then WP4.2a
  STOPS at a committed head and rebases after. **Brief FINAL on that word** once folded in. Owed by me: DR-78/79 trigger rewrite +
  CLOSED at WP4.2a's accept; WP4.2's DR-67/71/73/74 rows and the cache row at its accept. Owner told: the split is the existing
  lane rule operating, not the balance change under evaluation.
- **WP4.2 + WP4.2a BRIEFS FINAL on main `aa4761b` (02:22Z, msg `26e7661fdaa21ab3`; `20ee254` revision 1, `aa4761b` FINAL + NEW
  `docs/briefs/wp4.2a-brief.md`, Codex form, read in full here, four orchestrator choices concurred: STRONG tier; (i) file check on the
  configured-footage path only; RefusedRequest and ValueError skips; real-ADS case kept where the OS allows). LIVE CELLS (OCCUPIED
  worktrees): **WP4.2a** Codex `codex_cell.py turn 1` in `.worktrees/wp4.2a` (branch `wp4.2a`, base aa4761b; evidence
  `clearwater-review-evidence\wp4.2a\cell\`; turn 1 = read-and-map + round-0 note, yields); **WP4.2 round 0** `wp42-cell1` opus-high in
  `.worktrees/wp4.2` (branch `wp4.2`, base aa4761b; ROUND 0 ONLY, ledger-only commits; Y1 = table + R1-Q4 cache finding). Paces at
  dispatch Codex 0.414 / Claude 1.331. CAP clock = WP4.2's Y1 + 3 h (orchestrator decides, tells me). No window open; the orchestrator
  posts one before WP4.2a's two-leg suite. Owed by me: DR-78/79 rewrite at WP4.2a's accept; WP4.2's rows at its accept.
- **WP4.2 ROUND 0 RULED 02:40Z (query `1286b25667b9ec63`, my post ruling-wp42r0; Y1 02:33:37Z, cell depth 209,438, build goes
  to a FRESH cell; CAP 05:33:37Z):** tripwire APPROVED = additive per-item `"video"` record object {device_backend, frame_device,
  encoder, decode_passes}, schema 1 kept, three conditions (existing fields unchanged; shape documented in the runner docstring +
  report; decode_passes counted from source opens, V17 asserts it); R0-Q2 = (b') expected_frames from probe nb_frames, readable count
  via one packet listing only on a D86 fault, analysis stays io-free; seat rulings concurred (G1 granted on the DR-45 (b)
  reproduction -> DR-47 (a) CLOSES at the accept; R0-Q1 (a), R0-Q3 (a), R0-Q4 (b) one-line app/__init__ re-export, R0-Q5 (a)
  lossless re-encode with decode proof + STOP, R0-Q6 (a)). **R1-Q4 REPRODUCED** (`cache/store.py:573` skips a junction entry at
  discovery; `:660-666` mkdir/write through it; `keys.py:103` is_link uncalled): my register row at WP4.2's accept, trigger the next
  `cache/` touch. WP4.2a: round 0 committed 933e33e, Codex turn 2 = build.
- **WINDOW OPEN 03:19Z (msg `429ac5c6dfecb436`): WP4.2a two-leg gate on `wp4.2a-mc` c4eab41 (six commits rebased onto d5d4b00,
  patch-id 9ca7ffa4 = author range aa4761b..952f31a), ~52 min EXCLUSIVE. NOTHING HEAVY HERE until the release post.** Then Reviewer B
  (Claude pass at the orchestrator's seat), accept, a HOLD ask before the ff. WP4.2a Reviewer A converged R2 (R1 BLOCKING 1 major F1).
  **F1 ROOT CAUSE RULED (my post 03:20Z): DR-80 on main `0f138ff`** = `jobs/naming.py` `OutputPlan.path` (:268) composes the output
  name from the unchecked source stem; `<letter>:<rest>` gives a DRIVE-RELATIVE planned path (reproduced here with pure paths); the
  suffix is validated (:54-75), the stem not. WP4.2a closes the runner route only (parent-of-planned-file check). **Fix = WP4.2b, Codex
  micro-package** after WP4.2a's accept, concurrent with WP4.2's build (disjoint files: `jobs/naming.py` validation + `tests/test_jobs_naming.py`
  + one runner test); nets = Claude passes, STRONG; gate stacked with WP4.2's suite if timing allows (orchestrator's call); BINDING at
  the latest WP4.3. N1 (mixed-separator redaction gap) row = mine at WP4.2a's accept with the DR-78/79 rewrite. Owed at WP4.2a's accept:
  DR-78 CLOSED, DR-79 CLOSED ('defensive; not reproduced' for (b)), N1 row, CHARC QA.
- **WP4.2a ACCEPTED main `3aa25a5` (04:25Z, inside the CAP; msg `a671ac6369c1364d`; record `docs/proofs/wp4.2a-accept.md`); WP4.2b brief
  FINAL `f991254`. CHARC QA CONFIRMED (static, ~04:35Z):** patch-id 9ca7ffa4 on `aa4761b..952f31a` = the record; code-only patch-id
  238bdcc2 equal on the author range and `32099ae..3aa25a5`; `git diff c4eab41 3aa25a5` over src tests tools EMPTY; `src/` untouched;
  7 files (runner, new hardening test file 545 lines, the two WP4.1 test files 13 lines each = the four granted sites only, stricter);
  0 CR; r1 / r2 / reviewB md5s = record (36f0ed68 / 3ef4cca1 / c4e0f9e3; every md5sums.txt OK); ruff / format 260 / mypy 141 /
  harness 382 OK here; no suite here (the orchestrator's gate 4539/1 + 1126/1 is the figure). **Register: DR-78 CLOSED, DR-79 CLOSED
  ('defensive; not reproduced'), NEW DR-81 (N1 mixed-separator redaction + B-F1 raising resolution; N5 noted).** Codex lane share:
  WP4.2a = 6 turns, peak depth 190,250 / 475,000; 4 Codex-built packages now. WP4.2b brief read (96 lines, 0 CR): three drafting
  choices CONCURRED (stem rule = my parenthetical only; whole composed name checked, so `x.mp4:s` refused; runner test via
  `export_jobs(reader=<double>)`, `c:` path built from a string). **LIVE next: WP4.2 build cell 2 (opus-high) on `wp4.2` rebased
  (ledger 9f4c0db); WP4.2b Codex turn 1 from f991254; gate stacked with WP4.2's suite if WP4.2b is ready first (orchestrator tells
  me).** Owed by me: DR-80 CLOSED at WP4.2b's accept; WP4.2's rows at its accept.
- **WP4.2b STOP RULED 04:50Z (query `604fcf727a26eb5d`, my post ruling-42b-stop; WIP head `wp4.2b` f1a6bba, 822 light tests green but
  22 WP4.2a hardening tests failing because the naming ValueError is swallowed by `check_outputs`' `except ValueError: continue`
  (:717), turning the before-jobs exit-2 refusal into an engine failed item):** (A) GRANTED = `OutputNameError(ValueError)` in
  `jobs/naming.py` exported from `clearwater.jobs` (additive, not frozen); WP4.2b grant on that ONE runner branch (OutputNameError ->
  RunnerRefusalError exit 2; other ValueError still to the engine); test-only grant on `test_wp42a_runner_hardening.py` limited to
  the two same-drive cases flipping to REFUSED + exact-text assertions, no deletions, node ids listed; parent guard and its planted
  tests (:272/:285) unchanged. WP4.2b merges FIRST, OWN two-leg window (~52 min); `wp4.2` rebased at cell 2's next yield before
  task 5. DR-80 closure gains the before-jobs sentence at the accept. Codex depth 137,070 / 475,000 after turn 2.
- **WP4.2b STOP 2 RULED 04:55Z (query `cb8a50fc31eb0187`; docs-only 79b60d9):** condition 3 EXTENDED test-only with (c) the eight
  drive-relative cases take their precondition plan from a monkeypatched `final_output_path` returning the old drive-relative path
  (they stay the parent guard's coverage) and (d) the planted file-form control isolated the same way; every edited node id + span +
  reason in ledger and report; no deletion, no skip, no weakened assertion. Correction of my condition 2: the tests at :266/:279 prove
  planning is SKIPPED, not that the guard fires. Cell idle at 167,794 before the word.
- **GEN 18 ROLLED 05:31Z at a clean boundary (msg `3fbce47735fff00e`): WP4.2b head `215817a` GREEN for R1 (turn 4 built OutputNameError,
  the runner branch, WP4.2a test edits (a)-(d); light 1076/12, the 22 nodes green); WP4.2 BUILD COMPLETE `wp4.2` 66169d2 (cell 2 stood
  down at 374,198; V3 no miss c3 0.0102 / ancuti 0.0067 /255; V9 max 0; V17 decodes 2 then 1; V4 CPU and GPU SAME; new serial cost
  ~210 s). THREE READINGS RULED 05:40Z (my post ruling-3readings): (1) unreadable_tail -> expected_frames None + Limit APPROVED
  (verify.py:681-700: unknowable without decoding; sink's missing_frames still guards export); (2) three builders INTO `__all__`
  with a one-line grant on `test_the_package_exports_the_root` (not KEEP); (3) V3 on the GPU job KEEP (169 s vs 650 s, same figures).
  Gen 19 next: WP4.2b R1 -> own window -> B -> accept FIRST; rebase `wp4.2`; cell 3 = WP4.2 Reviewer A R1. Worktrees wp4.2a, wp4.2a-mc,
  brief-wp4.2r, brief-wp4.2b removable by gen 19.
- **WP4.2b R1 RULED 05:50Z (query `0d0659fe906001ac`): Claude pass NO_NEW_CRITICAL_MAJOR on 215817a; F1 MINOR (mutation M1 showed the
  per-file form check `_write_form_refusal` :734-736 unproved once naming pre-empts real names) = (a) GRANTED, ONE twin test beside the
  3(d) control in `test_wp42a_runner_hardening.py`, RED under M1; F2-F5 at the orchestrator's seat concurred (F3 = real `carrier:` stream
  + real reader instead of the brief's `c:` + double, forced by export.py:712 os.stat, deviation in the report). Next: Codex turn 6,
  R2, OWN window, B, accept (merges first). WP4.2 cell 3 (opus-high) = Reviewer A R1 from the ledger, concurrent.
- **WP4.2 Y4 RULED 05:58Z (query `d1ed1dea8842ce87`; cell 3; readings applied at `wp4.2` 2e79df7 / 1fa33a8; Reviewer A R1 0/0/4
  terminating, cleanup granted):** FLAG 2 = (a) ONE recorded CPU V3 run in an exclusive window (~11 min), backend named, both figures
  files md5'd, the report cites equality by the two hashes (my item 3 had asserted a hash that was never recorded; `work\wp4.2-v3-
  figures.txt` f76c42a5 is cell 2's unlabelled observation); a difference = STOP before the two-leg window. FLAG 1 concurred: the
  unreadable_tail Limit now says a gap inside the written range is refused, an early end accepted (cell 2's 'sink refuses a short
  set' was false for that case). Builders all in `__all__`, alias dropped. WP4.2b: turn 6 running; one extra parameter row in its one
  runner test granted at the orchestrator's seat.
- **V3 WINDOW 06:15-06:24Z RELEASED + STOP RULED 06:30Z (query `e29ac0a1978afabb`): CPU and GPU V3 figures on `wp4.2` e3b5d5f differ
  in 13/64 rows (12 encoded characterisation rows at the 2nd-3rd decimal, 1 planted row by 0.001); every V3 / AD-14 asserted or
  recorded row (24) SAME, pre-encode. RULED (a): the claim narrows to the 24 deciding rows by md5 (selection in compare.txt; files
  3ec7f59c gpu / 1eba25f5 cpu; driver b128c609); mechanism stated as the cell's reading; V4 SAME (AD-11 tolerance) unaffected; CPU
  leg coverage = 'the same V3/AD-14 figures, not the same encoded characterisation'. WP4.2 suite HELD until WP4.2b merges. Cell 3
  237,804 at the yield (evaluation point). WP4.2b: A converged R2; candidate `wp4.2b-mc` a6910f1 on f3835cc (patch-id b88eac69);
  Reviewer B running; own window next.
- **WP4.2b ACCEPTED main `3cedac6` (07:28Z, msg `745283af419914b9`; record `docs/proofs/wp4.2b-accept.md`). CHARC QA CONFIRMED
  (static, ~07:35Z):** code patch-id e785715a equal on `f991254..f3c1381`, `f3835cc..a6910f1` and `983eae1..3cedac6`; `git diff
  a6910f1 3cedac6` over src tests tools EMPTY; 9 files (naming.py +18/-?, jobs/__init__ +2, runner +12/-?, WP4.2a test file 60 lines
  under the (a)-(d) + twin grants, new naming tests, new guard test file, report, ledger, record); interfaces untouched; 0 CR; r1 /
  r2 / reviewB md5s = record (e459925b / 48c380f5 / bc9b165b; md5sums.txt 6/6 each); ruff / format 261 / mypy 141 / harness 382 OK
  here; no suite here (own gate 5250/1 + 1126/1 is the figure). **Register: DR-80 CLOSED (before-jobs sentence included); NEW DR-82
  (B-A3 engine-route cost before `_plan` raises + the failed-item wording / POSIX `:` note, WP4.3).** Codex-built packages now 5
  (WP3.20R, WP-T4, WP-T5, WP4.2a, WP4.2b). Worktrees `wp4.2b`, `wp4.2b-mc` released. **NEXT: orchestrator rebases `wp4.2` onto
  3cedac6 (runner conflict resolved at its seat, recorded), grants WP4.2's two-leg suite (~58 min, OPEN to me); cell 3 at ~257K
  runs it and writes the task-10 RESUME HERE; fresh cell for task 10 = the orchestrator's call.** Owed by me at WP4.2's accept:
  DR-67, DR-71, DR-73, DR-74, DR-47 (a), DR-45 (b) rows; the R1-Q4 cache-interior row; DR-81's trigger moves to WP4.3.
- **WP4.2 SUITE WINDOW RELEASED 08:33Z (status `2a24c6cf87e37512`, no reply owed): GREEN on rebased `wp4.2` 401521e** (22 commits
  on 38f291e; collision fix 0109c39 = two `match=` strings only, as granted): parallel 5304/1 644 s, serial 1135/1 2,937 s (1136
  selected = WP4.2a's 1127 + 9 new: V3 file 6, DR-74, DR-67 gpu, V4 gpu). **Question 9 budget MET: ~207 s at most** (V3 ad14
  67+44 s, V3 jitter 15+15 s, DR-74 22 s = 164 s measured; rest under the 8.5 s cut). Orchestrator FLAG noted: serial wall +396 s
  over WP4.2a's 2,541 s with no like-for-like split (no `--durations` there; shared laptop); the per-test figure is the budget
  evidence, ACCEPTED as such. Cell 3 stood down at 278,978; **cell 4 (opus-high) DISPATCHED for task 10** (runs + ledger + report
  only; ledger ab9ea83). **NEXT: cell 4's WINDOW REQUEST for task 10 (GX011627 GPU + WP2.3 V4 set GPU and --force-cpu, each
  through `video_fidelity.py compare`, EXCLUSIVE); then Reviewer B on `wp4.2-mc`, accept, my HOLD, ff.** Main still 38f291e; the
  suite stands on the candidate only while code identity to 401521e holds (I check patch-id at the accept).
- **TASK-10 WINDOW OPEN ~08:45Z (status `06be70c3c0044a40`, no reply owed; EXCLUSIVE, 25-35 min): cell 4 runs the V4 SAME leg
  on footage** via the uncommitted driver `work\wp4.2\v4\window.sh` (md5 85ca41d6, read at the orchestrator's seat; stops at the
  first non-zero runner exit or the first compare not 'MANDATORY+REQUIRED all SAME: True'): GX011627 pure defaults on the GPU
  (path only from `find_footage_file`, never logged) + compare; WP2.3 V4 set (hevc8-bt709-full, hevc10, rotated, untagged, vfr,
  truncated) one GPU batch + one `--force-cpu` batch + 12 compares; vid-hlg / vid-pq excluded (refused by design, suite covers).
  Outputs under `work\wp4.2\v4\` and `work\wp3.10\wp4.2-v4\`, nothing committed. Start checks: 9.43 GiB free (5 GiB guard
  re-read per step), GPU idle, worktree clean at ab9ea83. Alongside, light only: Reviewer B (Codex, WSL, offline, read-only, no
  tests/FFmpeg) on `wp4.2-mc` ab9ea83 vs 38f291e, 14 owned paths, report + ledger withheld. ACCEPTABLE: task 10 is a fidelity
  (SAME) leg, not a timing figure, so a read-only reviewer beside it does not touch the hardware rule. Nothing heavy at my seat.
- **TASK-10 WINDOW RELEASED 08:48Z (status `56141b18bc042961`, no reply owed): GREEN, 13/13 V4 compares SAME on every MANDATORY
  and REQUIRED item** (orchestrator checked window.done OK, 16 steps exit 0, 13 SAME lines, record md5s; no footage path in logs or
  records). GX011627 GPU 681/681 frames, BE-different 8 = WP3.21's same 8, record md5 4922fd54 (device GPU, cuda:0, hevc_nvenc,
  2 decode passes; elapsed 218.9 s, information only, not a V16 row); WP2.3 set GPU md5 4d892589 and --force-cpu md5 99294d0a,
  every item SAME (truncated = D86 readable part to 0.800800 s; untagged = assumed-tags warning). Free memory >= 9.37 GiB
  throughout. `wp4.2` at 265251f (docs only: ledger +75/-1, report V4 section +40, 0 CR, Limits unchanged); cell 4 at 105,663.
  Return report's register list = mine exactly: DR-67, DR-71, DR-73 (a)+(b), DR-74 CLOSE; DR-45 (b) CLOSES with the
  `unreadable_tail` residual as a Limit; DR-47 (a) CLOSES, (b)(c) stay on the next `analysis/engine.py` touch; NEW R1-Q4
  cache-interior row (store.py:573 skips a link at discovery, :660-666 writes through it; trigger next `cache/` touch); DR-81
  untouched, trigger -> WP4.3. **NEXT: Reviewer B still running on `wp4.2-mc` ab9ea83; cell 4 report FINAL (docs only); orchestrator
  code identity + harness gate + accept record; HOLD request to me; ff; then my QA + the rows above.**
- **WP4.2 REVIEWER B BLOCKED 08:55Z: NEW_CRITICAL_MAJOR_FOUND (2 MAJOR / 4 MINOR / 4 ADVISORY) on `wp4.2-mc` ab9ea83 vs 38f291e
  (msg `9ba4ebbb651162db`; evidence reviewB/review-B.txt md5 b1865ba2). CHARC CONCURRED with every disposition (my fyi
  d17f0088, ~08:59Z).** B1 MAJOR: test-only figures switch `CLEARWATER_WP42_V3_FIGURES` (`tests/test_wp42_v3_product.py:63-76`)
  writes an operator-named path with no footage check -> route through `write_target_refusal(target,
  configured_footage_folder())`, refused when none is configured; MY NOTE: the check runs BEFORE the fixture's parent mkdir (:71),
  plus one planted row for a not-yet-existing parent inside the stand-in footage folder. B2 MAJOR: new-file rule not atomic ->
  `open(path, 'xb')`, one module-scope handle; new light test file `tests/test_wp42_v3_figures.py` (granted at the orchestrator's
  seat; refusal rows existing file / stand-in footage / dangling link + control, RED first). B3 builder test asserts the sink's
  backend; B4 DR-74 case asserts rendering started and frames remain at the release; B5 docs (`composition.py` no-cache-folder
  promise overstated); B6 docs (runner docstring: cache writes bypass SafeWrite). B7 ADVISORY banked -> NEW ROW mine at the
  accept (import-time witness does not instrument the video constructors; trigger WP4.3's `test_app_composition.py` touch); B8
  (frame count is a minimum when known; surplus passes; reuse not rechecked) and B9 (own-clip result inherits the cache key's
  size+mtime collision) = Limit sentences; B10 PRE-EXISTING = DR-58(b) re-sighting (inherited FFREPORT) noted in that row.
  Fill Part 2: ONE bounded remediation (cell 4 + Reviewer A R2 at its seat; light window = one V3 node jitter c3 unset then set
  under work/wp4.2/b-remediation, DR-74's case, builder test), ONE B re-run, then the orchestrator's OWN two-leg gate on the final
  candidate (identity with the 401521e suite is broken). Bare-cd SLIP into `.worktrees/wp4.2-mc` acknowledged (read-only, both
  trees clean). **NEXT: remediation commit(s), A R2, B re-run, new gate (~52 min, OPEN to me), accept record, HOLD, ff.**
- **OWNER 2026-10-29 ~09:00-09:05Z (in chat): asked why the suite is so long and why it runs more than once per package;
  CHARC answered (eight whole-clip fidelity tests = 1,735 of 2,937 s; sequencing put the suite before Reviewer B in WP4.2, my
  concurrence); owner: "let's commission that change".** DONE: (1) fill Part 2 new **Order** bullet = ONE full gate per
  package AFTER A converged and B returned (WP4.2's second suite is that one gate); (2) **AD-30** gate tests sized by the
  property proved (floors: lead 61 frames for steady-state/release/D87; six frames otherwise; 1080p unless the subject is the
  large-frame path; GX011627 as a stream-copied ~3 s trim per session; full-clip forms behind a marker both legs exclude);
  (3) **WP-T6 COMMISSIONED** to the orchestrator (brief drafted at its seat for my ruling, as WP-T5; tests + pyproject markers
  only; rung 1 measures, rung 3 cuts with every assertion kept or its loss ruled; target serial leg < 900 s, two-leg ~25 min;
  Codex-eligible, Codex pace 0.51 at 09:11Z; dispatch AFTER WP4.2's ff because the owned test files overlap). At WP-T6's
  accept, mine: fill two-leg command + marker exclusion, CLAUDE.md gate paragraph, AD-28 figures.
- **WP4.2 GATE WINDOW OPEN ~09:45Z (status `db0cfda437df5f88`; ~60 min EXCLUSIVE): the ONE two-leg gate on `wp4.2-mc` 8bc927a
  (= 798af0c rebased onto 246052b; package patch-id 7dfc431f on both bases).** Before it: B remediation 5e74d01 (B1/B2 refusal
  before mkdir + `xb` on one handle, my fifth row present; B3-B6); Reviewer A R2 0/0/3 TERMINATED; cleanup 9aa2783 (DR-74 window
  deterministic, GREEN 3x; B2 premise corrected: on Windows `xb` on a dangling symlink CREATES the target, rule (ii) refuses it
  first); **Reviewer B re-run on 33f13e5 vs 246052b = NO_NEW_CRITICAL_MAJOR** (4 MINOR; reviewB2/review-B.txt md5 cabd2c51).
  B'1 BANKED = **DR-81 (c)** candidate, mine at the accept (`io/video/verify.py:234` packet-listing timeout text carries the
  ffprobe path; Redactor ignorant of the tool folder; 120 s timeout only; trigger WP4.3). B'2-B'4 fixed docs/help only
  (798af0c). **CHARC CONCURRED (my status ~09:48Z): post-B diff over src/tools = two docstrings + parser description, verified
  at the candidate.** Order bullet satisfied. **NEXT: gate result, accept record, HOLD request, ff; then my QA + rows (DR-67,
  DR-71, DR-73, DR-74, DR-45 (b), DR-47 (a), R1-Q4 cache row, B7 row, DR-58(b) note, DR-81 (c) + trigger WP4.3); then the
  WP-T6 brief draft arrives for my ruling.**
- **WP4.2 GATE RELEASED 10:36Z (status `db1fdaed1f328ad0`, no reply owed): GREEN on 8bc927a, parallel 5312/1 660 s (5304 + the
  8 figures-switch rows), serial 1135/1 2,621 s; Q9 at the gate ~127 s of 300 (ad14 28+27, DR-74 20, jitter 13+12, rest < 7 s);
  ruff / format 267 / mypy 141 / harness 382 OK at the orchestrator's seat. Serial 316 s under the 07:32Z run on the same code =
  laptop variance. `work\wp4.2\gate-logs\wp4.2-serial.log` (--durations=40) = WP-T6's rung-1 BASELINE.** Second bare-cd slip
  (into work/wp4.2/gate-logs, read only) acknowledged. **NEXT: cell 4 FINAL docs turn (227,702); code identity `git diff 8bc927a
  <final> -- src tests tools` empty; accept record; HOLD REQUEST to me (main f225528; candidate rebased onto it, patch-id
  re-proved); ff; release; then my QA + rows.**
- **WP4.2 ACCEPTED main `ff234ee` (10:42Z, HOLD 57de40e2 granted ~10:41Z, RELEASE `7cd0f8a00aadab2c`; record
  `docs/proofs/wp4.2-accept.md`, report `docs/reports/wp4.2-video-path.md` FINAL). CHARC QA CONFIRMED (static, ~10:50Z):**
  code patch-id af839429 equal on `246052b..8bc927a` and `f716417..922d1c6` = record; `git diff 8bc927a ff234ee -- src tests
  tools` EMPTY (identity with the gated tree); 18 files = 15 package paths + report, ledger, record; `src/clearwater/interfaces`
  untouched; 0 CR on every blob; evidence md5sums.txt all OK (r1 9/9, r2 9/9, reviewB 7/7, reviewB2 8/8; review-B b1865ba2 and
  cabd2c51 = the posts); ruff / format 267 / mypy 141 / harness 382 OK on main; no suite here (own gate 5312/1 + 1135/1 on
  8bc927a is the figure). **Register: DR-67, DR-71, DR-73, DR-74 CLOSED; DR-45 (b) CLOSED ((a) open); DR-47 (a) CLOSED ((b)(c)
  open, next engine.py touch); DR-58 (b) re-sighted (B10); DR-81 (c) added, trigger WP4.3; NEW DR-83 (R1-Q4 cache-interior
  link write-through, next `cache/` touch), DR-84 (B7 import-time witness, WP4.3's test_app_composition.py touch).** Lane:
  WP4.2 = Claude (opus-high, cells 2-4), Codex nets A + B; Codex-built packages still 5. **NEXT: WP-T6 brief DRAFT from the
  orchestrator for my ruling (baseline `work/wp4.2/gate-logs/wp4.2-serial.log`); then WP4.3 brief revision (DR-75 REQUIRED
  test under Q12, DR-76, DR-77, DR-81 (a)(b)(c), DR-82, DR-84, DR-68, DR-69, DR-52, DR-62; AD-23 note at its accept).**
- **WP-T6 BRIEF RULED FINAL ~11:15Z (query `699ca89c367b9a9d`; draft `work/wp-t6/wp-t6-brief-DRAFT.md` md5 87d8c915, 469
  lines, read in full; my ruling post ruling-wp-t6). Orchestrator commits it as `docs/briefs/wp-t6-brief.md` FINAL + rulings
  and dispatches to the CODEX lane from d1d8fd9+.** Map: 38 rows of the serial top 40 (2,227 of 2,621 s): CUT R1 engine 456 s,
  R2 NVENC levels 330 s, R3 sink 222 s, R4 colour round trip 170 s (only if Q4's measured rule passes), R5-R7 hardware decode
  389 s; 30 KEEP with reasons; row 10 OPEN (63 s for two 128x72 frames inside tools/prototype/bench.py; rung 1 profiles).
  Projected AFTER serial ~1,310-1,445 s (saving ~1,180-1,315 s). Rulings: Q1 conftest additive (imports in bodies; guard copies
  conftest beside local_config only, verified :122); Q2 `fullclip` marker, amended expressions at the gate (fill, CLAUDE.md,
  AD-28 figures mine at the accept; ADDED fullclip runs once per phase-end gate); Q3 operand KEPT not a loss; Q4 as drafted +
  plant MARGINS reported, KEEP if any margin at N < half its margin at 30; Q5 whole trim for R2, STOP on a 1.25 link; Q6 BEFORE
  = baseline log, AFTER = the one gate, verdict TIGHTENED to the seven CUT bodies' per-test sum > 110 s under 1,567 s (316 s
  host spread makes a leg-wall verdict unreliable); Q7 900 s = TARGET not pass criterion (my commission figure; gap: 5.3K CPU
  121 s, bench rows 163 s, V3 81 s, tail 394 s) BANKED as a follow-on DR row at the accept, owner trigger; Q8 W4 fullclip once
  (~27 min); Q9 teardown removal; Q10 materiality 20 s; Q11 FAST one round + cleanup; Q12 Codex (6th Codex-built package;
  pace 0.54). Owed by me at WP-T6's accept: Q7 gap row, row-10 row if a tools/ lever, DR-22/DR-66 consumer notes, fill +
  CLAUDE.md + AD-28 update, fullclip-per-phase sentence.
- **WP-T6 DISPATCHED ~11:12Z to the CODEX lane (status `b35e95450b611156`): brief FINAL on main `6ecc4e5`
  (`docs/briefs/wp-t6-brief.md`, 506 lines, 0 CR, my ruling 7458b470 verbatim under Rulings; checked). Worktree `.worktrees/wp-t6`
  on 6ecc4e5, local config byte-equal, venv synced; evidence `clearwater-review-evidence\wp-t6\cell\`. Turn 1 = rung 0 + the W1
  script only (stack check vs 8bc927a empty, three collections, ledger skeleton, `work/wp-t6/w1.sh` with my Q4 margins); the
  orchestrator runs W1 (~15 min, posted window); turn 2 = the round-0 table, sent to me BEFORE any build. **NEXT: W1 window
  post (no reply), then the round-0 table for my reply (N, T, checks (a)-(e), ALLOWED_TAG_DIFFS keys, R2's chain, R4's N +
  margins, row 10's profile); WP4.3 brief revision draft after.**
- **WP-T6 W1 WINDOW OPEN ~11:22Z (status `b9b8441d7f530d3b`, no reply owed; EXCLUSIVE ~20 min at the orchestrator's seat):**
  turn 1 c06c808 ledger only (base 6ecc4e5; stack check vs 8bc927a EMPTY; pytest 8.4.2); the Codex sandbox's `--collect-only`
  returned nothing in ~5 min -> cell STOPped, collections run at the orchestrator's seat by its `base-collect.sh`. W1 =
  `work/wp-t6/w1.sh` md5 7e6d01a6, 342 lines read by the orchestrator (packet listing; provisional trim + checks (a)-(e) with tag
  diffs by KEY only; NVENC chain; R4 at 30/6/10/15 with signed margins and walls; row-10 cProfile; scratch removed on every
  exit; subprocess output withheld). **NOTE: the Codex cell's context window is 258,400 (WP4.2b's was 475,000); turn 1 used
  104,555, so the ~250K evaluation point binds early; the orchestrator watches it.**
- **WP-T6 W1 STOP RULED ~11:25Z (query `5b9dd6b0dfacc46e`; my post ruling-wp-t6-w1stop): R-a..R-d CONCURRED.** W1 ran 3 s and
  stopped at the first trim: 4(b)/(c) PASS (90 packets equal by pts/duration/size/flags/MD5 = a true copy), 4(d)/(e) FAIL because
  the check paired streams BY INDEX after `-write_tmcd 1` placed the regenerated tmcd after gpmd; gpmd intact (3 packets < T).
  Facts: N = 90, T = 3.003 s, keyframes every 30. Rulings: R-a roster as a multiset, pairing by (codec_type, codec_tag_string),
  TIGHTENED with source-index order inside a shared key + equal count; R-b `-movflags use_metadata_tags` joins the fixed flags
  (keeps GoPro `firmware`); R-c ALLOWED_TAG_DIFFS = muxer-written keys only (format major_brand/minor_version/compatible_brands/
  encoder; stream handler_name/language; audio timecode), any other key STOP, LIMIT: those tag items hit the real container only
  in the fullclip form; R-d draft correction (f) did not reproduce, flags stay. Base collections at the orchestrator's seat:
  all 6449 / parallel 5313 / serial 1136. NEXT: turn 2 corrects w1.sh, W1 re-run (~15 min window), round-0 table for my reply.
- **(history) After WP4.1's accept:** WP4.2's brief (DRAFT RULED on main 3aa3c51) got ONE revision pass against WP4.1's accept record, then FINAL
  on CHARC's word; its revision must carry: DR-78/79 (B2 rows) as WP4.2 items, the WP4.1 runner's final names and the stream-syntax
  predicate, the Limit text. WP4.3's revision later carries DR-75 (REQUIRED test under its Q12), DR-76, DR-77, and the AD-23 'applied by
  WP4.3' note is mine at its accept. Lane: WP4.2 / WP4.3 opus-high, Codex nets. Order WP4.2 -> WP4.3.
- **WP-T5 ACCEPTED main 4933a45 (2026-10-29 00:40Z), CHARC QA CONFIRMED (my msg 56844e86; register + CLAUDE.md 3114d23, DR-65
  CLOSED).** Serial leg 2,798 -> 2,261 s like-for-like; stacked gate green 4,473 / 1 + 1,126 / 1. Worktrees `wp-t5`, `wp-t5-mc`
  released (orchestrator copies logs out first).
- **Phase 4 commission (my msg 136bfecd) and ruling packet (c7452911) are verbatim in the four briefs on main 3aa3c51**; WP4.2 Q3
  narrowing accepted; DR-47 (a) closes in WP4.2 only if its Q7 engine.py grant fires; DR-62 = WAIT; DR-69 stays OPEN (GUI shows no
  device-wide total); 43-Q13 AD-23 extension = N1 approval for the CREATE_NO_WINDOW helper.
- **Owner-pending inputs (carry):** photos (WP3.6P; WP4.1 records the owner-photo leg OWED), the iPhone clip (DR-15). **Spec v0.5.6
  APPLIED 2026-10-29 ~00:55Z (owner verbatim "Apply N6 erratum"; text only; DR-64 CLOSED; CLAUDE.md updated).** Open owner decisions:
  none. Every owner-facing summary ends with that line.
- **Rules learned this generation:** a seat correction to a working cell lands only at its yield (warn cells of windows at the previous
  yield); the stacked-gate form needs a hold cap so a ready package is not held hostage; a design guard's pre-ruled remedy must fit the
  trigger's CLASS (the fifth finding was a stream-syntax route the Q9 alternative did not touch; the structural predicate did).

### Generation 5 (2026-10-28 16:50Z to 2026-10-29 00:45Z; rolled at ~402K; kept as record)

#### Gen 5 live block as left (`clearwater-charc-20261028-0647`, fable/medium, ONLINE 2026-10-28 16:50Z)

- **Orchestrator = gen 17 `clearwater-orchestrator-20261028-1101`** (launched 21:01Z by gen 16, which rolled at ~421K, state
  1b6de7f; ONLINE 21:04Z at f706cc8, msg `f7c9b147cb92bf0d`, gauge 34 ms, acked by my msg ack-gen17; re-read
  `comms/.launch-sessions.json` before every cue; every post gets ONE SendMessage cue). Subjects under 120 chars; bodies via `--body-file`; edit docs with a scratchpad
  Python script (`newline="\n"`); `tr -cd '\r' | wc -c` = 0 before every commit; commit by pathspec; never an uncommitted edit left
  in the main tree (hazard 7). Bash gauge 64 ms at pickup. Gen 4 `clearwater-charc-20261026-2007` rolled ~16:35Z at ~390K and
  launched this seat itself.
- **PHASE 3 COMPLETE 2026-10-28 18:30Z. WP3.21 ACCEPTED main `7e228fb`** (record `docs/proofs/wp3.21-accept.md`; candidate `wp3.21-mc`
  0ca1970 = `wp3.21` 227ed32 code; two-leg suite on 227ed32 = main's figure by code identity, main docs-only since d1e4537, verified
  here; Reviewer B BLOCKING 2 major adjudicated at the gate, CHARC UPHELD (A), msg 24a26b64). **CHARC QA CONFIRMED (static, msg
  83b59f48):** whole-diff patch-id 906842c7 identical on `d1e4537..wp3.21` and `6d48541..7e228fb`; `git diff 7e228fb 227ed32` over
  src tests tools pyproject uv.lock EMPTY; footprint owned + named grants; interfaces / export_seam / samples.py / pyproject / uv.lock /
  fixtures untouched; cupy only under core/; 0 CR; B md5s OK (6), VERDICT anchored, gpt-6.1-sol, 16 succeeded; ruff / format 250 /
  mypy 138 / harness 382 (1 skipped) at this seat; no suite here. **Register `cffd243`: DR-63 CLOSED; NEW DR-67 (WP4.2
  `device_backend`), DR-68 (WP4.3 preview FFT plans), DR-69 (job estimate bench-only; IF-8/IF-2 extension = CHARC decision at WP4.3),
  DR-70 (analysis-bound export; trigger owner wish < ~9.5 or WP5.2), DR-71..DR-74 (B1 max of rates, B2 bench exit, B4 + misnamed test,
  B5 longer boundary-free case).** Worktrees `wp3.21`, `wp3.21-mc` released (branches kept); deletion grant for the 13 V4
  `*_corrected.mp4` outputs ONLY, everything else under work/wp3.21 and work/wp3.10/wp3.21-v4 KEPT.
- **V16 figures of record (device frames ON, exclusive windows):** GX011627 cold c3 9.57 / 9.78 / 9.92 min/min [31.8-31.9];
  GX011625 sustained 9.58 [31.26]; warm 9.06; ancuti2018 8.74; libx265 14.59; 5.3K synthetic 36.65 [136.03]. Memory: 4K device-wide
  3,277 <= 4,065, pool 1,511 <= 2,174; 5.3K pool 4,312 <= 6,281 (binding), device-wide 7,901 <= 10,331. D106's 25 met on every NVENC
  row; AD-21's ~10 met cold. Next speed lever = the analysis pass (DR-70), not before WP5.2 or an owner wish.
- **PHASE 4 COMMISSIONED 18:37Z (msg 136bfecd, new thread):** WP4.1 photo path -> WP4.2 video path -> WP4.3 wiring IN ORDER, all
  `implementer-opus-high`, A and B Codex gpt-6.1-sol/high; plus **WP-T5 suite cost (DR-65)**, Sonnet-class by pace tiebreak,
  concurrent with WP4.1 (disjoint test files). One drafting helper per brief; CHARC approves each FINAL; drafts arrive as one set with
  numbered questions. Ruled bounds in the post: composition root replaces `gui/engines.py` stub wiring (photo legs in WP4.1, video in
  WP4.2; a new module = my pass before dispatch); headless runner under tools/ owned by WP4.1, extended by WP4.2; WP4.2 binds DR-67
  (+ DR-71/73(a)/74 where reached), V4 SAME leg through the product composition (one window), no V16 re-measure (WP5.2); WP4.3 binds
  DR-68, DR-69 (IF-8/IF-2 extension = STOP to me), DR-52, DR-62, WP3.18 adapter notes, DR-50/51 swaps, V7 re-measure, G1-G13; WP-T5
  = minimum-frame 5.3K V4 export + shared GX011627 export fixture, no product code, serial wall before/after.
- **PHASE 4 RULING PACKET POSTED 19:01Z (my msg c7452911; drafts packet `8c3c624c224c263e` + correction `56e00cce` + addendum
  `528b3db8`; drafts on `.worktrees/briefs-p4`, branch `briefs-p4` from 6536f60): ALL FOUR DRAFTS APPROVED, 42 questions + 5 flags
  ruled, helper recommendations adopted throughout with these notes.** Tripwires GRANTED: new package `clearwater.app`
  (`__init__.py` Qt-free + `composition.py` in WP4.1; `main.py` the only Qt module, `startup.py`, `analysis_adapter.py`,
  `activity.py`, `src/clearwater/__main__.py` = `python -m clearwater`, no scripts entry, in WP4.3); the leftover JOURNAL (JSON in
  config_dir, format_version 1, atomic; start-up scans output folder + journal folders with `remove_leftovers`; never footage; D85
  kept). 42-Q3 NARROWING accepted (GUI video legs stay stubs until WP4.3; N4 ground). 42-Q1 additive keyword-only ExportEngine
  factories (DR-67). DR-47 (a) closes in WP4.2 ONLY if its Q7 engine.py grant fires, else trigger = next engine.py touch. 43-Q7:
  GUI shows no device-wide total, DR-69 stays OPEN. 43-Q8 DR-62 = WAIT (per-key process-local lock, cancellable). 43-Q13:
  AD-23's 2026-10-21 extension IS the N1 approval for the CREATE_NO_WINDOW helper in `io/video/pipes.py` (three conditions); I add
  a dated 'applied by WP4.3' note to AD-23 at WP4.3's accept. 43-Q12 uses AD-11 AS AMENDED (k=1 exact; k>1 p99 bounds). WP-T5:
  3 frames, module-local session fixture, engine test not shared = DR-65's recorded reason, W1 BEFORE / W3 AFTER, measurable
  > 110 s, FAST one round; saving ~12 min/gate (my ~30 corrected). **Owed at accepts:** AD-23 note (WP4.3); DR rows per each
  brief's table (the orchestrator's record lists them; I write the register). **NEXT:** orchestrator writes rulings into the
  briefs, commits `briefs-p4`, ff main, dispatches WP4.1 (opus-high) + WP-T5 (lane by pace); WP4.2 / WP4.3 FINAL on my word after
  their predecessor's accept + one revision; windows OPEN/CLOSE as before; CHARC QA at each accept (standing rules below).
- **PHASE 4 LIVE 19:07Z (msg `89e7cc14ede77ef3`): briefs on main 3aa3c51 (WP4.1 + WP-T5 FINAL; WP4.2 + WP4.3 DRAFT RULED, FINAL on
  my word after the predecessor's accept + one revision; each carries my packet verbatim as `## Rulings`; verified at my seat: 0 CR,
  rulings section x4, AD-11 AS AMENDED in WP4.3).** Live cells (OCCUPIED worktrees): **WP4.1 `wp41-cell1`** opus-high in
  `.worktrees/wp4.1` from 3aa3c51 (depth 0 at dispatch; yields Y1 round-0 table BEFORE building, Y2 window requests, Y3 STOPs, Y4
  each A round, Y5 return); **WP-T5 Codex lane** (`codex_cell.py turn`, turn 1 = rung 0) in `.worktrees/wp-t5` from 3aa3c51, pace
  Codex 0.188 vs Claude 1.355 at 19:02Z; the orchestrator runs W1/W2/W3 in exclusive windows (OPEN/CLOSE to me); reviewer = the
  Claude pass FAST (STRONG on any non-test change). Evidence `clearwater-review-evidence\wp-t5\cell\`. **No window open yet; W1
  (BEFORE serial leg ~45 min) comes first. Nothing heavy at this seat while any window is OPEN.**
- **W1 CLOSED 20:08Z (msg `60e90b28ba1d0b94`): BEFORE serial leg on 3aa3c51 EXIT 0, 1,104 passed / 10 skipped, wall 2,798.4 s;
  four DR-65 bodies 492.5 + 434.4 + 355.0 + 216.0 = 1,498.9 s (54 %); projection 6.5-7.5 min saving, W3 decides. 9 of the 10 skips =
  v8 look-check frames absent (the Codex worktree's own work/ has no wp1.3/frames) -> NOT gate-equivalent. RULED (my msg ack-w1):
  W3 / W2 same config as W1 (like-for-like); the GATE legs run at the orchestrator's seat with the gate worktree's local config
  pointing at the MAIN tree's work/ (no 3.4 GB copy), expected 1,113 / 1; both configs stated in the record. **No window open; seat
  free.** WP-T5 turn 2 (round-0 table) running; WP4.1 released for light runs.
- **WP4.1 REVIEWER A R1 (head ef6bf2f; FYI `152c00dbd05527be`): 0 critical / 2 major / 6 minor, all NEW in envelope; adjudication
  UPHELD (F2 MINOR). F1 path privacy (D87 refusal text and two stderr lines carry full paths -> one redaction helper at every exit
  + test); F3 `UnsupportedFormatVersionError` escapes `main` -> usage refusal exit 2 + test; F2, F4-F8 minors. V8 (c) on two
  1080x1920 crops inside the amended bounds (k=2 mean 0.08-0.09, p99 0.47-1.11; k=4 mean 0.27-0.29, p99 1.36-3.70; max ~22-30
  recorded). **SEAT PLAN CORRECTED (my msg 6ba8af9a): cell 1 at 299K fixes F1 + F3 ONLY (fill re-seat line, hazard (6)), depth
  read after F1 and at the yield, hands over at 370K at the latest; cell 2 (opus-high, fresh) takes F2 + F4-F8, then A round 2,
  the two-leg window, the report.** Short window (WP4.1 gpu + v8c legs) 20:12Z OPEN/CLOSED, 2 passed, 28 s, no figure. WP4.1
  light runs green at 755513b (V9 planted control = gamma 1.5; a strength at default moves no pixels under neutral).
- **W2 CLOSED 20:58Z + ORCHESTRATOR GEN 16 -> GEN 17 ROLLOVER 21:01Z (msg `1cdfb1eca2fa1b29`; gen 16 at ~421K, clean boundary,
  stopped draining; state 1b6de7f).** W2: the three changed tests 656.67 s vs 1,063.5 s in W1 = ~407 s saved (projection 401);
  observer PASS (one standard encode, sink record on it, NVENC tied, 681 frames, 5.3K 3 frames AAC SAME); sink alone 208 s,
  levels alone 478 s; depth control failed by name. Control-script defects (harness, not product): (a) the 'caught' grep needs
  `FAILED <nodeid>` which `-rs` suppresses, so the draft-as-standard control did NOT run; (b) `git apply -R` rewrote the test file
  CRLF (restored to HEAD, 0 CR). Gen 17: Codex turn 4 = corrected script, short W2b for the draft control, then W3 (rung 4).
  WP4.1: cell 1 STOOD DOWN ~336K (F1-F8 fixed); cell 2 made one report-truth fix (`dca6d1e`), PREPARED round 2 (`wp4.1\r2\`),
  STOOD DOWN at 66,183 (a successor cannot reach gen 16's cells); gen 17 dispatches **cell 3** for round 2. Lesson (gen 16): warn
  cells of a coming window at their previous yield.
- **GEN 17 ONLINE 21:04Z; live cells:** WP4.1 **cell 3** `wp41-cell3` (opus-high) from `wp4.1` dca6d1e, depth 0 at dispatch: light
  re-check, Reviewer A round 2, adjudicate, yield before any remediation (window request in the same yield if clean); WP-T5 Codex
  **turn 4** running (corrected W2b script, W3 script prepared, W2 ledger rows, a stated condition for W3 straight after W2b).
  Window plan: W2b (~10 min) then W3 (~55 min), each opened only at a WP4.1 yield; WP4.1's two-leg suite after W3 unless ready
  first.
- **W2b CLOSED 21:26Z (msg `2d744869f4fdf495`): depth control DECIDED from W2 evidence (junit names the one failure; depth 10 vs
  output 8 DIFFERENT); draft-as-standard control CAUGHT by name (levels test, 5.0 Main, 328 s); both test files byte-identical to
  HEAD, 0 CR. W3 run condition MET; W3 (~55 min, both legs, W1's config) opens at WP4.1 cell 3's next yield. No window open;
  seat free.** (history: W2b OPEN ~21:21Z, msg `125c9dae6a66d68f`.)
- **W3 CLOSED 22:44Z (query `cf2e5e6007c760a2`): AFTER parallel 4,174 / 1 in 509.95 s; serial 1,104 / 10 in 2,261.41 s, W1's ten
  skips identical, collections identical (5,289 / 1,114). SAVING 536.97 s (~9 min) > 110 s bar; no second pair. DR-65 closes at
  WP-T5's accept with the engine test's recorded reason. No window open; seat free.** (history: W3 OPEN ~21:59Z, msg
  `ad582f053ab6724d`.) **STACKED GATE WP-T5 + WP4.1 RULED YES (my msg ruling-stack):** own Reviewer B and record per package;
  per-package patch-id before/after rebase; stack-top two-leg suite in the main-work gate config (1,113 / 1 expected) = figure of
  record for both by code identity; replaces WP4.1 cell 4's final-head suite only if patch-id equal to cell 4's head; HOLD CAP
  ~2 h after WP-T5's Reviewer A converges, else WP-T5 gates alone.
- **WP-T5 REVIEWER A R1 CONVERGED ~23:00Z (msg `7402a1cc9ce15a38`; Claude pass opus-5-5/high on `3aa3c51..6467e54`,
  `wp-t5\r1\`, review.txt md5 d1f4dda4...): 0/0/2/5; R1-1 no test asserts `nvenc_proof.tied` (pre-existing; closure says
  'observed in W2', not 'proof'); R1-2 closure carries both figures (536.97 s whole leg; 405.27 s attributable to the three tests;
  remainder = variation 112.98 + engine test 18.72; W1 overlap named). Advisories = limits (3-frame libx265 may emit no B-frames so
  the 5.3K test may not reach `ctts`; fixture failure shows as setup ERROR). Cleanup turn 6 docs-only; tests frozen after W3.
  **HOLD CAP runs out ~01:00Z (2026-10-29): WP4.1 cell 4 (round 4 running) ready by then = stacked gate, else WP-T5 gates alone.**
- **WP-T5 REVIEWER B CLEAN 23:14Z (msg `5e2e07d8118d51d2`): candidate `wp-t5-mc` c5a5654 on main 51f0e5e, patch-id 2f1173a5 =
  author branch; Claude pass opus-5-5/high, 25 turns, `wp-t5\reviewB\` review.txt md5 55e16d69...; 0/0/1/5 (F1 report cites
  author SHAs -> record maps 045d622->7341c73, 259a219->7c42596, code identity empty; F2 erratum at the gate). WP-T5 WAITS for the
  stacked gate. **WP4.1 R4 (cell 4, 109,960): 0/1/4; I1 MAJOR a file symlink inside the footage folder + `--beside-source` put a
  PNG inside (naming planned from the unresolved parent) -> GO broadened: realpath check on EVERY planned write target with symlink
  and junction failing-first tests; I2 MINOR upheld; I3-I5 minor (Interop IFD drop would be io.photo's = STOP). R5 = FIVE-ROUND
  GATE with the orchestrator's DESIGN GUARD (fourth blocking round on the containment/redaction surface). MY PRE-RULING (msg
  ack-r4): a FIFTH blocking finding there = STOP and the brief's Q9 ALTERNATIVE (`--out` always required with realpath outside
  footage; `--beside-source` removed; D34 default proved at the library API on tmp_path only); not before. Candidate estimate
  00:15-00:30Z inside the 01:00Z cap.** My QA after each accept.
- **WP4.1 R3 H1 RULED (A) BANK to WP4.3 (my msg ruling-h1), four conditions:** the GUI preview shows an nclx-only Display P3 HEIC
  UNCONVERTED (`gui/render_worker.py`, `gui/preview.py` pass only `icc_profile`; WP3.16 lines c9fb2e8 / b51cc8d, reachable with
  real data since WP4.1's swap 4ee4ea7; preview (199, 40, 60) vs (217, 0, 54) via the D53 built-in; export correct; evidence
  `wp4.1\r3\`). (1) register row at WP4.1's accept BINDING for WP4.3 (trigger = its V8 photo leg; fix = tag the display copy of
  a no-ICC tagged source with the D53 built-in + chromatic nclx-only P3 test); (2) WP4.3 brief revision carries it under Q12 as a
  REQUIRED test; (3) WP4.1 report Limits + accept record name it; (4) the WP2.3 fixture gap (every P3 still carries ICC) recorded;
  WP4.3 builds the sample under tmp_path or adds an nclx-only fixture at round 0. Rest of R3: H2-H4 MINOR UPHELD, H5-H7 MINOR;
  cell 3 (208,313) does the bounded minors, RESUME HERE, stands down; cell 4 runs round 4, the two-leg suite, the report.
  **Owed at WP4.1's accept (mine): the H1 row; the G5 writer/importer row (trigger WP4.3); WP3.6P OWED noted.** Codex turn 4 259a219 (depth 82,213). **WP4.1 R2 (cell 3, depth 93,956 at yield): 0 critical / 2 major / 5 minor, all in
  envelope: G1 `\\?\` path spelling defeats `inside()` so `--out` could write INTO the footage folder (a real safety catch); G2 =
  F1 REOPENED, a non-ASCII folder path escapes the Redactor via `ascii_text`; G3/G4/G6/G7 minor; G5 MAJOR->MINOR.** Orchestrator
  GOes the remediation after W2b (runner + its test + report limits; under the 250K rule). **BANKED TO ME (G5), row at WP4.1's
  accept, trigger WP4.3:** the photo writer's HEIC provenance carries `"profile": "built-in sRGB"` (WP3.6 7624f5c) which the
  accepted `PresetStore.import_preset` (WP3.15 75d7dc5) refuses, as the runner's `--parameters` does; IF-9 / AD-13 hold; two
  accepted components disagree; runner docstring narrowed to the AD-13 forms. W3 at WP4.1's next yield.
- (history) W2 OPEN ~20:37Z (msg `7e81a160651af8af`, ~30-40 min; W1's config; the 3 changed node ids with an
  observer plugin: exactly ONE standard encode, sink record on it, NVENC tied, 681 frames, 5.3K at 3 frames with AAC packets SAME;
  each test alone; 2 planted controls applied with `git apply`, reverted, restore proved). NOTHING HEAVY AT THIS SEAT until CLOSE.**
  WP-T5 turn 3 `045d622` (Codex depth 209,195 / 475,000): 5.3K `duration="0.1"` + `nb_frames == 3` precondition; module-local
  session fixture `gx011627_standard_encode`; engine test untouched; 146 node ids unchanged. **WP4.1 cell 1 DONE at 335,741:** my
  seat correction landed only at its turn end (subagents receive at yield), by which time it had fixed ALL F1-F8 (`bf4b837`,
  `d22f1aa`) and written RESUME HERE (`37cf14a`), under the 370K cap; **cell 2 (opus-high) DISPATCHED**, reading only until W2
  closes, then Reviewer A round 2 on the remediated head, the two-leg window, the report.
- (history) W1 OPEN ~19:20Z (msg `65c91896081df817`; collections 5,289 all / 1,114 serial). WP-T5 turn 1 `a9abb8d`
  (depth 138,874): rung 0 done, frame counts 9 / 3 / 2 confirmed, no frame-count branch between 3 and 9; Codex sandbox stalled on
  CuPy import at collection, so the orchestrator collects at its seat (recorded). WP4.1 round 0 RULED at the orchestrator's seat
  (FYI `a83c68c87441b510`, ledger b8b2485, depth 140,680): S1 N10 brief text corrected to AD-11 pre-encode (provenance `created`
  differs by design); S4 `tests/test_app_deps.py` GRANTED to WP4.1 (the one gui-to-app edge + no PySide6/CuPy on importing
  `clearwater.app`); S2-S7 inside the brief. Nothing to rule.
- **WP4.1 S8 RULED (A) 19:29Z (query `ec230a99117732c4`; my msg 53d047cf): V9's reference for an export BELOW the source depth =
  the source quantised to the export depth by the writer's rule; AD-11 bound unchanged; raw error recorded and asserted for 16-bit
  exports and 8-bit sources; ICC = source's or the D53 built-in; planted control kept. AD-11 clarified (dated) in decisions.md at
  this seat. W1 STANDS despite the cell's ~4 s probe inside it (orchestrator's slip, recorded).**
- **Owner-pending inputs (carry):** photos (WP3.6P; WP4.1 records the owner-photo leg OWED), the iPhone clip (DR-15), the N6 body
  erratum DR-64 (apply on the owner's word 'apply N6 erratum' as spec v0.5.6). Open owner decisions: none. Every owner-facing
  summary ends with that line.

### Phase / state

**Phase 4 (integration) in flight: WP-T5 ACCEPTED 4933a45, WP4.1 at its own gate, WP4.2 / WP4.3 DRAFT RULED.** Plan
`docs/clearwater-implementation-plan.md` v1.2. **CHARC generation 6** (RESUME HERE above); gen 5 = `clearwater-charc-20261028-0647`. Gen 4 = `clearwater-charc-20261026-2007`
(fable/medium), launched by gen 3 at 06:07Z, picked up 2026-10-27 ~06:10Z from main 08a14ee; bash gauge
44 ms. Main ~1295 commits ahead of `origin/main`, unpushed; no push asked (verify `git status -sb`).

### Generation 4 (2026-10-27 06:10Z to 2026-10-28 16:35Z; rolled at ~390K; kept as record)

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
- **MICRO-TIMING CLOSED ~09:10Z; TASK 6 GO + Q-C5a RULED (msg `62e85d40722a00c8`; my ruling-task6).** Cb/Cr blurs (sigma 108) =
  0.198 of a 0.504 s render (39 %; total blur 71.4 %); per-axis FFT 0.0185 s -> -0.180 s/frame; projection 15.37 -> ~10-11
  min/min at 4K (AD-21 target); max abs 2.2e-7..2.9e-6 deterministic (3x inside 1e-5). Gate stays 1080 / 32; per-axis; mask
  blur direct; 2-D variant recorded not built. Run 1 died from the DRIVER never freeing plans (instrument fault). **Q-C5a = (a)
  default plan cache + (1) `CupyBackend` method clearing plans and pool free blocks, called by export.py at JOB END in the
  `finally`, never per frame; (2) persistent plan bytes counted in `memory_estimate_bytes` and reported separately at 5.3K.
  Max-parameter 5.3K row: YES; on breach the gate keys on PROJECTED plan+buffer bytes vs a FIXED budget constant in core, never
  live free memory (deterministic path per inputs); breach at DEFAULT params at 5.3K = STOP to me.** 5.3K estimate ~7.3 of 8 GB.
  Relayed to cell 5 in full 09:15Z (msg `c620af9a4886d174`; depth 141,332); cell finishes the Q-R7 tool-side stamp then builds task 6;
  memory re-read and oracle legs come as windows.
  **STOP yield 13 (msg `f0c06f32e48bc68e`, depth 163,071): the 5.3K FFT figure was WRONG, plans are ADDITIVE to the transient
  (one plane ~0.55 transient + ~0.5 persistent = ~1.05 GiB; 5.3K default c3 ~7.8 of 8.0 GiB, no margin); plan size depends on
  transform LENGTH not shape. RULED (A) CHUNKED per-axis (my ruling-chunked): batch = FIXED 512 lines in core, last batch = the
  FINAL 512 (overlap recomputed); REQUIRED test bit-identical to unchunked on non-multiple-of-512 shapes at 1080p / 4K / 5.3K;
  Q-C5a (2) restated as a BOUND per line length measured with the plan cache CLEARED first, added to memory_estimate_bytes for the
  clip's longer side, test asserts peak < bound; (1) job-end release and the fixed-budget projection rule unchanged. Expected 5.3K
  default ~7.0-7.1 GiB; task 10 5.3K row = measurement of record, breach = STOP to me.**
  **Task 6 gate/route/release BUILT `7061699`** (msg `909645ddab0d76cf`; cell 5 depth 232,900 at yield 14): `FFT_MIN_SHORT_SIDE` 1080 /
  `FFT_MIN_SIGMA` 32 in core, `fft_route(h, w, sigma)` reads shape + sigma only; per-axis rfft inside `gaussian_blur` on both
  backends; `CupyBackend.release_fft_plans()`; tests (a) proxy tripwire max short side 1079, (b) 1079-high blur bit-identical CPU +
  GPU, (c) 1080p / 4K / 5.3K within 1e-5 deterministic + GX011627 frame 0; light 2,156 passed. Orchestrator placement ruling
  CONCURRED: release in `_run`'s finally (covers photo jobs; a 12 MP photo meets the gate), logged if it raises, never replaces the
  outcome. **OWED AT WP3.21's ACCEPT (mine), now THREE rows: WP4.2 `device_backend=<GPU backend>`; WP4.3 GUI preview >= 1080 short
  side releases FFT plans at a preview boundary (clip change / unload) and counts them in its memory reading; DR-63 CLOSED.** Cell 5
  finishes batching (A), the estimate fold + bound test, ONE window (4K + 5.3K memory re-read + oracle legs), then hands to **cell 6**
  (Reviewer A, two-leg suite, task 10).
- **TASK 6 ORACLE COMPLETE; gxa CLOSED 10:03Z TIER1 (681 / 0, max abs 0)** (msg `37613171b50ac33d`; gxa OPEN `d814b05852784c29`).
  Summary: WP2.3 TIER1 x10; GX011627 c3 TIER2 7.06e-6; synth 4K c3 TIER2 2.44e-6; GX011627 ancuti2018 TIER1; records / proxies /
  source stats / analyze calls / pts equal in every TIER2. Quantised figure (mandatory): 8-bit on the 23 sampled frames = 14,793 of
  572,313,600 channel values change (2.58e-5), none by more than ONE code value, under AD-5 `floor(x*255+0.5)`; 10-bit count/max
  + a check that the sink's device `rgb_to_planes` rounds by AD-5's rule = cell 5 if depth allows, else cell 6's first item.
  **Quantised figure COMPLETE by the PRODUCT's rule** (msg `a06e41142eaa40f0`; cell 5 `aa06584`): the sink rounds HALF TO EVEN
  (`xp.rint` after clip and float32 scale, `core/backend.py` ~637-665), NOT AD-5's floor+0.5 (the proxy's rule); on the 23 frames
  8-bit 14,858 changed (2.60e-5), 10-bit 60,692 (1.06e-4), max 1 code value; by AD-5 14,856 / 60,459. Report names the rule.
  **Cell 5 STOOD DOWN at 326,666; CELL 6 DISPATCHED 10:06Z** (`wp321-cell6`, opus-high, from aa06584): Reviewer A (Codex
  gpt-6.1-sol/high at its seat, WSL, probe first, five-round gate), then two-leg suite one window per leg, then task 10 LAST under
  the binding memory method, then the report. **No window open; seat free.**
  **Reviewer A r1 (Codex, cell 6, `wp3.21/r1/`): NEW_CRITICAL_MAJOR_FOUND, 0 critical, 6 major reported** (FYI msg `cec78dcf31626489`):
  F5 CONFIRMED BLOCKING (Q-R6 extrapolation returns 0 on a retry when the old incomplete entry already covers the lead; fix in
  export.py = extrapolate from the entry's own bytes per stored frame, failing-first); F2 ruled (a) MINOR at the orchestrator's seat
  (sink.abort() BEFORE joining A on failure/cancel, releases the encoder at once; R0.2 text corrected; order pinned by a test);
  F1 / F4 rejected (DR-57 (b) hung-encoder case; V17 complete semantics); F3 banked to Limits; F6-F9 minor in the cleanup; F10-F11
  out of envelope. Cell 6 depth 140,415; round 2 after F5. Nothing to rule.
- **ORCHESTRATOR GEN 15 -> GEN 16 ROLLOVER 2026-10-28 ~12:19Z (clean boundary, ~390K; state 9b8e848; msg `dc69718c8543960b`).**
  **Gen 16 = `clearwater-orchestrator-20261028-0219`, ONLINE 12:21Z at 9b8e848** (re-read `comms/.launch-sessions.json` before every
  cue); gen 15 stopped draining. Gen 16 relays my
  STOP ruling and dispatches **cell 7** from ledger RESUME HERE `ea78946` (line 1767). **Ruling (A) relayed in full; cell 7
  DISPATCHED 12:23Z** (`wp321-cell7`, opus-high, depth 0; msg `a9e0cb823b141331`; state cfc4d4c): fix -> V8 + prototype pair (light)
  -> serial leg (window) -> task 10 last (one window per block) -> report -> return report; then Reviewer B at gen 16's seat, accept.
- **BLOCK 2 CLOSED 14:07Z = STOP (msg `1e9174b629179d0a`): synthetic 5.3K c3 cold, job ok, 1.1830 s/frame = 35.46 min/min [136.03],
  but device-wide GPU peak 7,854 MiB (idle 248) > estimate 6,281 AND > base x 1.25 = 7,371; FLAT plateau 7,853 during the OVERLAP
  (18-55 s; two decoders + analysis on device frames + render), 6,598 frames-only after the analysis returned at 78.9 s, 5,462 late;
  334 MiB under the 8,188 card (cell reads pool growth into free memory, NOT proved); RSS 7,405 MiB [6,354], N4 holds; 4K rows x
  1.30-1.35 their baseline (not a STOP). Cell 5's in-process re-read had the 5.3K RENDER at 2,710 MiB, so the device-wide figure
  carries NVDEC x2 at 5.3K + NVENC + two device-frame sets + pool cache, unattributed. **RULED (A) GRANTED (my ruling-5k3): one
  ~4 min EXCLUSIVE attribution window, uncommitted driver under work/wp3.21/, in-process pool used/total per sample + plan cache +
  per-pid nvidia-smi if WDDM reports it; split the 7,854 and the overlap's +1,256 before any fix is ruled; no product change, no
  commit. Block 3 (GX011625) HELD.** Cell 7 depth 167,263; ledger f6c9511.
- **ATTRIBUTION CLOSED 14:27Z (msgs `948b4bfaa1d35f1e`, addendum `77343768b31407e4`): the 5.3K breach is DEVICE-WIDE ONLY.**
  Pool reserved peak 4,427 MiB ON / 3,628 OFF (UNDER AD-1's 6,281 and base 5,897); remainder = FFmpeg export decoder + NVENC
  ~2,445 every phase + the overlap's SECOND decoder ~790-1,240 (vanishes when the analysis thread exits; OFF still 7,593) +
  context ~250; pool CACHED 1,246 at peak / 3,483 plateau never returned before job end; analysis-half device frames ~800 pool /
  ~330 device-wide (secondary). nvidia-smi per-pid [N/A] under WDDM; per-thread pool not measurable (one shared pool; timing
  attribution recorded as a label). **FIX RULED (my ruling-5k3-fix): (b3) AD-1 gains a device-wide JOB term (pool estimate +
  context + decoders x NVDEC + NVENC; constants from these remainders; overlap = two decoders) in `core/memory.py`, selection
  UNCHANGED; plus ONE `free_all_blocks` at the analysis-end boundary in `jobs/export.py` (bounded, no arithmetic change). (b2),
  (b4) not taken; (C) owner-reserved, not taken. STOP test for the re-run = BOTH instruments (device-wide vs the job total;
  pool peak vs 6,281). Then light set -> TWO-LEG SUITE again on the final head -> block 2 re-run -> block 3 LAST -> report;
  Reviewer B reviews the FINAL head with the post-convergence diff named; cell 7 (223K) takes the fix + 5.3K re-check, cell 8
  the suite, block 3, report. AD-1 AMENDED (dated) in decisions.md.** **No window open; seat free.**
  Relayed; seat SET (msg `066a5ccab8691211`): cell 7 fix -> light set -> block 2 re-run (both instruments) -> RESUME HERE; cell 8
  two-leg suite on the final head -> block 3 LAST -> report (block 2 before the suite still measures the final head since the suite
  changes no code). **Scaling of the NVDEC/NVENC terms PRE-RULED (my msg ack-scaling): SCALED by pixels with a per-session FLOOR,
  term = floor + per_pixel x (W x H), constants fitted from the 5.3K remainders and the 4K cold-row peaks (two sizes, two
  constants), 1080p by extrapolation stated as such; the total must cover every measured device-wide peak; the cell yields the
  fitted constants and the checks before coding (b3).**
  **Fit UNDERDETERMINED (4 constants, 3 equations; the 4K pool during the overlap never measured; a common floor fits NEGATIVE
  with the pool at its estimate) -> RULED (my ruling-fit, msg `7fbfe9f761dde8fe`): (1)(a) ONE 4K attribution run (GX011627 ON, same
  uncommitted driver, ~4-5 min) GRANTED, FIRST in block 2's re-run window; exact fit, constants rounded up, a floor <= 0 clamped to
  0 (per-pixel form (S) as a result); covered-row test incl. the 4K run. (2)(a) pool term stays the selection bound; job total at
  5.3K (~10.1 GB) exceeds the card by design (pool part loose: 4,427 vs 6,281), stated in docstring + record; BINDING 5.3K check =
  instrument (ii) pool peak vs 6,281 + covered rows; (i) binding at 4K. Verified: `memory_estimate_bytes` consumed ONLY by
  select_backend (core/backend.py:613) and the IF-2 method, so the figure misleads nobody; showing it is WP4.3's business. Part 2
  (boundary release in `_Analysis._run` finally, once per job; planted 64 MiB test; F2 order re-pinned abort -> boundary -> release)
  ACCEPTED as built (b5a383c). Cell 7 266,488, continues for the bounded remainder.**
- **EXCLUSIVE WINDOW OPEN 2026-10-28 ~16:27Z: WP3.21 TASK 10 BLOCK 3, GX011625 x1 cold c3, LAST (~1.5-2.5 h; fresh process;
  check at 4K: (i) device-wide vs job estimate 4,065 BINDS, (ii) pool peak recorded; either failing = STOP)** (msg
  `6eb83eba33be44c5`). **NOTHING HEAVY AT THIS SEAT until CLOSE.** Then report, return report, Reviewer B at gen 16's seat, accept.
  Cell 8 depth 83,323; head 29e068e (ledger-only since 227ed32).
- **TWO-LEG SUITE GREEN on code 227ed32 (16:25Z): parallel 4174 / 1; serial 1113 / 1 (`test_photo_check.py:139`), 2,685 s, 0
  failures.** (serial OPEN was `03f2d48ac0937e35`.)
  **Retroactive GRANT (msg `6c5c116644bf5d62`): `src/clearwater/analysis/__init__.py` +6 additive re-exports (`AnalysisDeviceBackend`,
  `frame_block_mean`, `frame_pixels_for_proxy`) in 05ee507 (#3 under AD-29), not in the brief's owned files, no ledger grant ->
  GRANTED, named in the record's owned-files list; the ungranted edit itself = a ledger finding (should have been a STOP), MINOR.**
- **PARALLEL LEG GREEN on the final head 15:38Z: 4174 passed / 1 skip (`test_color_roundtrip.py:121`) / 0 failures, 488 s; head 2b14e21,
  code 227ed32** (parallel OPEN was `afaadfc07237ce40`; it ran 15:30-15:38Z). Recollection 5,289 / 4,175 /
  1,114 explained: parallel +27 (`test_wp321_job_memory.py`), 3 ids RENAMED by part 2 in `test_wp321_fft_release.py` (none removed);
  serial +1 (gpu boundary-free test). Naming point banked for B: `...releases_at_the_analysis_end_and_after_every_frame` asserts
  exactly TWO releases (name overstates; assertion right) -> rename in B's cleanup or a MINOR. Cell 8 dispatched ~15:27Z from
  61a3e08, depth 62,302. Then SERIAL leg (own window), block 3 LAST.
- **WINDOW CLOSED 15:21Z: BLOCK 2 RE-RUN PASSES BOTH INSTRUMENTS on 227ed32** (msg `37be8fe8cb46f38f`): (ii) pool reserved peak
  4,311.7 MiB <= 6,281.4 (binding at 5.3K); (i) device-wide 7,901 <= job estimate 10,330.8 (idle 256); speed 1.2229 s/frame = 36.65
  min/min [136.03]; RSS 7,753. 4K attribution (GX011627 ON): peak 3,054 (pool 1,353, remainder 1,586), frames-only 2,433, NVDEC
  increment +472.0; the part-2 boundary free returned ~150 MiB. **Exact four-point fit, NO clamp: NVDEC 80 MiB + 51 B/px; NVENC
  368 MiB + 36 B/px; context 272** (solved 75.4 + 50.14 / 364.2 + 35.17; residuals 10-25 MiB; 1080p extrapolated 181 / 439). ALL
  covered rows pass with margins 652-2,946 MiB. Light 226, WP3.14 bench/select tests unchanged, 0 CR since afad7af. Post-convergence
  range for Reviewer B = afad7af..227ed32 (export.py boundary free; memory.py estimate + fit; export_bench two-instrument check;
  3 test files). **Cell 7 STOOD DOWN 344,750; cell 8 next from 61a3e08:** recollect both sets, two-leg suite on the final head (one
  window per leg), block 3 GX011625 LAST, report, return report. **No window open; seat free.** Fit script evidence
  work/wp3.21/fit_sessions.py md5 23391ae7.
- (history) window OPEN ~15:07Z (msg `fc94c9446ebfde88`). (b3) built 9a4256b: `core/memory.py` `session_bytes` + `job_device_memory_estimate_bytes(h, w, pool_estimate, *,
  decoders, nvenc)` (pool estimate passed in; memory.py backend-free); `export_bench.py` record `memory_check` with (i) and (ii) +
  passes; 26 tests; light 225; WP3.14 bench/select tests unchanged. The cell's provisional fit from cell 5's render-only pool
  crossed my ruling; the orchestrator corrected the order (measured 4K first). **DEVIATION ACCEPTED: the job cannot REPORT the
  total itself (IF-8 JobResult FROZEN, no field); the bench record reports it; no product-side reporter; folded into the WP4.3
  register row I owe (show the figure = IF-8/IF-2 extension, WP4.3's if its GUI wants it).** Cell 7 depth 305,720.
- (history) attribution window OPEN ~14:20Z (msg `4ebb2986077a3c1e`).
- (history) block 2 OPEN ~14:03Z (msg `f643b1059bdc063a`). STOP test
  (conservative): nvidia-smi device-wide memory.used (same instrument as the baseline 6,104; ~250-330 MiB idle + decoder + NVENC
  sessions) vs 6,281 (5,897 + 384) and vs base x 1.25 = 7,371; above either = STOP to me, idle offset stated. Block 3 GX011625
  (~1.5-2.5 h) LAST in its own OPEN. Cell 7 depth 154,676.
- **BLOCK 1 CLOSED 13:59Z (GX011627, 681 frames, device frames ON, hw decode ON): V16 FIGURES OF RECORD.** c3 cold x3 0.3195 /
  0.3264 / 0.3310 s/frame = **9.57 / 9.78 / 9.92 min/min** [WP3.14 31.8-31.9] (RSS 3,394-3,417 / GPU 3,130-3,244 MiB); c3 warm 9.06
  [23.2] (labelled per (a)); ancuti2018 cold 8.74 [21.6]; libx265 cold 14.59 [35.6] (stray System 41.5 % CPU kept as spread); OFF row
  (device frames off) 17.25 -> #2 + #3 worth ~-0.25 s/frame, lead 19.7 -> 5.2 s. Every NVENC row meets D106's 25; cold c3 meets the
  ~10 aim (AD-21). **Slow frames PLACED: every 16 frames in every cold device-frames row (c3 19, 35, ... 611; ~0.55 s vs 0.29-0.30
  median), stopping where the analysis thread returned, none in the warm row; record_wait sums 10.7-11.5 s = the excess; cause =
  `analysis/engine.py` STREAM_STEP 16: with the FFT the frame loop OUTRUNS the streamed analysis, so the overlapped job is now
  ANALYSIS-BOUND. No fix in this package; report names the analysis pass as the next target.** -> FOURTH register row owed at the
  accept (analysis-bound overlapped export; lever = the analysis pass, not the step). Code head 57a7a2e. Cell 7 depth 123,491. **Warm-row memory
  method RULED (a): run as is; label the warm row's GPU peak "includes the prime analysis's pooled blocks (the product's own
  state after an analysis)"; the 5.3K COLD row is the figure of record and carries the STOP check; no tool change after
  convergence.** GOP check (light): 681 packets, no B-frames, keyframe every 30; frames 323 / 387 are NOT keyframes, so decode
  seek does not explain them; task 10 per-frame records place them.
- **SERIAL LEG 2 CLOSED 13:18Z GREEN: 1112 passed / 1 skip (`test_photo_check.py:139`) / 4148 deselected, 2,661.52 s; TWO-LEG SUITE
  GREEN at afad7af** (parallel 4147 / 1 on identical node ids). Ledger 6c27111. (serial 2 OPEN was `808413c57ac3fbfa`.) Fix = one autouse fixture
  appended to conftest.py (only `import sys`; acts only when cupy AND clearwater.core.backend are in sys.modules and `_probe_gpu` ran;
  calls the probed backend's release_fft_plans; never touches cupy). Condition 1 AST proof EQUAL (20 nodes, docstring equal); condition
  2 failing-first (pair 1 failed -> 10 passed; pin test `test_wp321_conftest_release.py`); condition 3 parallel ids IDENTICAL (no
  re-run), serial 1,113 = 1,111 + 2 pin tests. **Narrowing ACCEPTED: plans from a DIRECTLY built CupyBackend before any probe are not
  released (only tools/core_speed.py, own process).** Cell 7 depth 97,433. Task 10 per-block windows follow.
- **SERIAL LEG CLOSED 12:09Z: 1 FAILED / 1109 passed / 1 skip (`test_photo_check.py:139`; WP-T4's nine V8 skips RAN here because
  the worktree's `working_path` is the main tree's work/) / 4148 deselected, 2,603 s; 1,111 collected vs WP-T4 1,046. STOP (msg
  `f97615d46b8e9d98`): `test_prototype_backend.py::test_bench_gpu_records_graphics_memory` fails (0.133 >= 1.0) because task 6's
  cuFFT plans from the V8 1080x1920 crops stay in pytest's main-thread plan cache and the prototype bench counts them as its own
  reserved pool; passes alone; repro ratio 1.669 -> 0.100 after one 4K FFT blur -> 1.668 after release. RULED (A) (my
  ruling-plans-conftest): `tests/conftest.py` GRANTED for one autouse fixture releasing plans after each test via core's entry,
  only when cupy is already in sys.modules, importing nothing new; guard + WP-T4 docstring untouched (ast.dump proof); pair test
  pins it; serial leg again in its own window (parallel: recollect, re-run only if the count moved); task 10 LAST; report Limits
  states 'any caller outside a job keeps its thread's plans until release' (WP4.3 row = the product case). Cell 6 STOOD DOWN
  ~258K. **No window open; seat free.** Recipe rule added: a deletion grant names what is KEPT in the same message.
- **(history) serial leg window OPEN ~11:25Z** (msg `9eaa4c78e158e9db`). Cell 6 depth 227,414.
- **PARALLEL LEG CLOSED 11:23Z: 4147 passed, 1 skipped (`test_color_roundtrip.py:121`, the same single skip as WP-T4's 4031 / 1),
  575 s, EXIT 0; 4,148 of 5,259 collected (+116 tests in this package).** Orchestrator deletion-grant SLIP recorded: 27 superseded
  oracle candidate folders (cand-devframes-*, cand-ad29-*, cand-i2-*, ~11 GB) deleted whole before the amendment to keep each
  `oracle.json` landed; lost = per-run oracle.json for H7-H14 (development evidence, superseded by cand-fft-*); verdict lines
  survive in the logs and the ledger; every ref-* and cand-fft-* intact. Not a register row (work/ evidence). Lesson noted: a deletion
  grant names what is KEPT in the same message. (parallel OPEN was `d113bb7affcf0675`.) **Reviewer A CONVERGED r2** (NO_NEW_CRITICAL_MAJOR, evidence wp3.21/r2/; F5 fixed
  9d73fe4 with failing-first retry test 0 -> 23,040 bytes; F2 order abort -> join A -> release pinned; cleanup 1df2626 tools+tests
  only; light 2,655 passed). Cell 6 on 012641e.
- **ORACLE LEG synth CLOSED 09:58Z: synthetic 4K c3 TIER2 as expected, 120 frames, max abs 2.44e-6, mean abs 2.62e-7; records/proxies
  equal by construction** (synth OPEN was `1e7d4c07c4a26046`). Cell 5 depth 310,029 at the synth OPEN.
- **ORACLE LEG gx CLOSED 09:56Z: GX011627 c3 TIER2 as expected, 681 frames differing, max abs 7.06e-6, mean abs 7.95e-7 (AD-11
  2e-3 / 2e-4); records (681), proxies (681), source statistics, analyze calls (1,362), pts ALL EQUAL (any inequality there = FAIL
  by the oracle's construction, `export_oracle.py:555-594`). WP2.3 legs TIER1 x10 max abs 0 (light).** CORRECTION accepted (msg
  `df7ed96f118b8951`): the oracle compares FLOAT pre-encode frames at the sink seam, so "no exported pixel changes" is NOT
  established; a float within 7e-6 of a rounding boundary flips one code value. Report wording = the orchestrator's; the quantised
  difference on the 23 sampled frames (8- and 10-bit, count and max of changed pixels) is MANDATORY (light, from the saved .npy). (gx OPEN was `341e39c6ab4c4018`.) Then synth (TIER2 expected) and gxa (ancuti2018, TIER1) each in its own OPEN; WP2.3 legs light outside windows.
  Cell 5 depth 298,494 at yield 16; runs the legs then hands to cell 6.
- **MEMORY RE-READ CLOSED ~09:50Z: every peak under base + bound; max-fraction 5.3K inside the card, projection rule NOT
  triggered.** 4K default 908 MiB (plans 30, transient 878) vs estimate 2,174; 4K max 947; 5.3K default 2,710 (97 / 2,614) vs 6,281;
  5.3K max 2,798 (184 plans). Render-level FFT saving: 4K 0.388 -> 0.207 s/frame (-0.181, confirms the micro-timing); 5.3K 2.930 ->
  0.777 (-2.15); at 5.3K the mask blur (46.5 px) also meets the gate. (history: memory window OPEN msg `afe6000f86033792`.) Task 6 (A) built
  `17743ec` (cell 5 depth 289,841 at yield 15): batches <= 512, last = final positions; **FINDING: odd cuFFT lengths are batch-
  position dependent (1 ulp), so the route takes the smallest EVEN fast length** (accepted numeric detail of the ruled path, no tier
  change); chunked == unchunked bit for bit at 1080p / 4K / 5.3K non-multiple shapes GPU + 1080p CPU, pinned. Bound
  `fft_memory_bound_bytes` = 48 B x 512 x L (L = pow2 >= longer + 2(shorter+1)) = 96 / 192 / 384 MiB; measured 5.3K default
  111-124 MiB (54 plans), max fractions 227-255 MiB (112 plans); unbatched 1.05 GiB -> batched 0.11 GiB; GPU test peak < bound.
  **QUERY RULED (a): `select_backend` stays on AD-1's BASE estimate (bound <= 384 MiB inside the 1.25 margin; pinned 4K figures in
  `test_core_select.py` and IF-2's example text unchanged); `CupyBackend.memory_estimate_bytes` = base + bound is the AD-1 figure
  the re-read and task 10 check; task 10's 5.3K peak settles it.** Then oracle legs (GX011627 c3 TIER2 expected, synth 4K TIER2,
  ancuti2018 TIER1) each in its own OPEN; cell 6 before them if cell 5 passes ~330K. **No window open; seat free.** (superseded by the OPEN above)
- **(history) micro-timing window ~08:43Z** (msg `f02a8e3d3ecf679e`). Measures: blur share of c3 render at 4K (CUDA events, median of 20); each render
  blur direct vs R0.4 per-axis FFT and 2-D FFT (time, max abs, determinism, pool bytes); sigma ladder 8-270 at 4K and 5.3K 8:7.
  Dry run 1080p synthetic: blur 57 % of render; gate-eligible = the two Cb/Cr blurs at 0.05 x short side; FFT error <= 8.6e-7.
  Cell 5 depth 87,298 at yield 10, branch 650a693. After CLOSE: share, projected saving under the Q-R1 gate, max abs vs 1e-5,
  5.3K peaks, build-or-yield for task 6 -> forwarded to me BEFORE any FFT code.
- **WP3.21 INTERIM 2 CLOSED 08:34Z: TIER1 x3 (GX011627 c3 681/0 max abs 0; synth 4K 120/0; GX011627 ancuti2018 681/0); bench
  GX011627 cold c3 device frames ON = 0.5130 s/frame = 15.37 min/min (DEVELOPMENT evidence, not V16; interim 1 24.28); frames
  phase 0.501 s/frame (interim 1 0.778; serial path 0.714); lead 5.28 s; median 0.483, p90 0.534, max 0.965; RECURRING ~0.96 s
  frames at indices 323 / 0 / 387 = FINDING for task 10 to place; peak RSS 3,393 MiB, graphics 3,138 MiB (+0.26 GB at 4K vs the
  +0.13 estimate, inside AD-1; 5.3K row = watch)** (msg `494cd8a04f40f124`; OPEN `e09002e4eb2349ec`; product 0ed0672, records
  git_head 23f8918 ledger-only). **No window open; seat free.** Cell 4 records H11-H14, writes RESUME HERE, stands down; cell 5
  (opus-high) **DISPATCHED 08:38Z** from `wp3.21` 74c97bf (cell 4 final 257,383; RESUME HERE ledger line 30; msg
  `e718f9408dc84098`); my four readings in its prompt; FFT gated: WINDOW RELEASED states the blur share + build-or-yield, the
  orchestrator confirms before any FFT code, a yield comes to me. No window open. Cell 4 yield 8, depth 236,806: `05ee507`
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

- Spec `docs/underwater-correction-spec.md` **v0.5.6** (text only, owner 2026-10-29 verbatim "Apply N6 erratum": N6 body = D106's interim; v0.5.5 owner 2026-10-27 verbatim
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
