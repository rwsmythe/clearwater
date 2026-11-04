# WP6.4 macOS adaptation -- cell ledger (`wp64-cell1`, implementer-opus-high)

Brief `docs/briefs/wp6.4-brief.md` (FINAL at `c1458747`); dispatch
`clearwater-review-evidence\wp6.4\cell\dispatch-1.md`. The cell keeps this file; the
dispatcher fills the depth figures.

## Cumulative round ledger

| Round | Reviewer | Blocking (crit/major) | Minor/nit | In-envelope / out | NEW / REOPENED | Reverts | Fixes: product / tests-only | Transport, CLI | Depth (dispatcher) |
|---|---|---|---|---|---|---|---|---|---|
| 0 | none (read-only work list) | - | - | - | - | 0 | none (no edit) | - | DISPATCHER TO FILL |

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

Depth at round-0 end: DISPATCHER TO FILL
