# WP-T6 -- Gate test sizing (AD-30) (dispatch brief, FINAL)

**Status:** FINAL 2026-10-29 on CHARC's ruling `7458b470a82d2dc3` (appended verbatim under
"Rulings" at the end; the rulings take precedence over the text above them). Drafted at the
orchestrator's seat (generation 19) under CHARC commission `8eb586a422e342ce` (Part 2).
Base = the main commit named in the dispatch prompt (`d1d8fd9` or later). Spec **v0.5.6**; no
spec clause changes. Tests, `pyproject.toml` markers, a report and a ledger only: nothing under
`src/` or `tools/`.

- Cell: `implementer-codex-sol-high` (commission: "Codex-eligible: well-specified, no interface,
  the same class as WP-T5"). Pace at commission: Codex 0.51 (7.0 % at 13.7 % of the week, read
  09:11Z); the orchestrator fills the Claude reading (`scripts/usage_claude.py`) in the dispatch
  row. Reviewer A = the Claude pass (fill Part 1, Codex lane); Reviewer B = the Claude pass at the
  orchestrator's seat (fill Part 2). If CHARC rules the lane Claude, the brief works unchanged
  with the Claude-lane reviewer (Codex) and the Claude lane's own commits.
- Worktree `.worktrees/wp-t6`, branch `wp-t6`. Runs AFTER WP4.2's ff (commission: its owned test
  files overlap). Nothing else in flight but WP4.3's brief revision (docs).
- Codex lane: the cell ends every turn with a FILES CHANGED block; the orchestrator commits and
  runs every heavy command, every command that reads the footage folder and every GPU command the
  cell yields (`.claude/agents/implementer-codex-sol-high.md`). The cell's own pytest runs use the
  sandbox shim: `PYTHONPATH=scripts uv run pytest <targets> --basetemp=work/wp-t6/tmp -p
  sandbox_mkdir_shim -p no:cacheprovider`.

**Why (commission Part 2, verbatim in substance).** "The SIZE of a gate test is set by the
PROPERTY it proves" (AD-30, `docs/decisions.md:45`). AD-30: "Frame count: the one floor is the
temporal smoothing window (2 s, c3's derived lead 61 frames at 30 fps); a test of the engine's
steady state, the analysis-end release (DR-74), the D87 re-check or the lead runs lead + a few
frames; every other property (decode correctness, colour tags, encoder levels, mux, frame-count
checks, naming, refusals, sink fidelity) is proved at six frames, the NVENC levels test at the few
dozen it needs for rate control to separate. Resolution: 1080p (the gated-resolution boundary)
unless the subject is the large-frame path (fixed-size pools, the 5.3K 8:7 clip), which stays
large and short. The real clip (GX011627) is kept only where the subject is the real container,
the hardware decoder on a real stream, the metadata tracks or the colour tags, as a stream-copied
trim (about 3 s, no re-encode) made once per session under the temp root, never the footage
folder ... Full-clip forms survive behind a marker both gate legs exclude ... Each cut is measured
first ... and every assertion is kept or its loss is named and ruled."

**Baseline of record.** `work/wp4.2/gate-logs/wp4.2-serial.log`: the SERIAL leg of WP4.2's ONE
gate (fill Part 2, Order) at the orchestrator's seat on `.worktrees/wp4.2-mc` with the main
tree's `clearwater.local.toml` copied in (`work/wp4.2/gate-logs/run_gate.sh`), `--durations=40`:
**1135 passed, 1 skipped, 5313 deselected in 2621.32 s**, exit 0 (`wp4.2-serial.done`), the one
skip the standing photo skip (`tests\test_photo_check.py:139`). Its top 40 rows merge to 38 node
IDs summing **2,226.91 s**; the other 1,097 serial tests take about 394 s. Why this log and not
the commission's `work/wp4.2-mc1-serial.log` (2,937.31 s, 5305 deselected): the gate log is the
final gate on code identical to main (`git diff --stat 8bc927a..d1d8fd9 -- src tests tools
pyproject.toml` is empty; `8bc927a` is the gate's candidate per `922d1c6`), while mc1 predates
WP4.2's Reviewer B remediation (`2f23b70`, `7b3da60` changed tests). The pair is cited as the
host's spread: between them single tests moved by up to 40 s (V3 ancuti2018 67.45 -> 27.48 s;
engine 499.89 -> 456.31 s; 5.3K 155.71 -> 121.45 s) and the leg by 316 s.

| Field | Content |
|---|---|
| Goal | The SERIAL leg (AD-28's floor) runs measurably shorter under AD-30's sizing rule with every assertion kept or its loss named and ruled; every full-size form is kept behind the new `fullclip` marker that both gate legs exclude; GX011627 tests read one stream-copied trim made once per session. |
| Spec / decision clauses | AD-30 (the rule); AD-28 (two legs; "Timing, memory and exclusive-window figures are read only from serial runs"); V4 (spec "V4 Video I/O fidelity", mandatory items incl. frame count, per-frame timestamps, start offset, colour tags); D105; D106; V9 / AD-11 (the colour round trip's regression bounds, `tests/test_color_roundtrip.py:42-53`); AD-12 / D75 (NVENC levels, `src/clearwater/io/video/encode.py:18-26`); AD-23 (forced default pipe); WP3.9 decode (`tests/test_io_video_decode_hw.py:1-8`); DR-18 (1) (CLOSED; the `EncodeRun` tie); DR-74 (CLOSED; lock below); plan 4.3, 4.5. V15 / N4: NOT touched (`tools/export_bench.py`'s 150-frame clip, `tests/test_io_video_encode_bench.py` not owned). |
| Depends on | WP4.2 on main (`ff234ee`, QA `d1d8fd9`). |
| Files owned | See "Files owned" below. |
| Interfaces consumed | none new. Tests call `probe`, `find_tool` (`clearwater.io.video`), `find_footage_file` / `FootageLookupError` / `load_local_config` (`tools/local_config.py`), `vf.encode_file`, `vf.fidelity_record`, `vf.gather`, `vf.location_like` (`tools/video_fidelity.py`), `verify_module.read_hevc_level`, `product_engine`, as today. |
| Done | Plan 4.5. ruff check, ruff format --check, mypy; the collection identities of rung 4; the full-size forms green once in W4 (Q8); Reviewer A converged; Reviewer B returned; then the ONE two-leg gate at the orchestrator's seat on the final candidate (fill Part 2, Order) with the amended expressions (Q2); its SERIAL leg is the AFTER figure, compared with the baseline of record (Q6: measurable = more than 110 s shorter); report and ledger written. The 900 s target is a TARGET, not a pass criterion (Q7). No harness gate (nothing in `scripts/`, `.claude/`, kernel docs or `tests/harness/` is owned). |

## Files owned

A file appears here only because a map row needs it. Of the commission's EXPECTED list,
`tests/test_prototype_clip.py`, `tests/test_prototype_backend.py`, `tests/test_wp42_v3_product.py`
and `tests/test_wp321_fft_release.py` are NOT owned: every row in them is KEEP (map rows 9-13, 15,
17, 27, 30, 38). `tests/fixture_plugin.py` is NOT owned (Q1).

- EDIT `tests/conftest.py`: ADD the two session fixtures of "The trim fixture" below, a
  `GX011627_FRAMES = 681` module constant and one module-docstring paragraph naming them. Every
  existing line stays byte-identical (the guard, `_footage_skip_reason`,
  `pytest_collection_modifyitems`, `_release_fft_plans`, the `pytest_plugins` statement). New
  imports go INSIDE the fixture bodies only: `tests/test_conftest_guard.py:118-125` copies
  `conftest.py` into a miniature repository beside `tools/local_config.py` alone, so a module-level
  import of `video_fidelity` or `clearwater` would break the guard tests. `from local_config import
  find_footage_file, FootageLookupError` may join the existing module-level `local_config` import
  (that file is copied).
- EDIT `tests/test_jobs_export_video.py`: ONLY `test_gx011627_through_the_engine_...` (`:711`) and
  the removal of `_footage_clip` (`:698`) and of the imports `FootageLookupError`,
  `find_footage_file`, `load_local_config` (`:43`) IF nothing else in the module uses them after the
  edit (ruff F401 decides; grep first).
- EDIT `tests/test_io_video_encode.py`: ONLY the fixture `gx011627_standard_encode` (`:161`), the
  sink test (`:1499`) and the levels test (`:1512`). `_footage_clip` (`:1475`) stays (its own test
  at `:1489` uses it).
- EDIT `tests/test_io_video_decode_hw.py`: the module docstring (`:1-8`), `FOOTAGE_FRAMES` (`:37`)
  use, the `footage` and `footage_reference` fixtures (`:75`, `:90`), `check_footage` (`:110`), the
  three real-clip tests (`:119`, `:129`, `:142`), and ONE new test (rung 2).
- EDIT `tests/test_color_roundtrip.py`: ONLY if rung 1's rule (Q4) selects a gate count below 30:
  `FOOTAGE_FRAMES` (`:60`), the module docstring line (`:11-12`), the bounds comment (`:42-50`, one
  added sentence) and `test_pair_round_trip_on_the_owners_main_case` (`:315`). Otherwise untouched.
- EDIT `pyproject.toml`: ONE line added to `markers` (`:74-79`); nothing else.
- NEW `docs/reports/wp-t6-gate-sizing.md`, `docs/proofs/wp-t6-ledger.md`.

**NOT owned:** every other test file and every other test in the owned files (including
`test_v4_synthetic_5k3_8_7_clip`, `test_a_short_5k_8_by_7_clip`, `Clips`, `Runs`, `_assert_v4`,
`test_the_footage_lookup_skips_only_a_missing_clip`); `tests/fixture_plugin.py`, `tests/fixtures/`
and the manifest; `tests/test_conftest_guard.py`; all of `src/` (IF-1..IF-10 FROZEN, AD-20) and
`tools/`; `uv.lock`; `docs/review-gate-clearwater.md`, `CLAUDE.md`, `docs/decisions.md`, the
register (CHARC writes those at the accept: commission "Register and docs at the accept").

## Locks

Commission's, in substance: tests only, plus `pyproject.toml` markers; no `src/`, no `tools/`;
V15 / N4 bench figures untouched (`tools/export_bench.py`'s 150-frame clip is not this package);
no footage write; the conftest guard stays; DR-74's case keeps its above-lead floor at a gated
resolution (its WP4.2 B4 strengthening honoured: `tests/test_wp321_fft_release.py:155` is not
edited); the WP2.3 fixtures and their manifest are not re-generated. Added:

1. The trim is written ONLY under the session temp root (`tmp_path_factory`); every run this
   brief names passes `--basetemp` under `work/`, so the trim lands inside `work/`. It is removed
   at session teardown. The fixture asserts its folder is not inside the configured footage folder
   (belt over the conftest guard).
2. No `gpmd` decode: data tracks are stream-copied and their packets compared by pts, size and
   hash only, as `tools/video_fidelity.py:46-50` does. No location tag VALUE is read into any
   comparison, message, log or report: tag dictionaries are filtered with `vf.location_like` before
   use, and location-like keys compare by presence only.
3. Nothing footage-derived is committed: no trim, no frame, no packet digest, no tag value. The
   report carries counts, times, the cut point `T`, stream kinds and codec tags only.
4. No test is deleted. A full-size form changes only by gaining the `[full]` / `[first30]` id and
   the `fullclip` mark; its assertions are byte-identical in effect (same literals reached).
5. No new dependency; the SERIAL expression never runs under `-n`.

## The trim fixture (rung 2) -- in `tests/conftest.py` (Q1)

`gx011627_trim` (`scope="session"`) yields `tuple[Path, int]` = (trim path, its frame count N):

1. Locate: `find_footage_file("GX011627", load_local_config().footage_path)` with the skip rule of
   `tests/test_io_video_encode.py:1475-1486` verbatim in effect (skip ONLY when the folder was
   searched and the clip is absent; several matches, a missing folder or an unsearchable folder
   RAISE; DR-27 (1) direction).
2. Cut point: list the source's video packets in decode order with `ffprobe -v error
   -select_streams v:0 -show_entries packet=pts_time,flags -of csv=p=0 -read_intervals %+6
   <src>`. N = the 0-based decode-order index of the first packet whose flags contain `K` and
   whose `pts_time >= 3.0`; T = that packet's `pts_time`. None found = the fixture FAILS.
3. Copy, mirroring the sink's own stream selection and metadata flags
   (`src/clearwater/io/video/encode.py:378-384`, `:420-431`) with input index 0 and `-c copy`:
   `ffmpeg -nostdin -hide_banner -v error -y -i <src> -map 0:v:0` + `-map 0:<i>` for every
   `probe(src).audio` stream + `-map 0:<i>` for every `probe(src).data` stream whose `codec_tag !=
   "tmcd"` + `-c copy -map_metadata 0 -map_metadata:s:v:0 0:s:v:0 -write_tmcd 1
   -video_track_timescale <probe(src).video.time_base.denominator> -frames:v N -t T -f mp4 <out>`.
   `-frames:v N` cuts the video at the keyframe in decode order (whole GOPs); `-t T` stops audio and
   data there. Add NO other flag; if a check below fails, STOP with the probe output (a finding).
4. Checks, each a fixture `assert` (a bad trim fails every consumer, never runs one):
   (a) N >= 66 (c3's lead 61 + 5); (b) the trim's first N video packets equal the source's first N
   in order by (`pts_time`, `duration_time`, `size`, `flags`, MD5 from `-show_data_hash MD5`), so no
   re-encode; (c) the trim's video pts, sorted, are `[k * 1001 for k in range(N)]` at time base
   1/30000 (contiguous); (d) stream parity: the same list of (`codec_type`, `codec_name`,
   `codec_tag_string`) as the source, and per video stream the same width, height, `pix_fmt`,
   `color_range`, `color_space`, `color_transfer`, `color_primaries`, rotation; per audio stream
   the same `sample_rate`, `channels`; a `gpmd` and a `tmcd` data stream present iff the source has
   them; (e) tags: the format and per-stream tag dictionaries with location-like keys removed
   (`vf.location_like`) are equal except the keys in the allow-list ruled at rung 1 (`ALLOWED_TAG_DIFFS`,
   a module constant); location-like keys present in one iff in the other.
5. Teardown removes the trim and its folder.

`gx011627` (`scope="session"`, `params=[pytest.param("trim", id="trim"), pytest.param("full",
id="full", marks=pytest.mark.fullclip)]`) yields `tuple[Path, int]`: for `trim` the value of
`gx011627_trim` (requested lazily with `request.getfixturevalue("gx011627_trim")` so the `full`
form never makes a trim); for `full` (the located source, `GX011627_FRAMES`). Google docstrings on
both fixtures and the constant.

## Rung-1 map (the serial leg's top 40, merged per node ID; seconds = setup + call in the baseline)

Floors per AD-30: SIX = six frames; LEAD = lead 61 + a few; LEVELS = a few dozen; LARGE = the
large-frame subject stays large and short; TRIM = real-container subject -> the trim. "CUT" rows are
built at rung 3; "KEEP" rows are not edited; savings are ESTIMATES (linear in frames plus a fixed
part), to be MEASURED, never assumed (AD-30's caution).

### CUT rows (7)

**R1 `tests/test_jobs_export_video.py::test_gx011627_through_the_engine_keeps_every_mandatory_and_required_item`** -- 456.31 s.
- Property: V4 MANDATORY + REQUIRED all SAME (and the roster item) on the real GoPro clip through
  `ExportEngine` (c3, NVENC standard, `provenance=True`) (module docstring `:1-12`; V4, D105).
- Size now: all 681 frames of GX011627, 3840x2160 29.97 HEVC 8-bit (`:716`; facts
  `tests/test_io_video_decode_hw.py:5`, `docs/reports/wp1.2b-speed-memory.md:181`).
- Floor: TRIM (real container through the engine). The trim's N >= 66 also passes c3's lead.
- Chosen: `gx011627` (trim in the gate; full behind `fullclip`). Change: the test requests
  `gx011627`; `source, _ = gx011627` replaces `:716`; `_nvenc_ready()` skip stays first in the body.
- Assertions: `result.ok`; one output; `_assert_v4(vf.fidelity_record(source, output, bit_depth=8))`;
  `os.remove(output)` -- all KEPT. Node ID -> `[trim]` / `[full]`.
- ESTIMATE: 456 s at about 0.67 s/frame -> about 70 s at N = 90; saving about 385 s.

**R2 `tests/test_io_video_encode.py::test_gx011627_nvenc_levels_give_distinct_sizes`** -- 330.02 s.
- Property: AD-12 levels: each quality signals its level (`5.2 / 5.1 / 5.0 Main`) and sizes
  separate (`high > 1.25 x standard > 1.25^2 x draft`) on busy real 4K (`:1512-1532`).
- Size now: 681 frames; two encodes in the body plus the shared standard encode (WP-T5).
- Floor: LEVELS on real content. The ceiling binds through a one-second VBV buffer
  (`encode.py:222`: bufsize = maxrate, "one second"), so the encode must span several seconds:
  the whole trim (N about 90, about three buffer lengths). TRIM.
- Chosen: the trim's N frames (Q5). Change: the fixture `gx011627_standard_encode` requests
  `gx011627` and encodes `gx011627[0]`; the body's `source` = `gx011627[0]`; nothing else.
- Assertions: level names and the size chain KEPT verbatim. Rung 1 MEASURES the three sizes on a
  provisional trim; any link of the chain at or below its 1.25 factor = STOP.
- ESTIMATE: about 0.24 s/frame per encode -> about 50 s; saving about 280 s.

**R3 `tests/test_io_video_encode.py::test_gx011627_through_the_sink_keeps_every_mandatory_and_required_item`** -- 221.69 s (setup 171.57 = the shared standard encode, call 50.12).
- Property: V4 through `FFmpegVideoSink` on the real clip, every frame written (`:1499-1506`; V4).
- Size now: 681 frames; `run.report.frames_written == 681` (`:1506`).
- Floor: TRIM. Chosen: `gx011627` via the shared fixture.
- Change: `source, frames = gx011627`; `assert run.report.frames_written == frames` (the `full`
  form reaches 681 through `GX011627_FRAMES`). This is the ONE operand change; Q3 rules it KEPT.
- Assertions: `_assert_v4(record)` KEPT; frame count KEPT per Q3. The `EncodeRun` still ties the
  NVENC proof to its encode; `tied` was never asserted here (DR-18 (1) closed on the full clip;
  the report records the trim run's `nvenc_proof` as an observation).
- ESTIMATE: about 35 s; saving about 185 s.

**R4 `tests/test_color_roundtrip.py::test_pair_round_trip_on_the_owners_main_case`** -- 169.97 s.
- Property: V9-side regression bounds of the swscale pair on the owner's main case (4K BT.709 full
  range `yuvj420p`), and six planted defects each exceed a bound (`:315-362`, bounds `:42-53`).
- Size now: the first 30 frames (`FOOTAGE_FRAMES = 30`, `:60`), read straight from the footage
  file (only the first frames are decoded), 7 measurements (base + 6 plants) = 210 frame round trips.
- Floor: SIX (colour tags / colour pair), BUT the bounds were measured on 30 frames (`:44-50`), so
  the rule is applied by measurement (Q4). Source stays the footage file (the trim would not change
  the frames read).
- Chosen: the smallest N in {6, 10, 15} passing Q4's rule; else KEEP 30 and the file is not edited.
- Change (if N < 30): `@pytest.mark.parametrize("frames", [pytest.param(N, id=f"first{N}"),
  pytest.param(30, id="first30", marks=pytest.mark.fullclip)])`; `FOOTAGE_FRAMES` -> the parameter
  in all four uses (`:330`, `:331`, `:358`, `:359`); docstring "the first 30 frames" -> "the first
  `frames` frames (30 in the `fullclip` form, where the bounds were measured)".
- Assertions: the pix-fmt/size check, base mean and share bounds, every plant's exceedance -- KEPT
  verbatim (same constants). Their ground at N is rung 1's measurement, recorded per plant.
- ESTIMATE: if cost is per frame, N = 6 -> about 34 s plus per-measure FFmpeg start-up; saving 0
  (KEEP) to about 135 s. Highest uncertainty in the map.

**R5 `tests/test_io_video_decode_hw.py::test_the_real_clip_decodes_to_its_pts_and_the_reference_bytes`** -- 152.09 s (setup 43.52 = `footage_reference`, call 108.57).
**R6 `...::test_the_real_clip_through_the_forced_default_pipe_is_identical`** -- 131.88 s.
**R7 `...::test_the_real_clip_through_cuda_decode_is_identical`** -- 105.41 s.
- Property: WP3.9 decode on a real HERO13 stream gives every frame's pts and bytes equal to an
  independent FFmpeg run, through the large pipe, the forced default pipe (AD-23), and CUDA
  (`:1-8`, `:110-146`).
- Size now: 681 frames (`FOOTAGE_FRAMES = 681`, `:37`); the `footage` fixture locates the clip
  itself (`:75-87`).
- Floor: TRIM (hardware decoder on a real HEVC stream). Chosen: `gx011627`.
- Change: `footage(gx011627)` returns `probe(gx011627[0])` (module scope stays; its own locator
  goes); a new module fixture `footage_frames(gx011627) -> int` returns `gx011627[1]` (never
  `nb_frames`, which is a probe field, not the asserted count); `check_footage(frames, reference,
  count)` takes the count as a third argument and R5-R7 request `footage_frames` and pass it;
  R5's `len(footage_reference) == FOOTAGE_FRAMES` reads `== footage_frames`; the constant
  `FOOTAGE_FRAMES` (`:37`) is deleted (the `full` form reaches 681 through `GX011627_FRAMES`);
  docstring `:5-7` says "the GX011627 trim (the whole clip, 681 frames, in the `fullclip` form)".
- Assertions: `time_base == Fraction(1, 30000)`; `len(reference) == frames`; pts `== [k * 1001 for
  k in range(frames)]`; digests `== reference` -- KEPT (operand per Q3).
- ESTIMATE: 389.38 s x 90/681 plus start-up -> about 58 s; saving about 330 s.

### KEEP rows (31) -- not edited

| # | Node ID (file:line) | s | Property and source | Why KEEP |
|---|---|---|---|---|
| 8 | `test_jobs_export_video.py::test_v4_synthetic_5k3_8_7_clip` (`:214`) | 121.45 | V4 on 5312x4648 8:7, 3 synthetic frames, CPU-forced libx265 (D106) | Already cut by WP-T5 (DR-65, T5-Q3: three frames ruled). LARGE: stays large. A GPU backend would change the ruled CPU-forced path (T5 assertion map); see Q7. |
| 9 | `test_prototype_clip.py::test_bench_whole_clip_modes_record_their_pass` (`:807`) | 66.12 | WP1.2B bench records for 5 modes; synthetic 60 frames 960x540 (`:51`, `:77`) | Below 1080p; `CLIP_FRAMES` is shared by the module's tests and the witness plant needs > 30 frames (`:1018`); cost is per bench run (6 `bench.main` calls), `tools/` code. |
| 10 | `test_prototype_backend.py::test_bench_gpu_records_graphics_memory` (`:335`) | 63.67 | bench GPU memory record; 2 frames 128x72 (`:336`) | **OPEN**: already minimal; the 63 s is not in any size the test sets (it is inside `tools/prototype/bench.py`). Rung 1 profiles it once; any lever is `tools/` (Q7, banked). |
| 11 | `test_prototype_clip.py::test_the_output_witness_passes_a_correct_export` (`:1042`) | 33.17 | WP1.2B witness; same 60-frame clip | As row 9. |
| 12 | `test_wp42_v3_product.py::test_ad14_bound_with_the_product_method[c3]` (`:416`) | 28.45 | AD-14 / V3 temporal smoothing; WP2.3 `ad14-flicker` 90 frames 540x960 (`:189`) | LEAD subject (smoothing); the clip is a WP2.3 fixture (lock); below 1080p. |
| 13 | same `[ancuti2018]` | 27.48 | as 12 | as 12. |
| 14 | `test_lookcheck_deep.py::test_the_deep_clip_is_staged_smoothed_encoded_checked_and_pruned` (`:988`) | 26.98 | WP1.3D staged deep clip; 4 s 1080p synthetic, 0.4 s excerpt (`:1004`, `:1021`) | LEAD-adjacent (2 s staged smoothing over the source); 1080p; the excerpt is set by `tools/lookcheck`; below materiality (Q10). |
| 15 | `test_prototype_clip.py::test_footage_smoke_gx011628` (`:849`) | 26.89 | prototype export of 30 frames of GX011628 (`:856`) | SIX would apply (30 -> 6), estimated saving about 15 s: below materiality (Q10); GX011628 is not AD-30's trim clip. |
| 16 | `test_io_video_encode_bench.py::test_run_once_records_the_row_and_deletes_the_output` (`:274`) | 22.58 | bench row, timing bound DR-58 (c), WP2.3 sample | A timing bound (fill GATE_CHECKS); V15/N4 bench file not owned. |
| 17 | `test_wp321_fft_release.py::test_the_analysis_end_release_frees_the_pool_while_frames_render` (`:155`) | 19.64 | DR-74: 90 frames 1920x1080 (`:163-168`) | Commission lock (above-lead floor, gated resolution, B4). 90 -> 66 would save about 5 s: below materiality (Q10). |
| 18 | `test_jobs_export_video.py::test_v11_a_killed_export_process_...` (`:650`) | 19.57 | V11 kill mid-export; 640x360 8 s synthetic (`:653`) | Below 1080p; needs the export still running at frame 10 of a CPU job; below materiality. |
| 19 | `test_container_spike.py::test_footage_smallest_chapter_against_itself_is_all_same` (`:901`) | 18.76 | WP1.5 instrument self-compare on GX011628 incl. `gpmd` (`:912`) | Real-container subject, but GX011628, not the trim clip; below materiality. |
| 20 | `test_lookcheck.py::test_the_flicker_clip_is_built_checked_and_pruned` (`:744`) | 18.41 | WP1.3 flicker pack; 10 s 320x240, excerpt 179-180 frames set by `tools/lookcheck` (`:755`, `:766`) | Excerpt length is tool code; below materiality. |
| 21 | `test_wp42_v3_product.py::test_v3_ratio_on_the_jittering_patch_clip_...[ancuti2018]` (`:436`) | 12.56 | V3 25 %; jitter clip 90 frames 270x480 (`:189`) | LEAD subject; small. |
| 22 | same `[c3]` | 12.15 | as 21 | as 21. |
| 23 | `test_lookcheck_deep.py::test_the_scan_runs_on_one_deep_chapter_at_three_timestamps` (`:360`) | 11.84 | WP1.3D scan, 3 timestamps of a footage chapter | Three frames already. |
| 24 | `test_wp321_bench.py::test_a_device_frame_run_gives_the_sink_device_frames` (`:52`) | 11.76 | device frames to the sink; WP2.3 45-frame sample (`:57`) | WP2.3 fixture (lock). |
| 25 | `test_wp41_v8.py::test_v8c_k_above_1_on_real_sized_content` (`:214`) | 10.31 | V8 k > 1 on 1080x1920 crops (`:182-183`) | Already 1080p; "real-sized" is the subject. |
| 26 | `test_gui_preview.py::test_planted_unbounded_view_factor_fails` (`:178`) | 10.02 | planted unbounded loop must time out (`timeout=10`, `:152`) | The 10 s bound is the subject. |
| 27 | `test_prototype_clip.py::test_the_output_witness_catches_a_wrong_statistics_index_by_name` (`:1105`) | 9.83 | witness plant, 30-frame shift | Needs > 30 frames (row 9). |
| 28 | `test_io_video_encode.py::test_a_short_5k_8_by_7_clip` (`:414`) | 9.70 | sink V4 at 5312x4648, 3 frames | LARGE, already short. |
| 29 | `test_io_video_encode_bench.py::test_an_nvenc_run_records_a_proof_tied_or_with_its_reason` (`:589`) | 9.17 | bench NVENC proof, WP2.3 sample | Bench file not owned; WP2.3 fixture. |
| 30 | `test_prototype_clip.py::test_the_output_witness_catches_a_frame_swap_by_name` (`:1073`) | 9.07 | witness plant | As row 9. |
| 31 | `test_jobs_export_video.py::test_v4_every_decodable_sample_through_the_engine[vid-hevc8-bt709-full-hevc_nvenc]` (`:170`) | 8.11 | V4 on a WP2.3 sample | WP2.3 fixture (lock). |
| 32 | `test_methods_assembly_v8.py::test_v8_planted_range_error_fails` (`:104`) | 7.97 | V8 planted range error on a 1080x1920 crop (`:36`) | Already 1080p. |
| 33 | `test_noise_experiments.py::test_the_runner_records_one_deep_frame_under_two_settings` (`:553`) | 7.90 | one 4K footage frame (`:561`) | One frame; 4K is asserted (`:565`). |
| 34 | `test_methods_assembly_v8.py::test_v8_preview_against_the_downscaled_export[GX011625_0114.648-c3-cpu]` (`:89`) | 7.84 | V8 on a 1080x1920 crop | Already 1080p. |
| 35 | same `[GX011625_0024.925-c3-cpu]` | 7.80 | as 34 | as 34. |
| 36 | `test_methods_assembly.py::test_gpu_reads_only_at_the_counted_points_...[c3]` (`:786`) | 6.97 | host-read count, 64x96 (`:792`) | Minimal already. |
| 37 | `test_prototype_temporal.py::test_7_the_runner_on_ten_frames_writes_its_record` (`:861`) | 6.79 | WP1.4 excerpt of 10 footage frames | Small; tool-set excerpt. |
| 38 | `test_prototype_backend.py::test_gpu_output_agrees_with_cpu[size2-c3]` (`:189`) | 6.58 | GPU/CPU agreement at 1024x1536 | The 1024 px size is the subject. |

**Map totals (ESTIMATE).** CUT rows R1-R7: 1,567.37 s in the baseline; estimated saving 1,180 s
without R4, up to 1,315 s with it. Projected AFTER serial leg 2,621 - (1,180 .. 1,315) + the trim
(a few seconds) = **about 1,310 .. 1,445 s**, with host spread of the order of the 316 s between
the two WP4.2 serial logs. Each per-test estimate assumes cost linear in frames plus a few seconds
of start-up; the trim's N (about 90) depends on GX011627's keyframe spacing, read at rung 1. The
900 s target is NOT reached by this map (Q7).

## Task ladder

Build cycle per rung (`docs/dispatch-recipe.md` section 2). Every run routes to a file under
`work/wp-t6/` (`> file 2>&1; echo EXIT=$? >> file`); read the summary and `EXIT=` lines only.
Orchestrator: copy the main tree's `clearwater.local.toml` into the worktree before any footage
run (fill GATE_CHECKS). The amended expressions (Q2), Git Bash, `PYTEST_ADDOPTS` unset,
`QT_QPA_PLATFORM=offscreen`, a fresh `--basetemp` under `work/` per run:

    PARALLEL  uv run pytest -q -rs -n 4 -m "not gpu and not footage and not gui and not slow and not fullclip" --basetemp=work/wp-t6/<run>-parallel
    SERIAL    uv run pytest -q -rs -m "(gpu or footage or gui or slow) and not fullclip" --basetemp=work/wp-t6/<run>-serial --durations=0 --junitxml=work/wp-t6/<run>-serial.xml
    FULLCLIP  uv run pytest -q -rs -m "fullclip" --basetemp=work/wp-t6/<run>-fullclip --durations=0

**Rung 0 -- facts (light, no window).** `uv sync`; base SHA; clean `git status`; re-run `git diff
--stat 8bc927a..<base> -- src tests tools pyproject.toml` (empty = the baseline stands; non-empty
= STOP, the stack moved). Collect all / parallel / serial with the CURRENT expressions into
`work/wp-t6/base-{all,parallel,serial}.txt` (node-ID lines only; counts equal pytest's own line).

**Rung 1 -- measurement (window W1, about 15 min), then the round-0 table, then YIELD.**
Yielded as one script `work/wp-t6/w1.sh` the orchestrator runs:
1. The packet listing of rung-2 step 2 on GX011627: N, T, the keyframe spacing (counts only).
2. A provisional trim by rung-2 step 3 into `work/wp-t6/w1-scratch/`, and checks 4(a)-(e) printed
   as PASS/FAIL per item; the tag keys that differ, by KEY only (never a value), for
   `ALLOWED_TAG_DIFFS`.
3. On the provisional trim: `vf.encode_file` at high, standard, draft (NVENC, 8-bit), the three
   sizes and `read_hevc_level` names, and the size-chain ratios.
4. R4: `measure_roundtrip` on GX011627 for the base and each of the six plants at frames 6, 10, 15
   (the test's own filters, `tests/test_color_roundtrip.py:328-356`), each figure's mean and share
   and each verdict, plus the wall time per N.
5. Row 10: one `cProfile` run of `test_bench_gpu_records_graphics_memory` (top 15 cumulative
   lines to a file) to name where the 63 s goes.
6. Delete `w1-scratch/` (it holds footage-derived files) and list what stays.
Then ONE round-0 table to the dispatcher: N, T; checks 4(a)-(e); the proposed `ALLOWED_TAG_DIFFS`
keys with the reason each differs; R2's measured chain (or a STOP); R4's N by Q4's rule (or KEEP);
row 10's finding; the updated estimate. YIELD; build nothing before the reply.

**Rung 2 -- the trim fixture (light build; short window W2).** Add the two fixtures and the
constant to `tests/conftest.py` per "The trim fixture". Add to `tests/test_io_video_decode_hw.py`
`test_the_gx011627_trim_is_a_stream_copy_of_the_source(gx011627_trim)` (marks `footage`, `slow`):
re-runs checks 4(a)-(e) through a module helper and asserts each by name (the fixture's asserts
guard consumers; this test reports them under one node ID). W2: that test alone, then
`tests/test_conftest_guard.py` (light, the guard tests). Controls (ledger): a planted re-encode
(`-c:v libx265` in place of `-c copy`) fails 4(b); a planted `-frames:v N+1` fails 4(c) or
4(b), recorded which; both reverted. One commit.

**Rung 3 -- the cuts (light edits; window W3, about 10 min).** R1, R2+R3 (one fixture), R5-R7,
and R4 if rung 1 selected an N, each per the map, one commit per file. W3: SERIAL expression
restricted to the changed node IDs (`[trim]` / `[firstN]`) with `--durations=0`. CHECK: green;
one standard encode in the combined run; the engine output's V4 record SAME on the trim. Controls
(ledger, reverted): the levels test with the fixture yielding the draft output as standard fails
by name (WP-T5's control on the trim); `footage_reference` truncated by one frame fails R5.

**Rung 4 -- the marker and the full-size forms (light, then window W4, about 27 min).**
`pyproject.toml` markers gains exactly: `"fullclip: the full-size form of a gate test sized by
AD-30 (whole GX011627 or the pre-AD-30 frame count); excluded from both gate legs, run in package
windows"`. Collect all / parallel / serial (amended) / fullclip into `work/wp-t6/cand-*.txt`.
CHECK: no duplicates; parallel, serial and fullclip pairwise disjoint; parallel + serial +
fullclip = all; fullclip = exactly the `[full]` / `[first30]` IDs; against `base-*`: in ALL,
removed = exactly the 6 or 7 unsuffixed CUT IDs, added = their two suffixed forms each plus the
rung-2 test; in SERIAL, removed = the same unsuffixed IDs, added = the `[trim]` / `[firstN]`
forms plus the rung-2 test; PARALLEL unchanged. W4: the FULLCLIP command once (Q8). CHECK: green;
`frames_written == 681` reached in the full sink form.

**Rung 5 -- report, ledger, review, then the one gate.** Write
`docs/reports/wp-t6-gate-sizing.md`: claims; the map as built (each row CUT/KEEP, assertions,
measured vs estimated); the trim's N, T and checks (no values); R2's chain and R4's figures per N;
row 10's finding; the collection identities; the W2-W4 figures; limits (the trim covers the first
N frames only; full-clip behaviour is the `fullclip` window's); a "for CHARC" block: the gate
expressions, the GATE_CHECKS collection identity "parallel + serial + fullclip = all", the
`CLAUDE.md` paragraph and AD-28 figures to update, any bank item (row 10, Q7's gap list). Ledger
`docs/proofs/wp-t6-ledger.md`: one row per heavy run (start, end, command, counts, EXIT, free
memory before), review rounds, the dispatcher's depth figures. Final head: ruff check, ruff
format --check, mypy. Then Reviewer A to convergence; then the orchestrator's Reviewer B; then
the ONE two-leg gate (orchestrator's seat, main's config copied, amended expressions, SERIAL with
`--durations=0 --junitxml`) = the AFTER figure. A last docs-only turn writes the AFTER row, the
BEFORE/AFTER comparison (leg wall; the seven CUT bodies from the gate log vs the junit file; the
KEEP rows' spread) and Q6's verdict into the report.

## Declared operating envelope

Windows 11, Python 3.12, pytest 8.4.2 with pytest-xdist 3.x (`uv.lock`), Git Bash, headless Qt,
the owner's laptop with its one NVIDIA GPU and NVENC, the WP0.1 FFmpeg build, GX011627 present
in the configured footage folder (read only). The SERIAL leg runs in one process. Out of envelope:
the SERIAL or FULLCLIP expression under `-n` (a session fixture is per worker); a reordering
plugin; several GPUs; a footage folder without GX011627 (the trim and full forms skip); another
FFmpeg build; a run without `--basetemp` (the trim then lands in the OS temp root, removed at
teardown; Q9).

## Review loop (Reviewer A) -- per `docs/review-gate-clearwater.md` Part 1

- Tier FAST (test-only, as T5-Q6); any change outside the owned files is a STOP first, and would
  make it STRONG. Round policy is the fill's; recommended cap ONE round plus the single cleanup
  (Q11).
- Codex lane (reviewer = Claude, run by the driver between turns): `scripts/codex_cell.py review`,
  `claude -p --model opus --effort high` per the fill's Part 1 lane paragraph and the WP-T4 Q6
  ruling; assertions as that paragraph (`modelUsage` key, `is_error` false, a `VERDICT:` line,
  empty `git status --porcelain` afterwards, every finding EXECUTED or REASONED). Never `--bare`.
- Evidence: `C:\Users\rwsmy\clearwater-review-evidence\wp-t6\rN\` with md5s; the ledger.
- WHAT TO EXAMINE: every assertion of R1-R7 still present and reading the same object (the map);
  the only operand change is Q3's; the trim is a stream copy (4(b)), whole GOPs (4(c)), with the
  source's streams and tags (4(d), 4(e)), and is removed at teardown; the `full` form never makes a
  trim; the fixtures skip exactly where the old locators skipped and raise where they raised; no
  module-level import in `conftest.py` beyond `local_config`; no location value anywhere in code,
  messages, logs or the report; the collection identities; the figures are serial runs as named.
- Reviewer B: the orchestrator's seat pass on the merge candidate, the other model.

## Notes for the cell

- **Windows.** W1 (about 15 min), W2 (short), W3 (about 10 min), W4 (about 27 min). Ask with
  `WINDOW REQUEST: <command, expected duration, evidence path>`; one heavy job at a time; at least 5
  GiB available first; `WINDOW RELEASED: <summary>` after. Codex lane: yield the exact command
  line; the orchestrator runs it and hands back the output path. No full suite before the gate
  (fill Part 2, Order: "A full-suite run before B is development evidence, not the gate, and gets
  no window").
- **Yields.** At rung 1 (round-0 table) and after every review round; report the depth figure the
  dispatcher gives you.
- **Return report** = the FINAL turn's message, under about 70 lines, then the FILES CHANGED block:
  per-commit changes; the map as built; the trim's N, T, checks; R2's chain; R4's N or KEEP; the
  controls; W2-W4 figures; the collection identities; review rounds; open items.
- **STOP for:** any change in `src/` or `tools/`; a needed edit to a NOT-owned file; any existing
  `conftest.py` line changed; a test deleted; an assertion removed or weakened beyond Q3's operand;
  a trim check failing; R2's chain failing on the trim; the stack moved (rung 0); any write outside
  the worktree, the temp root and `work/`.
- **Working rules:** commit subjects `test(wp-t6): ...` (`docs(wp-t6)` for report and ledger), one
  logical change per turn; every blob LF. Never `git stash`; never a bare `cd`; never post to a
  mailbox. The footage folder is read only; no footage-derived output is committed.

## Questions for CHARC (recommended answer first)

1. **Where the trim fixture lives.** Recommended: `tests/conftest.py`, additive only, imports
   inside the fixture bodies. Ground: its subject is the footage (it already loads the local
   configuration and owns the footage skip, `:303-330`), while `tests/fixture_plugin.py` states
   "Nothing here reads the footage folder or any local configuration" (`:20`), a contract the
   WP2.3 fixtures rely on. Cost: the guard file is touched (DR-22, DR-66 become consumer notes;
   `tests/test_conftest_guard.py` runs at W2). Alternative: `fixture_plugin.py` with that sentence
   amended.
2. **Marker and expressions.** Recommended: `fullclip`; the WP-T6 gate already runs the amended
   expressions (rung table above), recorded in the accept; at the accept CHARC updates the fill's
   two-leg command, its collection rule to "parallel + serial + fullclip = all", and `CLAUDE.md`.
   Alternative: the gate runs the old expressions (the full forms would then run in the SERIAL leg
   and the AFTER figure would not show the cut).
3. **The frame-count operand.** Recommended: KEPT, not a loss: R3's `frames_written == 681` and
   R5-R7's 681 become the clip's own count (N on the trim, 681 on the full form through
   `GX011627_FRAMES`), the same property ("every frame") on the clip the test reads. Alternative:
   name it a loss and write a DR row.
4. **R4's rule.** Recommended: the gate form takes the smallest N in {6, 10, 15} at which the base
   is within both bounds AND every one of the six plants exceeds a bound (each verdict as at 30),
   AND the measured wall at N is at least 30 s below 30's; else R4 is KEEP at 30 and the file is
   not edited. Deterministic (bitexact FFmpeg, `:49-50`), so a verdict is not a flake risk.
   Alternative: KEEP 30 without measuring (AD-30's caution read as a hold).
5. **R2's frame count.** Recommended: the whole trim (N, about 90 = about three one-second VBV
   buffers), chain measured at W1, STOP if any link fails. Alternative: a fixed 60 frames (two
   buffers) by a separate `-frames:v` encode, which un-shares the standard encode (WP-T5's share).
6. **BEFORE and AFTER.** Recommended: BEFORE = the baseline of record (no BEFORE window: code
   identical, per-test durations present for all seven CUT rows); AFTER = the package's one gate's
   SERIAL leg at the orchestrator's seat (same seat, main's config, as WP4.2's gate); measurable =
   more than 110 s shorter (T5-Q5). Alternative: a BEFORE window on the base (about 44 min) for a
   junit file, as WP-T5's W1.
7. **The 900 s target.** Recommended: a TARGET recorded against the measured AFTER, not a pass
   criterion: the map projects about 1,310-1,445 s. The gap sits outside AD-30's rule or the locks:
   the 5.3K CPU export (121 s; a GPU path would change T5-Q3's ruled form), the prototype bench
   tests (rows 9-11, 163 s; `tools/` fixed costs, row 10 OPEN), V3/AD-14 (81 s, lead-bound), and
   the 1,097-test tail (about 394 s). Recommended: the report lists them as a follow-on candidate
   (BANKED with the owner's trigger), WP-T6 does not reach for them.
8. **Prove the full forms once.** Recommended: yes, W4 (`-m fullclip`, about 27 min), since this
   package rewrites how they reach the clip. Alternative: no run; the first package window that
   asks for them proves them.
9. **The trim off the gate.** Recommended: teardown removal, no working-folder check (a worktree
   run's `--basetemp` lies in the worktree's `work/`, not the configured working folder, so the
   check would refuse legitimate runs); the limit goes in the envelope. Alternative: refuse to
   make a trim unless the basetemp is inside the configured working folder.
10. **Materiality.** Recommended: a row whose estimated saving is under 20 s is KEEP (rows 14, 15,
    17-20): the two WP4.2 serial logs show single tests moving by up to 40 s, so such a saving is
    not measurable, and each cut costs review. Alternative: apply the rule to every row (DR-74
    90 -> 66 frames, GX011628 smoke 30 -> 6), about 20 s more.
11. **Reviewer tier and cap.** Recommended: FAST, ONE round plus the single cleanup; Codex lane:
    the pinned Claude pass (opus / high). Any non-test change: STRONG.
12. **Lane.** Recommended: Codex, as commissioned: every cut is fixed by the map, and the three
    judgment points (the cut point, R2's count, R4's N) are measured against stated rules with a
    STOP on failure. The one place a Codex cell could drift is the fixture's FFmpeg flags; the
    brief fixes them and forbids additions.

## Return report

Your FINAL turn's message, under about 70 lines, as listed in "Notes for the cell", then the FILES
CHANGED block. An undelivered report is a failed handoff.

## Rulings (CHARC `7458b470a82d2dc3`, 2026-10-29 11:04:46Z, verbatim; they GOVERN the text above)

**CHARC RULING on the WP-T6 brief DRAFT (query 699ca89c367b9a9d; `work/wp-t6/wp-t6-brief-DRAFT.md` md5 87d8c915, read in full): FINAL on this post.** Commit it as `docs/briefs/wp-t6-brief.md` with Status FINAL and these rulings appended under "Rulings" (they take precedence over the text above them, WP-T5's form); dispatch to the Codex lane from `d1d8fd9` or later.

**Corrections (a)-(g) ACCEPTED.** 900 s is not reachable within AD-30 and the locks; the trim is about 7.6x, not 200x; the eight-test sum is 1,791.74 s; parametrising renames the cut IDs and the collection identity is restated; no BEFORE window; the trim flags are fixed; the four files with KEEP rows only are not owned. I checked `test_conftest_guard.py:122` (copies `conftest.py` beside `local_config.py` alone), `fixture_plugin.py:20` (the no-footage contract) and `encode.py:222/:280` (bufsize = maxrate, one second); each holds.

**Q1 conftest, additive, imports inside the fixture bodies: CONCUR.** `from local_config import find_footage_file, FootageLookupError` may join the existing module-level import at `conftest.py:70` (that file is copied into the guard's miniature). DR-22 and DR-66 become consumer notes; the guard tests run at W2.

**Q2 marker `fullclip`, amended expressions at the gate: CONCUR.** The WP-T6 gate runs the three amended expressions; at the accept I update the fill's two-leg command, its collection rule ("parallel + serial + fullclip = all") and `CLAUDE.md`. ADDED, for the fill at the accept (the cell does nothing for it): the FULLCLIP expression runs at least once per phase-end gate report and whenever a package brief asks, so the full forms never rot.

**Q3 the frame-count operand: CONCUR, KEPT, not a loss.** The property is "every frame of the clip the test reads"; N on the trim and 681 on the full form through `GX011627_FRAMES`. No DR row.

**Q4 R4's rule: CONCUR as drafted** (smallest N in {6, 10, 15} with the base inside both bounds, every plant exceeding a bound, and a wall at least 30 s under 30's; else KEEP 30, file untouched). ADDED: the round-0 table reports each plant's MARGIN at the chosen N (figure minus bound, mean and share), not only the verdict; a plant whose margin at N is under half its margin at 30 makes R4 KEEP (the bounds were measured at 30 and the gate form must not sit on the line).

**Q5 R2's frame count = the whole trim: CONCUR**, chain measured at W1, STOP on any link at or under 1.25.

**Q6 BEFORE = the baseline of record, AFTER = the package's one gate: CONCUR, with the verdict TIGHTENED.** The two WP4.2 serial logs differ by 316 s on identical code, so a leg wall alone cannot carry a 110 s verdict. Q6's PASS rests on the seven CUT bodies' per-test sum (junit AFTER vs the baseline log) being more than 110 s under the baseline sum (1,567 s), with the leg wall REPORTED alongside and the KEEP rows' spread as the noise estimate. The projected 1,180 s saving is ten times the spread, so this changes nothing if the map holds; it keeps the verdict honest if it does not.

**Q7 the 900 s target: CONCUR.** 900 s was my figure in the commission and the map shows it is outside AD-30 plus the locks. It is a TARGET recorded against the measured AFTER, not a pass criterion. The gap list (the 5.3K CPU export 121 s in its T5-Q3 form; the prototype bench rows 9-11, 163 s, cost inside `tools/`; V3/AD-14 81 s lead-bound; the 394 s tail) is BANKED in the report's "for CHARC" block as a follow-on candidate; I write its DR row at the accept with the owner as trigger. Row 10 stays OPEN for rung 1's profile: 63 s for two 128x72 frames is a fixed cost somewhere in `tools/prototype/bench.py`, and the profile's top lines name it so the follow-on can be a one-line brief.

**Q8 prove the full forms once (W4, about 27 min): CONCUR.** This package rewires how they reach the clip; once is the proof. The W4 figures are information, never a V16 row.

**Q9 the trim off the gate: CONCUR** (teardown removal; lock 1's not-inside-footage assert stays; no working-folder check; the OS-temp case is an envelope limit).

**Q10 materiality 20 s: CONCUR** (rows 14, 15, 17-20 KEEP).

**Q11 Reviewer A FAST, one round plus the single cleanup: CONCUR**; the fill's round policy governs if round 1 finds a major; any non-test change makes it STRONG and is a STOP first.

**Q12 lane Codex: CONCUR, as commissioned.** Codex-built packages become 6 of the harness's accepts (WP3.20R, WP-T4, WP-T5, WP4.2a, WP4.2b, WP-T6); pace at ruling Codex 0.54, Claude not read (owner's probe). Reviewer A = the pinned Claude pass; B = the Claude pass at your seat.

**Two notes for the cell, not rulings.** (i) `pytest.param(..., marks=pytest.mark.fullclip)` inside a fixture's `params` applies the mark to every test item generated for that parameter, which is what the expressions rely on; the rung-4 collection check is the proof, and the cell records the pytest version it saw it on. (ii) In R5-R7 the module-scoped `footage` fixture depends on the session-parametrised `gx011627`, so it is built once per parameter; that is intended and the ledger says so.

**Register at the accept (mine):** the Q7 gap-list row; a row 10 row if the profile names a `tools/` lever; DR-22 and DR-66 consumer notes; the fill, `CLAUDE.md` and AD-28's figures updated to the measured AFTER; the fullclip-per-phase-gate sentence in the fill.

Main is at d1d8fd9, free. WP4.3's brief revision follows this dispatch, as sequenced.
