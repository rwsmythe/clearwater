# WP4.2b -- output-name containment in jobs.naming (DR-80)

**DRAFT -- for Reviewer A**

Base: `f991254`; round-0 ledger commit: `e5983bd`. Implementation is limited
to `src/clearwater/jobs/naming.py`'s validation and the two public planning
functions' `Raises:` documentation. Existing tests, frozen interfaces,
dependencies, export engine, composition and runner are unchanged.

## Validation and placement

`_base_plan` (`src/clearwater/jobs/naming.py:287-307`) validates the whole
composed unnumbered name, `base + extension`, before constructing `OutputPlan`.
It rejects `/`, `\`, `:`, a name unequal to `Path(name).name`, or a nonempty
`os.path.splitdrive(name)[0]`. `ValueError` identifies only `source.name`:
`output name for '<source name>' must be a single portable name component`.
The video extension is included, protecting `x.mp4:s` as well as source stems.

The colon ban is a portability rule under spec N1: POSIX permits colons in
filenames, but the composed output name must also avoid Windows drive and
stream syntax.

Both public planners call `_base_plan` first: `final_output_path` at line 335
and `plan_output` at line 392. Folder scanning, source/collision checks and
reservations occur later. Collision numbering adds only `_<N>` to the checked
base, so the same component guarantee holds for every candidate. Validating
the property instead would raise during candidate checks and reservations.
Direct manual construction of `OutputPlan` is unchanged, as allowed by the
ruling's `_base_plan` alternative.

The suffix validator's other restrictions are not extended to source stems:
`* ? " < > |`, controls, `..`, trailing dot/space and the temporary marker are
not added to this guard. Existing source, collision and temporary-name rules
are unchanged.

## RED/GREEN evidence

All runs used the sandbox mkdir shim and disabled pytest's cache provider.
Logs live under `work/wp4.2b/`; exact commands and exits are in
`docs/proofs/wp4.2b-ledger.md`.

The following node families were run RED on unmodified product code:

- `tests/test_jobs_naming.py::test_composed_output_name_is_refused`, all 8
  combinations of `c:x.jpg`/`carrier:x.jpg`, photo/video and final/plan.
- `tests/test_jobs_naming.py::test_video_extension_stream_is_refused`,
  `[final]` and `[plan]` for `x.mp4:s`.

All ten failed with `DID NOT RAISE ValueError`. The same run passed all 696
`test_wp23_fixture_names_keep_output_paths` cases: every one of the manifest's
87 paths, both media kinds, both planners, explicit output folder and beside
source, default suffix. Expected names are composed from the spec's naming
contract independently of the production planners. No legitimate fixture
output name or path changes. Evidence: `red-planners.log`, EXIT 1.

The ONE runner test is
`tests/test_wp42b_naming_guard.py::test_naming_refusal_is_readable_and_writes_nothing`.
It uses the real `composition.export_jobs()`, the real photo reader, an actual
JPEG ADS named `carrier:input.jpg`, and library `run(..., footage_folder=None)`.
There is no reader double or stat double. The carrier, source stream, output
folder and empty cwd all live under the test's `tmp_path`. A platform or ADS
creation refusal produces an explicit skip; no such skip occurred here.

RED on base: the engine attempted a stream temporary/output name, created
`out/carrier`, then failed its rename with `OSError: [WinError 87] The parameter
is incorrect`. The test failed its empty-output-folder assertion. Its earlier
assertions verified the carrier main data and JPEG source stream were
unchanged. All attempted writes stayed under `tmp_path`.
Evidence: `red-runner.log`, EXIT 1.

GREEN after the validation: the whole naming file plus the runner test passed
**822 tests**, no skips, EXIT 0 (`green-naming.log`). The runner now observes
one failed item whose message starts `carrier:input.jpg: ValueError:`, with no
folder spelling or traceback in failure, summary or captured output/logging.
The output folder and cwd are empty, and both source data streams are
unchanged.

## Engine refusal route and defence in depth

The real photo path reads the source at `src/clearwater/jobs/export.py:711`
and stats it at line 712 before calling `_plan` at line 753. This is why the
turn-2 ruling requires a real ADS source instead of the brief's nonexistent
source plus reader double. `_plan` calls `plan_output` at line 679.
The video path probes at line 808 and calls `_plan` at line 837.

`_run` catches the naming exception at lines 607-608. `_describe` at 634-641
adds the exception type (ValueError is outside `_READABLE_ERRORS`, line 106)
and ASCII-escapes the text. It returns a failed item rather than a traceback.
The library failed-item route has status 1 via
`tools/headless_export.py:874-886`; it is not a CLI usage refusal with exit 2.

WP4.2a's parent check remains at `tools/headless_export.py:719-724`, followed
by its file-form check at 725-727, as defence in depth. Its existing
`except ValueError` at 717-718 leaves a naming refusal to the engine; with
`footage_folder=None`, preflight returns at 697-698. None of this runner code
was changed.

## Checks, verification loop and acceptance status

- `ruff check .`: PASS, EXIT 0 (`ruff-check-final.log`).
- `ruff format --check .`: 261 files already formatted, EXIT 0
  (`ruff-format-final.log`). Initial import-order and wrapping issues in the
  new runner test were fixed in that file only.
- `mypy`: no issues in 141 source files, EXIT 0 (`mypy.log`).
- Broader requested light set: **22 failed, 1053 passed, 12 deselected**, zero
  skips, EXIT 1 (`light.log`). Three UNC nodes were deselected as authorized;
  nine other deselections came from the requested marker filter.

**STOP -- existing-test scope boundary.** All 22 failures are in the unchanged,
unowned `tests/test_wp42a_runner_hardening.py`: eight stream-preflight cases,
eight drive-relative-plan cases, the real stream/cwd case, two same-drive
accepted-output cases, the enumerator's after-refusal setup, and two
hard-link/preflight cases. Full IDs and mechanisms are in the ledger and
`work/wp4.2b/light-failures.txt`. These expectations require unchecked plans,
or pre-job runner refusal; the mandated naming refusal now supersedes them
through the existing choice-3 route. Recommended disposition: commission a
test-only reconciliation of those expectations while preserving direct
parent/file-form guard coverage. No existing test was edited or suppressed.

Verification loop: the round-0 missing-source premise was independently
confirmed and resolved by the dispatcher's real-ADS ruling. RED confirmed
all ten missing planner refusals and the actual stream-writing attempt;
the validation fixes them, with the full naming file and real runner GREEN.
The broader run confirmed the suspected existing-runner expectation conflict;
it remains unresolved at the owned-file tripwire. No false-positive rejection
or product revert. `final-scope.log` (EXIT 0) confirms exactly five owned files
changed, original naming-test content preserved apart from new imports/tests,
ONE new runner test, zero CR bytes and a clean diff whitespace check.
Verification has not converged. Reviewer A, Reviewer B and the posted two-leg
gate are outstanding; the gate request is held for the scope ruling. This
draft does not claim acceptance or DR-80 closure.

For CHARC (proposed closure on accept): **DR-80 CLOSED by WP4.2b** -- both
jobs.naming planners reject a composed output name that is not one portable
name component before constructing a plan; drive/stream spellings in the
stem or retained video extension cannot reach output-path composition.
WP4.2a's parent and file-form checks remain as defence in depth.
