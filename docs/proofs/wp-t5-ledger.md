# WP-T5 suite-cost ledger

## Dispatch and depth

Codex lane, turn 1, rung 0 only, 2026-10-28. Base:
`3aa3c51da6cc5870322fb4688fbc61227f4efdd2`, branch `wp-t5`.
The initial `git status --porcelain` was empty. Evidence is under
`work/wp-t5/`; no footage was opened by this cell. The supplied local
configuration was not changed. No product or test file was changed this turn.

Depth figures are dispatcher readings, never cell estimates.

| Turn / gate | Dispatcher-provided depth / tokens | Disposition |
|---|---|---|
| 1 / rung 0 | Not yet supplied; dispatcher fills after this turn | Yield with collection blocker and dependent W1 request |

## Rung 0 commands and results

| Check | Evidence | Result |
|---|---|---|
| Base SHA, branch, initial status | `base-head.txt`, `base-branch.txt`, `base-status.txt` | Expected base and branch; clean |
| `uv sync` | `uv-sync.log` | `EXIT=0`; no dependency-file edits |
| Collect all node IDs | `base-all.log`, `base-all-debug.log`, `base-all-retry.log`, `base-all-plain.log`; interruption notes | BLOCKED; no successful exit, summary or baseline node list |
| Collect SERIAL node IDs | Not run: the same full collection precedes marker deselection | BLOCKED by all-tests collection; no baseline node list |
| Small lavfi frame counts | `frame-count-0.3.log`, `frame-count-0.1.log`, `frame-count-0.06.log` | 9, 3, 2 frames respectively; each `EXIT=0` |
| Default smoothing / streaming checks and encode-call AST check | `branch-check.log` | `EXIT=0`; identical default smoothing line sets; identical encode arguments except output |

Collection commands use `PYTHONPATH=scripts`, `QT_QPA_PLATFORM=offscreen`, empty
`PYTEST_ADDOPTS`, and the sandbox shim:

```text
uv run pytest --collect-only -q --basetemp=work/wp-t5/base-collect-all -p sandbox_mkdir_shim -p no:cacheprovider
uv run pytest --collect-only -q --basetemp=work/wp-t5/base-collect-serial -p sandbox_mkdir_shim -p no:cacheprovider -m "gpu or footage or gui or slow"
```

Successful collection must supply output and `EXIT=` in `.log` files and `.txt`
files retaining only node IDs starting with `tests/` and containing `::`.
Those success artifacts have NOT been obtained. Each collection attempt uses
its own temp root. The light count command, for each D in 0.3, 0.1, 0.06, was:

```text
ffmpeg -nostdin -hide_banner -f lavfi -i testsrc2=size=160x96:rate=30000/1001:duration=D -f null -
```

Environment deviation: Git Bash startup under this sandbox failed before any
command executed (`CreateFileMapping`, Win32 error 5). PowerShell launched the
light commands; a Python subprocess wrapper preserved collection and FFmpeg
output as bytes, adding each exit status. W1 remains a dispatcher-run Git Bash
command. No SERIAL/PARALLEL leg or GPU/footage test was run by the cell.

**MAJOR / EXECUTED, environment blocker:** the initial all-tests collection
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
turn were terminated before yielding; no test body ran. The dispatcher must
collect both baseline lists at its seat before W1; no environment or test
workaround has been adopted. Rung 0 is incomplete until those lists exist.

## Frame-count ground and branch audit

The current test is `tests/test_jobs_export_video.py:214-221`: 5312x4648,
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

`tests/test_io_video_encode.py:1482` uses
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

No heavy run has occurred in this cell turn. W1 is requested from the
dispatcher; actual start/end, wall, counts, skips, exit and free memory must be
filled from the granted run, never from historical projections.

| Window / run | Start UTC | End UTC | Command / evidence | Counts / skips | EXIT | Available memory before |
|---|---|---|---|---|---|---|
| W1 / BEFORE | Pending | Pending | Brief SERIAL command; `work/wp-t5/before-serial.log`, `before-serial.xml`, `before-serial-meta.log` | Pending | Pending | Pending; require >= 5 GiB |

**MINOR / REASONED, reporting question for the dispatcher:** stock pytest's JUnit XML has one summed
testcase duration, not separate setup/call/teardown attributes
(`.venv/Lib/site-packages/_pytest/junitxml.py:147`, `:616-621`, default `total`
at `:410-415`). Recommended disposition: use XML totals and the already-required
`--durations=0` log for phase timings, with the two sources labelled. No extra
plugin, dependency or test change is needed. Await ruling before presenting
phase data as though it came from XML.

## Verification and review ledger

| Turn | Suspected | Independently confirmed / rejected | Fixed / open |
|---|---|---|---|
| 1 | Three frames might select a different application path | Rejected for the audited paths: source read plus small-axis smoothing/streaming checks | No test edit yet; W2 remains required |
| 1 | Sink and levels standard encodes might differ | Rejected: call-site AST comparison plus `encode_file` implementation | No test edit yet |
| 1 | JUnit might provide phase timings | Confirmed reporting mismatch by pytest implementation | Dispatcher ruling requested; phase log is available by prescribed command |
| 1 | Baseline collection might be blocked under the sandbox | Confirmed no-progress collection and debug retry; direct CuPy import succeeded, so exact cause is OPEN | No source fix; dispatcher-seat collection requested before W1 |

No Reviewer A round has been supplied or adjudicated yet. Round 0 design table
belongs to rung 2, after W1. Future round rows record severity, envelope,
NEW/REOPENED, reverts, product/test-only fixes, evidence and dispatcher depth.
