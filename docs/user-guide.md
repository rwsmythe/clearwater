# Clearwater user guide

## 1. What Clearwater does

Clearwater improves colour cast, contrast and haze in underwater photographs
and video. It aims for a pleasing view, rather than physically exact colour.
Open iPhone HEIC or JPG photos (PNG and TIFF also work), or GoPro and iPhone
MP4/MOV videos using HEVC or H.264. Videos may be 8-bit or 10-bit. RAW/DNG/ProRAW
photos and native Insta360 recordings are not supported. HDR video tagged with
HLG or PQ transfer characteristics is refused, including Dolby Vision footage
with those transfers: for HLG the message is "This video uses HLG HDR, which
Clearwater does not support. Record in standard (SDR) mode instead." PQ shows
"PQ (HDR10)" in place of "HLG". Use your camera's standard/SDR recording mode
for future clips. See [accepted inputs and refusals](underwater-correction-spec.md).

## 2. Install on Windows 11 (from 1.1.1)

The 1.1.1 Windows artifact bundles FFmpeg and ffprobe beside `Clearwater.exe`;
its artifact notices identify their versions, terms and corresponding sources.

Download **Clearwater-1.1.1-windows-onedir.zip** from the
[Clearwater release page](https://github.com/rwsmythe/clearwater/releases).
This one-folder application includes Python, so Python needs no separate install.
Allow space for the unpacked folder, output files and video cache.

Optionally download the matching `.zip.sha256` file and compare its hash with:

```powershell
Get-FileHash -Algorithm SHA256 .\Clearwater-1.1.1-windows-onedir.zip
```

The hash must match the sidecar's 64 hexadecimal characters. If it differs, do
not run that download; download the assets again from the same release.

Unzip the whole archive anywhere you can write, such as a folder under your user
account, and open the extracted folder. Keep its files and `_internal` folder
together. Double-click **Clearwater.exe**. Do not run it from inside the zip.
Program Files is unnecessary; choose it only if you intend to manage its permissions.
Clearwater stores settings, presets and logs under **%APPDATA%\Clearwater** and
cache/GPU support under **%LOCALAPPDATA%\Clearwater**; exported photos and videos
go to the output folder you choose in Settings.

If Windows SmartScreen shows an unknown publisher, choose **More info** >
**Run anyway** after checking that you obtained this release from Clearwater's
release page. This happens because the application is unsigned (N14).

For GPU processing, choose **Tools > Install GPU support...**, review the wheels,
sizes, destination and NVIDIA licence statement, then press **Download and install**.
The pack is a large download (about 1.7 GB to download, 2.5 GB installed); the dialog calculates the exact
locked download size and installed-space estimate. Installing obtains the
optional NVIDIA components separately under NVIDIA's EULA; the release zip
contains no CUDA libraries. Wait for completion and restart Clearwater to use
the pack. **Tools > Remove GPU support** asks for confirmation and takes effect
at the next start. If a running Clearwater is using the pack, removal is deferred
until the next GUI start; close other Clearwater windows if removal remains pending.

GPU processing needs a CUDA-capable NVIDIA card and a driver supporting CUDA 12.
The locked runtime is CUDA 12.9; use a current NVIDIA driver (the CUDA 12.9
Update 1 Windows driver baseline is 576.57 in
[NVIDIA's release notes](https://docs.nvidia.com/cuda/archive/12.9.1/cuda-toolkit-release-notes/index.html)).
A separate CUDA toolkit install is normally unnecessary. Without a suitable card
or usable GPU libraries, Clearwater uses the CPU and tells you why. Hardware
video encoding is a separate capability from GPU colour processing.

For a terminal or script in **cmd.exe**, use
`start /wait "" Clearwater.exe --install-gpu-pack > install.log 2>&1` or
`start /wait "" Clearwater.exe --remove-gpu-pack > remove.log 2>&1`. This waits for
the windowed executable to finish; it prints only when its output is redirected.
In **PowerShell**, the streams are separate:

```powershell
Start-Process -Wait -FilePath .\Clearwater.exe -ArgumentList '--install-gpu-pack' -RedirectStandardOutput install.log -RedirectStandardError install.err
Start-Process -Wait -FilePath .\Clearwater.exe -ArgumentList '--remove-gpu-pack' -RedirectStandardOutput remove.log -RedirectStandardError remove.err
```

The N13 licence notice is in `install.log`; progress and the installation outcome
are in `install.err`. For removal, read both `remove.log` and `remove.err`; the
outcome is in `remove.err`. Run only the operation you need.

### Developer/source install with uv

Install [Git for Windows](https://git-scm.com/downloads/win) and
[uv](https://docs.astral.sh/uv/getting-started/installation/), then open a new
PowerShell window. Python need not already be installed: uv obtains Python 3.12.

```powershell
git clone https://github.com/rwsmythe/clearwater.git clearwater
Set-Location clearwater
uv sync --no-default-groups
uv run --no-sync python -m clearwater
```

For source GPU support, use `uv sync --no-default-groups --extra gpu` instead.
The ordinary development command `uv sync` installs both **dev and comms** groups,
including CuPy/CUDA, and is larger. Source runs use their environment's GPU extra;
the downloaded pack is loaded by the frozen application at its next start.
Source terminal requests are `python -m clearwater --install-gpu-pack` and
`python -m clearwater --remove-gpu-pack` in that environment.

A source install also needs FFmpeg and ffprobe on PATH; obtain a build with
`libx265` and, for NVIDIA encoding, `hevc_nvenc`. See
[FFmpeg's download page](https://ffmpeg.org/download.html). Add its **bin** folder
to your user **Path**, open a new terminal and check `ffmpeg -version` and
`ffprobe -version`. The packaged application uses its adjacent bundled tools first.

For developer/instrument folder configuration, copy `clearwater.local.example.toml`
to `clearwater.local.toml` and replace its placeholders with absolute paths:
`footage_path` is your read-only source collection, and `working_path` a separate
writable folder for tool outputs, caches and reports. Follow the template's Windows
quoting examples. This Git-ignored file has no FFmpeg setting and does not choose
GUI output/cache folders; use **Tools > Settings** for those. An optional machine
diagnostic, from the repository folder, is:

```powershell
uv run --no-sync --with "psutil>=6,<8" --with "py-cpuinfo>=9,<10" python tools/environment_report.py --out work/environment
```

It prints a dated JSON path under work/environment/reports and explains unavailable
hardware probes. Clearwater's own graphics-card state confirms GPU processing.

## 3. First run: open, compare, adjust and export

From 1.1.1, run **Clearwater.exe** from the unpacked release folder.

For a developer/source install, start from the repository folder with
`uv run --no-sync python -m clearwater`. With the full developer environment,
the usual equivalent is `uv run python -m clearwater`.

1. Choose **File > Open** and select one photo or clip. Start with a short clip
   or a copy of a photo. Read the source and graphics-card information shown by
   the window; video analysis starts when the clip opens.
2. Compare the original and corrected preview by moving the split divider.
   **View > Fit** shows the whole image; **1:1** shows pixel detail. Zoom in/out
   and **Reset split** are also in View. For a clip, scrub the timeline to inspect
   different frames after analysis. A preview is for judging the correction;
   export produces the full-size result.
3. In **Basic**, choose **3C** (the default) or **Ancuti 2018**. Adjust
   **Compensation strength**, **White balance strength**, **Sharpening strength**
   and **Blend with original (%)**. **Blue compensation** applies to Ancuti 2018.
   Use a larger blend percentage to bring back more of the original. Gamma and
   the more detailed controls are in **Advanced**, rather than Basic.
4. In **Presets**, use **Load** to apply a saved look and **Save as...** to keep
   your current settings. **Rename...**, **Delete**, **Import...** and
   **Export...** manage/share presets. Loading a preset changes the current
   correction; it does not overwrite the source.
5. Before exporting, open **Tools > Settings**. Choose a writable **Output
   folder**. **Use source folder** selects the default behavior of writing beside
   each source. For a read-only source collection, always choose a separate
   working/output folder. The default **Output suffix** is _corrected; change it
   here if desired. Choose PNG bit depth or video encoder/quality as appropriate,
   then choose **File > Export** to start the export.
6. The **Export** panel shows the export's status and progress. Its **Cancel**
   button stops the current job and removes its unfinished output; the source
   and any already completed exports remain. For video, export becomes available
   when analysis is complete.
   Cancelling analysis leaves export unavailable until you use **Analyse** again.
7. For several items, in the **Batch** panel, use **Add files...**, check the list,
   and choose **Start**.
   **Remove selected** and **Clear** edit the queue before starting. **Cancel**
   stops the unfinished work and leaves completed batch outputs in place.

Names follow the source name: reef.JPG becomes reef_corrected.png;
dive.MOV becomes dive_corrected.mp4. Photos export as PNG and videos as HEVC MP4.
Existing files are preserved: collisions get _2, _3 and so on, including a MOV
and MP4 with the same stem. These are the [D25/D36 naming rules](underwater-correction-spec.md).

### Optional fixture walkthrough without the window

The repository includes small synthetic fixtures so you can try an export
without your own footage. Make separate output/cache/settings folders first:

```powershell
New-Item -ItemType Directory -Force work/try/photo, work/try/video, work/try/cache, work/try/settings
```

Export one 16-bit photo using the CPU:

```powershell
uv run --no-sync python tools/headless_export.py tests/fixtures/stills/jpeg/jpeg-gradient-srgb.jpg --out work/try/photo --settings-dir work/try/settings --force-cpu --bit-depth 16 --record work/try/photo.json
```

Export the small clip with the CPU and the software encoder:

```powershell
uv run --no-sync python tools/headless_export.py tests/fixtures/video/hevc8-bt709-full.mp4 --out work/try/video --settings-dir work/try/settings --cache-dir work/try/cache --force-cpu --encoder libx265 --quality standard --record work/try/video.json
```

The outputs should be jpeg-gradient-srgb_corrected.png and
hevc8-bt709-full_corrected.mp4. A repeated run adds a collision number. This
functional example makes no performance claim. The automated offscreen launch
check is [the existing application startup smoke](../tests/test_app_startup.py),
which starts the real module entry point and closes its event loop cleanly.

## 4. Working with video

The analysis pass reads the clip's frames, measures whole-frame colour/brightness
statistics and smooths them over time to reduce flicker. Wait for analysis to
finish before exporting. Export then corrects the full-size frames and encodes
them, carrying timing, orientation and supported audio/data tracks. The window
reports metadata it cannot carry; keep the original if you need all camera data.
Changing the correction can require updated statistics/analysis; watch the
timeline's state and **Analyse** control.

The release target is **about 12 minutes of processing per minute of 4K footage**
on a laptop of the tested class with GPU processing. That is the complete
analysis-and-export job, not analysis alone. The recorded cold GPU median was
**10.89 min/min**, on the tested laptop/clip/settings; other footage and hardware
will differ. The CPU route is many times slower. An automatic fallback is reported
on the export as "Processed on the CPU (...)". Choosing **Force CPU processing**
in **Tools > Settings**, under **Advanced**, gives no warning. The status bar's
**Device:** line shows which device is in use. See
[spec D106/N6](underwater-correction-spec.md) and the conditions
and figures in [the WP5.2 performance report](reports/wp5.2-performance-memory.md).
There is no separate fixed analysis-time promise.

Clearwater caches analysis statistics and small JPEG preview proxies. It reuses
matching complete entries and removes older entries to respect **Tools > Settings
> Cache size limit**. **Clear cache** frees that space; analysis must be rebuilt
when needed. On Windows the cache is under %LOCALAPPDATA%\Clearwater\cache.
These are Clearwater's own proxies; camera .LRV files are not used.

**Video quality** offers **High**, **Standard** and **Draft**. Standard is the
normal choice; High favors quality/larger output, and Draft favors a smaller,
rougher review copy. Ten-bit sources keep 10-bit output. For 8-bit sources,
**Write 10-bit video from 8-bit sources** can reduce new quantization during
processing, but cannot recover detail the camera never recorded. Choose an
encoder supporting that output depth; the settings panel explains unavailable
choices. Automatic selection prefers usable NVIDIA HEVC encoding, with libx265
as the software route. Quality/depth rules are [D75/D76 in the spec](underwater-correction-spec.md).

## 5. Working with photos

For iPhone HEIC, Clearwater applies the file's orientation transforms once,
following the primary image's rotation/mirroring information rather than rotating
it again from EXIF. It reads the image's colour information for conversion to the
working colour space, so the orientation/colour interpretation follows the
phone's view; the correction itself deliberately changes the appearance.
See [AD-24 verification](reports/wp3.6p-real-photos.md).

The default output is **16-bit PNG**; 8-bit is available in Settings. The PNG
embeds the ICC profile describing the output colour space, so use a colour-managed
viewer to judge it. The output is not a HEIC or JPG. Clearwater carries supported
EXIF while updating tags affected by the export, such as orientation/dimensions;
it does not copy arbitrary incompatible camera metadata blindly. Keep the source
as your original. See [D22/D53 and the photo rules](underwater-correction-spec.md)
and [the EXIF verification report](reports/wp4.5-exif-bytes.md).

## 6. When something goes wrong (from 1.1.1)

The 1.1.1 Windows artifact bundles FFmpeg and ffprobe beside `Clearwater.exe`; if you moved it, put it back
with the rest of the extracted folder. For a source install, or as a fallback when
the adjacent tools are absent, both tools must be on PATH; open a new terminal
after changing PATH. Keep the bundled versions together rather than mixing builds.

The startup console warning "UserWarning: CUDA path could not be detected. Set
CUDA_PATH ..." from CuPy is harmless and expected without a separate CUDA toolkit
because the ctk wheels carry the runtime; the graphics-card state Clearwater
itself reports is the one that matters.

| What you see | What to do |
| --- | --- |
| HLG HDR / PQ (HDR10) is not supported | Use an SDR source; changing a filename or tag does not convert HDR to SDR. |
| "Clearwater assumes BT.709 colours and limited range for those." | The clip has missing colour tags. This is an assumption, so check the preview against your original. |
| A file cannot be read, or its format is unsupported | Check the accepted formats above and whether the file opens in another viewer. Keep the original and report a small reproducible example if possible. |
| "The video encoder stopped (exit status ...): ..." | FFmpeg failed. Check its error text, disk space, chosen encoder/depth and FFmpeg installation. Try libx265 if hardware encoding is unavailable. |
| "The video encoder (...) stopped accepting data for ... s; the export was stopped." | The encoder stalled; the watchdog ended the export. Retry, or use libx265. The unfinished output is cleaned up. |
| "Not enough free space in ...: need ... bytes, ... free." | Free space or choose a larger output volume, then retry. Cache and temporary output also need room. |
| An output folder cannot be written | Choose a writable folder separate from your protected originals. |

At startup Clearwater attempts to clean up unfinished outputs recorded from a
previous interrupted export, before starting new jobs. Failed cleanup is logged;
there is no special cleanup dialog to wait for. Check the log and the affected
output folder if a previous temporary file remains (D85).

On Windows the rotating log is **%APPDATA%\Clearwater\logs\clearwater.log**, with
numbered backups. These folders follow the platform's application-data settings
([log behavior](../src/clearwater/config/log.py)); they do not come from the
developer's local-config template. Settings/presets are also under
%APPDATA%\Clearwater. The Windows pipe-buffer tuning is Windows-only (AD-23);
the guide's tested platform is Windows 11, and equivalent performance elsewhere
has not been established.

When reporting a problem, send the Clearwater version, exact message, input
format, selected method/quality/encoder, steps to reproduce and relevant log
lines. Include the export's embedded provenance when available: PNG uses
clearwater-provenance and video carries JSON in its metadata. It records version,
parameters and source summary, allowing the settings to be reproduced. Leave
**Embed Clearwater version and parameters** enabled in Settings for this.
Review/redact diagnostic reports and log excerpts before sharing: remove personal
folder paths and other private information. Use file names or placeholders in
your report; do not send your whole photo collection.

## 7. Known limitations and release notes for v1

- **DR-114:** Windows WDDM can make free graphics-memory reporting inaccurate
  for the process; a reported figure is not a guarantee that a large job fits.
  Close other GPU-heavy programs or use the CPU route if needed.
- **DR-115:** intermittent encoder stalls have been seen. They are now bounded
  by the encoder watchdog and reported as a failed export; the underlying stall
  is not claimed fixed. See [WP5.8](reports/wp5.8-watchdog.md).
- **DR-117:** halos on some high-contrast edges against open water; investigated
  in WP5.7; a fix is deferred to a later release by the owner. Inspect edges in
  the preview before exporting; see [the investigation](reports/wp5.7-halo-investigation.md).
- GoPro chapter joining/handling is deferred to v2; open clips individually.
- Native Insta360 input is not supported; that investigation is on hold.
- Camera .LRV proxies are not used. Clearwater makes its own proxy cache.

Version 1.0.0 is the first repository release for the complete photo/video
workflow. It includes presets, batch export, provenance and safe export cleanup.
The release's gate figures and acknowledged debt are recorded at acceptance in
docs/proofs/release-1.0.0.md; the tag is made only with the owner's approval.

### Upgrading on macOS from a 1.0.0 source run

From this release Clearwater on macOS keeps its settings and presets under
`~/Library/Application Support/Clearwater`, so they start fresh there. The
folders a 1.0.0 source run used, `~/.config/clearwater` and
`~/.cache/clearwater`, are not read, moved or deleted: copy a preset you want
to keep from `~/.config/clearwater/presets` into the new `presets` folder (or
use Import... in the Presets panel), and remove the old folders when you no
longer need them.

## 8. Licence (from 1.1.1)

The bundled FFmpeg is built from BtbN's scripts in `rwsmythe/FFmpeg-Builds`
without zvbi.

Clearwater is free software under **GPL-2.0-or-later**, meaning GPL version 2 or
any later version; see [LICENSE](../LICENSE) and
[THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md) for the source-install audit.
The release artifact carries its own generated **THIRD_PARTY_NOTICES.md** beside
`Clearwater.exe`; that file gives the redistributed component terms, full licence
texts and corresponding-source pointers for that artifact. Qt uses LGPLv3 dynamic
linking; when bundled, FFmpeg runs as a separate process and requires GPL-3.0 terms for
the combined artifact under Clearwater's or-later grant. Optional, user-obtained
NVIDIA CUDA components retain NVIDIA's EULA.
