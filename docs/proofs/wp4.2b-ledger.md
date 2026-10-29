# WP4.2b -- output-name containment ledger

| Turn / round boundary | Dispatcher-read depth / tokens | Disposition |
|---|---|---|
| Turn 1 / round 0 | tokens used 90,285; input depth 87,357 / 475,000 | Dispatcher supplied at turn 2; round-0 note committed as `e5983bd` |
| Turn 2 / build | tokens used 144,321; input depth 137,070 / 475,000 | Dispatcher supplied at turn 3; WIP committed as `f1a6bba` |
| Turn 3 / ruling check | Pending dispatcher reading | STOP: condition 3 does not cover eight unsafe-plan assertions or the file-form planted-control setup |

Base: `f991254`, branch `wp4.2b`. Dispatch: orchestrator generation 18,
FINAL brief on CHARC `5c056d647ad9ca99`. Scope: DR-80 naming containment.

## Governing scope amendment -- CHARC `0c8d52528a11b714`

Received with turn 3, 2026-10-29 04:43Z. The following ruling is VERBATIM and
GOVERNS the original brief wherever it amends scope or sequencing:

> **(A), GRANTED as you list it, with four conditions.** Verified here: `tools/headless_export.py:716-718` is the bypass (`except ValueError: continue`); `final_output_path` is already exported from `clearwater.jobs` (`__init__.py:35/77`), so `OutputNameError(ValueError)` beside it is additive and `jobs` is not a frozen interface; the parent guard already has planted-path tests through a monkeypatched `final_output_path` (`test_wp42a_runner_hardening.py:272/285`).
>
> 1. `OutputNameError(ValueError)` in `jobs/naming.py`, exported from `clearwater.jobs`; its message names the source by name only (no folder). Every existing `except ValueError` still catches it; the engine's `_describe` route is unchanged for other `ValueError`s.
> 2. GRANT to WP4.2b on `check_outputs`' one `except ValueError` branch ONLY: `except OutputNameError as exc: raise RunnerRefusalError(...)` (exit 2, before any job, name only); any other `ValueError` continues to the engine (WP4.2a choice 3 kept for the invalid suffix). The parent guard below it stays as written (defence in depth) and its planted-path tests at :272/:285 must still pass unedited, so the guard remains tested now that the naming check pre-empts it on real names.
> 3. Test-only grant on `tests/test_wp42a_runner_hardening.py` limited to (a) the two `same_drive_stream_output_keeps_checked_parent` cases flipping to REFUSED (the DR-80 rule: every `:` refused; record the flip in the ledger and the report) and (b) assertions on the exact refusal TEXT that the new refusal changes. Every other WP4.2a assertion passes unedited; the cell lists the edited node ids and the 22 now-green node ids by name in the ledger. No deletion of a WP4.2a test.
> 4. Sequencing and gate as you propose: WP4.2b merges FIRST; you rebase `wp4.2` onto main at cell 2's next yield before task 5 (if cell 2 has already touched the runner, you resolve the one-branch conflict at your seat and say so in the WP4.2 ledger). WP4.2b gets its OWN two-leg window (~52 min), not a stack; post OPEN/CLOSE as usual. DR-80's closure text at the accept gains one sentence: the runner refuses an `OutputNameError` before jobs (exit 2).

Additional owned files are limited to `src/clearwater/jobs/__init__.py`'s
exception export, `tools/headless_export.py`'s one catch branch and needed
import, and `tests/test_wp42a_runner_hardening.py` under condition 3. No
frozen-interface grant. The two-leg suite has its OWN window after review
convergence, never a stack. The dispatcher owns merge/rebase sequencing.

## Round 0 -- runner-test premise and FINAL ruling

**Disposition (turn 2, FINAL):** the finding stands, but the dispatcher
requires a REAL ADS source, with no stat patch. The ONE new runner test uses
the accepted WP4.2a creation pattern with a multi-letter carrier and a real
JPEG stream, through library `run(..., footage_folder=None)`. It uses the
real reader; neither a reader double nor a stat double is needed. Skip with
an explicit reason if the platform/OS refuses the ADS. The implementation
and the new test follow this ruling; no out-of-envelope product edit.

**[MAJOR, EXECUTED, brief-premise mismatch]** Task 4 says the reader double
means the source need not exist and planning is reached. On the dispatched
base, `ExportEngine._photo` reads at `src/clearwater/jobs/export.py:711`, then
calls `os.stat(request.source)` at line 712, before planning at line 753.
The specified nonexistent `c:input.jpg` therefore fails with
`FileNotFoundError`, before the naming guard can run. A reader double alone
cannot test the required refusal route.

Cheap reproduction on this base: use the actual
`composition.export_jobs(reader=...)` with a reader returning
`tests/fixtures/stills/jpeg/jpeg-gradient-srgb.jpg`'s image and metadata,
the string-built absolute synthetic source `c:input.jpg`, an existing scratch
output folder, `force_cpu=True`, and library `run(..., footage_folder=None)`.
Wrap the engine's `plan_output` to count calls. Observed: reader calls **1**,
engine planner calls **0**, item **failed**, error **FileNotFoundError**,
`exit_status(record)` **1**, output folder empty. Probe assertions passed,
process **EXIT 0**. Evidence: `work/wp4.2b/round0-probe.log` (gitignored).
No naming refusal was observed or claimed.

The brief's "exit 2 / failed item" alternatives are kept distinct: task 4
specifically requests the library failed-item route. An executed batch's
`exit_status` is 1 for a failed item (`tools/headless_export.py:874-886`);
the new library test will assert the failed item, not invent an exit-2
contract for that route.

## Placement and exact rule

Place the validation in `_base_plan` (`src/clearwater/jobs/naming.py:287`),
after the existing suffix validation and computation of base and extension,
before constructing `OutputPlan` (currently lines 292-297).

On the base, both `final_output_path` (line 324) and `plan_output` (line 380) call this
function first. `plan_output` scans the destination only afterward (line 381);
filesystem collision checks and reservations are later still (lines 383-387).
`final_output_path` performs its source/temporary checks only after the call
(lines 325-326). Thus rejection occurs before any plan, filesystem read or
reservation in these naming entry points. This does not claim that the export
engine does no filesystem reads before it reaches naming.

Validate the whole composed unnumbered NAME, `base + extension`, exactly as
the ruling requires:

- No `/` or `\` separator.
- No drive and no `:`.
- `Path(name).name == name`.
- `os.path.splitdrive(name)[0] == ''`.

The explicit colon check carries the portable drive/stream protection on
POSIX too. Photo extension is `.png`; video extension is `source.suffix`, so
the latter must participate in validation. Error type: `ValueError`; its
message identifies `source.name` only, never the source or output folder.
Update only the two public planning functions' `Raises:` entries along with
this validation.

Collision numbering only appends `_<N>` to the base
(`OutputPlan.path`, lines 267-268), which cannot introduce any prohibited
component syntax. One validation before construction therefore covers every
candidate produced by these planners. A raising `OutputPlan.path` property
would instead interrupt candidate checks/reservations mid-loop.

Do not extend the suffix rule's other restrictions to source stems:
`* ? " < > |`, controls, `..`, trailing dot/space and the temporary marker
remain outside this validation. Existing temporary-name and source guards
remain in force. Direct manual `OutputPlan` construction is unchanged by this
placement, as permitted by the ruling's `_base_plan` alternative.

## RED-first roster and observed results

All tests below are additions; existing test bodies remain unchanged.
These node families were executed RED before any product edit, then GREEN.

| Test in `tests/test_jobs_naming.py` | Matrix | Observed result on base |
|---|---|---|
| `test_composed_output_name_is_refused` | `c:x.jpg`, `carrier:x.jpg` x PHOTO/VIDEO x `final_output_path`/`plan_output` (8 cases) | RED: all 8 failed `DID NOT RAISE ValueError` |
| `test_video_extension_stream_is_refused` | `x.mp4:s` x both planners, VIDEO (2 cases) | RED: both failed `DID NOT RAISE ValueError` |
| `test_wp23_fixture_names_keep_output_paths` | Every manifest entry x both kinds x explicit output folder/beside source x both planners (696 cases) | PASS: all 696 unchanged default-suffix names and paths |

Each refusal case constructs the synthetic source from a full string
(`Path(f"{tmp_path}{os.sep}{name}")`), rather than joining a colon-bearing
child with `/` and asserts its basename first. It checks `ValueError` includes
the source name and excludes source/output folder spellings. Sources need
not exist for these direct naming tests. `red-planners.log` retains the ten
failing node IDs. Parameter IDs are `[<name>-<photo|video>-<final|plan>]` for
the eight stem cases, and `[final]`/`[plan]` for the two extension cases.

ONE new runner test was added:
`tests/test_wp42b_naming_guard.py::test_naming_refusal_is_readable_and_writes_nothing`,
following the FINAL turn-2 ruling. It creates `src/carrier` and a real JPEG
stream `Path(f"{carrier}:input.jpg")` inside `tmp_path`, with an output folder,
force CPU and empty per-test cwd; no doubles. Preflight is bypassed only by
the specified `footage_folder=None`, so the real engine reaches naming.
RED: failed its empty-output-folder assertion because the base created
`out/carrier`; the engine's failed item reported `OSError: [WinError 87] The
parameter is incorrect` while renaming its stream temporary to
`carrier:input_corrected.png`. Carrier main data and source stream assertions
passed before that failure. Evidence: `red-runner.log`, EXIT 1.
GREEN: real ADS creation worked in this sandbox; no skip. The engine returned
one failed item starting `carrier:input.jpg: ValueError:`, no folder spelling
or traceback in failure/summary/captured logging, no output, empty output/cwd
folders, unchanged carrier and stream. The whole naming file plus this test
passed 822 tests. No hardware/timing markers; all new tests are parallel-leg.

## WP2.3 control observed on the base

Manifest: `tests/fixtures/manifest.json`, all **87** `samples[].path` entries,
including the generated clip, placeholder/sidecar files, DNG refusal fixtures,
stills, mask and videos. Naming is checked independently of media decoding.
For each entry, use an isolated hypothetical source under
`work/wp4.2b/control-source/`, default suffix `_corrected`, PHOTO and VIDEO,
explicit scratch output folder and beside-source settings, and both planners.

Expected paths are independently composed as destination /
`(source.stem + '_corrected' + extension)`, where PHOTO uses `.png` and VIDEO
keeps `source.suffix`. All **696** baseline planner comparisons passed. Every
composed control name also passed the exact proposed separator/colon,
`Path(name).name`, and native `splitdrive` conditions. Thus the proposed rule
rejects none of these legitimate fixture output names. This is baseline
control evidence, not a post-change GREEN claim.

## Export and runner route mapped

- `composition.export_jobs`, `src/clearwater/app/composition.py:148-188`,
  accepts the photo-reader override and returns the real export engine wrapper.
- `_photo` reads/stat-checks before `_plan` at
  `src/clearwater/jobs/export.py:711-712,753`; `_video` probes before `_plan`
  at lines 808,837. `_plan` calls `plan_output` at line 679.
- `_run` catches an unexpected exception at lines 607-608; `_describe`
  (634-641) prefixes the exception type and ASCII-escapes its text.
  `ValueError` is absent from `_READABLE_ERRORS` (106). The result is
  `<source name>: ValueError: <message>`, without a traceback.
- WP4.2a's `check_outputs` retains its folder check and leaves a naming
  `ValueError` to the engine at `tools/headless_export.py:715-718`.
  The planned-parent guard at 719-724 and file-form guard at 725-727 stay as
  defence in depth. With no footage setting, it returns at 697-698.
- Library `run` invokes preflight at line 765 and the batch at 775.
  `summary_lines` renders failed-item text at 901-906.

## Cumulative round ledger

| Round | Reviewer / verdict | Critical / major / minor | In / out | NEW / REOPENED | Reverts | Product / test-only fixes | Transport / CLI | Depth |
|---|---|---|---|---|---|---|---|---|
| 0 | No Reviewer A run; read/map STOP ruled at turn 2 | N/A | N/A | N/A | 0 | None; ledger only | Codex cell; reviewer not invoked | tokens 90,285; input 87,357 / 475,000 |
| Turn 2 build (not a review round) | No Reviewer A run; initial scope STOP ruled at turn 3 | N/A | N/A | N/A | 0 | Product validation + new tests | Codex cell; reviewer not invoked | tokens 144,321; input 137,070 / 475,000 |
| Turn 3 ruling check (not a review round) | No Reviewer A run; narrower test-scope STOP below | N/A | N/A | N/A | 0 | None; documentation + cheap reproductions only | Codex cell; reviewer not invoked | Pending dispatcher |

Review policy: the driver's Claude pass, STRONG tier, per the Clearwater
seam-3 fill. Adjudicate every supplied finding; yield at each round boundary.
At round 5 and every fifth round, STOP for the dispatcher gate. Reviewer A
convergence and Reviewer B remain outstanding.

## Runs and verification record

| Turn / run | Command / conditions | Evidence / counts | EXIT |
|---|---|---|---|
| 1 / baseline and premise probe (light) | PowerShell stdin script; `PYTHONPATH=src;tools`, `C:/Users/rwsmy/clearwater/.venv/Scripts/python.exe -B -`; stdout/stderr captured with `Out-File -Encoding utf8` | `work/wp4.2b/round0-probe.log`; 696 control comparisons PASS; reader 1 / planner 0; missing-source failure confirmed | 0 |

The read-only interpreter/dependencies were reused from main's existing uv
environment because this worktree has no `.venv`; `-B` disables bytecode
writes. No dependency installation or configuration change was performed.
Scratch writes were confined to `work/wp4.2b/`; footage was not accessed.
The Windows native stderr wrapper in the log accompanies the expected batch
warning; the Python process and its assertions exited 0.

Owner verification loop, round 0: suspected reader-only test could fail before
naming; confirmed by the stat call order and independent executed probe;
not fixed pending ruling. Fixture-name compatibility control passed on base.
No other confirmed issue, false-positive rejection or product fix this turn.

Heavy runs: **none**. No pytest, lint, format or mypy run this turn; no
post-change verification claim. The two-leg suite is reserved for the
dispatcher's posted window; stacked-versus-own timing remains its decision.
No RUN REQUEST for that gate yet: this is the mandated round-0 yield.

## Turn 2 -- build and check record

All commands below ran from this worktree with
`UV_PROJECT_ENVIRONMENT=C:/Users/rwsmy/clearwater/.venv` and `uv run --no-sync`:
reuse the installed uv environment read-only, without synchronization or
dependency installation. Pytest additionally used `PYTHONPATH=scripts;src`
(Windows spelling), `QT_QPA_PLATFORM=offscreen`,
`-p sandbox_mkdir_shim -p no:cacheprovider`. The explicit `src` ensures the
worktree product code is used despite main's editable installation.
All log paths below are relative to `work/wp4.2b/`; PowerShell captures
stdout/stderr with `Out-File -Encoding utf8`.

| Run | Command after `uv run --no-sync` | Log | Counts / EXIT |
|---|---|---|---|
| RED planners and control | `pytest -q tests/test_jobs_naming.py -k 'composed_output_name_is_refused or video_extension_stream_is_refused or wp23_fixture_names_keep_output_paths' --basetemp=work/wp4.2b/tmp-red-planners -p sandbox_mkdir_shim -p no:cacheprovider` | `red-planners.log` | 10 failed, 696 passed, 115 deselected; EXIT 1 |
| RED runner | `pytest -q -rs tests/test_wp42b_naming_guard.py --basetemp=work/wp4.2b/tmp-red-runner -p sandbox_mkdir_shim -p no:cacheprovider` | `red-runner.log` | 1 failed; EXIT 1; real ADS, no skip |
| GREEN full naming + runner | `pytest -q -rs tests/test_jobs_naming.py tests/test_wp42b_naming_guard.py --basetemp=work/wp4.2b/tmp-green-naming -p sandbox_mkdir_shim -p no:cacheprovider` | `green-naming.log` | 822 passed, zero skips; EXIT 0 |
| Initial lint | `ruff check .` | `ruff-check.log` | 2 new runner-test style findings; EXIT 1 |
| Initial format check | `ruff format --check .` | `ruff-format.log` | 1 new runner-test file would reformat; EXIT 1 |
| Import-order fix | `ruff check --fix tests/test_wp42b_naming_guard.py` | `ruff-fix-runner.log` | 1 fixed, line-length finding remained; EXIT 1 |
| Runner-test formatting | `ruff format tests/test_wp42b_naming_guard.py` | `ruff-format-runner.log` | 1 file reformatted; EXIT 0 |
| Final lint | `ruff check .` | `ruff-check-final.log` | All checks passed; EXIT 0 |
| Final format check | `ruff format --check .` | `ruff-format-final.log` | 261 files already formatted; EXIT 0 |
| Types | `mypy` | `mypy.log` | No issues found in 141 source files; EXIT 0 |
| Broader requested light set | Full command below | `light.log` | 22 failed, 1053 passed, 12 deselected, zero skips; EXIT 1 |
| Final scope/encoding check | `uv run --no-sync python -B -` with stdlib assertions over git status/diff, original naming-test content and new runner-test AST | `final-scope.log` | Exactly five owned files; existing naming tests preserved; ONE new runner test; zero CR bytes; diff whitespace check PASS; EXIT 0 |

Broader light command (PowerShell expanded `tests/test_jobs_export*.py` to
`test_jobs_export.py`, `test_jobs_export_photo.py`, `test_jobs_export_support.py`
and `test_jobs_export_video.py` before invoking pytest):

```text
uv run --no-sync pytest -q -rs tests/test_jobs_naming.py tests/test_wp42b_naming_guard.py tests/test_headless_export.py tests/test_wp42a_runner_hardening.py tests/test_jobs_export.py tests/test_jobs_export_photo.py tests/test_jobs_export_support.py tests/test_jobs_export_video.py -m "not gpu and not footage and not slow" --deselect=tests/test_headless_export.py::test_g1_inside_sees_every_spelling_of_the_same_folder --deselect=tests/test_headless_export.py::test_g1_main_refuses_every_footage_check_through_another_spelling[unc] --deselect=tests/test_headless_export.py::test_g1_the_redactor_hides_the_extended_spellings --basetemp=work/wp4.2b/tmp-light -p sandbox_mkdir_shim -p no:cacheprovider
```

The 12 deselections include the three explicitly authorized UNC nodes and
nine marker exclusions. No additional test was deselected to hide a failure.
Every executed new test passed; all failures belong to the existing WP4.2a
file. Full node IDs were extracted to `work/wp4.2b/light-failures.txt` (22).

## Turn 2 -- STOP: existing-test scope boundary

**Disposition at turn 3:** CHARC granted the additive exception, one runner
catch branch and narrowly specified test edits in the governing ruling
above. That resolves the original prohibition on all edits to this test
file. The newly verified mismatch with condition 3 is recorded below;
the original 22 failures are not yet green.

**[MAJOR, EXECUTED, introduced integration conflict / out-of-owned-file
remediation]** The requested light run exposes 22 tests that depend on a
colon-bearing plan being returned, or on runner preflight rejecting it
before jobs. The new `_base_plan` refusal prevents returning such a plan;
`check_outputs` intentionally catches that `ValueError` and leaves it to
the engine (the accepted choice 3, unchanged at runner lines 715-718).
Thus old preflight-only fake-job tests do not get their required
`RunnerRefusalError`/exit 2, and direct unsafe-plan expectations now raise.
This is a confirmed integration conflict caused by the intended behavior
change, not an unrelated pre-existing failure to bank or suppress.

All failing IDs below have prefix `tests/test_wp42a_runner_hardening.py::`:

```text
test_stream_named_output_is_refused_before_jobs[explicit-out-jpg-run]
test_stream_named_output_is_refused_before_jobs[explicit-out-jpg-main]
test_stream_named_output_is_refused_before_jobs[explicit-out-mp4-run]
test_stream_named_output_is_refused_before_jobs[explicit-out-mp4-main]
test_stream_named_output_is_refused_before_jobs[beside-source-jpg-run]
test_stream_named_output_is_refused_before_jobs[beside-source-jpg-main]
test_stream_named_output_is_refused_before_jobs[beside-source-mp4-run]
test_stream_named_output_is_refused_before_jobs[beside-source-mp4-main]
test_drive_relative_output_is_refused_before_jobs[relative-out-jpg-run]
test_drive_relative_output_is_refused_before_jobs[relative-out-jpg-main]
test_drive_relative_output_is_refused_before_jobs[relative-out-mp4-run]
test_drive_relative_output_is_refused_before_jobs[relative-out-mp4-main]
test_drive_relative_output_is_refused_before_jobs[beside-source-jpg-run]
test_drive_relative_output_is_refused_before_jobs[beside-source-jpg-main]
test_drive_relative_output_is_refused_before_jobs[beside-source-mp4-run]
test_drive_relative_output_is_refused_before_jobs[beside-source-mp4-main]
test_drive_relative_stream_cannot_write_into_footage_cwd
test_same_drive_stream_output_keeps_checked_parent[absolute-out]
test_same_drive_stream_output_keeps_checked_parent[beside-source]
test_stream_enumeration_failure_is_not_a_skip[after-refusal]
test_stream_output_on_hard_link_leaves_original_unchanged[run]
test_stream_output_on_hard_link_leaves_original_unchanged[main]
```

Mechanics confirmed against the unchanged tests:

- Eight stream-form cases plus two hard-link cases call
  `_assert_stream_refusal` (lines 60-76), which requires pre-job refusal.
- Eight drive-relative cases call `final_output_path` before running jobs
  (line 108); the two same-drive cases do likewise (line 166) and expect a
  usable output. The new guard rejects their colon-bearing source names.
- The real stream/cwd case (line 144) expects CLI exit 2; it now receives the
  engine failed-item status 1 while the stand-in footage folder stays empty.
- The stream-enumerator planted control's after-refusal setup (line 208)
  requires a `RunnerRefusalError` that the naming refusal now supersedes.

Owner verification loop, turn 2: RED independently confirmed missing planner
refusals and the actual unsafe stream-writing attempt; fixed by the guard.
The exact fixture-name compatibility matrix and real engine test are GREEN.
Suspected old runner expectations would conflict; confirmed by the requested
light run and tracing their assertions. No false positive or product revert.
Verification has not converged: the existing-test conflict is unresolved at
the explicit scope tripwire. Initial lint/format slips were fixed only in
the new test. Scope inspection shows only owned files changed, no frozen
interface/dependency/configuration/runner edit, and scratch writes under
`work/wp4.2b/` (including pytest tmp paths); footage not accessed by this work.

`docs/reports/wp4.2b-naming-guard.md` is **DRAFT -- for Reviewer A**.
Reviewer A and Reviewer B have not run. The two-leg suite is not run by this
cell; the RUN REQUEST below is for the dispatcher's OWN window after review
convergence. The turn-3 scope check below remains unresolved.

## RUN REQUEST -- seat two-leg gate, after convergence and scope resolution

Run from Git Bash at the dispatcher's seat on the resolved candidate, in its
OWN posted window, per CHARC `0c8d52528a11b714`; do not stack with WP4.2.
Run ID `wp4.2b`; all evidence and basetemps below stay under `work/wp4.2b/`.
Seat runs use no sandbox shim or UNC deselections. Retain collection/partition,
skip-accounting and patch-ID evidence required by the review/gate fill.

```bash
unset PYTEST_ADDOPTS
export QT_QPA_PLATFORM=offscreen
uv run python -c "import psutil; assert psutil.virtual_memory().available >= 5*2**30" > work/wp4.2b/gate-memory-parallel.log 2>&1
uv run pytest -q -rs -n 4 -m "not gpu and not footage and not gui and not slow" --basetemp=work/wp4.2b/pytest-gate-wp4.2b-parallel > work/wp4.2b/gate-parallel.log 2>&1
uv run python -c "import psutil; assert psutil.virtual_memory().available >= 5*2**30" > work/wp4.2b/gate-memory-serial.log 2>&1
uv run pytest -q -rs -m "gpu or footage or gui or slow" --basetemp=work/wp4.2b/pytest-gate-wp4.2b-serial > work/wp4.2b/gate-serial.log 2>&1
```

Proceed to each leg only after its memory precheck exits 0. No heavy command
in this request has been executed by this cell. No harness gate is required.

## Turn 3 -- STOP: condition-3 premise does not match `f1a6bba`

**Recommended amendment:** extend the test-only grant to (1) replacing the
obsolete unsafe-plan setup/assertion in all eight drive-relative cases with
an `OutputNameError` assertion while keeping their runner/no-jobs/no-write
assertions, and (2) isolating the existing file-form planted control from
naming via a planted `final_output_path`. Also authorize adding a genuine
planted escaped-parent control. Keep production changes limited to the
already granted exception/export/catch, keep the runner's parent guard
unchanged, and keep the :272/:285 negative-call controls unedited. No test
deletion or failure suppression. Await this narrow amendment before build.

**[MAJOR, EXECUTED] Eight non-text assertions require an additional grant.**
`test_drive_relative_output_is_refused_before_jobs` calls
`he.final_output_path` directly at line 110, then asserts
`planned.parent != checked` at line 112. These execute BEFORE the runner.
The naming guard already raises `ValueError` on that call, and the granted
`OutputNameError(ValueError)` must still raise there. Neither a new catch in
`check_outputs` nor a changed refusal-text assertion can make these eight
cases pass without editing this non-text setup/assertion. They are not the
two same-drive cases explicitly granted the behavior flip.

Cheap reproduction on the untouched WIP head `f1a6bba`:
`test_drive_relative_output_is_refused_before_jobs[relative-out-jpg-run]`
fails at the direct planner call with name-only `ValueError` before reaching
`assert planned.parent != checked`. The same run passes both :272/:285
controls. Result: **1 failed, 2 passed**, EXIT 1;
`work/wp4.2b/turn3-grant-repro.log`.

**[MAJOR, REASONED] The asserted parent-guard controls are different controls.**
At lines 272 and 285, `final_output_path` is patched to `unexpected`, a
function that calls `pytest.fail` if invoked. The tests are
`test_no_footage_still_skips_output_checks` and
`test_refused_request_does_not_plan_an_output`. Their passing results above
prove planning is NOT called on those routes. They cannot exercise the
parent comparison that follows a successful planner call. There is no
planted `final_output_path` returning an escaped parent in this file at
`f1a6bba` (all occurrences were inspected).

The actual planted file-form control is
`test_output_file_form_check_has_a_planted_control` at lines 248-263. It
patches only `_write_form_refusal`, not `final_output_path`, and uses a
colon-bearing source. Once the granted early naming refusal is implemented,
that refusal will pre-empt the disabled file-form check: the control expects
an `AssertionError` from CLI status 1, but the new naming catch returns 2.
Changing only refusal TEXT cannot preserve this control; its setup must
isolate the predicate it is intended to test.

The turn-3 requested route evidence is also captured, using existing tests
without edits: the before-jobs CLI case
`test_stream_named_output_is_refused_before_jobs[explicit-out-jpg-main]`
is RED on `f1a6bba` (`assert 1 == 2`), while
`test_invalid_suffix_stays_an_engine_refusal` PASSES. Result: **1 failed,
1 passed**, EXIT 1; `work/wp4.2b/turn3-route-red.log`.

Both runs used the existing read-only uv environment with
`UV_PROJECT_ENVIRONMENT=C:/Users/rwsmy/clearwater/.venv`,
`PYTHONPATH=scripts;src`, `QT_QPA_PLATFORM=offscreen`, stdout/stderr to
UTF-8 logs, and the mandatory sandbox shim:

```text
uv run --no-sync pytest -q -rf tests/test_wp42a_runner_hardening.py::test_drive_relative_output_is_refused_before_jobs[relative-out-jpg-run] tests/test_wp42a_runner_hardening.py::test_no_footage_still_skips_output_checks tests/test_wp42a_runner_hardening.py::test_refused_request_does_not_plan_an_output --basetemp=work/wp4.2b/tmp-turn3-grant-repro -p sandbox_mkdir_shim -p no:cacheprovider
uv run --no-sync pytest -q -rf tests/test_wp42a_runner_hardening.py::test_stream_named_output_is_refused_before_jobs[explicit-out-jpg-main] tests/test_wp42a_runner_hardening.py::test_invalid_suffix_stays_an_engine_refusal --basetemp=work/wp4.2b/tmp-turn3-route-red -p sandbox_mkdir_shim -p no:cacheprovider
```

No product or test file was edited this turn. The same-drive flip, exception
class/export and runner branch remain NOT built. No edited WP4.2a node IDs
and no 22-now-green claim. No full light/lint/type rerun: the ruling's failed
test premise was reproduced cheaply and the cell yields at the scope
tripwire. No heavy run or reviewer run; report remains DRAFT. Depth for
turn 3 is pending the dispatcher; turn-2 supplied readings are recorded.
