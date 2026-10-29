# WP4.2b -- output-name containment in jobs.naming (DR-80)

**DRAFT -- for Reviewer A**

The implementation and requested light checks are GREEN. Reviewer A round 1
returned NO_NEW_CRITICAL_MAJOR (one minor and four advisory findings); its
non-blocking remediation is complete. Reviewer A round 2, Reviewer B and the
full two-leg gate are outstanding; this is not acceptance.
Base: `f991254`. Turn-2 WIP: `f1a6bba`; turn-3 STOP record: `79b60d9`.
The governing CHARC rulings `0c8d52528a11b714`, `050c52106cd8c6ad` and
`8262cd59b0d48c73` are recorded verbatim in the ledger. The last grants ONE
added file-form twin in WP4.2a for both APIs; the seat also grants the
`[engine-drive-relative]` row inside the ONE WP4.2b runner test.

## Behavior and scope

`_base_plan` (`src/clearwater/jobs/naming.py:291-311`) validates the composed
unnumbered name, `base + extension`, before constructing `OutputPlan`. It
rejects `/`, `\`, `:`, a name unequal to `Path(name).name`, or a nonempty
`os.path.splitdrive(name)[0]`. Video's retained extension is included, so
`x.mp4:s` is refused as well as `c:x.jpg` and `carrier:x.jpg`.

The colon ban is a portability rule under spec N1: POSIX permits colons in
filenames, but composed output names must avoid Windows drive and stream syntax.

`OutputNameError(ValueError)` at `naming.py:53` identifies the source by
`source.name` only, never a folder. It is exported from `clearwater.jobs`.
Existing `except ValueError` callers still catch it; the ten direct refusal
cases assert both that compatibility and the specific exported subclass.
Suffix validation still raises ordinary `ValueError`.

Both public planners call `_base_plan` first (lines 339 and 396), before
naming filesystem reads or reservations. Numbering only appends `_<N>` to the
checked base; checking once covers later candidates. A raising path property
would instead fail mid-loop. Direct manual `OutputPlan` construction remains
unchanged, as allowed by the ruling. The suffix validator's other bans are
not extended to source stems: `* ? " < > |`, controls, `..`, trailing dot/space
and the temporary marker are not added to this guard.

Scope delta authorized by CHARC: one public exception class and its jobs
export; one new catch in `check_outputs` plus its import; the existing
WP4.2a test file edited only for the two same-drive flips, exact refusal text,
eight drive-relative plants and the planted file-form control's isolation.
The round-1 remediation adds only the granted positive file-form twin and
engine-drive-relative row, with report/ledger updates; no product edit.
No frozen-interface, dependency, composition or export-engine edit.

## Runner and engine routes

`tools/headless_export.py:724-727` catches `OutputNameError` before its broader
`ValueError` catch. It raises name-only, ASCII-safe `RunnerRefusalError` before
any job, yielding CLI exit 2. Other `ValueError`s still continue to the engine:
`test_invalid_suffix_stays_an_engine_refusal` passed unedited. The original
parent and file-form guards below the catch (lines 728-736) are byte-for-byte
unchanged and remain defence in depth.

With `footage_folder=None`, `check_outputs` still returns before planning.
The real photo engine reads/stats at `src/clearwater/jobs/export.py:711-712`,
then calls `_plan` at 753; video probes at 808 and calls `_plan` at 837.
`_plan` calls `plan_output` at 679. `_run` catches at 607-608 and `_describe`
at 634-641 prefixes the actual exception type and ASCII-escapes the text.
This unchanged route reports `<source>: OutputNameError: <message>` as a
failed item with status 1, without a traceback. Other engine `ValueError`s
retain their existing description route.

## RED/GREEN and controls

Turn 2 RED on unmodified product code: all eight source-stem cases and both
video-extension cases failed `DID NOT RAISE ValueError` (`red-planners.log`).
All 696 fixture controls passed: every manifest path (87), both media kinds,
both planners and explicit-folder/beside-source settings at the default
suffix, compared with independently composed spec paths. No legitimate
fixture output name or path changed.

The ONE WP4.2b runner test function,
`tests/test_wp42b_naming_guard.py::test_naming_refusal_is_readable_and_writes_nothing`,
retains `[engine]` and `[before-jobs]` and adds `[engine-drive-relative]`.
The first pair uses real `carrier:input.jpg` ADS data and proves the engine
failed-item / configured-preflight routes. The new row uses a real one-letter
carrier matching the test folder's drive, the engine route with no footage
preflight, a relative output folder and an empty monkeypatched cwd. It proves
the drive-relative cwd-escape route separately from multi-letter ADS coverage.
All rows use real composition/reader, no stat or reader double; all paths
are per-test tmp_path children. They check readable name-only refusal, no
traceback, empty output/cwd and unchanged carrier main data and source stream.
The before-jobs spy checks zero job calls and CLI exit 2. All three ADS rows
ran successfully here; no OS-refusal skip occurred.

Approved deviation from brief task 4: the turn-2 FINAL ruling replaced
nonexistent `c:input.jpg` plus a reader double with a real
`carrier:input.jpg` JPEG stream and the real reader, because
`ExportEngine._photo` stats the source before planning (`export.py:712`).
The new parameter row restores automated coverage of the one-letter,
relative-output escape while keeping ONE test function. Reviewer A's F3
engine-route probe on a real `c:input.jpg` stream is recorded in
`C:\Users\rwsmy\clearwater-review-evidence\wp4.2b\r1\review.txt`; the cell's
independent equivalent is `work/wp4.2b/turn5-probes-ok.log`. Both found a
name-only OutputNameError, empty output/cwd and unchanged source data.

Original runner RED on base attempted a stream output, created `out/carrier`,
then failed rename with WinError 87; source data remained unchanged
(`red-runner.log`). Turn 4 RED before the exception/catch change: `[engine]`
reported plain ValueError instead of OutputNameError, `[before-jobs]` returned
1 instead of 2, and the invalid-suffix control passed: **2 failed, 1 passed**,
EXIT 1 (`turn4-red.log`).

Turn 4 GREEN: **1076 passed, 12 deselected, zero failures/errors/skips**,
EXIT 0 (`turn4-light.log`, `turn4-light.xml`). XML checks independently confirm
all 22 previously failing nodes, both real-ADS cases, the unchanged suffix
control and the guard controls passed (`turn4-outcomes.log`). The deselections
are the three explicitly authorized UNC nodes plus nine marker exclusions.
No additional suppression or skip was introduced.

Round-1 F1 was independently CONFIRMED: removing the final file-form branch
IN MEMORY left the existing 126 selected tests green, just like baseline.
The new positive twin, parameterized `[run]` and `[main]`, keeps that branch ON
and plants the old stream path to bypass only naming. It checks REFUSED_FORM,
name-only text, no jobs and no writes; run raises RunnerRefusalError and main
returns 2. Under M1 both cases are RED (2 failed, EXIT 1); on the real runner
both are GREEN. The original negative planted control remains unchanged.

The new drive-relative row is also RED with the original unchecked
_base_plan restored IN MEMORY (M3): the job completes and writes
`input_corrected.png` in the isolated cwd instead of the output folder.
The test fails its required failed-item assertion (1 failed, EXIT 1).
Both source streams remain unchanged. On the real runner all five focused
cases pass (EXIT 0). No tracked product file was mutated.

Final turn-6 light set: **1079 passed, 12 deselected, zero failures/errors/skips**,
EXIT 0 (`turn6-light.log`, `turn6-light.xml`), using the same command/UNC
exclusions as turn 4. XML comparison proves exactly three added node IDs,
none removed, and all original 22 failures still PASS. Evidence:
`turn6-m1-red.log`, `turn6-m3-red.log`, `turn6-green.log`,
`turn6-outcomes-final.log`.


The two same-drive cases below intentionally flip from accepted output to
REFUSED: DR-80 refuses every colon, including the formerly normalized
same-drive spelling. They now assert planner/preflight refusal, zero jobs,
empty output/stand-in footage, name-only text and unchanged main/stream data.
Their original node IDs are retained; no WP4.2a test was deleted or added.

## Reviewer A edit list and assertion evidence

Line spans below refer to the completed turn-4 tree. A helper-only text
change lists both the consuming node and helper span. The negative-call
controls formerly at :272/:285 are unchanged, now functions at lines
302-312 and 315-324; both passed. They prove planning is skipped, as CHARC's
second ruling corrects. The eight planted drive-relative cases are the
actual parent-guard coverage. The planted file-form control passed at
258-275 with all original defect-catching assertions intact.

`work/wp4.2b/turn4-wp42a.diff` is the exact git diff against `79b60d9`.
`turn4-diff-evidence.log` (EXIT 0) verifies:

- All original assertions are retained outside the two authorized behavior
  flips and the two exact-text expectation changes. No assertion is weakened
  by the plants: only the planner source moves to a plant, and a parent-drive
  assertion is added to strengthen fidelity.
- That turn-4 audit changed no WP4.2a test IDs or parametrizations. Under
  `8262cd59b0d48c73`, turn 6 adds only the one twin function with run/main
  cases; every pre-existing WP4.2a function remains identical to `215817a`.
- The entire runner AST matches the WIP head after removing only the new
  import/catch; the parent/file-form guard text is identical.
- All eight plants match the unchanged old `OutputPlan.path` composition for
  their folder/media/drive cases; each plant has parent `<letter>:`.

Reviewer A should check that fidelity explicitly against the following list.

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
| `tests/test_wp42a_runner_hardening.py::test_output_file_form_check_refuses_planted_stream_before_jobs[run]` | 279-299 | coverage of the file-form layer after naming pre-empts real names |
| `tests/test_wp42a_runner_hardening.py::test_output_file_form_check_refuses_planted_stream_before_jobs[main]` | 279-299 | coverage of the file-form layer after naming pre-empts real names |

The edited-node list includes the planted file-form control, which was already passing, while the previously failing-node list includes the unedited stream-enumerator `[after-refusal]` case, which becomes green through the new exception catch.
The two newly added twin cases likewise appear only in the edit list.

All 22 previously failing node IDs, independently checked PASS in turn-6 XML:

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

## Checks, verification loop and acceptance transfer

Final turn-6 `ruff check .`: all checks passed, EXIT 0
(`turn6-ruff-check.log`). `ruff format --check .`: 261 files already formatted,
EXIT 0 (`turn6-ruff-format.log`). Mypy: no issues in 141 source files, EXIT 0
(`turn6-mypy.log`). Full commands/counts are in the ledger. Every pytest run
used the sandbox mkdir shim and disabled cacheprovider; installed dependencies
were reused read-only with uv run --no-sync and PYTHONPATH=scripts;src.

Owner verification loop: R1 F1 confirmed by a surviving M1 mutation -> the
positive twin granted and added -> both APIs RED under M1 and GREEN on the
real runner. F3 was already authorized/recorded; report now states that
approved deviation explicitly, names both independent one-letter probes,
and the new row catches original drive-relative writing under M3. F4's
list difference is explained. F2 (unreachable literal '..') and F5 (cosmetic
local rebinding / mandated retained name) are BANKED in the ledger, with no
code change. Final light checks and independent outcomes/scope audits find
no additional issue; no product revert or unresolved scope question.

This remediation's diff against `215817a` is exactly four files: the two
tests, this report and the ledger. The WP4.2a delta is ONE added twin test
only; the WP4.2b delta is ONE parameter row and its source/output setup.
`turn6-final-scope.log` records the final audit, including raw blob IDs and
zero CR bytes for every changed file. All product files, prior WP4.2a test
functions, frozen interfaces, dependencies, local config and stray .venv
remain unchanged. No owner footage was written; scratch stayed under work/.

WP4.2b merges FIRST. The dispatcher rebases WP4.2 at its next yield before
its task 5 and resolves any runner-branch conflict at the seat. This package
gets its OWN posted two-leg window after review convergence, not a stack.
No heavy run or reviewer run was performed by this cell this turn.

For CHARC (proposed on accept): **DR-80 CLOSED by WP4.2b** -- both jobs.naming
planners reject a composed output name that is not one portable name component
before constructing a plan; drive/stream spellings in the stem or retained
video extension cannot reach output-path composition. WP4.2a's parent and
file-form checks remain as defence in depth. The runner refuses an
`OutputNameError` before jobs (exit 2). The engine failed-item route remains
in force when footage preflight is disabled. Closure awaits the accept.
