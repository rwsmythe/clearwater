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
- **STOP [MAJOR, walkthrough environment]:** the guide's lean environment-report
  command could not resolve its temporary psutil/py-cpuinfo dependencies.
  Online exit **2**, package-index connection refused (WinError 10061):
  `lean-environment-report-online.log`. Offline exit **1**, psutil missing from
  cache: `lean-environment-report.log`. The initial offline lean sync also
  lacked the PySide wheel; normal sync then succeeded. This is an execution
  prerequisite failure, not evidence of a product fault or an incorrect guide
  command. Dispatcher disposition needed: provide working index access or cache
  the two diagnostic packages, then rerun the unchanged guide command in the
  lean environment. Do not claim step 8(c) fully exercised yet.
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
| Lean diagnostics might be unavailable | Online connection-refused and offline missing-cache reproductions | CONFIRMED / OPEN to dispatcher; no product fix attempted |

Final file-constraint pass found no further product/document defect. Execution
remains incomplete only for the lean diagnostic above. DR-119 (a)-(b) are paid
down in the candidate; formal closure, N13 satisfaction, Reviewer A/B, the full
release gate, merge, tag and release record remain with the dispatcher/CHARC.
No footage was read; no unowned tracked file, dependency list or frozen interface
changed. No dependency was added/removed, git write, mailbox post, remote action,
installer, timing window or fabricated gate claim occurred. All runtime export
outputs stayed under this worktree. YIELD for the dispatcher to disposition the
environment blocker and run Reviewer A.
