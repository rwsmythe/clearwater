# FFmpeg listing texts for the portability tests (WP6.4)

These files feed `tests/test_portability.py` (W-CODEC) with what an arm64 macOS FFmpeg build
prints. They live outside `tests/fixtures/` on purpose: that tree is manifest-checked
(`tools/fixtures/manifest.py`, `tests/test_fixtures.py`), and these are text samples, not
generated media (CHARC's WP6.4 round-0 ruling S1).

| File | Stands for | Provenance |
|---|---|---|
| `vt-encoders.txt` | `ffmpeg -hide_banner -encoders` on an arm64 macOS build with VideoToolbox and libx265 | SYNTHETIC: hand-written on 2026-11-04 in the real six-character flag format of the laptop's FFmpeg 9.0.2 (gyan.dev full build) listing |
| `vt-help.txt` | `ffmpeg -hide_banner -h encoder=hevc_videotoolbox`, trimmed | SYNTHETIC: hand-written on 2026-11-04 from the option names the WP6.2 audit cites (DOC [FF], FFmpeg n8.0 `videotoolboxenc.c`) |

No arm64 capture existed offline: the repository's evidence holds only prose about
VideoToolbox, and the laptop's FFmpeg prints "Codec 'hevc_videotoolbox' is not recognized by
FFmpeg." for the help call. **WP6.5 replaces both files with real captures from the owner's
Mac** (the FFmpeg build that WP6.5 bundles), keeps the `# SYNTHETIC` header off the captures,
and re-runs W-CODEC.

The product reads no more than the encoder-name line of the listing (`capability._listed`).
It never reads the help text; the tests read the help only to check that the `-allow_sw`
option the capability trials pass is one the encoder declares.
