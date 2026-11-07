# WP6.3e - Release workflow fresh-tree fix

Status: turn 4 candidate, 2026-11-07, folding Reviewer A r2's two MINORs on
turn 3 (`8a30d6d4`, after `c66af644` and `e9cde49d`, based on `d14a09c1`).
The whole-selection spy run, final runner-PATH seat rehearsal, actionlint,
Reviewer A r3 (FINAL), Reviewer B, the package gate and
the 1.1.1 release remain pending. Product code, build tools and version are unchanged.

## Failure and fix

The dispatch records release run `42387791040` on `v1.1.0` (`356f2e4d`)
failing before any test ran: `_pytest/tmpdir.py:152 getbasetemp` called
`basetemp.mkdir(mode=0o700)` and raised
`FileNotFoundError: [WinError 3] The system cannot find the path specified:
'D:\a\clearwater\clearwater\work\ci-parallel'`. No draft was created.
The gitignored `work/` parent is absent on a fresh checkout.

`.github/workflows/release.yml:117` now creates `work` with
`New-Item -ItemType Directory -Force -Path work | Out-Null` before pytest
at :118. Turn 3 adds only `-rs` to the pytest command for skip visibility.
Asset staging at :143 also gains `-Force`. No other workflow line changes;
action SHAs, uv 0.10.9,
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

Outside the workflow's marker expression,
`tests/test_lookcheck_deep.py:1040` (turn-2 line; formerly :988)
`test_the_deep_clip_is_staged_smoothed_encoded_checked_and_pruned` is `gpu` +
`slow` and now inherits the stand-in through `_deep_roots()`.
`tests/test_noise_experiments.py:553`
`test_the_runner_records_one_deep_frame_under_two_settings` carries
`@pytest.mark.footage` at :549, as well as `gpu` + `slow`, and skips when the
local TOML is missing; it does not fail for a missing TOML. Both are excluded
from the rehearsal's parallel leg. These corrections dispose of Reviewer A F-2.

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

## Runner PATH (Reviewer A F-1)

**[MAJOR] F-1 confirmed, guard fold applied.** The seat and CHARC report that
the GitHub runner image `windows-2025-vs2026` has neither FFmpeg nor ffprobe
in `actions/runner-images/images/windows/Windows2025-VS2026-Readme.md`.
This cell is offline and did not fetch that list. The successful rehearsal on
`c66af644` inherited the laptop's WinGet Links PATH: sync, parallel tests
(`8367 passed, 210 skipped`), build (no window) and staging each exited 0.
That record did not model the runner's absent tools.

The seat then removed every PATH entry containing `ffmpeg.exe` or `ffprobe.exe`
and set `CUDA_VISIBLE_DEVICES=-1`. Parallel results were
`149 failed, 7522 passed, 903 skipped, 3 errors`. The 152 failed/error node IDs
are staged read-only at `work/wp6.3e/seat/runner-path-node-ids.txt`.
The seat's causal split on those IDs found (A) tools absent, GPU visible:
the same 152 failures/errors; (B) tools present, GPU hidden: 152 passed.
FFmpeg absence is the sole confirmed cause; no GPU marker changes are needed.
Leaving System32's `nvidia-smi` visible is a stated runner-PATH simulation limit.

CHARC rulings `3b0e47f3383dc0f1` and `875e398addfd6ded` grant test-only guards
in the following 15 modules. Counts are affected node IDs; sites count new
guards, not parametrized cases. All modules contain tests outside the granted
FFmpeg-dependent cases, so none receives a module-wide guard. The fixture
policy is `tests/fixture_plugin.py:274-277`: skip with `SKIP_NO_FFMPEG` when
`video.tools_available()` is false. Existing module-local skip styles are retained.

| Module under `tests/` | Nodes | Added sites / form | Why / evidence in the final source |
|---|---:|---|---|
| `test_app_composition.py` | 1 | 1 per-test `usefixtures("ffmpeg_tools")` | :127 tests the real unreadable-video refusal, which first probes. |
| `test_color_swscale.py` | 10 | 5 per-test fixture marks | :96, :113, :263, :338, :353 probe committed videos before checking color arguments; other tests use constructed streams. |
| `test_fixtures.py` | 1 | 1 existing `needs_ffmpeg` decorator | :634 calls `video.measure()` on planted MP4 user data; other manifest/still tests need no tools. |
| `test_headless_export.py` | 1 | 1 per-test fixture mark | :483 runs the real video refusal through the headless runner. |
| `test_io_video_encode_units.py` | 2 | 2 per-test fixture marks | :1237 and :1260 stub subprocess results but `verify.read_packet_table()` still resolves ffprobe. |
| `test_io_video_probe.py` | 71 | 36 per-test fixture marks | :88 onward probe real samples or check the real locator (:542); parser/filter and missing-tool tests stay unguarded. |
| `test_io_video_spawn.py` | 2 | 1 per-test fixture mark | :302 spawns each real tool to prove FFREPORT suppression. |
| `test_lookcheck_deep.py` | 4 | 2 per-test existing-style `skipif`; 1 fixture dependency | :174 calls `scan.scan_document()` (tool versions); :618 `deep_pack` generates/extracts a clip before its two consumers; :710 generates/extracts a clip. |
| `test_photo_verify.py` | 24 | 11 per-test fixture marks; 1 conditional fixture guard | :98 onward use the FFmpeg orientation oracle; :122 guards all orientation cases; :1571 guards only `compare_poses`; :1741 guards both larger-size-difference cases, which call real FFmpeg before corrupting its output. |
| `test_reviewpack.py` | 24 | 17 per-test fixture marks; 2 conditional fixture guards | :539 onward probe/copy/extract/render real media, including failure tests that first probe; :1663 guards only video, :1908 only non-photo failures. |
| `test_wp321_bench.py` | 2 | 2 per-test fixture marks | :64 and :95 run the CPU video bench's real probe/decode. |
| `test_wp321_device_frames.py` | 7 | 5 per-test fixture marks | :184, :196, :300, :331, :361 decode or open/close a real video sink; other cases are mocked/device-selected. |
| `test_wp321_fft_release.py` | 4 | 4 per-test fixture marks | :228, :240, :249, :263 run real video jobs through release boundaries. |
| `test_wp42_composition.py` | 1 | 1 per-test fixture mark | :151 expects a cache-folder refusal after the real probe succeeds. |
| `test_wp44_mov_input.py` | 1 | 1 fixture dependency | :98 `qt_mov` generates the synthetic QuickTime source; routing and command-assembly cases stay unguarded. |

Total after turn 4: 155 guarded node IDs, 94 added guard sites (turn 3: 152 IDs,
93 sites). Conditional guards request the
existing fixture through `request.getfixturevalue("ffmpeg_tools")`; they change
no existing assertion or test operation. `deep_pack` and `qt_mov` request the
fixture before generating any media. There are no changes to conftest,
fixture_plugin, product/build code, or selection markers (`gpu`, `footage`,
`gui`, `slow`, `fullclip`). No new dependency or network test is introduced.

No purpose-of-tool-absence test occurs among the 152. These existing controls
outside the list remain unguarded:

- `test_io_video_probe.py::test_a_missing_ffprobe_is_a_clear_error`
- `test_io_video_encode_units.py::test_missing_ffmpeg_is_a_reason_not_an_exception`
- `test_fixtures.py::test_plugin_skips_a_generated_sample_when_ffmpeg_is_absent`
- `test_fixtures.py::test_plugin_hands_out_committed_samples_without_ffmpeg`
- `test_fixtures.py::test_cli_rejects_an_unknown_group_and_reports_missing_ffmpeg`

The adjacent mocked capability controls
`test_an_encoder_missing_from_the_build_is_named` and
`test_a_failed_listing_makes_every_encoder_unavailable` also stay unguarded.
The existing `ffmpeg_decode` failure parameter in photo verification remains
unguarded, as do both photo aid cases. Assertions expecting unsupported/unreadable/parse results
are preserved, never widened to accept missing-tool errors.

**Visibility and advisories:** the workflow's pytest argv now reads
`uv run pytest -q -rs -n 4 ...`; adding `-rs` is its only turn-3 change.
`test_order_parallel_marker_and_build_flags_match_local_contract` pins the new
argv. RED before the workflow edit: `1 failed in 0.17s`, on the argv assertion
(`work/wp6.3e/turn3-red.log`, exit 1). F-2's two static-prediction sentences
are corrected above (**[MINOR] F-2 confirmed, corrected**).
**[MINOR] F-4 confirmed, fixed:** checklist step 9 now names
`docs/release-notes-<version>.md`, matching the workflow's versioned lookup.
F-3 has no change, per CHARC's conftest precedent ruling.

### Turn 3 validation

Cell logs, exit-code files, the isolated runner and skip XML are under
`work/wp6.3e/turn3-*`. All uv invocations are offline/no-sync with the existing
shared environment. All pytest runs load `sandbox_mkdir_shim`, disable the
cache provider and plugin autoload, load the timeout plugin explicitly, exclude
the seat-only startup test and use fresh basetemps. APPDATA, LOCALAPPDATA and
all XDG roots point inside disposable `turn3-profiles`; GUI imports are blocked
in-process and in inheriting children through scratch `sitecustomize`.

- FFmpeg present, staged target list, `work/c63e-3p`: exit 0,
  `152 passed in 79.03s (0:01:19)` (`turn3-present.log`).
- FFmpeg absent, the same list, `work/c63e-3a`: exit 0,
  `152 skipped in 1.11s` (`turn3-absent.log`). Before importing pytest, the
  runner strips every PATH entry holding either executable and asserts both
  `shutil.which()` results are `None`; the child environment inherits that PATH.
  No failed tests or setup errors. Skip reasons are checked in `turn3-absent.xml`.
- `ruff check .`: exit 0, `All checks passed!`; `ruff format --check .`:
  exit 0, `337 files already formatted`.
- `mypy` and `mypy --platform darwin`: both exit 0,
  `Success: no issues found in 166 source files`.

- All 15 touched modules, whole parallel selection, `work/c63e-3m`: exit 1,
  `6 failed, 1359 passed, 37 deselected, 6 warnings in 202.33s (0:03:22)`
  (`turn3-modules.log`, case results in `turn3-modules.xml`). The six failures
  are outside the 152-node fold. An isolated rerun using the original HEAD
  (`c66af644`) test definitions reproduced the same six identities:
  `6 failed in 10.45s` (`turn3-baseline.log`, exit 1). The scratch runner
  recompiles the original test modules into their existing module namespaces
  and replaces the six collected test objects; the unchanged audit fixture
  runs normally. No tracked file or product revision is swapped for that check.
  `turn3-baseline-comparison.log` records the comparison. They are:

  | Unchanged test | Observed limitation / disposition |
  |---|---|
  | `test_fixtures.py::test_generators_write_only_inside_their_output_folders` | Audit records a `nul` write. Baseline reproduces; no edit authorized. |
  | `test_fixtures.py::test_generators_read_only_their_own_code_and_libraries` | Shared environment resolves editable Clearwater imports under the main tree's `src`, outside this worktree's allowed audit roots. Baseline reproduces; unrestricted/local-environment seat rerun required. |
  | `test_fixtures.py::test_ffmpeg_is_told_to_write_only_into_the_output_folders` | Audit records 55 media-tool processes plus `cmd.exe /c ver`. Baseline reproduces; no edit authorized. |
  | `test_headless_export.py::test_g1_inside_sees_every_spelling_of_the_same_folder` | Restricted token cannot stat `\\localhost\C$\` (`WinError 5`). Baseline reproduces; seat rerun required. |
  | `test_headless_export.py::test_g1_main_refuses_every_footage_check_through_another_spelling[unc]` | Same administrative-share denial; baseline reproduces; seat rerun required. |
  | `test_headless_export.py::test_g1_the_redactor_hides_the_extended_spellings` | Same administrative-share denial; baseline reproduces; seat rerun required. |

- Workflow module whole, `work/c63e-3w`: exit 1,
  `5 failed, 54 passed in 1.76s` (`turn3-workflow.log`). All five failures
  are the previously recorded real-Git cases of
  `test_real_git_gate_restores_checkout_overwrite_and_refuses_invalid_tags`:
  `annotated`, `lightweight`, `wrong-commit`, `mismatched-name`, `deleted-origin`.
  Their fixture's local push exits 128 with Git `sh.exe`'s `CreateFileMapping`
  fatal error, before any gate assertion. Both fresh-tree pins and the updated
  `-rs` argv pin pass. The seat must run the five Git cases unrestricted.
- Absent-tools controls, `work/c63e-3-controls`: exit 0,
  `11 passed in 1.06s` (`turn3-controls.log`). This historical run covered the
  five tool-absence controls listed above, the two mocked capability controls,
  three valid unguarded parameter cases and the false pass fixed in R2-1 below.
- Collection before and after: the touched modules retain exactly the same
  1,402 node IDs. Their disjoint legs are 1,365 parallel + 37 serial + 0 fullclip
  = 1,402 all (`turn3-collection.log`, exit 0). The empty scoped fullclip
  collection returns pytest's no-tests exit 5; all/parallel/serial return 0.
  No node or selection marker moves. These are scoped counts, not the full-suite
  gate count; the laptop parallel floor remains 8,367 passed / 210 skipped,
  to be checked at the seat against the final package head.
- Independent delta check, `turn3-verification.log`: exit 0. Removing only
  the 93 new guards and their fixture arguments restores every granted module's
  original AST exactly, including assertions, parameter sets and selection
  markers. The workflow, pin and checklist have exactly their requested edits;
  only owned files changed. The staged node-list SHA256 is unchanged:
  `485cca894a2ff25b5081feac0494ad695108f51907c18ca4712f6ba62e7f8dce`.
  XML confirms 150 `SKIP_NO_FFMPEG` skips and two `ffmpeg not on PATH` skips.
- `git diff --check`: exit 0 (`turn3-diff-check.log`).

Verification loop: the seat confirmed F-1 by the causal split; the guard fold
then passed all 152 with tools and skipped exactly those 152 without them.
Broader module verification exposed six failures outside the fold; independent
baseline reproduction rejected them as turn-3 regressions. No change was made
to those tests, their fixtures or the environment under test to suppress them.
The final delta/skip/collection pass found no additional in-scope issue.
F-2/F-4 are fixed and F-3 is left unchanged as ruled. Reviewer A r2 and
Reviewer B remain the dispatcher's next review steps; there is no new review
verdict claimed here. This turn bundles F-1, the `-rs` pin and the two advisory
text folds as explicitly dispatched; no product-code fix, revert or reopened
finding. The cumulative review ledger remains at the seat (outside this
turn's owned-file envelope).

STOPPED validation items: the six unchanged whole-module cases and the five
real-Git cases above need the seat's unrestricted runs; their bodies are not
in this fold's edit grant. Actionlint is unavailable in the offline cell and
remains a seat check. The whole laptop parallel floor, full runner-PATH
rehearsal on a new clone (sync/tests/build/staging), actual expected runner
skip count, both reviews, package gate and release remain COMMISSIONED to the
seat by this dispatch. No network fetch, build, GUI launch, footage read/write,
owner-profile write, evidence-folder write, project Git write, tag, push or
mailbox operation was performed. The failed `v1.1.0` tag is untouched.

Seat runner-path rehearsal on the final head: (the seat fills)

### Reviewer A r2

The seat's Claude review of `8a30d6d4` returned `NO_NEW_CRITICAL_MAJOR`;
F-1 is CLOSED by execution. The seat reports the 152 pass/skip proof, the six
cell-only failures passing, all 59 workflow tests passing (including real Git),
and unchanged full parallel collection of 8,577. These are seat-supplied results.

- **[MINOR] R2-1 confirmed, fixed:** all orientation parameters call the real
  FFmpeg oracle, including `exif-only`. A missing executable produced
  `oracle_failed` and the expected `orientation_ok=False`, masking the intended
  size/pose check. The guard is now unconditional `usefixtures("ffmpeg_tools")`;
  the conditional and added `request` argument are removed. EXIF-only is no
  longer a tool-absent control.
- **[MINOR] R2-2 confirmed, fixed:** both `two-pixels` and `tile` call
  `pv.verify_orientation()`. Their `corrupted()` wrapper unconditionally calls
  the saved real `subprocess.run` before editing the decoded PNG in either
  damage branch. Missing FFmpeg therefore satisfied `oracle_failed` before the
  size gate ran. Both parameters now have the unconditional fixture guard.
- **R2-3 advisory, no action:** guarding the whole lookcheck test also drops
  its non-FFmpeg checks, as permitted by the no-logic-change ruling.

CHARC ruling `616c87d6c5d8b47a` grants the two new in-envelope MINOR folds.
No product code, assertions, test operations, parameter sets or selection
markers change; no tests are added/removed, reverts or reopened findings.
The photo row now covers 24 cases at 12 sites; package totals are 155 guarded
cases at 94 sites.

Turn 4 validation, logs/exit codes under `work/wp6.3e/turn4-*`:

- Ruff check/format: exit 0, `All checks passed!` / `337 files already formatted`.
- Mypy and darwin mypy: exit 0 each, `Success: no issues found in 166 source files`.
- Photo whole parallel selection, present (`work/c63e-4p`): exit 0,
  `122 passed, 1 deselected, 6 warnings in 20.87s` (`turn4-photo-present.log`).
- Photo whole parallel selection, absent (`work/c63e-4a`): exit 0,
  `98 passed, 24 skipped, 1 deselected in 11.51s` (`turn4-photo-absent.log`).
- Original 152-node list, present (`work/c63e-4tp`): exit 0,
  `152 passed, 6 warnings in 81.59s (0:01:21)` (`turn4-target-present.log`).
- Original 152-node list, absent (`work/c63e-4ta`): exit 0,
  `152 skipped in 1.47s` (`turn4-target-absent.log`): 150 standard fixture
  reasons and two existing lookcheck reasons. All four runs have zero failures/errors.

XML confirms these reviewed nodes in `tests/test_photo_verify.py`:

| Node | FFmpeg present | FFmpeg absent |
|---|---|---|
| `test_orientation_matches_generated_upright[both]` | PASSED | SKIPPED, `SKIP_NO_FFMPEG` |
| `test_orientation_matches_generated_upright[exif-only]` | PASSED | SKIPPED, `SKIP_NO_FFMPEG` |
| `test_orientation_matches_generated_upright[irot-only]` | PASSED | SKIPPED, `SKIP_NO_FFMPEG` |
| `test_orientation_matches_generated_upright[neither]` | PASSED | SKIPPED, `SKIP_NO_FFMPEG` |
| `test_r9_decode_rejects_larger_size_difference[two-pixels]` | PASSED | SKIPPED, `SKIP_NO_FFMPEG` |
| `test_r9_decode_rejects_larger_size_difference[tile]` | PASSED | SKIPPED, `SKIP_NO_FFMPEG` |

The existing isolated runner retains the sandbox shim, disabled cache provider,
GUI import blocks, disposable APPDATA/LOCALAPPDATA/XDG roots, bounded tests and
startup-test exclusion. Runs are offline/no-sync with fresh basetemps; absent
mode strips executable-holding PATH entries and asserts both tools are absent.
`turn4-verification.log` (exit 0) confirms exactly the two authorized test edits,
unchanged 122 selected photo IDs and staged 152-node list, only two owned files
changed, and the empty spy section. `git diff --check` exits 0
(`turn4-diff-check.log`). The final delta/outcome pass finds no additional issue.

The seat's rehearsal on `8a30d6d4` is retained as the pre-fold record
(record path: the seat fills). The rehearsal of record requires a NEW fresh
clone on the final turn-4 head, or turn 5 if the spy finds more false passes.
The whole-selection spy, its plugin/record paths and node dispositions belong
below; the cell does not run it. Spy, final-head rehearsal, A r3 FINAL, B,
laptop floor and release gates remain COMMISSIONED to the seat. No stopped
cell item or scope deviation; no network fetch, build, GUI launch, footage
access, owner-profile/evidence-folder write, project Git write, tag, push or
mailbox action.

## Spy run (runner PATH, the seat fills)
