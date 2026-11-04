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
