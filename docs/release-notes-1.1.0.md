# Clearwater 1.1.0

Clearwater corrects colour cast, contrast loss and haze in amateur underwater
photos and video. 1.1.0 is the first release that ships as a download: a
Windows one-folder build attached to this release page. It also installs from
the repository with uv, as 1.0.0 did.

## What is new since 1.0.0

- **Windows one-folder download.** `Clearwater-1.1.0-win64.zip` (name as
  attached) unzips to one folder; run `Clearwater.exe` from it. No installer
  and no system changes. The folder is unsigned, so Windows SmartScreen may
  ask you to confirm the first start. Built by GitHub Actions from the tagged
  commit; the zip's `.sha256` sidecar names the source commit.
- **GPU support as an optional install.** The download runs on the CPU. In the
  app, **Tools > Install GPU support...** downloads the NVIDIA CUDA runtime and
  CuPy wheels (about 2 to 3 GB) into your user profile after showing their
  terms and size, verifies every file, and restarts into GPU mode. **Tools >
  Remove GPU support...** removes it. Headless equivalents:
  `Clearwater.exe --install-gpu-pack` and `--remove-gpu-pack`. Requires an
  NVIDIA graphics card with a current driver.
- **Bundled FFmpeg with full provenance.** The download carries its own
  FFmpeg 9.0 (release branch, GPL build with x265 and NVENC), built from
  BtbN's build scripts in the maintainer's fork with the zvbi stage removed so
  that every component is GPL-3.0 compatible. `THIRD_PARTY_NOTICES.md` inside
  the folder lists every bundled component, including code compiled into the
  carried native libraries and into the FFmpeg binary itself (the Rust and GCC
  runtimes), with the licence texts.
- **Hardened frozen application.** Video exports run in an isolated worker
  process with its own standard input; an unexpected error in the frozen app
  is written to the log and reported in one message instead of a silent exit;
  the GPU pack is loaded only after its manifest and file hashes check out.
- **macOS groundwork.** The code paths for macOS (VideoToolbox encoding,
  Library folders, POSIX process handling) are in this release and run from a
  source install with uv. They have not yet been validated on a Mac, and there
  is no macOS download in 1.1.0.
- **Tooling.** The environment report prints platform facts by default; the
  footage guard refuses writes into the footage folder by file identity; the
  release workflow verifies the annotated tag, pins every action and tool
  version, and publishes only a draft.

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
