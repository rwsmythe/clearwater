# WP3.11 report: analysis engine

**Spec:** v0.5.4. **Brief:** `docs/briefs/wp3.11-brief.md` (FINAL; CHARC rulings
`53d1d906e47fe2c9`; orchestrator round-0 rulings on P1, P2 and choices 1-10). **Branch:**
`wp3.11` (base `de206e2`). **Module:** `src/clearwater/analysis/` (`proxy.py`, `smoothing.py`,
`store.py`, `engine.py`). **Instrument:** `tools/step_aware_eval.py`. **Ledger:**
`docs/proofs/wp3.11-ledger.md`. **Status:** DRAFT (the step-aware figures and the V3 ruling are
pending; Reviewer A not yet run).

## Public API (`clearwater.analysis`)

| Area | Names |
|---|---|
| Engine | `AnalysisEngine(*, method, backend, cache, key, source, probe, params, window_s=2.0, kind="median_gaussian", hw_decode=False)`; `.store`, `.schema_hash`, `.parameters`, `state() -> AnalysisSnapshot`, `is_complete()`, `analysis_job() -> Callable[[Progress], JobResult]`, `set_parameters(params, around_pts) -> job or None`, `cancel()`, `smoothed_record(pts, *, schema_hash=None)`, `provisional_record(pts)`; `AnalysisSnapshot(phase, done, total, message)` (the fields of `gui.contract.AnalysisState`), `CANCELLED`, `Phase` |
| Store (IF-4) | `AnalysisStore(stages, schema_hash, time_base)`: IF-4 exactly, plus keyword-only `schema_hash=` on `put`/`raw`/`smoothed`, and `smooth_at`, `has_smoothed`, `ensure_axis`, `raw_missing`, `smoothed_complete`, `axis`, `clear`; `SchemaMismatchError(ValueError)`; `schema_hash(method, params, kind, window_s)`, `shaping_parameters(method)` |
| Smoothing | `smooth_series(ticks, time_base, values, window_s, kind, out=None)`, `reach(...)`, `exact_window`, `half_window_ticks`; `DEFAULT_KIND`, `DEFAULT_WINDOW_S` (2.0, PROVISIONAL), `MEDIAN_WINDOW_S` (1/10), `GAUSSIAN_FALLOFF`, `KINDS`, `STEP_AWARE_KINDS` |
| Proxy | `proxy_factor`, `block_mean` (float64), `quantise`, `make_proxy`, `proxy_image`, `frame_pixels_on_host`, `PROXY_SHORT_SIDE` |

Imports: the standard library, NumPy and `clearwater.interfaces` only (test
`tests/test_analysis_deps.py`: a fresh interpreter importing `clearwater.analysis` loads none of
`clearwater.gui/.jobs/.io/.methods/.cache/.core`, PySide6, CuPy, PIL, SciPy).

## Threading model

One writer: the job returned by `analysis_job` or `set_parameters` runs on one worker thread at a
time (a second `analysis_job` while one runs is a `RuntimeError`); it is the only caller of the
cache's store methods (`store_proxy`, `store_source_statistics`, `mark_complete`). Readers on any
thread: `state`, `is_complete`, `smoothed_record`, `provisional_record`, the store's readers; the
engine and the store each hold a lock and return copies. A parameter change while a job runs is
absorbed by that job at its next frame (choice 5): it re-reads the parameters, invalidates from
the first affected stage and restarts its stage loop near-first; `set_parameters` then returns
None. During the decode pass a change is taken up after the pass (the first stage, measured
inline, is re-measured from the stored proxies if the change touches it).

## Claims

| # | Claim | Evidence |
|---|---|---|
| 1 | Proxy (AD-5, Q3, P2): block mean by `max(1, min(H, W) // 540)` with `ceil` edge blocks, kept in float64 and quantised `floor(x * 255 + 0.5)` clipped; its float32 cast equals `gui.imaging.downscale` bit for bit and the factor equals `statistics_factor`; on 8-bit data it equals WP3.12's `floor((sum + 8) / 16)`, which the float32 path misses on about half the exact ties (reproduction `C:\Users\rwsmy\clearwater-review-evidence\wp3.11\r0\q3_quantisation_repro.py`). | `tests/test_analysis_proxy.py` |
| 2 | Every statistic is measured on the proxy AS STORED: `store_proxy` then `proxy` read back, `/ 255` as float32 on the injected backend, at first analysis and on reopen; a lossy codec (`DiskProxyCache`, JPEG q75) shows a planted pre-store measurement would differ. | `test_statistics_are_measured_on_the_stored_proxy` |
| 3 | Decode pass: one iteration of the source; progress; cancel between frames; an early end is not an error (D86); zero frames, out-of-order or duplicate pts and a size change fail by name; `mark_complete` after the last proxy only. A complete entry skips the pass (the source is never iterated) and gives bit-identical statistics (V17 analysis side); an incomplete one does not skip. | `tests/test_analysis_engine.py` |
| 4 | Staged statistics (D97): each later stage measured on the stored proxies with the SMOOTHED records of all earlier stages, then smoothed; a one-stage method runs (D98). | `test_stage_two_is_measured_with_stage_one_smoothed`, `test_a_one_stage_method_runs` |
| 5 | Smoother: `median_gaussian` over pts, exact windows; equals the prototype's `Smoother("median_gaussian", w).apply` within 1e-12 on CFR (5 rates x 5 lengths x 4 windows, including 1- and 2-frame series); on `vid-vfr`'s 1001/1001/2002 durations it equals a direct definition and differs from a planted tap filter (DR-23). | `tests/test_analysis_smoothing.py` |
| 6 | Store checks (DR-25 (1), (2), (4)-(7)): missing or extra name, shape change (also after invalidation), non-finite, non-real dtype refused at `put` with pts, stage and statistic named; hash mismatch refused on put and read; windows `Fraction(str(w))`. | `tests/test_analysis_store.py`, `test_windows_are_exact_decimals` |
| 7 | Recompute (AD-7, P1): first invalidated stage by `depends_on_parameters`; a closed-form stage reads no proxy; near set = the exact closure over the real pts, 30 frames per stage at 29.97 fps (Gaussian 29 + median 1): stage 1 over +-60, stage 2 over +-30 for c3 (+-90 for three stages); the displayed frame's smoothed record is final at the end of the near phase and equals the final one; planted Gaussian-only and single-stage reaches are refused; "complete" only after the background part. AD-7's "+-29" is the Gaussian alone. | `tests/test_analysis_recompute.py` |
| 8 | Provisional (D108, V18 engine side): `provisional_record(pts)` is the frame's own chain on its stored proxy, available while the analysis runs; the smoothed record after. | `test_provisional_statistics_come_before_the_smoothed_ones` |
| 9 | Cancel and states (AD-15, D70): cancel within one frame, no `mark_complete`, statistics dropped, phase `cancelled` (the unloaded state); a failure gives `failed` with `"<Type>: <text>"`. Cancel during a recompute is the same (choice 6); the stored proxies stay in the cache and the entry stays complete, so the re-analysis does not decode again (a cancel DURING the decode pass leaves the entry incomplete, so that re-analysis decodes). | `test_cancel_*`, `test_a_failing_analyze_*` |
| 10 | V3 / AD-14 (Q7): see "V3" below. | `tests/test_analysis_v3.py` |

## The `schema_hash`

SHA-256 hex of canonical JSON (`sort_keys`, compact separators, floats by `repr`, NaN refused) of
`{"method": id, "parameters": [[name, present, value], ...], "smoothing": {"kind": kind,
"window_s": str(Fraction(str(window_s)))}}` over the sorted union of every stage's
`depends_on_parameters`. A parameter no stage depends on leaves it unchanged; a missing name and
`None` differ.

## V3

PENDING the dispatcher's ruling on finding V3-1 (ledger).

## Step-aware design task (AD-3, question 6)

Candidates (`smoothing.STEP_AWARE_KINDS`, thresholds fixed before the run): `median_gaussian_cut`
(Gaussian weights cut across a step: a 0.5 s before/after mean difference that is a local maximum
and exceeds 6 robust noise units, the noise 1.4826 x the MAD of the frame-to-frame differences)
and `median_bilateral` (the Gaussian times a range kernel of width 3 noise units on the
median-filtered values). Table PENDING the windowed footage run. The default stays
`median_gaussian` 2.0 s (spec 7.2; a change is the owner's at CP5 / WP5.2).

## Y-1 (the statistics contract; one text identical to WP3.4's report)

DRAFT, to be reconciled with WP3.4's at the gate. IF-3 fixes the signatures, not what a record
holds or who calls `closed_form`; read as follows (an IF-3 reading, not an amendment). (a)
`analyze` returns every name of the stage's `Stage.statistics` for that frame, render-ready, as
float64 host arrays of a fixed shape per name. (b) White-balance `gains` are the gray-world gains
BEFORE the strength and the D99 clamp; strength and clamp are applied inside `render` and inside
later stages' `analyze`, after smoothing (AD-6). (c) Ancuti `alpha` is the capped alpha per
frame, smoothed as a value (AD-6, WP1.4b claim 10). (d) `closed_form` returns the full record
with every parameter-dependent name recomputed from the measured names, or None when the stage's
measurement depends on parameters or earlier stages: in v1 non-None only for Ancuti
`compensation`. (e) Ancuti `compensation` is the only `source_only` stage; the engine caches the
record `analyze` returned and never uses a cached record without passing it through
`closed_form` with the current parameters.

## Consumer notes

- **WP3.18 (timeline and analysis):** run `engine.analysis_job()` on `JobRunner.run`; map
  `engine.state()` to `AnalysisState(**dataclasses.asdict(...))` for `Session.set_analysis`;
  progress units are cumulative frame-stage units (choice 7). Preview: `smoothed_record(pts)`
  (KeyError while not final) else `provisional_record(pts)` (None while the proxy is not stored;
  then the shell's own D108 path). On a parameter change call `set_parameters(params, displayed
  pts)` and run the returned job if any. AD-15 reads "restart the dependent stages when analysis
  completes"; the engine restarts them in the running job at once, with the same final result.
- **WP3.14 (export):** wait for `is_complete()`; render frame `pts` with
  `smoothed_record(pts, schema_hash=engine.schema_hash)` (or a hash from
  `clearwater.analysis.schema_hash(method, params, kind, window_s)`); a mismatch raises
  `SchemaMismatchError`.
- **WP4.2 (end to end):** V3 with the product method; V17 holds by construction (the same stored
  pixels at first analysis and on reopen).
- **WP4.3 (wiring):** inject `DiskProxyCache` (with its registered codec, DR-41), the key from
  `cache_key`/`key_for`, the IF-5 source and the backend.

## Debt dispositions

- DR-23: closes for the product (pts keys; every window a time window over pts; VFR test).
- DR-25: (1), (2), (4)-(7) close for the product's store and smoother; (3) stays (AD-3: WP5.2);
  the step-aware run records the span length and the edge-free frame count.
- DR-41: not reopened (the engine constructs no cache and passes no codec).

## Limits

- The proxy block mean of a 4K frame runs on the host (Q9; no timing in this package).
- `provisional_record` measures on the caller's thread with the injected backend (CuPy is then
  used from two threads).
- Scrubbing during a recompute does not re-prioritise it; a new `set_parameters` does.
- The step-aware kinds read the whole series (a global noise scale), so their near phase is the
  whole clip.
