# WP5.5 release preparation - completion report

Candidate: branch `wp5.5`, base `e2cf4752`; build `e7876912`, Reviewer A
round-1 fixes `6135c496`, followed by this turn's round-2 documentation fixes.
This report transfers the package to the orchestrator. Reviewer A returned
**NO_NEW_CRITICAL_MAJOR** in round 2; Reviewer B and acceptance are pending.
The cumulative execution and adjudication record is
[the WP5.5 ledger](../proofs/wp5.5-ledger.md).

## What was built

- [THIRD_PARTY_NOTICES.md](../../THIRD_PARTY_NOTICES.md) records Python,
  FFmpeg, all 18 selected runtime/gpu distributions, their native components,
  and a separate 43-package dev/comms table. It preserves copyrights, licence
  terms, disclaimers, source pointers, LGPL replacement rights and the optional
  CUDA position. The final file is **433,096 UTF-8/LF bytes**. Its **44 distinct
  texts / 54 source records** represent **399,470 bytes** of distinct
  LF-normalised source text: 35 installed-source texts (including Python) and
  nine upstream supplements. All 44 SHA-256 values and byte counts match their
  source bytes; the ten duplicate records also match. LGPLv3 is reproduced
  once. NumPy, SciPy, Pillow and CuPy aggregate/component texts are complete.
  The full source/selection/hash/byte inventory is
  `work/wp5.5/notices-inventory.json` and `notices-inventory.md`; the committed
  notices also carry the per-text sources, hashes and counts. Turn-3's corrected
  UTF-8 inventory supersedes the corrupted round-0/turn-2 text copies.
- [The user guide](../user-guide.md) has eight sections: purpose/inputs,
  installation, first run/panels, video, photos, troubleshooting,
  limitations/release notes, and licence. It describes the actual Basic and
  Advanced controls, presets, File > Export, Export progress/Cancel, Batch
  buttons, naming, safe output folders, CPU/GPU choices and proxy cache.
  FFmpeg discovery is through PATH (R3). A lean install explicitly omits default
  groups; ordinary developer sync includes CUDA through dev. The 12 min/min
  target is end-to-end, not analysis-only; the 10.89 GPU median cites WP5.2.
  HDR refusal follows HLG/PQ transfer tags. DR-117 says the owner deferred a fix.
  Messages and labels were checked against source by Reviewer A; this is not a
  claim of a manual GUI walkthrough.
- [README.md](../../README.md) gained an eight-line, 412-byte application
  introduction pointing to the guide/notices. The previous 5,622-byte harness
  text remains byte-identical beneath it, independently checked by Reviewer A.
- Version **1.0.0** agrees in `src/clearwater/__init__.py`, `pyproject.toml`
  and installed editable distribution metadata. R4 permits the additional
  one-line root-package version change in `uv.lock`, with no dependency change.
  Existing composition wiring supplies this version to real export provenance.
- [The release checklist](../release-checklist.md) orders reviews, the disk
  floor, static/collection/parallel/serial/fullclip/harness gate, evidence
  archive, merge, the owner's explicit tag instruction, annotated tag and
  CHARC's release record. The archive is
  `clearwater-review-evidence\release-1.0.0\`, beside the clone and outside it.
  Tagging/pushing are not cell actions.
- **DR-119 (a)-(b) paid down:** `tools/export_bench.py` now labels D106/N6
  with 12.0 min/min and documents the `d106_min_per_min` / `meets_d106` keys.
  Tests pin 12.0, derive about 0.4004 s/source frame at 30000/1001 fps, and
  read the constant in the record assertion. `tools/halo_part3.py` writes
  `wholeset-list` UTF-8/LF bytes on every platform; a byte-backed CRLF-stream
  regression test catches the old `print` behavior. No other listing behavior
  changed. CHARC closes these parts at accept; (c)-(d) remain Phase 6.

## Licence audit and evidence

This is the already completed Windows AMD64 / Python 3.12 audit, not a new
audit. Locked versions and installed metadata are in
`work/wp5.5/round0/audit.json`; Reviewer A independently recomputed the
runtime/gpu closure and the dev/comms set in both rounds. Evidence paths below
are relative to the installed environment's `Lib/site-packages`, except Python
and FFmpeg. Every distribution also has its own dist-info `METADATA` evidence.
For aggregate packages, the table gives the main licence path and links to the
complete installed-source inventory in the notices. Verdict conditions and
required notices are retained per row.

| Component | Version | Licence | Installed evidence | Source / texts | Verdict and required notice |
| --- | --- | --- | --- | --- | --- |
| Python | 3.12.13 (outside lock) | PSF-2.0 and historical terms | `LICENSE.txt` beside the CPython 3.12.13 installation; text 01 | [Source](https://github.com/python/cpython/tree/v3.12.13); [text](../../THIRD_PARTY_NOTICES.md#text-01) | COMPATIBLE: preserve Python copyright and historical notices. |
| cuda-pathfinder | 1.8.3 | Apache-2.0 | `cuda_pathfinder-1.8.3.dist-info/licenses/LICENSE` | [Source](https://github.com/NVIDIA/cuda-python); [text](../../THIRD_PARTY_NOTICES.md#text-02) | **COMPATIBLE-WITH-CONDITION**: Retain NVIDIA copyright, Apache licence and notices in the notices; GPLv3-compatible branch under Clearwater's or-later grant. |
| cuda-toolkit | 12.9.2.0 | No licence declaration; metadata-only | `cuda_toolkit-12.9.2.0.dist-info/METADATA` and `RECORD`; no licence file/code/data | [Source](https://pypi.org/project/cuda-toolkit/12.9.2.0/); [terms](../../THIRD_PARTY_NOTICES.md) | **COMPATIBLE-WITH-CONDITION**: metadata-only meta-package: installs no code or data of its own; selects the nvidia-* component wheels, which are the NVIDIA rows under the NVIDIA EULA (optional component, not redistributed by this repository). |
| cupy-cuda12x | 14.2.0 | MIT; BSD/Apache-2.0/LLVM-exception component terms | `cupy/_core/include/cupy/_cccl/LICENSE`; all 6 installed files identified by the linked texts/inventory | [Source](https://github.com/cupy/cupy); [text](../../THIRD_PARTY_NOTICES.md#text-03), [text](../../THIRD_PARTY_NOTICES.md#text-04), [text](../../THIRD_PARTY_NOTICES.md#text-05), [text](../../THIRD_PARTY_NOTICES.md#text-06), [text](../../THIRD_PARTY_NOTICES.md#text-07), [text](../../THIRD_PARTY_NOTICES.md#text-08) | **COMPATIBLE-WITH-CONDITION**: Optional gpu extra; retain complete CuPy aggregate and component texts; separately installed CUDA position in the notices. |
| numpy | 2.5.4 | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0; bundled OpenBLAS/LAPACK and GCC runtime exception | `numpy-2.5.4.dist-info/licenses/LICENSE.txt`; all 20 installed files identified by the linked texts/inventory | [Source](https://github.com/numpy/numpy); [text](../../THIRD_PARTY_NOTICES.md#text-09), [text](../../THIRD_PARTY_NOTICES.md#text-10), [text](../../THIRD_PARTY_NOTICES.md#text-11), [text](../../THIRD_PARTY_NOTICES.md#text-12), [text](../../THIRD_PARTY_NOTICES.md#text-13), [text](../../THIRD_PARTY_NOTICES.md#text-14), [text](../../THIRD_PARTY_NOTICES.md#text-15), [text](../../THIRD_PARTY_NOTICES.md#text-16), [text](../../THIRD_PARTY_NOTICES.md#text-17), [text](../../THIRD_PARTY_NOTICES.md#text-18), [text](../../THIRD_PARTY_NOTICES.md#text-19), [text](../../THIRD_PARTY_NOTICES.md#text-20), [text](../../THIRD_PARTY_NOTICES.md#text-21), [text](../../THIRD_PARTY_NOTICES.md#text-22), [text](../../THIRD_PARTY_NOTICES.md#text-23), [text](../../THIRD_PARTY_NOTICES.md#text-24), [text](../../THIRD_PARTY_NOTICES.md#text-25) | **COMPATIBLE-WITH-CONDITION**: Retain the complete aggregate and component copyright, conditions, disclaimers and GCC exception in the notices. |
| nvidia-cublas-cu12 | 12.9.2.10 | NVIDIA CUDA EULA (proprietary) | `nvidia_cublas_cu12-12.9.2.10.dist-info/licenses/License.txt` | [Source](https://developer.nvidia.com/cuda-zone); [text](../../THIRD_PARTY_NOTICES.md#text-26) | **COMPATIBLE-WITH-CONDITION**: Optional, user-installed component; not redistributed by Clearwater and not GPL-compatible as a combined work. Retain NVIDIA copyright/EULA and component notices in the notices if redistributing under its terms. |
| nvidia-cuda-nvrtc-cu12 | 12.9.86 | NVIDIA CUDA EULA (proprietary) | `nvidia_cuda_nvrtc_cu12-12.9.86.dist-info/licenses/License.txt` | [Source](https://developer.nvidia.com/cuda-zone); [text](../../THIRD_PARTY_NOTICES.md#text-26) | **COMPATIBLE-WITH-CONDITION**: Optional, user-installed component; not redistributed by Clearwater and not GPL-compatible as a combined work. Retain NVIDIA copyright/EULA and component notices in the notices if redistributing under its terms. |
| nvidia-cuda-runtime-cu12 | 12.9.79 | NVIDIA CUDA EULA (proprietary) | `nvidia_cuda_runtime_cu12-12.9.79.dist-info/licenses/License.txt` | [Source](https://developer.nvidia.com/cuda-zone); [text](../../THIRD_PARTY_NOTICES.md#text-26) | **COMPATIBLE-WITH-CONDITION**: Optional, user-installed component; not redistributed by Clearwater and not GPL-compatible as a combined work. Retain NVIDIA copyright/EULA and component notices in the notices if redistributing under its terms. |
| nvidia-cufft-cu12 | 11.4.1.4 | NVIDIA CUDA EULA (proprietary) | `nvidia_cufft_cu12-11.4.1.4.dist-info/licenses/License.txt` | [Source](https://developer.nvidia.com/cuda-zone); [text](../../THIRD_PARTY_NOTICES.md#text-26) | **COMPATIBLE-WITH-CONDITION**: Optional, user-installed component; not redistributed by Clearwater and not GPL-compatible as a combined work. Retain NVIDIA copyright/EULA and component notices in the notices if redistributing under its terms. |
| nvidia-curand-cu12 | 10.3.10.19 | NVIDIA CUDA EULA (proprietary) | `nvidia_curand_cu12-10.3.10.19.dist-info/License.txt` | [Source](https://developer.nvidia.com/cuda-zone); [text](../../THIRD_PARTY_NOTICES.md#text-26) | **COMPATIBLE-WITH-CONDITION**: Optional, user-installed component; not redistributed by Clearwater and not GPL-compatible as a combined work. Retain NVIDIA copyright/EULA and component notices in the notices if redistributing under its terms. |
| nvidia-cusolver-cu12 | 11.7.5.82 | NVIDIA CUDA EULA (proprietary) | `nvidia_cusolver_cu12-11.7.5.82.dist-info/licenses/License.txt` | [Source](https://developer.nvidia.com/cuda-zone); [text](../../THIRD_PARTY_NOTICES.md#text-26) | **COMPATIBLE-WITH-CONDITION**: Optional, user-installed component; not redistributed by Clearwater and not GPL-compatible as a combined work. Retain NVIDIA copyright/EULA and component notices in the notices if redistributing under its terms. |
| nvidia-cusparse-cu12 | 12.5.10.65 | NVIDIA CUDA EULA (proprietary) | `nvidia_cusparse_cu12-12.5.10.65.dist-info/licenses/License.txt` | [Source](https://developer.nvidia.com/cuda-zone); [text](../../THIRD_PARTY_NOTICES.md#text-26) | **COMPATIBLE-WITH-CONDITION**: Optional, user-installed component; not redistributed by Clearwater and not GPL-compatible as a combined work. Retain NVIDIA copyright/EULA and component notices in the notices if redistributing under its terms. |
| nvidia-nvjitlink-cu12 | 12.9.86 | NVIDIA CUDA EULA (proprietary) | `nvidia_nvjitlink_cu12-12.9.86.dist-info/licenses/License.txt` | [Source](https://developer.nvidia.com/cuda-zone); [text](../../THIRD_PARTY_NOTICES.md#text-26) | **COMPATIBLE-WITH-CONDITION**: Optional, user-installed component; not redistributed by Clearwater and not GPL-compatible as a combined work. Retain NVIDIA copyright/EULA and component notices in the notices if redistributing under its terms. |
| pillow | 12.3.0 | MIT-CMU (PIL/HPND family); bundled codec/font terms | `pillow-12.3.0.dist-info/licenses/LICENSE` | [Source](https://github.com/python-pillow/Pillow); [text](../../THIRD_PARTY_NOTICES.md#text-27) | **COMPATIBLE-WITH-CONDITION**: Retain the complete aggregate in the notices, including FreeType and libjpeg acknowledgements. |
| pillow-heif | 1.8.1 | BSD-3-Clause wrapper; binary wheel GPLv2 with LGPLv3/GPLv2-or-later components | `pillow_heif-1.8.1.dist-info/licenses/LICENSE.txt`; all 2 installed files identified by the linked texts/inventory | [Source](https://github.com/bigcat88/pillow_heif); [text](../../THIRD_PARTY_NOTICES.md#text-28), [text](../../THIRD_PARTY_NOTICES.md#text-29), [text](../../THIRD_PARTY_NOTICES.md#text-37), [text](../../THIRD_PARTY_NOTICES.md#text-38), [text](../../THIRD_PARTY_NOTICES.md#text-39), [text](../../THIRD_PARTY_NOTICES.md#text-40), [text](../../THIRD_PARTY_NOTICES.md#text-41), [text](../../THIRD_PARTY_NOTICES.md#text-42), [text](../../THIRD_PARTY_NOTICES.md#text-43), [text](../../THIRD_PARTY_NOTICES.md#text-44) | **COMPATIBLE-WITH-CONDITION**: Retain wrapper and bundled manifest, native component notices and corresponding-source pointers in the notices; LGPL libraries remain replaceable. |
| pyside6-essentials | 6.12.0 | LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only (metadata) | `pyside6_essentials-6.12.0.dist-info/METADATA`; `pyside6_essentials-6.12.0.dist-info/licenses/LicenseRef-Qt-Commercial.txt` (commercial only; R2) | [Source](https://code.qt.io/cgit/pyside/pyside-setup.git/); [terms](../../THIRD_PARTY_NOTICES.md) | **COMPATIBLE-WITH-CONDITION**: Clearwater relies on LGPL-3.0 for dynamically linked, replaceable QtCore/QtGui/QtWidgets; Qt notice in the notices. |
| scipy | 1.18.1 | BSD-3-Clause; bundled library terms | `scipy-1.18.1.dist-info/LICENSE.txt`; all 5 installed files identified by the linked texts/inventory | [Source](https://github.com/scipy/scipy); [text](../../THIRD_PARTY_NOTICES.md#text-30), [text](../../THIRD_PARTY_NOTICES.md#text-31), [text](../../THIRD_PARTY_NOTICES.md#text-32), [text](../../THIRD_PARTY_NOTICES.md#text-33), [text](../../THIRD_PARTY_NOTICES.md#text-34) | **COMPATIBLE-WITH-CONDITION**: Retain aggregate OpenBLAS/LAPACK/GCC notices plus uarray, duccfft, DOP and Qhull texts in the notices. |
| shiboken6 | 6.12.0 | LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only (metadata) | `shiboken6-6.12.0.dist-info/METADATA`; `shiboken6-6.12.0.dist-info/licenses/LicenseRef-Qt-Commercial.txt` (commercial only; R2) | [Source](https://code.qt.io/cgit/pyside/pyside-setup.git/); [terms](../../THIRD_PARTY_NOTICES.md) | **COMPATIBLE-WITH-CONDITION**: LGPL-3.0 binding runtime, dynamically linked and replaceable; Qt notice in the notices. |
| tifffile | 2026.10.15 | BSD-3-Clause | `tifffile-2026.10.15.dist-info/licenses/LICENSE` | [Source](https://github.com/cgohlke/tifffile); [text](../../THIRD_PARTY_NOTICES.md#text-35) | **COMPATIBLE**: Retain Christoph Gohlke/contributors' copyright, conditions and disclaimer in the notices. |
| FFmpeg / ffprobe | 9.0.2-full_build-www.gyan.dev (outside lock) | GPL-3.0-or-later | Environment report `ffmpeg_version`; external executable build/licensing pages (not installed as a Python distribution) | [Tested build/source](https://www.gyan.dev/ffmpeg/builds/); [licensing](https://ffmpeg.org/legal.html) | COMPATIBLE-WITH-CONDITION: separate process, not redistributed, located on PATH. User obtains its licence and corresponding source from the build publisher. |

### Native contents and conditions

The [native component notices](../../THIRD_PARTY_NOTICES.md#native-components-and-conditions)
cover the wheel contents as well as the Python distributions:

| Component | Version / evidence | Licence and disposition |
| --- | --- | --- |
| NumPy/SciPy bundled libraries | Installed aggregates and component files, texts 09-25 and 30-34 | COMPATIBLE-WITH-CONDITION: retain OpenBLAS/LAPACK, GCC runtime exception and all other aggregate/component notices. |
| Pillow bundled libraries | Installed aggregate, text 27; twelve named component versions in the notices | COMPATIBLE-WITH-CONDITION: retain all codec/font copyrights and acknowledgements, including FreeType and libjpeg. |
| libheif | 1.23.6; pillow-heif bundled manifest and [versioned source](https://github.com/strukturag/libheif/tree/v1.23.6), texts 39/42 | LGPL-3.0; COMPATIBLE-WITH-CONDITION: common LGPLv3 text, copyright/project notice, corresponding source and replacement/relinking rights. |
| libde265 | 1.1.3; same manifest and [versioned source](https://github.com/strukturag/libde265/tree/v1.1.3), texts 40/43 | LGPL-3.0; COMPATIBLE-WITH-CONDITION: same LGPL obligations. |
| x265 | 4.3; same manifest and [versioned source](https://github.com/Multicorewareinc/x265/tree/4.3), texts 37/38 | GPL-2.0-or-later; COMPATIBLE-WITH-CONDITION: preserve GPL text, Multicoreware copyright/source grant and source access. It is bundled even though Clearwater only reads HEIC. |
| MinGW-w64 / winpthreads | Version not recorded by the wheel; bundled DLL/manifest evidence; [MinGW](https://github.com/mingw-w64/mingw-w64/blob/master/COPYING) / [winpthreads](https://github.com/mingw-w64/mingw-w64/blob/master/mingw-w64-libraries/winpthreads/COPYING), texts 41/44 | GPL with GCC runtime exception / MIT-BSD; COMPATIBLE-WITH-CONDITION: retain notices and exception. Unversioned upstream copies explicitly dated 2026-11-03; no invented version match. |

CHARC's round-0 ruling, message `ce6094d108b9546f`, resolved the four STOPs:

| Ruling | Position applied |
| --- | --- |
| R1 | cuda-toolkit is a metadata-only selector installing no code/data of its own. Its NVIDIA component wheels retain their EULA. COMPATIBLE-WITH-CONDITION under the optional, separately installed component position; no licence text invented for the selector. |
| R2 | Qt/Shiboken use LGPL-3.0 dynamic linking and remain replaceable. Clearwater imports QtCore/QtGui/QtWidgets only. Both installed wheels supply only `LicenseRef-Qt-Commercial.txt`; their METADATA declares LGPL/GPL options. Upstream licensing/attributions and the common LGPLv3 text supply the open-source evidence; the commercial text is not relied on. |
| R3 | No FFmpeg local-config key exists. The guide instructs installation on PATH; the local-config template separately supplies footage/working paths to instruments. |
| R4 | Exactly the root `uv.lock` version row may change from 0.0.0 to 1.0.0. The saved diff is one insertion/one deletion; no dependency row changed. |

Clearwater's **GPL-2.0-or-later** permits the GPLv3-compatible branch needed by
Apache/LGPLv3-bearing components. FFmpeg is separately installed, not bundled,
and invoked as a separate process. The notices quote the complete NVIDIA EULA
section 1.1.1(3), including its distribution conditions. NVIDIA's proprietary
EULA is not GPL-compatible as a combined work; the accepted position is that
optional CuPy/ctk CUDA components are installed separately by the user and not
redistributed by this source repository. No incompatible dependency was
established; these conditional positions are disclosed rather than converted
into an unconditional compatibility claim. N13 satisfaction is CHARC's accept
record, still pending.

### Development / comms only

These 43 packages are outside the selected installed-program runtime closure.
Versions, groups and licences below come from the existing audit/notices, with
per-distribution METADATA/licence-file evidence retained in `audit.json` and
the round-0 licence evidence folder. No program notice is required for these
development tools. Source URLs are retained in the notices' dev/comms table.

| Component | Version | Group | Licence |
| --- | --- | --- | --- |
| annotated-doc | 0.0.5 | comms | MIT |
| annotated-types | 0.8.0 | comms | MIT |
| anyio | 4.15.1 | comms | MIT |
| av | 16.1.0 | dev | BSD-3-Clause |
| certifi | 2026.7.22 | comms | MPL-2.0 |
| click | 8.5.0 | comms | BSD-3-Clause |
| colorama | 0.4.6 | dev | BSD-3-Clause |
| execnet | 2.1.2 | dev | MIT |
| fastapi | 0.143.1 | comms | MIT |
| h11 | 0.16.0 | comms | MIT |
| httpcore | 1.0.9 | comms | BSD-3-Clause |
| httptools | 0.9.0 | comms | MIT |
| httpx | 0.28.1 | comms | BSD-3-Clause |
| idna | 3.20 | comms | BSD-3-Clause |
| iniconfig | 2.3.1 | dev | MIT |
| jinja2 | 3.1.6 | comms | BSD License |
| librt | 0.16.0 | dev | MIT |
| markupsafe | 3.0.4 | comms | BSD-3-Clause |
| mypy | 1.20.2 | dev | MIT |
| mypy-extensions | 1.1.0 | dev | MIT |
| opentelemetry-api | 1.45.1 | comms | Apache-2.0 |
| packaging | 26.3 | dev | Apache-2.0 OR BSD-2-Clause |
| pathspec | 1.1.1 | dev | MPL-2.0 |
| pluggy | 1.6.0 | dev | MIT |
| psutil | 7.2.2 | dev | BSD-3-Clause |
| py-cpuinfo | 9.0.0 | dev | MIT |
| pydantic | 2.14.1 | comms | MIT |
| pydantic-core | 2.50.1 | comms | MIT |
| pygments | 2.21.0 | dev | BSD-2-Clause |
| pytest | 8.4.2 | dev | MIT |
| pytest-qt | 4.5.0 | dev | MIT |
| pytest-timeout | 2.4.0 | dev | MIT |
| pytest-xdist | 3.8.0 | dev | MIT |
| python-dotenv | 1.2.4 | comms | BSD-3-Clause |
| python-multipart | 0.0.32 | comms | Apache-2.0 |
| pyyaml | 6.0.3 | comms | MIT |
| ruff | 0.17.0 | dev | MIT |
| starlette | 1.8.0 | comms | BSD-3-Clause |
| typing-extensions | 4.16.0 | comms, dev | PSF-2.0 |
| typing-inspection | 0.4.4 | comms | MIT |
| uvicorn | 0.54.0 | comms | BSD-3-Clause |
| watchfiles | 1.3.0 | comms | MIT |
| websockets | 17.2 | comms | BSD-3-Clause |

The Windows audit excludes marker-inapplicable uvloop. Unselected extras such
as imagecodecs are outside the runtime closure. `uv_build` is a build-system
requirement, not an installed runtime/dev/comms closure member.

## Exercised walkthrough

Turn-2 evidence is under `work/wp5.5/walkthrough/`; exact commands/exit codes
are in `results.json`, with inspection in `inspection.log` and
`video-probe.json`. This turn does not rerun the walkthrough or sync an
environment. All exports below used shipped fixtures and wrote inside this
worktree; no footage item was opened.

The cell exercised the guide's headless commands with package-scoped output
folders (the published guide now uses neutral `work/try` folders):

```powershell
uv run --no-sync python tools/headless_export.py tests/fixtures/stills/jpeg/jpeg-gradient-srgb.jpg --out work/wp5.5/walkthrough/photo --settings-dir work/wp5.5/walkthrough/settings --force-cpu --bit-depth 16 --record work/wp5.5/walkthrough/photo.json
uv run --no-sync python tools/headless_export.py tests/fixtures/video/hevc8-bt709-full.mp4 --out work/wp5.5/walkthrough/video --settings-dir work/wp5.5/walkthrough/settings --cache-dir work/wp5.5/walkthrough/cache --force-cpu --encoder libx265 --quality standard --record work/wp5.5/walkthrough/video.json
```

| Step | Seat / result / evidence |
| --- | --- |
| Photo | Cell turn 2, exit 0; `jpeg-gradient-srgb_corrected.png`, 96x64, 16-bit RGB, 588-byte ICC, embedded app_version 1.0.0. `photo.log`, `photo.json`, `inspection.log`. |
| Video | Cell turn 2, exit 0; `hevc8-bt709-full_corrected.mp4`, HEVC, 320x180, yuvj420p, 30000/1001 fps, 45 frames, full range, BT.709 tags, embedded app_version 1.0.0. `video.log`, `video.json`, `video-probe.json`. |
| Startup smoke | Cell turn 2, exit 0; **1 passed in 6.71s**. Existing `test_python_m_clearwater_starts_the_shell_and_exits_0` launches the real `python -m clearwater` offscreen and closes its event loop. `startup-test.log`. No sitecustomize hook or interactive GUI walkthrough was used. |
| Lean installation | Cell turn 2, `uv sync --no-default-groups`, exit 0 in the dedicated `work/wp5.5/walkthrough/lean-venv`; 8 distributions, pytest/CuPy absent. `lean-sync-online.log`, `lean-distributions.json`. The full environment's 62 METADATA hashes remained unchanged. |
| Lean photo | Cell turn 2, exit 0; output in `lean-photo/jpeg-gradient-srgb_corrected.png`. `lean-photo.log`. |
| Lean environment report | Orchestrator seat, exit 0; original unpinned command below installed two temporary diagnostic tools. `environment/reports/environment-20261103T234816Z.json`: Python 3.12.13, FFmpeg 9.0.2-full_build-www.gyan.dev, `unavailable {}`. Cell confirmed the report and that the lean environment still contained 8 distributions. |
| Independent exports | Reviewer A rounds 1 and 2 reran both fixture commands with output folders relocated to its probe folder; both exited 0 and produced the documented PNG/MP4 names. Source: `work/wp5.5/A-r1-review.txt` (F6) and `A-r2-review.txt` (F6). |

The offscreen test command, with `QT_QPA_PLATFORM=offscreen` and redirected
application-data folders under the walkthrough root, was:

```powershell
$env:PYTHONPATH = 'scripts'
uv run pytest tests/test_app_startup.py::test_python_m_clearwater_starts_the_shell_and_exits_0 --timeout 300 --basetemp=work/wp5.5/t2-startup -p sandbox_mkdir_shim -p no:cacheprovider
```

The successful lean diagnostic was run by the orchestrator with
`UV_PROJECT_ENVIRONMENT` set to this worktree's lean-venv:

```powershell
uv run --no-sync --with psutil --with py-cpuinfo python tools/environment_report.py --out work/wp5.5/walkthrough/environment
```

The cell's earlier online attempt exited 2 (index connection refused); offline
exited 1 (psutil not cached). The orchestrator's successful run resolved that
execution prerequisite before round 1. The full-environment diagnostic also
exited 0 (`environment-20261103T234509Z.json`), but is not used as a substitute
for the lean run. Reviewer A round 2 independently ran the original guide
diagnostic successfully with the same Python/FFmpeg and empty unavailable map.

N4 now pins the diagnostic tools to the dev group's ranges:

```powershell
uv run --no-sync --with "psutil>=6,<8" --with "py-cpuinfo>=9,<10" python tools/environment_report.py --out work/environment
```

It was deliberately not attempted in the cell's network-restricted sandbox.
**Run at the orchestrator's seat** (2026-11-04 00:26Z, network available; lean environment `work\wp5.5\walkthrough\lean-venv` via `UV_PROJECT_ENVIRONMENT`, output folder `work/wp5.5/walkthrough/environment`): exit 0; report `environment-20261104T002627Z.json`; `python_version` 3.12.13; `ffmpeg_version` "ffmpeg version 9.0.2-full_build-www.gyan.dev"; `unavailable` {}; `uv_version` 0.10.9.

## Tests and validation

RED preceded the turn-2 implementation. Logs are under `work/wp5.5/`.

| Control | RED | GREEN / independent evidence |
| --- | --- | --- |
| Release literal | 0.0.0 != 1.0.0, intended failure | 1.0.0; matching TOML and installed metadata. Reviewer A r1 mutations of the live version or installed metadata fail the tests. |
| Real photo provenance | Already passed before bump: live wiring existed | Real exported PNG carries 1.0.0. Reviewer A r2 mutation of app_version to 0.0.0 makes `test_photo_export_records_the_application_version` fail. |
| D106 arithmetic | Old 25.0 disagrees with 12.0 derived at 29.97 fps | `test_d106_is_0_4004_seconds_per_frame_at_29_97` passes; docstring names D106/spec v0.5.8. |
| N6 constant | 25.0 != 12.0, intended failure | `test_d106_matches_spec_n6_12_minutes_per_minute` passes; record assertion reads the constant. |
| Listing bytes | CRLF-stream output contains CR, intended failure | `test_wholeset_listing_writes_lf_bytes_on_a_crlf_stream` passes. Reviewer A independently reproduced old `print` output with CRLF and confirmed the regression test catches it. |

| Run | Exit | Summary / log |
| --- | --- | --- |
| Turn-2 RED | 1 | 4 failed, 68 passed, 1 deselected in 71.91s; `t2-red.log`. |
| Turn-2 final GREEN | 0 | 72 passed, 1 deselected in 67.94s; `t2-green-final.log`. |
| Reviewer A r1 baseline | 0 | 72 passed, 1 deselected in 67.36s; findings copy. |
| Turn-3 targeted | 0 | 72 passed, 1 deselected in 72.09s; `t3.log`. |
| Reviewer A r2 baseline | 0 | 72 passed, 1 deselected in 68.50s; findings copy. |
| Turn-4 targeted | 0 | 72 passed, 1 deselected in 70.20s; `t4.log`. |
| Turn-4 ruff check | 0 | All checks passed!; `t4-ruff.log`. |
| Turn-4 format check | 0 | 317 files already formatted; `t4-format.log`. |
| Turn-4 mypy | 0 | Success: no issues found in 158 source files; `t4-mypy.log`. |
| Turn-4 F1 source-byte verification | 0 | 44 texts, 0 mismatches; 54 source records; hashes/counts equal source bytes; all four mojibake markers 0; full EULA clause matches; `t4-notices-verify.log`. |

The cell's pytest runs always used the sandbox shim, disabled cacheprovider
and a worktree basetemp. The existing slow halo test is the one deselection in
the prescribed targeted run. No whole suite or xdist run occurred at this seat.
Turn-4's exact targeted command was:

```powershell
$env:PYTHONPATH = 'scripts'
uv run pytest tests/test_version.py tests/test_export_bench.py tests/test_tools_halo_part3.py -m "not gpu and not footage and not gui and not slow and not fullclip" --timeout 300 --basetemp=work/wp5.5/t4 -p sandbox_mkdir_shim -p no:cacheprovider > work/wp5.5/t4.log 2>&1
```

The static commands were `uv run ruff check .`, `uv run ruff format --check .`
and `uv run mypy`, each logged separately. uv warned that the inherited
VIRTUAL_ENV did not match the project environment and was ignored; the runs
used this worktree's `.venv`, not the main tree's environment.

## Verification loop and review

| Round | Suspected / confirmed / rejected / fixed |
| --- | --- |
| 0 | Four NEW MAJOR STOPs: missing selector licence, Qt wheel evidence gap, nonexistent FFmpeg config key, unowned root lock version. All confirmed; none rejected. CHARC R1-R4 resolved the positions/ownership before build; no incompatible dependency established. |
| Turn 2 | Stale D106, CRLF listing and release literal confirmed by RED and fixed; missing/repeated notice conditions addressed during assembly. Suspected lock/dependency drift, README damage and lean install mutation rejected with diff/hash/distribution evidence. Network diagnostic prerequisite confirmed, subsequently resolved at the orchestrator seat. Its notice check compared corrupted evidence copies; F1 corrected that verification weakness in turn 3. |
| A r1 | **0 critical / 2 major / 4 minor / 4 advisory**, all 10 NEW/in-envelope; 0 reverts, 0 product-code fixes. F1-F9 confirmed/fixed (including UTF-8 source recopy, actual Settings menu and complete EULA quote); F10 confirmed/no change, lean evidence supplied. F5's absent native version remained an explicit disclosure. No finding rejected. Verdict NEW_CRITICAL_MAJOR_FOUND. |
| A r2 | **0 critical / 0 major / 2 minor / 1 reopened partial / 4 advisory**, all in envelope; NEW N1-N4, REOPENED F7, F8 regression; 0 reverts, 0 product-code fixes. Verdict **NO_NEW_CRITICAL_MAJOR**. All cleanup findings confirmed, none rejected; fixes listed below. F5's native-version disclosure remains accepted. |

Round-2 fixes in this turn: F7 replaces turn vocabulary/stale re-fetch caveats
with the 2026-11-03 copy date; F5's remaining dev link points to pydantic-core
2.50.1's release page; F8 names the required external archive folder; N1 starts
export through File > Export and locates status/progress/Cancel in its panel;
N2 links texts 37-44 from pillow-heif's row; N3 uses panel/button wording for
Batch; N4 pins the two diagnostic ranges. The F1 script was rerun after all
notices changes, against original source bytes. Reviewer A r2 also re-fetched
all nine upstream supplements on 2026-11-03: five whole-file matches and four
matches to the declared selections. The cell did not re-fetch them this turn.

Reviewer A's loop converged on blocking findings under the fill's criterion;
this turn is its non-blocking cleanup, not another review round. Detailed
per-finding adjudication and transport/version evidence limits are in the
ledger and the two review copies. Reviewer B remains the orchestrator's
independent Claude pass on the final candidate.

## Limits

- One Windows 11 machine class was exercised, with Python 3.12.13. No timing
  or memory measurement was performed by this package; figures in the guide
  refer to the cited reports under their recorded conditions.
- Only FFmpeg 9.0.2-full_build-www.gyan.dev was exercised. Substitution of
  another FFmpeg build was not tested.
- The lean sync and successful lean environment-report command were each
  exercised once (cell and orchestrator seats respectively). Reviewer A's
  additional diagnostic run does not establish a second lean install. The
  revised ranged diagnostic still awaits the orchestrator-seat run.
- GUI evidence is the offscreen startup smoke only. The GUI walkthrough was
  written from code and checked by Reviewer A against source, not performed
  interactively by a camera user.
- MinGW/winpthreads versions are absent from the wheel manifest. Their source
  pointers remain unversioned, with that limitation disclosed.
- Upstream-only texts were copied on 2026-11-03; their date and selected
  boundaries are stated. Reviewer A independently checked them on that date.

## Release gate

**PENDING: the orchestrator's release gate.** No package-targeted result above
is a release-gate figure. The [checklist](../release-checklist.md) delegates
the exact collection/outcome/stall-watch rules to
[the review/gate fill](../review-gate-clearwater.md). The orchestrator runs
static, collection identity, parallel, serial, fullclip and harness on the
final candidate after Reviewer B, with no sandbox shim. Representative
commands below use a fresh RUN identifier; logs, exit codes, conditions and
JUnit files must be retained. They have not been executed by this cell.

```bash
df -h /c
export QT_QPA_PLATFORM=offscreen
unset PYTEST_ADDOPTS
uv run ruff check . > work/release-RUN-ruff.log 2>&1
uv run ruff format --check . > work/release-RUN-format.log 2>&1
uv run mypy > work/release-RUN-mypy.log 2>&1
uv run pytest --collect-only -q --basetemp=work/release-RUN-collect-all > work/release-RUN-all.txt 2>&1
uv run pytest --collect-only -q -m "not gpu and not footage and not gui and not slow and not fullclip" --basetemp=work/release-RUN-collect-parallel > work/release-RUN-parallel.txt 2>&1
uv run pytest --collect-only -q -m "(gpu or footage or gui or slow) and not fullclip" --basetemp=work/release-RUN-collect-serial > work/release-RUN-serial.txt 2>&1
uv run pytest --collect-only -q -m "fullclip" --basetemp=work/release-RUN-collect-fullclip > work/release-RUN-fullclip.txt 2>&1
uv run pytest -q -rs -n 4 --timeout 600 -m "not gpu and not footage and not gui and not slow and not fullclip" --basetemp=work/release-RUN-parallel --junitxml=work/release-RUN-parallel.xml > work/release-RUN-parallel.log 2>&1
uv run pytest -q -rs --timeout 1200 -m "(gpu or footage or gui or slow) and not fullclip" --basetemp=work/release-RUN-serial --durations=0 --junitxml=work/release-RUN-serial.xml > work/release-RUN-serial.log 2>&1
uv run pytest -q -rs --timeout 2400 -m "fullclip" --basetemp=work/release-RUN-fullclip --durations=0 --junitxml=work/release-RUN-fullclip.xml > work/release-RUN-fullclip.log 2>&1
uv run python -m unittest discover -s tests/harness > work/release-RUN-harness.log 2>&1
```

The disk floor is **25 GB**, checked before each heavy leg; the fill additionally
requires at least 5 GiB available RAM before each heavy leg. The orchestrator
must verify local configuration, collection identity against main, counts,
skips and the stall watch, stopping on failure. No other pytest runs beside
serial/fullclip. Archive the figures of record to
`clearwater-review-evidence\release-1.0.0\` outside the clone. The orchestrator
fills the release figures at accept; CHARC writes `docs/proofs/release-1.0.0.md`.
Only the owner's explicit "tag 1.0.0" authorizes the annotated merge-commit tag.

## Deviations, locks and handoff

R3 corrects the brief's assumed FFmpeg configuration to the shipped PATH
behavior. R4 adds only the root lockfile version row to ownership. The guide
documents Windows paths, the Windows-only pipe-buffer tuning (AD-23), driver
baseline and tested platform; no new OS-specific product code was introduced.
The guide's GPU/default-group distinction follows the locked installation as
it exists. DR-117 is owner-deferred, not pending a decision.

No unresolved design or licence question remains. Pending actions have named
owners: the orchestrator exercises the N4 ranged diagnostic and runs Reviewer B
and the release gate; CHARC records N13 satisfaction, formal DR-119 (a)-(b)
closure, acknowledged debt and Phase 5 closure at acceptance; tagging waits
for the owner's word. DR-119 (c)-(d) are banked to Phase 6. These are not
completed cell actions.

The package preserves LICENSE, the spec, the local-config template, dependency
lists and frozen interfaces. This turn changes only the five authorized
documentation paths, with no code/test/dependency/lockfile change. No footage,
main-tree work directory or other worktree was read; outputs/logs stay in this
worktree. No sync, whole-suite/xdist run, git write, mailbox post, remote action,
installer, packaged executable or unapproved heavy gate was performed. The
orchestrator commits the named files; this report and the final message are
the acceptance-transfer handoff.
