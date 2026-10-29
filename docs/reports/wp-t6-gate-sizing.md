# WP-T6 -- gate test sizing (AD-30)

Status: Reviewer A R1 converged after its single cleanup and W2b re-proof;
Reviewer B returned and all dispositions were ruled by CHARC. The ONE two-leg
gate is green on candidate `a4472fb`; Q6 PASS is established below. Accept
is pending. W3 is development evidence; W4 proves the retained full forms
and is not a V16 row. Review/gate evidence and dispositions are recorded in
the cumulative ledger and the sources below.

## Claims and scope

All seven CUT rows now have a gate form and a retained full-size form. The
real-container tests use one session-scoped, stream-copied GX011627 trim;
the colour-pair test uses six frames. Full-size forms carry `fullclip`, which
both gate expressions exclude. Every mapped assertion remains: the count
operands follow the selected clip under Q3 (90 on the trim, 681 on the full
clip), and the colour bounds and defect assertions are unchanged. No test was
deleted. No product interface, `src/`, `tools/`, dependency, WP2.3 fixture or
manifest was changed. V15/N4 and the locked DR-74 case remain untouched.

The implementation and ownership proof are recorded in
`docs/proofs/wp-t6-ledger.md` (rung 2, seat-2 turns 2-4 and their static-proof
artifacts). The candidate collection identities below independently account
for every renamed and added test. Successful W2 controls prove the trim
checker rejects re-encoding and a late cut; W3 controls prove the selected
tests still reject a draft substituted for standard and a shortened reference.

This report contains counts, timings, codec identifiers and metadata/item
names only. No footage-derived media, packet digest, metadata value or footage
path is included. Heavy evidence was produced serially at the dispatcher's
seat on the declared Windows/Python/FFmpeg/NVIDIA envelope; the cell did not
read the footage folder or run those windows.

## Baseline and timing convention

The baseline of record is the WP4.2 gate SERIAL leg: 1,135 passed, one standing
photo skip, 5,313 deselected, EXIT 0, wall 2,621.32 s. Its seven CUT setup+call
totals sum to 1,567.37 s. The merged top-duration map contains 38 tests;
the remaining 1,097 serial tests account for about 394 s. These historical
figures are transcribed from `docs/briefs/wp-t6-brief.md`, sections "Baseline
of record" and "Rung-1 map", which identify
`work/wp4.2/gate-logs/wp4.2-serial.log` as the original source. That original
log is not copied into this worktree. Rung 0's empty code diff against the
baseline is recorded in `docs/proofs/wp-t6-ledger.md`.

Historical leg spread was about 316 s and individual tests moved by up to
43.58 s (engine 499.89 -> 456.31 s; brief, same section; corrected under B3).
That is a noise indicator, not a matched new
measurement. Q6's tightened verdict requires the final gate's seven CUT
per-test sum to fall by more than 110 s. A shorter leg wall alone cannot
establish PASS. The 900 s serial target is recorded separately and is not a
pass criterion.

The tables distinguish rounded `--durations=0` setup/call times from JUnit
`testcase.time`, which includes teardown. "Not listed" means the setup was
below pytest's displayed duration threshold, not necessarily zero. The shared
standard encode is charged to R2 in W3 and R3 in W4; the independent decoder
reference is charged to R5. Per-row shifts in setup attribution are not
independent speed measurements.

## Map as built -- CUT

All paths in this table are under `tests/`. Gate suffixes are `[trim]` except
R4 `[first6]`; retained suffixes are `[full]` except R4 `[first30]`.

| Row | Test | Size and property | Assertions retained |
|---|---|---|---|
| R1 CUT | `test_jobs_export_video.py::test_gx011627_through_the_engine_keeps_every_mandatory_and_required_item` | Real-container V4 through c3/standard NVENC/provenance; 681 -> 90 frames | `result.ok`, one output, `_assert_v4(vf.fidelity_record(..., bit_depth=8))`, output removal; readiness skip remains first within the test body |
| R2 CUT | `test_io_video_encode.py::test_gx011627_nvenc_levels_give_distinct_sizes` | Busy real content, whole trim spanning several VBV buffer lengths; 681 -> 90 | All three HEVC level names and both strict 1.25 size links; shared `EncodeRun` remains tied to its encode |
| R3 CUT | `test_io_video_encode.py::test_gx011627_through_the_sink_keeps_every_mandatory_and_required_item` | Real-container sink V4; shared standard encode on selected source | `_assert_v4(record)` and `frames_written == frames`; Q3 retains the "every frame" property on trim and full |
| R4 CUT | `test_color_roundtrip.py::test_pair_round_trip_on_the_owners_main_case` | Main-case colour pair; 30 -> 6 decoded frames | Source format/size, base mean/share bounds, all six defect exceedances, same constants and filters |
| R5 CUT | `test_io_video_decode_hw.py::test_the_real_clip_decodes_to_its_pts_and_the_reference_bytes` | Real-stream CPU decode; 681 -> 90 | Time base, independent reference length, every PTS and frame digest; count comes from selected fixture, never probe `nb_frames` |
| R6 CUT | `test_io_video_decode_hw.py::test_the_real_clip_through_the_forced_default_pipe_is_identical` | Same real stream through forced default pipe (AD-23) | Same time base/PTS/reference-byte equality over the selected count; default-pipe forcing retained |
| R7 CUT | `test_io_video_decode_hw.py::test_the_real_clip_through_cuda_decode_is_identical` | Same real stream through CUDA decode | Same time base/PTS/reference-byte equality over the selected count; CUDA path retained |

The jobs-only locator and its unused imports were removed. The encode module's
own locator and lookup test remain; the dispatcher granted removal of only its
unused `load_local_config` import. Decode's module fixtures rebuild for each
session source parameter. Full-size assertions reach the original literals
through the selected count; the full fixture lazily avoids creating a trim.
Fixtures run before the test body's NVENC readiness skip; on an out-of-envelope
machine without NVENC, trim/lookup errors can therefore precede that skip (F5).
The marker's registration was advanced from rung 4 to fix the real-conftest
guard's in-process strict-marker load (W2 run 1), with no other marker change.

### Estimated and measured CUT times

Baseline and W1 estimates below are from the ledger's "Rung-1 round-0 table";
the estimate scales frame costs and allocates the measured encode triplet,
so it does not predict fixture ownership or fixed overhead accurately.
Measured W3 values are from `work/wp-t6/w3/w3-serial.xml` and
`work/wp-t6/w3/01-serial.log`; W4 values are from
`work/wp-t6/w4/w4-fullclip.xml` and `work/wp-t6/w4/01-fullclip.log`.
All figures are seconds. These windows are not the final gate comparison.

| Row | Baseline setup+call | W1 estimated gate | W3 gate JUnit total | W4 full JUnit total |
|---|---:|---:|---:|---:|
| R1 | 456.31 | 60.31 | 76.681 | 445.748 |
| R2 | 330.02 | 51.04 | 78.986 | 327.713 |
| R3 | 221.69 | 32.15 | 11.858 | 223.542 |
| R4 | 169.97 | 35.77 | 37.206 | 167.290 |
| R5 | 152.09 | 20.10 | 21.711 | 150.251 |
| R6 | 131.88 | 17.43 | 17.203 | 135.280 |
| R7 | 105.41 | 13.93 | 13.207 | 104.019 |
| Sum | 1,567.37 | 230.73 (unrounded model) | 256.852 | 1553.843 |

Displayed phase times (setup / call), from the corresponding duration logs:

| Row | W3 setup / call | W4 setup / call |
|---|---:|---:|
| R1 | 2.22 / 74.44 | not listed / 445.65 |
| R2 | 25.94 / 53.01 | not listed / 327.71 |
| R3 | not listed / 11.83 | 163.24 / 60.30 |
| R4 | not listed / 37.18 | 0.01 / 167.28 |
| R5 | 8.10 / 13.58 | 42.94 / 107.31 |
| R6 | not listed / 17.18 | not listed / 135.28 |
| R7 | not listed / 13.18 | not listed / 104.02 |

The W1 model estimated a CUT sum of 230.73 s and a serial wall near 1,286.88 s
plus repeated trim-test/fixed overhead; the once-per-session packet listing
and trim/check measurement was 2.205362 s
(`work/wp-t6/w1/01-packets.json`, `02-timing.json`; model in the ledger).
W3 and W4 replace those estimates for the selected windows only. The extra
parity node's W3 JUnit total is 1.112 s; its call is 1.08 s. W3's standard
encode observer records exactly one invocation of
`gx011627_standard_encode`, 90 frames and `nvenc_tied=true`
(`work/wp-t6/w3/01-serial.json`). That tie is an observation, not a new sink
assertion or a replacement for the closed DR-18 proof.

## Map as built -- KEEP

Every row below is KEEP, with its original assertions and sizes unchanged.
Times are historical baseline setup+call seconds, not W3/W4 remeasurements;
there is no claimed saving. Properties, sizes, times and the KEEP rationale
are transcribed from `docs/briefs/wp-t6-brief.md`, "KEEP rows". Line numbers
there refer to the pre-cut snapshot. Rows with abbreviated names use the
brief's own abbreviations.

| # / disposition | Node ID (file:line) | s | Property and source | Why KEEP |
|---|---|---|---|---|
| 8 KEEP | `test_jobs_export_video.py::test_v4_synthetic_5k3_8_7_clip` (`:214`) | 121.45 | V4 on 5312x4648 8:7, 3 synthetic frames, CPU-forced libx265 (D106) | Already cut by WP-T5 (DR-65, T5-Q3: three frames ruled). LARGE: stays large. A GPU backend would change the ruled CPU-forced path (T5 assertion map); see Q7. |
| 9 KEEP | `test_prototype_clip.py::test_bench_whole_clip_modes_record_their_pass` (`:807`) | 66.12 | WP1.2B bench records for 5 modes; synthetic 60 frames 960x540 (`:51`, `:77`) | Below 1080p; `CLIP_FRAMES` is shared by the module's tests and the witness plant needs > 30 frames (`:1018`); cost is per bench run (6 `bench.main` calls), `tools/` code. |
| 10 KEEP | `test_prototype_backend.py::test_bench_gpu_records_graphics_memory` (`:335`) | 63.67 | bench GPU memory record; 2 frames 128x72 (`:336`) | **BANKED after W1 profile**: already minimal; the 63 s is not in any size the test sets (it is inside `tools/prototype/bench.py`). W1 profiled it once (finding below); the lever is `tools/` (Q7, banked). |
| 11 KEEP | `test_prototype_clip.py::test_the_output_witness_passes_a_correct_export` (`:1042`) | 33.17 | WP1.2B witness; same 60-frame clip | As row 9. |
| 12 KEEP | `test_wp42_v3_product.py::test_ad14_bound_with_the_product_method[c3]` (`:416`) | 28.45 | AD-14 / V3 temporal smoothing; WP2.3 `ad14-flicker` 90 frames 540x960 (`:189`) | LEAD subject (smoothing); the clip is a WP2.3 fixture (lock); below 1080p. |
| 13 KEEP | same `[ancuti2018]` | 27.48 | as 12 | as 12. |
| 14 KEEP | `test_lookcheck_deep.py::test_the_deep_clip_is_staged_smoothed_encoded_checked_and_pruned` (`:988`) | 26.98 | WP1.3D staged deep clip; 4 s 1080p synthetic, 0.4 s excerpt (`:1004`, `:1021`) | LEAD-adjacent (2 s staged smoothing over the source); 1080p; the excerpt is set by `tools/lookcheck`; below materiality (Q10). |
| 15 KEEP | `test_prototype_clip.py::test_footage_smoke_gx011628` (`:849`) | 26.89 | prototype export of 30 frames of GX011628 (`:856`) | SIX would apply (30 -> 6), estimated saving about 15 s: below materiality (Q10); GX011628 is not AD-30's trim clip. |
| 16 KEEP | `test_io_video_encode_bench.py::test_run_once_records_the_row_and_deletes_the_output` (`:274`) | 22.58 | bench row, timing bound DR-58 (c), WP2.3 sample | A timing bound (fill GATE_CHECKS); V15/N4 bench file not owned. |
| 17 KEEP | `test_wp321_fft_release.py::test_the_analysis_end_release_frees_the_pool_while_frames_render` (`:155`) | 19.64 | DR-74: 90 frames 1920x1080 (`:163-168`) | Commission lock (above-lead floor, gated resolution, B4). 90 -> 66 would save about 5 s: below materiality (Q10). |
| 18 KEEP | `test_jobs_export_video.py::test_v11_a_killed_export_process_...` (`:650`) | 19.57 | V11 kill mid-export; 640x360 8 s synthetic (`:653`) | Below 1080p; needs the export still running at frame 10 of a CPU job; below materiality. |
| 19 KEEP | `test_container_spike.py::test_footage_smallest_chapter_against_itself_is_all_same` (`:901`) | 18.76 | WP1.5 instrument self-compare on GX011628 incl. `gpmd` (`:912`) | Real-container subject, but GX011628, not the trim clip; below materiality. |
| 20 KEEP | `test_lookcheck.py::test_the_flicker_clip_is_built_checked_and_pruned` (`:744`) | 18.41 | WP1.3 flicker pack; 10 s 320x240, excerpt 179-180 frames set by `tools/lookcheck` (`:755`, `:766`) | Excerpt length is tool code; below materiality. |
| 21 KEEP | `test_wp42_v3_product.py::test_v3_ratio_on_the_jittering_patch_clip_...[ancuti2018]` (`:436`) | 12.56 | V3 25 %; jitter clip 90 frames 270x480 (`:189`) | LEAD subject; small. |
| 22 KEEP | same `[c3]` | 12.15 | as 21 | as 21. |
| 23 KEEP | `test_lookcheck_deep.py::test_the_scan_runs_on_one_deep_chapter_at_three_timestamps` (`:360`) | 11.84 | WP1.3D scan, 3 timestamps of a footage chapter | Three frames already. |
| 24 KEEP | `test_wp321_bench.py::test_a_device_frame_run_gives_the_sink_device_frames` (`:52`) | 11.76 | device frames to the sink; WP2.3 45-frame sample (`:57`) | WP2.3 fixture (lock). |
| 25 KEEP | `test_wp41_v8.py::test_v8c_k_above_1_on_real_sized_content` (`:214`) | 10.31 | V8 k > 1 on 1080x1920 crops (`:182-183`) | Already 1080p; "real-sized" is the subject. |
| 26 KEEP | `test_gui_preview.py::test_planted_unbounded_view_factor_fails` (`:178`) | 10.02 | planted unbounded loop must time out (`timeout=10`, `:152`) | The 10 s bound is the subject. |
| 27 KEEP | `test_prototype_clip.py::test_the_output_witness_catches_a_wrong_statistics_index_by_name` (`:1105`) | 9.83 | witness plant, 30-frame shift | Needs > 30 frames (row 9). |
| 28 KEEP | `test_io_video_encode.py::test_a_short_5k_8_by_7_clip` (`:414`) | 9.70 | sink V4 at 5312x4648, 3 frames | LARGE, already short. |
| 29 KEEP | `test_io_video_encode_bench.py::test_an_nvenc_run_records_a_proof_tied_or_with_its_reason` (`:589`) | 9.17 | bench NVENC proof, WP2.3 sample | Bench file not owned; WP2.3 fixture. |
| 30 KEEP | `test_prototype_clip.py::test_the_output_witness_catches_a_frame_swap_by_name` (`:1073`) | 9.07 | witness plant | As row 9. |
| 31 KEEP | `test_jobs_export_video.py::test_v4_every_decodable_sample_through_the_engine[vid-hevc8-bt709-full-hevc_nvenc]` (`:170`) | 8.11 | V4 on a WP2.3 sample | WP2.3 fixture (lock). |
| 32 KEEP | `test_methods_assembly_v8.py::test_v8_planted_range_error_fails` (`:104`) | 7.97 | V8 planted range error on a 1080x1920 crop (`:36`) | Already 1080p. |
| 33 KEEP | `test_noise_experiments.py::test_the_runner_records_one_deep_frame_under_two_settings` (`:553`) | 7.90 | one 4K footage frame (`:561`) | One frame; 4K is asserted (`:565`). |
| 34 KEEP | `test_methods_assembly_v8.py::test_v8_preview_against_the_downscaled_export[GX011625_0114.648-c3-cpu]` (`:89`) | 7.84 | V8 on a 1080x1920 crop | Already 1080p. |
| 35 KEEP | same `[GX011625_0024.925-c3-cpu]` | 7.80 | as 34 | as 34. |
| 36 KEEP | `test_methods_assembly.py::test_gpu_reads_only_at_the_counted_points_...[c3]` (`:786`) | 6.97 | host-read count, 64x96 (`:792`) | Minimal already. |
| 37 KEEP | `test_prototype_temporal.py::test_7_the_runner_on_ten_frames_writes_its_record` (`:861`) | 6.79 | WP1.4 excerpt of 10 footage frames | Small; tool-set excerpt. |
| 38 KEEP | `test_prototype_backend.py::test_gpu_output_agrees_with_cpu[size2-c3]` (`:189`) | 6.58 | GPU/CPU agreement at 1024x1536 | The 1024 px size is the subject. |

## Trim construction and checks

`work/wp-t6/w1/01-packets.json` records N=90, cut T=3.003000 s and keyframe
spacing 30 frames. N exceeds the required lead-plus-five floor of 66. The
packet listing uses decode order and chooses the first keyframe with PTS at
least three seconds. The session trim lives only under the pytest temp root;
both the root and trim folder are checked against the configured read-only
footage folder, and teardown removes the trim folder even after failed setup.
Lookup skips only an absent clip after a successful folder search; ambiguity,
a missing folder and an unsearchable folder raise. For decode R5-R7 this
intentionally tightens the old locator: a walk error now raises rather than
skips, as the brief's step 1 and DR-27 (1) require (F6).

The command is fixed by the brief plus CHARC R-b's sole added metadata flag
(`tests/conftest.py`, `gx011627_trim_plan`; rulings in the ledger). Symbolic
input/output names below do not denote a footage path:

```text
ffmpeg -nostdin -hide_banner -v error -y -i <source>
  -map 0:v:0 <one -map 0:i for each audio and non-tmcd data stream>
  -c copy -map_metadata 0 -map_metadata:s:v:0 0:s:v:0
  -write_tmcd 1 -video_track_timescale <source-time-base-denominator>
  -frames:v N -t T -movflags use_metadata_tags -f mp4 <trim>
```

No `gpmd` decode occurs. The copy proof covers **video and data packets**;
audio packet fidelity to the original is not checked (F1). Audio checks cover
roster, sample rate, channels and tags. Packet comparisons operate in memory;
no digest is retained in report artifacts.
`work/wp-t6/w1/02-trim-checks.json` records every
check PASS and the stream roster: video HEVC/`hvc1`, audio AAC/`mp4a`, data
`tmcd` and data `gpmd`. The two data tracks change muxer order, so R-a pairs
streams by `(codec_type, codec_tag_string)` and ordinal within each key,
after comparing counts. The checker returns named failures on mismatched
groups instead of raising before the packet checks.

| Check | Guarded property | Result |
|---|---|---|
| 4(a) | N >= 66 | PASS |
| 4(b) | Video packet count equals N **and** first N packet tuples agree in decode order by PTS, duration, size, flags and MD5 | PASS; count and packet clauses are separate named sub-results in the checker |
| 4(c) | Time base 1/30000 and sorted PTS exactly `[k * 1001 for k in range(N)]`; cleanup also requires the source packet at N to carry `K` and have PTS equal to planned T | Original PTS check PASS in W1/W2; W2b parity PASS and N=75 `4c_cut_on_keyframe` FAIL, caught (F3; `work/wp-t6/w2b/01-trim.log`, `03-non_keyframe.json`) |
| 4(d) | Same roster multiset and paired video size/pixel format/colour/rotation, audio sample rate/channels, `gpmd`/`tmcd` presence | PASS under R-a's pairing |
| 4(e) | Filtered tag dictionaries agree under scoped R-c exceptions and R-e's semantic rule; location-like keys agree in presence | PASS |
| Data packets | Copied packet prefix agrees without decoding; cleanup also requires its count to equal source packets with PTS strictly before T | Original prefix check PASS: three trim `gpmd` packets from 23 source packets; W2b parity PASS, truncated-data count FAIL with prefix PASS, caught (F2; `work/wp-t6/w2b/03-truncated_data.json`) |

The fixture asserts all five checks and copied data equality before any
consumer runs; the dedicated parity test repeats these named assertions.
On pairing failure the checker marks tag/data comparisons FAIL while still
returning the packet-count, packet-equality and PTS results.
The fixture passes its planned T into the cleaned checker; three-argument
callers derive T independently as the first source keyframe at or after
three seconds. The cut result is conjoined into 4(c). Data records expose
the expected count before T, count equality and packet equality separately;
the existing data assertion requires their conjunction. These cleanup changes
are proved synthetically in `work/wp-t6/rA1-cleanup-synthetic.log` and now
re-proved by the positive parity pass and four caught real controls under
`work/wp-t6/w2b/`; the cumulative ledger records their verified checksums.

Scoped `ALLOWED_TAG_DIFFS` is format {`major_brand`, `minor_version`,
`compatible_brands`, `encoder`}; all streams {`handler_name`, `language`};
audio only {`timecode`}. These are muxer-written differences accepted by R-c.
Format `creation_time` is checked semantically under R-e, not unconditionally
allow-listed: splitting on `;` must produce at least one part and every part
must equal the source. W1 records two equal parts. `firmware` survives with
R-b's metadata flag and needs no exception. Location-like values are removed
before comparisons and diagnostics; only key presence is checked. Source:
`work/wp-t6/w1/02-trim-checks.json` and the two CHARC W1 rulings in the ledger.

## R2 -- measured level and size chain

W1's complete 90-frame trim was encoded at each quality, taking 76.565051 s
in total (`work/wp-t6/w1/03-levels.json`):

| Quality | Bytes | HEVC level |
|---|---:|---|
| high | 27,731,069 | 5.2 Main |
| standard | 13,720,197 | 5.1 Main |
| draft | 6,639,630 | 5.0 Main |

High/standard = 2.021186 and standard/draft = 2.066410, both strictly above
1.25. The standard encode wrote 90 frames; its proof was tied with 123 samples.
No separate per-quality timings were measured in W1. The original level and
size-chain assertions passed again in W3 and in W4's full form.

## R4 -- count selection and defect margins

The unchanged bounds are mean <= 1.0 (1/255 units) and share-over-two <= 0.01
(a proportion). Each plant must exceed at least one. All base/plant verdicts
pass at each measured count. Sources: `work/wp-t6/w1/04-first6.json`,
`04-first10.json`, `04-first15.json`, `04-first30.json` and
`04-comparisons.json`. Each cell below is **mean / share-over-two**.

| Measurement | 6 frames | 10 frames | 15 frames | 30 frames |
|---|---:|---:|---:|---:|
| base | 0.684298522 / 0.007303268 | 0.686187249 / 0.007285365 | 0.686520087 / 0.007173375 | 0.686802822 / 0.007224387 |
| encode range | 5.108201094 / 0.715041460 | 5.175708110 / 0.718372553 | 5.240621190 / 0.722326228 | 5.323826024 / 0.729845802 |
| encode matrix | 3.111772140 / 0.597846894 | 3.112489960 / 0.598669938 | 3.085336020 / 0.593441658 | 2.980265734 / 0.570920048 |
| accurate_rnd dropped in both halves | 1.131466726 / 0.069446286 | 1.133656649 / 0.070869888 | 1.136330711 / 0.072099449 | 1.141306802 / 0.073483034 |
| accurate_rnd dropped in the first decode | 0.780798183 / 0.037213441 | 0.786798117 / 0.038437588 | 0.790510147 / 0.039390687 | 0.795794250 / 0.040655778 |
| siting center | 0.698592457 / 0.015481804 | 0.702162671 / 0.015952940 | 0.703927469 / 0.016273116 | 0.705520643 / 0.016681069 |
| siting topleft | 0.727749425 / 0.019787849 | 0.731071216 / 0.020171545 | 0.732518623 / 0.020433859 | 0.734738300 / 0.021094204 |

The base at six versus 30 is shown side by side above: its share headroom at
six is about 27%; the 30-frame base is similarly close to that bound. The
wall measurements include the base and all six plants:

| Frames | Wall seconds | Saving vs 30, seconds | Base / all plant verdicts |
|---|---:|---:|---|
| 6 | 35.772337 | 124.694986 | PASS / all PASS |
| 10 | 56.486785 | 103.980537 | PASS / all PASS |
| 15 | 84.478559 | 75.988763 | PASS / all PASS |
| 30 | 160.467322 | 0.000000 | PASS / all PASS |

Six is the smallest candidate in {6, 10, 15}; it saves 124.694986 s against
the within-window 30-frame run, exceeding the required 30 s. Every positive
30-frame plant margin retains at least half at six (all nine applicable
comparisons). Signed margins, figure minus bound, are:

| Plant | Mean margin at 6 | Mean margin at 30 | Share margin at 6 | Share margin at 30 | Half-margin check |
|---|---:|---:|---:|---:|---|
| encode range | 4.108201094 | 4.323826024 | 0.705041460 | 0.719845802 | Both PASS |
| encode matrix | 2.111772140 | 1.980265734 | 0.587846894 | 0.560920048 | Both PASS |
| accurate_rnd dropped in both halves | 0.131466726 | 0.141306802 | 0.059446286 | 0.063483034 | Both PASS |
| accurate_rnd dropped in the first decode | -0.219201817 | -0.204205750 | 0.027213441 | 0.030655778 | Share PASS; mean not applicable |
| siting center | -0.301407543 | -0.294479357 | 0.005481804 | 0.006681069 | Share PASS; mean not applicable |
| siting topleft | -0.272250575 | -0.265261700 | 0.009787849 | 0.011094204 | Share PASS; mean not applicable |

Negative mean margins on the first-decode and siting plants were not half-margin
tests: those plants exceed the share bound at both six and 30. The same
applicable-margin checks pass at 10 and 15. The selected six-frame form keeps
the bounds and every assertion from the 30-frame form. FFmpeg's bit-exact
filters make these verdicts deterministic in the declared envelope
(`tests/test_color_roundtrip.py`, bounds comment); this does not claim
portability to an untested FFmpeg build.

## Row 10 -- profile and banked lever

The unchanged two-frame GPU-memory test was profiled once. The enclosing
command exited zero in 80.873235 s; pytest reported one pass in 79.54 s
(`work/wp-t6/w1/05-result.json`). The profile covers 80.481 s; its top block
is pytest/runpy wrappers. The bench-specific block from the same profile
names `bench.main` at 78.325 s, four calls to
`tools/prototype/bench.py:1305` `stray_processes` at 59.501 s cumulative, and
`stop` at 16.303 s (`work/wp-t6/w1/05-profile-top15.txt`). Cumulative times
overlap and must not be summed.

The ledger's inspected-code diagnosis is repeated whole-system process CPU
sampling plus sampler shutdown/final sampling. The cost is not governed by
this test's frame count. No deeper profile, proposed fix or tools edit is
claimed. The lever is BANKED for an owner-triggered follow-on; the original
unprofiled baseline time remains the map's timing source.

## W2-W4 evidence, controls and deviations

| Window | Outcome | Evidence |
|---|---|---|
| W2 run 1 | Parity passed; guard stopped on two strict-marker failures; marker registered early | `docs/proofs/wp-t6-ledger.md`, W2 run-1 facts / seat-2 turn 1 |
| W2 run 2 | Parity 1 passed in 3.63 s; guard 60 passed in 41.20 s; controls STOPPED: pairing assertion prevented re-encode result; N+1 alone was masked | `work/wp-t6/w2-run2/`, recorded in ledger; resolved by CHARC controls ruling |
| W2 run 3 | Parity 1 passed in 3.57 s; guard 60 passed in 41.55 s; both controls caught; W2 DONE EXIT 0; scratch/trim cleanup clean | `work/wp-t6/w2/01-trim.log`, `02-guard.log`, `03-reencode.json`, `03-extra_frame.json`, `04-cleanup.json`; ledger W2 DONE |
| W2b, R1 cleanup re-proof | Parity 1 passed in 3.29 s; guard 60 passed in 41.67 s; all four controls caught; W2b DONE EXIT 0; scratch and both basetemps removed | `work/wp-t6/w2b/01-trim.log`, `02-guard.log`, four `03-*.json` control records, `04-cleanup.json` |
| W3 run 1 | Eight passed in 322.26 s; V4 comparison stopped on dispatcher reference-path slip, before controls | `work/wp-t6/w3-run1/`; ledger reference-path correction |
| W3 run 2 | Eight passed in 258.91 s; one standard encode, one engine record, MANDATORY/REQUIRED and roster SAME; branch (i), both controls caught; W3 DONE EXIT 0 | `work/wp-t6/w3/01-serial.log`, `01-serial.json`, `02-engine-v4-names.json`, `03-v4-delta.json`, control JSON and `06-cleanup.json` |
| W4 | Seven passed, 6,450 deselected in 1,556.05 s; W4 DONE EXIT 0; full sink both count operands 681; zero trim setups; cleanup clean | `work/wp-t6/w4/01-fullclip.log`, `02-fullclip-check.json`, `03-cleanup.json`, `w4-fullclip.xml` |

The ledger records each window's start/end, command, free memory and EXIT;
successful windows ran alone at the seat with the required memory floor.
W4 started 13:06:46.706213Z with 11,047,211,008 available bytes and finished
cleanup at 13:32:45.218973Z (`work/wp-t6/w4/00-window.json`, `03-cleanup.json`).

The final controls and rejection sites are:

| Control | Rejection / evidence |
|---|---|
| Re-encode trim | 4(b) FAIL: count PASS, packets FAIL; 4(d)/4(e) FAIL. Video codec groups `hvc1` and `hev1` differ; checker returns rather than raising. W2b repeats these results; cut sub-result PASS, data verdict FAIL through pairing mismatch. `work/wp-t6/w2/03-reencode.json`, `work/wp-t6/w2b/03-reencode.json` |
| Late cut plan | Both `-frames:v 91` and `-t` one frame later; 4(b) FAIL: count FAIL, first-N packets PASS; 4(c) FAIL; 4(d)/4(e) PASS. W2b repeats these results; cut sub-result and data count PASS. `work/wp-t6/w2/03-extra_frame.json`, `work/wp-t6/w2b/03-extra_frame.json` |
| Non-keyframe plan | W2b N=75: 4(c) and `4c_cut_on_keyframe` FAIL; video count/packets PASS; data count also FAIL; caught by the required F3 sub-result. `work/wp-t6/w2b/03-non_keyframe.json` |
| Truncated data | W2b 1 copied packet versus 3 expected before T: count FAIL, prefix PASS, `equal=false`; all 4(a)-(e) PASS and `failed_checks=[]`, but the fixture's separate `data_packet_checks[*].equal` assertion rejects it, as adjudicated for F2. `work/wp-t6/w2b/03-truncated_data.json` |
| Draft yielded as standard | Levels `[trim]` fails `level is not None and level.name == expected[quality]`; expected pytest EXIT 1, control verified | `work/wp-t6/w3/04-draft-control.json` |
| Reference shortened | R5 `[trim]` fails `len(footage_reference) == footage_frames`, 90 -> 89; expected pytest EXIT 1, control verified | `work/wp-t6/w3/05-reference-control.json` |

W3 planted controls used runtime fixture substitution, with no tracked-code
mutation. Cleanup proves test byte hashes unchanged, empty test status and
`git diff --quiet` (`work/wp-t6/w3/06-cleanup.json`). W2 scratch controls were
deleted; W4 removed its observer scratch and basetemp. All retain only logs,
JSON/XML and counts, with no trim or other media left. No planted code is
committed. Stops were findings and authorized adjustments, not successful
controls; only the final caught controls above count as proof.

## Collections -- rung 4 CLOSED

Seat collection on pytest 8.4.2 passed, EXIT 0, at 13:06:30.821536Z
(`work/wp-t6/cand-collection-summary.json`; node-ID-only sets are
`cand-all.txt`, `cand-parallel.txt`, `cand-serial.txt`, `cand-fullclip.txt`).
Counts: all 6,457; parallel 5,313; serial 1,137; fullclip seven.
There are no duplicates; all three selected sets are pairwise disjoint and
**parallel + serial + fullclip = all**.

Against `base-*.txt`, ALL removes exactly the seven unsuffixed CUT IDs and
adds their fourteen suffixed forms plus the new parity node. SERIAL removes
the same seven and adds the seven `[trim]`/`[first6]` gate forms plus parity.
PARALLEL is unchanged. FULLCLIP is exactly R1-R3 and R5-R7 `[full]` plus R4
`[first30]`. This verifies fixture-parameter marks on the recorded pytest
version, including module-scoped decode fixtures depending on the session
parameter. The collection proof, rather than a count prediction, establishes
that no test was lost or accidentally assigned to both legs.
Session parametrisation also regroups the serial items: the trim block now
runs at the decode module's position, before the rest of encode/jobs. Gate
KEEP-row timing comparisons must account for changed warm-up/state order (F4;
`work/wp-t6/rA1/review-r1.txt`), which W3's restricted run did not exercise.

## Limits

- The trim covers only its first N=90 frames. Whole-clip behaviour is proved
  by the fullclip window, not extrapolated from the trim.
- Audio `timecode` does not survive the copy (R-c). Real-container handler
  names and audio timecode are exercised by the full forms; the trim's V4
  export compares against its own FFmpeg-muxed source container.
- The V4 comparison has exactly six best-effort delta names, listed below.
  No MANDATORY or REQUIRED differences occur on either side. These differences
  do not weaken R1's assertions, which cover MANDATORY and REQUIRED.
- `-frames:v N+1` alone is masked by `-t T` (the belt working, not a defect).
  The successful late-cut control moves both cut-plan flags one frame late.
- The function-local `from conftest import ...` in the parity test relies on
  pytest's default import mode. Reviewer A's `--import-mode=importlib` probe
  fails earlier while loading the existing `fixture_plugin`, before the parity
  import is reached; that mode is outside this package's envelope (F8).
- On the trim, R5's 1/30000 time base follows the fixture's explicit track
  timescale flag and 4(c); only `[full]` retains proof of the camera container's
  original time base (F10).
- The fixture checks its plan's own T, so a later keyframe plan (N=120, T=4.004) passes every fixture-path check; the parity test omits T, independently re-derives it and fails that plan in the same serial leg, so the gate still goes red (B1; CHARC `7c59772d`; DR trigger: next touch of the `gx011627` fixture).
- The declared seat has one GPU, serial non-xdist execution, the pinned
  FFmpeg build and a configured clip. A missing clip skips; no skip substitutes
  for these positive proofs. Fixture sessions are per worker, so serial and
  fullclip expressions must never run under `-n`. No reordering plugin is
  covered. Runs without the prescribed `--basetemp` may use OS temp; teardown
  still removes the trim, but that use lies outside these window figures.

The V4 item-name delta is from `work/wp-t6/w3/03-v4-delta.json` and CHARC
ruling `c80aacc9844cd837` (verbatim in the ledger):

| Side only | Best-effort difference item name | Ruled explanation |
|---|---|---|
| trim | `creation time: container tag` | R-e two-part `creation_time` is written back by export as one value |
| trim | `creation time: mvhd (seconds since 1904)` | Same R-e representation reason |
| trim | `creation time: per-stream tags` | Same R-e representation reason |
| full | `edit lists as written, non-video tracks (media_time in media seconds)` | Fewer differences against the FFmpeg-muxed trim container |
| full | `timecode value (stream tags)` | Trim has no audio `timecode` (R-c) |
| full | `track layout (key:sample entry:tkhd flags)` | Fewer differences against the FFmpeg-muxed trim container |

The five other best-effort difference names are common to both records;
there is no unexplained name. Branch (i) proceeds under the ruling. In the
required accept wording: **the trim form proves V4 MANDATORY and REQUIRED; three best-effort container items are proved by the fullclip form only**.
W4 has now exercised that full form; future package/phase windows must retain
it. This does not claim the three full-only best-effort items are SAME.

## For CHARC

At accept, update the review/gate fill and `CLAUDE.md` test-conventions
paragraph to record `fullclip`, the following expressions and collection
identity, the measured gate counts/times below, and the policy that
FULLCLIP runs at least once per phase-end gate report and whenever a package
brief asks. AD-28's leg figures must use the final gate's observed parallel
and serial walls and counts, with the baseline/AFTER comparison below. These
documents and the decision register are CHARC-owned and were not edited here.
GATE_CHECKS collection identity: **parallel + serial + fullclip = all**.

Run in Git Bash with `PYTEST_ADDOPTS` unset, headless Qt and fresh basetemps
under `work/`. SERIAL and FULLCLIP have no `-n`:

```bash
uv run pytest -q -rs -n 4 -m "not gpu and not footage and not gui and not slow and not fullclip" --basetemp=work/wp-t6/gate-parallel
uv run pytest -q -rs -m "(gpu or footage or gui or slow) and not fullclip" --basetemp=work/wp-t6/gate-serial --durations=0 --junitxml=work/wp-t6/gate-serial.xml
uv run pytest -q -rs -m "fullclip" --basetemp=work/wp-t6/phase-fullclip --durations=0
```

Banked owner-triggered follow-on candidates, from the brief's Q7 and W1's
profile: the fixed sampling cost at `tools/prototype/bench.py:1305`
`stray_processes`; the 5.3K CPU export (about 121 s, locked T5-Q3 form);
prototype bench rows 9-11 (about 163 s); V3/AD-14 (about 81 s, lead-bound);
and the remaining-test tail (about 394 s). These historical rounded figures
come from the brief's map and Q7, not an additive prediction of recoverable
time. The gap to 900 s lies outside the current sizing envelope and locks.
Also carry DR-22/DR-66 consumer notes for additive conftest use, the scoped
tag exceptions and six-item Limit, plus the fullclip-per-phase-gate sentence.
CHARC also writes B1's DR row, triggered by the next touch of `gx011627`;
the Limit above is accepted without a code change in this package.

## AFTER (the gate) -- GREEN; Q6 PASS

This is the final candidate's ONE gate after Reviewer A convergence and
Reviewer B. W3 and W4 are separate development/full-form evidence. Sources
are the copied `work/wp-t6/gate-g1/` records; all 13 entries in `md5sums.txt`
were independently verified (`work/wp-t6/gate-g1-analysis.json`).

| Final-gate field | Observed result / source |
|---|---|
| Candidate and integration | `a4472fbe485a306f09cbd7750d98f9e193299ed5` in `wp-t6-mc`; dispatcher records 21 commits rebased from `e2dc969` onto main `5fdcda4`, matching patch-id prefix `a7a7d115` on both sides; `progress.log` records candidate HEAD |
| Seat conditions / config / start-end | Dispatcher seat, Git Bash, headless Qt, `PYTEST_ADDOPTS` unset, fresh work basetemps. Gate 14:43:42Z-15:23:27Z; serial held until the only other cell was verified idle. Candidate and main local configurations are byte-identical in a post-gate check at 15:28:25Z (`work/wp-t6/gate-g1-config-identity.json`); no configuration values retained |
| Free memory before each leg | Parallel 9,086,959,616 bytes; serial 9,663,655,936 bytes, both above floor (`mem.log`) |
| Static checks | Ruff PASS; format check: 267 files already formatted; mypy: no issues in 141 source files; all EXIT 0 (`ruff.log`, `format.log`, `mypy.log`) |
| Collections | 6,457 = 5,313 parallel + 1,137 serial + 7 fullclip; no duplicates, pairwise disjoint, union all, every collection EXIT 0. Against main's 6,449/base set, exactly seven unsuffixed CUT IDs removed, fifteen added (split forms and parity); `collect-*.txt`, independent set proof in `gate-g1-analysis.json` |
| PARALLEL | 5,312 passed, one skip (`test_color_roundtrip.py:123`), EXIT 0, 714.41 s. Process interval 14:44:08Z-14:56:04Z (`parallel.log`, `progress.log`) |
| SERIAL -- AFTER | 1,136 passed, one standing photo skip (`test_photo_check.py:139`), 5,320 deselected, EXIT 0, **1,389.24 s**. JUnit suite 1,389.176 s (1,389.18 rounded); interval 15:00:16Z-15:23:27Z, alone (`serial.log`, `serial.xml`, `progress.log`) |
| Seven CUT sum | **281.236 s** JUnit setup+call+teardown; rounded log setup+call sum 280.65 s, teardown sum 0.58 s; detailed reconciliation below |
| Leg wall reduction | 2,621.32 -> 1,389.24 s: **1,232.08 s (47.00%)** shorter; reported alongside the per-test verdict, not used alone |
| KEEP rows | All 31 matched, none missing; setup+call 659.54 -> 687.85 s, aggregate +28.31 s; individual deltas -1.81 to +8.80 s, median +0.34 s; table below |
| Q6 verdict | **PASS**: 1,567.37 - 281.236 = **1,286.134 s** conservative seven-CUT reduction (82.06%), strictly more than 110 s. AFTER includes teardown and new shared trim setup, so neither can inflate this saving |
| 900 s target | Not reached: AFTER is 489.24 s above target. Informational under Q7, not an acceptance failure |
| Reviews | A R1: zero critical/major, three minor, eight advisory; single result-bearing cleanup re-proved in W2b, converged, no R2. B: zero critical/major, one minor, nine advisory; returned, all dispositions ruled by CHARC `7c59772d`; details below |

### Seven CUT bodies and timing-category reconciliation

The BEFORE map is setup+call; JUnit's per-test `time` is setup+call+teardown.
Each row below is keyed to the CUT map above. Rounded phase times come from
`work/wp-t6/gate-g1/serial.log`, JUnit totals from `serial.xml`; not-listed
phases are below the display threshold, not asserted zero.

| CUT | BEFORE setup+call | AFTER setup | AFTER call | AFTER teardown | AFTER JUnit total |
|---|---:|---:|---:|---:|---:|
| R1 | 456.31 | Not listed | 88.42 | 0.08 | 88.511 |
| R2 | 330.02 | Not listed | 54.14 | 0.08 | 54.223 |
| R3 | 221.69 | 27.47 | 11.90 | 0.07 | 39.440 |
| R4 | 169.97 | 0.01 | 41.28 | Not listed | 41.292 |
| R5 | 152.09 | 10.77 | 14.35 | 0.11 | 25.220 |
| R6 | 131.88 | Not listed | 17.98 | 0.15 | 18.127 |
| R7 | 105.41 | Not listed | 14.33 | 0.09 | 14.423 |
| Total | 1,567.37 | Included once | Included once | 0.58 displayed | **281.236** |

The seven JUnit totals sum to **281.236 s**. Displayed setup+call sums to
280.65 s and teardown to 0.58 s; their 281.23 s total differs by 0.006 s from
JUnit because of rounding and undisplayed small phases. A matched displayed
setup+call comparison gives 1,286.72 s saved. Q6 instead uses the conservative
JUnit reduction of 1,286.134 s, counting teardown in AFTER only. Both exceed
110 s by a wide margin; millisecond precision is not claimed for the rounded
historical map.

R5's 10.77 s setup carries the shared trim construction/checks and independent
`footage_reference`; the log cannot split those internal fixture costs. R3's
27.47 s setup carries `gx011627_standard_encode` and other fixture work. Both
are included once in the seven-row sum. Their baseline setup charges were
43.52 s and 171.57 s respectively (brief's map). The new parity node adds
1.388 s JUnit (call 1.30 s, displayed teardown 0.09 s); including it gives
282.624 s and still saves 1,284.746 s against the old seven tests. No shared
setup is subtracted or charged twice to improve the verdict. The gate's
broader item order differs from the baseline as disclosed under F4.

### KEEP comparison and noise estimate

Row numbers refer to the unchanged KEEP map above. All 31 actual gate node
IDs matched, including expansion of the brief's abbreviated names; none are
missing. BEFORE and AFTER below are setup+call seconds, with AFTER from the
rounded duration log; the analysis record retains each full node ID and its
JUnit total. No KEEP assertion or size changed.

| KEEP row | BEFORE setup+call | AFTER setup+call | Delta (s) |
|---|---:|---:|---:|
| 8 | 121.45 | 130.25 | +8.80 |
| 9 | 66.12 | 67.10 | +0.98 |
| 10 | 63.67 | 62.94 | -0.73 |
| 11 | 33.17 | 39.38 | +6.21 |
| 12 | 28.45 | 27.43 | -1.02 |
| 13 | 27.48 | 27.40 | -0.08 |
| 14 | 26.98 | 27.65 | +0.67 |
| 15 | 26.89 | 26.67 | -0.22 |
| 16 | 22.58 | 24.15 | +1.57 |
| 17 | 19.64 | 20.02 | +0.38 |
| 18 | 19.57 | 17.76 | -1.81 |
| 19 | 18.76 | 20.60 | +1.84 |
| 20 | 18.41 | 22.40 | +3.99 |
| 21 | 12.56 | 12.76 | +0.20 |
| 22 | 12.15 | 12.38 | +0.23 |
| 23 | 11.84 | 12.28 | +0.44 |
| 24 | 11.76 | 12.08 | +0.32 |
| 25 | 10.31 | 10.61 | +0.30 |
| 26 | 10.02 | 10.02 | +0.00 |
| 27 | 9.83 | 10.51 | +0.68 |
| 28 | 9.70 | 10.91 | +1.21 |
| 29 | 9.17 | 10.30 | +1.13 |
| 30 | 9.07 | 9.72 | +0.65 |
| 31 | 8.11 | 8.25 | +0.14 |
| 32 | 7.97 | 8.95 | +0.98 |
| 33 | 7.90 | 8.24 | +0.34 |
| 34 | 7.84 | 8.12 | +0.28 |
| 35 | 7.80 | 8.18 | +0.38 |
| 36 | 6.97 | 7.04 | +0.07 |
| 37 | 6.79 | 6.98 | +0.19 |
| 38 | 6.58 | 6.77 | +0.19 |
| Total | **659.54** | **687.85** | **+28.31** |

The KEEP sum is 659.54 -> 687.85 s (+28.31 s); its JUnit total including
teardown is 690.850 s, so that total is not used for the matched KEEP spread.
The range -1.81 to +8.80 s and median +0.34 s describe this gate's observed
variation, not a causal attribution or confidence interval. Fixture grouping,
warm-up/state and host variation can contribute. This noise is much smaller
than the seven-CUT reduction; the older host-spread indicator remains about
316 s between legs, with 43.58 s for the engine pair. The non-CUT tail and
runner/teardown overhead also affect leg wall, so leg-wall and CUT-sum savings
need not agree. Sources: baseline map in the brief, `serial.log`, `serial.xml`,
`work/wp-t6/gate-g1-analysis.json`.

### Reviewer B and final handoff

The dispatcher ran the Claude process `claude-opus-5-5`/high on `a4472fb`:
model assertion passed, `is_error=false`, 36 turns, worktree clean afterward;
eight sandbox permission denials, none a withheld-path access. Verdict:
`NO_NEW_CRITICAL_MAJOR`, one minor and nine advisory. Full review text was
not handed to the cell; the binding findings and dispositions are the
dispatcher's quoted CHARC ruling `7c59772d`, recorded in the ledger.

| Review | Ruled disposition |
|---|---|
| B | B1 REPORT-ONLY: exact later-keyframe Limit above, DR at next fixture touch; B2 and B9 REPORT-ONLY (already covered by F2 or minor per ruling); B3 FIX: historical maximum is 43.58 s; B4 DECLINED: descriptive docstring text, assertion retained; B5-B8 out of envelope or already-stated Limits, no implementation change; B10 sandbox guard run unavailable, W2b's 60 passes stand |

Dispatcher evidence: `clearwater-review-evidence/wp-t6/reviewB/`; supplied
MD5 prefixes review `ff96cce0`, prompt `92d44bf8`, diff `953355a8`. Gate
checksums are in `work/wp-t6/gate-g1/md5sums.txt`; the serial XML/log and
parallel log verified respectively as prefixes `5b88c916`, `9142b765`,
`f080acfa`. Final docs-only whitespace/scope checks are in the ledger.
The work package is ready for CHARC's accept actions; acceptance itself
remains pending.
