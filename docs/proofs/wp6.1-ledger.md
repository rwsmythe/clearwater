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
