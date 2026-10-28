# WP-T5: suite cost (DR-65)

**DRAFT - 2026-10-28. Standard gate and Reviewer A are PENDING.**

Base: `3aa3c51`. Test changes: `045d622`. W3 comparison head: `259a219`.
The tests are unchanged since W3; this turn adds documentation only.
This report does not close DR-65 or claim standard-gate acceptance.

## Claims and scope

The like-for-like SERIAL wall fell from **2798.380 s to 2261.414 s**:
**536.966 s (8 min 56.966 s, 19.19%) shorter**. This exceeds T5-Q5's > 110 s
bar, so the ruled second BEFORE/AFTER pair is unnecessary. Both comparison
serial runs passed 1104 tests and skipped 10, with identical skip lines.
W3 PARALLEL passed 4174 and skipped 1. All/SERIAL collections remain exactly
5289/1114 unique node IDs. Every existing assertion is retained verbatim.

The synthetic 5312x4648, 30000/1001 V4 export now has three frames instead of
nine. The sink and levels tests share one module-local session NVENC standard
encode of GX011627, including its actual `EncodeRun`; the engine test remains
separate. No product, instrument, dependency, marker, test name, or frozen
interface changed. Only the three approved test bodies and one fixture changed.

## Configurations and conditions

| Purpose | Working-folder configuration and outcome |
|---|---|
| W1/W3 comparison | This worktree's unchanged `clearwater.local.toml`, working folder = this worktree's `work/`. It lacks `wp1.3/frames`. Both serial runs have 1104 passed / 10 skipped, including nine missing V8 look-check-frame skips plus the standing photo skip. W3 verifies the config hash, frozen head, absent frames and identical skip lines. No frames were copied. |
| Standard gate | Dispatcher seat, separate gate worktree, local config working folder = MAIN tree's `work/`, which contains the V8 frames, as WP3.21 did. Expected SERIAL 1113 passed / 1 skipped. Both standard-gate legs and their actual serial wall are **PENDING**. The comparison wall must not replace the standard-gate figure. |

Declared host: owner's Windows 11 laptop, Python 3.12, one NVIDIA GPU/NVENC,
WP0.1 FFmpeg build, Git Bash, Qt offscreen, `PYTEST_ADDOPTS` unset. Every heavy
run's recorded available memory exceeded 5 GiB. Timing figures below are from
serial processes; the parallel wall describes that leg only.

Requested conditions were **"same quiet host, exclusive window"**. W1 has an
explicit exception: WP4.1 ran light tests and a four-second probe during
19:22-19:27Z. CHARC ruled **"W1 STANDS, overlap stated"**. W1 therefore is not
claimed fully quiet. W3 was run in the dispatcher's exclusive window; no
overlap was reported. This qualification applies to all timing claims.

## Frame-count ground

The built test is `tests/test_jobs_export_video.py:214`. Duration is now
`"0.1"`, with added `assert probe(source).video.nb_frames == 3`; size
`"5312x4648"`, rate `"30000/1001"`, and CPU-forced libx265 settings remain.
`Clips.make` supplies sine/AAC audio (`tests/test_jobs_export_video.py:142`);
`_settings` forces CPU (`:83`) and `_export` selects c3 (`:95`). Three frames
provide a first frame/start offset, an interior frame with a PTS step on both
sides, and a last frame/end duration. One frame loses the PTS step; the adopted
three-frame ground retains an interior frame. The accepted sink-level 5.3K test
also uses duration 0.1 (`tests/test_io_video_encode.py:414`, default 30 fps).

Light FFmpeg counts at 160x96 and 30000/1001 confirmed duration 0.3 -> 9,
0.1 -> 3, and 0.06 -> 2 frames (`frame-count-*.log`, all EXIT=0).
The branch audit found no threshold separating 3 and 9:

| Source (unchanged from base) | Ground for the same path |
|---|---|
| `src/clearwater/analysis/engine.py:154`, `:185` | c3's derived lead is 61 on a long 150-frame axis, clipped to the full 3/9-frame axes. Both short clips complete analysis before final records. |
| `src/clearwater/analysis/engine.py:78`, `:945` | `STREAM_STEP=16`, `STREAM_SHARE=64`; neither count advances a streamed chunk. |
| `src/clearwater/analysis/engine.py:609`, `:809`; `src/clearwater/jobs/export.py:377` | Both finish analysis in one smoothing chunk (limit 2048) and publish all records before rendering. |
| `src/clearwater/analysis/smoothing.py:30`, `:152`, `:172`, `:194`, `:280`, `:314` | Default median_gaussian, 2 s smoothing and 0.1 s median window: median width 3 at both counts; no empty, one-frame, or width-one shortcut. Independent small-axis traces visit identical source-line sets and return 3/9 rows. |
| `src/clearwater/jobs/export.py:1016` | Every decoded frame is rendered using its final statistics and written; analysis is joined. |
| `src/clearwater/io/video/encode.py:739`, `:1017`, `:1061`; `src/clearwater/io/video/verify.py:614`, `:641`, `:721`, `:795` | Empty-write rejection, full readable-list checks, last-frame end sentinel, exact count/PTS, start, duration, orientation and audio verification apply at both counts. |
| `tools/video_fidelity.py:1193`, `:1251`; `tools/container_spike/compare.py:1098` | Complete count and per-frame PTS comparisons, colour/depth and the mandatory/required roster have no minimum-count exemption. |
| `tools/container_spike/compare.py:603`, `:624`, `:1193`; `tools/video_fidelity.py:643`, `:1221` | All video PTS and audio packets, AAC payload MD5, decoder configuration, priming/side data and sync remain compared. |

The actual W2 5.3K export passed `_assert_v4`: all mandatory/required items
SAME, video source/output count 3, AAC present, and six source/output audio
packets compared SAME. Thus count, per-frame timing, start, resolution, depth,
chroma, audio, orientation and colour-tag assertions remain exercised at 5.3K
8:7. This is V4/D105/D106 coverage, not a speed guarantee for long 5.3K clips.
V15/N4 memory measurements still use the separate 150-frame bench clip.

## Assertion map and sharing as built

`git diff 3aa3c51..HEAD -- tests/` contains **zero removed assert lines**;
the removed/re-added-assert list is empty. Independent AST/source comparison
also retains every old assert verbatim in its original test, all markers,
all unowned function/class ASTs, and all test IDs. Evidence:
`work/wp-t5/turn5-evidence-audit.log`, EXIT=0.

| Test / helper | Assertions and objects retained |
|---|---|
| `test_v4_synthetic_5k3_8_7_clip` (`test_jobs_export_video.py:214`) | `assert result.ok, result.failure`; `(output,) = result.outputs`; `_assert_v4(vf.fidelity_record(source, output, bit_depth=8))`. Same size/rate, `_settings(out)` and c3 product engine. Only duration changes and `assert probe(source).video.nb_frames == 3` is added. |
| `test_gx011627_through_the_sink_keeps_every_mandatory_and_required_item` (`test_io_video_encode.py:1499`) | Its body still computes `record = vf.fidelity_record(source, out, bit_depth=8, run=run)`, calls `_assert_v4(record)`, and checks `assert run.report.frames_written == 681`. The fixture supplies that encode's actual `(out, run)`. |
| `test_gx011627_nvenc_levels_give_distinct_sizes` (`test_io_video_encode.py:1512`) | Every high/standard/draft iteration retains `assert level is not None and level.name == expected[quality], (quality, level)`, with expected 5.2/5.1/5.0 Main. Retains `assert sizes["high"] > 1.25 * sizes["standard"] > 1.25 * 1.25 * sizes["draft"], sizes`. Standard size/level read the fixture output; high/draft are still body encodes and removed there. |
| `test_gx011627_through_the_engine_keeps_every_mandatory_and_required_item` (`test_jobs_export_video.py:711`) | Entire test unchanged: c3 `ExportEngine`, standard quality, `provenance=True`, `assert result.ok, result.failure`, one output, `_assert_v4(vf.fidelity_record(source, output, bit_depth=8))`, output removal. |
| Both unchanged `_assert_v4` helpers (`test_jobs_export_video.py:107`, `test_io_video_encode.py:189`) | `assert summary["mandatory_and_required_all_same"], (wrong["MANDATORY"], wrong[compare.REQUIRED])`; `assert _items(record)[vf._ROSTER_ITEM]["status"] == "SAME"`. These still read each test's own record. |

The new `gx011627_standard_encode` fixture (`test_io_video_encode.py:162`) is
module-local, session-scoped, and documented. It checks `_nvenc_ready()` then
resolves `_footage_clip("GX011627", ...)` before creating/encoding output.
Existing NVENC/absent-clip skips and lookup/configuration errors retain their
meaning. Both consumers depend on it, so no encode precedes those decisions.
Its output lives under `tmp_path_factory`, and `finally` removes it if present.
The levels body leaves standard for teardown; high/draft cleanup stays local.

The shared call is exactly
`vf.encode_file(source, out, encoder="hevc_nvenc", quality="standard", bit_depth=8)`.
The old two calls differed only in output path, as independently AST-checked;
`tools/video_fidelity.py:350` does not select encode options from the name.
W2 observes one standard encode, matching sink output and run identity,
681 frames, NVENC proof tied, and outputs removed. The sink still computes
its own fidelity record; levels does not compute an unnecessary one.

**Share NOT made (DR-65 recorded reason):** the engine test exports corrected
c3 pixels with provenance and returns a `JobResult`; the sink writes an
uncorrected file with an encode-specific sampler/`EncodeRun`. Reusing either
would lose the engine-path V4 assertion or the sink's tied NVENC/681-frame
proof. High/draft cannot replace standard because distinct level/size
assertions require their separate encodes. No cross-file fixture is needed.

## Measured figures

All timestamps are UTC on 2026-10-28. Logs record shell wall independently
from pytest elapsed and JUnit totals. **JUnit supplies testcase totals/counts;
call/setup/teardown phases come from `--durations=0` log lines**, per the
dispatcher ruling. No call phase is inferred from XML. The four rows below
use the individual phase readings, not the packet's rounded aggregate.

| Run | Start / end UTC | Wall (s) | Pytest elapsed (s) | Counts | EXIT |
|---|---|---|---|---|---|
| W1 BEFORE SERIAL | 19:21:35 / 20:08:14 | 2798.380 | 2796.46 | 1104 passed, 10 skipped, 4175 deselected, 1 warning | 0 |
| W3 AFTER PARALLEL | 21:57:37 / 22:06:08 | 509.951 | 508.72 | 4174 passed, 1 skipped, 5 warnings | 0 |
| W3 AFTER SERIAL | 22:06:08 / 22:43:49 | 2261.414 | 2259.49 | 1104 passed, 10 skipped, 4175 deselected, 1 warning | 0 |
| Standard gate, main working-folder inputs | PENDING | PENDING | PENDING | SERIAL expected 1113 passed / 1 skipped | PENDING |

| DR-65 body | BEFORE call (s) | AFTER call (s) | BEFORE XML total (s) | AFTER XML total (s) |
|---|---|---|---|---|
| `test_v4_synthetic_5k3_8_7_clip` | 354.99 | 122.76 | 355.100 | 122.836 |
| `test_gx011627_through_the_engine_keeps_every_mandatory_and_required_item` | 434.35 | 415.64 | 434.428 | 415.713 |
| `test_gx011627_through_the_sink_keeps_every_mandatory_and_required_item` | 215.98 | 50.50 | 216.052 | 214.834 |
| `test_gx011627_nvenc_levels_give_distinct_sizes` | 492.51 | 320.71 | 492.585 | 320.794 |

The retained standard encode moves into sink setup: AFTER **164.27 s**;
BEFORE sink setup is hidden (< 0.005 s). The sink call reduction therefore is
mostly phase movement. BEFORE all four setups are hidden; AFTER synthetic
setup is 0.01 s and engine/levels setups hidden (< 0.005 s). Teardowns BEFORE
are 0.11/0.07/0.07/0.08 s in table order, AFTER 0.07/0.07/0.07/0.08 s.

The three changed testcase XML totals fall by **405.273 s**; the unchanged
engine also varies by 18.715 s. All four totals fall by 423.988 s, versus the
whole-leg observed 536.966 s saving. The remaining 112.978 s comes from other
suite work/overhead variation; it is not assigned to these edits. This limits
causal precision while preserving the measured > 110 s outcome.

Before building, W1 projected 236.66 s from reducing nine frames to three,
plus an equal-thirds estimate of 164.17 s for one standard encode: 400.83 s.
The actual retained standard setup and the 405.273 s changed-test total
reduction support that scale. The historical approximately 12-minute
projection is superseded by measured comparison figures, not claimed achieved.

Evidence prefixes under `work/wp-t5/`: `before-serial`, `after-parallel`,
`after-serial` (`.log`, `.xml`, `-meta.log`); `after-comparison.json`;
`turn5-figures.json`; `after-identity-check.log`. Both serial skip summaries
are identical (five/four absent V8 frames and one standing photo skip).
PARALLEL's one standing skip is `test_color_roundtrip.py:121`, the refused
swscale full-range case. Identity diffs `after-all.diff` and
`after-serial.diff` are empty; collections completed with EXIT=0.

## Development runs and controls

| Case | Result / evidence under `work/wp-t5/` |
|---|---|
| W2 combined changed tests | 3 passed in 656.67 s; wall 661.518 s; EXIT=0. `w2-combined*` and observation check EXIT=0 prove one shared standard encode, same output/run, tied NVENC, 681 frames, three-frame 5.3K and nonempty AAC SAME, cleanup. |
| W2 sink alone | 1 passed, 113 deselected in 208.06 s; wall 208.938 s; EXIT=0 (`w2-sink-alone*`). |
| W2 levels alone | 1 passed, 113 deselected in 478.02 s; wall 478.851 s; EXIT=0 (`w2-levels-alone*`). |
| Depth plant, W2 | Only the synthetic test's `fidelity_record` depth changed to 10. Named JUnit failure at `_assert_v4`, 1 failed in 119.29 s, EXIT=1. Actual observation: selected depth 10, output 8, bit depth DIFFERENT. `w2-control-depth*`; W2b adjudicates existing evidence with EXIT=0, no export rerun. |
| Draft-as-standard plant, W2b | Only fixture quality changed to draft. Levels fails by name at standard's level assertion: actual 5.0 Main versus expected 5.1 Main. 1 failed in 327.94 s; wall 328.925 s; EXIT=1. Observer sees real draft fixture output plus high encode, 681 frames and cleanup; `w2b-draft-observation-check.log` EXIT=0. |

W2 ran 20:34:10-20:58:41Z. Its original request script had two confirmed
runner defects: `-q -rs` omitted the `FAILED <nodeid>` summary expected by
its grep, so the wrapper exited 2 after the correctly failing depth control;
and `git apply -R` under `core.autocrlf=true` rewrote the synthetic test with
726 CR bytes. The dispatcher restored HEAD with autocrlf disabled. The draft
control did not run in W2; no result is inferred from that interrupted script.

W2b ran 21:20:37-21:26:08Z. A new request preserves W2's original script,
checks JUnit identity/reason instead of relying on a summary grep, uses
`-rfEs`, and applies/reverses with `git -c core.autocrlf=false apply`.
CPU-only cycles proved safe reversal before the request. Seat syntax checks
passed. W2b's initial/final restore checks both report HEAD-identical bytes,
empty test diff and 0 CR; wrapper `W2B_REQUEST_EXIT=0`. These are development
controls, not acceptance-suite failures. No planted edit remains.

## Validation, limits and pending acceptance

On head `259a219` plus these documentation edits, sandbox static checks:

| Check | Actual result / evidence under `work/wp-t5/` |
|---|---|
| `uv run ruff check .` | All checks passed; EXIT=0 (`turn5-ruff-check.log`) |
| `uv run ruff format --check .` | 250 files already formatted; EXIT=0 (`turn5-ruff-format.log`); dispatcher seat rerun pending |
| `uv run mypy` | Success: no issues found in 138 source files; EXIT=0 (`turn5-mypy.log`); tests remain outside configured mypy files |
| Source/assertion/identity audit | EXIT=0 (`turn5-evidence-audit.log`); zero removed assert lines; unowned definitions unchanged |
| `git diff 259a219 -- tests/` | Empty (`turn5-tests-since-w3.diff`); no test change since W3 |

All heavy tests were run by the dispatcher, never in this cell. Early sandbox
full collection stalled around CuPy import; successful seat collections
resolved it as a sandbox artifact, not a product finding. Sandbox Bash syntax
probes were blocked before parsing; seat `bash -n` passed for W2b and W3.

This is one ruled BEFORE/AFTER pair on the declared host, with W1's overlap
disclosed. Output codec/quality costs and other test runtimes vary. Session
sharing assumes the declared one-process serial leg; xdist serial execution,
reordering plugins, another FFmpeg build, or missing GX011627 are outside the
measured envelope. Missing NVENC/clip decisions retain existing skip behavior,
but absence scenarios were checked by source review rather than newly executed
hardware/environment permutations. Synthetic shortening proves V4 coverage;
it does not establish long-clip performance or N4 memory.

Only the two test files and two owned documents are in package scope. Footage
remains read-only; outputs/observations are uncommitted under the worktree's
working/temp roots. No gpmd stream, IMU/GPS data or location tag was read by
this cell or added to this report. No output or local configuration is committed.

Standard gate legs, dispatcher format rerun, Reviewer A convergence, final
acceptance and merge to main remain PENDING. Documentation now changes after
W3, so W3 is comparison evidence on its recorded head; the standard gate must
validate the final candidate. This DRAFT will be finalized only after those
results. Reviewer A's whole-package range is `3aa3c51..HEAD`; the round-0
approval is not a review round.

## For CHARC

**Proposed DR-65 closure, conditional on acceptance and landing AFTER on main:**
"DR-65 CLOSED by WP-T5: retained all four tests' assertions; shortened the
5.3K 8:7 V4 export from nine to three frames and shared one GX011627 NVENC
standard sink/levels encode. Like-for-like serial wall 2798.380 -> 2261.414 s,
saving 536.966 s (19.19%), above 110 s; W1's brief overlap disclosed. Engine
export remains separate because corrected c3/provenance JobResult and the
uncorrected sink's tied EncodeRun/681-frame proof are not interchangeable.
Standard gate and review: PENDING." Replace the pending tail with accepted
gate/review evidence before closing the register.

**CLAUDE.md serial-leg figure:** comparison value is 2261.414 s (1104/10);
the replacement **standard-gate serial figure is PENDING** (expected 1113/1).
Use the dispatcher's final gate measurement for CLAUDE.md, with its head and
configuration; do not substitute the comparison wall. This cell edits neither
CLAUDE.md nor the debt register. DR-18's tied-run association is retained;
DR-28/57/58/22/66 and DR-36/56 receive no product/instrument/guard changes.
