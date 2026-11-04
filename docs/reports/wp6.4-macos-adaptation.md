# WP6.4 macOS adaptation: completion report

**Package:** WP6.4 (brief `docs/briefs/wp6.4-brief.md`, FINAL, with its round-0, group-A and
group-B yield rulings).

**Cells:**
- `wp64-cell1` ran round 0.
- `wp64-cell2` built group A, the product (through `283b9d78`; ledger `451799f5`).
- `wp64-cell3` built group B: the tools, the remaining W rows and the M rows (`8b3f62e8`, with
  CHARC's export grant `1a003fe4`). Its file tool refused this report (S-B2); its return carried
  the text.
- `wp64-cell4` ran the A r1 fold-in turn: the W-FS[P30] pair, this report and the ledger's turn-4
  section. S-B1 (the environment facts on by default) is NOT built at this head: the turn-4 cell
  stopped it (section 10).

The ledger is `docs/proofs/wp6.4-ledger.md`, branch `wp6.4`. **No Mac was run.** Every M test is
written to run natively and is UNEXECUTED until WP6.5. The counts below are the turn-4 cell's own
runs at `b08e9f43`. Reviewer A (Codex) round 2 on groups A + B and the package gate follow.

## 1. What was built

### Group A: the product (design items 1-10 and 12)

The per-item build cycles are recorded in ledger A.1.

- **The encoder roster per platform (item 1).**
  - darwin: `hevc_videotoolbox`, then `libx265`.
  - Every other platform: `hevc_nvenc`, then `libx265` (CHARC's ruling).
  - VT test encodes run at 8 and 10 bit with `-allow_sw 0`. A failed 10-bit trial disables 10-bit
    only.
  - The NVENC markers stay scoped to NVENC. VT has its own ASCII-safe reason.
  - A saved known encoder outside the roster is kept and shown as unavailable with its reason (D26).
- **The VT command branch (item 2).**
  - It sits behind `VT_RATE_CONTROL` (default `"B"`) and carries `-allow_sw 0`.
  - The shared `rate_ceiling` exposes `nvenc_rate`'s numeric R. `nvenc_rate` itself is unchanged,
    as the snapshots prove.
  - The geometry refusal now applies to VT as to NVENC.
- **`pipes.py` (item 3).** It uses the AD-36 statement form and AD-37's `start_new_session` (True
  off win32, an explicit False on win32). The default-pipe fallback logs at INFO off Windows.
- **The Library paths in `config/paths.py` (item 4).** See section 8.
- **User-facing text (item 7).**
  - The darwin AD-9 reason is "CPU: graphics-card processing is not available on macOS". Force CPU
    still gives "CPU: forced".
  - AUTO_TEXT is "Automatic (the hardware encoder when available)", with a tooltip that names the
    roster's hardware encoder.
  - The missing-tool text is platform-neutral (P16).
- **Filesystem identity and names.**
  - DR-121: the queue identity is `(st_dev, st_ino)`, with the lexical fallback (P29); labels are
    unchanged (D5).
  - P70: the output-name refusal names the character and the stem.
  - P71: the wheel accumulates to 120 units per step. This is the fix of a pre-existing Windows
    defect: the old `wheelEvent` zoomed a full step on any non-zero delta, so a precision touchpad
    over-zoomed (section 10).
  - P73: the preset rename never replaces (case-only rename, link then unlink, and the
    EPERM / EXDEV / ENOTSUP / EMLINK fallback with one WARNING).
- **The P55 docstrings in `interfaces/settings.py`.**
- **The CPU-only dependency expression and the `macos` marker (item 12).**

### Group B: the tools, the tests and the static step

- **Item 5, tools part.** These functions are now in the AD-36 statement form:
  - `tools/prototype/bench.py`: `_windows_power`, `_cpu_brand` and `_platform_name`. `:1467` was
    converted with `:1479`, and its stale comment corrected (D4 (d)).
  - `tools/spike_io/transport.py`: `idle_gate`.

  `mypy --platform darwin` is clean on the full `files` set.
- **Item 6: NEW `tools/footage_guard.py` `is_inside(path, root)` (DR-122).**
  - It first runs the old text check on the lexical and the resolved spellings, so nothing the old
    tools refused is accepted now.
  - It then splits each path into its nearest EXISTING ancestor and the lexical tail of names that
    do not exist yet. The path is inside when the root's existing ancestor is, by identity
    (`os.path.samestat`), the path's existing ancestor or one of that ancestor's own ancestors, and
    the remaining names begin with the root's tail (`normcase`-d).
  - A file system with no file numbers (`st_ino == 0`) falls back to text.
  - The seams `_stat`, `_normcase` and `_realpath` look their functions up at call time, so the
    existing alias tests' monkeypatches still reach them.
  - It is used at five sites, located by name at the base:
    - `inventory.main` (the old `_resolved` is removed);
    - `lookcheck/frames.check_output_path` (the footage check; the output-folder check is
      unchanged);
    - `container_spike/compare.check_output_path` (likewise);
    - `analysis_breakdown.refuse_inside`;
    - `export_oracle.refuse_inside`.
  - `halo_probe._cache_conflict` is noted only: it already uses `headless_export.inside`.
- **The ruled tool edits.**
  - D4 (a): the module-docstring label "Windows / NVIDIA evidence; not a Mac instrument", with its
    row and reason, on eight modules: `video_io_bench` (T13, T37), `reviewpack/build` (T33),
    `prototype/clip` (T34), `container_spike/spike` (T35), `video_fidelity` (T36), `export_bench`
    (T38), `core_speed` (T39) and `device_hold` (T42). The edit script asserted that each module's
    AST is otherwise equal.
  - D4 (b): `export_oracle.record_name` refuses `:` and a backslash on every platform (T52), and
    `tests/test_export_oracle.py` loses its POSIX skip (X46).
  - D4 (c): `inventory --exclude` casefolds both sides on every platform (T16).
  - Item 13: the inventory counts AppleDouble `._` names on their own summary line, "AppleDouble
    files (._ names, macOS metadata; not rows)", and never probes or lists them (T14).
  - Item 13: on darwin, `environment_report`'s NVIDIA fields are null with "not applicable on this
    platform", and `nvidia-smi` is not run there. `--platform-facts` adds the machine, the process
    architecture, the correction backend and its reason, and the roster's capability rows from the
    product's trial model (T01, T02). It is opt-in at this head: CHARC granted S-B1 (the facts on
    by default, the flag removed, one edit to `EXPECTED_KEY_ORDER`), and the turn-4 cell stopped
    that item because 16 of the 19 `tests/test_environment_report.py` tests would then reach the
    real trial seam with no stub, and the stub is a second edit to that file (section 10).
- **The export grant (CHARC, `63ff45f3`; commit `1a003fe4`).** In `jobs/export.py`, the video job's
  encoder check (the `capability is None or not capability.available` branch after
  `resolve_encoder`): a saved known encoder that the platform's capability report does not list
  now fails with "...is not available here: not offered on this platform". A listed but
  unavailable encoder keeps its own reason. The test is
  `test_portability_export_names_an_encoder_outside_the_roster`: it drives the
  `test_jobs_export_support.Rig` with `hevc_videotoolbox` (absent from the rig's report on every
  platform; red before the edit), with `hevc_nvenc` (listed as unavailable, keeps its reason) as
  the control. This closes open item 3 of ledger A.7.
- **Item 11: the tests.**
  - `tests/test_portability.py` has 180 cases, the W rows of the audit's section 8 (13 functions
    with `site` parameters), plus the snapshots, the per-character refusal, the slow real trials,
    the D3 parity test and the export-grant test.
  - NEW `tests/test_macos_portability.py` has 15 M functions and 178 cases.
  - The `macos` skip policy in `tests/conftest.py`: off darwin, every `macos` item also gets the
    skip "macOS native leg (WP6.5)".

### Turn 4: the A r1 fold-in

- **W-FS[P30] (A r1 ADVISORY).** `_fs_p30` gains the pair `Stra\u00dfe.MP4` (folder `a`) /
  `STRASSE.mp4` (folder `b`) and asserts the unchanged bare labels. The two names differ under
  `normcase` (`str.lower` on Windows, no fold elsewhere) and share only a casefold. An in-memory
  mutant of `batch_panel.item_labels` comparing by `casefold` instead of `normcase` now FAILS the
  case (it adds the parent folders); the unmutated code passes. The case count is unchanged (the
  pair is inside the existing case).
- **S-B1 (GRANTED, STOPPED this turn):** see section 10.

### Notable tests

- **The planted footage guard (W-FS T17, T26-T29).**
  - The fixture is a synthetic footage root `Dive/Footage` (with a clip). The output is under the
    differently cased existing spelling `DIVE/FOOTAGE/out`.
  - footage_guard's seams make it behave as macOS does: `normcase` folds nothing and `realpath`
    keeps the typed case, while the host's real `os.stat` gives one identity, as case-insensitive
    APFS does.
  - Each of the five sites refuses before any write, and the tree snapshot is unchanged.
  - The safe sibling `DIVE/Footage-out` passes.
  - The control: the old text check under the same seams lets the unsafe path through, so the test
    discriminates.
- **The D3 parity test.** `footage_guard` agrees with `headless_export.inside` on a real-filesystem
  containment corpus, and with `jobs.naming.is_same_path` on the equality subset (mutual
  containment).
- **W-GUARD.** A checker confirms that every Windows-only construct in the test helpers (mklink,
  junctions, ADS, 8.3 names, volume GUID, drive-relative paths, PowerShell) sits behind a platform
  guard, or behind a helper that skips off Windows, or is only called from guarded tests. A planted
  unguarded `mklink` helper fails by name.
- **W-FS[P30].** The Unicode label pair above kills the `casefold` mutant.
- **The M module.**
  - Disk images: a case-sensitive APFS image and an exFAT image are created with `hdiutil` under
    the temp folder and detached at teardown. They are attached only for the rows that need them.
  - VideoToolbox: real VT trials and encodes. A Mac without VT (a CI Mac) passes on a PROVED
    "unavailable" reason with the x265 fallback, and the VT-only cases skip with that reason.
  - The full comparator: `container_spike.compare` with D105's mandatory class for M-V4.
  - P74: a real `os.killpg` on a parent in its own session. The tool child stays in its own
    session and exits through EOF when its parent dies.
  - Cocoa: a child process for M-GUI. Qt events go only to Clearwater's own widgets.
  - M-BUNDLE: driven by `CLEARWATER_MAC_BUNDLE`.
  - Isolation: every child that imports the product gets HOME, APPDATA, LOCALAPPDATA and the XDG
    variables redirected, and a bounded timeout.
  - No test calls `clearwater.__main__`, `app.main` or the export worker's entry point.
  - Interactive native dialogs and Finder / Dock / Cmd-Q are the owner's hand checks at WP6.5.

## 2. Row-by-row disposition

Disposition categories:
- implemented (A or B) = the recommended change is built;
- validated (W) = a retain row whose portable behaviour is pinned by its W case;
- partly deferred = with the reason.

Every row also has its M case written, unexecuted. The W column names `test_portability_<function>`,
whose `site` parameter is the row ID; W-STATIC is the two mypy runs. Totals: implemented (A) 28,
implemented (B) 27, partly deferred 8, validated (W) 109; 172 rows. A site ending in `...` is
shortened; the full site is the WP6.2 audit's row.

| ID | Site | Disposition | Windows-side (test_portability_...) | Mac (written, unexecuted) |
|---|---|---|---|---|
| P01 | config/paths.py:115 | implemented (A) | `app_locations` | M-PATH[P01] |
| P02 | io/video/pipes.py:56 | implemented (A) | `spawn_policy`, W-STATIC (mypy both targets) | M-SPAWN[P02]; M-STATIC[P02] |
| P03 | io/video/pipes.py:67,85,95,112-116 | implemented (A) | `default_pipe` | M-PIPE[P03] |
| P04 | io/video/decode.py:335,350 | validated (W) | `default_pipe` | M-PIPE[P04] |
| P05 | io/video/decode.py:132-149,759; jobs/export.py... | validated (W) | `cpu_selection` | M-DEVICE[P05] |
| P06 | io/video/decode.py:72 | validated (W) | `tool_text_and_redaction` | M-TEXT[P06] |
| P07 | io/video/capability.py:35-42 | implemented (A) | `encoder_roster_and_commands` | M-CODEC[P07] |
| P08 | io/video/capability.py:109 | validated (W) | `tool_text_and_redaction` | M-TEXT[P08] |
| P09 | io/video/capability.py:50-56 | implemented (A) | `encoder_roster_and_commands` | M-CODEC[P09] |
| P10 | io/video/capability.py:57-66,160-169 | implemented (A) | `tool_text_and_redaction` | M-TEXT[P10] |
| P11 | io/video/capability.py:248-260 | implemented (A) | `encoder_roster_and_commands` | M-CODEC[P11] |
| P12 | io/video/encode.py:107 | implemented (A) | `encoder_rate_mapping` | M-RATE[P12] |
| P13 | io/video/encode.py:256 | implemented (A) | `encoder_rate_mapping` | M-RATE[P13] |
| P14 | io/video/encode.py:323 | implemented (A) | `encoder_roster_and_commands` | M-CODEC[P14] |
| P15 | io/video/encode.py:100,404-405,418-421,434-455 | validated (W) | `container_contract` | M-V4[P15] |
| P16 | io/video/probe.py:100; WP6.1 brief, round-0 ru... | implemented (A); bundle half M-BUNDLE at WP6.5 | `spawn_policy` | M-BUNDLE[P16] |
| P17 | io/video/probe.py:74 | validated (W) | `container_contract` | M-V4[P17] |
| P18 | core/memory.py:45 | validated (W) | `cpu_selection` | M-DEVICE[P18] |
| P19 | core/memory.py:85 | validated (W) | `cpu_selection` | M-DEVICE[P19] |
| P20 | core/backend.py:551 | validated (W) | `cpu_selection` | M-DEVICE[P20] |
| P21 | core/backend.py:797 | validated (W) | `cpu_selection` | M-DEVICE[P21] |
| P22 | core/backend.py:933,943,1028-1029; gui/shell.p... | implemented (A) | `cpu_selection`, `gui_contract` | M-DEVICE[P22]; M-GUI[P22] |
| P23 | core/backend.py:1027 | validated (W) | `cpu_selection` | M-DEVICE[P23] |
| P24 | app/composition.py:461; WP6.1 brief, FINAL rul... | partly deferred: bundle: M-BUNDLE at WP6.5 | `spawn_policy` | M-BUNDLE[P24] |
| P25 | app/main.py:270 | validated (W) | `app_locations` | M-PATH[P25] |
| P26 | app/startup.py:69 | validated (W) | `app_locations` | M-PATH[P26] |
| P27 | gui/sources.py:38 | validated (W) | `gui_contract` | M-GUI[P27] |
| P28 | gui/sources.py:57 | validated (W) | `filesystem_semantics` | M-FS[P28] |
| P29 | gui/batch_panel.py:94 | implemented (A) | `filesystem_semantics` | M-FS[P29] |
| P30 | gui/batch_panel.py:107 | validated (W); the Unicode pair kills the casefold mutant (turn 4) | `filesystem_semantics` | M-FS[P30] |
| P31 | gui/shell.py:465-476,488-489 | validated (W) | `gui_contract` | M-GUI[P31] |
| P32 | gui/shell.py:480 | validated (W) | `gui_contract` | M-GUI[P32] |
| P33 | gui/shell.py:274 | validated (W) | `gui_contract` | M-GUI[P33] |
| P34 | gui/batch_panel.py:149 | validated (W) | `gui_contract` | M-GUI[P34] |
| P35 | gui/preset_panel.py:126 | validated (W) | `gui_contract` | M-GUI[P35] |
| P36 | gui/settings_dialog.py:160 | validated (W) | `gui_contract` | M-GUI[P36] |
| P37 | gui/settings_dialog.py:542 | implemented (A) | `encoder_roster_and_commands` | M-GUI[P37] |
| P38 | gui/preview.py:211,294,319,383 | validated (W) | `gui_contract` | M-GUI[P38] |
| P39 | config/presets.py:70 | validated (W) | `filesystem_semantics` | M-FS[P39] |
| P40 | config/presets.py:264,549-564; docs/debt-regis... | validated (W) | `filesystem_semantics` | M-FS[P40] |
| P41 | gui/preset_panel.py:146 | validated (W) | `filesystem_semantics` | M-FS[P41] |
| P42 | jobs/naming.py:34 | validated (W) | `filesystem_semantics` | M-FS[P42] |
| P43 | jobs/naming.py:116 | validated (W) | `filesystem_semantics` | M-FS[P43] |
| P44 | jobs/naming.py:171 | validated (W) | `filesystem_semantics` | M-FS[P44] |
| P45 | jobs/naming.py:188 | validated (W) | `filesystem_semantics` | M-FS[P45] |
| P46 | jobs/naming.py:300 | validated (W) | `filesystem_semantics` | M-FS[P46] |
| P47 | jobs/export.py:111,725 | validated (W) | `filesystem_semantics` | M-FS[P47] |
| P48 | jobs/safe_write.py:112 | validated (W) | `filesystem_semantics` | M-FS[P48] |
| P49 | config/atomic.py:29-38; docs/debt-register.md:... | validated (W) | `filesystem_semantics` | M-FS[P49] |
| P50 | cache/keys.py:106 | validated (W) | `filesystem_semantics` | M-FS[P50] |
| P51 | cache/store.py:573 | validated (W) | `filesystem_semantics` | M-FS[P51] |
| P52 | io/video/inputs.py:54 | validated (W) | `filesystem_semantics` | M-FS[P52] |
| P53 | io/photo/png.py:162 | validated (W) | `filesystem_semantics` | M-FS[P53] |
| P54 | io/photo/reader.py:319 | validated (W) | `filesystem_semantics` | M-FS[P54] |
| P55 | interfaces/settings.py:34,66 | implemented (A) | `encoder_roster_and_commands` | M-CODEC[P55] |
| P56 | gpu_pack.py, pack_root; WP6.1 brief, FINAL Q6 | validated (W) | `app_locations` | M-PATH[P56] |
| P57 | __main__.py; WP6.1 brief, round-0 D1 | partly deferred: bundle: M-BUNDLE at WP6.5 | `spawn_policy` | M-BUNDLE[P57] |
| P58 | gpu_pack.py; WP6.1 brief, round-0 D2 | validated (W) | `spawn_policy`, W-STATIC (mypy both targets) | M-SPAWN[P58]; M-STATIC[P58] |
| P59 | io/video/encode.py:406-408 | implemented (A) | `encoder_rate_mapping` | M-RATE[P59] |
| P60 | io/video/encode.py:703-713 | implemented (A) | `encoder_rate_mapping` | M-RATE[P60] |
| P61 | io/video/encode.py:593-595 | implemented (A) | `encoder_rate_mapping` | M-RATE[P61] |
| P62 | io/video/encode.py:838-842 | implemented (A); export tail by CHARC grant | `encoder_roster_and_commands`; `export_names_an_encoder_outside_the_roster` | M-CODEC[P62] |
| P63 | gui/settings_dialog.py:95,507 | implemented (A) | `gui_contract` | M-GUI[P63] |
| P64 | jobs/disk_space.py:70-120,161 | validated (W) | `disk_space_estimate` | M-SPACE[P64] |
| P65 | io/video/pipes.py:56; review A r2 N1 | implemented (A) | W-STATIC (mypy both targets) | M-STATIC[P65] |
| P66 | io/video/encode.py:143-145 | validated (W) | `tool_text_and_redaction` | M-TEXT[P66] |
| P67 | cache/store.py:126-150 | validated (W) | `filesystem_semantics` | M-FS[P67] |
| P68 | io/video/encode.py:506-515 | validated (W) | `filesystem_semantics` | M-FS[P68] |
| P69 | jobs/safe_write.py:68-74 | validated (W) | `disk_space_estimate` | M-SPACE[P69] |
| P70 | jobs/naming.py:304-311 | implemented (A) | `filesystem_semantics`; `output_name_refusal_names_the_character` | M-FS[P70] |
| P71 | gui/preview.py:394-399 | implemented (A) | `gui_contract` | M-GUI[P71] |
| P72 | io/video/probe.py:67,504 | validated (W) | `tool_text_and_redaction` | M-TEXT[P72] |
| P73 | config/presets.py:395-402; docs/debt-register.... | implemented (A) | `filesystem_semantics` | M-FS[P73] |
| P74 | io/video/pipes.py:45-58; tools/headless_export.... | implemented (A) | `spawn_policy` | M-SPAWN[P74] |
| T01 | environment_report.py:172 | implemented (B): --platform-facts (opt-in; S-B1 granted, not built at this head: turn-4 STOP) | `tool_reporting` | M-TOOL[T01] |
| T02 | environment_report.py:171 | implemented (B): darwin NVIDIA fields null, not run | `tool_reporting` | M-TOOL[T02] |
| T03 | prototype/bench.py:1157-1159 | implemented (B): bench._windows_power statement form | `tool_reporting`, W-STATIC (mypy both targets) | M-TOOL[T03]; M-STATIC[T03] |
| T04 | prototype/bench.py:1467 | implemented (B): bench._cpu_brand statement form, comment fixed (D4 (d)) | `tool_reporting` | M-TOOL[T04] |
| T05 | prototype/bench.py:1479-1482 | implemented (B): bench._platform_name statement form | `tool_reporting`, W-STATIC (mypy both targets) | M-TOOL[T05]; M-STATIC[T05] |
| T06 | prototype/bench.py:156 | partly deferred: label not granted (bench.py owned at the mypy lines only); historical scope pinned | `tool_reporting` | M-TOOL[T06] |
| T07 | spike_io/transport.py:378 | validated (W) | `default_pipe` | M-PIPE[T07] |
| T08 | spike_io/transport.py:388 | validated (W) | `default_pipe` | M-PIPE[T08] |
| T09 | spike_io/transport.py:948-950 | implemented (B): transport.idle_gate statement form | `tool_reporting`, W-STATIC (mypy both targets) | M-TOOL[T09]; M-STATIC[T09] |
| T10 | spike_io/transport.py:116 | partly deferred: label not granted (transport.py owned at the mypy line only); pinned | `tool_reporting` | M-TOOL[T10] |
| T11 | spike_io/licences.py:132,149,152,158 | partly deferred: candidate DR 3 (licences.py not owned); M-TOOL xfail until it lands | `tool_reporting` | M-TOOL[T11] |
| T12 | spike_io/licences.py:188,192-210 | partly deferred: candidate DR 3; M-TOOL xfail until it lands | `tool_reporting` | M-TOOL[T12] |
| T13 | video_io_bench.py:118 | implemented (B): label (D4 (a)) | `tool_reporting` | M-TOOL[T13] |
| T14 | inventory.py:822-832 | implemented (B): inventory: AppleDouble counted apart | `filesystem_semantics` | M-FS[T14] |
| T15 | inventory.py:293,301 | validated (W) | `filesystem_semantics` | M-FS[T15] |
| T16 | inventory.py:825 | implemented (B): inventory: --exclude casefold | `filesystem_semantics` | M-FS[T16] |
| T17 | inventory.py:1112,1155 | implemented (B): footage_guard (DR-122) | `filesystem_semantics` | M-FS[T17] |
| T18 | inventory.py:1094 | validated (W) | `filesystem_semantics` | M-FS[T18] |
| T19 | local_config.py:140 | validated (W) | `filesystem_semantics` | M-FS[T19] |
| T20 | local_config.py:196 | validated (W) | `filesystem_semantics` | M-FS[T20] |
| T21 | headless_export.py:598 | validated (W) | `filesystem_semantics` | M-FS[T21] |
| T22 | headless_export.py:761 | validated (W) | `filesystem_semantics` | M-FS[T22] |
| T23 | headless_export.py:790,801 | validated (W) | `filesystem_semantics` | M-FS[T23] |
| T24 | headless_export.py:826,870 | validated (W) | `filesystem_semantics` | M-FS[T24] |
| T25 | headless_export.py:414 | validated (W) | `tool_text_and_redaction` | M-TEXT[T25] |
| T26 | lookcheck/frames.py:161 | implemented (B): footage_guard | `filesystem_semantics` | M-FS[T26] |
| T27 | container_spike/compare.py:1877 | implemented (B): footage_guard | `filesystem_semantics` | M-FS[T27] |
| T28 | analysis_breakdown.py:984 | implemented (B): footage_guard | `filesystem_semantics` | M-FS[T28] |
| T29 | export_oracle.py:645 | implemented (B): footage_guard | `filesystem_semantics` | M-FS[T29] |
| T30 | halo_probe.py:2360 | partly deferred: noted only (brief); pinned: reuses headless_export.inside | `filesystem_semantics` | M-FS[T30] |
| T31 | halo_probe.py:2373 | validated (W) | `filesystem_semantics` | M-FS[T31] |
| T32 | reviewpack/select.py:230 | validated (W) | `filesystem_semantics` | M-FS[T32] |
| T33 | reviewpack/build.py:875 | implemented (B): label | `encoder_roster_and_commands` | M-CODEC[T33] |
| T34 | prototype/clip.py:133 | implemented (B): label | `encoder_roster_and_commands` | M-CODEC[T34] |
| T35 | container_spike/spike.py:78 | implemented (B): label | `encoder_roster_and_commands` | M-CODEC[T35] |
| T36 | video_fidelity.py:377 | implemented (B): label | `encoder_roster_and_commands` | M-V4[T36] |
| T37 | video_io_bench.py:147 | implemented (B): label | `encoder_roster_and_commands` | M-CODEC[T37] |
| T38 | export_bench.py:580 | implemented (B): label | `tool_reporting` | M-TOOL[T38] |
| T39 | core_speed.py:350 | implemented (B): label | `tool_reporting` | M-TOOL[T39] |
| T40 | analysis_breakdown.py:848 | validated (W) | `tool_reporting` | M-TOOL[T40] |
| T41 | photo_verify.py:1161 | validated (W) | `tool_reporting` | M-TOOL[T41] |
| T42 | device_hold.py:57 | implemented (B): label | `cpu_selection` | M-DEVICE[T42] |
| T43 | prototype/backend.py:197 | validated (W) | `cpu_selection` | M-DEVICE[T43] |
| T44 | fixtures/video.py:317 | validated (W) | `encoder_roster_and_commands` | M-CODEC[T44] |
| T45 | fixtures/files.py:36 | validated (W) | `filesystem_semantics` | M-FS[T45] |
| T46 | photo_check.py:68 | validated (W) | `filesystem_semantics` | M-FS[T46] |
| T47 | photo_verify.py:332 | validated (W) | `filesystem_semantics` | M-FS[T47] |
| T48 | photo_memory.py:162 | validated (W) | `filesystem_semantics` | M-FS[T48] |
| T49 | prototype/bench.py:1480; review A r2 N1 | implemented (B): as T05 | W-STATIC (mypy both targets) | M-STATIC[T49] |
| T50 | prototype/bench.py:1159; review A r2 N1 | implemented (B): as T03 | W-STATIC (mypy both targets) | M-STATIC[T50] |
| T51 | spike_io/transport.py:950; review A r2 N1 | implemented (B): as T09 | W-STATIC (mypy both targets) | M-STATIC[T51] |
| T52 | export_oracle.py:661 | implemented (B): export_oracle.record_name refuses : and backslash | `filesystem_semantics` | M-FS[T52] |
| X01 | conftest.py:111 | validated (W) | `footage_guard_and_test_helpers` | M-GUARD[X01] |
| X02 | conftest.py:215 | validated (W) | `footage_guard_and_test_helpers` | M-GUARD[X02] |
| X03 | conftest.py:134 | validated (W) | `footage_guard_and_test_helpers` | M-GUARD[X03] |
| X04 | conftest.py:214 | validated (W) | `footage_guard_and_test_helpers` | M-GUARD[X04] |
| X05 | test_conftest_guard.py:82 | validated (W) | `footage_guard_and_test_helpers` | M-GUARD[X05] |
| X06 | test_conftest_guard.py:329 | validated (W) | `footage_guard_and_test_helpers` | M-GUARD[X06] |
| X07 | test_conftest_guard.py:337 | validated (W) | `footage_guard_and_test_helpers` | M-GUARD[X07] |
| X08 | test_conftest_guard.py:346 | validated (W) | `footage_guard_and_test_helpers` | M-GUARD[X08] |
| X09 | test_conftest_guard.py:381 | validated (W) | `footage_guard_and_test_helpers` | M-GUARD[X09] |
| X10 | test_conftest_guard.py:478 | validated (W) | `footage_guard_and_test_helpers` | M-GUARD[X10] |
| X11 | test_conftest_guard.py:599 | validated (W) | `footage_guard_and_test_helpers` | M-GUARD[X11] |
| X12 | test_conftest_guard.py:670 | validated (W) | `footage_guard_and_test_helpers` | M-GUARD[X12] |
| X13 | test_config_paths.py:44 | implemented (A) | `app_locations` | M-PATH[X13] |
| X14 | test_config_isolation.py:31 | validated (W) | `app_locations` | M-PATH[X14] |
| X15 | test_app_startup.py:178 | implemented (A) | `app_locations` | M-PATH[X15] |
| X16 | test_gui_startup.py:206 | implemented (A) | `app_locations` | M-PATH[X16] |
| X17 | test_app_wiring.py:415 | validated (W) | `footage_guard_and_test_helpers` | M-GUARD[X17] |
| X18 | test_footage_locator.py:48 | validated (W) | `footage_guard_and_test_helpers` | M-GUARD[X18] |
| X19 | test_footage_locator.py:78 | validated (W) | `filesystem_semantics` | M-FS[X19] |
| X20 | test_inventory.py:81 | validated (W) | `filesystem_semantics` | M-FS[X20] |
| X21 | test_headless_export.py:603 | validated (W) | `footage_guard_and_test_helpers` | M-GUARD[X21] |
| X22 | test_headless_export.py:629 | validated (W) | `filesystem_semantics` | M-FS[X22] |
| X23 | test_io_video_decode_lifecycle.py:407 | validated (W) | `default_pipe` | M-PIPE[X23] |
| X24 | test_io_video_decode_lifecycle.py:424 | validated (W) | `default_pipe` | M-PIPE[X24] |
| X25 | test_io_video_decode_rules.py:97 | validated (W) | `tool_text_and_redaction` | M-TEXT[X25] |
| X26 | test_io_video_spawn.py:274,278 | validated (W) | `spawn_policy` | M-SPAWN[X26] |
| X27 | test_io_video_spawn.py:324 | validated (W) | `spawn_policy` | M-SPAWN[X27] |
| X28 | test_jobs_export_process.py:544 | partly deferred: bundle: M-BUNDLE at WP6.5 | `spawn_policy` | M-BUNDLE[X28] |
| X29 | test_jobs_naming.py:182 | validated (W) | `filesystem_semantics` | M-FS[X29] |
| X30 | test_jobs_naming.py:452 | validated (W) | `footage_guard_and_test_helpers` | M-GUARD[X30] |
| X31 | test_reviewpack.py:366 | validated (W) | `footage_guard_and_test_helpers` | M-GUARD[X31] |
| X32 | test_wp42a_runner_hardening.py:99 | validated (W) | `footage_guard_and_test_helpers` | M-GUARD[X32] |
| X33 | test_wp42a_runner_hardening.py:134 | validated (W) | `footage_guard_and_test_helpers` | M-GUARD[X33] |
| X34 | test_wp42a_runner_hardening.py:197 | validated (W) | `footage_guard_and_test_helpers` | M-GUARD[X34] |
| X35 | test_wp42a_runner_hardening.py:234 | validated (W) | `footage_guard_and_test_helpers` | M-GUARD[X35] |
| X36 | test_wp42a_runner_hardening.py:464 | validated (W) | `footage_guard_and_test_helpers` | M-GUARD[X36] |
| X37 | test_wp42b_naming_guard.py:29 | validated (W) | `footage_guard_and_test_helpers` | M-GUARD[X37] |
| X38 | test_wp42_runner_video.py:74 | validated (W) | `footage_guard_and_test_helpers` | M-GUARD[X38] |
| X39 | gui_support.py:12 | validated (W) | `gui_contract` | M-GUI[X39] |
| X40 | test_gui_preview.py:349 | validated (W) | `gui_contract` | M-GUI[X40] |
| X41 | test_gui_settings_dialog.py:489 | validated (W) | `encoder_roster_and_commands` | M-GUI[X41] |
| X42 | test_io_video_encode.py:77 | validated (W) | `encoder_roster_and_commands` | M-V4[X42] |
| X43 | test_io_video_encode.py:1851 | validated (W) | `encoder_roster_and_commands` | M-CODEC[X43] |
| X44 | test_core_backend.py:35 | validated (W) | `cpu_selection` | M-DEVICE[X44] |
| X45 | acceptance_support.py:73 | validated (W) | `tool_text_and_redaction` | M-TEXT[X45] |
| X46 | test_export_oracle.py:303-309 | implemented (B): POSIX skip removed | `filesystem_semantics` | M-FS[X46] |

## 3. The VT argument lists, per depth and quality, for both Q1 candidates

Source: ledger A.2 and the evidence file `vt-argument-lists-group-a.txt`. The encoder segment is
shown below. Everything outside it is NVENC's argument list, byte for byte (W-V4[P15]). Each R is
`nvenc_rate`'s maxrate for the same case (W-RATE[P13]).

R values:
- 4K60 HEVC source (level 5.1 Main, so R is capped at 40 Mb/s): High 40,000,000; Standard
  20,000,000; Draft 10,000,000.
- 1080p29.97 H.264 source (no source cap): High 14,915,004; Standard 7,457,502; Draft 3,728,751.

Candidate B (the default):

    -c:v hevc_videotoolbox -allow_sw 0 -b:v R -maxrate R -pix_fmt yuv420p -profile:v main      (8-bit)
    -c:v hevc_videotoolbox -allow_sw 0 -b:v R -maxrate R -pix_fmt p010le -profile:v main10     (10-bit)

Candidate A (`VT_RATE_CONTROL = "A"`). The Q values are PLACEHOLDERS, measured at WP6.5 (High 65,
Standard 55, Draft 45):

    -c:v hevc_videotoolbox -allow_sw 0 -q:v Q -maxrate R -pix_fmt yuv420p -profile:v main      (8-bit)
    -c:v hevc_videotoolbox -allow_sw 0 -q:v Q -maxrate R -pix_fmt p010le -profile:v main10     (10-bit)

At 10-bit the `-vf` chain still ends `format=yuv420p10le,setparams=...` (AD-10 unchanged).

The trials:
- 8-bit: `-c:v hevc_videotoolbox -allow_sw 0 -pix_fmt yuv420p -profile:v main`
- 10-bit: `... -pix_fmt p010le -profile:v main10`

## 4. The NVENC and x265 snapshot evidence

Source: ledger A.3. `capture_snapshots.py` ran on the base tree `c1458747` and on the head:
- the 24-case sha256 grid is equal;
- the 4 full argument literals are equal;
- the 4 trial commands are equal.

`test_portability_windows_encoder_command_snapshot[hevc_nvenc, libx265]` holds the base literals.
It passed on the unchanged code before any edit, and on every later commit.

## 5. The dual-target mypy output

At `b0c0d5fd` (turn 4; `b08e9f43` after it changes only a test file's escapes, outside mypy's
`files`), run from the worktree root:

    uv run --no-sync mypy                    Success: no issues found in 162 source files
    uv run --no-sync mypy --platform darwin  Success: no issues found in 162 source files

At the base, the darwin target found 4 errors in 3 files: `pipes.py:56`, `prototype/bench.py:1159`
and `:1480`, and `spike_io/transport.py:950`. At the group-A yield 3 remained, all tool sites. At
group B there are 0, and still 0 at turn 4. `strict` and `warn_unreachable` are unchanged, and
there is no `platform` key in `[tool.mypy]`.

## 6. The lock diff summary

Source: ledger A.4 and `uv-lock.record.txt`.
- `uv lock --offline` exited 0 (uv 0.10.9, 70 packages), and `uv lock --check --offline` exited 0.
- A tomllib comparison against `c1458747:uv.lock` found:
  - the top-level keys equal (`version 1`, `revision 3`, no `resolution-markers`);
  - the same 70 package names;
  - no package other than `clearwater` changed, and no version moved.
- The diff is 4 lines, all in the `clearwater` entry: the darwin marker on the four cupy edges.
- `test_gpu_pack.py::test_locked_distributions_equal_the_lock` passes, so the eleven pack wheels
  are unchanged.

## 7. The W and M test counts per gate leg

Re-taken by the turn-4 cell at `b08e9f43` (`-p no:cacheprovider --timeout 600`,
`QT_QPA_PLATFORM=offscreen`; the parallel expression with `-n 4`, the serial expression without):

| Module | Parallel leg (collected / passed / skipped) | Serial leg (collected / passed / skipped) | Fullclip |
|---|---|---|---|
| `test_portability` (180) | 163 / 163 / 0 | 17 / 17 / 0 (14 `gui`, 3 `slow`) | 0 |
| `test_macos_portability` (178) | 159 / 0 / 159 | 19 / 0 / 19 (`macos` + `gui`: M-GUI 15, M-BUNDLE 4) | 0 |
| `test_environment_report` (19) | 19 / 19 / 0 | 0 | 0 |

The three modules together: parallel 182 passed, 159 skipped; serial 17 passed, 19 skipped.

On Windows every M case is collected and skipped with "macOS native leg (WP6.5)"; no other skip
reason appears. The gate's two marker expressions are unchanged, and the collection identity
counts the M cases.

The M functions, with their case counts:

| Function | Cases |
|---|---|
| M-STATIC | 9 |
| M-PATH | 8 |
| M-SPAWN | 5 |
| M-PIPE | 6 |
| M-DEVICE | 10 |
| M-TEXT | 8 |
| M-CODEC | 12 |
| M-RATE | 5 |
| M-V4 | 4 |
| M-SPACE | 2 |
| M-FS | 51 |
| M-GUARD | 24 |
| M-TOOL | 15 |
| M-GUI | 15 |
| M-BUNDLE | 4 |

The package gate's full-suite figures are the gate's (not run by a cell).

## 8. The Library path table as built

| Platform | config_dir: settings.json, presets/, logs/clearwater.log, write-journal.json | cache_dir | GPU pack root |
|---|---|---|---|
| win32 | `%APPDATA%\Clearwater` | `%LOCALAPPDATA%\Clearwater\cache` | `%LOCALAPPDATA%\Clearwater\gpu-pack` |
| darwin | `~/Library/Application Support/Clearwater` | `~/Library/Caches/Clearwater` | None (no lookup) |
| other | `$XDG_CONFIG_HOME/clearwater` (default `~/.config/clearwater`) | `$XDG_CACHE_HOME/clearwater` (default `~/.cache/clearwater`) | `$XDG_DATA_HOME/clearwater/gpu-pack` |

- The home is the existing injectable parameter (HOME through `Path.home()`). No override variable
  was added.
- There is no migration from XDG on macOS (AD-25(a)): a Mac developer with data under
  `~/.config/clearwater` starts fresh.

## 9. The dependency expression

    gpu = ["cupy-cuda12x[ctk]>=14.2,<15; sys_platform != 'darwin'"]                (the gpu extra)
    "cupy-cuda12x[ctk]>=14.2,<15; sys_platform != 'darwin'",                       (the dev group)

A Mac `uv sync` installs no CuPy, and the product runs CPU-only (P22).

## 10. Limits

- **No Mac was run.** Every M test is unexecuted until WP6.5.
- **The VT texts are SYNTHETIC.** The VT listing and help texts (`tests/ffmpeg_text/`), the VT
  stderr markers and the macOS showinfo sample lines are synthetic. WP6.5 replaces them with a
  capture.
- **Interactive checks are the owner's.** The native file dialogs (P33-P36: picking a file), and
  the bundle's Finder / Terminal launch, Dock Quit, Cmd-Q and logout during an export, are the
  owner's hand checks at WP6.5. No synthetic desktop input is used.
- **M-DEVICE checks the CPU-only selection and reasons natively.** The comparison of the Mac CPU
  output with the Windows references within AD-11's tolerances is not written yet; it is WP6.5's.
- **Linux has a roster (NVENC then x265, as ruled), but nothing is proved for Linux.**
- **P71's Windows behaviour change is the FIX of a pre-existing Windows defect.** The old
  `wheelEvent` zoomed a full step on any non-zero delta, so a precision touchpad over-zoomed.
  - A mouse notch (120) is unchanged.
  - Sub-120 touchpad deltas now accumulate to one step.
  - A single 240 event now takes two steps.
  - Not checked on real hardware.
- **The jobs/export.py empty-reason gap** (ledger A.7, item 3) is closed by CHARC's grant
  (`1a003fe4`; section 1).
- **S-B1 is open at this head.** CHARC granted the environment facts on by default (the
  `--platform-facts` flag and the `platform_facts` parameter removed; one edit to
  `tests/test_environment_report.py`'s `EXPECTED_KEY_ORDER`). The turn-4 cell stopped the item
  before any edit: an in-memory simulation of the default-on change showed 16 of the module's 19
  tests reaching `_correction_backend` (the product's CuPy probe) and `_encoder_rows` (the
  product's FFmpeg trials) with no stub, and adding the stub is a second edit to that file. The
  same turn found that M-TOOL[T01] / [T02] run their W case and their native half on ONE
  monkeypatch, so on a Mac the native half would read the W stubs (encoders `['libx265']`, and
  `sys.platform` left at `win32` for T02) and fail. Both wait for the dispatcher's ruling (ledger
  turn-4 section).
- **The rows built only in part without a Mac.** For ONE register row at the accept; each row with
  its Windows proof and the WP6.5 native check that closes it (ledger B.6):

| Row(s) | Windows proof (W) | WP6.5 native check (M) that closes it |
|---|---|---|
| P09 P10 P12 P14 P59 | the VT argument lists, reasons and branch from snapshot / argv and the SYNTHETIC listings (W-CODEC, W-RATE, W-TEXT) | M-CODEC[P09, P14]: real VT 8 / 10-bit trials and a sink encode. M-RATE: both Q1 candidates under R. M-TEXT[P08, P10]: the real listing and reasons. Plus replacing the synthetic listings with a capture |
| P01 P25 P26 | injected-home Library paths (W-PATH) | M-PATH: a child with HOME redirected resolves the Library roots natively |
| P03 P74 | INFO fallback and `start_new_session` built with stubs (W-PIPE, W-SPAWN) | M-PIPE[P03]: the native INFO fallback. M-SPAWN[P74]: `os.killpg` leaves the child in its own session, and it exits on its parent's death |
| P22 | the darwin reason through a patched platform (W-DEVICE, W-GUI) | M-DEVICE: the reason with no CuPy installed. M-GUI[P22]: the Cocoa status text |
| P29 | identity on a fake stat and on NTFS (W-FS) | M-FS[P29]: case-insensitive and case-sensitive APFS images |
| P73 | the link / unlink / fallback branches stubbed (W-FS) | M-FS[P40, P41, P49, P73]: the DR-34(a) folding corpus on both APFS modes. M-FS[P48]: exFAT link refusal |
| P71 | synthetic offscreen `QWheelEvent`s (W-GUI) | M-GUI[P71]: Cocoa wheel phases including momentum; the owner's trackpad by hand |
| T14 | a synthetic `._` tree (W-FS) | M-FS[T14]: exFAT AppleDouble files made by `xattr` |
| T17 T26-T29 | the planted case alias reproduced through footage_guard's text and link-resolution seams on NTFS (W-FS) | M-FS[T17, T26-T29]: a native symlink alias and a native case alias |
| T01 T02 | the environment facts with stubs (W-TOOL); opt-in, S-B1 | M-TOOL[T01, T02]: the native report (arm64, macosx-*, NVIDIA not applicable, the VT / x265 rows) |
| T11 T12 | the Windows licence-scan forms are pinned (W-TOOL) | M-TOOL[T11, T12]: xfail until candidate DR 3 adds the Mach-O forms |
| P16 P24 P57 X28 | source / frozen command construction (W-SPAWN) | M-BUNDLE with `CLEARWATER_MAC_BUNDLE`, plus the owner's Finder, Dock-Quit and Cmd-Q checks |
| (no row ID) M-DEVICE AD-11 | none on Windows | the Mac CPU output against the Windows references within AD-11's tolerances; not yet written, WP6.5 |

- **Other notes.**
  - The P30 labels are unchanged (D5); turn 4's Unicode pair pins that against a casefold change.
  - `tools/package/build.py:645` is reported only (WP6.3b, D4 (d)).
  - The `test_prototype_clip` order dependence is not caused by this package. It is reproduced on
    main at HEAD.
  - Two failures under `-n 4` in group B's runs (a MemoryError in `analysis_breakdown` and the
    container spike's x265 proof) passed serially; host load.
