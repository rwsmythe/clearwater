# WP6.4 macOS adaptation -- cell ledger (`wp64-cell1`, implementer-opus-high)

Brief `docs/briefs/wp6.4-brief.md` (FINAL at `c1458747`); dispatch
`clearwater-review-evidence\wp6.4\cell\dispatch-1.md`. The cell keeps this file; the
dispatcher fills the depth figures.

## Cumulative round ledger

| Round | Reviewer | Blocking (crit/major) | Minor/nit | In-envelope / out | NEW / REOPENED | Reverts | Fixes: product / tests-only | Transport, CLI | Depth (dispatcher) |
|---|---|---|---|---|---|---|---|---|---|
| 0 | none (read-only work list) | - | - | - | - | 0 | none (no edit) | - | 247,937 (cell1, at return) |

## Round 0

Read-only turn at base `c1458747` (worktree `.worktrees/wp6.4`). No product edit, no
`pyproject.toml` / `uv.lock` change, no `uv lock`. Runs made: `mypy` on both targets
(scratch cache dirs), four existing pin tests (5 cases, `--basetemp=work/wp6.4/r0-pins`,
5 passed in 0.51 s), the laptop FFmpeg's `-encoders` and `-h encoder=hevc_videotoolbox`, and
one `tools/fixtures/manifest.check_files` call on a scratch COPY of `tests/fixtures`. No
product entry point was called.

### 0.1 STOPs and disputes (each needs a seat / CHARC ruling before turn 2)

- **S1 (STOP, reproduced) -- the VT listing fixture cannot live under `tests/fixtures/`.**
  `tools/fixtures/manifest.py:443-450` (`check_files`) reports every file under
  `tests/fixtures/` that `manifest.json` does not list, and
  `tests/test_fixtures.py:86-87` asserts that list is empty. `tests/test_fixtures.py:90-117`
  also pins the manifest's sample id set exactly. Neither file is owned. Reproduction: a
  scratch copy of `tests/fixtures` plus `ffmpeg-text/vt-encoders.txt` gives
  `['ffmpeg-text/vt-encoders.txt: not listed in the manifest']`. So the brief's location
  (Hardware flags row) fails an existing test whatever the content.
  **Recommended:** a new folder `tests/ffmpeg_text/` (outside the manifest root, owned as
  new) with `README.md` (provenance: SYNTHETIC, replaced by WP6.5's capture) and the two
  `.txt` listings. Alternative: a manifest entry, which needs `tests/fixtures/manifest.json`
  AND `tests/test_fixtures.py:90-117` granted. Readers use `splitlines()`, so a CRLF checkout
  is harmless.
- **S2 (STOP) -- an existing, unowned test pins darwin to XDG.**
  `tests/test_config_paths.py:44-49` `test_xdg_variables_win_elsewhere[darwin]` expects
  `cfg/clearwater` on darwin (green at base, 2 of the 5 passes above). Design item 4 (AD-25(a)
  as amended) makes darwin ignore XDG, so this case fails by construction. Audit row X13 says
  "split darwin native roots from Linux XDG expectations". The Done row allows only the two
  start-up tests and the interface docstring assertion to change.
  **Recommended:** grant `tests/test_config_paths.py`, edit limited to the parametrize line
  (`["linux"]`). The darwin Library expectations move to W-PATH[X13] in
  `tests/test_portability.py`.
- **D1 -- design item 8 (P73) would break a case-only preset rename on default APFS.**
  `config/presets.py:401-402` already allows `rename("look", "Look")`, pinned by
  `tests/test_config_presets.py:194-197` (green at base). On a case-insensitive volume
  `os.link("look.json", "Look.json")` fails with `FileExistsError`, because the target is the
  source itself. **Recommended:** keep the `_matches` prediction. When the only match is the
  source itself (`source.name.casefold() == target.name.casefold()`, or `samefile(source,
  target)`), use `os.rename`: there is nothing else it could replace. Otherwise
  `os.link`+`os.unlink`. Fall back to `os.rename` with a WARNING naming the file on
  `EPERM`, `EXDEV`, `ENOTSUP` / `EOPNOTSUPP` or `EMLINK`, so exFAT on a Mac is covered: link
  is not supported there. win32 stays `os.rename`. The same no-replace sequence is AD-25(b)'s,
  in `jobs/safe_write.py`. `config/` should not import `jobs/`, so the few lines are repeated
  in `presets.py`.
- **D2 -- W-GUI cannot be unmarked.** In `tests/`, 21 of the 22 modules that use
  `qtbot` / `QApplication` carry `pytest.mark.gui`. The 22nd is `gui_support.py`, a helper
  module. The parallel leg excludes `gui`. **Recommended:** `test_portability_gui_contract` is
  marked `gui`, so it runs in the serial leg. Every other W function stays unmarked, which
  keeps the brief's Markers row for everything that needs no Qt.
- **D3 -- Q4's "jobs/ product check" is not a containment check.** The product's guard is
  `jobs/naming.py:174-192` `is_same_path`, which compares the identity of two paths (P45). The
  closest containment reference, nearest existing ancestor by `samestat`, is the tools-side
  `tools/headless_export.py:774-805` `inside`. **Recommended:** the one parity test compares
  `footage_guard.is_inside` with `headless_export.inside` on the containment corpus, and with
  `naming.is_same_path` on its equality subset (path == root spellings). Both references are
  imported read-only by the test; the helper imports neither.
- **D4 -- items whose sites lie outside the owned files.** Each needs a grant or a
  report-only disposition:
  (a) item 13's labels "Windows / NVIDIA evidence; not a Mac instrument" belong in module
  docstrings of unowned tools: `video_io_bench.py` (T13/T37), `reviewpack/build.py` (T33),
  `prototype/clip.py` (T34), `container_spike/spike.py` (T35), `video_fidelity.py` (T36),
  `export_bench.py` (T38), `core_speed.py` (T39), `device_hold.py` (T42). Two more are only
  partly owned: `spike_io/transport.py` (T07/T10) and `prototype/bench.py` (T06), each
  owned at the mypy lines only. **Recommended:** grant module-docstring-only edits to those
  files.
  (b) T52 / X46 are not in the brief. `tools/export_oracle.py:661` uses `Path(name).anchor`,
  so `C:x` is accepted on POSIX, while `tests/test_export_oracle.py:303-309` expects `C:x`
  refused everywhere. That expectation fails natively on a Mac. **Recommended:** grant an
  explicit `:` / `\` refusal at `export_oracle.py:661`, like `halo_probe.py:2373` (T31).
  That file is already touched at `:645` for DR-122, and the test stays unchanged.
  (c) T16 is not in the brief. `tools/inventory.py:825` compares the excluded folder name
  with `normcase`, which folds case on Windows only. That range (`:822-832`) is owned.
  **Recommended:** `casefold()` on both sides on every platform. The result is identical on
  Windows for ASCII names. Exact-case and varied-case controls go in W-FS[T16].
  (d) AD-36 asks for every guard in the statement form. `tools/package/build.py:645`
  (`".exe" if sys.platform == "win32" else ""`) is WP6.3b's and not owned. It passes both
  mypy targets. **Recommended:** report it to WP6.3b, no edit here.
  `tools/prototype/bench.py:1467` (`os.name == "nt"`, T04) is in the owned file but not on
  an owned line. Its comment "(not sys.platform: mypy would drop the other branch)" becomes
  stale once `:1479` is converted. **Recommended:** convert it in the same edit as `:1479`
  and fix the comment.
- **D5 -- P30 labels, a reading.** The brief says "labels follow the same identity".
  Consider two distinct files whose names differ only by case: in different folders they
  already get distinct label text, and in one folder on a case-sensitive volume their names
  differ textually. `item_labels` (`gui/batch_panel.py:97-112`) therefore never hides a
  distinction. **Recommended:** no code change to labels. W-FS[P30] pins them for one file
  under two spellings (one item, one label) and for two case-distinct files (two items, two
  labels). The alternative is `casefold` labels, which changes Windows text for non-ASCII
  names.
- **D6 -- group split, see 0.8.** Group A writes the tests that pin its own behaviour.

Noted, no ruling needed:
- **N1 -- the spawn helper's shape.** `tests/test_io_video_spawn.py:239-264` requires exactly
  one `creationflags` dict setter inside `tool_spawn_kwargs`. `:267-284` requires
  `creationflags == 0` under a patched `linux`. Both files are unowned and must stay
  unchanged. The plan is one dict built after an AD-36 `if`/`else` that sets two locals:
  win32 `CREATE_NO_WINDOW` / `False`, else `0` / `True`, returned as
  `{"creationflags": flags, "start_new_session": new_session, "env": ...}`. On Windows
  `start_new_session=False` is passed explicitly. It is Popen's default and is ignored there,
  so no Windows behaviour changes. The TypedDict gains `start_new_session: bool`.
- **N2 -- the Linux roster becomes `(libx265,)`, as brief item 1 says.** Today Linux is
  offered NVENC too. Nothing is proved for Linux, but a Linux developer with an NVIDIA card
  loses NVENC. Recorded as a limit in the report.
- **N3 -- P74's `tools/headless_export.py:1391` is the runner's SIGINT handler, not a
  spawn.** The runner spawns through the product's helper, so AD-37 reaches it with no
  tools edit. With `start_new_session=True` a Terminal Ctrl+C reaches only the runner, and
  its handler cancels in order, which is the intended effect.
- **N4 -- the VT export carries `-allow_sw 0` explicitly, as the trials do.** It is FFmpeg's
  default, so this only makes the hardware claim checkable from the argv.
- **N5 -- the AD-36 form also covers `pipes.py:67-85`.** `_create_pipe`'s trailing
  `raise OSError(...)` runs only off win32, so it moves into the `else` branch. Behaviour is
  unchanged.

### 0.2 Work list at base `c1458747` (design items 1-13)

Product paths are relative to `src/clearwater/`; tool paths to `tools/`.

| Item | Sites at base (file:line, by name) | Audit rows | Misses / drift |
|---|---|---|---|
| 1 roster | `io/video/capability.py:35` `HARDWARE_ENCODER`, `:38` `SOFTWARE_ENCODER`, `:41` `ENCODERS`; `:50-56` `_TEST_PIX_FMT` / `_PROFILE`; `:57-66` `_NO_DEVICE_MARKERS`; `:104-114` `_listed`; `:117-151` `trial_encode_command`; `:160-169` `_reason`; `:172-198` `_detect`; `:201-225` `detect_capabilities`; `:228-264` `resolve_encoder` (`:248` explicit, `:258` auto); `io/video/encode.py:599-605` `capabilities`; `:832-842` `_check_options`; `gui/settings_dialog.py:497-529` `_populate_encoders`, `:95` `AUTO_TEXT` | P07 P08 P09 P10 P11 P37 P55 P62 | Field is `EncoderCapability.hw` (`interfaces/video.py:227`), not "hardware". Plan: `KNOWN_ENCODERS` = nvenc, VT, x265 (validation); the platform roster via an injectable `encoder_roster(platform)`; `ENCODERS` = the running platform's roster, unchanged on win32. A known name outside the roster resolves unchanged and is refused at `open` as `"unavailable"` with a reason (D26); an unknown name stays `"refused"`. The dialog already keeps a saved unreported name disabled (`NOT_FOUND_REASON`, `:516-526`). |
| 2 VT branch + rate | `io/video/encode.py:236-248` `NvencRate`; `:256-300` `nvenc_rate`; `:323-338` `_encoder_options`; `:347-459` `encode_command` (rate `:406-408`); `:593-595` `VideoSink.nvenc_rate`; `:703-713` `_prepare` rate + geometry refusal; `:733` state assignment | P12 P13 P14 P59 P60 P61 | none |
| 3 spawn / pipe | `io/video/pipes.py:38-42` `_ToolSpawnKwargs`; `:45-58` `tool_spawn_kwargs` (`:56` expression); `:61-85` `_create_pipe` (`:85` raise after guard); `:88-95` `_log_fallback` (`:95` WARNING); module docstring `:9-12` | P02 P03 P65 P74 | P74's tools line is not a spawn (N3); see N1 for the shape |
| 4 Library paths | `config/paths.py:93-136` `app_locations` (`:116` win32 branch, `:127-136` XDG); module table `:7-12`; `POSIX_FOLDER_NAME` `:32`; `app/main.py:270` and `app/startup.py:69` read `Locations.config_dir` (unowned, unchanged) | P01 P25 P26 P56 X13-X16 | X13 is S2. DR-124: `tests/test_app_startup.py:175-196` sets APPDATA/LOCALAPPDATA/XDG only (`:180-183`), with no HOME / USERPROFILE, and asserts `written in (["roaming"], ["xdg-config"])` `:196`. `tests/test_gui_startup.py:204-209` `_sentinel_environment` already sets HOME / USERPROFILE. |
| 5 guard form | `io/video/pipes.py:56`, `:67-85`; `tools/prototype/bench.py:1157-1159`, `:1479-1482` (and `:1467`, D4(d)); `tools/spike_io/transport.py:948-950`; already in form: `gpu_pack.py:970-985`, `app/export_worker.py:165-176`, `spike_io/transport.py:378` | P02 P58 P65 T03 T05 T09 T49 T50 T51 | `tools/package/build.py:645`: D4(d) |
| 6 identity | `gui/batch_panel.py:92-94` `_key` (normcase/abspath), `:97-112` `item_labels` (`:107`), `:272-282` queue use; tool guards `tools/inventory.py:1111-1112` `_resolved` used at `:1150-1160`; `tools/lookcheck/frames.py:161`; `tools/container_spike/compare.py:1877`; `tools/analysis_breakdown.py:984-985`; `tools/export_oracle.py:645-646`; noted `tools/halo_probe.py:2360-2361`; product pin `jobs/naming.py:174-192` `is_same_path` | P29 P30 P43 P44 P45 T17 T26-T30 | D3, D5. Identity key plan: `(st_dev, st_ino)` from `os.stat` on the absolute path when the file exists and `st_ino != 0`; else the existing lexical key. Injectable stat for W-FS. |
| 7 text | `io/video/probe.py:114-120` `find_tool` (`:118-119`); `core/backend.py:941-943` `_probe_gpu` not-installed branch; `gui/settings_dialog.py:95` `AUTO_TEXT`, `:507`; capability tooltip at `:513-515` / `:565-587` | P16 P22 P63 | Pins kept: `tests/test_gui_open.py:265` needs the first sentence `"ffprobe was not found on the PATH."`, so only the second sentence changes. The status bar path `gui/shell.py:549,554` is untouched. |
| 8 preset rename | `config/presets.py:381-403` `rename` (`:402` `os.rename`) | P73 (P40 P49 noted) | D1 |
| 9 output name | `jobs/naming.py:291-317` `_base_plan` (`:304-311`) | P70 | Pins kept: "must be a single portable name component" (`tests/test_wp42a_runner_hardening.py:74,160`, `tests/test_wp42b_naming_guard.py:73`, `tests/test_wp42_runner_video.py:312,314`), so the character and stem are appended after it. |
| 10 wheel | `gui/preview.py:394-399` `wheelEvent` | P71 | No existing test sends a `QWheelEvent` (grep), so no pin moves |
| 11 tests | new `tests/test_portability.py`, `tests/test_macos_portability.py`; `tests/conftest.py:338-346` `pytest_collection_modifyitems` (footage skip; the `macos` policy joins it); `pyproject.toml:80-86` markers | section 8, all W/M refs | conftest plan: off darwin, every `macos` item that is not already skipped gets the same skip, as a belt-and-braces backstop to the explicit `skipif`. |
| 12 dependency | `pyproject.toml:30` `gpu` extra, `:46` dev group; `uv.lock` `clearwater` entry (`:83-85` optional gpu, `:96-97` dev edge, `:111` requires-dist, `:131` requires-dev) | AD-36, P22 | see 0.5 |
| 13 tools | `tools/environment_report.py:135-181` `collect` (`:171` GPU probe, `:172-174` OS fields); `tools/inventory.py:822-832` walk (`:825` exclude, D4(c)); T-row labels (D4(a)) | T01 T02 T14 T16 T06 T07 T10 T13 T33-T42 | D4(a), D4(c) |

The frozen docstring (P55) is at `interfaces/settings.py:34` and `:66-69` (the
`video_encoder` attribute entry spans four lines). No other interface module names NVENC
(grep of `interfaces/*.py`).

### 0.3 `mypy --platform darwin` at base (full `files` = `src/clearwater`, `tools`)

`uv run --no-sync mypy --platform darwin --cache-dir=<scratch>`: exit 1,
"Found 4 errors in 3 files (checked 161 source files)":

    src\clearwater\io\video\pipes.py:56: error: Module has no attribute "CREATE_NO_WINDOW"  [attr-defined]
    tools\prototype\bench.py:1159: error: Statement is unreachable  [unreachable]
    tools\prototype\bench.py:1480: error: Module has no attribute "getwindowsversion"  [attr-defined]
    tools\spike_io\transport.py:950: error: Statement is unreachable  [unreachable]

These are exactly the four named sites, with no other error. The default target
(`uv run --no-sync mypy`) reports "Success: no issues found in 161 source files", exit 0.

### 0.4 Roster and rate helper (items 1-2)

- **Where R is computed.** In `encode.py:256-300` `nvenc_rate`: H0 at `:284`, the source's
  Main-tier cap at `:285-288`, the 1 / 2 / 4 divisor at `:289`, the fitting levels at
  `:290-297`, the level choice at `:298`, and R = `min(maxrate, cap)` at `:299`. `:300` wraps
  R into `NvencRate(maxrate=R, bufsize=R, level=...)`.
- **The helper.** Lines `:282-299` move verbatim into a module-level internal
  `rate_ceiling(width, height, frame_rate, quality, source_level) -> RateCeiling`, a frozen
  dataclass holding `bits_per_second` and `level_idc`, with the same `ValueError`s.
  `nvenc_rate` becomes `NvencRate(maxrate=c.bits_per_second, bufsize=c.bits_per_second,
  level=f"{c.level_idc / 30:.1f}")`. Its signature, return value and NVENC callers
  (`:408`, `:707`) are unchanged.
- **The VT branch.** VT takes `rate_ceiling(...).bits_per_second` in `encode_command` and in
  `_prepare`, where it gets the same geometry refusal (P60). The rate state is stored in a
  private `self._vt_rate` (P61); `VideoSink.nvenc_rate` stays NVENC-only.
  `VT_RATE_CONTROL = "B"` gives `-b:v R -maxrate R`. `"A"` gives `-q:v <VT_Q_LEVEL[q]>
  -maxrate R`, with `VT_Q_LEVEL = {high: 65, standard: 55, draft: 45}` marked PLACEHOLDER,
  "WP6.5 measures".
- **The snapshot test's shape.** Two cases, `[hevc_nvenc]` and `[libx265]`. For each it
  checks the full `encode_command` argv and the two `trial_encode_command` argvs, as literal
  lists. The argvs come from synthetic `ProbeResult`s (a 4K HEVC Main-tier source and a
  1080p H.264 source) at 3 qualities x 2 depths. The literals are captured ONCE from the base
  tree (`git archive c1458747 src`, extracted to scratch, then a scratch script; the record
  goes in `cell\`), never regenerated by the test. No listing is involved, because the argv
  builders are pure.
- **Where the listings come in.** The roster's listing parse is tested separately in two
  ways. The SYNTHETIC VT fixture listing feeds stubbed `_run` for the darwin roster (fast).
  The laptop's real `ffmpeg -hide_banner -encoders` (FFmpeg 9.0.2 gyan.dev full build:
  `hevc_nvenc` and `libx265` listed, VT absent) feeds the `slow` real-trial case.
- **W-RATE.** It pins `rate_ceiling(...).bits_per_second == nvenc_rate(...).maxrate` over a
  grid, plus an independent recomputation: rounding, Fraction and VFR-average fps,
  Main / High / unknown source caps, all 3 divisors, the geometry refusal and the
  highest-level clamp.

### 0.5 VT listing fixture (Q2)

SYNTHETIC. There is no arm64 capture in the repository: every `videotoolbox` hit is prose in
the docs. The evidence tree holds only review diffs that quote those docs. The uv cache
holds Python distributions only, never FFmpeg text. The laptop's FFmpeg has no VT:
`ffmpeg -h encoder=hevc_videotoolbox` prints "Codec 'hevc_videotoolbox' is not recognized by
FFmpeg." and exits 0, so a help call cannot signal absence by its status. The fixture will be
a hand-written minimal `-encoders` line in the real 6-character flag format, plus a minimal
help text showing `-allow_sw`. Both are marked SYNTHETIC and replaced by WP6.5's capture. The
product parses only the encoder name line (the existing `_listed`) and never the help text;
the help fixture is used by tests only.

### 0.6 `uv lock` plan (seat clarification 4; runs in turn 2, group A)

- **Marker edit, two lines.** `pyproject.toml:30` becomes
  `gpu = ["cupy-cuda12x[ctk]>=14.2,<15; sys_platform != 'darwin'"]`. `:46` becomes
  `"cupy-cuda12x[ctk]>=14.2,<15; sys_platform != 'darwin'",`. The comment above `:46` gains
  "(not on macOS: CPU only, AD-36)".
- **Command.** First
  `uv lock --offline --project C:\Users\rwsmy\clearwater\.worktrees\wp6.4 > <evidence>\cell\uv-lock.log 2>&1`.
  If that fails for want of metadata, the same command without `--offline` (clarification 4).
  Then `uv lock --check --offline --project ...`, which must exit 0. uv 0.10.9; lock
  `version = 1`, `revision = 3`.
- **Proof that the eleven pack wheels are unchanged.**
  (1) A stdlib `tomllib` script compares `git show c1458747:uv.lock` with the new lock. The
  top-level keys must be equal, with no `resolution-markers` added. Every `[[package]]` other
  than `clearwater` must be identical in name, version, source, sdist, wheels, dependencies,
  optional-dependencies and metadata. The `clearwater` entry may differ only by
  `marker = "sys_platform != 'darwin'"` on the four cupy edges.
  (2) `tests/test_gpu_pack.py:252-279` `test_locked_distributions_equal_the_lock` passes. It
  compares the closure, versions and full wheel sets with `gpu_pack.LOCKED_DISTRIBUTIONS`.
  (3) `git diff --stat uv.lock` is recorded.
  All three go in `cell\uv-lock.record.txt`.
- **Can any version move?** It should not: `uv lock` prefers the locked versions, no
  requirement is widened, and the only thing excluded on darwin is CuPy's own closure (which
  cuda-pathfinder is reached only through). Any moved version, or a `resolution-markers`
  fork that re-pins a package, is a STOP to the seat. The lock is then restored with
  `git checkout -- uv.lock`, never fixed by hand.

### 0.7 Q1-Q4

- **Q1: agree, default `"B"`.** It is the control whose ceiling FFmpeg maps to
  DataRateLimits (audit section 4, DOC [FF]), so the D87 / DR-48 estimate keeps its
  NVENC-style bound. A's `q:v` values are labelled PLACEHOLDER in code and report.
- **Q2: SYNTHETIC (0.5).** The location is S1.
- **Q3: agree.** On darwin only, the CuPy-not-installed branch (`core/backend.py:941-943`)
  returns `"CPU: graphics-card processing is not available on macOS"`. `force_cpu` still
  returns `"CPU: forced"` (`:1028-1029`). win32 and else are unchanged, pinned by
  `tests/test_core_select.py`, `test_core_deps.py`, `test_core_wp34.py` and
  `test_gui_status.py`.
- **Q4: agree with a tools-side helper, but the parity reference is disputed (D3).**

### 0.8 Tests

- **W functions in `tests/test_portability.py`.** One per reference, each parameterised by
  `site`. Site lists are from the audit tables, 178 W references in all; W-STATIC is mypy, so
  169 pytest sites remain:
  - `test_portability_app_locations` W-PATH (8): P01 P25 P26 P56 X13 X14 X15 X16
  - `test_portability_spawn_policy` W-SPAWN (9): P02 P16 P24 P57 P58 P74 X26 X27 X28
  - `test_portability_default_pipe` W-PIPE (6): P03 P04 T07 T08 X23 X24
  - `test_portability_cpu_selection` W-DEVICE (10): P05 P18 P19 P20 P21 P22 P23 T42 T43 X44
  - `test_portability_tool_text_and_redaction` W-TEXT (8): P06 P08 P10 P66 P72 T25 X25 X45
  - `test_portability_encoder_roster_and_commands` W-CODEC (16): P07 P09 P11 P14 P37 P55 P62
    T33 T34 T35 T36 T37 T44 X41 X42 X43
  - `test_portability_encoder_rate_mapping` W-RATE (5): P12 P13 P59 P60 P61
  - `test_portability_container_contract` W-V4 (2): P15 P17
  - `test_portability_disk_space_estimate` W-SPACE (2): P64 P69
  - `test_portability_filesystem_semantics` W-FS (51): P28-P30 P39-P54 P67 P68 P70 P73
    T14-T24 T26-T32 T45-T48 T52 X19 X20 X22 X29 X46
  - `test_portability_footage_guard_and_test_helpers` W-GUARD (24): X01-X12 X17 X18 X21
    X30-X38
  - `test_portability_tool_reporting` W-TOOL (15): T01-T06 T09-T13 T38-T41
  - `test_portability_gui_contract` W-GUI (13, marked `gui`, D2): P22 P27 P31-P36 P38 P63
    P71 X39 X40

  Extras, all in the same module:
  - `test_portability_windows_encoder_command_snapshot[hevc_nvenc|libx265]` (2);
  - `test_portability_footage_guard_matches_the_reference_checks` (1, Q4 / D3);
  - `test_portability_output_name_refusal_names_the_character[:|\|/]` (3, item 9's "one
    test per character");
  - `test_portability_encoder_trials_on_this_laptop[P07|P09|P11]` (3, `slow` with its
    reason; a real one-frame NVENC / x265 trial through AD-23's helper with explicit
    `stdin=`; both availability outcomes accepted, reason pinned to availability; no `gpu`
    marker).
- **M functions in `tests/test_macos_portability.py`.** All marked `macos` and skipped by
  `skipif(sys.platform != "darwin", reason="macOS native leg (WP6.5)")`. 15 functions,
  178 sites:
  - `test_macos_static_target_policy` M-STATIC (9)
  - `test_macos_app_locations_and_isolation` M-PATH (8)
  - `test_macos_tool_and_worker_spawn` M-SPAWN (5)
  - `test_macos_default_pipe_fidelity` M-PIPE (6)
  - `test_macos_cpu_without_cuda` M-DEVICE (10)
  - `test_macos_ffmpeg_text_and_redaction` M-TEXT (8)
  - `test_macos_videotoolbox_capabilities` M-CODEC (12)
  - `test_macos_videotoolbox_quality_controls` M-RATE (5)
  - `test_macos_videotoolbox_v4` M-V4 (4)
  - `test_macos_videotoolbox_space_estimate` M-SPACE (2)
  - `test_macos_filesystem_semantics` M-FS (51)
  - `test_macos_footage_guard_and_helpers` M-GUARD (24)
  - `test_macos_tool_reporting` M-TOOL (15)
  - `test_macos_native_gui_contract` M-GUI (15, `macos` + `gui`)
  - `test_macos_bundle_smoke` M-BUNDLE (4, `macos` + `gui`; the bundle path comes from an
    environment variable, and the test skips with a reason when it is unset: WP6.5 builds
    the bundle)

  M-CODEC and M-V4 accept a proved "VT unavailable" result with the x265 fallback, as the
  brief says. M tests that call an entry point redirect HOME, APPDATA, LOCALAPPDATA and XDG
  (DR-124), block or stub the GUI except in M-GUI / M-BUNDLE, and have bounded timeouts.
- **Legs (seat clarification 5).** Parallel: the 12 unmarked W functions (156 sites) plus
  the snapshot (2), the guard parity test (1) and the per-character refusal (3), which is
  162 passed, plus 2 interface docstring tests, so 164 new passed. The parallel leg also
  collects 159 skipped M cases (`macos` alone). Serial: W-GUI (13) plus the slow trials (3),
  which is 16 new passed, and 19 skipped M cases (`macos` + `gui`: M-GUI 15 + M-BUNDLE 4).
  The two start-up tests are modified, not added. The test_config_paths change (S2) adds 0
  if it only narrows the parametrize; W-PATH[X13] carries the darwin case instead. Windows
  expectation: **358 new cases = 180 passed + 178 skipped** (parallel 164 passed +
  159 skipped, serial 16 passed + 19 skipped). The S2 edit removes one existing parallel
  case (`test_xdg_variables_win_elsewhere[darwin]`), so the net change against the base is
  +357 collected and +179 passed. The base figures are read at the gate's collect step.

### 0.9 Group split and yield point

Items 1-10 and 12 are group A, as filled. Items 5 (tools), 6 (`tools/footage_guard.py` and
the five sites), 11 and 13 are group B. **One change is proposed, with its reason.**
Group A's yield must show the snapshots green, and the build cycle writes the failing
check first. So group A also writes the tests that pin its own behaviour:
- the snapshot test;
- the W-PATH, W-SPAWN, W-PIPE, W-CODEC, W-RATE and W-V4 functions;
- the W-FS sites P29 P30 P70 P73;
- the W-GUI sites P22 P63 P71 P37;
- the per-character refusal;
- the DR-124 start-up edits;
- the interface docstring assertion;
- the S2 change.
Group B completes the rest of `tests/test_portability.py`, all of
`tests/test_macos_portability.py`, the conftest policy, the tools and the report. The
group-A yield's static step may still show exactly the three tool errors
(`bench.py:1159`, `:1480`; `transport.py:950`), as CHARC's FINAL note says.

### 0.10 Registration

The new files are:
- `tests/test_portability.py`
- `tests/test_macos_portability.py`
- `tests/ffmpeg_text/` (README plus two `.txt` files, if S1 is ruled as recommended)
- `tools/footage_guard.py`
- `docs/reports/wp6.4-macos-adaptation.md`
- `docs/proofs/wp6.4-ledger.md`

None needs `INSTANCE_SURFACE_RELPATHS` registration: `tests/`, `tools/`, `docs/reports/` and
`docs/proofs/` are all `INSTANCE_SURFACE_PREFIXES` (`tests/harness/genericity_lists.py:253-268`).

Depth at round-0 end: 247,937 (wp64-cell1, read by the dispatcher with cell_depth.py at its round-0 return)

## Group A

Build turn 2, cell `wp64-cell2` (fresh, implementer-opus-high), on `wp6.4` from `3a3ffbab`
(the base `c1458747` plus main `0de7d429`; `src`, `tools`, `tests`, `pyproject.toml` and
`uv.lock` are identical between the two). It follows dispatch-2 and CHARC's round-0 rulings.
Evidence: `clearwater-review-evidence\wp6.4\cell\` (`snapshot-base-c1458747.json`,
`snapshot-head-283b9d78.json`, `capture_snapshots.py`, `uv-lock.record.txt`, `uv-lock.log`,
`vt-argument-lists-group-a.txt`).

### A.1 Build cycles (failing check first, then the change)

| # | Commit | P rows | Change | Test (`tests/test_portability.py` unless named) | Red before the change |
|---|---|---|---|---|---|
| 0 | `62b45d70` | lock | none: snapshot literals captured from `git archive c1458747 src` into `work\wp6.4\base-c1458747` (`clearwater.__file__` printed from that tree) | `test_portability_windows_encoder_command_snapshot[hevc_nvenc, libx265]`: 24-case sha256 grid, 4 full literals, 4 trial commands | green on the unchanged code, as required |
| 1 | `07a4f0f4` | P55 | `interfaces/settings.py` docstrings only (`:34`, `:66-69`): "the platform's hardware HEVC encoder" | `tests/test_interfaces.py::test_settings_auto_encoder_docs_are_platform_neutral_and_the_fields_unchanged` (field names and defaults as read from base); W-CODEC[P55] | P55 failed on "NVENC" |
| 2 | `c0d2497e` | P07 P09 P10 P11 P12 P13 P14 P37 P59 P60 P61 P62 | `capability.py`: `encoder_roster` (darwin VT + x265; else NVENC + x265 as ruled), `KNOWN_ENCODERS`, `HARDWARE_ENCODERS`, VT trials with `-allow_sw 0`, `_VT_NO_SESSION_MARKERS` (NVENC markers still scoped to NVENC), `_detect(roster)`, `resolve_encoder(roster=)`, which keeps a known name (D26), `not_offered_reason`. `encode.py`: `rate_ceiling` / `RateCeiling` (`nvenc_rate` built on it), the VT branch behind `VT_RATE_CONTROL` (default `"B"`), `VT_Q_LEVEL` PLACEHOLDER 65/55/45, the geometry refusal for VT in `_prepare`, `_vt_ceiling`, `_check_options` (an unknown name is refused; a known name outside the roster is unavailable with its reason) | W-CODEC (11 sites), W-RATE (5), W-V4 (2) | 17 of 20 failed (import / attribute errors); P15 is a contract test and was green both ways |
| 3 | `494842c7` | P02 P03 P16 P65 P74 | `pipes.py`: AD-36 statement form, `start_new_session` (False on win32, True elsewhere) in the one dict, `_create_pipe` raise moved into `else`, fallback INFO off Windows. `probe.py:118-119`: the second sentence names FFmpeg and the user guide | W-SPAWN (9), W-PIPE (6); a guard-form checker over `src/` with planted expression and early-return controls | P02 named `pipes.py:56` and `:67`; P16 found "command prompt"; P74 / X26 had no `start_new_session`; P03 logged WARNING (30) on darwin |
| 4 | `723aa6dd` | P01 P25 P26 P56 X13-X16, DR-124 | `config/paths.py`: a darwin branch, `~/Library/Application Support/Clearwater` and `~/Library/Caches/Clearwater` from the injectable home, no XDG and no migration; one branch per platform. S2: `tests/test_config_paths.py:44` parametrize is `["linux"]`. DR-124: `tests/test_app_startup.py` sets HOME / USERPROFILE and expects only the platform's disposable folder; `tests/test_gui_startup.py` asserts every platform's resolution lands in the sentinel | W-PATH (8) | P01, X13, X15, X16 failed |
| 5 | `dd6b8a3f` | P22 P37 P63 | `settings_dialog.py`: `AUTO_TEXT` and `auto_tooltip` (the roster's hardware encoder, by family name, read from the capability report). `backend.py`: on darwin a missing CuPy gives `MACOS_CPU_REASON`; force CPU still gives "CPU: forced" | W-GUI P22 P37 P63 (`gui`) | all three failed |
| 6 | `4b7b634f` | P29 (P30 per D5) | `batch_panel._key`: `(st_dev, st_ino)` through the injectable `_stat`; the lexical key when stat fails or `st_ino == 0` | W-FS P29 (two spellings of one object = one key; two case-distinct objects = two keys; a blanket casefold fails the second control), P30 | P29 failed (`_stat` absent) |
| 7 | `dba46023` | P71 | `preview.wheelEvent`: one step per 120 accumulated units, reset on a direction change; `WHEEL_STEP_UNITS` | W-GUI P71: synthetic `QWheelEvent`s sent to the offscreen widget only (3 x 40 = one step; one notch; reversal; 240 = two steps) | failed (import) |
| 8 | `c404a20a` | P70 | `naming._base_plan`: the refusal keeps its pinned clause and names the character and the stem | W-FS P70; `test_portability_output_name_refusal_names_the_character[:, \, /]`, video and photo | 4 failed |
| 9 | `32bc1143` | P73 | `presets._rename_without_replace`: case-only uses `os.rename`; otherwise `os.link` then `os.unlink`; on `_LINKS_REFUSED` (EPERM, EXDEV, ENOTSUP, EOPNOTSUPP, EMLINK) `os.rename` with one WARNING naming the file; Windows `os.rename`. The platform is read through the new `config/paths.rename_replaces` (deviation 1) | W-FS P73: case-only, link, taken (FileExistsError), exFAT fallback, Windows; all stubbed | failed (`_LOG` absent) |
| 10 | `c50a6e73` | AD-36 deps | `pyproject.toml`: `; sys_platform != 'darwin'` on cupy in the `gpu` extra and the `dev` group, plus the `macos` marker; `uv lock --offline` | `test_gpu_pack.py::test_locked_distributions_equal_the_lock`; A.4 | n/a |
| 11 | `d2fdcb61` | P07 P09 P11 (native) | none in product. W-CODEC[P62] now stubs the sink's capabilities, so no unmarked test runs a real trial | `test_portability_encoder_trials_on_this_laptop[P07, P09, P11]` (`slow`) | n/a |
| 12 | `283b9d78` | docs | two docstrings: `FFmpegVideoSink.open` encoder argument; `BatchItem.key` | none (docstring only) | n/a |

Every commit was made by pathspec with `-c core.autocrlf=false`. A blob check over all 13
commits found 0 CR bytes (`tr -cd '\r' | wc -c`; `grep -c $'\r'` miscounts in this shell).

### A.2 The VT argument lists (encoder segment; from `snapshot_argv`, record `vt-argument-lists-group-a.txt`)

The encoder segment for every depth and quality, for both Q1 candidates. Everything outside it
is NVENC's argument list, byte for byte (W-V4[P15]). Each R below is `nvenc_rate`'s maxrate
for the same case (W-RATE[P13]).

- 4K60 HEVC source (level 5.1 Main, so R is capped at 40 Mb/s):
  - High: R = 40,000,000.
  - Standard: R = 20,000,000.
  - Draft: R = 10,000,000.
- 1080p29.97 H.264 source (no source cap):
  - High: R = 14,915,004.
  - Standard: R = 7,457,502.
  - Draft: R = 3,728,751.

Candidate B (the default):

    -c:v hevc_videotoolbox -allow_sw 0 -b:v R -maxrate R -pix_fmt yuv420p -profile:v main      (8-bit)
    -c:v hevc_videotoolbox -allow_sw 0 -b:v R -maxrate R -pix_fmt p010le -profile:v main10     (10-bit)

Candidate A (`VT_RATE_CONTROL = "A"`). The Q values are PLACEHOLDERS (High 65, Standard 55,
Draft 45):

    -c:v hevc_videotoolbox -allow_sw 0 -q:v Q -maxrate R -pix_fmt yuv420p -profile:v main      (8-bit)
    -c:v hevc_videotoolbox -allow_sw 0 -q:v Q -maxrate R -pix_fmt p010le -profile:v main10     (10-bit)

At 10-bit the `-vf` chain still ends `format=yuv420p10le,setparams=...` (AD-10 unchanged).
The trials are `-c:v hevc_videotoolbox -allow_sw 0 -pix_fmt yuv420p -profile:v main` (8-bit)
and `... -pix_fmt p010le -profile:v main10` (10-bit).

### A.3 Snapshot evidence

`capture_snapshots.py` was run on the base tree (`snapshot-base-c1458747.json`) and on the
head (`snapshot-head-283b9d78.json`). Comparing the two:
- grid: 24 cases, equal;
- full literals: 4, equal;
- trial commands: 4, equal.

The test holds the base literals and passed on the unchanged code before any edit. It passes
on every later commit.

### A.4 `uv lock` (record `uv-lock.record.txt`)

- Commands: `uv lock --offline` exited 0 (uv 0.10.9, 70 packages); no network was needed.
  `uv lock --check --offline` also exited 0.
- tomllib comparison against `c1458747:uv.lock`:
  - the top-level keys are equal (`version 1`, `revision 3`, no `resolution-markers`);
  - the same 70 package names;
  - no package other than `clearwater` changed, and no version moved.
- The diff is 4 lines, all in the `clearwater` entry: the darwin marker on the four cupy edges
  (dev-dependencies, optional-dependencies, requires-dev, requires-dist). requires-dist
  combines the markers as `sys_platform != 'darwin' and extra == 'gpu'`.
- `test_locked_distributions_equal_the_lock` passed, so the eleven pack wheels are unchanged.
- No STOP.

### A.5 Static and counts at `283b9d78` (all run from the worktree root)

- `ruff check .`: All checks passed.
- `ruff format --check .`: 324 files already formatted.
- `mypy`: Success, 161 files.
- `mypy --platform darwin`: exit 1, "Found 3 errors in 2 files". These are exactly group B's
  three sites, and `pipes.py:56` is clean:
  - `tools\prototype\bench.py:1159` [unreachable];
  - `tools\prototype\bench.py:1480` [attr-defined, getwindowsversion];
  - `tools\spike_io\transport.py:950` [unreachable].

Tests ran with `-p no:cacheprovider --timeout 600`, with basetemp under `work\wp6.4\`, and with
`QT_QPA_PLATFORM=offscreen` for the serial chunks:
- parallel expression, `-n 4`: 2019 passed, 0 failed, 0 skipped;
- serial expression: 300 + 33 = 333 passed, 0 skipped.

The suites are the dispatch's list plus the existing modules of every touched product file.

| Module | Parallel | Serial |
|---|---|---|
| test_portability | 50 | 7 (3 `slow`, 4 `gui`) |
| test_io_video_encode_units | 137 | - |
| test_io_video_encode | 115 | 20 |
| test_wp44_mov_input | 6 | 1 |
| test_io_video_spawn | 263 | - |
| test_io_video_decode_lifecycle | 32 | - |
| test_io_video_decode_rules | 19 | - |
| test_io_video_probe | 83 | - |
| test_gui_open | - | 31 |
| test_config_paths | 10 | - |
| test_config_isolation | 14 | - |
| test_config_presets | 121 | - |
| test_core_select / test_core_deps / test_core_wp34 | 17 / 4 / 29 | 1 / - / 1 |
| test_gui_status / settings_dialog / batch_panel / preview / preset_panel | - | 13 / 95 / 44 / 51 / 46 |
| test_jobs_naming | 877 | - |
| test_wp42a_runner_hardening / test_wp42b_naming_guard / test_wp42_runner_video | 55 / 3 / 14 | - |
| test_interfaces / test_interfaces_stubs | 48 / 22 | - |
| test_app_startup / test_gui_startup | - | 10 / 13 |
| test_gpu_pack | 100 | - |

`test_portability` has 57 cases at this point (group A), listed by function with the number of
sites each covers:
- snapshot 2;
- W-PATH 8;
- W-SPAWN 9;
- W-PIPE 6;
- W-CODEC 11 + 3 `slow`;
- W-RATE 5;
- W-V4 2;
- W-FS 4;
- refusal 3;
- W-GUI 4 `gui`.

A Popen-refusing pytest plugin ran the 50 unmarked cases; all 50 passed, so none of them spawns
a process.

### A.6 Verification loop (suspected / confirmed / rejected / fixed)

1. The parallel leg failed `test_config_isolation.py::test_only_paths_py_touches_the_environment_or_the_home_folder`
   with "presets.py:106 uses .platform". CONFIRMED by the run and FIXED in `32bc1143`: the
   platform is now read in `paths.rename_replaces` (deviation 1).
2. W-CODEC[P62] ran the real `detect_capabilities`, which spawns FFmpeg, in an unmarked test.
   CONFIRMED by reading the code and FIXED in `d2fdcb61`: the capabilities are stubbed, and
   the Popen-refusing plugin run proves it.
3. Two docstrings were stale (`open`'s encoder argument, `BatchItem.key`). CONFIRMED and FIXED
   in `283b9d78`.
4. ruff SIM300 / RUF059 / E501 / SIM114 in my own edits. FIXED before each commit.
5. Suspected: `jobs/export.py:879-883` (unowned) refuses a saved known encoder outside the
   roster with an empty reason, so the sink's `not_offered_reason` is not reached. CONFIRMED
   by reading the code. NOT FIXED: the file is outside the owned set (open item 3).
6. A full pass after fix 3 found nothing new: the static checks above, the snapshot comparison,
   and a re-read of every product diff.

### A.7 Deviations and open items for the seat / CHARC

1. **`config/paths.rename_replaces` (new public function).** The brief puts P73's platform
   branch in `presets.py`. The unowned `tests/test_config_isolation.py:51-65` forbids any
   `.platform` attribute in `clearwater.config` outside `paths.py`. The function keeps
   `paths.py` as config's one platform site, and the `app_locations` docstring now says so.
   No owned-file boundary is crossed. Alternative: grant the isolation test an exemption.
2. **D1 reading.** On Windows a preset rename stays `os.rename`. This is cell1's D1
   recommendation, which CHARC accepted; the ruling's "otherwise link then unlink" is read as
   POSIX only. On Windows nothing observable changes.
3. **The export's empty reason** (A.6 item 5). A Mac user whose saved encoder is `hevc_nvenc`
   gets the export's own "not available" message without the reason; the settings dialog does
   show `NOT_FOUND_REASON`. Suggested follow-up (unowned): pass `not_offered_reason` there.
4. **P71 changes Windows behaviour (the brief's pre-existing-defect rule; CHARC opens the DR).**
   A mouse notch (120) is unchanged. Sub-120 precision-touchpad deltas now accumulate: before,
   each event was a full step. A single event of 240 now takes two steps; before, it took one.
   Not checked on real hardware.
5. **New public names in owned modules (none in `interfaces/`):**
   - `capability`: `VIDEOTOOLBOX_ENCODER`, `KNOWN_ENCODERS`, `HARDWARE_ENCODERS`,
     `encoder_roster`, `not_offered_reason`; a keyword-only `roster=` on `resolve_encoder`;
   - `encode`: `RateCeiling`, `rate_ceiling`, `VT_RATE_CONTROL`, `VT_Q_LEVEL`;
   - `settings_dialog`: `auto_tooltip`, `ENCODER_FAMILIES`;
   - `backend`: `MACOS_CPU_REASON`;
   - `preview`: `WHEEL_STEP_UNITS`;
   - `pipes`: `start_new_session` added to the private TypedDict.
6. **W-CODEC T33-T37 are left to group B.** They pin group B's tool-docstring labels.
   W-PIPE[T07/T08] reads `tools/spike_io/transport.py:376-395` through the AST, without
   running it.
7. **The `macos` marker is registered** (`pyproject.toml`, owned). Its conftest skip policy
   and the M tests are group B's.
8. **Process slips.**
   - One bare `cd` inside a command (the snapshot-assembly call, into the worktree). The
     session cwd read `/c/Users/rwsmy/clearwater` right after; later directory changes were
     subshells only.
   - `tests/test_app_startup.py`'s test runs the real entry point under offscreen QPA. That is
     the test's purpose, and it was not changed. Its app data AND now its home are redirected
     under `tmp_path`, with a 180 s timeout. It was run as the dispatch lists it.

### A.8 Rows built only in part without a Mac (for the next DR)

- P09 / P10 / P14 / P12 / P59: the VT trials, reasons and commands are built and pinned by
  argument list only. No VideoToolbox encode has run. The VT stderr markers and both listing
  texts are SYNTHETIC (`tests/ffmpeg_text/README.md`); WP6.5 replaces them with a capture.
- P01 / P25 / P26: the Library paths are injected on Windows; no native macOS home has been
  resolved yet (M-PATH).
- P03 / P74: INFO logging and `start_new_session=True` are constructed and stubbed. No child
  has run in its own session (M-SPAWN, `os.killpg`).
- P22: the darwin AD-9 text is reached with a patched platform only (M-DEVICE / M-GUI).
- P29: the identity key is checked against a fake stat provider and real NTFS. APFS in
  case-sensitive and case-insensitive modes is M-FS.
- P73: the link, unlink and fallback branches are stubbed. The APFS folding corpus and exFAT
  are M-FS.
- P71: synthetic offscreen events only; real trackpad momentum is M-GUI.

Depth at group-A yield: 392,066 (wp64-cell2, read by the dispatcher with cell_depth.py at its group-A return; retired, group B to a fresh wp64-cell3)

## Group B

Build turn 3, cell `wp64-cell3` (fresh, implementer-opus-high), on `wp6.4` from `27505be4`, following
dispatch-3. No group-A product file was edited. Evidence `clearwater-review-evidence\wp6.4\cell\`:
`row-disposition-group-b.txt` (the 172-row table, generated from the audit's tables) and
`mypy-darwin-group-b.txt`. Every commit was made by pathspec with `-c core.autocrlf=false`; a blob check
over all six found 0 CR bytes.

### B.1 Commits

| Commit | Rows | Change |
|---|---|---|
| `bbf777bc` | T03 T04 T05 T09 T49-T51 | `bench._windows_power`, `_cpu_brand`, `_platform_name` (`:1467` with its stale comment, D4 (d)) and `transport.idle_gate` in the statement form |
| `facf31a5` | T14 T16 T17 T26-T29 T52 X46 | NEW `tools/footage_guard.py`, used at the five sites; inventory AppleDouble and casefold; `export_oracle.record_name`; the one-edit `test_export_oracle.py` |
| `11525691` | T13 T33-T39 T42 | the D4 (a) labels on eight modules; docstrings only, with the AST asserted equal |
| `9a983ac4` | T01 T02 | `environment_report`: darwin NVIDIA fields null and not run; opt-in `--platform-facts` (S-B1) |
| `43b7a263` | W rows | the remaining W cases (179 in the module); the D3 parity test |
| `705bf3a4` | M rows | NEW `tests/test_macos_portability.py` (178 cases); the conftest `macos` policy; one escaped literal |

### B.2 Static at `705bf3a4`

- `ruff check .`: All checks passed.
- `ruff format --check .`: 326 files already formatted.
- `mypy`: Success, 162 files.
- `mypy --platform darwin`: "Success: no issues found in 162 source files", 0 errors. Group A's three
  tool sites are gone.

### B.3 Counts

| Module | Parallel leg: collected / passed / skipped | Serial leg: collected / passed / skipped |
|---|---|---|
| `test_portability` (179) | 162 / 162 / 0 | 17 / 17 / 0 (14 `gui`, 3 `slow`) |
| `test_macos_portability` (178) | 159 / 0 / 159 | 19 / 0 / 19 (M-GUI 15 + M-BUNDLE 4, `macos` + `gui`) |

Neither module collects anything in the fullclip leg. The skip reason is "macOS native leg (WP6.5)".

Runs (`-p no:cacheprovider --timeout 600`; basetemp `work\wp6.4\tB-par` and `tB-ser`; offscreen for
the serial leg) covered both new modules and every touched tool's test module, plus
`test_export_oracle`, `test_fixtures`, `test_inventory`, `test_config_presets` and
`test_core_backend`. The module list is in `work\wp6.4\tB-mods.txt`.
- parallel expression, `-n 4`: 1834 passed, 159 skipped;
- serial expression: 104 passed, 19 skipped.

Against round 0's projection of 358 new cases, there are 357: 179 W + 178 M. The 2 interface docstring
cases are group A's, in `test_interfaces`. W-GUI has 14 cases, not 13, because group A also put P37 there.

### B.4 Verification loop (suspected / confirmed / rejected / fixed)

1. `footage_guard` bound `os.path.realpath` at import, so the existing alias tests' monkeypatch would
   not have reached it (`test_export_oracle.py:296`, `test_analysis_breakdown.py:347`). CONFIRMED by
   reading the code. FIXED before the first run: the seams now look the function up at call time.
2. `environment_report.main` called `collect(platform_facts=...)`, and
   `test_same_second_reports_never_overwrite` stubs `collect()` with no arguments. CONFIRMED by the
   run. FIXED: without the flag, `main` calls `collect()`.
3. The W-GUI cases ran on the real `windows` QPA when `QT_QPA_PLATFORM` was unset, because the module
   imported `gui_support` lazily. X39 caught it. CONFIRMED and FIXED: the module now imports
   `gui_support` at import. A rerun with the variable unset passes 14/14 offscreen. Slip: that one
   earlier run showed the test windows on the desktop briefly; no input was sent.
4. W-GUARD markers for X17, X32 and X37 named constructs that are not in those files, and the checker
   missed a guard made by a skip helper. CONFIRMED by the run. FIXED: the markers now match, and the
   checker counts a call to a helper that skips off Windows. The planted unguarded control still fails
   by name.
5. Non-ASCII literals appeared in two string literals in the test files. CONFIRMED and FIXED: they are
   now `\u` escapes.
6. `test_prototype_clip.py::test_open_source_refuses_non_square_pixels` fails when run alone, both here
   and on main at HEAD (the `clips` folder is created by another test). REJECTED as not caused by this
   package: the module and the tool are untouched, and it passes in module order.
7. Under `-n 4`, `test_analysis_breakdown::...replica_differs` (MemoryError) and the container spike's
   x265 proof failed once. Both pass serially. REJECTED as host load (a shared laptop).
8. A full pass after these fixes found nothing new: the static checks, both legs, and a re-read of the
   tool diffs.

### B.5 STOPs, deviations and open items

- **S-B1 (STOP, reproduced): the item-13 environment facts cannot be in the default report without an
  unowned test edit.** `tests/test_environment_report.py:13-33` pins the exact key list and order. Any
  new default key fails `test_report_has_every_key`. Built as opt-in `--platform-facts`, so the default
  output is unchanged and the 19 existing tests pass. **Recommended:** grant a one-edit change to
  `EXPECTED_KEY_ORDER` and make the facts default, or keep the flag.
- **S-B2 (STOP): the completion report could not be written by this cell.** The cell's file tool
  refuses to write a report `.md` from a subagent. The report's full text goes to the dispatcher in the
  return message, and the dispatcher writes `docs/reports/wp6.4-macos-adaptation.md`.
- **D-B1: the AppleDouble line needs `inventory.py` lines outside `:822-832`.** These are the new
  `ScanResult.appledouble` field (default 0), the `_summary_text` / `write_inventory` parameter
  (default 0), `main` passing the count, and the module and `--exclude` help text. All are in the owned
  file; the line range was the brief's pointer.
- **D-B2: T06 and T10 carry no label.** `bench.py` and `transport.py` were granted at the mypy lines
  only, so W-TOOL pins their Windows process names and the report lists the label as deferred.
- **Deferred to candidate DR 3: T11 and T12** (`spike_io/licences.py` is not owned). M-TOOL marks them
  `xfail` until the Mach-O forms land.
- **Process:**
  - No bare `cd` ran. One chained command held `&& cd` but stopped before it; `pwd` confirmed the
    session cwd.
  - Every new commit is LF.

### B.6 Addendum: CHARC's group-A yield rulings (`63ff45f3`), relayed mid-turn

- **The export grant.** `jobs/export.py`, in the video job's encoder check (by name: the
  `capability is None or not capability.available` branch after `resolve_encoder`). When the
  capability is None, the failure now ends ": not offered on this platform". When a reason exists,
  it is unchanged. Commit `1a003fe4`. The one test is
  `test_portability_export_names_an_encoder_outside_the_roster`. It drives the
  `test_jobs_export_support.Rig` with `hevc_videotoolbox`, which is absent from the rig's report on
  every platform, and failed red before the edit. Its control is `hevc_nvenc`, listed as
  unavailable, which keeps its reason. This closes open item 3 of A.7.
  Runs after the edit:
  - `test_portability`, `test_jobs_export`, `test_jobs_export_video`, `test_jobs_export_process`
    and `test_wp42_runner_video`, parallel expression: 372 passed;
  - the serial expression over the export modules plus `test_gui_export_panel`: 46 passed;
  - static: ruff, format and both mypy targets clean.
- **Counts, updated.** `test_portability` has 180 cases: parallel 163 / 163, serial 17 / 17.
  `test_macos_portability` is unchanged.
- **P71.** It is the fix of a pre-existing Windows defect: the old `wheelEvent` zoomed a full step on
  any non-zero delta, so a precision touchpad over-zoomed.
- **Partial rows, for ONE register row at the accept.** Each row is listed with its Windows proof and
  the WP6.5 native check that closes it:

| Row(s) | Windows proof (W) | WP6.5 native check (M) that closes it |
|---|---|---|
| P09 P10 P12 P14 P59 | the VT argument lists, reasons and branch, from snapshot / argv and the SYNTHETIC `tests/ffmpeg_text/` listings (W-CODEC, W-RATE, W-TEXT) | M-CODEC[P09, P14]: real VT 8 / 10-bit trials and a sink encode. M-RATE: both Q1 candidates under R. M-TEXT[P08, P10]: the real listing and reasons. Plus replacing the synthetic listings with a capture |
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
| M-DEVICE AD-11 | none on Windows | the Mac CPU output against the Windows references within AD-11's tolerances; not yet written, WP6.5 |

Depth at group-B yield: 416,156 (wp64-cell3, read by the dispatcher with cell_depth.py after its final return incl. the export grant; PAST its cap, retired; the A r1 fold-in goes to a fresh cell)

## Group B fold-in (turn 4)

Cell `wp64-cell4` (implementer-opus-high, FRESH), dispatch-4, base `107e6c77`. Four items: S-B1,
S-B2, the A r1 P30 advisory, this section. Evidence scripts and logs: `work\wp6.4\` in the
worktree (`p30_mutant.py`, `sb1_spy.py`, `mtool_leak.py`, `t4-*.log`).

### T4.1 Commits

| Commit | What |
|---|---|
| `b0c0d5fd` | test: W-FS[P30] gains the `Stra\u00dfe.MP4` (folder `a`) / `STRASSE.mp4` (folder `b`) pair, asserting the bare labels |
| `b08e9f43` | test: the same pair in ASCII source (`\u00df` escape); the file tool had written the literal character |
| `3ec3f7cf` | docs: NEW `docs/reports/wp6.4-macos-adaptation.md`; this section (first return) |
| `a6294d43` | feat: S-B1 on by default, the flag removed; the two `test_environment_report` edits; the W-TOOL / M-TOOL callers; the M-TOOL context fix (T4.8) |
| (this commit) | docs: the report and this section after the ruling (T4.8) |

All by pathspec with `-c core.autocrlf=false`, the Co-Authored-By line, blob check 0 CR.

### T4.2 Item 3: W-FS[P30] (A r1 ADVISORY) -- DONE

- The mutant, in memory (`work\wp6.4\p30_mutant.py`, a pytest plugin replacing
  `batch_panel.item_labels` with a copy that compares `item.path.name.casefold()` instead of
  `os.path.normcase(item.path.name)`; no committed edit):
  - `mutant`: `1 failed`, at `assert batch_panel.item_labels(unicode_pair) == ["Stra\u00dfe.MP4",
    "STRASSE.mp4"]` (the mutant added `(...\a)` / `(...\b)`); exit 1.
  - `clean`: `1 passed`; exit 0.
  - Both re-run at `b08e9f43` with the same result.
- The case count is unchanged (180): the pair is inside the existing `_fs_p30`.

### T4.3 Item 1: S-B1 (GRANTED) -- STOPPED at the first return, no edit made; built after the ruling (T4.8)

- **The conflict.** The grant allows ONE edit to `tests/test_environment_report.py` (the key
  order at `:13-33`), and the dispatch requires that every test calling `collect()` / `main()`
  stubs the trial seam. The module's tests call `main()` and stub only `subprocess.run` and
  `cpuinfo`. With the facts on by default they would reach `_correction_backend` (the product's
  `select_backend`: a real CuPy import, CUDA device count and test kernel) and `_encoder_rows`
  (the product's `detect_capabilities`: the real `find_tool("ffmpeg")` and its trials). The stub
  they need (an autouse fixture beside `stub_cpuinfo`) is a second edit to that file.
- **Reproduction (cheap, no trial, no CuPy):** `work\wp6.4\sb1_spy.py` sets `collect`'s keyword
  default to `platform_facts=True` in memory, simulates the granted key order, and replaces the
  two seams with RECORDERS returning stub values. Result: `19 passed`; `SPY: 16 tests reached the
  trial seam (unstubbed in the module)` -- every test except `test_missing_config_without_out_fails`,
  `test_run_decodes_undecodable_output_with_replacement` and
  `test_same_second_reports_never_overwrite`.
- **Found while there (M-TOOL, MAJOR for WP6.5, test-only):** `test_macos_tool_reporting` runs the
  W case `_w().TOOL_CASES[site](monkeypatch, tmp_path)` and then `_tool_native` on the SAME
  monkeypatch, so the native half reads the W stubs. `work\wp6.4\mtool_leak.py` replays it with
  stubs only: T01's native `collect` sees encoders `['libx265']` (it asserts `[VT, X265]`); after
  T02's W case `sys.platform` is `win32` and the gpu reason is `nvidia-smi not found` (it asserts
  "not applicable on this platform"). So M-TOOL[T01] and [T02] fail on a Mac as written. The fix
  (the W case under its own `pytest.MonkeyPatch.context()`) makes the native T01 half run real
  VT / x265 trials, which the dispatch's rule asks to be `slow` / `gpu`-marked "for that reason":
  that marker choice moves cases between gate legs, so it waits for the ruling too.
- **Recommended:** grant a second edit to `tests/test_environment_report.py`: an autouse fixture
  stubbing `environment_report._correction_backend` and `environment_report._encoder_rows` (as
  `_tool_report` in `test_portability.py` does); then the tool change, the key order, the two
  W-TOOL callers and the M-TOOL context fix as dispatched, with M-TOOL's native T01 / T02 left on
  the `macos` marker only (they exist to run natively; they are skipped off darwin).
- **The callers at this head** (`grep` of `environment_report.collect(` / `.main(` in `tests` and
  `tools`; no other module imports `environment_report`): `test_environment_report.py:76, 182,
  189, 199, 216, 230` (`main`); `test_portability.py:3327, 3329, 3345, 3351` (`collect`, all under
  `_tool_report`'s stubs); `test_macos_portability.py:1032` (`collect(platform_facts=True)`,
  `macos`, skipped here).

### T4.4 Item 2: S-B2 (ACCEPTED) -- DONE

- `docs/reports/wp6.4-macos-adaptation.md` written with the Write tool; the tool did NOT refuse
  this time. Content: return-3 section 7, plus the export grant (section 1), P71's line (sections
  1 and 10), ledger B.6's partial-row table (section 10), the turn-4 changes, and the counts
  re-taken at `b08e9f43`. S-B1 is described as granted and NOT built at this head.
- **File-tool note:** the Write / Edit tools decoded a typed `\u00df` escape into the literal
  character (in the test source and in the report). Both were turned back into the ASCII escape by
  a byte-level replace; the report and the test file are now pure ASCII. The 172-row table was
  checked line by line against return-3 section 7: identical except the P30 and T01 cells, which
  were changed on purpose.
- 0 CR in the file.

### T4.5 Static and counts at `b08e9f43` (run from the worktree root)

    uv run --no-sync ruff check .                  All checks passed!
    uv run --no-sync ruff format --check .         326 files already formatted
    uv run --no-sync mypy                          Success: no issues found in 162 source files
    uv run --no-sync mypy --platform darwin        Success: no issues found in 162 source files

(mypy at `b0c0d5fd`; `b08e9f43` changes one test file's escapes only, outside mypy's `files`.)

Tests (`-p no:cacheprovider --timeout 600`, `QT_QPA_PLATFORM=offscreen`, `PYTEST_ADDOPTS` unset,
basetemp `work\wp6.4\t4-*`):

| Module | Parallel leg, `-n 4` (collected / passed / skipped) | Serial leg (collected / passed / skipped) | Fullclip |
|---|---|---|---|
| `test_environment_report` | 19 / 19 / 0 | 0 | 0 |
| `test_portability` | 163 / 163 / 0 | 17 / 17 / 0 | 0 |
| `test_macos_portability` | 159 / 0 / 159 | 19 / 0 / 19 | 0 |
| the three together | 341 / 182 / 159 | 36 / 17 / 19 | 0 |

Every skip reads "macOS native leg (WP6.5)".

### T4.6 Verification loop (suspected / confirmed / rejected / fixed)

- Suspected: W-FS[P30] lets a casefold label mutant through (A r1). Confirmed by the in-memory
  mutant after the fix (fails); fixed by the pair.
- Suspected: the default-on facts would reach the real trial seam in `test_environment_report`.
  Confirmed (16 / 19 by the spy). Not fixed: STOP (T4.3).
- Suspected: M-TOOL's native half reads the W stubs. Confirmed (replay). Not fixed: held with
  S-B1 (T4.3).
- Suspected: the file tool wrote non-ASCII into the test source. Confirmed (`grep`); fixed
  (`b08e9f43`).
- Suspected: the report's row table drifted from return-3 while being retyped. Rejected: the
  line-by-line comparison shows only the two intended cells.
- A second pass over the three edited files found nothing new.

### T4.7 Discipline record

- **`wp64-cell3` returned at 416,156, PAST the cap; recorded here as a discipline breach** (CHARC,
  brief tail: "the rule is STOP near 400K, a return is not a licence to run on"); the successor's
  dispatches to a cell name its mid-build yield points (the 2026-10-29 rule).
- This cell: no bare `cd` (subshells only), no stash, no mailbox post, no edit outside the owned
  files, no real FFmpeg / `nvidia-smi` / CuPy run from a test or probe, every test run offscreen.

Depth at the first turn-4 return (the S-B1 STOP): 148,769 (the dispatcher's figure at the ruling relay)

### T4.8 After the turn-4 STOP ruling (CHARC `a5ca96e5`, relayed by the dispatcher)

The ruling: (1) a second `tests/test_environment_report.py` edit GRANTED, ONE autouse fixture
stubbing `_correction_backend` and `_encoder_rows` (that module's grant is exactly two edits),
then S-B1 as ruled; (2) the M-TOOL leak fixed in scope, the W case in its own
`pytest.MonkeyPatch.context()`, native T01 / T02 on `macos` ONLY (no `slow`; the "no real trial
unless slow / gpu" rule binds the Windows legs), no case moving between legs.

- **Built (`a6294d43`):**
  - `tools/environment_report.py`: the facts ON BY DEFAULT; `--platform-facts` and the
    `platform_facts` parameter removed; the module and `collect` docstrings and the
    `_PLATFORM_KEYS` note say the report runs the product's encoder trials.
  - `tests/test_environment_report.py`, the two edits only: `machine`, `process_architecture`,
    `correction_backend`, `correction_backend_reason`, `encoders` appended to `EXPECTED_KEY_ORDER`
    before `unavailable`; the autouse fixture `stub_trial_seam`. (The working copy had CRLF from
    the checkout; it was normalised to LF before the commit; blob 0 CR.)
  - `tests/test_portability.py` W-TOOL T01: the facts read from the default `collect()`; the
    `plain` / `platform_facts=True` pair is gone (the tail assertion `keys[-6:] ==
    [*_PLATFORM_KEYS, "unavailable"]` stays).
  - `tests/test_macos_portability.py` M-TOOL: `collect()`; the W case under
    `with pytest.MonkeyPatch.context() as w_patch`.
- **No real trial on the Windows legs:** `work\wp6.4\sb1_check.py` installs RECORDERS (stub
  values) over the real seams at session start; a test's own stub replaces them. Over the three
  modules: parallel expression `182 passed, 159 skipped`, `CHECK: 0 unstubbed seam calls`; serial
  expression `17 passed, 19 skipped`, `CHECK: 0 unstubbed seam calls`. (The first return's spy saw
  16 of 19 reach it before the fixture.)
- **M-TOOL fix shown:** `work\wp6.4\mtool_fixed.py` replays the fixed sequence (stubs only):
  `T01: stubbed inside=True, originals restored after=True`; the same for T02.
- **The callers** (`grep` of `environment_report.collect(` / `.main(` / `platform_facts` in `tests`
  and `tools`; no other module imports `environment_report`): `test_environment_report.py:88, 194,
  201, 211, 228, 242` (`main`, all under `stub_trial_seam`; `:201` fails on the config before
  `collect`); `test_portability.py:3327, 3343, 3349` (`collect()`, under `_tool_report`'s stubs);
  `test_macos_portability.py:1032` (`collect()`, the native half, `macos` only, skipped here). No
  `platform_facts` remains.
- **Report:** `docs/reports/wp6.4-macos-adaptation.md` updated (S-B1 default in sections 1 and 2,
  the M-TOOL fix and the default trials in section 10, counts and mypy at `a6294d43`).

Static at `a6294d43`:

    uv run --no-sync ruff check .                  All checks passed!
    uv run --no-sync ruff format --check .         326 files already formatted
    uv run --no-sync mypy                          Success: no issues found in 162 source files
    uv run --no-sync mypy --platform darwin        Success: no issues found in 162 source files

Counts at `a6294d43` (same options as T4.5):

| Module | Parallel leg, `-n 4` (collected / passed / skipped) | Serial leg (collected / passed / skipped) | Fullclip |
|---|---|---|---|
| `test_environment_report` | 19 / 19 / 0 | 0 | 0 |
| `test_portability` | 163 / 163 / 0 | 17 / 17 / 0 | 0 |
| `test_macos_portability` | 159 / 0 / 159 | 19 / 0 / 19 | 0 |
| the three together | 341 / 182 / 159 | 36 / 17 / 19 | 0 |

Every skip reads "macOS native leg (WP6.5)". No case moved between legs.

Verification loop, second pass: suspected that a W-TOOL or M-TOOL caller still passed
`platform_facts` (rejected: grep, none); that the fixture missed a `main()` caller (rejected: the
recorder saw 0); that the M-TOOL context leaves a stub live (rejected: the replay); that the test
file would commit CR (confirmed in the working copy; fixed before the commit). Nothing new.

Depth at turn-4 yield: 175,078 (cell_depth.py --live, read at the seat 2026-11-04 ~23:08Z after the final return; 69 turns); cell4 retired, the A r2 fold-in goes to a fresh cell.
