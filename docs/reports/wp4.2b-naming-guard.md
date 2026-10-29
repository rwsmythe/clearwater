# WP4.2b -- output-name containment in jobs.naming (DR-80)

**DRAFT -- for Reviewer A**

The implementation and requested light checks are GREEN. Reviewer A round 1,
Reviewer B and the full two-leg gate are outstanding; this is not acceptance.
Base: `f991254`. Turn-2 WIP: `f1a6bba`; turn-3 STOP record: `79b60d9`.
Both scope rulings, CHARC `0c8d52528a11b714` and `050c52106cd8c6ad`, are recorded
verbatim in `docs/proofs/wp4.2b-ledger.md` and govern this build.

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
now has `[engine]` and `[before-jobs]` cases. Both use a real JPEG ADS named
`carrier:input.jpg`, real composition and reader, no stat or reader double.
All carrier/stream/output/cwd paths are per-test `tmp_path` children. The
engine case uses `footage_folder=None`; the preflight case uses a stand-in
footage folder and a forwarding job spy to prove zero job calls and exit 2.
Both check name-only text, no traceback, empty output/cwd, and unchanged
carrier main data and source stream. ADS creation worked here; no skip.

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

The two same-drive cases below intentionally flip from accepted output to
REFUSED: DR-80 refuses every colon, including the formerly normalized
same-drive spelling. They now assert planner/preflight refusal, zero jobs,
empty output/stand-in footage, name-only text and unchanged main/stream data.
Their original node IDs are retained; no WP4.2a test was deleted or added.

## Reviewer A edit list and assertion evidence

Line spans below refer to the completed turn-4 tree. A helper-only text
change lists both the consuming node and helper span. The negative-call
controls formerly at :272/:285 are unchanged, now functions at lines
278-288 and 291-300; both passed. They prove planning is skipped, as CHARC's
second ruling corrects. The eight planted drive-relative cases are the
actual parent-guard coverage. The planted file-form control passed at
258-275 with all original defect-catching assertions intact.

`work/wp4.2b/turn4-wp42a.diff` is the exact git diff against `79b60d9`.
`turn4-diff-evidence.log` (EXIT 0) verifies:

- All original assertions are retained outside the two authorized behavior
  flips and the two exact-text expectation changes. No assertion is weakened
  by the plants: only the planner source moves to a plant, and a parent-drive
  assertion is added to strengthen fidelity.
- No WP4.2a test or parametrization was added, deleted or changed.
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

All 22 previously failing node IDs, now independently checked PASS in XML:

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

Final `ruff check .`: all checks passed, EXIT 0
(`turn4-ruff-check-final.log`). Final `ruff format --check .`: 261 files
already formatted, EXIT 0 (`turn4-ruff-format-final.log`). Mypy: no issues
in 141 source files, EXIT 0 (`turn4-mypy.log`). Initial wrapping findings
were fixed in the new runner test only. Full light command and every run's
exit/counts are in the ledger; all pytest runs used the sandbox mkdir shim
and disabled cacheprovider. Installed dependencies were reused read-only
with `uv run --no-sync` and `PYTHONPATH=scripts;src`.

Owner verification loop: missing-source premise confirmed and resolved by
real ADS; unsafe naming/write attempt confirmed RED and fixed; the 22 old
runner conflicts confirmed, scope amendments obtained and implemented;
RED/GREEN and the independent assertion/plant/outcome audits confirm the
new routes and compatibility controls. Final pass found no additional
issue. No false-positive rejection or product revert. The only deviations
from the original brief are the explicitly recorded governing rulings.
No unresolved scope question remains. Review/gate work remains outstanding.

Only the eight owned files changed; `turn4-final-scope.log` (EXIT 0) confirms
the restricted naming/export deltas, complete node lists in both documents,
zero CR bytes and a clean diff whitespace check. Frozen interfaces, dependencies, local config,
composition and export engine are unchanged. No owner footage was written;
test media came from shared fixtures and scratch stayed under the worktree.

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
