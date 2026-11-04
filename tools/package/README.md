# tools/package -- the WP6.1 packaging spike's build script

Spike tooling (evidence, not product). It builds Clearwater with PyInstaller in one of two
forms, both from ONE argument list (`pyinstaller_args` in `build.py`):

- `onedir`: a folder holding `Clearwater.exe` and its `_internal/` folder;
- `onefile`: one self-extracting `Clearwater.exe`, which unpacks into `%TEMP%\_MEIxxxx` at
  each start.

PyInstaller is a `dev` group dependency (N13 row approved by CHARC for WP6.1). It runs in the
build script's own process through `PyInstaller.__main__.run(args)`.

## Use

From the repository (or worktree) root, with the synced `.venv`:

```
uv run --no-sync python tools/package/build.py --form onedir
uv run --no-sync python tools/package/build.py --form onefile --with-ffmpeg
```

- `--out <folder>` changes the output folder (default `work/wp6.1/`, gitignored).
- `--with-ffmpeg` copies the `ffmpeg` and `ffprobe` found on this machine's PATH beside the
  executable. It is used for the spike's PATH-less proof only; the real bundle rule, with its
  licence consequences, is WP6.3's.

Check at least 25 GB free on the drive before a build (the brief's floor). Route the build's
output to a file; it is long.

Each build first deletes its own release folder (`dist-<form>/Clearwater-<version>-...`), so
nothing from an earlier build survives into it. PyInstaller's cache goes to
`<out>/pyinstaller-config` (`PYINSTALLER_CONFIG_DIR`), so `--clean` cleans nothing outside the
output folder. FFmpeg is copied under the names `ffmpeg.exe` / `ffprobe.exe` and each copy
must run `-version` from the release folder, with only that folder on PATH; the build prints
the version line.

## Outputs

```
work/wp6.1/
  dist-<form>/Clearwater-<version>-<platform>-<form>/   the release folder
  build-<form>/                                         PyInstaller's work folder (warn-Clearwater.txt, xref)
  spec-<form>/Clearwater.spec                           the generated spec
  pyinstaller-config/                                   PyInstaller's cache (bincache)
```

`<version>` is `clearwater.__version__`, parsed from this tree's `src/clearwater/__init__.py`
(not imported, so nothing is written into `src/`).

## What is left out, and checked

The excluded modules are `EXCLUDED_MODULES` in `build.py`:

- the GPU pack: CuPy, `cuda-pathfinder` and the NVIDIA wheels (never bundled; spec N14). On
  Windows, the application loads them at run time from a per-user folder;
- the test suite and the repository's tools;
- the `dev` and `comms` dependency groups;
- `tkinter`.

After the build, `forbidden_paths` and `forbidden_entries` fail the run (exit 1) on any
violation in what they inspect: every file and folder of the release folder; every entry of
the executable's package archive (CArchive); every module of its frozen-module archive (PYZ);
and every member of every ZIP archive found in any of these (by a ZIP suffix or the ZIP
magic), opened recursively in memory, never extracted. Names are compared lower-case. The
violations:

- `cupy`, `cupyx`, `cupy_backends`, `cuda`, `nvidia` or `fastrlock` as ANY component of a
  path, entry or dotted module name, whatever the entry's type (scripts, run-time hooks and
  PyInstaller's boot modules included; one exception: SciPy's own vendored adapter
  `scipy/_external/array_api_compat/cupy`, which is SciPy's code, `GPU_NAME_EXCEPTIONS`);
- `tests` as the first component;
- a GPU-pack `.dist-info`, `.egg-info` or `.data` folder at any depth, with distribution
  names normalized per PEP 503 (case ignored; runs of hyphens, underscores and dots treated
  as one hyphen);
- a CUDA library file name (`cublas*`, `cudart*`, `cudnn*`, `cufft*`, `curand*`,
  `cusolver*`, `cusparse*`, `cutensor*`, `nccl*`, `nvblas*`, `nvjitlink*`, `nvrtc*`, `nvtx*`,
  with or without `lib`, ending `.dll`, `.so` or `.so.<n>`; a test checks every DLL the locked
  pack wheels install);
- a `clearwater` subpackage (or a package `io`) at the top level;
- a module outside `ALLOWED_TOP_LEVEL` and the standard library: PYZ modules, CArchive module
  entries (PyInstaller's own boot modules exempt from this rule only), the one-file archive's
  binary and data entries, and loose `.py` / `.pyc` / `.pyd` / `.so` files anywhere in the
  release folder (under `_internal`, beside the executable or at the release root), and in a
  ZIP at the bundle's root. `ALLOWED_TOP_LEVEL` is the product's dependency closure from
  `uv.lock`.
- a ZIP that cannot be read, or nested deeper than four levels.

Scope: the allowlist names top-level packages, not distributions, so a module of a different
distribution under an allowed name (for example `PySide6.QtCharts` from PySide6-Addons) would
pass; the locked environment holds no such distribution. The checks were validated on Windows
builds; the Linux library names are covered by the pattern but not by a real Linux build.

## The GPU pack's standard-library needs (hidden imports)

The pack lives outside the bundle, so PyInstaller cannot see the standard-library modules
that only the pack imports (`ctypes.wintypes` from `cuda-pathfinder`, say). Before PyInstaller
runs, `build.py`:

1. scans every `.py` file the eleven pack distributions install in the build environment
   (their `RECORD`, through `importlib.metadata`; the distributions are
   `clearwater.gpu_pack.LOCKED_DISTRIBUTIONS`) with `ast`. An import anywhere counts
   (module level, functions, `if` / `try` blocks), and so do `from __future__ import ...`,
   `importlib.import_module("x")` and `__import__("x")` with a string literal. Relative
   imports, third-party names and non-literal dynamic imports are skipped. A name that
   does not exist on the build platform (`fcntl` on Windows) is recorded, not imported;
2. adds the committed list `PACK_EXTENSION_STDLIB_NEEDS` (`graphlib` today), the needs of
   the pack's extension modules, which no `.py` file names;
3. passes each member as `--hidden-import`, and writes the set, each member marked
   `scan` and / or `committed`, to `work/wp6.1/hidden-imports-<form>.json` and to the
   build log.

After the build, the hidden-import check FAILS the build (exit 1) when any member is
missing from the bundle: the PYZ, the package archive's module entries, `base_library.zip`,
the extension modules (`_internal/` or the one-file archive's binaries), or the
interpreter's built-ins. A pack file that cannot be parsed fails the build before
PyInstaller runs, and so does a pack distribution that is not installed in the build
environment. So a lock bump that brings a new standard-library need fails the build or
bundles the module; it never reaches a user's GPU as an import error.

## The export worker's standard input

The export worker isolates its own standard input in source and frozen runs, after its
argument check and before reading the request or running any backend probe or job. It
duplicates the request pipe to a private, non-inheritable descriptor and points descriptor 0
(and the Win32 standard-input handle on Windows) at the null device, so every child it spawns
with inherited stdin gets EOF, including CuPy's pathfinder canary. One raw `os.read` reader
serves the request and the daemon cancel watcher without a buffered-reader lock at interpreter
shutdown. The original `sys.stdin` object stays bound to descriptor 0; the watcher is neither
joined nor closed at exit. Isolation fails closed on any `Exception`, with status 2 and one stderr
line (`export worker: stdin isolation failed: <exception type>`); absent stdin follows the normal
empty-request refusal. The frozen entry branch runs the GPU pack loader and then the worker;
it has no stdin shim.

## The GPU pack manifest

The frozen application loads CuPy and the CUDA wheels from a per-user folder, the GPU pack
(`src/clearwater/gpu_pack.py`, AD-33):

```
<pack root>/<stamp>/manifest.json
<pack root>/<stamp>/site-packages/
```

`<pack root>` is `%LOCALAPPDATA%/Clearwater/gpu-pack` on Windows and
`$XDG_DATA_HOME/clearwater/gpu-pack` on Linux; macOS has none. `<stamp>` is the locked
`cupy-cuda12x` version plus the CUDA major version (`14.2.0-cu12`). The loader acts only in a
frozen build, and only reads the folder.

For the spike the pack is filled by hand with the eleven locked wheels (`--no-deps`, from the
uv cache, no network), and the manifest is then written by this script:

```
uv pip install --offline --no-deps --target <pack root>/<stamp>/site-packages <the eleven pins>
uv run --no-sync python tools/package/build.py --write-manifest <pack root>/<stamp>
```

`uv pip install --target` leaves an empty `.lock` file in `site-packages` (uv's own
install lock). No `RECORD` owns it, so the loader's ownership check rejects the pack
until it is removed: delete `<pack root>/<stamp>/site-packages/.lock` before writing the
manifest.

The folder must be named for this build's stamp. For each distribution in
`gpu_pack.LOCKED_DISTRIBUTIONS`, the manifest records its version, the locked wheel whose tags
match the installed `WHEEL` file, that wheel's sha256 from `uv.lock`, and the sha256 of the
installed `RECORD` file. The loader rejects the pack when any of these disagrees with the lock
or with the folder. Point `LOCALAPPDATA` at a folder under `work/` for a proof run; never fill
the real `%LOCALAPPDATA%\Clearwater` from the harness.

### What the loader checks at every start-up, and `--verify`

The CHEAP check (`gpu_pack.check_pack`, every start-up, no file hashed but the `RECORD`
files) rejects the pack, with a one-line reason and the CPU path, when:

- (d) the manifest disagrees with the lock (above), or a `RECORD` file with the manifest;
- (c) no `Tag:` line of a distribution's `WHEEL` file fits the running interpreter and
  platform (`gpu_pack.tag_fits`: `win_amd64` here; on Linux a `manylinux` tag of the same
  machine, its glibc version not compared);
- (a) a `RECORD` row is malformed or leaves `site-packages`, or the file it names is missing,
  not a regular file, or not the row's size (a row without a size, the `RECORD` file's own,
  is checked for existence only);
- (b) `site-packages` holds a top-level entry that is not the first path component of any
  row of the eleven `RECORD` files (an unlisted package, module, `.pth` file or
  `.dist-info`), so nothing outside the pack can shadow the bundle's `numpy`.

Hashing every file is the installer's job, once. For a pack filled by hand:

```
uv run --no-sync python tools/package/build.py --verify <pack root>/<stamp>
```

runs the FULL check: all of the above plus each listed file's sha256 (`RECORD`'s urlsafe
base64 form) against the file, any listed file without a hash, and a walk of every file
under `site-packages` that lists each one no `RECORD` row names (`unlisted file in
site-packages: <path>`, `__pycache__` included; Q2). It exits 0 with one
summary line (rows, files, size) when the pack is clean, and 1 with every problem listed.
`--verify` excludes `--form` and `--write-manifest`.
