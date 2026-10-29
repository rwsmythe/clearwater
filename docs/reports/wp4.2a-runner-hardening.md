# WP4.2a runner hardening

Status: FINAL. Reviewer A converged at round 2 on `7addc2b`, verdict
`NO_NEW_CRITICAL_MAJOR`; its terminating cleanup fixes N2's argument-discovery
redaction leak and corrects the report; pre-existing N1/N5 are banked below. The
orchestrator's two-leg gate on the candidate is GREEN and Reviewer B returned
`NO_NEW_CRITICAL_MAJOR` (see "Erratum at the gate").

## Changes and regression evidence

| Function / owned site | Result | New test node in `tests/test_wp42a_runner_hardening.py` |
|---|---|---|
| `_write_form_refusal`, `write_target_refusal` | Factor predicate (i) into one implementation. Folder checks retain their existing refusal reasons and precedence. | `test_stream_named_output_is_refused_before_jobs`, `test_output_file_form_check_has_a_planted_control` |
| `check_outputs` | Both output-folder modes check each planned photo/video FILE from frozen `final_output_path`. Its parent must equal the checked folder, before the shared form check. No footage means no check; RefusedRequest skips planning; naming ValueError stays with the engine. | `test_stream_named_output_is_refused_before_jobs` (8), `test_stream_output_on_hard_link_leaves_original_unchanged` (2), `test_drive_relative_output_is_refused_before_jobs` (8), `test_drive_relative_stream_cannot_write_into_footage_cwd`, `test_same_drive_stream_output_keeps_checked_parent` (2), and the no-footage / refused-request / invalid-suffix controls |
| `Redactor` apostrophe forms | Each existing form gains its escaped-apostrophe counterpart. Match quoted spellings before an ordinary parent can consume their prefix; preserve original-form ordering. | `test_apostrophe_folder_in_refused_suffix_is_hidden`, `test_apostrophe_folder_in_record_and_summary_is_hidden` (5 forms) |
| Redactor construction in `main` (both paths), `run`, `record_object` | OSError / RuntimeError from those construction expressions becomes a safe, pathless usage refusal. The argument-error guard includes unchanged `_folders_named_in`; if discovery silently drops a given spelling, main uses the same generic refusal instead of partially redacting argparse's text. Library callers get RunnerRefusalError; main catches propagated construction refusals. Earlier footage-check errors, mixed separators and post-batch races are separate limitations below. | `test_resolve_failure_is_a_cli_usage_refusal` (6 cases, sibling cwd), `test_resolve_failure_is_a_library_refusal` (4 cases) |
| Two N10 assertions in `tests/test_wp41_photo_path.py`; `equal_statistics` and k=1 assertion in `tests/test_wp41_v8.py` | Require dtype/shape/bytes equality AND the original numeric equality, so signed zero differs and NaNs remain unequal. | `test_signed_zero_is_distinct_in_bit_comparisons` (4), `test_nan_remains_unequal_in_all_four_comparisons` (4); actual pixel assertion expressions are executed through AST extraction without GUI test execution |
| `_streams` in the new regression file | Enumeration must succeed on both initial and post-refusal calls; no enumeration failure becomes a skip. Capability skips remain at actual ADS/link creation. | `test_stream_enumeration_failure_is_not_a_skip` (2 planted failures: initial / after refusal) |

Files: `tools/headless_export.py` (only owned functions/forms/construction wraps,
plus the top-level `clearwater.jobs` import line explicitly granted by turn-2
ruling 1); new `tests/test_wp42a_runner_hardening.py`; the four granted comparison
sites in `tests/test_wp41_photo_path.py` and `tests/test_wp41_v8.py`; this report;
`docs/proofs/wp4.2a-ledger.md`. No mixed-pin edit was needed. No `src/`, frozen
interface, dependency, local config or harness file changed.

All 53 new cases passed in the hardening and light runs, without skips or hardware/GUI/footage/
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

The added invariant is: **every planned output file's parent is the checked
output folder**. `check_outputs` compares Path objects without resolving them:
`output.parent` must equal `Path(request.settings.output_folder)` for `--out`,
or `request.source.parent` for beside-source mode. This happens after the
existing folder check and successful planning, before predicate (i). A mismatch
is a usage refusal naming only the source basename. Thus drive-relative joins
cannot redirect this runner's output into the process cwd or another drive.

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

One-letter source streams need the parent invariant because pathlib can
reinterpret their stem as a drive prefix before predicate (i) sees the output.
With relative `--out`, `c:input.jpg` previously yielded
`c:input_corrected.png`; a RED real-ADS export, with cwd set to a tmp_path
stand-in footage folder, returned 0 and wrote `input_corrected.png` there. It
now returns 2 before any job starts. Safe same-drive joins, including absolute
folders and drive-relative `--out C:out` with a same-letter source, are allowed
when pathlib drops the source colon and retains the checked parent. The latter
plans `C:out/input_corrected.png`, still inside the checked `C:out` folder;
the actual absolute-folder control exports land at `<tmp_path>/out/input_corrected.png`, or
`<tmp_path>/src/input_corrected.png` in beside-source mode. These have no stream
name in the planned output, and predicate (i) still refuses every output stream
name it receives.

The root cause is the drive-relative join in product code
`jobs/naming.py`, `OutputPlan.path` (`folder / (stem + extension)`). This package
does not own or change it. The join remains reachable by callers other than
this guarded runner.

## Resolution and race boundaries (Reviewer A F3/F4/F6)

The defensive exception conversion covers the four Redactor construction
expressions. In library `run` with a footage folder configured, the earlier
`check_outputs` / `inside` resolution can still raise a raw OSError or
RuntimeError. This call order predates WP4.2a; it is not a promise of generalized
filesystem error conversion. `main` has the same residual: its redactor is built
before those checks but never holds the footage folder, so a raising resolution
of the footage folder in `check_outputs` / `_check_own_paths` / `inside` escapes
`main` as a raw exception carrying that path (unchanged from `aa4761b`; Reviewer B
F1, banked with N1).

Outside the static-path envelope, a mid-run folder change can make later
`summary_lines` / `record_json` construction fail after jobs have already run.
Main can then return 2 despite completed work; failure during record
serialization can leave an empty newly created record file. This is an
unfixed race residual, not covered by the pre-run no-jobs guarantee. Changing
`_write_record` or broadening the status contract is outside this package's
ownership. The dispatcher owns any follow-up commissioning.

Existing folder-refusal texts and within-request priority remain unchanged.
New file guards run in request order, so a request-1 file refusal may precede
a request-2 folder refusal; either stops the run before jobs. The approved
per-request check does not introduce a global two-pass refusal priority.

Typed-contract boundary (Reviewer A round 2 N4): `Settings.output_folder` is
typed `Path | None`; the runner's `main` passes a `Path` when `--out` is given.
A library caller
violating that contract with a `str` output folder now gets `TypeError` from
`check_outputs`; accepting strings is not part of this package's API grant.

## Reviewer A convergence and banked findings

Round 1 on `a05c13e`: `NEW_CRITICAL_MAJOR_FOUND` (1 major, 1 minor, 5 advisory).
F1's checked-parent guard, F2's NaN-preserving comparisons and F5's enumeration
failure assertions were fixed RED-first in turn 5. F3/F4/F7 were documented;
F6 was declined under the approved per-request checks.

Round 2 on `7addc2b`: `NO_NEW_CRITICAL_MAJOR` (0 critical, 0 major, 3 minor,
2 advisory; all NEW). This terminates Reviewer A under the fill. The reviewer
ran 127 passing cases including UNC, and its old-runner F1 control produced
9 failed / 13 passed on `a05c13e`. The dispatcher separately reports 357 passed,
2 deselected for the full light command on `7addc2b`, UNC included.

Terminating cleanup: N2's strengthened
`test_resolve_failure_is_a_cli_usage_refusal[argument-discovery-OSError]`
changes cwd to a sibling of the failing folder, so the cwd cannot mask a leak.
It fails both on `aa4761b` and on `7addc2b` with an unredacted argparse path.
The owned argument-error construction wrap now detects incomplete discovery
without another filesystem call and prints the generic usage refusal; all six
CLI exception cases pass. This corrects the earlier claim that the discovery
OSError parameter was merely an already-safe control. `_folders_named_in` is
unchanged. N3's safe drive-relative folder case and N4's typed boundary are
documented here. No further Reviewer A round is opened.

Banked outside this cleanup's ownership:

- N1 (MINOR, pre-existing): known-folder spellings have no arbitrary mixed
  separators. An argparse refusal for `--bit-depth C:\a\b/c` can still print
  that path. The reviewer reproduced this on base `aa4761b`.
  `git log -S 'path.as_posix()' -- tools/headless_export.py` identifies
  WP4.1 commit `f7e7442`, which introduced raw, doubled-backslash and forward-slash
  forms. The present grant adds escaped apostrophes only; no mixed-form fix.
- N5 (ADVISORY, pre-existing): the unchanged scalar branch of
  `equal_statistics` equates float32 `+0.0` and `-0.0`.
  `git log -S 'return bool(got == expected)' -- tests/test_wp41_v8.py`
  identifies WP4.1 commit `715fd08`. Current statistics are dicts of `ndarray`,
  reaching the strengthened array branch; the scalar branch is outside the four
  granted comparisons and remains unchanged.

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
| `t5-red.log` | 15 failed, 2 passed, 36 deselected; EXIT=1. Nine drive-escape cases, four NaN cases and two enumeration controls RED; both safe same-drive real exports already pass. |
| `t5-green.log` | Same selection after remediation: 17 passed, 36 deselected; EXIT=0. |
| `t5-hardening.log` | All 53 hardening cases passed, no skips/deselections; EXIT=0. Logs actual same-drive output paths, caught planted failure and both loop observations. |
| `t5-format.log` | 1 file reformatted, 3 left unchanged; EXIT=0. |
| `t5-ruff-check.log` | All checks passed; EXIT=0. |
| `t5-format-check.log` | 260 files already formatted; EXIT=0. |
| `t5-mypy.log` | Success: no issues found in 141 source files; EXIT=0. |
| `t5-light.log` | 354 passed, 5 deselected; EXIT=0. The three authorized UNC nodes explicitly deselected, plus 2 marker exclusions; no skips. |
| `t6-red-base.log`, `t6-red-head.log` | Each 1 failed, 52 deselected; EXIT=1. Strengthened N2 case leaks a full path on `aa4761b` and `7addc2b` respectively. The base runner is loaded by an ignored scratch pytest plugin. |
| `t6-green.log` | 6 passed, 47 deselected; EXIT=0. All CLI resolve-error routes, sibling cwd. |
| `t6-ruff-check.log` | All checks passed; EXIT=0. |
| `t6-format-check.log` | 260 files already formatted; EXIT=0. |
| `t6-mypy.log` | Success: no issues found in 141 source files; EXIT=0. |
| `t6-light.log` | 354 passed, 5 deselected in 26.01 s; EXIT=0. Three seat-verified UNC nodes explicitly deselected, plus 2 marker exclusions; all 53 new cases pass, no skips. |

Every cell pytest run used `PYTHONPATH=scripts`, `sandbox_mkdir_shim`,
`no:cacheprovider`, and a fresh basetemp under `work/wp4.2a/`. Exact commands,
intermediate attempts and per-node RED/GREEN results are in the ledger.

Confirmed and fixed: source-derived stream output bypass; escaped apostrophe
redaction; construction exceptions; signed-zero numeric equality. The quote
GREEN attempt exposed a parent-prefix ordering problem in the added forms,
fixed before its successful rerun. Rejected as product evidence: initial AST
selector bug and the first planted test's expectation about pytest's rendered
assertion text; both were test-only corrections. Rejected as an executed real
loop failure: both topologies returned paths. Reviewer A round 1 then confirmed
the drive-relative escape (F1), NaN weakening (F2), and overly broad enumeration
skip (F5). Each has a distinguishing RED test and a GREEN result above. F3/F4
are explicitly bounded here; F6's requested global priority change is declined
under the approved per-request design; F7's status and Limit are refreshed.
Reviewer A round 2 found N2's false control and associated leak; both are
corrected in the terminating cleanup as described above. N1/N5 are banked with
origin evidence, N3/N4 documented. The full two-leg verification remains pending.

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
sandbox turn-5 rerun explicitly deselected the three listed nodes and passed
the remaining 354 cases, with 5 total deselected. No test was changed to
accommodate the sandbox. Reviewer A converged at round 2; the two-leg suite and
Reviewer B results are in "Erratum at the gate".

## For CHARC

- Closure at acceptance: **DR-78 CLOSED**: one predicate (i) now checks every
  planned output FILE, with the checked-parent invariant containing the
  runner's drive-relative naming route.
- Closure at acceptance: **DR-79 CLOSED**, including (a) escaped-apostrophe
  redaction; (b) defensive construction handling, **not reproduced on Python
  3.12 / Windows**; and (c) all four dtype/shape/byte comparisons with signed-zero
  and NaN controls. N2's suppressed-discovery error route is handled pathlessly.
- Register-row candidate (N1): pre-existing mixed-separator argparse redaction
  leak, origin WP4.1 `f7e7442`, reproduced on `aa4761b`. Commission broader known
  spelling coverage separately; this package owns escaped apostrophes only.
  Reviewer B F1 belongs with it: a raising resolution of the footage folder escapes
  `main` raw with the full path (`tools/headless_export.py` `_main`, unchanged from
  `aa4761b`; defensive only, not reproduced on Python 3.12 / Windows).
- F1's root cause is REGISTERED as DR-80 (CHARC, `0f138ff`): the drive-relative join
  in `jobs.naming.OutputPlan.path` accepts a source stem resembling a drive prefix;
  callers other than this runner can still plan outside their intended folder. The
  fix is WP4.2b (Codex lane); this runner's parent check stays as defence in depth.
- Banked N5: scalar statistics signed zero, origin WP4.1 `715fd08`, outside the
  four granted lines; current dict-of-ndarray statistics take the guarded branch.

The dispatcher updates the register only at acceptance; no debt-register edit
is part of this package.

## Erratum at the gate (orchestrator, 2026-10-29)

- **Two-leg gate** at the orchestrator's seat on the candidate `wp4.2a-mc` `c4eab41`
  (WP4.2a rebased onto main `d5d4b00`; main `work\` config): PARALLEL 4539 passed /
  1 skipped (`test_color_roundtrip.py:121`), 644.49 s, EXIT 0; SERIAL 1126 passed /
  1 skipped (`test_photo_check.py:139`), 2,540.97 s, EXIT 0. 4539 = WP4.1's gate 4486
  plus the 53 new hardening cases; the serial leg is unchanged (no serial-leg test
  added).
- **Reviewer B** (the Claude pass at the orchestrator's seat, `claude-opus-5-5`,
  high, on `c4eab41`): `NO_NEW_CRITICAL_MAJOR`; all seven claims hold (claims 2, 3,
  4, 6 and 7 by EXECUTED probes, including a 216-combination apostrophe fuzz with 0
  leaks). Findings: F1 MINOR (pre-existing: `main` lets a raising footage-folder
  resolution escape; the "Resolution and race boundaries" sentence above is
  replaced accordingly, banked with N1); F2 ADVISORY (`test_loop_resolution_reproduction`
  is an observation, not a regression test, though it is counted in the 53); F3
  ADVISORY (a library caller passing a `str` source now gets `AttributeError` from
  `check_outputs` in `--out` mode too; `run` already raised it on base, `main` always
  passes a `Path`); F4 ADVISORY (a same-drive one-letter stream source writes a plain
  file in the checked folder whose name drops the stream syntax, safe, numbered on a
  collision); F5 ADVISORY (the logs this report cites under `work/wp4.2a/` are the
  cell worktree's; they are copied to the main working folder
  `work\wp4.2a\cell-logs\`, the gate logs to `work\wp4.2a\gate-logs\`).
