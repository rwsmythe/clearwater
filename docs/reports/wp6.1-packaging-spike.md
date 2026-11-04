# WP6.1 packaging spike: completion report

Package: WP6.1, the packaging spike (Windows). Brief: `docs/briefs/wp6.1-brief.md` (FINAL).
Branch `wp6.1`; the final code is `dc784b4f`; both measured builds are of that commit.
Every fact below comes from the cell ledger `docs/proofs/wp6.1-ledger.md` (cited by section)
or from the evidence folder `C:\Users\rwsmy\clearwater-review-evidence\wp6.1\` (cited as
`<ev>\...`). This report was written from those records only; nothing was run to write it.

Status: code-complete. Reviewer A converged at round 5. Reviewer B, the gate and the owner's
D6 hand check are still to come.

## 1. Summary and the CP6a inputs

CP6a is the owner's decision, presented by CHARC. The owner's choice is recorded in the accept
record and the WP6.3 brief, not in this report. This section lays out the inputs from the
records; it does not recommend a form.

What both forms do (both PASS):

- Both forms build from one script, `tools/package/build.py`, and start to the first window.
- With the GPU pack present, both load it, and the frozen export worker exports on the GPU
  (`device GPU`). All CUDA files come from the pack or the NVIDIA driver, none from elsewhere.
- Without the pack, both fall back to the CPU with AD-9's text, `CPU: CuPy not installed`.

Where the forms differ (figures from section 2 unless another source is named):

| Input | One-folder | One-file |
|---|---|---|
| Release size, with FFmpeg (434.4 MiB of each) | 668.3 MiB | 523.9 MiB |
| Without FFmpeg | a 234.0 MiB folder (`Clearwater.exe` plus `_internal`) | one 89.5 MiB `Clearwater.exe` |
| Zipped size | not measured | not measured |
| Cold start, median | 4.469 s | 2.771 s |
| Warm start, median | 0.893 s | 3.170 s |
| First export, GPU, warm kernel cache, median | 1.285 s | 3.220 s |
| First export, GPU, empty kernel cache | 15.460 s | 18.284 s |
| First export, CPU, no pack | 0.531 s | 2.728 s |
| Unpacking at launch | none | every launch unpacks the bundle into a new `_MEI` folder in `%TEMP%` |
| The PID the parent holds for a worker (F-B) | the worker | the bootloader |
| `_MEI` left in `%TEMP%` | none | when the bootloader itself is killed (seen twice in 2b-1) |

Notes on these inputs:

- **One-file's per-launch extraction.** Every one-file launch unpacks the bundle, so its warm
  start is not faster than its cold start (3.170 s against 2.771 s, warm spread 1.059 s). The
  one-folder cold start is about 5x its warm start, because the unbuffered copy left
  `_internal` out of the file cache.
- **The export rows** were measured with headless workers started on their own, so each
  one-file worker unpacked its own bundle. Whether a worker started by the one-file GUI
  reuses the GUI's `_MEI` folder was not measured (section 9).
- **F-B.** In the one-file form, when the bootloader's PID was killed, the Python worker under
  it ran on and finished the export, and an orphaned `_MEI` folder stayed in `%TEMP%` (ledger,
  "Turn 3 group 2b-1", "The write journal (D85)"). The product's hung-worker kill
  (`process.kill()` in `jobs/export_process.py`) ends only the process it holds, so a one-file
  build would need a job-object kill (section 8). The one-folder form has no bootloader layer.
- **`_MEI` handling.** When the worker under a one-file bootloader was killed, or crashed after
  its result (DR-125), the bootloader removed its `_MEI` folder. Only a kill of the bootloader
  itself left the folder behind.
- **The D6 hand check is still to come** for both forms (the GUI's own photo and video exports,
  by the owner). It may add inputs for either form.

Other observations from the records:

- The first GPU export with an empty kernel cache takes about 14-15 s longer than with a warm
  one (the kernel compile), in both forms.
- **The device fallback chain worked as designed.** Twice before the final code (F-E and F-F
  below), the GPU path failed in the frozen worker. Each time the export finished on the CPU
  with a readable reason (`CPU: CUDA device unusable`, and the cause in the log), the result
  was `ok`, and nothing was written outside the redirected folders. (Ledger, "Turn 3 group
  2b-3 (items 4-5)" item 4 and "(F-E shim)". The first run exited 0; the second exited with
  DR-125's code after its result line.)

## 2. The measured table

Builds of `dc784b4f` (ledger, "Turn 3 group 2c-a", "Both rebuilds"). Timings: the orchestrator's
seat, the exclusive window from 15:46Z on 2026-11-04 (ledger, "Group 2c and turn 4"). Every
timing figure is from `<ev>\timings\t4\summary.json`, checked against `timings.jsonl`.

| Measure | One-folder | One-file |
|---|---|---|
| Release size, with FFmpeg | 668.3 MiB (700,792,298 B) | 523.9 MiB (549,320,681 B) |
| Executable | `Clearwater.exe` 10,678,999 B, plus `_internal` 234,668,819 B | `Clearwater.exe` 93,876,201 B (89.5 MiB) |
| FFmpeg beside it | `ffmpeg.exe` 217.3 MiB, `ffprobe.exe` 217.1 MiB | the same |
| Build wall (shell / build.py) | 71 s / 61.8 s | 84 s / 80.7 s |
| Cold start, s: median; min-max; spread | **4.469**; 4.188-4.718; 0.530 | **2.771**; 2.763-3.049; 0.286 |
| Warm start, s: median; min-max; spread | **0.893**; 0.874-1.149; 0.275 | **3.170**; 2.762-3.821; 1.059 |
| First export, GPU, warm kernel cache (52 files), s: median; min-max; spread | **1.285**; 1.258-1.293; 0.035 | **3.220**; 3.210-3.524; 0.314 |
| First export, GPU, empty kernel cache (new cache, 0 -> 52 files), s | 15.460 | 18.284 |
| First export, GPU warm-up run (cache 0 -> 52 files; not in the medians), s | 15.915 | 18.398 |
| First export, CPU, pack renamed away, s | 0.531 (`CPU: CuPy not installed`) | 2.728 (the same) |

How each row was measured:

- **Pack state.** Every start launch and every GPU export ran with the pack PRESENT, so the
  loader's start-up check ran. The CPU row ran with the pack folder renamed
  `14.2.0-cu12.renamed` for that run.
- **Kernel-cache state.** The start launches' cache had 0 files before each form's first cold
  launch and 2 before every later launch (the GUI's start-up test kernel). The GPU warm-cache
  rows had 52 files before and after. The warm-up and empty-cache rows went from 0 to 52.
  The CPU row's cache held 52 files and was not touched.
- **Start.** From the spawn to the first visible window of the launched process tree. Each
  launch posted `WM_CLOSE` to its own window 3 s after it appeared. Every start launch exited
  0 with a clean close, no bound hit and nothing left.
- **Cold start method** (round 0's, ledger "Round 0", item 7). The account is not elevated, so
  the file cache cannot be purged. Before each cold run, `robocopy /E /J` (unbuffered) copied
  the release into a new folder `work\wp6.1\cold-<form>-<n>`, and that copy was launched once.
  **Limit:** Windows' own DLLs and the GPU driver stay warm, unlike after a reboot. The sanity
  check holds for one-folder (cold about 5x warm). For one-file it does not, for the reason in
  section 1.
- **Warm start.** An immediate relaunch of the same copy.
- **First export.** Headless (D6 as ruled): `cold-<form>-1`'s `Clearwater.exe
  --export-worker` with one request, `tests/fixtures/stills/heic/heic10-gradient-display-p3.heic`
  -> PNG, timed from the spawn to the `result` line. Every export exited 0 with `ok` and
  nothing left. The GUI's own in-process photo export was not timed (D6); the owner checks it
  by hand.
- **Three runs each** for the starts and the warm-cache exports; one run for the other rows.
- On this small fixture the CPU (0.531 s) beats the warm GPU (1.285 s), because the GPU's
  start-up cost dominates. This says nothing about large photos or video.
- Brackets: 76.6 GB free before; the pack's full `--verify` PASS before and after; the pack
  listing md5 `e10a2b10...` unchanged; the owner's log md5 `69ed0432...` unchanged.

## 3. The two screenshots

- `<ev>\cell\t3i\shots\first-window-onedir.png` and `<ev>\cell\t3i\shots\first-window-onefile.png`.
- Each is a PrintWindow capture of Clearwater's own top-level window, 2586 x 1630, taken
  3 s after the first window appeared, with the pack present (ledger, "Group 2c").
- They show the first window: the File / View / Tools menu, "Open a photo or video", the
  Presets dock (Scuba (deep), Snorkel (shallow)), and the Batch dock. The status bar begins
  "Device: GPU"; it is clipped at the bottom edge.
- The two files are byte-identical (md5 `91fb036a...` both, re-read for this report). Both
  forms render the same window at the same size.
- The thin white strip at the right and bottom edges comes from the capture, not the UI.

## 4. The build commands and the bundle

**Commands** (from the worktree root; ledger, "Turn 3 group 2c-a", "Both rebuilds"):

```
uv run --no-sync python tools/package/build.py --form onedir --with-ffmpeg > work/wp6.1/build-onedir-t3i.log 2>&1
uv run --no-sync python tools/package/build.py --form onefile --with-ffmpeg > work/wp6.1/build-onefile-t3i.log 2>&1
```

`build.py` builds one PyInstaller argument list for both forms and runs it in-process through
`PyInstaller.__main__.run`. The PyInstaller line as logged (`<ev>\cell\t3i\build-onedir-t3i.log`,
line 64, without its 61 `--hidden-import` arguments):

```
PyInstaller <wt>\src\clearwater\__main__.py --onedir --name Clearwater --windowed --noconfirm
  --clean --paths <wt>\src --distpath <wt>\work\wp6.1\dist-onedir\Clearwater-1.0.0-windows-onedir
  --workpath <wt>\work\wp6.1\build-onedir --specpath <wt>\work\wp6.1\spec-onedir
  --exclude-module ... (the list below) --hidden-import ... (61)
```

The one-file line differs only in `--onefile` and the `onefile` folder names. `build.py` sets
`PYINSTALLER_CONFIG_DIR` under the output folder first (Reviewer A r1 F4), so PyInstaller's
cache stays out of `%LOCALAPPDATA%`. `--with-ffmpeg` copies `ffmpeg.exe` / `ffprobe.exe`
beside the executable and runs each copy's `-version` from there.

**PyInstaller:** 6.22.3 (`pyinstaller>=6.22,<7`) with `pyinstaller-hooks-contrib` 2026.9, in the
`dev` group, N13 approved by CHARC at round 0 (brief, "CHARC rulings at round 0").

**The exclude list** (`--exclude-module`, from the logged line): `cupy cupyx cupy_backends cuda
nvidia fastrlock tests tools pytest _pytest pluggy xdist execnet pytest_timeout pytestqt mypy
mypyc ruff psutil cpuinfo av fastapi starlette uvicorn jinja2 httpx httpcore multipart
python_multipart yaml _yaml typing_extensions tkinter`.

**The build's own checks** (both forms, both PASS in the final logs):

- `bundle check`: no `cupy`, `cupyx`, `cupy_backends`, `cuda`, `nvidia`, `fastrlock` or `tests`
  at any depth, in any case, or in any ZIP; no CUDA library; every module's top-level name is
  on the product's allowlist (computed from `uv.lock`). It reads the release folder, the
  CArchive and the PYZ. One narrow exception: SciPy's own vendored array-API adapter
  `scipy._external.array_api_compat.cupy` (ledger, "Turn 3 group 2a").
- `hidden-import check: PASS (61 modules, each in the bundle)`.

**The hidden-import set: 61 modules** (F-C2; ledger, "Turn 3 group 2b-3", "The resolved
hidden-import set"):

- How it is derived: at build time `build.py` parses (AST) every `.py` file listed in the RECORD
  of the eleven locked pack distributions, 376 files. Every import of a standard-library
  module counts, including conditional and function-level ones and literal
  `importlib.import_module("x")`. That gives 60 modules. A short committed list adds the needs
  of extension modules that no `.py` file shows: `graphlib` today. Total 61.
- Why: CuPy and `cuda.pathfinder` live outside the bundle, so PyInstaller cannot see what they
  import. Before this, the frozen worker failed with `No module named 'ctypes.wintypes'`, then
  `'graphlib'`.
- A member missing from the bundle FAILS the build, so a lock bump that adds a new stdlib need
  fails at build time, not on a user's GPU. The set is written to
  `work/wp6.1/hidden-imports-<form>.json`; the final copies are
  `<ev>\cell\t3i\hidden-imports-on{dir,file}-t3i.json`, equal to the previous builds' sets.

**The bundle by top-level entry** (the one-folder release; `<ev>\cell\t3i\build-onedir-t3i.log`,
lines 177-262):

| Entry | MiB | Entry | MiB |
|---|---|---|---|
| `ffmpeg.exe` | 217.3 | `_internal/python312.dll` | 6.6 |
| `ffprobe.exe` | 217.1 | `_internal/numpy` | 6.1 |
| `_internal/PySide6` | 73.7 | `_internal/libcrypto-3-x64.dll` | 5.5 |
| `_internal/scipy` | 46.1 | `_internal/libstdc++-6-*.dll` (pillow-heif) | 2.5 |
| `_internal/libx265-217-*.dll` (pillow-heif) | 21.6 | `_internal/libheif-*.dll` | 2.1 |
| `_internal/numpy.libs` | 20.2 | `_internal/base_library.zip` | 1.3 |
| `_internal/scipy.libs` | 19.3 | `_internal/shiboken6` | 1.1 |
| `_internal/PIL` | 10.7 | `_internal/unicodedata.pyd`, `ucrtbase.dll`, `libssl-3-x64.dll` | 1.1, 1.1, 1.0 |
| `Clearwater.exe` | 10.2 | `_internal/libde265-*.dll` (pillow-heif) | 0.9 |
| | | 64 more entries (`.pyd` files and DLLs) | 0.2 or less each |

Total 668.3 MiB. Inside `PySide6`, the split is from turn 2's build 2 (ledger, "Turn 2 group A";
`PySide6` was 73.7 MiB then too); the final build log does not break it down:
`opengl32sw.dll` 20, `Qt6Core` 10, `Qt6Gui` 9.3, `Qt6Widgets` 6.3, `translations/` 6.9,
`plugins/` 5.7 (`imageformats` 2.4, `platforms` 2.2, `tls` 0.66, `styles` 0.24, `generic` 0.10,
`networkinformation` 0.08, `iconengines` 0.07). The one-file executable holds the same content,
compressed (89.5 MiB); no per-folder figure exists for it.

**Data files.** None from `clearwater`. The photo path reads embedded ICC profiles only; the
Display P3 profile is built in code (ledger, "Round 0", item 4).

**FFmpeg.** The laptop's FFmpeg 9.0.2, build `full_build-www.gyan.dev` (`ffmpeg version
9.0.2-full_build-www.gyan.dev`, from the build logs), copied beside the executable for the
PATH-less proof only. **Its licence was not recorded in the spike** (the configure line was not
captured); WP6.3 reads it before choosing the bundled FFmpeg. The bundle rule is WP6.3's.

**Build-log warnings**, the same in every build: `Hidden import "scipy.special._cdflib" not
found!` (benign: scipy 1.18.1 has no such module), and CuPy's `CUDA path could not be detected`
printed by PyInstaller's analysis process, which imports the dev venv's CuPy at build time
only. Neither artifact contains CuPy (the bundle check).

## 5. The plugin and path check list

| Check | Result | Record |
|---|---|---|
| Both forms build from one script | PASS | ledger, "Turn 3 group 2c-a" |
| First window, both forms (pack present and absent) | PASS: 1.093 / 1.198 s one-folder, 2.677 / 2.714 s one-file; title `Clearwater`; a UIA element tree under it (105 elements) | `<ev>\cell\t3i\gui-check.jsonl` |
| The loader's line, VERBATIM from the redirected log, pack present | PASS: `2026-11-04T05:45:11.655-10:00 INFO clearwater.gpu_pack gpu pack 14.2.0-cu12: loaded` (one-folder); `...05:45:23.191... loaded` (one-file) | `gui-check.jsonl` |
| The loader's line, pack renamed away | PASS: `2026-11-04T05:45:16.492-10:00 INFO clearwater.gpu_pack gpu pack 14.2.0-cu12: absent` (one-folder); `...05:45:30.235... absent` (one-file) | `gui-check.jsonl` |
| Clean close (`WM_CLOSE` to Clearwater's own window) | PASS: exit 0 in all four launches; no process and no `_MEI` left | `gui-check.jsonl`; `GUI CHECK: PASS`, exit 0 (`<ev>\cell\t3i\seat-run\gui-check.stdout`) |
| Qt plugins loaded at the first window | `platforms/qwindows.dll` and `styles/qmodernwindowsstyle.dll` only, every `Qt6*.dll` from the bundle (one-folder, turn 2). The dev-run baseline for comparison was NOT taken. | ledger, "Turn 2 group B" |
| HEIC in -> PNG out, EXIF carried, frozen worker | PASS, both forms: eXIf 178 B equal to `exif.edit(source, 96, 64)` | ledger, "Turn 3 group 2b-1", "The frozen worker, headless" |
| JPEG in -> PNG out (D22: photo output is PNG), frozen worker | PASS, both forms (the fixture carries an ICC profile and no EXIF) | the same |
| Video (`vfr.mp4`) -> MP4, frozen worker | PASS, both forms, CPU and GPU | 2b-1; ledger, "Turn 3 group 2b-6", item 5 |
| FFmpeg beside the executable used, with `PATH` = Windows only and the working directory outside the release | PASS: the bundled `ffmpeg.exe` / `ffprobe.exe` were spawned | 2b-1 |
| The write journal (D85): a worker killed mid-export, then the start-up clean-up | PASS, both forms: the entry kept, the partial file removed by `clean_leftovers`, the journal empty | 2b-1, "The write journal (D85)" |
| TIFF in, frozen | NOT exercised | -- |
| The GUI's own photo and video export, both forms | PENDING: the owner's D6 hand check | ledger, "Turn 3 group 2c-a", "The owner's hand check (D6)" |
| Time to the first photo export through the GUI | NOT timed (D6 as ruled; headless figure in section 2) | -- |

Every GUI launch ran with APPDATA, LOCALAPPDATA, TEMP / TMP and XDG_* redirected under
`work\wp6.1\t3c\appdata\`, with a 60 s hard bound, and sent no input (ledger, "Turn 3 group 2c-a",
"The two scripts"). The owner's log md5 was `69ed0432...` before and after.

## 6. The frozen spawn and re-entry mechanism (material for AD-34)

The export worker is a `subprocess.Popen` of a command built in `app/composition.py`, not a
`multiprocessing` spawn (brief, Q5). In a frozen build `sys.executable` is `Clearwater.exe`,
which ignores `-m`. `src/clearwater/__main__.py` now dispatches; `main()` acts on the
arguments in this order (ledger, "Turn 3 group 2b-5"):

1. **Multiprocessing refusal, first, frozen only.** Any `--multiprocessing-fork` or
   `--multiprocessing-resource-tracker` anywhere in the arguments: `Clearwater:
   multiprocessing children are not supported`, status 2. Nothing runs before it, not even the
   PATH step. `freeze_support()` is not called. The only such string the bundled code emits is
   `--multiprocessing-fork` (read from both bundles; ledger, "Reviewer A r3 fold-in", #3).
2. **PATH, frozen only (D1, then r2 #10).** The executable's folder is moved to the front of
   `PATH`, once. Every other spelling (case, trailing separator, quotes) is removed and the
   other entries keep their order. So the bundled FFmpeg is found first and deterministically.
   (PyInstaller's PySide6 runtime hook adds its own two entries first; the move puts the
   folder back in front.)
3. **`--export-worker`, frozen only.** The worker branch: the F-E stdin shim, then the GPU pack
   loader, then `clearwater.app.export_worker.main(argv[2:])`. Nothing Qt-bearing is imported
   on this branch. A source run of `python -m clearwater --export-worker` reaches the GUI, as in
   1.0.0 (A r3 #1). `app/composition.py` builds `[sys.executable, "--export-worker"]` when
   frozen and the unchanged `-m clearwater.app.export_worker` command otherwise.
4. **`-m` / `-c`, frozen only (F-D).** The arguments are read with CPython 3.12's option grammar.
   - `-c` is refused: `Clearwater: -c is not supported`, status 2.
   - `-m <module>` is accepted only when the module's top-level package resolves from the
     ACTIVATED pack folder: every location of its spec (origin and namespace portions) lies
     under the pack's `site-packages` (`gpu_pack.module_from_pack`). It then runs through
     `runpy.run_module(..., run_name="__main__", alter_sys=True)`, after the loader, Qt-free.
     Anything else is refused with one stderr line, status 2, and no GUI (for example
     `Clearwater: -m 'http.server': no GPU pack is loaded`).
   - Why it exists: `cuda.pathfinder` starts its canary as `[sys.executable, "-m", ...]`. Before
     this handler, that canary started the frozen GUI branch (the second incident, section 9).
5. **Anything else** starts the GUI, as in 1.0.0 (with D3's early `configure_logging` and the
   loader, frozen only).

**The option grammar, derived by execution and pinned to the version** (ledger, "Turn 3 group
2b-5", "The grammar, derived by execution"; `<ev>\cell\t3g\grammar-letters.txt`). Every ASCII
letter and every long option was run through the dev interpreter (CPython 3.12.13, the bundle's
version). Result: 16 flag letters `b d i q s t u v x B E I O P R S` (they may be clustered), 2
value letters `W X`, and one long run-modifier, `--check-hash-based-pycs` with `always` /
`default` / `never` as the next argument. Informational options (`-h`, `-V`, `-?`, `--help*`,
`--version`), unknown options and the `=` spelling are not re-entries and reach the GUI, as
CPython would refuse or print and exit. `GRAMMAR_PYTHON_VERSION_INFO` = `(3, 12, 13, "final", 0)`
is recorded in `__main__`; a test fails with "re-derive it" when the running minor version
differs.

**The F-E stdin shim: TEMPORARY, fail-closed, one N1 site.**

- The problem (F-E): the worker's cancel thread blocks reading the protocol pipe on fd 0. Any
  Python child that inherits that stdin (CuPy's canary did) hangs at its own start-up, before
  any Clearwater code runs (`<ev>\cell\t3e\repro_stdin.py`: base CPython hangs the same way).
- The shim (`isolate_worker_stdin`, frozen only, the first thing on the worker branch): it
  duplicates fd 0 to a private, non-inheritable descriptor that becomes `sys.stdin`, and points
  fd 0 at `os.devnull`. On win32 it also calls `SetStdHandle(STD_INPUT_HANDLE, ...)` under a
  `sys.platform` guard: the one new N1 site.
- It fails closed (A r4 #4): any failure ends the worker with `Clearwater: worker stdin
  isolation failed: <type>`, status 2, before the loader, any log or the worker import. The only
  fallback is `os.dup(0)` raising `OSError` with `EBADF` (no standard input at all).
- It is TEMPORARY: DR-125's package moves the isolation into `app/export_worker.py` and removes
  the shim (`tools/package/README.md`, "The frozen worker's standard input").

**QtCore in every frozen process (A r2 #3; CHARC ruled (i)).** PyInstaller's PySide6 runtime hook
imports QtCore in every process of the bundle before the entry script. Measured on the 2b-1
builds (a guide, not exclusive; ledger, "Turn 3 group 2b-1", "#3 measurement"):

| Worker | First message, s (median) | Private memory, MiB (median) | Qt-family DLLs mapped |
|---|---|---|---|
| one-folder `--export-worker` | 0.543 | 1,047.8 | `Qt6Core.dll`, `pyside6.abi3.dll`, `shiboken6.abi3.dll` |
| one-file `--export-worker` | 2.375 | 1,047.9 (worker) | the same three |
| source `python -m clearwater.app.export_worker` | 0.720 | 1,044.0 | none |

No `Qt6Gui`, no `Qt6Widgets`, no platform plugin. The cost is about +4 MiB and no start-up
penalty against the source worker, inside CHARC's guide (0.3 s, 40 MB). AD-31's concern (GIL
contention from the GUI stack and its event loop) does not arise without a QApplication.

**Collateral, named:** `-qmljsdebugger=...` (a Qt option) matches the grammar as `-q` then `-m`,
so it is refused (`-m 'ljsdebugger=...': not a GPU pack module`). Clearwater has no QML.

**Proved on the final-code behaviour** (builds of `926bfdfa`, whose code differs from
`dc784b4f` only by one docstring; ledger, "Turn 3 group 2b-6", item 3): ten refusal rows per
form (`-c pass`, `-m http.server`, both multiprocessing flags, `-R -c pass`, `-t -m http.server`,
`-Rt -c pass`, `--check-hash-based-pycs always -c pass`, `--check-hash-based-pycs never -m
http.server`, `-m http.server --multiprocessing-fork`). Each: status 2, its one line, no
window, nothing left, no `_MEI`, and nothing created or changed in the redirected tree. The
final builds were read out (nothing executed): every entry-script function, every `gpu_pack`
function and the six grammar constants equal `dc784b4f`'s source
(`<ev>\cell\t3i\handler-check-t3i.json`, `HANDLER CHECK: PASS`).

## 7. The GPU pack loader (material for AD-33)

**Layout and stamp.** `<pack root>\<stamp>\manifest.json` and `<pack root>\<stamp>\site-packages\`.
The stamp is the locked `cupy-cuda12x` version plus the CUDA major: `14.2.0-cu12`. The pack root
(Q6): `%LOCALAPPDATA%\Clearwater\gpu-pack` on Windows, `$XDG_DATA_HOME/clearwater/gpu-pack`
(default `~/.local/share/...`) on Linux, none on macOS. The loader acts only when frozen (D4),
so a source run and the gate are unaffected.

**The pack's content:** the eleven locked distributions (`cupy-cuda12x` 14.2.0, `cuda-pathfinder`
1.8.3, `cuda-toolkit` 12.9.2.0 and eight `nvidia-*-cu12` wheels). `numpy` stays in the bundle. The
hand-filled pack holds 2,701 files, 2,412.6 MiB (ledger, "Turn 3 group 2b-2", item 6).

**The manifest:** format 1, the stamp, and per distribution its name, version, wheel file name
with the lock's sha256, and the sha256 of its installed RECORD. A test keeps the loader's table
equal to `uv.lock`.

**The cheap start-up check** (every frozen start; CHARC's r2 ruling): the manifest matches the
lock; each RECORD's sha256 matches the manifest; every RECORD row's file exists with RECORD's
size (no hashing of the files); every top-level entry of `site-packages` is owned by one of the
eleven RECORDs (an unlisted package or `.pth` is rejected, so nothing can shadow the bundle's
numpy); each wheel's platform tag fits the running platform. Any failure, or any exception, is
`rejected: <reason>` (one ASCII line) and the CPU path.

**Its cost:** `check_pack` alone took 0.066 s (median of 5, 0.058-0.072 s) on the real pack. In
the frozen worker, with against without the pack: +0.015 s one-folder, +0.065 s one-file, within
the spread. This was measured on a shared host, as a guide (ledger, "Turn 3 group 2b-2", item 8).

**The full `--verify`** (`build.py --verify <pack folder>`, for the hand-filled pack; WP6.3's
downloader does the same once at install): everything above, plus every listed file's sha256
and size, plus a walk of every file under `site-packages` that lists any file no RECORD names,
`__pycache__` included (Q2). The full verify took 26 s cold and 4 s warm. It was run before and
after every pack-activating group and passed each time with the same figures.

**Activation, after a pack is accepted:**

- on `win32` only, `os.add_dll_directory` for each `site-packages\nvidia\*\bin` (D2), because
  `cuda.pathfinder` loads DLLs with a search that honours `AddDllDirectory` and ignores `PATH`;
- `site-packages` inserted at `sys.path[0]`, once;
- **F-F:** the pack's `site-packages` put first in `site.PREFIXES` (`add_site_prefix`), so
  `site.getsitepackages()` lists it. `cuda.pathfinder` finds both the wheel DLLs and the CUDA
  headers through `site.getsitepackages()`, not `sys.path`.

**The proof** (ledger, "Turn 3 group 2b-4" item 4 and "Turn 3 group 2b-6" item 5; tool
`<ev>\cell\t3h\proof4.py`; records `<ev>\cell\t3h\proof5.jsonl`):

- Command: `<release>\Clearwater.exe --export-worker`, spawned as `jobs/export_process.py`
  spawns it. APPDATA, LOCALAPPDATA, TEMP / TMP and XDG_* under `work\wp6.1\t3c\appdata\`;
  `PATH = C:\Windows\System32;C:\Windows`; every `CUDA_PATH*` removed; a fresh, empty kernel
  cache per form; a read-only UI Automation window watch beside each run.
- Requests: `heic-ad24-both.heic` -> PNG and `vfr.mp4` -> MP4, c3 defaults.

| Form | Request | Exit | Device | Output | Kernel cache | Files mapped |
|---|---|---|---|---|---|---|
| one-folder | HEIC -> PNG | 0 | `GPU`; log `export heic-ad24-both.heic: ok; device GPU` | 37,080 B, ok | 0 -> 52 | 67 = 59 pack + 8 driver + 0 elsewhere |
| one-folder | video | 0 | `GPU` | 55,168 B, ok | 52 -> 62 | the same 67 |
| one-file | HEIC -> PNG | 0 | `GPU` | 37,080 B, ok | 0 -> 52 | the same 67 |
| one-file | video | 0 | `GPU` | 55,168 B, ok | 52 -> 62 | the same 67 |

- **67 mapped files = 59 pack + 8 driver + 0 elsewhere**, in every run (`<ev>\cell\t3h\mapped-cuda-files.tsv`).
  The pack's 59: `cublas64_12.dll`, `cublasLt64_12.dll`, `nvrtc64_120_0.dll`,
  `nvrtc-builtins64_129.dll`, and 55 CuPy extension modules. The driver's 8: `nvcuda.dll` in
  `System32` and seven files in the driver store. No CUDA toolkit, no `CUDA_PATH` and no bundle
  copy appears.
- **The kernels compiled** with the pack's NVRTC: each form's empty cache gained 52 `.cubin`
  files during the HEIC run and 10 more during the video run.
- **The canary.** No canary child ran in any worker run, and when run standalone it returns
  promptly (`not-found`, 0.27 s onedir / about 2.5 s onefile) (ledger, "Turn 3 group 2b-4",
  "The canary, the kernel, pathfinder, the site flags", 1). The canary uses system search only,
  which correctly does not reach the pack.
- **Header lookup: INFERRED.** `find_nvidia_header_directory("cudart")` / `("nvrtc")` were not
  printed from a frozen process (no pack module can call them, and nothing may be planted in
  the pack). Three legs support it:
  1. frozen `-m cuda.pathfinder._dynamic_libs.dynamic_lib_subprocess load cudart` / `load nvrtc`
     returned the pack DLL paths through `find_sub_dirs_all_sitepackages`, the same reader as
     the header step;
  2. the kernels compiled where they had failed before F-F (`Failed to find CUDA headers`);
  3. 2b-3's base-CPython reproduction printed `<pack>\nvidia\cuda_runtime\include` and
     `<pack>\nvidia\cuda_nvrtc\include` once the pack was in `site.PREFIXES`
     (`<ev>\cell\t3e\headers-repro-prefixes.out`).
- **No user site.** In the frozen process the user's site-packages is not on `sys.path`, and
  `site.ENABLE_USER_SITE` is falsy (observed by a plant probe in the redirected profile; ledger,
  "Turn 3 group 2b-3 (items 4-5)", "Item 4 addition"). The exact `sys.flags` values were reasoned,
  not printed.
- **No window, nothing left, the pack untouched:** 0 UIA elements and 0 visible windows in every
  run; no process or `_MEI` left; the pack gained and lost 0 files; `--verify` PASS after.

**Without the pack (the regression; AD-9's text).** With the folder renamed, the frozen worker's
device is `CPU: CuPy not installed`, its warning `Processed on the CPU (CPU: CuPy not
installed).`, its log `CuPy not installed: No module named 'cupy'`, and the PNG is written
(37,104 B), both forms (ledger, "Turn 3 group 2b-6", item 6). The GUI logs `gpu pack
14.2.0-cu12: absent` (section 5). This is 1.0.0's behaviour.

**Rejections, proved on the frozen worker** (ledger, "Turn 3 group 2b-2", item 7): one byte added
to `cupy/__init__.py` (`rejected: cupy-cuda12x file cupy/__init__.py size 42867, RECORD says
42866`), a planted `numpy` package (`rejected: unlisted entry in site-packages: numpy`), and a
Linux wheel tag (`rejected: cupy-cuda12x wheel tag cp312-cp312-manylinux2014_x86_64 is not for
win_amd64`). Each gave the CPU path and a written PNG, both forms.

## 8. Failures and what they imply for WP6.3

**Findings, each with its resolution:**

| ID | Finding | Resolution |
|---|---|---|
| D1 | FFmpeg "beside the executable" is not found by `shutil.which` unless it is the working directory. | Frozen `PATH` prepend of the executable's folder (CHARC D1), later move-to-front with dedupe (r2 #10, r3 #6). |
| F-A | The export worker crashes after its result line at interpreter shutdown (exit 3221225477). A 1.0.0 worker defect, reproduced on the source worker. | DR-125. Not fixed here (`app/export_worker.py` is not owned). See section 9. |
| F-B | One-file: the parent holds the bootloader's PID; killing it leaves the worker running and an orphaned `_MEI`. | A CP6a input (section 1). If one-file is chosen, WP6.3 needs a job-object kill. |
| F-C | `uv pip install --target` leaves an empty `.lock` file that the ownership check rejects. | Removed by hand from the spike's pack; README step. CHARC: no allowlist. |
| F-C2 | The bundle lacked stdlib modules that only the pack imports (`ctypes.wintypes`, `graphlib`, also `site`, `ctypes.util`, `unittest.mock`). | The 61-module hidden-import set and its build-failing check (section 4). |
| F-D | `cuda.pathfinder`'s canary `[sys.executable, "-m", ...]` started the frozen GUI branch. | The pack-scoped frozen `-m` handler, `-c` refused, the full grammar (section 6). |
| F-E | Any Python child inheriting the worker's protocol stdin hangs at start-up. | The TEMPORARY fail-closed stdin shim (section 6); removed by DR-125's package. |
| F-F | `cuda.pathfinder` finds headers and wheel DLLs through `site.getsitepackages()`, not `sys.path`. | `add_site_prefix`: the pack first in `site.PREFIXES` (section 7). |

**Reviewer A** (Codex at the orchestrator's seat; texts `<ev>\A\r1..r5\review.txt`):

| Round | Verdict | Findings | Outcome |
|---|---|---|---|
| r1 (on turn 2's `tools/package`) | NEW_CRITICAL_MAJOR_FOUND | 4 MAJOR, 4 MINOR, 3 ADVISORY | all fixed except F9 (banked, out of envelope) |
| r2 | NEW_CRITICAL_MAJOR_FOUND | 6 MAJOR, 6 MINOR, 2 ADVISORY | fixed; #1 / #2 / #7 (pack check scope) and #3 (QtCore) ruled by CHARC then built; #14 banked |
| r3 | NEW_CRITICAL_MAJOR_FOUND | 4 MAJOR, 6 MINOR, 2 ADVISORY | all fixed (#3: multiprocessing refused, CHARC) |
| r4 | NEW_CRITICAL_MAJOR_FOUND | 1 MAJOR, 4 MINOR, 2 ADVISORY | all fixed except #7 (banked, out of envelope) |
| r5 | **NO_NEW_CRITICAL_MAJOR** | 1 MINOR, 3 ADVISORY (test or docstring only) | all fixed in `dc784b4f` |

**For WP6.3:**

- Set `CUDA_CACHE_PATH` under the Clearwater cache root before CUDA initialises (otherwise the
  driver's JIT cache lands in the real `%APPDATA%\NVIDIA\ComputeCache`), alongside
  `CUPY_CACHE_DIR` (CuPy's default is `%USERPROFILE%\.cupy\kernel_cache`).
- Filter CuPy's "CUDA path could not be detected" UserWarning by its exact message in
  `activate()`. It is printed on every pack-present start and export and is harmless.
- The full `--verify` rejects any reparse point / symlink under the pack, and the downloader
  never creates one (A r4 #7).
- The downloader leaves nothing that RECORD does not own (uv's `.lock`, F-C).
- The full `--verify` form is inherited: the downloader verifies every file once at install.
- A job-object kill if one-file is chosen (F-B).
- Also open from the records: the Linux form of `os.add_dll_directory` (D2) and of the
  `site.PREFIXES` spelling (`lib/python3.12/site-packages`) are unproved; the bundled FFmpeg's
  licence and the bundle rule; the notice rows for PyInstaller's bootloader and run-time modules
  and hooks-contrib's runtime hooks (N13 second pass).

**For WP6.4:** the POSIX-portability advisory (A r5 #4, fixed in `dc784b4f`) goes on WP6.4's
audit list: the frozen-entry tests run on macOS there.

## 9. Limits

- **One machine.** Every figure is from the owner's Windows 11 laptop, one NVIDIA card, one
  driver. Only Windows was exercised for real; Linux and macOS are tested by monkeypatch only.
- **The laptop's FFmpeg** (9.0.2, gyan.dev full build) was copied beside the executable for the
  PATH-less proof. It is not the bundle rule (WP6.3), and its licence was not recorded.
- **The hand-filled pack.** The pack was filled with `uv pip install --target --offline
  --no-deps --link-mode copy` from the uv cache, plus `build.py --write-manifest`. WP6.3's
  downloader is not built.
- **Not measured:** the zipped size of either form; the size and disk need of the one-file
  `_MEI` extraction (its time shows only as the one-file overhead); whether a worker started by
  the one-file GUI reuses the GUI's `_MEI` folder (PyInstaller 6.9+ documents that it does; the
  measured worker starts were headless, so each unpacked its own); the Qt plugin set of a dev
  run, for comparison; a frozen TIFF input.
- **Three incidents, and what changed after each:**
  1. The keystroke incident (turn 2): a GUI check script used `AppActivate` + `SendKeys`, the
     window did not come forward, and keystrokes went to other windows on the owner's desktop.
     Since then: the **desktop input rule** in CLAUDE.md (no synthetic input; UI Automation on
     Clearwater's own elements, PrintWindow, or the owner by hand).
  2. The canary GUI re-entry incident (2b-2, F-D): a library's own re-entry reached the GUI
     branch; the rule held. A window was possible for up to 10 s; no input was sent. Since then:
     no pack-activating run until the frozen `-m` handler is in the build under test, and a
     read-only window watch beside every frozen run.
  3. The before-record source-GUI incident (2b-3): a test run against an old revision started
     the source GUI against the owner's real profile for up to 120 s and appended one line to
     the owner's log (left as it was). Since then: the **entry-point isolation rule** in
     CLAUDE.md (redirect the app-data variables, block the GUI, a bounded timeout, and a grep
     of the test file before any run against an old revision). The owner's log md5 stayed
     `69ed0432...` at every check after it.
- **PID reuse in the seat scripts.** The GUI-check and timing scripts keep each PID's create
  time, so a reused PID is never touched. The orchestrator noted that `post_close` /
  `print_window_png` re-check ownership against the tracked tree (dead PIDs included) rather
  than the live one; negligible, because the window must be visible and titled exactly
  `Clearwater` (ledger, "Group 2c and turn 4").
- **DR-125.** The crash is post-result (exit 3221225477 after the result line and the output),
  and the parent's AD-31 handling reports the export done with the worker's exit code logged.
  It appeared in 1 of the 12 frozen worker runs of groups 2b-4 and 2b-6, and in 0 of the 12
  exports of the turn-4 window (`<ev>\timings\t4\timings.jsonl`: every `exit` is 0).
- **The r4 #7 link residual.** The full `--verify` does not follow directory links, so a file
  behind a planted link escapes its accounting. Banked for WP6.3 (section 8).
- **Windows-only measurement tool (N1 note).** The cold-start and window code in the timing
  tools is Windows-only. CHARC approved it under N1 as a tool, not product.
- **The D6 hand check is pending with the owner:** the GUI's own HEIC and JPEG photo exports to
  PNG and one video export, in both forms (step list in the ledger, "The owner's hand check
  (D6)").
- **Cold copies kept.** The six cold copies (3,750,338,937 B) stay under `work\wp6.1\cold-*`
  until the owner says to delete them.
