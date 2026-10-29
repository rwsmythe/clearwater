# WP4.2a runner hardening

Status: DRAFT -- for Reviewer A. Turn-3 cleanup on `d5c9ae3` plus working diff.
Static checks and the permitted sandbox light run pass. The dispatcher resolved
the UNC STOP as a sandbox artifact and verified the full light suite at its seat.
Reviewer A, the full two-leg gate and acceptance are pending.

## Changes and regression evidence

| Function / owned site | Result | New test node in `tests/test_wp42a_runner_hardening.py` |
|---|---|---|
| `_write_form_refusal`, `write_target_refusal` | Factor predicate (i) into one implementation. Folder checks retain their existing refusal reasons and precedence. | `test_stream_named_output_is_refused_before_jobs`, `test_output_file_form_check_has_a_planted_control` |
| `check_outputs` | Both output-folder modes additionally check each planned photo/video FILE from frozen `final_output_path`. No footage means no check; RefusedRequest skips file planning; naming ValueError stays with the engine's refusal. | `test_stream_named_output_is_refused_before_jobs` (8 cases), `test_stream_output_on_hard_link_leaves_original_unchanged` (2 cases), `test_no_footage_still_skips_output_checks`, `test_refused_request_does_not_plan_an_output`, `test_invalid_suffix_stays_an_engine_refusal` |
| `Redactor` apostrophe forms | Each existing form gains its escaped-apostrophe counterpart. Match quoted spellings before an ordinary parent can consume their prefix; preserve original-form ordering. | `test_apostrophe_folder_in_refused_suffix_is_hidden`, `test_apostrophe_folder_in_record_and_summary_is_hidden` (5 forms) |
| Redactor construction in `main` (both paths), `run`, `record_object` | OSError / RuntimeError becomes a safe, pathless usage refusal; main returns 2 without traceback. The argument-error guard includes `_folders_named_in`, which stays unchanged. Library callers get RunnerRefusalError. Main also catches safe refusals propagated from later construction. | `test_resolve_failure_is_a_cli_usage_refusal` (6 cases), `test_resolve_failure_is_a_library_refusal` (4 cases) |
| Two N10 assertions in `tests/test_wp41_photo_path.py`; `equal_statistics` and k=1 assertion in `tests/test_wp41_v8.py` | Compare dtype, shape and bytes; signed zero differs. | `test_signed_zero_is_distinct_in_bit_comparisons` (4 actual comparison sites; AST execution avoids running GUI tests in a new parallel-leg test) |

Files: `tools/headless_export.py` (only owned functions/forms/construction wraps,
plus the top-level `clearwater.jobs` import line explicitly granted by turn-2
ruling 1); new `tests/test_wp42a_runner_hardening.py`; the four granted comparison
sites in `tests/test_wp41_photo_path.py` and `tests/test_wp41_v8.py`; this report;
`docs/proofs/wp4.2a-ledger.md`. No mixed-pin edit was needed. No `src/`, frozen
interface, dependency, local config or harness file changed.

All 36 new cases passed in the light run, without skips or hardware/GUI/footage/
slow markers. Every write is under the per-test tmp_path; logs are under
`work/wp4.2a/`. Stand-in footage only; no test names or reads the real footage
folder. The real ADS reproduction creates a valid JPEG stream and an output
carrier hard-linked to a stand-in original; refusal preserves original data
bytes, its full stream names/sizes, and the output folder's sole carrier entry.

## Revised Limit: the footage check

One predicate, `write_target_refusal`, decides the folder and runner-owned file
write targets before anything runs when a footage folder is configured: each
output folder as `jobs.naming` plans it (`--out`, or the source's own folder
beside a source), the record file, the `--settings-dir` folder and its
`settings.json`. Each planned output FILE path, photo and video alike, also
passes predicate (i) through `_write_form_refusal`, the same helper called by
`write_target_refusal`.

A target passes only if (i) after its drive or UNC prefix it has no `:` (no NTFS
stream name) and is not a `\\?\` or `\\.\` path; (ii) every existing path on
the way down is its own real path (no symbolic link, junction or other reparse
point, and no short 8.3 name, so a link or short name is refused even when it
leads elsewhere); (iii) the real path of the deepest existing one is outside
the footage folder (compared resolved, prefix-free, case-normalised and, where
the footage folder exists, by file identity; a file system without file
identities falls back to the text comparison). For planned output files,
(ii)/(iii) remain on their folder as ruled; (i) additionally checks the file.

Residual: a hard link to a footage file placed outside the footage folder cannot
be told apart by its path. The runner never writes over an existing file (D84),
so only a stream name could reach the original, and (i) refuses every stream
name, including source-derived output FILE names. A link created after the check
(during the run) is not seen. With no configured footage folder, this check
continues to check nothing.

## DR-79 (b): executed reproduction

Not reproduced on Python 3.12 / Windows. Specifically, project Python 3.12.13
on win32 returned paths for both `(loop / 'x').resolve()` with a self-loop
junction created by `mklink /J`, and the directory symlink-loop variant. Both
were successfully created under tmp_path, bounded subprocesses completed, and
only the link entries were removed. No capability skip; no outside-sandbox
reproduction is needed for these two topologies. See the two
`RESOLVE_OBSERVATION` lines in `work/wp4.2a/red-all.log`.

The construction wraps are defensive. Path-selective monkeypatches independently
demonstrate OSError and RuntimeError handling; this report does not claim that
either real topology raised. No exception message with a full path is printed
when redactor construction fails.

## Validation and verification-loop record

| Run / evidence under `work/wp4.2a/` | Result |
|---|---|
| `red-all.log` | 26 failed, 4 passed, 3 deselected, EXIT=1. Intended regression failures plus one initial AST-selector test bug. |
| `red-bits.log` | Corrected controls: all 4 actual comparison sites RED, EXIT=1. |
| `green-guard-2.log` | 14 passed, 22 deselected, EXIT=0. |
| `green-quote-2.log` | 6 passed, 30 deselected, EXIT=0. |
| `green-resolve.log` | 10 passed, 26 deselected, EXIT=0. |
| `green-bits.log` | 4 passed, 32 deselected, EXIT=0. |
| `mypy.log` | Success: no issues found in 141 source files; EXIT=0. |
| `ruff-check.log` | Initial E501 on new test line 143; EXIT=1; corrected by turn-3 formatter cleanup. |
| `ruff-format-check.log` | Initial 3 files would be reformatted, 257 already formatted; EXIT=1; corrected in turn 3. |
| `light.log` | Initial 337 passed, 3 failed, 2 deselected; EXIT=1. Sandbox-only UNC failures resolved by the dispatcher's FINAL ruling. |
| `unc-probe.log` | Standalone pathlib administrative-share probe raises PermissionError, EXIT=1, without importing runner. |
| Dispatcher seat on `d5c9ae3` (turn-3 message) | Three UNC names: 4 passed; full light suite: 340 passed, 2 deselected in 26.64 s. Dispatcher-supplied evidence; no log path supplied. |
| `t3-format.log` | 3 files reformatted; EXIT=0. No behavior change: ASTs identical to `d5c9ae3` in `t3-ast-check.log`, EXIT=0. |
| `t3-ruff-check.log` | All checks passed; EXIT=0. |
| `t3-format-check.log` | 260 files already formatted; EXIT=0. |
| `t3-mypy.log` | Success: no issues found in 141 source files; EXIT=0. |
| `t3-light.log` | 337 passed, 5 deselected, EXIT=0. The three authorized, seat-verified UNC nodes explicitly deselected, plus 2 marker exclusions. No skips. |

Every cell pytest run used `PYTHONPATH=scripts`, `sandbox_mkdir_shim`,
`no:cacheprovider`, and a fresh basetemp under `work/wp4.2a/`. Exact commands,
intermediate attempts and per-node RED/GREEN results are in the ledger.

Confirmed and fixed: source-derived stream output bypass; escaped apostrophe
redaction; construction exceptions; signed-zero numeric equality. The quote
GREEN attempt exposed a parent-prefix ordering problem in the added forms,
fixed before its successful rerun. Rejected as product evidence: initial AST
selector bug and the first planted test's expectation about pytest's rendered
assertion text; both were test-only corrections. Rejected as an executed real
loop failure: both topologies returned paths. Turn 3's diff contains only
formatter edits in code/tests, with matching ASTs, and the checks above pass.
The full two-leg verification and independent review remain pending.

## Resolved sandbox STOP and outstanding work

Three existing nodes in unchanged `tests/test_headless_export.py` fail only in
the sandbox:

- `test_g1_inside_sees_every_spelling_of_the_same_folder`
- `test_g1_main_refuses_every_footage_check_through_another_spelling[unc]`
- `test_g1_the_redactor_hides_the_extended_spellings`

All fail at the unchanged `_unc_extended` helper's `LOCAL_SHARE.is_dir()` probe
(line 612), `\\localhost\C$\`, with PermissionError / WinError 5. The standalone
pathlib probe confirms the environment failure independently of this change.
No existing test was weakened or edited to bypass it.

The dispatcher's turn-3 FINAL ruling resolves this STOP as a sandbox artifact,
not a defect: the three names selected 4 passing cases, and the full light
command passed 340 cases with 2 deselected at its seat on `d5c9ae3`. The permitted
sandbox rerun explicitly deselected the three listed nodes and passed the
remaining 337, with 5 total deselected. No test was changed to accommodate the
sandbox. Formatting cleanup is complete. Reviewer A and the full two-leg suite
remain pending; do not treat this draft as completion or closure.

For CHARC, proposed closure at acceptance: **DR-78 CLOSED; DR-79 CLOSED,
including (a) escaped apostrophe redaction, (b) defensive construction handling;
not reproduced on Python 3.12 / Windows, and (c) all four dtype/shape/byte
comparisons with signed-zero controls.** The dispatcher updates the register
only at acceptance; no debt-register edit is part of this package.
