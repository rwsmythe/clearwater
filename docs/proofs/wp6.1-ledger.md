# WP6.1 packaging spike -- cell ledger

Cell: implementer-opus-high (Claude). Brief `docs/briefs/wp6.1-brief.md` (FINAL at `223b33f4`);
dispatch `clearwater-review-evidence/wp6.1/cell/dispatch-1.md`. Worktree `.worktrees/wp6.1`,
branch `wp6.1`, base `c051306f`. Builds, packs and timings go under the worktree's
`work/wp6.1/`. Round-0 evidence: `clearwater-review-evidence/wp6.1/cell/r0-*.txt`.

## Round 0 (2026-11-04 ~08:40Z, read-only)

Environment used for every read: the worktree has NO `.venv`. The first
`uv run --no-sync` in the worktree created an EMPTY `.venv` (no packages; gitignored), which I
deleted at once. Every later read used the main tree's `.venv` interpreter with
`PYTHONPATH=<worktree>/src`, after `git diff c051306f 5671a927 -- uv.lock pyproject.toml src`
came back empty (same lock, same source). No throwaway PyInstaller venv was made: the PyPI
JSON API and PyInstaller's online documentation were enough for round 0. The hook sources
are read from the installed 6.22.3 in turn 2.

### 1. The entry and the spawn as they stand

- `src/clearwater/__main__.py:5` imports `clearwater.app.main.main` at module top, and
  `:7-8` runs it. `clearwater.app.main` imports PySide6 at `:32-33`. Measured: importing
  `clearwater.app.main` loads `PySide6` and `shiboken6`.
- `src/clearwater/app/composition.py:461` builds the worker command:
  `worker = [sys.executable, "-m", "clearwater.app.export_worker"] if command is None else command`.
  This is the ONLY `sys.executable` site in `src/` (grep). No `multiprocessing` and no
  `ProcessPoolExecutor` exist anywhere in `src/`, so `freeze_support()` does not apply
  (Q5's premise holds).
- `jobs/export_process.py:224` is the `ProcessExportJobs` docstring that names the command.
  `:292-298` is `subprocess.Popen(list(self._command), stdin=PIPE, stdout=PIPE, stderr=PIPE,
  **tool_spawn_kwargs())`. `tool_spawn_kwargs` (`io/video/pipes.py:45-60`) passes
  CREATE_NO_WINDOW and a copy of the parent environment without FFREPORT.
- Only VIDEO jobs go to the worker. Photo requests run in the GUI process
  (`app/main.py:281-284`: `process_export_jobs(photo_exports=composition.export_jobs(cache=cache), ...)`).
- `app/export_worker.py`:
  - Imports: stdlib, `clearwater.app.composition`, `clearwater.interfaces`,
    `clearwater.jobs.export_seam` (`:29-43`).
  - Measured: importing `clearwater.app.export_worker` loads NEITHER PySide6/shiboken6 NOR any
    `cupy`/`cupyx`/`cuda`/`nvidia` module. Only PIL, pillow_heif and tifffile are loaded among
    the native-library packages checked. AD-31 holds.
  - `main(argv=None)` (`:299-319`) REJECTS any argument (`:308-311`: `"export worker: takes
    no arguments"`, exit 2), then takes over fd 1 for the protocol.
  - The worker accepts `kind` `"photo"` as well as `"video"` (`decode_request`, `:129-133`).
- The first `cupy` import: `core/backend.py:936` `importlib.import_module("cupy")` inside
  `_probe_gpu` (`:932-933`, `functools.cache`, once per process). It is reached from
  `select_backend` (`:1001`, `:1030`) and the GUI's start-up device probe
  (`app/main.py:206-218`, `app/startup.py:355`). `CupyBackend.__init__` imports it again at
  `:575` (cached). No module-level `cupy` import exists anywhere in `src/`.
- **Q5 confirmed, with three details for turn 3:**
  - (a) `__main__.py` top level must import only stdlib and `clearwater.gpu_pack`. The
    `clearwater.app.main` import moves INTO the GUI branch.
  - (b) The worker branch must call `export_worker.main(sys.argv[2:])`, the remaining
    arguments. Passing nothing (`argv=None`) would make it read `sys.argv[1:]` =
    `["--export-worker"]` and exit 2.
  - (c) One-file forms: PyInstaller 6.9 and later treats a process spawned through
    `sys.executable` of a one-file parent as a worker that REUSES the parent's unpacked
    `_MEIxxxx` (PyInstaller docs, "Common Issues and Pitfalls", the
    `PYINSTALLER_RESET_ENVIRONMENT` section). So a video job does not re-extract the bundle,
    provided `PYINSTALLER_RESET_ENVIRONMENT` is NOT set for the worker (it is not today).
    Turn 2 verifies this by listing `%TEMP%\_MEI*` during an export.
- **Windowed stdio for the worker** (a frozen GUI build is a windowed-subsystem executable).
  Evidence: `r0-windowed-stdio.txt`, with `pythonw.exe` standing in for the windowed
  bootloader.
  - Started with three PIPEs and CREATE_NO_WINDOW (exactly what `export_process.py:292`
    does): `sys.stdin`, `sys.stdout` and `sys.stderr` are all set, and the worker's
    dup / dup2 protocol trick delivers `proto-ok` on stdout and `err-ok` on stderr.
  - Started without pipes: all three are None.
  - So the worker's stdout takeover is expected to work frozen. Turn 2 confirms it on the
    real build.
- **The ONE loader call site: `src/clearwater/__main__.py`, its first statement after the
  stdlib imports, before either branch.**

### 2. Test modules exercising the worker command and the start-up path

The SERIAL leg runs these:

| Module | Marker | Tests | Why |
|---|---|---|---|
| `tests/test_app_export_worker.py` | `slow` (module) | 7 | pins the default `-m` command (`:37`, `:266-283`); spawns the real worker |
| `tests/test_app_startup.py` | `gui` (module) | 10 | `:171` runs `runpy.run_module("clearwater", run_name="__main__")`, the entry itself, with `LOCALAPPDATA` / `APPDATA` / XDG under `tmp_path` (`:180-186`) |
| `tests/test_gui_startup.py` | `gui` (module) | 13 | the shell's start-up (`configure_logging`, settings) |
| `tests/test_core_backend.py` | 4 `gpu`, 28 unmarked | 32 | the backend probe the loader precedes |
| `tests/test_app_wiring.py` | `gui` (module) | 21 | `:752-756` builds the process export engine |

`tests/test_app_v7.py` (gui + slow, 6) also builds `ProcessExportJobs`, but it INJECTS its own
hold-worker command (`:298-310`), so the Q5 expression does not reach it. It is optional and
timing-sensitive.

The PARALLEL leg runs these:

| Module | Tests | Why |
|---|---|---|
| `tests/test_jobs_export_process.py` | 49 | runs the command it is given |
| `tests/test_app_composition.py` | 16 | the composition root |
| `tests/test_wp42_composition.py` | 10 | the composition root |
| `tests/test_core_backend.py` | 28 | its unmarked part |
| `tests/test_gpu_pack.py` | new | the loader |
| the Q5 tests | new | see item 6 / D5 |

### 3. The pack list

All eleven are confirmed against `importlib.metadata` (the main tree's `.venv`, the same lock):

| Distribution | Version | Its non-extra requirements |
|---|---|---|
| `cupy-cuda12x` | 14.2.0 | `numpy<2.6,>=2.0`, `cuda-pathfinder==1.*,>=1.3.4` |
| `cuda-pathfinder` | 1.8.3 | none |
| `cuda-toolkit` | 12.9.2.0 | none (its extras pull the CUDA wheels) |
| `nvidia-cublas-cu12` | 12.9.2.10 | `nvidia-cuda-nvrtc-cu12` |
| `nvidia-cuda-nvrtc-cu12` | 12.9.86 | none |
| `nvidia-cuda-runtime-cu12` | 12.9.79 | none |
| `nvidia-cufft-cu12` | 11.4.1.4 | `nvidia-nvjitlink-cu12` |
| `nvidia-curand-cu12` | 10.3.10.19 | none |
| `nvidia-cusolver-cu12` | 11.7.5.82 | `nvidia-cublas-cu12`, `nvidia-nvjitlink-cu12`, `nvidia-cusparse-cu12` |
| `nvidia-cusparse-cu12` | 12.5.10.65 | `nvidia-nvjitlink-cu12` |
| `nvidia-nvjitlink-cu12` | 12.9.86 | none |

- The installed `cuda`/`cupy`/`nvidia`/`fastrlock` set is exactly these eleven.
- `fastrlock` is neither required by CuPy 14.2.0 nor installed.
- **Verdict: the list is complete; no transitive dependency is missing.** `numpy` is the
  only out-of-set requirement and stays in the bundle (2.5.4 satisfies `<2.6,>=2.0`).
- The loader's drift guard should check that bound, because a bundle numpy of 2.6 or later
  would break the pack.
- `uv.lock` carries each wheel's URL and sha256 (for example
  `cupy_cuda12x-14.2.0-cp312-cp312-win_amd64.whl`). The manifest and the WP6.3 downloader can
  key on them.
- Measured size in the dev venv: `nvidia/` 2.3 GB, `cupy/` 147 MB.

### 4. The build plan

- **Script.** `tools/package/build.py --form onedir|onefile` builds ONE argument list
  (`pyinstaller_args(form)`) and calls `PyInstaller.__main__.run(args)` (the TTS160 shape).
  The two forms differ in `--onedir` / `--onefile` only.
- **Fixed arguments:**
  - the entry script `src/clearwater/__main__.py`, with `--paths src`;
  - `--name Clearwater`;
  - `--windowed`, `--noconfirm`, `--clean`;
  - `--distpath work/wp6.1/dist-<form>`, `--workpath work/wp6.1/build-<form>`,
    `--specpath work/wp6.1/spec-<form>`;
  - the version read from `clearwater.__version__`. It names the output folder or archive
    `Clearwater-<version>-windows-<form>`.
- **Excludes** (`--exclude-module`):
  - the GPU set: `cupy`, `cupyx`, `cupy_backends`, `cuda`, `nvidia`, `fastrlock`;
  - the test and tool code: `tests`, `tools`, `pytest`, `_pytest`, `xdist`, `pytest_timeout`,
    `pytestqt`;
  - the rest of the dev group: `mypy`, `ruff`, `psutil`, `cpuinfo`, `av`;
  - the comms group: `fastapi`, `uvicorn`, `jinja2`, `httpx`, `multipart`, `starlette`;
  - `tkinter`.

  CuPy is only reached by `importlib.import_module("cupy")` (a string, invisible to
  modulegraph). But SciPy's array-API layer contains function-level `import cupy`
  statements, and modulegraph follows those, so the explicit exclude is required.
  `build.py` then ASSERTS absence: it walks `dist` and the PYZ table of contents
  (PyInstaller's archive readers) and fails on any `cupy*`, `cuda.*`, `nvidia*` or `tests.*`
  entry.
- **Hidden imports.** None expected. `clearwater` has no dynamic imports besides CuPy's
  (grep `import_module` / `__import__` / `entry_points`). PIL's plugins and `scipy.fft` /
  `scipy.ndimage` are covered by PyInstaller's and hooks-contrib's hooks. Any `warn-*.txt`
  entry for a runtime package is triaged in turn 2.
- **Data files.** None from `clearwater`: the only non-Python file in the package is
  `py.typed`.
  - The ICC handling reads EMBEDDED profiles only. The Display P3 profile is BUILT in code
    (`io/photo/p3_profile.py`), and LittleCMS comes in as PIL's compiled `_imagingcms`.
    **So the brief's "ICC profiles the photo path reads" is an empty set.**
  - HEIC: `pillow_heif` 1.8.1 imports the top-level `_pillow_heif.cp312-win_amd64.pyd`.
    Its DLLs are delvewheel-mangled and sit beside it in `site-packages`: `libheif`,
    `libde265`, `libx265` (22 MB), `libstdc++`, `libgcc_s_seh`, `libwinpthread`.
    PyInstaller's PE import analysis collects these. Turn 2 checks they are in the bundle and
    that a HEIC decodes frozen.
- **Qt.** The application imports only `QtCore`, `QtGui` and `QtWidgets` (grep). PyInstaller
  6's Qt hook utilities collect, per module, the plugin families: platforms, platformthemes,
  platforminputcontexts, generic, iconengines, imageformats and accessible bridge for QtGui;
  styles for QtWidgets. They also collect the Qt translations. This is to be confirmed
  against the installed 6.22.3 hook sources in turn 2.
- **Which Qt plugins load today, and how I will find out.** `psutil.Process(pid).memory_maps()`
  after the first window, filtered to `PySide6\plugins\`, is run on BOTH `python -m clearwater`
  (dev venv, the baseline) and the frozen build. A photo is then opened and the scan repeated.
  No trimming: the plugin set beyond today's is out of scope.
- **FFmpeg.** The laptop's FFmpeg 9.0.2 `full_build-www.gyan.dev` (`ffmpeg.exe` and
  `ffprobe.exe`, 217 MiB each) is copied beside `Clearwater.exe` in each dist. See D1 for why
  "beside" is not by itself found by `find_tool`.

### 5. The GPU pack loader's design (`src/clearwater/gpu_pack.py`, stdlib only)

- **Stamp.** `<cupy-cuda12x version>-cu<CUDA major>`. The CUDA major is the `cuda12x`
  package suffix's digits, giving `14.2.0-cu12`. The expected table (the eleven name /
  version / wheel-sha256 rows from `uv.lock`, and the stamp) is a constant in `gpu_pack.py`.
  A parallel test asserts it equals `uv.lock` (the drift guard, which also checks
  `numpy<2.6`).
- **Layout.** `<root>/<stamp>/manifest.json` and `<root>/<stamp>/site-packages/`, filled
  in the spike by `uv pip install --offline --no-deps --target <root>/<stamp>/site-packages
  <the eleven pins>` (from the uv cache: no network), plus `build.py manifest <dir>`.
- **Manifest.**

  ```json
  {"format": 1, "stamp": "14.2.0-cu12",
   "distributions": [{"name": "...", "version": "...", "wheel_sha256": "...",
                      "record_sha256": "..."}]}
  ```

- **What is checked at load.**
  - the manifest parses, `format` is 1 and `stamp` matches;
  - the distribution set equals the expected eleven at the lock versions;
  - each `wheel_sha256` equals the lock's;
  - each `<name>-<version>.dist-info/RECORD` exists and its sha256 equals `record_sha256`.
- **What is not checked at load:** each file listed in RECORD (2.4 GB at every start). Turn 3
  times that deep check; my recommendation is that it is the downloader's install-time check
  (WP6.3).
- **Threat model:** a partial, corrupt or wrong-version install. It is not a local attacker
  who can already write the user's own folder.
- **Outcomes, one line each to the start-up log:**
  - `gpu pack 14.2.0-cu12: absent` when `<root>/<stamp>` does not exist, or `pack_root()` is
    None;
  - `rejected: <reason>` when the folder exists but any check fails;
  - `loaded` otherwise: `sys.path.insert(0, <root>/<stamp>/site-packages)`.

  The loader never writes, creates or deletes anything.
- **`pack_root(*, environ=None, platform=None, home=None)`, per Q6.** It mirrors
  `config.paths.app_locations`'s injection and fallbacks (`config/paths.py:84-136`: an
  unset, empty or relative variable falls back to the home folder).
  - win32: `%LOCALAPPDATA%\Clearwater\gpu-pack`;
  - linux: `$XDG_DATA_HOME/clearwater/gpu-pack`, default `~/.local/share/clearwater/gpu-pack`;
  - darwin: `None`.

  This is a deliberate difference from `app_locations`, which treats darwin as XDG.
- **How CuPy finds the CUDA DLLs (finding D2, needs a ruling).** `sys.path` insertion makes
  `import cupy` work, but NOT the NVIDIA DLLs.
  - CuPy loads them through `cuda.pathfinder.load_nvidia_dynamic_lib`. Its site-packages
    step scans `site.getsitepackages()` plus the user site, NOT `sys.path`
    (`cuda/pathfinder/_utils/find_sub_dirs.py`, `find_sub_dirs_all_sitepackages`, used by
    `_dynamic_libs/search_platform.py:30,54,95`).
  - Its system-search step is `LoadLibraryExW(name, NULL, 0)` under CPython's
    `LOAD_LIBRARY_SEARCH_DEFAULT_DIRS` (`load_dl_windows.py:136-152`), which honours
    `AddDllDirectory` directories and IGNORES `PATH`.
  - So the loader, on win32 and after validation, calls `os.add_dll_directory()` for each
    existing `site-packages/nvidia/*/bin`. It keeps the handles for the process life.
  - That is OS-specific code: an N1 site for CHARC to approve (AD-33). On other platforms
    nothing is added, and Linux library resolution from a pack is unproved (a recorded limit).
  - CuPy then derives its CUDA root from nvrtc's location (`cupy/_environment.py:142-185`).
    With `found_via` = system search it takes `nvidia/cuda_nvrtc` as the root. Turn 3 proves
    a kernel-compiling export works that way.
- **Masking check.** `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.4` exists on the
  laptop with only `include` and `lib` (no `bin`, no DLL). `CUDA_PATH` is unset in this
  shell. The proof still records every loaded NVIDIA DLL's path (psutil `memory_maps` of the
  frozen worker) and requires each to lie under the pack root.
- **Test isolation from the real `%LOCALAPPDATA%`.** I propose no new environment knob.
  - `test_gpu_pack.py` passes an explicit `root=tmp_path/...`, or an `environ=` mapping, or
    monkeypatches `LOCALAPPDATA` / `XDG_DATA_HOME` under `tmp_path`.
  - The only product call is in `__main__`, which tests reach only through
    `test_app_startup.py:171`. That test's subprocess already sets
    `LOCALAPPDATA=tmp_path/local`, so the pack is absent there.
  - A test asserts the loader creates nothing (a tree listing before and after).
- **The pack proof (turn 3).** It runs the frozen exe with `LOCALAPPDATA` AND `APPDATA`
  pointed under `work/wp6.1/appdata/`, because the dispatch forbids writing under the real
  `%LOCALAPPDATA%\Clearwater`. This also keeps the owner's settings and cache untouched.

### 6. Q1-Q6

- **Q1 (the N13 STOP).** I propose `pyinstaller` 6.22.3, uploaded 2026-09-12, with
  `pyinstaller-hooks-contrib` 2026.9, uploaded 2026-10-20. Source: the PyPI JSON API, read
  2026-11-04 08:35Z, `r0-pypi.txt`. Proposed pin: `pyinstaller>=6.22,<7` in `dev`.
  - **PyInstaller licence:** its license field reads "GPLv2-or-later with a special exception
    which allows to use PyInstaller to build and distribute non-free programs (including
    commercial ones)". Its classifier is GPLv2. `license_expression` is unset. It requires
    `pyinstaller-hooks-contrib>=2026.7`.
  - **hooks-contrib licence:** the license field is unset. Its classifiers are "Apache Software
    License" and "GPLv2" (a dual licence; the per-file split is read from its installed LICENSE
    in turn 2).
  - **New transitive build-time distributions:** `altgraph` 0.17.5 (MIT), `pefile` 2024.8.26
    (MIT), `pywin32-ctypes` 0.2.3 (BSD-3-Clause) and `setuptools` 84.2.1 (MIT). None of them is
    in `uv.lock` today. `packaging` is already locked (26.3).
  - **What ships in the artifact:** the bootloader and PyInstaller's run-time modules (under
    the GPL exception) and hooks-contrib run-time hooks (Apache-2.0). These are WP6.3's
    notices rows.
- **Q2.** Agree as ruled: one call in `__main__`, which covers the GUI and the frozen worker.
  Caveat: the UNFROZEN worker (`-m clearwater.app.export_worker`) bypasses `__main__`, so a
  source install with a pack folder and no CuPy would load the pack in the GUI but not in
  the worker. See D4.
- **Q3.** Agree: the default `_MEIxxxx` under `%TEMP%`. The worker reuses it (item 1 (c)).
  Turn 4 measures the extraction time and size. A crashed one-file process leaves its
  `_MEI` folder behind; the report states this.
- **Q4.** Agree: one table plus two first-window screenshots, taken with `PIL.ImageGrab`
  over the window rectangle from the dev venv.
- **Q5.** Confirmed (item 1), with the `sys.argv[2:]` pass-through and the Qt-free top
  level.
- **Q6.** Agree (item 5), with `pack_root` mirroring `app_locations`'s injection and
  fallbacks.

### 7. Cold-start method

The account is NOT elevated (`net session` fails), so a standby-list purge (RAMMap /
EmptyStandbyList need the profile privilege) is unavailable. A first run after the build is
NOT cold either: the build's own writes sit in the file cache.

- **Proposed cold start:** before each cold run, `robocopy /J` (unbuffered I/O, which bypasses
  the cache manager) the dist into a NEW folder under `work/wp6.1/cold-<form>-<n>`, then launch
  that copy once. Three copies, three runs per form.
  - Limit: Windows' own DLLs and the GPU driver stay warm, as they would after a real reboot
    only partly.
  - Sanity check: cold should be noticeably slower than warm. If it is not, the report says so.
- **Warm start:** relaunch the same copy immediately, three runs.
- **First window:** a poll at 10 ms, via `ctypes` `EnumWindows` / `IsWindowVisible` /
  `GetWindowThreadProcessId`, for a visible top-level window owned by the launched process or
  its descendants. A one-file build runs the application in a child of the bootloader. Then
  `WM_CLOSE` is sent and the exit awaited. This is Windows-only measurement code in
  `tools/package/build.py measure` (an N1 note for the spike tool).
- **First export:** time from spawn to the `{"result"...}` line for `Clearwater.exe
  --export-worker` fed one photo request: `tests/fixtures/stills/heic/heic10-gradient-display-p3.heic`
  to PNG, three runs per form. That covers the frozen start without Qt plus the real export
  engine. One GUI-driven photo export (PNG and JPEG) and one video export are also done by
  hand for the path checks, not timed. See D6.

### 8. Window and disk

- **Turn 4's EXCLUSIVE window:** about 35 minutes. Per form: 3 cold copies and launches
  (~4 min), 3 warm (~1.5 min) and 3 first exports (~2 min), plus the screenshot. Twice that,
  plus setup, teardown and checks.
- **Turn 2's builds:** about 5-8 minutes of CPU each. They are not timed, but should not
  overlap a gate leg.
- **Disk, estimated:**

  | Item | Estimate |
  |---|---|
  | onedir dist | ~0.3-0.4 GB |
  | onefile exe | ~0.15-0.2 GB |
  | each workpath | ~0.3 GB |
  | FFmpeg beside each dist | 0.43 GiB |
  | cold copies | about 3 x 0.8 GB onedir and 3 x 0.6 GB onefile (deletable after the window, on a grant) |
  | one-file extraction in `%TEMP%` | ~0.35 GB per running instance |
  | GPU pack | ~2.5 GB |
  | a worktree `.venv`, if turn 2 syncs one | ~3 GB (the main tree's `.venv` is 3.0 GB) |

  Peak about 10-12 GB. C: had 104 GB free at 08:36Z.

### Disputes and questions raised at round 0

- **D1 (finding, reproduced): FFmpeg "beside the executable" is not found as such.**
  - `find_tool` (`io/video/probe.py:100-121`) is `shutil.which(name)`: PATH, plus the CURRENT
    directory on Windows only when `NoDefaultCurrentDirectoryInExePath` is unset.
  - Reproduction (`r0-which-repro.txt`): with `PATH=C:\Windows\System32` and an `ffmpeg.exe`
    in the current folder, it returns None with the variable set (it is set in this agent
    shell). With the variable unset it finds `.\ffmpeg.EXE` from that folder and None from any
    other folder.
  - So the PATH-less run works only when the working directory is the executable's folder,
    as on an Explorer double-click.
  - Recommendation: in the spike, run the proof with cwd = the dist folder and the variable
    unset, record the dependence, and hand a real "beside the executable" lookup to WP6.3.
    The alternatives are a `PATH` prepend in `__main__`'s frozen branch (owned, but a product
    behaviour the brief did not grant) or a `find_tool` change (not owned).
- **D2 (needs a ruling, N1): `os.add_dll_directory` for the pack's `nvidia/*/bin`** (item 5).
  Without it the pack cannot load the CUDA libraries on a machine with no system toolkit.
- **D3 (question): where the loader's line reaches the log.** Logging is configured later, in
  `gui/shell.py:143` (`configure_logging`). The worker's protocol handler attaches only inside
  `run()` (`export_worker.py:276-279`). A record logged at `__main__`'s top is therefore
  dropped in both processes.
  - Recommendation: the GUI branch calls `configure_logging(app_locations().log_dir)` first,
    tolerating OSError. The shell's later call is then the idempotent same-file branch
    (`config/log.py:84-86`). The worker logs no pack line: its backend reason reaches the
    parent's log through the protocol.
- **D4 (question): should the loader act only when `sys.frozen`?** Recommended yes. The pack
  is the artifact's mechanism, and source installs use the `[gpu]` extra (N14's developer
  path). This removes Q2's caveat and makes the gate machine a no-op by construction. The
  brief's text implies it always acts.
- **D5 (owned paths).** I ask to add `tests/test_frozen_entry.py` (parallel: Q5 (a) by
  monkeypatching `sys.frozen` / `sys.executable`; (b) with injected fakes; an AST check that
  `__main__`'s top level imports no Qt-bearing module). A subprocess Qt-free check would be
  serial, which the brief excludes; the frozen build is checked by hand instead. The ledger
  itself is `docs/proofs/wp6.1-ledger.md`.
  - Harness registration: NONE of the new files needs it. `docs/proofs/`, `docs/reports/`,
    `tools/`, `src/` and `tests/` are instance-surface prefixes
    (`tests/harness/genericity_lists.py:253-268`).
- **D6 (question): the "first export" measure.** Photo exports run in the GUI process
  (`app/main.py:281-284`), and timing three GUI-driven exports needs UI automation. I propose
  the worker-headless measure (item 7) as "headless where the runner allows". Is that
  acceptable?
- **D7 (minor wording): "D111's line".** D111 is the memory-based CPU fallback. Without CuPy
  the line is AD-9's reason `CPU: CuPy not installed` (`core/backend.py:941-943`). The proof
  records that line.

Depth at round-0 end: DISPATCHER TO FILL

Depth at round-0 yield (dispatcher): 178,334.

## Turn 2 group A (2026-11-04 08:45-09:05Z): the build script and the onedir build

Built (owned paths):

- `tools/package/build.py`. One argument list (`pyinstaller_args(form, out=, version=)`)
  serves both forms. It is run in-process through `PyInstaller.__main__.run(args)`.
  - Entry `src/clearwater/__main__.py`, with `--paths src`. PyInstaller adds the script's
    TOP-LEVEL package folder (`src`), not `src/clearwater`, to the analysis path
    (`get_path_to_toplevel_modules`, `building/build_main.py:614-636`).
  - Flags: `--windowed --noconfirm --clean --name Clearwater`.
  - Outputs go to `work/wp6.1/dist-<form>/Clearwater-<__version__>-windows-<form>/`,
    `build-<form>/` and `spec-<form>/`.
  - Excludes `EXCLUDED_MODULES`.
  - The post-build checks are `forbidden_paths` (the release folder) and `forbidden_entries`
    (the executable's CArchive TOC and its PYZ module list). They fail the run on any of:
    - `cupy`, `cupyx`, `cupy_backends`, `cuda`, `nvidia`, `fastrlock` or `tests`;
    - a GPU-pack `.dist-info`;
    - a CUDA DLL;
    - a `clearwater` subpackage frozen at the top level, or an `io.*` submodule;
    - a non-stdlib top-level module outside `ALLOWED_TOP_LEVEL` (the product's dependency
      closure computed from `uv.lock`: numpy, scipy, PIL, pillow_heif, tifffile, PySide6,
      shiboken6, plus clearwater and `_pyi_rth_utils`).
  - `--with-ffmpeg` copies `ffmpeg` / `ffprobe` from PATH beside the executable. It is for
    group B; it was not run this turn.
  - The `measure` and `manifest` parts wait for turns 3-4.
- `tools/package/README.md`.
- Static checks on both: `uv run --no-sync ruff check tools/package` passed;
  `ruff format --check` reported 1 file already formatted; `mypy tools/package/build.py`
  passed. The whole configured `uv run --no-sync mypy` passed on 159 source files.
  `PyInstaller` has no `py.typed`, so `build.py` reaches it through
  `importlib.import_module`. This needs no `pyproject.toml` override.

Builds (`df -h /c` before each: 73 GB free at 08:48Z, 70 GB at 08:56Z; floor 25 GB):

| # | Command (from the worktree root) | Exit | Wall | Result |
|---|---|---|---|---|
| 1 | `uv run --no-sync python tools/package/build.py --form onedir > work/wp6.1/build-onedir.log 2>&1` | 0 | 287 s (PyInstaller 284.3 s) | 234.2 MiB; old check PASS |
| 2 | same, after the exclude list gained `yaml`, `_yaml`, `typing_extensions` and the allowlist check (`> work/wp6.1/build-onedir-2.log`) | 0 | 154 s (PyInstaller 152.7 s) | **233.8 MiB; every check PASS** |

- **Why build 2.** Build 1's PYZ held two packages outside the product's closure: `yaml`
  (imported by `numpy.__config__` / `scipy.__config__`; PyYAML is in the env through the
  comms group's `uvicorn[standard]`) and `typing_extensions` (imported only under
  `TYPE_CHECKING` or optionally by numpy / scipy; it comes from the dev tools).
- **The new check distinguishes.** Run on build 1's executable, it reports
  `['pyz-unexpected:typing_extensions', 'pyz-unexpected:yaml']`; on build 2 it reports none.
  Build 2's PYZ has 1,050 modules (build 1 had 1,068), 103 of them `clearwater.*`. Its
  package archive has 12 entries, all PyInstaller boot / run-time hooks (`pyi_rth_inspect`,
  `pyi_rth_pkgutil`, `pyi_rth_multiprocessing`, `pyi_rth_pyside6`) plus `__main__` and
  `PYZ.pyz`.

Size of build 2 by top-level entry (MiB; the 233.8 MiB total includes many small `.pyd` and
DLL files under 0.1 MiB each):

| Entry | MiB | Entry | MiB |
|---|---|---|---|
| `_internal/PySide6` | 73.7 | `_internal/libcrypto-3-x64.dll` | 5.5 |
| `_internal/scipy` | 46.1 | `_internal/libstdc++-6-*.dll` (pillow-heif) | 2.5 |
| `_internal/libx265-217-*.dll` (pillow-heif) | 21.6 | `_internal/libheif-*.dll` | 2.1 |
| `_internal/numpy.libs` | 20.2 | `_internal/base_library.zip` | 1.3 |
| `_internal/scipy.libs` | 19.3 | `_internal/shiboken6` | 1.1 |
| `_internal/PIL` | 10.7 | `_internal/unicodedata.pyd` | 1.1 |
| `Clearwater.exe` | 10.0 | `_internal/ucrtbase.dll` | 1.1 |
| `_internal/python312.dll` | 6.6 | `_internal/libssl-3-x64.dll` | 1.0 |
| `_internal/numpy` | 6.1 | `_internal/libde265-*.dll` | 0.9 |

- **Inside `PySide6` (73.7):**
  - `opengl32sw.dll` 20 (the Qt hook's software-OpenGL fallback);
  - `Qt6Core` 10, `Qt6Gui` 9.3, `Qt6Widgets` 6.3, `Qt6Network` 1.7, `Qt6Svg` 0.6;
  - `translations/` 6.9;
  - `plugins/` 5.7: `imageformats` 2.4, `platforms` 2.2, `tls` 0.66, `styles` 0.24,
    `generic` 0.10, `networkinformation` 0.08, `iconengines` 0.07.
- `libcrypto` / `libssl` / `_ssl` come with the stdlib `ssl`, which `urllib.request`,
  `http.client` and `logging.handlers` import. Qt's `tls` / `networkinformation` plugins and
  `Qt6Network` come from the PySide6 hooks. Trimming either is out of scope (the brief
  excludes the Qt plugin set beyond what the application loads). Group B measures what
  actually loads.

**warn-*.txt triage** (build 2, `work/wp6.1/build-onedir/Clearwater/warn-Clearwater.txt`,
277 `missing module` lines; classifier `warn_triage.py` and both outputs in
`clearwater-review-evidence/wp6.1/cell/t2a/`). All are ACCEPTED, none needs a hidden import:

- **A, excluded by design (1):** `cupy.cuda`, from `scipy._external.array_api_compat.cupy`.
  This is the analysis following SciPy's function-level CuPy imports, which the exclude
  stops.
- **B, non-Windows platform modules (18 names):** `posix`, `pwd`, `grp`, `fcntl`, `termios`,
  `resource`, `_posixsubprocess`, `_posixshmem`, `_scproxy`, `readline`, `vms_lib`, `java`,
  `_winreg` and the like. All are imported under platform guards.
- **C, names re-exported from compiled or dynamic modules (212):** `from pkg import name`
  where the name is defined inside a `.pyd` or by `globals()` updates: `scipy.special.*`
  (from `_ufuncs`), `scipy.sparse.*`, `scipy.linalg.*`, `numpy.*`, `multiprocessing.*`.
  These are attributes at run time, not modules.
- **D, optional third-party packages not installed in the dev env either (41 lines,
  28 top-level names):** Cython, cffi, dask, defusedxml, imagecodecs, jax, lxml,
  matplotlib, sparse, sphinx, threadpoolctl, torch, uarray, xarray, zarr, win32evtlog / pdh,
  and others. Every one is reached only through conditional, optional or delayed imports.
- **E, inspected by hand (5):**
  - `_typeshed`: a type-checker-only stub;
  - `dask.array` and `torch`: SciPy's array-API adapters, reached only for dask or torch
    arrays;
  - `olefile`: PIL's FlashPix / MIC plugins, formats Clearwater does not accept (spec 5.1:
    HEIC, JPEG, PNG, TIFF);
  - `zarr`: `tifffile.zarr`, the zarr store interface, unused.

  None is installed in the dev env, so the frozen run behaves as the source run.
- **The one build-log warning:** `Hidden import "scipy.special._cdflib" not found!` comes
  from PyInstaller's `hook-scipy.special._ufuncs.py:20-21`, which adds it for scipy >= 1.13.
  scipy 1.18.1 ships no `_cdflib` (no such file in `scipy/special/`), so this is benign.
  Group B's frozen start confirms SciPy imports.

No STOP. Group B (the onefile build and the plugin / path checks) is next.

Depth at turn-2 group-A end: DISPATCHER TO FILL

Depth at turn-2 group-A end (dispatcher): 248,067.

## Turn 2 group B (2026-11-04 09:05-09:25Z): the onefile build and the first frozen checks -- STOPPED on an incident

### INCIDENT (first): keystrokes went to a window that was not Clearwater's

- **What ran.** My GUI check script `clearwater-review-evidence/wp6.1/cell/t2b/gui_check.py`
  drove the onedir build's photo export with PowerShell `WScript.Shell` `AppActivate(<pid>)`
  plus `SendKeys`.
- **What went wrong.** AppActivate did NOT bring the Clearwater window forward, so the keys
  went to whatever window held the focus. Both screenshots from the run show other windows in
  front, PowerShell / terminal tabs, one of them a conversation session. They stay in
  `work/wp6.1/t2b/onedir/` and were not copied to evidence.
- **What was sent, between about 09:12:55Z and 09:19Z, twice:**
  - `Ctrl+O`;
  - the full path of a photo copy followed by Enter: first
    `C:\Users\rwsmy\clearwater\.worktrees\wp6.1\work\wp6.1\t2b\onedir\photos\heic-ad24-both.heic`,
    then the same folder's `jpeg-gradient-display-p3.jpg`;
  - `Alt+F`;
  - `e`.
- **The consequence is unknown.** If a terminal session had the focus, those two path lines
  may have been submitted to it as input. The owner should check the foreground
  terminal / session windows for those lines.
- **Current state.** No Clearwater process is left (`tasklist`), and I stopped the GUI
  automation at once. A warning file now sits beside the script
  (`t2b/WARNING-gui_check-keystrokes.txt`).
- **Rule for any successor:** no SendKeys, SendInput or keybd_event. Use a method bound to
  the Clearwater window itself: UI Automation patterns on its own elements, and PrintWindow
  for screenshots.
- **Result for this turn:** the GUI photo-export check (HEIC in, PNG out, EXIF), the
  write-journal check and both first-window screenshots were NOT obtained.

### The onefile build

`df -h /c` read 104 GB free at 09:08Z.

| Command (worktree root) | Exit | Wall | Result |
|---|---|---|---|
| `uv run --no-sync python tools/package/build.py --form onefile --with-ffmpeg > work/wp6.1/build-onefile.log 2>&1` | 0 | 104 s (PyInstaller 102.7 s) | `Clearwater.exe` 89.4 MiB; `ffmpeg.exe` 217.3 and `ffprobe.exe` 217.1 MiB beside it; forbidden / allowlist check PASS |

- The build log has the same single warning as onedir (`scipy.special._cdflib`, benign) and
  the same exclude list.
- FFmpeg was also copied beside the onedir `Clearwater.exe` by `build.copy_ffmpeg` (one
  `uv run --no-sync python -c` call).

### Checks obtained (onedir only, before the incident's effect was seen)

From `t2b/result-onedir.json` and `t2b/clearwater-onedir.log`:

- **Run setup.** `APPDATA` / `LOCALAPPDATA` were redirected to
  `work/wp6.1/t2b/onedir/{roaming,local}`. PATH was SET BY HAND to the exe's folder plus
  `C:\Windows\System32` and `C:\Windows` (D1 lands in turn 3). The working directory was
  `work/wp6.1/t2b/onedir`.
- **First window: PASS.** A top-level window titled `Clearwater`, 1293 x 815. It was
  detected by an EnumWindows poll over the process tree.
- **Qt plugins mapped at the first window** (psutil `memory_maps`):
  `platforms/qwindows.dll` and `styles/qmodernwindowsstyle.dll` only. Every `Qt6*.dll` was
  mapped from the bundle's `_internal/PySide6`. The dev-run baseline was NOT taken.
- **Start-up log** (frozen): starter presets installed, then
  `clearwater.core.backend CuPy not installed: No module named 'cupy'` and
  `clearwater.app.startup device: CPU: CuPy not installed`. That is AD-9's line, D7's
  wording, for the no-pack case. The log ends with `Clearwater closed`. `settings.json` was
  written with the defaults (method `c3`, PNG 16-bit, `_corrected` suffix). Exit code 0.
- **Not established:**
  - that FFmpeg beside the exe is used (the start-up log has no encoder line; the check
    needs a video open or the settings dialog's encoder list);
  - the write journal (no export happened);
  - the HEIC / JPEG photo export.
- **Spec note for the successor:** D22 makes photo output PNG only (8- or 16-bit). The
  group-B wording "PNG and JPEG out" can only mean HEIC in -> PNG and JPEG in -> PNG.
  `tests/fixtures/stills/heic/heic-ad24-both.heic` carries EXIF (118 bytes). The JPEG
  fixtures (`tests/fixtures/stills/jpeg/jpeg-gradient-*.jpg`) carry none (0 tags, an ICC
  profile only).
- **The frozen worker.** It is unreachable without the turn-3 code, by reading the code:
  `composition.py:461` builds `[sys.executable, "-m", "clearwater.app.export_worker"]`,
  and the frozen `Clearwater.exe` ignores `-m` and starts the GUI (`__main__.py:5-8`). So a
  video export from the frozen GUI would start a second GUI as its "worker". This was NOT run.
  It is turn 3's.

Depth at turn-2 end: DISPATCHER TO FILL

## Handoff to turn 3

Built and where (worktree `C:\Users\rwsmy\clearwater\.worktrees\wp6.1`, branch `wp6.1`; all
outputs gitignored under `work/wp6.1/`):

- **onedir:** `work/wp6.1/dist-onedir/Clearwater-1.0.0-windows-onedir/Clearwater/Clearwater.exe`
  (233.8 MiB) with `ffmpeg.exe` and `ffprobe.exe` beside it.
  Built by `uv run --no-sync python tools/package/build.py --form onedir`.
- **onefile:** `work/wp6.1/dist-onefile/Clearwater-1.0.0-windows-onefile/Clearwater.exe`
  (89.4 MiB) with FFmpeg beside it. Built by `... --form onefile --with-ffmpeg`.
- Both builds predate any turn-3 `src/` change; rebuild after it. Each build takes about
  2-5 minutes of CPU. Read `df -h /c` first (25 GB floor).

Open checks, in order:

1. **Turn 3's product code** (the brief's rulings D1-D4, Q5, Q6): `src/clearwater/gpu_pack.py`;
   the `__main__.py` dispatch and frozen PATH prepend; the `composition.py:461` frozen
   command; `tests/test_gpu_pack.py`, `tests/test_frozen_entry.py`. Then rebuild both forms.
2. **The frozen worker**: one video export and one HEIC -> PNG request through
   `Clearwater.exe --export-worker`, both forms. Also confirm that the one-file worker reuses
   the parent's `_MEI` folder (list `%TEMP%\_MEI*` during the export).
3. **The GUI checks still owed, both forms:**
   - first-window screenshots;
   - the Qt plugins against the dev run (`python -m clearwater`);
   - FFmpeg beside the exe in use;
   - HEIC -> PNG and JPEG -> PNG through the GUI with EXIF carried;
   - the write journal (`<APPDATA>/Clearwater/write-journal.json` after an export).

   Use a method bound to the Clearwater window: UI Automation on its own elements, PrintWindow
   for screenshots, or the owner by hand (D6 already allows "checked by hand"). NEVER
   keystroke injection (the incident above).
4. **The GPU pack proof** (brief design 2, ruling D2). Then turn 4's timings.

Commands that worked:

- **The onedir check run**, from the worktree root:

  ```
  uv run --no-sync python C:\Users\rwsmy\clearwater-review-evidence\wp6.1\cell\t2b\gui_check.py --label onedir --exe <exe> --work <worktree>\work\wp6.1\t2b --window-only
  ```

  `--window-only` skips the keystroke part. Its `shot()` still calls the unsafe `keys(pid, "")`
  (an AppActivate plus an empty SendKeys), so replace `shot()` with PrintWindow before reuse.
- **Without `--exe`**, the same script runs the dev baseline (`python -m clearwater`).

## Turn 3 group 1 (2026-11-04): the loader, the frozen entry, their tests

Fresh cell (implementer-opus-high), dispatch `clearwater-review-evidence/wp6.1/cell/dispatch-3.md`.
No GUI launch, no synthetic input, nothing under the real `%LOCALAPPDATA%\Clearwater` (checked
after the runs: the folder does not exist). Evidence `clearwater-review-evidence/wp6.1/cell/t3/`.

Built:

- `src/clearwater/gpu_pack.py` (stdlib only).
  - `pack_root()` per Q6.
  - `STAMP` = `stamp_for("cupy-cuda12x", <locked version>)` = `14.2.0-cu12`.
  - `LOCKED_DISTRIBUTIONS` = the eleven pack distributions with every locked wheel (29 file
    name / sha256 pairs, generated from `uv.lock` by `t3/gen_locked.py`; a test keeps them
    equal to the lock).
  - `check_pack(folder)` checks, in order: `manifest.json` present and parseable; `format` is
    the int 1; `stamp` matches; `site-packages` exists; the name set is exactly the eleven (no
    extra, no duplicate, none missing); each version is the lock's; each (wheel,
    wheel_sha256) is a locked pair; each installed `<name>-<version>.dist-info/RECORD` exists
    and has the manifest's sha256.
  - `load(root)`: absent when `root` is None or `root/<STAMP>` is not a folder; rejected on
    the first failed check; else, on win32 only, `os.add_dll_directory` for each
    `site-packages/nvidia/*/bin` (handles kept for the process; a failure closes those already
    added and rejects), then `site-packages` inserted at `sys.path[0]` once.
  - One INFO line `gpu pack 14.2.0-cu12: loaded` / `absent` / `rejected: <reason>`. Reasons
    are ASCII-safe: manifest text is escaped and cut at 80 characters.
  - `activate()` returns None and logs nothing unless `sys.frozen` (D4). Nothing is written.
- `src/clearwater/__main__.py`.
  - Module level: the stdlib and `clearwater.gpu_pack` only.
  - `main(argv)` first calls `prepend_executable_folder()` (D1: frozen only; not again when
    the folder is already first, as in a spawned worker).
  - `argv[1:2] == ["--export-worker"]`: `gpu_pack.activate()`, then
    `export_worker.main(argv[2:])` (Q5(b)).
  - Otherwise: `configure_logging(app_locations().log_dir)` with OSError suppressed (D3),
    `gpu_pack.activate()`, then `clearwater.app.main.main(argv)`, imported on that branch only.
- `src/clearwater/app/composition.py` `process_export_jobs`: `command` if given; else
  `[sys.executable, "--export-worker"]` when `sys.frozen`; else the unchanged
  `-m clearwater.app.export_worker` (Q5(a)). The one-line conditional became an if / elif /
  else on the same statement; the docstring states both. `jobs/export_process.py`,
  `io/video/pipes.py` and `app/export_worker.py` are untouched.
- `tools/package/build.py --write-manifest <pack root>/<stamp>` (`manifest_document`,
  `write_manifest`, `wheel_file_tags`, `installed_wheel_tags`): refuses a folder not named
  `STAMP`; picks the one locked wheel whose tags match the installed `WHEEL` file; records the
  lock's sha256 and the installed RECORD's sha256. `--form` and `--write-manifest` are mutually
  exclusive. README section added.

Commands (worktree root, Git Bash, `PYTEST_ADDOPTS` unset, outputs in `t3/`):

| Command | Exit | Summary |
|---|---|---|
| `uv run --no-sync pytest -q -rs -p no:cacheprovider --basetemp=<wt>/work/c61b-4 tests/test_gpu_pack.py tests/test_frozen_entry.py` | 0 | 49 passed in 1.82 s (slowest call 0.06 s) |
| `uv run --no-sync pytest -q -rs -p no:cacheprovider --basetemp=<wt>/work/c61b-5 tests/test_gpu_pack.py tests/test_frozen_entry.py tests/test_jobs_export_process.py tests/test_app_composition.py tests/test_wp42_composition.py tests/test_core_backend.py -m "not gpu"` | 0 | 200 passed, 41 deselected in 27.15 s |
| `uv run --no-sync ruff check .` | 0 | All checks passed |
| `uv run --no-sync ruff format --check .` | 0 | 321 files already formatted |
| `uv run --no-sync mypy` | 0 | no issues in 160 source files |
| `uv run --no-sync python <ev>/t3/mutate.py <wt>` | 0 | 21 / 21 mutations KILLED; the three product files restored byte-exact (sha256 checked) |

Not run (the gate is the orchestrator's): the gui / slow / serial modules, among them
`tests/test_app_startup.py` (which runs the real entry through `runpy`) and
`tests/test_app_export_worker.py`.

Mutations and the tests that catch them (each run by `t3/mutate.py`; the first failing test
is named):

| # | Mutation | Caught by |
|---|---|---|
| M1 | `activate()` ignores `sys.frozen` | `test_activate_does_nothing_in_a_source_run` |
| M2 | `sys.path.append` instead of `insert(0)` | `test_a_valid_pack_is_loaded` |
| M3 | RECORD sha256 not compared | `test_a_tampered_manifest_is_rejected[record]`, `test_a_changed_record_file_is_rejected` |
| M4 | wheel / sha256 not checked against the lock | `test_a_tampered_manifest_is_rejected[wheel-hash]`, `[wheel-name]` |
| M5 | missing distributions not checked | `test_a_missing_distribution_is_rejected` |
| M6 | DLL folders added off Windows | `test_no_dll_folder_is_added_on_linux` |
| M7 | macOS given an XDG root | `test_pack_root_on_macos_is_none` |
| M8 | stamp without the CUDA major | `test_the_stamp_is_the_cupy_version_and_the_cuda_major` |
| M9 | version not checked | `test_a_tampered_manifest_is_rejected[version]` |
| M10 | `clearwater.app.main` imported at the entry's top level | `test_the_worker_flag_runs_the_worker_without_qt` (import blocker) |
| M11 | worker given `argv[1:]` (its own flag: exit 2 in the real worker) | `test_the_worker_flag_runs_the_worker_without_qt`, `test_the_worker_flag_alone_passes_no_arguments` |
| M12 | no loader on the worker branch | `test_the_worker_flag_runs_the_worker_without_qt` (call order) |
| M13 | loader before the log on the GUI branch | `test_anything_else_starts_the_gui_after_logging_and_the_loader` |
| M14 | PATH prepend not guarded by `sys.frozen` | `test_a_source_run_leaves_path_alone` |
| M15 | PATH prepended again when already first | `test_frozen_puts_the_executable_folder_first_on_path` |
| M16 | `main()` never prepends PATH | `test_the_entry_sets_path_before_either_branch` |
| M17 | frozen build keeps the `-m` command | `test_a_frozen_build_re_enters_its_executable_as_the_worker` |
| M18 | worker branch opens the log file | `test_the_worker_flag_runs_the_worker_without_qt` (call list) |
| M19 | `format: true` accepted (`True == 1`) | `test_a_tampered_manifest_is_rejected[format-bool]` |
| M20 | non-ASCII manifest text in a reason | `test_an_extra_or_duplicated_distribution_is_rejected` |
| M21 | unreadable RECORD reported as missing | `test_an_unreadable_record_is_rejected` |

Other tests and what they pin:

- `test_locked_distributions_equal_the_lock`: the constant against `uv.lock`. The closure of
  `cupy-cuda12x[ctk]` minus numpy is the eleven, and the versions and wheel pairs are equal.
  It catches a lock bump without a loader update.
- `test_the_bundle_numpy_satisfies_cupys_requirement`: the locked numpy lies inside CuPy's
  installed `numpy` bound (skips if CuPy is not installed).
- `test_pack_root_on_windows`, `_on_linux`, `_reads_the_running_platform_and_environment`:
  the environment and home fallbacks, by injection and by monkeypatch of `sys.platform` and
  the environment. `test_the_app_folder_names_match_config_paths`.
- `test_no_pack_is_absent_and_changes_nothing` (missing / empty / None root: nothing created,
  `sys.path` unchanged, one `absent` line); `test_a_pack_under_another_stamp_is_absent`;
  `test_a_manifest_naming_another_stamp_is_rejected`.
- `test_the_dll_folders_are_added_on_windows` (exactly the eight `nvidia/*/bin`, not
  `include`); `test_a_failing_dll_folder_rejects_the_pack`.
- `test_an_injected_command_wins_when_frozen`; `test_a_log_folder_failure_does_not_stop_the_gui`;
  the build helper's three tests.

Self-review (suspected / confirmed / fixed):

1. A RECORD that exists but cannot be read was reported as `missing`: confirmed, fixed
   (`unreadable: <type>`); M21.
2. `format: true` passed the `== 1` check: confirmed, fixed (int type check); M19.
3. A manifest name with non-ASCII text reached the log line unescaped: confirmed, fixed
   (`_safe`); M20.
4. The DLL-failure reason named only `bin`: fixed to `nvidia/<lib>/bin`.

A second pass found nothing new.

Notes for group 2 and the report:

- The pack's `site-packages` is put on `sys.path`, not processed by `site.addsitedir`, so a
  `.pth` file in it is ignored. None of the eleven wheels is expected to ship one; group 2
  confirms on the real install.
- The worker logs no pack line (D3). Its `clearwater` logger has no handler when `activate()`
  runs, and the line is INFO, below the last-resort handler's WARNING, so nothing reaches the
  worker's stderr either.
- In a source run the loader logs nothing (D4), so the gate machine is a no-op by
  construction, whatever folders exist.

Commits: `3ed5c409` feat(wp6.1): GPU pack loader from a per-user folder, its tests, the
manifest helper; `01cdd6ca` feat(wp6.1): frozen entry -- --export-worker re-entry, PATH
prepend, frozen worker command.

Deviation (accepted by the dispatcher at dispatch-4): `process_export_jobs`'s one-line
conditional became an if / elif / else on the same statement; the behaviour is Q5(a)'s.

Depth at turn-3 group-1 end (dispatcher): 190,972.

## Turn 3 group 2a (2026-11-04 ~09:30-10:00Z): Reviewer A round 1 fixes, both rebuilds

Dispatch `clearwater-review-evidence/wp6.1/cell/dispatch-4.md`. No GUI launch, no
`--export-worker` run, no synthetic input. Group 1's composition deviation was accepted by
the dispatcher (above).

### Reviewer A round 1 adjudication

Review: Codex at the orchestrator's seat, on turn 2's `tools/package` at `526f3a8f`. Full text
`clearwater-review-evidence/wp6.1/A/r1/review.txt`. Verdict NEW_CRITICAL_MAJOR.

Every finding is FIXED; none is disputed. The tests are in the new module
`tests/test_tools_package_build.py` (21 tests).

The turn-2 column comes from running the same module against turn 2's `build.py`
(`git show 526f3a8f:tools/package/build.py`, loaded through `WP61_BUILD_SCRIPT`;
`t3/pytest-9-turn2.log`). The result was 20 failed, 1 passed (the no-false-positive test).

| # | Sev | Verdict | Fix (`tools/package/build.py`) | Test(s) | On turn 2's code |
|---|---|---|---|---|---|
| F1 | MAJOR | FIXED | `name_violations` checks EVERY component, lower-cased, of every dist path, CArchive entry, ZIP member and dotted PYZ module against `GPU_MODULE_NAMES`. `CUDA_LIBRARY` is applied to each basename. | `test_a_nested_cuda_library_in_the_dist_is_found`, `test_a_nested_gpu_package_in_the_dist_is_found`, `test_nested_gpu_entries_in_the_package_archive_are_found` (a real CArchive + PYZ) | `assert []`: the nested DLL, the nested `cupy_backends`, the CArchive entries and `PySide6.cupy_backends` all passed |
| F2 | MAJOR | FIXED | All comparisons are made after lower-casing. | `test_gpu_names_in_another_case_are_found_in_the_dist`, `..._in_the_package_archive` | `assert []` for `Cupy/__init__.pyc` and `NVIDIA/cublas/bin/cublas64_12.dll` |
| F3 | MAJOR | FIXED | `zip_violations` opens each ZIP in memory and recurses to depth 4. A ZIP is found by suffix (`.zip` / `.egg` / `.whl`) or by the `PK\x03\x04` magic, in the dist and in CArchive data / binary entries. Nothing is extracted to disk. An unreadable ZIP is a violation. | `test_a_gpu_module_inside_base_library_zip_is_found`, `test_a_gpu_module_inside_an_archived_zip_is_found`, `test_zips_are_found_by_magic_and_opened_recursively`, `test_an_unreadable_zip_fails_closed`, `test_zip_members_are_never_extracted_to_disk` | `assert []` in each |
| F4 | MAJOR | FIXED | `build()` sets `PYINSTALLER_CONFIG_DIR=<out>/pyinstaller-config` before PyInstaller is run or imported for the build. | `test_pyinstallers_cache_is_kept_under_the_output_folder` | `assert None is not None` (the variable was not set) |
| F5 | minor | FIXED | The allowlist (`ALLOWED_TOP_LEVEL` plus the stdlib) now also covers loose `.py` / `.pyc` / `.pyd` / `.so` files relative to a `sys.path` root (`_internal`, the one-file root, a root-level ZIP), and CArchive module entries (PyInstaller's `pyimod*` / `pyiboot*` / `pyi_rth_*` allowed). The README is corrected. | `test_an_unexpected_extension_module_in_the_dist_is_found`, `..._in_the_package_archive_is_found`; no false positive: `test_the_products_own_modules_and_the_stdlib_pass` | `assert []` for `av/_core...pyd` and `yaml/__init__.pyc` |
| F6 | minor | FIXED | `clean_release_dir` deletes `dist-<form>/<release>` (and only that, after checking it lies inside `out`) before each build. | `test_a_rebuild_starts_from_an_empty_release_folder` | stale `ffmpeg.exe` was still present when PyInstaller ran |
| F7 | minor | FIXED | `copy_ffmpeg` copies to the canonical `ffmpeg.exe` / `ffprobe.exe`. `tool_version` then runs each copy's `-version` from the dist folder with PATH = that folder only; it requires exit 0 and a `version` line, and the build prints that line. | `test_ffmpeg_is_copied_under_its_canonical_name`, `test_a_copied_tool_that_does_not_run_as_ffmpeg_is_refused` | `['ffmpeg-9.0.2.exe'] == ['ffmpeg.exe']` failed; `tool_version` absent |
| F8 | minor | FIXED | `app_version()` parses `src/clearwater/__init__.py` with `ast` (no import). The `--write-manifest` branch sets `sys.dont_write_bytecode` before its lazy `clearwater.gpu_pack` import. The module-level `from clearwater import gpu_pack` that group 1 added is gone. | `test_the_version_is_read_without_importing_the_package` | `'stale-installed' == '1.0.0'` failed |
| F9 | advisory | BANKED | The allowlist names top-level packages, not distributions (`PySide6.QtCharts` would pass). Out of envelope: the locked environment has no Addons. Stated in the README's scope. | none | n/a |
| F10 | advisory | FIXED (by F8) | No import, so a pre-imported stale `clearwater` cannot supply the version. | same test as F8 | same failure |
| F11 | advisory | FIXED (one pattern) | `CUDA_LIBRARY` takes an optional `lib` prefix and `.dll` / `.so` / `.so.<n>`. The README states that validation was on Windows only. | `test_linux_cuda_library_names_are_found` | `assert []` |

Also added:

- `test_the_scipy_adapter_exception_is_narrow`. On turn 2's code it fails only on the new
  violation label.
- `test_shadowing_top_level_modules_are_found`. This one is a regression test: turn 2 also
  flagged these names, and the test fails there only because the label format changed.

**One new adjudication, for the dispatcher to see.** On the turn-2 dists (read-only,
`t3/calibrate-turn2-dists.txt`), the deeper check found four PYZ modules:
`scipy._external.array_api_compat.cupy` (+ `._aliases`, `._info`, `._typing`).

- These are SciPy's own vendored array-API adapter, shipped inside the scipy wheel. They are
  not CuPy code; they import `cupy` only when handed CuPy arrays.
- I did not exclude them, because that would change what SciPy can import.
- Instead I added `GPU_NAME_EXCEPTIONS = (("scipy", "_external", "array_api_compat", "cupy"),)`.
  It excuses only that one `cupy` component; every other component of such a path is still
  checked (the narrow test pins this).
- The alternative is `--exclude-module scipy._external.array_api_compat.cupy`. The
  dispatcher rules if wanted.

### F4: the default cache, before and after

- Turn 2's three builds each logged `Removing temporary files and cleaning cache in
  C:\Users\rwsmy\AppData\Local\pyinstaller`: `build-onedir.log`, `build-onedir-2.log`,
  `build-onefile.log`.
- So turn 2's builds DID clean PyInstaller's default cache folder. That folder is
  PyInstaller's own bincache and nothing else; PyInstaller's `--clean` removes only its cache
  folder.
- Before this group's builds (09:53Z), `%LOCALAPPDATA%\pyinstaller` did not exist. After
  both builds, it still does not exist.
- This group's build logs name `...\work\wp6.1\pyinstaller-config\pyinstaller` as the cleaned
  cache instead.

### The rebuilds

Both builds ran with the fixed script and group 1's product code (`51ae68f6`), from the
worktree root.

| # | Command | `df -h /c` before | Exit | Wall (shell / PyInstaller) | Result |
|---|---|---|---|---|---|
| 3 | `uv run --no-sync python tools/package/build.py --form onedir --with-ffmpeg > work/wp6.1/build-onedir-3.log 2>&1` | 101 GB free (09:53:59Z) | 0 | 116 s / 106.1 s | `_internal` 223.8 MiB + `Clearwater.exe` 10.1 MiB = 233.9 MiB bundle; 668.2 MiB release with FFmpeg; bundle checks 7.8 s: **PASS** |
| 4 | `uv run --no-sync python tools/package/build.py --form onefile --with-ffmpeg > work/wp6.1/build-onefile-2.log 2>&1` | 100 GB free (09:56:10Z) | 0 | 100 s / 97.6 s | `Clearwater.exe` 89.4 MiB; 523.8 MiB release with FFmpeg; bundle checks 0.9 s: **PASS** |

- FFmpeg (F7, design item 5): each copy ran `-version` from its dist folder with PATH set to
  that folder only.
  - `ffmpeg version 9.0.2-full_build-www.gyan.dev Copyright (c) 2000-2026 the FFmpeg developers`
  - `ffprobe version 9.0.2-full_build-www.gyan.dev Copyright (c) 2007-2026 the FFmpeg developers`

  The licence line is the report's (turn 4).
- Build-log warnings, the same in both builds and in all three turn-2 builds:
  - `Hidden import "scipy.special._cdflib" not found!` (benign; turn 2 group A).
  - A CuPy `UserWarning: CUDA path could not be detected`, printed during PyInstaller's
    "Looking for dynamic libraries" step. PyInstaller's isolated analysis process imports
    the dev venv's CuPy at that point, at BUILD time only. The bundle check shows no CuPy
    reached either artifact. A note for the report.

### Commands and exits (outputs in `t3/`)

| Command | Exit | Summary |
|---|---|---|
| `pytest -q -rs -p no:cacheprovider --basetemp=<wt>/work/c61b-10 tests/test_tools_package_build.py tests/test_gpu_pack.py tests/test_frozen_entry.py` | 0 | 70 passed in 4.25 s |
| `WP61_BUILD_SCRIPT=<turn-2 build.py> pytest ... tests/test_tools_package_build.py` (`--basetemp=<wt>/work/c61b-9`) | 1 | 20 failed, 1 passed (the before record) |
| `ruff check .` | 0 | All checks passed |
| `ruff format --check .` | 0 | 322 files already formatted |
| `mypy` (strict, configured set) | 0 | no issues in 160 source files |
| `mypy --platform darwin tools/package/build.py src/clearwater/gpu_pack.py src/clearwater/__main__.py` | 0 | no issues in 3 source files |

Commit: `51ae68f6` fix(wp6.1): bundle checks at every depth, case and ZIP member; build
hygiene (Reviewer A r1).

Depth at turn-3 group-2a end: DISPATCHER TO FILL

## Turn 3 group 2b-1 (2026-11-04 ~10:15-10:50Z): Reviewer A round 2 fixes, rebuilds, the headless frozen worker

Fresh cell (implementer-opus-high), dispatch `clearwater-review-evidence/wp6.1/cell/dispatch-5.md`.
No GUI launch, no synthetic input, `t2b/gui_check.py` not run. Nothing under the real
`%LOCALAPPDATA%\Clearwater` (checked at the end: the folder does not exist). Evidence
`clearwater-review-evidence/wp6.1/cell/t3b/`.

### Reviewer A round 2 (Codex at the dispatcher's seat, on `16e03c0f`)

Full text `clearwater-review-evidence/wp6.1/A/r2/review.txt`: 6 MAJOR, 6 minor, 2 advisory, all
in envelope except #14. Held for CHARC (not fixed here): #1 + #2 (what the pack check proves)
and #3 (the PySide6 runtime hook loads Qt in the worker; measured below). #7 is held with
#1 / #2. #14 is banked.

The "on `16e03c0f`" column is the same test files run against `16e03c0f`'s `src` and `build.py`
(`git archive 16e03c0f`, `PYTHONPATH` and `WP61_BUILD_SCRIPT` pointing at the copy):
`t3b/pytest-4-on-16e03c0f.log`, **12 failed, 73 passed**. Line numbers are the current files'.

| # | Sev | Verdict | Fix | Test(s) | On `16e03c0f` |
|---|---|---|---|---|---|
| 1, 2 | MAJOR | HELD (CHARC) | none | none | n/a |
| 3 | MAJOR | HELD (CHARC); measured | none (see the #3 table) | none | n/a |
| 4 | MAJOR | FIXED | `FORBIDDEN_LIBRARY_PREFIXES` gains `nvblas`, `cudnn`, `cutensor`, `nccl`, `nvtx` (`tools/package/build.py`) | `test_every_dll_the_locked_pack_wheels_install_is_flagged` (every DLL basename the eleven locked wheels' RECORD files list, 14, plus `cudnn64_9.dll`, planted nested, beside the exe, in a ZIP and as a CArchive entry); `test_every_extension_module_the_locked_pack_wheels_install_is_flagged` (all 63 `.pyd` at their RECORD paths, at `_internal/` and at the release root) | `test_tools_package_build.py:430` `nvblas64_12.dll` not flagged; `:449` the release-root `.pyd` not flagged (that one is #8) |
| 5 | MAJOR | FIXED | script and option entries are named-checked (`module_root=False`); the boot-prefix exemption now drops only the allowlist rules (`module_violations`) | `test_script_and_boot_module_entries_are_checked_for_gpu_names` (`cupy/__init__.py` and `tests/accidental.py` as `s` entries, `pyimod_accidental.cupy` as `m`; the real boot names, `__main__` and an `o` option pass) | `:469` `pkg:cupy/__init__.py (gpu-module)` absent |
| 6 | MAJOR | FIXED | `__main__.main` calls `_start_logging()` only when `sys.frozen` | `test_a_source_run_starts_the_gui_as_1_0_0_did` (real `app_locations` + `configure_logging`, app data under `tmp_path`, a stand-in GUI: no log folder, no new handler); the two GUI-branch log tests now run frozen | `test_frozen_entry.py:217` `assert not log_dir.exists()` |
| 7 | minor | HELD with #1 / #2 | none | none | n/a |
| 8 | minor | FIXED | every loose file in the release folder meets the allowlist (`forbidden_paths`: `module_root=is_file`); `_bundle_parts`' docstring corrected | `test_an_extension_module_beside_the_executable_is_found` (`av.pyd` at the root and beside the exe, `Clearwater/yaml/__init__.pyc`) | `:479` `dist:av.pyd` not flagged |
| 9 | minor | FIXED | `check_pack` turns any `OSError` into `pack unreadable: <type>`; `load` (`_find_and_load`) the same for the stamp folder's `is_dir`; `_add_dll_directories` returns `DLL folders unreadable: <type>` | `test_a_file_system_error_is_a_rejection_not_an_exception[5 cases]` (`PermissionError` from the stamp folder, `manifest.json`, `site-packages`, a RECORD, an `nvidia/*/bin`) | all 5: `PermissionError` escaped `gpu_pack.load` (`test_gpu_pack.py:383`) |
| 10 | minor | FIXED | `prepend_executable_folder` is membership-based (`normcase(normpath)` of every entry): no change when the folder is ANY entry | `test_a_worker_whose_path_was_changed_by_pyside6_does_not_add_the_folder_again` (parent prepend, then the PySide6 hook's two prepends, then the child: unchanged, the folder once; a trailing-separator spelling counts) | `:283` the child prepended again (`True is False`) |
| 11 | minor | FIXED (test) | none in product code | `test_the_worker_branch_imports_no_qt_in_a_fresh_interpreter` (`python -I -c`: imports the entry and `export_worker` afresh, stubs `export_worker.main`, runs the `--export-worker` branch, lists `PySide6` / `shiboken6` / `clearwater.gui` / `clearwater.app.main` in `sys.modules`); `test_the_fresh_interpreter_probe_sees_a_top_level_qt_import` (the reviewer's mutation on a copy of the package under `tmp_path`: caught) | passes (the product was right); the self-check is the distinguishing run |
| 12 | minor | FIXED | `_safe` escapes ASCII control characters as `\x..` after the non-ASCII escape | `test_a_reason_is_always_one_line` (`\n`, `\t`, `\r`, `\x7f` in a name) | `test_gpu_pack.py:385` raw newline in the reason |
| 13 | advisory | FIXED (test) | none | `test_each_copied_tool_is_run_from_the_destination` (`tool_version` called on each copy, its line returned) | passes (the code was right); fails on the reviewer's mutation (`tool_version(target)` -> `""`): `t3b/pytest-5-mut13.log`, 1 failed |
| 14 | advisory | BANKED (out of envelope) | none | none | n/a |

Residual on #10 (for the dispatcher): membership means a user `PATH` that already lists the
executable's folder BEHIND another FFmpeg folder is left as it is, so that FFmpeg would win.
Moving the folder to the front (deduplicated) would close it; the literal ruling was kept.

Self-review (suspected / confirmed / fixed): (1) the first #4 `.pyd` assertion expected
`unexpected-module` for every root `.pyd`: `core.cp312-win_amd64.pyd` is `shadow` (a
clearwater subpackage name), confirmed correct behaviour, the test now accepts any rule;
(2) the strict mypy run over the touched TEST files found 7 errors from group 1 (`object()` as
`photo_exports`, `_command` on `ExportJobs`, an `Any` return, `os.add_dll_directory` on darwin):
confirmed, fixed in `16aceca9`. A second pass found nothing new.

Commands (worktree root, Git Bash, `PYTEST_ADDOPTS` unset; outputs in `t3b/`):

| Command | Exit | Summary |
|---|---|---|
| `pytest -q -rs -p no:cacheprovider --basetemp=<wt>/work/c61c-8 tests/test_gpu_pack.py tests/test_frozen_entry.py tests/test_tools_package_build.py tests/test_jobs_export_process.py tests/test_app_composition.py tests/test_wp42_composition.py tests/test_core_backend.py -m "not gpu"` | 0 | 236 passed, 41 deselected in 26.83 s (head `16aceca9`) |
| the three owned modules alone (`c61c-3`) | 0 | 85 passed in 5.13 s; slowest the two fresh-interpreter tests, 1.54 s and 0.79 s |
| the same three against `16e03c0f` (`c61c-4`) | 1 | 12 failed, 73 passed (the before record) |
| `ruff check .` / `ruff format --check .` | 0 / 0 | All checks passed / 322 files already formatted |
| `mypy` (strict, configured set) | 0 | no issues in 160 source files |
| `mypy --platform darwin tools/package/build.py src/clearwater/gpu_pack.py src/clearwater/__main__.py` | 0 | no issues in 3 source files |
| `mypy --strict` (win32 and `--platform darwin`) on the three touched test modules | 0 / 0 | no issues in 3 source files (after `16aceca9`) |

Commits: `5e437c46` fix(wp6.1): source-run logging as 1.0.0, PATH membership, pack errors as
rejections, one-line reasons; `240a62e0` fix(wp6.1): bundle checks name every entry type,
every locked CUDA DLL, modules beside the exe; `16aceca9` test(wp6.1): strict mypy on the tests.

### The rebuilds (from `240a62e0`; the product code is unchanged by `16aceca9`)

| # | Command (worktree root) | `df -h /c` before | Exit | Wall (shell / PyInstaller) | Result |
|---|---|---|---|---|---|
| 5 | `uv run --no-sync python tools/package/build.py --form onedir --with-ffmpeg > work/wp6.1/build-onedir-t3b.log 2>&1` | 85 GB free (10:26:25Z) | 0 | 196 s / 173.0 s | `_internal` 223.8 MiB + `Clearwater.exe` 10.1 MiB; 668.2 MiB release with FFmpeg; bundle checks 16.7 s: **PASS** |
| 6 | `... --form onefile --with-ffmpeg > work/wp6.1/build-onefile-t3b.log 2>&1` | 82 GB free | 0 | 214 s / 206.3 s | `Clearwater.exe` 89.4 MiB; 523.8 MiB release; bundle checks 1.4 s: **PASS** |

Sizes are unchanged from builds 3 / 4. The walls are about twice group 2a's: a Codex cell
(WP-T8) was running tests beside them (not timed, as the dispatch allows). The same two
build-log warnings as before (`scipy.special._cdflib`; the build-time CuPy `CUDA path`
warning). FFmpeg copies: `ffmpeg version 9.0.2-full_build-www.gyan.dev`, `ffprobe version
9.0.2-full_build-www.gyan.dev`. The stricter #5 / #8 checks found nothing in either real build.

### The frozen worker, headless (D6)

Tool: `t3b/headless.py` (evidence tooling, run from the dev environment). Each request line is
built by the product's `ProcessExportJobs._request_line`; each worker is spawned as
`jobs/export_process.py` spawns it (`Popen(command, stdin/stdout/stderr=PIPE,
**tool_spawn_kwargs())`, the request written first, stdin closed on the result). The child's
`APPDATA` / `LOCALAPPDATA` / `TEMP` / `TMP` are under `work/wp6.1/t3b/<form>/`, `PATH` is
`C:\Windows\System32;C:\Windows`, no `PYTHON*` variable, and the working directory is that
work folder (never the dist folder). Command: `uv run --no-sync python
<ev>/t3b/headless.py run --form <form> --req <heic|jpeg|video>`; worker command
`<dist>\Clearwater.exe --export-worker`. Requests: `heic-ad24-both.heic` -> PNG,
`jpeg-gradient-display-p3.jpg` -> PNG (D22), `tests/fixtures/video/vfr.mp4` (the shortest
fixture video: 1.33 s, 30 frames, 320x180) -> MP4; c3 defaults, `force_cpu` off, encoder
`auto`. Every record is in `t3b/runs.jsonl`.

| Form | Request | Exit | Output | Final protocol message | EXIF check | Left over |
|---|---|---|---|---|---|---|
| onedir | HEIC | 0 | `heic-ad24-both_corrected.png` 37,104 B (96x64 16-bit RGB) | `result` ok, device `CPU: CuPy not installed`, warning `Processed on the CPU (CPU: CuPy not installed).` | eXIf 178 B == `exif.edit(source 112 B, 96, 64)`: **PASS**; differs from the source only in D63's four fields (Orientation 6 -> 1, Software, PixelX / YDimension) | none |
| onedir | JPEG | 0 | `jpeg-gradient-display-p3_corrected.png` 1,921 B | the same | the source has no EXIF; eXIf 92 B == `exif.edit(None, 96, 64)`: **PASS** | none |
| onedir | video | 0 | `vfr_corrected.mp4` 55,165 B | `result` ok, the same device | n/a | none |
| onefile | HEIC | **3221225477** | the same PNG, 37,104 B | the same `result` ok | **PASS** (as onedir) | none |
| onefile | JPEG | **3221225477** | 1,921 B | the same | **PASS** | none |
| onefile | video | **3221225477** | 55,165 B | the same | n/a | none |

- **FFmpeg (D1).** Both video runs spawned the BUNDLED `<dist>\ffmpeg.exe` and `ffprobe.exe`
  (the worker's process tree, from psutil), with `PATH` = Windows only and the working
  directory outside the dist. The protocol log has no `shutil.which` line. The worker's own
  `PATH`, read from the frozen child (psutil `environ()`, the `path-check` runs): onedir
  `<dist>;<dist>\_internal\PySide6;<dist>\_internal;C:\Windows\System32;C:\Windows`, onefile
  `<dist>;<TEMP>\_MEI...\PySide6;<TEMP>\_MEI...;...`: the executable's folder once, first,
  after PyInstaller's PySide6 hook added its two entries (D1 and #10 as built).
- **Left over.** No process of any run's own tree was alive after it (psutil, by PID).
  `tasklist` twice showed one `ffmpeg.exe` that was not in the run's tree (PIDs 35044, 25248;
  another session's); at the end `tasklist` shows no `Clearwater.exe` and no `ffmpeg.exe`. No
  `_MEI` folder was left by a run that ended by itself.
- **The non-zero exits: a 1.0.0 export-worker defect, not a packaging one (a DR row
  candidate; `app/export_worker.py` is not owned).** Every non-zero exit is the worker
  crashing AFTER its result line: stderr `Fatal Python error: _enter_buffered_busy: could not
  acquire lock for <_io.BufferedReader name='<stdin>'> at interpreter shutdown, possibly due
  to daemon threads`, then exit `0xC0000005`. The worker's daemon `_watch_stdin` thread is
  blocked in `stdin.readline()` when the main thread finalises; it is a race with the
  parent's close of stdin on the result. Reproduced with the SOURCE worker (`python -m
  clearwater.app.export_worker`) and with the product's own parent (`ProcessExportJobs`,
  unchanged, `t3b/repro_exit.py`, no sampling): the parent logs `export worker sent its
  result, then exit status 3221225477`; source 5 / 5 and 2 / 2 runs, onedir 2 / 5, onefile
  1 / 5 (`t3b/repro-exit-*.log`), and 9 / 9 of the #3 runs below (all three forms). The job's
  result is still used (the export is OK), and the crash adds about 1 s before the process
  ends. (The source runs in `repro_exit.py` failed their export for the expected reason, no
  `ffprobe` on the Windows-only `PATH`, and crashed the same way after that result.)

### The write journal (D85)

Tool: `headless.py journal --form <form> --target <worker|spawned>`, records in
`t3b/journal.jsonl`. The GUI's own guarded path runs in the dev process: `GuardedExports(
ProcessExportJobs(..., command=[<exe>, "--export-worker"]), cache=DeferredProxyCache(<redirected
cache>), locks=ClipLocks(), journal=WriteJournal(<redirected config>))` on `vfr.mp4`. The kill
is `taskkill /PID <pid> /F` once the temporary output exists in the output folder (the encode
has begun). Then the product's start-up clean-up `clean_leftovers(settings,
WriteJournal(<redirected config>))`.

| Form | Killed PID | During the export | After the kill | `clean_leftovers` | After it |
|---|---|---|---|---|---|
| onedir | the worker (the spawned `Clearwater.exe`) | journal: one entry, the output folder; folder: `vfr_corrected.clearwater-partial-66938c574ef6.mp4` | job failed `The export worker ended without a result (exit status 1)`; the entry KEPT (its folder holds a temporary); the partial file still there; no process left | `removed=(...partial-66938c574ef6.mp4,)`, `failed=()` | journal `entries: []`; folder empty: **PASS** |
| onefile | the worker = the bootloader's CHILD (PID 17620; spawned PID 32928) | the same, `...partial-60765307cc75.mp4` | the same failure; entry kept; partial there; the bootloader exited too and removed its `_MEI`; no process left | `removed=(...partial-60765307cc75.mp4,)` | journal empty; folder empty: **PASS** |
| onefile | the SPAWNED PID (the bootloader, 41044) | the same, `...partial-3aec56619800.mp4` | the child worker (PID 39048) was still alive 1 s later and FINISHED the export: job `ok=True`, `vfr_corrected.mp4` written, the entry removed; an orphaned `_MEI0000a0542` left in `TEMP` | nothing to remove | `vfr_corrected.mp4` only |

- **Finding for WP6.3 / CP6a (packaging): in the one-file form the PID the parent holds is the
  bootloader, not the worker.** `export_process`'s `process.kill()` (its hung-worker path,
  `KILL_AFTER_CANCEL_S` after a cancel or a result) would end only the bootloader; the Python
  worker runs on to its own end, and the bootloader's `_MEI` extraction is left in `%TEMP%`.
  The first, too-early journal attempt (killed during analysis, before any temporary existed)
  showed the same orphan and leak (`_MEI0000ab1c2`). The one-folder form has no such layer.
  The leaked `_MEI` folders are kept under `work/wp6.1/t3b/onefile/temp/` as evidence.

### #3 measurement (for CHARC's ruling; a guide, not of record, nothing exclusive)

HEIC -> PNG, `force_cpu` on (so the source worker does not load CuPy), three runs per form,
interleaved; `t3b/runs.jsonl` labels `m3-1..3`. "First message" = from `Popen` to the first
protocol line (`progress 0/4 Reading ...`). "Private" = the peak of psutil's
`memory_info().private` over 50 ms samples (the worker process; the one-file tree adds its
bootloader). DLLs = psutil `memory_maps()` of the worker, sampled at the first message and
throughout. The sampling itself costs some time, the same for every form.

| Form | First message, s (median; range) | Private, MiB (median; range) | Qt-family DLLs mapped (at the first message, and at any time) | DLLs mapped |
|---|---|---|---|---|
| onedir `Clearwater.exe --export-worker` | 0.543 (0.528-0.558) | 1,047.8 (1,047.5-1,048.2) | `Qt6Core.dll`, `pyside6.abi3.dll`, `shiboken6.abi3.dll` (3 / 3 runs) | 122-126 |
| onefile `Clearwater.exe --export-worker` | 2.375 (2.340-3.380) | 1,047.9 worker (1,049.3 with the bootloader) | the same three, from `_MEI...\PySide6` (3 / 3) | 125-129 |
| source `python -m clearwater.app.export_worker` | 0.720 (0.717-0.736) | 1,044.0 (1,043.3-1,044.0) | none | 108-112 |

- So #3 is confirmed on the real builds: every frozen worker maps `Qt6Core`, PySide6's and
  shiboken6's runtime libraries before its first message (no `Qt6Gui` / `Qt6Widgets`), which
  the source worker never does. The cost seen here is small: about +4 MiB private and no
  start-up penalty against the source worker (onedir is faster than the source run; onefile's
  extra ~1.8 s is its extraction).
- The first onedir HEIC run after the build took 5.87 s to its first message (a cold file
  cache); later runs 0.5-0.7 s.
- About 1 GiB of private memory in all three forms, the source worker included, is the
  worker's own (not a packaging effect); recorded only.

Depth at turn-3 group-2b-1 end: 296,797 (wp61-cell3, at its yield; read by the dispatcher)

## Turn 3 group 2b-2 (2026-11-04 ~11:00-11:45Z): the pack check, `--verify`, #10, the hand-filled pack -- STOPPED on two findings

Fresh cell (implementer-opus-high, wp61-cell4), dispatch
`clearwater-review-evidence/wp6.1/cell/dispatch-6.md`, worktree head at start `1e043cfc`.
No desktop input was sent. `t2b/gui_check.py` was not run. Nothing was written under the real
`%LOCALAPPDATA%\Clearwater` (checked at the end: the folder does not exist) or the footage
folder. No network access (the pack came from the uv cache, `--offline`). Evidence:
`clearwater-review-evidence/wp6.1/cell/t3c/`.

One unintended start of the frozen executable without `--export-worker` happened in an
EXPERIMENTAL run (finding F-D below). It may have started the GUI branch for up to 10 s; no
Clearwater log or settings file appeared in the redirected tree. I made no further run that
could reach it.

### Rulings applied (CHARC gen 15, on group 2b-1)

1. #3 ACCEPT (i): nothing built. The report text is CHARC's.
2. F-A = DR-125. Recorded only; `app/export_worker.py` was not touched. Every frozen run below
   exits `3221225477` after its result line, which is DR-125.
3. F-B is a point against onefile at CP6a. Recorded only.
4. #10: move-to-front with dedupe, built (item 3).

### Items 1-4: the fix / feature table

Before record: the three owned test modules were run against `fcc88ee1`'s `src` and
`build.py` (`git archive fcc88ee1`, then `PYTHONPATH` and `WP61_BUILD_SCRIPT` pointing at the
copy; `test_gpu_pack.py` now honours `WP61_BUILD_SCRIPT` as `test_tools_package_build.py`
does). Log `t3c/pytest-2-on-fcc88ee1.log`: **39 failed, 87 passed**. Per test, the first
failing line is in `t3c/before-table.txt`. Every planted rejection fails at
`tests/test_gpu_pack.py:428` (`_rejected`: `assert 'loaded' == 'rejected'`, so the old
loader accepted the planted pack).

| Item | What (file) | Tests | On `fcc88ee1` |
|---|---|---|---|
| 1 (a) RECORD rows | `gpu_pack.pack_problems` / `_record_problems` / `_row_problems`: every row of the eleven RECORD files names a regular file that exists with the row's size (`os.stat`, no hashing). A row without a size is existence-only. `parse_record` (CSV) rejects a malformed row (not three fields, empty path, non-integer size) and a row that leaves `site-packages` (absolute, drive, or `..`). | `test_a_listed_file_that_is_missing_is_rejected`, `test_a_listed_file_of_another_size_is_rejected`, `test_a_listed_folder_where_a_file_should_be_is_rejected`, `test_a_row_without_a_size_is_checked_for_existence_only`, `test_a_malformed_or_escaping_record_row_is_rejected[dotdot, absolute, drive, two-fields, bad-size]` | all fail at `:428` (loaded) |
| 1 no hashing | only the RECORD files are read and hashed at start-up | `test_the_cheap_check_hashes_no_listed_file` (`_file_digest` replaced by a raiser; a same-size content change still passes the cheap check) | passes (the old check hashed no listed file either; it pins the property) |
| 1 (b) ownership | a top-level entry of `site-packages` is OWNED when it equals (`os.path.normcase`) the FIRST PATH COMPONENT of some row of the eleven RECORD files; any other entry is `unlisted entry in site-packages: <name>`. Skipped when a RECORD could not be read (that problem is reported first). | `test_an_unlisted_top_level_entry_is_rejected[package (numpy), module, pth, dist-info]`; no false positive: `test_ownership_is_the_first_component_of_any_record_row` (an extra file INSIDE `cupy/` passes; top level only), `test_ownership_ignores_case_where_the_platform_does` | the four planted cases fail at `:428`; the two no-false-positive tests pass |
| 1 (c) platform tag (#7) | `_wheel_tag_problems`: at least one `Tag:` line of each `WHEEL` file must fit `platform_tags()` (`cp312`, `win_amd64` here, from `sys.implementation` / `sysconfig.get_platform()`), by `tag_fits` (python `cp312` / `py3` / `py312`; ABI `none` / `cp312` / `abi3`; platform `any`, the running tag, or on Linux a `manylinux` tag of the same machine, glibc not compared). A missing `WHEEL`, or one with no `Tag:` line, is a rejection. | `test_a_locked_wheel_for_another_platform_is_rejected` (the LINUX locked CuPy wheel, installed whole with a true manifest, on Windows); `test_a_wheel_file_without_a_usable_tag_is_rejected`; `test_tag_fits[13 cases]`; `test_platform_tags_name_the_running_interpreter_and_platform` | fail at `:428`, or `AttributeError` (no `tag_fits` / `platform_tags`) |
| 1 (d) manifest = lock | kept as it was (now the first step of `pack_problems`) | the existing tests, unchanged in what they assert | n/a |
| 1 OSError in the walk | a listed file that cannot be `stat`-ed becomes `<dist> file <path> unreadable: <type>`; a `site-packages` listing failure becomes `pack unreadable: <type>` (via `check_pack`) | `test_an_os_error_during_the_walk_is_a_rejection` (`os.stat` refused for one listed file, then `os.scandir` refused for `site-packages`) | fails at `:428` |
| 1 clean pack | -- | `test_a_clean_pack_passes_the_cheap_and_the_full_check`, `test_a_valid_pack_is_loaded` (synthetic packs now have real RECORD rows, hashes, sizes, WHEEL / METADATA / INSTALLER files) | `AttributeError` (no `pack_problems`) |
| 2 `--verify` | `build.py --verify <pack folder>` = `verify_pack` (`gpu_pack.pack_problems(folder, full=True)`: everything above plus each listed file's sha256 in RECORD's urlsafe-base64 form, and any listed file without a hash, RECORD's own row excepted) + `pack_census`. Exit 0 with one summary line, 1 with each problem listed. A third member of the `--form` / `--write-manifest` exclusive group. README section added. | `test_verify_passes_a_clean_pack_with_one_line`, `test_verify_lists_every_mismatch` (content changed at the same size, size changed, file missing, unlisted top-level entry: 5 lines), `test_verify_also_runs_the_start_up_checks` ((c) and (d)), `test_verify_flags_a_listed_file_without_a_hash`, `test_verify_is_exclusive_with_the_other_actions[--form, --write-manifest]` | all fail (argparse: no `--verify`) |
| 3 #10 | `__main__.prepend_executable_folder`: every spelling of the executable's folder is removed (`normcase(normpath)`), the folder is put first, and the other entries keep their order (empty entries included). No change when the folder is already first and appears once. Only the given environment (`os.environ`) is written. | NEW `test_a_path_listing_the_folder_behind_another_ffmpeg_puts_it_first_once`; 2b-1's `test_a_worker_whose_path_was_changed_by_pyside6_does_not_add_the_folder_again` kept and still green on its no-duplicate check (see the deviation below) | new test `test_frozen_entry.py:319` `assert False is True`; 2b-1's test `:290` the same |

**Deviation (for the dispatcher): 2b-1's membership test had to change its expectation.** Its
worker case asserted that `PATH` stays UNCHANGED when the PySide6 hook has put
`_internal\PySide6;_internal` in front of the folder. Under ruling 4 ("the exe folder is first
on PATH and appears once") that is impossible, because the folder is no longer first. The
test now asserts: the folder is moved back to the front; it appears once; the hook's entries
keep their order; a trailing-separator spelling counts as the folder; and a folder that is
already first is left unchanged. Its name and its scenario are unchanged. Nothing else
depends on the old order: the folder holds only `Clearwater.exe`, `ffmpeg.exe`, `ffprobe.exe`
and `_internal`, and Python 3.8+ resolves extension-module DLLs without `PATH`.

**Design note (b).** "Owned" = the first path component of any RECORD row of the eleven. So
`nvidia` is owned by eight distributions and `cupy` / `cupyx` / `cupy_backends` by one; each
`.dist-info` folder owns itself through its own RECORD row. Nested extra files (a
`__pycache__` inside `cupy/`) are not the cheap check's concern: they cannot shadow a
top-level module.

Self-review (suspected / confirmed / rejected / fixed):

1. The ownership key first used `PureWindowsPath` for the component and `PurePosixPath` for
   the stat path. On Linux a backslash name would be keyed differently: confirmed by reading,
   fixed (both `PurePosixPath`).
2. A version or wheel mismatch no longer stops the walk, so the full check lists all
   problems. The cheap check still returns the first, in the old order: confirmed by the
   unchanged reasons of the existing tests.
3. `test_an_unreadable_record_is_rejected` monkeypatched `gpu_pack.file_sha256`, which the
   RECORD read no longer uses. Confirmed. The test now refuses `Path.read_bytes` / `Path.open`
   for that RECORD. It passes on `fcc88ee1` too, as it should (that code also reported the
   file as unreadable).

A second pass found nothing new.

Commands (worktree root, Git Bash, `PYTEST_ADDOPTS` unset, outputs in `t3c/`):

| Command | Exit | Summary |
|---|---|---|
| `pytest -q -rs -p no:cacheprovider --basetemp=<wt>/work/c61d-1 tests/test_gpu_pack.py tests/test_frozen_entry.py tests/test_tools_package_build.py` | 0 | 126 passed in 9.52 s |
| the same against `fcc88ee1` (`c61d-2`, `PYTHONPATH` + `WP61_BUILD_SCRIPT`) | 1 | 39 failed, 87 passed (the before record) |
| `pytest ... --basetemp=<wt>/work/c61d-3 <the three> tests/test_jobs_export_process.py tests/test_app_composition.py tests/test_wp42_composition.py tests/test_core_backend.py -m "not gpu" --durations=5` | 0 | 277 passed, 41 deselected in 30.54 s (slowest 2.34 s, `test_jobs_export_process`) |
| `ruff check .` / `ruff format --check .` | 0 / 0 | All checks passed / 322 files already formatted |
| `mypy` (strict, configured set) | 0 | no issues in 160 source files |
| `mypy --platform darwin tools/package/build.py src/clearwater/gpu_pack.py src/clearwater/__main__.py` | 0 | no issues in 3 source files |
| `mypy --strict` on the three test modules, win32 and `--platform darwin` | 0 / 0 | no issues in 3 source files |

Commits: `7af84366` feat(wp6.1): cheap GPU pack check at every start-up (RECORD sizes,
ownership, platform tags); build.py --verify; `472b0b6e` fix(wp6.1): the executable folder
first on PATH and once (move-to-front with dedupe). 0 CR in every blob.

### Item 5: the rebuilds (from `472b0b6e`)

| # | Command (worktree root) | `df -h /c` before | Exit | Wall (shell / PyInstaller) | Result |
|---|---|---|---|---|---|
| 7 | `uv run --no-sync python tools/package/build.py --form onedir --with-ffmpeg > work/wp6.1/build-onedir-t3c.log 2>&1` | 86 GB free (11:07Z) | 0 | 88 s / 79.1 s | `_internal` 225 MB (du) + `Clearwater.exe` 10.1 MiB; 668.2 MiB release with FFmpeg; bundle checks 7.3 s: **PASS** |
| 8 | `... --form onefile --with-ffmpeg > work/wp6.1/build-onefile-t3c.log 2>&1` | 86 GB free | 0 | 84 s / 82.0 s | `Clearwater.exe` 93,764,460 B (89.4 MiB); 523.8 MiB release; bundle checks 0.7 s: **PASS** |

Both logs have the same single warning as every earlier build (`scipy.special._cdflib`,
benign). FFmpeg copies: `ffmpeg version 9.0.2-full_build-www.gyan.dev` and `ffprobe version
9.0.2-full_build-www.gyan.dev`. Copies of the logs are in `t3c/`.

### Item 6: the hand-filled GPU pack (redirected `LOCALAPPDATA`)

- **Root.** `LOCALAPPDATA` = `<wt>\work\wp6.1\t3c\appdata\Local` (with `APPDATA` = `...\Roaming`,
  `TEMP` / `TMP` = `...\Temp` beside it). Pack folder =
  `<LOCALAPPDATA>\Clearwater\gpu-pack\14.2.0-cu12\` (`gpu_pack.pack_root()` + `STAMP`).
  `df -h /c` before filling: 86 GB free (11:11Z).
- **Fill** (`t3c/fill.log`, exit 0, 14 s, all from the uv cache):
  `uv pip install --python <wt>\.venv\Scripts\python.exe --target <pack>\site-packages
  --offline --no-deps --link-mode copy` of `cupy-cuda12x==14.2.0 cuda-pathfinder==1.8.3
  cuda-toolkit==12.9.2.0 nvidia-cublas-cu12==12.9.2.10 nvidia-cuda-nvrtc-cu12==12.9.86
  nvidia-cuda-runtime-cu12==12.9.79 nvidia-cufft-cu12==11.4.1.4 nvidia-curand-cu12==10.3.10.19
  nvidia-cusolver-cu12==11.7.5.82 nvidia-cusparse-cu12==12.5.10.65
  nvidia-nvjitlink-cu12==12.9.86`. "Resolved 11 packages ... Installed 11 packages."
  `--link-mode copy` was used so that a planted change cannot reach the uv cache through a
  hard link.
- **Manifest:** `build.py --write-manifest <pack>`, exit 0. A copy is at `t3c/manifest.json`
  (sha256 `6f7ee900...b536bd`, equal to the pack's).
- **`--verify`, first run: FAIL** (`t3c/verify-1-with-uv-lock.log`, 26 s, cold file cache):
  `unlisted entry in site-packages: .lock`.
- **FINDING F-C (packaging, for WP6.3 and the README).** `uv pip install --target` leaves an
  EMPTY `.lock` file (uv's own install lock, 0 B) at the top of `site-packages`. No RECORD
  owns it, so ruling 2's ownership check rejects it, as specified. I deleted that 0-byte
  file from my own fill (looked at first) and added a README step. The WP6.3 downloader
  must leave no such file, or CHARC may rule an allowlist.
- **`--verify` after that** (`t3c/verify-2.log`, exit 0, 4 s warm):
  `verify ...\14.2.0-cu12: PASS (11 distributions; 2701 RECORD rows, each file's sha256 and
  size; 2701 files, 2412.6 MiB)`. **The pack: 2,701 files, 2,529,777,432 B (2,412.6 MiB) in
  `site-packages`, plus `manifest.json`.** The RECORD rows equal the files on disk, so no
  unlisted nested file exists.
- After all the runs below, `--verify` again PASSES with the same figures
  (`t3c/verify-3-after-cases.log`). **No run wrote into the pack:** every record shows 0 files
  added and 0 removed (CuPy's partial import wrote no bytecode there).

### Item 7: the proof, headless -- STOPPED at "WITH the pack"

Tools: `t3c/proof.py` (2b-1's `t3b/headless.py` helpers; the worker spawned as
`export_process.py` spawns it) and `t3c/loader_probe.py` (the product's
`gpu_pack.check_pack` / `gpu_pack.load` from the dev environment). The child environment is
the redirected tree plus `CUPY_CACHE_DIR = appdata\cupy-kernel-cache` (empty, so CuPy must
compile with the pack's NVRTC; the product default would be `%USERPROFILE%\.cupy\kernel_cache`,
a write outside `%LOCALAPPDATA%` for WP6.3 to note). Every `CUDA_PATH*` variable is removed,
`PATH = C:\Windows\System32;C:\Windows`, and the working directory is
`work\wp6.1\t3c\runs\<form>`. Requests: `heic-ad24-both.heic` -> PNG and `vfr.mp4` -> MP4, c3
defaults, `force_cpu` off, encoder `auto`. Every record is in `t3c/proof.jsonl`.

**The loader's line.** The frozen WORKER logs no pack line (D3: no handler yet, and INFO is
below the last-resort handler). Only the frozen GUI branch writes it, to its log file, so
**the frozen loader line verbatim moves to group 2c.** Headless, the line comes from the
product function on the same folder (`loader_probe.py`), and the frozen worker's device text
shows which way its own loader went: an accepted pack gives `CuPy failed to load` (CuPy was
importable); an absent or rejected pack gives `CuPy not installed`.

| Form | Case | Loader line (product function, same folder) | Exit | Device (worker result) | Output | CUDA DLLs mapped | Left over |
|---|---|---|---|---|---|---|---|
| onedir | with, video | `gpu pack 14.2.0-cu12: loaded` | 3221225477 (DR-125) | `CPU: CuPy failed to load` (log: `ModuleNotFoundError: No module named 'ctypes.wintypes'`) | `vfr_corrected.mp4` 55,166 B, ok | none | none; no `_MEI` |
| onedir | with, heic | the same | 3221225477 | the same | `heic-ad24-both_corrected.png` 37,105 B, ok | none | none |
| onefile | with, video | the same | 3221225477 | the same (`ctypes.wintypes`) | 55,166 B, ok | none | none; `_MEI` before [] after [] |
| onefile | with, heic | the same | 3221225477 | the same | 37,105 B, ok | none | none; no `_MEI` |
| onedir | without (folder renamed `14.2.0-cu12.renamed`) | `gpu pack 14.2.0-cu12: absent` | 3221225477 | **`CPU: CuPy not installed`**; log `CuPy not installed: No module named 'cupy'`; warning `Processed on the CPU (CPU: CuPy not installed).` (AD-9's text, in the worker's result) | 37,104 B, ok | none | none |
| onefile | without | the same | 3221225477 | the same | 37,104 B, ok | none | none; no `_MEI` |
| onedir | broken (a): one byte appended to `cupy/__init__.py` | `gpu pack 14.2.0-cu12: rejected: cupy-cuda12x file cupy/__init__.py size 42867, RECORD says 42866` | 3221225477 | `CPU: CuPy not installed` (rejected) | 37,104 B, ok | none | none |
| onefile | broken (a) | the same | 3221225477 | the same | 37,104 B, ok | none | none; no `_MEI` |
| onedir | broken (b): an empty `site-packages/numpy/__init__.py` | `gpu pack 14.2.0-cu12: rejected: unlisted entry in site-packages: numpy` | 3221225477 | `CPU: CuPy not installed` | 37,104 B, ok | none | none |
| onefile | broken (b) | the same | 3221225477 | the same | 37,104 B, ok | none | none; no `_MEI` |
| onedir | broken (c): cupy's `WHEEL` `Tag:` set to `cp312-cp312-manylinux2014_x86_64` | `gpu pack 14.2.0-cu12: rejected: cupy-cuda12x wheel tag cp312-cp312-manylinux2014_x86_64 is not for win_amd64` | 3221225477 | `CPU: CuPy not installed` | 37,104 B, ok | none | none |
| onefile | broken (c) | the same | 3221225477 | the same | 37,104 B, ok | none | none; no `_MEI` |

The broken cases ran on a COPY of the pack (`cp -r`) placed at the stamp path, with the
original renamed beside it. Each case was planted, run on both forms, and reverted (`cmp`
against the original). The copy was then deleted and the original renamed back. After every
run: no process of the run's tree alive (psutil, by PID); `tasklist` shows no `Clearwater.exe`
and no `ffmpeg.exe` (one record shows another session's `ffmpeg.exe`, PID 47016, not in the
run's tree); `TEMP\_MEI*` empty before and after every onefile run.

**FINDING F-C2 (packaging, blocks "WITH the pack"): the bundle lacks stdlib modules that only
the pack imports.** PyInstaller collects the stdlib modules its analysis sees. CuPy and
`cuda.pathfinder` live outside the bundle, so what they alone import is missing:

- `ctypes.wintypes` (`cuda/pathfinder/_dynamic_libs/load_dl_windows.py:7`);
- `graphlib`, imported by a CuPy extension module (no pack `.py` names it).

Measure, `t3c/import_gap.py` -> `t3c/import-gap.json`: the SOURCE worker, with
`-X importtime` and the venv's CuPy 14.2.0, ran one GPU HEIC and one GPU video request
(device `GPU` both). Its imported set was diffed against the onedir bundle's PYZ,
`base_library.zip`, the `.pyd` files and the builtins:

- 948 modules imported, 279 of them the pack's own.
- The real gap is `ctypes.wintypes` and `graphlib`.
- The rest of the diff is not a gap: failed optional imports (`posix`, `fcntl`,
  `charset_normalizer`, `cython`, `ml_dtypes`, ...), venv start-up modules (`site`,
  `_virtualenv`, `sitecustomize`), and `struct` (a PyInstaller CArchive module, not in the
  PYZ).

**EXPERIMENT (evidence only; the committed `build.py` is unchanged).** `t3c/build_exp.py`
loads `build.py`, appends `--hidden-import` arguments, and runs its `build()` into
`work/wp6.1/t3c/exp/`. Bundle checks PASS, 668.2 MiB release.

- **Build 1, `ctypes.wintypes` only** (`t3c/build-exp-onedir-1.log`). Onedir video: CuPy got
  further, then failed with `ModuleNotFoundError: No module named 'graphlib'`. CuPy's
  import-failure report resolved each DLL dependency, and 27 CUDA / CuPy files were mapped,
  all under the pack or the driver, 0 elsewhere:
  - 8 NVIDIA-wheel DLLs from the pack's `nvidia/*/bin`: `cublas64_12`, `cublasLt64_12`,
    `nvrtc64_120_0`, `cufft64_11`, `curand64_10`, `cusolver64_11`, `cusparse64_12`,
    `nvJitLink_120_0`. This is D2's `os.add_dll_directory` at work: no `CUDA_PATH`, no
    toolkit `bin`.
  - 18 CuPy `.pyd` files from the pack.
  - `C:\Windows\System32\nvcuda.dll`.

  The report also named `cuTENSOR.dll` / `cuTENSORMg.dll` as not found (not in the lock;
  optional).
- **Build 2, both modules** (`t3c/build-exp-onedir.log`). Onedir video: CuPy imports. 62
  files were mapped, 0 elsewhere:
  - 54 CuPy / cupyx `.pyd` files from the pack;
  - 8 driver files: `System32\nvcuda.dll` and
    `DriverStore\FileRepository\nvami.inf_amd64_...\{nvcuda64, nvapi64, nvapi64_impl,
    nvdiagclt64, nvdxgdmal64, nvobjectloader64, NvMessageBus}.dll`;
  - NO NVIDIA-wheel DLL: the failure below came before `cuda.pathfinder` loaded one.

  The device test then failed: log `a test kernel failed on the CUDA device: Canary probe
  child process timed out after 10.0 seconds.`, device **`CPU: CUDA device unusable`**,
  export ok on the CPU.

**FINDING F-D (packaging; a STOP, and the unintended start).**
`cuda/pathfinder/_dynamic_libs/subprocess_protocol.py:42` builds its canary probe as
`[sys.executable, "-m", <pathfinder probe module>, mode, libname]` and runs it with
`subprocess.run(..., timeout=10)` (`load_nvidia_dynamic_lib.py:107-116`). In a frozen build
`sys.executable` is `Clearwater.exe`. `__main__.main` sends every first argument other than
`--export-worker` to the GUI branch (`src/clearwater/__main__.py`, `main`). So the probe
started the frozen GUI branch, which never answered, and pathfinder killed it at 10 s.

- No Clearwater log folder and no settings file appeared in the redirected `LOCALAPPDATA` /
  `APPDATA`. That suggests the branch had not reached `_start_logging` when it was killed,
  but a window cannot be ruled out.
- No input was sent. No `Clearwater.exe` was left (`tasklist`).
- I made NO further WITH-pack run on the experimental build, and none on the onefile form.

This is the same class as Q5: a library inside the pack re-enters the interpreter through
`sys.executable -m`. Options for CHARC, for the record (not chosen; no change made):

- (i) `__main__` handles `-m <module> [args]` in a frozen build: `runpy.run_module` with
  `alter_sys=True`, after the pack loader, Qt-free. The frozen executable then acts as an
  interpreter for `-m`, as CPython does for the canary.
- (ii) Make the canary unnecessary: pathfinder's earlier search steps must find the libraries
  first. Its site-packages step reads `site.getsitepackages()`, not `sys.path`, so this
  needs pathfinder's own configuration, which is fragile.
- (iii) A frozen executable refuses unknown arguments (exit non-zero, no GUI). That is safe,
  but the canary then fails and the GPU path stays off.

Whichever is chosen, the GUI branch should never start for an unknown first argument (a
`-m` / `-c` re-entry).

**What item 7 needs from CHARC before it can finish:**

- (1) how the bundle carries the pack's stdlib needs (F-C2): the two observed modules as
  hidden imports in `build.py`; the whole stdlib; or the observed set plus an AST-derived
  set from the pack's `.py` files;
- (2) the F-D mechanism.

Then: the WITH-pack GPU export (video and HEIC), both forms, with every CUDA DLL path; the
experimental build's DLL list above is the expected shape. Owed to group 2c (GUI only): the
frozen loader's log line verbatim.

### Item 8: the cheap check's start-up cost (a guide, not of record; the host was shared with WP-T8)

| Measure | Runs | Median | Range |
|---|---|---|---|
| `gpu_pack.check_pack(<pack>)` alone, the dev environment, a fresh process each (`t3c/cost-check.jsonl`); 2,701 rows stat-ed, 11 RECORD files hashed | 5 | **0.066 s** | 0.058-0.072 s |
| onedir worker, `Popen` -> first protocol message, WITH the pack (the loader accepts; CuPy's import fails later, after the first message) | 3 | 0.605 s | 0.596-0.646 s |
| onedir worker, the same, WITHOUT (folder renamed) | 3 | 0.590 s | 0.529-0.593 s |
| onefile worker, WITH | 3 | 2.483 s | 2.455-2.505 s |
| onefile worker, WITHOUT | 3 | 2.418 s | 2.338-2.809 s |

Runs interleaved with / without per form (`t3c/cost-frozen.txt`, `proof.jsonl` labels
`cost-*`). The frozen difference (+0.015 s onedir, +0.065 s onefile) is within the spread and
agrees with the 0.066 s check alone. The first `--verify` (full hashing, cold) took 26 s,
warm 4 s: that cost belongs to install time, not start-up.

### Files changed this group

`src/clearwater/gpu_pack.py`, `src/clearwater/__main__.py`, `tools/package/build.py`,
`tools/package/README.md`, `tests/test_gpu_pack.py`, `tests/test_frozen_entry.py`,
`docs/proofs/wp6.1-ledger.md`. Evidence tools (not product, not committed):
`t3c/proof.py`, `t3c/loader_probe.py`, `t3c/import_gap.py`, `t3c/build_exp.py`. The pack,
both builds and the experimental onedir build stay under `work/wp6.1/` (pack 2.4 GB at
`work/wp6.1/t3c/appdata/Local/Clearwater/gpu-pack/14.2.0-cu12`, kept for item 7's resumption).

Depth at turn-3 group-2b-2 end: 300,127 (wp61-cell4, at its yield; read by the dispatcher)

## Turn 3 group 2b-3 (2026-11-04 ~11:50Z-): F-C2 hidden imports, the F-D `-m` handler; the with-pack GPU proof

Fresh cell (implementer-opus-high, wp61-cell5), dispatch
`clearwater-review-evidence/wp6.1/cell/dispatch-7.md`, head at start `97eff4e6`. Evidence:
`clearwater-review-evidence/wp6.1/cell/t3d/`. No desktop input was sent. `t2b/gui_check.py` and
the `t3c/exp/` builds were not run (the exp build was only READ, by the bundle check).

### INCIDENT (this cell): a before-record test started the real GUI branch

- **What happened (11:55:31Z).** I ran the new `tests/test_frozen_entry.py` against
  `97eff4e6`'s `src` (`git archive` to `work/wp6.1/t3d-base`, `PYTHONPATH`). One new test,
  `test_the_real_pathfinder_canary_module_runs_through_the_frozen_dash_m`, starts a fresh
  `python -I -c` child with `sys.frozen` faked and calls
  `entry.main(["Clearwater.exe", "-m", <pathfinder probe>, ...])`.
- **Why it reached the GUI.** On `97eff4e6` that argument list goes to the GUI branch. The child
  ran the real `_start_logging` and then the real `clearwater.app.main` with the owner's real
  app-data variables. The test's 120 s subprocess timeout killed it.
- **Consequences.**
  - A window was possible for up to 120 s.
  - One line was appended to the owner's `%APPDATA%\Clearwater\logs\clearwater.log`:
    `2026-11-04T01:55:31.566-10:00 INFO clearwater.app.startup device: GPU`. The file is now
    479 B, md5 `69ed0432...`. It was left untouched on the dispatcher's word.
  - `settings.json` and `presets/` are unchanged. `%LOCALAPPDATA%\Clearwater` is absent.
  - No process was left.
- **Logs.** `t3d/pytest-2-on-97eff4e6-INCIDENT.log`, `applog-after-incident.txt`,
  `applog-tail.txt`.
- **Cause.** The test was safe on the new code, but not on the old revision it was run
  against.
- **Fix** (`584d711d`, then `e27fa134` under the dispatcher's two new rules):
  - every test that calls an entry point redirects APPDATA, LOCALAPPDATA and XDG_* under
    `tmp_path`;
  - it blocks or stubs the GUI BEFORE it runs, on any revision;
  - before any before-record run, the test file is grepped for entry-point calls.
- **What each test does now.**
  - The pathfinder child blocks PySide6 and shiboken6 and stubs `clearwater.app.main`.
  - The worker-import child blocks `clearwater.app.main` and `clearwater.gui`.
  - The `calls`, `pack` and absent-pack tests redirect the variables and stub the log set-up.
- **Checks since.** Every later run, the before-records included: the owner's log md5 is
  unchanged, and `%LOCALAPPDATA%\Clearwater` is absent.
- **Two other slips (mine).**
  - An empty heredoc started a stray `python3` REPL (PID 46648, its own command line). I killed
    it by PID with `taskkill /PID 46648 /T /F`.
  - One command carried a bare `cd`. A subagent's shell cwd resets per call.

### Rulings applied (CHARC gen 15, on group 2b-2)

1. F-C2 (iii) with (a) and (b): built (item 1).
2. F-D (i), frozen only and narrowed: built (item 2). The attached and combined forms
   (`-mfoo`, `-cCODE`, `-I -m x`, `-Im x`) still go to the GUI, per the literal text. The
   question is with CHARC through the dispatcher.
3. F-C: no allowlist.
4. The 2b-1 deviation is concurred.
5. Noted: the frozen loader line is moved to 2c; the CuPy kernel cache goes to WP6.3; 3221225477
   = DR-125; the report's limits get the incident line.

### Items 1-2: the table

"On `97eff4e6`" = the same test files with `PYTHONPATH` / `WP61_BUILD_SCRIPT` on the
`git archive 97eff4e6` copy (`t3d/pytest-8.log`): **31 failed, 44 passed**.

| Item | What (file) | Tests | On `97eff4e6` |
|---|---|---|---|
| 2 F-D | `__main__.run_interpreter_option`, frozen only, when `argv[1]` is exactly `-m` or `-c`. `-c` is refused before the loader. For `-m`: `prepend_executable_folder()`, `gpu_pack.activate()`, then the check, then `runpy.run_module(module, run_name="__main__", alter_sys=True)` with `sys.argv = [<file>, *args]`. A refusal is `Clearwater: <reason>`, one stderr line (skipped when the windowed process has no stderr), exit 2, no GUI. An exception from the module prints its traceback and gives status 1, so a windowed build shows no traceback dialog. `SystemExit` passes through. Qt-free (only `runpy` / `traceback` are imported on the branch). | `test_a_frozen_dash_m_runs_a_pack_module_after_the_loader_without_qt` (planted pack module; `__name__ == "__main__"`, argv, file, loader first, no Qt via the import blocker); `..._of_anything_else_and_dash_c_refuse_with_one_line[9]` (`http.server`, `json.tool`, `clearwater`, a missing name, `.relative`, `-m` alone, `-m ""`, `-c print(1)`, `-c` alone); `..._refuses_when_no_pack_is_loaded[absent, rejected]`; `test_a_pack_modules_exit_passes_and_its_exception_is_printed_not_raised[2]`; `test_the_real_pathfinder_canary_module_runs_through_the_frozen_dash_m` (the real `cuda.pathfinder._dynamic_libs.dynamic_lib_subprocess canary nvrtc` from the venv's site-packages as the "pack", fresh `-I` child: JSON payload printed, status 0, no PySide6) | `test_frozen_entry.py:547` / `:581` `assert 3 == 2` (the GUI stand-in ran); `:659` `assert 3 == 5` / `3 == 1`; `:745` `'status 9 qt -'` (the GUI stand-in, safely); `:48` the GUI import blocked |
| 2 resolution | `gpu_pack.module_from_pack(module, site_packages)`: `importlib.util.find_spec(<top-level name>)` on the LIVE `sys.path` and hooks (after activation the pack is `sys.path[0]`). EVERY location (the `origin` when `has_location`, plus each `submodule_search_locations` portion) must lie under `site_packages`, compared with `realpath` and `normcase` (`os.path.commonpath`). A built-in, frozen, unresolvable, empty, relative or non-identifier name is not from the pack. Finding a top-level spec runs none of its code. | `test_a_name_in_the_bundle_and_the_pack_is_judged_by_the_first_on_sys_path` (bundle first: refused; pack first: accepted, and the pack copy runs); `test_a_namespace_package_is_from_the_pack_only_when_every_portion_is` (`cuda` is a namespace package in the pack); `test_built_in_stdlib_and_bundle_modules_are_not_from_the_pack` | `:600`, `:624`, `:636` `AttributeError` (no `module_from_pack`) |
| 2 source run | no new branch when not frozen | `test_a_source_run_sends_dash_m_and_dash_c_to_the_gui_as_before[3]` | PASSES (by design: it pins the 1.0.0 behaviour; it would catch a dropped `sys.frozen` guard) |
| 1 F-C2 scan | `build.scan_stdlib_imports` / `import_candidates` / `_resolve` / `stdlib_kind` / `stdlib_search_path`. `ast` over each `.py` file that `pack_sources()` lists: the RECORD of the eleven `LOCKED_DISTRIBUTIONS`, from the build venv via `importlib.metadata`. An import anywhere counts, including conditional / `try` / function-level ones and `from __future__` (a real `IMPORT_NAME` at run time). A literal `importlib.import_module("x")` or `__import__("x")` counts. Skipped: relative imports, third-party names (a top level not in `sys.stdlib_module_names`), non-literal dynamic imports. `from a import b` adds `a.b` only when `a` is a package with a submodule `b`. `import os.path` gives `os`. Existence is decided WITHOUT importing: built-ins, then `PathFinder` over the stdlib folders. A name absent on this platform goes to `unavailable` (recorded, not imported). | `test_the_scan_of_a_fixture_package_returns_exactly_its_stdlib_imports` (an exact set of 15, plus `winreg` here / `fcntl` unavailable); `test_a_file_that_cannot_be_parsed_is_reported`; `test_the_real_pack_scan_finds_ctypes_wintypes` | `:581`-`:613` `AttributeError` |
| 1 set + report (a) | `hidden_imports(scan, committed=PACK_EXTENSION_STDLIB_NEEDS)`: sorted `HiddenImport(name, sources, named_by, named)`, each marked `committed` and / or `scan`. `build()` writes `work/wp6.1/hidden-imports-<form>.json` (with the unavailable and unparsable lists) and one log line per member, and passes each member as `--hidden-import`. An unparsable pack file fails the build BEFORE PyInstaller. | `test_the_hidden_import_set_marks_each_member_by_its_source`; `test_the_committed_list_is_graphlib`; `test_every_hidden_import_is_passed_to_pyinstaller`; `test_an_unparsable_pack_file_fails_the_build_before_pyinstaller` | `:619` `TypeError` (no `hidden=`), the rest `AttributeError` |
| 1 bundle check (b) | `bundled_modules(exe)` looks in the PYZ, the CArchive module entries (`struct`), `base_library.zip` (an `_internal/` file in onedir, a CArchive entry in onefile), the extension modules (`.pyd` / `.so` under `_internal/` and `lib-dynload/`, or CArchive binaries) and `sys.builtin_module_names`. `missing_hidden_imports` lists `hidden-import missing from the bundle: <name> (<sources>)`. `build()` then returns 1: a FAILURE, never a warning. | `test_a_planted_removal_from_the_committed_list_fails_the_bundle_check_by_name` (a build from the list WITHOUT `graphlib`: its args lack it, and its real CArchive + PYZ fails BY NAME, `graphlib (committed)`; with it, `[]`); `test_the_bundle_check_looks_in_every_place_pyinstaller_puts_a_module`; `test_a_missing_member_fails_the_build_and_the_set_is_written_to_the_report[pass, fail]` (`build()` end to end with PyInstaller replaced) | `AttributeError` / `TypeError` |

- The two existing build tests (`_stopping_build`, `:318`) now stub `pack_sources`. On
  `97eff4e6` they fail at that `setattr` only (no `pack_sources` there). That is a helper
  change, not a behaviour change.
- **`ctypes.wintypes` comes from the SCAN**, named 3 times:
  `cuda-pathfinder:cuda/pathfinder/_dynamic_libs/load_dl_windows.py:7`,
  `cuda/pathfinder/_utils/windows_arch.py:58` and
  `cupy-cuda12x:cupy/_environment.py:735`. Only `graphlib` is on the committed list.

### The resolved hidden-import set (the scan over this venv's eleven distributions)

The scan covers 376 `.py` files in 2.5 s. Nothing was unparsable and nothing was unavailable
here. There are **61 members**: 60 from the scan and `graphlib` from the committed list.

`__future__ abc argparse ast atexit binascii cmath collections collections.abc contextlib
contextvars copy ctypes ctypes.util ctypes.wintypes dataclasses enum functools glob
graphlib[committed] hashlib importlib importlib.metadata importlib.util inspect io itertools
json linecache math multiprocessing ntpath numbers operator os pathlib platform random re
shlex shutil site socket string struct subprocess sys sysconfig tempfile textwrap threading
time traceback types typing unittest unittest.mock urllib.request warnings weakref winreg`

**The check run READ-ONLY on the existing builds** (`t3d/scan-probe-on-2b2-builds.txt`):

- The 2b-2 onedir and onefile builds each lack 5:
  - `ctypes.util` (`load_dl_linux.py:8`);
  - `ctypes.wintypes`;
  - `graphlib (committed)`;
  - `site` (`cuda/pathfinder/_utils/find_sub_dirs.py:6`, a module-level import);
  - `unittest.mock` (`cupy/testing`).
- The `t3c/exp/` onedir build (2b-2's experiment) lacks 3: `ctypes.util`, `site` and
  `unittest.mock`.
- So the check distinguishes, on real artifacts.
- **Note on `site`.** 2b-2's import-gap measurement set `site` aside as a venv start-up
  module. The scan shows that `cuda-pathfinder` imports it at module level, and the frozen
  bundle does not hold it. With `--hidden-import site` it is bundled (frozen
  `sys.flags.no_site` stops it running `site.main()` on import). The with-pack proof shows
  whether that path is reached.

### Item 3: tests and static checks (worktree root, Git Bash, `PYTEST_ADDOPTS` unset; logs in `t3d/`)

| Command | Exit | Summary |
|---|---|---|
| `pytest -q -rs -p no:cacheprovider --durations=5 --basetemp=<wt>/work/c61e-7 tests/test_gpu_pack.py tests/test_frozen_entry.py tests/test_tools_package_build.py tests/test_jobs_export_process.py tests/test_app_composition.py tests/test_wp42_composition.py tests/test_core_backend.py -m "not gpu"` | 0 | **309 passed, 41 deselected in 39.49 s** (slowest 2.38 s, `test_jobs_export_process`) |
| the two touched test modules against `97eff4e6` (`c61e-8`) | 1 | 31 failed, 44 passed (the before record) |
| `ruff check .` / `ruff format --check .` | 0 / 0 | All checks passed / 322 files already formatted |
| `mypy` (strict, configured set) | 0 | no issues in 160 source files |
| `mypy --strict` on the 5 touched files, win32 and `--platform darwin` | 0 / 0 | no issues in 5 source files |

Self-review (suspected / confirmed / fixed):

1. CArchive module entries (`struct`) were not counted as bundled. This was confirmed by the
   first read-only check, which listed `struct` as missing. Fixed.
2. A `@dataclass` in `build.py` breaks loading by path (`sys.modules` lookup) in the tests.
   Confirmed. Fixed with a `NamedTuple` and a plain class.

A second pass found nothing new.

Commits:

- `584d711d` feat(wp6.1): frozen -m runs a GPU pack module only; -c and every other -m
  refused (F-D);
- `4409077f` feat(wp6.1): bundle the GPU pack's stdlib needs as hidden imports; fail the build
  when one is missing (F-C2);
- `e27fa134` test(wp6.1): every entry-point test redirects app data and blocks the GUI on any
  revision.

0 CR in every blob.

### CHARC's rulings at the first mid-build yield (gen 15, 12:06Z), applied

- **(A)** The entry-point isolation rule is now in CLAUDE.md (main `9b25535d`). Every
  entry-point test in `tests/test_frozen_entry.py` was checked against it before the
  before-record on `584d711d`: `t3d/rule-check.txt` (an AST listing; 19 of 19 OK). Every
  pytest run since uses `--timeout 120`, and its children use 60 / 120 s.
- **(B)** F-D is WIDENED (`fd330049`, `src/clearwater/__main__.py`).
  - `interpreter_reentry(arguments)` applies only when frozen. It skips any `-I -E -s -S -B
    -u -O -q`, and `-X` / `-W` with their value. The next argument must fullmatch
    `REENTRY_ARGUMENT` = `-([BdEhiIOPqsSuvVWxX]*)([mc])(.*)`.
  - The flags are dropped, and the result is `["-m" | "-c", <attached operand, if any>,
    *rest]`. `run_interpreter_option` then applies the 584d711d rule unchanged.
  - Anything else goes to the GUI as before: `-I` alone, `-X utf8` alone, `-platform ...`,
    `-style ...`, `-reverse`, `-widgetcount`, a file. A re-entry is recognised only from the
    first argument onwards, so `photo.heic -m x` goes to the GUI.
  - **Collateral (named for the report):** `-qmljsdebugger=...` matches the grammar (`-q`
    then `-m`) and is refused (`-m 'ljsdebugger=...': not a GPU pack module`). Clearwater has
    no QML.
- **(C)** The resolution rule is concurred.

| Tests (`tests/test_frozen_entry.py`, all under rule (A)) | On `584d711d` (`t3d/pytest-11.log`: 35 failed, 52 passed) |
|---|---|
| `test_interpreter_reentry_follows_cpythons_grammar[22]`: the normalisation table, re-entries and non-re-entries | all 22 FAIL, `:786` `AttributeError` (no `interpreter_reentry`) |
| `test_every_spelling_of_dash_m_runs_a_pack_module[5]`: `-mfoo`, `-I -m`, `-Im`, `-X utf8 -m`, `-I -W ignore -sm`; the planted module runs as `__main__`, no Qt | all 5 FAIL, `:48`: the old code went to the GUI branch, and the test's import blocker refused `clearwater.app.main` (no window) |
| `test_every_spelling_of_dash_c_and_of_a_foreign_dash_m_refuses[8]`: `-cCODE`, `-I -c CODE`, `-Ic CODE`, `-mhttp.server`, `-I -m http.server`, `-X utf8 -m json.tool`, `-qmljsdebugger=port:1234`, `-I -m` | all 8 FAIL, `:840` `assert 3 == 2` (the GUI stand-in ran) |
| `test_qt_options_and_non_reentries_reach_the_gui_as_before_when_frozen[7]` | PASS (by design: they pin the unchanged GUI path) |
| `test_a_source_run_sends_every_spelling_to_the_gui_as_before[7]` | PASS (by design: the source run is 1.0.0) |
| the existing `-m` tests, separate `-m` included (the pathfinder canary test) | PASS on both |

Runs under the host note (WP-T8's serial leg active), focused modules only:

| Command | Exit | Summary |
|---|---|---|
| `pytest -q -rs -p no:cacheprovider --timeout 120 --basetemp=<wt>/work/c61e-12 tests/test_gpu_pack.py tests/test_frozen_entry.py tests/test_tools_package_build.py` | 0 | **207 passed in 10.96 s** |
| `tests/test_frozen_entry.py` against `584d711d` (`c61e-11`) | 1 | 35 failed, 52 passed |
| `ruff check .` / `ruff format --check` (touched) / `mypy` / `mypy --strict --platform darwin` (touched) | 0 | clean (`mypy`: 160 files) |

The owner's log md5 is `69ed0432...` before and after. `%LOCALAPPDATA%\Clearwater` is absent.

**DEFERRED to the dispatcher's word (host note):** item 3's WIDER run, the c61e-7 set on the
final head (`test_jobs_export_process`, `test_app_composition`, `test_wp42_composition`,
`test_core_backend -m "not gpu"`). It last ran green on `e27fa134`, before the widening
(309 passed).


MID-BUILD YIELD here. The builds and the with-pack proof (items 4-5) follow on the
dispatcher's word.
