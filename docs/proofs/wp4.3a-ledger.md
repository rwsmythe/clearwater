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
  passes. No reviewer has run for this package yet.
- Dispatch overrides older generic instructions: yield after each named task
  group; adjudication turns change only the ledger before yielding; format check
  and the final two-leg gate run at the orchestrator's seat. Both gate expressions
  exclude `fullclip` under the dispatch's AD-30 amendment.

| Turn / boundary | Dispatcher-provided depth | Window of record | Action |
|---|---|---|---|
| Turn 1 footer, supplied at Turn 2 dispatch | `tokens used` 96,223; input depth 102,475 | 258,400 tokens | Dispatcher-read figure for session `01a18856-955d-74e3-b211-dfb519efdf0c`; evaluate near 200K, stop at a step boundary near 250K. |
| Turn 2 footer, supplied at Turn 3 dispatch | `tokens used` 238,706; input depth 146,818 | 258,400 tokens | Dispatcher-read figure; no estimate substituted. |
| Turn 3 footer, supplied at Turn 4 dispatch | `tokens used` 346,443; input depth 205,870 | 258,400 tokens | Past the evaluation point. Turn 4 is explicitly bounded; leave a successor handoff and await the next dispatcher depth. |
| Turn 4 | Awaiting dispatcher footer reading | 258,400 tokens | No estimate substituted. Next seat may be fresh; stop at this task boundary. |

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
| Not started | - | - | - | - | - | - | - | Orchestrator Claude pass; version not yet supplied | Not supplied | Pending |

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

## RESUME HERE - successor seat

### Commits and current work

- Dispatch base: `fe65e6a867106dd984d1c27ef3104e2ee3de0df4`.
- `a614160`: Round 0 ledger, accepted by the dispatcher.
- `ef903e5`: task 3 spawn helper, seven callers, delegation, six regression
  cases; green development checks and dispatcher-seat video QA.
- `fa2afab`: tasks 4-5 config/provenance/redaction implementation and tests;
  committed with the old B4 expectation red by design, as the dispatcher states.
- Turn 4 current diff: tools/headless_export.py; the single granted B4 function
  in tests/test_headless_export.py; added WARNING cases in
  tests/test_wp43_runner_redaction.py; DRAFT report; this ledger. Dispatcher
  assigns the commit SHA after this yield. Suggested subject:
  `fix(wp4.3a): redact logged warnings and assert corrupt-settings defaults`.

### Task 6 light-run matrix and actual status

| Required surface | Latest evidence | Remaining action on the amended candidate |
|---|---|---|
| New spawn file | Six cases passed Turn 2; forced-error additions passed Turn 3 focused set. | Include in the final combined light run. |
| tests/test_io_video_*.py | Turn 2 sandbox 474 passed/36 deselected including core layering; dispatcher video-only 494 passed/12 footage deselected. Turn 3 changed only failure texts and added forced-error checks. | Rerun permitted video cases after the text edits; leave hardware/footage/fullclip to the seat. |
| tests/test_config_*.py | Turn 3 broad set contained their passing cases; new timestamp/provenance cases passed individually and in the focused set. | Rerun after the scoped CLI logging change to check logging state interactions. |
| tests/test_headless_export.py | Turn 4 bounded run green, including renamed B4; one GUI plus three explicit UNC exclusions. | Seat run for the three UNC cases on this amendment; GUI handled at gate. |
| tests/test_wp43_runner_redaction.py | Turn 4 entire file green in bounded run, including both new WARNING cases. | Include in final combined light run. |
| tests/test_wp42a_runner_hardening.py | Turn 4 entire permitted file green in bounded run. | Include in final combined light run. |
| tests/test_wp42b_naming_guard.py | Turn 3 broad set green for its permitted cases. | Rerun after the logging amendment. |
| Layering: core_deps, io_video_decode_rules, io_video_probe_rules | Turn 2 all 48 selected layering cases passed unchanged. | Include in final layering run. |
| Layering: color_deps, analysis_deps, gui_deps, app_deps | Not yet run by this cell. | Run the permitted nodes; no GUI execution. |
| Ruff / mypy | Turn 4 both green; mypy 141 files. | Confirm against final candidate at the required boundary. |
| Global format check | Dispatcher 269 files already formatted before Turn 4; write-mode format applied to this amendment. | Dispatcher `uv run ruff format --check .`. |

### Remaining work and review discipline

1. Complete the task-6 combined light-run and layering lists above, with the
   required sandbox shim/no-cache options and work/wp4.3a temp roots. Do not
   execute the three administrative-share cases in this sandbox.
2. Refresh the DRAFT report's validation/limits after those checks and reviews;
   the draft is written, so it need not be recreated.
3. Reviewer A is the dispatcher's read-only Claude Opus/high PROCESS pass via
   scripts/codex_cell.py review. No round has been supplied/run yet. Adjudication
   turns change the ledger only and YIELD before remediation. Record cumulative
   severity/envelope/NEW-REOPENED/revert/product-vs-test/depth rows. At round 5
   and every fifth round, STOP under the fill's continuation policy.
4. Reviewer B is also the dispatcher's Claude pass. Then the orchestrator runs
   the ONE two-leg gate on the final candidate AFTER B; both expressions exclude
   fullclip. Do not request a full suite before B. No harness gate is required
   for this owned-file set.
5. Gate collection delta is intentional: one existing B4 node is renamed, and
   two new parameterized WARNING cases are added. This grant explains that
   removal/addition; no other existing headless node is changed.
6. All original locks persist, with only the explicit B4/runner grant added.
   No interface, GUI/app/jobs/photo writer, dependency, fixtures or register edit.
   No footage reads/writes, mailbox posts, git writes or sibling-worktree access.
   Keep report/register closures distinct: CHARC owns the closure/AD notes.

### Every ruling's location

- FINAL brief and governing Q-A/Q-B/Q-C: docs/briefs/wp4.3a-brief.md,
  CHARC `8fb519bac1878075`. The same brief carries the inherited Q9/Q13 approval
  (`2c4476d9869df056`) and Q14/Q20/Q21/Q23 decisions
  (`7c7df3dbe237ceb7`) verbatim.
- B4 and WARNING amendment: CHARC `a2ef868a6e14b506`, authoritative file
  C:\Users\rwsmy\clearwater-review-evidence\wp4.3a\b4-ruling-b6aa800a.md;
  verbatim text is in this ledger immediately above the Turn 4 execution record.
- AD-13 / AD-23 source: docs/decisions.md; accept notes remain owed by CHARC.
- Round/gate policy: docs/review-gate-clearwater.md, with the dispatch's AD-30
  not-fullclip amendment. The turn schedule/seat-only format/no-network sandbox
  constraints are in the dispatch prompts; latest bounded-turn instruction is
  the Turn 4 prompt. Do not replace them with generic skill workflow choices.

Context of record: Turn 3 input depth 205,870 of 258,400, supplied by the
orchestrator; Turn 4 footer depth is not yet supplied. Evaluate/re-seat from
this committed handoff rather than assuming more room or compacting mid-task.
