# WP-T8 tools, cache guard and suite-cost paydown

Status: groups 1 and 2 are committed at `90fd9263` and `d558c48a`;
Reviewer A cleanup is `0e784986`, followed by the Reviewer B follow-up
(this revision, after merge `a844a37f`).
The DR-116 archive analysis and item (d)'s apply step are CLOSED with no
reduction applied, by CHARC's generation-15 ruling at 11:17Z on 2026-11-04.
DR-116 closes at acceptance on the attribution; its host-load-or-creep
hypothesis is refuted. Reviewer A round 1 found no new critical/major;
Reviewer B also found no new critical/major. This revision addresses its
minor and granted advisories. The final three gate legs and acceptance
await the dispatcher. WP-T8 does not claim a
measured reduction in serial-leg time.

## Changes and regression coverage

The implementation below includes `90fd9263`, `d558c48a`, Reviewer A's
`0e784986`, and this revision's Reviewer B follow-up.
Historical RED witnesses and development results are recorded in
`C:/Users/rwsmy/clearwater-review-evidence/wp-t8/cell/return-2.md` and
`return-3.md`; their earlier interpreter problem is qualified below.
The current seat result is the validation of record.

| Register item | Change | Regression test in `tests/` |
|---|---|---|
| DR-119(c) | `tools/export_bench.py::_write` uses `atomic_write_text`: write and close a temporary sibling before replacing the final JSON. The completed run's ROW prints and flushes before that replacement, so its figures survive a blocked JSON publication. | `test_export_bench.py::test_record_interrupt_preserves_the_previous_publication[False]` and `[True]` preserve an absent or previous final file after an interrupted write; `test_record_updates_replace_the_complete_json` checks repeated successful replacement and temporary cleanup. `test_completed_run_prints_its_row_before_a_record_permission_error` checks the completed figures and readable propagated `PermissionError`. |
| DR-119(d), V3 output | `tools/halo_part3.py::main` builds the V3 run in staging, publishes after JSON and table are complete, and abandons interrupted staging under a failed name. | `test_tools_halo_part3.py::test_v3_interrupt_publishes_no_final_folder`; `test_v3_publishes_the_record_and_table_together` covers success and the diagnostic STOP status. |
| DR-119(d), overlap and documentation | `wholeset-run` refuses a resolved cache equal to or below `<out>/items` before processing. `build_sheet` documents `sheet-<stamp>/sheet.json`. | `test_tools_halo_part3.py::test_wholeset_refuses_a_cache_inside_the_items_folder` covers equality and a nested cache, with no processing or output creation; existing sheet tests cover the published record. |
| DR-119(e) | `tools/n6.py` defines `N6_MIN_PER_MIN` and `FRAME_BUDGET_S_29_97`. `core_speed.py` and `export_bench.py` import the shared target. The module names D106, spec v0.5.8 and the owner's ruling date. | `test_core_speed.py::test_the_bar_is_d106_at_29_97_fps` extracts the current target from the spec's N6 line, checks both instruments and the frame conversion. |
| DR-120 | `tests/fixture_plugin.py::sample_provider` uses `tmp_path_factory.getbasetemp()/fixtures-generated` when basetemp is explicit, including xdist's worker basetemp. Only a non-xdist run without basetemp reaches Git discovery of the main checkout's `work/fixtures/generated`; failed Git discovery warns once with the error reason and falls back to the session basetemp. An unwritable cache falls back under basetemp. Pytest deletes an explicit basetemp at session start, so every run of that root regenerates the cache (about 4 s per root, charged to its first consumer); later serial figures are not strictly comparable with the DR-116 pair on that account (Reviewer B, B3). Each fresh root costs about 3.3 s generation + 0.7 s verification and 89,227,437 bytes; up to four parallel worker roots cost about 357 MB, plus serial/fullclip roots if used (Reviewer A measurement, F2, source below). | `test_fixtures.py::test_generated_cache_prefers_an_explicit_basetemp`, `test_generated_cache_without_basetemp_uses_the_main_checkout`, `test_generated_cache_without_git_uses_the_basetemp`, and `test_relocated_session_cache_keeps_the_manifest_content`. The fallback test covers missing Git, a non-checkout and timeout; the content test checks the unchanged manifest. |
| DR-118 | Only `DiskProxyCache._entry_for_write` changes in product code. It refuses a pre-existing symlink, junction or nondirectory, logs a WARNING naming the path and raises `OSError`, preserving the path and target. | `test_cache_store.py::test_a_write_refuses_a_preplanted_junction[proxy]` and `[statistics]` check refusal, warning, unchanged sentinel bytes and the surviving junction. Creation failures skip with an explicit platform/filesystem reason. Added `test_a_write_refuses_a_preplanted_file[proxy]` and `[statistics]` check the readable refusal, WARNING naming the file, and unchanged bytes, without platform privileges. |
| DR-116 / DR-86 | Join the archived serial JUnits by `(classname, name)`, retain parameter suffixes, reconcile wall and node changes, and update banked candidate costs. Item (d)'s apply step is CLOSED with no reduction applied by CHARC's ruling; DR-86 candidates stay banked. | The stdlib analysis script checks unique keys, suite counts, skips, no errors/failures, the complete wall reconciliation, module sums and the fixed historical tail membership. Independent XML/CSV checks are recorded below. |

The N6 label remains 12 minutes per minute and 0.4004 seconds per frame
at `30000/1001` fps. Source: `tools/n6.py` and the N6 line of
`docs/underwater-correction-spec.md` (D106, v0.5.8). The stale product
instrument label is gone; the historical prototype budgets in
`tools/prototype/bench.py` and `tools/prototype/clip.py` are untouched.
No figure of record changes.

DR-118's extra nondirectory refusal is accepted by CHARC because the
previous `mkdir(exist_ok=True)` would already raise at that path. It now
fails earlier with the same readable refusal as a link. The scan silently
skips links; the write path raises `OSError`, not a custom store error.
This abnormal planted-path case fails the job; it does not continue
uncached. These are the binding round-0 ruling and group-1 disposition,
recorded in `docs/briefs/wp-t8-brief.md` (CHARC's round-0 ruling), its
TURN-4 dispatch disposition, and DR-118's paydown text in
`docs/debt-register.md` ("a link or not a directory"). The durable
TURN-4 dispatch is
`C:/Users/rwsmy/clearwater-review-evidence/wp-t8/cell/dispatch-4.md`.
No cache format or ordinary-path behavior changes.

The DR-120 per-root cost is Reviewer A's F2 measurement in
`C:/Users/rwsmy/clearwater-review-evidence/wp-t8/A/r1/review.txt`.
An xdist developer run without `--basetemp` still gets explicit
`popen-gwN` worker basetemps under `%TEMP%`, so each worker generates
there instead of reaching the main-checkout rule. This is additional
generation and storage per fresh root, not changed fixture content.
The non-xdist no-basetemp path falls back if Git is missing,
times out, or reports that the directory is not a checkout, using
`tmp_path_factory.getbasetemp()/fixtures-generated`. A single warning
names that contained fallback and the Git error's one-line reason.
Git path output is decoded explicitly as UTF-8. The existing
unwritable-main-cache fallback still applies.

## Validation environment and the resolved STOP

Sources: the binding generation-42 dispatches in
`C:/Users/rwsmy/clearwater-review-evidence/wp-t8/cell/dispatch-4.md`,
`dispatch-5.md` and `dispatch-6.md`, and the durable seat logs below.
These seat results were supplied by the dispatcher; the cell did not
read the main checkout's work folder. The sandbox STOP is recorded in
`C:/Users/rwsmy/clearwater-review-evidence/wp-t8/cell/return-4.md` and
the full cell transcript `cell/turn-4.txt` under the same evidence root.

The worktree `.venv` was created empty at 10:08Z and remained empty until
the seat ran `uv sync --frozen` at 10:58Z on 2026-11-04. Earlier
`uv run --no-sync pytest` results came from another interpreter. The
environment's `VIRTUAL_ENV` pointed at the main checkout's `.venv`;
the TURN-4 log shows uv now ignoring that value in favor of the project
environment. The synced worktree imports Clearwater from its own `src`.
The earlier failure attribution is superseded by the seat checks below.

| Check | Result | Evidence source |
|---|---|---|
| Three fixture audit tests on main | 3 passed | `C:/Users/rwsmy/clearwater-review-evidence/wp-t8/seat/fixaudit-main.log` |
| Same audit tests in the synced worktree at `d558c48a` | 3 passed | `C:/Users/rwsmy/clearwater-review-evidence/wp-t8/seat/fixaudit-wpt8b.log` |
| Five-module set at the seat, outside the sandbox, no shim | 488 passed, 2 deselected in 138.86 s | `C:/Users/rwsmy/clearwater-review-evidence/wp-t8/seat/wpt8-rerun-seat.log` |
| Three audit tests at the seat with `PYTHONPATH=scripts` and the mkdir shim | 3 passed | `C:/Users/rwsmy/clearwater-review-evidence/wp-t8/seat/wpt8-rerun-shim.log` |
| Same five-module set inside the Codex sandbox, with the shim | 485 passed, 3 failed, 2 deselected in 144.53 s | `C:/Users/rwsmy/clearwater-review-evidence/wp-t8/cell/return-4.md`, `cell/turn-4.txt` |

The five modules are `test_export_bench.py`, `test_tools_halo_part3.py`,
`test_core_speed.py`, `test_cache_store.py` and `test_fixtures.py`.
The two commits add no test module. The cell used this command from
PowerShell, with all runner output redirected to the log above:

```powershell
$env:PYTHONPATH = 'scripts'
uv run --frozen pytest tests/test_export_bench.py tests/test_tools_halo_part3.py tests/test_core_speed.py tests/test_cache_store.py tests/test_fixtures.py --basetemp=C:/Users/rwsmy/clearwater/.worktrees/wp-t8/work/ct8-4 -p sandbox_mkdir_shim -p no:cacheprovider -m 'not gpu and not footage and not gui and not slow and not fullclip'
```

The sandbox failures are the two generator read/write audits, each
recording an unexpected `nul` access, and the process audit, recording
56 launches versus 55 FFmpeg/FFprobe launches. The cell stopped as
instructed. The seat reproduced the set outside the sandbox and ruled
the residual sandbox-only: the restricted child adds the `nul` open
and extra launch. Neither the code nor the shim causes it. The seat
run is of record; no DR row is requested. TURN 5 authorizes continuation
without another test run.

## DR-116 sources and method

The archived stdlib script is
`C:/Users/rwsmy/clearwater-review-evidence/wp-t8/dr116/dr116_table.py`.
Its CSV/JSON/Markdown outputs are under
`C:/Users/rwsmy/clearwater-review-evidence/wp-t8/dr116/dr116/`.
The cell ran the script on worktree copies; the durable original inputs
are the sources of record below. All timing tables derive from them
unless a historical source is explicitly named:

| Label | Archive source | MD5 |
|---|---|---|
| BEFORE | `C:/Users/rwsmy/clearwater-review-evidence/wp-t6/work-copy/wp-t6/gate-g1/serial.xml` | `5b88c916589c843e09dd2815f0e58f17` |
| AFTER | `C:/Users/rwsmy/clearwater-review-evidence/release-1.0.0/g40-p55-serial.xml` | `93beab292d38c7c7b28dcfc22100f242` |

The copies were supplied as identical to the archives. The script computes
the hashes above from the worktree copies; this turn does not re-open the
archives. BEFORE has the same suite count and time as
`docs/reports/wp-t6-gate-sizing.md`, final gate: 1,137 tests, 1,389.176 s
JUnit suite time. That report's pytest wall is 1,389.24 s, rounded to
1,389 s in the register. The copied XML is the correct baseline, not a
restricted W3 development run. The XML timestamps identify starts on
2026-10-29 for BEFORE and 2026-11-03 for AFTER, on the same named host;
they do not establish equal host load.

The join uses the complete JUnit `(classname, name)` pair. Duplicate
keys are errors. A changed name is counted as absent/new rather than
guessed to be a rename. The module aggregate takes the classname prefix
through its `test_*` module component. Testcase times include setup, call
and teardown; a shared fixture is generally charged to its first consumer.
The wall outside testcase timing is suite time minus their sum. It can
include collection and runner work; JUnit alone cannot split that residual
or assign all session fixtures to it. Per-node fixture attribution can
move when test ordering changes.

Outputs retained for the dispatcher to archive:

- `C:/Users/rwsmy/clearwater-review-evidence/wp-t8/dr116/dr116/summary.json`: sources, hashes, totals, ratios, skip changes and DR-86 group sums.
- `C:/Users/rwsmy/clearwater-review-evidence/wp-t8/dr116/dr116/joined.csv`: every joined row, status, module, both times, delta and ratio.
- `C:/Users/rwsmy/clearwater-review-evidence/wp-t8/dr116/dr116/modules.csv`: all module aggregates, descending signed delta.
- `C:/Users/rwsmy/clearwater-review-evidence/wp-t8/dr116/dr116/top40-delta.csv`: shared nodes ranked by absolute delta.
- `C:/Users/rwsmy/clearwater-review-evidence/wp-t8/dr116/dr116/top40-new.csv`: new nodes ranked by AFTER cost.
- `C:/Users/rwsmy/clearwater-review-evidence/wp-t8/dr116/dr116/new.csv` and `removed.csv`: all additions/removals with their module.
- `C:/Users/rwsmy/clearwater-review-evidence/wp-t8/dr116/dr116/status-changes.csv`: shared nodes whose pass/skip status changed.
- `C:/Users/rwsmy/clearwater-review-evidence/wp-t8/dr116/dr116/dr86-nodes.csv`: exact membership and times for every banked group, including the frozen historical tail.
- `C:/Users/rwsmy/clearwater-review-evidence/wp-t8/dr116/dr116/tables.md`: complete module table and both top-40 tables.

The script and outputs are already copied to the durable analysis
folder above, outside the releasable worktree. They are evidence, not
deliverable Git blobs. Reproduction must copy them and the inputs to
an authorized working folder before running the script.

### Totals and attribution

Source: both copied JUnits and `C:/Users/rwsmy/clearwater-review-evidence/wp-t8/dr116/dr116/summary.json`.
Counts include skipped nodes; both XMLs have zero failures and errors.

| Quantity | BEFORE | AFTER | AFTER minus BEFORE |
|---|---:|---:|---:|
| Test count | 1,137 | 1,273 | +136 |
| Skips | 1 | 11 | +10 |
| Suite seconds | 1,389.176 | 2,049.135 | +659.959 |
| Sum of testcase seconds | 1,386.069 | 2,045.965 | +659.896 |
| Seconds outside testcase timing | 3.107 | 3.170 | +0.063 |

| Join category | Nodes | Contribution to wall delta (s) |
|---|---:|---:|
| Present in both, AFTER minus BEFORE | 1,131 | +43.227 |
| Only in AFTER, full AFTER cost | 142 | +616.724 |
| Only in BEFORE, subtract BEFORE cost | 6 | -0.055 |
| Outside-testcase wall change | Not a node set | +0.063 |
| Reconciled total | 1,131 + 142 = 1,273 AFTER; 1,131 + 6 = 1,137 BEFORE | +659.959 |

Most added wall is in new node IDs. The shared-node total needs the
status split: the real-photo test moved from a 0.119 s skip to a
249.952 s pass (+249.833 s). Ten V8 nodes moved from pass to skip
because look-check frames were absent (-56.759 s). The remaining
shared nodes, with unchanged pass status, total -149.847 s. Thus
`249.833 - 56.759 - 149.847 = 43.227`. The AFTER XML's additional
new V8 skip makes its skip count eleven. Skip messages are retained
in `summary.json`; no working-folder media was read for this analysis.
Those skips are coverage limits, not optimizations.

For shared nodes above 0.5 s BEFORE, AFTER/BEFORE has median 0.9413
and p90 1.0974 across 168 nodes (p10 0.5295). Excluding pass/skip
transitions leaves 158 nodes, median 0.9594, p90 1.1090
(p10 0.6125). Percentiles use linear interpolation at `(n-1)*p`.
These ratios do not show uniform positive host slowdown in this pair.
New coverage, changed skip status and particular faster nodes explain
the net growth arithmetically. The archive cannot establish the cause
of each test's change or explain every earlier wall in DR-116's series.

### Module costs

Source: `C:/Users/rwsmy/clearwater-review-evidence/wp-t8/dr116/dr116/modules.csv`. The following are the largest
positive deltas and largest declines; the CSV and `tables.md` contain
every module. Module labels below omit the common `tests.` prefix.

| Module | BEFORE s | AFTER s | Delta s | Status (BEFORE -> AFTER) |
|---|---:|---:|---:|---|
| `test_photo_check` | 0.119 | 249.952 | +249.833 | 1 skip -> 1 pass |
| `test_v51_video_acceptance` | 0 | 201.060 | +201.060 | absent -> 20 pass |
| `test_v51_shell_acceptance` | 0 | 74.445 | +74.445 | absent -> 2 pass |
| `test_wp44_mov_input` | 0 | 58.575 | +58.575 | absent -> 1 pass |
| `test_app_v7` | 0 | 57.528 | +57.528 | absent -> 6 pass |
| `test_app_preview_fft` | 0 | 46.449 | +46.449 | absent -> 14 pass |
| `test_app_wiring` | 0 | 42.842 | +42.842 | absent -> 29 pass |
| `test_app_export_worker` | 0 | 35.645 | +35.645 | absent -> 23 pass |
| `test_reviewpack` | 0 | 25.120 | +25.120 | absent -> 3 pass |
| `test_app_v8_v18` | 0 | 13.343 | +13.343 | absent -> 6 pass, 1 skip |
| `test_app_leftovers` | 0 | 11.410 | +11.410 | absent -> 3 pass |
| `test_app_startup` | 0 | 10.181 | +10.181 | absent -> 10 pass |
| `test_jobs_export_video` | 276.984 | 255.759 | -21.225 | 9 pass -> 9 pass |
| `test_io_video_encode` | 158.048 | 136.315 | -21.733 | 18 pass -> 20 pass |
| `test_prototype_clip` | 168.275 | 139.725 | -28.550 | 10 pass -> 10 pass |
| `test_methods_assembly_v8` | 47.192 | 1.027 | -46.165 | 9 pass -> 9 skip |
| `test_prototype_backend` | 74.491 | 25.775 | -48.716 | 18 pass -> 18 pass |

### Largest shared-node deltas

Source: `C:/Users/rwsmy/clearwater-review-evidence/wp-t8/dr116/dr116/top40-delta.csv`. This is the requested top
ten by absolute delta, including improvements and status changes.
Node IDs below use `tests/<module>.py::<name>` for readability;
the CSV retains the exact classname and name join keys.

| Node | BEFORE s | AFTER s | Delta s | Status (BEFORE -> AFTER) |
|---|---:|---:|---:|---|
| `test_photo_check.py::test_the_real_photo_leg_reads_and_round_trips_the_owners_photos` | 0.119 | 249.952 | +249.833 | skip -> pass |
| `test_prototype_backend.py::test_bench_gpu_records_graphics_memory` | 63.021 | 14.114 | -48.907 | pass -> pass |
| `test_prototype_clip.py::test_bench_whole_clip_modes_record_their_pass` | 67.228 | 43.231 | -23.997 | pass -> pass |
| `test_wp41_v8.py::test_v8c_k_above_1_on_real_sized_content` | 10.722 | 0.128 | -10.594 | pass -> skip |
| `test_jobs_export_video.py::test_gx011627_through_the_engine_keeps_every_mandatory_and_required_item[trim]` | 88.511 | 78.964 | -9.547 | pass -> pass |
| `test_io_video_encode_bench.py::test_run_once_records_the_row_and_deletes_the_output` | 24.253 | 14.809 | -9.444 | pass -> pass |
| `test_methods_assembly_v8.py::test_v8_planted_range_error_fails` | 9.040 | 0.130 | -8.910 | pass -> skip |
| `test_methods_assembly_v8.py::test_v8_preview_against_the_downscaled_export[GX011625_0024.925-c3-cpu]` | 8.271 | 0.105 | -8.166 | pass -> skip |
| `test_methods_assembly_v8.py::test_v8_preview_against_the_downscaled_export[GX011625_0114.648-c3-cpu]` | 8.203 | 0.110 | -8.093 | pass -> skip |
| `test_methods_assembly_v8.py::test_v8_preview_against_the_downscaled_export[GX011625_0024.925-ancuti2018-cpu]` | 6.568 | 0.105 | -6.463 | pass -> skip |

Among shared nodes whose status stayed passed, the largest increases
are `test_prototype_clip.py::test_footage_smoke_gx011628`
(26.771 -> 32.257 s, +5.486 s),
`test_wp42_v3_product.py::test_v3_ratio_on_the_jittering_patch_clip_with_the_product_method[c3]`
(12.486 -> 16.994 s, +4.508 s), and
`test_gui_status.py::test_real_selection_through_the_shell_shows_gpu`
(0.218 -> 4.127 s, +3.909 s). Source: `joined.csv`.

### Largest new-node costs

Source: `C:/Users/rwsmy/clearwater-review-evidence/wp-t8/dr116/dr116/top40-new.csv`. BEFORE is absent for every
row below. The full new-node roster, with module/package prefix, is
`new.csv`. The six removed/renamed IDs in `removed.csv` are GUI routing,
settings and stub-era status tests; their total BEFORE cost is 0.055 s.
The join does not assert that a removed node lost coverage.

| New node | AFTER s |
|---|---:|
| `test_v51_shell_acceptance.py::test_v18_real_trim_preview_precedes_analysis_and_updates` | 73.722 |
| `test_v51_video_acceptance.py::test_v4_real_trim_records_best_effort_presence` | 66.399 |
| `test_wp44_mov_input.py::test_phone_mov_runner_and_v4` | 58.575 |
| `test_app_v7.py::test_v7_c_e_export_and_a_full_render_during_it` | 32.708 |
| `test_app_preview_fft.py::test_the_device_reading_returns_after_the_boundary` | 28.197 |
| `test_reviewpack.py::test_all_tiny_set` | 20.175 |
| `test_app_preview_fft.py::test_force_cpu_after_a_gpu_render_still_releases_the_gpu_plans` | 13.587 |
| `test_v51_video_acceptance.py::test_n10_video_gpu_render_digests_repeat_and_match_cpu` | 13.016 |
| `test_io_video_encode_bench.py::test_a_frames_release_is_not_timed_as_its_write` | 12.454 |
| `test_app_export_worker.py::test_q9_the_worker_and_the_in_process_engine_encode_the_same_frames` | 12.395 |

## DR-86 banked candidates, updated

Sources: copied BEFORE/AFTER JUnits, `C:/Users/rwsmy/clearwater-review-evidence/wp-t8/dr116/dr116/dr86-nodes.csv`
and `summary.json`. The historical approximately 121/163/81/394 s
labels are from `docs/reports/wp-t6-gate-sizing.md`, KEEP map and
"For CHARC", and `docs/debt-register.md` DR-86. They describe an older
setup+call map, not these exact JUnit totals.

| Group / exact node within `tests/` | BEFORE s | AFTER s |
|---|---:|---:|
| 5.3K CPU V4: `test_jobs_export_video.py::test_v4_synthetic_5k3_8_7_clip` | 130.323 | 128.704 |
| Row 9: `test_prototype_clip.py::test_bench_whole_clip_modes_record_their_pass` | 67.228 | 43.231 |
| Row 10: `test_prototype_backend.py::test_bench_gpu_records_graphics_memory` | 63.021 | 14.114 |
| Row 11: `test_prototype_clip.py::test_the_output_witness_passes_a_correct_export` | 39.464 | 34.106 |
| Prototype rows 9-11 total | 169.713 | 91.451 |
| Row 12: `test_wp42_v3_product.py::test_ad14_bound_with_the_product_method[c3]` | 27.599 | 29.361 |
| Row 13: `test_wp42_v3_product.py::test_ad14_bound_with_the_product_method[ancuti2018]` | 27.503 | 29.654 |
| Row 21: `test_wp42_v3_product.py::test_v3_ratio_on_the_jittering_patch_clip_with_the_product_method[ancuti2018]` | 12.868 | 13.208 |
| Row 22: `test_wp42_v3_product.py::test_v3_ratio_on_the_jittering_patch_clip_with_the_product_method[c3]` | 12.486 | 16.994 |
| V3 / AD-14 total | 80.456 | 89.217 |
| Historical remaining-test tail, fixed membership | 412.476 | 360.337 |

The tail is the original 1,097 passed node IDs, not a newly chosen
"everything else" bucket. In BEFORE, the script excludes the report's
seven CUT and 31 KEEP nodes, the added trim-parity node, and the skipped
photo node. It verifies the 38 mapped names against the historical map;
they are also the 38 largest BEFORE node costs. AFTER retains 1,091
tail IDs; the six removed IDs cost 0.055 s BEFORE and contribute zero
AFTER. Every tail member and its absent/present status is in
`dr86-nodes.csv`. New tests and the now-active old photo node are not
silently folded into that historical tail. Its decrease also contains
skip effects. These costs are not additive recoverable savings.

The large prototype memory-node decline is consistent with the existing
short stray-sampling fixture in `test_prototype_backend.py` (DR-87);
the archive comparison is not a fresh isolated measurement of that fix.
Both prototype test modules already shorten sampling in fixtures.
The prototype witness source, planted statistics and export are already
module fixtures in `test_prototype_clip.py`. The V3 clips and AD-14
mask are already module fixtures in `test_wp42_v3_product.py`.
Recommending those same fixture changes again would save no new work.

## Candidate reductions: declined; apply step closed

CHARC DECLINED C1 and C2 (generation 15, 2026-11-04 11:17Z), closing
item (d)'s apply step with no reduction applied. The V-suite acceptance
checks retain their independent runs. Source:
`C:/Users/rwsmy/clearwater-review-evidence/wp-t8/cell/dispatch-6.md`.
The source checks below establish
opportunities to reuse identical setup while keeping every assertion.
They do not establish measured savings: the archived JUnits provide
whole-node totals, not the subcall costs or a before/after run of a
proposed change. The measured costs and the limits are stated explicitly
instead of treating a whole node as seconds saved. No redundant
parameterization safe to drop was established.

| Candidate and file | Exact affected node IDs (within `tests/test_v51_video_acceptance.py`) | Measured AFTER cost / saving evidence | Coverage retained |
|---|---|---|---|
| C1: reuse one untagged CPU export through a module fixture | `test_v4_runner_preserves_fixture_fidelity[untagged]`; `test_v6_untagged_runner_warns_bt709_limited` | 6.313 s and 5.773 s, 12.086 s combined (`joined.csv`). Removes one duplicate `run_main` invocation. That invocation is inside the second node's 5.773 s total; its saved seconds are not separately measured. No measured saving is claimed. | Both currently use the identical source and `CPU` flags, with default correction. Keep the V4 comparison, frame count, CPU/libx265 checks, D54 warning checks and every mutation control. Consumers do not mutate the original result (V4 controls deep-copy). Give each consumer its own result copy, preserve source guards, and keep the export beneath the session basetemp. Selecting either node alone must still build the fixture. |
| C2: reuse the immutable source timestamp set through a module fixture | `test_n10_video_cpu_render_digests_repeat`; `test_n10_video_gpu_render_digests_repeat_and_match_cpu` | 9.570 s and 13.016 s, 22.586 s combined (`joined.csv`). Removes one duplicate `_source_ticks` probe/gather of the same unchanged committed source. Subcall cost is not present in JUnit, so saved seconds are unmeasured. | Keep all independent exports and render recordings, repeated-run comparisons, CPU/GPU bounds, post-decode characterization and mutation controls. Only the expected source ticks are shared; return an immutable value or a copy. Preserve the per-test source guard and the GPU readiness behavior. |

C1 and C2 are retained here as declined proposals, not planned edits.
CHARC judged their unmeasured benefit (at most about 35 s of the
2,049 s leg) less valuable than independent acceptance checks of record.
The whole-node sums above are affected-cost figures, not a savings
forecast; they must not be added to DR-86's banked group costs.
F8's additional candidate, sharing the CPU reference export in
`test_n10_video_gpu_render_digests_repeat_and_match_cpu` with the CPU
test's runs, is declined with the others.

The following remain banked recommendations, not no-risk reductions or
a commission for another suite-cost pass before the new trigger:

- Keep the 5.3K CPU export in its ruled form. Source:
  `test_jobs_export_video.py::test_v4_synthetic_5k3_8_7_clip` asserts
  the three-frame source before the CPU engine and V4 comparison.
  Changing size, frame count or backend changes the commissioned path;
  its 128.704 s AFTER cost is not a deletion budget.
- Profile remaining prototype bench overhead before changing sampling
  or telemetry. Rows 9-11 now cost 91.451 s in AFTER; the old sampling
  paydown is already present. The bench-mode test asserts timing,
  residuals, memory, comparison and witness behavior; stubbing those
  paths would weaken its coverage. The witness positive and planted
  cases are distinct, not redundant reruns.
- Keep both product methods and both V3/AD-14 clips. The four nodes
  cost 89.217 s AFTER, but use different methods or different clip
  properties. Lead length, smoothing and the fixed fixture are the
  subject. Dropping a parameter or shortening them changes coverage.
- The two GPU preview memory tests in `test_app_preview_fft.py` cost
  28.197 s and 13.587 s AFTER. Inspection shows different transitions:
  one checks a source boundary after a warmed GPU render; the other
  forces CPU after GPU before the boundary. Sharing their completed
  scenario or deleting one would remove a distinct transition. Pure
  immutable input construction could be profiled, but no saving from
  that part is established by the archive.

Sources for the recommendation costs are `dr86-nodes.csv` and
`top40-new.csv`; the assertion checks are in the named current test
bodies. No proposed change alters what a test asserts in this turn.

## Recommendation, verification and gate handoff

CHARC RULED that **DR-116 closes at acceptance on the attribution**:
the register's host-load-or-creep hypothesis is REFUTED. The roughly
660 s increase is new coverage: about 617 s in new nodes plus 43 s
net shared-node growth, dominated by the previously skipped photo leg
becoming active. The approximately 250 s real-photo leg is owner-footage
coverage live since the phone photos arrived on 2026-10-29 and stays.
The p55 figure of record is restated as **1,273 tests / 2,049 s**
(exact JUnit values above). Source: the binding ruling in
`C:/Users/rwsmy/clearwater-review-evidence/wp-t8/cell/dispatch-6.md`;
the archived JUnits establish the arithmetic.

DR-86's candidates stay banked, with the measured costs above and their
existing CPU/fixture/lead locks. No new suite-cost pass for Phase 6 is
commissioned unless the serial leg crosses about **40 minutes**. The
cell does not edit either register row. No reduction is applied.

A new serial leg was not run for DR-116. The already required final
gate retains the quiet-host serial leg, fresh basetemp and its normal
duration log. Its figures and pass/skip roster belong in the gate record;
that gate is verification, not a newly commissioned suite-cost pass.

| Final-candidate gate field | Result |
|---|---|
| Ruff / format / mypy | gate `t8a` on `ad385cbb` (13:11Z): ruff exit 0; format exit 0, 318 files already formatted; mypy exit 0, no issues in 159 source files |
| Collection identity: parallel + serial + fullclip = all | 6,806 + 1,273 + 7 = 8,086 = all; 0 duplicates; 0 differences |
| Parallel leg | exit 0, 591 s: 6,805 passed, 1 skipped (the by-design swscale yuvj case), 5 warnings (CuPy CUDA path, PIL truncated read; none from this package) |
| Serial leg (exclusive) | exit 0, 2,163 s: 1,273 passed, 0 skipped (the eleven V8 look-check nodes ran on the restored frames), 1 warning |
| Fullclip leg | exit 0, 1,601 s: 7 passed, 1 warning |
| Owned-path diff and zero-CR check on final candidate | `git diff --name-only main...wp-t8` = the 12 owned paths; 0 CR in every changed blob |
| Reviewer A | R1 `NO_NEW_CRITICAL_MAJOR`; terminating-round cleanup verified below |
| Reviewer B | `NO_NEW_CRITICAL_MAJOR`; this revision addresses its minor and granted advisories |

The earlier groups' static/development summaries are in the supplied
returns; they are not substituted for these final-candidate gates.
The dispatcher runs the legs sequentially under its scheduling lock.
No whole suite, gate leg, GPU exercise or footage read was performed
by the cell for the archive analysis.

Verification loop for this report:

| Suspected issue | Independent confirmation / disposition |
|---|---|
| Wrong WP-T6 baseline | Confirmed correct: copied suite time/count match the sizing report; hash matches its recorded prefix. No fix needed. |
| Growth might be mostly runner overhead or uniform host slowdown | Rejected as the explanation of this pair: wall residual changes by 0.063 s; join and ratios show additions and status changes dominate. Causal attribution of individual deltas remains unproved. |
| Pass/skip changes could look like speedups | Confirmed and separated: photo activation and ten old V8 skips are explicit, and ratios also exclude transitions. |
| Historical tail could absorb new tests | Confirmed risk, prevented by fixed baseline membership and exact mapped-name checks; full member CSV retained. |
| Duplicate keys, count drift or rounding could break reconciliation | Script asserts uniqueness/counts and uses decimal sums; independent XML/CSV reconciliation passes. The residual still includes cumulative XML rounding. |
| Proposed reuse could be claimed as measured saving | Rejected: only affected whole-node costs are available. Candidates stay unimplemented with unmeasured savings disclosed. |

The scratch script initially stopped on a guessed trim-parity name.
The exact archived name, `test_io_video_decode_hw.py::test_the_gx011627_trim_is_a_stream_copy_of_the_source`,
replaced the guess before generating the report. Its final run and the
independent reconciliation passed. No product/test fix resulted from
that scratch correction. Report scope/encoding checks pass; a full
report pass found no further unresolved arithmetic or source mismatch.
Durable evidence: the archived script and tables under
`C:/Users/rwsmy/clearwater-review-evidence/wp-t8/dr116/`, the cell's
verification results in `C:/Users/rwsmy/clearwater-review-evidence/wp-t8/cell/turn-5.txt`
and `cell/return-5.md`, and Reviewer A's independent re-derivation in
`C:/Users/rwsmy/clearwater-review-evidence/wp-t8/A/r1/review.txt`.

Limits: archived timings are one pair of serial executions, rounded per
node, with different code, inputs available and fixture/order state.
They are costs, not controlled benchmarks or additive saving forecasts.
`tools/fixtures/generate.py:12` and the manifest's `command` still document `--generated-out work/fixtures/generated`; this is documentation only and is not changed here (Reviewer B, B6).
The evidence copies and generated CSVs are retained in the durable paths above.
The sandbox audit residual has a seat ruling and no new DR. No reduction,
interface, dependency, manifest, harness file or other product behavior
was changed in the archive-analysis turn. This cleanup edits only the
report, fixture plugin and scoped tools/tests; the footage and main
working-folder contents remain unread by the cell.

F7 coverage limit (Reviewer A advisory): eleven V8 look-check nodes have
skipped at every gate since the CP2 packs were archived on 2026-10-29
to `D:/clearwater-archive/`; the frames formerly under the main checkout's
`work/wp1.3/frames` are absent. This is a coverage loss outside WP-T8,
routed by the orchestrator to CHARC. Source:
`C:/Users/rwsmy/clearwater-review-evidence/wp-t8/A/r1/review.txt` and
the binding TURN-6 dispatch. CHARC ruled at 11:34Z that the two frames be restored from the archive; they have been restored, so the gate of record runs these eleven nodes again (TURN-7 dispatch). The gate of record (`t8a`) ran them: the serial leg skipped none. This cell did not inspect those folders.

## Reviewer A round 1 disposition and cumulative ledger

Source: `C:/Users/rwsmy/clearwater-review-evidence/wp-t8/A/r1/review.txt`,
on `92bea573..6d0a249a`. Verdict `NO_NEW_CRITICAL_MAJOR`; the seat's
five-module run passed, static checks were clean, and all DR-116 figures
were independently re-derived. This is the terminating round's cleanup;
Reviewer B has since returned; its follow-up is below, and the dispatcher owns the final gates.

| Finding | Classification | Disposition |
|---|---|---|
| F1 | MINOR, in envelope, NEW | Confirmed by removing only the nondirectory clause in memory; both new planted-file writer cases fail on the missing refusal message and pass on real code. Product source unchanged. |
| F2 | MINOR, in envelope, NEW | Accepted: DR-120 row now states generation/verification time, bytes per root, worker multiplicity and the xdist exception. |
| F3 | MINOR, in envelope, NEW | Confirmed by injected missing-Git, non-checkout and timeout failures. At A cleanup, caught the ruled exception families and kept the then-ruled checkout cache fallback; all three cases passed. B1 below supersedes that fallback with contained basetemp and a warning. |
| F4 | MINOR, in envelope, NEW | Accepted: sources of record now name the durable archives, analysis, seat logs and ruling, rather than scratch paths. |
| F5 | MINOR, in envelope, NEW | Accepted: module and top-delta tables now show BEFORE -> AFTER pass/skip status. |
| F6 | MINOR, in envelope, NEW | Resolved by CHARC's ruling: apply step CLOSED, no reduction applied, DR-116 closes at accept on attribution. |
| F7 | ADVISORY, in envelope, NEW | Disclosed as an out-of-package coverage loss routed to CHARC; no inline fix. |
| F8 | ADVISORY, in envelope, NEW | Additional CPU-reference reuse noted and declined with C1/C2. |
| F9 | ADVISORY, in envelope, NEW | No change: reviewer measured refusal overhead as negligible. |
| F10 | ADVISORY, out of envelope, NEW | No change: alternative Git layouts remain outside the declared checkout envelope. |
| F11 | ADVISORY, out of envelope, NEW | No change: broader POSIX symlink coverage is outside this Windows-junction package. |

| Round | Critical / major / minor / advisory | In / out | NEW / REOPENED | Reverts | Product fixes / test and infrastructure fixes | Dispatcher-read depth at entry |
|---|---|---|---|---|---|---|
| A r1 cleanup | 0 / 0 / 6 / 5 | 9 / 2 | 11 / 0 | 0 | 0 / 2 (file regression; Git fallback and regression); remaining fixes are report-only | 160,961 of 475,000 |

The cleanup's execution evidence is delivered in this cell's TURN-6
return and transcript, recorded by the dispatcher under
`C:/Users/rwsmy/clearwater-review-evidence/wp-t8/cell/return-6.md` and
`cell/turn-6.txt`. The source mutation was in memory only; a copy of the
mutated method and its launcher remain scratch evidence for transfer.

| Cleanup check | Observed result |
|---|---|
| F1 RED, only nondirectory clause removed in memory | Both planted-file writer cases fail: the `FileExistsError` message does not match `refusing cache entry path` |
| F3 RED on the unchanged plugin at `6d0a249a` | All three injected errors escape: `FileNotFoundError`, `CalledProcessError`, `TimeoutExpired` |
| F1 + F3 GREEN on real code | 5 passed in 0.15 s |
| Requested `test_cache_store.py` + `test_fixtures.py` module run | 393 passed, 3 expected sandbox audit failures in 70.17 s; no other failure or skip |
| Ruff / format on the three touched Python files | All checks passed; 3 files already formatted |
| Scope, bytes and report consistency | Four owned files only; both test diffs additions-only; zero CR in all four files; 37 timing rows and 27 pass/skip status entries match the CSVs; diff whitespace check passes |

The module run used the parallel-leg marker expression, explicit
worktree basetemp `ct8-17`, `PYTHONPATH=scripts`, the sandbox mkdir shim,
and `-p no:cacheprovider`. Its only failures were
`test_generators_write_only_inside_their_output_folders`,
`test_generators_read_only_their_own_code_and_libraries`, and
`test_ffmpeg_is_told_to_write_only_into_the_output_folders` in
`test_fixtures.py`: the ruled `nul` access and 55/56 launch residual.
The seed tests gain lines only; no product source is changed in cleanup.

## Reviewer B follow-up

Source: Findings section of
`C:/Users/rwsmy/clearwater-review-evidence/wp-t8/B/review.txt`, on
`a844a37f`; binding rulings are in the TURN-7 dispatch. Verdict:
`NO_NEW_CRITICAL_MAJOR`. This section records the small follow-up;
the final gate figures are in the gate table above.

| Finding | Classification | Disposition |
|---|---|---|
| B1 | MINOR, in envelope, NEW | Git failure now falls back under basetemp and warns once with path, error class and one-line reason; updated all three F3 cases. |
| B2 | MINOR, out of envelope, NEW | Report's eleven V8 nodes retained; the register correction belongs to CHARC/orchestrator. No register edit. |
| B3 | ADVISORY, in envelope, NEW | DR-120 row states basetemp deletion, regeneration per run, first-consumer charging and serial-comparison limit. |
| B4 | ADVISORY, in envelope, NEW | ROW prints and flushes before JSON writing; one regression catches a blocked replacement after a completed run. `PermissionError` still propagates with its readable reason and record path. |
| B5 | ADVISORY, in envelope, NEW | Noted limit: concurrent developer runs without basetemp/xdist share the main-checkout cache; a manifest-changing branch can regenerate it while another run uses it. Gate legs are contained and unaffected. |
| B6 | ADVISORY, in envelope, NEW | Disclosed the unchanged manual-generation command documentation under limits. |
| B7 | ADVISORY, in envelope, NEW | Status and Changes name `0e784986` and the Reviewer B follow-up. |
| B8 | ADVISORY, originally out of envelope, NEW; correction explicitly granted | Git subprocess decoding is UTF-8. |
| B9 | ADVISORY, in envelope, NEW | Missing N6 prefix yields an assertion naming the expected prefix, using `next(..., None)`. |

| Round | Critical / major / minor / advisory | In / out as reviewed | NEW / REOPENED | Reverts | Product fixes / tools and test fixes | Dispatcher-read depth at entry |
|---|---|---|---|---|---|---|
| B follow-up | 0 / 0 / 2 / 7 | 7 / 2 (B8 correction granted) | 9 / 0 | 0 | 0 / 3 (fixture fallback/decoding; ROW publication order; N6 diagnostic), plus report changes | 207,206 of 475,000 |

Before these changes, the updated Git-failure cases failed for missing
warnings and the new blocked-write case failed because no ROW was printed.
The focused GREEN run passed all changed behaviors and the N6 assertion.
Execution evidence is transferred by the dispatcher to
`C:/Users/rwsmy/clearwater-review-evidence/wp-t8/cell/return-7.md` and
`cell/turn-7.txt`; scratch logs are not sources of record.

TURN-7 checks: focused GREEN is 5 passed in 0.76 s. The requested
`test_fixtures.py`, `test_export_bench.py` and `test_core_speed.py` run
is 391 passed, 1 deselected and only the 3 ruled sandbox audit failures
in 129.12 s. Those failures are
`test_generators_write_only_inside_their_output_folders`,
`test_generators_read_only_their_own_code_and_libraries`, and
`test_ffmpeg_is_told_to_write_only_into_the_output_folders`. No other
test failed. The run used the parallel-leg markers, explicit `ct8-20`
basetemp, the sandbox mkdir shim and no cacheprovider. Ruff passes;
format reports 5 files already formatted. Scope/encoding checks pass:
six owned files, zero CR, fixture-test changes confined to the turn-6
F3 addition, export-bench regression additions only, and clean diff
whitespace. The three-leg gate figures are in the gate table above.
