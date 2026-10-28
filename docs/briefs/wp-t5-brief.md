# WP-T5 -- Suite cost (DR-65) (dispatch brief, FINAL)

**Status:** FINAL 2026-10-28 (CHARC `2c4476d9869df056`, rulings below, which take precedence over the text above them); DRAFT 2026-10-28, written by a drafting helper for the orchestrator (generation 16)
under CHARC commission `159c14fb79ad1aae` (section 1 lane, section 2 the WP-T5 bullet). For
CHARC's pass; base = the main commit named in the dispatch prompt (`6536f60` or later). Spec
**v0.5.5**; no spec clause changes. Tests and a report only: no product code, nothing under
`src/` or `tools/`.

- Cell: `implementer-sonnet-high` or `implementer-codex-sol-high` by the pace tiebreak at dispatch
  (orchestrator fills: both readings of `scripts/usage_codex.py` / `scripts/usage_claude.py` and
  the paces in the dispatch row); the reviewer is the other model. The brief works for either
  lane; the Codex cell takes well-specified packages only, and this is one (it designs no
  interface).
- Worktree `.worktrees/wp-t5`, branch `wp-t5`. Runs CONCURRENTLY with WP4.1 (commission 1:
  "disjoint files"); its windows are exclusive like any other.
- Lane differences: the Claude lane commits itself and runs its own granted windows; the Codex
  lane ends every turn with a FILES CHANGED block, the orchestrator commits and runs every heavy
  command the cell yields (`.claude/agents/implementer-codex-sol-high.md`).

**Why.** DR-65 (`docs/debt-register.md`, OPEN): "four export test bodies of WP3.14 and WP3.10
... take about 2,276 s = 68 % of the serial leg (3,331 s), which is the two-leg gate's floor;
they are serial by necessity (one GPU, real footage), so workers cannot shorten them. The lever is
their SIZE". The figures are WP-T4's (D3 on `ba6e923`, `docs/reports/wp-t4-parallel-tests.md`
"ten longest cases"): `test_v4_synthetic_5k3_8_7_clip` 870.74 s, `test_gx011627_through_the_engine_...`
725.15 s, `test_gx011627_nvenc_levels_give_distinct_sizes` 472.50 s,
`test_gx011627_through_the_sink_...` 207.83 s. They PREDATE WP3.21: its gate's serial leg was
2,685.30 s (`docs/proofs/wp3.21-accept.md`, two-leg row, 1,113 passed / 1 skipped), so the four
bodies' present cost is unknown until rung 1 measures it.

| Field | Content |
|---|---|
| Goal | The two-leg gate's SERIAL leg (the floor, AD-28) runs measurably shorter with every assertion of the four DR-65 tests kept: the synthetic 5.3K V4 test exports the minimum frame count that still proves V4 on a 5.3K 8:7 frame set, and the GX011627 sink-level encode is made once and shared where the assertions allow. |
| Spec / decision clauses | V4 (spec "V4 Video I/O fidelity": "mandatory: output matches source frame count, per-frame timestamps, start offset, resolution, bit depth ..., chroma format, audio and display orientation; color tags match the source"); D105 ("per-frame timing, start offset, audio sync and display orientation are mandatory"); D106 ("5.3K is supported but best-effort on speed"); spec 5.2 Video ("including 5.3K and 8:7 modes"); AD-28 (two legs; "Timing, memory and exclusive-window figures are read only from serial runs"); plan 4.3 (exclusive windows), 4.5 (done). V15 / N4 are NOT touched: the 5.3K memory figure is the bench's 150-frame clip (`tools/export_bench.py` `SYNTHETIC = "synthetic-5k3"`; WP3.14 ledger (b)), not this test. |
| Depends on | Main at or after `6536f60` (Phase 3 complete). Nothing in flight; WP4.1 concurrent on disjoint files. |
| Debt and decided items | See the table below. |
| Files owned | EDIT `tests/test_jobs_export_video.py` (origin WP3.14, `8a3f34a`): ONLY `test_v4_synthetic_5k3_8_7_clip` (`:214`), its `clips.make(..., duration="0.3")` argument (Q3) and, if Q4 adopts it, one precondition line. EDIT `tests/test_io_video_encode.py` (origin WP3.10): ONE new session-scoped fixture beside `runs` (`:105`) and `clips` (`:156`), and the bodies of `test_gx011627_through_the_sink_...` (`:1475`) and `test_gx011627_nvenc_levels_give_distinct_sizes` (`:1492`) to consume it (Q2). NEW `docs/reports/wp-t5-suite-cost.md`, `docs/proofs/wp-t5-ledger.md`. The four DR-65 tests live in these TWO files; no shared fixture module is needed for the recommended share (Q1). |
| NOT owned | `tests/conftest.py` (unless round 0 shows the need: a Question, Q1); `tests/fixture_plugin.py`; `tests/test_jobs_export_support.py` (`product_engine`); every other test in the two owned files, including `test_gx011627_through_the_engine_...` (`test_jobs_export_video.py:710`, unchanged unless Q2 rules otherwise), `test_a_short_5k_8_by_7_clip`, `_assert_v4`, `Clips`, `Runs`; `tools/video_fidelity.py`, `tools/container_spike/`; all of `src/` (IF-1..IF-10 FROZEN, AD-20); `pyproject.toml`, `uv.lock`; `docs/review-gate-clearwater.md`, `CLAUDE.md`, the register (CHARC and the orchestrator write those at accept); any file named in WP4.1's dispatch row (a clash is RAISED, never edited). |
| Interfaces consumed | none (the tests call `vf.encode_file`, `vf.fidelity_record`, `verify_module.read_hevc_level`, `product_engine` as they do today). |
| Done | Plan 4.5. ruff check, ruff format --check, mypy (strict; tests are outside its `files`, run it anyway), BOTH legs green on the frozen head; the serial leg's AFTER wall measurably below its BEFORE wall (Q5) with every assertion kept, OR a recorded reason why not in the report and the accept; report and ledger written; Reviewer A converged. No harness gate (nothing in `scripts/`, `.claude/`, kernel docs or `tests/harness/` is owned). |

**Debt and decided items (register rule, commission section 2).** Greps: `wp-t5`, both owned
test paths, `conftest`, `fixture_plugin`, `video_fidelity`, `GX011627`, `5k3`, `serial`, `slow`.

| Row | Why it is cited | Disposition |
|---|---|---|
| DR-65 | This package's row. | CLOSES when the AFTER serial leg is on main with the four tests' assertions kept; the closure text names the measured saving and the share the assertions did NOT allow (Q2: the engine test's export stays its own). If the saving is not measurable (Q5), the row is updated with the recorded reason instead. |
| DR-18 | CLOSED by WP3.10; its (1) closure is "`tied` True on GX011627", read from the `run` the sink test passes to `fidelity_record`. | CONSUMER NOTE: the shared fixture keeps the `vf.encode_file` call and its `EncodeRun` (the pmon sampler tied to that encode window) together; the sink test still passes that `run` to `fidelity_record`. |
| DR-28 | CLOSED by WP3.14's `test_dr28_*` in the owned `test_jobs_export_video.py`. | NOT REACHED: those tests are not edited. |
| DR-57 | OPEN (d); (a) says "the V4 instrument hashes the audio payloads", which `_assert_v4` reads. | NOT REACHED: the instrument is not edited; a 3-frame clip still carries an AAC track whose packets it hashes (rung 3 CHECK). |
| DR-58 | (c) CLOSED by WP-T4 (the `slow` E1 mark, serial leg). | NOT REACHED: `tests/test_io_video_encode_bench.py` is not owned. |
| DR-22, DR-66 | Name `tests/conftest.py` (guard limits; worker-side refusal). | NOT REACHED: `conftest.py` is not owned (Q1). If Q1 grants it, both become CONSUMER NOTES (the guard code is not touched). |
| DR-36 (c)-(f), DR-56 | Name `src/clearwater/io/video/` and the GX011627 best-effort rows the sink test reads. | NOT REACHED: no product code; no V4 item or class changes. |

## Task ladder

Run the build cycle (produce, validate, converge; `docs/dispatch-recipe.md` section 2) per rung.
The two legs, verbatim from `CLAUDE.md` (Git Bash, `PYTEST_ADDOPTS` unset,
`QT_QPA_PLATFORM=offscreen`, a fresh `--basetemp` under `work/` per run):

    PARALLEL  uv run pytest -q -rs -n 4 -m "not gpu and not footage and not gui and not slow" --basetemp=work/wp-t5/<run>-parallel
    SERIAL    uv run pytest -q -rs -m "gpu or footage or gui or slow" --basetemp=work/wp-t5/<run>-serial --durations=0 --junitxml=work/wp-t5/<run>-serial.xml

Route every run to a file under `work/wp-t5/` (`> file 2>&1; echo EXIT=$? >> file`) and read
the summary and `EXIT=` lines. Copy the main tree's `clearwater.local.toml` into the worktree
first (orchestrator; without it the footage tests skip and the gate is void, fill GATE_CHECKS).

**Rung 0 -- facts (light, no window).**
1. `uv sync`; record the base SHA and a clean `git status`.
2. Collection: `--collect-only -q` node-ID lists for all and for the SERIAL expression into
   `work/wp-t5/base-*.txt` (they are the BEFORE side of the rung 4 identity check).
3. The 5.3K test's frame count today, by a LIGHT count at the test's rate and duration but a
   small size (the drafting helper ran `testsrc2=size=160x96:rate=30000/1001:duration=D` through
   `-f null`: D 0.3 -> 9 frames, 0.1 -> 3, 0.06 -> 2; confirm). Read and cite (file:line) every
   frame-count branch the export and the instrument can take below 10 frames: c3's derived
   analysis lead (61 frames, DR-74), `STREAM_STEP` 16 (`analysis/engine.py`, DR-70), the
   smoothing window, the sink's close-time checks, `tools/video_fidelity.py`'s per-frame and
   AAC items. CHECK: no branch separates 3 (or Q3's count) from 9; any that does is a STOP.
4. Read `vf.encode_file` (`tools/video_fidelity.py:350`) and confirm the sink test's call and
   the levels test's `standard` call take identical arguments apart from the output path.

**Rung 1 -- BEFORE (window W1, exclusive).** The SERIAL leg on the base, as above with
`<run>=before`. Record the wall, the counts and skips, and from the junit file the four DR-65
bodies' current times (setup / call / teardown). Then the projection: for the 5.3K test, its
time per frame at 9 frames against Q3's count; for the levels test, one encode's share.

**Rung 2 -- round-0 design table, then YIELD.** One table, sent to the dispatcher (copy to CHARC
only if it touches a tripwire: a `conftest.py` need, a new module, a cross-file share). Rows:
the 5.3K frame count and its ground (rung 0.3); the fixture's name, scope, what it yields and
its teardown (Q2); where each skip condition sits; the assertion map below, test by test, showing
each line kept; the projected saving from rung 1's figures; anything the assertions forbid
sharing, with the reason. YIELD. Build nothing before the reply.

**Assertion map ("assertions unchanged", per test).**
- `test_v4_synthetic_5k3_8_7_clip`: `size="5312x4648"`, `rate="30000/1001"` and the CPU-forced
  libx265 export (`_settings(out)`) stay; `assert result.ok, result.failure`; one output
  (`(output,) = result.outputs`); `_assert_v4(vf.fidelity_record(source, output, bit_depth=8))`
  (`mandatory_and_required_all_same` and the roster item SAME). Only `duration=` changes.
- `test_gx011627_through_the_sink_...`: `_assert_v4(record)` with `record =
  vf.fidelity_record(source, out, bit_depth=8, run=run)` computed IN the test body from the
  fixture's `(out, run)`; `assert run.report.frames_written == 681`. Its `os.remove(out)`
  moves to the fixture's teardown.
- `test_gx011627_nvenc_levels_give_distinct_sizes`: per quality, `level.name == expected[quality]`
  (`5.2 / 5.1 / 5.0 Main`); `sizes["high"] > 1.25 * sizes["standard"] > 1.25 * 1.25 *
  sizes["draft"]`. `high` and `draft` are encoded in the body as now (and removed as now); the
  `standard` size and level are read from the fixture's output, which the test must NOT delete.
- `test_gx011627_through_the_engine_...`: unchanged (Q2).
- Markers, test names and node IDs of all four: unchanged.

**Rung 3 -- build (light edits; one short window W2).**
1. The 5.3K test: `duration=` per Q3 (and Q4's precondition line if adopted). One commit.
2. The fixture in `tests/test_io_video_encode.py` (Q2): `scope="session"`, defined in the module;
   it runs `_nvenc_ready()` and `_footage_clip("GX011627", ...)` BEFORE encoding (a skip raised in
   the fixture skips both tests exactly as today; a skip left in a test body would run after the
   fixture tried to encode), writes under `tmp_path_factory`, yields `(out, run)`, and removes the
   output at teardown. Google docstring. The two test bodies consume it. One commit.
3. W2: run ONLY the three changed tests by node ID (the 5.3K test, the sink test, the levels
   test) in one serial process with `--durations=0`, then each GX011627 test alone (`-k`), so the
   fixture is proved for either test selected by itself. CHECK: green; the 5.3K record still has
   an AAC audio item compared SAME and the "video frame count" output equals Q3's count; one
   NVENC `standard` encode logged in the combined run, not two.
4. Controls (light where possible, else inside W2): a planted break in each changed test still
   fails it, then is reverted, recorded in the ledger: the 5.3K test with `bit_depth=10` passed to
   `fidelity_record` (the bit-depth item goes DIFFERENT); the levels test with the fixture
   yielding the `draft` output as `standard` (the level or size assertion fails).

**Rung 4 -- AFTER (window W3, exclusive) and the identity check.** On the frozen head: PARALLEL
then SERIAL with `<run>=after`. CHECK:
- both legs green; the SERIAL counts and skip lines equal rung 1's (passed + skipped the same;
  any moved skip explained, fill GATE_CHECKS);
- collection lists for all and SERIAL identical to rung 0.2's (no test added, removed or renamed);
- `git diff <base>..HEAD -- tests/` removes no `assert` line that is not re-added verbatim in the
  same test (list them in the ledger);
- the saving = BEFORE wall - AFTER wall, and the four bodies before and after from the junit
  files; Q5's threshold applied.

**Rung 5 -- report, ledger, gates.** `docs/reports/wp-t5-suite-cost.md`: claims; the frame-count
ground (rung 0.3 with file:line); the assertion map as built; the share made and the share NOT
made with its reason (Q2); the figures table (W1, W3: wall, counts, the four bodies; start times;
"same quiet host, exclusive window"); the controls; limits; a "for CHARC" line with the DR-65
closure text and the updated CLAUDE.md serial-leg figure (the cell edits neither file).
`docs/proofs/wp-t5-ledger.md`: one row per heavy run (start, end, command, counts, EXIT, free
memory before), the review rounds, the depth readings. Final head: ruff check, ruff format
--check, mypy; if any file changed after W3, both legs again (a window).

## Declared operating envelope

Windows 11, Python 3.12, pytest 8.4.2 with pytest-xdist 3.x (`uv.lock`), Git Bash, headless Qt,
the owner's laptop with its one NVIDIA GPU and NVENC, the WP0.1 FFmpeg build, GX011627 present in
the configured footage folder (read only). The SERIAL leg runs in one process, as AD-28 has it.
Out of envelope: the SERIAL expression under `-n` (a session fixture is per worker, so the
encode would repeat; not a defect), `pytest-randomly` or any reordering plugin, several GPUs, a
footage folder without GX011627 (the tests skip as today), another FFmpeg build.

## Review loop (Reviewer A) -- per `docs/review-gate-clearwater.md` Part 1

- **Tier FAST**, under the fill's rule "Tier by the blast radius of a MISSED finding: `strong`
  ... for every product-code package; `fast` for docs, briefs and tools under `tools/` that
  produce no shipped output. Never tier the rigor", read with the commission's bound "FAST tier
  only if the change is test-only; otherwise STRONG". Any change outside the two test files and
  the two docs makes it STRONG (and is a STOP first). Round policy is the fill's (zero new
  blocking terminates; five-round gate); recommended cap ONE round plus the single cleanup, as
  WP-T4 (Q6).
- **Claude lane** (reviewer = Codex, WSL, codex-cli 0.162.1): `-m gpt-6-luna -c
  model_reasoning_effort=medium -s read-only --skip-git-repo-check` (the `fast` tier,
  `docs/codex-reviewer.md`); one probe through the exact invocation first; diff Windows-side with
  `git -C <worktree> diff -U8 <base>..HEAD -- . ':!docs/proofs'`. Assertions (`grep -a`): banner
  model and effort; every `^ERROR` / `ERROR codex_core` line classified by provenance; the
  `^tokens used` footer; an anchored VERDICT line; at least one `^ succeeded in`;
  `grep -a -n 'docs/proofs\|wp-t5-ledger'` with every hit classified as echo or access. The prompt
  carries the EXECUTED/REASONED paragraph verbatim from `docs/codex-reviewer.md` and: "Do NOT read
  `docs/proofs/` or anything under `clearwater-review-evidence`; those are withheld. Never read or
  list `/mnt/c/Users/rwsmy/clearwater-footage`." The reviewer runs no footage or GPU test.
- **Codex lane** (reviewer = Claude, run by the driver between turns): `scripts/codex_cell.py
  review`, `claude -p --model opus --effort high` per the fill's Part 1 lane paragraph and the
  WP-T4 Q6 ruling (`3c3c35d7e40b525e`: "there is no 'Sonnet medium' variant and nobody improvises
  the invocation"); assertions as that paragraph (`modelUsage` key, `is_error` false, a `VERDICT:`
  line, empty `git status --porcelain` afterwards, every finding EXECUTED or REASONED).
- **Evidence:** `C:\Users\rwsmy\clearwater-review-evidence\wp-t5\rN\` with md5s; ledger
  `docs/proofs/wp-t5-ledger.md`.
- **WHAT TO EXAMINE:**
  - whether every assertion of the four tests is still present and still reads the same object
    (the assertion map), and whether any was weakened by moving it into or out of the fixture;
  - whether Q3's frame count still exercises every V4 MANDATORY item on a 5.3K 8:7 frame set
    (frame count, per-frame timestamps, start offset, resolution, depth, chroma, audio, orientation,
    colour tags), and whether any code path branches between that count and 9;
  - whether the fixture skips exactly as the tests did (NVENC absent, clip absent, footage folder
    errors) and never encodes before deciding to skip;
  - whether the shared `standard` output is the same call the levels test made, and whether its
    `EncodeRun` still ties the NVENC proof to that encode (DR-18 (1));
  - whether the footage-derived outputs are still removed and nothing is written outside the
    temp root;
  - whether the report's figures are the commands as run, from serial runs in exclusive windows.
- Reviewer B is the orchestrator's seat pass on the merge candidate (fill Part 2), the other model
  from the implementer.

## Notes for the cell

- **Windows (X5, AD-28).** W1 (BEFORE serial leg, about 45 min), W2 (the three changed tests,
  short), W3 (AFTER: both legs, about 55 min). Ask for each with `WINDOW REQUEST: <command,
  expected duration, evidence path>`; one heavy job at a time; at least 5 GiB available first
  (`uv run python -c "import psutil; assert psutil.virtual_memory().available >= 5*2**30"`); send
  `WINDOW RELEASED: <summary>` after each. Claude lane: run in the background with output to a
  file under `work/wp-t5/`, wait with foreground poll calls on the done marker, read the summary
  AND the `EXIT=` line (a reaped run is not a result). Codex lane: yield the exact command line;
  the orchestrator runs it and hands back the output path. Figures come only from serial runs in
  these windows. Light inner loops (ruff, the collection lists, a 160x96 lavfi count) need none.
- **Yields.** Report `scripts/cell_depth.py` at every yield (~250K evaluation point, ~400K STOP).
  YIELD at rung 2 (round-0 table). After each review round, end the turn once the verdict is
  adjudicated, before remediating.
- **Return report** = your FINAL message, under about 70 lines, to your dispatcher by your
  messaging tool (Codex lane: then the FILES CHANGED block): per-commit changes; the frame count
  and its ground; the fixture; the assertion map; the controls; W1 / W3 figures and the four
  bodies; the saving against Q5's threshold; the gate lines (both legs, counts, skips); the
  register dispositions; review rounds and assertions; open items.
- **STOP for:** any change in `src/`, `tools/` or `src/clearwater/interfaces/` (AD-20); a need to
  edit `tests/conftest.py`, `tests/fixture_plugin.py` or `tests/test_jobs_export_support.py`; a
  test removed, renamed, re-marked or an assertion changed; a frame-count branch between Q3's count
  and 9; a clash with a file in WP4.1's dispatch row; any write outside the worktree, the temp root
  and `work/`.
- **Working rules:** `uv sync`. Commit by pathspec with `git -c core.autocrlf=false commit -m
  "test(wp-t5): ..." -- <paths>` (`docs(wp-t5)` for the report and ledger), one commit per logical
  change, `Co-Authored-By:` naming your model; every committed blob LF. Never `git stash`; never a
  bare `cd`; never post to a mailbox. The footage folder `C:\Users\rwsmy\clearwater-footage\` is
  read-only and only the SERIAL leg's `footage` tests open it; no footage-derived output is
  committed. No `gpmd`, IMU or GPS data is read or committed, and no location tag appears in a
  committed record (the instrument already withholds them).

## Questions for CHARC (recommended answer first)

1. **`tests/conftest.py` or a shared fixture module.** Recommended: NEITHER. The share the
   assertions allow (Q2) is between two tests of ONE file, `tests/test_io_video_encode.py`, so a
   `scope="session"` fixture defined in that module serves both, as its own `runs` and `clips`
   fixtures already do (`:105`, `:156`). `conftest.py` stays not owned. Alternative, only if Q2
   rules a cross-file share: a fixture registered at conftest level (in `tests/conftest.py`, or a
   new `tests/gx011627_plugin.py` added to its `pytest_plugins` statement); both edit
   `conftest.py`, which holds the footage guard (DR-22, DR-66), so it would come back as a
   round-0 Question with the exact lines.
2. **Which tests share the export.** Recommended: the SINK test and the levels test's `standard`
   leg share ONE session-scoped NVENC `standard` encode of GX011627 (the calls are identical apart
   from the path: `vf.encode_file(source, out, encoder="hevc_nvenc", quality="standard",
   bit_depth=8)`); the fixture yields `(out, run)` and removes the output at teardown; the sink
   test computes its own record. The ENGINE test is NOT shared, and that is the recorded reason
   under DR-65: its export is a c3-corrected `ExportEngine` job with `provenance=True`, a different
   file from the uncorrected sink write, and its `JobResult` carries no `EncodeRun`, so neither
   test's assertions could read the other's output without dropping one (the engine-path V4, or the
   sink test's NVENC proof and `frames_written == 681`). Alternatives: reuse the module's existing
   `Runs.get(source, "hevc_nvenc", 8)` (it keeps the footage-derived output for the whole session
   and computes a record the levels test does not need); or read DR-65 literally as engine + sink,
   which relaxes an assertion and is outside the bound.
3. **The 5.3K frame count.** Recommended: **3** (`duration="0.1"` at `30000/1001`; today 0.3 s =
   9 frames). Ground: (a) three frames are the fewest that hold a first frame (start offset), an
   interior frame (a pts step on both sides) and a last frame (the end duration), so every V4
   MANDATORY item is exercised at 5312x4648; (b) every frame-count branch near this test is already
   above 9 (c3's 61-frame lead, `STREAM_STEP` 16), so 3 and 9 take the same paths (rung 0.3
   proves it); (c) WP3.10's accepted sink-level 5.3K V4 test uses three frames
   (`test_a_short_5k_8_by_7_clip`, `duration="0.1"` at 30 fps, `tests/test_io_video_encode.py:391`).
   Projected 871 s -> about 290 s if the cost is per frame (rung 1 measures it). Alternatives: 2
   (`"0.06"`; the strict minimum for a pts step, about 97 s less, no interior frame); 1 rejected
   (per-frame timestamps collapse to the start offset).
4. **A precondition line in the 5.3K test.** Recommended: add `assert probe(source).video.nb_frames
   == 3` after `clips.make` (`probe` is already imported; `nb_frames` is IF field
   `ProbeResult.video.nb_frames`): it pins the ground of Q3 against an FFmpeg change that would
   make the clip shorter. It adds an assertion and changes none. Alternative: no line; the count is
   recorded in the ledger only.
5. **"Measurably shorter" and the windows.** Recommended: one BEFORE (W1) and one AFTER (W3)
   serial leg; measurable = a saving above 110 s (three times WP-T4's r1-r2 serial spread, 3,335.36
   vs 3,372.59 s, `docs/proofs/wp-t4-accept.md`); below it, one more BEFORE/AFTER pair in granted
   windows, then the recorded-reason branch of Done. Three windows in all (W2 short), against the
   commission's "two short windows" estimate: W1 is needed because the DR-65 figures predate WP3.21.
   Alternative: take WP3.21's gate serial leg (2,685.30 s, `227ed32`, code-identical by the
   docs-only `7e228fb..6536f60` diff) as BEFORE and skip W1; it saves about 45 min but gives no
   per-test figures on this base.
6. **Reviewer tier and cap.** Recommended: FAST (test-only), ONE round plus the single cleanup.
   Claude lane: Codex `gpt-6-luna` / medium. Codex lane: the pinned Claude pass (`opus` / high),
   per the WP-T4 Q6 ruling, not the fill's "fast = Sonnet medium" line. Any non-test change: STRONG.
7. **The commission's "~30 min shorter" (section 3), for information.** Recommended: record the
   figure as projected about 12 min on WP-T4-era figures (about 580 s from Q3, about 150 s from
   Q2's one saved encode), with W1 replacing the projection. The largest remaining body, the
   engine test (725 s), stays by the bounds. WP4.2's commissioned "V4 SAME leg on GX011627 through
   the product composition" would add a body of the same size; recommended that WP4.2's brief
   supersede or extend `test_gx011627_through_the_engine_...` rather than add one beside it (a
   CHARC note for that brief; WP-T5 does not touch it).

## Return report

Your FINAL message, under about 70 lines, as listed in "Notes for the cell". An undelivered report
is a failed handoff.

## Rulings (CHARC `2c4476d9869df056`, 2026-10-28, verbatim; they GOVERN the Questions section above)

PRIMARY: orchestrator. Thread `159c14fb79ad1aae`, reply to `8c3c624c224c263e` (+ `56e00cce74e65b5c`, `528b3db814b6d2c5`). **RULING PACKET: all four drafts APPROVED with the rulings below; every helper recommendation ADOPTED except where a line says otherwise. Write the rulings verbatim into each brief, commit on `briefs-p4`, ff main; dispatch WP4.1 (opus-high) and WP-T5 (by pace) now; WP4.2 and WP4.3 stay DRAFT until their predecessor's accept plus one revision pass, then FINAL on my word.** Tripwire passes (new package `clearwater.app`, the WP4.3 modules, `python -m clearwater`, the leftover journal) are all GRANTED here.

**Flags.** (1) WP4.2 Q3 narrowing ACCEPTED (N4 ground: the stub analysis over a real source stores ~23 GB for GX011625; the GUI's video legs swap in WP4.3 with the adapter). (2) withdrawn; see 43-Q13. (3) tripwires GRANTED as listed; the `gui/engines.py -> clearwater.app.composition` edge is the ONE gui-to-app edge, pinned by `tests/test_app_deps.py`. (4) the two S1 tests go in WP4.3 (43-Q11); WP-T5's three bodies as T5-Q2/Q3/Q4. (5) noted; my "~30 min" is CORRECTED to the helper's ~12 min projection, W1 replaces it.

**Addendum.** (1) WP4.3's V8 legs cite AD-11 AS AMENDED 2026-10-21 (k = 1 EXACT; k > 1 mean <= 1/255, p99 <= 2/255 at k = 2 and <= 4/255 at k = 4, max recorded never asserted), the same text as WP4.1 line 301. (2) 41-Q3 + 43-Q11 ruled together as recommended: `default_engines()` stays, takes its photo legs and methods from the root in WP4.1, its selector and video legs in WP4.3; `shell.run` and `gui/__init__.py` unedited. (3) WP4.2's DR-35 clause STRUCK.

**WP-T5 (Sonnet-class; lane by pace at dispatch; the other model reviews).** Q1 NEITHER (module-local session fixture in `tests/test_io_video_encode.py`; `conftest.py` not owned). Q2 as recommended (sink test + levels `standard` leg share ONE NVENC standard encode, fixture yields `(out, run)`, teardown removes the output; the engine test NOT shared = DR-65's recorded reason). Q3 THREE frames (`duration="0.1"`), ground (a)-(c); rung 0.3 proves 3 and 9 take the same paths. Q4 the precondition assertion ADDED. Q5 as recommended: W1 BEFORE, W3 AFTER, measurable = > 110 s; one more pair below it, then the recorded-reason branch; three windows (W1 is owed because DR-65's figures predate WP3.21; per-test figures on this base are the point). Q6 FAST, one round + cleanup, lane-dependent reviewer per the WP-T4 Q6 ruling; any non-test change = STRONG. Q7 record ~12 min projected, W1 replaces it; my commission figure corrected.

**Cost restated:** unchanged from the commission except WP-T5's saving (~12 min per gate, not ~30) and one extra short window for it.
