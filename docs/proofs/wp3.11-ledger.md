# WP3.11 ledger -- analysis engine

Cell: `implementer-opus-high`, worktree `.worktrees/wp3.11`, branch `wp3.11`, base `de206e2`.
Tier STRONG. Brief `docs/briefs/wp3.11-brief.md` (FINAL; CHARC rulings `53d1d906e47fe2c9`).

## Cumulative round ledger

| Round | Depth (dispatcher) | Critical | Major | Minor | In / out of envelope | NEW / REOPENED | Reverts | Fixes: product / test-only | Transport, CLI | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 (design table) | 143,868 | - | - | - | - | - | - | - | - | APPROVED as written (orchestrator round-0 rulings: P1, P2, choices 1-10) |
| 1 (head 00b248b) | 316,506 (at the window yield; the R1 yield's figure is the dispatcher's) | 0 | 3 (F1, F2, F5) | 5 (F3, F4, F6, F7, F8) | 8 in / 0 out | 8 NEW / 0 REOPENED | 0 | F5 test-only, fixed out of band at 9c53134; F1-F4, F6 product; F7, F8 tool -- NOT yet fixed | WSL, gpt-5.6-sol high, 19 exec lines, all findings REASONED | NEW_CRITICAL_MAJOR_FOUND; adjudicated (F3, F4 downgraded to MINOR), next round needed |
| R1 remediation (cell 2, head e327954) | 171,115 (dispatcher, at the remediation yield) | - | - | - | - | - | 0 | F1-F4, F6 product; F7, F8 tool; V3-1 test-only | - | remediated; step-aware re-run in a window |
| 2 (head 7c8e6ed) | 202,325 | 0 | 1 NEW (A1) + 1 REOPENED (A2, F1's "during" half; MINOR recommended) | 0 (A2 if downgraded) | 2 in / 0 out | 1 NEW / 1 REOPENED | 0 | none yet (both product) | WSL, gpt-5.6-sol high, 14 exec lines, both REASONED by the reviewer, both reproduced by the cell | NEW_CRITICAL_MAJOR_FOUND; adjudicated, next round needed |
| 3 (head 7f9dff8) | 237,310 | 0 | 0 | 1 (B1, docstring) | 1 in / 0 out | 1 NEW / 0 REOPENED | 0 | R2 fixes: A1, A2 product (f139ef5, 7f9dff8); B1 not yet (docstring) | WSL, gpt-5.6-sol high, 17 exec lines, REASONED | NO_NEW_CRITICAL_MAJOR: CONVERGED (zero new blocking) |

## Round 0 -- design table (no product code yet)

Grounded on main `de206e2`: `interfaces/statistics.py` (IF-4), `interfaces/method.py` (IF-3),
`interfaces/cache.py` (IF-7), `interfaces/stubs.py`, `interfaces/backend.py` (`name`, `device`,
`asarray`, `to_host`), `gui/contract.py` (`AnalysisPhase`, `AnalysisState`, `JobRunner.run`),
`gui/imaging.py` (`downscale`, `statistics_factor`, `measure_statistics`), `gui/jobs.py` (an
exception in a job becomes `JobResult(ok=False, failure="<Type>: <text>")`),
`docs/reports/wp3.12-proxy-cache.md` (public API, consumer notes), `tools/prototype/temporal.py`
(`half_width`, `Smoother`), the manifest entries `ad14-flicker` (90 frames, 30000/1001, ffv1,
generated) and `vid-vfr` (30 frames, 1001/1001/2002 ticks at 1/30000). Importing
`clearwater.interfaces` loads none of gui, io, cache, methods, jobs, core, PySide6, cupy, PIL,
scipy (checked).

### R0-1 Modules (all NEW, all owned)

| File | Holds |
|---|---|
| `src/clearwater/analysis/__init__.py` | the public names below |
| `src/clearwater/analysis/proxy.py` | `PROXY_SHORT_SIDE = 540`, `proxy_factor(h, w)`, `block_mean(pixels, k)` (float64), `make_proxy(pixels) -> uint8`, `proxy_image(proxy, backend, color, orientation_applied) -> Image` |
| `src/clearwater/analysis/smoothing.py` | `DEFAULT_KIND = "median_gaussian"`, `DEFAULT_WINDOW_S = 2.0`, `MEDIAN_WINDOW_S = Fraction(1, 10)`, `GAUSSIAN_FALLOFF = 0.01`, `KINDS`, `exact_window(window_s) -> Fraction`, `smooth_series(ticks, time_base, values, window_s, kind, out_index=None)`, `reach(ticks, time_base, window_s, kind, lo, hi) -> (lo', hi')`; step-aware kinds (task 9) |
| `src/clearwater/analysis/store.py` | `AnalysisStore` (IF-4), `SchemaMismatchError(ValueError)`, `schema_hash(method, params, kind, window_s)` |
| `src/clearwater/analysis/engine.py` | `AnalysisEngine`, `AnalysisSnapshot` |
| `tests/test_analysis_proxy.py`, `_smoothing.py`, `_store.py`, `_engine.py`, `_recompute.py`, `_v3.py`, `_deps.py` | the roster of task 10 |
| `tools/step_aware_eval.py` | the step-aware evaluation (task 9) |
| `docs/reports/wp3.11-analysis.md`, `docs/proofs/wp3.11-ledger.md` | report, this ledger |

Imports in `src/clearwater/analysis`: stdlib, NumPy, `clearwater.interfaces` only (no SciPy
needed: the filters run over irregular pts, so they are written directly in NumPy).

### R0-2 Engine API and threading model

```python
@dataclass(frozen=True)
class AnalysisSnapshot:            # the field names of gui.contract.AnalysisState, gui not imported
    phase: Literal["none", "running", "complete", "cancelled", "failed"] = "none"
    done: int = 0
    total: int | None = None
    message: str = ""

class AnalysisEngine:
    def __init__(self, *, method: CorrectionMethod, backend: ArrayBackend, cache: ProxyCache,
                 key: CacheKey, source: VideoSource, probe: ProbeResult,
                 params: Mapping[str, Any], window_s: float = DEFAULT_WINDOW_S,
                 kind: str = DEFAULT_KIND, hw_decode: bool = False) -> None
    store: AnalysisStore                     # read-only property (IF-4)
    schema_hash: str                         # read-only property: the CURRENT parameters' hash
    def state(self) -> AnalysisSnapshot
    def analysis_job(self) -> Callable[[Progress], JobResult]
    def set_parameters(self, params: Mapping[str, Any], around_pts: int | None
                       ) -> Callable[[Progress], JobResult] | None
    def cancel(self) -> None
    def is_complete(self) -> bool
    def smoothed_record(self, pts_ticks: int, *, schema_hash: str | None = None
                        ) -> dict[str, Statistics]      # every stage; KeyError while not final
    def provisional_record(self, pts_ticks: int) -> dict[str, Statistics] | None
```

- **One writer at a time.** Every job returned by the engine runs the whole state machine to
  "complete" from whatever state exists (decode pass if the entry is not complete, then every
  stage not valid under the current parameters). Only one job runs at a time: `analysis_job()`
  while a job runs is a `RuntimeError`.
- **A parameter change during a running job is absorbed by that job** (no superseded job
  results): `set_parameters` records the new values under the engine lock and bumps a
  generation; the running job sees it at its next frame boundary, invalidates from the first
  invalidated stage and restarts its stage loop near-first. `set_parameters` returns a NEW job
  only when no job is running (and the change touches some stage); it returns None when the
  running job absorbs it or no stage depends on a changed name. The end-of-job check and
  `set_parameters` take the same lock, so a change racing the end is never lost.
- **Readers on any thread:** `state`, `is_complete`, `smoothed_record`, `provisional_record`,
  and the store's readers. The store and the engine each guard their mutable state with a lock;
  readers get copies. Cache WRITES (`store_proxy`, `store_source_statistics`, `mark_complete`)
  happen only on the job thread (WP3.12: overlapping store calls are a `RuntimeError`); cache
  READS (`proxy`, `lookup`) may come from readers too (WP3.12: readers unaffected).
- `provisional_record` measures on the caller's thread with the injected backend (limit: a
  CuPy backend is then used from two threads).

### R0-3 Proxy rule and quantisation (question 3, ruled: a twin with an equality test)

- `proxy_factor(h, w) = max(1, min(h, w) // 540)`; `block_mean(pixels, k)`: the S3 block mean
  with `ceil` edge blocks, summed in float64 exactly as `gui.imaging.downscale` does, but
  returned in float64 BEFORE the float32 cast. Tests assert
  `block_mean(p, k).astype(float32) == gui.imaging.downscale(p, k)` bit for bit and
  `proxy_factor == gui.imaging.statistics_factor`, on 2160x3840, 2988x5312 (5.3K),
  3024x4032, 540x960, 541x961, 1x1, odd sizes.
- Quantisation: `clip(floor(mean64 * 255 + 0.5), 0, 255).astype(uint8)` on the FLOAT64 mean.
- **PREMISE (Q3) -- reproduced:** quantising the float32 result of `gui.imaging.downscale` in
  float64 does NOT reproduce WP3.12's `floor((block sum + 8) / 16)` on 8-bit data: on 200
  random 64x64x3 8-bit frames at k = 4, 4,707 of the 9,558 exact-tie cells differ by one level;
  on the float64 mean, 0 differ (seconds to rerun:
  `C:\Users\rwsmy\clearwater-review-evidence\wp3.11\r0\q3_quantisation_repro.py`). So the rule
  binds to the float64 mean; a test asserts equality with the integer rule on 8-bit-derived frames.
- Host side: `pixels = backend.to_host(frame.pixels)` when `frame.device != "cpu"`, else
  `np.asarray`. The proxy Image: `backend.asarray(proxy_readback / 255, float32)` with the
  frame's `color` and `orientation_applied`, `device = backend.device`.

### R0-4 Store layout and the `put` checks (DR-25 (1), (2), (5), (6); Y-2)

- `AnalysisStore(stages: Sequence[Stage], schema_hash: str)`. Columnar: one pts axis (ascending
  `int` ticks, a dict pts -> row), and per (stage, name) a float64 array `(capacity, *shape)`
  grown by doubling, plus per stage a "raw present" and a "smoothed present" boolean column.
  108k frames x a few dozen floats per stage stays in megabytes.
- `put(pts, stage, raw, *, schema_hash=None)`, ONE `ValueError` naming pts, stage and statistic
  for: unknown stage; a missing or an extra name against `Stage.statistics`; a non-numeric or
  complex dtype (or a non-host array); a shape different from that name's first shape in this
  clip (shapes survive `invalidate_from`); any non-finite value. A new pts must be greater than
  every pts on the axis (out-of-order / duplicate frames are refused by name, envelope); a put
  for a pts already on the axis is allowed in any order (the recompute's near-first puts).
  Values are stored as float64 copies. `schema_hash` given and different from the store's:
  `SchemaMismatchError`.
- `raw` / `smoothed(pts, stage, *, schema_hash=None)`: copies; `KeyError` when absent;
  `SchemaMismatchError` on a hash mismatch. The keyword-only extension keeps IF-4 conformance
  (mypy accepts an implementation with extra optional keyword parameters); IF-4 is unchanged.
- `smoothed` record = every name of the stage: the smoothed names smoothed, the others copied
  from raw.
- `smooth(stage, names, window_s, kind)`: every pts on the axis must hold a raw record of the
  stage (else `KeyError` naming the first missing pts); `names` must be a subset of the stage's
  statistics; unknown `kind` is a `ValueError`. Extra `smooth_at(stage, names, window_s, kind,
  pts)`: computes only the given outputs, refusing when any raw record their windows reach is
  missing (the recompute's near phase).
- `invalidate_from(stage)`: drops raw and smoothed of the stage and every later one; the pts
  axis stays (it is the clip's frame list). `all_pts()` = every pts holding at least one raw
  record (as the stub); `pts_range()` from it, `ValueError` when empty (as the stub).
- `schema_hash`: a property with a setter (the protocol attribute is settable, so a read-only
  property would fail the mypy conformance assignment); only the engine sets it.

### R0-5 The smoother over pts (AD-3, D95, DR-23, DR-25 (7))

- Times are exact: `dt = (ticks_j - ticks_i) * time_base` compared with exact `Fraction`
  half-windows; `exact_window(w) = Fraction(str(w))` (2.0 -> 2, 0.1 -> 1/10), refusing a
  negative or non-finite window.
- `median_gaussian`: (1) running median over the samples with `|dt| <= 1/20 s`
  (`MEDIAN_WINDOW_S / 2`); (2) Gaussian over the samples with `|dt| <= window/2`, weight
  `exp(-dt^2 / (2 s^2))`, `s = (window/2) / sqrt(2 ln 100)` (1 % at half the window), weights
  normalised per output; a window shorter than the gap to every neighbour is the identity.
- **Edge rule (a choice the brief left to the table):** past each end, VIRTUAL samples holding
  the end value at the end's own spacing (`t_last + k * (t_last - t_prev)`, the same at the
  start), as many as the window reaches. On a CFR series this reproduces SciPy's
  `mode="nearest"` exactly, for any series length (scipy pads indefinitely; a mirror-of-pts rule
  would fail on a series shorter than the window). A one-frame series is the identity.
- **Even sample counts** in the median on VFR (a neighbour on one side only; `vid-vfr`'s 2002-tick
  gaps are 0.0667 s > 0.05 s): `np.median` (the mean of the two middle values). Stated choice.
- Equality: on CFR 30000/1001 (and 30, 25, 60) `smooth_series` equals
  `prototype.temporal.Smoother("median_gaussian", 2.0).apply` within 1e-12, measured and
  reported. VFR test on `vid-vfr`'s durations: smoothed by time; a planted "taps from the
  nominal rate" smoother (fixed kernel at 22500/1001) differs and the test fails it.
- Memory: the filter loops over neighbour offsets accumulating `(n, m)` sums (never an
  `(n, taps, m)` cube); the median is computed in chunks of frames.
- One clip, no resets (spec 7.2 line 325 read as single-clip).

### R0-6 Staged pass order and cache reads (tasks 3, 4)

1. `lookup(key)`. Complete -> skip the decode pass; the pts list is `entry.pts_ticks`.
   Otherwise the DECODE PASS: `source.frames(probe, hw_decode=...)` once; per frame: refuse
   pts not strictly ascending and a proxy shape change (ValueError by name); `make_proxy`;
   `store_proxy`; `proxy()` READ BACK; stage 1 measured on the read-back proxy (stage 1 has no
   earlier stage, so it needs no smoothing first) and `put`; when stage 1 is `source_only`,
   `store_source_statistics(key, stage1, pts, record)` too. Cancel/generation checked between
   frames. A source that ends early (D86) is not an error; zero frames is a failure ("the
   source yielded no frames"). `mark_complete(key)` after the last proxy, never after a cancel
   or a failure.
2. Reopen (complete): stage 1 from the cache when it is `source_only` and `entry.stages`
   lists it: `source_statistics` -> `closed_form(stage, params, {}, measured)` -> `put`; if
   `closed_form` returns None the cached record is not used and stage 1 is re-measured from the
   proxies (Y-1 (d), (e)). Otherwise stage 1 is measured from the proxies.
3. `smooth(stage1, stage1.smoothed, window_s, kind)`.
4. For each later stage in `method.stages` order: for every pts, `proxy(key, pts)` re-read,
   `analyze(stage, proxy_image, params, earlier)` with `earlier` = the SMOOTHED records of ALL
   earlier stages at that pts (as IF-3's docstring and `measure_statistics` do); `put`; then
   `smooth`. Proxies are never all in memory.
5. Phase "complete" when every stage is smoothed for every pts under the current parameters.
- The engine also keeps, per stage, the record `analyze` (or the cache) gave in a columnar
  "measured" table (megabytes), the `measured` argument of `closed_form` (task 6).
- **Progress units (a choice):** `done`/`total` count frame-stage units across the job:
  total = frames x (decode pass + later stages); `total` None while the decode pass runs with
  `nb_frames` None; the message names the pass ("decoding", "stage fusion (2 of 2)",
  "recomputing ..."). The phase is never decided from it (AD-15 feeds the shell).

### R0-7 Recompute scheme and its cumulative reach (task 6, AD-7, question 8)

- First invalidated stage: the first stage, in order, whose `depends_on_parameters` holds a
  name whose value changed (a later stage that depends on it is later by construction, and
  every later stage is recomputed anyway, spec 7.3). No stage affected -> nothing to do; the
  hash and the parameters are still updated (the hash only covers shaping parameters).
- The store's hash is set to the new one and `invalidate_from(first)` runs under the job's
  writer lock; preview reads of the old records then miss (KeyError) and fall back to
  provisional.
- For each stage from the first invalidated one: `closed_form(stage, params, earlier,
  measured)` is tried on the stored measured record; non-None -> that stage is updated for ALL
  pts without reading a proxy ("closed forms at once"), then smoothed; None -> the stage is
  re-measured from the proxies.
- **Near set, exact over the real pts:** with the displayed pts `p`, `R_last = reach({p})`
  and `R_s = reach(R_{s+1})` for earlier invalidated stages, where `reach(set)` is the index
  interval of every raw sample the smoothed values on `set` read (Gaussian half-window, plus the
  median's half-window, on the actual pts). Stage `s` is re-measured on `R_s` first, then
  `smooth_at` computes its smoothed values on `R_{s+1}` (exact there by construction), then
  stage `s+1` on `R_{s+1}`, ... and finally the smoothed values of every stage at `p` are final:
  `smoothed_record(p)` succeeds from then on. Then the background part re-measures the rest of
  each stage (the near frames are not re-measured: their inputs were exact), smooths the whole
  stage, and so on; "complete" only at the end.
- **PREMISE (task 6 / AD-7 figures) -- reproduced:** the brief says "the median's own reach
  included" and quotes WP1.4b claim 10b's "29 frames per stage, so 58 frames for c3 and 87
  (2.9 s) for Ancuti's three stages"; those figures EXCLUDE the median. With it the reach is 30
  per stage: `Smoother("median_gaussian", 2.0).radius(30000/1001) == 30` (`half_width(2.0) =
  29`, `half_width(0.1) = 1`), so 60 for c3 and 90 for three stages; AD-7's "±29 frames" is the
  Gaussian alone. The exact closure above gives 30 / 60 / 90 at 29.97 fps, and the test plants a
  single-stage reach (and a Gaussian-only reach) and fails both.
- `around_pts=None` (nothing displayed): no near phase.
- Later scrubbing does not re-prioritise a running recompute (limit; `set_parameters` again does).

### R0-8 `schema_hash` (question 5)

`schema_hash(method, params, kind, window_s)` = SHA-256 hex of canonical JSON
(`sort_keys=True, separators=(",", ":")`, floats by `repr`) of
`{"method": method.id, "parameters": [[name, present, value], ...], "smoothing": {"kind": kind,
"window_s": str(exact_window(window_s))}}`, the names = the sorted union of every stage's
`depends_on_parameters`; `present` False for a name the mapping lacks (so a missing name and a
`None` cap differ). Module-level, so WP3.14 and WP3.18 compute it before rendering; the store
refuses a `put`, `raw` or `smoothed` given another hash (`SchemaMismatchError`), and
`smoothed_record` likewise.

### R0-9 Provisional path (question 4, D108, V18)

`provisional_record(pts)`: `proxy(key, pts)` (KeyError -> None: not stored yet); every stage
measured in order on that STORED proxy with that frame's own unsmoothed earlier records (as
`gui.imaging.measure_statistics`), under the current parameters. Not stored. The switch to
smoothed is signalled by `smoothed_record(p)` succeeding (near phase) and by the phase
"complete" (whole clip); WP3.18 chooses before the frame is in the cache.

### R0-10 Cancel and the states (task 8, AD-15, D70)

- Phases: `none` (constructed, no job yet) -> `running` -> `complete` / `cancelled` /
  `failed`; a parameter change from `complete` goes back to `running`.
- Cancel (`progress.cancelled()` or `engine.cancel()`), checked between frames: stops within one
  frame, never `mark_complete`, drops every in-memory statistic (store and measured tables
  cleared), phase `cancelled` (the unloaded state: export unavailable, nothing usable), job
  returns `JobResult(ok=False, failure="cancelled")`. A later `analysis_job()` starts again
  (the decode pass reruns unless the entry became complete; re-stored identical proxies are
  skipped by the cache).
- **Cancel during a recompute (a choice):** the same rule (back to the unloaded state, all
  statistics dropped), one rule for AD-15. Alternative: keep the earlier stages.
- Failure: an exception in `analyze`, `closed_form`, the source or the cache -> phase `failed`,
  `message` = `"<Type>: <text>"`, statistics dropped, no `mark_complete`, the job returns
  `JobResult(ok=False, failure=message)` (not re-raised, so the message is the engine's).

### R0-11 Step-aware candidates and the evaluation (question 6, ruled: default unchanged)

- Candidate kinds of the store's `smooth` (each still a time window over pts):
  1. `median_gaussian_cut`: `median_gaussian` whose Gaussian weights are zero across a detected
     step: a step is where the difference of the means over 0.5 s before and after (on the
     median-filtered series) exceeds `k` times the series' robust frame-to-frame noise (MAD);
     weights are cut between the two sides.
  2. `median_bilateral`: `median_gaussian` times a range kernel `exp(-dv^2 / (2 sv^2))` on the
     median-filtered value difference, `sv` from the robust noise (a classic step-preserving
     smoother).
  Thresholds fixed before the run and recorded.
- `tools/step_aware_eval.py` (footage read only via `tools/local_config.find_footage_file`,
  outputs under `work/wp3.11/`): GX011600, an excerpt around pts 662.962 s at least 182 frames
  plus the stage reach on each side (the WP1.4b widened span: 3 s before the original 6 s
  excerpt), proxies at 540, staged analysis per kind with the read-only prototype's `measure`
  and `render` (c3 and ancuti2018), figures: rendered step size (frame means across +-1 s, the
  claim 10b table's form) and flicker away from the step (the prototype's flicker metric on
  frames >= 1 s from the step), excerpt length and edge-free frame count recorded (DR-25 (3)).
  Runs in a dispatcher WINDOW (heavy: footage decode).

### R0-12 Answers to Y-1, Y-2, questions 3-9

- Y-1: as ruled (an IF-3 reading); the report carries ONE text identical to WP3.4's (relayed by
  the dispatcher). The engine relies on (a) render-ready full records, (d) closed form for
  source-only Ancuti `compensation`, (e) cached records always through `closed_form`.
- Y-2: as ruled; the store's checks in R0-4 (one ValueError naming pts, stage, statistic).
- Q3: twin rule + equality tests (R0-3), with the float64 quantisation premise above.
- Q4: R0-9. Q5: R0-8. Q6: R0-11 (default unchanged). Q7: V3 with a test-local gray-world
  double on `ad14-flicker` decoded through FFmpeg in the test (skips without FFmpeg, as the
  `sample` fixture does), flicker inside `ad14-mask`: V3's <= 25 % and AD-14's < 0.5/255.
  Q8: R0-7 with the "absorbed by the running job" refinement in R0-2. Q9: no timing.

### R0-13 Choices the brief left open (for the dispatcher's ruling)

1. Reach figures: 30 per stage at 29.97 fps (60 c3, 90 three stages), the exact closure over
   the real pts (premise R0-7).
2. Quantisation on the float64 block mean (premise R0-3).
3. Edge rule: virtual end samples at the end spacing (R0-5).
4. Median of an even sample count on VFR: the mean of the two middle values (R0-5).
5. A parameter change during a running job is absorbed by it; `set_parameters` returns a job
   only when idle (R0-2).
6. Cancel during a recompute returns to the unloaded state like any cancel (R0-10).
7. Progress in cumulative frame-stage units (R0-6).
8. `earlier` = the smoothed records of ALL earlier stages (R0-6).
9. The store's hash checks as keyword-only extensions of `put`/`raw`/`smoothed` (R0-4).
10. `all_pts` = pts holding at least one raw record; the axis survives `invalidate_from` (R0-4).

## Build findings (before Reviewer A)

### V3-1 -- V3's 25 % ratio is not met on the AD-14 clip by a centred smoother (STOP, reproduced)

`tests/test_analysis_v3.py` runs the engine on `ad14-flicker` (90 frames, decoded by FFmpeg) with
two test-local methods holding real whole-frame statistics, and measures the AD-14 metric (mean
absolute frame-to-frame difference of the corrected output inside `ad14-mask`, in /255):

| Double | Per-frame (provisional) | Smoothed (2.0 s median_gaussian) | Ratio | AD-14 (< 0.5) |
|---|---|---|---|---|
| Gray-world gains | 0.0076 | 0.0042 | 0.55 | met |
| Gains + 0.5/99.5 % luma stretch (c3's two kinds of statistic) | 0.0835 | 0.0533 | 0.64 | met |

Cause: the disc's centre sweeps LINEARLY across the frame (`tools/fixtures/flicker.py`
`disc_centre_x`), so the whole-frame statistics drift smoothly (red gain first differences grow
steadily, e.g. 2e-5 to 9e-5 over 20 frames); a centred filter preserves a smooth trend, so it
cannot take the frame-to-frame change below about half. WP1.4's real-footage figures are also
above 25 % (0.053/0.151 = 0.35 to 0.106/0.236 = 0.45, AD-14's row). AD-14's absolute bound is
met by two orders of magnitude. The two V3-ratio tests are `xfail(strict=True)` pending a ruling.
Reproduction: `uv run pytest tests/test_analysis_v3.py -s` (about 45 s; FFmpeg needed).

**V3-1 premise corrected (orchestrator, 2026-10-21): the metric was AD-14's, not V3's.** V3
(spec 15, line 472ff) measures, in the untouched region of the output, the per-frame mean L*,
a*, b* and a contrast measure, and takes flicker = the standard deviation of the frame-to-frame
differences of each measure. `tests/test_analysis_v3.py` now measures that (CIELAB D65 from the
output read as sRGB; contrast = the standard deviation of L* over the region) alongside AD-14's
figure. Re-measured (`work/t-v3b.log`; 2 passed, 2 xfailed):

| Double | Measure | Per-frame | Smoothed | Ratio |
|---|---|---|---|---|
| Gray-world gains | L* / a* / b* / contrast | 0.002234 / 0.005461 / 0.010578 / 0.000645 | 0.001061 / 0.002444 / 0.005165 / 0.000307 | 0.475 / 0.447 / 0.488 / 0.476 |
| Gains + stretch | L* / a* / b* / contrast | 0.053445 / 0.007161 / 0.008942 / 0.032053 | 0.020678 / 0.003453 / 0.004067 / 0.012821 | 0.387 / 0.482 / 0.455 / 0.400 |

The standard deviation removes the sweep's constant part but not its curvature; V3's 25 % is
still not met (0.39-0.49). V3-1 STANDS with these figures. The test file changed while Reviewer
A round 1 was running (its diff predates the change).

## Round 1 (Reviewer A) -- adjudicated, NOT remediated

Evidence `C:\Users\rwsmy\clearwater-review-evidence\wp3.11\r1\` (prompt, diff, transcript
`review.txt` + `review.stderr.txt`, `test-summary.txt`, `probe.txt`, `adjudication.md`,
`md5sums.txt`). Per-finding adjudication with the fix kind for each: `adjudication.md` there.
Summary: F1 MAJOR (cancel not checked during/after smoothing; "complete" published without a final
cancel check), F2 MAJOR (a cancel raised by the last decode report still reaches `mark_complete`),
F5 MAJOR (V3 metric; fixed at 9c53134, now superseded by the V3-1 ruling); MINOR: F3 (frame-shape
change with an equal proxy shape not refused; message wording), F4 (stale tail proxies of an
incomplete entry marked complete; narrow: needs a non-deterministic re-decode), F6 (reopen
progress double count), F7 (eval flicker reference not the raw mean; result-bearing), F8 (eval
edge-free count per kind).

## CHARC ruling on V3-1 (binding for the next seat; copied verbatim, not yet implemented)

**V3-1 RULED: the RECOMMENDED reading, with four conditions. No spec change; the 25 % threshold is untouched.**

Ground. V3's own text asks for "a moving disturbance (e.g., a colored patch or a brightness ripple)" and defines flicker as the standard deviation of frame-to-frame differences. A steadily swept disc changes the whole-frame statistics along a smooth curve; the differences are nearly constant, their standard deviation is curvature, and a centred smoother is REQUIRED to keep a smooth trend (that is the whole case for 2 s over 0.5 s in WP1.4). So the AD-14 clip measures a trend, not flicker, and failing V3's ratio on it says nothing about smoothing. The clip was designed for AD-14's absolute bound and does that job. Your premise check (metric first) was the right order.

Conditions:
1. **The test-local clip's disturbance must be frequency-agnostic.** A patch whose POSITION is re-drawn at random each frame (uniform within a band in the lower third, fixed size and brightness, seeded) -- white-noise-like in the statistics, so the ratio cannot be tuned to pass by choosing a tone the Gaussian happens to kill (at sigma 0.33 s a 1 Hz tone passes at ~0.12 and a 0.5 Hz tone fails at ~0.58; a single ripple frequency is therefore not sufficient on its own). A ripple MAY be added as a second case; the jittering patch is the asserted one. The measured region is the upper half and a test proves the patch never touches it (the AD-14 mask pattern).
2. **The two V3-ratio tests stop being xfail.** The ad14-flicker tests assert AD-14's bound and RECORD V3's four ratios without asserting them (an xfail that unexpectedly passes is noise, not evidence). The jitter-clip test asserts the 25 % ratio on all four measures (L*, a*, b*, contrast) with V3's metric, for both test-local methods.
3. **Recorded for the owner, not asked now.** The report and the accept record carry the ad14-flicker ratios (0.39-0.49) and the WP1.4 real-footage ratios (0.35-0.45) under one heading, with the cause stated as above. They go on the owner-pending list for CP5 / WP4.2 as INFORMATION under V3's "tunable" clause; V3 on real footage stays V2's (D112). No `decision_request` from this.
4. **Recorded durably:** AD-14 extended by one clause on main (`docs/decisions.md`, main b9f3d09).

Step-aware: read. Default `median_gaussian` 2.0 s stands; both candidates lose on flicker (1.7-5.4x) and the peak step (5-13x) with no gain on the rendered step, which is decisive evidence for WP5.2's table. AD-3 stays PROVISIONAL until then; a change would be spec 7.2 and the owner's. Window CLOSED acknowledged (~07:40Z).

## Round 1 remediation and the V3-1 ruling (cell 2, 2026-10-26, from `e82aa2b`)

One commit per finding, each with a test shown failing on the unfixed code first:

| Finding | Commit | Kind | Test (failure on the unfixed code) |
|---|---|---|---|
| F1 | d62a822 | product | `test_a_cancel_during_the_last_smooth_is_not_published_as_complete` (result ok, phase complete) |
| F2 | 27b6128 | product | `test_a_cancel_at_the_last_decode_report_never_marks_complete` (`marks == 1`) |
| F3 | a4b9752 | product | `test_a_frame_size_change_with_an_equal_proxy_shape_is_refused` (1082/1081 x 1100 frames, both 541 x 550 proxies: no failure) |
| F4 | 4b9650c | product | `test_stale_proxies_of_an_incomplete_entry_are_never_marked_complete` (job ok, stale tail marked complete) |
| F6 | 199fc21 | product | `test_reopen_progress_counts_each_frame_stage_once` (total 90, not 60) |
| F7 | 0f8d769 | tool | `test_the_flicker_reference_is_the_mean_of_the_own_raw_statistics` (reference R mean 0.449686 vs 0.449837); report figures await the footage re-run (WINDOW) |
| F8 | 2e2a09c | tool + report | `test_the_instrument_runs_on_a_synthetic_step` per-kind asserts (`KeyError: 'edge_free_frames'`) |

V3-1 ruling implemented at 5eb6f93: jittering-patch clip built in the test (AD-14 texture at
480 x 270, 90 frames, 60 x 60 patch of the disc's colour, corner re-drawn uniformly in the lower
third each frame, seed 14, all fixed before the first run); V3's 25 % asserted on L*, a*, b*,
contrast for `GrayWorld` (ratios 0.023 / 0.024 / 0.022 / 0.023) and `GainsStretch` (0.017 /
0.024 / 0.023 / 0.018); the patch-never-touches-the-upper-half test; the ad14-flicker tests
assert AD-14 and record the ratios (unchanged: 0.475 / 0.447 / 0.488 / 0.476 and 0.387 / 0.482 /
0.455 / 0.400), no xfail. Run `work/t-v3c.log`: 5 passed, 69 s. Report: V3 section with the one
heading for CP5 / WP4.2 (24e8dcb also brings claims 3 and 9 up to the fixes and adds the DR-45 (a)
consumer note: the engine closes the stream on the job thread, never concurrently).

Gates at 24e8dcb: ruff check, ruff format --check (189 files), mypy strict (113 files) green;
analysis tests without V3 212 passed (`work/t-an.log`), V3 file 5 passed.

## Round 2 (Reviewer A) -- adjudicated, NOT remediated

Evidence `C:\Users\rwsmy\clearwater-review-evidence\wp3.11\r2\` (prompt listing R1's findings to
verify, diff de206e2..7c8e6ed, transcript `review.txt` + `review.stderr.txt`, `test-summary.txt`
(217 passed at 7c8e6ed), `probe.txt`, `probe_r2.py` + `probe_r2.txt` (the cell's reproductions),
`adjudication.md`, `md5sums.txt`). The reviewer reports R1's F1-F8 fixed except F1's "during
smoothing" half.

- A1 MAJOR, NEW, CONFIRMED (executed by the cell): `_drive` re-hashes the store, then
  invalidates; a reader in between is served the OLD records under the NEW schema (DR-25 (4)).
- A2 MAJOR as filed, REOPENED (F1), CONFIRMED; MINOR recommended for the dispatcher: no cancel
  check DURING a stage's whole-series smoothing; measured 0.29-0.72 s per statistic at 107,892
  frames, so a few seconds per stage at the envelope's end; the outcome is right, only the latency
  misses "within one frame".

The step-aware re-run (F7) ran in the granted window before the round: exit 0, the table moved by
at most 0.002 flicker and 0.09 peak (`work/wp3.11/step-aware-f7.log`; report f53a1a2).

## Round 3 (Reviewer A) -- CONVERGED

Evidence `C:\Users\rwsmy\clearwater-review-evidence\wp3.11\r3\` (prompt listing R2's A1, A2 and
R1's findings to verify, diff de206e2..7f9dff8, transcript, `test-summary.txt`, probe,
`adjudication.md`, `md5sums.txt`). No earlier finding reported unfixed or regressed. One MINOR:
B1 `store.py:414` the `axis()` docstring says "every pts ever put", but `ensure_axis` (reopen)
adds pts ahead of their records; CONFIRMED, docstring only, fixed in the terminating round's
cleanup. Zero new blocking: the loop terminates at round 3.

R2 remediation (dispatcher ruled A1 and A2 MAJOR): A1 f139ef5 (invalidate before re-hashing;
test `test_a_reader_never_gets_old_records_under_the_new_schema`, unfixed served/served); A2
7f9dff8 (`SMOOTH_CHUNK` 2048, `_smooth_stage` through `smooth_at` with a cancel check between;
test `test_a_cancel_during_a_stages_smoothing_stops_before_the_stage_ends`, unfixed rows [60, 60];
guard `test_chunked_smoothing_equals_the_whole_series`; the F1 test now hooks `smooth_at` too).
Gates at 7f9dff8: ruff, format, mypy strict green; analysis tests 215 + V3 5 passed (one host
MemoryError in run A while another package's full pytest ran, cleared on the re-run).

## RESUME HERE (cell 2, at the R3 yield, 2026-10-26)

**State.** Head = this ledger commit (code as at 7f9dff8). Reviewer A CONVERGED at round 3.

**Do next, in order.**
1. DONE: B1 cleanup (8b8a9ac, docstring only, no new round); Y-1 reconciled with WP3.4's text
   byte for byte (dispatcher, 478ecab; report commit after 8b8a9ac), report status final.
2. DONE (window granted, d3e3c36, 2026-10-26 16:52-17:15Z): full pytest 3789 passed, 2 skipped,
   1 failed -- `tests/test_gui_startup.py::test_shutdown_stops_every_worker_when_one_overruns_its_timeout`
   (WP3.16's timing test, untouched by this branch: its precondition `_thread.is_alive()` after a
   0.05 s shutdown timeout failed under host load); the file re-run 13 passed and the test alone
   5 of 5 passed (`work/t-full.log`, `work/t-gui.log`). Was: Full pytest in a dispatcher WINDOW (`QT_QPA_PLATFORM=offscreen`, `--basetemp=work/<name>`,
   output to a file; grep the summary); `WINDOW RELEASED: <summary>`.
3. The final return report (recipe section 4; brief "Return report").
