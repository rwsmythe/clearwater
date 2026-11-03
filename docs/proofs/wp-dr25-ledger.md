# WP-DR25 cumulative ledger

## Round 0

Read-only turn 1 on base `758575d9`; no files changed and no test, probe or
instrument phase ran. Findings were routed by the dispatcher to CHARC. The
worktree was rebased onto CHARC's ruling commit `0f2d19c4` before turn 2.

| Item | Finding / observation on the original instrument | Classification | CHARC ruling (`0f2d19c4`, brief round-0 section) |
|---|---|---|---|
| D1 | The smoothing-candidate loop selects only `RENDER_METHOD=ancuti2018`; both methods receive only the fixed Gaussian 1 s comparison. | Confirmed MAJOR, in envelope; source trace at original instrument lines 913-918 and WP1.4 report line 458. | Under `--long` only, run the window study for both methods. Preserve the default loop and `RENDER_METHOD`. |
| D2 | `_interior` uses a fixed single-filter margin of 60 frames; `staged_reach` has no executable caller and the instrument prints no staged edge-free counts. Candidate records omit the per-step arrays needed for re-trimming. | Confirmed MAJOR, in envelope; original lines 668-677, 864, 916-935, confirmed by read-only `rg`. | Long staged interiors use method-specific staged reach, flat interiors use single-filter radius; record frame/step counts and staged/flat per-step arrays. |
| D3 | Historical GX011627 duration 22.7227 s leaves only 15.90589 s at 0.30; extraction does not clamp. GX011625 duration 498.43 s fits at 0.50. | Confirmed start-fit observation from WP1.4 report lines 36-39, not a fresh footage probe. | Clamp long specs only to `min(fraction * duration, duration - 20.0)`; record requested and actual start and probed duration. |
| D4 | WP3.11's strict endpoint-excluding convention differs by two frames from the brief's `N - 2 * reach` arithmetic. | Confirmed MINOR, in envelope; `step_aware_eval.py` original lines 283-287. | Use the instrument's slice form: `slice(reach, count - 1 - reach)` for steps. State WP3.11's strict form beside it in the later report. |

Round-0 finding counts: 0 critical, 2 major, 1 minor, plus D3's fit observation;
all new, none reopened, none reverted. No product or test fix in turn 1.
This was a prerequisite audit, not a Reviewer A round. Both review nets remain
the dispatcher's Claude passes.

The local configuration points at the main tree's working folder, which is
outside this cell's writable roots. The dispatcher launches both GPU phases at
its seat after Reviewer A's first round. No footage or main-tree work read is
needed by the synthetic tests in turn 2.

### Expected edge-free counts

At 30000/1001 fps, a 20.0 s interval spans approximately 599.4 frame periods;
the actual extraction records the count. Gaussian half-widths for 1 / 2 / 4 s
are 14 / 29 / 59; the median adds one, so `median_gaussian` radii are
15 / 30 / 60. Staged reach = stages * radius (c3: 2; Ancuti: 3).
Frames = `max(N - 2 * reach, 0)`; steps = `max(N - 1 - 2 * reach, 0)`.

These expectations apply separately to both excerpts; no footage has been
probed in the cell.

| Filter | Method | Reach at 1 / 2 / 4 s | N=600 frames | N=600 steps | N=599 frames | N=599 steps |
|---|---|---|---|---|---|---|
| median_gaussian | c3 | 30 / 60 / 120 | 540 / 480 / 360 | 539 / 479 / 359 | 539 / 479 / 359 | 538 / 478 / 358 |
| median_gaussian | ancuti2018 | 45 / 90 / 180 | 510 / 420 / 240 | 509 / 419 / 239 | 509 / 419 / 239 | 508 / 418 / 238 |
| gaussian or moving_average | c3 | 28 / 58 / 118 | 544 / 484 / 364 | 543 / 483 / 363 | 543 / 483 / 363 | 542 / 482 / 362 |
| gaussian or moving_average | ancuti2018 | 42 / 87 / 177 | 516 / 426 / 246 | 515 / 425 / 245 | 515 / 425 / 245 | 514 / 424 / 244 |
| median_gaussian, flat | either | 15 / 30 / 60 | 570 / 540 / 480 | 569 / 539 / 479 | 569 / 539 / 479 | 568 / 538 / 478 |
| gaussian or moving_average, flat | either | 14 / 29 / 59 | 572 / 542 / 482 | 571 / 541 / 481 | 571 / 541 / 481 | 570 / 540 / 480 |

WP3.11's strict convention excludes two additional endpoint-touching frames
from a full span. The convention above is the one CHARC chose for this package.

## Turn 2

Depth at turn-1 end: 119,280 of 258,400 (driver footer)

Depth at turn-2 end: 176,708 input tokens of 475,000 (driver footer, 2026-11-03 turn 2; the footer reported a 258,400 window at turn 1)

Scope: the instrument, its new synthetic test module and this ledger only.
No product code, prototype, dependency, frozen interface or default smoothing
decision is changed. No instrument run or GPU phase is launched by this cell.

### RED on the unchanged instrument

Command (PowerShell; the required sandbox shim is the only addition to the
dispatch's pytest command):

```powershell
$env:PYTHONPATH='scripts'
uv run pytest -q -p sandbox_mkdir_shim -p no:cacheprovider tests/test_tools_statistics_experiments.py --timeout 120 --basetemp=work/cdr25-2-red > work/cdr25-2-red.log 2>&1
```

Exit 1; `6 failed, 5 passed in 6.96s`. Every long test failed; every default
test passed, as required.

| Test (module `tests/test_tools_statistics_experiments.py`) | RED outcome | Failure line / evidence |
|---|---|---|
| `test_default_cli_keeps_original_specs_root_and_render_selection[extract]` | PASS by design | Default extraction specs, lookup and root retained. |
| `test_default_cli_keeps_original_specs_root_and_render_selection[analyse]` | PASS by design | Default analysis folders/root retained; no long keyword selected. |
| `test_default_cli_keeps_original_specs_root_and_render_selection[render]` | PASS by design | Only the original render-enabled spec is passed to rendering. |
| `test_default_extract_keeps_start_and_record_schema` | PASS by design | Unchanged start and absence of the new long-only field. |
| `test_default_window_study_keeps_one_method_and_fixed_margin` | PASS by design | Ancuti-only 12-candidate study; all candidate interiors use margin 60. |
| `test_long_cli_selects_long_specs_and_separate_root_without_mutating_defaults[extract]` | FAIL as expected | `SystemExit: 2`; parser rejects `--long`. |
| `test_long_cli_selects_long_specs_and_separate_root_without_mutating_defaults[analyse]` | FAIL as expected | `SystemExit: 2`; parser rejects `--long`. |
| `test_long_extract_records_requested_and_clamped_start[clamped]` | FAIL as expected | `assert 6.816809999999999 == 2.7227` (approximate expected value); start was not clamped. |
| `test_long_extract_records_requested_and_clamped_start[fits]` | FAIL as expected | `KeyError: 'requested_start_s'`. |
| `test_long_window_study_records_both_methods_reaches_counts_and_auditable_steps[600]` | FAIL as expected | `TypeError: run_experiments() got an unexpected keyword argument 'long'`. |
| `test_long_window_study_records_both_methods_reaches_counts_and_auditable_steps[599]` | FAIL as expected | Same missing long-study entry point. |

The boundary control independently constructs frame-step values of 100 at the
two ends and 1 in the middle. A fixed 60-frame trim includes markers (default
interior 24239/479 at N=600); the 4 s Ancuti staged reach of 180 excludes them
(long interior 1). Expectations use literal radii and the constructed signal,
never `staged_reach` to calculate their oracle. The real flicker calculation,
real root construction and real checked JSON writers remain under test.

### GREEN and development checks

The first new-module GREEN run exited 0: `11 passed in 0.83s`.
Initial lint/format checks found three line-length issues and two formatting
changes after indentation of the default loop; corrected without changing
behavior.

| Check | Final summary observed | Log |
|---|---|---|
| New synthetic module | `11 passed in 0.83s`, exit 0; final rerun after LF normalization: `11 passed in 0.81s`, exit 0 | `work/cdr25-2-green.log`, `work/cdr25-2-green-final.log` |
| Existing importers, selected non-hardware tests | `85 passed, 4 deselected, 1 warning in 15.40s`, exit 0; GPUs hidden for this process only (see initial-attempt record below) | `work/cdr25-2-old.log` |
| Ruff on the two Python files | `All checks passed!`, exit 0 | `work/cdr25-2-ruff.log` |
| Ruff format on the two Python files | `2 files already formatted`, exit 0 | `work/cdr25-2-format.log` |
| Whole configured mypy scope | `Success: no issues found in 156 source files`, exit 0 | `work/cdr25-2-mypy.log` |

Commands for the static checks:

```text
uv run ruff check tools/statistics_experiments.py tests/test_tools_statistics_experiments.py
uv run ruff format --check tools/statistics_experiments.py tests/test_tools_statistics_experiments.py
uv run mypy
```

Every runner's stdout/stderr was redirected to its log under this worktree's
`work/`. uv warns that the inherited main-tree `VIRTUAL_ENV` differs from the
project environment and is ignored; the commands use this worktree's `.venv`,
without `--active` or `uv sync`.

### Verification-loop record

| Suspected issue | Independent confirmation / rejection | Disposition |
|---|---|---|
| Long selection could alter default extraction, analysis or render routing. | Default routing tests passed on both RED and GREEN; exact original specs/root/render selection are asserted, and module defaults are unchanged. | Rejected as a default-path regression. |
| Clamping could leak into normal excerpts or fail to record the requested start. | Default extraction record test passes unchanged; the clamped and fitting long cases fail on RED and pass on GREEN using probe stubs. | Long-only clamp and record field implemented. |
| A 60-frame margin could still count boundary markers in the long 4 s staged Ancuti figure. | Independent step signal gives 24239/479 with the old trim, versus 1 after the 180-frame trim; both N=600 and N=599 test all method/filter/window records and counts. | Fixed on the long path; default margin remains unchanged. |
| Per-step audit arrays or method coverage could be missing. | Tests assert both methods, 24 distinct method/candidate evaluations, both arrays and re-trimmed interior means in persisted JSON. | Fixed on the long path. |
| Default result payload could drift while the new branch is introduced. | Read the default synthetic `results.json` from RED and GREEN; after replacing only `written` timestamps, the serialized text matches byte for byte. | Rejected on the exercised synthetic surface; no real-footage identity run was launched. |
| Source formatting/encoding could violate the dispatch. | Ruff identified the three long lines; formatting identified two wrapped calls. Read all owned files as bytes; normalize the existing instrument's CRLF to LF. | Style corrected; all owned files must be LF-only and ASCII at handoff. |

The importer check's initial attempt produced no pytest progress or basetemp
while consuming CPU. The pre-existing module-level `_AUTO = select_backend("auto")`
in `tests/test_prototype_temporal.py:47` reaches a CUDA test-kernel compile in
`tools/prototype/backend.py:211`, even with GPU markers deselected. This is an
environmental collection-stall hypothesis, not a product-code finding. Process
metadata confirmed the launcher in this worktree's `.venv`; CIM stack/process
inspection was denied by the sandbox. The cell stopped only that run's uv,
launcher and Python processes, preserved `work/cdr25-2-old-initial.log` and
`work/cdr25-2-old-watch.log`, and retried the same selected tests with
`CUDA_VISIBLE_DEVICES=-1`. Initial attempt: terminated, not a passing result.
The retry exited 0: `85 passed, 4 deselected, 1 warning in 15.40s`. This
supports the import-time CUDA-probe hypothesis; no product or test code was
changed to unblock it. The warning is CuPy's `CUDA path could not be detected.
Set CUDA_PATH environment variable if CuPy fails to load.` There were no
selected-test skips. GPU/footage outcomes are still owed at the dispatcher's
serial gate, with the GPU visible there.

Exact importer retry and final synthetic rerun:

```powershell
$env:PYTHONPATH='scripts'
$env:CUDA_VISIBLE_DEVICES='-1'
uv run pytest -q -p sandbox_mkdir_shim -p no:cacheprovider tests/test_footage_locator.py tests/test_prototype_temporal.py -m "not gpu and not footage and not gui and not slow" --timeout 300 --basetemp=work/cdr25-2-old > work/cdr25-2-old.log 2>&1
```

The final synthetic rerun was in a separate shell, without that GPU mask:

```powershell
$env:PYTHONPATH='scripts'
uv run pytest -q -p sandbox_mkdir_shim -p no:cacheprovider tests/test_tools_statistics_experiments.py --timeout 120 --basetemp=work/cdr25-2-green-final > work/cdr25-2-green-final.log 2>&1
```

Final verification pass: no further in-envelope code/test issue found. The
default study body is retained under `else` (only indentation and call wrapping
changed). `RENDER_METHOD`, `_interior`, `EXCERPTS` and `WORK_SUBDIR` are unchanged.
The shared CLI now selects locals, with the original values and original
`run_experiments` call when the flag is absent. Extraction adds a membership
guard, false for either original spec, so normal start/record contents stay
unchanged. Docstrings describe the added path. The additional keyword-only
argument defaults to false. All other changes are long-only.

Encoding/ownership checks: `git diff --check` is clean; all three owned files
are ASCII with zero CR bytes. The only tracked modification is the instrument,
plus the new test and ledger (untracked until the dispatcher's pathspec commit).
This turn bundles the ruled instrument change and its synthetic evidence as
one logical RED/GREEN change. No review findings are adjudicated in this turn;
no reopens or reverts. The default-regression suspicions were rejected by the
tests and saved-record comparison; confirmed long-path gaps and style issues
were fixed. The collection stall is disclosed above, with a process-only
workaround rather than an out-of-envelope code change.

No Reviewer A round has run yet; the dispatcher runs it after this turn. No
GPU instrument phase, full suite, harness gate or serial-leg footage/GPU test
was run by the cell. The report is deferred until the dispatcher's instrument
records exist. No AD-3 ruling is made here.

## Turn 3 (Reviewer A round 1 remediation)

Base: `71806c5e`, the dispatcher's commit of turn 2. Depth at turn-2 end:
176,708 of 475,000 (driver footer, supplied by the dispatcher).

Depth at turn-3 end: 211,019 input tokens of 475,000 (driver footer, 2026-11-03 turn 3)

Reviewer A: dispatcher-seat Claude pass on `71806c5e`, verdict
`NO_NEW_CRITICAL_MAJOR`. The dispatcher reports claims 1-5 and 7 HOLD by
execution, claim 6 PARTIAL (9 of 13 mutants killed). The full transcript is
held by the dispatcher in the package's evidence folder; its exact filename
and model/version were not supplied to this cell. This ledger records the
supplied findings and independently executed remediation evidence, not a new
review pass.

### Cumulative round ledger

| Round | Critical | Major | Minor | Advisory | In / out of envelope | NEW / REOPENED | Reverts | Fix surface | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| 0 prerequisite audit | 0 | 2 | 1 | D3 fit observation | All in | All new / 0 | 0 | No turn-1 edits; ruled changes implemented in turn 2 | CHARC ruled at `0f2d19c4` |
| A1 | 0 | 0 | 2 | 6 | F1-F7 in; F8 out | 8 / 0 | 0 permanent | Tests: F1/F2/F5/F7; instrument: F5/F6/F7; no shipped product code | `NO_NEW_CRITICAL_MAJOR`; cleanup performed once |

The four temporary mutation edits below were restored in `finally` after each
probe and are not permanent reverts. No code under `src/clearwater/`, shared
prototype or dependency file changed. Both review nets remain dispatcher-owned.

### Dispositions

| Finding | Severity / envelope | Independent confirmation and action | Disposition |
|---|---|---|---|
| F1 | MINOR, in | The old `_signals` fake ignored method, series and reference. It now emits time-varying slopes keyed by params method and staged/flat/unsmoothed/linear-trend series. Reference slopes use the real `temporal.constant_statistics` applied to distinct per-method raw bounds. Tests assert literal per-method residual offsets, unsmoothed arrays, reference fields and every candidate's staged/flat per-step arrays and interior. M5/M6/M8 now fail. | FIXED in tests. |
| F2 | ADVISORY, in | The previous default probe duration left enough room for 6 s, so broadening the clamp was invisible. Added duration 10 s for the default 0.50/6 s spec: start must stay 5 s, while the mutant moves it to 4 s. | FIXED in tests; M13 now fails at the start assertion. |
| F3 | ADVISORY, seat | Resource estimates supplied by the dispatcher: about 15-25 GB transient disk per excerpt during extraction, about 7 GB persistent `.npy`, about 7 GB RAM peak. These are not cell measurements. The dispatcher raises the free-disk floor to 50 GB before extraction and runs nothing heavy beside it. | SEAT responsibility; no cell code change or GPU run. |
| F4 | ADVISORY, report | Top-level `interior_margin_frames` / `interior_steps` describe only `flicker`, not the candidate-specific long interiors. | REPORT OBLIGATION: re-trim each method's unsmoothed `flicker` per-step array to each candidate/analysis record's own `interior_steps` before comparing its baseline. Explain the top-level fields' scope. |
| F5 | ADVISORY, in | `render --long` previously selected no render-enabled spec and exited successfully. It now returns 2 with `error: --long supports extract and analyse only; render is disabled`, before configuration, path or device access. A test forbids those accesses. | FIXED in instrument and test. Normal render is unchanged. |
| F6 | ADVISORY, in | The long branch replaces the default window-study branch. | FIXED docstring: explicitly says a two-method study replaces the Ancuti-only study. |
| F7 | ADVISORY, in | `StreamInfo` exposes only the resolved duration. A long-only read-only `run_ffprobe` query recovers stream/container source using the shared probe's exact missing/`N/A` fallback predicate; the long record adds `duration_source`. Tests cover present stream duration, missing duration and `N/A` for both clamped/fitting cases, and forbid the additional query/default field on normal extraction. | FIXED within the owned instrument; the shared probe/interface and default records remain unchanged. |
| F8 | MINOR, out | The clamp can produce a negative start when total duration is under 20 s. Both commissioned chapters exceed 20 s; the dispatcher explicitly excludes a code change. | REPORT LIMIT obligation, not loop-driving; no code change. |

Signal-witness arithmetic is independent of the instrument's smoothing helpers.
The constructed boundary step levels remain 100 versus 1 in the interior.
Method keys are Ancuti=2 and c3=7, staged/flat series keys 11/17, and raw-reference
keys Ancuti=3 and c3=5. Thus staged/flat residual offsets are 16/28 for Ancuti
and 42/84 for c3. Unsmoothed offsets are 40 and 126. A constant signal offset
would cancel in flicker; these keys are slopes and survive the real difference
calculation. The 4 s Ancuti staged interior is therefore 17 (1 + 16), while the
old margin still includes marker steps. Counts/re-trimming remain checked at
both N=600 and N=599.

### RED for newly required behavior

Before changing the instrument, the revised module ran with:

```powershell
$env:PYTHONPATH='scripts'
uv run pytest -q -p sandbox_mkdir_shim -p no:cacheprovider tests/test_tools_statistics_experiments.py --timeout 120 --basetemp=work/cdr25-3-red > work/cdr25-3-red.log 2>&1
```

Exit 1: `7 failed, 10 passed in 0.89s`. The long-render refusal failed on its
forbidden configuration access; all six long clamp/source combinations failed
on missing `duration_source`. The strengthened witnesses and the new default
short-duration case passed on the correct pre-mutation instrument, as intended.

### Mutation probes (all killed)

Each probe read the current instrument into a PowerShell string, required one
exact match for its replacement, wrote the mutant as UTF-8/LF, ran the command
below, and restored the saved original in `finally`. Afterward it asserted
byte-equivalent original text was restored. Each pytest invocation exited 1;
the wrapper required that exit and exited 0 only after restoration. No mutant
is committed or left on disk.

| Mutant | Exact temporary change in the long helper (or clamp) | Result / failing test |
|---|---|---|
| M5 | `("staged", staged, staged_reach(name, smoother, rate))` -> `("staged", flat, staged_reach(name, smoother, rate))` | `2 failed, 15 passed in 0.85s`; both `[600]` and `[599]` long-window tests fail their keyed per-step witness. |
| M6 | In the long helper's `_sequence_record` call, `_signals(loaded.proxies, params, series, backend)` -> `_signals(loaded.proxies, METHODS["ancuti2018"], series, backend)` | `2 failed, 15 passed in 0.85s`; both long-window tests reject the wrong c3 render params. |
| M8 | Only the long helper's reference construction: `temporal.constant_statistics(loaded.raw[name])` -> `temporal.constant_statistics(loaded.raw["ancuti2018"])` | `2 failed, 15 passed in 0.83s`; both long-window tests reject the wrong c3 reference slope. |
| M13 | Move `start = min(start, info.duration_s - spec.duration_s)` outside the `if is_long` guard; keep the extra duration probe guarded. | `1 failed, 16 passed in 0.83s`; `test_default_extract_keeps_start_and_record_schema[short-unclamped]` observes 4 s instead of 5 s. |

Exact pytest commands, each with process-local `PYTHONPATH=scripts`:

```text
uv run pytest -q -p sandbox_mkdir_shim -p no:cacheprovider tests/test_tools_statistics_experiments.py --timeout 120 --basetemp=work/cdr25-3-m5 > work/cdr25-3-m5.log 2>&1
uv run pytest -q -p sandbox_mkdir_shim -p no:cacheprovider tests/test_tools_statistics_experiments.py --timeout 120 --basetemp=work/cdr25-3-m6 > work/cdr25-3-m6.log 2>&1
uv run pytest -q -p sandbox_mkdir_shim -p no:cacheprovider tests/test_tools_statistics_experiments.py --timeout 120 --basetemp=work/cdr25-3-m8 > work/cdr25-3-m8.log 2>&1
uv run pytest -q -p sandbox_mkdir_shim -p no:cacheprovider tests/test_tools_statistics_experiments.py --timeout 120 --basetemp=work/cdr25-3-m13 > work/cdr25-3-m13.log 2>&1
```

This is fresh evidence for the four requested survivors, not a claim that all
13 original mutations were re-executed in this turn.

### GREEN and checks

| Check | Observed summary (exit 0) | Log |
|---|---|---|
| New synthetic module | `17 passed in 0.96s`; after probes/restoration and formatting: `17 passed in 0.76s` | `work/cdr25-3-green.log`, `work/cdr25-3-green-final.log` |
| Importers' non-hardware selection | `85 passed, 4 deselected, 1 warning in 1.99s` | `work/cdr25-3-old.log` |
| Ruff, two Python files | `All checks passed!` | `work/cdr25-3-ruff.log` |
| Ruff format, two Python files | `2 files already formatted` | `work/cdr25-3-format.log` |
| Whole configured mypy scope | `Success: no issues found in 156 source files` | `work/cdr25-3-mypy.log` |

Commands (all stdout/stderr redirected to the named worktree logs):

```powershell
$env:PYTHONPATH='scripts'
uv run pytest -q -p sandbox_mkdir_shim -p no:cacheprovider tests/test_tools_statistics_experiments.py --timeout 120 --basetemp=work/cdr25-3-green > work/cdr25-3-green.log 2>&1
uv run pytest -q -p sandbox_mkdir_shim -p no:cacheprovider tests/test_tools_statistics_experiments.py --timeout 120 --basetemp=work/cdr25-3-green-final > work/cdr25-3-green-final.log 2>&1
```

The importer command used `CUDA_VISIBLE_DEVICES=-1` proactively in its own
process, reusing turn 2's confirmed collection workaround rather than repeating
the stalled CUDA-probe attempt. No new stall occurred. The selected tests had
no skips. The one warning is CuPy's undetected CUDA path; GPU/footage tests stay
deselected and remain the dispatcher's serial-gate obligation.

```powershell
$env:PYTHONPATH='scripts'
$env:CUDA_VISIBLE_DEVICES='-1'
uv run pytest -q -p sandbox_mkdir_shim -p no:cacheprovider tests/test_footage_locator.py tests/test_prototype_temporal.py -m "not gpu and not footage and not gui and not slow" --timeout 300 --basetemp=work/cdr25-3-old > work/cdr25-3-old.log 2>&1
```

```text
uv run ruff check tools/statistics_experiments.py tests/test_tools_statistics_experiments.py
uv run ruff format --check tools/statistics_experiments.py tests/test_tools_statistics_experiments.py
uv run mypy
```

The initial lint/format pass found one overlong refusal-message call and a test
comprehension layout; both were corrected before the final passing checks.
uv's inherited-`VIRTUAL_ENV` warning remains informational: it ignores the
main-tree environment and uses this worktree's environment, without `--active`.

Final verification pass: the requested survivors are killed, normal starts and
record schema remain pinned, the new source probe is long-only, and no mutant
remains. No new in-envelope issue found after cleanup. F3 remains at the seat;
F4/F8 are explicit obligations for the later report, not claimed completed.
This is one logical review-cleanup turn; no instrument or footage run, whole
suite, harness gate, dependency change, commit or AD-3 decision was made here.

## Turn 4 -- GX011625-long analyse failure

Diagnosis-only turn on `45bca4db`, per generation 37's step 0. STOP / YIELD
before the instrument fix, Reviewer A round-2 test cleanup and completion
report. No instrument or test source was edited. The dispatcher must commit
this ledger; this sandbox cannot write `.git`.

### Finding and exact failing call

**MAJOR, confirmed, experiment blocker; pre-existing instrument diagnostic,
not a demonstrated shipped-product defect.** In `run_experiments`
(`tools/statistics_experiments.py:994-1007`), the first method is
`ancuti2018`. After its constant reference and unsmoothed, staged and flat
sequences, the `flicker` loop reaches `label="linear_trend"`. Its series is
`temporal.linear_trend(loaded.raw[name])`. `_signals` selects
`temporal.at(series, index)` and calls `temporal.render`. At zero-based frame
542, the supplied N{} bounds are exactly the pair in the failed GPU log:

| Method | First invalid index | PTS ticks (time base 1/30000) | PTS seconds | Fitted low | Fitted high |
|---|---|---|---|---|---|
| ancuti2018 (the actual failure) | 542 | 8020012 | 267.3337333333333 | -0.0010379406363364915 | -0.0011621024076525072 |
| c3 (would fail later if only Ancuti were skipped) | 542 | 8020012 | 267.3337333333333 | -0.0010472760167360845 | -0.0012093584930396722 |

Both methods' fitted bounds cross on **57 frames, indices 542..598**, ticks
8020012..8076068, PTS 267.3337333333333..269.2022666666667 s. There are 599
frames in each long excerpt. This failure precedes the first method's
`staged/flat done` print, the entire long window study, and the robust study.
It is not a candidate smoother/window, staged or flat failure, or a failure
of the constant reference.

The refusal is specifically **the prototype's**
`tools/prototype/pipeline.py:202-237` `check_statistics`, reached from
`temporal.render` -> `prototype.pipeline.correct` (check at line 867), before
any correction on the rejected frame. The dispatch's attribution to product
`fusion._checked_bounds` is corrected by this source trace and the exact
message reproduction. That product function's message starts `bounds has
low ...`; the observed message starts `supplied normalisation_bounds has
low ...`. The prototype pipeline does not delegate this render to product
fusion code.

### Cause: unconstrained independent lines, not inverted measurements

`tools/prototype/temporal.py:413-431` fits each scalar independently with
`np.polyfit(index, values, 1)` and evaluates the fitted line at every excerpt
frame. It does not constrain one scalar against another. For GX011625-long,
with `i` the zero-based excerpt index:

```text
Ancuti low(i)  = -0.03990916575068024 + 0.00007171812751723938 * i
Ancuti high(i) =  0.05299684262503532 - 0.00009992425282783732 * i
c3 low(i)     = -0.03959069969501710 + 0.00007111332781970666 * i
c3 high(i)    =  0.05305168224606432 - 0.00010011262128985976 * i
```

The scene's measured spread falls toward a narrower positive spread, whereas
the fitted high keeps falling and the fitted low keeps rising until they
cross at the tail. A least-squares fit is not an order-preserving smoother,
even at positions inside its fitting interval. A second calculation using
centred covariance/variance, without `polyfit` or `linear_trend`, reproduces
all four methods/excerpts' fitted bound arrays (atol 1e-16, rtol 1e-13).

The actual raw bounds at the failing Ancuti frame are
`(-0.005461454689502716, 0.005912245213985423)`, a positive spread of about
0.011374. The proxy at frame 542 has RGB spatial standard deviations
`[0.0448529225, 0.0428661717, 0.0456989876]`; it is not an exactly flat
frame. Tiny negative fitted endpoints do not establish collapsed measured
bounds. No saved raw, comparison-staged or comparison-flat pair crosses:

| Excerpt | Method | Minimum raw spread | Minimum staged Gaussian 1 s spread | Minimum flat Gaussian 1 s spread | Minimum fitted-line spread |
|---|---|---|---|---|---|
| GX011627-long | ancuti2018 | 0.030496441126 | 0.032372232246 | 0.032373572726 | 0.085847987444 |
| GX011627-long | c3 | 0.029607575685 | 0.031269948159 | 0.031271040903 | 0.081369453976 |
| GX011625-long | ancuti2018 | 0.009362280667 | 0.009856560414 | 0.009856512775 | -0.009736135071 |
| GX011625-long | c3 | 0.009257019162 | 0.009777220923 | 0.009777347919 | -0.009750735626 |

All four constant-reference pairs are ordered too. `git log -1 -S
'trend = temporal.linear_trend' -- tools/statistics_experiments.py` identifies
`2feea7fc feat(wp1.4): drift floor, render differences and bound step in the
experiments` as the construction's origin. The new long path exposes this
existing auxiliary-diagnostic limitation; it did not introduce the fit.

### Product analysis / smoothing check

The shipped analysis measures fusion `bounds` together as two ordered
percentiles (`src/clearwater/methods/ancuti_fusion.py:226-243`,
`fusion.normalisation_bounds` at `src/clearwater/methods/fusion.py:101-135`).
Both method stage declarations smooth the `bounds` array
(`ancuti_fusion.py:106-107,134-135`). `AnalysisStore.smooth` and `smooth_at`
pass that array to `smooth_series` (`src/clearwater/analysis/store.py:550,601`),
not to the prototype's independent linear fit. The product's default
`median_gaussian`, and its `gaussian`, preserve ordered bounds: the running
median is monotone on the same frame sets, followed by identical nonnegative
normalised Gaussian weights for low and high, with the same held endpoints.
Staging re-measures ordered percentiles before each such smoothing. This
mechanism cannot cause the observed fitted-line crossing from ordered data;
the measured spreads here are also far above floating-point roundoff.

Read-only CPU checks on both chapters and both methods found zero crossings
in 128 product `smooth_series` cases: raw proxy bound pairs and the saved
staged fusion measurements, each at 0.5 / 1 / 2 / 4 s for all four product
kinds. All 48 prototype flat candidate series were ordered as well. These
are smoothing probes on saved prototype measurements, not a run of the full
product analysis or a claim of product/prototype pixel identity. In
particular, step-aware kinds have component-dependent weights; the common
weight order-preservation argument applies to Gaussian/median-Gaussian,
not generally to those experimental kinds. They did not cross on the probed
data. No product defect is confirmed by this failure.

### Smallest proposed in-envelope fix (not implemented; ruling required)

On the **long path only**, preflight the auxiliary `linear_trend` bounds
before `_signals`. When any `low > high`, mark that method's entire
`flicker.linear_trend` diagnostic unavailable and continue to the actual
window study. Record a reason and every affected frame's index, PTS ticks,
PTS seconds, fitted low and fitted high (57 entries for each method here).
Emit no numeric whole/interior trend level for an unavailable sequence.
Do not sort, clamp, replace or silently discard invalid samples in a
reported numeric metric. This preserves the meaning of a pure linear-drift
diagnostic and exposes why it could not be measured.

The guard must cover both methods, leave the default path's behavior and
record schema unchanged, and leave the successful long trend record unchanged
when the preflight passes. GX011627-long has no crossed fit, so this proposal
changes none of its existing figures. Reference rendering, unsmoothed/staged/
flat comparisons, candidate smoothing, per-step arrays, reach accounting and
robust study remain untouched. This resolves the reproduced refusal; a full
successful analysis is still to be observed at the dispatcher's seat after
the fix is ruled, implemented and tested.

**Required re-run after that ruling/fix:**
`uv run python tools/statistics_experiments.py analyse --long` alone, at the
dispatcher's seat in its hardware window. Extraction stands; neither extract
nor render is needed. The CLI will analyse both excerpts again. Compare
GX011627-long's regenerated numeric results against its durable successful
records; this cell has not run or scheduled that phase.

### Evidence, verification and handoff

Inputs: durable copies under
`C:\Users\rwsmy\clearwater-review-evidence\wp-dr25\runs\`, including the failed
analysis log, and a read-only `np.load(..., mmap_mode="r")` view of
`C:\Users\rwsmy\clearwater\work\wp-dr25\GX011625-long\proxies.npy`.
All eight excerpt/raw/staged/flat JSON files in the durable copies match
their current main-tree counterparts by SHA-256; hashes are in the probe log.
The proxy mapping reports mode `r`, `writeable=False`. No frame was rendered
by this probe and no file was written under the main-tree work or footage
folders.

Scratch evidence (under this worktree's ignored `work/`, not committed):
`cdr25-4-diagnose.py`, `cdr25-4-diagnose.log`, `cdr25-4-diagnose.exit`, and
`cdr25-4-GX011625-long-{ancuti2018,c3}-crossed.json` (all affected frames).
The dispatcher can preserve these in its evidence folder. Exact final probe:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
Remove-Item Env:VIRTUAL_ENV -ErrorAction SilentlyContinue
uv run python work/cdr25-4-diagnose.py > work/cdr25-4-diagnose.log 2>&1
$probeExit = $LASTEXITCODE
Set-Content -LiteralPath work/cdr25-4-diagnose.exit -Value $probeExit
exit $probeExit
```

Observed exit 0 and final summary:
`DIAGNOSIS_PROBE_COMPLETE product_smoothing_cases 128 prototype_flat_cases 48`.
The two expected `ValueError` traces are caught reproductions, with the
Ancuti message exactly matching the failed GPU log. An initial invocation
returned shell exit 1 while producing the probe output; uv's inherited
`VIRTUAL_ENV` warning was surfaced as PowerShell `NativeCommandError`.
The final invocation clears only that process's inherited environment value
and completes without that warning; it does not select the main environment.

| Suspected | Confirmation / rejection | Disposition |
|---|---|---|
| Candidate staged smoothing or constant reference crosses. | Saved raw/staged/flat and reference pairs are ordered; the failing exact pair comes from the fitted trend before any candidate print. | Rejected for this failure. |
| The auxiliary independent linear fit crosses near the tail. | Exact logged pair reproduced at frame 542; centred-OLS calculation independently agrees; both methods cross on 542..598. | Confirmed MAJOR; proposed long-only unavailable diagnostic, pending CHARC ruling. |
| Product default smoothing can create the same crossing. | Product call trace uses medians/common positive Gaussian weights, not a line fit; 128 product smoothing probes on saved data have no crossing. | Rejected as the source of this failure; no full product analysis claimed. |
| A truly collapsed source frame caused the negative pair. | Raw spread at frame 542 is positive, about 0.011374; all raw spreads exceed 0.009 on GX011625-long. | Rejected; fitted-line overshoot is the cause. |

No pytest, GPU job, extract/analyse/render phase, lint or mypy gate ran in
this diagnosis-only turn. Reviewer A round 2 is reported CONVERGED by the
dispatcher; its F1/F3 cleanup and the report remain for the later turn, not
claimed complete here. No AD-3 decision is made. Only this owned ledger is
changed; product, prototype, instrument, tests and dependencies are untouched.

Depth at turn-4 (diagnosis) end: 131,886 input tokens of 258,400 (driver footer, FRESH session 01a1a0cb-94f7-71d2-a4c3-34ad022b488a, 2026-11-03 turn 4).

## Turn 5 (R1 fix, Reviewer A round 2 F1 / F3)

Base: `6dfccdfc`. This turn implements CHARC's binding R1 ruling
(`e09d10970e1fcdfd`, 2026-11-03 09:52Z) and the terminating Reviewer A round-2
test cleanup. R2 (truncated fit) and R3 (order-preserving fit) were rejected
because they change the diagnostic's quantity; neither is implemented.
The completion report waits for the dispatcher's analysis re-run.

### R1 behavior and exact schema

In `run_experiments`, only for `long=True` and `label="linear_trend"`,
preflight the fitted low/high arrays before `_signals`. If any low exceeds
its high, skip rendering the entire method's trend and write this row at
`flicker.<method>.linear_trend`:

```json
{
  "available": false,
  "reason": "fitted normalisation_bounds.low exceeds normalisation_bounds.high",
  "crossing": {
    "count": 2,
    "frames": [
      {"index": 6, "pts_ticks": 6006, "pts_seconds": 0.2002, "low": 7.25, "high": -7.25},
      {"index": 7, "pts_ticks": 7007, "pts_seconds": 0.23356666666666667, "low": 15.5, "high": -15.5}
    ]
  }
}
```

This is the synthetic witness, with fitted bounds shown to display precision,
not a real-footage record. `index` is zero-based excerpt position. PTS values
come from the corresponding excerpt frame. `count` is an integer; `frames`
contains EVERY crossed pair in order, with its actual fitted float values.
No numeric trend flicker fields are emitted for an unavailable row. Equality
is valid: only `low > high` triggers this row. No samples are sorted, clipped,
replaced or re-fitted. A noncrossing long trend keeps the previous complete
row, without an added `available` key. The default path bypasses the guard.
The guard and its docstring are the only instrument changes.

Both-method synthetic tests use the real independent fit on eight ordered
measurements: low `[-100,-1,-1,-1,-1,-1,-1,-1]`, high its negative. The fit
crosses on indices 6/7 (low 7.25/15.5, high -7.25/-15.5). The signal boundary
asserts if a crossed fit is even submitted to rendering. The test checks
the persisted unavailable schema, both positions, times, count and fitted
values; every other result is compared whole against fixed pre-R1 source
from `git show 6dfccdfc:tools/statistics_experiments.py`. The valid long case
compares the whole result, including both complete 599-step trend rows,
against that same revision.

### Reviewer A round 2 and cumulative ledger

The supplied A2 verdict is CONVERGED, all seven claims HOLD, 18/20 mutants
killed, on `2e40eb85` (same content later rebased to `45bca4db`). The
dispatcher owns both Claude review nets. No new pass ran in this cell and
the withheld transcript's filename/model version was not supplied.

| Round | Critical | Major | Minor | Advisory | In / out of envelope | NEW / REOPENED | Reverts | Fix surface | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| 0 prerequisite audit | 0 | 2 | 1 | D3 fit observation | All in | All new / 0 | 0 | Ruled instrument changes in turn 2 | CHARC ruled at `0f2d19c4` |
| A1 | 0 | 0 | 2 | 6 | F1-F7 in; F8 out | 8 / 0 | 0 permanent | Instrument and tests; no shipped product code | `NO_NEW_CRITICAL_MAJOR`; cleanup in turn 3 |
| A2 | 0 | 0 | 1 | 3 | F1-F4 in | 4 / 0 | 0 permanent | Tests: F1/F3; report: F2/F4 owed | CONVERGED; test cleanup in turn 5 |

The pre-existing instrument failure and separately ruled R1 fix are not
invented as an additional reviewer finding or round. All temporary mutants
and historical source substitutions were restored, not permanently reverted.

| Finding | Classification | Disposition |
|---|---|---|
| A2 F1 | MINOR, in | FIXED: five default JSON documents pinned whole to WP1.4 base source; Mj/Mk killed. |
| A2 F2 / A1 F4 | ADVISORY, report | CARRIED: use each candidate's own interior/counts, and re-trim unsmoothed per-step arrays to its slice. Top-level margin/steps describe only `flicker`. |
| A2 F3 | ADVISORY, in | FIXED: removed `raising=False` from `run_ffprobe` patch. The current module uses normal attribute-existence checking; only the historical base, which has no additional probe, skips installing that stub. |
| A2 F4 | ADVISORY, report | CARRIED: long references use 20 s mean statistics, old references 6 s means; re-trimming gives comparable, not identical, quantities. |

A1 F8's under-20 s chapter limit and the supplied extraction resources remain
report obligations. CHARC's required R1 qualification also carries forward:
crossing is an independent-fit property over a narrowing 20 s excerpt, not
a product defect; product analysis never fits this trend, no saved measured/
staged/flat pair crosses, and the refusal is prototype `check_statistics`.

### Default golden provenance and exclusions

Goldens are generated at test runtime from immutable source obtained by
`git show 0cafb374:tools/statistics_experiments.py`, executed in a separate
module. They never come from the working source. Base and current receive
identical synthetic inputs, stubs and per-test paths. Golden JSON files are
read and removed before the current invocation, preventing a missing write
from passing through a stale file.

**Only top-level `written` is excluded** in each document. No other field,
path, array, numeric value or definition is normalized. The extraction timer
is console output and needs no document exclusion. The pinned documents are
`excerpt.json`, `statistics-raw.json`, `statistics-staged.json`,
`statistics-flat.json`, and `results.json`. Extraction covers fitting and
short-unclamped durations. Default analysis also covers both methods' crossed
fits with the historical signal stub: leaking R1 out of `--long` changes
their whole recorded payload and fails.

### RED / GREEN and mutation evidence

All pytest invocations use process-local `PYTHONPATH=scripts`, the required
`sandbox_mkdir_shim`, and `no:cacheprovider`. Before instrument edits, initial
RED exited 1: `2 failed, 18 passed in 1.87s`; both long crossing tests failed
at `attempted to render a crossed trend`. Initial GREEN exited 0:
`20 passed in 1.49s`.

After strengthening the witness and adding default crossing controls, the
final tests were rechecked on the exact instrument from `6dfccdfc`. Final
RED exited 1: **`2 failed, 20 passed in 1.98s`**, again both
`test_long_crossed_trend_is_unavailable_without_rendering_or_changing_other_records`
parameters, at the intended assertion. The driver restored the instrument
in `finally` and recorded `RESTORED True`. Final GREEN exited 0:
**`22 passed in 2.09s`**.

| Mutant | Temporary change | Final failed check (pytest exit 1) |
|---|---|---|
| Mj | Add `document["long"] = long` to `results.json`. | `test_default_window_study_keeps_one_method_and_fixed_margin`: whole `results.json` differs; `1 failed in 1.24s`. |
| Mk | Add `document["start_clamped"] = False` to `excerpt.json`. | `test_default_extract_keeps_start_and_record_schema[fits]` and `[short-unclamped]`: whole `excerpt.json` differs; `2 failed in 0.90s`. |
| Mtrend | Remove `long and` from the guard, changing default trend handling. | `test_default_crossed_trend_record_matches_wp14_base[ancuti2018]` and `[c3]`: whole `results.json` differs; `2 failed in 0.87s`. |

The driver command was `uv run python work/cdr25-5-mutations.py`, output
`work/cdr25-5-mutations.log`. It launches the exact worktree interpreter
selected by `uv run`, `.venv/Scripts/python.exe -m pytest`, with the shim
and environment above. Exact pytest argument lists (all output to individual
`work/cdr25-5-<name>.log` files, exit codes in `.exit`):

```text
python -m pytest -q -p sandbox_mkdir_shim -p no:cacheprovider tests/test_tools_statistics_experiments.py::test_default_window_study_keeps_one_method_and_fixed_margin --timeout 120 --basetemp=work/cdr25-5-mj
python -m pytest -q -p sandbox_mkdir_shim -p no:cacheprovider tests/test_tools_statistics_experiments.py::test_default_extract_keeps_start_and_record_schema --timeout 120 --basetemp=work/cdr25-5-mk
python -m pytest -q -p sandbox_mkdir_shim -p no:cacheprovider tests/test_tools_statistics_experiments.py::test_default_crossed_trend_record_matches_wp14_base --timeout 120 --basetemp=work/cdr25-5-mtrend
```

Final restored instrument SHA-256, also independently matched by
`Get-FileHash` after checks:
`9bf859fd6a2f3cc9066d5c7201ca253dd0ee124d3b2f9ea505cd0d1456767908`.
No mutant is committed. The final RED driver command was
`uv run python work/cdr25-5-red-recheck.py`, output
`work/cdr25-5-red-recheck.log`. Its child uses the same interpreter/shim,
the full new module, `--timeout 120`, and
`--basetemp=work/cdr25-5-red-final`. Pytest log/exit:
`work/cdr25-5-red-final.log` / `.exit`.

### Final development checks

| Check | Final observed summary (exit 0) | Worktree log |
|---|---|---|
| Synthetic module after restoration and formatting | `22 passed in 2.09s` | `work/cdr25-5-green-final.log` |
| Existing importers, selected non-hardware tests (once) | `85 passed, 4 deselected, 1 warning in 3.46s` | `work/cdr25-5-importers.log` |
| Whole-tree Ruff | `All checks passed!` | `work/cdr25-5-ruff-final.log` |
| Whole-tree format check | `312 files already formatted` | `work/cdr25-5-format-final.log` |
| Whole configured mypy scope | `Success: no issues found in 156 source files` | `work/cdr25-5-mypy-final.log` |

Commands, with stdout/stderr redirected to the corresponding logs:

```powershell
$env:PYTHONPATH='scripts'
$env:PYTHONDONTWRITEBYTECODE='1'
Remove-Item Env:VIRTUAL_ENV -ErrorAction SilentlyContinue
uv run pytest -q -p sandbox_mkdir_shim -p no:cacheprovider tests/test_tools_statistics_experiments.py --timeout 120 --basetemp=work/cdr25-5-green
uv run pytest -q -p sandbox_mkdir_shim -p no:cacheprovider tests/test_tools_statistics_experiments.py --timeout 120 --basetemp=work/cdr25-5-green-final
```

Initial RED used the same module/options and `--basetemp=work/cdr25-5-red`.
The importer invocation additionally set `CUDA_VISIBLE_DEVICES=-1` inside
its own process, proactively using the confirmed turn-2 import-time CUDA
workaround while another cell renders. No new collection stall occurred.
The warning is the existing CuPy undetected CUDA-path warning; no selected
test skipped. It preceded only formatting and additional test controls,
not another behavioral instrument change, so it was not repeated.

```text
uv run pytest -q -p sandbox_mkdir_shim -p no:cacheprovider tests/test_footage_locator.py tests/test_prototype_temporal.py -m "not gpu and not footage and not gui and not slow" --timeout 120 --basetemp=work/cdr25-5-importers
uv run ruff check .
uv run ruff format --check .
uv run mypy
```

Initial static checks found three overlong lines and formatter changes;
these were corrected before the final passing checks. No full suite,
harness gate, GPU/footage test or instrument phase was launched here.

### Re-run instructions and verification loop

At the dispatcher's seat, from this worktree with its existing configuration,
in its GPU window, run only:

```text
uv run python tools/statistics_experiments.py analyse --long
```

**No folder or record needs moving aside or deleting.**
`OutputRoots.write_text` / `write_bytes` (`tools/lookcheck/frames.py:260-294`)
check the target then overwrite ordinary existing files. Existence alone is
not refused. The active refusal rules are paths outside the output root,
inside footage, and existing output files with multiple hard links
(`check_output_path`, lines 164-197). Analysis replaces staged/flat JSON,
results JSON and flicker PNG for both excerpts, reading the existing
excerpt/raw JSON and proxies. Extraction stands. Preserve the existing
durable successful GX011627-long copies for the numeric identity comparison.
This cell touched neither main-tree excerpt folder.

| Suspected | Independent evidence | Disposition |
|---|---|---|
| Crossed fits still reach rendering. | Both methods fail RED at the signal boundary, pass GREEN with two crossings recorded, and retain other results against fixed pre-R1 source. | Fixed under `--long`; real GPU completion remains for the seat. |
| R1 changes defaults or valid long trends. | Five default documents match fixed WP1.4 source; default crossing cases match it; valid long result matches pre-R1 whole. All three mutants fail named assertions. | Rejected after controls. |
| Stale golden output hides a missing current write. | Golden JSONs are removed before the current invocation; exact file sets and payloads are compared. | Rejected on the tested synthetic surface. |
| Mutant or scope/style drift remains. | Restored hash matches; final synthetic module, whole-tree Ruff/format and configured mypy pass; only the three owned files changed. | No new unresolved in-envelope implementation finding. |

One logical ruled fix and its controls are bundled in this turn. No new
dependency, frozen interface, product/prototype change, footage write,
main-tree work write, AD-3 decision, mailbox post or git commit was made.
Transient evidence stays under this worktree's ignored `work/`; its durable
preservation and the analysis re-run are the dispatcher's responsibility.
The report and its obligations above remain for the next turn after that run.

Depth at turn-5 end: 174,724 input tokens of 258,400 (driver footer, session 01a1a0cb, 2026-11-03 turn 5).

## Turn 6 (report)

Fresh report session on `68caf100`, per orchestrator generation 38. The
previous session's supplied turn-5 depth is recorded above; it is not this
session's depth. Only the new completion report and this ledger are changed.
No instrument/test edit, GPU phase or commit was performed by the cell.

### Cumulative round ledger

| Round | Critical | Major | Minor | Advisory | In / out of envelope | NEW / REOPENED | Reverts | Fix surface | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| 0 prerequisite audit | 0 | 2 | 1 | D3 fit observation | All in | All new / 0 | 0 | Ruled instrument changes in turn 2 | CHARC ruled at `0f2d19c4` |
| A1 | 0 | 0 | 2 | 6 | F1-F7 in; F8 out | 8 / 0 | 0 permanent | Instrument/tests in turn 3; report obligations completed in turn 6; no shipped product code | `NO_NEW_CRITICAL_MAJOR` |
| A2 | 0 | 0 | 1 | 3 | F1-F4 in | 4 / 0 | 0 permanent | Tests F1/F3 in turn 5; report F2/F4 in turn 6 | CONVERGED |

No additional reviewer round is invented for the report. Both Claude nets
remain dispatcher-owned; the supplied A2 verdict and withheld transcript
provenance are unchanged. Separately ruled **R1 was fixed in turn 5**;
the successful `68caf100` analysis and report now record its real-footage
consequence. No finding is reopened, no permanent revert and no product-
code fix occurs in this turn.

### Completion report sections

`docs/reports/wp-dr25-staged-run.md` contains:

1. Scope and durable evidence (runs2 only; results hashes).
2. Excerpts and timing (requested/actual starts, stream duration source,
   ticks, rate, frame counts and tags).
3. Interior accounting and read-only audit (per-method/window reach,
   frame/step counts, own slices and WP3.11's strict convention).
4. Flicker levels and the WP1.4 figures (staged/flat own interiors,
   separately matched unsmoothed baselines; Ancuti-only historical study).
5. Ground-2 reading (own-interior and common-step 1 s / 2 s comparisons).
6. Boundary exposure of the original 6 s figures (old PTS re-trims,
   edge-free intersections and changed-reference qualification).
7. Commands and resources (extract and both analyses, including failure).
8. Limits and deep-step context (under-20 s limit, R1 crossings,
   WP3.11 span and edge-free counts, no rerun).
9. Verification and acceptance transfer (checks, verification loop,
   ownership and outstanding seat actions).

Report obligations discharged: A1 F4 / A2 F2 use each candidate's own
`interior`, reach and counts and re-trim unsmoothed arrays to its slice;
A2 F4 explains 20 s versus 6 s reference means at the historical
comparison; A1 F8 excludes under-20 s chapters; A1 F3 gives the supplied
resource record; CHARC R1 gives both 57-frame exceptions, their first
crossing and the required prototype/product qualification.

### Record audit and reading

Read-only inputs: all 14 files under
`C:\Users\rwsmy\clearwater-review-evidence\wp-dr25\runs2\`.
Scratch script/log/exit and hashes are in this worktree's ignored `work/`:
`cdr25-6-audit.py`, `.log`, `.exit`, and `cdr25-6-record-hashes.json`.
The script checks both methods and all 12 candidate labels, all candidate
reach/count/slice arithmetic, per-step `all`/`interior` means, tick identity
in the saved raw/staged/flat and per-stage measurements, ordered saved
N{} bounds, and the absence of any other unavailable row. Before/after
SHA-256s of all 14 evidence files match. Observed exit 0:

```text
AUDIT_PASS sequence_records 110 max_mean_abs_error 2.7755575615628914e-17 unchanged_files 14
```

Both excerpts have 599 frames. Staged 2 s counts are 479 frames / 478
steps for c3 and 419 / 418 for Ancuti; 4 s counts are 359 / 358 and
239 / 238. GX011625's only unavailable rows are the two `linear_trend`
rows: exactly 57 crossings each, indices 542..598, first ticks 8020012.
No dispatch STOP condition was found, so the report was written after
the audit passed.

Own-interior 1 s -> 2 s staged levels (percent decrease computed at
recorded precision):

| Method | Chapter | 1 s | 2 s | Decrease |
|---|---|---|---|---|
| c3 | GX011627 | 0.032020 | 0.024577 | 23.24% |
| c3 | GX011625 | 0.073744 | 0.066203 | 10.23% |
| ancuti2018 | GX011627 | 0.117788 | 0.101864 | 13.52% |
| ancuti2018 | GX011625 | 0.109015 | 0.100218 | 8.07% |

Direction holds in all four cases; an approximately 20% gap does not
hold uniformly. A matched 2 s-interior control also favors 2 s (c3
24.62% / 14.54%, Ancuti 15.03% / 16.16%). Old-frame re-trims do not
isolate boundary bias, because references differ and GX011625's left
boundary remains in the full old span. The report states those limits;
AD-3's status and DR-25 (3) disposition remain CHARC's accept actions.

### Light verification

Each runner's output was redirected to the named log; matching `.exit`
files record exit 0. No code changed, so importers were not rerun.

| Check | Observed summary | Worktree log |
|---|---|---|
| Required synthetic module, shim loaded | `22 passed in 4.53s` | `work/cdr25-6-green.log` |
| Whole-tree Ruff | `All checks passed!` | `work/cdr25-6-ruff.log` |
| Whole-tree format check | `312 files already formatted` | `work/cdr25-6-format.log` |
| Whole configured mypy scope | `Success: no issues found in 156 source files` | `work/cdr25-6-mypy.log` |

Final scratch document check: `work/cdr25-6-report-check.py` exited 0,
with output `work/cdr25-6-report-check.log`:

```text
REPORT_CHECK_PASS table_rows 31 ASCII_LF 2 scope 2 links_exist True diff_check clean
```

It independently matches all 12 long-run flicker rows, four ground-2
rows, nine count/slice rows and six historical re-trim rows to the durable
data; confirms ASCII/LF, local link targets and the two-file ownership
surface; and runs `git diff --check`. Git emitted only the prospective
LF-to-CRLF warning from its configuration; on-disk CR-byte counts are zero.

Exact commands are in the report's section 9. Pytest uses process-local
`PYTHONPATH=scripts`, `sandbox_mkdir_shim`, `no:cacheprovider`, timeout
120 and `--basetemp=work/cdr25-6-green`. The inherited main-tree
`VIRTUAL_ENV` was cleared only in these processes. Static checks use
this worktree's uv environment. No full gate, harness gate, serial test,
GPU work or extract/analyse/render phase was run by this cell.

| Suspected issue | Independent confirmation / rejection | Disposition |
|---|---|---|
| Saved interiors or candidate coverage contradict the instrument. | Re-trim all available sequence records; compare counts/slices to literal radii and staged multipliers; both methods/all windows present. | Rejected; no instrument defect or STOP. |
| An unavailable row violates R1. | Recursive scan finds only GX011625's two trends; exactly 57 crossed pairs per method with aligned ticks. | Expected limitation confirmed; reported with CHARC's wording. |
| Unsmoothed baselines use a different step population. | Re-trim separately to every candidate's own slice; add common-2 s-slice cross-window control. | Addressed in report, no code change. |
| Old/new differences measure boundary bias alone. | Match original ticks, intersect with long edge-free slice, and trace constant reference construction to each span's raw mean. | Rejected; changed-reference and remaining-left-edge limits stated. |
| The report omits carried review obligations or crosses ownership. | Final section/figure/obligation audit and path-limited diff check. | Report and ledger only; all carried report obligations covered. |

Final verification pass found no new in-envelope issue. Binding locks
honored: product/prototype and frozen interfaces unchanged; no dependency,
OS-specific product code or default change; ASCII/LF owned artifacts;
no footage/evidence/main-tree work write, deletion, mailbox post or `.git`
mutation. The durable records were only read; scratch stays in-worktree.
No deviations or new questions. Reviewer B and the specified final gate
(parallel/serial, harness, collection identity) remain dispatcher work;
CHARC owns the register/AD-3 note and WP1.4 erratum pointer.

Depth at turn-6 end: 133,949 input tokens of 475,000 (driver footer, FRESH session 01a1a157-6f2b-7391-9242-5fa191ebfca1, 2026-11-03 turn 6).

## Turn 7 (Reviewer B remediation)

Resumed session on `83ad9d69`, after the dispatcher's rebase onto main
`6393cb35`. The supplied turn-6 depth is recorded above. This is Reviewer
B's single remediation, not a new reviewer round or a new instrument run.
The dispatcher-seat Claude B verdict on `83ad9d69` is
`NEW_CRITICAL_MAJOR_FOUND`; transcript withheld. B independently recomputed
the report figures without a mismatch and supplied seven findings with
binding dispositions. The dispatcher owns the one B rerun and final gate.

### Seven dispositions

| Finding | Severity / envelope | Confirmation and disposition |
|---|---|---|
| B1 | MAJOR, in | FIXED. `_revision_runner` now takes a full blob id, asserts `git cat-file -t` succeeds and returns `blob`, then reads `git cat-file blob`. Both fixtures use fixed blob constants, with no commit/path or branch-relative lookup. Two direct-blob loading cases and a missing-blob diagnostic case cover this contract. The guard names the missing/non-blob object and explains the history prerequisite. |
| B2 | MINOR, in | FIXED. The report identifies each analysis by its full instrument blob and commit subject. Old commit names appear only as parenthesized pre-rebase labels beside a stable blob; the code used for each run is no longer identified solely by an unreachable commit. |
| B3 | ADVISORY, in | FIXED. The lead and section 5 explicitly identify the original approximately-one-fifth claim as Ancuti-only. The new c3 comparison is independent, with its first-chapter gap larger and second-chapter gap smaller than that historical margin; no c3 failure of an original c3 claim is implied. |
| B4 | ADVISORY, in | FIXED in tests. Each method has a trend with exactly one equal low/high pair at index 3. Equality is planted after the real fit to avoid numerical pseudo-ties. The ordinary signal boundary rejects actual crossed pairs, and the test requires a complete available seven-step trend row. M8 now fails both method cases. The executable guard remains strict `>`, matching prototype `check_statistics`. |
| B5 | ADVISORY, in | FIXED docstring only. `run_experiments` says an invalid trend is recorded unavailable "instead of rendering it". Byte comparison to the analysed instrument confirms this is the only instrument change; no executable or record-writing behavior changes. |
| B6 | ADVISORY, out | NO CODE CHANGE. The report's Limits now states `_duration_source` assumes `streams[0]`; an empty list is outside this envelope because `probe_stream` succeeded first. No new malformed-probe handling is added. |
| B7 | ADVISORY, accepted coverage limit | NO CHANGE. The default-extract golden covers only the GX011625 spec; this diff touches no full-frame extraction code. |

### Rebase-stable source identity

The three `git cat-file -t <id>` commands returned `blob` (captured in
`work/cdr25-7-blobs.log`):

| Role | Instrument blob |
|---|---|
| Fixed WP1.4 base / `base_runner` | `74019b47e56bb1b1d7d0ad0c15b3615150ba8925` |
| Pre-R1 diagnosis / `pre_r1_runner`; also the failed first analysis | `5bada347da89885c93453b57a2cc03053e4de4c2` |
| R1-fixed successful second analysis | `e346ca303cadf719c6b1f30eb9aaeaa80dcdbe61` |

`git rev-parse 8abb3869:tools/statistics_experiments.py` independently
returned the pre-R1 blob above. The dispatcher supplied the historical
mapping: first analysis pre-rebase `45bca4db` -> `8abb3869`, successful
second analysis pre-rebase `68caf100` -> `056d9d74`. The report includes
both exact commit subjects, with blobs as the run identifiers. The old
ledger entries are chronological records, not fixture source pins.

The new valid-blob test restores any existing `sys.modules` registration
through `monkeypatch`, so it does not remove a live historical fixture's
module when test scheduling changes. The missing-blob case uses the null
object id; it does not remove or rewrite any git object/ref. The existing
whole-document goldens and pre-R1 comparisons retain their original data
and exclusions; only their source-addressing mechanism changes.

### RED, equality and M8

All pytest runs use process-local `PYTHONPATH=scripts`,
`PYTHONDONTWRITEBYTECODE=1`, `sandbox_mkdir_shim`, `no:cacheprovider` and
timeout 120. The inherited `VIRTUAL_ENV` was cleared only in the runner
process. Every runner's stdout/stderr is under this worktree's ignored
`work/`; no log or temporary file was written to the main-tree work root.

Before changing the loader, the new blob/guard/equality selection ran
against the current instrument and old test helper:

```text
uv run pytest -q -p sandbox_mkdir_shim -p no:cacheprovider tests/test_tools_statistics_experiments.py -k "revision_runner or equal_trend_bounds" --timeout 120 --basetemp=work/cdr25-7-red
```

Observed exit 1: **`3 failed, 2 passed, 22 deselected in 1.29s`**
(`work/cdr25-7-red.log`). The two direct-blob tests failed because the
old loader appended `:tools/statistics_experiments.py` to a blob id;
the missing-blob test failed because that loader emitted a subprocess
failure rather than the required clear assertion. The two tie cases
**passed on the current head**, as expected: the instrument already uses
strict `>` and equality is valid. This is not a claim that equality
needed an executable fix.

The one-off M8 probe temporarily replaced only
`np.flatnonzero(lows > highs)` with `np.flatnonzero(lows >= highs)`.
Its child command was:

```text
python -m pytest -q -p sandbox_mkdir_shim -p no:cacheprovider tests/test_tools_statistics_experiments.py -k equal_trend_bounds --timeout 120 --basetemp=work/cdr25-7-m8
```

The child used the exact interpreter selected by `uv run python -` and
the environment above. Observed pytest exit 1:
**`2 failed, 25 deselected in 5.40s`**, both
`test_long_equal_trend_bounds_remain_available` method cases, because
the trend row was incorrectly unavailable. The inline driver restored
the instrument bytes in `finally`, printed **`RESTORED True`**, and
exited 0 after asserting the expected mutant failures. Logs/exit files:
`work/cdr25-7-m8.log`, `.exit`, and `work/cdr25-7-m8-driver.log`, `.exit`.
No mutant is retained or committed; this temporary restoration is not
a permanent code revert.

### GREEN and light checks

| Check | Final observed summary (exit 0) | Worktree log |
|---|---|---|
| New synthetic module | `27 passed in 2.16s` | `work/cdr25-7-green.log` |
| Three previously commit-dependent pre-R1 tests, explicitly selected | `3 passed in 1.12s` | `work/cdr25-7-pre-r1.log` |
| Existing importers, once | `85 passed, 4 deselected, 1 warning in 7.37s` | `work/cdr25-7-importers.log` |
| Whole-tree Ruff | `All checks passed!` | `work/cdr25-7-ruff.log` |
| Whole-tree format check | `312 files already formatted` | `work/cdr25-7-format.log` |
| Whole configured mypy scope | `Success: no issues found in 156 source files` | `work/cdr25-7-mypy.log` |

The explicit three-test selection names the two parametrized crossing
cases and `test_long_ordered_trend_keeps_full_record_unchanged`. The
full-module initial GREEN was 27 passed in 2.82 s; it was repeated after
isolating the direct-blob test's module registration, giving the final
result above. The initial format check requested one call-layout change;
it was fixed before the final checks. Importers were not repeated because
that later change affects only the new synthetic test's module cleanup.

Exact commands, each redirected to its log (pytest environment as above):

```text
uv run pytest -q -p sandbox_mkdir_shim -p no:cacheprovider tests/test_tools_statistics_experiments.py --timeout 120 --basetemp=work/cdr25-7-green
uv run pytest -q -p sandbox_mkdir_shim -p no:cacheprovider tests/test_tools_statistics_experiments.py::test_long_crossed_trend_is_unavailable_without_rendering_or_changing_other_records tests/test_tools_statistics_experiments.py::test_long_ordered_trend_keeps_full_record_unchanged --timeout 120 --basetemp=work/cdr25-7-pre-r1
uv run pytest -q -p sandbox_mkdir_shim -p no:cacheprovider tests/test_footage_locator.py tests/test_prototype_temporal.py -m "not gpu and not footage and not gui and not slow" --timeout 120 --basetemp=work/cdr25-7-importers
uv run ruff check .
uv run ruff format --check .
uv run mypy
```

Only the importer process additionally set `CUDA_VISIBLE_DEVICES=-1`,
proactively reusing the confirmed turn-2 collection workaround to avoid
an import-time CUDA probe beside the host's batch. No new collection
stall occurred and no selected test skipped. The warning is the existing
CuPy undetected-CUDA-path warning, not a test failure. No GPU/footage
test, full gate, extract/analyse/render phase or harness gate ran here.

### Final verification and cumulative ledger

The inline read-only audit (`work/cdr25-7-audit.log`, exit 0) compares
the current instrument to the successful analysis blob byte for byte,
allowing only the one ruled docstring replacement. All 62 report table
rows match the committed report, except the two instrument-identifier
cells and the corresponding header; all other cells are identical.
Prose figures also match after excluding source identifiers/subjects,
section references and the newly required empty-streams limit line.
Thus no report figure or executable record-writing behavior changed.
The initial prose-token check counted the new section-1 cross-reference;
excluding section references resolved that audit false positive without
changing any measured figure. Final summary:

```text
REMEDIATION_AUDIT_PASS instrument_docstring_only True report_table_rows 62 report_prose_figures_unchanged True ASCII_LF True
```

| Round | Critical | Major | Minor | Advisory | In / out of envelope | NEW / REOPENED | Reverts | Fix surface | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| 0 prerequisite audit | 0 | 2 | 1 | D3 fit observation | All in | All new / 0 | 0 | Ruled instrument changes in turn 2 | CHARC ruled at `0f2d19c4` |
| A1 | 0 | 0 | 2 | 6 | F1-F7 in; F8 out | 8 / 0 | 0 permanent | Instrument/tests in turn 3; report obligations in turn 6 | `NO_NEW_CRITICAL_MAJOR` |
| A2 | 0 | 0 | 1 | 3 | F1-F4 in | 4 / 0 | 0 permanent | Tests F1/F3 in turn 5; report F2/F4 in turn 6 | CONVERGED |
| B1 | 0 | 1 | 1 | 5 | B6 out; other six dispositioned in envelope / accepted coverage | 7 / 0 | 0 permanent | 3 test functions plus loader/fixture pins; 1 report; 1 instrument docstring; no executable product fix | `NEW_CRITICAL_MAJOR_FOUND`; single remediation complete, dispatcher rerun owed |

The three new test functions supply five parameter cases (two blob loads,
one missing-blob guard, two method ties). All seven findings are
dispositioned above; none is reopened. No remaining in-envelope defect
was found in the final verification pass. The only instrument edit is
documentation, so no run-code or record-affecting STOP is triggered.
Owned paths are the instrument, its test module, report and this ledger;
ASCII/LF, diff and scope checks close this turn. No product/prototype,
frozen interface, dependency, footage/evidence file, main-tree output,
git history or mailbox is changed. No new question or deviation is raised.

Depth at turn-7 end: 173,792 input tokens of 258,400 (driver footer, session 01a1a157, 2026-11-03 turn 7; the footer reported 475,000 at turn 6).

## Turn 8 (Reviewer B re-run minor)

Resumed session on `d5650ea8`. Reviewer B's dispatcher-seat Claude rerun
on that candidate returned `NO_NEW_CRITICAL_MAJOR`: all seven earlier
findings closed, every report figure recomputed without mismatch, and
14 of 14 mutants failed the test module. The transcript is withheld;
these are dispatcher-supplied review results, not another cell review.

### Three dispositions

| Finding | Classification | Disposition |
|---|---|---|
| B rerun 1 | MINOR, in envelope | FIXED in report section 9 only. Replaced the stale turn-6 verification state with the final four-file package scope, the fresh 27-test command/result, the turn-7 importers' 85 passed / 4 deselected result, and explicitly dated turn-7 static evidence. Identified the final instrument blob and its sole docstring difference from the second analysis blob, so the saved records stand for the final code. Removed stale two-file package-scope and importer-not-rerun claims; distinguished this turn's two documentation edits from the four-file package. |
| B rerun 2 | ADVISORY, accepted integration constraint | NO CHANGE. Blob pins survive rebases but not a squash merge followed by pruning. The dispatcher states it will fast-forward merge and records that in the accept record; this cell performs no merge or history operation. |
| B rerun 3 | ADVISORY, confirmed ordering | NO CHANGE. The crossing preflight follows the method's reference / unsmoothed / staged / flat renders and runs before any render of the trend series, as ruled. The dispatcher reports records identical across the two runs. |

### Evidence and checks

`git rev-parse HEAD:tools/statistics_experiments.py` returned final blob
`f7a4988f300006c878c4636e022a5336c83960c2`. A read-only byte comparison
against the second analysis's blob
`e346ca303cadf719c6b1f30eb9aaeaa80dcdbe61` allowed only the single
`run_experiments` docstring replacement, "before rendering it" ->
"instead of rendering it", and passed. Output/exit:
`work/cdr25-8-blobs.log` / `.exit`, exit 0:

```text
INSTRUMENT_BLOB_CHECK_PASS f7a4988f300006c878c4636e022a5336c83960c2 only_change run_experiments_docstring
```

The required synthetic module ran **once**, with stdout/stderr redirected
under this worktree's ignored `work/`:

```powershell
$env:PYTHONPATH='scripts'
$env:PYTHONDONTWRITEBYTECODE='1'
Remove-Item Env:VIRTUAL_ENV -ErrorAction SilentlyContinue
uv run pytest -q -p sandbox_mkdir_shim -p no:cacheprovider tests/test_tools_statistics_experiments.py --timeout 120 --basetemp=work/cdr25-8-green > work/cdr25-8-green.log 2>&1
```

Observed exit 0: **`27 passed in 1.96s`**, recorded in section 9 and
`work/cdr25-8-green.log` / `.exit`. Importers were not repeated this
turn; section 9 now correctly quotes their turn-7 result, **85 passed,
4 deselected, 1 warning in 7.37s**, with its command and process-local
GPU-mask explanation. Ruff/format/mypy evidence there is explicitly from
turn 7. No code or test file changed; no static runner or GPU phase ran
this turn.

Final document validation (`work/cdr25-8-final-check.log`) checks ASCII/LF,
`git diff --check`, and exactly the two owned documentation paths. It
also compares report sections 1-8 byte for byte to `d5650ea8`, preserving
every measured figure and historical comparison, and checks the
instrument/test files against HEAD. Only report section 9 and this
ledger change. No report measurement was recomputed or altered.

### Cumulative round ledger

| Round | Critical | Major | Minor | Advisory | In / out of envelope | NEW / REOPENED | Reverts | Fix surface | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| 0 prerequisite audit | 0 | 2 | 1 | D3 fit observation | All in | All new / 0 | 0 | Ruled instrument changes in turn 2 | CHARC ruled at `0f2d19c4` |
| A1 | 0 | 0 | 2 | 6 | F1-F7 in; F8 out | 8 / 0 | 0 permanent | Instrument/tests in turn 3; report obligations in turn 6 | `NO_NEW_CRITICAL_MAJOR` |
| A2 | 0 | 0 | 1 | 3 | F1-F4 in | 4 / 0 | 0 permanent | Tests F1/F3 in turn 5; report F2/F4 in turn 6 | CONVERGED |
| B1 | 0 | 1 | 1 | 5 | B6 out; other six dispositioned / accepted coverage | 7 / 0 | 0 permanent | Three new test functions, loader pins, report, instrument docstring in turn 7; no executable product fix | All seven closed by B rerun |
| Reviewer B re-run | 0 | 0 | 1 | 2 | Minor in; advisories accepted integration/ordering constraints | 3 / 0 | 0 | Report section 9 only; no code/test fix | `NO_NEW_CRITICAL_MAJOR`; minor corrected in turn 8 |

Final verification found no additional issue. No assumptions or new
questions, code/test edits, dependency or frozen-interface changes,
extract/analyse/render rerun, footage/evidence/main-tree output write,
git history mutation or mailbox post occurred. Only the report and
ledger are handed back; the dispatcher owns the final gate and accept.

Depth at turn-8 end: 185,072 input tokens of 258,400 (driver footer, session 01a1a157, 2026-11-03 turn 8).
