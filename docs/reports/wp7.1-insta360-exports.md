# WP7.1: Insta360 Studio exports, 2026-11-09

**Result: HEVC inputs accepted; D/E throughput at N6; V4 FAIL. Acceptance is pending.**
The product finding is exact end-of-track preservation, with movie-level interpretation
held for the owner. The look verdict is also pending. This report does not turn the
ruled admission of failed outputs into a V4 pass.

Evidence paths below are relative to the WP7.1 worktree unless absolute. `R/` means
`work/wp7.1/records/`; `P/` means `work/wp7.1/probe/`; `DEC/` means `work/wp7.1/decode/`.
`W1` and `W2` mean the seat logs at
`C:/Users/rwsmy/clearwater-review-evidence/wp7.1/seat/window1/window1.log` and
`C:/Users/rwsmy/clearwater-review-evidence/wp7.1/seat/window2/window2.log`.
Seat-log line numbers use LF-delimited lines, as `rg -n` reports them; embedded CR
continuations in process lists do not advance that numbering. GB means decimal bytes;
MiB/GiB are binary units. Rounded table values retain exact values in the cited JSON.

## 1. Scope and inputs

Scope is HEVC-only under CHARC's correction `626e30f0`. Spec 5.2 admits HEVC/H.264;
ProRes is refused. The MOVs are independent plain-FFmpeg decode references only.
The extra `SCUBA vids.mp4` is inventory/probe-only. No product, tool, test or
dependency was changed by WP7.1. Sources were read in place from the configured
footage root; outputs, caches and evidence are under `work/wp7.1/`.

The inventory refresh is [inventory-2026-11-09.md](inventory-2026-11-09.md), sections
2 and 11: seven Insta360 videos, 224,253,936,407 bytes; total inventory 135 rows
(62 videos, 73 photos), zero error rows. Historical non-Insta360 aggregates match;
historical payload identity is not claimed.

| File | Bytes | Video duration s | Raw codec / pixel format | Evidence |
|---|---:|---:|---|---|
| `SCUBA vids 2.mov` | 4,147,033,418 | 61.795067 | ProRes Standard / yuv422p10le | `P/0.json`, `raw` |
| `SCUBA vids2.mp4` | 567,779,287 | 61.795133 | HEVC Main / yuvj420p | `P/1.json`, `raw` |
| `SCUBA vids 3.mov` | 28,688,898,652 | 438.905133 | ProRes Standard / yuv422p10le | `P/2.json`, `raw` |
| `SCUBA vids 3.mp4` | 3,902,405,419 | 438.905567 | HEVC Main / yuvj420p | `P/3.json`, `raw` |
| `SCUBA vids(1).mov` | 152,128,238,670 | 2259.223633 | ProRes Standard / yuv422p10le | `P/4.json`, `raw` |
| `SCUBA vids(1).mp4` | 20,658,042,496 | 2259.225900 | HEVC Main / yuv420p | `P/5.json`, `raw` |
| `SCUBA vids.mp4` | 14,161,538,465 | 2259.225900 | HEVC Main / yuv420p | `P/6.json`, `raw` |

Durations above are `duration_ts * time_base`, not rounded container durations.
Owner Q1 answers, recorded in the final dispatch brief: H.265 export near 71-73 Mbps;
ProRes offered no bitrate control; stabilization ON for all; recording mode "HDR video";
colour profile unknown. Probe video rates are 73.37 / 71.00 / 73.01 Mbps for the main
MP4s, 50.01 Mbps for the extra MP4 (`P/1,3,5,6.json`, raw video `bit_rate`).
The camera-mode name does not override the exported BT.709 tags.

Limits are one camera, three videos, and the owner's chosen Studio export settings.
There is no native `.insv`, 360/equirectangular, ProRes input-support or ProRes-output
validation. Footage category is SCUBA, supplied by the owner.

## 2. Probe, SDR consistency and decode agreement

All raw video headers are 3840x2160, nominal 30000/1001 fps, BT.709
primaries/transfer/matrix, with AAC audio and no data track (`P/0.json` through
`P/6.json`). Product-accepted MP4s have no faults and are marked VFR by the product;
the inventory's nominal-rate heuristic is not the timing authority.

| File | Product result | Raw range -> product range | Chosen decode path | Evidence |
|---|---|---|---|---|
| `SCUBA vids 2.mov` | Refused, `unsupported` | tv -> unresolved | None | `P/0.json` |
| `SCUBA vids2.mp4` | Accepted | pc -> full | Software FrameStream checked | `P/1.json`; `DEC/short-first.json` |
| `SCUBA vids 3.mov` | Refused, `unsupported` | tv -> unresolved | None | `P/2.json` |
| `SCUBA vids 3.mp4` | Accepted | pc -> full | Software FrameStream checked | `P/3.json`; `DEC/medium-first.json` |
| `SCUBA vids(1).mov` | Refused, `unsupported` | tv -> unresolved | None | `P/4.json` |
| `SCUBA vids(1).mp4` | Accepted | tv -> limited | CUDA RGB pipe checked, C3 | `P/5.json`; `R/decode-hevc2259-prefix.json` |
| `SCUBA vids.mp4` | Accepted, probe-only | tv -> limited | Command recorded, not exercised | `P/6.json` |

The refusal messages are verbatim:

- `SCUBA vids 2.mov uses the codec prores; H.265 and H.264 only.` (`P/0.json`)
- `SCUBA vids 3.mov uses the codec prores; H.265 and H.264 only.` (`P/2.json`)
- `SCUBA vids(1).mov uses the codec prores; H.265 and H.264 only.` (`P/4.json`)

The selected-frame checks use the product's software HEVC decode to float32 RGB,
against plain FFmpeg's ProRes-to-RGB reference; no product admission was bypassed.
Values below are normalized RGB, R / G / B. There is **no numerical pass band**.

| Selection | MAE | p99 absolute | Maximum absolute | Evidence |
|---|---|---|---|---|
| Short, first frame | .004392 / .003604 / .005119 | .016083 / .012634 / .017975 | .057313 / .037964 / .076127 | `DEC/short-first.json`, `agreement` |
| Short, nearest 30 s | .004538 / .003385 / .005211 | .016220 / .011765 / .018235 | .053590 / .047974 / .066270 | `DEC/short-30s.json`, `agreement` |
| Medium, first frame | .004545 / .003706 / .004899 | .015442 / .012161 / .016480 | .040436 / .037461 / .092470 | `DEC/medium-first.json`, `agreement` |

First-frame PTS is zero in both pairs. Near 30 s, HEVC is `899900/30000`, ProRes
`899899/30000`; independent packet enumeration selects ordinal 899 in both
1,852-frame sources. Roster offsets span zero to two ticks, retained without
interpolation (`DEC/short-30s.json`, `alignment`; `DEC/alignment-check.json`).

Independent same-HEVC controls agree exactly at all selections: channel MAE/p99/max
zero, luma slope 1 / intercept 0, shape `(2160,3840,3)`, residual parity and adjacent
change zero. ProRes-reference luma slopes are 1.003865 / 1.003870 / 1.002954,
with intercepts .000070 / -.000023 / .000516, respectively (the three selection
records, `same_hevc_control_metrics` and `agreement`). These independent controls
found no sampled range-double-expansion or missing-upsampling signature; normal
codec/chroma differences are not classified as a defect from their magnitude alone.

The brightest of the required samples is short-near-30 s, selected by RGB-luma p99,
not a whole-clip scene search (`DEC/results.json`, `brightest_sample`). Raw Y spans
2-255; p1/p50/p90/p99/p99.9 = 21/97/196/217/245; occupancy at least 235 is
.400427%, at least 250 is .018880% (`DEC/short-30s.json`, `sdr_histogram`). This is
consistent with tagged full-range SDR. A scene histogram cannot prove the absence
of mislabelled HDR or reconstruct Studio's tone mapping. The limited-range long
source has admission and prefix decode evidence, not this ProRes-reference check.

## 3. Throughput and host conditions

The source-venv GPU path used c3 defaults, Standard quality, auto encoder,
`device_frames=True`, cold cache and `keep=True`. D/E record `GPU`,
`CupyBackend(device='cuda:0')`, `hevc_nvenc` and tied NVENC proof (`R/bench-hevc62q.json`,
`R/bench-hevc439.json`, `bench`). GPU pack remained absent. The D gate shows an
RTX 4070-family GPU, 8,188 MiB and driver 621.14 (seat
`window2/gate-raw-D-20261109T173659Z.txt:4,10-11`, under the absolute seat root above).

Window 1 is **host-confounded, not performance of record** (CHARC `e6a411f4`).
The foreground 3D game `Wow.exe` appears in `R/bench-hevc62.json`, `bench.strays`;
idle GPU memory was 3,467 MiB, device peak 6,483 MiB against estimate 4,065.4 MiB.
The product V16 memory rule failed; idle memory is never subtracted. That leg took
2,632.07 s / 42.59 min/min (`bench.wall_s`, `total`, `memory_check`). Its successful
native export does not make its failed wrapper acceptable. W1:3-8 dates C1/C3/D.

Window 2 is the performance record accepted by CHARC. The N6 target is 12.0 min/min
(`tools/n6.py:8`); historical cold median is 10.888984
([WP5.2 report, section 2](wp5.2-performance-memory.md#2-n6-facts-for-charc-and-the-owner)).

| Leg | Frames | Wall s | min/min | Frames-phase fps | Output bytes | Evidence |
|---|---:|---:|---:|---:|---:|---|
| D, short | 1,852 | 639.48 | 10.35 | 3.01 | 232,415,145 | `R/bench-hevc62q.json`, `bench`; W2:12 |
| E, medium | 13,154 | 4,845.61 | 11.04 | 2.73 | 1,575,091,882 | `R/bench-hevc439.json`, `bench`; W2:18 |
| N6 control GX011627 | 681 | 246.3 | 10.84 | 3.11 fps (681 frames / 219.3 s, seat log W2:6) | Not quoted | **Seat log W2:6**; record path there is in the main working folder |

Frames-phase fps is `frames / phases_s.frames`, not the end-to-end rate. The control
record was not copied here; its figures above are explicitly seat-log evidence.
D's child passed but launcher exited 1 during pid-reuse cleanup; W2:13 records the
instrument failure after measurement. E's launcher exited 0 (W2:18).
E's retained throughput output replaces dropped export B for V4 and the look pack.
The spawned-worker short export A completed on GPU in 2,143.33 s, but was not
exclusive and is not a timing figure of record (`R/export-hevc62.json`, `result`).
That record has top-level `ok: false`, `error: "RuntimeError: required GPU correction path not established"`:
the turn-3 driver's wrong device check (dispatch 4), not an export failure;
`result.ok` is true with `result.device: "GPU"`.

Native benchmark phases, in seconds, retain their instrument names:

| Leg | setup | probe | analysis | open | frames | close | committed | Evidence |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| D | .000280 | 1.763 | 21.754 | .563 | 614.565 | .787 | .0437 | `R/bench-hevc62q.json`, `bench.phases_s` |
| E | .000485 | 3.513 | 27.766 | 2.212 | 4,810.443 | 1.600 | .0733 | `R/bench-hevc439.json`, `bench.phases_s` |

`analysis` is the lead phase; analysis overlaps the frame loop. These are not an
additive decode/correct/encode cost split. No such split is claimed.

| Leg | Peak tree RSS bytes | Device peak / estimate MiB | Idle MiB | Pool peak / estimate MiB | V16 check | Evidence |
|---|---:|---:|---:|---:|---|---|
| D | 3,691,827,200 | 3,465 / 4,065.4 | 288 | 1,471.3 / 2,173.8 | PASS | `R/bench-hevc62q.json`, `bench.telemetry`, `memory_check` |
| E | 3,709,526,016 | 3,327 / 4,065.4 | 312 | 1,471.3 / 2,173.8 | PASS | `R/bench-hevc439.json`, same fields |

RSS is sampled nominally at 0.25 s (maximum gaps 0.332 s for D, 0.511 s for E);
device memory is sampled at 1 s (maximum gaps 1.053 s / 1.241 s for D / E), with
no sampler errors (`bench.telemetry.periods_s`, `gaps_s`, `errors` in those records). Sampled peaks
are not continuous bounds. Both RSS peaks are below N4's 16 GB ceiling (spec N4).

| Decode-only leg | Range | Frames read | Pipe bytes | Wall s | fps | Evidence |
|---|---|---:|---:|---:|---:|---|
| C1, whole short | Full | 1,852 | 46,083,686,400 | 247.354 | 7.48724 | `R/decode-hevc62.json` |
| C3, long-source prefix | Limited | 3,000 | 74,649,600,000 | 397.436 | 7.54839 | `R/decode-hevc2259-prefix.json` |

These are the product's CUDA decode command drained to host RGB; no FrameStream
normalization, correction or encoding. Bytes crossed a pipe, not a saved frame file.
C3 stopped at its cap without forced kill or trailing bytes; decoder exit 1 was the
expected cap termination. Full and limited range decode alike at the sampled rates.
Both legs are from confounded window 1, so this comparison is descriptive, not a
clean absolute throughput baseline. No C2 medium decode-only result is claimed.

The seat's five-second `gpu-series.csv` files are device-wide, not job-attributed.
CSV timestamps are local UTC-10; the table selects each leg's UTC interval from W1/W2.
Columns after timestamp are GPU / decoder / encoder utilization and used MiB, as in
the gate query header (`window2/gate-raw-D-20261109T173659Z.txt:25`).

| Leg | Samples | Median GPU % | Decoder min-max % | Encoder min-max % | Used MiB min-max | Raw CSV evidence |
|---|---:|---:|---:|---:|---:|---|
| C1 | 54 | 51.5 | 0-6 | 0-0 | 3,351-3,867 | seat `window1/gpu-series.csv:1-54` |
| C3 | 90 | 63.5 | 0-4 | 0-0 | 3,351-3,866 | seat `window1/gpu-series.csv:55-144` |
| D, window 1 | 546 | 82 | 0-7 | 0-51 | 3,286-6,467 | seat `window1/gpu-series.csv:145-690` |
| N6 control | 55 | 81 | 0-6 | 0-54 | 261-3,200 | seat `window2/gpu-series.csv:1-55` |
| D, window 2 | 132 | 84 | 0-7 | 0-63 | 172-3,417 | seat `window2/gpu-series.csv:83-214` |
| E | 973 | 84 | 0-8 | 0-70 | 195-3,327 | seat `window2/gpu-series.csv:229-1201` |

Sparse zero decoder/encoder samples do not establish an unused hardware path;
the tied NVENC evidence is separate. Window-1 high memory includes other work.
The coarse series misses D's 1 s device-sampler peak, illustrating its sampling limit.
W2:7,10,16 records light byte-probe/review overlap; W2:18 records background
system activity and E GPU temperature 67.9 C before / 78.1 C after. These conditions
are retained; the seat admitted window 2 as the comparison window.

CHARC's like-for-like reading: legs D and E AND the N6 control GX011627 (10.84)
all ran under the same frozen-t6 supervisor in the same window, so the "D and E
at N6" comparison is like-for-like whatever the supervisor cost; the cost can
only bias the absolute figures upward on a multi-core host. The measured figure
is recorded; the conclusion does not depend on it. The supervisor measurement is
8.65% of one core for frozen-t6 and 1.11% for r5 (section 6; W2:33).

## 4. V4 = FAIL: the package finding

**[MAJOR, product] Exact end-of-track preservation fails D94 / D95 / D105 and
spec 7.5.** The same class appears in all completed V4 legs; no pass is claimed.

| V4 record (`R/`) | Source/export | MANDATORY different | REQUIRED different | BEST-EFFORT different | Video duration ticks, source -> output |
|---|---|---:|---:|---:|---|
| `v4-bench-hevc62q.json` | Short, D | 4 | 0 | 7 | 1,853,854 -> 1,853,855 |
| `v4-hevc62c.json` | Short, spawned A | 4 | 0 | 7 | 1,853,854 -> 1,853,855 |
| `v4-bench-hevc439b.json` | Medium, E | 4 | 0 | 7 | 13,167,167 -> 13,167,168 |

Evidence: each record's `v4.summary`, `required_differences` and `v4.path` raw item
record; the source video time base is `1/30000` in `P/1.json` and `P/3.json`.
The video-duration delta is exactly +1/30000 s. `missing` and `unexpected` are empty.
Frame counts, full presentation-PTS sequences, start offsets and audio
packets are SAME: short 1,852 frames / 2,897 audio packets; medium 13,154 / 20,574
(the raw V4 `items`, reached through each `v4.path`). Colour, sync and orientation
items also pass. Instrument cleanup is clean: survivors empty, no discovery error,
`ppid_map`, psutil 7.2.2 (records' `v4.monitor`; W2:37,42,48).

The four MANDATORY names, exactly as recorded, are:

- `video stream duration`
- `movie duration: mvhd (presentation form, exact)`
- `edit list, video track, as written (media_time in media seconds)`
- `edit list, video and audio tracks (presentation effect)`

The same seven BEST-EFFORT names occur in each `v4.summary.different_items`:
`camera atoms: moov/udta children (type, bytes, MD5)`; `ftyp brands`;
`container tags other than creation_time`; `stream tags other than creation_time and timecode`;
`video sample entry child boxes`; `edit lists as written, non-video tracks (media_time in media seconds)`;
`container duration (ffprobe, 1 us)`.

CHARC and WP7.2 round 0 traced the video error to
`src/clearwater/io/video/verify.py:652` (`presentation_end`) and `:676` (`frame_end`):
the source edit-list end, represented on the movie grid, is preferred over the exact
track duration and then ceiled to a video tick. For the short clip,
61,795,134/1,000,000 s * 30,000 = 1,853,854.02 ticks, ceiled to 1,853,855;
the track's `start_pts=0`, `duration_ts=1853854` gives 1,853,854 exactly
(`P/1.json`, `product.edit_list`, raw video header; `R/v4-hevc62c.json`, duration items).

The product fix belongs to **WP7.2**, not this worktree. Per CHARC, no product-debt
register row is carried: resolution is through that fix and its acceptance proof.
WP7.1 acceptance remains pending that proof; this report does not claim it ran here.
The ruled fix targets making video stream duration SAME; the three movie-level
rows remain a separate owner-held reading.

The movie-level rows will not automatically clear with the video-track fix.
WP7.2 round 0 found Studio's Lavf60.3.100 muxer rounds video UP and audio DOWN to
whole microseconds, leaving movie-level timing inconsistent with track-exact ends.
For example, the short audio presentation duration is `61781333/1000000` in source
and `23168/375` in output (`R/v4-hevc62c.json`, edit-list presentation-effect item).
The owner's word is **PENDING** on: "SAME when within one movie tick of each side's
grid; track-level items stay exact" (CHARC disposition in dispatch 13). No V4
instrument reading has been changed ahead of that decision.

CHARC's disposition for E: **the E record stays FAIL on this class permanently;
the accept reads the 439 s clip's D94 status from the unchanged class across
D / A2b / E plus WP7.2's unit proof and the 62 s re-runs.** This is an acceptance
plan, not a changed verdict on the retained record.

Follow-ups ran under narrow ruling `a87c0040`. Their fields remain
`v4_admitted: "end-of-track +1 tick, CHARC ruling a87c0040"`, `v4_pass: false`.
Admission checks the exact four names, exact +1 source-track tick, no REQUIRED or
roster differences, and a successful retained export. JSON proofs are in
`work/wp7.1/proofs-t7b/result.json`. **Admitted never means passed.**

## 5. Comparisons, look pack and long-clip projection

F1/F2 compare each output with its own source, not the two different videos with
each other. These are intended correction differences, not an oracle or quality
pass; no numerical band was applied. All source/output PTS match exactly.
Values are normalized float32 RGB, R / G / B (`R/compare-hevc62.json` and
`R/compare-hevc439.json`, `samples[].alignment`, `difference`).

| Record | Requested s | Exact matched PTS | MAE | p99 absolute | Maximum absolute |
|---|---:|---|---|---|---|
| `R/compare-hevc62.json` | 10 | 1001/100 | .110489 / .120365 / .289691 | .313726 / .196078 / .388235 | .478431 / .278431 / .490196 |
| same | 30 | 8999/300 | .150514 / .112848 / .273578 | .317647 / .180392 / .376471 | .427451 / .266667 / .482353 |
| same | 50 | 499833/10000 | .112482 / .096911 / .233820 | .333333 / .184314 / .341176 | .439216 / .294118 / .494118 |
| `R/compare-hevc439.json` | 60 | 8999/150 | .148759 / .110261 / .262141 | .270588 / .184314 / .341176 | .384314 / .278431 / .435294 |
| same | 220 | 16499/75 | .121886 / .118073 / .279708 | .200000 / .192157 / .360784 | .317647 / .262745 / .458824 |
| same | 380 | 28501/75 | .135843 / .119560 / .301641 | .211765 / .180392 / .376471 | .333333 / .262745 / .490196 |

The look pack is `work/wp7.1/look/index.html`: six before/after pairs, linked
full-resolution PNG16 images and 960x540-bounded thumbnails. Provenance, exact PTS,
artifact hashes and pending outcome are in `work/wp7.1/look/manifest.json`,
`R/look-assemble.json`, `R/look-html.json`. HTML md5 is
`c9e6e40bd216c54e0405efee8653017b` (`R/look-html.json`). **Owner look verdict: PENDING.**
Playback and flicker quality are not established by stills or V4. F1/F2/G/H/I
finished with `ok=true`, launcher exit 0 and no survivors (seat log W2:50-66);
all retain the V4 FAIL admission fields.

The projection record is `R/long-projection.json`, using C3 only for decode wall.
The long source is `SCUBA vids(1).mp4`, exact duration `22592259/10000` s
(about 37.7 min), 67,709 frames (`P/5.json`; projection `exact_duration_s`).
This is information outside the D117 usage profile, not authorization to export.

| Projection quantity | Value / basis | Evidence in `R/long-projection.json` |
|---|---|---|
| Decode-only wall | 8,969.99 s / 2.49166 h = 67,709 / C3 fps | `projected_decode_only_wall_s`, `wall_basis` |
| Total export wall | Unestablished (`null`) | `total_export_wall_s`, `total_export_wall_limit` |
| Output size from D / E rates | 8.49708 / 8.10764 GB | `rows[].projected_output_bytes_measured_rate` |
| Video ceiling | 29,829,980 bps; source cap ignored conservatively | `video_ceiling_bps`, `source_cap_ignored` |
| Audio / mux allowance | 127,616 bps / 1% planning margin | `audio_bps`, `mux_margin_fraction` |
| Video/audio planning size | 8.54472 GB | `rows[].projected_video_audio_planning_bytes` |
| Incremental disk allowance | 41.38441 GB, plus retained package bytes | `rows[].incremental_disk_planning_bytes`, `disk_assumptions` |
| Cache / other disk allowance | 20,000,000,000-byte cache cap; two output allowances; 4 GiB margin | `rows[].cache_limit_bytes`, `disk_assumptions` |
| Package bytes already retained at projection | 4,118,566,276 | `retained_package_bytes` |
| D RSS early / late quartile medians | 3.60301 / 3.60861 GB; fitted slope +444,522 bytes/s | `rows[0].memory` |
| E RSS early / late quartile medians | 3.60856 / 1.77369 GB; fitted slope -481,797 bytes/s | `rows[1].memory` |

C3 is a prefix-only, host-confounded observation. Its decode wall excludes analysis,
normalization, correction and encoding. D/E full-range rates are not substituted
for the limited-range long clip's wall rate. D/E supply size/memory context only;
CQ/VBR size depends on content, the mux allowance is not a guaranteed bound, and
sampled memory is not multiplied by duration or claimed bounded for the long clip.
**No long export ran; it runs only on the owner's word.**

## 6. Instrument record and verification

These are candidate instrument rows for CHARC's accept, not product defect rows.

| Candidate | Finding, disposition and evidence |
|---|---|
| WP7.1 seat process supervision | WP7.1 seat process supervision (isolate.py pid reuse, run_export.py poll exception type, finally-wait, F1 stale-parent adoption, F2 stale sampling, and the unmeasured supervisor cost) was never exercised against a child that outlives one poll or a pid that is reused; the frozen drivers now carry proofs (frozen-t7 / t8). |
| V16 idle memory never subtracted | Window-1 game raised idle memory; device peak, not peak minus idle, is compared with estimate. `R/bench-hevc62.json`, `bench.memory_check`, correctly fails with idle 3,467 MiB and device peak 6,483 MiB. Preserve the host-confounded record; do not relax the product check. |

The seat DID hit pid reuse in window 2 (seat log W2:13), which is how the defect was found.

The initial supervision proof gap covered children outliving a poll and reused pids;
it is not a claim that the later seat never encountered them. D's cleanup exception
and the failed first V4 chain supplied the concrete reproductions (W2:13,29-32).
Final proofs cover long-child success, launcher timeout, wrong identity untouched,
outer supervisor, stale-parent exclusion, guarded discovery failure, and both discovery
paths. Previously unseen orphans after all observed ancestry exits remain unreachable;
the frozen packet states this limit. The residual psutil check-to-kill race is documented.

Supervisor cost measurements use an own five-process sleeper tree, supervisor
`cpu_times()`, about 60 s, no media. These are not clip throughput measurements.

| Supervisor | CPU s | Wall s | % of one core | Evidence under `work/wp7.1/proofs-t7a/` |
|---|---:|---:|---:|---|
| Frozen-t6 | 5.218750 | 60.328 | 8.65 | `r4/cpu-frozen/result.json` |
| Pre-r3 | 34.671875 | 60.375 | 57.43 | `r3/cpu-before/result.json` |
| r3 | 18.640625 | 60.344 | 30.89 | `r3/cpu-after/result.json` |
| r4 | .750000 | 60.281 | 1.24 | `r4/cpu-r4/result.json` |
| r5, ppid_map | .671875 | 60.344 | 1.11 | `r5/cpu-native/result.json` |
| r5, process_iter fallback | 6.687500 | 60.375 | 11.08 | `r5/cpu-fallback/result.json` |

Frozen-t6's actual copied source md5 is `4f7fd279ff0135719852996de693f95d`.
Its old supervisor `driver_md5` misleadingly named the live r4 file; the correction
is in `proofs-t7a/r5/review-ledger.md`, M3. Original proof outputs remain unchanged.
The primary r5 path meets CHARC's 5% bar; the fallback has no bar and records its path
and psutil version. No supervisor cost is subtracted from D/E/control walls.

Turn 7b-fold's seat delta read was CLEAN; frozen-t8 follow-ups completed (W2:50,66).
This report turn ran `uv run --no-sync ruff check work/wp7.1`: **exit 1, 511 findings**,
including historical generators, copied proof sources and generated stubs
(`work/wp7.1/report-audit/ruff.log`). No driver was edited to hide that result.
This broad scratch-tree check is not the earlier targeted-driver Ruff pass.
No pytest, media, GPU, GUI or independent report review ran in this turn.
Evidence-preservation audit is `work/wp7.1/report-audit/final.json`; report review
and the report-only static/harness accept gate remain at the seat.

## 7. Spec note proposed to the owner

Proposed source note, subject to the pending acceptance items:

> Insta360 Studio's flat SDR-tagged H.265/HEVC MP4 exports are accepted as Clearwater
> inputs under section 5.2. Clearwater uses their stream colour and range tags under
> D54, including full-range exports. ProRes exports are refused under section 5.2;
> use Studio's H.265 export setting. Native `.insv` input is not supported and is
> excluded from the supported-source scope by the owner's standing decision.

This proposes no ProRes/4:2:2 admission or spec edit by WP7.1. The owner decides any
future change separately. The note does not waive the V4 failure documented above.

## 8. Limits and open acceptance items

- **ProRes / 4:2:2 input:** a separate owner question at the accept (a spec change
  plus a product package, Phase 7 candidate), per the brief's scope correction
  `626e30f0` (`docs/briefs/wp7.1-brief.md:3`): "ProRes / 4:2:2 input is put to the owner at the accept as a separate question (a spec change + a product package, Phase 7 candidate)."
- **Owner look verdict pending:** the pack is prepared; preference, artifacts,
  playback and flicker remain owner-reserved.
- **Owner movie-level reading pending:** the one-movie-tick proposal in section 4
  has not changed the exact V4 instrument or the stored FAIL records.
- **WP7.2 and short re-runs pending:** WP7.1 accept waits on the video-end fix,
  its unit proof and two 62 s re-exports, budgeted at about 25 min of exclusive GPU
  in an owner quiet window. This is CHARC's scheduling estimate in dispatch 13,
  not a measured run or a command authorized by this report turn.
- **E remains FAIL:** its acceptance evidence is the unchanged failure class plus
  WP7.2 proof and short re-runs, as ruled; no medium re-export is claimed.
- **Long clip:** prefix decode and full-range size/memory context do not establish
  end-to-end long-export cost or bounded memory. No long export without owner word.
- **Coverage:** one camera, three Studio videos; selected-frame agreement and stills
  are not exhaustive scene-quality or flicker checks. ProRes is reference-only;
  the extra lower-rate MP4 is probe-only; native `.insv` is excluded.
- **Verification:** broad scratch Ruff is not green (section 6); the report and
  package acceptance still require the seat's remaining review/gate disposition.
