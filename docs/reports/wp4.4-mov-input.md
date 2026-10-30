# WP4.4 -- MOV input

Candidate report, 2026-10-29. Base main `5e3537d`; branch `wp4.4`;
seat-2 cleanup starts at `d427dc9`. Reviewer A R1 converged with
`NO_NEW_CRITICAL_MAJOR`. Reviewer B and the gate: pending at the
orchestrator's seat. This report does not claim acceptance.

## Binding specification

Spec v0.5.7, 5.2, `docs/underwater-correction-spec.md:213`:

> MP4 or QuickTime container (`.mp4`, `.mov`; 0.5.7), H.265/HEVC or H.264. Both are ISO base media files read by the same FFmpeg demuxer; the iPhone records QuickTime (`qt` brand), the GoPro MP4.

Spec 8.3, `docs/underwater-correction-spec.md:384`:

> **Naming:** source filename plus suffix, default `_corrected`, editable in settings. Photos change extension to `.png`. Examples: `GX010123.MP4` &#8594; `GX010123_corrected.MP4`; a `.mov` source is written as MP4 and takes the `.mp4` extension (`IMG_1234.MOV` &#8594; `IMG_1234_corrected.mp4`; D25, 0.5.7); `IMG_1234.HEIC` &#8594; `IMG_1234_corrected.png`.

The arrows use HTML character references to preserve the quotation's rendered
text in an ASCII source file. D25 requires MP4/HEVC output; D105 makes frame
timing, start offset, audio sync and display orientation mandatory. Q3 of
CHARC `197131faf8764ebd` corrects the commission's AD-11 wording: these runner
tests assert the house V4 MANDATORY/REQUIRED verdict and roster SAME, without
a pixel-error bound.

## Changes and owned files

| File | Change and authority |
|---|---|
| `src/clearwater/gui/sources.py:25` | Add `.mov` to the case-insensitive video route/filter; docstring cites 5.2 (0.5.7). Original brief. |
| `tools/headless_export.py:142` | Matching suffix set/docstring; refusal strings unchanged. Original brief. |
| `src/clearwater/jobs/naming.py:291-316` | Only a video suffix whose lowercase spelling is `.mov` becomes lowercase `.mp4`; other video suffixes retain case. Public naming docstrings describe the rule. Original brief, 8.3. |
| `src/clearwater/io/video/encode.py:99,387` | Q2, CHARC `197131faf8764ebd`: deterministic `MP4_DATA_CODEC_TAGS = frozenset({"gpmd"})`; retain the tmcd exclusion; map no other data tag, with existing not_carried reporting. No probe/retry. |
| `src/clearwater/io/video/encode.py:6,705` | Docstring-only GRANT `fd2269acf257054d` (dispatch anchors 6 and 703): describe allowlisted stream copying and D105 omissions. Executable AST unchanged in cleanup. |
| `tests/test_jobs_naming.py` | Original new MOV coverage; Q1 authorizes the old clip.mov expectation edit and new clip.Mp4 control. CHARC `5a8339db3b9c6b4a` additionally authorizes case-only collision witnesses below. |
| `tests/test_gui_open.py` | Q1, CHARC `197131faf8764ebd`: only add filter `*.mov`, change a.mov route and add a.MOV row. |
| `tests/test_io_video_encode_units.py:80` | ONE-token GRANT `73d2797750c57625`: synthetic map input `meta` becomes `gpmd`. Original map assertions remain verbatim. Original line 753 `meta` is a packet-table row, not a map input, and is unchanged. |
| `tests/test_wp44_mov_input.py` | New route, unknown-tag map, qt integration and one phone footage test. Stereo fixture authorized by `093384f126589674`. Orchestrator generation 24's turn-4 ruling requires `done with warnings` and exactly two mebx warnings. R1 cleanup drains runner capture in finally; assertions unchanged. |
| `tools/container_spike/compare.py` | THREE equivalences only, Footage STOP GRANT `9c8f461b73ec8c05`; R1 finding 1 retains every matrix coefficient except translation. |
| `tests/test_container_spike_compare_equivalences.py` | New synthetic equivalence/control tests under the same grant; R1 adds non-translation controls and translation-note coverage. |
| `docs/proofs/wp4.4-ledger.md`, this report | Round evidence, rulings, validation and handoff. |

The naming rule runs before the unchanged composed-name guard, collision
numbering and temporary-path logic. Both `final_output_path` and `plan_output`
map `IMG_6702.MOV`, `x.mov` and `x.Mov`, including edited `_fixed` and empty
suffixes. A mapped temporary ends `.mp4`; `x.mov:s` remains refused.
Existing MP4/photo names, source protection and WP2.3 controls are preserved.

Case-only collisions number rather than overwrite. In one Reservations registry,
`IMG_1.MOV` then `IMG_1.MP4` yields `IMG_1_corrected.mp4` then
`IMG_1_corrected_2.MP4`; reverse order yields `IMG_1_corrected.MP4` then
`IMG_1_corrected_2.mp4`. An existing `IMG_2_corrected.MP4`, or its uppercase
MP4 temporary, sends `IMG_2.MOV` to `IMG_2_corrected_2.mp4`.
The four nodes passed on the existing product implementation; no naming fix
was needed for CHARC's NTFS point.

## RED/GREEN and collection changes

Full commands, parameter rosters and log paths are in the cumulative ledger.
Node families below retain their exact test names; bracketed parameter families
are expanded by the ledger rather than represented as single collected nodes.

| Evidence | Nodes | RED then GREEN |
|---|---|---|
| Routing | `tests/test_wp44_mov_input.py::test_runner_routes_mov[a.mov]`, `[a.MOV]`, `[a.Mov]`; `test_qt_mov_probe_decode_runner_and_v4`; GUI chooser and two MOV route nodes | Base routing: 7 failed / 14 passed. Suffix edit: 21 passed / 1 qt deselected, including unchanged routing-table equality pin. |
| Naming | `tests/test_jobs_naming.py::test_video_extension_case_is_preserved`; `test_mov_output_extension[<folder>-<suffix>-<name>-<planner>]` (36 nodes); `test_mov_and_mp4_share_collision_sequence`; `test_mov_collision_uses_mapped_extension[final/temporary]`; `test_mov_temporary_path_uses_mp4[final/plan]` | Unchanged naming: 42 failed / 4 passed / 819 deselected. Mapping: entire file 865 passed. |
| Data map | `tests/test_wp44_mov_input.py::test_data_map_only_carries_proved_mp4_tags` | Base includes planted zzzz map: 1 failed / 2 passed; allowlist plus granted token: 81 passed. gpmd carried and tmcd excluded remain controls. |
| Equivalences | `tests/test_container_spike_compare_equivalences.py::test_translation_is_equivalent[forward/reverse-side/tkhd]`, `test_unset_square_sar_is_equivalent[forward/reverse-absent/null]`, `test_unset_mono_layout_is_equivalent[forward/reverse-absent/null]` | Base af4ccc0: 12 failed / 15 passed. Granted changes: 27 passed. |
| R1 matrix narrowing | Same file `test_nontranslation_matrix_change_control[w-side]`, `[w-tkhd]`, `[uv-side]`, `[uv-tkhd]` | At d427dc9 all four incorrectly SAME: 4 failed / 6 passed / 892 deselected in focused run. Non-translation comparison: 10 passed / 892 deselected. |

Q1 collection diff: removed
`tests/test_gui_open.py::test_routing_by_extension[a.mov-refusal]`; added
`tests/test_gui_open.py::test_routing_by_extension[a.mov-video]` and
`tests/test_gui_open.py::test_routing_by_extension[a.MOV-video]`.
`test_file_dialog_route_uses_the_injected_chooser` is retained, with `*.mov`
added. Naming node `test_video_extension_case_is_preserved` is retained with
clip.mov now expecting clip_corrected.mp4; added
`tests/test_jobs_naming.py::test_mp4_extension_case_is_preserved` proves
clip.Mp4 still produces clip_corrected.Mp4. No other original node was removed.

Additional retained guard/control nodes include
`test_runner_unknown_extension_refusal_is_unchanged`,
`test_mov_extension_stream_is_refused[final/plan]`, and
`test_wp23_fixture_names_keep_output_paths` in the naming file.
The final NTFS witnesses are
`tests/test_jobs_naming.py::test_mov_and_uppercase_mp4_share_run_registry[mov-first]`,
`[mp4-first]`, and `test_mov_collision_with_uppercase_mp4_on_disk[final]`,
`[temporary]`.

## Fixture, footage and V4 evidence

The tmp_path fixture `clip.MOV` is qt-brand QuickTime: HEVC, B-frames present,
192x144, 30 fps, about 0.5 s, stereo 48 kHz pcm_s16le and a 180-degree display
matrix. The test asserts the brand, B-frames and rotation before probing,
fully decoding and exporting through the CPU runner to `clip_corrected.mp4`.
Decoded count equals probe count; MANDATORY and REQUIRED items and the roster
are SAME. The fixture's rotation has zero translation as written by FFmpeg;
translation equivalence is witnessed by synthetic tests and IMG_6702 only.
FFmpeg cannot author the phone's mebx tracks; the synthetic zzzz unit covers
omission in the parallel leg and the real phone test witnesses mebx omission.

Round 0 at unchanged base `5e3537d` drove the product sink directly because
the runner still refused MOV. `vf.encode_file(..., encoder="libx265",
bit_depth=8)` failed before V4: `VideoEncodeError`, kind `encoder_failed`,
script EXIT 1, encoder exit 4294967274. Streams were hevc/hvc1 video,
pcm_s16le/lpcm audio and two data/mebx streams. Safe diagnostic fragments:
`Could not find tag for codec none`, `codec not currently supported in
container`, `Could not write header`, `Invalid argument`, `Nothing was
written into output file`. No comparison was reached; this is not a V4 pass.
Seat evidence established PCM copying works; mebx mapping caused the failure.

At c353dfd the phone runner completed successfully but V4 failed on both
orientation items and size/SAR: 1 failed in 59.4 s, EXIT 1. Rotation was -180
and size 1920x1440 on both sides; only translation changed from
[125829120, 94371840] to [0, 0], and SAR from unset/null to 1:1.

The footage figure of record is the orchestrator's generation-24 run at
`d427dc9`, 23:35Z: **1 passed in 60.15 s, EXIT 0** for
`tests/test_wp44_mov_input.py::test_phone_mov_runner_and_v4`.
IMG_6702's 0.5 s / 15-frame HEVC source exported as the sole
`IMG_6702_corrected.mp4`, exit 0, record state `done with warnings`.
V4 MANDATORY/REQUIRED and roster were SAME; the test separately names display
orientation SAME and asserts source/output frame count 15.
Best-effort not_carried names: `data track mebx`, `data track mebx`.
The two dropped Core Media tracks stay out of the output (Q2, D105).

Privacy seat evidence (names/counts only): source location keys
`com.apple.quicktime.location.ISO6709` and
`com.apple.quicktime.location.accuracy.horizontal` do not reach the output;
output format keys are {comment, compatible_brands, creation_time, encoder,
major_brand, minor_version}, with 0 loci, 0 (c)xyz and 0 keys atoms.

For CHARC / Q4: supplied source video edit-list media_time is 0, with reorder
in negative ctts. The footage pass confirms SAME for `edit list, video track,
as written (media_time in media seconds)` and `edit list, video and audio
tracks (presentation effect)`. These corroborate DR-15 only; its original
trigger stays OPEN and the register is untouched. Exact duration/rate and
source/output edit-list row payloads were not supplied to this cell; they are
not inferred from the verdict. The safe row-extraction RUN REQUEST in the
ledger remains for the seat to attach before accept.

## Granted comparison equivalences

CHARC `9c8f461b73ec8c05` permits only these instrument equivalences:

1. Both orientation items compare rotation and all non-translation matrix
   coefficients. R1 finding 1 corrects the first implementation's 2x2-only
   projection: indices 0, 1, 2, 3, 4, 5 and 8 are now exact; only 6 and 7
   are excluded. Translation terms remain beside each verdict as BEST-EFFORT
   text. Quarter-turn, mirrored linear part, rotation-only, doubled w and
   nonzero u/v controls are DIFFERENT. Both translation-note tests require
   source and output terms while verdict remains SAME; deleting the note
   makes both tests fail in the mutation check.
2. Unset/null SAR equals 1:1. The 1:1 versus 4:3, width and height controls
   remain DIFFERENT.
3. At channels == 1, absent/null channel_layout equals mono, for any codec.
   Channel count, codec, sample rate and other layouts remain exact. The
   1-versus-2-channel and stereo-versus-5.1 controls remain DIFFERENT.
   The declared-mono issue is FIXED, superseding the earlier prospective
   MINOR row; no mono-layout register row opens. The qt fixture stays stereo
   to retain its existing independent integration witness.

The original 14 planted-difference controls passed before and after the
equivalences. The final file has 33 synthetic nodes, including the six R1
additions. Existing V4 tests were not changed.

## Dolby Vision scope and limits

Inventory `docs/reports/inventory-2026-10-29.md:263-299` identifies
IMG_6704.MOV and IMG_6772.MOV as transfer `arib-std-b67` (HLG), with a DV RPU.
Under spec 5.3 and CHARC Q5 they are correctly refused: "This video uses HLG
HDR, which Clearwater does not support. Record in standard (SDR) mode
instead." This text comes from `src/clearwater/io/video/probe.py:443-452`;
it is a code/inventory conclusion, not a real-file run in this package.
Neither DV clip was tested here; no second footage test or register row.

R1 finding 2, out of envelope: `verify.py:890-895` pairs data tracks by
position. A mixed source [mebx, gpmd] becoming [gpmd] can falsely warn that
gpmd was not carried. No owner footage has that mix (phone mebx only;
HERO13 tmcd plus gpmd). CHARC owns the register row at accept under
`fd2269acf257054d` Q-B(a); verify.py and the register remain unchanged.

R1 finding 7, advisory: an empty tag produces `data track ` with no tag
after it; uppercase `GPMD` is not mapped. Both are on the safe side of the
allowlist. No additional code change is authorized or made.

## Review, verification and remaining handoff

Reviewer A R1, Claude opus/high read-only pass, returned
`NO_NEW_CRITICAL_MAJOR`: 0 critical, 0 major, 4 minor, 5 advisory; converged.
Findings 1/3/4/6/9 are fixed as dispatched; 2 is out of envelope and reported;
5 is the zero-translation fixture qualification; 7 is the safe-side limit;
8 is settled by the seat privacy check above. The terminating-round cleanup
is explicitly authorized in this turn; no further A round is requested.

Final cell validation on the cleanup:

| Check | Result |
|---|---|
| Focused R1/naming GREEN | 10 passed / 892 deselected, EXIT 0 |
| Required six-file light run, sandbox shim and marker exclusions | 1122 passed / 3 failed / 5 deselected in 56.93 s, EXIT 1; all three failures are the already confirmed sandbox-only UNC permission artifact in headless tests |
| `uv run ruff check .` | All checks passed, EXIT 0 |
| `uv run ruff format --check .` | 273 files already formatted, EXIT 0 |
| `uv run mypy` | No issues in 141 source files, EXIT 0 |
| Note-deletion / AST checks | 2/2 note deletions rejected; encode executable AST and every footage assertion unchanged, EXIT 0 |

The three sandbox UNC failures are
`test_g1_inside_sees_every_spelling_of_the_same_folder`,
`test_g1_main_refuses_every_footage_check_through_another_spelling[unc]`,
`test_g1_the_redactor_hides_the_extended_spellings` in test_headless_export.py.
Prior seat confirmation is authoritative; the final two-leg gate remains due.
The separate prototype importer stall is also a confirmed sandbox artifact:
the seat ran 52 passed / 10 deselected, EXIT 0, at d427dc9. Turn-1 available
comparison/importer regressions had 250 passed / 35 deselected, EXIT 0.

All cell tests use the required sandbox shim. No footage, GPU, GUI, slow or
fullclip test ran in this cleanup. Footage and local configuration were not
read or changed; all generated cell artifacts are work-local. No dependency,
frozen interface, register or file outside the owned/granted surface changed.
The report's safe-row evidence gap and the three environment failures are
explicit; no new unresolved product/design STOP is claimed.

The ledger carries exact final phone RUN REQUEST and safe edit-row extraction.
Reviewer B, the final footage rerun, the standard two-leg gate (no fullclip),
and accept remain with the orchestrator.
