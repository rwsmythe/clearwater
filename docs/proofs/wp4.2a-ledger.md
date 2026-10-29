# WP4.2a runner hardening: cumulative ledger

## Depth and tokens (dispatcher supplied)

| Turn / gate | Dispatcher-read depth or tokens | Source / disposition |
|---|---|---|
| Turn 1 / round 0 | `tokens used` 77,213; input depth 88,453 / 475,000 | Dispatcher supplied on turn 2; driver log, 02:21:57Z start. |
| Turn 2 / build | `tokens used` 127,137; input depth 134,393 / 475,000 | Dispatcher supplied on turn 3; 02:26:28Z start. |
| Turn 3 / cleanup | `tokens used` 140,058; input depth 146,457 / 475,000 | Dispatcher supplied on turn 4. |
| Turn 4 / Reviewer A round 1 adjudication | Pending dispatcher reading | No self-estimated depth; dispatcher reads this turn's footer. |

Evaluation point: approximately 250K; STOP at a round boundary at approximately
400K, using the dispatcher's reading.

## Contract and workspace

- Brief: `docs/briefs/wp4.2a-brief.md`, FINAL; CHARC `c8340144a8e87c09`.
  R1-Q1, R1-Q2, the DR-79 (b) correction and R1-Q5 govern.
- Verified starting branch `wp4.2a`, HEAD `aa4761b`, clean working tree.
- Turn 1 is read/map and this ledger ONLY. No implementation, test file,
  reproduction, lint run, pytest run, dependency change or commit this turn.
- Changes remain within the brief's exact function/line ownership. No `src/`,
  frozen interface, configuration, harness or dependency edit. All future test
  inputs, hard links, streams and junctions stay under each test's `tmp_path`;
  runner logs and scratch evidence stay under `work/wp4.2a/`.
- WP4.2 task 5 edits the same runner functions; its build waits for this merge.
  The dispatcher owns the round-0-yield-plus-three-hour cap and any stop/rebase.
- Read: dispatch recipe in full; APPLICATION and CLAUDE; model prompting standard;
  review/gate fill; plan 4.1-4.5; spec 8.3-8.4 and N8; runner; naming module;
  WP4.1 report (including Limits and Erratum); relevant existing runner fixtures,
  refusal tests and all four comparison sites. Superpowers' entry skill explicitly
  exempts dispatched subagents; this dispatch's fixed protocol is followed.

## Round 0: grounded map and proposed mechanics

### DR-78: one text predicate, planned output files included

Proposed helper: `_write_form_refusal(target: Path) -> str | None`, immediately
beside `write_target_refusal`. It returns `REFUSED_FORM` for predicate (i), else
None; it performs only the existing stream-name / extended-form text test.
`write_target_refusal` calls it instead of retaining its own copy. Existing
inside-footage reason precedence and folder predicates (ii)/(iii) stay intact.
There is one implementation of the colon / extended-prefix decision.

Grounded anchors on base:

| Mechanic | Surface / proposed change |
|---|---|
| `write_target_refusal`, `tools/headless_export.py:611` | Existing (iii) test precedes the inline (i) checks; replace only (i) with the helper call. |
| `check_outputs`, `tools/headless_export.py:654` | Its None-footage return stays first. Existing `--out` branch's `continue` currently skips any further per-request work; restructure that branch within this owned function so both output-folder modes reach the new file check. |
| `final_output_path`, `src/clearwater/jobs/naming.py` | Frozen naming function validates suffix, chooses photo PNG / video source extension, and protects the source name. Call it; never change it. `MediaKind` and `final_output_path` are exported by `clearwater.jobs`. Turn-2 ruling 1 grants extending the existing top-level jobs import line; use that line, not function-local imports. |
| `RefusedRequest`, runner | Perform the existing folder checks, then skip file planning for this type; its placeholder kind never reaches an engine. |

The file check sits after each request's existing folder check, before moving to
the next request. For every non-refused request, compute
`final_output_path(request.source, request.settings, MediaKind(request.kind))`,
then apply `_write_form_refusal` to that FILE path. A refusal raises
`RunnerRefusalError` with `ascii_text(request.source.name)`, no parent path.
Catch `ValueError` from planning and leave that request to the engine's existing
refusal; `main` already validates suffixes before calling this function.

The revised report Limit will enumerate output folders, each planned output FILE
(photo and video, predicate (i) through the shared helper), record file, settings
folder and `settings.json`. Predicates (ii)/(iii) remain on output folders, as
ruled. The hard-link residual still exists, but source-derived output stream names
are refused before work, making '(i) refuses every stream name' true for outputs.
Links created after checking remain unseen.

### DR-79 (a): apostrophe forms

`Redactor.__init__` currently builds raw, doubled-backslash and forward-slash
spellings, plus `_escaped_pattern`'s non-ASCII escaped and doubled variants.
Extend every existing form with the spelling in which each apostrophe becomes
`\'`; retain the original forms and longest-first replacement. Keep
`_escaped_pattern`'s existing case-equivalent non-ASCII behavior.

The suffix reproduction will include both quote characters, so Python `repr`
actually chooses an apostrophe-escaped spelling instead of avoiding that escape
with double quotes. Usage refusal prints no record; a separate library refusal
record checks `record_json` / `summary_lines` on that same quoted form.

### DR-79 (b): reproduction and construction guards

There are four construction sites, not just the normal CLI path:

| Base anchor | Surface |
|---|---|
| `tools/headless_export.py:726` | `run`, last-resort logging filter |
| `tools/headless_export.py:746` | `record_object`, also reached by JSON and summaries |
| `tools/headless_export.py:1010` | `main`, argparse usage refusal |
| `tools/headless_export.py:1020` | `main`, normal parsed arguments |

Guard construction from given folders against `OSError` and `RuntimeError`,
translate to a name-only `RunnerRefusalError` for library surfaces, and have
`main` return 2 with no traceback or exception text containing the path. The
argument-refusal expression also calls `_folders_named_in`: that function
already suppresses `OSError` but can propagate `RuntimeError` before construction;
the guard around the expression must cover that call too, without editing the
unowned discovery function. No engine job may start after a construction refusal.

Reproduction plan for turn 2, before the defensive change:

1. Under `tmp_path` on Windows, run `cmd /c mklink /J <loop> <loop>` with both
   absolute paths verified under that same `tmp_path`; resolve `loop / 'x'` on
   the project Python and record returned path or exception class. Use a bounded
   subprocess for a possible looping filesystem operation; no performance claim.
2. Try a directory symlink loop under the same test root where privileges allow;
   record its resolution result or the exact capability skip reason.
3. Do not assert that either topology must raise. If neither raises, report
   'not reproduced on Python 3.12 / Windows'; the closure is defensive, not an
   assertion that the register's original reasoned claim was executed.
4. Independently inject each exception class with a path-selective monkeypatch
   of `Path.resolve`, after creating the test directories. Check normal CLI and
   argument-refusal construction, plus library construction surfaces, without
   changing resolution globally for pytest's own paths.

### DR-79 (c): four stricter comparisons

Each array comparison becomes equality of `(dtype, shape, tobytes())` (C-order
logical bytes). No tolerance, cast or array mutation is introduced.

| Owned site on base | Existing comparison | Replacement |
|---|---|---|
| `tests/test_wp41_photo_path.py:514` | `np.array_equal(recording.pixels[0], p)` | Compare dtype, shape and bytes for every pre-encode array against the first. |
| `tests/test_wp41_photo_path.py:528` | `np.array_equal(pixels[0], p)` | Same comparison for decoded arrays. |
| `tests/test_wp41_v8.py:74` | dtype + shape + `np.array_equal(a, b)` | Keep dtype and shape; replace numeric equality with byte equality. |
| `tests/test_wp41_v8.py:162` | dtype + `np.array_equal(preview, written_pixels)` | Compare dtype, shape and bytes. |

The new signed-zero control uses float32 arrays differing only by +0.0 / -0.0:
`np.array_equal` accepts them, whereas all four sites' comparison form rejects
them. Include the real `equal_statistics` helper (its module imports no Qt at
module scope); preserve all existing tests and markers.

## RED-first roster (proposed node IDs)

All new tests live in `tests/test_wp42a_runner_hardening.py`, use `tmp_path`,
and have no `gui`, `gpu`, `footage` or `slow` marker. Controls that should already
pass on the base are explicitly distinguished from regressions.

| Proposed node ID / parameter coverage | Expected behavior on base |
|---|---|
| `test_stream_named_output_is_refused_before_jobs` [run/main x jpg/mp4 x explicit-out/beside-source] | RED: a colon-bearing stand-in source path reaches the engine instead of a usage refusal; assert refusal, source basename only, no job starts and no outputs. Source need not be opened or created as an ADS for this test. |
| `test_stream_output_on_hard_link_leaves_original_unchanged` [run/main] | RED where NTFS ADS and hard links are available: create a valid JPEG in a source carrier's stream and an output carrier hard-linked to a stand-in footage original, all under tmp_path; require refusal before jobs, original bytes and full stream list unchanged. Skip with capability reason otherwise. Enumerate streams independently on Windows, never just directory entries. |
| `test_output_file_form_check_has_a_planted_control` | After extraction, plant a helper that retains folder checks but skips the output FILE; the refusal assertion from the stream regression must fail by its named test/control line. Record the caught failure; do not treat a missing-helper AttributeError on base as RED evidence. |
| `test_no_footage_still_skips_output_checks` | Base control passes: no configured folder means no helper or naming call; same runner behavior. |
| `test_refused_request_does_not_plan_an_output` | Base control passes: placeholder requests remain unopened; planted planning callable detects an accidental call. |
| `test_invalid_suffix_stays_an_engine_refusal` | Base control passes: library request remains an item refusal, no new ValueError escapes `check_outputs`; CLI remains exit 2. |
| `test_apostrophe_folder_in_refused_suffix_is_hidden` | RED: CLI refused suffix leaks the escaped known folder; require exit 2, name only, no output or record created. |
| `test_apostrophe_folder_in_record_and_summary_is_hidden` | RED: the same escaped folder leaks through library refusal record/summary; require basename-only replacement. Cover existing path-form variants, including non-ASCII escaping. |
| `test_resolve_failure_is_a_cli_usage_refusal` [OSError/RuntimeError x parsed/argument-error] | RED: selective resolve failure escapes or fails to redact; require exit 2, no traceback or full path, and no jobs. |
| `test_resolve_failure_is_a_library_refusal` [OSError/RuntimeError x run/record_object] | RED: construction currently leaks the raw exception instead of `RunnerRefusalError`; require safe name-only text and no job starts. |
| `test_signed_zero_is_distinct_in_bit_comparisons` | RED at the real `equal_statistics` helper on base; the four dtype/shape/bytes forms reject signed zero, and `np.array_equal` demonstrably accepts it. Include identical-array and dtype/shape mismatch controls. |
| `test_loop_resolution_reproduction` [self-junction/symlink-loop] | Observation/capability control, no mandated base failure; record actual Python/platform and outcome. |

## Validation and review policy

Turn 1: no runners executed; no RED/green or convergence claims. Read-only git
commands confirmed branch/base/clean state (exit 0). Source inspection confirmed
the four comparison sites and four redactor construction sites.

Turn 2 and later: runner output goes to files under `work/wp4.2a/`; only summary
lines enter the return report. Each RED run precedes its matching change. The
allowed targeted command, adapted to PowerShell environment syntax, is:

```powershell
$env:PYTHONPATH = 'scripts'
uv run pytest -q tests/test_wp42a_runner_hardening.py tests/test_headless_export.py tests/test_wp41_photo_path.py tests/test_wp41_v8.py -m "not gpu and not footage and not slow" --basetemp=work/wp4.2a/tmp -p sandbox_mkdir_shim -p no:cacheprovider
```

Each invocation will have a fresh basetemp beneath that scratch root and its own
log path. An existing-test failure with the file check added triggers STOP,
except the explicitly conditional mixed pin; no mixed-pin change is expected
because `no_footage` bypasses `check_outputs` there. Ruff check, format check and
strict mypy follow implementation. The full two-leg gate is NEVER run by this
cell: yield exact commands/output paths as a RUN REQUEST for the dispatcher.
No harness gate is triggered by this ownership list.

Reviewer A: driver-run Claude Opus/high, STRONG tier, read-only, findings handed
back between turns. Adjudicate every finding and yield after each review round
before remediation as this brief directs. Convergence and round-five continuation
follow the review/gate fill. Reviewer B runs at the orchestrator's seat.

## Cumulative review rounds

| Round | Head / turn | Critical | Major | Minor | In / out envelope | NEW / REOPENED | Reverts | Product / test-only fixes | Transport / version | Depth | Verdict / disposition |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | `aa4761b` / turn 1 | N/A | N/A | N/A | N/A | N/A | 0 | Neither: ledger only | Reviewer not run | 88,453 input; 77,213 tokens used | Read/map complete; committed by dispatcher as `933e33e`; turn-2 GO received. |
| Build | `933e33e` + working diff / turn 2 | N/A | N/A | N/A | In-envelope implementation | No review yet | 0 | Runner tool + four test comparisons + new regressions | Reviewer not run | Pending dispatcher | STOP: three existing tests fail on the sandbox's administrative-share probe; no existing test edited. |
| Cleanup | `d5c9ae3` + working diff / turn 3 | N/A | N/A | N/A | In-envelope formatting | No review yet | 0 | Formatting only, no behavior change | Reviewer not run | Pending dispatcher | Turn-2 STOP resolved by dispatcher seat verification; static and permitted light checks clean; Reviewer A pending. |
| A1 | `a05c13e` / turn 4 | 0 | 1 (F1) | 1 (F2); 5 advisory (F3-F7) | 6 in / 1 out (F4) | 7 NEW / 0 REOPENED | 0 | None this turn; proposed runner + tests + report fixes | Driver-run Claude process; `claude-opus-5-5`, high, STRONG; CLI version not supplied | Pending turn-4 reading | `NEW_CRITICAL_MAJOR_FOUND`; adjudicated below; YIELD before remediation. |

## Execution record

| Turn / round | Command or run | Counts / EXIT | Evidence |
|---|---|---|---|
| 1 / 0 | Read-only `git status --short`, `git branch --show-current`, `git rev-parse --short HEAD` | Clean; `wp4.2a`; `aa4761b`; EXIT 0 | Tool output this turn; no runner log or heavy run. |

All turn-2 commands below ran from the worktree. Pytest prefix:
`PYTHONPATH=scripts uv run pytest`; all pytest calls include
`-p sandbox_mkdir_shim -p no:cacheprovider`. PowerShell set `PYTHONPATH` via
`$env:PYTHONPATH='scripts'`. The light run additionally set
`QT_QPA_PLATFORM=offscreen`. Each log records the runner's `EXIT=` independently
of the surrounding shell's exit status. No two-leg / heavy run occurred.

| Turn / phase | Command (pytest prefix/plugins as above) | Counts / EXIT | Log under `work/wp4.2a/` |
|---|---|---|---|
| 2 / initial RED | `pytest -q -rs -s tests/test_wp42a_runner_hardening.py -k 'not planted_control and not no_footage and not refused_request' --basetemp=work/wp4.2a/tmp-red` | 26 failed, 4 passed, 3 deselected; EXIT=1. One failure was a test-selector bug, not product RED evidence; see below. | `red-all.log` |
| 2 / bit RED | `pytest -q tests/test_wp42a_runner_hardening.py -k signed_zero --basetemp=work/wp4.2a/tmp-red-bits` | 4 failed, 32 deselected; EXIT=1; actual four comparison sites all equate signed zero on the base. | `red-bits.log` |
| 2 / guard first GREEN attempt | `pytest -q -rs tests/test_wp42a_runner_hardening.py -k 'stream or planted_control or no_footage or refused_request or invalid_suffix' --basetemp=work/wp4.2a/tmp-green-guard` | 1 failed, 13 passed, 22 deselected; EXIT=1; planted failure was caught, but the new test expected the wrong pytest-rendered assertion text. | `green-guard.log` |
| 2 / guard GREEN | Same selection with `-s`, `--basetemp=work/wp4.2a/tmp-green-guard-2` | 14 passed, 22 deselected; EXIT=0. Both real ADS/hard-link tests passed, no skips. | `green-guard-2.log` |
| 2 / quote first GREEN attempt | `pytest -q -rs tests/test_wp42a_runner_hardening.py -k apostrophe --basetemp=work/wp4.2a/tmp-green-quote` | 1 failed, 5 passed, 30 deselected; EXIT=1; ordinary parent-pattern ordering consumed a quoted doubled-backslash form's prefix. | `green-quote.log` |
| 2 / quote GREEN | Same selection, `--basetemp=work/wp4.2a/tmp-green-quote-2` | 6 passed, 30 deselected; EXIT=0; new quoted forms now precede ordinary patterns, with their own longest-first ordering. | `green-quote-2.log` |
| 2 / resolve GREEN | `pytest -q -rs tests/test_wp42a_runner_hardening.py -k resolve_failure --basetemp=work/wp4.2a/tmp-green-resolve` | 10 passed, 26 deselected; EXIT=0. | `green-resolve.log` |
| 2 / bits GREEN | `pytest -q tests/test_wp42a_runner_hardening.py -k signed_zero --basetemp=work/wp4.2a/tmp-green-bits` | 4 passed, 32 deselected; EXIT=0. | `green-bits.log` |
| 2 / static | `uv run ruff check .` | One E501 at new test line 143; EXIT=1; not remediated after mandatory STOP. | `ruff-check.log` |
| 2 / static | `uv run ruff format --check .` | 3 files would be reformatted, 257 already formatted; EXIT=1. Files: runner, new test, owned V8 assertion. Not remediated after STOP. | `ruff-format-check.log` |
| 2 / static | `uv run mypy` | Success: no issues found in 141 source files; EXIT=0. | `mypy.log` |
| 2 / light | `pytest -q -rs tests/test_wp42a_runner_hardening.py tests/test_headless_export.py tests/test_wp41_photo_path.py tests/test_wp41_v8.py -m 'not gpu and not footage and not slow' --basetemp=work/wp4.2a/tmp-light` | 3 failed, 337 passed, 2 deselected; EXIT=1. All 36 new cases passed; existing failures trigger STOP. | `light.log` |
| 2 / independent STOP probe | `uv run python -c "from pathlib import Path; print(Path('//localhost/C$/').is_dir())"` | `PermissionError: [WinError 5] Access is denied`; EXIT=1. No runner module imported. | `unc-probe.log` |
| Dispatcher / turn-3 ruling | Three UNC test names via `-k` on `d5c9ae3`, outside sandbox | 4 passed, including both spelling parameters. Dispatcher-supplied evidence, not a cell execution. | Orchestrator's turn-3 message; log path not supplied. |
| Dispatcher / turn-3 ruling | Full four-file light command on `d5c9ae3`, outside sandbox | **sandbox-only; 340 passed at the orchestrator's seat on d5c9ae3**; 2 deselected, 26.64 s. Dispatcher-supplied evidence, not a cell execution. | Orchestrator's turn-3 message; log path not supplied. |
| 3 / before cleanup | `uv run ruff check .`; `uv run ruff format --check .` | E501 is at new test line 143; runner line 715 is a format hunk. One E501, EXIT=1; 3 files would be reformatted, EXIT=1. | `t3-ruff-before.log`, `t3-format-before.log` |
| 3 / cleanup | `uv run ruff format tools/headless_export.py tests/test_wp41_v8.py tests/test_wp42a_runner_hardening.py` | 3 files reformatted; EXIT=0; also fixes the sole E501. | `t3-format.log` |
| 3 / static | `uv run ruff check .` | All checks passed; EXIT=0. | `t3-ruff-check.log` |
| 3 / static | `uv run ruff format --check .` | 260 files already formatted; EXIT=0. | `t3-format-check.log` |
| 3 / static | `uv run mypy` | Success: no issues found in 141 source files; EXIT=0. | `t3-mypy.log` |
| 3 / no behavior change | `uv run python -c <AST comparison of the three formatted files against git show d5c9ae3:path>` | All three parsed ASTs identical (locations excluded); EXIT=0. | `t3-ast-check.log` |
| 3 / light, three authorized UNC nodes deselected | `pytest -q -rs tests/test_wp42a_runner_hardening.py tests/test_headless_export.py tests/test_wp41_photo_path.py tests/test_wp41_v8.py -m 'not gpu and not footage and not slow' --deselect=tests/test_headless_export.py::test_g1_inside_sees_every_spelling_of_the_same_folder --deselect=tests/test_headless_export.py::test_g1_main_refuses_every_footage_check_through_another_spelling[unc] --deselect=tests/test_headless_export.py::test_g1_the_redactor_hides_the_extended_spellings --basetemp=work/wp4.2a/tmp-t3-light` | 337 passed, 5 deselected, EXIT=0. Three seat-verified UNC nodes explicitly deselected plus 2 marker deselections; no skips. Prefix/plugins as above, offscreen Qt. | `t3-light.log` |
| 4 / F1 planning reproduction | `./.venv/Scripts/python.exe -` (stdin pathlib-only probe: join a source-derived `c:input_corrected.png` to relative, different-drive and same-drive stand-in output folders) | Relative and different-drive cases have parent `c:`, outside the checked folder; same-drive absolute case retains the checked parent and drops the stream colon. Assertions pass, EXIT=0. No resolution or test-file writes by the probe; shell output only under work. | `t4-f1-planning.log` |
| 4 / F2 independent probe | `./.venv/Scripts/python.exe -` (stdin NumPy probe of identical float32 NaN arrays) | Original `np.array_equal` False; dtype/shape/bytes True; byte comparison AND original numeric equality False; EXIT=0. | `t4-f2-nan.log` |

## Reviewer A round 1: adjudication only (turn 4)

Review head: `a05c13e`; verdict `NEW_CRITICAL_MAJOR_FOUND`.
Authorized evidence read: ONLY
`C:\Users\rwsmy\clearwater-review-evidence\wp4.2a\r1\review.txt`,
MD5 `36f0ed68fd4e935b70b7e668498b9323`. No other file in the evidence folder
was opened or modified. Model/effort/tier are dispatcher-supplied
(`claude-opus-5-5`, high, STRONG); invocation assertion details and CLI version
were not supplied to the cell. Reviewer pytest was refused by its sandbox:
test-claim checks are REASONED, not executed suite evidence. F1 and F2 are
EXECUTED reviewer probes; the cell independently confirmed their planning and
NaN mechanics using the two logged probes above. No pytest, heavy run, code,
test or report edit this turn. The only tracked change is this ledger.

### Dispositions

| ID | Severity / reachability / evidence | Decision | Reason and precise disposition |
|---|---|---|---|
| F1 | MAJOR; in envelope; EXECUTED | ACCEPT | The new guard misses a required output path shape. The frozen join can reinterpret a one-letter carrier stream as a drive-relative filename. Independently reproduced with pathlib: relative `..\out` and different-drive `D:\stand-in\out` both produce `c:input_corrected.png`, parent `c:`. Fix inside owned `check_outputs`: compare the planned file's parent with the folder already checked, before its shared form check. No frozen naming edit and no second colon test. |
| F2 | MINOR; in envelope; EXECUTED | ACCEPT | Recommend option (a), preserving NaN rejection with one numeric-equality guard expression per site. Keep the new dtype/shape/bytes check AND the original `np.array_equal` result. This is a conservative NaN-rejection guard and also preserves old behavior for any other supported dtype; a report-only qualification would not meet the brief's 'assertions only stricter' lock. |
| F3 | ADVISORY; in envelope; REASONED | ACCEPT-DOC | Disclose the exact boundary: only the four Redactor construction expressions are wrapped. With configured footage, an earlier resolution failure in `check_outputs` can still escape library `run` raw. Base `aa4761b` already calls `check_outputs(requests, folder)` before `Redactor(folders)` (confirmed by `git show`); the turn-2 construction-site grant does not grant wrapping unrelated footage-check operations. No code expansion. |
| F4 | ADVISORY; OUT of envelope; REASONED | ACCEPT-DOC | Disclose the mid-run mutation/race residual: a later redactor failure after jobs have run can yield exit 2, and a failure during record serialization can leave an empty newly created record. The review explicitly requires a mid-run change; the declared static Windows/local-NTFS envelope and owned construction-wrap scope do not authorize changing `_write_record` or the exit-status contract. No race-handling implementation here; dispatcher owns any follow-up commissioning. |
| F5 | ADVISORY; in envelope; REASONED | ACCEPT | Tighten the new test helper: once the test has created its ADS and hard link, a PowerShell enumeration failure must fail, not skip, on either call. Keep capability skips only around actual link/stream creation. This prevents post-refusal enumeration failure from silently discarding preservation assertions. Add a planted enumerator-failure control. |
| F6 | ADVISORY; in envelope; REASONED | DECLINE | New request-1 file refusal now precedes request-2 folder refusal, but all legacy folder texts and within-request precedence remain intact. R1-Q1 requires a per-request FILE check, and turn-2 ruling 3 concurs with reaching it from both folder modes; neither prescribes a new global two-pass ordering. Both shapes refuse before any jobs. Preserve the approved request-order implementation. |
| F7 | ADVISORY; in envelope; REASONED | ACCEPT-DOC | Refresh report status to the actual reviewed/remediated head and update the Limit with F1's checked-parent invariant. Distinguish the pre-fix proven escape from the post-fix boundary; no stale working-diff claim. Include F3/F4's precise disclosures. Report stays untouched this adjudication turn. |

Totals: 0 critical, 1 major, 1 minor, 5 advisory; 6 in envelope, 1 outside;
7 NEW, 0 REOPENED; no reverts or fixes this turn. ACCEPT: F1/F2/F5;
ACCEPT-DOC: F3/F4/F7; DECLINE: F6. The major remains open pending remediation,
verification and the next review disposition. This round does not converge.

### Proposed remediation, pending dispatcher GO

1. **F1 RED-first:** add
   `test_drive_relative_output_is_refused_before_jobs`, parameterized for
   library/CLI and photo/video, covering relative output folders and a
   beside-source one-letter stream on a different drive prefix. Construct the
   source as a full path string (for example `Path(f"{src / 'c'}:input.jpg")`),
   so joining the source itself does not normalize away its colon. A no-write
   job spy must remain untouched. Add
   `test_drive_relative_stream_cannot_write_into_footage_cwd` for the real JPEG
   ADS case where the OS permits: cwd is a tmp_path stand-in footage folder,
   output folder is a relative sibling, and the source carrier letter matches
   the actual cwd drive. Verify usage refusal and no new entry in the stand-in
   footage folder. Add a safe same-drive absolute-output control, because that
   join retains its checked parent and does not need refusal.
2. **F1 implementation:** immediately after successful `final_output_path`
   planning and before `_write_form_refusal(output)` in `check_outputs`, set
   `checked_folder = request.source.parent if folder is None else folder`;
   if `output.parent != checked_folder`, raise `RunnerRefusalError` with exactly:
   `the output for {ascii_text(request.source.name)} would leave its checked output folder.`
   This is a lexical pathlib parent equality check, not a resolve call. It
   closes the drive-reinterpretation escape while keeping (ii)/(iii) on the
   checked folder and (i) solely in `_write_form_refusal`. Existing folder
   checks/refusal precedence remain before this guard; RefusedRequest and
   naming ValueError handling remain unchanged. No new `":"` check.
3. **F2 RED-first:** add
   `test_nan_remains_unequal_in_all_four_comparisons`, executing the real
   statistics helper and the same three extracted pixel assertion expressions
   on identical NaN arrays. It must fail on current byte-only comparisons.
   Preserve signed-zero, dtype/shape and identical-finite controls. At the four
   owned sites conjoin `np.array_equal(first, other)` (with bool conversion
   where required) with dtype/shape/bytes equality. This is option (a)'s
   strictness-preserving NaN guard, without a new helper or dtype special cases.
4. **F5 RED-first:** add
   `test_stream_enumeration_failure_is_not_a_skip`, planting a nonzero
   subprocess result. Translate any caught pytest-skip exception into a failed
   assertion so the current late-skip behavior is demonstrably RED, not an
   apparent capability skip. `_streams` will assert subprocess success rather
   than call pytest.skip. No product change.
5. Run targeted RED/GREEN checks with sandbox plugins and work logs, then ruff,
   format, strict mypy and the allowed light command with the three explicitly
   authorized UNC-node deselections recorded. If a different existing test
   fails, STOP under the standing rule. Update the report for F3/F4/F7, the
   round execution record and final claims. Yield to the driver for the next
   review/gate step; no two-leg suite is run by the cell.

No new dependency, src/interface edit, external write or change to the
one-predicate text test is proposed. Any request to fix F3/F4 in code requires
an explicit envelope/ownership ruling rather than silent scope expansion.

### RED/GREEN by regression node

The filename prefix is `tests/test_wp42a_runner_hardening.py::` throughout.

| Node / parameters | RED observation | GREEN observation |
|---|---|---|
| `test_stream_named_output_is_refused_before_jobs` [8 cases] | Missing library refusal / CLI status 1 instead of 2, `red-all.log`. | All 8 in `green-guard-2.log` and light run. |
| `test_stream_output_on_hard_link_leaves_original_unchanged` [run/main] | Both real ADS cases failed at missing refusal, `red-all.log`; no capability skip. | Both in `green-guard-2.log`; original bytes, full stream names/sizes and output carrier unchanged. |
| `test_apostrophe_folder_in_refused_suffix_is_hidden` | Escaped known basename was not replaced, `red-all.log`. | `green-quote-2.log`. |
| `test_apostrophe_folder_in_record_and_summary_is_hidden` [5 forms] | All 5 retain quoted folder components, `red-all.log`. | All 5 in `green-quote-2.log`. |
| `test_resolve_failure_is_a_cli_usage_refusal` [2 exception classes x 3 routes] | Parsed and constructor routes leak exceptions; discovery RuntimeError leaks. Discovery OSError already passes (existing suppression), so that case is a control, not new RED evidence. | All 6 in `green-resolve.log`. |
| `test_resolve_failure_is_a_library_refusal` [run/record_object x OSError/RuntimeError] | All 4 leak original exception type, `red-all.log`. | All 4 in `green-resolve.log`. |
| `test_signed_zero_is_distinct_in_bit_comparisons` [statistics/pre-encode/decoded/preview] | All 4 actual code forms numerically equate signed zero, `red-bits.log`. | All 4 in `green-bits.log`. |

The initial signed-zero test selected a fourth unrelated assertion
(`len(recording.pixels) == 4`) while extracting three pixel comparisons. This
test-only selector bug was fixed before any comparison-site change; its initial
failure is rejected as product RED evidence. The corrected selector extracts
only array comparisons and all four sites then demonstrably failed on signed zero.

The planted-control node is
`test_output_file_form_check_has_a_planted_control`. A test-local monkeypatch
lets the helper pass PNG file paths while preserving folder checks. It catches
`_assert_stream_refusal`'s `assert status == 2` at new-file line 65, displaying
`assert 1 == 2`; `green-guard-2.log` records the named failure and line. The
plant exists only in the test. The first control run's assertion about pytest's
rendered text was corrected from `status == 2` to `assert 1 == 2`.

### DR-79 (b) executed reproduction

`test_loop_resolution_reproduction[self-junction]` successfully created the
self-junction with bounded `cmd /c mklink /J`, entirely under `tmp_path`, and
`loop / 'x'` resolved to a path. The symlink-loop parameter also successfully
created its loop and returned a path. Both link entries were removed without
recursive traversal. `red-all.log` records both `RESOLVE_OBSERVATION` lines:
Python 3.12.13, platform `win32`, no exception. Both tests also passed in the
light run; no capability skips and no outside-sandbox reproduction needed.

**Result: not reproduced on Python 3.12 / Windows.** DR-79 (b)'s implemented
wrap is defensive. Injected OSError/RuntimeError tests verify the refusal paths;
the original reasoned claim is not reclassified as an executed reproduction.

### Verification-loop record and STOP

| Suspected issue | Independent confirmation / rejection | Disposition |
|---|---|---|
| Source-derived output stream syntax bypasses folder guard | Eight stand-in cases and two real ADS/hard-link cases RED before helper extraction. | Fixed in owned functions; GREEN. |
| Escaped apostrophe leaks known folder | CLI plus five record/summary forms RED. | Fixed; new quoted forms ordered before ordinary parent prefixes; GREEN. |
| Resolve errors escape redactor construction | Nine failing injected paths plus one already-safe OSError discovery control. | Four sites wrapped; main handles propagated safe refusals; GREEN. |
| Self-referential junction / symlink necessarily raises | Executed both on Python 3.12.13 / Windows; both returned paths. | Rejected as reproduced claim; defensive handling retained as ruled. |
| Signed-zero assertions accept unequal bits | Corrected controls execute all four original comparisons and fail. | Four comparisons strengthened; GREEN. |
| Existing UNC tests fail because of the new runner guard | All fail in unchanged `_unc_extended` at `LOCAL_SHARE.is_dir()`; standalone pathlib probe reproduces PermissionError without importing runner. | Turn-3 FINAL ruling: sandbox artifact, not a defect; full light suite passes at dispatcher seat. |

Existing failures (all `tests/test_headless_export.py`):

- `test_g1_inside_sees_every_spelling_of_the_same_folder`
- `test_g1_main_refuses_every_footage_check_through_another_spelling[unc]`
- `test_g1_the_redactor_hides_the_extended_spellings`

All three fail in unchanged helper line 612, probing `\\localhost\C$\`, with
`PermissionError [WinError 5]`, before their UNC assertions. No edits to this
file or tests/conftest.py. The dispatcher resolved this STOP on turn 3: the
three names selected 4 passing cases at its seat; the full light command passed
all 340 selected cases there on `d5c9ae3`. This is a sandbox artifact, not a
defect (FINAL ruling). Future sandbox runs deselect exactly the three failing
nodes; every such execution row discloses those deselections. No test was
weakened or patched.

## Current disposition

Reviewer A round 1 on `a05c13e` found one new major (F1), one minor (F2),
and five advisories. Every finding is adjudicated above. The cell independently
reproduced F1 planning and F2 NaN behavior; only this ledger changed. No code,
test or report remediation this turn. YIELD for dispatcher GO on the precise
plan above. Reviewer A is not converged; full two-leg gate and acceptance remain
pending. DR-78/DR-79 stay OPEN. No mailbox post or evidence-folder write.
