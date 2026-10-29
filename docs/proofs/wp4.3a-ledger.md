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
| Turn 1 dispatch | Not supplied; fresh session (usage pace is not context depth) | 258,400 tokens | Record the next dispatcher reading without estimating; evaluate near 200K, stop at a step boundary near 250K. |

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
