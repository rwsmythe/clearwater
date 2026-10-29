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
| (a) analysis | 19.0 / 17.0 ms, 257 ticks | pending | WP3.18 12-39 ms |
| (b) scrubbing during it | 22.0 / 18.0 ms, 256; 62 proxies shown during the analysis | pending | WP3.18 12-39 ms |
| (c) File > Export | 19.0 / 17.0 ms, 455 | pending | WP3.19 11-13 ms |
| (d) a 300-still batch (DR-50) | 34.0 / 14.0 ms, 948 | pending | WP3.19 11-13 ms (2 items) |
| (e) a 1:1 4K render during (c) | 57.0 / 24.0 ms, 1491; 1 render with k = 1 delivered inside the export sink's write | pending | WP3.16 11-12 ms |
| (f) start-up, slow cache open | 35.0 / 12.0 ms, 338; the analysis waited for the open | pending | none |

Each gate form witnesses its workload, derived from the scenario text quoted in its docstring
(R1-12; R3-3 and R3-4). (b) counts the stored proxies the preview shows while the analysis phase
is running, not slider moves. (e) counts the delivered renders of the photo with `k == 1` while
the export's sink is inside a `write`: the fixture clip's encode ends before a 1:1 4K render
does, so the sink holds its first `write` in progress (the frame written, the call not returned)
until such a render has been delivered, and the 1:1 view is asked for only once that write has
begun. Rows (a), (b), (c) and (e) are from cell 6's targeted run, (d) and (f) from cell 4's
(2026-10-29; a shared host).

V8 (AD-11 as amended) on the shell, (mean, p99, max) in [0, 1] units, the preview's uint8 against
the exported 16-bit PNG: smooth synthetic scene k = 1 exact (within the 16-bit step), k = 2
(0.00100, 0.00196, 0.0145), k = 4 (0.00106, 0.00422, 0.0228); the WP1.3 look-check crop k = 2
(0.00117, 0.00459, 0.117), k = 4 (0.00156, 0.0146, 0.109). Video pre-encode at k = 2: mean
0.00305, p99 0.0392, max 0.0817 on the 320 x 180 fixture frame, RECORDED and printed, not
asserted (R1-13 = (a), CHARC ruling ace08fbb). The reason is AD-11's domain: its k > 1 bound (p99
within 2/255 at k = 2) is set "on real-sized content (at least 1080p)", and "small stills and
synthetic noise are outside V8's domain (a preview is a downscale of a real-sized image)", so the
fixture-frame p99 is a characterisation, not a V8 result. The V8 video figure of record is the
GX011627 window leg: mean abs within 1/255 AND p99 within 2/255 at k = 2 ASSERTED on the real-size
frame, p99.9 and max recorded (window, pending). DR-75: the nclx-only Display P3 sample shows
(217, 0, 54), the colour its export's embedded profile gives; the base rule shows (199, 40, 60)
and its planted form fails.
V18 gate form on `hevc8-bt709-full` with the held engine: a corrected frame before completion,
the engine's `smoothed_record` after. GX011627 V18: window, pending.

DR-68 (`gpu`, this laptop): `free_device_bytes()` 7,388.9 MB before the 1:1 4K render, 7,338.1
MB after it (6 cuFFT plans on `clearwater-preview`), 7,388.9 MB after the boundary (0 plans).

DR-44 (c): from `close()`, an analysis mid-decode ended in 17 ms, an export mid-encode in 10 ms,
a batch item in 23 ms (fixture clip); `gui/jobs.py` is not touched. GX011627: window, pending.
The start-up jobs (R1-5), reproduced on the real `main()` path with a 12 s cache open and a
close 0.3 s after the window showed: the close returned after the 5 s `SHUTDOWN_TIMEOUT_S` wait
(the open cannot be cancelled), `app.exec()` returned with it, and the process ended 0.3 s later
with the open's daemon thread abandoned: no exit hang past the timeout and no late delivery
after the loop, so `gui/jobs.py` is not touched. The device probe's `on_done` was delivered
inside the close (the runner delivers every ended job there); a guard in `app/main.py` now drops
every start-up callback once the window got its close event, the catalog's included, and a test
shows a late delivery to a loop that keeps running reaches nothing (evidence
`C:\Users\rwsmy\clearwater-review-evidence\wp4.3\major5\`, `md5sums.txt`).

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
| DR-89 | OPENS (CHARC's row at the accept, ruling ace08fbb): the D85 missing-folder residual, a Limit below. |
| DR-90 | OPENS (CHARC's row at the accept, ruling 38a7c702): R2-4, a Clear during another clip's export, a Limit below. |

## Limits

- The V7 and start-up figures above come from a shared host; the figures of record come from the
  exclusive window.
- The shell's close waits up to `SHUTDOWN_TIMEOUT_S` (5 s) for a start-up job that cannot be
  cancelled (the cache's first open); the interface thread is held for that wait (R1-5). A
  settings-dialog clear or limit job that waits on that open and fails after the window's close
  logs its error and presents nothing (R2-3, ruling 38a7c702).
- The V8 video leg's fixture-frame p99 (10/255 at k = 2) is recorded, not asserted, because AD-11
  sets the k > 1 bound "on real-sized content (at least 1080p)" and "small stills and synthetic
  noise are outside V8's domain" (R1-13 = (a), ruling ace08fbb); the asserted p99 is the GX011627
  window leg's.
- A journal entry that cannot be written, or a journal that exists but cannot be read, fails the
  export readably before any read or probe, with nothing written; a doubtful read never
  overwrites the retained entries (R1-2, ruling d530b564; R2-1, ruling 38a7c702); the output
  folder is always scanned.
- A Clear during another clip's export fails that export readably, with nothing partial written
  (R2-4, banked as DR-90 by ruling 38a7c702; the dialog's Clear is gated only by the open clip's
  analysis, WP3.20's rule).
- A journal entry stays until its folder's clean-up has succeeded (R1-3). A folder that no longer
  exists counts as clean and its entry is dropped; a folder that cannot be listed keeps its
  entry. For D85 this means: a temporary left on a drive that is unplugged when the program
  next starts (its path then reads as missing) is not removed when the drive comes back, unless
  that folder is the output folder or a later export's destination again; it stays a visible
  `.clearwater-partial` file the user can delete. ACCEPTED as a Limit, register row DR-89
  (CHARC's at the accept, ruling ace08fbb; trigger: the next touch of the leftover journal, or an
  owner report of a stale `.clearwater-partial`).

## Collection diff against `038f02e`

Every node ID removed from a test file that exists on the base, with its reason (fill
GATE_CHECKS). Every other change only adds node IDs: eight new `tests/test_app_*.py` files, new
cases in `test_app_composition.py`, and `test_app_leftovers.py`'s undecodable-journal parameter,
which became bytes with its five old ids kept and two added.

| Removed node ID | Reason |
|---|---|
| `tests/test_app_deps.py::test_no_app_module_imports_the_gui_or_qt` | RENAMED to `::test_no_app_module_but_main_imports_the_gui_or_qt_and_none_imports_cupy` (Q15: `main.py` is exempt from the gui/Qt ban; the cupy ban covers all) |
| `tests/test_gui_settings_dialog.py::test_auto_is_resolved_by_a_rule_that_disagrees_with_the_interim_rule` | RENAMED to `::test_auto_is_resolved_by_a_rule_that_disagrees_with_the_default_rule` (DR-52: the interim rule is gone; it compares with `capability.resolve_encoder`) |
| `tests/test_gui_settings_dialog.py::test_interim_rule_matches_the_wp310_rule` | DELETED (DR-52: `interim_resolve_encoder` deleted) |
| `tests/test_gui_status.py::test_stub_era_adapter_estimates_an_unknown_method_as_c3` | DELETED (Q11: the S1 stand-in `stub_era_select_backend` deleted) |
| `tests/test_gui_status.py::test_default_engines_select_cpu_forced_with_the_real_selection` | DELETED (Q11, the same) |
