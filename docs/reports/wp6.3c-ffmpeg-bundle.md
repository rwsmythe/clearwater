# WP6.3c - FFmpeg bundle

Status: turn 2 edits prepared, 2026-11-05. Fork commit/export, actionlint and
Dockerfile generation belong to the seat. The real asset, lock re-pin, remaining
build work, review, package gate and release are pending.

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
