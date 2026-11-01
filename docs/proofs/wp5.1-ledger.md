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
| 4 / T3-1 amendment | `01a1963b-002e-7cc3-9d5d-0f7807bb5ed9` | pending dispatcher | read turn footer; STOP T4-1 before T5 |

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
