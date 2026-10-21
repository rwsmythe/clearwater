# WP3.11 — Analysis engine (dispatch brief, DRAFT for CHARC)

**Status:** DRAFT 2026-10-21 for CHARC (commission `e7745b2be6fdd55c`, tranche A); drafted by a
drafting helper of the orchestrator (gen 9). Owner decisions: none inside the package. The 2.0 s
smoothing default is spec text (7.2, "provisional"); adopting a step-aware variant as the
default would change it and is the owner's (question 6).
- Spec **v0.5.4** (approved by the owner 2026-10-20, AD-27). Architecture FINAL 1.0 section 2
  (video analysis and preview data flow, "Parameter change (AD-7)"), section 3 (IF-1, IF-3,
  IF-4, IF-5, IF-7, IF-8), section 5 ("**Analysis** (WP3.11): proxy 540 (AD-5) to the cache
  (AD-5, IF-7); staged statistics (AD-6); smoothing (AD-3) with a step-aware variant as a design
  task; provisional preview (AD-15)"), section 10 ("Step-aware smoothing variant | WP3.11 design
  task (AD-3)"); AD-3, AD-5, AD-6, AD-7, AD-14, AD-15, AD-20. Frame
  `docs/briefs/wp2.4-phase3-frame.md` (section 5 maps "D98 one stage permitted" and "7.2
  smoothing default, step-aware task" here). Reports `docs/reports/wp1.4-statistics.md`
  section 7, `docs/reports/wp1.4b-gain-cap-noise.md` claims 10 and 10b,
  `docs/reports/wp3.12-proxy-cache.md` ("Public API", "Differences between the stub and the
  product (WP3.11 consumer notes)"). DR-23, DR-25, DR-41 (row "Debt and decided items").
- Cell: `implementer-opus-high`. Tier **STRONG**.
- Worktree `.worktrees/wp3.11`, branch `wp3.11`, base = the main commit named at dispatch.

**Why.** Spec 7.1: "**The statistics are chained.** Each is measured on the output of the stage
before it". This package is the host side of IF-3's staged scheme: the decode pass that makes
and caches the proxies, the per-stage analysis over a clip, the smoothing over pts, the
limited recompute after a parameter change, and the state the shell reads to keep export
disabled until the clip is analysed (AD-15). WP3.14 (export), WP3.18 (timeline and analysis)
and WP4.2 (video path end to end) consume it.

| Field | Content |
|---|---|
| ID and title | WP3.11 — Analysis engine; plan section 6 Phase 3 row WP3.11 (size L); module `clearwater.analysis` (plan 8.1: "Decode pass, staged statistics, smoothing, recompute") |
| Goal | An analysis engine that, for one clip, runs the decode pass that stores 540-line proxies in the IF-7 cache, measures each method stage over every frame on the STORED proxies using the smoothed earlier stages, smooths each declared statistic with a centred filter whose window is in seconds over pts, keeps the statistics in an IF-4 store keyed by pts, recomputes after a parameter change from the first invalidated stage (frames near the displayed one first), supplies the provisional statistics, and supports cancel; plus the step-aware smoothing design task. |
| Spec / decision clauses | Plan bullet "**WP3.11** runs the decode pass that stores proxies; computes statistics stage by stage from the proxies, each stage using the smoothed results of earlier ones; applies the centered, time-based smoothing; limits recomputation after a parameter change to frames near the one displayed; supplies per-frame statistics for the provisional preview; and supports cancel. It is built and tested against a stub method and a stub frame source, so it does not wait for WP3.4 or WP3.9." 7.2: "1. **Decode pass:** every frame is decoded once and a low-resolution proxy of it is stored (Section 7.3). Runs in the background when a clip is opened, shows progress, and can be cancelled (cancel returns to an unloaded state)."; "2. **Staged statistics (D97):** for each stage, in the method's declared order: the stage's statistics are computed for every frame from the proxies, using the smoothed results of earlier stages; a centered (non-causal) temporal filter is applied to each statistic the method declares smoothable. The window is defined in time (seconds), not frames (D95). Default (0.5.4, AD-3, provisional): a 3-frame median followed by a Gaussian with a 2.0 s window. A genuine lighting step inside a clip is not hidden by the window (deep look check 2026-10-20); a step-aware variant is a design task for the analysis engine."; "3. **Render pass:** correct each frame using the smoothed statistics. Used for both preview and export."; "A single-stage (flat) method is permitted."; "No scene-cut handling; inputs are continuous clips."; "**Provisional preview (D108).** When a clip is opened, the current frame is shown immediately, corrected with its own unsmoothed statistics, while analysis runs in the background. The preview switches to the smoothed statistics when they are available." 7.3: "When a parameter changes, the statistics that depend on it, and every later stage, are recomputed from the proxy cache rather than by re-decoding the source (D59), then re-smoothed."; "For live preview, only frames within reach of the displayed frame's smoothing windows need recomputing. The recompute scheme is a design item."; "Statistics with a closed-form dependency on a parameter or on an earlier stage may be updated directly without touching the proxy."; "Smoothing, and statistics that depend on parameters or earlier stages, are always recomputed from the cache."; "Reopening a clip skips the decode pass." D57 "*(amended by D97)* All whole-frame statistics (incl. sharpening normalization, saliency reference) are analyzed and smoothed, in dependency order"; D59 "Parameter changes recompute statistics from a low-resolution proxy cache built during analysis"; D70 "Analysis pass has a cancel control"; D95 "Variable-frame-rate input processed with timing preserved; smoothing window defined in time, not frames (tested per D115)"; D97 "Whole-frame statistics are analyzed in ordered stages; each stage is measured using the smoothed results of the stages before it. A method may declare a single stage"; D98 "... a method may declare one stage; the plug-in interface stays staged"; D108 "Provisional preview: on clip open the current frame is shown at once using its own unsmoothed statistics while analysis runs in the background"; D113 "Cache key includes a cache format version; the cache holds only results that depend on the source file alone; smoothing is always recomputed". Feeds V3 (synthetic clip; "pass if flicker with smoothing ≤ 25% of flicker with per-frame (unsmoothed) statistics") and V18 "on opening a clip, a corrected frame is shown before analysis completes, and it updates to the smoothed statistics afterwards." AD-3 ("`median_gaussian` (3-frame median, then a centred Gaussian), default window 2.0 s, defined over pts (D95). PROVISIONAL (DR-25(3)).", "WP3.11 carries a design task for a step-aware variant ... evaluated on the deep clip before the default is confirmed at WP5.2"); AD-5 as ruled ("measured at first analysis AND on reopen from the same round-tripped pixels, so V17 and V8 hold by construction"; "WP3.11 measures on the stored proxy only."); AD-7 ("a parameter change re-measures from the first stage it invalidates, first for the frames within the displayed frame's smoothing reach (±29 frames at 2.0 s, 29.97 fps), then the rest of the clip in the background"; "Export waits for the whole clip's recompute."); AD-14 (the flicker clip; "the metric is the mean absolute frame-to-frame difference of the corrected output in that region, which must stay under 0.5/255 after smoothing"); AD-15 ("export is unavailable until analysis of that clip completes"; "Cancel returns to the unloaded state"). |
| Depends on | WP2.2 (`b288533`, IFs frozen; IF-7 amended under AD-20). WP3.12 merged (accept `3aaf395`): `clearwater.cache.DiskProxyCache`, `cache_key`, `DEFAULT_CODEC` (JPEG q75 4:4:4), `round_trip`. WP3.1 merged (`f4acbd0`): `clearwater.core.NumpyBackend`, `select_backend`. WP2.3 samples `ad14-flicker`, `ad14-mask` (V3, AD-14), `vid-vfr` (D95), through the `sample` fixture. **Stubs (frame rule 2):** `clearwater.interfaces.stubs.StubCorrectionMethod` (IF-3, stages `C3_STAGES`, zero statistics, identity render) and `StubVideoSource(frames, probe_result)` (IF-5) until WP3.4 and WP3.9 merge; `StubProxyCache` and `StubProgress` for unit tests; `StubStatisticsStore` is the reference shape of IF-4 only. Tests build non-trivial statistics with test-local subclasses of the stub method (a one-stage one for D98, one with a closed form for AD-7). |
| Files owned | `src/clearwater/analysis/` (NEW: `__init__.py`, and modules the round-0 table names, for example `proxy.py` (AD-5 proxy), `store.py` (the IF-4 store), `smoothing.py` (the filters over pts), `engine.py` (decode pass, stages, recompute, cancel, state)); `tests/test_analysis_*.py` (NEW); `docs/reports/wp3.11-analysis.md`; `docs/proofs/wp3.11-ledger.md`. X1-style owned outside the module path: `tools/step_aware_eval.py` (question 6). NOT owned: `src/clearwater/interfaces/` (AD-20), `src/clearwater/cache/`, `src/clearwater/methods/`, `src/clearwater/gui/` (the proxy rule's owner, question 3), `src/clearwater/io/`, `tools/prototype/` (read-only reference), `pyproject.toml` (no dependency; SciPy is already a product dependency), `tests/conftest.py`, `tests/fixture_plugin.py`. |
| Interfaces provided | IF-4: a class satisfying `clearwater.interfaces.statistics.StatisticsStore` exactly as frozen (`put`, `raw`, `smoothed`, `smooth(stage, names, window_s, kind)`, `invalidate_from`, `pts_range`, `all_pts`, `schema_hash`), keyed by `pts_ticks`. Outside the IFs: the engine API named at round 0 (start an analysis as an IF-8 job `Callable[[Progress], JobResult]` that `clearwater.gui.contract.JobRunner.run` can take; state readable as `gui.contract.AnalysisState`'s fields `phase`, `done`, `total`, `message` without importing `gui`; provisional statistics; recompute after a parameter change; the smoothed record per pts for render). |
| Interfaces consumed | IF-1 `Frame` (`pixels`, `pts`, `pts_ticks`, `time_base`, `color`); IF-3 `CorrectionMethod` (`id`, `parameters`, `stages`, `analyze`, `closed_form`) and `Stage` (`statistics`, `smoothed`, `depends_on_parameters`, `depends_on_stages`, `source_only`); IF-5 `VideoSource.frames(probe, *, hw_decode, start_s, end_s)` and `ProbeResult` (`video.nb_frames`, `video.time_base`, `video.color`); IF-7 `ProxyCache` (`lookup`, `store_proxy`, `proxy`, `store_source_statistics`, `source_statistics`, `mark_complete`; `CacheEntry.complete`, `stages`, `pts_ticks`); IF-8 `Progress` (`report`, `cancelled`), `JobResult`; IF-2 `ArrayBackend` (`asarray`, `device`) injected by the caller. Everything is injected: the engine imports no `clearwater.io`, `.cache`, `.methods`, `.gui`, `.jobs`. |
| Consumers | WP3.18 (progress, cancel, the provisional-to-smoothed switch, `AnalysisState` via `Session.set_analysis`, AD-15), WP3.14 (export reads the smoothed record per pts and checks `schema_hash`; waits for completion, AD-7), WP4.2 (V3, V17 end to end), WP4.3 (wiring). |
| Hardware flags | None timed (question 9); no `gpu` (stub method; the engine runs on whatever backend it is given). `footage` (read only) on the step-aware evaluation only (question 6). |
| Out of scope | Decoding (WP3.9; the stub frame source until then); the method's numerics and the statistics record's content (WP3.4; Y-1 is the shared contract); the cache store itself (WP3.12; consumed); rendering for export (WP3.14) and the GUI (WP3.18); sparse analysis (D109, in reserve); weight-map smoothing (D96); chapter groups and smoothing across files (5.5, v2); changing the smoothing default (owner, question 6); GoPro data (no `gpmd`, IMU or GPS data anywhere). |
| Debt and decided items | **DR-23 — CLOSES for the product:** statistics keyed by pts ticks; every window a time window over pts, never a tap count from a nominal rate (a test on `vid-vfr`'s 1001/1001/2002-tick durations). **DR-25 — CLOSES for the product's store and smoother, items (1), (2) store side, (4)-(7):** (1) every `put` checked against the stage's full name set; (2) and (5) every supplied array checked (shape fixed per name, finite) whether or not later used, the method side per Y-2; (4) `schema_hash` binds the method, the parameters that shaped the stage and the smoother (question 5), and a mismatched record is refused; (6) a NaN refused at `put`, before any later stage; (7) windows taken as exact decimals (`Fraction(str(window_s))` or equivalent), so 2.0 s at 30000/1001 is exact; (3) not this package's (AD-3: the default is confirmed at WP5.2), though the step-aware evaluation records its excerpt length and edge-free frame count. The entry stays OPEN for the prototype instrument unless CHARC closes it at the accept. **AD-5 as ruled — IMPLEMENTS:** every statistic measured on the proxy AS STORED, at first analysis too (`store_proxy`, then `proxy` read back, before any `analyze`; WP3.12 consumer note). **IF-7 amended — IMPLEMENTS:** `source_statistics` for a `source_only` stage, `mark_complete` after the whole decode pass, the decode pass skipped only when `CacheEntry.complete`. **IF-4 `schema_hash` — IMPLEMENTS** (question 5). **7.2 smoothing default — IMPLEMENTS** 2.0 s `median_gaussian`, PROVISIONAL, with the step-aware design task (question 6). **Spec 7.2 line 325** ("Smoothing spans chapter boundaries within a consecutive recording group and resets at breaks (Section 5.5)") — READ AS single-clip: every input file is its own clip in v1 (5.5), so smoothing spans the clip and never resets (CHARC: owner's next-revision list). **D98 — IMPLEMENTS:** a one-stage method runs (test). **AD-15 — feeds** the shell's state (phase and progress), never decides it. **DR-41 — must not reopen:** the engine passes no non-registered codec to `DiskProxyCache`. DR-44 (a) is WP3.18's; DR-28 is the export engine's. |
| Done | Plan 4.5; frame section 2 rules 1-11; ruff check, ruff format --check, mypy strict, full pytest green (in a granted window); V3 and V18's engine side shown by named tests; DR-23 and DR-25's product items shown by tests; the step-aware evaluation recorded in the report; Reviewer A converged. |

## Task ladder

1. **Round 0 yield: the design table.** Before product code, write in the ledger: the engine
   API (names and signatures) and its threading model; the proxy rule and quantisation
   (question 3); the store layout and the `put` checks (DR-25); the smoother over pts for CFR
   and VFR (the median and the Gaussian as time windows, edge rule, D95); the staged pass order
   with the cache reads (task 4); the recompute scheme with its cumulative reach (task 6); the
   `schema_hash` definition (question 5); the provisional path (question 4); cancel and the
   states; the step-aware candidates and the evaluation plan (question 6); and the answers to Y-1,
   Y-2 and questions 3-9. YIELD for the dispatcher. Anything the table cannot settle is a STOP.
2. **Proxy (AD-5).** From each full decoded `Frame`: the block mean by the factor
   `max(1, min(H, W) // 540)` (question 3), quantised to uint8 by the round-0 rule, stored with
   `store_proxy(key, frame.pts_ticks, proxy)`, then READ BACK with `proxy(key, pts_ticks)`; only
   the read-back array, as float32 `/ 255` on the injected backend, is ever measured. A shape
   change within a clip is refused (the cache refuses it too).
3. **Decode pass (7.2 item 1, D70, D86).** `VideoSource.frames(probe, hw_decode=...)` once;
   progress `(done, total)` with `total = probe.video.nb_frames` or None; cancel checked between
   frames; the source stopping early at a truncated file's readable end is not an error (D86);
   `mark_complete(key)` only after the last frame's proxy is stored (and never after a cancel or
   a failure). On reopen, `lookup(key)` with `complete` True skips the decode pass and reads
   proxies by `entry.pts_ticks` (V17's analysis side). Stage 1 of a `source_only` stage may be
   measured in the decode pass and stored with `store_source_statistics`; on reopen it is read
   back with `source_statistics` when `entry.stages` lists it (Y-1 (e)).
4. **Staged statistics (7.2 item 2, D97, D57).** For each stage in `method.stages` order: for
   every pts, `analyze(stage, proxy_image, params, earlier)` with `earlier` the SMOOTHED records
   of the earlier stages at that pts; `put` the raw record; then `smooth(stage, stage.smoothed,
   window_s, kind)`. Proxies are re-read from the cache for each stage pass; the clip's proxies
   are never all held in memory (N4: a 60-minute 4K clip is about 107,892 proxies).
5. **Smoothing (AD-3, D95, DR-23).** `median_gaussian` as a time-window filter over pts: the
   median over the frames within ±0.05 s (the prototype's `MEDIAN_WINDOW_S = 0.1`, 3 frames at
   30 fps), then a Gaussian whose weights are taken from each neighbour's time offset and fall
   to 1 % at half the window (`GAUSSIAN_FALLOFF`), normalised; the end value held past the ends
   (`EDGE_MODE = "nearest"`). On a CFR series it equals `prototype.temporal.Smoother(
   "median_gaussian", 2.0).apply` within 1e-12 (measured, reported). One clip, no resets (line
   325 read as single-clip).
6. **Recompute after a parameter change (7.3, AD-7).** The first invalidated stage is the first
   whose `depends_on_parameters` contains a changed name, or which depends on an invalidated
   stage; a stage with a non-None `closed_form` is updated from its stored measured record
   without touching the proxy (Y-1 (d)); then the stages from there are re-measured, first for
   the frames within the displayed pts's CUMULATIVE reach (each stage's reach adds up: WP1.4b
   claim 10b, "29 frames per stage, so 58 frames for c3 and 87 (2.9 s) for Ancuti's three
   stages"; the median's own reach included), then the rest of the clip in the background. The
   engine reports "complete" only when every stage under the current parameters is smoothed for
   every pts; export waits for that (AD-7, AD-15).
7. **Provisional statistics (D108, V18; question 4).** For a pts whose proxy is stored, the
   frame's own chain: each stage measured with that frame's own unsmoothed earlier records, as
   `clearwater.gui.imaging.measure_statistics` does; the switch to the smoothed record is
   signalled by the state (task 8).
8. **State and cancel (AD-15, D70).** Phases matching `gui.contract.AnalysisPhase`
   (`none`, `running`, `complete`, `cancelled`, `failed`) with `done`, `total`, `message`;
   cancel stops within one frame, leaves the cache entry incomplete, drops the in-memory
   statistics and returns to the unloaded state (7.2); a failure carries its message.
9. **Step-aware design task (AD-3; question 6).** Implement the candidate variant(s) as extra
   `kind` values of the store's `smooth`; evaluate them on the deep excerpt of WP1.4b claim 10b
   (GX011600, the step at "0.90 s into the excerpt (pts 662.962 s)") against `median_gaussian`
   2.0 s: the rendered step size and the flicker away from the step; figures in the report. The
   default does not change here.
10. **Tests.**
    - IF-4 conformance (`isinstance(store, StatisticsStore)`, a mypy assignment as in
      `stubs.py`); `put` refuses a missing or extra name, a shape change, a NaN (DR-25 (1),
      (2), (6)); `invalidate_from` drops the stage and every later one.
    - Smoothing: CFR equality with the prototype; a VFR series (`vid-vfr` durations, or a
      synthetic one) smoothed by time, a planted "taps from the nominal rate" fails (DR-23);
      2.0 s at 30000/1001 exact (DR-25 (7)); one clip, no reset.
    - Staged order: stage 2 measured with stage 1's SMOOTHED records (a planted "raw earlier"
      fails); a one-stage method (D98).
    - AD-5: no statistic is ever measured on the pre-store proxy (a planted float-proxy
      measurement fails with a lossy test codec through `DiskProxyCache` under `tmp_path`).
    - V17 analysis side: a complete entry skips the decode pass (the frame source is never
      iterated); an incomplete one does not; `mark_complete` never after cancel; a
      `source_only` stage read back through `source_statistics`.
    - Recompute: a parameter of stage 2 leaves stage 1 untouched; a closed-form stage never
      reads a proxy; the near-frame set covers the cumulative reach (a planted single-stage
      reach fails); "complete" only after the background part.
    - V3 per question 7 on `ad14-flicker` / `ad14-mask`; V18 engine side: provisional
      statistics available for a frame before the analysis completes, smoothed afterwards.
    - Cancel within one frame; the phases; a failing `analyze` gives `failed` with its message.
    - `schema_hash` changes with each shaping parameter and with the smoother, not with a
      parameter no stage depends on; a record of another hash is refused (DR-25 (4)).
    - Threads: one analysis thread writing while reader threads call `smoothed` and the state.
    - Dependency rule (plan 8.1, frame rule 5): importing `clearwater.analysis` loads nothing
      from `clearwater.gui`, `.jobs`, `.io`, `.methods`, `.cache`, nor `PySide6`, `cupy`, `PIL`.

## Declared operating envelope

Windows 11; Python 3.12; one clip at a time per engine; clips from a few frames to 60 minutes
at 4K 29.97 fps (about 107,892 frames; the statistics series in memory, the proxies in the
cache); CFR and VFR timestamps; one analysis writer thread with preview readers on other
threads of the same process; the cache folder as WP3.12's envelope. Out of envelope: two
engines on one cache key at once (the cache refuses it, `RuntimeError`); a frame source that
returns frames out of pts order or with duplicate pts (refused by name); chapter groups (v2);
other operating systems (portable, N1, not run there).

## Review loop (Reviewer A), per `docs/review-gate-clearwater.md` Part 1

- Tier **STRONG**, run by you at your seat to convergence; five-round gate. Evidence
  `C:\Users\rwsmy\clearwater-review-evidence\wp3.11\rN\`; ledger `docs/proofs/wp3.11-ledger.md`.
  Copy the runner and prompt shape from `C:\Users\rwsmy\clearwater-review-evidence\wp3.1\r2\`
  (`run_review.sh`, `review-prompt.md`; the round also keeps `probe.txt`, `review-diff.txt`,
  `review.txt`, `adjudication.md`, `md5sums.txt`, `test-summary.txt` as there); the reviewer
  excludes `docs/proofs` with `--glob '!docs/proofs/**'`.
- **WHAT TO EXAMINE:**
  - each stage measured on the stored proxy with the SMOOTHED earlier stages; nothing measured
    on a float or pre-store proxy;
  - smoothing over pts in seconds on CFR and VFR; edges; exact windows; no reset in a clip;
  - recompute: the first invalidated stage right; the cumulative reach right; closed form
    without proxy reads; "complete" never early; export's wait (AD-7, AD-15);
  - the cache contract: `mark_complete` only after a whole pass, never after cancel; the
    decode pass skipped only on `complete`; `source_statistics` use;
  - the store's checks (DR-25) and `schema_hash`; thread safety; cancel;
  - nothing outside the owned files changed; no import of `io`, `cache`, `methods`, `gui`.
- Reviewer B is the orchestrator's seat pass on the merge candidate.

## Notes for the cell

- **Yields.** Round 0: read and table, then YIELD before product code. After each review
  round: END YOUR TURN as soon as round N's verdict is adjudicated, BEFORE remediating; make NO
  change in the turn that adjudicates a round. Report `scripts/cell_depth.py`'s reading at
  every yield (~250K evaluation point; past it, "REVIEW ONLY this turn"; ~400K STOP).
- **Windows.** Full pytest (about 3559 tests, about 15 min) runs ONLY in a window the
  dispatcher grants by message, in the background with `QT_QPA_PLATFORM=offscreen` and output
  to a file under `work/`; send `WINDOW RELEASED: <summary>` when it finishes. Never two heavy
  jobs at once; the step-aware evaluation's footage run is heavy: ask for a window. Inner loops
  run only your own tests.
- **Return report** = your FINAL message, under about 70 lines (`docs/dispatch-recipe.md`
  section 4): the public API, the threading model, the proxy rule, the smoother definition and
  its prototype agreement, the recompute scheme with its reach, the `schema_hash` definition,
  the V3 and V18 results, the step-aware table, the debt dispositions, the gates, the
  Reviewer A rounds and verdict, open items.
- **STOP for:** any change needed in `src/clearwater/interfaces/` (AD-20); a need to import
  `clearwater.gui`, `.cache`, `.methods` or `.io` from `src/clearwater/analysis`; a dependency
  (none is granted); OS-specific code; a statistic you can only measure on a pre-store proxy;
  a contract question Y-1 does not settle when WP3.4's methods arrive; changing the smoothing
  default; any write to the footage folder; the round-0 table showing a choice the brief left
  open.
- **Working rules:** `uv sync`. Commit inside the worktree with `git -c core.autocrlf=false`,
  by pathspec, `feat(wp3.11): ...`, with a `Co-Authored-By:` footer naming your model. NEVER
  `git stash` (the stash stack is shared by every worktree; use a WIP commit or a scratch
  copy). Never a bare `cd`. Never post to a mailbox. Gates: ruff check, ruff format --check,
  mypy strict, full pytest (in a window); no harness gate. Report
  `docs/reports/wp3.11-analysis.md` (claims, evidence paths, limits, a "Consumer notes" section
  for WP3.14, WP3.18 and WP4.2, and the step-aware table). Instrument outputs under
  `work/wp3.11/`. Footage read only through `tools/local_config.find_footage_file`. No `gpmd`,
  IMU or GPS data.

## Questions for CHARC (recommended answer first)

1. **Y-1 (cross-brief, WP3.4 and WP3.11): the statistics contract.** IF-3 fixes the signatures,
   not what a record holds or who calls `closed_form`. Recommended (identical text in WP3.4's
   brief): (a) `analyze` returns every name of the stage's `Stage.statistics` for that frame,
   render-ready (as `clearwater.gui.imaging.measure_statistics` on main already relies on), as
   float64 host arrays of a fixed shape per name; (b) white balance `gains` are the gray-world
   gains BEFORE the strength and the D99 clamp (the prototype `Statistics.white_balance_gains`;
   WP3.2 consumer note "`applied_gains` takes the smoothed gray-world gains"); strength and clamp
   are applied inside `render` and inside later stages' `analyze`, after smoothing (AD-6), which
   is why the frozen `C3_STAGES` lists them only under `fusion`; (c) Ancuti `alpha` is the
   capped alpha per frame, smoothed as a value (AD-6, WP1.4b claim 10); (d) `closed_form`
   returns the full record with every parameter-dependent name recomputed from the measured
   names, or None when the stage's measurement depends on parameters or earlier stages: in v1
   non-None only for Ancuti `compensation`; (e) Ancuti `compensation` is the only `source_only`
   stage; the engine caches the record `analyze` returned and never uses a cached record without
   passing it through `closed_form` with the current parameters. Alternative for (e), if D113
   ("the cache holds only results that depend on the source file alone") is read strictly
   against a cached alpha: an AD-20 amendment adding a `Stage` field naming the measured
   (cacheable) statistics.
2. **Y-2 (cross-brief, WP3.4 and WP3.11): validating records (DR-25 (2), (5)).** Recommended:
   the store refuses at `put` a record that lacks a declared name, carries an extra one, changes
   a name's shape within the clip, or holds a non-finite value (one ValueError naming the pts,
   stage and statistic); the method's `render` and `analyze` check supplied records on their
   side (WP3.4).
3. **The proxy rule's owner.** CHARC's S3 ruling made `clearwater.gui.imaging` "the one owner"
   of the block-mean rule and `statistics_factor`, but `clearwater.analysis` may not import
   `gui`. Recommended: `clearwater.analysis` implements the same rule (block mean, `ceil` edge
   blocks, factor `max(1, min(H, W) // 540)`: 960 x 540 at 4K) and a test asserts equality with
   `gui.imaging.downscale` and `statistics_factor` on several sizes; consolidation into one
   lower module is WP4.3's. Quantisation: `floor(x * 255 + 0.5)` clipped to [0, 255] (round
   half up), which on 8-bit-derived frames reproduces the 8-bit proxy of WP3.12's measured test
   (`tools/cache_store_test.py` `block_proxy`: "`floor((block sum + 8) / 16)` (round half up of
   the block mean)").
4. **Who supplies provisional statistics.** The shell already measures a frame's own chain on
   the full image's statistics proxy (WP3.16, D108). Recommended: the engine also offers the
   provisional record for any pts whose proxy is stored, measured on the STORED proxy (AD-5),
   so the provisional and the smoothed statistics come from the same pixels; WP3.18 chooses
   which to use before the frame is in the cache.
5. **`schema_hash` (IF-4: "The method id and the parameters that shaped the statistics (DR-25
   erratum)").** Recommended: a SHA-256 hex digest over canonical JSON of the method id, the
   values of every parameter named in any stage's `depends_on_parameters` (sorted by name), the
   smoothing kind and the window as an exact decimal string; a helper computes it from (method,
   params, kind, window) so WP3.14 and WP3.18 can compare before rendering; the store refuses a
   `put` or a read under another hash.
6. **The step-aware design task (AD-3).** Recommended: candidates as extra `kind` values (for
   example a median-gaussian whose Gaussian weights are cut where the luma or a statistic jumps
   beyond a threshold); evaluation by an owned instrument `tools/step_aware_eval.py` that reuses
   the read-only prototype's measure and render on the WP1.4b claim 10b excerpt (GX011600 around
   pts 662.962 s, at least 182 frames so the figures are not boundary-affected, DR-25 (3)),
   outputs under `work/wp3.11/`, figures (rendered step size, flicker away from the step) in the
   report. The default stays `median_gaussian` 2.0 s: a change of default is a spec 7.2 change
   (owner) at CP5 / WP5.2, not this package's.
7. **V3 without the real method.** The stub method has no whole-frame statistics, so V3 cannot
   be shown with it. Recommended: a test-local method double with real whole-frame statistics
   (gray-world means and gains on the proxy, rendered as gains) runs the engine on `ad14-flicker`
   and measures in `ad14-mask` both V3's criterion ("flicker with smoothing ≤ 25% of flicker
   with per-frame (unsmoothed) statistics") and AD-14's (under 0.5/255); the product-method V3 is
   WP4.2's (plan section 7: V3 "WP3.11, WP4.2"). Alternative: a test adapter over the read-only
   prototype pipeline.
8. **Recompute API.** Recommended: `set_parameters(params, around_pts)` cancels the running
   recompute, applies closed forms at once, re-measures the near frames first (cumulative reach
   of task 6) and the rest in the background, and publishes "complete" only at the end; the
   preview reads whatever is smoothed (the near frames' smoothed values are final only once
   their whole reach is re-measured, so they are published then).
9. **No timing here.** Recommended: no EXCLUSIVE window; the analysis-pass throughput (7.2
   "Analysis speed", D109) is recorded with the real decode and method at WP4.2 / WP5.2. The
   proxy block mean of a 4K frame on the host is a known cost, stated as a limit.
