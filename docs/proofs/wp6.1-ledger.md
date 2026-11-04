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

Depth at turn-3 group-1 end: DISPATCHER TO FILL
