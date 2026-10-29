# WP4.3 report: application wiring

Brief `docs/briefs/wp4.3-brief.md` (FINAL; rulings `2c4476d9869df056`, `7c7df3dbe237ceb7`), round-0
ruling `fcb2a9205c060013` (ledger `docs/proofs/wp4.3-ledger.md`). Base main `038f02e`. Built by
cell 2 (`implementer-opus-high`). STATUS: build complete; Reviewer A and the exclusive window
(V7 of record, the GX011627 legs) are still to come, so the figures marked "window" below are
pending.

## What WP4.3 adds

- `python -m clearwater` (`src/clearwater/__main__.py`) and `clearwater.app.main.main`, the
  ONLY `clearwater.app` module that imports `clearwater.gui` or loads Qt. `build_application`
  makes the program the owner starts.
- `clearwater.app.startup`: the write journal, the leftover clean-up, the start-up job bodies.
- `clearwater.app.analysis_adapter`: the GUI's `ClipAnalysis` over WP3.11's `AnalysisEngine`.
- `clearwater.app.activity`: one activity per clip (`ClipLocks`, DR-62) and the export wrapper
  (`GuardedExports`: DR-82, DR-62, DR-68, the journal, the AD-9 log line).
- `clearwater.app.composition`: the application's ONE proxy cache, `DeferredProxyCache` built
  by `proxy_cache_opener(folder)` and opened once by a start-up job (ruling S1 (a)), and
  `export_jobs(cache=...)` (Q16).
- `gui/engines.py`: `default_engines(*, locations=None)`; the S1 stand-in is gone (Q11, Q17).
- `gui/settings_dialog.py`: WP3.10's `resolve_encoder`, `install_settings_dialog(catalog=)`
  (DR-52), DR-61 (i)-(iii). `gui/shell.py`: `MainWindow.set_idle_device` (S3) only.
- `gui/render_worker.py`, `gui/preview.py`: worker chores and the FFT plan release (DR-68);
  the D53 display profile (DR-75). `jobs`: the public `expected_frames` (Q18).

## The start-up sequence (round-0 order as ruled)

| Step | Thread | Measured (round 0, shared host; shape evidence) |
|---|---|---|
| imports (PySide6 + the shell) | main | 1,458 ms |
| `QApplication`, `app_locations()` | main | 11.8 ms, 0.01 ms |
| engines from the root (`default_engines(locations=...)`; the cache NOT opened) | main | 0.12 ms |
| `MainWindow`: the log, the ONE settings read, the presets | main | 13.8 ms |
| leftover clean-up over `Settings.output_folder` + the journal's folders | main, before any panel | 0.81 ms (750 files) |
| installs, then `show()` | main | 3.4 ms (show) |
| (i) cache open with `Settings.cache_limit_bytes` | job worker | 126 ms warm, 16.4 s first open (20 GB) |
| (ii) encoder detection into the catalog | job worker | 550 ms fresh |
| (iii) graphics-card detection, reason to the status bar | job worker | 947 ms first selection |

No job exists until the clean-up has ended (`test_the_cleanup_ends_before_any_panel_or_job`).
Every cache member waits for (i) and runs on a worker; a dialog limit or clear asked during the
open is applied after it (`test_s1_a_limit_and_a_clear_from_the_dialog_during_the_open_apply_after_it`).
A failed open is shown once and the photo path keeps working.

## Wiring table

| Panel | Engine | Test |
|---|---|---|
| Basic, Advanced, Presets (`install_parameter_panels`) | the root's methods, `"c3"` first | G3, G6 |
| Timeline (`install_timeline`) | `make_analysis_factory` over `AnalysisEngine` on the one cache | G4, G5, V18, adapter tests |
| Export, Batch (`install_export_panels`) | `GuardedExports(composition.export_jobs(cache=<the one cache>))` | G7, G8, G10, activity tests |
| Settings (`install_settings_dialog`) | `capability.resolve_encoder`, the start-up catalog, the one cache | G12, DR-52/61 tests |

## G-matrix (`tests/test_app_wiring.py`, on `build_application`'s shell)

G1, G2, G3, G4, G5, G6, G7, G8 (export and batch), G9 (engines off the UI thread; the 100 ms
figures are V7's), G10 (HLG, PQ, truncated, untagged, DNG; DR-35 (a) `NU`+`L`; DR-82 photo and
video, single and batch), G12 (every setting; force CPU gives `Device: CPU: forced`), G13 (two
window lifetimes): each has a passing test. G11 is deferred to v2 (spec 0.5.3): no test.

## V7, V8, V18

V7 (WP3.16's 10 ms probe; longest gap, p99, ticks). Gate forms on the fixture clip, a shared host
(not figures of record):

| Scenario | Gate form (fixture) | Window (GX011627) | Stub era |
|---|---|---|---|
| (a) analysis | 12.0 / 11.0 ms, 260 ticks | pending | WP3.18 12-39 ms |
| (b) scrubbing during it | 12.0 / 11.4 ms, 266 | pending | WP3.18 12-39 ms |
| (c) File > Export | 11.0 / 11.0 ms, 480 | pending | WP3.19 11-13 ms |
| (d) a 300-still batch (DR-50) | 30.0 / 14.0 ms, 942 | pending | WP3.19 11-13 ms (2 items) |
| (e) a 1:1 4K render during (c) | 20.0 / 12.0 ms, 1218 | pending | WP3.16 11-12 ms |
| (f) start-up, slow cache open | 49.0 / 11.0 ms, 329 | pending | none |

V8 (AD-11 as amended) on the shell, (mean, p99, max) in [0, 1] units, the preview's uint8 against
the exported 16-bit PNG: smooth synthetic scene k = 1 exact (within the 16-bit step), k = 2
(0.00100, 0.00196, 0.0145), k = 4 (0.00106, 0.00422, 0.0228); the WP1.3 look-check crop k = 2
(0.00117, 0.00459, 0.117), k = 4 (0.00156, 0.0146, 0.109). Video pre-encode at k = 2: mean
0.00305, max 0.0817. DR-75: the nclx-only Display P3 sample shows (217, 0, 54), the colour its
export's embedded profile gives; the base rule shows (199, 40, 60) and its planted form fails.
V18 gate form on `hevc8-bt709-full` with the held engine: a corrected frame before completion,
the engine's `smoothed_record` after. GX011627 V18: window, pending.

DR-68 (`gpu`, this laptop): `free_device_bytes()` 7,388.9 MB before the 1:1 4K render, 7,338.1
MB after it (6 cuFFT plans on `clearwater-preview`), 7,388.9 MB after the boundary (0 plans).

DR-44 (c): from `close()`, an analysis mid-decode ended in 17 ms, an export mid-encode in 10 ms,
a batch item in 23 ms (fixture clip); `gui/jobs.py` is not touched. GX011627: window, pending.

## DR dispositions

| Row | Disposition |
|---|---|
| DR-52 | CLOSES: stand-in and mirror test deleted; `resolve_encoder` default; `catalog` argument; erratum appended to the WP3.20 report; the `"unavailable"` error shown as the 10-bit reason. |
| DR-61 | CLOSES: (i) detail with a fallback; (ii) OK re-evaluated on `set_settings`; (iii) one banner per text. |
| DR-62 | CLOSES: WAIT, both orders tested on the real engines; cancel while waiting returns `CANCELLED`. |
| DR-68 | CLOSES: the release on `clearwater-preview` at a source change, close and before a job selects. |
| DR-75 | CLOSES: the REQUIRED test above. |
| DR-82 | CLOSES: the wrapper's pre-plan check, one test per route. |
| DR-84 | CLOSES: the witness instruments the three video constructors, with planted controls. |
| DR-35 (c) | CLOSES: the clean-up ends before any job can start. |
| DR-44 (c) | CLOSES as measured (above); window figures pending. |
| DR-50 | pending the window's 300-item figure (gate form 30 ms). |
| DR-51 (a) | CLOSES for the product path (the reader-versus-new-run test). (b) NOT REACHED. |
| DR-85 | the start-up test is `xfail(strict, raises=OverflowError)` until WP4.3a's fix is on main. |
| DR-35 (a), DR-47, DR-45 (a), DR-34 | CONSUMER NOTES as the brief says; DR-49's ground checked on the shell. |
| DR-69 | NOT REACHED (Q7): stays OPEN. |

## Limits

- The V7 and start-up figures above come from a shared host; the figures of record come from the
  exclusive window.
- `gui/shell.py`'s module and `run` docstrings still say WP4.3 calls `run`; the grant was the
  device text only, so they are left and flagged.
- A journal that cannot be written is logged and the export goes on (a crash then leaves no
  entry for that folder); the output folder is always scanned.
