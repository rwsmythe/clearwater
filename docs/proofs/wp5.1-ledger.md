# WP5.1 cumulative ledger

## Dispatch and round 0

- Package: WP5.1, automated acceptance suite, CODEX lane, STRONG tier.
- Inspected base and HEAD: `2050a89a`; branch/worktree supplied by the dispatcher.
- Turn 1 scope: T1 only. No test code, product code, existing test, dependency,
  local configuration, interface or register was changed.
- Delivery: this ledger and the final turn report; the dispatcher commits and
  runs the Claude Reviewer A/B passes. No mailbox post or git write was made.
- Session id and `depth_input_tokens`: dispatcher to fill from the cell record.
- Status: T1 mapping complete; STOP to CHARC for R0-1 through R0-4 below.
  The roster is provisional until those rulings arrive. No test has been added,
  run, skipped or claimed passing in this turn.

## Rulings needed before T2

### R0-1 [MAJOR, NEW, in envelope]: JPEG recipe error precedes the neutral path

Recommended: keep the 2/255 neutral-path bound against an independently decoded,
correctly oriented JPEG source, and have CHARC specify the separate pristine-recipe
pose check. Do not change a tolerance without that ruling.

T3 requires max error at most 2/255 against the generating recipe. Pillow's
independent JPEG decode already differs from that recipe by **3/255 on all eight
JPEGs**. The generator explicitly uses lossy JPEG quality 95, subsampling 0
(`tools/fixtures/stills.py:66`, `:831`). The existing oracle instead compares the
output with Pillow's oriented decode (max 3 levels) and records the recipe match
with a mean bound (`tests/test_wp41_photo_path.py:308`, `:318`, `:319`).

Cheap reproduction, `t1-pose-probe.log`: `uv run python -` loaded each committed
JPEG with Pillow, applied `ImageOps.exif_transpose`, and compared its RGB array
with `spike_io.photo.upright_image(8, width, height)`. Max = 3 for all eight;
means range 0.523872 to 0.544488 in 1/255 units. This reads no product decoder.
Independent shipped-runner reproduction, `t1-photo-runner-probe.log`: a neutral
8-bit `jpeg-orient-land-o1.jpg` export exited 0, was **0/255 max from the decoded
source**, and **3/255 max from the pristine recipe**. The literal T3 assertion
would reject an exact neutral export because of source JPEG loss.

The non-identity controls also need the shape case stated explicitly: o3 gives
max 255/255 against stored pixels, while o6/o8 swap the unequal width and height,
so direct elementwise subtraction has no defined matching shape. Recommended:
accept unequal shape as a detected wrong pose, with max > 64/255 for equal-shape
wrong poses. No fallback planted asymmetric still is needed for content symmetry.

Disposition: resolved by CHARC `cdeefe5fb8114b0c`, R0-1. T2 bounds the
oriented source decode at 2/255, records recipe mean without a bound, and accepts
unequal shape as a detected wrong pose. This was not a product defect.

### R0-2 [MAJOR, NEW, in envelope]: specified PNG never reaches 64 KiB

Recommended: inject ENOSPC after **1 KiB** of actual writes for this exact fixture,
splitting the crossing write so some bytes really reach the file before the
exception. Keep the real writer, source, cleanup and failure assertions unchanged.

T4's source `png16-gradient-srgb.png` is 96 x 64 RGB16
(`tests/fixtures/manifest.json:2718`). Even the uncompressed rows total only
64 * (1 + 96 * 3 * 2) = 36,928 bytes. The actual default-correction 16-bit export
through `headless_export.main` exited 0 and produced **1,881 bytes**, including
metadata/provenance (`t1-photo-runner-probe.log`). It cannot raise a fault after
65,536 bytes have been written. It is not a disk-full product failure.

Writer seam: `PhotoWriter.write` delegates at
`src/clearwater/io/photo/writer.py:135`; the real file is opened with
`Path.open("wb")` at `src/clearwater/io/photo/png.py:184`, with writes at `:185`,
`:190`, `:202`. `Path.open` uses `io.open`, so patch the lower `io.open` (or
`Path.open`) only for binary output temporaries under the node's output folder.
A blanket `builtins.open` patch would miss this writer.

Disposition: resolved by CHARC `cdeefe5fb8114b0c`, R0-2. T2 injects after
1 KiB of actual writes at Path.open, limited to binary output temporaries under
the node's output folder; the threshold and firing are asserted.

### R0-3 [MAJOR, NEW, in envelope]: truncated fixture is readable, not refused

Recommended: the truncated batch item succeeds with the D86 warning and a
readable-prefix output, the next item succeeds, and the batch exits 0. Preserve
the exact readable-prefix fidelity checks. Use an unreadable file for a failed
item only if CHARC commissions that additional case.

T6 says `truncated` is a failed item. Spec 5.4 and D86 instead require processing
the readable portion with a warning (`docs/underwater-correction-spec.md:124`,
`:225`). Existing engine nodes explicitly assert success for this fixture:
`tests/test_wp42_video_path.py:183` and
`tests/test_jobs_export_video.py:169` (its truncated branch at `:187`).

Cheap reproduction, `t1-truncated-runner-probe.log`: in-process `main`, forced
CPU/libx265, batch `[truncated.mp4, hevc8-bt709-full.mp4]`, separate scratch output,
cache and record. Exit **0**. Item 1 **done with warnings**, failure null, output
`truncated_corrected.mp4`; warning:

> The source is cut short; the output ends at its last readable frame, and the audio and other tracks are cut at the same point.

Item 2 **done**, failure null, output `hevc8-bt709-full_corrected.mp4`.
This is the shipped path obeying the spec, not a product defect to remediate.

Disposition: resolved by CHARC `cdeefe5fb8114b0c`, R0-3. T6 will require
success with the D86 warning and readable-prefix fidelity, following the ruling.

### R0-4 [MAJOR, NEW, in envelope]: fixture sweep versus sizing rule

Recommended: retain the committed fixtures unchanged for the explicit V4/V6/V9
fixture sweep (the subject includes their actual containers, timing, tags and
orientation); have CHARC explicitly rule that sizing exception. Apply six-frame
sizing to new derived cases only where CHARC identifies them. Do not re-encode
the fixtures and call them the original container evidence.

The brief's marker rule calls for six frames and 1080p, while T6/T7 name the
committed fixtures and require comparing their source and output timing/tags.
Their manifest facts are **320 x 180**, 45 frames for hevc8, hevc10, untagged and
rotated; VFR is 30 frames; truncated has 24 readable frames from a 45-frame
container. The VFR durations alternate 1001/2002 ticks as intended.
`t1-manifest.log` contains the inspected synthetic fixture facts.
AD-30 (`docs/decisions.md:45`) distinguishes properties and real-container cases,
but does not explicitly resolve this brief's named synthetic-fixture sweep.
The existing engine V4 node consumes those committed files without resizing
(`tests/test_jobs_export_video.py:173`, `:183`).

Disposition: resolved by CHARC `cdeefe5fb8114b0c`, R0-4. The named fixture
sweep uses committed files unchanged; derived cases retain six-frame sizing.
The <= 180 s serial-leg budget remains subject to measurement at the seat.

## Anchor relocation on 2050a89a

Line numbers below refer to this worktree's inspected base. A range means the
named mechanic starts at the first cited line; it is not a substitute for an
execution result. Literal brief anchors that did not move are recorded too.

### Protocol, spec and decisions

| Brief reference | Located anchor and binding content |
|---|---|
| Dispatch protocol | `docs/dispatch-recipe.md:1`: read in full; isolated workspace, build cycle, review, acceptance transfer, STOP = yield |
| Application | `APPLICATION.md:1`: application definition; spec/plan hierarchy and owned-file locks |
| Project entry point | `CLAUDE.md:1`: read; current-state summaries do not supersede shipped code or this dispatch |
| Plan 3 / 4.5 / 6 / 7 | `docs/clearwater-implementation-plan.md:43`, `:89`, `:351`, `:369`; no assumptions at `:100`; failures routed at `:361` |
| Plan N10 / D91 | `docs/clearwater-implementation-plan.md:405`, `:406`: same export twice; provenance checked here |
| V1-V18 | `docs/underwater-correction-spec.md:469`; V1 `:473`, V2 `:474`, V3 `:475`, V4 `:482`, V5 `:486`, V6 `:487`, V7 `:488`, V8 `:489`, V9 `:490`, V10 `:491`, V11 `:492`, V12 `:493`, V13 `:494`, V14 `:495`, V15 `:496`, V16 `:497`, V17 `:498`, V18 `:499` |
| Spec 5.3 / 5.4 / 6.5 | `docs/underwater-correction-spec.md:219`, `:224`, `:275`; missing-tag assumption and warning at `:278` |
| D25 / D54 / D55 / D63 | `docs/underwater-correction-spec.md:63`, `:92`, `:93`, `:101`; four EXIF edits at `:363` |
| D81 / D84 / D85-D87 | `docs/underwater-correction-spec.md:119`, `:122`, `:123`, `:124`, `:125`; naming at `:382`, safe writing at `:388` |
| D91 / D92 / N10 | `docs/underwater-correction-spec.md:129`, `:130`, `:460`; output provenance at `:369`, `:380` |
| D105 / D114 / D115 | `docs/underwater-correction-spec.md:143`, `:152`, `:153`; mandatory/best-effort at `:376`, `:379` |
| G10 | `docs/underwater-correction-spec.md:410`: clear messages for unsupported, damaged and untagged inputs; real-shell message node below |
| AD-10 / AD-11 | `docs/decisions.md:19`, `:20`: transport versus pre-encode bounds; amended V8 has p99 bounds, not the obsolete max-only summary |
| AD-13 / AD-24 | `docs/decisions.md:22`, `:33`: source file name only; HEIC apply irot once and EXIF additionally only without irot |
| AD-28 / AD-30 | `docs/decisions.md:37`, `:45`: leg split, fullclip identity and property-specific sizing |
| Prompting standard | `docs/model-prompting-standard.md:1`: read in full; verify claims at gates, report every finding with severity |
| Reviewer A / B and round policy | `docs/review-gate-clearwater.md:12`, `:87`; Claude passes for this lane, NEW blocking convergence, five-round/depth gates; dispatcher runs them |
| Final suite gate | `docs/review-gate-clearwater.md:132`, `:149`: B before ONE gate; dispatch additionally requires the phase-end fullclip leg |
| DR-98 / DR-99 | `docs/debt-register.md:107`, `:108`: DR-98 OPEN on this base; DR-99 exception limited to the named telemetry-origin failure |
| V14 figure of record | `docs/reports/wp1.6-gate-report.md:25`, `:106`, `:125`, `:148`, `:168`, `:180`, `:214`: six results and V14 record |
| V7 / V18 window evidence | `docs/reports/wp4.3-application-wiring.md:70`, `:79`, `:97`, `:216`; (a) 18, (b) 19, (d) 56, (f) 50.6 ms PASS; (c) 180/181, (e) 182 ms OPEN STOP |
| WP4.6 window evidence | No WP4.6 report is present on this base. Read it on the final rebased candidate, never from another worktree; refresh DR-98 then |

### Shipped paths and exact reuse points

| Brief reference / task | Located mechanic and intended reuse |
|---|---|
| Runner docstring/schema | `tools/headless_export.py:1`, `:48`: status meanings, record source/output names, warning/failure redaction, injected-engine video facts null |
| Runner main/run/exports | `tools/headless_export.py:1311`, `:942`; `main(argv, exports=...)`, run passes through `run_batch`; composition at `:996` |
| Runner record | `tools/headless_export.py:1024`, `:1110`, `:1122`: JSON object/serialization/status; item warnings and failure `:1052`, `:1053` |
| Composition injection | `src/clearwater/app/composition.py:351`: methods, writer, source_for, sink_for, cache_folder; real factories `:149`, `:162` |
| Fidelity instrument | `tools/video_fidelity.py:1251` `fidelity_record`, `:1175` `fidelity_items`, `:1151` roster invariant, `:102` item roster |
| Fidelity classes | `tools/container_spike/compare.py:19`, `:28`, `:34`, constants `:72`: MANDATORY, REQUIRED (D55/D114), BEST-EFFORT; assert both mandatory and required summary |
| Best-effort telemetry anchor | `tests/test_video_fidelity.py:119` (brief cites `:123`, the class argument); packet-count-only redaction at `:130` |
| V4 assertion helper | `tests/test_wp42_video_path.py:373`, `tests/test_jobs_export_video.py:106`: summary plus roster; imitate in support |
| Output video decode form | `tools/video_fidelity.py:168`, command `:194`; noautorotate, exact pts, passthrough, source-depth planar RGB converted to arrays |
| Alternative decode anchor | `tools/lookcheck/frames.py:773` `decode_command`; `tests/test_color_support.py:136` is the actual pair's decode command used by the color-roundtrip tests |
| WP3.5 pair bounds | `tests/test_color_roundtrip.py:44`, `:54`, `:56`, `:58`: synthetic mean 2.5, real mean 1.0; max recorded; pair excludes the encoder |
| PNG readers / metadata | `tests/test_wp41_photo_path.py:64` chunks, `:95` provenance, `:111` EXIF; T3 uses Pillow getexif on the output plus a separate FFmpeg RGB24 decode |
| V5 bit depth / ICC / EXIF / D91 | `tests/test_wp41_photo_path.py:258`: existing coverage, cite rather than duplicate; source provenance name at `:269` |
| JPEG orientation | `tests/test_wp41_photo_path.py:308`; upright recipe helper `:164`; independent oriented Pillow decode `:313` |
| HEIC orientation | `tests/test_wp41_photo_path.py:325`: reuse landscape recipe, mean < 6 levels, shape equality and other-pose rejection at `:332`-`:338` |
| Photo V9 | `tests/test_wp41_photo_path.py:344`, `:361`: quantized-source oracle and AD-11; not a pristine-JPEG-codec bound |
| Photo V10 | `tests/test_wp41_photo_path.py:425`, `:441`, `:453`: existing cross-format collision, pre-existing-output and custom-suffix nodes |
| Photo N10 / GPU | `tests/test_wp41_photo_path.py:502`, `:544`: pre-encode pixels and same-device bit identity; GPU comparison figures |
| Video V4 sweep | `tests/test_jobs_export_video.py:169`, fixture roster `:52`; CPU/GPU engine path, not runner main |
| Video refused samples | `tests/test_wp42_video_path.py:426`: asserts name, ASCII and no writes; DOES NOT assert transfer words there; HLG/PQ words are in `src/clearwater/io/video/probe.py:443` (HLG/PQ refusal at `:451`) |
| Video V9 pre-encode | `tests/test_wp42_video_path.py:464`, source decode `:444`; existing c3/ancuti nodes; new post-encode nodes add a different surface |
| Video V17 | `tests/test_wp42_video_path.py:498`: reopen counts 2 then 1 decode, version mismatch re-analysis; cite existing node |
| Disk-full doubles | `tests/test_jobs_export.py:523`, `:536`: existing sink/photo doubles; new real PNG fault is T4 |
| Existing video crash | `tests/test_jobs_export_video.py:649`: subprocess kill/leftovers, engine child rather than runner; use as cleanup reference only |
| Existing startup cleanup | `tests/test_app_leftovers.py:370`: shell startup; direct non-GUI form `:287`, call at `:300`; production `clean_leftovers` at `src/clearwater/app/startup.py:274`, `WriteJournal` at `:49` |
| MP4/MOV numbering | `tests/test_jobs_naming.py:550`, `:560`, `:594`, `:607`: mapped extension, shared sequence, both order/case rules; new runner nodes do not edit these |
| Video provenance reader | `tests/test_io_video_encode.py:1293` `_comment`: ffprobe format_tags=comment JSON; assertions at `:1312`, `:1325` |
| Runner testing conventions | `tests/test_headless_export.py:57` `_main`, `:240` schema/names; `:338` child process; `:533` stdout/stderr/record path checks; imitate without its OS-specific helper additions |
| Stub-probe untagged case | `tests/test_gui_open.py:341`: existing stub path; not evidence for the new real-file text assertion |
| Real G10 shell case | `tests/test_app_wiring.py:382`, untagged words empty at `:377`: real open, captured presenter and severity at `:387`-`:393`; retain old test unchanged |
| Shell fixture helpers | `tests/test_app_startup.py:71` `make_app`, `:63` CPU settings, `:98` presenter, `:105` wait_started, `:114` open_source, `:123` wait_analysis, `:131` latest_analysis |
| GUI support | `tests/gui_support.py:67` CapturingPresenter; startup fixture builds real application over tmp_path; no custom conftest edit |
| V18 hold and running shell | `tests/test_app_v8_v18.py:366` HeldEngines, `:405` existing node; release in finally, verify running phase and provisional statistics, then smoothed statistics and render |
| Render pixels | `tests/test_app_v8_v18.py:77` rendered_at and `:86` image_bytes; new real-trim node snapshots before/after and records a nonzero pixel change |
| Oracle recording pattern | `tools/export_oracle.py:161` RecordingMethod records RENDER INPUT STATISTICS at `:217`; returned-pixel digests are actually in RecordingSink `:231`/`:255`, with host/dtype/shape/C-order digest at `:110`/`:116` |
| Session trim | `tests/conftest.py:827` gx011627_trim (tuple path/count), checks at `:850`, teardown at `:855`; gx011627 `:868` is trim/full parametrized and will NOT be used by new nodes |
| Manifest/sample helpers | `tests/fixture_plugin.py:51` load_manifest, `:268` fixture_manifest, `:274` ffmpeg_tools, `:297` sample, `:303` sample_entry; no footage read in that plugin |
| Fixture generator entry | `tools/fixtures/generate.py:46` generate; delegates stills at `:72` to `tools/fixtures/stills.py:701` build |
| JPEG/HEIC recipe | `tools/fixtures/stills.py:713`, `:831`, `:865`; detailed below |
| Type checking | `pyproject.toml:100`: strict mypy currently targets src/clearwater and tools, not tests; type the new modules and separately check them as needed without changing configuration |

## Pose recipe and controls

`spike_io.photo.upright_image` (`tools/spike_io/photo.py:226`) uses red increasing
left-to-right, green top-to-bottom, blue = 0.2 + 0.6*x*y. Eight-bit values are
rounded from [0, 1] to [0, 255]. Landscape is width 96, height 64; portrait width
64, height 96. This content distinguishes rotations and flips.

`stored_image` (`tools/spike_io/photo.py:278`) applies the inverse orientation:
o1 unchanged; o3 rotates 180; o6 stores with o8 (90 anticlockwise); o8 stores
with o6 (90 clockwise). JPEG then saves that array at quality 95/subsampling 0
and tags it with its orientation. T3's JPEG reader must not confuse JPEG loss
with a neutral-path error (R0-1).

All four HEIC cases target the same landscape recipe. The three rotated cases
store the o6 inverse pose; the `neither` case stores the upright pose:

| Case | Stored orientation recipe | EXIF tag | irot transform given to encoder | Manifest irot |
|---|---|---|---|---|
| both | inverse of o6 | 6 | 6 | 270 degrees anticlockwise |
| irot-only | inverse of o6 | 1 | 6 | 270 degrees anticlockwise |
| exif-only | inverse of o6 | 6 | 1 | absent |
| neither | o1 | 1 | 1 | absent |

`write_heic` uses `CtxEncode` to separate the EXIF tag and irot
(`tools/fixtures/stills.py:235`, `:265`). Use the existing AD-24 pose oracle as
instructed, not a new color-error bound. HEIC's ordinary Pillow opener already
applies container rotation; a control claiming stored pixels must account for
that, rather than calling its already-rotated result an untransposed source.
The generated arrays are sufficiently asymmetric: equal-shape wrong o3 has
255-level maximum difference; 90-degree poses have different shape. The
optional planted asymmetric still is unnecessary on symmetry grounds.

Manifest anchors: HEIC cases `:476`, `:532`, `:588`, `:644`; JPEG cases `:2035`,
`:2086`, `:2137`, `:2188`, `:2239`, `:2290`, `:2341`, `:2392` in
`tests/fixtures/manifest.json`.

## Planned support module

`tests/acceptance_support.py` will contain typed helpers, not product substitutes:

- `run_main`: call shipped `headless_export.main(argv, exports=...)`, store/read
  its requested JSON record under tmp_path, capture its printed text, assert
  source/output name fields and absence of known full-folder spellings in every
  string-bearing record/printed surface. Preserve the actual warnings/failures.
- `runner_command` / subprocess helper: use the current interpreter and shipped
  runner script, explicit output/cache/record paths, bounded waits and child
  cleanup; logs under the node's tmp_path, names only in recorded properties.
- Streaming file MD5; independent Pillow and FFmpeg PNG RGB24 decoders; output
  Orientation check. Source checks do not read any owner path.
- FFmpeg video-to-array decoding: imitate the source-depth decode command used
  by the color pair/video fidelity instrument, preserve timestamps/rotation
  convention and scale 16-bit RGB to 1/255 units. Do not substitute the product
  decoder for both independent readers.
- Fidelity summary assertion including REQUIRED and the item-roster invariant;
  presence-only best-effort summary (creation time, gpmd, timecode, camera atoms).
  Do not put paths or metadata payloads into the new property/JSON records.
- PNG iTXt and MP4 comment provenance readers, imitating the existing readers
  above; names-only source validation including provenance source.name.
- A delegating method wrapper via composition's `methods=` and runner's
  `exports=`. Hash each returned render's dtype, shape and bytes by pts, imitate
  the oracle's actual array-digest pattern, assert no missing/duplicate pts.
  RecordingMethod's statistics digests alone do not prove N10 render identity.
- `ACCEPTANCE_NODES`, V1-V18 plus N10 and D91; rows for pending/out-of-scope
  requirements carry an explicit status/evidence citation rather than a made-up
  passing node. New-node results remain pending until observed.

The photo/video/shell modules own their assertions and fixtures; support will
not import the shell. Video gets an autouse source-MD5 guard, including copies
made for the MOV collision cases; outputs/caches/records stay under tmp_path.
Reuse assertions/helpers only where they prove the requested new surface;
existing passing tests are cited in traceability, not copied as new nodes.

## Planned nodes, markers, legs and runner forms

These are planned function names, not collected nodes. Bracket labels describe
planned parameter ids. `P?` means a candidate for the parallel leg, requiring
an isolated measurement under 5 s. `S?` means provisionally slow because of
FFmpeg encode; the marker is finalized from actual isolated duration. The
dispatcher performs seat measurements; no timing below is a figure of record.
All eventual slow markers will state the brief's reason. No fullclip node is added.

### tests/test_v51_photo_acceptance.py: 14 instances

| Planned node | Instances | Planned markers / leg | Runner form |
|---|---:|---|---|
| test_v5_jpeg_two_readers_and_pose[land-o1,land-o3,land-o6,land-o8,port-o1,port-o3,port-o6,port-o8] | 8 | none / P? | in-process main, neutral RGB8; two output decoders |
| test_v5_heic_two_readers_and_ad24[both,irot-only,exif-only,neither] | 4 | none / P? | in-process main, neutral RGB8; existing AD-24 oracle |
| test_v11_png_disk_full_removes_partial_output | 1 | none / P? | in-process main; real PNG file-object fault; R0-2 pending |
| test_v11_photo_crash_leftovers_are_cleaned_at_start | 1 | slow / serial; reason: runs the headless runner as a subprocess | shipped runner subprocess, 40 temp copies, poll 10 ms, kill, startup cleanup |

Crash observation ceiling: at most 20 attempts. If none observes a temporary,
record and skip exactly "not observable at this size". This is a planned allowed
skip, not an observed skip. Source md5s and pre-existing outputs stay unchanged.

### tests/test_v51_video_acceptance.py: 20 instances

| Planned node | Instances | Planned markers / leg | Runner form |
|---|---:|---|---|
| test_v4_runner_preserves_fixture_fidelity[hevc8-bt709-full,hevc10,untagged,vfr,rotated] | 5 | slow / S?; reason: FFmpeg encode | in-process main, CPU/libx265, fidelity_record, VFR exact pts |
| test_v4_truncated_runner_batch_obeys_d86 | 1 | slow / S?; reason: FFmpeg encode | in-process main; spec outcome subject to R0-3 |
| test_v4_real_trim_records_best_effort_presence | 1 | footage, slow / serial; reason: FFmpeg encode | in-process main, GPU if usable else CPU, gx011627_trim only; assert gpmd and mandatory/required, record other presence |
| test_v6_hdr_refusals_do_not_stop_batch | 1 | slow / S?; reason: FFmpeg encode | in-process main, HLG + PQ + good source |
| test_v6_untagged_runner_warns_bt709_limited | 1 | slow / S?; reason: FFmpeg encode | in-process main, real untagged fixture; literal warning assertion |
| test_v9_neutral_runner_postencode[hevc8-bt709-full,untagged,rotated,hevc10] | 4 | slow / S?; reason: FFmpeg encode | in-process main, neutral, CPU/libx265; paired FFmpeg decode, mean <= 2.5 levels, max recorded, tags/rotation |
| test_v10_repeated_video_exports_are_numbered | 1 | slow / S?; reason: FFmpeg encode | two in-process main invocations, same output folder |
| test_v10_existing_video_output_is_unchanged | 1 | slow / S?; reason: FFmpeg encode | in-process main with pre-planted bytes and MD5 |
| test_v10_mov_mp4_share_one_numbering_sequence | 1 | slow / S?; reason: FFmpeg encode | in-process main, temp same-stem MOV/MP4 copies |
| test_d91_video_provenance[default,off] | 2 | slow / S?; reason: FFmpeg encode | in-process main, ffprobe comment reader; compare app version/request parameters/name-only source |
| test_n10_video_cpu_render_digests_repeat | 1 | slow / S?; reason: FFmpeg encode | two in-process main calls, injected delegating method, CPU/libx265; file identity recorded only |
| test_n10_video_gpu_render_digests_repeat_and_match_cpu | 1 | gpu, slow / serial; reason: FFmpeg encode | two GPU main calls with wrapper plus CPU comparison, same encoder; decoded first-frame CPU/GPU figures per T7 |

The real-trim node need not carry gpu: both CPU and GPU forms are expressly
allowed, and the result records its actual backend. The explicit T7 GPU node
requires a usable CUDA backend and must not silently count a CPU fallback as GPU.
T7's decoded CPU/GPU bound is retained literally pending measured evidence;
an over-bound result is reported, never relaxed.

### tests/test_v51_shell_acceptance.py: 2 instances

| Planned node | Instances | Planned markers / leg | Running surface |
|---|---:|---|---|
| test_v6_real_untagged_shell_warns_bt709_limited | 1 | gui / serial | real application/open_path, real committed untagged fixture, CapturingPresenter/status text; no stub probe |
| test_v18_real_trim_preview_precedes_analysis_and_updates | 1 | gui, footage, slow / serial; reason: real-trim analysis and FFmpeg decode | make_app and HeldEngines pattern, before/after image_bytes, nonzero pixel change, smoothed statistics |

The old G10 `words=""` assertion is retained. If the new text check fails, its
node stays failing and yields a product-defect STOP per Q3. Same rule for the
runner warning node. Neither behavior is assumed broken from inspection.

### tests/test_v51_traceability.py: 1 instance

| Planned node | Instances | Planned markers / leg | Check |
|---|---:|---|---|
| test_acceptance_matrix_references_existing_test_functions | 1 | none / parallel, pure | the brief's no-subprocess module-import/function-name form |

T9 chooses function-address validation by importing each referenced test module
and checking the named test callable. Parameterized function addresses represent
their instances; the report names the parameter sets. The final gate collection
verifies the expanded node ids and the three-leg union. T9 will not invoke a new
pytest subprocess or require a collection file to pre-exist in light runs.
Negative stale-name controls can live inside this node without extra collection.

Provisional total: **37 instances** (photo 14 + video 20 + shell 2 + traceability
1). With the tentative marker choices above: **14 parallel candidates, 23 serial**,
**0 new fullclip**; slow 22, gui 2, footage 2, gpu 1 (marker counts overlap).
If a measured duration moves a node across the 5 s boundary, update this ledger
and the final report; do not treat this provisional split as gate evidence.
The 180 s serial delta is unmeasured and potentially at risk with the unmodified
45-frame fixtures and real trim. Report excess to CHARC rather than excluding tests.

## Anticipated RUN REQUESTs

No seat run is requested now: the nodes do not exist and the four rulings are
pending. The commands below name the expected later requests, runnable from
this worktree root in Git Bash, with PYTEST_ADDOPTS unset. Each redirects runner
output to a worktree file. Seat runs do not need the cell's sandbox mkdir shim;
cell pytest runs always use that shim and exclude gpu/footage/gui/fullclip.
Wall-time values are scheduling estimates only, to be replaced by measurements.

After T4, to establish photo node markers and crash observability (roughly
30-120 s, or longer if all 20 attempts run):

```bash
PYTHONPATH=scripts uv run pytest -q -rs tests/test_v51_photo_acceptance.py --basetemp=work/wp5.1-seat-photo --durations=0 --junitxml=work/wp5.1-seat-photo.xml > work/wp5.1-seat-photo.log 2>&1
```

After T6, the metadata-track trim node (roughly 30-120 s with usable GPU;
CPU fallback may take several minutes):

```bash
PYTHONPATH=scripts uv run pytest -q -rs tests/test_v51_video_acceptance.py::test_v4_real_trim_records_best_effort_presence --basetemp=work/wp5.1-seat-metadata --durations=0 --junitxml=work/wp5.1-seat-metadata.xml > work/wp5.1-seat-metadata.log 2>&1
```

After T8, T7's GPU form (roughly 20-90 s, depending on R0-4 and host conditions):

```bash
PYTHONPATH=scripts uv run pytest -q -rs tests/test_v51_video_acceptance.py::test_n10_video_gpu_render_digests_repeat_and_match_cpu --basetemp=work/wp5.1-seat-gpu --durations=0 --junitxml=work/wp5.1-seat-gpu.xml > work/wp5.1-seat-gpu.log 2>&1
```

After T8, the two shell legs (roughly 30-150 s; real-trim CPU analysis may be
longer; no EXCLUSIVE window or WP5.3 build piece running):

```bash
PYTHONPATH=scripts QT_QPA_PLATFORM=offscreen uv run pytest -q -rs tests/test_v51_shell_acceptance.py --basetemp=work/wp5.1-seat-shell --durations=0 --junitxml=work/wp5.1-seat-shell.xml > work/wp5.1-seat-shell.log 2>&1
```

For marker decisions the dispatcher will run each new node alone as necessary,
using the explicit ids above (and parameter ids once collected), a distinct
basetemp/log per invocation, and --durations=0. Full-module durations do not
replace the required isolated measurement. At the final candidate, measure all
new marked instances in the leg for the serial delta, retaining JUnit properties
for best-effort presence, N10 file identity and V18 pixel change.

Final seat gate remains the dispatch's ONE parallel + serial + fullclip run
after A converges and B returns, with collection identity, lint, format, mypy
and LF checks. Expected order of magnitude: 35 min for the two existing legs
plus about 26 min fullclip, plus the new delta; not a new measured promise.
Do not start that gate during the development turns. No harness gate is needed
for the owned file set.

## T1 validation and verification record

All runner outputs were redirected into work/wp5.1. Only summary lines were
read back; the files below are gitignored evidence, not added deliverables:

| Evidence file name | Run / observed summary |
|---|---|
| t1-uv-sync.log | uv sync: exit 0; resolved 62 packages in 1 ms, audited 61 in 7 ms; no tracked dependency diff |
| t1-pose-probe.log | independent Pillow/recipe read: exit 0, all 8 JPEG max errors 3 levels; non-identity pose controls distinguish content/shape |
| t1-photo-runner-probe.log | main photo reproductions: both exit 0; PNG16 output 1,881 bytes; neutral JPEG max 0 from source decode, 3 from pristine recipe |
| t1-truncated-runner-probe.log | main video batch reproduction: exit 0; truncated done with warnings, following good fixture done |
| t1-manifest.log | synthetic fixture manifest inspection: exit 0; source sizing and pose facts recorded; no owner-file read |
| t1-ledger-validation.log | citation targets/line bounds valid; LF-only and no absolute-path spelling; git status lists only the new ledger |

Verification loop: suspected JPEG-bound mismatch, unreachable disk-full trigger,
truncated-outcome conflict and fixture-sizing ambiguity; independently confirmed
by the above probes/spec/generator traces; rejected as false positives: none;
fixed: none (ruling required); routed: all four to CHARC via final report.
No product defect is established by those four brief findings. No pytest/lint/
mypy or whole-suite gate result is claimed for a documentation-only T1 turn.
No footage, GPU or GUI run was attempted. No other worktree was accessed.

## Cumulative review rounds

Round 0 is a mapping/premise audit, not a counted Reviewer A round. Severity is
relative to the acceptance brief: a false acceptance oracle blocks its build.

| Round | Critical | Major | Minor | In / out envelope | NEW / REOPENED | Reverts | Fix surface | Transport / model | Verdict |
|---|---:|---:|---:|---|---|---:|---|---|---|
| 0 / T1 | 0 | 4 | 0 | 4 / 0 | 4 / 0 | 0 | ledger only; no test/product fix | no external reviewer yet | STOP for R0-1 through R0-4; yield before T2 |

For every future Reviewer A round, adjudicate every finding in a ledger-only
turn and yield before remediation. Track product-code versus test-only fixes
(product changes prohibited here), evidence names, reopened findings and depth.
At round 5 and every five thereafter, yield for the dispatcher's continuation
ruling; evaluate depth near 200K and stop at a step boundary near 250K.

## Depth table (dispatcher-owned figures)

| Turn / boundary | Session id | depth_input_tokens | Dispatcher action |
|---|---|---|---|
| 1 / T1 round 0 | pending dispatcher | pending dispatcher | read footer; rule on R0-1 through R0-4 before T2 |
| 1 / retirement | `01a1962f-69c6-...` (dispatcher supplied abbreviation) | 210,098 | CHARC concurred with a fresh session for T2 onward |
| 2 / T2 build | `01a1963b-002e-7cc3-9d5d-0f7807bb5ed9` | 136,776 | T2 committed as `087892d8`; CHARC `755ef1b004b92902` resolved T2-1 with the in-flight tightening |
| 3 / T2-1 amendment | `01a1963b-002e-7cc3-9d5d-0f7807bb5ed9` | 155,324 | committed as `9d662f09` (0 CR); CHARC `da72ec040fc4de35` resolved T3-1 |
| 4 / T3-1 amendment | `01a1963b-002e-7cc3-9d5d-0f7807bb5ed9` | 178,501 | committed as `0d310b87` (0 CR); CHARC `8276adb56f541a57` resolved T4-1 by end state |
| 5 / T4 complete; session 2 ends | `01a1963b-002e-7cc3-9d5d-0f7807bb5ed9` | 194,928 | retired after `93869f4c`; fresh session 3 starts T5 from this ledger |
| 6 / T5-T6 product STOP; session 3 starts | `01a19671-ba33-7f71-a3ee-47dd1c74f2db` | 120,480 | committed `462d7bb6` (0 CR); CHARC `3a1497d6` permits T6/T7 continuation with T6-1 KNOWN RED, owned by WP-D54 |
| 7 / T6 validation | `01a19671-ba33-7f71-a3ee-47dd1c74f2db` | 143,997 | committed `7687f564` (ledger, 0 CR); brief amendment `1ed04a21` folds in CHARC's T6-1/T6-2 rulings |
| 8 / T6-2 remediation and T7; session 3 ends | `01a19671-ba33-7f71-a3ee-47dd1c74f2db` | 177,474 | retired after `2f1c0954`; fresh session 4 starts T8 from this ledger |
| 9 / T8; session 4 starts | `01a1968e-ac9f-7f81-aecc-78a4b492c479` | 91,630 | committed `84a030a1` (0 CR); seat format check and both GUI nodes pass |
| 10 / T8 seat result and T9 | `01a1968e-ac9f-7f81-aecc-78a4b492c479` | pending dispatcher | read footer; Reviewer A round 1 at the seat follows this yield; evaluate near 200K, stop near 250K at a step boundary |

Next authorized build group after rulings: T2 support + photo RED, then yield.
Later yields remain after T4, T6, T8, every adjudicated review round, and before
T10. The final report will explicitly retain pending V2/CP5, V12/v2, V15/V16
WP5.2, unavailable real-static V3 evidence and the final-rebase DR-98 status.

## Session 2 / Turn 2: T2

### Session boundary and scope

This is the fresh session authorized by CHARC's re-seat ruling. Session 1
retired at the dispatcher-supplied depth **210,098**. No depth for session 2
has yet been supplied; none is estimated here. Inspected base: `d8778fa6`.
The four round-0 dispositions above now reflect ruling `cdeefe5fb8114b0c`.
The historical T1 evidence and roster have not been re-derived.

Built this turn:

- `tests/acceptance_support.py`: file-backed in-process main and subprocess
  helpers, explicit output/settings/cache/record arguments, recursive names-only
  checks, source MD5, Pillow/FFmpeg RGB8 PNG readers and output Orientation check.
  Future video consumers have the paired FFmpeg decode, fidelity/roster check,
  best-effort presence extraction, PNG/MP4 provenance readers and an IF-3
  delegating returned-render digest wrapper. T2 exercises the photo subset;
  video consumers and their validation remain T5-T8 work. `ACCEPTANCE_NODES`
  explicitly has pending empty rows for V1-V18, N10 and D91; T9 populates it with
  verified node addresses alongside the report. No pending row claims a pass.
- `tests/test_v51_photo_acceptance.py`: the exact 14 planned instances: eight
  JPEG two-reader/source-pose nodes, four HEIC two-reader/AD-24 nodes, real PNG
  ENOSPC and real runner-process crash/startup cleanup. Every source is guarded
  by a before/after MD5, including all 40 scratch batch copies for the crash.
- Runner forms are in-process main for all 13 photo/ENOSPC cases and the shipped
  script in a subprocess for the crash. No product module or existing test was
  changed. Every test write is under its own tmp_path; raw decode files and
  logs are there too. Evidence scripts/logs outside the node roots stay under
  the allowed gitignored work folder. The footage folder was not opened.

### T2-1 [MAJOR, NEW, in envelope]: the crash oracle rejects completed batch items

**STOP to CHARC. Recommended ruling:** allow already committed, complete PNGs
from the 40-item batch, including a commit racing with detection/kill; verify
those finals are complete and preserved, require no partial final, and require
startup to remove every remaining temporary. Keep the 10 ms polling and real
runner process. This would amend the literal "nothing else new" assertion;
it has NOT been applied to the committed node.

Failing node:
`tests/test_v51_photo_acceptance.py::test_v11_photo_crash_leftovers_are_cleaned_at_start`.
Assertion retained verbatim in meaning: **"crash produced a new final output"**.
The node currently fails before its cleanup assertions and planted-leftover
negative control. It is neither skipped nor xfailed. No product defect is yet
established by this assertion.

Reproduction on the shipped product, with no injected hold or product change:

1. The full new module run, `t2-photo.log` / `t2-photo.xml`, observed a temporary
   on attempt 1 and failed. Four complete finals (`photo-00_corrected.png`
   through `photo-03_corrected.png`) existed beside a temporary belonging to
   `photo-03`. The latter is consistent with kill between safe-write link and
   unlink; the files alone do not prove the exact instruction at kill.
2. The isolated same-node rerun, `t2-crash-repro.log` / `t2-crash-repro.xml`,
   also observed a temporary on attempt 1 and failed the same assertion.
   Seven complete finals (`photo-00_corrected.png` through
   `photo-06_corrected.png`) existed beside the temporary for `photo-07`.
   The runner stderr ends at `[8/40] Writing photo-07.png`. This independently
   shows that the poll can miss the first items' short-lived temporaries.
3. Independent inspection in `t2-inspect.log`: Pillow verify AND full decode
   succeeded on every final in both reproductions; all were 96 x 64. On copies
   of those output folders under each node's temporary root, the shipped
   `clean_leftovers(Settings(output_folder=...), WriteJournal(...))` removed
   exactly the temporary and preserved every completed final and sentinel
   byte-identically. The original failing evidence folders were retained.

The brief selected 40 copies of the largest fixture. The manifest's largest
committed still area is a tie at 96 x 64; the node checks that the chosen
`png16-gradient-srgb` is in that maximum-area tie. It was not enlarged or
replaced. A 10 ms poll detects a later in-flight item after completed earlier
items, making the literal crash oracle reject safe completed outputs. Raising
the polling rate, adding a hold, accepting completed outputs or changing the
fixture would each need a ruling here; none was substituted silently.

### Per-node results, controls and marker measurements

Every row below has the file prefix `tests/test_v51_photo_acceptance.py::`.
The isolated seconds are JUnit testcase elapsed time (setup + call + teardown),
read from `t2-isolated-1.xml` through `t2-isolated-13.xml`, in roster order.
They are sandbox development observations, not an exclusive hardware figure or
the final owner's leg measurement. These 13 nodes have no marker and are
parallel candidates under AD-30 (< 5 s individually). The crash keeps its
mandated slow marker even though this failing development attempt is short.

| Node | Marker / leg | Result | Isolated seconds | Passing-oracle probe |
|---|---|---|---:|---|
| test_v5_jpeg_two_readers_and_pose[land-o1] | none / parallel | GREEN-ON-ARRIVAL | 0.130 | reversed output rejected |
| test_v5_jpeg_two_readers_and_pose[land-o3] | none / parallel | GREEN-ON-ARRIVAL | 0.141 | reversed output rejected |
| test_v5_jpeg_two_readers_and_pose[land-o6] | none / parallel | GREEN-ON-ARRIVAL | 0.131 | reversed output rejected |
| test_v5_jpeg_two_readers_and_pose[land-o8] | none / parallel | GREEN-ON-ARRIVAL | 0.135 | reversed output rejected |
| test_v5_jpeg_two_readers_and_pose[port-o1] | none / parallel | GREEN-ON-ARRIVAL | 0.127 | reversed output rejected |
| test_v5_jpeg_two_readers_and_pose[port-o3] | none / parallel | GREEN-ON-ARRIVAL | 0.139 | reversed output rejected |
| test_v5_jpeg_two_readers_and_pose[port-o6] | none / parallel | GREEN-ON-ARRIVAL | 0.130 | reversed output rejected |
| test_v5_jpeg_two_readers_and_pose[port-o8] | none / parallel | GREEN-ON-ARRIVAL | 0.126 | reversed output rejected |
| test_v5_heic_two_readers_and_ad24[both] | none / parallel | GREEN-ON-ARRIVAL | 0.126 | reversed output rejected |
| test_v5_heic_two_readers_and_ad24[irot-only] | none / parallel | GREEN-ON-ARRIVAL | 0.123 | reversed output rejected |
| test_v5_heic_two_readers_and_ad24[exif-only] | none / parallel | GREEN-ON-ARRIVAL | 0.133 | reversed output rejected |
| test_v5_heic_two_readers_and_ad24[neither] | none / parallel | GREEN-ON-ARRIVAL | 0.133 | reversed output rejected |
| test_v11_png_disk_full_removes_partial_output | none / parallel | GREEN-ON-ARRIVAL | 0.142 | missing ENOSPC rejected |
| test_v11_photo_crash_leftovers_are_cleaned_at_start | slow / serial | FAIL, T2-1 | 0.91 call | planned planted-leftover probe not reached |

Photo probe details (committed within each respective green node, actually run):

- All 12 outputs were pixel-identical between Pillow RGB conversion without
  transpose and FFmpeg RGB24, and had output Orientation absent or 1. All JPEG
  neutral source maximum errors were **0/255**, within the retained 2/255 bound.
  Their recipe means were 0.523872-0.544488 levels. The prior round's 3/255
  pristine-recipe maximum is a lossy-fixture property, not a product bound.
- All HEIC recipe means were 0.990994-0.991753 levels; each passed the existing
  AD-24 mean < 6 and alternative-pose oracle. Stored-pose controls for container
  irot undo libheif's already applied container turn, without applying EXIF.
  Non-identity JPEG/HEIC stored poses differ by shape or > 64/255 as ruled.
- Every one of the 12 nodes also called the SAME pose assertion with its output
  reversed in both axes and observed the expected AssertionError. This covers
  the identity poses as well as the rotated ones; JUnit records the probe.
- ENOSPC: the real PNG temporary received **1,024 actual flushed bytes**, then
  the crossing write raised ENOSPC. Exit 1, failed item, source file name in the
  failure text, outputs empty, output folder empty, source MD5 unchanged.
  The injector was scoped to Path.open("wb") on a recognized temporary under
  this node's output folder; settings and record writes were unaffected.
  A second real export without that injection succeeded, and the SAME failure
  assertion rejected it at exit status. JUnit records bytes and negative probe.

### Validation and verification loop

All command output is retained in worktree evidence files; no whole log was
copied into the handoff. Commands used the sandbox mkdir shim on EVERY pytest
invocation, with cacheprovider disabled. The full-module run used the supplied
light marker expression, with durations and JUnit added.

| Evidence file(s) | Observed summary |
|---|---|
| t2-photo.log / t2-photo.xml | 13 passed, 1 failed in 3.15 s; 14 xunit2 record_property warnings; failing crash node T2-1 |
| t2-isolated-1..13.log / .xml | all 13 green nodes passed alone; xunit1 selected so no property-family warnings |
| t2-crash-repro.log / .xml | 1 failed in 1.54 s; same crash assertion; 0.91 s call; xunit1 |
| t2-inspect.log | all final PNGs independently verified/decoded; copied crash folders' startup cleanup removed exactly temporaries and preserved completed files |
| t2-ruff.log | All checks passed! for both new modules |
| t2-format.log | 2 files reformatted; seat format --check remains the dispatcher's check |
| t2-mypy.log | Success: no issues found in 146 source files |
| t2-test-mypy.log | Success: no issues found in 2 source files (new modules explicitly, MYPYPATH=tools;tests) |

Verification loop: suspected bad source-pose/two-reader transport; rejected as
false positives by independent decoded-source/reference checks and reversed-pose
probes. Suspected a disk-full fixture/injection mismatch; confirmed actual
1 KiB writes and missing-fault rejection, no product defect. Suspected crash
partial finals; independently verified every final as complete, rejected the
product-defect interpretation, and confirmed the literal crash-oracle conflict
T2-1 on both module and isolated runs. Fixed: one test-helper Any-return type
error and formatting/import order. No product fix, tolerance relaxation, skip or
xfail was introduced. No full acceptance/gate pass or crash cleanup-node pass is
claimed. The crash node and its negative control remain blocked by the ruling.

Review status: no Reviewer A round has yet run on the T2 diff. This build-turn
finding is not a counted Reviewer A round. Its ledger classification is
Critical 0 / Major 1 / Minor 0; in-envelope 1 / out 0; NEW 1 / REOPENED 0;
reverts 0; product-code fixes 0; test-only additions 2 modules.

Yield: T2 complete as test construction, **STOP T2-1 before T3/T4 continuation**.
No seat run is requested until CHARC rules on the retained failing crash oracle.
The final gate, footage/GPU/GUI runs, final serial-leg delta and T9/T10 remain
pending at their authorized boundaries.

## Session 2 / Turn 3: T2-1 amended, T4 complete

Intended T4 completion is **BLOCKED by T3-1 below**; the heading names the
dispatched milestone, not a passing acceptance claim. T2 was committed by the
dispatcher as `087892d8`, with zero CR in the three blobs. The supplied session
2 id and depth after T2 (136,776) are recorded in the depth table. This turn's
depth is not estimated. Evaluate near 200K; stop at a step boundary near 250K.

### Ruling applied and delivered change

CHARC `755ef1b004b92902` resolved T2-1 and withdrew "nothing else new". The
crash node now implements its five amended assertions without a relaxation:

1. Every non-sentinel, non-temporary file in the output folder is opened with
   Pillow verify, reopened for full decode, and checked against 96 x 64. Its
   MD5 is saved before cleanup and compared after cleanup.
2. A partial final causes an assertion failure, including a truncated PNG.
3. The last `[n/40] Writing photo-NN.png` line in the actual runner stderr
   identifies the in-flight source. Its index is checked against the batch,
   its stem is matched against the observed temporary, and its final must be
   ABSENT before cleanup. No inference solely from the temporary replaces
   the required stderr identification.
4. The shipped clean_leftovers must remove exactly all remaining temporaries,
   report no failed removal, and preserve all verified finals and the sentinel
   byte-identically. The prior planted-leftover negative remains in the node.
5. The original fixture and all 40 scratch copies retain their source MD5s in
   the finally guard, including on a failing assertion.

The real runner subprocess, maximum-area fixture tie, 40-copy batch, 10 ms
polling, 20-attempt ceiling and exact allowed skip reason are unchanged.
Each attempt records its verified completed-final count in a JUnit property,
including attempts where no temporary was seen. No bound is imposed on that
count. There was one attempt in this turn; it observed a temporary and failed,
so the unobserved-temporary skip is not applicable.

The committed node includes two new negative probes against its SAME
pre-cleanup assertion, planting a truncated final beside the real temporary
and a valid final for the in-flight item. It fails the actual-product assertion
before reaching those probes. Both probes were therefore also exercised
independently on a separate planted folder under the failing node's temp root;
the original failure folder was only read by that inspection. Details below.

### T3-1 [MAJOR, NEW, in envelope]: kill can interrupt link-before-unlink commit

**STOP to CHARC. Recommended ruling:** classify a fully verified, successfully
installed final as completed even when its temporary hard link remains after
kill; allow that state when temporary and final refer to the same file and
startup removes only the temporary. Keep the prohibition on a partial final.
This requires amending the in-flight tightening. It has NOT been applied.

Failing node remains:
`tests/test_v51_photo_acceptance.py::test_v11_photo_crash_leftovers_are_cleaned_at_start`.
Actual assertion: **"in-flight item has a final before cleanup"**.
The failing node is retained, with no xfail, retry on a failed observation,
tolerance change, hold hook, smaller poll interval or product edit.

Evidence from `t3-photo.log`, `t3-photo.xml` and `t3-inspect.log`:

- Attempt 1: the runner's last writing line is
  `[3/40] Writing photo-02.png`. The observed temporary is
  `photo-02_corrected.clearwater-partial-ea178a35f2b4.png`, matching that source.
- Three completed finals exist: `photo-00_corrected.png`,
  `photo-01_corrected.png` and `photo-02_corrected.png`. Pillow verify AND full
  decode independently succeeded on all three, each 96 x 64.
- The in-flight final `photo-02_corrected.png` and its temporary have the
  **same file identity** (os.path.samefile True) and the **same MD5**. Thus this
  run caught a successfully installed final while its temporary name survived.
- The read-only source trace is `src/clearwater/jobs/safe_write.py:88`:
  `_install` calls `os.link(temp, final)` at `:101`, then `_unlink_quietly(temp)`
  at `:107`. The observed two names for the same complete file agree with kill
  in that interval. No source edit is proposed or made here.
- The source MD5 finally guard did not fail. The real node stops before its
  cleanup call; no passing cleanup result is claimed for this run.

This is additional evidence about the tightened oracle, not evidence of a
partial final. The prior race characterisations **4 and 7** completed finals
remain in the T2 record for the final report; this run adds **3** (including
the installed final with a surviving temporary hard link). No bound is proposed
on those counts. No product defect is established from this complete-file state.

Independent planted-failure probes, `t3-inspect.log`:

- A copied real temporary plus sentinel, with no final, first passed the same
  `_assert_crash_before_cleanup` baseline in its own scratch folder.
- A 32-byte truncated PNG planted as another final beside that temporary was
  rejected with **"crash left a partial final: planted-truncated.png"**.
- After removing that truncation, a copied VALID completed PNG planted at the
  in-flight final name was rejected with **"in-flight item has a final before
  cleanup"**. This proves that the third assertion is distinct from the
  completeness check. Probe files were removed in finally blocks; the original
  failing evidence folder and all its files were retained unchanged.

### Per-node result and time on this base

File prefix for each node is `tests/test_v51_photo_acceptance.py::`.
Times are JUnit testcase seconds (setup + call + teardown), from the full-module
light run on this candidate, not fresh isolated measurements. T2's isolated
figures remain the marker evidence; these are development observations only.

| Node | Marker / leg | Result | Seconds |
|---|---|---|---:|
| test_v5_jpeg_two_readers_and_pose[land-o1] | none / parallel | PASS | 0.197 |
| test_v5_jpeg_two_readers_and_pose[land-o3] | none / parallel | PASS | 0.143 |
| test_v5_jpeg_two_readers_and_pose[land-o6] | none / parallel | PASS | 0.146 |
| test_v5_jpeg_two_readers_and_pose[land-o8] | none / parallel | PASS | 0.136 |
| test_v5_jpeg_two_readers_and_pose[port-o1] | none / parallel | PASS | 0.126 |
| test_v5_jpeg_two_readers_and_pose[port-o3] | none / parallel | PASS | 0.138 |
| test_v5_jpeg_two_readers_and_pose[port-o6] | none / parallel | PASS | 0.118 |
| test_v5_jpeg_two_readers_and_pose[port-o8] | none / parallel | PASS | 0.105 |
| test_v5_heic_two_readers_and_ad24[both] | none / parallel | PASS | 0.118 |
| test_v5_heic_two_readers_and_ad24[irot-only] | none / parallel | PASS | 0.109 |
| test_v5_heic_two_readers_and_ad24[exif-only] | none / parallel | PASS | 0.113 |
| test_v5_heic_two_readers_and_ad24[neither] | none / parallel | PASS | 0.119 |
| test_v11_png_disk_full_removes_partial_output | none / parallel | PASS | 0.134 |
| test_v11_photo_crash_leftovers_are_cleaned_at_start | slow / serial | FAIL, T3-1 | 0.929 |

### Validation and verification loop

Command for the full photo-module run (stdout/stderr redirected to
`work/wp5.1/t3-photo.log`):

```bash
PYTHONPATH=scripts uv run pytest -q tests/test_v51_photo_acceptance.py --basetemp=work/wp5.1/t3-tmp -p sandbox_mkdir_shim -p no:cacheprovider -m "not gpu and not footage and not gui and not fullclip" --durations=0 -o junit_family=xunit1 --junitxml=work/wp5.1/t3-photo.xml
```

| Evidence | Observed summary |
|---|---|
| t3-photo.log / t3-photo.xml | 13 passed, 1 failed in 3.33 s; failure is the tightened in-flight assertion; no skip |
| t3-inspect.log | all three finals verify/decode; in-flight final/temporary same file and bytes; both requested negative probes rejected |
| t3-ruff.log | All checks passed! for both new modules |
| t3-format.log | Only the owned photo module formatted; seat format --check remains pending |
| t3-test-mypy.log | Success: no issues found in 2 source files |
| t3-mypy.log | Success: no issues found in 146 source files |

Verification loop: suspected that the amendment would distinguish completed
batch items from the in-flight item; confirmed that parsing identifies the
correct source, but the last writing line does not distinguish commit's
link/unlink interval from an uncommitted write. Independently confirmed file
completeness, equal MD5 and equal file identity; rejected partial-output product
defect as a false positive for this observation. Confirmed both requested
negative probes against the node's exact assertion helper. Fixed: test-only
oracle amendment per CHARC, with no product change. Remaining: T3-1 ruling.

No Reviewer A round has run in this turn. This new build finding is Critical 0 /
Major 1 / Minor 0; in-envelope 1 / out 0; NEW 1 / REOPENED 0 (T2-1's withdrawn
blanket assertion was resolved; this is the new in-flight tightening); reverts
0; product fixes 0; test-only modification 1 module. Only that owned test module
and this ledger changed. No existing test, support module, configuration,
dependency, frozen interface, footage file or other worktree was changed or
opened. No commit or git-index write was attempted.

Yield: **STOP T3-1**, as required when the amended node fails on the shipped
product. T4 is not claimed complete. No further build task or seat run is
requested before the ruling; no whole-set gate was run.

## Session 2 / Turn 4

### Scope, ruling and change

The dispatcher supplied depth **155,324** after T3 and commit `9d662f09`
(zero CR); both are now in the depth table. This turn's depth is not estimated.
T3-1 was resolved by CHARC `da72ec040fc4de35`. Applied only the authorized
test changes to assertions (3) and (4):

- The in-flight source is still identified from the actual runner stderr,
  checked against its batch index, and matched to the observed temporary.
  A present final is allowed ONLY if a surviving temporary for that final
  passes os.path.samefile AND MD5 identity. The final still undergoes Pillow
  verify, full decode and expected-dimension checks. An absent final is allowed.
- After shipped clean_leftovers, every remaining temporary NAME must be gone.
  In the installed-final branch the final must explicitly remain a file and
  retain its before-cleanup MD5. All other finals are reverified and compared
  with their pre-cleanup digests, and the sentinel and exact output-name set
  must remain unchanged. Assertions (1), (2) and (5) remain in force.
- The new unrelated-final negative probe uses two byte-identical but distinct
  files, ensuring that equal content alone cannot satisfy the same-file branch.
  Probes moved into a separate folder under the node's temporary root so they
  cannot overwrite, unlink or alter the REAL installed final before cleanup.
- Each attempt records its completed-final count and state. Successful observed
  branches are `no final` / `same-file final`; the additional rejected state
  `final without same-file temporary` is recorded diagnostically before the
  assertion. An unobserved attempt records `no temporary observed`.

The fixture, 40 copies, actual runner process, 10 ms poll and 20-attempt skip
rule remain unchanged. No failed observed state is retried or softened. T4
remains blocked by the new state below; **T5 was not started** because the
photo node failed, independently of depth headroom.

### T4-1 [MAJOR, NEW, in envelope]: the temporary can disappear before kill

**STOP to CHARC. Recommended ruling:** recognize a third valid commit state,
complete final with NO surviving temporary, and apply the same verification,
before/after byte identity and cleanup-preservation requirements to it. The
poll can observe a temporary whose commit finishes before the process is
killed. That is different from a surviving temporary beside an unrelated
final, which must still fail. This recommendation is NOT applied to the node.

Failing node:
`tests/test_v51_photo_acceptance.py::test_v11_photo_crash_leftovers_are_cleaned_at_start`.
Actual assertion: **"in-flight final is not the same file as a surviving
temporary"**. Under the ruling's literal disjunction, it correctly rejects a
present final with no surviving temporary. It remains failing, without xfail
or skip. No product defect is established from the observed complete-file state.

Evidence: `t4-photo.log`, `t4-photo.xml`, `t4-inspect.log`:

- Attempt 1 observed
  `photo-04_corrected.clearwater-partial-577d968ceb79.png`, matching stderr's
  last writing line, `[5/40] Writing photo-04.png`.
- After kill there were **five** completed finals (`photo-00_corrected.png`
  through `photo-04_corrected.png`) and **zero** temporary names. Independent
  Pillow verify plus full decode succeeded on all five, all 96 x 64.
- The original fixture and all 40 copies passed the node's source-MD5 finally
  guard. The real node failed BEFORE clean_leftovers, so no real-crash cleanup
  PASS or D85 cleanup defect is claimed for this run.
- Source mechanic: `src/clearwater/jobs/safe_write.py:101` installs the final
  link, then `:107` unlinks the temporary. The observed absence of the temporary
  and presence of a complete final are consistent with a commit that finished
  between directory observation and process termination. A last Writing line
  does not prove the item remained uncommitted at the actual kill instant.
- After adding diagnostic state recording (assertions unchanged), the final
  candidate's exact pre-cleanup helper was re-applied read-only to the retained
  real output folder and rejected the same state with the same assertion.
  The full module was not rerun to seek a different race outcome.

Race characterisation for the eventual report: prior completed-final counts
**3, 4, 7** remain of record; this run adds **5**. The observed states now
include no-final, same-file final and final-without-surviving-temporary in the
branch probes/real evidence as explicitly distinguished below. No bound on
completed-final count is introduced.

### Requested branch probes and cleanup evidence

The committed negative probes follow the same helper used by the real node,
but the actual failure precedes them. Independently exercised those branches
against the final candidate in a scratch sibling under the failing node's
temporary root; the actual output folder was not modified. `t4-inspect.log`
records:

1. A valid file under a recognized temporary name, with no final: accepted by
   the node's exact pre-cleanup helper.
2. A 32-byte truncated final beside that temporary: rejected as a partial final.
3. A valid byte-identical COPY at the in-flight final name: MD5 equal, samefile
   False, rejected by the new same-file assertion. The copy was then removed.
4. A hard link at the in-flight final name: samefile True, accepted by the
   helper after verify/decode/dimension checks. An additional valid earlier
   final and sentinel were planted beside it. The actual shipped clean_leftovers
   removed exactly the temporary NAME, reported no failed removal, and left
   the installed final, earlier final and sentinel present and byte-identical.

Thus the newly authorized same-file branch and its cleanup addition have
positive planted evidence, and the unrelated-final branch has the requested
negative evidence. This is separate from the real-run node, which is still RED
on the final-without-temporary state and has not passed its full cleanup leg.

### Per-node result and time

Prefix for each node: `tests/test_v51_photo_acceptance.py::`.
JUnit elapsed seconds include setup/call/teardown for the full-module run;
these are sandbox observations, not an isolated marker remeasurement or a
hardware figure of record. Existing marker choices remain unchanged.

| Node | Marker / leg | Result | Seconds |
|---|---|---|---:|
| test_v5_jpeg_two_readers_and_pose[land-o1] | none / parallel | PASS | 0.141 |
| test_v5_jpeg_two_readers_and_pose[land-o3] | none / parallel | PASS | 0.105 |
| test_v5_jpeg_two_readers_and_pose[land-o6] | none / parallel | PASS | 0.102 |
| test_v5_jpeg_two_readers_and_pose[land-o8] | none / parallel | PASS | 0.101 |
| test_v5_jpeg_two_readers_and_pose[port-o1] | none / parallel | PASS | 0.101 |
| test_v5_jpeg_two_readers_and_pose[port-o3] | none / parallel | PASS | 0.103 |
| test_v5_jpeg_two_readers_and_pose[port-o6] | none / parallel | PASS | 0.102 |
| test_v5_jpeg_two_readers_and_pose[port-o8] | none / parallel | PASS | 0.100 |
| test_v5_heic_two_readers_and_ad24[both] | none / parallel | PASS | 0.105 |
| test_v5_heic_two_readers_and_ad24[irot-only] | none / parallel | PASS | 0.108 |
| test_v5_heic_two_readers_and_ad24[exif-only] | none / parallel | PASS | 0.109 |
| test_v5_heic_two_readers_and_ad24[neither] | none / parallel | PASS | 0.112 |
| test_v11_png_disk_full_removes_partial_output | none / parallel | PASS | 0.128 |
| test_v11_photo_crash_leftovers_are_cleaned_at_start | slow / serial | FAIL, T4-1 | 0.914 |

### Validation, verification and handoff

The full photo-module light command included slow nodes, used the mandatory
sandbox mkdir shim and disabled cacheprovider. Basetemp was
`work/wp5.1/t4-tmp`, with durations and xunit1 JUnit added. All output went to
worktree files; no full runner log is copied into the handoff.

| Evidence | Observed summary |
|---|---|
| t4-photo.log / t4-photo.xml | 13 passed, 1 failed in 2.94 s; no skip; observed-final count 5 |
| t4-inspect.log | retained real state rejected by final candidate helper; no-final/same-file branches accepted; unrelated copy and truncated final rejected; shipped same-file cleanup preserved installed/earlier finals and sentinel |
| t4-ruff.log | All checks passed! for the two new modules, after final test edit |
| t4-format.log | Only the owned photo module formatted; seat format --check pending |
| t4-test-mypy.log | Success: no issues found in 2 source files, after final test edit |
| t4-mypy.log | Success: no issues found in 146 source files |

Verification loop: confirmed implementation of the authorized same-file and
cleanup branches with positive and negative planted evidence. Suspected a
product partial/final preservation defect in the real run; independently
verified all five finals and no surviving temporary, rejecting that product
interpretation for this observation. Confirmed instead the new poll-to-kill
post-commit state that the ruled disjunction excludes. Fixed only the authorized
test assertions/probes and diagnostic recording. T4-1 remains for CHARC; no
additional acceptance branch was guessed or silently allowed.

No Reviewer A round ran this turn. Build finding: Critical 0 / Major 1 /
Minor 0; in-envelope 1 / out 0; NEW 1 / REOPENED 0 (T3-1's same-file state was
resolved; this is the distinct state with no surviving temporary); reverts 0;
product-code fixes 0; test-only modification 1 module. Only that owned module
and this ledger changed. No product/existing-test edit, new dependency, tolerance
change, configuration edit, footage-folder read, other-worktree access, mailbox
post, commit or git-index write occurred.

Yield: **STOP T4-1**. T4 is not claimed green or complete; T5 remains unstarted.
No further task or seat run is requested before the ruling. The whole-set gate,
Reviewers A/B and remaining acceptance work are still pending.

## Session 2 / Turn 5: T4 complete (session 2 ends)

### Final ruling applied

Inspected base: `0d310b87` (dispatcher: zero CR). The dispatcher supplied
**178,501** as session 2's depth after T4; the depth table records it. This is
the LAST turn of session 2, as directed. No current-depth estimate is made.

CHARC `8276adb56f541a57` resolves T4-1 with the final end-state oracle:

- All finals in every attempt still undergo Pillow verify, full decode and
  expected-dimension checks. Sources retain their MD5 guards.
- The source named by the last real stderr Writing line may have no final,
  a complete final sharing identity AND bytes with its surviving temporary,
  or a complete final with no surviving temporary for that item. A present
  unrelated final beside a surviving temporary still fails. Temporary
  observation and the last stderr line are recorded independently: a job
  can advance between polling and termination, so the earlier snapshot is
  not used to impose an extra in-flight correspondence assertion.
- Every attempt records completed-final count, observed and surviving
  temporary names, the stderr-named source and end state. A recorded attempt
  without a surviving temporary is retried within the existing 20 attempts.
  No cleanup is invoked on a clean output folder as a crash witness. An
  unobserved, normally completed process is likewise recorded and retried.
  Twenty attempts without a surviving crash temporary still skip with the
  exact reason `not observable at this size`.
- Once a killed attempt leaves at least one temporary, shipped clean_leftovers
  must remove every temporary NAME and preserve every verified final and the
  sentinel byte-identically. The node explicitly checks the installed final
  remains present and unchanged when that branch is observed.
- The largest-fixture tie, 40 copies, 10 ms polling, real runner subprocess,
  output folders, source guards and 20-attempt limit are unchanged.

### Committed deterministic D85 witness

Added the independent parallel-leg node:
`tests/test_v51_photo_acceptance.py::test_d85_same_file_cleanup_preserves_installed_final`.

It copies the committed fixture under a valid temporary name under tmp_path,
plants another complete final and a sentinel, and first demonstrates the
negative control: a byte-identical COPY at the in-flight final name has a
different file identity and is rejected by the same pre-cleanup oracle. It
then replaces that test-only copy with a HARD LINK to the temporary, verifies
the shared identity and identical MD5, and runs the actual shipped
clean_leftovers. The temporary name disappears; the installed final remains
present and byte-identical; the earlier final and sentinel are unchanged.
The fixture's own source MD5 is guarded in finally.

**The deterministic probe, not the race, is the D85 witness.** The race remains
the end-to-end shipped-runner crash/leftover acceptance leg. No new product
hook, product change, dependency, fixture or existing-test edit was introduced.

The D85 node is GREEN-ON-ARRIVAL, with the requested planted unrelated-final
failure control actually executed and recorded as a property. It has no marker:
the isolated node passed in 0.63 s wall time (about 0.01 s call), below AD-30's
5 s boundary in this sandbox observation. The owner's isolated/leg measurements
remain the final scheduling figures.

### Actual crash attempts and race characterisation

Full-module run: crash node PASS in 2.035 JUnit testcase seconds. Both attempts
used fresh output folders under the node's own tmp_path and the same 40 guarded
scratch sources. Properties in `t5-photo.xml`, summarized in `t5-results.log`:

| Attempt | Last Writing source | End state | Completed finals | Surviving temporaries | Action |
|---|---|---|---:|---:|---|
| 1 | photo-00.png | complete with no temporary | 1 | 0 | recorded and retried; no cleanup call |
| 2 | photo-06.png | same-file final | 7 | 1 | actual cleanup removed the temporary name and preserved all seven finals and sentinel |

Attempt 2 observed
`photo-06_corrected.clearwater-partial-58ebbc987e5e.png`. Before cleanup its
final shared the same file identity and MD5 and verified/decoded at 96 x 64.
The shipped cleanup removed that temporary name; final and other outputs
passed the before/after checks. The crash node's planted truncated-final and
planted-leftover controls both ran and were rejected by their respective
assertions. The source MD5 finally guard passed. There was NO skip.

End states for the report are `no final`, `same-file final`, and `complete with
no temporary`. No-final was accepted in the earlier independent branch probes;
this actual run observed the latter two states. Historical real-run counts
**3, 4, 5, 7** remain race characterisations, not bounds; this run adds **1** and
another **7**. The report must distinguish branch-probe evidence from natural
race observations and retain the sentence identifying the D85 witness above.

### Per-node result and time

Every row has prefix `tests/test_v51_photo_acceptance.py::`. JUnit times are
setup + call + teardown from the full-module run, not exclusive hardware
figures. No marker choice changed except the addition of the unmarked D85 node.

| Node | Marker / leg | Result | Seconds |
|---|---|---|---:|
| test_v5_jpeg_two_readers_and_pose[land-o1] | none / parallel | PASS | 0.156 |
| test_v5_jpeg_two_readers_and_pose[land-o3] | none / parallel | PASS | 0.123 |
| test_v5_jpeg_two_readers_and_pose[land-o6] | none / parallel | PASS | 0.133 |
| test_v5_jpeg_two_readers_and_pose[land-o8] | none / parallel | PASS | 0.137 |
| test_v5_jpeg_two_readers_and_pose[port-o1] | none / parallel | PASS | 0.152 |
| test_v5_jpeg_two_readers_and_pose[port-o3] | none / parallel | PASS | 0.120 |
| test_v5_jpeg_two_readers_and_pose[port-o6] | none / parallel | PASS | 0.122 |
| test_v5_jpeg_two_readers_and_pose[port-o8] | none / parallel | PASS | 0.121 |
| test_v5_heic_two_readers_and_ad24[both] | none / parallel | PASS | 0.118 |
| test_v5_heic_two_readers_and_ad24[irot-only] | none / parallel | PASS | 0.120 |
| test_v5_heic_two_readers_and_ad24[exif-only] | none / parallel | PASS | 0.120 |
| test_v5_heic_two_readers_and_ad24[neither] | none / parallel | PASS | 0.112 |
| test_v11_png_disk_full_removes_partial_output | none / parallel | PASS | 0.138 |
| test_d85_same_file_cleanup_preserves_installed_final | none / parallel | PASS | 0.021 |
| test_v11_photo_crash_leftovers_are_cleaned_at_start | slow / serial | PASS | 2.035 |

### Validation and verification loop

Full photo-module command (stdout/stderr redirected to
`work/wp5.1/t5-photo.log`):

```bash
PYTHONPATH=scripts uv run pytest -q tests/test_v51_photo_acceptance.py --basetemp=work/wp5.1/t5-tmp -p sandbox_mkdir_shim -p no:cacheprovider -m "not gpu and not footage and not gui and not fullclip" --durations=0 -o junit_family=xunit1 --junitxml=work/wp5.1/t5-photo.xml
```

| Evidence | Observed summary |
|---|---|
| t5-photo.log / t5-photo.xml | 15 passed in 4.36 s; no skip; crash succeeds on attempt 2 |
| t5-results.log | all node times/properties; two crash end states/counts; all planted controls recorded |
| t5-d85-isolated.log / .xml | 1 passed in 0.63 s; about 0.01 s call; negative copy control and actual cleanup both pass |
| t5-ruff.log | All checks passed! for both new modules |
| t5-format.log | Only the owned photo module formatted; seat format --check remains pending |
| t5-test-mypy.log | Success: no issues found in 2 source files |
| t5-mypy.log | Success: no issues found in 146 source files |

Verification loop: suspected the observed-temporary/no-survivor race could
still bypass or falsely prove cleanup; confirmed attempt 1 was recorded and
retried without a cleanup call, and attempt 2 had a real surviving temporary
before shipped cleanup. Confirmed installed-final preservation deterministically
in the separate D85 node; independently distinguished file identity from equal
bytes with its rejected planted copy. Partial-final and leftover controls also
ran in the passing crash node. Rejected product defect: none found in this
turn. Fixed: the test-only end-state oracle and deterministic witness per final
CHARC ruling. Full pass found no new in-envelope issue. Earlier oracle STOPs
T2-1, T3-1 and T4-1 are resolved by their recorded rulings; no product fix was
needed or made.

No Reviewer A round ran in this turn. New build findings: Critical 0 / Major 0 /
Minor 0; NEW 0 / REOPENED 0; reverts 0; product-code fixes 0; test-only changes
1 module (including one added node). This is not the phase-end gate or a claim
that all WP5.1 acceptance work is complete. Only the owned photo module and
this ledger changed; no product/existing-test edit, new dependency, tolerance
change, footage-folder read, configuration edit, other-worktree access, mailbox
post, commit or git-index write occurred.

### Session boundary: session 2 retires; fresh session 3 starts T5

**T2 support and T3/T4 photo construction are complete. Session 2 ENDS at this
yield. T5 onward is assigned to a FRESH session 3 from the committed ledger.**
The dispatcher supplies the final depth/session boundary figure; do not infer
one from this text. All new photo nodes are green in the latest light run.

Handoff for session 3:

- Reuse `tests/acceptance_support.py`; its photo/main helpers have the evidence
  above. Future video helpers (decode, fidelity/best-effort, provenance and
  RenderDigests) remain scaffolding to exercise against the real consumers at
  T5-T8. Their strict typing is checked; their video acceptance behavior has
  NOT yet been claimed passing. ACCEPTANCE_NODES rows remain explicitly pending
  for T9 population alongside the report.
- Start T5: write the 20 planned video instances in the new owned video module,
  then run the sandbox-eligible ones. Keep the named committed fixtures
  unchanged (R0-4); truncated SUCCEEDS with D86 warning and readable-prefix
  fidelity (R0-3). Use the ledger's relocated anchors and roster, not another
  worktree. GPU/footage/GUI nodes are written here but run ONLY by the
  dispatcher from RUN REQUEST lines. A genuine product failure stays failing
  and yields a STOP with evidence; never xfail, soften or edit the product.
- The new D85 node changes the planned total to **38 instances**: photo 15,
  video 20, shell 2, traceability 1. Tentative split: **15 parallel candidates,
  23 serial**, zero new fullclip; slow 22, gui 2, footage 2, gpu 1 (overlap).
  The serial-leg delta and 180 s budget are still pending seat measurements.
- Carry into T9/T10 the new D85 node, final crash oracle `8276adb56f541a57`,
  the per-attempt states/counts and the deterministic-witness sentence. The
  final report file has NOT been created yet. Reviewer A/B, the final rebase,
  full matrix, two legs + one fullclip gate, collection identity, final
  format/LF checks and final DR-98 status remain the later authorized work.
- No new seat RUN REQUEST is issued in this retirement turn. The dispatcher
  controls review scheduling and the fresh-session T5 dispatch. No further
  work is authorized in session 2 after this yield.

## Session 3 / Turn 6: T5-T6

### Session boundary and build scope

Fresh session 3 starts from committed handoff `93869f4c`. Session 2 retired
after turn 5 at **194,928**, supplied by the dispatcher; the depth table is
updated. Session 3's id and this turn's depth are for the dispatcher to fill,
never estimated here. This turn builds T6 only, with T5's failure controls;
T7's two N10 instances are NOT implemented in this turn.

Added `tests/test_v51_video_acceptance.py`: **18 instances** (17 sandbox-eligible,
one footage-only). All currently carry `slow(reason="FFmpeg encode")`; the real
trim additionally carries `footage`. Scheduling markers are provisional until
the owner's isolated measurements under AD-30; some sandbox call times are
under five seconds, others exceed five seconds. No new fullclip/GPU/GUI node.

The module contains the five unchanged-container V4 cases, readable-prefix
truncated batch, real-trim best-effort presence/GPMF node, HDR refusal batch,
untagged warning, four post-encode neutral comparisons at the unchanged 2.5/255
mean bound, three numbering/collision nodes, and provenance default/off. All
runner calls are in-process `headless_export.main`, via the committed support
helper, with explicit settings/cache/record/output under tmp_path. A module
autouse fixture MD5-guards every committed video source in `finally`; the MOV
copies and real trim have additional local finally guards.

Extended support with a names-only `fidelity_record`: the existing instrument
compares the files; only its two top-level path fields become file names before
the new JSON is saved. Existing comparison facts and tolerances are unchanged.
Corrected the support presence extraction to distinguish the instrument's
`"absent"`, `{count: 0}` and dictionaries of null stream tags from present
metadata. This was unexercised scaffolding from T2, not a product change.
An independent literal probe of absent/zero/null and present/count cases passes
(`work/wp5.1/t6-evidence.log`). The actual real-trim presence result awaits the seat.

### T6-1 [MAJOR, NEW, in envelope]: D54 words missing in the real runner record

**STOP. Recommended: route the warning propagation/text defect to its owning
product package; retain this failing node and the literal BT.709/limited
assertion; resume T6 validation after CHARC's disposition.** No product fix,
xfail, tolerance increase or weakened assertion was made.

Failing node:
`tests/test_v51_video_acceptance.py::test_v6_untagged_runner_warns_bt709_limited`.

`tests/test_v51_video_acceptance.py:256` requires one item warning containing
both `BT.709` and `limited`. Export succeeds, status 0, item `done with warnings`,
but its only warning is:

> The source's colour tags are missing or unexpected; the output is tagged with the assumed values (color_primaries bt709, color_trc bt709, colorspace bt709, color_range tv).

It has neither required substring. The node remains FAILING on the shipped
product, as Q3 requires. Runner stdout/stderr and its JSON already passed the
support helper's names-only checks; this failure is the warning assertion,
not path redaction, encoding, parsing or fixture availability.

Independent confirmation: directly probing the unchanged real committed
`untagged.mp4` yields a `missing_tags` warning ending:
`Clearwater assumes BT.709 colours and limited range for those.` Evidence in
`t6-evidence.log` records both that probe fault and the actual runner warning.
Mechanic: `src/clearwater/io/video/probe.py:457` builds the missing-tags fault;
`src/clearwater/jobs/export.py:864` only forwards `gp_log` warning faults;
`src/clearwater/io/video/encode.py:668` instead adds the encoder's tag-code
message above. Those files were read only. The existing shell case with empty
words is unchanged; T8's real-shell assertion has not yet been built or run.

### Actual run and per-node evidence

The sandbox command below stopped at the first product failure. Logs and raw
outputs stay under this worktree; no footage fixture or other worktree was read.

```bash
PYTHONPATH=scripts uv run pytest -q -x tests/test_v51_video_acceptance.py --basetemp=work/wp5.1/tmp -p sandbox_mkdir_shim -p no:cacheprovider -m "not gpu and not footage and not gui and not fullclip" --durations=0 -o junit_family=xunit1 --junitxml=work/wp5.1/t6-video.xml > work/wp5.1/t6-video.log 2>&1
```

Observed summary: **1 failed, 7 passed, 1 deselected in 40.39 s**. Nine later
sandbox instances were not executed because of `-x`; they are not skips or
passing evidence. The footage node was deselected. No further export was run
after the STOP. All rows have prefix `tests/test_v51_video_acceptance.py::`.
Times are JUnit setup + call + teardown in this sandbox run, not exclusive
hardware or owner's isolated/leg figures.

| Node | Marker / leg | Result | Seconds |
|---|---|---|---:|
| test_v4_runner_preserves_fixture_fidelity[hevc8-bt709-full] | slow / serial provisional | PASS | 5.406 |
| test_v4_runner_preserves_fixture_fidelity[hevc10] | slow / serial provisional | PASS | 5.050 |
| test_v4_runner_preserves_fixture_fidelity[untagged] | slow / serial provisional | PASS | 4.813 |
| test_v4_runner_preserves_fixture_fidelity[vfr] | slow / serial provisional | PASS | 3.836 |
| test_v4_runner_preserves_fixture_fidelity[rotated] | slow / serial provisional | PASS | 5.059 |
| test_v4_truncated_runner_batch_obeys_d86 | slow / serial provisional | PASS | 7.257 |
| test_v4_real_trim_records_best_effort_presence | footage, slow / serial | NOT RUN: seat-only | pending |
| test_v6_hdr_refusals_do_not_stop_batch | slow / serial provisional | PASS | 4.120 |
| test_v6_untagged_runner_warns_bt709_limited | slow / serial provisional | FAIL: T6-1 | 4.115 |
| test_v9_neutral_runner_postencode[hevc8-bt709-full] | slow / serial provisional | NOT RUN: STOP | pending |
| test_v9_neutral_runner_postencode[untagged] | slow / serial provisional | NOT RUN: STOP | pending |
| test_v9_neutral_runner_postencode[rotated] | slow / serial provisional | NOT RUN: STOP | pending |
| test_v9_neutral_runner_postencode[hevc10] | slow / serial provisional | NOT RUN: STOP | pending |
| test_v10_repeated_video_exports_are_numbered | slow / serial provisional | NOT RUN: STOP | pending |
| test_v10_existing_video_output_is_unchanged | slow / serial provisional | NOT RUN: STOP | pending |
| test_v10_mov_mp4_share_one_numbering_sequence | slow / serial provisional | NOT RUN: STOP | pending |
| test_d91_video_provenance[default] | slow / serial provisional | NOT RUN: STOP | pending |
| test_d91_video_provenance[off] | slow / serial provisional | NOT RUN: STOP | pending |

The seven green-on-arrival nodes all executed planted-failure controls:
mandatory frame-count difference and missing roster rejected in each of the
six V4 nodes; the VFR node additionally rejected a one-microsecond change to
one rational pts after comparing ALL 30 actual rational timestamps (variable
steps also checked); the truncated batch rejected a dropped D86 warning and
an unrun following item; the HDR batch rejected generic HLG and PQ refusals
and an unrun SDR item. JUnit properties and `t6-evidence.log` retain these
results. Truncated output contains exactly the 24 readable frames; the next
item exports. All tested mandatory/required comparisons pass with zero
differences. Controls in the unrun nodes are written but NOT claimed executed.

### Validation, verification-loop record and handoff

| Evidence under work/wp5.1/ | Actual result |
|---|---|
| t6-sync.log | uv sync resolved 62 / audited 61 packages; no dependency-file change |
| t6-video.log / t6-video.xml | 7 pass, 1 product failure, 1 deselected; stopped in 40.39 s |
| t6-evidence.log | independent real-file warning, runner counts/warning, all executed properties/times; presence-helper literal probe passes |
| t6-ruff.log | All checks passed! for support and all existing new v51 modules |
| t6-format.log | owned support/video format only; seat format --check pending |
| t6-test-mypy.log | Success: no issues found in 2 source files (MYPYPATH=tools;tests) |
| t6-mypy.log | Success: no issues found in 146 source files |
| t6-collect.log | 18 test instances collected in 0.59 s; no fixture execution |
| t6-lf.log | zero CR bytes in each of the three changed files |

Verification loop: suspected missing propagation of the real probe's D54
warning; CONFIRMED by the runner failure and independent probe/source trace.
Not a false positive: the encoder warning spells neither required substring.
No product fix authorized or made; T6-1 remains open for CHARC. The passing
oracles independently rejected their planted wrong results. Fixed test-only
typing/style slips before final validation; no additional product issue was
observed before the required STOP. No complete clean verification pass, full
suite, isolated node timing sweep, serial delta or phase-end gate is claimed.

New build findings: Critical 0 / Major 1 / Minor 0; in-envelope 1 / out 0;
NEW 1 / REOPENED 0; reverts 0; product-code fixes 0; test-only files changed 2.
No Reviewer A round ran this turn; its cumulative round ledger is unchanged.
The turn bundles support extension and T6 test construction as commissioned.

Locks honored on disk: only the owned support, new video module and ledger
changed. No product/existing-test edit, dependency, committed fixture, frozen
interface, local-config edit, footage-folder read, other-worktree access,
mailbox post, git-index write or commit. New records use file names only.
No bound changed. Every node's files are below its tmp_path. T6 validation,
T7/T8, traceability/report, reviews and final gate remain pending.

RUN REQUEST (dispatcher schedules after the STOP disposition; cell cannot run
the footage fixture), from the worktree root in Git Bash, expected **30-120 s**
with usable GPU, longer on CPU; this is an estimate, not a measured figure:

```bash
PYTHONPATH=scripts uv run pytest -q -rs tests/test_v51_video_acceptance.py::test_v4_real_trim_records_best_effort_presence --basetemp=work/wp5.1/t6-seat-metadata --durations=0 -o junit_family=xunit1 --junitxml=work/wp5.1/t6-seat-metadata.xml > work/wp5.1/t6-seat-metadata.log 2>&1
```

Return the log/XML plus the best-effort presence and device properties for the
later report. No heavy seat run is started here. This is the binding T6 yield;
await CHARC's T6-1 disposition and the dispatcher's next-turn instructions.

## Session 3 / Turn 7: T6 complete

### Ruling, scope and depth

Base is `462d7bb6` (dispatcher: all three committed files have zero CR).
Session 3 is `01a19671-ba33-7f71-a3ee-47dd1c74f2db`; dispatcher-supplied
depth after turn 6 is **120,480**, now recorded in the depth table. Turn 7's
depth remains for the dispatcher to fill. Evaluate near 200K and stop at a
step boundary near 250K.

CHARC `3a1497d6ceb21355` (2026-11-01T09:41:37Z) concurs that the missing
D54 words are a product defect and authorizes WP5.1 to continue T6/T7 with
that node unchanged. WP-D54 owns only the encoder's assumed-tags warning
text and its unit tests; it is a separate package. The candidate must be
rebased over that fix before the gate. T8's shell half proceeds independently.

**KNOWN RED: T6-1, product fix WP-D54 (CHARC 3a1497d6).**

`test_v6_untagged_runner_warns_bt709_limited` and its literal assertion remain
EXACTLY as committed: no code edit, xfail, skip or softened assertion. No
support or video-module code changed in this turn. "T6 complete" here means
the full T6 roster has now been exercised across cell and seat; acceptance
is NOT green. The additional V9 failures below require a new STOP.

### T6-2 [MAJOR, NEW, in envelope]: neutral post-encode mean exceeds 2.5/255

**STOP. Recommended: CHARC adjudicates/routes the three post-encode bound
failures before further build work; retain all failing nodes, the unchanged
2.5/255 bound and the commissioned libx265/standard runner settings.** No
product change, tolerance proposal applied, quality override, shorter sample
or weakened assertion was made.

All nodes have prefix `tests/test_v51_video_acceptance.py::`:

| Failing node | Mean absolute error, 1/255 | Maximum, 1/255 | Bound |
|---|---:|---:|---:|
| test_v9_neutral_runner_postencode[hevc8-bt709-full] | 2.953815972222 | 183 | mean <= 2.5 |
| test_v9_neutral_runner_postencode[untagged] | 2.788103780864 | 203 | mean <= 2.5 |
| test_v9_neutral_runner_postencode[rotated] | 2.953815972222 | 183 | mean <= 2.5 |

Failure is `_assert_postencode` at
`tests/test_v51_video_acceptance.py:265`: `PAIR_MEAN_SYNTHETIC exceeded`.
The three assertions fail on the real shipped runner's outputs. Each source
and output contains 45 decoded frames at 320 x 180 RGB (7,776,000 samples),
and their shapes agree. The actual runner records say `parameters_from=neutral`,
method `c3`, encoder `libx265`, quality `standard`. Exit status for each export
is 0; this is a numeric acceptance failure after successful export.

Cheap independent confirmation, without another encode or the acceptance
array-conversion helper: `t7-results.log` reads the saved source/output
`decoded.raw` files directly with NumPy, subtracts flattened uint8 samples as
float64 and recomputes both mean and maximum. It independently confirms all
three values above. The same direct calculation for the passing hevc10 case
uses little-endian uint16 scaled by 255/65535; mean **2.472876682319**, max
**183**, agreeing with its JUnit properties. Both sides use the same FFmpeg
decode command/filter as committed. No encoder setting or bound was varied
after this STOP. The evidence establishes the over-bound figures, not a
root-cause attribution between product encoding and the commissioned
post-encode acceptance bound (the older WP3.5 pair characterization excludes
the encoder, as its existing docstring says). That adjudication belongs to CHARC.

The V9 three failed before their later colour/rotation assertions and planted
controls; those steps are NOT claimed executed for these three instances.
The pre-existing V4 nodes separately pass mandatory colour/rotation comparisons.

### Whole T6 sandbox run and per-node table

Authorized run WITHOUT `-x` (PowerShell set `PYTHONPATH=scripts`; command below
is the equivalent runnable Git Bash form):

```bash
PYTHONPATH=scripts uv run pytest -q tests/test_v51_video_acceptance.py --basetemp=work/wp5.1/t7-tmp -p sandbox_mkdir_shim -p no:cacheprovider -m "not gpu and not footage and not gui and not fullclip" --durations=0 -o junit_family=xunit1 --junitxml=work/wp5.1/t7-video.xml > work/wp5.1/t7-video.log 2>&1
```

Exit **1**: **4 failed, 13 passed, 1 deselected in 99.22 s**. One failure is
KNOWN RED T6-1; three are new T6-2. Every sandbox-eligible instance ran; the
one deselected footage instance was already run at the dispatcher's seat.
No skipped instance and no additional export run after the completed batch.
All MD5 guards and names-only runner/fidelity/provenance checks that were
reached passed. This is not the whole-suite gate.

Every node below has prefix `tests/test_v51_video_acceptance.py::`. Sandbox
seconds are JUnit setup + call + teardown. G2's seat seconds are total wall
time, with call time separately recorded below. Markers remain provisional
as in turn 6, pending the owner's isolated/leg measurements.

| Node | Marker / leg | Result | Seconds |
|---|---|---|---:|
| test_v4_runner_preserves_fixture_fidelity[hevc8-bt709-full] | slow / serial provisional | PASS | 6.087 |
| test_v4_runner_preserves_fixture_fidelity[hevc10] | slow / serial provisional | PASS | 5.251 |
| test_v4_runner_preserves_fixture_fidelity[untagged] | slow / serial provisional | PASS | 5.165 |
| test_v4_runner_preserves_fixture_fidelity[vfr] | slow / serial provisional | PASS | 4.349 |
| test_v4_runner_preserves_fixture_fidelity[rotated] | slow / serial provisional | PASS | 5.308 |
| test_v4_truncated_runner_batch_obeys_d86 | slow / serial provisional | PASS | 8.121 |
| test_v4_real_trim_records_best_effort_presence | footage, slow / serial | PASS at dispatcher seat | 92.460 |
| test_v6_hdr_refusals_do_not_stop_batch | slow / serial provisional | PASS | 5.084 |
| test_v6_untagged_runner_warns_bt709_limited | slow / serial provisional | KNOWN RED T6-1 / WP-D54 | 4.895 |
| test_v9_neutral_runner_postencode[hevc8-bt709-full] | slow / serial provisional | FAIL T6-2 | 4.870 |
| test_v9_neutral_runner_postencode[untagged] | slow / serial provisional | FAIL T6-2 | 4.992 |
| test_v9_neutral_runner_postencode[rotated] | slow / serial provisional | FAIL T6-2 | 5.022 |
| test_v9_neutral_runner_postencode[hevc10] | slow / serial provisional | PASS | 7.631 |
| test_v10_repeated_video_exports_are_numbered | slow / serial provisional | PASS | 9.014 |
| test_v10_existing_video_output_is_unchanged | slow / serial provisional | PASS | 4.363 |
| test_v10_mov_mp4_share_one_numbering_sequence | slow / serial provisional | PASS | 9.504 |
| test_d91_video_provenance[default] | slow / serial provisional | PASS | 4.280 |
| test_d91_video_provenance[off] | slow / serial provisional | PASS | 4.465 |

### Executed planted-failure controls

All 13 passing sandbox instances and G2's passing seat instance exercised
their controls; JUnit properties retain the execution evidence:

| Node family / instances | Wrong result actually rejected |
|---|---|
| V4 fixture fidelity x5 | mandatory frame-count difference and missing roster |
| V4 VFR (additional) | a single rational pts changed by 1 us; actual 30-frame exact sequence compared and variable steps checked |
| V4 truncated | same fidelity controls; dropped D86 warning; following item marked not run |
| V4 real trim at seat | same fidelity controls; dropped GPMF telemetry |
| V6 HDR batch | generic HLG refusal, generic PQ refusal, following SDR item marked not run |
| V9 hevc10 | 3/255 RGB offset; each changed colour tag; changed tkhd display orientation |
| V10 repeated | reusing the first output name instead of numbering |
| V10 pre-existing file | selecting the planted first output instead of `_2` |
| V10 MOV/MP4 | using `.mov` as the second output extension instead of the shared `.mp4` sequence |
| D91 default | wrong app_version, empty/wrong parameters, full path in source name |
| D91 off | unwanted embedded provenance |

The known-red V6 untagged node fails before its empty-warning mutation;
the three new failing V9 instances fail before their controls, as stated
above. Their real failures already demonstrate the assertions reject the
shipped results; no claim that their later controls ran.

### G2 seat result and V4 best-effort observations

Dispatcher-returned evidence (not a cell footage-folder read): from this
worktree root at approximately **2026-11-01 09:41Z**, `PYTEST_ADDOPTS` unset:

```bash
PYTHONPATH=scripts uv run pytest -q -rs tests/test_v51_video_acceptance.py::test_v4_real_trim_records_best_effort_presence --basetemp=work/wp5.1/t6-seat-metadata --durations=0 -o junit_family=xunit1 --junitxml=work/wp5.1/t6-seat-metadata.xml
```

Exit **0**, **1 passed, 1 warning in 92.46 s**, call **90.61 s**. The warning
is CuPy's `CUDA path could not be detected` UserWarning. Device property is
`GPU`; video facts are `device_backend=cuda:0`, `frame_device=cuda:0`,
`encoder=libx265`, `decode_passes=2`. Both the mandatory-frame-count/roster
control and dropped-telemetry control were recorded as rejected. All
mandatory/required comparisons and GPMF carry assertions passed.

Names/presence only, as returned by the dispatcher:

| Best-effort item | Source present | Output present |
|---|---|---|
| GPMF gpmd | true | true |
| Camera atoms | true | true |
| Timecode track tmcd | true | true |
| Timecode value | true | true |
| Creation time: container tag | true | **false** |
| Creation time: mvhd | true | **false** |
| Creation time: per-stream tags | true | **false** |

The three creation-time FALSE rows are observations, with no preservation
assertion and no STOP: they belong to the brief's best-effort set. T10 must
carry this exact table and the three observed losses into the report's V4
best-effort section. The report has not yet been authored; the binding yield
before T10 still applies. Seat evidence files are
`work/wp5.1/t6-seat-metadata.log` and `work/wp5.1/t6-seat-metadata.xml`.

Budget planning flag: mixed-condition observed totals 99.22 s (this sandbox
module) + 92.46 s (seat G2) = **191.68 s**, already above 180 s before T7 and
shell work. This sum is NOT the required same-seat serial-leg delta: final
isolated measurements, marker classification and leg measurement remain
pending. Disclose it to CHARC as a budget risk; no node or marker was moved
to an exclusion, and no budget was raised.

### Light checks, verification loop and yield

| Evidence under work/wp5.1/ | Observed result |
|---|---|
| t7-video.log / t7-video.xml | exit 1; 13 pass, 4 fail, 1 deselected; 99.22 s |
| t7-results.log | per-node times/properties/failure messages; independent saved-raw mean/max confirmation |
| t7-ruff.log | exit 0; All checks passed! for support/video modules |
| t7-format.log | exit 0; 2 files already formatted |
| t7-mypy.log | exit 0; Success: no issues found in 2 source files (MYPYPATH=tools;tests) |
| t7-lf.log | zero CR bytes in the changed ledger |
| t7-code-unchanged.log / t7-diff-check.log | exit 0 for unchanged support/video modules and diff whitespace check |

Verification loop: confirmed the authorized known red without editing its
node; exercised all nine previously unrun sandbox instances; discovered
three real numeric failures at the commissioned bound; independently
confirmed their figures directly from saved raw samples. No false positive
is claimed for those figures and no product root cause is presumed. No
test/product fix was attempted. Every green-on-arrival node has an executed
negative control; T6-2 now goes to CHARC. Full acceptance, reviews, serial-leg
budget measurement and final gate remain pending.

New build findings: Critical 0 / Major 1 / Minor 0; in-envelope 1 / out 0;
NEW 1 (T6-2, three node instances) / REOPENED 0. One existing known-red
Major (T6-1) remains open under WP-D54, not a new or reopened finding.
Reverts 0; product fixes 0; test-code fixes 0; Reviewer A rounds 0 this turn.

Only this owned ledger changed. The support and video modules, particularly
the known-red node, are untouched. No product/existing-test edit, dependency,
fixture, tolerance change, local-config edit, footage-folder read, other
worktree access, mailbox post, git-index write or commit. No new seat run
request is needed. Yield at the T6 boundary with T6-2 for CHARC; do not start
T7 in this turn.

## Session 3 / Turn 8: T6-2 remediation and T7

### Binding ruling, depth and scope

Inspected base `1ed04a21`, containing the committed brief's full T6-2 ruling,
read in full this turn. CHARC `2bd14e3a90ed741d` (2026-11-01T09:51:05Z)
governs G5's new post-encode characterisation and the serial budget. Session
3's dispatcher-supplied depth after turn 7 is **143,997**, now in the depth
table; this turn's depth is for the dispatcher to fill. No depth estimate.

**Serial-leg budget: 300 s for the package, CHARC 2bd14e3a.** This supersedes
the historical 180 s limit/risk above. No node moves behind `fullclip` and
all video nodes retain `slow(reason="FFmpeg encode")`; GPU/footage markers
are additional. The actual serial-leg delta is measured at the final gate;
over 300 s is reported to CHARC for another ruling. No sizing STOP this turn.

**KNOWN RED: T6-1, product fix WP-D54 (CHARC 3a1497d6).** Its node and warning
assertion were left exactly unchanged. The source-text comparison against
committed HEAD for both the test function and its warning helper passed in
`work/wp5.1/t8-results.log`. It was deselected in this turn's targeted run,
not rerun or claimed passing. Rebase over WP-D54 remains a gate prerequisite.

### RED first, then the separate runner bound

T6-2's real-output RED of record remains turn 7's
`t7-video.log` / `t7-video.xml` / `t7-results.log`: the three failed
`test_v9_neutral_runner_postencode` instances name `PAIR_MEAN_SYNTHETIC`
and means 2.953815972, 2.788103781, 2.953815972 against 2.5/255. Those were
run before the new constant existed; not rerun merely to duplicate that RED.

Before adding the constant, added the ruled planted-output control to the
hevc8 instance: copy the actual decoded output as float64 in 1/255 units,
add exactly **4.0 to its red channel only**, do not clip, and call the same
post-encode bound assertion on that planted output. The initial call was
uncaught so the RED run demonstrates its actual failure, not a simulated
pytest result:

```bash
PYTHONPATH=scripts uv run pytest -q 'tests/test_v51_video_acceptance.py::test_v9_neutral_runner_postencode[hevc8-bt709-full]' --basetemp=work/wp5.1/t8-red-tmp -p sandbox_mkdir_shim -p no:cacheprovider -o junit_family=xunit1 --junitxml=work/wp5.1/t8-red.xml > work/wp5.1/t8-red.log 2>&1
```

Observed exit **1**, **1 failed in 10.12 s**. The failing source line is
`_assert_postencode(src, planted)`; message:
`PAIR_MEAN_SYNTHETIC exceeded: 3.719042052/255 > 2.5/255`.
The unplanted mean property remains 2.953815972. This RED was collected
before `RUNNER_POSTENCODE_MEAN` existed.

Then applied the ruling: new **RUNNER_POSTENCODE_MEAN = 3.5** only in the
owned video module, with its docstring naming the 2026-11-01 measurements
(2.79-2.95 at 8 bits, 2.47 at 10 bits), shipped libx265 quality standard,
the encoder-free `PAIR_MEAN_SYNTHETIC` 2.5 below it, and the recorded/unbounded
maximum. The bound assertion now fails by the new constant's name. The
planted-red-offset call is retained inside `pytest.raises` matching
`RUNNER_POSTENCODE_MEAN exceeded`, and passes as a control because the
planted 3.719042052 still exceeds **3.5**. The earlier artificial +3/255
all-channel control was replaced by this explicitly ruled +4/255 one-channel
control; one pixel control suffices. Colour/rotation tag controls remain
executed for all four V9 instances.

`tests/test_color_roundtrip.py` and AD-11's pre-encode bounds are unchanged.
T6-2 is resolved by the bound ruling and passing controls, not a product fix.
T10 must cite CHARC `2bd14e3a` and retain the accept-note sentence:
"V9's AD-11 bound binds pre-encode; the runner's post-encode leg is
characterised at 3.5/255 mean at the shipped quality".

### GREEN run: four V9 instances, high characterisation, CPU N10

```bash
PYTHONPATH=scripts uv run pytest -q -x tests/test_v51_video_acceptance.py --basetemp=work/wp5.1/t8-tmp -p sandbox_mkdir_shim -p no:cacheprovider -m "not gpu and not footage and not gui and not fullclip" -k "test_v9_neutral_runner_postencode or test_n10_video_cpu_render_digests_repeat" --durations=0 -o junit_family=xunit1 --junitxml=work/wp5.1/t8-targeted.xml > work/wp5.1/t8-targeted.log 2>&1
```

Exit **0**, **5 passed, 15 deselected in 41.32 s**. All selected instances
ran; no skip. Video-module roster is now the planned **20 instances**, with
two N10 instances added (one seat-only GPU). No extra high-quality test
instance was added: its one additional runner export and recorded properties
live in the existing hevc8 V9 instance. All module MD5 guards pass.

| V9 sample / quality | Mean absolute error, 1/255 | Maximum, 1/255 | Result |
|---|---:|---:|---|
| hevc8-bt709-full / standard | 2.953815972222 | 183 | PASS <= 3.5 |
| untagged / standard | 2.788103780864 | 203 | PASS <= 3.5 |
| rotated / standard | 2.953815972222 | 183 | PASS <= 3.5 |
| hevc10 / standard | 2.472876682319 | 183 | PASS <= 3.5 |
| hevc8-bt709-full / high | 2.521328960905 | 125 | characterisation ONLY, no numeric assertion |
| hevc8 output, planted red +4/255 / standard | 3.719042052469 | not needed | rejected by RUNNER_POSTENCODE_MEAN as required |

The high figure is recorded beside standard (2.521329 vs 2.953816) without
an asserted improvement or numeric bound. It is one `--quality high` export
of the unchanged hevc8 fixture, same source decode, neutral parameters,
CPU/libx265; maximum also recorded. All samples use the full committed
containers under the R0-4 sizing exception.

JUnit setup + call + teardown seconds from this run (prefix
`tests/test_v51_video_acceptance.py::`):

| Node | Markers / leg | Result | Seconds |
|---|---|---|---:|
| test_v9_neutral_runner_postencode[hevc8-bt709-full] (includes one high export and pixel control) | slow / serial | PASS | 12.104 |
| test_v9_neutral_runner_postencode[untagged] | slow / serial | PASS | 5.839 |
| test_v9_neutral_runner_postencode[rotated] | slow / serial | PASS | 5.693 |
| test_v9_neutral_runner_postencode[hevc10] | slow / serial | PASS | 6.034 |
| test_n10_video_cpu_render_digests_repeat | slow / serial | PASS | 11.057 |
| test_n10_video_gpu_render_digests_repeat_and_match_cpu | gpu, slow / serial | NOT RUN: seat-only request below | pending |

### T7 N10 construction and actual CPU result

Reuse the committed `acceptance_support.RenderDigests`: wrap real IF-3
`c3`, digest its returned pixels (dtype/shape/C-order SHA-256) by input pts
before the writer encodes them, and delegate all analysis/closed-form/render
behavior unchanged. Build a composition-root export engine around that method
and an explicitly owned scratch proxy cache closed on every path. Pass it
through `headless_export.main(argv, exports=...)`. No oracle CLI is imported.

CPU: two independent scratch invocations with the same source, parameters
and flags `--force-cpu --encoder libx265 --no-provenance`. Provenance is off
in both so its creation timestamp does not confound the file-byte
characterisation. Fresh caches exercise actual complete analysis/render
passes. Expected pts ticks come independently from the source's exact
rational timestamps and time base, with integer-tick, frame-count and
uniqueness checks. Assert both digest maps cover ALL source pts and are
identical. Assert actual render devices `{cpu}` and item device `CPU: forced`.

Actual CPU result: **45 render digests**, all 45 pts covered, identical
run-to-run; `render_devices=['cpu']`. Complete output FILES were
**byte-identical = True**, recorded only, not asserted. All digest values
are retained in JUnit properties. Planted changed digest and dropped pts
both rejected by name in the passing node (GREEN-ON-ARRIVAL controls).

GPU form is written but NOT run in the sandbox. It uses the shipped GPU
selector, skips only if CUDA is unavailable, asserts actual `{cuda:0}`
rendering and item `GPU` (so CPU fallback cannot count as GPU), compares
two GPU runs' full-pts digest maps, and records file-byte identity. It then
does one CPU export with the same encoder/options, decodes the first output
frame on each side using the existing helper, scales errors from 1/255 to
[0,1], records and asserts **max <= 2e-3, mean <= 2e-4** unchanged. Separate
above-max and above-mean first-frame controls are present. These GPU
assertions/controls await the seat and are not claimed passing here.

### G2 creation-time documentation anchors for T10

Read-only report search found `docs/reports/wp3.10-video-encode.md:145`-`:148`
explicitly lists **creation date and time** among `not_carried` items when
the source has GoPro settings (Q10, D105). That documents the general
best-effort limitation category. Its historical GX011627 measurement at
`:199` instead recorded creation time SAME. The current G2 three-field loss
is therefore a new observation, not a repeat of that old figure.

`docs/reports/wp4.4-mov-input.md:123`-`:129` lists lost mebx data tracks and
an output creation_time key; it does not document this creation-time loss.
Neither historical report documents the exact current triple loss
(container tag, mvhd, per-stream tags). T10 must cite the WP3.10 generic
limitation and this distinction beside turn 7's full G2 presence table;
do not replace the three observed FALSE rows with the earlier SAME result.
No preservation assertion or new STOP was added for best-effort loss.

### Light checks and verification-loop record

| Evidence under work/wp5.1/ | Observed summary |
|---|---|
| t8-red.log / t8-red.xml | 1 failed in 10.12 s, named old bound on actual planted red-channel offset |
| t8-targeted.log / t8-targeted.xml | exit 0; 5 passed, 15 deselected in 41.32 s |
| t8-results.log | per-node times/properties; high/standard figures; 45 CPU digests and file-byte identity; known-red functions exactly unchanged |
| t8-ruff.log | exit 0; All checks passed! for support and new v51 modules |
| t8-test-mypy.log | exit 0; Success: no issues found in 2 source files (MYPYPATH=tools;tests) |
| t8-format.log | only owned video module formatted |
| t8-format-check.log | exit 0; support/video modules already formatted |
| t8-lf.log | zero CR bytes in each of the two changed files |
| t8-diff-check.log | exit 0; diff whitespace check clean |

Verification loop: RED confirmed before introducing the ruled constant;
three old-bound real-output REDs retained as turn 7's record; GREEN confirmed
with actual four-sample comparisons and one-channel positive control at the
new bound. Confirmed CPU N10 full-coverage bit identity and independently
exercised changed-digest/dropped-pts controls. High quality is observed,
never bounded. No new product failure or false-positive finding; no product
fix. GPU validation and the complete suite remain pending. No second full
run was needed after the selected tests passed; later edits were ledger and
the constant's explanatory docstring only.

New findings: Critical 0 / Major 0 / Minor 0; NEW 0 / REOPENED 0;
T6-2 resolved by CHARC ruling; T6-1 remains KNOWN RED under WP-D54. Reverts 0;
product-code fixes 0; one owned test-code module changed plus this ledger.
No Reviewer A round ran this turn. The bound/control and N10 builds are
bundled as explicitly commissioned for turn 8.

Locks: no product/existing-test edit, dependency, committed fixture,
interface, local configuration, footage-folder read, other-worktree access,
mailbox post, git-index write or commit. Every export/cache/decode/record
written by these nodes is below its tmp_path; records/provenance contain
names only. `tests/acceptance_support.py` and
`tests/test_color_roundtrip.py` are unchanged. No GPU node ran in the cell.

### T7 GPU RUN REQUEST and yield

Dispatcher's seat from the worktree root, `PYTEST_ADDOPTS` unset, expected
**20-40 s** (estimate, not a measured figure), no exclusive window or other
heavy run open:

```bash
PYTHONPATH=scripts uv run pytest -q -rs tests/test_v51_video_acceptance.py::test_n10_video_gpu_render_digests_repeat_and_match_cpu --basetemp=work/wp5.1/t8-seat-gpu --durations=0 -o junit_family=xunit1 --junitxml=work/wp5.1/t8-seat-gpu.xml > work/wp5.1/t8-seat-gpu.log 2>&1
```

Return log/XML, actual render device, digest count/file-byte characterisation,
CPU/GPU first-frame mean/max and executed mutation properties. Any GPU
failure is adjudicated against the brief's unchanged T7 bounds; no fallback
or softening. Yield here after T7 for the seat run; T8 shell construction
is not started in this turn.

## Session 4 / Turn 9: T8

### Session boundary, inherited state and scope

Fresh session 4 starts from committed HEAD `2f1c0954`, as dispatched.
Session 3 retired after turn 8 at **177,474** depth_input_tokens; that
dispatcher-supplied figure and the retirement are now in the depth table.
Session 4's id and depth remain for the dispatcher to fill; no estimate.

This turn builds only `tests/test_v51_shell_acceptance.py` and updates this
ledger. T9 traceability and T10 report construction have not begun. Known
T6-1 runner-warning RED remains unchanged, awaiting the separate WP-D54
product fix and rebase. No new product STOP is established by collection or
static inspection; the two GUI outcomes require the seat run below.

### G8 GPU seat result returned by the dispatcher

The turn-9 dispatch supplies the following result on `2f1c0954`. This is
seat evidence returned by the dispatcher, not a GPU run in this sandbox;
it supersedes turn 8's pending GPU row without rewriting that history.
Evidence requested in turn 8: `work/wp5.1/t8-seat-gpu.log` and
`work/wp5.1/t8-seat-gpu.xml`.

| Node (tests/test_v51_video_acceptance.py::) | Markers / leg | Returned result | Returned figures |
|---|---|---|---|
| test_n10_video_gpu_render_digests_repeat_and_match_cpu | gpu, slow / serial | 1 passed in 19.37 s; call 18.75 s | render_frame_count 45; render_devices ['cuda:0']; output_files_byte_identical True; cpu_gpu_first_frame_max 0.0; cpu_gpu_first_frame_mean 0.0; both mutation probes rejected |

All 45 rendered pts have repeat-identical GPU digests. The decoded 8-bit
CPU/GPU first frames are identical: unchanged AD-11 max 2e-3 and mean 2e-4
bounds hold. File-byte identity is recorded only, not a requirement.

### T8 nodes and reused anchors

Exactly **two** nodes are added, matching round 0's roster. All shell
startup uses the existing real `make_app` fixture from
`tests/test_app_startup.py:71`, `cpu_settings` at `:63`, `wait_started`
at `:105`, `open_source` at `:114`, `presenter` at `:98`, and
`wait_analysis` / `latest_analysis` at `:123` / `:131`. Importing
`gui_support` sets offscreen QPA before the shell imports. Settings,
startup journal, cache and configured output folder are below tmp_path.

| Collected node (tests/test_v51_shell_acceptance.py::) | Markers / leg | Runner surface / assertions | Result |
|---|---|---|---|
| test_v6_real_untagged_shell_warns_bt709_limited | gui / serial | real committed vid-untagged, build_application/open_path, capturing presenter; warning identifies source and contains both BT.709 and limited; ASCII and names-only text; source MD5 unchanged | COLLECTED; GUI execution pending seat |
| test_v18_real_trim_preview_precedes_analysis_and_updates | gui, footage, slow(reason="real-trim analysis and FFmpeg decode") / serial | gx011627_trim, existing HeldEngines hook, displayed provisional pixels during running analysis, later nonzero displayed-pixel change at unchanged pts and geometry, exact smoothed_record statistics | COLLECTED; GUI/footage execution pending seat |

V6 follows `tests/test_app_wiring.py:382`'s real G10 case; the existing
empty-word row at `:377` remains unchanged. Its stricter new literal assertion
is not softened or xfailed. The actual product route is
`gui/sources.py:169` open_video -> fault_messages / assumed_colour ->
`gui/shell.py:436` _on_opened -> presenter. Message text is checked for
names only; the presenter's internal Message.path identity is not serialized
as a record. Names-only source and actual warning texts are JUnit properties.
Controls reject no warning, BT.709-only and limited-only warnings, inside
the node; their execution awaits the seat. V6 has gui only, as planned;
its measured duration will decide whether it also needs slow under AD-30.

V18 reuses `tests/test_app_v8_v18.py:366` HeldEngines and the `:405` test's
form. The only hold is inside the real analysis frame iterator after the
first frame: it does not replace any probe, correction method or decoder.
The node releases the hold in finally even if the provisional assertions
fail. Before release: a rendered corrected after_image exists, analysis
phase is running and session.statistics is None. Its RGB888 image_bytes
snapshot is a copy (`gui/imaging.py:257`), so later widget replacement
cannot mutate the baseline. After release: analysis completes, a later
render arrives, hook decode ends after the expected real-trim frame count,
the same pts and shape remain, and maximum absolute pixel change is > 0.
Mean and max change (1/255 units), pts, source name and frame count are
recorded. The supplied statistics must equal the engine's smoothed_record
at that same pts. Source MD5 is guarded on success and failure. This node
uses the trim fixture directly, adding no fullclip instance.

### Light validation and verification-loop record

All runner outputs are file-backed below work/wp5.1. No GUI, footage or
GPU execution occurred in this sandbox. Collection invokes pytest with
the mandatory sandbox_mkdir_shim and no cache provider; it does not
instantiate any fixture or open the footage folder.

| Evidence under work/wp5.1/ | Observed summary |
|---|---|
| t9-collect.log | exit 0; 2 tests collected in 1.01 s on the final source; both full node ids and all markers printed by collection-only hook |
| t9-ruff.log | exit 0; All checks passed! for support and all three new acceptance modules |
| t9-mypy.log | exit 0; Success: no issues found in 146 source files (project strict mypy) |
| t9-test-mypy.log | supplementary unscoped new-test check encountered 32 existing errors in the two imported GUI test modules; no existing test edited |
| t9-test-mypy-scoped.log | exit 0; Success: no issues found in 1 source file; strict check of the new module with MYPYPATH=tools;tests and --follow-imports=silent |
| t9-lf.log | zero CR bytes in both changed files |
| t9-diff-check.log | exit 0; diff whitespace check clean |

The unscoped test check follows imports into existing test_app_startup and
test_app_v8_v18, which the project's mypy files list does not include. The
scoped supplementary check keeps strict checking enabled for the owned
module while suppressing errors inside those read-only imported modules;
the normal project mypy check also passes. No type-ignore or project
configuration change was added. Ruff format --check remains the dispatcher's
seat check, as the fill specifies.

Verification loop: checked the real warning dispatch path independently
against the G10 test; no missing-warning defect inferred from the existing
empty-string assertion. Confirmed collection and intended markers without
running GUI fixtures. Checked pixel snapshots are copies and held analysis
is released in finally, and guarded unchanged pts/shape so a different
frame cannot satisfy the statistics-update assertion. Behavior, controls
and pixel figures remain unverified until the seat run; they are not
claimed green. No confirmed new product finding, false-positive product
finding, product fix or review round this turn. NEW 0 / REOPENED 0;
reverts 0; product-code fixes 0; one new test module and this ledger.

Locks: no product/existing-test edit, dependency, committed fixture,
interface, local configuration, footage-folder read, other-worktree access,
mailbox post, git-index write or commit. Names-only records and source MD5
checks are implemented; their runtime outcome is pending. T6-1's failing
node and its helper are untouched. Every node write is under tmp_path;
the existing guarded session trim is managed by its session fixture.

### T8 RUN REQUEST and yield

ONE run at the dispatcher's seat, from the worktree root in Git Bash with
PYTEST_ADDOPTS unset, no exclusive window or other heavy job running.
Expected **30-150 s** (estimate, not a timing figure); covers both nodes,
including the footage node. No sandbox shim at the seat.

```bash
PYTHONPATH=scripts QT_QPA_PLATFORM=offscreen uv run pytest -q -rs tests/test_v51_shell_acceptance.py -m "gui" --basetemp=work/wp5.1/t9-seat-shell --durations=0 -o junit_family=xunit1 --junitxml=work/wp5.1/t9-seat-shell.xml > work/wp5.1/t9-seat-shell.log 2>&1
```

Return the log/XML, per-node setup/call/teardown times, actual warning
texts and executed controls, V18 pixel-change max/mean and smoothed-statistics
result, and any skips/failures. A real-product failure stays red and is a
STOP to CHARC under Q3; no softening or product repair is authorized here.
The 300 s package serial-leg budget remains in force, measured at the gate;
these pending durations are not yet a serial delta. Yield after T8.

## Session 4 / Turn 10: T8 seat result and T9

### Depth, base and carried state

Turn 9 was committed as `84a030a1`, with zero CR and the seat's
ruff format --check passing. The dispatcher supplied session 4 id
`01a1968e-ac9f-7f81-aecc-78a4b492c479` and depth **91,630** after that
turn (context window 475,000); the depth table records them. This turn's
depth is left for the dispatcher, never estimated. Evaluate near 200K and
stop at a step boundary near 250K.

This turn owns T9 only: support's function-address table, the one pure
traceability node and this ledger. No report is created yet; T10 follows
Reviewer A's convergence. No rebase is performed. The candidate will be
rebased by the dispatcher over WP4.6 and WP-D54 before its gate. Known
T6-1 is unchanged and remains a failing acceptance assertion until WP-D54
lands; its failure is not a new STOP or a reason to relax the test.

### T8 seat result: both shell legs PASS

Returned by the dispatcher: 2026-11-01 about 10:09Z, from this worktree,
PYTEST_ADDOPTS unset, offscreen QPA, the exact turn-9 RUN REQUEST.
Exit **0**, **2 passed in 80.94 s**, no skip. The local XML was also read
for its names/counts/properties, not rerun; summary evidence is
`work/wp5.1/t10-seat-summary.log`. Source names and record values below
contain no absolute paths. The original log/XML are
`work/wp5.1/t9-seat-shell.log` / `work/wp5.1/t9-seat-shell.xml`.

| Node (tests/test_v51_shell_acceptance.py::) | Markers / leg | Seat result | XML setup + call + teardown seconds |
|---|---|---|---:|
| test_v6_real_untagged_shell_warns_bt709_limited | gui / serial | PASS | 0.815 |
| test_v18_real_trim_preview_precedes_analysis_and_updates | gui, footage, slow / serial | PASS | 79.344 |

G4 / V6 on **untagged.mp4** records exactly:

> The video's colour tags are missing or unexpected (range missing; primaries missing; transfer missing; matrix missing). Clearwater assumes BT.709 colours and limited range for those.

Its recorded mutation probe is "absent warning and either missing word
rejected". The shell half of G4 PASSES on the shipped product: the shell
shows the probe's own fault text. No shell STOP. The old
`test_app_wiring.py` empty-word row is unchanged and is still only weaker
coverage, not contrary evidence. This new node's measured time is below
5 s, so it retains gui without an extra slow marker.

G10 / V18 on **GX011627-trim.mp4** records provisional_analysis_phase
**running**, provisional_render_count **1**, analysis_frame_count **90**,
shown_pts_ticks **0**, preview_pixel_change_max_255 **3** and
preview_pixel_change_mean_255 **0.578** (XML unrounded
0.5784706147119342). shown_statistics is "equal to smoothed_record at
the unchanged pts". Thus the running shell shows a corrected provisional
frame before completion, then visibly changes its pixels and uses exactly
the smoothed statistics at the same pts. MD5 and all in-node assertions
passed. The matrix's V6 and V18 rows include these exact function addresses;
these results are the T10 report's input, not pending GUI outcomes.

### V7 figure-of-record update supplied by the dispatcher

WP4.6 was accepted on main **bbb4ef3e**, 2026-11-01 10:38Z. The returned
window figures are **(c) 39.0 ms PASS** and **(e) 48.0 ms PASS**; DR-98's
STOPs are closed at CHARC's accept commit. T10 cites WP4.3 window 5 for
(a) 18, (b) 19, (d) 56 and (f) 50.6 ms PASS, then WP4.6's window for
(c)/(e), using `docs/proofs/wp4.6-accept.md` and
`docs/reports/wp4.6-export-process.md`. Those later-main documents are
read on the final rebased candidate, never in another worktree. These
returned figures replace the historical pending DR-98 status for T10;
WP5.1 does not remeasure them. V7's table still references the existing
four automated workload functions as well as those report citations.

### T9 matrix and validation form

`acceptance_support.ACCEPTANCE_NODES` now explicitly contains all **20**
ids: V1-V18, N10 and D91, with **82 function-address references**. Each
address is `tests/test_module.py::test_function`; parameterized function
addresses represent every instance. T10 uses this same roster for its
matrix. The table includes existing unit/composition/shell coverage and
every new WP5.1 acceptance function (the D85 hard-link witness under V11),
without duplicating any existing implementation test. V1 names individual
compensation, cap, mask, white-balance/clamp, fusion and ordering checks;
the compensation image fixtures include their 10-bit grid. V3 names the
product-method jitter ratio and AD-14 nodes; no real static clip is
invented. V4 names mandatory and best-effort runner legs and existing
10-bit/GPU/real-container coverage. V17's existing reopen node also checks
cache-format mismatch re-analysis. D91's photo node already checks default
and disabled provenance; the new video node covers both modes.

`ACCEPTANCE_NON_NODE_REASONS` explicitly accounts for the five empty
automated rows: **V2 CP5 owner review pending; V12 v2; V14 the six-result
wp1.6 gate report; V15 and V16 WP5.2 pending**. An empty reason, a missing
id or an empty node list without its own reason fails the traceability
assertion. An empty tuple is no longer a silent placeholder.

The new parallel-leg node is
`tests/test_v51_traceability.py::test_acceptance_matrix_references_existing_test_functions`.
It imports each module with importlib and inspects each named function;
it requests no GUI/footage/GPU fixture, executes none of those referenced
tests and spawns no subprocess. It rejects malformed addresses, missing
modules/functions, non-functions, imported aliases and __test__=False
functions. No pre-produced collection file is required. This is the
brief's module-import/function-name form; parameter ids and fixture
expansion remain the final gate's collection-identity check.

### Stale-node RED then GREEN

First ran the traceability node with a planted stale V1 address passed to
the validator without catching its error:

```bash
PYTHONPATH=scripts uv run pytest -q tests/test_v51_traceability.py --basetemp=work/wp5.1/t10-red-tmp -p sandbox_mkdir_shim -p no:cacheprovider -o junit_family=xunit1 --junitxml=work/wp5.1/t10-red.xml > work/wp5.1/t10-red.log 2>&1
```

Exit **1**, **1 failed in 1.97 s**, specifically:
`stale acceptance node for V1: tests/test_v51_traceability.py::test_planted_stale_acceptance_node`.
The valid table completed first, so this RED is the intentional stale
address, not a typo in the real roster. Then retained the same planted
table inside pytest.raises matching the stale node's escaped full name.

```bash
PYTHONPATH=scripts uv run pytest -q tests/test_v51_traceability.py --basetemp=work/wp5.1/t10-trace-tmp -p sandbox_mkdir_shim -p no:cacheprovider -o junit_family=xunit1 --junitxml=work/wp5.1/t10-trace.xml > work/wp5.1/t10-trace.log 2>&1
```

Exit **0**, **1 passed in 1.13 s**; XML node time **0.241 s**, no markers,
parallel leg. Properties list all 20 ids, function_addresses **82**, all
five reasons and mutation_probe
"stale node rejected by name: tests/test_v51_traceability.py::test_planted_stale_acceptance_node".
The RED record and executed passing control prove a stale function cannot
silently count as acceptance coverage. Summary:
`work/wp5.1/t10-trace-summary.log`.

### Whole light command and checks

```bash
PYTHONPATH=scripts uv run pytest -q -rs tests/test_v51_photo_acceptance.py tests/test_v51_video_acceptance.py tests/test_v51_shell_acceptance.py tests/test_v51_traceability.py --basetemp=work/wp5.1/tmp -p sandbox_mkdir_shim -p no:cacheprovider -m "not gpu and not footage and not gui and not fullclip" --durations=0 -o junit_family=xunit1 --junitxml=work/wp5.1/t10-light.xml > work/wp5.1/t10-light.log 2>&1
```

Exit **1**, **1 failed, 33 passed, 4 deselected in 152.91 s (0:02:32)**.
No skips. The roster is now **38 instances**: photo 15, video 20, shell 2,
traceability 1. The light selection contains photo 15, video 18 and
traceability 1; the two shell nodes, the real-trim metadata node and GPU
N10 are deselected. XML confirms **photo 15 PASS; video 17 PASS / 1 known
FAIL; traceability 1 PASS**. Traceability's node time in this full run is
0.088 s. The extra photo D85 witness accounts for the increase from
round 0's provisional 37-instance total.

The ONLY failing node is unchanged
`tests/test_v51_video_acceptance.py::test_v6_untagged_runner_warns_bt709_limited`.
Its actual assertion remains **D54 BT.709/limited warning missing from
untagged item**. The returned encoder text still says only the assumed
codes (color_primaries bt709, color_trc bt709, colorspace bt709,
color_range tv), without the required literal words. This repeats known
T6-1 on the pre-WP-D54 base; not a new defect, not xfailed, no test softened.
Its node time is 6.252 s. No additional failing node or new STOP arose.
The original failure is retained in t10-light.log/XML; summary by module
and status is `work/wp5.1/t10-light-summary.log`.

| Evidence under work/wp5.1/ | Observed final-state summary |
|---|---|
| t10-red.log / t10-red.xml | exit 1; 1 failed in 1.97 s, planted stale node named in AssertionError |
| t10-trace.log / t10-trace.xml | exit 0; 1 passed in 1.13 s; 20 ids, 82 references, five non-node reasons; stale-name control executed |
| t10-light.log / t10-light.xml | exit 1; 33 passed, 1 known T6-1 failed, 4 deselected in 152.91 s; no skips |
| t10-seat-summary.log | returned T8 XML: warning and control, real-trim running phase and nonzero pixel update, exact smoothed statistics; both PASS |
| t10-ruff.log | exit 0; All checks passed! for ruff check . |
| t10-mypy.log | exit 0; Success: no issues found in 146 source files, normal strict project check |
| t10-test-mypy.log | exit 0; Success: no issues found in 2 source files, strict owned support/traceability check with --follow-imports=silent and MYPYPATH=tools;tests |
| t10-format.log / t10-format-final.log | owned support formatted initially; final formatter left both owned Python files unchanged; seat format --check remains for the dispatcher |
| t10-lf.log | zero CR and no trailing whitespace in all three changed files; known-red video module unchanged |
| t10-diff-check.log | exit 0; git diff --check clean |

### Verification, scope and handoff

Verification loop: confirmed all real function references before the
planted stale address failed by exact name; retained the same control in
the passing node and saw it execute again in the whole light run. Confirmed
every empty automated row has its reason, and all required acceptance ids
are present. Checked the T8 returned properties against its local XML;
shell V6 has both words and V18 has a nonzero pixel delta at unchanged pts.
All allowed light nodes ran, including the known RED; no unrelated failure
was hidden by a selector or a skip. New suspected product defects 0;
confirmed new defects 0; rejected false positives 0; product fixes 0.
The stale-node failure is an intentional test-control RED, not a product
STOP. NEW 0 / REOPENED 0, reverts 0. No Reviewer A round was run here;
the dispatcher runs round 1 on the package after this yield.

Locks: only support, the new traceability module and this ledger changed.
No product/existing-test edit, dependency, committed fixture, interface,
configuration, footage-folder read, GUI/GPU/footage execution, other-worktree
access, mailbox post, git-index write, commit or rebase. Scratch logs and
test writes stayed under work/ and tmp_path. Existing acceptance behavior
was not edited; the whole-light known RED remains literal. V2, V12,
V14, V15/V16 are explicit dispositions, not claimed automated passes.
V7's later-main figures are attributed to the dispatcher, not remeasured.
The 300 s serial-leg delta and final three-leg collection identity remain
gate measurements; this light-only run supplies neither.

Yield after T9 for Reviewer A round 1. T10 report waits for convergence,
as commissioned. No new RUN REQUEST is needed this turn.
