# WP4.2 ledger -- Video path end to end

Cell 1 (implementer-opus-high), worktree `.worktrees/wp4.2`, branch `wp4.2`, base main `aa4761b`
(brief FINAL, CHARC `c8340144a8e87c09`). Round 0 only in this seat (ledger-only commit); the
build waits for WP4.2a's merge and the orchestrator's rebase (R1-Q5 condition 3, CAP +3 h).

## Depth (filled by the dispatcher from `scripts/cell_depth.py`)

| Gate | Cell | Depth (tokens) | Read at | Note |
|---|---|---|---|---|
| Y1 (round 0) | cell 1 | 209,438 (70 turns) | 2026-10-29 02:33:37Z | at Y1; cell 1 STOOD DOWN 02:35Z, build to a fresh cell |

## Round ledger (Reviewer A, Codex `gpt-6.1-sol` / high, WSL)

| Round | Critical | Major | Minor | In / out of envelope | New / reopened | Reverts | Fixes: product / test-only | Transport, CLI | Depth |
|---|---|---|---|---|---|---|---|---|---|
| (none yet) | | | | | | | | | |

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

## RESUME HERE (build)

For a fresh cell after the build grant: read `docs/dispatch-recipe.md`, the brief (Rulings and
Revision 1 rulings govern), this ledger's design table AS RULED (the orchestrator's reply to
Y1 carries the rulings on G1 and R0-Q1..Q6; record them here verbatim first). Confirm the
branch was rebased onto main with WP4.2a merged (`git -C <wt> log --oneline -3`; WP4.2a's
helper and `check_outputs` file check present in `tools/headless_export.py`). Build order:
item 1 (DR-67 hook + `test_wp42_device_backend.py`, RED first with planted wirings), item 2
(root + `test_wp42_composition.py` + router pin (a)), item 3/4 (runner + pins (b) (c) +
`test_wp42_runner_video.py`), items 8/9 (G1, RED on the reproduction first), item 10, items
11/12, then `test_wp42_video_path.py` and `test_wp42_v3_product.py` (a V3 miss = STOP with the
figures), light gates (ruff, format, mypy, the targeted files plus the four deps tests), then
Reviewer A from WP4.1's `r5\` runner shape, then `WINDOW REQUEST` for the two-leg suite, then
task 10 only when granted. Reproduction scripts: the round-0 scratchpad scripts are NOT durable;
their content is summarised under "Round 0 -- read and map" and is re-derived by the RED tests.
