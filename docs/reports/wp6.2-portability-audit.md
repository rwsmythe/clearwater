# WP6.2 portability audit: macOS arm64 CPU path

Date: 2026-11-04. Audited source: 5671a927, branch wp6.2.
Status: Reviewer A CONVERGED; Reviewer B NO_NEW_CRITICAL_MAJOR, corrections applied; acceptance pending.
Scope: src/clearwater, tools, and product tests. Scripts and tests/harness are
excluded. This report changes no product, tool, test, interface, or dependency.

## 1. Summary

Class 1 means platform conditionals, platform identification, Windows APIs, or
explicit Windows executable/path spellings. Class 2 means platform assumptions
without those conditionals: encoder/device models, filesystem identity, native
GUI behaviour, external-tool wording, and test coverage.

The round-0 searches (W/R rerun at Reviewer A round 1) produced these
matching-line / matching-file counts. Comments and test data count; these are screening counts, not counts of
executable branches. Searches overlap and must not be summed as unique sites.

| Search | Class / purpose | src/clearwater | tools | tests excluding harness |
|---|---|---:|---:|---:|
| B | Class 1 baseline | 13 / 2 | 10 / 3 | 42 / 19 |
| W | Class 1 broad widening, CRLF Windows checkout | 103 / 31 | 166 / 30 | 286 / 62 |
| W (LF blobs) | Same pattern, committed LF text | 103 / 31 | 164 / 30 | 285 / 62 |
| R | Class 1 refined | 19 / 2 | 36 / 5 | 88 / 21 |
| A0 | Class 2 initial screen | 211 / 36 | 438 / 43 | 1124 / 100 |
| A | Class 2 refined screen | 94 / 25 | 183 / 27 | 481 / 79 |
| S | Filesystem/process supplement | 77 / 31 | 153 / 30 | 1011 / 96 |
| L | Literal two-backslash sweep | 8 / 4 | 35 / 10 | 95 / 29 |

The semantic site table has the following row counts. These are mechanisms,
not regex hits; they include already-portable mechanisms that need a Mac leg.

| Tree | Class 1 rows | Class 2 rows | Total rows |
|---|---:|---:|---:|
| src/clearwater | 6 | 68 | 74 |
| tools | 9 | 43 | 52 |
| tests excluding harness | 27 | 19 | 46 |
| Total | 42 | 130 | 172 |

The product total includes three ruled sites arriving with WP6.1, not yet on
main (P56-P58); those are not included in the grep counts of current code.
P65/T49-T51 separately identify static-target failures at sites whose runtime
behaviour is covered earlier; semantic rows are not a count of unique lines.

REASONED: the existing product has a usable CPU/x265 path and an automatic
default decoder-pipe fallback. The missing commissioned leg is VideoToolbox;
the current encoder registry cannot select it. The proposed Library policy, APFS
identity cases, native GUI behaviour, and a self-contained arm64 bundle need
follow-on implementation or validation. No Windows product defect was confirmed.

This is a code audit with documentation research, not Mac execution evidence.
Every current macOS assessment below is labelled REASONED or DOC. "Works" means
the inspected portable mechanism is expected to work, not that it was run.
"Untested" preserves uncertainty about a real build, filesystem, or native UI.
Recommended changes and proposed tests are future work, not completed work.

## 2. Grep record

These are the accepted round-0 commands and counts; W and R were rerun exactly
at Reviewer A round 1 on 4f67743f; W on LF blobs was checked at round 2 on
1e59f941. Other scans were not repeated by this cell. PowerShell was
the shell. Each pattern below was assigned to $p and counted separately for each
root by this exact loop:

    foreach ($root in @('src/clearwater','tools','tests')) {
        $a = @(rg -n -g '!**/harness/**' -e $p $root)
        $f = @(rg -l -g '!**/harness/**' -e $p $root)
        Write-Output ($root + ' | lines=' + $a.Count + ' | files=' + $f.Count)
    }

### B: requested Class 1 baseline

    $p = 'sys\.platform|os\.name|platform\.system\(|CREATE_NO_WINDOW|msvcrt|windll|LOCALAPPDATA|APPDATA'

Counts: src 13 / 2; tools 10 / 3; tests 42 / 19.
The product's two files are config/paths.py and io/video/pipes.py. The 13 lines
include documentation as well as code; they are not 13 distinct conditionals.

### W: first widening

    $p = 'startupinfo|creationflags|winreg|ctypes|\.exe\b|powershell|\bwhere(?:\.exe)?\s|cmd /c|[A-Za-z]:\\|\bnul\b|os\.startfile|WinDLL|SetNamedPipeHandleState|CreatePipe|PeekNamedPipe|GetLastError|O_BINARY|O_NOINHERIT|os\.uname|platform\.machine|fork|spawn|posix|darwin|win32|Windows|macOS|linux'

Counts: src 103 / 31; tools 166 / 30; tests 286 / 62.
These W counts describe the CRLF Windows checkout. Committed LF-text counts
are 103 / 31, 164 / 30, 285 / 62 respectively; the round-2 blob check confirms
them. REASONED: a Mac checkout using LF text should match those byte semantics;
no Mac run is claimed.
W is an additional search, not B union W. It intentionally admits prose.
Its drive-letter pattern also catches regex fragments such as n:\s.

### R: refined Class 1

    $p = 'sys\.platform|os\.name|platform\.system\(|CREATE_NO_WINDOW|msvcrt|windll|LOCALAPPDATA|APPDATA|startupinfo|creationflags|winreg|ctypes|\.exe\b|powershell|\x22where(?:\.exe)?\x22|\x27where(?:\.exe)?\x27|\x22cmd\x22|\x27cmd\x27|cmd /c|[\x22\x27][A-Za-z]:\\|os\.startfile|_winapi|WinDLL|O_BINARY|O_NOINHERIT'

Counts: src 19 / 2; tools 36 / 5; tests 88 / 21.
R adds launch keywords and explicit command/path literals while removing prose
"where", generic platform prose, and unanchored drive-like regex fragments.
Hexadecimal quote escapes avoid native PowerShell argument-quoting ambiguity.

The predecessor's 109-file tools/tests result has no exact command in the
dispatch, so it is not a reproducible identity target. W matched 92 files across
those roots; R matched 26. Neither number includes the harness.
Two exploratory literal-quote patterns were discarded after shell transport
changed their meaning; their outputs do not support this report's counts.

### A0: initial Class 2

    $p = 'hevc_nvenc|libx265|nvidia-smi|memGetInfo|cuda|suffix|\.MP4|\.MOV|\.HEIC|normcase|casefold|lower\(|resolve\(|is_relative_to|commonpath|TMP|TEMP|tempfile|tempdir|split\(.*/|replace\(.*/|backslash|separator'

Counts: src 211 / 36; tools 438 / 43; tests 1124 / 100.

### A: refined Class 2

    $p = 'hevc_nvenc|libx265|nvidia-smi|memGetInfo|free_device_bytes|CUDA_CONTEXT_BYTES|NVDEC_|NVENC_|suffix\.lower\(|normcase|casefold|splitdrive|is_junction|isjunction|samestat|samefile|TMPDIR|PYTEST_DEBUG_TEMPROOT|[\x22\x27](?:TMP|TEMP)[\x22\x27]|EXTENDED_PREFIXES|_FORBIDDEN|_DEVICE_NAMES|QT_QPA_PLATFORM|offscreen|devicePixelRatio|Ctrl\+|sys\.executable'

Counts: src 94 / 25; tools 183 / 27; tests 481 / 79.
A narrows generic CUDA, suffix, resolve, and lower-case prose to named mechanisms.

### S: filesystem, process, names, fixtures

    $p = 'backslash|separator|reserved|NUL|CONIN|CONOUT|\.MP4|\.mp4|\.MOV|\.HEIC|F_SETPIPE_SZ|fcntl|resource|SIGTERM|SIGKILL|SIGBREAK|killpg|setsid|start_new_session|shell=True|chmod|fchmod|fsync|os\.link|os\.replace|os\.rename|os\.environ.*(?:HOME|PATH)|gettempdir|tempfile'

Counts: src 77 / 31; tools 153 / 30; tests 1011 / 96.
S retains rejected-name tests, filesystem publication semantics, and historical
instrument assumptions. NUL-byte, JSON-separator, and binary-format terminology
is not itself a platform site.

### L: literal backslash coverage

    $p = '\\'

The same per-root loop used rg -n -F and rg -l -F, retaining the harness exclusion.
Counts: src 8 / 4; tools 35 / 10; tests 95 / 29.
This is a literal two-backslash search, not a regex for every backslash.
Regex escapes, newline escapes, and ASCII backslash-escaping of diagnostics were
classified as data/format handling rather than Windows filesystem dependencies.

Targeted rg reads then followed the actual mechanics at the file:line sites
below: suffix routing, containment/identity, encoder options and stderr parsing,
memory selection, native GUI entry points, and Windows-only test controls.
No scripts were audited, no product/tool subprocess invoking "where" or
PowerShell was run, and no footage was opened.

### Reviewer A round 1: W/R reproduction record

Tool: `rg --version` returned `ripgrep 15.2.0 (rev e89fff89ac)`;
features +pcre2, PCRE2 10.45 available, default regex engine used (no -P).
The exact W/R patterns and per-root loop above reproduce the original totals:
W = 103/31, 166/30, 286/62; R = 19/2, 36/5, 88/21.
These are CRLF Windows working-tree counts; the W per-file roster below uses
that checkout, not the committed LF blobs.
Per-file matching-line counts below were produced with:

    rg -c -g '!**/harness/**' -e $p $root

An independent Python re scan over git ls-files also reproduced those totals
when UTF-8 bytes were split on literal LF, retaining CR. Its command was
`python -` with the following input, run from this worktree (read-only):

```python
from pathlib import Path
import re
import subprocess

report = Path("docs/reports/wp6.2-portability-audit.md").read_text()
for key in ("W", "R"):
    section = report.split("### " + key + ":", 1)[1]
    pattern = re.search(r"(?m)^    \$p = '(.*)'$", section)[1]
    for root in ("src/clearwater", "tools", "tests"):
        lines = files = 0
        names = subprocess.check_output(["git", "ls-files", root], text=True)
        for name in names.splitlines():
            if "/harness/" in name:
                continue
            try:
                text = Path(name).read_bytes().decode("utf-8")
            except UnicodeError:
                continue
            hits = sum(bool(re.search(pattern, line)) for line in text.split("\n"))
            lines += hits
            files += bool(hits)
        print(key, root, lines, files)
```

CR handling explains a concrete difference: read_text().splitlines() removes
the CR that rg can match with W's terminal \s. That variant gives W 103/31,
164/30, 285/62; it loses tools/lookcheck/pack.py:422,
tools/prototype/pipeline.py:488 and tests/test_prototype_backend.py:211, each
ending in "where". R still reproduces 19/2, 36/5, 88/21 in that variant.
This explains three missing W lines, not all of the reviewer's lower figures.
The review supplied no Python program; the remainder of its discrepancy cannot
be established from "Python re over git ls-files" alone. No binary/encoding or
regex-engine cause is asserted. The exact rg rerun, independent Python command
and per-file roster are the reproducible record; counts have not been guessed.

Reviewer A round 2 refinement, independently confirmed here: the three-line W
difference is a CRLF-checkout versus LF-blob effect. Using the same W pattern
over committed blobs gives src 103/31, tools 164/30 and tests 285/62. This
accounts for those three lines, not the rest of round 1's lower Python counts.
The blob check used `git ls-files src/clearwater tools tests` (excluding
tests/harness), fed `HEAD:<path>` requests to `git cat-file --batch`, decoded
UTF-8 blobs, split on literal LF and applied Python re.search once per line.
No checked-out source was rewritten. Reviewer A also reproduced all other
searches unchanged; this cell does not claim to have rerun those searches.

W/R per-file roster: src/clearwater (tests/harness excluded).

| File relative to tree | W lines | R lines |
|---|---:|---:|
| analysis/store.py | 1 | 0 |
| app/composition.py | 2 | 0 |
| app/export_worker.py | 1 | 0 |
| cache/keys.py | 1 | 0 |
| cache/layout.py | 1 | 0 |
| cache/store.py | 2 | 0 |
| config/log.py | 2 | 0 |
| config/paths.py | 7 | 6 |
| config/presets.py | 3 | 0 |
| core/backend.py | 1 | 0 |
| gui/analysis_service.py | 2 | 0 |
| gui/contract.py | 1 | 0 |
| gui/messages.py | 1 | 0 |
| gui/shell.py | 1 | 0 |
| gui/timeline.py | 1 | 0 |
| interfaces/parameters.py | 1 | 0 |
| interfaces/settings.py | 1 | 0 |
| io/photo/errors.py | 1 | 0 |
| io/video/capability.py | 3 | 0 |
| io/video/decode.py | 9 | 0 |
| io/video/encode.py | 6 | 0 |
| io/video/pipes.py | 9 | 13 |
| io/video/probe.py | 2 | 0 |
| io/video/verify.py | 18 | 0 |
| jobs/disk_space.py | 1 | 0 |
| jobs/export.py | 6 | 0 |
| jobs/export_process.py | 12 | 0 |
| jobs/naming.py | 1 | 0 |
| jobs/safe_write.py | 3 | 0 |
| methods/compensation.py | 2 | 0 |
| methods/fusion.py | 1 | 0 |

W/R per-file roster: tools (tests/harness excluded).

| File relative to tree | W lines | R lines |
|---|---:|---:|
| analysis_breakdown.py | 1 | 0 |
| container_spike/compare.py | 5 | 0 |
| core_speed.py | 1 | 0 |
| environment_report.py | 0 | 1 |
| export_bench.py | 2 | 0 |
| fixtures/files.py | 2 | 0 |
| fixtures/flicker.py | 1 | 0 |
| fixtures/manifest.py | 1 | 0 |
| fixtures/stills.py | 2 | 0 |
| fixtures/video.py | 1 | 0 |
| halo_part3.py | 6 | 0 |
| halo_probe.py | 9 | 0 |
| headless_export.py | 6 | 0 |
| inventory.py | 11 | 0 |
| local_config.py | 3 | 0 |
| lookcheck/frames.py | 3 | 0 |
| lookcheck/pack.py | 3 | 0 |
| lookcheck/scan.py | 1 | 0 |
| noise_experiments.py | 6 | 0 |
| prototype/bench.py | 22 | 12 |
| prototype/clip.py | 18 | 0 |
| prototype/pipeline.py | 6 | 0 |
| prototype/run.py | 1 | 0 |
| prototype/temporal.py | 6 | 0 |
| reviewpack/build.py | 4 | 0 |
| spike_io/licences.py | 1 | 1 |
| spike_io/photo.py | 2 | 0 |
| spike_io/transport.py | 31 | 21 |
| statistics_experiments.py | 3 | 0 |
| video_fidelity.py | 4 | 0 |
| video_io_bench.py | 4 | 1 |

W/R per-file roster: tests (tests/harness excluded).

| File relative to tree | W lines | R lines |
|---|---:|---:|
| acceptance_support.py | 1 | 0 |
| conftest.py | 8 | 4 |
| fixture_plugin.py | 1 | 0 |
| gui_support.py | 1 | 0 |
| test_app_activity.py | 1 | 0 |
| test_app_composition.py | 1 | 0 |
| test_app_export_worker.py | 4 | 0 |
| test_app_interface_load.py | 2 | 0 |
| test_app_leftovers.py | 2 | 0 |
| test_app_preview_fft.py | 3 | 0 |
| test_app_startup.py | 4 | 2 |
| test_app_v7.py | 2 | 0 |
| test_app_v8_v18.py | 2 | 0 |
| test_app_wiring.py | 5 | 1 |
| test_color_roundtrip.py | 3 | 0 |
| test_config_isolation.py | 0 | 2 |
| test_config_log.py | 1 | 0 |
| test_config_paths.py | 7 | 5 |
| test_config_presets.py | 3 | 0 |
| test_config_settings.py | 3 | 1 |
| test_conftest_guard.py | 19 | 18 |
| test_container_spike.py | 1 | 0 |
| test_core_backend.py | 1 | 0 |
| test_core_speed.py | 1 | 0 |
| test_fixture_cache_lock.py | 1 | 0 |
| test_fixtures.py | 5 | 0 |
| test_footage_locator.py | 4 | 2 |
| test_gate_timeout.py | 1 | 0 |
| test_gui_deps.py | 0 | 1 |
| test_gui_startup.py | 0 | 1 |
| test_gui_timeline.py | 1 | 0 |
| test_headless_export.py | 20 | 4 |
| test_inventory.py | 9 | 0 |
| test_io_video_decode_lifecycle.py | 6 | 2 |
| test_io_video_decode_rules.py | 0 | 2 |
| test_io_video_encode.py | 2 | 0 |
| test_io_video_encode_bench.py | 3 | 1 |
| test_io_video_encode_units.py | 4 | 0 |
| test_io_video_spawn.py | 56 | 21 |
| test_jobs_export.py | 6 | 0 |
| test_jobs_export_process.py | 29 | 4 |
| test_jobs_export_support.py | 1 | 0 |
| test_jobs_naming.py | 1 | 2 |
| test_jobs_safe_write.py | 1 | 0 |
| test_local_config.py | 3 | 0 |
| test_lookcheck.py | 1 | 0 |
| test_lookcheck_deep.py | 2 | 0 |
| test_methods_assembly_prototype.py | 1 | 0 |
| test_methods_compensation.py | 1 | 0 |
| test_methods_fusion_prototype.py | 1 | 0 |
| test_photo_verify.py | 3 | 0 |
| test_prototype_backend.py | 2 | 0 |
| test_prototype_clip.py | 8 | 0 |
| test_prototype_pipeline.py | 1 | 0 |
| test_reviewpack.py | 4 | 5 |
| test_spike_io_photo.py | 1 | 0 |
| test_tools_halo_probe.py | 6 | 0 |
| test_v51_photo_acceptance.py | 1 | 0 |
| test_video_fidelity.py | 1 | 0 |
| test_wp321_device_frames.py | 1 | 0 |
| test_wp42_composition.py | 2 | 0 |
| test_wp42_runner_video.py | 3 | 2 |
| test_wp42_v3_figures.py | 1 | 0 |
| test_wp42a_runner_hardening.py | 14 | 7 |
| test_wp42b_naming_guard.py | 2 | 1 |
| test_wp43_runner_redaction.py | 1 | 0 |

### Round-3 supplement: os.sep

    rg -n -g '!**/harness/**' 'os\.sep' src/clearwater tools tests

Matching lines / files: src 0/0, tools 1/1, tests 9/6. The os.sep platform
conditional at test_export_oracle.py:306 is X46; other hits are portable
separator construction or existing T19 local-config name handling. This
supplement does not alter the earlier B/W/R patterns or their counts.

## 3. Site table and test references

Paths in the first table are relative to src/clearwater; paths in the next two
are relative to tools and tests respectively. A row identifies one mechanism;
several lines belonging to that mechanism are cited together where necessary.
Retain means preserve the portable behaviour and add the stated coverage.
A named test reference W-... or M-... expands in section 8 to a proposed test
function and parameter contract. The bracketed row ID is that test's site
parameter, so every row has a specific Windows-side and Mac-side test target.
M references all require the proposed macos marker. No named new test exists yet.

### 3.1 Product

The static-target rows P65/T49-T51 cite Reviewer A round 2's EXECUTED Windows
mypy experiment, not Mac execution; runtime assessments remain REASONED.

| ID | File:line | Class | Assumption / mechanic | macOS today | Recommended change | Windows-side test | macos test |
|---|---|---|---|---|---|---|---|
| P01 | config/paths.py:115 | 1 | win32 uses APPDATA/LOCALAPPDATA; all else XDG | REASONED works via XDG, compliant with AD-25(a), no Library branch | PROPOSED Library locations in section 5 need CHARC's AD-25(a) amendment and N1 approval; retain Windows/XDG | W-PATH[P01] | M-PATH[P01] |
| P02 | io/video/pipes.py:56 | 1 | CREATE_NO_WINDOW in a conditional expression only on win32 | REASONED runtime uses zero flags; DOC review A r2: darwin-target mypy rejects the expression, P65 | Use an `if sys.platform == "win32": ... else: ...` statement with each platform's code inside its own branch: no early return, and no code after the guard that only one platform reaches. EXECUTED by Reviewer A r3: the early-return form fails the default win32 target with [unreachable]; the if/else form passes both `--platform win32` and `--platform darwin`. W-STATIC runs both targets. CHARC approval required for AD-23 helper; retain flags and FFREPORT policy | W-SPAWN[P02]; W-STATIC[P02] | M-SPAWN[P02]; M-STATIC[P02] |
| P03 | io/video/pipes.py:67,85,95,112-116 | 1 | _winapi/msvcrt enlarged pipe; OSError caught, fallback WARNING | REASONED works via default-pipe fallback | Retain default pipe for darwin, Q2; INFO off Windows is proposed, not decided | W-PIPE[P03] | M-PIPE[P03] |
| P04 | io/video/decode.py:335,350 | 2 | Separate enlarged/default stdout paths | REASONED works by fallback; throughput untested | Retain both lifecycle paths; validate frames/PTS | W-PIPE[P04] | M-PIPE[P04] |
| P05 | io/video/decode.py:132-149,759; jobs/export.py:905; app/analysis_adapter.py:377; gui/analysis_service.py:323; gui/sources.py:141 | 2 | CUDA trial is short-circuited by hw_decode=False; CPU and GUI callers pass false | REASONED software decode available without the CUDA trial or its WARNING on the CPU Mac path; R3-5 disputed with call-site evidence | Retain CPU short-circuit and pin no trial/extra process on that path; no new darwin-specific branch needed | W-DEVICE[P05] | M-DEVICE[P05] |
| P06 | io/video/decode.py:72 | 2 | Exact showinfo prefix, frame and time-base fields | REASONED untested on Mac FFmpeg | Validate pinned build text; change parser only for demonstrated difference | W-TEXT[P06] | M-TEXT[P06] |
| P07 | io/video/capability.py:35-42 | 2 | Registry offers NVENC/x265 only | REASONED fails to offer VT; x265 available | Platform encoder roster: darwin VT then x265 | W-CODEC[P07] | M-CODEC[P07] |
| P08 | io/video/capability.py:109 | 2 | Encoder-list flag/name parsing | REASONED untested against Mac build | Parse listing plus actual trial; include absent/failed VT cases | W-TEXT[P08] | M-TEXT[P08] |
| P09 | io/video/capability.py:50-56 | 2 | Trial format/profile table knows two encoders | REASONED VT absent | Add independent 8/10-bit VT trials | W-CODEC[P09] | M-CODEC[P09] |
| P10 | io/video/capability.py:57-66,160-169 | 2 | NVIDIA stderr fragments explain failures | REASONED generic failure path works; VT reason absent | Keep NVENC markers scoped to NVENC; preserve ASCII-safe VT diagnostic | W-TEXT[P10] | M-TEXT[P10] |
| P11 | io/video/capability.py:248-260 | 2 | Explicit names validated against ENCODERS; auto iterates that tuple | REASONED selects x265, never VT; saved VT name refused today | Platform preference with fallback; explicit/saved selection still validated | W-CODEC[P11] | M-CODEC[P11] |
| P12 | io/video/encode.py:107 | 2 | cq 22/26/30 and crf 21/26/30 are encoder-specific | REASONED x265 works; VT mapping absent | Separate VT controls; no numeric cq-to-qscale translation | W-RATE[P12] | M-RATE[P12] |
| P13 | io/video/encode.py:256 | 2 | NVENC output pixel-rate/level ceiling | REASONED arithmetic portable; VT application absent | Reuse numeric rule through an approved internal helper; map VT separately | W-RATE[P13] | M-RATE[P13] |
| P14 | io/video/encode.py:323 | 2 | non-NVENC branch emits x265 options | REASONED no VT command branch | Add explicit VT branch, never x265 params/preset/crf for VT | W-CODEC[P14] | M-CODEC[P14] |
| P15 | io/video/encode.py:100,404-405,418-421,434-455 | 2 | gpmd allowlist, hvc1, tmcd, rotation/NUT input, cut, timescale and negative CTS offsets | REASONED platform-neutral arguments; Mac mux/reorder behaviour untested | Preserve container policy in section 4; run full V4 and VT reorder/edit-list comparison | W-V4[P15] | M-V4[P15] |
| P16 | io/video/probe.py:100; WP6.1 brief, round-0 ruling D1 | 2 | shutil.which locates ffmpeg/ffprobe; frozen PATH prepend already ruled | REASONED source install works with PATH; bundle untested | Retain find_tool; validate D1's bundled-first lookup and resolved absolute paths, P57; make the missing-tool message (probe.py:118-119) platform-neutral; it is user-facing G10 text | W-SPAWN[P16] | M-BUNDLE[P16] |
| P17 | io/video/probe.py:74 | 2 | Transfer identifiers refuse HLG/PQ | REASONED works independently of encoder | Retain refusal before decode/encode; add VT selection control | W-V4[P17] | M-V4[P17] |
| P18 | core/memory.py:45 | 2 | memory_estimate_bytes implements D111 CUDA working-array bound | REASONED portable arithmetic, not a Mac RAM admission rule | Retain formula; report CPU RAM separately | W-DEVICE[P18] | M-DEVICE[P18] |
| P19 | core/memory.py:85 | 2 | CUDA/NVDEC/NVENC constants fitted on NVIDIA | REASONED inapplicable to Mac CPU jobs | Do not present these as unified-memory estimates | W-DEVICE[P19] | M-DEVICE[P19] |
| P20 | core/backend.py:551 | 2 | CPU free_device_bytes is None | REASONED works | Retain; never compare None with D111 estimate | W-DEVICE[P20] | M-DEVICE[P20] |
| P21 | core/backend.py:797 | 2 | CUDA free memory plus reusable CuPy pool | REASONED unused on CPU path | Keep CUDA-specific; no Apple GPU substitution | W-DEVICE[P21] | M-DEVICE[P21] |
| P22 | core/backend.py:933,943,1028-1029; gui/shell.py:549,554 | 2 | Optional CuPy import/device/kernel probe; AD-9 reason displayed by status bar | REASONED N14 CPU-only Mac automatic selection without CuPy shows "CPU: CuPy not installed"; explicit force CPU instead returns "CPU: forced" (:1028-1029), so B4's "every Mac" is overbroad | Retain graceful missing/unusable-CUDA paths; CHARC decides whether macOS gets a platform reason (with WP6.1 D7); W-GUI / M-GUI pin the text, including force CPU | W-DEVICE[P22]; W-GUI[P22] | M-DEVICE[P22]; M-GUI[P22] |
| P23 | core/backend.py:1027 | 2 | force_cpu/no CUDA returns before free-device query | REASONED works; Mac RSS unmeasured | Pin no-CUDA selection and distinguish RSS from GPU estimates | W-DEVICE[P23] | M-DEVICE[P23] |
| P24 | app/composition.py:461; WP6.1 brief, FINAL ruling Q5 | 2 | Current source worker is sys.executable -m module; frozen --export-worker re-entry already ruled, arriving with WP6.1 | DOC (repository) Q5 fixes mechanism; REASONED Mac bundle untested | VALIDATION only: Contents/MacOS re-entry, Qt-free/no extra GUI or Dock icon, protocol/cancel, no orphan FFmpeg; AD-34 at WP6.1 accept | W-SPAWN[P24] | M-BUNDLE[P24] |
| P25 | app/main.py:270 | 2 | Journal receives Locations.config_dir | REASONED follows current XDG resolver | Keep injected folder; native darwin branch flows through | W-PATH[P25] | M-PATH[P25] |
| P26 | app/startup.py:69 | 2 | write-journal.json resides in config_dir | REASONED works under XDG | Keep persistent config placement; Application Support is PROPOSED pending AD-25(a), never cache/app bundle | W-PATH[P26] | M-PATH[P26] |
| P27 | gui/sources.py:38 | 2 | Dialog filters enumerate lower-case suffix globs | REASONED native filter case behaviour untested | Validate mixed-case visibility; add upper-case globs only if needed | W-GUI[P27] | M-GUI[P27] |
| P28 | gui/sources.py:57 | 2 | Route lower-cases suffix | REASONED works for upper/lower extensions | Retain case-insensitive routing | W-FS[P28] | M-FS[P28] |
| P29 | gui/batch_panel.py:94 | 2 | normcase(abspath) is queue identity | REASONED APFS case-alias risk, DR candidate 1 | Existing-file identity plus conservative nonexistent fallback; preserve distinct files | W-FS[P29] | M-FS[P29] |
| P30 | gui/batch_panel.py:107 | 2 | normcase identifies duplicate display names | REASONED case treatment differs on Darwin | Align label policy with queue identity; avoid blanket filesystem casefold | W-FS[P30] | M-FS[P30] |
| P31 | gui/shell.py:465-476,488-489 | 2 | Qt controls native menu placement; Settings is Tools' sole action | DOC native menus [QT]; REASONED Settings/Quit text-heuristic merge may leave Tools empty, untested | Retain native menu; validate merged layout, empty Tools treatment, action access and corresponding G-check wording | W-GUI[P31] | M-GUI[P31] |
| P32 | gui/shell.py:480 | 2 | View shortcuts use Ctrl; Open/Quit StandardKey | DOC Qt maps Control to Command by default [QK] | Retain mapping; validate shortcuts, do not mechanically substitute Meta | W-GUI[P32] | M-GUI[P32] |
| P33 | gui/shell.py:274 | 2 | Native single-file dialog | REASONED untested | Validate filters, cancellation, Unicode and paths with spaces | W-GUI[P33] | M-GUI[P33] |
| P34 | gui/batch_panel.py:149 | 2 | Native multi-file dialog | REASONED untested | Validate multi-selection and mixed-case names | W-GUI[P34] | M-GUI[P34] |
| P35 | gui/preset_panel.py:126 | 2 | Native import/save dialogs and custom overwrite confirmation | REASONED untested | Preserve confirmation and JSON extension; validate native flow | W-GUI[P35] | M-GUI[P35] |
| P36 | gui/settings_dialog.py:160 | 2 | Native folder chooser | REASONED untested | Validate directory choice, cancellation and saved folder | W-GUI[P36] | M-GUI[P36] |
| P37 | gui/settings_dialog.py:542 | 2 | Capability rows drive encoder UI | REASONED generic row mechanism portable, VT absent | Populate platform roster; preserve unavailable saved selection with reason | W-CODEC[P37] | M-GUI[P37] |
| P38 | gui/preview.py:211,294,319,383 | 2 | Device-pixel ratio affects scale/render | REASONED implementation portable; native Retina untested | Retain 1:1 contract; validate DPR 1/2 and screen changes | W-GUI[P38] | M-GUI[P38] |
| P39 | config/presets.py:70 | 2 | Windows forbidden/device names rejected everywhere | REASONED works conservatively | Retain portable naming policy | W-FS[P39] | M-FS[P39] |
| P40 | config/presets.py:264,549-564; docs/debt-register.md:43, DR-34(a) | 2 | NFC/casefold predicts preset identity before atomic replacement | REASONED APFS folding/no-replace guarantee unproved, existing DR-34(a) | Retain logical identity distinct from arbitrary file identity; pin APFS folding corpus and no silent overwrite | W-FS[P40] | M-FS[P40] |
| P41 | gui/preset_panel.py:146 | 2 | UI uses matching NFC/casefold identity | REASONED works | Retain consistency with preset store | W-FS[P41] | M-FS[P41] |
| P42 | jobs/naming.py:34 | 2 | Suffix rejects both separators/Windows punctuation | REASONED works conservatively | Retain portable fragment restrictions | W-FS[P42] | M-FS[P42] |
| P43 | jobs/naming.py:116 | 2 | Temporary groups use casefolded final name | REASONED conservative collision grouping | Retain no-clobber grouping; document over-reservation | W-FS[P43] | M-FS[P43] |
| P44 | jobs/naming.py:171 | 2 | Reservations/nonexistent fallback casefold paths | REASONED may over-reserve distinct case-sensitive names | Preserve safety; test both actual volume case modes | W-FS[P44] | M-FS[P44] |
| P45 | jobs/naming.py:188 | 2 | Existing source/output guard uses samefile | REASONED portable identity mechanism | Retain identity comparison before lexical fallback | W-FS[P45] | M-FS[P45] |
| P46 | jobs/naming.py:300 | 2 | MOV output rule lower-cases source suffix | REASONED works | Retain .MOV -> _corrected.mp4 collision handling | W-FS[P46] | M-FS[P46] |
| P47 | jobs/export.py:111,725 | 2 | Reserved Windows device names refused | REASONED works conservatively | Retain cross-platform output safety policy | W-FS[P47] | M-FS[P47] |
| P48 | jobs/safe_write.py:112 | 2 | Link promotion then rename fallback | DOC POSIX overwrite-race limit already described in module:13, DR-16 | Retain documented envelope; test APFS/external-volume paths, no new safety claim | W-FS[P48] | M-FS[P48] |
| P49 | config/atomic.py:29-38; docs/debt-register.md:43, DR-34(a) | 2 | Same-directory temp, fsync, os.replace; no filesystem-enforced no-replace | REASONED portable replacement; APFS preset-name prediction unproved | Retain atomic replacement/cleanup; test DR-34(a) through preset overwrite=False with folding corpus | W-FS[P49] | M-FS[P49] |
| P50 | cache/keys.py:106 | 2 | Symlink/junction exclusion | REASONED junction branch irrelevant off Windows | Retain portable Python predicate and symlink refusal | W-FS[P50] | M-FS[P50] |
| P51 | cache/store.py:573 | 2 | Cache scan excludes links/junctions | REASONED portable mechanism | Validate cache reopen, pruning, link refusal on Mac | W-FS[P51] | M-FS[P51] |
| P52 | io/video/inputs.py:54 | 2 | Sidecar suffix lower-cased | REASONED works | Retain | W-FS[P52] | M-FS[P52] |
| P53 | io/photo/png.py:162 | 2 | PNG suffix lower-cased | REASONED works | Retain; verify 8/16-bit output on arm64 | W-FS[P53] | M-FS[P53] |
| P54 | io/photo/reader.py:319 | 2 | DNG suffix lower-cased plus metadata detection | REASONED portable logic; native codec wheels untested | Retain refusal/detection and validate HEIC/JPEG/TIFF codec stack | W-FS[P54] | M-FS[P54] |
| P55 | interfaces/settings.py:34,66 | 2 | Frozen-interface documentation names NVENC/x265 auto preference | REASONED stale for proposed VT roster | CHARC approves documentation disposition; preserve fields/signatures | W-CODEC[P55] | M-CODEC[P55] |

The following WP6.1 rows cite the rulings in docs/briefs/wp6.1-brief.md rather
than invented future code lines. P56-P58 are **arriving with WP6.1, not yet on
main**; DOC here means the mechanism is ruled, not executed on macOS.

| ID | File:line or ruling | Class | Assumption / mechanic | macOS today | Recommended change | Windows-side test | macos test |
|---|---|---|---|---|---|---|---|
| P56 | gpu_pack.py, pack_root; WP6.1 brief, FINAL Q6 | 1 | Windows LOCALAPPDATA/Clearwater/gpu-pack; Linux XDG_DATA_HOME/clearwater/gpu-pack (default ~/.local/share); darwin None | DOC (repository) darwin no-op ruled by N14; REASONED native run untested | Validate no CUDA pack lookup/load on Mac; preserve Windows/Linux roots | W-PATH[P56] | M-PATH[P56] |
| P57 | __main__.py; WP6.1 brief, round-0 D1 | 2 | Frozen-only dirname(sys.executable) prepended to PATH using portable os.pathsep | DOC (repository) prepend ruled; REASONED Mac collected-tool/onefile extraction location may differ, section 10 | Validate bundled-first lookup; either Contents/MacOS placement plus re-sign or CHARC-amended D1 adding sys._MEIPASS; keep find_tool unchanged | W-SPAWN[P57] | M-BUNDLE[P57] |
| P58 | gpu_pack.py; WP6.1 brief, round-0 D2 | 1 | os.add_dll_directory on nvidia/*/bin under win32 guard | DOC (repository) Windows-only call approved; REASONED darwin must not invoke it | Use an `if sys.platform == "win32": ... else: ...` statement with each platform's code inside its own branch: no early return, and no code after the guard that only one platform reaches. EXECUTED by Reviewer A r3: the early-return form fails the default win32 target with [unreachable]; the if/else form passes both `--platform win32` and `--platform darwin`. W-STATIC runs both targets. Retain Mac no-op, Linux equivalent open | W-SPAWN[P58]; W-STATIC[P58] | M-SPAWN[P58]; M-STATIC[P58] |
| P59 | io/video/encode.py:406-408 | 2 | encode_command computes rate only for HARDWARE_ENCODER (NVENC) | REASONED VT command would have no numeric ceiling | Map approved VT rate rule separately here and in _prepare, retaining NVENC | W-RATE[P59] | M-RATE[P59] |
| P60 | io/video/encode.py:703-713 | 2 | _prepare computes NVENC-only rate and geometry refusal | REASONED VT would bypass this admission path | Apply approved numeric rule and geometry refusal to VT before spawn | W-RATE[P60] | M-RATE[P60] |
| P61 | io/video/encode.py:593-595 | 2 | VideoSink.nvenc_rate is NVENC state; None for x265, outside frozen SinkReport | REASONED no VT rate state/reporting contract | Keep NVENC attribute semantics; add internal VT state only as approved, no frozen-interface change | W-RATE[P61] | M-RATE[P61] |
| P62 | io/video/encode.py:838-842 | 2 | _check_options refuses names outside ENCODERS | REASONED VT refused today | Align validation with approved platform roster and actual capability; retain unknown/unavailable refusal | W-CODEC[P62] | M-CODEC[P62] |
| P63 | gui/settings_dialog.py:95,507 | 2 | AUTO_TEXT hard-codes Automatic (NVENC when available) | REASONED inaccurate for proposed darwin VT preference | Platform-aware automatic label; CHARC routes owner-reserved G12 wording item, section 7 | W-GUI[P63] | M-GUI[P63] |
| P64 | jobs/disk_space.py:70-120,161 | 2 | D87/DR-48 estimate relies on NVENC ceiling and measured x265 sizes; disk_usage reports free bytes | REASONED VT estimate unproved; APFS purgeable capacity not represented as an explicit field | Pin existing arithmetic/Windows behaviour; WP6.5 measures VT sizes versus estimate and APFS free/purgeable-space behaviour | W-SPACE[P64] | M-SPACE[P64] |
| P65 | io/video/pipes.py:56; review A r2 N1 | 1 | Conditional expression does not narrow Windows-only subprocess attribute for darwin-target mypy | DOC review EXECUTED: attr-defined error on Windows targeting darwin; REASONED native static gate affected | Use an `if sys.platform == "win32": ... else: ...` statement with each platform's code inside its own branch: no early return, and no code after the guard that only one platform reaches. EXECUTED by Reviewer A r3: the early-return form fails the default win32 target with [unreachable]; the if/else form passes both `--platform win32` and `--platform darwin`. W-STATIC runs both targets. Subject to CHARC's AD-23 approval; retain runtime policy, P02 | W-STATIC[P65] | M-STATIC[P65] |
| P66 | io/video/encode.py:143-145 | 2 | 16 KiB provenance cap motivated by Windows command-line limit | REASONED conservative cap can remain; not a measurement of Mac ARG_MAX | Retain refusal boundary and ASCII-safe diagnostic | W-TEXT[P66] | M-TEXT[P66] |
| P67 | cache/store.py:126-150 | 2 | _unlink retries PermissionError for Windows open-file rule | REASONED harmless retry policy on POSIX | Retain retry/exhaustion/missing-file controls | W-FS[P67] | M-FS[P67] |
| P68 | io/video/encode.py:506-515 | 2 | _remove retries PermissionError after child exit | REASONED harmless retry policy on POSIX | Retain cleanup and bounded retry failure handling | W-FS[P68] | M-FS[P68] |
| P69 | jobs/safe_write.py:68-74 | 2 | Disk-full classifier accepts winerror 112/39 alongside ENOSPC/EDQUOT | REASONED portable errno path works; missing winerror handled by getattr | Retain both Windows and portable error cases | W-SPACE[P69] | M-SPACE[P69] |
| P70 | jobs/naming.py:304-311 | 2 | Composed output name refuses `:`, `\`, `/` taken from the source stem | REASONED fails: legal POSIX source names are refused | CHARC decides: keep the refusal with a message naming the character, or a mapped stem; no silent rename | W-FS[P70] | M-FS[P70] |
| P71 | gui/preview.py:394-399 | 2 | One zoom step per wheel event | REASONED: trackpad, momentum and natural scrolling untested; likely over-zooms | Accumulate angleDelta to 120 units per step; validate the direction. REASONED: the same per-event step applies to Windows precision touchpads; not checked on the laptop. W-GUI pins accumulation with synthetic sub-120 deltas; if confirmed on Windows, it becomes a DR row under the brief's rule for pre-existing defects | W-GUI[P71] | M-GUI[P71] |
| P72 | io/video/probe.py:67,504 | 2 | FFprobe stderr substring and displaymatrix text format | REASONED: depends on FFmpeg version, not OS; :504 is backed up by the corrupt-flag and nb_frames checks | Pin Mac-build samples (truncated and rotated fixtures) | W-TEXT[P72] | M-TEXT[P72] |
| P73 | config/presets.py:395-402; docs/debt-register.md:43, DR-34(a) | 2 | rename checks the target is free with the NFC/casefold prediction (_matches), then calls os.rename; Windows refuses an existing target (FileExistsError), POSIX replaces it | REASONED: a missed prediction or a race silently replaces another preset on macOS; no file-system refusal | Retain the prediction; CHARC decides on a no-replace rename (for example os.link then unlink) as a DR-34(a) extension or a new candidate DR | W-FS[P73] | M-FS[P73] |
| P74 | io/video/pipes.py:45-58; tools/headless_export.py:1391 | 2 | CREATE_NO_WINDOW also detaches children from console Ctrl+C on Windows; zero flags on POSIX leave FFmpeg and the worker in the terminal's process group | REASONED: a Terminal Ctrl+C reaches FFmpeg and the worker directly; an orderly cancel may end as a failure | Recommendation for CHARC under AD-23: start_new_session=True (or process_group=0) on POSIX in the helper, then validate child exit on parent death; or keep and document | W-SPAWN[P74] | M-SPAWN[P74] |

### 3.2 Tools

| ID | File:line | Class | Assumption / mechanic | macOS today | Recommended change | Windows-side test | macos test |
|---|---|---|---|---|---|---|---|
| T01 | environment_report.py:172 | 1 | platform.system/release/version identifies host | REASONED works | Retain; add architecture/backend/encoder facts, section 9 | W-TOOL[T01] | M-TOOL[T01] |
| T02 | environment_report.py:171 | 2 | GPU fields derive solely from nvidia-smi | REASONED NVIDIA fields unavailable, Apple identity absent | Explicit CPU-only/arm64 facts; absent CUDA is normal, not an invented GPU figure | W-TOOL[T02] | M-TOOL[T02] |
| T03 | prototype/bench.py:1157-1159 | 1 | Guarded Windows power-plan APIs | REASONED null runtime fields elsewhere; DOC review: darwin mypy unreachable diagnostic, T50 | Retain runtime telemetry policy; restructure static guard under CHARC target policy | W-TOOL[T03]; W-STATIC[T03] | M-TOOL[T03]; M-STATIC[T03] |
| T04 | prototype/bench.py:1467 | 1 | Windows CPU env versus cpuinfo/platform fallback | REASONED fallback exists; Apple model untested | Validate fallback; record unknown honestly | W-TOOL[T04] | M-TOOL[T04] |
| T05 | prototype/bench.py:1479-1482 | 1 | os.name guard around getwindowsversion | REASONED runtime fallback exists; DOC review: darwin mypy attribute error, T49 | Retain WMI-free runtime behaviour; use approved static-safe guard structure | W-TOOL[T05]; W-STATIC[T05] | M-TOOL[T05]; M-STATIC[T05] |
| T06 | prototype/bench.py:156 | 2 | Watched-process names are Windows services | REASONED Mac ambient attribution incomplete | Keep historical instrument labelled NVIDIA/Windows; separate Mac telemetry if commissioned | W-TOOL[T06] | M-TOOL[T06] |
| T07 | spike_io/transport.py:378 | 1 | Windows CreatePipe branch | REASONED alternate os.pipe path exists | Retain historical branch and explicit platform labels | W-PIPE[T07] | M-PIPE[T07] |
| T08 | spike_io/transport.py:388 | 2 | Optional Linux F_SETPIPE_SZ | REASONED default pipe retained without setter | Do not request Linux pipe tuning on Mac | W-PIPE[T08] | M-PIPE[T08] |
| T09 | spike_io/transport.py:948-950 | 1 | Guarded PowerShell GPU watcher | REASONED watcher omitted at runtime; DOC review: darwin mypy unreachable diagnostic, T51 | Retain omission; fix static guard under CHARC policy, no harness script port | W-TOOL[T09]; W-STATIC[T09] | M-TOOL[T09]; M-STATIC[T09] |
| T10 | spike_io/transport.py:116 | 2 | Windows ambient-process exclusions | REASONED Mac attribution incomplete | Label historical scope; new Mac instrument is separate work | W-TOOL[T10] | M-TOOL[T10] |
| T11 | spike_io/licences.py:132,149,152,158 | 2 | PyAV av.libs DLL globs and Windows DELVEWHEEL record; pillow-heif RECORD already accepts .so/.dylib | REASONED PyAV Mac wheel discovery needs delocate .dylibs coverage, not a blanket missing-dylib claim | Candidate DR 3: platform binary discovery for bundled artefacts; retain working pillow-heif native scan | W-TOOL[T11] | M-TOOL[T11] |
| T12 | spike_io/licences.py:188,192-210 | 2 | _CODE_SUFFIXES lacks .so/.dylib, so wheel_text_files reads those binaries as text | REASONED Mac binary/text classification incomplete | Candidate DR 3: include Mac extension/library forms, retain Windows forms | W-TOOL[T12] | M-TOOL[T12] |
| T13 | video_io_bench.py:118 | 2 | Sampler names accept bare and .exe | REASONED portable name set for existing sampler | Retain; label NVIDIA sampler | W-TOOL[T13] | M-TOOL[T13] |
| T14 | inventory.py:822-832 | 2 | os.walk, lower-case suffix, POSIX report-relative paths | REASONED works on case-sensitive volume; AppleDouble ._* names can pass suffix filter | Retain distinct paths/slash serialization; exclude AppleDouble or report unreadable, with synthetic control | W-FS[T14] | M-FS[T14] |
| T15 | inventory.py:293,301 | 2 | LRV stem/name matching ignores case | REASONED works | Retain sidecar matching independently of volume case | W-FS[T15] | M-FS[T15] |
| T16 | inventory.py:825 | 2 | Exclude comparison uses normcase | REASONED exclusion case treatment differs on Darwin | Make documented folder-name policy explicit; test exact and varied case | W-FS[T16] | M-FS[T16] |
| T17 | inventory.py:1112,1155 | 2 | Resolved/normcased text guards footage | REASONED APFS alias risk, candidate DR 2 | Add existing-ancestor identity containment before any mkdir/write | W-FS[T17] | M-FS[T17] |
| T18 | inventory.py:1094 | 2 | Link/exclusive-copy report publication | REASONED portable mechanism; real volume untested | Retain no-overwrite and partial-cleanup checks | W-FS[T18] | M-FS[T18] |
| T19 | local_config.py:140 | 2 | Both separator forms rejected in bare stem | REASONED works conservatively | Retain | W-FS[T19] | M-FS[T19] |
| T20 | local_config.py:196 | 2 | Lower-case suffix, casefold stem, ambiguity refusal | REASONED works on case-sensitive volume | Retain; test distinct same-stem matches | W-FS[T20] | M-FS[T20] |
| T21 | headless_export.py:598 | 2 | Lower-case suffix routing | REASONED works | Retain | W-FS[T21] | M-FS[T21] |
| T22 | headless_export.py:761 | 2 | Windows extended-prefix conversion | REASONED ordinary POSIX spelling unchanged | Retain Windows handling; no prefix surgery on POSIX names | W-FS[T22] | M-FS[T22] |
| T23 | headless_export.py:790,801 | 2 | Text containment plus ancestor samestat | REASONED portable identity path exists | Validate APFS aliases and link refusal before writes | W-FS[T23] | M-FS[T23] |
| T24 | headless_export.py:826,870 | 2 | Device/stream/drive/link-form refusal | REASONED conservative POSIX restrictions | Retain portable safe-name envelope | W-FS[T24] | M-FS[T24] |
| T25 | headless_export.py:414 | 2 | Path redaction accepts slash/backslash/escaped forms | REASONED portable mechanism; Mac path corpus untested | Add POSIX, spaces, Unicode normalization and nested-root controls | W-TEXT[T25] | M-TEXT[T25] |
| T26 | lookcheck/frames.py:161 | 2 | Resolved/normcased output containment | REASONED APFS alias risk | Candidate DR 2: identity-based guard, shared semantics not blanket casefold | W-FS[T26] | M-FS[T26] |
| T27 | container_spike/compare.py:1877 | 2 | Same containment mechanic | REASONED APFS alias risk | Candidate DR 2: identity-based guard | W-FS[T27] | M-FS[T27] |
| T28 | analysis_breakdown.py:984 | 2 | Lexical/realpath normcase containment | REASONED APFS alias risk | Candidate DR 2: identity-based guard | W-FS[T28] | M-FS[T28] |
| T29 | export_oracle.py:645 | 2 | Lexical/realpath normcase containment | REASONED APFS alias risk | Candidate DR 2: identity-based guard | W-FS[T29] | M-FS[T29] |
| T30 | halo_probe.py:2360 | 2 | Cache-conflict check uses normalized text | REASONED APFS case-alias risk | Validate identity of existing output/cache ancestors | W-FS[T30] | M-FS[T30] |
| T31 | halo_probe.py:2373 | 2 | Portable stem/device-name refusal | REASONED works conservatively | Retain | W-FS[T31] | M-FS[T31] |
| T32 | reviewpack/select.py:230 | 2 | Link pruning, casefold source matching | REASONED portable mechanism | Retain; duplicate matches must remain explicit | W-FS[T32] | M-FS[T32] |
| T33 | reviewpack/build.py:875 | 2 | Pair encoder x265 if force_cpu, otherwise NVENC | REASONED CPU leg available, default VT absent | Keep historical defaults labelled; explicit Mac CPU/VT option only if WP6.4 needs tool | W-CODEC[T33] | M-CODEC[T33] |
| T34 | prototype/clip.py:133 | 2 | Prototype encoding fixed to NVENC | REASONED fails without NVIDIA | Label historical Windows/NVIDIA instrument; do not silently port prototype algorithms | W-CODEC[T34] | M-CODEC[T34] |
| T35 | container_spike/spike.py:78 | 2 | Two encoders and NVIDIA proof sampler | REASONED x265 possible; VT leg absent | Separate Mac leg if reused; retain historical proofs | W-CODEC[T35] | M-CODEC[T35] |
| T36 | video_fidelity.py:377 | 2 | NVENC proof uses nvidia-smi pmon | REASONED x265 path available, VT proof absent | Add VT execution/V4 evidence without pretending NVIDIA sampler proves it | W-CODEC[T36] | M-V4[T36] |
| T37 | video_io_bench.py:147 | 2 | Fixed NVENC/x265 benchmark plan | REASONED no Mac plan | New explicitly Mac plan in WP6.5, not a retiming of Windows results | W-CODEC[T37] | M-CODEC[T37] |
| T38 | export_bench.py:580 | 2 | Every non-x265 leg gets NVIDIA sampler | REASONED VT would be misclassified | Dispatch telemetry by encoder/platform; no fake NVIDIA proof | W-TOOL[T38] | M-TOOL[T38] |
| T39 | core_speed.py:350 | 2 | NVIDIA telemetry with unavailable fallback | REASONED CPU result possible; GPU fields unavailable | Retain honest absence; separate CPU RSS | W-TOOL[T39] | M-TOOL[T39] |
| T40 | analysis_breakdown.py:848 | 2 | nvidia-smi occupancy sampler | REASONED occupancy unavailable | Retain unavailable reason; no Apple occupancy estimate | W-TOOL[T40] | M-TOOL[T40] |
| T41 | photo_verify.py:1161 | 2 | NVIDIA memory query | REASONED unavailable | Retain absent GPU field and CPU verification | W-TOOL[T41] | M-TOOL[T41] |
| T42 | device_hold.py:57 | 2 | Intentional CuPy allocation instrument | REASONED unavailable on CPU-only Mac | Label GPU-only; keep out of Mac required suite | W-DEVICE[T42] | M-DEVICE[T42] |
| T43 | prototype/backend.py:197 | 2 | Optional CuPy with CPU fallback | REASONED CPU path available | Retain fallback, distinguish explicit GPU request refusal | W-DEVICE[T43] | M-DEVICE[T43] |
| T44 | fixtures/video.py:317 | 2 | Synthetic HEVC generation needs x265 | REASONED works if supplied FFmpeg has x265 | Bundle/test x265 even when VT is preferred | W-CODEC[T44] | M-CODEC[T44] |
| T45 | fixtures/files.py:36 | 2 | Upper-case GoPro placeholder suffixes | REASONED portable names | Retain; never treat placeholder bytes as video | W-FS[T45] | M-FS[T45] |
| T46 | photo_check.py:68 | 2 | Lower-case photo suffix discovery | REASONED works | Retain | W-FS[T46] | M-FS[T46] |
| T47 | photo_verify.py:332 | 2 | Casefold duplicate photo roster detection | REASONED conservative on case-sensitive volumes | Retain explicit ambiguity, document logical identity | W-FS[T47] | M-FS[T47] |
| T48 | photo_memory.py:162 | 2 | Lower-case PNG suffix | REASONED works | Retain | W-FS[T48] | M-FS[T48] |
| T49 | prototype/bench.py:1480; review A r2 N1 | 1 | os.name guard does not narrow sys.getwindowsversion under darwin mypy target | DOC review EXECUTED: attr-defined error; REASONED runtime fallback still available | Approved static-safe platform guard, preserving WMI-free Windows reading and fallback | W-STATIC[T49] | M-STATIC[T49] |
| T50 | prototype/bench.py:1159; review A r2 N1 | 1 | Early non-win32 return makes subsequent Windows-only block unreachable to target checker | DOC review EXECUTED: unreachable error, no runtime failure claimed | Restructure guard for approved target matrix; keep strict/warn_unreachable and null non-Windows telemetry | W-STATIC[T50] | M-STATIC[T50] |
| T51 | spike_io/transport.py:950; review A r2 N1 | 1 | Early non-win32 return makes PowerShell setup unreachable to target checker | DOC review EXECUTED: unreachable error; REASONED runtime omission works | Restructure static guard; retain no real PowerShell invocation on Mac | W-STATIC[T51] | M-STATIC[T51] |
| T52 | export_oracle.py:661 | 2 | Drive refusal relies on host Path anchor | REASONED: accepts `C:x` on POSIX (a legal name) | Explicit `:` / `\` refusal as in halo_probe T31, or a per-platform expectation | W-FS[T52] | M-FS[T52] |

### 3.3 Tests

These rows describe test portability, not product defects. Keeping a Windows-only
control skipped on Mac is legitimate when a separately named Mac control covers
the relevant invariant. Meta-test proposals inspect fixtures/helpers with stubs
on Windows; they do not launch Windows APIs under a fake Darwin platform.

| ID | File:line | Class | Assumption / mechanic | macOS today | Recommended change | Windows-side test | macos test |
|---|---|---|---|---|---|---|---|
| X01 | conftest.py:111 | 1 | Strip extended prefix only on Windows | REASONED ordinary POSIX path retained | Retain conditional normalization | W-GUARD[X01] | M-GUARD[X01] |
| X02 | conftest.py:215 | 1 | Windows versus POSIX default temp candidates | REASONED POSIX candidate list exists | Pin TMPDIR/TEMP/TMP/system/cwd precedence for both platforms | W-GUARD[X02] | M-GUARD[X02] |
| X03 | conftest.py:134 | 2 | Existing-ancestor samefile containment | REASONED covers case aliases by identity; APFS untested | Keep identity fallback and prove both APFS case modes | W-GUARD[X03] | M-GUARD[X03] |
| X04 | conftest.py:214 | 2 | Mirror tempfile temp-variable order | REASONED portable logic | Retain early no-write guard; isolate all temp env variables | W-GUARD[X04] | M-GUARD[X04] |
| X05 | test_conftest_guard.py:82 | 1 | Test helper strips Windows prefix conditionally | REASONED portable alternate path | Retain; avoid claiming it canonicalizes APFS case | W-GUARD[X05] | M-GUARD[X05] |
| X06 | test_conftest_guard.py:329 | 1 | Case-alias control Windows-only | REASONED Mac case-insensitive coverage absent | Keep Windows case; add real-volume case-aware Mac control | W-GUARD[X06] | M-GUARD[X06] |
| X07 | test_conftest_guard.py:337 | 1 | Extended-length path control | REASONED correctly skipped | Retain Windows control; Mac ordinary-path counterpart | W-GUARD[X07] | M-GUARD[X07] |
| X08 | test_conftest_guard.py:346 | 1 | GetShortPathNameW control | REASONED correctly skipped | Retain guard; Mac symlink/ancestor identity counterpart | W-GUARD[X08] | M-GUARD[X08] |
| X09 | test_conftest_guard.py:381 | 1 | Junction versus symlink topology | REASONED symlink branch exists | Retain branch and explicit topology coverage | W-GUARD[X09] | M-GUARD[X09] |
| X10 | test_conftest_guard.py:478 | 1 | Volume GUID API control | REASONED correctly skipped | Retain Windows API guard; Mac volume identity case | W-GUARD[X10] | M-GUARD[X10] |
| X11 | test_conftest_guard.py:599 | 1 | Second Windows-only case-alias control | REASONED Mac coverage absent | Add matching Mac case-aware root control | W-GUARD[X11] | M-GUARD[X11] |
| X12 | test_conftest_guard.py:670 | 1 | Second volume GUID control | REASONED correctly skipped | Retain; Mac existing-ancestor counterpart | W-GUARD[X12] | M-GUARD[X12] |
| X13 | test_config_paths.py:44 | 2 | Darwin expected to use XDG | REASONED matches current resolver | Split darwin native roots from Linux XDG expectations | W-PATH[X13] | M-PATH[X13] |
| X14 | test_config_isolation.py:31 | 2 | Scrub Windows/XDG/HOME variables | REASONED current stores isolated | Include injected Darwin home/location; retain no-real-store checks | W-PATH[X14] | M-PATH[X14] |
| X15 | test_app_startup.py:178 | 2 | Child redirects Windows and XDG roots | REASONED isolated today, future Library root not redirected | Child HOME/location injection under tmp_path for Darwin | W-PATH[X15] | M-PATH[X15] |
| X16 | test_gui_startup.py:206 | 2 | App-data environment isolation | REASONED future Library branch needs coverage | Redirect all platform roots including child HOME | W-PATH[X16] | M-PATH[X16] |
| X17 | test_app_wiring.py:415 | 1 | Real NTFS ADS control | REASONED appropriately skipped | Retain; portable refused-name control remains required | W-GUARD[X17] | M-GUARD[X17] |
| X18 | test_footage_locator.py:48 | 1 | Guarded cmd /c mklink junction creation | REASONED junction skipped; symlink leg available | Retain Windows junction plus Mac symlink traversal exclusion | W-GUARD[X18] | M-GUARD[X18] |
| X19 | test_footage_locator.py:78 | 2 | Mixed-case stem/suffix fixture roster | REASONED portable coverage | Retain and add same-stem distinct-file ambiguity case | W-FS[X19] | M-FS[X19] |
| X20 | test_inventory.py:81 | 2 | MP4/mp4/MOV/HEIC fixtures | REASONED portable discovery coverage | Run on case-sensitive volume too; preserve every distinct path | W-FS[X20] | M-FS[X20] |
| X21 | test_headless_export.py:603 | 1 | Windows flag gates native-path cases | REASONED ordinary POSIX cases remain | Keep Windows controls; add POSIX aliases/Unicode cases | W-GUARD[X21] | M-GUARD[X21] |
| X22 | test_headless_export.py:629 | 2 | C-drive strings exercise prefix conversion | REASONED string-level control, not a real POSIX drive | Use ntpath/PureWindowsPath for foreign syntax tests; no host Path fiction | W-FS[X22] | M-FS[X22] |
| X23 | test_io_video_decode_lifecycle.py:407 | 1 | Real enlarged-pipe assertion Windows-only | REASONED appropriately skipped | Preserve; add default-pipe real lifecycle case | W-PIPE[X23] | M-PIPE[X23] |
| X24 | test_io_video_decode_lifecycle.py:424 | 1 | Second enlarged-pipe assertion Windows-only | REASONED appropriately skipped | Preserve; add fallback cancellation/cleanup case | W-PIPE[X24] | M-PIPE[X24] |
| X25 | test_io_video_decode_rules.py:97 | 2 | Scan pins approved OS-specific decode module | REASONED portable source-policy check | Update only after CHARC AD approval; keep planted violation control | W-TEXT[X25] | M-TEXT[X25] |
| X26 | test_io_video_spawn.py:274,278 | 1 | Native flag expectation; Linux simulation | REASONED native zero-flag branch exists, explicit Darwin case absent | Parameterize win32/linux/darwin with stubbed Windows constant | W-SPAWN[X26] | M-SPAWN[X26] |
| X27 | test_io_video_spawn.py:324 | 2 | Mock ffprobe/ffmpeg paths end .exe | REASONED mocks do not need Windows binaries | Retain foreign-name tests; include extensionless executable stub | W-SPAWN[X27] | M-SPAWN[X27] |
| X28 | test_jobs_export_process.py:544 | 1 | Root spelling selected by platform | REASONED POSIX branch exists | Retain; add frozen-command protocol path in bundle smoke | W-SPAWN[X28] | M-BUNDLE[X28] |
| X29 | test_jobs_naming.py:182 | 2 | Case-insensitive clash controls probe actual volume | REASONED skip on case-sensitive volume | Add distinct-case no-clobber case instead of treating skip as complete coverage | W-FS[X29] | M-FS[X29] |
| X30 | test_jobs_naming.py:452 | 1 | Windows-only junction fallback after symlink attempt | REASONED symlink path exists | Retain; Mac source-alias refusal through symlink | W-GUARD[X30] | M-GUARD[X30] |
| X31 | test_reviewpack.py:366 | 1 | Windows junction, symlink elsewhere | REASONED portable alternate control | Retain both topology legs | W-GUARD[X31] | M-GUARD[X31] |
| X32 | test_wp42a_runner_hardening.py:99 | 1 | Drive-relative output reproduction | REASONED correctly skipped | Keep real Windows case; portable invalid-output test | W-GUARD[X32] | M-GUARD[X32] |
| X33 | test_wp42a_runner_hardening.py:134 | 1 | NTFS one-letter carrier | REASONED correctly skipped | Retain native control; foreign syntax tested as data | W-GUARD[X33] | M-GUARD[X33] |
| X34 | test_wp42a_runner_hardening.py:197 | 1 | PowerShell stream-enumeration helper | REASONED native ADS callers Windows-only, stub control portable | Assert no real PowerShell call off Windows | W-GUARD[X34] | M-GUARD[X34] |
| X35 | test_wp42a_runner_hardening.py:234 | 1 | Real hard-link/ADS reproduction | REASONED correctly skipped | Retain Windows case; Mac hard-link output/footage identity control | W-GUARD[X35] | M-GUARD[X35] |
| X36 | test_wp42a_runner_hardening.py:464 | 1 | Self-junction versus symlink-loop | REASONED junction skipped; symlink topology available | Retain bounded refusal for Mac symlink loop | W-GUARD[X36] | M-GUARD[X36] |
| X37 | test_wp42b_naming_guard.py:29 | 1 | Real ADS source control | REASONED correctly skipped | Retain Windows guard; portable naming refusal counterpart | W-GUARD[X37] | M-GUARD[X37] |
| X38 | test_wp42_runner_video.py:74 | 1 | Guarded cmd junction helper | REASONED junction cases skipped | Add Mac symlink/alias footage guard case before CPU video run | W-GUARD[X38] | M-GUARD[X38] |
| X39 | gui_support.py:12 | 2 | QT_QPA_PLATFORM defaults to offscreen | REASONED plugin availability untested | Keep offscreen for unit suite; native cocoa smoke separately | W-GUI[X39] | M-GUI[X39] |
| X40 | test_gui_preview.py:349 | 2 | Offscreen child sets QT_SCALE_FACTOR=2 | REASONED synthetic DPR control, not Retina evidence | Retain scale control plus native display test | W-GUI[X40] | M-GUI[X40] |
| X41 | test_gui_settings_dialog.py:489 | 2 | Exact auto/NVENC/x265 row expectation | REASONED no VT roster coverage | Parameterize platform capabilities, unavailable/saved encoder cases | W-CODEC[X41] | M-GUI[X41] |
| X42 | test_io_video_encode.py:77 | 2 | x265/NVENC encoder matrix | REASONED no VT encode/V4 leg | Add Mac VT 8/10-bit matrix; keep Windows NVENC coverage | W-CODEC[X42] | M-V4[X42] |
| X43 | test_io_video_encode.py:1851 | 2 | Capability set pinned to two names | REASONED no platform roster expectation | Parameterize roster and auto resolution | W-CODEC[X43] | M-CODEC[X43] |
| X44 | test_core_backend.py:35 | 2 | NumPy plus gpu-marked CuPy parameters | REASONED CPU leg available; GPU unavailable | Keep CUDA-specific tests separate from CPU Mac gate | W-DEVICE[X44] | M-DEVICE[X44] |
| X45 | acceptance_support.py:73 | 2 | Privacy assertion normalizes separators and casefolds | REASONED conservative portable assertion | Retain; add native POSIX/Unicode path spellings | W-TEXT[X45] | M-TEXT[X45] |
| X46 | test_export_oracle.py:303-309 | 1 | `C:x` expected refused on every host; os.sep conditional at :306 | REASONED fails on macOS | Make the expectation match T52's chosen policy | W-FS[X46] | M-FS[X46] |

Screening-only Class 1 matches not requiring another product change include
test_config_settings.py:367 (R: a parameter named "where"), test_gui_deps.py:79 forbidden
environment-access assertions, test_io_video_encode_bench.py:44 a Windows
launcher comment, test_jobs_export_process.py:522/858 foreign path text, and
test_reviewpack.py:2237/2589 Windows DLL diagnostic strings. They remain data,
mocking, or policy controls. test_config_settings.py:461 is a W match for "nul"
(the malformed-NUL-path control), not an R/Class 1 refined match.
ASCII backslash escaping in io/photo/errors.py:30,
io/video/inputs.py:42, gui/messages.py:48, jobs/disk_space.py:66,
jobs/export_process.py:775 and app/export_worker.py:267 is deliberately
platform-independent and should be retained, not changed to a path conversion.

## 4. Encoder: the VideoToolbox leg

### Current contract and proposed roster

REASONED from capability.py:35-42,50-56,249 and encode.py:323: the application currently
offers only hevc_nvenc and libx265. Actual trial success determines availability
and depth; NVIDIA-specific stderr matching improves reasons, not the success
predicate. The generic failure path already captures a bounded ASCII-safe tail.
Listing an encoder alone is insufficient evidence that hardware can encode.

Recommendation for WP6.4: on darwin offer hevc_videotoolbox as the preferred
hardware encoder and libx265 as software fallback; preserve the Windows
NVENC/x265 preference. Preserve explicit unavailable saved choices with a reason
instead of silently changing them. Use the existing EncoderCapability shape,
including independent bit_depths and hardware flag. CHARC must authorize any
frozen-interface documentation correction (P55); no field/signature change is
proposed. CPU correction and VideoToolbox hardware encoding are separate choices:
force_cpu must not automatically force x265.

Proposed Mac listing/help and 8-bit capability command, not executed here:

    ffmpeg -hide_banner -encoders
    ffmpeg -hide_banner -h encoder=hevc_videotoolbox
    ffmpeg -nostdin -hide_banner -loglevel error -f lavfi -i color=c=black:s=256x256:r=25:d=0.04 -frames:v 1 -c:v hevc_videotoolbox -allow_sw 0 -pix_fmt yuv420p -profile:v main -f null -

Repeat the trial with p010le and main10 for 10-bit. Use the resolved absolute
FFmpeg path, shared spawn helper, timeout, captured stderr and process cache.
Do not allow a VideoToolbox software fallback to masquerade as hardware success;
libx265 is the explicit software fallback. Probe qscale and rate controls
separately from this minimal availability trial. A failed depth is disabled
without hiding a working 8-bit encoder.

DOC [FF]: the n8.0 source gates qscale on Apple Silicon, maps q:v quality to a
0..1 property through a 0..100 scale, and uses AverageBitRate without qscale.
Its HEVC formats include yuv420p, nv12 and p010le, with Main/Main10 support.
It maps maxrate to a one-second DataRateLimits request. A failed HEVC rate-limit
property can be logged while initialization continues. These are upstream source
facts, not proof of the future bundled build.

Recommendation: use yuv420p/Main at 8-bit and p010le/Main10 at 10-bit for VT,
retaining yuv420p10le/Main10 for x265. Keep CPU frame transport and correction
unchanged; VT consumes the converted output, not a Metal correction backend.
Each depth must pass a real encode and FFprobe decoded-format/profile check.
REASONED 10-bit conversion: the -vf from color/swscale.py:181-203 ends in
format=yuv420p10le; NVENC's p010le is FFmpeg's automatic conversion after it, and
VT's would be the same. Keep encode_filter (AD-10 flags) unchanged; verify the
decoded format and profile.
A null-muxer trial alone does not validate MP4, timestamps or metadata.

### Q1: two controls, no selection in this audit

Candidate A is q:v Q_LEVEL, with High/Standard/Draft values measured in WP6.5.
Candidate B is b:v R_LEVEL with maxrate R_LEVEL, using the same ceiling below.
Candidate A may also request that ceiling, but must not claim it is effective
without the Mac rate-control evidence. Do not copy cq 22/26/30 into q:v, copy
NVENC-only presets/tune/rc/tier flags, or route VT through the x265 else branch.
No Q_LEVEL values or final A/B preference are selected by this report.

REASONED: WP6.5 must compare both candidates on busy and calm SDR clips, inspect
stderr for rejected/ignored controls, record video bitrate and rolling-window
rates, output profile/level/tier, visual quality, and repeatability on the actual
Mac/FFmpeg/OS combination. Exit zero alone does not establish a bitrate ceiling.
If a required control is unsupported, surface that fact and use the documented
fallback policy; do not silently claim NVENC-equivalent control. The brief
explicitly reserves this measurement and choice for WP6.5.

REASONED from jobs/disk_space.py:70-120,161 (P64): its NVENC-bounded estimate is
not yet proved conservative for VT, especially candidate A's potentially ignored
ceiling; WP6.5 must compare actual output bytes with the estimate at every quality
and depth, and check APFS free versus purgeable capacity rather than treating the
disk_usage free figure as Finder's reclaimable capacity.

### Rate-rule mapping from encode.py:256

The existing nvenc_rate function is the exact numeric reference, not a loose
"half the source bitrate" target:

1. Reject nonpositive frame rate. Use output dimensions and source average fps
   for VFR: H0 = floor((24/100) * width * height * fps).
2. If a known HEVC source level is Main tier, H = min(H0, its Main-tier cap).
   Otherwise H = H0. H.264, unknown level, and High-tier source do not supply
   that source cap.
3. For high/standard/draft, R0 = max(H // divisor, 1), divisor 1/2/4.
4. Find Main-tier levels fitting luma picture size, dimension bound, and luma
   sample rate. Refuse if none fits. Select the lowest fitting level whose
   bitrate cap holds R0, or the highest fitting level if none holds it.
   R = min(R0, that level's cap).
5. Existing NVENC uses maxrate R, bufsize R and explicit Main tier/selected level.
   Preserve this unchanged on Windows. For VT, map the numeric R to maxrate and
   to b:v for candidate B. Treat level/tier enforcement and buffer behaviour as
   encoder-specific: the NVENC flags are not a portable VT API.

Recommendation: an internal rate helper can expose the existing calculation
without altering frozen interfaces, subject to CHARC's AD row. Tests must pin
rounding, source cap, VFR average, all three divisors, unsupported geometry and
highest-fitting-level clamp against the current function. VT's observed
level/tier still feeds the existing warning policy. macOS N6 is information,
not the Windows NVIDIA timing acceptance threshold (spec N1/N6 v0.6.0).

### Container and decoder invariants

REASONED from encode.py:100,404-455, probe.py:74 and verify.py:525: the current
MP4/FFprobe policy is platform-neutral, but the Mac build has not been exercised.
Retain hvc1, explicit color primaries/transfer/matrix/range, SAR/orientation,
copyts, passthrough fps mode, demux encoder time base, metadata mapping, and
timecode regeneration. Also retain -movflags +negative_cts_offsets (:454-455),
-video_track_timescale (:440-441), -noautorotate and conditional -display_rotation
(:404,418-419), the NUT input -bsf:v (:420-421), and the conditional -to cut
(:405,426) before the original-source input. Only gpmd is the currently proved non-timecode MP4 data
allowlist; mebx remains reported not carried, not newly advertised as preserved.

The Mac V4 leg must compare source/output through both the product verifier and
the established container_spike comparator, with MANDATORY and REQUIRED items
unchanged: per-frame PTS/time base/start offset/edit-list presentation effect;
video geometry, bit depth, color and display orientation; compressed audio
packet identity/timing, or PCM sample format/count/channel layout and bytes;
hvc1/HEVC profile/level/tier; timecode and gpmd best-effort fidelity; creation_time,
other supported metadata and provenance. Keep the existing report's distinction
between mandatory/required and best-effort results; never promote a tag merely
because its name appears in FFprobe JSON. Product verify.py does not list data
packet payloads, so it alone cannot prove gpmd/timecode payload fidelity.
Use existing equivalences for orientation, unset square SAR and mono layout.
REASONED: VT's reorder depth can differ from NVENC/x265; M-V4 must include a
reordered-frame case with negative CTS offsets and AD-22 edit-list reproduction,
checking presentation PTS/start/duration through both verifier and comparator.

REASONED: FFprobe's structured identifiers and container boxes do not depend on
a Windows shell. The showinfo parser and diagnostic-reason fragments do depend
on FFmpeg text/version and need pinned Mac-build samples. Do not redesign the
container path merely because the binary was built for another OS.

Retain the HLG/PQ refusal at probe.py:74 (arib-std-b67/smpte2084) before decoding
or VT selection. Ten-bit output support does not authorize HDR processing.
Tests must prove a VT-capable machine still refuses both transfers unchanged.

## 5. Paths: config, cache, journal and filesystem identity

Current behaviour is REASONED from config/paths.py:115: darwin takes the XDG
branch, with ~/.config/clearwater and ~/.cache/clearwater fallbacks.
DOC (repository), docs/decisions.md:34, AD-25(a), specifies XDG directories
outside Windows: today's darwin behaviour complies. The Library branch below is
PROPOSED, not approved; it requires CHARC's AD-25(a) amendment and approval of the
new N1 platform site. Retaining XDG is the currently compliant alternative.
The proposal uses the existing injectable home and Locations shape:

| Purpose | Proposed darwin path | Existing filename/subfolder |
|---|---|---|
| Settings and persistent application state | ~/Library/Application Support/Clearwater | settings.json |
| Presets | ~/Library/Application Support/Clearwater/presets | Existing preset format |
| Log, preserving current Locations.log_dir contract | ~/Library/Application Support/Clearwater/logs | clearwater.log |
| Export recovery journal | ~/Library/Application Support/Clearwater | write-journal.json |
| Re-creatable proxy cache and worker scratch | ~/Library/Caches/Clearwater | Existing cache layout; export/uuid scratch |

DOC [APPLE-FS]: macOS has user Library locations for application support and
caches. The particular Clearwater subfolder and retained logs-under-config
layout above are recommendations, not existing Mac behaviour. Keep journal and
settings out of an evictable cache. A migration, if required for an earlier
developer's XDG data, is an explicit CHARC item, not an automatic destructive move.
Windows APPDATA/LOCALAPPDATA and Linux XDG behaviour remain separately tested.
Do not make a bundled app use its current directory or installation directory
as an app-data location.
REASONED: ~/Library/Logs/Clearwater is an alternative native log location for
CHARC to consider with AD-25(a); the table preserves Locations.log_dir's current
logs-under-config contract pending that decision.

Both footage and working paths still come from local configuration; none of
these conventions replaces those owner-supplied paths. No audit command reads
them. Outputs remain in the configured/selected working destination and must
pass footage containment checks before any mkdir or write.

DOC [PY-PATH]: normcase folds case/separators on Windows and otherwise leaves
path text unchanged; samefile uses file identity. REASONED: changing normcase to
casefold everywhere would conflate genuinely distinct files on a case-sensitive
volume. Compare existing objects and ancestors by identity; use explicit
conservative fallback only for not-yet-existing names. Treat preset logical
identity separately from arbitrary source-file identity. Add composed/decomposed
Unicode names to the Mac corpus without assuming filesystem normalization.
DOC (repository), docs/debt-register.md:43, DR-34(a), already records that preset
overwrite=False depends on NFC/casefold name prediction before os.replace, not
filesystem-enforced no-replace. REASONED: case-insensitive APFS folding could
disagree with that prediction; M-FS must exercise dotless i (U+0131), sharp s
(U+00DF), and NFD versus NFC spellings, requiring unchanged original preset bytes
when overwrite=False and distinguishing genuinely separate files. This is
existing debt, not a newly confirmed Mac overwrite or Windows defect.

REASONED from gui/sources.py:57, inventory.py:828, local_config.py:196 and
headless_export.py:598: suffix discovery already ignores case. On a case-sensitive
volume, distinct upper/lower files remain discoverable; inventory emits both.
The stem locator reports multiple matches as ambiguity. Native QFileDialog
filter visibility is a separate test, not proved by suffix routing.
Portable forbidden names, both separators, drive/stream refusal and Windows
extended-prefix diagnostic handling should remain deliberate cross-platform
policies rather than accidental host-Path parsing.

## 6. Process: spawn flags, pipes and worker lifetime

REASONED from pipes.py:56: CREATE_NO_WINDOW is evaluated only on win32; elsewhere
creationflags is zero. REASONED: zero POSIX flags leave FFmpeg and the export
worker in the terminal's process group, so Terminal Ctrl+C reaches them directly
and orderly cancellation may become a failure; M-SPAWN must deliver SIGINT to
the process group (os.killpg), not raise_signal (P74).
Retain the shared helper at every product FFmpeg,
FFprobe and export-worker launch, including removal of every case spelling of
FFREPORT. Tests simulating win32 on Windows can use the real constant; tests on
Mac must stub its value rather than access an absent subprocess attribute.
This is ordinary subprocess spawning, not a request to port the harness.
DOC (repository), Reviewer B's source/Grep check: no code assumes fork. Only
tests/test_fixture_cache_lock.py:88 (explicit spawn) and tools/cache_store_test.py:842
(a ProcessPoolExecutor) use multiprocessing in this audit's trees. REASONED:
Python 3.12 defaults that executor to spawn on both Windows and macOS.

REASONED runtime behaviour does not prove static-target compatibility. P02/P65
need an `if sys.platform == "win32": ... else: ...` statement with each platform's code
inside its own branch: no early return, and no code after the guard that only one
platform reaches. EXECUTED by Reviewer A r3: the early-return form fails the default
win32 target with [unreachable]; the if/else form passes both `--platform win32` and
`--platform darwin`. W-STATIC runs both targets. Subject to CHARC's AD-23 approval;
WP6.1 D2's os.add_dll_directory guard uses the same shape (P58).
Section 8 records the reviewer's executed darwin-target errors and gate-policy item.

Q2 recommendation: use the existing OS-default decoder pipe on macOS for 1.2.0.
_create_pipe raises internally off Windows, open_frame_pipe catches OSError and
logs the fallback once, and decode.py uses subprocess.PIPE. No new pipe-sizing
syscall, Linux F_SETPIPE_SZ assumption or throughput guarantee is proposed.
The encoder already uses the default stdin pipe; it must not be described as
having the decoder's 32 MiB buffer (AD-23 note, docs/decisions.md:32).

DOC (repository): WP2.1S, docs/reports/wp2.1s-io-spike.md:234 and :236, measured
55.87 ms/frame default pipe (W2) versus 16.11 ms/frame enlarged pipe (W4), software
decode of GX011627, 681 frames at 3840x2160; byte hashes and PTS agreed.
These are historical Windows results under that report's conditions, not new
measurements or Mac forecasts. AD-23 expressly selects fallback for macOS.
DOC (repository): WP2.1S row s (:240) measured loopback TCP at 24.3 ms/frame on
Windows; REASONED: it is a candidate for a later Mac pipe study, not a 1.2.0 change.
REASONED from pipes.py:95: darwin's designed fallback emits WARNING once per
process, hence once per video export job because AD-31 starts a fresh worker
per job; WP6.4 should consider INFO off Windows (proposal, not an approved decision).

REASONED: a future full-clip Mac run would establish its actual default-pipe
throughput, RSS, bytes/frame counts, exact PTS pairing and cancellation/EOF
cleanup. A later pipe-tuning study would compare alternatives on that host.
This package measures nothing and does not infer a Mac regression from Windows
buffer figures.

DOC (repository), docs/briefs/wp6.1-brief.md, CHARC rulings at FINAL Q5:
app/composition.py builds [sys.executable, "--export-worker"] when sys.frozen,
retaining the source -m command otherwise; __main__.py dispatches --export-worker
to export_worker.main before any Qt-bearing import and passes remaining arguments
through unchanged. AD-34 is to be recorded at WP6.1's accept. This mechanism is
already ruled and arriving with WP6.1, not an open WP6.5 design item.
Retain AD-31's parent-resolved paths, Qt-free protocol, stdin cancellation,
stderr capture, bounded result handling and per-job scratch cache. REASONED:
the Mac work is VALIDATION of Contents/MacOS executable re-entry, no GUI or extra
Dock icon for the worker, progress/result/cancel, forced stop and no orphaned
FFmpeg; Windows process-tree evidence cannot establish Mac lifetime behaviour.
DOC (repository), WP6.1 round-0 D1/D2 and FINAL Q6 also rule the frozen PATH
prepend, win32-only DLL-directory call and darwin GPU-pack no-op (P56-P58).

## 7. GUI

DOC [QT, QK]: Qt supplies native macOS menus and maps its Control modifier to
Command by default. Recommendation: retain QKeySequence StandardKey and existing
Ctrl sequences unless an actual native test shows a problem. Do not blindly
rewrite Ctrl to Meta. Check Quit and Settings actions, menu roles, keyboard
focus, native file/folder dialogs, and application activation in a cocoa session.
REASONED from shell.py:465-476,488-489: text-heuristic menu merging may move
&Settings... and &Quit to the application menu, leaving Tools empty; M-GUI must
check the actual merged layout/empty-menu treatment and corresponding G-check
wording as well as action operation, without assuming Windows menu positions.

REASONED: lower-case dialog globs do not prove native dialog visibility of upper
suffixes. Open, batch-add, preset import/export and output-folder selection need
native cancellation and mixed-case/Unicode/path-with-spaces checks. Preserve
the preset overwrite confirmation and read-only footage rule.

REASONED: devicePixelRatioF is already used by preview.py. The offscreen
QT_SCALE_FACTOR=2 test is useful, but cannot establish native Retina rendering,
moving between displays, or menu/dialog placement. Require a native DPR 1/2
preview control with a known pixel pattern, fit and 1:1 views, zoom/split
interaction, and export/preview consistency. Keep the GUI free of direct
correction-backend imports and the export worker free of Qt.

REASONED from settings_dialog.py:95 (P63): AUTO_TEXT names only NVENC and needs a
platform-aware label for VT. CHARC must route the spec G12 wording item
(docs/underwater-correction-spec.md:414, NVENC/software auto preference) to the
owner; the spec is owner-reserved, and this report proposes no replacement text.

## 8. Tests: named platform parameters and Mac legs

All following tests are proposed for WP6.4/WP6.5, not tests run by this audit.
Suggested homes are tests/test_portability.py for stubbed platform cases and
tests/test_macos_portability.py for native cases; a Mac timing instrument is
separate WP6.5 work. The implementing brief must grant those files explicitly.
The table references expand below. Each proposed test function accepts site, selecting the
row's cited mechanic and expected outcome, so coverage is traceable by row ID.
A Windows-side W test uses real Windows behaviour plus injected platform values,
command builders, stubs, ntpath/posixpath/PureWindowsPath, or fake filesystem
identity. It must never patch sys.platform to Darwin and then run a real Windows
API as if that were a Mac. The corresponding M test uses actual native paths,
subprocesses or UI as stated.

| Reference | Proposed Windows-side function / static gate | Required platform parameters / meaningful control | Proposed macos-marked function |
|---|---|---|---|
| W-STATIC / M-STATIC | uv run mypy --platform win32 AND uv run mypy --platform darwin (Windows-side static gates; no new pytest function required) | Run on Windows against the commissioned source/tool set with both explicit win32 and darwin targets; preserve strict/warn_unreachable; no early-return platform guard; cover P02/P58/P65/T03/T05/T09/T49-T51 guard mechanics | test_macos_static_target_policy: macos-marked native gate wrapper runs pinned mypy against the same source/tool set, with darwin target and no platform spoofing |
| W-PATH / M-PATH | test_portability_app_locations | win32/darwin/linux; injected absolute home/env; missing/empty/relative env; settings/cache/log/journal roots; WP6.1 Q6 pack roots including XDG_DATA_HOME and darwin None; assert resolvers create nothing | test_macos_app_locations_and_isolation: native HOME redirection, stores/cache/journal under disposable home, no bundle/CWD writes, GPU-pack root None/no load |
| W-SPAWN / M-SPAWN | test_portability_spawn_policy | win32/darwin/linux; stub Windows constant and DLL-directory API; zero other flags; FFREPORT variants removed; spaces/non-ASCII argv; source/frozen worker and PATH selection; approved POSIX session/group option construction with stubs | test_macos_tool_and_worker_spawn: extensionless binaries, clean FFREPORT env, complete protocol/cancel/child cleanup, no Windows DLL API call; SIGINT delivered to the process group (os.killpg), not raise_signal; isolate the test process group and validate child exit on parent death |
| W-PIPE / M-PIPE | test_portability_default_pipe | win32 large success/failure and darwin/linux fallback; force pipe-sizing OSError; bytes/PTS/EOF/cancel and descriptor ownership | test_macos_default_pipe_fidelity: real decoder default pipe, bytes/PTS match fixture, no descriptor/child leak on cancel |
| W-DEVICE / M-DEVICE | test_portability_cpu_selection | force_cpu, no CuPy, failed CuPy import/kernel, fake CUDA success/free-memory failure; darwin CPU profile; CPU decode short-circuits CUDA trial; never reinterpret NVIDIA constants as CPU RAM | test_macos_cpu_without_cuda: clean CPU-only environment, correction/export, reason/RSS reporting; GPU-only instrument explicitly unavailable; Mac CPU output versus Windows-generated references within AD-11 tolerances, never byte identity. |
| W-CODEC / M-CODEC | test_portability_encoder_roster_and_commands | win32 NVENC/x265 and darwin VT/x265; listing absent/present; trial success/failure/8-only/10-bit; auto/explicit/saved-unavailable; no x265 options in VT | test_macos_videotoolbox_capabilities: actual VT/x265 trials, 8/10-bit outcome, unavailable fallback, explicit choice |
| W-RATE / M-RATE | test_portability_encoder_rate_mapping | platform/encoder, high/standard/draft; Fraction fps, VFR average, source Main/High/unknown caps, geometry/rounding/clamp; both VT candidates; unchanged Windows arguments | test_macos_videotoolbox_quality_controls: both candidates on busy/calm SDR, stderr and output rate/quality/profile/level; WP6.5 exclusive measurement |
| W-V4 / M-V4 | test_portability_container_contract | platform/encoder command snapshots plus structured FFprobe/container fixtures; preserve hvc1/color/SAR/timing/maps, NUT bsf, rotation, timescale, cut, negative CTS offsets; HLG/PQ refusal even with VT available | test_macos_videotoolbox_v4: real 8/10-bit MP4, VFR/start/edit-list/orientation/audio/metadata/provenance fixtures, VT reorder-depth/negative-CTS AD-22 case; product verifier plus full comparator |
| W-SPACE / M-SPACE | test_portability_disk_space_estimate | platform/encoder/quality/depth; pin D87/DR-48 arithmetic, injected disk_usage free bytes and insufficient-space refusal; do not count unproved purgeable bytes; ENOSPC/EDQUOT, absent winerror and 112/39 classifier controls; preserve Windows results | test_macos_videotoolbox_space_estimate: actual VT output size versus estimate for both Q1 candidates, depths and qualities; APFS free/purgeable-space behaviour and portable disk-full errno classification, WP6.5 exclusive measurement |
| W-TEXT / M-TEXT | test_portability_tool_text_and_redaction | Windows/Mac FFmpeg text fixtures; unknown wording/generic reason; malformed/missing showinfo; escaped drive and POSIX paths; planted privacy leak; provenance cap boundary/refusal | test_macos_ffmpeg_text_and_redaction: actual pinned build listing/showinfo/failure tails; native path corpus, no private roots in output |
| W-FS / M-FS | test_portability_filesystem_semantics | win32/darwin/linux syntax independent of host; fake samefile identities, distinct-file control, case-sensitive/insensitive modes; suffix/names/normalization/link/publish failures, AppleDouble ._clip.MP4 versus real clip.MP4 | test_macos_filesystem_semantics: actual case-insensitive and case-sensitive volumes, same-object aliases versus distinct files, links, no-clobber, codec outputs, exFAT AppleDouble exclusion/unreadable outcome; DR-34(a) case-insensitive APFS corpus U+0131/U+00DF/NFD/NFC with preset overwrite=False and unchanged original bytes; bounded unlink retries; Finder-typed `/` name in the source-name corpus (REASONED stored as `:` on macOS), with P70 refusal/mapping policy explicit; rename into each folding-corpus name; the other preset's bytes stay unchanged |
| W-GUARD / M-GUARD | test_portability_footage_guard_and_test_helpers | platform, temp origin, native-only API guard, alias topology; synthetic footage only; planted unsafe root must fail before writes, safe root must pass | test_macos_footage_guard_and_helpers: TMPDIR/TEMP/TMP/basetemp, ancestors/symlinks/hard links/loops/case aliases; snapshot synthetic footage unchanged |
| W-GUI / M-GUI | test_portability_gui_contract | platform capability rows and automatic label/AD-9 status reasons (including force CPU)/dialog stubs/shortcuts/DPR 1,2; synthetic sub-120 wheel deltas pin accumulation; cancellation and saved paths; missing offscreen plugin produces explicit environment failure | test_macos_native_gui_contract: cocoa menus/Command keys/native dialogs/Retina, VT-aware automatic label and CHARC-approved AD-9 reason including force CPU, Settings/Quit application-menu merge/empty Tools layout and G-check wording; trackpad scroll, momentum, natural scrolling; separate offscreen Qt unit-suite startup |
| W-TOOL / M-TOOL | test_portability_tool_reporting | win32/darwin/Linux reports; missing NVIDIA tool, stderr, unknown CPU model, binary suffix corpus and unsupported historical instrument; no fake telemetry | test_macos_tool_reporting: native environment facts, bundled binary inventory and notices, CPU tools run without NVIDIA dependencies |
| M-BUNDLE | W-SPAWN checks WP6.1's ruled source/frozen command construction; no Mac binary is run on Windows | source versus frozen; tool path and worker dispatch stubs; external PATH unavailable | test_macos_bundle_smoke: Finder/Terminal launch, no Python/FFmpeg on PATH, Contents/MacOS worker re-entry with no extra GUI/Dock icon, export/cancel/no orphan FFmpeg, native Qt plugins and persistent paths; Dock Quit, Cmd-Q and logout during an export each run `shutdown()` (settings saved, no worker or FFmpeg left running). |

REASONED: GitHub macos-latest CI may have no VT hardware; M-CODEC must accept a
proved "VT unavailable" capability/reason with x265 fallback, and M-V4 must run
x265 while explicitly skipping VT-only cases with that reason; neither replaces
the owner's hardware-Mac VT capability/V4 evidence required for WP6.5.

For a platform parameter that changes a source policy test, include a planted
forbidden launch/OS dependency and prove the checker fails by name, retaining the
existing positive controls. For a no-write guard, pair an unsafe synthetic root
with a safe sibling and check both behaviour and snapshots. For identity tests,
pair one object through two spellings with two genuinely distinct objects;
a blanket casefold implementation must fail the latter control.

Marker/dependency disposition, NOT owned by this package:

- pyproject.toml:79 registers gpu/footage/gui/slow/fullclip, but no macos marker.
  WP6.4 must register macos under strict markers and define selection/skip policy.
  A macos marker alone does not skip on Windows; add an explicit platform skip.
  Native cocoa tests also carry gui; timing/quality runs carry the appropriate
  isolation marker. Ordinary stubbed W tests must not acquire GPU requirements.
- pyproject.toml:46 and the :30 `gpu` extra declare cupy-cuda12x[ctk] in the
  default development group and optional GPU dependencies respectively; neither
  declaration has a platform marker.
  CHARC must commission a CPU-only Mac developer/test install group or platform
  dependency markers and lock verification. This report adds no dependency and
  assumes no Windows CUDA wheel can satisfy an arm64 Mac environment.
- pyproject.toml:105-109 sets strict and warn_unreachable but no mypy platform;
  DOC (repository) Reviewer A r2 EXECUTED on Windows:
  `timeout 900 uv run --no-sync mypy --platform darwin --cache-dir=nul`
  reported "Found 4 errors in 3 files": pipes.py:56, missing CREATE_NO_WINDOW;
  prototype/bench.py:1480, missing getwindowsversion; prototype/bench.py:1159
  and spike_io/transport.py:950, statement unreachable. Its default-platform
  command reported "Success: no issues found in 158 source files". This cell
  inspected the sites but did not rerun mypy; the evidence is the reviewer's.
  REASONED: a native darwin static gate inherits these failures. CHARC must
  decide/commission the target-platform policy, W-STATIC and guard changes,
  including ownership of the AD-23 helper; do not silently pin Windows or relax
  strict/warn_unreachable to hide the failures. N1 is MAJOR if WP6.4 includes
  a darwin static leg, minor if its static gate remains Windows-only; no runtime
  failure is claimed. WP6.1 D2 should use an `if sys.platform == "win32": ... else: ...` statement with each platform's code inside its own branch: no early return, and no code after the guard that only one platform reaches. EXECUTED by Reviewer A r3: the early-return form fails the default win32 target with [unreachable]; the if/else form passes both `--platform win32` and `--platform darwin`. W-STATIC runs both targets.
- Product pytest, lint/type checks, and the Mac native leg belong to WP6.4's
  implementation gate. The current read-only audit runs no pytest or build.
- The brief requires one harness suite at the final package gate because this
  report lives on the existing docs/reports instance surface. The dispatcher
  owns that gate. No harness vocabulary registration or harness edit is proposed;
  no harness suite was run by this cell in this turn.
- Run Mac tests against synthetic fixtures unless a separately configured,
  read-only footage set is explicitly supplied. Do not import the owner's
  Windows drive paths into Mac tests.
- Preserve Windows-only ADS, 8.3, volume-GUID and junction controls. Their skips
  are expected on Mac; portable counterparts must cover the shared safety rule.
  Existing gpu markers remain CUDA-specific, not a label for VT hardware encoding.

## 9. Tools and follow-on scope

Recommendation for environment_report.py: retain OS release/version, Python and
executable, uv/FFmpeg/git versions, CPU model/cores and RAM. Add process/build
architecture and explicit CPU correction backend; report VT/x265 availability
and 8/10-bit capabilities from the same trial model as the product. REASONED:
nvidia-smi absence is expected on the CPU-only target; keep its fields null with
a precise unavailable/not-applicable reason rather than calling Apple unified
memory "VRAM". Record the exact Mac model/OS/FFmpeg build for WP6.5 comparisons.
Do not invent a GPU-utilization percentage or borrow Windows memory constants.

Inventory and the headless runner already lower-case suffixes. Keep report paths
serialized with forward slashes while using Path for local I/O. Candidate DR 2
covers text-only footage containment in older tools; the headless runner already
has an identity fallback and supplies a useful semantic reference, not blanket
permission to copy its implementation without tests. The inventory folder
exclusion policy also needs explicit case treatment.
REASONED from inventory.py:822-832: macOS AppleDouble ._* files on exFAT/FAT can
pass the video suffix filter; WP6.4 should exclude them or show unreadable, not count them as playable clips (T14).

Historical prototype/spike instruments remain evidence of their original
Windows/NVIDIA experiments. WP6.4 need not retrofit every historical benchmark
to perform Apple hardware sampling. Its deliverable must explicitly label
unsupported instruments and keep the CPU/source workflows useful; WP6.5
commissions the new Mac measurement legs. Device-hold is deliberately CUDA-only.
If a historical instrument is reused for the Mac gate, add its VT/CPU command
and telemetry leg from the relevant table row before using its result.

Tool licence evidence must inventory the binaries actually distributed on each
platform, including Mach-O extensions and dylibs, rather than infer Mac notices
from a Windows DLL scan. Candidate DR 3 names the existing scan sites.

## 10. Packaging on macOS: information for WP6.5

This section is a proposed handoff, not a build result or an artifact-shape
decision. N14 requires one self-contained CPU-only Mac artifact; CP6a/WP6.1's
shape decision and WP6.5's actual Mac evidence govern the final build.

DOC [PYI-SPEC]: PyInstaller supports a BUNDLE target producing an .app and a
generated Info.plist, with bundle_identifier/version and info_plist overrides.
Recommendation: a native arm64 build should verify CFBundleName/identifier,
CFBundleShortVersionString/CFBundleVersion and NSPrincipalClass=NSApplication,
then validate Retina rendering. REASONED: add NSHighResolutionCapable to the
Info.plist checks supporting P38/X40 Retina evidence. Record the minimum
supported OS from the pinned
Python/Qt/native-wheel/FFmpeg combination, not from this audit's Windows host.

DOC [PYI-FEATURES]: target architecture must match the collected native modules;
PyInstaller re-signs changed collected binaries ad hoc by default, including
arm64. This is a technical build requirement, distinct from Developer ID signing
and notarisation, which remain out of scope under N14. No signing identity,
certificate purchase or notarisation workflow is proposed.

REASONED known D1 risk: PyInstaller 6 .app collection can place binaries under
Contents/Frameworks (sys._MEIPASS), while dirname(sys.executable) identifies
Contents/MacOS; onefile tools unpack under a temporary sys._MEIPASS. The ruled
D1 prepend alone may therefore miss FFmpeg/FFprobe. WP6.5 must validate one of
two options: explicitly place tools in Contents/MacOS and ad-hoc re-sign the
arm64 bundle after any post-build copy, or obtain CHARC's amendment of D1 to
also prepend sys._MEIPASS. Neither option is selected here; acceptance remains
an actual bundle lookup/export check with no external FFmpeg on PATH.
The same displacement applies to Windows onedir (`_internal`) and to every
onefile form; the Mac build mirrors whatever placement WP6.1's Windows build proves.
REASONED: PyInstaller 6's onefile .app deprecation is a CP6a shape-decision risk
to check against the pinned version; no Mac artifact shape is decided here.

WP6.5 build/validation checklist:

1. Build on a Mac with arm64 Python and compatible NumPy/SciPy/Pillow/pillow-heif/
   PySide6 native dependencies. Use the CPU profile; exclude CuPy/CUDA/NVIDIA
   downloads. Confirm each collected extension and FFmpeg binary has the arm64
   slice and usable library dependencies. A Windows artifact is not Mac evidence.
2. Produce the selected .app layout with Info.plist and application resources.
   Retain the permitted unsigned distribution workflow and notices for every
   bundled binary. Do not decide onedir versus onefile here.
3. Include FFmpeg and FFprobe with the required VideoToolbox and x265 capabilities,
   dependent non-system dylibs, executable permissions, recorded versions/hashes
   and notices. Validate WP6.1 D1's frozen executable-directory PATH prepend
   against actual collected/extracted tool placement (the two D1 options above)
   and invoke resolved absolute paths from find_tool, independent of Finder's
   external PATH; a D1 amendment requires CHARC, not an audit decision.
4. Use PyInstaller's PySide6 hooks, inspect the resulting Qt plugin search paths/
   qt.conf where applicable, and include the cocoa platform plugin
   (logical plugins/platforms/libqcocoa.dylib) and required image-format plugins.
   REASONED: exact placement must follow the produced bundle/hook layout, not a
   guessed Windows plugins directory. Prove no development-machine Qt is loaded.
   Offscreen availability for tests is a separate leg.
5. Validate WP6.1 FINAL Q5's ruled [sys.executable, "--export-worker"] re-entry
   and pre-Qt __main__ dispatch (P24), with AD-34 at WP6.1's accept. Prove the
   Contents/MacOS executable starts a Qt-free worker with no GUI or extra Dock
   icon, receives progress/result, cancels, and leaves no FFmpeg children.
6. Launch from Finder and Terminal on a clean arm64 machine without installed
   Python/FFmpeg/CUDA. Test first-run settings, journal cleanup, cache, one photo
   and 8/10-bit video export, unavailable VT/x265 diagnostics, and native dialogs.
   Restart and confirm persistent state uses the approved resolver policy
   (XDG today, Library only after AD-25(a) amendment), never inside .app or a
   onefile extraction directory.
7. Exercise a downloaded/quarantined copy and publish the actual unsigned-app
   opening steps for the tested macOS version. DOC [APPLE-OPEN]: Apple's supported
   override is System Settings > Privacy & Security > Open Anyway, followed by
   confirmation where offered. Do not tell users to disable system security.
   REASONED: quarantine behaviour and the exact prompt still need the real
   artifact test; no Mac opening procedure was executed here.
8. Preserve app-bundle symlinks/executable modes in the release archive and test
   extraction. Run V4 and the native GUI/worker/path tests on that extracted copy,
   then record Mac timing/RSS as information with the required exclusive window.

DOC (repository), AD-31 (decisions.md:46) notes a 7.8 GB worker-tree private peak
as "not of record" Windows GPU evidence; REASONED: GUI plus CPU worker pressure
on 8/16 GB Macs is a WP6.5 risk to measure, not a Mac memory estimate or acceptance result.

## 11. Metal: information only

REASONED: a future Metal correction backend would require an approved IF-2
implementation or adapter with float32 operations, pyramid/FFT or equivalent
kernels, host/device transport and synchronization, separate unified-memory
accounting, CPU parity tests against AD-11, numerical/preview/export fidelity,
and new performance evidence. CuPy/CUDA buffers and NVIDIA memory/session
constants cannot supply that implementation. VideoToolbox HEVC encoding alone
does not add a Metal correction backend. Metal design, dependencies, kernels
and interface changes are outside WP6.2/WP6.4's CPU-path envelope.

## 12. Q1-Q3 disposition

- Q1: retain both q:v quality control where supported and bitrate/ceiling control,
  without choosing values or a winner. DOC [FF] supports conditional qscale and
  warns that HEVC ceiling-setting failure need not fail initialization.
  WP6.5 measures both on its pinned artifact. No owner decision is made here.
- Q2: retain the automatic default-pipe strategy for macOS 1.2.0, per AD-23.
  DOC (repository) WP2.1S figures are Windows-only; no Mac measurement is inferred.
- Q3: REASONED from P28/T14/T20/T21: discovery/route/inventory already lower-case
  suffixes. Distinct paths survive inventory; ambiguous stem matches are refused.
  Native dialog visibility and real case-sensitive-volume coverage remain Mac
  tests. No blanket casefold of all filesystem paths is recommended.

## 13. Candidate DR list

These are candidates for the dispatcher/CHARC, not newly assigned DR numbers.
Severity is the potential consequence within the proposed Mac envelope.
None is a confirmed Windows product defect or a new implementation by this
package. No tool was run against real footage to reproduce a write risk.

| Candidate | Severity / evidence | Sites and mechanism | Disposition / confirmation trigger |
|---|---|---|---|
| 1. APFS queue/file identity | Minor, REASONED; DOC basis [PY-PATH] | gui/batch_panel.py:94/:107 uses normcase text for queue identity/labels; case-insensitive Darwin aliases may become separate items | BANKED candidate to CHARC for WP6.4: on case-insensitive APFS add one existing file twice with varied case, then add two distinct files on a case-sensitive volume; assert dedup versus preservation |
| 2. Older tool footage-containment aliases | Major, REASONED; DOC basis [PY-PATH] | inventory.py:1112/:1155, lookcheck/frames.py:161, container_spike/compare.py:1877, analysis_breakdown.py:984, export_oracle.py:645 use normalized lexical/realpath checks without existing-ancestor identity fallback; halo_probe.py:2360 has related cache-conflict exposure | BANKED candidate to CHARC for WP6.4: synthetic APFS footage root plus differently cased existing ancestor and output descendant; require refusal before mkdir/write and unchanged snapshots; safe sibling positive control |
| 3. Mac binary licence evidence omitted | Minor, REASONED | spike_io/licences.py `:149`/`:152` glob only `av.libs/*.dll`, and `:158` reads delvewheel's Windows DELVEWHEEL record (macOS wheels use delocate's `.dylibs`); `:188` `_CODE_SUFFIXES` lacks `.so` and `.dylib`, so Mac binaries are read as text by `wheel_text_files`; `:132` already accepts `.so` and `.dylib` | BANKED candidate to CHARC for WP6.5/N13: binary inventory against the actual Mac bundle plus per-binary notices; include extension modules, not only named dylibs |
| 4. Startup isolation when Library resolver lands | Minor, REASONED, conditional future defect | test_app_startup.py:178 and test_gui_startup.py:206 redirect Windows/XDG variables; a new native HOME/Library resolver must remain redirected too | COMMISSIONED test-plan item for WP6.4 P01/X15/X16; presently not a defect because the existing Darwin resolver uses XDG; prove disposable-home-only writes when adding the branch |

Candidate 4 preserves the accepted round-0 correction: the startup test does
already redirect XDG_CONFIG_HOME and XDG_CACHE_HOME. It must not be described
as Windows-only isolation or an existing user-home write defect.

The safe-write POSIX no-hardlink rename race is already the documented DR-16
single-owner limitation (safe_write.py:13-16), not a fifth candidate.
Missing VT, native paths and bundle adapters are commissioned Phase 6 work,
not findings to disguise as uncommissioned defects.

## 14. Limits, sources and verification record

No Mac, no Mac emulator, no footage reads, no native GUI run, no encoding,
no throughput/RSS measurement, no pytest, no build and no instrument run.
Only this Markdown report is authorized to change. All future test names and
encoding commands above are proposals. Platform simulation on Windows cannot prove native Mac
behaviour. The report's source line numbers refer to 5671a927.

Source labels used in DOC assessments and recommendations:

- [FF] [FFmpeg n8.0 VideoToolbox encoder source](https://raw.githubusercontent.com/FFmpeg/FFmpeg/n8.0/libavcodec/videotoolboxenc.c):
  vtenc_qscale_enabled, vtenc_create_encoder, hevc_pix_fmts. A release-tagged
  reference was used to ground round 0's upstream-master observation; the
  selected bundled version must be checked again in WP6.5.
- [PY-PATH] [Python 3.12 os.path documentation](https://docs.python.org/3.12/library/os.path.html):
  normcase and samefile semantics.
- [QT] [Qt macOS issues](https://doc.qt.io/qt-6/macos-issues.html):
  native menus, platform keys and deployment structures.
- [QK] [Qt ApplicationAttribute documentation](https://doc.qt.io/qt-6/qt.html#ApplicationAttribute-enum):
  AA_MacDontSwapCtrlAndMeta and default Command mapping.
- [APPLE-FS] [Apple File System Programming Guide](https://developer.apple.com/library/archive/documentation/FileManagement/Conceptual/FileSystemProgrammingGuide/FileSystemOverview/FileSystemOverview.html):
  user Library/application-support/cache roles; specific Clearwater paths are
  recommendations in section 5, not a previously implemented convention.
- [PYI-SPEC] [PyInstaller spec-file bundle options](https://pyinstaller.org/en/stable/spec-files.html#spec-file-options-for-a-macos-bundle):
  BUNDLE and Info.plist.
- [PYI-FEATURES] [PyInstaller macOS architecture/signing notes](https://pyinstaller.org/en/stable/feature-notes.html#macos-multi-arch-support):
  architecture validation and ad-hoc signing.
- [APPLE-OPEN] [Apple: safely open apps on your Mac](https://support.apple.com/en-ie/102445):
  Privacy & Security override procedure.
- Repository sources: docs/decisions.md AD-12/AD-23/AD-25(a)/AD-31; docs/architecture.md;
  spec v0.6.0 N1/N14 and D75/D111; docs/reports/wp2.1s-io-spike.md:234/:236/:240;
  docs/briefs/wp6.1-brief.md, CHARC FINAL Q5/Q6 and round-0 D1/D2.
  These establish intended policy and historical Windows measurements, not
  executed Mac results.

Verification loop at this report boundary:

| Suspect / claim | Independent check used | Disposition |
|---|---|---|
| Non-Windows pipe-sizing raise prevents decoding | Followed pipes.open_frame_pipe catch and decode subprocess.PIPE branch | Rejected; fallback exists |
| Startup subprocess isolation is Windows-only | Confirmed env.update also redirects XDG roots | Rejected as a current defect; conditional Library test item retained |
| VT is already selectable through generic encoder strings | Read registry, resolver, trial format map and _encoder_options branch | Confirmed missing leg; explicit follow-on specified |
| normcase establishes Mac case-insensitive identity | Python documentation versus queue/older-tool mechanics | Candidate risk retained, native reproduction not claimed |
| Literal Ctrl shortcuts necessarily require Meta substitution | Qt modifier/ApplicationAttribute documentation | Rejected; default Command mapping documented |
| VT exit zero proves its requested ceiling | Release-tagged FFmpeg rate-property error handling | Rejected; Mac test must inspect stderr and rates |
| Full report claims Mac tests or measurements | Checked labels and proposed-test language | No Mac execution claim authorized |

Reviewer A CONVERGED at round 3, VERDICT: NO_NEW_CRITICAL_MAJOR. Final A text
corrections were applied once, without a fourth A review. Reviewer B also returned
NO_NEW_CRITICAL_MAJOR and upheld R3-5's dispute; its corrections and B4's narrow
qualification are recorded below. The dispatcher verifies these lines and runs
the accept gate; this report does not claim acceptance. CHARC owns the new AD
rows, AD-25(a)/N1 path disposition, owner-reserved G12 wording referral,
dependency-group disposition, candidate-DR disposition and WP6.4 brief.
WP6.5 owns native packaging validation and the deferred quality/performance choice.

## 15. Reviewer A cumulative round ledger

The dispatch restricts edits to this report; the ledger is retained here for
transfer to the dispatcher, with no separate proof-file edit. Durable review:
C:/Users/rwsmy/clearwater-review-evidence/wp6.2/A/r1/review.txt (read once in full).
Round 2: C:/Users/rwsmy/clearwater-review-evidence/wp6.2/A/r2/review.txt
(read once in full). Round 3:
C:/Users/rwsmy/clearwater-review-evidence/wp6.2/A/r3/review.txt (read once in full).
Reviewer B: C:/Users/rwsmy/clearwater-review-evidence/wp6.2/B/review.txt
(read once in full). The dispatcher supplied turn-5 end depth as 187,664 of
475,000; no turn-6 end figure is available to this cell.

| Round | Severity counts | Envelope | New / reopened | Text-bearing / non-text-bearing | Reverts | Fix type | Depth | Disposition |
|---|---|---|---|---|---|---|---|---|
| A r1 | 0 critical, 1 major, 7 minor, 5 advisory | 13 in, 0 out | 13 / 0 | 12 / 1 (F13) | 0 | 13 documentation fixes; 0 product-code, 0 test-only | Fresh cell; no current figure supplied | All FIXED; yield for A r2, no convergence claim |
| A r2 | 0 critical, 1 conditional major, 3 minor, 7 advisory | 11 in, 0 out | 11 / 0; all 13 r1 fixes confirmed true, none reopened | 9 / 2 (A1/A3, review classification) | 0 | 11 documentation fixes; 0 product-code, 0 test-only | Turn-3 end: 112,720 / 475,000 input tokens, dispatcher supplied | All FIXED; yield for A r3, final text round |
| A r3 | 0 critical, 0 major, 3 minor, 8 advisory (itemized) | 11 in, 0 out; 10 applied, 1 disputed | 11 / 0; all 11 r2 fixes confirmed true, none reopened | 11 / 0 (itemized classifications) | 0 | 10 documentation corrections plus 1 evidence-backed dispute; 0 product-code, 0 test-only | Turn-4 end: 150,325 / 475,000, dispatcher supplied | CONVERGED, NO_NEW_CRITICAL_MAJOR; final cleanup once, no A r4; yield for B |
| B | 0 critical, 0 major, 2 minor, 6 advisory | 8 in, 0 out; 7 applied, 1 applied with partial dispute | 8 / 0; R3-5 dispute upheld | 8 / 0 | 0 | 8 documentation changes; B4 universal wording disputed with source evidence; 0 product-code, 0 test-only | Turn-5 end: 187,664 / 475,000, dispatcher supplied | NO_NEW_CRITICAL_MAJOR; corrections applied, yield for accept gate |

| Finding | Severity / classification | Adjudication and evidence in this report |
|---|---|---|
| F1 | MAJOR, text-bearing | FIXED: P24/P56-P58, sections 6/10 and M-BUNDLE cite WP6.1 FINAL Q5/Q6 and round-0 D1/D2; worker mechanism ruled, Mac work validation only |
| F2 | minor, text-bearing | FIXED: section 5 and P01/P26 cite AD-25(a); XDG compliant, Library PROPOSED pending CHARC amendment/N1 approval |
| F3 | minor, text-bearing | FIXED: P59-P62 cite the four confirmed encode.py sites; rate/state/validation test mappings added |
| F4 | minor, text-bearing | FIXED: P63 and section 7 cover AUTO_TEXT and owner-reserved spec G12 wording referral |
| F5 | minor, text-bearing | FIXED: P03/P07/P09/P10 point to confirmed catch, registry, trial table and reason mechanics |
| F6 | minor, text-bearing | FIXED: section 2 records exact W/R rerun, rg version, independent Python command, CR comparison and per-file roster; reviewer's remaining counting discrepancy explicitly unestablished |
| F7 | minor, text-bearing | FIXED: P64, section 4 and W-SPACE/M-SPACE cover unproved VT bound and APFS free/purgeable-space validation |
| F8 | minor, text-bearing | FIXED: P15, section 4 and W-V4/M-V4 retain all named arguments and add VT reorder/negative-CTS/edit-list case |
| F9 | advisory, text-bearing | FIXED: section 6 cites WP2.1S TCP row s and proposes INFO off Windows for pipes.py:95, not a decision |
| F10 | advisory, text-bearing | FIXED: T14, section 9 and W-FS/M-FS cover AppleDouble ._* suffix admission and exclusion/unreadable outcome |
| F11 | advisory, text-bearing | FIXED: section 8 declares VT-unavailable CI expectation, x265 leg and explicit VT skip; hardware Mac evidence still required |
| F12 | advisory, text-bearing | FIXED: section 10 labels AD-31's 7.8 GB Windows GPU figure not of record and flags 8/16 GB Mac memory risk |
| F13 | advisory, non-text-bearing (review classification) | FIXED: screening paragraph distinguishes test_config_settings.py:367 R/where from :461 W/nul |

Round-2 adjudications (all NEW and in envelope):

| Finding | Severity / classification | Adjudication and evidence in this report |
|---|---|---|
| N1 | MAJOR conditional on darwin static gate, text-bearing | FIXED: P02/P58/P65/T03/T05/T09/T49-T51, W-STATIC/M-STATIC and section 8 cite reviewer's executed errors; CHARC must commission guard changes/static policy, minor if Windows-only static gate |
| N2 | minor, text-bearing, REASONED | FIXED: P57 and section 10 name Frameworks/sys._MEIPASS/onefile lookup risk, post-copy arm64 re-sign and two D1 options without selecting one |
| N3 | minor, text-bearing | FIXED: section 2 labels CRLF checkout counts and independently confirms LF-blob W totals 103/31, 164/30, 285/62 |
| N4 | minor, text-bearing, REASONED | FIXED: P40/P49 and section 5 cite DR-34(a); M-FS adds dotless-i/sharp-s/NFD/NFC case-insensitive APFS no-overwrite corpus |
| N5 | advisory, text-bearing, REASONED | FIXED: section 6 states AD-31's fresh video worker makes fallback WARNING recur per export job |
| N6 | advisory, text-bearing | FIXED: Retain rows P66-P69 cover provenance cap, two unlink retries and portable/Windows disk-full classification, with W/M references |
| N7 | advisory, text-bearing, REASONED | FIXED: P31, section 7 and M-GUI cover Settings/Quit merge, empty Tools layout and G-check wording |
| N8 | advisory, text-bearing, REASONED | FIXED: section 10 adds NSHighResolutionCapable and onefile .app deprecation risk for CP6a |
| A1 | advisory, non-text-bearing (review classification) | FIXED: P57 is Class 2; current totals include the new round-2 rows, 41 Class 1 / 124 Class 2 |
| A2 | advisory, text-bearing | FIXED: P11 cites capability.py:248-260 and includes saved unknown-name refusal |
| A3 | advisory, non-text-bearing (review classification) | FIXED: P18 cites memory_estimate_bytes at core/memory.py:45; review's suggested :44 is blank in this checkout, confirmed by source read |

Round-3 adjudications (all NEW and in envelope; final text corrections once):

The review header says 3 minor / 7 advisory / 9 text-bearing. Its itemized
R3-1 through R3-11 classifications contain 3 minor and 8 advisory, all explicitly
text-bearing (including R3-10 citations); the ledger records those actual items.

| Finding | Severity / classification | Adjudication and evidence in this report |
|---|---|---|
| R3-1 | minor, text-bearing | APPLIED: five remedy sites now quote the explicit if/else branches, Reviewer A's executed early-return failure/both-target success, and W-STATIC runs win32 and darwin |
| R3-2 | minor, text-bearing | APPLIED: T52/X46 reproduce the requested drive-name policy and test correction; os.sep supplement recorded in section 2 |
| R3-3 | minor, text-bearing, REASONED | APPLIED: P70 and M-FS cover legal source-name refusal, CHARC's explicit refusal/mapping choice and Finder-typed slash corpus |
| R3-4 | advisory, text-bearing, REASONED | APPLIED: P71 and M-GUI add 120-unit wheel accumulation/direction and trackpad/momentum/natural-scrolling validation |
| R3-5 | advisory, text-bearing | DISPUTED: decode.py:759 short-circuits cuda_decode_available when hw_decode=False; jobs/export.py:905 and app/analysis_adapter.py:377 set false for CPU, gui/analysis_service.py:323 and gui/sources.py:141 explicitly pass false. REASONED CPU Mac GUI/worker paths do not run or warn from that trial; P05/W-DEVICE pin this existing behaviour instead of proposing a new N1 branch |
| R3-6 | advisory, text-bearing, REASONED | APPLIED: P72 covers displaymatrix and partial-file text with pinned Mac-build truncated/rotated samples and existing corrupt/nb_frames backup |
| R3-7 | advisory, text-bearing, REASONED | APPLIED: section 10 extends D1 displacement to Windows _internal and all onefile forms, tied to WP6.1's proved placement |
| R3-8 | advisory, text-bearing | APPLIED: candidate DR 3 mechanism replaced as requested; T11/T12 distinguish PyAV DLL/DELVEWHEEL and suffix omissions from pillow-heif's existing .so/.dylib scan |
| R3-9 | advisory, text-bearing, REASONED | APPLIED: M-DEVICE requires Mac CPU comparisons with Windows-generated references within AD-11 tolerances, never byte identity |
| R3-10 | advisory, text-bearing | APPLIED after opening every range: P59 encode.py:406-408, P67 cache/store.py:126-150, P68 encode.py:506-515 |
| R3-11 | advisory, text-bearing, REASONED | APPLIED: M-BUNDLE requires Dock Quit, Cmd-Q and logout during export to run shutdown, save settings and leave no worker/FFmpeg |

Reviewer B adjudications (all NEW, in envelope and text-bearing):

| Finding | Severity / classification | Adjudication and evidence in this report |
|---|---|---|
| B1 | minor, text-bearing | APPLIED: P73 reproduces the preset rename/no-replace risk, DR-34(a) extension/new candidate choice and M-FS unchanged-other-preset-bytes control |
| B2 | minor, text-bearing, REASONED | APPLIED: P74 reproduces the console/process-group difference and CHARC's AD-23 options; section 6 and M-SPAWN require process-group SIGINT via os.killpg, not raise_signal, plus parent-death child-exit validation |
| B3 | advisory, text-bearing | APPLIED: P16 commissions platform-neutral probe.py:118-119 missing-tool G10 text |
| B4 | advisory, text-bearing | APPLIED policy/test correction; DISPUTED universal "every Mac" wording: backend.py:1028-1029 returns "CPU: forced" before _probe_gpu when force_cpu is set. P22 records backend.py:943's automatic-selection reason, shell.py:549/554 display, CHARC/WP6.1 D7 disposition and W-GUI/M-GUI assertions for both cases |
| B5 | advisory, text-bearing, REASONED | APPLIED: P71 explicitly includes Windows precision touchpads, synthetic sub-120 accumulation and conditional DR referral if confirmed on the laptop; no Windows execution/defect confirmation claimed |
| B6 | advisory, text-bearing | APPLIED: section 6 records no fork assumptions, explicit spawn at test_fixture_cache_lock.py:88 and ProcessPoolExecutor at cache_store_test.py:842, with Python 3.12 Windows/Mac spawn default labelled REASONED |
| B7 | advisory, text-bearing | APPLIED: section 8 now cites both unmarked CUDA declarations, pyproject.toml:46 development group and :30 gpu extra |
| B8 | advisory, text-bearing | APPLIED after source read: section 4 names color/swscale.py:181-203's yuv420p10le filter end, REASONED automatic p010le conversion for NVENC/VT, unchanged AD-10 flags and decoded-format/profile verification |

Boundary verification: source anchors for new/corrected citations were inspected;
round-1 W/R checkout counts and round-2 LF-blob W counts independently reproduced;
semantic rows are 74 product (including 3 arriving WP6.1 sites), 52 tools,
46 tests, 172 total (Class 1 / Class 2 = 42 / 130). No Mac execution or
Windows product defect is claimed. The final yield reports the on-disk diff,
ASCII/LF checks and report-only status. No application, instrument, build,
pytest or harness suite was run by this remediation cell.
