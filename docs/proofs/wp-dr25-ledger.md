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
