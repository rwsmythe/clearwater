# WP3.11 ledger -- analysis engine

Cell: `implementer-opus-high`, worktree `.worktrees/wp3.11`, branch `wp3.11`, base `de206e2`.
Tier STRONG. Brief `docs/briefs/wp3.11-brief.md` (FINAL; CHARC rulings `53d1d906e47fe2c9`).

## Cumulative round ledger

| Round | Depth (dispatcher) | Critical | Major | Minor | In / out of envelope | NEW / REOPENED | Reverts | Fixes: product / test-only | Transport, CLI | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 (design table) | (dispatcher) | - | - | - | - | - | - | - | - | yielded for ruling |

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
