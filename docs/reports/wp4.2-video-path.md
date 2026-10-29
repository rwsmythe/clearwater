# WP4.2 -- Video path end to end (report, DRAFT; Reviewer A converged at round 1)

Cell 2 (implementer-opus-high), worktree `.worktrees/wp4.2`, branch `wp4.2` on main `f991254`
(WP4.2a merged). Brief `docs/briefs/wp4.2-brief.md` (FINAL; Rulings `2c4476d9869df056`, Revision
1 rulings `c8340144a8e87c09`); round-0 rulings in `docs/proofs/wp4.2-ledger.md` (orchestrator
seat and CHARC `881cc956f1335e7e`).

## What WP4.2 adds

- **DR-67, the per-job device hook** (`src/clearwater/jobs/export.py`). `ExportEngine` gains two
  keyword-only, defaulted parameters, `source_for` and `sink_for`
  (`Callable[[ArrayBackend | None], VideoSource | VideoSink]`). In `_video`, right after the
  job's one `select_backend` call, `_job_device(backend)` gives the backend itself for a GPU job
  (identity, never a second selection) and None for a CPU job; each factory is called once with
  it. The per-job source decodes the analysis (`AnalysisEngine(source=..., backend=<the job's>)`)
  and the render; the base `video_source` only probes, so a probe failure or refusal builds
  nothing per job. `hw_decode = backend.device != "cpu"` is unchanged. Absent the parameters the
  engine is today's (`export_bench`, `export_oracle`, the WP3.14 / WP3.21 tests and
  `product_engine` are unchanged; the private methods keep their positional order, the new
  `source` argument last).
- **The composition root's video legs** (`src/clearwater/app/composition.py`). `export_jobs()`
  returns the `ExportEngine` itself: `FFmpegVideoSource` / `FFmpegVideoSink` built per video job
  by the new builders `video_source(device_backend)` and `video_sink(device_backend)`, and
  `DiskProxyCache(cache_folder, cache_limit_bytes)` with its registered `DEFAULT_CODEC`, keyed by
  that cache's own `key_for` (DR-41), through `proxy_cache(folder, limit_bytes)`; selection is
  `core.select_backend`. New keyword-only parameters `cache_folder`, `cache_limit_bytes`,
  `source_for`, `sink_for`. Without `cache_folder` the engine has a private refusing cache, so a
  video job fails readably ("video export needs a cache folder; none was given") after its probe
  and before any write; photos are unaffected (R0-Q1 (a)). `_PhotoExports`, `_no_video_probe`,
  `_no_cache_key` and the stub collaborators are gone. The root never resolves `app_locations()`.
  `clearwater.app` re-exports the three builders and lists them in `__all__` beside WP4.1's five
  (R0-Q4 (b); CHARC `91c2c22f4b6edd18` 2, with the granted additive edit of
  `tests/test_app_composition.py::test_the_package_exports_the_root`).
- **DR-45 (b) analysis half and DR-47 (a)** (`src/clearwater/analysis/engine.py`, grant G1).
  `AnalysisEngine(expected_frames=None)`: a decode pass that ends with fewer frames raises
  "the frame source ended after N of the clip's M frames; the cache entry is left incomplete"
  before `mark_complete`. The export job fills it (`_expected_frames`): the probe's `nb_frames`
  for a clip with no D86 fault; for `truncated`, the readable count from one packet listing
  (`read_packet_table` + `readable_video_pts`, the set the sink's check uses); None for
  `unreadable_tail` and an unknown count. `clearwater.analysis` still imports no `clearwater.io`.
  Each job callable from `analysis_job` / `set_parameters` runs once; a retained one called again
  returns "this analysis job has already run" and touches nothing.
- **DR-71** (`jobs/export.py`): `_Analysis.cache_growth_bytes` takes the larger of the marginal
  rate and the entry's own bytes per stored frame; the F5 fallback (lead stored nothing) is the
  own rate as before.
- **The runner's video legs** (`tools/headless_export.py`). One new option `--cache-dir DIR`,
  required when any item is a video (exit 2, nothing run) and refused when it does not exist
  (R0-Q3 (a)); checked by `write_target_refusal` with the other own paths and joined to the
  redactor's known folders. `run()` gains `cache_folder`: checked by `write_target_refusal`
  beside `check_outputs`, shown by name only, and passed to `composition.export_jobs()` with the
  first request's `cache_limit_bytes`; a video request with no engine given and no cache folder
  is a `RunnerRefusalError`. Video requests go through WP4.2a's `check_outputs` unchanged (output
  folder and planned output FILE path); no second footage check exists.
- **The record's `"video"` object** (CHARC `881cc956f1335e7e` A, additive under `"schema": 1`,
  each item's last field): null for a photo or refused item and when the caller gave the engine;
  otherwise `{"device_backend": "cuda:0" | null, "frame_device": "cuda:0" | "cpu" | null,
  "encoder": <name> | null, "decode_passes": <int>}`, collected runner-side by wrapping the
  root's own builders (`_VideoObserver`, `_ObservedSource`, `_ObservedSink`). `decode_passes`
  counts the job's source `frames()` calls: 2 when analysed, 1 when a complete entry skipped the
  decode pass (V17). The shape and domains are in the runner's module docstring.
- **DR-73**: (a) the `block_sums` docstring now says 40 bits for 10-bit input; (b) the test
  renamed to `test_a_video_job_releases_twice_at_the_analysis_end_and_at_the_job_end`.
- **DR-74**: `tests/test_wp321_fft_release.py::test_the_analysis_end_release_frees_the_pool_while_frames_render`
  (`gpu`, `slow`): a 1920x1080, 90-frame clip (longer than c3's 61-frame lead); at the
  analysis-end release the sink is open, not closed, fewer than 90 frames are written, and the
  pool's free bytes drop (a planted 64 MiB cached block included).

## Evidence (light runs in this seat; the two-leg gate is a granted window)

| Item | Test | Figure |
|---|---|---|
| DR-67 | `test_wp42_device_backend.py` (recording doubles; three plants fail by name: GPU job given None, CPU job given a device backend, a second selection) | gpu leg through the root: sink frames `{"cuda:0"}`, `JobResult.device` GPU |
| Composition | `test_wp42_composition.py` (classes, codec, `key_for`, keyword-only, no `app_locations`, static "only the root" with a planted control) | -- |
| V4 (suite) | `test_wp42_video_path.py` `vid-hevc8-bt709-full` CPU and GPU (device frames) through `video_fidelity.fidelity_record` | every MANDATORY and REQUIRED item SAME, roster SAME, 45 frames |
| D86 | `vid-truncated` through the root | ok, "cut short" warning; expected count 24 (listing) |
| Refusals | `vid-hlg`, `vid-pq`, `gopro-lower-gl010001-lrv` | readable failures, nothing written, no cache folder |
| V9 | c3 and ancuti2018 at `Parameter.neutral`, sink frames vs decoded source | max 0.0000/255, mean 0.00000/255 (bound 2/255, 0.2/255); colour tags SAME; plant (c3 defaults) exceeds 2/255 |
| V17 | a reopen over the same cache folder | decodes 2 then 1; 45 pre-encode frames bit-identical; another-version entry removed at open, next export decodes 2 |
| Own clip | two files in one batch, both orders | each output's pre-encode frames bit-identical to its solo export; two entries |
| DR-45 (b) | strict prefix (30 of 45) through the root | RED on the base: the job failed only at the sink's frame-count check (export half; round 0 reproduced the complete entry on the engine); now "ended after 30 of the clip's 45 frames", entry incomplete, nothing written |
| Cancel / failure | lead and mid-encode cancels; a planted analysis read error | `CANCELLED`, nothing in the output folder, no job thread or FFmpeg child left; the failure keeps its own text |
| Runner | `test_wp42_runner_video.py` (12 tests) | CPU run through `main`; refusals; exit 0/1/2; two outputs and two entries; record names only; forced-CPU run loads no PySide6 or CuPy |

Bit-identity assertions compare dtype, shape and bytes (`same_bits`, with a signed-zero control).

## V3 ratios (information for CP5)

Measured pre-encode on the frames the sink receives from the composed GPU job (device frames),
against the per-frame leg (each frame's `provisional_record`, the same decode, method and
backend). Clips encoded in-test as lossless 8-bit 4:2:0 HEVC MP4 with BT.709 tags; R0-Q5's
condition is the first test (Main profile, no fault, every frame decoded).

| Clip | Method | AD-14 /255 unsmoothed / smoothed (bound 0.5) | V3 ratio L* / a* / b* / contrast | Encoded output (characterisation) |
|---|---|---|---|---|
| ad14-flicker | c3 | 0.0416 / **0.0102** | 0.053 / 0.200 / 0.401 / 0.072 (recorded) | 0.0348; 0.084 / 1.134 / 0.329 / 0.170 |
| ad14-flicker | ancuti2018 | 0.0388 / **0.0067** | 0.061 / 0.257 / 0.497 / 0.071 (recorded) | 0.0288; 0.124 / 0.256 / 0.097 / 0.152 |
| jittering patch | c3 | 0.1006 / 0.0017 | **0.018 / 0.014 / 0.026 / 0.016** (<= 0.25 asserted) | 0.0378; 0.089 / 0.134 / 0.167 / 0.136 |
| jittering patch | ancuti2018 | 0.1055 / 0.0017 | **0.012 / 0.016 / 0.024 / 0.012** (<= 0.25 asserted) | 0.0332; 0.082 / 0.110 / 0.034 / 0.137 |
| ad14-flicker (WP3.11) | GrayWorld | -- | 0.475 / 0.447 / 0.488 / 0.476 | -- |
| ad14-flicker (WP3.11) | GainsStretch | -- | 0.387 / 0.482 / 0.455 / 0.400 | -- |

Each acceptance reads the unrounded figure and has a planted control through the same
measurement (Reviewer A round 1): a 1/255 flicker on every other smoothed frame gives AD-14
1.0/255 on all four rows (refused against 0.5); the smoothed and per-frame frames interleaved
give V3 ratios 0.63-5.05 per measure (refused against 0.25).

V3 runs on the GPU job in the suite (device frames; CHARC `91c2c22f4b6edd18` 3, KEEP for
question 9's budget); the suite does not cover the CPU leg. After Reviewer A converged, `428d8b4`
added two environment variables to `tests/test_wp42_v3_product.py` (CHARC `2a336830303f3a2d`;
covered by the orchestrator's Reviewer B, not by Reviewer A): `CLEARWATER_WP42_V3_BACKEND=cpu`
runs every leg on the CPU job (the export `force_cpu`, the per-frame leg on the CPU backend), and
`CLEARWATER_WP42_V3_FIGURES` names a new figures file the run writes, its first line naming the
backend. The suite never sets either; unset, the file is the GPU job as before.

**The CPU leg: the same V3/AD-14 figures, not the same encoded characterisation** (CHARC ruling
(a) on the V3 STOP). One recorded window, 2026-10-29 06:15:01Z-06:24:29Z, ran the file twice
through its own measurement, unchanged, by the scratch driver `work\wp4.2\v3\driver.py` (md5
`b128c6096945b5bc48b935c92361b7e8`, not committed), GPU (91.0 s) then CPU (470.3 s), 6 passed
each. The cited figures files are the window's, under `work\wp4.2\v3\window\`:
`figures-gpu.txt` (md5 `3ec7f59c682e8b8319d409a2f4bd5ed5`) and `figures-cpu.txt` (md5
`1eba25f524befde9627fc063f9191efa`); each row names its backend, so the two file hashes differ by
construction. The 24 rows V3 and AD-14 assert or record (`ad14_unsmoothed`, `ad14_smoothed` and
the four V3 ratios on the four rows of the table above, the backend column removed; the selection
is recorded in `compare.txt`) have the same md5 from both files,
`b72d9e7b57b53b0e28593c1f55c91abd`. All four planted AD-14 rows and 15 of the 16 planted ratios
are equal too. 13 of the 64 rows differ (`compare.txt`, GPU | CPU), verbatim:

```
ad14-flicker | c3 | encoded_ratios.L* | gpu 0.084 | cpu 0.085
ad14-flicker | c3 | encoded_ratios.a* | gpu 1.134 | cpu 1.024
ad14-flicker | c3 | encoded_ratios.b* | gpu 0.329 | cpu 0.292
ad14-flicker | c3 | encoded_ratios.contrast | gpu 0.17 | cpu 0.143
ad14-flicker | c3 | planted_ratios.a* | gpu 2.717 | cpu 2.716
ad14-flicker | ancuti2018 | encoded_ratios.L* | gpu 0.124 | cpu 0.125
ad14-flicker | ancuti2018 | encoded_ratios.a* | gpu 0.256 | cpu 0.265
ad14-flicker | ancuti2018 | encoded_ratios.b* | gpu 0.097 | cpu 0.088
ad14-flicker | ancuti2018 | encoded_ratios.contrast | gpu 0.152 | cpu 0.155
jitter | c3 | ad14_encoded | gpu 0.0378 | cpu 0.0376
jitter | c3 | encoded_ratios.a* | gpu 0.134 | cpu 0.145
jitter | c3 | encoded_ratios.b* | gpu 0.167 | cpu 0.193
jitter | c3 | encoded_ratios.contrast | gpu 0.136 | cpu 0.14
```

The encoded rows are characterisation only (not V3's measurement point, question 5); they are
backend-dependent at the second or third decimal with the SAME encoder: `"auto"` resolves to
`hevc_nvenc` on both jobs (`resolve_encoder`, `src/clearwater/io/video/capability.py:228`; the
compute backend does not choose the encoder). The cell's READING, not established: the CPU and
GPU pre-encode floats differ below the figures' rounding, and 8-bit quantisation and NVENC in a
near-static masked region turn that into a different encoded flicker; its one direct evidence is
the planted row's 0.001 (2.717 against 2.716). The pre-encode frames were not compared directly.
V4's CPU/GPU SAME is AD-11's tolerance test and is unaffected by these rows (CHARC's ruling).
Run to run the GPU is identical: the window's raw GPU file and the earlier light run's
`work\wp4.2\v3\figures-gpu.txt` have the same md5 (`629f7dc9c85c45418f70f01a9c5c6363`); that
earlier file is cited only as this determinism check. Cell 2's unlabelled observation
`work\wp4.2-v3-figures.txt` (md5 `f76c42a5fae87b9cb691ac5594b5d3a2`, 2026-10-29T05:22:48Z; four
rows equal to the above, no backend named) is that cell's observation only, not the CPU record.

WP1.4 real footage: 0.35-0.45. No product-method miss: no STOP. The encoded ratios include the
encoder's frame-to-frame quantisation (NVENC, Standard); they are not V3's measurement point
(question 5).

## V4 on GX011627 and the WP2.3 set (task 10)

The window was the orchestrator's exclusive grant, 2026-10-29T08:42:01Z-08:48:18Z, at head
`ab9ea83`. Free memory was 9.39 GiB at the start and at least 9.37 GiB before each export, and
the GPU was idle beforehand. Each export ran through `tools/headless_export.py` on the product
composition, with settings at their defaults: c3, encoder `auto`, `standard`, 8-bit from
8-bit. Each output was then compared to its source by `tools/video_fidelity.py compare`, at the
source's bit depth. GX011627 was found through `find_footage_file` and was not skipped (DR-27).
The WP2.3 set is the six committed fixtures, each leg run as one batch. `vid-hlg` and `vid-pq`
are refused by design and were not run; the suite's refusal test covers them (Evidence above).
Commands, logs and record md5s are in `docs/proofs/wp4.2-ledger.md` (cell 4).

| Item | Leg | Frames (src / out) | MANDATORY / REQUIRED / BEST-EFFORT different | V4 |
|---|---|---|---|---|
| GX011627 | GPU | 681 / 681 | 0 / 0 / 8 | SAME |
| `vid-hevc8-bt709-full` | GPU, CPU | 45 / 45 | 0 / 0 / 6 | SAME, SAME |
| `vid-hevc10` (10-bit) | GPU, CPU | 45 / 45 | 0 / 0 / 6 | SAME, SAME |
| `vid-rotated` | GPU, CPU | 45 / 45 | 0 / 0 / 5 | SAME, SAME |
| `vid-untagged` | GPU, CPU | 45 / 45 | 0 / 0 / 6 | SAME, SAME |
| `vid-vfr` | GPU, CPU | 30 / 30 | 0 / 0 / 6 | SAME, SAME |
| `vid-truncated` (D86) | GPU, CPU | 24 / 24 | 0 / 0 / 8 | SAME, SAME |

Each of the 13 compares checked 46 items, and every MANDATORY and REQUIRED item was SAME.
GX011627's eight BEST-EFFORT differences are the same eight items as in WP3.21's record of the
engine-level run. `vid-truncated` was compared on its readable part, ending at 0.800800 s, as
D86 says; the runner reported its "cut short" warning. `vid-untagged` got the assumed-tags
warning. GX011627's warnings name the camera firmware tag and the camera settings atoms as not
carried to the output.

The record's facts, the same on every item of a leg:

| Run | `JobResult.device` | `device_backend` | Sink frame device | Encoder | Decode passes | Elapsed (information only, not a V16 row) |
|---|---|---|---|---|---|---|
| GX011627 | `GPU` | `cuda:0` | `cuda:0` | `hevc_nvenc` | 2 | 218.9 s |
| WP2.3, GPU | `GPU` | `cuda:0` | `cuda:0` | `hevc_nvenc` | 2 | 3.0-7.1 s per clip |
| WP2.3, `--force-cpu` | `CPU: forced` | null | `cpu` | `hevc_nvenc` | 2 | 3.9-6.3 s per clip |

Every output, cache, record and compare record is kept under `work\wp4.2\v4\` and
`work\wp3.10\wp4.2-v4\`. Nothing derived from footage is committed.

## Limits

- **The footage check** (WP4.1's Limit as WP4.2a revised it, the target list extended): one
  predicate, `write_target_refusal`, decides the folder and runner-owned file write targets
  before anything runs when a footage folder is configured: each output folder as `jobs.naming`
  plans it (`--out`, or the source's own folder beside a source), photo and video alike, the
  record file, the `--settings-dir` folder and its `settings.json`, and the `--cache-dir` folder
  (in `main` and, for a library caller, `run`'s `cache_folder`). Each planned output FILE path,
  photo and video alike, passes predicate (i) through `_write_form_refusal` and keeps its checked
  folder as its parent. The predicate's (i)-(iii), the hard-link residual and "a link created
  after the check is not seen" stand as WP4.2a's report states them.
- **The cache interior (R1-Q4, reproduced at round 0).** The predicate checks the `--cache-dir`
  path itself, not a link planted inside an existing cache folder. `DiskProxyCache` skips a
  junction or symbolic link entry at discovery (`cache/store.py:573`) and then writes through
  it: `_entry_for_write` creates and opens `data.pack` under `folder / entry_name(key)`
  (`cache/store.py:660-666`); `cache/keys.py` `is_link` is never called. No `cache/` edit here;
  CHARC's register row at the accept (trigger "the next `cache/` touch").
- **DR-45 (b) residual (CHARC `91c2c22f4b6edd18` 1).** An `unreadable_tail` source gets no
  expected count and no packet listing (`_expected_frames`): its decodable end is known only by
  decoding (D86; `readable_video_pts` cuts the list only for `truncated`). So a short decode of
  an `unreadable_tail` clip is marked complete at the decoder's end, as D86 intends, and later
  exports reuse that entry (V17). The export half is still guarded by the sink's
  `missing_frames` rule, which for this case requires every readable frame up to the last one
  written, none skipped (`verify.missing_frames`): a gap inside the written range is refused,
  an early end is accepted as the decoder's end. `truncated` keeps the one-listing count and a
  clean probe the probe's count. Test:
  `tests/test_wp42_video_path.py::test_an_unreadable_tail_job_makes_no_listing_and_no_refusal`
  (a planted `unreadable_tail` probe and a 30-of-45 decoder: no listing, the job ok, the entry
  complete).
- V12 is deferred to v2 (spec 0.5.3). V16 and every speed figure are out of scope (WP5.2).
- Out of envelope as declared in the brief (concurrent runners on one cache folder, network
  shares, a CPU backend with a hardware decoder, other operating systems).

## Deviations and items for the dispatcher

- **The record's `"video"` when the engine is given** (`run(exports=...)`, `main(exports=...)`):
  null, as the facts are observed only through the root's builders.
- **DR-74's test is `gpu` and `slow`.** The V3 product tests are `gpu` and `slow` (the GPU job
  with device frames; about 170 s for the file in this seat; CHARC `91c2c22f4b6edd18` 3 KEEP).
  New serial-leg cost measured here: about 210 s (V3 file 169 s, DR-74 18 s, the two gpu V4 / DR-67 legs about 23 s), inside
  question 9's 300 s.

## Register dispositions

DR-67 CLOSES; DR-71 CLOSES; DR-73 (a) and (b) CLOSE; DR-74 CLOSES; DR-45 (b) CLOSES on both
halves (the residual above); DR-47 (a) CLOSES (G1 exercised), (b) and (c) stay stated limits,
the row open for them with trigger the next `analysis/engine.py` touch; DR-41 consumer note held
(test); DR-78 / DR-79 WP4.2a's (closed); NEW for CHARC: the R1-Q4 cache-interior row.
