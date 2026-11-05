# Clearwater release checklist v2: Windows 1.1.0

The orchestrator executes this checklist; implementer acceptance does not authorize
a version bump, tag, push or publication. The owner supplies the release instruction,
pushes the tag and publishes the draft. The local release gate runs on this laptop
BEFORE the tag (N14). The workflow builds from that tagged commit. The Windows
artifact is one folder, not an installer; it is unsigned. No PyPI release is planned.

**Current HOLD:** the pinned FFmpeg build's zvbi licence incompatibility is with
the owner, and `build.py --zip` is pending that ruling. This checklist describes
the release path after those items are resolved. STOP before any release attempt
while either remains open; workflow presence is not release readiness.

1. Confirm Reviewer A converged and Reviewer B is clean or its permitted bounded
   remediation is dispositioned under [the review/gate fill](review-gate-clearwater.md).
   Check ownership, the root-only lockfile diff, the guide walkthrough, artifact
   notices and carried debt. Preserve the WP6.3b review evidence separately from
   release evidence. **STOP** for an open blocking review finding or licence HOLD.
2. Obtain the owner's explicit **"tag 1.1.0"** through CHARC. On that word, prepare
   the reviewed version-bump commit: `pyproject.toml`, `src/clearwater/__init__.py`
   and the root notices title become 1.1.0. Update the lock's root package version
   consistently without changing dependency pins. Merge at the orchestrator's
   seat under the gate fill; record base, candidate and merge commits and prove
   patch identity over any rebase. The version bump is a release step, not part
   of WP6.3b. **STOP** without the owner's word, on version disagreement or on an
   unreviewed change; acceptance alone is not tag permission.
3. Check disk space in Git Bash before the local build/release gate and again
   before each heavy leg (serial and fullclip). Require **25 GB free** on C: at
   each check, allowing for onedir, FFmpeg archive, zip and smoke roots. Never
   prune without an explicit owner grant. **STOP** below the floor.

   ```bash
   df -h /c
   ```

4. Verify build inputs on the version-bump commit. The
   **python-build-standalone `20260303` build (CPython 3.12.13, OpenSSL 3.5.5) is
   a pinned BUILD INPUT; a change is a notices re-audit**. Re-verify
   `tools/package/native-licences/` (manifest, texts, bundled versions) whenever
   uv's managed Python changes; the generator fails closed on mismatched inputs.
   The workflow's uv pin (`0.10.9`) and laptop's `uv --version` must agree before the tag; any uv change requires native-licences re-verification.
   Read the FFmpeg URL/hash from `tools/package/ffmpeg.lock.json`, verify every
   linked component's source/licence evidence and re-pin the FFmpeg asset before
   the retention expiry (about **2028-10**). Re-pinning requires repeating the
   hash, configuration, source and encoder audit, not just replacing the URL.
   **STOP** for an expired/unavailable asset, unresolved incompatible component,
   missing native material or unreviewed interpreter change.
5. Complete the seat's local onedir build with the locked `--ffmpeg-from` and
   `--ffmpeg-sha256`, plus `--notices --smoke --zip --out work/release`.
   Inspect the REAL built-folder census against the generated notices in full:
   every binary has its terms and corresponding-source evidence. Retain the
   smoke transcript, its redirected profiles, row statuses, no-window UIA watch,
   no-survivor job census, bundle/hidden-import checks, sizes, zip member count
   and sha256. Verify no CUDA, footage, work directory or .venv is bundled.
   Run the V4 container instrument on a video export using the BUNDLED FFmpeg
   and retain its `hevc_nvenc`/`libx265` capability lines; prove GPU export through
   an installed pack where available (otherwise the outstanding GPU proof must
   be dispositioned before release). Run the seat's pinned, checksum-verified
   actionlint on `.github/workflows/release.yml` and verify action inputs against
   their pinned `action.yml` files. **STOP** on any failed check, unknown binary,
   missing source, unexpected window/process or unproved required export path.
6. Run the fresh LOCAL release gate on that exact final commit, using the current
   commands and collection rules in [the gate fill](review-gate-clearwater.md).
   Order: **static checks (including `mypy --platform darwin`), collection identity,
   parallel, serial, fullclip, harness**, plus module-alone
   `tests/test_gpu_pack_install.py` (WP6.3a F2 / WP6.3b ADV-1).
   Run one leg at a time with the stall watch; nothing else heavy runs beside
   serial/fullclip. Preserve stdout/stderr, exit codes, JUnits and conditions.
   Collection must prove disjoint parallel/serial/fullclip sets whose union is
   all tests; explain removed IDs and new/moved skips. Harness uses unittest
   separately. Archive logs, collection lists, JUnits and hashes under
   **clearwater-review-evidence\release-1.1.0\**, beside the clone, with the
   exact candidate commit. These figures supersede prior package-gate figures.
   **STOP** for any failed gate, unexplained collection/skip change or subsequent
   candidate change; repeat applicable integration checks before tagging.
7. On the owner's recorded instruction, create the annotated tag on the actual
   gated commit. Replace the placeholder; the message is **Clearwater 1.1.0**.
   **STOP** if HEAD, gated commit and intended tag target differ, or the tag
   already exists with another target. Never move an existing release tag.

   ```bash
   git tag -a v1.1.0 <gated-commit> -m "Clearwater 1.1.0"
   ```

8. The OWNER pushes the commit and tag; the harness never pushes. The push starts
   `.github/workflows/release.yml`. A manual verification run must select the
   existing tag and input `1.1.0`; it builds/uploads workflow artifacts but
   creates no release. Nothing in this package dispatches such a run.
   **STOP** without the owner's push, or if the remote tag targets another commit.
9. Watch the real workflow and archive its run URL, resolved commit, job logs and
   artifacts. `windows` syncs the locked GPU extra for analysis, checks tag/source
   equality, runs ONLY the parallel leg, then builds, checks and zips. This does
   not replace step 6's local gate. `release` runs only on a tag push, with
   `contents: write`, and attaches the zip, its `.sha256` and generated notices
   to a **DRAFT** release; notes come from `docs/release-notes-1.1.0.md` if present.
   **STOP** for a failed/incomplete job, wrong commit/version, missing asset or
   non-draft release. Do not publish to work around a workflow failure.
10. Download the three assets from the draft release. Compare the downloaded
    zip's SHA-256 against the sidecar (PowerShell `Get-FileHash -Algorithm SHA256`),
    list its single top-level folder and compare the attached notices with the
    copy inside. **STOP** on hash/content/layout disagreement; preserve the
    downloaded evidence rather than substituting the local build.
11. Test that DOWNLOADED artifact in a CLEAN Windows user account on this laptop:
    no Python, no FFmpeg and no added PATH entries. By the OWNER's hand or UIA
    on Clearwater's own window, unzip, run `Clearwater.exe`, open a photo and
    export; choose **Tools > Install GPU support...**, review the NVIDIA terms
    and size, install, restart and export on the GPU. Confirm the device and
    output; use disposable data/output folders. The Desktop-input rule binds
    the harness: no synthetic keyboard/mouse input. Entry-point tests/probes
    still require redirected roots, GUI isolation and bounded timeouts; the
    recorded QUIT_SCRIPT exception is seat-only, offscreen, in a gate leg.
    **STOP** for any failure, unexpected dependency/PATH requirement, wrong
    device or missing owner/UIA proof. Do not edit the owner's real profile.
12. CHARC writes **docs/proofs/release-1.1.0.md**: owner's instructions, gated/tag
    commit, local gate figures/hashes, both review verdicts, carried debt,
    workflow URL/log archive, downloaded zip hash, notices census, bundled V4 /
    encoder proof and clean-account outcome. Record N13's artifact verdict only
    against the artifact notices and corresponding-source evidence. At package
    accept CHARC also records AD-38, the checklist pointer and dated retention /
    indirect-source debt dispositions. **STOP** for missing proof or unresolved
    release debt requiring the owner's acknowledgement.
13. The OWNER reviews the draft and clicks **Publish release**. The workflow and
    harness never publish a non-draft release. **STOP** until that explicit click;
    a successful build or tag push does not authorize publication.

Keep original footage read-only and out of all artifacts. The repository's code
remains GPL-2.0-or-later. Each release zip carries its own generated
`THIRD_PARTY_NOTICES.md`, the notice of record for that binary artifact.
