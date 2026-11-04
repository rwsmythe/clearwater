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
- a GPU-pack `.dist-info` / `.egg-info` folder at any depth;
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

The folder must be named for this build's stamp. For each distribution in
`gpu_pack.LOCKED_DISTRIBUTIONS`, the manifest records its version, the locked wheel whose tags
match the installed `WHEEL` file, that wheel's sha256 from `uv.lock`, and the sha256 of the
installed `RECORD` file. The loader rejects the pack when any of these disagrees with the lock
or with the folder. Point `LOCALAPPDATA` at a folder under `work/` for a proof run; never fill
the real `%LOCALAPPDATA%\Clearwater` from the harness.
