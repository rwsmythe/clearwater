# WP5.5 release preparation - cumulative ledger

## Round 0

Read-only audit: `work/wp5.5/round0/return-1.md` and `audit.json` (copied
from the dispatcher's evidence). Four MAJOR STOP findings; all NEW and
in-envelope; no reopens, reverts or code changes. No incompatible dependency
was established. CHARC ruled in message `ce6094d108b9546f`:

| Finding | Ruling | Disposition |
| --- | --- | --- |
| cuda-toolkit has no licence declaration/file | R1: metadata-only selector, no code/data; optional NVIDIA component position | COMPATIBLE-WITH-CONDITION; describe once, no invented licence text |
| PySide6/shiboken wheels carry only a commercial licence file | R2: LGPL-3.0, dynamically linked and replaceable; QtCore/QtGui/QtWidgets only; upstream licensing/attributions plus metadata evidence | COMPATIBLE-WITH-CONDITION; reproduce LGPLv3 once and disclose wheel evidence gap |
| Brief assumed an FFmpeg local-config key | R3: FFmpeg is discovered through PATH; config template sets footage/working folders separately | Guide corrected to installed behavior |
| Root version also occurs in unowned uv.lock | R4: grant exactly the root version line, 0.0.0 -> 1.0.0 | Any further lock diff requires STOP |

Re-seat: fresh Codex build session from round 0 at dispatch head `e2cf4752`.
Reviewer A and Reviewer B are Claude passes run by the dispatcher; neither has
run on this build yet. Owner ruling on DR-117: defer the fix to a later release.

## Turn 2

Depth at turn-1 end (previous session): 178,295 of 475,000 (driver footer)

Depth at turn-2 end: 156,273 of 258,400 (driver footer; fresh session 01a1a3bf)

Build scope: notices, guide, README prepend, release checklist, version
synchronization, DR-119 (a) bench label and (b) listing LF output. The completion
report follows Reviewer A in a later turn. Release gate/tag remain at the
orchestrator's seat.

### Execution record

- Tests first: `work/wp5.5/t2-red.log`, exit 1: **4 failed, 68 passed,
  1 deselected in 71.91s**. All four failures matched the intended changes.
  The existing slow halo test was deselected by the prescribed expression.

  | New / changed test | RED result and evidence |
  | --- | --- |
  | test_release_version_is_1_0_0 | FAIL as expected: 0.0.0 != 1.0.0; test_version.py:22 |
  | test_release_version_matches_project_and_installed_metadata | PASS as expected: the old version was already synchronized; release-value test separately goes RED |
  | test_photo_export_records_the_application_version | PASS as expected: existing real composition wiring already carries the live version |
  | test_d106_is_0_4004_seconds_per_frame_at_29_97 | FAIL as expected: calculated 12.0 vs old constant 25.0; test_export_bench.py:31 |
  | test_d106_matches_spec_n6_12_minutes_per_minute | FAIL as expected: old constant 25.0 != 12.0; test_export_bench.py:36 |
  | test_run_once_records_the_row_and_deletes_its_folder (cold/warm) | PASS as expected: reads the constant; fixture rate lies below either threshold |
  | test_wholeset_listing_writes_lf_bytes_on_a_crlf_stream | FAIL as expected: IMG_0001 and GX000002 contained CRLF; test_tools_halo_part3.py:105 at RED |

- Minimal code: version 1.0.0 in the package/project; D106 constant/docstrings
  and record-key comment; listing writes UTF-8 bytes ending in LF.
  `uv run` refreshed editable metadata and changed only the root version line in
  uv.lock. `work/wp5.5/t2-lock.diff` and `t2-lock-stat.log`: **1 insertion,
  1 deletion**. No dependency or other lock entry changed.
- GREEN: `work/wp5.5/t2-green.log`, exit 0: **72 passed, 1 deselected in
  68.17s**. After lint fixes, `t2-green-final.log`, exit 0: **72 passed,
  1 deselected in 67.94s**. Every pytest invocation loaded sandbox_mkdir_shim,
  disabled cacheprovider and used a worktree basetemp; no whole-suite or -n run.
- Static logs: `work/wp5.5/t2-ruff.log`: **All checks passed!**;
  `t2-format.log`: **317 files already formatted**;
  `t2-mypy.log`: **Success: no issues found in 158 source files**. All exit 0.
  Initial lint found one long docstring line and redundant UTF-8 encode argument;
  both corrected within the owned lines before the final GREEN run.
- Notices: `work/wp5.5/build_notices.py` assembled **432,512 UTF-8/LF bytes**,
  **44 distinct texts / 54 source records**, from round-0 licence copies and
  identified upstream supplements. Complete NumPy/SciPy/Pillow/CuPy aggregate
  and component texts retained. LGPLv3 appears once; libheif/libde265 retain
  their project notices and copyright headers with the common text referenced.
  x265 source grant, GPL text and MinGW/winpthreads notices included.
  Inventory with source paths, SHA-256 and byte counts:
  `work/wp5.5/notices-inventory.json` and `notices-inventory.md`.
  The later completion report must incorporate this inventory and the audit's
  evidence-per-row table; it is deliberately not created in this turn.
- Guide/checklist/README: all eight guide sections mapped to the round-0 shell
  findings and R3. Lean commands avoid default dev/CUDA installation; Gamma is
  Advanced; HLG/PQ wording follows transfer tags; DR-117 says owner-deferred.
  Checklist orders gate, archive, merge, owner's word, annotated tag and CHARC
  record. README adds **8 lines / 412 LF bytes** above the unchanged **5,622-byte
  HEAD blob**; `git diff README.md` has additions only.
- Fixture walkthrough (`work/wp5.5/walkthrough/`): headless photo/video and
  startup smoke all exit 0 (`results.json`, `photo.log`, `video.log`,
  `startup-test.log`). Startup: **1 passed in 6.71s**. No sitecustomize hook.
  Photo: `jpeg-gradient-srgb_corrected.png`, **96x64, 16-bit RGB, ICC 588 bytes,
  app_version 1.0.0**. Video: `hevc8-bt709-full_corrected.mp4`, **HEVC,
  320x180, yuvj420p, 30000/1001 fps, 45 frames, full range, BT.709 tags**;
  embedded app_version **1.0.0** (`inspection.log`, `video-probe.json`).
  This is functional verification, not a performance measurement.
- Lean install: absolute `UV_PROJECT_ENVIRONMENT` under
  `work/wp5.5/walkthrough/lean-venv`, never .venv. The guide's lean sync exited
  **0**, installing **8 distributions**; **pytest and CuPy absent**
  (`lean-sync-online.log`, `lean-distributions.json`). Main environment's
  **62 distribution METADATA hashes unchanged** (`lean-run.log`,
  `lean-run-offline.log`). Independent lean headless photo export exited **0**
  and wrote `lean-photo/jpeg-gradient-srgb_corrected.png` (`lean-photo.log`).
- **Turn-2 STOP [MAJOR, walkthrough environment; resolved before Round 1]:** the guide's lean environment-report
  command could not resolve its temporary psutil/py-cpuinfo dependencies.
  Online exit **2**, package-index connection refused (WinError 10061):
  `lean-environment-report-online.log`. Offline exit **1**, psutil missing from
  cache: `lean-environment-report.log`. The initial offline lean sync also
  lacked the PySide wheel; normal sync then succeeded. This is an execution
  prerequisite failure, not evidence of a product fault or an incorrect guide
  command. The dispatcher subsequently ran the unchanged guide command with
  network access; the successful orchestrator-seat result is recorded below.
- The report tool itself ran successfully through the full environment (exit
  **0**): `environment-report.log`,
  `environment/reports/environment-20261103T234509Z.json`; no unavailable
  probes, Python 3.12.13, Windows 11, FFmpeg 9.0.2 full Gyan, NVIDIA driver
  621.01. This does not substitute for the blocked lean diagnostic.
- Disk check: Git Bash's df is unavailable under the sandbox token
  (CreateFileMapping Win32 error 5, `disk-before-lean.log`). Portable
  shutil.disk_usage reported **42.022 GB free** (`disk-python.log`). No heavy
  release-gate leg was run. The orchestrator must still run df at its own seat.
- Artifact checks: `work/wp5.5/t2-artifact-checks.log`: all **13 authorized
  deliverables LF-only**; README original blob preserved; one-line root lock
  change; **44 copied-text hashes/counts match**; one LGPLv3 text; guide local
  links resolve and no owner's-home path; exactly the **13 owned paths** changed.

### Verification loop

| Suspected | Independent confirmation | Disposition |
| --- | --- | --- |
| Stale D106 target | RED arithmetic/constant tests both fail with 25.0 | CONFIRMED / FIXED (DR-119 a); GREEN |
| CRLF item listing | Byte-backed CRLF stream reproduces CR in output | CONFIRMED / FIXED (DR-119 b); GREEN |
| Release version still 0.0.0 | RED literal check fails; TOML and installed metadata agree on old value | CONFIRMED / FIXED; real photo and video provenance 1.0.0 |
| Version bump might alter other lock entries | Saved diff plus one-line insertion/deletion count | REJECTED as false positive; root row only |
| Notices might omit aggregate/native conditions or repeat LGPLv3 | Source inventory and independent extraction/hash checks | Confirmed during assembly and FIXED: complete aggregate/native texts, common LGPLv3 once |
| README prepend or platform checkout might rewrite harness content | Compare suffix against git HEAD blob and additions-only diff | REJECTED as false positive on delivered diff; original blob retained |
| Lean install could pull in CUDA/test tools or mutate .venv | Count installed distributions and compare main METADATA hashes | REJECTED as false positive: 8 lean distributions, no pytest/CuPy, main unchanged |
| Lean diagnostics might be unavailable | Online connection-refused and offline missing-cache reproductions | CONFIRMED at cell seat / RESOLVED at orchestrator seat before Round 1; no product fix needed |

The turn-2 file-constraint pass found no further issue; Reviewer A subsequently
identified the encoding/menu defects recorded in Round 1 below. DR-119 (a)-(b)
are paid down in the candidate; formal closure, N13 satisfaction, Reviewer A/B,
the full release gate, merge, tag and release record remain with the dispatcher/CHARC.
No footage was read; no unowned tracked file, dependency list or frozen interface
changed. No dependency was added/removed, git write, mailbox post, remote action,
installer, timing window or fabricated gate claim occurred. All runtime export
outputs stayed under this worktree. Turn 2 yielded for the dispatcher to
disposition the environment blocker and run Reviewer A.

## Round 1

Reviewer A: Claude, read-only process at the orchestrator's seat on `e7876912`.
Findings copy: `work/wp5.5/A-r1-review.txt`; verdict
**NEW_CRITICAL_MAJOR_FOUND**. Reviewer baseline: **72 passed, 1 deselected in
67.36s**. Driver transport / CLI version is dispatcher-owned, not supplied in
the findings copy; no version is inferred here.

| Round | Critical | Major | Minor | Advisory | In / out of envelope | NEW / REOPENED | Reverts | Product-code fixes | Tools docstring | Other fixes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A r1 | 0 | 2 | 4 | 4 | 10 / 0 | 10 / 0 | 0 | 0 | 1 | Documentation; F10 requires no change |

Depth at turn-3 start: 156,273 of 258,400 (previous turn's driver footer)

Depth at turn-3 end: 192,011 of 258,400 (driver footer; session 01a1a3bf)

### Per-finding adjudication

All ten findings are confirmed and in envelope under the binding dispatch;
none is rejected or reopened.

| Finding | Severity | Confirmation and fix |
| --- | --- | --- |
| F1 | MAJOR | CONFIRMED. The round-0 audit used locale-default `read_text(errors="replace")` on valid UTF-8 source files, then wrote those mis-decoded strings as UTF-8. Turn 2 copied the already corrupted evidence bytes and compared them back to that evidence, so its hashes did not establish source fidelity. Regenerated every installed text directly from original source BYTES, decoded UTF-8 explicitly; CRLF -> LF only. Upstream texts use their existing UTF-8 cached files and declared source selections. The independent source-byte verifier checks original files, not the audit copies or merely the generated hashes. |
| F2 | MAJOR | CONFIRMED by `ShellWindow._build_actions` at `gui/shell.py:458-489` and `set_settings_dialog` at `:399-407`. Changed all three guide paths to Tools > Settings. Checked File > Open/Export/Quit; View > Fit/1:1/Zoom in/Zoom out/Reset split; Tools > Settings against the actual action wiring. No other incorrect menu path remains. |
| F3 | MINOR | CONFIRMED against the installed NVIDIA License.txt. The quote now contains the whole section 1.1.1(3), through "meets the distribution requirements indicated in this Agreement." It is extracted programmatically, with whitespace joined for the prose quote; the full licence text remains a byte-true copy. |
| F4 | MINOR | CONFIRMED. Every Source line now names its distribution/version and installed package/dist-info path, the Python installation's LICENSE.txt, or an upstream URL. No Source line contains a work/ path. |
| F5 | MINOR | CONFIRMED. Qt LGPL text uses v6.12.0; x265 uses 4.3, libheif v1.23.6, libde265 v1.1.3. All upstream-only texts explicitly state they were copied from the URL as it stood at turn 2 and were not re-fetched. The actual wheel manifest specifies no MinGW/winpthreads version, so no version-matched tag can be identified; the native component entry and both unversioned source entries disclose that gap instead of inventing a tag. The manifest's own upstream URL is retained verbatim in its copied text. |
| F6 | MINOR | CONFIRMED. User-facing fixture commands now use work/try/photo, video, cache and settings, with work/try/photo.json and video.json records. Source paths, command flags and expected output names are unchanged from the exercised commands. |
| F7 | ADVISORY | CONFIRMED. Removed CHARC, ruling identifiers, R2 and "accepted by" framing from the third-party notices. Stated the LGPL and optional CUDA positions plainly; the licensing substance is unchanged. Also matched R1's lowercase "metadata-only" sentence exactly. |
| F8 | ADVISORY | CONFIRMED. Checklist archive path is now <evidence-folder>\release-1.0.0\, described as the harness's review-evidence folder outside the repository. |
| F9 | ADVISORY | CONFIRMED. Reflowed the ragged export_bench module docstring; no executable statement changed. |
| F10 | ADVISORY | CONFIRMED / NO CHANGE, as directed. Turn-2 lean sync succeeded with 8 distributions; the orchestrator then ran the lean diagnostic successfully. Seat and evidence are recorded in the walkthrough table below. |

### Walkthrough closure

The network prerequisite from turn 2 is resolved; no product or guide-command
fix was necessary.

| Step | Seat / command / result |
| --- | --- |
| Lean sync | Cell seat, turn 2: `uv sync --no-default-groups`, exit 0; 8 distributions, pytest/CuPy absent. |
| Lean environment report | **Run at the orchestrator's seat**, with UV_PROJECT_ENVIRONMENT set to this worktree's work/wp5.5/walkthrough/lean-venv: `uv run --no-sync --with psutil --with py-cpuinfo python tools/environment_report.py --out work/wp5.5/walkthrough/environment`; exit 0, "Installed 2 packages" (dispatcher-supplied execution result). |
| Report evidence | work/wp5.5/walkthrough/environment/reports/environment-20261103T234816Z.json; Python 3.12.13; FFmpeg 9.0.2-full_build-www.gyan.dev; unavailable {}. Cell read the resulting report and confirmed those fields. |
| Lean environment after diagnostic | Still 8 installed distributions, confirmed from its dist-info directories at the cell seat. The two diagnostic packages were temporary. |
| Lean photo export | Cell seat, turn 2: exit 0, jpeg-gradient-srgb_corrected.png; previously recorded above. |

### Validation

`work/wp5.5/verify_notices_utf8.py` -> `t3-notices-verify.log`, exit 0:

```text
TEXTS: 44; MISMATCHES: 0
SOURCE RECORDS: 54; every duplicate also byte-equal to its original source
MARKER U+00C2: SOURCE=0; NOTICES=0
MARKER U+00C3: SOURCE=0; NOTICES=0
MARKER U+00E2 U+20AC: SOURCE=0; NOTICES=0
MARKER U+FFFD: SOURCE=0; NOTICES=0
HASHES/BYTES: all 44 match LF-normalised SOURCE bytes
NOTICES SIZE: 433520 bytes
SOURCES: no work/ paths; no harness/ruling references
EULA: complete section 1.1.1(3) quote matches installed License.txt
```

Corrected source-byte inventory (source location, SHA-256, LF-normalised byte
count per text): `work/wp5.5/notices-inventory.json` and `notices-inventory.md`.
This replaces turn 2's corrupted-source inventory for the completion report.
The nine upstream-only source texts were not re-fetched in this turn.

`work/wp5.5/t3-guide-verify.log`, exit 0: all documented menu paths agree with
the shell action wiring; three Settings paths corrected; neutral walkthrough
folders checked; orchestrator report fields and eight-distribution lean state
confirmed.

Prescribed targeted pytest command (sandbox_mkdir_shim, no cacheprovider,
basetemp work/wp5.5/t3), `work/wp5.5/t3.log`, exit 0:
**72 passed, 1 deselected in 72.09s (0:01:12)**.

Static checks, all exit 0:

- `work/wp5.5/t3-ruff.log`: **All checks passed!**
- `work/wp5.5/t3-format.log`: **317 files already formatted**
- `work/wp5.5/t3-mypy.log`: **Success: no issues found in 158 source files**

Round 1 fixes introduce no executable product/tool changes, tests, dependencies,
lockfile changes, footage reads or writes outside this worktree. Reviewer A's
next pass remains at the dispatcher seat; no convergence claim is made here.
`work/wp5.5/t3-scope-verify.log`, exit 0: exactly five owned paths changed;
all UTF-8/LF-only; export_bench AST identical with its module docstring excluded;
version/dependency files unchanged; git diff --check clean.
