# WP4.2b -- output-name containment ledger

| Turn / round boundary | Dispatcher-read depth / tokens | Disposition |
|---|---|---|
| Turn 1 / round 0 | Pending dispatcher reading; no figure supplied | Read and map only; yield before RED |

Base: `f991254`, branch `wp4.2b`. Dispatch: orchestrator generation 18,
FINAL brief on CHARC `5c056d647ad9ca99`. Scope: DR-80 naming containment.

## Round 0 -- STOP: runner-test premise

**Recommended answer:** permit a source-specific stat double in the ONE new
runner test, in addition to its required reader double. Return the WP2.3
still's stat for the exact synthetic source and delegate every other stat to
the real implementation. This changes only the new test; no change to
`export.py`, composition, the runner, existing tests or interfaces is needed.
Await the dispatcher's ruling before building it.

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

Both `final_output_path` (line 324) and `plan_output` (line 380) call this
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

## RED-first roster for the next authorized build turn

All tests below are additions; existing tests remain byte-for-byte unchanged.
IDs are planned names, not collected or executed pytest node IDs yet.

| Planned test in `tests/test_jobs_naming.py` | Matrix | Expected result on base |
|---|---|---|
| `test_composed_output_name_is_refused` | `c:x.jpg`, `carrier:x.jpg` x PHOTO/VIDEO x `final_output_path`/`plan_output` (8 cases) | RED: no required `ValueError`; the unchecked composed name reaches a path |
| `test_video_extension_stream_is_refused` | `x.mp4:s` x both planners, VIDEO (2 cases) | RED: colon-bearing extension is retained instead of refused |
| `test_wp23_fixture_names_keep_output_paths` | Every manifest entry x both kinds x explicit output folder/beside source x both planners (696 checks) | PASS: unchanged default-suffix names and paths |

For each refusal case, construct the synthetic source from a full string
(`Path(f"{tmp_path}{os.sep}{name}")`), rather than joining a colon-bearing
child with `/`; assert its basename first. Assert `ValueError` includes the
source name and excludes the folder spelling. Sources need not exist for
these direct naming tests. Execute the refusal tests on unmodified product
code first and retain the failing node IDs and summaries before implementing
the guard, then run the complete naming file GREEN.

ONE new runner test is planned:
`tests/test_wp42b_naming_guard.py::test_naming_refusal_is_readable_and_writes_nothing`,
parameterized over a stand-in footage folder and None. Subject to the STOP
ruling above, use the required real composition plus reader double and a
source-specific stat double. Use a string-built `c:input.jpg`, output-folder
setting, force CPU, and an empty per-test cwd. Assert failed item, source name
and `ValueError` in readable failure/summary, no folder spelling or traceback,
no outputs, and empty output/cwd folders. Before the fix, configured-footage
preflight refuses the escaped parent rather than returning this failed item;
without footage preflight, planning is not rejected with the required naming
`ValueError`. This test must distinguish those base paths from the fixed path.
No hardware/timing markers; all new tests belong to the parallel leg.

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
| 0 | No Reviewer A run; read/map STOP above | N/A | N/A | N/A | 0 | None; ledger only | Codex cell; reviewer not invoked | Pending dispatcher |

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
