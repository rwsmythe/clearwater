# Clearwater 1.1.1 release record (CHARC generation 20, 2026-11-08)

The release record required by `docs/release-checklist.md` v2 step 12. Written by
CHARC after the owner's words, the orchestrator's tag report, the verified draft
release, the owner's clean-account check and the publication. 1.1.1 is the first Clearwater version delivered as a download. It carries the
same product code as the tag `v1.1.0`, whose release run failed before building anything;
that attempt is recorded here too.

## The 1.1.0 attempt (recorded, not a release)

| Item | Value |
|---|---|
| Owner's word | 2026-11-06 16:27Z, verbatim: "tag 1.1.0" |
| Tag | `v1.1.0` = annotated object `0127e1a2` -> commit `356f2e4d` (the WP6.3d head plus the bump `3737cee0`, the UA pin `c6bf824c` and the Codex r4 notes fix); gate r110 all green on it |
| Push | by the OWNER's hand 2026-11-07 ~15:43Z (main `007586db..44d80520`, then the tag) |
| Workflow run | `42387791040`: the version and annotated-tag gates PASSED on the real tag; "Run parallel tests" FAILED at once because `--basetemp=work/ci-parallel` names a parent a fresh checkout does not have (`work/` is gitignored; pytest does not create it); no draft, nothing published |
| Disposition | checklist step 7: a pushed tag is never moved; `v1.1.0` stays on origin as history with no release; the owner said "tag 1.1.1" (2026-11-07 ~16:05Z); the fix is WP6.3e (below) |
| Record | `clearwater-review-evidence\release-1.1.0\` (bump, build, gate-r110, `workflow\run-42387791040\`); register DR-154 (record, closed) |

## WP6.3e (the fix between 1.1.0 and 1.1.1)

Accepted at `48b08d91` (Codex lane, both nets Claude; A converged r3 plus the seat's popen
spy, B NO_NEW_CRITICAL_MAJOR), merged to main at `e4f0cb6f`, record
`docs/proofs/wp6.3e-accept.md`. The workflow creates `work` before pytest and carries
`-rs`; the existing FFmpeg skip-with-reason policy was applied at 96 sites over 15 test
modules (157 node ids) because the GitHub runner has no FFmpeg; a CI-shaped rehearsal
(fresh clone, no `work/`, no local toml, runner PATH shape, no GPU) now precedes every
tag (AD-38 item 17). Register: DR-155 (runner leg without FFmpeg), DR-156 (zip not
byte-reproducible), DR-157 (find_tool-gated units skip on the runner), DR-158 (one V8
serial transient in gate p63e, 3 / 3 alone; watched; it passed in the release gate).

## Tag

| Item | Value |
|---|---|
| Tag | `v1.1.1` (annotated, unsigned), message exactly `Clearwater 1.1.1` |
| Tagged commit | `c5ed85172b32fee474ddb4fb3b54f30eadf9adf4` = `main` = `release-1.1.1`: WP6.3e's merge `e4f0cb6f` plus CHARC state commits plus the bump `092c295d` and three fix commits `af29545e`, `8a96f45b`, `c5ed8517` (rebased onto main with range-diff all `=`) |
| Tag object | `85cd001772d4be3dbb9d6d86cc6f5ce60e5bf897`; tagger Reid Smythe, 2026-11-07 23:29:44Z (13:29:44 -1000); `git cat-file -t v1.1.1` = tag, `v1.1.1^{commit}` = `c5ed8517`, verified at CHARC's seat |
| Applied by | the orchestrator (generation 59, `clearwater-orchestrator-20261107-1113`) at the main checkout after the full gate, nothing else running; tag report `daae836580d4d1ee`; record `clearwater-review-evidence\release-1.1.1\tag\tag.txt` |
| Owner's words | "tag 1.1.1" (2026-11-07 ~16:05Z, in chat to CHARC); then, after the tag report, "You do the pushing" and "prune" (2026-11-07 ~23:35Z) |
| Push | by CHARC on the owner's word, 2026-11-07 ~23:40Z: `origin/main` `44d80520` -> `d0cd949f` (the tagged commit an ancestor), then `v1.1.1`; `ls-remote` verified `85cd0017` peeling to `c5ed8517`; `v1.1.0` unchanged. A one-time instruction for 1.1.1; the standing rule that the harness never pushes Clearwater's repository without the owner's word stands |

Commits after the tag on `main` are documentation only (orchestrator and CHARC state, the
prune record `docs/proofs/prune-2026-11-07.md`, this record). The product content of
1.1.1 is exactly the tree at `c5ed8517`; `git diff v1.1.0..c5ed8517 -- src/` is
`__version__` only (confirmed by the Codex reads).

## What 1.1.1 is

- The 1.0.0 product (spec `docs/underwater-correction-spec.md` v0.6.2) delivered as a
  PyInstaller one-folder Windows build (`tools/package/build.py`, CP6a = onedir, N14):
  `Clearwater-1.1.1-windows-onedir.zip`, one top-level folder, `Clearwater.exe` plus
  `_internal/`, FFmpeg and ffprobe bundled beside the executable (the zvbi-free
  self-build from the owner's fork `rwsmythe/FFmpeg-Builds`, FFmpeg `release/9.0` at
  `b204e94e`, build 20261106; WP6.3c / WP6.3d), the generated `THIRD_PARTY_NOTICES.md`
  inside the folder and attached to the release; unsigned; no installer.
- GPU support as an optional download installed from the Tools menu or `--install-gpu-pack`
  (CuPy + CUDA wheels, about 1.7 GB to download, 2.5 GB installed; verified file by file at
  install, a shorter check at every start; WP6.1 / WP6.3a / WP-DR125).
- The source install with uv still works as in 1.0.0; the macOS code paths (WP6.4) are in
  the tree but not validated on a Mac (WP6.5 pending); there is no macOS download.
- Version `1.1.1` in `pyproject.toml`, `src/clearwater/__init__.py`, the `uv.lock` root
  package, the root notices title and the installer's User-Agent `Clearwater/1.1.1`
  (`tests/test_version.py`, `tests/test_gpu_pack_install.py`).
- Licence GPL-2.0-or-later. **N13 SATISFIED for 1.1.1** on the artifact notices
  (1,540 entries / 478 component rows, strict UTF-8, every carried native's embedded
  components and the FFmpeg build components with their own licence texts; WP6.3c,
  WP6.3d, AD-38 items 9-16).
- `docs/user-guide.md` (install from the download, the GPU pack, troubleshooting,
  licence), `README.md`, `docs/release-notes-1.1.1.md` (the draft's body).

## The bump and the Codex reads

The bump commit and three fix commits were reviewed by ONE read-only Codex pass each
(gpt-6.1-sol / high; records `clearwater-review-evidence\release-1.1.1\{bump\r1,fix\r2-delta,fix2\r3-delta,fix3\r4-delta}\review.txt`):

| Round | Head | Verdict | Findings and disposition |
|---|---|---|---|
| r1 | `d6d1d259` | NEW_CRITICAL_MAJOR | F1 CRITICAL `notices.py:2191` "Clearwater 1.1.0 redistributes ..." inside the download's notices (CHARC had kept it as history; folded version-neutral + pin); F3 root notices :15 / :18 / :24 (folded); F2 notes "fixes the workflow and nothing else" (reworded); F5 Insta360 "being validated" (planned, not yet done); A1 "file ownership" (reworded); F4 checklist "1.1.0" literals (deferred to DR-159) |
| r2 | `c1625e55` | NEW_CRITICAL_MAJOR | N1 MAJOR: CHARC's A1 replacement claimed the set of installed files is checked at every start; false (`gpu_pack.py` cheap check); folded; N2 three more root-notice artifact lines (folded) |
| r3 | `6105f1f1` | NEW_CRITICAL_MAJOR | N3 MAJOR: "the size of every listed file" overstated (size-less RECORD rows are existence-only); the sentence reduced to its shape: "verified file by file when it is installed, and a shorter check of its files runs at every start" |
| r4 | `bc14bc98` | NO_NEW_CRITICAL_MAJOR | one advisory ("every start" is shorthand), no change |

Eight false or stale claims were caught by the Codex reads across 1.1.0 and 1.1.1, two of
them CHARC's own wording in this release. The lesson is a DR-159 item: the notes writer
greps every behaviour claim against the code before the read, and every version string a
reader of the download sees is version-neutral or current.

## Release gate: the figures of record

Gate r111 by the orchestrator (generation 59) at its seat on `c5ed8517` in
`.worktrees/release-1.1.1` (toml present, venv synced), one leg at a time, nothing else
heavy running, 2.5 TB free throughout; archive `clearwater-review-evidence\release-1.1.1\gate\`.

| Leg | Result |
|---|---|
| static | ruff 0; format 0 (337 files); mypy `Success` (166 files); darwin mypy `Success` (166) |
| collect | 9,921 = parallel 8,577 + serial 1,337 + fullclip 7; duplicates 0; diff against all 0 |
| parallel | 8,370 passed / 207 skipped, exit 0, 597 s |
| serial | 1,318 passed / 19 skipped / 0 failed, exit 0, 2,299 s (DR-158's node passed) |
| fullclip | 7 passed, exit 0, 1,724 s |
| harness | 423 OK (skipped 1) |
| installer module alone | 113 passed |

## Build, proofs and rehearsal (same head)

- Build (`release-1.1.1\build\`): exit 0 in 248 s under the UIA window watch (no window);
  native origin, hidden-import (61) and bundle checks PASS; notices PASS 1,540 entries /
  478 rows strict UTF-8 (the old "Clearwater 1.1.0 redistributes" sentence 0 hits); every
  smoke row PASS (`hevc_nvenc; libx265`); local zip sha256 `361a9301...ef53` = its
  sidecar, 306 members byte-identical to the built folder, 555.1 MiB, census 0 forbidden;
  actionlint 1.7.12 clean on `release.yml`.
- CPU export proof (`release-1.1.1\proofs\cpu\`): the frozen worker, redirected roots,
  PySide6 blocked, PATH = bundle + System32; `IMG_6702.MOV` (read-only) exported on the
  CPU with `hevc_nvenc`, 64.0 s; V4 mandatory and required all SAME (0 / 0); no
  descendant left. **Limit:** the GPU proof was NOT repeated for 1.1.1; the FFmpeg bytes
  and the shipped Python are unchanged since the 1.1.0 GPU proof
  (`release-1.1.0\build\record.md`: real 1,725,155,461 B install, export on the GPU V4
  0 / 0, removal clean).
- CI-shaped rehearsal (`release-1.1.1\rehearsal\c5ed851-runnerpath\`): a fresh clone of
  `c5ed8517`, no `work/`, no toml, runner PATH shape, `CUDA_VISIBLE_DEVICES=-1`: sync 0;
  parallel `7517 passed, 1060 skipped`; build 0 with no window; staging 0 with the three
  1.1.1 assets. Limits: Windows PowerShell 5.1 (the runner pwsh 7); the ubuntu release
  job is not rehearsable locally.

## The workflow run and the draft (checklist steps 9-10)

| Item | Value |
|---|---|
| Run | `42439969961`, event push, ref `v1.1.1`, headSha `c5ed8517` (= the gated commit), runner image windows-2025-vs2026 20261103.298.1; conclusion SUCCESS (jobs windows, release); record `release-1.1.1\workflow\run-42439969961\` (run.json, run.log, release.json, assets, the workflow artifact, step10.json) |
| Runner test leg | 7,515 passed / 1,062 skipped (239 s); vs the rehearsal's 7,517 / 1,060 the two extra skips are runner-environment only (`test_conftest_guard.py`: no 8.3 short name on that volume; `test_headless_export.py`: the C$ administrative share unreachable); no other difference |
| Draft | isDraft true, isPrerelease false, tag `v1.1.1`; body = `docs/release-notes-1.1.1.md` at `c5ed8517` + the source commit line |
| Assets | `Clearwater-1.1.1-windows-onedir.zip` 221,565,914 B, sha256 `3a4da9d1e66f80600636c7ac00b428672f01a2cb2f870a2d4e735d60d2a0395d` = the runner's own sidecar (recomputed at CHARC's seat on the downloaded file); `.zip.sha256` carries `# source-commit: c5ed8517...`; `THIRD_PARTY_NOTICES.md` 4,697,437 B sha256 `69a6837e...7c7d` = the copy inside the zip = the local build's |
| Source commit | EQUAL in four places: sidecar = run headSha = draft body = the gated commit |
| Zip vs the local build (DR-156) | member SET 306 = 306, names identical, one top-level folder; three members differ in bytes (`Clearwater.exe`, `_internal/base_library.zip`, numpy's `RECORD` for its two console-script launchers written per install); the zip is not byte-reproducible across machines, as recorded |

## Steps 11 and 13: the owner's check and the publication

| Item | Value |
|---|---|
| Step 11, clean-account check | PASS by the OWNER's hand on the downloaded artifact (owner 2026-11-08, verbatim in chat to CHARC: "step 1 complete.  Publish", where "step 1" is the clean-account check as listed by CHARC); the harness drove nothing on the desktop |
| Step 13, publish | Done by CHARC on the owner's word "Publish" (`gh release edit v1.1.1 --draft=false`); `isDraft` false, `isPrerelease` false, `publishedAt` 2026-11-09T05:30:45Z (GitHub's clock), target `main`, the same three assets (221,565,914 B zip; 161 B sidecar; 4,697,437 B notices); https://github.com/rwsmythe/clearwater/releases/tag/v1.1.1 |
| Standing rule | The two acts the owner usually performs by hand (the push, the publish) were done by CHARC on the owner's explicit words in this session ("You do the pushing", "Publish"); each is a one-time instruction recorded here, not a change to the rule that the harness never pushes or publishes Clearwater's repository without the owner's word |

**Clearwater 1.1.1 is RELEASED** (2026-11-09 05:30Z; 2026-11-08 19:30 -1000). Open after the
record: DR-159 (checklist v3); the owed prune of `.worktrees/release-1.1.1` (+ r111
basetemps), `.worktrees/release-1.1.1-rv`, `work/release-1.1.1` and
`work/release-1.1.1-proof-cpu` on the owner's word.
