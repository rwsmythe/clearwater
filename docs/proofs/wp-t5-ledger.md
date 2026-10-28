# WP-T5 suite-cost ledger

## Dispatch and depth

Codex lane, turns 1-3, rungs 0-3, 2026-10-28. Base:
`3aa3c51da6cc5870322fb4688fbc61227f4efdd2`, branch `wp-t5`.
The initial `git status --porcelain` was empty. Evidence is under
`work/wp-t5/`; no footage was opened by this cell. The supplied local
configuration was not changed. Turns 1-2 changed this ledger only; the dispatcher
committed them at `a9abb8d` and `b17b2d4`. Turn 3 changes the two approved test
files and this ledger; product code remains unchanged. The two rung-3 test edits
are bundled in this turn as requested by the turn-3 dispatch.

Depth figures are dispatcher readings, never cell estimates.

| Turn / gate | Tokens (as supplied) | Input depth | Window | Disposition |
|---|---|---|---|---|
| 1 / rung 0 | 182,117 | 138,874 | 475,000 | Dispatcher reading supplied at turn 2; collection artifact resolved at seat |
| 2 / rungs 1-2 | 351,779 | 164,909 | 258,400 | Dispatcher reading supplied at turn 3; round-0 table approved with comparability amendment |
| 3 / rung 3 | Not yet supplied | Not yet supplied | 258,400 last reported | Yield build and W2 request |

The reported window changed from 475,000 (turn 1) to 258,400 (turn 2). Both
figures are retained as given; the dispatcher monitors depth against the smaller
window. No cell estimate replaces either reading.

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

No Reviewer A round has been supplied or adjudicated yet. The round-0 design
was approved; it is not a Reviewer A round. Future round rows record severity,
envelope, NEW/REOPENED, reverts, product/test-only fixes, evidence and dispatcher
depth. Turn 3 builds the approved test-only changes and yields for W2; no
heavy command or planted full-size test was run by the cell.
