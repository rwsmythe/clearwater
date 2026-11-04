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

## Outputs

```
work/wp6.1/
  dist-<form>/Clearwater-<version>-<platform>-<form>/   the release folder
  build-<form>/                                         PyInstaller's work folder (warn-Clearwater.txt, xref)
  spec-<form>/Clearwater.spec                           the generated spec
```

`<version>` is `clearwater.__version__` read from this tree's `src/`.

## What is left out, and checked

The excluded modules are `EXCLUDED_MODULES` in `build.py`:

- the GPU pack: CuPy, `cuda-pathfinder` and the NVIDIA wheels (never bundled; spec N14). On
  Windows, the application loads them at run time from a per-user folder;
- the test suite and the repository's tools;
- the `dev` and `comms` dependency groups;
- `tkinter`.

After the build, `forbidden_paths` and `forbidden_entries` fail the run (exit 1) if any of the
following appears in the release folder, in the executable's package archive, or in its
frozen-module archive (PYZ):

- `cupy`, `cupyx`, `cupy_backends`, `cuda`, `nvidia`, `fastrlock` or `tests`;
- a GPU-pack `.dist-info`;
- a CUDA library;
- a `clearwater` subpackage frozen at the top level;
- a non-standard-library top-level module outside `ALLOWED_TOP_LEVEL`, which is the product's
  dependency closure from `uv.lock` (this catches a package that leaked in from the dev
  environment).

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
