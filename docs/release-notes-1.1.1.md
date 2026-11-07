# Clearwater 1.1.1

Clearwater corrects colour cast, contrast loss and haze in amateur underwater
photos and video. 1.1.1 is the first release that ships as a download: a
Windows one-folder build attached to this release page. It also installs from
the repository with uv, as 1.0.0 did.

1.1.1 carries the same product code as the tag `v1.1.0`. That tag was pushed,
but its release workflow failed on the fresh GitHub checkout before building
anything (the test step wrote under a folder the checkout does not have), so no
1.1.0 release exists. 1.1.1 fixes the workflow and nothing else. The `v1.1.0`
tag stays in the repository as history.

## What is new since 1.0.0

- **Windows one-folder download.** `Clearwater-1.1.1-windows-onedir.zip` unzips to one folder; run `Clearwater.exe` from it. No installer
  and no system changes. The folder is unsigned, so Windows SmartScreen may
  ask you to confirm the first start. Built by GitHub Actions from the tagged
  commit; the zip's `.sha256` sidecar names the source commit.
- **GPU support as an optional install.** The download runs on the CPU. In the
  app, **Tools > Install GPU support...** downloads the NVIDIA CUDA runtime and
  CuPy wheels (about 1.7 GB to download, 2.5 GB installed) into your user
  profile after showing their terms and size and verifies every file; restart
  Clearwater to use the GPU.
  **Tools > Remove GPU support** removes it. Headless equivalents:
  `Clearwater.exe --install-gpu-pack` and `--remove-gpu-pack`. Requires an
  NVIDIA graphics card with a current driver.
- **Bundled FFmpeg with full provenance.** The download carries its own
  FFmpeg 9.0 (release branch, GPL build with x265 and NVENC), built from
  BtbN's build scripts in the maintainer's fork with the zvbi stage removed so
  that every component is GPL-3.0 compatible. `THIRD_PARTY_NOTICES.md` inside
  the folder lists every bundled component with its licence and source or
  redistribution terms, including code compiled into the carried native
  libraries and into the FFmpeg binary itself (its build components and the
  Rust and GCC runtimes), and carries their licence texts, with the
  exceptions it names.
- **Hardened frozen application.** Video exports run in an isolated worker
  process with its own standard input; an unexpected error in the frozen app
  is written to the log and reported in one message instead of a silent exit;
  the GPU pack is verified file by file when it is installed, and at every
  start its manifest, RECORD hashes, file sizes and file ownership are checked.
- **macOS groundwork.** The code paths for macOS (VideoToolbox encoding,
  Library folders, POSIX process handling) are in this release and run from a
  source install with uv. They have not yet been validated on a Mac, and there
  is no macOS download in 1.1.1.
- **Tooling.** The environment report includes platform facts by default; the
  footage guard refuses writes into the footage folder by file identity; the
  release workflow verifies the annotated tag, pins every action to a commit
  and the build's uv and Python versions, and publishes only a draft.

## Known limitations

- Halos at strong edges in some photos (recorded, fix deferred).
- GoPro chapter joining is not supported; open clips individually.
- Insta360: Studio exports (ProRes `.mov`, HEVC `.mp4`) are the intended input
  and are being validated; native `.insv` files are not supported.
- The Windows download is unsigned.

## Installing from source

```
git clone https://github.com/rwsmythe/clearwater
cd clearwater
uv sync
uv run python -m clearwater
```

See `docs/user-guide.md` for the full guide, including the GPU pack and the
macOS section.
