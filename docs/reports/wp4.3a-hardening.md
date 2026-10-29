# WP4.3a hardening report - DRAFT

This is development evidence for the dispatched WP4.3a package, not an accept
record. Reviewer A, Reviewer B and the final two-leg gate remain pending.
Base: `fe65e6a867106dd984d1c27ef3104e2ee3de0df4`; implementation through
`fa2afab`, followed by the bounded Turn 4 WARNING/B4 amendment awaiting commit.
The detailed evidence and verification history are in
`docs/proofs/wp4.3a-ledger.md`.

## Changes against the five register rows

| Row | Implemented behavior and development evidence |
|---|---|
| DR-58 (b) / AD-23 | `pipes.tool_spawn_kwargs` supplies CREATE_NO_WINDOW on win32, zero elsewhere, and a fresh FFREPORT-free environment. All seven product subprocess calls use it; capability.tool_env delegates. AST guards, native/other-platform cases and actual FFmpeg/ffprobe report-file positive controls passed. |
| DR-76 | Both preset readers drop and report/accept the writer's profile key. Synthetic nclx HEIC provenance extracted from a real CPU engine export imports into PresetStore and is accepted by CLI --parameters. The writer remains unchanged. |
| DR-77 | Preset import/load/list map the year-1 offset overflow to readable failures/unreadable entries, preserving the source. Three failing-first cases passed after the reader mapping changed. |
| DR-81 (a)(b)(c)(d), plus the ruled WARNING route | Redactor matches mixed separators in literal, doubled, escaped and quoted forms. Raising configured-footage resolution returns a path-free usage refusal. Packet-listing timeout text carries the input basename and READ_TIMEOUT_S; CUDA-check timeout carries CUDA_CHECK_TIMEOUT_S, and OSError carries only its class and strerror. The CLI now owns a scoped WARNING stderr handler whose formatter redacts a copy of the rendered record; it is installed in _main before settings loading and detached on exit. Settings/backup files are named by basename. |
| DR-85 | load_settings sets aside the unrepresentable timestamp and uses defaults. The amended B4 integration test proves exit 0, exactly one byte-identical set-aside file, an actual export, default parameter values/bit depth instead of planted settings, and no full path in stderr. |

Register closures and the AD-13/AD-23 accept notes remain CHARC's work.

## Grounding and rulings

Round 0 found seven calls on the dispatch base: capability.py:89;
decode.py:171/:330/:344; encode.py:879; probe.py:127; verify.py:225. Only
capability, encode and verify passed env=tool_env. The new helper remains in
standard-library-only pipes.py, so probe need not import capability and create
a cycle. The existing video module set is unchanged.

- Q-A: retain READ_TIMEOUT_S = 600 and construct the timeout text through the
  constant. The historical 120-second figure belonged to probe's separate
  TOOL_TIMEOUT_S. Tests also vary the limit to prove it is not hard-coded.
- Q-B: the inherited-environment test launches at
  tests/test_wp42_v3_product.py:141 (command starts at :133 on this base) and
  tests/test_wp321_fft_release.py:165 remain unowned residuals. They can adopt
  the helper at their next authorized touch; an operator-set FFREPORT during
  those tests is outside this package's envelope. DR-58 (a) is not reached.
- Q-C: both CUDA-check exception branches are covered; the timeout limit remains
  30 seconds and is referenced through CUDA_CHECK_TIMEOUT_S. The warning caller
  is unchanged. DR-81 N5 is not reached.
- CHARC `a2ef868a6e14b506` grants only the B4 test function's rename/update and
  the runner WARNING amendment. Its full text is recorded verbatim in the
  ledger; authoritative source:
  `C:\Users\rwsmy\clearwater-review-evidence\wp4.3a\b4-ruling-b6aa800a.md`.

WP4.1 behavior change: B4's overflow refusal (exit 2) becomes the documented D89
corrupt-file behavior (set aside, defaults, successful export), because DR-85
classifies that timestamp as a reader decode failure for every caller, as
CHARC ruled in `a2ef868a6e14b506`.

The corrupt-settings WARNING contains full paths at its source. CHARC identified
the plain-corrupt-file WARNING route as a pre-existing WP4.1 DR-81-class gap;
this amendment covers it alongside the overflow case. Under pytest capture,
the RED cases received the raw logged record but no redacted stderr warning;
the new handler makes that stderr warning explicit and redacted. The defensive
OverflowError arm in runner _settings is retained, with a comment stating that
DR-85 handles it in load_settings and this arm is unreachable through that loader.

## Validation so far

- Turn 2: six new cases RED then GREEN; 474 passed/36 deselected in the allowed
  sandbox video/layering run. Dispatcher seat: 494 passed/12 footage cases
  deselected; format check reported 268 files already formatted.
- Turn 3: six config cases and thirteen redaction cases reproduced RED;
  final focused set 25 passed. Broader set: 370 passed, four failures, one
  deselected. The failures were the stale B4 assertion and three blocked
  administrative-share tests. Dispatcher subsequently confirmed all three UNC
  cases pass and format check reports 269 files already formatted.
- Turn 4: both WARNING forms reproduced RED; both passed after the handler fix.
  Updated B4 plus both WARNING cases: 3 passed/9 deselected. Bounded headless,
  new runner and WP4.2a set: 136 passed/4 deselected (one GUI case and the three
  known sandbox-blocked UNC cases), no failures/skips. The UNC cases require a
  seat rerun on the amended candidate.
- Ruff check and strict mypy passed at each build boundary; the latest mypy
  summary is 141 source files. Global format check is a dispatcher-seat check.
- Every sandbox pytest execution uses sandbox_mkdir_shim, disables the cache
  provider and writes temp material under work/wp4.3a. Logs are under that same
  directory, with turn-specific names listed in the ledger.

The verification loop caught and fixed an incorrect provenance-test expectation
(the engine records effective defaults and a fresh timestamp), a missing doubled
literal-Unicode redaction form, and test lint issues. The external B4 test
conflict was raised before editing and resolved only under CHARC's narrow grant.
No new in-envelope finding arose in Turn 4's bounded GREEN pass.

## Limits and remaining work

- This report is DRAFT. Finish the task-6 light-run matrix on the amended head,
  Reviewer A to convergence, Reviewer B, then the ONE final two-leg gate. This
  package has no full-suite/gate pass claim yet.
- The runner redacts its own outputs and warning handler. A host's existing
  logging handlers receive their original records; formatting copies the record
  rather than changing another handler's view. The library run API retains its
  existing last-resort filtering and adds no handler.
- No frozen interface, GUI/app/jobs/photo writer, dependency, fixture or local
  configuration changed. The frozen timestamp parser's underlying overflow is
  contained at the owned readers. WP4.3 owns the separate startup integration
  test and its xfail removal after integration.
- No actual footage test, hardware measurement or fullclip run was performed
  by this cell. Synthetic inputs and per-test temp paths supplied the new
  integration evidence. No timing or memory claim is made.
