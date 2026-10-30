# WP4.3 report: application wiring

Brief `docs/briefs/wp4.3-brief.md` (FINAL; rulings `2c4476d9869df056`, `7c7df3dbe237ceb7`), round-0
ruling `fcb2a9205c060013` (ledger `docs/proofs/wp4.3-ledger.md`). Base main `038f02e`, rebased
onto `5e3537d` by the orchestrator (cell 7's entry). Built by cell 2 (`implementer-opus-high`).
STATUS: build complete; Reviewer A ran six rounds (R1-R4 converged on the build, R5-R6 on the V7
remediation step, below); the exclusive windows 1-5 are done (V7 of record, the GX011627 legs);
product code final at `7b4c10b`. Reviewer B and the gate follow.

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

Record correction (cell 7): round 0's 20 GB cache was described as "made sparse and extended by
`truncate`"; it was not sparse. On Windows `truncate` extends a file through the C runtime's
`_chsize_s`, which writes the zeros (`fsutil sparse queryrange`: one range), so the 20 GB
cache-open figures above (126 ms warm, 16.4 s first open) come from 19.96 GB of fully allocated
packs, which is what a real full cache is. Each such plant costs 19.96 GB of real disk.

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

V7 (WP3.16's 10 ms probe; longest gap, p99, ticks; bound 100 ms). Gate forms on the fixture clip,
a shared host (not figures of record). The window column holds the figures of record: GX011627
((d): 300 synthetic stills), GPU, the owner's laptop, EXCLUSIVE windows, every run independent, no
tuning, no re-run; each names its window and EXIT (the runs are listed below the table).

| Scenario | Gate form (fixture) | Window (of record) | Stub era |
|---|---|---|---|
| (a) analysis | 19.0 / 17.0 ms, 257 ticks | 18.0 / 15.0 ms, 5,909 ticks; 681 frames in 59.1 s. Window 5, EXIT 0: PASS | WP3.18 12-39 ms |
| (b) scrubbing during it | 22.0 / 18.0 ms, 256; 62 proxies shown during the analysis | 19.0 / 15.0 ms, 6,352 ticks; 1,300 proxies shown during the analysis. Window 5, EXIT 0: PASS | WP3.18 12-39 ms |
| (c) File > Export | 19.0 / 17.0 ms, 455 | **180.0** / 12.0 ms, 20,897 ticks at the default 5 ms switch interval; **181.0** / 12.0 ms, 21,025 at 1 ms; export 209.1 / 210.7 s, one 86.0 MB output each. Window 4, EXIT 1 / 1: **OPEN STOP** | WP3.19 11-13 ms |
| (d) a 300-still batch (DR-50) | 34.0 / 14.0 ms, 948 | 56.0 / 43.0 ms, 1,855 ticks; 300 of 300 done in 28.6 s. Window 5, EXIT 0: PASS | WP3.19 11-13 ms (2 items) |
| (e) a 1:1 4K render during (c) | 57.0 / 24.0 ms, 1491; 1 render with k = 1 delivered inside the export sink's write | **182.0** / 12.0 ms, 21,080 ticks at 5 ms; 80.0 / 12.0 ms, 21,102 at 1 ms (one sample); 1 render with k = 1 inside the sink's write in each. Window 4, EXIT 1 / 0: **OPEN STOP** | WP3.16 11-12 ms |
| (f) start-up, slow cache open | 35.0 / 12.0 ms, 338; the analysis waited for the open (before the probe move; 18.0 ms after it, `28c4ece`, cell 9's targeted run) | from `show()`, settled 20 GB cache: 50.6 / 14.8 ms, 5,898 gaps. Window 5, EXIT 0: PASS | none |

Each gate form witnesses its workload, derived from the scenario text quoted in its docstring
(R1-12; R3-3 and R3-4). (b) counts the stored proxies the preview shows while the analysis phase
is running, not slider moves. (e) counts the delivered renders of the photo with `k == 1` while
the export's sink is inside a `write`: the fixture clip's encode ends before a 1:1 4K render
does, so the sink holds its first `write` in progress (the frame written, the call not returned)
until such a render has been delivered, and the 1:1 view is asked for only once that write has
begun. Rows (a), (b), (c) and (e) are from cell 6's targeted run, (d) and (f) from cell 4's
(2026-10-29; a shared host).

The runs of record:

- Window 5 (2026-10-30 02:02:51Z-02:07:14Z, chain exit 0): (a), (b), (d), (f). HEAD `8eaa897`
  (product code `7b4c10b`, the head this report describes), chain `bash
  <evidence>/windows/window5-commands.sh` (md5 `5b14d981...`), each run `timeout 2400 uv run
  python <evidence>/windows/s7_driver.py <mode> <work>/rec` with `QT_QPA_PLATFORM=offscreen` at
  the default switch interval, `s7_driver.py` md5 `0b9ee6cc...`; EXIT v7a 0, v7b 0, v7d 0,
  plant-f 0, v7f-settled 0.
- Window 4 (2026-10-30 ~01:24Z-01:48:34Z): (c), (e). HEAD `b4c8561` (product code `86ba69a`: item
  3's gc policy present, see the remediation step below), chain `window4-commands.sh` (md5
  `fb943904...`), each run `timeout 2400 uv run python <evidence>/windows/s7_switch.py <ms> <mode>
  <work>/sw<ms>` (md5 `5457aca8...`: it sets `sys.setswitchinterval` at process start, checks the
  driver's md5, then runs the unchanged `s7_driver.py` `0b9ee6cc...`); EXIT v7c 5 ms 1, v7c 1 ms
  1, v7e 5 ms 1, v7e 1 ms 0. They were not re-run on the reverted head: "(c)/(e) are not re-run
  (their figures of record stand; the revert cannot move them)" (CHARC `921babda38ba1f3a` Q1).
- `<evidence>` = `C:\Users\rwsmy\clearwater-review-evidence\wp4.3\`; the logs are in
  `windows\win4\` and `windows\win5\`, md5s in `windows\md5sums.txt`.
- History, not the figures of record: windows 1-2 (product code `300731d`, before the remediation
  step; window 1's driver `a1fb597b...`, window 2's `0b9ee6cc...`) (a) 18.0, (b) 21.0, (c) 182.0
  STOP, (d) 66.0, (e) 196.0 STOP ms; window 3 (f) from `show()` 47.5 ms; window 4's (b) 195.0 and
  (f) 395.4 ms STOPs were the gc policy's and went with its revert (window 5 above).

(c) and (e) are OPEN STOPs of record (CHARC `921babda38ba1f3a` Q3 (a)): 180.0 / 181.0 / 182.0 ms
longest, p99 12 ms, at 4K on the owner's laptop. The cause is in-process GIL contention with no
single holder (windows 3-4). Window 3's characterisation runs (not of record; py-spy and the call
wrappers perturb their figures) showed it: an out-of-process heartbeat never saw an interval over
16.3 ms across both probes, so the stall is inside the product process, not the host or paging;
py-spy `--gil` found the GIL passing among the two compute threads (`clearwater-job`,
`export-analysis`) and the interface thread inside the gaps, the compute threads alternating on it
while the interface thread's Python entries wait for it; no device-to-host copy holds it across a
gap. The switch interval was measured at the default 5 ms and at 1 ms (both figures above) and is
NOT adopted: "sys.setswitchinterval NOT adopted; the default stays" (`921babda38ba1f3a` Q2). A
register row, DR-98 (V7 (c)/(e) at 4K export: open; trigger = the follow-on package), is to be
opened at the accept by CHARC. The follow-on is WP4.6, export process isolation (the export's
per-frame work in a spawned process through AD-23's helper, the interface process keeping only
progress and the result), briefed by CHARC.

(f)'s rule (CHARC ruling B `b9a0ce010581a296`): "V7 (f)'s probe starts at show() ...
build_application's wall time is RECORDED beside the (f) figure as a start-up figure, cold and
warm, and is never asserted against 100 ms." The start-up figures, recorded and never asserted:
window 5's `v7f-settled` (the run above) `build_application` cold 93.8 ms, warm (the second build
in the process) 40.1 ms, the cache open 186.1 ms (plant-f's settling opens 4,243.1 ms then 108.4
ms); window 3's `v7f-settled` (history) cold 85.9 ms, warm 40.0 ms, the cache open 223.8 ms.
Development figures (cell 7's `f_build_profile.py` and dry runs on the fixture; shared host, NOT
of record): `build_application` in a fresh process without a cache 55 / 37 ms (first / second
build), and right after 20 GB of writes 933 / 771 ms (the first build in two runs; disk-cache
eviction, report-only); the pre-move probe's longest gap 158 ms and 651 ms planted in-process (two
runs) and 157 ms settled, the pre-show `build_application` being that gap (609 ms just after
planting, 126 ms settled), which is why the probe moved.

The V7 remediation step (CHARC `7b32521f060044d9`, after windows 1-3; one bounded step, each
change RED-first). Item 1 KEPT: `AppWindow(MainWindow)` notes its close in `closeEvent`, so no
Python event filter runs on the window's paint, update, layout or timer events (RED `6c06e54`,
GREEN `6dd9f19`); development witness on the real window, not of record: 101.3 / 264.0 ms ->
31.2 / 111.4 ms per progress report (median / max). The grant on `gui/jobs.py` and
`gui/export_panel.py` was GRANTED and NOT USED: the runner already delivers at most one report per
tick, the latest (now pinned in `tests/test_app_interface_load.py`). Item 2, the switch interval:
measured, not adopted (above). The (f) probe move (`838b665`, `28c4ece`) per ruling B. Item 3, a gc
policy (`FullCollections`: CPython's automatic full collection off while the window was open, a
freeze at the first idle check, collections at later idle checks), was tried, reviewed in R5
(ruling `cc0703a79f98154e`) and R6 (ruling `424f573b88b5a203`), and REVERTED (`7b4c10b`, ruling
`921babda38ba1f3a` Q1). Its epitaph: in window 4 (c) and (e) did not move (180.0 / 181.0 / 182.0
ms against 182.0 / 196.0 before), so it bought nothing measurable, and (b) 195.0 ms and (f) 395.4
ms were new STOPs where it acts (an idle-time collection on the interface thread beside the opener
worker; the cell's reading, not characterised); its memory readings (window 4, not of record):
working set +101.1 MB per 4K export ((c), both intervals), +247.2 / +237.0 MB in (e) with the 1:1
4K render, `gc.garbage` 0. R6 was this step's last Reviewer A round; the remaining findings
(R6-1..R6-4) were minor (THE CAP, `424f573b88b5a203`). The Reviewer A round count, six, exceeds the
fill's five because R5 and R6 reviewed a new step after R1-R4 converged on the main build.

V8 (AD-11 as amended) on the shell, (mean, p99, p99.9, max) in [0, 1] units, the preview's uint8
against the exported 16-bit PNG; p99.9 and max are AD-11's characterisation, recorded and never
asserted (R4-2): smooth synthetic scene k = 1 exact (within the 16-bit step), k = 2 (0.00100,
0.00196, 0.00796, 0.0145), k = 4 (0.00106, 0.00422, 0.0108, 0.0228); the WP1.3 look-check crop
k = 2 (0.00117, 0.00459, 0.0350, 0.117), k = 4 (0.00156, 0.0146, 0.0507, 0.109). Video pre-encode
at k = 2: mean
0.00305, p99 0.0392, max 0.0817 on the 320 x 180 fixture frame, RECORDED and printed, not
asserted (R1-13 = (a), CHARC ruling ace08fbb). The reason is AD-11's domain: its k > 1 bound (p99
within 2/255 at k = 2) is set "on real-sized content (at least 1080p)", and "small stills and
synthetic noise are outside V8's domain (a preview is a downscale of a real-sized image)", so the
fixture-frame p99 is a characterisation, not a V8 result. DR-75: the nclx-only Display P3 sample
shows (217, 0, 54), the colour its export's embedded profile gives; the base rule shows (199, 40,
60) and its planted form fails.

The V8 video leg on GX011627 (window 3's `v8v18`, of record: 2026-10-29 23:14:16Z-23:28:55Z, HEAD
`480f232` by the commit times, product code `300731d`, chain `window3-commands.sh` md5
`58478c4d...`, `s7_driver.py` `0b9ee6cc...`; 3840 x 2160, k = 2, GPU). Frames 10, 170, 340, 510:
mean 0.000488, 0.000330, 0.000185, 0.000315; p99 0.007203, 0.003579, 0.002301, 0.007885; at frame
510 p99.9 0.027003 and max 0.101342 (recorded); the shown frame equals the harness preview at all
four (max diff 0). Frame 510's p99 (2.011/255) was over the 2/255 the driver then asserted, by
0.000042 (EXIT 1). The video bound was then RE-RULED (CHARC `921babda38ba1f3a` Q4, and
`95392965dc5f8a6c` on its scope): it applies to the GX011627 video leg only, and the AD-11 note
CHARC writes at the accept reads "video at k = 2: p99 <= 2.5/255 per frame (mean <= 1/255; p99.9
and max recorded); stills unchanged at 2/255". Frame 510 is within the re-ruled video bound;
`v8v18` is not re-run; the stills' bound in `tests/test_app_v8_v18.py` (`P99_BOUND`, 2/255 at k =
2) is unchanged. The evidence for the re-rule is window 4's 16-frame characterisation (NOT of
record: HEAD `b4c8561`, product code `86ba69a`, `s7_v8char.py` md5 `60ab95a2...`, EXIT 0;
3840 x 2160, k = 2, GPU), values x 1/255:

| Frame | Mean | p99 | p99.9 | Max |
|---|---|---|---|---|
| 21 | 0.124 | 1.704 | 4.778 | 16.090 |
| 63 | 0.132 | 1.732 | 4.987 | 21.082 |
| 106 | 0.114 | 1.330 | 4.447 | 21.100 |
| 148 | 0.092 | 0.910 | 3.558 | 19.970 |
| 191 | 0.071 | 0.837 | 3.355 | 16.454 |
| 234 | 0.078 | 1.009 | 3.928 | 19.096 |
| 276 | 0.121 | 1.946 | 5.478 | 18.832 |
| 319 | 0.043 | 0.434 | 2.744 | 15.758 |
| 361 | 0.081 | 1.646 | 5.086 | 20.228 |
| 404 | 0.083 | 1.746 | 5.399 | 19.276 |
| 446 | 0.070 | 1.414 | 4.743 | 21.114 |
| 489 | 0.047 | 0.743 | 3.977 | 17.707 |
| 532 | 0.055 | 0.958 | 4.889 | 21.643 |
| 574 | 0.081 | 1.834 | 6.679 | 22.162 |
| 617 | 0.055 | 0.790 | 5.564 | 23.173 |
| 659 | 0.049 | 0.241 | 2.940 | 40.848 |

p99 median 1.169, max 1.946 (frame 276); no frame over 2/255 or 2.5/255; mean max 0.132; the shown
frame equals the harness preview at all 16 (max diff 0).

V18 gate form on `hevc8-bt709-full` with the held engine: a corrected frame before completion,
the engine's `smoothed_record` after. V18 on GX011627 (window 3's `v8v18`, above, of record; the
run's EXIT 1 is frame 510's V8 reading alone): the first render with the analysis running showed
a corrected frame with statistics None; after completion the shown statistics equal
`smoothed_record(pts)` (analysis 68.7 s, 681 frames).

DR-68 (`gpu`, this laptop): `free_device_bytes()` 7,388.9 MB before the 1:1 4K render, 7,338.1
MB after it (6 cuFFT plans on `clearwater-preview`), 7,388.9 MB after the boundary (0 plans).

DR-44 (c), from the first job runner's `close()` (fixture clip, cell 6's targeted run, a shared
host): an analysis whose frame source had yielded a frame, whose frame iterator had not ended
(run out, closed or raised) and whose phase was running ended in 52 ms; an export whose sink was open and had written a frame, with neither its close
nor its abort begun, in 33 ms; a running batch item in 39 ms. The two predicates are read as
that close begins (R3-5); each job is held after its first frame until then, so neither can be
missed. `gui/jobs.py` is not touched. On GX011627 (window 3, of record; the run named in the V8
paragraph above): the analysis ended in 361 ms, the export in 218 ms and the batch in 262 ms, each
at the close, with no temporaries left (EXIT 0 each).
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
| DR-44 (c) | CLOSES as measured (above): the fixture and GX011627 (window 3: 361, 218, 262 ms). |
| DR-50 | CLOSES by measurement: V7 (d), the 300-item batch, 56.0 / 43.0 ms (window 5, PASS); no per-row update, `gui/batch_panel.py` untouched. |
| DR-51 (a) | CLOSES for the product path (the reader-versus-new-run test). (b) NOT REACHED. |
| DR-85 | CLOSED by WP4.3a; the start-up test's `xfail(strict, raises=OverflowError)` was dropped at `300731d` once the fix was on main. |
| DR-35 (a), DR-47, DR-45 (a), DR-34 | CONSUMER NOTES as the brief says; DR-49's ground checked on the shell. |
| DR-69 | NOT REACHED (Q7): stays OPEN. |
| DR-89 | OPENS (CHARC's row at the accept, ruling ace08fbb): the D85 missing-folder residual, a Limit below. |
| DR-90 | OPENS (CHARC's row at the accept, ruling 38a7c702): R2-4, a Clear during another clip's export, a Limit below. |
| DR-98 | to be opened at the accept by CHARC (ruling 921babda): V7 (c)/(e) at 4K export, open; trigger = the follow-on package (WP4.6, export process isolation). A Limit below. |

## Limits

- The gate forms and the development start-up figures above come from a shared host; the figures
  of record come from the exclusive windows.
- V7 (c) and (e) miss the 100 ms bound at 4K on the owner's laptop (180.0 / 181.0 / 182.0 ms
  longest, window 4): OPEN STOPs of record, cause in-process GIL contention; DR-98 (to be opened
  at the accept) and the follow-on WP4.6 (CHARC ruling 921babda Q3).
- The shell's close waits up to `SHUTDOWN_TIMEOUT_S` (5 s) for a start-up job that cannot be
  cancelled (the cache's first open); the interface thread is held for that wait (R1-5). A
  settings-dialog clear or limit job that waits on that open and fails after the window's close
  logs its error and presents nothing (R2-3, ruling 38a7c702).
- The V8 video leg's fixture-frame p99 (10/255 at k = 2) is recorded, not asserted, because AD-11
  sets the k > 1 bound "on real-sized content (at least 1080p)" and "small stills and synthetic
  noise are outside V8's domain" (R1-13 = (a), ruling ace08fbb); the video p99 of record is the
  GX011627 window leg's, under the re-ruled video bound (p99 <= 2.5/255 per frame at k = 2,
  rulings 921babda Q4 and 95392965).
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
