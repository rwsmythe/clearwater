# WP-T5 suite-cost ledger

## Dispatch and depth

Codex lane, turns 1-5, rungs 0-4 and draft rung 5, 2026-10-28. Base:
`3aa3c51da6cc5870322fb4688fbc61227f4efdd2`, branch `wp-t5`.
The initial `git status --porcelain` was empty. Evidence is under
`work/wp-t5/`; no footage was opened by this cell. The supplied local
configuration was not changed. Turns 1-2 changed this ledger only; the dispatcher
committed them at `a9abb8d` and `b17b2d4`. Turn 3 changed the two approved test
files and this ledger, committed by the dispatcher at `045d622`; product code
remains unchanged. The two rung-3 test edits were bundled as requested by the
turn-3 dispatch. Turn 4 updated this ledger and ignored request/evidence artifacts,
committed at `259a219`; both test files were restored byte-for-byte to HEAD after
CPU-only control cycles. Turn 5 adds the DRAFT report and updates this ledger;
tests remain unchanged since W3's head `259a219`.

Depth figures are dispatcher readings, never cell estimates.

| Turn / gate | Tokens (as supplied) | Input depth | Window | Disposition |
|---|---|---|---|---|
| 1 / rung 0 | 182,117 | 138,874 | 475,000 | Dispatcher reading supplied at turn 2; collection artifact resolved at seat |
| 2 / rungs 1-2 | 351,779 | 164,909 | 258,400 | Dispatcher reading supplied at turn 3; round-0 table approved with comparability amendment |
| 3 / rung 3 | 455,659 | 209,195 | 475,000 | Dispatcher reading supplied at turn 4; W2 ran, runner exited 2 after the intended depth failure |
| 4 / controls and rung-4 preparation | 547,891 cumulative | 82,213 | 258,400 | Dispatcher reading supplied at turn 5; W2b and W3 completed at seat |
| 5 / draft report and ledger | Not yet supplied | Not yet supplied | 258,400 last reported | Yield for Reviewer A; standard gate still pending |

The reported window changed from 475,000 (turn 1) to 258,400 (turn 2), then
475,000 (turn 3), then 258,400 (turn 4). All figures are retained as given; the dispatcher said it
monitors depth against the smaller window. No cell estimate replaces a reading.

## Rung 0 commands and results

| Check | Evidence | Result |
|---|---|---|
| Base SHA, branch, initial status | `base-head.txt`, `base-branch.txt`, `base-status.txt` | Expected base and branch; clean |
| `uv sync` | `uv-sync.log` | `EXIT=0`; no dependency-file edits |
| Collect all node IDs | Dispatcher: `base-all-seat.log`, `base-all.txt` | 5,289 collected in 3.78 s, `EXIT=0`; 5,289 unique IDs |
| Collect SERIAL node IDs | Dispatcher: `base-serial-seat.log`, `base-serial.txt` | 1,114 / 5,289 collected, 4,175 deselected in 2.03 s, `EXIT=0`; 1,114 unique IDs |
| Small lavfi frame counts | `frame-count-0.3.log`, `frame-count-0.1.log`, `frame-count-0.06.log` | 9, 3, 2 frames respectively; each `EXIT=0` |
| Default smoothing / streaming checks and encode-call AST check | `branch-check.log` | `EXIT=0`; identical default smoothing line sets; identical encode arguments except output |

Collection commands use `PYTHONPATH=scripts`, `QT_QPA_PLATFORM=offscreen`, empty
`PYTEST_ADDOPTS`, and the sandbox shim:

```text
uv run pytest --collect-only -q --basetemp=work/wp-t5/base-collect-all -p sandbox_mkdir_shim -p no:cacheprovider
uv run pytest --collect-only -q --basetemp=work/wp-t5/base-collect-serial -p sandbox_mkdir_shim -p no:cacheprovider -m "gpu or footage or gui or slow"
```

The dispatcher obtained both baseline lists at its seat in Git Bash with
`PYTEST_ADDOPTS` unset and Qt offscreen. The `.log` summaries and `EXIT=0` were
read in turn 2; `.txt` files contain only node IDs. The cell checked uniqueness,
that SERIAL is a subset of all, and that all four DR-65 nodes are in SERIAL.
Each collection attempt uses its own temp root. The light count command, for
each D in 0.3, 0.1, 0.06, was:

```text
ffmpeg -nostdin -hide_banner -f lavfi -i testsrc2=size=160x96:rate=30000/1001:duration=D -f null -
```

Environment deviation: Git Bash startup under this sandbox failed before any
command executed (`CreateFileMapping`, Win32 error 5). PowerShell launched the
light commands; a Python subprocess wrapper preserved collection and FFmpeg
output as bytes, adding each exit status. W1 remains a dispatcher-run Git Bash
command. No SERIAL/PARALLEL leg or GPU/footage test was run by the cell.

**Turn-1 operational MAJOR / EXECUTED; RESOLVED at the dispatcher's seat,
sandbox artifact, not a product finding:** the initial all-tests collection
produced zero stdout bytes after more than seven minutes with sustained CPU.
It was terminated, not counted as a result. A retry adding only pytest's
built-in `--debug=work/wp-t5/base-all-debug.log` reached collection of
`tests/test_prototype_backend.py`, then stopped making debug-log progress after
the `cupy.polynomial` import entry. That module selects the auto backend at
import (`tests/test_prototype_backend.py:23`; prototype GPU probing is in
`tools/prototype/backend.py:197-218`). This is the last observed hook activity,
not proof of the exact stuck Python/native function. A direct CuPy import,
bounded by a 15-second faulthandler timer, succeeded (`cupy-import-probe.log`,
`CUPY_IMPORT_OK`, `EXIT=0`); the collection interaction remains unconfirmed.
A fresh `--assert=plain` attempt also failed to produce collection output
within its observation interval. All collection processes launched by this
turn were terminated before yielding; no test body ran. The successful seat
collections resolve the STOP and complete rung 0. No product or test workaround
has been adopted for the sandbox artifact.

## Frame-count ground and branch audit

The baseline test is `tests/test_jobs_export_video.py:214-221`: 5312x4648,
30000/1001, duration 0.3, CPU-forced libx265. `Clips.make` supplies sine audio
and AAC at `:142-147`; `_settings` forces CPU at `:83-86`; `_export` selects c3
at `:95`. The light lavfi count confirms the existing nine frames and the ruled
three-frame replacement (`duration="0.1"`). Three frames retain first,
interior and last timestamps. The existing accepted sink-level 5.3K test uses
duration 0.1 at default 30 fps (`tests/test_io_video_encode.py:390-394`).

| Mechanic / source | Branch and result for 3 versus 9 |
|---|---|
| `src/clearwater/analysis/engine.py:154-182`, `:185-191` | c3's composed lead is derived from the axis. The light check gives 61 on a 150-frame 30000/1001 axis, and 3 / 9 on the respective clipped axes. Both short clips need their complete axis before final records. The whole/prefix distinction is the same. |
| `src/clearwater/analysis/engine.py:78-83`, `:945-948` | `max(STREAM_STEP=16, raw // STREAM_SHARE=64)` prevents a streamed advance at either count. Calling `_advance` for every raw count through 3 and through 9 leaves `advanced=0` in each case. |
| `src/clearwater/analysis/engine.py:73`, `:809-819`, `:609-622`; `src/clearwater/jobs/export.py:377-399` | Both complete through end-of-analysis, one smoothing chunk (limit 2048), then publish all records. Export's lead wait handles analysis completion before writing. No threshold between 3 and 9. |
| `src/clearwater/analysis/smoothing.py:30-36`, `:152-161` | Defaults are median_gaussian and 2 s, with a 0.1 s median window. Same local-kind and composed-reach operations for both counts. |
| `src/clearwater/analysis/smoothing.py:172-180`, `:194-213`, `:280-301`, `:314-365` | Empty-series, one-frame, and width-one shortcuts do not apply. At this rate the median width is 3 at both counts; endpoint holding and Gaussian smoothing execute. A light trace of default `smooth_series` on each axis visits identical source-line sets, returning 3 / 9 rows. This supports the code read; it is not a full export run. |
| `src/clearwater/jobs/export.py:1016-1048` | Every decoded frame is rendered with its own final statistics, written, then analysis is joined. No count shortcut. |
| `src/clearwater/io/video/encode.py:739-745`, `:1017-1038`, `:1061-1083` | Empty-write rejection, whole-readable-video check, last-frame end sentinel and output verification apply at both counts. |
| `src/clearwater/io/video/verify.py:614-621`, `:641-648`, `:721-736`, `:795-820` | Last-frame end uses the presentation end at both counts; missing/extra and exact pts/count checks, start, duration, orientation and audio checks remain active. Fault-specific truncation branches are not selected by a sound synthetic source. |
| `tools/video_fidelity.py:1251-1273`, `:1193-1247`; `tools/container_spike/compare.py:1098-1120` | The complete frame count and pts sequences are compared; no minimum-count exemption. Colour/depth readings and the roster remain active. |
| `tools/container_spike/compare.py:603-620`, `:624-655`, `:1193-1244`; `tools/video_fidelity.py:643-681`, `:1221-1243` | Every video pts and every audio packet is read; AAC payload MD5, decoder configuration, priming/side data and sync comparisons do not depend on a 3-to-9 frame threshold. W2 must still witness nonempty AAC and SAME on the actual three-frame export. |

No separating application branch was found. This is the rung-0 ground, not a
claim that W2 has already verified V4 on the changed clip.

## Encode-call ground

At base `3aa3c51`, `tests/test_io_video_encode.py:1482` uses
`vf.encode_file(source, out, encoder="hevc_nvenc", quality="standard", bit_depth=8)`.
The standard iteration of `:1498-1500` has exactly the same source, encoder,
quality and bit depth, with only the output path different. The AST check in
`branch-check.log` confirms these arguments. `tools/video_fidelity.py:350-394`
has no output-name-dependent encode option; it returns the report, FFmpeg PID,
encode interval and sampler together as `EncodeRun`. Keeping that object with
the shared output preserves the sink test's DR-18 proof association.

The engine test (`tests/test_jobs_export_video.py:710-725`) stays separate:
`ExportEngine` performs c3 correction and provenance=True, and returns a
`JobResult` rather than this uncorrected encode's `EncodeRun`.

## Heavy-run ledger

The dispatcher ran W1 at its seat; this cell has run no heavy command. The
requested SERIAL command was:

```text
uv run pytest -q -rs -m "gpu or footage or gui or slow" --basetemp=work/wp-t5/before-serial --durations=0 --junitxml=work/wp-t5/before-serial.xml
```

Git Bash, `PYTEST_ADDOPTS` unset, `QT_QPA_PLATFORM=offscreen`; shell `time`
recorded wall seconds. W1 was on the unchanged base tests (the intervening
`a9abb8d` commit is ledger-only).

| Window / run | Start UTC | End UTC | Command / evidence | Counts / skips | EXIT | Available memory before |
|---|---|---|---|---|---|---|
| W1 / BEFORE | 2026-10-28T19:21:35Z | 2026-10-28T20:08:14Z | SERIAL command above; `work/wp-t5/before-serial.log`, `before-serial.xml`, `before-serial-meta.log`; wall 2798.380 s | 1104 passed, 10 skipped, 4175 deselected, 1 warning; pytest 2796.46 s | 0 | 11,999,920,128 bytes; >= 5 GiB |

**W1 conditions, dispatcher report and CHARC disposition:** the WP4.1 cell
ran light tests and a 4-second probe inside W1, 19:22-19:27Z. CHARC ruled
"W1 STANDS, overlap stated." This is a qualified exclusive-window reading;
it is not described as a fully quiet host. This overlap limits attribution of
small timing differences. The acceptance threshold remains > 110 s per T5-Q5.

**MINOR / REASONED, reporting issue, RULED by the dispatcher in turn 2:** stock pytest's JUnit XML has one summed
testcase duration, not separate setup/call/teardown attributes
(`.venv/Lib/site-packages/_pytest/junitxml.py:147`, `:616-621`, default `total`
at `:410-415`). Adopted disposition: XML totals and counts, with phase timings
from the required `--durations=0` log, labelled separately. No extra plugin,
dependency or test change is needed.

## W1 phase figures and rung-1 projection

All four setups are absent from the duration listing. The log explicitly says
`(1796 durations < 0.005s hidden.  Use -vv to show these durations.)`; therefore
their reported bound is < 0.005 s, not an invented zero or an XML residual.
Call/teardown figures below are rounded log readings; XML totals have their own
three-decimal precision. `work/wp-t5/w1-analysis.json` holds the light parsing
and projection arithmetic.

| DR-65 test | Setup, log | Call, log (s) | Teardown, log (s) | Total, XML (s) |
|---|---|---|---|---|
| `test_v4_synthetic_5k3_8_7_clip` | < 0.005 s, hidden | 354.99 | 0.11 | 355.100 |
| `test_gx011627_through_the_engine_keeps_every_mandatory_and_required_item` | < 0.005 s, hidden | 434.35 | 0.07 | 434.428 |
| `test_gx011627_nvenc_levels_give_distinct_sizes` | < 0.005 s, hidden | 492.51 | 0.08 | 492.585 |
| `test_gx011627_through_the_sink_keeps_every_mandatory_and_required_item` | < 0.005 s, hidden | 215.98 | 0.07 | 216.052 |

The four calls sum to 1497.83 s. For the 5.3K test, a linear projection is
354.99 / 9 = 39.4433 s per frame, or 118.33 s for three frames: saving 236.66 s.
This assumes call cost scales with frame count; source creation, probing and
other fixed costs were not isolated. It is a projection, not an AFTER result.

The levels test has three encodes and no per-quality timings. Equal thirds
project one standard encode's share as 492.51 / 3 = 164.17 s, not a measured
standard-encode duration. Its quality-dependent cost may differ. The sink's
215.98 s includes its encode AND `fidelity_record`, so that entire call cannot
be claimed as the saving. The sink's fidelity computation remains in its body.

Combined estimate: 236.66 + 164.17 = **400.83 s (6 min 40.83 s)** per SERIAL
leg; projected wall 2798.380 - 400.83 = 2397.550 s (39 min 57.55 s).
This replaces the historical approximately 12-minute projection with the W1
ground. It is above the > 110 s criterion, but only actual W3 wall can establish
measurable saving. The remaining engine export and its assertions are kept.
Sharing moves the retained standard encode into the first consumer's fixture
SETUP, so final analysis must compare XML totals and the full SERIAL wall as
well as call phases; a phase shift alone is not a saved encode.

**MINOR / EXECUTED, aggregate reporting discrepancy:** CHARC's turn-3 packet
describes the four calls as 1498.9 s (54%). The four individual log readings
above sum to 1497.83 s, a 1.07 s difference. Retain those call phases as the
figures of record, as ruled, and describe their share as approximately 54%.
This does not change W1 wall, the projection, or the > 110 s acceptance bar.

## Rung 2: round-0 design table (approved, comparability amended)

The orchestrator approved this table on 2026-10-28, with the comparability
amendment below from CHARC `2548bd27b24909b8`. Its source-line anchors refer to
the pre-build base `3aa3c51`; function names identify the built code. It follows
CHARC's adopted T5-Q1-Q7 rulings; no
`conftest.py`, new shared module, cross-file share or frozen-interface change
is proposed. Fixture code stays in `tests/test_io_video_encode.py`.

| Required row | Design / assertion map / evidence |
|---|---|
| 5.3K frame count and ground | THREE frames: change only `duration="0.3"` to `duration="0.1"` at `tests/test_jobs_export_video.py:215`, then add `assert probe(source).video.nb_frames == 3` (T5-Q3/Q4). Rung-0 lavfi checks and the branch audit above support the first/interior/last-frame ground; 3 and 9 take the same audited application paths. Actual three-frame AAC and frame-count fidelity are still W2 checks. |
| Fixture name, scope, yield and teardown | `gx011627_standard_encode`, module-local `@pytest.fixture(scope="session")`, placed beside the existing `clips` fixture. Annotate `Iterator[tuple[Path, vf.EncodeRun]]` (`Iterator` is already imported). Resolve NVENC and source readiness first. Use `tmp_path_factory.mktemp("wp-t5-gx011627-standard")` and a local `.mp4` output. Call exactly `vf.encode_file(source, out, encoder="hevc_nvenc", quality="standard", bit_depth=8)`. Yield `(out, run)` with that output's actual `EncodeRun`; do not precompute a fidelity record. A `try/finally` covers encode and yield; teardown uses `os.remove(out)` if it exists. Existing `encode_file` also aborts on encode failure. Add a Google-style docstring with the yielded values. |
| Skip conditions and errors | Conftest's existing no-configured-footage handling is unchanged. The new fixture first runs `_nvenc_ready()` and preserves `pytest.skip("NVENC is not available on this machine")`; next it runs `_footage_clip("GX011627", load_local_config().footage_path)`, before temp-output creation or encoding. `_footage_clip` skips only a searched, absent clip; multiple matches, missing/unsearchable folders and configuration errors remain errors (`:1451-1462`). Both bodies consume the fixture before running; they keep their source lookup for fidelity/high/draft input but remove their duplicate NVENC gate. Missing-NVENC/missing-clip decisions therefore precede the shared encode, including when either test is selected alone. |
| Assertion map: `test_v4_synthetic_5k3_8_7_clip` | Keep `size="5312x4648"`, `rate="30000/1001"`, `product_engine(...)` and CPU-forced libx265 `_settings(out)`. Keep verbatim `assert result.ok, result.failure`, `(output,) = result.outputs`, and `_assert_v4(vf.fidelity_record(source, output, bit_depth=8))`. `_assert_v4` stays unchanged: `assert summary["mandatory_and_required_all_same"], (wrong["MANDATORY"], wrong[compare.REQUIRED])` and `assert _items(record)[vf._ROSTER_ITEM]["status"] == "SAME"`. Only duration changes and the ruled source-count precondition is added. |
| Assertion map: `test_gx011627_through_the_sink_keeps_every_mandatory_and_required_item` | Consume the fixture's `(out, run)`; retain source lookup. Keep verbatim IN THE BODY `record = vf.fidelity_record(source, out, bit_depth=8, run=run)`, `_assert_v4(record)`, and `assert run.report.frames_written == 681`. The helper's mandatory/required summary and roster assertions stay unchanged, reading this source/output record. The body's encode moves into the fixture; its `os.remove(out)` moves into fixture teardown. The `run` is still tied to the encode that made `out` (DR-18). |
| Assertion map: `test_gx011627_nvenc_levels_give_distinct_sizes` | Keep the high/standard/draft loop and `expected = {"high": "5.2 Main", "standard": "5.1 Main", "draft": "5.0 Main"}`. For standard, read size and HEVC level from the fixture's output; for high and draft, retain the current body encodes, size/level reads and removals under `tmp_path`. Keep verbatim `assert level is not None and level.name == expected[quality], (quality, level)` for EVERY iteration, and `assert sizes["high"] > 1.25 * sizes["standard"] > 1.25 * 1.25 * sizes["draft"], sizes`. Do not delete the fixture's standard output in the body. |
| Assertion map: `test_gx011627_through_the_engine_keeps_every_mandatory_and_required_item` | Entire test unchanged (`tests/test_jobs_export_video.py:707-725`): retain NVENC/source gates, c3 `ExportEngine` job, `quality_level="standard"`, `provenance=True`, `assert result.ok, result.failure`, `(output,) = result.outputs`, `_assert_v4(vf.fidelity_record(source, output, bit_depth=8))`, and its `finally: os.remove(output)`. All helpers unchanged. |
| Assertion-map identity: all four | Names, node IDs and markers remain unchanged. No assertion line is removed or weakened. The three changed bodies remain the only test bodies edited; no test is added. The existing collections contain 5,289 all / 1,114 SERIAL IDs for the rung-4 identity comparison. |
| Projected saving from W1 | 5.3K: 354.99 / 9 * 3 = 118.33 s projected call, saving 236.66 s. One standard encode: approximately 492.51 / 3 = 164.17 s under an explicit equal-thirds assumption, not individually timed. Combined approximately 400.83 s, with projected SERIAL wall 2397.550 s; actual W3 saving must exceed 110 s. Fixed costs, quality-dependent encode costs and W1's stated overlap limit the projection. |
| Sharing the assertions forbid | ENGINE is not shared with SINK/levels. Its corrected c3 output has provenance=True and a `JobResult`; the uncorrected `vf.encode_file` output has its encode-specific sampler/`EncodeRun`. Substitution would lose either engine-path V4 or the sink's tied NVENC proof / 681-frame assertion. The sink's fidelity record also stays in its own body; levels only needs size and level. High/draft cannot share standard because their distinct levels and size ratios are the point. This is DR-65's required recorded reason for the share not made. |
| Comparability ruling (CHARC `2548bd27b24909b8`) | **MAJOR / EXECUTED for any claim of standard-gate equivalence, not a product defect:** W1 has 9 missing-look-check-frame skips plus the standing photo skip, so it is a valid ruled BEFORE timing but NOT the standard gate. W3 and any W2 pair use the SAME local config and absent `work/wp1.3/frames` state as W1; full comparison SERIAL expects 1,104 passed / 10 skipped with identical skip reasons. NO frames copy. The dispatcher runs separate gate legs at its seat in a gate worktree whose `clearwater.local.toml` working folder points to the MAIN tree's `work/`, containing the V8 frames, as WP3.21 did. Gate SERIAL expects 1,113 passed / 1 skipped if other conditions stay the same. Record both configs and both figures, explaining that the working-folder inputs account for the 9 V8 outcomes. The gate wall is not substituted for the like-for-like W3 wall. W1 overlap remains disclosed; the four individual bodies' call phases remain the per-test figures of record. |

W1 skip evidence, read from `before-serial.log` (paths are relative here to
avoid repeating the machine prefix):

- `SKIPPED [5] tests/test_methods_assembly_v8.py:44`: absent
  `work/wp1.3/frames/GX011625_0024.925.png`.
- `SKIPPED [4] tests/test_methods_assembly_v8.py:44`: absent
  `work/wp1.3/frames/GX011625_0114.648.png`.
- `SKIPPED [1] tests/test_photo_check.py:139`: the footage folder has no photos
  yet (WP3.6P is queued).

No frames were copied, opened or deleted by this cell; none will be copied for
the gate under the amended ruling. The local config here remains unchanged.
T5-Q5's > 110 s rule and its additional-pair branch still bind. No extra window
is claimed granted.

## Turn 3: rung-3 build and light checks

- `tests/test_jobs_export_video.py`: the 5.3K test now uses duration 0.1 and
  asserts `probe(source).video.nb_frames == 3`; all existing assertions and
  export settings remain unchanged.
- `tests/test_io_video_encode.py`: added the approved session fixture
  `gx011627_standard_encode` beside `clips`, with Google-style docstring,
  pre-encode readiness checks, one real standard encode, `(out, run)` yield and
  `finally` cleanup. The sink body still creates its own fidelity record and
  checks 681 written frames. Levels reads standard size/level from that output;
  high/draft remain body encodes and are removed as before. The standard output
  is left for fixture teardown. No import, other helper or other test changed.

| Light check | Evidence under `work/wp-t5/` | Result |
|---|---|---|
| `uv run ruff check tests/test_jobs_export_video.py tests/test_io_video_encode.py` | `w2-ruff-check.log` | `All checks passed!`, `EXIT=0` |
| `uv run ruff format --check tests/test_jobs_export_video.py tests/test_io_video_encode.py` | `w2-ruff-format-check.log` | `2 files already formatted`, `EXIT=0`; no sandbox formatter artifact this time |
| Owned-file collection with sandbox shim | `w2-collect-owned.log`, `w2-collect-owned.txt`, `w2-base-owned.txt`, `w2-collect-owned.diff` | 146 tests collected in 0.69 s, `EXIT=0`; 146 unique IDs exactly match the two files' subset of `base-all.txt`; identity diff empty |
| Source/AST audit against `3aa3c51` | `w2-source-audit.log` | Every old assert retained verbatim, all changed-test markers identical, all unowned function/class ASTs unchanged; only the approved fixture added; `EXIT=0` |
| Control-patch preflight | `w2-control-manifest.json`, `w2-control-depth.patch`, `w2-control-standard-draft.patch` | Both single-line plants parse and pass `git apply --check`; neither patch applied in the cell |
| Light real instrument/control witness (160x96, CPU, three frames) | `w2-light-instrument-control.log` | Real libx265 export; unchanged `_assert_v4` passes at selected depth 8, fails at selected depth 10 with bit-depth item DIFFERENT; observer sees AAC and nonempty packets SAME; `EXIT=0` |

The owned-file collection command, with `PYTHONPATH=scripts`, offscreen Qt and
empty `PYTEST_ADDOPTS`, was:

```text
uv run pytest --collect-only -q tests/test_jobs_export_video.py tests/test_io_video_encode.py --basetemp=work/wp-t5/w2-collect-owned -p sandbox_mkdir_shim -p no:cacheprovider
```

The small instrument witness validates the observer's item schema and the
bit-depth plant cheaply. It does NOT stand in for the actual changed 5.3K
test's W2 control or a full-resolution fidelity result. No GPU/footage test body
or suite leg ran in this cell.

### W2 request and controls (not executed by the cell)

The complete dispatcher-only command script is
`work/wp-t5/w2-run-request.sh`; run from this worktree after the turn is
committed. It uses W1's unchanged config, offscreen Qt and unset
`PYTEST_ADDOPTS`. Every heavy case checks >= 5 GiB available, records the exact
command and UTC start/end in `w2-<case>-meta.log`, records wall / summary / EXIT
in `w2-<case>.log`, and writes `w2-<case>.xml`. Approximate requested window:
30-40 minutes for all five serial cases, not a measured performance claim.

| W2 case | Selection / plant | Required result |
|---|---|---|
| `combined` | Exactly the changed 5.3K, sink and levels node IDs, one process, `--durations=0` | 3 passed; one NVENC standard encode, matching sink output/EncodeRun and tied proof, 681 frames; 5.3K record count 3 and nonempty AAC packets SAME; footage-derived outputs removed |
| `sink-alone` | Only sink selected with `-k` in its module | 1 passed, proving the fixture works with this test alone |
| `levels-alone` | Only levels selected with `-k` in its module | 1 passed, proving the fixture works with this test alone |
| `control-depth` | Apply `w2-control-depth.patch`: ONLY this test's `fidelity_record` argument changes from `bit_depth=8` to 10; select just the 5.3K node | `EXIT=1`, named test FAILED, observed bit-depth item DIFFERENT; restore patch |
| `control-standard-draft` | Apply `w2-control-standard-draft.patch`: ONLY the shared fixture's encode quality changes from standard to draft, yielding the real draft output as standard; select just levels | `EXIT=1`, named levels test FAILED at level or size assertion; restore patch |

Both full-size planted breaks need W2: the 5.3K control needs the actual CPU
export (although its instrument behavior has a light witness), and the draft
control needs the real footage/NVENC output. The scratch observer
`work/wp-t5/w2_observer.py` delegates all encode/fidelity calls unchanged and
records selected frame/audio/depth items, encode counts, output/run identities,
NVENC tie and output cleanup under `work/wp-t5/w2-*-observation.json`. It adds
no persistent test logging and no fixture module to the repository. Combined
observations and the depth control have separate validation logs. The request
script restores each control, has an EXIT cleanup trap, and finally checks
that the test files match the committed candidate. The script is prepared,
not run; all five heavy-run ledger rows await dispatcher results.

## Turn 4: W2 results, corrected controls and W3 preparation

W2 ran at the dispatcher's seat on committed `045d622`, 20:34:10-20:58:41Z,
using `w2-run-request.sh` unedited. The cell read every case's log, meta log and
JUnit XML, the combined observation/check, and the depth observation. Independent
light extraction is `work/wp-t5/w2b-w2-evidence-audit.log`, `EXIT=0`.
The original W2 script is retained unchanged as the run record.

The following are the exact commands recorded in the corresponding meta logs;
`PYTEST_ADDOPTS` was unset and Qt offscreen at the seat:

```text
C1: env PYTHONPATH=work/wp-t5 uv run pytest -q -rs tests/test_jobs_export_video.py::test_v4_synthetic_5k3_8_7_clip tests/test_io_video_encode.py::test_gx011627_through_the_sink_keeps_every_mandatory_and_required_item tests/test_io_video_encode.py::test_gx011627_nvenc_levels_give_distinct_sizes --durations=0 -p w2_observer --basetemp=work/wp-t5/w2-combined --junitxml=work/wp-t5/w2-combined.xml
C2: uv run pytest -q -rs tests/test_io_video_encode.py -k test_gx011627_through_the_sink_keeps_every_mandatory_and_required_item --durations=0 --basetemp=work/wp-t5/w2-sink-alone --junitxml=work/wp-t5/w2-sink-alone.xml
C3: uv run pytest -q -rs tests/test_io_video_encode.py -k test_gx011627_nvenc_levels_give_distinct_sizes --durations=0 --basetemp=work/wp-t5/w2-levels-alone --junitxml=work/wp-t5/w2-levels-alone.xml
C4: env PYTHONPATH=work/wp-t5 uv run pytest -q -rs tests/test_jobs_export_video.py::test_v4_synthetic_5k3_8_7_clip --durations=0 -p w2_observer --basetemp=work/wp-t5/w2-control-depth --junitxml=work/wp-t5/w2-control-depth.xml
```

| Window / case | Start UTC, 2026-10-28 | End UTC | Command / evidence prefix under `work/wp-t5/` | Counts / skips / pytest seconds | EXIT | Available bytes before | Wall seconds |
|---|---|---|---|---|---|---|---|
| W2 / combined | 20:34:10Z | 20:45:11Z | C1 / `w2-combined` | 3 passed, 0 skipped; 656.67 s | 0 | 12,022,423,552 | 661.518 |
| W2 / sink alone | 20:45:12Z | 20:48:41Z | C2 / `w2-sink-alone` | 1 passed, 113 deselected, 0 skipped; 208.06 s | 0 | 12,288,577,536 | 208.938 |
| W2 / levels alone | 20:48:41Z | 20:56:40Z | C3 / `w2-levels-alone` | 1 passed, 113 deselected, 0 skipped; 478.02 s | 0 | 12,363,792,384 | 478.851 |
| W2 / depth control | 20:56:40Z | 20:58:41Z | C4 / `w2-control-depth` | 1 failed as intended, 0 skipped; 119.29 s | 1 | 12,403,748,864 | 120.293 |

Each prefix has `.log`, `.xml` and `-meta.log`. All memory checks exceeded
5 GiB. The wrapper itself exited 2 after C4; it did not execute the draft
control, the depth observation check, or its final restore check. No fifth
heavy run is inferred. No W2 overlap was reported by the dispatcher.

Combined phase log: 5.3K call 124.67 s; sink setup 160.52 s / call 49.96 s;
levels call 317.18 s. The XML testcase totals are 124.690 / 210.479 / 317.187 s
respectively. The setup accounts for the retained standard encode, so reduced
sink call time alone is not the saving. The matched three W1 call phases sum
to 1063.48 s versus this combined pytest elapsed 656.67 s (about 407 s lower,
an informational mixed-phase comparison). Only W3's full serial wall decides
T5-Q5; these figures do not establish the package's final wall saving.

`w2-combined-observation-check.log` reports both PASS lines and `EXIT=0`.
Independent JSON inspection confirms exactly one standard, one high and one
draft sink encode, all 681 frames, all outputs absent at session end. The sink
record uses the standard output and the same run identity, with NVENC tied.
The 5.3K record has mandatory/required all SAME, source/output frame counts 3,
AAC present, and six audio packets in both source/output compared SAME.
The separate selections pass with standard fixture setup 157.88 s (sink) and
161.15 s (levels), confirming either consumer works alone.

### Runner defects and W2b

- **MAJOR / EXECUTED, runner reporting:** line 83 expected `FAILED <nodeid>`
  from a `-q -rs` log. The existing log has the traceback and `1 failed`, but
  no `FAILED` summary line; the grep therefore failed despite the correct
  control result. Line 103 had the same latent defect. The light reproduction
  confirms the absent line, and the XML names the single failed 5.3K test.
  W2b uses JUnit identity/counts/failure content as the verdict, with `-rfEs`
  on its one new control run for a human-readable failure summary.
- **MAJOR / EXECUTED, runner restoration:** the dispatcher observed that
  `git apply -R` under `core.autocrlf=true` rewrote the synthetic test with
  726 CR bytes. The dispatcher restored it using
  `git -c core.autocrlf=false checkout -- tests/test_jobs_export_video.py`;
  this cell independently confirmed HEAD-identical bytes and 0 CR. Every W2b
  apply/check/reverse now uses `git -c core.autocrlf=false apply`. The EXIT
  cleanup trap uses the same form. The restore verdict checks both files'
  bytes against `git show HEAD:<path>`, 0 CR, and `git diff --exit-code`.

`work/wp-t5/w2b-run-request.sh` is a new dispatcher-only request, not an edit
to W2's record. Its light depth verdict reads the EXISTING W2 XML, log and
observation. It proves the named `_assert_v4` failure, selected depth 10 versus
actual output 8, and bit depth DIFFERENT; no depth rerun is needed.
The same checker passed here (`w2b-depth-evidence-light.log`, `EXIT=0`).
The one heavy W2b command is:

```text
env PYTHONPATH=work/wp-t5 uv run pytest -q -rfEs tests/test_io_video_encode.py::test_gx011627_nvenc_levels_give_distinct_sizes --durations=0 -p w2_observer --basetemp=work/wp-t5/w2b-control-standard-draft --junitxml=work/wp-t5/w2b-control-standard-draft.xml
```

The plant is the existing single-line fixture quality change to draft. The
new checker requires one named levels failure at the standard level assertion,
actual `5.0 Main`, plus observer evidence of the fixture's real draft encode
under the standard output name and the high encode, both 681 frames and cleaned
up. It rejects a skip, unrelated error, or an unobserved encode. All W2b output
is under `work/wp-t5/w2b-*`; no test/product source change is retained.

CPU-only checks in `w2b-light-check.log` and the final
`w2b-light-final.log` passed, `EXIT=0`: both control patches
were applied with autocrlf disabled, their one-line diffs inspected with
`git diff --stat`, and reversed. Each cycle ended with both files byte-identical
to HEAD, empty test diff and 0 CR. No pytest body ran. Git's default diff emitted
LF-to-CRLF warnings while a plant was present; the byte checks after each safe
reverse still proved 0 CR. Both Python evidence helpers parse and all new
request/helper artifacts use LF. A light extraction of the real `HevcLevel`
class confirms that its raw repr `HevcLevel(level_idc=150, high_tier=False)`
means `5.0 Main`; the checker accepts that repr as well as pytest's expanded
property text, avoiding reliance on a property appearing in a dataclass repr.

`bash -n` was attempted on each new request script. Both invocations were
blocked before parsing by the known sandbox `CreateFileMapping` Win32 error 5,
`EXIT=256` (`w2b-request-syntax-sandbox.log`, `w3-request-syntax-sandbox.log`).
Syntax is therefore NOT claimed verified here. Seat `bash -n` with `EXIT=0`
is an explicit prerequisite in each RUN REQUEST. No alternative shell parser
or successful syntax result is invented.

### W3 prepared, not run

`work/wp-t5/w3-run-request.sh` requests PARALLEL then SERIAL with `<run>=after`,
the brief's expressions/flags and separate JUnit XMLs. Per leg it records
>= 5 GiB preflight, exact command, UTC start/end, wall, counts/skip summary and
EXIT. It then captures all/SERIAL collection logs and ID lists, producing
`after-all.diff` and `after-serial.diff` against rung 0.2's IDs. Its checker
requires zero failures/errors, SERIAL 1104 passed / 10 skipped with identical
W1 skip lines, and matching collection membership/counts. It records actual
W1-W3 wall saving and whether the > 110 s bar is met; a smaller saving still
requires the ruled second pair. W3 results remain pending.

Preflight rechecks both control verdicts, W2b check-log EXITs, HEAD byte
restoration and 0 CR. The current local config hash and absent V8 frames are
pinned; HEAD and config must stay frozen through W3. Nothing copies the V8
frames or changes local configuration. This is the 1104/10 comparison, NOT the
separate dispatcher-seat standard gate (1113/1, working folder = main work).
No full suite leg or GPU/footage body ran in this cell.

The dispatcher may run W3 directly after W2b ONLY if seat syntax checks pass,
the draft control is caught by name at its expected assertion, its observation
check has `EXIT=0`, and the restore check has `EXIT=0`, HEAD-identical bytes and
0 CR in both files. W2b's depth evidence check must also have `EXIT=0`.
No further cell turn or edit is needed between those runs under those conditions.

## Turn 5: W2b and W3 evidence, report and static checks

The dispatcher ran W2b and W3 unedited after seat `bash -n`; both syntax logs
have `EXIT=0`, and both request logs have final `EXIT=0` plus their success
markers. This cell read logs/XML/observations and ran light audits only, no
pytest body. W2b wrapper period was 21:20:37-21:26:08Z; the heavy case's own
meta timestamps are 21:20:38-21:26:07Z below. W3 wrapper period was
21:57:37-22:43:57Z, including the final light collection/identity checks.

Exact commands from the run metadata (normal shell quoting shown):

```text
C5: env PYTHONPATH=work/wp-t5 uv run pytest -q -rfEs tests/test_io_video_encode.py::test_gx011627_nvenc_levels_give_distinct_sizes --durations=0 -p w2_observer --basetemp=work/wp-t5/w2b-control-standard-draft --junitxml=work/wp-t5/w2b-control-standard-draft.xml
C6: uv run pytest -q -rs -n 4 -m "not gpu and not footage and not gui and not slow" --basetemp=work/wp-t5/after-parallel --junitxml=work/wp-t5/after-parallel.xml
C7: uv run pytest -q -rs -m "gpu or footage or gui or slow" --basetemp=work/wp-t5/after-serial --durations=0 --junitxml=work/wp-t5/after-serial.xml
```

| Window / case | Start UTC, 2026-10-28 | End UTC | Command / evidence prefix under `work/wp-t5/` | Counts / pytest elapsed | EXIT | Available bytes before | Wall seconds |
|---|---|---|---|---|---|---|---|
| W2b / draft-as-standard control | 21:20:38Z | 21:26:07Z | C5 / `w2b-control-standard-draft` | 1 failed as intended, 0 skipped; 327.94 s | 1 | 11,666,051,072 | 328.925 |
| W3 / AFTER PARALLEL | 21:57:37Z | 22:06:08Z | C6 / `after-parallel` | 4174 passed, 1 skipped, 5 warnings; 508.72 s | 0 | 11,578,253,312 | 509.951 |
| W3 / AFTER SERIAL | 22:06:08Z | 22:43:49Z | C7 / `after-serial` | 1104 passed, 10 skipped, 4175 deselected, 1 warning; 2259.49 s | 0 | 11,683,901,440 | 2261.414 |

Every prefix has `.log`, `.xml`, `-meta.log`; all memory preflights exceed
5 GiB. These rows are the heavy runs; the existing depth export was NOT rerun.
W2b depth evidence, initial/final restore, and draft observation checks all
report `EXIT=0`. The draft failure is the named levels test at its standard
level assertion: `HevcLevel(level_idc=150, high_tier=False)`, actual 5.0 Main
versus expected 5.1 Main. Actual observations show the fixture's draft encode
under its standard output name, then high, both 681 frames and outputs removed.
Both test files match HEAD bytes with 0 CR before/after; no plant remains.
`W2B_REQUEST_EXIT=0`; the two W2 script defects remain disclosed above.

W3's `after-frozen.json` records head
`259a2190d5fd74764ecde1c37da074be244c74cb`, unchanged local config hash and
absent V8 frames. `after-preflight.log` and `after-identity-check.log` both
have `EXIT=0`; `W3_REQUEST_EXIT=0`. Serial skip lines are identical to W1.
PARALLEL's single skip is the standing swscale refusal at
`tests/test_color_roundtrip.py:121`. No W3 overlap was reported; W1's ruled
WP4.1 overlap is still disclosed, so an unqualified quiet-host claim is not made.

The light seat collections were:

| Collection command | Start/end UTC | Available bytes | Result |
|---|---|---|---|
| `uv run pytest --collect-only -q --basetemp=work/wp-t5/after-collect-all` | 22:43:50Z / 22:43:53Z | 11,723,149,312 | 5289 collected in 1.91 s; wall 3.311 s; EXIT=0 |
| `uv run pytest --collect-only -q -m "gpu or footage or gui or slow" --basetemp=work/wp-t5/after-collect-serial` | 22:43:53Z / 22:43:57Z | 11,733,430,272 | 1114/5289 collected, 4175 deselected in 1.88 s; wall 3.351 s; EXIT=0 |

`after-all.txt`/`after-serial.txt` exactly match baseline node-ID membership
and counts (5289/1114 unique); both `.diff` files are empty. The independent
turn-5 audit reconfirms this rather than trusting only the wrapper summary.

### W1/W3 four-test timing and savings

Phase figures below come from `--durations=0` logs; JUnit supplies totals and
counts, per the resolved turn-2 ruling. XML has no per-phase fields.

| DR-65 body | BEFORE call (s) | AFTER call (s) | BEFORE XML total (s) | AFTER XML total (s) |
|---|---|---|---|---|
| `test_v4_synthetic_5k3_8_7_clip` | 354.99 | 122.76 | 355.100 | 122.836 |
| `test_gx011627_through_the_engine_keeps_every_mandatory_and_required_item` | 434.35 | 415.64 | 434.428 | 415.713 |
| `test_gx011627_through_the_sink_keeps_every_mandatory_and_required_item` | 215.98 | 50.50 | 216.052 | 214.834 |
| `test_gx011627_nvenc_levels_give_distinct_sizes` | 492.51 | 320.71 | 492.585 | 320.794 |

AFTER sink setup is 164.27 s (retained shared standard encode), synthetic
setup 0.01 s, engine/levels setups hidden (< 0.005 s). All BEFORE setups are
hidden (< 0.005 s). The log hides 1798 AFTER phases below that bound; no hidden
phase is invented as zero. AFTER teardown in table order is
0.07/0.07/0.07/0.08 s; BEFORE is 0.11/0.07/0.07/0.08 s.

Whole SERIAL saving = 2798.380 - 2261.414 = **536.966 s (19.19%)**, above
T5-Q5's > 110 s, so no second pair. The three changed XML testcase totals
save 405.273 s; unchanged engine varies by 18.715 s; all four save 423.988 s.
The remaining 112.978 s of whole-leg difference is other suite work/overhead
variation, not assigned to the edits. This distinction and W1 overlap bound
the attribution. `after-comparison.json` and independently computed
`turn5-figures.json` agree on the wall saving.

### Assertion audit and report status

`git diff 3aa3c51..HEAD -- tests/` removes **zero assert lines**: removed /
re-added assert-line list = EMPTY. The audit independently verifies each old
assert's source text in the same test, unchanged markers, unowned function/
class ASTs, and no product/instrument changes. The retained assertions are:

- Synthetic test: `assert result.ok, result.failure`; one output and
  `_assert_v4(vf.fidelity_record(source, output, bit_depth=8))`. Added only
  `assert probe(source).video.nb_frames == 3` beside the duration reduction.
- Sink: `assert run.report.frames_written == 681` and its own
  `_assert_v4(record)`, computed in the body from source/output and actual run.
- Levels: `assert level is not None and level.name == expected[quality], (quality, level)`
  for every quality; `assert sizes["high"] > 1.25 * sizes["standard"] > 1.25 * 1.25 * sizes["draft"], sizes`.
- Engine: entire unchanged test, including `assert result.ok, result.failure`,
  one output and its V4 helper call.
- Both V4 helpers unchanged: `assert summary["mandatory_and_required_all_same"], (wrong["MANDATORY"], wrong[compare.REQUIRED])`;
  `assert _items(record)[vf._ROSTER_ITEM]["status"] == "SAME"`.

`git diff 259a219 -- tests/` is empty, including the working tree, captured in
`turn5-tests-since-w3.diff`. No test changed since W3. Independent audit
`turn5-evidence-audit.log` has `EXIT=0`; it reads existing evidence and source,
never executes a pytest body.

`docs/reports/wp-t5-suite-cost.md` is **DRAFT** until standard gate and Reviewer
A converge. It includes current source anchors, assertion/object map, both
controls, share made/not made, W1 overlap, both configurations and limits.
Standard gate at the dispatcher seat uses main `work/` inputs, expected
1113/1 SERIAL; both legs and actual gate wall remain PENDING. Documentation
changes after W3, so the final candidate still needs that gate. Proposed
DR-65 closure is conditional; CLAUDE.md's standard serial replacement stays
PENDING rather than incorrectly using the 1104/10 comparison wall. Neither
CLAUDE.md nor the register is edited.

Final static-check evidence under `work/wp-t5/`:

| Command | Summary | EXIT | Log |
|---|---|---|---|
| `uv run ruff check .` | All checks passed | 0 | `turn5-ruff-check.log` |
| `uv run ruff format --check .` | 250 files already formatted; dispatcher seat rerun pending | 0 | `turn5-ruff-format.log` |
| `uv run mypy` | Success: no issues found in 138 source files | 0 | `turn5-mypy.log` |

Tests are outside mypy's configured files as before. Uv reports that the main
tree `VIRTUAL_ENV` does not match `.venv` and is ignored; checks use this
worktree's project environment. No new dependency or file outside the owned
tracked envelope is introduced.

## Verification and review ledger

| Turn | Suspected | Independently confirmed / rejected | Fixed / open |
|---|---|---|---|
| 1 | Three frames might select a different application path | Rejected for the audited paths: source read plus small-axis smoothing/streaming checks | No test edit yet; W2 remains required |
| 1 | Sink and levels standard encodes might differ | Rejected: call-site AST comparison plus `encode_file` implementation | No test edit yet |
| 1 | JUnit might provide phase timings | Confirmed reporting mismatch by pytest implementation | RULED turn 2: XML totals/counts, phase log for phases; hidden setups reported as bounds |
| 1 | Baseline collection might be blocked under the sandbox | Confirmed sandbox no-progress; dispatcher collections passed | RESOLVED at seat; sandbox artifact, not product finding; no source fix |
| 2 | W1 might be standard-gate equivalent | Rejected: log shows 9 missing V8-frame skips plus 1 standing photo skip; XML confirms 10 skips / 1114 tests | RULED turn 3: like-for-like W3 here; separate seat gate worktree config points working folder to main work; NO frames copy |
| 2 | A full sink call might equal the saved encode duration | Rejected: source shows fidelity computation in the sink call; W1 has no per-quality encode timings | Projection labels equal-thirds estimate, retains fidelity computation and counts fixture setup |
| 3 | Refactoring might remove an assertion or change an unowned body | Rejected by verbatim-assert / marker audit, unchanged unowned ASTs and empty node-ID diff | No corrective change needed; full W2 still pending |
| 3 | The depth plant or observer might use the wrong item shape | Confirmed actual packet item names include a stream suffix and sequence summaries carry `count`; scratch observer/check corrected before request, then real small CPU witness passed | Work artifacts corrected; no extra test/product changes |
| 3 | CHARC's aggregate might equal the sum of logged calls | Rejected: 1498.9 vs logged sum 1497.83, difference 1.07 s | MINOR reporting discrepancy disclosed; individual logged call phases retained per ruling |
| 4 | W2 fixture might encode twice, lose the run tie, or fail when selected alone | Rejected by actual combined observer plus both separate green selections | Three changed tests passed; three-frame AAC SAME and 681-frame tied run confirmed |
| 4 | Depth control might have failed for an unrelated reason | Rejected by named JUnit failure at `_assert_v4` plus actual bit-depth DIFFERENT observation; light verdict EXIT=0 | No heavy rerun; W2b reuses existing evidence |
| 4 | Control grep might misclassify a real failure | Confirmed MAJOR: `-rs` omitted the expected FAILED line; wrapper exited 2 | New W2b uses JUnit failure identity/reason and `-rfEs`; draft control pending |
| 4 | Patch reversal might violate LF-only discipline | Confirmed MAJOR at seat: 726 CR bytes; dispatcher restored HEAD with autocrlf disabled | Both CPU-only safe apply/reverse cycles pass HEAD-byte / 0-CR / empty-diff checks; W2b uses safe Git option throughout |
| 4 | New Bash requests might be syntax-verified in this sandbox | Rejected: both `bash -n` attempts blocked before parsing, Win32 error 5, EXIT=256 | Mandatory seat syntax checks remain; no heavy run attempted |
| 5 | Corrected controls might still misclassify or leave a plant/CRLF | Rejected by actual named draft assertion, observation checks, depth evidence and both HEAD-byte/0-CR checks, wrapper EXIT=0 | Both controls confirmed; no source plant remains |
| 5 | W3 might change counts/skips or test IDs | Rejected by XML/logs and independent audit: same 1104/10 SERIAL skip lines, identical 5289/1114 IDs | Comparison green; standard gate remains distinct and pending |
| 5 | All whole-leg time saved might be attributable to edited bodies | Rejected: changed three XML totals save 405.273 s; whole leg saves 536.966 s | Report states phase movement and other suite variation; no over-attribution |
| 5 | An assert might have been weakened or removed | Rejected by committed diff and independent verbatim/AST audit | Zero removed assert lines; only frame precondition added; tests unchanged since W3 |
| 5 | Standard gate might be complete because W3 is green | Rejected: working-folder inputs differ and acceptance/review not supplied | DRAFT report, conditional DR-65 closure and CLAUDE figure pending |

No Reviewer A round has been supplied or adjudicated yet. The round-0 design
was approved; it is not a Reviewer A round. Future round rows record severity,
envelope, NEW/REOPENED, reverts, product/test-only fixes, evidence and dispatcher
depth. Turn 5 records W2b/W3 and yields the DRAFT report for Reviewer A over
`3aa3c51..HEAD`. The standard gate and Reviewer A verdict remain PENDING.
No heavy command or planted full-size test was run by the cell.
