# WP6.3e - Release workflow fresh-tree fix

Status: turn 2 candidate, 2026-11-07, folding the seat rehearsal of turn 1
(`e9cde49d`, based on `d14a09c1`). Reviewer A,
actionlint, the seat rehearsal, Reviewer B, the package gate and the 1.1.1
release remain pending. Product code, build tools and version are unchanged.

## Failure and fix

The dispatch records release run `42387791040` on `v1.1.0` (`356f2e4d`)
failing before any test ran: `_pytest/tmpdir.py:152 getbasetemp` called
`basetemp.mkdir(mode=0o700)` and raised
`FileNotFoundError: [WinError 3] The system cannot find the path specified:
'D:\a\clearwater\clearwater\work\ci-parallel'`. No draft was created.
The gitignored `work/` parent is absent on a fresh checkout.

`.github/workflows/release.yml:117` now creates `work` with
`New-Item -ItemType Directory -Force -Path work | Out-Null` before pytest
at :118. The pytest command itself is byte-unchanged. Asset staging at :143
also gains `-Force`. No other workflow line changes; action SHAs, uv 0.10.9,
version/annotated-tag gates, draft-only publication and permissions are unchanged.
Checklist step 9 at `docs/release-checklist.md:162` requires a new patch
version on a fixed commit after a pushed tag's workflow-only failure, retaining
the failed tag on origin without a release and naming it in the next notes.

## Work-path audit

Line numbers below refer to the fixed workflow. No other `work/` write can
precede pytest's new parent creation in the Windows job. The release job has
its own checkout and creates its own paths.

| Path / use | Workflow line | Parent creation / fresh-tree disposition |
|---|---|---|
| `work/ci-parallel` (pytest writes) | :118 | NEW explicit idempotent `work` creation at :117, before pytest. |
| `work/release` (build output) | :124 | `build()` calls `write_hidden_import_report()` at `tools/package/build.py:2952`; that function creates `path.parent` with `parents=True, exist_ok=True` at :2340 before writing. FFmpeg download also creates `out/ffmpeg` with parents at :1596; ZIP output creates `out` with parents at :2861. |
| `work/release/$name.zip`, `.zip.sha256`, `dist-onedir/$name/Clearwater/THIRD_PARTY_NOTICES.md` (asset inputs) | :133-135 | Reads of build outputs, checked as leaf files at :137-140 before staging writes; a failed build exits at :125. |
| `work/release/$name.zip.sha256` (commit annotation) | :142 | Appends only after the build and the leaf-file checks; its parent already exists. |
| `work/release-assets` (mkdir and copies) | :143, :145 | CHANGED mkdir adds `-Force`; the explicit step creates the destination before `Copy-Item`. The `work` parent already exists from :117. |
| `work/release-assets/*` (upload) | :152 | Read-only glob over the staging destination created at :143; missing files are an error. |
| `work/release-assets` (download in release job) | :192 | `actions/download-artifact` creates its configured extraction destination, including parents, in this separate checkout. |
| `work/release-body.md` (notes write) | :205, :208 | Embedded Python explicitly calls `body.parent.mkdir(parents=True, exist_ok=True)` at :206 before writing. |
| `work/release-assets/*.zip`, `*.zip.sha256`, `THIRD_PARTY_NOTICES.md` (draft attachments) | :221-223 | Reads of the preceding download's destination; `fail_on_unmatched_files: true` at :219. |

## Round 0 - static rehearsal prediction

No fresh-tree test run was performed in the cell. Static inspection predicts
TEN failures and TWO setup errors in the workflow's parallel leg, all in
`tests/test_lookcheck_deep.py`, assuming FFmpeg/ffprobe are available. Each is
unmarked for footage and reaches an unguarded `load_local_config()`; absent
`clearwater.local.toml` raises `LocalConfigError` before synthetic work begins.
The prediction and its test-module line references describe the turn-1 snapshot.

| Test (all in `tests/test_lookcheck_deep.py`) | Definition line | Config dependency / expected result |
|---|---|---|
| `test_an_interrupted_chapter_scan_resumes_and_matches_an_uninterrupted_one` | :403 | Direct call at :406; FAIL. |
| `test_a_usable_cache_loads_and_every_kind_of_unusable_one_is_refused` | :469 | `_write_cache()` at :462-463; FAIL. |
| `test_finish_refuses_a_stale_cache_instead_of_writing_scan_json` | :518 | `_write_cache()` at :462-463; FAIL. |
| `test_discard_cache_removes_the_cache_and_the_interrupted_run_file` | :528 | `_write_cache()` at :462-463; FAIL. |
| `test_an_interrupted_run_file_from_other_rules_is_discarded_not_resumed` | :537 | Direct call at :538; FAIL. |
| `test_the_deep_pack_has_its_layout_and_the_index_names_every_file` | :596 | `deep_pack` fixture :565, :569 -> `_deep_roots()` :559-561; ERROR. |
| `test_the_deep_page_head_sections_and_wording` | :632 | Same `deep_pack` fixture chain; ERROR. |
| `test_a_candidate_that_is_also_a_still_is_corrected_once` | :656 | `_deep_roots()` :559-561; FAIL. |
| `test_deep_frames_must_agree_with_scan_json` | :771 | `_deep_roots()` :559-561; FAIL. |
| `test_encode_deep_clip_refuses_stale_inputs_before_it_runs_any_tool` | :899 | `_deep_roots()` :559-561; FAIL. |
| `test_clear_clip_removes_clips_statistics_and_frames_only` | :918 | `_deep_roots()` :559-561; FAIL. |
| `test_the_page_links_only_a_verified_clip_of_the_current_deepest_frame` | :931 | `_deep_roots()` :559-561; FAIL. |

Two additional conditional failures outside the workflow's marker expression
also lack `footage`: `tests/test_lookcheck_deep.py:988`
`test_the_deep_clip_is_staged_smoothed_encoded_checked_and_pruned` calls
`_deep_roots()` at :998, and `tests/test_noise_experiments.py:553`
`test_the_runner_records_one_deep_frame_under_two_settings` loads config at
:558. Both are `gpu` + `slow`, and skip first if GPU selection fails; if a GPU
is available they fail without config. They are excluded from the rehearsal's
parallel leg.

`tests/conftest.py:294-297` makes its guard inert without config; :343-361
skips footage-marked tests when config/footage is missing. The GX011627
fixtures reach config at :760 / :854 but their real-footage consumers carry
`footage`. `tests/fixture_plugin.py` supplies committed/generated synthetic
samples without local config or footage. Other inspected config-dependent
helpers either use disposable config, catch missing config and skip/return,
or belong to footage-marked tests. Turn 1 left these predicted defects unchanged.
The rehearsal below confirms the prediction and records CHARC's ruled fold.

## Turn 1 - pins and validation

`test_parallel_tests_create_basetemp_parent_before_pytest` at
`tests/test_release_workflow.py:460` parses the step's `run:` block, derives
the parent from `--basetemp=`, and at :479 asserts that the tokenized
`New-Item -ItemType Directory -Force -Path <parent> | Out-Null` command is
present BEFORE the pytest line. `test_release_asset_staging_creates_directory_with_force`
at :484 pins the idempotent staging mkdir before the first copy. No existing
assertion required an update; the existing command/marker/build pins still pass.

RED: extracted `git show 356f2e4d:.github/workflows/release.yml` to
`work/wp6.3e/release-356f2e4d.yml`; a scratch pytest plugin redirects only the
workflow fixture's source path. Both new tests FAIL on their intended assertions:
`2 failed, 57 deselected`, exit 1 (`work/wp6.3e/red5.log`).

Final validation logs and exit-code files are under `work/wp6.3e/`:

| Check | Result | Log |
|---|---|---|
| `uv run --no-sync ruff check .` | Exit 0, all checks passed | `ruff.log` |
| `uv run --no-sync ruff format --check .` | Exit 0, 337 files already formatted | `format.log` |
| `uv run --no-sync mypy` | Exit 0, no issues in 166 source files | `mypy.log` |
| `uv run --no-sync mypy --platform darwin` | Exit 0, no issues in 166 source files | `mypy-darwin.log` |
| Isolated pytest: workflow + package-build modules | Exit 1, 185 passed / 5 expected real-Git failures; both new pins GREEN | `pytest-final.log` |

The five failures are cases `annotated`, `lightweight`, `wrong-commit`,
`mismatched-name`, `deleted-origin` of
`test_real_git_gate_restores_checkout_overwrite_and_refuses_invalid_tags`.
All stop at the fixture's local Git push (exit 128, Git's `sh.exe` reports a
`CreateFileMapping` fatal error), before the gate assertion.
The seat must run these unrestricted. No test contacts a network remote.

The scratch runner redirects APPDATA, LOCALAPPDATA and all XDG roots under
`work/wp6.3e/profiles`, blocks PySide6/shiboken6 imports, disables plugin
autoload (including pytest-qt), loads the timeout plugin explicitly, and keeps
the required startup-test exclusion. The RED proof and final run load
`sandbox_mkdir_shim` with the cache provider disabled and a fresh basetemp.
The final run uses `work/c63e-1b`. `PYTHONPATH=scripts` bootstraps the shim;
the runner then removes the environment variable, retaining `sys.path`, because
the build tests correctly refuse ambient PYTHONPATH. Offline/no-sync commands
select the existing shared environment via `UV_PROJECT_ENVIRONMENT` because
the worktree initially had no populated environment. Initial runner attempts
(missing pytest, pytest-qt autoload, old-workflow text encoding, and ambient
PYTHONPATH) were corrected in scratch only; they are not product findings.

Verification loop: missing parent and non-idempotent staging were suspected,
confirmed by the two RED assertions, fixed in the workflow, and verified GREEN.
The static path audit found no additional gap. The final scoped run found no
other failure beyond the expected real-Git sandbox limitation. No false-positive
product finding, deviation in scope, or product/build-tool change. Actionlint
is unavailable offline and remains a seat check; no build, GUI, footage read,
tag, push to an external remote, release or mailbox operation was performed.

The independent scratch check `work/wp6.3e/verify_gate.py` exited 0
(`verification.log`): the workflow equals the base plus exactly the two
specified edits, the pytest command and every protected line are unchanged,
and the pins reject removal of the parent mkdir, loss of either `-Force`, and
moving the parent mkdir after pytest. This final pass found nothing new.
`git diff --check` also exited 0 (`diff-check.log`).

## Rehearsal

### Seat record and prediction comparison

The seat supplied the rehearsal record for `e9cde49d` in dispatch 2; the cell
has not read the external evidence directory. Record location:
`clearwater-review-evidence/wp6.3e/seat/rehearsal/e9cde49/`.
The clone had no `work/`, local TOML or footage path and used the workflow's
own run blocks. Run 1 reached the seat's 30-minute sync limit downloading
CUDA wheels; this was an infrastructure limit, not a code finding. Run 2
resumed the same clone and synced successfully (exit 0).

Run 2 parallel tests exited 1 in 588 s:
`10 failed, 8353 passed, 210 skipped, 5 warnings, 2 errors`.
The ten failures and two setup errors are EXACTLY the twelve identities and
classifications in the round-0 prediction table above. Each reached
`tools/local_config.py:108` with the clone's local TOML absent. No prediction
mismatch and no additional test failure. Build/staging evidence was not supplied
with this turn; the seat continues that work independently.

**[MAJOR] R-F1, confirmed, fixed in tests:** twelve synthetic tests depended on
the owner's local config for a guard root. CHARC ruling `a0df6f36`
(`a0df6f3668e4d109`, 2026-11-07T16:05Z) requires a stand-in rather than a skip.
One `_footage_root(tmp_path)` helper at `tests/test_lookcheck_deep.py:34`
returns the configured footage path unchanged; on `LocalConfigError` only,
it creates and returns an empty `tmp_path/footage-stand-in`, with parents and
`exist_ok=True`. Outputs stay in sibling synthetic-output folders; nothing is
written inside the stand-in after its creation.

The four readers now use this helper: the interrupted scan at :458,
`_write_cache()` at :515, the stale interrupted scan at :590, and
`_deep_roots()` at :613. Both existing root helpers already accept the
temporary-root argument they need, so their signatures are unchanged.
The real-chapter scan, its footage marker and lookup/skip logic are untouched.
No marker, conftest, workflow, product-code or build-tool change was made.
Both existing GPU/slow test bodies are unchanged.

### Turn 2 proofs and validation

Proof (a), local TOML present: the isolated cell run of deep-lookcheck plus
release-workflow tests reports `5 failed, 98 passed, 2 deselected`, exit 1,
in `work/wp6.3e/turn2-pytest.log` (`--basetemp=work/c63e-2`). All 44 selected
deep-lookcheck cases passed, as did 54 release-workflow cases. Only the same
five sandbox real-Git cases failed (local fixture push, exit 128,
`CreateFileMapping` fatal error). The `gpu`/`slow` case and real-chapter scan
were deselected: the latter is excluded explicitly from the cell's `-k` to
honor the no-footage-read rule. This is synthetic coverage with the owner's
TOML present; the whole-module proof including real footage remains at the seat.

Proof (b), sandbox form: a scratch pytest plugin replaces ONLY this test
module's `load_local_config` with a function raising `LocalConfigError`.
There is no supported config environment override; the actual local TOML was
never renamed, moved or edited. The same synthetic module selection reports
`44 passed, 2 deselected`, exit 0, in `work/wp6.3e/turn2-missing.log`
(`--basetemp=work/c63e-2-missing`). Session-end inspection confirmed all
27 stand-in folders remained empty. This simulates missing config at every
synthetic reader; actual fresh-clone absence is proved by the seat's final rerun.

The two new helper tests at :51 and :63 were first RED with the helper absent
(`2 failed, 44 deselected`, exit 1, `turn2-red.log`), then GREEN in both runs.
Their assertions kill these mutations:

| Assertion | Mutation caught |
|---|---|
| Configured result equals the supplied path | Always return a fallback or another root. |
| Configured folder remains absent | Create/write the configured footage root. |
| No stand-in exists for valid config | Create an unnecessary fallback on the configured branch. |
| Missing-config result equals the nested root's `footage-stand-in` | Use another name or a root outside the supplied temp folder. |
| Fallback `is_dir()` | Return a nonexistent path without creating the directory. |
| Fallback contents are empty | Plant an output in the guard root. |
| Repeated fallback call returns the same root | Omit `exist_ok=True`; the nested input also exercises parent creation. |

Static checks all exited 0: `ruff check .` (all checks passed),
`ruff format --check .` (337 files formatted), `mypy` and
`mypy --platform darwin` (166 source files each). Logs and exit-code files:
`work/wp6.3e/turn2-{ruff,format,mypy,mypy-darwin}.*`.
The runner retains redirected profiles, blocked GUI imports, explicit timeout
plugin, the startup-test exclusion, sandbox mkdir shim and disabled cache provider.
Commands remain offline and no-sync using the existing shared environment.

Verification loop: the seat independently confirmed the predicted config
dependency; the ruled test-only fix preserves configured behavior and passes
the missing-config simulation without dropping synthetic coverage. No further
in-scope failure was found. `turn2-verification.log` (exit 0) confirms the two-file
envelope, exactly four changed existing function bodies, and unchanged existing
markers, real-chapter body and GPU/slow body. `git diff --check` also exited 0
(`turn2-diff-check.log`). Reviewer A has not run yet. No STOP item or scope
deviation; full-module real-footage proof, unrestricted Git, actionlint,
final-head rehearsal and both reviews remain seat work.

Seat re-run on the final head: (the seat fills)
