# WP4.3a cumulative ledger

## Dispatch and depth

- Package: WP4.3a, spawn helper and import / redaction hardening; CODEX lane,
  STRONG product-code tier. Binding brief: `docs/briefs/wp4.3a-brief.md`, FINAL
  under CHARC `8fb519bac1878075`; its Q-A/Q-B/Q-C rulings govern.
- Worktree / branch: `.worktrees/wp4.3a` / `wp4.3a`.
- Dispatch base, verified by `git rev-parse HEAD`:
  `fe65e6a867106dd984d1c27ef3104e2ee3de0df4`. Initial `git status --short` was empty.
- Turn 1 is tasks 1-2 only: read and Round 0 note, no product code or tests changed.
- Reviewer A and B: the orchestrator's read-only Claude Opus / high process
  passes. Reviewer A R1 is adjudicated below; remediation, convergence,
  Reviewer B and the final gate remain pending.
- Dispatch overrides older generic instructions: yield after each named task
  group; adjudication turns change only the ledger before yielding; format check
  and the final two-leg gate run at the orchestrator's seat. Both gate expressions
  exclude `fullclip` under the dispatch's AD-30 amendment.

| Turn / boundary | Dispatcher-provided depth | Window of record | Action |
|---|---|---|---|
| Turn 1 footer, supplied at Turn 2 dispatch | `tokens used` 96,223; input depth 102,475 | 258,400 tokens | Dispatcher-read figure for session `01a18856-955d-74e3-b211-dfb519efdf0c`; evaluate near 200K, stop at a step boundary near 250K. |
| Turn 2 footer, supplied at Turn 3 dispatch | `tokens used` 238,706; input depth 146,818 | 258,400 tokens | Dispatcher-read figure; no estimate substituted. |
| Turn 3 footer, supplied at Turn 4 dispatch | `tokens used` 346,443; input depth 205,870 | 258,400 tokens | Past the evaluation point. Turn 4 is explicitly bounded; leave a successor handoff and await the next dispatcher depth. |
| Seat 1 Turn 4 footer, supplied at Seat 2 dispatch | `tokens used` 439,112; input depth 237,170 | 258,400 tokens | Seat 1 retired at this boundary; Seat 2 is a fresh session. |
| Seat 2 Turn 1 (ledger Turn 5) | 86,848 / 258,400; turn-5 tokens used 89,765 | 258,400 tokens | Supplied at Turn 6; no estimate substituted. |
| Seat 2 Turn 2 (ledger Turn 6) | Input depth 154,379; tokens used 161,780 | 258,400 tokens | Supplied at Turn 7. Next turn or two may reach the evaluation point; this review-only turn is bounded. |
| Seat 2 Turn 3 (ledger Turn 7) | Input depth 176,357; tokens used 184,744 | 258,400 tokens | Supplied at Turn 8; last bounded turn in this seat, stop at a step boundary if near 240K. |

## Round 0: observed base

Read `docs/dispatch-recipe.md` in full, `APPLICATION.md`, `CLAUDE.md`, the model
prompting standard, the Clearwater review/gate fill, plan working rules and
definition of done (4.1-4.5), the applicable spec requirements, AD-13 / AD-23, and
DR-58 / DR-76 / DR-77 / DR-81 / DR-85. The dispatched brief and its rulings fix the
implementation; no interface design or spec change is needed.

### Every product spawn

An AST inventory of every Python module under `src/clearwater` found exactly
these seven `subprocess.run` / `subprocess.Popen` calls on the dispatch base.
The source scan also checked subprocess imports/usages for other spawn forms.
All seven remain at the `101f181` line numbers quoted by the brief; none moved.

| Source and line | Mechanic | Current environment |
|---|---|---|
| `src/clearwater/io/video/capability.py:89` | `_run`, `subprocess.run` | `env=tool_env()` at line 95 |
| `src/clearwater/io/video/decode.py:171` | `_check_cuda`, `subprocess.run` | Inherited; no explicit `env` |
| `src/clearwater/io/video/decode.py:330` | `_Process._start`, enlarged pipe, `subprocess.Popen` | Inherited; no explicit `env` |
| `src/clearwater/io/video/decode.py:344` | `_Process._start`, default pipe, `subprocess.Popen` | Inherited; no explicit `env` |
| `src/clearwater/io/video/encode.py:879` | `FFmpegVideoSink._start`, `subprocess.Popen` | `env=tool_env()` at line 884 |
| `src/clearwater/io/video/probe.py:127` | `_run_ffprobe`, `subprocess.run` | Inherited; no explicit `env` |
| `src/clearwater/io/video/verify.py:225` | `_listing`, packet listing, `subprocess.run` | `env=tool_env()` at line 231 |

No product spawn currently sets `creationflags`. The Windows runtime reports
`sys.platform == "win32"` and `subprocess.CREATE_NO_WINDOW == 134217728`.
The inventory result is in `work/wp4.3a/turn1-spawn-inventory.log` (exit 0).

DR-58 (b)'s test-only residual, NOT owned under Q-B:

| Source and line | Mechanic / disposition |
|---|---|
| `tests/test_wp42_v3_product.py:141` | `_encode_lossless` calls `subprocess.run` without `env`; command assignment starts at line **133**, one line earlier than the brief's line 134. Leave unchanged; closure names the residual. |
| `tests/test_wp321_fft_release.py:165` | GPU FFT release test calls `subprocess.run` without `env`. Leave unchanged; closure names the residual. |

Those tests can adopt the cleared environment at their next authorized touch.
Their execution under an operator-set `FFREPORT` is outside this envelope.
DR-58 (a) and DR-81 N5 are not reached.

### Helper signature and import graph

Planned helper in the existing `io/video/pipes.py`:
`tool_spawn_kwargs() -> _ToolSpawnKwargs`, where the private `TypedDict` contains
`creationflags: int` and `env: dict[str, str]`. Each of the seven calls will use
`**tool_spawn_kwargs()`, replacing the three current explicit `env` arguments.
The helper returns `subprocess.CREATE_NO_WINDOW` on `win32`, otherwise `0`, and
a fresh environment copy excluding every case variant of `FFREPORT`.

`capability.tool_env() -> dict[str, str]` remains available and delegates by
returning `tool_spawn_kwargs()["env"]`; it will no longer own a second environment
filter. `pipes.py` currently imports only the standard library and will keep
that property. `probe.py` imports the helper directly from `pipes.py`;
`capability.py` already imports `probe.find_tool`, so importing capability from
probe would create a cycle. All five caller modules can depend on pipes without
that reverse edge. No new `io/video` module is needed; the module-set pin in
`tests/test_io_video_probe_rules.py:31` remains unchanged.

### Failure-text and redaction mechanics

- DR-81 (c): `verify._listing` catches `OSError` and `TimeoutExpired` together at
  lines 233-234 and embeds the raw exception in
  `f"{name} could not be listed: {error}"`. A timeout therefore exposes the
  ffprobe command, including its executable path. The call's timeout at line
  229 is `READ_TIMEOUT_S`, defined as **600** at line 45. The timeout branch will
  name the ASCII-safe input basename and the limit through that constant, with
  no raw exception or command. The constant is unchanged (Q-A).
- Q-C / DR-81 (d): `decode._check_cuda` currently returns
  `ascii_text(f"{type(error).__name__}: {error}")` at lines 178-179 for both
  exceptions. Split the branches: fixed timeout text using
  `CUDA_CHECK_TIMEOUT_S` (30 at line 65); an `OSError` reports only its class and
  `strerror`, excluding `filename` and raw `str(error)`. The existing WARNING
  caller at line 148 stays; regressions assert the returned text.
- DR-81 (a): `Redactor` at runner line 379 builds literal, resolved, plain,
  escaped and quoted forms, but line 412 enumerates uniform separator spellings.
  Match each path separator under arbitrary mixes of slash and backslash while
  retaining case-insensitive, escaped-character, escaped-apostrophe and doubled
  backslash coverage. Continue the existing longest-form ordering and basename
  substitution. Cover the argparse error surface as well as direct redaction.
- DR-81 (b): `main` constructs its known-folder redactor at lines 1286-1295 and
  calls `_main` at line 1298. `_main` calls `configured_footage_folder()` at line
  1309 inside a block catching only `RunnerRefusalError` (line 1323). That
  function maps `LocalConfigError`, but an `OSError` / `RuntimeError` raised by
  resolution can escape. Convert that failure at this route to a path-free or
  redacted usage refusal with exit 2; never print a raw exception whose footage
  folder is not yet known. Inject the failure in tests; do not resolve or read
  the owner's footage.

### Config readers and the synthetic DR-76 fixture

- `presets._read:577` currently maps `(ValueError, RecursionError)` to
  `FormatError`; add `OverflowError` there. Existing wrappers then supply
  `PresetImportError` on import (`:449-450`), `PresetError` on load
  (`_read_preset`), and an unreadable list entry (`:326-329`). No frozen IF-9 edit.
- `settings_store.load_settings:71` has the same incomplete decode tuple; add
  `OverflowError` to use the existing set-aside/defaults route.
- Add `"profile"` to `presets._PROVENANCE_KEYS:69` and the runner's
  `PROVENANCE_KEYS:143`; revise the runner's `read_parameter_file` docstring
  at lines 593-599 to describe the accepted writer provenance. The photo writer
  and its `"profile"` output key stay unchanged.
- Fixture: WP2.3 synthetic `heic8-gradient-none`, through the existing `sample`
  fixture. `tests/test_wp41_photo_path.py:48-52` identifies this family as HEIC
  tagged sRGB by `nclx`, without an ICC profile. No owner's footage is involved.
- Export via the real `clearwater.app.composition.export_jobs()` engine, using
  `Settings(force_cpu=True, output_folder=<tmp_path child>)` and the real method
  parameters. The existing runner `requests_for` / `run` seam can drive it with
  `footage_folder=None`, avoiding local footage lookup. Read the PNG's actual
  `iTXt` text with keyword `clearwater-provenance` (`io/photo/png.py:26`), assert
  that it contains the writer's built-in profile field, and write that text to
  a JSON file under `tmp_path`. Import using the real method schema and assert
  that `profile` is reported in `dropped_keys` and omitted from the stored set.
  Use the same export-and-extract recipe for the runner's `--parameters` test,
  isolating configuration through a test double and keeping outputs in `tmp_path`.

### Planned test roster and RED bases

Names below describe the tests to add; RED outcomes are expected from the source
mechanics above, **not test executions claimed for Turn 1**. Every new test is
parallel-leg, without `gpu`, `footage`, `gui`, `slow` or `fullclip` markers; every
write is under its own `tmp_path`. No new shared fixture or existing-test edit.

| Owned test file | Planned test / cases | Base that it distinguishes and expected RED |
|---|---|---|
| NEW `tests/test_io_video_spawn.py` | `test_every_product_spawn_uses_the_helper` (AST inventory, including aliases) | `fe65e6a`: all seven calls lack helper kwargs; require every call to consume them. |
| Same | `test_only_the_helper_sets_creationflags` (AST pin) | Positive structural guard: baseline has no flags; after helper introduction only its construction may set them. Not claimed as an independent baseline failure. |
| Same | `test_spawn_kwargs_windows_and_other_platforms` (native win32 and monkeypatched other OS) | `fe65e6a`: helper is absent; then assert native constant vs 0, identical environment content, case-insensitive FFREPORT removal and unchanged parent environment. |
| Same | `test_tool_env_delegates_to_spawn_helper` | `fe65e6a`: helper is absent and `tool_env` owns its filter; spy delegation and verify compatibility. |
| Same | `test_ffreport_parent_does_not_make_a_child_report` (FFmpeg and ffprobe) | `fe65e6a`: no helper to protect the launch. Positive control: inherited FFREPORT makes an actual tool write a tmp_path report; protected launch succeeds without a report. |
| Same | `test_packet_listing_timeout_omits_tool_path` | Pre-Task-5 state (also `fe65e6a`): force `_listing` TimeoutExpired with a private tool path; old text leaks it. Assert input basename and the current READ_TIMEOUT_S limit. |
| Same | `test_cuda_check_timeout_omits_command` | Pre-Task-5 state (also `fe65e6a`): forced TimeoutExpired leaks its command. Assert False and text with CUDA_CHECK_TIMEOUT_S, no command/path. |
| Same | `test_cuda_check_oserror_omits_filename` | Pre-Task-5 state (also `fe65e6a`): forced OSError with filename leaks it. Assert False, class and strerror only. |
| `tests/test_config_presets.py` (new tests only) | `test_year_one_created_import_is_a_readable_refusal` | Pre-Task-4 state (also `fe65e6a`): `0001-01-01T00:00:00+01:00` raises OverflowError instead of PresetImportError. |
| Same | `test_year_one_created_load_is_a_readable_refusal` | Same state: stored file raises OverflowError instead of PresetError; file remains intact. |
| Same | `test_year_one_created_is_listed_as_unreadable` | Same state: list_presets raises OverflowError instead of returning an error entry; file remains intact. |
| Same | `test_writer_provenance_import_drops_profile` | Same state: actual HEIC engine-exported provenance is rejected for unknown profile key; assert accepted parameters and dropped profile after fix. |
| `tests/test_config_settings.py` (new tests only) | `test_year_one_created_settings_are_set_aside` | Pre-Task-4 state (also `fe65e6a`): nested last_parameters stamp raises OverflowError; assert defaults, bad-file rename, original bytes preserved and warning. |
| NEW `tests/test_wp43_runner_redaction.py` | `test_parameters_accept_writer_provenance` | Pre-Task-4 state (also `fe65e6a`): CLI --parameters refuses the extracted provenance's profile key; after fix reaches a successful export using that file. |
| Same | `test_redactor_matches_mixed_separators` (ordinary / escaped / quoted forms) | Pre-Task-5 state (also `fe65e6a`): known folder remains visible under a non-uniform separator mix. |
| Same | `test_argparse_redacts_mixed_separators` | Same state: force argparse to quote a mixed-separator spelling of a known folder; expect exit 2, basename retained and private parent absent. |
| Same | `test_raising_footage_resolution_is_a_usage_refusal` (OSError and RuntimeError) | Same state: injected configured-footage resolution error escapes main; expect exit 2, safe stderr and no export calls. |

At each build group, capture RED before the corresponding product edits, then
GREEN with the same cases. Broaden existing-test coverage only as task 6 directs.
WP4.3 owns the DR-85 startup test; it is neither read from the sibling worktree
nor changed here.

## Validation and verification record

| Turn | Suspected / checked | Confirmed / rejected | Fixed / result |
|---|---|---|---|
| 1 | Dispatch anchors may have drifted. | Seven product spawn anchors unchanged; test command assignment at line 133 instead of 134. No scope discrepancy found. | Ledger uses this base's locations; no product edits. |
| 1 | Helper might create a probe/capability cycle. | Source imports confirm capability -> probe; pipes has no package imports. | Planned direct pipes imports avoid the reverse edge. |
| 1 | Timeout limit in historical row might govern code incorrectly. | verify.READ_TIMEOUT_S is 600; probe.TOOL_TIMEOUT_S is 120; Q-A explicitly governs. | Preserve constants; planned text uses READ_TIMEOUT_S. |

- `uv sync --offline`: exit 0, `Resolved 62 packages in 1ms`,
  `Audited 61 packages in 4ms`. Log: `work/wp4.3a/turn1-uv-sync.log`.
  Offline mode honors the dispatch's no-network sandbox; no dependency change.
- AST inventory: exit 0, seven calls, native Windows flag available. Log above.
- Ledger byte check: exit 0, LF only and ASCII. Log:
  `work/wp4.3a/turn1-ledger-check.log`. `git diff --check` passed; the final status
  contains only the new owned ledger.
- No pytest, ruff, mypy, format check or review run in this documentation-only
  rung. No package-completion or regression-pass claim is made.
- Turn 1 locks: only the owned ledger is changed; no frozen interface, GUI, app,
  jobs, photo writer, existing test, dependency or register edit; local config
  untouched; no footage read/write, GPU/network operation, timing/memory
  measurement, mailbox post, commit or sibling-worktree access.
- No STOP, open question or new out-of-envelope finding. The two Q-B residual
  launches remain explicitly deferred by CHARC's ruling.

## Reviewer A cumulative rounds

Round 0 above is a preparation note, not a reviewer round or convergence result.
Evidence is retained by the orchestrator outside the repository under
`C:\Users\rwsmy\clearwater-review-evidence\wp4.3a\rN\` and `reviewB\`.

| Round | Critical | Major | Minor / advisory | In / out of envelope | NEW / REOPENED | Reverts | Product / tests-only fixes | Transport / CLI | Dispatcher depth | Verdict / evidence |
|---|---|---|---|---|---|---|---|---|---|---|
| R1 | 0 | 1 | 2 minor / 6 advisory | 8 in / 1 out after F4 grant (F5 residual); original adjudication 7 / 2 | 9 NEW / 0 REOPENED | 0 | F1/F4/F9 product (3); F2 tests-only (1); F3 report; external R3-1 adds product/tests separately | Orchestrator process via codex_cell.py review; claude-opus-5-5 / high; CLI version not supplied | Turn 5: input 86,848 / 258,400; tokens used 89,765. Turn 6: input 154,379 / 258,400; tokens used 161,780 | NEW_CRITICAL_MAJOR_FOUND; R2 verifies closure of F1/F3/F4/F9 and R3-1; F2 partially reopened; evidence below |
| R2 | 0 | 0 | 1 minor / 4 advisory | 4 in / 1 POSIX out; R2-3 report in, pre-existing redaction repair out of grant | 4 NEW / 1 REOPENED (R1 F2, partial) | 0 | R2-1 tests/control only; R2-2 product message; R2-4 product + test; R2-3/5 report/docstring; cleanup executed Turn 8 | Orchestrator codex_cell.py review; claude-opus-5-5 / high; CLI version not supplied | Turn-6 input 154,379 / 258,400; tokens used 161,780; Turn-7 input 176,357 / 258,400; tokens used 184,744 | NO_NEW_CRITICAL_MAJOR; blocking-axis CONVERGED at R2; terminating cleanup done Turn 8; B/gate pending |

At round 5 and every fifth round thereafter, yield with the cumulative ledger
for approval to continue under the fill. Reviewer B and the final ONE two-leg
gate remain the orchestrator's work after Reviewer A convergence.

## Turn 2: task 3, shared spawn policy

Round 0 was accepted by the orchestrator; its ledger was committed as `a614160`.
This turn implements only task 3. The config and DR-81 text changes remain for
Turn 3, including the still-raw exceptions in verify and decode.

### Produced

- `pipes.tool_spawn_kwargs() -> _ToolSpawnKwargs` returns the two policy kwargs.
  The only new platform-specific branch is in that helper: Windows
  `subprocess.CREATE_NO_WINDOW`, else `0`. It copies the current environment,
  removing FFREPORT in any letter case without modifying the parent.
- All seven product spawn calls consume `**tool_spawn_kwargs()` directly.
  `capability.tool_env` retains its signature and delegates to the helper's
  environment. The helper's module remains standard-library-only. No new module
  or change to the module-set pin.
- Added only `tests/test_io_video_spawn.py`; existing tests remain unchanged.
  Its AST inventory recognizes aliased subprocess module/direct imports, checks
  every discovered run/Popen call, and rejects explicit per-site environment or
  flag overrides. The second AST test requires exactly one flag construction,
  inside the helper, so this structural guard also fails on the original base.

### RED -> GREEN

RED was run at product base `a614160` (only the accepted ledger differs from
`fe65e6a`) after writing the new tests and before any product edit. It returned
exit 1, **6 failed in 1.08s**, with no setup errors. Log:
`work/wp4.3a/turn2-spawn-red.log`.

The unchanged six cases then returned exit 0, **6 passed in 1.17s**, after the
product edit. Log: `work/wp4.3a/turn2-spawn-green.log`.

| Test | Observed RED reason | Observed GREEN |
|---|---|---|
| `test_every_product_spawn_uses_the_helper` | Assertion lists all seven product sites bypassing the helper. | Every discovered product run/Popen consumes helper kwargs without a local env/creationflags override. |
| `test_only_the_helper_sets_creationflags` | Zero flag constructions, expected exactly one in the helper. | Exactly one, within pipes.tool_spawn_kwargs. |
| `test_spawn_kwargs_windows_and_other_platforms` | Shared policy helper absent. | Native Windows constant and monkeypatched Linux zero; literal expected environment, mixed-case FFREPORT exclusion, parent preservation and fresh copies. |
| `test_tool_env_delegates_to_spawn_helper` | Existing tool_env ignores the injected shared policy. | The real compatibility function returns the helper's environment. |
| `test_ffreport_parent_does_not_make_a_child_report[ffmpeg]` | Real inherited-environment positive control wrote a nonempty report; protected launch could not proceed because helper was absent. | Positive-control report exists, actual helper-protected child succeeds, no protected report or other file appears. |
| `test_ffreport_parent_does_not_make_a_child_report[ffprobe]` | Same observed distinction for ffprobe. | Same actual-child result for ffprobe. |

Both tools executed in the sandbox. The child tests require the tools rather
than silently skipping when absent; all reports are in each test's tmp_path.
No hardware, GUI, footage, slow or fullclip marker was added.

### Validation and verification

- `uv run ruff check .`: exit 0, `All checks passed!`.
  Logs: `work/wp4.3a/turn2-ruff.log` and, after formatting the new test,
  `work/wp4.3a/turn2-ruff-final.log` (same exit and summary).
- `uv run mypy`: exit 0,
  `Success: no issues found in 141 source files`.
  Log: `work/wp4.3a/turn2-mypy.log`.
- `uv` emitted the inherited VIRTUAL_ENV mismatch warning and used this
  worktree's project environment; neither runner failed.
- Formatting (write mode, only owned Python files): exit 0, new test file
  reformatted; all six product files unchanged. Logs:
  `work/wp4.3a/turn2-format-test.log` and
  `work/wp4.3a/turn2-format-product.log`. The global `ruff format --check .`
  remains the orchestrator-seat check specified at dispatch.
- The broader permitted run passed: **474 passed, 36 deselected in 502.55s
  (0:08:22)**, exit 0, no skips, failures or errors. It ran every
  `tests/test_io_video_*.py` file plus `tests/test_core_deps.py`, with
  `-q -rA -m "not gpu and not footage and not slow and not gui and not fullclip"`,
  `PYTHONPATH=scripts`, `--basetemp=work/wp4.3a/tmp`,
  `-p sandbox_mkdir_shim -p no:cacheprovider`.
  Log: `work/wp4.3a/turn2-video-layering.log`.
- Passed-node inventory: 474 node IDs, matching the pytest summary.
  Log: `work/wp4.3a/turn2-test-counts.log`.
- Excluded-node collection (no marked test executed): exit 0,
  `36/510 tests collected (474 deselected) in 0.36s`, using the complement
  expression `gpu or footage or slow or gui or fullclip`, with the same shim
  and no cache provider, basetemp `work/wp4.3a/tmp-collect`.
  The exact 36 unrun node IDs are retained in
  `work/wp4.3a/turn2-excluded-collection.log`.
- Final rerun of the formatted new test file: exit 0,
  **6 passed in 1.11s**, using basetemp `work/wp4.3a/tmp-final` and the required
  shim/no-cache options. Log: `work/wp4.3a/turn2-spawn-final.log`.
- Scope/bytes audit: exit 0, exactly eight owned paths changed, all LF;
  `git diff --check` passed. Log: `work/wp4.3a/turn2-scope-check.log`.

All selected pre-existing WP3.7, WP3.9 and WP3.10 tests ran unchanged and green:

| Package / file under tests/ | Passed | Deselected, not executed |
|---|---|---|
| WP3.7 `test_io_video_probe.py` | 83 | 0 |
| WP3.7 `test_io_video_probe_boxes.py` | 45 | 0 |
| WP3.7 `test_io_video_probe_rules.py` | 25 | 1 footage case |
| WP3.9 `test_io_video_decode.py` | 36 | 0 |
| WP3.9 `test_io_video_decode_lifecycle.py` | 32 | 0 |
| WP3.9 `test_io_video_decode_rules.py` | 19 | 0 |
| WP3.9 `test_io_video_decode_hw.py` | 0 | 13 GPU / footage / slow / fullclip cases |
| WP3.10 `test_io_video_encode.py` | 96 | 20 GPU / footage / slow / fullclip cases |
| WP3.10 `test_io_video_encode_units.py` | 80 | 0 |
| WP3.10 `test_io_video_encode_bench.py` | 48 | 2 GPU / slow cases |
| New `test_io_video_spawn.py` | 6 | 0 |
| Layering `test_core_deps.py` | 4 | 0 |
| Total | 474 | 36 |

The requested probe/decode/core layering subset totals 48 passing cases and is
included in this run, not counted a second time. The marked exclusions remain
for the orchestrator's appropriate gate/package windows; this is development
evidence, not the final two-leg gate.

| Pass | Suspected / independently checked | Confirmed / rejected | Disposition |
|---|---|---|---|
| Task-3 RED | Seven launches lack common window/env policy; compatibility filter is independent; helper is absent. | All six regression cases failed for the stated product reasons. Both real tools wrote the positive-control report before the absent-helper assertion. | Added the helper, wired the seven calls, delegated tool_env. |
| Task-3 GREEN | Branch, environment-copy, delegation and real-tool behavior may differ. | All six unchanged tests passed; native Windows flag and other-platform zero both checked. | Fixed within the granted files. |
| Task-3 source pass | Missing/overridden helper at a spawn, extra flag owner, import cycle or module-set change. | AST guards pass; direct pipes imports have no reverse package import; existing module set unchanged. Product diff contains only task-3 policy, imports and related docs. | No new issue found in this pass; later-task exception redaction remains explicitly pending. |
| Task-3 unchanged-suite pass | Spawn kwargs might break existing decode lifecycle, probe rules, encode checks or layer boundaries. | All 474 selected cases passed, including all 48 requested layering cases; 36 marked cases deliberately not executed. Final formatted-file rerun also passed. | No new issue found; no existing test changed to obtain GREEN. |

The tests and product edit should be committed together to keep committed
states green; the RED state is preserved in its log, not as a failing commit.
The ledger accompanies the same logical task-3 commit.

Turn 2 locks: only the eight owned paths changed (the six video modules, new
spawn tests, ledger); no frozen interface, GUI, app, jobs, photo, config,
existing test, dependency, register or local-config edit. No new video module,
unapproved OS branch, network operation, hardware-marked test execution, mailbox
post, commit or sibling-worktree access. No product timing or memory figure
was measured. The inherited-report positive controls wrote only within
tmp_path. No STOP or new open question. The remaining requested seat check is
`uv run ruff format --check .`; no blocked FFmpeg run needs a request.

## Turn 3: tasks 4-5, config readers and failure texts

### Dispatcher-seat QA of Turn 2 (supplied at Turn 3 dispatch)

The orchestrator committed Turn 2 as one green commit, `ef903e5`, and reported:

- Product diff read: the sole helper owns CREATE_NO_WINDOW on win32, all seven
  sites consume it, tool_env delegates, and pipes imports no package module.
- `uv run ruff format --check .`: **268 files already formatted**.
- `QT_QPA_PLATFORM=offscreen uv run pytest -q -rs tests/test_io_video_*.py
  -m "not footage and not fullclip"`: **494 passed, 12 deselected in 640.87 s**.
  Its non-footage decode-hardware, encode and bench cases passed unchanged.

These are dispatcher-supplied seat results, not additional sandbox executions.
No Reviewer A round has been supplied yet.

### Task 4: produced and RED -> GREEN

- Added OverflowError to PresetStore._read's decode-failure mapping and
  load_settings' existing set-aside/defaults mapping; frozen IF-9 is untouched.
- Added profile to the two provenance-key sets. Updated the runner's granted
  parameter-reader docstring and the directly affected PresetImportResult
  dropped_keys docstring. The writer's key and output shape remain unchanged.
- Added three independent preset stamp regressions (import/load/list), the
  settings stamp regression, a real-writer provenance import test, and a real
  CLI --parameters test. A helper in the new runner test file exports the
  synthetic HEIC through composition.export_jobs with force_cpu, reads the PNG's
  actual iTXt through Pillow, and writes its provenance text under tmp_path.
  The preset test reuses that test-only helper; no conftest or shared fixture
  was changed.

All six cases ran before the reader/key edits at product base `ef903e5`:
**6 failed, 180 deselected in 1.62s**, exit 1. Log:
`work/wp4.3a/turn3-config-red.log`.

| Test | Observed RED | Final GREEN |
|---|---|---|
| `test_year_one_created_import_is_a_readable_refusal` | OverflowError escapes import. | PresetImportError, source unchanged, no store created. |
| `test_year_one_created_load_is_a_readable_refusal` | OverflowError escapes load. | PresetError with readable decode reason; file unchanged. |
| `test_year_one_created_is_listed_as_unreadable` | OverflowError aborts listing. | Good entry retained, corrupt entry has error/no parameter set, source unchanged. |
| `test_year_one_created_settings_are_set_aside` | OverflowError escapes load_settings. | Defaults returned, original bytes moved aside, warning names decode failure and defaults. |
| `test_writer_provenance_import_drops_profile` | PresetImportError: unknown keys: profile. | Actual exported metadata preserved as parameters; source/settings/profile reported dropped; stored file has no profile. |
| `test_parameters_accept_writer_provenance` | CLI returns 2: unknown keys: profile. | Same extracted file is accepted by --parameters; real CPU export succeeds, record identifies file parameters. |

The first post-fix run had four passes and two provenance-test expectation
failures: the helper compared exported provenance to the original request.
Independent source trace confirmed jobs.provenance.provenance_object builds a
fresh export timestamp and records effective parameters with defaults overlaid
(jobs/export.py photo export passes those effective parameters). This was a
test expectation error, not another product defect. The helper now constructs
its expected ParameterSet directly from the actual written method, parameter
mapping, timestamp and version. No jobs or interface code changed. The original
RED failures occur at the profile refusal before those comparison assertions.

The corrected six cases passed: **6 passed, 180 deselected in 0.75s**, exit 0.
Log: `work/wp4.3a/turn3-config-green-final.log`. Both real CPU export tests ran
inside the sandbox; no DR-76 run request is needed.

### Task 5: produced and RED -> GREEN

- Redactor now matches every actual path separator independently as slash or
  backslash. Literal Unicode, escaped Unicode, doubled separators/escapes and
  quoted apostrophes retain their separate forms and ordering. Escape
  backslashes generated for Unicode are not treated as path separators.
- Only the configured-footage lookup in _main gained an OSError/RuntimeError
  conversion into a fixed, path-free RunnerRefusalError, handled by the existing
  usage-refusal route (exit 2, before request creation or export).
- verify._listing's timeout branch names the ASCII-safe source basename and
  READ_TIMEOUT_S, without the command or tool path. Its 600-second constant is
  unchanged. Its existing non-timeout OSError handling was not widened.
- decode._check_cuda now returns fixed timeout text through
  CUDA_CHECK_TIMEOUT_S, or the OSError class and strerror only. The existing
  warning caller is unchanged. This implements Q-C's DR-81 (d) disposition.

Before these edits, all 13 task-5 cases failed for their intended reasons:
**13 failed, 7 deselected in 0.91s**, exit 1. Log:
`work/wp4.3a/turn3-redaction-red.log`.

| Test / cases | Observed RED | Final GREEN |
|---|---|---|
| `test_redactor_matches_mixed_separators` (5 forms) | Mixed path remains visible, including raw/doubled/ASCII/ASCII-doubled/quoted forms. | Known child folder shown by its ASCII-safe basename, with no parent prefix. |
| `test_argparse_redacts_mixed_separators` | Quoted invalid integer exposes private parent. | Exit 2, parser reason retained, private parent absent, no configuration lookup. |
| `test_raising_footage_resolution_is_a_usage_refusal` (OSError/RuntimeError) | Injected Path.resolve error escapes main with the unknown folder path. | Exit 2, fixed ASCII-safe refusal, no request/export/output. |
| `test_packet_listing_timeout_omits_tool_path` (native limit / 17) | TimeoutExpired includes ffprobe command and private folders. | Source basename and configured limit present, command/paths absent. |
| `test_cuda_check_timeout_omits_command` (native limit / 19) | TimeoutExpired includes full FFmpeg command. | False plus fixed text with configured limit, no command/path. |
| `test_cuda_check_oserror_omits_filename` | Raw FileNotFoundError includes errno and executable filename. | False plus exactly the error class and strerror. |

The first post-fix pass caught one remaining doubled-literal Unicode form:
the parent matched but the child prefix survived. The failure independently
identified the missing literal-Unicode/doubled-separator pattern. Added that
form, then the same 13 cases passed: **13 passed, 7 deselected in 0.72s**,
exit 0. Log: `work/wp4.3a/turn3-redaction-green-final.log`.

### Requested checks and the STOP finding

- Final focused run, covering all new task-3/4/5 cases: **25 passed,
  180 deselected in 2.15s**, exit 0. Log:
  `work/wp4.3a/turn3-focused-final.log`. Required sandbox shim and no-cache
  provider used throughout, with temp roots under work/wp4.3a.
- Requested broader regression set (every tests/test_config_*.py, spawn tests,
  headless tests, WP4.2a and WP4.2b runner tests, new runner tests):
  **4 failed, 370 passed, 1 deselected in 11.72s**, exit 1. The marker expression
  was `not gpu and not footage and not slow and not gui and not fullclip`.
  Log: `work/wp4.3a/turn3-touched-regression.log`.
- `uv run ruff check .`: initially reported a new-test regex-literal lint and
  local-import order; both corrected in the added test code. Final exit 0,
  `All checks passed!`. Log: `work/wp4.3a/turn3-ruff-final.log`.
- `uv run mypy`: exit 0, `Success: no issues found in 141 source files`.
  Log: `work/wp4.3a/turn3-mypy.log`.
- Formatter write mode on the nine owned Python files: exit 0,
  `1 file reformatted, 8 files left unchanged`. Log:
  `work/wp4.3a/turn3-format.log`. Global format check remains at the seat.
- Final scope/bytes check: exit 0, exactly ten owned paths changed, all LF;
  unowned headless tests unchanged; `git diff --check` passed. Log:
  `work/wp4.3a/turn3-scope-check.log`.

| ID / severity | Finding and evidence | Disposition |
|---|---|---|
| T3-F1 / MINOR, out-of-envelope test alignment | `tests/test_headless_export.py:1093-1105`, `test_b4_a_settings_file_whose_created_stamp_overflows_is_a_usage_refusal`, expects status 2/no output for the exact DR-85 stamp. With the ruled fix, load_settings sets aside the file and returns defaults; the real CPU export succeeds with status 0. Isolated reproduction: exit 1, `1 failed in 0.69s`, `AssertionError: assert 0 == 2`; `work/wp4.3a/turn3-b4-repro.log`. Origin: `git log -S` identifies `f6023dd`, WP4.1 Reviewer B remediation. | **STOP: required test alignment is outside ownership.** Recommended grant: update only this test to assert the ruled set-aside/defaults behavior and successful CLI export. Do not restore the OverflowError or alter ungranted runner settings logic to preserve this stale expectation. Existing test is untouched. Dispatcher/CHARC ruling required; requested regression set is not green, so hold a green-commit claim. |
| T3-F2 / MINOR, sandbox environment | Three existing tests fail at `tests/test_headless_export.py:615`, `_unc_extended` calling `LOCAL_SHARE.is_dir()`, with PermissionError/WinError 5 for the localhost administrative share: `test_g1_inside_sees_every_spelling_of_the_same_folder`; `test_g1_main_refuses_every_footage_check_through_another_spelling[unc]`; `test_g1_the_redactor_hides_the_extended_spellings`. They do not reach the relevant UNC assertions. Origin of helper: `git log -S` identifies `831e900`, WP4.1 R2. Digest: `work/wp4.3a/turn3-failure-digests.log` (exit 0, four actual failures confirmed). | RUN REQUEST at the orchestrator's seat for these three tests. No helper/test edit and no further share access attempted here. This is not evidence of a new product regression. |

Cheap reproduction of T3-F1 (PowerShell sets PYTHONPATH to scripts first):

```text
uv run pytest tests/test_headless_export.py::test_b4_a_settings_file_whose_created_stamp_overflows_is_a_usage_refusal -q --basetemp=work/wp4.3a/tmp-b4 -p sandbox_mkdir_shim -p no:cacheprovider
```

Seat run request (no sandbox shim at the seat):

```text
uv run pytest -q -rs tests/test_headless_export.py::test_g1_inside_sees_every_spelling_of_the_same_folder "tests/test_headless_export.py::test_g1_main_refuses_every_footage_check_through_another_spelling[unc]" tests/test_headless_export.py::test_g1_the_redactor_hides_the_extended_spellings --basetemp=work/wp4.3a-seat-unc
uv run ruff format --check .
```

### Verification record and handoff

| Pass | Suspected / confirmed / rejected | Fix or remaining action |
|---|---|---|
| Task-4 RED/GREEN | All six required defects reproduced. A later equality failure was confirmed as an incorrect test expectation by tracing the real provenance writer. | Reader mappings/key sets fixed; test expectation corrected to the actual written metadata; six cases green. |
| Task-5 RED/GREEN | All 13 cases reproduced their intended leaks or escaping exception. Doubled raw Unicode exposed one incomplete pattern after the first fix. | Added the missing form; all 13 cases green. |
| Final focused pass | Twenty-five cases pass, including real CPU provenance exports, constant changes, both resolution exceptions and previous spawn policy. | No new in-envelope issue found in this pass. |
| Broader unchanged-test pass | Three failures confirmed as share-access restrictions in existing helper code; one confirmed as a stale test contract after the required settings behavior change. | Route T3-F2 to a seat run; STOP for T3-F1's narrow test-update grant. No out-of-scope remediation. |

This turn bundles tasks 4 and 5 in overlapping runner files; propose one combined
commit only after the STOP is dispositioned so that the requested regression
set can be green. No acceptance/full-pass claim, Reviewer A convergence, or
package-completion claim is made. The final report remains scheduled for Turn 4.

Turn 3 locks: changes remain in the five owned product modules, four owned test
files and ledger; tests/test_headless_export.py is unchanged. No frozen
interface, GUI, app, jobs, writer, dependency, local-config or register edit.
No actual footage access, hardware-marked test execution, mailbox post, commit
or sibling-worktree access. The attempted administrative-share access came from
the authorized existing test set and failed in the sandbox; further execution
of those cases is yielded to the seat. All new tests remain parallel-leg and
all new writes stay under tmp_path. No new product timing/memory measurement.


## Turn 4: CHARC ruling, recorded verbatim before remediation

Ruling `a2ef868a6e14b506`, authoritative source: `C:\Users\rwsmy\clearwater-review-evidence\wp4.3a\b4-ruling-b6aa800a.md`.

```text
---

PRIMARY: CHARC. Ruling on query f513222455172d4e (WP4.3a STOP, B4).

**(a) GRANTED. RULED.** Grounds, read at this seat on `wp4.3a` ef903e5: the runner's module docstring (`tools/headless_export.py:9-10`) already documents that `load_settings` "renames a corrupt settings.json beside itself" (D89) and the run proceeds on defaults; the `OverflowError` arm at `:1196-1200` was WP4.1's defensive refusal for the CRASH that DR-85 now classifies as a decode failure of the same class. One reader, one behaviour for every caller: the overflow case follows the documented corrupt-file case (set aside, defaults, exit 0). (b) is DECLINED for the reason you gave (a per-caller split with a duplicated decode).

Conditions:
1. **Scope of the test grant:** `tests/test_headless_export.py` `test_b4_...` (`:1093-1105`) ONLY, renamed to say what it now proves. Assertions: exit 0; the original bytes kept at `settings.json.bad-*` (exactly one such file, equal bytes); the export written; stderr carries no full path (`_no_full_path`); and the export used DEFAULT parameters (the record or the output shows the default set, not the planted one), so the set-aside is proved, not inferred.
2. **The WARNING route (owned file, RED-first):** the runner installs no logging handler (no `basicConfig` / `StreamHandler` in `tools/headless_export.py`), so `settings_store._log.warning(... %s ...)` (`settings_store.py:161/168`, full path) reaches stderr through logging's last-resort handler UNREDACTED. Fix in the runner: a stderr handler (or `logging` filter) whose formatter passes the record's rendered message through the run's `Redactor`, installed once in `_main` before `_settings`. Test: the B4 stderr line names the file by basename only. This gap is PRE-EXISTING for the plain-corrupt-file case (WP4.1), DR-81-class; closes with the same edit; I append it to DR-81's closure text at the accept. Note it in the report.
3. The `:1196` tuple may keep `OverflowError` as defensive; the comment changes to say the loader handles it (DR-85) and the arm is unreachable through `load_settings`. The cell's call; say which in the ledger.
4. Report: one line naming the WP4.1 behaviour change (B4's refusal -> the documented corrupt-file behaviour), the grounds above, and the accept record carries it.

Everything else in turn 3 stands as built; resume the Codex cell from the STOP (tasks 4-5 commit, then this edit, then task 6 and the report). Depth 205,870 / 258,400 noted: if the remaining work does not fit under the cap in this seat, re-seat at a committed head per the depth discipline rather than compacting mid-task.

Slip noted, no action. WP4.3 cell 5 Group A noted.

Owner-pending inputs: photos (WP3.6P), the iPhone clip (DR-15). Open owner decisions: none.


```


### Turn 4 execution and verification

The dispatcher committed Turn 3 as `fa2afab`, recording the stale B4 expectation
as intentionally red at that commit. The prior STOP is now resolved by CHARC's
verbatim ruling above. Scope extends only to the one B4 test function and the
owned runner WARNING route; no other existing headless test was changed.

Dispatcher-seat results supplied at this boundary (not additional sandbox runs):
format check **269 files already formatted**; the three UNC cases **3 passed**;
old B4 reproduces exit 0 versus its stale expected exit 2, with full paths in the
captured settings WARNING record.

Implementation:

- `_main` scopes `_redacted_stderr` around its execution, installing the handler
  once before `_settings`. The handler belongs to the clearwater application
  logger, emits WARNING or above only, and is removed/closed in finally.
- `_RedactingFormatter` copies the record, suppresses existing tag-value forms,
  formats it and passes the complete rendered text through the run's Redactor.
  It does not mutate the records seen by a host's handlers. The existing library
  run/last-resort policy remains in place.
- The settings file is also a known redaction path, so both settings.json and
  its .bad-* sibling appear by file basename, without even the settings-folder
  prefix. Existing redactor construction/refusal handling guards this path too.
- Renamed only the granted B4 function to
  `test_b4_overflowing_settings_are_preserved_and_export_uses_defaults`.
  It plants nondefault gamma, PNG depth and suffix, then proves exit 0, exactly
  one byte-identical backup, an actual corrected PNG, the entire default
  parameter mapping (including gamma 1.5 rather than planted 2.25), default
  16-bit output and path-free stderr.
- Kept the runner _settings OverflowError arm as defensive. Its comment now
  explicitly says DR-85 handles it in load_settings and this arm is unreachable
  through that loader, as condition 3 permits.
- Wrote `docs/reports/wp4.3a-hardening.md` as DRAFT, including the five rows,
  Round 0 facts, Q-A/Q-B/Q-C, the WP4.1 behavior change, the WARNING route and
  Limits. Reviewer/gate claims are explicitly pending.

| Check | RED or final result | Evidence under work/wp4.3a/ |
|---|---|---|
| WARNING route, year-one and plain corrupt JSON | RED: 2 failed, 9 deselected in 0.98s, exit 1. Existing pytest logging capture receives the warning record, while stderr has progress only, not the required redacted warning. | turn4-warning-red.log |
| Same two WARNING cases after fix | 2 passed, 9 deselected in 0.73s, exit 0. File names only; warning printed once; application handlers restored. | turn4-warning-green.log |
| Updated B4 plus both WARNING cases | 3 passed, 9 deselected in 0.85s, exit 0. | turn4-b4-warning-green.log |
| Bounded headless / new runner / WP4.2a regression | 136 passed, 4 deselected in 8.22s, exit 0; no failures or skips. Deselects: the three known sandbox-blocked UNC tests and one GUI-marked case. | turn4-regression.log |
| Ruff check | All checks passed!, exit 0. | turn4-ruff.log |
| Strict mypy | Success: no issues found in 141 source files, exit 0. | turn4-mypy.log |
| Write-mode formatting, three changed Python files | 2 files reformatted, 1 file left unchanged, exit 0. Global --check remains at the seat. | turn4-format.log |
| Ownership / LF / diff check | Exactly five changed owned/granted paths; byte-for-byte equality outside the B4 function in test_headless_export.py; ruling text still preserved; all LF; diff check passed, exit 0. | turn4-scope-check.log |

The bounded pytest command includes tests/test_headless_export.py,
tests/test_wp43_runner_redaction.py and tests/test_wp42a_runner_hardening.py,
with the standard exclusion expression for gpu/footage/slow/gui/fullclip and
three explicit --deselect node IDs for the administrative-share cases.
All executions use PYTHONPATH=scripts, sandbox_mkdir_shim, no cache provider,
and a temp root under work/wp4.3a. No further share access was attempted.

Verification loop:

| Suspected / checked | Confirmed or rejected | Fix / final status |
|---|---|---|
| WARNING needs an explicit CLI stderr route under captured logging. | Both corrupt-file forms lack the required warning in stderr before the change. | Scoped handler and copying redacting formatter; both cases green. The standalone last-resort filtering already existed; no claim is made that the RED test observed a raw path in stderr. |
| B4 could pass while silently using planted settings. | The old assertion is obsolete under DR-85; defaults need direct evidence. | Byte-identical set-aside and exported provenance prove the required defaults, bit depth and suffix. Updated B4 green under the narrow grant. |
| Handler might leak or duplicate output across runs. | Two distinct corrupt-file invocations each print the settings warning exactly once and restore the handler list. | No new issue found in the bounded GREEN pass. |
| Fix might cross the test grant. | Source comparison strips only the B4 function and proves the rest is byte-identical. | Grant honored; no other headless test edited. |

Current disposition: T3-F1 resolved by CHARC and the passing amended test;
T3-F2 passes at the dispatcher's seat on fa2afab, remains a sandbox limitation,
and is requested again at the seat for the amended candidate. No new STOP.
The final format/UNC seat checks, remainder of task 6 and reviewer/gate work
remain pending; the DRAFT report does not claim acceptance.

## Seat 2 Turn 1 (ledger Turn 5): Reviewer A R1 adjudication

### Boundary and supplied task-6 evidence

The fresh seat read the successor handoff, the verbatim CHARC B4 ruling and
Round 0, then the binding dispatched brief, the four-commit history/status and
R1 in full. History matches the dispatch: a614160, ef903e5, fa2afab and 553d1f2;
HEAD is 553d1f2 and the starting tracked tree is clean. Seat 1's final depth is
recorded above exactly as supplied. This turn changes only this ledger.

The dispatcher ran task 6 at its seat on **553d1f2**. The supplied evidence is
also present in `work/wp4.3a/seat-t6.log`; its summary lines were read here:

| Seat check | Recorded result |
|---|---|
| Ruff format --check | 269 files already formatted |
| Ruff check | All checks passed! |
| Strict mypy | Success: no issues found in 141 source files |
| Full brief task-6 list, including all three UNC cases, GPU and slow cases; QT_QPA_PLATFORM=offscreen; pytest -q -rs; -m "not footage and not fullclip" | 884 passed, 12 deselected in 777.96s (0:12:57); EXIT=0 |

The list comprises tests/test_io_video_*.py, tests/test_config_*.py,
tests/test_headless_export.py, tests/test_wp42a_runner_hardening.py,
tests/test_wp42b_naming_guard.py, tests/test_wp43_runner_redaction.py and the
brief's core/color/analysis/gui/app and video-rule layering set. The 12
exclusions are footage tests, as the dispatcher reports. These are development
checks on 553d1f2, not the final gate or evidence for an unbuilt remediation.
They were **not rerun** by Seat 2. The previous UNC rerun request is satisfied.

### R1 provenance and cumulative accounting

- Reviewed candidate: fe65e6a..553d1f2, excluding docs/proofs and uv.lock.
- Reviewer: orchestrator's read-only Claude process, claude-opus-5-5 / high,
  via scripts/codex_cell.py review. Dispatcher assertions: model correct,
  is_error false, 52 turns, tree clean afterward; 7 sandbox permission denials.
  CLI version was not supplied; no version is inferred.
- Full local review: `work/wp4.3a/rA1/review-r1.txt`, read in full.
- Durable evidence, dispatcher-owned:
  `C:\Users\rwsmy\clearwater-review-evidence\wp4.3a\r1\`.
  Dispatcher-supplied md5 prefixes: review e5244b65, prompt cb643310,
  diff de197b35, json a6b61860. No independent hash verification is claimed.
- Verdict: **NEW_CRITICAL_MAJOR_FOUND**. Count the enumerated F1-F9:
  0 critical, 1 major, 2 minor, 6 advisory; all 9 NEW, 0 REOPENED.
- Envelope accounting: F1/F2/F3/F6/F7/F8/F9 are in; F4 concerns product help
  but its edit is outside the grant; F5 is a POSIX residual outside the ruled
  exception-arm touch. Thus 7 in / 2 out for remediation ownership/reachability.
  The reviewer labels F4 in-envelope while explicitly acknowledging that its
  line is ungranted; this ledger distinguishes those two meanings.
- Executed remediation this turn: 0 product fixes, 0 test/control fixes,
  0 reverts; documentation-only adjudication. Planned: product fixes F1/F9,
  test/control fix F2, report fix F3 and report-only disclosures F4-F8.
  No convergence claim: F1 is new, in-envelope and major.

### Every finding adjudicated

| Finding / severity / evidence | Decision and cited ground | Next-turn action or explicit disposition |
|---|---|---|
| F1 / MAJOR / reviewer EXECUTED; independently reproduced here | **FIX.** Confirmed. tools/headless_export.py:724-744 returns an unresolved configured path. _resolved:768 is reached through inside:788 from _check_own_paths:1282, check_outputs:900/904 and run:970/972. The new guard at :1353-1358 protects only configuration lookup. Q23 / DR-81 (b) requires a raising footage resolution to become a redacted usage refusal, so the current closure claim is unsupported. | Next turn, map OSError, RuntimeError and ValueError from EVERY footage-dependent check in _main and run to path-free RunnerRefusalError; main returns 2 before exporting, including a later run refusal. Rewrite the test so configured_footage_folder returns the unresolved path and Path.resolve or _resolved raises at the real check. Cover own-path, output and cache checks, main and library routes, and NUL-path ValueError. Remove the old artificial-resolution case unless retained under a name that proves only defensive configuration-lookup handling; it cannot prove DR-81 (b). RED first. |
| F2 / MINOR / reviewer EXECUTED; independently reproduced here | **FIX.** Confirmed. tests/test_io_video_spawn.py:46-53 recognizes only run/Popen and :86 asserts count > 0. Brief goal 1 is EVERY FFmpeg/ffprobe child through the helper; task 3 supplies the AST control. Current product sites are all covered, but the control admits alternate launches. | Widen the guard to subprocess.call/check_call/check_output/getoutput/getstatusoutput as well as run/Popen; os.system/popen/spawn*/exec*; asyncio.create_subprocess_*; module and direct-import aliases; bound names, getattr and functools.partial references. Plant each form as a synthetic positive control and require exactly seven real sites. These alternate APIs must be caught or rejected as bypasses, not newly authorized for product use. RED first. |
| F3 / MINOR / reviewer REASONED; source/report checked | **FIX (report).** Confirmed. docs/reports/wp4.3a-hardening.md:6 still awaits the already-recorded 553d1f2 commit, its validation section still requests the now-satisfied UNC seat rerun, and its DR-81 (b) row overclaims F1. Plan 4.5 and the model-prompting standard require evidence-backed return claims. | Next turn replace stale commit/seat-run statements with the supplied task-6 results above; correct DR-81 (b) only against F1's actual results; record R1 status and add F8's consequence. Preserve pending Reviewer B/final-gate status. No report edit this turn. |
| F4 / ADVISORY / reviewer REASONED; exact help line checked | **REPORT-ONLY; proposed grant, no edit.** tools/headless_export.py:1203 says only source/settings additions are accepted, omitting the newly accepted writer profile. Files owned limits this provenance alignment to the key set and read_parameter_file docstring (:143 and :593-599 on the base); the B4 WARNING grant does not grant CLI help. Q20 changes importer acceptance, not ownership of this help line. | Dispatcher to ask CHARC for a one-line grant. Recommended replacement help: "an AD-13 preset JSON file (writer provenance, including profile, is read too)". The line remains untouched unless granted. This advisory does not block the authorized F1/F2/F3/F9 remediation. |
| F5 / ADVISORY, OUT OF ENVELOPE / reviewer EXECUTED + REASONED | **REPORT-ONLY (Limit).** The four unchanged raw OSError arms at verify.py:238, probe.py:140, encode.py:886 and capability.py:99 may expose OSError.filename on POSIX. Reviewer executed Windows CreateProcess failures with filename=None; POSIX reach is reasoned. Q-C expressly widens ONLY _check_cuda's two arms; the brief says implement exactly its ruled touch. Ownership of a module does not widen that touch. | Add a Limit naming all four arms, platform distinction and the unexecuted POSIX claim. Dispatcher/CHARC owns banking and follow-on assignment at those arms' next authorized error-text touch. No cross-platform leak fix in this package and no claim of an executed POSIX reproduction. |
| F6 / ADVISORY / reviewer EXECUTED | **REPORT-ONLY (Limit).** file:/// URI and dot-segment spellings survive redaction, but the reviewer finds no product text producing them. Q23 / task 5 requires mixed slash/backslash spellings of known folders; it does not commission arbitrary URI/canonicalization forms. Existing required separator spellings held in R1. | Disclose the two unsupported spellings; dispatcher/CHARC may bank with trigger: a product surface starts emitting either form. No redactor expansion or new review round driven by this advisory. No decline or claim that arbitrary caller text is safe. |
| F7 / ADVISORY / reviewer REASONED | **REPORT-ONLY (Limit).** A malformed logging call with missing mapping keys can make getMessage fail before the redacting formatter, causing logging.handleError to print the raw record. The ruled B4 grant requires rendered product WARNING messages through the Redactor; a malformed log call is not a product-produced message, and the same shape predates this handler in _RedactingFilter. | Disclose the malformed-record limit; dispatcher/CHARC may bank for the next logging hardening touch or a reachable malformed product call. Preserve valid-record redaction, copy semantics and handler teardown. No claim of a malformed-record safety guarantee. |
| F8 / ADVISORY / reviewer REASONED | **REPORT-ONLY (behavior line).** Q13 / AD-23 explicitly mandates CREATE_NO_WINDOW for all these Windows children, including the runner. Its console-signal consequence follows the mandated flag; changing signal policy is not granted. This is disclosure, not a reason to revert the flag. | Next report: Windows FFmpeg children no longer receive the runner console's Ctrl-C/Ctrl-Break; Ctrl-C uses the runner cancellation handler, while Ctrl-Break killing Python can leave a child until stdin EOF. Attribute the consequence as reasoned, not an executed signal/orphan test. |
| F9 / ADVISORY / reviewer REASONED; source checked | **FIX (one line).** Confirmed. decode.py:182 interpolates error.strerror directly and can render OSError: None. Q-C owns this exact arm and requires class/strerror without raw exception or filename. A path-free fallback preserves that ruling. | Next turn use error.strerror or "an operating-system error" in the existing expression; add a focused None-strerror case in the owned spawn test, RED first. No wider exception refactor. |

Disposition totals: **FIX 4** (F1/F2/F3/F9), **REPORT-ONLY 5** (F4-F8),
**DECLINE 0**. No finding is silently discarded. Report-only does not imply
that the reported spelling, malformed record or POSIX case is fixed.

### Independent confirmation and turn verification

Cheap probes ran against unchanged product/test code on 553d1f2 with
`uv run --offline python -`; complete output is retained at
`work/wp4.3a/seat2-turn1-adjudication-probes.log` (exit 0).

- Monkeypatched Path.resolve only for a synthetic path under work/wp4.3a;
  configured_footage_folder returned that path unresolved. For each of OSError,
  RuntimeError and ValueError, both main's real own-path route and run's real
  output-check route let the raw exception escape with the synthetic private
  path. Six escapes confirmed. main used --settings-dir to reach the check
  before any settings load; run failed before the supplied dummy export object
  could be used. No output or configuration write occurred.
- Loaded the current _spawn_calls helper and fed eleven synthetic AST sources:
  check_output, aliased call, directly imported aliased check_call, os.system,
  os.popen, os.spawnv, os.execv, asyncio.create_subprocess_exec, a bound Popen
  name, getattr(subprocess, "run"), and functools.partial(subprocess.run).
  All eleven bypassed the guard. This is a control failure, not an extra current
  product spawn.
- F3/F4/F9 were checked directly against the report, help string and exception
  arm. F5-F8 retain the reviewer's EXECUTED/REASONED provenance above; no
  independent POSIX, URI, malformed-record or console-signal run is claimed.
- No pytest/lint/type/format rerun this documentation-only turn. The dispatcher
  explicitly said not to rerun task 6. Ledger scope/byte/diff checks are recorded
  after the edit: `work/wp4.3a/seat2-turn1-ledger-check.log`, exit 0, confirms
  only this ledger changed, LF/ASCII, exactly one disposition for F1-F9,
  consistent counts, task-6/depth/handoff anchors, no untracked deliverables
  and a clean git diff --check. Product, tests and report remain unchanged.

### Question and next boundary

**F4 question for CHARC (recommended answer first):** grant only the
--parameters help string at current tools/headless_export.py:1203 to use the
replacement above; otherwise leave it and bank the stale help text. The literal
file grant excludes this line, so the dispatcher must route it before any edit.
This question does not stop the already-authorized R1 remediation.

YIELD now as dispatched: remediation is the NEXT turn after the dispatcher's
reply. No round-5 continuation gate is due at R1. Reviewer A has not converged;
Reviewer B and the ONE two-leg gate remain pending at the orchestrator's seat.
No new dependency, module, OS branch, interface, GUI/app/jobs/photo-writer,
fixture, local-config or register change; no footage read/write, mailbox post,
subagent, commit, git write or sibling-worktree access.


## Turn 6 (Seat 2 Turn 2): R1 remediation

### CHARC ruling recorded verbatim before remediation

Source: CHARC `d6e9abdfa16feb0e`, 2026-10-29T17:03:59Z;
`C:/Users/rwsmy/clearwater-review-evidence/wp4.3a/r1-ruling-d6e9abdf.md`.

```text
**2. WP4.3a R1.**
- **F1 MAJOR, FIX as the reviewer reads it:** DR-81 (b) closes only when the guard wraps the resolve that product code actually reaches (`write_target_refusal` via `_check_own_paths` / `check_outputs`), with the test planting the raise AT that site; NUL as `ValueError` included. The current test is moved, not kept beside.
- F2, F3 FIX; F5-F9 as proposed.
- **QUERY F4 = GRANT, RULED:** the ONE help-string line at `tools/headless_export.py:1203`, in step with Q20's `:143` and `:593-599`; text only; seat 2 confirms no test pins it (if one does, the test's expected text changes with it, same grant).

(ii) **Scope addition to WP4.3a, GRANTED:** in `config/settings_store.py`, an `output_folder` (and any other path-valued field) that cannot be a path (NUL, or `Path()` raising `ValueError`) is treated like an out-of-range field by the EXISTING per-field rule (`_clamp`, :129: replaced by its default with one warning), NOT a whole-file set-aside: the file is well-formed, one value is unusable, and the user's other settings survive. One decode check + one RED-first test in `tests/test_config_settings.py` (owned). Codex seat 2 folds it into the R1 remediation turn; it is the DR-85 sibling in spirit ("a settings file cannot stop the program from starting") and the brief's register table gains one line. Banking it is DECLINED: the startup skip alone leaves a silently ignored output folder with no warning at the source.
```

### Turn-6 RED/GREEN record (in execution order)

- F1: moved the old artificial-resolution test to the real write-check routes;
  no defensive-lookup duplicate retained. Final RED: **23 failed, 9 deselected
  in 2.06s**, exit 1, `work/wp4.3a/turn6-f1-red-final.log`. The main assertion
  `assert he.main(argv) == 2` instead receives raw OSError/RuntimeError/ValueError;
  library cases fail `pytest.raises(RunnerRefusalError)` with those raw errors.
  The trace reaches write_target_refusal -> inside -> _resolved -> Path.resolve.
  ValueError cases use an actual embedded-NUL path. Two transient-error cases
  arm at the real run call to prove late refusal handling. Initial matrix was
  24 RED cases; the redundant late-NUL case was removed because NUL necessarily
  fails the first check, so it cannot represent a later transient failure.
  GREEN: **23 passed, 9 deselected in 0.69s**, exit 0,
  `work/wp4.3a/turn6-f1-green.log`. A private _footage_checks context wraps
  configuration/own-path and output preflight checks, plus run's configuration,
  output and cache checks. Each maps the three exception classes to a path-free
  RunnerRefusalError before engine construction/export; CLI returns 2.

- F2: synthetic launch forms RED: **156 failed, 6 passed, 11 deselected
  in 0.89s**, `turn6-f2-red.log`, exit 1. Failing assertion:
  `assert _spawn_calls(ast.parse(source))`, with `guard missed <form>: <api>`.
  Six existing direct/module/direct-import run/Popen controls already passed;
  the other call families, bound names, getattr and partial were missed.
  Widened API recognition and import/bound-callable resolution conservatively;
  callable factories count as suspicious sites too. Pin now requires exactly
  seven product sites. GREEN including both product structural guards:
  **164 passed, 9 deselected in 0.87s**, `turn6-f2-green.log`, exit 0.

- F9: RED **1 failed, 173 deselected in 0.18s**, `turn6-f9-red.log`,
  exit 1: expected "OSError: an operating-system error", got "OSError: None".
  One-line fallback in _check_cuda's existing arm. GREEN **1 passed,
  173 deselected in 0.09s**, `turn6-f9-green.log`, exit 0.

- R3-1 (ii): confirmed frozen Settings.output_folder is the ONLY path-valued
  Settings field. Added one parameterized config test (NUL, constructor
  ValueError, path-use ValueError) and one real CPU CLI warning integration.
  RED **4 failed, 96 deselected in 0.96s**, `turn6-r31-red.log`, exit 1:
  the expected whole Settings equality fails (NUL/use retains the bad field;
  constructor failure loses the other settings by setting aside the file);
  CLI warning count is 0 instead of 1. A decode check now validates NUL,
  Path construction and absolute-path formation without requiring existence
  or resolving/reading the configured output directory. It substitutes null
  only to let frozen IF-10 validate the other fields, then passes the invalid
  original to _with_valid_values, which uses the actual default and existing
  _warn_out_of_range exactly once. The other ranges use the same function,
  now invoked after successful IF-10 decoding inside _decode. GREEN **4 passed,
  96 deselected in 0.88s**, `turn6-r31-green.log`, exit 0. File bytes, other
  settings, one warning, no backup and actual export suffix are proved.
  The runner's existing formatter suppresses repr-valued warning arguments,
  so even this output path, unknown to its Redactor, is hidden. No handler
  change or frozen Settings edit was needed.
- F4: repository test search found no pin of the old help wording; the existing
  test_help_exits_0 checks status only. An in-memory --help check RED raised
  `AssertionError: help omits the accepted writer provenance/profile form`
  (`turn6-f4-red.log`); the single granted line now reads the recommended text.
  The same check GREEN exits 0 and describes writer provenance/profile
  (`turn6-f4-green.log`). No existing-test expectation was changed.

### Executed fixes and cumulative accounting after Turn 6

CHARC's grant changes F4 from the initial REPORT-ONLY disposition to FIX.
R1 severity remains 0 critical / 1 major / 2 minor / 6 advisory, all 9 NEW,
0 REOPENED. Current edit/reachability envelope is 8 in / 1 out (F5). No revert.
R3-1 (ii) is an external granted scope addition from WP4.3 R3, nominal MAJOR;
it is not counted as another Reviewer A R1 finding or a reopened finding.

| Finding | Executed disposition | Product versus tests/control versus report |
|---|---|---|
| F1 / MAJOR | FIXED locally; real-route tests moved, guard now surrounds the actual checks. | Product plus 23 regression cases; RED/GREEN above. R2 confirmation pending. |
| F2 / MINOR | FIXED locally; alternate launch detection and exactly-seven pin. | Tests/control only; 162 planted cases plus two product guards GREEN. |
| F3 / MINOR | FIXED in the refreshed report. | Report only; supplied task-6 figures, committed anchors, actual F1 results and current review/gate status. |
| F4 / ADVISORY | FIXED under the explicit one-line grant. | Product help text only; no existing test pin/expected-text edit. In-memory help check RED/GREEN. |
| F5 / ADVISORY, outside ruled touch | REPORT-ONLY Limit recorded. | No product/test fix. Dispatcher/CHARC owns banking/follow-on at the four unchanged arms' next authorized error-text touch. |
| F6 / ADVISORY | REPORT-ONLY Limit recorded. | No product/test fix. Dispatcher/CHARC owns banking, triggered if product text emits a URI/dot-segment spelling. |
| F7 / ADVISORY | REPORT-ONLY Limit recorded. | No product/test fix. Dispatcher/CHARC owns banking at the next logging hardening touch or a reachable malformed product log call. |
| F8 / ADVISORY | REPORT-ONLY behavior line recorded. | No product/test fix; reasoned console-signal consequence, no signal/orphan experiment. Dispatcher/CHARC owns any later signal-policy commission. |
| F9 / ADVISORY | FIXED locally, one logical expression. | Product plus one None-strerror test; Ruff wraps the expression without a refactor. |
| R3-1 (ii) / external scope addition | FIXED locally under CHARC d6e9abdf. | Product plus three config cases and one actual CLI warning/export case. Per-field default, one warning, no backup and other values preserved. |

R1 disposition totals now **FIX 5** (F1/F2/F3/F4/F9), **REPORT-ONLY 4**
(F5-F8), DECLINE 0. Product-bearing R1 fixes: 3; tests-only fixes: 1;
report fix: 1. R3-1 adds 1 product-bearing scope fix separately.
These are executed changes, not a claim that Reviewer A has converged.

### Final light checks and verification loop

| Check / surface | Actual result | Evidence under work/wp4.3a/ |
|---|---|---|
| All tests/test_config_*.py, tests/test_headless_export.py, tests/test_wp43_runner_redaction.py, tests/test_wp42a_runner_hardening.py, tests/test_wp42b_naming_guard.py, tests/test_io_video_spawn.py | 561 passed, 4 deselected in 13.65s, exit 0; no skips/failures. | turn6-light.log |
| Final spawn file after E501 fixture-string line split | 174 passed in 1.52s, exit 0, no deselections/skips/failures. | turn6-spawn-final.log |
| Ruff check . | Initial E501: one added AST fixture string exceeded 100 columns; fixed by literal concatenation. Final All checks passed!, exit 0. | turn6-ruff.log; turn6-ruff-final.log |
| Strict mypy | Success: no issues found in 141 source files, exit 0. | turn6-mypy.log |
| Write-mode Ruff format on six touched Python files | 6 files reformatted, exit 0. Global --check is the dispatcher's seat check. | turn6-format.log |
| Final write-mode format after the lint/docstring edits | 6 files left unchanged, exit 0. No code changed after the passing checks. | turn6-format-final.log |
| Scope, ruling preservation and claims audit | Exactly eight owned paths; LF, ASCII docs; existing config tests byte-identical; new CHARC excerpts and prior B4 ruling verbatim; report summaries match logs; one current handoff; no untracked deliverables; git diff --check clean, exit 0. | turn6-scope-claims-check.log |

The light run uses PYTHONPATH=scripts, sandbox_mkdir_shim and no cache provider,
with --basetemp under work/wp4.3a. Marker expression excludes gpu, footage,
slow, gui and fullclip. Four deselections: one GUI case plus the three known
sandbox-blocked UNC nodes explicitly deselected below. No new test has a marker;
all use per-test tmp_path/synthetic inputs or in-memory AST sources. The baseline
884-pass task-6 run is not rerun or relabeled as this candidate's gate.

| Verification pass | Suspected / confirmed / rejected | Fix or resulting action |
|---|---|---|
| F1 actual route | Previous guard misses real own/output/cache resolves; independently confirmed at Turn 5 and 23 final RED cases at Turn 6. NUL is an actual ValueError, not a configured() fake. | _footage_checks covers all caller routes; 23 GREEN cases prove safe status/message and no export/config/cache writes. Old artificial test moved, not duplicated. |
| F2 controls | Guard misses non-run/Popen APIs and indirect calls; 156 planted assertions failed while six old forms passed. | All 162 forms now detected; seven real sites and single flag-construction guard pass. No product spawning API changed. |
| F9 | Missing strerror renders literal None, confirmed RED. | Fixed-text fallback, exact returned-message GREEN. |
| R3-1 | Bad path is accepted or a constructor error sets aside the entire file; four RED cases confirm source behavior and missing warning. | Decode validation + existing per-field rule, four GREEN cases preserve bytes/other settings and hide even an unknown private path in CLI stderr. |
| F4 | Help omits the newly accepted writer form; source and in-memory check confirm. No test pins it. | Only granted help line changed; check GREEN. |
| Final light run / static checks | No regression in 561 selected cases; no new product defect found. One long added-test line confirmed by Ruff. | Literal split; all 174 spawn cases rechecked; Ruff and strict mypy pass. No broader rerun justified by this formatting-only edit. |
| F3 claims audit | Prior report had stale commit/UNC statements and an unsupported F1 closure; R1/Turn-6 status must remain distinct from acceptance. | Report rewritten against actual logs, including external row and F5-F8; R2, B and final gate explicitly pending. |

### RUN REQUEST and boundary

At the dispatcher seat on the amendment, run global `uv run ruff format --check .`
and these existing UNC nodes (the sandbox limitation is already documented;
no additional administrative-share attempt is made here):

```text
tests/test_headless_export.py::test_g1_inside_sees_every_spelling_of_the_same_folder
tests/test_headless_export.py::test_g1_main_refuses_every_footage_check_through_another_spelling[unc]
tests/test_headless_export.py::test_g1_the_redactor_hides_the_extended_spellings
```

NEXT is the orchestrator's Reviewer A R2 on the amended candidate. Reviewer B
and the ONE two-leg gate remain pending after A convergence; no harness gate.
No open STOP/question: F4 is granted and the new path-field scope is implemented.

All changes remain in six owned Python files and the owned report/ledger.
No existing headless-test change this turn; the earlier B4 function grant stands.
No frozen interface, GUI/app/jobs/photo writer, dependency/lock, fixture,
local-config, register or harness file changed; no footage read/write, hardware
or fullclip run, timing/memory measurement, mailbox, commit, git write, stash,
subagent or sibling-worktree access. Exact scope/bytes/ruling preservation and
claims checks passed as recorded above; the final documentation-only diff check
is retained at work/wp4.3a/turn6-final-diff-check.log.

## Turn 7 (Seat 2 Turn 3): Reviewer A R2 adjudication only

### Entry, depth and dispatcher-seat QA

Turn 6 is committed as c9a7771 (six product/test paths) and 40eef4e
(report/ledger). HEAD/history match the dispatch; the starting tracked tree is
clean. All committed blobs are LF as supplied by the dispatcher. Turn-6 depth
is **154,379 of 258,400**, footer **tokens used 161,780**. This is the supplied
figure, not an estimate. Turn-7 depth awaits the next dispatcher reading.

The dispatcher supplied these QA results on the Turn-6 amendment:

| Requested check | Dispatcher-seat result |
|---|---|
| The three named UNC nodes | 3 passed in 0.98s |
| uv run ruff format --check . | 269 files already formatted |

The three nodes are test_g1_inside_sees_every_spelling_of_the_same_folder,
test_g1_main_refuses_every_footage_check_through_another_spelling[unc], and
test_g1_the_redactor_hides_the_extended_spellings in tests/test_headless_export.py.
The Turn-6 RUN REQUEST is satisfied. The dispatcher also confirmed _decode has
one caller, frozen interfaces/settings.py is untouched, and the per-field
route follows CHARC's ruling. None of these checks is rerun in this turn.

### R2 provenance and review verification

- Review: base fe65e6a, candidate **40eef4e**, orchestrator's read-only Claude
  process via scripts/codex_cell.py review, claude-opus-5-5 / high.
- Supplied assertions: model correct; is_error false; 37 turns; one permission
  denial; tracked tree clean afterward. CLI version not supplied/inferred.
- Full 55-line review was read from the durable evidence file
  `C:/Users/rwsmy/clearwater-review-evidence/wp4.3a/r2/review.txt`. The suggested
  local work/wp4.3a/rA2/review.txt copy is absent; the authoritative file was
  readable, so this is not a STOP or missing-review condition.
- Dispatcher-supplied md5s (not independently rehashed here):
  review.txt `99cd27d9394d8a4335eaa8885eb43450`;
  review-prompt-r2.md `e7a77bf09bb167c1391af70b9dd46ed9`;
  review-diff.txt `fd4914673bf259f970b2147a0122a17e`;
  review.json `946580f219affe62f31938198c495ba6`.
- Verdict: **NO_NEW_CRITICAL_MAJOR**. R2 has 0 critical, 0 major, 1 minor
  (REOPENED R1 F2, partial), 4 advisory (NEW observations, including the newly
  reported pre-existing-class leak). Thus 4 NEW / 1 REOPENED; no reverts.
- R2 independently EXECUTED the real NUL footage case in a fresh process on
  every main/run route and closed F1. It verified F3/F4/F9 and R3-1 (ii), all
  162 existing guard controls, seven current sites and the per-field warnings.
  It reports 108 config-reader mutations with no escaped exception, 395 passing
  touched-test cases, Ruff green and 269 files formatted. Those are reviewer
  results, not additional cell executions. Log-cited report figures were
  withheld from the reviewer and are REASONED there; Turn-6 local claim checks
  and the supplied seat results remain the evidence for those figures.

### Independent checks and every finding adjudicated

All five checks below ran against unchanged 40eef4e product/test/report code
with `uv run --offline python -`, using in-memory ASTs, records and fault
injection. Output: `work/wp4.3a/turn7-adjudication-probes.log`, exit 0.
No test file, configuration, export or product file was written by the probes.

| R2 finding / classification | Independent check and envelope | Disposition / cited ground / bounded cleanup plan |
|---|---|---|
| R2-1 / MINOR / **REOPENED R1 F2 (partial)** | Confirmed all 16 listed spelling classes return no spawn from the current _spawn_calls: asyncio.subprocess attribute/from-import; attribute binding; star import; submitted callable; default binding; walrus; dict lookup; Popen subclass; os.posix_spawn; os.startfile; __import__; importlib; _winapi; multiprocessing; pty. Injected kw["creationflags"] = 1 outside the helper into an in-memory source and called the actual flag guard: it passes. This is in-envelope test/control weakness; no present product bypass. | **FIX, bounded control cleanup plus report precision.** Accept the dispatch's cheap additions: asyncio.subprocess forms, star imports for the recognized subprocess family, attribute binding, os.posix_spawn/startfile and subscript creationflags stores, each with a failing planted control. Keep the seven-real-site pin. Narrow the report to the exact APIs and syntactic forms proved; explicitly disclose remaining dynamic/higher-order/subclass and other launcher families. The brief's Q13/task-3 AST control warrants the cheap fixes. Arbitrary Python call-flow coverage is not claimed or commissioned; residual forms are report-only limits. No further review round driven by this reopened minor. |
| R2-2 / ADVISORY / **NEW** | Confirmed on the real own-path route: Path.resolve injected to raise OSError for the existing docs target, inside _check_own_paths under _footage_checks, produces the fixed configured-footage message and hides the injected detail. The target, not footage, failed. In-envelope diagnostic text; no natural trigger found by the reviewer or claimed by this probe. Exit/refusal safety holds. | **FIX, one message plus focused control.** Use neutral wording such as "a folder cannot be resolved for the footage write checks." It covers both configured footage and user targets, retains a fixed path-free refusal and changes neither status 2 nor the protected routes. Q23 commissions readable resolution refusal, not an exact message that must blame footage. This owns the wrapper already changed by F1; no new scope/grant is needed. |
| R2-3 / ADVISORY / **NEW observation of a pre-existing class** | Confirmed: frozen Settings.from_json rejects a list-valued output_folder with a FormatError embedding its repr. Passed the real reason through _RedactingFormatter in a real settings WARNING-shaped LogRecord: an unknown synthetic private value survives via the %s reason, while the new per-field %r route is separate. Product reach is real, but redaction repair is outside the granted touch; report precision is in envelope. git log -S independently finds _field_error's repr at bf76136 (WP2.2 frozen IF-10) and the settings-store "is not valid settings:" route at 75d7dc5 (WP3.15). | **FIX report sentence; REPORT-ONLY pre-existing leak.** Say explicitly that the unknown-path suppression claim applies ONLY to the per-field out-of-range warning. Record the wrong-type/whole-file set-aside %s-reason limitation. CHARC d6e9abdf grants unusable string path values via the per-field rule; a wrong-typed value is still frozen IF-10's whole-file refusal. The B4 grant covers known settings/backup paths, not arbitrary private values nested in an IF-10 error. Dispatcher/CHARC owns banking and any future error-text/redaction hardening commission. Do not change frozen IF-10 or absorb a broader sanitizer here. |
| R2-4 / ADVISORY / **NEW, OUT OF ENVELOPE (POSIX trigger)** | Confirmed mechanism in memory: injected FileNotFoundError from os.getcwd while _decode processes a relative output_folder escapes the current decode path. Actual deleted-POSIX-cwd reach is REASONED, not executed; no directory was deleted or cwd changed. Reviewer says Windows cannot delete the running process's cwd. This outside-envelope trigger is non-blocking. | **FIX, accept the dispatch's bounded option.** Next cleanup add OSError to the existing path-validation except arm, preserving _with_valid_values/_warn_out_of_range, original file and other fields; one injected-getcwd RED-first case proves it. Update load_settings's range-description text accordingly. The user explicitly proposes this one-line extension to the new R3-1 decode check; it uses the existing portable error path and adds no OS branch/dependency or frozen edit. No need to replace the validation design. Do not claim a real POSIX reproduction or full startup proof beyond this reader. |
| R2-5 / ADVISORY / **NEW** | Confirmed by source and execution: _redacted_stderr on the clearwater logger prints a synthetic clearwater.synthetic.batch WARNING once, so its scope includes non-settings batch warnings. The module's exit-2 list omits the new resolution refusal; its existing logging paragraph already describes handler coverage correctly. In-envelope report/module documentation accuracy. | **FIX text only in cleanup.** Describe all clearwater.* WARNING records across _main in the report (including settings and batch); add the generic folder-resolution refusal to the module exit-2 list, matching R2-2's final message. The dispatch's findings-3/5 cleanup expressly names report/docstring text; no behavior expansion or existing-test change is needed for these prose corrections. |

Planning-note decisions: accept the cheap R2-1 control fixes AND narrow the
report, rather than promising exhaustive arbitrary-Python discovery; accept
R2-4's one-line OSError option rather than replace the check; accept R2-3/5's
text corrections and the pre-existing leak's report-only disposition. R2-2 is
a small in-envelope diagnostic fix, supported by the independent injected-route
check. No finding is declined or silently dropped. All fixes are **PLANNED**;
none is executed in this ledger-only turn.

### Cumulative accounting and convergence

- R1 observations: 0 critical / 1 major / 2 minor / 6 advisory, 9 NEW.
  Its F1 major is closed by R2's executed checks; F3/F4/F9 are closed, F2 is
  partially reopened as a minor. R3-1 remains a separate external scope fix.
- R2 observations: 0 critical / 0 major / 1 minor / 4 advisory;
  4 NEW / 1 REOPENED, 4 in / 1 POSIX out for reachability. R2-3 is split:
  report correction in, pre-existing leak repair out of the edit grant.
- Across two review rounds: 14 observations, 13 NEW and 1 REOPENED; nominal
  observation counts 0 critical / 1 major / 3 minor / 10 advisory. These count
  historical observations, not current open blocking defects. No reverts.
- Executed R2 cleanup this turn: **0 product, 0 tests-only, 0 report fixes**;
  ledger adjudication only. Planned cleanup includes test/control changes for
  R2-1, one message for R2-2, one exception tuple for R2-4, and report/docstring
  corrections for R2-1/3/5. The R2-3 leak component is REPORT-ONLY.
- **Reviewer A has CONVERGED on the blocking axis.** Fill Part 1
  CONVERGENCE_CRITERION / ROUND_TERMINATION ends the loop on zero NEW blocking
  findings. R2's verdict is NO_NEW_CRITICAL_MAJOR; independent checks found no
  contrary in-envelope critical/major. A reopened minor and an out-of-envelope
  POSIX advisory do not reopen the blocking loop.
- Under that same fill, non-blocking cleanup happens once in the terminating
  round and does not open another round. R2-1 test/control polish is not a basis
  for R3. No round-5 continuation gate is due at R2. Reviewer B and the ONE final
  two-leg gate remain the orchestrator's work after cleanup verification.

### Turn discipline and next action

This dispatch is REVIEW ONLY. No product, test or report file changed. No
pytest, Ruff, mypy, format run, hardware/footage/fullclip test or gate is rerun.
The fresh seat-6 QA above satisfies the old RUN REQUEST. No additional heavy
RUN REQUEST or CHARC question is needed now; the next turn starts only after
the dispatcher reply, as instructed.

Only the owned ledger and gitignored probe/runner logs are written. No new
module, OS branch, dependency, frozen/interface/GUI/app/jobs/photo-writer,
fixture/local-config/register edit, footage access, configuration/export write,
mailbox, commit, git write, stash, sibling-worktree access or subagent.
Scope/byte/ruling-preservation/diff checks passed, exit 0, in
work/wp4.3a/turn7-ledger-check.log: only the ledger changed, LF/ASCII, five
dispositions and one R2 row, supplied QA/depth, CHARC blocks intact, no
untracked deliverables and git diff --check clean. The final documentation-only
diff check is retained in work/wp4.3a/turn7-final-diff-check.log. No
cleanup-completion or final-gate claim is made.

## Turn 8 (Seat 2 Turn 4): terminating R2 cleanup

Entry HEAD 5ec9142, clean tracked tree; Turn-7 ledger committed LF. Supplied
Turn-7 depth: **176,357 of 258,400**, tokens used **184,744**. This is the last
bounded turn in the seat; stop at a step boundary if the dispatcher-supplied
depth approaches 240K. No self-estimate substituted. The dispatcher accepted
all R2 adjudications; this turn implements that bounded cleanup only.

### RED/GREEN and executed cleanup

- R2-1 RED: **89 failed, 162 passed, 12 deselected in 0.94s**, exit 1,
  work/wp4.3a/turn8-guard-red.log. New API/attribute/star cases fail
  `assert _spawn_calls(...)`; three subscript store controls fail with
  DID NOT RAISE AssertionError from the actual flag guard. Added the finite
  cheap forms and store detection, retaining the exact seven-site pin.
  GREEN full spawn file: **263 passed in 1.92s**, exit 0,
  work/wp4.3a/turn8-guard-green.log. No product spawn/flag policy changed.

- R2-4 RED: **1 failed, 67 deselected in 0.21s**, exit 1,
  turn8-path-red.log: FileNotFoundError escapes load_settings/_decode when
  os.getcwd is injected to fail for a relative output_folder. OSError joins
  the existing validation arm; no new OS-specific branch or path design.
  GREEN: **1 passed, 67 deselected in 0.09s**, exit 0,
  turn8-path-green.log. Other fields/file preserved, one per-field warning,
  no set-aside. No POSIX cwd deletion/manipulation/reproduction is claimed.
- R2-2: fixed-message smoke RED asserts the old wording incorrectly blames
  only the configured footage folder (turn8-label-red.log). GREEN after the
  text-only change: "a folder cannot be resolved for the footage write checks."
  (turn8-label-green.log). No status/exception/control-flow change. Existing
  real-route cases pass in the final light set.
- R2-3/5: narrowed the R3-1 report guarantee to the per-field warning, disclosed
  the pre-existing wrong-type %s reason leak and origins (bf76136/75d7dc5),
  stated all clearwater.* WARNING coverage across _main, and added the generic
  folder-resolution refusal to the module exit-2 list. The report enumerates
  the 31 API / seven-form control boundary and residual dynamic forms. No
  sanitizer, frozen IF-10 text or malformed-file policy changed. Dispatcher
  owns banking R2-3 with CHARC as explicitly stated at this dispatch.

### Final checks, accounting and terminal status

| Check | Actual result | Evidence under work/wp4.3a/ |
|---|---|---|
| All tests/test_config_*.py, tests/test_headless_export.py, tests/test_wp43_runner_redaction.py, tests/test_io_video_spawn.py | 593 passed, 4 deselected in 13.66s; no skips/failures; exit 0. | turn8-light.log |
| Ruff check . | All checks passed!, exit 0. | turn8-ruff.log |
| Strict mypy | Success: no issues found in 141 source files, exit 0. | turn8-mypy.log |
| Write-mode format on four touched Python files | 3 files reformatted, 1 left unchanged, exit 0. Global --check is at the dispatcher seat. | turn8-format.log |

Pytest uses PYTHONPATH=scripts, sandbox_mkdir_shim, no cache provider and a
work/wp4.3a temp root. Marker expression excludes gpu/footage/slow/gui/fullclip;
one GUI case and the three known sandbox-blocked UNC nodes are deselected.
The prior three-UNC/format seat results remain valid for the prior candidate;
they are not relabeled as this cleanup's verification. Every added test stays
in the parallel leg, with per-test tmp_path or an in-memory AST as appropriate.

| R2 item | Final execution / verification record | Fix class |
|---|---|---|
| R2-1, reopened MINOR | 89 added controls failed RED; 263-case spawn file and 593-case final light set GREEN. Exactly seven current product sites still required. Report lists finite forms and unsupported residuals. | Tests/control only plus report. |
| R2-2, NEW ADVISORY | Fixed-text smoke RED/GREEN; final real-route tests GREEN. Neutral message applies to both targets/footage without leaking paths. | Product message only. |
| R2-3, NEW ADVISORY/pre-existing class | Report now distinguishes per-field %r suppression from whole-file %s reason. Leak itself not modified; dispatcher will bank it with CHARC. | Report FIX; leak REPORT-ONLY. |
| R2-4, NEW ADVISORY/POSIX reach out of envelope | Portable injected-getcwd RED/GREEN, file/other-field preservation and one warning proved. Actual POSIX deleted cwd not executed. | Product exception tuple plus one test/docstring. |
| R2-5, NEW ADVISORY | Report handler scope and module exit-2 list corrected against the handler/wrapper; no new logging behavior. | Report/docstring only. |

Cumulative reviewer observations unchanged: R1 = 0 critical/1 major/2 minor/
6 advisory, 9 NEW; R2 = 0 critical/0 major/1 reopened minor/4 NEW advisory.
Total 14 observations = 13 NEW + 1 REOPENED; nominal historical severity
0 critical/1 major/3 minor/10 advisory, not an active-blocker count. No reverts.
R1 executed fixes remain F1/F4/F9 product, F2 tests/control, F3 report, external
R3-1 product/tests separate. Turn 8 executes the R2 classes in the table above;
no review round or additional finding is invented for cleanup.

**Reviewer A terminal status: CONVERGED at R2; terminating cleanup DONE.**
The fill ends the blocking loop on NO_NEW_CRITICAL_MAJOR. The minor/control
and advisory fixes were done once in that terminal round; they do not create
R3 or postpone convergence. Verification found no new issue in this cleanup:
all planted controls, path-default case, final light set, lint and types pass.
No full-suite/gate/acceptance claim is made. NEXT is **Reviewer B at the
orchestrator seat, then the ONE two-leg gate, then accept**.

### RUN REQUEST, scope and final handoff

Dispatcher-seat `uv run ruff format --check .` and these existing UNC nodes
on this cleanup (not retried inside the known restricted sandbox):

```text
tests/test_headless_export.py::test_g1_inside_sees_every_spelling_of_the_same_folder
tests/test_headless_export.py::test_g1_main_refuses_every_footage_check_through_another_spelling[unc]
tests/test_headless_export.py::test_g1_the_redactor_hides_the_extended_spellings
```

No STOP/open question. The dispatcher explicitly accepted the R2 adjudication
and ordered this last bounded turn. Changes stay in six owned paths: settings
store, runner, new spawn tests, added config tests, report and ledger. No
existing headless/runner regression test changed, no decoder edit this turn.
No new dependency/module/OS branch, frozen/interface/GUI/app/jobs/photo-writer,
fixture/local-config/register/harness edit, footage access, hardware/fullclip
run, product timing/memory measurement, mailbox, subagent, git write/commit,
stash or sibling-worktree access. Scope/byte/ruling/claims checks passed,
exit 0 (work/wp4.3a/turn8-scope-claims-check.log): exactly six owned paths,
LF/ASCII docs, existing config tests unchanged apart from the new test's import,
31 tested APIs, seven product sites, one flag construction, verbatim rulings
intact, report summaries matching logs, one terminal handoff, no untracked
deliverables and clean git diff --check. Final documentation-only diff check:
work/wp4.3a/turn8-final-diff-check.log. The dispatcher assigns the commit SHA.

## RESUME HERE - successor seat

- Last committed head at Turn-8 entry: **5ec9142**, branch wp4.3a, base fe65e6a.
  Turn-8 cleanup is ready for dispatcher commit; only six owned paths changed.
- Last supplied depth: Turn 7 input **176,357 of 258,400**, tokens used
  **184,744**. This was the last bounded turn in Seat 2; Turn-8 footer/depth
  awaits the dispatcher. No estimate substituted; use a fresh seat if any
  further implementation is commissioned near the instructed 240K boundary.
- **Reviewer A CONVERGED at R2 (NO_NEW_CRITICAL_MAJOR); cleanup DONE.**
  R1's major closed by R2; R2's one reopened minor/four advisories adjudicated.
  Cheap controls, OSError path default and text/report fixes executed in Turn 8.
  R2-3's pre-existing IF-10 repr leak is REPORT-ONLY; dispatcher banks with CHARC.
- Current verified results: **593 passed, 4 deselected in 13.66s**, Ruff green,
  strict mypy clean in 141 source files. Spawn file **263 passed in 1.92s**.
  Full RED/GREEN/assertion record and actual log paths are in Turn 8 above.
- Guard claim is finite: 31 APIs x seven direct/alias/name/attribute/getattr/
  partial forms = 217, plus 31 recognized-family star imports = 248 process
  controls; three subscript-store controls, 12 remaining spawn cases = 263.
  Exactly seven real sites and one flag construction remain pinned. Higher-order,
  default/walrus/dict/subclass/dynamic-import/other-launcher forms are disclosed
  residual limits, not claimed handled or used by current product code.
- RUN REQUEST: global format --check and three named UNC nodes above, at the
  dispatcher seat on this cleanup. No additional sandbox share attempt.
- NEXT: **Reviewer B (orchestrator), then the ONE two-leg gate, then accept**.
  No A R3 for non-blocking polish; no full-suite run before B; no harness gate.
- CHARC's original brief/B4/d6e9abdf verbatim rulings remain above; registration
  and AD notes/closures remain CHARC's at accept. All locks stay binding.
