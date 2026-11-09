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

Depth at group-2a part-2 r1 yield: DISPATCHER TO FILL
