# Clearwater

Clearwater corrects the colour cast, lost contrast and haze in underwater photos and
video shot with ordinary cameras: an iPhone at snorkel depth, a GoPro on a dive. It aims
for a pleasing, natural-looking image rather than physically exact colour. Everything runs
on your own computer; your photos and videos never leave it.

Version 1.1.1 is a Windows download. Unzip it and run `Clearwater.exe`. No Python, no
installer, no account.

- [Download the latest release](https://github.com/rwsmythe/clearwater/releases)
- [User guide](docs/user-guide.md): installation, a first-run walkthrough, video and photo
  details, troubleshooting
- [Release notes](docs/release-notes-1.1.1.md)

## What it does

- **Photos:** opens iPhone HEIC and JPG (PNG and TIFF also work), corrects the image and
  writes a 16-bit PNG (8-bit optional) with the colour profile embedded and the camera's
  EXIF carried over, orientation applied once and correctly.
- **Video:** opens GoPro and iPhone MP4 or MOV clips in HEVC or H.264, 8-bit or 10-bit.
  A first pass analyses the whole clip and smooths the correction over time so it does not
  flicker; the export writes an HEVC MP4 at full size, carrying timing, orientation and the
  audio and data tracks it can keep.
- **Compare before you export:** a split view slides between the original and the
  corrected image. Fit the whole frame or look at 1:1 pixels. For a clip, scrub the
  timeline and inspect any frame.
- **Two correction methods:** 3C (the default) and Ancuti 2018. Adjust compensation
  strength, white balance strength, sharpening and how much of the original to blend back;
  finer controls live under Advanced.
- **Presets:** save a look, load it later, import and export preset files to share them.
- **Batch:** queue several photos and clips and process them in one run.
- **Safe output:** results are written beside the source or to a folder you choose, named
  `<original>_corrected`. Nothing is ever overwritten; a second export of the same file
  gets `_2`, `_3` and so on. Your originals are never modified.
- **Graphics-card processing, optional:** with an NVIDIA card, install GPU support from
  the Tools menu (a separate download of about 1.7 GB, 2.5 GB installed). Without it,
  everything still works on the processor, many times more slowly for video.

## Requirements

- Windows 11 (Windows 10 is untested). The unpacked program is about 0.7 GB.
- For GPU processing: an NVIDIA card with a driver that supports CUDA 12 (the 12.9
  runtime; driver 576.57 or newer).
- Disk space for the outputs and for the video analysis cache, whose size limit you set
  in Settings.

## Performance

With GPU processing on the laptop used for development, a full analysis and export of 4K
GoPro footage takes about 11 to 12 minutes per minute of video. Other hardware and footage
will differ. The processor-only route is many times slower and is reported on the export
when it is used.

## What it does not do

- **ProRes and other codecs:** only HEVC and H.264 video is accepted. Insta360 Studio
  exports work when exported as H.265; ProRes exports are refused with a message.
- **HDR video:** clips tagged HLG or PQ (including Dolby Vision with those transfers) are
  refused. Record in your camera's standard (SDR) mode.
- **RAW photos:** DNG and ProRAW are not supported.
- **Native Insta360 recordings (`.insv`)** are not supported; export from Insta360 Studio
  first.
- **GoPro chapters** are not joined; open each chapter file on its own.
- **Halos** can appear at some high-contrast edges against open water. Inspect edges in
  the preview before exporting; a fix is planned.
- **Not signed.** Windows SmartScreen may show an unknown publisher the first time; choose
  More info, then Run anyway, after confirming you downloaded it from this repository's
  release page. Each release ships a `.sha256` file to check the download against.

## Platforms

- **Windows:** the download above.
- **macOS (Apple Silicon):** there is no Mac download yet; the Mac version is being
  validated now. To run Clearwater from source on a Mac, install two command-line tools
  first, in Terminal:
  - **Xcode Command Line Tools.** Check with `xcode-select -p`: if it prints a folder,
    they are already installed. If not, run `xcode-select --install` and follow the
    dialog that opens.
  - **uv**, which installs Clearwater's Python and packages. Install the version the
    project's own builds use with `curl -LsSf https://astral.sh/uv/0.10.9/install.sh | sh`,
    then open a new Terminal window and check with `uv --version`.

  uv fetches Python 3.12 by itself. FFmpeg is still needed on your PATH for video, as for
  any source run (next item).
- **From source, any platform:** clone the repository and run it with
  [uv](https://docs.astral.sh/uv/); see the user guide's "Developer/source install"
  section. Python 3.12 and FFmpeg on your PATH are needed for a source run.

## Privacy

Clearwater does not collect anything and makes no network connection, with one exception:
installing GPU support downloads the NVIDIA and CuPy packages from their public package
index, after showing you their sizes and licence terms. Settings, presets and logs live
under `%APPDATA%\Clearwater`; the cache and GPU support under `%LOCALAPPDATA%\Clearwater`.

## Licence

Clearwater is free software under the GNU General Public License, version 2 or any later
version; see [LICENSE](LICENSE). The bundled FFmpeg and the other third-party components
are listed with their licences and sources in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)
(the release zip carries its own copy for exactly the components it contains).

## Developers

The repository is developed by a multi-agent harness; that machinery is documented in
[docs/harness-readme.md](docs/harness-readme.md), and the application's requirements in
[the specification](docs/underwater-correction-spec.md) and
[the implementation plan](docs/clearwater-implementation-plan.md).
