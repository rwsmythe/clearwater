# WP6.5 macOS validation -- cell ledger (`wp65-cell1`, implementer-opus-high)

Brief `docs/briefs/wp6.5-brief.md` (FINAL, the orchestrator's fill at `49ca01bf`); dispatch
`clearwater-review-evidence\wp6.5\cell\dispatch-1.md`. The cell keeps this file; the
dispatcher fills the depth figures.

## Cumulative round ledger

| Round | Reviewer | Blocking (crit/major) | Minor/nit | In-envelope / out | NEW / REOPENED | Reverts | Fixes: product / tests-only | Depth (dispatcher) |
|---|---|---|---|---|---|---|---|---|
| 0 | none (read-only work list) | - | - | - | - | 0 | none (no edit) | DISPATCHER TO FILL |

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

Depth at round-0 end: DISPATCHER TO FILL
