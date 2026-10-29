# WP4.3a hardening report - R1 remediation, R2 pending

Development evidence for WP4.3a; this is not an accept record. Base:
`fe65e6a867106dd984d1c27ef3104e2ee3de0df4`. Product commits through `553d1f2`
were reviewed in R1; adjudication is committed as `a0b9235`. Turn 6 remedies
R1 under CHARC `d6e9abdf` and adds the granted settings-path fix. Reviewer A R2,
Reviewer B and the ONE final two-leg gate are **PENDING**.

## Hardening table

| Row | Implemented behavior and evidence |
|---|---|
| DR-58 (b) / AD-23 | pipes.tool_spawn_kwargs supplies CREATE_NO_WINDOW on win32, zero elsewhere, and a fresh FFREPORT-free environment. All seven product spawn sites consume it; capability.tool_env delegates. Native/other-platform and real FFmpeg/ffprobe report-file controls passed. R1's AST weakness is fixed: alternate process APIs, aliases, bound names, getattr and partial are detected by 162 planted controls; exactly seven real sites are pinned. |
| DR-76 | PresetStore and the runner accept the writer's profile key as dropped provenance. Real CPU export of a synthetic nclx HEIC provides the PNG iTXt used by both importer and CLI tests. The writer is unchanged. The granted --parameters help line now describes writer provenance including profile. |
| DR-77 | Preset import/load/list map the year-1 offset overflow to readable errors/unreadable entries while preserving the source. Three failing-first cases passed. |
| DR-81 (a)(b)(c)(d), plus the ruled WARNING route | Mixed literal/escaped/quoted separator forms are redacted. The R1 remediation guards the actual footage resolve reached through write_target_refusal/inside/_resolved, including own-path, output and cache checks in main and run. OSError, RuntimeError and actual embedded-NUL ValueError become path-free RunnerRefusalError; main exits 2 before any export, including late run refusals. The old artificial-resolution test was moved to these real routes; 23 RED-first cases pass. Packet-listing timeout names the input basename and READ_TIMEOUT_S; CUDA timeout names CUDA_CHECK_TIMEOUT_S; CUDA OSError exposes class/strerror only, with a fixed fallback when strerror is absent. CLI settings WARNINGs use the scoped redacting formatter and detach on exit. |
| DR-85 | load_settings sets aside the unrepresentable timestamp and returns defaults. The amended B4 test proves exit 0, one byte-identical backup, a real export using default parameter values/bit depth, and no full path in stderr. |
| R3-1 (ii), CHARC `d6e9abdf` | output_folder is the only path-valued Settings field. A NUL or ValueError during path construction/absolute-path formation defaults only that field through _with_valid_values and _warn_out_of_range. Other settings and the original file survive; there is one warning and no set-aside. The decode check precedes frozen IF-10's Path construction and requires no output-directory existence or filesystem resolution. Three RED-first config cases and a real CLI export/warning case pass. The warning formatter hides the repr-valued invalid path even when it is unknown to Redactor. |

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
in WP4.1. The scoped handler covers that and the year-one stamp; R3-1's new
per-field warning also passes through it. A host's own logging handlers still
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
| Final spawn file after lint-only fixture line split | 174 passed in 1.52s, no deselections/skips/failures. turn6-spawn-final.log. |
| Ruff check | All checks passed! turn6-ruff-final.log. Initial E501 in an added AST fixture was corrected. |
| Strict mypy | Success: no issues found in 141 source files. turn6-mypy.log. |
| Write-mode format on six touched Python files | 6 files reformatted. turn6-format.log. Global format --check remains a dispatcher-seat check. |

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
scope addition, not an extra R1 finding. R2 must assess the remediation;
Reviewer A has not yet converged. Reviewer B and the ONE final two-leg gate
remain pending at the dispatcher seat. There is no final-suite/acceptance claim.

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
  preserves valid relative paths. It handles NUL and ValueError; it does not
  turn an unavailable output directory into a corrupt settings file.
- Global format check and three UNC cases need dispatcher-seat verification
  on this amendment. Reviewer/gate work is not replaced by the baseline run.
- Only owned files and the previously granted B4 function have changed over
  the arc. This turn changes no existing headless test, frozen interface,
  GUI/app/jobs/photo writer, dependency, fixture, local configuration or register.
  WP4.3 owns startup defense and its integration tests. No hardware, footage or
  fullclip test, product timing or memory measurement was run by this cell.
