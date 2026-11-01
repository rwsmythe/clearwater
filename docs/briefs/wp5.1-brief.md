# WP5.1 — Automated acceptance suite (dispatch brief)

**Status:** FINAL 2026-11-01 on CHARC commission post `05533fa67a11cee3` (file `20261101T081408Z-...-b488ac53.md`, 2026-11-01T08:14:08Z); drafted by CHARC (generation 10, session `clearwater-charc-20261031-2201`); the dispatch fill (base, lane, GATE_CHECKS, yields) folded in by the orchestrator (generation 28) at the end of this brief.
No tripwire (plan section 3): tests and a report only; no product module, no
dependency, no frozen interface, no persistent-data shape. Spec v0.5.7, no clause changes. Owner
decisions inside: NONE. The Questions carry CHARC's recommended answers; a round-0 dispute with
evidence is a STOP to CHARC.

| Field | Content |
|---|---|
| ID and title | WP5.1 — Automated acceptance suite: the spec section 11 tests that package tests do not yet complete, built as committed tests through the shipped runner and shell; the whole set run once; a traceability report V1-V18 to test nodes and results |
| Lane | **CODEX**: `implementer-codex-sol-high` (a brief that fixes the tests, the oracles and the bounds; no frozen interface; the Claude lane is at its weekly ceiling until 2026-11-02 10:00Z). Reviewer A = the Claude pass (`claude -p --model opus --effort high`) between turns, to convergence, five-round gate. Reviewer B = the Claude pass at the orchestrator's seat. Evidence `C:\Users\rwsmy\clearwater-review-evidence\wp5.1\`. |
| Tier and size | **STRONG** (these tests gate the release, WP5.5). Size L per the plan, delivered as ONE rung: four new test modules, one support module, the report. Codex STOP line near 250K; the orchestrator names the yields (after T2, T4, T6, T8 below). |
| Base | main at dispatch (`dd3cf1eb` + the fill commit; floor WP4.3 `28c4a75`). The cell does NOT wait for WP3.6P or WP4.6: their accepts land on main while this package runs and touch no file it owns; the gate runs on the final rebased candidate. Worktree `.worktrees/wp5.1`, branch `wp5.1`. |
| Goal | Every acceptance test in spec section 11 that plan section 7 completes in WP5.1 (V1, V3-V11, V13, V17, V18; plus N10 / D92 and D91 which plan :405-406 assign here) has a committed, passing test node or a cited figure of record, and the report says which. The gaps found by CHARC's coverage pass (below) are closed with new tests through the SHIPPED paths (`tools/headless_export.py` for exports; the running shell for the `gui` legs). A gap that turns out to be a PRODUCT defect is a STOP to CHARC with the failing node and its evidence: this package edits no product code (plan 6: "failures go back to the owning package"). |
| Spec / decision clauses | Section 11 V1-V18 as quoted below per task; AD-11 (tolerances: V9 pre-encode max 2/255 mean 0.2/255; V8 mean 1/255 max 3/255; N10 bit-identical pre-encode on one device); the WP3.5 characterisation bounds for the post-encode pair (`tests/test_color_roundtrip.py:44-59`: `PAIR_MEAN_SYNTHETIC` 2.5, `PAIR_MEAN_REAL` 1.0, in 1/255); AD-13 (file names only in records); AD-24 (HEIC orientation rule); AD-28 / AD-30 (two legs, markers, sizing: six frames and 1080p unless the subject is the real container); D63 (the four EXIF edits); D81 (a failed item is logged, the batch goes on); D84 / D25 (numbering, `.mov` writes `.mp4`); D85-D87 (safe write, leftovers, disk space); D91 (provenance on by default, can be off); D105 / D114 / D115 (V4 mandatory and best-effort sets, the VFR sample); spec 5.3 / 5.4 / 6.5 (refusals; the BT.709 limited assumption text); G10. |
| Files owned | **NEW:** `tests/acceptance_support.py` (helpers: run the runner in-process via `headless_export.main(argv, exports=...)` and as a subprocess; FFmpeg decode of an output to arrays with `tools/lookcheck/frames.py`'s decode command form or `tools/video_fidelity.py`'s; md5 of a file; the two-reader PNG decode; the provenance readers already used by `tests/test_io_video_encode.py:1312` and `tests/test_wp41_photo_path.py:258`), `tests/test_v51_photo_acceptance.py`, `tests/test_v51_video_acceptance.py`, `tests/test_v51_shell_acceptance.py`, `tests/test_v51_traceability.py` (T9), `docs/reports/wp5.1-acceptance.md`, `docs/proofs/wp5.1-ledger.md`. **READ only:** everything else. |
| NOT owned | `src/clearwater/` whole; `tools/` whole (the runner, `video_fidelity.py`, `export_oracle.py`, `lookcheck/` are imported or imitated, never edited); `tests/conftest.py`, `tests/fixture_plugin.py`, `tests/gui_support.py`, `tests/fixtures/` (the session fixtures `gx011627_trim` / `gx011627` and the manifest are USED); every existing test file (no edit, no weakening, no duplication of a passing node: a gap is a NEW node); `pyproject.toml`, `uv.lock`; the register and the decisions log (CHARC's). |
| Locks | No product edit (a defect = STOP). No existing test edited. Footage folder read-only; the only real footage used is the `gx011627_trim` session fixture (a stream copy under the temp root) and, for V6's untagged text in the shell, the committed fixture: NO new footage file is named. Every write under `tmp_path`. Records and messages checked for file names only (AD-13): a full path in any new record is a failing assertion. Bounds are those named in this brief; a figure over a bound is a STOP with the figures, never a raised bound. |
| Markers | Parallel-leg when a node runs under 5 s on the owner's laptop with FFmpeg (measured first, AD-30; six-frame fixtures, 1080p); `slow` with the reason "runs the headless runner as a subprocess" or "FFmpeg encode" when over; `gui` for every shell node (`QT_QPA_PLATFORM=offscreen`, `tests/gui_support.py`'s helpers); `footage` for the `gx011627_trim` nodes; `gpu` for the one GPU form named in T7. No `fullclip` node is added. Serial-leg budget: the new marked nodes add at most 180 s to the serial leg (figures in the report; over = report and CHARC rules). |
| Hardware flags | None of record. The gate (two legs + ONE `fullclip` leg: this is the phase-end whole-set run) runs at the orchestrator's seat with no window open and no other heavy job (the WP5.3 build pieces and the dangler windows are scheduled around it). |
| Out of scope | V2 (WP5.3 / CP5); V12 (v2); V14 (the gate report `docs/reports/wp1.6-gate-report.md`, cited); V15 / V16 (WP5.2); V7 and V18 re-measurement on GX011627 (window evidence of record: WP4.3 and WP4.6; cited with DR-98's status at report time); the V3 real static clip (none identified in the inventory; stated); any product fix; any tolerance change (AD-11 is "tunable after WP5.1": a proposal goes in the report for CHARC, the tests keep the current bounds). |
| Debt and decided items | At the accept CHARC writes: the acceptance matrix pointer in the plan (section 7 completion), AD-11 NOTE (bounds held or a tuning proposal), DR rows for every STOP that was a product defect (routed during the package), the WP5.5 release checklist input. The cell writes no register row. |
| Done | Plan 4.5. ruff check, ruff format --check, mypy strict clean (the test modules are typed like their neighbours); every new node green on the two legs; collection identity holds (parallel + serial + fullclip = all); Reviewer A converged; Reviewer B returned; the ONE gate = parallel + serial + the `fullclip` leg on the final candidate at the orchestrator's seat, figures in the report; the report's matrix lists for each of V1-V18, N10 and D91 the node ids (existing and new), the markers, the leg, the result and, for the window-measured items, the figure of record and its source; the serial-leg delta recorded. |

## Why

Plan section 7 completes V1, V3-V11, V13, V17 and V18 in WP5.1 and names WP5.1 for N10 and D91.
CHARC's coverage pass (2026-11-01, against main `928760a7`) found the package tests already prove
most of each V and left these gaps, each quoted from section 11:

| Gap | Section 11 clause | Today |
|---|---|---|
| G1 | V5 "orientation correct for rotated and portrait sources in multiple viewers" | one reader (`test_wp41_photo_path.py:308,325`); the docstring at `:7` names this as WP5.1's leg |
| G2 | V4 "best-effort: which of creation time, GPMF, timecode and camera atoms are present is recorded" | the instrument has the class (`tools/video_fidelity.py`, `test_video_fidelity.py:123`); no node records the list per output |
| G3 | V4 "the test set includes one variable-frame-rate sample"; the sample set through the shipped runner | engine and sink only (`test_jobs_export_video.py:169`, `test_io_video_encode.py:263`) |
| G4 | V6 "HLG/PQ test files refused with a clear message" through the runner; "untagged video triggers the BT.709/limited warning" on a real file at export and in the shell | engine / composition / stub-probe shell (`test_gui_open.py:341` uses a stub; `test_app_wiring.py:377` asserts no words for the untagged case); runner covers DNG and sidecar only |
| G5 | V9 video "the output matches the input ... including color tags" through the runner, post-encode | one sample pre-encode (`test_wp42_video_path.py:464`) |
| G6 | V10 video "collision numbering ... no source or existing output ever overwritten" end to end | units only (`test_jobs_naming.py`, `test_jobs_safe_write.py`); photos end to end (`test_wp41_photo_path.py:425-453`) |
| G7 | V11 "simulated failures (crash, disk full) leave no partial outputs" on a real writer through the runner; a photo crash | doubles only for disk full (`test_jobs_export.py:523`); video crash only (`test_jobs_export_video.py:649`) |
| G8 | N10 / D92 for video: "same inputs and parameters give output identical within tolerance" | photos only (`test_wp41_photo_path.py:502,544`) |
| G9 | D91 video provenance through the runner, on and off | sink only (`test_io_video_encode.py:1312,1325`) |
| G10 | V18 on a real clip through the shell | fixture clip only (`test_app_v8_v18.py:405`); GX011627 was window evidence |

## Task ladder and test roster (the cell builds exactly these; depth read at every yield)

**T1 Read and map.** This brief; `tools/headless_export.py` (docstring, `main`, `run`, `exports`
parameter, the record schema); `tools/video_fidelity.py` (`fidelity_record`, the mandatory /
required / best-effort classes); `tests/test_wp41_photo_path.py`, `tests/test_wp42_video_path.py`,
`tests/test_jobs_export_video.py`, `tests/test_headless_export.py`, `tests/test_app_v8_v18.py`,
`tests/test_app_wiring.py` (G10 case), `tests/test_color_roundtrip.py:44-59`, `tests/conftest.py`
(`gx011627_trim`), `tests/fixtures/manifest.json`, `tools/fixtures/generate.py` (the recipe of the
`jpeg-orient-*` and `heic-ad24-*` stills: the upright reference and the pose applied). Round-0 note:
the exact helpers reused (file:line), the pose recipe found, the expected node count, any dispute.
`uv sync`.

**T2 `tests/acceptance_support.py` + RED for T3-T4** (photo module).

**T3 V5 multiple viewers (G1)**, `test_v51_photo_acceptance.py`, parallel-leg or `slow`:
- For each of the eight `jpeg-orient-{land,port}-o{1,3,6,8}` and the four `heic-ad24-*` stills: a
  `--neutral` 8-bit export through the runner (in-process `main`); then the OUTPUT PNG decoded by TWO
  independent readers, Pillow (`Image.open(...).convert("RGB")`, no transpose) and FFmpeg
  (`-i out.png -f rawvideo -pix_fmt rgb24`), asserted pixel-identical; the output's EXIF Orientation
  read with Pillow's `getexif()` is 1 or absent (so a viewer that honours EXIF and one that ignores it
  show the same pose).
- Pose: the decoded output equals the fixture's UPRIGHT reference from the generating recipe (T1),
  max abs ≤ 2/255 (AD-11 V9, the neutral path) for the JPEG eight; for the HEIC four the expected pose
  is the one `test_wp41_photo_path.py:325` already asserts under AD-24 (reuse its oracle, do not
  re-derive); CONTROL: for every non-identity pose (o3, o6, o8; irot ≠ 0) the un-transposed source
  differs from the output by max > 64/255 (the recipe's content is asymmetric; if it is not, the
  cell says so in round 0 and the control uses a planted asymmetric still written under `tmp_path`
  with Pillow and an EXIF Orientation tag).
- Q1 applies (viewers = readers).

**T4 V11 photo legs (G7, photo half)**, same module:
- Disk full on the real PNG writer: `--bit-depth 16` export of `png16-gradient-srgb` through the
  in-process runner with `builtins.open` (or the writer's lower write call, whichever the cell
  finds at `io/photo/writer.py`, cited) wrapped so the file object for a path under the output
  folder raises `OSError(errno.ENOSPC)` after the first 64 KiB; assert: exit status 1, the item is
  failed with a text that names the file (name only), NO final output, NO temporary left under the
  output folder, the source md5 unchanged.
- Photo crash: the runner as a SUBPROCESS over a 16-bit export with a planted writer hold (an env var
  or flag the cell CANNOT add to the product: instead use the slowest legitimate form, a 16-bit
  export of the largest fixture repeated as a batch of 40 copies under `tmp_path`, and kill the
  process at the first appearance of a temporary name under the output folder, polled at 10 ms);
  assert: a temporary MAY remain and nothing else new does; then `clearwater.app.startup.
  clean_leftovers` (or the shell's start-up path that calls it, `test_app_leftovers.py:370` shows the
  form) removes it; the source md5 unchanged. `slow`. If no temporary is ever observed in 20
  attempts, the node records "not observable at this size" and SKIPs with that reason (not a
  failure; stated in the report).

**T5 RED for T6-T8** (video module).

**T6 V4, V6, V9, V10, D91 through the runner**, `test_v51_video_acceptance.py`:
- **G3 V4 runner sweep:** every decodable fixture (`hevc8-bt709-full`, `hevc10`, `untagged`, `vfr`,
  `rotated`) exported through the runner (`--force-cpu`, `--encoder libx265`, `--cache-dir`,
  `--record`); `fidelity_record` of source vs output: every MANDATORY item SAME (frame count,
  timestamps, start offset, resolution, bit depth, chroma, audio, orientation, colour tags); the
  VFR sample's per-frame pts EXACT. `truncated`: a failed item with the D86 text, batch goes on.
- **G2 V4 best-effort record:** on the `gx011627_trim` session fixture (`footage`, `slow`) exported
  through the runner (GPU if present else CPU: both forms allowed, the record says which): the
  best-effort list (creation time, GPMF `gpmd`, timecode, camera atoms) present in source and output
  is RECORDED to the node's output (`record_property` and the report) and asserted ONLY as WP4.4 /
  WP3.10 documented: `gpmd` carried, the mandatory set SAME; the rest recorded (no assertion).
- **G4 V6 runner:** `hlg.mp4` and `pq.mp4` as items of one batch with `hevc8-bt709-full`: exit 1,
  the two refused with the probe's transfer text (the same text `test_wp42_video_path.py:426`
  asserts; cite), the third done; `untagged.mp4` exported: the record's warnings for that item
  carry "BT.709" and "limited" (the engine's D54 warning); if the record carries no such warning
  for a real untagged file, that is a STOP (G4 product half), not a softened assertion.
- **G5 V9 video through the runner, post-encode:** `--neutral` export of `hevc8-bt709-full`,
  `untagged`, `rotated` (8-bit) and `hevc10`; output and source decoded to RGB by the SAME FFmpeg
  command form (`test_color_roundtrip.py`'s pair, 8-bit RGB for the 8-bit samples; 16-bit RGB
  scaled to 1/255 units for `hevc10`); assert mean abs ≤ `PAIR_MEAN_SYNTHETIC` (2.5/255) per
  sample, record max; colour tags of the output equal the source's (`fidelity_record`); the
  rotation flag kept for `rotated`. Over the bound = STOP with the figures.
- **G6 V10 video end to end:** the same source exported twice into one `--out` folder gives
  `<stem>_corrected.mp4` then `<stem>_corrected_2.mp4`; a pre-planted file at the first output name
  (random bytes, md5 taken) is byte-identical afterwards and the export went to `_2`; a copy of
  `hevc8-bt709-full.mp4` renamed `<stem>.mov` beside the `.mp4` copy, both exported: ONE numbering
  sequence across the two (D25 / D84, the `test_jobs_naming.py:550-607` rule end to end); the
  source md5s unchanged after every node in the module (an autouse fixture in the module).
- **G9 D91 video provenance:** default export carries provenance parseable by the reader
  `test_io_video_encode.py:1312` uses, with `app_version` and the parameters equal to the request's;
  `--no-provenance` export carries none; the provenance's `"source"` carries the NAME, never a path.

**T7 N10 video (G8)**, same module:
- Two runner exports of `hevc8-bt709-full` with identical arguments (`--force-cpu`, `--encoder
  libx265`), the runner composed with `exports=` from the composition root wrapped the way
  `tools/export_oracle.py`'s `RecordingMethod` records per-frame render digests (imitate; do not
  import the oracle's CLI): assert the two runs' render digests are IDENTICAL for every pts
  (AD-11 N10, bit-identical pre-encode); RECORD whether the two output FILES are byte-identical
  (libx265 determinism is a characterisation, not a bound). One `gpu` form of the same node without
  `--force-cpu`: digests identical run to run; the CPU-vs-GPU figure (AD-11 2e-3 max, 2e-4 mean)
  computed from the decoded first frame and asserted.

**T8 shell legs**, `test_v51_shell_acceptance.py` (`gui`):
- **G4 V6 shell:** open the real `tests/fixtures/video/untagged.mp4` in the running shell (the
  form `test_app_wiring.py`'s G10 case uses, without the stub probe): the status / warning surface
  shows a text containing "BT.709" and "limited" (spec 5.4 / D54 "untagged video triggers the
  BT.709/limited warning"). If the shell shows NO such text for a real untagged file, the node is
  written to FAIL as the spec reads and the failure is a STOP to CHARC (the existing `words=""`
  assertion at `test_app_wiring.py:377` is NOT edited; the report states the two).
- **G10 V18 on the real trim:** `test_app_v8_v18.py:405`'s form on the `gx011627_trim` fixture
  (`gui`, `footage`, `slow`): a corrected frame is shown before the analysis completes (the hold
  hook the existing node uses) and the frame updates afterwards (pixel change recorded, > 0).

**T9 Traceability**, `tests/test_v51_traceability.py` (parallel-leg, pure): the matrix in the report
is ALSO a Python table in `acceptance_support.py` (V id -> node ids); the test asserts every listed
node id exists in the collected suite (`pytest --collect-only -q` output read from a file the
orchestrator produces at the gate, OR the test imports the modules and checks the function names:
the cell picks the form that needs no subprocess and says so). A stale node id fails the suite.

**T10 Report** `docs/reports/wp5.1-acceptance.md`: the matrix (V1-V18, N10, D91: node ids, markers,
leg, result, figure of record and source for V7 (WP4.3 window 5 and WP4.6's window: (a) 18, (b) 19,
(d) 56, (f) 50.6 ms PASS; (c)/(e) per DR-98's status at report time), V14 (`wp1.6-gate-report.md`),
V15 / V16 (WP5.2 pending), V2 (CP5 pending), V12 (v2)); the whole-set run figures (three legs);
the serial-leg delta; every STOP raised and its disposition; every SKIP and its reason; the
tolerance proposals, if any, for CHARC (AD-11 "tunable after WP5.1").

## Questions (CHARC's recommended answers)

- **Q1. "Multiple viewers".** Recommended: two independent DECODERS of the output (Pillow, FFmpeg)
  plus the Orientation-tag check stand in for viewers; the real-viewer leg (opening in Windows
  Photos, a browser) is the owner's at CP5 if wanted, not automated. The report says so.
- **Q2. Runner form.** Recommended: in-process `main(argv, exports=...)` where a wrapper or an
  injected failure is needed (T4 disk full, T7 digests); a subprocess where the shipped process
  boundary IS the subject (T4 crash, T6 sweeps may use either; say which per node).
- **Q3. A gap that is a product defect.** Recommended: write the node to the spec's reading, let it
  fail, STOP to CHARC with the node id, the assertion and the evidence; do not mark it xfail, do not
  soften it, do not fix the product. CHARC routes the fix (a remediation package) and rules whether
  WP5.1's gate waits or records the failure.
- **Q4. The serial-leg budget.** Recommended: 180 s total for the new marked nodes; the cell
  measures each node alone and in the leg, and reports; over budget = report and CHARC rules (a
  node may move to `fullclip`-like exclusion only by CHARC ruling).
- **Q5. Fixture reuse.** Recommended: no new committed fixture; planted files are written under
  `tmp_path` by the test (the asymmetric control still, the random-byte collision file, the
  renamed `.mov` copy).

## Dispatch fill (orchestrator generation 28, 2026-11-01; FINAL)

- **Status:** FINAL on CHARC commission post `05533fa67a11cee3` (file `20261101T081408Z-...-b488ac53.md`, 2026-11-01T08:14:08Z).
- **Base:** main `dd3cf1eb` plus this fill (docs only); the worktree is created from main at the fill commit. Worktree `C:\Users\rwsmy\clearwater\.worktrees\wp5.1`, branch `wp5.1`. Codex session: a FRESH one (its id is recorded in the ledger after turn 1).
- **Lane:** CODEX, `implementer-codex-sol-high`, driven by `scripts/codex_cell.py` (evidence `C:\Users\rwsmy\clearwater-review-evidence\wp5.1\cell\`; Reviewer A rounds under `...\wp5.1\rN\`). Paces at this dispatch (read 2026-11-01 08:15:23-24Z): Codex 0.196 (11 % used at 56.0 % of its window, resets 2026-11-04 10:07Z) vs Claude 0.992 (84 % at 84.7 %, resets 2026-11-02 09:59Z). Lane share at this commission: Codex 3 live packages (WP3.6P, WP5.3, WP5.1); Claude 1 (WP4.6, past convergence, at its window/report). Every Codex package's Reviewer A and B are Claude passes, so the Claude lane's burn continues through them until the 2026-11-02 reset.
- **GATE_CHECKS** (`docs/review-gate-clearwater.md` Part 2, at the orchestrator's seat on the final candidate rebased onto main): `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy`; the two legs from Git Bash with `PYTEST_ADDOPTS` unset, parallel `uv run pytest -q -rs -n 4 -m "not gpu and not footage and not gui and not slow and not fullclip" --basetemp=work/<run>-parallel` then serial `uv run pytest -q -rs -m "(gpu or footage or gui or slow) and not fullclip" --basetemp=work/<run>-serial`, then the `fullclip` leg ONCE (`uv run pytest -q -rs -m fullclip --basetemp=work/<run>-fullclip`, no `-n`, about 26 min; this is the phase-end whole-set run); collection identity parallel + serial + fullclip = all; the LF blob check (0 CR) on every file in `git diff --name-only <base>..<candidate>`; no harness gate unless the diff touches `scripts/`, `.claude/`, the kernel docs or `tests/harness/`. **DR-99:** `tests/test_io_video_encode_bench.py::test_run_once_records_the_row_and_deletes_the_output` failing on `telemetry_origin` the same way AND alone on main is recorded under DR-99, not a STOP; any other failure is a STOP.
- **Yields (binding):** turn 1 = T1 (round 0 in `docs/proofs/wp5.1-ledger.md`: the helpers reused with file:line, the pose recipe found, the expected node count per module and marker, any dispute with evidence); then after T2, T4, T6 and T8; after each Reviewer A round is ADJUDICATED (no remediation in that turn); before T10.
- **Runs the sandbox cannot make (binding):** the cell never reads the footage folder. The `footage` nodes (the `gx011627_trim` session fixture copies from it), the `gpu` form of T7 and the `gui` shell nodes are run by the orchestrator at its seat from the cell's `RUN REQUEST:` line (exact command runnable from the worktree root, expected wall time); the cell writes them and reads the returned output. The cell's light runs in its sandbox: `PYTHONPATH=scripts uv run pytest -q <its new modules> --basetemp=work/wp5.1/tmp -p sandbox_mkdir_shim -p no:cacheprovider -m "not gpu and not footage and not gui and not fullclip"`, `uv run ruff check tests/acceptance_support.py tests/test_v51_*.py`, `uv run mypy`; the orchestrator runs `ruff format --check` at its seat.
- **Scheduling:** run requests and the gate's three legs run with no EXCLUSIVE window open and no WP5.3 build piece running; the orchestrator schedules.
- **Concurrent work:** WP3.6P (Codex, `.worktrees/wp3.6p`), WP5.3 (Codex, `.worktrees/wp5.3`) and WP4.6 (Claude, `.worktrees/wp4.6`) are live. Never read or write another worktree; WP3.6P's and WP4.6's accepts land on main during this package and touch no file it owns.
- **Depth:** the orchestrator reads the turn footer's `depth_input_tokens` and gives it to the cell at the next turn; the ledger keeps a depth table. Evaluate at about 200K; STOP at a step boundary near 250K.
