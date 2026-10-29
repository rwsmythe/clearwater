# WP4.2a runner hardening: cumulative ledger

## Depth and tokens (dispatcher supplied)

| Turn / gate | Dispatcher-read depth or tokens | Source / disposition |
|---|---|---|
| Turn 1 / round 0 | Pending dispatcher reading | No figure supplied at dispatch. The dispatcher reads the Codex `tokens used` footer and fills this table; the cell does not estimate its depth or run `scripts/cell_depth.py` against an unidentified transcript. |

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
| `final_output_path`, `src/clearwater/jobs/naming.py` | Frozen naming function validates suffix, chooses photo PNG / video source extension, and protects the source name. Call it; never change it. `MediaKind` and `final_output_path` are exported by `clearwater.jobs`. Function-local imports in `check_outputs` avoid touching the unowned top-level import block. |
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
| 0 | `aa4761b` / turn 1 | N/A | N/A | N/A | N/A | N/A | 0 | Neither: ledger only | Reviewer not run | Pending dispatcher | Read/map complete; YIELD for go before building. |

## Execution record

| Turn / round | Command or run | Counts / EXIT | Evidence |
|---|---|---|---|
| 1 / 0 | Read-only `git status --short`, `git branch --show-current`, `git rev-parse --short HEAD` | Clean; `wp4.2a`; `aa4761b`; EXIT 0 | Tool output this turn; no runner log or heavy run. |

## Current disposition

Round-0 note complete. No scope discrepancy or ruling question identified.
Await the dispatcher's go and actual token/depth reading before tasks 3-6.
DR-78 and DR-79 remain OPEN until implementation, validation and acceptance;
the dispatcher owns the eventual debt-register closure. No mailbox post.
