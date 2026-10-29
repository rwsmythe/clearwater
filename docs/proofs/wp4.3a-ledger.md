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
| Seat 2 Turn 1 (ledger Turn 5) | seat 2 turn 1, pending me | 258,400 tokens | Dispatcher supplies the next footer reading; no estimate substituted. |

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
| R1 | 0 | 1 | 2 minor / 6 advisory | 7 in / 2 out (F4 edit scope; F5 reachability) | 9 NEW / 0 REOPENED | 0 | 0 / 0 executed; ledger-only adjudication; product F1/F9 and test control F2 planned | Orchestrator process via codex_cell.py review; claude-opus-5-5 / high; CLI version not supplied | seat 2 turn 1, pending me | NEW_CRITICAL_MAJOR_FOUND; r1 evidence below; remediation pending |

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

## RESUME HERE - successor seat

- Current committed product/test/report head: **553d1f2**, branch wp4.3a, base
  fe65e6a. Only this R1 adjudication ledger is uncommitted by this seat; the
  dispatcher commits it. Prior commits and verbatim B4 ruling remain above.
- Task 6 is COMPLETE as development evidence on 553d1f2: dispatcher seat
  **884 passed, 12 footage deselected in 777.96s**, all three UNC cases included;
  ruff format/check and strict mypy green. See the supplied evidence table.
  Do not rerun that matrix merely to replace prior-seat evidence.
- R1: 1 major, 2 minor, 6 advisory, all NEW. Full dispositions and independent
  F1/F2 confirmations are above. Four fixes planned, none performed this turn.
  Blocking item F1 means no Reviewer A convergence claim.
- NEXT TURN after dispatch: RED-first F1 real-route tests and exception mapping,
  F2 AST positive controls/seven-site pin, one-line F9 fallback plus focused
  test; then refresh the report for F3 and disclosures F4-F8 against actual
  results. Keep F4's help line untouched without CHARC's grant. Scope otherwise
  remains the FINAL brief plus verbatim B4/runner grant above.
- Remediation checks use the sandbox shim/no cache provider and work/wp4.3a
  temp roots, exclude gpu/footage/slow/gui/fullclip; no administrative-share
  cases in the sandbox. Global format check, heavy commands, Reviewer A/B and
  the ONE final two-leg gate remain at the dispatcher seat as instructed.
- Seat 1 retired at input depth 237,170 / 258,400, footer tokens used 439,112.
  Seat 2 Turn 1 depth: **seat 2 turn 1, pending me**; dispatcher supplies it.
  Re-seat discipline: evaluate near 200K, stop at a step boundary near 250K.
