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
