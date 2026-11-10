# WP6.5 macOS validation -- cell ledger (`wp65-cell1`, implementer-opus-high)

Brief `docs/briefs/wp6.5-brief.md` (FINAL, the orchestrator's fill at `49ca01bf`); dispatch
`clearwater-review-evidence\wp6.5\cell\dispatch-1.md`. The cell keeps this file; the
dispatcher fills the depth figures.

## Cumulative round ledger

| Round | Reviewer | Blocking (crit/major) | Minor/nit | In-envelope / out | NEW / REOPENED | Reverts | Fixes: product / tests-only | Depth (dispatcher) |
|---|---|---|---|---|---|---|---|---|
| 0 | none (read-only work list) | - | - | - | - | 0 | none (no edit) | 254,025 (wp65-cell1, read by the dispatcher with cell_depth.py at its round-0 yield) |
| A r1 | Codex (seat, detached copy) on the group-1 head | 1 major (A1) | 1 minor (A2), 1 advisory (A3) | 3 in / 0 out | 3 NEW / 0 REOPENED | 0 | product 3 (build.py) + tests; all three FIXED at `2704a852` (group 2b) | group-2b row below |
| A r3 | Codex (seat, detached copy) on the group-2a part-2 head `de3d68a0` | 3 major (A3-F1, F2, F3) | 2 minor (A3-F4, F5) | 5 in / 0 out | 5 NEW / 0 REOPENED | 0 | product 5 (build.py) + tests; all five FIXED at `d81549fc` (turn 4b-r1, `wp65-cell7`); 1 more found by the cell's loop and fixed (configuration candidates) | part-2 r1 section below |
| A r4 | Codex (seat, detached copy) on the part-2 r1 head `ae96a4e2` | 3 major (A4-F1, F2, F3) | 0 | 3 in / 0 out | 3 NEW / 0 REOPENED | 0 | product 3 (build.py) + tests; all three FIXED at `d6296b92` (turn 4b-r2, `wp65-cell8`); 2 more found by the cell's loop and fixed (printed configure form, extra-version spellings) | part-2 r2 section below |
| A r5 | Codex (seat, detached copy) on the part-2 r2 head `87df4840` | 0 | 1 minor (redundant quoting admitted by the printed-form parser) | 1 in / 0 out | 1 NEW / 0 REOPENED | 0 | product 1 (build.py `_sh_quote` canonical check) + tests; FIXED at `fcfe5073` (turn G3-fix, `wp65-cell10`); the same turn folded the G3 runner classification (test-only, plus `notices.py` C15 and `stills.py` C1) | G3-fix section below |
| A r6 | Codex (seat, detached copy) on the part-3c head `00e18e71` | 0 | 2 minor (status type, switch-OFF guard `else` arm), 1 advisory (x264 provenance; closed by the dispatcher) | 3 in / 0 out | 3 NEW / 0 REOPENED | 0 | product 1 (build.py) + test-only 1 (the guard), both FIXED at `cbe0a8b6` / `be5fe211` (turn QA-fix, `wp65-cell14`), with the seat-QA conftest regression (test-only, `b1f0d507`) | QA-fix section below |

## Round 0

Read-only turn at base `49ca01bf` (worktree `.worktrees/wp6.5`). No product, test, workflow
or tools edit; no `uv lock`. Runs made: `pytest --collect-only` of
`tests/test_tools_package_notices.py` (415) and of `-m macos` (224); `mypy --platform darwin`
(Success, 166 source files); AST scans of the notices test module (scratch scripts, not
committed). Web / `gh api` reads were TEXT only (README files, docs pages, release pages,
`.sha256` sidecars, `versions.txt` / `codecs.txt`); no binary was downloaded or run. No product
entry point was called.

### 0.0 Findings for CHARC before the build (each with its evidence)

- **F0-1 (needs a ruling) -- M-BUNDLE presumes an `.app`; Q3's working assumption is onedir.**
  `tests/test_macos_portability.py:1566-1572` (`_bundle`) reads `CLEARWATER_MAC_BUNDLE` and
  asserts `<bundle>/Contents/MacOS`; `:1586` looks for `ffmpeg` / `ffprobe` anywhere under
  that bundle; `:1601-1606` expects the frozen worker command in `Contents/MacOS`. The onedir
  zip ships `Clearwater/Clearwater` + `_internal/` with FFmpeg beside the executable (AD-34 (2)).
  Either the M-BUNDLE helper learns the onedir folder (an edit beyond "marker and skip-reason
  edits", so a grant), or the macOS artifact is the `.app` (Q3). See Q3 below: PyInstaller
  6.22.3 builds the `.app` anyway on macOS because `build.py` passes `--windowed`.
- **F0-2 (sizing) -- the Mac notices are a census, not a suffix set.** `tools/package/notices.py`
  is Windows-shaped: `Clearwater.exe` (`:1870`, `:1875`), `ffmpeg.exe` / `ffprobe.exe`
  (`:1510`), CPython's `DLLs/*.pyd` and `python3x.dll` (`:1482-1494`); the embedded-components
  rule (AD-38 (13)) is keyed on Windows host paths and hashes in
  `tools/package/native-licences/manifest.json` (140 rows / 1,536 entries). N13 for the Mac
  artifact needs a macOS host census (CPython's `.so` / `libpython3.12.dylib`, Qt frameworks,
  numpy / SciPy / Pillow delocate `.dylibs`) and a macOS FFmpeg lock with its own component
  texts and toolchain census. DR-123's brief text (suffix set + delocate record) is the
  smallest part. My reading: in scope (the Goal row: the Mac artifact's notices); it is the
  largest item and may warrant its own group or rung.
- **F0-3 (correction to CHARC note 4) -- the runner is NEWER than the Mac.** `macos-latest` and
  `macos-26` are macOS 26.6.2 arm64 (`images/macos/macos-26-arm64-Readme.md:8`); the Mac is
  26.3.1. `macos-15` (15.8.2) also exists.
- **F0-4 (correction to CHARC note 4) -- no right-click Open on macOS 15+.** Apple: "In macOS
  Sequoia, users will no longer be able to Control-click to override Gatekeeper ... They'll need
  to visit System Settings > Privacy & Security" (Q3 claims). The run sheet and the guide carry
  the "Open Anyway" path, not right-click Open.
- **F0-5 (correction to the brief's "~22") -- the notices skip hides 35 functions / 158 node
  ids** that request neither `release` nor a Windows-only input (item 6 below), plus one
  native-reading function (3 ids) that reads `.venv/Lib/site-packages` (Windows venv layout).
- **F0-6 (workflow) -- `workflow_dispatch` needs the file on the default branch.** GitHub:
  "This event will only trigger a workflow run if the workflow file exists on the default
  branch." A new validation workflow on branch `wp6.5` alone cannot be dispatched (item 1).
- **F0-7 (workflow) -- the `setup-uv` checksum is per platform.** `release.yml:46` pins the
  Windows asset's sha256; the macOS job needs the `uv-aarch64-apple-darwin` asset's sha256 for
  0.10.9, seat-fetched like the Windows one.
- **F0-8 (runner budget) -- the standard arm64 runner is 3 vCPU (M1), 7 GB RAM, 14 GB SSD**
  (docs.github.com hosted-runners table: "macOS 3 (M1) 7 GB 14 GB arm64 macos-latest , macos-15
  , macos-26"). The Windows leg runs `-n 4`; WP6.4 saw one MemoryError under `-n 4` on the
  laptop. I propose `-n 3` on the macOS job only (stated as the one difference), CHARC rules.
- **F0-9 (origin check) -- macOS builds contain symlinks.** PyInstaller's
  `collect_files_from_framework_bundles` (`PyInstaller/utils/osx.py:609-618`) creates
  `Versions/Current`, `<name>` and `Resources` links in every collected `.framework`;
  `build.py:2636-2637` refuses ANY linked file, and so does the ZIP walk `_release_files` (`:2769`, `:2777-2782`). The macOS origin rule must accept in-folder
  relative framework links (and refuse links that escape), and `--zip` must store them as links.
- **F0-10 (README) -- `README.md` is core-scanned.** It is not instance surface
  (`tests/harness/genericity_lists.py:211-276`); `FORBIDDEN_TERMS` (`:53-72`) includes the test
  runner's and the linter's names. The "macOS prerequisites" section names Xcode Command Line
  Tools and `uv` only, and must not name those two tools.
- **F0-11 (serial leg on the runner) -- QUIT_SCRIPT.** The recorded exception runs
  `tests/test_app_startup.py` QUIT_SCRIPT "at the SEAT in a gate leg only". The runner's serial
  leg would include it (a disposable machine, not the owner's profile). CHARC rules whether the
  macOS serial leg keeps it or carries the cell `-k` exclusion.

### 1. Q5 -- how stage 1 runs on GitHub

Confirmed: `release.yml:66-68` -- `if not re.fullmatch(r"refs/tags/v[0-9]+\.[0-9]+\.[0-9]+",
ref): raise SystemExit("Release requires an existing vMAJOR.MINOR.PATCH tag")`. A dispatch on
a branch fails there; a `v*` tag push starts the `release` job (`release.yml:155-157`).

| | (a) separate validation workflow | (b) validation path inside `release.yml` | (c) reusable `macos` workflow (RECOMMENDED) |
|---|---|---|---|
| Files | NEW `.github/workflows/macos-validation.yml` (the macOS steps); `release.yml` gets a SECOND copy of the steps in its `macos` job; `tests/test_release_workflow.py`; harness registration | `release.yml` only (`macos` job + a `validate_only` input that skips the tag gate for that job); `tests/test_release_workflow.py` | NEW `.github/workflows/macos-build.yml` (`on: workflow_call` input `release-version`, `workflow_dispatch`, `push: branches: ["macos-validation/**"]`; the ONE `macos` job); `release.yml` calls it (`macos: needs: windows, uses: ./.github/workflows/macos-build.yml, with: release-version: ${{ needs.windows.outputs.version }}`) and the `release` job changes (item 2); `tests/test_release_workflow.py`; harness registration |
| Owner types (stage 1) | after the file reaches main (F0-6): `gh workflow run macos-validation.yml --ref wp6.5`; before that, a `push` trigger is needed instead | `gh workflow run release.yml --ref wp6.5 -f version=... -f validate_only=true` | `git push origin wp6.5:refs/heads/macos-validation/wp6.5` (the `push` trigger needs no default-branch presence); re-runs: re-push or the run page's "Re-run jobs"; after the merge, also `gh workflow run macos-build.yml --ref <branch>` |
| Run produces | workflow artifacts only | workflow artifacts; the `windows` job FAILS red at its version gate on every validation dispatch | workflow artifacts only (`macos-release` zip + sidecar + notices, logs, junit, the captured listing) |
| `windows` job byte-identical | yes | yes, but red in every validation run (minutes spent, noisy) | yes |
| 1.2.0 tag path | the `macos` job in `release.yml` (the copy) | the same job, gate active | `release.yml` -> `windows` (the tag gate) -> `macos` (called; checks `clearwater.__version__` = `release-version`) -> `release` |
| Risk | two copies of the macOS steps drift; the validated copy is not the shipped one | changes the tag gate's semantics; a dispatch input can relax a release gate | one definition validated AND shipped; the macOS job runs after `windows` on a tag (serial wall), and inherits the caller's `contents: read` |

Recommendation: (c). It needs CHARC's grant for the new workflow file and for
`tests/test_release_workflow.py` (its pins: `:59-69` six `uses:` lines and SHA pins, `:441-458`
`needs: windows`, `:603` `windows-release`), plus the harness registration (item 11). Limit in
every option: the `release` job's macOS download / attach steps are first exercised at the
1.2.0 tag (they are pinned by tests and actionlint until then).

### 2. Clarification 2 -- the `release` job

Changes in the `release` job only: `needs: [windows, macos]`; a second
`actions/download-artifact` step (`name: macos-release`, `path: work/release-assets`); `files:`
gains `work/release-assets/THIRD_PARTY_NOTICES-macos.md`. The `*.zip` / `*.zip.sha256` globs
(`release.yml:221-222`) already match both zips. NAME COLLISION: the `windows` job stages
`THIRD_PARTY_NOTICES.md` (`release.yml:135`) and must stay byte-identical, so the macOS job
stages its notices under `THIRD_PARTY_NOTICES-macos.md`. `body_path` keeps
`needs.windows.outputs.version`. A failing `macos` job then blocks the draft (both artifacts
or none), which is what N14's one-artifact-per-platform needs; CHARC rules.

### 3. Q1 -- the runner (claim | source URL | quoted line)

- `macos-latest` = macOS 26 arm64 | https://github.com/actions/runner-images/blob/main/README.md | "macOS 26 Arm64 ... arm64 | `macos-latest`, `macos-26` or `macos-26-xlarge`"
- `macos-15` = macOS 15 arm64 | same | "macOS 15 Arm64 ... arm64 | `macos-15`, or `macos-15-xlarge`"
- macOS 26 image version | https://github.com/actions/runner-images/blob/main/images/macos/macos-26-arm64-Readme.md (commit `6d2bc0ac`, 2026-10-30) | "- OS Version: macOS 26.6.2 (25G83)"; "- Image Version: 20261026.0455.2"
- macOS 15 image version | .../images/macos/macos-15-arm64-Readme.md | "- OS Version: macOS 15.8.2 (24H232)"
- No FFmpeg on the image | macos-26-arm64-Readme.md "### Utilities" list (`:48-70`) | no ffmpeg row (7-Zip ... Ninja 1.13.2); Homebrew 7.0.11 present (`:35`)
- Standard arm64 runner hardware | https://docs.github.com/en/actions/reference/runners/github-hosted-runners | "macOS 3 (M1) 7 GB 14 GB arm64 macos-latest , macos-15 , macos-26 , xcode-27"
- Larger runner names GPU acceleration, the standard one does not | https://docs.github.com/en/actions/reference/runners/larger-runners | "XLarge arm64 (M2) 5 (+ 8 GPU hardware acceleration) 14 GB 14 GB macos-latest-xlarge"
- The documented arm64 limit | github-hosted-runners page, "Limitations for arm64 macOS runners" | "Nested-virtualization is not supported due to the limitation of Apple's Virtualization Framework."
- `hevc_videotoolbox` encode on the runner | none found | NO GitHub or runner-images document states whether VideoToolbox hardware encode works in the arm64 runner VM. UNVERIFIED either way; the first runner run decides it through the product's own trial (`-allow_sw 0`, AD-35), and the smoke records which encoder ran. The Q1 measurement is stage 2 regardless.

Recommended label: `macos-26` (pinned major, = `macos-latest` today; avoids the `-latest`
migration the README describes at `:94-96`).

### 4. Q2 -- macOS arm64 FFmpeg provider candidates (claim list; no pick, no download)

- **BtbN/FFmpeg-Builds (the 1.1.x provider) does NOT build macOS** | https://github.com/BtbN/FFmpeg-Builds README | "Auto-Builds run ONLY for win(arm)64 and linux(arm)64"; targets list `win64`, `winarm64`, `linux64`, `linuxarm64`; `variants/` has no mac/darwin file. The owner's fork cannot produce a Mac asset without a new recipe.
- **martin-riedl.de (release 9.0.2, arm64)** | https://ffmpeg.martin-riedl.de/ | "Download Release Build ... Release: 9.0.2"; asset `https://ffmpeg.martin-riedl.de/download/macos/arm64/1789931890_9.0.2/ffmpeg.zip` (+ `ffprobe.zip`). sha256 published as same-host sidecars: `ffmpeg.zip` `c8ed4c4e6978a03c485edbfe4e0a5dc2380f8a30bba5150531b31b094492d924`, `ffprobe.zip` `fcbe839537485eaee7a7a8bc5cbc0f90d53617e80943e8a5b2e31cb851197ea6`. Licence build: `versions.txt` configure "--enable-version3 --enable-gpl ... --enable-libzvbi ... --enable-libx265" (GPL-3.0; **zvbi 0.2.35 linked**, the same GPL-2.0-only problem WP6.3c removed). Corresponding source: component VERSIONS in `versions.txt` (e.g. "x265 4.2", "zvbi 0.2.35"), no commit pins on the page; the build script is Apache-2.0 at `git.martin-riedl.de/ffmpeg/build-script` ("This script is made to compile FFmpeg with common codecs on Linux and macOS") and has a `-SKIP_ZVBI=YES` switch. Immutability: a timestamped path on a personal host, not a GitHub release digest. `codecs.txt` lists "encoders: libx265 hevc_videotoolbox".
- **osxexperts.net (9.0.2 Apple Silicon)** | https://www.osxexperts.net/ | "Download ffmpeg 9.0.2 (Apple Silicon) SHA256 checksum of FFmpeg file : 762f16b2913b8d3b8fdb8092df12b691053b035b13ae9b88205513c55cb8e71e"; asset `https://www.osxexperts.net/ffmpeg902arm.zip` (a mutable name). "Source used to compile : here" links `https://github.com/FFmpeg/FFmpeg/tree/release/6.1` (does not match 9.0.2); no configure line, no component pins; "provided ... for educational purposes only". Fails the provider rule on source and terms.
- **evermeet.cx** | https://evermeet.cx/ffmpeg/ (the one macOS link on https://ffmpeg.org/download.html) | "static FFmpeg binaries for macOS 64-bit Intel"; "I do not plan to provide native ffmpeg binaries for Apple Silicon ARM." Intel only; also `--enable-libzvbi`. Excluded (not arm64).
- **jellyfin-ffmpeg portable macarm64** | `gh api repos/jellyfin/jellyfin-ffmpeg/releases` | latest `v8.1.3-2` (2026-11-03): `jellyfin-ffmpeg_8.1.3-2_portable_macarm64-gpl.tar.xz` digest `sha256:d898cc819e7c4e9219d6410ddbdaada0838f14bec6ff89e283639915394cb43f`. GitHub release digest (immutable), GPL; but 8.1.x (not 9.x) and a patched fork of FFmpeg. Fails "9.x".
- **Self-build in the owner's fork (no provider exists yet)** | the WP6.3c pattern | a macOS recipe on a GitHub `macos-26` arm64 runner: e.g. the Apache-2.0 Riedl build script with `-SKIP_ZVBI=YES`, FFmpeg pinned to the same `release/9.0` commit as Windows (`b204e94e`), per-component pins + texts + toolchain census as AD-38 (9)-(16); asset = the fork's GitHub release (digest). Not a recommendation: the seat verifies, CHARC rules. It is the only candidate that meets every rule without a zvbi exception.
- Homebrew / conda-forge FFmpeg: dynamically linked against their own trees; the brief bars relying on Homebrew. Not listed further.

### 5. Q3 -- macOS evidence on onedir zip vs `.app` (claim | source | quoted line)

- `--windowed` builds a `.app` on macOS | PyInstaller 6.22.3 `PyInstaller/building/makespec.py:472-474` (https://github.com/pyinstaller/pyinstaller/blob/v6.22.3/PyInstaller/building/makespec.py) | "On macOS this also triggers building a macOS .app bundle." and `:869-871` "# For macOS create .app bundle. / if is_darwin and not console: specfile.write(bundletmplt % d)". `build.py` passes `--windowed` on every platform, so a macOS onedir build emits BOTH `dist/Clearwater/` and `dist/Clearwater.app`.
- PyInstaller re-signs every collected binary | https://pyinstaller.org/en/stable/feature-notes.html | "the process of collecting binaries (e.g., library path rewriting in binaries' headers) invalidates their signatures ... By default, PyInstaller ad-hoc (re)signs all collected binaries and the generated executable itself." ; "PyInstaller also automatically attempts to sign .app bundles"
- No Control-click override since macOS 15 | https://developer.apple.com/news/?id=saqachfa (2024-08-06) | "In macOS Sequoia, users will no longer be able to Control-click to override Gatekeeper when opening software that isn't signed correctly or notarized. They'll need to visit System Settings > Privacy & Security to review security information for software before allowing it to run."
- The Open Anyway path | https://support.apple.com/en-us/102445 | "Open System Settings. Click Privacy & Security, scroll down, and click the Open Anyway button to confirm your intent to open or install the app."
- Quarantine on downloaded unsigned binaries (provider guidance, not Apple) | evermeet.cx and osxexperts.net pages | "xattr -dr com.apple.quarantine <path_to_binary>"; osxexperts: "Apple Silicon devices can only run signed files. If needed you can ad-hoc sign".
- UNVERIFIED expectations for the Mac (run-sheet steps, not claims): a bare onedir executable double-clicked in Finder opens in Terminal; FFmpeg copied INTO a signed `.app` after PyInstaller's bundle signing breaks the bundle seal (a quarantined broken seal reads "damaged", worse than "unidentified developer"), so an `.app` artifact needs FFmpeg placed before signing or an ad-hoc re-sign after; a onedir folder has no bundle seal. Each is a stage-2 observation.

### 6. The two CHARC notes at this base

**Note 1 -- the notices skip.** `tests/test_tools_package_notices.py:21-24`:
`pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Windows native/interpreter
fixtures; WP6.5 supplies native fixtures")`. The `release` fixture (`:191-267`) copies
`Path(sys.base_prefix) / "python312.dll"` (`:198`) and builds `Clearwater.exe` (`:165-188`):
Windows-bound. 108 functions request `release`. Functions that do NOT (35 functions, 158 ids;
AST scan of fixture closure + helper calls, scratch `neutral.py` / `calls.py`):

`test_native_licence_text_is_exempt_from_checkout_normalization` (1),
`test_native_licence_manifest_hash_matches_committed_blob` (1),
`test_stage_only_notices_explain_representative_and_shared_text_labels` (1),
`test_component_row_renderer_refuses_missing_texts_without_validator` (4),
`test_root_annex_generator_checks_committed_bytes_and_detects_a_changed_row` (1),
`test_each_upstream_reuse_preserves_bytes_hash_and_true_label` (9),
`test_each_upstream_reuse_refuses_tampered_material` (27),
`test_commercial_qt_text_is_never_rendered_even_in_a_direct_plan` (1),
`test_real_native_manifest_verifies_the_seat_bytes` (1),
`test_production_embedded_hosts_have_complete_verified_source_text_rows` (1; `python312.dll`
is a manifest KEY, not a read),
`test_release_archive_keeps_sourceware_repository_and_member_path` (1),
`test_release_archive_refuses_unsafe_member_source_path` (5),
`test_native_surface_refuses_integrity_and_coverage_errors` (6),
`test_native_manifest_rejects_unverifiable_schema_fields` (14),
`test_native_manifest_rejects_invalid_document_shapes` (5),
`test_version_evidence_is_required_and_structured` (5),
`test_co_licence_links_require_symmetric_complete_claims` (4),
`test_excerpt_requires_source_file_and_valid_line_range` (4),
`test_native_binding_schema_fails_closed` (10),
`test_provenance_kinds_accept_exactly_their_own_form` (3),
`test_provenance_kinds_refuse_mixed_forms` (6),
`test_provenance_kind_identity_errors_fail_closed` (4),
`test_proprietary_files_require_each_measured_file_version` (3),
`test_nonproprietary_rows_refuse_excerpt_fields` (4),
`test_co_licence_link_requires_nonempty_file_bindings` (2),
`test_in_tree_component_labels_and_llvm_source_subtree` (1),
`test_git_tree_source_path_refuses_unsafe_values` (9),
`test_co_licence_asymmetry_is_refused_before_duplicate_claim_check` (1),
`test_shared_reference_preserves_original_heading` (3),
`test_production_limits_bind_every_commissioned_host_to_its_census` (1),
`test_production_wheel_census_binds_every_scipy_native_runtime` (1),
`test_production_wheel_texts_bind_exact_censused_hosts` (4),
`test_carried_audit_text_refusal_names_embedded_host_and_component` (2),
`test_production_tnc_retains_original_tnbc_attribution` (1),
`test_originals_and_patents_bind_verified_texts_to_carried_hosts` (12).
Native-reading, keep skipped off Windows: `test_real_wheel_licence_files_are_copied_byte_for_byte`
(3; `ROOT / ".venv/Lib/site-packages"` at `:1049`; the Mac wheels' licence files also differ).
Design: drop the module-level `pytestmark`; put `skipif(sys.platform != "win32", reason=...)`
on the `release` fixture (a skip raised inside the fixture) and on the one native-reading test.
Proof on Windows: collection and outcome identical (415 collected, same pass set); a darwin
proof is the runner's (the 158 ids pass there, the 108 + 3 skip with the reason).

**Note 2 -- `build.py`.** The darwin PATH branch: `run_pyinstaller` (`build.py:2349`), the
`else:` at `:2382-2386` ("POSIX dependency resolution uses loader paths/rpaths ... pass").
The whole-file-hash origin check: `_is_native` (`:2396`), `_record_native_hash` (`:2469`),
`_native_origin_hashes` (`:2487`, a set of whole-file sha256), `_locked_bootloader` (`:2500`,
darwin `runw` at `:2504-2505`), `_is_clearwater_bootloader` (`:2519`; darwin branch `:2576-2579`
= byte-prefix compare), `native_origin_violations` (`:2582`; the symlink refusal `:2636-2637`).

Design, darwin PATH (AD-36 form `if win32: ... elif darwin: ... else: raise
BuildEnvironmentError`, Linux fail-closed): PATH = interpreter `bin`
(`Path(sys.base_prefix) / "bin"`), venv `bin` (`Path(sys.prefix) / "bin"`), `/usr/bin`, `/bin`,
`/usr/sbin`, `/sbin` (PyInstaller runs `/usr/bin/codesign` by path and `lipo` /
`install_name_tool` by name, both in `/usr/bin`); PATH alone is not enough on macOS: PyInstaller
resolves libraries with macholib's `dyld_find` (`PyInstaller/depend/bindepend.py:645`),
which reads `DYLD_LIBRARY_PATH` / `DYLD_FRAMEWORK_PATH` and a fallback that includes
`/usr/local/lib`, so the branch also removes every `DYLD_*` variable and sets
`DYLD_FALLBACK_LIBRARY_PATH=/usr/lib` and `DYLD_FALLBACK_FRAMEWORK_PATH=/System/Library/Frameworks`
for the analysis, restored in the same `finally`. Homebrew (`/opt/homebrew`, `/usr/local`) is
never on it. Test on Windows: the existing `test_analysis_uses_only_sanitized_path_and_restores_it`
(`tests/test_tools_package_build.py:114`) parametrised over `sys.platform` (`win32`, `darwin`,
`linux`) with the stubbed PyInstaller main capturing `os.environ`: the exact list, no `DYLD_*`
leak, restoration on success and failure, Linux refused by name.

Design, Mach-O origin rule. Of CHARC's three options:
- `codesign --remove-signature` on a copy then whole-file compare: does NOT match. PyInstaller
  rewrites the load commands of every collected binary (`set_dylib_dependency_paths`:
  `LC_LOAD_DYLIB` / `LC_ID_DYLIB` to `@rpath/<basename>`, every `LC_RPATH` replaced,
  `utils/osx.py:437-591`), thins universal2 inputs (`binary_to_target_arch`, `lipo -thin`,
  `building/utils.py:321`), and the RECORD originals are themselves signed. It also needs
  `codesign`, so it cannot be tested on Windows.
- Re-sign-then-compare (replay PyInstaller's transformation on the RECORD original and compare
  bytes): exact, but it re-implements PyInstaller's private rpath computation, depends on ad-hoc
  signature determinism, and needs `install_name_tool` / `codesign` (untestable on Windows).
- RECOMMENDED: a stdlib-`struct` Mach-O NORMALISED IDENTITY, the Mach-O analogue of the PE
  section identity already at `build.py:2526-2575` (macholib is darwin-only in `uv.lock:709`,
  so it cannot serve the Windows tests; no new dependency). For thin arm64 (a fat original
  contributes its arm64 slice): header cputype / cpusubtype / filetype / flags; every segment's
  file bytes except `__LINKEDIT`; `__LINKEDIT` bytes up to the code-signature `dataoff`; load
  commands in order with `LC_CODE_SIGNATURE` and `LC_RPATH` removed, `__LINKEDIT`'s
  filesize / vmsize zeroed, each dylib name reduced to its basename (`@rpath/<b>` only where the
  original's basename is `<b>`). Separately: each built binary carries exactly one `LC_RPATH`
  of the form `@loader_path(/..)*` with the depth of its location. The bootloader: the same, plus
  `LC_SYMTAB` strsize, `__LINKEDIT` extended over the appended archive (`fix_exe_for_code_signing`,
  `utils/osx.py:167-212`), `LC_BUILD_VERSION` sdk (`set_macos_sdk_version`, `api.py:901`) and
  `update_exe_identifier` (`api.py:860`) as the only allowed differences. Symlinks: relative,
  inside the folder, framework-structure only; anything else refused. Tested on Windows with
  synthetic Mach-O fixtures built by `struct` (thin and fat; a re-signed signature, a rewritten
  dylib name, a replaced rpath pass; a changed `__TEXT` byte, an added load command, a different
  basename, the x86_64 slice, a foreign file, an escaping link fail), each "pass" case also
  shown to FAIL under the old whole-file rule (the check distinguishes). The runner build is the
  native proof (0 violations on the real bundle; a planted foreign dylib refused).

Also before `--smoke` can run on macOS: `tools/package/smoke.py:578-597` refuses POSIX
containment ("awaits WP6.5 native proof"); the darwin `_contained_process`
(`start_new_session` + `killpg(pgid, 0)` census + bounded `killpg`) is WP6.5's, proved on the
runner, with `tests/test_tools_package_smoke.py:754-757` as its existing tripwire.

### 7. The M census at this base

`pytest --collect-only -q -m macos`: 224 / 9,921 collected, all in
`tests/test_macos_portability.py`. By family and stage (stage 1 = the runner; stage 2 = the Mac):

| Family (function) | Cases | Stage 1 (runner) | Stage 2 (Mac) only |
|---|---|---|---|
| M-STATIC (`static_target_policy`) | 9 | all | - |
| M-PATH (`app_locations_and_isolation`) | 8 | all | - |
| M-SPAWN (`tool_and_worker_spawn`) | 5 | all (`killpg`, parent death) | - |
| M-PIPE (`default_pipe_fidelity`) | 6 | all (bundle FFmpeg on PATH) | - |
| M-DEVICE (`cpu_without_cuda`) | 10 | the reason / no-CuPy rows | DR-135 (a) AD-11 comparison of record (design item 5) |
| M-TEXT (`ffmpeg_text_and_redaction`) | 8 | the real listing + capture (DR-134) | P10's VT trial reason if the runner has no VT |
| M-CODEC (`videotoolbox_capabilities`) | 12 | "proved unavailable" + x265 fallback if no VT | the VT 8 / 10-bit trials and sink encode |
| M-RATE (`videotoolbox_quality_controls`) | 5 | skips with the VT reason if no VT | both Q1 candidates |
| M-V4 (`videotoolbox_v4`) | 4 | x265 half | VT half |
| M-V4 corpus (`videotoolbox_v4_corpus`) | 46 | x265 rows | VT rows |
| M-SPACE (`videotoolbox_space_estimate`) | 2 | skips if no VT | D87 / DR-48 on VT |
| M-FS (`filesystem_semantics`) | 51 | all (`hdiutil` images) | - |
| M-GUARD (`footage_guard_and_helpers`) | 24 | all | - |
| M-TOOL (`tool_reporting`) | 15 | all; T11 / T12 xfail flip with DR-123 | - |
| M-GUI (`native_gui_contract`, `gui`) | 15 | the Cocoa facts IF the runner has a GUI session (UNVERIFIED) | P71 trackpad phases, P33-P36 picking: the owner's hands |
| M-BUNDLE (`bundle_smoke`, `gui`) | 4 | all, after the build (F0-1 decides the path shape) | Finder / Terminal launch, Dock Quit, Cmd-Q, logout: the owner's hands |

If the runner has VT, the VT halves also run there; stage 2 stays the hardware evidence. The
VT-only M cases are SOURCE pytest cases: on the Mac they need the source checkout + venv
(~2.5 GiB), which item 9 shows fits; if it did not, they would re-bank by name.

### 8. The `macos` job sketch (mirrors `windows`, same order)

1. Checkout (same pin, `persist-credentials: false`, `fetch-depth: 0`).
2. `setup-uv` (same pin, uv 0.10.9, Python 3.12.13, `enable-cache: false`, the
   `uv-aarch64-apple-darwin` checksum, seat-fetched; F0-7).
3. Sync: `uv sync --frozen --no-default-groups --group dev` (no `--extra gpu`).
4. Version: release mode = `clearwater.__version__ == inputs.release-version` (the tag gate
   ran in `windows`); validation mode = record `clearwater.__version__` and `GITHUB_SHA`.
5. Static: `uv run mypy` and `uv run mypy --platform darwin`.
6. Parallel leg: `mkdir -p work`, `unset PYTEST_ADDOPTS`, `uv run pytest -q -rs -n 3 --timeout 600
   -m "not gpu and not footage and not gui and not slow and not fullclip and not macos"
   --basetemp=work/ci-parallel` (runner PATH shape: no FFmpeg; the WP6.3e skip policy applies).
7. Serial leg: `uv run pytest -q -rs --timeout 1200 -m "(gpu or footage or gui or slow) and not
   fullclip and not macos" --basetemp=work/ci-serial` (QUIT_SCRIPT per F0-11).
8. Build: `uv run python tools/package/build.py --form onedir --ffmpeg-from <macOS lock url>
   --ffmpeg-sha256 <macOS lock sha> --notices --smoke --zip --out work/release` (the smoke's
   export row on VT if the trial passes, else libx265, recorded).
9. M leg: bundle folder first on PATH, `CLEARWATER_MAC_BUNDLE=<built>`, `uv run pytest -q -rs
   --timeout 1200 -m macos --basetemp=work/ci-macos --junitxml=...`; then a skip-reason
   allowlist check over `-rs` (only "VideoToolbox unavailable on this Mac: ..." and the named
   hand-check reasons allowed; an FFmpeg-absent skip in the M leg fails the job).
   Collection identity on darwin: step 6 + step 7 + step 9 + fullclip = all.
10. Capture: the bundled `ffmpeg -hide_banner -encoders` and `-h encoder=hevc_videotoolbox`
    with the binary's sha256, the image version and `GITHUB_SHA` (DR-134 provenance).
11. Stage: `Clearwater-<version>-macos-onedir.zip`, `.zip.sha256` + `# source-commit`,
    `THIRD_PARTY_NOTICES-macos.md` (item 2).
12. Upload `macos-release` (assets) and `macos-evidence` (logs, junit, captures, walls).
Runner `macos-26`; `timeout-minutes` from the first run's walls (start at 180). A failing M
case fails the job (no `continue-on-error`).

### 9. Stage-2 run sheet outline (titles only; `docs/reports/wp6.5-mac-run-sheet.md`)

Disk minimum (CHARC note 1). The smallest full SCUBA clip by size (inventory CSV
`work\reports\inventory-20261018T235556Z.csv`, md5 `d86ed6bd...` as the 10-18 report records;
the reports carry folder totals only): `SCUBA/GX011589.mp4` 48,849,388 B (46.6 MiB, 6.4 s).
Next: `GX011592.mp4` 396,297,563 B (378 MiB, 42.3 s). A 6.4 s clip is a full clip but its
per-minute figure is start-up dominated; CHARC picks between the two. Minimum = input + output
(bounded by the input: High's R = 40 Mb/s < the source's ~61 Mb/s) + bundle (zip ~0.4 + unzipped
~0.7 GiB, CHARC's estimate) + the trim legs (~0.4 GiB: the trim + 12 Q1 outputs) + 5 GiB:
GX011589 -> 6.6 GiB, stated 7 GiB; GX011592 -> 7.3 GiB, stated 8 GiB; plus ~2.5 GiB if the
source legs run (10.5 GiB worst case, inside the Mac's 17 GiB).

1. Check free space (`df -h ~`); STOP below the minimum, naming what to free.
2. Create the program folder and `wp6.5-mac/` inside it.
3. Copy the inputs from Google Drive (the trim clip, the chosen full clip, the AD-11 inputs).
4. Unzip the artifact; first launch through System Settings > Privacy & Security > Open Anyway.
5. Record the machine facts (macOS version, model, free space) into `wp6.5-mac/`.
6. Bundle: version / refusal rows with HOME redirected.
7. Bundle: headless export of the trim on VideoToolbox (Q1 both candidates x quality x depth).
8. Bundle: V4 on each VT output.
9. Bundle: the CPU N6 figure, trim and the full clip (EXCLUSIVE); delete the full-clip output.
10. Bundle: the AD-11 exports (M-DEVICE design item 5).
11. Hand checks: Finder / Terminal launch, Dock Quit, Cmd-Q, logout during an export.
12. Hand checks: native file dialogs (P33-P36), trackpad wheel phases (P71).
13. Source legs if the minimum holds: Xcode CLT check, `uv` install (0.10.9), clone, sync, the
    M leg (VT halves) with HOME redirected.
14. Clean-up: delete large outputs; check `wp6.5-mac/` size.
15. Copy `wp6.5-mac/` into your Google Drive.

### 10. Group split and yields

- Group 1 (proved on Windows; no runner): CHARC note 1 (the notices skip moved), CHARC note 2
  (darwin PATH + `DYLD_*`; the Mach-O normalised identity for natives and the bootloader; the
  framework-link rule; `--zip` storing links), DR-123's licence-scan suffix set and delocate
  record (one test per suffix class; M-TOOL T11 / T12 un-xfail), the smoke's darwin
  containment (built, tested by stubs). YIELD.
- Group 2a: the macOS FFmpeg per CHARC's Q2 ruling (lock row, validator, Mach-O tool names in
  `bundle_ffmpeg`, notices rows) and the macOS notices census (F0-2). If the ruling is a
  self-build, the fork act is the owner's (as WP6.3c). YIELD (and an owner act if a fork build).
- Group 2b: the workflow per CHARC's Q5 ruling, the `release` job changes, the
  `tests/test_release_workflow.py` pins, actionlint, a byte-identity check of the `windows` job
  slice. YIELD for the owner's push (owner act: item 1's line).
- Group 3: fold the runner run (`gh run view` / `gh run download` read-only into
  `clearwater-review-evidence\wp6.5\runner\`), fix forward, the captured listing (DR-134),
  the M walls and `slow` markers; each re-run is an owner act; YIELD per run.
- Stage 2: the run sheet; YIELD for the owner's Mac run; fold the returned `wp6.5-mac/`.

### 11. Registration

New files and their surface (`tests/harness/genericity_lists.py`):
- `docs/proofs/wp6.5-ledger.md`, `docs/reports/wp6.5-macos-validation.md`,
  `docs/reports/wp6.5-mac-run-sheet.md`: prefixes `docs/proofs/`, `docs/reports/` (no edit).
- `tests/ffmpeg_text/*`, any `tools/package/native-licences/...` macOS texts: prefixes `tests/`,
  `tools/` (no edit).
- `.github/workflows/macos-build.yml` (option (c)) or `macos-validation.yml` (option (a)):
  OUTSIDE every prefix; needs a line in `INSTANCE_SURFACE_RELPATHS` beside
  `.github/workflows/release.yml` (`:254`). That file is the harness's, not WP6.5's: the seat
  makes the edit (or CHARC grants it) and runs the harness gate.
- `README.md`: existing, core-scanned (F0-10); no registration, vocabulary limits apply.

Depth at round-0 end: 254,025 (wp65-cell1, read by the dispatcher with cell_depth.py at its round-0 yield)

## Group 1 (`wp65-cell2`, dispatch-2; base `520a4a7e`)

Build turn, proved on Windows; no review round yet (Reviewer A r1 reads this head). Every
item test-first: the RED runs used the pre-change module (for `build.py`, a `git show` copy
under `work\wp6.5\base3|base4\` loaded through the test module's own `WP61_BUILD_SCRIPT`
hook; nothing checked out in the worktree). Working copies of the touched files were CRLF
(system `autocrlf=true`); each was normalised to LF before editing; every commit's blobs
have 0 CR.

### Items

1. **CHARC note 1 (F0-5), `5aa65d35`.** `tests/test_tools_package_notices.py:21-26` (the
   module `pytestmark` dropped; `WINDOWS_RELEASE_SKIP`; `VENV_SITE_PACKAGES` from
   `sysconfig.get_path("purelib")`), `:195-196` (the skip raised inside `release`), `:1053`
   (the real-wheel reader platform-neutral, so it keeps no skip). Identity proof below.
2. **CHARC note 2, darwin PATH, `3191302a`.** `tools/package/build.py:2350`
   (`DARWIN_ANALYSIS_SYSTEM_PATH`), `:2354-2428` (`run_pyinstaller`: win32 branch unchanged
   by text; `elif darwin` PATH = interpreter `bin`, venv `bin`, `/usr/bin`, `/bin`,
   `/usr/sbin`, `/sbin`, every `DYLD_*` removed, `DYLD_FALLBACK_LIBRARY_PATH=/usr/lib`,
   `DYLD_FALLBACK_FRAMEWORK_PATH=/System/Library/Frameworks`; `else` raises
   `BuildEnvironmentError` naming Linux; PATH and the `DYLD_*` set restored in the one
   `finally`). Test `tests/test_tools_package_build.py:120`
   `test_analysis_uses_only_sanitized_path_and_restores_it` x {win32, darwin, linux} x
   {success, failure} (6 ids; captures `os.environ` inside the stubbed analysis; exact PATH;
   DYLD set; full environment equal before / after; Linux refused before PyInstaller).
   RED: 4 failed (darwin, linux: the foreign PATH entry resolved, `else: pass`); GREEN 6.
3. **CHARC note 2, Mach-O origin rule, `96d162ce`.** `build.py:2597` `_macho_slices` (thin
   64-bit, or each slice of a FAT / FAT_64 file), `:2665` `_macho_identity` (the ledger
   section 6 design; for the bootloader also LC_SYMTAB strsize, LC_UUID, the SDK of
   LC_BUILD_VERSION / LC_VERSION_MIN_MACOSX), `:2776` `_macos_origin_identities` (interpreter
   and locked-RECORD files counted by suffix OR magic, so suffixless framework binaries
   count; RECORD verified first), `:2806` `macho_built_problem` (identity, then
   `@rpath/<basename>` names and id, then the LC_RPATH rule), `:2840` `_is_macos_bootloader`
   (thin arm64 built image vs the locked `runw`'s arm64 slice; `__LINKEDIT` must START with
   the original's, the PKG may follow), `:2931` `_macos_native_origin_violations` (the walk),
   `:3047` the `elif darwin` of `_is_clearwater_bootloader`, `:3057` `native_origin_violations`
   dispatches darwin / else; the Windows body moved UNCHANGED (diff: additions only) into
   `:3097` `_pe_native_origin_violations`; `_native_origin_hashes` gains a darwin-only
   `|= _macos_origin_identities()` after its unchanged loops. `_is_native` needed no change:
   its magic test already covers suffixless Mach-O; the darwin origin set now passes it the
   file head. RPATH RULE AS BUILT: exactly `@loader_path` + one `/..` per folder between the
   binary and the contents root when any dependency needs `@rpath`; none or that one
   otherwise, because PyInstaller adds the rpath only when required
   (`PyInstaller/utils/osx.py:574`, `if rpath_required and target_rpath not in rpaths`);
   the target depth is PyInstaller's (`building/utils.py:323-325`, dest name relative to the
   contents directory, `api.py:1186`). Tests `test_tools_package_build.py:1998-2200`
   (synthetic thin / fat images by `struct`, constants the test's own): 6 admitted
   transformations, each also refused under win32 (the whole-file rule) in the same test
   (re-signed, dylib names rewritten, rpath replaced, unsigned original, fat original's
   arm64 slice, suffixless framework binary); 8 refused images (changed `__TEXT` byte, added
   load command, different basename, system dependency redirected to `@rpath`, changed
   `__LINKEDIT`, x86_64 slice transformed, x86_64 slice untouched, foreign file); 7
   location faults (depth too shallow / deep, two rpaths, no rpath for an `@rpath`
   dependency, foreign rpath, absolute dependency name, id not `@rpath`); no-rpath allowed
   without an `@rpath` dependency; a transformed native outside the contents root refused;
   7 bootloader cases (the PyInstaller transformations admitted on darwin AND refused by the
   old prefix rule, which now serves only `else`; code byte, added dependency, changed
   `__LINKEDIT` prefix, added rpath, x86_64, still-fat refused). RED (base3): 15 failed =
   every admitted / location case (the base refuses every transformed Mach-O, fail-closed);
   the 15 refusal cases pass on both (they guard against over-admission). GREEN 30.
4. **F0-9 links, `c88da7f4` (the origin-walk half landed in `96d162ce`).** `build.py:2856`
   `framework_link_problem` (pure: admits exactly `<fw>/Versions/Current` -> a sibling
   version folder and `<fw>/<name>` -> `Versions/Current/<name>`, PyInstaller's
   `utils/osx.py:671-692`; refuses absolute / non-POSIX / empty targets, links outside a
   `.framework`, escapes and every other shape), `:2895` `_macos_entries` (`os.walk` without
   following links; a linked folder, a junction included, is pruned, never entered), `:2917`
   `_macos_link_problem` (adds: resolves outside the release folder, dangling, junction;
   resolution from the link's physical folder), `:3261-3318` `_release_files` (darwin ->
   `_macos_release_files`; else -> `_release_files_without_links`, the Windows body
   unchanged), `:3320` the snapshot records a link as `link:<text>`, `:3346-3410`
   `--zip` stores an admitted link as `S_IFLNK | 0755`, `ZIP_STORED`, content = the link
   text; files unchanged (0644, deflate 9). Tests `test_tools_package_build.py:2249-2435`: the
   pure rule (8 admitted incl. the `.app` path and a nested framework; 15 refused, each with
   its reason), the darwin origin walk over REAL links (admitted; and under win32 every link
   refused with today's text plus the transformed binary unknown), 4 refused real links, a
   junction (Windows only), the ZIP (links as links, files 0644, two writes byte-identical),
   the win32 ZIP refusal unchanged, 2 refused ZIP links, the snapshot detecting a retargeted
   link. `os.symlink` worked at this seat (no skip fired); a host without the privilege skips
   those tests by the named reason, the pure-rule tests run everywhere. RED (base3): 34 of 41
   failed (`framework_link_problem` absent; links refused); the 3 pre-existing
   `test_release_zip_refuses_smoke_mutations` ids also fail under a base COPY because the
   copy's `REPO_ROOT` is `work\` (environmental, not RED-relevant; they pass in tree). GREEN 41.
5. **DR-123, `8d1d53b9`.** `tools/spike_io/licences.py:86` `BUNDLED_LIBRARY_FOLDERS`
   (`av.libs` delvewheel, `av/.dylibs` delocate), `:156` `bundled_libraries`, `:175`
   `library_licence_wording` (prefixes match with or without `lib`), `:237` `_CODE_SUFFIXES`
   + `.so`, `.dylib`; the record adds `bundled_library_folders`. Framework binaries without
   suffix were NOT added: `wheel_text_files` is called for `av` only, whose macOS wheel
   carries `.so` and delocate `.dylib`s, no framework. Windows record checked at this seat:
   old vs new `pyav_ffmpeg()` every existing key equal (31 libraries, same order). Tests
   `tests/test_portability.py:4004` one per suffix class (`.so`, `.dylib`, `.dll`, `.pyd`,
   `.exe`: a Mach-O head full of licence words is never read as text) and `:4038` one per
   repair folder (delvewheel `.dll`, delocate `.dylib`); `_tool_t11` (`:3976`, W-TOOL T11 /
   T12) now asserts the Mach-O forms. RED: `.so` / `.dylib` read as text (4 GPL counted),
   `bundled_libraries` absent, T11 / T12 suffix assert; `.dll` / `.pyd` / `.exe` pass on both
   (controls). GREEN 22 (selection). **M-TOOL T11 / T12 NOT edited:** they are `macos`-marked
   and skip on Windows by design, so they cannot pass here; their `xfail` is conditional on
   `{".so", ".dylib"} <= _CODE_SUFFIXES` (`tests/test_macos_portability.py:1453-1456`), now
   false, so on the runner they run plain and must pass (G3 then drops the dead xfail).
6. **Smoke darwin containment, `838b0d59`.** `tools/package/smoke.py:172`
   `_group_contained_process` (`start_new_session=True`, pgid = root pid; refuses pgid 0 / 1
   / its own group before any signal; `communicate` bounded; the `killpg(pgid, 0)` census
   until the deadline -> SURVIVORS; a `finally` that always sends `killpg(SIGKILL)` and waits
   `_GROUP_CLEANUP_SECONDS` (5 s) for the group to empty, else a named failure), `:707`
   `elif darwin` binds `os.killpg` / `signal.SIGKILL` / `os.getpgrp()`, `:732` `else`
   refuses Linux by name. `_environment` (`:121`): the SystemRoot / System32 lines moved
   UNCHANGED into a win32 branch; darwin sets `TMPDIR` and PATH `/usr/bin:/bin` (needed: at
   the base `_environment` raises on any non-Windows host, so the darwin containment, and
   the existing `test_smoke_environment_strips_all_python_overrides`, would fail on the
   runner; the latter passes under the darwin simulation now). The Job Object path is
   unchanged (diff: no removed line in it). Tests `tests/test_tools_package_smoke.py:899-990`
   by stubs (clean row: new session, redirected HOME / TMPDIR, system PATH, stdin bytes, the
   signal sequence census -> SIGKILL -> census; survivor; survivor holding the pipes; hang;
   immortal group; pgid 77 / 1 / 0 never signalled; the darwin binding loaded under
   `sys.platform = "darwin"`; the Linux refusal) and the tripwire `:771` rewritten: off
   Windows, darwin runs a REAL clean row and a REAL survivor row (refused, then the
   grandchild must be gone within 5 s); any other POSIX host is refused by name. RED: 8
   errors + 2 failures (`_group_contained_process` absent; darwin refused "awaits WP6.5");
   GREEN 10 + the tripwire skipped here by its reason.

### Note-1 identity proof (Windows)

Base module `git archive a186c3ee tests/test_tools_package_notices.py` ->
`work\wp6.5\base-a186c3ee\` (sha256 `15392b8f...` = the worktree's file before the edit).
Base run: 415 collected, 415 passed. After: 415 collected, 415 passed. Outcome sets by node id
(`-v` lines, `PASSED|FAILED|SKIPPED`, sorted): 415 = 415, identical (sha256 of both sorted
lists `64503c4c6188de96...`). Final head: 415 passed.

Darwin expectation for the runner (from a SIMULATION at this seat: a scratch plugin sets
`sys.platform = "darwin"` after start-up; not a proof): 161 ids run (the 158 neutral + the 3
real-wheel reader ids, now platform-neutral), 254 ids (108 functions) skip with
"Windows native/interpreter fixture: the synthetic release copies python312.dll and writes
Clearwater.exe (no macOS release fixture yet)". In the simulation 160 passed and 1 failed:
`test_root_annex_generator_checks_committed_bytes_and_detects_a_changed_row` imports
`urllib.request`, which on `sys.platform == "darwin"` imports `_scproxy` (absent on Windows): a
simulation artifact; the runner decides it. The 3 reader ids read
`<venv purelib>/numpy-2.5.4.dist-info/licenses/LICENSE.txt`,
`scipy-1.18.1.dist-info/LICENSE.txt`, `pyinstaller-6.22.3.dist-info/licenses/COPYING.txt`:
that the macOS wheels install those exact names is UNVERIFIED (no wheel downloaded).

### Counts at the group-1 head `838b0d59` (`-p no:cacheprovider --timeout 600 -k 'not test_python_m_clearwater_starts_the_shell_and_exits_0'`)

Static: `ruff check .` All checks passed; `ruff format --check .` 337 files already formatted;
`mypy` Success 166; `mypy --platform darwin` Success 166.

| Module | Result |
|---|---|
| `tests/test_tools_package_notices.py` | 415 passed |
| `tests/test_tools_package_build.py` | 200 passed (base 131: the PATH test 1 -> 6 ids, +30 Mach-O, +34 links / ZIP) |
| `tests/test_tools_package_smoke.py` | 44 passed, 1 skipped (the non-Windows tripwire, by its reason) |
| `tests/test_portability.py` | 192 passed |
| `tests/test_macos_portability.py` | 224 skipped (`macos` platform skip) |
| `tests/test_release_workflow.py` | 59 passed |

### Verification loop (self, before Reviewer A)

- Suspected: a one-slice FAT file passes the bootloader check. CONFIRMED by design review
  of `_macho_slices`; FIXED before commit (the built bootloader must be a thin image;
  `still-fat` case).
- Suspected: relative links with `/` do not resolve on Windows through a linked folder.
  CONFIRMED (real-link tests reported `dangling link`); FIXED: resolve from the link's own
  physical folder (`path.parent / target`), the same result on macOS.
- Suspected: `os.walk(followlinks=False)` still enters a Windows junction. CONFIRMED (the
  junction test saw the junction's file); FIXED: linked folders are pruned from the walk.
- Suspected: the licence record's library order changes on Windows. CONFIRMED (Path sort is
  case-insensitive on Windows); FIXED: sorted by name; records compared equal.
- Suspected: `_environment` raises on macOS. CONFIRMED by reading (`SystemRoot` check);
  FIXED in item 6 (darwin branch); the existing env test passes under the simulation.
- Rejected as false positive: none. A final pass found nothing new.

### Findings for the dispatcher (evidence; not built here)

- **G1-F1 (STOP for a ruling; affects the first runner build) -- PyInstaller makes links
  OUTSIDE frameworks in a macOS onedir.** `PyInstaller/depend/bindepend.py:196-210`: on
  non-Windows, every binary dependency collected into a subfolder gets a top-level link
  `<contents>/<basename>` -> `<subfolder path>` unless a hook suppresses it (no PySide6 /
  numpy / scipy / Pillow hook does; only the NVIDIA hooks set
  `bindepend_symlink_suppression`). Qt framework dependencies resolve to
  `PySide6/Qt/lib/QtCore.framework/Versions/A/QtCore`, so the onedir will very likely hold
  `_internal/QtCore -> PySide6/Qt/lib/QtCore.framework/Versions/A/QtCore` and the delocate
  dylibs' top-level links. Item 4 as dispatched refuses them ("outside a framework"), so
  the origin check and `--zip` would fail the build. Recommended second admitted class
  (not built): a link directly in the contents root, relative, whose name equals its
  target's basename, resolving inside the contents root to a regular file (the exact
  `bindepend` shape). A `.app` adds BUNDLE's cross-links between `Contents/Frameworks`,
  `Contents/Resources` and `Contents/MacOS` (`building/osx.py:418-425`, `:488-490`,
  `:545-547`): a third class only if Q3 rules the `.app`.
- **G1-F2 (G2a) -- `tools/package/notices.py:1418-1419` refuses ANY linked entry** in the
  built folder (`notices: unsafe linked entry`), so `--notices` fails on the first
  framework link: the Mac notices census (F0-2) must learn the same link rule.
- **G1-F3 (G2a / G2b) -- the ZIP gives every file mode 0644** (`build.py` `write_release_zip`):
  the unzipped macOS `Clearwater` executable and the bundled `ffmpeg` / `ffprobe` will not
  be executable. A darwin executable-bit rule (0755 for Mach-O executables) is needed before
  stage 2; not built (outside items 1-6).
- **G1-F4 (G2a) -- the smoke's run path is still Windows-only:** `run_smoke` refuses
  non-Windows, `_ffmpeg_checks` looks for `ffmpeg.exe`, the planted exception targets
  `_ccallback_c*.pyd`; item 6 built the containment only.
- **G1-F5 (record) -- `test_root_annex_generator...` on darwin** imports `urllib.request`
  (`_scproxy`); expected to pass natively, unverified.

### What only the runner can prove (the G3 list)

1. The 158 neutral notices ids + 3 reader ids pass natively; the 254 skip with the reason.
2. A real PyInstaller build passes the Mach-O identity: 0 origin violations (every
   transformed native admitted by identity + its rpath / names; the bootloader by its
   normalised image), and a planted foreign dylib is refused.
3. The darwin analysis environment: PyInstaller analysis succeeds under the sanitised PATH
   and DYLD fallbacks (no Homebrew library reached).
4. The framework links (and G1-F1's class once ruled) pass the walk and survive `--zip` as
   links; an unzip on macOS restores them.
5. The smoke tripwire natively: a clean row, a survivor refused and killed with its group.
6. M-TOOL T11 / T12 pass plain (xfail condition false).
7. `test_smoke_environment_strips_all_python_overrides` and the other smoke tests natively.

Depth at group-1 yield: 369,005 (wp65-cell2, read by the dispatcher with cell_depth.py at its group-1 yield)

## Group 2b (`wp65-cell3`, dispatch-3; base `8ca7aeaf`)

Build turn plus the Reviewer A r1 fold, proved on Windows. Commits: `2704a852` (items 1-4),
`01407c6e` (item 5), `b8fcecc8` (item 6), `a8b0132c` (the AD-33 pack-scan fix found in the
cell's own loop), then this ledger. RED runs used the base `build.py` / `notices.py` copied
to `work\wp6.5\base\` and loaded through `WP61_BUILD_SCRIPT` (as group 1), and for the
workflow a copy of the test module beside the BASE `release.yml` under `work\wp6.5\redwf\`.
Every commit's blobs have 0 CR (checked per file per commit).

### A r1 adjudication

| # | Severity | Finding | Verdict | Change | Tests (RED on base -> GREEN) |
|---|---|---|---|---|---|
| A1 | MAJOR | `os.walk` without `onerror` swallowed an unreadable subtree from the origin check and the ZIP | FIXED | `build.py:2972` `_walk_error` raises; `:2977` `_macos_entries` passes it (the ONE macOS walker: origin walk, ZIP, notices and the folder-link view all use it) | `test_tools_package_build.py:2802` `test_unreadable_folder_fails_the_macos_walks[root,nested]`: `os.scandir` patched to raise for the root / a nested folder; the origin check, the ZIP and the notices inventory each raise and no ZIP is written. RED: 2 failed (DID NOT RAISE) |
| A2 | MINOR | `linkedit.rstrip(b"\0")` admitted a changed final string-table terminator | FIXED | `build.py:2714` `_macho_identity`: `__LINKEDIT` content runs to the signature; ONLY a gap of < 16 zero bytes between the LC_SYMTAB string table's declared end and the signature is excluded (`:2795`); `:2829` `_macho_digest` and `:2907` `_is_macos_bootloader` compare without any strip | `:2258` padding table (7: padding dropped / kept admitted; 16 zeros dropped refused, kept admitted; junk dropped refused, kept admitted; final terminator changed refused); `:2280` the same for an ordinary native (2); bootloader `changed-final-string-terminator`; native `dropped-final-string-terminator`. RED: 6 failed incl. the reviewer's probe |
| A3 | ADVISORY | unexplained bytes after the segments left the identity unchanged | FIXED (folded) | `build.py:2824`: an image must END where its segments end; `:2789-2791` the signature must lie inside `__LINKEDIT`. Applies to every thin image, the bootloader included: its PKG lies INSIDE `__LINKEDIT` after `fix_exe_for_code_signing` (`PyInstaller/utils/osx.py:223-224` sets strsize / filesize to the file end before signing), so the archive stays its only allowance. No PyInstaller output for an ordinary native carries a trailer: `codesign` writes the signature at `__LINKEDIT`'s end (the runner build is the native proof, G3 item 2) | `appended-trailer` (native and bootloader), `signature-outside-linkedit`. RED: the two trailer cases failed (admitted) |

### Items

1. **A r1 fold:** above.
2. **G1-F1 classes (B) and (C), ONE shared predicate (`2704a852`).** `build.py:3071`
   `macos_link_problem(root, contents, path)` = THE rule; `:3009`
   `_macos_link_class_problem` (relative POSIX target; resolved from the link's physical
   folder inside `root`; exists; ONE HOP: the named target itself (lstat of the joined
   path) is not a link; then framework (`framework_link_problem`, unchanged) or (B) or
   (C)); `:3049` `macos_link_view` (a folder target's entries, never through a further
   link); `:3126` `_macos_depth` (a `.app`'s Resources mirrors Frameworks). Callers: the
   origin walk `:3232` (a folder link's FILES are origin-checked at the link's location,
   depth included); the ZIP `_macos_release_files` (contents root from `:3119`
   `_macos_contents`); `notices.py:1419` (G1-F2: on darwin the same walker and predicate,
   an admitted link adds no entry; win32 unchanged, every link refused with today's text).
   Reading of "one hop" (disclosed, not a STOP): the TARGET named by the link must not be a
   link; a target path that passes THROUGH an admitted folder link is allowed, because the
   framework class the ruling keeps already does that (`<fw>/QtCore -> Versions/Current/QtCore`
   traverses `Versions/Current`), and every link on such a path is itself checked by the
   walk. Tests: `test_tools_package_build.py:2539` `LINK_CASES` (14 cases: B onedir; B in a
   `.app` through PyInstaller's dotted-folder link plus its Resources copy; C data file; C
   binary folder with nested framework links; refused: B name mismatch, B not in the
   contents root, B to a folder, B to outside the contents root, a PLANTED ESCAPING LINK, a
   PLANTED LINK-TO-LINK (the bindepend name pointed at the framework's own top-level link),
   C link-to-link, C outside the three folders, C into `_CodeSignature`, a cross-link shape
   in a onedir) run through ALL callers: `:2696` origin walk (14), `:2709` ZIP (14), `:2737`
   notices (9 onedir); `:2749` notices on win32 unchanged; `:2758` a bad link INSIDE a
   folder target refuses the folder link too; `:2777` a transformed native seen through a
   non-mirrored cross-link fails its rpath depth. Two group-1 rows re-reasoned
   (`:2411`: the B-shaped dangling link now reads "dangling", the escaping
   `Versions/B` reads "outside the release folder"). RED: 42 failed (admitted cases refused
   as "outside a .framework"; refusals with the base's other text; A1 not raised).
3. **G1-F3 (`2704a852`).** `build.py:3653` `write_release_zip`: darwin members whose mode
   carries an execute bit are `S_IFREG | 0755`, others 0644 (`:3720-3724`, AD-36 form);
   win32 0644 always, the mode never read. Tests `:2842` the Windows byte-identity over a
   MIXED run (`.exe` / `.bat` / suffixless files chmod 0755 beside 0644 texts; every member
   0644; the archive's sha256 pinned to the BASE's output
   `0d3bfbfb13332df42f0180e90556ccf7d7d43602b8b2ea04c924df21788d6d10`, which the base
   module reproduces: PASSED on base); `:2859` the darwin rule from the real file mode
   (green on a Windows host via `.exe`'s execute bit, and on darwin for all four
   executables). RED: the darwin test failed (every member 0644).
4. **The `.app` zip shape and the tool hook (`2704a852`).** `build.py:92` `MACOS_APP`;
   `:345` `release_zip_name` (Windows unchanged; darwin `Clearwater-<version>-macos`);
   `:365` `release_zip_folder` (darwin = `Clearwater.app`, the ZIP's ONE top-level item);
   `:702` `find_executable` prefers `Clearwater.app/Contents/MacOS/Clearwater` on darwin
   (PyInstaller's `--windowed` leaves the onedir COLLECT beside the BUNDLE; not shipped);
   `:3653` `write_release_zip(..., name=)`; `build()` zips `release_zip_folder(root)` under
   `release_zip_name` (`:3933-3945`). The hook: `:3138` `place_macos_tools(bundle,
   executables, texts)` copies the VERIFIED bytes unchanged, code to `Contents/MacOS` (0755;
   AD-34 (2) puts the frozen executable's folder first on PATH, so the bundled FFmpeg is
   found there; M-BUNDLE P16 / P57 find it anywhere under the bundle) and texts to
   `Contents/Resources` (0644; `Contents/MacOS` holds only code under the seal); `:3183`
   `seal_macos_bundle` = ad-hoc RE-SIGN AFTER (`/usr/bin/codesign --sign - --force
   --timestamp=none <app>`, WITHOUT `--deep` so nested code keeps its bytes and the origin
   hashes / identities still hold) then `codesign --verify --deep --strict --verbose=2`
   (ruling 3's seal proof), bounded, named failures. `build()` `:3905-3924`: on darwin,
   after FFmpeg and notices, seal then RE-RUN the origin check (the re-signed bootloader).
   Tests `:2904`, `:2912`, `:2922`, `:2950` (4 refusals), `:2957`, `:2986` (4 failures),
   `:3032` (sealed / seal fails / origin after seal fails), `:3090` (win32 never seals).
   RED: 18 failed. **Found in the loop and fixed (`a8b0132c`):** `build()` scanned the GPU
   pack on darwin, but a CPU-only sync installs none of its distributions, so EVERY darwin
   build would have failed "the pack sources cannot be scanned" before PyInstaller; darwin
   now scans no pack (AD-33) (`:3802-3811`); test `:3059` (darwin passes without a pack,
   win32 still refuses). Its RED by reading (the base calls `pack_sources()` on every
   platform; the base copy under `work\` cannot run `build()`: its `REPO_ROOT` is `work\`).
5. **The workflow (`01407c6e`).** `.github/workflows/macos-build.yml` per rulings 1-2: one
   `macos` job; `workflow_call` (`release-version` required), `workflow_dispatch`, `push`
   `macos-validation/**`; `permissions: contents: read`; no release job, no tag gate;
   `macos-26`; `timeout-minutes: 180`; the windows job's three pinned actions (checkout,
   setup-uv with the darwin checksum `a92f61e9...f376`, upload-artifact); CPU-only sync;
   steps: version + run record (validation: `clearwater.__version__`, `GITHUB_SHA`,
   `ImageOS`, `ImageVersion`, `sw_vers`; release: equals `release-version`), static (both
   mypy targets), parallel (`-n 3`, the canonical marker `and not macos`, the cell `-k`),
   serial (`and not macos`, the `-k`), build, the M leg (`CLEARWATER_MAC_BUNDLE` = the
   built `.app`, its `Contents/MacOS` first on PATH, `-k`, junit), the skip-reason
   allowlist (only "VideoToolbox unavailable on this Mac: ..."; a missing passing summary
   fails), the capture, the stage (`Clearwater-<v>-macos.zip`, sidecar + `# source-commit`,
   `THIRD_PARTY_NOTICES-macos.md` from `Contents/Resources`), uploads `macos-release` and
   `macos-evidence` (`if: always()`); every pytest line `| tee work/evidence/<leg>.log`
   under bash's `-eo pipefail`. **The named switch** `MACOS_FFMPEG_BUNDLED: "false"` (job
   env): off = the build makes the `.app` with NO `--ffmpeg-*` / `--notices` / `--smoke` /
   `--zip`, the M leg deselects the FFmpeg families, no capture of encoders, no stage, no
   `macos-release`, and RELEASE MODE IS REFUSED by the version step ("macOS release assets
   await WP6.5 group 2a"); on = the release build from `tools/package/ffmpeg-macos.lock.json`
   (`asset_url`, `seat_sha256`; the lock's name and shape are group 2a's to confirm, the
   step's pin test with it). `release.yml` exactly as ruled: `macos: needs: windows, uses:
   ./.github/workflows/macos-build.yml, with: release-version`; `release: needs: [windows,
   macos]`; a second download (`macos-release`); `THIRD_PARTY_NOTICES-macos.md` in `files:`.
   Tests `tests/test_release_workflow.py`: the windows job slice and the header (triggers,
   permissions, concurrency) sha256-pinned to `8ca7aeaf` (`:805`); the release job equals
   the base after undoing exactly the three ruled edits (`:811`); the existing pins
   re-pointed (`job()` helper; 7 pinned actions + the one local call; `needs: [windows,
   macos]`; the macOS download and notices); `macos-build.yml` `:834-1094` (triggers, no
   release / tag gate / write permission / download / secrets / push; same pins; runner,
   budget, env, CPU-only; step order; the three pytest lines token by token; the switch;
   the version step EXECUTED in 5 modes; the allowlist EXECUTED on 6 logs). RED (base
   workflow): 21 failed. actionlint and the harness registration are the SEAT's (ruling 1).
6. **README (`b8fcecc8`).** The `## Platforms` macOS bullet replaced: no Mac download yet;
   for a source run on a Mac, Xcode Command Line Tools (`xcode-select -p`, `xcode-select
   --install`) and uv at the builds' 0.10.9 (`curl -LsSf https://astral.sh/uv/0.10.9/install.sh
   | sh`, `uv --version`); uv fetches Python 3.12; FFmpeg on PATH as for any source run (the
   existing next bullet). No forbidden term (F0-10); nothing claimed the code does not do.

### Counts at the group-2b head (`-p no:cacheprovider --timeout 600 --basetemp=work\wp6.5\g2b\<module> -k 'not test_python_m_clearwater_starts_the_shell_and_exits_0'`)

Static: `ruff check .` All checks passed; `ruff format --check .` 337 files already
formatted; `mypy` Success 166; `mypy --platform darwin` Success 166.

| Module | Result |
|---|---|
| `tests/test_tools_package_build.py` | 275 passed (group 1: 200) |
| `tests/test_release_workflow.py` | 78 passed (group 1: 59) |
| `tests/test_tools_package_notices.py` | 415 passed (run with `-n 3` to fit the 10-minute tool call; with the same `notices.py` the 415 also passed serially in a combined run before the commit) |
| `tests/test_tools_package_smoke.py` | 44 passed, 1 skipped (the non-Windows tripwire) |
| `tests/test_portability.py` | 192 passed |
| `tests/test_macos_portability.py` | 224 skipped (`macos` platform skip) |

### Verification loop (self)

- Suspected: a one-hop rule read as "no link anywhere on the target path" would refuse the
  framework links the ruling keeps. CONFIRMED by reading (`<fw>/QtCore ->
  Versions/Current/QtCore`); resolved by the reading above (the TARGET itself), tested by
  the planted link-to-link and the dotted-folder cases.
- Suspected: a folder link's view could recurse forever through a cycle of folder links.
  CONFIRMED possible in principle; FIXED by design: nested links are classified at the
  virtual location but never entered (each is checked, and viewed, at its own physical
  place).
- Suspected: the darwin build fails before PyInstaller (the GPU pack scan). CONFIRMED by
  reading `pack_sources` against a CPU-only sync; FIXED `a8b0132c`.
- Suspected: re-signing the bundle `--deep` would rewrite the FFmpeg tools and break their
  whole-file hashes. CONFIRMED by PyInstaller's own `--deep` signing (`building/osx.py`
  `assemble`); the seal re-signs WITHOUT `--deep`.
- Suspected: the darwin build tests import PyInstaller under a patched `sys.platform`.
  CONFIRMED (`PyInstaller/compat.py:110` reads `platform.mac_ver()` at import: failed in a
  narrow selection); FIXED in the tests (the archive is built before the patch).
- Rejected as false positive: none. A final pass found nothing new.

### Findings for the dispatcher

- **G2b-F1 (record; runner decides) -- PyInstaller can make a link-to-link the ruled rule
  refuses.** `building/osx.py:400-425` cross-links a binary-only folder whose parent is
  MIXED (`Contents/Resources/<p>/.dylibs -> ../../Frameworks/<p>/.dylibs`) and `:440-462`
  makes `Contents/Frameworks/<p>/.dylibs -> __dot__dylibs`: two hops, refused by ONE HOP.
  Not expected in this build: in the 1.1.1 Windows onedir `PIL`, `numpy` and `scipy` hold
  binaries only (so the WHOLE folder is cross-linked once and the dotted link sits behind
  it). If the runner's origin walk names a "link to a link", it is this, and the ruling
  needs a third shape (the dotted-folder pair).
- **G2b-F2 (record) -- a tag push before group 2a makes NO draft.** With the switch off,
  release mode refuses in the macOS job, so `release` (needs both) is skipped: once this
  reaches main, no Windows-only release can be cut until group 2a lands (or the switch's
  meaning is ruled otherwise).
- **G2b-F3 (record) -- the source-run FFmpeg on a Mac.** The README's existing source-run
  line requires FFmpeg on PATH; the Mac prerequisites name only the ruled two tools, so the
  guide's Mac source section (stage 2) must say where a source run's FFmpeg comes from (no
  Homebrew requirement is ruled).

### What only the runner proves (stage 1, first run, switch OFF)

WILL prove (the owner's push of this head): the darwin uv checksum and CPU-only sync; the
version / run record (image version, `GITHUB_SHA`, `sw_vers`); both mypy targets natively;
the parallel and serial legs on macOS (the WP6.3e FFmpeg skip policy; the 158 neutral
notices ids; the smoke tripwire's real clean / survivor rows; G1-F5); a real PyInstaller
`.app` under the darwin PATH / DYLD sanitising; the Mach-O identity on real natives and the
bootloader (0 violations expected), the link classes on real BUNDLE output (G2b-F1), the
A3 end-of-image rule on real files; the seal (`codesign` re-sign + `--verify --deep
--strict`) and the origin re-check after it; the M leg without the FFmpeg families: M-STATIC,
M-PATH, M-DEVICE, M-FS (`hdiutil`), M-GUARD, M-TOOL (T11 / T12 plain), M-GUI (if the
runner has a session), M-BUNDLE P24 / X28 on the real `.app`; the allowlist.
WILL NOT prove until group 2a (the switch ON): FFmpeg inside the bundle and the seal over
it, the notices (`Contents/Resources/THIRD_PARTY_NOTICES.md`), the darwin smoke, `--zip`
and the ZIP's links / execute bits after a real unzip, the stage and `macos-release`, the
encoder capture (DR-134), and the M families deselected now: M-PIPE, M-TEXT, M-CODEC,
M-RATE, M-V4, M-V4 corpus, M-SPACE, M-SPAWN, M-BUNDLE P16 / P57. Release mode is refused.

### The owner's act for stage 1 (asked by CHARC)

`git push origin wp6.5:refs/heads/macos-validation/wp6.5` (after the seat's actionlint and
harness registration of `.github/workflows/macos-build.yml`). Re-runs: re-push, or "Re-run
jobs" on the run page.

Depth at group-2b yield: 381,605 (wp65-cell3, read by the dispatcher with cell_depth.py at its group-2b return)

## Group 2a (`wp65-cell4`, dispatch-4; base `b76066e1`)

Turn 4a = part 1: the fork's macOS FFmpeg recipe as a patch, and the component pin table. No
product, test or workflow edit in Clearwater; no `uv lock`; no downloaded script or binary was
run (the build scripts and tarballs were read as text / listed as data; `bash -n` PARSE-ONLY
syntax checks on the four edited scripts and the workflow's run blocks, no execution). Helper
clones and data under `work\wp6.5\g2a\` (left in place for the seat): `FFmpeg-Builds\` (the fork,
branch `wp6.5-macos`), `FFmpeg-Builds-applycheck\` (the apply proof), `build-script\` (Riedl),
`x264\` (metadata clone), `dl\` (the 19 downloaded files, data only), `x265cmp\`, `ffmpeg-src\`
(`configure`, `ffbuild/version.sh`, `RELEASE` at `b204e94e`), `runner\` (the image readme),
`riedl-site\` (the provider's `versions.txt` / `codecs.txt`), `static\check_pins.py` + its output,
`fork-commit-message.txt`.

### 4a.0 The fork base

`git ls-remote --symref https://github.com/rwsmythe/FFmpeg-Builds.git HEAD` (2026-11-09):
`ref: refs/heads/wp6.3c-nozvbi-r2 HEAD` / `d77b8352f60bd180ebce585632846533aa60b183 HEAD`; branches
`master` `c63bb308...`, `wp6.3c-nozvbi` `92d0b6a6...`, `wp6.3c-nozvbi-r2` `d77b8352...`. As expected.

### 4a.1 The Riedl script pin

`https://git.martin-riedl.de/ffmpeg/build-script.git`, default branch `main` (`ls-remote --symref`),
head **`f63b8aab8f5ce1a067da86ba69e34a36a7e217e5`** (2026-08-17T17:33:44+02:00, "chore: ffmpeg
update (version 9.0.1)"); read from a `git clone` (autocrlf off; 0 CR in the tree). Kept despite
`develop` being newer (`ab619910`, 2026-10-31): the README names `main` the release-build branch;
`develop` differs in scripts only by fribidi's switch to meson (needed for fribidi 1.0.17's help2man)
and lame. Evidence that matters for the runner: the provider's own 9.0.2 macOS arm64 build
(`riedl-site\versions.txt`) says "built with Apple clang version 14.0.0 (clang-1400.0.29.102)", so the
script's macOS path is proven on an old toolchain, not on Xcode 26.6 / clang 21.

Runner (image readme `images/macos/macos-26-arm64-Readme.md` at `actions/runner-images`
`741e4eb8`, 2026-11-09): macOS 26.7.2 (25G332), image 20261102.0473.1 (round 0 read 26.6.2 /
20261026: the image moved); default Xcode 26.6 (17F113), Clang/LLVM 21.0.0, Xcode CLT
26.6.0.0.1781586589, Homebrew 7.0.11 with pkgconf 3.0.10, Ninja 1.13.2, CMake 4.4.5, Python3
3.15.2, Cargo / Rust 1.99.1; **no autoconf, automake, libtool, cargo-c, meson or virtualenv** (0 hits).

### 4a.2 Component pin table (arm64 macOS GPL build, the proposed skip set)

Columns: component | how the script obtains it (at `f63b8aab`) | as the script stands | the recipe's
pin | licence (basis) | GPL-3.0-compatible | linkage | file:line (upstream). "Windows row" = the
seat-verified row of `tools/package/ffmpeg.lock.json` for the same project at a different pin;
"tarball read" = the licence file read inside the pinned tarball by the cell; neither is a
seat verification of THIS pin (part 3's census).

| Component | Obtained | As the script stands | Recipe pin | Licence (basis) | GPL-3.0 | Linkage | file:line |
|---|---|---|---|---|---|---|---|
| FFmpeg 9.0.1 | `https://ffmpeg.org/releases/ffmpeg-$VERSION.tar.bz2` | FLOATING (tarball, no checksum) | **edit**: git `release/9.0` + `checkout --detach b204e94e90fca64045e9ca7dd44c65678c7eb29e` | GPL-3.0-or-later as configured (`--enable-gpl --enable-version3`) | yes | the program | `build-ffmpeg.sh:49`; `build.sh:662` |
| zlib 1.3.2 | `https://www.zlib.net/fossils/zlib-1.3.2.tar.gz` | FLOATING | sha256 `bb329a0a...9d16` | Zlib (tarball read; Windows row) | yes | static (`--static`) | `build-zlib.sh:41`; `build.sh:265` |
| openssl 3.6.1 | GitHub release `openssl-3.6.1.tar.gz` | FLOATING | sha256 `b1bfedcd...a82e` (= upstream `.sha256` = GitHub digest) | Apache-2.0 (tarball read; Windows row) | yes (GPL-3 only: the script sets `--enable-version3` for it, `build.sh:274-275`) | static (`no-shared`) | `build-openssl.sh:41`; `build.sh:271` |
| libxml2 2.15.3 | `download.gnome.org/.../libxml2-2.15.3.tar.xz` | FLOATING | sha256 `78262a6e...7a07` (= gnome `.sha256sum`) | MIT AND ISC-Veillard (Windows row; tarball `Copyright` read) | yes | static (`--enable-shared=no`); `--enable-libxml2` always (`build-ffmpeg.sh:68`) | `build-libxml2.sh:42`; `build.sh:292` |
| fribidi 1.0.16 | GitHub release tar.xz | FLOATING | sha256 `1b1cde5b...a05c` (asset has no GitHub digest) | LGPL-2.1-or-later (tarball read; Windows row) | yes | static | `build-fribidi.sh:41`; `build.sh:298` |
| freetype 2.13.0 | savannah, mirror sourceforge | FLOATING | sha256 `a7aca0e5...1f80` (both URLs, same bytes) | FTL OR GPL-2.0-or-later (Windows row; cell-read UNVERIFIED for this tarball) | yes | static | `build-freetype.sh:46,49`; `build.sh:304` |
| fontconfig 2.17.1 | freedesktop GitLab generic package | FLOATING | sha256 `9f5cae93...a541` | MIT (Windows row; tarball `COPYING` read) | yes | static | `build-fontconfig.sh:41`; `build.sh:311` |
| harfbuzz 14.3.0 | GitHub release tar.xz (meson) | FLOATING | sha256 `16070d77...eae` (= GitHub digest) | MIT-Modern-Variant ("Old MIT", tarball read; Windows row) | yes | static | `build-harfbuzz.sh:41`; `build.sh:318` |
| SDL2 2.32.10 | `libsdl.org/release` | FLOATING | sha256 `5f5993c5...5165` | Zlib (tarball read; Windows row) | yes | static; unskippable in `build.sh:324-328`, FFmpeg autodetects `sdl2` (configure `EXTERNAL_AUTODETECT_LIBRARY_LIST`): ffplay (not shipped) and libavdevice's sdl2 output device in ffmpeg | `build-sdl.sh:41` |
| libass 0.17.5 | GitHub release | FLOATING | sha256 `caab4b99...094a` (= GitHub digest) | ISC (tarball read; Windows row) | yes | static | `build-libass.sh:41`; `build.sh:384` |
| x264 | `code.videolan.org/.../archive/master/x264-master.tar.gz` | FLOATING (branch) | **edit**: git clone + `checkout --detach 0480cb05fa188d37ae87e8f4fd8f1aea3711f7ee` (master head, 2025-09-10, r3223; also the Windows pin) | GPL-2.0-or-later (repo `COPYING` + Windows row) | yes | static | `build-x264.sh:36`; `build.sh:554` |
| x265 4.2 | `bitbucket.org/multicoreware/x265_git/get/4.2.tar.gz` (generated) | FLOATING | **edit**: `downloads/x265_4.2.tar.gz` sha256 `40b1ea04...1210` | GPL-2.0-or-later AND MIT (Windows row) | yes | static, 8+10+12-bit (`SKIP_X265_MULTIBIT=NO`, Main10 needed) | `build-x265.sh:42`; `build.sh:568` |
| libogg 1.3.6 | osuosl | FLOATING | sha256 `83e67047...4638` | BSD-3-Clause (tarball read; Windows row) | yes | built, NOT linked (unskippable `build.sh:402-406`; no FFmpeg flag uses it once vorbis / theora / opus are skipped) | `build-libogg.sh:41` |
| nasm 3.02 (tool) | `http://www.nasm.us/...` + GitHub archive mirror | FLOATING | sha256 `f504227b...5998` / mirror `39e251d3...1586` | BSD-2-Clause (tarball read) | n/a | build tool, not linked (x86 asm only) | `build-nasm.sh:43,46`; `build.sh:238` |
| pkg-config 0.29.2 (tool) | freedesktop | FLOATING | sha256 `6fc69c01...d591` | GPL-2.0-or-later, internal glib LGPL-2.1-or-later (tarball read) | n/a | build tool (`--with-pc-path=$TOOL_DIR/lib/pkgconfig`) | `build-pkg-config.sh:40,98`; `build.sh:259` |
| cmake 4.0.3 (tool) | Kitware `cmake-4.0.3-macos-universal.tar.gz`, fallback source build | FLOATING (version hard-coded, no checksum) | sha256 `4e85de4d...ce9a` (= `SHA-256.txt` = GitHub digest); source `8d3537b7...3ffb` (= `SHA-256.txt`) | BSD-3-Clause | n/a | build tool (ninja, x265) | `build-cmake.sh:67,90`; `build.sh:280` |
| ninja 1.13.2 (tool) | GitHub tag archive (built with cmake) | FLOATING | sha256 `974d6b2f...ae17` | Apache-2.0 (tarball read) | n/a | build tool (meson) | `build-ninja.sh:41`; `build.sh:286` |
| meson (tool) | `pip install meson` (latest) in `python3 -m virtualenv` | FLOATING | **edit + workflow**: meson 1.11.2 wheel `--require-hashes` sha256 `7e4f6e83...a39` in a venv of `/usr/bin/python3` (1.12.x needs Python >= 3.10; the Xcode python3 is 3.9) | Apache-2.0 | n/a | build tool (harfbuzz) | `functions.sh:51-66` |
| Apple clang (toolchain) | the runner's Xcode 26.6 (17F113), Clang 21.0.0, SDK 26.x | FLOATING with the image (recorded per run in `build/toolchain.txt`) | `MACOSX_DEPLOYMENT_TARGET=14.0` (= PySide6 6.12 / shiboken6 wheel floor `macosx_14_0`; <= the owner's 26.3.1) | Apple Xcode terms (not distributed); compiled-in compiler-rt builtins and libc++ header code: Apache-2.0 WITH LLVM-exception (part 3 toolchain census) | yes (LLVM-exception) | static builtins only | - |
| macOS system libraries / frameworks | SDK (`/usr/lib`, `/System/Library`; VideoToolbox, CoreMedia, CoreVideo, CoreFoundation, AudioToolbox, AVFoundation, Security, libc++, libiconv, libbz2 ...) | system | the `otool -L` allowlist | system libraries, not distributed | n/a | dynamic | - |
| Rust / cargo | for rav1e only | - | NOT USED (rav1e skipped) | - | - | - | `build-rav1e.sh:51` |
| Riedl build script | vendored | - | `f63b8aab` + 5 edits in 4 files | Apache-2.0 (`LICENSE`) | n/a (not in the binary) | - | - |

Skips (all are the script's own switches, `build.sh:47-165`; each component's script is NOT
vendored, so a lost switch fails loudly):

- `-SKIP_ZVBI=YES`: GPL-2.0-only (AD-38 (10)); owner-ruled.
- `-SKIP_DECKLINK=YES`: nonfree (`build.sh:638`); already the default (`build.sh:43`), passed so a default change cannot enable it.
- `-SKIP_LIBKLVANC=YES`, `-SKIP_ZIMG=YES`: their scripts run `./autogen.sh` (`build-libklvanc.sh:51`, `build-zimg.sh:51`), which needs autoconf / automake / libtool, absent from the image: a CERTAIN runner failure. libklvanc only serves DeckLink; zscale is unused.
- `-SKIP_RAV1E=YES`: `cargo cinstall` needs cargo-c (absent from the image) and brings the Rust std + crate graph into the census (223 crate rows on Windows); AV1 encode unused.
- `-SKIP_SRT=YES`: MPL-2.0 is not in AD-38 (16)'s component compatible constant as written (UNSETTLED there); a network protocol Clearwater does not use.
- `-SKIP_LIBBLURAY`, `SNAPPY`, `LIBVMAF`, `AOM`, `DAV1D`, `OPEN_H264`, `OPEN_JPEG`, `SVT_AV1`, `LIBTHEORA`, `VPX`, `VVENC`, `LIBWEBP`, `LAME`, `OPUS`, `LIBVORBIS` `=YES`: unused by Clearwater (product: `libx265`, `hevc_videotoolbox`, native decoders, `-c:a copy`, `io/video/encode.py:515-531`, `decode.py:251`; tests: `libx264`, `libx265`, the native `aac` / `pcm_s16le` / `png` / `ffv1` encoders and `lavfi`, 0 uses of the others outside notices tests). Each kept one would be a pin, a texts row in part 3, and one more compile on an untested toolchain; dav1d / svt-av1 come from GitLab-generated archives whose bytes GitLab may regenerate (a sha256 mismatch = a second commit).
- KEPT: x264 (`-SKIP_X264=NO`: the tests make H.264 fixtures with it), x265 with multibit (Main10).

Summary: **18 components** (13 built: FFmpeg + 12 libraries, 11 of them linked, libogg built not
linked; 5 build tools: nasm, pkg-config, cmake, ninja, meson) + the toolchain and system rows;
**0 pinned as the script stands** (every tarball was fetched without a checksum, x264 from a branch,
meson from latest); **18 pinned by the recipe's edits** (15 tarballs by sha256 incl. cmake's and
x265's, FFmpeg and x264 by 40-hex commit, meson by wheel hash); **0 licence unsettled for a linked
component** (SRT's MPL-2.0 is avoided by the skip); no GPL-2.0-only component (zvbi skipped and not
vendored). Licence basis for THIS pin = the cell's read; the seat census is part 3.

### 4a.3 The recipe (fork branch `wp6.5-macos`, ONE commit on `d77b8352`)

Cell commit `a8d20eb4569fb8d3d5baf8b496a3d04c9eea8dd6` (tree `077bb2eaafaa5f4468d1a1b8bdfcdfe4cb731dc8`;
37 files, all ADDED: `macos/build-script/` 34 files, `macos/sha256-pins.txt`,
`macos/meson-requirements.txt`, `.github/workflows/build-macos.yml`; nothing else in the fork
changes). The 30 unedited vendored files are blob- and mode-identical to `f63b8aab` (19 scripts
100755); exactly four files differ. Edits (each in the commit message with its reason):

1. `script/functions.sh` `download()`: sha256 looked up by exact URL in `macos/sha256-pins.txt`; a missing pin or a mismatch `exit 1` (no mirror fallback on a mismatch); a curl failure still returns non-zero so the script's own mirror path runs (and is pinned too).
2. `script/functions.sh` `prepareMeson()`: requires the workflow's meson on PATH instead of `pip install meson` in a virtualenv.
3. `script/build-ffmpeg.sh`: FFmpeg by `git clone --filter=blob:none --branch=release/9.0` + `git checkout --detach b204e94e...` (the WP6.3c form; `checkStatus` fails the build if absent); `-FFMPEG_SNAPSHOT` other than NO refused; `--extra-version` = `date -u +%Y%m%d` (Windows form) instead of the provider URL. `version/ffmpeg` not vendored.
4. `script/build-x264.sh`: git clone + `checkout --detach 0480cb05...`.
5. `script/build-x265.sh`: the uploaded release file `downloads/x265_4.2.tar.gz`: same tree as the generated `get/4.2.tar.gz` except `x265Version.txt`, which in the generated archive reads `releasetag: 4.0` / `repositorychangeset: 6318f22` (`x265cmp\`, `diff -rq`), and x265's `source/cmake/Version.cmake:51-122` reads that file when the tree is not a git checkout: the library would report 4.0.

The workflow `.github/workflows/build-macos.yml`: `workflow_dispatch` only; `permissions: {}` at the
top; both jobs `if: github.repository == 'rwsmythe/FFmpeg-Builds'`; actions pinned to 40-hex (checkout
`11bd7190...` v4.2.2, upload-artifact `ea165f8d...` v4.6.2, download-artifact `d3f86a10...` v4.3.0,
each verified to be the tag's commit via `gh api .../git/ref/tags/...`; the same pins Clearwater's
workflows carry). **Not inherited:** `build.yml`'s floating `actions/checkout@v7`,
`upload-artifact@v7`, `download-artifact@v8`, `cache@v6`, `docker/*@v4/v7` (AD-38 (15)) stay in
`build.yml` only. Job `build` (`macos-26`, `contents: read`, `timeout-minutes: 150`): record the runner
(sw_vers, image, Xcode, SDK, clang) and check every tool the build uses exists on the sanitized PATH,
`build-zvbi.sh` absent, pins unique; meson 1.11.2 by hash into a venv of `/usr/bin/python3`; the build
under `env -i` (PATH = meson venv + `/usr/bin:/bin:/usr/sbin:/sbin`, HOME, TMPDIR,
`MACOSX_DEPLOYMENT_TARGET=14.0`, nothing else) with the 27 switches; on failure the last 80 lines of
every component log; the logs as an artifact (`always()`); CHECKS that fail the run: the FFmpeg and
x264 clones are at the pinned commits; `skip-*` markers (zvbi, decklink, libklvanc, rav1e, srt = YES;
x264, x265, openssl = NO); per `ffmpeg` / `ffprobe`: executable, `lipo -archs` = `arm64`, `file` =
`Mach-O 64-bit executable arm64`, `LC_BUILD_VERSION minos` = 14.0, `otool -L` entries ONLY under
`/usr/lib/` or `/System/Library/` (the backstop); `-version` token fullmatch
`^n9\.0\.2-47-gb204e94e[0-9a-f]*-[0-9]{8}$`, ffprobe's token equal; the configure line carries
`--enable-gpl --enable-version3 --enable-libx265 --enable-libx264 --enable-openssl
--extra-version=<the token's date>` and none of `--enable-nonfree`, `libfdk`, `--enable-libzvbi`,
`--enable-decklink`; encoders `libx265`, `hevc_videotoolbox`, `libx264`, `aac`; decoders `hevc`,
`h264`, `aac`. Package: ONE zip `ffmpeg-<describe>-macos-arm64-gpl-9.0.zip` (expected
`ffmpeg-n9.0.2-47-gb204e94e90-macos-arm64-gpl-9.0.zip`, root folder = name minus `.zip` as Windows)
holding `bin/ffmpeg`, `bin/ffprobe`, `LICENSE.txt` (FFmpeg's `COPYING.GPLv3`, as BtbN's 35,147-byte
LICENSE.txt), `build/` (`FFmpeg-LICENSE.md`, versions, `-version` both tools, encoders, decoders,
dylib lists, `toolchain.txt`, the pins, `logs/`), `zip -X -r -9`; `checksums.sha256` (shasum form).
Job `publish_release` (`ubuntu-24.04`, `contents: write`, needs build): re-verify the sha256, refuse
an existing tag, `gh release create ffmpeg-9.0-gb204e94e-macos-arm64-nozvbi-<GITHUB_SHA:0:7>
--target $GITHUB_SHA --latest=false` with the zip + `checksums.sha256`, then FAIL unless the tag ref
= `GITHUB_SHA` (F3 form) and the GitHub asset digest = `sha256:<computed>` (retried 6 x 10 s).

**Homebrew isolation:** `env -i` keeps `/opt/homebrew` and `/usr/local` off PATH (so no Homebrew
`pkgconf`, `libpng-config` and the like, which freetype's configure would otherwise find), and drops
`PKG_CONFIG_*`, `CPATH`, `LIBRARY_PATH`, `*FLAGS`, `HOMEBREW_*`; the script's own pkg-config searches
only `$TOOL_DIR/lib/pkgconfig` (`build-pkg-config.sh:98`); Apple clang does not search
`/opt/homebrew` by default. RESIDUAL: CMake 4.0.3's `Modules/Platform/Darwin.cmake:251-270` prepends
`/opt/homebrew` to `CMAKE_SYSTEM_PREFIX_PATH` on arm64 even without `brew` on PATH, and no
environment variable disables it (the 4.0.3 `Help/envvar` list); CMake builds only ninja and x265,
whose macOS finds are NUMA (Linux-only), `rt` / `dl` and an unused VMAF lookup
(`source/CMakeLists.txt:144-177`). The `otool -L` check is the backstop.

**VideoToolbox:** FFmpeg's configure AUTODETECTS it on darwin (`configure:2180`
`HWACCEL_AUTODETECT_LIBRARY_LIST`, `:7115` `check_apple_framework VideoToolbox`, encoder deps
`:3812-3813`, `:3905`); the Riedl configure line passes no VideoToolbox flag (`build-ffmpeg.sh:67-68`);
the provider's own build lists `hevc_videotoolbox` (`riedl-site\codecs.txt:101`). The encoder check
makes a silent loss loud.

**Patch:** `git format-patch -1 --stdout --base=d77b8352...` -> `tools/package/ffmpeg-fork-macos.patch`,
**108,053 bytes, sha256 `9f334458d2eccc52ada5e0c429f1b303f8b89d18c620ea8d094039a25f353e30`**, 0 CR,
`base-commit: d77b8352f60bd180ebce585632846533aa60b183` trailer. **Applies:** on a second fresh clone
at `d77b8352` (`FFmpeg-Builds-applycheck\`), `git apply --check` OK and `git am --3way
--committer-date-is-author-date` OK: tree `077bb2ea...` = the cell's tree, 19 files 100755. The
commit sha depends on the committer identity and date (the cell's is `a8d20eb4`).

### 4a.4 Static checks (here, no downloaded binary)

- YAML parse (PyYAML `safe_load`): OK; jobs `build` (`contents: read`, `macos-26`, 150 min) and
  `publish_release` (`contents: write`, `ubuntu-24.04`, 20 min); top `permissions: {}`; trigger
  `workflow_dispatch` only; 4 `uses:`, all 40-hex.
- `bash -n` (parse only) on the 7 run blocks and `bash --posix -n` on the four edited scripts: OK.
- `static\check_pins.py` (reads the vendored tree as text): every `download` URL the vendored
  scripts can request on darwin resolves (with `$VERSION` / cmake's `VERSION_*` / libxml2's
  `VERSION_WITHOUT_PATCH`) to exactly one pin: 18 of 18, every pin requested, the 7 msys-only
  pkg-config patch URLs excluded (`build-pkg-config.sh:52-89`, `uname -o` = Msys only); all 27
  switches the workflow passes are parsed exactly once in `build.sh` (`:47-165`); every
  `build.sh` call to a non-vendored script sits under a `SKIP_*` the workflow sets YES. NO PROBLEMS.
- Release tag and asset name are deterministic from the run: `GITHUB_SHA:0:7` and the built
  `-version` describe token (the date only in `--extra-version`, as Windows).
- Found and fixed in the loop: two `pipefail` SIGPIPE hazards in the workflow (`awk ... exit` after
  `otool -l`, `cmake --version | head -n 1`); both now read to the end.

### 4a.5 What only the fork run proves; budget; the most likely failure

Runner-only: every compile on Xcode 26.6 / clang 21 (the script's macOS path is proven only on Apple
clang 14); the meson venv on the Xcode python3; the sanitized PATH being sufficient (checked first,
in the record step); the deployment target taking in every component (minos check); the otool
backstop; the encoder / decoder lists incl. `hevc_videotoolbox`; the zip, its digest three ways
(computed, re-verified in the publish job, GitHub's asset digest) and the tag at the head.
**Budget:** about 45-75 min on the 3-vCPU M1 arm64 runner (by component: openssl and the three x265
depths are the largest C/C++ builds after FFmpeg's own ~10-15 min at `-j 3`; cmake is a binary
download; no Rust); `timeout-minutes: 150` (2x the high end). **Most likely failure:** a compile error
in an OLD component under clang 21, first suspect pkg-config 0.29.2's bundled 2017 glib (the script
already carries the Dec 2024 `-Wno-int-conversion` fix, `build-pkg-config.sh:93-95`, `8509c03`
"fix: pkg-config build on latest macOS"); the fix would be one more `CFLAGS` term in that script (or
the build's pkg-config replaced) = a second fork commit = a new owner word. The log tail step prints
the error in the job log, so diagnosis needs no second run.

### 4a.6 Verification loop (self)

- Suspected: the binaries would carry the runner's macOS (26.6+) as `minos` and refuse to start on
  the owner's 26.3.1. CONFIRMED by reading (no deployment target anywhere in the script); FIXED by
  `MACOSX_DEPLOYMENT_TARGET=14.0` (clang and CMake read it) plus the minos check.
- Suspected: harfbuzz would find no meson (`prepareMeson` needs `virtualenv` or a meson on PATH; the
  image has neither). CONFIRMED (readme); FIXED (edit 2 + the hashed meson).
- Suspected: zimg / libklvanc need autotools. CONFIRMED (`./autogen.sh` in both; 0 autotools in the
  image); avoided by the skips.
- Suspected: the x265 generated archive reports the wrong version. CONFIRMED (`diff -rq`,
  `Version.cmake`); FIXED (edit 5).
- Suspected: freetype's configure finds Homebrew libpng via `libpng-config` on PATH. Plausible by
  reading (not confirmed: depends on the image's packages); PREVENTED by `env -i`.
- Suspected: SIGPIPE under `pipefail` in the check steps. CONFIRMED by reading; FIXED.
- Suspected: the vendored files lost their exec bits on Windows. CHECKED: `update-index --chmod=+x`
  from the upstream modes; the patch carries `new file mode 100755` and the apply clone has 19.
- Rejected as false positive: a lost `-SKIP_ZVBI` silently building zvbi (its script is not vendored,
  so `build.sh:424` would fail `checkStatus`).
- A final pass found nothing new.

### Findings for the dispatcher (4a)

- **G2a-F1 (seat edit, not owned):** `.gitattributes` has `tools/package/ffmpeg-fork.patch -text`
  but nothing for `ffmpeg-fork-macos.patch`; on a checkout with `core.autocrlf=true` (this
  machine's system setting) the working copy turns CRLF. Add the same `-text` line.
- **G2a-F2 (ruling):** the skip set goes beyond the owner's "-SKIP_ZVBI=YES" (the dispatch invited
  proposals). To restore any component: drop its switch, vendor its script and version file, add
  its pin; the cell regenerates the patch (before the fork commit, no owner word needed).
- **G2a-F3 (owner acts, the WP6.3c form):** push `wp6.5-macos`; set it as the fork's default branch
  (a `workflow_dispatch` workflow must exist on the default branch; `build.yml` and the Windows
  recipe are on it unchanged); `gh workflow run build-macos.yml -R rwsmythe/FFmpeg-Builds --ref
  wp6.5-macos` (no inputs: a successful run always publishes).
- **G2a-F4 (part 2):** the zip stores 0755 for the tools, but Python's `zipfile` extraction drops
  modes; `bundle_ffmpeg`'s darwin path must set the execute bits (the darwin exec-bit ruling).
- **G2a-F5 (part 3):** census items new to macOS: compiler-rt builtins / libc++ header code
  (Apache-2.0 WITH LLVM-exception), SDL2 inside ffmpeg (libavdevice sdl2 outdev), libogg built but not
  linked, the deployment target 14.0 and the image version as lock / provenance fields.

Slips this turn (disclosed): two Bash calls early in the turn carried a bare `cd` (`cd <worktree>
2>/dev/null; true` and `cd /c && true`); no file was written by them; every later call used
absolute paths. One read-only Bash call (the upstream digest cross-check) passed the tool's
120 s default and was moved to the background by the tool; it completed (exit 0) and its
output file was read.

Depth at group-2a part-1 yield: 302,932 (wp65-cell4, read by the dispatcher with cell_depth.py at its 4a return)

## Group 2a part 2 (`wp65-cell5`, dispatch-5; base `1ef10536`)

Build turn 4b: the Clearwater side that consumes the fork's macOS asset, proved on Windows
without the asset. No review round yet (Reviewer A reads this head). Every item test-first;
the RED runs used the base `build.py` (`git archive 1ef10536`) loaded through the test
modules' own hooks or a repo-rooted copy under `work\` (deleted after). Nothing downloaded was
run; the only network reads were three FFmpeg source files at `b204e94e` as TEXT
(`fftools/opt_common.c`, `libavutil/utils.c`, `ffbuild/version.sh`, under
`work\wp6.5\g2a2\src\`) to confirm how the version and configuration are compiled in. Commits:
`51b7e76a` (items 1-2), `34c16c24` (item 3), `d23c2856` (item 4), `dd9c734a` (item 5 loop
fix), then this ledger; every committed blob 0 CR (byte count per file per commit).

### The lock shape (item 1) and why

A SECOND lock FILE `tools/package/ffmpeg-macos.lock.json` (the name G2b's switch reads),
validated by the SAME `validate_ffmpeg_lock` with a `platform` keyword (`"win32"` default,
`"darwin"`), the document's discriminator being `"platform": "macos-arm64"`. Against AD-38:
(2) one lock per provider asset, each recording provider, tag, URL, size, GitHub digest = seat
digest, the FFmpeg commit and the configure line verbatim with the MUST / MUST NOT rules; (11)
`ffmpeg_ref` + 40-hex `ffmpeg_commit`, `version` fullmatched against `-g<prefix>`, the date
bound to `--extra-version`; (12) the only bundling path `--ffmpeg-from <lock url>
--ffmpeg-sha256 <lock sha>` with the provenance fields cross-bound; (13) the census rows bound
to THIS asset. A row INSIDE the Windows lock was rejected: it would change the Windows
document's bytes and its validator's field set (the brief and the dispatch require both
unchanged) and would make every Windows reader carry a macOS asset; a second file keeps the
Windows lock byte-identical and lets each platform's bundling read only its own pin.

Fields (`build.py:919` `FFmpegMacLock`, 30): `schema_version` 2, `platform` `macos-arm64`,
`census` (`pending`), `provider` (pinned `rwsmythe/FFmpeg-Builds`), `build_script`
{`repository` pinned `https://git.martin-riedl.de/ffmpeg/build-script.git`, `commit` 40-hex},
`release_tag` (fullmatch `ffmpeg-9.0-g<commit8>-macos-arm64-nozvbi-<build7>`),
`build_repository_commit`, `build_run_url` (`https://github.com/<provider>/actions/runs/<n>`),
`asset_name` (= `archive_root.zip`), `asset_url` (= the release download form, exact),
`size_bytes`, `github_sha256` = `seat_sha256`, `ffmpeg_ref` `release/9.0`, `ffmpeg_commit`,
`ffmpeg_repository` (the recipe's `https://github.com/FFmpeg/FFmpeg.git`), `version` (F3b),
`configure_line`, `licence` `GPL-3.0-or-later`, `archive_root` (= `ffmpeg-<version minus
date>-macos-arm64-gpl-9.0`, so a Windows-shaped root, name or URL can never pass),
`extract_members` `[bin/ffmpeg, bin/ffprobe, LICENSE.txt]`, `source_record_url` (= the tree at
the build commit, the Windows form), `retention_note`, `macos_deployment_target` `14.0`,
`runner_label` `macos-26`, `runner_image_version` (`\d{8}\.\d+\.\d+`), `components` [],
`excluded` (rows {stage `SKIP_<NAME>`, status `not-built(disabled)`, reason}; `SKIP_ZVBI` and
`SKIP_DECKLINK` required), `toolchain` null, `toolchain_runtime` [].

**Reading disclosed (not a STOP):** the dispatch lists "`source_record_url` (the run)". The
Windows `source_record_url` is the recipe tree at the build commit (the per-component source
recipes, AD-38 (12)); the macOS lock keeps that meaning AND adds `build_run_url` for the run,
both bound to the provider. **Census form chosen:** `census: "pending"` requires `components`,
`toolchain_runtime` EMPTY and `toolchain` null; `"complete"` is REFUSED this turn ("the macOS
census rules are WP6.5 part 3's"), so no half-defined census rule ships; part 3 writes the
complete-census rules with the real rows. `build()` on darwin refuses `--notices` / `--zip`
while the census is pending (`build.py:4242`).

### Items

1. **The lock and its validator (`51b7e76a`).** `build.py:912` `FFmpegBuildScript`, `:919`
   `FFmpegMacLock`, `:964` `FFMPEG_MACOS_LOCK_PATH` and the pinned constants, `:1435`
   `_macos_configure_problem` (printed prefix; MUST `--enable-gpl`, `--enable-version3`,
   `--enable-libx265`; MUST NOT `--enable-nonfree`, any `libfdk` token, `--enable-libzvbi`,
   `--enable-decklink`; exactly one `--extra-version` = the version's date), `:1453`
   `_validate_macos_ffmpeg_lock`, `:1572-1598` `validate_ffmpeg_lock` overloads + the
   discriminator at `:1636` (darwin: `platform` must read `macos-arm64`; win32: a document
   carrying `platform` is refused "is not the Windows lock"; any other platform refused; the
   Windows body after it is unchanged), `:1824` `load_macos_ffmpeg_lock`. The synthetic fixture
   `tests/ffmpeg_lock/ffmpeg-macos.fixture.json` (census pending; fork commit `deadbeef...`,
   sha `0`x64, run id `40000000001`; `retention_note` says SYNTHETIC). The real lock is NOT
   created. Tests `tests/test_tools_package_build.py:3111-3330`: the fixture passes and its
   field set = `FFmpegMacLock`; its 21 excluded stages = the patch's `-SKIP_*=YES` switches
   minus `SKIP_TEST` / `SKIP_BUNDLE`; each MUST / MUST NOT in turn (9) + prefix / no date; a
   Windows-shaped asset 4 ways (URL only, root+name+URL, the Windows lock's URL, the Windows
   tag); 25 provenance mutations (schema, provider, size, digests, commits, ref, repository,
   major, licence, `.exe` members, source record, run URL x2, deployment target, runner label,
   image version, retention note, census complete / unknown, non-empty census lists, toolchain,
   build_script fields); the build script pin (2); excluded rows (7); exact field set (2); the
   discriminator both ways + Linux; the loader reads its own file and refuses the Windows lock.
   RED (base `build.py`): 51 `validate_ffmpeg_lock() got an unexpected keyword argument
   'platform'` + 27 `no attribute 'FFMPEG_MACOS_LOCK_PATH'`; the excluded-rows data test
   passes on both. GREEN.
2. **`bundle_ffmpeg`'s darwin path (`51b7e76a`).** `build.py:2159` `bundle_ffmpeg(...,
   platform="win32")`: `:2197` darwin -> `:2055` `_bundle_macos_ffmpeg`; any other platform
   refused; the Windows body unchanged. The darwin order: the macOS lock; the destination must
   be `Contents/MacOS` of a `.app` and none of the four targets may exist (BEFORE any
   download); `_download_ffmpeg` (URL = lock, sha = lock, size bound, digest verified before
   the archive is opened); `_ffmpeg_archive_members` (every member inspected: unsafe names,
   links, duplicates; `bin/ffmpeg`, `bin/ffprobe`, `LICENSE.txt` required); staged under
   `<out>/ffmpeg/<archive_root>.verified` with chmod 0755 on the two tools, 0644 on the texts
   (G2a-F4); each tool `:2008` `_macos_tool_problem` (thin 64-bit Mach-O, CPU arm64,
   MH_EXECUTE; FAT, x86_64, dylib, PE refused) and `:2018` `_macos_ffmpeg_version`; the
   `ffmpeg-BUILD.txt` record (provider, build script @ commit, tag, asset, sha, version, commit,
   ref, build commit, run, source recipes, the macOS lock path, deployment target, runner,
   configure line); then `place_macos_tools` (tools to `Contents/MacOS` 0755, texts to
   `Contents/Resources` 0644) and `verified_hashes` updated only after all of it. **Version
   check, said as asked:** Windows RUNS `ffmpeg.exe -version` (bounded, PATH = its folder,
   `_pinned_ffmpeg_version`) and byte-reads only the GCC / rustc toolchain markers; the darwin
   path never runs the tool: it reads `FFMPEG_VERSION` and `FFMPEG_CONFIGURATION` from the
   bytes (both are standalone C strings: `opt_common.c:204` prints `"%s version %s"` with
   `FFMPEG_VERSION`, `:211` `"%sconfiguration: %s\n"` with `FFMPEG_CONFIGURATION`), requiring
   exactly ONE version token (`n9.x.y-n-g<hex>-<8 digits>`, NUL-terminated, not glued to a
   token character) equal to the lock's and the configure body as a NUL-terminated string not
   preceded by a printable byte; 1 MiB blocks with an overlap, a match at a carried-over first
   byte judged only in its earlier block. The smoke runs `-version` on the runner (item 3).
   **The Apple toolchain marker check** (the Windows `_check_ffmpeg_toolchain_markers`)
   needs the census: declared part 3 in `_bundle_macos_ffmpeg`'s docstring. `build()`
   (`:4291`) passes `platform="darwin"` through `functools.partial` on darwin only (the
   Windows call keeps its exact keywords: an existing stub test has no `platform`
   parameter). Tests `test_tools_package_build.py:3334-3690` with a synthetic fork zip and fake
   Mach-O heads (`subprocess.run` / `Popen` patched to FAIL, so nothing is ever run):
   placement, bytes, texts, record fields, archive kept, modes (POSIX hosts); the chmod spy
   (0755 on exactly ffmpeg / ffprobe, staged + placed, everything else 0644); verify before
   open x3 (nothing staged or placed); unsafe members x4; zip symlink; Windows tool names; 10
   per-tool refusals (x86_64, dylib, fat, PE, wrong / second / absent / glued version token,
   configuration, prefixed configuration; nothing placed, no trusted hash); strings across
   the 1 MiB boundary; destination outside an `.app` refused before download; the other
   platform's lock refused by both bundling paths and Linux refused; an existing tool in the
   `.app` refused before anything is placed; `build()` on darwin uses the macOS lock and the
   darwin path and refuses `--notices` / `--zip` while the census is pending, and a sha other
   than the lock's. RED: as item 1 (same run). GREEN 85 in the selection.
3. **The darwin smoke run path (`34c16c24`, G1-F4).** `smoke.py:1095` `run_smoke`: win32
   unchanged, darwin -> `:1003` `_run_macos_smoke`, any other host refused by name. The
   darwin path: the executable `Clearwater.app/Contents/MacOS/Clearwater` (a release folder or
   `Contents/MacOS` accepted, a onedir or a bundle without `Contents/Frameworks` refused);
   smoke root disjoint from the bundle; `:967` `_macos_static_checks` (forbidden paths on the
   bundle, forbidden entries, hidden imports with NO pack scan as `build()` on darwin, notices
   read from `Contents/Resources/THIRD_PARTY_NOTICES.md` against `plan_notices` of the
   executable folder); the 10 refusal + 2 worker rows, each through `_process` ->
   `_contained_process` (G1's process-group containment and `killpg` census); the planted
   exception: exactly one regular `Contents/Frameworks/scipy/_lib/_ccallback_c*.so`, never
   reached through a link (checked on the shipping bundle and again in the copy), removed from
   a COPY (`copytree(symlinks=True)`), the copy's `Contents/MacOS/Clearwater --export-worker`
   expected to exit non-zero with the one stderr line naming `:961` `_macos_log_file` (= HOME
   `/Library/Application Support/Clearwater/logs/clearwater.log`), the log holding one
   traceback naming `_ccallback_c`; `:840` `_ffmpeg_checks`: darwin REQUIRES both tools in
   `Contents/MacOS` (regular files; fail-closed, no SKIP), reads the macOS lock, runs
   `ffmpeg` / `ffprobe -version` (version + configure line) and `ffmpeg -hide_banner -encoders`
   expecting `:833` `_SMOKE_ENCODERS["darwin"]` = (`hevc_videotoolbox`, `libx265`); the Windows
   message, PASS line, SKIP-when-absent rule and `load_ffmpeg_lock()` call are unchanged.
   Tests `test_tools_package_smoke.py:999-1280` (a darwin `.app` fixture under a monkeypatched
   `sys.platform`, `_contained_process` replaced by a bounded child running a Python stub):
   the complete run (rows and their order, executables, the planted copy, the FFmpeg rows in
   `Contents/MacOS`, PATH `/usr/bin` + `/bin`, every root under `out/smoke`, the log location,
   shipping bytes unchanged, the PASS lines incl. `(hevc_videotoolbox; libx265)`); the log
   path equals `config.paths.app_locations(platform="darwin", home=...)`; the encoder rows
   equal `capability.encoder_roster(platform)` for win32 and darwin; 5 row failures by name
   (version, configure, no VideoToolbox, the WINDOWS roster on darwin, no log); 11 fail-closed
   inputs (no ffmpeg, no ffprobe, `.exe` tools, no `.so` (the shipping worker rows fail
   first), two `.so`, `.pyd` only, no notices, notices in `Contents/MacOS`, stale notices, no
   Frameworks, a onedir); the link refusal; Linux refused. RED: 19 "platform: smoke requires
   the Windows onedir artifact" + 2 `_SMOKE_ENCODERS` absent + 1 Linux message. GREEN 22.
4. **The switch's lock fields (`d23c2856`).** The step already reads `asset_url` and
   `seat_sha256` from `tools/package/ffmpeg-macos.lock.json`, the fields of item 1's shape: no
   rename. `.github/workflows/macos-build.yml:29-34` the env comment now names part 3;
   `MACOS_FFMPEG_BUNDLED: "false"` kept (`:35`). Test `tests/test_release_workflow.py:1124`:
   the step's lock path = `build.FFMPEG_MACOS_LOCK_PATH`; the two fields read, in order, are
   `FFmpegMacLock` fields and fixture keys; the build line passes them as `--ffmpeg-from` /
   `--ffmpeg-sha256`; the fixture's values are not in the workflow; the switch is exactly
   `"false"` and no real lock exists (part 3 changes both together). RED: on the base
   `build.py` (a copy of the module beside it under `work\wp6.5\g2a2\wfred\`): `no attribute
   'FFMPEG_MACOS_LOCK_PATH'`. GREEN. `release.yml` untouched (the windows job's sha pins pass).
5. **Verification loop:** below.

### Proof the Windows lock / bundling verdicts are unchanged

- `tools/package/ffmpeg.lock.json`: not touched (no diff from `1ef10536`).
- `tests/test_tools_package_ffmpeg.py` (unmodified; the Windows lock validator and bundling):
  run against the BASE `build.py` (the module copied beside a `git archive 1ef10536
  tools/package`) and against the new one: 290 passed / 290 passed, the sorted node-id +
  outcome lists identical (sha256 `2eb4eed8d476ccc8...` both).
- `tests/test_tools_package_build.py`, the 275 pre-existing ids (no existing test edited; the
  module only grew): new 275 passed; base (`WP61_BUILD_SCRIPT` = the base `build.py` copied
  to `work\pkgbase\`, so its `REPO_ROOT` is the worktree) 275 passed; outcome maps identical
  (`31abdd2acc190b86` both). (A first base copy under `work\wp6.5\g2a2\base\` failed 35
  build()-calling ids environmentally, its `REPO_ROOT` being `work\`: discarded.)
- `tests/test_tools_package_smoke.py`: no line removed from the module; the 44 + 1 pre-existing
  ids pass / skip as before (66 passed, 1 skipped in all).
- Darwin SIMULATION (a scratch plugin sets `sys.platform = "darwin"` after collection; not a
  proof): the build module's 255 pre-existing non-space ids have IDENTICAL outcomes on base and
  new (56 fail on both: simulation artifacts or G3 runner items, unchanged by this turn); the
  2 new ids failing there are simulation artifacts (Windows file modes read as 0666; PyInstaller
  reads `platform.mac_ver()` at import; the plugin's PYTHONPATH trips the build guard).

### Counts at the group-2a part-2 head (`-p no:cacheprovider --timeout 600 --basetemp=work\wp6.5\g2a2\<module> -k 'not test_python_m_clearwater_starts_the_shell_and_exits_0'`)

Static: `ruff check .` All checks passed; `ruff format --check .` 337 files already
formatted; `mypy` Success 166; `mypy --platform darwin` Success 166.

| Module | Result |
|---|---|
| `tests/test_tools_package_build.py` | 355 passed (group 2b: 275; +80) |
| `tests/test_tools_package_ffmpeg.py` | 290 passed (unchanged module; identical to base) |
| `tests/test_tools_package_smoke.py` | 66 passed, 1 skipped (group 2b: 44 + 1; +22; the skip is the non-Windows tripwire) |
| `tests/test_release_workflow.py` | 79 passed (group 2b: 78; +1) |
| `tests/test_tools_package_notices.py` | 415 passed (`-n 3`, as group 2b, to fit the tool call; module and `notices.py` untouched) |
| `tests/test_portability.py` | 192 passed |
| `tests/test_macos_portability.py` | 224 skipped (`macos` platform skip) |

### Verification loop (self)

- Suspected: `"--enable-nonfree"` read as a REMOVAL by the test helper (prefix `-`).
  CONFIRMED (6 must-not ids did not raise); FIXED in the test (`---` marks removal).
- Suspected: the prefixed-configuration probe also erased the version's NUL. CONFIRMED
  ("version token(s) []"); FIXED in the test (the probe keeps the terminator).
- Suspected: the `fftools` print concatenates the version / configuration into its format
  literal, so a NUL-delimited read would miss them. REJECTED by reading the source at
  `b204e94e` (`opt_common.c:204`, `:211`: both passed as `%s` arguments); the `"FFmpeg version
  " FFMPEG_VERSION` arrays (space before the token) also satisfy the token rule.
- Suspected: Python's lookbehind cannot see bytes before `pos`, so the block-start rule would
  misjudge. REJECTED: `re.compile(rb'(?<![a-z])b').search(b'ab', 1)` is None.
- Suspected: a pre-existing Windows `build()` stub (`fetched(destination, *, out, url,
  sha256, verified_hashes)`) breaks if the call gains `platform=`. CONFIRMED by reading;
  AVOIDED: darwin only passes it (`functools.partial`).
- Suspected: the existing smoke fixture stubs `load_ffmpeg_lock` with a zero-argument lambda.
  CONFIRMED; AVOIDED: the Windows path keeps `load_ffmpeg_lock()`; darwin calls
  `load_macos_ffmpeg_lock()`.
- Suspected: a partial placement leaves `ffmpeg` in the `.app` when `ffprobe` already exists.
  CONFIRMED by design review (`place_macos_tools` is per file); FIXED: all four targets are
  checked before the download (test asserts nothing placed, nothing fetched).
- Suspected: the planted copy's unlink could follow a link into the shipping bundle.
  CONFIRMED possible in principle; FIXED: the target must be a regular file inside the bundle
  and its copy inside the copy (test with a link-reporting `.so`: refused, shipping file kept).
- Suspected: a `.so`-less shipping bundle reaches the planted row. REJECTED: its worker rows
  fail first (`worker-empty: exit 1`), which the test now records.
- Found: the module docstring and `smoke_artifact`'s argument named only the Windows lock /
  onedir. FIXED `dd9c734a`.
- A final pass over items 1-4 found nothing new.

### What only the fork run and the runner prove

- **The fork run (seat):** the real asset's name, size, three-way digest, tag at the run's
  head (F3), the run URL, the image version, the configure line VERBATIM and the build date;
  that the real `ffmpeg` / `ffprobe` carry exactly one version token and the configure body
  as C strings (the rule is from the source, never tested on a real Mach-O here); thin arm64
  MH_EXECUTE; that `zip -X` gives no member the archive inspection refuses.
- **The runner (switch ON, part 3):** `bundle_ffmpeg` on darwin over the real download; the
  tools 0755 after a real extraction; the origin check admitting the two whole-file hashes in
  `Contents/MacOS`; the seal (`codesign --sign -` without `--deep`, then `--verify --deep
  --strict`) accepting the linker-signed tools as nested code, and the origin re-check after
  it; the darwin smoke natively: the rows under `killpg` containment, the planted copy
  starting from a bundle whose seal the removed `.so` breaks, the log under the redirected
  HOME, `-version` / `-encoders` listing `hevc_videotoolbox` and `libx265`; `--zip` keeping the
  execute bits.

### What part 3 must fill

1. `tools/package/ffmpeg-macos.lock.json` from the fork run (every field above; `census`
   then flips with the census rows).
2. The complete-census rules in `_validate_macos_ffmpeg_lock` (refused today): `components[]`
   (the Riedl components, Windows row shape, texts under a macOS texts folder), the
   `toolchain` object (Apple clang / SDK / deployment target bound to THIS asset) and
   `toolchain_runtime[]` (compiler-rt builtins, libc++ header code, G2a-F5), plus the two-way
   configure coverage.
3. The Apple toolchain marker byte-check in `_bundle_macos_ffmpeg` (the Windows
   `_check_ffmpeg_toolchain_markers` analogue), from the census.
4. The Mac notices (`notices.py` reading the macOS lock; written to
   `Contents/Resources/THIRD_PARTY_NOTICES.md`; confirm `plan_notices`' input is the
   executable folder, as `_macos_static_checks` assumes), then lift the `--notices` / `--zip`
   census refusal in `build()`.
5. `MACOS_FFMPEG_BUNDLED: "true"` and the pin test's `"false"` + no-lock assertions
   (`tests/test_release_workflow.py:1124`) flipped together.

### Findings for the dispatcher

- **G2a2-F1 (record):** the G2a-F2 skip set is mirrored in the fixture's `excluded` rows and
  bound to the patch by a test; if CHARC's concurrence changes the skips, the patch and the
  fixture change together (the test fails otherwise).
- **G2a2-F2 (record, runner):** `--smoke Clearwater.app` (the bundle folder itself) is not
  accepted: `find_executable` looks for `Clearwater.app/...` or `Clearwater` UNDER the folder
  given; the release folder or `Contents/MacOS` work (the build passes `Contents/MacOS`).
- Slip (disclosed): my second Bash call began with a bare `cd /dev/null 2>/dev/null;` (it
  failed, `/dev/null` not being a directory; no cwd change, nothing written); every later call
  used absolute paths or `--directory` / `git -C`. One heredoc collapsed `\\` (the known trap)
  and failed its own assertion before writing; the edits were redone with the Edit tool.

Depth at group-2a part-2 yield: 368,353 (wp65-cell5, read by the dispatcher with cell_depth.py at its 4b return)

## Group 2a part 2 r1 (`wp65-cell7`, dispatch-8; base `de3d68a0`)

Turn 4b-r1: fold Reviewer A r3 (Codex, FINDINGS: 3 major, 2 minor, all executed;
`clearwater-review-evidence\wp6.5\A\r3\review.txt`). Worktree head at the start `23e28fbe`
(`wp65-cell6`'s patch commit), `2be3d775` during the turn; this cell touched neither the
patch nor any file outside `tools/package/build.py`, `tests/test_tools_package_build.py`
and this ledger. Test-first: every new refusal test ran RED on the part-2 `build.py`
(unchanged in the worktree until the fold) before the fix: `work\wp6.5\g2a2r1\red.log`,
67 failed for the right reasons (65 `DID NOT RAISE`, 1 `no attribute
'FFMPEG_MACOS_EXCLUDED_STAGES'`, 1 `_macos_tool_problem() takes 1 positional argument`), then
GREEN. Network reads, as DATA only, nothing run: FFmpeg's source at `b204e94e` (codeload
tarball, `work\wp6.5\g2a2r1\src\`; `configure`, `ffbuild/version.sh`, every
`FFMPEG_VERSION` / `FFMPEG_CONFIGURATION` use) and the provider's own macOS arm64 FFmpeg
9.0.2 release zip (`ffmpeg.martin-riedl.de`, sha256 `c8ed4c4e...d924`, 28,395,699 bytes,
`work\wp6.5\g2a2r1\dl\`), whose `ffmpeg` bytes were passed to the new parsers (below).

### A r3 adjudication

| Finding | Verdict | Change (head `d81549fc`) | RED (part-2 code) | GREEN |
|---|---|---|---|---|
| A3-F1 MAJOR, tool check reads 32 bytes, no deployment target | FIXED | `build.py:2158` `_macos_tool_image` reads the header + the WHOLE declared table when `sizeofcmds` lies within the file and <= 1 MiB (`_MACOS_TOOL_COMMANDS_LIMIT`); `:2175` `_macos_tool_problem(image, deployment_target)`: magic / arm64 / MH_EXECUTE, then `_macho_parse` (the origin check's bounded parser: table inside the image, each `cmdsize` >= 8, a multiple of 8, inside the table, the commands filling it exactly; `ncmds` bounded by the table), then no `LC_VERSION_MIN_*` (0x24 / 0x25 / 0x2F / 0x30: REFUSED, the older form; the recipe's toolchain emits `LC_BUILD_VERSION`, and two deployment records could disagree), exactly ONE `LC_BUILD_VERSION`, `cmdsize` = 24 + 8 x `ntools`, platform 1 (macOS), `minos` EQUAL to the lock's `macos_deployment_target`; `:2365` the bundling call. **Equal, not at-most:** the recipe sets `MACOSX_DEPLOYMENT_TARGET=14.0` exactly and the fork run checks minos 14.0, so equality is the evidence that the binary is the recipe's build; a lower minos would also run on 26.3.1 but would contradict the lock's record. | 15 bundle mutations (minos 26 / 13 / 14.0.1, iOS platform, missing, duplicate, VERSION_MIN beside / alone, table truncated past the file, table shorter than its commands, table past the limit, unaligned / zero `cmdsize`, `ntools` mismatch, `ncmds` 0xFFFFFFFF): `DID NOT RAISE`; the unit test (the reviewer's two images + a 32-byte head): TypeError | `test_tools_package_build.py:3825` (15) + `:3464` (reviewer's minos 14 admitted, 26 refused, a 32-byte head refused); positive fixture `macho_image` `:3429` (header + `LC_UUID` + `LC_BUILD_VERSION` minos 14.0 with one ld entry, structurally valid) now in every bundle test |
| A3-F2 MAJOR, older versions invisible to the 9.x regex | FIXED | `build.py:2105` `_FFMPEG_VERSION_CANDIDATES`: DETECTION of every plausible FFMPEG_VERSION, any major, every `ffbuild/version.sh` form (read at `b204e94e`): bare C strings `n<maj>.<min>...`, `N-<n>-g<hash>...`, `git-YYYY-MM-DD-<hash>...`, a numeric RELEASE / VERSION ending in an 8-digit extra-version; and the `av_*_ffversion[] = "FFmpeg version " FFMPEG_VERSION` arrays (six `version.c`), matched anywhere with a version-shaped token; `:2219` `_scan_blocks` judges every start position in exactly one block with >= the longest match after it (no truncated candidate, no double count); `:2244` `_macos_ffmpeg_version` then refuses unless exactly ONE distinct candidate exists and it is the lock's token. | 6 tool mutations (the reviewer's `n8.0.1-...` + planted token, `FFmpeg version 8.0.1`, master `N-...`, shallow `git-...`, dated numeric, suffixed token) + 2 across the 1 MiB boundary: `DID NOT RAISE` (`other-banner` n9.0.1 was already refused by the 9.x regex) | `:3676` 8 new damages, `:3788` (2 needles x 3 split points), `:3751` banner of the locked token admitted |
| A3-F3 MAJOR, `--disable-libx265` accepted | FIXED | `build.py:1491` `_macos_configure_problem` (macOS only): configure's `for opt do` loop applies options left to right and `$action $option` lets the LAST enable / disable win, so a disable after the enable is effective; the rule refuses `--disable-gpl` / `--disable-version3` / `--disable-libx265` ANYWHERE (order-independent; the recipe line carries none) and every option that can switch the libx265 ENCODER off with the library on (`:1022` `_LIBX265_ENCODER_OFF`: `--disable-encoders`, `--disable-everything`, `--disable-all`, `--disable-avcodec`, `--enable-random`, `--disable-random[=...]`; `--disable-encoder=<patterns>` matched as configure's shell `case` patterns, items split on `,` and `|`). | 15 of the 16 mutations: `DID NOT RAISE` (`aac|libx265` added after the RED run) | `:3213` (16) + `:3229` admits `--disable-encoder=aac`, `--disable-libx264`, `--disable-doc` |
| A3-F4 MINOR, excluded set not bound | FIXED | `build.py:986` `FFMPEG_MACOS_EXCLUDED_STAGES` (21), `:1638` `stages` must EQUAL it (missing and unknown named). **A constant, not read from the patch at validation time:** the validator then needs nothing but the lock (no file I/O, the same verdict wherever the lock is checked) and the binding is a test that compares the VALIDATOR's set with the patch's `-SKIP_*=YES` less `SKIP_TEST` / `SKIP_BUNDLE`. | 19 single deletions (zvbi / DeckLink already refused) + invented row x3 forms: `DID NOT RAISE`; the binding test: `no attribute` | `:3133` (validator set = patch = fixture, 21), `:3142` (21 deletions), `:3151` (invented; zvbi + DeckLink only; both). Re-run after `2be3d775`: below |
| A3-F5 MINOR, member outside `archive_root` accepted | FIXED | `build.py:1959` `_macos_archive_members`: the shared `_ffmpeg_archive_members` (UNCHANGED, AST-identical) first, then every member, extracted or not, must start with `<archive_root>/`; `:2348` the darwin path's only inventory call. The reviewer's probe called the shared helper directly; the macOS rule lives in the macOS wrapper so the Windows helper stays byte-identical. | 4 (`outside-root/unrelated`, a top-level file, the root upper-cased, a file named exactly the root): `DID NOT RAISE` | `:3868` (4) + `:3880` the Windows inventory still ignores an outside member |

Counts: 3 major + 2 minor = 5, all in-envelope, all NEW, 0 reverts; product fixes 5 (`build.py`)
plus one found by the loop (below); tests-only change: one existing test's padding moved past
the load commands (`test_macos_bundle_reads_strings_across_the_read_boundary`, its 64-byte
insertion point now inside the valid table).

The reviewer's probe re-run at the head (`work\wp6.5\g2a2r1\ar3_probe.py`, F1 / F5 through the
head's entry points): F1 minos 14 None, minos 26 "minos 26.0 differs from the lock's deployment
target 14.0", 32 bytes only "malformed or truncated"; F2 REFUSED (`['n8.0.1-...',
'n9.0.2-47-...']`); F3 REFUSED; F4 two-only / two + invented / 21 + invented all REFUSED; F5
REFUSED.

### Real arm64 Mach-O read (data only)

The provider's own `ffmpeg` 9.0.2 macOS arm64 (66,332,880 bytes) through the head's parsers
(`work\wp6.5\g2a2r1\real_macho_probe.py`): load-command table 5,168 bytes parsed, one
`LC_BUILD_VERSION` (platform 1, minos 12.0, sdk 12.3, one tool); `_macos_tool_problem` None
against 12.0, refused against 14.0 / 13.0 / 11.0. Its first read FOUND TWO FALSE CANDIDATES in
my first cut: the version token `to` (libavutil's prose "Update your FFmpeg version to the
newest one from Git") and a component's own build configuration `--prefix=/Volumes/ffmpeg_arm64/tool
--disable-unit-tests` (libvpx's by its option, `vpx_codec_build_config`; libvpx is skipped in
the fork recipe). Fixed before the commit: the banner token must start as a version.sh form
does; a configuration candidate must carry an FFmpeg licence switch (`--enable-gpl` /
`version3` / `nonfree`) or be the lock's own line. Then end to end with the provider's own
token and configure line (`versions.txt`): ADMITTED (one version candidate `9.0.2-https://www.
martin-riedl.de`, one configuration), 3.6 s for 66 MB; with the fork's token: REFUSED naming
the provider's. Guard test `:3760` carries the three real strings (prose, libvpx's line, a
banner after printable data bytes).

### Proof the Windows verdicts are unchanged

`work\wp6.5\g2a2r1\windows_compare.py` (base `git show 1ef10536:tools/package/build.py` vs the
head, both loaded by path): **Windows validator comparisons: 33, mismatches: []** (the real
lock ACCEPTED by both; appended `--disable-libx265` / `-gpl` / `-version3` /
`--disable-encoder=libx265` / `--disable-everything` / `--enable-nonfree`; `--enable-gpl`
removed; an invented excluded row; each of the 24 fields missing); **archive-member
comparisons: 5, mismatches: []** (clean, outside-root, top-level, traversal, case-duplicate);
**Windows-path definitions AST-identical to `de3d68a0`: 10 of 10** (`validate_ffmpeg_lock`,
`load_ffmpeg_lock`, `_ffmpeg_archive_members`, `_download_ffmpeg`, `_pinned_ffmpeg_version`,
`_check_ffmpeg_toolchain_markers`, `bundle_ffmpeg`, `_ffmpeg_runtime`,
`_ffmpeg_component_texts`, `FFmpegLock`). `tests/test_tools_package_ffmpeg.py` 290 passed.

### Counts at the r1 head (`-p no:cacheprovider --timeout 600 --basetemp=work\wp6.5\g2a2r1\<module> -k 'not test_python_m_clearwater_starts_the_shell_and_exits_0'`)

Static: `ruff check .` All checks passed; `ruff format --check .` 337 files already formatted;
`mypy` Success 166; `mypy --platform darwin` Success 166.

| Module | Result |
|---|---|
| `tests/test_tools_package_build.py` | 432 passed (part 2: 355; +77) |
| `tests/test_tools_package_ffmpeg.py` | 290 passed (unchanged) |
| `tests/test_tools_package_smoke.py` | 66 passed, 1 skipped (unchanged; the skip is the non-Windows tripwire) |
| `tests/test_release_workflow.py` | 79 passed (unchanged) |
| `tests/test_tools_package_notices.py` | 415 passed (`-n 3`) |
| `tests/test_portability.py` | 192 passed |
| `tests/test_macos_portability.py` | 224 skipped (`macos` platform skip) |

### Verification loop (self)

- Suspected: a long or block-straddling candidate is seen truncated (a false conflict) or twice.
  CONFIRMED possible with an unbounded token and the old one-byte skip; FIXED by bounded
  candidate forms (longest 183 bytes, `_FFMPEG_CANDIDATE_SPAN` 256) and `_scan_blocks`' rule
  (a start is judged only with >= the overlap after it); tests at 3 split points.
- Suspected (class sweep, "filters before comparing"): the configuration check only looked
  for the lock's body, so a second FFmpeg configuration passed. CONFIRMED (the
  `second-configuration` mutation, RED on the part-2 code); FIXED: configuration candidates
  collected, exactly one, equal.
- Suspected: requiring the configuration to start with `--` refuses a legitimate line
  beginning `cc=clang` (configure's `*)` branch strips an optional `--`). CONFIRMED (RED on a
  copy without the exact-line candidate: "0 distinct configuration string(s)"); FIXED: the
  lock's own line is a candidate whatever its first byte (`:3775`).
- Suspected: real-binary false candidates. CONFIRMED twice on the provider's real arm64
  binary (above); FIXED. Source greps of FFmpeg at `b204e94e` and of the ten kept-component
  tarballs in `work\wp6.5\g2a\dl\` (fontconfig, freetype, fribidi, harfbuzz, libass, libxml2,
  openssl, SDL2, x265, zlib; x264's clone there holds no sources and libogg was not grepped)
  found no string literal of the bare forms and no `"--...enable-` / `disable-` literal; the
  only `FFmpeg version` literals are the six `version.c` arrays, but a line-based grep cannot
  see a phrase split across concatenated literals: libavutil's prose (`log.c:501-502`) was
  found only by the real binary, so the binary read, not the grep, is the evidence.
- Suspected (class sweep, "fixed small prefix"): `_macos_origin_identities`' 4-byte `head()`
  only CLASSIFIES (the whole file is then read). REJECTED. Smoke's darwin `-encoders` row
  accepts a superset by design (the roster is a lower bound); its `-version` rows compare the
  first line's third field and require exactly one configuration line. REJECTED.
- Suspected: `--disable-encoder=a|libx265` escapes a `,`-only split (configure builds a `case`
  alternation with `|`). CONFIRMED by reading `configure`; FIXED (split on both) + test.
- A final pass over F1-F5 and the loop items found nothing new.

### Limits stated

The configuration detector does not see a second FFmpeg configuration carrying none of the
licence switches and not starting with `--` (that build's own `FFmpeg version` arrays are
still candidates); a bare `x.y.z` FFmpeg version with no extra-version is seen only in the
`FFmpeg version` arrays (alone it cannot be told from another library's version string). The
real fork binary's strings are the fork run's proof (the first real read of OUR build).

### Findings for the dispatcher

- **G2a2r1-F1 (Windows, the same hole as A3-F3; NOT changed here):** the Windows validator
  ACCEPTS the real Windows lock with `--disable-libx265`, `--disable-gpl`,
  `--disable-version3`, `--disable-encoder=libx265`, `--disable-encoders` or
  `--disable-everything` appended (`work\wp6.5\g2a2r1\windows_hole.py`, 6 of 6 ACCEPTED):
  `build.py` Windows branch checks `--enable-*` membership only. A Windows fold changes a
  Windows verdict, so it is the dispatcher's / CHARC's call (a DR row or a later package).
- **G2a2r1-F2 (record):** the F4 constant and the patch move together; a recipe skip change
  fails `test_macos_lock_excluded_rows_are_exactly_the_recipe_skips` until both agree.

Slips: one Bash heredoc collapsed backslashes (the known trap) and failed its own assertion
before writing; the edits were redone with the Edit tool. One early Bash grep ran against
an empty path variable and so searched the shared cwd (read-only; nothing written).

Depth at group-2a part-2 r1 yield: 271,885 (wp65-cell7, read by the dispatcher with cell_depth.py at its 4b-r1 return)

## Group 2a part 2 r2 (`wp65-cell8`, dispatch-9; base `ae96a4e2`)

Turn 4b-r2: fold Reviewer A r4 (Codex, FINDINGS: 3 major, all executed;
`clearwater-review-evidence\wp6.5\A\r4\review.txt`), with the dispatcher's steer: CONSERVATIVE
REFUSAL over emulation. Only `tools/package/build.py`, `tests/test_tools_package_build.py` and
this ledger changed; macOS branch only. Test-first: the new and changed tests ran against the
`ae96a4e2` `build.py` (`git show` into `work\wp6.5\g2a2r2\red-ae96\`, loaded through the test
module's `WP61_BUILD_SCRIPT` hook; `redfull.log`): **89 failed for the right reasons**
(`DID NOT RAISE`, `ACCEPTED` where a refusal was asserted, the byte-family lists non-empty,
the UTF-8 configuration refused as "2 distinct"), one of them on its message only (the tab
case `--enable-libass\t--disable-libx265`: the old `split()` refused it as "disabled", the new
rule as "printed form"); 3 more failures were the copy's location (`notices.py` not beside it),
not new tests. Then GREEN. Nothing downloaded or run: FFmpeg's `configure` at `b204e94e`
(r1's extract, `work\wp6.5\g2a2r1\src\`) read as text; the provider's arm64 `ffmpeg` (r1's zip,
sha256 `c8ed4c4e...d924`) read as bytes. Commit `d6296b92`.

### A r4 adjudication

| Finding | Verdict | Change (head `d6296b92`) | RED (`ae96a4e2` code) | GREEN; the class each test binds |
|---|---|---|---|---|
| A4-F1 MAJOR, `--disable-encoder=` patterns matched unlike configure | FIXED (conservative refusal, not emulation) | `build.py:1053` `_LITERAL_ENCODER_LIST`: configure (`configure:4733-4741` at `b204e94e`) turns the value into ONE `case` pattern (`,` -> `_encoder\|`, `_encoder` appended once) and `eval`s it; that is NOT reproduced. `:1571` admits only a literal comma list of `[A-Za-z0-9_]` names not naming `libx265` (for such a list the pattern reaches `libx265_encoder` only through the item `libx265`); every other value is refused, **including the reviewer's reverse case `libx265\|aac`, which matches nothing in configure: refused as intended**. Neighbour found by the loop: the rules judged `config.split()` tokens, but configure prints each argument through `sh_quote` (a list is printed `'aac,mp3'`, and `'--disable-libx265 '`, which configure's `eval` still applies, split into `'--disable-libx265` and `'`): `:1040` `_CONFIGURE_ARGUMENT` + `:1515` `_configure_arguments` parse configure's PRINTED form (single spaces; `l` as given, the value bare in `[A-Za-z0-9_/.+-]` or `'...'` with `'\''`), the line refused when it is not that form. Second neighbour: `extra-version` is taken by configure's `*)` branch in any spelling (`--` optional, `-`/`_` alike); `:1588` counts every spelling (exactly one). The recipe's real line (the patch's `build-ffmpeg.sh` configure call plus `FFMPEG_LIB_FLAGS`; no quote, no disable) and the provider's printed line both parse. | the reviewer's three + `[[:digit:]]`, `libx26?`, `*265*`, `\l\i\b\x\2\6\5`, printed: 7 `DID NOT RAISE`, bare: 4 (`libx265\|aac`, `libx26?` and `*265*` were already refused); the byte family: 124 admitted values; literal lists naming libx265 / empty items: 5; printed form: 10; extra-version spellings: 3; the r1 test's three quoted forms: 3 | `test_tools_package_build.py:3266` (7 patterns x printed / bare); `:3281` EVERY printable byte other than a name byte or `,` (all pattern metacharacters, quotes, space, the rest), at 4 positions, printed; `:3304` (libx265 at each list position; empty items); `:3328` (10 non-printed forms: bare list, unquoted space, quoted names, unbalanced quotes, tabs, empty argument); `:3348` admitted quoting forms (the UTF-8 path, an embedded quote, a space in a value, an empty value); `:3363` (4 spellings); `:3372` the recipe's own line (each `--enable-*` traced to the patch); `:3239` admits literal lists incl. `libx265_encoder`, `LIBX265` |
| A4-F3 MAJOR, candidates without complete C-string boundaries | FIXED | `build.py:2167` `_FFMPEG_BARE_VERSION` matches only where a version.sh form BEGINS (after a non-printable byte or the file start); `:2371` `_c_string` then takes the WHOLE C string around it (a NUL or the file start before, a NUL after, at most `_FFMPEG_STRING_LIMIT` = 8192 bytes, `:2214`), compared in full with the token: a trailing word, a control byte, a leading byte or a missing NUL make it another string. `:2185` `_FFMPEG_BANNER_VERSION`: the `"FFmpeg version " FFMPEG_VERSION` arrays are `const char[]` data whose START is not a NUL in a real binary (three of the provider's six arrays follow `\xff\xff\xff\xff`, `CJQ` and table bytes, the other three a NUL), so their start is not judged; the token runs from the prefix to the array's NUL (`:2356` `_c_string_end`), judged whole. `ffmpeg version %s` in `opt_common.c` is a printf format (`"%s version %s"` in the binary), never a candidate. Unterminated (file end first) and oversized (no NUL within the bound) candidates are kept as such and named in the refusal; a configuration candidate that is not valid UTF-8 is refused "not UTF-8". C strings are delimited by NUL only, so a UTF-8 path is part of ONE string (the reviewer's false "2 distinct" gone). `:2320` `_scan_blocks` now carries `context` = 8192 + 32 bytes of look-behind AND look-ahead around every judged position (`_ScanBlock`: `at_start` / `at_end`); matches are searched to the block's end (a lookahead sees the real next byte) and kept when they start before `stop`. | the reviewer's five cases: 5 `ACCEPTED`; the token / configuration byte families: lists non-empty; the UTF-8 lock: refused "2 distinct"; oversized: refused for another reason (a printable prefix counted as a second configuration), never as oversized; across the boundaries: 3 | `:3991` the reviewer's five; `:4006` EVERY byte 0x01-0xFF after the token, after it with words, before it, and after the token inside a banner, plus the token unterminated bare and in a banner; `:4035` every byte after / glued before the configuration, and it unterminated; `:4103` UTF-8 path accepted when the lock carries it, its Latin-1 form refused "not UTF-8" (alone and as a second string); `:4118` four oversized forms refused, a 7.9 KiB line and the token as the file's first string admitted; `:4147` three needles x 3 splits x 4 boundaries (the 1 MiB read boundary, the judged-region edges); `:4166` the real strings straddling the same boundaries admitted |
| A4-F2 MAJOR, a conflicting `cc=` configuration ignored | FIXED | `build.py:2198` `_FFMPEG_CONFIGURE_SWITCH`: a configuration candidate is ANY complete C string carrying an FFmpeg-only configure switch as a whole space-separated token (`--enable-/--disable-` `gpl` / `version3` / `nonfree` / `libx264` / `libx265`, and `extra-version=` / `pkg-config-flags=` in every spelling), whatever its first argument; the lock's line always carries them (the validator requires `--enable-gpl` and one `--extra-version=`). **Library configurations are EXCLUDED by this stated rule, not refused:** they carry none of those switches (`grep` of FFmpeg's `.c` / `.h` / `.m` at `b204e94e` finds no such literal; in the provider's real binary, the only C strings with any `--enable-` / `--disable-` token are FFmpeg's own line, libvpx's `--prefix=/Volumes/ffmpeg_arm64/tool --disable-unit-tests` and two encoder help texts naming `--enable-rate-guide-deltaq` / `--delt...`). Refusing them instead would refuse a correct build for a component's string. LIMIT (unchanged in kind): an FFmpeg configuration with none of those switches is not seen; its build's `FFmpeg version` arrays are. | 44 of the 60 family cases `ACCEPTED` (the 16 already seen began with `--` and carried a licence switch) | `:4074` 6 first arguments (`cc=clang`, `--cc=clang`, `extra-version=x`, `--prefix=/other`, `--enable-gpl`, `x`) x 10 switches; `:4094` five library-like strings left alone (libvpx's real one, the help text, a `--enable-libs` configure, `--enable-gpl-compat-mode`, `(--enable-gpl)`) |

Counts: 3 major, all in-envelope, all NEW (none reopened), 0 reverts; product fixes 3
(`build.py`) plus 2 neighbours found by the loop (printed configure form, extra-version
spellings), both in `_macos_configure_problem`; tests-only change: the r1 refusal test's three
list / pattern values now in their printed (quoted) form (`:3200-3203`), its intent unchanged.

### The reviewer's probe and the provider binary at the head

`work\wp6.5\g2a2r2\ar4_probe.py` (`ar4_probe.log`), through the head's functions, bytes only:
F1 bare `libx265_encoder|aac`, `libx26[[:digit:]]`, `libx265|aac` refused "not configure's
printed form"; printed (quoted) refused "the libx265 encoder can be disabled ... only a literal
list"; F2 second `cc=` record refused (2 distinct); F3 unterminated configuration refused
`(unterminated)`, control byte refused, version with extra words refused (`'n9.0.2-...-20261110
extra words'`), version at EOF refused `(unterminated)`; the UTF-8 path lock ACCEPTED and its
binary ACCEPTED. **Provider binary** (66,332,880 bytes, its own token and printed line from
`versions.txt`): **ACCEPTED** in 2.73 s; the line parses as configure's printed form; with the
fork's token: REFUSED naming `'9.0.2-https://www.martin-riedl.de'`; with a wrong line: REFUSED
naming the provider's.

### Proof the Windows verdicts are unchanged

`work\wp6.5\g2a2r2\windows_compare.py` (r1's script, base `git show 1ef10536`, head the
worktree): **Windows validator comparisons: 33, mismatches: []** (the real lock ACCEPTED by
both); **archive-member comparisons: 5, mismatches: []**; **Windows-path definitions
AST-identical to `de3d68a0`: 10 of 10**. `tests/test_tools_package_ffmpeg.py` 290 passed.

### Counts at the r2 head (`-p no:cacheprovider --timeout 600 --basetemp=work\wp6.5\g2a2r2\<module> -k 'not test_python_m_clearwater_starts_the_shell_and_exits_0'`)

Static: `ruff check .` All checks passed; `ruff format --check .` 337 files already formatted;
`mypy` Success 166; `mypy --platform darwin` Success 166.

| Module | Result |
|---|---|
| `tests/test_tools_package_build.py` | 555 passed (r1: 432; +123) |
| `tests/test_tools_package_ffmpeg.py` | 290 passed (unchanged) |
| `tests/test_tools_package_smoke.py` | 66 passed, 1 skipped (unchanged; the non-Windows tripwire) |
| `tests/test_release_workflow.py` | 79 passed (unchanged) |
| `tests/test_tools_package_notices.py` | 415 passed (`-n 3`) |
| `tests/test_portability.py` | 192 passed |
| `tests/test_macos_portability.py` | 224 skipped (`macos` platform skip) |

### Verification loop (self)

- Suspected (F1 neighbour, "the rules read a different tokenisation than configure"): the
  printed line quotes values and whole arguments, so `config.split()` both mis-split quoted
  lists and missed a quoted option name. CONFIRMED by reading `sh_quote` (`configure:615`) and
  the `for v in "$@"` assembly (`configure:4555-4559`): `'--disable-libx265 '` (configure's
  `eval` drops the space and disables libx265) was ACCEPTED at `ae96a4e2`. FIXED: the printed
  form is parsed, anything else refused; tests `:3328` / `:3348`.
- Suspected (F1 neighbour, "another spelling of a judged option"): configure's `*)` branch
  takes `[--]extra[-_]version=`; the date rule counted only `--extra-version=`. CONFIRMED
  (`extra-version=20261110` appended was ACCEPTED). FIXED (`:1588`), test `:3363`. The
  `--enable-X` / `--disable-X` and `--disable-encoder=` branches need the exact `--` spelling
  (`configure:4733`, `:4743`; other spellings die in `die_unknown`): REJECTED as a hole.
- Suspected (F1 neighbour): `libx265_encoder_select="atsc_a53 dovi_rpuenc"`; disabling a
  selected item disables the encoder (`check_deps`, `configure:868`). Both are in
  `CONFIG_EXTRA`, not `CMDLINE_SELECT` (`configure:2859`), so no command-line option reaches
  them. REJECTED.
- Suspected (F3, the block scanner): the bounded C string needs context on BOTH sides of a
  judged position, and a match must not be cut at `stop` (a lookahead at `endpos` sees an end
  of string). CONFIRMED in my first draft (searching with `endpos=stop`); FIXED before any
  commit (search to the block end, keep starts before `stop`; context = bound + 32 for the
  banner prefix). Proved by `work\wp6.5\g2a2r2\blocks_probe.py`: for 9 file sizes (0, 1,
  context, 1 MiB +-1, 1 MiB + context, 2 MiB, 3 MiB + 7) every position judged exactly once,
  with >= context bytes before (or the file start) and after (or the file end), `at_start` /
  `at_end` exact: 0 problems.
- Suspected (F3 class, "a one-byte change the families miss"): `mutation_probe.py`, 20,000
  random one-byte replace / insert / delete mutations of a minimal tool against a C-string
  oracle (accepted exactly when the token and the line are still complete strings and no new
  version / configuration string appeared): 0 mismatches.
- Suspected (F2, real-binary false candidates under the new rule): the provider's binary
  (above) ACCEPTED; its C strings with configure-like tokens enumerated
  (`real_strings.py`, `real_strings.log`): 4, only FFmpeg's own carries an FFmpeg-only switch.
- A final pass over F1-F3 and the loop items found nothing new.

### Limits stated

The printed-form parser treats every unquoted space as an argument separator; configure
leaves the part of an argument before its first `=` unquoted, so an argument with a space
there prints like two arguments. Every such reading is judged (more tokens, never fewer), and
configure rejects such option names (`die_unknown`) for every option this rule judges. The
banner arrays' start is not judged (const data, evidence above). An FFmpeg configuration with
none of the FFmpeg-only switches is not seen; a bare `x.y.z` version with no extra-version is
seen only in the `FFmpeg version` arrays. The real fork binary's strings are the fork run's
proof (run `42661533922`, not read by this cell).

### Findings for the dispatcher

- **G2a2r1-F1 (Windows; OPEN, routed to CHARC; UNCHANGED by this cell):** the Windows
  validator ACCEPTS the real Windows lock with `--disable-libx265`, `--disable-gpl`,
  `--disable-version3`, `--disable-encoder=libx265`, `--disable-encoders` or
  `--disable-everything` appended (r1's `work\wp6.5\g2a2r1\windows_hole.py`, 6 of 6
  ACCEPTED); the Windows branch checks `--enable-*` membership only. The A4-F1 rules (printed
  form, literal encoder lists) would apply there as well. A Windows fold changes a Windows
  verdict: CHARC's call (a DR row or a later package).

Slips: one Bash call began `cd /c && ...` (the RED run) in breach of the no-`cd` rule; the
directory lay outside the working directories, so the shell returned to its start folder
(`pwd` checked straight after: `/c/Users/rwsmy/clearwater`); no later call used `cd`. One
probe command built a `$'\r'` grep inside `$(...)` and failed to parse (nothing run); the CR
check was redone with a script (`crcheck.py`, raw `git cat-file` blobs: 0 CR). One Bash
heredoc collapsed backslashes (the known trap) and failed its own assertion before writing;
the ledger edits were redone with the Edit tool.

Depth at group-2a part-2 r2 yield: 216,416 (wp65-cell8, read by the dispatcher with cell_depth.py at its 4b-r2 return)

## G3 fix (`wp65-cell10`, dispatch-11; base `87df4840`)

Turn G3-fix: fold the stage-1 runner classification and Reviewer A r5's minor. The runner
run `42661729379` (on `ae96a4e2`) failed 63 tests in its parallel leg; the read-only
classification turn (`wp65-cell9`, dispatch-10; depth 244,789 at its return) is the record:
`clearwater-review-evidence\wp6.5\cell\g3-classification.md` (class (a) 60, (b) 1, (c) 2,
(d) 0). CHARC's G3 rulings (2026-11-09 18:06Z) applied as given: C16 measurement first (no
product change), C15 the tool fix, C1 / C2 granted, A4 a POSIX-only conftest HOME redirect,
classes (a) / (b) fixed in the TEST. **No `src/` change; no committed fixture or committed
notices-annex byte moved.** Scratch `work\wp6.5\g3fix\`.

### A r5 adjudication

| Finding | Verdict | Change | RED (`87df4840` code) | GREEN |
|---|---|---|---|---|
| A r5 MINOR, `build.py:1040` / `:1528-1531`: the printed-form parser admits redundant quoting configure never prints (`--extra-version='20261110'`, `--disable-encoder='aac'`) | FIXED (in-envelope, NEW) | `tools/package/build.py:1515` `_sh_quote` (configure's `sh_quote` at `b204e94e`: `'` -> `'\''`, bare when every byte is in `[A-Za-z0-9_/.+-]`, the empty string included); `:1546` `_configure_arguments` re-quotes each decoded value and refuses the line when the spelling differs. The positive guards hold: the UTF-8 path, the space, the embedded quote and the provider's real line (`--extra-version='https://www.martin-riedl.de'`, 34 arguments) parse. Windows branch untouched. The binary scan compares against the lock's line, which is validated on load, so the lock rule closes the reviewer's "noncanonical binary" case too. | `test_tools_package_build.py:3417` 10 redundant-quote forms (the reviewer's two; the four `extra-version` spellings; `--pkg-config-flags`; the whole `--prefix` value; `--disable-encoder='aac_at'`; `--extra-cflags=''` / `'-O2'`): **10 `DID NOT RAISE`**; `:3439` the canonical-spelling sweep: 1 `DID NOT RAISE` (`g3fix\a5-red.log`: 11 failed, 7 passed) | 566 passed; the r2 list test's empty value is now given in its printed (bare) form, `--disable-encoder=` (refused "disabled" as before) |

Windows verdicts unchanged (`windows_compare.py`, base `git show 1ef10536`): validators 33,
mismatches []; archive members 5, mismatches []; Windows-path definitions AST-identical to
`de3d68a0` 10 of 10.

### Per cause

| Cause | Rows | Class | Change (head file:line) | Proof on Windows | Owed to the runner |
|---|---|---|---|---|---|
| A4 | (note 2) | ruling | `tests/conftest.py:369` `_posix_home_redirect`: autouse, `sys.platform != "win32"` only, `HOME` = `tmp_path_factory.mktemp("home")` (beside the test's `tmp_path`, so a test listing its `tmp_path` sees nothing new); composes with the footage temp-root guard (a basetemp child) and `_release_fft_plans`; a test that sets `HOME` itself wins | `tests/test_wp65_conftest_home.py`: the two POSIX tests SKIPPED by marker, the Windows test PASSES (HOME as collection found it) | the POSIX tests: `Path.home()`, `os.path.expanduser("~")`, `~/Library` and `app_locations()` under the folder |
| C1 | 16-33 (18) | a | `tools/fixtures/stills.py:88` `_ICC_PLATFORM = b"MSFT"`, `:109` pinned in `srgb_profile()` (docstring says why) | `test_fixtures.py:1364`: LittleCMS stamp MSFT / APPL / SUNW / zero -> the manifest's `icc_md5`; RED on the old `stills.py` 3 failed (APPL, SUNW, zero), 1 passed; the regeneration test byte-identical (committed fixtures unchanged) | the 18 `-srgb` ids |
| C2 | 1 | c | `tests/test_fixtures.py:1420` collects every mismatch, `:1402` `_pixel_figure` prints per entry decoded max / p99 / nonzero / worst (row, col, channel) plus `libheif_info()`; still FAILS | probe `g3fix\c2_probe.py`: a re-encoded HEIC `max 5, p99 3`, a one-pixel PNG change `max 7 ... worst at (3, 5, 1)`; Windows regeneration passes | the full mismatch list and its figures; CHARC rules the bound |
| C3 | 10-15 | a | `test_core_deps.py:56`; `test_core_select.py:21` / `test_core_wp34.py:41` `NOT_INSTALLED` (darwin: `MACOS_CPU_REASON`), row 15's regex `re.escape`d; `got in (*REASONS, MACOS_CPU_REASON)` | passes; **simulated darwin** (`sys.platform = "darwin"` set by a scratch plugin in `pytest_configure`, `g3fix\sim\simdarwin.py`; `_probe_gpu` reads it and calls no Windows API after): the 12 select / wp34 ids PASS | `test_core_deps.py` (a child interpreter: the host's platform) |
| C4 | 34-37 | a | `test_io_video_encode_units.py:223` `WINDOWS_ROSTER = encoder_roster("win32")`, passed to `_detect` / `resolve_encoder` in the four tests | 137 passed; simulated darwin (same plugin): the four PASS | the four ids |
| C5 | 2 | a | `test_frozen_entry.py:620` `HOME` under `tmp_path` on POSIX | passes (unchanged path on win32) | the id |
| C6 | 3 | b | `test_frozen_entry.py:1200` `skipif(darwin, "the gpu extra is not installable on macOS (AD-35)")`; the guard checks `find_spec("cuda")` first | passes on Windows (the canary RUNS; not skipped) | SKIPPED with the reason |
| C7 | 4 | a | `test_gpu_pack.py:930` the expectation follows the file system (`cupy/__init__.py` still found after the rename -> `unlisted entry in site-packages: CuPy`, the runner's string) | passes (normcase branch) | the id |
| C8 | 5-8 | a | `test_gpu_pack_install.py:1242` `skipif(!= win32, "Windows mapped-image sharing semantics")` (the siblings' reason) | passes, not skipped | SKIPPED |
| C9 | 9 | a | `test_headless_export.py:1038` makes `footage/x` | passes | the read-only refusal |
| C10 | 38 | a | `test_portability.py:3214` the Windows spelling part on win32 only | passes | the id |
| C11 | 39-40 | a | `test_tools_package_build.py:140` sets `SYSTEMROOT` (the name `build.py` reads) | passes | the two win32-param ids |
| C12 | 41, 42, 45 | a | `:339`, `:360`, `:427` `skipif(!= win32, "PE bootloader checks; pefile is win32-only (uv.lock)")` | pass, not skipped | SKIPPED |
| C13 | 43-44, 49-52, 55-61 (13) | a | `:386`, `:1304`, `:1359`, `:1575`, `:1665` `skipif(!= win32, "Windows FFmpeg bundle contract ...; the macOS contract awaits ffmpeg-macos.lock.json, WP6.5 part 3")` | pass, not skipped | SKIPPED; **their darwin counterparts are part-3 work** (skipping is not darwin coverage) |
| C14 | 46-48, 53-54 | a | rows 46-47 / 53-54: `:1094`, `:1411` `skipif(!= win32, ...)` -- the FALLBACK, not the platform-path stand-in: on darwin the build then seals a `.app` with `codesign` and re-checks origin, and rows 46-47's `json` comes from the pack scan that darwin skips (AD-33), so a platform-path stand-in does not make them pass cheaply; row 48: `:1125` `skipif(darwin, "no GPU pack is scanned on macOS (AD-33)")` | pass, not skipped | SKIPPED; darwin missing-member / smoke-after-notices counterparts are part-3 work |
| C15 | 62 | a (tool, A2 (ii)) | `tools/package/notices.py:113` `_licence_order` = `as_posix().lower().split("/")` then the input (on Windows the very list `WindowsPath` compares); `:2577` | `notices.py --root-annex --check`: **root annex matches** (committed bytes unchanged); `test_tools_package_notices.py:872`: POSIX-style and Windows-style paths give the Windows order (zlib's three texts; every row of the root annex's FFmpeg rows); native POSIX order differs on **21 of 337** rows (cell9's figure) | the root-annex check on darwin |
| C16 | 63 | c (STOP) | `tests/test_wp321_fft_gaussian.py:307` the CPU test prints, on mismatch, `_batch_mismatch_report` (`:269`): max abs, p99, nonzero count, the first 12 (row, col[, channel]), numpy / scipy versions, inside 1e-5 or not, and a control with `FFT_BATCH_LINES = 516` (patched inside the test only); still FAILS; `:327` proves the report on a planted one-ulp difference | the CPU test and the planted test pass; `backend.py` untouched | **the figure** (CHARC rules on it) |

Counts: A r5 1 minor, in-envelope, NEW, 0 reverts; product-code fixes 1 (`build.py`) plus
the release tool `notices.py` (C15, tool) and the fixture generator `stills.py` (C1, test
infrastructure); test-only 13 causes plus A4 plus 1 loop finding. No `src/` change.

### Proof Windows is unchanged (each module before at `87df4840` vs after at the head; `-m "not gpu"`, `-n 3`)

| Module | Before | After |
|---|---|---|
| `test_tools_package_build.py` | 555 passed | 566 passed (+11 new) |
| `test_tools_package_notices.py` | 415 passed | 416 passed (+1) |
| `test_fixtures.py` | 354 passed | 358 passed (+4) |
| `test_wp321_fft_gaussian.py` | 18 passed | 19 passed (+1) |
| `test_portability.py` | 192 passed | 192 passed |
| `test_macos_portability.py` | 224 skipped | 224 skipped |
| `test_core_deps.py` / `test_core_select.py` / `test_core_wp34.py` | 4 / 17 / 29 passed | 4 / 17 / 29 passed |
| `test_io_video_encode_units.py` / `test_io_video_encode.py` | 137 / 116 passed | 137 / 116 passed |
| `test_frozen_entry.py` / `test_gpu_pack.py` / `test_gpu_pack_install.py` / `test_headless_export.py` | 193 / 112 / 113 / 74 passed | 193 / 112 / 113 / 74 passed |
| `test_wp65_conftest_home.py` | (new) | 1 passed, 2 skipped (POSIX-only, by marker) |
| `test_tools_package_ffmpeg.py` / `test_conftest_guard.py` | 290 / 60 passed | 290 / 60 passed |

Skips on Windows: 0 before and 0 after in every module but the macOS module and the new
POSIX tests. The before run used the base versions of the 19 changed files written in place
by `g3fix\swap.py` and restored after (`git status` clean); the base test files' entry-point
tests were checked first (the GUI stubbed, app-data redirected, as at every earlier gate).

### Verification loop (self)

- Pass 1, each cause against the runner's deciding `E` line (the table's row, the log
  `runner\run-42661729379\macos-evidence\parallel.log`): C3 row 15's regex message, C4 row 35's
  `'No NVIDIA graphics card' in ...videotoolbox...`, C6 `No module named 'cuda'` raised by
  `find_spec` (marker + guard), C7 the runner's exact reason string, C11 `SYSTEMROOT is unset`,
  C13 the five tests behind the 13 rows, C14 the five rows plus row 48. Each fix addresses its
  deciding line, not a neighbour. Confirmed.
- Pass 1, same assumption hidden by the runner's skips: **FOUND and FIXED**
  `test_io_video_encode.py:1850` `test_real_capabilities_and_the_auto_rule` (C4's cause,
  FFmpeg-gated: `set(caps) == {"hevc_nvenc", "libx265"}` would fail on darwin with FFmpeg);
  it now expects `encoder_roster()`. Listed, not fixed (GUI- or GPU-marked; this cell runs
  neither): `test_gui_settings_dialog.py:776` (`resolve_encoder("auto", capabilities)` without
  a roster, NVENC rows; the darwin default roster would resolve otherwise -- C4's cause, serial
  leg), `test_io_video_encode_bench.py:591` (`{...}["hevc_nvenc"]` KeyError on darwin,
  `gpu`-marked). Checked and clean: `test_frozen_entry.py:730` (normcase, as the product),
  `test_io_video_encode.py:1864` (guarded by `_nvenc_ready()`), the `CuPy not installed`
  literals in `test_gui_gpu_pack_dialog.py` / `test_gui_status.py` (inputs, not expectations),
  no other `SystemRoot`, `import pefile`, nested `find_spec`, or `x/..` spelling.
- Pass 1, A4 composition: the guard is a `pytest_configure` hook on the basetemp (HOME plays
  no part); `mktemp` lives under the basetemp; session- and module-scoped fixtures run before
  the redirect (stated in the docstring; none of the tests reaching `app_locations()` found by
  the grep uses one). On Linux `XDG_CONFIG_HOME` / `XDG_CACHE_HOME`, when set, outrank HOME
  (not redirected by this ruling; the macOS legs do not read them).
- Pass 2 over every cause and the loop items: nothing new. Loop ended.

### Limits stated

Every darwin-only fix is proven on Windows by its logic only, except C3 / C4 (simulated
`sys.platform`, named above); the runner proves the rest at the re-push. `test_tools_package_build.py`
cannot be imported under a simulated darwin on Windows (`urllib` reaches `_scproxy`), so
C11-C14 have no simulation. C2 and C16 still fail on darwin by design (CHARC rules on the
printed figures). With HOME redirected, git in a POSIX test reads no global config (the
runner's checkout is owned by the runner user, so `safe.directory` is not needed).

### Findings for the dispatcher

- Same-cause tests listed above (`test_gui_settings_dialog.py:776`, `test_io_video_encode_bench.py:591`)
  for the next table; both run only in legs this cell does not run.
- C13 / C14 skips are not darwin coverage: the macOS bundle, notices-after-FFmpeg, smoke
  propagation, zip-after-success, zip-mutation and missing-member contracts need darwin
  counterparts in part 3 before the switch goes on.

Depth at G3-fix yield: 259,224 (wp65-cell10, read by the dispatcher with cell_depth.py at its G3-fix return)

## Group 2a part 3 (`wp65-cell11`, dispatch-12; base `7149758f`)

Turn G2a-PART-3. **STOPPED at item 2 (the census) on the dispatch's own rule** ("where a
text is needed and is not in the zip's text members or already in the repository, STOP and
name it"): seven licence texts the census needs are in neither place, and the Apple
toolchain-runtime rows have no source pin or linkage evidence in the log. Item 1 (the lock)
is DONE AS A DRAFT, validated and mutation-proved, but NOT committed: the pin test asserts
the real lock is absent (`tests/test_release_workflow.py:1144`) and condition 4 flips that
assertion only in the switch-ON commit, which cannot land before the notices rows (they need
the texts). No product, test, workflow or fixture byte moved this turn; this ledger is the
only commit. Nothing downloaded was extracted or run; no network read. Scratch
`work\wp6.5\part3\` (scripts `scripts\zipread.py`, `tarlic.py`, `draft_lock.py`,
`mutate.py`; outputs `tarlic.out`, `mutate.out`).

### STOP: the census inputs not in the zip or the repository

The zip's text members (30: `LICENSE.txt` = FFmpeg's GPLv3, 35,147 B, sha `8ceb4b9e...`;
`build/FFmpeg-LICENSE.md`; versions, pins, toolchain, dylib lists, 15 component logs) carry
NO component licence text. Each linked component's licence files were read IN MEMORY from
the pinned source tarballs group 2a part 1 left under `work\wp6.5\g2a\dl\` (every tarball's
sha256 equals its pin in the zip's `build/sha256-pins.txt`, the runner-verified list) and
matched by sha256 against EVERY tracked file of the repository (`git ls-files`):

| Component (pin) | Text needed (the Windows row's set, at this pin) | sha256 | Bytes | In repo |
|---|---|---|---|---|
| fribidi 1.0.16 | `fribidi-1.0.16/COPYING` (LGPL-2.1) | `32434afcc8666ba0...` | 26,440 | **NO** (Windows used `libiconv--COPYING.LIB`, other bytes) |
| freetype 2.13.0 | `freetype-2.13.0/LICENSE.TXT` | `2e3bbb7d3c5c3963...` | 2,074 | **NO** (Windows `bd36c8b4...`) |
| freetype 2.13.0 | `freetype-2.13.0/docs/FTL.TXT` | `08c135755dd58903...` | 6,743 | **NO** (Windows `5a5ee54c...`) |
| SDL2 2.32.10 | `SDL2-2.32.10/LICENSE.txt` | `97f35b302b361680...` | 884 | **NO** (Windows `1c040b82...`) |
| SDL2 2.32.10 | `SDL2-2.32.10/Xcode/SDL/pkg-support/resources/License.txt` | `37b975b5273734ea...` | 909 | **NO** |
| libxml2 2.15.3 | `libxml2-2.15.3/dict.c` (whole file; the Windows row carries it) | `416253664eb3d95a...` | 25,239 | **NO** (its lines 1-17 = repo `libxml2--dict.c-L1-17.txt`) |
| Apple clang-2100.1.1.101 runtime (compiler-rt builtins, libc++ header code; G2a-F5) | llvm-project `LICENSE.TXT` (Apache-2.0 WITH LLVM-exception) at Apple's source for this clang | - | - | **NO** (repo has `llvm-3.6.2-LICENSE.TXT` and Rust's compiler-builtins combined text, neither this source) |

In the repository at the SAME bytes (reusable): zlib 1.3.2 (3 texts), openssl 3.6.1 (2),
libxml2 (`Copyright`, `list.c`, both `NOTICE`, both excerpts), freetype (`docs/GPLv2.TXT`,
`src/bdf/README`, `src/pcf/README`), fontconfig 2.17.1 (`COPYING`), harfbuzz 14.3.0
(`COPYING`, `src/ms-use/COPYING`; the Windows `perf/texts/COPYING` is absent from 14.3.0),
SDL2 (`hidapi` x4, `yuv2rgb`, `visualtest`, `Xcode-iOS` bitmapfont), libass 0.17.5, libogg
1.3.6, x265 4.2 (3), x264 (the SAME commit `0480cb05` as the Windows row, so its text).

**Toolchain-runtime gap (beyond the text):** the log names the compiler (`Apple clang version
21.0.0 (clang-2100.1.1.101)`, lines 160 / 661) but no source repository or commit for it, and
no link line showing `libclang_rt` (FFmpeg's make is not verbose; the zip's 15 component logs
carry no `libclang_rt` / `compiler-rt` string). A `toolchain_runtime` row needs a pinned
source (`repository/tree/<pin>`) and a linkage basis; neither is in the log. G2a-F5's rows
are an inference the run does not prove.

Reproduction: `python -I work\wp6.5\part3\scripts\tarlic.py work\wp6.5\g2a\dl -
tools\package\native-licences\ffmpeg-components` (output `tarlic.out`); the repository-wide
match is a 10-line `git ls-files` hash scan (0 matches for the six component texts).

### Item 1: the lock (draft, validated; NOT committed)

`work\wp6.5\part3\ffmpeg-macos.lock.draft.json` (sha256 `a6675a4e57aa8a9c...`, 0 CR; written
by `draft_lock.py` from the sources, the fixture's shape kept field for field; the fixture
untouched). It passes `validate_ffmpeg_lock(..., platform="darwin")` at the head (census
`pending`, the only value the head admits).

| Field | Value | Source |
|---|---|---|
| `release_tag` | `ffmpeg-9.0-gb204e94e-macos-arm64-nozvbi-9cb0fa8` | seat `fork-recipe-macos.md:57` (lightweight tag -> `9cb0fa81...` by `git ls-remote`) |
| `build_repository_commit` | `9cb0fa81871f09ae3f750d6845874c26a871b985` | seat `:57`; `attempt3-run.json` `headSha`; zip `build/versions.txt` `recipe rwsmythe/FFmpeg-Builds@9cb0fa81...` |
| `build_run_url` | `https://github.com/rwsmythe/FFmpeg-Builds/actions/runs/42661533922` | zip `build/toolchain.txt` last line; dispatch |
| `asset_name` / `archive_root` | `ffmpeg-n9.0.2-47-gb204e94e90-macos-arm64-gpl-9.0(.zip)` | the seat file name; zip root folder (every member under it) |
| `asset_url` | `.../releases/download/<tag>/<asset>` | the validator's exact form; dispatch |
| `size_bytes` | 37,978,871 | the cell's own read of the seat zip |
| `github_sha256` | `e3f251dc...76e4` | seat `:59` (GitHub asset digest) = `checksums.sha256` |
| `seat_sha256` | `e3f251dc281a71e46e1464436c8cb281994af7fe4ed4978d95922ad82bb176e4` | **the cell's own `python -I` hash of the seat zip** (37,978,871 B) |
| `version` | `n9.0.2-47-gb204e94e90-20261109` | log line 660 (`Check the binaries`) |
| `configure_line` | `configuration: --prefix=/Users/runner/work/FFmpeg-Builds/FFmpeg-Builds/work/out --pkg-config-flags=--static --extra-version=20261109 --enable-gray --enable-libxml2 --enable-version3 --enable-gpl --enable-openssl --enable-libfreetype --enable-fontconfig --enable-libharfbuzz --enable-libass --enable-libx264 --enable-libx265` | log line 662, VERBATIM after the timestamp (read by script, not retyped) |
| `runner_image_version` | `20261102.0473.1` | log line 18 (`Runner Image` group); line 155 `ImageVersion=` |
| `source_record_url` | `https://github.com/rwsmythe/FFmpeg-Builds/tree/9cb0fa81...` | the fork tree at the build commit |
| `retention_note` | "the asset is a release of the owner's fork (tag `<tag>`, not Latest); no retention policy applies; rebuild in the fork for an FFmpeg bump (checklist step)" | the Windows note's form plus the tag |
| `build_script` | Riedl `f63b8aab...` | zip `build/versions.txt` last line |
| `extract_members`, `ffmpeg_*`, `licence`, `macos_deployment_target`, `runner_label` | as the fixture | zip `build/versions.txt` line 1 (FFmpeg commit / ref); log 160-161, step env `DEPLOYMENT_TARGET: 14.0` |
| `excluded[]` | the fixture's 21 rows | log lines 337-343: the build.sh call's `-SKIP_*=YES` = these 21 + `SKIP_TEST` / `SKIP_BUNDLE` (G2a2-F1) |
| `components[]`, `toolchain`, `toolchain_runtime[]` | empty / null (census pending) | the STOP above |

**Digest proof:** the cell's own hash of the seat zip: 37,978,871 B, sha256
`e3f251dc281a71e46e1464436c8cb281994af7fe4ed4978d95922ad82bb176e4` (equal to the dispatch, the
seat post and `checksums.sha256`).

**Mutation family** (`mutate.py`: the draft validated, then `_download_ffmpeg` over the seat
zip as a file URL with the module's test switch; `mutate.out`): unmutated GREEN; `size_bytes`
+1 RED "download size differs from lock", -1 RED "size exceeds lock"; `github_sha256` digit 0
/ 63 +1 RED and `seat_sha256` digit 0 / 63 +1 RED ("sha256 readings differ"); both digests
moved together (a self-consistent lock) digit 0 / 63 RED "download sha256 mismatch; archive was
not opened"; the `--ffmpeg-sha256` argument digit 0 / 63 RED "argument differs from the lock".
10 of 10 mutations RED. These are the head's existing rules (no new rule was needed); the
family becomes a committed test with the lock.

### The census from the run (rows and sources; `components[]` blocked by the STOP)

| Item | Value | Source |
|---|---|---|
| Linkage, `ffmpeg` | 21 entries, all `/usr/lib/` (`libSystem.B`, `libbz2.1.0`, `libiconv.2`, `libc++.1`, `libobjc.A`) or `/System/Library/Frameworks/` (Foundation, AudioToolbox, CoreAudio, AVFoundation, CoreVideo, CoreMedia, CoreGraphics, OpenGL, ApplicationServices, CoreFoundation, Metal, VideoToolbox, CoreImage, AppKit, CoreServices, CoreText); no third-party dylib | log 618-638 (`Check the binaries`); zip `build/ffmpeg-dylibs.txt` |
| Linkage, `ffprobe` | the same 21 (byte-identical list, sha `bd8b69c1...` both) | log 639-659; zip `build/ffprobe-dylibs.txt` |
| FFmpeg's external libraries | appkit, avfoundation, bzlib, coreimage, iconv, libass, libfontconfig, libfreetype, libharfbuzz, libx264, libx265, libxml2, metal, openssl, sdl2, zlib; hwaccel audiotoolbox, videotoolbox | zip `build/logs/build-ffmpeg.log:144-153` |
| Statically linked components | x264 `0480cb05`, x265 4.2 (8/10/12-bit), openssl 3.6.1, libxml2 2.15.3, zlib 1.3.2, freetype 2.13.0, fontconfig 2.17.1, harfbuzz 14.3.0, fribidi 1.0.16 (through libass; FFmpeg's line has no `--enable-libfribidi`), libass 0.17.5, SDL2 2.32.10 (autodetected) | zip `build/versions.txt`; pins `build/sha256-pins.txt`; the dylib census above (none of them dynamic) |
| Built, not linked | libogg 1.3.6 | not in FFmpeg's external list |
| Build tools (not in the binary) | nasm 3.02, pkg-config 0.29.2, cmake 4.0.3, ninja 1.13.2, meson 1.11.2 | `build/versions.txt`, `build/toolchain.txt` |
| System, dynamic (not distributed) | bzlib, iconv, libc++, libobjc, libSystem, the frameworks | the dylib census |
| Toolchain | Xcode 26.6 (17F113), SDK 26.5, `Apple clang version 21.0.0 (clang-2100.1.1.101)`, target `arm64-apple-darwin25.6.0`, `MACOSX_DEPLOYMENT_TARGET=14.0` (the step's minos check passed for both tools; the value itself is not printed) | log 157-163, 661, 551-556; zip `build/toolchain.txt` |
| Two-way configure coverage | enabled = gpl, version3, gray, libxml2, openssl, libfreetype, fontconfig, libharfbuzz, libass, libx264, libx265; licence / feature switches (not libraries): gpl, version3, gray; the 8 others map to one component each; zlib and sdl2 are autodetected (`configure_flag` null) | log 662; `build-ffmpeg.log:144-150` |

### Not done (blocked by the STOP), in the dispatch's order

2. The complete-census rules (`components[]`, `toolchain`, `toolchain_runtime[]`, coverage)
   and the `census` block naming the step and line range: need the texts and the runtime pin.
3. The Apple toolchain marker byte-check (`Apple clang version 21.0.0 (clang-2100.1.1.101)`
   from log 661, the `toolchain` object's field): not started; it reads the census object.
4. The Mac notices and lifting the `--notices` / `--zip` refusal: need the texts.
5. Switch ON + notices rows + pin-test flip (one commit) and the C13 un-skip: not done; the
   lock lands in that commit. C13's five skips (`test_tools_package_build.py:386`, `:1304`,
   `:1359`, `:1575`, `:1665`) are unchanged.

### Verification loop (self)

- Every draft field re-read against its source (table above): the configure line and version
  are read by the script from the log lines, not retyped; size and digest from the bytes.
- Suspected: the excluded rows drifted from the run. REJECTED: the log's build.sh call
  (337-343) passes exactly the 21 + `SKIP_TEST` / `SKIP_BUNDLE`.
- Suspected: a pinned tarball under `work\` differs from what the runner built. REJECTED: each of
  the 15 distinct digests in the zip's `build/sha256-pins.txt` equals a tarball there
  (`tarlic.out`); the three other files there (the cmake source, the nasm mirror archive, the
  x265 generated archive) are not in the pin list and were not used.
- Suspected: the Windows texts could stand in for this pin. CONFIRMED false for 6 texts (other
  bytes); those are the STOP.
- Readers of the lock fields at the head: `macos-build.yml:130` (`asset_url`, `seat_sha256`),
  `build.py` (`_download_ffmpeg`, `_bundle_macos_ffmpeg`, `build()`), `smoke.py:854`; all read
  fields the draft fills; no reader yet consumes the census (part 3's code, not written).
- A second pass found nothing new.

Counts: no product, tool, test, workflow or fixture byte changed, so no suite was re-run
for this turn (the G3-fix counts stand); the only commit is this ledger (0 CR).

Depth at part-3 yield: 221,656 (wp65-cell11, read by the dispatcher with cell_depth.py at its part-3 STOP return)

## Group 2a part 3b (`wp65-cell12`, dispatch-13; base `5ccf7c75`)

Turn G2a-PART-3b: PART 3 items 2-5 after CHARC's STOP rulings R1-R3 (mail `20261109T2020Z`).
**STOPPED at items 4-5 (the Mac notices, the switch ON) on a finding with a reproduction:**
`notices.py` cannot inventory the `.app`, so `--notices` (which the switch turns on) fails on
the runner before any zip, smoke or M leg on the bundle. Items 2 and 3 are DONE and committed
green; the R3 commit (lock, texts, notices rows, pin flip, switch, mutation and re-hash tests)
is NOT made: its lock and texts are drafted and validated under `work\wp6.5\part3b\r3\`.
No `src/` change; no committed fixture or Windows notices-annex byte moved; nothing extracted
or run from the asset or the tarballs; no network. Scratch `work\wp6.5\part3b\` (scripts
`scripts\repro_app_inventory.py`, `make_texts.py`, `make_lock.py`, `mutate.py` (cell11's,
plus a texts-folder argument); `windows_compare.py` (cell8's)).

### STOP: the Mac notices cannot be generated for the `.app` (items 4-5)

- `build()` passes `executable.parent` = `Clearwater.app/Contents/MacOS` to
  `write_artifact_notices` (the `if notices:` block); the darwin smoke passes the same folder
  to `plan_notices` (`smoke.py:995`). So the input IS the executable folder (dispatch-12
  item 4's "confirm": confirmed).
- `notices._inventory` (`notices.py:1431-1436`) then requires `Contents/MacOS/_internal`.
  PyInstaller 6.22.3 builds a `.app` with NO `_internal`: code goes to `Contents/Frameworks`,
  data to `Contents/Resources`, cross-linked (`PyInstaller/building/osx.py:183-311`).
  **Reproduction** (`scripts\repro_app_inventory.py`: a minimal `.app` tree, `sys.platform`
  set to `darwin` for the call only, no Windows API after):
  `REFUSED: notices: expected an onedir folder with _internal`.
- Past that line the darwin inventory walks only `Contents/MacOS` (`notices.py:1438-1442`), so
  Frameworks / Resources (libpython, the Qt frameworks, the delocated `.dylibs`) would be
  uncovered; the native manifest is keyed on Windows host paths and hashes
  (`_internal/python312.dll`, `Qt6Core.dll`; round-0 F0-2); `_is_python_binary` reads
  Windows DLL names; `write_notices` writes beside the executable (`notices.py:2750-2751`,
  `Contents/MacOS`), while the darwin smoke and `macos-build.yml:191` read
  `Contents/Resources/THIRD_PARTY_NOTICES.md`.
- This is round-0 **F0-2** (the macOS host census), which CHARC concurred is "its own group
  after the first runner run" (dispatch-2 item 5); the first run failed in the parallel leg
  and never reached the build, so that group has not run. Dispatch-12 item 4 names only the
  FFmpeg side.
- **Consequence of switching ON now:** `macos-build.yml:133` runs `--notices --smoke --zip`;
  the build exits 1 at `FAILED: artifact notices`, then `Run macOS tests on the built bundle`
  finds no bundle (`test -d`), so the re-push loses the whole M leg the switch-OFF build
  delivers today. Fail-closed (no unlisted binary ships), but no evidence.
- **Asked of CHARC (recommended first):** (i) keep the switch OFF until the F0-2 host-census
  group lands; amend R3 so the lock + texts + census + mutation / re-hash tests + the C13
  un-skip commit now, the pin test's "no lock" half flipped and its `"false"` kept (switch ON
  and the Mac notices then land together in the F0-2 group); (ii) switch ON now and accept a
  red build step on the re-push (not recommended); (iii) run the F0-2 group first, then this
  R3 commit unchanged.
- **Also asked (R1 form):** the macOS validator checks ONE folder holding EXACTLY the macOS
  lock's texts (the Windows rule's form), so the draft folder holds 36 files: the 7 R1 / R2
  name plus 29 copied byte for byte from the same pinned tarballs (each equal to a Windows
  text; x264's from the Windows row, same commit). The literal reading ("the six texts plus
  the LLVM text", 7 files) needs a two-folder rule (macOS rows referencing
  `ffmpeg-components/`, whose names collide: `freetype--LICENSE.TXT` differs per pin).
  Recommendation: the one-folder form; CHARC rules.

### Commits

| Commit | What | Blobs |
|---|---|---|
| `5d7bd6d4` | items 2 + 3 + the notices folder exclusion, with tests | 0 CR (4 files) |
| (this ledger) | this section; cell11's depth filled | 0 CR |

### Item 2: the complete-census rules (`5d7bd6d4`)

`census` is `"pending"` (unchanged rules) or a `FFmpegMacCensus` object; anything else is
refused. A complete census (`_validate_macos_ffmpeg_lock` -> four helpers in `build.py`):

- **Source block** (`_macos_census_source`): `state` complete; `job_url` a job of the lock's
  `build_run_url`; `linkage_lines` / `version_lines` / `toolchain_lines` ordered spans;
  `external_libraries` = `build/logs/build-ffmpeg.log:<a>-<b>`; every field nonempty text.
- **Components** (`_macos_census_components`, the Windows row shape, `FFmpegMacComponent`):
  names EXACTLY `FFMPEG_MACOS_COMPONENTS` (12: the zip's `build/versions.txt` less FFmpeg and
  the build tools); `stage` = `build-<name>` (its zip log); `pin_kind` `sha256` (repository =
  the pinned download URL, pin = the runner-verified digest) or `commit` (40 hex); HTTPS;
  `extra_repositories` empty; `licence_basis` `pinned-source-text` (a new value: the identity
  read from the texts at this pin, as the Windows seat-verified row for the component; the
  Windows value `seat-verified` is refused here because no seat pass read these pins: CHARC
  may want one) and `gpl3_compatible` `yes`; the licence expression and `chosen` by the
  Windows component rules; `status` `built-not-linked` exactly for `FFMPEG_MACOS_UNLINKED`
  (libogg) and then no flag; texts `{path, sha256, member}` (`FFmpegMacText`: safe file name,
  64 hex, a relative member path, an excerpt as `#L<a>-<b>` with a `-L<a>-<b>.txt` name).
- **Coverage, two-way:** the line's `--enable-*` less `FFMPEG_MACOS_NON_LIBRARY_SWITCHES`
  (`gpl`, `version3`, `gray`) = the rows' flags, each mapped once.
- **Toolchain** (`_macos_census_toolchain`, `FFmpegMacToolchain`): `compiler` the marker form
  (`FFMPEG_MACOS_COMPILER`), `xcode`, `sdk`, `target` (arm64 darwin); `deployment_target` =
  `macos_deployment_target`, `census_build_commit` = `build_repository_commit`,
  `census_asset_sha256` = `github_sha256` (bound to THIS asset).
- **Runtime** (`_macos_census_runtime`, `FFmpegMacRuntime`): EXACTLY one row, CHARC R2: kind
  `apple-clang-runtime`, reached via `toolchain`, `pin_kind` `toolchain-marker`, `pin` = the
  toolchain `compiler`, `version` = its clang build, `name` derived ("Apple clang 21.0.0
  (clang-2100.1.1.101), Xcode 26.6, SDK 26.5, deployment target 14.0"), repository
  `https://github.com/llvm/llvm-project`, `source_url` a commit tree there, licence
  `Apache-2.0 WITH LLVM-exception`, `licence_basis` `upstream-text`, `linkage` `inferred`,
  `basis` `toolchain-marker`, `chosen` null. **Windows-row fields that cannot apply, and how
  filled:** `pin` (no Apple source commit) = the marker; `source_url` = the licence text's
  upstream commit tree (R2: tag `llvmorg-21.1.0` -> `3623fe66`); `basis` (Windows:
  `compile-log` / `lock-graph` / `binary`) = `toolchain-marker`; `linkage` (Windows: `proven`
  / `superset`) = `inferred`, as R2 says.
- **Texts** (`_macos_census_texts`): each referenced file exists (no link), sha256 equal,
  strict UTF-8; one digest per path; the folder (`FFMPEG_MACOS_TEXTS_PATH` =
  `native-licences/ffmpeg-macos-components`, read at call time) holds EXACTLY the lock's
  texts. `validate_ffmpeg_lock(component_texts_path=None)` now resolves the platform's folder
  (Windows: `FFMPEG_COMPONENT_TEXTS_PATH`; verdicts unchanged, below).

Tests `test_tools_package_build.py` (`complete_macos_lock`: a SYNTHETIC complete census on
the fixture; the fixture file is untouched): it validates (+ field sets); the default folder
is read at call time; **59 refusals** (`test_macos_complete_census_refuses`, each matched to
its rule's message: census, components, pins, basis, licence, status, coverage, members /
paths / excerpts, toolchain, runtime, text bytes / folder); a shared text + an excerpt + a
commit pin admitted; the pending-provenance row for `census: "complete"` now expects the new
message. RED on the parent `build.py` (`WP61_BUILD_SCRIPT` = `git show
5ccf7c75:tools/package/build.py` under `work\pkgbase\`): **71 failed** (70 `no attribute
'FFMPEG_MACOS_COMPONENTS'`, 1 the old "census rules are WP6.5 part 3's" message). The parent
refuses EVERY complete census, so no rule-by-rule RED exists there; each refusal's
specificity is its matched message on the new code. GREEN.

### Item 3: the Apple toolchain marker (`5d7bd6d4`)

`build.py` `_check_macos_toolchain_marker`: the toolchain `compiler` must occur in each tool
as a COMPLETE C string (non-printable byte or file start before, NUL after), read in 1 MiB
blocks (`_scan_blocks`), never run; called in `_bundle_macos_ffmpeg` after the version read,
before anything is placed. Source of the rule: FFmpeg's configure stores `$cc --version`'s
first line as `CC_IDENT`, printed by `fftools/opt_common.c` as `built with %s` (the run's
`built with Apple clang version 21.0.0 (clang-2100.1.1.101)`, log line 661). A pending lock
has no toolchain and is not checked (`build()` refuses `--notices` / `--zip` for it). Tests:
7 bundle cases (NUL / control byte before: admitted; absent, printable byte glued before,
glued after, `21.0.1`, a shorter build: refused, nothing placed, nothing trusted); 5 split
points x 2 prefixes across the 1 MiB boundary, the file-start case, the pending case.
**Proof here:** logic and synthetic bytes only (the real tools are never read, by the
dispatch's rule). **The runner proves** that the real `ffmpeg` / `ffprobe` carry the marker
as such a string.

### Item 4 (partial): the notices folder (`5d7bd6d4`)

`notices.py` `load_native_licences` leaves `ffmpeg-macos-components/` to its lock as it does
the Windows two (otherwise the Windows notices fail with "native licence files without
manifest rows" the moment the folder lands). Test
`test_native_surface_leaves_the_ffmpeg_lock_text_folders_to_their_locks` (4): RED on the
parent `notices.py` 1 failed (`...without manifest rows: ffmpeg-macos-components`), 3 passed;
GREEN 4. `notices.py --root-annex --check`: **root annex matches**. The `_ffmpeg_rows` darwin
branch (tools without `.exe`, material in `Contents/Resources`, the macOS lock and folder)
is NOT written: its entry labels depend on the `.app` inventory design (the STOP).

### The R3 draft (NOT committed; `work\wp6.5\part3b\r3\`)

- `ffmpeg-macos.lock.json` (sha256 `caf3bdef...`, 25,699 B, 0 CR): cell11's draft (sha
  `a6675a4e`, verified) with the census filled by `make_lock.py`; it **validates** under
  `5d7bd6d4` against `r3\ffmpeg-macos-components\` (36 files; 0 CR except two upstream CRLF
  texts the Windows folder also carries, `zlib--contrib--dotzlib--LICENSE_1_0.txt` and
  `sdl--visualtest--COPYING.txt`; `.gitattributes` has `native-licences/** -text`).
- Texts: `make_texts.py` read the runner-verified pins from the zip's
  `build/sha256-pins.txt` (in memory), opened each pinned tarball in memory, refused any whose
  digest is not a pin, and wrote ONLY the named members. The seven new texts:

| File | Member | sha256 | Bytes | Source |
|---|---|---|---|---|
| `fribidi--COPYING` | `fribidi-1.0.16/COPYING` | `32434afcc8666ba0...` | 26,440 | `.../fribidi-1.0.16.tar.xz`, pin `1b1cde5b...` |
| `freetype--LICENSE.TXT` | `freetype-2.13.0/LICENSE.TXT` | `2e3bbb7d7c5c3963...` | 2,074 | `.../freetype-2.13.0.tar.gz`, pin `a7aca0e5...` |
| `freetype--docs--FTL.TXT` | `freetype-2.13.0/docs/FTL.TXT` | `08c135755dd58903...` | 6,743 | same |
| `sdl--LICENSE.txt` | `SDL2-2.32.10/LICENSE.txt` | `97f35b302b361680...` | 884 | `.../SDL2-2.32.10.tar.gz`, pin `5f5993c5...` |
| `sdl--Xcode--SDL--pkg-support--resources--License.txt` | `SDL2-2.32.10/Xcode/SDL/pkg-support/resources/License.txt` | `37b975b5273734ea...` | 909 | same |
| `libxml2--dict.c` (+ `libxml2--dict.c-L1-17.txt`, member `#L1-17`, = the Windows excerpt's bytes) | `libxml2-2.15.3/dict.c` | `416253664eb3d95a...` | 25,239 | `.../libxml2-2.15.3.tar.xz`, pin `78262a6e...` |
| `llvm-project--LICENSE.TXT` | `LICENSE.TXT` | `8d85c1057d742e59...` | 15,141 | seat `LICENSE.TXT.llvmorg-21.1.0`, digest checked = R2 |

  Licence identities read from the six (the LGPL-2.1 text; FreeType's dual FTL / GPLv2; the
  zlib-style SDL texts; the ISC-style Veillard header) agree with the Windows rows.
- **R2 seat record, verbatim:** see "The R2 record" below.
- **Digest proof:** my own `python -I` hash of the seat zip: 37,978,871 B, sha256
  `e3f251dc281a71e46e1464436c8cb281994af7fe4ed4978d95922ad82bb176e4` = `checksums.sha256`.
- **Mutation family** on the COMPLETE draft (`mutate.out`): unmutated GREEN over the seat zip;
  size +1 / -1 RED; `github_sha256` / `seat_sha256` digit 0 / 63 RED (readings differ); both
  digests moved together, digit 0 / 63, now RED one rule EARLIER ("toolchain
  census_asset_sha256 differs from github_sha256; re-census"); `--ffmpeg-sha256` digit 0 / 63
  RED. 10 of 10. The committed form (R3) adds the three-field move (both digests and the
  census digest) to reach "download sha256 mismatch", on a synthetic zip carrying the real
  lock's other fields (the seat zip is not in the repository).

### The R2 record (verbatim, `seat\llvm-licence\fetch-record.md`)

Command (Git Bash, at the seat):

    for T in llvmorg-21.1.0 llvmorg-17.0.1; do
      gh api repos/llvm/llvm-project/git/ref/tags/$T --jq '"ref object: \(.object.type) \(.object.sha)"'
      O=$(gh api repos/llvm/llvm-project/git/ref/tags/$T --jq '.object.sha'); gh api repos/llvm/llvm-project/git/tags/$O --jq '"peeled: \(.object.type) \(.object.sha)"'
      gh api "repos/llvm/llvm-project/contents/LICENSE.TXT?ref=$T" -H "Accept: application/vnd.github.raw" > LICENSE.TXT.$T
      wc -c < LICENSE.TXT.$T; sha256sum LICENSE.TXT.$T
    done

Output (verbatim):

    == llvmorg-21.1.0
    ref object: tag 827731c0bf12b0ce8d70e15ebf9f731e7961fe51
    peeled: commit 3623fe661ae35c6c80ac221f14d85be76aa870f1
    15141
    8d85c1057d742e597985c7d4e6320b015a9139385cff4cbae06ffc0ebe89afee
    == llvmorg-17.0.1
    ref object: tag 3898e35f0ccd78c7dc82056d5c810ef44453bd75
    peeled: commit e19b7dc36bc047b9eb72078d034596be766da350
    15141
    8d85c1057d742e597985c7d4e6320b015a9139385cff4cbae06ffc0ebe89afee

Result: the two digests are EQUAL (no STOP). Path `LICENSE.TXT` (repository root), 15,141 B,
0 CR.

### The census (rows, sources)

| Item | Value | Source |
|---|---|---|
| census `job_url` / log | `.../actions/runs/42661533922/job/129375108552`; the seat's saved job log (attempt 3, 874 lines) | seat `fork-run\attempt3-build.log`; dispatch-12 |
| linkage | `ffmpeg` / `ffprobe`: 21 entries each, all `/usr/lib` or `/System/Library/Frameworks` | `Check the binaries`, lines 618-659 |
| version, marker, configure | `ffmpeg version n9.0.2-47-gb204e94e90-20261109`; `built with Apple clang version 21.0.0 (clang-2100.1.1.101)`; the configure line | same step, 660-662 |
| toolchain | Xcode 26.6 (17F113), SDK 26.5, the clang line, target `arm64-apple-darwin25.6.0` | `Record and check the runner`, 157-163; zip `build/toolchain.txt` |
| FFmpeg's libraries | zlib, sdl2 autodetected; the eight flagged libraries | zip `build/logs/build-ffmpeg.log:144-153` |
| components (12) | x264 `0480cb05` (commit); x265 4.2, openssl 3.6.1, libxml2 2.15.3, zlib 1.3.2, freetype 2.13.0, fontconfig 2.17.1, harfbuzz 14.3.0, fribidi 1.0.16, libass 0.17.5, SDL2 2.32.10 (tarball sha256 pins); libogg 1.3.6 built, NOT linked | zip `build/versions.txt`, `build/sha256-pins.txt` |
| runtime (1) | the Apple clang runtime, `Apache-2.0 WITH LLVM-exception`, linkage inferred | CHARC R2; the R2 record |

**For CHARC's accept note:** the Mac bundle's FFmpeg component set is NARROWER than the
Windows one: 11 statically linked components (plus libogg, built but not linked) against the
Windows lock's 100 component rows; the macOS line enables 8 external libraries and
autodetects 2 (zlib, SDL2); 21 recipe stages are skipped (`excluded`). No `pending` gap
remains in the census itself.

### Not done (the STOP), in the dispatch's order

4. The `_ffmpeg_rows` darwin branch and the `.app` notices (inventory, native rows, the write
   location): the F0-2 host census.
5. The R3 commit: `tools/package/ffmpeg-macos.lock.json` and
   `native-licences/ffmpeg-macos-components/` (from `r3\`), the committed mutation family and
   text re-hash test, the pin test (`tests/test_release_workflow.py:1144`, "false" and
   no-lock), `macos-build.yml:35` "true", the C13 un-skip (the five `skipif` sites in
   `test_tools_package_build.py`, whose darwin counterparts need the lock) and the C14 darwin
   counterparts (missing-member, smoke-after-notices: both need the Mac notices).

### Counts at `5d7bd6d4` (`-p no:cacheprovider -n 3 --timeout 600 -m "not gpu" --basetemp=work\wp6.5\part3b\<module> -k 'not test_python_m_clearwater_starts_the_shell_and_exits_0'`)

Static: `ruff check .` All checks passed; `ruff format --check .` 338 files already formatted;
`mypy` Success 166; `mypy --platform darwin` Success 166.

| Module | Result |
|---|---|
| `tests/test_tools_package_build.py` | 636 passed (G3 fix: 566; +70) |
| `tests/test_tools_package_notices.py` | 420 passed (416; +4) |
| `tests/test_tools_package_ffmpeg.py` | 290 passed |
| `tests/test_release_workflow.py` | 79 passed |
| `tests/test_tools_package_smoke.py` | 66 passed, 1 skipped (the non-Windows tripwire) |
| `tests/test_portability.py` | 192 passed |
| `tests/test_macos_portability.py` | 224 skipped (`macos` platform skip) |

`notices.py --root-annex --check`: root annex matches. **Windows unchanged**
(`windows_compare.py` against `git show 1ef10536:tools/package/build.py`): validators 33,
mismatches []; archive members 5, mismatches []; Windows-path definitions AST-identical to
`de3d68a0` 9 of 10, the changed one `validate_ffmpeg_lock` (its texts-folder default is now
resolved at call time; its verdicts are the 33 above).

### Verification loop (self)

- Pass 1, every rule against the real draft: the draft validates; each of the 59 synthetic
  damages is refused by its own rule (matched message). Confirmed.
- Suspected: a census object refused by the document's field-text loop. CONFIRMED in the
  first edit (the loop checked `census` as text); FIXED before the commit (`census` has its
  own rule).
- Suspected: reusing `_ffmpeg_component_obligations` for the macOS rows would refuse
  `built-not-linked`. CONFIRMED by reading; AVOIDED (the licence / chosen checks are inline).
- Suspected: the marker's look-behind misjudged at a block start. REJECTED: `_scan_blocks`
  gives `len(marker) + 2` bytes of context, and the test glues a printable byte in the
  previous block at five split points (refused each time).
- Readers of the lock fields: `macos-build.yml:131-132` (`asset_url`, `seat_sha256`);
  `build()` (`lock.get("census") == "pending"`: a census object lifts the `--notices` /
  `--zip` refusal with no code change); `_bundle_macos_ffmpeg` (now `toolchain`); `smoke.py`
  (`load_macos_ffmpeg_lock()`: on the runner it re-validates the texts in the checkout's
  folder); `notices.py` reads only the Windows lock. Each reads the draft's fields correctly.
- Pass 2 over items 2-3, the R3 draft and the STOP evidence: nothing new. Loop ended.

Depth at part-3b yield: 376,153 (wp65-cell12, read by the dispatcher with cell_depth.py at its part-3b STOP return)

## Group 2a part 3c (`wp65-cell13`, dispatch-14; base `ea68e99e`)

Turn G2a-PART-3c: the AMENDED R3 commit under CHARC's rulings on the part-3b STOP (mail
`20261109T2055Z`): Q1 option (i), the switch STAYS OFF; Q2, ONE texts folder of 36. No STOP.
No `src/` change; `MACOS_FFMPEG_BUNDLED`, `notices.py`'s `_inventory` and the C14 rows are
untouched; the committed Windows notices annex bytes did not move. Nothing downloaded was
extracted or run; no network read. Scratch `work\wp6.5\part3c\` (scripts
`scripts\verify_texts.py`, `scripts\verify_fields.py`, both this cell's; `mutate_seat.py` and
`windows_compare.py`, copies of the part-3b scripts, read before they ran).

### The commit

| Commit | What | Blobs |
|---|---|---|
| `02d07744` | the lock, the 36 texts, the tests (artifact pin, re-hash, transport family, C13 darwin counterparts, pin flip, CHARC's guard) and the notices-fixture fix | 40; 0 CR except the two upstream CRLF texts (below); every text and the lock byte-equal to their source |
| (this ledger) | this section; cell12's part-3b depth filled | 0 CR |

### The lock (`tools/package/ffmpeg-macos.lock.json`, sha256 `caf3bdef...`, 25,699 B, 0 CR)

Cell12's draft `work\wp6.5\part3b\r3\ffmpeg-macos.lock.json`, committed byte for byte (blob
sha256 `caf3bdefbe24c4beaa7d2937799c530d1e107fcf4bdd252332e0b7e0177eac6f`). Verified before the
commit (`verify_fields.py`, output `verify_fields.out`, VERDICT PASS):

- re-validated under the head (`validate_ffmpeg_lock(platform="darwin")` against the draft
  folder; then `load_macos_ffmpeg_lock()` against the committed folder in the tests);
- the seat zip hashed by this cell: 37,978,871 B, sha256 `e3f251dc...76e4` = `size_bytes`,
  `github_sha256`, `seat_sha256`, `toolchain.census_asset_sha256`; `checksums.sha256` agrees;
- against the seat log `fork-run\attempt3-build.log` (874 lines): `version` (660),
  `configure_line` (662, string-equal after the timestamp), the compiler (160 and 661 `built
  with ...`), `xcode` (157-158), `sdk` (159), `target` (161), `runner_image_version` (18 and
  155), `macos_deployment_target` (150 `DEPLOYMENT_TARGET: 14.0`), `excluded[]` = the build.sh
  call's `-SKIP_*=YES` less `SKIP_TEST` / `SKIP_BUNDLE` (330-349), linkage 618-659 system-only;
- `census.job_url` under `build_run_url`; `attempt3-run.json`: `headSha` `9cb0fa81...`, job
  129375108552 at that URL; zip `build/versions.txt`: every component version, x264
  `0480cb05`, recipe `9cb0fa81`, Riedl `f63b8aab`;
- every `sha256` pin is in the zip's `build/sha256-pins.txt` with the row's `repository` as its
  URL.

**Seat-zip family on the committed lock** (`mutate_seat.py`, output `mutate_seat.out`):
unmutated GREEN; size +1 / -1, `github_sha256` / `seat_sha256` digit 0 / 63, both digests
together digit 0 / 63 (census binding), `--ffmpeg-sha256` digit 0 / 63: 10 of 10 RED.

### The 36 texts (`tools/package/native-licences/ffmpeg-macos-components/`)

Each re-verified by `verify_texts.py` (output `verify_texts.out`): the tarball whose sha256
equals the row's pin (and is in `build/sha256-pins.txt`) opened IN MEMORY with `python -I`,
the member read and compared with the lock's digest and the draft file's bytes; excerpts as
the member's lines; LLVM from the seat file; x264 from the Windows x264 row (the same commit
`0480cb05`, its `libdvdnav--COPYING`, re-hashed against that row). 36 of 36 OK, 0 extra.
Every committed blob is byte-equal to its draft (so to its source). Tarballs under
`work\wp6.5\g2a\dl\`: fontconfig `9f5cae93`, freetype `a7aca0e5`, fribidi `1b1cde5b`,
harfbuzz `16070d77`, libass `caab4b99`, libogg `83e67047`, libxml2 `78262a6e`, openssl
`b1bfedcd`, sdl `5f5993c5`, x265 (`x265-downloads.bin`) `40b1ea04`, zlib `bb329a0a`.

| File | Source | sha256 |
|---|---|---|
| `fontconfig--COPYING` | `fontconfig.bin` `fontconfig-2.17.1/COPYING` | `51a51aa9823704fd90bccc616cdd17ebabb5b2b3e9cbde886ca02c7002288067` |
| `freetype--LICENSE.TXT` | `freetype.bin` `freetype-2.13.0/LICENSE.TXT` | `2e3bbb7d7c5c396368dd0853a790ec29ce5b8647163dde42a0493fb0d6556b2b` |
| `freetype--docs--FTL.TXT` | `freetype.bin` `freetype-2.13.0/docs/FTL.TXT` | `08c135755dd589039470f1fdbb400daaabaaa50d0b366d19cebff4d22986baa1` |
| `freetype--docs--GPLv2.TXT` | `freetype.bin` `freetype-2.13.0/docs/GPLv2.TXT` | `c4120c6752c910c299e3bd9cb3a46ff262c268303ca2069b61f92f10a5656c18` |
| `freetype--src--bdf--README` | `freetype.bin` `freetype-2.13.0/src/bdf/README` | `7984455e7e5a9faba3797c8bf095fbe10cc846316b7320aff8c58402e22b82fe` |
| `freetype--src--pcf--README` | `freetype.bin` `freetype-2.13.0/src/pcf/README` | `18d9782898d9eac04476e2f744678137b2a889689ed3e923e052fc396a86f86b` |
| `fribidi--COPYING` | `fribidi.bin` `fribidi-1.0.16/COPYING` | `32434afcc8666ba060e111d715bfdb6c2d5dd8a35fa4d3ab8ad67d8f850d2f2b` |
| `harfbuzz--COPYING` | `harfbuzz.bin` `harfbuzz-14.3.0/COPYING` | `ba8f810f2455c2f08e2d56bb49b72f37fcf68f1f4fade38977cfd7372050ad64` |
| `harfbuzz--src--ms-use--COPYING` | `harfbuzz.bin` `harfbuzz-14.3.0/src/ms-use/COPYING` | `c2cfccb812fe482101a8f04597dfc5a9991a6b2748266c47ac91b6a5aae15383` |
| `libass--COPYING` | `libass.bin` `libass-0.17.5/COPYING` | `f7e30699d02798351e7f839e3d3bfeb29ce65e44efa7735c225464c4fd7dfe9c` |
| `libogg--COPYING` | `libogg.bin` `libogg-1.3.6/COPYING` | `d2ab5758336489da61c12cc5bb757da5339c4ae9001f9bb0562b4370249af814` |
| `libxml2--Copyright` | `libxml2.bin` `libxml2-2.15.3/Copyright` | `5d4873884a890122a4b9b20ad56ac6f7da1d796a5bfcf04a427970ac96217626` |
| `libxml2--dict.c` | `libxml2.bin` `libxml2-2.15.3/dict.c` | `416253664eb3d95a393be6c61c649a1b5600729bbd1e3ce9123df08b12d8f388` |
| `libxml2--dict.c-L1-17.txt` | `libxml2.bin` `libxml2-2.15.3/dict.c` lines 1-17 | `ea9e97f88bf4ef8ad1142e12d0e6da003968420aa38094f74b9b51206675438a` |
| `libxml2--list.c` | `libxml2.bin` `libxml2-2.15.3/list.c` | `8a04740bfd8a37f3006bfc0404aa31429e56ef991cddcd47707ce2a9b1d98506` |
| `libxml2--list.c-L1-16.txt` | `libxml2.bin` `libxml2-2.15.3/list.c` lines 1-16 | `2fdb83809864852d236c64fffa74054699e61887b736e18724d4a8ac0e9684f8` |
| `libxml2--result--html-tokenizer--NOTICE` | `libxml2.bin` `libxml2-2.15.3/result/html-tokenizer/NOTICE` | `d6a2cb265a0a249a234b89eeffa7f316ebe5bff546672a0a2b1a861dd2238460` |
| `openssl--LICENSE.txt` | `openssl.bin` `openssl-3.6.1/LICENSE.txt` | `7d5450cb2d142651b8afa315b5f238efc805dad827d91ba367d8516bc9d49e7a` |
| `openssl--external--perl--Text-Template-1.56--LICENSE` | `openssl.bin` `openssl-3.6.1/external/perl/Text-Template-1.56/LICENSE` | `9837f05336ef3cbacb6a96e1672a0426d81ad01191f214b8d48e22ca62338181` |
| `sdl--LICENSE.txt` | `sdl.bin` `SDL2-2.32.10/LICENSE.txt` | `97f35b302b361680ec1e891e95d2d52097bb95abff361434916d99dc1305f127` |
| `sdl--Xcode-iOS--Demos--data--bitmapfont--license.txt` | `sdl.bin` `SDL2-2.32.10/Xcode-iOS/Demos/data/bitmapfont/license.txt` | `5059bc9c2f37b7e7a557685ae9330ecfd798537bdfde94de63a9c721c92a8856` |
| `sdl--Xcode--SDL--pkg-support--resources--License.txt` | `sdl.bin` `SDL2-2.32.10/Xcode/SDL/pkg-support/resources/License.txt` | `37b975b5273734ea157fb1e363d06191036f289eca7767f736967816bedd156f` |
| `sdl--src--hidapi--LICENSE-bsd.txt` | `sdl.bin` `SDL2-2.32.10/src/hidapi/LICENSE-bsd.txt` | `30eb1bef29b46f8ba7ab8b416035dbd93cb034a45481dd97815b944284582cd2` |
| `sdl--src--hidapi--LICENSE-gpl3.txt` | `sdl.bin` `SDL2-2.32.10/src/hidapi/LICENSE-gpl3.txt` | `8ceb4b9ee5adedde47b31e975c1d90c73ad27b6b165a1dcd80c7c545eb65b903` |
| `sdl--src--hidapi--LICENSE-orig.txt` | `sdl.bin` `SDL2-2.32.10/src/hidapi/LICENSE-orig.txt` | `fb5436aa63d1b71a8dfbf74ecaf1a5b4e1ec4df7f80074d11fec99284f69ca5f` |
| `sdl--src--hidapi--LICENSE.txt` | `sdl.bin` `SDL2-2.32.10/src/hidapi/LICENSE.txt` | `7d3b087c34f35d4d538e3bcddd1ff8f66e92f9ef336881999482800ddf840913` |
| `sdl--src--video--yuv2rgb--LICENSE` | `sdl.bin` `SDL2-2.32.10/src/video/yuv2rgb/LICENSE` | `f7d74004cc75778cae46c5f0139f244d67c07ef64cf51937e8272352197dcb18` |
| `sdl--visualtest--COPYING.txt` | `sdl.bin` `SDL2-2.32.10/visualtest/COPYING.txt` (upstream CRLF, 18 CR) | `dae65ccf728227eff8e10194437078a5628047b9f55d796039688e7ca8e3aa4e` |
| `x264--COPYING` | Windows x264 row (`0480cb05`) text `ffmpeg-components/libdvdnav--COPYING` | `32b1062f7da84967e7019d01ab805935caa7ab7321a7ced0e30ebe75e5df1670` |
| `x265--COPYING` | `x265-downloads.bin` `x265_4.2/COPYING` | `d8afb1bcc7a2cfc603683b168d6987ef0a48e59e0da3693bf55c5d33b67e2b49` |
| `x265--source--dynamicHDR10--LICENSE.txt` | `x265-downloads.bin` `x265_4.2/source/dynamicHDR10/LICENSE.txt` | `47f15d63e82eb8a4de6e46471d5f96cf6d052fd5355944a002c3157880248b69` |
| `x265--source--dynamicHDR10--json11--LICENSE.txt` | `x265-downloads.bin` `x265_4.2/source/dynamicHDR10/json11/LICENSE.txt` | `950e288a2548cb33f6a90d23958806b0803f510ab17c600d661619a73ae3a6c8` |
| `zlib--LICENSE` | `zlib.bin` `zlib-1.3.2/LICENSE` | `e32ff4e00d9d94930537635291da39e7e612703334bf6fde8c7f1686fe8a45a2` |
| `zlib--contrib--dotzlib--LICENSE_1_0.txt` | `zlib.bin` `zlib-1.3.2/contrib/dotzlib/LICENSE_1_0.txt` (upstream CRLF, 22 CR) | `36266a8fd073568394cb81cdb2b124f7fdae2c64c1a7ed09db34b4d22efa2951` |
| `zlib--contrib--minizip--LICENSE.Info-Zip` | `zlib.bin` `zlib-1.3.2/contrib/minizip/LICENSE.Info-Zip` | `fc686023047ce5ce3a18a9b8a777156f0e475929d3de06bac279f3c025d2b2ca` |
| `llvm-project--LICENSE.TXT` | seat `llvm-licence\LICENSE.TXT.llvmorg-21.1.0` (R2) | `8d85c1057d742e597985c7d4e6320b015a9139385cff4cbae06ffc0ebe89afee` |

**The two CR-bearing blobs** carry the upstream's own CRLF bytes (the tarball members hold 18
and 22 CR); the Windows folder's committed blobs of the same two texts hold the same counts,
and `.gitattributes` has `tools/package/native-licences/** -text`. Byte equality to the source
is the binding form (the validator re-hashes them), so "0 CR" holds for every other blob.

### C13: skip -> check

The five Windows tests keep a platform skip on darwin (they build `Clearwater.exe` against
`ffmpeg.lock.json`), the "awaits ffmpeg-macos.lock.json" reason DELETED and replaced by a
pointer to the counterpart. Each counterpart runs `build()` on its darwin path against the
COMMITTED macOS lock on every host (on Windows `sys.platform` reads `darwin` for the build
call only, the stand-in executable written first, as `darwin_app_build` does; the runner runs
it natively).

| Site (head) | Windows test (ids) | Before on darwin | After: darwin counterpart (ids), what is real |
|---|---|---|---|
| `:383` | `test_build_enforces_origin_after_all_native_copies` (2) | SKIPPED "awaits lock" | `..._on_darwin` (2): the REAL darwin bundling (real lock's version, configure line, census, toolchain marker; synthetic zip with the transport moved) and the REAL darwin origin walk; the tampered Mach-O is refused with the PATH source named |
| `:1301` | `test_release_bundle_is_checked_in_the_built_executable_folder` (2) | SKIPPED "awaits lock" | `..._on_darwin` (2): build() takes the workflow's pair (`asset_url`, `seat_sha256`) from the committed lock, bundles into `Contents/MacOS`, fails on a bundle failure; a digest off the lock refused before PyInstaller |
| `:1356` | `test_notices_writing_follows_ffmpeg_and_fails_the_build_on_error` (2) | SKIPPED "awaits lock" | `..._on_darwin` (2): the complete census admits `--notices`; the stand-in writer sees the real bundling's tools and `ffmpeg-BUILD.txt`; a notice failure refuses before the seal (the writer is a stand-in: the `.app` notices are F0-2's) |
| `:1572` | `test_zip_is_published_only_after_successful_notices_and_smoke` (4) | SKIPPED "awaits lock" | `..._on_darwin` (4): notices -> seal -> smoke -> zip on the committed lock; stale zip removed first; the `.app` zip carries the notices |
| `:1662` | `test_release_zip_refuses_smoke_mutations` (3) | SKIPPED "awaits lock" | `..._on_darwin` (3): added / removed / changed after the snapshot refuse the zip |

On Windows the 13 Windows ids still pass (unchanged bodies); the 13 darwin ids pass. On the
runner: 13 Windows ids SKIPPED with the pointer reason (the parallel leg; the `-m macos`
allowlist is not involved), 13 darwin ids RUN. RED on the parent (lock and folder held out):
all 13 darwin ids fail.

### Other committed tests

- `test_the_real_macos_lock_pins_the_artifact_and_validates`: tag, fork commit, asset, URL,
  size, both digests and the census digest = `e3f251dc...`, census complete, run URL.
- `test_the_macos_component_texts_are_exactly_the_locks_and_rehash_to_it`: the folder holds
  EXACTLY the 36 names and each re-hashes to the lock; `..._refuses_a_damaged_texts_folder` (3:
  one byte, one missing, one extra -> refused by the validator).
- `test_the_real_macos_lock_refuses_each_transport_mutation` (13): the real lock with its
  transport moved to a synthetic zip (the seat zip is not in the repository): unmutated GREEN;
  size +1 / -1; `github_sha256` / `seat_sha256` digit 0 / 63; `all` (both digests and the census
  digest moved, a self-consistent lock) digit 0 / 63 -> "download sha256 mismatch; archive was
  not opened"; the `--ffmpeg-sha256` argument digit 0 / 63; plus `both` (the two digests only)
  digit 0 / 63 -> the census binding. 12 RED, 1 GREEN.
- The pin test (`test_release_workflow.py`
  `test_macos_release_build_reads_the_macos_lock_fields_and_the_switch_stays_off`): its "false"
  half KEPT; its "no lock" half FLIPPED to: the lock loads (validated), sits at
  `FFMPEG_MACOS_LOCK_PATH`, and its `asset_url` / `seat_sha256` are not hard-coded in the
  workflow.
- **CHARC's guard** `test_the_lock_with_the_switch_off_is_inert`: reads `macos-build.yml`
  statically (the existing `step` / `script` helpers): the switch reads exactly `"false"`;
  every step's `if:` is one of four known conditions (an unknown one is a violation); for each
  step that runs with the switch OFF, its text less the shell branches taken only on `"true"`
  names none of `--notices`, `--zip`, `--ffmpeg-from`, `--ffmpeg-sha256`, the lock path,
  `asset_url`, `seat_sha256`, `releases/download`, `curl`, `wget`, `gh release`,
  `hide_banner`, the asset name or the tag; the three release steps do not run; the OFF build
  command parses (`build.parse_args`) to `--form onedir` with no FFmpeg pair, no notices, no
  smoke, no zip; the capture step runs no bundled tool. Controls
  `test_the_switch_off_guard_sees_each_planted_breach` (4): switch flipped on, `--notices`
  planted in the OFF build, the release step's gate removed, the capture branch forced: each
  reported.
- `test_tools_package_notices.py` `_make_native_surface` / `omit_production_embedded_census`:
  the copied native surface leaves `ffmpeg-macos-components` to its lock as it does the
  Windows two. **Found by this turn's module run:** with the folder committed and the fixtures
  unchanged, `test_tools_package_notices.py` gave 76 passed, 344 errors and
  `test_tools_package_smoke.py` 51 passed, 15 errors (`PermissionError` unlinking the folder as a
  file); after: 420 passed and 66 passed, 1 skipped. Test-only.

### What the runner proves at the re-push (switch OFF)

- the parallel leg on darwin: the lock validates against the committed folder
  (`load_macos_ffmpeg_lock`, the 36 texts re-hashed on the runner's checkout), the transport
  family, the 13 C13 darwin ids natively (the real darwin bundling and origin walk included),
  the guard and the pin test;
- the build step runs `Build app bundle without FFmpeg` (no FFmpeg, no notices, no zip):
  nothing bundles, nothing downloads; the M leg on the `.app` runs as before with the FFmpeg
  families deselected;
- the G3 diagnostics still owed (C2 / C16 figures, the C3 / C4 / C5 / C7 / C9-C11 ids, A4).

### F0-2 carry-over (CHARC's re-stated condition 4; not this turn)

ONE commit, in the F0-2 group: the `.app`-aware Mac census (`notices._inventory` over
`Contents/MacOS`, `Frameworks`, `Resources`; a native manifest for the Mac host), the Mac
notices rows (the `_ffmpeg_rows` darwin branch, the write location `Contents/Resources`), the
C14 darwin counterparts (missing-member, smoke-after-notices), and `MACOS_FFMPEG_BUNDLED:
"true"` with the pin test's `"false"` half flipped.

### Counts at `02d07744` (`-p no:cacheprovider -n 3 --timeout 600 -m "not gpu" --basetemp=work\wp6.5\part3c\<module> -k 'not test_python_m_clearwater_starts_the_shell_and_exits_0'`)

Static: `ruff check .` All checks passed; `ruff format --check .` 338 files already formatted;
`mypy` Success 166; `mypy --platform darwin` Success 166.

| Module | Result |
|---|---|
| `tests/test_tools_package_build.py` | 667 passed (part 3b: 636; +31) |
| `tests/test_tools_package_notices.py` | 420 passed |
| `tests/test_tools_package_ffmpeg.py` | 290 passed |
| `tests/test_release_workflow.py` | 84 passed (79; +5) |
| `tests/test_tools_package_smoke.py` | 66 passed, 1 skipped (the POSIX process-group proof) |
| `tests/test_portability.py` | 192 passed |
| `tests/test_macos_portability.py` | 224 skipped (`macos` platform skip) |

RED on the parent (`tools/package/ffmpeg-macos.lock.json` and the folder held out, the rest of
the tree as committed): the 37 new or changed ids, 24 failed and 13 errors (the transport
fixture). `notices.py --root-annex --check`: root annex matches. **Windows unchanged**
(`windows_compare.py` against `git show 1ef10536:tools/package/build.py`): validators 33,
mismatches []; archive members 5, mismatches []; Windows-path definitions AST-identical to
`de3d68a0` 9 of 10 (`validate_ffmpeg_lock`, as at part 3b; `build.py` did not change this turn).

### Verification loop (self)

- Pass 1: every lock field against its source (above); every text against its source (above);
  the committed blobs against the draft (40 blobs, 0 unequal). Confirmed.
- Suspected: the committed folder breaks a consumer that copies `native-licences`. CONFIRMED
  (the notices fixtures; FIXED, test-only, counts above). Every other reader checked: `build.py`
  (the two path constants), `notices.py:1144` (the folder excluded), the workflow tests, the
  ffmpeg tests: green.
- Suspected: a darwin-host test changes behaviour now that the lock exists. REJECTED: the darwin
  build tests point `FFMPEG_MACOS_LOCK_PATH` at their own fixture; `smoke.py:854` reads the lock
  only when the tools are in the bundle; no `macos`-marked test reads the lock.
- Observation (not this turn's scope; for the dispatcher): the darwin origin walk judges a file
  native by suffix or magic (`build.py:3725` `_is_native`), so a NON-Mach-O file replacing
  `Contents/MacOS/ffmpeg` after placement is not an origin violation
  (`_is_native("ffmpeg", b"#!/bin/sh ...")` is False; a changed Mach-O IS refused, as the
  counterpart proves). Windows has the `.exe` suffix. The bundling check and the smoke's
  version read are the other guards.
- Pass 2 over the tests, the guard's controls and the blob check: nothing new. Loop ended.

Depth at part-3c yield: 273,035 (wp65-cell13, read by the dispatcher with cell_depth.py at its part-3c return)

## QA fix (`wp65-cell14`, dispatch-15; base `00e18e71`)

The seat's QA of `00e18e71` (parallel leg `work/orch-g63/gate-p00e1/`: 8981 passed, 209
skipped, 1 error) and A r6's two minors, fixed under CHARC's ruling `77c70316`. Scratch
`work\wp6.5\qafix\`. No `src/` change; no committed fixture, lock, text or notices-annex byte
moved; the workflow unchanged.

### The regression: cause as confirmed

- Reproduced on `00e18e71` with the seat's command, `uv run --no-sync pytest -q -p
  no:cacheprovider -p cupy "tests/test_portability.py::test_portability_cpu_selection[P23]"`:
  **1 passed, 1 error**, `AttributeError: 'function' object has no attribute 'cache_info'` at
  `tests\conftest.py:418` (teardown).
- Confirmed with `--setup-show` on the same id: `SETUP F monkeypatch`, `SETUP F
  _posix_home_redirect (fixtures used: monkeypatch)`, `SETUP F _release_fft_plans`, ...;
  teardown `_release_fft_plans` BEFORE `monkeypatch`. A4's fixture requested `monkeypatch` and
  so set it up ahead of `_release_fft_plans`; teardown is last-in, first-out, so `release()`
  read P23's lambda `_probe_gpu` before the undo. It reaches the probe only when `cupy` is in
  `sys.modules` (xdist order; `-p cupy` makes it deterministic). The seat's diagnosis holds.

### The fix (commits)

| Item | Commit | Change |
|---|---|---|
| (i) + (ii) + (iii) | `b1f0d507` | `tests/conftest.py`: `_posix_home_redirect(request)` requests nothing else; on POSIX its own `pytest.MonkeyPatch` sets `HOME` and `XDG_CONFIG_HOME` / `XDG_DATA_HOME` / `XDG_CACHE_HOME` / `XDG_STATE_HOME` (`POSIX_XDG_FOLDERS`: `.config`, `.local/share`, `.cache`, `.local/state` under the per-test home, not created, so the home stays empty), undone in a `finally` after the `yield`; on Windows it yields untouched. `release()` returns when `getattr(core_backend._probe_gpu, "cache_info", None)` is None. `tests/test_wp65_conftest_home.py`: the POSIX test asserts the four XDG paths and `app_locations()` under `.config` / `.cache` on Linux; new POSIX test: a test's own `monkeypatch` of `HOME` / `XDG_CONFIG_HOME` still wins; the Windows test also asserts the XDG names as collection found them. New `tests/test_wp65_conftest_order.py` (the ordering proof, below) |
| A r6 minor 1 | `cbe0a8b6` | `tools/package/build.py:1834` `isinstance(status, str)` first, then the set, then the linked rule (messages unchanged); `test_macos_complete_census_refuses` `status-list` / `status-dict` expect `ValueError` `zlib: invalid component status []` / `{}` |
| A r6 minor 2 | `be5fe211` | `tests/test_release_workflow.py`: `_off_reading` strips a switch-true `if ... fi` only when its inner lines hold no branching keyword (`if` / `then` / `else` / `elif` / `fi` / `case` / `esac` as a word); otherwise the step is reported `unsupported switch branch shape` and the block stays in the live text (conservative refusal, as ruled). The inert test asserts the real capture step has no refusal. Planted breaches added: `else-asset-download` (r6's executed probe: `else` + `curl <asset_url> -o /tmp/asset.zip` before the capture step's `fi`), `elif-arm`, `nested-branch`; each must report the refusal AND `curl ` |

The ordering proof: each class holds one test and a class-scoped sentinel, set up before and
torn down after every function-scoped fixture, which puts a stand-in `cupy` in `sys.modules`
(only when the real one is absent; nothing imported, no device). Class 1: the sentinel installs
a WITNESS probe, the test replaces it with a TRIPWIRE through `monkeypatch`; right order = the
undo restores the witness and `release()` reads its `cache_info` exactly once (checked after
the `yield`); wrong order = the tripwire raises. Class 2: a plain-function probe (P23's shape)
must be neither called nor raise. `--setup-show` on the fix: `_release_fft_plans` set up
before `monkeypatch`, torn down after it.

### RED on the parent / GREEN

| Proof | Parent | Fix |
|---|---|---|
| `-p cupy` `[P23]` (seat command) | `00e18e71`: 1 passed, 1 error (AttributeError, `conftest.py:418`) | 1 passed |
| `test_wp65_conftest_order.py` (conftest swapped to its `00e18e71` blob, `qafix\swap.py`, restored) | 2 errors at teardown: class 1 `_release_fft_plans ran before the test's monkeypatch undo` + `read the restored probe 0 times`; class 2 `AttributeError` at `conftest.py:418` | 2 passed (also 2 passed with `-p cupy`) |
| XDG redirect, simulated darwin (scratch probe copied into `tests/` for the run and deleted; `g3fix\sim\simdarwin.py` sets `sys.platform`) | 1 failed (`KeyError: 'XDG_CONFIG_HOME'`) | 1 passed (HOME under the basetemp, the four XDG paths under it) |
| minor 1 (`build.py` swapped to its `00e18e71` blob, `qafix\swap_minors.py`, restored) | 2 failed, `TypeError: unhashable type: 'list'` / `'dict'` at `build.py:1835` | 2 passed |
| minor 2 (the parent's strip-the-whole-block logic substituted in `_off_reading`, restored) | 3 failed (`else-asset-download`, `elif-arm`, `nested-branch`: `assert []`), 5 passed | 8 passed |

The Windows half of `test_wp65_conftest_home.py` cannot go RED on Windows (the parent left
`HOME` and the XDG names alone there too); the POSIX tests skip here by marker, so their
XDG assertions are proven on Windows only by the simulated-darwin probe above.

### Tests at the head (`-m "not gpu"`, every run with `-k 'not
test_python_m_clearwater_starts_the_shell_and_exits_0'`)

| Module | Result |
|---|---|
| `tests/test_portability.py` (`-n 3`) | 192 passed; with `-p cupy` 192 passed |
| `tests/test_release_workflow.py` | 87 passed (84; +3) |
| `tests/test_tools_package_build.py` | 669 passed (+2) |
| `tests/test_tools_package_ffmpeg.py` | 290 passed |
| `tests/test_tools_package_smoke.py` | 66 passed, 1 skipped (the POSIX process-group proof) |
| `tests/test_tools_package_notices.py` (`-n 3`) | 420 passed |
| `tests/test_macos_portability.py` | 224 skipped (`macos` platform skip); with `-p cupy` the same |
| `tests/test_wp65_conftest_home.py` | 1 passed, 3 skipped (POSIX-only, by marker; +1 POSIX test) |
| `tests/test_wp65_conftest_order.py` (new) | 2 passed; with `-p cupy` 2 passed |

Every other module that patches `_probe_gpu`, with `-p cupy -n 3`: `test_core_backend` 38,
`test_core_ops` 14, `test_core_prototype` 21, `test_core_select` 17, `test_core_speed` 20,
`test_core_wp34` 29, `test_wp321_device_frames` 9, `test_wp321_device_proxy` 2,
`test_methods_assembly` 73, `test_methods_assembly_prototype` 147, `test_methods_assembly_v8`
5, `test_methods_compensation` 211, `test_methods_fusion` 126, `test_methods_fusion_prototype`
94, `test_methods_white_balance` 97: all passed, none failed or errored.

Static: `ruff check .` all passed; `ruff format --check .` 339 files formatted; `mypy` and
`mypy --platform darwin` no issues in 166 source files. Blobs: 0 CR in each of the six
committed files.

### Verification loop (self)

- Pass 1. Suspected: the own-MonkeyPatch fixture breaks "a test that sets HOME itself wins".
  REJECTED: autouse setup precedes the test's `monkeypatch`, whose undo runs first and restores
  the redirect value, then the fixture's `finally` restores the original (new POSIX test).
  Suspected: the class sentinels' stand-in `cupy` leaks to other tests on the worker. REJECTED:
  class teardown runs in the one item's teardown, before the next item; the stand-in is
  installed only when no real `cupy` is loaded (`-p cupy` runs green). Suspected: the keyword
  scan refuses the real capture step (`-hide_banner`, `hevc_videotoolbox`, paths). REJECTED:
  the word match needs non-word, non-`-` boundaries; the inert test asserts no refusal.
  Suspected: a switch `fi` followed by `|| cmd` or at another indent escapes. REJECTED: the
  closer must be `fi` alone at the opener's indent, so such a block either does not match
  (all of it stays live) or swallows an inner `fi` (refused).
- Slip, fixed before any commit: a heredoc collapsed `\\n` in the release-test edit to a literal
  newline (the known Git Bash trap); repaired with the Edit tool, the diff re-read.
- Pass 2 over the three items and the tests: nothing new. Loop ended.

Depth at QA-fix yield: 122,607 (wp65-cell14, read by the dispatcher with cell_depth.py at its QA-fix return)

Re-gate on 69538abe (gen 63, work/orch-g63/gate-r6953/): parallel 8988 passed / 210 skipped; serial 1 failed / 1317 passed / 19 skipped = DR-96's THIRD recurrence (tests/test_gui_startup.py::test_shutdown_stops_every_worker_when_one_overruns_its_timeout, 3/3 alone); the gate STANDS (CHARC 77a42ff3).

## Run-2 fix (`wp65-cell15`, dispatch-16; base `69538abe`)

Runner run 2 (`42764505729`, on `69538abe`; macOS 26.7.2 arm64, ImageOS macos26, image
20261102.0473.1; validation mode, `MACOS_FFMPEG_BUNDLED` false) failed its parallel leg:
**4 failed / 7762 passed / 1227 skipped** in 187.6 s (run 1: 63 failed). The serial leg and
every bundle step were skipped. CHARC's rulings (`351a1c1c`) applied as given. No `src/`
change; no committed fixture, lock, text or notices-annex byte moved; `release.yml`
byte-identical; `MACOS_FFMPEG_BUNDLED` stays "false". Scratch `work\wp6.5\run2fix\`.

### The runner figures (the seat's table, `runner\run-42764505729\runner-table.md`)

| # | Test | Figure |
|---|---|---|
| 1 (C2) | `test_fixtures.py::test_stills_files_and_mask_regenerate_byte_identically` | 4 of 78 differ, all HEIC AD-24, decoded uint8 (shape per entry, `parallel.log:166-169`): `-both` (64, 96, 3) max 2 / p99 1 / nonzero 489; `-exif-only` (96, 64, 3) 2 / 1 / 489; `-irot-only` (64, 96, 3) 2 / 1 / 489; `-neither` (64, 96, 3) 3 / 1 / 555 (corrected at the A r8 fold: not all 64x96x3); libheif 1.23.6, x265 4.3+1-e9b8812, libde265 1.1.3 |
| 2 (C16) | `test_wp321_fft_gaussian.py::...bit_for_bit_cpu[shape1-32.0]` | max abs 1.788e-07, p99 5.96e-08, nonzero 102,925 of 6,236,289; inside 1e-5; control `FFT_BATCH_LINES=516` max 1.49e-07, nonzero 9,996, not bit-identical; numpy 2.5.4, scipy 1.18.1 |
| 3 | `test_jobs_export_process.py::test_an_exception_from_the_progress_kills_the_worker` | "the beat file stayed empty" (`:177`, read at `:1131`) after the worker kill |
| 4 | `test_tools_package_smoke.py::test_non_windows_containment_never_silently_skips` | expected `b: SURVIVORS`; got `b: native containment failed: [Errno 1] Operation not permitted` (SURVIVORS raised at `smoke.py:254`, then the cleanup's `killpg(pgid, 0)` at `:221` raised EPERM) |

### Commits

| Item | Commit | Files |
|---|---|---|
| 1 C2 | `7f554bc5` | `tests/test_fixtures.py` |
| 2 C16 | `641d1cb1` | `tests/test_wp321_fft_gaussian.py` |
| 3 beat | `0eeee5b3` | `tests/test_jobs_export_process.py` |
| 4 containment | `500dbea3` | `tools/package/smoke.py`, `tests/test_tools_package_smoke.py` |
| 5 workflow | `40d9b5d7` | `.github/workflows/macos-build.yml`, `tests/test_release_workflow.py` |
| 6 gui `:776` | `9b15e87a` | `tests/test_gui_settings_dialog.py` |

### Item 1: C2, the HEIC AD-24 bound (`7f554bc5`)

- `tests/test_fixtures.py:1402` `_pixel_figures` returns the printed figure plus the decoded dtype, max and p99; `_pixel_figure` (kept, same text) wraps it.
- `:1450` `HEIC_AD24_IDS` (the four ids), `HEIC_AD24_MAX_ABS = 4`, `HEIC_AD24_P99 = 1.0`.
- `:1465` `_regeneration_report(fresh_root, committed_root, host)`: on `win32` every entry byte-identical; on any other host the same except a HEIC AD-24 entry whose bytes differ passes when its decode is uint8 of the committed shape with max <= 4 and p99 <= 1. Returns `(compared, failures, bounded)`; a byte-identical entry still checks the manifest md5.
- `:1516` the regeneration test calls it with `sys.platform`; it prints the bounded rows (figures, "-- inside the non-Windows HEIC AD-24 bound ...") and fails on any failure row (an over-bound HEIC row says "-- OUTSIDE ..."); `compared == 78` and the file-set check unchanged.
- Proofs: `:1577` the committed tree passes on win32 / darwin / linux (78 compared, no rows); `:1585` a real re-encoded `heic-ad24-neither` (pixels inverted: max 255, p99 253) fails on darwin, linux AND win32; `:1612` `png8-gradient-none` with one pixel moved by 1 (`max 1, ... nonzero 3` = one pixel's three channels) fails on darwin and linux, no bound applied; `:1654` the edges on a stubbed decode, simulated darwin: max 4 with p99 1 (186 samples moved) passes as a bounded row, max 5 / p99 2 / a uint16 decode / a different shape fail; on win32 every plant fails.

### Item 2: C16, the tier-2 bound off Windows (`641d1cb1`)

- `tests/test_wp321_fft_gaussian.py:307` `NON_WINDOWS_REASON`: the 516-line control (a multiple of 4) is not bit-identical on the arm64 runner either (max 1.49e-07, nonzero 9,996), which settles that the difference comes from the library's FFT path (pocketfft SIMD on arm64), not the batch size.
- `:317` `_cpu_batch_verdict(..., host)`: bit-identical passes; on `win32` any difference fails (report + "host win32: the assertion is bit-for-bit"); elsewhere passes iff max abs <= `BOUND` (1e-5), the report (max / p99 / nonzero / control, `_batch_mismatch_report`) plus the verdict and the reason always printed.
- `:358` the CPU test uses it with `sys.platform`. `backend.py` untouched.
- `:392` proof by host: win32 equal passes, one ulp fails; darwin equal / one ulp pass, 2e-5 fails; linux one ulp passes, 2e-5 fails (7 cases).

### Item 3: atomic beats (`0eeee5b3`)

- `tests/test_jobs_export_process.py:66` `BEAT_WRITER`: `write_beat(beat, text)` writes `beat.tmp` in the same folder and `os.replace`s it onto `beat` (retrying a Windows `PermissionError` while a reader holds the old file, 200 x 1 ms, then once more unguarded).
- `:86` `GRANDCHILD` (Q11's grandchild) and the progress-raises child (`:1134`) both use it, including the first beat "0": the two writers share one shape.
- `:190` `_read_beat` keeps its retry; an empty file is still NOT a beat (docstring says why).
- **Hypothesis statement:** "the kill lands between `write_text`'s truncate and its write" is **NOT CONFIRMED**. The runner's log carries no kill timestamp or file mtime. The failure is made impossible by the atomic write, whatever the cause.
  - Supporting reading, not proof: the child sends the progress line and starts its next `write_text` right after, and that line is what triggers the kill. So the kill races that write, rather than a random point in the 50 ms loop.
  - Windows probe `work\wp6.5\run2fix\probe_race.py` (kill on reading the progress line; 300 runs per form): bare `write_text` left the file empty **0 of 300** (always "1", so no Windows repro). The atomic form left "0" in 14 of 300, which shows the kill does land inside the beat that follows the progress line, and never empty.
- **10 runs on Windows** (a loop; `-n 3`, `-m "not gpu"`): 84 passed in each of the 10 (8.47-9.24 s), 0 failed.

### Item 4: darwin containment (`500dbea3`)

`tools/package/smoke.py`:

- `:173` `GroupMember(pid, stat, comm)`.
- `:191` `_group_census(pgid, run=subprocess.run)`: `/bin/ps -A -o pid=,pgid=,stat=,comm=` (absolute, timeout 10 s), keeps the rows of `pgid` with zombies included. A failed `ps` or an unreadable line is a named `SmokeError`.
- `:237` `_live` = members whose stat does not start with `Z`; `_listing` = `pid <pid> <stat> <comm>` per member.
- `:309` `group_alive()`:
  - `ProcessLookupError` = empty.
  - `PermissionError` = the census decides: a live member raises "`<row>: process group <pgid> has a member this process may not signal (EPERM; members: ...)`"; no live member prints "`... answers EPERM with no live member (members: ...): contained`" and counts as contained.
  - The probe answering = the census counts the live members.
  - Any other exception propagates (`_process` names it "native containment failed").
  - Every SURVIVORS / "did not terminate" message carries `members: <listing>`.
  - The PASS line reads "0 live processes".
- `:845` darwin binds `census=_group_census`.

`tests/test_tools_package_smoke.py`:

- `FakeGroup` gains `census`, zombies, an EPERM / other-error probe and an unsignalable member.
- New tests:
  - `:1014` Lookup -> empty, no census.
  - `:1025` zombie-only contained, whether the probe answers or raises EPERM (the EPERM line printed).
  - `:1043` one live member beside a zombie -> SURVIVORS naming both.
  - `:1056` EPERM with a live member -> the named message with the listing, caused by the `PermissionError`.
  - `:1069` an `OSError(EIO)` propagates.
  - `:1088` the `ps` parse.
- The existing SURVIVORS / did-not-terminate regexes now carry the listing.
- The native darwin test (`:808`) asserts the survivor's pid is in row b's message and prints it.

**Hypothesis pending:** "EPERM from `killpg(pgid, 0)` on a group holding only zombies after the SIGKILL" stays a HYPOTHESIS until the next runner run. The runner's listing (row b's message, or the printed EPERM line) confirms it.

- If that listing shows a LIVE member after SIGKILL, that is a different defect and a STOP.
- Note: on the parent code, the stub zombie-only-EPERM case reproduces the runner's raw `PermissionError` exactly.

### Item 5: the workflow (`40d9b5d7`)

- `.github/workflows/macos-build.yml` conditions:
  - `:123` "Run serial tests" `if: ${{ !cancelled() }}`.
  - `:130` "Build app bundle without FFmpeg", `:143` "Run macOS tests on the built bundle" and `:175` "Capture runner and encoder facts" `if: ${{ !cancelled() && env.MACOS_FFMPEG_BUNDLED != 'true' }}`.
- Unchanged: no `continue-on-error` anywhere, the skip-reason check and every release-only step.
- **pipefail:** set by the job's `defaults: run: shell: bash` (`:44-46`; the comment at `:38-43` says so). For the named `bash` shell, Actions runs `bash --noprofile --norc -eo pipefail {0}`, so a failing pytest before `| tee` fails its step (run 2's job did fail on the parallel leg). The three test steps declare no `shell:` of their own.
- The facts capture needs nothing from the skip-reason check, so neither moves: no STOP.
- Reading noted: the serial condition is the ruling's verbatim `!cancelled()`. In release mode a failed earlier step therefore also runs the serial leg, but the job still fails and the release-only steps keep their default `success()` gate. With the switch "false" the version step refuses release mode anyway.
- `tests/test_release_workflow.py`:
  - `:975` `MACOS_STEP_CONDITIONS`, every step's exact `if:`.
  - `:1016` `_validation_violations` reports a condition off the map, any `continue-on-error`, a test step with its own `shell:` or without `| tee`, the job's bash default missing, or release.yml's text sha256 other than `dd91eae3...` (69538abe).
  - `:1043` asserts none.
  - `:1065` five planted breaches, each reported.
  - `:1273` `SWITCH_GATES` admits the two new conditions (both run with the switch "false"). The inert-lock guard still passes with "Build app bundle without FFmpeg" run and the release steps not run.
  - The build-gate test reads the new condition.
- actionlint NOT run (the seat runs it).

### Item 6: `test_gui_settings_dialog.py:776` (`9b15e87a`)

- `tests/test_gui_settings_dialog.py:57` `WINDOWS_ROSTER = capability.encoder_roster("win32")`.
- `:779` `resolve_encoder("auto", capabilities, roster=WINDOWS_ROSTER) == default`, then `default != resolved` (as C4).

### RED on the parent / GREEN

| Proof | Parent `69538abe` | Head |
|---|---|---|
| 1 C2 new tests | collection-level: `_regeneration_report` absent (no host rule exists; the parent's test is byte-identity on every host, so run 2 itself is its darwin RED) | 12 passed; module 370 passed (358 + 12) |
| 2 C16 new tests | `_cpu_batch_verdict` absent (the parent asserts bit-identity on every host; run 2 is its darwin RED) | 7 passed; module CPU 26 passed (19 + 7) |
| 3 beats | no Windows RED: the bare form passes on Windows, and the probe gave 0 / 300 empty | 10 x 84 passed |
| 4 stubs (`red_smoke.py`: parent `smoke.py` swapped in, `run_group` passing `census` only when accepted; restored, `git status` clean) | 10 failed, 11 passed: zombie-only (answers) -> SURVIVORS / did not terminate; zombie-only EPERM -> raw `PermissionError` (the runner's failure); survivor beside zombie -> wrong message; EPERM with a live member -> raw `PermissionError`; census parse / binding absent; the four reworded messages lack the listing. Guards passing on the parent too: Lookup -> empty, other `OSError` propagates, own-group refusals | 73 passed, 1 skipped (66 + 7; the skip = the native POSIX proof) |
| 5 workflow (parent `macos-build.yml` swapped in, restored) | 3 failed: the new guard (4 condition rows), the build-gate test, the inert-lock guard (the old condition is no longer admitted) | 93 passed (87 + 6) |
| 6 gui `:776`, simulated darwin (`run2fix\sim\simdarwin2.py`: imports `urllib.request` first, since on darwin it imports `_scproxy`, absent here, then sets `sys.platform`) | 1 failed (`injected-enables-ten-bit`: `'libx265' == 'hevc_nvenc'`), 1 passed | 2 passed; Windows parent 2 passed, head module 95 passed |

### Static and tests at the head (`9b15e87a`; `-m "not gpu"`, every run with `-k 'not test_python_m_clearwater_starts_the_shell_and_exits_0'`)

Static: `ruff check .` all passed; `ruff format --check .` 339 files formatted; `mypy` and
`mypy --platform darwin` no issues in 166 source files. Blobs 0 CR (counted in Python).

| Module | Result |
|---|---|
| `tests/test_fixtures.py` (`-n 3`) | 370 passed |
| `tests/test_wp321_fft_gaussian.py` | 26 passed, 17 deselected (gpu) |
| `tests/test_jobs_export_process.py` (`-n 3`) | 84 passed (and 10 x 84 in the loop) |
| `tests/test_tools_package_smoke.py` | 73 passed, 1 skipped |
| `tests/test_release_workflow.py` | 93 passed |
| `tests/test_gui_settings_dialog.py` (`QT_QPA_PLATFORM=offscreen`) | 95 passed |
| `tests/test_tools_package_build.py` (`-n 3`) | 669 passed |
| `tests/test_tools_package_notices.py` (`-n 3`) | 420 passed |
| `tests/test_macos_portability.py` | 224 skipped (platform) |
| `tests/test_wp65_conftest_home.py` | 1 passed, 3 skipped |

### Verification loop (self)

Pass 1:

- **Suspected:** the HEIC bound admits a 10-bit or reshaped decode. REJECTED: uint8 and the committed shape are required (the uint16 and shape plants fail).
- **Suspected:** p99 at exactly 1 is an interpolation artefact. Checked: with 18,432 samples, p99 sits between sorted indices 18,246 and 18,247. 185 moved samples gave 0.69, so the edge plant moves 186 to land exactly on 1.
- **Suspected:** `os.replace` fails on Windows while `_read_beat` holds the file. HANDLED: the writer retries `PermissionError`. The 10-run loop and the Q11 grandchild test stay green.
- **Suspected:** the cleanup's census raising inside `finally` hides the first error. ACCEPTED as is: it raises only a named `SmokeError` (EPERM with a live member) or an un-named `OSError`, never a pass.
- **Slips, fixed before commit:**
  - A heredoc collapsed `\\n` / `\\0` (the known Git Bash trap). This left a NUL byte in `test_fixtures.py` and broke f-strings in the FFT test. Repaired, then NUL and CR counts checked.
  - `test_jobs_export_process.py` was checked out CRLF (1,392 CR) and normalised to LF before commit (HEAD blob 0 CR).
  - The workflow comment first said "continue-on-error", which the existing guard rightly refused; it was reworded.
- **Found, NOT fixed (out of this turn's scope; the dispatcher's):** the whole `test_gui_settings_dialog.py` under simulated darwin gives 2 more failures: `test_cache_job_errors_are_not_presented_once_the_main_window_closes[window-closing / window-open]` (presented-message lists differ). This may be a simulation artefact (on Windows `Path.home()` ignores HOME) or a real serial-leg darwin row; the next runner run's serial leg will say. No write under `C:\Users\rwsmy\Library` (checked: absent).

Pass 2 over the six items and the tests: nothing new. Loop ended.

Depth at run-2-fix yield: 207,998 (wp65-cell15, read by the dispatcher with cell_depth.py at its run-2-fix return)

### Fold (A r8)

Reviewer A r8 on `2e98ca1c`: 1 MAJOR, 1 MINOR; CHARC's corrected ruling `7910e7df`. Commit
`bdf369ee` (`.github/workflows/macos-build.yml`, `tests/test_release_workflow.py`) and this
ledger. Only `tests/test_release_workflow.py` was run.

**MAJOR (A r8, `macos-build.yml:143` at `2e98ca1c`):** the continuation keyed on the bundling
switch skipped "Run macOS tests on the built bundle" with the switch ON. That step is the only
producer of `work/evidence/macos.log`, which "Check macOS skip reasons" reads, so a successful
release run would fail. The fault is in the ruling's wording.

**Fix.** The mode is `inputs.release-version`, set only by release.yml's `workflow_call`.

- These four steps now carry `if: ${{ success() || (!cancelled() && !inputs.release-version) }}` (`!inputs.release-version`, not `== ''`):
  - "Run serial tests" (`:125`);
  - "Run macOS tests on the built bundle" (`:145`);
  - "Check macOS skip reasons" (`:161`, which had no `if:` before);
  - "Capture runner and encoder facts" (`:178`).
- "Build app bundle without FFmpeg" keeps `${{ !cancelled() && env.MACOS_FFMPEG_BUNDLED != 'true' }}` (`:132`).
- In release mode every step runs under `success()`, as at `69538abe`.
- The job comment (`:38-46`) is rewritten.
- No `continue-on-error` anywhere; release.yml untouched (its sha256 is still pinned).

**Guard** (`tests/test_release_workflow.py`):

- `:975` `MACOS_STEP_CONDITIONS`: the new exact map.
- `:1079` `evaluate_if`: a small recursive-descent evaluator over `success()`, `cancelled()` (always false here), `always()`, `env.X`, `inputs.X`, string literals, `!`, `&&`, `||`, `==` / `!=` (string vs string, case-insensitive), and parentheses.
  - GitHub's implicit `success() &&` applies when no status function appears; no `if:` = `success()`.
  - Any other function, context, operator, literal, a non-string comparison or a broken wrapper raises `UnknownExpressionError`: conservative refusal.
  - Qualified at the A r9 fold: the guarantee holds with GitHub's precedence (`!` over `==` / `!=` over `&&` over `||`), which `eeefd4cf` did not have. A comparison with a boolean or null operand (e.g. `!env.X == 'false'`) and a chained comparison are refused, not coerced.
- `:1232` `_walk` evaluates the REAL `if:` of every step in order; a reached step fails only if it is the case's failing step.
- `:1244` `_mode_violations` reports a reached list other than `MODE_REACHED`, or a reached step that reads `macos.log` before any reached step produced it (`tee work/evidence/macos.log`).
- `:1275` the four cases:
  1. release, all success: everything but the build without FFmpeg, with the bundle tests (the producer) before the skip-reason check (the reader), and staging and upload reached;
  2. release, a failed parallel leg: only "Upload evidence" after it, as at `69538abe`;
  3. validation, switch off, a failed leg: serial, the build without FFmpeg, the bundle tests, the skip reasons, the facts, the evidence upload;
  4. validation, switch on, a failed leg: the same without the build, and NOT staging or upload.
- `:1286` the control: `2e98ca1c`'s conditions rebuilt in the text fail case 1 with "Check macOS skip reasons reads work/evidence/macos.log before any reached step produced it".
- `:1327` nine refused forms: `failure()`, `github.ref`, `steps.*`, `contains(...)`, `null`, `>`, a dangling `||`, an unclosed `(` and a broken `${{ }`.
- `:1349` ten known-form evaluations.
- `:1368` the planted-breach controls, re-aimed: "capture-keyed-on-the-switch" plants the A r8 form.
- `:1576` `SWITCH_GATES` admits the new condition (it runs with the switch "false").

**RED on `2e98ca1c`** (its `macos-build.yml` swapped in, restored, `cmp` equal):
`test_both_modes_reach_the_ruled_steps_by_evaluation` 4 failed:

- (1) release-all-success: missing the bundle tests and the facts, AND the skip-reason check reads `macos.log` before it is produced (the MAJOR).
- (2) release-failed-leg: extra "Run serial tests". `2e98ca1c`'s bare `!cancelled()` ran the serial leg in release mode after a failure, unlike `69538abe`.
- (3) validation-off-failed-leg: missing the skip-reason check.
- (4) validation-on-failed-leg: missing the bundle tests, the skip-reason check and the facts.

**GREEN at `bdf369ee`:** `tests/test_release_workflow.py` 117 passed (93 + 24: four cases, one control, nine refusals, ten known forms).

**MINOR (A r8, ledger `:2417`):** the four HEIC entries are not all 64x96x3; `heic-ad24-exif-only` decoded as (96, 64, 3) (runner `parallel.log:167`). The runner-figures row now gives each entry's shape. The code was right: the bound requires the committed shape per entry, never 64x96x3.

**Static:**

- `ruff check .` all passed.
- `ruff format --check .` 339 files already formatted.
- `mypy` and `mypy --platform darwin` no issues in 166 source files.
- Blobs 0 CR.
- actionlint not run (the seat's).

**Verification (self):**

- Suspected: a push run's `inputs` context is empty and `workflow_dispatch` defines no `release-version`. Both read as null, so `!inputs.release-version` is true. That is validation mode, as intended.
- Suspected: release mode with the switch OFF (refused by the version step) still runs the build without FFmpeg after that failure. True, and it is the ruling's unchanged condition: the job fails at the version step either way, and no release asset is staged.
- Nothing new on a second pass.

#### A r9 minor

A r9 on `eeefd4cf` found no critical or major issue and passed CHECKs 1 and 3-6. Its one MINOR: `evaluate_if` gave comparisons precedence over `!`, so `!env.X == 'false'` with X = 'true' evaluated True, whereas GitHub reads `(!'true') == 'false'`.

- **Fix** (`58596e3b`, `tests/test_release_workflow.py` only): the grammar is now or -> and -> comparison (`:1142`, its operands from `negation`) -> unary (`:1154`, `!` unary | primary) -> primary. Under the string-only comparison policy, a boolean operand raises `UnknownExpressionError` ("compares False with 'false'").
- **New tests:**
  - `:1338` the reviewer's expression, bare and wrapped, must raise.
  - `:1347` `!(env.X == 'a')`, bare and wrapped, evaluates correctly: X = 'a' / 'A' -> False, 'b' -> True, and False after a failed step (implicit `success()`).
- **Results:** the four mode cases, the A r8 control and every earlier evaluator case pass unchanged. `tests/test_release_workflow.py` 122 passed (117 + 5).
- **RED at `eeefd4cf`:** `eeefd4cf`'s `evaluate_if` was swapped into the head file for one run, then restored (`cmp` equal). 2 failed (both must-raise cases, `DID NOT RAISE`), 27 passed: the parenthesized case, the four mode cases, the control and the earlier evaluator cases.
- **Static:** `ruff check .` all passed; `ruff format --check .` 339 files already formatted; `mypy` and `mypy --platform darwin` no issues in 166 source files. Blobs 0 CR.

Depth at A-r8-fold yield: 239,708 (wp65-cell15, read by the dispatcher with cell_depth.py at its A-r8-fold return)

Depth at A-r9-fold yield: 251,366 (wp65-cell15, read by the dispatcher with cell_depth.py at its A-r9-fold return)

## Run-3 fix (`wp65-cell16`, dispatch-17; base `a93a0ab7`)

Runner run 3 (`42781244075`, on `a93a0ab7`; macOS 26.7.2 arm64, ImageOS macos26, image
20261102.0473.1; validation mode, `MACOS_FFMPEG_BUNDLED` false): parallel **0 failed / 7827
passed / 1227 skipped** (248.5 s); serial **15 failed / 518 passed / 784 skipped** (134.9 s);
the bundle build without FFmpeg FAILED at the one-hop link rule (`build.log:115`, after
BUNDLE completed and signed); the bundle's macOS tests **1 failed / 133 passed** (65.1 s);
the skip-reason check failed as a consequence. CHARC's rulings `d6981092` applied as given.
No `src/` change; `release.yml` byte-identical (its pinned sha256 test passes);
`MACOS_FFMPEG_BUNDLED` stays "false"; `notices.py`, the debt register, the C14 rows, the
committed fixtures and the Windows notices annex untouched. Scratch `work\wp6.5\run3fix\`.

### Commits

| Item | Commit | Files |
|---|---|---|
| 1 S1 FFmpeg guards | `3c4c0a15` | `tests/test_app_leftovers.py`, `tests/test_app_startup.py`, `tests/test_reviewpack.py`, `tests/test_wp321_bench.py` |
| 3 S3 settings cache jobs | `4f236be1` | `tests/test_gui_settings_dialog.py` |
| 2 S2 GPU pack lock skip | `40296214` | `tests/test_gui_gpu_pack_dialog.py` |
| 4 (b) `.app` link chain | `27d443a1`, `cb37f6d3`, `85f2739d` | `tools/package/build.py`, `tests/test_tools_package_build.py` |
| 6 + 7 workflow | `bfccb8e6`, `1e275359` | `.github/workflows/macos-build.yml`, `tests/test_release_workflow.py` |
| 5 T14 cleanup | `f6c84722` | `tests/test_macos_portability.py` |
| 8 census file | `725423a4` | `tests/test_tools_package_smoke.py` |

Items 6 and 7 share one commit (both edit the one workflow file and its one test module).
`cb37f6d3` adds the junction case; `85f2739d` and `1e275359` are the verification pass's
fixes (below).

### Item 1: S1, FFmpeg absent (`3c4c0a15`)

- **Anchor drift:** `test_start_up_never_scans_a_folder_because_a_source_lies_there` lives
  in `tests/test_app_leftovers.py:416`, not `tests/test_app_startup.py` (runner
  `serial.log:46`, `tests/test_app_leftovers.py:430`). Guarded there; test-only, as ruled.
- The existing session fixture `ffmpeg_tools` (`tests/fixture_plugin.py:274`, reason
  `SKIP_NO_FFMPEG` at `:47`) is the one guard; no second helper.
  - `tests/test_app_leftovers.py:416` and `tests/test_app_startup.py:138`
    (`..._keeps_only_the_latest_analysis`): `@pytest.mark.usefixtures("ffmpeg_tools")`;
    each test is wholly video.
  - `tests/test_app_startup.py:377` (`test_a_failed_cache_open_is_shown_once_and_photos_still_work`):
    **the photo half still runs**; `request.getfixturevalue("ffmpeg_tools")` sits just
    before the clip is opened, so the start-up warning and the photo export are asserted
    without FFmpeg and only the video half (and the closing once-only count) skips. No
    rewrite was needed.
  - `tests/test_reviewpack.py:954` (`test_all_tiny_set`): whole-test guard; one `build.main`
    call exports the photos and the clip together, so a partial guard would be a rewrite.
  - `tests/test_wp321_bench.py:52` (the `gpu` test): whole-test guard.
- **RED on the parent** (`a93a0ab7`'s four files swapped in, restored, `cmp` equal; FFmpeg
  dropped from PATH by removing `WinGet\Links`): 4 failed (`test_app_startup.py:120` x3 with
  "ffprobe was not found on the PATH", `test_reviewpack.py:998` with `failed=1`) and the bench
  test 1 failed (`VideoProbeError`, `probe.py:116`): run 3's five failures, line for line.
- **GREEN, FFmpeg dropped:** the five SKIP with "ffmpeg and ffprobe are not on the PATH
  (needed to generate or probe video)". **Normal PATH:** the four non-GPU tests 4 passed.
- The bench test is `gpu`-marked; its skip proof ran with FFmpeg dropped AND
  `CUDA_VISIBLE_DEVICES=-1`, so the fixture skipped at setup and nothing reached a device.
  It was not run with the normal PATH (no GPU test at a cell).

### Item 2: S2, the GPU pack lock (`40296214`, test-only)

- `tests/test_gui_gpu_pack_dialog.py:53` `lock_gap(tags=None)`: for
  `gpu_pack.platform_tags()` (or the given pair) a locked distribution none of whose
  wheels has a tag that `gpu_pack.tag_fits` (expanded by `gpu_pack_install._wheel_tags`,
  the expansion `plan()` uses at `gpu_pack_install.py:158-163`) gives "GPU pack lock carries
  no wheels for `<os>/<machine>` (`<distribution>`; tags `<interpreter>`, `<platform>`)".
  More than one fitting wheel is a lock defect, not a gap, so it does not skip.
- `:36` `_PLATFORM_TAG` / `_platform_words`: the words come from the tag
  (`macosx_14_0_arm64` -> `darwin/arm64`, `win_amd64` -> `win32/amd64`,
  `linux_x86_64` -> `linux/x86_64`); never `sys.platform`.
- `:86` `require_locked_wheels()`, `:94` fixture `locked_wheels`; applied to the seven
  tests (`usefixtures` at `:168`, `:187`, `:210`, `:226`, `:294`, `:327`, `:337`) and, in
  `test_pending_reason_clears_after_marker_is_gone`, only to the `install` branch (`:389`).
  Every other test keeps running without the lock.
- `:517` `test_the_lock_decides_the_skip_as_plan_does` (5 cases): cp312 win_amd64 and
  cp312 linux_x86_64 -> no skip AND `plan()` succeeds; macosx_14_0_arm64,
  macosx_15_0_x86_64 and cp313 win_amd64 -> the exact reason AND `plan()` raises
  "cupy-cuda12x: 0 compatible locked wheels" AND `require_locked_wheels()` skips.
- **RED on the parent** (scratch plugin `run3fix\sim\simmac_tags.py` sets
  `platform_tags` to `("cp312", "macosx_14_0_arm64")`; the parent file swapped in,
  restored): **8 failed, 16 passed**, exactly run 3's eight.
- **GREEN, same plugin:** 21 passed, **8 skipped** with "GPU pack lock carries no wheels for
  darwin/arm64 (cupy-cuda12x; tags cp312, macosx_14_0_arm64)". **Real Windows:** 29 passed
  (24 + 5), none skipped.

**What a Mac user sees TODAY (read from the code; no GUI launched):**

- `gpu_pack.pack_root()` returns None on darwin (`gpu_pack.py:421`).
- `MainWindow._update_gpu_actions` (`shell.py:513`) then hides AND disables both "Install GPU
  support..." and "Remove GPU support" (`shell.py:538-541`); the Tools menu shows only
  Settings. `_open_gpu_pack` (`:548`) and `_confirm_gpu_remove` (`:560`) return at once when
  `pack_root()` is None. The idle "Tools > Install GPU support..." tooltip needs a pack root
  (`shell.py:669`).
- Were the dialog built, it raises "GPU support is not available on this platform" before
  `plan()` (`gpu_pack_dialog.py:126`) and catches `plan()`'s `ValueError` into its status
  line with Install disabled (`:143-145`): no exception dialog, no traceback.
- Headless `--install-gpu-pack` (`__main__.py:463`): `install()` prints the licence text,
  then returns "GPU support is not available on this platform" (`gpu_pack_install.py:665-667`)
  before `plan()`.
- So `plan()` is never reached on darwin in the product. The eight tests reached it only
  because their autouse `isolated_pack` fixture monkeypatches `pack_root` to a temporary
  folder (a supported platform), on a host whose tags the lock does not carry.
  `test_platform_visibility_and_idle_hint[False]` (`:280`) pins the hidden actions and
  passed on the runner.

**Debt row, for the follow-on product package (DR number: CHARC assigns at the accept):**
"On macOS the GUI offers the GPU pack menu and dialog, and `gpu_pack_install.plan()` raises
`cupy-cuda12x: 0 compatible locked wheels` (`gpu_pack_install.py:165`); the pack is None by
design on macOS (brief), but the product does not say so." Must be fixed before the 1.2.0
macOS release.
S2 premise refuted at the seat and by CHARC; no DR row; no product package (CHARC c1c14926).

### Item 3: S3, settings cache-job errors (`4f236be1`, test-side)

**Diagnosis: NOT a product race; an environment difference in how the test drives the
dialog.**

- `cpu_settings()` stores `video_encoder="libx265"` (`tests/test_app_startup.py:65`).
- Without FFmpeg the sink reports every encoder unavailable ("ffmpeg was not found on the
  PATH"), so `_encoder_unacceptable` (`settings_dialog.py:656`; its D74 table: "a name |
  reported, unavailable | stored or picked | refused") refuses the stored libx265.
- `_refresh_ok` disables OK (`settings_dialog.py:699`), and `dialog.ok_button.click()` on a
  disabled button does nothing: `accept()` never runs and no limit job is queued.
- `window.jobs.active() >= 2` still held: the slow, failing cache open is itself a start-up
  job (`app/main.py:201`), plus the clear.
- Hence one `job failed` line, only "The cache could not be cleared:", and `[window-open]`
  reaching `jobs.active() == 0`. The product follows its documented rule; nothing is
  dropped.
- Trace (scratch `run3fix\sim\diag_s3.py` under simulated darwin): `refresh_ok
  enabled=False ... enc='libx265' ... caps=[('hevc_nvenc', False, 'ffmpeg was not found on
  the PATH...'), ('libx265', False, ...)]`; `accept` never called.

**RED on the parent, deterministic (no timing):** on real Windows with FFmpeg dropped from
PATH, both params fail exactly as on the runner: `[window-closing]` at `:1435`;
`[window-open]` at `:1437` ("Right contains one more item: 'The cache limit could not be
set:'"). Simulated darwin also reproduces them (the run-2 ledger's open item).

**Fix (test only):**

- `tests/test_gui_settings_dialog.py:1413` stores `module.AUTO` ("auto": allowed whatever
  the sink reports).
- `:1423` asserts OK is enabled (showing the encoder note if not).
- `:1425` asserts the dialog was accepted.
- `:1427` asserts `jobs.active() >= 3` (the open, the clear and the limit).
- The test's assertions about presented and logged errors are unchanged.

**GREEN:** 2 passed with FFmpeg dropped, with the normal PATH and under simulated darwin. The
whole module: 95 passed in each of the three (Windows unchanged).

### Item 4: (b) the `.app` link chain (`27d443a1`, `cb37f6d3`, `85f2739d`)

`tools/package/build.py`:

- `:4259` `_MACOS_LINK_HOPS = 8`.
- `:4263` `_not_posix_relative` (today's text test, shared).
- `:4268` `_macos_link_chain_problem(root, physical)`: inside a `.app`, hop by hop:
  - each hop's text is relative POSIX;
  - each hop lands (parent resolved physically, the final name kept) inside the real
    `Contents`;
  - no hop repeats (loop);
  - a junction refuses;
  - the end is an existing regular file;
  - at most 8 hops.
  Refusals read "link chain `<reason>`: `<hop>` -> `'<text>'`; ...; `<end>`", every hop
  named.
- `_macos_link_class_problem` (`:4336`): when `root` is a `.app` (`:4347`) and the target is
  a link, the chain decides first. Then today's outside / dangling checks run on the final
  target, then the class (framework / B / C) is read on it. Outside a `.app` a link to a
  link still returns "link to a link (one hop only)" (`:4358`), byte for byte.
- Still THE one function, shared by the origin check, the ZIP and the notices. The
  docstring (`:4404` onward) states the chain reading.

`tests/test_tools_package_build.py`:

- `:2585` `PYSIDE_LIB`.
- `LINK_CASES`:
  - `C-app-pyinstaller-chain` (`:2678`): Resources -> Frameworks B link -> file,
    ADMITTED. Run through the origin walk and the ZIP.
  - `onedir-two-hop-chain` (`:2687`): refused with today's message. Run through the origin
    walk, the ZIP and the notices.
  - **`C-app-link-to-a-link` (`:2669`) is now ADMITTED** (MacOS -> Frameworks -> Resources
    file, all inside Contents, ending in a file): the ruling's change, so its expectation
    moved from "link to a link (one hop only)" to admitted.
- Dedicated tests:
  - `:2846`: the PyInstaller chain admitted per link and by the origin walk.
  - `:2856`: the onedir two-hop line pinned whole:
    `native origin: linked file <path>: link to a link (one hop only)`.
  - `:2936` `CHAIN_REFUSALS` (5): out of the release; out of `Contents` but inside the
    `.app`; dangling; a loop; a folder end. Each checks the reason and every hop in order.
  - `:2952`: 8 hops admitted, 9 refused with all hops.
  - `:2971`: an absolute second hop.
  - `:2993` (win32): a junction hop.
  - `:3016` (win32): a link handed over as its real path under an aliased root.

Symlinks are available at this seat: **0 skipped**. Module 686 passed (669 + 17); notices 420
passed.

**RED on the parent** (`a93a0ab7`'s `build.py` swapped in, restored, `cmp` equal; `-k "link or
chain"`): **13 failed, 116 passed**. Failing:

- the accepted shape `C-app-pyinstaller-chain` in the origin walk, the ZIP and the dedicated
  test ("link to a link (one hop only)", run 3's refusal);
- `C-app-link-to-a-link` in the origin walk and the ZIP;
- both bound cases;
- the five refusals and the absolute hop: the parent refuses them too, but with one-hop or
  dangling text instead of the chain.

The onedir two-hop tests PASS on the parent: the unchanged message. The junction test fails
on the parent the same way ("link to a link (one hop only)").

**GREEN:** `-k "link or chain"` 131 passed.

### Item 5: T14's exFAT cleanup (`f6c84722`)

- `tests/test_macos_portability.py:1149` `_vanished_entry(function, path, error)`: swallows
  exactly `FileNotFoundError` from `os.unlink` (a listed non-folder entry, `shutil`'s
  `onexc(os.unlink, fullname, err)`); every other error, and a `FileNotFoundError` from any
  other call (the folder's own `rmdir`, `lstat`, `scandir`), is re-raised.
- `:1183` `shutil.rmtree(root, onexc=_vanished_entry)`; T14's assertions unchanged.
- Unit checks:
  - `:1350`: swallow vs five propagating cases; the same exception object re-raised.
  - `:1366`: a simulated exFAT pair (unlinking either file removes its partner). Plain
    `rmtree` raises run 3's `FileNotFoundError` (the parent's cleanup, the RED form); with
    the `onexc` the folder is gone.
- The module is darwin-only: on Windows it collects 226, all skipped (224 + 2), as before.
  The two unit checks were run on Windows by lifting the module's skips for them alone
  (scratch plugin `run3fix\sim\unskip_mac.py`): 2 passed.
- Parent RED: collection-level (`_vanished_entry` absent). Run 3 is the parent's darwin
  RED.

### Item 6: the skip-reason check's summary reading (`bfccb8e6`)

- `.github/workflows/macos-build.yml:198`: `SUMMARY` matches any pytest summary
  (`<n> <word>` parts in any order, then ` in <seconds>s`, optional `=` banner). The LAST
  summary is read into counts.
- `:208`: any failed or error count fails: "macOS leg: `<f>` failed, `<e>` errors:
  `<parts>`".
- No summary at all, or no passed count, also fails, each saying so.
- The skip allowlist is unchanged; the success line is "macOS leg: `<n>` passed; `<k>`
  skipped, all allowed".
- Kept inline: the workflow has no tested module home.
- `tests/test_release_workflow.py`:
  - `:1562` `RUN_SUMMARIES`: the four real lines, copied as literals from run 2
    `parallel.log:1254` and run 3 `parallel.log:887`, `serial.log:930` and `macos.log:102`.
  - `:1595`: the step's REAL script run on each line; the passed count is read and printed,
    and a failed count fails with its words.
  - `:1625`: seven synthetic orders (skipped first, warnings, banner, an error, errors first,
    nothing passed, no tests ran).
  - `:1630`: an off-allowlist reason is still refused under a reordered passing summary.

### Item 7: the listing step (`bfccb8e6`, `1e275359`)

- `.github/workflows/macos-build.yml:137` "List the app bundle", right after "Build app
  bundle without FFmpeg", with `if: ${{ !cancelled() && !inputs.release-version }}`
  (CHARC's form; the A r8 / A r9 evaluator reads it unchanged).
- It writes `work/evidence/app-listing.txt`, inside the existing `Upload evidence`
  `path: work/evidence/`, so no path change. The listing holds:
  - `find <app> -ls` (a failure recorded, not fatal: `1e275359`);
  - `otool -L` over every regular file whose `file -b` starts with `Mach-O`. The check is
    by type, never by name, so the extensionless `Contents/MacOS/Clearwater` counts.
- A missing `.app` writes "No app bundle at `<app>`: nothing to list." and exits 0.
- No `continue-on-error` anywhere; release mode never reaches the step.
- `tests/test_release_workflow.py`:
  - `:976` `VALIDATION_ONLY`; `MACOS_STEP_CONDITIONS`, the step order, `MODE_REACHED`
    (both validation cases) and `SWITCH_GATES` gain the step.
  - `:1645`: the step pinned (position, `if:`, env, the commands, by type not name, the
    upload path).
  - `:1697`: the evaluated-condition table. Validation (no input / empty input; ok or
    after a failure) RUNS. Release (`1.2.0`; ok or after a failure) does NOT. Each for
    both switch values.

**RED on the parent** (items 6-7; `a93a0ab7`'s workflow swapped in, restored): **20 failed,
120 passed**:

- the step order, the condition map and both validation mode cases;
- the four real summaries: run 3's `1 failed, 133 passed` gets "no passing summary line"
  instead of the failed count, and run 3's parallel line passes but prints the old words;
- five of the seven orders (e.g. "2 skipped, 133 passed" refused);
- the reordered allowlist case;
- the listing pin and its five condition rows.

**GREEN:** module 140 passed (122 + 18).

### Item 8: the darwin containment census to a file (`725423a4`)

- `tests/test_tools_package_smoke.py:770` `CENSUS_FILE` =
  `work/evidence/containment-census.txt`, inside the evidence upload.
- In `test_non_windows_containment_never_silently_skips`, on darwin only (Windows and Linux
  return before it, as today):
  - `:866`: the real `os.killpg` and the smoke's own `_group_census` are wrapped to record,
    per 0-signal probe, its outcome (`ProcessLookupError` / `PermissionError` / answered)
    and the live count and `_listing` of the census that followed. No second census runs;
    the smoke still decides.
  - The lines the smoke printed are taken from `capsys` (re-emitted to stdout).
  - In a `finally`, so a failing row still leaves it, `:905` writes `census_text`: one line
    per probe naming its branch (`census_branch` `:775`: "ProcessLookupError (empty
    group)", "EPERM with no live member", "SURVIVORS (a live member)", "answered, no live
    member", "EPERM with a live member") with the listing, then the printed lines.
- `:814` `test_the_census_text_names_each_branch` pins the text (runs everywhere).
- Windows: module 74 passed, 1 skipped (73 + 1; the skip = the native POSIX proof, as
  today). No `work/evidence/` was written at this seat.
- Parent RED: collection-level (`census_text` absent).

### Static and tests at the head (`1e275359`; `-m "not gpu"`, every run `-k 'not test_python_m_clearwater_starts_the_shell_and_exits_0'` where it applies)

Static:

- `ruff check .` all passed;
- `ruff format --check .` 339 files already formatted;
- `mypy` and `mypy --platform darwin` no issues in 166 source files;
- every committed blob 0 CR and 0 NUL (counted in Python).

| Module | Normal PATH | FFmpeg dropped |
|---|---|---|
| `tests/test_app_startup.py` (offscreen) | 9 passed, 1 deselected | 7 passed, 2 skipped |
| `tests/test_app_leftovers.py` (offscreen) | 27 passed | 26 passed, 1 skipped |
| `tests/test_reviewpack.py` (offscreen) | 177 passed | 150 passed, 27 skipped |
| `tests/test_wp321_bench.py` | 11 passed, 1 deselected (gpu) | 9 passed, 2 skipped |
| `tests/test_gui_gpu_pack_dialog.py` (offscreen) | 29 passed | - |
| `tests/test_gui_settings_dialog.py` (offscreen) | 95 passed | 95 passed |
| `tests/test_tools_package_build.py` (`-n 3`) | 686 passed (669 + 17) | - |
| `tests/test_tools_package_notices.py` (`-n 3`) | 420 passed | - |
| `tests/test_tools_package_smoke.py` | 74 passed, 1 skipped | - |
| `tests/test_release_workflow.py` | 140 passed | - |
| `tests/test_macos_portability.py` | 226 skipped (platform) | - |
| `tests/test_wp65_conftest_home.py` | 1 passed, 3 skipped | - |

Every skip with FFmpeg dropped has the one reason "ffmpeg and ffprobe are not on the PATH
(needed to generate or probe video)". Simulated darwin: `test_gui_settings_dialog.py` 95
passed (the run-2 ledger's two open failures are gone). No write under
`C:\Users\rwsmy\Library`.

### Verification loop (self)

Pass 1:

- **Suspected:** the chain walk's first label used `physical.relative_to(root)`. A folder
  link's view (`macos_link_view`) hands nested links over as REAL paths, so under a root named
  through an alias (macOS `/var` -> `/private/var`) it raises `ValueError` instead of
  refusing. **CONFIRMED** (`27d443a1`'s `build.py` swapped in: `ValueError ... is not in the
  subpath of ...`). **FIXED** in `85f2739d`: the label falls back to the real `.app`; test
  `:3016`.
- **Suspected:** `find -ls` failing would fail an evidence step in an otherwise green run.
  **FIXED** in `1e275359` (`|| echo`), pinned.
- **Suspected:** `file -b | grep` under `pipefail` gives a SIGPIPE false negative. Avoided by
  design: `case "$(file -b ...)"`, no pipeline.
- **Suspected:** the S3 fix hides a product defect. **REJECTED:** OK refusing a reported-
  unavailable stored encoder is the D74 table. Noted for the dispatcher: on a Mac without
  FFmpeg, Settings' OK stays disabled until "auto" or an available encoder is chosen. This is
  by design; with bundling ON it does not arise.
- **Suspected:** the S2 skip could mask a lock defect. **REJECTED:** only zero fitting wheels
  skips; more than one still reaches `plan()`'s error.
- **Slips, fixed before commit:**
  - a misplaced insertion split the smoke test's `skipif` decorator from its function
    (`SyntaxError`), corrected before commit;
  - a heredoc collapsed `\\n` in one scripted edit (the known trap), caught by the failing
    test and redone with the Edit tool;
  - four test files checked out CRLF were normalised to LF (HEAD blobs 0 CR).

Pass 2 over the eight items, the ledger's claims and the commits: nothing new. Loop ended.

**For the dispatcher:**

- (a) S2's dictated debt-row premise is refuted (above).
- (b) `test_wp321_bench.py::test_a_device_frame_run_gives_the_sink_device_frames` is
  `gpu`-marked and not skipped without CUDA. With FFmpeg bundled ON on the runner it would
  pass the new guard and fail at `CupyBackend` (no CUDA on macOS); outside this dispatch.
- (c) `test_macos_portability.py` now collects 226 (the brief's 224 M cases plus two unit
  checks).
- (d) the listing and the census files are first produced by the next runner run.

Depth at run-3-fix yield: 316,018 (wp65-cell16, read by the dispatcher with cell_depth.py at its run-3-fix return)

## A r11 fold (`wp65-cell17`, dispatch-18; base `0a40c058`)

Codex Reviewer A r11 on `a93a0ab7..0a40c058`: `VERDICT: FINDINGS`, 1 MAJOR + 3 MINOR, all
upheld by CHARC (`75e7d765`) and folded as ruled. The S2 entry above carries CHARC's
`c1c14926` line. No `src/` change; `release.yml` byte-identical (`git diff 0a40c058` empty,
its sha256 pin passes); `MACOS_FFMPEG_BUNDLED` stays "false"; `notices.py`, the debt
register, the C14 rows, the committed fixtures and the Windows notices annex untouched.
Scratch `work\wp6.5\ar11fold\`.

### Commits

| Finding | Commit | Files |
|---|---|---|
| F1 MAJOR, the `.app` walk | `2b7cbcc5` | `tools/package/build.py`, `tests/test_tools_package_build.py` |
| F2 the tiny set's photo half | `bb644951` | `tests/test_reviewpack.py` |
| F3 the GPU pack platform gap | `230d652d` | `tests/test_gui_gpu_pack_dialog.py` |
| F4 the listing after both builds | `3a9bc562` | `.github/workflows/macos-build.yml`, `tests/test_release_workflow.py` |

### F1 MAJOR: a `.app` link is walked component by component (`2b7cbcc5`)

`tools/package/build.py`:

- `:4268` `_macos_link_chain_problem(root, physical)` is rewritten as a component walk:
  - the boundary `realpath(root / "Contents")` is canonicalised ONCE, at the start, so an
    alias above the release root (macOS `/var` -> `/private/var`) is untouched;
  - the walk starts at the link's canonical folder; each component of the stored text is
    taken in turn: `..` steps to the canonical parent, a name steps into it;
  - a component outside `Contents` is refused AT THAT POINT ("link chain leaves the
    bundle"), before any later component is read, so an outside alias's return hop is never
    followed. **Correction (A r12):** for the whole rule this claim was FALSE at `5d9a1d89`
    (Codex A r12 finding 1): the single-link preflight at `:4371` (`named.is_symlink()`,
    `realpath(named)`) ran BEFORE the walk and resolved the outside alias first; and at
    `b7e2dfb1` it was still false for the callers (Codex A r13 findings 1 and 2: `os.walk`'s
    following `DirEntry.is_dir()`, and `realpath(root / "Contents")` on a linked boundary).
    **The invariant (CHARC `4ed56fcb`):** inside a `.app`, no filesystem call that FOLLOWS a
    link (`stat`, `realpath`, `exists`, `is_file` / `is_dir` with following,
    `DirEntry.is_dir()` default, `open`) is made on any path at or under the release root
    until every link on that path has been admitted by the component walk; only `lstat` /
    `readlink` / `is_symlink` / `is_junction` and non-following `DirEntry` queries precede
    admission. **Narrowed (A r14 M1):** the claim "proved by the recorder test from
    `30d9ccde`" was NOT true at `bce8bddc` (Codex A r14 finding 1: the origin check's
    diagnostic PATH lookup ran `is_file()` on a candidate through the unadmitted link
    `Contents/Resources/bin`, and the recorder missed real opens, late admissions and
    junctions). From `b38e7420` the invariant is EVIDENCED by the recorder test for its
    covered shapes only, not proved for every following call (`## A r14 fold` below);
  - EVERY link met (a folder link in mid-path as much as a further hop at the final name)
    counts against `_MACOS_LINK_HOPS` = 8 and is validated as the first: relative POSIX text,
    never a junction, never met twice (a loop); its text is then walked in place;
  - a CHAIN (a link met at the final name) must end in an existing regular file; a single
    hop's end stays with the class rule (a folder target is legitimate there);
  - the message lists every link met, the departing one included, and for a departure ends
    with where the hop was heading, read lexically (A's shape:
    `<release>/outside/back/data`, the external hop).
- `:4383` `_macos_link_class_problem`: inside a `.app`, a SINGLE hop is now walked too,
  after today's outside / dangling checks (so their messages hold). That closes the
  second link of A's shape, which `named.is_symlink()` (the OS resolving the outside alias)
  had read as a single hop and admitted as a (B) link.
- `:4446` `macos_link_problem`'s docstring states the component reading. Still THE one rule,
  shared by the origin check, the ZIP and the notices. Outside a `.app` (onedir, and every
  Windows caller) the code path is unchanged: "link to a link (one hop only)" byte for byte.

`tests/test_tools_package_build.py` (the out-of-root alias is built beside the `.app`, inside
the test's tmp folder; `:3047` `outside_alias` writes its text with the host's separator,
since a Windows host follows a folder link only through backslash text, and the rule never
reads it):

- `:3062` A's exact shape: both bundle links REFUSED, each message naming
  `Contents/Frameworks/data -> '../../../outside/back/data'` and the external
  `<tmp>/wrapper/outside/back/data`; the origin walk names both, the ZIP refuses with it.
- `:3093` a folder link in mid-chain (`Contents/Frameworks/F -> ../../../outside/back`, the
  alias leading back to `Contents/Frameworks/pkg`) REFUSED where it leaves.
- `:3115` a single hop that steps above `Contents` and back with no link at all
  (`../../Contents/Frameworks/y.dylib`) REFUSED at the `..` (the ruling's "any component").
- `:3134` the bound counts folder links: five file hops through four folder links (9 links)
  REFUSED with all nine named; four file hops through four folder links (8) ADMITTED.
- `:3164` an alias (a folder link) above the release root: the PyInstaller chain and the
  single-hop cross-link ADMITTED by the walk, the single hop by the whole rule and the
  origin walk. (The chain is checked through the walk: on a Windows host `ntpath.realpath`
  cannot follow a POSIX-text file link under an alias, a host artifact of today's
  `realpath(named)` check, not of the rule.)
- MIRRORS still ADMITTED, unchanged: `C-app-pyinstaller-chain` and `C-app-link-to-a-link`
  (`LINK_CASES`, origin walk and ZIP), `test_the_pyinstaller_chain_is_admitted_in_the_origin_walk`,
  the aliased-root label case from `85f2739d`. The five `CHAIN_REFUSALS`, the absolute hop,
  the junction and the 8 / 9 direct-hop bound keep their exact messages.
- Onedir two-hop: `test_the_onedir_two_hop_chain_keeps_todays_message` passes unchanged.

**RED on `0a40c058`** (its `build.py` swapped in, restored, `cmp` equal): the four new
refusal tests FAIL (A's shape; the mid-chain folder link: `None`; the lexical exit: `None`;
the 9-link bound: `None`); the five mirrors / alias tests pass. A's shape on the parent, by
a scratch probe (`ar11fold\probe_ashape.py`, a `release\` tree): `Contents/Frameworks/data`
-> `None` (ADMITTED, the hole); `Contents/Resources/data` -> "link resolves outside the
release folder" on this Windows host only, the same `ntpath.realpath` artifact (A executed it
on POSIX semantics: admitted). Head: both refused with the chain.

**GREEN:** `test_tools_package_build.py` + `test_tools_package_notices.py` (`-n 3`) **1112
passed** (686 + 6 new = 692; notices 420). Symlinks available: 0 skipped.

### F2 MINOR: the tiny set's photo half runs without FFmpeg (`bb644951`)

A split test (the ruled preference):

- `tests/test_reviewpack.py:953` `TINY_PHOTOS` / `TINY_VIDEO`; `:960` `_run_tiny_set` plants
  the inputs, writes the config and manifest, runs `build.main all --force-cpu` (== 2,
  R3-5) and checks the links.
- `:1004` `test_all_tiny_set_photos` (`slow`, NO FFmpeg guard): the two photos; the corrected
  / neutral PNG assertions (the former `:996-998`), the P-A / P-Z records, `pack.json` (128
  items, 126 pending), two review-sheet rows, byte immutability.
- `:1026` `test_all_tiny_set` (`slow`, `ffmpeg_tools`): the three-item run with every
  assertion it had, unchanged.

**RED on `0a40c058`** (its test file swapped in, restored, `cmp` equal; FFmpeg dropped from
PATH by removing `WinGet\Links`; the file calls no `clearwater.__main__`, `app.main` or
export worker: its runner is `tools/headless_export.py`, which loads no PySide6): `-k tiny_set` **1
skipped** (the whole test, at `:953`, with the FFmpeg reason): no photo assertion ran.
**GREEN, FFmpeg dropped:** `test_all_tiny_set_photos` PASSED, `test_all_tiny_set` SKIPPED
"ffmpeg and ffprobe are not on the PATH (needed to generate or probe video)". **Normal
PATH:** module 178 passed (177 + 1). **FFmpeg dropped:** module 151 passed, 27 skipped, every
skip that one reason.

### F3 MINOR: only a platform gap skips (`230d652d`)

- `tests/test_gui_gpu_pack_dialog.py:53` `_fits_the_platform(tag, interpreter, platform)`:
  a wheel tag's PLATFORM part read through `gpu_pack.tag_fits` itself, the python and ABI
  parts replaced by `py3-none` (any CPython 3 interpreter accepts them).
- `:63` `lock_gap`: a locked distribution none of whose wheels (expanded by
  `gpu_pack_install._wheel_tags`, as `plan()` does) has a tag for the platform skips, with
  the unchanged reason. An interpreter / ABI miss on a platform the lock carries is no
  skip: the test runs and `plan()` fails it. Per distribution, as `plan()` fails per
  distribution: `cuda-pathfinder` is a `py3-none-any` wheel, so a whole-lock "no wheel fits
  the platform" would never skip darwin.
- `:531` `test_the_lock_decides_the_skip_as_plan_does`: `win-cp312` and `linux-cp312` no skip,
  `plan()` succeeds; `win-cp313` no skip, `require_locked_wheels()` does not skip, `plan()`
  raises "cupy-cuda12x: 0 compatible locked wheels"; `mac-arm64` / `mac-x86_64` skip with the
  reason, `plan()` raises.

**RED on `0a40c058`:** the new unit case with the parent's fit (`gpu_pack.tag_fits` on the
full tag, swapped in, restored): `[win-cp313]` FAILS ("GPU pack lock carries no wheels for
win32/amd64 (cupy-cuda12x; tags cp313, win_amd64)" is not None), 4 passed. The parent file
under a cp313 / win_amd64 scratch plugin (`ar11fold\sim\simcp313_tags.py`): 21 passed, **8
skipped** with that win32/amd64 reason (A's finding).
**GREEN:** real Windows 29 passed, none skipped; simulated darwin/arm64
(`ar11fold\sim\simmac_tags.py`) 21 passed, **8 skipped** "GPU pack lock carries no wheels
for darwin/arm64 (cupy-cuda12x; tags cp312, macosx_14_0_arm64)"; simulated cp313 / win_amd64:
**8 failed** (no skip; the first at `gpu_pack_install.py:165`, "cupy-cuda12x: 0 compatible
locked wheels"), 21 passed: the ruled "stays a FAILURE".

### F4 MINOR: the listing after both builds (`3a9bc562`)

- `.github/workflows/macos-build.yml:145` "List the app bundle" now follows "Build release
  bundle and zip" (`:137`), with the same `if: ${{ !cancelled() && !inputs.release-version }}`
  and the same script: it lists whichever `.app` the build that ran left. Release mode
  unchanged; `release.yml` untouched.
- `tests/test_release_workflow.py`:
  - `:897` the step order pin: the listing after both builds;
  - `:1645` the listing pin: right after "Build release bundle and zip", after "Build app
    bundle without FFmpeg";
  - `:1714` `test_the_app_listing_follows_whichever_build_ran` (4 cases): the real `if:`
    expressions evaluated step by step in validation mode, switch off / on, green / a
    failed leg. The listing is reached after the build that ran (with the switch on and
    green, after the FFmpeg-ON build), never before a build; release mode never lists.
  - `MODE_REACHED` and the condition-table tests unchanged and passing.

**RED on `0a40c058`** (its workflow swapped in, restored, `cmp` equal): **3 failed, 141
passed**: the order pin, the listing pin and `[ok-switch-on]` (the listing reached before
the FFmpeg-ON build). **GREEN:** module 144 passed (140 + 4).

### Static and tests at the head (`3a9bc562`; `-m "not gpu"`, every run `-k 'not test_python_m_clearwater_starts_the_shell_and_exits_0'`)

Static:

- `ruff check .` all passed;
- `ruff format --check .` 339 files already formatted;
- `mypy` and `mypy --platform darwin` no issues in 166 source files;
- every committed blob of the delta 0 CR and 0 NUL (counted in Python); `git diff --check`
  clean.

| Module | Normal PATH | FFmpeg dropped |
|---|---|---|
| `tests/test_tools_package_build.py` + `tests/test_tools_package_notices.py` (`-n 3`) | 1112 passed | - |
| `tests/test_reviewpack.py` (offscreen, no `-n`) | 178 passed | 151 passed, 27 skipped |
| `tests/test_gui_gpu_pack_dialog.py` (offscreen, no `-n`) | 29 passed | - |
| `tests/test_release_workflow.py` | 144 passed | - |
| `tests/test_tools_package_smoke.py` | 74 passed, 1 skipped | - |
| `tests/test_macos_portability.py` | 226 skipped (platform) | - |

### Verification loop (self)

Pass 1:

- **Suspected:** after the walk, a one-hop `.app` link that also leaves the release would
  change today's "link resolves outside the release folder" text
  (`test_folder_link_checks_nested_links_as_if_at_its_location` pins it). **Avoided by
  design:** the single-hop walk runs AFTER today's outside / dangling checks; the test
  passes unchanged.
- **Suspected:** A's second link (`Contents/Frameworks/data`) never reaches the chain walk
  because `named.is_symlink()` resolves through the outside alias to a regular file.
  **CONFIRMED** by the probe (parent: `None`); **FIXED** in the same commit: every `.app`
  single hop is walked.
- **Suspected:** the walk refuses a legitimate PyInstaller shape. **REJECTED:** BUNDLE's
  cross-links are written relative within `Contents` (`../Frameworks/...`, depth-based
  `../../Frameworks/...` from a Resources subfolder), and the dotted-folder and
  framework-structure links stay inside; every admitted `LINK_CASES` row, the folder-link
  depth test and the PyInstaller chain still pass.
- **Noted, conservative:** a path that meets the same link twice (`F/../F/x`) is refused as
  a loop; PyInstaller writes no such text, and a refusal is the safe side.
- **Slips, fixed before commit:** a leftover `folder, executable = ..., None` line in the
  first draft of the alias test; a first draft of the A-shape test asserted
  `realpath(...).is_file()` on POSIX-text links, which a Windows host cannot follow (redone
  on the outside alias itself).

Pass 2 over the four findings, the S2 line, the ledger's claims and the commits: nothing
new. Loop ended.

**For the dispatcher:**

- (a) The S2 entry's heading above still reads "(DR number: CHARC assigns at the accept)";
  the dispatch replaced only the placeholder sentence, so the heading was left as written.
- (b) F2: the photo half uses its own two-photo manifest inside the split (126 pending, two
  sheet rows); the three-item test keeps every original assertion.
- (c) F1's refusal for a departure names where the hop was heading (lexically), not the
  outside alias's own text: reading the alias would be following a hop outside the bundle,
  which the ruling forbids.

Depth at A-r11-fold yield: 199,951 (wp65-cell17, read by the dispatcher with cell_depth.py at its A-r11-fold return)

## A r12 fold (`wp65-cell17`, continuation of dispatch-18; base `5d9a1d89`)

Codex Reviewer A r12 on `0a40c058..5d9a1d89`: `VERDICT: FINDINGS`, 1 MAJOR, upheld by CHARC
(`3d0e43ea`). Commit `ad73639a` (`tools/package/build.py`, `tests/test_tools_package_build.py`).
No `src/` change; `release.yml`, `MACOS_FFMPEG_BUNDLED`, `notices.py`, the debt register and
the C14 rows untouched.

- **Change:** `tools/package/build.py:4371` `_macos_link_class_problem`: inside a `.app` the
  component walk (`_macos_link_chain_problem`, `:4376`) now runs FIRST for every link, before
  any call that depends on the target (`named.is_symlink()`, `realpath(named)`, `exists()`).
  Only an admitted walk, every component of which stayed inside `Contents`, reaches those
  checks. The two former walk call sites (before / after the preflight) are gone. Onedir
  and Windows: `in_app` is false, so the same calls run in the same order with the same
  messages ("link to a link (one hop only)" byte for byte). The `macos_link_problem`
  docstring (`:4446`) states the order.
- **Consequence, pinned:** inside a `.app` a link that leaves the bundle is refused with its
  chain, never "link resolves outside the release folder".
  `tests/test_tools_package_build.py:2827`
  `test_folder_link_checks_nested_links_as_if_at_its_location` now expects
  "evil under the linked folder: link chain leaves the bundle:
  Contents/Frameworks/pkg/evil -> '../../../../outside'; `<tmp>/wrapper/outside`" (still a
  refusal, in the rule and twice in the origin walk). The onedir "outside the release
  folder" rows (`planted-escaping-link` and the rest) are unchanged.
- **Regressions:**
  - `:3114` `test_the_walk_resolves_nothing_outside_contents` (both bundle links of A's
    out-and-back shape): `os.path.realpath`, `os.readlink`, `os.stat` and `os.lstat`
    recorded during the whole rule; no recorded path (normalised lexically) lies outside
    `Contents` except the release root and its ancestors (canonicalising the boundary;
    `:3102` `_outside_contents`).
  - `:3150` `test_a_missing_return_file_still_refuses_with_the_chain`: the same shape with
    `Contents/Frameworks/pkg/data` absent: "link chain leaves the bundle" with the chain and
    the lexical heading, for both links.
- **RED on `5d9a1d89`** (its `build.py` swapped in, restored, `cmp` equal): **3 failed, 56
  passed** over the link selection. Failing: the recorder for `Contents/Frameworks/data`
  (3 recorded calls outside `Contents`, the first an `os.stat` of the path through
  `outside/back/data`); the missing return for `Contents/Frameworks/data` ("dangling link");
  and the nested-link test (the old "outside the release folder" text). The
  `Contents/Resources/data` cases pass there, as A's probe found (its chain walk already
  ran first).
- **GREEN:** the mirrors stay admitted: `C-app-pyinstaller-chain`, `C-app-link-to-a-link`,
  the aliased-root label case, the alias above the release root and the framework-structure
  links (`framework_origin_check` and the release-ZIP framework tests). The onedir two-hop
  message is unchanged.
  - `test_tools_package_build.py` + `test_tools_package_notices.py` (`-n 3`): **1116
    passed** (1112 + 4).
  - `test_tools_package_smoke.py`: 74 passed, 1 skipped.
  - `ruff check .` and `ruff format --check .` (339 files) clean; `mypy` and
    `mypy --platform darwin` no issues in 166 source files.
  - Committed blobs 0 CR.
- **Verification loop:** suspected that the walker itself stats outside `Contents` (its
  `realpath(root)` and `realpath(physical.parent)`): REJECTED, those canonicalise the
  release root and the link's own folder, never the target; the recorder admits only the
  root and its ancestors outside `Contents` and passes. A second pass found nothing new.

Depth at A-r12-fold yield: 226,212 (wp65-cell17, read by the dispatcher with cell_depth.py at its A-r12-fold return)

## A r13 fold (`wp65-cell17`, continuation 2 of dispatch-18; base `b7e2dfb1`)

Codex Reviewer A r13 on `5d9a1d89..b7e2dfb1`: `VERDICT: FINDINGS`, 2 MAJOR + 1 advisory,
ruled by CHARC (`4ed56fcb`, the invariant above). Commit `30d9ccde`
(`tools/package/build.py`, `tests/test_tools_package_build.py`). No `src/` change;
`notices.py` untouched (it enumerates through `build._macos_entries`, and only for an onedir
home: it requires `_internal`, so it never lists a `.app`); `release.yml`,
`MACOS_FFMPEG_BUNDLED`, the debt register and the C14 rows untouched.

### Changes (`tools/package/build.py`)

- **F1, the listing.** `:4227` `_macos_app_entries(root)`: ONE `os.scandir` listing that
  never follows a link. Each entry is classified as a link (`is_symlink()` /
  `is_junction()`) BEFORE any folder query; the folder and file queries pass
  `follow_symlinks=False`, and only a physical folder is listed further. `:4258`
  `_macos_entries(root, *, in_app=None)` uses it for the `.app` form (default: `root` is a
  `.app`) and keeps `os.walk` for onedir. It serves:
  - the origin check (its loop over `_macos_entries(root)`);
  - the release ZIP (`_macos_release_files`);
  - `macos_link_view(path, *, in_app=False)` (`:4471`), whose folder-target listing passes
    `in_app` (`:4491`), from `macos_link_problem` (`:4545`) and the origin check (`:4745`).
- **F2, the boundary.** `_macos_link_chain_problem` (`:4334`) reads `root / "Contents"`
  with `is_junction()` and `os.lstat` first:
  - a junction gives "link chain meets a linked boundary: Contents (junction)";
  - a symlink gives "link chain meets a linked boundary: Contents -> '<text>'";
  - a missing or non-folder entry gives "link chain finds no Contents folder".

  Only then is the boundary canonicalised as `realpath(root) / "Contents"`. An alias ABOVE
  the release root is untouched. A `Contents` link met as an entry is refused by the rule's
  first junction test or by the walk.
- **Under the same invariant, two more following calls in the `.app` form:**
  - `_macos_link_class_problem` (`:4448`, `:4461`) reads the real contents root and the
    three bundle folders as `realpath(root) / <relative>` instead of `realpath()`-ing
    `Contents/Frameworks|Resources|MacOS`, so a linked Frameworks is never followed and
    admits nothing under it.
  - The origin check (`:4730`) opens the executable (the bootloader comparison and
    `read_package`) only when `_macos_link_on_path` (`:4670`, an `lstat` reading from the
    root down, stopping at the first link) finds no link on its path. Otherwise it records
    "native origin: `<executable>` lies behind a link in the bundle; not read".
    **Corrected (A r14 advisory 3):** the executable guard declines to read an executable
    behind a link INDEPENDENTLY of the shared link rule. The walk refuses that link only
    when the rule refuses it: a class-(C) link (`Contents/MacOS/Clearwater ->
    ../Frameworks/Clearwater`) stays ADMITTED by the rule, and its executable is still
    not read. No code change; the class-(C) admission is preserved.
- Onedir and Windows: unchanged. The listing keeps `os.walk`; the class rule's onedir
  branch makes the same calls. **Evidence:** scratch probe `ar11fold\onedir_calls_probe.py`
  recorded every filesystem call (the test's recorder) of the origin check, the ZIP, the
  shared rule and the notices inventory on all nine onedir `LINK_CASES`. Against
  `b7e2dfb1`'s `build.py` and the fold's, the 2,129 recorded calls (names, paths, order,
  following flags) and every result and message are IDENTICAL, once the folder the scratch
  copy of `notices.py` was loaded from is normalised.

### Regressions (`tests/test_tools_package_build.py`)

- `:3188` `_FsRecorder` instruments:
  - `os.stat` (its `follow_symlinks`), `os.lstat`, `os.readlink`, `os.path.realpath`;
  - `os.scandir`, wrapping each `DirEntry` so that `is_dir` / `is_file` / `stat` record
    their `follow_symlinks`;
  - `Path.exists` / `is_file` / `is_dir` / `resolve`.

  A violation is either of:
  - ANY call whose (lexically normalised) path lies in the outside zone
    (`wrapper/outside`);
  - a FOLLOWING call on a path under the release root through a link component not
    admitted for that shape.

  The release root and its ancestors may be canonicalised.
- `:3356` `test_no_following_call_before_the_walk_admits_the_links`, three shapes
  (`LINK_SHAPES`, `:3348`):
  - r11's out-and-back;
  - r13's nested `pkg/evil`: the folder cross-link `Contents/Resources/pkg` is admitted,
    and `evil -> ../../../../outside/back/data` is refused;
  - r13's linked `Contents -> ../outside/back`, with the alias to an outside payload that
    holds `MacOS/Clearwater`.

  Each runs the PUBLIC entry points: `native_origin_violations` (the bootloader and
  `read_package` stubs record an `open`), `write_release_zip` and `macos_link_problem` on
  each link. Each refuses; the recorder finds no violation. For the linked `Contents`, the
  rule's text and both origin lines are pinned, and no `open` is recorded.
- `:3403` `test_a_linked_contents_boundary_is_refused_by_its_text`:
  - a link `Contents` gives "link chain meets a linked boundary: Contents -> '../elsewhere'";
  - a junction `Contents` gives "junction" from the rule's first test, and a link reached
    through it is refused by the walk with "Contents (junction)". The junction case ran on
    this host.
- `:3428` `test_the_app_listing_never_follows_and_matches_the_walk`: on a physical tree, the
  `.app` listing equals the onedir `os.walk` listing, entry for entry.
- The earlier regressions (r11's four refusals and bound, r12's recorder and missing return)
  and every mirror stay green:
  - admitted: the PyInstaller chain, `C-app-link-to-a-link`, the aliased-root label, the
    alias above the release root, the framework links;
  - the onedir two-hop message unchanged.

### RED / GREEN

- **RED on `b7e2dfb1`** (its `build.py` swapped in, restored, `cmp` equal): **6 failed, 4
  passed** over the new tests and r12's:
  - the recorder on all three shapes:
    - out-and-back: a following `DirEntry.is_dir` on `Contents/Resources/data`;
    - nested: a following `DirEntry.is_dir` on `pkg/evil`;
    - linked Contents: an `open` of the executable and more;
  - both boundary cases ("link chain leaves the bundle" for the link; `None` for the link
    through the junction);
  - the listing test (no `in_app`).

  r12's four still pass there.
- **GREEN:**
  - `test_tools_package_build.py` + `test_tools_package_notices.py` (`-n 3`): **1122
    passed** (1116 + 6).
  - `test_tools_package_smoke.py`: 74 passed, 1 skipped.
  - `ruff check .`, `ruff format --check .` (339 files), `mypy`, `mypy --platform darwin`
    (166 source files): clean.
  - Committed blobs 0 CR.

### F3 (advisory): the onedir call order

Recorded: the fold's onedir call order equals `5d9a1d89`'s (and `b7e2dfb1`'s, above).
`5d9a1d89` had already added `is_symlink(T)` / `is_junction(T)` before `realpath(T)`
relative to `a93a0ab7`, with identical messages, so identity with `a93a0ab7`'s call order
is not claimed.

### Verification loop

Pass 1:

- **Suspected:** the origin check's bootloader comparison and `read_package` open the
  executable through a linked `Contents` before any walk. **CONFIRMED** (the linked-Contents
  shape's recorded `open` at `b7e2dfb1`); **FIXED** with the `lstat` path guard.
- **Suspected:** `realpath(contents)` / `realpath(folder)` in the class rule follow an
  unadmitted Frameworks link. **CONFIRMED** by reading. **FIXED**: the folders are read from
  the real root, in the `.app` form only (onedir's calls unchanged, by the probe).
- **Suspected:** the new listing differs from `os.walk` on a legitimate tree. **REJECTED** by
  the equality test.
- **Not fixed, outside scope:** the notices inventory on a `.app` folder
  (`find_executable`'s `is_file()` on `Clearwater.app/Contents/MacOS/Clearwater`, then
  `(home / "_internal").is_dir()` in `notices.py`) follows before raising "expected an onedir
  folder"; the `.app`-aware notices is F0-2.

Pass 2: nothing new.

Depth at A-r13-fold yield: 304,492 (wp65-cell17, read by the dispatcher with cell_depth.py at its A-r13-fold return)

## A r14 fold (`wp65-cell18`, dispatch-19; base `bce8bddc`)

Codex Reviewer A r14 on `b7e2dfb1..bce8bddc`: `VERDICT: FINDINGS`, 2 MINOR + 1 advisory, folded
under CHARC's standing fold rule (`4ed56fcb`); no ruling needed. CHECK 2 (no wrong admission)
and CHECK 3 (onedir identical) passed at r14 and stay so. Commit `b38e7420`
(`tools/package/build.py`, `tests/test_tools_package_build.py`): M1 and M2 in ONE commit,
because M1's regression runs under M2's recorder. No `src/` change; `release.yml`,
`MACOS_FFMPEG_BUNDLED`, `notices.py`, the debt register and the C14 rows untouched. No
admission changed (the shared rule `macos_link_problem` and its walk are untouched).

### M1 MINOR: the diagnostic PATH lookup (`tools/package/build.py`)

As committed in `b38e7420`; the root comparison below is SUPERSEDED by the residual fold
(`976f8c26`, `### Residual fold` below): any link on the path now skips the candidate.

- `:4690` `_macos_candidate_behind_a_link(roots, candidate)`: reads a PATH candidate as
  WRITTEN, component by component from its anchor (`..` lexically, which matches the
  system's reading up to the first link, where the reading stops). Every component strictly
  below a root is read with `is_junction()` and `os.lstat` only, never followed. Names
  compare case-folded (a case-insensitive volume's spelling of the root). A component that
  cannot be read ends the reading: the system's own lookup stops there too.
- `:4738` `linked()` in `_macos_native_origin_violations`, used by `unknown()` (`:4750`):
  - inside a `.app`, a candidate with a link or junction on its path below the release root
    is SKIPPED as a diagnostic: no "likely PATH source" for it, never resolved, never routed
    through the walk;
  - the roots are the `.app` as given and `realpath(root)` (an alias above the root, the
    one following call the invariant allows on the root), read once, on first need;
  - a candidate outside the release root (the host's PATH) keeps today's `is_file()`.
- Onedir: `linked()` returns `False` with no call, so the calls, their order and the
  messages are those of `bce8bddc`. **Evidence:** scratch probe
  `work\wp6.5\ar14fold\onedir_calls_probe_r14.py` (the A r13 probe with a NONEMPTY
  `original_path`: the onedir `_internal`, an outside folder and an empty entry, so
  `unknown()` queries candidates under the root) over the nine onedir `LINK_CASES` (the
  origin check, the ZIP, the shared rule, the notices inventory), under the strengthened
  recorder, against `bce8bddc`'s `build.py` and the fold's: 2,188 recorded calls (names,
  paths, order, following flags) and every result and message IDENTICAL, once the two
  checkout folders are normalised (`compare_probe.py`). Windows origin
  (`_pe_native_origin_violations`) untouched.
- The comment at `:4782` now says the executable guard works independently of the shared
  rule (advisory 3); a comment only.

### M2 MINOR: the recorder (`tests/test_tools_package_build.py`)

`:3196` `_FsRecorder` is EVIDENCE FOR ITS COVERED SHAPES, not a proof of every following
call. It records, as `(call, path, following)` in ONE ordered sequence:

- `os.stat` (its `follow_symlinks`), `os.lstat`, `os.readlink`, `os.path.realpath`,
  `os.scandir`, `os.listdir`;
- `os.path.exists` / `isfile` / `isdir` (on Windows these bypass `os.stat`);
- each listed `DirEntry`'s `is_dir` / `is_file` / `stat` with their `follow_symlinks`;
- `Path.exists` / `is_file` / `is_dir` / `resolve` / `open` (`read_bytes` and `read_text`
  open through `Path.open` and `io.open` on 3.12);
- **gap 1, the real opens:** `builtins.open`, `io.open`, `os.open` (following unless
  `O_NOFOLLOW`);
- **gap 2, admissions as events:** `admit`, recorded when the component walk
  (`build._macos_link_chain_problem`) returns admitted, after its own calls.

Not covered: opens made in C below these names (`io.FileIO` built directly, an extension
module's own `fopen`), child processes, calls on a file descriptor; from the A r15 fold
(below) also named: calls with `dir_fd`, and `DirEntry.is_symlink` / `is_junction`
(cached from the listing, whose `scandir` is recorded). The reading of a recorded path
was changed by the A r15 fold (below).

`:3332` `violations(root, zone)` walks the calls IN ORDER: a call is a violation when it
touches the outside zone at all, or FOLLOWS a path under the release root through a link
not admitted EARLIER in the sequence (a later admission does not excuse it). **Gap 3:** a
link is `S_ISLNK` by `lstat` OR a junction by `os.path.isjunction` (looked up per call; on
POSIX it is `False`). `:3319` `admitted(root)` lists the admissions in order; the shape
test now asserts the walk admits exactly the shape's admitted links instead of whitelisting
them.

**The covered shapes** (each through the public entry points: `native_origin_violations`,
`write_release_zip`, `macos_link_problem` on each link; `:3426` `_recorded_entry_points`):

1. r11's out-and-back (`Resources/data -> ../Frameworks/data`,
   `Frameworks/data -> ../../../outside/back/data`, the outside alias back in): nothing
   admitted;
2. r13's nested `pkg/evil` (`Resources/pkg -> ../Frameworks/pkg` admitted,
   `Frameworks/pkg/evil -> ../../../../outside/back/data` refused);
3. r13's linked `Contents -> ../outside/back`: nothing admitted, and no open of any kind
   under the release root;
4. A r14's linked PATH folder (`Contents/Resources/bin -> ../../../outside/bin`, an unknown
   `Contents/Aaa.dylib` met first), with `original_path` naming the linked folder as
   written, through `..` past the link, and followed by a host folder holding the file;
   from the residual fold also a host alias into the bundle and a host link elsewhere.

### Regressions

- `:3500` `test_a_linked_path_candidate_is_never_followed[linked-only | linked-then-host |
  through-dotdot]` (shape 4): `found` is exactly "native origin unknown:
  Contents/Aaa.dylib" (with "; likely PATH source: `<host>/Aaa.dylib`" for the host case,
  whose `Path.is_file` is recorded) and the link's refusal, unchanged: "link chain leaves the
  bundle: Contents/Resources/bin -> '../../../outside/bin'; `<real wrapper>/outside/bin`".
  Nothing admitted; no violation.
- `:3542` `test_a_path_candidate_is_read_below_the_root_in_any_spelling`: the helper finds
  the link through the root as given, through its canonical spelling (an alias above the
  root, made in the test), in upper case (on a case-insensitive volume), through `..`, and
  out through the link and lexically back outside; a physical path, a missing component and
  a host path are not "behind a link".
- `:3572` `test_the_recorder_records_an_ordinary_read`: `Path.read_bytes`, `Path.read_text`,
  `builtins.open`, `io.open`, `os.open` each record a following open of the file (A's
  probe).
- `:3592` `test_the_recorder_orders_admission_events`: `realpath` on `Resources/pkg` before
  its admission is a violation; after it, none.
- `:3611` `test_the_recorder_records_the_walks_admissions`: the walk's admission is recorded
  once, after its `readlink`.
- `:3635` `test_the_recorder_sees_a_junction_as_a_link[modeled | real]`: an `open` of
  `Contents/MacOS/Clearwater` through a junction `Contents/MacOS` is a violation (A's
  modeled case on every host; a real junction on Windows, which ran here).
- `:3463` `test_no_following_call_before_the_walk_admits_the_links` (shapes 1-3) moves to
  the ordered checker and the admission assertion; its docstring says evidence for the
  covered shapes.

### RED / GREEN

- **RED, M1 on `bce8bddc`'s `build.py`** (a throwaway detached worktree at `bce8bddc` under
  `work\wp6.5\ar14fold\red-wt`; the fold's tests run with `WP61_BUILD_SCRIPT` naming its
  `build.py`): **4 failed, 8 passed** over the new and recorder tests. Failing: the three
  shape-4 cases, each by the recorder (a following `Path.is_file` and its `os.stat` on
  `Contents/Resources/bin/Aaa.dylib`, through the unadmitted link), and the spelling test
  (no helper). On this Windows host the POSIX-text folder link is not followed by the OS,
  so the old messages happened to match; the recorder is what catches it (on macOS the old
  code also NAMED the linked candidate, as A's probe showed). Shapes 1-3 pass there under
  the strengthened recorder, as A's CHECK 1 reruns found.
- **RED, M2 on `bce8bddc`'s recorder** (scratch `test_ar14_old_recorder_red.py`, the three
  gap cases in the OLD recorder's API, run in the throwaway worktree against its own test
  module): **4 failed**: `read_bytes` recorded nothing; the late admission (whitelisted)
  gave no violation; the modeled and the real junction gave no violation.
- **GREEN** (`b38e7420`):
  - `test_tools_package_build.py` + `test_tools_package_notices.py` (`-n 3`): **1131
    passed** (1122 + 9);
  - `test_tools_package_smoke.py`: 74 passed, 1 skipped;
  - `test_macos_portability.py`: 226 skipped (darwin-only on this host);
  - `ruff check .`, `ruff format --check .` (339 files), `mypy`, `mypy --platform darwin`
    (166 source files): clean;
  - committed blobs 0 CR, 0 NUL.

### ADV3 (advisory): ledger wording only

`## A r13 fold`'s executable-guard bullet is corrected in place (above): the guard rejects
reading an executable behind a link independently of the shared rule; a class-(C) link stays
admitted. No code change beyond the matching comment (`:4782`).

### Verification loop

Pass 1:

- **Suspected:** `..` in a PATH entry after a bundle link (`<root>/.../bin/../bin`) escapes
  a check on the normalised path. **CONFIRMED** by reading (a normalised path would hide the
  link the system follows); **FIXED** by reading the components as written
  (`through-dotdot`, and the spelling test's out-and-back).
- **Suspected:** a PATH entry naming the canonical root (an alias above it) or another
  letter case is taken for a host path and followed. **CONFIRMED** by reading; **FIXED**
  (both roots, case-folded); the spelling test.
- **Suspected:** the strengthened recorder flags legitimate reads in shapes 1-3 (the origin
  check's `read_bytes` of physical files). **REJECTED**: shapes 1-3 are green under it.
- **Suspected:** onedir calls change (the moved `in_app` line, `linked()`). **REJECTED** by
  the nonempty-PATH probe (identical).
- **Folded in `976f8c26` (dispatch-19b, `### Residual fold` below), was open here:** a
  HOST PATH entry that
  reaches into the bundle through a link OUTSIDE the release root (for example
  `/tmp/alias -> <root>/Contents/Resources`, then `/tmp/alias/bin`) is lexically outside
  the root, so it keeps today's `is_file()` per the dispatch ("candidates outside the
  release root keep today's query"), and that query follows the bundle's `bin` link.
  Closing it needs a non-following resolver of host links (`readlink` per component),
  i.e. a change to the outside-candidate query the dispatch fixed as unchanged.

Pass 2: nothing new.

Depth at A-r14-fold yield: DISPATCHER TO FILL

### Residual fold (`wp65-cell18`, dispatch-19b; base `d1ecd039`)

The A r14 fold's own open item (a host PATH alias into the bundle), folded as a MINOR under
CHARC `4ed56fcb`; dispatch-19b overrides dispatch-19's "candidates outside the release root
keep today's query" for the `.app` form only. Commit `976f8c26` (`tools/package/build.py`,
`tests/test_tools_package_build.py`). No admission change; no `src/`, `release.yml`,
`MACOS_FFMPEG_BUNDLED`, `notices.py`, debt-register or C14 change.

- **Change:** `tools/package/build.py:4690` `_macos_candidate_behind_a_link(candidate)`: a
  link or junction ANYWHERE on the candidate's path, from the anchor, read as written
  (`..` lexically, exact because the reading stops at the first link) with `os.lstat` /
  `is_junction()` only, marks it linked; a component that cannot be read ends the reading.
  The release-root comparison (both root spellings, case folding, `realpath(root)`) is
  REMOVED: with any link deciding, it served nothing, and the fold makes one following call
  fewer. `:4728` `linked()` is `in_app and _macos_candidate_behind_a_link(candidate)`; a
  linked candidate is skipped as a diagnostic (no "likely PATH source"), never resolved.
  The lost hint for a PATH entry behind a host alias (macOS `/tmp` -> `/private/tmp`) is
  accepted (dispatch-19b).
- **Recorder:** `tests/test_tools_package_build.py:3332` `violations()` now reads EVERY
  component of a followed path from the anchor: a link under the release root must be
  admitted earlier (as before); a link OUTSIDE it is a violation when it resolves at or
  under the release root (a host alias into the bundle). An alias above the root (macOS
  `/var`) resolves to an ancestor of the root and is not one. Covered shape 4 gains the
  two host cases below.
- **Regressions:**
  - `:3521` `test_a_linked_path_candidate_is_never_followed`, two new cases:
    `host-alias-into-bundle` (`<real tmp>/alias -> <root>/Contents/Resources`,
    `original_path = <real tmp>/alias/bin`, the bundle's `Contents/Resources/bin` a link)
    and `host-link-elsewhere` (`<real tmp>/hostlink -> <real tmp>/host/bin`, which holds the
    file): no "likely PATH source"; no following call through either host link (asserted
    directly) or through the bundle link (the recorder); the bundle link's refusal
    unchanged. `linked-then-host` still names the physical host folder.
  - `:3579` `test_a_path_candidate_with_any_link_on_it_is_skipped` (replaces the spelling
    test): linked through the bundle link, through `..` past it, out through it and
    lexically back, through an alias above the root, in upper case (case-insensitive
    volume), and as a path relative to the working folder; not linked: a physical path, a
    missing component, an absent host folder.
- **macOS exposure (dispatch-19b):** every host or physical path a new test expects to be
  queried or "not linked" is built under `Path(os.path.realpath(tmp_path))` (the named host
  folder, the host link and alias, the helper test's physical paths). Checked the fold's
  other new tests: the linked-only / through-dotdot cases expect a skip anyway; the recorder
  unit tests (read, order, admissions, junction) never call the helper, and the new
  checker reads the `/var` link as an alias above the root (no violation); the shape tests
  pass `original_path=""`; the one other test with a nonempty `original_path` (`:299`) is
  an onedir `.exe` layout, untouched. Nothing else exposed.
- **RED on `d1ecd039`** (a throwaway detached worktree; the fold's tests with
  `WP61_BUILD_SCRIPT` naming its `build.py`): **3 failed, 11 passed** over the new and
  recorder tests: `host-alias-into-bundle` (the recorder: a following `Path.is_file` and
  its `os.stat` on `<real tmp>/alias/bin/Aaa.dylib`), `host-link-elsewhere` (named "likely
  PATH source: `<real tmp>/hostlink/Aaa.dylib`") and the helper test (the old signature).
- **Onedir identity, re-run:** the nonempty-`original_path` probe over the nine onedir
  `LINK_CASES`, `bce8bddc`'s `build.py` against `976f8c26`'s: 2,188 recorded calls and
  every result and message IDENTICAL.
- **GREEN** (`976f8c26`):
  - `test_tools_package_build.py` + `test_tools_package_notices.py` (`-n 3`): **1133
    passed** (1131 + 2);
  - `test_tools_package_smoke.py`: 74 passed, 1 skipped;
  - `test_macos_portability.py`: 226 skipped (darwin-only on this host);
  - `ruff check .`, `ruff format --check .` (339 files), `mypy`, `mypy --platform darwin`
    (166 source files): clean; committed blobs 0 CR, 0 NUL.
- **Verification loop:** suspected the new checker flags the shapes' ordinary calls through
  a host ancestor link: REJECTED (an ancestor alias resolves above the root; all green, and
  the reasoning holds for macOS `/var`). Suspected the dropped `realpath(root)` changes
  onedir: REJECTED (onedir never called it; probe identical). Pass 2: nothing new.
- **Slips (declared at the A r14 return):** one Bash call ended with a bare `cd` (no
  effect, agent cwd resets), and scratch went to the main repo's `work\wp6.5\ar14fold\`.

Depth at residual-fold yield: DISPATCHER TO FILL

### A r15 fold (recorder)

Codex Reviewer A r15 on `bce8bddc..4a1ccd69`: `VERDICT: FINDINGS`, three MINOR, all in the
TEST recorder, folded under CHARC `4ed56fcb` (dispatch-19c, `wp65-cell18`; base
`4a1ccd69`). Its CHECK 1, 3, 4 and 5 passed. Commit `2222a794`
(`tests/test_tools_package_build.py` only): NO product change; no admission, onedir or
Windows change.

- **The reading model** (`tests/test_tools_package_build.py:3343` `violations()`, `:3387`
  `_followed()`): a recorded path is read as the system reads it, with the unpatched
  `lstat` / `readlink` only. From its anchor, component by component: a link (symlink, or a
  junction by `os.path.isjunction`) is replaced by its TEXT at its PHYSICAL position (an
  absolute text restarts at its anchor; the `\\?\` and `\??\` prefixes are dropped), and
  `..` steps from the physical position. A link under the release root must be admitted
  earlier, unless it is met while following an admitted link's own text (that walk
  validated it); a component reached through an OUTSIDE link's text that lies strictly
  under the release root is a violation (the residual's host alias); an alias to the root
  or above it is allowed. A component that cannot be read ends the reading; 40 hops end a
  loop. `realpath` is no longer used in the reading.
- **#1 relative paths** (`:3229` `note()`): a relative path is recorded joined to
  `os.getcwd()` of the moment, never normalised (`..` kept); a hand-built relative call is
  joined at check time; admission events the same.
  `:3775` `test_the_recorder_reads_a_relative_path_from_the_working_folder` (A's probe:
  cwd beside the `.app`, `open("Clearwater.app/Contents/Resources/pkg/data")` with no
  admission: a violation; and a recorded relative `os.lstat` carries the joined path).
- **#2 an allowed ancestor alias** (`_followed`): after an alias the reading continues at
  its physical target, so later components are recognised under the release root.
  `:3792` `test_the_recorder_reads_on_from_an_allowed_alias_physical_target` (A's probe:
  `<real tmp>/alias -> <wrapper>`, an `open` through `Contents/Resources/bin`: a violation;
  an `open` of the physical `Contents/MacOS/Clearwater` through the same alias: none).
- **#3 non-following calls** (`violations()` no longer skips them; `:3250` `os.open` still
  records `following` as "the final component followed"): every call's ANCESTORS are
  checked; `following=False` spares only the final component.
  `:3809` `test_the_recorder_checks_the_ancestors_of_a_non_following_call` (A's probe:
  modeled `O_NOFOLLOW`, a stubbed open backend returning 7; `os.open` and `lstat` of
  `Contents/Resources/pkg/data` are violations, `lstat` of the link itself is not).
  **Found, as asked:** at `4a1ccd69` EVERY call recorded `following=False` was skipped
  wholesale, ancestors included: `lstat`, `readlink`, `os.open` under `O_NOFOLLOW`,
  `DirEntry.is_dir` / `is_file` / `stat` with `follow_symlinks=False`, and the `admit`
  events. All but `admit` are now ancestor-checked. `Path.is_symlink` / `is_junction` and
  `os.path.isjunction` reach the recorder as `os.lstat` (Windows; POSIX `isjunction` makes
  no call); `DirEntry.is_symlink` / `is_junction` are not recorded (cached; listed above).
- The modeled-junction test (`test_the_recorder_sees_a_junction_as_a_link[modeled]`)
  models both spellings of `Contents/MacOS`, since the reading is now physical (macOS
  `/var` -> `/private/var`).
- **RED on `4a1ccd69`** (a throwaway detached worktree; scratch
  `work\wp6.5\ar14fold\test_ar15_recorder_red.py`, the three new tests verbatim, run
  against that revision's own recorder): **3 failed**, each at its violation assertion
  (`[]` returned). **GREEN** at `2222a794`.
- **Re-run of every recorder-dependent test** (the r11 / r13 shapes, the A r14 PATH cases
  and host cases, the recorder unit tests, the boundary, walk and missing-return tests): 23
  passed; NO product call is newly reported. Cross-check that the new reading still
  catches the residual: the PATH cases against `d1ecd039`'s `build.py` still fail
  `host-alias-into-bundle` at `recorder.violations` (and `host-link-elsewhere` at its
  message).
- **GREEN:** `test_tools_package_build.py` + `test_tools_package_notices.py` (`-n 3`):
  **1136 passed** (1133 + 3); `test_tools_package_smoke.py`: 74 passed, 1 skipped;
  `test_macos_portability.py`: 226 skipped; `ruff check .`, `ruff format --check .` (339
  files), `mypy`, `mypy --platform darwin` (166 source files): clean; committed blob 0 CR,
  0 NUL.
- **Verification loop:** suspected the physical reading turns the shapes' legitimate
  non-following calls (the walk's `lstat` / `readlink` on canonical paths, the listing's
  `DirEntry` queries) into violations: REJECTED, all green (their ancestors are physical
  by construction). Suspected the checker is now vacuous on some path (an exception or an
  early `False`): REJECTED by the three RED -> GREEN cases, the late-admission and junction
  tests, and the `d1ecd039` cross-check. Pass 2: nothing new.

Depth at A-r15-fold yield: DISPATCHER TO FILL
