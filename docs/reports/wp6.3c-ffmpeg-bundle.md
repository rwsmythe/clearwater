# WP6.3c - FFmpeg bundle

Status: turn 4 edits prepared, 2026-11-05. The dispatch records the seat's fork
commit/export and clean actionlint result; Dockerfile generation was refused by
the seat's tool policy and a static proof recorded instead. The real asset,
lock re-pin, remaining package work, review, package gate and release are pending.

## Turn 2 - Fork preparation and PATH-copy retirement

**Built.** Edited only `scripts.d/50-zvbi.sh`, `addins/9.0.sh` and
`.github/workflows/build.yml` in the supplied fork clone. The stage is disabled,
FFmpeg is pinned to `n9.0.2`, dispatch inputs remain, and the matrices select one
amd64 base runner, win64 bases and win64 / gpl 9.0 builds. Empty `tag_suffix`
dimensions preserve the retained steps' existing expressions. The repository
guard now runs on every dispatch; `build_ffmpeg` directly needs `pre_check` and
requires its success, including for `buildOnly=true`. The original sequential
job chain remains. Publication retains archive download/layout and checksums,
uses `ffmpeg-n9.0.2-nozvbi-${GITHUB_SHA:0:7}` and targets `$GITHUB_REF_NAME` (the
owner's dispatched fork branch). Latest, Wiki, Prune and all three GHCR cleanup
steps are removed. All 38 other retained steps are byte-unchanged against the
saved pre-edit LF texts. No Git command was run in the clone.

Requested fork commit subject:
`feat(wp6.3c): build win64 GPL FFmpeg n9.0.2 without zvbi`.
The independently generated unified diff is
`work/wp6.3c/turn2/ffmpeg-fork.diff` (256 lines), from the saved pre-edit texts and
the edited files, using Python's `difflib`, without Git. The seat compares it to
its Git diff, commits and exports `tools/package/ffmpeg-fork.patch`.

Removed `--with-ffmpeg`, the `with_ffmpeg` build argument/wiring and `copy_ffmpeg`.
Its unreferenced helper chain (`FFMPEG_TOOLS`, `tool_file_name`, `tool_version`)
is also removed. The CLI now reports the option as unrecognized. The README
names the paired pinned HTTPS fetch for release and local spike use. The native
origin implementation is unchanged; verified-archive origin support belongs to
the next turn.

**Test changes.** Removed these obsolete PATH-copy tests:

- `test_ffmpeg_is_copied_under_its_canonical_name`;
- `test_a_copied_tool_that_does_not_run_as_ffmpeg_is_refused`;
- `test_each_copied_tool_is_run_from_the_destination`.

Their replacement path is already exercised by the unchanged archive module's
canonical extraction, bounded tool execution and exact version/configuration
refusal tests. Rewrote both cases of
`test_build_enforces_origin_after_all_native_copies` and both cases of
`test_notices_writing_follows_ffmpeg_and_fails_the_build_on_error` to use that
module's existing synthetic ZIP/file-transport fixture. Only the text-executable
loader boundary is adapted; extraction, digest checks and version checks run.
The origin test retains the actual origin gate, positive trusted-byte control
and negative unknown-native/PATH-source diagnostic. Its test-only trust input
does not add a production exemption. The notices test requires extracted bytes
and the digest-bearing provenance record before notices, and retains its planted
coverage-failure refusal. The fixture adapter delegates non-FFmpeg subprocesses
to the real runner so PyInstaller's archive writer can query the OS.

Added `test_retired_with_ffmpeg_option_is_unknown`; updated
`test_release_ffmpeg_options_reach_the_build` to omit the removed keyword;
removed the obsolete mixed `--with-ffmpeg` / `--ffmpeg-from` parameter from
`test_release_ffmpeg_options_refuse_conflicting_or_incomplete_requests` (the
four incomplete/conflicting-request controls remain). Updated the stale-copy
test's docstring. Net collection change: three cases removed (three removed
functions, one removed parameter, one added function).

**RED -> GREEN.** The unmodified fork failed ten of thirteen structural checks
(`fork-red.log`). The final fork passes all thirteen (`fork-green-final.log`),
the retained-step audit (`fork-audit-final.log`) and the matrix-reference audit
(`fork-matrix-green.log`). These are local structural checks; actionlint and
generated Dockerfile evidence are not claimed. Before retirement, the new CLI
test failed with `DID NOT RAISE SystemExit` and the forwarding test failed on the
extra `with_ffmpeg` argument (`retirement-red.log`: two failed). After retirement
and fixture corrections, the six focused cases pass
(`retirement-green-clean-env-3.log`: six passed, 102 deselected).

**Validation.** All logs/XML below are under `work/wp6.3c/turn2/`.

- `ruff-check-final.log`: `All checks passed!`.
- `ruff-format-final.log`: `337 files already formatted`.
- `mypy-win32.log` and `mypy-darwin.log`: each reports
  `Success: no issues found in 166 source files`.
- `pytest-prescribed.log` / `.xml`: the prescribed command with the shim,
  timeout 300, QUIT_SCRIPT exclusion and fresh `work/c63c-2` basetemp reports
  `146 failed, 333 passed, 1 skipped, 15 errors in 70.22s (0:01:10)`.
- `pytest-isolated.log` / `.xml`: the same selection/shim/timeout/exclusion,
  fresh `work/c63c-2-isolated`, with the runner-only `PYTHONPATH` removed before
  `pytest.main`, reports
  `3 failed, 491 passed, 1 skipped in 98.15s (0:01:38)`.

| Module | Prescribed runner | Isolated runner |
|---|---|---|
| `test_tools_package_build.py` | 85 passed, 23 failed | 108 passed |
| `test_tools_package_ffmpeg.py` | 68 passed | 68 passed |
| `test_tools_package_notices.py` | 125 passed, 120 failed | 245 passed |
| `test_tools_package_smoke.py` | 19 passed, 15 setup errors, 1 skipped | 34 passed, 1 skipped |
| `test_release_workflow.py` | 36 passed, 3 failed | 36 passed, 3 failed |

The single skip is
`test_non_windows_containment_never_silently_skips`:
`POSIX process-group native proof belongs to WP6.5`.
The three failures in both runs are
`test_real_git_gate_restores_checkout_overwrite_and_refuses_invalid_tags`
with parameters `annotated`, `lightweight` and `wrong-commit`. Each fails while
setting up the local test repository's Git push (exit 128); Git's `sh.exe` reports fatal
`CreateFileMapping`, followed by inability to read the local remote. The seat
must rerun these outside the sandbox; no passing real-git result is claimed.

**Verification loop / deviations.**

- [MINOR, runner] Confirmed the prescribed `PYTHONPATH=scripts` conflicts with
  the unchanged production environment refusal: the exact runner fails before
  normal build/notices work. The supplemental runner starts with
  `PYTHONPATH=scripts`, imports pytest, removes that environment variable, then
  calls `pytest.main` with `-p sandbox_mkdir_shim -p no:cacheprovider` and the
  same selection. `scripts` remains on `sys.path`, so the shim loads normally.
  No production check or unowned test was altered to hide this conflict.
- [MINOR, fixture] Confirmed the reused fixture's release path initially lay
  outside its supplied build output root; aligned the test's output root with
  the fixture's parent. Confirmed its broad subprocess replacement intercepted
  PyInstaller's `ver` query; restricted the adapter to the two FFmpeg tools.
  Both corrections are test-only; all six focused cases then pass.
- [MINOR, verification false positive] Rejected the initial structural check's
  substring match for a push trigger: it also matched Docker's `push: true`.
  Restricted the check to the trigger block. The edited workflow was already
  dispatch-only.
- [MAJOR, fork workflow] Confirmed that deleting the arm include rows also
  deleted the declarations of `matrix.tag_suffix` used by retained steps.
  The independent expression audit failed by job name for both target-image
  jobs (`fork-matrix-red.log`). Added one empty suffix value in each matrix;
  the same audit now reports zero undeclared references.
- [MINOR, sandbox] The three real-git fixture failures remain seat-owned as
  commissioned. The final pass over the owned diff, fork step identity and
  matrix expressions found no further issue. Initial import-order/format slips
  were corrected; final static checks above are green.

**Handoff.** This turn bundles the two explicitly commissioned items. Reviewer
A is dispatcher-run after this yield. The seat still commits/exports the fork,
runs pinned actionlint and Dockerfile generation, and reruns the three real-git
cases. Q1 and round 0's four rulings remain with CHARC. All later package work is
commissioned by subsequent turns. The lock, lock policy, release workflow and
three unowned test modules were not edited. No dependency or frozen interface change,
footage/profile write, real PyInstaller build, frozen/GUI launch, Docker action,
external fetch, direct Git write, GitHub action or mailbox post was performed.

Depth: unavailable to the cell; the dispatcher supplies `depth_input_tokens`.

## Turn 3 - Deterministic release zip and verified FFmpeg origin

**Built (A).** Added onedir-only `--zip`, requiring `--notices --smoke` so neither
check can be omitted before publication. A successful smoke status now falls
through to zip creation; failures still return without writing a new archive or
sidecar. The build queries the checked-out source/tag commit with the read-only
`git log -1 --format=%ct HEAD` (20-second subprocess bound), then passes that
integer explicitly as `source_epoch` to `write_release_zip`. Writer tests supply
the integer directly without Git; the query test uses a bounded subprocess stub.

The writer takes the release wrapper, giving a single top-level
`Clearwater-<version>-<platform>-onedir/` folder and sorted relative file members.
It publishes `<wrapper name>.zip` and `<wrapper name>.zip.sha256` directly under
`--out`, matching the existing workflow. Only physical files count as members;
empty directories do not add members. Linked/special files, empty trees, outputs
inside the tree and dates outside ZIP's 1980..2107 range are refused. Every
member uses the commit's UTC date, seconds rounded down to DOS precision, fixed
Unix regular-file mode 0644, fixed creator/extractor versions and empty extra/
comment/internal attributes. Compression is explicitly DEFLATE level 9 per file.
No file mtime/mode is copied. The writer reads one file at a time, writes temporary
outputs and replaces the final paths after completing the archive and checksum.
The ASCII checksum line ends with literal LF. The workflow's existing append
form therefore places `# source-commit` on a separate line (including with CRLF
for that appended line). The release-workflow test's sole pending-flag assertion
now requires an empty set; no workflow code was edited this turn.

**Built (B).** `bundle_ffmpeg` retains its existing list return and accepts an
optional `verified_hashes` output set. After download size/sha256 verification and
the complete ZIP inventory check, it hashes the archive streams while extracting.
Only `bin/ffmpeg.exe` and `bin/ffprobe.exe` contribute identities. Both bounded
version/configuration checks must succeed before the set is updated. The build
starts a fresh set for each invocation and carries it directly into
`native_origin_violations(ffmpeg_hashes=...)`. That gate combines these complete
file hashes with the existing interpreter/locked-RECORD sources; the bootloader
check and recursive native/archive inspection remain active. Neither names nor
destination files nor `ffmpeg-BUILD.txt` supply trusted identities.

The extracted `ffmpeg-LICENSE.txt` (archive `LICENSE.txt`) and generated
`ffmpeg-BUILD.txt` are ordinary text, with neither a native suffix nor native
magic. They therefore need no native origin. They grant no trust to another
file, and native magic in a `.txt` would still trigger the existing content check.
Unextracted archive members, including `ffplay.exe`, contribute no hashes.

**Built (C).** Added only `tools/package/ffmpeg-fork.patch -text` to
`.gitattributes`. RED: read-only `git check-attr --source=HEAD text --
tools/package/ffmpeg-fork.patch` reports `text: unspecified`. GREEN: the same
working-tree query without `--source=HEAD` reports `text: unset`, preventing
checkout newline conversion of the mail patch (`patch-attribute-red.log` and
`patch-attribute-green.log`). The patch itself was not edited.

**RED -> GREEN.** Logs are under `work/wp6.3c/turn3/`.

- `red.log`: 17 failed, 6 passed, 101 deselected. The new CLI test reports
  `unrecognized arguments: --zip`; the writer/build cases expose missing APIs.
  Most importantly, the existing real origin gate rejects both verified tools
  with `native origin unknown` when no test-supplied hash exemption is present.
- `naive-red.log`: the separate `zipfile.write` baseline raises
  `AssertionError: naive ZIP bytes vary with filesystem mtimes` for identical
  content and changed filesystem times. This control does not call the new writer.
- `green.log`: the same focused selection reports
  `23 passed, 101 deselected`. Two writes of identical content are byte-equal
  despite reversed creation order, different mtimes and different file modes.
  Tests check layout, UTC/DOS timestamps, attributes, physical-file count, content,
  digest and final LF, plus the two-line checksum/comment append. Build tests
  refuse publication after notice, smoke or timestamp failure and cover success.
- `hash-mutant-red.log`: one failed, 125 deselected. A scratch copy of the build
  module is deliberately changed to hash destination files. A test corrupts an
  extraction write and rejects that implementation: the destination's altered
  digest must never replace the archive-stream identity. No product file was
  changed for this control. The final selection runs the unmodified stream reader.
- Origin controls cover post-extraction tool changes, an unknown native, a
  non-extracted archive member smuggled under another native name, a wrong digest
  argument, downloaded bytes differing from their pinned digest, unsafe inventory
  and failed version checks. Rejected bundles never populate the trusted set.

**Runner.** The exact isolated runner is
`work/wp6.3c/turn3/run_tests.py`:

```python
import os
import sys
import pytest

os.environ.pop('PYTHONPATH', None)
raise SystemExit(pytest.main([
    '-p', 'sandbox_mkdir_shim', '-p', 'no:cacheprovider', '--timeout', '300',
    '-k', 'not test_python_m_clearwater_starts_the_shell_and_exits_0',
    *sys.argv[1:]
]))
```

It is launched from PowerShell with `$env:PYTHONPATH='scripts'`, then:

```text
uv run --no-sync python work/wp6.3c/turn3/run_tests.py tests/test_tools_package_build.py tests/test_tools_package_ffmpeg.py tests/test_tools_package_notices.py tests/test_tools_package_smoke.py tests/test_release_workflow.py --basetemp=work/c63c-3-final --junitxml=work/wp6.3c/turn3/pytest-final.xml -q
```

The initial full selection uses `--basetemp=work/c63c-3`, `pytest.xml` and
`pytest.log`; it reports `3 failed, 507 passed, 1 skipped in 98.49s (0:01:38)`.
The final selection adds the downloaded-byte and corrupted-extraction controls
and reruns the final per-file compression implementation with a fresh basetemp.

**Final validation.**

- `ruff-check-final.log`: `All checks passed!`.
- `ruff-format-final.log`: `337 files already formatted`.
- `mypy-win32-final.log` and `mypy-darwin-final.log`: each reports
  `Success: no issues found in 166 source files`.
- `pytest-final.log` / `.xml`:
  `3 failed, 509 passed, 1 skipped in 98.33s (0:01:38)`.
- `module-counts.txt` (independently summarized from the final JUnit XML):

| Module | Final result |
|---|---|
| `test_tools_package_build.py` | 126 passed |
| `test_tools_package_ffmpeg.py` | 68 passed |
| `test_tools_package_notices.py` | 245 passed |
| `test_tools_package_smoke.py` | 34 passed, 1 skipped |
| `test_release_workflow.py` | 36 passed, 3 failed (sandbox Git fixture setup) |

Read-only `git diff --check` is clean. The final full selection found no new
product/test failure beyond the three named fixture limitations below. The
smoke module's source-entry routing child was checked before execution: it
redirects APPDATA, LOCALAPPDATA and XDG roots, blocks Qt imports, stubs GUI/worker
effects and has a 15-second timeout. No QUIT_SCRIPT integration test was run.

**Verification loop / handoff.**

- [MAJOR, identity control] Independently confirmed that destination-derived
  trust accepts the wrong identity using the deliberately broken scratch module;
  the test rejects it. The product hashes the verified archive streams instead.
- [MINOR, deterministic zip] Confirmed filesystem metadata makes the naive
  archive vary; the fixed-metadata writer passes byte-equality and independent
  metadata/digest expectations.
- [MINOR, portability] The first darwin mypy run rejected a Windows subprocess
  constant inside a conditional expression. Moved it into the existing explicit
  `sys.platform == "win32"` guard style and reran both platforms.
- [MINOR, sandbox] The initial full selection's only failures are the three
  pre-existing real-Git cases (`annotated`, `lightweight`, `wrong-commit`), during
  fixture setup's local Git push. Git's `sh.exe` reports fatal `CreateFileMapping`
  and cannot read the local remote. Those cases need the commissioned seat rerun;
  no passing real-Git claim is made here. The skip is the unchanged non-Windows
  containment proof deferred to WP6.5.

This turn bundles exactly the three commissioned items. Reviewer A remains the
dispatcher's pass after this yield. Q1, the real asset/re-pin, embedded-native
notices, later tag-gate work and the release remain later/seat work. No lock,
notices/smoke module, dependency or frozen interface was changed. No external
fetch, Git write to the Clearwater/fork repositories, real PyInstaller build,
frozen/GUI launch, Docker, desktop input, footage/profile write, GitHub action or
mailbox post was performed. The commissioned real-Git tests create only their
own temporary fixture repositories before the sandbox refuses the local push.

Depth: unavailable to the cell; the dispatcher supplies `depth_input_tokens`.

## Turn 4 - Release tag gate hardening

**Built.** Changed only the inline `Check release version` step, its tests and
this report. The re-fetch now runs:

```text
git -c http.lowSpeedLimit=1 -c http.lowSpeedTime=20 fetch --force --no-tags origin +refs/tags/v1.1.0:refs/tags/v1.1.0
```

The tag argument is derived from the validated `GITHUB_REF`; the example shows
the test's literal value. The existing 30-second subprocess timeout remains.
The HTTP settings also bound stalled/low-speed remote helpers, rather than
depending only on terminating their parent process. The execution test pins
the complete argv, single refspec and subprocess options.

After verifying the fetched ref's object type, the gate reads `git cat-file tag
<ref>` and requires exactly one `tag` header, equal to the short ref name. It
parses only the header block before the blank line; a matching line in the tag
message cannot satisfy the check. Missing, duplicate and mismatched headers are
refused. The annotated requirement, peel-to-`GITHUB_SHA`, package/requested
version checks, checkout-overwrite restoration and version output remain.

Every Git invocation supplies an operation-specific failure label to the shared
wrapper. `CalledProcessError`, `TimeoutExpired` and `OSError` become named
`SystemExit` messages, with exception chaining suppressed (`from None`). A fetch
failure says `Release tag v1.1.0 could not be fetched from origin (missing or
unavailable)` followed by its failure category. This deliberately does not
misidentify every transport/access failure as a missing tag. Twelve injected
failure cases exercise all four operations and three failure categories; each
requires the named refusal, suppressed context and no version-output file.

**Real-Git fixture / seat RED checklist.** All cases use file-only temporary
repositories, bounded subprocesses and a `clearwater.py` version stub; no
product entry point is imported. After cloning, origin force-moves an unrelated
tag from the first commit to the second. The checkout-overwrite fetch explicitly
uses `--no-tags` and its one refspec. After the gate, every case requires the
unrelated local tag to remain at its original object. All refusals require no
`Traceback` or `CalledProcessError` text and no output file.

| Item / test | Expected RED against `cbb25494` with these tests |
|---|---|
| Transport argv: `test_release_requires_annotated_tag_at_the_built_commit` (allowed case) | Exact call list differs: old fetch lacks both HTTP `-c` settings; old gate also omits the object-content read. |
| Object name: three `test_tag_gate_refuses_wrong_or_missing_object_name` cases | Old gate accepts the object; `pytest.raises(SystemExit)` fails. |
| Git failures: twelve `test_tag_gate_git_failures_are_named_refusals` cases | Existing operations leak process/timeout/OS exceptions; the new object-read operation is never reached, so its expected refusal is absent. |
| Real-Git `mismatched-name` | Origin's `v1.1.0` points to an annotated object created as `v1.0.9`, peeling to the correct commit. Old gate exits zero, so the nonzero-exit assertion fails. New gate must emit the object-name refusal. |
| Real-Git `deleted-origin` | Origin deletes the requested tag after checkout. Old gate exits with a process traceback; the named-fetch-message assertion fails. New gate must emit the named fetch refusal without a traceback. |
| Real-Git `annotated`, `lightweight`, `wrong-commit`; unrelated-tag assertion in every case | Existing-behavior controls: expected GREEN on both revisions. `cbb25494` already has `--no-tags` and the single-tag refspec. The unrelated-tag control catches a broadened forced fetch, while the exact-argv test also pins `--no-tags`. No baseline RED is claimed for behavior already correct. |

The seat runs the real-Git RED with the old workflow text and these tests, then
GREEN with this workflow, outside the sandbox. No real-Git success or observed
seat RED is claimed by this cell.

**Observed RED -> GREEN.** All logs/XML are under `work/wp6.3c/turn4/`.
The test-first focused run (`red.log` / `.xml`, fresh `work/c63c-4-red`) reports
`16 failed, 2 passed, 38 deselected in 0.45s`. The same selection after the gate
change (`green.log` / `.xml`, fresh `work/c63c-4-green`) reports
`18 passed, 38 deselected in 0.17s`. This selection covers the exact argv,
annotation/peeling controls, header cases and all twelve Git-failure cases.

**Final validation.** Used the turn-3 isolated runner's exact implementation,
copied to `work/wp6.3c/turn4/run_tests.py`: launch with `PYTHONPATH=scripts`,
remove that variable before `pytest.main`, and retain the sandbox mkdir shim,
disabled cache provider, 300-second timeout and QUIT_SCRIPT exclusion. Command:

```text
uv run --no-sync python work/wp6.3c/turn4/run_tests.py tests/test_release_workflow.py tests/test_tools_package_build.py --basetemp=work/c63c-4 --junitxml=work/wp6.3c/turn4/pytest.xml -q
```

- `ruff-check-final.log`: `All checks passed!`.
- `ruff-format-final.log`: `337 files already formatted`.
- `mypy-win32.log` and `mypy-darwin.log`: each reports
  `Success: no issues found in 166 source files`.
- `pytest.log` / `.xml`: `5 failed, 177 passed in 10.31s`.
  `module-counts.txt`, independently summarized from JUnit XML: build module
  126 passed; workflow module 51 passed / 5 failed.
- `diff-check.log`: read-only `git diff --check` exit 0.

All five pytest failures are fixture setup's local Git push (exit 128): Git's
`sh.exe` reports fatal `CreateFileMapping` and cannot read the temporary local
remote. They precede gate execution and affect exactly
`test_real_git_gate_restores_checkout_overwrite_and_refuses_invalid_tags` with
`annotated`, `lightweight`, `wrong-commit`, `mismatched-name`, `deleted-origin`.
The commissioned seat rerun is still required. The uv commands report that the
inherited main-tree `VIRTUAL_ENV` is ignored in favor of this project's `.venv`.

**Verification loop / handoff.** Confirmed the absent transport settings,
unvalidated object name and escaping Git errors with the focused baseline
failures; implemented their fixes and reran to green. Rejected a supposed
baseline unrelated-tag defect: the accepted gate already narrows the fetch, so
its new real-Git assertion is a preservation control. Corrected the initial
lint complaint about an unescaped regex match; final static checks are clean.
The final owned-diff/requirements pass found no further issue. No Reviewer A
round occurs inside this turn; the dispatcher runs it after this yield.

Seat real-Git execution and its before/after proof remain undone. All other
package rungs, Q1 and release work remain outside this turn. No external fetch,
repository Git write, build, frozen/GUI launch, Docker, desktop input,
footage/profile write, dependency/frozen-interface change, GitHub action or
mailbox post was performed. Git writes occurred only in pytest's disposable
fixture repositories under the commissioned basetemp.

Depth: unavailable to the cell; the dispatcher supplies `depth_input_tokens`.
