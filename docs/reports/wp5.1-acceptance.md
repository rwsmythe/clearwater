# WP5.1 automated acceptance suite

Status: turn 15, Reviewer B cleanup on `7ab7bd39`, 2026-11-01. Reviewer A
converged at round 2; Reviewer B returned NO_NEW_CRITICAL_MAJOR. Development
and returned seat evidence is below; the final three-leg gate remains pending.
This report does not claim release acceptance.

The contract is spec v0.5.7 section 11, plan section 7 and the
[WP5.1 brief and folded rulings](../briefs/wp5.1-brief.md).
The [cumulative ledger](../proofs/wp5.1-ledger.md) contains the reproductions,
per-turn results, ruling ids and session boundaries. Only tests, acceptance
support and documentation were built here; product remediation was routed
to its owning package. No product, frozen interface, dependency, existing
package test or committed fixture was changed by WP5.1.

## Evidence and scope

All new exports use the shipped `tools/headless_export.py`: in-process
`main(argv, exports=...)` for injected failures and render recording, and
the real interpreter executing that unchanged script for the crash leg.
Shell legs use the running application and real probe. The committed
fixture sweep is unchanged under CHARC's R0-4 sizing exception; derived
cases follow AD-30. The only owner-clip input is the guarded session trim
GX011627-trim.mp4, run at the orchestrator's seat. Every test write is
under tmp_path; source MD5 guards, names-only record checks and independent
readers remain assertions. This report includes file names, comparison
figures and presence booleans, without footage paths or metadata payloads.

| Key | Result of record | Evidence under work/wp5.1 / provenance |
|---|---|---|
| L13 | 34 passed, 4 deselected, 0 skipped, 114.78 s; exit 0 | t13-light.log/xml; sandbox shim, no cache provider; all four new test modules, excluding gpu/footage/gui/fullclip |
| L15 | 34 passed, 4 deselected, 0 skipped, 162.53 s; exit 0 | t15-light.log/xml; same four-module sandbox command after Reviewer B cleanup |
| X13 | Traceability plus the two existing cache-format nodes: 3 passed, 0.87 s | t13-trace.log/xml; supplemental V17 addresses and wrong-module-file control |
| C13 | Real photo crash: 15/15 isolated passes, no skips | t13-crash-01 through t13-crash-15.log/xml; t13-crash-summary.log; summed pytest suite times 30.422 s, not enclosing-loop wall |
| C15 | Real photo crash: 15/15 isolated passes, no skips; every cleanup on attempt 1 | t15-crash-01 through t15-crash-15.log/xml; t15-crash-repeat.log; summed XML suite times 37.444 s, not gate delta; UTF-8/package/PID/stability witnesses checked |
| H12 | GPU N10 plus both shell nodes: 3 passed, 86.69 s; exit 0 | t12-seat.log/xml, seat on 5f75a03a at about 2026-11-01 17:50Z; exact properties summarized in t13-seat-summary.log |
| M6 | Real-trim V4 metadata: 1 passed, 92.46 s; exit 0 | t6-seat-metadata.log/xml, seat at about 2026-11-01 09:41Z; GPU, libx265, 90 frames |
| A2 | Reviewer A light run: 34 passed, 2 deselected, 108.09 s | External round-2 review on f059b2e0 against 4ece5183; shell module omitted, hence two fewer deselections than L13 |

The orchestrator confirmed in turn 14 that H12 stands after turn 13:
the three seat nodes and their called helpers are unchanged; the changed
interpreter/runner command helpers are used only by the photo crash node.
M6 remains the returned real-clip observation; its strengthened presence
roster guard was checked from returned data and controls in turn 12.
The final gate will execute the current footage node. No hardware rerun
or measurement was made during this documentation turn.

The new roster has 38 instances: photo 15, video 20, shell 2, traceability
1. Source markers place 15 in P, 23 in S and none in F; final collection
identity remains a gate check. Every video node is slow with reason
`FFmpeg encode`; the photo crash is slow because it runs the runner as a
subprocess; V18 is gui/footage/slow for real-trim analysis and FFmpeg decode.
The two-reader photo nodes, ENOSPC node, deterministic D85 witness and
pure traceability node belong to P. The shell warning is gui and belongs to S.

## Acceptance matrix

The following function addresses reproduce `ACCEPTANCE_NODES` in
tests/acceptance_support.py: 20 acceptance ids, 83 addresses, 81 unique
functions. An address covers all its parameterized instances. P = parallel
(`not gpu and not footage and not gui and not slow and not fullclip`),
S = serial (`(gpu or footage or gui or slow) and not fullclip`),
F = fullclip. Mixed forms list their markers and legs separately.
`none` means no scheduling marker; usefixtures/parametrize are not leg markers.
`(gate)` means the current-candidate execution is pending, not a passing claim.
Existing nodes were preserved and statically checked; L15/H12/M6/X13 identify
actual development or returned-seat results. Figures of record follow the table.

| ID | Node id / non-node disposition | Scheduling markers | Leg | Result / source |
|---|---|---|---|---|
| V1 | `tests/test_methods_compensation.py::test_ancuti_chain_matches_prototype` | none (CPU); +gpu (CUDA) | P / S | (gate) |
| V1 | `tests/test_methods_compensation.py::test_ancuti_render_matches_prototype_on_supplied_values` | none (CPU); +gpu (CUDA) | P / S | (gate) |
| V1 | `tests/test_methods_compensation.py::test_c3_matches_prototype` | none (CPU); +gpu (CUDA) | P / S | (gate) |
| V1 | `tests/test_methods_compensation.py::test_c3_matches_prototype_off_default` | none (CPU); +gpu (CUDA) | P / S | (gate) |
| V1 | `tests/test_methods_compensation.py::test_uniform_image` | none (CPU); +gpu (CUDA) | P / S | (gate) |
| V1 | `tests/test_methods_compensation.py::test_near_zero_red_cap_binds_and_none_compensates` | none (CPU); +gpu (CUDA) | P / S | (gate) |
| V1 | `tests/test_methods_compensation.py::test_cap_binding_not_binding_and_none` | none | P | (gate) |
| V1 | `tests/test_methods_compensation.py::test_blue_off_leaves_blue_and_green_unchanged` | none (CPU); +gpu (CUDA) | P / S | (gate) |
| V1 | `tests/test_methods_compensation.py::test_c3_mask_below_at_and_above_threshold` | none (CPU); +gpu (CUDA) | P / S | (gate) |
| V1 | `tests/test_methods_white_balance.py::test_measure_closed_form_and_render_match_prototype` | none (CPU); +gpu (CUDA) | P / S | (gate) |
| V1 | `tests/test_methods_white_balance.py::test_near_zero_red_hits_the_floor_and_the_clamp` | none (CPU); +gpu (CUDA) | P / S | (gate) |
| V1 | `tests/test_methods_white_balance.py::test_clamp_binds_as_d99_says` | none | P | (gate) |
| V1 | `tests/test_methods_fusion_prototype.py::test_fusion_inputs_with_supplied_bounds` | none (CPU); +gpu (CUDA) | P / S | (gate) |
| V1 | `tests/test_methods_fusion_prototype.py::test_weights` | none (CPU); +gpu (CUDA) | P / S | (gate) |
| V1 | `tests/test_methods_fusion_prototype.py::test_multiscale_fusion` | none (CPU); +gpu (CUDA) | P / S | (gate) |
| V1 | `tests/test_methods_fusion.py::test_v1_edge_cases` | none (CPU); +gpu (CUDA) | P / S | (gate) |
| V1 | `tests/test_methods_assembly.py::test_v1_stage_measured_with_the_supplied_earlier_records` | none | P | (gate) |
| V1 | `tests/test_methods_assembly_prototype.py::test_analyze_against_statistics_of` | none | P | (gate) |
| V1 | `tests/test_methods_assembly_prototype.py::test_render_against_correct_with_the_same_record` | none | P | (gate) |
| V1 | `tests/test_methods_assembly_prototype.py::test_cpu_against_gpu_within_ad11` | gpu | S | (gate) |
| V2 | Owner visual review at CP5 | n/a | n/a | Pending CP5; no automated preference oracle |
| V3 | `tests/test_wp42_v3_product.py::test_the_lossless_clips_decode_inside_wp39s_envelope` | gpu, slow | S | (gate) |
| V3 | `tests/test_wp42_v3_product.py::test_ad14_bound_with_the_product_method` | gpu, slow | S | (gate) |
| V3 | `tests/test_wp42_v3_product.py::test_v3_ratio_on_the_jittering_patch_clip_with_the_product_method` | gpu, slow | S | (gate) |
| V4 | `tests/test_v51_video_acceptance.py::test_v4_runner_preserves_fixture_fidelity` | slow | S | PASS L15 |
| V4 | `tests/test_v51_video_acceptance.py::test_v4_truncated_runner_batch_obeys_d86` | slow | S | PASS L15 |
| V4 | `tests/test_v51_video_acceptance.py::test_v4_real_trim_records_best_effort_presence` | footage, slow | S | PASS M6 observation; current gate pending |
| V4 | `tests/test_wp42_video_path.py::test_v4_through_the_composition_on_the_cpu` | none | P | (gate) |
| V4 | `tests/test_wp42_video_path.py::test_v4_through_the_composition_on_the_gpu_with_device_frames` | gpu | S | (gate) |
| V4 | `tests/test_jobs_export_video.py::test_v4_every_decodable_sample_through_the_engine` | none (libx265); gpu (NVENC) | P / S | (gate) |
| V4 | `tests/test_jobs_export_video.py::test_v4_synthetic_5k3_8_7_clip` | slow | S | (gate) |
| V4 | `tests/test_jobs_export_video.py::test_gx011627_through_the_engine_keeps_every_mandatory_and_required_item` | footage, gpu, slow; +fullclip on full | S trim / F full | (gate) |
| V5 | `tests/test_wp41_photo_path.py::test_v5_bit_depth_icc_exif_and_provenance` | none | P | (gate) |
| V5 | `tests/test_v51_photo_acceptance.py::test_v5_jpeg_two_readers_and_pose` | none | P | PASS L15 |
| V5 | `tests/test_v51_photo_acceptance.py::test_v5_heic_two_readers_and_ad24` | none | P | PASS L15 |
| V6 | `tests/test_v51_video_acceptance.py::test_v6_hdr_refusals_do_not_stop_batch` | slow | S | PASS L15 |
| V6 | `tests/test_v51_video_acceptance.py::test_v6_untagged_runner_warns_bt709_limited` | slow | S | PASS L15 |
| V6 | `tests/test_v51_video_acceptance.py::test_v4_truncated_runner_batch_obeys_d86` | slow | S | PASS L15 |
| V6 | `tests/test_v51_shell_acceptance.py::test_v6_real_untagged_shell_warns_bt709_limited` | gui | S | PASS H12 |
| V6 | `tests/test_headless_export.py::test_refused_items_fail_and_the_batch_continues` | none | P | (gate) |
| V6 | `tests/test_headless_export.py::test_damaged_photos_are_failed_items_and_the_batch_continues` | none | P | (gate) |
| V6 | `tests/test_app_wiring.py::test_g10_damaged_unsupported_and_untagged_inputs_get_a_readable_message` | gui | S | (gate) |
| V7 | `tests/test_app_v7.py::test_v7_a_b_analysis_and_scrubbing` | gui, slow | S | (gate); PASS figure of record below |
| V7 | `tests/test_app_v7.py::test_v7_c_e_export_and_a_full_render_during_it` | gui, slow | S | (gate); PASS figure of record below |
| V7 | `tests/test_app_v7.py::test_v7_d_a_batch_of_300_stills` | gui, slow | S | (gate); PASS figure of record below |
| V7 | `tests/test_app_v7.py::test_v7_f_start_up_with_a_slow_cache_open` | gui, slow | S | (gate); PASS figure of record below |
| V8 | `tests/test_app_v8_v18.py::test_v8_photo_preview_at_1_1_and_k_2_and_4_against_the_downscaled_export` | gui | S | (gate); WP4.3 figure cited below |
| V8 | `tests/test_app_v8_v18.py::test_v8_photo_k_above_1_on_real_sized_content` | gui, slow | S | (gate); WP4.3 figure cited below |
| V8 | `tests/test_app_v8_v18.py::test_dr75_an_nclx_only_p3_photo_is_displayed_through_the_profile_its_export_embeds` | gui | S | (gate); WP4.3 figure cited below |
| V8 | `tests/test_app_v8_v18.py::test_v8_video_pre_encode_through_the_harness_on_the_shells_frame` | gui | S | (gate); WP4.3 figure cited below |
| V8 | `tests/test_methods_assembly_v8.py::test_v8_preview_against_the_downscaled_export` | slow (CPU); gpu (CUDA) | S | (gate); WP4.3 figure cited below |
| V9 | `tests/test_wp41_photo_path.py::test_v9_neutral_is_the_identity` | none | P | (gate) |
| V9 | `tests/test_wp42_video_path.py::test_v9_neutral_parameters_reproduce_the_decoded_source` | none | P | (gate) |
| V9 | `tests/test_v51_video_acceptance.py::test_v9_neutral_runner_postencode` | slow | S | PASS L15 |
| V10 | `tests/test_wp41_photo_path.py::test_v10_cross_format_clash_is_numbered` | none | P | (gate) |
| V10 | `tests/test_wp41_photo_path.py::test_v10_an_existing_output_is_never_overwritten` | none | P | (gate) |
| V10 | `tests/test_wp41_photo_path.py::test_v10_custom_suffix` | none | P | (gate) |
| V10 | `tests/test_v51_video_acceptance.py::test_v10_repeated_video_exports_are_numbered` | slow | S | PASS L15 |
| V10 | `tests/test_v51_video_acceptance.py::test_v10_existing_video_output_is_unchanged` | slow | S | PASS L15 |
| V10 | `tests/test_v51_video_acceptance.py::test_v10_mov_mp4_share_one_numbering_sequence` | slow | S | PASS L15 |
| V11 | `tests/test_v51_photo_acceptance.py::test_v11_png_disk_full_removes_partial_output` | none | P | PASS L15 |
| V11 | `tests/test_v51_photo_acceptance.py::test_v11_photo_crash_leftovers_are_cleaned_at_start` | slow | S | PASS L15 / C15 |
| V11 | `tests/test_v51_photo_acceptance.py::test_d85_same_file_cleanup_preserves_installed_final` | none | P | PASS L15 |
| V11 | `tests/test_jobs_export_video.py::test_v11_an_encoder_killed_mid_stream_leaves_no_partial_output` | none | P | (gate) |
| V11 | `tests/test_jobs_export_video.py::test_a_cancel_mid_encode_leaves_nothing_and_keeps_earlier_outputs` | none | P | (gate) |
| V11 | `tests/test_jobs_export_video.py::test_a_cancel_during_the_product_sinks_close_is_aborted_and_leaves_nothing` | none | P | (gate) |
| V11 | `tests/test_jobs_export_video.py::test_v11_a_killed_export_process_leaves_only_a_temporary_that_is_cleaned_up` | slow | S | (gate) |
| V11 | `tests/test_jobs_export.py::test_cancel_at_each_phase_leaves_nothing` | none | P | (gate) |
| V11 | `tests/test_jobs_export.py::test_disk_full_from_the_sink_is_named_and_leaves_nothing` | none | P | (gate) |
| V11 | `tests/test_app_leftovers.py::test_v11_leftovers_of_a_crash_are_removed_at_the_next_start` | gui | S | (gate) |
| V12 | Chapter grouping deferred to v2 | n/a | n/a | Deferred v2 |
| V13 | `tests/test_config_presets.py::test_v13_export_then_import_reproduces_the_set` | none | P | (gate) |
| V14 | Six N5 results and decisions in docs/reports/wp1.6-gate-report.md | n/a | n/a | Recorded; PASS V14, see six-result table |
| V15 | Memory measurement owned by WP5.2 | n/a | n/a | Pending WP5.2 |
| V16 | Performance measurement owned by WP5.2 | n/a | n/a | Pending WP5.2 |
| V17 | `tests/test_wp42_video_path.py::test_v17_a_reopen_skips_the_decode_and_renders_the_same_frames` | none | P | (gate) |
| V17 | `tests/test_analysis_engine.py::test_a_complete_entry_skips_the_decode_pass_and_gives_the_same_statistics` | none | P | (gate) |
| V17 | `tests/test_cache_store.py::test_other_versions_and_unreadable_entries_are_removed_when_opening` | none | P | PASS X13 |
| V17 | `tests/test_cache_jpeg.py::test_the_format_number_was_bumped_and_a_format_1_entry_is_removed_when_opening` | none | P | PASS X13 |
| V18 | `tests/test_v51_shell_acceptance.py::test_v18_real_trim_preview_precedes_analysis_and_updates` | footage, gui, slow | S | PASS H12 |
| V18 | `tests/test_app_v8_v18.py::test_v18_a_corrected_frame_shows_before_the_analysis_completes_and_updates_after` | gui | S | (gate) |
| N10 | `tests/test_wp41_photo_path.py::test_n10_the_same_still_twice_is_identical` | none | P | (gate) |
| N10 | `tests/test_wp41_photo_path.py::test_gpu_export_reports_gpu_and_matches_the_cpu` | gpu | S | (gate) |
| N10 | `tests/test_methods_assembly_prototype.py::test_same_device_twice_is_bit_identical` | none (CPU); +gpu (CUDA) | P / S | (gate) |
| N10 | `tests/test_v51_video_acceptance.py::test_n10_video_cpu_render_digests_repeat` | slow | S | PASS L15 |
| N10 | `tests/test_v51_video_acceptance.py::test_n10_video_gpu_render_digests_repeat_and_match_cpu` | gpu, slow | S | PASS H12 |
| D91 | `tests/test_wp41_photo_path.py::test_v5_bit_depth_icc_exif_and_provenance` | none | P | (gate) |
| D91 | `tests/test_v51_video_acceptance.py::test_d91_video_provenance` | slow | S | PASS L15 |

The table's existence check is itself committed as
`tests/test_v51_traceability.py::test_acceptance_matrix_references_existing_test_functions`
(none, P, PASS L15/X13). It imports referenced modules without running their
tests, requires the exact tests/<module>.py file and a locally defined
function, and rejects stale names and a same-named module from another
folder. Parameterized function addresses stand for every instance; the
gate separately checks expanded collection identity. T10's own check is
static source reading, without imports or pytest collection.

V1 retains stage correctness, both methods, caps, mask/kernels, white
balance, normalization/weights/fusion, statistics ordering and edge-depth
cases. V3 retains the region-based synthetic flicker oracle (smoothed
flicker <= 25% of unsmoothed for each measure); no real static clip was
identified in the inventory. Real-clip subjective flicker belongs to V2.
V13 remains the existing preset round trip. V17's existing WP4.2 node
already renames the entry to a different cache_version, requires removal
on reopen and asserts a new two-decode export; the two extra cache nodes
add direct format-invalidation traceability. V2 needs CP5's owner review
(preference >= 80% and no obvious artifacts); V12 is deferred to v2;
V15/V16 require WP5.2. None of these pending/deferred rows is silently passed.

## V4, V5 and V6 observations

The runner sweep covers hevc8-bt709-full, hevc10, untagged, vfr and rotated.
All mandatory/required fidelity items and the item roster must be SAME;
VFR per-frame PTS are exact Fractions. Truncated exports its 24 readable
frames with the D86 warning and continues to the next item, exit 0.
HLG/PQ are transfer-specific refusals in a batch whose following SDR item
completes, exit 1. Untagged export and shell warnings both literally
require BT.709 and lowercase limited, with missing-word and uppercase-only
controls. T6-1's original product defect is closed by accepted WP-D54
(main 4ece5183); the rebased node is green in L13.

M6 records the real trim's best-effort presence as follows. Mandatory
fidelity and GPMF packet carry are asserted; the other presence values
are recorded rather than required to survive. All seven comparison rows
must exist, and False values are valid.

| Best-effort item | Source present | Output present |
|---|---|---|
| Creation time: container tag | true | false |
| Creation time: mvhd | true | false |
| Creation time: per-stream tags | true | false |
| GPMF gpmd | true | true |
| Timecode track tmcd | true | true |
| Timecode value | true | true |
| Camera atoms | true | true |

[WP3.10's report](wp3.10-video-encode.md), section 3, lists creation date
and time among possible not_carried items (D105/Q10); its historical
GX011627 figure instead recorded creation time SAME. Neither that report
nor [WP4.4's MOV report](wp4.4-mov-input.md) documents this exact triple
loss. These three false output rows are the current M6 observation, with
the generic WP3.10 limitation as context, not a repeat of its old figure.

V5 exports eight JPEG poses and four AD-24 HEIC poses neutrally to PNG8.
Pillow without transpose and FFmpeg rgb24 decodes of the OUTPUT are
pixel-identical; output Orientation is absent or 1. JPEG pose error is
bounded by 2/255 against Pillow's exif-transposed SOURCE, not the pristine
recipe. The recipe's 3/255 JPEG offset is a lossy-fixture property, recorded
as recipe mean rather than a product failure. HEIC retains WP4.1's AD-24
oracle. Wrong-pose controls detect swapped shape or max > 64/255. Two
independent decoders plus Orientation checks stand in for multiple viewers;
opening Windows Photos or a browser is an optional owner's CP5 leg, not
claimed as automated viewer evidence.

## V7, V8, V14 and V18 figures of record

V7 uses the 100 ms longest-gap bound. No GX011627 responsiveness
remeasurement was commissioned in WP5.1. The current record is:

| V7 scenario | Longest gap | Result | Source |
|---|---:|---|---|
| (a) Analysis | 18 ms | PASS | WP4.3 window 5 |
| (b) Scrubbing during analysis | 19 ms | PASS | WP4.3 window 5 |
| (c) File > Export | 39 ms | PASS | WP4.6 exclusive window, p99 11 ms |
| (d) 300-still batch | 56 ms | PASS | WP4.3 window 5 |
| (e) 1:1 4K render during export | 48 ms | PASS | WP4.6 exclusive window, p99 12 ms |
| (f) Startup with slow cache open | 50.6 ms | PASS | WP4.3 window 5 |

Sources: [WP4.3 application-wiring report](wp4.3-application-wiring.md),
V7 table/window 5, and [WP4.6 accept record](../proofs/wp4.6-accept.md),
V7 window 08:46-09:08Z on 1563da2a. **DR-98 is CLOSED** at WP4.6's accept
(main bbb4ef3e). The old WP4.3 (c)/(e) 180-182 ms STOPs are historical
and superseded by those accepted figures. WP4.6's 67 ms batch control
does not replace the commissioned WP4.3 56 ms figure in this matrix.

V8 keeps AD-11 as amended: k=1 exact; real-sized stills at k>1 have
mean <= 1/255 and p99 <= 2/255 at k=2, <= 4/255 at k=4; video at k=2
has p99 <= 2.5/255 per frame, mean <= 1/255. Max/p99.9 are recorded.
The [WP4.3 V8 record](wp4.3-application-wiring.md) reports GX011627
window 3 frame 510 p99 2.011/255, and window 4's 16-frame p99 maximum
1.946/255 (median 1.169/255), mean maximum 0.132/255; the shown frame
equals the harness preview. These are cited figures, not new measurements.
Real-sized archived-frame tests retain their availability skips below.

V14 is satisfied by recording all six N5 results with decisions, not by
retroactively labelling every prototype performance target a pass.
The [WP1.6 prototype gate report](wp1.6-gate-report.md), V14 record,
closed at CP3 on 2026-10-20, is the source:

| N5 result | Outcome of record | Decision |
|---|---|---|
| Speed | 4K core missed original N6 by 3.6x (ancuti2018), 5.8x (c3); measured export 4.4x, estimated c3 6.6x | Owner Option C: interim 25 min/min, WP3.21 optimization, WP5.2 remeasure |
| Peak memory | Video holds: 3,682 MiB RSS, 2,860 MiB graphics at 4K; photo pending in that historical record | Limit retained; current V15 assigned to WP5.2 |
| Look check | Shallow and deep CP2 complete, c3 default | Spec v0.5.3 applied |
| Gain-cap noise | Caps KEEP; c3 lowest noise | Owner kept caps |
| Staged/flat statistics | No visible difference | One stage permitted; IF-3 staged |
| Container spike | SIMPLE meets mandatory items | WP3.10 as planned |

V18 on the full GX011627 remains the WP4.3 window-3 record: corrected
frame with statistics None while analysis runs, then statistics equal to
smoothed_record at the shown PTS (681 frames, 68.7 s analysis). That
window's EXIT 1 was its then-over-bound V8 reading, not a V18 failure.
The new automated trim leg H12 additionally records provisional/original
pixel change max **73/255**, followed by a same-PTS post-analysis change
max **3/255**, mean **0.5784706147119342/255**, and equality to the smoothed
statistics. An unchanged provisional copy is rejected. The older
test_app_v8_v18.py:421 only checks not-None before analysis; it is unchanged
and is strengthened by this new node rather than treated as its own
provisional-correction proof. The older test_app_wiring.py untagged row
likewise has words=""; the new shell node explicitly checks both D54 words.

## V9, N10, provenance and tolerances

AD-11's V9 decoded-RGB/pre-encode bound remains max 2/255, mean 0.2/255,
with encoder and 8-bit Y'CbCr conversion excluded. Photo depth reduction
uses the ruled quantized reference. N10 requires bit-identical pre-encode
pixels on one device. CPU/GPU render bounds remain max 2e-3, mean 2e-4
in [0,1] values; H12 records max **6.556510925292969e-07**, mean
**7.77701347100514e-08** on the first rendered frame. Both CPU and GPU
runs repeat every one of 45 PTS digests identically. Output-file byte
identity is True in these runs, recorded only; libx265 determinism is
not a requirement. Decoded CPU/GPU first frames are equal (max 0.0);
equality/within-one-code is observed, with no sub-quantum bound asserted.

CHARC 2bd14e3a set the distinct runner post-encode characterisation bound
`RUNNER_POSTENCODE_MEAN = 3.5` in 1/255 units at libx265/standard.
It does not change the encoder-free `PAIR_MEAN_SYNTHETIC = 2.5` or the
real-pair 1.0 characterisation in test_color_roundtrip.py. The measured
neutral runner figures (T12 record, unchanged algorithms in L13) are:

| Sample / quality | Mean absolute error, 1/255 | Maximum, recorded only |
|---|---:|---:|
| hevc8-bt709-full / standard | 2.9538159722222224 | 183 |
| untagged / standard | 2.7881037808641977 | 203 |
| rotated / standard | 2.9538159722222224 | 183 |
| hevc10 / standard | 2.472876682318937 | 183 |
| hevc8-bt709-full / high, characterisation only | 2.52132896090535 | 125 |

The +8/255 red-channel control gives mean 4.837543595679012, exceeding
3.5 by 1.337543595679012, and fails by the bound's name. Maxima 183-203
are recorded rather than bounded; a mean bound can miss sparse or small
errors. The high-quality figure is one characterisation, not a changed
shipped setting or another acceptance bound. Colour tags and rotation
remain asserted separately for every neutral output.

No further tolerance proposal is pending from the cell. CHARC's accept
NOTE remains: V9's AD-11 bound binds pre-encode; the runner post-encode
leg is characterised at 3.5/255 mean at shipped quality. AD-11 and existing
test constants are unchanged. D91 verifies default-on parseable video
provenance against app_version and requested parameters, an absent comment
when disabled, and the source name without a path; photo provenance is
covered by the existing V5 node. V10 asserts repeat/collision/MOV-MP4
numbering, preserved pre-existing bytes and unchanged sources.

## V11, STOPs and SKIPs

The ENOSPC node faults the real PNG binary temporary after >=1 KiB of
actual writes, scoped by output path, then requires exit 1, named
disk-full wording, no final/temporary and unchanged source MD5. It rejects
an unrelated named failure. The real crash batch uses 40 copies of the
largest committed fixture (96x64, a maximum-area tie), 10 ms polling,
the real interpreter with matched worktree package, explicitly proved UTF-8
mode/stderr encoding, a PID-file equality assertion and the post-wait
names/sizes witness. A timed-out wait kills/reaps, records the attempt
and retries within the existing 20-attempt rule; the import probe allows
60 s. Complete earlier outputs
are preserved, partial finals are rejected and startup removes surviving
temporary names. A complete installed final sharing the temporary's hard
link survives cleanup byte-identically.

**The deterministic D85 same-file probe, not the race, is the D85 witness.**
It rejects a byte-identical unrelated copy, then hard-links temporary/final,
runs actual cleanup and requires only the temporary name disappear. Natural
race observations include same-file-final and complete-with-no-temporary;
no-final is established by independent branch probes. Historical completed
final counts 1, 3, 4, 5 and 7 are race characterisations, not bounds.

| STOP / finding raised | Evidence and disposition |
|---|---|
| R0-1: JPEG pristine-recipe error already 3/255 | CHARC cdeefe5f: bound oriented source at 2/255; recipe mean recorded; unequal shape detects rotated pose. Fixture issue, no product defect. |
| R0-2: PNG cannot reach 64 KiB | CHARC cdeefe5f: real Path.open seam, ENOSPC after 1 KiB actual writes, firing proved; no product change. |
| R0-3: truncated fixture is readable | CHARC cdeefe5f: D86 readable-prefix success/warning, 24 frames, batch exit 0; not a failed item. |
| R0-4: sweep sizing conflicts with named containers | CHARC cdeefe5f: use committed sweep unchanged; derived cases keep AD-30 sizing. |
| T2-1: crash rejects already-completed batch outputs | CHARC 755ef1b0: complete earlier outputs may survive; independently verify/preserve them. No product defect. |
| T3-1: kill between link and unlink leaves two names | CHARC da72ec04: installed complete same-file final is valid; remove only temporary on startup. No product defect. |
| T4-1: observed temporary can commit before kill | CHARC 8276adb5: record no-survivor attempt and retry; cleanup assertions require a surviving temporary. Deterministic D85 witness added. |
| T6-1: runner D54 warning lacks BT.709/limited words | Confirmed product defect; CHARC 3a1497d6 routed WP-D54; accepted on main 4ece5183, branch rebased, unchanged literal assertion green. |
| T6-2: runner standard-quality mean exceeds 2.5/255 | CHARC 2bd14e3a: distinct 3.5/255 post-encode characterisation, high-quality observation and control; AD-11 pre-encode unchanged. |
| Serial allowance flagged at mixed-condition 191.68 s before T7/T8 | Same ruling raises package allowance 180 -> 300 s; this sum was not a measured serial delta; gate comparison remains pending. |
| Reviewer A R1 crash flake | Real venv launcher leaves child alive past wait; fixed with real interpreter, stable-output witness, then R2 PID/package pin. C13 15/15 passed. |
| Carried V7 (c)/(e) STOPs, DR-98 | WP4.6 accepted; closed on main bbb4ef3e; 39/48 ms figures cited above. |
| Session-depth yields | Fresh-session boundaries at dispatcher depths 210,098; 194,928; 177,474; 191,275; 238,374. Procedural yields, not product defects; session 6 continues from the committed ledger. |

No new STOP is open in WP5.1. Historical REDs stayed literal until the
ruling or owning-package fix; none was hidden with xfail. Reviewer A R1
F3 is REJECTED-WITH-RULING under CHARC c39cc00d, which withdrew the
conflicting sentence and confirmed 8276adb5's end-state retry/SKIP rule.

| SKIP / exclusion | Actual status and reason |
|---|---|
| New WP5.1 nodes in development/returned seat evidence | **0 observed skips.** L13's four deselections are G2, GPU N10 and two shell nodes, all separately returned PASS, not skipped. |
| Crash: no surviving temporary in 20 attempts | Allowed SKIP `not observable at this size`; never observed in recorded successful suite runs. C13 attempts were 1,1,1,1,1,1,2,1,1,1,1,1,1,2,2; all 15 reached cleanup, no skip. T12's 15 isolated passes all used attempt 1. |
| Turn-15 crash observations | C15: 15/15 cleanup on attempt 1, no skips; forced single writer-wait timeout was recorded/retried, then cleanup passed on attempt 2 (t15-timeout-probe.log/xml, 1 passed in 4.39 s). |
| Hardware/source availability | GPU form can skip if no usable CUDA device; footage fixture can skip without configured footage. Neither occurred in returned seat runs; the final gate must use the configured host. |
| Prior main gate: standing swscale case | WP-D54 parallel had 1 skip: yuvj is read as full regardless of in_range, so that planted range-misread case is refused; not a new WP5.1 skip. |
| Prior main gate: archived look-check content | WP-D54 serial had 11 skips: absent frames archived to D:, 1 shell V8 crop, 5+4 method V8 cases, 1 WP4.1 V8 crop. Existing availability guards unchanged; no current-candidate skip count invented. |
| Final whole-set gate skips | (gate); exact nodes/reasons copied from the accept record. |

## Reviews and verification

| Reviewer A round | Critical | Major | Minor | Advisory | In/out | NEW/REOPENED | Result |
|---|---:|---:|---:|---:|---|---|---|
| 1 | 0 | 1 | 2 | 5 | 8/0 | 8/0 | NEW_CRITICAL_MAJOR_FOUND; real-interpreter crash, provisional/original check and five advisory fixes; F3 rejected by CHARC ruling |
| 2 | 0 | 0 | 2 | 5 | 7/0 | 7/0 | NO_NEW_CRITICAL_MAJOR; **converged**, terminating cleanup applied |

Both passes were Claude (`claude-opus-5-5`, high requested), run by the
dispatcher on the Codex lane, read-only. R1: exit 0, is_error false,
39 turns, worktree clean; R2: exit 0, is_error false, 36 turns,
worktree clean. No reverts; product fixes by this package 0. R2 pins
writer PID/package, disables automatic site startup before restoring
explicit venv paths, verifies traceability module files, strengthens D54
controls and removes the unused subprocess wrapper. R2's V17 missing-half
premise is rejected by the existing third-export re-analysis assertions;
the two requested extra addresses were nevertheless added. Retained pytest
sys.path entries are a banked harness limitation; tools is prepended and
the package identity is asserted. No pristine script-start environment
is claimed. External review evidence remains at the dispatcher's r1/r2
locations; the ledger carries adjudication, not copied review transcripts.

Turn 13 checks on the rebased tree: ruff clean; mypy clean on 148 source
files; changed blobs 0 CR (dispatcher confirmation). The code was formatted
within owned files; format --check remains a seat gate check. Every suspected
issue was independently reproduced or refuted, fixed within scope, then
rechecked. The launcher mutant now fails specifically on PID mismatch,
wrong-package and wrong-module controls fail by name, and legitimate local
nodes pass. No pytest, ruff or mypy was run during this T10 documentation
turn because an exclusive host measurement window was open.

## Reviewer B

Claude opus, high, at the orchestrator's seat on `7ab7bd39` returned
**NO_NEW_CRITICAL_MAJOR**: 34 passed, 2 deselected in 139.90 s, including
the real crash node. All four executed product mutants were caught
(abort omitted, orientation dropped, 6/8 swapped, D63 Orientation kept);
claims 1-7 held. The external B/review.txt remains outside the repository.
The dispatcher's turn-15 adjudication authorizes this terminating cleanup.

| Item | Severity / disposition | Result |
|---|---|---|
| B-1 | ADVISORY, no change by binding ruling | Case-sensitive `limited` remains the ruled reading of CHARC f6252e0b. |
| B-2 | MINOR, accepted / fixed | Real interpreter adds `-X utf8`; the import probe asserts UTF-8 mode and stderr encoding despite `-I`. |
| B-3 | MINOR, accepted / fixed | Writer wait timeout kills/reaps and records a retry within 20 attempts; import probe allows 60 s. Forced timeout control reaches cleanup on attempt 2. |
| B-4 | ADVISORY, accepted / fixed | Names-only guard rejects relative file paths with either separator in nested provenance/fidelity data and printed text; controls cover both spellings. |
| B-5 | ADVISORY, accepted / fixed | Encoder-free colour-pair node removed from V9's matrix and Python roster; its characterisation remains context in the tolerance section. |
| B-6 | ADVISORY, accepted / fixed | Display-matrix side-data orientation added to the tag-mutation loop; omission mutant fails at the new control. |
| B-7 | ADVISORY, accepted / fixed | Traceability rejects skip/xfail marks by node name; both controls exercised. Conditional skipif remains allowed. |
| B-8 | ADVISORY, out of envelope / banked | D85 hard-link witness requires hard-link support: the configured C: NTFS temp root is in envelope; exFAT/FAT is outside it. |

Limit (B-8): the deterministic D85 `os.link` witness requires hard-link
support and cannot run with a temp root on exFAT/FAT.

After cleanup, **L15 is 34 passed, 4 deselected, no skips in 162.53 s**;
**C15 is 15/15 isolated crash passes**, no skips. RED controls reproduced
the prior relative-path and skip-mark gaps; an omission mutant is caught
by the new display-matrix mutation. The traceability controls then passed.
Ruff and format-check pass on the support/four modules; mypy passes on
148 configured source files. Evidence is t15-light.log/xml,
t15-crash-repeat.log, t15-red-paths.log, t15-red-marks.log,
t15-red-orientation.log, t15-trace.log, t15-ruff.log, t15-format.log and
t15-mypy.log. The single whole-set gate and its figures remain pending below.

## Whole-set gate and serial-leg delta

Figures recorded at the gate by the orchestrator (accept record `docs/proofs/wp5.1-accept.md`); this section is filled from it in the accept commit.

The gate runs AFTER Reviewer B on the final rebased candidate, with
PYTEST_ADDOPTS unset, offscreen QPA, correct local configuration and no
other heavy work. No sandbox shim at the seat. Parallel uses -n 4;
serial and the ONE fullclip leg run alone. Collection must establish
P + S + F = all, pairwise disjoint. Static checks and 0-CR blobs are
also recorded by the orchestrator. The named DR-99 telemetry-origin
failure is exempt only under the brief's same-alone-on-main condition;
any other gate failure is a STOP. It passed in the cited prior main gate.

| Final candidate / check | Passed | Skipped | Failed | Deselected / selected | Wall seconds | Exit / source |
|---|---|---|---|---|---|---|
| Candidate and base ids | (gate) | (gate) | (gate) | (gate) | (gate) | (gate) |
| Parallel P | (gate) | (gate) | (gate) | (gate) | (gate) | (gate) |
| Serial S | (gate) | (gate) | (gate) | (gate) | (gate) | (gate) |
| Fullclip F, ONE run | (gate) | (gate) | (gate) | (gate) | (gate) | (gate) |
| Collection identity, no duplicates / overlaps | (gate) | (gate) | (gate) | (gate) | (gate) | (gate) |
| Ruff / format / mypy / LF checks | (gate) | (gate) | (gate) | (gate) | (gate) | (gate) |

Two serial baselines are preserved rather than mixing their populations:

| Baseline | Serial result | Wall seconds | Use |
|---|---|---:|---|
| [WP-T6 sizing](wp-t6-gate-sizing.md), final gate SERIAL AFTER | 1,136 passed, 1 skipped | 1,389.24 (1,389 rounded) | Historical sized-gate floor named by the brief |
| [WP-D54 accept](../proofs/wp-d54-accept.md), g30-wpd54 attempt 2, of record | 1,230 passed, 11 skipped, 0 failed | 1,606 | **Primary current comparison**, latest completed main gate on this branch; alone on host |

WP-D54's first serial attempt hung and was killed; it is not the baseline.
Its accept record assigns the hang/stall-watch issues to DR-108/DR-109.
The second attempt is the recorded passing leg. The historical WP-T6 and
recent main populations differ; a whole-leg timing delta alone cannot
attribute all change to WP5.1. Record both deltas and the new serial nodes'
contribution at the gate, without substituting a mixed-condition sum.

| Serial addition / comparison | Figure | Rule / interpretation |
|---|---|---|
| New WP5.1 serial node count and measured time contribution | (gate) | Marked addition measured in the leg; development figures are not this value |
| Final serial wall minus primary WP-D54 1,606 s | (gate) | Primary contemporary leg delta |
| Final serial wall minus historical WP-T6 1,389.24 s | (gate) | Historical floor comparison |
| Package serial addition against allowance | (gate) | <= 300 s per CHARC 2bd14e3a; over allowance goes to CHARC, never hidden behind fullclip |
| Final skips with reasons / any STOP disposition | (gate) | Accept record names exact nodes and outcomes |

The accept commit fills these figures and dispositions from its gate
record. V2/CP5, V12/v2 and V15/V16/WP5.2 retain their separate owners and
are not completed by a green automated gate.
