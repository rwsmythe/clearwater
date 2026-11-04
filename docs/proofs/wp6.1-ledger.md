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


MID-BUILD YIELDS here (twice: after F-C2 / F-D, and after the widening). The dispatcher then
ended this cell's scope at the code (depth 270,675 at the second yield, past the evaluation
point). The builds and the with-pack proof (items 4-5) go to a fresh cell: see the handoff below.

**Before-record of the widening against `1c61bc37`**, as the dispatcher asked (`t3d/c61e-13.log`):
- `src` there is byte-identical to `584d711d` (`git diff --stat 584d711d 1c61bc37 -- src` is
  empty).
- The rule check was re-run first: 19 of 19 OK.
- Result: **35 failed, 52 passed**, the same lines as above (`:786` x22, `:48` x5, `:840` x8).
- The focused run on the final code (`c61e-14`): **87 passed in 4.00 s**.
- The static checks on the two touched files are clean: ruff check, ruff format, `mypy
  --strict`, and `mypy --strict --platform darwin`.
- The owner's log md5 is unchanged, and `%LOCALAPPDATA%\Clearwater` is absent.

### Handoff to item 4 (for the fresh cell; wp61-cell5 retires at the code end by the depth rule)

State: head `9e87f85d` + this ledger commit. The product code for F-C2 and F-D (with its
widening) is complete. Nothing is built from it yet. The existing builds under
`work/wp6.1/dist-*` predate it and lack the handler, as do the `t3c/exp/` builds. NEVER run any
of them with the pack present.

1. **Item 3's wider run** (deferred under the host note; on the dispatcher's word):
   - Run `pytest -q -rs -p no:cacheprovider --timeout 120 --basetemp=<wt>/work/<n>` over
     `tests/test_gpu_pack.py`, `tests/test_frozen_entry.py`, `tests/test_tools_package_build.py`,
     `tests/test_jobs_export_process.py`, `tests/test_app_composition.py`,
     `tests/test_wp42_composition.py` and `tests/test_core_backend.py`, with `-m "not gpu"`.
   - Expect about 350 tests in about 40 s.
2. **Builds**, from the worktree root, after `df -h /c` (25 GB floor):
   - Run `uv run --no-sync python tools/package/build.py --form onedir --with-ffmpeg >
     work/wp6.1/build-onedir-t3d.log 2>&1`, then the same with `--form onefile`
     (`build-onefile-t3d.log`).
   - The log must show `<n> hidden imports from 376 pack files`: 61 expected, the members in
     the list above.
   - It must show `hidden-import check: PASS (61 modules, each in the bundle)` and the
     existing `bundle check: PASS`.
   - The report goes to `work/wp6.1/hidden-imports-<form>.json`. Copy it to `t3d/`.
   - A FAILED line is a build failure. Do not work around it; report it. `site` is the member
     to watch, because PyInstaller may treat it specially.
3. **The pack.** It is at
   `<wt>\work\wp6.1\t3c\appdata\Local\Clearwater\gpu-pack\14.2.0-cu12\` (2,701 files,
   2,412.6 MiB). Its site-packages has no `.lock` file. Run `uv run --no-sync python
   tools/package/build.py --verify <that folder>` before the proof and again after it; the
   expected result is PASS with the same counts.
4. **The proof, headless.** The tool is
   `clearwater-review-evidence\wp6.1\cell\t3c\proof.py`, reused as in 2b-2. It spawns the
   worker as `export_process.py` does.
   - Its environment: `LOCALAPPDATA` / `APPDATA` / `TEMP` / `TMP` under `t3c\appdata\`;
     `PATH = C:\Windows\System32;C:\Windows`; every `CUDA_PATH*` removed; `CUPY_CACHE_DIR` under
     the redirected tree; the working directory `work\wp6.1\t3c\runs\<form>`.
   - Before running it, check that its child command is `<new dist>\Clearwater.exe
     --export-worker`, pointed at the NEW dists. Check also that it redirects every app-data
     variable (CLAUDE.md's entry-point isolation rule).
   - Order: the onedir form first, then onefile. For each: the HEIC -> PNG request, then the
     `vfr.mp4` request.
   - Record for each run:
     - the exit (3221225477 is DR-125);
     - the device line, which must be the GPU / CUDA backend;
     - the output;
     - every mapped CUDA / CuPy file over the run's process tree, sampled during the run
       (psutil `memory_maps()`). Each must lie under the pack or the NVIDIA driver. List them
       all;
     - the canary children: psutil command lines, and their exits;
     - the leftovers (tasklist; `_MEI*` in the redirected `TEMP` for onefile).
   - Then one without-pack run per form (the folder renamed, as in 2b-2), with the device
     `CPU: CuPy not installed`.
5. **The window watch** (read-only; my planned form; not yet written).
   - A sampler runs beside each with-pack run. Every 0.25 s it lists the run's process tree
     by PID (psutil, from the worker's PID down: the canary children included).
   - For each PID it asks UI Automation for top-level windows: PowerShell `Add-Type
     -AssemblyName UIAutomationClient`, then
     `[System.Windows.Automation.AutomationElement]::RootElement.FindAll([System.Windows.Automation.TreeScope]::Children,
     (New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ProcessIdProperty,
     <pid>)))`.
   - It writes the count and names to a JSONL file. ANY element is a STOP.
   - Alternative: `ctypes` `EnumWindows` + `GetWindowThreadProcessId` filtered to the
     tree's PIDs, also read-only.
   - It never sends input and never activates or focuses a window.
6. **Item 5.** Ledger: the builds, the resolved set as built, the proof table, the canary
   observations.
   - The report's limits get two lines: CHARC's on the library re-entry ("a library's own
     re-entry reached the GUI branch; the rule held"), and this group's before-record
     incident.
   - Name the `-qmljsdebugger` collateral in the report.

Depth at turn-3 group-2b-3 (code) end: 304,242 (wp61-cell5, at its final report; read by the dispatcher)

## Turn 3 group 2b-3 (items 4-5) (2026-11-04 ~13:10-13:30Z): both rebuilds, the handler check, the with-pack proof -- STOPPED at the first with-pack run (F-E)

Fresh cell (implementer-opus-high, wp61-cell6), dispatch
`clearwater-review-evidence/wp6.1/cell/dispatch-8.md`, head at start `e0a90bc5`. Evidence:
`clearwater-review-evidence/wp6.1/cell/t3e/`. No desktop input was sent. No GUI launch.
`t2b/gui_check.py`, the 2b-2 builds and `t3c/exp/` were not run (`t3c/exp/` was only READ, as
the handler check's control). No network. Nothing under the real `%APPDATA%\Clearwater` or
`%LOCALAPPDATA%\Clearwater` (the latter absent before and after). Every frozen run had APPDATA,
LOCALAPPDATA, TEMP / TMP, XDG_DATA_HOME / XDG_CONFIG_HOME / XDG_CACHE_HOME / XDG_STATE_HOME and
XDG_RUNTIME_DIR under `work\wp6.1\t3c\appdata\`, every `CUDA_PATH*` removed, and
`PATH = C:\Windows\System32;C:\Windows`.

**Owner log** `%APPDATA%\Clearwater\logs\clearwater.log`: md5 `69ed0432c562db9445daecbe8f15fe27`
before (13:12:50Z) and after (13:27:08Z) (`t3e/owner-log-md5-{before,after}.txt`).

### Item 1: the wider run on `e0a90bc5`

| Command (worktree root, Git Bash, `PYTEST_ADDOPTS` unset) | Exit | Summary |
|---|---|---|
| `uv run --no-sync pytest -q -rs -p no:cacheprovider --timeout 120 --durations=5 --basetemp=<wt>/work/c61f-1 tests/test_gpu_pack.py tests/test_frozen_entry.py tests/test_tools_package_build.py tests/test_jobs_export_process.py tests/test_app_composition.py tests/test_wp42_composition.py tests/test_core_backend.py -m "not gpu"` | 0 | **358 passed, 41 deselected in 46.01 s** (slowest 4.61 s, `test_the_real_pack_scan_finds_ctypes_wintypes`) (`t3e/pytest-wider-c61f-1.log`) |

### Item 2: both rebuilds (from `e0a90bc5`; `src` and `tools` clean, only this ledger modified)

| Form | Command (worktree root) | `df -h /c` before | Exit | Wall (shell / PyInstaller) | Result |
|---|---|---|---|---|---|
| onedir | `uv run --no-sync python tools/package/build.py --form onedir --with-ffmpeg > work/wp6.1/build-onedir-t3d.log 2>&1` | 77 GB free (13:14Z) | 0 | 89 s / 77.7 s | `_internal` 225 MB (du) + `Clearwater.exe` 10,670,591 B; 668.3 MiB release with FFmpeg; bundle checks 7.9 s |
| onefile | `... --form onefile --with-ffmpeg > work/wp6.1/build-onefile-t3d.log 2>&1` | 77 GB free (13:15Z) | 0 | 88 s / 84.1 s | `Clearwater.exe` 93,866,946 B (89.5 MiB); 523.9 MiB release; bundle checks 0.8 s |

- Both logs show `61 hidden imports from 376 pack files`, `hidden-import site (scan; named 1x)`,
  `hidden-import check: PASS (61 modules, each in the bundle)` and `bundle check: PASS`.
- The single warning is the usual `scipy.special._cdflib` (benign). FFmpeg and ffprobe
  9.0.2-full_build-www.gyan.dev were copied.
- The resolved set is the 61 members listed in group 2b-3 (60 from the scan, `graphlib`
  committed). `site` was bundled without complaint.
- Copies: `t3e/build-on{dir,file}-t3d.log`, `t3e/hidden-imports-on{dir,file}.json`.

**The handler check, read-only** (`t3e/handler_check.py` -> `t3e/handler-check.json`).

- Method: PyInstaller's own `CArchiveReader` on each new `Clearwater.exe`; the entry script
  `__main__` (typecode `s`) unmarshalled; nothing executed.
- Both builds: `interpreter_reentry` and `run_interpreter_option` are PRESENT, and their
  bytecode and constants EQUAL a compile of `src/clearwater/__main__.py` at `e0a90bc5`.
  `REENTRY_ARGUMENT` is in the module's names. `clearwater.__main__` is not in the PYZ: the
  entry script is the only copy. **PASS on both.**
- Control: the same check on the 2b-2 experimental build
  (`t3c/exp/dist-onedir/.../Clearwater.exe`) gives `present: false` for both functions and
  `HANDLER CHECK: FAIL` (`t3e/handler-check-control-t3c-exp.json`). So the check distinguishes.

**The window watch** (`t3e/proof3.py` + `t3e/uia_watch.ps1`; read-only, no input, no focus).

- A process-tree tracker runs every 0.02 s. It records each PID's command line and parent and
  keeps an `OpenProcess` handle, so a child's EXIT code can be read after it ends.
- Every 0.25 s it queries, for each PID of the tree, the UI Automation top-level elements (a
  long-lived PowerShell `FindAll(Children, ProcessId = pid)`) and `EnumWindows`.
- A UIA element or a visible top-level window = kill the tree by PID (create time checked)
  and STOP. A hard timeout also kills the tree.
- Positive control (`t3e/control.out`, counts only): explorer.exe showed 2 UIA elements and 9
  visible / 46 hidden windows; this Python showed 0.

**The second check, executed** (pack folder renamed `14.2.0-cu12.renamed`, watch running;
`t3e/argv-*.out`, `t3e/proof3.jsonl`):

| Form | Arguments | Exit | stderr (one line) | Windows (UIA / visible) | Tree | Left |
|---|---|---|---|---|---|---|
| onedir | `-c pass` | 2 | `Clearwater: -c is not supported` | 0 / 0 (1 sample) | 1 PID | none |
| onedir | `-m http.server` | 2 | `Clearwater: -m 'http.server': no GPU pack is loaded` | 0 / 0 | 1 PID | none |
| onefile | `-c pass` | 2 | `Clearwater: -c is not supported` | 0 / 0 (9 samples) | bootloader + child, both exit 2 | none; no `_MEI` |
| onefile | `-m http.server` | 2 | `Clearwater: -m 'http.server': no GPU pack is loaded` | 0 / 0 (8 samples) | the same | none; no `_MEI` |

### Item 3: `--verify` (pack renamed back)

`build.py --verify <t3c pack>`: exit 0, `PASS (11 distributions; 2701 RECORD rows, each file's
sha256 and size; 2701 files, 2412.6 MiB)`, the same as 2b-2's figures (`t3e/verify-1-before.log`).
`site-packages` has no `.lock` and no unlisted entry.

### Item 4: the with-pack proof -- STOPPED at the first run

| Form | Request | Exit | Device (worker result) | Output | CUDA / CuPy files mapped | Canary children | Windows | Left over |
|---|---|---|---|---|---|---|---|---|
| onedir | HEIC -> PNG (`with-heic-t3e`, 13:22:38Z, 11.8 s) | 0 (not DR-125 this time) | **`CPU: CUDA device unusable`**; log `a test kernel failed on the CUDA device: Canary probe child process timed out after 10.0 seconds.` (child stderr empty); warning `Processed on the CPU (CPU: CUDA device unusable).` | `heic-ad24-both_corrected.png`, ok | 62: 54 CuPy / cupyx `.pyd` files from the pack and 8 driver files (`System32\nvcuda.dll`; `DriverStore\FileRepository\nvami.inf_amd64_...\{nvcuda64, nvapi64, nvapi64_impl, nvdiagclt64, nvdxgdmal64, nvobjectloader64, Display.NvContainer\NvMessageBus}.dll`); **0 elsewhere**; no NVIDIA-wheel DLL (the failure came first) (`t3e/with-onedir-heic-cuda-files.txt`) | ONE: `Clearwater.exe -m cuda.pathfinder._dynamic_libs.dynamic_lib_subprocess canary cudart`, exit **1** (pathfinder's kill at 10 s) | 0 UIA / 0 visible in 41 samples | none (psutil, tasklist); 0 files added to the pack |

This is the dispatch's STOP condition: the device is not GPU and the canary timed out.

- No further pack-activating run was made: not the onedir video, not onefile.
- Item 5's without-pack regression was NOT run. The builds will change with the fix, so it is
  owed on the next builds.

**FINDING F-E (packaging; the STOP): the canary child hangs at start-up because the export
worker's cancel thread is blocked reading the inherited stdin pipe.**

The cheap reproduction: `t3e/repro_stdin.py` and `t3e/stdin_parent.py`. The parent is a
plain-Python stand-in with a PIPE stdin (no product code). The grandchild runs under the window
watch. Outputs are in `t3e/repro-*.out`.

| Stand-in parent | Child (stdin inherited, `capture_output=True`, timeout 15 s) | Result |
|---|---|---|
| no thread reading stdin | new onedir `Clearwater.exe -m ...dynamic_lib_subprocess canary cudart` | returncode 0 in 0.24 s, `{"status": "not-found", "abs_path": null}` |
| a daemon thread blocked in `sys.stdin.buffer.readline()` (as `export_worker._watch_stdin`) | the same | **timeout 15 s**, empty stderr; killed (exit 1) |
| the same | base CPython 3.12 `python.exe -I -c "print(1)"` | **timeout 15 s** |
| the same | new onedir `Clearwater.exe -c pass` (refused in `__main__`'s first lines) | **timeout 15 s** |
| (direct, `t3e/repro-onedir-canary*.out`) no parent thread; worker-like cwd (pack `site-packages`) and / or stdin left open | the canary | exit 0 in about 0.42 s, the same payload |

- So ANY Python child hangs when it inherits a pipe stdin on which its parent has a pending
  synchronous read. The hang is in the child's process start-up (CPython / the bootloader),
  before Clearwater's code runs. Nothing in the `-m` handler can fix it.
- In the frozen worker, `cuda.pathfinder` runs its canary with `subprocess.run(...,
  capture_output=True)` and no `stdin`. So the canary inherits the worker's protocol stdin,
  and `export_worker._watch_stdin` is blocked reading it (`app/export_worker.py:214-217`; the
  thread is started at `:273`).
- The source run never reached the canary: pathfinder finds the wheels through
  `site.getsitepackages()` in the venv. That is why 2b-2's import-gap source run was GPU.
- Side observation for DR-125 (a lead, not a claim about the cause): in every run where its
  daemon thread was still blocked in the stdin read at exit, the stand-in parent itself exited
  `3221225477`. Where there was no such thread, it exited `0`.

**Options for CHARC (none made; a code change is a STOP first):**

- (a) Owned, frozen only, in `src/clearwater/__main__.py`. On the `--export-worker` branch,
  before `export_worker.main()`, move the protocol pipe off the standard-input slot:
  - duplicate fd 0 to a private, non-inheritable descriptor and point `sys.stdin` at it;
  - point fd 0 and the Win32 standard input handle at `os.devnull`. The windowed build is a
    GUI-subsystem process, so the CRT's `_dup2` may not update the Win32 handle. An explicit
    `SetStdHandle` is an N1 site under `sys.platform`.

  Children then inherit NUL. 1.0.0's source run is unchanged.
- (b) Not owned, product-wide: the same inside `app/export_worker.py` (source and frozen
  alike), or start the cancel thread only after the backend probe.
- (c) Avoid the canary through pathfinder's own configuration. This is fragile, as 2b-2 (ii).

Recommended: (a), with a test that a child spawned by the frozen worker branch inherits no
pipe stdin. Then both rebuilds, the handler check, and this proof from its start.

### Item 4 addition (CHARC, via the dispatcher): the frozen process and the user's site-packages

The question: since `site` is now a hidden import, does a frozen process put the user's
site-packages on `sys.path`? CHARC asked for `sys.flags.no_site`, `sys.flags.no_user_site`,
`site.ENABLE_USER_SITE`, and any `...\Python\Python312\site-packages` entry on `sys.path`.

**Route.** No pack module prints these values. `-m` refusals carry the same text whether a name
is unresolvable or resolved outside the pack. So I used two behaviours of existing pack code,
in pack-activating `-m` runs on the two NEW builds only, under the isolation redirect and the
window watch. Nothing was planted in the pack.

- **Plant (disposable tree only).** I created two EMPTY directories in the REDIRECTED user site,
  `t3c\appdata\Roaming\Python\Python312\site-packages\`: `cuda\` and `nvidia\nvjpeg\bin\`.
  There are no files and no code (`t3e/usersite-plant.txt`). Both were removed afterwards.
- **Probe 1 (`sys.path`, before `site` is imported).** The `-m` handler accepts a module only
  when EVERY namespace portion of `cuda` lies under the pack (`gpu_pack.module_from_pack`).
  - If the user site were on `sys.path`, the empty `cuda\` would be a second portion and the
    run would be refused.
  - The check runs before the module, so before pathfinder's `import site`.
- **Probe 2 (`site.ENABLE_USER_SITE`, after `import site`).** Mode `load nvjpeg` (a library not
  in the pack) runs pathfinder's `find_sub_dirs_all_sitepackages`
  (`cuda/pathfinder/_utils/find_sub_dirs.py`). That function adds `site.getusersitepackages()`
  only `if site.ENABLE_USER_SITE`. Its not-found message lists `listdir("<dir>")` for each
  existing searched directory.

| Process | `-m` accepted? | `load nvjpeg` message lists the user-site `nvidia\nvjpeg\bin`? | Exit; windows; left |
|---|---|---|---|
| NEW onedir `Clearwater.exe -m cuda.pathfinder._dynamic_libs.dynamic_lib_subprocess load nvjpeg` | **yes** (ran; payload `not-found`) | **no**: `Failure finding "known nvjpeg DLL": No such file: known nvjpeg DLL, No such file: known nvjpeg DLL` | 0; 0 UIA / 0 visible; none (`t3e/usersite-probe-onedir.out`) |
| NEW onefile, the same | **yes** | **no** (the same message) | 0; 0 / 0; none; no `_MEI` (`t3e/usersite-probe-onefile.out`) |
| CONTROL: base CPython 3.12 (non-frozen), `PYTHONPATH` = the pack, the same redirect (`t3e/usersite_control.py`, `t3e/usersite-control.out`) | `module_from_pack` = **False** (it would be refused); the redirected user site IS on `sys.path`; `no_site 0`, `no_user_site 0`, `ENABLE_USER_SITE True` | **yes**: `... \n  listdir("...\t3c\appdata\Roaming\Python\Python312\site-packages\nvidia\nvjpeg\bin"):` | 0 |

**What is OBSERVED inside each frozen process (both forms):**

- the user site, as that process would compute it, is NOT on `sys.path` at the `-m` check;
- after pathfinder's module-level `import site`, `site.ENABLE_USER_SITE` is FALSY, so pathfinder
  searches no user site either.

The control shows that both probes change outcome when the user site is enabled.

**What is REASONED, not observed (the exact flag values):**

- The windowed bootloader sets CPython's `site_import` config by name. `runw.exe` (PyInstaller
  6.22.3, `.venv\Lib\site-packages\PyInstaller\bootloader\Windows-64bit-intel\runw.exe`) holds
  the strings `site_import` at byte offset 215856 and `Failed to set 'site_import': %s` at
  215872. Both built `Clearwater.exe` files hold the latter at the same offset, 215872.
  `site_import = 0` is `sys.flags.no_site == 1`. The probes fit it: with `no_site 0`, CPython
  would run `site.main()` at start-up, and in a non-venv process that adds the user site to
  `sys.path` unless `no_user_site` is set.
- `sys.flags.no_user_site`: NOT determined. The bootloader has no `user_site` string, and the
  venv has no C source to cite.
- `site.ENABLE_USER_SITE`: falsy, observed. `None` when `site.main()` never ran, which the
  `no_site` reading implies. A value of `False` cannot be told apart from `None` by this route.
- The PyInstaller Python-side loader (`PyInstaller/loader/pyimod0*.py`, `pyiboot01_bootstrap.py`)
  has no site-flag handling (grep: no `no_site`, `site_import`, `ENABLE_USER_SITE` or
  `user_site`).
- I found no route to print the four values verbatim from inside the frozen process without a
  code change or a planted module. I did not make one.

**The real profile.** `C:\Users\rwsmy\AppData\Roaming\Python\Python312\` holds only
`comtypes_cache`. There is no `site-packages` there, so nothing of the owner's could be on a
frozen `sys.path` today in any case. I only listed it.

Owner log md5 after this addition: `69ed0432c562db9445daecbe8f15fe27` (a check only).
`%LOCALAPPDATA%\Clearwater` is absent. No `Clearwater.exe` is left (tasklist).

### Item 5 (partial)

- `--verify` after the runs: exit 0, the same PASS line and figures (`t3e/verify-2-after.log`).
  No run wrote into the pack.
- The without-pack regression: NOT run (see above).

### Slips (mine)

- One tool call carried a bare `cd` into the worktree (a `py_compile` of an evidence script).
  It was harmless here (the subagent's shell cwd resets per call) and was not repeated.

### Files changed this group

`docs/proofs/wp6.1-ledger.md` only.

- Evidence tools (not product, not committed): `t3e/handler_check.py`, `t3e/proof3.py`,
  `t3e/uia_watch.ps1`, `t3e/repro_stdin.py`, `t3e/stdin_parent.py`, `t3e/usersite_control.py`.
- The new builds are at `work/wp6.1/dist-on{dir,file}/`; they replace the 2b-2 builds.
- The pack is unchanged at `work/wp6.1/t3c/appdata/Local/Clearwater/gpu-pack/14.2.0-cu12`.

Depth at turn-3 group-2b-3 (items 4-5) end: DISPATCHER TO FILL

## Turn 3 group 2b-3 (F-E shim) (2026-11-04 ~13:35-13:55Z): the F-E shim, rebuilds, the with-pack proof -- STOPPED again (F-F, headers)

Same cell (wp61-cell6). The work: CHARC's F-E ruling (gen 15, 13:32Z), option (a) with its five
amendments, relayed by the dispatcher. No desktop input, no GUI launch. Every frozen run used
the isolation redirect and the window watch. Nothing touched the real profile. No network.

### The change (`62198baf`)

- `src/clearwater/__main__.py`: a new function `isolate_worker_stdin()`, called FIRST on the
  `--export-worker` branch, before `gpu_pack.activate()`, the worker import, its backend probe
  and any CuPy import (a comment at the call says so). It acts only when frozen.
  - It duplicates fd 0 to a private descriptor (`os.dup`, not inheritable by PEP 446), which
    becomes `sys.stdin`.
  - It points fd 0 at `os.devnull` in AD-36's statement form, `if sys.platform == "win32":`
    `dup2` and `ctypes.windll.kernel32.SetStdHandle(STD_INPUT_HANDLE, <fd 0's handle>)`,
    `else:` `dup2` only. This is the ONE new N1 site, for AD-34.
  - A failed `SetStdHandle` raises `OSError` (the Win32 slot would otherwise name the closed
    pipe handle).
  - A process without a standard input is left alone.
  - The docstring and `tools/package/README.md` (new section "The frozen worker's standard
    input (a TEMPORARY shim)") say the shim is temporary and that DR-125's package moves the
    isolation into the worker and removes it.
- `tests/test_frozen_entry.py`: three new tests, under the isolation rule (rule check
  `t3e/rule-check.txt`):
  - (i) `test_a_child_of_the_frozen_worker_branch_inherits_nul_not_the_request_pipe`. A fresh
    `-I` child plays the frozen worker: the GUI is unimportable, the app data is under
    `tmp_path`, and its stdin is a pipe the test holds open. The branch's `gpu_pack.activate`
    is replaced by a spawn, the first thing after the shim. The grandchild (`stdin=None`) reads
    its stdin to EOF and must report 0 bytes within 10 s. The test also checks: no
    `clearwater.app.export_worker` / `cupy` import yet; the worker's `sys.stdin.fileno() != 0`;
    `SetStdHandle` called once on win32.
  - (ii) `test_the_frozen_worker_reads_its_request_and_the_cancel_line_through_the_private_fd`.
    This is `test_cancel_is_delivered_on_stdin_and_the_child_ends`, re-pointed. Its own
    `_run` / `_Progress` (imported from `test_jobs_export_process`, not copied) drive a child
    running the frozen branch with the REAL `export_worker.main`. A stand-in `run` reads the
    request and then the `{"cancel": true}` line. The test asserts: `CANCELLED`, the cancel
    line, the request read, and the descriptor `!= 0`. The non-owned test file was NOT edited.
  - (iii) `test_the_worker_branch_moves_no_standard_input_when_not_frozen`: the 1.0.0 lock.
    Source run, `os.dup` replaced by a raiser, `SetStdHandle` by a counter: 0 duplicates, 0
    calls, `sys.stdin` the same object.
  - The existing in-process frozen worker-branch test (`..._sets_path_before_either_branch`)
    now stubs the shim, so it cannot re-point the test process's own stdin.

| Command (worktree root, Git Bash) | Exit | Summary |
|---|---|---|
| `pytest ... --timeout 120 --basetemp=<wt>/work/c61f-2 tests/test_frozen_entry.py -k "<the 4>"` | 0 | 4 passed in 1.56 s |
| BEFORE-record: `tests/test_frozen_entry.py` with `PYTHONPATH` = `git archive 3c67f0f3` src (`c61f-3`; `t3e/pytest-fe-before-on-3c67f0f3.log`; the entry-point grep and rule check first) | 1 | **2 failed, 88 passed**: (i) `:481` `assert 'timeout' == '0'` (the grandchild inherited the pipe and blocked); (ii) `:547` `assert 0 != 0` (the request was read on fd 0). (iii) PASSES by design: it pins 1.0.0 |
| the wider set (the 7 modules, `-m "not gpu"`, `c61f-4`) | 0 | **361 passed, 41 deselected in 32.14 s** |
| `ruff check .` / `ruff format --check .` / `mypy` / `mypy --strict` (2 files, win32 and `--platform darwin`) | 0 | All checks passed / 322 files already formatted / 160 files no issues / no issues |

0 CR in each blob (counted with `tr -cd '\r'`).

### Rebuilds (from `62198baf`; 78 GB free)

| Form | Exit | Wall (shell / PyInstaller) | Size | Checks |
|---|---|---|---|---|
| onedir | 0 | 67 s / 56.8 s | 668.3 MiB; `Clearwater.exe` 10,672,066 B | 61 hidden imports from 376 pack files; hidden-import check PASS (61); bundle check PASS |
| onefile | 0 | 77 s / 73.9 s | 523.9 MiB; `Clearwater.exe` 93,869,539 B | the same |

Logs and reports: `t3e/build-on{dir,file}-t3e.log`, `t3e/hidden-imports-on{dir,file}-t3e.json`.

**Read out of both bundles before any run** (`t3e/handler_check.py`, extended;
`t3e/handler-check-t3e.json`): `interpreter_reentry`, `run_interpreter_option`,
`isolate_worker_stdin` and `main` are present in the entry script of each `Clearwater.exe`,
with bytecode and constants equal to `62198baf`'s source. `main` names
`isolate_worker_stdin`, and `STD_INPUT_HANDLE` is in the module's names. **PASS on both.**
Control: the `t3c/exp` build (read only) shows the three functions absent and `main` without
the shim: FAIL.

### The with-pack proof -- STOPPED at the first run again

`--verify` before: PASS. (The file count read 2729: see the pack note below.)

| Form | Request | Exit | Device | Output | CUDA / CuPy files | Canary | Windows | Left |
|---|---|---|---|---|---|---|---|---|
| onedir | HEIC -> PNG (`shim-with-heic`, 13:48:41Z, 2.7 s) | 3221225477 (DR-125) | **`CPU: CUDA device unusable`**; log `a test kernel failed on the CUDA device: Failed to find CUDA headers. Please install CUDA toolkit headers (e.g., pip install cupy-cuda12x[ctk]) or specify CUDA_PATH environment variable.` | PNG, ok | 62: 54 pack `.pyd`, 8 driver, **0 elsewhere** | `Clearwater.exe -m ...dynamic_lib_subprocess canary cudart`, **exit 0, alive 1.346-1.591 s (about 0.25 s): F-E is FIXED** | 0 UIA / 0 visible (9 samples) | none |

**The shim works**: the canary now returns at once instead of timing out. But the device is
still not GPU, which is dispatch-8's STOP condition. No further pack-activating run was made
(not the onedir video, not onefile, not the site-flag probes on these builds). The regression
without the pack was NOT run either.

**FINDING F-F (packaging; the STOP): `cuda.pathfinder` looks for the CUDA HEADERS in
`site.getsitepackages()`, not on `sys.path`, so a frozen process never finds the pack's
headers.** The headers are in the pack (`nvidia/{cuda_runtime, cuda_nvrtc, cublas, ...}/include`).

- `cuda/pathfinder/_headers/find_nvidia_headers.py:82-86`, step 1 `find_in_site_packages`,
  calls `find_sub_dirs_all_sitepackages` = `site.getsitepackages()` plus the user site
  (`_utils/find_sub_dirs.py`). The later steps are conda, the product roots, `CUDA_PATH` /
  `CUDA_HOME`, the CTK-root canary and the system dirs.
- In the frozen process the pack is only on `sys.path` (the loader's design), so every step
  misses and CuPy's kernel compile refuses.
- The canary's own JSON, read standalone on the e0a90bc5 builds (`t3e/repro-onedir-canary*.out`;
  the `-m` branch is unchanged since), is `{"status": "not-found", "abs_path": null}`:
  `cudart` is not on the system search path, so the canary gives no CTK root either.

Reproduced cheaply with base CPython and no product code (`t3e/headers_repro.py`,
`t3e/headers-repro-{plain,prefixes}.out`; `-B -s`, the redirect, no `CUDA_PATH`). Pathfinder
was imported from the pack in both runs.

| Mode | The pack in `site.getsitepackages()` | `find_nvidia_header_directory("cudart")` / `("nvrtc")` |
|---|---|---|
| `plain`: the pack on `sys.path` only (as the frozen loader leaves it) | no | `None` / `None` |
| `prefixes`: the same, plus `site.PREFIXES.insert(0, <pack site-packages>)` before the import | yes | `<pack>\nvidia\cuda_runtime\include` / `<pack>\nvidia\cuda_nvrtc\include` |

**Options for CHARC (none made; a code change is a STOP first):**

- (a) Owned, frozen only, in `gpu_pack.activate()` after the `sys.path` insertion: `import
  site` (bundled since F-C2; inert under `no_site`) and put the pack's `site-packages` first in
  `site.PREFIXES`.
  - On Windows `getsitepackages()` then lists it, so pathfinder's site-packages step finds the
    pack's headers, and its wheel DLLs the intended way.
  - The `-m` canary child gets it through the same `activate()`.
  - The repro shows it for the headers.
  - The Linux form (`lib/python3.12/site-packages` under each prefix) needs a different
    spelling; that is for WP6.3 / WP6.4.
- (b) Set `CUDA_PATH` to `<pack>/nvidia/cuda_runtime`. It reaches CuPy's own CUDA-path logic
  and pathfinder's DLL steps as well, and the NVRTC headers live in another folder. Wider
  effect; not recommended.
- (c) Configure or patch pathfinder itself. Fragile.

Recommended: (a), with a test that a frozen activation makes `site.getsitepackages()` list the
pack and leaves a source run unchanged. Then rebuild, the bundle read-out, and this proof from
its start (amendment 4's evidence included).

### The site flags (amendment 4)

Not re-run on the shim builds (the STOP). The values of record are the group's earlier
addition on the `e0a90bc5` builds. The shim does not touch `site`, `sys.path` or `sys.flags`.

### The pack, and a slip of mine (repaired; disclosed)

- My two NON-frozen helper runs wrote bytecode INTO the pack: 28 `cuda/pathfinder/**/__pycache__/*.pyc`
  files each time.
  - The first was the earlier user-site control (base CPython, `PYTHONPATH` = the pack, about
    13:33Z).
  - The second was `headers_repro.py`. It ran with `-B`, but pathfinder's CTK-root canary
    spawns `sys.executable -m ...` without `-B`, with the working directory set to the pack's
    `site-packages`.
- The frozen runs write none (`write_bytecode` is off in the bootloader; 0 files added in every
  frozen record).
- `--verify` cannot see nested unlisted files: it PASSED with 2729 files. I found them by the
  file count.
- I deleted exactly those 28 files twice (the same names both times, `t3e/stray-pyc-removed{,-2}.txt`;
  no RECORD row names a `__pycache__`) and the empty `__pycache__` folders left behind.
- `--verify` then gave `PASS (11 distributions; 2701 RECORD rows ...; 2701 files, 2412.6 MiB)`
  (`t3e/verify-5-after-pyc-removal-2.log`), the 2b-2 figures. The shim run at 13:48Z ran while
  the first 28 files were present; it does not count as a pack-state proof.
- For WP6.3: a full-content verify that also counts unlisted nested files would have caught
  this.

Owner log md5 `69ed0432c562db9445daecbe8f15fe27` at every check (13:35-13:55Z; a check only).
`%LOCALAPPDATA%\Clearwater` is absent. No `Clearwater.exe` is left.

### Files changed

`src/clearwater/__main__.py`, `tests/test_frozen_entry.py`, `tools/package/README.md`
(`62198baf`) and `docs/proofs/wp6.1-ledger.md`. Evidence tools (not committed): the extended
`t3e/handler_check.py` and `t3e/proof3.py` (each process's end time), and
`t3e/headers_repro.py`.

Depth at turn-3 group-2b-3 (F-E shim) end: DISPATCHER TO FILL

## Turn 3 group 2b-3 (Reviewer A r3 fold-in) (2026-11-04 ~14:00-14:40Z): the r3 fixes on top of the F-E shim -- MID-BUILD YIELD, no build

Same cell (wp61-cell6). The work: the dispatcher's amendment (fold Reviewer A round 3,
`clearwater-review-evidence/wp6.1/A/r3/review.txt`, into the pending change) and CHARC's rulings
on #3 and its precisions.

- **Timing note.** The amendment ("DO NOT REBUILD YET") reached me after the F-E-shim builds of
  `62198baf`; those builds are superseded by this change. Nothing was built in this group.
- No pack-activating run was made. F-F (the CUDA headers) is still with CHARC and NOT in this
  change.

Commit `48c0891f`. The before-record (its line numbers are those of the test files as run then; `test_gpu_pack.py` was reformatted afterwards) is the three owned test modules with `PYTHONPATH` /
`WP61_BUILD_SCRIPT` on `git archive e0a90bc5` src and tools (`t3e/pytest-r3-before-on-e0a90bc5.log`):
**42 failed, 220 passed**. The rule check came first (`t3e/rule-check-r3.txt`, 25 call sites).
The owner log md5 was unchanged before and after.

| # | Fix (file) | Test(s) | On `e0a90bc5` |
|---|---|---|---|
| 1 MAJOR | `__main__.main`: the `--export-worker` dispatch is inside `if sys.frozen`. A source `python -m clearwater --export-worker` reaches `app.main` as in 1.0.0. | `:161` re-pointed: `test_a_source_run_sends_the_worker_flag_to_the_gui_as_1_0_0_did` (GUI stand-in, `calls` redirect). The worker tests became frozen-simulated, with the shim stubbed: `test_the_frozen_worker_flag_runs_the_shim_the_loader_then_the_worker_without_qt` pins the order shim -> loader -> worker. `test_the_worker_flag_alone...` is now frozen. The fresh-interpreter worker-import probe sets `sys.frozen`. | `:174` (the worker ran: 7, not 3); the frozen order test `:196` (no shim); F-E (iii) `:689` |
| 2 MAJOR | `interpreter_reentry`: a character scanner over CPython 3.12's option grammar. `FLAG_LETTERS` `bBdEiIOPqsSuvx` (from `python -h`) may be clustered. `VALUE_LETTERS` `WX` take the rest of the cluster or the next argument. `REENTRY_LETTERS` `mc` take an attached or the next operand. Any other letter (`h`, `V`, `?`, `p`, `t`, `w`, ...), `-`, `--`, or a non-option = not a re-entry (GUI). `REENTRY_ARGUMENT` / `LEADING_FLAGS` / `VALUED_FLAGS` are removed. | grammar table +27 rows: `-Xutf8 -m`, `-Wignore -m`, `-Wignore -cpass`, `-OO`, `-Es`, `-IIs`, `-bb`, `-IXutf8`, `-IW ignore`, `-IIm`, `-E -s -m`, `-movie.mp4`; and the GUI ones: `-X`, `-Xutf8` alone, `-h`, `-V`, `-?`, `-hm a`, `--version`, `-`, `--`, `-- -m a`, empty, non-ASCII, `-style=fusion`. `test_every_spelling_of_dash_m_runs_a_pack_module` +4 (`-Xutf8`, `-Wignore`, `-OO`, `-Es`). `test_cpythons_own_interpreter_flags_prefix_is_a_re_entry`: a child started `-OO -Wignore -Xutf8` prints `_args_from_interpreter_flags()` (it emits `-OO`, `-Wignore`, `-X utf8`); that prefix and this process's own, each before `-m x`, give `["-m", "x"]`. | `:1171` x10 (9 new forms, plus `-hm a`, which the old regex took as a re-entry: CPython would print its help); `:1230` x4 (`:49`, the GUI blocked); `:1200` |
| 3 MAJOR (CHARC: REFUSE) | `MULTIPROCESSING_FLAGS` = `--multiprocessing-fork`, `--multiprocessing-resource-tracker`; `multiprocessing_reentry` matches ANY argument after the program name. Frozen only, it is checked FIRST, before the worker flag and the `-m` / `-c` grammar: `Clearwater: multiprocessing children are not supported`, status 2, nothing else consulted (no shim, loader, log or GUI). The list was read from BOTH bundles' frozen code (`t3e/mp_flags.py` -> `t3e/mp-flags.txt`: the 23 PYZ `multiprocessing*` modules and every CArchive script / module entry). The only `--multiprocessing-` string is `--multiprocessing-fork` (`multiprocessing.spawn`). `--multiprocessing-resource-tracker` is CHARC's name; no bundled code emits it. `freeze_support()` is not called. | `test_a_frozen_multiprocessing_re_entry_is_refused_before_every_branch[4]` (`resource-tracker`; after `--export-worker`, after `-m`, after `-c`); `test_the_real_multiprocessing_spawn_command_line_is_refused_when_frozen` (`multiprocessing.spawn.get_command_line(parent_pid=123, pipe_handle=456)` with `sys.frozen` set: `[exe, "--multiprocessing-fork", ...]`); `test_a_source_run_sends_a_multiprocessing_flag_to_the_gui_as_before` (1.0.0) | `:240` / `:241` x4 (the GUI stand-in ran, or `-c`'s line); `:262`; the source pin PASSES by design |
| 4 MAJOR | `gpu_pack.parse_record` validates each row up front. CSV errors; exactly 3 fields; no NUL; a non-empty path; a hash empty or `<alg>=<base64>` (`_RECORD_HASH`); a size empty or 1-20 ASCII digits (`_RECORD_SIZE`); then each path part (split at `/` and backslash) through `_component_problem`. `pack_problems` is now a wrapper over `_pack_problems`: an `OSError` gives `pack unreadable: <type>`, any other exception `pack check failed: <type>`. `check_pack` catches any exception too. `--verify` uses the same wrapper. | `test_a_malformed_or_escaping_record_row_is_rejected`, one row per probe with its REASON: `.,,1` -> `RECORD row path not allowed (an empty or '.' part): .`; an embedded NUL -> `RECORD malformed: row 8: a NUL character`; a 5,000-digit size -> `... a size not of 1-20 digits`; `not-a-hash` -> `... a hash not of the form algorithm=base64`. The two old rows' reasons gain their `: <what>` suffix. `test_any_exception_in_the_walk_is_a_rejection_at_start_up_and_in_verify` (`_row_problems` raising `IndexError`: `pack check failed: IndexError`, and `--verify` lists it, exit 1). | `test_gpu_pack.py:816` x10 (the old reasons, or an exception); `:976` (the `IndexError` escaped) |
| 5 MINOR | `_component_problem`: `:` (ADS or a drive), a trailing `.` or space, an empty part (`a//b`). | rows `ads`, `trailing-dot` (`cupy/__init__.py.`), `trailing-space`, `empty-part` | in `:816` above (the old code accepted the trailing-dot and trailing-space rows: the file resolved) |
| 6 MINOR | `__main__._path_key` drops surrounding double quotes. `prepend_executable_folder` treats a quoted first entry as not yet first, because `shutil.which` does not strip quotes (`Lib/shutil.py:1523-1526` only splits). | `test_a_quoted_spelling_of_the_folder_is_dropped_from_behind`: `x;"<folder>"` -> `<folder>;x`; `"<folder>";x` -> `<folder>;x`, then unchanged | `:436` |
| 7 MINOR | `_add_dll_directories` lists `nvidia` with `os.scandir` (an access error becomes `DLL folders unreadable: <type>`). | `test_an_unlistable_nvidia_folder_rejects_the_pack` | `test_gpu_pack.py:1003` (via `_rejected` `:469-471`: loaded, with no DLL folders) |
| 8 MINOR | `_safe()` on the folder name in `DLL folder nvidia/<name>/bin: <type>`. | `test_a_failing_non_ascii_dll_folder_is_named_in_ascii` (`nvidia/\xe9/bin`) | `:1024` |
| 9 MINOR | `build.name_violations`: allowlist and stdlib membership case-folded (`_ALLOWED_FOLDED`, `_STDLIB_FOLDED`). | `test_the_dependency_allowlist_is_case_folded` (`pyside6/QtCore.pyd`, `NUMPY/x.pyc`, `JSON.pyc` pass; `AV/x.pyd` is still `unexpected-module`) | `test_tools_package_build.py:757` |
| 10 MINOR | test only | `test_a_frozen_dash_m_runs_a_pack_module_after_the_loader_without_qt` now records, through `PROBE_SYS_BODY`, `sys.argv[0]` and `sys.modules["__main__"].__file__` (each must be the module's file). Mutation run (`t3e/pytest-r3-mutation-alter-sys.log`, `alter_sys=False` on a copy of the new src): **1 failed**, `assert 'Clearwater.exe' == '...probe.py'`. | passes (the old code is correct; the test now catches the mutation) |
| 11 ADVISORY | `build.forbidden_entries` also checks a PYZ entry's own name, by the name rules. | `test_a_pyz_containers_own_name_is_checked` (a PYZ named `cupy/runtime.pyd` holding only `json`: `gpu-module`; a canonical `PYZ.pyz`: clean). The test helper `make_exe` gained `pyz_name`. | `:766` |
| 12 ADVISORY | `build.pack_sources()` (the pack's own set) raises `ValueError` when an installed version is not the lock's. `build()` turns that, and a missing distribution, into `FAILED: the pack sources cannot be scanned: ...`, exit 1 (it raised before). | `test_a_pack_distribution_at_another_version_fails_the_scan_and_the_build` (a stale `cupy-cuda12x` 0.0) | `:792` (DID NOT RAISE) |

The rest of the 42: the F-E tests (i) `:592` and (ii) `:658`, as in the F-E group ((iii) `:689` is
counted under #1). The frozen worker-flag-alone test PASSES on the old code by design (the old worker branch
gives `[]` too).

Commands (worktree root, Git Bash, `PYTEST_ADDOPTS` unset; logs in `t3e/`):

| Command | Exit | Summary |
|---|---|---|
| the three owned modules (`c61f-6`) | 0 | 262 passed in 10.57 s |
| the same on `e0a90bc5` (`c61f-7`) | 1 | 42 failed, 220 passed |
| the wider set (the 7 modules, `-m "not gpu"`, `c61f-10`) | 0 | **413 passed, 41 deselected in 32.72 s** |
| `ruff check .` / `ruff format --check .` | 0 / 0 | All checks passed / 322 files already formatted |
| `mypy` / `mypy --strict` on the 6 touched files, win32 and `--platform darwin` | 0 / 0 / 0 | 160 files / 6 / 6, no issues |
| `build.py --verify` on the real pack with the new row validation (`t3e/verify-6-new-validation.log`) | 0 | PASS, 2701 rows / files, 2412.6 MiB (every real row passes the new checks) |

Self-review (suspected / confirmed / fixed):

1. A heredoc collapsed `\\x00` into a literal NUL byte and `[/\\]` into `[/\]` in `gpu_pack.py`.
   Confirmed by a byte count. Fixed with a byte-level replacement from a written script; the
   file now holds 0 NUL bytes.
2. The F-E (iii) test, the fresh-interpreter worker probe and its mutation twin assumed a source
   `--export-worker` reaches the worker. Confirmed by 2 failures. Re-pointed (above).
3. A quoted first `PATH` entry was "already first". Confirmed by reading `shutil.which`. Fixed:
   it is rewritten unquoted.

A second pass found nothing new.

Slip (mine): one tool call carried a stray `cd /dev/null` (it failed; no effect). Not repeated.

Owner log md5 `69ed0432c562db9445daecbe8f15fe27` at every check (a check only).
`%LOCALAPPDATA%\Clearwater` is absent. The pack is unchanged (0 `.pyc`, `--verify` PASS).

For the one rebuild after F-F's ruling, read from both bundles before any with-pack run:
`interpreter_reentry`, `run_interpreter_option`, `isolate_worker_stdin`,
`multiprocessing_reentry` and `main` (bytecode equal to the source; `main` names both new
functions; `MULTIPROCESSING_FLAGS` present). `t3e/handler_check.py` needs `multiprocessing_reentry`
added to its list.

(This batch continues in the next section; its depth line is there.)

## Turn 3 group 2b-3 (A r3 batch, continued): F-F and Q2 as CHARC ruled; the before-record on `54266f5e` -- FINAL for wp61-cell6

Same cell (wp61-cell6). The dispatcher bounded the rest of my seat: the A r3 batch above, plus
CHARC's F-F and Q2 rulings. NO build and NO pack-activating run; then retire. Commit `69d31929`.
`tests/test_jobs_export_process.py` is untouched. The re-point of the cancel case inside
`tests/test_frozen_entry.py` was ACCEPTED by CHARC.

| Item | Fix (file) | Test(s) | On `54266f5e` |
|---|---|---|---|
| F-F (a) | `gpu_pack.add_site_prefix`, called by `activate()` (so frozen only) after a LOADED pack's `sys.path` insertion. It does `import site` (the bundled module) and puts the pack's `site-packages` FOLDER first in `site.PREFIXES`: moved to the front, never twice, never `<pack>`. The module docstring notes the `lib/python3.12/site-packages` spelling as a future-Linux-leg matter only. `CUDA_PATH` and a pathfinder patch are not used. | `test_a_frozen_activation_puts_the_pack_folder_first_in_site_prefixes`: `site.PREFIXES == [<pack>/site-packages, *before]`; `<pack>` not in it; on Windows `getsitepackages()[0] == <pack>/site-packages` exactly and `[1] == .../Lib/site-packages`; `ENABLE_USER_SITE` unchanged; `sys.path` gains only the one pack entry; a second activation adds nothing. `test_a_source_run_leaves_site_prefixes_untouched` (the 1.0.0 lock). `test_a_rejected_pack_adds_no_site_prefix`. The `isolated` fixture now also copies `site.PREFIXES`, so no test touches the pytest process's own. | `test_gpu_pack.py:1169` (no prefix); the source and rejected pins PASS by design |
| Q2 | `_pack_problems(full=True)`, i.e. `--verify`, ends with `_unlisted_files`. It walks every file under `site-packages` (`os.walk`; a listing error is raised and the wrapper turns it into `pack unreadable`) and yields `unlisted file in site-packages: <path>` for each path no RECORD row names (normcase, `/`-joined). No exclusions: `__pycache__` included. A top-level entry already reported as unowned is not repeated. The start-up (cheap) check stays top-level. | `test_the_full_verify_lists_every_unlisted_nested_file`: a planted `cupy/__pycache__/__init__.cpython-312.pyc` and `cupy/planted.py`. `check_pack` still passes; `--verify` exits 1 listing both. | `test_gpu_pack.py:1223` (`--verify` passed) |

The real pack under the full walk (`t3e/verify-7-q2-walk.log`): **PASS**, 2701 rows, 2701 files,
2412.6 MiB. Every file on disk is named by a row, and there are 0 `.pyc` files.

**Readers of `site.PREFIXES`, `site.getsitepackages()` and `site.getusersitepackages()`**
(`t3e/site_readers.py` -> `t3e/site-readers.txt`). Both bundles were read by PyInstaller's
readers (1,073 code objects each: every PYZ module, the stdlib and PySide6 included, and every
CArchive script and module entry). The pack's `.py` files got a text search, nothing imported.

- Bundle: **`site` itself** (its own `getsitepackages` / `getusersitepackages` /
  `addsitepackages`; `main()` never runs under `no_site`).
- Bundle: `PIL.TiffImagePlugin` matches only by name. Its `PREFIXES` is PIL's own TIFF
  byte-order constant (`PIL/TiffImagePlugin.py:280`), not `site`'s.
- Pack: **`cuda/pathfinder/_utils/find_sub_dirs.py:53`** `site.getsitepackages()` and **`:55`**
  `site.getusersitepackages()`. That is `find_sub_dirs_all_sitepackages`, the reader F-F
  targets.
- Nothing else in the bundle or the pack (CuPy included) reads them.
- Effect of the pack prefix: pathfinder's site-packages step now searches the pack first, then
  `<pack>/site-packages/Lib/site-packages` (absent), then the bundle's own prefixes, as before.
  `getusersitepackages()` does not read `PREFIXES` (it uses the user base) and is reached only
  when `ENABLE_USER_SITE` is truthy, which it is not in the frozen process. No reader is
  changed harmfully.
- `sysconfig` reads `sys.prefix` / `sys.base_prefix` (`Lib/sysconfig.py:172-173`, `:650-651`),
  never `site.PREFIXES`.

**The before-record of the whole batch on `54266f5e`** (the F-E shim head; rule check first,
`t3e/rule-check-ff.txt`): the three owned modules with `PYTHONPATH` / `WP61_BUILD_SCRIPT` on
`git archive 54266f5e` give **41 failed, 225 passed** (`t3e/pytest-batch-before-on-54266f5e.log`).

- Failing: every new A r3 test as listed in the fold-in table, the F-F frozen test (`:1169`) and
  the Q2 test (`:1223`).
- Lines in `test_frozen_entry.py` as in the fold-in table: `:174`, `:240`/`:241` x4, `:262`,
  `:436`, `:1171` x10, `:1200`, `:1230` x4, F-E (iii) `:689`.
- Lines in `test_gpu_pack.py`, now: `:826` x10, `:986`, `:1013`, `:1034`.
- Lines in `test_tools_package_build.py`: `:757`, `:766`, `:792`.
- The F-E (i) / (ii) tests and the frozen order test PASS there, as they should: the shim is in
  `54266f5e`. The earlier fold-in before-record on `e0a90bc5` (42 failed) stands beside this one.

| Command (worktree root, Git Bash, `PYTEST_ADDOPTS` unset) | Exit | Summary |
|---|---|---|
| the three owned modules on the final code (`c61f-11`, then `c61f-14` for `test_gpu_pack.py` after ruff's fix) | 0 | 266 passed; 98 passed |
| the same on `54266f5e` (`c61f-12`) | 1 | 41 failed, 225 passed |
| the wider set (the 7 modules, `-m "not gpu"`, `c61f-13`) | 0 | **417 passed, 41 deselected in 33.01 s** |
| `ruff check .` / `ruff format --check .` | 0 / 0 | All checks passed (after `--fix` of 3 SIM300 in the new test) / 322 files already formatted |
| `mypy` / `mypy --strict` on the 6 touched files, win32 and `--platform darwin` | 0 | 160 / 6 / 6 files, no issues |

The harness rule for the pack (CHARC): no non-frozen helper imported from the pack in this part.
`site_readers.py` only reads text, and ran with `-B`. The pack still has 0 `.pyc` files and
`--verify` PASSES.

Owner log md5 `69ed0432c562db9445daecbe8f15fe27` at every check (a check only).
`%LOCALAPPDATA%\Clearwater` is absent. No build and no pack-activating run in this group.

**For the fresh cell's one rebuild and proof.** The handler check reads, from BOTH bundles:
`interpreter_reentry`, `run_interpreter_option`, `isolate_worker_stdin`,
`multiprocessing_reentry` and `main`, plus `MULTIPROCESSING_FLAGS`. Add `multiprocessing_reentry`
to `t3e/handler_check.py`'s list. The gpu_pack loader (`add_site_prefix`) is in the PYZ, not the
entry script, so read it there too. Then the WITH-pack proof (onedir HEIC + video, then onefile),
CHARC's amendment-4 evidence (the canary JSON, the device line, the site flags), the
without-pack regression, `--verify` before and after.

Depth at turn-3 group-2b-3 (A r3 batch) end: 468,982 (wp61-cell6, at its final report; past the 400K stop, the F-F batch landed before the stop message; read by the dispatcher)

## Turn 3 group 2b-4 (the one rebuild and the WITH-pack proof) (2026-11-04 ~14:25-14:41Z)

Fresh cell (implementer-opus-high, wp61-cell7), dispatch
`clearwater-review-evidence/wp6.1/cell/dispatch-9.md`, head at start `49150ccf` (the merge of
main `c7ea0004`). Evidence: `clearwater-review-evidence/wp6.1/cell/t3f/`. This group changed
ONLY this ledger. No STOP condition was met.

- No desktop input was sent and there was no GUI launch. `t2b/gui_check.py` was not run.
  Nothing under `t3c/exp/` was run; its onedir executable was only READ, as the handler
  check's control.
- No network. Nothing under the real `%APPDATA%\Clearwater` or `%LOCALAPPDATA%\Clearwater`
  (the latter absent before and after).
- Every frozen run had APPDATA, LOCALAPPDATA, TEMP / TMP and the five XDG_* variables under
  `work\wp6.1\t3c\appdata\`, every `CUDA_PATH*` removed, and `PATH = C:\Windows\System32;C:\Windows`.
  The read-only window watch ran beside every frozen run (UI Automation per PID of the run's
  tree plus `EnumWindows`, every 0.25 s).
- The two NON-frozen helpers (`t3f/handler_check.py`, `t3f/proof4.py`) import nothing from the
  pack. Both ran with `-B`. The full `--verify` bracketed the group.

**Owner log** `%APPDATA%\Clearwater\logs\clearwater.log`: md5 `69ed0432c562db9445daecbe8f15fe27`
before (14:26:05Z) and after (14:40:07Z) (`t3f/owner-log-md5-{before,after}.txt`; a check only).

### Item 1: the wider run on `49150ccf`

| Command (worktree root, Git Bash, `PYTEST_ADDOPTS` unset) | Exit | Summary |
|---|---|---|
| `uv run --no-sync pytest -q -rs -p no:cacheprovider --timeout 120 --durations=5 --basetemp=<wt>/work/c61g-1 tests/test_gpu_pack.py tests/test_frozen_entry.py tests/test_tools_package_build.py tests/test_jobs_export_process.py tests/test_app_composition.py tests/test_wp42_composition.py tests/test_core_backend.py tests/test_cache_store.py -m "not gpu"` | 0 | **459 passed, 41 deselected in 35.52 s** (slowest 1.03 s, `test_jobs_export_process`) (`t3f/pytest-wider-c61g-1.log`) |
| `ruff check .` / `ruff format --check .` | 0 / 0 | All checks passed / 323 files already formatted |
| `mypy` (strict, configured set) | 0 | no issues in 161 source files |

The merge added `tests/test_cache_store.py` (WP-T8): 459 = 417 (2b-3's last wider run) plus that
module's 42.

### Item 2: both rebuilds (from `49150ccf`; `src` and `tools` clean, only this ledger modified)

| Form | Command (worktree root) | `df -h /c` before | Exit | Wall (shell / PyInstaller) | Result |
|---|---|---|---|---|---|
| onedir | `uv run --no-sync python tools/package/build.py --form onedir --with-ffmpeg > work/wp6.1/build-onedir-t3f.log 2>&1` | 77 GB free (14:27Z) | 0 | 74 s / 65.0 s | `_internal` 234,668,819 B + `Clearwater.exe` 10,677,212 B; 668.3 MiB release with FFmpeg; bundle checks 7.6 s |
| onefile | `... --form onefile --with-ffmpeg > work/wp6.1/build-onefile-t3f.log 2>&1` | 77 GB free (14:28Z) | 0 | 82 s / 79.6 s | `Clearwater.exe` 93,874,026 B (89.5 MiB); 523.9 MiB release; bundle checks 0.7 s |

- `PYINSTALLER_CONFIG_DIR` was set by `build.py` itself, under the output folder.
- Both logs show:
  - `61 hidden imports from 376 pack files`;
  - `hidden-import site (scan; named 1x)`;
  - `hidden-import check: PASS (61 modules, each in the bundle)`;
  - `bundle check: PASS (no cupy, cupyx, cupy_backends, cuda, nvidia, fastrlock, tests ...; no CUDA library; every module's top-level name allowed)`.
- The single warning is the usual `scipy.special._cdflib` (benign). FFmpeg and ffprobe
  9.0.2-full_build-www.gyan.dev were copied beside each executable.
- **The resolved set** is the 61 members of group 2b-3: 60 from the scan, `graphlib` from the
  committed list. Every one of them is passed as `--hidden-import` on the PyInstaller command
  line in both logs. `site` was bundled without complaint.
- Copies: `t3f/build-on{dir,file}-t3f.log`, `t3f/hidden-imports-on{dir,file}-t3f.json`.

**The handler read-out, before any run of the new builds** (`t3f/handler_check.py` ->
`t3f/handler-check-t3f.json`). Method:

- `t3e/handler_check.py` was copied and extended: `multiprocessing_reentry` added, plus
  `MULTIPROCESSING_FLAGS` and the PYZ's `clearwater.gpu_pack`.
- PyInstaller's own `CArchiveReader` read each new `Clearwater.exe`. The entry script
  `__main__` (typecode `s`) and the PYZ entry `clearwater.gpu_pack` were unmarshalled.
  Nothing was executed.
- The comparison is with a compile of `src/clearwater/__main__.py` and
  `src/clearwater/gpu_pack.py` at `49150ccf`, the build's commit.

| Read in each `Clearwater.exe` (onedir and onefile alike) | Result |
|---|---|
| entry script: `interpreter_reentry`, `run_interpreter_option`, `isolate_worker_stdin`, `multiprocessing_reentry`, `main` | present; bytecode AND non-code constants equal the source, each |
| entry script, whole module | 10 of 10 functions equal; module-level bytecode and constants equal |
| `main` names `isolate_worker_stdin` and `multiprocessing_reentry` | yes, both |
| `MULTIPROCESSING_FLAGS` | in the module's names; the constant `("--multiprocessing-fork", "--multiprocessing-resource-tracker")` in its constants |
| `clearwater.__main__` in the PYZ | no (the entry script is the only copy) |
| PYZ `clearwater.gpu_pack.add_site_prefix` | present; bytecode and constants equal the source |
| PYZ `clearwater.gpu_pack.activate` | bytecode equal; its names include `add_site_prefix` (it calls it) |
| PYZ `clearwater.gpu_pack`, whole module | 38 of 38 functions equal; module-level bytecode and constants equal |

**HANDLER CHECK: PASS on both.**

Control: the same check on the `t3c/exp` onedir build, read only
(`t3f/handler-check-t3f-control-t3c-exp.json`), gives `HANDLER CHECK: FAIL`, with 5 `present:
false` entries. So the check distinguishes.

**The second check, executed** (pack folder renamed `14.2.0-cu12.renamed`, window watch
running; `t3f/argv-<form>-<case>.out`, records in `t3f/proof4.jsonl`). A positive control of the
watch came first (`t3f/control.out`): explorer.exe showed 2 UIA elements and 9 visible / 46
hidden windows; this Python showed 0.

| Form | Arguments | Exit | stderr (one line) | Windows (UIA / visible) | Tree | Left |
|---|---|---|---|---|---|---|
| onedir | `-c pass` | 2 | `Clearwater: -c is not supported` | 0 / 0 (1 sample) | 1 PID | none |
| onedir | `-m http.server` | 2 | `Clearwater: -m 'http.server': no GPU pack is loaded` | 0 / 0 (1) | 1 PID | none |
| onedir | `--multiprocessing-fork` | 2 | `Clearwater: multiprocessing children are not supported` | 0 / 0 (1) | 1 PID | none |
| onedir | `--multiprocessing-resource-tracker` | 2 | `Clearwater: multiprocessing children are not supported` | 0 / 0 (1) | 1 PID | none |
| onefile | `-c pass` | 2 | `Clearwater: -c is not supported` | 0 / 0 (9) | bootloader + child, both exit 2 | none; no `_MEI` |
| onefile | `-m http.server` | 2 | `Clearwater: -m 'http.server': no GPU pack is loaded` | 0 / 0 (9) | the same | none; no `_MEI` |
| onefile | `--multiprocessing-fork` | 2 | `Clearwater: multiprocessing children are not supported` | 0 / 0 (8) | the same | none; no `_MEI` |
| onefile | `--multiprocessing-resource-tracker` | 2 | `Clearwater: multiprocessing children are not supported` | 0 / 0 (8) | the same | none; no `_MEI` |

`tasklist` after the eight runs showed no `Clearwater.exe` and no `ffmpeg.exe`.

### Item 3: `--verify` (the pack renamed back; the full walk, Q2)

`build.py --verify <t3c pack>`: exit 0, `PASS (11 distributions; 2701 RECORD rows, each file's
sha256 and size; 2701 files, 2412.6 MiB)` in 4 s (`t3f/verify-1-before.log`). `find` gives 2,701
files under `site-packages` and 0 `.pyc`. The sorted file list's md5 is `27f33db1...`
(`t3f/pack-filelist-before.md5`).

### Item 4: the WITH-pack GPU proof, headless -- PASS on both forms

- **Tool.** `t3f/proof4.py` is `t3e/proof3.py` copied, with the evidence paths moved to `t3f`
  and a fresh per-form kernel cache `appdata\cupy-kernel-cache-t3f-<form>`. The spawn, the
  environment, the tree tracker and the watch are unchanged.
- **Command.** The child command is `<new dist>\Clearwater.exe --export-worker`, built from
  `t3b/headless.EXES`, which points at the `dist-on{dir,file}` paths rebuilt above.
- **Requests.** `heic-ad24-both.heic` -> PNG and `vfr.mp4` -> MP4, c3 defaults, `force_cpu` off,
  encoder `auto`.
- **Working directory.** `work\wp6.1\t3c\runs\<form>`.
- **Order.** onedir HEIC, onedir video, onefile HEIC, onefile video.

| Form | Request (moment) | Exit | Device | Output | Kernels compiled (cache `.cubin` count) | CUDA / CuPy files mapped | Canary children | Windows (UIA / visible) | Left over |
|---|---|---|---|---|---|---|---|---|---|
| onedir | HEIC -> PNG (14:36:18Z, 17.4 s) | **0** | **`GPU`**; log `export heic-ad24-both.heic: ok; device GPU`; no warning | `heic-ad24-both_corrected.png` 37,080 B, ok | 0 -> 52 (first file 14:36:01Z, inside the run) | 67: 59 pack + 8 driver, **0 elsewhere** | **none** | 0 / 0 (62 samples) | none; pack +0 / -0 files |
| onedir | `vfr.mp4` -> MP4 (14:36:52Z, 11.1 s) | **0** | **`GPU`**; `export vfr.mp4: ok; device GPU` | `vfr_corrected.mp4` 55,168 B, ok | 52 -> 62 | 67: 59 pack + 8 driver, 0 elsewhere | none | 0 / 0 (33) | none; +0 / -0 |
| onefile | HEIC -> PNG (14:37:30Z, 21.3 s) | **0** | **`GPU`** | 37,080 B, ok | 0 -> 52 (first file 14:37:11Z) | 67: 59 pack + 8 driver, 0 elsewhere | none | 0 / 0 (70) | none; `_MEI` before [] after []; +0 / -0 |
| onefile | `vfr.mp4` -> MP4 (14:37:47Z, 14.5 s) | **0** | **`GPU`** | 55,168 B, ok | 52 -> 62 | 67: 59 pack + 8 driver, 0 elsewhere | none | 0 / 0 (39) | none; `_MEI` [] / []; +0 / -0 |

- **The process trees.**
  - Each onefile tree is the bootloader plus one `Clearwater.exe --export-worker` child
    (both exit 0).
  - The video trees hold the ffprobe / ffmpeg children of 1.0.0's video path: the probes, the
    encoder detection, the decode, the encode, and their `conhost.exe`.
  - Three short-lived PIDs (one in onedir video, two in onefile video) ended before psutil
    could read them (`NoSuchProcess`; no command line). Each had an ffprobe / ffmpeg / worker
    parent and was gone at the end.
  - The onefile bootloader's two top-level windows are HIDDEN (`PyInstaller Onefile Hidden
    Window` and `Default IME`, `IsWindowVisible` false). There was no UIA element. Neither
    window is a Clearwater window.
- **stderr of every with-pack worker run (one warning, CuPy's own).**
  `...\gpu-pack\14.2.0-cu12\site-packages\cupy\_environment.py:286: UserWarning: CUDA path
  could not be detected. Set CUDA_PATH environment variable if CuPy fails to load.`
  - Reason: `_get_cuda_path` returns `None` for a CUDA 12 wheel layout found through
    site-packages (`cupy/_environment.py:172-179`, "no single root").
  - It is harmless here: the kernels compiled.
  - It goes to the worker's stderr, not to the user.
  - For WP6.3: whether to silence it.
- **DR-125 did not appear.** Every worker run in this group exited 0, with the pack and without
  it. Every frozen worker run before the F-E shim exited `3221225477`. This fits F-E's side
  observation, but this group did not test the cause.

**The canary, the kernel, pathfinder, the site flags.**

1. **CuPy's canary child: NONE in any of the four runs.**
   - The tracker saw no `-m` child and no `dynamic_lib_subprocess` command line.
   - So pathfinder's search steps that run before its CTK-root canary found what CuPy asked
     for. The canary had nothing to do.
   - The dispatch expected a canary child with `status: found`. That premise does not hold on
     the new builds, and it is not one of the STOP conditions. Also, pathfinder's success
     status is spelled `"ok"`, not `"found"` (`cuda/pathfinder/_dynamic_libs/subprocess_protocol.py:16-17`:
     `STATUS_OK = "ok"`, `STATUS_NOT_FOUND = "not-found"`).
   - To record the canary's own behaviour, I ran its exact command standalone through the
     frozen `-m` handler, both forms, the pack present, under the watch:
     `Clearwater.exe -m cuda.pathfinder._dynamic_libs.dynamic_lib_subprocess canary cudart`
     (and `... canary nvrtc`).
   - Result: exit 0 in 0.27-0.28 s (onedir) and 2.4-2.7 s (onefile, bootloader included), no
     window, nothing left, payload `{"status": "not-found", "abs_path": null}` for both.
   - The canary uses SYSTEM search only (`dynamic_lib_subprocess.py:31-42`,
     `LOADER.load_with_system_search`). With `PATH` = Windows only and no toolkit, it finds no
     CUDA runtime, and that is correct.
   - It was not needed: see 3.
   - Records: `t3f/probe-<form>-canary-{cudart,nvrtc}.out`.
2. **The kernels compiled with the pack's NVRTC.**
   - `nvrtc64_120_0.dll` and `nvrtc-builtins64_129.dll` were mapped from the pack's
     `nvidia\cuda_nvrtc\bin` in all four runs.
   - Each form's kernel cache started EMPTY:
     - the HEIC run wrote 52 `.cubin` files, timestamped inside the run;
     - the video run wrote 10 more (62).
   - The device stayed `GPU` with no warning. The device test kernel's failure (F-E's timeout,
     F-F's `Failed to find CUDA headers`) is gone.
3. **`cuda.pathfinder` and the pack (the route: frozen `-m` runs of the pack's own
   `dynamic_lib_subprocess` module under the pack rules; NOT the run's log, which names no
   path).**
   - Frozen `-m ... load cudart` gives `{"status": "ok", "abs_path": "<pack>\site-packages\nvidia\cuda_runtime\bin\cudart64_12.dll"}`.
   - Frozen `-m ... load nvrtc` gives `{"status": "ok", "abs_path": "<pack>\site-packages\nvidia\cuda_nvrtc\bin\nvrtc64_120_0.dll"}`.
   - Both forms give the same result, exit 0, no window (`t3f/probe-<form>-load-{cudart,nvrtc}.out`).
   - The canary above shows that system search does NOT reach the pack. So these PACK paths
     came from pathfinder's site-packages step: `search_platform.py:30/54/95` ->
     `find_sub_dirs_all_sitepackages` -> `site.getsitepackages()`.
   - `find_nvidia_header_directory`'s step 1 calls the SAME function
     (`_headers/find_nvidia_headers.py:86`) with `nvidia/cuda_runtime/include` and
     `nvidia/cuda_nvrtc/include`, and the pack has both folders.
   - **`find_nvidia_header_directory("cudart")` / `("nvrtc")` themselves were NOT printed
     from a frozen process.** No pack module has a `__main__` that calls them. The only `-m`
     runnable pack modules are `dynamic_lib_subprocess` (modes `canary` / `load`, no header
     mode) and three `cupyx/tools` scripts. Nothing may be planted in the pack.
   - **The pack paths for the headers are therefore INFERRED, from four facts:**
     - the same reader returns the pack in the frozen process;
     - the kernels compiled in an environment identical to F-F's failing one except for
       `add_site_prefix`;
     - 2b-3's base-CPython reproduction printed exactly `<pack>\nvidia\cuda_runtime\include` /
       `<pack>\nvidia\cuda_nvrtc\include` once the pack was in `site.PREFIXES`
       (`t3e/headers-repro-prefixes.out`);
     - F-F's run showed that no other header source is reachable here (CUDA_PATH unset, no
       conda, no toolkit headers found by any other step).
4. **The site flags of the frozen process.**
   - **`site.PREFIXES` holds the pack's `site-packages`: OBSERVED in effect** (item 3:
     `site.getsitepackages()` yields it in the frozen process).
   - **That it is at index 0: NOT observed directly.** It comes from:
     - the bundled `add_site_prefix` being byte-identical to the source (the read-out above);
     - `test_a_frozen_activation_puts_the_pack_folder_first_in_site_prefixes`;
     - the bundle's other prefixes (`_internal`) holding no `nvidia` folder, so the order
       cannot change a lookup today.
   - **`ENABLE_USER_SITE` falsy, and no user site on `sys.path`: OBSERVED again on the new
     builds**, by 2b-3's plant probe:
     - two EMPTY folders, `cuda\` and `nvidia\nvjpeg\bin\`, in the REDIRECTED user site
       `t3c\appdata\Roaming\Python\Python312\site-packages\` (`t3f/usersite-plant.txt`;
       removed afterwards);
     - frozen `-m ... load nvjpeg`, both forms.
   - **The plant probe's result.**
     - The `-m` was ACCEPTED. An empty `cuda\` on `sys.path` would be a second namespace
       portion outside the pack and would be refused.
     - The not-found message does not list the user-site `nvidia\nvjpeg\bin`:
       `Failure finding "known nvjpeg DLL": No such file: known nvjpeg DLL, No such file: known nvjpeg DLL`.
       Pathfinder adds the user site only `if site.ENABLE_USER_SITE`.
     - Exit 0, no window, nothing left (`t3f/usersite-probe-{onedir,onefile}.out`).
     - 2b-3's base-CPython control (`t3e/usersite-control.out`) showed that both probes flip
       when the user site is enabled.
   - The exact `sys.flags.no_site` / `no_user_site` values remain as 2b-3 reported them
     (reasoned, not printed).

**Every mapped CUDA / CuPy / NVRTC file over the four runs' trees** (`t3f/mapped-cuda-files.tsv`;
the same 67 paths in each of the four runs; psutil `memory_maps()` sampled every 0.05 s over
every live PID except ffmpeg / ffprobe):

- **Pack, 59 (88.1 %)**, under `<wt>\work\wp6.1\t3c\appdata\Local\Clearwater\gpu-pack\14.2.0-cu12\site-packages\`:
  - `nvidia\cublas\bin\cublas64_12.dll`
  - `nvidia\cublas\bin\cublasLt64_12.dll`
  - `nvidia\cuda_nvrtc\bin\nvrtc64_120_0.dll`
  - `nvidia\cuda_nvrtc\bin\nvrtc-builtins64_129.dll`
  - 55 extension modules: 45 under `cupy\`, 9 under `cupy_backends\`, 1 under `cupyx\`.
- **NVIDIA driver, 8 (11.9 %):**
  - `C:\Windows\System32\nvcuda.dll`
  - under `C:\Windows\System32\DriverStore\FileRepository\nvami.inf_amd64_00e5dc1fb00a1261\`:
    `nvcuda64.dll`, `nvapi64.dll`, `nvapi64_impl.dll`, `nvdiagclt64.dll`, `nvdxgdmal64.dll`,
    `nvobjectloader64.dll`, `Display.NvContainer\NvMessageBus.dll`.
- **Elsewhere: 0.** The share is 100 % pack + driver, as expected.
- The filter: any file under the pack root, or a DLL whose name starts `cu` / `nv` or contains
  `cuda`. No CUDA toolkit, `CUDA_PATH` or bundle `_internal` copy appears.

**Leftovers.** After every run: no live PID of the run's tree; `tasklist` shows no
`Clearwater.exe`, `ffmpeg.exe` or `ffprobe.exe`; the redirected `TEMP\_MEI*` is empty before and
after every onefile run. The pack gained and lost 0 files in every run.

**For WP6.3 (observed, not acted on).** The NVIDIA driver keeps its JIT cache under
`%APPDATA%\NVIDIA\ComputeCache`. Here that is the redirected tree's (created in 2b-2, used
again now). On a user's machine it is the user's real APPDATA; it is the driver's, not
Clearwater's.

### Item 5: the WITHOUT-pack regression (pack renamed `14.2.0-cu12.renamed`), then `--verify`

| Form | Request (moment) | Exit | Device and warning (AD-9's text) | Log | Output | CUDA files | Windows | Left |
|---|---|---|---|---|---|---|---|---|
| onedir | HEIC -> PNG (14:39:49Z, 0.6 s) | 0 | **`CPU: CuPy not installed`**; warning `Processed on the CPU (CPU: CuPy not installed).` | `CuPy not installed: No module named 'cupy'` | `heic-ad24-both_corrected.png` 37,104 B, ok | 0 | 0 / 0 (2) | none |
| onefile | HEIC -> PNG (14:39:54Z, 2.8 s) | 0 | the same | the same | 37,104 B, ok | 0 | 0 / 0 (10) | none; no `_MEI` |

- The device, the warning, the log line and the output size equal 2b-2's without-pack rows.
  The exit is now 0, where it was `3221225477` there (DR-125, above).
- The GPU PNG (37,080 B) and the CPU PNG (37,104 B) differ in size, as the two backends' float
  paths do.
- **`--verify` after the runs (pack renamed back): PASS**, with the same line and figures:
  2701 rows, 2701 files, 2412.6 MiB (`t3f/verify-2-after.log`).
- 0 `.pyc` files.
- The sorted file list's md5 is `27f33db1...` again (`t3f/pack-filelist-after.md5`).
- **No run wrote into the pack.**

### Files changed this group

`docs/proofs/wp6.1-ledger.md` only. Evidence tools (not product, not committed):
`t3f/handler_check.py`, `t3f/proof4.py`, `t3f/uia_watch.ps1` (copied unchanged). The new builds
are at `work/wp6.1/dist-on{dir,file}/` (of `49150ccf`); they replace `62198baf`'s. The pack is
unchanged at `work/wp6.1/t3c/appdata/Local/Clearwater/gpu-pack/14.2.0-cu12`.

Depth at turn-3 group-2b-4 end: 210,615 (wp61-cell7, at its yield; read by the dispatcher)

## Turn 3 group 2b-5 (Reviewer A r4 fold-in) (2026-11-04 ~14:45-15:00Z)

Same cell (wp61-cell7), dispatch `clearwater-review-evidence/wp6.1/cell/dispatch-10.md`, on
Reviewer A round 4 (`clearwater-review-evidence/wp6.1/A/r4/review.txt`, on `e0a90bc5..49150ccf`:
one MAJOR, four MINOR, two ADVISORY). Evidence: `clearwater-review-evidence/wp6.1/cell/t3g/`.

- MID-BUILD YIELD: no build and no frozen run. Nothing under the pack was run or imported;
  `--verify` read it once.
- No desktop input, no GUI launch, no network. Nothing under the real `%APPDATA%\Clearwater`
  or `%LOCALAPPDATA%\Clearwater` (the latter absent).
- `jobs/export_process.py`, `io/video/pipes.py` and `app/export_worker.py` are untouched.
- Code + tests: commit `08a96243`.

**Owner log** md5 `69ed0432c562db9445daecbe8f15fe27` before (14:55:16Z) and after (14:58:57Z)
(`t3g/owner-log-md5-{before,after}.txt`; a check only).

### The grammar, derived by execution (A r4 #1)

`t3g/derive_grammar.py` -> `t3g/grammar-letters.txt`. It runs only the dev interpreter
(`.venv\Scripts\python.exe`, CPython 3.12.13, MSC v.1944, the bundle's version) with `-B` and
`-c pass`, with stdin from NUL and the `PYTHON*` variables removed. No product code runs.

- For every ASCII letter L, it runs `-<L> -c pass`.
- Where that fails, it also runs `-<L> x -c pass` and `-<L>x -c pass`.
- It then runs every long option `--help-all` names, with and without values, in the `=` form,
  and abbreviated.

| Class | Letters / options | Evidence (exit codes) |
|---|---|---|
| FLAG (no value; may be clustered) | `b d i q s t u v x B E I O P R S` (16) | `-<L> -c pass`: 0, no output |
| VALUE (the next argument, or the rest of the cluster) | `W X` | `-<L> -c pass`: 2 (it took `-c` as its value); `-<L> x -c pass` and `-<L>x -c pass`: 0 |
| INFORMATIONAL (prints, exits) | `h V`, also `-?` | 0 with usage / version text |
| RE-ENTRY (by definition) | `m c` | -- |
| REJECTED | the other 30 letters | 2, `Try python -h` |
| `--check-hash-based-pycs <always\|default\|never>` | accepted, also around `-I`, `-Wignore`, `-Xutf8` | 0 |
| `--check-hash-based-pycs=always` / `=never`; a missing value; `bogus`; `--check-hash-based-pyc` / `--check-hash` (abbreviations) | REJECTED | 2 |
| `--help`, `--help-env`, `--help-xoptions`, `--help-all`, `--version` | INFORMATIONAL | 0 with text |
| `--help-al`, `--vers`, `--other` | REJECTED | 2 |
| `-R -m this`, `-t -c pass`, `-Rt` / `-tR -c pass` | accepted | 0 |

So `FLAG_LETTERS` gains `R` and `t` (it had 14). `VALUE_LETTERS` stays `WX`.

The new `LONG_VALUE_OPTIONS` is `{"--check-hash-based-pycs": {"always", "default", "never"}}`.
Its value is ALWAYS the next argument. The `=` form, a missing or unknown value, an
abbreviation, an informational long option and every other `--x` are not re-entries, so they
go to the GUI, as CPython refuses them or prints and exits.

### The fold-in table

| # (r4) | Disposition | Fix (file) | Test(s) | On `49150ccf` |
|---|---|---|---|---|
| 1 MAJOR | FIX | `__main__`: `FLAG_LETTERS` = the executed FLAG set (adds `R`, `t`). New `LONG_VALUE_OPTIONS`: `interpreter_reentry` consumes `--check-hash-based-pycs <accepted value>` like a separate `-W` / `-X` value. Any other `--...` token (the `=` form, a wrong or missing value, `--help*`, `--version`, unknown) gives None (GUI). The docstrings name the derivation. | grammar table +20 rows: r4's `-R -m x`, `-t -m x`, `-Rt -c pass`, `--check-hash-based-pycs always -m x`, `... never -c pass`, plus `-tRIm x`, `default -I -m x`, `-I ... always -Xutf8 -m x`; the GUI rows `=always`, the option alone, `... -m x` (no value), `bogus`, `--check-hash`, `--help`, `--help-env`, `--help-xoptions`, `--help-all`, `--version`, `-a`, `-Rp`. NEW `test_the_option_letters_are_cpythons_by_execution`: the letter loop, run live against this interpreter, must EQUAL `FLAG_LETTERS` / `VALUE_LETTERS`. NEW `test_the_long_options_are_cpythons_by_execution`: the three values exit 0; `=always`, `bogus`, a missing value, the option alone, `--check-hash` and `--other` fail; the five informational options print. Main-level: `test_every_spelling_of_dash_m_runs_a_pack_module` +3 (`-R`, `-t`, `--check-hash-based-pycs always`); `..._dash_c_..._refuses` +2 (`-Rt -c pass`, `--check-hash-based-pycs never -c pass`); `test_qt_options_..._reach_the_gui` +2 (`=always -m x`, the option alone). | `:1485` x8 (the 8 new re-entry rows); `:1526` (the letter test: `t`/`R` missing); `:1536` (`AttributeError`: no `LONG_VALUE_OPTIONS`); `:51` x3 (the GUI blocker refused `clearwater.app.main`: no window); `:1644` x2 (the GUI stand-in ran: 3, not 2). The new GUI rows PASS there by design. |
| 2 MINOR | FIX | `gpu_pack.add_site_prefix`: every entry whose `normcase(normpath(...))` equals the folder's is removed, and the canonical `str(site_packages)` is put first. `site.PREFIXES[:] = ...` keeps the list object. Returns False only when that is already the state. New helper `_prefix_key`. | NEW `test_another_spelling_of_the_pack_folder_is_replaced_not_kept` (Windows: r4's exact `["C:/PACK/site-packages/", "C:/bundle"]` + `Path("C:/pack/site-packages")` -> `["C:\pack\site-packages", "C:/bundle"]`, then False); NEW `test_every_existing_equivalent_prefix_is_removed_before_the_one_canonical_entry` (any platform: a trailing-separator copy, the exact entry twice and a doubled-separator copy all go; other prefixes keep their order; the same list object). | `test_gpu_pack.py:1187`, `:1203` |
| 3 MINOR | FIX (tests only) | -- | F-E (i): the child also reports `os.get_inheritable(sys.stdin.fileno())`, which must be `False`. F-E (ii): the record's `inheritable` must be `False`. NEW `test_the_end_of_the_request_pipe_reaches_the_workers_reader_through_the_shim[parent-closes, parent-dies]`: a child runs the frozen branch with the REAL `export_worker.main`; a stand-in `run` reads the request, then runs the REAL `_watch_stdin` on the private reader. The parent closes its end, or a middle process holding the write end is KILLED. The watcher must see the end of the stream (`eof` true, well inside its 30 s bound), with fd != 0 and not inheritable. | All PASS on `49150ccf`: the shim there already makes a non-inheritable duplicate. The protection is in the tests. **Mutation** (`t3g/mutation-inheritable.diff`: `os.set_inheritable(private, True)` after the `dup`, on a copy of the final `src`; `t3g/pytest-mutation-inheritable.log`): **4 failed** (both F-E tests and both pipe-end cases), each at its `inheritable is False` assertion. |
| 4 MINOR | FIX, fail closed (the dispatcher's form; CHARC may re-rule) | `isolate_worker_stdin`: only `os.dup(0)` raising `OSError` with `errno.EBADF` returns False (no standard input); any other errno raises. Every later step (`os.open(devnull)`, `dup2`, `SetStdHandle`, `open(private, "rb")`, `TextIOWrapper`) is in one `try`. On any exception: the null descriptor is closed (inner `finally`); `private` is closed by the reader that owns it, or directly; then it re-raises. `main` catches `Exception` from the shim and returns `_refuse("worker stdin isolation failed: <type>")`, status 2, BEFORE `gpu_pack.activate`, any log and the worker import. New `STDIN_REFUSAL` constant; README section updated. | NEW `test_a_failed_stdin_isolation_ends_the_frozen_worker_before_anything_else[open-null (PermissionError), dup2, set-std-handle (win32 only), reader-open (ValueError), reader-wrap (TypeError), dup-emfile]`, each in a fresh `-I` child (NoGui prelude; worker import blocked and recorded; loader and log set-up stubbed and recorded). Each asserts: status 2; stderr EXACTLY `Clearwater: worker stdin isolation failed: <type>\n`; nothing ran; no worker import attempted; the open descriptor set (fstat of 0-255) is the same before and after (no leak). NEW `test_a_process_without_a_standard_input_runs_the_worker_branch_on` (`EBADF`): the branch goes on (loader, worker import attempted), no refusal line, no descriptor left. | `:915` x5 (the 5 non-EMFILE modes: an exception escaped `main`, so the child's traceback and no JSON) and `:917` x1 (`dup-emfile`: the old code took it as "no standard input" and ran on). The EBADF test PASSES there by design: it pins the kept fallback. |
| 5 MINOR | FIX | `main`: `frozen and multiprocessing_reentry(...)` is checked FIRST, before `prepend_executable_folder()`. | Both multiprocessing refusal tests set `PATH` to `/x;/y` and assert it unchanged after the refusal, as well as `calls == []` and no blocked import. | `:250` x4, `:274` (`PATH` gained the executable's folder) |
| 6 ADVISORY | FIX | The `__main__` module docstring: the branches in `main`'s order; multiprocessing before `PATH`; the shim's fail-closed refusal; "Every branch that can import CuPy ... runs the loader before it; a refusal ... ends before the loader" replaces "On every branch". `REFUSED_STATUS` now names every refusal. `gpu_pack.activate`: "its worker, `-m` and GUI branches; its refusals end before it". `test_gpu_pack.py` ownership test docstring: the FULL check does list a nested extra (Q2). `tools/package/README.md` (the `--verify` paragraph: the unlisted-file walk; the shim paragraph: fails closed) and `build.py` `verify_pack` docstring (the walk). | docs only | n/a |
| 7 ADVISORY (OUT of envelope) | BANK | none | none | n/a |

**Banked (r4 #7), for the report's limits and for WP6.3 (CHARC bae5dba5 (4), verbatim):** the
full --verify does not follow directory links; WP6.3: the full --verify rejects any reparse
point / symlink under the pack, and the downloader never creates one.

### Commands (worktree root, Git Bash, `PYTEST_ADDOPTS` unset; logs in `t3g/`)

| Command | Exit | Summary |
|---|---|---|
| Rule check first (`t3g/rule-check.txt`): every entry-point call site in `tests/test_frozen_entry.py` / `tests/test_gpu_pack.py` listed. The guards of the new / changed sites: the in-process `calls` + `_fresh_entry` + `_fake_gui`; the children's NoGui prelude + `_app_data_environ`; the parent-dies middle passes that environment on; bounded timeouts. | -- | OK on the new and the old revision |
| BEFORE-record: the three owned modules with `PYTHONPATH` / `WP61_BUILD_SCRIPT` on `git archive 49150ccf src tools` (`c61g-5`, then `c61g-6` with `-rf` for the names; `t3g/pytest-before-on-49150ccf{,-rf}.log`) | 1 | **28 failed, 278 passed** (lines in the table above) |
| the three owned modules on the final code (`c61g-7`) | 0 | **306 passed in 17.40 s** (266 before this batch, +40) |
| the WIDER run (dispatch-9 item 1's 8 modules, `-m "not gpu"`, `--timeout 120`, `c61g-8`) | 0 | **499 passed, 41 deselected in 41.55 s** (459 + 40); slowest 2.77 s, the letter-by-execution test |
| mutation `os.set_inheritable(private, True)` (`c61g-9`, the copy of the final `src` first on `PYTHONPATH`) | 1 | 4 failed, at the `inheritable is False` lines |
| `ruff check .` / `ruff format --check .` | 0 / 0 | All checks passed / 323 files already formatted |
| `mypy` (strict, configured set) | 0 | no issues in 161 source files |
| `mypy --strict` on the 5 touched Python files, win32 and `--platform darwin` | 0 / 0 | no issues in 5 source files, each |
| `build.py --verify` (full) on the t3c pack, read only (`t3g/verify.log`) | 0 | PASS: 2701 rows, 2701 files, 2412.6 MiB; 0 `.pyc` |

Every pytest run here used `-p no:cacheprovider` and `--timeout 120`. No test child was left
(psutil, by command line). The owner-log md5 was unchanged after the before-record runs (14:55:36Z
and again at the end).

### Self-review (suspected / confirmed / rejected / fixed)

1. `OSError(errno.EACCES, ...)` is constructed as `PermissionError`, so the refusal line names
   `PermissionError`, not `OSError`. Confirmed by the first run (1 failure). The behaviour is
   right: the line names the real type. The test's expectation was fixed.
2. A docstring with an escaped backslash tripped ruff D301. Confirmed. Reworded ("a forward
   slash or a backslash").
3. Ruff's SIM300 (three Yoda comparisons) and RUF100 (an unused `noqa: BLE001`). Confirmed.
   Fixed with `ruff --fix` on the touched files; ruff format then reflowed one file.
4. A bash heredoc collapsed a `\\n` in a scripted test edit. Confirmed: its own assertion
   refused to write. Redone with the Edit tool; 0 CR in every blob.
5. Suspected: the shim's `except BaseException` re-raises `KeyboardInterrupt` past `main`'s
   `except Exception`. Confirmed. Kept: an interrupt is not an isolation failure, and the
   descriptors are closed before it propagates.
6. Suspected: `--check-hash-based-pycs` consumed before the `--` check could hide `--`.
   REJECTED: `--` is not a key of `LONG_VALUE_OPTIONS`, and the table's `--` rows pass.

A second pass found nothing new.

### CHARC's amendment to dispatch-10 (ruling `bae5dba5`, relayed by the dispatcher), folded in

**Timing:** the amendment asked for this BEFORE the code commit. It reached me after
`08a96243` was committed, so it is a follow-up commit (below). Nothing was rebuilt.

| Item | Fold-in (file) | Test | Result on the old code |
|---|---|---|---|
| (1) the grammar records its CPython | `__main__`: `GRAMMAR_PYTHON_VERSION` = `"3.12.13 (main, Mar  3 2026, 15:01:35) [MSC v.1944 64 bit (AMD64)]"` and `GRAMMAR_PYTHON_VERSION_INFO` = `(3, 12, 13, "final", 0)`. Both were read from the deriving interpreter: `sys.version` and `tuple(sys.version_info)`. `t3g/grammar-letters.txt` also carries the `version_info` line now. The rule is unchanged: run-modifier long options are consumed like `-W` / `-X`; `--help*`, `--version` and unknown `--x` reach the GUI. | NEW `test_the_grammar_table_was_derived_from_this_python_minor_version`: the version string matches the tuple, and `sys.version_info[:2]` must EQUAL the recorded `[:2]`; otherwise it FAILS with "re-derive it". | `49150ccf`: FAILS (no constant). Mutation `(3, 13, 0, "final", 0)` on a copy of the final `src` (`t3g/pytest-amend-mutation-version.log`): FAILS, with the re-derive message. |
| (2) #4 fail closed | CONFIRMED as built in `08a96243`; no change | -- | -- |
| (3) #5: the refusal is the FIRST statement after the arguments are read | `main`: `if getattr(sys, "frozen", False) and multiprocessing_reentry(arguments): return _refuse(...)` follows `arguments = ...` directly. The `frozen = ...` local now comes after it. | the two multiprocessing tests, unchanged (PATH observed) | `49150ccf`: 5 FAIL (`t3g/pytest-amend-before-on-49150ccf.log`) |
| (4) #7's ledger line | the "Banked (r4 #7)" line above now reads as CHARC worded it | -- | -- |

| Command | Exit | Summary |
|---|---|---|
| the three owned modules (`c61g-10`) | 0 | **307 passed in 30.48 s** (+1) |
| the WIDER run (`c61g-11`) | 0 | **500 passed, 41 deselected in 45.35 s** |
| the amendment's tests on `49150ccf` (`c61g-12`; no entry point in the new test, rule unchanged for the other two) | 1 | 6 failed (the version test + the 5 multiprocessing cases) |
| `ruff check .` / `ruff format --check .` / `mypy` / `mypy --strict` (2 touched files, win32 and `--platform darwin`) | 0 | clean; 323 files formatted; 161 files no issues; 2 / 2 files no issues |

The owner-log md5 was `69ed0432c562db9445daecbe8f15fe27` after these runs.

Depth at turn-3 group-2b-5 end: 371,271 (wp61-cell7, at its final report; read by the dispatcher)

## Turn 3 group 2b-6 (the rebuild of the r4 fold-in and the re-proof) (2026-11-04 ~15:07-15:22Z)

Fresh cell (implementer-opus-high, wp61-cell8), dispatch
`clearwater-review-evidence/wp6.1/cell/dispatch-11.md`, head at start `926bfdfa` (the r4 fold-in
`08a96243` + `34f0e15e`, CHARC's pin `09cbba2c`, ledger `926bfdfa`). Evidence:
`clearwater-review-evidence/wp6.1/cell/t3h/`. This group changed ONLY this ledger. No STOP
condition was met.

- No desktop input, no GUI launch; no grammar row whose result is "GUI" was run frozen.
  `t2b/gui_check.py` was not run. Nothing under `t3c/exp/` was run; its onedir executable was
  only READ, as the read-out's control.
- No network. Nothing under the real `%APPDATA%\Clearwater` or `%LOCALAPPDATA%\Clearwater` (the
  latter absent before and after).
- Every frozen run had APPDATA, LOCALAPPDATA, TEMP / TMP and the five XDG_* variables under
  `work\wp6.1\t3c\appdata\`, every `CUDA_PATH*` removed, `PATH = C:\Windows\System32;C:\Windows`,
  and the read-only window watch beside it (UI Automation per PID of the run's tree plus
  `EnumWindows`, every 0.25 s). The positive control came first (`t3h/control.out`, 15:15:27Z):
  explorer.exe 2 UIA elements, 9 visible / 46 hidden windows; this Python 0.
- Only the two NEW builds below were run. The two non-frozen helpers (`t3h/handler_check.py`,
  `t3h/proof4.py`) import nothing from the pack; both ran with `-B`; the full `--verify`
  bracketed every pack-activating run.

**Owner log** `%APPDATA%\Clearwater\logs\clearwater.log`: md5 `69ed0432c562db9445daecbe8f15fe27`
before (15:07:08Z) and after (15:21:22Z) (`t3h/owner-log-md5-{before,after}.txt`; a check only).

### Item 1: the wider run on `926bfdfa`

| Command (worktree root, Git Bash, `PYTEST_ADDOPTS` unset) | Exit | Summary |
|---|---|---|
| `uv run --no-sync pytest -q -rs -p no:cacheprovider --timeout 120 --durations=5 --basetemp=<wt>/work/c61h-1 tests/test_gpu_pack.py tests/test_frozen_entry.py tests/test_tools_package_build.py tests/test_jobs_export_process.py tests/test_app_composition.py tests/test_wp42_composition.py tests/test_core_backend.py tests/test_cache_store.py -m "not gpu"` | 0 | **500 passed, 41 deselected in 43.21 s** (the 2b-5 figure; slowest 1.10 s) (`t3h/pytest-wider-c61h-1.log`) |
| `ruff check .` / `ruff format --check .` | 0 / 0 | All checks passed / 323 files already formatted |
| `mypy` (strict, configured set) | 0 | no issues in 161 source files |

### Item 2: both rebuilds (from `926bfdfa`; `src` and `tools` clean, only this ledger modified)

| Form | Command (worktree root) | `df -h /c` before | Exit | Wall (shell / build.py) | Result |
|---|---|---|---|---|---|
| onedir | `uv run --no-sync python tools/package/build.py --form onedir --with-ffmpeg > work/wp6.1/build-onedir-t3h.log 2>&1` | 77 GB free (15:08Z) | 0 | 86 s / 75.9 s | `_internal` 234,668,819 B + `Clearwater.exe` 10,678,892 B; 668.3 MiB release with FFmpeg; bundle checks 7.4 s |
| onefile | `... --form onefile --with-ffmpeg > work/wp6.1/build-onefile-t3h.log 2>&1` | 77 GB free (15:10Z) | 0 | 85 s / 81.6 s | `Clearwater.exe` 93,875,800 B (89.5 MiB); 523.9 MiB release; bundle checks 0.9 s |

- Both logs: `61 hidden imports from 376 pack files`; `hidden-import site (scan; named 1x)`;
  `hidden-import check: PASS (61 modules, each in the bundle)`; `bundle check: PASS (no cupy,
  cupyx, cupy_backends, cuda, nvidia, fastrlock, tests ...)`. The one warning is the usual
  `scipy.special._cdflib`. FFmpeg / ffprobe 9.0.2-full_build-www.gyan.dev copied beside each
  executable.
- **The resolved set** (`t3h/hidden-imports-on{dir,file}-t3h.json`): 61 members, EQUAL to 2b-4's
  `t3f/hidden-imports-on{dir,file}-t3f.json` (compared as JSON). Every member is passed as
  `--hidden-import` on the PyInstaller line of both logs. Logs copied to
  `t3h/build-on{dir,file}-t3h.log`.
- The executables grew by 1,680 B (onedir) and 1,774 B (onefile) over 2b-4's: the r4 fold-in's
  code in the entry script.

**The read-out, before any run of the new builds** (`t3h/handler_check.py` ->
`t3h/handler-check-t3h.json`). Method:

- `t3f/handler_check.py` copied and extended. PyInstaller's own `CArchiveReader` read each new
  `Clearwater.exe`; the entry script `__main__` (typecode `s`) and the PYZ entry
  `clearwater.gpu_pack` were unmarshalled. Nothing was executed.
- The comparison is with a compile of `git show 926bfdfa:src/clearwater/__main__.py` and
  `...gpu_pack.py` (`t3h/src-926bfdfa/`; byte-equal to the worktree's files), the build's commit.
- Functions are now keyed by `co_qualname` (2b-4 keyed by `co_name`, so nested names merged:
  its "38 of 38" for `gpu_pack` is 53 by qualified name), and each compares bytecode AND
  non-code constants.
- The six constants are rebuilt from the BUNDLE's module bytecode by a stack walker over the
  constant-building opcodes only (`LOAD_CONST`, `BUILD_SET` / `SET_UPDATE`, `BUILD_MAP`,
  `BUILD_TUPLE`, a `CALL` of the name `frozenset` evaluated with the reader's own builtin); the
  same walk over the source compile gives the expected values.

| Read in each `Clearwater.exe` (onedir and onefile alike) | Result |
|---|---|
| entry script: `interpreter_reentry`, `run_interpreter_option`, `isolate_worker_stdin`, `multiprocessing_reentry`, `main` | present; bytecode AND constants equal the source, each |
| entry script, every function | **10 of 10 equal** (by qualified name, none missing, none extra); module-level bytecode and constants equal |
| `main` names `isolate_worker_stdin` and `multiprocessing_reentry` | yes, both |
| `FLAG_LETTERS` | `frozenset("bBdEiIOPqRsStuvx")`: 16 letters, **`R` and `t` in it**; equal to the source |
| `VALUE_LETTERS` | `frozenset("WX")`; equal |
| `LONG_VALUE_OPTIONS` | `{"--check-hash-based-pycs": frozenset({"always", "default", "never"})}`; equal |
| `MULTIPROCESSING_FLAGS` | `("--multiprocessing-fork", "--multiprocessing-resource-tracker")`; in the module's names and constants; equal |
| `GRAMMAR_PYTHON_VERSION` | `"3.12.13 (main, Mar  3 2026, 15:01:35) [MSC v.1944 64 bit (AMD64)]"`; equal |
| `GRAMMAR_PYTHON_VERSION_INFO` | `(3, 12, 13, "final", 0)`; equal |
| `clearwater.__main__` in the PYZ | no (the entry script is the only copy) |
| PYZ `clearwater.gpu_pack.add_site_prefix` | present; bytecode and constants equal the source |
| PYZ `clearwater.gpu_pack.activate` | bytecode and constants equal; its names include `add_site_prefix` |
| PYZ `clearwater.gpu_pack`, every function | **53 of 53 equal** (by qualified name); module-level bytecode and constants equal |

**READ-OUT: PASS on both. Build commit `926bfdfa`.**

Control: the same check on the `t3c/exp` onedir build, read only
(`t3h/handler-check-t3h-control-t3c-exp.json`): **`HANDLER CHECK: FAIL`**, exit 1. Its entry
script has 4 of the 10 functions (1 equal); `interpreter_reentry`, `run_interpreter_option`,
`isolate_worker_stdin`, `multiprocessing_reentry` absent; none of the six constants found.

### Item 3: the refusals (pack renamed `14.2.0-cu12.renamed`, the watch running)

`t3h/proof4.py argv --form <f> --label <l> --timeout 60 -- <arguments>`; stdin an empty pipe;
outputs `t3h/argv-<form>-<label>.out`, records in `t3h/proof5.jsonl`. `run_argv` now also
snapshots every file under the redirected tree (`t3c\appdata`, 3,078 files: size and mtime)
before and after each run.

| Arguments | Exit (onedir / onefile) | stderr (one line, both forms) | Windows (UIA / visible) | Tree | Left | Redirected tree |
|---|---|---|---|---|---|---|
| `-c pass` | 2 / 2 | `Clearwater: -c is not supported` | 0 / 0 | 1 PID / bootloader + child, both 2 | none; no `_MEI` | 0 created, 0 changed, 0 removed |
| `-m http.server` | 2 / 2 | `Clearwater: -m 'http.server': no GPU pack is loaded` | 0 / 0 | the same | none; no `_MEI` | 0 / 0 / 0 |
| `--multiprocessing-fork` | 2 / 2 | `Clearwater: multiprocessing children are not supported` | 0 / 0 | the same | none; no `_MEI` | **0 / 0 / 0 (no log file)** |
| `--multiprocessing-resource-tracker` | 2 / 2 | `Clearwater: multiprocessing children are not supported` | 0 / 0 | the same | none; no `_MEI` | **0 / 0 / 0 (no log file)** |
| `-R -c pass` (new) | 2 / 2 | `Clearwater: -c is not supported` | 0 / 0 | the same | none; no `_MEI` | 0 / 0 / 0 |
| `-t -m http.server` (new) | 2 / 2 | `Clearwater: -m 'http.server': no GPU pack is loaded` | 0 / 0 | the same | none; no `_MEI` | 0 / 0 / 0 |
| `-Rt -c pass` (new) | 2 / 2 | `Clearwater: -c is not supported` | 0 / 0 | the same | none; no `_MEI` | 0 / 0 / 0 |
| `--check-hash-based-pycs always -c pass` (new) | 2 / 2 | `Clearwater: -c is not supported` | 0 / 0 | the same | none; no `_MEI` | 0 / 0 / 0 |
| `--check-hash-based-pycs never -m http.server` (new) | 2 / 2 | `Clearwater: -m 'http.server': no GPU pack is loaded` | 0 / 0 | the same | none; no `_MEI` | 0 / 0 / 0 |
| `-m http.server --multiprocessing-fork` (new) | 2 / 2 | **`Clearwater: multiprocessing children are not supported`** (the refusal comes first) | 0 / 0 | the same | none; no `_MEI` | **0 / 0 / 0 (no log file)** |

- Walls: onedir 0.29-0.43 s; onefile 2.40-2.95 s (bootloader extraction included). Window
  samples: 1 per onedir run, 8-10 per onefile run; no UIA element, no visible window, no
  timeout kill. stdout empty in all 20.
- `tasklist` after the 20 runs: no `Clearwater.exe`, `ffmpeg.exe` or `ffprobe.exe`.

### Item 4: the full `--verify` (the pack renamed back)

`uv run --no-sync python -B tools/package/build.py --verify <t3c pack>`: exit 0, `PASS (11
distributions; 2701 RECORD rows, each file's sha256 and size; 2701 files, 2412.6 MiB)`
(`t3h/verify-1-before.log`). `find` gives 2,701 files under `site-packages` and 0 `.pyc`.

The sorted file-list md5 (`t3h/pack-filelist-before.md5`, 15:18:16Z, 2,702 files with
`manifest.json`):

- paths, `(cd <pack> && find . -type f -printf '%P\n' | LC_ALL=C sort | md5sum)`:
  `5eba08dc993edf7b7e9441b1d4663ae9`;
- paths + size + mtime, `... -printf '%P %s %T@\n' ...`: `8c70a2672ff3c5c4ae800aae79f04e3c`.

2b-4's `27f33db1...` did not record its command, and none of the list forms tried here
reproduces it; so the comparison of record is within this group (before vs after, item 6). The
pack is unchanged since 2b-4 by `--verify` (every RECORD row's sha256 and size, no unlisted
file).

### Item 5: the WITH-pack re-proof, headless -- PASS on both forms

- **Tool.** `t3h/proof4.py` is `t3f/proof4.py` copied, with the evidence paths moved to `t3h`,
  the log `t3h/proof5.jsonl`, and a fresh, empty per-form kernel cache
  `appdata\cupy-kernel-cache-t3h-<form>`. The spawn, the environment, the tree tracker and the
  watch are unchanged.
- **Command.** `<new dist>\Clearwater.exe --export-worker` (`t3b/headless.EXES`, the
  `dist-on{dir,file}` paths rebuilt in item 2). Requests `heic-ad24-both.heic` -> PNG and
  `vfr.mp4` -> MP4, c3 defaults, `force_cpu` off, encoder `auto`. Order: onedir HEIC, onedir
  video, onefile HEIC, onefile video.

| Form | Request (end moment, wall) | Exit | Device | Output, result | Kernel cache `.cubin` | CUDA / CuPy files mapped | Windows (UIA / visible; samples) | Left over |
|---|---|---|---|---|---|---|---|---|
| onedir | HEIC -> PNG (15:18:46Z, 19.2 s) | **0** | **`GPU`**; log `export heic-ad24-both.heic: ok; device GPU`; no warning | `heic-ad24-both_corrected.png` 37,080 B; ok | 0 -> 52 (first file 15:18:27Z, inside the run) | 67: 59 pack + 8 driver, **0 elsewhere** | 0 / 0 (68) | none; pack +0 / -0 |
| onedir | `vfr.mp4` -> MP4 (15:19:01Z, 12.1 s) | **0** | **`GPU`**; `export vfr.mp4: ok; device GPU` | `vfr_corrected.mp4` 55,168 B; ok | 52 -> 62 | 67: 59 + 8, 0 elsewhere | 0 / 0 (34) | none; +0 / -0 |
| onefile | HEIC -> PNG (15:19:25Z, 20.9 s) | **0** | **`GPU`** | 37,080 B; ok | 0 -> 52 (first file 15:19:06Z) | 67: 59 + 8, 0 elsewhere | 0 / 0 (62) | none; `_MEI` [] / []; +0 / -0 |
| onefile | `vfr.mp4` -> MP4 (15:19:42Z, 14.8 s) | **0** | **`GPU`** | 55,168 B; ok | 52 -> 62 | 67: 59 + 8, 0 elsewhere | 0 / 0 (38) | none; `_MEI` [] / []; +0 / -0 |

- **Trees.** onedir HEIC: the worker alone. onefile HEIC: the bootloader plus one
  `Clearwater.exe --export-worker` child, both exit 0. The video trees hold 1.0.0's ffprobe /
  ffmpeg children and their `conhost.exe` (onedir 26 PIDs, onefile 22), all exit 0 except three
  short-lived PIDs that ended before psutil read them (no command line), gone at the end.
  The onefile bootloader's two top-level windows are HIDDEN (`PyInstaller Onefile Hidden
  Window`, `Default IME`); no UIA element; neither is a Clearwater window.
- **No CuPy canary child** in any run (no `dynamic_lib_subprocess` command line), as in 2b-4.
- **stderr**: CuPy's own `cupy\_environment.py:286: UserWarning: CUDA path could not be
  detected` in every with-pack run, as in 2b-4 (harmless here: the kernels compiled; for WP6.3).
- No `CUDA*` variable in any child environment.

**Every mapped CUDA / CuPy / NVRTC file over the four runs' trees** (`t3h/mapped-cuda-files.tsv`):
the same 67 paths in each of the four runs, and the SAME SET as 2b-4's `t3f/mapped-cuda-files.tsv`.

- **Pack, 59 (88.1 %)**, under
  `<wt>\work\wp6.1\t3c\appdata\Local\Clearwater\gpu-pack\14.2.0-cu12\site-packages\`:
  `nvidia\cublas\bin\cublas64_12.dll`, `nvidia\cublas\bin\cublasLt64_12.dll`,
  `nvidia\cuda_nvrtc\bin\nvrtc64_120_0.dll`, `nvidia\cuda_nvrtc\bin\nvrtc-builtins64_129.dll`,
  and 55 extension modules (45 `cupy\`, 9 `cupy_backends\`, 1 `cupyx\`).
- **NVIDIA driver, 8 (11.9 %):** `C:\Windows\System32\nvcuda.dll`, and under
  `C:\Windows\System32\DriverStore\FileRepository\nvami.inf_amd64_00e5dc1fb00a1261\`:
  `nvcuda64.dll`, `nvapi64.dll`, `nvapi64_impl.dll`, `nvdiagclt64.dll`, `nvdxgdmal64.dll`,
  `nvobjectloader64.dll`, `Display.NvContainer\NvMessageBus.dll`.
- **Elsewhere: 0.** 100 % pack + driver.

### Item 6: the WITHOUT-pack regression (pack renamed `14.2.0-cu12.renamed`), then `--verify`

| Form | Request (end moment, wall) | Exit | Device and warning (AD-9's text) | Log | Output | CUDA files | Windows | Left |
|---|---|---|---|---|---|---|---|---|
| onedir | HEIC -> PNG (15:20:41Z, 0.6 s) | 0 | **`CPU: CuPy not installed`**; warning `Processed on the CPU (CPU: CuPy not installed).` | `CuPy not installed: No module named 'cupy'`; `export heic-ad24-both.heic: ok; device CPU: CuPy not installed` | `heic-ad24-both_corrected.png` 37,104 B; ok | 0 | 0 / 0 (3) | none |
| onefile | HEIC -> PNG (15:20:47Z, 3.9 s) | **3221225477** (both PIDs) | the same | the same | 37,104 B; ok | 0 | 0 / 0 (14) | none; no `_MEI` |

- Device, warning, log lines and output size equal 2b-4's without-pack rows.
- **The onefile run's exit is DR-125's signature, not 0 as in 2b-4.** stderr: `Fatal Python
  error: _enter_buffered_busy: could not acquire lock for <_io.BufferedReader name=3> at
  interpreter shutdown, possibly due to daemon threads` (fd 3: the shim's private reader, read
  by the worker's watcher thread). The result line had been delivered (`ok`, the PNG written);
  the child exited 0xC0000005 and the bootloader passed it on. Dispatch-9 named this exit
  expected and not a STOP; dispatch-11's STOP list does not name it. Seen once in 12 frozen
  worker runs since the shim (2b-4: 0 of 6; this group: 1 of 6). Not chased: DR-125's paydown
  is its own package.
- **`--verify` after the runs (pack renamed back): PASS**, the same line and figures: 2701 rows,
  2701 files, 2412.6 MiB (`t3h/verify-2-after.log`); 0 `.pyc`.
- **The file-list md5s are UNCHANGED** (`t3h/pack-filelist-after.md5`, 15:21Z): paths
  `5eba08dc...`, paths + size + mtime `8c70a267...`. No run wrote into the pack.
- `tasklist` after: no `Clearwater.exe`, `ffmpeg.exe` or `ffprobe.exe`.

### Files changed this group

`docs/proofs/wp6.1-ledger.md` only. Evidence tools (not product, not committed):
`t3h/handler_check.py` (qualname keys, every function, the constant walker), `t3h/proof4.py`
(paths, log, kernel cache, the redirected-tree diff in `run_argv`), `t3h/uia_watch.ps1` (copied
unchanged). The new builds are at `work/wp6.1/dist-on{dir,file}/` (of `926bfdfa`); they replace
`49150ccf`'s. The pack is unchanged at `work/wp6.1/t3c/appdata/Local/Clearwater/gpu-pack/14.2.0-cu12`.

Depth at turn-3 group-2b-6 end: 179,394 (wp61-cell8, at its yield; read by the dispatcher)

## Turn 3 group 2c-a (Reviewer A r5 fold-in, the final-code rebuild, the two scripts) (2026-11-04 ~15:25-15:42Z)

Same cell (wp61-cell8), dispatch `clearwater-review-evidence/wp6.1/cell/dispatch-12.md`, on
Reviewer A round 5 (`clearwater-review-evidence/wp6.1/A/r5/review.txt`, on `49150ccf..926bfdfa`:
VERDICT NO_NEW_CRITICAL_MAJOR; one MINOR, three ADVISORY, all test or docstring only). Evidence:
`clearwater-review-evidence/wp6.1/cell/t3i/`. Code + tests: commit `dc784b4f`.

- NO frozen run and NO GUI launch in this group; neither Part-3 script was run. No desktop input,
  no network. Nothing under the real `%APPDATA%\Clearwater` or `%LOCALAPPDATA%\Clearwater` (the
  latter absent). Nothing under the pack was run or imported.
- `jobs/export_process.py`, `io/video/pipes.py` and `app/export_worker.py` are untouched.
- **Owner log** md5 `69ed0432c562db9445daecbe8f15fe27` before (15:27:46Z) and after (15:41:03Z)
  (`t3i/owner-log-md5-{before,after}.txt`; a check only).

### The fold-in table

| # (r5) | Disposition | Fix (file) | Test(s) | Result |
|---|---|---|---|---|
| 1 MINOR | FIX | `tests/test_frozen_entry.py`: new helper `_within(read, timeout, what)` runs one blocking pipe read on a daemon thread and FAILS the test at its deadline. The parent-dies case reads the worker PID through it (60 s) inside a `try` / `finally` that kills and waits the parent if it is alive and kills the worker when no record came. Without a PID, the worker ends by itself: its pipe closes with the parent and its wait is bounded at 30 s. The sweep of the three owned test modules for other raw child-pipe reads found one more: the F-E (i) test (`..._inherits_nul_not_the_request_pipe`) read `stdout` / `stderr` with plain `read()` after the wait. Both now go through `_within` (30 s each), and the child is killed in a `finally`. Every other child call in the three modules is a `subprocess.run(..., timeout=...)` or a `communicate(timeout=...)`. | The three changed tests: `test_a_child_of_the_frozen_worker_branch_inherits_nul_not_the_request_pipe` and `test_the_end_of_the_request_pipe_reaches_the_workers_reader_through_the_shim[parent-closes, parent-dies]` | 4 passed (`t3i/pytest-changed-c61h-4.log`, with #2's test) |
| 2 ADVISORY | FIX | `test_the_long_options_are_cpythons_by_execution`: the values come from an independent literal, `{"always", "default", "never"}` (CPython 3.12's own), plus near misses (`ALWAYS`, `Default`, `checked`, `unchecked`, `none`, `bogus`). Each is run through CPython; the accepted set must equal the literal AND `LONG_VALUE_OPTIONS[...]`. | the same test | **Mutation** (`t3i/mutation_long_option.py` -> `t3i/mutation-long-option.log`: in memory, no file changed): the constant as committed -> PASS; `"never"` dropped -> **FAIL** (`AssertionError` at the table comparison) |
| 3 ADVISORY | FIX | `gpu_pack.activate` docstring: a named `-m` target activates the pack BEFORE it is judged (an absent or rejected pack, or a module not from the pack, is refused after the call); `-c`, the multiprocessing flags, `-m` without a module name and a failed worker stdin isolation are refused before it. Checked against `__main__.main` / `run_interpreter_option` (`:379`, `:342-350`, `:388-392`). | docstring only | read-out below: the new builds carry it |
| 4 ADVISORY (OUT of envelope) | FIX | The parent-closes case: `communicate(input=<request>, timeout=60)` with NO prior `stdin.close()`. `communicate` writes the request and then closes the parent's end, which is still the pipe-close EOF the test proves. The child is killed and waited in a `finally` if it is still alive. | the parent-closes case (the `eof` / `waited_s` / fd / inheritable assertions unchanged) | PASS |

No before-record (test and docstring only, as the dispatch allows).

### Commands (worktree root, Git Bash, `PYTEST_ADDOPTS` unset; logs in `t3i/`)

| Command | Exit | Summary |
|---|---|---|
| the three owned modules (`c61h-2`) | 0 | **307 passed in 18.97 s** |
| the WIDER run (dispatch-11's 8 modules, `-m "not gpu"`, `--timeout 120`, `c61h-3`) | 0 | **500 passed, 41 deselected in 41.28 s** |
| the changed tests after the last docstring edit (`c61h-4`) | 0 | 4 passed |
| `ruff check .` / `ruff format --check .` | 0 / 0 | All checks passed / 323 files already formatted |
| `mypy` (strict, configured set) | 0 | no issues in 161 source files |
| `mypy --strict` on the 2 touched files, `--platform win32` and `--platform darwin` | 0 / 0 | no issues in 2 source files, each |

Every pytest run used `-p no:cacheprovider` and `--timeout 120`. 0 CR in both committed blobs.

### Both rebuilds (from `dc784b4f`; `src` and `tools` clean)

| Form | Command (worktree root) | `df -h /c` before | Exit | Wall (shell / build.py) | Result |
|---|---|---|---|---|---|
| onedir | `uv run --no-sync python tools/package/build.py --form onedir --with-ffmpeg > work/wp6.1/build-onedir-t3i.log 2>&1` | 77 GB free (15:29:53Z) | 0 | 71 s / 61.8 s | `Clearwater.exe` 10,678,999 B, `_internal` 234,668,819 B; 668.3 MiB release; bundle checks 7.6 s |
| onefile | `... --form onefile --with-ffmpeg > work/wp6.1/build-onefile-t3i.log 2>&1` | 77 GB free (15:31:06Z) | 0 | 84 s / 80.7 s | `Clearwater.exe` 93,876,201 B (89.5 MiB); 523.9 MiB release; bundle checks 0.8 s |

- Both logs: `61 hidden imports from 376 pack files`, `hidden-import site (scan; named 1x)`,
  `hidden-import check: PASS (61 modules, each in the bundle)`, `bundle check: PASS`. The one
  warning is the usual `scipy.special._cdflib`. FFmpeg / ffprobe 9.0.2 were copied beside each
  executable.
- **The resolved set** (`t3i/hidden-imports-on{dir,file}-t3i.json`) is EQUAL, as JSON, to 2b-6's.
  Logs: `t3i/build-on{dir,file}-t3i.log`.

**The read-out** (`t3i/handler_check.py`, 2b-6's tool unchanged -> `t3i/handler-check-t3i.json`;
the source is `git show dc784b4f:...` in `t3i/src-dc784b4f/`). Nothing was executed.

| Read in each `Clearwater.exe` (onedir and onefile alike) | Result |
|---|---|
| entry script, every function (incl. `interpreter_reentry`, `run_interpreter_option`, `isolate_worker_stdin`, `multiprocessing_reentry`, `main`) | **10 of 10 equal** (bytecode and constants, by qualified name); module-level bytecode and constants equal |
| the six constants (`FLAG_LETTERS` with `R` and `t`, `VALUE_LETTERS`, `LONG_VALUE_OPTIONS`, `MULTIPROCESSING_FLAGS`, `GRAMMAR_PYTHON_VERSION`, `GRAMMAR_PYTHON_VERSION_INFO`) | rebuilt from the bundle's bytecode; each equal to the source (values as in 2b-6) |
| PYZ `clearwater.gpu_pack`, every function | **53 of 53 equal**; `add_site_prefix` and `activate` equal, `activate` calls `add_site_prefix`; module-level equal |
| `clearwater.__main__` in the PYZ | no |

**READ-OUT: PASS on both. Build commit `dc784b4f`.**

Two controls, read only:

- `t3c/exp` (`t3i/handler-check-t3i-control-t3c-exp.json`): **FAIL**, exit 1. Its entry script
  has 1 of 10 functions equal and none of the constants; `gpu_pack` has 28 of 53.
- The NEW builds against the OLD source `926bfdfa` (`t3i/handler-check-t3i-vs-926bfdfa.json`):
  **FAIL**, exit 1, on exactly one item: `gpu_pack.activate`, whose bytecode is equal but whose
  constants (the docstring) are not. So the builds carry `dc784b4f`'s docstring, and the check
  sees a one-docstring change.

**No frozen run in this group.** The 2b-6 refusals and proof stand for behaviour, because the
only product change is that docstring. These are the builds for groups 2c and turn 4.

### The two scripts (WRITTEN, NOT RUN)

Under `clearwater-review-evidence/wp6.1/cell/t3i/`:

| File | md5 | Role |
|---|---|---|
| `gui_check.py` | `0e05e8e7171f73c74ece4715f87a75eb` | group 2c's GUI check (modes `check` and `owner`) |
| `timings.py` | `db50def86b7fc2df1c27e8148501e94e` | turn 4's exclusive timings |
| `launch_common.py` | `1ab40e7d381809a2b06c5ff4a7f6e4da` | the shared launch / window / bound helpers both import |
| `uia_tree.ps1` | `10963628c6e35dfc1fa6f8d69b729d7f` | the read-only UIA element-tree dump `gui_check.py` calls |

Static checks only:

- `compile()` of the three Python files: OK.
- PowerShell `Parser.ParseFile` of `uia_tree.ps1`: 0 errors.
- `ruff check --isolated --select E,F,W,B,UP,SIM`: clean.
- `mypy --check-untyped-defs` (static analysis, nothing imported or run): clean in the three
  files; its one error is in the 2b-1 helper `t3b/headless.py:253`, which is not changed here.
- `grep -nE "SendKeys|AppActivate|SendInput|keybd_event|mouse_event|pyautogui|SetForegroundWindow|PostMessage.*WM_KEY|WM_CHAR"`
  over all four: **0 hits** (comments included).
- 0 CR in each file.

**`launch_common.py`** (shared):

- **Environment.** Every frozen launch gets APPDATA, LOCALAPPDATA, TEMP / TMP, CUPY_CACHE_DIR
  and the five XDG_* variables under `work\wp6.1\t3c\appdata\`, so the pack under it is the one
  found. `CUDA_PATH*` and `PYTHON*` are removed and `PATH = C:\Windows\System32;C:\Windows`. The
  environment goes to `Popen(env=...)`; the script's own `os.environ` is never changed, and the
  owner's profile is only READ (its log's md5).
- **Refusals before any launch.** The read-out JSON must be PASS, name both dist executables,
  and be newer than them; no `Clearwater.exe` may be running.
- **The tree.** The launched PID plus every psutil descendant, gathered while it runs (create
  times kept, so a reused PID is never touched).
- **Windows.** `EnumWindows` is walked. For a window whose `GetWindowThreadProcessId` owner is
  not in the tree, nothing else is called (no title, no class, no message). A tree window is
  read, captured by `PrintWindow(hwnd, ..., PW_RENDERFULLCONTENT)` into a memory DC of that
  window's own DC, and closed by `PostMessageW(hwnd, WM_CLOSE)`. The owner PID is re-checked
  just before each capture and close.
- **No activation.** A GUI launch sets `STARTUPINFO.wShowWindow = SW_SHOWNOACTIVATE`, which
  Windows applies to the application's first `ShowWindow`, so the owner's typing stays in the
  window the owner has in front. Best effort: an explicit activation by Qt would override it.
- **The hard bound.** A watchdog `threading.Timer` kills the whole tree by PID at the bound,
  whatever step is running.
- **The worker spawn.** As `jobs/export_process.py` does it: `tool_spawn_kwargs()`'s creation
  flags, and its no-FFREPORT rule applied to the redirected environment.
- **Pack helpers.** The pack's full `build.py --verify`, and an md5 of its listing
  (path, size, mtime).

**`gui_check.py check`** (both forms, or `--form`). Per form, two launches of `Clearwater.exe`
with no arguments: `with` (the pack present) and `absent` (the pack renamed
`14.2.0-cu12.renamed` for that launch only, renamed back in a `finally`). Each launch has a
**60 s** hard bound and runs these steps:

1. Wait for the first visible window of the tree (10 ms poll).
2. Read the redirected log's NEW lines, from its size before the launch (nothing deleted),
   until the loader's line appears (20 s). Record it VERBATIM; it must end
   `gpu pack 14.2.0-cu12: loaded` or `...: absent`.
3. Wait 3 s, then, on `with` only, take a PrintWindow PNG of the tree's window titled
   `Clearwater` (`t3i\shots\first-window-<form>.png`; it must print every row and not be all
   black).
4. Take the UIA element tree of the tree's own top-level windows (`uia_tree.ps1`: a
   `ProcessId` condition, the Control view to depth 4, at most 300 elements, no pattern
   invoked). There must be a top element named `Clearwater`.
5. Post `WM_CLOSE` to that window. The exit (0) is awaited 30 s and the tree's end 10 s;
   otherwise the tree is killed and the launch FAILS.
6. Record the exit, the leftovers, and the `_MEI*` folders before and after.

Once per script run it also records the owner-log md5, the pack's `--verify` and its listing
md5 (before and after), and `tasklist`. Records go to `t3i\gui-check.jsonl` and `t3i\gui\`.
Exit status: 0 PASS, 1 FAIL, 2 refused.

**`gui_check.py owner --form <f>`** is the D6 hand check, for the owner at the keyboard; see
the step list below. It stages copies of the three fixtures into a NEW
`work\wp6.1\t3i\hand\<form>\` (it refuses an existing folder), then launches that form's GUI
with the same redirect and the pack present. It sends nothing to the window and waits for the
owner's close (45 min bound). It then lists the folder's files with their sizes, the EXIF entry
count of each PNG, and the log's new lines.

**`timings.py`** (turn 4, EXCLUSIVE; estimated wall about 15 min, printed at the top):

- **Refusals.** The read-out guard; under 25 GB free; any running `Clearwater.exe`, pytest or
  PyInstaller process; a cold folder that already exists (nothing is overwritten or deleted).
- **Per form, n = 1..3:**
  - `robocopy <release> work\wp6.1\cold-<form>-<n> /E /J` (unbuffered);
  - the copy's FIRST launch: COLD start, spawn to the first visible window of the tree;
  - an immediate relaunch: WARM start;
  - each start launch posts `WM_CLOSE` to its own window 3 s after the window appears, waits
    30 s for the exit, and has a 60 s bound.
- **First export**, through `cold-<form>-1`'s `Clearwater.exe --export-worker`:
  `heic10-gradient-display-p3.heic` -> PNG, spawn to the `result` line, 300 s bound. The rows:
  - `gpu-warmup`: empty cache, untimed for the medians;
  - `gpu-warm` x3, the medians;
  - `gpu-empty-cache` x1: a new, empty cache;
  - `cpu-no-pack` x1: the pack renamed away for that run.
- **Pack and kernel-cache state, stated in every record.** Starts run with the pack PRESENT (the
  shipped GPU path; the loader's cheap check runs). Their cache `t4-start-<form>` is empty before
  the form's first cold launch, and its file count is recorded per launch.
- **Brackets.** The owner-log md5; the pack's `--verify` and listing md5 (before and after);
  `tasklist`; the cold copies' total size, printed (they are KEPT, to be deleted only on the
  owner's word).
- **Output.** Records go to `clearwater-review-evidence\wp6.1\timings\t4\timings.jsonl`. The
  summary (median, min, max, spread for cold, warm and gpu-warm; the single rows with their
  device and cache state) goes to `summary.json` and stdout.
- This follows the dispatch's default, with the empty-cache GPU row added: it is the first export
  a user ever makes, and the one that pays for kernel compilation.

### The owner's hand check (D6), for CHARC to relay

D22: a photo's output is always PNG. So "PNG and JPEG" reads here as a HEIC input and a JPEG
input, each exported to PNG.

1. Ask the orchestrator to start it (or run it yourself) from
   `C:\Users\rwsmy\clearwater\.worktrees\wp6.1`:
   `.venv\Scripts\python.exe -B C:\Users\rwsmy\clearwater-review-evidence\wp6.1\cell\t3i\gui_check.py owner --form onedir`.
   Clearwater opens without taking focus: click its window. It uses a test profile under
   `work\wp6.1\t3c\appdata`, never your own settings.
2. **File > Open...**, go to `C:\Users\rwsmy\clearwater\.worktrees\wp6.1\work\wp6.1\t3i\hand\onedir\`
   and open `heic-ad24-both.heic`. When the picture shows, **File > Export...**. The result
   `heic-ad24-both_corrected.png` appears in the same folder. Check that it is corrected and the
   right way up.
3. The same with `jpeg-gradient-display-p3.jpg`; the result is `jpeg-gradient-display-p3_corrected.png`.
4. Open `vfr.mp4`, wait until Export is available (the analysis completes), then **File >
   Export...**. Play `vfr_corrected.mp4` in your usual player.
5. **File > Quit**. The script prints the files, their sizes, each PNG's EXIF entry count and
   Clearwater's log lines.
6. Repeat steps 1-5 with `--form onefile` (folder `...\work\wp6.1\t3i\hand\onefile\`). Tell
   CHARC, per form, whether each of the three exports worked, and anything odd.

### Files changed this group

`src/clearwater/gpu_pack.py` (docstring), `tests/test_frozen_entry.py` (`dc784b4f`), and this
ledger. Evidence tools (not committed): the four scripts above,
`t3i/mutation_long_option.py`, and `t3i/handler_check.py` (2b-6's, unchanged). The new builds
are at `work/wp6.1/dist-on{dir,file}/` (of `dc784b4f`); they replace `926bfdfa`'s.

Depth at turn-3 group-2c-a end: DISPATCHER TO FILL
