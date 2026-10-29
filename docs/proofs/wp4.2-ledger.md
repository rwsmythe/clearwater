# WP4.2 ledger -- Video path end to end

Cell 1 (implementer-opus-high), worktree `.worktrees/wp4.2`, branch `wp4.2`, base main `aa4761b`
(brief FINAL, CHARC `c8340144a8e87c09`). Round 0 only in this seat (ledger-only commit); the
build waits for WP4.2a's merge and the orchestrator's rebase (R1-Q5 condition 3, CAP +3 h).

## Depth (filled by the dispatcher from `scripts/cell_depth.py`)

| Gate | Cell | Depth (tokens) | Read at | Note |
|---|---|---|---|---|
| Y1 (round 0) | cell 1 | 209,438 (70 turns) | 2026-10-29 02:33:37Z | at Y1; cell 1 STOOD DOWN 02:35Z, build to a fresh cell |
| Y4 (Reviewer A R1) | cell 3 | 165,011 (turn 50) | 2026-10-29 05:55Z | R1 adjudicated; cleanup granted |
| Y2 (window request) | cell 3 | 202,221 (turn 75) | 2026-10-29 06:09Z | cleanup concurred |
| Y2 (window request 2) | cell 3 | 223,004 (turn 89) | 2026-10-29 06:14Z | CPU V3 record granted |
| Y3 (V3 STOP) | cell 3 | 237,804 (turn 101) | 2026-10-29 06:26Z | near the 250K evaluation point |
| ruling (a) applied | cell 3 | 256,795 (turn 114) | 2026-10-29 06:30Z | past 250K; bounded remaining load (suite, task-10 RESUME HERE) |
| rebase + suite grant | cell 3 | 259,350 (turn 116) | 2026-10-29 07:28Z | rebased head `6e0eb1d` |
| final | cell 3 | 278,978 (turn 142) | 2026-10-29 | re-seated for task 10 |
| dispatch | cell 4 | 0 | 2026-10-29 | task 10 (the GX011627 V4 window) |
| window request / release | cell 4 | not given at the grant (figure owed at the release yield) | 2026-10-29 | |
| WINDOW RELEASED | cell 4 | 105,663 (turn 47) | 2026-10-29 | release accepted; Reviewer B ordered |
| Y4 (Reviewer A R2) | cell 4 | 184,286 (turn 100) | 2026-10-29 | R2 TERMINATED; cleanup ruled FIX x3 |
| Reviewer B re-run minors | cell 4 | 213,446 (turn 118) | 2026-10-29 | docs-only turn before the gate |
| FINAL docs turn | cell 4 | 227,702 (turn 129) | 2026-10-29 | report FINAL; package done |

## Round ledger (Reviewer A, Codex `gpt-6.1-sol` / high, WSL)

| Round | Critical | Major | Minor | In / out of envelope | New / reopened | Reverts | Fixes: product / test-only | Transport, CLI | Depth |
|---|---|---|---|---|---|---|---|---|---|
| 1 (`1fa33a8`) | 0 | 0 | 4 | 4 in / 0 out | 4 new / 0 reopened | 0 | 1 tool code (F1) / 3 test-only (F2-F4) | WSL, codex-cli 0.162.1, `gpt-6.1-sol` / high | 165,011 (turn 50, 05:55Z) |
| 2 (`5e74d01`, the Reviewer B remediation, diff `265251f..`) | 0 | 0 | 3 | 3 in / 0 out | 3 new / 0 reopened | 0 | 0 product / 3 test-only (R2-1..3) | WSL, `gpt-6.1-sol` / high | 184,286 (turn 100) |

## Round 0 -- read and map (task 1), evidence

Light, in-process runs only (no window, no footage, no GPU). Scripts kept at the cell's session
scratchpad `wp42r0\` (`repro_dr45b.py`, `repro_r1q4.py`, `count_check.py`).

- **DR-45 (b) analysis half: REPRODUCED.** `AnalysisEngine` over `ListSource` and
  `CountingCache` (`tests/test_analysis_support.py`), probe `nb_frames=30`, source yields 20
  and ends cleanly: `ok=True failure=None`, entry `complete=True`, 20 frames held. Decided by
  `src/clearwater/analysis/engine.py:749-762` (`_decode`: only "no frames" and the stale-tail
  check precede `self._cache.mark_complete(self._key)` at :762; no count comparison). The real
  decoder does not catch it either: `io/video/decode.py:658-664` (`FrameStream._end`) returns on
  exit status 0 with no count check. So the analysis-half grant is ASKED (G1).
- **Frame-count premise on the WP2.3 set** (`count_check.py`, CPU decode): `hevc8-bt709-full`,
  `hevc10`, `rotated` 45/45, `untagged` 45/45 (fault `missing_tags`, not D86), `vfr` 30/30, all
  with a one-segment edit list; `truncated` 24 of `nb_frames` 45 (fault `truncated`). A clean
  probe decodes exactly `nb_frames`; a D86 probe does not.
- **Layering fact for Q7.** `tests/test_analysis_deps.py:8-11` FORBIDS `clearwater.io` (and
  `clearwater.cache`) in `clearwater.analysis`, so the analysis engine cannot compute the
  readable count of a `truncated` source (`io/video/verify.py:681-702` `readable_video_pts` on
  `read_packet_table`); the probe carries that count only inside the fault's message text
  (`io/video/probe.py:503`). See question R0-Q2.
- **R1-Q4: NOT REFUSED (reproduced).** A junction planted inside an existing cache folder under
  the entry name of a key (`cache/keys.py:72` `entry_name`): a new `DiskProxyCache` over the
  folder skips it at discovery (`cache/store.py:573`, `is_symlink() or is_junction()` ->
  `continue`, so it is neither registered nor removed), then `store_proxy` writes THROUGH it:
  `_entry_for_write` `cache/store.py:660-661` (`folder = self._folder / entry_name(key)`;
  `folder.mkdir(parents=True, exist_ok=True)` succeeds on the link) and `:664-666` opens
  `data.pack` there; the run left `data.pack` and `meta.json` in the junction's target. Note:
  `cache/keys.py:103-105` defines `is_link` ("never followed by the cache") and nothing in
  `cache/` calls it. Consequence for WP4.2: the report's cache-interior Limit (task 8) and
  CHARC's row at the accept (trigger "the next `cache/` touch"); no `cache/` edit here.
- **WP4.1 names checked on the base** (`aa4761b`): `composition.py:79-188` (`_PhotoExports`,
  `_no_video_probe`, `_no_cache_key`, `export_jobs` with the stubs at :176-187);
  `tools/headless_export.py` `run` :687, `check_outputs` :654, `write_target_refusal` :611,
  `Redactor` :223, `main` :995, `_main` :1025, `_check_own_paths` :970; `export_jobs(` is called
  in `src`/`tools` only by `headless_export.run` (:722); `gui/engines.py` does not call it.
- **Engine shape** (`jobs/export.py`): `ExportEngine.__init__` :516-556; `_video` :801-905
  (probe :808 on `self._video_source`; `select_backend` :817; `self._sink_factory()` :821;
  `hw_decode = backend.device != "cpu"` :851); `_analyse` :907-938 builds
  `AnalysisEngine(source=self._video_source, backend=backend, hw_decode=...)` :925-934;
  `_write_frames` :995-1048 decodes from `self._video_source` :1019. `FFmpegVideoSource`
  (`io/video/decode.py:688-698`, `frames` :755-758) and `FFmpegVideoSink`
  (`io/video/encode.py:507-519`, `_payload` :930-944) take `device_backend`; the sink refuses a
  device frame unless its backend satisfies `DeviceFrameBackend` with the same device.
- **ad14-flicker is FFV1 in Matroska** (manifest), and the probe refuses a non-MP4/MOV
  container (`io/video/probe.py:565-568`), so V3 through the composed engine needs the clip
  re-encoded into an MP4 in-test (question R0-Q5).
- **Register re-grep** at `aa4761b` (register `c358816`, unchanged since `eb0074f`): rows naming
  WP4.2 / WP4.x are DR-45, -46, -47, -56, -67, -71, -73, -74, -78, -79, all in the brief's table.

## Round 0 -- the design table (task 2)

| # | Item | Design (as proposed; "Q" = needs a ruling) |
|---|---|---|
| 1 | Per-job device hook (Q1, DR-67) | `ExportEngine.__init__` gains two keyword-only, defaulted parameters: `source_for: Callable[[ArrayBackend \| None], VideoSource] \| None = None` and `sink_for: Callable[[ArrayBackend \| None], VideoSink] \| None = None`. In `_video`, right after the ONE `self._select_backend(...)` (:817): `device = backend if backend.device != "cpu" else None`; `source = self._video_source if self._source_for is None else self._source_for(device)`; `sink = self._sink_factory() if self._sink_for is None else self._sink_for(device)` (replacing :821, same position). The per-job `source` is threaded into `_analyse` (`AnalysisEngine(source=source, backend=backend, hw_decode=...)`, unchanged backend argument) and `_encode` -> `_write_frames` (`source.frames(...)` replacing :1019). The probe stays on `self._video_source` (:808), so a probe failure, a refused probe or any failure before selection builds nothing per job. `hw_decode = backend.device != "cpu"` unchanged. Absent both parameters the engine is today's: every existing caller (`export_bench`, `export_oracle`, WP3.14/WP3.21 tests, `product_engine`) unchanged. Both factories are called exactly once per video job, never for a photo. |
| 2 | Root video builders (task 4) | `composition.py` adds public builders `video_source(device_backend: ArrayBackend \| None = None) -> VideoSource` (`FFmpegVideoSource(device_backend=...)`) and `video_sink(device_backend=None) -> VideoSink` (`FFmpegVideoSink(device_backend=...)`), and `proxy_cache(folder: Path, limit_bytes: int) -> DiskProxyCache` (default registered codec, DR-41). `export_jobs()` gains keyword-only `cache_folder: Path \| None = None`, `cache_limit_bytes: int = DEFAULT_CACHE_LIMIT_BYTES`, `source_for=None`, `sink_for=None` (test and instrument overrides, defaulting to `video_source` / `video_sink`); builds ONE `ExportEngine(video_source=video_source(), sink_factory=video_sink, source_for=..., sink_for=..., cache=proxy_cache(cache_folder, cache_limit_bytes), cache_key=<that cache>.key_for, select_backend=backend_selector(), ...)` and returns it (annotation narrowed to `ExportEngine`). Deleted: `_PhotoExports`, `_no_video_probe`, `_no_cache_key`, the `interfaces.stubs` and `unavailable_exports` imports. Photo builders unchanged; still never resolves `app_locations()`. Without `cache_folder`: see R0-Q1. `app/__init__.py` is NOT owned and is not edited (R0-Q4). |
| 3 | Runner video legs (task 5, Q12) | ONE new option `--cache-dir DIR`: REQUIRED when any item routes to `"video"` (exit 2, nothing run); must exist (R0-Q3); checked by `write_target_refusal` in `_check_own_paths` as `("--cache-dir", args.cache_dir)` (text "the --cache-dir path <reason>."), added to `known` (redacted by name). `run()` gains keyword-only `cache_folder: Path \| None = None`: checked with `write_target_refusal` beside `check_outputs` before anything runs, added to the run's folders, passed to `composition.export_jobs(cache_folder=..., cache_limit_bytes=<first request's settings>)` when `exports` is None; a video request with `exports=None` and no `cache_folder` is a `RunnerRefusalError`. Video output folders and output FILE paths go through WP4.2a's `check_outputs` unchanged (no second check). Module docstring: the WP4.1 "video fails UNAVAILABLE_TEXT" sentence replaced; the usage line gains `[--cache-dir DIR]`. |
| 4 | Record fields (Q12; persistent-data shape, TRIPWIRE) | Additive under `"schema": 1`, per item: `"video"`: null for photo and refused items, else `{"device_backend": "cuda:0" \| null, "frame_device": "cuda:0" \| "cpu" \| null, "encoder": "<name>" \| null, "decode_passes": int}`. Gathered runner-side only: `run()` passes the root `source_for` / `sink_for` wrappers that delegate to `composition.video_source` / `video_sink` and observe (the backend handed in, the first written frame's device, `open`'s encoder, the per-job source's `frames()` calls); `_WithRefusals.job` brackets each job so the facts attach to the running item (`run_batch` runs `exports.job(r)(p)` one at a time, `jobs/batch.py:125-132`). `decode_passes` 1 = the cache entry was complete at start (V17), 2 = analysed. `device` (JobResult.device) unchanged. No engine or interface change. |
| 5 | GUI video legs (Q3, RULED) | No `gui/` edit; `default_engines()` keeps its stub video legs and `StubProxyCache` until WP4.3. The three `test_gui_export_panel.py` seam tests are untouched. |
| 6 | Router pins (Q2, R1-Q3, RULED) | (a) `tests/test_app_composition.py::test_a_video_request_fails_unavailable_and_writes_nothing` (:118-128): build with `export_jobs(cache_folder=tmp_path / "cache")`; assert `ok False`, the failure starts `"GX010001.MP4: "` and is the probe's readable refusal of the unreadable file (not `UNAVAILABLE_TEXT`), `outputs ()`, `out` empty, no cache entry folder. Module docstring line 5 and the `UNAVAILABLE_TEXT` import (:26) updated/removed. (b) `tests/test_headless_export.py::test_a_video_fails_unavailable_in_wp41` (:480-492): `he.run(requests, footage_folder=None, cache_folder=tmp_path / "cache")`; assert `("failed", <the probe's readable failure for GX010001.MP4>, ("video",))` and `out` empty; its name is kept unless R0-Q6 rules a rename. (c) `::test_the_record_has_schema_1_and_file_names_only` (:240-271): add `--cache-dir <tmp_path / "cache">` (created); line 268 becomes the real job's readable failure for the missing `GX010001.MP4` (the probe's "does not exist" text, name only); everything else unchanged, the names-only loop over `tmp_path` covers the cache folder. Docstring lines 8-9 and the `UNAVAILABLE_TEXT` import (:30) updated (`CANCELLED` kept). |
| 7 | V3 point (Q5, RULED) | Pre-encode at the sink seam: a recording sink (through `sink_for`) that keeps a host copy of every frame `write` receives and delegates to a real `FFmpegVideoSink`, so the encoded output's figures are recorded beside. The unsmoothed baseline: R0-Q5. |
| 8 | DR-45 (b) analysis half (Q7) | Reproduced (above). Grant G1 asked: `analysis/engine.py` `_decode`, after the stale check and before `mark_complete` (:752-762): with no `truncated` / `unreadable_tail` fault and `nb_frames` known, `len(decoded) < nb_frames` raises `ValueError("the frame source ended after N of the clip's M frames; the cache entry is left incomplete")` (a failed result, the entry not marked); the D86 form per R0-Q2. Test through the composition: a `source_for` wrapper over the real source that yields a strict prefix and ends cleanly; RED on the base = complete entry; GREEN = the analysis's failure, entry incomplete, nothing written. |
| 9 | DR-47 (Q6 amended) | Same touch (G1): `analysis_job` returns a one-shot callable (a second call of the same callable returns a failed result `"this analysis job has already run"` without touching the store or cache); test: a retained callable run twice. DR-47 (a) CLOSES; (b), (c) stay the stated limits (row stays OPEN for them, trigger the next `analysis/engine.py` touch). |
| 10 | DR-71 (task 8) | `cache_growth_bytes`: when both are defined, `max(marginal, own)`; the marginal-only and own-only paths as now; F5 fallback test unchanged. Test: a partially extended retry (before: h frames of size S; the lead adds k << h frames with growth below S/h per frame) gives the own rate. Parallel leg. |
| 11 | DR-74 + DR-73 (b) (Q8) | `tests/test_wp321_fft_release.py`: rename `test_a_video_job_releases_at_the_analysis_end_and_after_every_frame` -> `test_a_video_job_releases_twice_at_the_analysis_end_and_at_the_job_end` (assertion unchanged); new `gpu`, `slow` case: a 1920x1080 clip of 75 frames (> c3's 61-frame lead) generated under `tmp_path`, exported on the GPU job with device frames; the sink records the pool's `used/total` at every `write`; assert a drop between two writes after the lead (the analysis-end release while frames render). |
| 12 | DR-73 (a) | `core/backend.py:684` docstring only: "38 bits at k = 8 for 8-bit input, 40 for 10-bit". |
| 13 | Footage-check Limit (task 8) | Restated in the report from WP4.2a's revised Limit with the targets extended by the video output folders and file paths and `--cache-dir`; plus the R1-Q4 cache-interior Limit (found). |

### Test list (markers, expected seconds; serial-leg budget about 300 s, Q9)

| File :: test (proposed) | Markers | Leg | Expected s |
|---|---|---|---|
| `test_wp42_device_backend.py` :: GPU job hands the selected backend (identity) to `source_for`, `sink_for` and `AnalysisEngine`; CPU job hands None; each factory once per video job, never for a photo; one `select_backend` call per job (recording doubles, `StubVideoSource` frames) | -- | parallel | 3 |
| same :: planted wrong wirings fail by name (GPU job given None; CPU job given the GPU backend; a second selection that differs) | -- | parallel | 2 |
| same :: real GPU leg, `vid-hevc8-bt709-full` through `export_jobs()`: the sink receives `cuda:0` frames, `JobResult.device` GPU | `gpu` | serial | 6 |
| `test_wp42_composition.py` :: collaborator classes (`FFmpegVideoSource`, `FFmpegVideoSink`, `DiskProxyCache` with `DEFAULT_CODEC`, `cache_key` is the cache's `key_for`, `core.select_backend`), no stub on a video leg, keyword-only additive signature, no `app_locations` call, static "only the root constructs `FFmpegVideoSource` / `FFmpegVideoSink` / `DiskProxyCache` in `src/clearwater`" with a planted control | -- | parallel | 3 |
| `test_wp42_video_path.py` :: V4 `vid-hevc8-bt709-full` CPU, compared by `tools/video_fidelity.py`'s comparison, every MANDATORY and REQUIRED item SAME | -- | parallel | 4 |
| same :: V4 same sample, GPU job with device frames | `gpu` | serial | 6 |
| same :: `vid-truncated` warns (D86); `vid-hlg`, `vid-pq`, a sidecar fail readably, nothing written | -- | parallel | 4 |
| same :: V9 neutral c3 and ancuti2018 (max <= 2/255, mean <= 0.2/255 vs the decoded source; colour tags SAME) | -- | parallel | 10 |
| same :: V17 reopen skips the decode (`decode` passes 1 vs 2, bit-pattern identical pre-encode frames); a renamed-version entry removed at open, next export re-analyses | -- | parallel | 8 |
| same :: own clip: two files in one batch, either order, each bit-identical to its solo export | -- | parallel | 12 |
| same :: DR-45 (b) strict prefix through the composition (RED on base) | -- | parallel | 4 |
| same :: DR-47 (a) one-shot job callable | -- | parallel | 1 |
| same :: cancel in the lead, cancel mid-encode (`CANCELLED`, no temporary, no final, threads joined); an analysis-half failure keeps its own text | -- | parallel | 8 |
| `test_wp42_v3_product.py` :: AD-14 bound asserted, four ratios recorded, `ad14-flicker` re-encoded in-test, c3 and ancuti2018 (CPU) | `slow` if over 20 s each (measured at build) | serial or parallel | 2 x 30 |
| same :: V3 25 % asserted on the jittering-patch clip, encoded in-test, c3 and ancuti2018 (CPU) | as above | serial or parallel | 2 x 25 |
| `test_wp42_runner_video.py` :: CPU run on `vid-hevc8-bt709-full` through `main`; the `--out` / `--beside-source` / `--cache-dir` refusals inside a stand-in footage folder and through a link; a `:`-stem video source refused by `check_outputs`; `--cache-dir` missing -> exit 2 nothing run; exit statuses; two files -> two outputs and two cache entries; record names only and the `video` object | -- | parallel | 15 |
| same :: subprocess `--force-cpu` video run loads no PySide6 or CuPy | -- | parallel | 10 |
| `test_wp321_fft_release.py` :: DR-74 case (1080p, 75 frames, GPU) | `gpu`, `slow` | serial | 25 |
| `test_wp42_device_backend.py` or `test_wp42_video_path.py` :: DR-71 partially extended retry | -- | parallel | 1 |

Serial-leg total: 37 s without V3 in the serial leg; up to about 147 s if all four V3 cases go
`slow`. Both inside the 300 s budget. GX011627 is never a suite test (Q4, T5-Q7).

### Register dispositions (confirmed against the code, with corrections)

DR-67 CLOSES (item 1 test). DR-71 CLOSES (item 10). DR-73 (a) and (b) CLOSE (items 12, 11).
DR-74 CLOSES (item 11). DR-45 (b) CLOSES on both halves IF G1 is granted (export half:
`FFmpegVideoSink.close` -> `verify.missing_frames`, `encode.py:1018-1024`; analysis half: item
8), with the D86 residual of R0-Q2 stated. DR-47: (a) CLOSES with G1 (item 9); (b) and (c)
remain stated limits, the row OPEN for them. DR-45 (a), DR-46, DR-56, DR-62, DR-68..70, DR-72,
DR-75..77 NOT REACHED as the brief says. DR-41 CONSUMER NOTE (default codec, `key_for` of the
same instance). DR-78, DR-79 WP4.2a's. NEW (for CHARC at the accept): the R1-Q4 cache-interior
row (reproduced, `cache/store.py:660-661`; `cache/keys.py` `is_link` unused).

### Grants asked

- **G1** `src/clearwater/analysis/engine.py`: the frame-count check before `mark_complete`
  (item 8) and DR-47 (a)'s one-shot guard (item 9), on the reproduction above.
- Nothing else beyond the brief's standing grants. No new module, no dependency. Tripwire: the
  record's per-item `"video"` object (item 4) is a persistent-data shape.

### Questions (recommended answer first)

- **R0-Q1. `export_jobs()` without `cache_folder`, given a video request.** (a) The root gives
  the engine a private refusing `ProxyCache` and `cache_key` (`_NoCacheFolder`, raising a
  readable "video export needs a cache folder; none was given"), so the video job fails at its
  analysis start with nothing written (after the probe and the space check; photo callers
  unaffected). (b) Make the engine fail before the probe (a new `ExportEngine` keyword, e.g.
  `video_enabled`; more engine surface). (c) `cache_folder` required (breaks every photo caller
  of `export_jobs()`; not additive).
- **R0-Q2. The D86 form of the frame-count check.** `clearwater.analysis` may not import
  `clearwater.io` (`test_analysis_deps.py`), so it cannot compute a `truncated` source's
  readable count. (a) Check `len(decoded) < nb_frames` only for a probe with no `truncated` /
  `unreadable_tail` fault and a known `nb_frames`; for a D86 source the decoder's clean end is
  the readable end (WP3.9's contract); state the residual (a prefix of a TRUNCATED source can
  still leave a complete entry; the export half's sink still refuses the short set, so no bad
  output) as a report Limit. (b) A new keyword `AnalysisEngine(expected_frames=None)` that the
  export job fills from `verify.readable_video_pts(probe, read_packet_table(path))` for
  `truncated` (one more packet listing per job; `unreadable_tail` still unknowable without a
  decode), closing the truncated case too.
- **R0-Q3. `--cache-dir` that does not exist.** (a) exit 2 "the --cache-dir folder does not
  exist." (as `--out`; `DiskProxyCache` would otherwise `mkdir(parents=True)` a typo's whole
  chain). (b) Created on first store.
- **R0-Q4. Re-export the new builders from `clearwater.app`.** (a) No: `app/__init__.py` is not
  owned; callers use `composition.video_source` etc. (b) Grant the one-line re-export.
- **R0-Q5. V3's unsmoothed baseline and the clip encoding.** (a) The smoothed leg is the frames
  the sink receives from the composed export; the per-frame (unsmoothed) leg renders the same
  decoded frames with the same method on the same backend using each frame's own statistics
  (`AnalysisEngine.provisional_record` from a second analysis over the same source and probe,
  as WP3.11's tests do); `ad14-flicker` (FFV1/MKV, refused by the probe) and the jittering-patch
  clip are encoded in-test under `tmp_path` as LOSSLESS 8-bit HEVC 4:2:0 MP4 (`libx265
  lossless=1`, BT.709 tags), so encoder noise adds no flicker to the static mask region. (b)
  Lossy HEVC MP4 (the encoder's frame-to-frame noise in the mask then counts against AD-14's
  0.5/255). (c) Both legs through the export (needs an unsmoothed export mode: an engine
  change, not proposed).
- **R0-Q6. The two pure router-pin tests keep their names** (`..._fails_unavailable_...`,
  `..._in_wp41`) while their assertions become the real job's readable failure. (a) Rename them
  in place to say what they now assert (e.g. `test_a_video_request_runs_the_real_video_job`,
  `test_a_video_runs_through_run`) -- a rename was not explicitly ruled, hence the ask. (b) Keep
  the names (they then overstate, as DR-73 (b) did).

### Could not verify in this seat

- GX011627's decoded count against its `nb_frames` (footage, window only); WP3.14's GX011627
  V4 SAME through the engine implies the clean count holds there.
- The V3 and DR-74 timings (estimates; measured at build, then the markers fixed).
- Whether `libx265` lossless 4:2:0 output decodes inside WP3.9's envelope through the product
  probe (expected: Main profile, 8-bit 4:2:0, MP4); first build step of R0-Q5.
- WP4.2a's final `check_outputs` / helper / `Redactor` code (in flight); item 3 assumes its
  brief's shape (`check_outputs(requests, footage_folder)` unchanged signature, file paths
  inside it).

## Round-0 rulings (recorded by the orchestrator, generation 18, 2026-10-29)

**Orchestrator seat rulings** (packet to CHARC `1286b25667b9ec63`, 02:34Z; CHARC CONCURRED, no overrule):
- **G1 GRANTED** (`analysis/engine.py`: the frame-count check before `mark_complete` plus DR-47 (a)'s one-shot guard,
  one touch), on the round-0 reproduction, under CHARC's Q2/Q7 ruling. DR-47 (a) CLOSES at the accept.
- **R0-Q1 = (a)**: `export_jobs()` with no `cache_folder` gives a video request a private refusing `ProxyCache` /
  `cache_key` in the root; the video job fails readably ("needs a cache folder"), nothing written; photo callers unchanged.
- **R0-Q3 = (a)**: a `--cache-dir` that does not exist is exit 2, as `--out`.
- **R0-Q4 = (b)**: GRANTED a one-line edit of `src/clearwater/app/__init__.py` re-exporting the three new builders.
- **R0-Q5 = (a)**: unsmoothed leg = each frame's own statistics (`provisional_record`); the clips re-encoded in-test as
  LOSSLESS libx265 8-bit 4:2:0 MP4 with BT.709 tags; CONDITION: first prove the lossless clip decodes through
  `FFmpegVideoSource` inside WP3.9's envelope; if not, STOP with a recommendation, no silent lossy fallback.
- **R0-Q6 = (a)**: the two pure router-pin tests are renamed in place.

**CHARC RULING `881cc956f1335e7e` (2026-10-29 02:35:56Z), verbatim:**

RULING on WP4.2 round 0 (query 1286b25667b9ec63; ledger `wp4.2` 283f022). PRIMARY: CHARC. Verified here: `verify.read_packet_table` (:482) and `readable_video_pts` (:681) exist; probe fault names `truncated` / `unreadable_tail` (probe.py:501/510); the bench's `device_backend` vocabulary (export_bench.py:395-428); `cache/store.py:573` skips a junction entry at discovery, consistent with the write-through you reproduced.

**A. TRIPWIRE (item 4) = APPROVED.** The per-item `"video"` object `{device_backend, frame_device, encoder, decode_passes}`, null for photo and refused items, additive under `"schema": 1`, collected runner-side through wrappers on `source_for` / `sink_for`; no product module, interface or cache format touched. Conditions: (1) the record's existing fields and their order are unchanged and the WP4.1 schema test keeps passing without edit beyond the three router pins already granted; (2) the four field names and value domains are written in the runner's module docstring (the record's one documented shape) and in the report; (3) `decode_passes` is counted from the source wrapper's open calls, not inferred, and the V17 leg asserts it (reopen = fewer passes).

**B. R0-Q2 = (b'), as you recommend.** `AnalysisEngine(expected_frames=None)`; the export job fills it with the probe's `nb_frames` when the probe reports no `truncated` / `unreadable_tail` fault (no extra cost), and with the readable count from ONE packet listing (`read_packet_table` + `readable_video_pts`) only when it does. `clearwater.analysis` stays free of `clearwater.io` (the job, not the engine, lists packets; `test_analysis_deps.py` unchanged). The check runs before `mark_complete`; a short count fails the job readably with nothing marked complete; a test plants each of the three cases (normal, truncated-with-listing, short-without-fault = DR-45 (b)'s reproduction). Q7's wording stands in full; (a) is not taken.

**Ruled at your seat: all CONCURRED, no overrule.** G1 granted on the reproduction (count check + DR-47 (a) one-shot guard, one touch; DR-47 (a) CLOSES at the accept since the engine.py grant is exercised); R0-Q1 (a); R0-Q3 (a); R0-Q4 (b) the one-line `app/__init__.py` re-export (keep the package's one surface); R0-Q5 (a) with your lossless-decode proof condition and the STOP, no silent lossy fallback; R0-Q6 (a).

**R1-Q4 reproduced:** noted with file:line (`store.py:573`, `:660-666`; `keys.py:103` `is_link` uncalled). The WP4.2 report carries the Limit; my register row (next `cache/` touch) lands at WP4.2's accept as ruled, with your evidence lines.

CAP at 05:33:37Z noted; WP4.2a in Codex turn 2 (round 0 at 933e33e). Build grant after WP4.2a's merge and the rebase, or at the cap, as the brief says. Nothing further from me.

## Build record (cell 2, on main `f991254`, WP4.2a merged)

Commits, in order: `0b9a1a1` DR-67 hook + `test_wp42_device_backend.py`; `cfc94cf` DR-73 (a);
`35e1c63` root + `test_wp42_composition.py` + router pin (a) renamed; `c5dc02d` runner +
pins (b) (c) + `test_wp42_runner_video.py`; `e2a324a` G1 (DR-45 (b) count check, DR-47 (a)
one-shot) + export `_expected_frames`; `2953d94` DR-71; `5b96e9c` DR-74 + DR-73 (b) rename;
`e37a3c2` V4 / V9 / V17 / own clip / cancel; `00397cb` V3; then the report and this ledger.

RED first: DR-67 (TypeError, no keyword), G1 (prefix: the job failed only at the sink's count
check; `expected_frames` unknown; the one-shot callable ran twice), DR-71 (89,600 against the
own rate's 864,985). The runner tests were written after the option (RED = argparse's unknown
`--cache-dir` on the base). An existing plant
(`test_jobs_export.py::test_planted_close_on_cancel_fails_by_name`, `args[6]` = the sink) caught
a first draft that inserted `source` mid-signature; the new argument is now LAST in `_analyse`,
`_encode` and `_write_frames` (no existing test changed).

Readings recorded (not new choices; flagged at the yield):
- CHARC B (R0-Q2 (b')) for `unreadable_tail`: no expected count (None), as R0-Q2 (b)'s own text
  said ("`unreadable_tail` still unknowable without a decode"); `readable_video_pts` lists every
  pts for it, so the listing there would fail every such clip. Residual in the report.
- R0-Q4 (b): `__all__` is pinned by WP4.1's `test_the_package_exports_the_root` (not owned), so
  the three builders are re-exported by redundant alias, not added to `__all__`.
- V3 runs on the GPU job (device frames), the per-frame leg on the same decode and backend; the
  round-0 test list said CPU, which took 650 s for the file (the same pre-encode figures); on the
  GPU 169 s. Marked `gpu`, `slow`.

Light gates at `00397cb` + report: `ruff check .` clean, `ruff format --check .` 265 files,
`mypy` 141 files clean; targeted parallel set (the four WP4.2 files, the two WP4.1 files,
WP4.2a's file, the four deps tests, `test_gui_export_panel.py`, `test_wp321_fft_release.py`) 266
passed; analysis / export / GUI-analysis set 558 passed; the jobs layering test and
`test_jobs_naming.py` 116 passed. Light `gpu` runs of my own (no window): the DR-67 gpu leg, the
V4 gpu leg, DR-74 (18 s), the V3 file (169 s, 5 passed).

New serial-leg cost (measured here, not in a window): V3 file 169 s, DR-74 18 s, DR-67 gpu 10 s,
V4 gpu 13 s: about 210 s against question 9's 300 s.

## Build rulings (CHARC 91c2c22f4b6edd18)

Ruling on cell 2's three readings (05:33Z), recorded verbatim by cell 3:

> 1. **`unreadable_tail` -> `expected_frames = None` with the residual as a Limit: APPROVED.** Verified at `verify.py:681-700`: `readable_video_pts` cuts the list only for `truncated`; for `unreadable_tail` the decodable end cannot be told without decoding (D86; `missing_frames` applies "up to the last frame written, none skipped" for that case). (b') narrows accordingly: `truncated` keeps the one-listing count; `unreadable_tail` = None. Conditions: the Limit names the residual (a short decode of an unreadable_tail clip is marked complete at the decoder's end, as D86 intends) and states that the export half is still guarded by the sink's `missing_frames` rule; one test plants an `unreadable_tail` probe and asserts no listing and no refusal.
>
> 2. **R0-Q4: the three builders go INTO `__all__`; one-line grant on `tests/test_app_composition.py::test_the_package_exports_the_root` to add the three names.** Not KEEP: an alias outside `__all__` is a half surface, and R0-Q4 (b) was ruled on "one surface". The test edit is additive (the five WP4.1 names stay), recorded in the ledger with the node id.
>
> 3. **V3 on the GPU job: KEEP.** 169 s vs 650 s for identical pre-encode figures keeps question 9's budget; the report states that V3 ran on the GPU job and that the CPU run (650 s) gave the same figures once, by hash, so the CPU leg is covered by that record and not by the suite.

Applied by cell 3 (before Reviewer A round 1):

1. `_expected_frames`' docstring (`src/clearwater/jobs/export.py`) states the None case's residual
   and the sink's guard; the report's "DR-45 (b) residual" Limit is REPLACED: cell 2's text said
   the sink "still refuses a short frame set", which is false for `unreadable_tail`
   (`verify.missing_frames` requires only the readable pts up to the last one written, so an early
   end passes); the new text says what the rule holds. Cell 2's
   `test_an_unreadable_tail_source_is_not_given_a_count` asserts only `_expected_frames(...) is
   None` (no listing assertion, no job), so a NEW test was added:
   `tests/test_wp42_video_path.py::test_an_unreadable_tail_job_makes_no_listing_and_no_refusal`
   (a planted `unreadable_tail` probe on `FFmpegVideoSource.probe`, `export_module.read_packet_table`
   replaced by a recorder that raises, a 30-of-45 `PrefixSource`: no listing, the job ok with the
   sink's tail warning, the entry complete). It pins existing behaviour; planted controls below.
2. `src/clearwater/app/__init__.py`: the three builders imported with the five and listed in
   `__all__` (the redundant-alias form dropped). Granted additive edit, node id
   `tests/test_app_composition.py::test_the_package_exports_the_root`: `"proxy_cache"`,
   `"video_sink"`, `"video_source"` appended to the asserted list; the five WP4.1 names and the
   identity loop unchanged.
3. The report's V3 section states V3 ran on the GPU job and that the CPU leg is not covered by the
   suite. **No hash of the 650 s CPU run exists** (FLAGGED at the yield): what exists is cell 2's
   build-record sentence ("the round-0 test list said CPU, which took 650 s for the file (the same
   pre-encode figures)") and one unlabelled figures file `work\wp4.2-v3-figures.txt` (md5
   `f76c42a5fae87b9cb691ac5594b5d3a2`, mtime 2026-10-29T05:22:48Z, four rows equal to the report's
   table, no backend named). The report says exactly that; no hash was invented.

## Reviewer A round 1 (cell 3) -- TERMINATING

Head `1fa33a8` (base `f991254`), Codex `gpt-6.1-sol` / high over WSL; probe READY (one
`succeeded in`). Evidence `C:\Users\rwsmy\clearwater-review-evidence\wp4.2\r1\` (prompt, diff,
transcript, test summary, `adjudication.md`, `md5sums.txt`; `review.txt` md5
`afff4213e7ac9e268c5daae216a445a1`). Assertions: banner model and effort PASS; 25 `succeeded in`;
`tokens used` 175,076; `VERDICT: NO_NEW_CRITICAL_MAJOR`. ERROR lines: a model-list refresh
timeout and an `rmcp` MCP connector closing (neither is the model transport; the session
completed), the rest echoed source. The reviewer could not run repository tests (WSL Python has no
NumPy); its probes were dependency-free.

| # | Severity | Tag | Finding | Adjudication | Fix (commit) |
|---|---|---|---|---|---|
| F1 | MINOR | EXECUTED | `tools/headless_export.py:248` `_ObservedSink.open` notes the encoder before the wrapped open: a refused open leaves `"encoder"` non-null against the docstring's "null when it was not opened" | CONFIRMED | encoder noted after a successful open; `tests/test_wp42_runner_video.py::test_the_encoder_is_recorded_only_once_the_sink_has_opened` (RED on `1fa33a8`: `'libx265' is None` failed) (`2a7a414`) |
| F2 | MINOR | EXECUTED | `tests/test_wp42_v3_product.py:279/306` AD-14 rounded to 4 places before `< 0.5` (0.49999 rejected; only ever stricter) | CONFIRMED | `_ad14_holds` / `_v3_holds` read unrounded figures (`raw_ad14_smoothed`); `::test_the_acceptance_reads_the_unrounded_figures` (`47a4cbf`) |
| F3 | MINOR | REASONED | `:325` the V3 "planted failure" `not all(u <= 0.25*u)` is a tautology; AD-14 has no plant | CONFIRMED | `_planted`: AD-14 plant = 1/255 on every other smoothed frame (figure 1.0 on all four rows, refused); V3 plant = smoothed and per-frame frames interleaved (ratios 0.63-5.05, refused); both through `_figures` and the acceptance (`47a4cbf`) |
| F4 | MINOR | EXECUTED | `tests/test_wp42_composition.py:48-67` the static check misses `from ... import FFmpegVideoSource as Source; Source()` | CONFIRMED | ImportFrom aliases resolved; `::test_the_video_static_check_reports_an_aliased_construction` (RED on `1fa33a8`: `[] == [...]` failed) (`2865b6a`) |

Zero new blocking: the loop TERMINATES at round 1 (fill CONVERGENCE_CRITERION); F1-F4 fixed once
in the terminating cleanup (orchestrator grant at Y4), no further counted round. Ruling
`91c2c22f` FLAG 1 (the Limit rewritten to what `missing_frames` holds) CONCURRED by the
orchestrator; FLAG 2 (no hash of the 650 s CPU V3 run) is with CHARC, the report text held as
written.

Cleanup gates at `2865b6a`: `ruff check .` clean; `ruff format --check .` 265 files; `mypy` 141
files clean; 0 CR in every changed blob. Light targeted parallel-expression set (the WP4.2 files,
app composition and deps, `test_headless_export.py`, WP4.2a's file, the four deps tests,
`test_wp321_fft_release.py`) 232 passed in 118.92 s. Light `gpu`/`slow` run of my own V3 file
(no window, not a timed figure): 6 passed in 102.51 s; the product figures equal the report's
table on all four rows.

## Y4 ruling (CHARC 2a336830303f3a2d, 05:56Z), verbatim as relayed by the orchestrator

> **FLAG 2 = (a).** My item 3 asserted a hash that was never recorded; the report must not cite one. ONE recorded CPU run of the V3 file in an exclusive window (~11 min, OPEN/RELEASE to me; before or beside WP4.2's two-leg window, your timing), the backend named in the run's own figures file, the md5 of the CPU and the GPU figures files both recorded, and the report citing the equality by those two hashes (or stating the difference if any). If they differ, STOP to me before the two-leg window. The unlabelled `work\wp4.2-v3-figures.txt` (f76c42a5...) stays as cell 2's observation, labelled as such, not as the CPU record.
>
> **FLAG 1 CONCURRED:** the rewritten Limit is the true statement (a gap inside the written range is refused, an early end is accepted as D86's decoder end). Record the correction of cell 2's sentence in the ledger.
>
> Items 1 and 2 as applied: accepted (the `test_the_package_exports_the_root` edit recorded; alias form dropped). R1 0/0/4 terminating with the cleanup granted: concurred (F1 tool fix + test; F2-F4 test-only).

**FLAG 1, the correction recorded:** cell 2's report sentence "the export half's sink check still
refuses a short frame set, so no bad output is written" was false for `unreadable_tail`
(`verify.missing_frames` requires only the readable pts up to the last one written); it was
REPLACED at `1fa33a8` by the Limit now in the report (a gap inside the written range is refused;
an early end is accepted as D86's decoder end).

**FLAG 2, applied by cell 3:** `tests/test_wp42_v3_product.py` gains `CLEARWATER_WP42_V3_BACKEND`
(`cpu` = every leg on the CPU job: the export `force_cpu`, the per-frame leg on the CPU backend
with `hw_decode` off, as the job decides it; unset = the GPU job, the suite's form, unchanged) and
`CLEARWATER_WP42_V3_FIGURES` (a NEW figures file: `backend: <device>` then each test's figures
line; an existing file is refused, never overwritten; checked: a second run naming
`figures-gpu.txt` failed at the fixture and left its md5 unchanged).
- GPU record (light `gpu` run of my own, no window, not timed): `work\wp4.2\v3\figures-gpu.txt`,
  6 passed in 88.47 s; `backend: cuda:0`; file md5 `629f7dc9c85c45418f70f01a9c5c6363`; the
  figure lines after the backend line md5 `5fb51f054dda4e6612e89578fb8de45b`; the four rows equal
  the report's table. Because each file names its backend, the two FILE hashes differ by
  construction; the equality is cited by the hashes of the figure lines (both recorded).
- CPU record: PENDING, the window's item (i).
- The report labels `work\wp4.2-v3-figures.txt` as cell 2's observation only.

## The V3 CPU/GPU window, the STOP and CHARC's ruling (a)

**Window (orchestrator grant, item 3; 2026-10-29 06:15:01Z-06:24:29Z, 9.6 GiB free before).**
The scratch driver `work\wp4.2\v3\driver.py` (md5 `b128c6096945b5bc48b935c92361b7e8`, never
committed) ran `tests/test_wp42_v3_product.py` at `e3b5d5f` twice through its own `_v3` /
`_figures`, unchanged, the only difference the committed switch of `428d8b4`
(`CLEARWATER_WP42_V3_BACKEND` unset = the GPU job; `cpu` = the CPU job), each run writing its
raw file through `CLEARWATER_WP42_V3_FIGURES`: GPU 6 passed in 91.0 s, CPU 6 passed in 470.3 s.
The orchestrator's later grant of the same run by the env-switch route (conditions: (1) state
that `428d8b4` came after Reviewer A converged and is covered by Reviewer B, the variables
unset in the suite; (2) equality on the lines from line 2, both hashes per file; (3) any
difference a STOP) crossed with the STOP; the run was not repeated. Outputs under
`work\wp4.2\v3\window\` (not `v3\`, where `figures-gpu.txt` already held the earlier GPU
record cited at `e3b5d5f`):

| File | md5 | Note |
|---|---|---|
| `figures-gpu.txt` | `3ec7f59c682e8b8319d409a2f4bd5ed5` | head `e3b5d5f5`, backend on every row |
| `figures-cpu.txt` | `1eba25f524befde9627fc063f9191efa` | as above, `cpu` |
| `raw-gpu.txt` | `629f7dc9c85c45418f70f01a9c5c6363` (from line 2: `5fb51f054dda4e6612e89578fb8de45b`) | equal to the earlier light run's `v3\figures-gpu.txt`: GPU deterministic run to run |
| `raw-cpu.txt` | `24a46d0e4c492b8247099da78c184c5c` (from line 2: `4f5b849290e3fb9a2a7a0fce88e782e7`) | |
| `compare.txt` | `d094c8d468dd68a1dffe5fc79b5d52c8` (after the selection was appended; `8d5fc45a556cec2959bc5fc313ce08b3` before) | DIFFERENT, 13 of 64 rows; then the 24-row selection: md5 `b72d9e7b57b53b0e28593c1f55c91abd` from BOTH files, SAME |

The 13 differing rows: 12 encoded-output characterisation (`ad14_encoded`, `encoded_ratios`)
and `ad14-flicker | c3 | planted_ratios.a*` 2.717 against 2.716; listed verbatim in the report.
The encoder was `hevc_nvenc` on both jobs (`resolve_encoder`, `io/video/capability.py:228`).
STOP yielded at 06:26Z (Y3) with recommendation (a); window released.

**CHARC RULING on the V3 STOP (query `e29ac0a1978afabb`, 06:3xZ), verbatim as relayed:**

> RULING on the V3 CPU/GPU STOP (query e29ac0a1978afabb): **(a).** The claim narrows to what V3 and AD-14 decide, which is measured pre-encode by question 5 and matches exactly on all 24 asserted/recorded rows (plus the four planted AD-14 rows and 15 of 16 planted ratios). Conditions:
> 1. The report cites CPU/GPU equality by the md5 of the 24 selected rows from each figures file (the selection recorded in compare.txt), names both whole-file md5s (3ec7f59c / 1eba25f5) and the driver md5 (b128c609), and lists the 13 differing rows verbatim.
> 2. The mechanism (pre-encode floats differing below the figures' rounding, then 8-bit quantisation and NVENC in a near-static masked region) is stated as the cell's READING with the planted row's 0.001 as its one direct evidence, not as an established fact; (c) is NOT required. V4's CPU/GPU SAME is AD-11's tolerance test and is unaffected; say so in one sentence.
> 3. The CPU leg's coverage sentence reads "the same V3/AD-14 figures, not the same encoded characterisation"; the encoded rows are characterisation only, backend-dependent at the second or third decimal with the same encoder (resolve_encoder -> hevc_nvenc on both; capability.py:228 cited).
> 4. Cell 2's unlabelled file stays labelled as its observation.
> Not (b): every deciding figure is equal; failing the claim on characterisation noise would misstate the evidence.

Orchestrator's addition: cite the WINDOW pair of GPU/CPU figures files; name the earlier
`v3\figures-gpu.txt` only as the run-to-run determinism check.

**Applied (cell 3):** the 24-row selection and its md5s appended to `compare.txt` (rule: keys
`ad14_unsmoothed`, `ad14_smoothed`, `ratios.<measure>`, from line 2 in file order, the leading
backend column removed, LF); the report's V3 section REPLACED: the `428d8b4` sentence
(condition (1) of the orchestrator's grant), the coverage sentence as ruled, the window files'
md5s, the driver md5, the 24-row md5, the 13 rows verbatim, the encoder citation, the mechanism as
the cell's READING with its one direct evidence, the V4 sentence, the determinism check, cell
2's file as its observation.

## Rebase onto main after WP4.2b (orchestrator seat)

WP4.2b ACCEPTED (main `3cedac6`, then CHARC's docs `38f291e`). The orchestrator rebased `wp4.2`
onto `38f291e`: clean, no conflict, 22 commits, head `6e0eb1d` (`git log` confirmed at this
seat, tree clean). WP4.2b's `except OutputNameError` branch sits in `check_outputs` at
`tools/headless_export.py:870`, untouched here.

**Semantic collision (CHARC condition 4's anticipated case).** The orchestrator's light set on
`6e0eb1d` (ruff and mypy clean): 966 passed, 1 FAILED, which is the RED:
`tests/test_wp42_runner_video.py::test_a_video_source_whose_stem_carries_a_colon_is_refused_by_check_outputs`
expected `match="in a form the footage check refuses"` (the file-form text, predicate (i)), but
WP4.2b's naming check now refuses `carrier:clip.mp4` EARLIER, inside the same `check_outputs`,
as `OutputNameError` -> `RunnerRefusalError("output name for 'carrier:clip.mp4' must be a single
portable name component")`, still before any job. The test's intent holds (a colon-stemmed video
is refused by `check_outputs` and by `run`, nothing written); only the text moved. FIX (granted
at the orchestrator's seat): both `match=` arguments changed to `"single portable name
component"`, nothing else (`0109c39`, 0 CR); GREEN: `tests/test_wp42_runner_video.py` 14 passed.
The report names no file-form text for a colon video, so it needs no change.

## Two-leg suite window (orchestrator grant item (ii), 2026-10-29)

Head `401521e` (on main `38f291e`, after the rebase and `0109c39`), from Git Bash in the worktree,
`PYTEST_ADDOPTS` unset, `QT_QPA_PLATFORM=offscreen`, the main tree's `clearwater.local.toml`
present (byte-equal), free memory 10.3 GiB before the parallel leg and 11.6 GiB before the serial.

| Leg | Command | Result | Wall | Window |
|---|---|---|---|---|
| parallel | `uv run pytest -q -rs -n 4 -m "not gpu and not footage and not gui and not slow" --basetemp=C:/Users/rwsmy/clearwater/work/wp4.2-mc1-parallel` | **5304 passed, 1 skipped**, EXIT 0 | 644.51 s | 07:33Z-07:43:48Z |
| serial | `uv run pytest -q -rs -m "gpu or footage or gui or slow" --durations=40 --basetemp=C:/Users/rwsmy/clearwater/work/wp4.2-mc1-serial` | **1135 passed, 1 skipped**, 5305 deselected, EXIT 0 | 2,937.31 s | 07:44Z-08:33:27Z |

Skips, the same two as WP4.2a's gate: parallel `tests\test_color_roundtrip.py:121` (swscale
reads a yuvj format as full whatever in_range says); serial `tests\test_photo_check.py:139` (the
footage folder has no photos yet). Logs `work\wp4.2-mc1-parallel.log`, `work\wp4.2-mc1-serial.log`
with their `.done` markers. Serial selected 1136 = WP4.2a's gate 1127 + the 9 new WP4.2 serial
tests (V3 file 6, DR-74 1, DR-67 `gpu` 1, V4 `gpu` 1).

**Question 9 budget (new serial-leg tests, about 300 s).** From `--durations=40` (threshold
8.51 s): V3 `test_ad14_bound...[ancuti2018]` 67.45 s, `[c3]` 44.35 s, the jitter V3 `[c3]` 15.34 s
and `[ancuti2018]` 15.11 s, DR-74 21.81 s: 164.06 s measured; the other new serial entries (the V3
lossless-decode test and the unrounded-figures test, the DR-67 and V4 `gpu` legs, the V3 clips
fixture setup) are each under 8.51 s, so at most about 43 s more: **at most about 207 s, inside
300 s.** The leg's wall is 396 s above WP4.2a's gate (2,540.97 s) on a shared laptop; WP4.2a's
log carries no durations, so the like-for-like split is not available.

## Cell 4 -- task 10, the GX011627 V4 window (orchestrator grant, 2026-10-29)

**Seat.** Worktree head `ab9ea83` on main `38f291e`, tree clean. Every product command ran
from the worktree as `UV_PROJECT_ENVIRONMENT=C:/Users/rwsmy/clearwater/.venv
PYTHONPATH='scripts;src;tools' uv run --no-sync python ...` (Git Bash, `PYTEST_ADDOPTS` unset);
under that form `clearwater.__file__` is `.worktrees\wp4.2\src\clearwater\__init__.py` and
`headless_export` / `video_fidelity` load from the worktree's `tools\`.

**Driver.** `work\wp4.2\v4\window.sh` (md5 `85ca41d64953868791c6b9975d1b5e08`, read and
granted unchanged at the orchestrator's seat; never committed). One job at a time in order;
stop at the first runner exit other than 0 or the first compare without "MANDATORY+REQUIRED
all SAME: True"; a 5 GiB free-memory guard first. Settings were the defaults (no `--method`,
`--encoder`, `--quality`, `--settings-dir`): c3, encoder `auto`, `standard`, 8-bit from 8-bit,
provenance on (the records' `settings` say so). GX011627 was FOUND through
`find_footage_file("GX011627")` (DR-27: found, not skipped); its path was held in a shell
variable and never printed or logged. No `gpmd`, IMU, GPS or location tag was read.
`vid-hlg` and `vid-pq` were left out by the grant (refused by design; the suite's refusal test
covers them). Commands, in order (paths under `C:\Users\rwsmy\clearwater\work\`):

1. `tools/headless_export.py "$GX" --out wp4.2/v4/gx/out --cache-dir wp4.2/v4/gx/cache --record wp4.2/v4/gx/record.json`
2. `tools/video_fidelity.py compare "$GX" wp4.2/v4/gx/out/GX011627_corrected.mp4 --out wp3.10/wp4.2-v4/v4-GX011627-c3-gpu`
3. `tools/headless_export.py <six> --out wp4.2/v4/gpu/out --cache-dir wp4.2/v4/gpu/cache --record wp4.2/v4/gpu/record.json`
4. as 3 with `--force-cpu`, into `wp4.2/v4/cpu/{out,cache,record.json}`
5. twelve `compare tests/fixtures/video/<s>.mp4 wp4.2/v4/<leg>/out/<s>_corrected.mp4 --out wp3.10/wp4.2-v4/v4-<s>-c3-<leg>`
   (bit depth the source's, the tool's default), GPU leg then CPU leg.

The six are the committed WP2.3 fixtures `tests/fixtures/video/{hevc8-bt709-full, hevc10,
rotated, untagged, vfr, truncated}.mp4`, one batch per leg.

**Window.** 2026-10-29T08:42:01Z-08:48:18Z, head `ab9ea83`; free memory 9.39 GiB at the start,
9.37 / 9.68 / 9.66 GiB before the three runner steps, 9.56 GiB at the end; GPU idle before (518
MiB used, 0 %, no compute job). Driver exit 0, `window.done` = OK. Orchestrator's Reviewer B
(Codex in WSL, offline, no tests, no FFmpeg) ran on a separate worktree; nothing else heavy.
Logs `work\wp4.2\v4\logs\` (`steps.txt`, one log per step).

| Item | Leg | Runner state | Frames (src / out) | MANDATORY / REQUIRED / BEST-EFFORT different | Verdict |
|---|---|---|---|---|---|
| GX011627 | GPU | done with warnings (2: camera firmware tag, camera settings atoms not carried) | 681 / 681 | 0 / 0 / 8 | SAME |
| hevc8-bt709-full | GPU / CPU | done / done | 45 / 45 | 0 / 0 / 6 | SAME / SAME |
| hevc10 (10-bit record) | GPU / CPU | done / done | 45 / 45 | 0 / 0 / 6 | SAME / SAME |
| rotated | GPU / CPU | done / done | 45 / 45 | 0 / 0 / 5 | SAME / SAME |
| untagged | GPU / CPU | done with warnings (the assumed-tags warning) | 45 / 45 | 0 / 0 / 6 | SAME / SAME |
| vfr | GPU / CPU | done / done | 30 / 30 | 0 / 0 / 6 | SAME / SAME |
| truncated | GPU / CPU | done with warnings (the D86 "cut short" warning) | 24 / 24 | 0 / 0 / 8 (2 D86 notes: readable part to 0.800800 s; audio on the kept packets) | SAME / SAME |

13 compares, 13 SAME on every MANDATORY and REQUIRED item, 46 items each. GX011627's eight
BEST-EFFORT differences are the same eight item names as WP3.21's
`work\wp3.10\wp3.21-v4\v4-GX011627-c3-gpu` record.

**Record fields** (`record.json`, schema 1, method c3, `parameters_from` defaults, `cancelled`
false, no failure):

| Run | `JobResult.device` | `video.device_backend` | `video.frame_device` | `video.encoder` | `decode_passes` | Elapsed (information only, never V16) | md5 |
|---|---|---|---|---|---|---|---|
| GX011627 | `GPU` | `cuda:0` | `cuda:0` | `hevc_nvenc` | 2 | job 218.9 s (step wall 220.2 s) | `4922fd542dc4822171979fcdd93298e8` |
| WP2.3 GPU (each of six) | `GPU` | `cuda:0` | `cuda:0` | `hevc_nvenc` | 2 | jobs 3.0-7.1 s, batch 23.8 s | `4d892589bc701a8bcea7958ba80ee5c7` |
| WP2.3 `--force-cpu` (each of six) | `CPU: forced` | null | `cpu` | `hevc_nvenc` | 2 | jobs 3.9-6.3 s, batch 30.5 s | `99294d0a0e147ba263bd001e0d45a0e2` |

Counts: GX011627 1 done with warnings; each WP2.3 leg 4 done, 2 done with warnings. Compare
records under `work\wp3.10\wp4.2-v4\v4-<item>-c3-<leg>\` (`.compare.json` and `.compare.md`).
Kept, nothing deleted: every output, cache, record, log and compare record above. Nothing
footage-derived is committed.

## Reviewer B -- disposition and remediation (cell 4)

**Reviewer B** (the orchestrator's seat, Codex `gpt-6.1-sol` / high, WSL, read-only, offline) on
`wp4.2-mc` `ab9ea83`, base `38f291e`: probe READY, exit 0 (08:55:22Z), worktree clean after, no
withheld path read. **`VERDICT: NEW_CRITICAL_MAJOR_FOUND`**: 2 MAJOR, 4 MINOR, 4 ADVISORY. Text
`C:\Users\rwsmy\clearwater-review-evidence\wp4.2\reviewB\review-B.txt`, md5
`b1865ba284b429169fcdc798e15f7431` (35 lines). The orchestrator's eleven dispositions, each
CONFIRMED against the file at `265251f` before the change (the one bounded remediation, fill
Part 2 "Disposition"):

| # | Severity | Finding (where) | Confirmed | Disposition | Change |
|---|---|---|---|---|---|
| B1 | MAJOR | `CLEARWATER_WP42_V3_FIGURES` reaches `mkdir` / `write_bytes` with no footage check (`tests/test_wp42_v3_product.py:63-76`) | yes (no `write_target_refusal`, no containment) | FIX | `create_figures_file`: no configured footage folder = refused; `headless_export.write_target_refusal(path, configured_footage_folder())` BEFORE `mkdir`; a refusal is `pytest.fail` with its text, nothing created |
| B2 | MAJOR | "NEW file" not atomic: `exists()` then `write_bytes` (`wb`), a dangling link passes (`:73`) | yes | FIX | exclusive `open(path, "xb")`; the module fixture yields that ONE handle and closes it at teardown; `_keep` writes through it (never reopened); docstrings corrected |
| B3 | MINOR | the builder test never passes a backend to `video_sink` (`tests/test_wp42_composition.py:114`) | yes | FIX | a distinct `DeviceFrameBackend`-shaped stand-in (`device` `cuda:7`) passed to both builders; source and sink hold it (`sink._device_backend is backend`); the `None` variant holds None |
| B4 | MINOR | DR-74's assertions allow a release before rendering (`tests/test_wp321_fft_release.py:195`) | yes (`written` sampled before the release; 0 satisfied it) | FIX, inside DR-74's case only | `started` = frames written when the release begins, asserted `>= 1`; `remaining` = frames still to write, sampled once the pool drop is observed, asserted `> 0`; the DR-73 (b) rename untouched |
| B5 | MINOR | the missing-cache promise is not on every route (`src/clearwater/app/composition.py:204`) | yes: `jobs/export.py` `_video` runs `resolve_encoder`, `_plan`, `_check_space` before `_analyse` asks `key_for` | FIX, docs only | `_NoCacheFolder` and `export_jobs` docstrings: fails before any write; an earlier refusal (the encoder, output planning, the disk-space check) may be reported first. No control-flow change; the report does not repeat the promise (its runner line is the `RunnerRefusalError` route), so no report change |
| B6 | MINOR | the runner's write-path description (`tools/headless_export.py:5`, `write_target_refusal`) | yes (`run()` opens `DiskProxyCache`; analysis writes without `SafeWrite`) | FIX, docs only | module docstring: outputs through the engine and `SafeWrite`; the cache under `--cache-dir` writes proxies and statistics through `DiskProxyCache`, opening it may remove stale entries; the predicate's residual: never writes over an existing OUTPUT file. Nothing else in the file |
| B7 | ADVISORY | the import-time witness misses the three video constructors (`tests/test_app_composition.py:183`) | yes | BANK | report, "For WP4.3" note; no test change (not WP4.2's file) |
| B8 | ADVISORY | the count guard is a minimum (`analysis/engine.py:780`) | yes (as stated) | RECORD | report Limit sentence |
| B9 | ADVISORY | own clip inherits the key's size-and-mtime collision (`cache/keys.py:50`) | yes (pre-existing, documented) | RECORD | report Limit sentence |
| B10 | ADVISORY | inherited `FFREPORT` is a write route (probe, decoder, the two new test launches) | yes (no explicit environment on the launches) | BANK, pre-existing | **DR-58 (b) re-sighting** for CHARC: the probe part is DR-58 (b); the decoder launches (`decode.py:330`, `:344`) and the two new test FFmpeg launches (`tests/test_wp42_v3_product.py` `_encode_lossless`, `tests/test_wp321_fft_release.py` DR-74's clip) inherit it the same way. No code change |

**A correction to B2's premise (reproduced, not a disagreement with the fix).** On this laptop
(Python 3.12, Windows 11, symlink creation allowed) `open(dangling_link, "xb")` SUCCEEDS and
creates the link's target: probe in the session scratchpad, "symlink ok True False / xb opened!".
So exclusive creation alone does not refuse a dangling link here; the footage check's rule (ii)
(every existing step is its own real path, a dangling link included) does, before the open. The
new test says so in a comment. A link planted between the check and the open is the predicate's
stated residual ("a link created after the check is not seen", WP4.2a).

**RED first (scratch, never committed; `work\wp4.2\b-remediation\red\`).**
- B1/B2: `old_logic.py` reproduces the `265251f` fixture logic (exists, `mkdir`, `write_bytes`,
  then append); `test_red_figures.py` = the new file with its import pointed there, run with
  `--noconftest`: **3 failed, 2 passed**. Failed: inside-the-footage-folder (DID NOT RAISE), the
  dangling link (DID NOT RAISE), no footage folder configured (DID NOT RAISE). Passed: the
  existing file (the old `exists()` refused it) and the fresh-path control.
- B3: plugin `plant_b3.py` (`video_sink` discards its argument): **1 failed, 1 passed**; `[gpu]`
  failed (`None = FFmpegVideoSink._device_backend`), `[None]` passes by construction (a discard
  yields None).
- B4: plugin `plant_b4.py` (the first `FakeSink.write` waits until the `export-analysis` thread
  has ended, so the analysis-end release runs with nothing written): **1 failed**, `assert 0 >=
  1` on `started` (21.76 s).

**GREEN.**
- `tests/test_wp42_v3_figures.py`: 5 passed (2.75 s). B3 node: 2 passed.
- Light window (orchestrator grant with this turn; 9.5 GiB free, 09:03:25Z-09:05:14Z, nothing
  else heavy): `test_v3_ratio_on_the_jittering_patch_clip_with_the_product_method[c3]` with the
  variable UNSET 1 passed (17.33 s); with `CLEARWATER_WP42_V3_FIGURES` =
  `work\wp4.2\b-remediation\figures-jitter-c3.txt` (new) 1 passed (15.44 s), the file
  (md5 `e3abba2b0040961b8604361fd3f1d6d1`) holds two lines: `backend: cuda:0`, then
  `jitter c3: ad14_unsmoothed 0.1006; ad14_smoothed 0.0017; ad14_encoded 0.0378; ratios
  {'L*': 0.018, 'a*': 0.014, 'b*': 0.026, 'contrast': 0.016}; encoded_ratios {...}`. DR-74's
  case 1 passed (21.59 s). The one warning in each is CuPy's "CUDA path could not be detected".
- `ruff check .` clean; `ruff format --check .` 267 files; `mypy` 141 files clean. Light set
  (`-n 4`, `not gpu and not footage and not gui and not slow`): the new file,
  `test_wp42_composition.py`, `test_wp321_fft_release.py`, `test_app_composition.py`,
  `test_headless_export.py` (the last two unchanged): **107 passed** (12.51 s).
- Logs `work\wp4.2\b-remediation\*.log`.

**CHARC addendum (`d0ba2d12`, CONCURS with every disposition):** two points. A row where the
named path's parent is inside the stand-in footage folder and does not exist yet: it is refused
and no folder is created. And the one module-scope `"xb"` handle. Both were already met at
`5e74d01`, so nothing changed:
- The row is `test_a_path_inside_the_footage_folder_is_refused_and_nothing_is_created`. Its target
  is `footage/records/figures.txt`, it asserts `footage` stays empty, and it was RED on the old
  logic.
- The fixture yields the one handle, and `_keep` writes through it.

## Reviewer A -- terminated at round 2 (cell 4)

Head `5e74d01`; diff `git diff -U8 265251f..HEAD` without `docs/proofs` (7 files). The prompt
names the eleven dispositions; Reviewer B's text was not given.

Evidence is in `C:\Users\rwsmy\clearwater-review-evidence\wp4.2\r2\`:
- `run_review.sh`, `review-prompt.md`, `test-summary.txt`, the probe files, `adjudication.md`,
  `md5sums.txt`;
- `review-diff.txt`, md5 `e0e17b049c47e355df081eb3ca424a72`;
- `review.txt`, md5 `010afb8732c95876dd9902187cff2b8b`.

The probe answered READY (09:09:36Z, `gpt-6.1-sol`, high). The review exited 0 at 09:14:11Z, with
14 `succeeded in`, 104,080 tokens used and no withheld path read.
**`VERDICT: NO_NEW_CRITICAL_MAJOR`**: 0 critical / 0 major / 3 minor.

| # | Severity | Tag | Finding | Adjudication | Blocking | Ruling (orchestrator) |
|---|---|---|---|---|---|---|
| R2-1 | MINOR | REASONED | DR-74's new assertions depend on thread scheduling: the render may not have started at the analysis-end release, or may finish during it | CONFIRMED as a risk: nothing in the product makes analysis wait for a write. Passed in both GPU runs | no | FIX, deterministic on BOTH halves: a bounded wait for the first frame, and the sink holds the next write until the drop is recorded. A miss fails; it never hangs |
| R2-2 | MINOR | EXECUTED | `create_figures_file` leaks the `"xb"` handle when the first line's write or flush raises | CONFIRMED | no | FIX: close and re-raise; add a row with a raising write |
| R2-3 | MINOR | REASONED | The new tests do not enforce exclusive creation or the one handle | CONFIRMED | no | FIX: a file planted between the predicate and the open; exactly one open across `_keep`; each RED against the weaker form |

Zero new blocking findings, so the loop TERMINATES at round 2 (fill CONVERGENCE_CRITERION). The
three fixes are a terminating test-only cleanup in owned files, as R1's were, with no further
counted round.

Next, in order:
1. The orchestrator's one Reviewer B re-run on the final candidate.
2. Its two-leg gate, the package's ONE gate under CHARC's order.
3. The FINAL docs turn.

**Cleanup (test-only).**
- **R2-1** (`tests/test_wp321_fft_release.py`, DR-74's case only, `HOLD_S = 30.0`):
  - The sink's write after the first frame waits on `dropped`, which the analysis-end spy sets
    once the pool drop is recorded. If the wait runs out it raises `TimeoutError("DR-74: no
    analysis-end pool drop within 30.0 s of the first frame")`.
  - The analysis-end spy waits up to `HOLD_S` for the first written frame. A miss fails as
    "rendering had not started within 30.0 s of the analysis end".
  - The DR-73 (b) rename is untouched.
- **R2-2** (`tests/test_wp42_v3_product.py`, `create_figures_file`): the first line's write and
  flush run inside `try`; any exception closes the handle and re-raises. The docstring's `Raises`
  is updated.
- **R2-3, plus R2-2's row** (`tests/test_wp42_v3_figures.py`, now 8 rows):
  - `test_a_file_planted_after_the_footage_check_is_refused_and_left_unchanged`: the predicate is
    monkeypatched to plant the file after it checks.
  - `test_every_line_goes_through_the_one_open`: `io.open` and `builtins.open` are counted for the
    target, and the count is exactly `["xb"]` across three `_keep` lines.
  - `test_a_failed_first_line_closes_the_handle`: `Path.open` returns a handle whose writes raise.
    The `OSError` propagates and the one handle is closed.

**RED (scratch, never committed; `work\wp4.2\b-remediation\r2c\`).**
- **DR-74 plants.** Neither run hung.
  - `plant_b4.py` (the first write is held until the analysis thread ends): 1 failed, "rendering
    had not started within 30.0 s of the analysis end / assert 0 >= 1" (51.16 s).
  - `plant_release_waits.py` (the analysis-end release waits for the sink's close, bound 45 s):
    1 failed, "gated-1080p.mp4: TimeoutError: DR-74: no analysis-end pool drop within 30.0 s of
    the first frame" (59.85 s).
- **Weaker helpers.** `weak.py` plus `test_weak_figures.py` (the new file pointed at a weaker
  helper, run with `--noconftest`):

  | Weak form | Result | Failed row(s) |
  |---|---|---|
  | `noclose` (the `5e74d01` helper) | 1 failed / 7 passed | the failed-first-line row |
  | `existswb` (`exists()` first, then the check and `"wb"`) | 2 failed / 6 passed | the planted-after-the-check row; the one-open row (mode `wb`) |
  | `reopen` (`_keep` reopens by name) | 1 failed / 7 passed | the one-open row |

**GREEN.**
- DR-74's case on the real product, three runs (light `gpu`, my own test, 09:18Z-09:21Z): 1 passed
  each, in 21.02, 20.72 and 20.63 s.
- `tests/test_wp42_v3_figures.py`: 8 passed.
- `ruff check .` clean; `ruff format --check .` 267 files; `mypy` 141 files clean.
- Light set (`-n 4`, the five files of the remediation's set): 110 passed (15.85 s).

## Reviewer B re-run (orchestrator seat; cell 4 docs-only turn)

The re-run ran on `wp4.2-mc` `33f13e5`. That is `wp4.2` at `9aa2783` rebased onto main `246052b`,
whose new commits are CHARC docs only; the package files are byte-identical and the patch-id
(`d1fbdf7d`) is equal on both bases. Codex `gpt-6.1-sol` ran 09:24Z-09:36:50Z, exited 0, left
the candidate worktree clean and read no withheld path.

**`VERDICT: NO_NEW_CRITICAL_MAJOR`**, with 4 MINOR findings. The text is
`C:\Users\rwsmy\clearwater-review-evidence\wp4.2\reviewB2\review-B.txt` (32 lines), md5
`cabd2c51e708ca23916b4f5bd4c81203`. Each item was CONFIRMED against the file before any change:

| # | Finding | Confirmed | Disposition | Change |
|---|---|---|---|---|
| B'1 | A packet-listing timeout text (`io/video/verify.py:234`, not owned) carries the full FFprobe executable path. The runner's `Redactor` does not know that path. Reachable only on a 120 s ffprobe timeout | yes, as stated | BANK | None. **DR-81 (c) candidate for CHARC**, trigger "the runner's next redaction touch, WP4.3". WP4.2 makes no `Redactor` edit |
| B'2 | The record's video facts (`tools/headless_export.py` ~57) misdescribe failures. `_ObservedSink.write` notes the device BEFORE delegating, so a failed first write still sets `frame_device`. `decode_passes` counts the passes started | yes (`write` at `:262-272`, `frames` at `:225-232`) | FIX, docs only | `frame_device` is the frame device of the sink's first ATTEMPTED write, set even when that write failed. `decode_passes` is 1 (V17) or 2 for an export that got as far as rendering, and 1 for a job that failed after its analysis began and before rendering. No code change |
| B'3 | `_NoCacheFolder` says "every use refuses", but `limit_bytes()` returns 0 (`src/clearwater/app/composition.py` ~89) | yes (`:130-132`) | FIX, docs only | Every operation that needs a cache folder refuses with `VIDEO_NEEDS_A_CACHE`; `limit_bytes` returns 0 |
| B'4 | `_parser()`'s description says photos only (`tools/headless_export.py` ~1130) | yes | FIX, help text only | Now "Export photos and video through ...". No test pins the old text: a grep for "Export photos through" found only the tool itself and its `.pyc`, nothing in `tests/` |

Gates after the change: `ruff check .` clean (the new help line was wrapped to 100 columns); `ruff
format --check .` 267 files; `mypy` 141 files clean; light set (`-n 4`):
`tests/test_headless_export.py`, `tests/test_wp42_runner_video.py` and
`tests/test_app_composition.py`, 97 passed (25.83 s). `--help` now opens with "Export photos and
video through Clearwater's export engine without the interface."

## Two-leg gate (orchestrator seat)

| Head | Leg | Command | Result | Wall | Window | EXIT |
|---|---|---|---|---|---|---|
| `wp4.2-mc` `8bc927a` (`798af0c` rebased onto `246052b`, patch-id `7dfc431f` equal) | parallel | `uv run pytest -q -rs -n 4 -m "not gpu and not footage and not gui and not slow" --basetemp=work/wp4.2-gate-parallel` | 5312 passed, 1 skipped (`test_color_roundtrip.py:121`) | 659.60 s | 09:41:40Z-09:52:48Z | 0 |
| same | serial | `uv run pytest -q -rs -m "gpu or footage or gui or slow" --durations=40 --basetemp=work/wp4.2-gate-serial` | 1135 passed, 1 skipped (`test_photo_check.py:139`), 5313 deselected | 2,621.32 s | ending 10:36:31Z | 0 |

Conditions: Git Bash, `PYTEST_ADDOPTS` unset, the offscreen Qt platform, the main `work/`
configuration, the worktree's own `.venv` from the lock, 10.99 GiB free before.

- Static checks on `8bc927a`: ruff check clean; ruff format 267 files; mypy 141 files clean.
- Harness gate: 382 OK, 1 skipped.
- Question 9 at the gate: at most about 127 s of 300 s (100.28 s measured in the top 40, plus at
  most about 26 s for the four under the 6.58 s cut-off).
- Logs: `work\wp4.2\gate-logs\`.

## Done

Every Definition-of-done item (plan 4.5 and the brief's Done row) with its evidence:

| Item | Evidence |
|---|---|
| Scope within owned files; frozen interfaces unchanged | the build record and each turn's `git diff --stat`; no `interfaces/` change |
| Docstrings; ruff, format, mypy | gate static checks on `8bc927a` |
| The full two-leg suite | GREEN at the orchestrator's seat, above |
| Existing tests unchanged except as ruled | Q2's router pins, R1-Q3's in-place edit, Q8's rename, plus the rebase match= fix `0109c39` (granted) |
| DR-67 test | `tests/test_wp42_device_backend.py` (build record) |
| V4 SAME in the suite | `vid-hevc8-bt709-full` on the CPU and the GPU |
| V4 SAME in task 10 | GX011627 and the WP2.3 set: 13 of 13 SAME (cell 4, task 10) |
| V9, V17, own clip, DR-45 (b), cancel and failure | `tests/test_wp42_video_path.py` (report Evidence) |
| V3 with the product method | AD-14 asserted and ratios recorded; CPU/GPU equal by the 24-row md5 (CHARC ruling (a)) |
| DR-71, DR-74, DR-73 (a)+(b), DR-45 (b) closed; DR-47 per Q6 | build record; report "Register dispositions" |
| Write targets through the one predicate | task 5 tests |
| Footage-check and cache-interior Limits | report Limits |
| V3 ratios in the report; V12 deferred | report |
| Serial-leg budget (Q9) | at most about 127 s of 300 s at the gate |
| Reviewer A converged | R1 terminated, then R2 on the remediation terminated |
| Reviewer B | NEW_CRITICAL_MAJOR_FOUND, then remediated `5e74d01` (CHARC `d0ba2d12`), then the re-run NO_NEW_CRITICAL_MAJOR with B'2-B'4 in `798af0c` (CHARC `a5decb35`: no logic) |
| Completion report | `docs/reports/wp4.2-video-path.md`, FINAL |
| Nothing footage-derived committed; outputs kept | task 10 and the remediation windows |

The package is complete. Cell 4 is not resumed unless the accept finds something.
## Done: RESUME HERE (task 10, the GX011627 V4 window) -- carried out by cell 4 above

For a fresh cell: read `docs/dispatch-recipe.md`, the brief (task 10, question 10; the Rulings
govern), this ledger and `docs/reports/wp4.2-video-path.md`. State: Reviewer A CONVERGED (R1,
cleanup committed); the CPU/GPU V3 record done (CHARC ruling (a)); the rebase onto `38f291e`
done by the orchestrator; the two-leg suite GREEN at `401521e` (above). Remaining: task 10 ONLY
when the orchestrator grants its ONE EXCLUSIVE window, then the return report (recipe section 4,
under about 70 lines, by SendMessage to the orchestrator).

Task 10, per the brief:
- GX011627 through the runner on the product composition: c3 defaults, `--encoder auto` (NVENC),
  Standard, 8-bit, the GPU job with device frames. Source path only from
  `tools/local_config.find_footage_file("GX011627")` (never listed, written or decoded beyond
  the export; no `gpmd`, IMU, GPS or location tag read). Shape:
  `uv run python tools/headless_export.py <source> --out C:\Users\rwsmy\clearwater\work\wp4.2\v4
  --cache-dir <an existing folder under work\wp4.2\> --record <new .json under work\wp4.2\>`
  (`--cache-dir` must exist; the record must not).
- Then `uv run python tools/video_fidelity.py compare SOURCE OUTPUT --out
  C:\Users\rwsmy\clearwater\work\wp3.10\wp4.2-v4\` (the tool refuses an `--out` outside its
  `wp3.10` root): every MANDATORY and REQUIRED item SAME, else a STOP.
- In the same window, the WP2.3 V4 set (`vid-hevc8-bt709-full`, `vid-hevc10`, `vid-rotated`,
  `vid-untagged`, `vid-vfr`, `vid-truncated`; `vid-hlg` and `vid-pq` are refused by design)
  through the runner on the GPU and with `--force-cpu`, each compared the same way.
- Record: `JobResult.device`, the record's `"video"` object (`device_backend`, `frame_device`
  `cuda:0`, `encoder`, `decode_passes`), the encoder, the elapsed (information only, NEVER a V16
  row). Nothing footage-derived committed; keep the outputs (no deletion without a grant naming
  them). At least 5 GiB free before. End with `WINDOW RELEASED: <summary>`.

## Superseded: RESUME HERE (Reviewer A round 1)

For a fresh cell: read `docs/dispatch-recipe.md`, the brief (Rulings govern), this ledger and
`docs/reports/wp4.2-video-path.md` (the claims). The build is complete and committed; light gates
green. Next: Reviewer A per the fill Part 1 (Codex `gpt-6.1-sol` / high, WSL, probe first); copy
`run_review.sh` and `review-prompt.md` from `C:\Users\rwsmy\clearwater-review-evidence\wp4.1\r5\`;
diff `git diff -U8 f991254..HEAD` with `--glob '!docs/proofs/**'`; WHAT TO EXAMINE = the brief's
list; evidence to `C:\Users\rwsmy\clearwater-review-evidence\wp4.2\r1\`. YIELD after
adjudicating each round (no change in that turn). Then the two-leg suite in a granted window,
then task 10 only when granted.
