# WP6.3b accept record (orchestrator generations 50-51, 2026-11-05)

**Package:** WP6.3b, the Windows release path WITHOUT the FFmpeg bundle (Seat-proof split ruling: 6.3b accepts WHOLE; the FFmpeg bundle, `--zip`, the FFmpeg smoke / V4 / `hevc_nvenc` rows, the FFmpeg notices rows, the root FFmpeg row and the 1.1.0 draft release are WP6.3c's). It delivers:
- `.github/workflows/release.yml`: tag-push / dispatch triggers; every action pinned to a 40-hex SHA; `setup-uv` with `enable-cache: false` and the uv 0.10.9 `checksum:`; job-level `UV_FROZEN` / `UV_NO_SYNC` / `UV_PYTHON_PREFERENCE`; an ANNOTATED-tag gate that re-fetches the tag from origin after checkout and requires it to peel to `GITHUB_SHA`; the built commit in the `.sha256` sidecar and the draft body; refusal of a published release; draft-only;
- `tools/package/build.py`: PyInstaller under a SANITIZED PATH; a post-build native ORIGIN check (byte-identity to the build interpreter, the venv's locked wheels' RECORDs or the bootloader; natives found by extension AND magic bytes); trust limited to the venv's purelib / platlib, refusing `PYTHONPATH` / `PYTHONHOME` / `PYTHONUSERBASE`; `--notices`; `--smoke`; a dedicated `BuildEnvironmentError`;
- `tools/package/notices.py` + `tools/package/native-licences/`: the artifact notices generator, fail-closed (every file, PYZ module, `base_library.zip` member and PKG entry owned by exactly one row unless `co_licensed_with`), with THREE strict provenance kinds (`release-archive`, `git-tree`, `proprietary-redistributable`), SciPy's namespace mapping and vendored-components rule, and the census rows (OpenSSL, libffi, the MSVC runtime (11 files), Mesa + LLVM, five SciPy vendored components) with byte-exact seat-fetched texts;
- `tools/package/smoke.py`: the headless smoke rows in a Windows Job Object (assigned before resume, breakaway denied, a survivor census, bounded pipe waits);
- `src/clearwater/__main__.py` / `app/main.py`: the fatal-error hooks (log + stderr, `os._exit(1)`, a presenter bounded at 30 s on every path and skipped on `offscreen` / `minimal`); the frozen-only GPU cache variables (`setdefault`);
- `docs/release-checklist.md` v2; `docs/user-guide.md` (the 1.1.0 sections marked "from 1.1.0", with pointers to the v1.0.0 instructions); the limited root `THIRD_PARTY_NOTICES.md` edits; `.gitattributes`.

**THE LIMIT, IN WORDS (Reviewer B r1 MAJOR 1, carved to WP6.3c):** the artifact notices do NOT yet cover third-party components COMPILED INTO carried natives (HACL*, expat and libmpdec in CPython's natives; FreeType, HarfBuzz, libpng, PCRE2 and libjpeg in Qt's). WP6.3c closes this before any release (its brief's owned item; a register row owned by 6.3c). No artifact is released from WP6.3b.

**The record:**
- **Brief:** `docs/briefs/wp6.3b-brief.md`, FINAL (CHARC gen 16), with every rulings tail: Round-0, Turn-3, Turn-6, Turn-9, Turn-11, Seat-proof split, Reviewer A r1, Stage-1, Turn-17 (CHARC gen 16); Turn-18, Reviewer A r3, Reviewer B r1, Reviewer B r2 (CHARC gen 17); and CHARC's status rulings of 17:31Z (turn 21's bound) and 19:2xZ (B r3's advisories: 1, 2, 3, 5 carried to WP6.3c; 4 a record line; 6 corrected here).
- **Lane: Codex `implementer-codex-sol-high`** (the lower weekly pace at commission; gen 49's reading: Codex 7 % / 0.433, Claude 61 % / 1.362). Turns 1-23; sessions and depths in the report and `cell\turn-N.driver.stdout`. Generation 50's sessions, depth at yield (of 475,000): `01a1ac75` t19 (RESUMED from t18's 99,129) 170,321, retired; `01a1aca5` t20 174,245; `01a1acc4` t21 91,904; `01a1ace3` t22 180,046; `01a1ad0c` t23 111,793.
- **Reviewers were the other model (Claude) in both nets**, each a read-only `claude -p` process at the seat (`codex_cell.py review`) on the detached copy `.worktrees/wp6.3b-rA`; every prompt banned `run_in_background`; every `review.txt` was checked to be the full report.
- **Report:** `docs/reports/wp6.3b-release-workflow.md`. **Correction (B r3 adv 6):** its turn-23 status line "the real-git proof BLOCKED / pending" is SUPERSEDED: the seat ran it outside the sandbox (`seat\t23-real-git-proof.md`: RED at `4e848bf2`'s workflow, [annotated] "Release requires an ANNOTATED tag"; GREEN at `260c63ae`, 3 of 3), and B r3 re-ran it with checkout's exact fetch shape.
- **Evidence:** `C:\Users\rwsmy\clearwater-review-evidence\wp6.3b\`: `cell\` (dispatches, prompts, returns, transcripts 1-23); `A\r1`, `A\r2`, `A\r3`; `B\r1`, `B\r2`, `B\r3`; `seat\` (the census inputs, `native-licences-provenance.md`, `stage1b-notices-read.md`, `smoke-uia\run1`, `dll-origin-stage1{b,c,d}.txt`, `uv-0.10.9-checksum.md`, `t23-real-git-proof.md`); `gate\` (copied from the seat folder at this accept).

**Candidate:** branch `wp6.3b`, base `50a25b3b` (the rebase after t14). The gate's head is `260c63ae` (turn 23).

**Footprint** (`git diff --name-only 50a25b3b..260c63ae`, 34 paths; every one owned by the brief or granted by a ruling; Reviewer B r1 lens 7 confirmed every `src/` hunk under a grant): `.gitattributes`, `.github/workflows/release.yml`, `THIRD_PARTY_NOTICES.md`, `docs/release-checklist.md`, `docs/reports/wp6.3b-release-workflow.md`, `docs/user-guide.md`, `src/clearwater/__main__.py`, `src/clearwater/app/export_worker.py`, `src/clearwater/app/main.py`, `src/clearwater/gpu_pack_install.py`, `tests/test_exception_hook.py`, `tests/test_frozen_entry.py`, `tests/test_gpu_pack_install.py`, `tests/test_release_workflow.py`, `tests/test_tools_package_build.py`, `tests/test_tools_package_ffmpeg.py`, `tests/test_tools_package_notices.py`, `tests/test_tools_package_smoke.py`, `tools/package/README.md`, `tools/package/build.py`, `tools/package/ffmpeg.lock.json`, `tools/package/native-licences/array-api-compat-LICENSE`, `tools/package/native-licences/array-api-extra-LICENSE`, `tools/package/native-licences/cobyqa-LICENSE`, `tools/package/native-licences/libffi-cpython-source-deps-LICENSE.txt`, `tools/package/native-licences/llvm-3.6.2-LICENSE.TXT`, `tools/package/native-licences/manifest.json`, `tools/package/native-licences/mesa-11.2.2-docs-license.html`, `tools/package/native-licences/msvc-distributable-code-excerpt.txt`, `tools/package/native-licences/openssl-3.5.5-LICENSE.txt`, `tools/package/native-licences/packaging-LICENSE.BSD`, `tools/package/native-licences/pyprima-LICENCE.txt`, `tools/package/notices.py`, `tools/package/smoke.py`. Plus the seat's `dc088f60` (`tests/harness/genericity_lists.py`: one instance-surface entry, below).

## Nets

| Net | Head | Verdict | Disposition |
| --- | --- | --- | --- |
| A r1 (full) | `00b221cb` | NEW_CRITICAL_MAJOR_FOUND: 1 CRITICAL by rule (C1), 2 MAJOR (M1, M2), 6 MINOR, 9 adv | Reviewer A r1 rulings; turns 15-16 |
| A r2 (delta) | `fa0fded4` | NO_NEW_CRITICAL_MAJOR | converged; t17-t19 followed under the Stage-1 / Turn-17 / Turn-18 rulings |
| A r3 (delta `fa0fded4..65784337`) | `65784337` | NO_NEW_CRITICAL_MAJOR; 5 MINOR (F1-F5) + 4 adv; k1 / k2 agreed MINOR | Reviewer A r3 ruling; turn 20 (k1, k2, F1-F4, A1, A3, A4; A2 a report line); F5 DEFERRED to WP6.5 |
| B r1 (full `50a25b3b..91f90c8f`) | `91f90c8f` | NEW_CRITICAL_MAJOR_FOUND: MAJOR 1 embedded components in carried natives; 8 MINOR; 5 adv | Reviewer B r1 rulings: MAJOR 1 CARVED to WP6.3c; turn 22 (2-12; 13, 14 report lines) |
| B r2 (delta) | `4e848bf2` | NEW_CRITICAL_MAJOR_FOUND: the annotated-tag gate refused every real release (checkout's forced lightweight overwrite; seat-CONFIRMED from `actions/checkout@11bd7190` source) | Reviewer B r2 rulings; turn 23 |
| B r3 (delta) | `260c63ae` | **NO_NEW_CRITICAL_MAJOR**; 6 adv | 1, 2, 3, 5 carried to WP6.3c; 4 a record line; 6 corrected in this record |

Seat QA of every turn: the diff read against its dispatch; owned files only; outside-sandbox re-runs of the seven package modules and the module-alone installer; ruff, format, mypy win32 and darwin; 0 CR in every changed blob.

## The seat proofs of record

- **Real one-folder builds** (no FFmpeg) from Git Bash's FULL PATH (two mingw64 entries and a JDK on PATH; `PYTHONPATH` unset): `work\wp6.3b-stage1b` at `65784337`, `stage1c` at `8938edd3`, `stage1d` at `4e848bf2` (`build.py` / `notices.py` unchanged since). Each: `native origin check: PASS`, `hidden-import check: PASS`, `bundle check: PASS`; `dll_origin.py`: 0 foreign origins. (Stage 1 at `fa0fded4`, before t17, HAD carried MSYS2's OpenSSL and a JDK's UCRT: the record row below.)
- **The smoke under a read-only UIA watch** (`seat\smoke-uia\run1`, at `65784337`; `smoke.py` untouched by t20; t22's `smoke.py` change none): exit 0, 13 frozen PIDs seen, `windows_seen` []; every refusal / worker / planted-exception row PASS with a 0-survivor job census; FFmpeg SKIP.
- **The notices read in full** (`seat\stage1b-notices-read.md`; re-checked at each rebuild): 1,536 entries, 25 rows; coverage exact both ways for 301 files, 1,067 PYZ modules, 155 `base_library.zip` members and 12 PKG archive entries; every native-licences text verbatim; every provenance value and bound-file hash equal to the seat's measured record. Final notices sha256 `3afe913e26ecd6fe65765943fef798450687bebf7df926d1f720da9b8e999d8c` (stage 1c and 1d identical); the project `LICENSE` byte-equal to its LF blob.

## Gate (`p63b2`, on `260c63ae`)

Run `p63b2` on `260c63ae` (orchestrator gen 51, 19:33-20:20Z; seat folder `work/orch-g51/gate-p63b2/`, archived to `wp6.3b\gate\`), after copying the uncommitted root `clearwater.local.toml` into the worktree:

| Leg | Result |
| --- | --- |
| static | ruff exit 0; format exit 0 (337 files); mypy win32 exit 0 (166 source files); `mypy --platform darwin` clean at the seat on `260c63ae` (166 files) |
| collect | all 9,487 = parallel 8,143 + serial 1,337 + fullclip 7; 0 duplicates; diff vs all 0 |
| parallel | **7,936 passed, 207 skipped**, exit 0, 572 s |
| serial | **1,318 passed, 19 skipped** (the WP6.5 macOS native-leg skips), exit 0, 2,228 s; the QUIT_SCRIPT seat test `tests/test_app_startup.py::test_python_m_clearwater_starts_the_shell_and_exits_0` PASSED (2.55 s, junit) |
| harness | first run **FAILED 2** (`.github/workflows/release.yml` unregistered: the genericity guard's term `pytest` and the manifest accounting). The seat registered it on the instance surface (`dc088f60`, one entry in `INSTANCE_SURFACE_RELPATHS`, the same form as WP5.5's `8e83fa76`); re-run **423 OK (1 skipped)**. Between `260c63ae` and `dc088f60` only `tests/harness/genericity_lists.py` (outside every pytest leg) changed |

Module-alone `tests/test_gpu_pack_install.py`: 113 passed at the seat on `260c63ae` (gen 50). No fullclip leg (no decode / encode path change).

**The aborted run `p63b`** (gen 50, 19:18-19:30Z, same head): static and collect green; the parallel leg failed 12 (10 failed + 2 errors), every one `LocalConfigError: .worktrees/wp6.3b/clearwater.local.toml: file not found`, an environment gap (the worktree never received the uncommitted local config), not code; the serial leg was killed at its start. Not the gate of record.

## Dispositions (for CHARC at this accept)

- **AD-38 (new):** the release workflow, the build's sanitized PATH and origin check (and its venv-only trust), the artifact notices generator with the three provenance kinds and the fail-closed coverage, the headless smoke in a Job Object, the bundle rule's 6.3c half, the lazy-import limit, the fatal-error hooks' `os._exit(1)`; **plus the limit in words above.**
- **Register rows (CHARC writes):**
  - FFmpeg re-pin about 2028-10 (opens as planned; 6.3c closes it);
  - the MinGW-runtime limitation;
  - the WP6.3c carve-out (owner: WP6.3c);
  - MAJOR 1, embedded components in carried natives (owner: WP6.3c, closed before the 1.1.0 draft);
  - RECORD: the WP6.1 spike builds' PATH contamination (`ucrtbase` at the top level; never released; opened and closed by the origin check);
  - RECORD: the 1.0.0 audit's SciPy vendored-code gap (1.0.0 did not redistribute the wheel);
  - NOTE: A r3 F5 (the darwin PATH list and a Mach-O-aware origin rule) owned by WP6.5's brief.
- **Record line (B r3 adv 4):** a private repository makes the tag re-fetch fail closed (anonymous after `persist-credentials: false`); the repository is public.
- **Carried to WP6.3c (brief note committed by CHARC):** B r3 adv 1 (transport bounds on the re-fetch), 2 (the tag object's own `tag` header equals the tag name), 3 (the real-git test pins `--no-tags` and the single refspec), 5 (a named refusal on a deleted origin tag); B r2 adv 5 (the sidecar's trailing LF).
- **Carried to WP6.5 (brief note):** A r3 F5; B r2 adv 4 (the notices tests' module-level win32 skip moves to the fixture).
- **CLAUDE.md:** the "v1.0.0 annotated, not pushed" line is stale (CHARC verified `v1.0.0` on origin, peeling to `40d2ce04`): CHARC corrects it.
- **Owed prunes (the owner's word only):** `work/wp6.3b-stage1`, `stage1-cleanpath`, `stage1b`, `stage1c`, `stage1d` and their logs; `work/seat63b-*`; `work/c63b-*` in the worktree; `.worktrees/wp6.3b-rA` after the accept.

## Merge

- `dc088f60`: the seat's harness registration (above).
- `b2d7e3bb`: main (`24801a23` plus the state commits; 40 commits since `50a25b3b`, none in `src/`, `tests/`, `tools/` or `.github/`) merged into `wp6.3b`; docs only (the CHARC / orchestrator state files, the 6.3c and 7.1 briefs, CLAUDE.md, the debt register). Harness re-run on the merged head: 423 OK (1 skipped).
- This record committed on `wp6.3b`; main fast-forwarded to it (`git merge --ff-only wp6.3b`); every changed blob 0 CR.
