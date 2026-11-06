# WP6.3c - FFmpeg bundle

Status: turn 15 implements Reviewer B r1's F-B1 runtime census and the
dispatched folds, 2026-11-06; acceptance pending. Its validation and remaining
seat checks are recorded in the turn-15 section below. The seat's supplied
baseline at `80914e17` is 698 passed / one skipped including real Git, with
local build/smoke/notices/zip and bundled-worker export proofs green.
Post-remediation reviews, seat verification, package gate and release remain
the seat's work. The fork patch remains the seat's r2 export.

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

## Turn 5 - DR-144 embedded components in carried natives (synthetic)

**Built.** Added independently declared, exact host identities and required
embedded-component/source sets. Planning measures carried hosts before consulting
interpreter or wheel ownership. A missing component row/binding, mismatched
source pin, or mismatched host identity refuses the artifact. Identity refusals
name the host, expected and actual SHA-256/size, and `re-census required`.
Embedded-text integrity errors name the host(s), component and text. An absent
host creates no embedded redistribution claim. Each carried host retains its
real parent row, including the parent's existing licence material and Qt
replaceability terms, plus explicit attribution to every embedded component.
The parent declaration is checked against the resolved owner, not used to grant
ownership. Coverage still checks entries and rows in both directions.

Embedded rows retain their own provenance and sources. Identical embedded text
bytes share one rendered block (SHA-256 plus byte count), while every individual
input is checked before sharing, including on a later render. Standalone native,
vendored, co-licensed and FFmpeg rules remain active. The loader's existing JSON,
path and schema checks are shared with the host preflight; invalid inputs are
not passed directly to ownership fallback.

**Exact schema addition for turn 6.** Schema version stays `1`. The optional
top-level `embedded_hosts` field is a list of records with exactly these keys:

```text
{
  "relpath": "<exact executable-folder-relative host path, using />",
  "sha256": "<64 lowercase hex characters>",
  "size_bytes": <positive integer, not boolean>,
  "parent": "<normalized audited parent owner, e.g. python or pyside6-essentials>",
  "components": [
    {"component": "<exact component-row name>", "source": {<provenance fields>}}
  ]
}
```

The host path is exact: no absolute paths, empty/dot/parent segments, backslash,
colon, or wildcard characters. Host declarations are unique case-insensitively;
inventory matching is case-insensitive. Each host's component list is nonempty
and has no duplicate names. Parent names use canonical lowercase distribution
spelling (`python` is the interpreter owner).

Each `source` object uses one of the existing provenance kinds, unchanged:
`release-archive`, `git-tree`, or `proprietary-redistributable`. It contains only
the selected component row's provenance fields: `provenance_kind`,
`upstream_repository`, `source_repository`, `source_commit`, `source_tag`,
`source_tag_object`, `source_path`, `source_archive_url`,
`source_archive_sha256`, `source_archive_size_bytes`, `licence_urls`,
`text_source`, `text_kind`, as applicable to that kind. It passes the existing
provenance validator and must equal the component row's corresponding field set
and values exactly (canonical JSON comparison). For the incoming CPython/Qt
git-tree rows this means `provenance_kind`, `source_repository`, `source_commit`,
`source_path`, and the paired `source_tag`/`source_tag_object` if supplied. A
well-formed replacement commit, tag, tag object or path still fails against the
independent host declaration.

Each embedded component row adds `embedded_in`, a nonempty list of the exact
declared `relpath` strings, without case-insensitive duplicates. Every path must
declare that component. This binding replaces `bundled_files`, `bundled_modules`,
`bundled_version_source`, `vendored_distribution`,
`vendored_distribution_version` and `co_licensed_with`; mixing those forms is
refused. All existing component-row fields, real text hash/size checks, version
evidence and provenance requirements still apply. One component can bind
several hosts, each with its own measured identity and parent. The fixture
exercises this across interpreter and wheel hosts, including one absent host.

No production manifest row or licence text was written. The production manifest
is byte-unchanged and does not yet declare any host. No smoke row-count edit is
needed. Turn 6 must supply the seat-verified production records/texts against
this schema; DR-144 is not claimed closed here.

**RED -> GREEN.** Evidence is under `work/wp6.3c/turn5/`.
The test-first baseline (`red.log` / `.xml`, `work/c63c-5-red`) reports
`24 failed, 245 deselected in 4.63s`. The baseline has no embedded declarations
or bindings: its strict schema refuses the new top-level field, so positive
cases cannot plan and the negative cases cannot produce their required
host/component-specific refusals. No claim is made that the baseline accepts
an unknown manifest field.

| Required case | Observed baseline RED | Final GREEN |
| --- | --- | --- |
| Missing row despite interpreter/RECORD owner | 2 failed | 2 passed |
| Changed host hash or size; both identities and re-census diagnostic | 2 failed | 2 passed |
| Wrong commit, tag, tag object or source path | 4 failed | 4 passed |
| Tampered text hash/size or missing text | 3 failed | 3 passed |
| Absent declared host, no redistributed text/claim | 1 failed | 1 passed |
| Complete Python, wheel and PySide6 hosts; parent + every text, exact coverage | 3 failed | 3 passed |

The other nine baseline failures are schema controls (wildcard/duplicate host,
bad identity/parent/source, unknown key, duplicate component and unbound row).
The final fixture has three embedded components and two distinct texts: alpha
and beta share one text, gamma has a different text; both texts render once.

Eight further controls cover removed/malformed bindings, a missing row whose
unique text would otherwise be orphaned, two-host carriage/absence, wrong parent
attribution, and a shared text copied to a separate path then tampered after
planning. `controls-red.log` / `.xml` reports `2 failed, 30 passed`: a null
binding leaked TypeError, and a scalar binding produced a generic schema error
without host/component context. The host preflight now requires a list before
membership testing. `green3.log` / `.xml`, fresh `work/c63c-5-green3`, reports
`32 passed, 245 deselected in 3.51s`.

Independent negative control: `run_guard_mutant.py` loads the real module and
replaces only `_embedded_claims` with an empty result in the test process.
`guard-mutant.log` / `.xml`, fresh `work/c63c-5-mutant`, reports
`6 failed, 271 deselected in 1.15s`, all six `DID NOT RAISE`. Thus both
missing-component cases and all four source-pin cases detect parent fallback
when the host preflight is disabled. No product file is changed for this proof.

**Final validation.** Used `work/wp6.3c/turn5/run_tests.py`, an exact copy of
turn 4's isolated runner: launch with `PYTHONPATH=scripts`, remove that variable
before `pytest.main`, retain `sandbox_mkdir_shim`, disable cacheprovider, set
the 300-second timeout, and exclude QUIT_SCRIPT. Command:

```text
uv run --no-sync python work/wp6.3c/turn5/run_tests.py tests/test_tools_package_notices.py tests/test_tools_package_build.py tests/test_tools_package_smoke.py tests/test_tools_package_ffmpeg.py --basetemp=work/c63c-5 --junitxml=work/wp6.3c/turn5/pytest.xml -q
```

- `ruff-check.log`: `All checks passed!` (exit 0).
- `ruff-format.log`: `337 files already formatted` (exit 0).
- `mypy-win32.log` and `mypy-darwin.log`: each reports
  `Success: no issues found in 166 source files` (exit 0).
- `pytest.log` / `.xml`: `505 passed, 1 skipped in 96.68s (0:01:36)` (exit 0).
- `evidence-summary.txt`, independently read from final JUnit XML: notices
  277 passed; build 126 passed; smoke 34 passed / 1 skipped; FFmpeg 68 passed.
  The unchanged skip is `test_non_windows_containment_never_silently_skips`:
  `POSIX process-group native proof belongs to WP6.5`.
- `diff-check.log`: read-only `git diff --check`, exit 0.

The smoke module's source-entry child was inspected before execution: redirected
APPDATA/LOCALAPPDATA/XDG roots, blocked Qt imports, stubbed GUI/worker effects and
a 15-second subprocess timeout. No QUIT_SCRIPT test was run. The uv commands
report the inherited main-tree VIRTUAL_ENV is ignored in favor of this project's
`.venv`; no environment override was used to evade a production check.

**Real-folder notices probe (copy only).** Copied the commissioned
`C:/Users/rwsmy/clearwater/work/wp6.3b-stage1d/dist-onedir/Clearwater-1.0.0-windows-onedir/Clearwater`
to `work/c63c-5/probe/Clearwater`, then ran:

```text
uv run --no-sync python tools/package/notices.py work/c63c-5/probe/Clearwater
```

`probe.log`: exit 0, notices written in the copy.
Inventory: **1536 entries; 25 component rows**. Notices SHA-256:
`3afe913e26ecd6fe65765943fef798450687bebf7df926d1f720da9b8e999d8c`.
It equals WP6.3b's supplied hash exactly; no notice lines changed.
`probe-source-before.log` and `probe-source-after.log` independently record that
same hash for the original's notices. The original build folder was never
written. The summary script records the probe count/digest/equality separately
in `evidence-summary.txt`.

**Verification loop / handoff.**

- [MAJOR, confirmed/fixed] Removing the carried-host preflight lets a missing
  embedded notice/source mismatch fall back to valid parent coverage. The
  independent mutant confirms this; the unmodified product's six controls pass.
- [MINOR, confirmed/fixed] Null/scalar embedded bindings lacked the required
  refusal behavior/context. Confirmed by the two additional RED cases; fixed
  before the focused and full GREEN runs.
- [MINOR, fixture, rejected as product defect] The initial Qt complete-host
  assertion read an entire upstream-audit container as if it were one licence
  input. Its actual input was an audited block, correctly rendered in isolation.
  Made this synthetic fixture carry its own installed LGPL text, so its
  byte-preservation assertion names the actual text. Existing audited-block
  negative controls remain unchanged and pass.
- [MINOR, static] Corrected initial line-length/format slips. Final static checks
  and both mypy targets pass. The final requirements/diff pass found nothing new.

Reviewer A is the dispatcher's pass after this yield; no review round is claimed
inside the turn. Turn 6's production census/records/texts, Q1, fork/asset/re-pin,
seat/release gates and the release remain undone as commissioned. Changed only
the notices module, its granted test module and this report. No dependency or
frozen-interface change, external fetch, Git write, real PyInstaller build,
frozen/GUI launch, Docker, desktop input, original build/footage/profile write,
GitHub action or mailbox post was performed.

Depth: unavailable to the cell; the dispatcher supplies `depth_input_tokens`.

## Turn 6 - STOP: bzip2 provenance input is incomplete

**Status:** input read-back only; no production records, texts, schema or tests
changed. The dispatch's instruction to stop on ambiguity applies before loading
the bzip2 row. The dispatcher receives this finding at the turn boundary.

**[MAJOR, input, in envelope]** The required `_internal/_bz2.pyd` row has a
verified existing licence text, but the supplied facts do not fit either existing
source-bearing provenance kind without inventing an upstream identity or deciding
how build-recipe provenance may stand in for component-source provenance.

Reproduction: `work/wp6.3c/turn6/provenance_probe.py`, executed as
`uv run --no-sync python work/wp6.3c/turn6/provenance_probe.py`, with output in
`work/wp6.3c/turn6/provenance-input.log` (exit 0). It reads only evidence, the
interpreter licence and the notices module; no product entry point is called.

- Census SHA-256 matches the commissioned
  `0a39493dde36344348b9cfcc80175d9852b5eebd295078016757e386fabaca2c`.
- The supplied texts directory currently contains 289 files (the dispatch named
  240); none has a bzip-named path. The census has no bzip2 upstream tag-object /
  commit / licence-file record. This count is an observation, not a claim that
  the later files belong to the verified 240-file inventory.
- PBS's supplied `pythonbuild/downloads.py`, lines 40-49, names bzip2 1.0.8,
  archive size 810029, SHA-256
  `ab5a03176ee106d3f0fa90e381da478ddae405918153cca248e682cd0c4a2269`,
  SPDX `bzip2-1.0.6`, and `LICENSE.bzip2.txt`. It supplies no upstream commit or
  tag object. The archive URL is
  `https://astral-sh.github.io/mirror/files/bzip2-1.0.8.tar.gz`.
- The actual build interpreter's `LICENSE.txt` is 25066 bytes, SHA-256
  `886a0ead2d89030ee62dbff52b04e47ab91998341295bb9c56fb952b4e081c7a`,
  matching census (f). Its line 362 names bzip2/libbzip2 1.0.8. Thus the existing
  text is available and verified; its absence is not the finding.
- Calling the existing `_provenance` validator with the supplied archive facts
  refuses them with `notices: native provenance missing source fields`.
  The `release-archive` form requires `source_tag`, `source_tag_object` and
  `source_commit` as well as archive identity. The `git-tree` form requires a
  source repository and commit. The known PBS commit pins a download recipe,
  rather than the bzip2 source tree or this interpreter's assembled licence.

**Ruling requested.** Recommended: the seat supplies bzip2's resolved upstream
tag / tag-object / commit and byte-verified licence file, allowing an ordinary
component row without broadening provenance. Alternatively, explicitly authorize
the PBS download-recipe pin as the bzip2 row's source provenance and specify the
binding to the existing interpreter text. The cell has not chosen that semantic
extension or mislabeled bzip2 as a proprietary redistributable.

**Host -> components -> texts read-back (all loading remains undone).** The
table summarizes the commissioned census, not newly installed manifest records.
Paths below are relative to `_internal/`; Qt host DLLs are under `PySide6/`.

| Host | Components | Supplied / existing texts to bind |
| --- | --- | --- |
| `python312.dll` | zlib, HACL*, BLAKE2, Mersenne Twister, SipHash24, dtoa, cfuhash, Audioop | zlib LICENSE; HACL / BLAKE2 source headers; CPython `Doc/license.rst` sections |
| `pyexpat.pyd`, `_elementtree.pyd` | expat | CPython expat COPYING / license.rst section |
| `_decimal.pyd` | libmpdec | CPython license.rst section |
| `_bz2.pyd` | bzip2 1.0.8 | Existing interpreter LICENSE.txt; source provenance awaits ruling above |
| `_lzma.pyd` | liblzma 5.8.1 | XZ COPYING.0BSD |
| `unicodedata.pyd`, `PySide6/Qt6Core.dll` | Unicode data | One shared Qt Unicode-3.0 text, as ruled |
| `PySide6/Qt6Core.dll` | zlib, PCRE2 / SLJIT, double-conversion, BLAKE2, MD4, MD5, SHA-1, SHA-3 / brg_endian, RFC 6234, SipHash, easing, TinyCBOR, tl::expected, UCD / CLDR, Tika MIME data | Corresponding qtbase component files / LICENSES files in census (d) |
| `PySide6/Qt6Gui.dll` | FreeType / BDF / PCF, grayraster, HarfBuzz, libpng, MD4C, Emoji Segmenter, D3D12MA, VMA, ICC profile, smooth scaling, X Server helper, AGLFN, XSVG, WebGradients, OpenGL headers, Vulkan registry, MiniEngine shader | Corresponding qtbase component files in census (d) |
| `PySide6/Qt6Network.dll` | libpsl, Public Suffix List | LICENSE.chromium, PSL-LICENSE.txt |
| `PySide6/Qt6Svg.dll` | XSVG-derived qsvghandler | HPND-sell-variant text and REUSE attribution |
| `PySide6/plugins/imageformats/qjpeg.dll`, `qtiff.dll` | libjpeg-turbo | qtbase LICENSE and ijg-license.txt |
| `PySide6/plugins/imageformats/qtiff.dll` | libtiff | qtimageformats COPYRIGHT |
| `PySide6/plugins/imageformats/qwebp.dll` | libwebp | qtimageformats COPYING and PATENTS |
| `PySide6/plugins/platforms/qwindows.dll`, `qdirect2d.dll` | Wintab | LicenseRef-Lcs-Telegraphics text and copyright attribution |
| `shiboken6/shiboken6.abi3.dll` | Python 3.7.0 buffer protocol and signature code | One PSF-3.7.0 text, as ruled |

**UNSURE dispositions.** U1: the PBS 5.8.1 pin and 0BSD ruling are available.
U2: carry the shared Unicode text as ruled; `python312.dll`'s table remains a
census inference. U3: dtoa / Audioop SPDX identification remains undone; use
licence-per-header labels if evidence cannot establish an SPDX id. U4: carry
one PSF 3.7.0 text for both uses as ruled. U5 / U6: carry tl::expected and
double-conversion as ruled, retaining the template-instantiation / inferred-build
limits. U7 / U9: retain attribution-version and inferred-configuration limits.
U8 belongs to the later wheel census. U10: retain the unverified HAVE_KQUEUE
guard limit. U11: pure-Python module census remains outside this turn. U12: the
missing root pyside REUSE file remains a limit, not an invented input.

**Validation / handoff.** RED and GREEN tests, both ruff commands, both mypy
targets, the four-module pytest selection, and positive / negative copied-folder
probes were not run: this is the binding input-ambiguity STOP before an
implementation change. No line-range field has landed; its exact schema remains
undone, together with every production row/text and the two root attribution
sentences. Reviewer A remains dispatcher-owned. No external fetch, Git write,
build, frozen/GUI run, Docker, desktop input or write to a protected source,
profile, footage or evidence directory occurred.

Depth: unavailable to the cell; the dispatcher supplies `depth_input_tokens`.


## Turn 7 - DR-144 production records: CPython and Qt / shiboken

**Built.** Loaded 60 embedded-component rows and 17 exact carried-host
declarations, bringing the native manifest to 70 records. Copied 93 new input
files, all referenced: whole licence texts, byte-exact source blobs and header /
section excerpts, and upstream attribution files. Census SHA-256 was checked
against `0a39493dde36344348b9cfcc80175d9852b5eebd295078016757e386fabaca2c`.
Every census input used was checked against section (d3)'s byte count, SHA-256
and Git blob SHA-1 before copying; all 240 inventory entries were parsed, and
only the named subset was read. The separately supplied bzip2 text matched its
1896-byte / SHA-256 / Git-blob record. No input from the concurrent wheel pass
was used. Scratch preparation and verification scripts/logs are under
`work/wp6.3c/turn7/`.

The bzip2 row binds `_internal/_bz2.pyd`, tag `bzip2-1.0.8`, tag object
`75a94bea3918e612b879d6a11ca64b8689526147`, commit
`6a8690fc8d26c815e798c588f796eabe9d684cf0`, and the published archive
SHA-256 `ab5a03176ee106d3f0fa90e381da478ddae405918153cca248e682cd0c4a2269`
/ 810029 bytes. Release-archive provenance now accepts a validated optional
`source_path` for its licence member (`LICENSE` here). Non-GitHub repositories
retain their real repository URL; the generator no longer invents a
Sourceware `/tree/<tag>` URL. Existing GitHub archive URL behavior remains.

The original ten records, interpreter-build record and vendored-path
declarations are unchanged (independent comparison with HEAD).
The Python and PySide6 rows in the root audit gain only the commissioned
attribution sentences. The smoke fixture carries the real `python312.dll`, so
its notices gain that host's eight embedded rows: its two row-count assertions
are now 14 / 16 (without / with its synthetic FFmpeg pair). No other smoke edit.

**Exact line-range field.** Schema version remains `1`. A git-tree row uses
`text_kind: "excerpt"`, its in-tree `source_path`, and:

```json
"text_lines": {
  "file": "<flat local filename of the complete source blob>",
  "lines": [1, 23],
  "git_blob_sha1": "<40 lowercase hex characters>",
  "sha256": "<64 lowercase hex characters>",
  "size_bytes": 38499
}
```

`lines` is a one-based, inclusive pair of positive integers, excluding booleans.
The end cannot exceed the blob's line count. The full source file must be a
regular, non-linked input with matching byte count, SHA-256 and Git blob SHA-1
(`blob <decimal byte length>\0<bytes>`). The excerpt's bytes must equal the
recorded range exactly, preserving original line endings. Both planning/loading
and rendering check this; a matching excerpt hash alone is insufficient.
The source path, range and full-blob identity are also part of the independent
host's source declaration, so a row cannot substitute another source/range.
Provenance prints the source path, blob hash and range. Complete source blobs
are verification inputs, not rendered licence text. HACL* carries lines 1-23;
BLAKE2 carries lines 1-12; the other CPython sections use the census's ranges.
The existing proprietary-interpreter excerpt contract is unchanged.

**Separate attribution inputs.** The real Qt licence texts sometimes omit the
component's copyright, which is in its `qt_attribution.json` (or qtsvg
`REUSE.toml`). Each affected git-tree row also declares:

```json
"attribution": {
  "file": "<flat local attribution filename>",
  "source_path": "<attribution path in the same pinned tree>",
  "git_blob_sha1": "<40 lowercase hex characters>",
  "sha256": "<64 lowercase hex characters>",
  "size_bytes": 731
}
```

All fields are strict; unsafe paths, other provenance kinds, unknown keys,
non-positive/boolean sizes, missing files and hash/blob mismatches fail closed.
Attributions are copied/rendered verbatim with their own source label. They are
included in the host's independently required source identity. Shared inputs
are checked before text sharing. This preserves Wintab's copyright, the
qsvghandler USC notice and generic-licence users' copyright statements without
inventing notice text or editing an upstream input. The row's main provenance
continues to identify its licence text's path separately.

**Host -> components -> texts.** Host paths below omit `_internal/`.
`cpython` means python/cpython at v3.12.13; `qtbase`, `qtimageformats`, `qtsvg`
and `pyside-setup` mean the census's resolved v6.12.0 commits. `zlib` is
madler/zlib v1.3.1; `xz` is tukaani-project/xz v5.8.1. Every full commit / tag
object, copied filename, text hash/size and attribution identity is in the
manifest, and each host's source set is independently declared there.

| Host | Emitted embedded rows |
| --- | --- |
| `PySide6/Qt6Core.dll` | 18 |
| `PySide6/Qt6Gui.dll` | 20 |
| `PySide6/Qt6Network.dll` | 2 |
| `PySide6/Qt6Svg.dll` | 1 |
| `PySide6/plugins/imageformats/qjpeg.dll` | 2 |
| `PySide6/plugins/imageformats/qtiff.dll` | 3 |
| `PySide6/plugins/imageformats/qwebp.dll` | 2 |
| `PySide6/plugins/platforms/qdirect2d.dll` | 1 |
| `PySide6/plugins/platforms/qwindows.dll` | 1 |
| `_bz2.pyd` | 1 |
| `_decimal.pyd` | 1 |
| `_elementtree.pyd` | 1 |
| `_lzma.pyd` | 1 |
| `pyexpat.pyd` | 1 |
| `python312.dll` | 8 |
| `shiboken6/shiboken6.abi3.dll` | 1 |
| `unicodedata.pyd` | 1 |

The detailed mapping includes the separate IJG and WebP patent notices as
required rows; OpenGL and ES2 headers retain their individual revisions.
FreeType's complete aggregate includes its FTL and GPL alternative texts, with
separate BDF/PCF rows. Identical shared terms/attributions render once.

| Host(s) | Component | Licence text / excerpt | Separate attribution |
| --- | --- | --- | --- |
| `pyexpat.pyd`, `_elementtree.pyd` | expat | `cpython:Doc/license.rst L847-873` | `-` |
| `_decimal.pyd` | libmpdec (mpdecimal) | `cpython:Doc/license.rst L978-1008` | `-` |
| `python312.dll` | zlib (CPython) | `zlib:LICENSE` | `-` |
| `python312.dll` | HACL* (hacl-star bb3d0dc8) | `cpython:Modules/_hacl/Hacl_Hash_MD5.c L1-23` | `-` |
| `python312.dll` | BLAKE2 reference code (libb2) | `cpython:Modules/_blake2/impl/blake2.h L1-12` | `-` |
| `python312.dll` | Mersenne Twister (MT19937) | `cpython:Doc/license.rst L305-352` | `-` |
| `python312.dll` | SipHash24 (Majkowski) | `cpython:Doc/license.rst L599-625` | `-` |
| `python312.dll` | cfuhash | `cpython:Doc/license.rst L937-975` | `-` |
| `python312.dll` | strtod and dtoa (David M. Gay) | `cpython:Doc/license.rst L628-655` | `-` |
| `python312.dll` | Audioop (SoX g771.c, Sun) | `cpython:Doc/license.rst L1048-1076` | `-` |
| `_lzma.pyd` | liblzma (XZ Utils) | `xz:COPYING.0BSD` | `-` |
| `_bz2.pyd` | bzip2 / libbzip2 | `bzip2:LICENSE` | `-` |
| `PySide6/Qt6Core.dll` | zlib (Qt bundled) | `qtbase:src/3rdparty/zlib/LICENSE` | `src/3rdparty/zlib/qt_attribution.json` |
| `PySide6/Qt6Core.dll` | PCRE2 | `qtbase:src/3rdparty/pcre2/LICENCE.md` | `src/3rdparty/pcre2/qt_attribution.json` |
| `PySide6/Qt6Core.dll` | PCRE2 - SLJIT | `qtbase:src/3rdparty/pcre2/LICENSE-SLJIT` | `src/3rdparty/pcre2/qt_attribution.json` |
| `PySide6/Qt6Core.dll` | double-conversion | `qtbase:src/3rdparty/double-conversion/LICENSE` | `src/3rdparty/double-conversion/qt_attribution.json` |
| `PySide6/Qt6Core.dll` | BLAKE2 reference (Qt) | `qtbase:src/3rdparty/blake2/COPYING` | `src/3rdparty/blake2/qt_attribution.json` |
| `PySide6/Qt6Core.dll` | MD4 | `qtbase:LICENSES/CC0-1.0.txt` | `src/3rdparty/md4/qt_attribution.json` |
| `PySide6/Qt6Core.dll` | MD5 | `qtbase:LICENSES/CC0-1.0.txt` | `src/3rdparty/md5/qt_attribution.json` |
| `PySide6/Qt6Core.dll` | SHA-1 (Reichl) | `qtbase:LICENSES/LicenseRef-SHA1-Public-Domain.txt` | `src/3rdparty/sha1/qt_attribution.json` |
| `PySide6/Qt6Core.dll` | SHA-3 Keccak | `qtbase:src/3rdparty/sha3/CC0_LICENSE` | `src/3rdparty/sha3/qt_attribution.json` |
| `PySide6/Qt6Core.dll` | SHA-3 brg_endian | `qtbase:src/3rdparty/sha3/BRG_ENDIAN_LICENSE` | `src/3rdparty/sha3/qt_attribution.json` |
| `PySide6/Qt6Core.dll` | RFC 6234 SHA-384/512 | `qtbase:src/3rdparty/rfc6234/LICENSE` | `src/3rdparty/rfc6234/qt_attribution.json` |
| `PySide6/Qt6Core.dll` | SipHash (Qt) | `qtbase:LICENSES/CC0-1.0.txt` | `src/3rdparty/siphash/qt_attribution.json` |
| `PySide6/Qt6Core.dll` | Easing equations (Penner) | `qtbase:src/3rdparty/easing/LICENSE` | `src/3rdparty/easing/qt_attribution.json` |
| `PySide6/Qt6Core.dll` | TinyCBOR | `qtbase:src/3rdparty/tinycbor/LICENSE` | `src/3rdparty/tinycbor/qt_attribution.json` |
| `PySide6/Qt6Core.dll` | tl::expected | `qtbase:LICENSES/CC0-1.0.txt` | `src/corelib/global/qt_attribution.json` |
| `PySide6/Qt6Core.dll`, `unicodedata.pyd` | Unicode UCD (Qt and CPython) | `qtbase:LICENSES/Unicode-3.0.txt` | `src/corelib/text/qt_attribution.json` |
| `PySide6/Qt6Core.dll` | Unicode CLDR | `qtbase:LICENSES/Unicode-3.0.txt` | `src/corelib/text/qt_attribution.json` |
| `PySide6/Qt6Core.dll` | Apache Tika MimeType definitions | `qtbase:LICENSES/Apache-2.0.txt` | `src/corelib/mimetypes/3rdparty/qt_attribution.json` |
| `PySide6/Qt6Gui.dll` | FreeType | `qtbase:src/3rdparty/freetype/LICENSE.txt` | `src/3rdparty/freetype/qt_attribution.json` |
| `PySide6/Qt6Gui.dll` | FreeType - BDF driver | `qtbase:src/3rdparty/freetype/BDF-LICENSE.txt` | `src/3rdparty/freetype/qt_attribution.json` |
| `PySide6/Qt6Gui.dll` | FreeType - PCF driver | `qtbase:src/3rdparty/freetype/PCF-LICENSE.txt` | `src/3rdparty/freetype/qt_attribution.json` |
| `PySide6/Qt6Gui.dll` | Anti-aliasing rasterizer (grayraster, from FreeType) | `qtbase:src/3rdparty/freetype/LICENSE.txt` | `src/gui/painting/qt_attribution.json` |
| `PySide6/Qt6Gui.dll` | HarfBuzz-NG | `qtbase:src/3rdparty/harfbuzz-ng/COPYING` | `src/3rdparty/harfbuzz-ng/qt_attribution.json` |
| `PySide6/Qt6Gui.dll` | libpng | `qtbase:src/3rdparty/libpng/LICENSE` | `src/3rdparty/libpng/qt_attribution.json` |
| `PySide6/Qt6Gui.dll` | MD4C | `qtbase:src/3rdparty/md4c/LICENSE.md` | `src/3rdparty/md4c/qt_attribution.json` |
| `PySide6/Qt6Gui.dll` | Emoji Segmenter | `qtbase:LICENSES/Apache-2.0.txt` | `src/3rdparty/emoji-segmenter/qt_attribution.json` |
| `PySide6/Qt6Gui.dll` | D3D12 Memory Allocator | `qtbase:src/3rdparty/D3D12MemoryAllocator/LICENSE.txt` | `src/3rdparty/D3D12MemoryAllocator/qt_attribution.json` |
| `PySide6/Qt6Gui.dll` | Vulkan Memory Allocator | `qtbase:src/3rdparty/VulkanMemoryAllocator/LICENSE.txt` | `src/3rdparty/VulkanMemoryAllocator/qt_attribution.json` |
| `PySide6/Qt6Gui.dll` | sRGB ICC profile (sRGB2014.icc) | `qtbase:src/3rdparty/icc/LICENSE.txt` | `src/3rdparty/icc/qt_attribution.json` |
| `PySide6/Qt6Gui.dll` | Smooth scaling algorithm (qimagescale.cpp) | `qtbase:src/gui/painting/LICENSE.QIMAGETRANSFORM.txt` | `src/gui/painting/qt_attribution.json` |
| `PySide6/Qt6Gui.dll` | X Server helper (qregion.cpp) | `qtbase:src/gui/painting/LICENSE.XCONSORTIUM.txt` | `src/gui/painting/qt_attribution.json` |
| `PySide6/Qt6Gui.dll` | Adobe Glyph List For New Fonts | `qtbase:src/gui/text/LICENSE.AGLFN.txt` | `src/gui/text/qt_attribution.json` |
| `PySide6/Qt6Gui.dll` | XSVG (qguisvg) | `qtbase:src/gui/util/LICENSE.XSVG.txt` | `src/gui/util/qt_attribution.json` |
| `PySide6/Qt6Gui.dll` | WebGradients | `qtbase:util/gradientgen/LICENSE.WEBGRADIENTS.txt` | `util/gradientgen/qt_attribution.json` |
| `PySide6/Qt6Gui.dll` | OpenGL headers | `qtbase:src/gui/opengl/LICENSE.KHRONOS.txt` | `src/gui/opengl/qt_attribution.json` |
| `PySide6/Qt6Gui.dll` | OpenGL ES 2 headers | `qtbase:src/gui/opengl/LICENSE.KHRONOS.txt` | `src/gui/opengl/qt_attribution.json` |
| `PySide6/Qt6Gui.dll` | Vulkan API Registry (vk.xml) | `qtbase:src/gui/vulkan/LICENSE.txt` | `src/gui/vulkan/qt_attribution.json` |
| `PySide6/Qt6Gui.dll` | MiniEngine D3D12 mipmap shader | `qtbase:src/gui/rhi/LICENSE.MiniEngine.txt` | `src/gui/rhi/qt_attribution.json` |
| `PySide6/Qt6Network.dll` | libpsl (lookup code) | `qtbase:src/3rdparty/libpsl/src/LICENSE.chromium` | `src/3rdparty/libpsl/qt_attribution.json` |
| `PySide6/Qt6Network.dll` | Public Suffix List data | `qtbase:src/3rdparty/libpsl/PSL-LICENSE.txt` | `src/3rdparty/libpsl/qt_attribution.json` |
| `PySide6/plugins/imageformats/qjpeg.dll`, `PySide6/plugins/imageformats/qtiff.dll` | libjpeg-turbo | `qtbase:src/3rdparty/libjpeg/LICENSE` | `src/3rdparty/libjpeg/qt_attribution.json` |
| `PySide6/plugins/imageformats/qjpeg.dll`, `PySide6/plugins/imageformats/qtiff.dll` | libjpeg-turbo (IJG notice) | `qtbase:src/3rdparty/libjpeg/ijg-license.txt` | `src/3rdparty/libjpeg/qt_attribution.json` |
| `PySide6/plugins/platforms/qwindows.dll`, `PySide6/plugins/platforms/qdirect2d.dll` | Wintab API headers | `qtbase:LICENSES/LicenseRef-Lcs-Telegraphics.txt` | `src/3rdparty/wintab/qt_attribution.json` |
| `PySide6/plugins/imageformats/qtiff.dll` | libtiff | `qtimageformats:src/3rdparty/libtiff/COPYRIGHT` | `src/3rdparty/libtiff/qt_attribution.json` |
| `PySide6/plugins/imageformats/qwebp.dll` | libwebp | `qtimageformats:src/3rdparty/libwebp/COPYING` | `src/3rdparty/libwebp/qt_attribution.json` |
| `PySide6/plugins/imageformats/qwebp.dll` | libwebp patent grant | `qtimageformats:src/3rdparty/libwebp/PATENTS` | `src/3rdparty/libwebp/qt_attribution.json` |
| `PySide6/Qt6Svg.dll` | XSVG-derived qsvghandler.cpp (USC ISI) | `qtsvg:LICENSES/HPND-sell-variant.txt` | `src/svg/REUSE.toml` |
| `shiboken6/shiboken6.abi3.dll` | Python 3.7.0 (shiboken buffer protocol and signatures) | `pyside-setup:sources/shiboken6/shibokenmodule/files.dir/shibokensupport/signature/PSF-3.7.0.txt` | `sources/shiboken6/libshiboken/qt_attribution.json` |


**UNSURE dispositions.**

- U1: liblzma 5.8.1 comes from PBS's pinned recipe, not a binary version string;
  0BSD is retained. The manifest's version evidence states this limit.
- U2: one Qt-pinned Unicode-3.0 text covers `unicodedata.pyd` (UCD 15.0.0),
  Qt6Core's UCD revision 36 and CLDR v48.2. The UCD row binds both declared
  hosts; CLDR retains a distinct component row using the same text. Presence
  of the separate `python312.dll` Unicode tables was not proved by the census;
  no additional host claim is invented for it.
- U3: the carried dtoa notice is David M. Gay / Lucent's permission notice;
  the Audioop notice is Sun's unrestricted-use / disclaimer text. No SPDX id
  was established offline, so rows say `LicenseRef-dtoa-notice` and
  `LicenseRef-Audioop-Sun-notice`, with "licence per ... header, no SPDX id
  claimed" in their evidence. `LicenseRef-WebP-patent-grant` likewise labels
  the separate patent text without inventing an SPDX identifier.
- U4: one PSF-3.7.0 text covers shiboken's compiled buffer-protocol code and
  attributed adapted signature code in one host-bound row. The signature
  members' Qt-only headers cannot establish which adapted PSF code survives;
  the manifest explicitly retains that limit. The PSF text renders once.
- U5/U6: tl::expected and double-conversion are carried as ruled. Surviving
  template instantiations / double-conversion presence are not independently
  proved by strings; Qt's attributions and build definitions are the evidence.
- U7: FreeType, HarfBuzz, libtiff, libwebp, MD4C, D3D12MA, VMA, TinyCBOR and
  Emoji Segmenter versions rely on the pinned attributions/build definitions
  where binary version strings are absent; no stronger claim is made.
- U8: pillow-heif and the other wheel census belong to the next dispatch.
- U9: Qt feature states rely on symbols/strings, build definitions and defaults;
  no configure summary/SBOM was supplied for this wheel.
- U10: the Windows select/kqueue absence retains the census's unverified
  `HAVE_KQUEUE` source-guard limit. `selectmodule.c` was not a supplied input.
- U11: the native census did not inspect the attributed pure-Python modules in
  PYZ/base_library.zip; their presence remains outside this turn's evidence.
- U12: pyside-setup's missing root REUSE.toml remains a limit; no replacement
  was invented. Its supplied component attribution files are carried.

**RED -> GREEN.** No network test or production entry point is added.

| New check | RED evidence | GREEN evidence |
| --- | --- | --- |
| Git-tree line-range source/blob/range and rendering controls (15 cases) | `red2.log`: 7 failed, 8 passed, 277 deselected; old schema cannot accept valid excerpt declarations or produce the required component-specific refusals | `green.log`: 15 passed; final `new-final.log` includes all 15 |
| Separate upstream copyright inputs (5 cases) | `attribution-red.log`: 5 failed, 292 deselected | `green2.log`: 20 passed for both groups; final selection retains all 5 |
| Production host/row/source/text completeness | `production-red.log`: 1 failed (no production host declarations) | `production-green2.log` includes the passing real manifest; final selection retains it |
| Sourceware archive member and unsafe-path controls (6 cases) | `archive-red.log`: 6 failed; old validator treats member path as mixed provenance | `production-green2.log`: 7 passed with the production case; final selection retains all 6 |

The corrected test-first baseline follows an initial fixture-only error in
`red.log`: the literal source blob has 54 bytes, not 55. That length/header was
corrected before recording `red2.log`; the erroneous run is not a product RED.
The first production GREEN attempt also reproduced the unsupported bzip2
member-path issue before its six focused RED controls and fix.

`excerpt-mutant.log`: **6 failed, 298 deselected**, all `DID NOT RAISE`, when a
test-only plugin substitutes text-hash-only reads for full-blob/range checks.
It detects wrong range, wrong Git blob, a self-consistent invented excerpt,
missing/changed full source and source mutation after planning. The product
file is never changed for this independent negative control.

`new-final.log` / `.xml`: **27 passed, 277 deselected in 4.70s** on final
inputs. The existing production Git checks now include full source blobs and
attributions as well as licence texts, checking raw Git identities and `-text`
checkout attributes for every input. Existing synthetic fixtures remove the
production declarations when reducing their copy to a synthetic OpenSSL row;
they do not claim the real census covers synthetic bytes.

**Validation.** Every runner output is file-backed under
`work/wp6.3c/turn7/`. The unchanged isolated runner (`run_tests.py`) starts with
`PYTHONPATH=scripts`, removes that environment variable before `pytest.main`,
retains the loaded `sandbox_mkdir_shim`, disables cacheprovider, uses a
300-second timeout and excludes QUIT_SCRIPT. No production environment refusal
is relaxed. The smoke source-entry child was inspected: disposable
APPDATA/LOCALAPPDATA/XDG roots, blocked Qt imports, stubbed GUI/worker effects
and a 15-second subprocess bound.

```text
uv run --no-sync python work/wp6.3c/turn7/run_tests.py tests/test_tools_package_notices.py tests/test_tools_package_build.py tests/test_tools_package_smoke.py tests/test_tools_package_ffmpeg.py --basetemp=work/c63c-7-final --junitxml=work/wp6.3c/turn7/pytest-final.xml -q
```

- `ruff-check-head.log`: `All checks passed!`, exit 0.
- `ruff-format-head.log`: `337 files already formatted`, exit 0.
- `mypy-win32-head.log` and `mypy-darwin-head.log`: each
  `Success: no issues found in 166 source files`, exit 0.
- Initial exact `work/c63c-7` selection: `pytest.log` / `.xml`,
  **2 failed, 530 passed, 1 skipped in 134.60s**. Both failures were
  `test_complete_smoke_preserves_shipping_bytes_and_checks_conditional_tools`
  (False/True): the stale 6/8 row-count assertion. The transcript independently
  recorded 14/16, and the commissioned row-count-only change fixes them.
- Final fresh `work/c63c-7-final` selection: `pytest-final.log` / `.xml`,
  **532 passed, 1 skipped in 135.15s**, exit 0.

| Module | Final result |
| --- | --- |
| `test_tools_package_notices.py` | 304 passed |
| `test_tools_package_build.py` | 126 passed |
| `test_tools_package_smoke.py` | 34 passed, 1 skipped |
| `test_tools_package_ffmpeg.py` | 68 passed |


The unchanged skip is `test_non_windows_containment_never_silently_skips`:
`POSIX process-group native proof belongs to WP6.5`.
The final focused input tests and static pass also cover the final patent-grant
LicenseRef label and explanatory docstring after the full run began; no
behavioral code changed during that run.

**Positive and negative notices probes (fresh copies only).** `probe.py` first
copies the commissioned seat folder, then verifies every declared host's full
hash and size in the copy before running the notices writer. Initial copies
are under `work/c63c-7/probe/` and `probe-negative/`; the final rerun, after the
patent-grant label clarification, uses fresh `probe-final/` and
`probe-negative-final/`. No frozen binary is run. `probe-final.log` and
`probe-results.json` record:

- POSITIVE: **85 component rows, 1536 entries, 60 embedded-component rows**;
  all 17 declared hosts present and matching, with per-host counts in the
  table above. Notices SHA-256
  `520df27e8c81d6802af37e60cb7cccfd4bfada8bfb8ae3ea8333ba808e0b1ac8`.
- NEGATIVE (expected refusal): after appending one byte only to the second
  copy's `_internal/_decimal.pyd`, the writer reports that host's identity
  differs, expected SHA-256
  `fcdc8bc61ee2dac17fbb9a8eea45242e22a34d1a71abac9bee7f732dc3f8b79f`
  / 246272 bytes, actual SHA-256
  `90936042862745fc94234592fc50f19c0d8f326610922962491e55288fc3a3ff`
  / 246273 bytes, **re-census required**. It refuses before writing notices.
- Original seat folder's notices SHA-256 before/after stays
  `3afe913e26ecd6fe65765943fef798450687bebf7df926d1f720da9b8e999d8c`.
- `surface-audit.log`: every new row's exact terms and attribution bytes occur
  in the final output; no unreferenced DR-144 input; the original ten records
  and other manifest declarations are unchanged; Unicode and PSF texts each
  occur once; source verification blobs are not rendered as licence texts.

**Verification loop / handoff.**

- [MAJOR, confirmed/fixed] A matching excerpt hash does not prove the text
  comes from the pinned blob/range. The new equality checks and the independent
  six-case bypass mutant establish the required distinction.
- [MAJOR, confirmed/fixed] Generic Qt licence texts alone lose copyrights
  stored in separate attributions. The byte-verified, source-bound attribution
  inputs now render with the corresponding terms and fail closed when altered.
- [MINOR, confirmed/fixed] Sourceware's archive needs its licence member path
  without a fabricated GitHub tree URL. Six focused controls plus the real
  bzip2 row verify the extension within release-archive provenance.
- [MINOR, test-only, confirmed/fixed] The two smoke fixture row totals changed
  with eight real CPython embedded components. Only their owned assertions
  changed; the final full selection passes.
- [MINOR, data, confirmed/fixed] The separate WebP patent row now uses the
  descriptive `LicenseRef-WebP-patent-grant`, rather than an invalid pseudo-SPDX
  conjunction. Final focused tests, static checks and both fresh copy probes
  cover the final input surface.
- [MINOR, fixture, rejected as product defect] Corrected the initial literal
  source-blob length before the valid RED. No production change was driven by
  that fixture error.
- Final comparison of census mappings, every output term/attribution and shared
  blocks, ownership boundaries, baseline manifest retention and the full
  validation results found no additional issue. Read-only `git diff --check`
  is recorded separately in `diff-check.log`.

**STOPPED ROWS:** none. The supplied bzip2 provenance resolves turn 6's STOP.

This turn bundles only the commissioned production loading and its necessary
line-range / attribution / archive-path support. Reviewer A is dispatcher-run
after this yield; no review round or convergence is claimed here. DR-144 is
not claimed closed: the wider Pillow / SciPy / other-wheel production census
is the next dispatch. Q1, fork run/asset/re-pin, remaining package work, seat
gates and the release also remain undone. No build.py, FFmpeg lock or workflow
edit, dependency/frozen-interface change, external fetch, Git write, real
PyInstaller build, frozen/GUI launch, Docker, desktop input, original build /
profile / footage / evidence-folder write, GitHub action or mailbox post was
performed. Only the files granted for this turn changed.

Depth: unavailable to the cell; the dispatcher supplies `depth_input_tokens`.


## Turn 8 - DR-144 production wheel-native census

**Built.** Loaded the second seat census, `dr144-census-wheels.md`, SHA-256
`c00de8a67b4222b927f1979112626f759863395c4f5cec510d6c6ff7563637cd`.
The parser consumes all 111 host identities in section (c) and all 170 text
inventory records in section (d3). The production manifest gains 43 embedded
component records and 93 independently measured host declarations (110 total).
All 83 SciPy natives are declared, including the 82 .pyd files' static runtime.
There are 113 component records: 108 local-text records and five references to
already carried notice inputs. The original ten standalone records stay first;
embedded component records, new host component lists and host paths are sorted.

`work/wp6.3c/turn8/load_records.py` is the seat-reviewable generation script.
It verifies the census hash and every selected input's byte count, SHA-256 and
Git blob SHA-1 before copying. Exact hosts and their hashes/sizes come only from
census (c), not from filenames or installed-file inference. The supplementary
`audit_surface.py` independently compares all 33 selected whole blobs to the
seat files and all 20 excerpt records to their one-based inclusive slices.
There are 53 new text/blob files; some rows share a whole input. A repeated
load is byte-identical. Final manifest SHA-256: `306b748543be40986bd8631071d8942e3aa9ee7fd42c3a6b96d9848e438d9156`.
`generated-hosts.json` records all new declarations; `verified-inputs.json`
records the selected full-blob identities. These scripts/results are scratch
files under `work/wp6.3c/turn8/`, not committed product or seat-folder edits.

**Why notices.py changes.** The original three provenance kinds remain intact.
Their local text-file schema could not bind an embedded runtime to an already
rendered wheel/audit input. Added a strictly separate carried-notice reference
binding, without a fourth provenance kind or invented source pin. Its row has
exactly `component`, `upstream_version`, `spdx`, `version_evidence`,
`embedded_in`, `carried_notice`. The last object has exactly `row` (an original
carried notice row's exact name) and `inputs` (unique objects with `sha256` and
`size_bytes`). The independent host declaration pins `{"carried_notice": ...}`
in its `source` field. Reference rows cannot mix local source/text fields.
The local-input loader validates references; planning resolves each against
one original carried row and one input per identity. Absent/ambiguous rows or
inputs refuse. References cannot chain. Absent hosts emit no reference claim.
Host hash/size, owner attribution, source-reference equality and ordinary
native/vendored/FFmpeg checks all remain active. Render rechecks each input
before sharing and names host/component on embedded audit-text failures.

GCC GPL/exception inputs, the MinGW-w64/winpthreads inputs, Pillow's
libyuv/libsharpyuv aggregate and NumPy's code terms are REUSED, not copied into
the surface. Text blocks are shared across original carried and embedded rows
by exact bytes; every source input is still checked. Original wheel/audit
provenance stays with the reused material. No new GCC/GPL, winpthreads,
libyuv or sharpyuv licence file is introduced. The rows supply explicit host
bindings even where the carried aggregate names another library or host.

**Host -> component -> text table (new records).** Paths below are relative to
`_internal/`; `.cp312-win_amd64.pyd` suffixes are shortened only in this table.
Every exact path, independent host identity, source commit, text hash/size and
full-blob/excerpt input is in the manifest. Seven xsf dependency users are
`special/{_ufuncs,_ufuncs_cxx,_special_ufuncs,_gufuncs,_specfun,_ellip_harm_2,cython_special}`;
the attribution follows the census and pinned xsf build dependency, without
claiming a per-function symbol/instantiation proof for each header.

| Host(s) | Component | Verified text / reused input |
| --- | --- | --- |
| `scipy/special/_ellip_harm_2`, `scipy/special/_gufuncs`, `scipy/special/_specfun`, `scipy/special/_special_ufuncs`, `scipy/special/_ufuncs`, `scipy/special/_ufuncs_cxx`, `scipy/special/cython_special` | AMOS (xsf) | `scipy/xsf@f7b85f505a94:include/xsf/amos/amos.h`; lines 1-37 |
| `scipy/sparse/linalg/_eigen/arpack/_arpacklib` | ARPACK (SciPy) | `scipy/scipy@e4e854eaa8f1:scipy/sparse/linalg/_eigen/arpack/arnaud/ARPACK_LICENSE.txt`; lines 52-91 |
| `scipy/optimize/_highspy/_core`, `scipy/optimize/_highspy/_highs_options` | BASICLU and IPX (HiGHS terms) | `scipy/HiGHs@4f96ee8f40b2:LICENSE.txt` |
| `scipy/optimize/_highspy/_core`, `scipy/optimize/_highspy/_highs_options` | BASICLU copyright notice (SciPy) | `scipy/HiGHs@4f96ee8f40b2:highs/ipm/basiclu/basiclu_factorize.c`; lines 1-6 |
| `scipy/stats/_biasedurn` | BiasedUrn (SciPy) | `scipy/scipy@e4e854eaa8f1:scipy/stats/biasedurn/license.txt` |
| `scipy/interpolate/_rbfinterp_pythran`, `scipy/linalg/_linalg_pythran`, `scipy/optimize/_group_columns`, `scipy/special/_ufuncs_cxx`, `scipy/stats/_stats_pythran` | Boost.Math and Pythran Boost headers | `boostorg/math@c114cf4a6ae9:LICENSE` |
| `scipy/sparse/linalg/_dsolve/_superlu` | COLAMD copyright notice (SciPy) | `scipy/scipy@e4e854eaa8f1:scipy/sparse/linalg/_dsolve/SuperLU/SRC/colamd.c`; lines 62-68 |
| `scipy/special/_ellip_harm_2`, `scipy/special/_gufuncs`, `scipy/special/_specfun`, `scipy/special/_special_ufuncs`, `scipy/special/_ufuncs`, `scipy/special/_ufuncs_cxx`, `scipy/special/cython_special` | Cephes (xsf) | `scipy/xsf@f7b85f505a94:LICENSES_bundled.txt`; lines 3-37 |
| `scipy/optimize/_direct` | DIRECT (SciPy) | `scipy/scipy@e4e854eaa8f1:scipy/optimize/_direct/COPYING` |
| `scipy/special/_ellip_harm_2`, `scipy/special/_gufuncs`, `scipy/special/_specfun`, `scipy/special/_special_ufuncs`, `scipy/special/_ufuncs`, `scipy/special/_ufuncs_cxx`, `scipy/special/cython_special` | Faddeeva (xsf) | `scipy/xsf@f7b85f505a94:LICENSES_bundled.txt`; lines 39-61 |
| all 82 SciPy .pyd (census c; exact paths in manifest) | GCC runtime (SciPy static) | REUSE `scipy` (1 exact SHA-256/size input(s)); original provenance |
| `scipy/optimize/_highspy/_core`, `scipy/optimize/_highspy/_highs_options` | HiGHS (SciPy) | `scipy/HiGHs@4f96ee8f40b2:LICENSE.txt` |
| `scipy/sparse/csgraph/_matching` | LAPJVsp (SciPy) | `scipy/scipy@e4e854eaa8f1:LICENSES_bundled.txt`; lines 33-66 |
| `scipy/optimize/_lsap` | LSAP (SciPy) | `scipy/scipy@e4e854eaa8f1:scipy/optimize/rectangular_lsap/rectangular_lsap.cpp`; lines 1-41 |
| `libde265-0-da04b6b2448c39c0b7f218769dedb2f1.dll` | MD5 notice (libde265) | `strukturag/libde265@ba62bf4cfb32:libde265/md5.cc`; lines 1-36 |
| all 82 SciPy .pyd + scipy.libs/OpenBLAS + numpy.libs/OpenBLAS | MinGW-w64 CRT and winpthreads (static wheels) | REUSE `pillow-heif / MinGW runtime` (2 exact SHA-256/size input(s)); original provenance |
| `scipy/linalg/_fblas`, `scipy/linalg/_flapack`, `scipy/stats/_biasedurn`, `scipy/stats/_rcont/rcont` | NumPy code embedded in SciPy | REUSE `numpy` (3 exact SHA-256/size input(s)); original provenance |
| `scipy/sparse/linalg/_propack` | PROPACK (SciPy) | `scipy/scipy@e4e854eaa8f1:scipy/sparse/linalg/_propack/PROPACK/PROPACK_LICENSE.txt` |
| `scipy/interpolate/_rbfinterp_pythran`, `scipy/linalg/_linalg_pythran`, `scipy/optimize/_group_columns`, `scipy/stats/_stats_pythran` | Pythran runtime (SciPy) | `serge-sans-paille/pythran@580c5abea7bd:LICENSE` |
| `libstdc++-6-e4d43a335d57132a6ec3004cece76b4f.dll` | Ryu (libstdc++) | `gcc-mirror/gcc@78d4ac73dd39:libstdc++-v3/src/c++17/ryu/common.h`; lines 1-16 |
| `scipy/sparse/linalg/_dsolve/_superlu` | SuperLU (SciPy) | `scipy/scipy@e4e854eaa8f1:scipy/sparse/linalg/_dsolve/SuperLU/License.txt` |
| `scipy/optimize/_moduleTNC` | TNBC original credit (TNC) | `scipy/scipy@e4e854eaa8f1:scipy/optimize/tnc/tnc.c`; lines 27-47 |
| `scipy/optimize/_moduleTNC` | TNC (SciPy) | `scipy/scipy@e4e854eaa8f1:scipy/optimize/tnc/LICENSE` |
| `scipy/special/_ufuncs_cxx` | Wright omega (SciPy) | `scipy/scipy@e4e854eaa8f1:scipy/special/wright.cc`; lines 21-51 |
| `scipy/sparse/linalg/_eigen/arpack/_arpacklib`, `scipy/sparse/linalg/_propack` | arnaud (SciPy) | `scipy/scipy@e4e854eaa8f1:scipy/sparse/linalg/_eigen/arpack/arnaud/LICENSE` |
| `scipy/optimize/_highspy/_core`, `scipy/optimize/_highspy/_highs_options` | cuPDLP-C (HiGHS terms) | `scipy/HiGHs@4f96ee8f40b2:LICENSE.txt` |
| `PIL/_avif` | dav1d (Pillow) | `videolan/dav1d@b546257f7707:COPYING` |
| `libstdc++-6-e4d43a335d57132a6ec3004cece76b4f.dll` | fast_float (libstdc++) | `gcc-mirror/gcc@78d4ac73dd39:libstdc++-v3/src/c++17/fast_float/fast_float.h`; lines 11-39 |
| `scipy/optimize/_highspy/_core`, `scipy/optimize/_highspy/_highs_options` | filereaderlp (SciPy) | `scipy/HiGHs@4f96ee8f40b2:extern/filereaderlp/LICENSE` |
| `libx265-217-276e7d75772a32bd086b54d54e01fd11.dll` | json11 (x265) | `Multicorewareinc/x265@e9b88125dc21:source/dynamicHDR10/json11/LICENSE.txt` |
| `PIL/_avif` | libaom (Pillow) | `python-pillow/Pillow@bb1d8e8ab8d2:wheels/dependency_licenses/AOM.txt` |
| `PIL/_avif`, `PIL/_imaging`, `PIL/_webp` | libsharpyuv (Pillow) | REUSE `pillow` (1 exact SHA-256/size input(s)); original provenance |
| `PIL/_avif` | libyuv (Pillow) | REUSE `pillow` (1 exact SHA-256/size input(s)); original provenance |
| `scipy/ndimage/_nd_image` | ndimage (SciPy) | `scipy/scipy@e4e854eaa8f1:scipy/ndimage/LICENSE.txt` |
| `scipy/optimize/_highspy/_core`, `scipy/optimize/_highspy/_highs_options` | pdqsort (SciPy) | `scipy/HiGHs@4f96ee8f40b2:extern/pdqsort/license.txt` |
| `scipy/fft/_duccfft/pyduccfft`, `scipy/optimize/_highspy/_core`, `scipy/optimize/_highspy/_highs_options`, `scipy/optimize/_pava_pybind`, `scipy/spatial/_distance_pybind` | pybind11 (SciPy) | `scipy/scipy@e4e854eaa8f1:LICENSES_bundled.txt`; lines 111-140 |
| `PIL/_avif`, `PIL/_imaging`, `PIL/_imagingcms`, `PIL/_imagingmath`, `PIL/_imagingtk`, `PIL/_webp` | pythoncapi_compat (Pillow) | `python-pillow/Pillow@bb1d8e8ab8d2:src/thirdparty/pythoncapi_compat.h`; lines 1-15 |
| `scipy/special/_ellip_harm_2`, `scipy/special/_gufuncs`, `scipy/special/_specfun`, `scipy/special/_special_ufuncs`, `scipy/special/_ufuncs`, `scipy/special/_ufuncs_cxx`, `scipy/special/cython_special` | qd double-double (xsf) | `scipy/xsf@f7b85f505a94:LICENSES_bundled.txt`; lines 63-114 |
| `scipy/special/_ellip_harm_2`, `scipy/special/_gufuncs`, `scipy/special/_specfun`, `scipy/special/_special_ufuncs`, `scipy/special/_ufuncs`, `scipy/special/_ufuncs_cxx`, `scipy/special/cython_special` | specfun (xsf) | `scipy/xsf@f7b85f505a94:include/xsf/specfun/specfun.h`; lines 1-20 |
| `scipy/optimize/_trlib/_trlib` | trlib (SciPy) | `scipy/scipy@e4e854eaa8f1:scipy/optimize/_trlib/trlib_krylov.c`; lines 1-23 |
| `PIL/_avif` | x86inc (dav1d) | `videolan/dav1d@b546257f7707:src/ext/x86/x86inc.asm`; lines 1-22 |
| `libx265-217-276e7d75772a32bd086b54d54e01fd11.dll` | x86inc (x265) | `Multicorewareinc/x265@e9b88125dc21:source/common/x86/x86inc.asm`; lines 1-24 |
| `scipy/special/_ellip_harm_2`, `scipy/special/_gufuncs`, `scipy/special/_specfun`, `scipy/special/_special_ufuncs`, `scipy/special/_ufuncs`, `scipy/special/_ufuncs_cxx`, `scipy/special/cython_special` | xsf (SciPy) | `scipy/xsf@f7b85f505a94:LICENSE` |

TNC additionally retains the original Stephen G. Nash TNBC credit and the C
conversion credit (tnc.c lines 27-47); the MIT terms remain in the TNC row.
BASICLU's exact copyright notice is separate from the shared HiGHS terms;
COLAMD's exact notice is labelled LicenseRef, not an inferred BSD grant.
The two HiGHS component rows share the same MIT text with HiGHS. ARPACK and
PROPACK retain their originals' texts as well as the shared SciPy rewrite
licence. Ryu selects the BSL-1.0 alternative; the original dual-licence header
is preserved and full BSL terms are also carried by the Boost row.

**STOPPED ROWS (excluded; no closure or substitute licence inferred).**

| Item / row | Missing input or ruling |
| --- | --- |
| U-S1: L-BFGS-B | Original upstream notice/obligations for the C rewrite absent from v1.18.1 tree. |
| U-S1: MINPACK | Original upstream notice/acknowledgment for the C rewrite absent. |
| U-S1: SLSQP | Original upstream notice/obligations for the C rewrite absent. |
| U-S1: NNLS | Original upstream notice/obligations for the C rewrite absent. |
| U-S1: LSODA | Original upstream notice/obligations for the C rewrite absent. |
| U-S1: VODE / ZVODE | Original upstream notice/obligations for the C rewrite absent. |
| U-S1: FITPACK | Original upstream notice/obligations for C/C++ rewrites absent. |
| U-S1: original ID | Only the SciPy rewrite header, not the original ID notice, is established. |
| U-S1: original CDFLIB | Only the SciPy rewrite header, not the original CDFLIB notice, is established. |
| U-S1: original QUADPACK | Only the SciPy rewrite header, not the original upstream notice, is established. |
| U-P2: AOM PATENTS | Text not fetched; CHARC/owner ruling pending. |
| U-P2: libyuv PATENTS | Text not fetched; CHARC/owner ruling pending. |
| U-T1: Tcl/Tk Pillow shim excerpt | Whether declaration-only _tkmini.h embeds copyrightable expression is pending; excerpt omitted as directed. |
| U-P1: libaom fastfeat, vector, SVT-AV1 kernels, x86inc | AOM build files and exact inclusion/texts not established. The separately proved dav1d x86inc row is loaded. |
| U-N2: libquadmath in either OpenBLAS DLL | Presence and applicable text not established; strings/import absence is not proof. |
| U-S6: mdspan/Kokkos in xsf | Header not fetched; instantiation/host not established. The bundled text is only a pointer. |
| U-S8: Cython-generated utility code | Whether a notice is owed and which text/hosts are required is not established. |
| U-S9: Sobol Joe-Kuo direction-number data | Carried data copy and applicable notice not established by this native census. |
| U-H3: Ryu / fast_float statically inside SciPy | Their use by any SciPy .pyd is not established; only the proven pillow-heif libstdc++ hosts are bound. |

The declared runtime rows for U-S1's compiled hosts still bind their proven
GCC/MinGW components. They do not supply a licence ruling for the stopped
upstream algorithm notices. COLAMD's missing referenced licence and the
inferred BASICLU/IPX/cuPDLP-C terms remain material limits below. DR-144 is
NOT claimed closed; the 1.1.0 draft remains subject to these dispositions.

**Limits (loaded records retained where only version/build option is unsure).**

- U-P3: AOM text is Pillow's exact 12.3.0 copy, not a verified AOM-tree text.
- U-N1: numpy Highway/x86-simd-sort coverage follows numpy build defaults;
  numpy-release build options were not obtained. Existing carried texts stay.
- U-S2: SciPy's bundled-licence path mislabels are reported by the census;
  this turn uses verified actual paths and does not edit upstream sources.
- U-S3: CRT/winpthreads versions are unknown; reused texts point at mingw-w64
  master. The SciPy GCC 15.2.0 ident is established for all 82 .pyd. Generic
  GPL/exception terms reused from the carried OpenBLAS aggregate do not claim
  the same compiler release as its GCC 10.3.0 source-path evidence.
- U-S4: COLAMD's copyright notice is loaded; its referenced licence is absent.
  No BSD-3-Clause determination is substituted for that missing document.
- U-S5: BASICLU/IPX/cuPDLP-C are built in HiGHS; repository-wide MIT coverage
  is inferred, not a separately verified upstream licence grant. The manifest
  evidence and generated notices say this; BASICLU's actual header is retained.
- U-S7: pybind11's exact release is not known; SciPy's pinned licence statement
  is used. Pythran is 0.19.0, but its bundled Boost-header version is not fixed
  by the Boost.Math 1.91.0 source pin; only the BSL terms are shared.
- U-H1: json11 presence has RTTI evidence; HDR10+ build options are inferred.
- U-H2: x86inc assembly build options in dav1d/x265 are not proved; both exact
  notices are loaded as directed.
- U-H3: libstdc++ 16.2.0 is inferred from siblings; to_chars/from_chars exports
  prove Ryu/fast_float presence. Their static inclusion in SciPy is not proved
  and no such additional SciPy binding is invented.
- Other build-derived versions (OpenJPEG, liblzma, libyuv, libsharpyuv, dav1d)
  are described as census/build evidence rather than new binary-version reads.

**RED -> GREEN and verification loop.** All logs remain file-backed under
`work/wp6.3c/turn8/`; none of the production entry points is invoked by the new
checks. The source-entry smoke child was inspected: disposable roots, Qt import
block, GUI/worker stubs, 15-second bound. QUIT_SCRIPT stays excluded.

| Suspected / confirmed / rejected / fixed | Evidence |
| --- | --- |
| Missing embedded reuse binding: CONFIRMED, FIXED | `red.log`/`.xml`: 7 failed; `green-reference2`: 7 passed. Existing texts now get host attribution without copying them. |
| Missing wheel records/runtime hosts: CONFIRMED, FIXED | `red-data`: 5 failed; `green-data2`: 13 passed (including reference/previous production checks). |
| Generated evidence trailing spaces: CONFIRMED, FIXED | Initial `green-data` schema refusal; generator trims metadata; subsequent checks load all inputs. |
| Audit failure lacked host context; TNBC original credit omitted: CONFIRMED, FIXED | Corrected-fixture `controls-red2`: 2 failed / 2 passed; `controls-green`: 4 passed. Initial `controls-red` had a test-fixture source-URL omission, corrected before the meaningful RED. |
| All new tests distinguish old production: CONFIRMED | `run_head_red.py` loads unmodified `git show HEAD:tools/package/notices.py` from scratch, patches only the test loader: 16 failed / 304 deselected, no errors. HEAD remains ec59bd66. |
| Regeneration might vary host ordering/material identity: REJECTED | `surface-audit.json`: repeated generation byte-equal; 33 whole inputs and 20 slices independently matched. |
| Final source/provenance description might claim a header where an aggregate exists: CONFIRMED, FIXED | Generator distinguishes source-file headers from line-range excerpts of licence files. `final-records`: 16 passed on the final manifest; fresh `probe-verified` rerun below. |

The final verification pass checked source-byte identities, deterministic
manifest loading, host bindings, reused-text rendering and refusal behavior;
no further in-envelope issue was found. Reviewer A has not run in this cell;
the dispatcher runs it between turns. No review ledger round is claimed here.

**Fresh copy probes (final manifest).** `probe-verified.log` and `probe-results.json`:

- POSITIVE: **128 rows, 1536 entries, 103 embedded rows**, all 110 declared hosts measured and matching. Notices SHA-256 `e4d9cd344e9d7da4bf6680d1a08306d0648e63264dc5b5a9ddc1b5385ce51afa`.
- Embedded rows by package: pillow 6; pillow-heif 5; numpy 1; scipy 32. The MinGW row is shared by numpy/SciPy, so these package counts overlap.
- NEGATIVE: `notices: embedded _internal/scipy/optimize/_highspy/_core.cp312-win_amd64.pyd identity differs: expected SHA-256 e6beb8321a4905c9bd0ba0eec2dfa7e27d76a01ab7d0abeab81fcce9ae6732e1 size 6709248; actual SHA-256 83281d6efb662f1a3d70c135d070dd66ec0cee47fc15ff327a50a99e39d75d9b size 6709249; re-census required`. One appended byte in a separate copy; refusal before notices are written.
- Source notices unchanged before/after: `3afe913e26ecd6fe65765943fef798450687bebf7df926d1f720da9b8e999d8c`. No frozen binary, GUI, PyInstaller build or export was run.

**Scope / remaining work.** Only the native-licences surface, notices tool,
notices tests and this report are changed. Smoke test row-count changes were
unnecessary. No source/application/frozen interface, lock, build.py, workflow,
root notices, dependency, network, git write, desktop input or protected-folder
write is involved. The seven-turn build's prior FFmpeg/fork/release work is not
reopened here. Q1 remains with the owner. STOPPED ROWS and limits above remain
for CHARC/seat disposition; the cell does not close DR-144 or authorize a draft.
Depth: `depth_input_tokens` unavailable to this fresh cell; dispatcher read due
at the turn boundary (no estimate supplied).


**Final validation.** All commands used `uv run --no-sync` in this worktree;
logs and JUnit XML are under `work/wp6.3c/turn8/`. Checker exit codes are in
`static-exits-final.txt` (all 0).

- `ruff-check-final.log`: `All checks passed!`.
- `ruff-format-final.log`: `337 files already formatted`.
- `mypy-win32-final.log`, `mypy-darwin-final.log`: each
  `Success: no issues found in 166 source files`.
- `pytest-final.log`/`.xml`, fresh `work/c63c-8-final`:
  **548 passed, 1 skipped in 151.37s (0:02:31)**, exit 0.
- `final-records.log`/`.xml`, fresh `work/c63c-8-final-records`:
  **16 passed, 304 deselected**, on the final evidence wording/manifest.
- `diff-check.log`: read-only `git diff --check`, exit 0.

The first full run, `pytest.log`/`.xml` with exactly `work/c63c-8`, was
**544 passed, 1 skipped in 150.91s**. Four final verification controls and their
fixes account for the final run's four additional passes. The provenance-only
manifest clarification during that final run was then checked with all 16 new
cases and the fresh `probe-verified` copies; no behavioral code changed after
the final run began.

| Module | Final result |
| --- | --- |
| `test_tools_package_build.py` | 126 passed |
| `test_tools_package_ffmpeg.py` | 68 passed |
| `test_tools_package_notices.py` | 320 passed |
| `test_tools_package_smoke.py` | 34 passed, 1 skipped |

The unchanged skip is `test_non_windows_containment_never_silently_skips`:
`POSIX process-group native proof belongs to WP6.5`.

Exact isolated-runner command (starts with `PYTHONPATH=scripts`, then removes
that environment variable before pytest while retaining the loaded shim;
no source environment check is bypassed):

```text
uv run --no-sync python work/wp6.3c/turn8/run_tests.py tests/test_tools_package_notices.py tests/test_tools_package_build.py tests/test_tools_package_smoke.py tests/test_tools_package_ffmpeg.py --basetemp=work/c63c-8-final --junitxml=work/wp6.3c/turn8/pytest-final.xml -q
```

The runner enforces `-p sandbox_mkdir_shim -p no:cacheprovider --timeout 300`
and excludes `test_python_m_clearwater_starts_the_shell_and_exits_0`.
No package gate, Reviewer A/B pass, fork run, real FFmpeg build, V4/GPU proof,
release/version/tag step or network fetch was attempted in this turn.

## Turn 9 - DR-144 final originals, patents and limits

**Built.** Loaded 12 embedded rows and 16 new files (11 complete pinned source
files, including seven whole rendered texts, plus five rendered excerpts).
The manifest now has 125 records and retains all 110 exact host declarations.
All prior source/host bindings remain; only the existing libyuv row's version
evidence changes to replace its resolved U-P2 patent STOP with the new row.
Pillow's original libaom row and bytes are unchanged. No notices.py schema or
renderer change is needed: version evidence carries the required SLSQP citation
and canonical-author-host evidence; the three provenance kinds are unchanged.

`work/wp6.3c/turn9/load_records.py` is the seat-reviewable, deterministic loader.
It checks the third record's 46,939 bytes / SHA-256
`437aa040aad415fc5550d6e635ee9cecc288cced3a10a3fb9db588049a2cc97c`
and census (c)'s SHA-256
`c00de8a67b4222b927f1979112626f759863395c4f5cec510d6c6ff7563637cd`.
Every copied source is checked against the record's byte count, SHA-256 and
raw Git blob SHA-1 (`blob <length>\0<bytes>`, no filters). Each excerpt also
matches its independently recorded byte count and SHA-256. Hosts' hash, size,
parent and exact path come from census (c) and must match the retained
declaration before a new binding is added. A row failure is recorded and left
out; the other rows continue. None failed. Readme revisions for libaom's
third-party rows use the upstream URLs/revision prefixes in the pinned seat
record; README.libaom files are evidence only and are not copied or rendered.

`audit_surface.py` independently checked repeated loading (all surface files
byte-identical), all retained records/declarations, all five full-blob slices,
seven whole rendered inputs and the original Pillow AOM bytes. The manifest
SHA-256 is `04c3a1215ad0e5ad4ed084c00bcf45e4c7e743d43faab962c643382b1556c894`.
The loader and audit are scratch instruments under the worktree, for seat
inspection; they are not claimed committed product files.

**Host -> component -> text table.** All hosts below have `_internal/` prefix
and `.cp312-win_amd64.pyd` suffix; source commits, tags, tag objects, complete
text hashes/sizes, raw blobs and excerpt ranges are in manifest.json.

| Host | Component | Pinned text / SPDX |
| --- | --- | --- |
| `scipy/optimize/_lbfgsb` | L-BFGS-B original licence | jacobwilliams/lbfgsb 1.0.0 `License.txt`, whole; BSD-3-Clause |
| `scipy/optimize/_lbfgsb` | L-BFGS-B authors and citation | SciPy v1.14.1 `scipy/optimize/lbfgsb_src/README` L15-38; BSD-3-Clause |
| `scipy/optimize/_minpack` | MINPACK original notice | PyBDSF v1.9.1 `src/minpack/DISCLAIMER`, whole, 2,246 bytes CRLF; Minpack |
| `scipy/optimize/_slsqplib` | SLSQP ACM release statement | SciPy v1.15.3 `scipy/optimize/slsqp/slsqp_optmz.f` L1-30; LicenseRef-SLSQP-ACM-BSD |
| `scipy/optimize/_slsqplib` | SLSQP Dieter Kraft copyright | Same pinned source, L215-215; LicenseRef-SLSQP-ACM-BSD |
| `scipy/linalg/_decomp_interpolative` | ID 0.4 original notice | SciPy v1.14.1 `scipy/linalg/src/id_dist/doc/doc.tex` L31-74; BSD-3-Clause |
| `scipy/special/_ufuncs`, `scipy/special/cython_special` | DCDFLIB original legalities | Scilab 5.5.2 `scilab/modules/statistics/src/dcdflib/README` L168-205; LicenseRef-DCDFLIB-Legalities |
| `PIL/_avif` | AOM patent licence | libaom v3.14.1 `PATENTS`, whole; LicenseRef-AOM-Patent-License-1.0 |
| `PIL/_avif` | libyuv patent grant | libyuv 644251f252a84bf8ce91ff0aca86a9b16b069ab8 `PATENTS`, whole, no final newline; LicenseRef-libyuv-Patents |
| `PIL/_avif` | fastfeat (libaom) | libaom v3.14.1 `third_party/fastfeat/LICENSE`, whole; BSD-3-Clause |
| `PIL/_avif` | vector (libaom) | libaom v3.14.1 `third_party/vector/LICENSE`, whole; MIT |
| `PIL/_avif` | x86inc (libaom) | libaom v3.14.1 `third_party/x86inc/LICENSE`, whole; ISC |

The L-BFGS-B, MINPACK and DCDFLIB rows name the authors' canonical URLs and
SHA-256s, plus archive members where applicable, in rendered version evidence.
Their third-party Git homes hold the exact bytes verified by the seat; they
are not described as authors' own repositories. SLSQP carries exactly one
attribution sentence (in the ACM row):

> D. Kraft, Algorithm 733: TOMP - Fortran modules for optimal control calculations, ACM Transactions on Mathematical Software 20(3), 1994, pp. 262-281, DOI 10.1145/192115.192124, https://www.netlib.org/toms/733.

**STOPPED ROWS / DR-144 status.** NONE this turn. No STOPPED row from turns
6-9 remains awaiting an input or ruling: turn 6's bzip2 source was supplied in
turn 7; turn 8's U-S1 / U-P2 / U-P1 texts are now loaded or explicitly converted
to limits under CHARC's rulings; U-T1 / U-N2 / U-S6 / U-S8 / U-S9 / U-H3 are
limits below. The historical turn-8 STOP table records that turn's disposition;
this status supersedes it. Existing material limits (notably COLAMD's absent
referenced licence and inferred HiGHS subcomponent terms) remain disclosed in
turn 8. DR-144's commissioned loading is complete; formal closure, independent
reviews and the acceptance register changes remain the seat/CHARC's work.
No 1.1.0 draft or N13 completion is asserted by the cell.

**Limits lines.** The manifest has no limits-statement field, and the root
THIRD_PARTY_NOTICES.md has no existing DR-144 limits paragraph. Accordingly
the following lines live here only; no root-notices section is added this
turn. Applicable carried-row caveats also appear in existing version evidence.

- L-BFGS-B: published License.txt is a BSD-3 template with unfilled placeholders
  and names no holder; Zhu, Byrd, Nocedal, Morales and the citation condition
  come from the authors' separately carried README.
- MINPACK: exact University of Chicago / Argonne acknowledgment and terms are
  carried; its third-party Git home is byte-identical to the canonical netlib
  disclaimer (R1), with original CRLF preserved.
- SLSQP: the BSD licence was named in the ACM e-mail, never written; the holder
  is ACM per the thread and Dieter Kraft per the source. No BSD text is invented.
- NNLS (`scipy/optimize/_slsqplib`): SciPy's C translation of Lawson and Hanson's
  NNLS (Solving Least Squares Problems, 1974; SIAM reprint 1995), distributed
  by netlib at https://www.netlib.org/lawson-hanson/ with no licence or copyright
  statement; no text is carried.
- LSODA (`scipy/integrate/_odepack`): SciPy's C translation of LSODA from
  ODEPACK (A. C. Hindmarsh and L. R. Petzold, Lawrence Livermore National
  Laboratory), distributed at https://www.netlib.org/odepack/ and
  https://computing.llnl.gov/projects/odepack/software with no licence or
  copyright statement; no text is carried.
- VODE / ZVODE (`scipy/integrate/_vode`): SciPy's C translations of VODE and
  ZVODE (P. N. Brown, G. D. Byrne, A. C. Hindmarsh), distributed at
  https://www.netlib.org/ode/ and
  https://computing.llnl.gov/projects/odepack/software with no licence or
  copyright statement; no text is carried.
- FITPACK (`scipy/interpolate/_fitpack`, `scipy/interpolate/_dierckx`): SciPy's
  C / C++ rewrites of Paul Dierckx's FITPACK (double-precision form by Pearu
  Peterson), distributed at https://www.netlib.org/dierckx/ with no licence or
  copyright statement; no text is carried.
- ID 0.4: the carried notice is LaTeX source, not a rendered PDF.
- DCDFLIB: the ACM Algorithms Policy condition (no copying for direct
  commercial advantage) is met on its face because Clearwater is distributed
  without fee; which DCDFLIB routines are ACM's was not traced. Per CHARC R4,
  a record-only register row at accept is COMMISSIONED to CHARC (not a release
  blocker): unchanged SciPy-wheel redistribution inherits SciPy's posture;
  reconsider if SciPy changes its posture or a holder asserts the condition.
- QUADPACK (`scipy/integrate/_quadpack`): SciPy's C rewrite of QUADPACK
  (R. Piessens, E. de Doncker-Kapenga, C. W. Ueberhuber, D. K. Kahaner),
  distributed at https://www.netlib.org/quadpack/ with no licence statement
  (netlib's permission file reads "prehistoric"); no text is carried.
- U-P1: x86inc inclusion is inferred from aom's x86-64 assembler build, not a
  Pillow build log or binary inclusion read. fastfeat/vector follow the
  encoder-on premise and direct CMake source lists. Third-party code within
  aom's own files outside third_party was not surveyed by the seat addendum.
- U-P3 replacement: aom LICENSE at v3.14.1, blob
  `fc340c37643472ced912d5acc4ec21a722505e30`, 1,316 bytes, equals Pillow's
  unchanged 1,315-byte AOM.txt plus one trailing newline. No second AOM
  copyright-licence row is added.
- U-T1 (`PIL/_imagingtk`): the Tcl/Tk header declaration carries no
  copyrightable code into the binary (CHARC ruling); Tcl/Tk's terms are already
  rendered through the Python row. No additional excerpt/text is carried.
- U-N2: libquadmath presence in either OpenBLAS DLL and the applicable text
  were not established; strings/import absence is not proof. No extra row.
- U-S6: mdspan/Kokkos header instantiation and carried host were not established;
  the fetched xsf text is only a pointer. No extra row.
- U-S8: whether Cython utility code owes a notice and which text/hosts are
  required were not established by the census. No extra row.
- U-S9: the carried Sobol direction-number data copy and applicable notice
  were not established by the native census. No extra row.
- U-H3: Ryu/fast_float static inclusion in SciPy was not established; only
  the previously proven pillow-heif libstdc++ hosts stay bound. No extra row.

The U-P1 OUT list (highway, libyuv, libwebm, googletest; no SVT-AV1 directory)
requires no additional libaom row. libyuv's separately proved libavif use
retains its copyright row and now gains its patent row. No absence of
licence statement is relabelled as a public-domain grant. These dispositions
are CHARC's commissioned limits, not new cell licence rulings.

**RED -> GREEN / verification loop.** All evidence is file-backed under
`work/wp6.3c/turn9/`.

| Suspected / confirmed / rejected / fixed | Evidence |
| --- | --- |
| Missing original terms, patent texts and host bindings: CONFIRMED, FIXED | `red.log`/`.xml`: 13 failed, 320 deselected against the pre-load manifest; `green3.log`/`.xml`: 13 passed, 320 deselected. Twelve parameter cases pin actual hosts and independently recorded text hashes/SPDX; one real synthetic-host plan/render checks every text, author-host URLs/hashes and exactly one SLSQP citation. |
| MINPACK CRLF or libyuv EOF might be normalized: REJECTED | `surface-audit.json`, new rendering test and positive probe: MINPACK 2,246 bytes with 52 CRLF intact; libyuv stored without final newline. Renderer preserves input bytes and adds only the separator LF before its closing fence for a non-newline-terminated text. |
| Regeneration or prior bindings might drift: REJECTED | `surface-audit.json`: repeated surface byte-identical, original host identities/source requirements retained, all original rows identical except resolved libyuv patent-status evidence. |
| Changed host could fall back to wheel coverage: REJECTED | Fresh negative copy below refuses the altered `_slsqplib` by exact path and both identities, before replacing notices. |

Two intermediate rendering runs exposed fixture assumptions, not product
defects: the synthetic surface helper intentionally deletes production texts
(the test now copies only its selected real inputs), and the published MINPACK
acknowledgment wraps across CRLF (the literal assertion now reflects its exact
bytes). `green.log` and `green2.log` retain those failures; `green3` is the first
complete focused GREEN. No product-code change was needed. The final source,
host, obligation, retention and output checks found no new in-envelope issue.
Reviewer A is dispatcher-run after this yield; no review round is claimed.

**Final validation.** All commands use `uv run --no-sync`; all exit codes are 0
(`static-exits.json`, `pytest-exit.txt`).

- `ruff-check.log`: `All checks passed!`.
- `ruff-format.log`: `337 files already formatted`.
- `mypy-win32.log`, `mypy-darwin.log`: each
  `Success: no issues found in 166 source files`.
- `pytest.log`/`.xml`, fresh `work/c63c-9`: **561 passed, 1 skipped**.

| Module | Final result |
| --- | --- |
| `test_tools_package_build.py` | 126 passed |
| `test_tools_package_ffmpeg.py` | 68 passed |
| `test_tools_package_notices.py` | 333 passed |
| `test_tools_package_smoke.py` | 34 passed, 1 skipped |

The unchanged skip is `test_non_windows_containment_never_silently_skips`:
`POSIX process-group native proof belongs to WP6.5`. The isolated runner
launches with `PYTHONPATH=scripts`, removes that environment variable before
pytest, loads `sandbox_mkdir_shim`, disables cacheprovider, sets timeout 300,
and excludes `test_python_m_clearwater_starts_the_shell_and_exits_0`.
The smoke source-entry child was inspected before execution: disposable
APPDATA/LOCALAPPDATA/XDG roots, blocked PySide6/shiboken6 imports, GUI/worker
stubs and 15-second timeout. No product entry point runs in the new tests.

```text
uv run --no-sync python work/wp6.3c/turn9/run_tests.py tests/test_tools_package_notices.py tests/test_tools_package_build.py tests/test_tools_package_smoke.py tests/test_tools_package_ffmpeg.py --basetemp=work/c63c-9 --junitxml=work/wp6.3c/turn9/pytest.xml -q -rs
```

**Fresh copy probes.** `probe.py`, `probe.log` and `probe-results.json`, under
`work/c63c-9/probe-positive/` and `probe-negative/`, copy the commissioned
seat folder; no original is written and no executable is run.

- POSITIVE: **140 rows, 1536 entries, 115 embedded rows**;
  all 110 declared hosts present and matching, all twelve new texts occur once.
  Notices SHA-256 `e06211214c7edda2c38c3691d4710e764e677f680e706ef10195566372f257a7`.
- Embedded rows by parent package: numpy: 1; pillow: 11; pillow-heif: 5; pyside6-essentials: 47; python: 13; scipy: 39; shiboken6: 1. Counts overlap for shared rows.
- MINPACK's complete 2,246-byte text renders with all 52 CRLF intact.
- NEGATIVE: one byte appended to a separate copy's
  `_internal/scipy/optimize/_slsqplib.cp312-win_amd64.pyd` causes:
  `notices: embedded _internal/scipy/optimize/_slsqplib.cp312-win_amd64.pyd identity differs: expected SHA-256 a108ab846bccb35169dc86b37c14e25a2ec4162b0235ea5282ba28ea057ff011 size 48640; actual SHA-256 8a8a6c62165f8d623422d377c3fff6f007cd2c5d930f834ffd25b9bcfabfb7d6 size 48641; re-census required`. The copied old notices remain untouched on refusal.
- Original notices SHA-256 before/after: `3afe913e26ecd6fe65765943fef798450687bebf7df926d1f720da9b8e999d8c` (unchanged).

**Scope / remaining work.** Changed only the native-licences manifest/texts,
notices tests and this report; no smoke row-count update was needed. No
notices.py change, dependency, frozen interface, lock, build.py, workflow,
root notices, external fetch, Git write, real build, frozen/GUI run, Docker,
synthetic desktop input, footage/profile/source-build/evidence write, push,
tag, GitHub action or mailbox post was performed. This turn bundles exactly
the commissioned final DR-144 rows and limits. Q1, the fork-dependent re-pin,
remaining package/release work, independent reviews and gate remain
COMMISSIONED to the subsequent dispatches/seat. CHARC's R4 register record at
accept remains COMMISSIONED to CHARC. No per-row input/ruling is left undone.
Depth: `depth_input_tokens` is unavailable to this fresh cell; dispatcher read
due at the turn boundary, with no estimate supplied.


## Turn 10 - Shipped DR-144 limits statements

**Built.** Added optional `limits` to the native-licences manifest and its
fail-closed loader/planner/renderer contract. An entry has exactly `component`,
`hosts`, `statement`; unknown top-level/entry keys are refused. Component and
statement must be nonempty strings without leading/trailing whitespace; component
names are unique. Hosts must be a nonempty, sorted, case-insensitively
duplicate-free list of exact relative paths already declared in `embedded_hosts`.
No provenance kind, text-file rule, source pin, host identity or component row
was changed. `NoticeLimit` carries the selected statements in `NoticePlan`;
the new plan field defaults to an empty tuple for existing callers.

**Absent-host decision.** Use only hosts returned by the EXISTING
`_embedded_claims` census preflight, never an independent weaker identity check.
A carried host with different bytes refuses by name with expected/actual hash
and size and `re-census required`, before package coverage or notice publication.
Turn-10 absence decision (superseded by turn 11 below): an absent declared host contributes no embedded claim and no limits host;
an entry whose hosts are ALL legitimately absent is omitted, matching embedded
rows' absence rule. Partial carriage renders only actual carried paths, sorted.
Both a text row and a limits entry for one component render independently.

**Production data.** The deterministic seat-reviewable loader is
`work/wp6.3c/turn10/load_limits.py`. It pins the turn-9 manifest SHA-256,
adds ONLY the sorted `limits` list and asserts every other manifest value is
unchanged. Repeated loading yields identical bytes: manifest SHA-256
`a53e8573a94489a07505d14d170baa0c1e298aee21b871ce19147a7cbf3e183b`.
All 17 commissioned entries loaded; STOPPED ENTRIES: NONE. The effective
shipped count is **17**, including COLAMD and BASICLU / IPX / cuPDLP-C;
any earlier dispatch shorthand of "16 limits" is superseded. No such literal
count appeared in the prior turn-9 report, so no historical count was replaced.
The seven mdspan host paths are turn 8's exact xsf users. The supplied census
does not establish the exact Cython build subset: the expressly allowed
fallback binds all 82 declared SciPy `.pyd`, with the statement naming
"SciPy extensions built from Cython sources". U-H3 also binds all 82 without
asserting inclusion. There is no new host declaration or licence text.

**PROCESS.** Turn 9's first launch was stopped by the seat within a minute: the seat record was re-hashed by its producing subagent after the dispatch pinned the earlier hash; rule adopted: a dispatch pins a seat record's hash only after the producing subagent has returned.

**RED -> GREEN.** All logs/XML and scratch instruments are under
`work/wp6.3c/turn10/`.

- `red.log` / `.xml`, fresh `work/c63c-10-red`: **24 failed, 1 passed,
  333 deselected** before the schema/renderer/data changes. The existing
  top-level unknown-key control is the passing preservation check. The old
  strict schema already refuses `limits`, so new negative cases require
  limits-specific diagnostics rather than claiming the old code accepted
  malformed declarations. Positive tests expose the unsupported field and
  production test exposes the absent 17 entries.
- `green.log` / `.xml`, fresh `work/c63c-10-green`: **25 passed,
  333 deselected**. Covers exact schema/types/unknown keys, undeclared hosts,
  duplicate components/hosts, whitespace, unsafe/unsorted paths, absent/empty
  lists, both text and limits, deterministic text/order, all-absent/partial/full
  host carriage, altered-host refusal and production host declarations.
- No source/product entry point was added. The existing smoke source-entry
  child was inspected before the full run: disposable APPDATA/LOCALAPPDATA/XDG
  roots, blocked PySide6/shiboken6 imports, GUI and worker stubs, timeout 15 s.

**Validation.** `validation-exits.json`: all five exit codes 0.

- `ruff-check.log`: `All checks passed!`.
- `ruff-format.log`: `337 files already formatted`.
- `mypy-win32.log`, `mypy-darwin.log`: each
  `Success: no issues found in 166 source files`.
- `pytest.log` / `.xml`, fresh `work/c63c-10`: **586 passed,
  1 skipped**.

| Module | Final result |
| --- | --- |
| `test_tools_package_build.py` | 126 passed |
| `test_tools_package_ffmpeg.py` | 68 passed |
| `test_tools_package_notices.py` | 358 passed |
| `test_tools_package_smoke.py` | 34 passed, 1 skipped |

The single unchanged skip is
`test_non_windows_containment_never_silently_skips`:
`POSIX process-group native proof belongs to WP6.5`.
Exact isolated runner (launched with `PYTHONPATH=scripts`, removed before
pytest while retaining the shim on `sys.path`):

```text
uv run --no-sync python work/wp6.3c/turn10/run_tests.py tests/test_tools_package_notices.py tests/test_tools_package_build.py tests/test_tools_package_smoke.py tests/test_tools_package_ffmpeg.py --basetemp=work/c63c-10 --junitxml=work/wp6.3c/turn10/pytest.xml -q -rs
```

It enforces `-p sandbox_mkdir_shim -p no:cacheprovider --timeout 300` and
`-k 'not test_python_m_clearwater_starts_the_shell_and_exits_0'`. No source
environment refusal is bypassed. `diff-check.log`: read-only `git diff --check`,
exit 0.

**Fresh-copy probes.** `probe.py`, `probe.log`, `probe-results.json` use
fresh `work/c63c-10/probes/positive/` and `negative/` copies of the commissioned
stage-1d folder. No copied executable or native is executed.

- POSITIVE: **140 rows, 1536 entries,
  17 limits entries**; all 110 declared hosts measured
  and matching. Notices SHA-256 `e9aec25af81312d48221b59abbc42e8778d575c6d3ad6ea891e65ecd5db8df22`.
- Section: zero-based byte offset **242907**,
  length **16000** (heading through separator LF,
  ending immediately before `## Full licence texts and provenance`);
  SHA-256 `45526f42af10824333029d0a4818ef6edb008b8e0c285c9c60206c8c46fc4b1b`.
- ABSENT and EMPTY lists each render byte-identically to turn 9's
  `e06211214c7edda2c38c3691d4710e764e677f680e706ef10195566372f257a7`.
  This uses a separate surface copy; no production manifest is changed by
  the probe. Repeated planning/rendering of the new output is byte-identical.
- NEGATIVE: appending one byte to the second copy's limits-only algorithm
  host (which also carries its existing runtime rows) yields:
  `notices: embedded _internal/scipy/integrate/_quadpack.cp312-win_amd64.pyd identity differs: expected SHA-256 03e0ed70dc1910b227f32676d4f4c8621f4b82ab45429e6f167dc582c4c67dd8 size 142336; actual SHA-256 74ef347aa381ccc27b409fb3ce657b965e24b10c6e5119c14148ad35898aae68 size 142337; re-census required`.
  Refusal preserves the copy's previous notices.
- Original seat-folder notices before/after:
  `3afe913e26ecd6fe65765943fef798450687bebf7df926d1f720da9b8e999d8c` (unchanged).

**Verification loop.**

| Suspected / disposition | Independent confirmation / result |
| --- | --- |
| Missing shipped limits: CONFIRMED, FIXED | RED positives and absent production list; GREEN controls plus fresh-copy section with all 17 verbatim statements. |
| Limits might weaken census or infer absent carriage: REJECTED | Existing preflight is the only carried-host source; altered-byte control and separate real `_quadpack` refusal; all-absent/partial/full cases pass. |
| Optional field might alter old notices: REJECTED | Both fresh-copy empty/absent outputs equal the independently supplied turn-9 digest and each other byte-for-byte. |
| Loading might change prior census/source rows or ordering: REJECTED | Loader asserts full prior manifest equality outside `limits`; repeat gives the same manifest digest; sorted-render control and all old tests pass. |

The final owned-diff/requirements pass found nothing new. No review round is
claimed; Reviewer A is the dispatcher-run pass after this yield.

**Rendered section (complete, verbatim).** The following is the exact 16,000-byte
section from the positive probe; its copy is `rendered-section.txt`.

```text
## Components with no carried licence text, and limits

Component: BASICLU / IPX / cuPDLP-C (U-S5)
Hosts: file:_internal/scipy/optimize/_highspy/_core.cp312-win_amd64.pyd, file:_internal/scipy/optimize/_highspy/_highs_options.cp312-win_amd64.pyd
These components are built in HiGHS; repository-wide MIT coverage is inferred, not a separately verified upstream licence grant. BASICLU's actual header is retained.

Component: COLAMD (U-S4)
Hosts: file:_internal/scipy/sparse/linalg/_dsolve/_superlu.cp312-win_amd64.pyd
The copyright notice is carried; its referenced License.txt is absent from the pinned tree. No SPDX id is substituted for that missing document.

Component: Cython-generated code (U-S8)
Hosts: file:_internal/scipy/_cyutility.cp312-win_amd64.pyd, file:_internal/scipy/_lib/_ccallback_c.cp312-win_amd64.pyd, file:_internal/scipy/_lib/_fpumode.cp312-win_amd64.pyd, file:_internal/scipy/_lib/_uarray/_uarray.cp312-win_amd64.pyd, file:_internal/scipy/_lib/messagestream.cp312-win_amd64.pyd, file:_internal/scipy/fft/_duccfft/pyduccfft.cp312-win_amd64.pyd, file:_internal/scipy/integrate/_dop.cp312-win_amd64.pyd, file:_internal/scipy/integrate/_odepack.cp312-win_amd64.pyd, file:_internal/scipy/integrate/_quadpack.cp312-win_amd64.pyd, file:_internal/scipy/integrate/_vode.cp312-win_amd64.pyd, file:_internal/scipy/interpolate/_dierckx.cp312-win_amd64.pyd, file:_internal/scipy/interpolate/_fitpack.cp312-win_amd64.pyd, file:_internal/scipy/interpolate/_interpnd.cp312-win_amd64.pyd, file:_internal/scipy/interpolate/_ppoly.cp312-win_amd64.pyd, file:_internal/scipy/interpolate/_rbfinterp_pythran.cp312-win_amd64.pyd, file:_internal/scipy/interpolate/_rgi_cython.cp312-win_amd64.pyd, file:_internal/scipy/linalg/_batched_linalg.cp312-win_amd64.pyd, file:_internal/scipy/linalg/_cythonized_array_utils.cp312-win_amd64.pyd, file:_internal/scipy/linalg/_decomp_interpolative.cp312-win_amd64.pyd, file:_internal/scipy/linalg/_decomp_update.cp312-win_amd64.pyd, file:_internal/scipy/linalg/_fblas.cp312-win_amd64.pyd, file:_internal/scipy/linalg/_flapack.cp312-win_amd64.pyd, file:_internal/scipy/linalg/_internal_matfuncs.cp312-win_amd64.pyd, file:_internal/scipy/linalg/_linalg_pythran.cp312-win_amd64.pyd, file:_internal/scipy/linalg/_matfuncs_sqrtm_triu.cp312-win_amd64.pyd, file:_internal/scipy/linalg/_solve_toeplitz.cp312-win_amd64.pyd, file:_internal/scipy/linalg/cython_blas.cp312-win_amd64.pyd, file:_internal/scipy/linalg/cython_lapack.cp312-win_amd64.pyd, file:_internal/scipy/ndimage/_nd_image.cp312-win_amd64.pyd, file:_internal/scipy/ndimage/_ni_label.cp312-win_amd64.pyd, file:_internal/scipy/ndimage/_rank_filter_1d.cp312-win_amd64.pyd, file:_internal/scipy/optimize/_bglu_dense.cp312-win_amd64.pyd, file:_internal/scipy/optimize/_direct.cp312-win_amd64.pyd, file:_internal/scipy/optimize/_group_columns.cp312-win_amd64.pyd, file:_internal/scipy/optimize/_highspy/_core.cp312-win_amd64.pyd, file:_internal/scipy/optimize/_highspy/_highs_options.cp312-win_amd64.pyd, file:_internal/scipy/optimize/_lbfgsb.cp312-win_amd64.pyd, file:_internal/scipy/optimize/_lsap.cp312-win_amd64.pyd, file:_internal/scipy/optimize/_lsq/givens_elimination.cp312-win_amd64.pyd, file:_internal/scipy/optimize/_minpack.cp312-win_amd64.pyd, file:_internal/scipy/optimize/_moduleTNC.cp312-win_amd64.pyd, file:_internal/scipy/optimize/_pava_pybind.cp312-win_amd64.pyd, file:_internal/scipy/optimize/_slsqplib.cp312-win_amd64.pyd, file:_internal/scipy/optimize/_trlib/_trlib.cp312-win_amd64.pyd, file:_internal/scipy/optimize/_zeros.cp312-win_amd64.pyd, file:_internal/scipy/sparse/_csparsetools.cp312-win_amd64.pyd, file:_internal/scipy/sparse/_sparsetools.cp312-win_amd64.pyd, file:_internal/scipy/sparse/csgraph/_flow.cp312-win_amd64.pyd, file:_internal/scipy/sparse/csgraph/_matching.cp312-win_amd64.pyd, file:_internal/scipy/sparse/csgraph/_min_spanning_tree.cp312-win_amd64.pyd, file:_internal/scipy/sparse/csgraph/_reordering.cp312-win_amd64.pyd, file:_internal/scipy/sparse/csgraph/_shortest_path.cp312-win_amd64.pyd, file:_internal/scipy/sparse/csgraph/_tools.cp312-win_amd64.pyd, file:_internal/scipy/sparse/csgraph/_traversal.cp312-win_amd64.pyd, file:_internal/scipy/sparse/linalg/_dsolve/_superlu.cp312-win_amd64.pyd, file:_internal/scipy/sparse/linalg/_eigen/arpack/_arpacklib.cp312-win_amd64.pyd, file:_internal/scipy/sparse/linalg/_propack.cp312-win_amd64.pyd, file:_internal/scipy/spatial/_ckdtree.cp312-win_amd64.pyd, file:_internal/scipy/spatial/_distance_pybind.cp312-win_amd64.pyd, file:_internal/scipy/spatial/_distance_wrap.cp312-win_amd64.pyd, file:_internal/scipy/spatial/_hausdorff.cp312-win_amd64.pyd, file:_internal/scipy/spatial/_qhull.cp312-win_amd64.pyd, file:_internal/scipy/spatial/_voronoi.cp312-win_amd64.pyd, file:_internal/scipy/spatial/transform/_rigid_transform_cy.cp312-win_amd64.pyd, file:_internal/scipy/spatial/transform/_rotation_cy.cp312-win_amd64.pyd, file:_internal/scipy/special/_comb.cp312-win_amd64.pyd, file:_internal/scipy/special/_ellip_harm_2.cp312-win_amd64.pyd, file:_internal/scipy/special/_gufuncs.cp312-win_amd64.pyd, file:_internal/scipy/special/_specfun.cp312-win_amd64.pyd, file:_internal/scipy/special/_special_ufuncs.cp312-win_amd64.pyd, file:_internal/scipy/special/_ufuncs.cp312-win_amd64.pyd, file:_internal/scipy/special/_ufuncs_cxx.cp312-win_amd64.pyd, file:_internal/scipy/special/cython_special.cp312-win_amd64.pyd, file:_internal/scipy/stats/_ansari_swilk_statistics.cp312-win_amd64.pyd, file:_internal/scipy/stats/_biasedurn.cp312-win_amd64.pyd, file:_internal/scipy/stats/_levy_stable/levyst.cp312-win_amd64.pyd, file:_internal/scipy/stats/_qmc_cy.cp312-win_amd64.pyd, file:_internal/scipy/stats/_qmvnt_cy.cp312-win_amd64.pyd, file:_internal/scipy/stats/_rcont/rcont.cp312-win_amd64.pyd, file:_internal/scipy/stats/_sobol.cp312-win_amd64.pyd, file:_internal/scipy/stats/_stats.cp312-win_amd64.pyd, file:_internal/scipy/stats/_stats_pythran.cp312-win_amd64.pyd
For SciPy extensions built from Cython sources, whether Cython utility code owes a notice and which text or hosts are required were not established by the census. This limits entry conservatively binds all 82 SciPy extensions; no extra licence text is carried.

Component: DCDFLIB
Hosts: file:_internal/scipy/special/_ufuncs.cp312-win_amd64.pyd, file:_internal/scipy/special/cython_special.cp312-win_amd64.pyd
The ACM Algorithms Policy condition (no copying for direct commercial advantage) is met on its face because Clearwater is distributed without fee; which DCDFLIB routines are ACM's was not traced.

Component: FITPACK
Hosts: file:_internal/scipy/interpolate/_dierckx.cp312-win_amd64.pyd, file:_internal/scipy/interpolate/_fitpack.cp312-win_amd64.pyd
SciPy's C / C++ rewrites of Paul Dierckx's FITPACK (double-precision form by Pearu Peterson) are distributed at https://www.netlib.org/dierckx/ with no licence or copyright statement; no text is carried.

Component: L-BFGS-B
Hosts: file:_internal/scipy/optimize/_lbfgsb.cp312-win_amd64.pyd
The published License.txt is a BSD-3 template with unfilled placeholders and names no holder; Zhu, Byrd, Nocedal, Morales and the citation condition come from the authors' separately carried README.

Component: LSODA (ODEPACK)
Hosts: file:_internal/scipy/integrate/_odepack.cp312-win_amd64.pyd
SciPy's C translation of LSODA from ODEPACK (A. C. Hindmarsh and L. R. Petzold, Lawrence Livermore National Laboratory) is distributed at https://www.netlib.org/odepack/ and https://computing.llnl.gov/projects/odepack/software with no licence or copyright statement; no text is carried.

Component: NNLS
Hosts: file:_internal/scipy/optimize/_slsqplib.cp312-win_amd64.pyd
SciPy's C translation of Lawson and Hanson's NNLS (Solving Least Squares Problems, 1974; SIAM reprint 1995) is distributed by netlib at https://www.netlib.org/lawson-hanson/ with no licence or copyright statement; no text is carried.

Component: QUADPACK
Hosts: file:_internal/scipy/integrate/_quadpack.cp312-win_amd64.pyd
SciPy's C rewrite of QUADPACK (R. Piessens, E. de Doncker-Kapenga, C. W. Ueberhuber, D. K. Kahaner) is distributed at https://www.netlib.org/quadpack/ with no licence statement (netlib's permission file reads "prehistoric"); no text is carried.

Component: Ryu / fast_float in SciPy (U-H3)
Hosts: file:_internal/scipy/_cyutility.cp312-win_amd64.pyd, file:_internal/scipy/_lib/_ccallback_c.cp312-win_amd64.pyd, file:_internal/scipy/_lib/_fpumode.cp312-win_amd64.pyd, file:_internal/scipy/_lib/_uarray/_uarray.cp312-win_amd64.pyd, file:_internal/scipy/_lib/messagestream.cp312-win_amd64.pyd, file:_internal/scipy/fft/_duccfft/pyduccfft.cp312-win_amd64.pyd, file:_internal/scipy/integrate/_dop.cp312-win_amd64.pyd, file:_internal/scipy/integrate/_odepack.cp312-win_amd64.pyd, file:_internal/scipy/integrate/_quadpack.cp312-win_amd64.pyd, file:_internal/scipy/integrate/_vode.cp312-win_amd64.pyd, file:_internal/scipy/interpolate/_dierckx.cp312-win_amd64.pyd, file:_internal/scipy/interpolate/_fitpack.cp312-win_amd64.pyd, file:_internal/scipy/interpolate/_interpnd.cp312-win_amd64.pyd, file:_internal/scipy/interpolate/_ppoly.cp312-win_amd64.pyd, file:_internal/scipy/interpolate/_rbfinterp_pythran.cp312-win_amd64.pyd, file:_internal/scipy/interpolate/_rgi_cython.cp312-win_amd64.pyd, file:_internal/scipy/linalg/_batched_linalg.cp312-win_amd64.pyd, file:_internal/scipy/linalg/_cythonized_array_utils.cp312-win_amd64.pyd, file:_internal/scipy/linalg/_decomp_interpolative.cp312-win_amd64.pyd, file:_internal/scipy/linalg/_decomp_update.cp312-win_amd64.pyd, file:_internal/scipy/linalg/_fblas.cp312-win_amd64.pyd, file:_internal/scipy/linalg/_flapack.cp312-win_amd64.pyd, file:_internal/scipy/linalg/_internal_matfuncs.cp312-win_amd64.pyd, file:_internal/scipy/linalg/_linalg_pythran.cp312-win_amd64.pyd, file:_internal/scipy/linalg/_matfuncs_sqrtm_triu.cp312-win_amd64.pyd, file:_internal/scipy/linalg/_solve_toeplitz.cp312-win_amd64.pyd, file:_internal/scipy/linalg/cython_blas.cp312-win_amd64.pyd, file:_internal/scipy/linalg/cython_lapack.cp312-win_amd64.pyd, file:_internal/scipy/ndimage/_nd_image.cp312-win_amd64.pyd, file:_internal/scipy/ndimage/_ni_label.cp312-win_amd64.pyd, file:_internal/scipy/ndimage/_rank_filter_1d.cp312-win_amd64.pyd, file:_internal/scipy/optimize/_bglu_dense.cp312-win_amd64.pyd, file:_internal/scipy/optimize/_direct.cp312-win_amd64.pyd, file:_internal/scipy/optimize/_group_columns.cp312-win_amd64.pyd, file:_internal/scipy/optimize/_highspy/_core.cp312-win_amd64.pyd, file:_internal/scipy/optimize/_highspy/_highs_options.cp312-win_amd64.pyd, file:_internal/scipy/optimize/_lbfgsb.cp312-win_amd64.pyd, file:_internal/scipy/optimize/_lsap.cp312-win_amd64.pyd, file:_internal/scipy/optimize/_lsq/givens_elimination.cp312-win_amd64.pyd, file:_internal/scipy/optimize/_minpack.cp312-win_amd64.pyd, file:_internal/scipy/optimize/_moduleTNC.cp312-win_amd64.pyd, file:_internal/scipy/optimize/_pava_pybind.cp312-win_amd64.pyd, file:_internal/scipy/optimize/_slsqplib.cp312-win_amd64.pyd, file:_internal/scipy/optimize/_trlib/_trlib.cp312-win_amd64.pyd, file:_internal/scipy/optimize/_zeros.cp312-win_amd64.pyd, file:_internal/scipy/sparse/_csparsetools.cp312-win_amd64.pyd, file:_internal/scipy/sparse/_sparsetools.cp312-win_amd64.pyd, file:_internal/scipy/sparse/csgraph/_flow.cp312-win_amd64.pyd, file:_internal/scipy/sparse/csgraph/_matching.cp312-win_amd64.pyd, file:_internal/scipy/sparse/csgraph/_min_spanning_tree.cp312-win_amd64.pyd, file:_internal/scipy/sparse/csgraph/_reordering.cp312-win_amd64.pyd, file:_internal/scipy/sparse/csgraph/_shortest_path.cp312-win_amd64.pyd, file:_internal/scipy/sparse/csgraph/_tools.cp312-win_amd64.pyd, file:_internal/scipy/sparse/csgraph/_traversal.cp312-win_amd64.pyd, file:_internal/scipy/sparse/linalg/_dsolve/_superlu.cp312-win_amd64.pyd, file:_internal/scipy/sparse/linalg/_eigen/arpack/_arpacklib.cp312-win_amd64.pyd, file:_internal/scipy/sparse/linalg/_propack.cp312-win_amd64.pyd, file:_internal/scipy/spatial/_ckdtree.cp312-win_amd64.pyd, file:_internal/scipy/spatial/_distance_pybind.cp312-win_amd64.pyd, file:_internal/scipy/spatial/_distance_wrap.cp312-win_amd64.pyd, file:_internal/scipy/spatial/_hausdorff.cp312-win_amd64.pyd, file:_internal/scipy/spatial/_qhull.cp312-win_amd64.pyd, file:_internal/scipy/spatial/_voronoi.cp312-win_amd64.pyd, file:_internal/scipy/spatial/transform/_rigid_transform_cy.cp312-win_amd64.pyd, file:_internal/scipy/spatial/transform/_rotation_cy.cp312-win_amd64.pyd, file:_internal/scipy/special/_comb.cp312-win_amd64.pyd, file:_internal/scipy/special/_ellip_harm_2.cp312-win_amd64.pyd, file:_internal/scipy/special/_gufuncs.cp312-win_amd64.pyd, file:_internal/scipy/special/_specfun.cp312-win_amd64.pyd, file:_internal/scipy/special/_special_ufuncs.cp312-win_amd64.pyd, file:_internal/scipy/special/_ufuncs.cp312-win_amd64.pyd, file:_internal/scipy/special/_ufuncs_cxx.cp312-win_amd64.pyd, file:_internal/scipy/special/cython_special.cp312-win_amd64.pyd, file:_internal/scipy/stats/_ansari_swilk_statistics.cp312-win_amd64.pyd, file:_internal/scipy/stats/_biasedurn.cp312-win_amd64.pyd, file:_internal/scipy/stats/_levy_stable/levyst.cp312-win_amd64.pyd, file:_internal/scipy/stats/_qmc_cy.cp312-win_amd64.pyd, file:_internal/scipy/stats/_qmvnt_cy.cp312-win_amd64.pyd, file:_internal/scipy/stats/_rcont/rcont.cp312-win_amd64.pyd, file:_internal/scipy/stats/_sobol.cp312-win_amd64.pyd, file:_internal/scipy/stats/_stats.cp312-win_amd64.pyd, file:_internal/scipy/stats/_stats_pythran.cp312-win_amd64.pyd
Static inclusion in SciPy was not established; this limits entry conservatively binds all 82 SciPy extensions and does not assert presence. Only the previously proven pillow-heif libstdc++ hosts carry their licence rows.

Component: SLSQP
Hosts: file:_internal/scipy/optimize/_slsqplib.cp312-win_amd64.pyd
The BSD licence was named in the ACM e-mail, never written; the holder is ACM per the thread and Dieter Kraft per the source. No BSD text is invented.

Component: Sobol direction numbers (U-S9)
Hosts: file:_internal/scipy/stats/_sobol.cp312-win_amd64.pyd
The carried Sobol direction-number data copy and applicable notice were not established by the native census. No extra licence text is carried.

Component: Tcl/Tk header (U-T1)
Hosts: file:_internal/PIL/_imagingtk.cp312-win_amd64.pyd
The Tcl/Tk header declaration carries no copyrightable code into the binary; Tcl/Tk terms are already rendered through the Python row. No additional excerpt or text is carried.

Component: VODE / ZVODE
Hosts: file:_internal/scipy/integrate/_vode.cp312-win_amd64.pyd
SciPy's C translations of VODE and ZVODE (P. N. Brown, G. D. Byrne, A. C. Hindmarsh) are distributed at https://www.netlib.org/ode/ and https://computing.llnl.gov/projects/odepack/software with no licence or copyright statement; no text is carried.

Component: libquadmath (U-N2)
Hosts: file:_internal/numpy.libs/libscipy_openblas64_-ed4f167a5330424524f45258e7ca2c8d.dll, file:_internal/scipy.libs/libscipy_openblas-197ee2fc9b4d071f7e048078cac74115.dll
Presence in either OpenBLAS DLL and the applicable text were not established; strings or import absence is not proof. No extra licence text is carried.

Component: mdspan (Kokkos, U-S6)
Hosts: file:_internal/scipy/special/_ellip_harm_2.cp312-win_amd64.pyd, file:_internal/scipy/special/_gufuncs.cp312-win_amd64.pyd, file:_internal/scipy/special/_specfun.cp312-win_amd64.pyd, file:_internal/scipy/special/_special_ufuncs.cp312-win_amd64.pyd, file:_internal/scipy/special/_ufuncs.cp312-win_amd64.pyd, file:_internal/scipy/special/_ufuncs_cxx.cp312-win_amd64.pyd, file:_internal/scipy/special/cython_special.cp312-win_amd64.pyd
Header instantiation and carried host were not established; the fetched xsf text is only a pointer. The upstream terms are Apache-2.0 WITH LLVM-exception; no extra licence text is carried.

Component: x86inc (libaom)
Hosts: file:_internal/PIL/_avif.cp312-win_amd64.pyd
Inclusion is inferred from aom's x86-64 assembler build, not a Pillow build log or binary inclusion read.

```

**Scope / handoff.** Only notices.py's schema/planner/renderer, the manifest's
`limits` list, notices tests and this report changed. Smoke row-count changes
were unnecessary. STOPPED ENTRIES: NONE; no commissioned turn-10 item remains
undone. No dependency, frozen interface, FFmpeg lock, build.py, release workflow,
root notices or other row/text changed. No network, Git write, real PyInstaller
build, frozen/GUI launch, Docker, synthetic desktop input, protected-folder
write, GitHub action, push, tag or mailbox post occurred. Q1, fork/asset/re-pin,
remaining package/release work, independent reviews and gates remain with
later dispatches/seat. The cell does not close DR-144 or assert N13/release
completion. One logical change this turn. `depth_input_tokens` is unavailable
to the fresh cell; dispatcher read due at the boundary, no estimate supplied.

## Turn 11 - Reviewer A round 1 remediation

**Status: commissioned fixes implemented; YIELD with a scope finding.** All
eleven FIX dispositions below are implemented. Static checks and the 64-case
focused selection pass. The prescribed five-module selection is NOT green:
15 smoke-fixture setup errors require a fixture edit outside this turn's grant;
five real-Git cases fail at the sandbox's local fixture push and need the seat.
Neither a passing package gate nor Reviewer A convergence is claimed.

**Adjudication and RED -> GREEN.** Logs, XML and instruments in this section
are under `work/wp6.3c/turn11/`; all basetemps are fresh. F3/F5 remain with CHARC,
as dispatched, and the fork patch is unchanged.

| Finding / severity | Disposition and implementation | RED evidence -> GREEN evidence |
| --- | --- | --- |
| F1 MAJOR | FIXED. Strict `parent_version` on every host; compare against the carried parent's installed version (and the lock/audit's existing version checks). Python binds CPython version plus the PBS `BUILD` release. A missing declared host with its parent carried refuses by host and parent. Every carried file matching a declared SHA-256/size at an undeclared path refuses as moved, including an additional copy with the original still present. | Final behavior baseline: five failures (rename, move, duplicate, missing host, legitimate parent upgrade). Current focused selection passes all five and five strict-version schema cases. Fresh production rename/move probes refuse below. |
| F2 minor | FIXED. A `LicenceInput.reference` marker distinguishes a reused input. The renderer checks each input as before and retains the original non-reference heading/provenance while preserving the shared anchor/order. | Four baseline heading failures -> four passes, including GCC/SciPy audit, MinGW/pillow-heif and libsharpyuv-libyuv/Pillow shapes. Exactly four production blocks change labels; listed below. |
| F3 minor | HELD by CHARC; not commissioned this turn. | No patch edit or new claim. |
| F4 minor | FIXED. A `--zip` invocation removes its exact zip and sidecar at entry, before environment/scan/build work; resolved targets must stay inside `--out`. | Four stale-output build cases fail before the scan on the old module -> all pass, including subsequent notices, smoke and timestamp refusals. |
| F5 advisory | HELD by CHARC; not commissioned this turn. | No fork permissions edit. |
| F6 advisory | FIXED. Physical-tree traversal refuses a junction/symlink before descending, every member resolving outside the root, and special files. The writer and snapshots use that traversal. | Real `_winapi.CreateJunction` control packs outside bytes on the old writer -> current writer refuses and preserves the outside file. The case ran on Windows; no junction skip. |
| F7 advisory | FIXED. Snapshot sorted relative paths, SHA-256 and sizes after notices immediately before smoke; compare after smoke and before publication, naming the first added/removed/changed file. | Three corrected-fixture baseline builds return success after smoke mutates covered files -> all three refuse now. The changed-file case keeps the same size, proving hashing is required. |
| F8 advisory | FIXED in the gate step only. Each named Git refusal appends the last nonempty stderr line, limited to its final 400 characters; byte stderr on timeout is decoded. Timeout structure/argv are unchanged. | Eight exit/timeout diagnostic assertions and one long-line assertion fail -> all nine pass; the four no-stderr launch-error controls also pass. |
| F9 advisory | DECLINED as ruled: the full tag peel is already checked against `GITHUB_SHA`. | No extra nested-tag restriction. |
| F10 advisory | FIXED. Independent host source pins also include `text_file`, `text_sha256`, `text_size_bytes`. Re-derived all 175 local-text host source references; references to already-carried material retain their separately pinned input identities. | A self-consistent component-only whole-text swap is accepted by the behavior baseline -> current planner refuses by host/component/source pin. |
| F11 advisory | FIXED. Excerpt line splitting uses LF only and preserves every byte, including lone CR and a missing final LF. The interpreter-text excerpt uses the same primitive. | A valid lone-CR-containing line is rejected by the old splitter -> current plan/render accepts it. All 34 production slices independently match LF numbering. |
| F12 advisory | FIXED. README says FFmpeg is extracted from the verified archive. | `manifest-audit.log` verifies HEAD's copy wording and the current extraction wording. |
| F13 advisory | FIXED. Limits component/statement values refuse CR, LF, all C0/C1 controls and Unicode line/paragraph separators. | Fourteen control-character baseline cases accept injected strings -> all fourteen refuse now. |
| F14 advisory | FIXED, test-only. Replace the vacuous shared byte-change control with a textless undeclared-host binding control that `_embedded_claims` cannot catch. | `limits-mutant.log`: disabling only `_limit_declarations` causes the new test to fail (`DID NOT RAISE`); the unmutated case passes in `focused-final.log` and the full selection. Rename/move controls independently cover F1. |

The final behavior baseline is `notices-red-valid-record.log` / `.xml`:
**25 failed, 362 deselected**. `red_legacy_schema.py` executes the unmodified
HEAD notices source from `notices-before.py`, adapting ONLY new host declaration
keys (strip `parent_version` and the three new text-pin fields) so the old
behavior is tested past its old strict schema. No runtime behavior is patched.
For rename/move tests the synthetic installed wheel file AND its RECORD change,
so metadata enumeration sees a genuine rebuilt/moved file. Earlier exploratory
RED runs that hit the old schema or a nonexistent repointed RECORD target are
not the behavior proof. The separate new parent-version schema controls still
exercise the current strict schema without adaptation.

`build-red-final.log` / `.xml` executes the old HEAD build source with corrected
regression fixtures: **8 failed, 122 deselected** (F4 four, F6 one, F7 three).
The initial combined `build-red.log` also records F8's nine diagnostic failures
(its first F7 fixture attempts did not reach the intended behavior; the final
eight-case baseline replaces that part). No production file was reverted for
these controls. `focused-final.log` / `.xml` is **64 passed, 510 deselected** on
the final unmodified production files. The F14 mutant is deliberately RED,
**1 failed, 386 deselected**, and is never loaded by a normal run.

**Absent-host decision, superseding turn 10.** A declaration alone still does
not assert redistribution. Omitting a component/limits entry because all its
hosts are absent is valid ONLY when those hosts' parents are not carried.
If a parent row is carried, each of its declared hosts must be present with the
census identity and parent version. Missing/renamed hosts require re-census;
identical bytes moved to an undeclared path refuse even if the original remains.
The partial/all-absent fixture controls now remove actual parent carriage as
well as the absent host. Installed build metadata alone is not carriage.

**Production generation and audit.** `prepare_manifest.py` derives parent
versions from the production plan on a fresh stage-1d copy, with existing
installed/lock/audit agreement, and verifies every declared host's measured
bytes. The Python identity also checks the interpreter's `BUILD` marker against
the manifest's PBS release. `parent-identities.json` is the seat-reviewable
110-host table. Parent counts/versions:

| Parent | Census identity | Hosts |
| --- | --- | --- |
| python | `3.12.13 (python-build-standalone 20260303)` | 7 |
| pyside6-essentials | `6.12.0` | 9 |
| shiboken6 | `6.12.0` | 1 |
| numpy | `2.5.4` | 1 |
| scipy | `1.18.1` | 83 |
| pillow | `12.3.0` | 6 |
| pillow-heif | `1.8.1` | 3 |

`manifest-generation-final.log` and `manifest-audit.log` prove 110 parent
versions and 175 source text pins; independent removal of only those added
fields reconstructs the entire previous manifest object. Every component,
source/version-evidence row, host byte identity, path and limits statement is
unchanged. Generated JSON uses literal LF, retaining the existing byte
discipline. Manifest SHA-256:
`1a3d3bba9fad9617dae0a966212de27322077c4c6922c35ec5ea46425d01bf9e`.
The loader, independent slice audit and full notices-module selection all pass.

**Fresh-copy production probes.** `notices_probe.py`, `probe-final.log` and
`probe-results.json` operate on `work/c63c-11/probes-final/` copies only. They
never execute a copied native/executable. The unchanged pre-fix renderer first
reproduced the exact supplied turn-10 hash; `notices-before.md` records it.

- POSITIVE: **140 rows, 1,536 entries, 17 limits**. New notices SHA-256
  `a50bc116ceee98dc23275bd62fde5cba51bdcb5ffe5d4474c8d16794ff79a2be`.
  Planning/rendering equals the written bytes. A scratch renderer with only
  F2's heading restoration removed reproduces the entire previous document
  byte-for-byte: `e9aec25af81312d48221b59abbc42e8778d575c6d3ad6ea891e65ecd5db8df22`.
  Thus F1/F10/F11/F13 do not change the valid artifact's rendered bytes.
- RENAME: rename `_internal/libx265-217-276e7d75772a32bd086b54d54e01fd11.dll`
  to a new hash-like name, change its bytes, and repoint an actual COPY of
  pillow-heif's RECORD. A distribution adapter reads that copied RECORD and
  resolves its renamed native to the copied file; installed metadata/licences
  and the original RECORD remain read-only. Refusal:
  `notices: embedded _internal/libx265-217-276e7d75772a32bd086b54d54e01fd11.dll absent while parent pillow-heif is carried; re-census required`.
- MOVE: copy unchanged `_internal/scipy/integrate/_quadpack.cp312-win_amd64.pyd`
  to `_quadpack_moved.cp312-win_amd64.pyd`, then remove only the original in
  that copy. Refusal names both paths and says `moved to undeclared path` and
  `re-census required`.
- Both negative copies preserve their previous notices. Original stage-1d
  notices before/after remain
  `3afe913e26ecd6fe65765943fef798450687bebf7df926d1f720da9b8e999d8c`.
  The original stage folder and installed wheel RECORD are never written.

`notices.diff` contains ONLY four headings and their corresponding `Source:`
labels; anchors, order, terms bytes and the rest of the document are unchanged:

| Shared block | Before | After |
| --- | --- | --- |
| `licence-45`, SciPy aggregate | `Reused carried notice: scipy; scipy-1.18.1.dist-info/LICENSE.txt` | `Installed wheel: scipy 1.18.1; scipy-1.18.1.dist-info/LICENSE.txt` |
| `licence-65`, Pillow aggregate | `Reused carried notice: pillow; pillow-12.3.0.dist-info/licenses/LICENSE` | `Installed wheel: pillow 12.3.0; pillow-12.3.0.dist-info/licenses/LICENSE` |
| MinGW CRT audit `COPYING` | `MinGW-w64 CRT and winpthreads (static wheels) not established by wheels` prefix | `pillow-heif / MinGW runtime not named by wheel` prefix |
| MinGW winpthreads audit `COPYING` | same reference prefix | same original pillow-heif prefix |

The latter two retain their respective upstream URL and
`; the 1.0.0 audit's upstream copy` suffix exactly. No licence text is dropped.

**Final validation.** The isolated runner is `run_tests.py` (unchanged from
turn 10): launch with `PYTHONPATH=scripts`, remove only that environment
variable before `pytest.main`, keep `sandbox_mkdir_shim`, disable cacheprovider,
timeout 300 and the QUIT_SCRIPT exclusion. No production environment check is
bypassed. The smoke source-entry child was inspected before execution: redirected
APPDATA/LOCALAPPDATA/XDG roots, blocked Qt imports, stubbed GUI/worker effects,
15-second timeout. No QUIT_SCRIPT integration test ran.

- `ruff-check-final.log`: `All checks passed!`.
- `ruff-format-final.log`: `337 files already formatted`.
- `mypy-win32-final.log`, `mypy-darwin-final.log`: each
  `Success: no issues found in 166 source files`.
- `static-exits-final.json`: all four exit codes 0.
- Exact requested `work/c63c-11` run, `pytest.log` / `.xml`:
  **5 failed, 656 passed, 1 skipped, 15 errors in 131.79s**.
- Final fresh `work/c63c-11-final` run, `pytest-final.log` / `.xml`:
  **5 failed, 656 passed, 1 skipped, 15 errors in 130.75s**.
- `test-summary.json` independently tabulates every result and names every
  failed/error case; `diff-check.log` records clean read-only `git diff --check`.

| Module | Final result |
| --- | --- |
| `test_tools_package_notices.py` | 387 passed |
| `test_tools_package_build.py` | 130 passed |
| `test_tools_package_ffmpeg.py` | 68 passed |
| `test_release_workflow.py` | 52 passed, 5 failed in local Git fixture setup |
| `test_tools_package_smoke.py` | 19 passed, 15 setup errors, 1 unchanged skip |

Five real-Git failures are
`test_real_git_gate_restores_checkout_overwrite_and_refuses_invalid_tags`
for `annotated`, `lightweight`, `wrong-commit`, `mismatched-name`, `deleted-origin`.
All fail at the fixture's `git push origin HEAD:refs/heads/main --tags`, exit 128,
with Git's restricted-token/CreateFileMapping failure. None reaches the gate.
As commissioned, these are COMMISSIONED to the seat outside the sandbox.
The unchanged skip is `test_non_windows_containment_never_silently_skips`:
`POSIX process-group native proof belongs to WP6.5`.

**[MINOR, in envelope, test-only, CONFIRMED; scope STOP]** The `synthetic` fixture
in `tests/test_tools_package_smoke.py` calls `real_plan` without the synthetic
`release["native_surface"]` at lines 262-269. It therefore combines a tiny
synthetic folder with the complete production census. Under F1 the first absent
Python host correctly refuses:
`notices: embedded _internal/_bz2.pyd absent while parent python is carried; re-census required`.
All 15 setup errors share this exact cause. A production absent-host exemption
would undo F1 and is not introduced. This turn owns that module for row counts
ONLY, so the fixture is not edited. Requested narrow follow-on grant: pass
`native_licences_path=release["native_surface"]` in that fixture's `real_plan`
call, then align its two expected notices row counts with the explicit synthetic
surface (6/8 rather than the inherited production-host 14/16). The seat must
authorize/implement the fixture change before the five-module selection can be
called green. F1's production success and negative controls already pass.

Affected setup cases (all in that fixture):

- `test_refusal_status_and_extra_stderr_fail_by_row_name`: `wrong-status`,
  `two-lines`, `stdout`.
- `test_timeout_and_surviving_child_fail_and_are_reaped`: `hang`, `leftover`,
  `fast-leftover`.
- `test_complete_smoke_preserves_shipping_bytes_and_checks_conditional_tools`:
  `False`, `True`.
- `test_bad_configuration_capabilities_or_missing_exception_log_fail`:
  `configure`, `version`, `encoders`, `no-log`.
- `test_static_checks_reread_artifact_and_refuse_before_entry_launch`:
  `cuda`, `hidden`, `notices`.

**Verification loop / cumulative round ledger.** The independent pre-change
behavior runs confirm every fixed finding; final focused controls, copied-folder
probes, manifest/slice audit and static checks find no further product issue.
The full run confirms the synthetic-fixture scope finding above; it remains
COMMISSIONED to the dispatcher for a narrow grant, not hidden with a test hook.
Initial invalid RECORD-fixture targeting and a type-variable reuse were fixed;
the corrected RED and final GREEN evidence are the results claimed here.

| Round | Critical / major / minor / advisory | In / out of envelope | NEW / REOPENED | Reverts | Dispositions | Fix type | Depth |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A r1 | 0 / 1 / 3 / 10 (seat classification) | 10 / 4 | 14 / 0 | 0 | 11 fixed; F3/F5 held by CHARC; F9 declined | 9 product-code, 1 test-only, 1 documentation | dispatcher supplies `depth_input_tokens` |

This row is the transfer for the dispatcher's cumulative ledger; no unowned
proof/ledger file was edited. The new fixture scope finding is an implementer
verification finding, not a new Reviewer A round. Reviewer A r2, Reviewer B and
the package gate remain the dispatcher's work. No five-round continuation gate
is reached in this turn.

**Scope / handoff.** Nine owned tracked files changed; `tests/test_tools_package_smoke.py`
is untouched. The manifest changes only `parent_version` and F10's pin fields.
The workflow changes only the tag gate's stderr handling, preserving its timeout
structure. No fork patch, FFmpeg lock, root notices, dependency, frozen interface
or `src/` change; no network, real PyInstaller build, frozen/GUI launch, Docker,
desktop input, protected-folder write, repository Git write, push, tag, workflow
dispatch or mailbox post. The prescribed real-Git tests create only their own
temporary fixture repositories before their sandbox push fails. Scratch files
and copied artifacts stay in this worktree. The real fork/asset/re-pin, release
work and CHARC-held F3/F5 remain later/seat work. This turn bundles the single
commissioned r1 remediation set; the seat commits. `depth_input_tokens` is
unavailable to the cell; dispatcher read due at this boundary, no estimate.

## Turn 12 - Synthetic smoke surface and content-hashed DLL controls

**Built (test-only).** The smoke fixture now passes its explicit
`release["native_surface"]` to `real_plan`. Expected counts are **6** component
rows without FFmpeg and **8** with FFmpeg, confirmed by the complete smoke
transcripts (13 / 17 entries). No production absent-host exemption.

The new parametrized notices test declares the production-shaped host
`_internal/libx265-217-276e7d75772a32bd086b54d54e01fd11.dll` through wheel path
`pillow_heif.libs/`, parent `pillow-heif` **1.8.1**. A positive plan establishes
parent/component carriage. Both negatives change wheel/bundle bytes and repoint
the actual RECORD path/hash/size, preserving METADATA and parent version.
Renaming to `libx265-217-0123456789abcdef0123456789abcdef.dll` refuses by
declared host and parent with `re-census required`; keeping the name refuses
with `identity differs`, expected/actual hashes and `re-census required`.

**RED -> GREEN.** Evidence is under `work/wp6.3c/turn12/`. `run_head_red.py`
loads the exact `git show 559621f7:tools/package/notices.py` bytes into a scratch
module. As in turn 11, its declaration adapter strips ONLY `parent_version` and
the three new source-text-pin keys to pass turn 10's strict schema; runtime
behavior is unchanged and no tracked production file is replaced.
`red-final.log` / `.xml`, fresh `work/c63c-12-red-final`: **1 failed, 1 passed,
387 deselected**. Rename fails `DID NOT RAISE`; same-name identity refusal
already passes. Current-code `green.log` / `.xml`, fresh `work/c63c-12-green`:
**2 passed, 387 deselected**.

**Validation.** Requested `uv run --no-sync` commands ran in order;
`static-exits.json` records four exit codes 0:

- `ruff-check.log`: `All checks passed!`.
- `ruff-format.log`: `337 files already formatted`.
- `mypy-win32.log`, `mypy-darwin.log`: each
  `Success: no issues found in 166 source files`.

The isolated `run_tests.py` retains `sandbox_mkdir_shim`, disables cacheprovider,
enforces timeout 300 and the QUIT_SCRIPT exclusion, and removes runner-only
`PYTHONPATH` before pytest while retaining `scripts` on `sys.path`.
`pytest.log` / `.xml`, exact fresh `--basetemp=work/c63c-12`, exit 1:
**5 failed, 673 passed, 1 skipped in 159.78s**. `test-summary.json` enumerates
every result.

| Module | Result |
| --- | --- |
| `test_tools_package_notices.py` | 389 passed |
| `test_tools_package_build.py` | 130 passed |
| `test_tools_package_smoke.py` | 34 passed, 1 unchanged skip |
| `test_tools_package_ffmpeg.py` | 68 passed |
| `test_release_workflow.py` | 52 passed, 5 sandbox fixture failures |

All five failures are
`test_real_git_gate_restores_checkout_overwrite_and_refuses_invalid_tags`
(`annotated`, `lightweight`, `wrong-commit`, `mismatched-name`, `deleted-origin`).
Each fails at local fixture `git push origin HEAD:refs/heads/main --tags`, exit
128, with restricted-token `CreateFileMapping`; none reaches the gate. Seat
reruns remain commissioned. The skip is
`test_non_windows_containment_never_silently_skips` (WP6.5 POSIX proof).

**Verification / handoff.** The granted smoke-fixture defect is CONFIRMED and
FIXED; baseline rename refusal is missing and same-name identity refusal is
preserved. Every other selected test passes; final owned-diff review finds no
new issue. No new review round or package acceptance is claimed. Only the two
granted test edits and this report change. Source-entry smoke isolation was
inspected: disposable profile/XDG roots, Qt import block, stubbed GUI/worker,
15-second timeout. No production/dependency/frozen-interface change, network,
real build, frozen/GUI launch, Docker, desktop input, protected-folder write,
repository Git write, push/tag/dispatch or mailbox post. Scratch evidence stays
in this worktree; only prescribed tests attempt temporary local Git fixture
pushes. No new scope question; real-Git reruns and review remain seat work.
`depth_input_tokens` is unavailable to the cell; dispatcher read due at yield.

## Turn 13 - Real fork asset re-pin and schema-2 notices

**Built.** The lock now names `rwsmythe/FFmpeg-Builds` at
`d77b8352f60bd180ebce585632846533aa60b183`, release
`ffmpeg-9.0-gb204e94e-nozvbi-d77b835`. Schema 2 adds `parent_provider` as
`{repository, commit}` (BtbN/FFmpeg-Builds at
`5031c6f1082414e53688d39e521849905071070d`) and `ffmpeg_ref: release/9.0`,
with FFmpeg's full commit `b204e94e90fca64045e9ca7dd44c65678c7eb29e`.
No `ffmpeg_tag`, schema-1 route or legacy-schema bypass remains. Unknown/missing
keys, malformed parent records, short/uppercase FFmpeg commits and mismatched
version abbreviations refuse. GPL/version3/x265 and disabled zvbi are required;
enabled zvbi, nonfree and enabled fdk-aac refuse. Disabled fdk-aac remains correct.
The 97 primary rows and five extra source records are unchanged except removal
of zvbi: 102 compatible source records, two downloaded-not-built, yielding 100
built-component notice rows plus the aggregate FFmpeg row. The excluded zvbi
entry names GPL-2.0-only `src/packet-830.*` / `src/pdc.*`, the owner's
2026-11-05 "self-build is fine" ruling and the full fork commit.

The existing lock convention stores `version` as the printed version TOKEN,
`n9.0.2-47-gb204e94e90-20261106`, rather than the entire first line; the field
remains directly consumable by `_pinned_ffmpeg_version`. Configuration keeps the
printed `configuration: ` prefix, verbatim. The synthetic executable now prints
`Exiting with exit code 0` after its version/configuration lines: the existing
probe accepts this without a production probe change. Its first-line and exact
configuration checks remain in force.

**Run 1 and r2 ruling (dispatch facts, not a cell fetch).** Run `42156511472`
at fork commit `92d0b6a6` failed because the `n9.0.2` FFmpeg tag calls
`oapvm_create` with one argument while BtbN's pinned openapv >= 1.1 requires two.
CHARC ruling `d5893fca` pins `release/9.0` commit
`b204e94e90fca64045e9ca7dd44c65678c7eb29e` instead: n9.0.2 plus 47 backports,
including `a7502e5f`'s openapv fix. The seat made the r2 commit/export; neither
the fork clone nor `tools/package/ffmpeg-fork.patch` was edited this turn.

**Seat provenance accepted from dispatch 13.** Successful run
[42180812511](https://github.com/rwsmythe/FFmpeg-Builds/actions/runs/42180812511),
branch `wp6.3c-nozvbi-r2`; seat record
`clearwater-review-evidence/wp6.3c/seat/fork-run.md`, SHA-256
`6fc40deda4b43c1ef6602821ceb657a1940d95fedbf48c37e886196bae094ead`.
Asset `ffmpeg-n9.0.2-47-gb204e94e90-win64-gpl-9.0.zip` is 194,771,780 bytes;
GitHub's per-asset digest, the seat's computed SHA-256 and `checksums.sha256`
all equal `3534afe300170f55521d78bad405f54def9d388abba30aee7620dc525e2e0c20`.
F3: the lightweight release tag peels to the fork commit above, equal to the
run's `head_sha`. F3b: the run log records
`+ git checkout --detach b204e94e90fca64045e9ca7dd44c65678c7eb29e` then
`HEAD is now at b204e94e90`; the binary's `-gb204e94e90` abbreviation is a
prefix of the full pin. The validator now enforces that relationship with at
least seven lowercase hex digits.

The seat's first lines, preserved here verbatim:

```text
ffmpeg version n9.0.2-47-gb204e94e90-20261106 Copyright (c) 2000-2026 the FFmpeg developers
ffprobe version n9.0.2-47-gb204e94e90-20261106 Copyright (c) 2007-2026 the FFmpeg developers
```

The seat records 48 archive entries, the expected two executable members and
`LICENSE.txt` (GPL-3.0, 35,147 bytes, SHA-256
`8ceb4b9ee5adedde47b31e975c1d90c73ad27b6b165a1dcd80c7c545eb65b903`).
Encoder output contains `libx265` and `hevc_nvenc` and no fdk encoder. The only
configuration changes from WP6.3b are enabled -> disabled zvbi and the date
20261031 -> 20261106. These are seat facts; no live download, real executable
probe or archive inspection was performed by this cell.

**Notices and docs.** FFmpeg rows share the existing single GPL-3.0 text block;
the aggregate notes now identify fork/parent provenance, the full fork commit,
FFmpeg ref/commit and every excluded stage's reason. The full-lock synthetic
render test proves 101 rows, one text block and the zvbi exclusion line. The
root notice's FFmpeg row now describes the bundle; its source-install sentence
keeps user-obtained tools on PATH without prescribing gyan.dev. The guide's
FFmpeg sentences describe the bundle and BtbN scripts without zvbi. The
checklist removes the obsolete HOLD/expiry and describes future fork rebuilds,
the full detached checkout, one dispatch, three-way digest, F3/F3b and re-audit.
The checked-in step 10 had no explicit force-moved-tag sentence; it now states
why the downloaded source/content census must match the local gated build.
No workflow field names changed; `release.yml` is untouched.

Reviewer A r2 minor 1: CONFIRMED and FIXED. A census parent must be `python`
or a runtime distribution present in the lock/audit runtime set, before the
absent-parent early return. Unknown `numpy-typo` refuses with the host, parent
and "declared parent unknown to this build; re-census required", even when its
host is absent. Known parents not carried still retain the prior omission rule.

**Reproducibility and limits.** Pinned: the fork commit, every `SCRIPT_COMMIT`
recorded by its pinned recipes, and FFmpeg's full `release/9.0` commit, plus the
published asset's bytes by size and SHA-256. Per CHARC:
"component scripts under `scripts.d/` byte-identical to `5031c6f1` except `50-zvbi.sh`; `build.sh` carries exactly one added checkout line; `addins/`, `variants/`, `images/`, `util/` untouched; the workflow trimmed as in r1 plus the TAGNAME."

Floating inputs remain `ubuntu:26.04`, apt packages, the Rust toolchain
(`images/base/Dockerfile:41-42` uses rustup without a version and unversioned
`cargo install cargo-c`), and crosstool-ng HEAD/download/patch recipes
(`images/base-win64/Dockerfile:6-11`). The checked-in ct-ng config names GCC
16.2.0, mingw-w64 v14.0.0 and binutils 2.47, but crosstool-ng itself is not pinned.
These prevent a byte-reproducible rebuild claim. They can also affect carried
runtime code: Rust's standard library is statically linked through rav1e
(`scripts.d/50-rav1e.sh:16-17,40`), so a future Rust toolchain can change that
bundled component's version; crosstool-ng's moving recipes/download set can
change the compiler/MinGW runtime inputs linked via `-static-libgcc` /
`-static-libstdc++` (`images/base-win64/Dockerfile:56-58`). None of this changes
the 102 recorded library source pins. Do not characterize all floats as
"toolchain only": CHARC's accept must open the prescribed register row for
floating Rust/compiler runtime inputs. Resolved runtime versions beyond the
seat's supplied facts are not asserted here. The rav1e recipe also runs
`cargo update cc` (line 26), an additional floating build dependency; its
transitive effects have not been proved toolchain-only.

the fork workflow grants contents + packages write at the top level, not per job; one-shot dispatch in the owner's fork

**RED -> GREEN and verification.** Logs/XML stay under
`work/wp6.3c/turn13/`. Before production/lock changes, `red.log` / `red.xml`,
fresh `work/c63c-13-red`, reported **9 failed, 23 passed, 437 deselected**:
schema-1 acceptance, old pin/source counts, short/mismatched hashes, enabled or
missing-disabled zvbi, and the absent-host unknown-parent omission were exposed.
After the changes, `green.log` / `green.xml`, fresh `work/c63c-13-green`,
reported **92 passed, 381 deselected**. The selected tests also cover the full
notices render, enabled fdk refusal, disabled fdk acceptance, exact configure
and tool-version matching, and the new trailing output line.

The old acceptance-only incompatibility test is replaced by two executed
bundle-to-notices refusal controls, for primary and built extra sources. The
synthetic file transport must share the fixture's explicitly enabled build-tool
hook with notices; that fixture boundary was corrected without a production
bypass. `refusal-fixed.log` reports three passed (including the full render);
`refusal-final.log` / `.xml`, fresh `work/c63c-13-final-refusal`, reports
**2 passed, 81 deselected** after the final regex/format cleanup.
`lock-audit.log` independently compares the current lock with `git show HEAD`:
all 102 remaining source records byte-equivalent as decoded records, prior
exclusions unchanged, exact dispatched digest and only the two dispatched
configuration substitutions. No new in-envelope product defect remained in the
final diff pass; the test-only stale-expiry issue below remains open.

**Final validation.** Requested no-sync static commands ran in order. Initial
ruff line-length/raw-regex findings were fixed; final files are:

- `ruff-check-final3.log`: **All checks passed!** (exit 0).
- `ruff-format-final3.log`: **337 files already formatted** (exit 0).
- `mypy-win32-final.log`, `mypy-darwin-final.log`: each
  **Success: no issues found in 166 source files** (both exit 0).
- `diff-check-final.log`: exit 0.

The isolated runner retains `sandbox_mkdir_shim`, no cacheprovider, per-test
300-second timeout, QUIT_SCRIPT exclusion and removal of runner-only PYTHONPATH
while keeping `scripts` on sys.path. The first prescribed full five-module run,
`pytest.log` / `.xml`, exact fresh `work/c63c-13`, reported **6 failed, 688 passed,
1 skipped in 178.41s**. After replacing the acceptance-only test with the two
refusal cases, the final complete run used fresh `work/c63c-13-final`:
`pytest-final.log` / `.xml`, exit 1, **6 failed, 689 passed, 1 skipped in 278.19s**.
`test-summary.json` names every failure and skip. These are the cell's historical
turn-13 results; the seat's resolution and superseding validation follow below.

| Module | Final result |
| --- | --- |
| `test_tools_package_notices.py` | 391 passed |
| `test_tools_package_build.py` | 130 passed |
| `test_tools_package_smoke.py` | 34 passed, 1 unchanged skip |
| `test_tools_package_ffmpeg.py` | 83 passed |
| `test_release_workflow.py` | 51 passed, 6 failed |

Five failures are the prescribed real-Git cases
`test_real_git_gate_restores_checkout_overwrite_and_refuses_invalid_tags`
(`annotated`, `lightweight`, `wrong-commit`, `mismatched-name`, `deleted-origin`).
All fail at the local fixture's `git push origin HEAD:refs/heads/main --tags`,
exit 128 with the restricted-token `CreateFileMapping` error, before exercising
the tag gate; seat reruns remain required. The
unchanged skip is `test_non_windows_containment_never_silently_skips` (POSIX
containment belongs to WP6.5).

**STOPPED ITEMS / out-of-envelope finding [MINOR, test-only].**
`tests/test_release_workflow.py:639` still asserts `2028-10` occurs in the
checklist. The required removal of the retired BtbN expiry date confirms this
failure independently in both complete runs. Turn 13 does not own that module;
it was untouched by the cell. The seat was asked to update/grant this assertion
to require the fork's no-retention-policy/rebuild rule instead. The checklist intentionally
keeps its correct new guidance. This is the only non-sandbox failure; the
turn's target of every other test passing was therefore not claimed by the cell.

**Seat resolution (supersedes the STOP above).** The seat GRANTED turn 13's STOP:
the assertion at `tests/test_release_workflow.py:639` moved from `"2028-10"` to
`"rebuild FFmpeg in the fork"` in seat commit `749fd30b`. The seat reports
**695 passed, 1 skipped**, including the real-Git cases, at that commit. The
release-workflow test module was changed by the seat; the workflow YAML itself
remained untouched. Turn 14's own validation appears below.

**Handoff / remaining work.** No new review round or package acceptance is
claimed. The seat owns the stale test disposition, real-Git reruns, review,
real local build + smoke + zip, bundled V4 / encoder proofs, gate and release.
CHARC's floating-runtime register row remains due at accept. Only the nine
tracked paths named in this turn's return are changed; neither the patch,
workflow nor any `src/` file changed. No dependency or frozen interface change,
network, real PyInstaller build, frozen/GUI launch, Docker, desktop input,
protected-folder write, repository Git write, push/tag/dispatch or mailbox post
was performed. Prescribed tests alone attempt temporary local Git-fixture
pushes; every runner output stays inside this worktree. No review ledger edit
was owned this turn. `depth_input_tokens` is unavailable to the cell;
dispatcher read is due at yield.

## Turn 14 - Reviewer A r3 cleanup

**Built / adjudication (2026-11-06).** Applied the eight dispatched folds in
the five owned files. No additional review round or package acceptance is
claimed. Reviewer A r3's supplied verdict is `NO_NEW_CRITICAL_MAJOR`.

| Finding | Severity | Disposition / evidence |
| --- | --- | --- |
| 1 | MINOR | CONFIRMED / FIXED: every refusal case matches its own message. Enabled zvbi now has a covered component and no excluded-stage collision. Removing only the zvbi guard accepts that fixture, proving the coverage check no longer masks it. |
| 2 | MINOR | CONFIRMED / FIXED: the turn-13 CHARC quote includes `variants/`, `images/`, `util/` and "plus the TAGNAME", verbatim from the amendment. |
| 3 | MINOR | CONFIRMED / FIXED: header and turn-13 seat note supersede the historical stale-assertion STOP with seat commit `749fd30b` and its 695 passed / 1 skipped result, including real Git. |
| 4 | MINOR | CONFIRMED / FIXED: future rebuild guidance updates hard-coded `TAGNAME` and requires a reviewed validator change before changing `release/9.0` or pinning exactly at a tag without `-g`. |
| 5 | MINOR | CONFIRMED / FIXED: checklist step 10 names the sidecar's `# source-commit:` and draft body's Source commit comparisons against the gated commit. Chose to DROP the undefined local content-census comparison; no CI/local byte-identity claim remains. |
| 6 | ADVISORY | CONFIRMED / FIXED: full version-token match rejects a second `-g` suffix; matching 7-, 10- and 40-hex abbreviations still pass. |
| 7 | ADVISORY | CONFIRMED / FIXED: parent repository must equal `BtbN/FFmpeg-Builds`; existing full lowercase-hex commit validation is retained and tested with short and uppercase refusals. |
| 8 | ADVISORY | CONFIRMED / FIXED: excluded zvbi uses `not-built(disabled)`. The full tool/notices tests check for dependencies on the prior status. |

**Refusal controls / mutation reasoning.** Each parameter below mutates a valid
lock. Its `match=` names the intended refusing guard, so removing that guard
cannot be masked by a later refusal with another message. The `basis` case now
changes only `licence_basis`, leaving a valid licence so the seat-verification
guard is reached.

| Mutation(s) | Guard / expected refusal |
| --- | --- |
| `schema` | Unsupported schema version. |
| `unknown`, `ffmpeg-tag`, `missing` | Exact document fields reject an extra key, retired field or absent provider. |
| `short-commit`, `uppercase-commit` | FFmpeg commit must be 40 lowercase hex. |
| `version-commit` | A well-shaped but unrelated abbreviation fails the commit-prefix comparison. |
| `short-version-commit`, `double-version-commit` | Whole-token grammar refuses six hex digits or an extra `-g` suffix. |
| `missing-disable-zvbi` | Explicit disable switch is required. |
| `enable-zvbi` | Enable switch is forbidden even with complete configure coverage; a synthetic compatible source row covers it and the excluded zvbi row is removed. |
| `parent-unknown`, `parent-missing` | Exact parent fields reject an extra or absent key. |
| `parent-repository` | `evil/x` fails exact parent repository identity. |
| `parent-short-commit`, `parent-uppercase-commit` | Parent commit must be 40 lowercase hex. |
| `digest-length`, `digest-mismatch` | SHA-256 must be 64 hex digits and both readings equal. |
| `missing-gpl`, `missing-x265` | Required configure switches must be present. |
| `nonfree`, `fdk` | Forbidden enabled configure switches are refused. |
| `extract` | Member allowlist refuses ffplay. |
| `duplicate-stage`, `duplicate-name` | Component identities must be unique. |
| `unmapped`, `reverse-map` | Two-way configure coverage refuses an unmapped enable or absent mapped switch. |
| `major` | The pre-existing FFmpeg-major guard still refuses n8. |
| `component-schema` | Exact component fields require repository. |
| `pin` | A moving-branch string fails the component's commit-pin grammar. |
| `basis` | Every licence must be seat-verified. |
| `extra-source` | An incomplete extra source fails exact source fields. |

**RED -> GREEN.** Logs and XML are under `work/wp6.3c/turn14/`.
`red.log` / `red.xml`, fresh `work/c63c-14-red`, reports **2 failed, 30 passed,
54 deselected** against the old validator: the double-`-g` and wrong-parent
cases were accepted. After the validator change, `green.log` / `green.xml`,
fresh `work/c63c-14-green`, reports **35 passed, 51 deselected**, including all
32 refusal cases and the three valid abbreviation lengths.
`zvbi-mutation.log` independently reports PASS after compiling an in-memory copy
of the current validator with only the zvbi guard removed: the enabled-zvbi
fixture is then accepted with configure coverage intact. No source file was
changed for that mutation.

**Validation.** The prescribed commands use `uv run --no-sync`; logs are in the
same turn-14 folder:

- `ruff-check.log`: **All checks passed!** (exit 0).
- `ruff-format.log`: **337 files already formatted** (exit 0).
- `mypy-win32.log`, `mypy-darwin.log`: each **Success: no issues found in
  166 source files** (both exit 0).
- `pytest.log` / `pytest.xml`, exact fresh `work/c63c-14`: **5 failed,
  693 passed, 1 skipped in 156.66s**, exit 1. All five failures are the expected
  real-Git fixture cases (`annotated`, `lightweight`, `wrong-commit`,
  `mismatched-name`, `deleted-origin`): fixture setup's local push exits 128
  with `CreateFileMapping` under the restricted token, before the tag gate.
  Every other test passes. The unchanged skip is the POSIX containment proof
  assigned to WP6.5. `test-summary.json` / `summary.log` confirm this from XML.
- `scope-audit.log`: PASS, lock differs only in excluded zvbi status and
  `build.py` differs only in `validate_ffmpeg_lock` (exit 0).
- `diff-check.log`: `git diff --check`, exit 0.

The unchanged isolated runner is `work/wp6.3c/turn13/run_tests.py`: launched with
`PYTHONPATH=scripts`, it removes that environment variable before pytest while
retaining the shim import path, loads `sandbox_mkdir_shim`, disables cacheprovider,
sets timeout 300 and excludes QUIT_SCRIPT. Exact full selection:

```text
uv run --no-sync python work/wp6.3c/turn13/run_tests.py tests/test_tools_package_notices.py tests/test_tools_package_build.py tests/test_tools_package_smoke.py tests/test_tools_package_ffmpeg.py tests/test_release_workflow.py --basetemp=work/c63c-14 --junitxml=work/wp6.3c/turn14/pytest.xml -q -rs
```

`entry-audit.log` records the entry-point grep. The source-entry smoke child
redirects APPDATA, LOCALAPPDATA and all four XDG roots, blocks Qt/shiboken imports,
stubs app/worker effects and has a 15-second timeout; native smoke execution is
substituted with the existing bounded Python stubs. No old revision was executed.

**Round-ledger transfer / verification loop.** A r3 cleanup: zero new critical
or major, five MINOR and three ADVISORY findings folded, all in-envelope and
NEW; zero reopened findings, reverts or false-positive rejections. Fixes touch
validator product code, tests/controls, one lock status and docs. Advisories 9
(seat trailer) and 10 (CHARC wording) are outside this turn as dispatched. Earlier
rounds' dispositions remain in this report and the dispatcher's cumulative
ledger; no unowned ledger file was edited. Suspected validator gaps were
independently confirmed by RED tests; the coverage-masking defect was confirmed
by the guard-removal mutation; all eight folds were fixed. Final diff review
and the completed validation found no new in-envelope defect. The expected
sandbox real-Git failures remain seat verification work.

**Scope / handoff.** No interface, dependency, source pin or asset identity
changed. The version remains the printed token. The only lock edit is zvbi's
status. No network, real PyInstaller build, frozen/GUI launch, Docker, synthetic
desktop input, protected-folder write, repository Git write, push/tag/dispatch
or mailbox post was performed. Prescribed real-Git tests alone attempt writes
in disposable local fixtures. Every runner output remains under this worktree.
STOPPED ITEMS: none in the eight folds. The seat owns real-Git verification,
review, real build/smoke/zip, V4/encoder proofs, gate, accept and release.
`depth_input_tokens` is unavailable to the cell; dispatcher read is due at yield.

## Turn 15 - Reviewer B r1 runtime notices and provenance remediation

**Built (2026-11-06; dispatch 15).** Added the measured `toolchain` object
and all 232 `toolchain_runtime` rows to schema 2 without a legacy-schema
route. The 97 primary stages and five additional source records are unchanged;
100 built stage/source rows plus 232 runtime rows and the aggregate make
333 FFmpeg notice rows. The runtime kinds are 223 cargo-crate, four rust-std
and five gcc-runtime; reached-via counts are librsvg 148, rav1e 65 and
toolchain 19. The census bases remain compile-log 213, lock-graph 13 and
binary six. There is no new mingw-runtime row: the existing mingw stage
covers the statically linked CRT / winpthreads, per CHARC's ruling.

**Input and copy evidence.** All three supplied input hashes matched:
`fb1-rows.json` = `2e7d796ec3c4f1d81b545139766d8d7a7b33e72bd62425c85bf6625c6b8b31df`;
`fb1-texts/index.json` = `faabab3691782a7f2be6c7fce839165e22d3d1f05e14d5282d7a1dab1e4a2c5b`;
`fb1-census.md` = `fb9c94639c8b4428851767eb76840c7a11b0cf4e81c83341c49b87a8ab3adb4c`.
`inputs.log`, `copy.log` and `data-verification.log` under
`work/wp6.3c/turn15/` record 157 distinct texts copied once with
`read_bytes` / `write_bytes`, named from the index's stored path by replacing
separators with `--`. Every copy and all 441 row-to-text references re-hash
correctly. The current, hash-pinned rows contain 441 references; the brief's
older 408-text count is superseded by these verified input bytes. All row
fields, row order and per-row hash order are unchanged except mapped paths;
no row was invented or dropped. The list for the dispatcher is
`work/c63c-15/copied-texts.txt` (also retained under the turn-15 log folder).

**Validator and text checks.** `validate_ffmpeg_lock` remains pure. Its helper
`_ffmpeg_runtime` enforces exact document/toolchain/runtime/text fields,
enumerations, pin lengths, crate archive URLs, unique name/version/stage
identities, chosen OR alternatives, compatible SPDX grammar, required Rust
and GCC rows, converse stage coverage and compiler version/commit bindings.
The compatible atom set is exactly CHARC's 15 expressions. Unknown atoms
refuse even in an OR branch; WITH binds before AND, which binds before OR.
The backtrace submodule keeps its own commit. Empty census licence notes are
preserved, and quick-error's published HTTP repository pointer is preserved;
its crate download URL remains the required HTTPS canonical URL.

`notices.py::_ffmpeg_rows` checks every runtime text's existence, plain
filename and SHA-256, then constructs contextual `LicenceInput`s with the
recorded hash and measured size. Rendering rechecks those inputs before
content deduplication, so changing a shared text after planning still refuses.
Runtime rows use their own terms only; the renderer does not require the
aggregate FFmpeg GPL input on each runtime row. The parent sentence appears
once per runtime row, as do the source/census notes, the chosen Apache-2.0
note on Ryu and MPL-2.0's section-3.3 statement on its five rows. Each distinct
runtime text renders once. The native manifest reader recognizes only the
`ffmpeg-toolchain` directory as separately locked; other undeclared files
and directories still refuse.

**Root notices.** The root file can carry 232 rows without changing its
source-install audit schema. A generated runtime annex uses the existing
`_ffmpeg_rows` / `render_notices` path, with the same 232 rows and links to
the 157 byte-preserved text files used by artifact generation.
`generate_root_notices.py` under the turn-15
log folder records the offline recipe; its four temporary notice-input files
were never executed. The runtime render test requires agreement between
the root annex and the artifact renderer's runtime table/details, and checks
all 157 text links and hashes. Artifact notices carry the full verbatim texts;
the root annex links them because Git normalizes Markdown line endings on
Windows and one upstream text (`approx-0.5.1/LICENSE`) contains CRLF bytes.
Original audit blocks remain available under their existing anchors.

| B r1 finding | Severity | Turn-15 disposition |
| --- | --- | --- |
| F-B1 | MAJOR | CONFIRMED / FIXED: runtime census, source and compiler bindings, byte-exact terms, artifact and root notice rows. Review/acceptance remains the seat's. |
| F-B2 | MINOR | CONFIRMED / FIXED: each of the five guards has a named-refusal mutation case; both invalid refs are covered. An independent in-memory AST mutation check distinguishes all five guards. |
| F-B3 | MINOR | CONFIRMED / FIXED: exact initial GitHub asset URL; fork tree-root source pointer; release tag contains FFmpeg's eight and fork's seven hex digits (the real tag satisfies both); required excluded-only zvbi; date equals exactly one extra-version value. The existing file-URL hook remains synthetic-test-only. |
| F-B4 | MINOR | CHARC DEFERRED to DR-149; no expansion to non-host native census this turn. |
| F-B5 | MINOR | CONFIRMED / FIXED: rebuild STOPs, patch re-export command, validator/five-module rerun, F-B1 re-census before a draft, and stale retention wording removed. |
| F-B6 | ADVISORY | CONFIRMED / FIXED: parser and direct build refuse zip without both verified FFmpeg arguments; the existing build path verifies them and bundles before notices/smoke/zip. Workflow line 123 already supplies both; YAML untouched. |
| F-B7 | ADVISORY | CONFIRMED / FIXED: `Excluded <stage> (<status>): <reason>`; BUILT / ENTRY instead use `Build stage`, avoiding a false exclusion claim. |
| F-B8 | ADVISORY | CONFIRMED / FIXED: build record writes Parent provider and FFmpeg ref, notices requires each exact line, and source_record_url points at the fork commit's tree root. |
| F-B9 | ADVISORY | NOTED per CHARC; exact scope note below. |
| F-B10 | ADVISORY / OUT OF ENVELOPE | Recorded as the reproducibility limit below; fork workflow untouched. |

B r1 F-B9 listed files outside the brief's Files-owned row (`docs/user-guide.md` sections 2 and 6, `tools/package/README.md`, `tests/test_tools_package_ffmpeg.py`, `.github/workflows/release.yml`, `tests/test_release_workflow.py`, `tests/test_tools_package_smoke.py`). CHARC NOTED it; each was granted in dispatches 3-11 (the seat's confirmation is in the accept record).

**Reproducibility and limits (runtime amendment).** The asset and all existing
stage source pins remain unchanged. The lock now records Rust 1.99.1 at
`58cf8f9c35b355199727627d07ae34a4e2846d67` and GCC 16.2.0 at
`78d4ac73dd391005b895a6148cd9831e28e1208b`, build
`crosstool-NG 1.29.0.7_b1a94f6`, with the two static flags and resolved crate
checksums. These are seat census facts copied offline, not a cell probe of
real executables or a claim of a byte-reproducible recipe.

- LIMITS: the fork workflow keeps BtbN's floating action tags at `5031c6f1`; the recorded asset is bound by run id plus the three-way digest, which a moved action cannot alter after the fact.
- LIMITS: libgcc soft-fp contains glibc files under LGPL-2.1-or-later with glibc's unlimited-link exception; no row is carried, per CHARC's ruling.
- LIMITS: header-only pstl is Apache-2.0 WITH LLVM-exception and enters a C++ dependency's own code only if that dependency uses parallel algorithms; no row is carried, per CHARC's ruling.
- LIMITS: mingw-w64 v14.0.0 crosstool sysroot headers used to compile the GCC runtime archives are the same project and licence family as the existing mingw row; no separate row is carried, per CHARC's ruling.
- LIMITS: the Rust toolchain is pinned by the recorded asset, not by the recipe; the base image installs unpinned stable Rust, and pinning it in the fork is out of envelope.

The libm / libstdc++ (fast_float) supersets retain their lock-graph/no-linkage-proof
notes. Ryu keeps `chosen: Apache-2.0`; libstdc++ includes the eight HP / SGI
notice excerpts. Existing floating ubuntu/apt/crosstool inputs and the
`cargo update cc` limit remain as recorded in turn 13. The checklist now
requires a fresh F-B1 census on every fork rebuild.

**Existing-case changes.** `release`'s synthetic FFmpeg lock now declares its
extra-version date, keeps the zvbi exclusion, and empties runtime rows/static
flags when both Rust stages are absent; `add_ffmpeg` writes the two provenance
lines. `test_fork_ffmpeg_notices_render_all_built_sources_and_explain_exclusions`
expects 333 FFmpeg rows and status-bearing stage text, preserving the single
GPL block check for the aggregate/stage rows. `_make_native_surface` excludes
the separately locked text directory from its file-only fixture;
`omit_production_embedded_census` retains that directory while pruning its
own file surface, fixing nine cases across
`test_census_native_rows_validate_and_bind_synthetic_bytes` and
`test_real_scipy_vendored_blocks_bind_module_inventory`. The three zip cases
(option routing, post-smoke publication and smoke mutations) supply the
required lock arguments; the latter two isolate zip behavior with a bundle
stub while existing synthetic archive tests exercise real verification.
No smoke or release-workflow test file changed.

**Verification loop.** Initial RED (`red.log` / `.xml`) reported 70 failed,
two passed and six fixture errors before production changes; the new
subdirectory exposed the fixture's file-only cleanup assumption. After the
fixture adjustment, `red-notices.log` / `.xml` reported all six new notices
cases failing against the old behavior. The first GREEN exposed an unintended
HTTPS-only repository guard and an incorrect librsvg switch spelling;
independent input inspection confirmed quick-error's actual HTTP repository
and the real `--enable-librsvg` spelling. Both were corrected without changing
the census data. `green2.log` / `.xml` reports 78 passed. The first full run
(`pytest-first.log` / `.xml`) reported 762 passed, 14 failed and one skipped:
nine failures were the second file-only fixture cleanup, and five were the
expected real-Git sandbox failures. The nine fixture cases are fixed;
`regression.log` / `.xml` then reports 105 passed, including the additional
chosen-without-OR control, root agreement, zip and census-fixture cases.
Initial mypy's three errors were a reused local variable's inferred type;
renaming it fixes the typing without changing behavior.

`mutations.log` independently compiles five AST-mutated in-memory copies:
removing ref/licence guards accepts the invalid data; removing build-commit,
asset-name or fullmatch validation reaches a different refusal. Each therefore
fails its new named-refusal test. `scope-audit.log` independently confirms that
only toolchain, toolchain_runtime and source_record_url changed in the lock,
all 102 stage/source records are unchanged, and all tracked/new paths are owned.
An additional checkout check (`newline-audit.log`) confirmed that CRLF input
and `core.autocrlf=true`; the root annex was changed to link exact text files
instead of embedding a copy whose bytes would change on checkout.
`root-agreement.log` / `.xml` reports the revised agreement case passing.
The subsequent diff review found no further in-envelope defect; no false-positive
review finding was silently dropped. No new review round or convergence claim
is made: A delta and B r2 belong to the seat after this handoff.

**Final validation (supersedes the intermediate runs).** All outputs are
file-backed under `work/wp6.3c/turn15/`. No-sync static commands ran in the
prescribed order on the final code/test state:

- `ruff-check-final.log`: All checks passed! (exit 0).
- `ruff-format-final.log`: 337 files already formatted (exit 0).
- `mypy-win32-final.log` and `mypy-darwin-final.log`: each Success: no issues
  found in 166 source files (exit 0).
- `pytest.log` / `.xml`, exact requested basetemp `work/c63c-15`: 772 passed,
  five expected sandbox failures, one skipped, 171.15 seconds (exit 1).
- `pytest-final.log` / `.xml`, fresh `work/c63c-15-final` after the root
  checkout adjustment: **772 passed, five expected sandbox failures, one
  skipped in 171.12 seconds** (exit 1). The runner keeps the sandbox mkdir
  shim, disables cacheprovider, excludes QUIT_SCRIPT and uses a bounded
  300-second per-test timeout; it removes runner-only PYTHONPATH while
  retaining scripts on sys.path.
- `data-verification-final.log`: all 232 input rows preserved except mapped
  paths; 441 references / 157 files verified; zero hash mismatches.
- `scope-audit-final.log`: all changes in the owned envelope, stage rows
  unchanged, no new tracked prefix requiring harness registration.
- `diff-check-final.log`: exit 0.

| Module | Final result |
| --- | --- |
| test_tools_package_notices.py | 397 passed |
| test_tools_package_build.py | 131 passed |
| test_tools_package_smoke.py | 34 passed, one unchanged skip |
| test_tools_package_ffmpeg.py | 158 passed |
| test_release_workflow.py | 52 passed, five sandbox fixture failures |

The five failures are
`test_real_git_gate_restores_checkout_overwrite_and_refuses_invalid_tags`
variants annotated, lightweight, wrong-commit, mismatched-name and
deleted-origin. Each fails in its temporary local fixture's
`git push origin HEAD:refs/heads/main --tags` with restricted-token
CreateFileMapping / Win32 error 5, before exercising the tag gate.
`test-summary.json` records every case and its sandbox classification.
The sole unchanged skip is
`test_non_windows_containment_never_silently_skips` (WP6.5 POSIX proof).
Every other prescribed test passes; this is not a claim that pytest's exit
status is zero or that the real-Git cases have been validated in the cell.

`byte-preservation.log` additionally proves the CRLF licence file's raw and
attribute-filtered Git blob hashes are identical under native-licences -text.
A probe-only false positive was rejected: Windows backslashes in an initial
`git hash-object --path` argument missed the attribute; the corrected
forward-slash control reports the same blob `75b52484ea471f882c29e02693b4f02dba175b5e`.
`desktop-input-audit-summary.log` finds no synthetic desktop-input call in
any turn-15 scratch script. The final convergence read found no additional
in-envelope issue after the checkout adjustment.

**Handoff / STOPPED ITEMS.** None of dispatch 15's items 1-8 is stopped or
left unimplemented. The root annex's external byte-preserved text links are
a presentation choice within item 1(e), not a missing runtime notice.
A delta, B r2, the five real-Git seat reruns, applicable seat artifact checks,
harness/package gate, acceptance/debt entries and release are the dispatcher's
next steps. F-B4 remains CHARC's DR-149 disposition. The supplied B-r1 ledger
counts are one MAJOR, four MINOR and five ADVISORY (F-B10 out of envelope),
all NEW, no REOPENED findings and no reverts; remediation changes both tool
code and tests/data. No new reviewer round was run and no cumulative ledger
file was owned or edited this turn.

Only the nine tracked owned files and 157 new toolchain texts changed.
The dispatcher file list is `work/c63c-15/copied-texts.txt` (157 lines).
No dependency, product source, frozen interface, workflow, fork patch or fork
clone changed. No network fetch, real build, frozen/GUI launch, Docker,
synthetic desktop input, protected-profile/footage/evidence-folder write,
repository Git write, remote push/tag/dispatch or mailbox post was performed.
The prescribed tests alone attempt temporary local Git-fixture writes/pushes.
The seat commits this one logical remediation turn; no commit was attempted.
`depth_input_tokens` is unavailable to this cell; dispatcher read is due at yield.
