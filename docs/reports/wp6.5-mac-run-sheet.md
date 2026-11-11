# WP6.5 stage 2: the Mac run sheet (DRAFT, run ONCE after the runner's run 10)

Status: DRAFT written 2026-11-11 by cell `wp65-sheet1` (dispatch S1, orchestrator generation 70)
from the brief `docs/briefs/wp6.5-brief.md` (Where the work runs, Design items 3, 4, 5, 8, Locks,
Hardware flags, Q4, the CHARC note of 2026-11-06). Docs only. The owner runs this sheet by hand,
ONCE, on the Mac, after run 10 has proved the fixed FFmpeg build (DR-163). The harness never
reaches the Mac; the owner's hands are the only input.

Nothing in this sheet names the Mac's account or host. Refer to the machine as "the Mac".

## 0. Read first

### 0.1 What the seat fills before handing this sheet over (markers)

| Marker | What goes there |
| --- | --- |
| `SEAT_FILLS_VERSION` (in step 4) | the `clearwater.__version__` of the run-10 build, as in the zip name `Clearwater-<version>-macos.zip` |
| `SEAT_FILLS_COMMIT` (in step 4) | the full 40-character commit run 10 built (the zip sidecar's `# source-commit:` line) |
| the DR-163 line (step 30 and section 6) | see the line there; the seat replaces the bracket |
| section 1 item L1 | how the run-10 `.app` zip leaves the runner (see the open point there) |
| section 1 items L2, L4 | the paths the seat used on the laptop |

If a step below still shows a literal `SEAT_FILLS_` token when you reach it, STOP: the sheet was
handed over unfilled.

### 0.2 Rules for the run

- Run the steps in order. Each step is ONE command (copy it whole into Terminal) or ONE hand
  action. Under each step: EXPECT is what you should see; LANDS is where its output file goes;
  IF NOT says what to do.
- Every output goes under ONE folder, `wp6.5-mac/`, inside the program folder (the owner's rule
  of 2026-11-05). The program folder is `/Users/Shared/clearwater-wp65`. It is outside any
  account's home folder, so no account name appears in any path or output.
- Every scripted step that runs Clearwater code (a tool, a test, the packaged program's headless
  rows) runs through `iso`, defined in step 4: it sets HOME and the XDG folders to a disposable
  root inside `wp6.5-mac/` and never starts the window. The account's real
  `~/Library/Application Support/Clearwater` is never touched by a scripted step. The ONLY steps
  that start the window are the hand checks: step 16 is a Finder launch and cannot be isolated
  (see its note); the Terminal launches (steps 47 to 54) run under `iso` through `gui`.
- The measurement steps (section 6, steps 33 to 45) are EXCLUSIVE: nothing else heavy on
  the Mac while they run. Quit every other app, pause Google Drive syncing, do not browse,
  download, or run Time Machine or Spotlight-heavy work. Do not touch the Mac during these steps
  except to read.
- A step that says STOP: write what you saw in `notes.txt` (step 5), skip to step 56 (Part G:
  clean up and copy the folder back) and tell the seat. Do not retry with changes, do not edit
  any file under `Clearwater.app`, do not run `xattr -d` or `xattr -c` on the bundle (that would
  change what this run proves).
- No step sends keystrokes or mouse input for you; none may be run with any automation tool.
- Keep command output exactly as printed; where a step redirects to a file, nothing needs
  copying by hand.

### 0.3 Layout on the Mac

```
/Users/Shared/clearwater-wp65/        the program folder ($PROG)
    in/                               inputs copied from Google Drive ($IN)
    Clearwater.app                    the unzipped build ($APP)
    src/                              the source checkout for the tool legs ($SRC)
    .uv/                              uv's own cache, Python and binary (never copied back)
    env.sh                            the shell definitions (step 4)
    wp6.5-mac/                        EVERY output ($W); the ONLY folder copied back
```

### 0.4 Disk (the CHARC note's first consequence; arithmetic in GiB)

The Mac had 17 GiB free of 460 GiB (97 % used) when the owner measured it (brief, CHARC note
2026-11-06). Peak while every leg is in place:

| Item | GiB |
| --- | ---: |
| inputs `in/`: the zip about 0.5 (estimate), the trim 0.02, the full clip 0.05, the Windows reference record 0.31 | 0.9 |
| the unzipped `Clearwater.app` (the brief's estimate 0.7, rounded up) | 1.0 |
| the source checkout (git, about 0.1) | 0.1 |
| `.uv/`: managed Python, the wheel cache and the venv (PySide6, NumPy, SciPy, Pillow, the dev group; estimate) | 3.0 |
| `wp6.5-mac/` at its end: the AD-11 record about 0.31 (three 4K float32 frames), Q1 outputs 0.1, GUI outputs 0.1, the rest 0.1 | 0.7 |
| transient inside `wp6.5-mac/`, the larger one at a time: the smoke's planted copy of the bundle 1.0, or the macOS test leg's disk images and clips (estimate 1.0); each deleted by its own step | 1.0 |
| **peak** | **6.7** |
| margin (the CHARC note) | 5.0 |
| **stated minimum** | **12 (11.7 rounded up)** |

The one full clip is `GX011589` (the smallest full SCUBA clip, 48,849,388 B = 46.6 MiB, 6.4 s,
3840 x 2160 at 29.97 fps, 8-bit HEVC; inventory `inventory-20261018T235556Z.csv`). Its output is
no larger than its input (the High ceiling, 0.24 bits per pixel, is below the source's own rate)
and is deleted by step 41 after the figure is recorded. The alternative, `GX011592` (378 MiB,
42.3 s), would add about 0.7 GiB (still inside 12); it is the seat's call before hand-over.

## 1. What the seat prepares on the laptop (before this sheet is handed over)

The Mac has no footage folder and the harness never reaches it. The seat builds ONE Drive folder,
`wp6.5-mac-in`, the owner copies it to the Mac in step 8:

| Item | Content | How | Size |
| --- | --- | --- | ---: |
| L1 | `Clearwater-<version>-macos.zip` and `Clearwater-<version>-macos.zip.sha256` | the run-10 build, downloaded at the seat (`gh run download`, read-only) and put in the folder. OPEN POINT: in validation mode the `macos` job uploads only `macos-evidence` (`.github/workflows/macos-build.yml:322-328`); `macos-release` (the zip) is uploaded only when `inputs.release-version` is set (`:314-320`), so run 10 as the workflow stands does not keep the zip off the runner. [SEAT FILLS: how run 10 delivers the zip.] | 0.5 GiB |
| L2 | `GX011627-trim.mp4`: the 90-frame stream-copy trim of `Snorkel/GX011627.mp4` | the command and the checks are the `gx011627_trim` fixture's (`tests/conftest.py:837` `_gx011627_trim_plan`, `:579` `gx011627_trim_checks`); the fixture deletes its trim at teardown, so the seat makes a persistent copy by that same plan [SEAT FILLS: the path used and the frame count] | 0.02 GiB |
| L3 | `GX011589.mp4`: the full clip | a plain copy of `SCUBA/GX011589.mp4` (read from the footage folder, never written to it) | 0.05 GiB |
| L4 | `win-ref/`: the Windows reference for the AD-11 comparison | on the laptop, with the trim from L2 copied OUTSIDE the footage folder under the SAME file name: `uv run python tools/export_oracle.py record --file <path>\GX011627-trim.mp4 --force-cpu --name win-ref` (`tools/export_oracle.py:700-717`; the record folder is `<working>\wp3.21\oracle\win-ref`, holding `oracle.json` and `frames\`). It must be a CPU record: `compare` fails when `force_cpu`, `method`, the clip name or the source size differ (`tools/export_oracle.py:531-545`) | 0.31 GiB |
| L5 | `SHA256SUMS.txt` | from inside `wp6.5-mac-in`: `find . -type f ! -name SHA256SUMS.txt -print0 \| sort -z \| xargs -0 sha256sum > SHA256SUMS.txt` | - |

The folder totals about 0.9 GiB.

## 2. Setup (steps 1 to 7)

### Step 1 -- check the free space (GATE)

```
df -h ~
```

EXPECT: one line for the Data volume (for example `/dev/disk3s5 ... /System/Volumes/Data`) whose
Avail column is at least **12 Gi** (section 0.4).
LANDS: the terminal only (step 7 records it again).
IF NOT: STOP. Below 12 Gi free, free space first: empty the Trash, delete large downloads and
old Time Machine local snapshots (`tmutil listlocalsnapshots /`, `tmutil deletelocalsnapshots`),
then run this step again. Do not start the run below 12 Gi.

### Step 2 -- quiet the Mac (hand action)

Quit every other app (browsers, mail, messages, Photos). Pause Google Drive syncing (its menu-bar
icon > pause) until step 59. Plug the Mac into power. Leave one Terminal window open.
EXPECT: Activity Monitor (if you look) shows the CPU idle.
LANDS: nothing.

### Step 3 -- make the folders

```
mkdir -p /Users/Shared/clearwater-wp65/in /Users/Shared/clearwater-wp65/wp6.5-mac
```

EXPECT: no output.
LANDS: the two folders.

### Step 4 -- write the shell definitions

Copy the whole block, including the first and last line, into Terminal:

```
cat > /Users/Shared/clearwater-wp65/env.sh <<'EOF'
PROG=/Users/Shared/clearwater-wp65
W=$PROG/wp6.5-mac
IN=$PROG/in
APP=$PROG/Clearwater.app
SRC=$PROG/src
VERSION=SEAT_FILLS_VERSION
COMMIT=SEAT_FILLS_COMMIT
ZIP=$IN/Clearwater-$VERSION-macos.zip
export UV_CACHE_DIR="$PROG/.uv/cache" UV_PYTHON_INSTALL_DIR="$PROG/.uv/python" UV_TOOL_DIR="$PROG/.uv/tools"
export UV_FROZEN=1 UV_NO_SYNC=1 UV_PYTHON_PREFERENCE=only-managed UV_PYTHON=3.12.13
export PATH="$PROG/.uv/bin:$APP/Contents/MacOS:$PATH"
# iso CMD...: run CMD with HOME and the XDG folders redirected into wp6.5-mac/ (never the real profile)
iso() (
  mkdir -p "$W/home" "$W/xdg-config" "$W/xdg-cache" "$W/xdg-data" "$W/tmp"
  export HOME="$W/home" USERPROFILE="$W/home" XDG_CONFIG_HOME="$W/xdg-config" XDG_CACHE_HOME="$W/xdg-cache" XDG_DATA_HOME="$W/xdg-data" TMPDIR="$W/tmp"
  unset PYTEST_ADDOPTS PYTHONPATH
  exec "$@"
)
# gui N: start the window from Terminal under iso; its output goes to wp6.5-mac/gui-N.out and .err
gui() {
  iso "$APP/Contents/MacOS/Clearwater" > "$W/gui-$1.out" 2> "$W/gui-$1.err"; echo "exit $?" | tee -a "$W/gui-$1.out"
}
# after LABEL: what to look at once a window has closed
after() {
  echo "== $1 =="; date
  ps -Ao pid,ppid,comm | grep -i -E 'Clearwater|ffmpeg' | grep -v grep || echo "no Clearwater or ffmpeg process"
  echo "-- gui-out"; ls -1 "$W/gui-out"
  echo "-- log tail"; tail -n 12 "$W/home/Library/Application Support/Clearwater/logs/clearwater.log"
}
EOF
```

EXPECT: no output.
LANDS: `/Users/Shared/clearwater-wp65/env.sh`. (The shell lines mirror the source runner's: uv's
variables as in `.github/workflows/macos-build.yml:26-28`, the Python pin as `:57`. `iso` applies
the entry-point rule's redirection: `tests/test_macos_portability.py:66-82`.)

The seat fills `SEAT_FILLS_VERSION` and `SEAT_FILLS_COMMIT` in this block before hand-over.

### Step 5 -- write the notes file

```
cat > /Users/Shared/clearwater-wp65/wp6.5-mac/notes.txt <<'EOF'
WP6.5 stage 2 notes (the owner writes under each heading; plain words, what you saw)
Date and time started:
STOP, if any (step number and what you saw):
Step 16 Finder first launch (every dialog text word for word; the path you took; window? Dock icon? menus?):
Step 47 Terminal launch (window? exit status printed? anything on the terminal?):
Step 48 native dialogs P33 (File > Open), P34 (Batch > Add files), P35 (Presets Save/Export/Import), P36 (Settings output folder), P27 (upper-case names listed?):
Step 49 trackpad wheel P71 (natural scrolling on or off; zoom label after each gesture; direction; momentum):
Step 50 Dock Quit during an export (what you saw; how long the window took to close):
Step 52 Cmd-Q during an export (same):
Step 54 logout during an export (what macOS said; anything blocking the logout; what you found after logging in):
Anything else odd:
Date and time finished:
EOF
```

EXPECT: no output.
LANDS: `wp6.5-mac/notes.txt`. Edit it in TextEdit with `open -e "$W/notes.txt"` (after step 6).

### Step 6 -- load the definitions

```
. /Users/Shared/clearwater-wp65/env.sh && echo "VERSION=$VERSION COMMIT=$COMMIT"
```

EXPECT: `VERSION=<a version> COMMIT=<40 hex digits>`.
LANDS: the terminal.
IF NOT: a literal `SEAT_FILLS_` in the line = STOP (unfilled sheet). In any NEW Terminal window
(or after a logout) run this step again first; the checkout steps also need `cd "$SRC"`.

### Step 7 -- record the Mac's facts

```
{ sw_vers; uname -m; system_profiler SPHardwareDataType | grep -E "Model Name|Model Identifier|Chip|Total Number of Cores|Memory"; df -h /Users/Shared; date; } > "$W/machine.txt" 2>&1; cat "$W/machine.txt"
```

EXPECT (the figures of record, brief CHARC note): macOS 26.3.1 build 25D2128, `arm64`, `Mac16,10`,
Apple M4, 32 GB, the free space as step 1.
LANDS: `wp6.5-mac/machine.txt`. (The grep keeps the serial number and hardware UUID out.)

## 3. The inputs and the bundle (steps 8 to 18)

### Step 8 -- copy the inputs (hand action)

In Finder, copy the CONTENTS of the Google Drive folder `wp6.5-mac-in` (the zip, its `.sha256`,
the two clips, `win-ref`, `SHA256SUMS.txt`) into `/Users/Shared/clearwater-wp65/in`. (Finder >
Go > Go to Folder... accepts that path.) Wait until the Drive client shows nothing left to
download.
EXPECT: the files are in `in/`; about 0.9 GiB.
LANDS: `in/`.

### Step 9 -- list the inputs

```
ls -1sh "$IN" && du -sh "$IN"
```

EXPECT: the zip, the `.zip.sha256`, `GX011627-trim.mp4`, `GX011589.mp4`, `SHA256SUMS.txt`,
`win-ref` (a folder); about 0.9 Gi.
LANDS: the terminal.

### Step 10 -- verify the copy

```
(cd "$IN" && shasum -a 256 -c SHA256SUMS.txt) 2>&1 | tail -n 40
```

EXPECT: every line ends `OK`; no `FAILED`.
LANDS: the terminal.
IF NOT: STOP. A damaged copy is not evidence; copy again from Drive once, repeat this step; a
second failure is a STOP.

### Step 11 -- check the zip against its sidecar

```
(cd "$IN" && head -n 1 "Clearwater-$VERSION-macos.zip.sha256" | shasum -a 256 -c -) && tail -n 1 "$IN/Clearwater-$VERSION-macos.zip.sha256"
```

EXPECT: `Clearwater-<version>-macos.zip: OK`, then a line `# source-commit: <hash>` equal to the
`COMMIT` printed in step 6. (The sidecar is `<digest>  <name>`, then the source-commit line:
`tools/package/build.py:5404`, `.github/workflows/macos-build.yml:300-312`.)
LANDS: the terminal.
IF NOT: STOP.

### Step 12 -- unzip the build

```
ditto -x -k "$ZIP" "$PROG" && ls -1 "$PROG"
```

EXPECT: the listing shows, among others, `Clearwater.app` (the zip's ONE top-level item, with its internal links
kept: `tools/package/build.py:350-364`). `ditto` is used because it keeps the links.
LANDS: `/Users/Shared/clearwater-wp65/Clearwater.app`.

### Step 13 -- look inside the bundle

```
{ du -sh "$APP"; ls -1 "$APP/Contents" "$APP/Contents/MacOS"; ls -l "$APP/Contents/Resources/THIRD_PARTY_NOTICES.md" | awk '{print $5, $9}'; } 2>&1 | tee "$W/bundle-listing.txt"
```

EXPECT: about 1 Gi; `Contents` holds `Frameworks`, `Info.plist`, `MacOS`, `Resources`;
`MacOS` holds `Clearwater`, `ffmpeg`, `ffprobe`; the notices file is present with a non-zero size
(notices at `Contents/Resources/THIRD_PARTY_NOTICES.md`, FFmpeg beside the executable:
`.github/workflows/macos-build.yml:289,297`).
LANDS: `wp6.5-mac/bundle-listing.txt`.

### Step 14 -- is the bundle quarantined?

```
{ echo "app:"; xattr "$APP"; echo "ffmpeg:"; xattr "$APP/Contents/MacOS/ffmpeg"; echo "(end)"; } 2>&1 | tee "$W/quarantine.txt"
```

EXPECT: either empty lists (files that reached the Mac through the Drive client are often not
marked) or `com.apple.quarantine`. Either is a result; copy it into `notes.txt` under step 16.
LANDS: `wp6.5-mac/quarantine.txt`. Do not remove an attribute.

### Step 15 -- is there already a real Clearwater profile? (before the Finder launch)

```
for d in "Application Support" "Caches"; do [ -d "$HOME/Library/$d/Clearwater" ] && echo "$d/Clearwater: present" || echo "$d/Clearwater: absent"; done | tee "$W/real-profile-before.txt"
```

EXPECT: two lines. Only the words `present` or `absent` are printed (no listing).
LANDS: `wp6.5-mac/real-profile-before.txt`.

### Step 16 -- first launch from Finder, the Gatekeeper path (hand action)

NOTE: a Finder launch cannot be redirected: it will create `~/Library/Application Support/Clearwater`
(log, settings) and `~/Library/Caches/Clearwater` in the account if they were `absent` in step 15.
This is the one place the sheet touches the real profile, on purpose, because the Finder launch IS
the check. If you would rather not, write `skipped: shared account` in `notes.txt` and go to step 18.
Nothing here is edited or deleted by the sheet; what you do with those folders afterwards is yours.

1. In Finder open `/Users/Shared/clearwater-wp65` and double-click `Clearwater.app`.
2. If macOS blocks it (the build is unsigned, F0-4 of the ledger): write the dialog's text and
   button names word for word in `notes.txt`. macOS 15 and later have NO Control-click (right-click)
   Open override; the path is: Apple menu > System Settings > Privacy & Security > scroll down to
   the Security section > the entry saying Clearwater was blocked > **Open Anyway** > enter the
   account's password or Touch ID > **Open** in the next dialog (Apple developer news 2024-08-06;
   Apple support 102445; ledger F0-4). Write down every step you actually had to take.
3. If it opens at once (nothing quarantined, step 14), write that.
4. When the window is up, write down: does a window appear; is there a Dock icon; the menu-bar
   titles (expected, M-GUI P31: File, View and Tools, with Tools holding only Settings... and no
   GPU pack entries, AD-33); is there a Clearwater > Quit item.
5. Quit with Cmd-Q.

EXPECT: the window appears after at most one Gatekeeper round; no message saying the app is
"damaged" (a damaged-seal message would be the brief's flagged risk: write it down and STOP).
LANDS: `notes.txt`, heading "Step 16".
IF NOT: a window that never appears, or "damaged": STOP.

### Step 17 -- the real profile after the Finder launch

```
for d in "Application Support" "Caches"; do [ -d "$HOME/Library/$d/Clearwater" ] && echo "$d/Clearwater: present" || echo "$d/Clearwater: absent"; done | tee "$W/real-profile-after.txt"
```

EXPECT: `present` for both after a Finder launch (`absent` before and `present` after means the
launch created them; paths: `src/clearwater/config/paths.py:136-140`).
LANDS: `wp6.5-mac/real-profile-after.txt`.

### Step 18 -- the bundle's own FFmpeg, from Terminal

```
{ "$APP/Contents/MacOS/ffmpeg" -hide_banner -version | head -n 2; "$APP/Contents/MacOS/ffmpeg" -hide_banner -encoders | grep -E "videotoolbox|libx265"; "$APP/Contents/MacOS/ffprobe" -hide_banner -version | head -n 1; } 2>&1 | tee "$W/bundle-ffmpeg.txt"
```

EXPECT: `ffmpeg version 9.0...`; encoder lines naming `hevc_videotoolbox` and `libx265`; an
`ffprobe version` line. (The runner captured the same: `.github/workflows/macos-build.yml:289-292`;
the M-BUNDLE rows P16 / P57: `tests/test_macos_portability.py:1933-1947`.)
LANDS: `wp6.5-mac/bundle-ffmpeg.txt`.
IF NOT: if Terminal reports that `ffmpeg` cannot be opened or verified, STOP and write the exact
message; do not strip any attribute.

## 4. The source tools, for the scripted legs (steps 19 to 27)

Every instrument below is a Python tool or test in the source tree; none runs from inside the
`.app` (its only non-window entries are the refusal rows and `--export-worker`,
`src/clearwater/__main__.py:445-520`). The checkout needs `uv` 0.10.9 and Python 3.12.13, both
kept under `.uv/`.

### Step 19 -- the disk gate for the source legs (GATE)

```
df -h ~
```

EXPECT: Avail at least **8 Gi** (the source legs add about 3.1 GiB, section 0.4, and the 5 GiB
margin must still hold after the bundle legs).
LANDS: the terminal.
IF NOT: SKIP steps 20 to 45 (they need the checkout and its venv): write `source legs skipped: disk`
in `notes.txt`; stage 1's runner job is their proof; go to step 46.

### Step 20 -- install uv 0.10.9

```
curl -LsSf https://astral.sh/uv/0.10.9/install.sh | env UV_UNMANAGED_INSTALL="$PROG/.uv/bin" sh
```

EXPECT: the installer prints that it installed `uv` into `/Users/Shared/clearwater-wp65/.uv/bin`.
`UV_UNMANAGED_INSTALL` puts it there and leaves the account's shell profile and PATH alone.
LANDS: `.uv/bin/uv`. (The pinned version is the workflow's, `.github/workflows/macos-build.yml:56`;
the installer command and variable are uv's documented ones, https://docs.astral.sh/uv/getting-started/installation/,
the page `docs/user-guide.md:83` links; the seat confirms it against the README "macOS
prerequisites" section before hand-over. No Homebrew anywhere.)
IF NOT: STOP.

### Step 21 -- confirm the version

```
uv --version
```

EXPECT: `uv 0.10.9 (...)`. Any other version = STOP.
LANDS: the terminal.

### Step 22 -- install the pinned Python

```
uv python install 3.12.13
```

EXPECT: `Installed Python 3.12.13` under `.uv/python`.
LANDS: `.uv/python`. (The runner pins 3.12.13: `.github/workflows/macos-build.yml:57`.)

### Step 23 -- clone the source

```
git clone https://github.com/rwsmythe/clearwater.git "$SRC"
```

EXPECT: `Cloning into '/Users/Shared/clearwater-wp65/src'...`, a few tens of MB. (Xcode Command Line
Tools provide `git`; repository URL: `docs/project-log.md` 1.1.1 release entry.)
LANDS: `src/`.

### Step 24 -- check out the run-10 commit

```
git -C "$SRC" checkout --detach "$COMMIT" && git -C "$SRC" rev-parse HEAD
```

EXPECT: the printed hash equals `COMMIT` (step 6) and the zip's source-commit (step 11).
LANDS: the terminal.
IF NOT: STOP (the tools would not match the build).

### Step 25 -- the tools' local configuration

```
printf 'footage_path = "%s"\nworking_path = "%s"\n' "$IN" "$W/work" > "$SRC/clearwater.local.toml" && cat "$SRC/clearwater.local.toml"
```

EXPECT: the two lines naming `/Users/Shared/clearwater-wp65/in` and
`/Users/Shared/clearwater-wp65/wp6.5-mac/work`. The tools treat `in/` as their read-only footage
folder and write only under `wp6.5-mac/work` (`tools/local_config.py:87-120`; template
`clearwater.local.example.toml`). The file is git-ignored.
LANDS: `src/clearwater.local.toml`.

### Step 26 -- sync the CPU-only environment

```
cd "$SRC" && /usr/bin/time -p uv sync --frozen --no-default-groups --group dev 2>&1 | tail -n 8
```

EXPECT: `Installed <n> packages` and a `real` time. No CuPy: the Mac is CPU only (AD-33, AD-35; the
workflow's identical sync: `.github/workflows/macos-build.yml:61-65`). From here every command runs
from `$SRC`.
LANDS: `src/.venv`.
IF NOT: STOP.

### Step 27 -- record the Python and the package

```
iso uv run python -c "import sys, clearwater; print(clearwater.__version__, sys.version.split()[0], sys.platform); print(open(sys.base_prefix + '/BUILD').read().strip() if __import__('os').path.isfile(sys.base_prefix + '/BUILD') else 'no BUILD file')" | tee "$W/python.txt"
```

EXPECT: `<version> 3.12.13 darwin` and the python-build-standalone BUILD stamp (the runner's was
`20260303`, ledger run-8 fold). A different BUILD stamp is a FINDING, write it in `notes.txt`.
Importing the `clearwater` package is not a product entry point and starts no window.
LANDS: `wp6.5-mac/python.txt`.

## 5. The bundle on the Mac, scripted (steps 28 to 32)

### Step 28 -- the headless smoke of THIS bundle

```
iso /usr/bin/time -p uv run python tools/package/build.py --smoke "$APP/Contents/MacOS" --out "$W/smoke-out" > "$W/smoke.log" 2>&1; echo "exit $?"; tail -n 14 "$W/smoke.log"
```

EXPECT: `exit 0`; the log ends with `smoke: PASS (headless process checks in contained process groups)`
(`tools/package/smoke.py:1210`). The rows: the ten refusal rows and two worker rows (`-c pass`,
`-m http.server`, the multiprocessing flags, `--export-worker` with no or bad input), the planted
exception on a COPY of the bundle, the FFmpeg rows. Each row runs with a fresh disposable HOME and a
system-only PATH (`tools/package/smoke.py:57-95,122-160,1121-1210`); `--smoke FOLDER` is
`tools/package/build.py:5665-5671,5729`. No window is started.
LANDS: `wp6.5-mac/smoke.log`, `wp6.5-mac/smoke-out/`.
IF NOT: STOP; the log is the evidence.

### Step 29 -- delete the smoke's bundle copy

```
rm -rf "$W"/smoke-out/smoke/run-*/planted && du -sh "$W/smoke-out"
```

EXPECT: well under 100 Mi left (the planted copy was about 1 Gi; it is only a copy of the bundle).
LANDS: `wp6.5-mac/smoke-out/`.

### Step 30 -- the macOS test leg on the built bundle (the VideoToolbox halves)

DR-163 (VideoToolbox last-sample duration on VFR sources): [SEAT FILLS AFTER RUN 10: closed by run 10 / open -- avoid VT on VFR sources]

```
iso /usr/bin/time -p env CLEARWATER_MAC_BUNDLE="$APP" uv run pytest -q -rs --timeout 1200 -m macos -k "not test_python_m_clearwater_starts_the_shell_and_exits_0" --basetemp="$W/pytest-macos" --junitxml="$W/macos-junit.xml" > "$W/macos.log" 2>&1; echo "exit $?"; tail -n 6 "$W/macos.log"
```

HANDS OFF: this leg opens and closes small Cocoa windows (M-GUI, M-BUNDLE rows); do not click or
type in them. It is also long; the runner's wall for the same leg is in run 10's `macos.log`
[SEAT FILLS: the runner's wall].
EXPECT: `exit 0`, a last line `N passed, M skipped ... in <s>s` with no `failed` or `error`. The
VideoToolbox rows (M-CODEC, M-RATE, M-V4 VT halves, M-SPACE) RUN here (the runner may not have had
hardware encode), so VideoToolbox skips should be absent; every `SKIPPED` line in `macos.log` carries its reason. If
the DR-163 line above says open, the four DR-163 VT/VFR cases are strict xfails and show as
`xfailed`; an `XPASS` is a failure to report (`tests/test_macos_portability.py:849`, ledger run-8
fold). This is the command the workflow runs (`.github/workflows/macos-build.yml:229-243`, with
FFmpeg bundled), with the bundle's folder first on PATH from step 4.
LANDS: `wp6.5-mac/macos.log`, `wp6.5-mac/macos-junit.xml`, `wp6.5-mac/pytest-macos/` (cleaned in step 32).
IF NOT: a failure is a finding, not a STOP for the rest of the sheet: copy the summary and the
`FAILED` lines into `notes.txt` and go on to step 31.

### Step 31 -- the skips, listed

```
grep -E "^(SKIPPED|XFAIL|XPASS)" "$W/macos.log" | sort | uniq -c | tee "$W/macos-skips.txt"
```

EXPECT: each line is a count and a reason; none says FFmpeg is absent (that would mean the bundle's
tools were not first on PATH).
LANDS: `wp6.5-mac/macos-skips.txt`.

### Step 32 -- keep the Q1 figures from the test leg, clear the leg's scratch

```
mkdir -p "$W/m-rate" && find "$W/pytest-macos" -name figures.json | while read f; do cp "$f" "$W/m-rate/$(basename "$(dirname "$f")").json"; done; ls -1 "$W/m-rate"; rm -rf "$W/pytest-macos"; echo "disk images still attached under wp6.5-mac:"; hdiutil info | grep -c "$W"
```

EXPECT: `m-rate` lists the `test_macos_videotoolbox_quality_controls*` figure files (M-RATE:
both Q1 candidates on a busy and a calm synthetic clip at the draft level, every advertised depth,
`tests/test_macos_portability.py:786-812`); the last line is `0`.
LANDS: `wp6.5-mac/m-rate/*.json`.
IF NOT: a count above 0 means a test disk image is still mounted: `hdiutil detach` each device
`hdiutil info` lists under `wp6.5-mac` and write it down.

## 6. The measurements (steps 33 to 45): EXCLUSIVE

EXCLUSIVE: nothing else heavy on the Mac from step 33 to step 45 (section 0.2). The Mac has no
GPU path (AD-33): every figure below is CPU correction; the encoder is VideoToolbox hardware unless
a step says otherwise. Bounds in a step ("longer than N minutes") are this sheet's safety valve,
not a requirement: press Ctrl-C (the job stops and removes its partial output, D44), write the
elapsed time in `notes.txt`, and go on.

DR-163 (VideoToolbox last-sample duration on VFR sources): [SEAT FILLS AFTER RUN 10: closed by run 10 / open -- avoid VT on VFR sources]

### Step 33 -- note the load before

```
ps -Ao pcpu,pmem,comm -r | head -n 8 | tee "$W/load-before.txt"
```

EXPECT: nothing above a few percent CPU. If a browser, Drive or Spotlight shows up, quit it and
repeat the step.
LANDS: `wp6.5-mac/load-before.txt`.

### Step 34 -- Q1, candidate B (the sink's default): the trim at both quality levels and both depths

AD-35's rate candidates (`src/clearwater/io/video/encode.py:122-129`): B (the default) is
`-b:v R -maxrate R`; A is `-q:v` per level plus `-maxrate R`. This step is B on the GX011627
trim, High and Standard, 8-bit and 10-bit (`--ten-bit` is D76's 10-bit from an 8-bit source).
Each export is the full pipeline on the CPU; the first one also analyses and fills the cache
that the other three reuse (V17).

```
mkdir -p "$W/q1" && for q in high standard; do for d in 8 10; do tag="B-$q-$d"; mkdir -p "$W/q1/$tag"; if [ "$d" = 10 ]; then t="--ten-bit"; else t=""; fi; iso /usr/bin/time -l uv run python tools/headless_export.py "$IN/GX011627-trim.mp4" --out "$W/q1/$tag" --quality "$q" --encoder hevc_videotoolbox $t --cache-dir "$W/cache-q1" --record "$W/q1/$tag.json" > "$W/q1/$tag.log" 2>&1; echo "exit $?" >> "$W/q1/$tag.log"; done; done; tail -n 4 "$W"/q1/B-*.log
```

EXPECT: four logs each ending `exit 0`; the `time -l` block gives the wall (`real`) and
`maximum resident set size` (bytes); each folder holds `GX011627-trim_corrected.mp4` (the
default `_corrected` suffix, `docs/user-guide.md:162`). The record JSON's `"video"` object names
`"encoder": "hevc_videotoolbox"` (the command line is `tools/headless_export.py:12-21,1190-1262`;
every VideoToolbox command carries `-allow_sw 0`, so a missing hardware encoder is an error, never
a silent software encode: `src/clearwater/io/video/encode.py:32-33`). It runs on the CPU with no
window and no cache folder other than `cache-q1`.
Longer than 90 minutes in total: Ctrl-C as above.
LANDS: `wp6.5-mac/q1/B-<quality>-<depth>/`, `wp6.5-mac/q1/B-<quality>-<depth>.log` and `.json`,
`wp6.5-mac/cache-q1/`.
IF NOT: an `exit 1` or `exit 2` log is a finding (copy its last lines into `notes.txt`); an error
naming the encoder or its trial is the VideoToolbox result itself.

### Step 35 -- Q1, the sizes and the stream facts

```
for f in "$W"/q1/B-*/GX011627-trim_corrected.mp4; do echo "== $f"; ls -l "$f" | awk '{print $5, "bytes"}'; ffprobe -v error -select_streams v:0 -show_entries stream=codec_name,profile,level,pix_fmt,bit_rate,nb_frames -show_entries format=size,bit_rate -of default=nw=1 "$f"; done > "$W/q1/streams.txt"; cat "$W/q1/streams.txt"
```

EXPECT: for each of the four outputs: `hevc`; profile `Main` for 8-bit and `Main 10` for 10-bit
(`tests/test_macos_portability.py:781-812`); `pix_fmt` `yuv420p` / `yuv420p10le`; `nb_frames=90` or
the trim's frame count (L2); bit rates below the ceiling R (High about 0.24 bits per pixel, Standard
half: `src/clearwater/io/video/encode.py:291`). The seat tabulates sizes and rates against NVENC's.
LANDS: `wp6.5-mac/q1/streams.txt`.

### Step 36 -- V4 on each Q1 output

```
for tag in B-high-8 B-high-10 B-standard-8 B-standard-10; do iso uv run python tools/video_fidelity.py compare "$IN/GX011627-trim.mp4" "$W/q1/$tag/GX011627-trim_corrected.mp4" --bit-depth "${tag##*-}" --out "$W/work/wp3.10/q1-$tag" > "$W/q1/$tag.v4.txt" 2>&1; echo "exit $?" >> "$W/q1/$tag.v4.txt"; done; tail -n 3 "$W"/q1/*.v4.txt
```

EXPECT: per output a one-line verdict `items N; DIFFERENT by class {...}; MANDATORY+REQUIRED all SAME:
True; notes K`, then `exit 0` (`tools/video_fidelity.py:1388-1390,1393-1416`). `compare` is the V4
instrument's source-against-output leg; its NVENC proof belongs to the `encode` leg only and is not
used (`tools/video_fidelity.py:1-70`, "Windows / NVIDIA evidence; not a Mac instrument": only the
`encode` leg is). `False` is a V4 finding: keep the record, do not retry.
LANDS: `wp6.5-mac/q1/<tag>.v4.txt`; the records `wp6.5-mac/work/wp3.10/q1-<tag>/*.compare.json` and `.md`.

### Step 37 -- Q1, candidate A: NOT RUNNABLE FROM THE SHIPPED TOOLS (gap for CHARC)

[CHARC FILLS: no existing command selects candidate A. `VT_RATE_CONTROL` is a module constant
(`src/clearwater/io/video/encode.py:122`, default `"B"`); only the tests flip it, by monkeypatch
(`tests/test_macos_portability.py:801,1350`); `tools/headless_export.py` has no option for it
(`:1190-1262`); `tools/video_fidelity.py encode` refuses `hevc_videotoolbox` (`:1409`, choices
`hevc_nvenc` / `libx265`); the `VT_Q_LEVEL` figures 65 / 55 / 45 are placeholders
(`encode.py:129`). Candidate A on the GX011627 trim at both quality levels and both depths, with
V4 on each output, needs either a tool option or a wrapper that CHARC grants. Until it is filled
this step stays EMPTY and nothing is run in its place. The test leg of step 30 already gave A and
B on the synthetic busy and calm clips (M-RATE `m-rate/`, M-SPACE).]

LANDS: nothing yet.

### Step 38 -- the N6 figure, the 90-frame trim, end to end

N6 is information on the Mac, not a target (spec N6; `tools/n6.py:8-12`: about 12 min of
processing per min of 4K at the Windows target). `export_bench.py` runs the product export job
end to end (probe, the whole analysis on a COLD cache, the render, encode, mux, verification) and
reports minutes of processing per minute of footage (`tools/export_bench.py:1-40,795-870`). Its
graphics-card readings will say `nvidia-smi did not run`: expected on a Mac
(`tools/video_io_bench.py:163-185`).

```
mkdir -p "$W/n6" && iso /usr/bin/time -l uv run python tools/export_bench.py run GX011627-trim --runs 1 --cache cold --force-cpu --encoder auto --quality standard > "$W/n6/trim.log" 2>&1; echo "exit $?" >> "$W/n6/trim.log"; tail -n 22 "$W/n6/trim.log"
```

EXPECT: `exit 0`; a `RUN ...` line, a result row with `min/min`, a `RECORD <path>` line; the `time -l`
block. `--encoder auto` is VideoToolbox here (G12); `--force-cpu` states the CPU backend; the
output and cache are deleted by the tool after the run (no `--keep`), so no clip stays.
Longer than 60 minutes: Ctrl-C as in section 6.
LANDS: `wp6.5-mac/n6/trim.log`; the record `wp6.5-mac/work/wp3.14/bench/export-bench-GX011627-trim-<stamp>.json`.
IF NOT: `ERROR ...` on the first line is the tool's refusal (a finding, with the line copied into
`notes.txt`); if it names `cpu_freq` or psutil, that is a finding about the tool on Apple Silicon.

### Step 39 -- the N6 figure, ONE full clip, end to end

```
iso /usr/bin/time -l uv run python tools/export_bench.py run GX011589 --runs 1 --cache cold --force-cpu --encoder auto --quality standard > "$W/n6/full.log" 2>&1; echo "exit $?" >> "$W/n6/full.log"; tail -n 22 "$W/n6/full.log"
```

EXPECT: as step 38, on the whole 6.4 s clip (about 192 frames). A short clip's per-minute figure is
dominated by start-up: the seat says so in the report.
Longer than 60 minutes: Ctrl-C as in section 6.
LANDS: `wp6.5-mac/n6/full.log`; `wp6.5-mac/work/wp3.14/bench/export-bench-GX011589-<stamp>.json`.

### Step 40 -- the load after the N6 runs

```
ps -Ao pcpu,pmem,comm -r | head -n 8 | tee "$W/load-after-n6.txt"
```

EXPECT: nothing heavy left running. LANDS: `wp6.5-mac/load-after-n6.txt`.

### Step 41 -- delete the full-clip output (the CHARC note)

```
find "$W/work/wp3.14/bench" -name "*.mp4" -exec ls -1sh {} \; ; echo "--- deleting"; find "$W/work/wp3.14/bench" -name "*.mp4" -delete; find "$W/work/wp3.14/bench" -name "*.mp4" | wc -l
```

EXPECT: the first listing is empty (the tool already deleted its output) or names clips; after the
delete the last line is `0`. The N6 records stay.
LANDS: `wp6.5-mac/work/wp3.14/bench/` (records only).

### Step 42 -- M-DEVICE / AD-11: the Mac CPU export of the reference input

The comparison instrument is `tools/export_oracle.py` (AD-11's tier bounds: max 2e-3 and mean 2e-4
absolute per channel on a differing frame; `tools/export_oracle.py:1-38,88-91`). `record` runs one
export through the product engine on the CPU and keeps the pre-encode frame digests and, for one
frame per second, the full float32 frame; `compare` sets it against the Windows reference from L4.

```
iso /usr/bin/time -l uv run python tools/export_oracle.py record --clip GX011627-trim --force-cpu --name mac-cpu > "$W/ad11-record.log" 2>&1; echo "exit $?" >> "$W/ad11-record.log"; tail -n 14 "$W/ad11-record.log"
```

EXPECT: `exit 0`; `ORACLE GX011627-trim.mp4 c3 <device>: <the trim's frame count> frames, about 3 kept, ...`; `RECORD <path>`
(`tools/export_oracle.py:689-750`). The record folder holds three float32 4K frames (about 100 MB
each, 0.3 GiB: that is the folder's size, section 0.4).
Longer than 60 minutes: Ctrl-C as in section 6.
LANDS: `wp6.5-mac/ad11-record.log`; `wp6.5-mac/work/wp3.21/oracle/mac-cpu/` (`oracle.json`, `frames/`).

### Step 43 -- AD-11: the verdict

```
iso uv run python tools/export_oracle.py compare "$IN/win-ref" "$W/work/wp3.21/oracle/mac-cpu" > "$W/ad11-compare.txt" 2>&1; echo "exit $?" >> "$W/ad11-compare.txt"; cat "$W/ad11-compare.txt"
```

EXPECT: `VERDICT TIER1` or `VERDICT TIER2` with the frame counts and `max abs` / `mean abs`, then
`exit 0`. TIER2 means some frames differ by no more than AD-11's bound. `VERDICT FAIL` with a
`REASON` line, or `exit 1`, means the Mac CPU output is outside AD-11's bound or another tier-1
check (statistics records, proxies) differs: this is a STOP for the seat, never a tolerance change.
Do not rerun with other settings; keep the files.
LANDS: `wp6.5-mac/ad11-compare.txt`.

### Step 44 -- AD-11: the per-channel table

The command line prints only the largest figures. This step calls the same `compare` function
(`tools/export_oracle.py:531`) and prints its whole result, which holds the per-channel maximum and
mean of each measured frame.

```
iso uv run python -c "import json, sys; sys.path.insert(0, 'tools'); import export_oracle as e; from pathlib import Path; print(json.dumps(e.compare(Path(sys.argv[1]), Path(sys.argv[2])), indent=1))" "$IN/win-ref" "$W/work/wp3.21/oracle/mac-cpu" > "$W/ad11-compare.json" 2>&1; head -n 40 "$W/ad11-compare.json"
```

EXPECT: a JSON object with `verdict`, `frames`, `frames_differing`, `frames_measured`, `max_abs`,
`mean_abs`, and `measured`: one entry per measured frame with `pts` and `max_abs` / `mean_abs` as
three numbers (one per colour channel). The same verdict as step 43.
LANDS: `wp6.5-mac/ad11-compare.json`.

### Step 45 -- the load after the measurements

```
ps -Ao pcpu,pmem,comm -r | head -n 8 | tee "$W/load-after.txt"
```

EXPECT: nothing heavy. The exclusive window ends here. LANDS: `wp6.5-mac/load-after.txt`.

## 7. The hand checks that need the window (steps 46 to 55)

These steps start the program's window. They run from Terminal under `iso` (the disposable
profile; the program's log is then `wp6.5-mac/home/Library/Application Support/Clearwater/logs/clearwater.log`,
`src/clearwater/config/paths.py:86-88,136-140`). Nothing sends input for you: your hands are the
only input.

### Step 46 -- the files the dialogs will pick

```
mkdir -p "$W/dialog-files/space dir" "$W/gui-out" && n="$(printf 'caf\303\251')" && cp "$IN/GX011627-trim.mp4" "$W/dialog-files/space dir/$n clip.MP4" && cp "$IN/GX011627-trim.mp4" "$W/dialog-files/space dir/plain.mp4" && cp "$IN/GX011627-trim.mp4" "$W/dialog-files/space dir/Upper.MOV" && ls -1 "$W/dialog-files/space dir"
```

EXPECT: three names: one with an accented letter and an upper-case `.MP4`, `plain.mp4`, `Upper.MOV`
(`.MOV` is in scope: spec v0.5.7), in a folder whose name has a space.
LANDS: `wp6.5-mac/dialog-files/`, `wp6.5-mac/gui-out/`. (About 60 MB.)

### Step 47 -- launch from Terminal, one complete export (hand action; P33, P36)

First run this command (Terminal stays busy until you quit the program; `gui` is defined in step 4):

```
gui 1
```

Then, in the window:

1. **File > Open**, choose `GX011627-trim.mp4` in `/Users/Shared/clearwater-wp65/in`. Wait for the
   analysis to finish (minutes on the CPU; the timeline says when).
2. **Tools > Settings**: press the Output folder button, choose `/Users/Shared/clearwater-wp65/wp6.5-mac/gui-out`
   in the native folder dialog (P36), OK. Do NOT pick "Use source folder". Leave the encoder on
   Automatic and the quality on Standard. Write down the encoder choices the dialog lists and the text
   of the Automatic entry (M-GUI P37 expects "Automatic (the hardware encoder when available)", rows
   VideoToolbox and libx265).
3. **File > Export**. Wait until the export panel says done.
4. **Cmd-Q**.

EXPECT: the window appears with no Gatekeeper dialog now; the export finishes and
`wp6.5-mac/gui-out/GX011627-trim_corrected.mp4` exists; after Cmd-Q the Terminal prompt returns with
`exit 0`.
LANDS: `wp6.5-mac/gui-1.out`, `gui-1.err`, `gui-out/`; `notes.txt` heading "Step 47".
IF NOT: a window that never appears, an error banner, or a non-zero exit is a finding: write it
down; go on.

### Step 48 -- the native dialogs (hand action; P33, P34, P35, P36, P27)

Launch again with `gui 2`.
For each dialog write down: native macOS look or not, the filter, what Cancel does, what you saw.

1. **P33, File > Open**: press Cancel (nothing opens, no error). Then open
   `/Users/Shared/clearwater-wp65/wp6.5-mac/dialog-files/space dir/` : are all three files (accented
   name, `plain.mp4`, `Upper.MOV`) selectable, i.e. not greyed out (P27: upper-case suffixes)? Open
   the accented one: does the title show its name intact?
2. **P34, the Batch panel > Add files...**: select all three files at once. The list shows three
   names, accents intact.
3. **P35, the Presets panel**: **Save as...** a preset named `wp65 test`. **Export...** it into
   `.../dialog-files/` as `wp65-preset` WITHOUT typing an extension: does the file get `.json`?
   Export again to the same name: does the program's own overwrite confirmation appear? Choose No.
   **Import...** the exported file.
4. **P36, Tools > Settings > Output folder**: open the folder dialog, Cancel (the field is
   unchanged); open it again, choose `gui-out`, OK, Save; reopen Settings: the folder is kept.
5. **Cmd-Q**.

EXPECT: as the audit lines say (`docs/reports/wp6.2-portability-audit.md:402,408-411`): native
dialogs, JSON extension kept, the custom overwrite confirmation, Cancel changes nothing, the chosen
folder saved.
LANDS: `notes.txt` heading "Step 48"; `wp6.5-mac/gui-2.out`, `gui-2.err`; the preset under
`wp6.5-mac/home/Library/Application Support/Clearwater/presets/`.

### Step 49 -- the trackpad wheel phases (hand action; M-GUI P71)

Launch again with `gui 3`, open `GX011627-trim.mp4`, wait for the
preview to show a frame. Note the System Settings > Trackpad > Scroll & Zoom "Natural scrolling"
switch (on or off). Over the preview, with the trackpad, and write down the zoom text in the
status bar after each:

1. one slow two-finger scroll of about one finger-length, up;
2. the same, down;
3. one fast flick up, then lift and watch whether the zoom keeps changing (momentum);
4. a flick up, then reverse the direction before it stops;
5. **View > Fit** to reset between tries.

EXPECT: the program adds the wheel movement up and takes one zoom step per 120 units (one mouse
notch), a direction change starts the count again, so a slow scroll steps gradually and one flick
does not run away to the largest zoom (`src/clearwater/gui/preview.py:89-90,399-418`; audit P71).
Write down which finger direction zooms in for your Natural scrolling setting, how many steps each
gesture made, and whether momentum kept zooming after the fingers lifted.
Then Cmd-Q.
LANDS: `notes.txt` heading "Step 49"; `wp6.5-mac/gui-3.out`, `gui-3.err`.

### Step 50 -- Dock Quit during an export (hand action)

Launch with `gui 4`, open `GX011627-trim.mp4` (the analysis is cached
from step 47: Export is available at once; if not, wait for the analysis), **File > Export**, and
WHILE it says it is exporting (the progress bar moving) right-click the program's Dock icon and
choose **Quit**. Write down how long the window took to close.

EXPECT: the program stops its export, removes the unfinished output and closes within a few
seconds (the shell cancels and joins the job, then logs "Clearwater closed": `src/clearwater/gui/shell.py:686-725`;
no partial output, D44).
LANDS: `notes.txt` heading "Step 50"; `wp6.5-mac/gui-4.out`, `gui-4.err`.

### Step 51 -- what the Dock Quit left

```
after "dock-quit" 2>&1 | tee "$W/after-dock-quit.txt"
```

EXPECT: `no Clearwater or ffmpeg process`; `gui-out` holds only the one finished export of step 47
(plus no partial or temporary file); the log tail ends with a `Clearwater closed` line.
LANDS: `wp6.5-mac/after-dock-quit.txt`.
IF NOT: a left-over `ffmpeg` process, a partial file or no `Clearwater closed` line is a finding
(write it down; `kill` nothing by hand).

### Step 52 -- Cmd-Q during an export (hand action)

As step 50 (launch with `gui 5`), but press **Cmd-Q** while it is exporting. Write down the time
the window took to close.

EXPECT: the same as step 50.
LANDS: `notes.txt` heading "Step 52"; `wp6.5-mac/gui-5.out`, `gui-5.err`.

### Step 53 -- what Cmd-Q left

```
after "cmd-q" 2>&1 | tee "$W/after-cmd-q.txt"
```

EXPECT: as step 51.
LANDS: `wp6.5-mac/after-cmd-q.txt`.

### Step 54 -- logout during an export (hand action; run it LAST)

The Mac is shared. Do this only if logging out of this account is fine right now: it ends the
account's whole login session. Everything of yours that is open should be saved first.
Launch with `gui 6`, open `GX011627-trim.mp4`, **File > Export**, and
while it is exporting choose Apple menu > **Log Out**, and confirm. Write down (on a piece of paper
if needed: the session ends) anything macOS or the program said, and whether the logout was
blocked or delayed. Log back in.

EXPECT: the session ends; no hang that needs a power button.
LANDS: what you wrote, into `notes.txt` heading "Step 54" after logging back in (step 55 follows).
IF NOT: if the logout is blocked for more than a minute, choose Cancel, Cmd-Q the program, write
that down and go on.

### Step 55 -- what the logout left (after logging back in)

Open Terminal, then:

```
. /Users/Shared/clearwater-wp65/env.sh && after "logout" 2>&1 | tee "$W/after-logout.txt"
```

EXPECT: no `ffmpeg` or Clearwater process left running; `gui-out` holds the step-47 export and
possibly an unfinished temporary file from the killed export (a hard end of the session is outside
D44's cancel path: write down what is there); the log tail shows how far it got.
LANDS: `wp6.5-mac/after-logout.txt`.

## 8. Close (steps 56 to 59)

### Step 56 -- clean up what is not evidence

```
rm -rf "$W/cache-q1" "$W/tmp" "$W/home/Library/Caches" "$W/pytest-macos"; du -sh "$W"
```

EXPECT: the last line is the size of `wp6.5-mac/`: about 0.7 Gi, and it must be **under 2 Gi**.
(The sheet keeps the program's log, settings and presets under `wp6.5-mac/home`.) The Google
Drive copy must stay small.
LANDS: `wp6.5-mac/`.
IF NOT: above 2 Gi: STOP and list `du -sh "$W"/* | sort -h` to the seat; do not copy.

### Step 57 -- make sure no account or host name travels back

```
grep -rIl -e "$USER" -e "$(hostname -s)" "$W" | head -n 20
```

EXPECT: no output (the paths are all under `/Users/Shared`; `grep -I` skips the video files; only
file NAMES are printed, never their lines).
LANDS: the terminal.
IF NOT: for each file listed, replace the name in place with `sed -i '' "s/$USER/ACCOUNT/g; s/$(hostname -s)/HOST/g" <file>`
and run this step again until it prints nothing. (Never replace it in a `.mp4`.)

### Step 58 -- list the folder

```
(cd "$W" && find . -maxdepth 2 \( -type d -o -type f \) -exec du -sh {} + | sort -h | tail -n 60) | tee "$W/wp6.5-mac-listing.txt"; df -h ~
```

EXPECT: the folders `q1`, `m-rate`, `n6`, `gui-out`, `dialog-files`, `home`, `work`, `smoke-out`
and the text files named in the steps above; the largest entry is `work/wp3.21/oracle/mac-cpu`
(about 0.3 Gi). The last line shows the free space left.
LANDS: `wp6.5-mac/wp6.5-mac-listing.txt`.

### Step 59 -- copy the folder back (hand action)

Copy the folder `/Users/Shared/clearwater-wp65/wp6.5-mac` into your Google Drive. Nothing more.
Then resume Drive syncing if you paused it. The seat copies it from Drive to `work/wp6.5/mac/` on
the laptop and reads it.

EXPECT: the folder appears in Drive with all its files.
LANDS: your Drive.

Optional, on the owner's word and not part of the sheet: the program folder
`/Users/Shared/clearwater-wp65` can be deleted once the seat confirms it has what it needs. The
real-profile folders steps 15 and 17 reported on are the account's; the sheet never deletes them.

## 9. Index of what each step gives the report

| Report need | Steps | Files in `wp6.5-mac/` |
| --- | --- | --- |
| machine facts, build identity | 6, 7, 11, 13, 14, 27 | `machine.txt`, `bundle-listing.txt`, `quarantine.txt`, `python.txt` |
| Gatekeeper first launch (F0-4) | 14-17 | `quarantine.txt`, `real-profile-*.txt`, `notes.txt` |
| the bundle's smoke on 26.3.1 | 28, 29 | `smoke.log` |
| the M leg, VideoToolbox halves (DR-134 / DR-135) | 30-32 | `macos.log`, `macos-junit.xml`, `macos-skips.txt`, `m-rate/` |
| Q1 candidate B on the trim, V4 on each output | 34-36 | `q1/` |
| Q1 candidate A on the trim | 37 | GAP |
| N6 CPU figure (trim, one full clip) | 38-41 | `n6/`, `work/wp3.14/bench/` |
| M-DEVICE / AD-11 | 42-44 | `ad11-*`, `work/wp3.21/oracle/mac-cpu/` |
| hand checks: Finder, Terminal, Dock Quit, Cmd-Q, logout | 16, 47, 50-55 | `notes.txt`, `gui-*.out`, `gui-*.err`, `after-*.txt` |
| native dialogs P33-P36, P27 | 48 | `notes.txt` |
| trackpad wheel P71 | 49 | `notes.txt` |
