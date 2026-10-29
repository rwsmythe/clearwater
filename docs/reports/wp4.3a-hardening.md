# WP4.3a hardening report - Reviewer A converged, R2 cleanup complete

Development evidence for WP4.3a; this is not an accept record. Base:
`fe65e6a867106dd984d1c27ef3104e2ee3de0df4`. Product commits through `553d1f2`
were reviewed in R1; adjudication is committed as `a0b9235`. Turn 6's fixes are
c9a7771/40eef4e, and R2 adjudication is 5ec9142. Reviewer A converged at R2
(NO_NEW_CRITICAL_MAJOR); Turn 8 completes its bounded non-blocking cleanup.
Reviewer B and the ONE final two-leg gate are **PENDING**.

## Hardening table

| Row | Implemented behavior and evidence |
|---|---|
| DR-58 (b) / AD-23 | pipes.tool_spawn_kwargs supplies CREATE_NO_WINDOW on win32, zero elsewhere, and a fresh FFREPORT-free environment. All seven product spawn sites consume it; capability.tool_env delegates. Native/other-platform and real FFmpeg/ffprobe report-file controls passed. The guard pins the seven current sites. Its finite tested set is 31 APIs across direct calls, module aliases, from-import aliases, simple name bindings, simple attribute bindings, literal getattr and bound functools.partial (217 controls), plus 31 recognized-family star imports. Keyword/dict-literal flag settings and three literal-subscript store forms are checked. Unsupported forms are listed below; exhaustive Python call-flow detection is not claimed. |
| DR-76 | PresetStore and the runner accept the writer's profile key as dropped provenance. Real CPU export of a synthetic nclx HEIC provides the PNG iTXt used by both importer and CLI tests. The writer is unchanged. The granted --parameters help line now describes writer provenance including profile. |
| DR-77 | Preset import/load/list map the year-1 offset overflow to readable errors/unreadable entries while preserving the source. Three failing-first cases passed. |
| DR-81 (a)(b)(c)(d), plus the ruled WARNING route | Mixed literal/escaped/quoted separator forms are redacted. The R1 remediation guards the actual footage resolve reached through write_target_refusal/inside/_resolved, including own-path, output and cache checks in main and run. OSError, RuntimeError and actual embedded-NUL ValueError become path-free RunnerRefusalError; main exits 2 before any export, including late run refusals. The old artificial-resolution test was moved to these real routes; 23 RED-first cases pass. Packet-listing timeout names the input basename and READ_TIMEOUT_S; CUDA timeout names CUDA_CHECK_TIMEOUT_S; CUDA OSError exposes class/strerror only, with a fixed fallback when strerror is absent. Every clearwater.* WARNING across _main, including settings and batch records, passes through the scoped formatter, which detaches on exit. The fixed resolution message now names either folder in the footage write check without blaming only the configured footage path. |
| DR-85 | load_settings sets aside the unrepresentable timestamp and returns defaults. The amended B4 test proves exit 0, one byte-identical backup, a real export using default parameter values/bit depth, and no full path in stderr. |
| R3-1 (ii), CHARC `d6e9abdf` | output_folder is the only path-valued Settings field. A NUL, ValueError or OSError during path construction/absolute-path formation defaults only that field through _with_valid_values and _warn_out_of_range. Other settings and the original file survive; there is one warning and no set-aside. The decode check precedes frozen IF-10's Path construction and requires no output-directory existence or filesystem resolution. Four RED-first config cases (including injected getcwd OSError) and a real CLI export/warning case pass. For the per-field out-of-range warning only, the formatter hides the repr-valued invalid path even when it is unknown to Redactor; this does not cover arbitrary values embedded in the separate whole-file set-aside reason. |

Register closures, the new register row and AD-13/AD-23 accept notes remain
CHARC's work. No register change is made by this package.

## Rulings and behavior changes

The ledger records Round 0, governing brief rulings, the verbatim B4 amendment
`a2ef868a6e14b506` and CHARC `d6e9abdfa16feb0e` item 2 plus scope addition (ii).

- The helper remains in existing, standard-library-only pipes.py; probe does
  not import capability, avoiding the existing reverse edge. No new module.
- Q-A: packet-listing READ_TIMEOUT_S remains 600; probe's separate TOOL_TIMEOUT_S
  is 120. Timeout tests vary the limits to prove the messages use the constants.
- Q-B: tests/test_wp42_v3_product.py:141 (command at :133 on the base) and
  tests/test_wp321_fft_release.py:165 retain inherited-environment launches.
  They are unowned test-only residuals; an operator-set FFREPORT during these
  tests is outside this envelope. Their next authorized touch may add tool_env.
  DR-58 (a) and DR-81 N5 are not reached.
- Q-C: CUDA_CHECK_TIMEOUT_S remains 30. Both exception arms are covered; the
  warning caller is unchanged. F9 adds only the missing-strerror fallback.
- WP4.1 behavior change: B4's overflow refusal (exit 2) becomes D89's documented
  corrupt-file behavior (set aside, defaults, successful export), because DR-85
  classifies that timestamp as a reader decode failure for every caller, as
  CHARC ruled in a2ef868a6e14b506. The defensive runner OverflowError arm stays
  with its comment that load_settings handles the overflow.
- Windows console behavior (F8, reasoned, not a signal experiment):
  CREATE_NO_WINDOW prevents FFmpeg children receiving the runner console's
  Ctrl-C/Ctrl-Break. Ctrl-C uses the runner cancellation handler; Ctrl-Break
  killing Python can leave a child until stdin EOF. The flag is mandated by
  Q13/AD-23; signal-policy changes are outside this touch.

The corrupt-settings WARNING gap was pre-existing for ordinary malformed JSON
in WP4.1. The scoped handler redacts known settings/backup paths for that and
the year-one stamp; R3-1's per-field warning also passes through it. Arbitrary
unknown values embedded in a whole-file IF-10 error reason remain a separate
pre-existing limit (R2-3 below). A host's own logging handlers still
receive original records. The formatter copies records; library run retains
its existing last-resort filtering without adding a handler.

## Validation

All logs below are under work/wp4.3a. Sandbox pytest runs use
PYTHONPATH=scripts, sandbox_mkdir_shim, no cache provider and per-run temp roots
under that directory. No owner-footage input is used by this cell.

| Check | Actual result / evidence |
|---|---|
| Task 6 at dispatcher seat on 553d1f2 | 884 passed, 12 footage deselected in 777.96s; all three UNC cases included. Ruff format: 269 files already formatted; Ruff check passed; mypy clean in 141 source files. seat-t6.log. This is baseline development evidence, not a gate on Turn 6. |
| F1 real-route RED -> GREEN | 23 failed -> 23 passed, 9 deselected; 2.06s -> 0.69s. turn6-f1-red-final.log / turn6-f1-green.log. |
| F2 AST controls RED -> GREEN | 156 failed/6 passed -> 164 passed including product AST guards; 11 -> 9 deselected, 0.89s -> 0.87s. turn6-f2-red.log / turn6-f2-green.log. |
| F9 fallback RED -> GREEN | 1 failed -> 1 passed, 173 deselected; 0.18s -> 0.09s. turn6-f9-red.log / turn6-f9-green.log. |
| R3-1 per-field defaults and CLI warning RED -> GREEN | 4 failed -> 4 passed, 96 deselected; 0.96s -> 0.88s. turn6-r31-red.log / turn6-r31-green.log. |
| F4 help smoke | Old help fails the writer-provenance/profile assertion; granted line passes and --help exits 0. turn6-f4-red.log / turn6-f4-green.log. No existing test pins the old help wording. |
| Requested Turn-6 light regression plus WP4.2b naming | 561 passed, 4 deselected in 13.65s, no skips/failures. All config files, headless, new runner redaction, WP4.2a/WP4.2b and spawn tests; excluded gpu/footage/slow/gui/fullclip and explicitly deselected the three sandbox-blocked UNC cases. turn6-light.log. |
| Turn-6 spawn file after lint-only fixture line split | 174 passed in 1.52s, no deselections/skips/failures. turn6-spawn-final.log. |
| Ruff check | All checks passed! turn6-ruff-final.log. Initial E501 in an added AST fixture was corrected. |
| Strict mypy | Success: no issues found in 141 source files. turn6-mypy.log. |
| Write-mode format on six touched Python files | 6 files reformatted. turn6-format.log. Global format --check remains a dispatcher-seat check. |

Turn-8 cleanup evidence (same log directory):

| Check | Actual result / evidence |
|---|---|
| R2-1 controls RED -> GREEN | 89 failed, 162 passed, 12 deselected in 0.94s -> full spawn file 263 passed in 1.92s. turn8-guard-red.log / turn8-guard-green.log. The additions are 55 API/form cases, 31 star imports and 3 subscript stores. |
| R2-4 injected-getcwd RED -> GREEN | FileNotFoundError escapes before the fix: 1 failed, 67 deselected in 0.21s -> 1 passed, 67 deselected in 0.09s. turn8-path-red.log / turn8-path-green.log. Other settings, original file and one per-field warning are proved; no POSIX cwd manipulation/reproduction. |
| R2-2 wording smoke | Old fixed text fails the neutral-folder assertion; new path-free message passes. turn8-label-red.log / turn8-label-green.log. Only the refusal text changed. |
| Requested light checks | 593 passed, 4 deselected in 13.66s; no skips/failures. All config files, headless, runner redaction and spawn tests, excluding gpu/footage/slow/gui/fullclip plus the three explicit UNC nodes. turn8-light.log. |
| Ruff / strict mypy | All checks passed! / Success: no issues found in 141 source files. turn8-ruff.log / turn8-mypy.log. |
| Write-mode formatting of four touched Python files | 3 files reformatted, 1 left unchanged. turn8-format.log. Global --check remains at the dispatcher seat. |

The prior Turn-6 amendment's seat QA was 3 UNC tests passed in 0.98s and
269 files already formatted. These are prior-candidate results; request the
seat checks again on this cleanup rather than claim a current global pass.

The initial 24-case F1 RED matrix included a redundant delayed-NUL case; it was
removed because NUL necessarily fails the first resolve. The final 23-case
matrix has seven actual NUL routes and two delayed transient-error routes.
No failure is omitted: the only development check failure after the required
RED runs was the corrected E501 fixture line. The three UNC cases were not
retried in the known restricted sandbox; request a seat run on this amendment.

## Review status and limits

Reviewer A R1: NEW_CRITICAL_MAJOR_FOUND, 1 major, 2 minor, 6 advisory. The ledger
adjudicated every finding. Turn 6 fixes F1/F2/F3/F4/F9, with F4's explicit grant;
F5-F8 are disclosed below/as the console behavior line. R3-1 (ii) is an external
scope addition, not an extra R1 finding. R2 returned NO_NEW_CRITICAL_MAJOR:
0 critical, 0 major, 1 reopened minor (F2 partial), 4 new advisory findings.
Reviewer A has converged on the blocking axis under the fill. R2 verified F1,
F3/F4/F9 and R3-1; the terminating-round cleanup addresses the finite cheap
controls, neutral refusal text, path-validation OSError and report/docstring
precision. It creates no extra A round for non-blocking polish. Reviewer B,
then the ONE final two-leg gate, then accept remain the dispatcher sequence.
There is no final-suite/acceptance claim.

- R2-1 control boundary: the 31 tested APIs are subprocess.run/Popen/call/
  check_call/check_output/getoutput/getstatusoutput; os.system/popen,
  spawnl/spawnle/spawnlp/spawnlpe/spawnv/spawnve/spawnvp/spawnvpe,
  execl/execle/execlp/execlpe/execv/execve/execvp/execvpe, posix_spawn/startfile;
  and create_subprocess_exec/shell under asyncio and asyncio.subprocess.
  The seven syntactic forms and recognized-family star imports above are the
  controls proved. Residual forms include higher-order executor submission,
  default-argument/walrus/dict-lookup bindings, Popen subclasses, dynamic
  __import__/importlib, _winapi, multiprocessing, pty and unenumerated APIs.
  Dynamic flag keys/dict mutation methods are not proved by the literal-store
  guard. No current product code uses those residual launch forms. Disposition:
  REPORT-ONLY limit; dispatcher/CHARC owns follow-on control work if a product
  change introduces one. The report makes no general Python-analysis promise.
- R2-3 pre-existing leak: a wrong-typed output_folder such as a list can embed
  an unknown private value in frozen IF-10's _field_error repr. That text travels
  in the whole-file set-aside reason as %s and survives the formatter if its
  path is unknown to Redactor. The per-field %r suppression guarantee does not
  apply to it. Origins: bf76136 (IF-10) and 75d7dc5 (settings warning route).
  Disposition: REPORT-ONLY; the dispatcher will bank it with CHARC. No frozen
  error text or broader sanitizer is changed by this package.
- F5: unchanged raw OSError arms at verify.py:238, probe.py:140, encode.py:886
  and capability.py:99 (reviewed-candidate anchors) may expose filename on
  POSIX. Reviewer A executed Windows CreateProcess failures with filename=None;
  POSIX reachability is reasoned, not executed here. Q-C grants only decode's
  two exception arms. Disposition: REPORT-ONLY; dispatcher/CHARC owns banking
  and follow-on assignment at these arms' next authorized error-text touch.
- F6: file:/// URI and dot-segment spellings are unsupported redaction forms;
  the reviewer found no product text generating them. Disposition: REPORT-ONLY;
  dispatcher/CHARC owns banking, triggered if a product surface emits either.
  This package promises the ruled mixed-separator forms, not arbitrary text.
- F7: a malformed logging call whose mapping omits a key can fail before the
  formatter and make logging.handleError print a raw record. Normal product
  messages do not produce this trigger; the filter has the same earlier shape.
  Disposition: REPORT-ONLY; dispatcher/CHARC owns banking for the next logging
  hardening touch or a reachable malformed product call.
- F8: the console-signal consequence is disclosed above, REPORT-ONLY under the
  mandated flag; dispatcher/CHARC owns any future signal-policy commission.
- The new settings path check is lexical, does not require existence, and
  preserves valid relative paths. It handles NUL, ValueError and OSError; it does not
  turn an unavailable output directory into a corrupt settings file. The new
  getcwd case is injected portably; a deleted POSIX cwd was not reproduced.
- Global format check and three UNC cases need dispatcher-seat verification
  on this amendment. Reviewer/gate work is not replaced by the baseline run.
- Only owned files and the previously granted B4 function have changed over
  the arc. This turn changes no existing headless test, frozen interface,
  GUI/app/jobs/photo writer, dependency, fixture, local configuration or register.
  WP4.3 owns startup defense and its integration tests. No hardware, footage or
  fullclip test, product timing or memory measurement was run by this cell.
