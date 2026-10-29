# WP4.2b -- output-name containment ledger

| Turn / round boundary | Dispatcher-read depth / tokens | Disposition |
|---|---|---|
| Turn 1 / round 0 | tokens used 90,285; input depth 87,357 / 475,000 | Dispatcher supplied at turn 2; round-0 note committed as `e5983bd` |
| Turn 2 / build | tokens used 144,321; input depth 137,070 / 475,000 | Dispatcher supplied at turn 3; WIP committed as `f1a6bba` |
| Turn 3 / ruling check | tokens used 306,885; input depth 167,794 / 475,000 | Dispatcher supplied at turn 4; docs-only STOP committed as `79b60d9` |
| Turn 4 / build | tokens used 379,056; input depth 206,526 / 475,000 | Dispatcher supplied at turn 6; committed as `215817a`; Reviewer A round 1 completed |
| Turn 5 / round-1 adjudication | tokens used 413,658; input depth 237,641 / 475,000 | No tracked change; adjudication delivered in return and persisted below at turn 6 |
| Turn 6 / round-1 remediation | Pending dispatcher reading | Bounded continuation authorized near evaluation point; test/report cleanup under `8262cd59b0d48c73` |

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

## Governing scope extension -- CHARC `050c52106cd8c6ad`

Received with turn 4, 2026-10-29 04:50Z. VERBATIM; GOVERNS together with
`0c8d52528a11b714` and resolves the turn-3 STOP:

> RULING on WP4.2b STOP 2 (query cb8a50fc31eb0187): **condition 3 EXTENDED with (c) and (d) as you recommend, test-only, no deletion, no skip.** Verified here: `test_drive_relative_output_is_refused_before_jobs` computes its precondition with the real `he.final_output_path` (:110) so DR-80 raises inside the test; and the tests at :266 and :279 monkeypatch `final_output_path` to FAIL if called, so they prove planning is skipped, not that the parent guard fires. My condition 2 mis-described them; the correction stands here.
>
> (c) In the eight drive-relative cases, the precondition's plan comes from a monkeypatched `he.final_output_path` returning the drive-relative path the old naming produced, built from a string (`Path(f"{letter}:{stem}_corrected{ext}")`); `planned.parent != checked` stays asserted on that plant; the rest of each case (run and main, exit 2, name only, nothing called on the jobs double) is unchanged. These eight remain the parent guard's coverage.
> (d) The planted file-form control's setup is isolated from the naming refusal the same way, so it still proves the file-form helper refuses.
> Conditions: every edited node id with its line span and a one-line reason in the ledger AND the report; no assertion weakened (the diff shows only the plan's source moving from the real function to a plant); the eight plus the two flipped same-drive cases plus any exact-text edits are the WHOLE WP4.2a test edit; real-name refusal is proved by WP4.2b's own naming tests and its runner before-jobs test. Reviewer A is told the edit list so it checks the plants are faithful to the old naming output (drive-relative, parent = `<letter>:`).
>
> Resume the cell. Sequencing and the own window unchanged.

Implementation uses only the original owned files and the three files added
by the first ruling, with WP4.2a edits restricted by both rulings. No new
test was added to or deleted from the WP4.2a file, and none was skipped.

## Governing round-1 remediation ruling -- CHARC `8262cd59b0d48c73`

Received with turn 6, 2026-10-29 05:48Z. VERBATIM; GOVERNS with
`0c8d52528a11b714` and `050c52106cd8c6ad`:

> RULING on WP4.2b R1 (query 0d0659fe906001ac): **F1 = (a) GRANTED.** ONE added test in `tests/test_wp42a_runner_hardening.py` beside the 3(d) control, its twin: the same planted old stream path through a monkeypatched `final_output_path`, the file-form check ON, asserting the `REFUSED_FORM` text, exit 2 and nothing called on the jobs double, for run and main; RED under mutation M1 (the cell records the M1 RED run in the ledger). Nothing else in the file changes; the edit list in ledger and report gains this node id with the reason "coverage of the file-form layer after naming pre-empts real names". The reviewer's mutation finding is the right test of 3(d): my wording held in letter only, the twin makes it hold in effect.
>
> Not (b): WP4.2a's guard coverage stays in WP4.2a's file. Not (c): a defence layer that can be deleted unnoticed is not a register item, it is a missing test, and the cell is on the file now.
>
> F2-F5 dispositions at your seat CONCURRED (F2 record only; F3 the deviation stated in the report, the engine-route probe named; F4 one sentence; F5 none).

The seat also grants `[engine-drive-relative]` as ONE additional parameter
row inside the existing ONE runner test, with real drive-letter ADS,
relative output, empty cwd and the existing data-preservation/refusal
assertions. This remediation changes only the two granted test files,
the report and this ledger. No product edit.

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
| Turn 3 ruling check (not a review round) | No Reviewer A run; narrower STOP ruled at turn 4 | N/A | N/A | N/A | 0 | None; documentation + cheap reproductions only | Codex cell; reviewer not invoked | tokens 306,885; input 167,794 / 475,000 |
| Turn 4 build (not a review round) | Reviewed at round 1 | N/A | N/A | N/A | 0 | Exception/export + one runner catch + granted tests | Codex cell | tokens 379,056; input 206,526 / 475,000 |
| Reviewer A round 1, adjudication turn 5 / cleanup turn 6 | `NO_NEW_CRITICAL_MAJOR`; 1 minor / 4 advisory adjudicated below | 0 / 0 / 1; 4 advisory | 4 / 1 | 5 / 0 | 0 | Test/report-only remediation; no product change | Driver Claude `claude-opus-5-5` / high; exit 0, 38 turns; CLI version not supplied | Turn 4: input 206,526; turn 5: input 237,641; turn 6 pending |

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

**Disposition at turn 4:** resolved by CHARC `050c52106cd8c6ad`, verbatim above.
The eight drive-relative cases retain their original escaped-parent
assertion on a planted old-style path; the file-form control is isolated
the same way. The :272/:285 negative-call controls stay unedited. No new
parent-guard test is needed because the eight existing cases now exercise
that guard directly. Implementation and observed results follow below.

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


## Turn 4 -- implementation, GREEN checks and Reviewer A handoff

Build complete within the amended scope; both prior STOPs resolved. Reviewer
A round 1 has not run. No code review convergence, Reviewer B or full-gate
claim. The report is DRAFT -- for Reviewer A. No new scope question remains.

`OutputNameError(ValueError)` is public and exported from jobs. The composed
name check now raises that subclass, and only the runner's exception branch
plus import changes: OutputNameError becomes a name-only RunnerRefusalError
before jobs; other ValueErrors continue unchanged (suffix control passed).
The engine remains unchanged and reports OutputNameError readably without
preflight. The ONE new runner test is parameterized over these two routes.
All eight path plants match old OutputPlan.path composition, parent
`<letter>:`; same-drive real-name cases flip to REFUSED under condition 3(a).

### Runs (all light; no heavy suite or reviewer invoked)

Environment: `UV_PROJECT_ENVIRONMENT=C:/Users/rwsmy/clearwater/.venv`,
`PYTHONPATH=scripts;src`, `QT_QPA_PLATFORM=offscreen`; `uv run --no-sync`
reuses installed dependencies without syncing outside the worktree.
All stdout/stderr was captured to UTF-8 files under `work/wp4.2b/`.

| Run | Command after `uv run --no-sync` | Evidence (under work/wp4.2b/) | Counts / EXIT |
|---|---|---|---|
| RED before exception/catch | `pytest -q -rf tests/test_wp42b_naming_guard.py tests/test_wp42a_runner_hardening.py::test_invalid_suffix_stays_an_engine_refusal --basetemp=work/wp4.2b/tmp-turn4-red -p sandbox_mkdir_shim -p no:cacheprovider` | `turn4-red.log` | 2 failed (both new runner modes), 1 passed (suffix); EXIT 1 |
| Initial lint | `ruff check .` | `turn4-ruff-check.log` | 2 line-length findings in new runner test; EXIT 1 |
| Initial format check | `ruff format --check .` | `turn4-ruff-format.log` | 1 file would reformat; EXIT 1 |
| Wrap new test | `ruff format tests/test_wp42b_naming_guard.py` | `turn4-format-fix.log` | 1 file reformatted; EXIT 0 |
| Final lint | `ruff check .` | `turn4-ruff-check-final.log` | All checks passed; EXIT 0 |
| Final format | `ruff format --check .` | `turn4-ruff-format-final.log` | 261 files already formatted; EXIT 0 |
| Types | `mypy` | `turn4-mypy.log` | No issues in 141 source files; EXIT 0 |
| Full requested light set | Exact command below | `turn4-light.log`, `turn4-light.xml` | 1076 passed, 12 deselected, zero failures/errors/skips; EXIT 0 |
| Assertion/scope/plant audit | `python -B -` (stdlib AST/git assertions plus old OutputPlan.path matrix) | `turn4-diff-evidence.log`, `turn4-wp42a.diff` | Only granted WP4.2a edits; original assertions retained except authorized flips/text; runner scope exact; 8 faithful plants; EXIT 0 |
| Independent XML outcomes | `python -B -` (stdlib XML assertions) | `turn4-outcomes.log` | All 1076 cases passed, all prior 22 present, suffix/negative-call/file-form and real ADS cases passed; EXIT 0 |
| Report and ledger assembly | `python -B -` (owned documentation writes using the audited node lists) | `turn4-docs.log` | DRAFT report and ledger contain every edited node/span/reason and every prior now-green node; EXIT 0 |
| Final scope/encoding audit | `python -B -` (stdlib git/AST/document assertions) | `turn4-final-scope.log` | Exactly eight owned files; naming delta restricted to class/raise/Raises, additive jobs export; full lists in both docs; zero CR bytes; diff whitespace PASS; EXIT 0 |

```text
uv run --no-sync pytest -q -rf -rs tests/test_jobs_naming.py tests/test_wp42b_naming_guard.py tests/test_headless_export.py tests/test_wp42a_runner_hardening.py tests/test_jobs_export.py tests/test_jobs_export_photo.py tests/test_jobs_export_support.py tests/test_jobs_export_video.py -m "not gpu and not footage and not slow" --deselect=tests/test_headless_export.py::test_g1_inside_sees_every_spelling_of_the_same_folder --deselect=tests/test_headless_export.py::test_g1_main_refuses_every_footage_check_through_another_spelling[unc] --deselect=tests/test_headless_export.py::test_g1_the_redactor_hides_the_extended_spellings --basetemp=work/wp4.2b/tmp-turn4-light --junitxml=work/wp4.2b/turn4-light.xml -o junit_family=xunit1 -p sandbox_mkdir_shim -p no:cacheprovider
```

The 12 deselections are the authorized three UNC nodes plus nine marker
exclusions. No failure was suppressed; no added skip occurred. Both real
ADS cases ran, not skipped. The ten naming tests now check the exported
subclass while keeping `pytest.raises(ValueError)` compatibility checks.
The 696 fixture-name controls remain GREEN.

### Edited WP4.2a nodes -- complete list for Reviewer A

The following 22 node IDs include helper-only exact-text edits. Line spans
are current function spans, with the helper span named where it changed.
No test node/parametrization was added or deleted. The same-drive pair's
accepted-output-to-REFUSED flip is intentional under DR-80. The new runner
catch restores the unedited stream-enumerator after-refusal setup too.

| Edited WP4.2a node ID | Current line span | Reason |
|---|---|---|
| `tests/test_wp42a_runner_hardening.py::test_stream_named_output_is_refused_before_jobs[explicit-out-jpg-run]` | 82-90; helper 60-76 | Helper exact-text expectation now names the portable-component refusal; exit/no-jobs/privacy unchanged. |
| `tests/test_wp42a_runner_hardening.py::test_stream_named_output_is_refused_before_jobs[explicit-out-jpg-main]` | 82-90; helper 60-76 | Helper exact-text expectation now names the portable-component refusal; exit/no-jobs/privacy unchanged. |
| `tests/test_wp42a_runner_hardening.py::test_stream_named_output_is_refused_before_jobs[explicit-out-mp4-run]` | 82-90; helper 60-76 | Helper exact-text expectation now names the portable-component refusal; exit/no-jobs/privacy unchanged. |
| `tests/test_wp42a_runner_hardening.py::test_stream_named_output_is_refused_before_jobs[explicit-out-mp4-main]` | 82-90; helper 60-76 | Helper exact-text expectation now names the portable-component refusal; exit/no-jobs/privacy unchanged. |
| `tests/test_wp42a_runner_hardening.py::test_stream_named_output_is_refused_before_jobs[beside-source-jpg-run]` | 82-90; helper 60-76 | Helper exact-text expectation now names the portable-component refusal; exit/no-jobs/privacy unchanged. |
| `tests/test_wp42a_runner_hardening.py::test_stream_named_output_is_refused_before_jobs[beside-source-jpg-main]` | 82-90; helper 60-76 | Helper exact-text expectation now names the portable-component refusal; exit/no-jobs/privacy unchanged. |
| `tests/test_wp42a_runner_hardening.py::test_stream_named_output_is_refused_before_jobs[beside-source-mp4-run]` | 82-90; helper 60-76 | Helper exact-text expectation now names the portable-component refusal; exit/no-jobs/privacy unchanged. |
| `tests/test_wp42a_runner_hardening.py::test_stream_named_output_is_refused_before_jobs[beside-source-mp4-main]` | 82-90; helper 60-76 | Helper exact-text expectation now names the portable-component refusal; exit/no-jobs/privacy unchanged. |
| `tests/test_wp42a_runner_hardening.py::test_drive_relative_output_is_refused_before_jobs[relative-out-jpg-run]` | 96-129 | Plant old drive-relative output; original escaped-parent/exit/no-jobs/no-write assertions retained, plus parent-drive check. |
| `tests/test_wp42a_runner_hardening.py::test_drive_relative_output_is_refused_before_jobs[relative-out-jpg-main]` | 96-129 | Plant old drive-relative output; original escaped-parent/exit/no-jobs/no-write assertions retained, plus parent-drive check. |
| `tests/test_wp42a_runner_hardening.py::test_drive_relative_output_is_refused_before_jobs[relative-out-mp4-run]` | 96-129 | Plant old drive-relative output; original escaped-parent/exit/no-jobs/no-write assertions retained, plus parent-drive check. |
| `tests/test_wp42a_runner_hardening.py::test_drive_relative_output_is_refused_before_jobs[relative-out-mp4-main]` | 96-129 | Plant old drive-relative output; original escaped-parent/exit/no-jobs/no-write assertions retained, plus parent-drive check. |
| `tests/test_wp42a_runner_hardening.py::test_drive_relative_output_is_refused_before_jobs[beside-source-jpg-run]` | 96-129 | Plant old drive-relative output; original escaped-parent/exit/no-jobs/no-write assertions retained, plus parent-drive check. |
| `tests/test_wp42a_runner_hardening.py::test_drive_relative_output_is_refused_before_jobs[beside-source-jpg-main]` | 96-129 | Plant old drive-relative output; original escaped-parent/exit/no-jobs/no-write assertions retained, plus parent-drive check. |
| `tests/test_wp42a_runner_hardening.py::test_drive_relative_output_is_refused_before_jobs[beside-source-mp4-run]` | 96-129 | Plant old drive-relative output; original escaped-parent/exit/no-jobs/no-write assertions retained, plus parent-drive check. |
| `tests/test_wp42a_runner_hardening.py::test_drive_relative_output_is_refused_before_jobs[beside-source-mp4-main]` | 96-129 | Plant old drive-relative output; original escaped-parent/exit/no-jobs/no-write assertions retained, plus parent-drive check. |
| `tests/test_wp42a_runner_hardening.py::test_drive_relative_stream_cannot_write_into_footage_cwd` | 148-161 | Exact refusal-text expectation only; exit 2, no jobs/writes and source-byte assertions unchanged. |
| `tests/test_wp42a_runner_hardening.py::test_same_drive_stream_output_keeps_checked_parent[absolute-out]` | 165-185 | Authorized accepted-to-REFUSED flip; check planner/preflight refusal, no jobs/writes and both source data streams unchanged. |
| `tests/test_wp42a_runner_hardening.py::test_same_drive_stream_output_keeps_checked_parent[beside-source]` | 165-185 | Authorized accepted-to-REFUSED flip; check planner/preflight refusal, no jobs/writes and both source data streams unchanged. |
| `tests/test_wp42a_runner_hardening.py::test_stream_output_on_hard_link_leaves_original_unchanged[run]` | 231-255; helper 60-76 | Helper exact-text expectation only; hard-link data/stream and no-jobs assertions unchanged. |
| `tests/test_wp42a_runner_hardening.py::test_stream_output_on_hard_link_leaves_original_unchanged[main]` | 231-255; helper 60-76 | Helper exact-text expectation only; hard-link data/stream and no-jobs assertions unchanged. |
| `tests/test_wp42a_runner_hardening.py::test_output_file_form_check_has_a_planted_control` | 258-275 | Plant old stream output to isolate disabled file-form helper; all original planted-defect assertions unchanged. |

### The original 22 failing node IDs -- now GREEN

Verified individually from JUnit XML, not inferred from the aggregate count:

- `tests/test_wp42a_runner_hardening.py::test_stream_named_output_is_refused_before_jobs[explicit-out-jpg-run]` -- PASS
- `tests/test_wp42a_runner_hardening.py::test_stream_named_output_is_refused_before_jobs[explicit-out-jpg-main]` -- PASS
- `tests/test_wp42a_runner_hardening.py::test_stream_named_output_is_refused_before_jobs[explicit-out-mp4-run]` -- PASS
- `tests/test_wp42a_runner_hardening.py::test_stream_named_output_is_refused_before_jobs[explicit-out-mp4-main]` -- PASS
- `tests/test_wp42a_runner_hardening.py::test_stream_named_output_is_refused_before_jobs[beside-source-jpg-run]` -- PASS
- `tests/test_wp42a_runner_hardening.py::test_stream_named_output_is_refused_before_jobs[beside-source-jpg-main]` -- PASS
- `tests/test_wp42a_runner_hardening.py::test_stream_named_output_is_refused_before_jobs[beside-source-mp4-run]` -- PASS
- `tests/test_wp42a_runner_hardening.py::test_stream_named_output_is_refused_before_jobs[beside-source-mp4-main]` -- PASS
- `tests/test_wp42a_runner_hardening.py::test_drive_relative_output_is_refused_before_jobs[relative-out-jpg-run]` -- PASS
- `tests/test_wp42a_runner_hardening.py::test_drive_relative_output_is_refused_before_jobs[relative-out-jpg-main]` -- PASS
- `tests/test_wp42a_runner_hardening.py::test_drive_relative_output_is_refused_before_jobs[relative-out-mp4-run]` -- PASS
- `tests/test_wp42a_runner_hardening.py::test_drive_relative_output_is_refused_before_jobs[relative-out-mp4-main]` -- PASS
- `tests/test_wp42a_runner_hardening.py::test_drive_relative_output_is_refused_before_jobs[beside-source-jpg-run]` -- PASS
- `tests/test_wp42a_runner_hardening.py::test_drive_relative_output_is_refused_before_jobs[beside-source-jpg-main]` -- PASS
- `tests/test_wp42a_runner_hardening.py::test_drive_relative_output_is_refused_before_jobs[beside-source-mp4-run]` -- PASS
- `tests/test_wp42a_runner_hardening.py::test_drive_relative_output_is_refused_before_jobs[beside-source-mp4-main]` -- PASS
- `tests/test_wp42a_runner_hardening.py::test_drive_relative_stream_cannot_write_into_footage_cwd` -- PASS
- `tests/test_wp42a_runner_hardening.py::test_same_drive_stream_output_keeps_checked_parent[absolute-out]` -- PASS
- `tests/test_wp42a_runner_hardening.py::test_same_drive_stream_output_keeps_checked_parent[beside-source]` -- PASS
- `tests/test_wp42a_runner_hardening.py::test_stream_enumeration_failure_is_not_a_skip[after-refusal]` -- PASS
- `tests/test_wp42a_runner_hardening.py::test_stream_output_on_hard_link_leaves_original_unchanged[run]` -- PASS
- `tests/test_wp42a_runner_hardening.py::test_stream_output_on_hard_link_leaves_original_unchanged[main]` -- PASS

### Guard integrity and verification-loop result

Exact diff: `work/wp4.2b/turn4-wp42a.diff`, against `79b60d9`.
The AST audit confirms that no original assertion was changed or removed
outside the two authorized same-drive flips and two exact refusal-text
expectations (helper and cwd case). In the eight parent-guard cases and the
file-form planted control, only the planner source is planted; the original
assertions all remain. A parent-drive assertion strengthens plant fidelity.
Independent old OutputPlan.path comparisons confirm all eight plants, each
with parent `<letter>:`. The entire runner AST matches the old module after
removing only the new import/catch, and the parent/file-form guard source is
identical. Reviewer A is explicitly directed to check this list/fidelity.

Unedited controls verified PASS:
`test_no_footage_still_skips_output_checks` (278-288),
`test_refused_request_does_not_plan_an_output` (291-300), and
`test_invalid_suffix_stays_an_engine_refusal` (303-316).
The isolated `test_output_file_form_check_has_a_planted_control` (258-275)
also PASSED with every original assertion retained.

Owner loop: missing-source premise confirmed -> real ADS ruling; unsafe
composed name/write attempt confirmed RED -> guard fixed; old runner/test
conflicts independently confirmed -> both narrow scope rulings obtained ->
exception/catch/plants/flips implemented -> full light set GREEN ->
independent outcome/assertion/plant audit GREEN. Final pass found nothing
new. No rejected false positive, product revert, unowned edit or open scope
question. Report remains DRAFT; Reviewer A/B and own-window gate outstanding.

The dispatcher merges WP4.2b first, rebases WP4.2 at the next yield before
its task 5, and owns any runner-branch conflict resolution. No stacked gate.
DR-80 closure proposal gains: the runner refuses an OutputNameError before
jobs (exit 2); closure remains for CHARC at the accept.


## Reviewer A round 1 -- adjudication

Persisted from the turn-5 return; F1/F3/F4 FIX dispositions below were
proposals at adjudication and are implemented under the turn-6 ruling.
Head reviewed: `215817a`, base `f991254`. Driver reported Claude
`claude-opus-5-5` / high, exit 0, 38 turns, clean worktree afterward.

**Verdict: `NO_NEW_CRITICAL_MAJOR`.** All five findings are non-blocking.

| Round | Critical | Major | Minor | Advisory | In/out envelope | NEW/REOPENED | Reverts | Fixes in adjudication turn |
|---|---:|---:|---:|---:|---|---|---:|---|
| 1 | 0 | 0 | 1 | 4 | 4 / 1 | 5 / 0 | 0 | None; adjudication only |

| Turn | Tokens used | Input depth |
|---|---:|---|
| 4 | 379,056 | 206,526 / 475,000 |
| 5 | 413,658 | 237,641 / 475,000 |
| 6 | Pending dispatcher reading | Pending dispatcher reading |

Evidence directory: `C:\Users\rwsmy\clearwater-review-evidence\wp4.2b\r1\`.
`review.txt` MD5 `E459925B4E409A65254FE27F4AB51FC7`;
`review-prompt-r1.md` MD5 `2A0C552F24327FF4B4DB51B39D14D8FE`.

### F1 -- CONFIRM; MINOR, in-envelope, non-blocking; FIX

Independently removed only check_outputs' final `_write_form_refusal(output)`
assignment and refusal branch IN MEMORY. Baseline and M1 each produced
126 passed, 3 UNC nodes deselected, EXIT 0, across WP4.2a hardening, the
WP4.2b runner test and headless-export tests. XML comparison confirmed
identical selected node IDs and no new failure. The control at WP4.2a
lines 258-275 disables the predicate and expects refusal to fail; it cannot
distinguish an absent branch.

Proposed twin:
`tests/test_wp42a_runner_hardening.py::test_output_file_form_check_refuses_planted_stream_before_jobs`.
Use the same planted stream path, leave the check ON, assert REFUSED_FORM,
name only, exit 2, zero jobs and no writes. Under M1 the fake job runs and
main returns 1. At turn 5, no test was added; CHARC now grants both APIs.
Evidence: `work/wp4.2b/turn5-baseline.log`, `turn5-m1.log`, their XML files,
and `turn5-final-audit.log`.

### F2 -- CONFIRM; ADVISORY, out-of-envelope, non-blocking; BANK

The independent probe confirmed literal `..` passes final_output_path while
plan_output selects `.._2` because the directory exists. It is not a source
file; routing rejects its empty extension (`headless_export.py:395-412`).
The ruling explicitly excludes extending the stem check to `..`.
BANKED HERE as an accepted boundary observation; no validation change.

### F3 -- CONFIRM report/coverage refinement; ADVISORY, non-blocking; FIX

The deviation is already authorized and explained in ledger lines 48-64
at the reviewed head: turn-2 FINAL requires a real multi-letter ADS and
permits the real reader because export.py:712 stats the source before
planning at 753. Reject any implication it was unauthorized or unrecorded.

Required report wording: approved deviation from brief task 4 replaces
nonexistent c:input.jpg plus reader double with a real carrier:input.jpg
JPEG stream and real reader, because the photo engine stats before planning.
Distinguish ADS coverage from drive-relative cwd-escape coverage.
My independent real one-letter ADS/relative output/empty cwd/no-footage
probe returned name-only OutputNameError; output/cwd stayed empty and both
source streams remained unchanged. EXIT 0; `turn5-probes-ok.log`.
Recommended `[engine-drive-relative]` row stays inside the ONE runner test,
retaining the existing two cases. Now granted at the dispatcher's seat.

### F4 -- CONFIRM; ADVISORY, non-blocking; FIX report sentence

Independent set comparison confirmed both lists have 22 entries and differ
exactly as described. Add: "The edited-node list includes the planted
file-form control, which was already passing, while the previously
failing-node list includes the unedited stream-enumerator [after-refusal]
case, which becomes green through the new exception catch."
Evidence: `turn5-document-audit.log`, EXIT 0.

### F5 -- CONFIRM; ADVISORY, non-blocking; BANK

BANKED HERE as accepted cosmetics: extension is harmlessly rebound at test
lines 110-111, and the same-drive test name is retained to preserve mandated
node IDs. No code change, as concurred by CHARC.

### Environment and unchanged adjudication state

With UV_PROJECT_ENVIRONMENT pointing to main's installed .venv,
PYTHONPATH=scripts;src and uv run --no-sync, the observed naming import was
`C:\Users\rwsmy\clearwater\.worktrees\wp4.2b\src\clearwater\jobs\naming.py`.
The standalone probe prepended tools, matching pytest's configured path.
The stray .venv contains standard skeleton entries; it was bypassed and
left untouched. Final audit: HEAD 215817a; git status --porcelain empty.
No tracked file changed in turn 5. The first standalone probe lacked tools
on sys.path (EXIT 1, `turn5-probes.log`); corrected setup exited 0 in
`turn5-probes-ok.log`. This was probe setup, not a product import failure.


## Turn 6 -- remediation

R1 cleanup under CHARC `8262cd59b0d48c73`; no product change. F1 FIXED by the
ONE positive file-form twin below, for run/main. F3 FIXED by the explicitly
stated approved deviation, both named engine probes and ONE extra parameter
row in the ONE WP4.2b runner test. F4 FIXED by the list-explanation sentence.
F2 and F5 remain BANKED observations in the preceding adjudication; no code
change for either. No finding rejected as a false positive or reopened.
No new blocking finding, revert or open scope question; round 2 is dispatched
by the orchestrator after this commit. Report remains DRAFT for Reviewer A.

### Additions to the WP4.2a edit list

The original 22 edited-node entries above remain unchanged, with the same
spans (all precede this insertion). The following TWO case IDs are the ONE
new function granted for F1. The original negative planted control is
untouched; no other existing WP4.2a function/assertion changed this turn.

| Added node ID | Current span | Reason |
|---|---|---|
| `tests/test_wp42a_runner_hardening.py::test_output_file_form_check_refuses_planted_stream_before_jobs[run]` | 279-299 | coverage of the file-form layer after naming pre-empts real names |
| `tests/test_wp42a_runner_hardening.py::test_output_file_form_check_refuses_planted_stream_before_jobs[main]` | 279-299 | coverage of the file-form layer after naming pre-empts real names |

The twin uses the same old stream output plant, leaves `_write_form_refusal`
ON, asserts REFUSED_FORM/name-only text, no traceback, no job calls and no
writes. The run API raises RunnerRefusalError (the CLI exit-2 refusal type);
the main API explicitly returns 2. It bypasses naming only, preserving the
separate layer's positive coverage rather than relying on the negative
control's caught failure.

Added WP4.2b row:
`tests/test_wp42b_naming_guard.py::test_naming_refusal_is_readable_and_writes_nothing[engine-drive-relative]`.
It uses a real drive-letter carrier/ADS, relative output, empty cwd and
footage_folder=None. Existing [engine]/[before-jobs] IDs and assertions remain.
All three ADS rows ran without an OS-refusal skip. The function count stays
ONE. Source/main data, source stream, failed item/name-only text, empty
output/cwd and no traceback are checked. Real-name ADS coverage and
one-letter drive-relative cwd-escape coverage are distinguished in report.

### RED before GREEN, with product mutations IN MEMORY only

M1: parse inspect.getsource(check_outputs), remove the last two statements
of its request loop (the final `_write_form_refusal(output)` assignment and
its refusal if), and recompile only that function into the module globals.
The tracked runner is never edited. `pytest.main` targets the twin:

```text
uv run --no-sync python -B -
# stdin M1 recipe above, then pytest.main(['-q', '-rf', 'tests/test_wp42a_runner_hardening.py::test_output_file_form_check_refuses_planted_stream_before_jobs', '--basetemp=work/wp4.2b/tmp-turn6-m1-red', '-p', 'sandbox_mkdir_shim', '-p', 'no:cacheprovider'])
```

Result: **2 failed**, EXIT 1 (`turn6-m1-red.log`). The run case fails
DID NOT RAISE RunnerRefusalError; main fails `assert 1 == 2`. These are the
named positive controls absent at R1. On the real runner both pass.

M3 additionally proves the new drive-relative row catches its intended
failure: load only the original `_base_plan` function from
`git show f991254:src/clearwater/jobs/naming.py`, compile it IN MEMORY into
naming's globals, then run only `[engine-drive-relative]`:

```text
uv run --no-sync python -B -
# stdin M3 recipe above, then pytest.main(['-q', '-rf', 'tests/test_wp42b_naming_guard.py::test_naming_refusal_is_readable_and_writes_nothing[engine-drive-relative]', '--basetemp=work/wp4.2b/tmp-turn6-m3-red', '-p', 'sandbox_mkdir_shim', '-p', 'no:cacheprovider'])
```

Result: **1 failed**, EXIT 1 (`turn6-m3-red.log`): unchecked naming completes
the job rather than failing it. Independent inspection confirms an
`input_corrected.png` in the isolated cwd, empty output folder and both
source streams unchanged (`turn6-outcomes-final.log`). Every write stayed
under that run's work/wp4.2b basetemp; no tracked product mutation.

### Runs and light gates

Environment remains UV_PROJECT_ENVIRONMENT=C:/Users/rwsmy/clearwater/.venv,
PYTHONPATH=scripts;src, QT_QPA_PLATFORM=offscreen. No uv sync, dependency or
stray-.venv change. Every pytest invocation uses the mandatory sandbox shim
and no cacheprovider. All outputs below are UTF-8 files under work/wp4.2b/.

| Run | Command after `uv run --no-sync` | Log | Counts / EXIT |
|---|---|---|---|
| M1 RED | `python -B -` with recipe/pytest args above | `turn6-m1-red.log` | 2 failed; EXIT 1 |
| M3 RED | `python -B -` with recipe/pytest args above | `turn6-m3-red.log` | 1 failed; EXIT 1 |
| Focused GREEN | `pytest -q -rf -rs tests/test_wp42a_runner_hardening.py::test_output_file_form_check_refuses_planted_stream_before_jobs tests/test_wp42b_naming_guard.py --basetemp=work/wp4.2b/tmp-turn6-green -p sandbox_mkdir_shim -p no:cacheprovider` | `turn6-green.log` | 5 passed, zero skips; EXIT 0 |
| Lint | `ruff check .` | `turn6-ruff-check.log` | All checks passed; EXIT 0 |
| Format | `ruff format --check .` | `turn6-ruff-format.log` | 261 files already formatted; EXIT 0 |
| Types | `mypy` | `turn6-mypy.log` | No issues in 141 source files; EXIT 0 |
| Full light set | Exact command below | `turn6-light.log`, `turn6-light.xml` | 1079 passed, 12 deselected, zero failures/errors/skips; EXIT 0 |
| Preliminary XML/artifact audit | `python -B -` | `turn6-outcomes.log` | XML/node checks passed; relative artifact path had no drive, causing audit IndexError; EXIT 1 |
| Corrected XML/artifact audit | `python -B -`, resolve artifact path before reading drive | `turn6-outcomes-final.log` | All 1079 PASS; exactly three added nodes, none removed; old 22 PASS; M3 cwd escape/source preservation confirmed; EXIT 0 |
| Adjudication persistence | `python -B -` | `turn6-adjudication-write.log` | Turn-5 findings and depth readings persisted; EXIT 0 |
| Report update | `python -B -` | `turn6-report-write.log` | F1/F3/F4 fixes and both new API IDs/reasons recorded; EXIT 0 |
| Final scope/blob audit | `python -B -` with git/AST/raw-byte checks | `turn6-final-scope.log` | Exactly four authorized files vs 215817a; removing ONE added WP4.2a function reconstructs the old file exactly; ONE WP4.2b function with three rows; no old node removed; zero CR for all four raw changed blobs; EXIT 0 |

```text
uv run --no-sync pytest -q -rf -rs tests/test_jobs_naming.py tests/test_wp42b_naming_guard.py tests/test_headless_export.py tests/test_wp42a_runner_hardening.py tests/test_jobs_export.py tests/test_jobs_export_photo.py tests/test_jobs_export_support.py tests/test_jobs_export_video.py -m "not gpu and not footage and not slow" --deselect=tests/test_headless_export.py::test_g1_inside_sees_every_spelling_of_the_same_folder --deselect=tests/test_headless_export.py::test_g1_main_refuses_every_footage_check_through_another_spelling[unc] --deselect=tests/test_headless_export.py::test_g1_the_redactor_hides_the_extended_spellings --basetemp=work/wp4.2b/tmp-turn6-light --junitxml=work/wp4.2b/turn6-light.xml -o junit_family=xunit1 -p sandbox_mkdir_shim -p no:cacheprovider
```

The twelve deselections are unchanged: three authorized UNC nodes and nine
marker exclusions. XML set comparison with turn 4 proves exactly the two
twin cases and one runner row were added, no prior node removed. All 22
prior failures remain individually PASS. Current unedited controls also
PASS: no-footage 302-312, refused-request 315-324, invalid-suffix 327-340.
Only test/report remediation occurred; no source/runner/fixture/config or
interface edit. Owner verification loop: confirm F1 with M1 survivor ->
add positive twin -> M1 RED / real GREEN; confirm F3 route with one-letter
probe -> add one row -> original-rule M3 RED / real GREEN; settle report
clarity -> full light gate/outcome audit GREEN. No further issue found.
Own-window two-leg gate, Reviewer B and Reviewer A round 2 remain pending.
