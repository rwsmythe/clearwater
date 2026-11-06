# Third-party notices - Clearwater 1.1.0

Clearwater's own code is licensed under **GNU GPL version 2 or any later version
(GPL-2.0-or-later)**; see [LICENSE](LICENSE). The 'or later' grant allows the
GPLv3-compatible branch for Apache-2.0 and LGPL-3.0 components and any GPLv3
combination. It does not make NVIDIA's proprietary EULA GPL-compatible.
FFmpeg is GPL-3.0-or-later and runs as a separate process in any case.

This repository delivers source installed with uv, not an installer, executable
or vendored dependency wheels. Dependencies are obtained from their publishers.
These notices preserve the audited installed wheels' notices and identify
corresponding sources; any future binary redistributor must independently meet
source-delivery and other licence obligations. No third-party licence is changed.

The 1.1.0 release zip carries its own generated `THIRD_PARTY_NOTICES.md` beside
`Clearwater.exe`; that file is the notice of record for the artifact. This root
file preserves the 1.0.0 source-install audit and its licence inputs, with the
FFmpeg row updated for the 1.1.0 bundle.

## Runtime dependency audit

Versions below are pinned by `uv.lock` and matched installed metadata in the
Windows AMD64 / Python 3.12 audit. Python and FFmpeg are external tools in a
source install; the 1.1.0 Windows artifact bundles both.
The 18 runtime distributions include the optional gpu extra and every selected
transitive dependency. Native component notices, including the platform runtimes
and software OpenGL renderer, are provided separately below.
The verdicts and any conditions are stated for each component below.

| Component | Version | Licence | Verdict and required notice | Source / full text |
| --- | --- | --- | --- | --- |
| Python | 3.12.13 (outside lock) | PSF-2.0 and historical terms | COMPATIBLE: preserve Python copyright and historical notices. The uv-managed CPython 3.12.13 build bundles OpenSSL (`DLLs/libcrypto-3-x64.dll`, `DLLs/libssl-3-x64.dll`), libffi (`DLLs/libffi-8.dll`), SQLite (`DLLs/sqlite3.dll`), Tcl/Tk (`DLLs/tcl86t.dll`, `DLLs/tk86t.dll`) and MSVC (`vcruntime140.dll`, `vcruntime140_1.dll` at the interpreter root), not all named in text 01; in the 1.0.0 source install Python is user-installed by uv and not redistributed. The 1.1.0 artifact REDISTRIBUTES Python and the interpreter's native libraries actually present in its built-folder census; its generated notices name those libraries, exact versions, full texts and corresponding sources. Compiled-in components in the carried interpreter and stdlib natives (zlib, HACL*, BLAKE2, MT19937, SipHash, dtoa, cfuhash, Audioop, expat, libmpdec, bzip2, liblzma and Unicode data) are attributed with their texts in the artifact notices. The audited build input is python-build-standalone 20260303 (CPython 3.12.13, OpenSSL 3.5.5); a build change requires a notices re-audit; see [python-build-standalone](https://github.com/astral-sh/python-build-standalone) for the build component licences. | [Source](https://github.com/python/cpython/tree/v3.12.13); [text](#text-01) |
| cuda-pathfinder | 1.8.3 | Apache-2.0 | **COMPATIBLE-WITH-CONDITION**: Retain NVIDIA copyright, Apache licence and notices below; GPLv3-compatible branch under Clearwater's or-later grant. | [Source](https://github.com/NVIDIA/cuda-python); [text](#text-02) |
| cuda-toolkit | 12.9.2.0 | No licence declaration; metadata-only | **COMPATIBLE-WITH-CONDITION**: metadata-only meta-package: installs no code or data of its own; selects the nvidia-* component wheels, which are the NVIDIA rows under the NVIDIA EULA (optional component, not redistributed by this repository). | [Source](https://pypi.org/project/cuda-toolkit/12.9.2.0/); see notices below |
| cupy-cuda12x | 14.2.0 | MIT; BSD/Apache-2.0/LLVM-exception component terms | **COMPATIBLE-WITH-CONDITION**: Optional gpu extra; retain complete CuPy aggregate and component texts; separately installed CUDA position below. | [Source](https://github.com/cupy/cupy); [text](#text-03), [text](#text-04), [text](#text-05), [text](#text-06), [text](#text-07), [text](#text-08) |
| numpy | 2.5.4 | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0; bundled OpenBLAS/LAPACK and GCC runtime exception | **COMPATIBLE-WITH-CONDITION**: Retain the complete aggregate and component copyright, conditions, disclaimers and GCC exception below. | [Source](https://github.com/numpy/numpy); [text](#text-09), [text](#text-10), [text](#text-11), [text](#text-12), [text](#text-13), [text](#text-14), [text](#text-15), [text](#text-16), [text](#text-17), [text](#text-18), [text](#text-19), [text](#text-20), [text](#text-21), [text](#text-22), [text](#text-23), [text](#text-24), [text](#text-25) |
| nvidia-cublas-cu12 | 12.9.2.10 | NVIDIA CUDA EULA (proprietary) | **COMPATIBLE-WITH-CONDITION**: Optional, user-installed component; not redistributed by Clearwater and not GPL-compatible as a combined work. Retain NVIDIA copyright/EULA and component notices below if redistributing under its terms. | [Source](https://developer.nvidia.com/cuda-zone); [text](#text-26) |
| nvidia-cuda-nvrtc-cu12 | 12.9.86 | NVIDIA CUDA EULA (proprietary) | **COMPATIBLE-WITH-CONDITION**: Optional, user-installed component; not redistributed by Clearwater and not GPL-compatible as a combined work. Retain NVIDIA copyright/EULA and component notices below if redistributing under its terms. | [Source](https://developer.nvidia.com/cuda-zone); [text](#text-26) |
| nvidia-cuda-runtime-cu12 | 12.9.79 | NVIDIA CUDA EULA (proprietary) | **COMPATIBLE-WITH-CONDITION**: Optional, user-installed component; not redistributed by Clearwater and not GPL-compatible as a combined work. Retain NVIDIA copyright/EULA and component notices below if redistributing under its terms. | [Source](https://developer.nvidia.com/cuda-zone); [text](#text-26) |
| nvidia-cufft-cu12 | 11.4.1.4 | NVIDIA CUDA EULA (proprietary) | **COMPATIBLE-WITH-CONDITION**: Optional, user-installed component; not redistributed by Clearwater and not GPL-compatible as a combined work. Retain NVIDIA copyright/EULA and component notices below if redistributing under its terms. | [Source](https://developer.nvidia.com/cuda-zone); [text](#text-26) |
| nvidia-curand-cu12 | 10.3.10.19 | NVIDIA CUDA EULA (proprietary) | **COMPATIBLE-WITH-CONDITION**: Optional, user-installed component; not redistributed by Clearwater and not GPL-compatible as a combined work. Retain NVIDIA copyright/EULA and component notices below if redistributing under its terms. | [Source](https://developer.nvidia.com/cuda-zone); [text](#text-26) |
| nvidia-cusolver-cu12 | 11.7.5.82 | NVIDIA CUDA EULA (proprietary) | **COMPATIBLE-WITH-CONDITION**: Optional, user-installed component; not redistributed by Clearwater and not GPL-compatible as a combined work. Retain NVIDIA copyright/EULA and component notices below if redistributing under its terms. | [Source](https://developer.nvidia.com/cuda-zone); [text](#text-26) |
| nvidia-cusparse-cu12 | 12.5.10.65 | NVIDIA CUDA EULA (proprietary) | **COMPATIBLE-WITH-CONDITION**: Optional, user-installed component; not redistributed by Clearwater and not GPL-compatible as a combined work. Retain NVIDIA copyright/EULA and component notices below if redistributing under its terms. | [Source](https://developer.nvidia.com/cuda-zone); [text](#text-26) |
| nvidia-nvjitlink-cu12 | 12.9.86 | NVIDIA CUDA EULA (proprietary) | **COMPATIBLE-WITH-CONDITION**: Optional, user-installed component; not redistributed by Clearwater and not GPL-compatible as a combined work. Retain NVIDIA copyright/EULA and component notices below if redistributing under its terms. | [Source](https://developer.nvidia.com/cuda-zone); [text](#text-26) |
| pillow | 12.3.0 | MIT-CMU (PIL/HPND family); bundled codec/font terms | **COMPATIBLE-WITH-CONDITION**: Retain the complete aggregate below, including FreeType and libjpeg acknowledgements. | [Source](https://github.com/python-pillow/Pillow); [text](#text-27) |
| pillow-heif | 1.8.1 | BSD-3-Clause wrapper; binary wheel GPLv2 with LGPLv3/GPLv2-or-later components | **COMPATIBLE-WITH-CONDITION**: Retain wrapper and bundled manifest, native component notices and corresponding-source pointers below; LGPL libraries remain replaceable. | [Source](https://github.com/bigcat88/pillow_heif); [text](#text-28), [text](#text-29), [text](#text-37), [text](#text-38), [text](#text-39), [text](#text-40), [text](#text-41), [text](#text-42), [text](#text-43), [text](#text-44) |
| pyside6-essentials | 6.12.0 | LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only (metadata) | **COMPATIBLE-WITH-CONDITION**: Clearwater relies on LGPL-3.0 for dynamically linked, replaceable QtCore/QtGui/QtWidgets; Qt notice below. The carried Qt and shiboken natives also embed third-party code and data, including font/raster and image codecs, PCRE2, Unicode/CLDR, compression, cryptographic helpers, libpsl/PSL, graphics helpers, Wintab and Python buffer/signature code; the artifact notices identify the host-bound components, full copyright notices, licence texts and corresponding sources. | [Source](https://code.qt.io/cgit/pyside/pyside-setup.git/); see notices below |
| scipy | 1.18.1 | BSD-3-Clause; bundled library terms | **COMPATIBLE-WITH-CONDITION**: Retain aggregate OpenBLAS/LAPACK/GCC notices plus uarray, duccfft, DOP and Qhull texts below. For array-api-compat, array-api-extra, cobyqa, prima (pyprima) and packaging.version, see THIRD_PARTY_NOTICES.md inside the packaged artifact. | [Source](https://github.com/scipy/scipy); [text](#text-30), [text](#text-31), [text](#text-32), [text](#text-33), [text](#text-34) |
| shiboken6 | 6.12.0 | LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only (metadata) | **COMPATIBLE-WITH-CONDITION**: LGPL-3.0 binding runtime, dynamically linked and replaceable; Qt notice below. | [Source](https://code.qt.io/cgit/pyside/pyside-setup.git/); see notices below |
| tifffile | 2026.10.15 | BSD-3-Clause | **COMPATIBLE**: Retain Christoph Gohlke/contributors' copyright, conditions and disclaimer below. | [Source](https://github.com/cgohlke/tifffile); [text](#text-35) |
| FFmpeg / ffprobe | n9.0.2-47-gb204e94e90 (release/9.0 at b204e94e90fca64045e9ca7dd44c65678c7eb29e; build 20261106) | GPL-3.0-or-later | COMPATIBLE-WITH-CONDITION: bundled in the 1.1.0 Windows artifact as separate processes; provider rwsmythe/FFmpeg-Builds at d77b8352f60bd180ebce585632846533aa60b183, built from parent BtbN/FFmpeg-Builds at 5031c6f1 (5031c6f1082414e53688d39e521849905071070d) with zvbi excluded because src/packet-830.* / src/pdc.* are GPL-2.0-only. Preserve the artifact notices, GPL-3.0 text and corresponding-source records. A source install obtains FFmpeg and ffprobe separately on PATH, with terms/source from its chosen publisher. | [Fork build/source](https://github.com/rwsmythe/FFmpeg-Builds/tree/d77b8352f60bd180ebce585632846533aa60b183); [FFmpeg source](https://github.com/FFmpeg/FFmpeg/tree/b204e94e90fca64045e9ca7dd44c65678c7eb29e); [lock](tools/package/ffmpeg.lock.json); [licensing](https://ffmpeg.org/legal.html); [Build-component and toolchain-runtime annex](#ffmpeg-build-components-and-toolchain-runtime-census) |

### Native components and conditions

- **NumPy / SciPy:** OpenBLAS, LAPACK and GCC runtimes carry their own notices
  (BSD terms and GPL-3.0-or-later WITH GCC-exception-3.1). NumPy additionally
  carries pocketfft, LAPACK-lite, random generators, libdivide, pythoncapi-compat,
  Highway, Dragon4, x86-simd-sort and SVML; SciPy carries uarray, duccfft, DOP and
  Qhull. Their complete installed aggregate and component texts follow.
- **Pillow:** the aggregate includes Brotli 1.2.0, FreeType 2.14.3, HarfBuzz
  14.2.1, lcms2 2.19.1, libavif 1.4.2, libjpeg-turbo 3.1.4.1, libpng 1.6.58,
  libwebp 1.6.0, OpenJPEG 2.5.4, TIFF 4.7.1, XZ 5.8.3 and zlib-ng 2.3.3.
  All associated copyright lines and licence terms are reproduced in that text.
- **pillow-heif:** the wrapper is BSD-3-Clause; its Windows wheel includes
  [libheif 1.23.6](https://github.com/strukturag/libheif/tree/v1.23.6)
  and [libde265 1.1.3](https://github.com/strukturag/libde265/tree/v1.1.3)
  (LGPL-3.0; the LGPL text below applies to both) and
  [x265 4.3](https://github.com/Multicorewareinc/x265/tree/4.3)
  (GPL-2.0-or-later; Multicoreware, Inc.; source grant and GPL text below).
  x265 is present even though Clearwater reads HEIC and never writes it.
  The wheel also ships MinGW-w64 libgcc_s_seh-1 / libstdc++-6
  (GPL with GCC runtime exception) and libwinpthread-1 (MIT/BSD); retain the
  manifest, MinGW notices below and the GCC exception in the aggregate texts.
  These components are COMPATIBLE-WITH-CONDITION: preserve their notices,
  corresponding-source access and LGPL replacement/relinking rights.
  The wheel manifest names no MinGW-w64 or winpthreads version, so a tagged
  copy matching the shipped runtime cannot be identified. The two unversioned
  upstream notices below were copied on 2026-11-03.
- **CuPy:** Preferred Infrastructure, Inc. / Preferred Networks, Inc.; the
  complete aggregate includes NumPy/SciPy and cuSignal notices, with separate
  CCCL, DLPack, Jitify and ndimage texts below. Apache-bearing combinations rely
  on the GPLv3-compatible branch of Clearwater's or-later grant.
- **Microsoft Visual C++ runtime (MSVC):** the audited wheels contain the
  following Microsoft Corporation compiler/platform runtime DLLs:
  - NumPy 2.5.4: `numpy.libs/msvcp140-a4c2229bdc2a2a630acdc095b4d86008.dll`.
  - PySide6_Essentials 6.12.0: `PySide6/concrt140.dll`, `msvcp140.dll`,
    `msvcp140_1.dll`, `msvcp140_2.dll`, `msvcp140_codecvt_ids.dll`,
    `vcamp140.dll`, `vccorlib140.dll`, `vcomp140.dll`, `vcruntime140.dll` and
    `vcruntime140_1.dll` (all under `PySide6/`).
  - shiboken6 6.12.0: the same ten MSVC DLL names under `shiboken6/`.

  These use Microsoft's Visual C++ Redistributable terms
  ([Microsoft Software License Terms](https://visualstudio.microsoft.com/license-terms/vs2022-cruntime/)).
  The wheels ship no licence file for these runtimes, so no licence text is
  reproduced here. **COMPATIBLE-WITH-CONDITION:** Clearwater's position is that
  these are C/C++ runtime libraries of the compiler and operating-system
  platform, bundled by the wheel publishers (NumPy and The Qt Company) under
  Microsoft's redistribution terms and installed by the user from PyPI. This
  repository does not redistribute them. GPLv2 section 3's major-components
  exception and GPLv3's definition of "System Libraries" address such platform
  runtime libraries. Microsoft code retains its own terms; a future binary
  redistributor must comply with those terms and the applicable GPL obligations.
- **Mesa llvmpipe software OpenGL renderer:** PySide6_Essentials 6.12.0 includes
  `PySide6/opengl32sw.dll`, the software renderer shipped by Qt for Windows.
  Its licence is **MIT**, as identified by
  [Qt's third-party attributions](https://doc.qt.io/qt-6/licenses-used-in-qt.html);
  see the [Mesa licence page](https://docs.mesa3d.org/license.html).
  **COMPATIBLE-WITH-CONDITION:** retain the applicable Mesa copyright notices,
  MIT permission notice and disclaimer on redistribution. The installed wheel's
  metadata/licence files identify no Mesa version or separate Mesa licence text,
  so the source pointer is the Mesa licence page, not a claimed version-matched
  copy. This repository does not redistribute the renderer; no additional
  licence text is reproduced here.

### Qt and Shiboken (LGPL-3.0)

Copyright The Qt Company Ltd. and other contributors; see
[Qt licensing](https://doc.qt.io/qt-6/licensing.html),
[Qt third-party attributions](https://doc.qt.io/qt-6/licenses-used-in-qt.html),
[Qt SBOM/source resources](https://doc.qt.io/qt-6/sbom.html) and the
[binding sources](https://code.qt.io/cgit/pyside/pyside-setup.git/).
Clearwater relies on **LGPL-3.0**, using only QtCore, QtGui and QtWidgets,
dynamically linked and replaceable as installed from PyPI. Unused GPLv3-only
modules in the Essentials wheel are not used by Clearwater (and would be
compatible via GPL-2.0-or-later). Each installed wheel ships only the commercial
licence file; its metadata declares
`LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only`, and the upstream licensing and
attribution pages supply the open-source licensing evidence.
The LGPL-3.0 text is reproduced once below: [text](#text-36).
The accompanying GPLv3 text is also present in the NumPy/SciPy aggregate notices.
Users may replace/relink these libraries and debug modifications, including
reverse engineering for that purpose under LGPLv3; Clearwater imposes no
additional restriction on those rights. Modified Qt/binding distributions must
also meet the LGPL's corresponding-source and installation-information terms.

### Optional CUDA components (not redistributed)

CuPy is an optional `gpu` extra the user installs; its `[ctk]` dependencies obtain
the NVIDIA runtime wheels separately. A plain developer `uv sync` also installs
that extra through the default dev group; the user guide gives a lean install.
NVIDIA's EULA permits redistribution of designated runtime components subject
to its conditions; it is **not GPL-compatible as a combined work**. Clearwater
does not bundle CUDA or claim such a redistribution grant. Clearwater's position
is that these are optional, separately installed components / system libraries;
NVIDIA code retains its own terms. Section 1.1.1(3) grants the right to:

> Distribute those portions of the SDK that are identified in this Agreement as distributable, as incorporated in object code format into a software application that meets the distribution requirements indicated in this Agreement.

Read the restrictions and CUDA supplement too:
[NVIDIA CUDA 12.9 EULA](https://docs.nvidia.com/cuda/archive/12.9.1/eula/index.html).
The full installed EULAs/component notices are reproduced below with NVIDIA's
copyright lines; different installed texts are retained separately.

## Development / comms dependencies - not part of the installed program

These are outside the runtime closure on the audited platform. A default
developer sync installs both groups, but the lean application install does not.
Licences are recorded for audit; these development tools need no notice in the
installed program. MPL-2.0 development packages are not linked into Clearwater.
Exception (2026-11-04, WP6.1, spec N13 second pass): PyInstaller's bootloader and the
run-time hooks it embeds DO reach the user inside a packaged 1.1.0 artifact; their
licence and exception are rowed below and the artifact's own notices (WP6.3) carry
the full text. The source install (this file's subject) carries none of that code.

| Component | Locked / installed version | Group | Licence | Source / metadata |
| --- | --- | --- | --- | --- |
| annotated-doc | 0.0.5 | comms | MIT | [Source](https://github.com/fastapi/annotated-doc); installed METADATA / licence file |
| annotated-types | 0.8.0 | comms | MIT | [Source](https://github.com/annotated-types/annotated-types); installed METADATA / licence file |
| anyio | 4.15.1 | comms | MIT | [Source](https://github.com/agronholm/anyio); installed METADATA / licence file |
| av | 16.1.0 | dev | BSD-3-Clause | [Source](https://github.com/PyAV-Org/PyAV); installed METADATA / licence file |
| certifi | 2026.7.22 | comms | MPL-2.0 | [Source](https://github.com/certifi/python-certifi); installed METADATA / licence file |
| click | 8.5.0 | comms | BSD-3-Clause | [Source](https://github.com/pallets/click/); installed METADATA / licence file |
| colorama | 0.4.6 | dev | BSD-3-Clause | [Source](https://github.com/tartley/colorama); installed METADATA / licence file |
| execnet | 2.1.2 | dev | MIT | [Source](https://execnet.readthedocs.io/en/latest/); installed METADATA / licence file |
| fastapi | 0.143.1 | comms | MIT | [Source](https://github.com/fastapi/fastapi); installed METADATA / licence file |
| h11 | 0.16.0 | comms | MIT | [Source](https://github.com/python-hyper/h11); installed METADATA / licence file |
| httpcore | 1.0.9 | comms | BSD-3-Clause | [Source](https://github.com/encode/httpcore); installed METADATA / licence file |
| httptools | 0.9.0 | comms | MIT | [Source](https://github.com/MagicStack/httptools); installed METADATA / licence file |
| httpx | 0.28.1 | comms | BSD-3-Clause | [Source](https://github.com/encode/httpx); installed METADATA / licence file |
| idna | 3.20 | comms | BSD-3-Clause | [Source](https://github.com/kjd/idna); installed METADATA / licence file |
| iniconfig | 2.3.1 | dev | MIT | [Source](https://github.com/pytest-dev/iniconfig); installed METADATA / licence file |
| jinja2 | 3.1.6 | comms | BSD License | [Source](https://github.com/pallets/jinja/); installed METADATA / licence file |
| librt | 0.16.0 | dev | MIT | [Source](https://github.com/mypyc/librt); installed METADATA / licence file |
| markupsafe | 3.0.4 | comms | BSD-3-Clause | [Source](https://github.com/pallets/markupsafe/); installed METADATA / licence file |
| mypy | 1.20.2 | dev | MIT | [Source](https://github.com/python/mypy); installed METADATA / licence file |
| altgraph | 0.17.5 | dev (PyInstaller dependency) | MIT | [Source](https://github.com/ronaldoussoren/altgraph); installed METADATA / licence file |
| pefile | 2024.8.26 | dev (PyInstaller dependency) | MIT | [Source](https://github.com/erocarrera/pefile); installed METADATA / licence file |
| pyinstaller | 6.22.3 | dev (`pyinstaller>=6.22,<7`, WP6.1) | Bootloader: GPL-2.0-or-later WITH the PyInstaller Bootloader Exception (the exception permits distributing a built executable under the application's own licence). Run-time hooks and additional run-time modules: Apache-2.0. | [Source](https://github.com/pyinstaller/pyinstaller/tree/v6.22.3); installed COPYING.txt states the terms separately for each kind and includes the Bootloader Exception. **Artifact notice (N13, 1.1.0):** the generated artifact notices name the bundled kinds/version and reproduce COPYING.txt verbatim, including its exception and full texts. The source install carries none of this code. |
| pyinstaller-hooks-contrib | 2026.9 | dev (PyInstaller dependency) | GPL-2.0-or-later WITH the same Bootloader Exception; its run-time hooks that a build embeds are covered the same way (named in the artifact notices, WP6.3) | [Source](https://github.com/pyinstaller/pyinstaller-hooks-contrib); installed METADATA / licence file |
| pywin32-ctypes | 0.2.3 | dev (PyInstaller dependency, Windows) | BSD-3-Clause | [Source](https://github.com/enthought/pywin32-ctypes); installed METADATA / licence file |
| mypy-extensions | 1.1.0 | dev | MIT | [Source](https://github.com/python/mypy_extensions); installed METADATA / licence file |
| opentelemetry-api | 1.45.1 | comms | Apache-2.0 | [Source](https://github.com/open-telemetry/opentelemetry-python); installed METADATA / licence file |
| packaging | 26.3 | dev | Apache-2.0 OR BSD-2-Clause | [Source](https://github.com/pypa/packaging); installed METADATA / licence file |
| pathspec | 1.1.1 | dev | MPL-2.0 | [Source](https://github.com/cpburnz/python-pathspec); installed METADATA / licence file |
| pluggy | 1.6.0 | dev | MIT | [Source](https://pypi.org/project/pluggy/1.6.0/); installed METADATA / licence file |
| psutil | 7.2.2 | dev | BSD-3-Clause | [Source](https://github.com/giampaolo/psutil); installed METADATA / licence file |
| py-cpuinfo | 9.0.0 | dev | MIT | [Source](https://github.com/workhorsy/py-cpuinfo); installed METADATA / licence file |
| pydantic | 2.14.1 | comms | MIT | [Source](https://github.com/pydantic/pydantic); installed METADATA / licence file |
| pydantic-core | 2.50.1 | comms | MIT | [Source](https://pypi.org/project/pydantic-core/2.50.1/); installed METADATA / licence file |
| pygments | 2.21.0 | dev | BSD-2-Clause | [Source](https://github.com/pygments/pygments); installed METADATA / licence file |
| pytest | 8.4.2 | dev | MIT | [Source](https://github.com/pytest-dev/pytest); installed METADATA / licence file |
| pytest-qt | 4.5.0 | dev | MIT | [Source](http://github.com/pytest-dev/pytest-qt); installed METADATA / licence file |
| pytest-timeout | 2.4.0 | dev | MIT | [Source](https://github.com/pytest-dev/pytest-timeout); installed METADATA / licence file |
| pytest-xdist | 3.8.0 | dev | MIT | [Source](https://github.com/pytest-dev/pytest-xdist); installed METADATA / licence file |
| python-dotenv | 1.2.4 | comms | BSD-3-Clause | [Source](https://github.com/theskumar/python-dotenv); installed METADATA / licence file |
| python-multipart | 0.0.32 | comms | Apache-2.0 | [Source](https://github.com/Kludex/python-multipart); installed METADATA / licence file |
| pyyaml | 6.0.3 | comms | MIT | [Source](https://github.com/yaml/pyyaml); installed METADATA / licence file |
| ruff | 0.17.0 | dev | MIT | [Source](https://github.com/astral-sh/ruff); installed METADATA / licence file |
| starlette | 1.8.0 | comms | BSD-3-Clause | [Source](https://github.com/Kludex/starlette); installed METADATA / licence file |
| typing-extensions | 4.16.0 | comms, dev | PSF-2.0 | [Source](https://github.com/python/typing_extensions); installed METADATA / licence file |
| typing-inspection | 0.4.4 | comms | MIT | [Source](https://github.com/pydantic/typing-inspection); installed METADATA / licence file |
| uvicorn | 0.54.0 | comms | BSD-3-Clause | [Source](https://github.com/Kludex/uvicorn); installed METADATA / licence file |
| watchfiles | 1.3.0 | comms | MIT | [Source](https://github.com/samuelcolvin/watchfiles); installed METADATA / licence file |
| websockets | 17.2 | comms | BSD-3-Clause | [Source](https://github.com/python-websockets/websockets); installed METADATA / licence file |

`typing-extensions` is shared by dev and comms and listed once. The Linux-only
comms dependency uvloop is not selected on this Windows audit; it is not part
of the installed program. Optional dependencies not selected by the lock's
runtime/gpu closure (for example imagecodecs) are not installed. `uv_build` is
the build backend, not an installed runtime dependency. This audit does not
claim to describe wheel-native contents for other operating systems.

## Full licence texts and copyright notices

The following texts are copied programmatically from the installed-distribution
licence files read as bytes and decoded explicitly as UTF-8, supplemented by the
identified upstream texts. Only CRLF line endings are normalized to LF;
non-ASCII text is retained. Identical texts are reproduced once with links from
each applicable row. Each Source names the installed distribution and its path
inside site-packages, the Python installation's licence, or an upstream URL.
Locate installed files inside the Python environment selected for Clearwater.
No commercial Qt licence is reproduced or relied on here.

<a id="text-01"></a>

### Python runtime licence and historical notices

Source: `CPython 3.12.13: LICENSE.txt in the Python installation`. SHA-256: `160a384f3520ae891b3197f14ff8b1db1d6a1270873424383045dc025a083908`. UTF-8/LF bytes: 24926.

````text
A. HISTORY OF THE SOFTWARE
==========================

Python was created in the early 1990s by Guido van Rossum at Stichting
Mathematisch Centrum (CWI, see https://www.cwi.nl) in the Netherlands
as a successor of a language called ABC.  Guido remains Python's
principal author, although it includes many contributions from others.

In 1995, Guido continued his work on Python at the Corporation for
National Research Initiatives (CNRI, see https://www.cnri.reston.va.us)
in Reston, Virginia where he released several versions of the
software.

In May 2000, Guido and the Python core development team moved to
BeOpen.com to form the BeOpen PythonLabs team.  In October of the same
year, the PythonLabs team moved to Digital Creations, which became
Zope Corporation.  In 2001, the Python Software Foundation (PSF, see
https://www.python.org/psf/) was formed, a non-profit organization
created specifically to own Python-related Intellectual Property.
Zope Corporation was a sponsoring member of the PSF.

All Python releases are Open Source (see https://opensource.org for
the Open Source Definition).  Historically, most, but not all, Python
releases have also been GPL-compatible; the table below summarizes
the various releases.

    Release         Derived     Year        Owner       GPL-
                    from                                compatible? (1)

    0.9.0 thru 1.2              1991-1995   CWI         yes
    1.3 thru 1.5.2  1.2         1995-1999   CNRI        yes
    1.6             1.5.2       2000        CNRI        no
    2.0             1.6         2000        BeOpen.com  no
    1.6.1           1.6         2001        CNRI        yes (2)
    2.1             2.0+1.6.1   2001        PSF         no
    2.0.1           2.0+1.6.1   2001        PSF         yes
    2.1.1           2.1+2.0.1   2001        PSF         yes
    2.1.2           2.1.1       2002        PSF         yes
    2.1.3           2.1.2       2002        PSF         yes
    2.2 and above   2.1.1       2001-now    PSF         yes

Footnotes:

(1) GPL-compatible doesn't mean that we're distributing Python under
    the GPL.  All Python licenses, unlike the GPL, let you distribute
    a modified version without making your changes open source.  The
    GPL-compatible licenses make it possible to combine Python with
    other software that is released under the GPL; the others don't.

(2) According to Richard Stallman, 1.6.1 is not GPL-compatible,
    because its license has a choice of law clause.  According to
    CNRI, however, Stallman's lawyer has told CNRI's lawyer that 1.6.1
    is "not incompatible" with the GPL.

Thanks to the many outside volunteers who have worked under Guido's
direction to make these releases possible.


B. TERMS AND CONDITIONS FOR ACCESSING OR OTHERWISE USING PYTHON
===============================================================

Python software and documentation are licensed under the
Python Software Foundation License Version 2.

Starting with Python 3.8.6, examples, recipes, and other code in
the documentation are dual licensed under the PSF License Version 2
and the Zero-Clause BSD license.

Some software incorporated into Python is under different licenses.
The licenses are listed with code falling under that license.


PYTHON SOFTWARE FOUNDATION LICENSE VERSION 2
--------------------------------------------

1. This LICENSE AGREEMENT is between the Python Software Foundation
("PSF"), and the Individual or Organization ("Licensee") accessing and
otherwise using this software ("Python") in source or binary form and
its associated documentation.

2. Subject to the terms and conditions of this License Agreement, PSF hereby
grants Licensee a nonexclusive, royalty-free, world-wide license to reproduce,
analyze, test, perform and/or display publicly, prepare derivative works,
distribute, and otherwise use Python alone or in any derivative version,
provided, however, that PSF's License Agreement and PSF's notice of copyright,
i.e., "Copyright (c) 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010,
2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023 Python Software Foundation;
All Rights Reserved" are retained in Python alone or in any derivative version
prepared by Licensee.

3. In the event Licensee prepares a derivative work that is based on
or incorporates Python or any part thereof, and wants to make
the derivative work available to others as provided herein, then
Licensee hereby agrees to include in any such work a brief summary of
the changes made to Python.

4. PSF is making Python available to Licensee on an "AS IS"
basis.  PSF MAKES NO REPRESENTATIONS OR WARRANTIES, EXPRESS OR
IMPLIED.  BY WAY OF EXAMPLE, BUT NOT LIMITATION, PSF MAKES NO AND
DISCLAIMS ANY REPRESENTATION OR WARRANTY OF MERCHANTABILITY OR FITNESS
FOR ANY PARTICULAR PURPOSE OR THAT THE USE OF PYTHON WILL NOT
INFRINGE ANY THIRD PARTY RIGHTS.

5. PSF SHALL NOT BE LIABLE TO LICENSEE OR ANY OTHER USERS OF PYTHON
FOR ANY INCIDENTAL, SPECIAL, OR CONSEQUENTIAL DAMAGES OR LOSS AS
A RESULT OF MODIFYING, DISTRIBUTING, OR OTHERWISE USING PYTHON,
OR ANY DERIVATIVE THEREOF, EVEN IF ADVISED OF THE POSSIBILITY THEREOF.

6. This License Agreement will automatically terminate upon a material
breach of its terms and conditions.

7. Nothing in this License Agreement shall be deemed to create any
relationship of agency, partnership, or joint venture between PSF and
Licensee.  This License Agreement does not grant permission to use PSF
trademarks or trade name in a trademark sense to endorse or promote
products or services of Licensee, or any third party.

8. By copying, installing or otherwise using Python, Licensee
agrees to be bound by the terms and conditions of this License
Agreement.


BEOPEN.COM LICENSE AGREEMENT FOR PYTHON 2.0
-------------------------------------------

BEOPEN PYTHON OPEN SOURCE LICENSE AGREEMENT VERSION 1

1. This LICENSE AGREEMENT is between BeOpen.com ("BeOpen"), having an
office at 160 Saratoga Avenue, Santa Clara, CA 95051, and the
Individual or Organization ("Licensee") accessing and otherwise using
this software in source or binary form and its associated
documentation ("the Software").

2. Subject to the terms and conditions of this BeOpen Python License
Agreement, BeOpen hereby grants Licensee a non-exclusive,
royalty-free, world-wide license to reproduce, analyze, test, perform
and/or display publicly, prepare derivative works, distribute, and
otherwise use the Software alone or in any derivative version,
provided, however, that the BeOpen Python License is retained in the
Software, alone or in any derivative version prepared by Licensee.

3. BeOpen is making the Software available to Licensee on an "AS IS"
basis.  BEOPEN MAKES NO REPRESENTATIONS OR WARRANTIES, EXPRESS OR
IMPLIED.  BY WAY OF EXAMPLE, BUT NOT LIMITATION, BEOPEN MAKES NO AND
DISCLAIMS ANY REPRESENTATION OR WARRANTY OF MERCHANTABILITY OR FITNESS
FOR ANY PARTICULAR PURPOSE OR THAT THE USE OF THE SOFTWARE WILL NOT
INFRINGE ANY THIRD PARTY RIGHTS.

4. BEOPEN SHALL NOT BE LIABLE TO LICENSEE OR ANY OTHER USERS OF THE
SOFTWARE FOR ANY INCIDENTAL, SPECIAL, OR CONSEQUENTIAL DAMAGES OR LOSS
AS A RESULT OF USING, MODIFYING OR DISTRIBUTING THE SOFTWARE, OR ANY
DERIVATIVE THEREOF, EVEN IF ADVISED OF THE POSSIBILITY THEREOF.

5. This License Agreement will automatically terminate upon a material
breach of its terms and conditions.

6. This License Agreement shall be governed by and interpreted in all
respects by the law of the State of California, excluding conflict of
law provisions.  Nothing in this License Agreement shall be deemed to
create any relationship of agency, partnership, or joint venture
between BeOpen and Licensee.  This License Agreement does not grant
permission to use BeOpen trademarks or trade names in a trademark
sense to endorse or promote products or services of Licensee, or any
third party.  As an exception, the "BeOpen Python" logos available at
http://www.pythonlabs.com/logos.html may be used according to the
permissions granted on that web page.

7. By copying, installing or otherwise using the software, Licensee
agrees to be bound by the terms and conditions of this License
Agreement.


CNRI LICENSE AGREEMENT FOR PYTHON 1.6.1
---------------------------------------

1. This LICENSE AGREEMENT is between the Corporation for National
Research Initiatives, having an office at 1895 Preston White Drive,
Reston, VA 20191 ("CNRI"), and the Individual or Organization
("Licensee") accessing and otherwise using Python 1.6.1 software in
source or binary form and its associated documentation.

2. Subject to the terms and conditions of this License Agreement, CNRI
hereby grants Licensee a nonexclusive, royalty-free, world-wide
license to reproduce, analyze, test, perform and/or display publicly,
prepare derivative works, distribute, and otherwise use Python 1.6.1
alone or in any derivative version, provided, however, that CNRI's
License Agreement and CNRI's notice of copyright, i.e., "Copyright (c)
1995-2001 Corporation for National Research Initiatives; All Rights
Reserved" are retained in Python 1.6.1 alone or in any derivative
version prepared by Licensee.  Alternately, in lieu of CNRI's License
Agreement, Licensee may substitute the following text (omitting the
quotes): "Python 1.6.1 is made available subject to the terms and
conditions in CNRI's License Agreement.  This Agreement together with
Python 1.6.1 may be located on the internet using the following
unique, persistent identifier (known as a handle): 1895.22/1013.  This
Agreement may also be obtained from a proxy server on the internet
using the following URL: http://hdl.handle.net/1895.22/1013".

3. In the event Licensee prepares a derivative work that is based on
or incorporates Python 1.6.1 or any part thereof, and wants to make
the derivative work available to others as provided herein, then
Licensee hereby agrees to include in any such work a brief summary of
the changes made to Python 1.6.1.

4. CNRI is making Python 1.6.1 available to Licensee on an "AS IS"
basis.  CNRI MAKES NO REPRESENTATIONS OR WARRANTIES, EXPRESS OR
IMPLIED.  BY WAY OF EXAMPLE, BUT NOT LIMITATION, CNRI MAKES NO AND
DISCLAIMS ANY REPRESENTATION OR WARRANTY OF MERCHANTABILITY OR FITNESS
FOR ANY PARTICULAR PURPOSE OR THAT THE USE OF PYTHON 1.6.1 WILL NOT
INFRINGE ANY THIRD PARTY RIGHTS.

5. CNRI SHALL NOT BE LIABLE TO LICENSEE OR ANY OTHER USERS OF PYTHON
1.6.1 FOR ANY INCIDENTAL, SPECIAL, OR CONSEQUENTIAL DAMAGES OR LOSS AS
A RESULT OF MODIFYING, DISTRIBUTING, OR OTHERWISE USING PYTHON 1.6.1,
OR ANY DERIVATIVE THEREOF, EVEN IF ADVISED OF THE POSSIBILITY THEREOF.

6. This License Agreement will automatically terminate upon a material
breach of its terms and conditions.

7. This License Agreement shall be governed by the federal
intellectual property law of the United States, including without
limitation the federal copyright law, and, to the extent such
U.S. federal law does not apply, by the law of the Commonwealth of
Virginia, excluding Virginia's conflict of law provisions.
Notwithstanding the foregoing, with regard to derivative works based
on Python 1.6.1 that incorporate non-separable material that was
previously distributed under the GNU General Public License (GPL), the
law of the Commonwealth of Virginia shall govern this License
Agreement only as to issues arising under or with respect to
Paragraphs 4, 5, and 7 of this License Agreement.  Nothing in this
License Agreement shall be deemed to create any relationship of
agency, partnership, or joint venture between CNRI and Licensee.  This
License Agreement does not grant permission to use CNRI trademarks or
trade name in a trademark sense to endorse or promote products or
services of Licensee, or any third party.

8. By clicking on the "ACCEPT" button where indicated, or by copying,
installing or otherwise using Python 1.6.1, Licensee agrees to be
bound by the terms and conditions of this License Agreement.

        ACCEPT


CWI LICENSE AGREEMENT FOR PYTHON 0.9.0 THROUGH 1.2
--------------------------------------------------

Copyright (c) 1991 - 1995, Stichting Mathematisch Centrum Amsterdam,
The Netherlands.  All rights reserved.

Permission to use, copy, modify, and distribute this software and its
documentation for any purpose and without fee is hereby granted,
provided that the above copyright notice appear in all copies and that
both that copyright notice and this permission notice appear in
supporting documentation, and that the name of Stichting Mathematisch
Centrum or CWI not be used in advertising or publicity pertaining to
distribution of the software without specific, written prior
permission.

STICHTING MATHEMATISCH CENTRUM DISCLAIMS ALL WARRANTIES WITH REGARD TO
THIS SOFTWARE, INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND
FITNESS, IN NO EVENT SHALL STICHTING MATHEMATISCH CENTRUM BE LIABLE
FOR ANY SPECIAL, INDIRECT OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT
OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

ZERO-CLAUSE BSD LICENSE FOR CODE IN THE PYTHON DOCUMENTATION
----------------------------------------------------------------------

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY
AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT,
INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR
OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
PERFORMANCE OF THIS SOFTWARE.



Additional Conditions for this Windows binary build
---------------------------------------------------

This program is linked with and uses Microsoft Distributable Code,
copyrighted by Microsoft Corporation. The Microsoft Distributable Code
is embedded in each .exe, .dll and .pyd file as a result of running
the code through a linker.

If you further distribute programs that include the Microsoft
Distributable Code, you must comply with the restrictions on
distribution specified by Microsoft. In particular, you must require
distributors and external end users to agree to terms that protect the
Microsoft Distributable Code at least as much as Microsoft's own
requirements for the Distributable Code. See Microsoft's documentation
(included in its developer tools and on its website at microsoft.com)
for specific details.

Redistribution of the Windows binary build of the Python interpreter
complies with this agreement, provided that you do not:

- alter any copyright, trademark or patent notice in Microsoft's
Distributable Code;

- use Microsoft's trademarks in your programs' names or in a way that
suggests your programs come from or are endorsed by Microsoft;

- distribute Microsoft's Distributable Code to run on a platform other
than Microsoft operating systems, run-time technologies or application
platforms; or

- include Microsoft Distributable Code in malicious, deceptive or
unlawful programs.

These restrictions apply only to the Microsoft Distributable Code as
defined above, not to Python itself or any programs running on the
Python interpreter. The redistribution of the Python interpreter and
libraries is governed by the Python Software License included with this
file, or by other licenses as marked.



--------------------------------------------------------------------------

This program, "bzip2", the associated library "libbzip2", and all
documentation, are copyright (C) 1996-2019 Julian R Seward.  All
rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions
are met:

1. Redistributions of source code must retain the above copyright
   notice, this list of conditions and the following disclaimer.

2. The origin of this software must not be misrepresented; you must 
   not claim that you wrote the original software.  If you use this 
   software in a product, an acknowledgment in the product 
   documentation would be appreciated but is not required.

3. Altered source versions must be plainly marked as such, and must
   not be misrepresented as being the original software.

4. The name of the author may not be used to endorse or promote 
   products derived from this software without specific prior written 
   permission.

THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS
OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE
GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

Julian Seward, jseward@acm.org
bzip2/libbzip2 version 1.0.8 of 13 July 2019

--------------------------------------------------------------------------

This software is copyrighted by the Regents of the University of
California, Sun Microsystems, Inc., Scriptics Corporation, ActiveState
Corporation and other parties.  The following terms apply to all files
associated with the software unless explicitly disclaimed in
individual files.

The authors hereby grant permission to use, copy, modify, distribute,
and license this software and its documentation for any purpose, provided
that existing copyright notices are retained in all copies and that this
notice is included verbatim in any distributions. No written agreement,
license, or royalty fee is required for any of the authorized uses.
Modifications to this software may be copyrighted by their authors
and need not follow the licensing terms described here, provided that
the new terms are clearly indicated on the first page of each file where
they apply.

IN NO EVENT SHALL THE AUTHORS OR DISTRIBUTORS BE LIABLE TO ANY PARTY
FOR DIRECT, INDIRECT, SPECIAL, INCIDENTAL, OR CONSEQUENTIAL DAMAGES
ARISING OUT OF THE USE OF THIS SOFTWARE, ITS DOCUMENTATION, OR ANY
DERIVATIVES THEREOF, EVEN IF THE AUTHORS HAVE BEEN ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.

THE AUTHORS AND DISTRIBUTORS SPECIFICALLY DISCLAIM ANY WARRANTIES,
INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE, AND NON-INFRINGEMENT.  THIS SOFTWARE
IS PROVIDED ON AN "AS IS" BASIS, AND THE AUTHORS AND DISTRIBUTORS HAVE
NO OBLIGATION TO PROVIDE MAINTENANCE, SUPPORT, UPDATES, ENHANCEMENTS, OR
MODIFICATIONS.

GOVERNMENT USE: If you are acquiring this software on behalf of the
U.S. government, the Government shall have only "Restricted Rights"
in the software and related documentation as defined in the Federal
Acquisition Regulations (FARs) in Clause 52.227.19 (c) (2).  If you
are acquiring the software on behalf of the Department of Defense, the
software shall be classified as "Commercial Computer Software" and the
Government shall have only "Restricted Rights" as defined in Clause
252.227-7014 (b) (3) of DFARs.  Notwithstanding the foregoing, the
authors grant the U.S. Government and others acting in its behalf
permission to use and distribute the software in accordance with the
terms specified in this license.

This software is copyrighted by the Regents of the University of
California, Sun Microsystems, Inc., Scriptics Corporation, ActiveState
Corporation, Apple Inc. and other parties.  The following terms apply to
all files associated with the software unless explicitly disclaimed in
individual files.

The authors hereby grant permission to use, copy, modify, distribute,
and license this software and its documentation for any purpose, provided
that existing copyright notices are retained in all copies and that this
notice is included verbatim in any distributions. No written agreement,
license, or royalty fee is required for any of the authorized uses.
Modifications to this software may be copyrighted by their authors
and need not follow the licensing terms described here, provided that
the new terms are clearly indicated on the first page of each file where
they apply.

IN NO EVENT SHALL THE AUTHORS OR DISTRIBUTORS BE LIABLE TO ANY PARTY
FOR DIRECT, INDIRECT, SPECIAL, INCIDENTAL, OR CONSEQUENTIAL DAMAGES
ARISING OUT OF THE USE OF THIS SOFTWARE, ITS DOCUMENTATION, OR ANY
DERIVATIVES THEREOF, EVEN IF THE AUTHORS HAVE BEEN ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.

THE AUTHORS AND DISTRIBUTORS SPECIFICALLY DISCLAIM ANY WARRANTIES,
INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE, AND NON-INFRINGEMENT.  THIS SOFTWARE
IS PROVIDED ON AN "AS IS" BASIS, AND THE AUTHORS AND DISTRIBUTORS HAVE
NO OBLIGATION TO PROVIDE MAINTENANCE, SUPPORT, UPDATES, ENHANCEMENTS, OR
MODIFICATIONS.

GOVERNMENT USE: If you are acquiring this software on behalf of the
U.S. government, the Government shall have only "Restricted Rights"
in the software and related documentation as defined in the Federal
Acquisition Regulations (FARs) in Clause 52.227.19 (c) (2).  If you
are acquiring the software on behalf of the Department of Defense, the
software shall be classified as "Commercial Computer Software" and the
Government shall have only "Restricted Rights" as defined in Clause
252.227-7013 (b) (3) of DFARs.  Notwithstanding the foregoing, the
authors grant the U.S. Government and others acting in its behalf
permission to use and distribute the software in accordance with the
terms specified in this license.

Copyright (c) 1993-1999 Ioi Kim Lam.
Copyright (c) 2000-2001 Tix Project Group.
Copyright (c) 2004 ActiveState

This software is copyrighted by the above entities
and other parties.  The following terms apply to all files associated
with the software unless explicitly disclaimed in individual files.

The authors hereby grant permission to use, copy, modify, distribute,
and license this software and its documentation for any purpose, provided
that existing copyright notices are retained in all copies and that this
notice is included verbatim in any distributions. No written agreement,
license, or royalty fee is required for any of the authorized uses.
Modifications to this software may be copyrighted by their authors
and need not follow the licensing terms described here, provided that
the new terms are clearly indicated on the first page of each file where
they apply.

IN NO EVENT SHALL THE AUTHORS OR DISTRIBUTORS BE LIABLE TO ANY PARTY
FOR DIRECT, INDIRECT, SPECIAL, INCIDENTAL, OR CONSEQUENTIAL DAMAGES
ARISING OUT OF THE USE OF THIS SOFTWARE, ITS DOCUMENTATION, OR ANY
DERIVATIVES THEREOF, EVEN IF THE AUTHORS HAVE BEEN ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.

THE AUTHORS AND DISTRIBUTORS SPECIFICALLY DISCLAIM ANY WARRANTIES,
INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE, AND NON-INFRINGEMENT.  THIS SOFTWARE
IS PROVIDED ON AN "AS IS" BASIS, AND THE AUTHORS AND DISTRIBUTORS HAVE
NO OBLIGATION TO PROVIDE MAINTENANCE, SUPPORT, UPDATES, ENHANCEMENTS, OR
MODIFICATIONS.

GOVERNMENT USE: If you are acquiring this software on behalf of the
U.S. government, the Government shall have only "Restricted Rights"
in the software and related documentation as defined in the Federal 
Acquisition Regulations (FARs) in Clause 52.227.19 (c) (2).  If you
are acquiring the software on behalf of the Department of Defense, the
software shall be classified as "Commercial Computer Software" and the
Government shall have only "Restricted Rights" as defined in Clause
252.227-7013 (c) (1) of DFARs.  Notwithstanding the foregoing, the
authors grant the U.S. Government and others acting in its behalf
permission to use and distribute the software in accordance with the
terms specified in this license. 

----------------------------------------------------------------------

Parts of this software are based on the Tcl/Tk software copyrighted by
the Regents of the University of California, Sun Microsystems, Inc.,
and other parties. The original license terms of the Tcl/Tk software
distribution is included in the file docs/license.tcltk.

Parts of this software are based on the HTML Library software
copyrighted by Sun Microsystems, Inc. The original license terms of
the HTML Library software distribution is included in the file
docs/license.html_lib.

````

<a id="text-02"></a>

### cuda-pathfinder: cuda_pathfinder-1.8.3.dist-info/licenses/LICENSE

Source: `cuda-pathfinder 1.8.3: cuda_pathfinder-1.8.3.dist-info/licenses/LICENSE`. SHA-256: `dc94465a4d540f776490e4b7a73d717d09fffbb1d5a7a6eaab47a0ca6f6624ab`. UTF-8/LF bytes: 11436.

````text
Copyright (c) 2024-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.

                                 Apache License
                           Version 2.0, January 2004
                        http://www.apache.org/licenses/

   TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION

   1. Definitions.

      "License" shall mean the terms and conditions for use, reproduction,
      and distribution as defined by Sections 1 through 9 of this document.

      "Licensor" shall mean the copyright owner or entity authorized by
      the copyright owner that is granting the License.

      "Legal Entity" shall mean the union of the acting entity and all
      other entities that control, are controlled by, or are under common
      control with that entity. For the purposes of this definition,
      "control" means (i) the power, direct or indirect, to cause the
      direction or management of such entity, whether by contract or
      otherwise, or (ii) ownership of fifty percent (50%) or more of the
      outstanding shares, or (iii) beneficial ownership of such entity.

      "You" (or "Your") shall mean an individual or Legal Entity
      exercising permissions granted by this License.

      "Source" form shall mean the preferred form for making modifications,
      including but not limited to software source code, documentation
      source, and configuration files.

      "Object" form shall mean any form resulting from mechanical
      transformation or translation of a Source form, including but
      not limited to compiled object code, generated documentation,
      and conversions to other media types.

      "Work" shall mean the work of authorship, whether in Source or
      Object form, made available under the License, as indicated by a
      copyright notice that is included in or attached to the work
      (an example is provided in the Appendix below).

      "Derivative Works" shall mean any work, whether in Source or Object
      form, that is based on (or derived from) the Work and for which the
      editorial revisions, annotations, elaborations, or other modifications
      represent, as a whole, an original work of authorship. For the purposes
      of this License, Derivative Works shall not include works that remain
      separable from, or merely link (or bind by name) to the interfaces of,
      the Work and Derivative Works thereof.

      "Contribution" shall mean any work of authorship, including
      the original version of the Work and any modifications or additions
      to that Work or Derivative Works thereof, that is intentionally
      submitted to Licensor for inclusion in the Work by the copyright owner
      or by an individual or Legal Entity authorized to submit on behalf of
      the copyright owner. For the purposes of this definition, "submitted"
      means any form of electronic, verbal, or written communication sent
      to the Licensor or its representatives, including but not limited to
      communication on electronic mailing lists, source code control systems,
      and issue tracking systems that are managed by, or on behalf of, the
      Licensor for the purpose of discussing and improving the Work, but
      excluding communication that is conspicuously marked or otherwise
      designated in writing by the copyright owner as "Not a Contribution."

      "Contributor" shall mean Licensor and any individual or Legal Entity
      on behalf of whom a Contribution has been received by Licensor and
      subsequently incorporated within the Work.

   2. Grant of Copyright License. Subject to the terms and conditions of
      this License, each Contributor hereby grants to You a perpetual,
      worldwide, non-exclusive, no-charge, royalty-free, irrevocable
      copyright license to reproduce, prepare Derivative Works of,
      publicly display, publicly perform, sublicense, and distribute the
      Work and such Derivative Works in Source or Object form.

   3. Grant of Patent License. Subject to the terms and conditions of
      this License, each Contributor hereby grants to You a perpetual,
      worldwide, non-exclusive, no-charge, royalty-free, irrevocable
      (except as stated in this section) patent license to make, have made,
      use, offer to sell, sell, import, and otherwise transfer the Work,
      where such license applies only to those patent claims licensable
      by such Contributor that are necessarily infringed by their
      Contribution(s) alone or by combination of their Contribution(s)
      with the Work to which such Contribution(s) was submitted. If You
      institute patent litigation against any entity (including a
      cross-claim or counterclaim in a lawsuit) alleging that the Work
      or a Contribution incorporated within the Work constitutes direct
      or contributory patent infringement, then any patent licenses
      granted to You under this License for that Work shall terminate
      as of the date such litigation is filed.

   4. Redistribution. You may reproduce and distribute copies of the
      Work or Derivative Works thereof in any medium, with or without
      modifications, and in Source or Object form, provided that You
      meet the following conditions:

      (a) You must give any other recipients of the Work or
          Derivative Works a copy of this License; and

      (b) You must cause any modified files to carry prominent notices
          stating that You changed the files; and

      (c) You must retain, in the Source form of any Derivative Works
          that You distribute, all copyright, patent, trademark, and
          attribution notices from the Source form of the Work,
          excluding those notices that do not pertain to any part of
          the Derivative Works; and

      (d) If the Work includes a "NOTICE" text file as part of its
          distribution, then any Derivative Works that You distribute must
          include a readable copy of the attribution notices contained
          within such NOTICE file, excluding those notices that do not
          pertain to any part of the Derivative Works, in at least one
          of the following places: within a NOTICE text file distributed
          as part of the Derivative Works; within the Source form or
          documentation, if provided along with the Derivative Works; or,
          within a display generated by the Derivative Works, if and
          wherever such third-party notices normally appear. The contents
          of the NOTICE file are for informational purposes only and
          do not modify the License. You may add Your own attribution
          notices within Derivative Works that You distribute, alongside
          or as an addendum to the NOTICE text from the Work, provided
          that such additional attribution notices cannot be construed
          as modifying the License.

      You may add Your own copyright statement to Your modifications and
      may provide additional or different license terms and conditions
      for use, reproduction, or distribution of Your modifications, or
      for any such Derivative Works as a whole, provided Your use,
      reproduction, and distribution of the Work otherwise complies with
      the conditions stated in this License.

   5. Submission of Contributions. Unless You explicitly state otherwise,
      any Contribution intentionally submitted for inclusion in the Work
      by You to the Licensor shall be under the terms and conditions of
      this License, without any additional terms or conditions.
      Notwithstanding the above, nothing herein shall supersede or modify
      the terms of any separate license agreement you may have executed
      with Licensor regarding such Contributions.

   6. Trademarks. This License does not grant permission to use the trade
      names, trademarks, service marks, or product names of the Licensor,
      except as required for reasonable and customary use in describing the
      origin of the Work and reproducing the content of the NOTICE file.

   7. Disclaimer of Warranty. Unless required by applicable law or
      agreed to in writing, Licensor provides the Work (and each
      Contributor provides its Contributions) on an "AS IS" BASIS,
      WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
      implied, including, without limitation, any warranties or conditions
      of TITLE, NON-INFRINGEMENT, MERCHANTABILITY, or FITNESS FOR A
      PARTICULAR PURPOSE. You are solely responsible for determining the
      appropriateness of using or redistributing the Work and assume any
      risks associated with Your exercise of permissions under this License.

   8. Limitation of Liability. In no event and under no legal theory,
      whether in tort (including negligence), contract, or otherwise,
      unless required by applicable law (such as deliberate and grossly
      negligent acts) or agreed to in writing, shall any Contributor be
      liable to You for damages, including any direct, indirect, special,
      incidental, or consequential damages of any character arising as a
      result of this License or out of the use or inability to use the
      Work (including but not limited to damages for loss of goodwill,
      work stoppage, computer failure or malfunction, or any and all
      other commercial damages or losses), even if such Contributor
      has been advised of the possibility of such damages.

   9. Accepting Warranty or Additional Liability. While redistributing
      the Work or Derivative Works thereof, You may choose to offer,
      and charge a fee for, acceptance of support, warranty, indemnity,
      or other liability obligations and/or rights consistent with this
      License. However, in accepting such obligations, You may act only
      on Your own behalf and on Your sole responsibility, not on behalf
      of any other Contributor, and only if You agree to indemnify,
      defend, and hold each Contributor harmless for any liability
      incurred by, or claims asserted against, such Contributor by reason
      of your accepting any such warranty or additional liability.

   END OF TERMS AND CONDITIONS

   APPENDIX: How to apply the Apache License to your work.

      To apply the Apache License to your work, attach the following
      boilerplate notice, with the fields enclosed by brackets "[]"
      replaced with your own identifying information. (Don't include
      the brackets!)  The text should be enclosed in the appropriate
      comment syntax for the file format. We also recommend that a
      file or class name and description of purpose be included on the
      same "printed page" as the copyright notice for easier
      identification within third-party archives.

   Copyright [yyyy] [name of copyright owner]

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
````

<a id="text-03"></a>

### cupy-cuda12x: cupy/_core/include/cupy/_cccl/LICENSE

Source: `cupy-cuda12x 14.2.0: cupy/_core/include/cupy/_cccl/LICENSE`. SHA-256: `f96f51edda77fb9897de29d924d615e6bd153f4969db85fc6b7a22d7a624631e`. UTF-8/LF bytes: 22452.

````text
==============================================================================
Thrust is under the Apache Licence v2.0, with some specific exceptions listed below
libcu++ is under the Apache License v2.0 with LLVM Exceptions:
==============================================================================
                                Apache License
                           Version 2.0, January 2004
                        http://www.apache.org/licenses/

    TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION

    1. Definitions.

      "License" shall mean the terms and conditions for use, reproduction,
      and distribution as defined by Sections 1 through 9 of this document.

      "Licensor" shall mean the copyright owner or entity authorized by
      the copyright owner that is granting the License.

      "Legal Entity" shall mean the union of the acting entity and all
      other entities that control, are controlled by, or are under common
      control with that entity. For the purposes of this definition,
      "control" means (i) the power, direct or indirect, to cause the
      direction or management of such entity, whether by contract or
      otherwise, or (ii) ownership of fifty percent (50%) or more of the
      outstanding shares, or (iii) beneficial ownership of such entity.

      "You" (or "Your") shall mean an individual or Legal Entity
      exercising permissions granted by this License.

      "Source" form shall mean the preferred form for making modifications,
      including but not limited to software source code, documentation
      source, and configuration files.

      "Object" form shall mean any form resulting from mechanical
      transformation or translation of a Source form, including but
      not limited to compiled object code, generated documentation,
      and conversions to other media types.

      "Work" shall mean the work of authorship, whether in Source or
      Object form, made available under the License, as indicated by a
      copyright notice that is included in or attached to the work
      (an example is provided in the Appendix below).

      "Derivative Works" shall mean any work, whether in Source or Object
      form, that is based on (or derived from) the Work and for which the
      editorial revisions, annotations, elaborations, or other modifications
      represent, as a whole, an original work of authorship. For the purposes
      of this License, Derivative Works shall not include works that remain
      separable from, or merely link (or bind by name) to the interfaces of,
      the Work and Derivative Works thereof.

      "Contribution" shall mean any work of authorship, including
      the original version of the Work and any modifications or additions
      to that Work or Derivative Works thereof, that is intentionally
      submitted to Licensor for inclusion in the Work by the copyright owner
      or by an individual or Legal Entity authorized to submit on behalf of
      the copyright owner. For the purposes of this definition, "submitted"
      means any form of electronic, verbal, or written communication sent
      to the Licensor or its representatives, including but not limited to
      communication on electronic mailing lists, source code control systems,
      and issue tracking systems that are managed by, or on behalf of, the
      Licensor for the purpose of discussing and improving the Work, but
      excluding communication that is conspicuously marked or otherwise
      designated in writing by the copyright owner as "Not a Contribution."

      "Contributor" shall mean Licensor and any individual or Legal Entity
      on behalf of whom a Contribution has been received by Licensor and
      subsequently incorporated within the Work.

    2. Grant of Copyright License. Subject to the terms and conditions of
      this License, each Contributor hereby grants to You a perpetual,
      worldwide, non-exclusive, no-charge, royalty-free, irrevocable
      copyright license to reproduce, prepare Derivative Works of,
      publicly display, publicly perform, sublicense, and distribute the
      Work and such Derivative Works in Source or Object form.

    3. Grant of Patent License. Subject to the terms and conditions of
      this License, each Contributor hereby grants to You a perpetual,
      worldwide, non-exclusive, no-charge, royalty-free, irrevocable
      (except as stated in this section) patent license to make, have made,
      use, offer to sell, sell, import, and otherwise transfer the Work,
      where such license applies only to those patent claims licensable
      by such Contributor that are necessarily infringed by their
      Contribution(s) alone or by combination of their Contribution(s)
      with the Work to which such Contribution(s) was submitted. If You
      institute patent litigation against any entity (including a
      cross-claim or counterclaim in a lawsuit) alleging that the Work
      or a Contribution incorporated within the Work constitutes direct
      or contributory patent infringement, then any patent licenses
      granted to You under this License for that Work shall terminate
      as of the date such litigation is filed.

    4. Redistribution. You may reproduce and distribute copies of the
      Work or Derivative Works thereof in any medium, with or without
      modifications, and in Source or Object form, provided that You
      meet the following conditions:

      (a) You must give any other recipients of the Work or
          Derivative Works a copy of this License; and

      (b) You must cause any modified files to carry prominent notices
          stating that You changed the files; and

      (c) You must retain, in the Source form of any Derivative Works
          that You distribute, all copyright, patent, trademark, and
          attribution notices from the Source form of the Work,
          excluding those notices that do not pertain to any part of
          the Derivative Works; and

      (d) If the Work includes a "NOTICE" text file as part of its
          distribution, then any Derivative Works that You distribute must
          include a readable copy of the attribution notices contained
          within such NOTICE file, excluding those notices that do not
          pertain to any part of the Derivative Works, in at least one
          of the following places: within a NOTICE text file distributed
          as part of the Derivative Works; within the Source form or
          documentation, if provided along with the Derivative Works; or,
          within a display generated by the Derivative Works, if and
          wherever such third-party notices normally appear. The contents
          of the NOTICE file are for informational purposes only and
          do not modify the License. You may add Your own attribution
          notices within Derivative Works that You distribute, alongside
          or as an addendum to the NOTICE text from the Work, provided
          that such additional attribution notices cannot be construed
          as modifying the License.

      You may add Your own copyright statement to Your modifications and
      may provide additional or different license terms and conditions
      for use, reproduction, or distribution of Your modifications, or
      for any such Derivative Works as a whole, provided Your use,
      reproduction, and distribution of the Work otherwise complies with
      the conditions stated in this License.

    5. Submission of Contributions. Unless You explicitly state otherwise,
      any Contribution intentionally submitted for inclusion in the Work
      by You to the Licensor shall be under the terms and conditions of
      this License, without any additional terms or conditions.
      Notwithstanding the above, nothing herein shall supersede or modify
      the terms of any separate license agreement you may have executed
      with Licensor regarding such Contributions.

    6. Trademarks. This License does not grant permission to use the trade
      names, trademarks, service marks, or product names of the Licensor,
      except as required for reasonable and customary use in describing the
      origin of the Work and reproducing the content of the NOTICE file.

    7. Disclaimer of Warranty. Unless required by applicable law or
      agreed to in writing, Licensor provides the Work (and each
      Contributor provides its Contributions) on an "AS IS" BASIS,
      WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
      implied, including, without limitation, any warranties or conditions
      of TITLE, NON-INFRINGEMENT, MERCHANTABILITY, or FITNESS FOR A
      PARTICULAR PURPOSE. You are solely responsible for determining the
      appropriateness of using or redistributing the Work and assume any
      risks associated with Your exercise of permissions under this License.

    8. Limitation of Liability. In no event and under no legal theory,
      whether in tort (including negligence), contract, or otherwise,
      unless required by applicable law (such as deliberate and grossly
      negligent acts) or agreed to in writing, shall any Contributor be
      liable to You for damages, including any direct, indirect, special,
      incidental, or consequential damages of any character arising as a
      result of this License or out of the use or inability to use the
      Work (including but not limited to damages for loss of goodwill,
      work stoppage, computer failure or malfunction, or any and all
      other commercial damages or losses), even if such Contributor
      has been advised of the possibility of such damages.

    9. Accepting Warranty or Additional Liability. While redistributing
      the Work or Derivative Works thereof, You may choose to offer,
      and charge a fee for, acceptance of support, warranty, indemnity,
      or other liability obligations and/or rights consistent with this
      License. However, in accepting such obligations, You may act only
      on Your own behalf and on Your sole responsibility, not on behalf
      of any other Contributor, and only if You agree to indemnify,
      defend, and hold each Contributor harmless for any liability
      incurred by, or claims asserted against, such Contributor by reason
      of your accepting any such warranty or additional liability.

    END OF TERMS AND CONDITIONS

    APPENDIX: How to apply the Apache License to your work.

      To apply the Apache License to your work, attach the following
      boilerplate notice, with the fields enclosed by brackets "[]"
      replaced with your own identifying information. (Don't include
      the brackets!)  The text should be enclosed in the appropriate
      comment syntax for the file format. We also recommend that a
      file or class name and description of purpose be included on the
      same "printed page" as the copyright notice for easier
      identification within third-party archives.

    Copyright [yyyy] [name of copyright owner]

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.


==============================================================================
Legacy LLVM License (https://llvm.org/docs/DeveloperPolicy.html#legacy):
==============================================================================
---- LLVM Exceptions to the Apache 2.0 License ----

As an exception, if, as a result of your compiling your source code, portions
of this Software are embedded into an Object form of such source code, you
may redistribute such embedded portions in such Object form without complying
with the conditions of Sections 4(a), 4(b) and 4(d) of the License.

In addition, if you combine or link compiled forms of this Software with
software that is licensed under the GPLv2 ("Combined Software") and if a
court of competent jurisdiction determines that the patent provision (Section
3), the indemnity provision (Section 9) or other Section of the License
conflicts with the conditions of the GPLv2, you may retroactively and
prospectively choose to deem waived or otherwise exclude such Section(s) of
the License, but only in their entirety and only with respect to the Combined
Software.

==============================================================================
Software from third parties included in the LLVM Project:
==============================================================================
The LLVM Project contains third party software which is under different license
terms. All such code will be identified clearly using at least one of two
mechanisms:
1) It will be in a separate directory tree with its own `LICENSE.txt` or
   `LICENSE` file at the top containing the specific license and restrictions
   which apply to that software, or
2) It will contain specific license and restriction terms at the top of every
   file.

==============================================================================
Legacy LLVM License (https://llvm.org/docs/DeveloperPolicy.html#legacy):
==============================================================================

The libc++ library is dual licensed under both the University of Illinois
"BSD-Like" license and the MIT license.  As a user of this code you may choose
to use it under either license.  As a contributor, you agree to allow your code
to be used under both.

Full text of the relevant licenses is included below.

==============================================================================

University of Illinois/NCSA
Open Source License

Copyright (c) 2009-2019 by the contributors listed in CREDITS.TXT

All rights reserved.

Developed by:

    LLVM Team

    University of Illinois at Urbana-Champaign

    http://llvm.org

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal with
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

    * Redistributions of source code must retain the above copyright notice,
      this list of conditions and the following disclaimers.

    * Redistributions in binary form must reproduce the above copyright notice,
      this list of conditions and the following disclaimers in the
      documentation and/or other materials provided with the distribution.

    * Neither the names of the LLVM Team, University of Illinois at
      Urbana-Champaign, nor the names of its contributors may be used to
      endorse or promote products derived from this Software without specific
      prior written permission.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL THE
CONTRIBUTORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS WITH THE
SOFTWARE.

==============================================================================

Copyright (c) 2009-2014 by the contributors listed in CREDITS.TXT

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

================================================================================
Some portions of Thrust may be licensed under other compatible open-source
licenses. Any divergence from the Apache 2 license will be noted in the source
code where applicable.
Portions under other terms include, but are not limited to:
================================================================================

Various C++ utility classes in Thrust are based on the Boost Iterator, Tuple,
System, and Random Number libraries, which are provided under the Boost Software
License:

    Boost Software License - Version 1.0 - August 17th, 2003

    Permission is hereby granted, free of charge, to any person or organization
    obtaining a copy of the software and accompanying documentation covered by
    this license (the "Software") to use, reproduce, display, distribute,
    execute, and transmit the Software, and to prepare derivative works of the
    Software, and to permit third-parties to whom the Software is furnished to
    do so, all subject to the following:

    The copyright notices in the Software and this entire statement, including
    the above license grant, this restriction and the following disclaimer,
    must be included in all copies of the Software, in whole or in part, and
    all derivative works of the Software, unless such copies or derivative
    works are solely in the form of machine-executable object code generated by
    a source language processor.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE, TITLE AND NON-INFRINGEMENT. IN NO EVENT
    SHALL THE COPYRIGHT HOLDERS OR ANYONE DISTRIBUTING THE SOFTWARE BE LIABLE
    FOR ANY DAMAGES OR OTHER LIABILITY, WHETHER IN CONTRACT, TORT OR OTHERWISE,
    ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
    DEALINGS IN THE SOFTWARE.

================================================================================

Portions of the thrust::complex implementation are derived from FreeBSD with the
following terms:

================================================================================


    Redistribution and use in source and binary forms, with or without
    modification, are permitted provided that the following conditions
    are met:

    1. Redistributions of source code must retain the above copyright
       notice[1] unmodified, this list of conditions, and the following
       disclaimer.
    2. Redistributions in binary form must reproduce the above copyright
       notice, this list of conditions and the following disclaimer in the
       documentation and/or other materials provided with the distribution.

    THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
    IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
    OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
    IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
    INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
    NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
    DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
    THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
    (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
    THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

[1] Individual copyright notices from the original authors are included in
    the relevant source files.

==============================================================================
CUB's source code is released under the BSD 3-Clause license:
==============================================================================
Copyright (c) 2010-2011, Duane Merrill.  All rights reserved.
Copyright (c) 2011-2023, NVIDIA CORPORATION.  All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
   *  Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
   *  Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
   *  Neither the name of the NVIDIA CORPORATION nor the
      names of its contributors may be used to endorse or promote products
      derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL NVIDIA CORPORATION BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
````

<a id="text-04"></a>

### cupy-cuda12x: cupy/_core/include/cupy/_dlpack/LICENSE

Source: `cupy-cuda12x 14.2.0: cupy/_core/include/cupy/_dlpack/LICENSE`. SHA-256: `3e8f6bc39276a586d60c8c5aaece2ff989262181cf2b3d2a128db58f97a9300c`. UTF-8/LF bytes: 11345.

````text
                                 Apache License
                           Version 2.0, January 2004
                        http://www.apache.org/licenses/

   TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION

   1. Definitions.

      "License" shall mean the terms and conditions for use, reproduction,
      and distribution as defined by Sections 1 through 9 of this document.

      "Licensor" shall mean the copyright owner or entity authorized by
      the copyright owner that is granting the License.

      "Legal Entity" shall mean the union of the acting entity and all
      other entities that control, are controlled by, or are under common
      control with that entity. For the purposes of this definition,
      "control" means (i) the power, direct or indirect, to cause the
      direction or management of such entity, whether by contract or
      otherwise, or (ii) ownership of fifty percent (50%) or more of the
      outstanding shares, or (iii) beneficial ownership of such entity.

      "You" (or "Your") shall mean an individual or Legal Entity
      exercising permissions granted by this License.

      "Source" form shall mean the preferred form for making modifications,
      including but not limited to software source code, documentation
      source, and configuration files.

      "Object" form shall mean any form resulting from mechanical
      transformation or translation of a Source form, including but
      not limited to compiled object code, generated documentation,
      and conversions to other media types.

      "Work" shall mean the work of authorship, whether in Source or
      Object form, made available under the License, as indicated by a
      copyright notice that is included in or attached to the work
      (an example is provided in the Appendix below).

      "Derivative Works" shall mean any work, whether in Source or Object
      form, that is based on (or derived from) the Work and for which the
      editorial revisions, annotations, elaborations, or other modifications
      represent, as a whole, an original work of authorship. For the purposes
      of this License, Derivative Works shall not include works that remain
      separable from, or merely link (or bind by name) to the interfaces of,
      the Work and Derivative Works thereof.

      "Contribution" shall mean any work of authorship, including
      the original version of the Work and any modifications or additions
      to that Work or Derivative Works thereof, that is intentionally
      submitted to Licensor for inclusion in the Work by the copyright owner
      or by an individual or Legal Entity authorized to submit on behalf of
      the copyright owner. For the purposes of this definition, "submitted"
      means any form of electronic, verbal, or written communication sent
      to the Licensor or its representatives, including but not limited to
      communication on electronic mailing lists, source code control systems,
      and issue tracking systems that are managed by, or on behalf of, the
      Licensor for the purpose of discussing and improving the Work, but
      excluding communication that is conspicuously marked or otherwise
      designated in writing by the copyright owner as "Not a Contribution."

      "Contributor" shall mean Licensor and any individual or Legal Entity
      on behalf of whom a Contribution has been received by Licensor and
      subsequently incorporated within the Work.

   2. Grant of Copyright License. Subject to the terms and conditions of
      this License, each Contributor hereby grants to You a perpetual,
      worldwide, non-exclusive, no-charge, royalty-free, irrevocable
      copyright license to reproduce, prepare Derivative Works of,
      publicly display, publicly perform, sublicense, and distribute the
      Work and such Derivative Works in Source or Object form.

   3. Grant of Patent License. Subject to the terms and conditions of
      this License, each Contributor hereby grants to You a perpetual,
      worldwide, non-exclusive, no-charge, royalty-free, irrevocable
      (except as stated in this section) patent license to make, have made,
      use, offer to sell, sell, import, and otherwise transfer the Work,
      where such license applies only to those patent claims licensable
      by such Contributor that are necessarily infringed by their
      Contribution(s) alone or by combination of their Contribution(s)
      with the Work to which such Contribution(s) was submitted. If You
      institute patent litigation against any entity (including a
      cross-claim or counterclaim in a lawsuit) alleging that the Work
      or a Contribution incorporated within the Work constitutes direct
      or contributory patent infringement, then any patent licenses
      granted to You under this License for that Work shall terminate
      as of the date such litigation is filed.

   4. Redistribution. You may reproduce and distribute copies of the
      Work or Derivative Works thereof in any medium, with or without
      modifications, and in Source or Object form, provided that You
      meet the following conditions:

      (a) You must give any other recipients of the Work or
          Derivative Works a copy of this License; and

      (b) You must cause any modified files to carry prominent notices
          stating that You changed the files; and

      (c) You must retain, in the Source form of any Derivative Works
          that You distribute, all copyright, patent, trademark, and
          attribution notices from the Source form of the Work,
          excluding those notices that do not pertain to any part of
          the Derivative Works; and

      (d) If the Work includes a "NOTICE" text file as part of its
          distribution, then any Derivative Works that You distribute must
          include a readable copy of the attribution notices contained
          within such NOTICE file, excluding those notices that do not
          pertain to any part of the Derivative Works, in at least one
          of the following places: within a NOTICE text file distributed
          as part of the Derivative Works; within the Source form or
          documentation, if provided along with the Derivative Works; or,
          within a display generated by the Derivative Works, if and
          wherever such third-party notices normally appear. The contents
          of the NOTICE file are for informational purposes only and
          do not modify the License. You may add Your own attribution
          notices within Derivative Works that You distribute, alongside
          or as an addendum to the NOTICE text from the Work, provided
          that such additional attribution notices cannot be construed
          as modifying the License.

      You may add Your own copyright statement to Your modifications and
      may provide additional or different license terms and conditions
      for use, reproduction, or distribution of Your modifications, or
      for any such Derivative Works as a whole, provided Your use,
      reproduction, and distribution of the Work otherwise complies with
      the conditions stated in this License.

   5. Submission of Contributions. Unless You explicitly state otherwise,
      any Contribution intentionally submitted for inclusion in the Work
      by You to the Licensor shall be under the terms and conditions of
      this License, without any additional terms or conditions.
      Notwithstanding the above, nothing herein shall supersede or modify
      the terms of any separate license agreement you may have executed
      with Licensor regarding such Contributions.

   6. Trademarks. This License does not grant permission to use the trade
      names, trademarks, service marks, or product names of the Licensor,
      except as required for reasonable and customary use in describing the
      origin of the Work and reproducing the content of the NOTICE file.

   7. Disclaimer of Warranty. Unless required by applicable law or
      agreed to in writing, Licensor provides the Work (and each
      Contributor provides its Contributions) on an "AS IS" BASIS,
      WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
      implied, including, without limitation, any warranties or conditions
      of TITLE, NON-INFRINGEMENT, MERCHANTABILITY, or FITNESS FOR A
      PARTICULAR PURPOSE. You are solely responsible for determining the
      appropriateness of using or redistributing the Work and assume any
      risks associated with Your exercise of permissions under this License.

   8. Limitation of Liability. In no event and under no legal theory,
      whether in tort (including negligence), contract, or otherwise,
      unless required by applicable law (such as deliberate and grossly
      negligent acts) or agreed to in writing, shall any Contributor be
      liable to You for damages, including any direct, indirect, special,
      incidental, or consequential damages of any character arising as a
      result of this License or out of the use or inability to use the
      Work (including but not limited to damages for loss of goodwill,
      work stoppage, computer failure or malfunction, or any and all
      other commercial damages or losses), even if such Contributor
      has been advised of the possibility of such damages.

   9. Accepting Warranty or Additional Liability. While redistributing
      the Work or Derivative Works thereof, You may choose to offer,
      and charge a fee for, acceptance of support, warranty, indemnity,
      or other liability obligations and/or rights consistent with this
      License. However, in accepting such obligations, You may act only
      on Your own behalf and on Your sole responsibility, not on behalf
      of any other Contributor, and only if You agree to indemnify,
      defend, and hold each Contributor harmless for any liability
      incurred by, or claims asserted against, such Contributor by reason
      of your accepting any such warranty or additional liability.

   END OF TERMS AND CONDITIONS

   APPENDIX: How to apply the Apache License to your work.

      To apply the Apache License to your work, attach the following
      boilerplate notice, with the fields enclosed by brackets "{}"
      replaced with your own identifying information. (Don't include
      the brackets!)  The text should be enclosed in the appropriate
      comment syntax for the file format. We also recommend that a
      file or class name and description of purpose be included on the
      same "printed page" as the copyright notice for easier
      identification within third-party archives.

   Copyright 2017 by Contributors

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
````

<a id="text-05"></a>

### cupy-cuda12x: cupy/_core/include/cupy/_jitify/LICENSE

Source: `cupy-cuda12x 14.2.0: cupy/_core/include/cupy/_jitify/LICENSE`. SHA-256: `2a6e7492dac91efeb0ed31317870153e49123c30727e9dc354f51c8d50732091`. UTF-8/LF bytes: 1523.

````text
BSD 3-Clause License

Copyright (c) 2017-2020, NVIDIA Corporation
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

* Neither the name of the copyright holder nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
````

<a id="text-06"></a>

### cupy-cuda12x: cupy_cuda12x-14.2.0.dist-info/licenses/LICENSE

Source: `cupy-cuda12x 14.2.0: cupy_cuda12x-14.2.0.dist-info/licenses/LICENSE`. SHA-256: `231c4efc36295f733f4d278eb254f592cf9d1955a7503971fc47af4136c7442b`. UTF-8/LF bytes: 1118.

````text
Copyright (c) 2015 Preferred Infrastructure, Inc.
Copyright (c) 2015 Preferred Networks, Inc.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
````

<a id="text-07"></a>

### cupy-cuda12x: cupy_cuda12x-14.2.0.dist-info/licenses/docs/source/license.rst

Source: `cupy-cuda12x 14.2.0: cupy_cuda12x-14.2.0.dist-info/licenses/docs/source/license.rst`. SHA-256: `918713532257491ac8ddcda50b1e8302425456b13b3176f2dcbd454bdfc9c8ab`. UTF-8/LF bytes: 5723.

````text
License
=======

Copyright (c) 2015 Preferred Infrastructure, Inc.

Copyright (c) 2015 Preferred Networks, Inc.


Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.


NumPy
-----

The CuPy is designed based on NumPy's API.
CuPy's source code and documents contain the original NumPy ones.


Copyright (c) 2005-2016, NumPy Developers.

All rights reserved.


Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

* Redistributions of source code must retain the above copyright
  notice, this list of conditions and the following disclaimer.
* Redistributions in binary form must reproduce the above
  copyright notice, this list of conditions and the following
  disclaimer in the documentation and/or other materials provided
  with the distribution.
* Neither the name of the NumPy Developers nor the names of any
  contributors may be used to endorse or promote products derived
  from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


SciPy
-----

The CuPy is designed based on SciPy's API.
CuPy's source code and documents contain the original SciPy ones.


Copyright (c) 2001, 2002 Enthought, Inc.

All rights reserved.


Copyright (c) 2003-2016 SciPy Developers.

All rights reserved.


Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

a. Redistributions of source code must retain the above copyright notice,
   this list of conditions and the following disclaimer.
b. Redistributions in binary form must reproduce the above copyright
   notice, this list of conditions and the following disclaimer in the
   documentation and/or other materials provided with the distribution.
c. Neither the name of Enthought nor the names of the SciPy Developers
   may be used to endorse or promote products derived from this software
   without specific prior written permission.


THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDERS OR CONTRIBUTORS
BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
THE POSSIBILITY OF SUCH DAMAGE.


cuSignal
--------

Part of CuPy's signal processing routines and their documentation are ported from `RAPIDS cuSignal <https://github.com/rapidsai/cusignal>`_.


Copyright (c) 2019-2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
````

<a id="text-08"></a>

### cupy-cuda12x: cupyx/scipy/ndimage/cuda/LICENSE

Source: `cupy-cuda12x 14.2.0: cupyx/scipy/ndimage/cuda/LICENSE`. SHA-256: `a509b83d419cbe3020ec4d69db6fab449ef9e10f9048920ee7d7551a7e163d4c`. UTF-8/LF bytes: 1110.

````text
MIT License

Copyright (c) 2019 School of Computing, National University of Singapore

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
````

<a id="text-09"></a>

### numpy: numpy-2.5.4.dist-info/licenses/LICENSE.txt

Source: `numpy 2.5.4: numpy-2.5.4.dist-info/licenses/LICENSE.txt`. SHA-256: `dc97d59562c75c04557f1e9a68f3eae326699eb119d569cd4ed6a4eafe5f9abb`. UTF-8/LF bytes: 45801.

````text
Copyright (c) 2005-2025, NumPy Developers.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

    * Redistributions of source code must retain the above copyright
       notice, this list of conditions and the following disclaimer.

    * Redistributions in binary form must reproduce the above
       copyright notice, this list of conditions and the following
       disclaimer in the documentation and/or other materials provided
       with the distribution.

    * Neither the name of the NumPy Developers nor the names of any
       contributors may be used to endorse or promote products derived
       from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

----


----

This binary distribution of NumPy also bundles the following software:


Name: OpenBLAS
Files: numpy.libs\libscipy_openblas*.dll
Description: bundled as a dynamically linked library
Availability: https://github.com/OpenMathLib/OpenBLAS/
License: BSD-3-Clause
  Copyright (c) 2011-2014, The OpenBLAS Project
  All rights reserved.

  Redistribution and use in source and binary forms, with or without
  modification, are permitted provided that the following conditions are
  met:

     1. Redistributions of source code must retain the above copyright
        notice, this list of conditions and the following disclaimer.

     2. Redistributions in binary form must reproduce the above copyright
        notice, this list of conditions and the following disclaimer in
        the documentation and/or other materials provided with the
        distribution.
     3. Neither the name of the OpenBLAS project nor the names of
        its contributors may be used to endorse or promote products
        derived from this software without specific prior written
        permission.

  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
  AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
  ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
  LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
  DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
  SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
  CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
  OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
  USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


Name: LAPACK
Files: numpy.libs\libscipy_openblas*.dll
Description: bundled in OpenBLAS
Availability: https://github.com/OpenMathLib/OpenBLAS/
License: BSD-3-Clause-Open-MPI
  Copyright (c) 1992-2013 The University of Tennessee and The University
                          of Tennessee Research Foundation.  All rights
                          reserved.
  Copyright (c) 2000-2013 The University of California Berkeley. All
                          rights reserved.
  Copyright (c) 2006-2013 The University of Colorado Denver.  All rights
                          reserved.

  $COPYRIGHT$

  Additional copyrights may follow

  $HEADER$

  Redistribution and use in source and binary forms, with or without
  modification, are permitted provided that the following conditions are
  met:

  - Redistributions of source code must retain the above copyright
    notice, this list of conditions and the following disclaimer.

  - Redistributions in binary form must reproduce the above copyright
    notice, this list of conditions and the following disclaimer listed
    in this license in the documentation and/or other materials
    provided with the distribution.

  - Neither the name of the copyright holders nor the names of its
    contributors may be used to endorse or promote products derived from
    this software without specific prior written permission.

  The copyright holders provide no reassurances that the source code
  provided does not infringe any patent, copyright, or any other
  intellectual property rights of third parties.  The copyright holders
  disclaim any liability to any recipient for claims brought against
  recipient by any third party for infringement of that parties
  intellectual property rights.

  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
  "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
  LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
  A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
  OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
  SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
  LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
  DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
  THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
  OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


Name: GCC runtime library
Files: numpy.libs\libscipy_openblas*.dll
Description: statically linked to files compiled with gcc
Availability: https://gcc.gnu.org/git/?p=gcc.git;a=tree;f=libgfortran
License: GPL-3.0-or-later WITH GCC-exception-3.1
  Copyright (C) 2002-2017 Free Software Foundation, Inc.

  Libgfortran is free software; you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation; either version 3, or (at your option)
  any later version.

  Libgfortran is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  Under Section 7 of GPL version 3, you are granted additional
  permissions described in the GCC Runtime Library Exception, version
  3.1, as published by the Free Software Foundation.

  You should have received a copy of the GNU General Public License and
  a copy of the GCC Runtime Library Exception along with this program;
  see the files COPYING3 and COPYING.RUNTIME respectively.  If not, see
  <http://www.gnu.org/licenses/>.

----

Full text of license texts referred to above follows (that they are
listed below does not necessarily imply the conditions apply to the
present binary release):

----

GCC RUNTIME LIBRARY EXCEPTION

Version 3.1, 31 March 2009

Copyright (C) 2009 Free Software Foundation, Inc. <https://fsf.org/>

Everyone is permitted to copy and distribute verbatim copies of this
license document, but changing it is not allowed.

This GCC Runtime Library Exception ("Exception") is an additional
permission under section 7 of the GNU General Public License, version
3 ("GPLv3"). It applies to a given file (the "Runtime Library") that
bears a notice placed by the copyright holder of the file stating that
the file is governed by GPLv3 along with this Exception.

When you use GCC to compile a program, GCC may combine portions of
certain GCC header files and runtime libraries with the compiled
program. The purpose of this Exception is to allow compilation of
non-GPL (including proprietary) programs to use, in this way, the
header files and runtime libraries covered by this Exception.

0. Definitions.

A file is an "Independent Module" if it either requires the Runtime
Library for execution after a Compilation Process, or makes use of an
interface provided by the Runtime Library, but is not otherwise based
on the Runtime Library.

"GCC" means a version of the GNU Compiler Collection, with or without
modifications, governed by version 3 (or a specified later version) of
the GNU General Public License (GPL) with the option of using any
subsequent versions published by the FSF.

"GPL-compatible Software" is software whose conditions of propagation,
modification and use would permit combination with GCC in accord with
the license of GCC.

"Target Code" refers to output from any compiler for a real or virtual
target processor architecture, in executable form or suitable for
input to an assembler, loader, linker and/or execution
phase. Notwithstanding that, Target Code does not include data in any
format that is used as a compiler intermediate representation, or used
for producing a compiler intermediate representation.

The "Compilation Process" transforms code entirely represented in
non-intermediate languages designed for human-written code, and/or in
Java Virtual Machine byte code, into Target Code. Thus, for example,
use of source code generators and preprocessors need not be considered
part of the Compilation Process, since the Compilation Process can be
understood as starting with the output of the generators or
preprocessors.

A Compilation Process is "Eligible" if it is done using GCC, alone or
with other GPL-compatible software, or if it is done without using any
work based on GCC. For example, using non-GPL-compatible Software to
optimize any GCC intermediate representations would not qualify as an
Eligible Compilation Process.

1. Grant of Additional Permission.

You have permission to propagate a work of Target Code formed by
combining the Runtime Library with Independent Modules, even if such
propagation would otherwise violate the terms of GPLv3, provided that
all Target Code was generated by Eligible Compilation Processes. You
may then convey such a combination under terms of your choice,
consistent with the licensing of the Independent Modules.

2. No Weakening of GCC Copyleft.

The availability of this Exception does not imply any general
presumption that third-party software is unaffected by the copyleft
requirements of the license of GCC.

----

                    GNU GENERAL PUBLIC LICENSE
                       Version 3, 29 June 2007

 Copyright (C) 2007 Free Software Foundation, Inc. <https://fsf.org/>
 Everyone is permitted to copy and distribute verbatim copies
 of this license document, but changing it is not allowed.

                            Preamble

  The GNU General Public License is a free, copyleft license for
software and other kinds of works.

  The licenses for most software and other practical works are designed
to take away your freedom to share and change the works.  By contrast,
the GNU General Public License is intended to guarantee your freedom to
share and change all versions of a program--to make sure it remains free
software for all its users.  We, the Free Software Foundation, use the
GNU General Public License for most of our software; it applies also to
any other work released this way by its authors.  You can apply it to
your programs, too.

  When we speak of free software, we are referring to freedom, not
price.  Our General Public Licenses are designed to make sure that you
have the freedom to distribute copies of free software (and charge for
them if you wish), that you receive source code or can get it if you
want it, that you can change the software or use pieces of it in new
free programs, and that you know you can do these things.

  To protect your rights, we need to prevent others from denying you
these rights or asking you to surrender the rights.  Therefore, you have
certain responsibilities if you distribute copies of the software, or if
you modify it: responsibilities to respect the freedom of others.

  For example, if you distribute copies of such a program, whether
gratis or for a fee, you must pass on to the recipients the same
freedoms that you received.  You must make sure that they, too, receive
or can get the source code.  And you must show them these terms so they
know their rights.

  Developers that use the GNU GPL protect your rights with two steps:
(1) assert copyright on the software, and (2) offer you this License
giving you legal permission to copy, distribute and/or modify it.

  For the developers' and authors' protection, the GPL clearly explains
that there is no warranty for this free software.  For both users' and
authors' sake, the GPL requires that modified versions be marked as
changed, so that their problems will not be attributed erroneously to
authors of previous versions.

  Some devices are designed to deny users access to install or run
modified versions of the software inside them, although the manufacturer
can do so.  This is fundamentally incompatible with the aim of
protecting users' freedom to change the software.  The systematic
pattern of such abuse occurs in the area of products for individuals to
use, which is precisely where it is most unacceptable.  Therefore, we
have designed this version of the GPL to prohibit the practice for those
products.  If such problems arise substantially in other domains, we
stand ready to extend this provision to those domains in future versions
of the GPL, as needed to protect the freedom of users.

  Finally, every program is threatened constantly by software patents.
States should not allow patents to restrict development and use of
software on general-purpose computers, but in those that do, we wish to
avoid the special danger that patents applied to a free program could
make it effectively proprietary.  To prevent this, the GPL assures that
patents cannot be used to render the program non-free.

  The precise terms and conditions for copying, distribution and
modification follow.

                       TERMS AND CONDITIONS

  0. Definitions.

  "This License" refers to version 3 of the GNU General Public License.

  "Copyright" also means copyright-like laws that apply to other kinds of
works, such as semiconductor masks.

  "The Program" refers to any copyrightable work licensed under this
License.  Each licensee is addressed as "you".  "Licensees" and
"recipients" may be individuals or organizations.

  To "modify" a work means to copy from or adapt all or part of the work
in a fashion requiring copyright permission, other than the making of an
exact copy.  The resulting work is called a "modified version" of the
earlier work or a work "based on" the earlier work.

  A "covered work" means either the unmodified Program or a work based
on the Program.

  To "propagate" a work means to do anything with it that, without
permission, would make you directly or secondarily liable for
infringement under applicable copyright law, except executing it on a
computer or modifying a private copy.  Propagation includes copying,
distribution (with or without modification), making available to the
public, and in some countries other activities as well.

  To "convey" a work means any kind of propagation that enables other
parties to make or receive copies.  Mere interaction with a user through
a computer network, with no transfer of a copy, is not conveying.

  An interactive user interface displays "Appropriate Legal Notices"
to the extent that it includes a convenient and prominently visible
feature that (1) displays an appropriate copyright notice, and (2)
tells the user that there is no warranty for the work (except to the
extent that warranties are provided), that licensees may convey the
work under this License, and how to view a copy of this License.  If
the interface presents a list of user commands or options, such as a
menu, a prominent item in the list meets this criterion.

  1. Source Code.

  The "source code" for a work means the preferred form of the work
for making modifications to it.  "Object code" means any non-source
form of a work.

  A "Standard Interface" means an interface that either is an official
standard defined by a recognized standards body, or, in the case of
interfaces specified for a particular programming language, one that
is widely used among developers working in that language.

  The "System Libraries" of an executable work include anything, other
than the work as a whole, that (a) is included in the normal form of
packaging a Major Component, but which is not part of that Major
Component, and (b) serves only to enable use of the work with that
Major Component, or to implement a Standard Interface for which an
implementation is available to the public in source code form.  A
"Major Component", in this context, means a major essential component
(kernel, window system, and so on) of the specific operating system
(if any) on which the executable work runs, or a compiler used to
produce the work, or an object code interpreter used to run it.

  The "Corresponding Source" for a work in object code form means all
the source code needed to generate, install, and (for an executable
work) run the object code and to modify the work, including scripts to
control those activities.  However, it does not include the work's
System Libraries, or general-purpose tools or generally available free
programs which are used unmodified in performing those activities but
which are not part of the work.  For example, Corresponding Source
includes interface definition files associated with source files for
the work, and the source code for shared libraries and dynamically
linked subprograms that the work is specifically designed to require,
such as by intimate data communication or control flow between those
subprograms and other parts of the work.

  The Corresponding Source need not include anything that users
can regenerate automatically from other parts of the Corresponding
Source.

  The Corresponding Source for a work in source code form is that
same work.

  2. Basic Permissions.

  All rights granted under this License are granted for the term of
copyright on the Program, and are irrevocable provided the stated
conditions are met.  This License explicitly affirms your unlimited
permission to run the unmodified Program.  The output from running a
covered work is covered by this License only if the output, given its
content, constitutes a covered work.  This License acknowledges your
rights of fair use or other equivalent, as provided by copyright law.

  You may make, run and propagate covered works that you do not
convey, without conditions so long as your license otherwise remains
in force.  You may convey covered works to others for the sole purpose
of having them make modifications exclusively for you, or provide you
with facilities for running those works, provided that you comply with
the terms of this License in conveying all material for which you do
not control copyright.  Those thus making or running the covered works
for you must do so exclusively on your behalf, under your direction
and control, on terms that prohibit them from making any copies of
your copyrighted material outside their relationship with you.

  Conveying under any other circumstances is permitted solely under
the conditions stated below.  Sublicensing is not allowed; section 10
makes it unnecessary.

  3. Protecting Users' Legal Rights From Anti-Circumvention Law.

  No covered work shall be deemed part of an effective technological
measure under any applicable law fulfilling obligations under article
11 of the WIPO copyright treaty adopted on 20 December 1996, or
similar laws prohibiting or restricting circumvention of such
measures.

  When you convey a covered work, you waive any legal power to forbid
circumvention of technological measures to the extent such circumvention
is effected by exercising rights under this License with respect to
the covered work, and you disclaim any intention to limit operation or
modification of the work as a means of enforcing, against the work's
users, your or third parties' legal rights to forbid circumvention of
technological measures.

  4. Conveying Verbatim Copies.

  You may convey verbatim copies of the Program's source code as you
receive it, in any medium, provided that you conspicuously and
appropriately publish on each copy an appropriate copyright notice;
keep intact all notices stating that this License and any
non-permissive terms added in accord with section 7 apply to the code;
keep intact all notices of the absence of any warranty; and give all
recipients a copy of this License along with the Program.

  You may charge any price or no price for each copy that you convey,
and you may offer support or warranty protection for a fee.

  5. Conveying Modified Source Versions.

  You may convey a work based on the Program, or the modifications to
produce it from the Program, in the form of source code under the
terms of section 4, provided that you also meet all of these conditions:

    a) The work must carry prominent notices stating that you modified
    it, and giving a relevant date.

    b) The work must carry prominent notices stating that it is
    released under this License and any conditions added under section
    7.  This requirement modifies the requirement in section 4 to
    "keep intact all notices".

    c) You must license the entire work, as a whole, under this
    License to anyone who comes into possession of a copy.  This
    License will therefore apply, along with any applicable section 7
    additional terms, to the whole of the work, and all its parts,
    regardless of how they are packaged.  This License gives no
    permission to license the work in any other way, but it does not
    invalidate such permission if you have separately received it.

    d) If the work has interactive user interfaces, each must display
    Appropriate Legal Notices; however, if the Program has interactive
    interfaces that do not display Appropriate Legal Notices, your
    work need not make them do so.

  A compilation of a covered work with other separate and independent
works, which are not by their nature extensions of the covered work,
and which are not combined with it such as to form a larger program,
in or on a volume of a storage or distribution medium, is called an
"aggregate" if the compilation and its resulting copyright are not
used to limit the access or legal rights of the compilation's users
beyond what the individual works permit.  Inclusion of a covered work
in an aggregate does not cause this License to apply to the other
parts of the aggregate.

  6. Conveying Non-Source Forms.

  You may convey a covered work in object code form under the terms
of sections 4 and 5, provided that you also convey the
machine-readable Corresponding Source under the terms of this License,
in one of these ways:

    a) Convey the object code in, or embodied in, a physical product
    (including a physical distribution medium), accompanied by the
    Corresponding Source fixed on a durable physical medium
    customarily used for software interchange.

    b) Convey the object code in, or embodied in, a physical product
    (including a physical distribution medium), accompanied by a
    written offer, valid for at least three years and valid for as
    long as you offer spare parts or customer support for that product
    model, to give anyone who possesses the object code either (1) a
    copy of the Corresponding Source for all the software in the
    product that is covered by this License, on a durable physical
    medium customarily used for software interchange, for a price no
    more than your reasonable cost of physically performing this
    conveying of source, or (2) access to copy the
    Corresponding Source from a network server at no charge.

    c) Convey individual copies of the object code with a copy of the
    written offer to provide the Corresponding Source.  This
    alternative is allowed only occasionally and noncommercially, and
    only if you received the object code with such an offer, in accord
    with subsection 6b.

    d) Convey the object code by offering access from a designated
    place (gratis or for a charge), and offer equivalent access to the
    Corresponding Source in the same way through the same place at no
    further charge.  You need not require recipients to copy the
    Corresponding Source along with the object code.  If the place to
    copy the object code is a network server, the Corresponding Source
    may be on a different server (operated by you or a third party)
    that supports equivalent copying facilities, provided you maintain
    clear directions next to the object code saying where to find the
    Corresponding Source.  Regardless of what server hosts the
    Corresponding Source, you remain obligated to ensure that it is
    available for as long as needed to satisfy these requirements.

    e) Convey the object code using peer-to-peer transmission, provided
    you inform other peers where the object code and Corresponding
    Source of the work are being offered to the general public at no
    charge under subsection 6d.

  A separable portion of the object code, whose source code is excluded
from the Corresponding Source as a System Library, need not be
included in conveying the object code work.

  A "User Product" is either (1) a "consumer product", which means any
tangible personal property which is normally used for personal, family,
or household purposes, or (2) anything designed or sold for incorporation
into a dwelling.  In determining whether a product is a consumer product,
doubtful cases shall be resolved in favor of coverage.  For a particular
product received by a particular user, "normally used" refers to a
typical or common use of that class of product, regardless of the status
of the particular user or of the way in which the particular user
actually uses, or expects or is expected to use, the product.  A product
is a consumer product regardless of whether the product has substantial
commercial, industrial or non-consumer uses, unless such uses represent
the only significant mode of use of the product.

  "Installation Information" for a User Product means any methods,
procedures, authorization keys, or other information required to install
and execute modified versions of a covered work in that User Product from
a modified version of its Corresponding Source.  The information must
suffice to ensure that the continued functioning of the modified object
code is in no case prevented or interfered with solely because
modification has been made.

  If you convey an object code work under this section in, or with, or
specifically for use in, a User Product, and the conveying occurs as
part of a transaction in which the right of possession and use of the
User Product is transferred to the recipient in perpetuity or for a
fixed term (regardless of how the transaction is characterized), the
Corresponding Source conveyed under this section must be accompanied
by the Installation Information.  But this requirement does not apply
if neither you nor any third party retains the ability to install
modified object code on the User Product (for example, the work has
been installed in ROM).

  The requirement to provide Installation Information does not include a
requirement to continue to provide support service, warranty, or updates
for a work that has been modified or installed by the recipient, or for
the User Product in which it has been modified or installed.  Access to a
network may be denied when the modification itself materially and
adversely affects the operation of the network or violates the rules and
protocols for communication across the network.

  Corresponding Source conveyed, and Installation Information provided,
in accord with this section must be in a format that is publicly
documented (and with an implementation available to the public in
source code form), and must require no special password or key for
unpacking, reading or copying.

  7. Additional Terms.

  "Additional permissions" are terms that supplement the terms of this
License by making exceptions from one or more of its conditions.
Additional permissions that are applicable to the entire Program shall
be treated as though they were included in this License, to the extent
that they are valid under applicable law.  If additional permissions
apply only to part of the Program, that part may be used separately
under those permissions, but the entire Program remains governed by
this License without regard to the additional permissions.

  When you convey a copy of a covered work, you may at your option
remove any additional permissions from that copy, or from any part of
it.  (Additional permissions may be written to require their own
removal in certain cases when you modify the work.)  You may place
additional permissions on material, added by you to a covered work,
for which you have or can give appropriate copyright permission.

  Notwithstanding any other provision of this License, for material you
add to a covered work, you may (if authorized by the copyright holders of
that material) supplement the terms of this License with terms:

    a) Disclaiming warranty or limiting liability differently from the
    terms of sections 15 and 16 of this License; or

    b) Requiring preservation of specified reasonable legal notices or
    author attributions in that material or in the Appropriate Legal
    Notices displayed by works containing it; or

    c) Prohibiting misrepresentation of the origin of that material, or
    requiring that modified versions of such material be marked in
    reasonable ways as different from the original version; or

    d) Limiting the use for publicity purposes of names of licensors or
    authors of the material; or

    e) Declining to grant rights under trademark law for use of some
    trade names, trademarks, or service marks; or

    f) Requiring indemnification of licensors and authors of that
    material by anyone who conveys the material (or modified versions of
    it) with contractual assumptions of liability to the recipient, for
    any liability that these contractual assumptions directly impose on
    those licensors and authors.

  All other non-permissive additional terms are considered "further
restrictions" within the meaning of section 10.  If the Program as you
received it, or any part of it, contains a notice stating that it is
governed by this License along with a term that is a further
restriction, you may remove that term.  If a license document contains
a further restriction but permits relicensing or conveying under this
License, you may add to a covered work material governed by the terms
of that license document, provided that the further restriction does
not survive such relicensing or conveying.

  If you add terms to a covered work in accord with this section, you
must place, in the relevant source files, a statement of the
additional terms that apply to those files, or a notice indicating
where to find the applicable terms.

  Additional terms, permissive or non-permissive, may be stated in the
form of a separately written license, or stated as exceptions;
the above requirements apply either way.

  8. Termination.

  You may not propagate or modify a covered work except as expressly
provided under this License.  Any attempt otherwise to propagate or
modify it is void, and will automatically terminate your rights under
this License (including any patent licenses granted under the third
paragraph of section 11).

  However, if you cease all violation of this License, then your
license from a particular copyright holder is reinstated (a)
provisionally, unless and until the copyright holder explicitly and
finally terminates your license, and (b) permanently, if the copyright
holder fails to notify you of the violation by some reasonable means
prior to 60 days after the cessation.

  Moreover, your license from a particular copyright holder is
reinstated permanently if the copyright holder notifies you of the
violation by some reasonable means, this is the first time you have
received notice of violation of this License (for any work) from that
copyright holder, and you cure the violation prior to 30 days after
your receipt of the notice.

  Termination of your rights under this section does not terminate the
licenses of parties who have received copies or rights from you under
this License.  If your rights have been terminated and not permanently
reinstated, you do not qualify to receive new licenses for the same
material under section 10.

  9. Acceptance Not Required for Having Copies.

  You are not required to accept this License in order to receive or
run a copy of the Program.  Ancillary propagation of a covered work
occurring solely as a consequence of using peer-to-peer transmission
to receive a copy likewise does not require acceptance.  However,
nothing other than this License grants you permission to propagate or
modify any covered work.  These actions infringe copyright if you do
not accept this License.  Therefore, by modifying or propagating a
covered work, you indicate your acceptance of this License to do so.

  10. Automatic Licensing of Downstream Recipients.

  Each time you convey a covered work, the recipient automatically
receives a license from the original licensors, to run, modify and
propagate that work, subject to this License.  You are not responsible
for enforcing compliance by third parties with this License.

  An "entity transaction" is a transaction transferring control of an
organization, or substantially all assets of one, or subdividing an
organization, or merging organizations.  If propagation of a covered
work results from an entity transaction, each party to that
transaction who receives a copy of the work also receives whatever
licenses to the work the party's predecessor in interest had or could
give under the previous paragraph, plus a right to possession of the
Corresponding Source of the work from the predecessor in interest, if
the predecessor has it or can get it with reasonable efforts.

  You may not impose any further restrictions on the exercise of the
rights granted or affirmed under this License.  For example, you may
not impose a license fee, royalty, or other charge for exercise of
rights granted under this License, and you may not initiate litigation
(including a cross-claim or counterclaim in a lawsuit) alleging that
any patent claim is infringed by making, using, selling, offering for
sale, or importing the Program or any portion of it.

  11. Patents.

  A "contributor" is a copyright holder who authorizes use under this
License of the Program or a work on which the Program is based.  The
work thus licensed is called the contributor's "contributor version".

  A contributor's "essential patent claims" are all patent claims
owned or controlled by the contributor, whether already acquired or
hereafter acquired, that would be infringed by some manner, permitted
by this License, of making, using, or selling its contributor version,
but do not include claims that would be infringed only as a
consequence of further modification of the contributor version.  For
purposes of this definition, "control" includes the right to grant
patent sublicenses in a manner consistent with the requirements of
this License.

  Each contributor grants you a non-exclusive, worldwide, royalty-free
patent license under the contributor's essential patent claims, to
make, use, sell, offer for sale, import and otherwise run, modify and
propagate the contents of its contributor version.

  In the following three paragraphs, a "patent license" is any express
agreement or commitment, however denominated, not to enforce a patent
(such as an express permission to practice a patent or covenant not to
sue for patent infringement).  To "grant" such a patent license to a
party means to make such an agreement or commitment not to enforce a
patent against the party.

  If you convey a covered work, knowingly relying on a patent license,
and the Corresponding Source of the work is not available for anyone
to copy, free of charge and under the terms of this License, through a
publicly available network server or other readily accessible means,
then you must either (1) cause the Corresponding Source to be so
available, or (2) arrange to deprive yourself of the benefit of the
patent license for this particular work, or (3) arrange, in a manner
consistent with the requirements of this License, to extend the patent
license to downstream recipients.  "Knowingly relying" means you have
actual knowledge that, but for the patent license, your conveying the
covered work in a country, or your recipient's use of the covered work
in a country, would infringe one or more identifiable patents in that
country that you have reason to believe are valid.

  If, pursuant to or in connection with a single transaction or
arrangement, you convey, or propagate by procuring conveyance of, a
covered work, and grant a patent license to some of the parties
receiving the covered work authorizing them to use, propagate, modify
or convey a specific copy of the covered work, then the patent license
you grant is automatically extended to all recipients of the covered
work and works based on it.

  A patent license is "discriminatory" if it does not include within
the scope of its coverage, prohibits the exercise of, or is
conditioned on the non-exercise of one or more of the rights that are
specifically granted under this License.  You may not convey a covered
work if you are a party to an arrangement with a third party that is
in the business of distributing software, under which you make payment
to the third party based on the extent of your activity of conveying
the work, and under which the third party grants, to any of the
parties who would receive the covered work from you, a discriminatory
patent license (a) in connection with copies of the covered work
conveyed by you (or copies made from those copies), or (b) primarily
for and in connection with specific products or compilations that
contain the covered work, unless you entered into that arrangement,
or that patent license was granted, prior to 28 March 2007.

  Nothing in this License shall be construed as excluding or limiting
any implied license or other defenses to infringement that may
otherwise be available to you under applicable patent law.

  12. No Surrender of Others' Freedom.

  If conditions are imposed on you (whether by court order, agreement or
otherwise) that contradict the conditions of this License, they do not
excuse you from the conditions of this License.  If you cannot convey a
covered work so as to satisfy simultaneously your obligations under this
License and any other pertinent obligations, then as a consequence you may
not convey it at all.  For example, if you agree to terms that obligate you
to collect a royalty for further conveying from those to whom you convey
the Program, the only way you could satisfy both those terms and this
License would be to refrain entirely from conveying the Program.

  13. Use with the GNU Affero General Public License.

  Notwithstanding any other provision of this License, you have
permission to link or combine any covered work with a work licensed
under version 3 of the GNU Affero General Public License into a single
combined work, and to convey the resulting work.  The terms of this
License will continue to apply to the part which is the covered work,
but the special requirements of the GNU Affero General Public License,
section 13, concerning interaction through a network will apply to the
combination as such.

  14. Revised Versions of this License.

  The Free Software Foundation may publish revised and/or new versions of
the GNU General Public License from time to time.  Such new versions will
be similar in spirit to the present version, but may differ in detail to
address new problems or concerns.

  Each version is given a distinguishing version number.  If the
Program specifies that a certain numbered version of the GNU General
Public License "or any later version" applies to it, you have the
option of following the terms and conditions either of that numbered
version or of any later version published by the Free Software
Foundation.  If the Program does not specify a version number of the
GNU General Public License, you may choose any version ever published
by the Free Software Foundation.

  If the Program specifies that a proxy can decide which future
versions of the GNU General Public License can be used, that proxy's
public statement of acceptance of a version permanently authorizes you
to choose that version for the Program.

  Later license versions may give you additional or different
permissions.  However, no additional obligations are imposed on any
author or copyright holder as a result of your choosing to follow a
later version.

  15. Disclaimer of Warranty.

  THERE IS NO WARRANTY FOR THE PROGRAM, TO THE EXTENT PERMITTED BY
APPLICABLE LAW.  EXCEPT WHEN OTHERWISE STATED IN WRITING THE COPYRIGHT
HOLDERS AND/OR OTHER PARTIES PROVIDE THE PROGRAM "AS IS" WITHOUT WARRANTY
OF ANY KIND, EITHER EXPRESSED OR IMPLIED, INCLUDING, BUT NOT LIMITED TO,
THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
PURPOSE.  THE ENTIRE RISK AS TO THE QUALITY AND PERFORMANCE OF THE PROGRAM
IS WITH YOU.  SHOULD THE PROGRAM PROVE DEFECTIVE, YOU ASSUME THE COST OF
ALL NECESSARY SERVICING, REPAIR OR CORRECTION.

  16. Limitation of Liability.

  IN NO EVENT UNLESS REQUIRED BY APPLICABLE LAW OR AGREED TO IN WRITING
WILL ANY COPYRIGHT HOLDER, OR ANY OTHER PARTY WHO MODIFIES AND/OR CONVEYS
THE PROGRAM AS PERMITTED ABOVE, BE LIABLE TO YOU FOR DAMAGES, INCLUDING ANY
GENERAL, SPECIAL, INCIDENTAL OR CONSEQUENTIAL DAMAGES ARISING OUT OF THE
USE OR INABILITY TO USE THE PROGRAM (INCLUDING BUT NOT LIMITED TO LOSS OF
DATA OR DATA BEING RENDERED INACCURATE OR LOSSES SUSTAINED BY YOU OR THIRD
PARTIES OR A FAILURE OF THE PROGRAM TO OPERATE WITH ANY OTHER PROGRAMS),
EVEN IF SUCH HOLDER OR OTHER PARTY HAS BEEN ADVISED OF THE POSSIBILITY OF
SUCH DAMAGES.

  17. Interpretation of Sections 15 and 16.

  If the disclaimer of warranty and limitation of liability provided
above cannot be given local legal effect according to their terms,
reviewing courts shall apply local law that most closely approximates
an absolute waiver of all civil liability in connection with the
Program, unless a warranty or assumption of liability accompanies a
copy of the Program in return for a fee.

                     END OF TERMS AND CONDITIONS

            How to Apply These Terms to Your New Programs

  If you develop a new program, and you want it to be of the greatest
possible use to the public, the best way to achieve this is to make it
free software which everyone can redistribute and change under these terms.

  To do so, attach the following notices to the program.  It is safest
to attach them to the start of each source file to most effectively
state the exclusion of warranty; and each file should have at least
the "copyright" line and a pointer to where the full notice is found.

    <one line to give the program's name and a brief idea of what it does.>
    Copyright (C) <year>  <name of author>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.

Also add information on how to contact you by electronic and paper mail.

  If the program does terminal interaction, make it output a short
notice like this when it starts in an interactive mode:

    <program>  Copyright (C) <year>  <name of author>
    This program comes with ABSOLUTELY NO WARRANTY; for details type `show w'.
    This is free software, and you are welcome to redistribute it
    under certain conditions; type `show c' for details.

The hypothetical commands `show w' and `show c' should show the appropriate
parts of the General Public License.  Of course, your program's commands
might be different; for a GUI interface, you would use an "about box".

  You should also get your employer (if you work as a programmer) or school,
if any, to sign a "copyright disclaimer" for the program, if necessary.
For more information on this, and how to apply and follow the GNU GPL, see
<https://www.gnu.org/licenses/>.

  The GNU General Public License does not permit incorporating your program
into proprietary programs.  If your program is a subroutine library, you
may consider it more useful to permit linking proprietary applications with
the library.  If this is what you want to do, use the GNU Lesser General
Public License instead of this License.  But first, please read
<https://www.gnu.org/licenses/why-not-lgpl.html>.

````

<a id="text-10"></a>

### numpy: numpy-2.5.4.dist-info/licenses/numpy/_core/include/numpy/libdivide/LICENSE.txt

Source: `numpy 2.5.4: numpy-2.5.4.dist-info/licenses/numpy/_core/include/numpy/libdivide/LICENSE.txt`. SHA-256: `fbc539f47d0cf83bc61378080fb873d5c14630126cacbfe754035c3926daa5ec`. UTF-8/LF bytes: 1018.

````text
  zlib License
  ------------

  Copyright (C) 2010 - 2019 ridiculous_fish, <libdivide@ridiculousfish.com>
  Copyright (C) 2016 - 2019 Kim Walisch, <kim.walisch@gmail.com>

  This software is provided 'as-is', without any express or implied
  warranty.  In no event will the authors be held liable for any damages
  arising from the use of this software.

  Permission is granted to anyone to use this software for any purpose,
  including commercial applications, and to alter it and redistribute it
  freely, subject to the following restrictions:

  1. The origin of this software must not be misrepresented; you must not
     claim that you wrote the original software. If you use this software
     in a product, an acknowledgment in the product documentation would be
     appreciated but is not required.
  2. Altered source versions must be plainly marked as such, and must not be
     misrepresented as being the original software.
  3. This notice may not be removed or altered from any source distribution.
````

<a id="text-11"></a>

### numpy: numpy-2.5.4.dist-info/licenses/numpy/_core/src/common/pythoncapi-compat/COPYING

Source: `numpy 2.5.4: numpy-2.5.4.dist-info/licenses/numpy/_core/src/common/pythoncapi-compat/COPYING`. SHA-256: `3f2c1ffa76383a55ae0aac01c9737cd70050dff63e1f026694fbe9d662573c98`. UTF-8/LF bytes: 690.

````text
BSD Zero Clause License

Copyright Contributors to the pythoncapi_compat project.

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY
AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT,
INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR
OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
PERFORMANCE OF THIS SOFTWARE.
````

<a id="text-12"></a>

### numpy: numpy-2.5.4.dist-info/licenses/numpy/_core/src/highway/LICENSE

Source: `numpy 2.5.4: numpy-2.5.4.dist-info/licenses/numpy/_core/src/highway/LICENSE`. SHA-256: `e340270d4f64384569a91d546acb5b094d69ce47f0c015db77abb74dc6f815af`. UTF-8/LF bytes: 20785.

````text
This project is primarily dual-licensed under your choice of either the Apache
License 2.0 or the BSD 3-Clause License.

The following files are licensed under different terms:
*   hwy/contrib/random/random-inl.h: CC0 1.0 Universal

The full texts of all applicable licenses are included below, separated by
'---'.

--------------------------------------------------------------------------------
Apache License 2.0
--------------------------------------------------------------------------------

                                 Apache License
                           Version 2.0, January 2004
                        http://www.apache.org/licenses/

   TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION

   1. Definitions.

      "License" shall mean the terms and conditions for use, reproduction,
      and distribution as defined by Sections 1 through 9 of this document.

      "Licensor" shall mean the copyright owner or entity authorized by
      the copyright owner that is granting the License.

      "Legal Entity" shall mean the union of the acting entity and all
      other entities that control, are controlled by, or are under common
      control with that entity. For the purposes of this definition,
      "control" means (i) the power, direct or indirect, to cause the
      direction or management of such entity, whether by contract or
      otherwise, or (ii) ownership of fifty percent (50%) or more of the
      outstanding shares, or (iii) beneficial ownership of such entity.

      "You" (or "Your") shall mean an individual or Legal Entity
      exercising permissions granted by this License.

      "Source" form shall mean the preferred form for making modifications,
      including but not limited to software source code, documentation
      source, and configuration files.

      "Object" form shall mean any form resulting from mechanical
      transformation or translation of a Source form, including but
      not limited to compiled object code, generated documentation,
      and conversions to other media types.

      "Work" shall mean the work of authorship, whether in Source or
      Object form, made available under the License, as indicated by a
      copyright notice that is included in or attached to the work
      (an example is provided in the Appendix below).

      "Derivative Works" shall mean any work, whether in Source or Object
      form, that is based on (or derived from) the Work and for which the
      editorial revisions, annotations, elaborations, or other modifications
      represent, as a whole, an original work of authorship. For the purposes
      of this License, Derivative Works shall not include works that remain
      separable from, or merely link (or bind by name) to the interfaces of,
      the Work and Derivative Works thereof.

      "Contribution" shall mean any work of authorship, including
      the original version of the Work and any modifications or additions
      to that Work or Derivative Works thereof, that is intentionally
      submitted to Licensor for inclusion in the Work by the copyright owner
      or by an individual or Legal Entity authorized to submit on behalf of
      the copyright owner. For the purposes of this definition, "submitted"
      means any form of electronic, verbal, or written communication sent
      to the Licensor or its representatives, including but not limited to
      communication on electronic mailing lists, source code control systems,
      and issue tracking systems that are managed by, or on behalf of, the
      Licensor for the purpose of discussing and improving the Work, but
      excluding communication that is conspicuously marked or otherwise
      designated in writing by the copyright owner as "Not a Contribution."

      "Contributor" shall mean Licensor and any individual or Legal Entity
      on behalf of whom a Contribution has been received by Licensor and
      subsequently incorporated within the Work.

   2. Grant of Copyright License. Subject to the terms and conditions of
      this License, each Contributor hereby grants to You a perpetual,
      worldwide, non-exclusive, no-charge, royalty-free, irrevocable
      copyright license to reproduce, prepare Derivative Works of,
      publicly display, publicly perform, sublicense, and distribute the
      Work and such Derivative Works in Source or Object form.

   3. Grant of Patent License. Subject to the terms and conditions of
      this License, each Contributor hereby grants to You a perpetual,
      worldwide, non-exclusive, no-charge, royalty-free, irrevocable
      (except as stated in this section) patent license to make, have made,
      use, offer to sell, sell, import, and otherwise transfer the Work,
      where such license applies only to those patent claims licensable
      by such Contributor that are necessarily infringed by their
      Contribution(s) alone or by combination of their Contribution(s)
      with the Work to which such Contribution(s) was submitted. If You
      institute patent litigation against any entity (including a
      cross-claim or counterclaim in a lawsuit) alleging that the Work
      or a Contribution incorporated within the Work constitutes direct
      or contributory patent infringement, then any patent licenses
      granted to You under this License for that Work shall terminate
      as of the date such litigation is filed.

   4. Redistribution. You may reproduce and distribute copies of the
      Work or Derivative Works thereof in any medium, with or without
      modifications, and in Source or Object form, provided that You
      meet the following conditions:

      (a) You must give any other recipients of the Work or
          Derivative Works a copy of this License; and

      (b) You must cause any modified files to carry prominent notices
          stating that You changed the files; and

      (c) You must retain, in the Source form of any Derivative Works
          that You distribute, all copyright, patent, trademark, and
          attribution notices from the Source form of the Work,
          excluding those notices that do not pertain to any part of
          the Derivative Works; and

      (d) If the Work includes a "NOTICE" text file as part of its
          distribution, then any Derivative Works that You distribute must
          include a readable copy of the attribution notices contained
          within such NOTICE file, excluding those notices that do not
          pertain to any part of the Derivative Works, in at least one
          of the following places: within a NOTICE text file distributed
          as part of the Derivative Works; within the Source form or
          documentation, if provided along with the Derivative Works; or,
          within a display generated by the Derivative Works, if and
          wherever such third-party notices normally appear. The contents
          of the NOTICE file are for informational purposes only and
          do not modify the License. You may add Your own attribution
          notices within Derivative Works that You distribute, alongside
          or as an addendum to the NOTICE text from the Work, provided
          that such additional attribution notices cannot be construed
          as modifying the License.

      You may add Your own copyright statement to Your modifications and
      may provide additional or different license terms and conditions
      for use, reproduction, or distribution of Your modifications, or
      for any such Derivative Works as a whole, provided Your use,
      reproduction, and distribution of the Work otherwise complies with
      the conditions stated in this License.

   5. Submission of Contributions. Unless You explicitly state otherwise,
      any Contribution intentionally submitted for inclusion in the Work
      by You to the Licensor shall be under the terms and conditions of
      this License, without any additional terms or conditions.
      Notwithstanding the above, nothing herein shall supersede or modify
      the terms of any separate license agreement you may have executed
      with Licensor regarding such Contributions.

   6. Trademarks. This License does not grant permission to use the trade
      names, trademarks, service marks, or product names of the Licensor,
      except as required for reasonable and customary use in describing the
      origin of the Work and reproducing the content of the NOTICE file.

   7. Disclaimer of Warranty. Unless required by applicable law or
      agreed to in writing, Licensor provides the Work (and each
      Contributor provides its Contributions) on an "AS IS" BASIS,
      WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
      implied, including, without limitation, any warranties or conditions
      of TITLE, NON-INFRINGEMENT, MERCHANTABILITY, or FITNESS FOR A
      PARTICULAR PURPOSE. You are solely responsible for determining the
      appropriateness of using or redistributing the Work and assume any
      risks associated with Your exercise of permissions under this License.

   8. Limitation of Liability. In no event and under no legal theory,
      whether in tort (including negligence), contract, or otherwise,
      unless required by applicable law (such as deliberate and grossly
      negligent acts) or agreed to in writing, shall any Contributor be
      liable to You for damages, including any direct, indirect, special,
      incidental, or consequential damages of any character arising as a
      result of this License or out of the use or inability to use the
      Work (including but not limited to damages for loss of goodwill,
      work stoppage, computer failure or malfunction, or any and all
      other commercial damages or losses), even if such Contributor
      has been advised of the possibility of such damages.

   9. Accepting Warranty or Additional Liability. While redistributing
      the Work or Derivative Works thereof, You may choose to offer,
      and charge a fee for, acceptance of support, warranty, indemnity,
      or other liability obligations and/or rights consistent with this
      License. However, in accepting such obligations, You may act only
      on Your own behalf and on Your sole responsibility, not on behalf
      of any other Contributor, and only if You agree to indemnify,
      defend, and hold each Contributor harmless for any liability
      incurred by, or claims asserted against, such Contributor by reason
      of your accepting any such warranty or additional liability.

   END OF TERMS AND CONDITIONS

   APPENDIX: How to apply the Apache License to your work.

      To apply the Apache License to your work, attach the following
      boilerplate notice, with the fields enclosed by brackets "[]"
      replaced with your own identifying information. (Don't include
      the brackets!)  The text should be enclosed in the appropriate
      comment syntax for the file format. We also recommend that a
      file or class name and description of purpose be included on the
      same "printed page" as the copyright notice for easier
      identification within third-party archives.

   Copyright [yyyy] [name of copyright owner]

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.

--------------------------------------------------------------------------------
BSD 3-Clause License
--------------------------------------------------------------------------------

Copyright (c) The Highway Project Authors. All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

1.  Redistributions of source code must retain the above copyright notice, this
    list of conditions and the following disclaimer.

2.  Redistributions in binary form must reproduce the above copyright notice,
    this list of conditions and the following disclaimer in the documentation
    and/or other materials provided with the distribution.

3.  Neither the name of the copyright holder nor the names of its
    contributors may be used to endorse or promote products derived from
    this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

--------------------------------------------------------------------------------
CC0 1.0 Universal
--------------------------------------------------------------------------------

Creative Commons Legal Code

CC0 1.0 Universal

    CREATIVE COMMONS CORPORATION IS NOT A LAW FIRM AND DOES NOT PROVIDE
    LEGAL SERVICES. DISTRIBUTION OF THIS DOCUMENT DOES NOT CREATE AN
    ATTORNEY-CLIENT RELATIONSHIP. CREATIVE COMMONS PROVIDES THIS
    INFORMATION ON AN "AS-IS" BASIS. CREATIVE COMMONS MAKES NO WARRANTIES
    REGARDING THE USE OF THIS DOCUMENT OR THE INFORMATION OR WORKS
    PROVIDED HEREUNDER, AND DISCLAIMS LIABILITY FOR DAMAGES RESULTING FROM
    THE USE OF THIS DOCUMENT OR THE INFORMATION OR WORKS PROVIDED
    HEREUNDER.

Statement of Purpose

The laws of most jurisdictions throughout the world automatically confer
exclusive Copyright and Related Rights (defined below) upon the creator
and subsequent owner(s) (each and all, an "owner") of an original work of
authorship and/or a database (each, a "Work").

Certain owners wish to permanently relinquish those rights to a Work for
the purpose of contributing to a commons of creative, cultural and
scientific works ("Commons") that the public can reliably and without fear
of later claims of infringement build upon, modify, incorporate in other
works, reuse and redistribute as freely as possible in any form whatsoever
and for any purposes, including without limitation commercial purposes.
These owners may contribute to the Commons to promote the ideal of a free
culture and the further production of creative, cultural and scientific
works, or to gain reputation or greater distribution for their Work in
part through the use and efforts of others.

For these and/or other purposes and motivations, and without any
expectation of additional consideration or compensation, the person
associating CC0 with a Work (the "Affirmer"), to the extent that he or she
is an owner of Copyright and Related Rights in the Work, voluntarily
elects to apply CC0 to the Work and publicly distribute the Work under its
terms, with knowledge of his or her Copyright and Related Rights in the
Work and the meaning and intended legal effect of CC0 on those rights.

1. Copyright and Related Rights. A Work made available under CC0 may be
protected by copyright and related or neighboring rights ("Copyright and
Related Rights"). Copyright and Related Rights include, but are not
limited to, the following:

  i. the right to reproduce, adapt, distribute, perform, display,
     communicate, and translate a Work;
 ii. moral rights retained by the original author(s) and/or performer(s);
iii. publicity and privacy rights pertaining to a person's image or
     likeness depicted in a Work;
 iv. rights protecting against unfair competition in regards to a Work,
     subject to the limitations in paragraph 4(a), below;
  v. rights protecting the extraction, dissemination, use and reuse of data
     in a Work;
 vi. database rights (such as those arising under Directive 96/9/EC of the
     European Parliament and of the Council of 11 March 1996 on the legal
     protection of databases, and under any national implementation
     thereof, including any amended or successor version of such
     directive); and
vii. other similar, equivalent or corresponding rights throughout the
     world based on applicable law or treaty, and any national
     implementations thereof.

2. Waiver. To the greatest extent permitted by, but not in contravention
of, applicable law, Affirmer hereby overtly, fully, permanently,
irrevocably and unconditionally waives, abandons, and surrenders all of
Affirmer's Copyright and Related Rights and associated claims and causes
of action, whether now known or unknown (including existing as well as
future claims and causes of action), in the Work (i) in all territories
worldwide, (ii) for the maximum duration provided by applicable law or
treaty (including future time extensions), (iii) in any current or future
medium and for any number of copies, and (iv) for any purpose whatsoever,
including without limitation commercial, advertising or promotional
purposes (the "Waiver"). Affirmer makes the Waiver for the benefit of each
member of the public at large and to the detriment of Affirmer's heirs and
successors, fully intending that such Waiver shall not be subject to
revocation, rescission, cancellation, termination, or any other legal or
equitable action to disrupt the quiet enjoyment of the Work by the public
as contemplated by Affirmer's express Statement of Purpose.

3. Public License Fallback. Should any part of the Waiver for any reason
be judged legally invalid or ineffective under applicable law, then the
Waiver shall be preserved to the maximum extent permitted taking into
account Affirmer's express Statement of Purpose. In addition, to the
extent the Waiver is so judged Affirmer hereby grants to each affected
person a royalty-free, non transferable, non sublicensable, non exclusive,
irrevocable and unconditional license to exercise Affirmer's Copyright and
Related Rights in the Work (i) in all territories worldwide, (ii) for the
maximum duration provided by applicable law or treaty (including future
time extensions), (iii) in any current or future medium and for any number
of copies, and (iv) for any purpose whatsoever, including without
limitation commercial, advertising or promotional purposes (the
"License"). The License shall be deemed effective as of the date CC0 was
applied by Affirmer to the Work. Should any part of the License for any
reason be judged legally invalid or ineffective under applicable law, such
partial invalidity or ineffectiveness shall not invalidate the remainder
of the License, and in such case Affirmer hereby affirms that he or she
will not (i) exercise any of his or her remaining Copyright and Related
Rights in the Work or (ii) assert any associated claims and causes of
action with respect to the Work, in either case contrary to Affirmer's
express Statement of Purpose.

4. Limitations and Disclaimers.

 a. No trademark or patent rights held by Affirmer are waived, abandoned,
    surrendered, licensed or otherwise affected by this document.
 b. Affirmer offers the Work as-is and makes no representations or
    warranties of any kind concerning the Work, express, implied,
    statutory or otherwise, including without limitation warranties of
    title, merchantability, fitness for a particular purpose, non
    infringement, or the absence of latent or other defects, accuracy, or
    the present or absence of errors, whether or not discoverable, all to
    the greatest extent permissible under applicable law.
 c. Affirmer disclaims responsibility for clearing rights of other persons
    that may apply to the Work or any use thereof, including without
    limitation any person's Copyright and Related Rights in the Work.
    Further, Affirmer disclaims responsibility for obtaining any necessary
    consents, permissions or other rights required for any use of the
    Work.
 d. Affirmer understands and acknowledges that Creative Commons is not a
    party to this document and has no duty or obligation with respect to
    this CC0 or use of the Work.
````

<a id="text-13"></a>

### numpy: numpy-2.5.4.dist-info/licenses/numpy/_core/src/multiarray/dragon4_LICENSE.txt

Source: `numpy 2.5.4: numpy-2.5.4.dist-info/licenses/numpy/_core/src/multiarray/dragon4_LICENSE.txt`. SHA-256: `f7b14309e5f54e5022b26448eefd419988ada2aec01d3c1162d84a0ea8f21f2c`. UTF-8/LF bytes: 1414.

````text
Copyright (c) 2014 Ryan Juckett

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to
deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
sell copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
IN THE SOFTWARE.

dragon4.c|h h contains a modified version of Ryan Juckett's Dragon4
implementation, obtained from https://www.ryanjuckett.com,
which has been ported from C++ to C and which has
modifications specific to printing floats in numpy.

Ryan Juckett's original code was under the Zlib license; he gave numpy
permission to include it under the MIT license instead.
````

<a id="text-14"></a>

### numpy: numpy-2.5.4.dist-info/licenses/numpy/_core/src/npysort/x86-simd-sort/LICENSE.md

Source: `numpy 2.5.4: numpy-2.5.4.dist-info/licenses/numpy/_core/src/npysort/x86-simd-sort/LICENSE.md`. SHA-256: `211e7d737d6179a08f791ebb0a99897ce7cd2457410c542876d125576edfe910`. UTF-8/LF bytes: 1514.

````text
BSD 3-Clause License

Copyright (c) 2022, Intel. All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its
   contributors may be used to endorse or promote products derived from
   this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
````

<a id="text-15"></a>

### numpy: numpy-2.5.4.dist-info/licenses/numpy/_core/src/umath/svml/LICENSE

Source: `numpy 2.5.4: numpy-2.5.4.dist-info/licenses/numpy/_core/src/umath/svml/LICENSE`. SHA-256: `c17011467b4fe6e20fbfbeda4df09e58c2bca5480a063e55735a4000a379aad9`. UTF-8/LF bytes: 1543.

````text
Copyright (c) 2005-2021, NumPy Developers.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

    * Redistributions of source code must retain the above copyright
       notice, this list of conditions and the following disclaimer.

    * Redistributions in binary form must reproduce the above
       copyright notice, this list of conditions and the following
       disclaimer in the documentation and/or other materials provided
       with the distribution.

    * Neither the name of the NumPy Developers nor the names of any
       contributors may be used to endorse or promote products derived
       from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
````

<a id="text-16"></a>

### numpy: numpy-2.5.4.dist-info/licenses/numpy/fft/pocketfft/LICENSE.md

Source: `numpy 2.5.4: numpy-2.5.4.dist-info/licenses/numpy/fft/pocketfft/LICENSE.md`. SHA-256: `a85ca13fdf90160b64a0698215868c13b74d835ad0a4e2ba44713b8c5058a056`. UTF-8/LF bytes: 1498.

````text
Copyright (C) 2010-2018 Max-Planck-Society
All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.
* Redistributions in binary form must reproduce the above copyright notice, this
  list of conditions and the following disclaimer in the documentation and/or
  other materials provided with the distribution.
* Neither the name of the copyright holder nor the names of its contributors may
  be used to endorse or promote products derived from this software without
  specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
````

<a id="text-17"></a>

### numpy: numpy-2.5.4.dist-info/licenses/numpy/linalg/lapack_lite/LICENSE.txt

Source: `numpy 2.5.4: numpy-2.5.4.dist-info/licenses/numpy/linalg/lapack_lite/LICENSE.txt`. SHA-256: `a14cc25e10d40a3aa705b7de2fb764a6535d8ee9b2db4e1724900585457dfd55`. UTF-8/LF bytes: 2266.

````text
Copyright (c) 1992-2013 The University of Tennessee and The University
                        of Tennessee Research Foundation.  All rights
                        reserved.
Copyright (c) 2000-2013 The University of California Berkeley. All
                        rights reserved.
Copyright (c) 2006-2013 The University of Colorado Denver.  All rights
                        reserved.

$COPYRIGHT$

Additional copyrights may follow

$HEADER$

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

- Redistributions of source code must retain the above copyright
  notice, this list of conditions and the following disclaimer.

- Redistributions in binary form must reproduce the above copyright
  notice, this list of conditions and the following disclaimer listed
  in this license in the documentation and/or other materials
  provided with the distribution.

- Neither the name of the copyright holders nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission.

The copyright holders provide no reassurances that the source code
provided does not infringe any patent, copyright, or any other
intellectual property rights of third parties.  The copyright holders
disclaim any liability to any recipient for claims brought against
recipient by any third party for infringement of that parties
intellectual property rights.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
````

<a id="text-18"></a>

### numpy: numpy-2.5.4.dist-info/licenses/numpy/ma/LICENSE

Source: `numpy 2.5.4: numpy-2.5.4.dist-info/licenses/numpy/ma/LICENSE`. SHA-256: `05f3b88351988ecfad10abe92c0c50e5875c6452d5009a0084cc291551ffcca6`. UTF-8/LF bytes: 1593.

````text
* Copyright (c) 2006, University of Georgia and Pierre G.F. Gerard-Marchant
* All rights reserved.
* Redistribution and use in source and binary forms, with or without
* modification, are permitted provided that the following conditions are met:
*
*     * Redistributions of source code must retain the above copyright
*       notice, this list of conditions and the following disclaimer.
*     * Redistributions in binary form must reproduce the above copyright
*       notice, this list of conditions and the following disclaimer in the
*       documentation and/or other materials provided with the distribution.
*     * Neither the name of the University of Georgia nor the
*       names of its contributors may be used to endorse or promote products
*       derived from this software without specific prior written permission.
*
* THIS SOFTWARE IS PROVIDED BY THE REGENTS AND CONTRIBUTORS ``AS IS'' AND ANY
* EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
* WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
* DISCLAIMED. IN NO EVENT SHALL THE REGENTS OR CONTRIBUTORS BE LIABLE FOR ANY
* DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
* (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
* LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
* ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
* (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
* SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
````

<a id="text-19"></a>

### numpy: numpy-2.5.4.dist-info/licenses/numpy/random/LICENSE.md

Source: `numpy 2.5.4: numpy-2.5.4.dist-info/licenses/numpy/random/LICENSE.md`. SHA-256: `103166b62b80443afb9eb3488e052ea06be0cff566b908f199e561fde49af19f`. UTF-8/LF bytes: 3511.

````text
**This software is dual-licensed under the The University of Illinois/NCSA
Open Source License (NCSA) and The 3-Clause BSD License**

# NCSA Open Source License
**Copyright (c) 2019 Kevin Sheppard. All rights reserved.**

Developed by: Kevin Sheppard (<kevin.sheppard@economics.ox.ac.uk>,
<kevin.k.sheppard@gmail.com>)
[http://www.kevinsheppard.com](http://www.kevinsheppard.com)

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal with
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

Redistributions of source code must retain the above copyright notice, this
list of conditions and the following disclaimers.

Redistributions in binary form must reproduce the above copyright notice, this
list of conditions and the following disclaimers in the documentation and/or
other materials provided with the distribution.

Neither the names of Kevin Sheppard, nor the names of any contributors may be
used to endorse or promote products derived from this Software without specific
prior written permission.

**THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
CONTRIBUTORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS WITH
THE SOFTWARE.**


# 3-Clause BSD License
**Copyright (c) 2019 Kevin Sheppard. All rights reserved.**

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice,
   this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its contributors
   may be used to endorse or promote products derived from this software
   without specific prior written permission.

**THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
THE POSSIBILITY OF SUCH DAMAGE.**

# Components

Many parts of this module have been derived from original sources, 
often the algorithm's designer. Component licenses are located with 
the component code.
````

<a id="text-20"></a>

### numpy: numpy-2.5.4.dist-info/licenses/numpy/random/src/distributions/LICENSE.md

Source: `numpy 2.5.4: numpy-2.5.4.dist-info/licenses/numpy/random/src/distributions/LICENSE.md`. SHA-256: `469778be8f33d54e1bcaab28c281cc472916d2d273f835e55bc487d30503face`. UTF-8/LF bytes: 2745.

````text
## NumPy

Copyright (c) 2005-2017, NumPy Developers.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

* Redistributions of source code must retain the above copyright
   notice, this list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above
   copyright notice, this list of conditions and the following
   disclaimer in the documentation and/or other materials provided
   with the distribution.

* Neither the name of the NumPy Developers nor the names of any
   contributors may be used to endorse or promote products derived
   from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


## Julia

The ziggurat methods were derived from Julia.

Copyright (c) 2009-2019: Jeff Bezanson, Stefan Karpinski, Viral B. Shah,
and other contributors:

https://github.com/JuliaLang/julia/contributors

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
````

<a id="text-21"></a>

### numpy: numpy-2.5.4.dist-info/licenses/numpy/random/src/mt19937/LICENSE.md

Source: `numpy 2.5.4: numpy-2.5.4.dist-info/licenses/numpy/random/src/mt19937/LICENSE.md`. SHA-256: `0e111337b25494a773106695f0e799f642b8567aaacca4f116a74a8177179156`. UTF-8/LF bytes: 2926.

````text
# MT19937

Copyright (c) 2003-2005, Jean-Sebastien Roy (js@jeannot.org)

The rk_random and rk_seed functions algorithms and the original design of
the Mersenne Twister RNG:

  Copyright (C) 1997 - 2002, Makoto Matsumoto and Takuji Nishimura,
  All rights reserved.

  Redistribution and use in source and binary forms, with or without
  modification, are permitted provided that the following conditions
  are met:

  1. Redistributions of source code must retain the above copyright
  notice, this list of conditions and the following disclaimer.

  2. Redistributions in binary form must reproduce the above copyright
  notice, this list of conditions and the following disclaimer in the
  documentation and/or other materials provided with the distribution.

  3. The names of its contributors may not be used to endorse or promote
  products derived from this software without specific prior written
  permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER
OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

Original algorithm for the implementation of rk_interval function from
Richard J. Wagner's implementation of the Mersenne Twister RNG, optimised by
Magnus Jonsson.

Constants used in the rk_double implementation by Isaku Wada.

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be included
in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
````

<a id="text-22"></a>

### numpy: numpy-2.5.4.dist-info/licenses/numpy/random/src/pcg64/LICENSE.md

Source: `numpy 2.5.4: numpy-2.5.4.dist-info/licenses/numpy/random/src/pcg64/LICENSE.md`. SHA-256: `e7d4f4fb20358f314210a892ae17351e04993813646f697ec387385ca2a36918`. UTF-8/LF bytes: 1154.

````text
# PCG64

## The MIT License

PCG Random Number Generation for C.

Copyright 2014 Melissa O'Neill <oneill@pcg-random.org>

Permission is hereby granted, free of charge, to any person obtaining 
a copy of this software and associated documentation files (the "Software"), 
to deal in the Software without restriction, including without limitation 
the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in 
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS 
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR 
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER 
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN 
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
````

<a id="text-23"></a>

### numpy: numpy-2.5.4.dist-info/licenses/numpy/random/src/philox/LICENSE.md

Source: `numpy 2.5.4: numpy-2.5.4.dist-info/licenses/numpy/random/src/philox/LICENSE.md`. SHA-256: `6f5828a57223d4cc7f8ea505a2623e7b978b242752c1515e355f46ba2cec1800`. UTF-8/LF bytes: 1509.

````text
# PHILOX

Copyright 2010-2012, D. E. Shaw Research.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

* Redistributions of source code must retain the above copyright
  notice, this list of conditions, and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright
  notice, this list of conditions, and the following disclaimer in the
  documentation and/or other materials provided with the distribution.

* Neither the name of D. E. Shaw Research nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
````

<a id="text-24"></a>

### numpy: numpy-2.5.4.dist-info/licenses/numpy/random/src/sfc64/LICENSE.md

Source: `numpy 2.5.4: numpy-2.5.4.dist-info/licenses/numpy/random/src/sfc64/LICENSE.md`. SHA-256: `9d4098846018319cd68e228ee6220361787f73bccbf00237a85e4fc9621b998f`. UTF-8/LF bytes: 1226.

````text
# SFC64

## The MIT License

Adapted from a C++ implementation of Chris Doty-Humphrey's SFC PRNG.

https://gist.github.com/imneme/f1f7821f07cf76504a97f6537c818083

Copyright (c) 2018 Melissa E. O'Neill

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
````

<a id="text-25"></a>

### numpy: numpy-2.5.4.dist-info/licenses/numpy/random/src/splitmix64/LICENSE.md

Source: `numpy 2.5.4: numpy-2.5.4.dist-info/licenses/numpy/random/src/splitmix64/LICENSE.md`. SHA-256: `268b0ca06759d31ea3ca68dd35f20e877916e927b1c2a835e4592a3c4354b1f9`. UTF-8/LF bytes: 332.

````text
# SPLITMIX64

Written in 2015 by Sebastiano Vigna (vigna@acm.org)

To the extent possible under law, the author has dedicated all copyright
and related and neighboring rights to this software to the public domain
worldwide. This software is distributed without any warranty.

See <http://creativecommons.org/publicdomain/zero/1.0/>.
````

<a id="text-26"></a>

### nvidia-cublas-cu12: nvidia_cublas_cu12-12.9.2.10.dist-info/licenses/License.txt

Source: `nvidia-cublas-cu12 12.9.2.10: nvidia_cublas_cu12-12.9.2.10.dist-info/licenses/License.txt`. SHA-256: `ad6f5853fba0ca0d159d0f58d49ae49830c2f8c93f7a92648b9ce90adb4c6ccd`. UTF-8/LF bytes: 59262.

````text
End User License Agreement
--------------------------


Preface
-------

The Software License Agreement in Chapter 1 and the Supplement
in Chapter 2 contain license terms and conditions that govern
the use of NVIDIA software. By accepting this agreement, you
agree to comply with all the terms and conditions applicable
to the product(s) included herein.


NVIDIA Driver


Description

This package contains the operating system driver and
fundamental system software components for NVIDIA GPUs.


NVIDIA CUDA Toolkit


Description

The NVIDIA CUDA Toolkit provides command-line and graphical
tools for building, debugging and optimizing the performance
of applications accelerated by NVIDIA GPUs, runtime and math
libraries, and documentation including programming guides,
user manuals, and API references.


Default Install Location of CUDA Toolkit

Windows platform:

%ProgramFiles%\NVIDIA GPU Computing Toolkit\CUDA\v#.#

Linux platform:

/usr/local/cuda-#.#

Mac platform:

/Developer/NVIDIA/CUDA-#.#


NVIDIA CUDA Samples


Description

This package includes over 100+ CUDA examples that demonstrate
various CUDA programming principles, and efficient CUDA
implementation of algorithms in specific application domains.


Default Install Location of CUDA Samples

Windows platform:

%ProgramData%\NVIDIA Corporation\CUDA Samples\v#.#

Linux platform:

/usr/local/cuda-#.#/samples

and

$HOME/NVIDIA_CUDA-#.#_Samples

Mac platform:

/Developer/NVIDIA/CUDA-#.#/samples


NVIDIA Nsight Visual Studio Edition (Windows only)


Description

NVIDIA Nsight Development Platform, Visual Studio Edition is a
development environment integrated into Microsoft Visual
Studio that provides tools for debugging, profiling, analyzing
and optimizing your GPU computing and graphics applications.


Default Install Location of Nsight Visual Studio Edition

Windows platform:

%ProgramFiles(x86)%\NVIDIA Corporation\Nsight Visual Studio Edition #.#


1. License Agreement for NVIDIA Software Development Kits
---------------------------------------------------------


Release Date: July 26, 2018
---------------------------


Important NoticeRead before downloading, installing,
copying or using the licensed software:
-------------------------------------------------------

This license agreement, including exhibits attached
("Agreement”) is a legal agreement between you and NVIDIA
Corporation ("NVIDIA") and governs your use of a NVIDIA
software development kit (“SDK”).

Each SDK has its own set of software and materials, but here
is a description of the types of items that may be included in
a SDK: source code, header files, APIs, data sets and assets
(examples include images, textures, models, scenes, videos,
native API input/output files), binary software, sample code,
libraries, utility programs, programming code and
documentation.

This Agreement can be accepted only by an adult of legal age
of majority in the country in which the SDK is used.

If you are entering into this Agreement on behalf of a company
or other legal entity, you represent that you have the legal
authority to bind the entity to this Agreement, in which case
“you” will mean the entity you represent.

If you don’t have the required age or authority to accept
this Agreement, or if you don’t accept all the terms and
conditions of this Agreement, do not download, install or use
the SDK.

You agree to use the SDK only for purposes that are permitted
by (a) this Agreement, and (b) any applicable law, regulation
or generally accepted practices or guidelines in the relevant
jurisdictions.


1.1. License


1.1.1. License Grant

Subject to the terms of this Agreement, NVIDIA hereby grants
you a non-exclusive, non-transferable license, without the
right to sublicense (except as expressly provided in this
Agreement) to:

  1. Install and use the SDK,

  2. Modify and create derivative works of sample source code
    delivered in the SDK, and

  3. Distribute those portions of the SDK that are identified
    in this Agreement as distributable, as incorporated in
    object code format into a software application that meets
    the distribution requirements indicated in this Agreement.


1.1.2. Distribution Requirements

These are the distribution requirements for you to exercise
the distribution grant:

  1. Your application must have material additional
    functionality, beyond the included portions of the SDK.

  2. The distributable portions of the SDK shall only be
    accessed by your application.

  3. The following notice shall be included in modifications
    and derivative works of sample source code distributed:
    “This software contains source code provided by NVIDIA
    Corporation.”

  4. Unless a developer tool is identified in this Agreement
    as distributable, it is delivered for your internal use
    only.

  5. The terms under which you distribute your application
    must be consistent with the terms of this Agreement,
    including (without limitation) terms relating to the
    license grant and license restrictions and protection of
    NVIDIA’s intellectual property rights. Additionally, you
    agree that you will protect the privacy, security and
    legal rights of your application users.

  6. You agree to notify NVIDIA in writing of any known or
    suspected distribution or use of the SDK not in compliance
    with the requirements of this Agreement, and to enforce
    the terms of your agreements with respect to distributed
    SDK.


1.1.3. Authorized Users

You may allow employees and contractors of your entity or of
your subsidiary(ies) to access and use the SDK from your
secure network to perform work on your behalf.

If you are an academic institution you may allow users
enrolled or employed by the academic institution to access and
use the SDK from your secure network.

You are responsible for the compliance with the terms of this
Agreement by your authorized users. If you become aware that
your authorized users didn’t follow the terms of this
Agreement, you agree to take reasonable steps to resolve the
non-compliance and prevent new occurrences.


1.1.4. Pre-Release SDK

The SDK versions identified as alpha, beta, preview or
otherwise as pre-release, may not be fully functional, may
contain errors or design flaws, and may have reduced or
different security, privacy, accessibility, availability, and
reliability standards relative to commercial versions of
NVIDIA software and materials. Use of a pre-release SDK may
result in unexpected results, loss of data, project delays or
other unpredictable damage or loss.

You may use a pre-release SDK at your own risk, understanding
that pre-release SDKs are not intended for use in production
or business-critical systems.

NVIDIA may choose not to make available a commercial version
of any pre-release SDK. NVIDIA may also choose to abandon
development and terminate the availability of a pre-release
SDK at any time without liability.


1.1.5. Updates

NVIDIA may, at its option, make available patches, workarounds
or other updates to this SDK. Unless the updates are provided
with their separate governing terms, they are deemed part of
the SDK licensed to you as provided in this Agreement. You
agree that the form and content of the SDK that NVIDIA
provides may change without prior notice to you. While NVIDIA
generally maintains compatibility between versions, NVIDIA may
in some cases make changes that introduce incompatibilities in
future versions of the SDK.


1.1.6. Third Party Licenses

The SDK may come bundled with, or otherwise include or be
distributed with, third party software licensed by a NVIDIA
supplier and/or open source software provided under an open
source license. Use of third party software is subject to the
third-party license terms, or in the absence of third party
terms, the terms of this Agreement. Copyright to third party
software is held by the copyright holders indicated in the
third-party software or license.


1.1.7. Reservation of Rights

NVIDIA reserves all rights, title, and interest in and to the
SDK, not expressly granted to you under this Agreement.


1.2. Limitations

The following license limitations apply to your use of the
SDK:

  1. You may not reverse engineer, decompile or disassemble,
    or remove copyright or other proprietary notices from any
    portion of the SDK or copies of the SDK.

  2. Except as expressly provided in this Agreement, you may
    not copy, sell, rent, sublicense, transfer, distribute,
    modify, or create derivative works of any portion of the
    SDK. For clarity, you may not distribute or sublicense the
    SDK as a stand-alone product.

  3. Unless you have an agreement with NVIDIA for this
    purpose, you may not indicate that an application created
    with the SDK is sponsored or endorsed by NVIDIA.

  4. You may not bypass, disable, or circumvent any
    encryption, security, digital rights management or
    authentication mechanism in the SDK.

  5. You may not use the SDK in any manner that would cause it
    to become subject to an open source software license. As
    examples, licenses that require as a condition of use,
    modification, and/or distribution that the SDK be:

      a. Disclosed or distributed in source code form;

      b. Licensed for the purpose of making derivative works;
        or

      c. Redistributable at no charge.

  6. Unless you have an agreement with NVIDIA for this
    purpose, you may not use the SDK with any system or
    application where the use or failure of the system or
    application can reasonably be expected to threaten or
    result in personal injury, death, or catastrophic loss.
    Examples include use in avionics, navigation, military,
    medical, life support or other life critical applications.
    NVIDIA does not design, test or manufacture the SDK for
    these critical uses and NVIDIA shall not be liable to you
    or any third party, in whole or in part, for any claims or
    damages arising from such uses.

  7. You agree to defend, indemnify and hold harmless NVIDIA
    and its affiliates, and their respective employees,
    contractors, agents, officers and directors, from and
    against any and all claims, damages, obligations, losses,
    liabilities, costs or debt, fines, restitutions and
    expenses (including but not limited to attorney’s fees
    and costs incident to establishing the right of
    indemnification) arising out of or related to your use of
    the SDK outside of the scope of this Agreement, or not in
    compliance with its terms.


1.3. Ownership

  1.  NVIDIA or its licensors hold all rights, title and
    interest in and to the SDK and its modifications and
    derivative works, including their respective intellectual
    property rights, subject to your rights described in this
    section. This SDK may include software and materials from
    NVIDIA’s licensors, and these licensors are intended
    third party beneficiaries that may enforce this Agreement
    with respect to their intellectual property rights.

  2.  You hold all rights, title and interest in and to your
    applications and your derivative works of the sample
    source code delivered in the SDK, including their
    respective intellectual property rights, subject to
    NVIDIA’s rights described in this section.

  3. You may, but don’t have to, provide to NVIDIA
    suggestions, feature requests or other feedback regarding
    the SDK, including possible enhancements or modifications
    to the SDK. For any feedback that you voluntarily provide,
    you hereby grant NVIDIA and its affiliates a perpetual,
    non-exclusive, worldwide, irrevocable license to use,
    reproduce, modify, license, sublicense (through multiple
    tiers of sublicensees), and distribute (through multiple
    tiers of distributors) it without the payment of any
    royalties or fees to you. NVIDIA will use feedback at its
    choice. NVIDIA is constantly looking for ways to improve
    its products, so you may send feedback to NVIDIA through
    the developer portal at https://developer.nvidia.com.


1.4. No Warranties

THE SDK IS PROVIDED BY NVIDIA “AS IS” AND “WITH ALL
FAULTS.” TO THE MAXIMUM EXTENT PERMITTED BY LAW, NVIDIA AND
ITS AFFILIATES EXPRESSLY DISCLAIM ALL WARRANTIES OF ANY KIND
OR NATURE, WHETHER EXPRESS, IMPLIED OR STATUTORY, INCLUDING,
BUT NOT LIMITED TO, ANY WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE, TITLE, NON-INFRINGEMENT, OR THE
ABSENCE OF ANY DEFECTS THEREIN, WHETHER LATENT OR PATENT. NO
WARRANTY IS MADE ON THE BASIS OF TRADE USAGE, COURSE OF
DEALING OR COURSE OF TRADE.


1.5. Limitation of Liability

TO THE MAXIMUM EXTENT PERMITTED BY LAW, NVIDIA AND ITS
AFFILIATES SHALL NOT BE LIABLE FOR ANY SPECIAL, INCIDENTAL,
PUNITIVE OR CONSEQUENTIAL DAMAGES, OR ANY LOST PROFITS, LOSS
OF USE, LOSS OF DATA OR LOSS OF GOODWILL, OR THE COSTS OF
PROCURING SUBSTITUTE PRODUCTS, ARISING OUT OF OR IN CONNECTION
WITH THIS AGREEMENT OR THE USE OR PERFORMANCE OF THE SDK,
WHETHER SUCH LIABILITY ARISES FROM ANY CLAIM BASED UPON BREACH
OF CONTRACT, BREACH OF WARRANTY, TORT (INCLUDING NEGLIGENCE),
PRODUCT LIABILITY OR ANY OTHER CAUSE OF ACTION OR THEORY OF
LIABILITY. IN NO EVENT WILL NVIDIA’S AND ITS AFFILIATES
TOTAL CUMULATIVE LIABILITY UNDER OR ARISING OUT OF THIS
AGREEMENT EXCEED US$10.00. THE NATURE OF THE LIABILITY OR THE
NUMBER OF CLAIMS OR SUITS SHALL NOT ENLARGE OR EXTEND THIS
LIMIT.

These exclusions and limitations of liability shall apply
regardless if NVIDIA or its affiliates have been advised of
the possibility of such damages, and regardless of whether a
remedy fails its essential purpose. These exclusions and
limitations of liability form an essential basis of the
bargain between the parties, and, absent any of these
exclusions or limitations of liability, the provisions of this
Agreement, including, without limitation, the economic terms,
would be substantially different.


1.6. Termination

  1. This Agreement will continue to apply until terminated by
    either you or NVIDIA as described below.

  2. If you want to terminate this Agreement, you may do so by
    stopping to use the SDK.

  3. NVIDIA may, at any time, terminate this Agreement if:

      a. (i) you fail to comply with any term of this
        Agreement and the non-compliance is not fixed within
        thirty (30) days following notice from NVIDIA (or
        immediately if you violate NVIDIA’s intellectual
        property rights);

      b. (ii) you commence or participate in any legal
        proceeding against NVIDIA with respect to the SDK; or

      c. (iii) NVIDIA decides to no longer provide the SDK in
        a country or, in NVIDIA’s sole discretion, the
        continued use of it is no longer commercially viable.

  4. Upon any termination of this Agreement, you agree to
    promptly discontinue use of the SDK and destroy all copies
    in your possession or control. Your prior distributions in
    accordance with this Agreement are not affected by the
    termination of this Agreement. Upon written request, you
    will certify in writing that you have complied with your
    commitments under this section. Upon any termination of
    this Agreement all provisions survive except for the
    license grant provisions.


1.7. General

If you wish to assign this Agreement or your rights and
obligations, including by merger, consolidation, dissolution
or operation of law, contact NVIDIA to ask for permission. Any
attempted assignment not approved by NVIDIA in writing shall
be void and of no effect. NVIDIA may assign, delegate or
transfer this Agreement and its rights and obligations, and if
to a non-affiliate you will be notified.

You agree to cooperate with NVIDIA and provide reasonably
requested information to verify your compliance with this
Agreement.

This Agreement will be governed in all respects by the laws of
the United States and of the State of Delaware as those laws
are applied to contracts entered into and performed entirely
within Delaware by Delaware residents, without regard to the
conflicts of laws principles. The United Nations Convention on
Contracts for the International Sale of Goods is specifically
disclaimed. You agree to all terms of this Agreement in the
English language.

The state or federal courts residing in Santa Clara County,
California shall have exclusive jurisdiction over any dispute
or claim arising out of this Agreement. Notwithstanding this,
you agree that NVIDIA shall still be allowed to apply for
injunctive remedies or an equivalent type of urgent legal
relief in any jurisdiction.

If any court of competent jurisdiction determines that any
provision of this Agreement is illegal, invalid or
unenforceable, such provision will be construed as limited to
the extent necessary to be consistent with and fully
enforceable under the law and the remaining provisions will
remain in full force and effect. Unless otherwise specified,
remedies are cumulative.

Each party acknowledges and agrees that the other is an
independent contractor in the performance of this Agreement.

The SDK has been developed entirely at private expense and is
“commercial items” consisting of “commercial computer
software” and “commercial computer software
documentation” provided with RESTRICTED RIGHTS. Use,
duplication or disclosure by the U.S. Government or a U.S.
Government subcontractor is subject to the restrictions in
this Agreement pursuant to DFARS 227.7202-3(a) or as set forth
in subparagraphs (c)(1) and (2) of the Commercial Computer
Software - Restricted Rights clause at FAR 52.227-19, as
applicable. Contractor/manufacturer is NVIDIA, 2788 San Tomas
Expressway, Santa Clara, CA 95051.

The SDK is subject to United States export laws and
regulations. You agree that you will not ship, transfer or
export the SDK into any country, or use the SDK in any manner,
prohibited by the United States Bureau of Industry and
Security or economic sanctions regulations administered by the
U.S. Department of Treasury’s Office of Foreign Assets
Control (OFAC), or any applicable export laws, restrictions or
regulations. These laws include restrictions on destinations,
end users and end use. By accepting this Agreement, you
confirm that you are not a resident or citizen of any country
currently embargoed by the U.S. and that you are not otherwise
prohibited from receiving the SDK.

Any notice delivered by NVIDIA to you under this Agreement
will be delivered via mail, email or fax. You agree that any
notices that NVIDIA sends you electronically will satisfy any
legal communication requirements. Please direct your legal
notices or other correspondence to NVIDIA Corporation, 2788
San Tomas Expressway, Santa Clara, California 95051, United
States of America, Attention: Legal Department.

This Agreement and any exhibits incorporated into this
Agreement constitute the entire agreement of the parties with
respect to the subject matter of this Agreement and supersede
all prior negotiations or documentation exchanged between the
parties relating to this SDK license. Any additional and/or
conflicting terms on documents issued by you are null, void,
and invalid. Any amendment or waiver under this Agreement
shall be in writing and signed by representatives of both
parties.


2. CUDA Toolkit Supplement to Software License Agreement for
NVIDIA Software Development Kits
------------------------------------------------------------


Release date: August 16, 2018
-----------------------------

The terms in this supplement govern your use of the NVIDIA
CUDA Toolkit SDK under the terms of your license agreement
(“Agreement”) as modified by this supplement. Capitalized
terms used but not defined below have the meaning assigned to
them in the Agreement.

This supplement is an exhibit to the Agreement and is
incorporated as an integral part of the Agreement. In the
event of conflict between the terms in this supplement and the
terms in the Agreement, the terms in this supplement govern.


2.1. License Scope

The SDK is licensed for you to develop applications only for
use in systems with NVIDIA GPUs.


2.2. Distribution

The portions of the SDK that are distributable under the
Agreement are listed in Attachment A.


2.3. Operating Systems

Those portions of the SDK designed exclusively for use on the
Linux or FreeBSD operating systems, or other operating systems
derived from the source code to these operating systems, may
be copied and redistributed for use in accordance with this
Agreement, provided that the object code files are not
modified in any way (except for unzipping of compressed
files).


2.4. Audio and Video Encoders and Decoders

You acknowledge and agree that it is your sole responsibility
to obtain any additional third-party licenses required to
make, have made, use, have used, sell, import, and offer for
sale your products or services that include or incorporate any
third-party software and content relating to audio and/or
video encoders and decoders from, including but not limited
to, Microsoft, Thomson, Fraunhofer IIS, Sisvel S.p.A.,
MPEG-LA, and Coding Technologies. NVIDIA does not grant to you
under this Agreement any necessary patent or other rights with
respect to any audio and/or video encoders and decoders.


2.5. Licensing

If the distribution terms in this Agreement are not suitable
for your organization, or for any questions regarding this
Agreement, please contact NVIDIA at
nvidia-compute-license-questions@nvidia.com.


2.6. Attachment A

The following portions of the SDK are distributable under the
Agreement:

Component

CUDA Runtime

Windows

cudart.dll, cudart_static.lib, cudadevrt.lib

Mac OSX

libcudart.dylib, libcudart_static.a, libcudadevrt.a

Linux

libcudart.so, libcudart_static.a, libcudadevrt.a

Android

libcudart.so, libcudart_static.a, libcudadevrt.a

Component

CUDA FFT Library

Windows

cufft.dll, cufftw.dll, cufft.lib, cufftw.lib

Mac OSX

libcufft.dylib, libcufft_static.a, libcufftw.dylib,
libcufftw_static.a

Linux

libcufft.so, libcufft_static.a, libcufftw.so,
libcufftw_static.a

Android

libcufft.so, libcufft_static.a, libcufftw.so,
libcufftw_static.a

Component

CUDA BLAS Library

Windows

cublas.dll, cublasLt.dll

Mac OSX

libcublas.dylib, libcublasLt.dylib, libcublas_static.a,
libcublasLt_static.a

Linux

libcublas.so, libcublasLt.so, libcublas_static.a,
libcublasLt_static.a

Android

libcublas.so, libcublasLt.so, libcublas_static.a,
libcublasLt_static.a

Component

NVIDIA "Drop-in" BLAS Library

Windows

nvblas.dll

Mac OSX

libnvblas.dylib

Linux

libnvblas.so

Component

CUDA Sparse Matrix Library

Windows

cusparse.dll, cusparse.lib

Mac OSX

libcusparse.dylib, libcusparse_static.a

Linux

libcusparse.so, libcusparse_static.a

Android

libcusparse.so, libcusparse_static.a

Component

CUDA Linear Solver Library

Windows

cusolver.dll, cusolver.lib

Mac OSX

libcusolver.dylib, libcusolver_static.a

Linux

libcusolver.so, libcusolver_static.a

Android

libcusolver.so, libcusolver_static.a

Component

CUDA Random Number Generation Library

Windows

curand.dll, curand.lib

Mac OSX

libcurand.dylib, libcurand_static.a

Linux

libcurand.so, libcurand_static.a

Android

libcurand.so, libcurand_static.a

Component

CUDA Accelerated Graph Library

Component

NVIDIA Performance Primitives Library

Windows

nppc.dll, nppc.lib, nppial.dll, nppial.lib, nppicc.dll,
nppicc.lib, nppicom.dll, nppicom.lib, nppidei.dll,
nppidei.lib, nppif.dll, nppif.lib, nppig.dll, nppig.lib,
nppim.dll, nppim.lib, nppist.dll, nppist.lib, nppisu.dll,
nppisu.lib, nppitc.dll, nppitc.lib, npps.dll, npps.lib

Mac OSX

libnppc.dylib, libnppc_static.a, libnppial.dylib,
libnppial_static.a, libnppicc.dylib, libnppicc_static.a,
libnppicom.dylib, libnppicom_static.a, libnppidei.dylib,
libnppidei_static.a, libnppif.dylib, libnppif_static.a,
libnppig.dylib, libnppig_static.a, libnppim.dylib,
libnppisu_static.a, libnppitc.dylib, libnppitc_static.a,
libnpps.dylib, libnpps_static.a

Linux

libnppc.so, libnppc_static.a, libnppial.so,
libnppial_static.a, libnppicc.so, libnppicc_static.a,
libnppicom.so, libnppicom_static.a, libnppidei.so,
libnppidei_static.a, libnppif.so, libnppif_static.a
libnppig.so, libnppig_static.a, libnppim.so,
libnppim_static.a, libnppist.so, libnppist_static.a,
libnppisu.so, libnppisu_static.a, libnppitc.so
libnppitc_static.a, libnpps.so, libnpps_static.a

Android

libnppc.so, libnppc_static.a, libnppial.so,
libnppial_static.a, libnppicc.so, libnppicc_static.a,
libnppicom.so, libnppicom_static.a, libnppidei.so,
libnppidei_static.a, libnppif.so, libnppif_static.a
libnppig.so, libnppig_static.a, libnppim.so,
libnppim_static.a, libnppist.so, libnppist_static.a,
libnppisu.so, libnppisu_static.a, libnppitc.so
libnppitc_static.a, libnpps.so, libnpps_static.a

Component

NVIDIA JPEG Library

Linux

libnvjpeg.so, libnvjpeg_static.a

Component

Internal common library required for statically linking to
cuBLAS, cuSPARSE, cuFFT, cuRAND, nvJPEG and NPP

Mac OSX

libculibos.a

Linux

libculibos.a

Component

NVIDIA Runtime Compilation Library and Header

All

nvrtc.h

Windows

nvrtc.dll, nvrtc-builtins.dll

Mac OSX

libnvrtc.dylib, libnvrtc-builtins.dylib

Linux

libnvrtc.so, libnvrtc-builtins.so

Component

NVIDIA Optimizing Compiler Library

Windows

nvvm.dll

Mac OSX

libnvvm.dylib

Linux

libnvvm.so

Component

NVIDIA Common Device Math Functions Library

Windows

libdevice.10.bc

Mac OSX

libdevice.10.bc

Linux

libdevice.10.bc

Component

CUDA Occupancy Calculation Header Library

All

cuda_occupancy.h

Component

CUDA Half Precision Headers

All

cuda_fp16.h, cuda_fp16.hpp

Component

CUDA Profiling Tools Interface (CUPTI) Library

Windows

cupti.dll

Mac OSX

libcupti.dylib

Linux

libcupti.so

Component

NVIDIA Tools Extension Library

Windows

nvToolsExt.dll, nvToolsExt.lib

Mac OSX

libnvToolsExt.dylib

Linux

libnvToolsExt.so

Component

NVIDIA CUDA Driver Libraries

Linux

libcuda.so, libnvidia-fatbinaryloader.so,
libnvidia-ptxjitcompiler.so

The NVIDIA CUDA Driver Libraries are only distributable in
applications that meet this criteria:

  1. The application was developed starting from a NVIDIA CUDA
    container obtained from Docker Hub or the NVIDIA GPU
    Cloud, and

  2. The resulting application is packaged as a Docker
    container and distributed to users on Docker Hub or the
    NVIDIA GPU Cloud only.


2.7. Attachment B


Additional Licensing Obligations

The following third party components included in the SOFTWARE
are licensed to Licensee pursuant to the following terms and
conditions:

  1. Licensee's use of the GDB third party component is
    subject to the terms and conditions of GNU GPL v3:

    This product includes copyrighted third-party software licensed
    under the terms of the GNU General Public License v3 ("GPL v3").
    All third-party software packages are copyright by their respective
    authors. GPL v3 terms and conditions are hereby incorporated into
    the Agreement by this reference:     http://www.gnu.org/licenses/gpl.txt

    Consistent with these licensing requirements, the software
    listed below is provided under the terms of the specified
    open source software licenses. To obtain source code for
    software provided under licenses that require
    redistribution of source code, including the GNU General
    Public License (GPL) and GNU Lesser General Public License
    (LGPL), contact oss-requests@nvidia.com. This offer is
    valid for a period of three (3) years from the date of the
    distribution of this product by NVIDIA CORPORATION.

    Component          License
    CUDA-GDB           GPL v3

  2. Licensee represents and warrants that any and all third
    party licensing and/or royalty payment obligations in
    connection with Licensee's use of the H.264 video codecs
    are solely the responsibility of Licensee.

  3. Licensee's use of the Thrust library is subject to the
    terms and conditions of the Apache License Version 2.0.
    All third-party software packages are copyright by their
    respective authors. Apache License Version 2.0 terms and
    conditions are hereby incorporated into the Agreement by
    this reference.
    http://www.apache.org/licenses/LICENSE-2.0.html

    In addition, Licensee acknowledges the following notice:
    Thrust includes source code from the Boost Iterator,
    Tuple, System, and Random Number libraries.

    Boost Software License - Version 1.0 - August 17th, 2003
    . . . .

    Permission is hereby granted, free of charge, to any person or
    organization obtaining a copy of the software and accompanying
    documentation covered by this license (the "Software") to use,
    reproduce, display, distribute, execute, and transmit the Software,
    and to prepare derivative works of the Software, and to permit
    third-parties to whom the Software is furnished to do so, all
    subject to the following:

    The copyright notices in the Software and this entire statement,
    including the above license grant, this restriction and the following
    disclaimer, must be included in all copies of the Software, in whole
    or in part, and all derivative works of the Software, unless such
    copies or derivative works are solely in the form of machine-executable
    object code generated by a source language processor.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
    MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, TITLE AND
    NON-INFRINGEMENT. IN NO EVENT SHALL THE COPYRIGHT HOLDERS OR
    ANYONE DISTRIBUTING THE SOFTWARE BE LIABLE FOR ANY DAMAGES OR
    OTHER LIABILITY, WHETHER IN CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
    OTHER DEALINGS IN THE SOFTWARE.

  4. Licensee's use of the LLVM third party component is
    subject to the following terms and conditions:

    ======================================================
    LLVM Release License
    ======================================================
    University of Illinois/NCSA
    Open Source License

    Copyright (c) 2003-2010 University of Illinois at Urbana-Champaign.
    All rights reserved.

    Developed by:

        LLVM Team

        University of Illinois at Urbana-Champaign

        http://llvm.org

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to
    deal with the Software without restriction, including without limitation the
    rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
    sell copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    *  Redistributions of source code must retain the above copyright notice,
       this list of conditions and the following disclaimers.

    *  Redistributions in binary form must reproduce the above copyright
       notice, this list of conditions and the following disclaimers in the
       documentation and/or other materials provided with the distribution.

    *  Neither the names of the LLVM Team, University of Illinois at Urbana-
       Champaign, nor the names of its contributors may be used to endorse or
       promote products derived from this Software without specific prior
       written permission.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
    THE CONTRIBUTORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
    OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
    ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
    DEALINGS WITH THE SOFTWARE.

  5. Licensee's use (e.g. nvprof) of the PCRE third party
    component is subject to the following terms and
    conditions:

    ------------
    PCRE LICENCE
    ------------
    PCRE is a library of functions to support regular expressions whose syntax
    and semantics are as close as possible to those of the Perl 5 language.
    Release 8 of PCRE is distributed under the terms of the "BSD" licence, as
    specified below. The documentation for PCRE, supplied in the "doc"
    directory, is distributed under the same terms as the software itself. The
    basic library functions are written in C and are freestanding. Also
    included in the distribution is a set of C++ wrapper functions, and a just-
    in-time compiler that can be used to optimize pattern matching. These are
    both optional features that can be omitted when the library is built.

    THE BASIC LIBRARY FUNCTIONS
    ---------------------------
    Written by:       Philip Hazel
    Email local part: ph10
    Email domain:     cam.ac.uk
    University of Cambridge Computing Service,
    Cambridge, England.
    Copyright (c) 1997-2012 University of Cambridge
    All rights reserved.

    PCRE JUST-IN-TIME COMPILATION SUPPORT
    -------------------------------------
    Written by:       Zoltan Herczeg
    Email local part: hzmester
    Emain domain:     freemail.hu
    Copyright(c) 2010-2012 Zoltan Herczeg
    All rights reserved.

    STACK-LESS JUST-IN-TIME COMPILER
    --------------------------------
    Written by:       Zoltan Herczeg
    Email local part: hzmester
    Emain domain:     freemail.hu
    Copyright(c) 2009-2012 Zoltan Herczeg
    All rights reserved.

    THE C++ WRAPPER FUNCTIONS
    -------------------------
    Contributed by:   Google Inc.
    Copyright (c) 2007-2012, Google Inc.
    All rights reserved.

    THE "BSD" LICENCE
    -----------------
    Redistribution and use in source and binary forms, with or without
    modification, are permitted provided that the following conditions are met:

      * Redistributions of source code must retain the above copyright notice,
        this list of conditions and the following disclaimer.

      * Redistributions in binary form must reproduce the above copyright
        notice, this list of conditions and the following disclaimer in the
        documentation and/or other materials provided with the distribution.

      * Neither the name of the University of Cambridge nor the name of Google
        Inc. nor the names of their contributors may be used to endorse or
        promote products derived from this software without specific prior
        written permission.

    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
    AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
    IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
    ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
    LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
    CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
    SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
    INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
    CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
    ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
    POSSIBILITY OF SUCH DAMAGE.

  6. Some of the cuBLAS library routines were written by or
    derived from code written by Vasily Volkov and are subject
    to the Modified Berkeley Software Distribution License as
    follows:

    Copyright (c) 2007-2009, Regents of the University of California

    All rights reserved.

    Redistribution and use in source and binary forms, with or without
    modification, are permitted provided that the following conditions are
    met:
        * Redistributions of source code must retain the above copyright
          notice, this list of conditions and the following disclaimer.
        * Redistributions in binary form must reproduce the above
          copyright notice, this list of conditions and the following
          disclaimer in the documentation and/or other materials provided
          with the distribution.
        * Neither the name of the University of California, Berkeley nor
          the names of its contributors may be used to endorse or promote
          products derived from this software without specific prior
          written permission.

    THIS SOFTWARE IS PROVIDED BY THE AUTHOR "AS IS" AND ANY EXPRESS OR
    IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
    WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
    DISCLAIMED. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT,
    INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
    (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
    SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
    HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
    STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING
    IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
    POSSIBILITY OF SUCH DAMAGE.

  7. Some of the cuBLAS library routines were written by or
    derived from code written by Davide Barbieri and are
    subject to the Modified Berkeley Software Distribution
    License as follows:

    Copyright (c) 2008-2009 Davide Barbieri @ University of Rome Tor Vergata.

    All rights reserved.

    Redistribution and use in source and binary forms, with or without
    modification, are permitted provided that the following conditions are
    met:
        * Redistributions of source code must retain the above copyright
          notice, this list of conditions and the following disclaimer.
        * Redistributions in binary form must reproduce the above
          copyright notice, this list of conditions and the following
          disclaimer in the documentation and/or other materials provided
          with the distribution.
        * The name of the author may not be used to endorse or promote
          products derived from this software without specific prior
          written permission.

    THIS SOFTWARE IS PROVIDED BY THE AUTHOR "AS IS" AND ANY EXPRESS OR
    IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
    WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
    DISCLAIMED. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT,
    INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
    (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
    SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
    HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
    STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING
    IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
    POSSIBILITY OF SUCH DAMAGE.

  8. Some of the cuBLAS library routines were derived from
    code developed by the University of Tennessee and are
    subject to the Modified Berkeley Software Distribution
    License as follows:

    Copyright (c) 2010 The University of Tennessee.

    All rights reserved.

    Redistribution and use in source and binary forms, with or without
    modification, are permitted provided that the following conditions are
    met:
        * Redistributions of source code must retain the above copyright
          notice, this list of conditions and the following disclaimer.
        * Redistributions in binary form must reproduce the above
          copyright notice, this list of conditions and the following
          disclaimer listed in this license in the documentation and/or
          other materials provided with the distribution.
        * Neither the name of the copyright holders nor the names of its
          contributors may be used to endorse or promote products derived
          from this software without specific prior written permission.

    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
    "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
    LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
    A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
    OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
    SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
    LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
    DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
    THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
    (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
    OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

  9. Some of the cuBLAS library routines were written by or
    derived from code written by Jonathan Hogg and are subject
    to the Modified Berkeley Software Distribution License as
    follows:

    Copyright (c) 2012, The Science and Technology Facilities Council (STFC).

    All rights reserved.

    Redistribution and use in source and binary forms, with or without
    modification, are permitted provided that the following conditions are
    met:
        * Redistributions of source code must retain the above copyright
          notice, this list of conditions and the following disclaimer.
        * Redistributions in binary form must reproduce the above
          copyright notice, this list of conditions and the following
          disclaimer in the documentation and/or other materials provided
          with the distribution.
        * Neither the name of the STFC nor the names of its contributors
          may be used to endorse or promote products derived from this
          software without specific prior written permission.

    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
    "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
    LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
    A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE STFC BE
    LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
    CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
    SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
    BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
    WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
    OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN
    IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

  10. Some of the cuBLAS library routines were written by or
    derived from code written by Ahmad M. Abdelfattah, David
    Keyes, and Hatem Ltaief, and are subject to the Apache
    License, Version 2.0, as follows:

     -- (C) Copyright 2013 King Abdullah University of Science and Technology
      Authors:
      Ahmad Abdelfattah (ahmad.ahmad@kaust.edu.sa)
      David Keyes (david.keyes@kaust.edu.sa)
      Hatem Ltaief (hatem.ltaief@kaust.edu.sa)

      Redistribution  and  use  in  source and binary forms, with or without
      modification,  are  permitted  provided  that the following conditions
      are met:

      * Redistributions  of  source  code  must  retain  the above copyright
        notice,  this  list  of  conditions  and  the  following  disclaimer.
      * Redistributions  in  binary  form must reproduce the above copyright
        notice,  this list of conditions and the following disclaimer in the
        documentation  and/or other materials provided with the distribution.
      * Neither  the  name of the King Abdullah University of Science and
        Technology nor the names of its contributors may be used to endorse
        or promote products derived from this software without specific prior
        written permission.

      THIS  SOFTWARE  IS  PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
      ``AS IS''  AND  ANY  EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
      LIMITED  TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
      A  PARTICULAR  PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
      HOLDERS OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
      SPECIAL,  EXEMPLARY,  OR  CONSEQUENTIAL  DAMAGES  (INCLUDING,  BUT NOT
      LIMITED  TO,  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
      DATA,  OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
      THEORY  OF  LIABILITY,  WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
      (INCLUDING  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
      OF  THIS  SOFTWARE,  EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE

  11. Some of the cuSPARSE library routines were written by or
    derived from code written by Li-Wen Chang and are subject
    to the NCSA Open Source License as follows:

    Copyright (c) 2012, University of Illinois.

    All rights reserved.

    Developed by: IMPACT Group, University of Illinois, http://impact.crhc.illinois.edu

    Permission is hereby granted, free of charge, to any person obtaining
    a copy of this software and associated documentation files (the
    "Software"), to deal with the Software without restriction, including
    without limitation the rights to use, copy, modify, merge, publish,
    distribute, sublicense, and/or sell copies of the Software, and to
    permit persons to whom the Software is furnished to do so, subject to
    the following conditions:
        * Redistributions of source code must retain the above copyright
          notice, this list of conditions and the following disclaimer.
        * Redistributions in binary form must reproduce the above
          copyright notice, this list of conditions and the following
          disclaimers in the documentation and/or other materials provided
          with the distribution.
        * Neither the names of IMPACT Group, University of Illinois, nor
          the names of its contributors may be used to endorse or promote
          products derived from this Software without specific prior
          written permission.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
    MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE CONTRIBUTORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
    IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR
    IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS WITH THE
    SOFTWARE.

  12. Some of the cuRAND library routines were written by or
    derived from code written by Mutsuo Saito and Makoto
    Matsumoto and are subject to the following license:

    Copyright (c) 2009, 2010 Mutsuo Saito, Makoto Matsumoto and Hiroshima
    University. All rights reserved.

    Copyright (c) 2011 Mutsuo Saito, Makoto Matsumoto, Hiroshima
    University and University of Tokyo.  All rights reserved.

    Redistribution and use in source and binary forms, with or without
    modification, are permitted provided that the following conditions are
    met:
        * Redistributions of source code must retain the above copyright
          notice, this list of conditions and the following disclaimer.
        * Redistributions in binary form must reproduce the above
          copyright notice, this list of conditions and the following
          disclaimer in the documentation and/or other materials provided
          with the distribution.
        * Neither the name of the Hiroshima University nor the names of
          its contributors may be used to endorse or promote products
          derived from this software without specific prior written
          permission.

    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
    "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
    LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
    A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
    OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
    SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
    LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
    DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
    THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
    (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
    OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

  13. Some of the cuRAND library routines were derived from
    code developed by D. E. Shaw Research and are subject to
    the following license:

    Copyright 2010-2011, D. E. Shaw Research.

    All rights reserved.

    Redistribution and use in source and binary forms, with or without
    modification, are permitted provided that the following conditions are
    met:
        * Redistributions of source code must retain the above copyright
          notice, this list of conditions, and the following disclaimer.
        * Redistributions in binary form must reproduce the above
          copyright notice, this list of conditions, and the following
          disclaimer in the documentation and/or other materials provided
          with the distribution.
        * Neither the name of D. E. Shaw Research nor the names of its
          contributors may be used to endorse or promote products derived
          from this software without specific prior written permission.

    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
    "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
    LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
    A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
    OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
    SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
    LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
    DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
    THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
    (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
    OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

  14. Some of the Math library routines were written by or
    derived from code developed by Norbert Juffa and are
    subject to the following license:

    Copyright (c) 2015-2017, Norbert Juffa
    All rights reserved.

    Redistribution and use in source and binary forms, with or without
    modification, are permitted provided that the following conditions
    are met:

    1. Redistributions of source code must retain the above copyright
       notice, this list of conditions and the following disclaimer.

    2. Redistributions in binary form must reproduce the above copyright
       notice, this list of conditions and the following disclaimer in the
       documentation and/or other materials provided with the distribution.

    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
    "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
    LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
    A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
    HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
    SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
    LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
    DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
    THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
    (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
    OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

  15. Licensee's use of the lz4 third party component is
    subject to the following terms and conditions:

    Copyright (C) 2011-2013, Yann Collet.
    BSD 2-Clause License (http://www.opensource.org/licenses/bsd-license.php)

    Redistribution and use in source and binary forms, with or without
    modification, are permitted provided that the following conditions are
    met:

        * Redistributions of source code must retain the above copyright
    notice, this list of conditions and the following disclaimer.
        * Redistributions in binary form must reproduce the above
    copyright notice, this list of conditions and the following disclaimer
    in the documentation and/or other materials provided with the
    distribution.

    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
    "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
    LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
    A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
    OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
    SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
    LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
    DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
    THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
    (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
    OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

  16. The NPP library uses code from the Boost Math Toolkit,
    and is subject to the following license:

    Boost Software License - Version 1.0 - August 17th, 2003
    . . . .

    Permission is hereby granted, free of charge, to any person or
    organization obtaining a copy of the software and accompanying
    documentation covered by this license (the "Software") to use,
    reproduce, display, distribute, execute, and transmit the Software,
    and to prepare derivative works of the Software, and to permit
    third-parties to whom the Software is furnished to do so, all
    subject to the following:

    The copyright notices in the Software and this entire statement,
    including the above license grant, this restriction and the following
    disclaimer, must be included in all copies of the Software, in whole
    or in part, and all derivative works of the Software, unless such
    copies or derivative works are solely in the form of machine-executable
    object code generated by a source language processor.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
    MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, TITLE AND
    NON-INFRINGEMENT. IN NO EVENT SHALL THE COPYRIGHT HOLDERS OR
    ANYONE DISTRIBUTING THE SOFTWARE BE LIABLE FOR ANY DAMAGES OR
    OTHER LIABILITY, WHETHER IN CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
    OTHER DEALINGS IN THE SOFTWARE.

  17. Portions of the Nsight Eclipse Edition is subject to the
    following license:

    The Eclipse Foundation makes available all content in this plug-in
    ("Content"). Unless otherwise indicated below, the Content is provided
    to you under the terms and conditions of the Eclipse Public License
    Version 1.0 ("EPL"). A copy of the EPL is available at http://
    www.eclipse.org/legal/epl-v10.html. For purposes of the EPL, "Program"
    will mean the Content.

    If you did not receive this Content directly from the Eclipse
    Foundation, the Content is being redistributed by another party
    ("Redistributor") and different terms and conditions may apply to your
    use of any object code in the Content. Check the Redistributor's
    license that was provided with the Content. If no such license exists,
    contact the Redistributor. Unless otherwise indicated below, the terms
    and conditions of the EPL still apply to any source code in the
    Content and such source code may be obtained at http://www.eclipse.org.

  18. Some of the cuBLAS library routines uses code from
    OpenAI, which is subject to the following license:

    License URL
    https://github.com/openai/openai-gemm/blob/master/LICENSE

    License Text
    The MIT License

    Copyright (c) 2016 OpenAI (http://openai.com), 2016 Google Inc.

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in
    all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
    THE SOFTWARE.

  19. Licensee's use of the Visual Studio Setup Configuration
    Samples is subject to the following license:

    The MIT License (MIT)
    Copyright (C) Microsoft Corporation. All rights reserved.

    Permission is hereby granted, free of charge, to any person
    obtaining a copy of this software and associated documentation
    files (the "Software"), to deal in the Software without restriction,
    including without limitation the rights to use, copy, modify, merge,
    publish, distribute, sublicense, and/or sell copies of the Software,
    and to permit persons to whom the Software is furnished to do so,
    subject to the following conditions:

    The above copyright notice and this permission notice shall be included
    in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
    OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

  20. Licensee's use of linmath.h header for CPU functions for
    GL vector/matrix operations from lunarG is subject to the
    Apache License Version 2.0.

  21. The DX12-CUDA sample uses the d3dx12.h header, which is
    subject to the MIT license .

-----------------
````

<a id="text-27"></a>

### pillow: pillow-12.3.0.dist-info/licenses/LICENSE

Source: `pillow 12.3.0: pillow-12.3.0.dist-info/licenses/LICENSE`. SHA-256: `51ed379cf673c9676b7fa7e1bedbfc5d4ad63caac4f6f99eeec5ccab50c3e0ef`. UTF-8/LF bytes: 76435.

````text
The Python Imaging Library (PIL) is

    Copyright © 1997-2011 by Secret Labs AB
    Copyright © 1995-2011 by Fredrik Lundh and contributors

Pillow is the friendly PIL fork. It is

    Copyright © 2010 by Jeffrey 'Alex' Clark and contributors

Like PIL, Pillow is licensed under the open source MIT-CMU License:

By obtaining, using, and/or copying this software and/or its associated
documentation, you agree that you have read, understood, and will comply
with the following terms and conditions:

Permission to use, copy, modify and distribute this software and its
documentation for any purpose and without fee is hereby granted,
provided that the above copyright notice appears in all copies, and that
both that copyright notice and this permission notice appear in supporting
documentation, and that the name of Secret Labs AB or the author not be
used in advertising or publicity pertaining to distribution of the software
without specific, written prior permission.

SECRET LABS AB AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS
SOFTWARE, INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS.
IN NO EVENT SHALL SECRET LABS AB OR THE AUTHOR BE LIABLE FOR ANY SPECIAL,
INDIRECT OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE
OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
PERFORMANCE OF THIS SOFTWARE.

===== brotli-1.2.0 =====

Copyright (c) 2009, 2010, 2013-2016 by the Brotli Authors.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

===== freetype-2.14.3 =====

FREETYPE LICENSES
-----------------

The FreeType  2 font  engine is  copyrighted work  and cannot  be used
legally without  a software  license.  In order  to make  this project
usable to  a vast majority of  developers, we distribute it  under two
mutually exclusive open-source licenses.

This means that *you* must choose  *one* of the two licenses described
below, then obey all its terms and conditions when using FreeType 2 in
any of your projects or products.

  - The FreeType License,  found in the file  `docs/FTL.TXT`, which is
    similar to the  original BSD license *with*  an advertising clause
    that forces  you to explicitly  cite the FreeType project  in your
    product's  documentation.  All  details are  in the  license file.
    This license is suited to products which don't use the GNU General
    Public License.

    Note that  this license  is compatible to  the GNU  General Public
    License version 3, but not version 2.

  - The   GNU   General   Public   License   version   2,   found   in
    `docs/GPLv2.TXT`  (any  later  version  can  be  used  also),  for
    programs  which  already  use  the  GPL.  Note  that  the  FTL  is
    incompatible with GPLv2 due to its advertisement clause.

The contributed  BDF and PCF  drivers come  with a license  similar to
that  of the  X Window  System.   It is  compatible to  the above  two
licenses (see files `src/bdf/README`  and `src/pcf/README`).  The same
holds   for   the   source    code   files   `src/base/fthash.c`   and
`include/freetype/internal/fthash.h`; they were part of the BDF driver
in earlier FreeType versions.

The gzip  module uses the  zlib license (see  `src/gzip/zlib.h`) which
too is compatible to the above two licenses.

The   files   `src/autofit/ft-hb-ft.c`,   `src/autofit/ft-hb-decls.h`,
`src/autofit/ft-hb-types.h`,     and    `src/autofit/hb-script-list.h`
contain code taken (almost) verbatim  from the HarfBuzz library, which
uses the 'Old MIT' license compatible to the above two licenses.

The  MD5 checksum  support  (only used  for  debugging in  development
builds) is in the public domain.


--- end of LICENSE.TXT ---
                    The FreeType Project LICENSE
                    ----------------------------

                            2006-Jan-27

                    Copyright 1996-2002, 2006 by
          David Turner, Robert Wilhelm, and Werner Lemberg



Introduction
============

  The FreeType  Project is distributed in  several archive packages;
  some of them may contain, in addition to the FreeType font engine,
  various tools and  contributions which rely on, or  relate to, the
  FreeType Project.

  This  license applies  to all  files found  in such  packages, and
  which do not  fall under their own explicit  license.  The license
  affects  thus  the  FreeType   font  engine,  the  test  programs,
  documentation and makefiles, at the very least.

  This  license   was  inspired  by  the  BSD,   Artistic,  and  IJG
  (Independent JPEG  Group) licenses, which  all encourage inclusion
  and  use of  free  software in  commercial  and freeware  products
  alike.  As a consequence, its main points are that:

    o We don't promise that this software works. However, we will be
      interested in any kind of bug reports. (`as is' distribution)

    o You can  use this software for whatever you  want, in parts or
      full form, without having to pay us. (`royalty-free' usage)

    o You may not pretend that  you wrote this software.  If you use
      it, or  only parts of it,  in a program,  you must acknowledge
      somewhere  in  your  documentation  that  you  have  used  the
      FreeType code. (`credits')

  We  specifically  permit  and  encourage  the  inclusion  of  this
  software, with  or without modifications,  in commercial products.
  We  disclaim  all warranties  covering  The  FreeType Project  and
  assume no liability related to The FreeType Project.


  Finally,  many  people  asked  us  for  a  preferred  form  for  a
  credit/disclaimer to use in compliance with this license.  We thus
  encourage you to use the following text:

   """
    Portions of this software are copyright © <year> The FreeType
    Project (https://freetype.org).  All rights reserved.
   """

  Please replace <year> with the value from the FreeType version you
  actually use.


Legal Terms
===========

0. Definitions
--------------

  Throughout this license,  the terms `package', `FreeType Project',
  and  `FreeType  archive' refer  to  the  set  of files  originally
  distributed  by the  authors  (David Turner,  Robert Wilhelm,  and
  Werner Lemberg) as the `FreeType Project', be they named as alpha,
  beta or final release.

  `You' refers to  the licensee, or person using  the project, where
  `using' is a generic term including compiling the project's source
  code as  well as linking it  to form a  `program' or `executable'.
  This  program is  referred to  as  `a program  using the  FreeType
  engine'.

  This  license applies  to all  files distributed  in  the original
  FreeType  Project,   including  all  source   code,  binaries  and
  documentation,  unless  otherwise  stated   in  the  file  in  its
  original, unmodified form as  distributed in the original archive.
  If you are  unsure whether or not a particular  file is covered by
  this license, you must contact us to verify this.

  The FreeType  Project is copyright (C) 1996-2000  by David Turner,
  Robert Wilhelm, and Werner Lemberg.  All rights reserved except as
  specified below.

1. No Warranty
--------------

  THE FREETYPE PROJECT  IS PROVIDED `AS IS' WITHOUT  WARRANTY OF ANY
  KIND, EITHER  EXPRESS OR IMPLIED,  INCLUDING, BUT NOT  LIMITED TO,
  WARRANTIES  OF  MERCHANTABILITY   AND  FITNESS  FOR  A  PARTICULAR
  PURPOSE.  IN NO EVENT WILL ANY OF THE AUTHORS OR COPYRIGHT HOLDERS
  BE LIABLE  FOR ANY DAMAGES CAUSED  BY THE USE OR  THE INABILITY TO
  USE, OF THE FREETYPE PROJECT.

2. Redistribution
-----------------

  This  license  grants  a  worldwide, royalty-free,  perpetual  and
  irrevocable right  and license to use,  execute, perform, compile,
  display,  copy,   create  derivative  works   of,  distribute  and
  sublicense the  FreeType Project (in  both source and  object code
  forms)  and  derivative works  thereof  for  any  purpose; and  to
  authorize others  to exercise  some or all  of the  rights granted
  herein, subject to the following conditions:

    o Redistribution of  source code  must retain this  license file
      (`FTL.TXT') unaltered; any  additions, deletions or changes to
      the original  files must be clearly  indicated in accompanying
      documentation.   The  copyright   notices  of  the  unaltered,
      original  files must  be  preserved in  all  copies of  source
      files.

    o Redistribution in binary form must provide a  disclaimer  that
      states  that  the software is based in part of the work of the
      FreeType Team,  in  the  distribution  documentation.  We also
      encourage you to put an URL to the FreeType web page  in  your
      documentation, though this isn't mandatory.

  These conditions  apply to any  software derived from or  based on
  the FreeType Project,  not just the unmodified files.   If you use
  our work, you  must acknowledge us.  However, no  fee need be paid
  to us.

3. Advertising
--------------

  Neither the  FreeType authors and  contributors nor you  shall use
  the name of the  other for commercial, advertising, or promotional
  purposes without specific prior written permission.

  We suggest,  but do not require, that  you use one or  more of the
  following phrases to refer  to this software in your documentation
  or advertising  materials: `FreeType Project',  `FreeType Engine',
  `FreeType library', or `FreeType Distribution'.

  As  you have  not signed  this license,  you are  not  required to
  accept  it.   However,  as  the FreeType  Project  is  copyrighted
  material, only  this license, or  another one contracted  with the
  authors, grants you  the right to use, distribute,  and modify it.
  Therefore,  by  using,  distributing,  or modifying  the  FreeType
  Project, you indicate that you understand and accept all the terms
  of this license.

4. Contacts
-----------

  There are two mailing lists related to FreeType:

    o freetype@nongnu.org

      Discusses general use and applications of FreeType, as well as
      future and  wanted additions to the  library and distribution.
      If  you are looking  for support,  start in  this list  if you
      haven't found anything to help you in the documentation.

    o freetype-devel@nongnu.org

      Discusses bugs,  as well  as engine internals,  design issues,
      specific licenses, porting, etc.

  Our home page can be found at

    https://freetype.org


--- end of FTL.TXT ---
		    GNU GENERAL PUBLIC LICENSE
		       Version 2, June 1991

 Copyright (C) 1989, 1991 Free Software Foundation, Inc.
     51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 Everyone is permitted to copy and distribute verbatim copies
 of this license document, but changing it is not allowed.

			    Preamble

  The licenses for most software are designed to take away your
freedom to share and change it.  By contrast, the GNU General Public
License is intended to guarantee your freedom to share and change free
software--to make sure the software is free for all its users.  This
General Public License applies to most of the Free Software
Foundation's software and to any other program whose authors commit to
using it.  (Some other Free Software Foundation software is covered by
the GNU Library General Public License instead.)  You can apply it to
your programs, too.

  When we speak of free software, we are referring to freedom, not
price.  Our General Public Licenses are designed to make sure that you
have the freedom to distribute copies of free software (and charge for
this service if you wish), that you receive source code or can get it
if you want it, that you can change the software or use pieces of it
in new free programs; and that you know you can do these things.

  To protect your rights, we need to make restrictions that forbid
anyone to deny you these rights or to ask you to surrender the rights.
These restrictions translate to certain responsibilities for you if you
distribute copies of the software, or if you modify it.

  For example, if you distribute copies of such a program, whether
gratis or for a fee, you must give the recipients all the rights that
you have.  You must make sure that they, too, receive or can get the
source code.  And you must show them these terms so they know their
rights.

  We protect your rights with two steps: (1) copyright the software, and
(2) offer you this license which gives you legal permission to copy,
distribute and/or modify the software.

  Also, for each author's protection and ours, we want to make certain
that everyone understands that there is no warranty for this free
software.  If the software is modified by someone else and passed on, we
want its recipients to know that what they have is not the original, so
that any problems introduced by others will not reflect on the original
authors' reputations.

  Finally, any free program is threatened constantly by software
patents.  We wish to avoid the danger that redistributors of a free
program will individually obtain patent licenses, in effect making the
program proprietary.  To prevent this, we have made it clear that any
patent must be licensed for everyone's free use or not licensed at all.

  The precise terms and conditions for copying, distribution and
modification follow.

		    GNU GENERAL PUBLIC LICENSE
   TERMS AND CONDITIONS FOR COPYING, DISTRIBUTION AND MODIFICATION

  0. This License applies to any program or other work which contains
a notice placed by the copyright holder saying it may be distributed
under the terms of this General Public License.  The "Program", below,
refers to any such program or work, and a "work based on the Program"
means either the Program or any derivative work under copyright law:
that is to say, a work containing the Program or a portion of it,
either verbatim or with modifications and/or translated into another
language.  (Hereinafter, translation is included without limitation in
the term "modification".)  Each licensee is addressed as "you".

Activities other than copying, distribution and modification are not
covered by this License; they are outside its scope.  The act of
running the Program is not restricted, and the output from the Program
is covered only if its contents constitute a work based on the
Program (independent of having been made by running the Program).
Whether that is true depends on what the Program does.

  1. You may copy and distribute verbatim copies of the Program's
source code as you receive it, in any medium, provided that you
conspicuously and appropriately publish on each copy an appropriate
copyright notice and disclaimer of warranty; keep intact all the
notices that refer to this License and to the absence of any warranty;
and give any other recipients of the Program a copy of this License
along with the Program.

You may charge a fee for the physical act of transferring a copy, and
you may at your option offer warranty protection in exchange for a fee.

  2. You may modify your copy or copies of the Program or any portion
of it, thus forming a work based on the Program, and copy and
distribute such modifications or work under the terms of Section 1
above, provided that you also meet all of these conditions:

    a) You must cause the modified files to carry prominent notices
    stating that you changed the files and the date of any change.

    b) You must cause any work that you distribute or publish, that in
    whole or in part contains or is derived from the Program or any
    part thereof, to be licensed as a whole at no charge to all third
    parties under the terms of this License.

    c) If the modified program normally reads commands interactively
    when run, you must cause it, when started running for such
    interactive use in the most ordinary way, to print or display an
    announcement including an appropriate copyright notice and a
    notice that there is no warranty (or else, saying that you provide
    a warranty) and that users may redistribute the program under
    these conditions, and telling the user how to view a copy of this
    License.  (Exception: if the Program itself is interactive but
    does not normally print such an announcement, your work based on
    the Program is not required to print an announcement.)

These requirements apply to the modified work as a whole.  If
identifiable sections of that work are not derived from the Program,
and can be reasonably considered independent and separate works in
themselves, then this License, and its terms, do not apply to those
sections when you distribute them as separate works.  But when you
distribute the same sections as part of a whole which is a work based
on the Program, the distribution of the whole must be on the terms of
this License, whose permissions for other licensees extend to the
entire whole, and thus to each and every part regardless of who wrote it.

Thus, it is not the intent of this section to claim rights or contest
your rights to work written entirely by you; rather, the intent is to
exercise the right to control the distribution of derivative or
collective works based on the Program.

In addition, mere aggregation of another work not based on the Program
with the Program (or with a work based on the Program) on a volume of
a storage or distribution medium does not bring the other work under
the scope of this License.

  3. You may copy and distribute the Program (or a work based on it,
under Section 2) in object code or executable form under the terms of
Sections 1 and 2 above provided that you also do one of the following:

    a) Accompany it with the complete corresponding machine-readable
    source code, which must be distributed under the terms of Sections
    1 and 2 above on a medium customarily used for software interchange; or,

    b) Accompany it with a written offer, valid for at least three
    years, to give any third party, for a charge no more than your
    cost of physically performing source distribution, a complete
    machine-readable copy of the corresponding source code, to be
    distributed under the terms of Sections 1 and 2 above on a medium
    customarily used for software interchange; or,

    c) Accompany it with the information you received as to the offer
    to distribute corresponding source code.  (This alternative is
    allowed only for noncommercial distribution and only if you
    received the program in object code or executable form with such
    an offer, in accord with Subsection b above.)

The source code for a work means the preferred form of the work for
making modifications to it.  For an executable work, complete source
code means all the source code for all modules it contains, plus any
associated interface definition files, plus the scripts used to
control compilation and installation of the executable.  However, as a
special exception, the source code distributed need not include
anything that is normally distributed (in either source or binary
form) with the major components (compiler, kernel, and so on) of the
operating system on which the executable runs, unless that component
itself accompanies the executable.

If distribution of executable or object code is made by offering
access to copy from a designated place, then offering equivalent
access to copy the source code from the same place counts as
distribution of the source code, even though third parties are not
compelled to copy the source along with the object code.

  4. You may not copy, modify, sublicense, or distribute the Program
except as expressly provided under this License.  Any attempt
otherwise to copy, modify, sublicense or distribute the Program is
void, and will automatically terminate your rights under this License.
However, parties who have received copies, or rights, from you under
this License will not have their licenses terminated so long as such
parties remain in full compliance.

  5. You are not required to accept this License, since you have not
signed it.  However, nothing else grants you permission to modify or
distribute the Program or its derivative works.  These actions are
prohibited by law if you do not accept this License.  Therefore, by
modifying or distributing the Program (or any work based on the
Program), you indicate your acceptance of this License to do so, and
all its terms and conditions for copying, distributing or modifying
the Program or works based on it.

  6. Each time you redistribute the Program (or any work based on the
Program), the recipient automatically receives a license from the
original licensor to copy, distribute or modify the Program subject to
these terms and conditions.  You may not impose any further
restrictions on the recipients' exercise of the rights granted herein.
You are not responsible for enforcing compliance by third parties to
this License.

  7. If, as a consequence of a court judgment or allegation of patent
infringement or for any other reason (not limited to patent issues),
conditions are imposed on you (whether by court order, agreement or
otherwise) that contradict the conditions of this License, they do not
excuse you from the conditions of this License.  If you cannot
distribute so as to satisfy simultaneously your obligations under this
License and any other pertinent obligations, then as a consequence you
may not distribute the Program at all.  For example, if a patent
license would not permit royalty-free redistribution of the Program by
all those who receive copies directly or indirectly through you, then
the only way you could satisfy both it and this License would be to
refrain entirely from distribution of the Program.

If any portion of this section is held invalid or unenforceable under
any particular circumstance, the balance of the section is intended to
apply and the section as a whole is intended to apply in other
circumstances.

It is not the purpose of this section to induce you to infringe any
patents or other property right claims or to contest validity of any
such claims; this section has the sole purpose of protecting the
integrity of the free software distribution system, which is
implemented by public license practices.  Many people have made
generous contributions to the wide range of software distributed
through that system in reliance on consistent application of that
system; it is up to the author/donor to decide if he or she is willing
to distribute software through any other system and a licensee cannot
impose that choice.

This section is intended to make thoroughly clear what is believed to
be a consequence of the rest of this License.

  8. If the distribution and/or use of the Program is restricted in
certain countries either by patents or by copyrighted interfaces, the
original copyright holder who places the Program under this License
may add an explicit geographical distribution limitation excluding
those countries, so that distribution is permitted only in or among
countries not thus excluded.  In such case, this License incorporates
the limitation as if written in the body of this License.

  9. The Free Software Foundation may publish revised and/or new versions
of the General Public License from time to time.  Such new versions will
be similar in spirit to the present version, but may differ in detail to
address new problems or concerns.

Each version is given a distinguishing version number.  If the Program
specifies a version number of this License which applies to it and "any
later version", you have the option of following the terms and conditions
either of that version or of any later version published by the Free
Software Foundation.  If the Program does not specify a version number of
this License, you may choose any version ever published by the Free Software
Foundation.

  10. If you wish to incorporate parts of the Program into other free
programs whose distribution conditions are different, write to the author
to ask for permission.  For software which is copyrighted by the Free
Software Foundation, write to the Free Software Foundation; we sometimes
make exceptions for this.  Our decision will be guided by the two goals
of preserving the free status of all derivatives of our free software and
of promoting the sharing and reuse of software generally.

			    NO WARRANTY

  11. BECAUSE THE PROGRAM IS LICENSED FREE OF CHARGE, THERE IS NO WARRANTY
FOR THE PROGRAM, TO THE EXTENT PERMITTED BY APPLICABLE LAW.  EXCEPT WHEN
OTHERWISE STATED IN WRITING THE COPYRIGHT HOLDERS AND/OR OTHER PARTIES
PROVIDE THE PROGRAM "AS IS" WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESSED
OR IMPLIED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.  THE ENTIRE RISK AS
TO THE QUALITY AND PERFORMANCE OF THE PROGRAM IS WITH YOU.  SHOULD THE
PROGRAM PROVE DEFECTIVE, YOU ASSUME THE COST OF ALL NECESSARY SERVICING,
REPAIR OR CORRECTION.

  12. IN NO EVENT UNLESS REQUIRED BY APPLICABLE LAW OR AGREED TO IN WRITING
WILL ANY COPYRIGHT HOLDER, OR ANY OTHER PARTY WHO MAY MODIFY AND/OR
REDISTRIBUTE THE PROGRAM AS PERMITTED ABOVE, BE LIABLE TO YOU FOR DAMAGES,
INCLUDING ANY GENERAL, SPECIAL, INCIDENTAL OR CONSEQUENTIAL DAMAGES ARISING
OUT OF THE USE OR INABILITY TO USE THE PROGRAM (INCLUDING BUT NOT LIMITED
TO LOSS OF DATA OR DATA BEING RENDERED INACCURATE OR LOSSES SUSTAINED BY
YOU OR THIRD PARTIES OR A FAILURE OF THE PROGRAM TO OPERATE WITH ANY OTHER
PROGRAMS), EVEN IF SUCH HOLDER OR OTHER PARTY HAS BEEN ADVISED OF THE
POSSIBILITY OF SUCH DAMAGES.

		     END OF TERMS AND CONDITIONS

	    How to Apply These Terms to Your New Programs

  If you develop a new program, and you want it to be of the greatest
possible use to the public, the best way to achieve this is to make it
free software which everyone can redistribute and change under these terms.

  To do so, attach the following notices to the program.  It is safest
to attach them to the start of each source file to most effectively
convey the exclusion of warranty; and each file should have at least
the "copyright" line and a pointer to where the full notice is found.

    <one line to give the program's name and a brief idea of what it does.>
    Copyright (C) <year>  <name of author>

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, write to the Free Software
    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA


Also add information on how to contact you by electronic and paper mail.

If the program is interactive, make it output a short notice like this
when it starts in an interactive mode:

    Gnomovision version 69, Copyright (C) year  name of author
    Gnomovision comes with ABSOLUTELY NO WARRANTY; for details type `show w'.
    This is free software, and you are welcome to redistribute it
    under certain conditions; type `show c' for details.

The hypothetical commands `show w' and `show c' should show the appropriate
parts of the General Public License.  Of course, the commands you use may
be called something other than `show w' and `show c'; they could even be
mouse-clicks or menu items--whatever suits your program.

You should also get your employer (if you work as a programmer) or your
school, if any, to sign a "copyright disclaimer" for the program, if
necessary.  Here is a sample; alter the names:

  Yoyodyne, Inc., hereby disclaims all copyright interest in the program
  `Gnomovision' (which makes passes at compilers) written by James Hacker.

  <signature of Ty Coon>, 1 April 1989
  Ty Coon, President of Vice

This General Public License does not permit incorporating your program into
proprietary programs.  If your program is a subroutine library, you may
consider it more useful to permit linking proprietary applications with the
library.  If this is what you want to do, use the GNU Library General
Public License instead of this License.

===== harfbuzz-14.2.1 =====

HarfBuzz is licensed under the so-called "Old MIT" license.  Details follow.
For parts of HarfBuzz that are licensed under different licenses see individual
files names COPYING in subdirectories where applicable.

Copyright © 2010-2022  Google, Inc.
Copyright © 2015-2020  Ebrahim Byagowi
Copyright © 2019,2020  Facebook, Inc.
Copyright © 2012,2015  Mozilla Foundation
Copyright © 2011  Codethink Limited
Copyright © 2008,2010  Nokia Corporation and/or its subsidiary(-ies)
Copyright © 2009  Keith Stribley
Copyright © 2011  Martin Hosken and SIL International
Copyright © 2007  Chris Wilson
Copyright © 2005,2006,2020,2021,2022,2023  Behdad Esfahbod
Copyright © 2004,2007,2008,2009,2010,2013,2021,2022,2023  Red Hat, Inc.
Copyright © 1998-2005  David Turner and Werner Lemberg
Copyright © 2016  Igalia S.L.
Copyright © 2022  Matthias Clasen
Copyright © 2018,2021  Khaled Hosny
Copyright © 2018,2019,2020  Adobe, Inc
Copyright © 2013-2015  Alexei Podtelezhnikov

For full copyright notices consult the individual files in the package.


Permission is hereby granted, without written agreement and without
license or royalty fees, to use, copy, modify, and distribute this
software and its documentation for any purpose, provided that the
above copyright notice and the following two paragraphs appear in
all copies of this software.

IN NO EVENT SHALL THE COPYRIGHT HOLDER BE LIABLE TO ANY PARTY FOR
DIRECT, INDIRECT, SPECIAL, INCIDENTAL, OR CONSEQUENTIAL DAMAGES
ARISING OUT OF THE USE OF THIS SOFTWARE AND ITS DOCUMENTATION, EVEN
IF THE COPYRIGHT HOLDER HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH
DAMAGE.

THE COPYRIGHT HOLDER SPECIFICALLY DISCLAIMS ANY WARRANTIES, INCLUDING,
BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
FITNESS FOR A PARTICULAR PURPOSE.  THE SOFTWARE PROVIDED HEREUNDER IS
ON AN "AS IS" BASIS, AND THE COPYRIGHT HOLDER HAS NO OBLIGATION TO
PROVIDE MAINTENANCE, SUPPORT, UPDATES, ENHANCEMENTS, OR MODIFICATIONS.

===== lcms2-2.19.1 =====

MIT License

Copyright (c) 2023 Marti Maria Saguer

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the 
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to 
permit persons to whom the Software is furnished to do so, subject
to the following conditions:

The above copyright notice and this permission notice shall be 
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF 
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE 
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

===== libavif-1.4.2 =====

Copyright 2019 Joe Drago. All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
this list of conditions and the following disclaimer in the documentation
and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

------------------------------------------------------------------------------

Files: src/obu.c

Copyright © 2018-2019, VideoLAN and dav1d authors
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

------------------------------------------------------------------------------

Files: third_party/iccjpeg/*

In plain English:

1. We don't promise that this software works.  (But if you find any bugs,
   please let us know!)
2. You can use this software for whatever you want.  You don't have to pay us.
3. You may not pretend that you wrote this software.  If you use it in a
   program, you must acknowledge somewhere in your documentation that
   you've used the IJG code.

In legalese:

The authors make NO WARRANTY or representation, either express or implied,
with respect to this software, its quality, accuracy, merchantability, or
fitness for a particular purpose.  This software is provided "AS IS", and you,
its user, assume the entire risk as to its quality and accuracy.

This software is copyright (C) 1991-2013, Thomas G. Lane, Guido Vollbeding.
All Rights Reserved except as specified below.

Permission is hereby granted to use, copy, modify, and distribute this
software (or portions thereof) for any purpose, without fee, subject to these
conditions:
(1) If any part of the source code for this software is distributed, then this
README file must be included, with this copyright and no-warranty notice
unaltered; and any additions, deletions, or changes to the original files
must be clearly indicated in accompanying documentation.
(2) If only executable code is distributed, then the accompanying
documentation must state that "this software is based in part on the work of
the Independent JPEG Group".
(3) Permission for use of this software is granted only if the user accepts
full responsibility for any undesirable consequences; the authors accept
NO LIABILITY for damages of any kind.

These conditions apply to any software derived from or based on the IJG code,
not just to the unmodified library.  If you use our work, you ought to
acknowledge us.

Permission is NOT granted for the use of any IJG author's name or company name
in advertising or publicity relating to this software or products derived from
it.  This software may be referred to only as "the Independent JPEG Group's
software".

We specifically permit and encourage the use of this software as the basis of
commercial products, provided that all warranty or liability claims are
assumed by the product vendor.


The Unix configuration script "configure" was produced with GNU Autoconf.
It is copyright by the Free Software Foundation but is freely distributable.
The same holds for its supporting scripts (config.guess, config.sub,
ltmain.sh).  Another support script, install-sh, is copyright by X Consortium
but is also freely distributable.

The IJG distribution formerly included code to read and write GIF files.
To avoid entanglement with the Unisys LZW patent, GIF reading support has
been removed altogether, and the GIF writer has been simplified to produce
"uncompressed GIFs".  This technique does not use the LZW algorithm; the
resulting GIF files are larger than usual, but are readable by all standard
GIF decoders.

We are required to state that
    "The Graphics Interchange Format(c) is the Copyright property of
    CompuServe Incorporated.  GIF(sm) is a Service Mark property of
    CompuServe Incorporated."

------------------------------------------------------------------------------

Files: contrib/gdk-pixbuf/*

Copyright 2020 Emmanuel Gil Peyrot. All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
this list of conditions and the following disclaimer in the documentation
and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

------------------------------------------------------------------------------

Files: android_jni/gradlew*


                                 Apache License
                           Version 2.0, January 2004
                        http://www.apache.org/licenses/

   TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION

   1. Definitions.

      "License" shall mean the terms and conditions for use, reproduction,
      and distribution as defined by Sections 1 through 9 of this document.

      "Licensor" shall mean the copyright owner or entity authorized by
      the copyright owner that is granting the License.

      "Legal Entity" shall mean the union of the acting entity and all
      other entities that control, are controlled by, or are under common
      control with that entity. For the purposes of this definition,
      "control" means (i) the power, direct or indirect, to cause the
      direction or management of such entity, whether by contract or
      otherwise, or (ii) ownership of fifty percent (50%) or more of the
      outstanding shares, or (iii) beneficial ownership of such entity.

      "You" (or "Your") shall mean an individual or Legal Entity
      exercising permissions granted by this License.

      "Source" form shall mean the preferred form for making modifications,
      including but not limited to software source code, documentation
      source, and configuration files.

      "Object" form shall mean any form resulting from mechanical
      transformation or translation of a Source form, including but
      not limited to compiled object code, generated documentation,
      and conversions to other media types.

      "Work" shall mean the work of authorship, whether in Source or
      Object form, made available under the License, as indicated by a
      copyright notice that is included in or attached to the work
      (an example is provided in the Appendix below).

      "Derivative Works" shall mean any work, whether in Source or Object
      form, that is based on (or derived from) the Work and for which the
      editorial revisions, annotations, elaborations, or other modifications
      represent, as a whole, an original work of authorship. For the purposes
      of this License, Derivative Works shall not include works that remain
      separable from, or merely link (or bind by name) to the interfaces of,
      the Work and Derivative Works thereof.

      "Contribution" shall mean any work of authorship, including
      the original version of the Work and any modifications or additions
      to that Work or Derivative Works thereof, that is intentionally
      submitted to Licensor for inclusion in the Work by the copyright owner
      or by an individual or Legal Entity authorized to submit on behalf of
      the copyright owner. For the purposes of this definition, "submitted"
      means any form of electronic, verbal, or written communication sent
      to the Licensor or its representatives, including but not limited to
      communication on electronic mailing lists, source code control systems,
      and issue tracking systems that are managed by, or on behalf of, the
      Licensor for the purpose of discussing and improving the Work, but
      excluding communication that is conspicuously marked or otherwise
      designated in writing by the copyright owner as "Not a Contribution."

      "Contributor" shall mean Licensor and any individual or Legal Entity
      on behalf of whom a Contribution has been received by Licensor and
      subsequently incorporated within the Work.

   2. Grant of Copyright License. Subject to the terms and conditions of
      this License, each Contributor hereby grants to You a perpetual,
      worldwide, non-exclusive, no-charge, royalty-free, irrevocable
      copyright license to reproduce, prepare Derivative Works of,
      publicly display, publicly perform, sublicense, and distribute the
      Work and such Derivative Works in Source or Object form.

   3. Grant of Patent License. Subject to the terms and conditions of
      this License, each Contributor hereby grants to You a perpetual,
      worldwide, non-exclusive, no-charge, royalty-free, irrevocable
      (except as stated in this section) patent license to make, have made,
      use, offer to sell, sell, import, and otherwise transfer the Work,
      where such license applies only to those patent claims licensable
      by such Contributor that are necessarily infringed by their
      Contribution(s) alone or by combination of their Contribution(s)
      with the Work to which such Contribution(s) was submitted. If You
      institute patent litigation against any entity (including a
      cross-claim or counterclaim in a lawsuit) alleging that the Work
      or a Contribution incorporated within the Work constitutes direct
      or contributory patent infringement, then any patent licenses
      granted to You under this License for that Work shall terminate
      as of the date such litigation is filed.

   4. Redistribution. You may reproduce and distribute copies of the
      Work or Derivative Works thereof in any medium, with or without
      modifications, and in Source or Object form, provided that You
      meet the following conditions:

      (a) You must give any other recipients of the Work or
          Derivative Works a copy of this License; and

      (b) You must cause any modified files to carry prominent notices
          stating that You changed the files; and

      (c) You must retain, in the Source form of any Derivative Works
          that You distribute, all copyright, patent, trademark, and
          attribution notices from the Source form of the Work,
          excluding those notices that do not pertain to any part of
          the Derivative Works; and

      (d) If the Work includes a "NOTICE" text file as part of its
          distribution, then any Derivative Works that You distribute must
          include a readable copy of the attribution notices contained
          within such NOTICE file, excluding those notices that do not
          pertain to any part of the Derivative Works, in at least one
          of the following places: within a NOTICE text file distributed
          as part of the Derivative Works; within the Source form or
          documentation, if provided along with the Derivative Works; or,
          within a display generated by the Derivative Works, if and
          wherever such third-party notices normally appear. The contents
          of the NOTICE file are for informational purposes only and
          do not modify the License. You may add Your own attribution
          notices within Derivative Works that You distribute, alongside
          or as an addendum to the NOTICE text from the Work, provided
          that such additional attribution notices cannot be construed
          as modifying the License.

      You may add Your own copyright statement to Your modifications and
      may provide additional or different license terms and conditions
      for use, reproduction, or distribution of Your modifications, or
      for any such Derivative Works as a whole, provided Your use,
      reproduction, and distribution of the Work otherwise complies with
      the conditions stated in this License.

   5. Submission of Contributions. Unless You explicitly state otherwise,
      any Contribution intentionally submitted for inclusion in the Work
      by You to the Licensor shall be under the terms and conditions of
      this License, without any additional terms or conditions.
      Notwithstanding the above, nothing herein shall supersede or modify
      the terms of any separate license agreement you may have executed
      with Licensor regarding such Contributions.

   6. Trademarks. This License does not grant permission to use the trade
      names, trademarks, service marks, or product names of the Licensor,
      except as required for reasonable and customary use in describing the
      origin of the Work and reproducing the content of the NOTICE file.

   7. Disclaimer of Warranty. Unless required by applicable law or
      agreed to in writing, Licensor provides the Work (and each
      Contributor provides its Contributions) on an "AS IS" BASIS,
      WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
      implied, including, without limitation, any warranties or conditions
      of TITLE, NON-INFRINGEMENT, MERCHANTABILITY, or FITNESS FOR A
      PARTICULAR PURPOSE. You are solely responsible for determining the
      appropriateness of using or redistributing the Work and assume any
      risks associated with Your exercise of permissions under this License.

   8. Limitation of Liability. In no event and under no legal theory,
      whether in tort (including negligence), contract, or otherwise,
      unless required by applicable law (such as deliberate and grossly
      negligent acts) or agreed to in writing, shall any Contributor be
      liable to You for damages, including any direct, indirect, special,
      incidental, or consequential damages of any character arising as a
      result of this License or out of the use or inability to use the
      Work (including but not limited to damages for loss of goodwill,
      work stoppage, computer failure or malfunction, or any and all
      other commercial damages or losses), even if such Contributor
      has been advised of the possibility of such damages.

   9. Accepting Warranty or Additional Liability. While redistributing
      the Work or Derivative Works thereof, You may choose to offer,
      and charge a fee for, acceptance of support, warranty, indemnity,
      or other liability obligations and/or rights consistent with this
      License. However, in accepting such obligations, You may act only
      on Your own behalf and on Your sole responsibility, not on behalf
      of any other Contributor, and only if You agree to indemnify,
      defend, and hold each Contributor harmless for any liability
      incurred by, or claims asserted against, such Contributor by reason
      of your accepting any such warranty or additional liability.

   END OF TERMS AND CONDITIONS

   APPENDIX: How to apply the Apache License to your work.

      To apply the Apache License to your work, attach the following
      boilerplate notice, with the fields enclosed by brackets "[]"
      replaced with your own identifying information. (Don't include
      the brackets!)  The text should be enclosed in the appropriate
      comment syntax for the file format. We also recommend that a
      file or class name and description of purpose be included on the
      same "printed page" as the copyright notice for easier
      identification within third-party archives.

   Copyright [yyyy] [name of copyright owner]

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.

------------------------------------------------------------------------------

Files: third_party/libyuv/*

Copyright 2011 The LibYuv Project Authors. All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

  * Redistributions of source code must retain the above copyright
    notice, this list of conditions and the following disclaimer.

  * Redistributions in binary form must reproduce the above copyright
    notice, this list of conditions and the following disclaimer in
    the documentation and/or other materials provided with the
    distribution.

  * Neither the name of Google nor the names of its contributors may
    be used to endorse or promote products derived from this software
    without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

===== libjpeg-turbo-3.1.4.1 =====

LEGAL ISSUES
============

In plain English:

1. We don't promise that this software works.  (But if you find any bugs,
   please let us know!)
2. You can use this software for whatever you want.  You don't have to pay us.
3. You may not pretend that you wrote this software.  If you use it in a
   program, you must acknowledge somewhere in your documentation that
   you've used the IJG code.

In legalese:

The authors make NO WARRANTY or representation, either express or implied,
with respect to this software, its quality, accuracy, merchantability, or
fitness for a particular purpose.  This software is provided "AS IS", and you,
its user, assume the entire risk as to its quality and accuracy.

This software is copyright (C) 1991-2020, Thomas G. Lane, Guido Vollbeding.
All Rights Reserved except as specified below.

Permission is hereby granted to use, copy, modify, and distribute this
software (or portions thereof) for any purpose, without fee, subject to these
conditions:
(1) If any part of the source code for this software is distributed, then this
README file must be included, with this copyright and no-warranty notice
unaltered; and any additions, deletions, or changes to the original files
must be clearly indicated in accompanying documentation.
(2) If only executable code is distributed, then the accompanying
documentation must state that "this software is based in part on the work of
the Independent JPEG Group".
(3) Permission for use of this software is granted only if the user accepts
full responsibility for any undesirable consequences; the authors accept
NO LIABILITY for damages of any kind.

These conditions apply to any software derived from or based on the IJG code,
not just to the unmodified library.  If you use our work, you ought to
acknowledge us.

Permission is NOT granted for the use of any IJG author's name or company name
in advertising or publicity relating to this software or products derived from
it.  This software may be referred to only as "the Independent JPEG Group's
software".

We specifically permit and encourage the use of this software as the basis of
commercial products, provided that all warranty or liability claims are
assumed by the product vendor.

libjpeg-turbo Licenses
======================

libjpeg-turbo is covered by two compatible BSD-style open source licenses:

- The IJG (Independent JPEG Group) License, which is listed in
  [README.ijg](README.ijg)

  This license applies to the libjpeg API library and associated programs,
  including any code inherited from libjpeg and any modifications to that
  code.  Note that the libjpeg-turbo SIMD source code bears the
  [zlib License](https://opensource.org/licenses/Zlib), but in the context of
  the overall libjpeg API library, the terms of the zlib License are subsumed
  by the terms of the IJG License.

- The Modified (3-clause) BSD License, which is listed below

  This license applies to the TurboJPEG API library and associated programs, as
  well as the build system.  Note that the TurboJPEG API library wraps the
  libjpeg API library, so in the context of the overall TurboJPEG API library,
  both the terms of the IJG License and the terms of the Modified (3-clause)
  BSD License apply.


Complying with the libjpeg-turbo Licenses
=========================================

This section provides a roll-up of the libjpeg-turbo licensing terms, to the
best of our understanding.  This is not a license in and of itself.  It is
intended solely for clarification.

1.  If you are distributing a modified version of the libjpeg-turbo source,
    then:

    1.  You cannot alter or remove any existing copyright or license notices
        from the source.

        **Origin**
        - Clause 1 of the IJG License
        - Clause 1 of the Modified BSD License
        - Clauses 1 and 3 of the zlib License

    2.  You must add your own copyright notice to the header of each source
        file you modified, so others can tell that you modified that file.  (If
        there is not an existing copyright header in that file, then you can
        simply add a notice stating that you modified the file.)

        **Origin**
        - Clause 1 of the IJG License
        - Clause 2 of the zlib License

    3.  You must include the IJG README file, and you must not alter any of the
        copyright or license text in that file.

        **Origin**
        - Clause 1 of the IJG License

2.  If you are distributing only libjpeg-turbo binaries without the source, or
    if you are distributing an application that statically links with
    libjpeg-turbo, then:

    1.  Your product documentation must include a message stating:

        This software is based in part on the work of the Independent JPEG
        Group.

        **Origin**
        - Clause 2 of the IJG license

    2.  If your binary distribution includes or uses the TurboJPEG API, then
        your product documentation must include the text of the Modified BSD
        License (see below.)

        **Origin**
        - Clause 2 of the Modified BSD License

3.  You cannot use the name of the IJG or The libjpeg-turbo Project or the
    contributors thereof in advertising, publicity, etc.

    **Origin**
    - IJG License
    - Clause 3 of the Modified BSD License

4.  The IJG and The libjpeg-turbo Project do not warrant libjpeg-turbo to be
    free of defects, nor do we accept any liability for undesirable
    consequences resulting from your use of the software.

    **Origin**
    - IJG License
    - Modified BSD License
    - zlib License


The Modified (3-clause) BSD License
===================================

Copyright (C) 2009-2026 D. R. Commander.  All Rights Reserved.<br>
Copyright (C) 2015 Viktor Szathmáry.  All Rights Reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

- Redistributions of source code must retain the above copyright notice,
  this list of conditions and the following disclaimer.
- Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.
- Neither the name of the libjpeg-turbo Project nor the names of its
  contributors may be used to endorse or promote products derived from this
  software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS",
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT HOLDERS OR CONTRIBUTORS BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.


Why Two Licenses?
=================

The zlib License could have been used instead of the Modified (3-clause) BSD
License, and since the IJG License effectively subsumes the distribution
conditions of the zlib License, this would have effectively placed
libjpeg-turbo binary distributions under the IJG License.  However, the IJG
License specifically refers to the Independent JPEG Group and does not extend
attribution and endorsement protections to other entities.  Thus, it was
desirable to choose a license that granted us the same protections for new code
that were granted to the IJG for code derived from their software.

===== libpng-1.6.58 =====

COPYRIGHT NOTICE, DISCLAIMER, and LICENSE
=========================================

PNG Reference Library License version 2
---------------------------------------

 * Copyright (c) 1995-2026 The PNG Reference Library Authors.
 * Copyright (c) 2018-2026 Cosmin Truta.
 * Copyright (c) 2000-2002, 2004, 2006-2018 Glenn Randers-Pehrson.
 * Copyright (c) 1996-1997 Andreas Dilger.
 * Copyright (c) 1995-1996 Guy Eric Schalnat, Group 42, Inc.

The software is supplied "as is", without warranty of any kind,
express or implied, including, without limitation, the warranties
of merchantability, fitness for a particular purpose, title, and
non-infringement.  In no event shall the Copyright owners, or
anyone distributing the software, be liable for any damages or
other liability, whether in contract, tort or otherwise, arising
from, out of, or in connection with the software, or the use or
other dealings in the software, even if advised of the possibility
of such damage.

Permission is hereby granted to use, copy, modify, and distribute
this software, or portions hereof, for any purpose, without fee,
subject to the following restrictions:

 1. The origin of this software must not be misrepresented; you
    must not claim that you wrote the original software.  If you
    use this software in a product, an acknowledgment in the product
    documentation would be appreciated, but is not required.

 2. Altered source versions must be plainly marked as such, and must
    not be misrepresented as being the original software.

 3. This Copyright notice may not be removed or altered from any
    source or altered source distribution.


PNG Reference Library License version 1 (for libpng 0.5 through 1.6.35)
-----------------------------------------------------------------------

libpng versions 1.0.7, July 1, 2000, through 1.6.35, July 15, 2018 are
Copyright (c) 2000-2002, 2004, 2006-2018 Glenn Randers-Pehrson, are
derived from libpng-1.0.6, and are distributed according to the same
disclaimer and license as libpng-1.0.6 with the following individuals
added to the list of Contributing Authors:

    Simon-Pierre Cadieux
    Eric S. Raymond
    Mans Rullgard
    Cosmin Truta
    Gilles Vollant
    James Yu
    Mandar Sahastrabuddhe
    Google Inc.
    Vadim Barkov

and with the following additions to the disclaimer:

    There is no warranty against interference with your enjoyment of
    the library or against infringement.  There is no warranty that our
    efforts or the library will fulfill any of your particular purposes
    or needs.  This library is provided with all faults, and the entire
    risk of satisfactory quality, performance, accuracy, and effort is
    with the user.

Some files in the "contrib" directory and some configure-generated
files that are distributed with libpng have other copyright owners, and
are released under other open source licenses.

libpng versions 0.97, January 1998, through 1.0.6, March 20, 2000, are
Copyright (c) 1998-2000 Glenn Randers-Pehrson, are derived from
libpng-0.96, and are distributed according to the same disclaimer and
license as libpng-0.96, with the following individuals added to the
list of Contributing Authors:

    Tom Lane
    Glenn Randers-Pehrson
    Willem van Schaik

libpng versions 0.89, June 1996, through 0.96, May 1997, are
Copyright (c) 1996-1997 Andreas Dilger, are derived from libpng-0.88,
and are distributed according to the same disclaimer and license as
libpng-0.88, with the following individuals added to the list of
Contributing Authors:

    John Bowler
    Kevin Bracey
    Sam Bushell
    Magnus Holmgren
    Greg Roelofs
    Tom Tanner

Some files in the "scripts" directory have other copyright owners,
but are released under this license.

libpng versions 0.5, May 1995, through 0.88, January 1996, are
Copyright (c) 1995-1996 Guy Eric Schalnat, Group 42, Inc.

For the purposes of this copyright and license, "Contributing Authors"
is defined as the following set of individuals:

    Andreas Dilger
    Dave Martindale
    Guy Eric Schalnat
    Paul Schmidt
    Tim Wegner

The PNG Reference Library is supplied "AS IS".  The Contributing
Authors and Group 42, Inc. disclaim all warranties, expressed or
implied, including, without limitation, the warranties of
merchantability and of fitness for any purpose.  The Contributing
Authors and Group 42, Inc. assume no liability for direct, indirect,
incidental, special, exemplary, or consequential damages, which may
result from the use of the PNG Reference Library, even if advised of
the possibility of such damage.

Permission is hereby granted to use, copy, modify, and distribute this
source code, or portions hereof, for any purpose, without fee, subject
to the following restrictions:

 1. The origin of this source code must not be misrepresented.

 2. Altered versions must be plainly marked as such and must not
    be misrepresented as being the original source.

 3. This Copyright notice may not be removed or altered from any
    source or altered source distribution.

The Contributing Authors and Group 42, Inc. specifically permit,
without fee, and encourage the use of this source code as a component
to supporting the PNG file format in commercial products.  If you use
this source code in a product, acknowledgment is not required but would
be appreciated.

===== libwebp-1.6.0 =====

Copyright (c) 2010, Google Inc. All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

  * Redistributions of source code must retain the above copyright
    notice, this list of conditions and the following disclaimer.

  * Redistributions in binary form must reproduce the above copyright
    notice, this list of conditions and the following disclaimer in
    the documentation and/or other materials provided with the
    distribution.

  * Neither the name of Google nor the names of its contributors may
    be used to endorse or promote products derived from this software
    without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


===== openjpeg-2.5.4 =====

/*
 * The copyright in this software is being made available under the 2-clauses 
 * BSD License, included below. This software may be subject to other third 
 * party and contributor rights, including patent rights, and no such rights
 * are granted under this license.
 *
 * Copyright (c) 2002-2014, Universite catholique de Louvain (UCL), Belgium
 * Copyright (c) 2002-2014, Professor Benoit Macq
 * Copyright (c) 2003-2014, Antonin Descampe
 * Copyright (c) 2003-2009, Francois-Olivier Devaux
 * Copyright (c) 2005, Herve Drolon, FreeImage Team
 * Copyright (c) 2002-2003, Yannick Verschueren
 * Copyright (c) 2001-2003, David Janssens
 * Copyright (c) 2011-2012, Centre National d'Etudes Spatiales (CNES), France 
 * Copyright (c) 2012, CS Systemes d'Information, France
 *
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 * 1. Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS `AS IS'
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
 * LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
 * CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
 * SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
 * INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
 * CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 * POSSIBILITY OF SUCH DAMAGE.
 */

===== tiff-4.7.1 =====

# LibTIFF license

Copyright © 1988-1997 Sam Leffler\
Copyright © 1991-1997 Silicon Graphics, Inc.

Permission to use, copy, modify, distribute, and sell this software and 
its documentation for any purpose is hereby granted without fee, provided
that (i) the above copyright notices and this permission notice appear in
all copies of the software and related documentation, and (ii) the names of
Sam Leffler and Silicon Graphics may not be used in any advertising or
publicity relating to the software without the specific, prior written
permission of Sam Leffler and Silicon Graphics.

THE SOFTWARE IS PROVIDED "AS-IS" AND WITHOUT WARRANTY OF ANY KIND, 
EXPRESS, IMPLIED OR OTHERWISE, INCLUDING WITHOUT LIMITATION, ANY 
WARRANTY OF MERCHANTABILITY OR FITNESS FOR A PARTICULAR PURPOSE.  

IN NO EVENT SHALL SAM LEFFLER OR SILICON GRAPHICS BE LIABLE FOR
ANY SPECIAL, INCIDENTAL, INDIRECT OR CONSEQUENTIAL DAMAGES OF ANY KIND,
OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS,
WHETHER OR NOT ADVISED OF THE POSSIBILITY OF DAMAGE, AND ON ANY THEORY OF 
LIABILITY, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE 
OF THIS SOFTWARE.

# Lempel-Ziv & Welch Compression (tif_lzw.c) license
The code of tif_lzw.c is derived from the compress program whose code is
derived from software contributed to Berkeley by James A. Woods,
derived from original work by Spencer Thomas and Joseph Orost.

The original Berkeley copyright notice appears below in its entirety:

Copyright (c) 1985, 1986 The Regents of the University of California.
All rights reserved.

This code is derived from software contributed to Berkeley by
James A. Woods, derived from original work by Spencer Thomas
and Joseph Orost.

Redistribution and use in source and binary forms are permitted
provided that the above copyright notice and this paragraph are
duplicated in all such forms and that any documentation,
advertising materials, and other materials related to such
distribution and use acknowledge that the software was developed
by the University of California, Berkeley.  The name of the
University may not be used to endorse or promote products derived
from this software without specific prior written permission.
THIS SOFTWARE IS PROVIDED ``AS IS'' AND WITHOUT ANY EXPRESS OR
IMPLIED WARRANTIES, INCLUDING, WITHOUT LIMITATION, THE IMPLIED
WARRANTIES OF MERCHANTIBILITY AND FITNESS FOR A PARTICULAR PURPOSE.

===== xz-5.8.3 =====


XZ Utils Licensing
==================

    Different licenses apply to different files in this package. Here
    is a summary of which licenses apply to which parts of this package:

      - liblzma is under the BSD Zero Clause License (0BSD).

      - The command line tools xz, xzdec, lzmadec, and lzmainfo are
        under 0BSD except that, on systems that don't have a usable
        getopt_long, GNU getopt_long is compiled and linked in from the
        'lib' directory. The getopt_long code is under GNU LGPLv2.1+.

      - The scripts to grep, diff, and view compressed files have been
        adapted from GNU gzip. These scripts (xzgrep, xzdiff, xzless,
        and xzmore) are under GNU GPLv2+. The man pages of the scripts
        are under 0BSD; they aren't based on the man pages of GNU gzip.

      - Most of the XZ Utils specific documentation that is in
        plain text files (like README, INSTALL, PACKAGERS, NEWS,
        and ChangeLog) are under 0BSD unless stated otherwise in
        the file itself. The files xz-file-format.txt and
        lzma-file-format.xt are in the public domain but may
        be distributed under the terms of 0BSD too.

      - Translated messages and man pages are under 0BSD except that
        some old translations are in the public domain.

      - Test files and test code in the 'tests' directory, and
        debugging utilities in the 'debug' directory are under
        the BSD Zero Clause License (0BSD).

      - The GNU Autotools based build system contains files that are
        under GNU GPLv2+, GNU GPLv3+, and a few permissive licenses.
        These files don't affect the licensing of the binaries being
        built.

      - The 'extra' directory contains files that are under various
        free software licenses. These aren't built or installed as
        part of XZ Utils.

    The following command may be helpful in finding per-file license
    information. It works on xz.git and on a clean file tree extracted
    from a release tarball.

        sh build-aux/license-check.sh -v

    For the files under the BSD Zero Clause License (0BSD), if
    a copyright notice is needed, the following is sufficient:

        Copyright (C) The XZ Utils authors and contributors

    If you copy significant amounts of 0BSD-licensed code from XZ Utils
    into your project, acknowledging this somewhere in your software is
    polite (especially if it is proprietary, non-free software), but
    it is not legally required by the license terms. Here is an example
    of a good notice to put into "about box" or into documentation:

        This software includes code from XZ Utils <https://tukaani.org/xz/>.

    The following license texts are included in the following files:
      - COPYING.0BSD: BSD Zero Clause License
      - COPYING.LGPLv2.1: GNU Lesser General Public License version 2.1
      - COPYING.GPLv2: GNU General Public License version 2
      - COPYING.GPLv3: GNU General Public License version 3

    If you have questions, don't hesitate to ask for more information.
    The contact information is in the README file.


===== zlib-ng-2.3.3 =====

(C) 1995-2024 Jean-loup Gailly and Mark Adler

This software is provided 'as-is', without any express or implied
warranty. In no event will the authors be held liable for any damages
arising from the use of this software.

Permission is granted to anyone to use this software for any purpose,
including commercial applications, and to alter it and redistribute it
freely, subject to the following restrictions:

1. The origin of this software must not be misrepresented; you must not
   claim that you wrote the original software. If you use this software
   in a product, an acknowledgment in the product documentation would be
   appreciated but is not required.

2. Altered source versions must be plainly marked as such, and must not be
   misrepresented as being the original software.

3. This notice may not be removed or altered from any source distribution.
````

<a id="text-28"></a>

### pillow-heif: pillow_heif-1.8.1.dist-info/licenses/LICENSE.txt

Source: `pillow-heif 1.8.1: pillow_heif-1.8.1.dist-info/licenses/LICENSE.txt`. SHA-256: `9e2635f155b00af5a46cb2f2c9b052072ec546d59837ee74efc9cba2cbb83f3d`. UTF-8/LF bytes: 1546.

````text
Copyright (c) 2021-2023, Pillow-Heif contributors.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

    * Redistributions of source code must retain the above copyright
       notice, this list of conditions and the following disclaimer.

    * Redistributions in binary form must reproduce the above
       copyright notice, this list of conditions and the following
       disclaimer in the documentation and/or other materials provided
       with the distribution.

    * Neither the name of the Pillow-Heif nor the names of any
       contributors may be used to endorse or promote products derived
       from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
````

<a id="text-29"></a>

### pillow-heif: pillow_heif-1.8.1.dist-info/licenses/LICENSES_bundled.txt

Source: `pillow-heif 1.8.1: pillow_heif-1.8.1.dist-info/licenses/LICENSES_bundled.txt`. SHA-256: `7c5eab5b0bc4ed21688891149081b38432b2bbe8e8b49c12708a8ddcf7d700d8`. UTF-8/LF bytes: 1147.

````text
The "pillow-heif" source code is licensed under the BSD-3-Clause license, see LICENSE.txt.
License for "pillow-heif" binary wheels: GPLv2, due to base library licenses.

Binary wheels combine several license-compatible libraries. Here they are listed.

Name: libheif
License: LGPLv3
Files: libheif.[dylib|so|dll]
  For details, see https://github.com/strukturag/libheif/tree/v1.23.6/COPYING
  Source code: https://github.com/strukturag/libheif/tree/v1.23.6

Name: libde265
License: LGPLv3
Files: libde265.[dylib|so|dll]
  For details, see https://github.com/strukturag/libde265/tree/v1.1.3/COPYING
  Source code: https://github.com/strukturag/libde265/tree/v1.1.3

Name: x265
License: GPLv2
Files: libx265.[dylib|so|dll]
  For details, see https://github.com/Multicorewareinc/x265/tree/4.3/COPYING
  Source code: https://github.com/Multicorewareinc/x265/tree/4.3

Name: MinGW-w64 runtime (Windows wheels only)
License: GPL-3.0-with-GCC-exception (libgcc, libstdc++), MIT and BSD (libwinpthread)
Files: libgcc_s_seh-1.dll, libstdc++-6.dll, libwinpthread-1.dll
  For details, see https://sourceforge.net/p/mingw-w64/mingw-w64/ci/master/tree/COPYING
````

<a id="text-30"></a>

### scipy: scipy-1.18.1.dist-info/LICENSE.txt

Source: `scipy 1.18.1: scipy-1.18.1.dist-info/LICENSE.txt`. SHA-256: `c803fb373fe0f3b038f3f841bf706d63e076ffc554ec889cdeb258e5b29802bb`. UTF-8/LF bytes: 45851.

````text
Copyright (c) 2001-2002 Enthought, Inc. 2003, SciPy Developers.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions
are met:

1. Redistributions of source code must retain the above copyright
   notice, this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above
   copyright notice, this list of conditions and the following
   disclaimer in the documentation and/or other materials provided
   with the distribution.

3. Neither the name of the copyright holder nor the names of its
   contributors may be used to endorse or promote products derived
   from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

----


----

This binary distribution of SciPy can also bundle the following software
(depending on the build):


Name: OpenBLAS
Files: scipy.libs\libscipy_openblas*.dll
Description: bundled as a dynamically linked library
Availability: https://github.com/OpenMathLib/OpenBLAS/
License: BSD-3-Clause
  Copyright (c) 2011-2014, The OpenBLAS Project
  All rights reserved.
  
  Redistribution and use in source and binary forms, with or without
  modification, are permitted provided that the following conditions are
  met:
  
     1. Redistributions of source code must retain the above copyright
        notice, this list of conditions and the following disclaimer.
  
     2. Redistributions in binary form must reproduce the above copyright
        notice, this list of conditions and the following disclaimer in
        the documentation and/or other materials provided with the
        distribution.
     3. Neither the name of the OpenBLAS project nor the names of 
        its contributors may be used to endorse or promote products 
        derived from this software without specific prior written 
        permission.
  
  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
  AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
  ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
  LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
  DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
  SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
  CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
  OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
  USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


Name: LAPACK
Files: scipy.libs\libscipy_openblas*.dll
Description: bundled in OpenBLAS
Availability: https://github.com/OpenMathLib/OpenBLAS/
License: BSD-3-Clause-Open-MPI
  Copyright (c) 1992-2013 The University of Tennessee and The University
                          of Tennessee Research Foundation.  All rights
                          reserved.
  Copyright (c) 2000-2013 The University of California Berkeley. All
                          rights reserved.
  Copyright (c) 2006-2013 The University of Colorado Denver.  All rights
                          reserved.
  
  $COPYRIGHT$
  
  Additional copyrights may follow
  
  $HEADER$
  
  Redistribution and use in source and binary forms, with or without
  modification, are permitted provided that the following conditions are
  met:
  
  - Redistributions of source code must retain the above copyright
    notice, this list of conditions and the following disclaimer.
  
  - Redistributions in binary form must reproduce the above copyright
    notice, this list of conditions and the following disclaimer listed
    in this license in the documentation and/or other materials
    provided with the distribution.
  
  - Neither the name of the copyright holders nor the names of its
    contributors may be used to endorse or promote products derived from
    this software without specific prior written permission.
  
  The copyright holders provide no reassurances that the source code
  provided does not infringe any patent, copyright, or any other
  intellectual property rights of third parties.  The copyright holders
  disclaim any liability to any recipient for claims brought against
  recipient by any third party for infringement of that parties
  intellectual property rights.
  
  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
  "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
  LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
  A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
  OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
  SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
  LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
  DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
  THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
  OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


Name: GCC runtime library
Files: scipy.libs\libscipy_openblas*.dll
Description: statically linked to files compiled with gcc
Availability: https://gcc.gnu.org/git/?p=gcc.git;a=tree;f=libgfortran
License: GPL-3.0-or-later WITH GCC-exception-3.1
  Copyright (C) 2002-2017 Free Software Foundation, Inc.
  
  Libgfortran is free software; you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation; either version 3, or (at your option)
  any later version.
  
  Libgfortran is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.
  
  Under Section 7 of GPL version 3, you are granted additional
  permissions described in the GCC Runtime Library Exception, version
  3.1, as published by the Free Software Foundation.
  
  You should have received a copy of the GNU General Public License and
  a copy of the GCC Runtime Library Exception along with this program;
  see the files COPYING3 and COPYING.RUNTIME respectively.  If not, see
  <http://www.gnu.org/licenses/>.


----

Full text of license texts referred to above follows (that they are
listed below does not necessarily imply the conditions apply to the
present binary release):

----

GCC RUNTIME LIBRARY EXCEPTION

Version 3.1, 31 March 2009

Copyright (C) 2009 Free Software Foundation, Inc. <http://fsf.org/>

Everyone is permitted to copy and distribute verbatim copies of this
license document, but changing it is not allowed.

This GCC Runtime Library Exception ("Exception") is an additional
permission under section 7 of the GNU General Public License, version
3 ("GPLv3"). It applies to a given file (the "Runtime Library") that
bears a notice placed by the copyright holder of the file stating that
the file is governed by GPLv3 along with this Exception.

When you use GCC to compile a program, GCC may combine portions of
certain GCC header files and runtime libraries with the compiled
program. The purpose of this Exception is to allow compilation of
non-GPL (including proprietary) programs to use, in this way, the
header files and runtime libraries covered by this Exception.

0. Definitions.

A file is an "Independent Module" if it either requires the Runtime
Library for execution after a Compilation Process, or makes use of an
interface provided by the Runtime Library, but is not otherwise based
on the Runtime Library.

"GCC" means a version of the GNU Compiler Collection, with or without
modifications, governed by version 3 (or a specified later version) of
the GNU General Public License (GPL) with the option of using any
subsequent versions published by the FSF.

"GPL-compatible Software" is software whose conditions of propagation,
modification and use would permit combination with GCC in accord with
the license of GCC.

"Target Code" refers to output from any compiler for a real or virtual
target processor architecture, in executable form or suitable for
input to an assembler, loader, linker and/or execution
phase. Notwithstanding that, Target Code does not include data in any
format that is used as a compiler intermediate representation, or used
for producing a compiler intermediate representation.

The "Compilation Process" transforms code entirely represented in
non-intermediate languages designed for human-written code, and/or in
Java Virtual Machine byte code, into Target Code. Thus, for example,
use of source code generators and preprocessors need not be considered
part of the Compilation Process, since the Compilation Process can be
understood as starting with the output of the generators or
preprocessors.

A Compilation Process is "Eligible" if it is done using GCC, alone or
with other GPL-compatible software, or if it is done without using any
work based on GCC. For example, using non-GPL-compatible Software to
optimize any GCC intermediate representations would not qualify as an
Eligible Compilation Process.

1. Grant of Additional Permission.

You have permission to propagate a work of Target Code formed by
combining the Runtime Library with Independent Modules, even if such
propagation would otherwise violate the terms of GPLv3, provided that
all Target Code was generated by Eligible Compilation Processes. You
may then convey such a combination under terms of your choice,
consistent with the licensing of the Independent Modules.

2. No Weakening of GCC Copyleft.

The availability of this Exception does not imply any general
presumption that third-party software is unaffected by the copyleft
requirements of the license of GCC.

----

                    GNU GENERAL PUBLIC LICENSE
                       Version 3, 29 June 2007

 Copyright (C) 2007 Free Software Foundation, Inc. <http://fsf.org/>
 Everyone is permitted to copy and distribute verbatim copies
 of this license document, but changing it is not allowed.

                            Preamble

  The GNU General Public License is a free, copyleft license for
software and other kinds of works.

  The licenses for most software and other practical works are designed
to take away your freedom to share and change the works.  By contrast,
the GNU General Public License is intended to guarantee your freedom to
share and change all versions of a program--to make sure it remains free
software for all its users.  We, the Free Software Foundation, use the
GNU General Public License for most of our software; it applies also to
any other work released this way by its authors.  You can apply it to
your programs, too.

  When we speak of free software, we are referring to freedom, not
price.  Our General Public Licenses are designed to make sure that you
have the freedom to distribute copies of free software (and charge for
them if you wish), that you receive source code or can get it if you
want it, that you can change the software or use pieces of it in new
free programs, and that you know you can do these things.

  To protect your rights, we need to prevent others from denying you
these rights or asking you to surrender the rights.  Therefore, you have
certain responsibilities if you distribute copies of the software, or if
you modify it: responsibilities to respect the freedom of others.

  For example, if you distribute copies of such a program, whether
gratis or for a fee, you must pass on to the recipients the same
freedoms that you received.  You must make sure that they, too, receive
or can get the source code.  And you must show them these terms so they
know their rights.

  Developers that use the GNU GPL protect your rights with two steps:
(1) assert copyright on the software, and (2) offer you this License
giving you legal permission to copy, distribute and/or modify it.

  For the developers' and authors' protection, the GPL clearly explains
that there is no warranty for this free software.  For both users' and
authors' sake, the GPL requires that modified versions be marked as
changed, so that their problems will not be attributed erroneously to
authors of previous versions.

  Some devices are designed to deny users access to install or run
modified versions of the software inside them, although the manufacturer
can do so.  This is fundamentally incompatible with the aim of
protecting users' freedom to change the software.  The systematic
pattern of such abuse occurs in the area of products for individuals to
use, which is precisely where it is most unacceptable.  Therefore, we
have designed this version of the GPL to prohibit the practice for those
products.  If such problems arise substantially in other domains, we
stand ready to extend this provision to those domains in future versions
of the GPL, as needed to protect the freedom of users.

  Finally, every program is threatened constantly by software patents.
States should not allow patents to restrict development and use of
software on general-purpose computers, but in those that do, we wish to
avoid the special danger that patents applied to a free program could
make it effectively proprietary.  To prevent this, the GPL assures that
patents cannot be used to render the program non-free.

  The precise terms and conditions for copying, distribution and
modification follow.

                       TERMS AND CONDITIONS

  0. Definitions.

  "This License" refers to version 3 of the GNU General Public License.

  "Copyright" also means copyright-like laws that apply to other kinds of
works, such as semiconductor masks.

  "The Program" refers to any copyrightable work licensed under this
License.  Each licensee is addressed as "you".  "Licensees" and
"recipients" may be individuals or organizations.

  To "modify" a work means to copy from or adapt all or part of the work
in a fashion requiring copyright permission, other than the making of an
exact copy.  The resulting work is called a "modified version" of the
earlier work or a work "based on" the earlier work.

  A "covered work" means either the unmodified Program or a work based
on the Program.

  To "propagate" a work means to do anything with it that, without
permission, would make you directly or secondarily liable for
infringement under applicable copyright law, except executing it on a
computer or modifying a private copy.  Propagation includes copying,
distribution (with or without modification), making available to the
public, and in some countries other activities as well.

  To "convey" a work means any kind of propagation that enables other
parties to make or receive copies.  Mere interaction with a user through
a computer network, with no transfer of a copy, is not conveying.

  An interactive user interface displays "Appropriate Legal Notices"
to the extent that it includes a convenient and prominently visible
feature that (1) displays an appropriate copyright notice, and (2)
tells the user that there is no warranty for the work (except to the
extent that warranties are provided), that licensees may convey the
work under this License, and how to view a copy of this License.  If
the interface presents a list of user commands or options, such as a
menu, a prominent item in the list meets this criterion.

  1. Source Code.

  The "source code" for a work means the preferred form of the work
for making modifications to it.  "Object code" means any non-source
form of a work.

  A "Standard Interface" means an interface that either is an official
standard defined by a recognized standards body, or, in the case of
interfaces specified for a particular programming language, one that
is widely used among developers working in that language.

  The "System Libraries" of an executable work include anything, other
than the work as a whole, that (a) is included in the normal form of
packaging a Major Component, but which is not part of that Major
Component, and (b) serves only to enable use of the work with that
Major Component, or to implement a Standard Interface for which an
implementation is available to the public in source code form.  A
"Major Component", in this context, means a major essential component
(kernel, window system, and so on) of the specific operating system
(if any) on which the executable work runs, or a compiler used to
produce the work, or an object code interpreter used to run it.

  The "Corresponding Source" for a work in object code form means all
the source code needed to generate, install, and (for an executable
work) run the object code and to modify the work, including scripts to
control those activities.  However, it does not include the work's
System Libraries, or general-purpose tools or generally available free
programs which are used unmodified in performing those activities but
which are not part of the work.  For example, Corresponding Source
includes interface definition files associated with source files for
the work, and the source code for shared libraries and dynamically
linked subprograms that the work is specifically designed to require,
such as by intimate data communication or control flow between those
subprograms and other parts of the work.

  The Corresponding Source need not include anything that users
can regenerate automatically from other parts of the Corresponding
Source.

  The Corresponding Source for a work in source code form is that
same work.

  2. Basic Permissions.

  All rights granted under this License are granted for the term of
copyright on the Program, and are irrevocable provided the stated
conditions are met.  This License explicitly affirms your unlimited
permission to run the unmodified Program.  The output from running a
covered work is covered by this License only if the output, given its
content, constitutes a covered work.  This License acknowledges your
rights of fair use or other equivalent, as provided by copyright law.

  You may make, run and propagate covered works that you do not
convey, without conditions so long as your license otherwise remains
in force.  You may convey covered works to others for the sole purpose
of having them make modifications exclusively for you, or provide you
with facilities for running those works, provided that you comply with
the terms of this License in conveying all material for which you do
not control copyright.  Those thus making or running the covered works
for you must do so exclusively on your behalf, under your direction
and control, on terms that prohibit them from making any copies of
your copyrighted material outside their relationship with you.

  Conveying under any other circumstances is permitted solely under
the conditions stated below.  Sublicensing is not allowed; section 10
makes it unnecessary.

  3. Protecting Users' Legal Rights From Anti-Circumvention Law.

  No covered work shall be deemed part of an effective technological
measure under any applicable law fulfilling obligations under article
11 of the WIPO copyright treaty adopted on 20 December 1996, or
similar laws prohibiting or restricting circumvention of such
measures.

  When you convey a covered work, you waive any legal power to forbid
circumvention of technological measures to the extent such circumvention
is effected by exercising rights under this License with respect to
the covered work, and you disclaim any intention to limit operation or
modification of the work as a means of enforcing, against the work's
users, your or third parties' legal rights to forbid circumvention of
technological measures.

  4. Conveying Verbatim Copies.

  You may convey verbatim copies of the Program's source code as you
receive it, in any medium, provided that you conspicuously and
appropriately publish on each copy an appropriate copyright notice;
keep intact all notices stating that this License and any
non-permissive terms added in accord with section 7 apply to the code;
keep intact all notices of the absence of any warranty; and give all
recipients a copy of this License along with the Program.

  You may charge any price or no price for each copy that you convey,
and you may offer support or warranty protection for a fee.

  5. Conveying Modified Source Versions.

  You may convey a work based on the Program, or the modifications to
produce it from the Program, in the form of source code under the
terms of section 4, provided that you also meet all of these conditions:

    a) The work must carry prominent notices stating that you modified
    it, and giving a relevant date.

    b) The work must carry prominent notices stating that it is
    released under this License and any conditions added under section
    7.  This requirement modifies the requirement in section 4 to
    "keep intact all notices".

    c) You must license the entire work, as a whole, under this
    License to anyone who comes into possession of a copy.  This
    License will therefore apply, along with any applicable section 7
    additional terms, to the whole of the work, and all its parts,
    regardless of how they are packaged.  This License gives no
    permission to license the work in any other way, but it does not
    invalidate such permission if you have separately received it.

    d) If the work has interactive user interfaces, each must display
    Appropriate Legal Notices; however, if the Program has interactive
    interfaces that do not display Appropriate Legal Notices, your
    work need not make them do so.

  A compilation of a covered work with other separate and independent
works, which are not by their nature extensions of the covered work,
and which are not combined with it such as to form a larger program,
in or on a volume of a storage or distribution medium, is called an
"aggregate" if the compilation and its resulting copyright are not
used to limit the access or legal rights of the compilation's users
beyond what the individual works permit.  Inclusion of a covered work
in an aggregate does not cause this License to apply to the other
parts of the aggregate.

  6. Conveying Non-Source Forms.

  You may convey a covered work in object code form under the terms
of sections 4 and 5, provided that you also convey the
machine-readable Corresponding Source under the terms of this License,
in one of these ways:

    a) Convey the object code in, or embodied in, a physical product
    (including a physical distribution medium), accompanied by the
    Corresponding Source fixed on a durable physical medium
    customarily used for software interchange.

    b) Convey the object code in, or embodied in, a physical product
    (including a physical distribution medium), accompanied by a
    written offer, valid for at least three years and valid for as
    long as you offer spare parts or customer support for that product
    model, to give anyone who possesses the object code either (1) a
    copy of the Corresponding Source for all the software in the
    product that is covered by this License, on a durable physical
    medium customarily used for software interchange, for a price no
    more than your reasonable cost of physically performing this
    conveying of source, or (2) access to copy the
    Corresponding Source from a network server at no charge.

    c) Convey individual copies of the object code with a copy of the
    written offer to provide the Corresponding Source.  This
    alternative is allowed only occasionally and noncommercially, and
    only if you received the object code with such an offer, in accord
    with subsection 6b.

    d) Convey the object code by offering access from a designated
    place (gratis or for a charge), and offer equivalent access to the
    Corresponding Source in the same way through the same place at no
    further charge.  You need not require recipients to copy the
    Corresponding Source along with the object code.  If the place to
    copy the object code is a network server, the Corresponding Source
    may be on a different server (operated by you or a third party)
    that supports equivalent copying facilities, provided you maintain
    clear directions next to the object code saying where to find the
    Corresponding Source.  Regardless of what server hosts the
    Corresponding Source, you remain obligated to ensure that it is
    available for as long as needed to satisfy these requirements.

    e) Convey the object code using peer-to-peer transmission, provided
    you inform other peers where the object code and Corresponding
    Source of the work are being offered to the general public at no
    charge under subsection 6d.

  A separable portion of the object code, whose source code is excluded
from the Corresponding Source as a System Library, need not be
included in conveying the object code work.

  A "User Product" is either (1) a "consumer product", which means any
tangible personal property which is normally used for personal, family,
or household purposes, or (2) anything designed or sold for incorporation
into a dwelling.  In determining whether a product is a consumer product,
doubtful cases shall be resolved in favor of coverage.  For a particular
product received by a particular user, "normally used" refers to a
typical or common use of that class of product, regardless of the status
of the particular user or of the way in which the particular user
actually uses, or expects or is expected to use, the product.  A product
is a consumer product regardless of whether the product has substantial
commercial, industrial or non-consumer uses, unless such uses represent
the only significant mode of use of the product.

  "Installation Information" for a User Product means any methods,
procedures, authorization keys, or other information required to install
and execute modified versions of a covered work in that User Product from
a modified version of its Corresponding Source.  The information must
suffice to ensure that the continued functioning of the modified object
code is in no case prevented or interfered with solely because
modification has been made.

  If you convey an object code work under this section in, or with, or
specifically for use in, a User Product, and the conveying occurs as
part of a transaction in which the right of possession and use of the
User Product is transferred to the recipient in perpetuity or for a
fixed term (regardless of how the transaction is characterized), the
Corresponding Source conveyed under this section must be accompanied
by the Installation Information.  But this requirement does not apply
if neither you nor any third party retains the ability to install
modified object code on the User Product (for example, the work has
been installed in ROM).

  The requirement to provide Installation Information does not include a
requirement to continue to provide support service, warranty, or updates
for a work that has been modified or installed by the recipient, or for
the User Product in which it has been modified or installed.  Access to a
network may be denied when the modification itself materially and
adversely affects the operation of the network or violates the rules and
protocols for communication across the network.

  Corresponding Source conveyed, and Installation Information provided,
in accord with this section must be in a format that is publicly
documented (and with an implementation available to the public in
source code form), and must require no special password or key for
unpacking, reading or copying.

  7. Additional Terms.

  "Additional permissions" are terms that supplement the terms of this
License by making exceptions from one or more of its conditions.
Additional permissions that are applicable to the entire Program shall
be treated as though they were included in this License, to the extent
that they are valid under applicable law.  If additional permissions
apply only to part of the Program, that part may be used separately
under those permissions, but the entire Program remains governed by
this License without regard to the additional permissions.

  When you convey a copy of a covered work, you may at your option
remove any additional permissions from that copy, or from any part of
it.  (Additional permissions may be written to require their own
removal in certain cases when you modify the work.)  You may place
additional permissions on material, added by you to a covered work,
for which you have or can give appropriate copyright permission.

  Notwithstanding any other provision of this License, for material you
add to a covered work, you may (if authorized by the copyright holders of
that material) supplement the terms of this License with terms:

    a) Disclaiming warranty or limiting liability differently from the
    terms of sections 15 and 16 of this License; or

    b) Requiring preservation of specified reasonable legal notices or
    author attributions in that material or in the Appropriate Legal
    Notices displayed by works containing it; or

    c) Prohibiting misrepresentation of the origin of that material, or
    requiring that modified versions of such material be marked in
    reasonable ways as different from the original version; or

    d) Limiting the use for publicity purposes of names of licensors or
    authors of the material; or

    e) Declining to grant rights under trademark law for use of some
    trade names, trademarks, or service marks; or

    f) Requiring indemnification of licensors and authors of that
    material by anyone who conveys the material (or modified versions of
    it) with contractual assumptions of liability to the recipient, for
    any liability that these contractual assumptions directly impose on
    those licensors and authors.

  All other non-permissive additional terms are considered "further
restrictions" within the meaning of section 10.  If the Program as you
received it, or any part of it, contains a notice stating that it is
governed by this License along with a term that is a further
restriction, you may remove that term.  If a license document contains
a further restriction but permits relicensing or conveying under this
License, you may add to a covered work material governed by the terms
of that license document, provided that the further restriction does
not survive such relicensing or conveying.

  If you add terms to a covered work in accord with this section, you
must place, in the relevant source files, a statement of the
additional terms that apply to those files, or a notice indicating
where to find the applicable terms.

  Additional terms, permissive or non-permissive, may be stated in the
form of a separately written license, or stated as exceptions;
the above requirements apply either way.

  8. Termination.

  You may not propagate or modify a covered work except as expressly
provided under this License.  Any attempt otherwise to propagate or
modify it is void, and will automatically terminate your rights under
this License (including any patent licenses granted under the third
paragraph of section 11).

  However, if you cease all violation of this License, then your
license from a particular copyright holder is reinstated (a)
provisionally, unless and until the copyright holder explicitly and
finally terminates your license, and (b) permanently, if the copyright
holder fails to notify you of the violation by some reasonable means
prior to 60 days after the cessation.

  Moreover, your license from a particular copyright holder is
reinstated permanently if the copyright holder notifies you of the
violation by some reasonable means, this is the first time you have
received notice of violation of this License (for any work) from that
copyright holder, and you cure the violation prior to 30 days after
your receipt of the notice.

  Termination of your rights under this section does not terminate the
licenses of parties who have received copies or rights from you under
this License.  If your rights have been terminated and not permanently
reinstated, you do not qualify to receive new licenses for the same
material under section 10.

  9. Acceptance Not Required for Having Copies.

  You are not required to accept this License in order to receive or
run a copy of the Program.  Ancillary propagation of a covered work
occurring solely as a consequence of using peer-to-peer transmission
to receive a copy likewise does not require acceptance.  However,
nothing other than this License grants you permission to propagate or
modify any covered work.  These actions infringe copyright if you do
not accept this License.  Therefore, by modifying or propagating a
covered work, you indicate your acceptance of this License to do so.

  10. Automatic Licensing of Downstream Recipients.

  Each time you convey a covered work, the recipient automatically
receives a license from the original licensors, to run, modify and
propagate that work, subject to this License.  You are not responsible
for enforcing compliance by third parties with this License.

  An "entity transaction" is a transaction transferring control of an
organization, or substantially all assets of one, or subdividing an
organization, or merging organizations.  If propagation of a covered
work results from an entity transaction, each party to that
transaction who receives a copy of the work also receives whatever
licenses to the work the party's predecessor in interest had or could
give under the previous paragraph, plus a right to possession of the
Corresponding Source of the work from the predecessor in interest, if
the predecessor has it or can get it with reasonable efforts.

  You may not impose any further restrictions on the exercise of the
rights granted or affirmed under this License.  For example, you may
not impose a license fee, royalty, or other charge for exercise of
rights granted under this License, and you may not initiate litigation
(including a cross-claim or counterclaim in a lawsuit) alleging that
any patent claim is infringed by making, using, selling, offering for
sale, or importing the Program or any portion of it.

  11. Patents.

  A "contributor" is a copyright holder who authorizes use under this
License of the Program or a work on which the Program is based.  The
work thus licensed is called the contributor's "contributor version".

  A contributor's "essential patent claims" are all patent claims
owned or controlled by the contributor, whether already acquired or
hereafter acquired, that would be infringed by some manner, permitted
by this License, of making, using, or selling its contributor version,
but do not include claims that would be infringed only as a
consequence of further modification of the contributor version.  For
purposes of this definition, "control" includes the right to grant
patent sublicenses in a manner consistent with the requirements of
this License.

  Each contributor grants you a non-exclusive, worldwide, royalty-free
patent license under the contributor's essential patent claims, to
make, use, sell, offer for sale, import and otherwise run, modify and
propagate the contents of its contributor version.

  In the following three paragraphs, a "patent license" is any express
agreement or commitment, however denominated, not to enforce a patent
(such as an express permission to practice a patent or covenant not to
sue for patent infringement).  To "grant" such a patent license to a
party means to make such an agreement or commitment not to enforce a
patent against the party.

  If you convey a covered work, knowingly relying on a patent license,
and the Corresponding Source of the work is not available for anyone
to copy, free of charge and under the terms of this License, through a
publicly available network server or other readily accessible means,
then you must either (1) cause the Corresponding Source to be so
available, or (2) arrange to deprive yourself of the benefit of the
patent license for this particular work, or (3) arrange, in a manner
consistent with the requirements of this License, to extend the patent
license to downstream recipients.  "Knowingly relying" means you have
actual knowledge that, but for the patent license, your conveying the
covered work in a country, or your recipient's use of the covered work
in a country, would infringe one or more identifiable patents in that
country that you have reason to believe are valid.

  If, pursuant to or in connection with a single transaction or
arrangement, you convey, or propagate by procuring conveyance of, a
covered work, and grant a patent license to some of the parties
receiving the covered work authorizing them to use, propagate, modify
or convey a specific copy of the covered work, then the patent license
you grant is automatically extended to all recipients of the covered
work and works based on it.

  A patent license is "discriminatory" if it does not include within
the scope of its coverage, prohibits the exercise of, or is
conditioned on the non-exercise of one or more of the rights that are
specifically granted under this License.  You may not convey a covered
work if you are a party to an arrangement with a third party that is
in the business of distributing software, under which you make payment
to the third party based on the extent of your activity of conveying
the work, and under which the third party grants, to any of the
parties who would receive the covered work from you, a discriminatory
patent license (a) in connection with copies of the covered work
conveyed by you (or copies made from those copies), or (b) primarily
for and in connection with specific products or compilations that
contain the covered work, unless you entered into that arrangement,
or that patent license was granted, prior to 28 March 2007.

  Nothing in this License shall be construed as excluding or limiting
any implied license or other defenses to infringement that may
otherwise be available to you under applicable patent law.

  12. No Surrender of Others' Freedom.

  If conditions are imposed on you (whether by court order, agreement or
otherwise) that contradict the conditions of this License, they do not
excuse you from the conditions of this License.  If you cannot convey a
covered work so as to satisfy simultaneously your obligations under this
License and any other pertinent obligations, then as a consequence you may
not convey it at all.  For example, if you agree to terms that obligate you
to collect a royalty for further conveying from those to whom you convey
the Program, the only way you could satisfy both those terms and this
License would be to refrain entirely from conveying the Program.

  13. Use with the GNU Affero General Public License.

  Notwithstanding any other provision of this License, you have
permission to link or combine any covered work with a work licensed
under version 3 of the GNU Affero General Public License into a single
combined work, and to convey the resulting work.  The terms of this
License will continue to apply to the part which is the covered work,
but the special requirements of the GNU Affero General Public License,
section 13, concerning interaction through a network will apply to the
combination as such.

  14. Revised Versions of this License.

  The Free Software Foundation may publish revised and/or new versions of
the GNU General Public License from time to time.  Such new versions will
be similar in spirit to the present version, but may differ in detail to
address new problems or concerns.

  Each version is given a distinguishing version number.  If the
Program specifies that a certain numbered version of the GNU General
Public License "or any later version" applies to it, you have the
option of following the terms and conditions either of that numbered
version or of any later version published by the Free Software
Foundation.  If the Program does not specify a version number of the
GNU General Public License, you may choose any version ever published
by the Free Software Foundation.

  If the Program specifies that a proxy can decide which future
versions of the GNU General Public License can be used, that proxy's
public statement of acceptance of a version permanently authorizes you
to choose that version for the Program.

  Later license versions may give you additional or different
permissions.  However, no additional obligations are imposed on any
author or copyright holder as a result of your choosing to follow a
later version.

  15. Disclaimer of Warranty.

  THERE IS NO WARRANTY FOR THE PROGRAM, TO THE EXTENT PERMITTED BY
APPLICABLE LAW.  EXCEPT WHEN OTHERWISE STATED IN WRITING THE COPYRIGHT
HOLDERS AND/OR OTHER PARTIES PROVIDE THE PROGRAM "AS IS" WITHOUT WARRANTY
OF ANY KIND, EITHER EXPRESSED OR IMPLIED, INCLUDING, BUT NOT LIMITED TO,
THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
PURPOSE.  THE ENTIRE RISK AS TO THE QUALITY AND PERFORMANCE OF THE PROGRAM
IS WITH YOU.  SHOULD THE PROGRAM PROVE DEFECTIVE, YOU ASSUME THE COST OF
ALL NECESSARY SERVICING, REPAIR OR CORRECTION.

  16. Limitation of Liability.

  IN NO EVENT UNLESS REQUIRED BY APPLICABLE LAW OR AGREED TO IN WRITING
WILL ANY COPYRIGHT HOLDER, OR ANY OTHER PARTY WHO MODIFIES AND/OR CONVEYS
THE PROGRAM AS PERMITTED ABOVE, BE LIABLE TO YOU FOR DAMAGES, INCLUDING ANY
GENERAL, SPECIAL, INCIDENTAL OR CONSEQUENTIAL DAMAGES ARISING OUT OF THE
USE OR INABILITY TO USE THE PROGRAM (INCLUDING BUT NOT LIMITED TO LOSS OF
DATA OR DATA BEING RENDERED INACCURATE OR LOSSES SUSTAINED BY YOU OR THIRD
PARTIES OR A FAILURE OF THE PROGRAM TO OPERATE WITH ANY OTHER PROGRAMS),
EVEN IF SUCH HOLDER OR OTHER PARTY HAS BEEN ADVISED OF THE POSSIBILITY OF
SUCH DAMAGES.

  17. Interpretation of Sections 15 and 16.

  If the disclaimer of warranty and limitation of liability provided
above cannot be given local legal effect according to their terms,
reviewing courts shall apply local law that most closely approximates
an absolute waiver of all civil liability in connection with the
Program, unless a warranty or assumption of liability accompanies a
copy of the Program in return for a fee.

                     END OF TERMS AND CONDITIONS

            How to Apply These Terms to Your New Programs

  If you develop a new program, and you want it to be of the greatest
possible use to the public, the best way to achieve this is to make it
free software which everyone can redistribute and change under these terms.

  To do so, attach the following notices to the program.  It is safest
to attach them to the start of each source file to most effectively
state the exclusion of warranty; and each file should have at least
the "copyright" line and a pointer to where the full notice is found.

    <one line to give the program's name and a brief idea of what it does.>
    Copyright (C) <year>  <name of author>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

Also add information on how to contact you by electronic and paper mail.

  If the program does terminal interaction, make it output a short
notice like this when it starts in an interactive mode:

    <program>  Copyright (C) <year>  <name of author>
    This program comes with ABSOLUTELY NO WARRANTY; for details type `show w'.
    This is free software, and you are welcome to redistribute it
    under certain conditions; type `show c' for details.

The hypothetical commands `show w' and `show c' should show the appropriate
parts of the General Public License.  Of course, your program's commands
might be different; for a GUI interface, you would use an "about box".

  You should also get your employer (if you work as a programmer) or school,
if any, to sign a "copyright disclaimer" for the program, if necessary.
For more information on this, and how to apply and follow the GNU GPL, see
<http://www.gnu.org/licenses/>.

  The GNU General Public License does not permit incorporating your program
into proprietary programs.  If your program is a subroutine library, you
may consider it more useful to permit linking proprietary applications with
the library.  If this is what you want to do, use the GNU Lesser General
Public License instead of this License.  But first, please read
<http://www.gnu.org/philosophy/why-not-lgpl.html>.
````

<a id="text-31"></a>

### scipy: scipy/_lib/_uarray/LICENSE

Source: `scipy 1.18.1: scipy/_lib/_uarray/LICENSE`. SHA-256: `c80c39b5fce06ba4897e14e0b0a88b54458334d951eb1361402ffad2cfb863b4`. UTF-8/LF bytes: 1514.

````text
BSD 3-Clause License

Copyright (c) 2018, Quansight-Labs
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

* Neither the name of the copyright holder nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
````

<a id="text-32"></a>

### scipy: scipy/fft/_duccfft/LICENSE.md

Source: `scipy 1.18.1: scipy/fft/_duccfft/LICENSE.md`. SHA-256: `c254b2b5fd30ae3c89d36ba061730563b9760fca04f1b746a1b2c3157da2c789`. UTF-8/LF bytes: 1498.

````text
Copyright (C) 2010-2019 Max-Planck-Society
All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.
* Redistributions in binary form must reproduce the above copyright notice, this
  list of conditions and the following disclaimer in the documentation and/or
  other materials provided with the distribution.
* Neither the name of the copyright holder nor the names of its contributors may
  be used to endorse or promote products derived from this software without
  specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
````

<a id="text-33"></a>

### scipy: scipy/integrate/LICENSE_DOP

Source: `scipy 1.18.1: scipy/integrate/LICENSE_DOP`. SHA-256: `ed9bf58c6d74d3fad9d92d1d67d9bff8141d8ab60de784516b0711364fd43357`. UTF-8/LF bytes: 3572.

````text
Copyright (C) 2025 SciPy developers

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

    a. Redistributions of source code must retain the above copyright notice,
       this list of conditions and the following disclaimer.
    b. Redistributions in binary form must reproduce the above copyright
       notice, this list of conditions and the following disclaimer in the
       documentation and/or other materials provided with the distribution.
    c. Names of the SciPy Developers may not be used to endorse or promote
       products derived from this software without specific prior written
       permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDERS OR CONTRIBUTORS
BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
THE POSSIBILITY OF SUCH DAMAGE.


DOP library consisting Dormand-Prince (4)5 and 8(5,3) integrators, is a
C translation of the Fortran code written by Ernst Hairer, and Gerhard
Wanner with the original descriptions below.

* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
    NUMERICAL SOLUTION OF A SYSTEM OF FIRST 0RDER
    ORDINARY DIFFERENTIAL EQUATIONS  Y'=F(X,Y).
    THIS IS AN EXPLICIT RUNGE-KUTTA METHOD OF ORDER 8(5,3)
    DUE TO DORMAND & PRINCE (WITH STEPSIZE CONTROL AND
    DENSE OUTPUT)

    AUTHORS: E. HAIRER AND G. WANNER
             UNIVERSITE DE GENEVE, DEPT. DE MATHEMATIQUES
             CH-1211 GENEVE 24, SWITZERLAND
             E-MAIL:  Ernst.Hairer@math.unige.ch
                      Gerhard.Wanner@math.unige.ch

    THIS CODE IS DESCRIBED IN:
        E. HAIRER, S.P. NORSETT AND G. WANNER, SOLVING ORDINARY
        DIFFERENTIAL EQUATIONS I. NONSTIFF PROBLEMS. 2ND EDITION.
        SPRINGER SERIES IN COMPUTATIONAL MATHEMATICS,
        SPRINGER-VERLAG (1993)

    VERSION OF APRIL 25, 1996
    (latest correction of a small bug: August 8, 2005)

* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
    NUMERICAL SOLUTION OF A SYSTEM OF FIRST 0RDER
    ORDINARY DIFFERENTIAL EQUATIONS  Y'=F(X,Y).
    THIS IS AN EXPLICIT RUNGE-KUTTA METHOD OF ORDER (4)5
    DUE TO DORMAND & PRINCE (WITH STEPSIZE CONTROL AND
    DENSE OUTPUT).

    AUTHORS: E. HAIRER AND G. WANNER
             UNIVERSITE DE GENEVE, DEPT. DE MATHEMATIQUES
             CH-1211 GENEVE 24, SWITZERLAND
             E-MAIL:  Ernst.Hairer@math.unige.ch
                      Gerhard.Wanner@math.unige.ch

    THIS CODE IS DESCRIBED IN:
        E. HAIRER, S.P. NORSETT AND G. WANNER, SOLVING ORDINARY
        DIFFERENTIAL EQUATIONS I. NONSTIFF PROBLEMS. 2ND EDITION.
        SPRINGER SERIES IN COMPUTATIONAL MATHEMATICS,
        SPRINGER-VERLAG (1993)

    VERSION OF APRIL 25, 1996
* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
````

<a id="text-34"></a>

### scipy: scipy/spatial/qhull_src/COPYING_QHULL.txt

Source: `scipy 1.18.1: scipy/spatial/qhull_src/COPYING_QHULL.txt`. SHA-256: `106d55c931fd6a84822e5345d900273d059f1c27310d02567ccb313c5d18c55d`. UTF-8/LF bytes: 1720.

````text
                    Qhull, Copyright (c) 1993-2020
                    
                            C.B. Barber
                           Arlington, MA 
                          
                               and

       The National Science and Technology Research Center for
        Computation and Visualization of Geometric Structures
                        (The Geometry Center)
                       University of Minnesota

                       email: qhull@qhull.org

This software includes Qhull from C.B. Barber and The Geometry Center.  
Files derived from Qhull 1.0 are copyrighted by the Geometry Center.  The
remaining files are copyrighted by C.B. Barber.  Qhull is free software 
and may be obtained via http from www.qhull.org.  It may be freely copied, 
modified, and redistributed under the following conditions:

1. All copyright notices must remain intact in all files.

2. A copy of this text file must be distributed along with any copies 
   of Qhull that you redistribute; this includes copies that you have 
   modified, or copies of programs or other software products that 
   include Qhull.

3. If you modify Qhull, you must include a notice giving the
   name of the person performing the modification, the date of
   modification, and the reason for such modification.

4. When distributing modified versions of Qhull, or other software 
   products that include Qhull, you must provide notice that the original 
   source code may be obtained as noted above.

5. There is no warranty or other guarantee of fitness for Qhull, it is 
   provided solely "as is".  Bug reports or fixes may be sent to 
   qhull_bug@qhull.org; the authors may or may not act on them as 
   they desire.
````

<a id="text-35"></a>

### tifffile: tifffile-2026.10.15.dist-info/licenses/LICENSE

Source: `tifffile 2026.10.15: tifffile-2026.10.15.dist-info/licenses/LICENSE`. SHA-256: `3cf196b1625812d2d119518294043e71017fe858355a58eb48e1e35b61213ce9`. UTF-8/LF bytes: 1529.

````text
BSD-3-Clause license

Copyright (c) 2008-2026, Christoph Gohlke
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice,
   this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its
   contributors may be used to endorse or promote products derived from
   this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
````

<a id="text-36"></a>

### LGPL-3.0.txt

Source: `https://raw.githubusercontent.com/qt/qtbase/v6.12.0/LICENSES/LGPL-3.0-only.txt`. SHA-256: `da7eabb7bafdf7d3ae5e9f223aa5bdc1eece45ac569dc21b3b037520b4464768`. UTF-8/LF bytes: 7651.

Copied from this URL on 2026-11-03.

````text
                   GNU LESSER GENERAL PUBLIC LICENSE
                       Version 3, 29 June 2007

 Copyright (C) 2007 Free Software Foundation, Inc. <http://fsf.org/>
 Everyone is permitted to copy and distribute verbatim copies
 of this license document, but changing it is not allowed.


  This version of the GNU Lesser General Public License incorporates
the terms and conditions of version 3 of the GNU General Public
License, supplemented by the additional permissions listed below.

  0. Additional Definitions.

  As used herein, "this License" refers to version 3 of the GNU Lesser
General Public License, and the "GNU GPL" refers to version 3 of the GNU
General Public License.

  "The Library" refers to a covered work governed by this License,
other than an Application or a Combined Work as defined below.

  An "Application" is any work that makes use of an interface provided
by the Library, but which is not otherwise based on the Library.
Defining a subclass of a class defined by the Library is deemed a mode
of using an interface provided by the Library.

  A "Combined Work" is a work produced by combining or linking an
Application with the Library.  The particular version of the Library
with which the Combined Work was made is also called the "Linked
Version".

  The "Minimal Corresponding Source" for a Combined Work means the
Corresponding Source for the Combined Work, excluding any source code
for portions of the Combined Work that, considered in isolation, are
based on the Application, and not on the Linked Version.

  The "Corresponding Application Code" for a Combined Work means the
object code and/or source code for the Application, including any data
and utility programs needed for reproducing the Combined Work from the
Application, but excluding the System Libraries of the Combined Work.

  1. Exception to Section 3 of the GNU GPL.

  You may convey a covered work under sections 3 and 4 of this License
without being bound by section 3 of the GNU GPL.

  2. Conveying Modified Versions.

  If you modify a copy of the Library, and, in your modifications, a
facility refers to a function or data to be supplied by an Application
that uses the facility (other than as an argument passed when the
facility is invoked), then you may convey a copy of the modified
version:

   a) under this License, provided that you make a good faith effort to
   ensure that, in the event an Application does not supply the
   function or data, the facility still operates, and performs
   whatever part of its purpose remains meaningful, or

   b) under the GNU GPL, with none of the additional permissions of
   this License applicable to that copy.

  3. Object Code Incorporating Material from Library Header Files.

  The object code form of an Application may incorporate material from
a header file that is part of the Library.  You may convey such object
code under terms of your choice, provided that, if the incorporated
material is not limited to numerical parameters, data structure
layouts and accessors, or small macros, inline functions and templates
(ten or fewer lines in length), you do both of the following:

   a) Give prominent notice with each copy of the object code that the
   Library is used in it and that the Library and its use are
   covered by this License.

   b) Accompany the object code with a copy of the GNU GPL and this license
   document.

  4. Combined Works.

  You may convey a Combined Work under terms of your choice that,
taken together, effectively do not restrict modification of the
portions of the Library contained in the Combined Work and reverse
engineering for debugging such modifications, if you also do each of
the following:

   a) Give prominent notice with each copy of the Combined Work that
   the Library is used in it and that the Library and its use are
   covered by this License.

   b) Accompany the Combined Work with a copy of the GNU GPL and this license
   document.

   c) For a Combined Work that displays copyright notices during
   execution, include the copyright notice for the Library among
   these notices, as well as a reference directing the user to the
   copies of the GNU GPL and this license document.

   d) Do one of the following:

       0) Convey the Minimal Corresponding Source under the terms of this
       License, and the Corresponding Application Code in a form
       suitable for, and under terms that permit, the user to
       recombine or relink the Application with a modified version of
       the Linked Version to produce a modified Combined Work, in the
       manner specified by section 6 of the GNU GPL for conveying
       Corresponding Source.

       1) Use a suitable shared library mechanism for linking with the
       Library.  A suitable mechanism is one that (a) uses at run time
       a copy of the Library already present on the user's computer
       system, and (b) will operate properly with a modified version
       of the Library that is interface-compatible with the Linked
       Version.

   e) Provide Installation Information, but only if you would otherwise
   be required to provide such information under section 6 of the
   GNU GPL, and only to the extent that such information is
   necessary to install and execute a modified version of the
   Combined Work produced by recombining or relinking the
   Application with a modified version of the Linked Version. (If
   you use option 4d0, the Installation Information must accompany
   the Minimal Corresponding Source and Corresponding Application
   Code. If you use option 4d1, you must provide the Installation
   Information in the manner specified by section 6 of the GNU GPL
   for conveying Corresponding Source.)

  5. Combined Libraries.

  You may place library facilities that are a work based on the
Library side by side in a single library together with other library
facilities that are not Applications and are not covered by this
License, and convey such a combined library under terms of your
choice, if you do both of the following:

   a) Accompany the combined library with a copy of the same work based
   on the Library, uncombined with any other library facilities,
   conveyed under the terms of this License.

   b) Give prominent notice with the combined library that part of it
   is a work based on the Library, and explaining where to find the
   accompanying uncombined form of the same work.

  6. Revised Versions of the GNU Lesser General Public License.

  The Free Software Foundation may publish revised and/or new versions
of the GNU Lesser General Public License from time to time. Such new
versions will be similar in spirit to the present version, but may
differ in detail to address new problems or concerns.

  Each version is given a distinguishing version number. If the
Library as you received it specifies that a certain numbered version
of the GNU Lesser General Public License "or any later version"
applies to it, you have the option of following the terms and
conditions either of that published version or of any later version
published by the Free Software Foundation. If the Library as you
received it does not specify a version number of the GNU Lesser
General Public License, you may choose any version of the GNU Lesser
General Public License ever published by the Free Software Foundation.

  If the Library as you received it specifies that a proxy can decide
whether future versions of the GNU Lesser General Public License shall
apply, that proxy's public statement of acceptance of any version is
permanent authorization for you to choose that version for the
Library.
````

<a id="text-37"></a>

### x265-COPYING.txt

Source: `https://raw.githubusercontent.com/Multicorewareinc/x265/4.3/COPYING`. SHA-256: `d8afb1bcc7a2cfc603683b168d6987ef0a48e59e0da3693bf55c5d33b67e2b49`. UTF-8/LF bytes: 18120.

Copied from this URL on 2026-11-03.

````text
		    GNU GENERAL PUBLIC LICENSE
		       Version 2, June 1991

 Copyright (C) 1989, 1991 Free Software Foundation, Inc.
     59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 Everyone is permitted to copy and distribute verbatim copies
 of this license document, but changing it is not allowed.

			    Preamble

  The licenses for most software are designed to take away your
freedom to share and change it.  By contrast, the GNU General Public
License is intended to guarantee your freedom to share and change free
software--to make sure the software is free for all its users.  This
General Public License applies to most of the Free Software
Foundation's software and to any other program whose authors commit to
using it.  (Some other Free Software Foundation software is covered by
the GNU Library General Public License instead.)  You can apply it to
your programs, too.

  When we speak of free software, we are referring to freedom, not
price.  Our General Public Licenses are designed to make sure that you
have the freedom to distribute copies of free software (and charge for
this service if you wish), that you receive source code or can get it
if you want it, that you can change the software or use pieces of it
in new free programs; and that you know you can do these things.

  To protect your rights, we need to make restrictions that forbid
anyone to deny you these rights or to ask you to surrender the rights.
These restrictions translate to certain responsibilities for you if you
distribute copies of the software, or if you modify it.

  For example, if you distribute copies of such a program, whether
gratis or for a fee, you must give the recipients all the rights that
you have.  You must make sure that they, too, receive or can get the
source code.  And you must show them these terms so they know their
rights.

  We protect your rights with two steps: (1) copyright the software, and
(2) offer you this license which gives you legal permission to copy,
distribute and/or modify the software.

  Also, for each author's protection and ours, we want to make certain
that everyone understands that there is no warranty for this free
software.  If the software is modified by someone else and passed on, we
want its recipients to know that what they have is not the original, so
that any problems introduced by others will not reflect on the original
authors' reputations.

  Finally, any free program is threatened constantly by software
patents.  We wish to avoid the danger that redistributors of a free
program will individually obtain patent licenses, in effect making the
program proprietary.  To prevent this, we have made it clear that any
patent must be licensed for everyone's free use or not licensed at all.

  The precise terms and conditions for copying, distribution and
modification follow.

		    GNU GENERAL PUBLIC LICENSE
   TERMS AND CONDITIONS FOR COPYING, DISTRIBUTION AND MODIFICATION

  0. This License applies to any program or other work which contains
a notice placed by the copyright holder saying it may be distributed
under the terms of this General Public License.  The "Program", below,
refers to any such program or work, and a "work based on the Program"
means either the Program or any derivative work under copyright law:
that is to say, a work containing the Program or a portion of it,
either verbatim or with modifications and/or translated into another
language.  (Hereinafter, translation is included without limitation in
the term "modification".)  Each licensee is addressed as "you".

Activities other than copying, distribution and modification are not
covered by this License; they are outside its scope.  The act of
running the Program is not restricted, and the output from the Program
is covered only if its contents constitute a work based on the
Program (independent of having been made by running the Program).
Whether that is true depends on what the Program does.

  1. You may copy and distribute verbatim copies of the Program's
source code as you receive it, in any medium, provided that you
conspicuously and appropriately publish on each copy an appropriate
copyright notice and disclaimer of warranty; keep intact all the
notices that refer to this License and to the absence of any warranty;
and give any other recipients of the Program a copy of this License
along with the Program.

You may charge a fee for the physical act of transferring a copy, and
you may at your option offer warranty protection in exchange for a fee.

  2. You may modify your copy or copies of the Program or any portion
of it, thus forming a work based on the Program, and copy and
distribute such modifications or work under the terms of Section 1
above, provided that you also meet all of these conditions:

    a) You must cause the modified files to carry prominent notices
    stating that you changed the files and the date of any change.

    b) You must cause any work that you distribute or publish, that in
    whole or in part contains or is derived from the Program or any
    part thereof, to be licensed as a whole at no charge to all third
    parties under the terms of this License.

    c) If the modified program normally reads commands interactively
    when run, you must cause it, when started running for such
    interactive use in the most ordinary way, to print or display an
    announcement including an appropriate copyright notice and a
    notice that there is no warranty (or else, saying that you provide
    a warranty) and that users may redistribute the program under
    these conditions, and telling the user how to view a copy of this
    License.  (Exception: if the Program itself is interactive but
    does not normally print such an announcement, your work based on
    the Program is not required to print an announcement.)

These requirements apply to the modified work as a whole.  If
identifiable sections of that work are not derived from the Program,
and can be reasonably considered independent and separate works in
themselves, then this License, and its terms, do not apply to those
sections when you distribute them as separate works.  But when you
distribute the same sections as part of a whole which is a work based
on the Program, the distribution of the whole must be on the terms of
this License, whose permissions for other licensees extend to the
entire whole, and thus to each and every part regardless of who wrote it.

Thus, it is not the intent of this section to claim rights or contest
your rights to work written entirely by you; rather, the intent is to
exercise the right to control the distribution of derivative or
collective works based on the Program.

In addition, mere aggregation of another work not based on the Program
with the Program (or with a work based on the Program) on a volume of
a storage or distribution medium does not bring the other work under
the scope of this License.

  3. You may copy and distribute the Program (or a work based on it,
under Section 2) in object code or executable form under the terms of
Sections 1 and 2 above provided that you also do one of the following:

    a) Accompany it with the complete corresponding machine-readable
    source code, which must be distributed under the terms of Sections
    1 and 2 above on a medium customarily used for software interchange; or,

    b) Accompany it with a written offer, valid for at least three
    years, to give any third party, for a charge no more than your
    cost of physically performing source distribution, a complete
    machine-readable copy of the corresponding source code, to be
    distributed under the terms of Sections 1 and 2 above on a medium
    customarily used for software interchange; or,

    c) Accompany it with the information you received as to the offer
    to distribute corresponding source code.  (This alternative is
    allowed only for noncommercial distribution and only if you
    received the program in object code or executable form with such
    an offer, in accord with Subsection b above.)

The source code for a work means the preferred form of the work for
making modifications to it.  For an executable work, complete source
code means all the source code for all modules it contains, plus any
associated interface definition files, plus the scripts used to
control compilation and installation of the executable.  However, as a
special exception, the source code distributed need not include
anything that is normally distributed (in either source or binary
form) with the major components (compiler, kernel, and so on) of the
operating system on which the executable runs, unless that component
itself accompanies the executable.

If distribution of executable or object code is made by offering
access to copy from a designated place, then offering equivalent
access to copy the source code from the same place counts as
distribution of the source code, even though third parties are not
compelled to copy the source along with the object code.

  4. You may not copy, modify, sublicense, or distribute the Program
except as expressly provided under this License.  Any attempt
otherwise to copy, modify, sublicense or distribute the Program is
void, and will automatically terminate your rights under this License.
However, parties who have received copies, or rights, from you under
this License will not have their licenses terminated so long as such
parties remain in full compliance.

  5. You are not required to accept this License, since you have not
signed it.  However, nothing else grants you permission to modify or
distribute the Program or its derivative works.  These actions are
prohibited by law if you do not accept this License.  Therefore, by
modifying or distributing the Program (or any work based on the
Program), you indicate your acceptance of this License to do so, and
all its terms and conditions for copying, distributing or modifying
the Program or works based on it.

  6. Each time you redistribute the Program (or any work based on the
Program), the recipient automatically receives a license from the
original licensor to copy, distribute or modify the Program subject to
these terms and conditions.  You may not impose any further
restrictions on the recipients' exercise of the rights granted herein.
You are not responsible for enforcing compliance by third parties to
this License.

  7. If, as a consequence of a court judgment or allegation of patent
infringement or for any other reason (not limited to patent issues),
conditions are imposed on you (whether by court order, agreement or
otherwise) that contradict the conditions of this License, they do not
excuse you from the conditions of this License.  If you cannot
distribute so as to satisfy simultaneously your obligations under this
License and any other pertinent obligations, then as a consequence you
may not distribute the Program at all.  For example, if a patent
license would not permit royalty-free redistribution of the Program by
all those who receive copies directly or indirectly through you, then
the only way you could satisfy both it and this License would be to
refrain entirely from distribution of the Program.

If any portion of this section is held invalid or unenforceable under
any particular circumstance, the balance of the section is intended to
apply and the section as a whole is intended to apply in other
circumstances.

It is not the purpose of this section to induce you to infringe any
patents or other property right claims or to contest validity of any
such claims; this section has the sole purpose of protecting the
integrity of the free software distribution system, which is
implemented by public license practices.  Many people have made
generous contributions to the wide range of software distributed
through that system in reliance on consistent application of that
system; it is up to the author/donor to decide if he or she is willing
to distribute software through any other system and a licensee cannot
impose that choice.

This section is intended to make thoroughly clear what is believed to
be a consequence of the rest of this License.

  8. If the distribution and/or use of the Program is restricted in
certain countries either by patents or by copyrighted interfaces, the
original copyright holder who places the Program under this License
may add an explicit geographical distribution limitation excluding
those countries, so that distribution is permitted only in or among
countries not thus excluded.  In such case, this License incorporates
the limitation as if written in the body of this License.

  9. The Free Software Foundation may publish revised and/or new versions
of the General Public License from time to time.  Such new versions will
be similar in spirit to the present version, but may differ in detail to
address new problems or concerns.

Each version is given a distinguishing version number.  If the Program
specifies a version number of this License which applies to it and "any
later version", you have the option of following the terms and conditions
either of that version or of any later version published by the Free
Software Foundation.  If the Program does not specify a version number of
this License, you may choose any version ever published by the Free Software
Foundation.

  10. If you wish to incorporate parts of the Program into other free
programs whose distribution conditions are different, write to the author
to ask for permission.  For software which is copyrighted by the Free
Software Foundation, write to the Free Software Foundation; we sometimes
make exceptions for this.  Our decision will be guided by the two goals
of preserving the free status of all derivatives of our free software and
of promoting the sharing and reuse of software generally.

			    NO WARRANTY

  11. BECAUSE THE PROGRAM IS LICENSED FREE OF CHARGE, THERE IS NO WARRANTY
FOR THE PROGRAM, TO THE EXTENT PERMITTED BY APPLICABLE LAW.  EXCEPT WHEN
OTHERWISE STATED IN WRITING THE COPYRIGHT HOLDERS AND/OR OTHER PARTIES
PROVIDE THE PROGRAM "AS IS" WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESSED
OR IMPLIED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.  THE ENTIRE RISK AS
TO THE QUALITY AND PERFORMANCE OF THE PROGRAM IS WITH YOU.  SHOULD THE
PROGRAM PROVE DEFECTIVE, YOU ASSUME THE COST OF ALL NECESSARY SERVICING,
REPAIR OR CORRECTION.

  12. IN NO EVENT UNLESS REQUIRED BY APPLICABLE LAW OR AGREED TO IN WRITING
WILL ANY COPYRIGHT HOLDER, OR ANY OTHER PARTY WHO MAY MODIFY AND/OR
REDISTRIBUTE THE PROGRAM AS PERMITTED ABOVE, BE LIABLE TO YOU FOR DAMAGES,
INCLUDING ANY GENERAL, SPECIAL, INCIDENTAL OR CONSEQUENTIAL DAMAGES ARISING
OUT OF THE USE OR INABILITY TO USE THE PROGRAM (INCLUDING BUT NOT LIMITED
TO LOSS OF DATA OR DATA BEING RENDERED INACCURATE OR LOSSES SUSTAINED BY
YOU OR THIRD PARTIES OR A FAILURE OF THE PROGRAM TO OPERATE WITH ANY OTHER
PROGRAMS), EVEN IF SUCH HOLDER OR OTHER PARTY HAS BEEN ADVISED OF THE
POSSIBILITY OF SUCH DAMAGES.

		     END OF TERMS AND CONDITIONS

	    How to Apply These Terms to Your New Programs

  If you develop a new program, and you want it to be of the greatest
possible use to the public, the best way to achieve this is to make it
free software which everyone can redistribute and change under these terms.

  To do so, attach the following notices to the program.  It is safest
to attach them to the start of each source file to most effectively
convey the exclusion of warranty; and each file should have at least
the "copyright" line and a pointer to where the full notice is found.

    <one line to give the program's name and a brief idea of what it does.>
    Copyright (C) <year>  <name of author>

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, write to the Free Software
    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA


Also add information on how to contact you by electronic and paper mail.

If the program is interactive, make it output a short notice like this
when it starts in an interactive mode:

    Gnomovision version 69, Copyright (C) year  name of author
    Gnomovision comes with ABSOLUTELY NO WARRANTY; for details type `show w'.
    This is free software, and you are welcome to redistribute it
    under certain conditions; type `show c' for details.

The hypothetical commands `show w' and `show c' should show the appropriate
parts of the General Public License.  Of course, the commands you use may
be called something other than `show w' and `show c'; they could even be
mouse-clicks or menu items--whatever suits your program.

You should also get your employer (if you work as a programmer) or your
school, if any, to sign a "copyright disclaimer" for the program, if
necessary.  Here is a sample; alter the names:

  Yoyodyne, Inc., hereby disclaims all copyright interest in the program
  `Gnomovision' (which makes passes at compilers) written by James Hacker.

  <signature of Ty Coon>, 1 April 1989
  Ty Coon, President of Vice

This General Public License does not permit incorporating your program into
proprietary programs.  If your program is a subroutine library, you may
consider it more useful to permit linking proprietary applications with the
library.  If this is what you want to do, use the GNU Library General
Public License instead of this License.

This program is also available under a commercial proprietary license.
For more information, contact us at license @ x265.com.
````

<a id="text-38"></a>

### x265-header.txt

Source: `https://raw.githubusercontent.com/Multicorewareinc/x265/4.3/source/x265.h`. SHA-256: `e8557aeb23ac7c220cc9298b485864e87df4ae9d7418ef0359cd0e5ccec34d01`. UTF-8/LF bytes: 1143.

Copied from this URL on 2026-11-03. Selection: initial copyright/licence comment through */ plus LF. The common licence texts are supplied separately below.

````text
/*****************************************************************************
 * Copyright (C) 2013-2020 MulticoreWare, Inc
 *
 * Authors: Steve Borho <steve@borho.org>
 *          Min Chen <chenm003@163.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02111, USA.
 *
 * This program is also available under a commercial proprietary license.
 * For more information, contact us at license @ x265.com.
 *****************************************************************************/
````

<a id="text-39"></a>

### libheif-COPYING.txt

Source: `https://raw.githubusercontent.com/strukturag/libheif/v1.23.6/COPYING`. SHA-256: `b9e2b836cce4c53bd189668e18467d0d88fbfa0fc4a9ff092fb275ce08e60b4a`. UTF-8/LF bytes: 285.

Copied from this URL on 2026-11-03. Selection: project notice preceding common LGPLv3/GPLv3 texts. The common licence texts are supplied separately below.

````text
* The library `libheif` is distributed under the terms of the GNU Lesser General Public License.
* The sample applications and the Go and C++ wrappers are distributed under the terms of the MIT License.

License texts below and in the `COPYING` files of the corresponding subfolders.

````

<a id="text-40"></a>

### libde265-COPYING.txt

Source: `https://raw.githubusercontent.com/strukturag/libde265/v1.1.3/COPYING`. SHA-256: `df06f23f556f4cac64ab2af63995d81cdc4412a2cb44696947bb62f11c6a70d0`. UTF-8/LF bytes: 258.

Copied from this URL on 2026-11-03. Selection: project notice preceding common LGPLv3/GPLv3 texts. The common licence texts are supplied separately below.

````text
* The library `libde265` is distributed under the terms of the GNU Lesser General Public License.
* The sample applications are distributed under the terms of the MIT license.

License texts below and in the `COPYING` files of the corresponding subfolders.

````

<a id="text-41"></a>

### mingw-COPYING.txt

Source: `https://raw.githubusercontent.com/mingw-w64/mingw-w64/master/COPYING`. SHA-256: `99a69660981156c21336fdb5661f89341b013c94e4bf9e1c7467b4745718397f`. UTF-8/LF bytes: 2326.

Copied from this URL on 2026-11-03. The pillow-heif wheel manifest names no MinGW-w64 or winpthreads version, so no version-matched tagged copy can be identified; this unversioned source is disclosed rather than assigning an unverified tag.

````text
With exception of certain parts that are prominently marked as being
in the Public Domain, BSD, or LGPL this Software is provided under the
Zope Public License (ZPL) Version 2.1.

Copyright (c) 2009 - 2013 by the mingw-w64 project

See the AUTHORS file for the list of contributors to the mingw-w64 project.

This license has been certified as open source. It has also been designated
as GPL compatible by the Free Software Foundation (FSF).

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

   1. Redistributions in source code must retain the accompanying copyright
      notice, this list of conditions, and the following disclaimer.
   2. Redistributions in binary form must reproduce the accompanying
      copyright notice, this list of conditions, and the following disclaimer
      in the documentation and/or other materials provided with the
      distribution.
   3. Names of the copyright holders must not be used to endorse or promote
      products derived from this software without prior written permission
      from the copyright holders.
   4. The right to distribute this software or to use it for any purpose does
      not give you the right to use Servicemarks (sm) or Trademarks (tm) of
      the copyright holders.  Use of them is covered by separate agreement
      with the copyright holders.
   5. If any files are modified, you must cause the modified files to carry
      prominent notices stating that you changed the files and the date of
      any change.

Disclaimer

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS ``AS IS'' AND ANY EXPRESSED
OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO
EVENT SHALL THE COPYRIGHT HOLDERS BE LIABLE FOR ANY DIRECT, INDIRECT,
INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, 
OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
````

<a id="text-42"></a>

### libheif-header.txt

Source: `https://raw.githubusercontent.com/strukturag/libheif/v1.23.6/libheif/api/libheif/heif.h`. SHA-256: `c0acdafc58cf45f394ab796d279001f16b7748a3b74d63dab34574d95ac8a42f`. UTF-8/LF bytes: 774.

Copied from this URL on 2026-11-03. Selection: initial copyright/licence comment through */ plus LF. The common licence texts are supplied separately below.

````text
/*
 * HEIF codec.
 * Copyright (c) 2017-2025 Dirk Farin <dirk.farin@gmail.com>
 *
 * This file is part of libheif.
 *
 * libheif is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Lesser General Public License as
 * published by the Free Software Foundation, either version 3 of
 * the License, or (at your option) any later version.
 *
 * libheif is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public License
 * along with libheif.  If not, see <http://www.gnu.org/licenses/>.
 */
````

<a id="text-43"></a>

### libde265-header.txt

Source: `https://raw.githubusercontent.com/strukturag/libde265/v1.1.3/libde265/de265.h`. SHA-256: `01810f59b757ca00a898b869481ea776f8478d75a900868970f7d151fcf0c9ab`. UTF-8/LF bytes: 794.

Copied from this URL on 2026-11-03. Selection: initial copyright/licence comment through */ plus LF. The common licence texts are supplied separately below.

````text
/*
 * H.265 video codec.
 * Copyright (c) 2013-2014 struktur AG, Dirk Farin <farin@struktur.de>
 *
 * This file is part of libde265.
 *
 * libde265 is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Lesser General Public License as
 * published by the Free Software Foundation, either version 3 of
 * the License, or (at your option) any later version.
 *
 * libde265 is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public License
 * along with libde265.  If not, see <http://www.gnu.org/licenses/>.
*/
````

<a id="text-44"></a>

### winpthreads-COPYING.txt

Source: `https://raw.githubusercontent.com/mingw-w64/mingw-w64/master/mingw-w64-libraries/winpthreads/COPYING`. SHA-256: `63263614cdd29f2f93cba85e992f041b31f9fc7b4033692f31269489a8a1b177`. UTF-8/LF bytes: 2883.

Copied from this URL on 2026-11-03. The pillow-heif wheel manifest names no MinGW-w64 or winpthreads version, so no version-matched tagged copy can be identified; this unversioned source is disclosed rather than assigning an unverified tag.

````text
Copyright (c) 2011 mingw-w64 project

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.


/*
 * Parts of this library are derived by:
 *
 * Posix Threads library for Microsoft Windows
 *
 * Use at own risk, there is no implied warranty to this code.
 * It uses undocumented features of Microsoft Windows that can change
 * at any time in the future.
 *
 * (C) 2010 Lockless Inc.
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without modification,
 * are permitted provided that the following conditions are met:
 *
 *
 *  * Redistributions of source code must retain the above copyright notice,
 *    this list of conditions and the following disclaimer.
 *  * Redistributions in binary form must reproduce the above copyright notice,
 *    this list of conditions and the following disclaimer in the documentation
 *    and/or other materials provided with the distribution.
 *  * Neither the name of Lockless Inc. nor the names of its contributors may be
 *    used to endorse or promote products derived from this software without
 *    specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AN
 * ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
 * WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
 * IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
 * INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
 * BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
 * DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
 * LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
 * OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
 * OF THE POSSIBILITY OF SUCH DAMAGE.
 */
````

<!-- WP6.3c generated FFmpeg toolchain runtime census -->

## FFmpeg build components and toolchain runtime census

This section applies to the bundled 1.1.0 Windows FFmpeg, not user-obtained tools.
Rows and links to licence texts are generated by `python tools/package/notices.py --root-annex --write`
using the artifact notices renderer and `tools/package/ffmpeg.lock.json` and include every stage source record carrying texts.
Over-inclusion is permitted: reached_via: toolchain rows retained with both Rust stages disabled produce extra notices.
Shared texts use a representative file name from the census; byte-identical texts are shared across components.

| Component | Version | Licence | Verdict | Corresponding source / terms | Texts |
| --- | --- | --- | --- | --- | --- |
| FFmpeg component: amf | 57ee0cfb0e1a08d9041f77435653794c1b012be0 | MIT | Redistributed in this artifact | https://github.com/GPUOpen-LibrariesAndSDKs/AMF.git @ 57ee0cfb0e1a08d9041f77435653794c1b012be0 | [licence-1](tools/package/native-licences/ffmpeg-components/amf--LICENSE.txt), [licence-2](tools/package/native-licences/ffmpeg-components/amf--Thirdparty--amd--AmdDxExt--LICENSE.txt) |
| FFmpeg component: aom | 9ace39e02a34992b83fc7f7f2bfbbd2e79348c74 | BSD-2-Clause | Redistributed in this artifact | https://aomedia.googlesource.com/aom @ 9ace39e02a34992b83fc7f7f2bfbbd2e79348c74 | [licence-3](tools/package/native-licences/ffmpeg-components/aom--LICENSE), [licence-4](tools/package/native-licences/ffmpeg-components/aom--PATENTS), [licence-5](tools/package/native-licences/ffmpeg-components/aom--third_party--fastfeat--LICENSE), [licence-6](tools/package/native-licences/ffmpeg-components/aom--third_party--googletest--src--LICENSE), [licence-7](tools/package/native-licences/ffmpeg-components/aom--third_party--highway--LICENSE-BSD3), [licence-11](tools/package/native-licences/ffmpeg-components/libwebp--COPYING), [licence-10](tools/package/native-licences/ffmpeg-components/libvpx--PATENTS), [licence-8](tools/package/native-licences/ffmpeg-components/aom--third_party--libyuv--LICENSE), [licence-9](tools/package/native-licences/ffmpeg-components/aom--third_party--x86inc--LICENSE) |
| FFmpeg component: avisynth | 523370a39933e2f9c208a5d74c1d35d43d177a76 | GPL-2.0-or-later | Redistributed in this artifact | https://github.com/AviSynth/AviSynthPlus.git @ 523370a39933e2f9c208a5d74c1d35d43d177a76 | [licence-12](tools/package/native-licences/ffmpeg-components/avisynth--avs_core--include--avisynth_c.h), [licence-14](tools/package/native-licences/ffmpeg-components/avisynth--distrib--docs--english--source--avisynthdoc--license.rst), [licence-13](tools/package/native-licences/ffmpeg-components/avisynth--avs_core--include--avisynth_c.h-L1-35.txt), [licence-15](tools/package/native-licences/ffmpeg-components/spdx--text--GPL-2.0-or-later.txt) |
| FFmpeg component: brotli | 2e2bcf17ae7115d84ef6588d9a3651cc987d73e7 | MIT | Redistributed in this artifact | https://github.com/google/brotli.git @ 2e2bcf17ae7115d84ef6588d9a3651cc987d73e7 | [licence-16](tools/package/native-licences/ffmpeg-components/brotli--LICENSE) |
| FFmpeg component: cairo | 74755964edef651691d5cd36ff140108298e4e6e | LGPL-2.1-only OR MPL-1.1 | Redistributed in this artifact | https://gitlab.freedesktop.org/cairo/cairo.git @ 74755964edef651691d5cd36ff140108298e4e6e | [licence-17](tools/package/native-licences/ffmpeg-components/cairo--COPYING), [licence-18](tools/package/native-licences/ffmpeg-components/cairo--COPYING-LGPL-2.1), [licence-19](tools/package/native-licences/ffmpeg-components/cairo--COPYING-MPL-1.1), [licence-20](tools/package/native-licences/ffmpeg-components/cairo--perf--COPYING), [licence-23](tools/package/native-licences/ffmpeg-components/cairo--util--COPYING), [licence-21](tools/package/native-licences/ffmpeg-components/cairo--util--cairo-script--COPYING), [licence-22](tools/package/native-licences/ffmpeg-components/cairo--util--cairo-trace--COPYING), [licence-24](tools/package/native-licences/ffmpeg-toolchain/gcc--COPYING3) |
| FFmpeg component: chromaprint | 3b38c100022bdfb49be7797c4828a476f1621d55 | MIT AND LGPL-2.1-or-later AND BSD-3-Clause | Redistributed in this artifact | https://github.com/acoustid/chromaprint.git @ 3b38c100022bdfb49be7797c4828a476f1621d55 | [licence-25](tools/package/native-licences/ffmpeg-components/chromaprint--LICENSE.md), [licence-6](tools/package/native-licences/ffmpeg-components/aom--third_party--googletest--src--LICENSE), [licence-26](tools/package/native-licences/ffmpeg-components/chromaprint--src--3rdparty--kissfft--COPYING), [licence-27](tools/package/native-licences/ffmpeg-components/chromaprint--src--3rdparty--kissfft--LICENSES--BSD-3-Clause), [licence-28](tools/package/native-licences/ffmpeg-components/chromaprint--src--3rdparty--kissfft--LICENSES--Unlicense), [licence-29](tools/package/native-licences/ffmpeg-components/spdx--text--LGPL-2.1-or-later.txt) |
| FFmpeg component: dav1d | b8b2d726b4b78a2fb174cb45baff441b5969672c | BSD-2-Clause | Redistributed in this artifact | https://code.videolan.org/videolan/dav1d.git @ b8b2d726b4b78a2fb174cb45baff441b5969672c | [licence-30](tools/package/native-licences/ffmpeg-components/dav1d--COPYING), [licence-31](tools/package/native-licences/ffmpeg-components/dav1d--doc--PATENTS) |
| FFmpeg component: davs2 | b41cf117452e2d73d827f02d3e30aa20f1c721ac | GPL-2.0-or-later | Redistributed in this artifact | https://github.com/pkuvcl/davs2.git @ b41cf117452e2d73d827f02d3e30aa20f1c721ac | [licence-32](tools/package/native-licences/ffmpeg-components/davs2--COPYING) |
| FFmpeg component: ffnvcodec | f2053071ea93137255b6dcf42e9b4c9e0965a44e | MIT | Redistributed in this artifact | https://github.com/FFmpeg/nv-codec-headers.git @ f2053071ea93137255b6dcf42e9b4c9e0965a44e | [licence-33](tools/package/native-licences/ffmpeg-components/ffnvcodec--include--ffnvcodec--dynlink_loader.h), [licence-35](tools/package/native-licences/ffmpeg-components/ffnvcodec--include--ffnvcodec--nvEncodeAPI.h), [licence-36](tools/package/native-licences/ffmpeg-components/ffnvcodec--include--ffnvcodec--nvEncodeAPI.h-L1-26.txt), [licence-34](tools/package/native-licences/ffmpeg-components/ffnvcodec--include--ffnvcodec--dynlink_loader.h-L1-26.txt), [licence-37](tools/package/native-licences/ffmpeg-toolchain/spdx--text--MIT.txt) |
| FFmpeg component: ffnvcodec / repository 2 | ced4f8eba3ba5dd431932cba17928f0dffdaeb2b | MIT | Source fetched by the build; not compiled into this artifact (notice carried by over-inclusion) | https://github.com/FFmpeg/nv-codec-headers.git @ ced4f8eba3ba5dd431932cba17928f0dffdaeb2b | [licence-38](tools/package/native-licences/ffmpeg-components/ffnvcodec-sdk13.0--include--ffnvcodec--dynlink_loader.h), [licence-39](tools/package/native-licences/ffmpeg-components/ffnvcodec-sdk13.0--include--ffnvcodec--nvEncodeAPI.h), [licence-40](tools/package/native-licences/ffmpeg-components/ffnvcodec-sdk13.0--include--ffnvcodec--nvEncodeAPI.h-L1-26.txt), [licence-34](tools/package/native-licences/ffmpeg-components/ffnvcodec--include--ffnvcodec--dynlink_loader.h-L1-26.txt), [licence-37](tools/package/native-licences/ffmpeg-toolchain/spdx--text--MIT.txt) |
| FFmpeg component: ffnvcodec / repository 3 | 833faee5f7b8d3f56444347c587f4aed11ee213f | MIT | Source fetched by the build; not compiled into this artifact (notice carried by over-inclusion) | https://github.com/FFmpeg/nv-codec-headers.git @ 833faee5f7b8d3f56444347c587f4aed11ee213f | [licence-38](tools/package/native-licences/ffmpeg-components/ffnvcodec-sdk13.0--include--ffnvcodec--dynlink_loader.h), [licence-41](tools/package/native-licences/ffmpeg-components/ffnvcodec-sdk11.1--include--ffnvcodec--nvEncodeAPI.h), [licence-42](tools/package/native-licences/ffmpeg-components/ffnvcodec-sdk11.1--include--ffnvcodec--nvEncodeAPI.h-L1-26.txt), [licence-34](tools/package/native-licences/ffmpeg-components/ffnvcodec--include--ffnvcodec--dynlink_loader.h-L1-26.txt), [licence-37](tools/package/native-licences/ffmpeg-toolchain/spdx--text--MIT.txt) |
| FFmpeg component: fftw3 | a7b679c528330cf6258253d6dcf5ec90552e6c93 | GPL-2.0-or-later | Redistributed in this artifact | https://github.com/FFTW/fftw3.git @ a7b679c528330cf6258253d6dcf5ec90552e6c93 | [licence-43](tools/package/native-licences/ffmpeg-components/fftw3--COPYING), [licence-44](tools/package/native-licences/ffmpeg-components/fftw3--COPYRIGHT), [licence-45](tools/package/native-licences/ffmpeg-components/fftw3--doc--license.texi) |
| FFmpeg component: fontconfig | b25ffeabd15b76f86c0c6736f6df2f1b89858010 | MIT | Redistributed in this artifact | https://gitlab.freedesktop.org/fontconfig/fontconfig.git @ b25ffeabd15b76f86c0c6736f6df2f1b89858010 | [licence-46](tools/package/native-licences/ffmpeg-components/fontconfig--COPYING) |
| FFmpeg component: freetype | 4ba7c3d82ab8b3cc80b869337d2c2b1913c5e415 | FTL OR GPL-2.0-or-later | Redistributed in this artifact | https://gitlab.freedesktop.org/freetype/freetype.git @ 4ba7c3d82ab8b3cc80b869337d2c2b1913c5e415 | [licence-49](tools/package/native-licences/ffmpeg-components/freetype--LICENSE.TXT), [licence-47](tools/package/native-licences/ffmpeg-components/freetype--docs--FTL.TXT), [licence-48](tools/package/native-licences/ffmpeg-components/freetype--docs--GPLv2.TXT), [licence-50](tools/package/native-licences/ffmpeg-components/freetype--src--bdf--README), [licence-51](tools/package/native-licences/ffmpeg-components/freetype--src--pcf--README) |
| FFmpeg component: freetype-bootstrap | 4ba7c3d82ab8b3cc80b869337d2c2b1913c5e415 | FTL OR GPL-2.0-or-later | Redistributed in this artifact | https://gitlab.freedesktop.org/freetype/freetype.git @ 4ba7c3d82ab8b3cc80b869337d2c2b1913c5e415 | [licence-49](tools/package/native-licences/ffmpeg-components/freetype--LICENSE.TXT), [licence-47](tools/package/native-licences/ffmpeg-components/freetype--docs--FTL.TXT), [licence-48](tools/package/native-licences/ffmpeg-components/freetype--docs--GPLv2.TXT), [licence-50](tools/package/native-licences/ffmpeg-components/freetype--src--bdf--README), [licence-51](tools/package/native-licences/ffmpeg-components/freetype--src--pcf--README) |
| FFmpeg component: frei0r | 618dde79716fab4e428a05e6476325b9e6f5b063 | GPL-2.0-or-later | Redistributed in this artifact | https://github.com/dyne/frei0r.git @ 618dde79716fab4e428a05e6476325b9e6f5b063 | [licence-43](tools/package/native-licences/ffmpeg-components/fftw3--COPYING) |
| FFmpeg component: fribidi | d2f3e1f4946e7cef9789e1c3ebdb4a60d4314c7f | LGPL-2.1-or-later | Redistributed in this artifact | https://github.com/fribidi/fribidi.git @ d2f3e1f4946e7cef9789e1c3ebdb4a60d4314c7f | [licence-52](tools/package/native-licences/ffmpeg-components/libiconv--COPYING.LIB) |
| FFmpeg component: glib | 50b938a3e8f5154a25b5af3dd8b9dd8b2ccba7c3 | LGPL-2.1-or-later | Redistributed in this artifact | https://github.com/GNOME/glib.git @ 50b938a3e8f5154a25b5af3dd8b9dd8b2ccba7c3 | [licence-54](tools/package/native-licences/ffmpeg-components/glib--LICENSES--AFL-2.0.txt), [licence-55](tools/package/native-licences/ffmpeg-toolchain/spdx--text--Apache-2.0.txt), [licence-56](tools/package/native-licences/ffmpeg-components/glib--LICENSES--CC-BY-SA-3.0.txt), [licence-57](tools/package/native-licences/ffmpeg-components/glib--LICENSES--CC0-1.0.txt), [licence-15](tools/package/native-licences/ffmpeg-components/spdx--text--GPL-2.0-or-later.txt), [licence-58](tools/package/native-licences/ffmpeg-components/glib--LICENSES--LGPL-2.1-only.txt), [licence-60](tools/package/native-licences/ffmpeg-components/glib--LICENSES--LLVM-exception.txt), [licence-59](tools/package/native-licences/ffmpeg-components/glib--LICENSES--LicenseRef-old-glib-tests.txt), [licence-61](tools/package/native-licences/ffmpeg-components/glib--LICENSES--MIT.txt), [licence-62](tools/package/native-licences/ffmpeg-components/glib--LICENSES--MPL-1.1.txt), [licence-53](tools/package/native-licences/ffmpeg-components/glib--docs--reference--COPYING) |
| FFmpeg component: glslang | 73b25650df6dc4545966674531e6b7cc8f5d2407 | Apache-2.0 AND BSD-2-Clause AND BSD-3-Clause AND MIT AND MIT-Khronos-old AND AML-glslang AND GPL-3.0-or-later WITH Bison-exception-2.2 | Redistributed in this artifact | https://github.com/KhronosGroup/glslang.git @ 73b25650df6dc4545966674531e6b7cc8f5d2407 | [licence-63](tools/package/native-licences/ffmpeg-components/glslang--LICENSE.txt), [licence-64](tools/package/native-licences/ffmpeg-components/glslang--LICENSES--AML-glslang.txt), [licence-65](tools/package/native-licences/ffmpeg-components/glslang--LICENSES--Apache-2.0.txt), [licence-67](tools/package/native-licences/ffmpeg-components/glslang--LICENSES--BSD-2-Clause.txt), [licence-68](tools/package/native-licences/ffmpeg-components/glslang--LICENSES--BSD-3-Clause.txt), [licence-66](tools/package/native-licences/ffmpeg-components/glslang--LICENSES--Bison-exception-2.2.txt), [licence-69](tools/package/native-licences/ffmpeg-components/gnulib--doc--COPYINGv3), [licence-70](tools/package/native-licences/ffmpeg-components/spirv-cross--LICENSES--LicenseRef-KhronosFreeUse.txt), [licence-37](tools/package/native-licences/ffmpeg-toolchain/spdx--text--MIT.txt) |
| FFmpeg component: gme | f68963b1de0633149b05732113d3c3113c6f63a1 | LGPL-2.1-or-later | Redistributed in this artifact | https://github.com/libgme/game-music-emu.git @ f68963b1de0633149b05732113d3c3113c6f63a1 | [licence-71](tools/package/native-licences/ffmpeg-components/gme--gme--ext--LICENSE), [licence-73](tools/package/native-licences/ffmpeg-components/gmp--COPYINGv2), [licence-72](tools/package/native-licences/ffmpeg-components/gme--license.txt) |
| FFmpeg component: gmp | 5c3e9a9d52b697cab7b7d26a53972a3bf922d59a | LGPL-3.0-or-later OR GPL-2.0-or-later | Redistributed in this artifact | https://github.com/BtbN/gmplib.git @ 5c3e9a9d52b697cab7b7d26a53972a3bf922d59a | [licence-74](tools/package/native-licences/ffmpeg-components/gmp--COPYING.LESSERv3), [licence-73](tools/package/native-licences/ffmpeg-components/gmp--COPYINGv2), [licence-75](tools/package/native-licences/ffmpeg-components/gmp--COPYINGv3) |
| FFmpeg component: harfbuzz | 75d8ac5d2313842550174eaab0cbaf653c8f2f77 | MIT-Modern-Variant | Redistributed in this artifact | https://github.com/harfbuzz/harfbuzz.git @ 75d8ac5d2313842550174eaab0cbaf653c8f2f77 | [licence-76](tools/package/native-licences/ffmpeg-components/harfbuzz--COPYING), [licence-77](tools/package/native-licences/ffmpeg-components/harfbuzz--perf--texts--COPYING), [licence-78](tools/package/native-licences/ffmpeg-toolchain/crates--windows-sys-0.59.0--license-mit) |
| FFmpeg component: kvazaar | 1f11f9ae33ef0cbe48a7d335b7144af1ecfe8092 | BSD-3-Clause | Redistributed in this artifact | https://github.com/ultravideo/kvazaar.git @ 1f11f9ae33ef0cbe48a7d335b7144af1ecfe8092 | [licence-79](tools/package/native-licences/ffmpeg-components/kvazaar--LICENSE), [licence-80](tools/package/native-licences/ffmpeg-components/kvazaar--LICENSE.EXT.greatest), [licence-81](tools/package/native-licences/ffmpeg-components/kvazaar--src--threadwrapper--LICENSE) |
| FFmpeg component: lcevcdec | 741fb7c869cf61012f7dcebfcd9e56981198c78b | BSD-3-Clause-Clear | Redistributed in this artifact | https://github.com/v-novaltd/LCEVCdec.git @ 741fb7c869cf61012f7dcebfcd9e56981198c78b | [licence-82](tools/package/native-licences/ffmpeg-components/lcevcdec--COPYING), [licence-83](tools/package/native-licences/ffmpeg-components/lcevcdec--LICENSE.md), [licence-86](tools/package/native-licences/ffmpeg-components/lcevcdec--licenses--FFmpeg--LICENSE.md), [licence-84](tools/package/native-licences/ffmpeg-components/lcevcdec--licenses--conan-center-index--LICENSE.txt), [licence-85](tools/package/native-licences/ffmpeg-components/lcevcdec--licenses--emscripten--licence.txt), [licence-87](tools/package/native-licences/ffmpeg-components/lcevcdec--licenses--fmt--LICENSE), [licence-88](tools/package/native-licences/ffmpeg-components/lcevcdec--licenses--gradle--LICENSE), [licence-89](tools/package/native-licences/ffmpeg-components/lcevcdec--licenses--ios-cmake--license.md), [licence-90](tools/package/native-licences/ffmpeg-components/lcevcdec--licenses--nlohmann_json--LICENSE.MIT), [licence-91](tools/package/native-licences/ffmpeg-components/lcevcdec--licenses--vma--LICENSE.txt) |
| FFmpeg component: lcms2 | 1112313b3784ced9297d8c0ee076aba17499827a | MIT | Redistributed in this artifact | https://github.com/mm2/Little-CMS.git @ 1112313b3784ced9297d8c0ee076aba17499827a | [licence-92](tools/package/native-licences/ffmpeg-components/lcms2--LICENSE), [licence-93](tools/package/native-licences/ffmpeg-components/lcms2--plugins--fast_float--COPYING.GPL3), [licence-94](tools/package/native-licences/ffmpeg-components/lcms2--utils--jpgicc--LICENSE_iccjpeg) |
| FFmpeg component: libaribb24 | 5e9be272f96e00f15a2f3c5f8ba7e124862aec38 | LGPL-3.0-or-later | Redistributed in this artifact | https://github.com/nkoriyama/aribb24.git @ 5e9be272f96e00f15a2f3c5f8ba7e124862aec38 | [licence-95](tools/package/native-licences/ffmpeg-components/libaribb24--COPYING) |
| FFmpeg component: libaribcaption | 37dde0f32652c32aa98bf92278944d1cfb2e7354 | MIT | Redistributed in this artifact | https://github.com/xqq/libaribcaption.git @ 37dde0f32652c32aa98bf92278944d1cfb2e7354 | [licence-96](tools/package/native-licences/ffmpeg-components/libaribcaption--LICENSE) |
| FFmpeg component: libass | f61db567e6593df3470e91594bcd4ad2d0473aff | ISC | Redistributed in this artifact | https://github.com/libass/libass.git @ f61db567e6593df3470e91594bcd4ad2d0473aff | [licence-97](tools/package/native-licences/ffmpeg-components/libass--COPYING) |
| FFmpeg component: libbluray | f33a738fd7bb8b5e1148b0a5424778db7342450b | LGPL-2.1-or-later | Redistributed in this artifact | https://code.videolan.org/videolan/libbluray.git @ f33a738fd7bb8b5e1148b0a5424778db7342450b | [licence-99](tools/package/native-licences/ffmpeg-components/libbluray--COPYING), [licence-98](tools/package/native-licences/ffmpeg-components/libbluray--contrib--asm--LICENSE.txt) |
| FFmpeg component: libdvdcss | 811ce97a1d4d1c9d936f4b2707f533a9ef768251 | GPL-2.0-or-later | Redistributed in this artifact | https://code.videolan.org/videolan/libdvdcss.git @ 811ce97a1d4d1c9d936f4b2707f533a9ef768251 | [licence-73](tools/package/native-licences/ffmpeg-components/gmp--COPYINGv2) |
| FFmpeg component: libdvdnav | 8147ccd35e5aae4afdd21171cf7b6b4d8f179d28 | GPL-2.0-or-later | Redistributed in this artifact | https://code.videolan.org/videolan/libdvdnav.git @ 8147ccd35e5aae4afdd21171cf7b6b4d8f179d28 | [licence-100](tools/package/native-licences/ffmpeg-components/libdvdnav--COPYING) |
| FFmpeg component: libdvdread | 0f30df53125b564ef45903714403ce0a1e6c5e9e | GPL-2.0-or-later | Redistributed in this artifact | https://code.videolan.org/videolan/libdvdread.git @ 0f30df53125b564ef45903714403ce0a1e6c5e9e | [licence-101](tools/package/native-licences/ffmpeg-components/libdvdread--COPYING) |
| FFmpeg component: libffi | bc553867367246d140cd156f060bd0409f57f157 | MIT | Redistributed in this artifact | https://github.com/libffi/libffi.git @ bc553867367246d140cd156f060bd0409f57f157 | [licence-102](tools/package/native-licences/ffmpeg-components/libffi--LICENSE), [licence-103](tools/package/native-licences/ffmpeg-components/libffi--LICENSE-BUILDTOOLS) |
| FFmpeg component: libiconv | b5a1735e02bf43ee6e490fcf9395e8abc8d32432 | LGPL-2.1-or-later | Redistributed in this artifact | https://git.savannah.gnu.org/git/libiconv.git @ b5a1735e02bf43ee6e490fcf9395e8abc8d32432 | [licence-24](tools/package/native-licences/ffmpeg-toolchain/gcc--COPYING3), [licence-52](tools/package/native-licences/ffmpeg-components/libiconv--COPYING.LIB) |
| FFmpeg component: libiconv / repository 2 | 5df606bbd0ef54a8f150c3303c870b9381a661f0 | GPL-3.0-or-later AND LGPL-2.1-or-later AND LicenseRef-gnulib-permissive | Redistributed in this artifact | https://git.savannah.gnu.org/git/gnulib.git @ 5df606bbd0ef54a8f150c3303c870b9381a661f0 | [licence-104](tools/package/native-licences/ffmpeg-components/gnulib--COPYING), [licence-52](tools/package/native-licences/ffmpeg-components/libiconv--COPYING.LIB), [licence-105](tools/package/native-licences/ffmpeg-components/gnulib--doc--COPYING.LESSERv3), [licence-106](tools/package/native-licences/ffmpeg-components/gnulib--doc--COPYINGv2), [licence-69](tools/package/native-licences/ffmpeg-components/gnulib--doc--COPYINGv3), [licence-107](tools/package/native-licences/ffmpeg-components/gnulib--doc--licenses-texi.texi), [licence-108](tools/package/native-licences/ffmpeg-components/gnulib--modules--COPYING) |
| FFmpeg component: libjxl | e47d2a2b5bb418f2947ce07f36cb048861db3820 | BSD-3-Clause | Redistributed in this artifact | https://github.com/libjxl/libjxl.git @ e47d2a2b5bb418f2947ce07f36cb048861db3820 | [licence-111](tools/package/native-licences/ffmpeg-components/libjxl--LICENSE), [licence-112](tools/package/native-licences/ffmpeg-components/libjxl--PATENTS), [licence-109](tools/package/native-licences/ffmpeg-components/libjxl--debian--copyright), [licence-110](tools/package/native-licences/ffmpeg-components/libjxl--lib--extras--LICENSE.apngdis), [licence-113](tools/package/native-licences/ffmpeg-components/libjxl--third_party--HEVCSoftware--cfg--LICENSE) |
| FFmpeg component: libmp3lame | 7113 | LGPL-2.0-or-later | Redistributed in this artifact | https://svn.code.sf.net/p/lame/svn/trunk/lame @ 7113 | [licence-114](tools/package/native-licences/ffmpeg-components/libmp3lame--COPYING), [licence-115](tools/package/native-licences/ffmpeg-components/libmp3lame--LICENSE) |
| FFmpeg component: libogg | 06a5e0262cdc28aa4ae6797627a783b5010440f0 | BSD-3-Clause | Redistributed in this artifact | https://github.com/xiph/ogg.git @ 06a5e0262cdc28aa4ae6797627a783b5010440f0 | [licence-116](tools/package/native-licences/ffmpeg-components/libogg--COPYING) |
| FFmpeg component: libopus | a8b2545eec71e0f53ecead2d583e7b6baa42684d | BSD-3-Clause | Redistributed in this artifact | https://github.com/xiph/opus.git @ a8b2545eec71e0f53ecead2d583e7b6baa42684d | [licence-117](tools/package/native-licences/ffmpeg-components/libopus--COPYING), [licence-118](tools/package/native-licences/ffmpeg-components/libopus--LICENSE_PLEASE_READ.txt) |
| FFmpeg component: libplacebo | 275f7dea27924cdd34ab2e6c20e448b6bc4fab65 | LGPL-2.1-or-later | Redistributed in this artifact | https://code.videolan.org/videolan/libplacebo.git @ 275f7dea27924cdd34ab2e6c20e448b6bc4fab65 | [licence-99](tools/package/native-licences/ffmpeg-components/libbluray--COPYING), [licence-57](tools/package/native-licences/ffmpeg-components/glib--LICENSES--CC0-1.0.txt) |
| FFmpeg component: libpng | 0b0876829d77db0827a8cc2c4326f63be22b2aa1 | Libpng-2.0 | Redistributed in this artifact | https://github.com/glennrp/libpng.git @ 0b0876829d77db0827a8cc2c4326f63be22b2aa1 | [licence-121](tools/package/native-licences/ffmpeg-components/libpng--LICENSE.md), [licence-122](tools/package/native-licences/ffmpeg-components/libpng--LICENSES--MIT-0.txt), [licence-123](tools/package/native-licences/ffmpeg-components/libpng--LICENSES--MIT.txt), [licence-101](tools/package/native-licences/ffmpeg-components/libdvdread--COPYING), [licence-119](tools/package/native-licences/ffmpeg-components/libpng--contrib--gregbook--LICENSE), [licence-120](tools/package/native-licences/ffmpeg-components/libpng--contrib--pngminus--LICENSE.txt) |
| FFmpeg component: librist | 47ad5513d1aa0adb692d78f635512e7fa123f06e | BSD-2-Clause | Redistributed in this artifact | https://code.videolan.org/rist/librist.git @ 47ad5513d1aa0adb692d78f635512e7fa123f06e | [licence-124](tools/package/native-licences/ffmpeg-components/librist--COPYING), [licence-125](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--portable-simd--LICENSE-APACHE) |
| FFmpeg component: librsvg | 0c074d0a25adefd65843067306f9bc1fb609f68f | LGPL-2.1-or-later | Redistributed in this artifact | https://github.com/GNOME/librsvg.git @ 0c074d0a25adefd65843067306f9bc1fb609f68f | [licence-127](tools/package/native-licences/ffmpeg-components/libudfread--COPYING), [licence-126](tools/package/native-licences/ffmpeg-toolchain/crates--siphasher-1.0.4--LICENSE-MIT) |
| FFmpeg component: libsamplerate | 0844c208f683527c08ea8a80acc13b398aa9c8bf | BSD-2-Clause | Redistributed in this artifact | https://github.com/libsndfile/libsamplerate.git @ 0844c208f683527c08ea8a80acc13b398aa9c8bf | [licence-128](tools/package/native-licences/ffmpeg-components/libsamplerate--COPYING), [licence-129](tools/package/native-licences/ffmpeg-components/libsamplerate--docs--license.md) |
| FFmpeg component: libssh | 9de02f3d01ba16d06f46c0c4d27aa08d8deeecee | LGPL-2.1-or-later | Redistributed in this artifact | https://gitlab.com/libssh/libssh-mirror.git @ 9de02f3d01ba16d06f46c0c4d27aa08d8deeecee | [licence-131](tools/package/native-licences/ffmpeg-components/libssh--COPYING), [licence-130](tools/package/native-licences/ffmpeg-components/libssh--cmake--Modules--COPYING-CMAKE-SCRIPTS) |
| FFmpeg component: libtheora | 28fd5ec77f0ad0e07a371cef1047828116f6bd8a | BSD-3-Clause | Redistributed in this artifact | https://github.com/xiph/theora.git @ 28fd5ec77f0ad0e07a371cef1047828116f6bd8a | [licence-132](tools/package/native-licences/ffmpeg-components/libtheora--COPYING), [licence-133](tools/package/native-licences/ffmpeg-components/libtheora--LICENSE) |
| FFmpeg component: libudfread | b0bc6957e7e07d5f35391f210596d9eb71cffdd9 | LGPL-2.1-or-later | Redistributed in this artifact | https://code.videolan.org/videolan/libudfread.git @ b0bc6957e7e07d5f35391f210596d9eb71cffdd9 | [licence-127](tools/package/native-licences/ffmpeg-components/libudfread--COPYING) |
| FFmpeg component: libunibreak | f8172fe771ef620112247cadfb876aecaa4f769e | Zlib | Redistributed in this artifact | https://github.com/adah1972/libunibreak.git @ f8172fe771ef620112247cadfb876aecaa4f769e | [licence-134](tools/package/native-licences/ffmpeg-components/libunibreak--LICENCE) |
| FFmpeg component: libva | f052e984e0c8bf10784198cc311b23c567b1367f | MIT | Redistributed in this artifact | https://github.com/intel/libva.git @ f052e984e0c8bf10784198cc311b23c567b1367f | [licence-135](tools/package/native-licences/ffmpeg-components/libva--COPYING) |
| FFmpeg component: libvorbis | 1b75110b5a2754ba1931d82dd83cb822b266a21d | BSD-3-Clause | Redistributed in this artifact | https://github.com/xiph/vorbis.git @ 1b75110b5a2754ba1931d82dd83cb822b266a21d | [licence-136](tools/package/native-licences/ffmpeg-components/libvorbis--COPYING), [licence-137](tools/package/native-licences/ffmpeg-components/libvorbis--debian--copyright) |
| FFmpeg component: libvpx | 900b2a52b69e9d4ab72eb855c365da1100c50eb1 | BSD-3-Clause | Redistributed in this artifact | https://chromium.googlesource.com/webm/libvpx @ 900b2a52b69e9d4ab72eb855c365da1100c50eb1 | [licence-138](tools/package/native-licences/ffmpeg-components/libvpx--LICENSE), [licence-10](tools/package/native-licences/ffmpeg-components/libvpx--PATENTS), [licence-6](tools/package/native-licences/ffmpeg-components/aom--third_party--googletest--src--LICENSE), [licence-11](tools/package/native-licences/ffmpeg-components/libwebp--COPYING), [licence-8](tools/package/native-licences/ffmpeg-components/aom--third_party--libyuv--LICENSE), [licence-139](tools/package/native-licences/ffmpeg-components/libvpx--third_party--nalloc--LICENSE), [licence-9](tools/package/native-licences/ffmpeg-components/aom--third_party--x86inc--LICENSE) |
| FFmpeg component: libwebp | 1844042d1ca751e62e61df7617dba19c98588339 | BSD-3-Clause | Redistributed in this artifact | https://chromium.googlesource.com/webm/libwebp @ 1844042d1ca751e62e61df7617dba19c98588339 | [licence-11](tools/package/native-licences/ffmpeg-components/libwebp--COPYING), [licence-10](tools/package/native-licences/ffmpeg-components/libvpx--PATENTS) |
| FFmpeg component: libxml2 | c79c9612fcc77b06b0d16f35fd363d938bdbbf5e | MIT AND ISC-Veillard | Redistributed in this artifact | https://github.com/GNOME/libxml2.git @ c79c9612fcc77b06b0d16f35fd363d938bdbbf5e | [licence-140](tools/package/native-licences/ffmpeg-components/libxml2--Copyright), [licence-141](tools/package/native-licences/ffmpeg-components/libxml2--dict.c), [licence-143](tools/package/native-licences/ffmpeg-components/libxml2--list.c), [licence-145](tools/package/native-licences/ffmpeg-components/libxml2--result--html-tokenizer--NOTICE), [licence-142](tools/package/native-licences/ffmpeg-components/libxml2--dict.c-L1-17.txt), [licence-144](tools/package/native-licences/ffmpeg-components/libxml2--list.c-L1-16.txt) |
| FFmpeg component: libzmq | 46493370217ac135246617fa2f6ac819d8b61bfc | MPL-2.0 | Redistributed in this artifact | https://github.com/zeromq/libzmq.git @ 46493370217ac135246617fa2f6ac819d8b61bfc | [licence-149](tools/package/native-licences/ffmpeg-toolchain/crates--dtoa-short-0.3.5--LICENSE), [licence-146](tools/package/native-licences/ffmpeg-components/libzmq--external--sha1--license.txt), [licence-147](tools/package/native-licences/ffmpeg-components/libzmq--external--unity--license.txt), [licence-148](tools/package/native-licences/ffmpeg-components/libzmq--external--wepoll--license.txt), [licence-150](tools/package/native-licences/ffmpeg-components/libzmq--packaging--debian--copyright) |
| FFmpeg component: lilv | 4b8f30055fa5cb4134a2eb45fc1555bc04289314 | ISC | Redistributed in this artifact | https://github.com/lv2/lilv.git @ 4b8f30055fa5cb4134a2eb45fc1555bc04289314 | [licence-151](tools/package/native-licences/ffmpeg-components/serd--COPYING), [licence-152](tools/package/native-licences/ffmpeg-components/zix--LICENSES--0BSD.txt) |
| FFmpeg component: lv2 | 3c57dae600a5ad8d05acd53ee3490f7d91cb7be6 | ISC | Redistributed in this artifact | https://github.com/lv2/lv2.git @ 3c57dae600a5ad8d05acd53ee3490f7d91cb7be6 | [licence-153](tools/package/native-licences/ffmpeg-components/lv2--COPYING), [licence-154](tools/package/native-licences/ffmpeg-components/lv2--LICENSES--0BSD.txt), [licence-160](tools/package/native-licences/ffmpeg-toolchain/crates--zune-core-0.5.3--LICENSE-APACHE), [licence-155](tools/package/native-licences/ffmpeg-components/lv2--LICENSES--CC-BY-1.0.txt), [licence-156](tools/package/native-licences/ffmpeg-components/lv2--LICENSES--CC-BY-4.0.txt), [licence-157](tools/package/native-licences/ffmpeg-components/lv2--LICENSES--MIT.txt), [licence-158](tools/package/native-licences/ffmpeg-components/lv2--LICENSES--W3C-19980720.txt), [licence-159](tools/package/native-licences/ffmpeg-components/lv2--LICENSES--W3C-20150513.txt) |
| FFmpeg component: mbedtls | v4.2.0 | Apache-2.0 OR GPL-2.0-or-later | Redistributed in this artifact | https://github.com/ARMmbed/mbedtls.git @ v4.2.0 | [licence-161](tools/package/native-licences/ffmpeg-components/mbedtls--LICENSE) |
| FFmpeg component: mingw | 7213d719fe344553aa24fef7cc7dedee4940d594 | ZPL-2.1 AND LicenseRef-mingw-w64-public-domain AND BSD-3-Clause AND LGPL-2.1-or-later AND MIT | Redistributed in this artifact | https://git.code.sf.net/p/mingw-w64/mingw-w64.git @ 7213d719fe344553aa24fef7cc7dedee4940d594 | [licence-162](tools/package/native-licences/ffmpeg-components/mingw--COPYING), [licence-164](tools/package/native-licences/ffmpeg-components/mingw--COPYING.MinGW-w64-runtime--COPYING.MinGW-w64-runtime.txt), [licence-163](tools/package/native-licences/ffmpeg-components/mingw--COPYING.MinGW-w64--COPYING.MinGW-w64.txt), [licence-165](tools/package/native-licences/ffmpeg-components/mingw--DISCLAIMER), [licence-166](tools/package/native-licences/ffmpeg-components/mingw--DISCLAIMER.PD), [licence-167](tools/package/native-licences/ffmpeg-components/mingw--mingw-w64-crt--profile--COPYING), [licence-168](tools/package/native-licences/ffmpeg-components/mingw--mingw-w64-libraries--libmangle--COPYING), [licence-169](tools/package/native-licences/ffmpeg-components/mingw--mingw-w64-libraries--pseh--COPYING), [licence-170](tools/package/native-licences/ffmpeg-components/mingw--mingw-w64-libraries--winpthreads--COPYING), [licence-171](tools/package/native-licences/ffmpeg-components/mingw--mingw-w64-libraries--winstorecompat--COPYING), [licence-24](tools/package/native-licences/ffmpeg-toolchain/gcc--COPYING3) |
| FFmpeg component: mingw-std-threads | c931bac289dd431f1dd30fc4a5d1a7be36668073 | BSD-2-Clause | Redistributed in this artifact | https://github.com/meganz/mingw-std-threads.git @ c931bac289dd431f1dd30fc4a5d1a7be36668073 | [licence-172](tools/package/native-licences/ffmpeg-components/mingw-std-threads--LICENSE) |
| FFmpeg component: onevpl | 674d015bcb294bc39fa276e99a652ea045423e82 | MIT | Redistributed in this artifact | https://github.com/intel/libvpl.git @ 674d015bcb294bc39fa276e99a652ea045423e82 | [licence-174](tools/package/native-licences/ffmpeg-components/onevpl--LICENSE), [licence-173](tools/package/native-licences/ffmpeg-components/onevpl--examples--api1x_core--legacy-decode--License.txt), [licence-6](tools/package/native-licences/ffmpeg-components/aom--third_party--googletest--src--LICENSE) |
| FFmpeg component: openal | 4a52288b772d1722713675f71bb30f321e78fd80 | LGPL-2.0-or-later AND BSD-3-Clause AND LicenseRef-PFFFT-modified-BSD AND Apache-2.0 AND MIT | Redistributed in this artifact | https://github.com/kcat/openal-soft.git @ 4a52288b772d1722713675f71bb30f321e78fd80 | [licence-175](tools/package/native-licences/ffmpeg-components/openal--COPYING), [licence-177](tools/package/native-licences/ffmpeg-components/openal--LICENSE-pffft), [licence-125](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--portable-simd--LICENSE-APACHE), [licence-178](tools/package/native-licences/ffmpeg-components/openal--LICENSE.BSD-3-Clause.txt), [licence-87](tools/package/native-licences/ffmpeg-components/lcevcdec--licenses--fmt--LICENSE), [licence-176](tools/package/native-licences/ffmpeg-components/openal--gsl--LICENSE) |
| FFmpeg component: openapv | b4ff69856b4c3e8849df431ee3db54fd535f9bf3 | BSD-3-Clause | Redistributed in this artifact | https://github.com/AcademySoftwareFoundation/openapv.git @ b4ff69856b4c3e8849df431ee3db54fd535f9bf3 | [licence-179](tools/package/native-licences/ffmpeg-components/openapv--LICENSE) |
| FFmpeg component: opencl | 82f60316cc142e7b21dc1d8983b26de18858fbd9 | Apache-2.0 | Redistributed in this artifact | https://github.com/KhronosGroup/OpenCL-Headers.git @ 82f60316cc142e7b21dc1d8983b26de18858fbd9 | [licence-125](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--portable-simd--LICENSE-APACHE) |
| FFmpeg component: opencl / repository 2 | 5192c84f8059e5f703e5452929b613f9487f6e4c | Apache-2.0 | Redistributed in this artifact | https://github.com/KhronosGroup/OpenCL-ICD-Loader.git @ 5192c84f8059e5f703e5452929b613f9487f6e4c | [licence-160](tools/package/native-licences/ffmpeg-toolchain/crates--zune-core-0.5.3--LICENSE-APACHE) |
| FFmpeg component: opencore-amr | 7dba8c32238418ce0b316a852b2224df586ca896 | Apache-2.0 | Redistributed in this artifact | https://git.code.sf.net/p/opencore-amr/code @ 7dba8c32238418ce0b316a852b2224df586ca896 | [licence-180](tools/package/native-licences/ffmpeg-components/opencore-amr--LICENSE), [licence-181](tools/package/native-licences/ffmpeg-components/opencore-amr--opencore--NOTICE) |
| FFmpeg component: openh264 | 1bca62311e447fd9c39fc93de2c4b96cd5ce971c | BSD-2-Clause | Redistributed in this artifact | https://github.com/cisco/openh264.git @ 1bca62311e447fd9c39fc93de2c4b96cd5ce971c | [licence-182](tools/package/native-licences/ffmpeg-components/openh264--LICENSE) |
| FFmpeg component: openjpeg | 8314119b067c0fc77834731168daaebd379fdb12 | BSD-2-Clause | Redistributed in this artifact | https://github.com/uclouvain/openjpeg.git @ 8314119b067c0fc77834731168daaebd379fdb12 | [licence-183](tools/package/native-licences/ffmpeg-components/openjpeg--LICENSE), [licence-184](tools/package/native-licences/ffmpeg-components/openjpeg--src--bin--wx--OPJViewer--source--license.txt), [licence-185](tools/package/native-licences/ffmpeg-components/openjpeg--thirdparty--astyle--LICENSE.md), [licence-186](tools/package/native-licences/ffmpeg-components/openjpeg--thirdparty--liblcms2--COPYING), [licence-187](tools/package/native-licences/ffmpeg-components/openjpeg--thirdparty--libpng--LICENSE) |
| FFmpeg component: openmpt | 3ee3c8000b45886703816fd027369ab6ad6fc6cb | BSD-3-Clause | Redistributed in this artifact | https://github.com/OpenMPT/openmpt.git @ 3ee3c8000b45886703816fd027369ab6ad6fc6cb | [licence-214](tools/package/native-licences/ffmpeg-components/openmpt--LICENSE), [licence-212](tools/package/native-licences/ffmpeg-components/openmpt--include--SignalsmithStretch--SignalsmithStretch--LICENSE.txt), [licence-211](tools/package/native-licences/ffmpeg-components/openmpt--include--SignalsmithStretch--signalsmith-linear--LICENSE.txt), [licence-188](tools/package/native-licences/ffmpeg-components/openmpt--include--ancient--LICENSE), [licence-189](tools/package/native-licences/ffmpeg-components/openmpt--include--ancient--LICENSE.bzip2), [licence-190](tools/package/native-licences/ffmpeg-components/openmpt--include--cryptopp--License.txt), [licence-191](tools/package/native-licences/ffmpeg-components/openmpt--include--flac--COPYING.Xiph), [licence-114](tools/package/native-licences/ffmpeg-components/libmp3lame--COPYING), [licence-192](tools/package/native-licences/ffmpeg-components/openmpt--include--lhasa--COPYING.md), [licence-193](tools/package/native-licences/ffmpeg-components/openmpt--include--minimp3--LICENSE), [licence-194](tools/package/native-licences/ffmpeg-components/openmpt--include--miniz--LICENSE), [licence-195](tools/package/native-licences/ffmpeg-components/openmpt--include--mpg123--COPYING), [licence-196](tools/package/native-licences/ffmpeg-components/openmpt--include--nlohmann-json--LICENSE.MIT), [licence-116](tools/package/native-licences/ffmpeg-components/libogg--COPYING), [licence-117](tools/package/native-licences/ffmpeg-components/libopus--COPYING), [licence-197](tools/package/native-licences/ffmpeg-components/openmpt--include--opusenc--COPYING), [licence-198](tools/package/native-licences/ffmpeg-components/openmpt--include--opusfile--COPYING), [licence-200](tools/package/native-licences/ffmpeg-components/openmpt--include--portaudio--LICENSE.txt), [licence-199](tools/package/native-licences/ffmpeg-components/openmpt--include--portaudio--bindings--cpp--COPYING), [licence-202](tools/package/native-licences/ffmpeg-components/openmpt--include--premake--LICENSE.txt), [licence-201](tools/package/native-licences/ffmpeg-components/openmpt--include--premake--binmodules--luasocket--LICENSE), [licence-161](tools/package/native-licences/ffmpeg-components/mbedtls--LICENSE), [licence-218](tools/package/native-licences/ffmpeg-components/zlib--LICENSE), [licence-203](tools/package/native-licences/ffmpeg-components/openmpt--include--premake--modules--xcode--LICENSE.TXT), [licence-204](tools/package/native-licences/ffmpeg-components/openmpt--include--premake--packages--debian--copyright), [licence-205](tools/package/native-licences/ffmpeg-components/openmpt--include--pthread-win32--docs--COPYING.FSF.md), [licence-206](tools/package/native-licences/ffmpeg-components/openmpt--include--pthread-win32--docs--COPYING.md), [licence-207](tools/package/native-licences/ffmpeg-components/openmpt--include--pugixml--LICENSE.md), [licence-208](tools/package/native-licences/ffmpeg-components/openmpt--include--r8brain--LICENSE), [licence-209](tools/package/native-licences/ffmpeg-components/openmpt--include--rtaudio--LICENSE), [licence-210](tools/package/native-licences/ffmpeg-components/openmpt--include--rtmidi--LICENSE), [licence-213](tools/package/native-licences/ffmpeg-components/openmpt--include--unrar--license.txt), [licence-136](tools/package/native-licences/ffmpeg-components/libvorbis--COPYING), [licence-217](tools/package/native-licences/ffmpeg-components/zlib--contrib--minizip--LICENSE.Info-Zip), [licence-215](tools/package/native-licences/ffmpeg-components/openmpt--src--mpt--LICENSE.BSD-3-Clause.txt), [licence-216](tools/package/native-licences/ffmpeg-components/openmpt--src--mpt--LICENSE.BSL-1.0.txt) |
| FFmpeg component: openssl | openssl-3.6.5 | Apache-2.0 | Redistributed in this artifact | https://github.com/openssl/openssl.git @ openssl-3.6.5 | [licence-220](tools/package/native-licences/ffmpeg-components/openssl--LICENSE.txt), [licence-219](tools/package/native-licences/ffmpeg-components/openssl--external--perl--Text-Template-1.56--LICENSE) |
| FFmpeg component: pango | 68e981d243d50e03f3df12fb400f31647ef570d2 | LGPL-2.0-or-later | Redistributed in this artifact | https://github.com/GNOME/pango.git @ 68e981d243d50e03f3df12fb400f31647ef570d2 | [licence-221](tools/package/native-licences/ffmpeg-components/pango--COPYING) |
| FFmpeg component: pcre2 | be940c4eaec0bc4117e06e8f14e56bf82089be6b | BSD-3-Clause | Redistributed in this artifact | https://github.com/PCRE2Project/pcre2.git @ be940c4eaec0bc4117e06e8f14e56bf82089be6b | [licence-223](tools/package/native-licences/ffmpeg-components/pcre2--LICENCE.md), [licence-222](tools/package/native-licences/ffmpeg-components/pcre2--cmake--COPYING-CMAKE-SCRIPTS) |
| FFmpeg component: pixman | e7fd44140fe6edef507d54bdbc25c09543ffc936 | MIT | Redistributed in this artifact | https://gitlab.freedesktop.org/pixman/pixman.git @ e7fd44140fe6edef507d54bdbc25c09543ffc936 | [licence-224](tools/package/native-licences/ffmpeg-components/pixman--COPYING) |
| FFmpeg component: rav1e | 31435de9d76fddd38f6dcc31d4014574cebb2092 | BSD-2-Clause | Redistributed in this artifact | https://github.com/xiph/rav1e.git @ 31435de9d76fddd38f6dcc31d4014574cebb2092 | [licence-226](tools/package/native-licences/ffmpeg-components/rav1e--LICENSE), [licence-227](tools/package/native-licences/ffmpeg-components/rav1e--PATENTS), [licence-225](tools/package/native-licences/ffmpeg-components/rav1e--ivf--LICENSE) |
| FFmpeg component: rubberband | e4296ac80b1170018a110bc326fd0d45a0eb27d6 | GPL-2.0-or-later | Redistributed in this artifact | https://github.com/breakfastquay/rubberband.git @ e4296ac80b1170018a110bc326fd0d45a0eb27d6 | [licence-228](tools/package/native-licences/ffmpeg-components/rubberband--COPYING), [licence-26](tools/package/native-licences/ffmpeg-components/chromaprint--src--3rdparty--kissfft--COPYING), [licence-229](tools/package/native-licences/ffmpeg-components/rubberband--src--ext--speex--COPYING) |
| FFmpeg component: sdl | 8acf7cfc0f88717e5c036f60f0314bfcafe39189 | Zlib | Redistributed in this artifact | https://github.com/libsdl-org/SDL.git @ 8acf7cfc0f88717e5c036f60f0314bfcafe39189 | [licence-230](tools/package/native-licences/ffmpeg-components/sdl--LICENSE.txt), [licence-237](tools/package/native-licences/ffmpeg-components/sdl--Xcode-iOS--Demos--data--bitmapfont--license.txt), [licence-236](tools/package/native-licences/ffmpeg-components/sdl--Xcode--SDL--pkg-support--resources--License.txt), [licence-231](tools/package/native-licences/ffmpeg-components/sdl--src--hidapi--LICENSE-bsd.txt), [licence-24](tools/package/native-licences/ffmpeg-toolchain/gcc--COPYING3), [licence-232](tools/package/native-licences/ffmpeg-components/sdl--src--hidapi--LICENSE-orig.txt), [licence-233](tools/package/native-licences/ffmpeg-components/sdl--src--hidapi--LICENSE.txt), [licence-234](tools/package/native-licences/ffmpeg-components/sdl--src--video--yuv2rgb--LICENSE), [licence-235](tools/package/native-licences/ffmpeg-components/sdl--visualtest--COPYING.txt) |
| FFmpeg component: serd | b621b0bc790d1e8102d3138ead16b974ddda8432 | ISC | Redistributed in this artifact | https://github.com/drobilla/serd.git @ b621b0bc790d1e8102d3138ead16b974ddda8432 | [licence-151](tools/package/native-licences/ffmpeg-components/serd--COPYING), [licence-238](tools/package/native-licences/ffmpeg-components/serd--LICENSES--0BSD.txt), [licence-239](tools/package/native-licences/ffmpeg-components/serd--LICENSES--BSD-3-Clause.txt) |
| FFmpeg component: shaderc | 2737994b552137a85545f956e303d620e6ff232c | Apache-2.0 | Redistributed in this artifact | https://github.com/google/shaderc.git @ 2737994b552137a85545f956e303d620e6ff232c | [licence-160](tools/package/native-licences/ffmpeg-toolchain/crates--zune-core-0.5.3--LICENSE-APACHE), [licence-240](tools/package/native-licences/ffmpeg-components/shaderc--third_party--LICENSE.glslang), [licence-241](tools/package/native-licences/ffmpeg-components/shaderc--third_party--LICENSE.spirv-tools) |
| FFmpeg component: snappy | 946606459314e55d029c85f9a8c46f8809467f0f | BSD-3-Clause | Redistributed in this artifact | https://github.com/google/snappy.git @ 946606459314e55d029c85f9a8c46f8809467f0f | [licence-242](tools/package/native-licences/ffmpeg-components/snappy--COPYING), [licence-243](tools/package/native-licences/ffmpeg-components/snappy--COPYING.notestdata) |
| FFmpeg component: sord | 4b5232bb91e7f2f1b84df384494d073fabbcd312 | ISC | Redistributed in this artifact | https://github.com/drobilla/sord.git @ 4b5232bb91e7f2f1b84df384494d073fabbcd312 | [licence-151](tools/package/native-licences/ffmpeg-components/serd--COPYING), [licence-154](tools/package/native-licences/ffmpeg-components/lv2--LICENSES--0BSD.txt), [licence-239](tools/package/native-licences/ffmpeg-components/serd--LICENSES--BSD-3-Clause.txt), [licence-244](tools/package/native-licences/ffmpeg-components/sord--LICENSES--ISC.txt) |
| FFmpeg component: soxr | 945b592b70470e29f917f4de89b4281fbbd540c0 | LGPL-2.1-or-later | Redistributed in this artifact | https://git.code.sf.net/p/soxr/code @ 945b592b70470e29f917f4de89b4281fbbd540c0 | [licence-245](tools/package/native-licences/ffmpeg-components/soxr--COPYING.LGPL), [licence-246](tools/package/native-licences/ffmpeg-components/soxr--LICENCE), [licence-100](tools/package/native-licences/ffmpeg-components/libdvdnav--COPYING) |
| FFmpeg component: spirv-cross | 300681bbcb8365a8d1eacdacdbdd0249bbf1d6b1 | Apache-2.0 | Redistributed in this artifact | https://github.com/KhronosGroup/SPIRV-Cross.git @ 300681bbcb8365a8d1eacdacdbdd0249bbf1d6b1 | [licence-125](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--portable-simd--LICENSE-APACHE), [licence-247](tools/package/native-licences/ffmpeg-components/spirv-cross--LICENSES--Apache-2.0.txt), [licence-248](tools/package/native-licences/ffmpeg-components/spirv-cross--LICENSES--CC-BY-4.0.txt), [licence-70](tools/package/native-licences/ffmpeg-components/spirv-cross--LICENSES--LicenseRef-KhronosFreeUse.txt), [licence-249](tools/package/native-licences/ffmpeg-components/spirv-cross--LICENSES--MIT.txt) |
| FFmpeg component: spirv-headers | fbf86836a9b1966586faf7be7bb8a6440e156d62 | MIT | Redistributed in this artifact | https://github.com/KhronosGroup/SPIRV-Headers.git @ fbf86836a9b1966586faf7be7bb8a6440e156d62 | [licence-250](tools/package/native-licences/ffmpeg-components/spirv-headers--LICENSE), [licence-251](tools/package/native-licences/ffmpeg-components/spirv-headers--LICENSES--CC-BY-4.0.txt), [licence-252](tools/package/native-licences/ffmpeg-components/spirv-headers--LICENSES--MIT.txt) |
| FFmpeg component: spirv-headers-shaderc | 86f980c731e62ae4eaf383d320449d71687936bf | MIT | Redistributed in this artifact | https://github.com/KhronosGroup/SPIRV-Headers.git @ 86f980c731e62ae4eaf383d320449d71687936bf | [licence-250](tools/package/native-licences/ffmpeg-components/spirv-headers--LICENSE), [licence-251](tools/package/native-licences/ffmpeg-components/spirv-headers--LICENSES--CC-BY-4.0.txt), [licence-252](tools/package/native-licences/ffmpeg-components/spirv-headers--LICENSES--MIT.txt) |
| FFmpeg component: spirv-tools | 71f287f18ed78d496e724fbfb1c3feae3a2af75a | Apache-2.0 | Redistributed in this artifact | https://github.com/KhronosGroup/SPIRV-Tools.git @ 71f287f18ed78d496e724fbfb1c3feae3a2af75a | [licence-125](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--portable-simd--LICENSE-APACHE) |
| FFmpeg component: sratom | 9e8ee84eed502e6030ce8bb49694fd28542b08fc | ISC | Redistributed in this artifact | https://github.com/lv2/sratom.git @ 9e8ee84eed502e6030ce8bb49694fd28542b08fc | [licence-253](tools/package/native-licences/ffmpeg-components/sratom--COPYING), [licence-254](tools/package/native-licences/ffmpeg-components/sratom--LICENSES--0BSD.txt) |
| FFmpeg component: srt | 9f2390232a8256ed4c72a5418c2b2777c49ad737 | MPL-2.0 | Redistributed in this artifact | https://github.com/Haivision/srt.git @ 9f2390232a8256ed4c72a5418c2b2777c49ad737 | [licence-255](tools/package/native-licences/ffmpeg-toolchain/crates--cssparser-0.37.0--LICENSE) |
| FFmpeg component: svtav1 | f2c3fb78611d542b12b11c6d10d3744b31b754a0 | BSD-3-Clause-Clear AND BSD-2-Clause | Redistributed in this artifact | https://gitlab.com/AOMediaCodec/SVT-AV1.git @ f2c3fb78611d542b12b11c6d10d3744b31b754a0 | [licence-256](tools/package/native-licences/ffmpeg-components/svtav1--LICENSE-BSD2.md), [licence-257](tools/package/native-licences/ffmpeg-components/svtav1--LICENSE.md), [licence-258](tools/package/native-licences/ffmpeg-components/svtav1--PATENTS.md), [licence-259](tools/package/native-licences/ffmpeg-components/svtav1--third_party--fastfeat--LICENSE), [licence-260](tools/package/native-licences/ffmpeg-components/svtav1--third_party--safestringlib--LICENSE) |
| FFmpeg component: twolame | 6fced852d4d5cfad58cf9dbe3ea619b08e87d398 | LGPL-2.1-or-later | Redistributed in this artifact | https://github.com/njh/twolame.git @ 6fced852d4d5cfad58cf9dbe3ea619b08e87d398 | [licence-261](tools/package/native-licences/ffmpeg-components/twolame--COPYING) |
| FFmpeg component: uavs3d | 0e20d2c291853f196c68922a264bcd8471d75b68 | BSD-3-Clause | Redistributed in this artifact | https://github.com/uavs3/uavs3d.git @ 0e20d2c291853f196c68922a264bcd8471d75b68 | [licence-262](tools/package/native-licences/ffmpeg-components/uavs3d--COPYING) |
| FFmpeg component: vapoursynth | R81 | LGPL-2.1-or-later | Redistributed in this artifact | https://github.com/vapoursynth/vapoursynth.git @ R81 | [licence-263](tools/package/native-licences/ffmpeg-components/vapoursynth--COPYING.LESSER) |
| FFmpeg component: vidstab | e2445c4081658318223762a696eb1c645c2d7168 | LGPL-2.1-or-later | Redistributed in this artifact | https://github.com/georgmartius/vid.stab.git @ e2445c4081658318223762a696eb1c645c2d7168 | [licence-127](tools/package/native-licences/ffmpeg-components/libudfread--COPYING), [licence-264](tools/package/native-licences/ffmpeg-components/vidstab--LICENSE) |
| FFmpeg component: vmaf | f712fa7564fe49b12991d83920b83573af2ae063 | BSD-2-Clause-Patent | Redistributed in this artifact | https://github.com/Netflix/vmaf.git @ f712fa7564fe49b12991d83920b83573af2ae063 | [licence-265](tools/package/native-licences/ffmpeg-components/vmaf--LICENSE) |
| FFmpeg component: vulkan-headers | v1.4.366 | Apache-2.0 OR MIT | Redistributed in this artifact | https://github.com/KhronosGroup/Vulkan-Headers.git @ v1.4.366 | [licence-266](tools/package/native-licences/ffmpeg-components/vulkan-headers--LICENSE.md), [licence-125](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--portable-simd--LICENSE-APACHE), [licence-267](tools/package/native-licences/ffmpeg-components/vulkan-headers--LICENSES--MIT.txt) |
| FFmpeg component: vulkan-loader | 65b3936528cd92eb4ea3de485d03f858a3850484 | MIT | Redistributed in this artifact | https://github.com/BtbN/Vulkan-Shim-Loader.git @ 65b3936528cd92eb4ea3de485d03f858a3850484 | [licence-268](tools/package/native-licences/ffmpeg-components/vulkan-loader--LICENSE) |
| FFmpeg component: vulkan-loader / repository 2 | v1.4.366 | Apache-2.0 OR MIT | Redistributed in this artifact | https://github.com/KhronosGroup/Vulkan-Headers.git @ v1.4.366 | [licence-266](tools/package/native-licences/ffmpeg-components/vulkan-headers--LICENSE.md), [licence-125](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--portable-simd--LICENSE-APACHE), [licence-267](tools/package/native-licences/ffmpeg-components/vulkan-headers--LICENSES--MIT.txt) |
| FFmpeg component: vvenc | 0e7508b811bbea3cd510956ddb3193f3a4c93684 | BSD-3-Clause-Clear | Redistributed in this artifact | https://github.com/fraunhoferhhi/vvenc.git @ 0e7508b811bbea3cd510956ddb3193f3a4c93684 | [licence-269](tools/package/native-licences/ffmpeg-components/vvenc--LICENSE.txt), [licence-270](tools/package/native-licences/ffmpeg-components/vvenc--thirdparty--nlohmann_json--LICENSE.MIT), [licence-271](tools/package/native-licences/ffmpeg-components/vvenc--thirdparty--simde--COPYING) |
| FFmpeg component: x264 | 0480cb05fa188d37ae87e8f4fd8f1aea3711f7ee | GPL-2.0-or-later | Redistributed in this artifact | https://code.videolan.org/videolan/x264.git @ 0480cb05fa188d37ae87e8f4fd8f1aea3711f7ee | [licence-100](tools/package/native-licences/ffmpeg-components/libdvdnav--COPYING) |
| FFmpeg component: x265 | 5143a2a00ad0cc600831654a248b96ec7307eb4a | GPL-2.0-or-later AND MIT | Redistributed in this artifact | https://github.com/Multicorewareinc/x265.git @ 5143a2a00ad0cc600831654a248b96ec7307eb4a | [licence-272](tools/package/native-licences/ffmpeg-components/x265--COPYING), [licence-274](tools/package/native-licences/ffmpeg-components/x265--source--dynamicHDR10--LICENSE.txt), [licence-273](tools/package/native-licences/ffmpeg-components/x265--source--dynamicHDR10--json11--LICENSE.txt) |
| FFmpeg component: xavs2 | eae1e8b9d12468059bdd7dee893508e470fa83d8 | GPL-2.0-or-later | Redistributed in this artifact | https://github.com/pkuvcl/xavs2.git @ eae1e8b9d12468059bdd7dee893508e470fa83d8 | [licence-32](tools/package/native-licences/ffmpeg-components/davs2--COPYING) |
| FFmpeg component: xvid | 2204 | GPL-2.0-or-later | Redistributed in this artifact | https://svn.xvid.org/trunk/xvidcore @ 2204 | [licence-275](tools/package/native-licences/ffmpeg-components/xvid--LICENSE) |
| FFmpeg component: xxhash | 61fd0fece2ebafc5bd9b573050e0c046c4e48d28 | BSD-2-Clause | Redistributed in this artifact | https://github.com/Cyan4973/xxHash.git @ 61fd0fece2ebafc5bd9b573050e0c046c4e48d28 | [licence-276](tools/package/native-licences/ffmpeg-components/xxhash--LICENSE), [licence-73](tools/package/native-licences/ffmpeg-components/gmp--COPYINGv2) |
| FFmpeg component: xz | 299eb5c3f597f107fd6019bf156885ac8bfaa5ea | 0BSD | Redistributed in this artifact | https://github.com/tukaani-project/xz.git @ 299eb5c3f597f107fd6019bf156885ac8bfaa5ea | [licence-277](tools/package/native-licences/ffmpeg-components/xz--COPYING), [licence-278](tools/package/native-licences/ffmpeg-components/xz--COPYING.0BSD), [licence-106](tools/package/native-licences/ffmpeg-components/gnulib--doc--COPYINGv2), [licence-69](tools/package/native-licences/ffmpeg-components/gnulib--doc--COPYINGv3), [licence-52](tools/package/native-licences/ffmpeg-components/libiconv--COPYING.LIB) |
| FFmpeg component: zimg | 67e0603271c080e22c8429856dd4a8a56587e61e | WTFPL | Redistributed in this artifact | https://github.com/sekrit-twc/zimg.git @ 67e0603271c080e22c8429856dd4a8a56587e61e | [licence-279](tools/package/native-licences/ffmpeg-components/zimg--COPYING) |
| FFmpeg component: zix | 17d632393f5addb6fa24dda2927b96515407cca7 | ISC | Redistributed in this artifact | https://github.com/drobilla/zix.git @ 17d632393f5addb6fa24dda2927b96515407cca7 | [licence-280](tools/package/native-licences/ffmpeg-components/zix--COPYING), [licence-152](tools/package/native-licences/ffmpeg-components/zix--LICENSES--0BSD.txt), [licence-281](tools/package/native-licences/ffmpeg-components/zix--LICENSES--ISC.txt) |
| FFmpeg component: zlib | 9d314c341b2ce16e01ae44e27ec3dd2f32aa58fd | Zlib | Redistributed in this artifact | https://github.com/madler/zlib.git @ 9d314c341b2ce16e01ae44e27ec3dd2f32aa58fd | [licence-218](tools/package/native-licences/ffmpeg-components/zlib--LICENSE), [licence-282](tools/package/native-licences/ffmpeg-components/zlib--contrib--dotzlib--LICENSE_1_0.txt), [licence-217](tools/package/native-licences/ffmpeg-components/zlib--contrib--minizip--LICENSE.Info-Zip) |
| FFmpeg toolchain runtime: addr2line 0.27.1 (toolchain) | 0.27.1 | Apache-2.0 OR MIT | Redistributed in this artifact | https://static.crates.io/crates/addr2line/addr2line-0.27.1.crate (crate archive sha256 e567177890eb1617b1f774005b66b26b2377afd138a2ca37aae7d8f0c81429d4); https://github.com/gimli-rs/addr2line | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-283](tools/package/native-licences/ffmpeg-toolchain/crates--addr2line-0.27.1--LICENSE-MIT) |
| FFmpeg toolchain runtime: adler2 2.0.1 (librsvg) | 2.0.1 | 0BSD OR MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/adler2/adler2-2.0.1.crate (crate archive sha256 320119579fcad9c21884f5c4861d16174d0e06250625266f50fe6898340abefa); https://github.com/oyvindln/adler2 | [licence-285](tools/package/native-licences/ffmpeg-toolchain/crates--adler2-2.0.1--LICENSE-0BSD), [licence-286](tools/package/native-licences/ffmpeg-toolchain/crates--adler2-2.0.1--LICENSE-APACHE), [licence-287](tools/package/native-licences/ffmpeg-toolchain/crates--adler2-2.0.1--LICENSE-MIT) |
| FFmpeg toolchain runtime: adler2 2.0.1 (toolchain) | 2.0.1 | 0BSD OR MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/adler2/adler2-2.0.1.crate (crate archive sha256 320119579fcad9c21884f5c4861d16174d0e06250625266f50fe6898340abefa); https://github.com/oyvindln/adler2 | [licence-285](tools/package/native-licences/ffmpeg-toolchain/crates--adler2-2.0.1--LICENSE-0BSD), [licence-286](tools/package/native-licences/ffmpeg-toolchain/crates--adler2-2.0.1--LICENSE-APACHE), [licence-287](tools/package/native-licences/ffmpeg-toolchain/crates--adler2-2.0.1--LICENSE-MIT) |
| FFmpeg toolchain runtime: ahash 0.8.12 (librsvg) | 0.8.12 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/ahash/ahash-0.8.12.crate (crate archive sha256 5a15f179cd60c4584b8a8c596927aadc462e27f2ca70c04e0071964a73ba7a75); https://github.com/tkaitchuck/ahash | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-288](tools/package/native-licences/ffmpeg-toolchain/crates--ahash-0.8.12--LICENSE-MIT) |
| FFmpeg toolchain runtime: aho-corasick 1.1.5 (librsvg) | 1.1.5 | Unlicense OR MIT | Redistributed in this artifact | https://static.crates.io/crates/aho-corasick/aho-corasick-1.1.5.crate (crate archive sha256 c982642fa9e8606056828ee9a8505737230110bb1099153c79efe865c59d12ba); https://github.com/BurntSushi/aho-corasick | [licence-289](tools/package/native-licences/ffmpeg-toolchain/crates--memchr-2.8.3--COPYING), [licence-290](tools/package/native-licences/ffmpeg-toolchain/crates--memchr-2.8.3--LICENSE-MIT), [licence-291](tools/package/native-licences/ffmpeg-toolchain/crates--memchr-2.8.3--UNLICENSE) |
| FFmpeg toolchain runtime: aligned 0.4.2 (rav1e) | 0.4.2 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/aligned/aligned-0.4.2.crate (crate archive sha256 377e4c0ba83e4431b10df45c1d4666f178ea9c552cac93e60c3a88bf32785923); https://github.com/rust-embedded-community/aligned | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-292](tools/package/native-licences/ffmpeg-toolchain/crates--aligned-0.4.2--LICENSE-MIT) |
| FFmpeg toolchain runtime: aligned-vec 0.6.4 (rav1e) | 0.6.4 | MIT | Redistributed in this artifact | https://static.crates.io/crates/aligned-vec/aligned-vec-0.6.4.crate (crate archive sha256 dc890384c8602f339876ded803c97ad529f3842aba97f6392b3dba0dd171769b); https://github.com/sarah-ek/aligned-vec/ | [licence-293](tools/package/native-licences/ffmpeg-toolchain/crates--aligned-vec-0.6.4--LICENSE) |
| FFmpeg toolchain runtime: anstream 0.6.19 (rav1e) | 0.6.19 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/anstream/anstream-0.6.19.crate (crate archive sha256 301af1932e46185686725e0fad2f8f2aa7da69dd70bf6ecc44d6b703844a3933); https://github.com/rust-cli/anstyle.git | [licence-294](tools/package/native-licences/ffmpeg-toolchain/crates--anstream-0.6.19--LICENSE-APACHE), [licence-295](tools/package/native-licences/ffmpeg-toolchain/crates--anstream-0.6.19--LICENSE-MIT) |
| FFmpeg toolchain runtime: anstyle 1.0.11 (rav1e) | 1.0.11 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/anstyle/anstyle-1.0.11.crate (crate archive sha256 862ed96ca487e809f1c8e5a8447f6ee2cf102f846893800b20cebdf541fc6bbd); https://github.com/rust-cli/anstyle.git | [licence-294](tools/package/native-licences/ffmpeg-toolchain/crates--anstream-0.6.19--LICENSE-APACHE), [licence-295](tools/package/native-licences/ffmpeg-toolchain/crates--anstream-0.6.19--LICENSE-MIT) |
| FFmpeg toolchain runtime: anstyle-parse 0.2.7 (rav1e) | 0.2.7 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/anstyle-parse/anstyle-parse-0.2.7.crate (crate archive sha256 4e7644824f0aa2c7b9384579234ef10eb7efb6a0deb83f9630a49594dd9c15c2); https://github.com/rust-cli/anstyle.git | [licence-294](tools/package/native-licences/ffmpeg-toolchain/crates--anstream-0.6.19--LICENSE-APACHE), [licence-295](tools/package/native-licences/ffmpeg-toolchain/crates--anstream-0.6.19--LICENSE-MIT) |
| FFmpeg toolchain runtime: anstyle-query 1.1.3 (rav1e) | 1.1.3 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/anstyle-query/anstyle-query-1.1.3.crate (crate archive sha256 6c8bdeb6047d8983be085bab0ba1472e6dc604e7041dbf6fcd5e71523014fae9); https://github.com/rust-cli/anstyle.git | [licence-294](tools/package/native-licences/ffmpeg-toolchain/crates--anstream-0.6.19--LICENSE-APACHE), [licence-295](tools/package/native-licences/ffmpeg-toolchain/crates--anstream-0.6.19--LICENSE-MIT) |
| FFmpeg toolchain runtime: anstyle-wincon 3.0.9 (rav1e) | 3.0.9 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/anstyle-wincon/anstyle-wincon-3.0.9.crate (crate archive sha256 403f75924867bb1033c59fbf0797484329750cfbe3c4325cd33127941fabc882); https://github.com/rust-cli/anstyle.git | [licence-294](tools/package/native-licences/ffmpeg-toolchain/crates--anstream-0.6.19--LICENSE-APACHE), [licence-295](tools/package/native-licences/ffmpeg-toolchain/crates--anstream-0.6.19--LICENSE-MIT) |
| FFmpeg toolchain runtime: anyhow 1.0.98 (rav1e) | 1.0.98 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/anyhow/anyhow-1.0.98.crate (crate archive sha256 e16d2d3311acee920a9eb8d33b8cbc1787ce4a264e85f964c2404b969bdcd487); https://github.com/dtolnay/anyhow | [licence-296](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--LICENSE-APACHE), [licence-287](tools/package/native-licences/ffmpeg-toolchain/crates--adler2-2.0.1--LICENSE-MIT) |
| FFmpeg toolchain runtime: approx 0.5.1 (librsvg) | 0.5.1 | Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/approx/approx-0.5.1.crate (crate archive sha256 cab112f0a86d568ea0e627cc1d6be74a1e9cd55214684db5561995f6dad897c6); https://github.com/brendanzab/approx | [licence-297](tools/package/native-licences/ffmpeg-toolchain/crates--approx-0.5.1--LICENSE) |
| FFmpeg toolchain runtime: arrayvec 0.7.6 (rav1e) | 0.7.6 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/arrayvec/arrayvec-0.7.6.crate (crate archive sha256 7c02d123df017efcdfbd739ef81735b36c5ba83ec3c59c80a9d7ecc718f92e50); https://github.com/bluss/arrayvec | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-298](tools/package/native-licences/ffmpeg-toolchain/crates--arrayvec-0.7.6--LICENSE-MIT) |
| FFmpeg toolchain runtime: as-slice 0.2.1 (rav1e) | 0.2.1 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/as-slice/as-slice-0.2.1.crate (crate archive sha256 516b6b4f0e40d50dcda9365d53964ec74560ad4284da2e7fc97122cd83174516); https://github.com/japaric/as-slice | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-299](tools/package/native-licences/ffmpeg-toolchain/crates--as-slice-0.2.1--LICENSE-MIT) |
| FFmpeg toolchain runtime: av-data 0.4.4 (librsvg) | 0.4.4 | MIT | Redistributed in this artifact | https://static.crates.io/crates/av-data/av-data-0.4.4.crate (crate archive sha256 fca67ba5d317924c02180c576157afd54babe48a76ebc66ce6d34bb8ba08308e); https://crates.io/crates/av-data | [licence-300](tools/package/native-licences/ffmpeg-toolchain/crates--av-data-0.4.4--LICENSE) |
| FFmpeg toolchain runtime: av-metrics 0.9.1 (rav1e) | 0.9.1 | MIT | Redistributed in this artifact | https://static.crates.io/crates/av-metrics/av-metrics-0.9.1.crate (crate archive sha256 996ce95bbdb0203e5b91d4a0c9b81c0d67d11c80f884482a0c1ea19e732e3530); https://github.com/rust-av/av-metrics | [licence-37](tools/package/native-licences/ffmpeg-toolchain/spdx--text--MIT.txt) |
| FFmpeg toolchain runtime: av-scenechange 0.14.1 (rav1e) | 0.14.1 | MIT | Redistributed in this artifact | https://static.crates.io/crates/av-scenechange/av-scenechange-0.14.1.crate (crate archive sha256 0f321d77c20e19b92c39e7471cf986812cbb46659d2af674adc4331ef3f18394); https://github.com/rust-av/av-scenechange | [licence-301](tools/package/native-licences/ffmpeg-toolchain/crates--av-scenechange-0.14.1--LICENSE) |
| FFmpeg toolchain runtime: av1-grain 0.2.4 (rav1e) | 0.2.4 | BSD-2-Clause | Redistributed in this artifact | https://static.crates.io/crates/av1-grain/av1-grain-0.2.4.crate (crate archive sha256 4f3efb2ca85bc610acfa917b5aaa36f3fcbebed5b3182d7f877b02531c4b80c8); https://github.com/rust-av/av1-grain | [licence-302](tools/package/native-licences/ffmpeg-toolchain/crates--av1-grain-0.2.4--LICENSE) |
| FFmpeg toolchain runtime: backtrace 0.3.76 (toolchain) | 0.3.76 | MIT OR Apache-2.0 | Redistributed in this artifact | https://github.com/rust-lang/backtrace-rs @ d902726a1dcdc1e1c66f73d1162181b5423c645b; https://github.com/rust-lang/backtrace-rs/tree/d902726a1dcdc1e1c66f73d1162181b5423c645b | [licence-303](tools/package/native-licences/ffmpeg-toolchain/rust-lang-backtrace-rs--LICENSE-MIT), [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE) |
| FFmpeg toolchain runtime: bitflags 2.13.2 (librsvg) | 2.13.2 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/bitflags/bitflags-2.13.2.crate (crate archive sha256 3ded4057c258ba199e2d26386d3af3780957ecaee6c4ef4041c6b4b8b97c0b06); https://github.com/bitflags/bitflags | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-304](tools/package/native-licences/ffmpeg-toolchain/crates--log-0.4.34--LICENSE-MIT) |
| FFmpeg toolchain runtime: bitreader 0.3.11 (librsvg) | 0.3.11 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/bitreader/bitreader-0.3.11.crate (crate archive sha256 886559b1e163d56c765bc3a985febb4eee8009f625244511d8ee3c432e08c066); https://github.com/irauta/bitreader | [licence-125](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--portable-simd--LICENSE-APACHE), [licence-305](tools/package/native-licences/ffmpeg-toolchain/crates--bitreader-0.3.11--LICENSE-MIT) |
| FFmpeg toolchain runtime: bitstream-io 4.2.0 (rav1e) | 4.2.0 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/bitstream-io/bitstream-io-4.2.0.crate (crate archive sha256 6afa0fc725d5ac9efc66f47b4c533ee850eb34aa6105681b5349c27157346ffa); https://github.com/tuffy/bitstream-io | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-306](tools/package/native-licences/ffmpeg-toolchain/crates--bitstream-io-4.2.0--LICENSE-MIT) |
| FFmpeg toolchain runtime: byte-slice-cast 1.2.3 (librsvg) | 1.2.3 | MIT | Redistributed in this artifact | https://static.crates.io/crates/byte-slice-cast/byte-slice-cast-1.2.3.crate (crate archive sha256 7575182f7272186991736b70173b0ea045398f984bf5ebbb3804736ce1330c9d); https://github.com/sdroege/bytes-num-slice-cast | [licence-307](tools/package/native-licences/ffmpeg-toolchain/crates--byte-slice-cast-1.2.3--LICENSE) |
| FFmpeg toolchain runtime: bytemuck 1.25.2 (librsvg) | 1.25.2 | Zlib OR Apache-2.0 OR MIT | Redistributed in this artifact | https://static.crates.io/crates/bytemuck/bytemuck-1.25.2.crate (crate archive sha256 95832e849adfb21180ccb6826a99da14e5d266ae5c2e668e1602cf234f153797); https://github.com/Lokathor/bytemuck | [licence-308](tools/package/native-licences/ffmpeg-toolchain/crates--bytemuck-1.25.2--LICENSE-APACHE), [licence-309](tools/package/native-licences/ffmpeg-toolchain/crates--bytemuck-1.25.2--LICENSE-MIT), [licence-310](tools/package/native-licences/ffmpeg-toolchain/crates--bytemuck-1.25.2--LICENSE-ZLIB) |
| FFmpeg toolchain runtime: byteorder 1.5.0 (librsvg) | 1.5.0 | Unlicense OR MIT | Redistributed in this artifact | https://static.crates.io/crates/byteorder/byteorder-1.5.0.crate (crate archive sha256 1fd0f2584146f6f2ef48085050886acf353beff7305ebd1ae69500e27c67f64b); https://github.com/BurntSushi/byteorder | [licence-289](tools/package/native-licences/ffmpeg-toolchain/crates--memchr-2.8.3--COPYING), [licence-290](tools/package/native-licences/ffmpeg-toolchain/crates--memchr-2.8.3--LICENSE-MIT), [licence-291](tools/package/native-licences/ffmpeg-toolchain/crates--memchr-2.8.3--UNLICENSE) |
| FFmpeg toolchain runtime: byteorder-lite 0.1.0 (librsvg) | 0.1.0 | Unlicense OR MIT | Redistributed in this artifact | https://static.crates.io/crates/byteorder-lite/byteorder-lite-0.1.0.crate (crate archive sha256 8f1fe948ff07f4bd06c30984e69f5b4899c516a3ef74f34df92a2df2ab535495); https://github.com/image-rs/byteorder-lite | [licence-290](tools/package/native-licences/ffmpeg-toolchain/crates--memchr-2.8.3--LICENSE-MIT), [licence-291](tools/package/native-licences/ffmpeg-toolchain/crates--memchr-2.8.3--UNLICENSE) |
| FFmpeg toolchain runtime: bytes 1.12.1 (librsvg) | 1.12.1 | MIT | Redistributed in this artifact | https://static.crates.io/crates/bytes/bytes-1.12.1.crate (crate archive sha256 fc652a48c352aef3ea3aed32080501cf3ef6ed5da78602a020c991775b0aff04); https://github.com/tokio-rs/bytes | [licence-311](tools/package/native-licences/ffmpeg-toolchain/crates--bytes-1.12.1--LICENSE) |
| FFmpeg toolchain runtime: cairo-rs 0.22.9 (librsvg) | 0.22.9 | MIT | Redistributed in this artifact | https://static.crates.io/crates/cairo-rs/cairo-rs-0.22.9.crate (crate archive sha256 df683f1d30b457964673a5541a4603208ef95ab6873d2a55871895cf310f3b56); https://github.com/gtk-rs/gtk-rs-core | [licence-312](tools/package/native-licences/ffmpeg-toolchain/crates--cairo-rs-0.22.9--COPYRIGHT), [licence-313](tools/package/native-licences/ffmpeg-toolchain/crates--cairo-rs-0.22.9--LICENSE) |
| FFmpeg toolchain runtime: cairo-sys-rs 0.22.9 (librsvg) | 0.22.9 | MIT | Redistributed in this artifact | https://static.crates.io/crates/cairo-sys-rs/cairo-sys-rs-0.22.9.crate (crate archive sha256 ee548131103ad8f698c6725669647b9c757b3b66992dd6a026037596417bee21); https://github.com/gtk-rs/gtk-rs-core | [licence-313](tools/package/native-licences/ffmpeg-toolchain/crates--cairo-rs-0.22.9--LICENSE) |
| FFmpeg toolchain runtime: cast 0.3.0 (librsvg) | 0.3.0 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/cast/cast-0.3.0.crate (crate archive sha256 37b2a672a2cb129a2e41c10b1224bb368f9f37a2b16b612598138befd7b37eb5); https://github.com/japaric/cast.rs | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-314](tools/package/native-licences/ffmpeg-toolchain/crates--cast-0.3.0--LICENSE-MIT) |
| FFmpeg toolchain runtime: cfg-if 1.0.1 (rav1e) | 1.0.1 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/cfg-if/cfg-if-1.0.1.crate (crate archive sha256 9555578bc9e57714c812a1f84e4fc5b4d21fcb063490c624de019f7464c91268); https://github.com/rust-lang/cfg-if | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-303](tools/package/native-licences/ffmpeg-toolchain/rust-lang-backtrace-rs--LICENSE-MIT) |
| FFmpeg toolchain runtime: cfg-if 1.0.4 (toolchain) | 1.0.4 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/cfg-if/cfg-if-1.0.4.crate (crate archive sha256 9330f8b2ff13f34540b44e946ef35111825727b38d33286ef986142615121801); https://github.com/rust-lang/cfg-if | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-303](tools/package/native-licences/ffmpeg-toolchain/rust-lang-backtrace-rs--LICENSE-MIT) |
| FFmpeg toolchain runtime: cfg-if 1.0.5 (librsvg) | 1.0.5 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/cfg-if/cfg-if-1.0.5.crate (crate archive sha256 4e7648175b45a9a48536d676f68d918270699102aa8dab5496df06904c914600); https://github.com/rust-lang/cfg-if | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-303](tools/package/native-licences/ffmpeg-toolchain/rust-lang-backtrace-rs--LICENSE-MIT) |
| FFmpeg toolchain runtime: clap 4.5.40 (rav1e) | 4.5.40 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/clap/clap-4.5.40.crate (crate archive sha256 40b6887a1d8685cebccf115538db5c0efe625ccac9696ad45c409d96566e910f); https://github.com/clap-rs/clap | [licence-294](tools/package/native-licences/ffmpeg-toolchain/crates--anstream-0.6.19--LICENSE-APACHE), [licence-295](tools/package/native-licences/ffmpeg-toolchain/crates--anstream-0.6.19--LICENSE-MIT) |
| FFmpeg toolchain runtime: clap_builder 4.5.40 (rav1e) | 4.5.40 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/clap_builder/clap_builder-4.5.40.crate (crate archive sha256 e0c66c08ce9f0c698cbce5c0279d0bb6ac936d8674174fe48f736533b964f59e); https://github.com/clap-rs/clap | [licence-294](tools/package/native-licences/ffmpeg-toolchain/crates--anstream-0.6.19--LICENSE-APACHE), [licence-295](tools/package/native-licences/ffmpeg-toolchain/crates--anstream-0.6.19--LICENSE-MIT) |
| FFmpeg toolchain runtime: clap_complete 4.5.54 (rav1e) | 4.5.54 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/clap_complete/clap_complete-4.5.54.crate (crate archive sha256 aad5b1b4de04fead402672b48897030eec1f3bfe1550776322f59f6d6e6a5677); https://github.com/clap-rs/clap | [licence-294](tools/package/native-licences/ffmpeg-toolchain/crates--anstream-0.6.19--LICENSE-APACHE), [licence-295](tools/package/native-licences/ffmpeg-toolchain/crates--anstream-0.6.19--LICENSE-MIT) |
| FFmpeg toolchain runtime: clap_lex 0.7.5 (rav1e) | 0.7.5 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/clap_lex/clap_lex-0.7.5.crate (crate archive sha256 b94f61472cee1439c0b966b47e3aca9ae07e45d070759512cd390ea2bebc6675); https://github.com/clap-rs/clap | [licence-294](tools/package/native-licences/ffmpeg-toolchain/crates--anstream-0.6.19--LICENSE-APACHE), [licence-295](tools/package/native-licences/ffmpeg-toolchain/crates--anstream-0.6.19--LICENSE-MIT) |
| FFmpeg toolchain runtime: color_quant 1.1.0 (librsvg) | 1.1.0 | MIT | Redistributed in this artifact | https://static.crates.io/crates/color_quant/color_quant-1.1.0.crate (crate archive sha256 3d7b894f5411737b7867f4827955924d7c254fc9f4d91a6aad6b097804b1018b); https://github.com/image-rs/color_quant.git | [licence-315](tools/package/native-licences/ffmpeg-toolchain/crates--color_quant-1.1.0--LICENSE) |
| FFmpeg toolchain runtime: colorchoice 1.0.4 (rav1e) | 1.0.4 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/colorchoice/colorchoice-1.0.4.crate (crate archive sha256 b05b61dc5112cbb17e4b6cd61790d9845d13888356391624cbe7e41efeac1e75); https://github.com/rust-cli/anstyle.git | [licence-294](tools/package/native-licences/ffmpeg-toolchain/crates--anstream-0.6.19--LICENSE-APACHE), [licence-295](tools/package/native-licences/ffmpeg-toolchain/crates--anstream-0.6.19--LICENSE-MIT) |
| FFmpeg toolchain runtime: compiler_builtins 0.1.160 (toolchain) | 0.1.160 | MIT AND Apache-2.0 WITH LLVM-exception AND (MIT OR Apache-2.0) | Redistributed in this artifact | https://github.com/rust-lang/rust @ 58cf8f9c35b355199727627d07ae34a4e2846d67; https://github.com/rust-lang/rust/tree/58cf8f9c35b355199727627d07ae34a4e2846d67/library/compiler-builtins/compiler-builtins | [licence-316](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--compiler-builtins--LICENSE.txt) |
| FFmpeg toolchain runtime: console 0.15.11 (rav1e) | 0.15.11 | MIT | Redistributed in this artifact | https://static.crates.io/crates/console/console-0.15.11.crate (crate archive sha256 054ccb5b10f9f2cbf51eb355ca1d05c2d279ce1804688d0db74b4733a5aeafd8); https://github.com/console-rs/console | [licence-317](tools/package/native-licences/ffmpeg-toolchain/crates--console-0.15.11--LICENSE) |
| FFmpeg toolchain runtime: core2 0.4.0 (rav1e) | 0.4.0 | Apache-2.0 OR MIT | Redistributed in this artifact | https://static.crates.io/crates/core2/core2-0.4.0.crate (crate archive sha256 b49ba7ef1ad6107f8824dbe97de947cbaac53c44e7f9756a1fba0d37c1eec505); https://github.com/bbqsrc/core2 | [licence-294](tools/package/native-licences/ffmpeg-toolchain/crates--anstream-0.6.19--LICENSE-APACHE), [licence-318](tools/package/native-licences/ffmpeg-toolchain/crates--core2-0.4.0--LICENSE-MIT) |
| FFmpeg toolchain runtime: core_detect 1.0.0 (librsvg) | 1.0.0 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/core_detect/core_detect-1.0.0.crate (crate archive sha256 7f8f80099a98041a3d1622845c271458a2d73e688351bf3cb999266764b81d48); https://github.com/thomcc/core_detect | [licence-319](tools/package/native-licences/ffmpeg-toolchain/crates--core_detect-1.0.0--LICENSE-APACHE), [licence-320](tools/package/native-licences/ffmpeg-toolchain/crates--core_detect-1.0.0--LICENSE-MIT) |
| FFmpeg toolchain runtime: crc32fast 1.5.3 (librsvg) | 1.5.3 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/crc32fast/crc32fast-1.5.3.crate (crate archive sha256 0ba106e844045ddc02c20768ac4b0b7cb45f2cc2ecbd833ac9f5dacb183c2055); https://github.com/srijs/rust-crc32fast | [licence-294](tools/package/native-licences/ffmpeg-toolchain/crates--anstream-0.6.19--LICENSE-APACHE), [licence-321](tools/package/native-licences/ffmpeg-toolchain/crates--crc32fast-1.5.3--LICENSE-MIT) |
| FFmpeg toolchain runtime: crossbeam 0.8.4 (rav1e) | 0.8.4 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/crossbeam/crossbeam-0.8.4.crate (crate archive sha256 1137cd7e7fc0fb5d3c5a8678be38ec56e819125d8d7907411fe24ccb943faca8); https://github.com/crossbeam-rs/crossbeam | [licence-322](tools/package/native-licences/ffmpeg-toolchain/crates--crossbeam-0.8.4--LICENSE-APACHE), [licence-323](tools/package/native-licences/ffmpeg-toolchain/crates--crossbeam-0.8.4--LICENSE-MIT) |
| FFmpeg toolchain runtime: crossbeam-channel 0.5.15 (rav1e) | 0.5.15 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/crossbeam-channel/crossbeam-channel-0.5.15.crate (crate archive sha256 82b8f8f868b36967f9606790d1903570de9ceaf870a7bf9fbbd3016d636a2cb2); https://github.com/crossbeam-rs/crossbeam | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-323](tools/package/native-licences/ffmpeg-toolchain/crates--crossbeam-0.8.4--LICENSE-MIT), [licence-324](tools/package/native-licences/ffmpeg-toolchain/crates--crossbeam-channel-0.5.15--LICENSE-THIRD-PARTY) |
| FFmpeg toolchain runtime: crossbeam-deque 0.8.6 (rav1e) | 0.8.6 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/crossbeam-deque/crossbeam-deque-0.8.6.crate (crate archive sha256 9dd111b7b7f7d55b72c0a6ae361660ee5853c9af73f70c3c2ef6858b950e2e51); https://github.com/crossbeam-rs/crossbeam | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-323](tools/package/native-licences/ffmpeg-toolchain/crates--crossbeam-0.8.4--LICENSE-MIT) |
| FFmpeg toolchain runtime: crossbeam-deque 0.8.8 (librsvg) | 0.8.8 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/crossbeam-deque/crossbeam-deque-0.8.8.crate (crate archive sha256 622f3fc73690be383c7214310406f28a90e6edeadc3cea882f9d71e495b9711a); https://github.com/crossbeam-rs/crossbeam | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-323](tools/package/native-licences/ffmpeg-toolchain/crates--crossbeam-0.8.4--LICENSE-MIT) |
| FFmpeg toolchain runtime: crossbeam-epoch 0.9.18 (rav1e) | 0.9.18 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/crossbeam-epoch/crossbeam-epoch-0.9.18.crate (crate archive sha256 5b82ac4a3c2ca9c3460964f020e1402edd5753411d7737aa39c3714ad1b5420e); https://github.com/crossbeam-rs/crossbeam | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-323](tools/package/native-licences/ffmpeg-toolchain/crates--crossbeam-0.8.4--LICENSE-MIT) |
| FFmpeg toolchain runtime: crossbeam-epoch 0.9.21 (librsvg) | 0.9.21 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/crossbeam-epoch/crossbeam-epoch-0.9.21.crate (crate archive sha256 dc74980687109a3b14c72fd458107bf0baa1da1a1a805e178d15501ba9b86d9d); https://github.com/crossbeam-rs/crossbeam | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-323](tools/package/native-licences/ffmpeg-toolchain/crates--crossbeam-0.8.4--LICENSE-MIT) |
| FFmpeg toolchain runtime: crossbeam-queue 0.3.12 (rav1e) | 0.3.12 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/crossbeam-queue/crossbeam-queue-0.3.12.crate (crate archive sha256 0f58bbc28f91df819d0aa2a2c00cd19754769c2fad90579b3592b1c9ba7a3115); https://github.com/crossbeam-rs/crossbeam | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-323](tools/package/native-licences/ffmpeg-toolchain/crates--crossbeam-0.8.4--LICENSE-MIT) |
| FFmpeg toolchain runtime: crossbeam-utils 0.8.21 (rav1e) | 0.8.21 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/crossbeam-utils/crossbeam-utils-0.8.21.crate (crate archive sha256 d0a5c400df2834b80a4c3327b3aad3a4c4cd4de0629063962b03235697506a28); https://github.com/crossbeam-rs/crossbeam | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-323](tools/package/native-licences/ffmpeg-toolchain/crates--crossbeam-0.8.4--LICENSE-MIT) |
| FFmpeg toolchain runtime: crossbeam-utils 0.8.23 (librsvg) | 0.8.23 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/crossbeam-utils/crossbeam-utils-0.8.23.crate (crate archive sha256 a31eee39dddec8330830986fcd7625edb5a24ec90ea038215273bbc3adb08ac6); https://github.com/crossbeam-rs/crossbeam | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-323](tools/package/native-licences/ffmpeg-toolchain/crates--crossbeam-0.8.4--LICENSE-MIT) |
| FFmpeg toolchain runtime: cssparser 0.37.0 (librsvg) | 0.37.0 | MPL-2.0 | Redistributed in this artifact | https://static.crates.io/crates/cssparser/cssparser-0.37.0.crate (crate archive sha256 8c9cdaae01d5ed7882b04d795e7f752f46ff52d2fa3b50a20d28c464510bba98); https://github.com/servo/rust-cssparser | [licence-255](tools/package/native-licences/ffmpeg-toolchain/crates--cssparser-0.37.0--LICENSE) |
| FFmpeg toolchain runtime: cssparser-color 0.5.0 (librsvg) | 0.5.0 | MPL-2.0 | Redistributed in this artifact | https://static.crates.io/crates/cssparser-color/cssparser-color-0.5.0.crate (crate archive sha256 bbaa233e1dcd9c13a5d3e3a8a2c0f5a727bac380398345dbcb31db4597edc86b); https://github.com/servo/rust-cssparser | [licence-255](tools/package/native-licences/ffmpeg-toolchain/crates--cssparser-0.37.0--LICENSE) |
| FFmpeg toolchain runtime: data-url 0.3.2 (librsvg) | 0.3.2 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/data-url/data-url-0.3.2.crate (crate archive sha256 be1e0bca6c3637f992fc1cc7cbc52a78c1ef6db076dbf1059c4323d6a2048376); https://github.com/servo/rust-url | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-325](tools/package/native-licences/ffmpeg-toolchain/crates--data-url-0.3.2--LICENSE-MIT) |
| FFmpeg toolchain runtime: dav1d 0.11.1 (librsvg) | 0.11.1 | MIT | Redistributed in this artifact | https://static.crates.io/crates/dav1d/dav1d-0.11.1.crate (crate archive sha256 3ee89cb860616069c67520dcd66cacdb900b57c799f634a0eb6d91f6e2a82b61); https://github.com/rust-av/dav1d-rs | [licence-326](tools/package/native-licences/ffmpeg-toolchain/crates--dav1d-0.11.1--LICENSE) |
| FFmpeg toolchain runtime: dav1d-sys 0.8.3 (librsvg) | 0.8.3 | MIT | Redistributed in this artifact | https://static.crates.io/crates/dav1d-sys/dav1d-sys-0.8.3.crate (crate archive sha256 c3c91aea6668645415331133ed6f8ddf0e7f40160cd97a12d59e68716a58704b); https://github.com/rust-av/dav1d-rs | [licence-326](tools/package/native-licences/ffmpeg-toolchain/crates--dav1d-0.11.1--LICENSE) |
| FFmpeg toolchain runtime: derive_more 2.1.1 (librsvg) | 2.1.1 | MIT | Redistributed in this artifact | https://static.crates.io/crates/derive_more/derive_more-2.1.1.crate (crate archive sha256 d751e9e49156b02b44f9c1815bcb94b984cdcc4396ecc32521c739452808b134); https://github.com/JelteF/derive_more | [licence-327](tools/package/native-licences/ffmpeg-toolchain/crates--derive_more-2.1.1--LICENSE) |
| FFmpeg toolchain runtime: dtoa 1.0.11 (librsvg) | 1.0.11 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/dtoa/dtoa-1.0.11.crate (crate archive sha256 4c3cf4824e2d5f025c7b531afcb2325364084a16806f6d47fbc1f5fbd9960590); https://github.com/dtolnay/dtoa | [licence-296](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--LICENSE-APACHE), [licence-287](tools/package/native-licences/ffmpeg-toolchain/crates--adler2-2.0.1--LICENSE-MIT) |
| FFmpeg toolchain runtime: dtoa-short 0.3.5 (librsvg) | 0.3.5 | MPL-2.0 | Redistributed in this artifact | https://static.crates.io/crates/dtoa-short/dtoa-short-0.3.5.crate (crate archive sha256 cd1511a7b6a56299bd043a9c167a6d2bfb37bf84a6dfceaba651168adfb43c87); https://github.com/upsuper/dtoa-short | [licence-149](tools/package/native-licences/ffmpeg-toolchain/crates--dtoa-short-0.3.5--LICENSE) |
| FFmpeg toolchain runtime: either 1.15.0 (rav1e) | 1.15.0 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/either/either-1.15.0.crate (crate archive sha256 48c757948c5ede0e46177b7add2e67155f70e33c07fea8284df6576da70b3719); https://github.com/rayon-rs/either | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-328](tools/package/native-licences/ffmpeg-toolchain/crates--either-1.15.0--LICENSE-MIT) |
| FFmpeg toolchain runtime: either 1.19.0 (librsvg) | 1.19.0 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/either/either-1.19.0.crate (crate archive sha256 0e9c71c2167ca323c882b99918929403426e2373ea17242ff5653e0d5e1058be); https://github.com/rayon-rs/either | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-328](tools/package/native-licences/ffmpeg-toolchain/crates--either-1.15.0--LICENSE-MIT) |
| FFmpeg toolchain runtime: encode_unicode 1.0.0 (rav1e) | 1.0.0 | Apache-2.0 OR MIT | Redistributed in this artifact | https://static.crates.io/crates/encode_unicode/encode_unicode-1.0.0.crate (crate archive sha256 34aa73646ffb006b8f5147f3dc182bd4bcb190227ce861fc4a4844bf8e3cb2c0); https://github.com/tormol/encode_unicode | [licence-125](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--portable-simd--LICENSE-APACHE), [licence-329](tools/package/native-licences/ffmpeg-toolchain/crates--encode_unicode-1.0.0--LICENSE-MIT) |
| FFmpeg toolchain runtime: encoding_rs 0.8.42 (librsvg) | 0.8.42 | (Apache-2.0 OR MIT) AND BSD-3-Clause | Redistributed in this artifact | https://static.crates.io/crates/encoding_rs/encoding_rs-0.8.42.crate (crate archive sha256 8e985e0451871ad22fb8d2b6b076e2028a502a0d3950998c2c5c0a4f9b5d9679); https://github.com/hsivonen/encoding_rs | [licence-330](tools/package/native-licences/ffmpeg-toolchain/crates--encoding_rs-0.8.42--COPYRIGHT), [licence-125](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--portable-simd--LICENSE-APACHE), [licence-331](tools/package/native-licences/ffmpeg-toolchain/crates--encoding_rs-0.8.42--LICENSE-MIT), [licence-332](tools/package/native-licences/ffmpeg-toolchain/crates--encoding_rs-0.8.42--LICENSE-WHATWG) |
| FFmpeg toolchain runtime: equator 0.4.2 (rav1e) | 0.4.2 | MIT | Redistributed in this artifact | https://static.crates.io/crates/equator/equator-0.4.2.crate (crate archive sha256 4711b213838dfee0117e3be6ac926007d7f433d7bbe33595975d4190cb07e6fc); https://github.com/sarah-ek/equator/ | [licence-333](tools/package/native-licences/ffmpeg-toolchain/crates--equator-0.4.2--LICENSE) |
| FFmpeg toolchain runtime: fallible_collections 0.4.9 (librsvg) | 0.4.9 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/fallible_collections/fallible_collections-0.4.9.crate (crate archive sha256 a88c69768c0a15262df21899142bc6df9b9b823546d4b4b9a7bc2d6c448ec6fd); https://github.com/vcombey/fallible_collections.git | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-334](tools/package/native-licences/ffmpeg-toolchain/crates--rayon-1.10.0--LICENSE-MIT) |
| FFmpeg toolchain runtime: fdeflate 0.3.7 (librsvg) | 0.3.7 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/fdeflate/fdeflate-0.3.7.crate (crate archive sha256 1e6853b52649d4ac5c0bd02320cddc5ba956bdb407c4b75a2c6b75bf51500f8c); https://github.com/image-rs/fdeflate | [licence-336](tools/package/native-licences/ffmpeg-toolchain/crates--miniz_oxide-0.9.1--LICENSE-APACHE.md), [licence-335](tools/package/native-licences/ffmpeg-toolchain/crates--fdeflate-0.3.7--LICENSE-MIT) |
| FFmpeg toolchain runtime: fern 0.7.1 (rav1e) | 0.7.1 | MIT | Redistributed in this artifact | https://static.crates.io/crates/fern/fern-0.7.1.crate (crate archive sha256 4316185f709b23713e41e3195f90edef7fb00c3ed4adc79769cf09cc762a3b29); https://github.com/daboross/fern | [licence-337](tools/package/native-licences/ffmpeg-toolchain/crates--fern-0.7.1--LICENSE) |
| FFmpeg toolchain runtime: flate2 1.1.10 (librsvg) | 1.1.10 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/flate2/flate2-1.1.10.crate (crate archive sha256 6e634e2e0ebac1ee034020da1ca582e17ffe4e0f5e985823721e168928136dcb); https://github.com/rust-lang/flate2-rs | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-338](tools/package/native-licences/ffmpeg-toolchain/crates--flate2-1.1.10--LICENSE-MIT) |
| FFmpeg toolchain runtime: float-cmp 0.10.0 (librsvg) | 0.10.0 | MIT | Redistributed in this artifact | https://static.crates.io/crates/float-cmp/float-cmp-0.10.0.crate (crate archive sha256 b09cf3155332e944990140d967ff5eceb70df778b34f77d8075db46e4704e6d8); https://github.com/mikedilger/float-cmp | [licence-339](tools/package/native-licences/ffmpeg-toolchain/crates--float-cmp-0.10.0--LICENSE) |
| FFmpeg toolchain runtime: form_urlencoded 1.2.2 (librsvg) | 1.2.2 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/form_urlencoded/form_urlencoded-1.2.2.crate (crate archive sha256 cb4cb245038516f5f85277875cdaa4f7d2c9a0fa0468de06ed190163b1581fcf); https://github.com/servo/rust-url | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-340](tools/package/native-licences/ffmpeg-toolchain/crates--form_urlencoded-1.2.2--LICENSE-MIT) |
| FFmpeg toolchain runtime: futures-channel 0.3.34 (librsvg) | 0.3.34 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/futures-channel/futures-channel-0.3.34.crate (crate archive sha256 b1f9e3d69d39e4862ffed03ed071a76f9a13ba1d9109d355b0f0aa6b15e393c4); https://github.com/rust-lang/futures-rs | [licence-341](tools/package/native-licences/ffmpeg-toolchain/crates--futures-channel-0.3.34--LICENSE-APACHE), [licence-342](tools/package/native-licences/ffmpeg-toolchain/crates--futures-channel-0.3.34--LICENSE-MIT) |
| FFmpeg toolchain runtime: futures-core 0.3.34 (librsvg) | 0.3.34 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/futures-core/futures-core-0.3.34.crate (crate archive sha256 92d699e522242e69e3003b94ecc1f960f3a5e015aa7c5d7486e65ad01dd94f5e); https://github.com/rust-lang/futures-rs | [licence-341](tools/package/native-licences/ffmpeg-toolchain/crates--futures-channel-0.3.34--LICENSE-APACHE), [licence-342](tools/package/native-licences/ffmpeg-toolchain/crates--futures-channel-0.3.34--LICENSE-MIT) |
| FFmpeg toolchain runtime: futures-executor 0.3.34 (librsvg) | 0.3.34 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/futures-executor/futures-executor-0.3.34.crate (crate archive sha256 031b47cf1a3c6cc8bc2fc76cd437f521619387907d469316e7c0bc278f1f5432); https://github.com/rust-lang/futures-rs | [licence-341](tools/package/native-licences/ffmpeg-toolchain/crates--futures-channel-0.3.34--LICENSE-APACHE), [licence-342](tools/package/native-licences/ffmpeg-toolchain/crates--futures-channel-0.3.34--LICENSE-MIT) |
| FFmpeg toolchain runtime: futures-io 0.3.34 (librsvg) | 0.3.34 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/futures-io/futures-io-0.3.34.crate (crate archive sha256 53c0fa8157de1303bfffdaa1cc2a673bfffb60102f76b0ef4441659124373fed); https://github.com/rust-lang/futures-rs | [licence-341](tools/package/native-licences/ffmpeg-toolchain/crates--futures-channel-0.3.34--LICENSE-APACHE), [licence-342](tools/package/native-licences/ffmpeg-toolchain/crates--futures-channel-0.3.34--LICENSE-MIT) |
| FFmpeg toolchain runtime: futures-task 0.3.34 (librsvg) | 0.3.34 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/futures-task/futures-task-0.3.34.crate (crate archive sha256 cd417de3d1d015fc3bfd2b1ea46dfc7bab72ef86f1cc7cc9c78e728b34a6d1fd); https://github.com/rust-lang/futures-rs | [licence-341](tools/package/native-licences/ffmpeg-toolchain/crates--futures-channel-0.3.34--LICENSE-APACHE), [licence-342](tools/package/native-licences/ffmpeg-toolchain/crates--futures-channel-0.3.34--LICENSE-MIT) |
| FFmpeg toolchain runtime: futures-util 0.3.34 (librsvg) | 0.3.34 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/futures-util/futures-util-0.3.34.crate (crate archive sha256 0d50a92467f8ba5dd6e3ee5d4bd04d73ab2e4e1c44474a0674821dfce14b79bc); https://github.com/rust-lang/futures-rs | [licence-341](tools/package/native-licences/ffmpeg-toolchain/crates--futures-channel-0.3.34--LICENSE-APACHE), [licence-342](tools/package/native-licences/ffmpeg-toolchain/crates--futures-channel-0.3.34--LICENSE-MIT) |
| FFmpeg toolchain runtime: gif 0.14.2 (librsvg) | 0.14.2 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/gif/gif-0.14.2.crate (crate archive sha256 ee8cfcc411d9adbbaba82fb72661cc1bcca13e8bba98b364e62b2dba8f960159); https://github.com/image-rs/image-gif | [licence-319](tools/package/native-licences/ffmpeg-toolchain/crates--core_detect-1.0.0--LICENSE-APACHE), [licence-343](tools/package/native-licences/ffmpeg-toolchain/crates--gif-0.14.2--LICENSE-MIT) |
| FFmpeg toolchain runtime: gimli 0.34.0 (toolchain) | 0.34.0 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/gimli/gimli-0.34.0.crate (crate archive sha256 1033caf0b349c518623b5396bfb2cf0bddf44f0306d543a250e5743297aafd10); https://github.com/gimli-rs/gimli | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-344](tools/package/native-licences/ffmpeg-toolchain/crates--gimli-0.34.0--LICENSE-MIT) |
| FFmpeg toolchain runtime: gio 0.22.10 (librsvg) | 0.22.10 | MIT | Redistributed in this artifact | https://static.crates.io/crates/gio/gio-0.22.10.crate (crate archive sha256 4620fbafdf19dba814473e19f18e75290cb3338662f6ae35f0402affd3b2b699); https://github.com/gtk-rs/gtk-rs-core | [licence-312](tools/package/native-licences/ffmpeg-toolchain/crates--cairo-rs-0.22.9--COPYRIGHT), [licence-313](tools/package/native-licences/ffmpeg-toolchain/crates--cairo-rs-0.22.9--LICENSE) |
| FFmpeg toolchain runtime: gio-sys 0.22.9 (librsvg) | 0.22.9 | MIT | Redistributed in this artifact | https://static.crates.io/crates/gio-sys/gio-sys-0.22.9.crate (crate archive sha256 6c28739f914c15b87a9856000bed9cbd5b3a8afbca5e982d9a299e1601422cb5); https://github.com/gtk-rs/gtk-rs-core | [licence-313](tools/package/native-licences/ffmpeg-toolchain/crates--cairo-rs-0.22.9--LICENSE) |
| FFmpeg toolchain runtime: glib 0.22.10 (librsvg) | 0.22.10 | MIT | Redistributed in this artifact | https://static.crates.io/crates/glib/glib-0.22.10.crate (crate archive sha256 e4cf9e5bd8713f1990a92c422998826e0fb34824277b46bc59757373483c6694); https://github.com/gtk-rs/gtk-rs-core | [licence-312](tools/package/native-licences/ffmpeg-toolchain/crates--cairo-rs-0.22.9--COPYRIGHT), [licence-313](tools/package/native-licences/ffmpeg-toolchain/crates--cairo-rs-0.22.9--LICENSE) |
| FFmpeg toolchain runtime: glib-sys 0.22.9 (librsvg) | 0.22.9 | MIT | Redistributed in this artifact | https://static.crates.io/crates/glib-sys/glib-sys-0.22.9.crate (crate archive sha256 99b38907e67e40dec9b60f858bcada952598719cb512a13eb13d6cdcd16f8295); https://github.com/gtk-rs/gtk-rs-core | [licence-313](tools/package/native-licences/ffmpeg-toolchain/crates--cairo-rs-0.22.9--LICENSE) |
| FFmpeg toolchain runtime: gobject-sys 0.22.9 (librsvg) | 0.22.9 | MIT | Redistributed in this artifact | https://static.crates.io/crates/gobject-sys/gobject-sys-0.22.9.crate (crate archive sha256 07595c9ba696bd9819cb6a8df39f08078f3dd679508fe052dd558492c2053834); https://github.com/gtk-rs/gtk-rs-core | [licence-313](tools/package/native-licences/ffmpeg-toolchain/crates--cairo-rs-0.22.9--LICENSE) |
| FFmpeg toolchain runtime: hashbrown 0.13.2 (librsvg) | 0.13.2 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/hashbrown/hashbrown-0.13.2.crate (crate archive sha256 43a3c133739dddd0d2990f9a4bdf8eb4b21ef50e4851ca85ab661199821d510e); https://github.com/rust-lang/hashbrown | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-345](tools/package/native-licences/ffmpeg-toolchain/crates--hashbrown-0.17.1--LICENSE-MIT) |
| FFmpeg toolchain runtime: hashbrown 0.17.1 (toolchain) | 0.17.1 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/hashbrown/hashbrown-0.17.1.crate (crate archive sha256 ed5909b6e89a2db4456e54cd5f673791d7eca6732202bbf2a9cc504fe2f9b84a); https://github.com/rust-lang/hashbrown | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-345](tools/package/native-licences/ffmpeg-toolchain/crates--hashbrown-0.17.1--LICENSE-MIT) |
| FFmpeg toolchain runtime: icu_collections 2.4.0 (librsvg) | 2.4.0 | Unicode-3.0 | Redistributed in this artifact | https://static.crates.io/crates/icu_collections/icu_collections-2.4.0.crate (crate archive sha256 fe090a42a0d3140fed8c63263ed1fecc02422cb2f4bfe55cd8de2de1b8e105dd); https://github.com/unicode-org/icu4x | [licence-346](tools/package/native-licences/ffmpeg-toolchain/crates--icu_collections-2.4.0--LICENSE) |
| FFmpeg toolchain runtime: icu_locale_core 2.4.0 (librsvg) | 2.4.0 | Unicode-3.0 | Redistributed in this artifact | https://static.crates.io/crates/icu_locale_core/icu_locale_core-2.4.0.crate (crate archive sha256 25d29b57c17c6528d0dc4c2141cfa2d08200465acb537a3909c8b9b8a4a984c0); https://github.com/unicode-org/icu4x | [licence-346](tools/package/native-licences/ffmpeg-toolchain/crates--icu_collections-2.4.0--LICENSE) |
| FFmpeg toolchain runtime: icu_normalizer 2.4.0 (librsvg) | 2.4.0 | Unicode-3.0 | Redistributed in this artifact | https://static.crates.io/crates/icu_normalizer/icu_normalizer-2.4.0.crate (crate archive sha256 404a3b8c486f205c87fe7f23ab6894d84a4ad76d6e4671ae1981ba7def87c599); https://github.com/unicode-org/icu4x | [licence-346](tools/package/native-licences/ffmpeg-toolchain/crates--icu_collections-2.4.0--LICENSE) |
| FFmpeg toolchain runtime: icu_normalizer_data 2.4.0 (librsvg) | 2.4.0 | Unicode-3.0 | Redistributed in this artifact | https://static.crates.io/crates/icu_normalizer_data/icu_normalizer_data-2.4.0.crate (crate archive sha256 20f0088bfb7441f7a37fa0c9e20cb1e9cba1cac6b9ce8cd2a6dc44294f8e8cbc); https://github.com/unicode-org/icu4x | [licence-346](tools/package/native-licences/ffmpeg-toolchain/crates--icu_collections-2.4.0--LICENSE) |
| FFmpeg toolchain runtime: icu_properties 2.4.0 (librsvg) | 2.4.0 | Unicode-3.0 | Redistributed in this artifact | https://static.crates.io/crates/icu_properties/icu_properties-2.4.0.crate (crate archive sha256 2ea83d991c56158f7cf898bf86436c1dfe7c07ee82fe88951f2695c9f37a379f); https://github.com/unicode-org/icu4x | [licence-346](tools/package/native-licences/ffmpeg-toolchain/crates--icu_collections-2.4.0--LICENSE) |
| FFmpeg toolchain runtime: icu_properties_data 2.4.0 (librsvg) | 2.4.0 | Unicode-3.0 | Redistributed in this artifact | https://static.crates.io/crates/icu_properties_data/icu_properties_data-2.4.0.crate (crate archive sha256 b98f29af82d02b163fe50161388350e743bb3107cc8e8c2f7314cb505faddfcf); https://github.com/unicode-org/icu4x | [licence-346](tools/package/native-licences/ffmpeg-toolchain/crates--icu_collections-2.4.0--LICENSE) |
| FFmpeg toolchain runtime: icu_provider 2.4.0 (librsvg) | 2.4.0 | Unicode-3.0 | Redistributed in this artifact | https://static.crates.io/crates/icu_provider/icu_provider-2.4.0.crate (crate archive sha256 413099315636c588ee8f011190b329b971a09a8fae9d157e01dcae8379468514); https://github.com/unicode-org/icu4x | [licence-346](tools/package/native-licences/ffmpeg-toolchain/crates--icu_collections-2.4.0--LICENSE) |
| FFmpeg toolchain runtime: idna 1.1.0 (librsvg) | 1.1.0 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/idna/idna-1.1.0.crate (crate archive sha256 3b0875f23caa03898994f6ddc501886a45c7d3d62d04d2d90788d47be1b1e4de); https://github.com/servo/rust-url/ | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-325](tools/package/native-licences/ffmpeg-toolchain/crates--data-url-0.3.2--LICENSE-MIT) |
| FFmpeg toolchain runtime: idna_adapter 1.2.2 (librsvg) | 1.2.2 | Apache-2.0 OR MIT | Redistributed in this artifact | https://static.crates.io/crates/idna_adapter/idna_adapter-1.2.2.crate (crate archive sha256 cb68373c0d6620ef8105e855e7745e18b0d00d3bdb07fb532e434244cdb9a714); https://github.com/hsivonen/idna_adapter | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-347](tools/package/native-licences/ffmpeg-toolchain/crates--idna_adapter-1.2.2--LICENSE-MIT) |
| FFmpeg toolchain runtime: image 0.25.10 (librsvg) | 0.25.10 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/image/image-0.25.10.crate (crate archive sha256 85ab80394333c02fe689eaf900ab500fbd0c2213da414687ebf995a65d5a6104); https://github.com/image-rs/image | [licence-336](tools/package/native-licences/ffmpeg-toolchain/crates--miniz_oxide-0.9.1--LICENSE-APACHE.md), [licence-335](tools/package/native-licences/ffmpeg-toolchain/crates--fdeflate-0.3.7--LICENSE-MIT) |
| FFmpeg toolchain runtime: image-webp 0.2.4 (librsvg) | 0.2.4 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/image-webp/image-webp-0.2.4.crate (crate archive sha256 525e9ff3e1a4be2fbea1fdf0e98686a6d98b4d8f937e1bf7402245af1909e8c3); https://github.com/image-rs/image-webp | [licence-336](tools/package/native-licences/ffmpeg-toolchain/crates--miniz_oxide-0.9.1--LICENSE-APACHE.md), [licence-335](tools/package/native-licences/ffmpeg-toolchain/crates--fdeflate-0.3.7--LICENSE-MIT) |
| FFmpeg toolchain runtime: is_terminal_polyfill 1.70.1 (rav1e) | 1.70.1 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/is_terminal_polyfill/is_terminal_polyfill-1.70.1.crate (crate archive sha256 7943c866cc5cd64cbc25b2e01621d07fa8eb2a1a23160ee81ce38704e97b8ecf); https://github.com/polyfill-rs/is_terminal_polyfill | [licence-294](tools/package/native-licences/ffmpeg-toolchain/crates--anstream-0.6.19--LICENSE-APACHE), [licence-295](tools/package/native-licences/ffmpeg-toolchain/crates--anstream-0.6.19--LICENSE-MIT) |
| FFmpeg toolchain runtime: itertools 0.10.5 (rav1e) | 0.10.5 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/itertools/itertools-0.10.5.crate (crate archive sha256 b0fd2260e829bddf4cb6ea802289de2f86d6a7a690192fbe91b3f46e0f2c8473); https://github.com/rust-itertools/itertools | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-328](tools/package/native-licences/ffmpeg-toolchain/crates--either-1.15.0--LICENSE-MIT) |
| FFmpeg toolchain runtime: itertools 0.14.0 (rav1e) | 0.14.0 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/itertools/itertools-0.14.0.crate (crate archive sha256 2b192c782037fadd9cfa75548310488aabdbf3d2da73885b31bd0abd03351285); https://github.com/rust-itertools/itertools | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-328](tools/package/native-licences/ffmpeg-toolchain/crates--either-1.15.0--LICENSE-MIT) |
| FFmpeg toolchain runtime: itertools 0.15.0 (librsvg) | 0.15.0 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/itertools/itertools-0.15.0.crate (crate archive sha256 8b4baf93f58d4425749ca49a51c50ebab072c5df6994d08fed93541c331481dc); https://github.com/rust-itertools/itertools | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-328](tools/package/native-licences/ffmpeg-toolchain/crates--either-1.15.0--LICENSE-MIT) |
| FFmpeg toolchain runtime: itoa 1.0.18 (librsvg) | 1.0.18 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/itoa/itoa-1.0.18.crate (crate archive sha256 8f42a60cbdf9a97f5d2305f08a87dc4e09308d1276d28c869c684d7777685682); https://github.com/dtolnay/itoa | [licence-296](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--LICENSE-APACHE), [licence-287](tools/package/native-licences/ffmpeg-toolchain/crates--adler2-2.0.1--LICENSE-MIT) |
| FFmpeg toolchain runtime: lab 0.11.0 (rav1e) | 0.11.0 | MIT | Redistributed in this artifact | https://static.crates.io/crates/lab/lab-0.11.0.crate (crate archive sha256 bf36173d4167ed999940f804952e6b08197cae5ad5d572eb4db150ce8ad5d58f); https://github.com/TooManyBees/lab | [licence-348](tools/package/native-licences/ffmpeg-toolchain/crates--lab-0.11.0--LICENSE) |
| FFmpeg toolchain runtime: language-tags 0.3.2 (librsvg) | 0.3.2 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/language-tags/language-tags-0.3.2.crate (crate archive sha256 d4345964bb142484797b161f473a503a434de77149dd8c7427788c6e13379388); https://github.com/pyfisch/rust-language-tags | [licence-349](tools/package/native-licences/ffmpeg-toolchain/crates--language-tags-0.3.2--LICENSE) |
| FFmpeg toolchain runtime: lazy_static 1.5.1 (librsvg) | 1.5.1 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/lazy_static/lazy_static-1.5.1.crate (crate archive sha256 20870f649af7073d53e38067b2a84312175d56ea15217e1b15bc83506ec50afb); https://github.com/rust-lang-nursery/lazy-static.rs | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-287](tools/package/native-licences/ffmpeg-toolchain/crates--adler2-2.0.1--LICENSE-MIT) |
| FFmpeg toolchain runtime: libc 0.2.172 (rav1e) | 0.2.172 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/libc/libc-0.2.172.crate (crate archive sha256 d750af042f7ef4f724306de029d18836c26c1765a54a6a3f094cbd23a7267ffa); https://github.com/rust-lang/libc | [licence-296](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--LICENSE-APACHE), [licence-350](tools/package/native-licences/ffmpeg-toolchain/crates--libc-0.2.172--LICENSE-MIT) |
| FFmpeg toolchain runtime: libc 0.2.189 (toolchain) | 0.2.189 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/libc/libc-0.2.189.crate (crate archive sha256 3eaf3ede3fee6db1a4c2ee091bf8a8b4dccdc6d17f656fb07896ee72867612f2); https://github.com/rust-lang/libc | [licence-296](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--LICENSE-APACHE), [licence-351](tools/package/native-licences/ffmpeg-toolchain/crates--libc-0.2.189--LICENSE-MIT) |
| FFmpeg toolchain runtime: libc 0.2.191 (librsvg) | 0.2.191 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/libc/libc-0.2.191.crate (crate archive sha256 65cd87c9a6d60536580b316ad985726104730a5151c99845f2490428ef91240a); https://github.com/rust-lang/libc | [licence-296](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--LICENSE-APACHE), [licence-351](tools/package/native-licences/ffmpeg-toolchain/crates--libc-0.2.189--LICENSE-MIT) |
| FFmpeg toolchain runtime: libgcc 16.2.0 (toolchain) | 16.2.0 | GPL-3.0-or-later WITH GCC-exception-3.1 | Redistributed in this artifact | https://github.com/gcc-mirror/gcc @ 78d4ac73dd391005b895a6148cd9831e28e1208b; https://github.com/gcc-mirror/gcc/tree/78d4ac73dd391005b895a6148cd9831e28e1208b/libgcc | [licence-24](tools/package/native-licences/ffmpeg-toolchain/gcc--COPYING3), [licence-352](tools/package/native-licences/ffmpeg-toolchain/gcc--COPYING.RUNTIME) |
| FFmpeg toolchain runtime: libgomp 16.2.0 (toolchain) | 16.2.0 | GPL-3.0-or-later WITH GCC-exception-3.1 | Redistributed in this artifact | https://github.com/gcc-mirror/gcc @ 78d4ac73dd391005b895a6148cd9831e28e1208b; https://github.com/gcc-mirror/gcc/tree/78d4ac73dd391005b895a6148cd9831e28e1208b/libgomp | [licence-24](tools/package/native-licences/ffmpeg-toolchain/gcc--COPYING3), [licence-352](tools/package/native-licences/ffmpeg-toolchain/gcc--COPYING.RUNTIME) |
| FFmpeg toolchain runtime: libm 0.2.16 (toolchain) | 0.2.16 | MIT | Redistributed in this artifact | https://github.com/rust-lang/rust @ 58cf8f9c35b355199727627d07ae34a4e2846d67; https://github.com/rust-lang/rust/tree/58cf8f9c35b355199727627d07ae34a4e2846d67/library/compiler-builtins/libm | [licence-353](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--compiler-builtins--libm--LICENSE.txt) |
| FFmpeg toolchain runtime: libstdc++ (fast_float) 16.2.0 (toolchain) | 16.2.0 | MIT OR Apache-2.0 | Redistributed in this artifact | https://github.com/gcc-mirror/gcc @ 78d4ac73dd391005b895a6148cd9831e28e1208b; https://github.com/gcc-mirror/gcc/tree/78d4ac73dd391005b895a6148cd9831e28e1208b/libstdc++-v3/src/c++17/fast_float | [licence-354](tools/package/native-licences/ffmpeg-toolchain/gcc--libstdc++-v3--src--c++17--fast_float--fast_float.h), [licence-355](tools/package/native-licences/ffmpeg-toolchain/gcc--libstdc++-v3--src--c++17--fast_float--fast_float.h-L1-40.txt) |
| FFmpeg toolchain runtime: libstdc++ (Ryu) 16.2.0 (toolchain) | 16.2.0 | Apache-2.0 OR BSL-1.0 | Redistributed in this artifact | https://github.com/gcc-mirror/gcc @ 78d4ac73dd391005b895a6148cd9831e28e1208b; https://github.com/gcc-mirror/gcc/tree/78d4ac73dd391005b895a6148cd9831e28e1208b/libstdc++-v3/src/c++17/ryu | [licence-356](tools/package/native-licences/ffmpeg-toolchain/gcc--libstdc++-v3--src--c++17--ryu--d2s.c), [licence-357](tools/package/native-licences/ffmpeg-toolchain/gcc--libstdc++-v3--src--c++17--ryu--d2s.c-L1-16.txt), [licence-55](tools/package/native-licences/ffmpeg-toolchain/spdx--text--Apache-2.0.txt) |
| FFmpeg toolchain runtime: libstdc++ 16.2.0 (toolchain) | 16.2.0 | GPL-3.0-or-later WITH GCC-exception-3.1 | Redistributed in this artifact | https://github.com/gcc-mirror/gcc @ 78d4ac73dd391005b895a6148cd9831e28e1208b; https://github.com/gcc-mirror/gcc/tree/78d4ac73dd391005b895a6148cd9831e28e1208b/libstdc++-v3 | [licence-24](tools/package/native-licences/ffmpeg-toolchain/gcc--COPYING3), [licence-352](tools/package/native-licences/ffmpeg-toolchain/gcc--COPYING.RUNTIME), [licence-358](tools/package/native-licences/ffmpeg-toolchain/gcc--libstdc++-v3--include--bits--stl_algo.h-L27-36.txt), [licence-359](tools/package/native-licences/ffmpeg-toolchain/gcc--libstdc++-v3--include--bits--stl_algo.h-L39-48.txt), [licence-365](tools/package/native-licences/ffmpeg-toolchain/gcc--libstdc++-v3--include--bits--stl_vector.h-L39-48.txt), [licence-362](tools/package/native-licences/ffmpeg-toolchain/gcc--libstdc++-v3--include--bits--stl_construct.h-L39-48.txt), [licence-364](tools/package/native-licences/ffmpeg-toolchain/gcc--libstdc++-v3--include--bits--stl_relops.h-L38-47.txt), [licence-360](tools/package/native-licences/ffmpeg-toolchain/gcc--libstdc++-v3--include--bits--stl_algobase.h-L39-48.txt), [licence-361](tools/package/native-licences/ffmpeg-toolchain/gcc--libstdc++-v3--include--bits--stl_bvector.h-L39-48.txt), [licence-363](tools/package/native-licences/ffmpeg-toolchain/gcc--libstdc++-v3--include--bits--stl_deque.h-L39-48.txt) |
| FFmpeg toolchain runtime: litemap 0.8.3 (librsvg) | 0.8.3 | Unicode-3.0 | Redistributed in this artifact | https://static.crates.io/crates/litemap/litemap-0.8.3.crate (crate archive sha256 47d9d19d1d6efa0109d2f65ff4c85cddd50bd572e5a00127ab10987290bcefae); https://github.com/unicode-org/icu4x | [licence-346](tools/package/native-licences/ffmpeg-toolchain/crates--icu_collections-2.4.0--LICENSE) |
| FFmpeg toolchain runtime: locale_config 0.3.0 (librsvg) | 0.3.0 | MIT | Redistributed in this artifact | https://static.crates.io/crates/locale_config/locale_config-0.3.0.crate (crate archive sha256 08d2c35b16f4483f6c26f0e4e9550717a2f6575bcd6f12a53ff0c490a94a6934); https://github.com/rust-locale/locale_config/ | [licence-366](tools/package/native-licences/ffmpeg-toolchain/crates--locale_config-0.3.0--LICENSE) |
| FFmpeg toolchain runtime: lock_api 0.4.14 (librsvg) | 0.4.14 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/lock_api/lock_api-0.4.14.crate (crate archive sha256 224399e74b87b5f3557511d98dff8b14089b3dadafcab6bb93eab67d3aace965); https://github.com/Amanieu/parking_lot | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-367](tools/package/native-licences/ffmpeg-toolchain/crates--lock_api-0.4.14--LICENSE-MIT) |
| FFmpeg toolchain runtime: log 0.4.34 (librsvg) | 0.4.34 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/log/log-0.4.34.crate (crate archive sha256 f9f8bd3e56ce4dfc153cf470fffbfa98c7620958b312ca5c3a4b8d5181fd13c6); https://github.com/rust-lang/log | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-304](tools/package/native-licences/ffmpeg-toolchain/crates--log-0.4.34--LICENSE-MIT) |
| FFmpeg toolchain runtime: log 0.4.34 (rav1e) | 0.4.34 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/log/log-0.4.34.crate (crate archive sha256 f9f8bd3e56ce4dfc153cf470fffbfa98c7620958b312ca5c3a4b8d5181fd13c6); https://github.com/rust-lang/log | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-304](tools/package/native-licences/ffmpeg-toolchain/crates--log-0.4.34--LICENSE-MIT) |
| FFmpeg toolchain runtime: markup5ever 0.39.0 (librsvg) | 0.39.0 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/markup5ever/markup5ever-0.39.0.crate (crate archive sha256 7122d987ec5f704ee56f6e5b41a7d93722e9aae27ae07cafa4036c4d3f9757de); https://github.com/servo/html5ever | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-368](tools/package/native-licences/ffmpeg-toolchain/crates--markup5ever-0.39.0--LICENSE-MIT) |
| FFmpeg toolchain runtime: matrixmultiply 0.3.11 (librsvg) | 0.3.11 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/matrixmultiply/matrixmultiply-0.3.11.crate (crate archive sha256 3f607c237553f086e7043417a51df26b2eb899d3caff94e6a67592ff992fedc7); https://github.com/bluss/matrixmultiply/ | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-369](tools/package/native-licences/ffmpeg-toolchain/crates--matrixmultiply-0.3.11--LICENSE-MIT) |
| FFmpeg toolchain runtime: maybe-rayon 0.1.1 (rav1e) | 0.1.1 | MIT | Redistributed in this artifact | https://static.crates.io/crates/maybe-rayon/maybe-rayon-0.1.1.crate (crate archive sha256 8ea1f30cedd69f0a2954655f7188c6a834246d2bcf1e315e2ac40c4b24dc9519); https://github.com/shssoichiro/maybe-rayon | [licence-370](tools/package/native-licences/ffmpeg-toolchain/crates--maybe-rayon-0.1.1--LICENSE) |
| FFmpeg toolchain runtime: memchr 2.7.5 (rav1e) | 2.7.5 | Unlicense OR MIT | Redistributed in this artifact | https://static.crates.io/crates/memchr/memchr-2.7.5.crate (crate archive sha256 32a282da65faaf38286cf3be983213fcf1d2e2a58700e808f83f4ea9a4804bc0); https://github.com/BurntSushi/memchr | [licence-289](tools/package/native-licences/ffmpeg-toolchain/crates--memchr-2.8.3--COPYING), [licence-290](tools/package/native-licences/ffmpeg-toolchain/crates--memchr-2.8.3--LICENSE-MIT), [licence-291](tools/package/native-licences/ffmpeg-toolchain/crates--memchr-2.8.3--UNLICENSE) |
| FFmpeg toolchain runtime: memchr 2.8.3 (librsvg) | 2.8.3 | Unlicense OR MIT | Redistributed in this artifact | https://static.crates.io/crates/memchr/memchr-2.8.3.crate (crate archive sha256 cf8baf1c55e62ffcace7a9f06f4bd9cd3f0c4beb022d3b367256b91b87513d98); https://github.com/BurntSushi/memchr | [licence-289](tools/package/native-licences/ffmpeg-toolchain/crates--memchr-2.8.3--COPYING), [licence-290](tools/package/native-licences/ffmpeg-toolchain/crates--memchr-2.8.3--LICENSE-MIT), [licence-291](tools/package/native-licences/ffmpeg-toolchain/crates--memchr-2.8.3--UNLICENSE) |
| FFmpeg toolchain runtime: memchr 2.8.3 (toolchain) | 2.8.3 | Unlicense OR MIT | Redistributed in this artifact | https://static.crates.io/crates/memchr/memchr-2.8.3.crate (crate archive sha256 cf8baf1c55e62ffcace7a9f06f4bd9cd3f0c4beb022d3b367256b91b87513d98); https://github.com/BurntSushi/memchr | [licence-289](tools/package/native-licences/ffmpeg-toolchain/crates--memchr-2.8.3--COPYING), [licence-290](tools/package/native-licences/ffmpeg-toolchain/crates--memchr-2.8.3--LICENSE-MIT), [licence-291](tools/package/native-licences/ffmpeg-toolchain/crates--memchr-2.8.3--UNLICENSE) |
| FFmpeg toolchain runtime: minimal-lexical 0.2.1 (rav1e) | 0.2.1 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/minimal-lexical/minimal-lexical-0.2.1.crate (crate archive sha256 68354c5c6bd36d73ff3feceb05efa59b6acb7626617f4962be322a825e61f79a); https://github.com/Alexhuszagh/minimal-lexical | [licence-371](tools/package/native-licences/ffmpeg-toolchain/crates--minimal-lexical-0.2.1--LICENSE-APACHE), [licence-287](tools/package/native-licences/ffmpeg-toolchain/crates--adler2-2.0.1--LICENSE-MIT), [licence-372](tools/package/native-licences/ffmpeg-toolchain/crates--minimal-lexical-0.2.1--LICENSE.md) |
| FFmpeg toolchain runtime: miniz_oxide 0.8.9 (librsvg) | 0.8.9 | MIT OR Zlib OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/miniz_oxide/miniz_oxide-0.8.9.crate (crate archive sha256 1fa76a2c86f704bdb222d66965fb3d63269ce38518b83cb0575fca855ebb6316); https://github.com/Frommi/miniz_oxide/tree/master/miniz_oxide | [licence-373](tools/package/native-licences/ffmpeg-toolchain/crates--miniz_oxide-0.9.1--LICENSE), [licence-336](tools/package/native-licences/ffmpeg-toolchain/crates--miniz_oxide-0.9.1--LICENSE-APACHE.md), [licence-374](tools/package/native-licences/ffmpeg-toolchain/crates--miniz_oxide-0.9.1--LICENSE-MIT.md), [licence-375](tools/package/native-licences/ffmpeg-toolchain/crates--miniz_oxide-0.9.1--LICENSE-ZLIB.md) |
| FFmpeg toolchain runtime: miniz_oxide 0.9.1 (librsvg) | 0.9.1 | MIT OR Zlib OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/miniz_oxide/miniz_oxide-0.9.1.crate (crate archive sha256 b63fbc4a50860e98e7b2aa7804ded1db5cbc3aff9193adaff57a6931bf7c4b4c); https://github.com/Frommi/miniz_oxide/tree/master/miniz_oxide | [licence-373](tools/package/native-licences/ffmpeg-toolchain/crates--miniz_oxide-0.9.1--LICENSE), [licence-336](tools/package/native-licences/ffmpeg-toolchain/crates--miniz_oxide-0.9.1--LICENSE-APACHE.md), [licence-374](tools/package/native-licences/ffmpeg-toolchain/crates--miniz_oxide-0.9.1--LICENSE-MIT.md), [licence-375](tools/package/native-licences/ffmpeg-toolchain/crates--miniz_oxide-0.9.1--LICENSE-ZLIB.md) |
| FFmpeg toolchain runtime: miniz_oxide 0.9.1 (toolchain) | 0.9.1 | MIT OR Zlib OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/miniz_oxide/miniz_oxide-0.9.1.crate (crate archive sha256 b63fbc4a50860e98e7b2aa7804ded1db5cbc3aff9193adaff57a6931bf7c4b4c); https://github.com/Frommi/miniz_oxide/tree/master/miniz_oxide | [licence-373](tools/package/native-licences/ffmpeg-toolchain/crates--miniz_oxide-0.9.1--LICENSE), [licence-336](tools/package/native-licences/ffmpeg-toolchain/crates--miniz_oxide-0.9.1--LICENSE-APACHE.md), [licence-374](tools/package/native-licences/ffmpeg-toolchain/crates--miniz_oxide-0.9.1--LICENSE-MIT.md), [licence-375](tools/package/native-licences/ffmpeg-toolchain/crates--miniz_oxide-0.9.1--LICENSE-ZLIB.md) |
| FFmpeg toolchain runtime: moxcms 0.8.1 (librsvg) | 0.8.1 | BSD-3-Clause OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/moxcms/moxcms-0.8.1.crate (crate archive sha256 bb85c154ba489f01b25c0d36ae69a87e4a1c73a72631fc6c0eb6dde34a73e44b); https://github.com/awxkee/moxcms.git | [licence-376](tools/package/native-licences/ffmpeg-toolchain/crates--moxcms-0.8.1--LICENSE-APACHE.md), [licence-377](tools/package/native-licences/ffmpeg-toolchain/crates--moxcms-0.8.1--LICENSE.md) |
| FFmpeg toolchain runtime: mp4parse 0.17.0 (librsvg) | 0.17.0 | MPL-2.0 | Redistributed in this artifact | https://static.crates.io/crates/mp4parse/mp4parse-0.17.0.crate (crate archive sha256 63a35203d3c6ce92d5251c77520acb2e57108c88728695aa883f70023624c570); https://github.com/mozilla/mp4parse-rust | [licence-255](tools/package/native-licences/ffmpeg-toolchain/crates--cssparser-0.37.0--LICENSE) |
| FFmpeg toolchain runtime: nalgebra 0.35.0 (librsvg) | 0.35.0 | Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/nalgebra/nalgebra-0.35.0.crate (crate archive sha256 adc43a60c217b0c6ff46e47f26911015ad8d2e5a8be1af668c67e370d99a4346); https://github.com/dimforge/nalgebra | [licence-378](tools/package/native-licences/ffmpeg-toolchain/crates--nalgebra-0.35.0--LICENSE) |
| FFmpeg toolchain runtime: new_debug_unreachable 1.0.6 (librsvg) | 1.0.6 | MIT | Redistributed in this artifact | https://static.crates.io/crates/new_debug_unreachable/new_debug_unreachable-1.0.6.crate (crate archive sha256 650eef8c711430f1a879fdd01d4745a7deea475becfb90269c06775983bbf086); https://github.com/mbrubeck/rust-debug-unreachable | [licence-379](tools/package/native-licences/ffmpeg-toolchain/crates--new_debug_unreachable-1.0.6--LICENSE-MIT) |
| FFmpeg toolchain runtime: new_debug_unreachable 1.0.6 (rav1e) | 1.0.6 | MIT | Redistributed in this artifact | https://static.crates.io/crates/new_debug_unreachable/new_debug_unreachable-1.0.6.crate (crate archive sha256 650eef8c711430f1a879fdd01d4745a7deea475becfb90269c06775983bbf086); https://github.com/mbrubeck/rust-debug-unreachable | [licence-379](tools/package/native-licences/ffmpeg-toolchain/crates--new_debug_unreachable-1.0.6--LICENSE-MIT) |
| FFmpeg toolchain runtime: nom 7.1.3 (rav1e) | 7.1.3 | MIT | Redistributed in this artifact | https://static.crates.io/crates/nom/nom-7.1.3.crate (crate archive sha256 d273983c5a657a70a3e8f2a01329822f3b8c8172b73826411a55751e404a0a4a); https://github.com/Geal/nom | [licence-380](tools/package/native-licences/ffmpeg-toolchain/crates--nom-7.1.3--LICENSE) |
| FFmpeg toolchain runtime: nom 8.0.0 (rav1e) | 8.0.0 | MIT | Redistributed in this artifact | https://static.crates.io/crates/nom/nom-8.0.0.crate (crate archive sha256 df9761775871bdef83bee530e60050f7e54b1105350d6884eb0fb4f46c2f9405); https://github.com/rust-bakery/nom | [licence-380](tools/package/native-licences/ffmpeg-toolchain/crates--nom-7.1.3--LICENSE) |
| FFmpeg toolchain runtime: num-bigint 0.4.6 (rav1e) | 0.4.6 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/num-bigint/num-bigint-0.4.6.crate (crate archive sha256 a5e44f723f1133c9deac646763579fdb3ac745e418f2a7af9cd0c431da1f20b9); https://github.com/rust-num/num-bigint | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-304](tools/package/native-licences/ffmpeg-toolchain/crates--log-0.4.34--LICENSE-MIT) |
| FFmpeg toolchain runtime: num-bigint 0.4.8 (librsvg) | 0.4.8 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/num-bigint/num-bigint-0.4.8.crate (crate archive sha256 c89e69e7e0f03bea5ef08013795c25018e101932225a656383bd384495ecc367); https://github.com/rust-num/num-bigint | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-304](tools/package/native-licences/ffmpeg-toolchain/crates--log-0.4.34--LICENSE-MIT) |
| FFmpeg toolchain runtime: num-complex 0.4.6 (librsvg) | 0.4.6 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/num-complex/num-complex-0.4.6.crate (crate archive sha256 73f88a1307638156682bada9d7604135552957b7818057dcef22705b4d509495); https://github.com/rust-num/num-complex | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-304](tools/package/native-licences/ffmpeg-toolchain/crates--log-0.4.34--LICENSE-MIT) |
| FFmpeg toolchain runtime: num-integer 0.1.46 (rav1e) | 0.1.46 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/num-integer/num-integer-0.1.46.crate (crate archive sha256 7969661fd2958a5cb096e56c8e1ad0444ac2bbcd0061bd28660485a44879858f); https://github.com/rust-num/num-integer | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-304](tools/package/native-licences/ffmpeg-toolchain/crates--log-0.4.34--LICENSE-MIT) |
| FFmpeg toolchain runtime: num-integer 0.1.47 (librsvg) | 0.1.47 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/num-integer/num-integer-0.1.47.crate (crate archive sha256 7ce2d95d4b3734dc35aa2f45e1aa22cd416814592a4f9d9205e11affd5b8e10b); https://github.com/rust-num/num-integer | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-304](tools/package/native-licences/ffmpeg-toolchain/crates--log-0.4.34--LICENSE-MIT) |
| FFmpeg toolchain runtime: num-rational 0.4.2 (librsvg) | 0.4.2 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/num-rational/num-rational-0.4.2.crate (crate archive sha256 f83d14da390562dca69fc84082e73e548e1ad308d24accdedd2720017cb37824); https://github.com/rust-num/num-rational | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-304](tools/package/native-licences/ffmpeg-toolchain/crates--log-0.4.34--LICENSE-MIT) |
| FFmpeg toolchain runtime: num-rational 0.4.2 (rav1e) | 0.4.2 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/num-rational/num-rational-0.4.2.crate (crate archive sha256 f83d14da390562dca69fc84082e73e548e1ad308d24accdedd2720017cb37824); https://github.com/rust-num/num-rational | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-304](tools/package/native-licences/ffmpeg-toolchain/crates--log-0.4.34--LICENSE-MIT) |
| FFmpeg toolchain runtime: num-traits 0.2.19 (librsvg) | 0.2.19 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/num-traits/num-traits-0.2.19.crate (crate archive sha256 071dfc062690e90b734c0b2273ce72ad0ffa95f0c74596bc250dcfd960262841); https://github.com/rust-num/num-traits | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-304](tools/package/native-licences/ffmpeg-toolchain/crates--log-0.4.34--LICENSE-MIT) |
| FFmpeg toolchain runtime: num-traits 0.2.19 (rav1e) | 0.2.19 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/num-traits/num-traits-0.2.19.crate (crate archive sha256 071dfc062690e90b734c0b2273ce72ad0ffa95f0c74596bc250dcfd960262841); https://github.com/rust-num/num-traits | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-304](tools/package/native-licences/ffmpeg-toolchain/crates--log-0.4.34--LICENSE-MIT) |
| FFmpeg toolchain runtime: object 0.39.1 (toolchain) | 0.39.1 | Apache-2.0 OR MIT | Redistributed in this artifact | https://static.crates.io/crates/object/object-0.39.1.crate (crate archive sha256 2e5a6c098c7a3b6547378093f5cc30bc54fd361ce711e05293a5cc589562739b); https://github.com/gimli-rs/object | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-381](tools/package/native-licences/ffmpeg-toolchain/crates--object-0.39.1--LICENSE-MIT) |
| FFmpeg toolchain runtime: once_cell 1.21.3 (rav1e) | 1.21.3 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/once_cell/once_cell-1.21.3.crate (crate archive sha256 42f5e15c9953c5e4ccceeb2e7382a716482c34515315f7b03532b8b4e8393d2d); https://github.com/matklad/once_cell | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-287](tools/package/native-licences/ffmpeg-toolchain/crates--adler2-2.0.1--LICENSE-MIT) |
| FFmpeg toolchain runtime: once_cell 1.21.4 (librsvg) | 1.21.4 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/once_cell/once_cell-1.21.4.crate (crate archive sha256 9f7c3e4beb33f85d45ae3e3a1792185706c8e16d043238c593331cc7cd313b50); https://github.com/matklad/once_cell | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-287](tools/package/native-licences/ffmpeg-toolchain/crates--adler2-2.0.1--LICENSE-MIT) |
| FFmpeg toolchain runtime: once_cell_polyfill 1.70.1 (rav1e) | 1.70.1 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/once_cell_polyfill/once_cell_polyfill-1.70.1.crate (crate archive sha256 a4895175b425cb1f87721b59f0f286c2092bd4af812243672510e1ac53e2e0ad); https://github.com/polyfill-rs/once_cell_polyfill | [licence-294](tools/package/native-licences/ffmpeg-toolchain/crates--anstream-0.6.19--LICENSE-APACHE), [licence-295](tools/package/native-licences/ffmpeg-toolchain/crates--anstream-0.6.19--LICENSE-MIT) |
| FFmpeg toolchain runtime: pango 0.22.9 (librsvg) | 0.22.9 | MIT | Redistributed in this artifact | https://static.crates.io/crates/pango/pango-0.22.9.crate (crate archive sha256 0b2022dbbd82e1c42bd950a6f1df9b98c796e725dce5ec275e03cbf9772e4efa); https://github.com/gtk-rs/gtk-rs-core | [licence-312](tools/package/native-licences/ffmpeg-toolchain/crates--cairo-rs-0.22.9--COPYRIGHT), [licence-313](tools/package/native-licences/ffmpeg-toolchain/crates--cairo-rs-0.22.9--LICENSE) |
| FFmpeg toolchain runtime: pango-sys 0.22.9 (librsvg) | 0.22.9 | MIT | Redistributed in this artifact | https://static.crates.io/crates/pango-sys/pango-sys-0.22.9.crate (crate archive sha256 ca02d64761b74d56cdd4b437db6d73dc95e6c0d40f27e1c707952c0f09052948); https://github.com/gtk-rs/gtk-rs-core | [licence-313](tools/package/native-licences/ffmpeg-toolchain/crates--cairo-rs-0.22.9--LICENSE) |
| FFmpeg toolchain runtime: pangocairo 0.22.9 (librsvg) | 0.22.9 | MIT | Redistributed in this artifact | https://static.crates.io/crates/pangocairo/pangocairo-0.22.9.crate (crate archive sha256 bd199a0fef965b3ebda91a929a1ab5e7729538882c68e8de38e1904d2e094757); https://github.com/gtk-rs/gtk-rs-core | [licence-312](tools/package/native-licences/ffmpeg-toolchain/crates--cairo-rs-0.22.9--COPYRIGHT), [licence-313](tools/package/native-licences/ffmpeg-toolchain/crates--cairo-rs-0.22.9--LICENSE) |
| FFmpeg toolchain runtime: pangocairo-sys 0.22.9 (librsvg) | 0.22.9 | MIT | Redistributed in this artifact | https://static.crates.io/crates/pangocairo-sys/pangocairo-sys-0.22.9.crate (crate archive sha256 a649a616d67ae68539bc85f00fb45d36fba742ed20fc20e6712a15d8ee52bd3f); https://github.com/gtk-rs/gtk-rs-core | [licence-313](tools/package/native-licences/ffmpeg-toolchain/crates--cairo-rs-0.22.9--LICENSE) |
| FFmpeg toolchain runtime: parking_lot 0.12.5 (librsvg) | 0.12.5 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/parking_lot/parking_lot-0.12.5.crate (crate archive sha256 93857453250e3077bd71ff98b6a65ea6621a19bb0f559a85248955ac12c45a1a); https://github.com/Amanieu/parking_lot | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-367](tools/package/native-licences/ffmpeg-toolchain/crates--lock_api-0.4.14--LICENSE-MIT) |
| FFmpeg toolchain runtime: parking_lot_core 0.9.12 (librsvg) | 0.9.12 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/parking_lot_core/parking_lot_core-0.9.12.crate (crate archive sha256 2621685985a2ebf1c516881c026032ac7deafcda1a2c9b7850dc81e3dfcb64c1); https://github.com/Amanieu/parking_lot | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-367](tools/package/native-licences/ffmpeg-toolchain/crates--lock_api-0.4.14--LICENSE-MIT) |
| FFmpeg toolchain runtime: percent-encoding 2.3.2 (librsvg) | 2.3.2 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/percent-encoding/percent-encoding-2.3.2.crate (crate archive sha256 9b4f627cb1b25917193a259e49bdad08f671f8d9708acfd5fe0a8c1455d87220); https://github.com/servo/rust-url/ | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-325](tools/package/native-licences/ffmpeg-toolchain/crates--data-url-0.3.2--LICENSE-MIT) |
| FFmpeg toolchain runtime: phf 0.13.1 (librsvg) | 0.13.1 | MIT | Redistributed in this artifact | https://static.crates.io/crates/phf/phf-0.13.1.crate (crate archive sha256 c1562dc717473dbaa4c1f85a36410e03c047b2e7df7f45ee938fbef64ae7fadf); https://github.com/rust-phf/rust-phf | [licence-382](tools/package/native-licences/ffmpeg-toolchain/crates--phf-0.13.1--LICENSE) |
| FFmpeg toolchain runtime: phf_shared 0.13.1 (librsvg) | 0.13.1 | MIT | Redistributed in this artifact | https://static.crates.io/crates/phf_shared/phf_shared-0.13.1.crate (crate archive sha256 e57fef6bc5981e38c2ce2d63bfa546861309f875b8a75f092d1d54ae2d64f266); https://github.com/rust-phf/rust-phf | [licence-382](tools/package/native-licences/ffmpeg-toolchain/crates--phf-0.13.1--LICENSE) |
| FFmpeg toolchain runtime: phf_shared 0.14.0 (librsvg) | 0.14.0 | MIT | Redistributed in this artifact | https://static.crates.io/crates/phf_shared/phf_shared-0.14.0.crate (crate archive sha256 c6fd9027e2d9319be6349febd1db4e8d02aa544921200c9b777720ac34a3aa89); https://github.com/rust-phf/rust-phf | [licence-382](tools/package/native-licences/ffmpeg-toolchain/crates--phf-0.13.1--LICENSE) |
| FFmpeg toolchain runtime: pin-project-lite 0.2.17 (librsvg) | 0.2.17 | Apache-2.0 OR MIT | Redistributed in this artifact | https://static.crates.io/crates/pin-project-lite/pin-project-lite-0.2.17.crate (crate archive sha256 a89322df9ebe1c1578d689c92318e070967d1042b512afbe49518723f4e6d5cd); https://github.com/taiki-e/pin-project-lite | [licence-336](tools/package/native-licences/ffmpeg-toolchain/crates--miniz_oxide-0.9.1--LICENSE-APACHE.md), [licence-287](tools/package/native-licences/ffmpeg-toolchain/crates--adler2-2.0.1--LICENSE-MIT) |
| FFmpeg toolchain runtime: png 0.18.1 (librsvg) | 0.18.1 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/png/png-0.18.1.crate (crate archive sha256 60769b8b31b2a9f263dae2776c37b1b28ae246943cf719eb6946a1db05128a61); https://github.com/image-rs/image-png | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-383](tools/package/native-licences/ffmpeg-toolchain/crates--png-0.18.1--LICENSE-MIT) |
| FFmpeg toolchain runtime: potential_utf 0.1.6 (librsvg) | 0.1.6 | Unicode-3.0 | Redistributed in this artifact | https://static.crates.io/crates/potential_utf/potential_utf-0.1.6.crate (crate archive sha256 d83eb9bc6d8e5cf568e7a1101d60ee05e81ed50ea106026f3d18deeb046d7661); https://github.com/unicode-org/icu4x | [licence-346](tools/package/native-licences/ffmpeg-toolchain/crates--icu_collections-2.4.0--LICENSE) |
| FFmpeg toolchain runtime: precomputed-hash 0.1.1 (librsvg) | 0.1.1 | MIT | Redistributed in this artifact | https://static.crates.io/crates/precomputed-hash/precomputed-hash-0.1.1.crate (crate archive sha256 925383efa346730478fb4838dbe9137d2a47675ad789c546d150a6e1dd4ab31c); https://github.com/emilio/precomputed-hash | [licence-384](tools/package/native-licences/ffmpeg-toolchain/crates--precomputed-hash-0.1.1--LICENSE) |
| FFmpeg toolchain runtime: profiling 1.0.16 (rav1e) | 1.0.16 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/profiling/profiling-1.0.16.crate (crate archive sha256 afbdc74edc00b6f6a218ca6a5364d6226a259d4b8ea1af4a0ea063f27e179f4d); https://github.com/aclysma/profiling | [licence-37](tools/package/native-licences/ffmpeg-toolchain/spdx--text--MIT.txt), [licence-55](tools/package/native-licences/ffmpeg-toolchain/spdx--text--Apache-2.0.txt) |
| FFmpeg toolchain runtime: pxfm 0.1.30 (librsvg) | 0.1.30 | BSD-3-Clause OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/pxfm/pxfm-0.1.30.crate (crate archive sha256 d55d956fa96f5ec02be2e13af0e20391a5aa83d6a074e3ad368959d0fab299ea); https://github.com/awxkee/pxfm | [licence-376](tools/package/native-licences/ffmpeg-toolchain/crates--moxcms-0.8.1--LICENSE-APACHE.md), [licence-377](tools/package/native-licences/ffmpeg-toolchain/crates--moxcms-0.8.1--LICENSE.md) |
| FFmpeg toolchain runtime: quick-error 2.0.1 (librsvg) | 2.0.1 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/quick-error/quick-error-2.0.1.crate (crate archive sha256 a993555f31e5a609f617c12db6250dedcac1b0a85076912c436e6fc9b2c8e6a3); http://github.com/tailhook/quick-error | [licence-294](tools/package/native-licences/ffmpeg-toolchain/crates--anstream-0.6.19--LICENSE-APACHE), [licence-385](tools/package/native-licences/ffmpeg-toolchain/crates--quick-error-2.0.1--LICENSE-MIT) |
| FFmpeg toolchain runtime: rawpointer 0.2.1 (librsvg) | 0.2.1 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/rawpointer/rawpointer-0.2.1.crate (crate archive sha256 60a357793950651c4ed0f3f52338f53b2f809f32d83a07f72909fa13e4c6c1e3); https://github.com/bluss/rawpointer/ | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-328](tools/package/native-licences/ffmpeg-toolchain/crates--either-1.15.0--LICENSE-MIT) |
| FFmpeg toolchain runtime: rayon 1.10.0 (rav1e) | 1.10.0 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/rayon/rayon-1.10.0.crate (crate archive sha256 b418a60154510ca1a002a752ca9714984e21e4241e804d32555251faf8b78ffa); https://github.com/rayon-rs/rayon | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-334](tools/package/native-licences/ffmpeg-toolchain/crates--rayon-1.10.0--LICENSE-MIT) |
| FFmpeg toolchain runtime: rayon 1.12.0 (librsvg) | 1.12.0 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/rayon/rayon-1.12.0.crate (crate archive sha256 fb39b166781f92d482534ef4b4b1b2568f42613b53e5b6c160e24cfbfa30926d); https://github.com/rayon-rs/rayon | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-334](tools/package/native-licences/ffmpeg-toolchain/crates--rayon-1.10.0--LICENSE-MIT) |
| FFmpeg toolchain runtime: rayon-core 1.12.1 (rav1e) | 1.12.1 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/rayon-core/rayon-core-1.12.1.crate (crate archive sha256 1465873a3dfdaa8ae7cb14b4383657caab0b3e8a0aa9ae8e04b044854c8dfce2); https://github.com/rayon-rs/rayon | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-334](tools/package/native-licences/ffmpeg-toolchain/crates--rayon-1.10.0--LICENSE-MIT) |
| FFmpeg toolchain runtime: rayon-core 1.13.0 (librsvg) | 1.13.0 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/rayon-core/rayon-core-1.13.0.crate (crate archive sha256 22e18b0f0062d30d4230b2e85ff77fdfe4326feb054b9783a3460d8435c8ab91); https://github.com/rayon-rs/rayon | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-334](tools/package/native-licences/ffmpeg-toolchain/crates--rayon-1.10.0--LICENSE-MIT) |
| FFmpeg toolchain runtime: rctree 0.6.0 (librsvg) | 0.6.0 | MIT | Redistributed in this artifact | https://static.crates.io/crates/rctree/rctree-0.6.0.crate (crate archive sha256 e03e7866abec1101869ffa8e2c8355c4c2419d0214ece0cc3e428e5b94dea6e9); https://github.com/RazrFalcon/rctree | [licence-386](tools/package/native-licences/ffmpeg-toolchain/crates--rctree-0.6.0--LICENSE) |
| FFmpeg toolchain runtime: regex 1.13.1 (librsvg) | 1.13.1 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/regex/regex-1.13.1.crate (crate archive sha256 f020237b6c8eed93db2e2cb53c00c60a8e1bc73da7d073199a1180401450218d); https://github.com/rust-lang/regex | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-304](tools/package/native-licences/ffmpeg-toolchain/crates--log-0.4.34--LICENSE-MIT) |
| FFmpeg toolchain runtime: regex-automata 0.4.18 (librsvg) | 0.4.18 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/regex-automata/regex-automata-0.4.18.crate (crate archive sha256 ad8553b9b26413251cbf30e620595c7a41b3887f03da04579c0e6b0d6a06b4b2); https://github.com/rust-lang/regex | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-304](tools/package/native-licences/ffmpeg-toolchain/crates--log-0.4.34--LICENSE-MIT) |
| FFmpeg toolchain runtime: regex-syntax 0.8.11 (librsvg) | 0.8.11 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/regex-syntax/regex-syntax-0.8.11.crate (crate archive sha256 d6f6ff9a378485b298a5286656da665ba74413d36db0979633275d2e708145d4); https://github.com/rust-lang/regex | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-304](tools/package/native-licences/ffmpeg-toolchain/crates--log-0.4.34--LICENSE-MIT) |
| FFmpeg toolchain runtime: rgb 0.8.53 (librsvg) | 0.8.53 | MIT | Redistributed in this artifact | https://static.crates.io/crates/rgb/rgb-0.8.53.crate (crate archive sha256 47b34b781b31e5d73e9fbc8689c70551fd1ade9a19e3e28cfec8580a79290cc4); https://github.com/kornelski/rust-rgb | [licence-387](tools/package/native-licences/ffmpeg-toolchain/crates--rgb-0.8.53--LICENSE) |
| FFmpeg toolchain runtime: rust-std 1.99.1 (toolchain) | 1.99.1 | MIT OR Apache-2.0 | Redistributed in this artifact | https://github.com/rust-lang/rust @ 58cf8f9c35b355199727627d07ae34a4e2846d67; https://github.com/rust-lang/rust/tree/58cf8f9c35b355199727627d07ae34a4e2846d67/library | [licence-391](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--LICENSE-MIT), [licence-296](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--LICENSE-APACHE), [licence-388](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--COPYRIGHT), [licence-390](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-MIT), [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-389](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--portable-simd--LICENSE-MIT), [licence-125](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--portable-simd--LICENSE-APACHE) |
| FFmpeg toolchain runtime: rustc-demangle 0.1.28 (toolchain) | 0.1.28 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/rustc-demangle/rustc-demangle-0.1.28.crate (crate archive sha256 b74b56ffa8bb2830709a538c2cbcae9aa062db0d2a42563bfb09bdaae44020eb); https://github.com/rust-lang/rustc-demangle | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-303](tools/package/native-licences/ffmpeg-toolchain/rust-lang-backtrace-rs--LICENSE-MIT) |
| FFmpeg toolchain runtime: rustc-hash 2.1.3 (librsvg) | 2.1.3 | Apache-2.0 OR MIT | Redistributed in this artifact | https://static.crates.io/crates/rustc-hash/rustc-hash-2.1.3.crate (crate archive sha256 6b1e7f9a428571be2dc5bc0505c13fb6bf936822b894ec87abf8a08a4e51742d); https://github.com/rust-lang/rustc-hash | [licence-392](tools/package/native-licences/ffmpeg-toolchain/crates--rustc-hash-2.1.3--LICENSE-APACHE), [licence-393](tools/package/native-licences/ffmpeg-toolchain/crates--rustc-hash-2.1.3--LICENSE-MIT) |
| FFmpeg toolchain runtime: safe_arch 1.2.0 (librsvg) | 1.2.0 | Zlib OR Apache-2.0 OR MIT | Redistributed in this artifact | https://static.crates.io/crates/safe_arch/safe_arch-1.2.0.crate (crate archive sha256 42c6efa15875e6ecb39ca61fb0b0c1a40b84fac5a5ffe71eef7d1000c8eb3f5f); https://github.com/Lokathor/safe_arch | [licence-308](tools/package/native-licences/ffmpeg-toolchain/crates--bytemuck-1.25.2--LICENSE-APACHE), [licence-394](tools/package/native-licences/ffmpeg-toolchain/crates--safe_arch-1.2.0--LICENSE-MIT.md), [licence-395](tools/package/native-licences/ffmpeg-toolchain/crates--safe_arch-1.2.0--LICENSE-ZLIB.md) |
| FFmpeg toolchain runtime: scan_fmt 0.2.6 (rav1e) | 0.2.6 | MIT | Redistributed in this artifact | https://static.crates.io/crates/scan_fmt/scan_fmt-0.2.6.crate (crate archive sha256 0b53b0a5db882a8e2fdaae0a43f7b39e7e9082389e978398bdf223a55b581248); https://github.com/wlentz/scan_fmt | [licence-396](tools/package/native-licences/ffmpeg-toolchain/crates--scan_fmt-0.2.6--LICENSE) |
| FFmpeg toolchain runtime: scopeguard 1.2.0 (librsvg) | 1.2.0 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/scopeguard/scopeguard-1.2.0.crate (crate archive sha256 94143f37725109f92c262ed2cf5e59bce7498c01bcc1502d7b9afe439a4e9f49); https://github.com/bluss/scopeguard | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-397](tools/package/native-licences/ffmpeg-toolchain/crates--scopeguard-1.2.0--LICENSE-MIT) |
| FFmpeg toolchain runtime: selectors 0.40.0 (librsvg) | 0.40.0 | MPL-2.0 | Redistributed in this artifact | https://static.crates.io/crates/selectors/selectors-0.40.0.crate (crate archive sha256 eeee001a77567bb05e71652718d3ff76d8697c151ac523e68e9513194eb2b75a); https://github.com/servo/stylo | [licence-398](tools/package/native-licences/ffmpeg-toolchain/spdx--text--MPL-2.0.txt) |
| FFmpeg toolchain runtime: serde 1.0.229 (librsvg) | 1.0.229 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/serde/serde-1.0.229.crate (crate archive sha256 4148590afebada386688f18773da617792bf2ef03ffc1e4cbd2b1d45b023e0ba); https://github.com/serde-rs/serde | [licence-296](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--LICENSE-APACHE), [licence-287](tools/package/native-licences/ffmpeg-toolchain/crates--adler2-2.0.1--LICENSE-MIT) |
| FFmpeg toolchain runtime: serde_core 1.0.229 (librsvg) | 1.0.229 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/serde_core/serde_core-1.0.229.crate (crate archive sha256 67dca2c9c51e58a4791a4b1ed58308b39c64224d349a935ab5039aa360942a48); https://github.com/serde-rs/serde | [licence-296](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--LICENSE-APACHE), [licence-287](tools/package/native-licences/ffmpeg-toolchain/crates--adler2-2.0.1--LICENSE-MIT) |
| FFmpeg toolchain runtime: servo_arc 0.4.3 (librsvg) | 0.4.3 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/servo_arc/servo_arc-0.4.3.crate (crate archive sha256 170fb83ab34de17dc69aa7c67482b22218ddb85da56546f9bd6b929e32a05930); https://github.com/servo/stylo | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-287](tools/package/native-licences/ffmpeg-toolchain/crates--adler2-2.0.1--LICENSE-MIT) |
| FFmpeg toolchain runtime: simba 0.10.2 (librsvg) | 0.10.2 | Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/simba/simba-0.10.2.crate (crate archive sha256 f1a7200d82ff1c7b4235efd12f11e2537a402c91cf83a5cb97ce80eef787fde7); https://github.com/dimforge/simba | [licence-378](tools/package/native-licences/ffmpeg-toolchain/crates--nalgebra-0.35.0--LICENSE) |
| FFmpeg toolchain runtime: simd-adler32 0.3.10 (librsvg) | 0.3.10 | MIT | Redistributed in this artifact | https://static.crates.io/crates/simd-adler32/simd-adler32-0.3.10.crate (crate archive sha256 3a219298ac11a56ea9a6d2120044824d6f01aeb034955e7af7bc16858527deea); https://github.com/mcountryman/simd-adler32 | [licence-399](tools/package/native-licences/ffmpeg-toolchain/crates--simd-adler32-0.3.10--LICENSE.md) |
| FFmpeg toolchain runtime: simdutf8 0.1.5 (librsvg) | 0.1.5 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/simdutf8/simdutf8-0.1.5.crate (crate archive sha256 e3a9fe34e3e7a50316060351f37187a3f546bce95496156754b601a5fa71b76e); https://github.com/rusticstuff/simdutf8 | [licence-400](tools/package/native-licences/ffmpeg-toolchain/crates--simdutf8-0.1.5--LICENSE-Apache), [licence-401](tools/package/native-licences/ffmpeg-toolchain/crates--simdutf8-0.1.5--LICENSE-MIT) |
| FFmpeg toolchain runtime: siphasher 1.0.4 (librsvg) | 1.0.4 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/siphasher/siphasher-1.0.4.crate (crate archive sha256 33f4fe9184a62d842c9ef383018f3306d8ba224fd9d836f56d7288308847c256); https://github.com/jedisct1/rust-siphash | [licence-402](tools/package/native-licences/ffmpeg-toolchain/crates--siphasher-1.0.4--COPYING), [licence-125](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--portable-simd--LICENSE-APACHE), [licence-126](tools/package/native-licences/ffmpeg-toolchain/crates--siphasher-1.0.4--LICENSE-MIT) |
| FFmpeg toolchain runtime: slab 0.4.12 (librsvg) | 0.4.12 | MIT | Redistributed in this artifact | https://static.crates.io/crates/slab/slab-0.4.12.crate (crate archive sha256 0c790de23124f9ab44544d7ac05d60440adc586479ce501c1d6d7da3cd8c9cf5); https://github.com/tokio-rs/slab | [licence-403](tools/package/native-licences/ffmpeg-toolchain/crates--slab-0.4.12--LICENSE) |
| FFmpeg toolchain runtime: smallvec 1.16.4 (librsvg) | 1.16.4 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/smallvec/smallvec-1.16.4.crate (crate archive sha256 d0d5d4b1981b8bbbb7aed204cae5726d683d5d6ac7e74ec54122ea28f315e7c8); https://github.com/servo/rust-smallvec | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-404](tools/package/native-licences/ffmpeg-toolchain/crates--smallvec-1.16.4--LICENSE-MIT) |
| FFmpeg toolchain runtime: stable_deref_trait 1.2.0 (rav1e) | 1.2.0 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/stable_deref_trait/stable_deref_trait-1.2.0.crate (crate archive sha256 a8f112729512f8e442d81f95a8a7ddf2b7c6b8a1a6f509a95864142b30cab2d3); https://github.com/storyyeller/stable_deref_trait | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-405](tools/package/native-licences/ffmpeg-toolchain/crates--stable_deref_trait-1.2.0--LICENSE-MIT) |
| FFmpeg toolchain runtime: stable_deref_trait 1.2.1 (librsvg) | 1.2.1 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/stable_deref_trait/stable_deref_trait-1.2.1.crate (crate archive sha256 6ce2be8dc25455e1f91df71bfa12ad37d7af1092ae736f3a6cd0e37bc7810596); https://github.com/storyyeller/stable_deref_trait | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-405](tools/package/native-licences/ffmpeg-toolchain/crates--stable_deref_trait-1.2.0--LICENSE-MIT) |
| FFmpeg toolchain runtime: static_assertions 1.1.0 (librsvg) | 1.1.0 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/static_assertions/static_assertions-1.1.0.crate (crate archive sha256 a2eb9349b6444b326872e140eb1cf5e7c522154d69e7a0ffb0fb81c06b37543f); https://github.com/nvzqz/static-assertions-rs | [licence-125](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--portable-simd--LICENSE-APACHE), [licence-406](tools/package/native-licences/ffmpeg-toolchain/crates--static_assertions-1.1.0--LICENSE-MIT) |
| FFmpeg toolchain runtime: string_cache 0.10.0 (librsvg) | 0.10.0 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/string_cache/string_cache-0.10.0.crate (crate archive sha256 daf8762eb74d0e3b53126a15f88db5de3c8ee98cd3b5e3b58c1a9e21c6438873); https://github.com/servo/string-cache | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-407](tools/package/native-licences/ffmpeg-toolchain/crates--string_cache-0.10.0--LICENSE-MIT) |
| FFmpeg toolchain runtime: string_cache 0.9.0 (librsvg) | 0.9.0 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/string_cache/string_cache-0.9.0.crate (crate archive sha256 a18596f8c785a729f2819c0f6a7eae6ebeebdfffbfe4214ae6b087f690e31901); https://github.com/servo/string-cache | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-407](tools/package/native-licences/ffmpeg-toolchain/crates--string_cache-0.10.0--LICENSE-MIT) |
| FFmpeg toolchain runtime: tendril 0.5.1 (librsvg) | 0.5.1 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/tendril/tendril-0.5.1.crate (crate archive sha256 5fed54709c5b3a53d09bb1c113ea4f5ceafd1e772ddcb0030a82e1d56c087b08); https://github.com/servo/html5ever | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-408](tools/package/native-licences/ffmpeg-toolchain/crates--tendril-0.5.1--LICENSE-MIT) |
| FFmpeg toolchain runtime: terminal_size 0.4.2 (rav1e) | 0.4.2 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/terminal_size/terminal_size-0.4.2.crate (crate archive sha256 45c6481c4829e4cc63825e62c49186a34538b7b2750b73b266581ffb612fb5ed); https://github.com/eminence/terminal-size | [licence-294](tools/package/native-licences/ffmpeg-toolchain/crates--anstream-0.6.19--LICENSE-APACHE), [licence-409](tools/package/native-licences/ffmpeg-toolchain/crates--terminal_size-0.4.2--LICENSE-MIT) |
| FFmpeg toolchain runtime: thiserror 1.0.69 (rav1e) | 1.0.69 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/thiserror/thiserror-1.0.69.crate (crate archive sha256 b6aaf5339b578ea85b50e080feb250a3e8ae8cfcdff9a461c9ec2904bc923f52); https://github.com/dtolnay/thiserror | [licence-296](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--LICENSE-APACHE), [licence-287](tools/package/native-licences/ffmpeg-toolchain/crates--adler2-2.0.1--LICENSE-MIT) |
| FFmpeg toolchain runtime: thiserror 2.0.12 (rav1e) | 2.0.12 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/thiserror/thiserror-2.0.12.crate (crate archive sha256 567b8a2dae586314f7be2a752ec7474332959c6460e02bde30d702a66d488708); https://github.com/dtolnay/thiserror | [licence-296](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--LICENSE-APACHE), [licence-287](tools/package/native-licences/ffmpeg-toolchain/crates--adler2-2.0.1--LICENSE-MIT) |
| FFmpeg toolchain runtime: tinystr 0.8.5 (librsvg) | 0.8.5 | Unicode-3.0 | Redistributed in this artifact | https://static.crates.io/crates/tinystr/tinystr-0.8.5.crate (crate archive sha256 abc840c238154d58f9e86b2792261edfde565a17696e1cda1a449de27979801a); https://github.com/unicode-org/icu4x | [licence-346](tools/package/native-licences/ffmpeg-toolchain/crates--icu_collections-2.4.0--LICENSE) |
| FFmpeg toolchain runtime: tinyvec 1.13.3 (librsvg) | 1.13.3 | Zlib OR Apache-2.0 OR MIT | Redistributed in this artifact | https://static.crates.io/crates/tinyvec/tinyvec-1.13.3.crate (crate archive sha256 fd3ca314f692efd6c868f8408f53fe444634a845f96c028b97d35f6a1f79f0ee); https://github.com/Lokathor/tinyvec | [licence-125](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--portable-simd--LICENSE-APACHE), [licence-410](tools/package/native-licences/ffmpeg-toolchain/crates--tinyvec-1.13.3--LICENSE-MIT.md), [licence-310](tools/package/native-licences/ffmpeg-toolchain/crates--bytemuck-1.25.2--LICENSE-ZLIB) |
| FFmpeg toolchain runtime: typenum 1.20.1 (librsvg) | 1.20.1 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/typenum/typenum-1.20.1.crate (crate archive sha256 b6f5e870be6c3b371b77fe0ee0bafb859fa4964b4404c27de1d380043c4dda20); https://github.com/paholg/typenum | [licence-411](tools/package/native-licences/ffmpeg-toolchain/crates--typenum-1.20.1--LICENSE), [licence-412](tools/package/native-licences/ffmpeg-toolchain/crates--typenum-1.20.1--LICENSE-APACHE), [licence-413](tools/package/native-licences/ffmpeg-toolchain/crates--typenum-1.20.1--LICENSE-MIT) |
| FFmpeg toolchain runtime: unicode-width 0.2.1 (rav1e) | 0.2.1 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/unicode-width/unicode-width-0.2.1.crate (crate archive sha256 4a1a07cc7db3810833284e8d372ccdc6da29741639ecc70c9ec107df0fa6154c); https://github.com/unicode-rs/unicode-width | [licence-414](tools/package/native-licences/ffmpeg-toolchain/crates--unicode-width-0.2.1--COPYRIGHT), [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-344](tools/package/native-licences/ffmpeg-toolchain/crates--gimli-0.34.0--LICENSE-MIT) |
| FFmpeg toolchain runtime: url 2.5.8 (librsvg) | 2.5.8 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/url/url-2.5.8.crate (crate archive sha256 ff67a8a4397373c3ef660812acab3268222035010ab8680ec4215f38ba3d0eed); https://github.com/servo/rust-url | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-325](tools/package/native-licences/ffmpeg-toolchain/crates--data-url-0.3.2--LICENSE-MIT) |
| FFmpeg toolchain runtime: utf8_iter 1.0.4 (librsvg) | 1.0.4 | Apache-2.0 OR MIT | Redistributed in this artifact | https://static.crates.io/crates/utf8_iter/utf8_iter-1.0.4.crate (crate archive sha256 b6c140620e7ffbb22c2dee59cafe6084a59b5ffc27a8859a5f0d494b5d52b6be); https://github.com/hsivonen/utf8_iter | [licence-415](tools/package/native-licences/ffmpeg-toolchain/crates--utf8_iter-1.0.4--COPYRIGHT), [licence-125](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--portable-simd--LICENSE-APACHE), [licence-331](tools/package/native-licences/ffmpeg-toolchain/crates--encoding_rs-0.8.42--LICENSE-MIT) |
| FFmpeg toolchain runtime: utf8parse 0.2.2 (rav1e) | 0.2.2 | Apache-2.0 OR MIT | Redistributed in this artifact | https://static.crates.io/crates/utf8parse/utf8parse-0.2.2.crate (crate archive sha256 06abde3611657adf66d383f00b093d7faecc7fa57071cce2578660c9f1010821); https://github.com/alacritty/vte | [licence-296](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--LICENSE-APACHE), [licence-416](tools/package/native-licences/ffmpeg-toolchain/crates--utf8parse-0.2.2--LICENSE-MIT) |
| FFmpeg toolchain runtime: v_frame 0.3.9 (rav1e) | 0.3.9 | BSD-2-Clause | Redistributed in this artifact | https://static.crates.io/crates/v_frame/v_frame-0.3.9.crate (crate archive sha256 666b7727c8875d6ab5db9533418d7c764233ac9c0cff1d469aec8fa127597be2); https://github.com/rust-av/v_frame | [licence-417](tools/package/native-licences/ffmpeg-toolchain/crates--v_frame-0.3.9--LICENSE) |
| FFmpeg toolchain runtime: web_atoms 0.2.6 (librsvg) | 0.2.6 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/web_atoms/web_atoms-0.2.6.crate (crate archive sha256 ba8b815c1b593dc0baf78dd0f4fc8fdb2de53198fb1163738093e9a311c33fb3); https://github.com/servo/html5ever | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-368](tools/package/native-licences/ffmpeg-toolchain/crates--markup5ever-0.39.0--LICENSE-MIT) |
| FFmpeg toolchain runtime: weezl 0.1.12 (librsvg) | 0.1.12 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/weezl/weezl-0.1.12.crate (crate archive sha256 a28ac98ddc8b9274cb41bb4d9d4d5c425b6020c50c46f25559911905610b4a88); https://github.com/image-rs/weezl | [licence-319](tools/package/native-licences/ffmpeg-toolchain/crates--core_detect-1.0.0--LICENSE-APACHE), [licence-418](tools/package/native-licences/ffmpeg-toolchain/crates--weezl-0.1.12--LICENSE-MIT) |
| FFmpeg toolchain runtime: wide 1.7.1 (librsvg) | 1.7.1 | Zlib OR Apache-2.0 OR MIT | Redistributed in this artifact | https://static.crates.io/crates/wide/wide-1.7.1.crate (crate archive sha256 d920ac99c3c8edce110cb8d07dbb324d6d026011dce85b1e9355b70f0adacc4f); https://github.com/Lokathor/wide | [licence-419](tools/package/native-licences/ffmpeg-toolchain/crates--wide-1.7.1--LICENSE-APACHE.txt), [licence-420](tools/package/native-licences/ffmpeg-toolchain/crates--wide-1.7.1--LICENSE-MIT.txt), [licence-421](tools/package/native-licences/ffmpeg-toolchain/crates--wide-1.7.1--LICENSE-ZLIB.txt) |
| FFmpeg toolchain runtime: winapi 0.3.9 (librsvg) | 0.3.9 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/winapi/winapi-0.3.9.crate (crate archive sha256 5c839a674fcd7a98952e593242ea400abe93992746761e38641405d28b00f419); https://github.com/retep998/winapi-rs | [licence-422](tools/package/native-licences/ffmpeg-toolchain/crates--winapi-0.3.9--LICENSE-APACHE), [licence-423](tools/package/native-licences/ffmpeg-toolchain/crates--winapi-0.3.9--LICENSE-MIT) |
| FFmpeg toolchain runtime: winapi-x86_64-pc-windows-gnu 0.4.0 (librsvg) | 0.4.0 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/winapi-x86_64-pc-windows-gnu/winapi-x86_64-pc-windows-gnu-0.4.0.crate (crate archive sha256 712e227841d057c1ee1cd2fb22fa7e5a5461ae8e48fa2ca79ec42cfc1931183f); https://github.com/retep998/winapi-rs | [licence-37](tools/package/native-licences/ffmpeg-toolchain/spdx--text--MIT.txt), [licence-55](tools/package/native-licences/ffmpeg-toolchain/spdx--text--Apache-2.0.txt) |
| FFmpeg toolchain runtime: windows-link 0.2.1 (librsvg) | 0.2.1 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/windows-link/windows-link-0.2.1.crate (crate archive sha256 f0805222e57f7521d6a62e36fa9163bc891acd422f971defe97d64e70d0a4fe5); https://github.com/microsoft/windows-rs | [licence-424](tools/package/native-licences/ffmpeg-toolchain/crates--windows-sys-0.59.0--license-apache-2.0), [licence-78](tools/package/native-licences/ffmpeg-toolchain/crates--windows-sys-0.59.0--license-mit) |
| FFmpeg toolchain runtime: windows-sys 0.59.0 (rav1e) | 0.59.0 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/windows-sys/windows-sys-0.59.0.crate (crate archive sha256 1e38bc4d79ed67fd075bcc251a1c39b32a1776bbe92e5bef1f0bf1f8c531853b); https://github.com/microsoft/windows-rs | [licence-424](tools/package/native-licences/ffmpeg-toolchain/crates--windows-sys-0.59.0--license-apache-2.0), [licence-78](tools/package/native-licences/ffmpeg-toolchain/crates--windows-sys-0.59.0--license-mit) |
| FFmpeg toolchain runtime: windows-sys 0.61.2 (librsvg) | 0.61.2 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/windows-sys/windows-sys-0.61.2.crate (crate archive sha256 ae137229bcbd6cdf0f7b80a31df61766145077ddf49416a728b02cb3921ff3fc); https://github.com/microsoft/windows-rs | [licence-424](tools/package/native-licences/ffmpeg-toolchain/crates--windows-sys-0.59.0--license-apache-2.0), [licence-78](tools/package/native-licences/ffmpeg-toolchain/crates--windows-sys-0.59.0--license-mit) |
| FFmpeg toolchain runtime: windows-targets 0.52.6 (rav1e) | 0.52.6 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/windows-targets/windows-targets-0.52.6.crate (crate archive sha256 9b724f72796e036ab90c1021d4780d4d3d648aca59e491e6b98e725b84e99973); https://github.com/microsoft/windows-rs | [licence-424](tools/package/native-licences/ffmpeg-toolchain/crates--windows-sys-0.59.0--license-apache-2.0), [licence-78](tools/package/native-licences/ffmpeg-toolchain/crates--windows-sys-0.59.0--license-mit) |
| FFmpeg toolchain runtime: windows_x86_64_gnu 0.52.6 (rav1e) | 0.52.6 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/windows_x86_64_gnu/windows_x86_64_gnu-0.52.6.crate (crate archive sha256 147a5c80aabfbf0c7d901cb5895d1de30ef2907eb21fbbab29ca94c5b08b1a78); https://github.com/microsoft/windows-rs | [licence-424](tools/package/native-licences/ffmpeg-toolchain/crates--windows-sys-0.59.0--license-apache-2.0), [licence-78](tools/package/native-licences/ffmpeg-toolchain/crates--windows-sys-0.59.0--license-mit) |
| FFmpeg toolchain runtime: writeable 0.6.4 (librsvg) | 0.6.4 | Unicode-3.0 | Redistributed in this artifact | https://static.crates.io/crates/writeable/writeable-0.6.4.crate (crate archive sha256 3ad82d2a33cdc9674dc7465672f271e096168fcdbe0f799d9e6db8c5892679dc); https://github.com/unicode-org/icu4x | [licence-346](tools/package/native-licences/ffmpeg-toolchain/crates--icu_collections-2.4.0--LICENSE) |
| FFmpeg toolchain runtime: xml5ever 0.39.0 (librsvg) | 0.39.0 | MIT OR Apache-2.0 | Redistributed in this artifact | https://static.crates.io/crates/xml5ever/xml5ever-0.39.0.crate (crate archive sha256 5ab627f34ff61b80d756180d556f9c68801d836d271b3b8c094504ceca69d221); https://github.com/servo/html5ever | [licence-284](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE), [licence-368](tools/package/native-licences/ffmpeg-toolchain/crates--markup5ever-0.39.0--LICENSE-MIT) |
| FFmpeg toolchain runtime: y4m 0.8.0 (rav1e) | 0.8.0 | MIT | Redistributed in this artifact | https://static.crates.io/crates/y4m/y4m-0.8.0.crate (crate archive sha256 7a5a4b21e1a62b67a2970e6831bc091d7b87e119e7f9791aef9702e3bef04448); https://github.com/image-rs/y4m.git | [licence-425](tools/package/native-licences/ffmpeg-toolchain/crates--y4m-0.8.0--LICENSE) |
| FFmpeg toolchain runtime: yoke 0.8.4 (librsvg) | 0.8.4 | Unicode-3.0 | Redistributed in this artifact | https://static.crates.io/crates/yoke/yoke-0.8.4.crate (crate archive sha256 417ef3fcf6c300b7dbd25c85531a746931c02ad536f3cf4786ed1e88223340b3); https://github.com/unicode-org/icu4x | [licence-346](tools/package/native-licences/ffmpeg-toolchain/crates--icu_collections-2.4.0--LICENSE) |
| FFmpeg toolchain runtime: zerocopy 0.8.63 (librsvg) | 0.8.63 | BSD-2-Clause OR Apache-2.0 OR MIT | Redistributed in this artifact | https://static.crates.io/crates/zerocopy/zerocopy-0.8.63.crate (crate archive sha256 e5fe1f8f1b06191a00962174c61aa5005e0bb391a6d80d07e24d115c01a92ed8); https://github.com/google/zerocopy | [licence-426](tools/package/native-licences/ffmpeg-toolchain/crates--zerocopy-0.8.63--LICENSE-APACHE), [licence-427](tools/package/native-licences/ffmpeg-toolchain/crates--zerocopy-0.8.63--LICENSE-BSD), [licence-428](tools/package/native-licences/ffmpeg-toolchain/crates--zerocopy-0.8.63--LICENSE-MIT) |
| FFmpeg toolchain runtime: zerofrom 0.1.8 (librsvg) | 0.1.8 | Unicode-3.0 | Redistributed in this artifact | https://static.crates.io/crates/zerofrom/zerofrom-0.1.8.crate (crate archive sha256 0ec05a11813ea801ff6d75110ad09cd0824ddba17dfe17128ea0d5f68e6c5272); https://github.com/unicode-org/icu4x | [licence-346](tools/package/native-licences/ffmpeg-toolchain/crates--icu_collections-2.4.0--LICENSE) |
| FFmpeg toolchain runtime: zerotrie 0.2.5 (librsvg) | 0.2.5 | Unicode-3.0 | Redistributed in this artifact | https://static.crates.io/crates/zerotrie/zerotrie-0.2.5.crate (crate archive sha256 4ea269c3bd32f0a32c321907a2ae912ba6f4649bb0fc764a15627e99a7095a3f); https://github.com/unicode-org/icu4x | [licence-346](tools/package/native-licences/ffmpeg-toolchain/crates--icu_collections-2.4.0--LICENSE) |
| FFmpeg toolchain runtime: zerovec 0.11.9 (librsvg) | 0.11.9 | Unicode-3.0 | Redistributed in this artifact | https://static.crates.io/crates/zerovec/zerovec-0.11.9.crate (crate archive sha256 f58a2799cfe9a1670c7ea8edbd52ef8edb93cb37a7f83bf31ba9e35d9dae6a40); https://github.com/unicode-org/icu4x | [licence-346](tools/package/native-licences/ffmpeg-toolchain/crates--icu_collections-2.4.0--LICENSE) |
| FFmpeg toolchain runtime: zune-core 0.5.3 (librsvg) | 0.5.3 | MIT OR Apache-2.0 OR Zlib | Redistributed in this artifact | https://static.crates.io/crates/zune-core/zune-core-0.5.3.crate (crate archive sha256 d56377fd46368984a170bc5aac5567e52ca5da874caa60bea39fcbca78fb658b); https://github.com/etemesi254/zune-image | [licence-160](tools/package/native-licences/ffmpeg-toolchain/crates--zune-core-0.5.3--LICENSE-APACHE), [licence-429](tools/package/native-licences/ffmpeg-toolchain/crates--zune-core-0.5.3--LICENSE-MIT), [licence-430](tools/package/native-licences/ffmpeg-toolchain/crates--zune-core-0.5.3--LICENSE-ZLIB) |
| FFmpeg toolchain runtime: zune-jpeg 0.5.15 (librsvg) | 0.5.15 | MIT OR Apache-2.0 OR Zlib | Redistributed in this artifact | https://static.crates.io/crates/zune-jpeg/zune-jpeg-0.5.15.crate (crate archive sha256 27bc9d5b815bc103f142aa054f561d9187d191692ec7c2d1e2b4737f8dbd7296); https://github.com/etemesi254/zune-image/tree/dev/crates/zune-jpeg | [licence-160](tools/package/native-licences/ffmpeg-toolchain/crates--zune-core-0.5.3--LICENSE-APACHE), [licence-429](tools/package/native-licences/ffmpeg-toolchain/crates--zune-core-0.5.3--LICENSE-MIT), [licence-430](tools/package/native-licences/ffmpeg-toolchain/crates--zune-core-0.5.3--LICENSE-ZLIB) |

## Component details and coverage

### FFmpeg component: amf

seat licence file(s) at the pin agree with the cell read; vendored subtree; compilation not determined at the seat: Thirdparty/amd/AmdDxExt/LICENSE.txt

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: aom

LICENSE BSD-2-Clause; separate PATENTS = AOM Patent License 1.0 (patent grant, not a copyright term); vendored subtree; compilation not determined at the seat: third_party/googletest/src/LICENSE, third_party/highway/LICENSE-BSD3, third_party/libwebm/LICENSE.TXT, third_party/libwebm/PATENTS.TXT, third_party/libyuv/LICENSE

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: avisynth

seat licence file(s) at the pin agree with the cell read; vendored subtree; compilation not determined at the seat: distrib/docs/english/source/avisynthdoc/license.rst; Pass 2 (U6): the grant in avs_core/include/avisynth_c.h L23-35 adds a C-interface linking exception ('As a special exception, I give you permission to link to the Avisynth C interface with independent modules that communicate with the Avisynth C interface solely through the interfaces defined in avisynth_c.h ...'); the expression stays GPL-2.0-or-later (CHARC). Pass 2 (U10): the whole avisynth_c.h blob is carried beside its excerpt.

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: brotli

seat licence file(s) at the pin agree with the cell read

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: cairo

seat licence file(s) at the pin agree with the cell read; vendored subtree; compilation not determined at the seat: perf/COPYING, util/COPYING, util/cairo-script/COPYING, util/cairo-trace/COPYING, util/cairo-trace/COPYING-GPL-3

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: chromaprint

LICENSE.md: own code MIT, includes FFmpeg LGPL-2.1 parts; 'as a whole LGPL 2.1'; vendored subtree; compilation not determined at the seat: src/3rdparty/googletest/LICENSE

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: dav1d

seat licence file(s) at the pin agree with the cell read; vendored subtree; compilation not determined at the seat (pass-1 P / vendored texts kept)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: davs2

seat licence file(s) at the pin agree with the cell read

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: ffnvcodec

seat licence file(s) at the pin agree with the cell read

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: ffnvcodec / repository 2

downloaded, not built at FFVER 900; headers MIT
Source status: downloaded-not-built

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: ffnvcodec / repository 3

downloaded, not built at FFVER 900; headers MIT
Source status: downloaded-not-built

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: fftw3

seat licence file(s) at the pin agree with the cell read; vendored subtree; compilation not determined at the seat: doc/license.texi

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: fontconfig

seat licence file(s) at the pin agree with the cell read

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: freetype

as 25-freetype (same pin); vendored subtree; compilation not determined at the seat (pass-1 P / vendored texts kept)
licence chosen: GPL-2.0-or-later

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: freetype-bootstrap

LICENSE.TXT: two mutually exclusive licences; GPL-2.0-or-later chosen; vendored subtree; compilation not determined at the seat (pass-1 P / vendored texts kept)
licence chosen: GPL-2.0-or-later

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: frei0r

seat licence file(s) at the pin agree with the cell read

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: fribidi

seat licence file(s) at the pin agree with the cell read

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: glib

seat licence file(s) at the pin agree with the cell read; vendored subtree; compilation not determined at the seat: docs/reference/COPYING

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: glslang

New record (CHARC ruling 1): fetched by shaderc's utils/git-sync-deps at the DEPS revision (shaderc DEPS 'glslang_revision') and built into libshaderc_combined (libshaderc/CMakeLists.txt links glslang and SPIRV). Texts: LICENSE.txt (the project's combined statement: BSD-3-Clause core, BSD-2-Clause, MIT, Apache-2.0, the NVIDIA preprocessor licence, GPL-3.0-or-later with the Bison exception for the generated grammar, MIT-Khronos-old headers) + the REUSE LICENSES/ set (8 texts). Expression = the LICENSES/ set; the NVIDIA text is LICENSES/AML-glslang.txt, SPDX identifier AML-glslang.; AML-glslang is GPL-3.0-compatible: its only conditions are notice retention and no endorsement by NVIDIA's name or marks (GPL-3.0 section 7 (b) / (d)); redistribution in source or binary, with or without modification, is granted. There is no patent grant (like BSD-3-Clause-Clear); the personal, non-exclusive grant accepted by use binds each recipient directly to NVIDIA and restricts nothing in Clearwater's redistribution.
Fetched via: shaderc git-sync-deps

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: gme

seat licence file(s) at the pin agree with the cell read; vendored subtree; compilation not determined at the seat: gme/ext/LICENSE

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: gmp

seat licence file(s) at the pin agree with the cell read

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: harfbuzz

COPYING: 'Old MIT' licence (cell read MIT: corrected identifier); vendored subtree; compilation not determined at the seat: perf/texts/COPYING, src/ms-use/COPYING

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: kvazaar

seat licence file(s) at the pin agree with the cell read; vendored subtree; compilation not determined at the seat: src/threadwrapper/LICENSE

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: lcevcdec

LICENSE.md: The Clear BSD License; expressly grants NO patent rights (LCEVC is patented: a patent-only note); vendored subtree; compilation not determined at the seat (pass-1 P / vendored texts kept)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: lcms2

seat licence file(s) at the pin agree with the cell read; vendored subtree; compilation not determined at the seat: plugins/fast_float/COPYING.GPL3, utils/jpgicc/LICENSE_iccjpeg

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: libaribb24

seat licence file(s) at the pin agree with the cell read

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: libaribcaption

LICENSE: MIT (cell read ISC: CORRECTED)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: libass

seat licence file(s) at the pin agree with the cell read

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: libbluray

seat licence file(s) at the pin agree with the cell read; vendored subtree; compilation not determined at the seat: contrib/asm/LICENSE.txt

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: libdvdcss

seat licence file(s) at the pin agree with the cell read

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: libdvdnav

seat licence file(s) at the pin agree with the cell read

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: libdvdread

seat licence file(s) at the pin agree with the cell read

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: libffi

seat licence file(s) at the pin agree with the cell read

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: libiconv

seat licence file(s) at the pin agree with the cell read; vendored subtree; compilation not determined at the seat (pass-1 P / vendored texts kept)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: libiconv / repository 2

gnulib README: licence stated per file/module; build infrastructure for libiconv; vendored subtree; compilation not determined at the seat: doc/licenses-texi.texi, modules/COPYING; gnulib per-module notices are not enumerated; COPYING and the four FSF texts are carried.

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: libjxl

LICENSE BSD-3-Clause; separate PATENTS grant; vendored subtree; compilation not determined at the seat: debian/copyright, lib/extras/LICENSE.apngdis, third_party/HEVCSoftware/cfg/LICENSE

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: libmp3lame

seat licence file(s) at the pin agree with the cell read

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: libogg

seat licence file(s) at the pin agree with the cell read

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: libopus

seat licence file(s) at the pin agree with the cell read

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: libplacebo

seat licence file(s) at the pin agree with the cell read; vendored subtree; compilation not determined at the seat: demos/LICENSE

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: libpng

seat licence file(s) at the pin agree with the cell read; vendored subtree; compilation not determined at the seat: contrib/gregbook/COPYING, contrib/gregbook/LICENSE, contrib/pngminus/LICENSE.txt

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: librist

seat licence file(s) at the pin agree with the cell read; vendored subtree; compilation not determined at the seat: contrib/mbedtls/LICENSE

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: librsvg

seat licence file(s) at the pin agree with the cell read; vendored subtree; compilation not determined at the seat: librsvg-rebind/LICENSE

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: libsamplerate

seat licence file(s) at the pin agree with the cell read; vendored subtree; compilation not determined at the seat: docs/license.md

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: libssh

seat licence file(s) at the pin agree with the cell read; vendored subtree; compilation not determined at the seat: cmake/Modules/COPYING-CMAKE-SCRIPTS

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: libtheora

seat licence file(s) at the pin agree with the cell read

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: libudfread

seat licence file(s) at the pin agree with the cell read

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: libunibreak

seat licence file(s) at the pin agree with the cell read

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: libva

seat licence file(s) at the pin agree with the cell read

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: libvorbis

seat licence file(s) at the pin agree with the cell read; vendored subtree; compilation not determined at the seat: debian/copyright

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: libvpx

seat licence file(s) at the pin agree with the cell read; vendored subtree; compilation not determined at the seat: third_party/googletest/src/LICENSE, third_party/libwebm/LICENSE.TXT, third_party/libyuv/LICENSE, third_party/nalloc/LICENSE

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: libwebp

seat licence file(s) at the pin agree with the cell read

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: libxml2

seat licence file(s) at the pin agree with the cell read; vendored subtree; compilation not determined at the seat: result/html-tokenizer/NOTICE; dict.c and list.c ISC-Veillard notices and whole source blobs are carried.

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: libzmq

LICENSE = MPL-2.0 text; sampled sources SPDX MPL-2.0, no Exhibit B 'Incompatible With Secondary Licenses' notice; vendored subtree; compilation not determined at the seat: external/sha1/license.txt, external/unity/license.txt, external/wepoll/license.txt, packaging/debian/copyright

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: lilv

seat licence file(s) at the pin agree with the cell read; vendored subtree; compilation not determined at the seat (pass-1 P / vendored texts kept)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: lv2

seat licence file(s) at the pin agree with the cell read; vendored subtree; compilation not determined at the seat (pass-1 P / vendored texts kept)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: mbedtls

seat licence file(s) at the pin agree with the cell read

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: mingw

COPYING.MinGW-w64-runtime: ZPL 2.1 except parts marked PD/BSD/LGPL; FSF: ZPL-2.1 GPL-compatible; vendored subtree; compilation not determined at the seat: mingw-w64-crt/profile/COPYING, mingw-w64-libraries/libmangle/COPYING, mingw-w64-libraries/pseh/COPYING, mingw-w64-libraries/winstorecompat/COPYING, mingw-w64-tools/gendef/COPYING

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: mingw-std-threads

seat licence file(s) at the pin agree with the cell read

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: onevpl

seat licence file(s) at the pin agree with the cell read; vendored subtree; compilation not determined at the seat: examples/api1x_core/legacy-decode/License.txt, libvpl/test/ext/googletest/LICENSE

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: openal

seat licence file(s) at the pin agree with the cell read; vendored subtree; compilation not determined at the seat (pass-1 P / vendored texts kept)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: openapv

seat licence file(s) at the pin agree with the cell read

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: opencl

seat licence file(s) at the pin agree with the cell read

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: opencl / repository 2

LICENSE Apache-2.0

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: opencore-amr

seat licence file(s) at the pin agree with the cell read

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: openh264

seat licence file(s) at the pin agree with the cell read

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: openjpeg

seat licence file(s) at the pin agree with the cell read; vendored subtree; compilation not determined at the seat: src/bin/wx/OPJViewer/source/license.txt, thirdparty/astyle/LICENSE.md, thirdparty/liblcms2/COPYING, thirdparty/libpng/LICENSE

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: openmpt

seat licence file(s) at the pin agree with the cell read; vendored subtree; compilation not determined at the seat: include/SignalsmithStretch/SignalsmithStretch/LICENSE.txt, include/SignalsmithStretch/signalsmith-linear/LICENSE.txt, include/ancient/LICENSE, include/ancient/LICENSE.bzip2, include/cryptopp/License.txt, include/flac/COPYING.Xiph, include/lame/COPYING, include/lhasa/COPYING.md, include/minimp3/LICENSE, include/miniz/LICENSE, include/mpg123/COPYING, include/nlohmann-json/LICENSE.MIT, include/ogg/COPYING, include/opus/COPYING, include/opusenc/COPYING, include/opusfile/COPYING, include/portaudio/LICENSE.txt, include/portaudio/bindings/cpp/COPYING, include/premake/LICENSE.txt, include/premake/binmodules/luasocket/LICENSE, include/premake/contrib/mbedtls/LICENSE, include/premake/contrib/zlib/LICENSE, include/premake/modules/xcode/LICENSE.TXT, include/premake/packages/debian/copyright, include/pthread-win32/docs/COPYING.FSF.md, include/pthread-win32/docs/COPYING.md, include/pugixml/LICENSE.md, include/r8brain/LICENSE, include/rtaudio/LICENSE, include/rtmidi/LICENSE, include/unrar/license.txt, include/vorbis/COPYING, include/zlib/contrib/minizip/LICENSE.Info-Zip, src/mpt/LICENSE.BSD-3-Clause.txt, src/mpt/LICENSE.BSL-1.0.txt

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: openssl

seat licence file(s) at the pin agree with the cell read; vendored subtree; compilation not determined at the seat: external/perl/Text-Template-1.56/LICENSE, util/perl/OpenSSL/copyright.pm

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: pango

COPYING is the GNU Library GPL 2 text (cell read LGPL-2.1-or-later; sources not sampled; either is GPL-3.0-compatible)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: pcre2

seat licence file(s) at the pin agree with the cell read; vendored subtree; compilation not determined at the seat: cmake/COPYING-CMAKE-SCRIPTS

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: pixman

seat licence file(s) at the pin agree with the cell read

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: rav1e

seat licence file(s) at the pin agree with the cell read; vendored subtree; compilation not determined at the seat: ivf/LICENSE

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: rubberband

seat licence file(s) at the pin agree with the cell read; vendored subtree; compilation not determined at the seat: src/ext/kissfft/COPYING, src/ext/speex/COPYING

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: sdl

seat licence file(s) at the pin agree with the cell read; vendored subtree; compilation not determined at the seat: Xcode-iOS/Demos/data/bitmapfont/license.txt, Xcode/SDL/pkg-support/resources/License.txt, src/hidapi/LICENSE-bsd.txt, src/hidapi/LICENSE-gpl3.txt, src/hidapi/LICENSE-orig.txt, src/hidapi/LICENSE.txt, src/video/yuv2rgb/LICENSE, visualtest/COPYING.txt

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: serd

seat licence file(s) at the pin agree with the cell read; vendored subtree; compilation not determined at the seat (pass-1 P / vendored texts kept)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: shaderc

statically links glslang, SPIRV-Tools and SPIRV-Headers at shaderc's DEPS revisions (records follow); vendored subtree; compilation not determined at the seat (pass-1 P / vendored texts kept); AML-glslang is GPL-3.0-compatible: its only conditions are notice retention and no endorsement by NVIDIA's name or marks (GPL-3.0 section 7 (b) / (d)); redistribution in source or binary, with or without modification, is granted. There is no patent grant (like BSD-3-Clause-Clear); the personal, non-exclusive grant accepted by use binds each recipient directly to NVIDIA and restricts nothing in Clearwater's redistribution. Test-only DEPS not built (BtbN -DSHADERC_SKIP_TESTS=ON, -DSPIRV_SKIP_EXECUTABLES=ON): googletest 52eb8108 (shaderc third_party/CMakeLists.txt L28-30), abseil-cpp dbf88f93, re2 972a15ce, effcee f8e8a164 (shaderc third_party/CMakeLists.txt L50-70; SPIRV-Tools external/CMakeLists.txt L97-191, CMakeLists.txt L316-317).

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: snappy

seat licence file(s) at the pin agree with the cell read

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: sord

seat licence file(s) at the pin agree with the cell read; vendored subtree; compilation not determined at the seat (pass-1 P / vendored texts kept)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: soxr

seat licence file(s) at the pin agree with the cell read; vendored subtree; compilation not determined at the seat: lsr-tests/COPYING

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: spirv-cross

seat licence file(s) at the pin agree with the cell read; vendored subtree; compilation not determined at the seat (pass-1 P / vendored texts kept)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: spirv-headers

seat licence file(s) at the pin agree with the cell read

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: spirv-headers-shaderc

New record (CHARC ruling 1): fetched by shaderc's utils/git-sync-deps at the DEPS revision (shaderc DEPS 'spirv_headers_revision'); headers and grammar tables compiled into SPIRV-Tools / glslang / shaderc. A different pin from the scripts.d/47-vulkan/60-spirv-headers.sh row (fbf86836). LICENSE (per-file statement, MIT-style for the headers) + LICENSES/CC-BY-4.0.txt and MIT.txt.
Fetched via: shaderc git-sync-deps

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: spirv-tools

New record (CHARC ruling 1): fetched by shaderc's utils/git-sync-deps at the DEPS revision (shaderc DEPS 'spirv_tools_revision'), built statically (-DSPIRV_TOOLS_BUILD_STATIC=ON) and linked into libshaderc_combined. LICENSE (Apache-2.0); no NOTICE file in the tree.
Fetched via: shaderc git-sync-deps

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: sratom

seat licence file(s) at the pin agree with the cell read; vendored subtree; compilation not determined at the seat (pass-1 P / vendored texts kept)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: srt

seat licence file(s) at the pin agree with the cell read

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: svtav1

LICENSE.md Clear BSD + LICENSE-BSD2.md for older files; PATENTS.md AOM patent licence; vendored subtree; compilation not determined at the seat (pass-1 P / vendored texts kept)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: twolame

seat licence file(s) at the pin agree with the cell read

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: uavs3d

seat licence file(s) at the pin agree with the cell read

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: vapoursynth

seat licence file(s) at the pin agree with the cell read

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: vidstab

LICENSE at the pin: relicensed to LGPL-2.1-or-later after v1.1.2 (cell read GPL-2.0-or-later: CORRECTED)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: vmaf

seat licence file(s) at the pin agree with the cell read

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: vulkan-headers

LICENSE.md + every header SPDX 'Apache-2.0 OR MIT' (cell read Apache-2.0)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: vulkan-loader

BtbN Vulkan-Shim-Loader LICENSE: MIT

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: vulkan-loader / repository 2

same repository/tag as 40-vulkan-headers

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: vvenc

LICENSE.txt: The Clear BSD License; vendored subtree; compilation not determined at the seat: thirdparty/nlohmann_json/LICENSE.MIT, thirdparty/simde/COPYING

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: x264

seat licence file(s) at the pin agree with the cell read

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: x265

seat licence file(s) at the pin agree with the cell read; vendored subtree; compilation not determined at the seat (pass-1 P / vendored texts kept)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: xavs2

seat licence file(s) at the pin agree with the cell read

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: xvid

seat licence file(s) at the pin agree with the cell read

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: xxhash

seat licence file(s) at the pin agree with the cell read; vendored subtree; compilation not determined at the seat: cli/COPYING

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: xz

COPYING: liblzma is 0BSD (the GPL/LGPL files are the CLI tools and getopt, not linked); vendored subtree; compilation not determined at the seat: build-aux/license-check.sh

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: zimg

seat licence file(s) at the pin agree with the cell read

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: zix

seat licence file(s) at the pin agree with the cell read; vendored subtree; compilation not determined at the seat (pass-1 P / vendored texts kept)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg component: zlib

seat licence file(s) at the pin agree with the cell read; vendored subtree; compilation not determined at the seat: contrib/dotzlib/LICENSE_1_0.txt, contrib/minizip/LICENSE.Info-Zip

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: addr2line 0.27.1 (toolchain)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: lock-graph; prebuilt rust-std dependency: included from rust library/Cargo.lock @58cf8f9c target graph (std, backtrace + panic-unwind)
Source evidence: library/Cargo.lock @58cf8f9c; std target graph (backtrace, panic-unwind); binary name string 'addr2line'

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: adler2 2.0.1 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling adler2 v2.0.1' (run 2) + target graph
Source evidence: log #158 'Compiling adler2 v2.0.1'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: adler2 2.0.1 (toolchain)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: lock-graph; prebuilt rust-std dependency: included from rust library/Cargo.lock @58cf8f9c target graph (std, backtrace + panic-unwind)
Source evidence: library/Cargo.lock @58cf8f9c; std target graph (backtrace, panic-unwind)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: ahash 0.8.12 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling ahash v0.8.12' (run 2) + target graph
Source evidence: log #158 'Compiling ahash v0.8.12'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: aho-corasick 1.1.5 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling aho-corasick v1.1.5' (run 2) + target graph
Source evidence: log #158 'Compiling aho-corasick v1.1.5'; resolver target graph; binary 99-librsvg/vendor path string x40/x40 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: aligned 0.4.2 (rav1e)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #87 rustc --target x86_64-pc-windows-gnu unit + line 'Compiling aligned v0.4.2' (run 2)
Source evidence: log #87 rustc --target x86_64-pc-windows-gnu unit (0 features)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: aligned-vec 0.6.4 (rav1e)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #87 rustc --target x86_64-pc-windows-gnu unit + line 'Compiling aligned-vec v0.6.4' (run 2)
Source evidence: log #87 rustc --target x86_64-pc-windows-gnu unit (2 features); binary cargo registry path string x3/x3 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: anstream 0.6.19 (rav1e)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #87 rustc --target x86_64-pc-windows-gnu unit + line 'Compiling anstream v0.6.19' (run 2)
Source evidence: log #87 rustc --target x86_64-pc-windows-gnu unit (3 features)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: anstyle 1.0.11 (rav1e)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #87 rustc --target x86_64-pc-windows-gnu unit + line 'Compiling anstyle v1.0.11' (run 2)
Source evidence: log #87 rustc --target x86_64-pc-windows-gnu unit (2 features)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: anstyle-parse 0.2.7 (rav1e)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #87 rustc --target x86_64-pc-windows-gnu unit + line 'Compiling anstyle-parse v0.2.7' (run 2)
Source evidence: log #87 rustc --target x86_64-pc-windows-gnu unit (2 features)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: anstyle-query 1.1.3 (rav1e)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #87 rustc --target x86_64-pc-windows-gnu unit + line 'Compiling anstyle-query v1.1.3' (run 2)
Source evidence: log #87 rustc --target x86_64-pc-windows-gnu unit (0 features)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: anstyle-wincon 3.0.9 (rav1e)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #87 rustc --target x86_64-pc-windows-gnu unit + line 'Compiling anstyle-wincon v3.0.9' (run 2)
Source evidence: log #87 rustc --target x86_64-pc-windows-gnu unit (0 features)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: anyhow 1.0.98 (rav1e)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #87 rustc --target x86_64-pc-windows-gnu unit + line 'Compiling anyhow v1.0.98' (run 2)
Source evidence: log #87 rustc --target x86_64-pc-windows-gnu unit (2 features)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: approx 0.5.1 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling approx v0.5.1' (run 2) + target graph
Source evidence: log #158 'Compiling approx v0.5.1'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: arrayvec 0.7.6 (rav1e)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #87 rustc --target x86_64-pc-windows-gnu unit + line 'Compiling arrayvec v0.7.6' (run 2)
Source evidence: log #87 rustc --target x86_64-pc-windows-gnu unit (2 features); binary cargo registry path string x1/x1 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: as-slice 0.2.1 (rav1e)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #87 rustc --target x86_64-pc-windows-gnu unit + line 'Compiling as-slice v0.2.1' (run 2)
Source evidence: log #87 rustc --target x86_64-pc-windows-gnu unit (0 features)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: av-data 0.4.4 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling av-data v0.4.4' (run 2) + target graph
Source evidence: log #158 'Compiling av-data v0.4.4'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: av-metrics 0.9.1 (rav1e)

crate ships no licence file; canonical SPDX text(s) at license-list-data v3.29.0; authors: Josh Holmer <jholmer.in@gmail.com>
statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #87 rustc --target x86_64-pc-windows-gnu unit + line 'Compiling av-metrics v0.9.1' (run 2)
Source evidence: log #87 rustc --target x86_64-pc-windows-gnu unit (0 features)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: av-scenechange 0.14.1 (rav1e)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #87 rustc --target x86_64-pc-windows-gnu unit + line 'Compiling av-scenechange v0.14.1' (run 2)
Source evidence: log #87 rustc --target x86_64-pc-windows-gnu unit (4 features); binary cargo registry path string x17/x17 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: av1-grain 0.2.4 (rav1e)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #87 rustc --target x86_64-pc-windows-gnu unit + line 'Compiling av1-grain v0.2.4' (run 2)
Source evidence: log #87 rustc --target x86_64-pc-windows-gnu unit (8 features)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: backtrace 0.3.76 (toolchain)

git submodule library/backtrace of rust-lang/rust @58cf8f9c (gitlink d902726a), compiled into std via #[path]
statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: binary; prebuilt toolchain component, no run-2 compile line and no lock: rests on the PE import table / binary strings in 'evidence' plus the toolchain facts (version, link flags)
Source evidence: binary 'RUST_BACKTRACE' strings (x6); std 'backtrace' feature (gimli/addr2line names present)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: bitflags 2.13.2 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling bitflags v2.13.2' (run 2) + target graph
Source evidence: log #158 'Compiling bitflags v2.13.2'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: bitreader 0.3.11 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling bitreader v0.3.11' (run 2) + target graph
Source evidence: log #158 'Compiling bitreader v0.3.11'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: bitstream-io 4.2.0 (rav1e)

declared 'MIT/Apache-2.0' (legacy '/' = OR)
statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #87 rustc --target x86_64-pc-windows-gnu unit + line 'Compiling bitstream-io v4.2.0' (run 2)
Source evidence: log #87 rustc --target x86_64-pc-windows-gnu unit (2 features); binary cargo registry path string x1/x1 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: byte-slice-cast 1.2.3 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling byte-slice-cast v1.2.3' (run 2) + target graph
Source evidence: log #158 'Compiling byte-slice-cast v1.2.3'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: bytemuck 1.25.2 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling bytemuck v1.25.2' (run 2) + target graph
Source evidence: log #158 'Compiling bytemuck v1.25.2'; resolver target graph; binary 99-librsvg/vendor path string x1/x1 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: byteorder 1.5.0 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling byteorder v1.5.0' (run 2) + target graph
Source evidence: log #158 'Compiling byteorder v1.5.0'; resolver target graph; binary 99-librsvg/vendor path string x2/x2 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: byteorder-lite 0.1.0 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling byteorder-lite v0.1.0' (run 2) + target graph
Source evidence: log #158 'Compiling byteorder-lite v0.1.0'; resolver target graph; binary 99-librsvg/vendor path string x2/x2 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: bytes 1.12.1 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling bytes v1.12.1' (run 2) + target graph
Source evidence: log #158 'Compiling bytes v1.12.1'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: cairo-rs 0.22.9 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling cairo-rs v0.22.9' (run 2) + target graph
Source evidence: log #158 'Compiling cairo-rs v0.22.9'; resolver target graph; binary 99-librsvg/vendor path string x19/x19 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: cairo-sys-rs 0.22.9 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling cairo-sys-rs v0.22.9' (run 2) + target graph
Source evidence: log #158 'Compiling cairo-sys-rs v0.22.9'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: cast 0.3.0 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling cast v0.3.0' (run 2) + target graph
Source evidence: log #158 'Compiling cast v0.3.0'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: cfg-if 1.0.1 (rav1e)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #87 rustc --target x86_64-pc-windows-gnu unit + line 'Compiling cfg-if v1.0.1' (run 2)
Source evidence: log #87 rustc --target x86_64-pc-windows-gnu unit (0 features)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: cfg-if 1.0.4 (toolchain)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: lock-graph; prebuilt rust-std dependency: included from rust library/Cargo.lock @58cf8f9c target graph (std, backtrace + panic-unwind)
Source evidence: library/Cargo.lock @58cf8f9c; std target graph (backtrace, panic-unwind)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: cfg-if 1.0.5 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling cfg-if v1.0.5' (run 2) + target graph
Source evidence: log #158 'Compiling cfg-if v1.0.5'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: clap 4.5.40 (rav1e)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #87 rustc --target x86_64-pc-windows-gnu unit + line 'Compiling clap v4.5.40' (run 2)
Source evidence: log #87 rustc --target x86_64-pc-windows-gnu unit (4 features)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: clap_builder 4.5.40 (rav1e)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #87 rustc --target x86_64-pc-windows-gnu unit + line 'Compiling clap_builder v4.5.40' (run 2)
Source evidence: log #87 rustc --target x86_64-pc-windows-gnu unit (4 features)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: clap_complete 4.5.54 (rav1e)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #87 rustc --target x86_64-pc-windows-gnu unit + line 'Compiling clap_complete v4.5.54' (run 2)
Source evidence: log #87 rustc --target x86_64-pc-windows-gnu unit (1 features)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: clap_lex 0.7.5 (rav1e)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #87 rustc --target x86_64-pc-windows-gnu unit + line 'Compiling clap_lex v0.7.5' (run 2)
Source evidence: log #87 rustc --target x86_64-pc-windows-gnu unit (0 features)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: color_quant 1.1.0 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling color_quant v1.1.0' (run 2) + target graph
Source evidence: log #158 'Compiling color_quant v1.1.0'; resolver target graph; binary 99-librsvg/vendor path string x2/x2 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: colorchoice 1.0.4 (rav1e)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #87 rustc --target x86_64-pc-windows-gnu unit + line 'Compiling colorchoice v1.0.4' (run 2)
Source evidence: log #87 rustc --target x86_64-pc-windows-gnu unit (0 features)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: compiler_builtins 0.1.160 (toolchain)

in-tree (library/compiler-builtins); derived in part from LLVM compiler-rt; LICENSE.txt carries MIT, Apache-2.0 and the LLVM exception; LLVM-exception only adds permissions (CHARC confirmed compatible, second addendum)
statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: lock-graph; path package of rust library/Cargo.lock @58cf8f9c (alloc -> compiler_builtins); no byte proof of its own
Source evidence: std dependency (alloc -> compiler_builtins) in library/Cargo.lock; every Rust staticlib carries it

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: console 0.15.11 (rav1e)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #87 rustc --target x86_64-pc-windows-gnu unit + line 'Compiling console v0.15.11' (run 2)
Source evidence: log #87 rustc --target x86_64-pc-windows-gnu unit (3 features)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: core2 0.4.0 (rav1e)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #87 rustc --target x86_64-pc-windows-gnu unit + line 'Compiling core2 v0.4.0' (run 2)
Source evidence: log #87 rustc --target x86_64-pc-windows-gnu unit (3 features)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: core_detect 1.0.0 (librsvg)

declared 'MIT/Apache-2.0' (legacy '/' = OR)
statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling core_detect v1.0.0' (run 2) + target graph
Source evidence: log #158 'Compiling core_detect v1.0.0'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: crc32fast 1.5.3 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling crc32fast v1.5.3' (run 2) + target graph
Source evidence: log #158 'Compiling crc32fast v1.5.3'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: crossbeam 0.8.4 (rav1e)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #87 rustc --target x86_64-pc-windows-gnu unit + line 'Compiling crossbeam v0.8.4' (run 2)
Source evidence: log #87 rustc --target x86_64-pc-windows-gnu unit (7 features)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: crossbeam-channel 0.5.15 (rav1e)

ships LICENSE-THIRD-PARTY (third-party notices carried as a text)
statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #87 rustc --target x86_64-pc-windows-gnu unit + line 'Compiling crossbeam-channel v0.5.15' (run 2)
Source evidence: log #87 rustc --target x86_64-pc-windows-gnu unit (1 features)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: crossbeam-deque 0.8.6 (rav1e)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #87 rustc --target x86_64-pc-windows-gnu unit + line 'Compiling crossbeam-deque v0.8.6' (run 2)
Source evidence: log #87 rustc --target x86_64-pc-windows-gnu unit (2 features); binary cargo registry path string x1/x1 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: crossbeam-deque 0.8.8 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling crossbeam-deque v0.8.8' (run 2) + target graph
Source evidence: log #158 'Compiling crossbeam-deque v0.8.8'; resolver target graph; binary 99-librsvg/vendor path string x1/x1 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: crossbeam-epoch 0.9.18 (rav1e)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #87 rustc --target x86_64-pc-windows-gnu unit + line 'Compiling crossbeam-epoch v0.9.18' (run 2)
Source evidence: log #87 rustc --target x86_64-pc-windows-gnu unit (2 features); binary cargo registry path string x6/x6 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: crossbeam-epoch 0.9.21 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling crossbeam-epoch v0.9.21' (run 2) + target graph
Source evidence: log #158 'Compiling crossbeam-epoch v0.9.21'; resolver target graph; binary 99-librsvg/vendor path string x6/x6 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: crossbeam-queue 0.3.12 (rav1e)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #87 rustc --target x86_64-pc-windows-gnu unit + line 'Compiling crossbeam-queue v0.3.12' (run 2)
Source evidence: log #87 rustc --target x86_64-pc-windows-gnu unit (2 features)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: crossbeam-utils 0.8.21 (rav1e)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #87 rustc --target x86_64-pc-windows-gnu unit + line 'Compiling crossbeam-utils v0.8.21' (run 2)
Source evidence: log #87 rustc --target x86_64-pc-windows-gnu unit (2 features)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: crossbeam-utils 0.8.23 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling crossbeam-utils v0.8.23' (run 2) + target graph
Source evidence: log #158 'Compiling crossbeam-utils v0.8.23'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: cssparser 0.37.0 (librsvg)

MPL-2.0 s3.2: the notice must say where the Source Code Form is available (source_url); no Incompatible-With-Secondary-Licenses notice; combined under GPL-3.0 per MPL-2.0 section 3.3
MPL-2.0 (secondary licence: GPL-3.0 permitted, section 3.3)
statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling cssparser v0.37.0' (run 2) + target graph
Source evidence: log #158 'Compiling cssparser v0.37.0'; resolver target graph; binary 99-librsvg/vendor path string x19/x19 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: cssparser-color 0.5.0 (librsvg)

MPL-2.0 s3.2: the notice must say where the Source Code Form is available (source_url); no Incompatible-With-Secondary-Licenses notice; combined under GPL-3.0 per MPL-2.0 section 3.3
MPL-2.0 (secondary licence: GPL-3.0 permitted, section 3.3)
statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling cssparser-color v0.5.0' (run 2) + target graph
Source evidence: log #158 'Compiling cssparser-color v0.5.0'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: data-url 0.3.2 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling data-url v0.3.2' (run 2) + target graph
Source evidence: log #158 'Compiling data-url v0.3.2'; resolver target graph; binary 99-librsvg/vendor path string x1/x1 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: dav1d 0.11.1 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling dav1d v0.11.1' (run 2) + target graph
Source evidence: log #158 'Compiling dav1d v0.11.1'; resolver target graph; binary 99-librsvg/vendor path string x5/x5 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: dav1d-sys 0.8.3 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling dav1d-sys v0.8.3' (run 2) + target graph
Source evidence: log #158 'Compiling dav1d-sys v0.8.3'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: derive_more 2.1.1 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling derive_more v2.1.1' (run 2) + target graph
Source evidence: log #158 'Compiling derive_more v2.1.1'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: dtoa 1.0.11 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling dtoa v1.0.11' (run 2) + target graph
Source evidence: log #158 'Compiling dtoa v1.0.11'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: dtoa-short 0.3.5 (librsvg)

MPL-2.0 s3.2: the notice must say where the Source Code Form is available (source_url); no Incompatible-With-Secondary-Licenses notice; combined under GPL-3.0 per MPL-2.0 section 3.3
MPL-2.0 (secondary licence: GPL-3.0 permitted, section 3.3)
statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling dtoa-short v0.3.5' (run 2) + target graph
Source evidence: log #158 'Compiling dtoa-short v0.3.5'; resolver target graph; binary 99-librsvg/vendor path string x2/x2 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: either 1.15.0 (rav1e)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #87 rustc --target x86_64-pc-windows-gnu unit + line 'Compiling either v1.15.0' (run 2)
Source evidence: log #87 rustc --target x86_64-pc-windows-gnu unit (2 features)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: either 1.19.0 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling either v1.19.0' (run 2) + target graph
Source evidence: log #158 'Compiling either v1.19.0'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: encode_unicode 1.0.0 (rav1e)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #87 rustc --target x86_64-pc-windows-gnu unit + line 'Compiling encode_unicode v1.0.0' (run 2)
Source evidence: log #87 rustc --target x86_64-pc-windows-gnu unit (2 features)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: encoding_rs 0.8.42 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling encoding_rs v0.8.42' (run 2) + target graph
Source evidence: log #158 'Compiling encoding_rs v0.8.42'; resolver target graph; binary 99-librsvg/vendor path string x23/x23 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: equator 0.4.2 (rav1e)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #87 rustc --target x86_64-pc-windows-gnu unit + line 'Compiling equator v0.4.2' (run 2)
Source evidence: log #87 rustc --target x86_64-pc-windows-gnu unit (0 features); binary cargo registry path string x1/x1 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: fallible_collections 0.4.9 (librsvg)

declared 'MIT/Apache-2.0' (legacy '/' = OR)
statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling fallible_collections v0.4.9' (run 2) + target graph
Source evidence: log #158 'Compiling fallible_collections v0.4.9'; resolver target graph; binary 99-librsvg/vendor path string x5/x5 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: fdeflate 0.3.7 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling fdeflate v0.3.7' (run 2) + target graph
Source evidence: log #158 'Compiling fdeflate v0.3.7'; resolver target graph; binary 99-librsvg/vendor path string x4/x4 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: fern 0.7.1 (rav1e)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #87 rustc --target x86_64-pc-windows-gnu unit + line 'Compiling fern v0.7.1' (run 2)
Source evidence: log #87 rustc --target x86_64-pc-windows-gnu unit (0 features)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: flate2 1.1.10 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling flate2 v1.1.10' (run 2) + target graph
Source evidence: log #158 'Compiling flate2 v1.1.10'; resolver target graph; binary 99-librsvg/vendor path string x4/x4 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: float-cmp 0.10.0 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling float-cmp v0.10.0' (run 2) + target graph
Source evidence: log #158 'Compiling float-cmp v0.10.0'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: form_urlencoded 1.2.2 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling form_urlencoded v1.2.2' (run 2) + target graph
Source evidence: log #158 'Compiling form_urlencoded v1.2.2'; resolver target graph; binary 99-librsvg/vendor path string x1/x1 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: futures-channel 0.3.34 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling futures-channel v0.3.34' (run 2) + target graph
Source evidence: log #158 'Compiling futures-channel v0.3.34'; resolver target graph; binary 99-librsvg/vendor path string x4/x4 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: futures-core 0.3.34 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling futures-core v0.3.34' (run 2) + target graph
Source evidence: log #158 'Compiling futures-core v0.3.34'; resolver target graph; binary 99-librsvg/vendor path string x1/x1 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: futures-executor 0.3.34 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling futures-executor v0.3.34' (run 2) + target graph
Source evidence: log #158 'Compiling futures-executor v0.3.34'; resolver target graph; binary 99-librsvg/vendor path string x2/x2 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: futures-io 0.3.34 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling futures-io v0.3.34' (run 2) + target graph
Source evidence: log #158 'Compiling futures-io v0.3.34'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: futures-task 0.3.34 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling futures-task v0.3.34' (run 2) + target graph
Source evidence: log #158 'Compiling futures-task v0.3.34'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: futures-util 0.3.34 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling futures-util v0.3.34' (run 2) + target graph
Source evidence: log #158 'Compiling futures-util v0.3.34'; resolver target graph; binary 99-librsvg/vendor path string x4/x4 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: gif 0.14.2 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling gif v0.14.2' (run 2) + target graph
Source evidence: log #158 'Compiling gif v0.14.2'; resolver target graph; binary 99-librsvg/vendor path string x5/x5 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: gimli 0.34.0 (toolchain)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: lock-graph; prebuilt rust-std dependency: included from rust library/Cargo.lock @58cf8f9c target graph (std, backtrace + panic-unwind)
Source evidence: library/Cargo.lock @58cf8f9c; std target graph (backtrace, panic-unwind); binary name string 'gimli'

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: gio 0.22.10 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling gio v0.22.10' (run 2) + target graph
Source evidence: log #158 'Compiling gio v0.22.10'; resolver target graph; binary 99-librsvg/vendor path string x156/x156 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: gio-sys 0.22.9 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling gio-sys v0.22.9' (run 2) + target graph
Source evidence: log #158 'Compiling gio-sys v0.22.9'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: glib 0.22.10 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling glib v0.22.10' (run 2) + target graph
Source evidence: log #158 'Compiling glib v0.22.10'; resolver target graph; binary 99-librsvg/vendor path string x83/x83 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: glib-sys 0.22.9 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling glib-sys v0.22.9' (run 2) + target graph
Source evidence: log #158 'Compiling glib-sys v0.22.9'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: gobject-sys 0.22.9 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling gobject-sys v0.22.9' (run 2) + target graph
Source evidence: log #158 'Compiling gobject-sys v0.22.9'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: hashbrown 0.13.2 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling hashbrown v0.13.2' (run 2) + target graph
Source evidence: log #158 'Compiling hashbrown v0.13.2'; resolver target graph; binary 99-librsvg/vendor path string x1/x1 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: hashbrown 0.17.1 (toolchain)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: lock-graph; prebuilt rust-std dependency: included from rust library/Cargo.lock @58cf8f9c target graph (std, backtrace + panic-unwind)
Source evidence: library/Cargo.lock @58cf8f9c; std target graph (backtrace, panic-unwind); binary name string 'hashbrown'

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: icu_collections 2.4.0 (librsvg)

Unicode License v3 (UNICODE LICENSE V3 text shipped); CHARC ruled Unicode-3.0 COMPATIBLE (second addendum)
statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling icu_collections v2.4.0' (run 2) + target graph
Source evidence: log #158 'Compiling icu_collections v2.4.0'; resolver target graph; binary 99-librsvg/vendor path string x3/x3 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: icu_locale_core 2.4.0 (librsvg)

Unicode License v3 (UNICODE LICENSE V3 text shipped); CHARC ruled Unicode-3.0 COMPATIBLE (second addendum)
statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling icu_locale_core v2.4.0' (run 2) + target graph
Source evidence: log #158 'Compiling icu_locale_core v2.4.0'; resolver target graph; binary 99-librsvg/vendor path string x1/x1 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: icu_normalizer 2.4.0 (librsvg)

Unicode License v3 (UNICODE LICENSE V3 text shipped); CHARC ruled Unicode-3.0 COMPATIBLE (second addendum)
statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling icu_normalizer v2.4.0' (run 2) + target graph
Source evidence: log #158 'Compiling icu_normalizer v2.4.0'; resolver target graph; binary 99-librsvg/vendor path string x2/x2 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: icu_normalizer_data 2.4.0 (librsvg)

Unicode License v3 (UNICODE LICENSE V3 text shipped); CHARC ruled Unicode-3.0 COMPATIBLE (second addendum)
statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling icu_normalizer_data v2.4.0' (run 2) + target graph
Source evidence: log #158 'Compiling icu_normalizer_data v2.4.0'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: icu_properties 2.4.0 (librsvg)

Unicode License v3 (UNICODE LICENSE V3 text shipped); CHARC ruled Unicode-3.0 COMPATIBLE (second addendum)
statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling icu_properties v2.4.0' (run 2) + target graph
Source evidence: log #158 'Compiling icu_properties v2.4.0'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: icu_properties_data 2.4.0 (librsvg)

Unicode License v3 (UNICODE LICENSE V3 text shipped); CHARC ruled Unicode-3.0 COMPATIBLE (second addendum)
statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling icu_properties_data v2.4.0' (run 2) + target graph
Source evidence: log #158 'Compiling icu_properties_data v2.4.0'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: icu_provider 2.4.0 (librsvg)

Unicode License v3 (UNICODE LICENSE V3 text shipped); CHARC ruled Unicode-3.0 COMPATIBLE (second addendum)
statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling icu_provider v2.4.0' (run 2) + target graph
Source evidence: log #158 'Compiling icu_provider v2.4.0'; resolver target graph; binary 99-librsvg/vendor path string x2/x2 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: idna 1.1.0 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling idna v1.1.0' (run 2) + target graph
Source evidence: log #158 'Compiling idna v1.1.0'; resolver target graph; binary 99-librsvg/vendor path string x3/x3 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: idna_adapter 1.2.2 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling idna_adapter v1.2.2' (run 2) + target graph
Source evidence: log #158 'Compiling idna_adapter v1.2.2'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: image 0.25.10 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling image v0.25.10' (run 2) + target graph
Source evidence: log #158 'Compiling image v0.25.10'; resolver target graph; binary 99-librsvg/vendor path string x39/x39 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: image-webp 0.2.4 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling image-webp v0.2.4' (run 2) + target graph
Source evidence: log #158 'Compiling image-webp v0.2.4'; resolver target graph; binary 99-librsvg/vendor path string x21/x21 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: is_terminal_polyfill 1.70.1 (rav1e)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #87 rustc --target x86_64-pc-windows-gnu unit + line 'Compiling is_terminal_polyfill v1.70.1' (run 2)
Source evidence: log #87 rustc --target x86_64-pc-windows-gnu unit (1 features)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: itertools 0.10.5 (rav1e)

declared 'MIT/Apache-2.0' (legacy '/' = OR)
statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #87 rustc --target x86_64-pc-windows-gnu unit + line 'Compiling itertools v0.10.5' (run 2)
Source evidence: log #87 rustc --target x86_64-pc-windows-gnu unit (3 features)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: itertools 0.14.0 (rav1e)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #87 rustc --target x86_64-pc-windows-gnu unit + line 'Compiling itertools v0.14.0' (run 2)
Source evidence: log #87 rustc --target x86_64-pc-windows-gnu unit (3 features)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: itertools 0.15.0 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling itertools v0.15.0' (run 2) + target graph
Source evidence: log #158 'Compiling itertools v0.15.0'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: itoa 1.0.18 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling itoa v1.0.18' (run 2) + target graph
Source evidence: log #158 'Compiling itoa v1.0.18'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: lab 0.11.0 (rav1e)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #87 rustc --target x86_64-pc-windows-gnu unit + line 'Compiling lab v0.11.0' (run 2)
Source evidence: log #87 rustc --target x86_64-pc-windows-gnu unit (0 features)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: language-tags 0.3.2 (librsvg)

declared 'MIT/Apache-2.0' (legacy '/' = OR)
licence chosen: MIT
statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling language-tags v0.3.2' (run 2) + target graph
Source evidence: log #158 'Compiling language-tags v0.3.2'; resolver target graph; binary 99-librsvg/vendor path string x2/x2 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: lazy_static 1.5.1 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling lazy_static v1.5.1' (run 2) + target graph
Source evidence: log #158 'Compiling lazy_static v1.5.1'; resolver target graph; binary 99-librsvg/vendor path string x1/x1 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: libc 0.2.172 (rav1e)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #87 rustc --target x86_64-pc-windows-gnu unit + line 'Compiling libc v0.2.172' (run 2)
Source evidence: log #87 rustc --target x86_64-pc-windows-gnu unit (2 features)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: libc 0.2.189 (toolchain)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: lock-graph; prebuilt rust-std dependency: included from rust library/Cargo.lock @58cf8f9c target graph (std, backtrace + panic-unwind)
Source evidence: library/Cargo.lock @58cf8f9c; std target graph (backtrace, panic-unwind)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: libc 0.2.191 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling libc v0.2.191' (run 2) + target graph
Source evidence: log #158 'Compiling libc v0.2.191'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: libgcc 16.2.0 (toolchain)

crosstool-NG 1.29.0.7_b1a94f6 GCC 16.2.0; tag releases/gcc-16.2.0 = tag object 1831ac03 -> commit 78d4ac73
statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: binary; prebuilt toolchain component, no run-2 compile line and no lock: rests on the PE import table / binary strings in 'evidence' plus the toolchain facts (version, link flags)
Source evidence: always linked by the gcc driver (-static-libgcc in CFLAGS/LDFLAGS; libgcc + libgcc_eh); Rust std's unwind needs _Unwind_* (gcc_eh); no libgcc_s*.dll imported

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: libgomp 16.2.0 (toolchain)

crosstool-NG 1.29.0.7_b1a94f6 GCC 16.2.0; tag releases/gcc-16.2.0 = tag object 1831ac03 -> commit 78d4ac73
statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: binary; prebuilt toolchain component, no run-2 compile line and no lock: rests on the PE import table / binary strings in 'evidence' plus the toolchain facts (version, link flags)
Source evidence: FFmpeg configure --extra-libs=-lgomp; strings 'libgomp: fatal error: error directive encountered: ', '.../src/gcc/libgomp/task.c' (5 libgomp source paths); no libgomp*.dll imported

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: libm 0.2.16 (toolchain)

no linkage proof (superset). SUPERSET-ONLY: libm sources are compiled into compiler_builtins' math module; whether any routine survives into the exe is not settled; LICENSE.txt carries the musl and Sun notices
carried as a superset of the static link; linkage not proven
Census basis: lock-graph; no linkage proof (superset) (CHARC second addendum (c))
Source evidence: compiler_builtins includes libm via #[path]; no binary proof

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: libstdc++ (fast_float) 16.2.0 (toolchain)

no linkage proof (superset). SUPERSET-ONLY: fast_float (upstream merge 2ef9abbc) inside libstdc++'s floating_from_chars; its MIT notice is in the header (L1-40 excerpt); presence not decidable from bytes (Rust core's dec2flt carries the same power-of-five table)
licence chosen: MIT
carried as a superset of the static link; linkage not proven
Census basis: lock-graph; no linkage proof (superset) (CHARC second addendum (c))
Source evidence: superset: no distinguishing byte evidence

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: libstdc++ (Ryu) 16.2.0 (toolchain)

Ryu (Ulf Adams; upstream merge 150d0c87) inside libstdc++'s floating_to_chars; licence stated in the file headers only (no LICENSE file in the gcc tree): header excerpt + canonical Apache-2.0 text
licence chosen: Apache-2.0
statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: binary; prebuilt toolchain component, no run-2 compile line and no lock: rests on the PE import table / binary strings in 'evidence' plus the toolchain facts (version, link flags)
Source evidence: binary carries Ryu's DOUBLE_POW5_INV_SPLIT and DOUBLE_POW5_SPLIT tables (3 x 48-byte probes each, x1 per exe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: libstdc++ 16.2.0 (toolchain)

crosstool-NG 1.29.0.7_b1a94f6 GCC 16.2.0; tag releases/gcc-16.2.0 = tag object 1831ac03 -> commit 78d4ac73; also carries the 8 distinct HP (1994) / SGI (1996-1999) permission notices of bits/stl_*.h as line-range excerpts (CHARC second addendum)
statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: binary; prebuilt toolchain component, no run-2 compile line and no lock: rests on the PE import table / binary strings in 'evidence' plus the toolchain facts (version, link flags)
Source evidence: -static-libstdc++; strings 'basic_string::_M_create' (x626 basic_string::*), 'vector::_M_realloc_append', '__gnu_cxx::__concurrence_lock_error', typeinfo 'std::bad_alloc'; no libstdc++*.dll imported

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: litemap 0.8.3 (librsvg)

Unicode License v3 (UNICODE LICENSE V3 text shipped); CHARC ruled Unicode-3.0 COMPATIBLE (second addendum)
statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling litemap v0.8.3' (run 2) + target graph
Source evidence: log #158 'Compiling litemap v0.8.3'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: locale_config 0.3.0 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling locale_config v0.3.0' (run 2) + target graph
Source evidence: log #158 'Compiling locale_config v0.3.0'; resolver target graph; binary 99-librsvg/vendor path string x3/x3 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: lock_api 0.4.14 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling lock_api v0.4.14' (run 2) + target graph
Source evidence: log #158 'Compiling lock_api v0.4.14'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: log 0.4.34 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling log v0.4.34' (run 2) + target graph
Source evidence: log #158 'Compiling log v0.4.34'; resolver target graph; binary 99-librsvg/vendor path string x1/x1 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: log 0.4.34 (rav1e)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #87 rustc --target x86_64-pc-windows-gnu unit + line 'Compiling log v0.4.34' (run 2)
Source evidence: log #87 rustc --target x86_64-pc-windows-gnu unit (2 features)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: markup5ever 0.39.0 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling markup5ever v0.39.0' (run 2) + target graph
Source evidence: log #158 'Compiling markup5ever v0.39.0'; resolver target graph; binary 99-librsvg/vendor path string x2/x2 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: matrixmultiply 0.3.11 (librsvg)

declared 'MIT/Apache-2.0' (legacy '/' = OR)
statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling matrixmultiply v0.3.11' (run 2) + target graph
Source evidence: log #158 'Compiling matrixmultiply v0.3.11'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: maybe-rayon 0.1.1 (rav1e)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #87 rustc --target x86_64-pc-windows-gnu unit + line 'Compiling maybe-rayon v0.1.1' (run 2)
Source evidence: log #87 rustc --target x86_64-pc-windows-gnu unit (2 features)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: memchr 2.7.5 (rav1e)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #87 rustc --target x86_64-pc-windows-gnu unit + line 'Compiling memchr v2.7.5' (run 2)
Source evidence: log #87 rustc --target x86_64-pc-windows-gnu unit (2 features)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: memchr 2.8.3 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling memchr v2.8.3' (run 2) + target graph
Source evidence: log #158 'Compiling memchr v2.8.3'; resolver target graph; binary 99-librsvg/vendor path string x11/x11 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: memchr 2.8.3 (toolchain)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: lock-graph; prebuilt rust-std dependency: included from rust library/Cargo.lock @58cf8f9c target graph (std, backtrace + panic-unwind)
Source evidence: library/Cargo.lock @58cf8f9c; std target graph (backtrace, panic-unwind)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: minimal-lexical 0.2.1 (rav1e)

declared 'MIT/Apache-2.0' (legacy '/' = OR)
statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #87 rustc --target x86_64-pc-windows-gnu unit + line 'Compiling minimal-lexical v0.2.1' (run 2)
Source evidence: log #87 rustc --target x86_64-pc-windows-gnu unit (1 features)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: miniz_oxide 0.8.9 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling miniz_oxide v0.8.9' (run 2) + target graph
Source evidence: log #158 'Compiling miniz_oxide v0.8.9'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: miniz_oxide 0.9.1 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling miniz_oxide v0.9.1' (run 2) + target graph
Source evidence: log #158 'Compiling miniz_oxide v0.9.1'; resolver target graph; binary 99-librsvg/vendor path string x7/x7 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: miniz_oxide 0.9.1 (toolchain)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: lock-graph; prebuilt rust-std dependency: included from rust library/Cargo.lock @58cf8f9c target graph (std, backtrace + panic-unwind)
Source evidence: library/Cargo.lock @58cf8f9c; std target graph (backtrace, panic-unwind); binary name string 'miniz_oxide'

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: moxcms 0.8.1 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling moxcms v0.8.1' (run 2) + target graph
Source evidence: log #158 'Compiling moxcms v0.8.1'; resolver target graph; binary 99-librsvg/vendor path string x30/x30 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: mp4parse 0.17.0 (librsvg)

MPL-2.0 s3.2: the notice must say where the Source Code Form is available (source_url); no Incompatible-With-Secondary-Licenses notice; combined under GPL-3.0 per MPL-2.0 section 3.3
MPL-2.0 (secondary licence: GPL-3.0 permitted, section 3.3)
statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling mp4parse v0.17.0' (run 2) + target graph
Source evidence: log #158 'Compiling mp4parse v0.17.0'; resolver target graph; binary 99-librsvg/vendor path string x6/x6 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: nalgebra 0.35.0 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling nalgebra v0.35.0' (run 2) + target graph
Source evidence: log #158 'Compiling nalgebra v0.35.0'; resolver target graph; binary 99-librsvg/vendor path string x3/x3 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: new_debug_unreachable 1.0.6 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling new_debug_unreachable v1.0.6' (run 2) + target graph
Source evidence: log #158 'Compiling new_debug_unreachable v1.0.6'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: new_debug_unreachable 1.0.6 (rav1e)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #87 rustc --target x86_64-pc-windows-gnu unit + line 'Compiling new_debug_unreachable v1.0.6' (run 2)
Source evidence: log #87 rustc --target x86_64-pc-windows-gnu unit (0 features)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: nom 7.1.3 (rav1e)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #87 rustc --target x86_64-pc-windows-gnu unit + line 'Compiling nom v7.1.3' (run 2)
Source evidence: log #87 rustc --target x86_64-pc-windows-gnu unit (3 features)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: nom 8.0.0 (rav1e)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #87 rustc --target x86_64-pc-windows-gnu unit + line 'Compiling nom v8.0.0' (run 2)
Source evidence: log #87 rustc --target x86_64-pc-windows-gnu unit (3 features)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: num-bigint 0.4.6 (rav1e)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #87 rustc --target x86_64-pc-windows-gnu unit + line 'Compiling num-bigint v0.4.6' (run 2)
Source evidence: log #87 rustc --target x86_64-pc-windows-gnu unit (1 features)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: num-bigint 0.4.8 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling num-bigint v0.4.8' (run 2) + target graph
Source evidence: log #158 'Compiling num-bigint v0.4.8'; resolver target graph; binary 99-librsvg/vendor path string x24/x24 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: num-complex 0.4.6 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling num-complex v0.4.6' (run 2) + target graph
Source evidence: log #158 'Compiling num-complex v0.4.6'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: num-integer 0.1.46 (rav1e)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #87 rustc --target x86_64-pc-windows-gnu unit + line 'Compiling num-integer v0.1.46' (run 2)
Source evidence: log #87 rustc --target x86_64-pc-windows-gnu unit (2 features)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: num-integer 0.1.47 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling num-integer v0.1.47' (run 2) + target graph
Source evidence: log #158 'Compiling num-integer v0.1.47'; resolver target graph; binary 99-librsvg/vendor path string x2/x2 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: num-rational 0.4.2 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling num-rational v0.4.2' (run 2) + target graph
Source evidence: log #158 'Compiling num-rational v0.4.2'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: num-rational 0.4.2 (rav1e)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #87 rustc --target x86_64-pc-windows-gnu unit + line 'Compiling num-rational v0.4.2' (run 2)
Source evidence: log #87 rustc --target x86_64-pc-windows-gnu unit (3 features); binary cargo registry path string x1/x1 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: num-traits 0.2.19 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling num-traits v0.2.19' (run 2) + target graph
Source evidence: log #158 'Compiling num-traits v0.2.19'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: num-traits 0.2.19 (rav1e)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #87 rustc --target x86_64-pc-windows-gnu unit + line 'Compiling num-traits v0.2.19' (run 2)
Source evidence: log #87 rustc --target x86_64-pc-windows-gnu unit (3 features)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: object 0.39.1 (toolchain)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: lock-graph; prebuilt rust-std dependency: included from rust library/Cargo.lock @58cf8f9c target graph (std, backtrace + panic-unwind)
Source evidence: library/Cargo.lock @58cf8f9c; std target graph (backtrace, panic-unwind)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: once_cell 1.21.3 (rav1e)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #87 rustc --target x86_64-pc-windows-gnu unit + line 'Compiling once_cell v1.21.3' (run 2)
Source evidence: log #87 rustc --target x86_64-pc-windows-gnu unit (4 features)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: once_cell 1.21.4 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling once_cell v1.21.4' (run 2) + target graph
Source evidence: log #158 'Compiling once_cell v1.21.4'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: once_cell_polyfill 1.70.1 (rav1e)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #87 rustc --target x86_64-pc-windows-gnu unit + line 'Compiling once_cell_polyfill v1.70.1' (run 2)
Source evidence: log #87 rustc --target x86_64-pc-windows-gnu unit (1 features)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: pango 0.22.9 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling pango v0.22.9' (run 2) + target graph
Source evidence: log #158 'Compiling pango v0.22.9'; resolver target graph; binary 99-librsvg/vendor path string x41/x41 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: pango-sys 0.22.9 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling pango-sys v0.22.9' (run 2) + target graph
Source evidence: log #158 'Compiling pango-sys v0.22.9'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: pangocairo 0.22.9 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling pangocairo v0.22.9' (run 2) + target graph
Source evidence: log #158 'Compiling pangocairo v0.22.9'; resolver target graph; binary 99-librsvg/vendor path string x2/x2 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: pangocairo-sys 0.22.9 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling pangocairo-sys v0.22.9' (run 2) + target graph
Source evidence: log #158 'Compiling pangocairo-sys v0.22.9'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: parking_lot 0.12.5 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling parking_lot v0.12.5' (run 2) + target graph
Source evidence: log #158 'Compiling parking_lot v0.12.5'; resolver target graph; binary 99-librsvg/vendor path string x1/x1 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: parking_lot_core 0.9.12 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling parking_lot_core v0.9.12' (run 2) + target graph
Source evidence: log #158 'Compiling parking_lot_core v0.9.12'; resolver target graph; binary 99-librsvg/vendor path string x4/x4 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: percent-encoding 2.3.2 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling percent-encoding v2.3.2' (run 2) + target graph
Source evidence: log #158 'Compiling percent-encoding v2.3.2'; resolver target graph; binary 99-librsvg/vendor path string x1/x1 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: phf 0.13.1 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling phf v0.13.1' (run 2) + target graph
Source evidence: log #158 'Compiling phf v0.13.1'; resolver target graph; binary 99-librsvg/vendor path string x3/x3 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: phf_shared 0.13.1 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling phf_shared v0.13.1' (run 2) + target graph
Source evidence: log #158 'Compiling phf_shared v0.13.1'; resolver target graph; binary 99-librsvg/vendor path string x5/x5 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: phf_shared 0.14.0 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling phf_shared v0.14.0' (run 2) + target graph
Source evidence: log #158 'Compiling phf_shared v0.14.0'; resolver target graph; binary 99-librsvg/vendor path string x1/x1 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: pin-project-lite 0.2.17 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling pin-project-lite v0.2.17' (run 2) + target graph
Source evidence: log #158 'Compiling pin-project-lite v0.2.17'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: png 0.18.1 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling png v0.18.1' (run 2) + target graph
Source evidence: log #158 'Compiling png v0.18.1'; resolver target graph; binary 99-librsvg/vendor path string x21/x21 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: potential_utf 0.1.6 (librsvg)

Unicode License v3 (UNICODE LICENSE V3 text shipped); CHARC ruled Unicode-3.0 COMPATIBLE (second addendum)
statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling potential_utf v0.1.6' (run 2) + target graph
Source evidence: log #158 'Compiling potential_utf v0.1.6'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: precomputed-hash 0.1.1 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling precomputed-hash v0.1.1' (run 2) + target graph
Source evidence: log #158 'Compiling precomputed-hash v0.1.1'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: profiling 1.0.16 (rav1e)

crate ships no licence file; canonical SPDX text(s) at license-list-data v3.29.0; authors: Philip Degarmo <aclysma@gmail.com>
statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #87 rustc --target x86_64-pc-windows-gnu unit + line 'Compiling profiling v1.0.16' (run 2)
Source evidence: log #87 rustc --target x86_64-pc-windows-gnu unit (3 features)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: pxfm 0.1.30 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling pxfm v0.1.30' (run 2) + target graph
Source evidence: log #158 'Compiling pxfm v0.1.30'; resolver target graph; binary 99-librsvg/vendor path string x54/x54 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: quick-error 2.0.1 (librsvg)

declared 'MIT/Apache-2.0' (legacy '/' = OR)
statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling quick-error v2.0.1' (run 2) + target graph
Source evidence: log #158 'Compiling quick-error v2.0.1'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: rawpointer 0.2.1 (librsvg)

declared 'MIT/Apache-2.0' (legacy '/' = OR)
statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling rawpointer v0.2.1' (run 2) + target graph
Source evidence: log #158 'Compiling rawpointer v0.2.1'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: rayon 1.10.0 (rav1e)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #87 rustc --target x86_64-pc-windows-gnu unit + line 'Compiling rayon v1.10.0' (run 2)
Source evidence: log #87 rustc --target x86_64-pc-windows-gnu unit (0 features); binary cargo registry path string x5/x5 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: rayon 1.12.0 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling rayon v1.12.0' (run 2) + target graph
Source evidence: log #158 'Compiling rayon v1.12.0'; resolver target graph; binary 99-librsvg/vendor path string x3/x3 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: rayon-core 1.12.1 (rav1e)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #87 rustc --target x86_64-pc-windows-gnu unit + line 'Compiling rayon-core v1.12.1' (run 2)
Source evidence: log #87 rustc --target x86_64-pc-windows-gnu unit (0 features); binary cargo registry path string x13/x13 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: rayon-core 1.13.0 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling rayon-core v1.13.0' (run 2) + target graph
Source evidence: log #158 'Compiling rayon-core v1.13.0'; resolver target graph; binary 99-librsvg/vendor path string x12/x12 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: rctree 0.6.0 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling rctree v0.6.0' (run 2) + target graph
Source evidence: log #158 'Compiling rctree v0.6.0'; resolver target graph; binary 99-librsvg/vendor path string x1/x1 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: regex 1.13.1 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling regex v1.13.1' (run 2) + target graph
Source evidence: log #158 'Compiling regex v1.13.1'; resolver target graph; binary 99-librsvg/vendor path string x7/x7 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: regex-automata 0.4.18 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling regex-automata v0.4.18' (run 2) + target graph
Source evidence: log #158 'Compiling regex-automata v0.4.18'; resolver target graph; binary 99-librsvg/vendor path string x80/x80 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: regex-syntax 0.8.11 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling regex-syntax v0.8.11' (run 2) + target graph
Source evidence: log #158 'Compiling regex-syntax v0.8.11'; resolver target graph; binary 99-librsvg/vendor path string x14/x14 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: rgb 0.8.53 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling rgb v0.8.53' (run 2) + target graph
Source evidence: log #158 'Compiling rgb v0.8.53'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: rust-std 1.99.1 (toolchain)

the x86_64-pc-windows-gnu std as linked into both staticlibs: core (incl. the in-tree stdarch core_arch and portable-simd subtrees, their own LICENSE-MIT/-APACHE carried), alloc, std, panic_unwind, panic_abort, unwind, std_detect, rustc-std-workspace-core/-alloc, windows-link; tag 1.99.1 = tag object 213cfbe6 -> commit 58cf8f9c
statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: binary; prebuilt toolchain component, no run-2 compile line and no lock: rests on the PE import table / binary strings in 'evidence' plus the toolchain facts (version, link flags)
Source evidence: binary /rustc/58cf8f9c/library/{core,alloc,std,std_detect} panic paths (x314 per exe); log #158 'Program rustc found: YES 1.99.1'

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: rustc-demangle 0.1.28 (toolchain)

declared 'MIT/Apache-2.0' (legacy '/' = OR)
statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: lock-graph; prebuilt rust-std dependency: included from rust library/Cargo.lock @58cf8f9c target graph (std, backtrace + panic-unwind)
Source evidence: library/Cargo.lock @58cf8f9c; std target graph (backtrace, panic-unwind); binary name string 'rustc-demangle'

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: rustc-hash 2.1.3 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling rustc-hash v2.1.3' (run 2) + target graph
Source evidence: log #158 'Compiling rustc-hash v2.1.3'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: safe_arch 1.2.0 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling safe_arch v1.2.0' (run 2) + target graph
Source evidence: log #158 'Compiling safe_arch v1.2.0'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: scan_fmt 0.2.6 (rav1e)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #87 rustc --target x86_64-pc-windows-gnu unit + line 'Compiling scan_fmt v0.2.6' (run 2)
Source evidence: log #87 rustc --target x86_64-pc-windows-gnu unit (0 features); binary cargo registry path string x1/x1 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: scopeguard 1.2.0 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling scopeguard v1.2.0' (run 2) + target graph
Source evidence: log #158 'Compiling scopeguard v1.2.0'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: selectors 0.40.0 (librsvg)

crate ships no licence file; canonical SPDX text(s) at license-list-data v3.29.0; authors: The Servo Project Developers; MPL-2.0 s3.2: the notice must say where the Source Code Form is available (source_url); no Incompatible-With-Secondary-Licenses notice; combined under GPL-3.0 per MPL-2.0 section 3.3
MPL-2.0 (secondary licence: GPL-3.0 permitted, section 3.3)
statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling selectors v0.40.0' (run 2) + target graph
Source evidence: log #158 'Compiling selectors v0.40.0'; resolver target graph; binary 99-librsvg/vendor path string x8/x8 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: serde 1.0.229 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling serde v1.0.229' (run 2) + target graph
Source evidence: log #158 'Compiling serde v1.0.229'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: serde_core 1.0.229 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling serde_core v1.0.229' (run 2) + target graph
Source evidence: log #158 'Compiling serde_core v1.0.229'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: servo_arc 0.4.3 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling servo_arc v0.4.3' (run 2) + target graph
Source evidence: log #158 'Compiling servo_arc v0.4.3'; resolver target graph; binary 99-librsvg/vendor path string x1/x1 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: simba 0.10.2 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling simba v0.10.2' (run 2) + target graph
Source evidence: log #158 'Compiling simba v0.10.2'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: simd-adler32 0.3.10 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling simd-adler32 v0.3.10' (run 2) + target graph
Source evidence: log #158 'Compiling simd-adler32 v0.3.10'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: simdutf8 0.1.5 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling simdutf8 v0.1.5' (run 2) + target graph
Source evidence: log #158 'Compiling simdutf8 v0.1.5'; resolver target graph; binary 99-librsvg/vendor path string x1/x1 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: siphasher 1.0.4 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling siphasher v1.0.4' (run 2) + target graph
Source evidence: log #158 'Compiling siphasher v1.0.4'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: slab 0.4.12 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling slab v0.4.12' (run 2) + target graph
Source evidence: log #158 'Compiling slab v0.4.12'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: smallvec 1.16.4 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling smallvec v1.16.4' (run 2) + target graph
Source evidence: log #158 'Compiling smallvec v1.16.4'; resolver target graph; binary 99-librsvg/vendor path string x8/x8 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: stable_deref_trait 1.2.0 (rav1e)

declared 'MIT/Apache-2.0' (legacy '/' = OR)
statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #87 rustc --target x86_64-pc-windows-gnu unit + line 'Compiling stable_deref_trait v1.2.0' (run 2)
Source evidence: log #87 rustc --target x86_64-pc-windows-gnu unit (0 features)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: stable_deref_trait 1.2.1 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling stable_deref_trait v1.2.1' (run 2) + target graph
Source evidence: log #158 'Compiling stable_deref_trait v1.2.1'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: static_assertions 1.1.0 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling static_assertions v1.1.0' (run 2) + target graph
Source evidence: log #158 'Compiling static_assertions v1.1.0'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: string_cache 0.10.0 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling string_cache v0.10.0' (run 2) + target graph
Source evidence: log #158 'Compiling string_cache v0.10.0'; resolver target graph; binary 99-librsvg/vendor path string x3/x3 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: string_cache 0.9.0 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling string_cache v0.9.0' (run 2) + target graph
Source evidence: log #158 'Compiling string_cache v0.9.0'; resolver target graph; binary 99-librsvg/vendor path string x9/x9 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: tendril 0.5.1 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling tendril v0.5.1' (run 2) + target graph
Source evidence: log #158 'Compiling tendril v0.5.1'; resolver target graph; binary 99-librsvg/vendor path string x10/x10 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: terminal_size 0.4.2 (rav1e)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #87 rustc --target x86_64-pc-windows-gnu unit + line 'Compiling terminal_size v0.4.2' (run 2)
Source evidence: log #87 rustc --target x86_64-pc-windows-gnu unit (0 features)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: thiserror 1.0.69 (rav1e)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #87 rustc --target x86_64-pc-windows-gnu unit + line 'Compiling thiserror v1.0.69' (run 2)
Source evidence: log #87 rustc --target x86_64-pc-windows-gnu unit (0 features)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: thiserror 2.0.12 (rav1e)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #87 rustc --target x86_64-pc-windows-gnu unit + line 'Compiling thiserror v2.0.12' (run 2)
Source evidence: log #87 rustc --target x86_64-pc-windows-gnu unit (2 features)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: tinystr 0.8.5 (librsvg)

Unicode License v3 (UNICODE LICENSE V3 text shipped); CHARC ruled Unicode-3.0 COMPATIBLE (second addendum)
statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling tinystr v0.8.5' (run 2) + target graph
Source evidence: log #158 'Compiling tinystr v0.8.5'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: tinyvec 1.13.3 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling tinyvec v1.13.3' (run 2) + target graph
Source evidence: log #158 'Compiling tinyvec v1.13.3'; resolver target graph; binary 99-librsvg/vendor path string x1/x1 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: typenum 1.20.1 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling typenum v1.20.1' (run 2) + target graph
Source evidence: log #158 'Compiling typenum v1.20.1'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: unicode-width 0.2.1 (rav1e)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #87 rustc --target x86_64-pc-windows-gnu unit + line 'Compiling unicode-width v0.2.1' (run 2)
Source evidence: log #87 rustc --target x86_64-pc-windows-gnu unit (2 features)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: url 2.5.8 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling url v2.5.8' (run 2) + target graph
Source evidence: log #158 'Compiling url v2.5.8'; resolver target graph; binary 99-librsvg/vendor path string x12/x12 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: utf8_iter 1.0.4 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling utf8_iter v1.0.4' (run 2) + target graph
Source evidence: log #158 'Compiling utf8_iter v1.0.4'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: utf8parse 0.2.2 (rav1e)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #87 rustc --target x86_64-pc-windows-gnu unit + line 'Compiling utf8parse v0.2.2' (run 2)
Source evidence: log #87 rustc --target x86_64-pc-windows-gnu unit (1 features)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: v_frame 0.3.9 (rav1e)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #87 rustc --target x86_64-pc-windows-gnu unit + line 'Compiling v_frame v0.3.9' (run 2)
Source evidence: log #87 rustc --target x86_64-pc-windows-gnu unit (0 features); binary cargo registry path string x1/x1 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: web_atoms 0.2.6 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling web_atoms v0.2.6' (run 2) + target graph
Source evidence: log #158 'Compiling web_atoms v0.2.6'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: weezl 0.1.12 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling weezl v0.1.12' (run 2) + target graph
Source evidence: log #158 'Compiling weezl v0.1.12'; resolver target graph; binary 99-librsvg/vendor path string x4/x4 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: wide 1.7.1 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling wide v1.7.1' (run 2) + target graph
Source evidence: log #158 'Compiling wide v1.7.1'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: winapi 0.3.9 (librsvg)

declared 'MIT/Apache-2.0' (legacy '/' = OR)
statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling winapi v0.3.9' (run 2) + target graph
Source evidence: log #158 'Compiling winapi v0.3.9'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: winapi-x86_64-pc-windows-gnu 0.4.0 (librsvg)

declared 'MIT/Apache-2.0' (legacy '/' = OR); crate ships no licence file; canonical SPDX text(s) at license-list-data v3.29.0; authors: Peter Atashian <retep998@gmail.com>
statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling winapi-x86_64-pc-windows-gnu v0.4.0' (run 2) + target graph
Source evidence: log #158 'Compiling winapi-x86_64-pc-windows-gnu v0.4.0'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: windows-link 0.2.1 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling windows-link v0.2.1' (run 2) + target graph
Source evidence: log #158 'Compiling windows-link v0.2.1'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: windows-sys 0.59.0 (rav1e)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #87 rustc --target x86_64-pc-windows-gnu unit + line 'Compiling windows-sys v0.59.0' (run 2)
Source evidence: log #87 rustc --target x86_64-pc-windows-gnu unit (10 features)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: windows-sys 0.61.2 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling windows-sys v0.61.2' (run 2) + target graph
Source evidence: log #158 'Compiling windows-sys v0.61.2'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: windows-targets 0.52.6 (rav1e)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #87 rustc --target x86_64-pc-windows-gnu unit + line 'Compiling windows-targets v0.52.6' (run 2)
Source evidence: log #87 rustc --target x86_64-pc-windows-gnu unit (0 features)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: windows_x86_64_gnu 0.52.6 (rav1e)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #87 rustc --target x86_64-pc-windows-gnu unit + line 'Compiling windows_x86_64_gnu v0.52.6' (run 2)
Source evidence: log #87 rustc --target x86_64-pc-windows-gnu unit (0 features)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: writeable 0.6.4 (librsvg)

Unicode License v3 (UNICODE LICENSE V3 text shipped); CHARC ruled Unicode-3.0 COMPATIBLE (second addendum)
statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling writeable v0.6.4' (run 2) + target graph
Source evidence: log #158 'Compiling writeable v0.6.4'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: xml5ever 0.39.0 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling xml5ever v0.39.0' (run 2) + target graph
Source evidence: log #158 'Compiling xml5ever v0.39.0'; resolver target graph; binary 99-librsvg/vendor path string x4/x4 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: y4m 0.8.0 (rav1e)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #87 rustc --target x86_64-pc-windows-gnu unit + line 'Compiling y4m v0.8.0' (run 2)
Source evidence: log #87 rustc --target x86_64-pc-windows-gnu unit (0 features)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: yoke 0.8.4 (librsvg)

Unicode License v3 (UNICODE LICENSE V3 text shipped); CHARC ruled Unicode-3.0 COMPATIBLE (second addendum)
statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling yoke v0.8.4' (run 2) + target graph
Source evidence: log #158 'Compiling yoke v0.8.4'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: zerocopy 0.8.63 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling zerocopy v0.8.63' (run 2) + target graph
Source evidence: log #158 'Compiling zerocopy v0.8.63'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: zerofrom 0.1.8 (librsvg)

Unicode License v3 (UNICODE LICENSE V3 text shipped); CHARC ruled Unicode-3.0 COMPATIBLE (second addendum)
statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling zerofrom v0.1.8' (run 2) + target graph
Source evidence: log #158 'Compiling zerofrom v0.1.8'; resolver target graph

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: zerotrie 0.2.5 (librsvg)

Unicode License v3 (UNICODE LICENSE V3 text shipped); CHARC ruled Unicode-3.0 COMPATIBLE (second addendum)
statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling zerotrie v0.2.5' (run 2) + target graph
Source evidence: log #158 'Compiling zerotrie v0.2.5'; resolver target graph; binary 99-librsvg/vendor path string x3/x3 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: zerovec 0.11.9 (librsvg)

Unicode License v3 (UNICODE LICENSE V3 text shipped); CHARC ruled Unicode-3.0 COMPATIBLE (second addendum)
statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling zerovec v0.11.9' (run 2) + target graph
Source evidence: log #158 'Compiling zerovec v0.11.9'; resolver target graph; binary 99-librsvg/vendor path string x5/x5 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: zune-core 0.5.3 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling zune-core v0.5.3' (run 2) + target graph
Source evidence: log #158 'Compiling zune-core v0.5.3'; resolver target graph; binary 99-librsvg/vendor path string x4/x4 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

### FFmpeg toolchain runtime: zune-jpeg 0.5.15 (librsvg)

statically linked into ffmpeg.exe / ffprobe.exe by the fork build at d77b8352f60bd180ebce585632846533aa60b183
Census basis: compile-log; log #158 line 'Compiling zune-jpeg v0.5.15' (run 2) + target graph
Source evidence: log #158 'Compiling zune-jpeg v0.5.15'; resolver target graph; binary 99-librsvg/vendor path string x20/x20 (ffmpeg/ffprobe)

Bundled entries: `file:ffmpeg.exe`, `file:ffprobe.exe`, `file:ffmpeg-BUILD.txt`, `file:ffmpeg-LICENSE.txt`

## Stage and runtime licence text files

These links preserve exact upstream bytes independently of Markdown checkout line endings.

- [crates--cast-0.3.0--LICENSE-MIT](tools/package/native-licences/ffmpeg-toolchain/crates--cast-0.3.0--LICENSE-MIT); SHA-256: `005b3f9b4687364514bbaea2a25e96d54ce6a59277d157386e8259cbcae8e095`; bytes: 1063.
- [cairo--util--COPYING](tools/package/native-licences/ffmpeg-components/cairo--util--COPYING); SHA-256: `008e976b6e5e7155ee24322073f42cab7cd6daf90bc2322f1d5c3aacab94111c`; bytes: 138.
- [zix--LICENSES--ISC.txt](tools/package/native-licences/ffmpeg-components/zix--LICENSES--ISC.txt); SHA-256: `010c7513fdccf856edda08d42d2c46ae393e67b3acf97f9e428980cca2f94b7d`; bytes: 752.
- [openmpt--include--miniz--LICENSE](tools/package/native-licences/ffmpeg-components/openmpt--include--miniz--LICENSE); SHA-256: `0115478d567121238cf6cc1c0c361926cf07a49d9e4c9e66da97fac6a01646b3`; bytes: 1184.
- [gcc--libstdc++-v3--src--c++17--fast_float--fast_float.h](tools/package/native-licences/ffmpeg-toolchain/gcc--libstdc++-v3--src--c++17--fast_float--fast_float.h); SHA-256: `01363132cf8d5b47721c1d614e4c5433ec7450da58d29a9acc32ae19cc88f215`; bytes: 112375.
- [crates--memchr-2.8.3--COPYING](tools/package/native-licences/ffmpeg-toolchain/crates--memchr-2.8.3--COPYING); SHA-256: `01c266bced4a434da0051174d6bee16a4c82cf634e2679b6155d40d75012390f`; bytes: 126.
- [libopus--COPYING](tools/package/native-licences/ffmpeg-components/libopus--COPYING); SHA-256: `01e1167d54a096d123cf6dfbbeb19587278845c6481d2d66d545669846079551`; bytes: 1945.
- [crates--flate2-1.1.10--LICENSE-MIT](tools/package/native-licences/ffmpeg-toolchain/crates--flate2-1.1.10--LICENSE-MIT); SHA-256: `025436edff4cfcdde17a5811fdea78892d8482efd1abdec5a17872d07a4f2112`; bytes: 1062.
- [openmpt--include--opusfile--COPYING](tools/package/native-licences/ffmpeg-components/openmpt--include--opusfile--COPYING); SHA-256: `0267ae795ab744c4e0f9c45e249440fdf2e75dac8c804f36066b28649bf74aaf`; bytes: 1487.
- [crates--v_frame-0.3.9--LICENSE](tools/package/native-licences/ffmpeg-toolchain/crates--v_frame-0.3.9--LICENSE); SHA-256: `02b80951ce6c1dd25d7278977222a91b2f61a883ca272b0238c52a60a03ae90a`; bytes: 1332.
- [crates--aligned-0.4.2--LICENSE-MIT](tools/package/native-licences/ffmpeg-toolchain/crates--aligned-0.4.2--LICENSE-MIT); SHA-256: `035e70219855119df4273b3c5b97543ae82e0dd60c520416e759107c602f651b`; bytes: 1058.
- [mingw--DISCLAIMER](tools/package/native-licences/ffmpeg-components/mingw--DISCLAIMER); SHA-256: `039ed6b4f31bb7fb97e733170b58cc435335352e4745734fcfd113877fdaf340`; bytes: 2245.
- [svtav1--third_party--fastfeat--LICENSE](tools/package/native-licences/ffmpeg-components/svtav1--third_party--fastfeat--LICENSE); SHA-256: `043dcfd059386f9facd376351b2bd79325778744aa442177390cdfcca54babed`; bytes: 1506.
- [crates--ahash-0.8.12--LICENSE-MIT](tools/package/native-licences/ffmpeg-toolchain/crates--ahash-0.8.12--LICENSE-MIT); SHA-256: `0444c6991eead6822f7b9102e654448d51624431119546492e8b231db42c48bb`; bytes: 1057.
- [crates--quick-error-2.0.1--LICENSE-MIT](tools/package/native-licences/ffmpeg-toolchain/crates--quick-error-2.0.1--LICENSE-MIT); SHA-256: `058f01fe181608d027fcde7e528fc03ea3cf90f30903c407644b0a9bbc54f500`; bytes: 1070.
- [crates--rayon-1.10.0--LICENSE-MIT](tools/package/native-licences/ffmpeg-toolchain/crates--rayon-1.10.0--LICENSE-MIT); SHA-256: `0621878e61f0d0fda054bcbe02df75192c28bde1ecc8289cbd86aeba2dd72720`; bytes: 1071.
- [lcevcdec--licenses--emscripten--licence.txt](tools/package/native-licences/ffmpeg-components/lcevcdec--licenses--emscripten--licence.txt); SHA-256: `06f2e6c024612605fc3c803b192983a26f19404eb54d78e399190d90ed32ac78`; bytes: 5092.
- [openmpt--include--SignalsmithStretch--signalsmith-linear--LICENSE.txt](tools/package/native-licences/ffmpeg-components/openmpt--include--SignalsmithStretch--signalsmith-linear--LICENSE.txt); SHA-256: `072b5e9eb5b22880bdf6256324654cf3ce53dba828edb911921121e1be09d9c3`; bytes: 1074.
- [spdx--text--Apache-2.0.txt](tools/package/native-licences/ffmpeg-toolchain/spdx--text--Apache-2.0.txt); SHA-256: `074e6e32c86a4c0ef8b3ed25b721ca23aca83df277cd88106ef7177c354615ff`; bytes: 10280.
- [lcevcdec--licenses--fmt--LICENSE](tools/package/native-licences/ffmpeg-components/lcevcdec--licenses--fmt--LICENSE); SHA-256: `07580f2a3b35709ce703d523f447b242f6dfec7582a8c0df102c7fa2849375f8`; bytes: 1431.
- [crates--miniz_oxide-0.9.1--LICENSE-ZLIB.md](tools/package/native-licences/ffmpeg-toolchain/crates--miniz_oxide-0.9.1--LICENSE-ZLIB.md); SHA-256: `0a54e647fe54104658b5e563c04c6f9edf251710e47bce692e0bd990a4ddaa39`; bytes: 984.
- [libzmq--packaging--debian--copyright](tools/package/native-licences/ffmpeg-components/libzmq--packaging--debian--copyright); SHA-256: `0a9b32db52765d7d0dd53eac99c373ef830ced0e859d1e6e62acc2fb590dbc9e`; bytes: 2757.
- [crates--phf-0.13.1--LICENSE](tools/package/native-licences/ffmpeg-toolchain/crates--phf-0.13.1--LICENSE); SHA-256: `0ab4d106b6faac07fb6a051815fd1b4d862d730895e2d7d7358c2f13565e7a38`; bytes: 1099.
- [svtav1--LICENSE.md](tools/package/native-licences/ffmpeg-components/svtav1--LICENSE.md); SHA-256: `0acc2fcb27472bdc9aaf8b71f37055bbdac4f54671b7d922f241bd7fcd0dd3e6`; bytes: 1709.
- [xz--COPYING.0BSD](tools/package/native-licences/ffmpeg-components/xz--COPYING.0BSD); SHA-256: `0b01625d853911cd0e2e088dcfb743261034a091bb379246cb25a14cc4c74bf1`; bytes: 607.
- [crates--smallvec-1.16.4--LICENSE-MIT](tools/package/native-licences/ffmpeg-toolchain/crates--smallvec-1.16.4--LICENSE-MIT); SHA-256: `0b28172679e0009b655da42797c03fd163a3379d5cfa67ba1f1655e974a2a1a9`; bytes: 1072.
- [crates--object-0.39.1--LICENSE-MIT](tools/package/native-licences/ffmpeg-toolchain/crates--object-0.39.1--LICENSE-MIT); SHA-256: `0b74dfa0bcee5c420c6b7f67b4b2658f9ab8388c97b8e733975f2cecbdd668a6`; bytes: 1064.
- [lcevcdec--licenses--ios-cmake--license.md](tools/package/native-licences/ffmpeg-components/lcevcdec--licenses--ios-cmake--license.md); SHA-256: `0b85f7cda17eeba9d545455874ede53b54efb3ec8a9ae381250d1183c98efea0`; bytes: 1581.
- [openmpt--include--premake--modules--xcode--LICENSE.TXT](tools/package/native-licences/ffmpeg-components/openmpt--include--premake--modules--xcode--LICENSE.TXT); SHA-256: `0ba7252324e5aa82440f966ba7adafae7a1ce09a54667569f7c090cfd6f964e4`; bytes: 1547.
- [libunibreak--LICENCE](tools/package/native-licences/ffmpeg-components/libunibreak--LICENCE); SHA-256: `0c57e2ec42ece17791a75d2f9b2f8e0663181be008667a507f765b3ef22522db`; bytes: 1045.
- [crates--locale_config-0.3.0--LICENSE](tools/package/native-licences/ffmpeg-toolchain/crates--locale_config-0.3.0--LICENSE); SHA-256: `0ceba5b58dfaeb0281ccd2da83a34eed8b3c5d5e0c1e1b947ce93000043f0200`; bytes: 1338.
- [crates--simdutf8-0.1.5--LICENSE-Apache](tools/package/native-licences/ffmpeg-toolchain/crates--simdutf8-0.1.5--LICENSE-Apache); SHA-256: `0cec06e0e55fbc3dc5cee4fca9b607f66cb8f4e4dbcf3b3c013594dd156732e9`; bytes: 10173.
- [crates--miniz_oxide-0.9.1--LICENSE-APACHE.md](tools/package/native-licences/ffmpeg-toolchain/crates--miniz_oxide-0.9.1--LICENSE-APACHE.md); SHA-256: `0d542e0c8804e39aa7f37eb00da5a762149dc682d7829451287e11b938e94594`; bytes: 10174.
- [crates--memchr-2.8.3--LICENSE-MIT](tools/package/native-licences/ffmpeg-toolchain/crates--memchr-2.8.3--LICENSE-MIT); SHA-256: `0f96a83840e146e43c0ec96a22ec1f392e0680e6c1226e6f3ba87e0740af850f`; bytes: 1081.
- [crates--av-data-0.4.4--LICENSE](tools/package/native-licences/ffmpeg-toolchain/crates--av-data-0.4.4--LICENSE); SHA-256: `0ffd79084929c4913ea1223796dccfb1d86abfb359e86ef7c0137d9805bfaacd`; bytes: 1069.
- [crates--encoding_rs-0.8.42--COPYRIGHT](tools/package/native-licences/ffmpeg-toolchain/crates--encoding_rs-0.8.42--COPYRIGHT); SHA-256: `11789f45bb180841cd362a5eee6789c68ddb573a11105e30768c308a6add0190`; bytes: 713.
- [crates--libc-0.2.189--LICENSE-MIT](tools/package/native-licences/ffmpeg-toolchain/crates--libc-0.2.189--LICENSE-MIT); SHA-256: `123a331b5dbf04c30097fa43b8f858bc85df671fe776de498d01f3d6b7c1f69e`; bytes: 1066.
- [zix--COPYING](tools/package/native-licences/ffmpeg-components/zix--COPYING); SHA-256: `1314cc14fb947491491c517c533ac7de4f6798585f922a472358082c25ac1881`; bytes: 752.
- [crates--y4m-0.8.0--LICENSE](tools/package/native-licences/ffmpeg-toolchain/crates--y4m-0.8.0--LICENSE); SHA-256: `1327309babc5f34582ae4731b9022c75ff6fa9903eb17cfd113f4abae95b898b`; bytes: 1129.
- [lcevcdec--LICENSE.md](tools/package/native-licences/ffmpeg-components/lcevcdec--LICENSE.md); SHA-256: `14358b0ecf6e7036c211c10f0f25563c94483dee7b8c7c954e09e10f3771d0af`; bytes: 1659.
- [libssh--COPYING](tools/package/native-licences/ffmpeg-components/libssh--COPYING); SHA-256: `1656186e951db1c010a8485481fa94587f7e53a26d24976bef97945ad0c4df5a`; bytes: 25008.
- [gcc--libstdc++-v3--include--bits--stl_construct.h-L39-48.txt](tools/package/native-licences/ffmpeg-toolchain/gcc--libstdc++-v3--include--bits--stl_construct.h-L39-48.txt); SHA-256: `16be99fb02277ef8821225845ca2f3a9759ffe1c754f576f2cf4e60207401cd1`; bytes: 551.
- [kvazaar--LICENSE.EXT.greatest](tools/package/native-licences/ffmpeg-components/kvazaar--LICENSE.EXT.greatest); SHA-256: `16f569c87d5ec20b7474b55ee0a8877b8f8b4dc13f9567ebe0b8fe8afdeb34d2`; bytes: 218.
- [rust-lang-rust--COPYRIGHT](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--COPYRIGHT); SHA-256: `172020dbfd5b53a226dfde77616190a48dcff519b0bc0e6deb91a8450782c4af`; bytes: 1571.
- [libffi--LICENSE](tools/package/native-licences/ffmpeg-components/libffi--LICENSE); SHA-256: `17b64dc60f3b6897a60f971e288b973f655c2edcdf08b25f3c3dd5549857881c`; bytes: 1132.
- [glslang--LICENSE.txt](tools/package/native-licences/ffmpeg-components/glslang--LICENSE.txt); SHA-256: `17e70c676e1521ff3e4686f04a2053d93a7e28a33be8de7ec37ab0ff72feb677`; bytes: 54615.
- [libpng--contrib--pngminus--LICENSE.txt](tools/package/native-licences/ffmpeg-components/libpng--contrib--pngminus--LICENSE.txt); SHA-256: `1806f1f10d393e9e377b3a8d1b968452b54f1a90378f14eeef45426946ace330`; bytes: 1164.
- [crates--simdutf8-0.1.5--LICENSE-MIT](tools/package/native-licences/ffmpeg-toolchain/crates--simdutf8-0.1.5--LICENSE-MIT); SHA-256: `1847e0e0698142ed4347c1441a9fa81c8fbddd44b1d8bbcd5e3647f991759d7f`; bytes: 1035.
- [gcc--libstdc++-v3--src--c++17--ryu--d2s.c](tools/package/native-licences/ffmpeg-toolchain/gcc--libstdc++-v3--src--c++17--ryu--d2s.c); SHA-256: `18b4445b268e9e7e0eaf2255addfb8e4b675c24d1aeed601c3a6792272a6ea3e`; bytes: 17142.
- [freetype--src--pcf--README](tools/package/native-licences/ffmpeg-components/freetype--src--pcf--README); SHA-256: `18d9782898d9eac04476e2f744678137b2a889689ed3e923e052fc396a86f86b`; bytes: 3311.
- [pcre2--LICENCE.md](tools/package/native-licences/ffmpeg-components/pcre2--LICENCE.md); SHA-256: `197d8a73ffee0d6b09adba2f9c677b5f5aede24edf89258a68e48248d010d811`; bytes: 4011.
- [crates--zerocopy-0.8.63--LICENSE-MIT](tools/package/native-licences/ffmpeg-toolchain/crates--zerocopy-0.8.63--LICENSE-MIT); SHA-256: `1a2f5c12ddc934d58956aa5dbdd3255fe55fd957633ab7d0d39e4f0daa73f7df`; bytes: 1060.
- [sdl--LICENSE.txt](tools/package/native-licences/ffmpeg-components/sdl--LICENSE.txt); SHA-256: `1c040b8271b37e5076359f8fd54240e371114112924d2df81ef87c7d6a1dfdfd`; bytes: 884.
- [vulkan-headers--LICENSES--MIT.txt](tools/package/native-licences/ffmpeg-components/vulkan-headers--LICENSES--MIT.txt); SHA-256: `1ca3502222d967f3be5751c55f6b7ee735b5383909c3b501495f54b216dbf227`; bytes: 1084.
- [openmpt--include--pthread-win32--docs--COPYING.md](tools/package/native-licences/ffmpeg-components/openmpt--include--pthread-win32--docs--COPYING.md); SHA-256: `1cf9a1551401d708d96d869aa0a20bbb7d4fdb93c22da835b0366c27a4c4c4d8`; bytes: 5899.
- [sratom--COPYING](tools/package/native-licences/ffmpeg-components/sratom--COPYING); SHA-256: `1d968c655ecad113e128dbf4d4deabd9e30b931b42943b6a681c9cf11d7da5d4`; bytes: 751.
- [mingw--COPYING.MinGW-w64-runtime--COPYING.MinGW-w64-runtime.txt](tools/package/native-licences/ffmpeg-components/mingw--COPYING.MinGW-w64-runtime--COPYING.MinGW-w64-runtime.txt); SHA-256: `1db8da07b436c68833c0673ffee3d9fcb2526047f3820b81661865dfedc79a1f`; bytes: 12155.
- [crates--av-scenechange-0.14.1--LICENSE](tools/package/native-licences/ffmpeg-toolchain/crates--av-scenechange-0.14.1--LICENSE); SHA-256: `1e27e28eafbc439fd153d0cca093fcb9ca83f269d93393e641ce5664181fd41b`; bytes: 1076.
- [lv2--COPYING](tools/package/native-licences/ffmpeg-components/lv2--COPYING); SHA-256: `1e6bb175e193608b767ff25a4ed68b82c4db599491cf0d2694435cf60e9a4841`; bytes: 827.
- [crates--dtoa-short-0.3.5--LICENSE](tools/package/native-licences/ffmpeg-toolchain/crates--dtoa-short-0.3.5--LICENSE); SHA-256: `1f256ecad192880510e84ad60474eab7589218784b9a50bc7ceee34c2b91f1d5`; bytes: 16725.
- [libvorbis--debian--copyright](tools/package/native-licences/ffmpeg-components/libvorbis--debian--copyright); SHA-256: `1f6c6b6397d86d20968d7856d6945591b89e4cb64e5fc1ec8b992811f6a65ed8`; bytes: 1695.
- [crates--console-0.15.11--LICENSE](tools/package/native-licences/ffmpeg-toolchain/crates--console-0.15.11--LICENSE); SHA-256: `2022c11b24fc1e50fa06a5959e40198a3464f560729ad3d00139abb8a328362d`; bytes: 1112.
- [gcc--libstdc++-v3--include--bits--stl_bvector.h-L39-48.txt](tools/package/native-licences/ffmpeg-toolchain/gcc--libstdc++-v3--include--bits--stl_bvector.h-L39-48.txt); SHA-256: `204d23bfa72433dc066ff28294a4073eb1ac1c6651dc95f598e7ebf25872fee7`; bytes: 551.
- [svtav1--PATENTS.md](tools/package/native-licences/ffmpeg-components/svtav1--PATENTS.md); SHA-256: `20678ab10402659106dc4c147c97b2a6e94b5c0695415e15a8f195ebc3547922`; bytes: 5767.
- [crates--form_urlencoded-1.2.2--LICENSE-MIT](tools/package/native-licences/ffmpeg-toolchain/crates--form_urlencoded-1.2.2--LICENSE-MIT); SHA-256: `20c7855c364d57ea4c97889a5e8d98470a9952dade37bd9248b9a54431670e5e`; bytes: 1072.
- [libiconv--COPYING.LIB](tools/package/native-licences/ffmpeg-components/libiconv--COPYING.LIB); SHA-256: `20e50fe7aae3e56378ebf0417d9de904f55a0e61e4df315333e632a4d3555d95`; bytes: 26419.
- [glslang--LICENSES--Bison-exception-2.2.txt](tools/package/native-licences/ffmpeg-components/glslang--LICENSES--Bison-exception-2.2.txt); SHA-256: `218a0cdacd4059d01e2ccff5b31d3e968a6a9c8ee7e4e0fc231c47d7fbf422c3`; bytes: 657.
- [openmpt--include--premake--packages--debian--copyright](tools/package/native-licences/ffmpeg-components/openmpt--include--premake--packages--debian--copyright); SHA-256: `22bb324973ed458997c09bb6f69fd297cc114e2e687b88b7cf38fb5dbe1a6867`; bytes: 2686.
- [crates--lab-0.11.0--LICENSE](tools/package/native-licences/ffmpeg-toolchain/crates--lab-0.11.0--LICENSE); SHA-256: `22c404ba4f8503eeef72b1cc644b95c2e40b9b974dfc3552aebfff8a26b07463`; bytes: 1069.
- [fftw3--COPYING](tools/package/native-licences/ffmpeg-components/fftw3--COPYING); SHA-256: `231f7edcc7352d7734a96eef0b8030f77982678c516876fcb81e25b32d68564c`; bytes: 18002.
- [crates--unicode-width-0.2.1--COPYRIGHT](tools/package/native-licences/ffmpeg-toolchain/crates--unicode-width-0.2.1--COPYRIGHT); SHA-256: `23860c2a7b5d96b21569afedf033469bab9fe14a1b24a35068b8641c578ce24d`; bytes: 321.
- [crates--adler2-2.0.1--LICENSE-MIT](tools/package/native-licences/ffmpeg-toolchain/crates--adler2-2.0.1--LICENSE-MIT); SHA-256: `23f18e03dc49df91622fe2a76176497404e46ced8a715d9d2b67a7446571cca3`; bytes: 1023.
- [gcc--libstdc++-v3--include--bits--stl_algo.h-L39-48.txt](tools/package/native-licences/ffmpeg-toolchain/gcc--libstdc++-v3--include--bits--stl_algo.h-L39-48.txt); SHA-256: `252505e045c2ef4968fea6787374ee16157aaa9d109ed02244573190b8f30291`; bytes: 546.
- [twolame--COPYING](tools/package/native-licences/ffmpeg-components/twolame--COPYING); SHA-256: `257a842724705950b07da76ce0e22ffa80ec77b3e9dfc6702522ac342409da0f`; bytes: 26428.
- [cairo--util--cairo-script--COPYING](tools/package/native-licences/ffmpeg-components/cairo--util--cairo-script--COPYING); SHA-256: `25f4d4ce651b1ee6aff713ff986275d6c190a8537e36437886f8bf1497b0a174`; bytes: 656.
- [libxml2--dict.c](tools/package/native-licences/ffmpeg-components/libxml2--dict.c); SHA-256: `2663392f29dd45eb7ad802c471e146d4f6f509e317a4938b496920b4ea0228b4`; bytes: 25613.
- [crates--futures-channel-0.3.34--LICENSE-APACHE](tools/package/native-licences/ffmpeg-toolchain/crates--futures-channel-0.3.34--LICENSE-APACHE); SHA-256: `275c491d6d1160553c32fd6127061d7f9606c3ea25abfad6ca3f6ed088785427`; bytes: 10874.
- [libbluray--contrib--asm--LICENSE.txt](tools/package/native-licences/ffmpeg-components/libbluray--contrib--asm--LICENSE.txt); SHA-256: `293b6af371eee28b0ff16f0334ea19e20a3d5522143faa4b95b346855507879a`; bytes: 1598.
- [rust-lang-rust--library--stdarch--LICENSE-MIT](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-MIT); SHA-256: `29662666b44dff84977b46e05642cdef910bc3a93a17b5fd86e632bafa59cf21`; bytes: 1071.
- [crates--moxcms-0.8.1--LICENSE.md](tools/package/native-licences/ffmpeg-toolchain/crates--moxcms-0.8.1--LICENSE.md); SHA-256: `2aa92cada6431e75615e3fe6cb1a9082c98f777d48ae1c087c0da0e37f7b8bff`; bytes: 1506.
- [xvid--LICENSE](tools/package/native-licences/ffmpeg-components/xvid--LICENSE); SHA-256: `2ab06d2335f9781f1a485c78a557e6c61b6c24e118caad4d4210c46426bbce95`; bytes: 17987.
- [aom--third_party--libyuv--LICENSE](tools/package/native-licences/ffmpeg-components/aom--third_party--libyuv--LICENSE); SHA-256: `2b2cc1180c7e6988328ad2033b04b80117419db9c4c584918bbb3cfec7e9364f`; bytes: 1506.
- [libsamplerate--COPYING](tools/package/native-licences/ffmpeg-components/libsamplerate--COPYING); SHA-256: `2c1f76ce2effdddb425018405d5690c0b1ab4e6976e35296b0a6db65c5e1a55d`; bytes: 1334.
- [libtheora--LICENSE](tools/package/native-licences/ffmpeg-components/libtheora--LICENSE); SHA-256: `2c902950c73a63cd285dc0c36573de9c5fefe66d49312949c51d941f33e92932`; bytes: 960.
- [openmpt--LICENSE](tools/package/native-licences/ffmpeg-components/openmpt--LICENSE); SHA-256: `2c999e99533c10a347916a72e075bacf10fcedeff793bd90d41d812b46161da2`; bytes: 1621.
- [rav1e--LICENSE](tools/package/native-licences/ffmpeg-components/rav1e--LICENSE); SHA-256: `2dd0a109751e939dec3f80ddcfbc1ba91553f18c574399e85c159632182a2c0a`; bytes: 1332.
- [onevpl--examples--api1x_core--legacy-decode--License.txt](tools/package/native-licences/ffmpeg-components/onevpl--examples--api1x_core--legacy-decode--License.txt); SHA-256: `2e35006c345787f7205bdaa86920c8fac86abd19b95d7b4c1ba5531853ea3938`; bytes: 1052.
- [openjpeg--thirdparty--astyle--LICENSE.md](tools/package/native-licences/ffmpeg-components/openjpeg--thirdparty--astyle--LICENSE.md); SHA-256: `2e8480e753b7a1d100c80920f4250b1bc9f93a18c6a5953c42b11445218cd0fb`; bytes: 1094.
- [libxml2--list.c-L1-16.txt](tools/package/native-licences/ffmpeg-components/libxml2--list.c-L1-16.txt); SHA-256: `2fdb83809864852d236c64fffa74054699e61887b736e18724d4a8ac0e9684f8`; bytes: 649.
- [sdl--Xcode--SDL--pkg-support--resources--License.txt](tools/package/native-licences/ffmpeg-components/sdl--Xcode--SDL--pkg-support--resources--License.txt); SHA-256: `30e349158ffdcb06b9bb2ec406df66758161ad1efa75a368243a6d0b50b43784`; bytes: 909.
- [sdl--src--hidapi--LICENSE-bsd.txt](tools/package/native-licences/ffmpeg-components/sdl--src--hidapi--LICENSE-bsd.txt); SHA-256: `30eb1bef29b46f8ba7ab8b416035dbd93cb034a45481dd97815b944284582cd2`; bytes: 1534.
- [crates--rustc-hash-2.1.3--LICENSE-MIT](tools/package/native-licences/ffmpeg-toolchain/crates--rustc-hash-2.1.3--LICENSE-MIT); SHA-256: `30fefc3a7d6a0041541858293bcbea2dde4caa4c0a5802f996a7f7e8c0085652`; bytes: 1022.
- [gcc--libstdc++-v3--include--bits--stl_deque.h-L39-48.txt](tools/package/native-licences/ffmpeg-toolchain/gcc--libstdc++-v3--include--bits--stl_deque.h-L39-48.txt); SHA-256: `31c47554f2362beae08bda8c75e7d867297be07dd98b97d0fce7676a34438e9f`; bytes: 546.
- [libdvdnav--COPYING](tools/package/native-licences/ffmpeg-components/libdvdnav--COPYING); SHA-256: `32b1062f7da84967e7019d01ab805935caa7ab7321a7ced0e30ebe75e5df1670`; bytes: 17992.
- [dav1d--doc--PATENTS](tools/package/native-licences/ffmpeg-components/dav1d--doc--PATENTS); SHA-256: `335eca574598bf4ca181b12f708d6669e5a5e78c8e1513e5b35fa1f03901484b`; bytes: 5730.
- [serd--LICENSES--0BSD.txt](tools/package/native-licences/ffmpeg-components/serd--LICENSES--0BSD.txt); SHA-256: `342bbffadbda3058b5b59fb9cf25d940e1c353b1181b892dc8a473f213a0440d`; bytes: 661.
- [zlib--contrib--dotzlib--LICENSE_1_0.txt](tools/package/native-licences/ffmpeg-components/zlib--contrib--dotzlib--LICENSE_1_0.txt); SHA-256: `36266a8fd073568394cb81cdb2b124f7fdae2c64c1a7ed09db34b4d22efa2951`; bytes: 1359.
- [rust-lang-backtrace-rs--LICENSE-MIT](tools/package/native-licences/ffmpeg-toolchain/rust-lang-backtrace-rs--LICENSE-MIT); SHA-256: `378f5840b258e2779c39418f3f2d7b2ba96f1c7917dd6be0713f88305dbda397`; bytes: 1057.
- [rust-lang-rust--library--compiler-builtins--libm--LICENSE.txt](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--compiler-builtins--libm--LICENSE.txt); SHA-256: `3823dda7cf046602f4b4e77ec8e227863dc4736037cc85bb33d9f19febe16bb7`; bytes: 14088.
- [gnulib--doc--COPYINGv3](tools/package/native-licences/ffmpeg-components/gnulib--doc--COPYINGv3); SHA-256: `3972dc9744f6499f0f9b2dbf76696f2ae7ad8af9b23dde66d6af86c9dfb36986`; bytes: 35149.
- [lcevcdec--COPYING](tools/package/native-licences/ffmpeg-components/lcevcdec--COPYING); SHA-256: `3afa5369b4fb44e18280b6e0e275971f78bc6eaf5f53553f41f2483fd8b1267e`; bytes: 817.
- [crates--maybe-rayon-0.1.1--LICENSE](tools/package/native-licences/ffmpeg-toolchain/crates--maybe-rayon-0.1.1--LICENSE); SHA-256: `3b2dbf86845042813be71eecfea49de557bb4ea908b9b15f5b285259714fa183`; bytes: 1070.
- [kvazaar--LICENSE](tools/package/native-licences/ffmpeg-components/kvazaar--LICENSE); SHA-256: `3c1dc3d7f8a3d08c14f4fbe9942f45764d8a21a3296e8d83446f33fd65f21c38`; bytes: 1549.
- [crates--wide-1.7.1--LICENSE-ZLIB.txt](tools/package/native-licences/ffmpeg-toolchain/crates--wide-1.7.1--LICENSE-ZLIB.txt); SHA-256: `3c6921f3dfec0bed0cfa2d632616edd7380a875c8ad76c7b23dc59892259f62c`; bytes: 850.
- [brotli--LICENSE](tools/package/native-licences/ffmpeg-components/brotli--LICENSE); SHA-256: `3d180008e36922a4e8daec11c34c7af264fed5962d07924aea928c38e8663c94`; bytes: 1084.
- [crates--approx-0.5.1--LICENSE](tools/package/native-licences/ffmpeg-toolchain/crates--approx-0.5.1--LICENSE); SHA-256: `3ddf9be5c28fe27dad143a5dc76eea25222ad1dd68934a047064e56ed2fa40c5`; bytes: 11560.
- [libzmq--external--wepoll--license.txt](tools/package/native-licences/ffmpeg-components/libzmq--external--wepoll--license.txt); SHA-256: `3e56262d2c0e9492f113089916ed624e98f88b31dfd6acae24ede59cdfda5a69`; bytes: 1394.
- [openmpt--include--portaudio--bindings--cpp--COPYING](tools/package/native-licences/ffmpeg-components/openmpt--include--portaudio--bindings--cpp--COPYING); SHA-256: `3ec8d97acf149e39aa440f39eb1126a6ec5089e2864cbecdf2d2952bc0a5ed83`; bytes: 1545.
- [libzmq--external--unity--license.txt](tools/package/native-licences/ffmpeg-components/libzmq--external--unity--license.txt); SHA-256: `3ed9b51da86f52c729c96cc99fdde6444b2297c788a9cf4ad1d3649dc34c4985`; bytes: 1123.
- [glib--LICENSES--CC-BY-SA-3.0.txt](tools/package/native-licences/ffmpeg-components/glib--LICENSES--CC-BY-SA-3.0.txt); SHA-256: `3f941b3b89cf7b8370ceb83cc76d2120d471b58735d8ca60238a751a48d7f72f`; bytes: 22240.
- [crates--encoding_rs-0.8.42--LICENSE-MIT](tools/package/native-licences/ffmpeg-toolchain/crates--encoding_rs-0.8.42--LICENSE-MIT); SHA-256: `3fa4ca83dcc9237839b1bdeb2e6d16bdfb5ec0c5ce42b24694d8bbf0dcbef72c`; bytes: 1053.
- [crates--float-cmp-0.10.0--LICENSE](tools/package/native-licences/ffmpeg-toolchain/crates--float-cmp-0.10.0--LICENSE); SHA-256: `40be1e77825d7e49485a2e43d89bed29dfff29f8f529e71d3c683656021f0d08`; bytes: 1075.
- [crates--miniz_oxide-0.9.1--LICENSE](tools/package/native-licences/ffmpeg-toolchain/crates--miniz_oxide-0.9.1--LICENSE); SHA-256: `4108245a1f2df9d4e94df8abed5b4ba0759bb2f9b40a6b939f1be141077ae50b`; bytes: 1213.
- [cairo--util--cairo-trace--COPYING](tools/package/native-licences/ffmpeg-components/cairo--util--cairo-trace--COPYING); SHA-256: `421158645572270264a980b8b130dd988138e4dae20144e22455446e0ef90902`; bytes: 179.
- [crates--simd-adler32-0.3.10--LICENSE.md](tools/package/native-licences/ffmpeg-toolchain/crates--simd-adler32-0.3.10--LICENSE.md); SHA-256: `42a35170233e83e18856792e748de4c1ce4a63b2afce9a370c89ef3fe23f9f2d`; bytes: 1078.
- [libjxl--lib--extras--LICENSE.apngdis](tools/package/native-licences/ffmpeg-components/libjxl--lib--extras--LICENSE.apngdis); SHA-256: `4319c422c3bf10168877a83cd9ff848684b9e53dce9a68de0a3f454a825933f6`; bytes: 1017.
- [gnulib--COPYING](tools/package/native-licences/ffmpeg-components/gnulib--COPYING); SHA-256: `438610ba3d10f492dff9e17f7d53a5316e3f4b4adc5f79a33ac7110d5a5ee210`; bytes: 570.
- [libjxl--third_party--HEVCSoftware--cfg--LICENSE](tools/package/native-licences/ffmpeg-components/libjxl--third_party--HEVCSoftware--cfg--LICENSE); SHA-256: `44a2c5f2ce34d00a30554a44d3e51377852f84bc183dc1b9fb2b48ece976ebef`; bytes: 1744.
- [spirv-cross--LICENSES--Apache-2.0.txt](tools/package/native-licences/ffmpeg-components/spirv-cross--LICENSES--Apache-2.0.txt); SHA-256: `44b0a56e80b41a1b0a6bd1292515e806539fd97b30be54c2719e6c763190ab57`; bytes: 10343.
- [crates--rgb-0.8.53--LICENSE](tools/package/native-licences/ffmpeg-toolchain/crates--rgb-0.8.53--LICENSE); SHA-256: `457b464bc0fba8a3d67d2458569104f5611869f0c1563a1a12d9c51a0bca9261`; bytes: 1063.
- [crates--bytes-1.12.1--LICENSE](tools/package/native-licences/ffmpeg-toolchain/crates--bytes-1.12.1--LICENSE); SHA-256: `45f522cacecb1023856e46df79ca625dfc550c94910078bd8aec6e02880b3d42`; bytes: 1055.
- [openmpt--include--nlohmann-json--LICENSE.MIT](tools/package/native-licences/ffmpeg-components/openmpt--include--nlohmann-json--LICENSE.MIT); SHA-256: `46a65cffd1ea955132d95a8dd921640714a8d6b537d2e4e482d31145ae95b603`; bytes: 1076.
- [libssh--cmake--Modules--COPYING-CMAKE-SCRIPTS](tools/package/native-licences/ffmpeg-components/libssh--cmake--Modules--COPYING-CMAKE-SCRIPTS); SHA-256: `46cde7dc11e64c78d650b4851b88f6704b4665ff60f22a1caf68ceb15e217e5b`; bytes: 1327.
- [aom--LICENSE](tools/package/native-licences/ffmpeg-components/aom--LICENSE); SHA-256: `4764a286d8b2faeaf42f4418e7d7a28d58fc8fd4d00a3d0a7f44b0a4099de7f2`; bytes: 1316.
- [shaderc--third_party--LICENSE.spirv-tools](tools/package/native-licences/ffmpeg-components/shaderc--third_party--LICENSE.spirv-tools); SHA-256: `47e20ce182bc68fab1a0cfb129b03c326aaf4f2b6b7905aa9d376d31018bd29f`; bytes: 11650.
- [x265--source--dynamicHDR10--LICENSE.txt](tools/package/native-licences/ffmpeg-components/x265--source--dynamicHDR10--LICENSE.txt); SHA-256: `47f15d63e82eb8a4de6e46471d5f96cf6d052fd5355944a002c3157880248b69`; bytes: 849.
- [aom--third_party--fastfeat--LICENSE](tools/package/native-licences/ffmpeg-components/aom--third_party--fastfeat--LICENSE); SHA-256: `499041ddee5227b6f29ca06c17803e5fe24d60f243c69635cd76b7ba08d0ddd5`; bytes: 1504.
- [openal--gsl--LICENSE](tools/package/native-licences/ffmpeg-components/openal--gsl--LICENSE); SHA-256: `4c21dc82a1c7186ea754fd59d504c00947953a3401fe8e24eaa44109ef8e2555`; bytes: 1157.
- [crates--scan_fmt-0.2.6--LICENSE](tools/package/native-licences/ffmpeg-toolchain/crates--scan_fmt-0.2.6--LICENSE); SHA-256: `4d0814fe61e6458a52ce8c744f23c6e7fbdacd20f4f6452bc5f29b7790a98588`; bytes: 1074.
- [chromaprint--src--3rdparty--kissfft--LICENSES--BSD-3-Clause](tools/package/native-licences/ffmpeg-components/chromaprint--src--3rdparty--kissfft--LICENSES--BSD-3-Clause); SHA-256: `4d6bcab46f27d6d0c878e8305d4bdcfe040d52bf6656b9771f04c9fb9902c0ed`; bytes: 1830.
- [gcc--libstdc++-v3--src--c++17--fast_float--fast_float.h-L1-40.txt](tools/package/native-licences/ffmpeg-toolchain/gcc--libstdc++-v3--src--c++17--fast_float--fast_float.h-L1-40.txt); SHA-256: `4d9b892115759074c680ab242e3a377f6a8a2cd37a9c6a35aa9bd4a15b58c118`; bytes: 1592.
- [crates--arrayvec-0.7.6--LICENSE-MIT](tools/package/native-licences/ffmpeg-toolchain/crates--arrayvec-0.7.6--LICENSE-MIT); SHA-256: `4da95ec4ecb65b738d470b7d762894ad9c97da93e6cbfb18b570fc2c96f4b871`; bytes: 1071.
- [crates--nom-7.1.3--LICENSE](tools/package/native-licences/ffmpeg-toolchain/crates--nom-7.1.3--LICENSE); SHA-256: `4dbda04344456f09a7a588140455413a9ac59b6b26a1ef7cdf9c800c012d87f0`; bytes: 1065.
- [ffnvcodec-sdk13.0--include--ffnvcodec--nvEncodeAPI.h](tools/package/native-licences/ffmpeg-components/ffnvcodec-sdk13.0--include--ffnvcodec--nvEncodeAPI.h); SHA-256: `4fe4094541ef0f8a13249d97a8692dc5f835a6e9dd42eeadb3e2f7321d54dc7e`; bytes: 311883.
- [sdl--Xcode-iOS--Demos--data--bitmapfont--license.txt](tools/package/native-licences/ffmpeg-components/sdl--Xcode-iOS--Demos--data--bitmapfont--license.txt); SHA-256: `5059bc9c2f37b7e7a557685ae9330ecfd798537bdfde94de63a9c721c92a8856`; bytes: 13091.
- [libpng--LICENSES--MIT.txt](tools/package/native-licences/ffmpeg-components/libpng--LICENSES--MIT.txt); SHA-256: `508a77d2e7b51d98adeed32648ad124b7b30241a8e70b2e72c99f92d8e5874d1`; bytes: 1036.
- [libaribcaption--LICENSE](tools/package/native-licences/ffmpeg-components/libaribcaption--LICENSE); SHA-256: `5149f1ce4fe89190d86bfb440456701a3a7406fc2b19ef0d8b57661f62b32c04`; bytes: 1065.
- [crates--typenum-1.20.1--LICENSE-APACHE](tools/package/native-licences/ffmpeg-toolchain/crates--typenum-1.20.1--LICENSE-APACHE); SHA-256: `516b24e051bf5630880ebbd55c40a25ce9552ebaf8970a53e8976eb70e522406`; bytes: 10835.
- [fontconfig--COPYING](tools/package/native-licences/ffmpeg-components/fontconfig--COPYING); SHA-256: `51a51aa9823704fd90bccc616cdd17ebabb5b2b3e9cbde886ca02c7002288067`; bytes: 8616.
- [snappy--COPYING.notestdata](tools/package/native-licences/ffmpeg-components/snappy--COPYING.notestdata); SHA-256: `5221a36a801b981fbdfda7b87db64cff231a3b88223a066c325411b539df796f`; bytes: 1475.
- [lcevcdec--licenses--vma--LICENSE.txt](tools/package/native-licences/ffmpeg-components/lcevcdec--licenses--vma--LICENSE.txt); SHA-256: `52df2c03d6cfc9ffec13c9d3626c530fc9ce0cbe41d5ea3d10cd46edeb1aeb38`; bytes: 1099.
- [cairo--COPYING-MPL-1.1](tools/package/native-licences/ffmpeg-components/cairo--COPYING-MPL-1.1); SHA-256: `53692a2ed6c6a2c6ec9b32dd0b820dfae91e0a1fcdf625ca9ed0bdf8705fcc4f`; bytes: 25755.
- [snappy--COPYING](tools/package/native-licences/ffmpeg-components/snappy--COPYING); SHA-256: `55172044f7e241207117448a4d9d6ba1d0925c8ad66b5d4c08c70adfa9cc3de6`; bytes: 2645.
- [crates--rctree-0.6.0--LICENSE](tools/package/native-licences/ffmpeg-toolchain/crates--rctree-0.6.0--LICENSE); SHA-256: `554c76c3cb6277827297f0af0ce2dedc0d2bcfef92517f9b4766762ac502eb72`; bytes: 1114.
- [chromaprint--LICENSE.md](tools/package/native-licences/ffmpeg-components/chromaprint--LICENSE.md); SHA-256: `562cfe59627e0c4e8e3b066f3ff2e9736f83811ffe4c6c2c7796595aa7595ebd`; bytes: 1801.
- [crates--crossbeam-0.8.4--LICENSE-MIT](tools/package/native-licences/ffmpeg-toolchain/crates--crossbeam-0.8.4--LICENSE-MIT); SHA-256: `5734ed989dfca1f625b40281ee9f4530f91b2411ec01cb748223e7eb87e201ab`; bytes: 1099.
- [crates--weezl-0.1.12--LICENSE-MIT](tools/package/native-licences/ffmpeg-toolchain/crates--weezl-0.1.12--LICENSE-MIT); SHA-256: `573f5227db835cd30bbdd3aed3f82615f80119a4d5c82b4daf642dbfe2b6afde`; bytes: 1080.
- [spdx--text--LGPL-2.1-or-later.txt](tools/package/native-licences/ffmpeg-components/spdx--text--LGPL-2.1-or-later.txt); SHA-256: `5749785c8bdefafcb5d798270ed0a967036fe2ca63dcedade1627565dfef81d2`; bytes: 26001.
- [crates--color_quant-1.1.0--LICENSE](tools/package/native-licences/ffmpeg-toolchain/crates--color_quant-1.1.0--LICENSE); SHA-256: `592dc80f1a865d20d61a2006a2d29ce34a2bc28cd7e868ab300fdeed6da154ca`; bytes: 1083.
- [freetype--docs--FTL.TXT](tools/package/native-licences/ffmpeg-components/freetype--docs--FTL.TXT); SHA-256: `5a5ee54c5001bbad1cdc1a57cc3dd4c42199b2da09d39c7ee41fab002d02967f`; bytes: 6743.
- [uavs3d--COPYING](tools/package/native-licences/ffmpeg-components/uavs3d--COPYING); SHA-256: `5a8dcb7da222df8a81b6e334000f859248196335e2d28e1db9f3c552827d7cdf`; bytes: 1690.
- [glslang--LICENSES--BSD-3-Clause.txt](tools/package/native-licences/ffmpeg-components/glslang--LICENSES--BSD-3-Clause.txt); SHA-256: `5a93d5831e1297ab10fe643e1a631e83be392896da14ee2951285a79012df69d`; bytes: 1460.
- [libwebp--COPYING](tools/package/native-licences/ffmpeg-components/libwebp--COPYING); SHA-256: `5aec868f669e384a22372a4e8a1a6cd7d44c64cd451f960ca69cc170d1e13acf`; bytes: 1496.
- [libmp3lame--LICENSE](tools/package/native-licences/ffmpeg-components/libmp3lame--LICENSE); SHA-256: `5c1f8d44f1eacbea3e1c31ff6ee11a4e1690ccbed4ee4af16de3b6eb61dc69a8`; bytes: 503.
- [rav1e--ivf--LICENSE](tools/package/native-licences/ffmpeg-components/rav1e--ivf--LICENSE); SHA-256: `5d3c397a3aeeecbc417962e4df8e8432af8219fda8a56ebe601a638a1e76c522`; bytes: 1332.
- [libxml2--Copyright](tools/package/native-licences/ffmpeg-components/libxml2--Copyright); SHA-256: `5d4873884a890122a4b9b20ad56ac6f7da1d796a5bfcf04a427970ac96217626`; bytes: 1314.
- [crates--stable_deref_trait-1.2.0--LICENSE-MIT](tools/package/native-licences/ffmpeg-toolchain/crates--stable_deref_trait-1.2.0--LICENSE-MIT); SHA-256: `5e05b024f653a5ce199e77cbbbd42fb5553562ec714b819421ed0c3e552a75d7`; bytes: 1056.
- [mingw--mingw-w64-libraries--pseh--COPYING](tools/package/native-licences/ffmpeg-components/mingw--mingw-w64-libraries--pseh--COPYING); SHA-256: `5ece225da0c7f0dba84dc64d773b5231075e8fee61cbeceb9f774e939918e638`; bytes: 1062.
- [crates--tendril-0.5.1--LICENSE-MIT](tools/package/native-licences/ffmpeg-toolchain/crates--tendril-0.5.1--LICENSE-MIT); SHA-256: `60a7062291b01ba068f300612cdbdc20382ac1d4934f07bcdd7167c15299f309`; bytes: 1061.
- [gcc--libstdc++-v3--include--bits--stl_algobase.h-L39-48.txt](tools/package/native-licences/ffmpeg-toolchain/gcc--libstdc++-v3--include--bits--stl_algobase.h-L39-48.txt); SHA-256: `6119c050f397029762676a0ec89cc45ff3c250194bee0dc6a1cb678273979f91`; bytes: 551.
- [xz--COPYING](tools/package/native-licences/ffmpeg-components/xz--COPYING); SHA-256: `616a3ad264ce29b8f1cb97e53037b139d406899ca8d1f799651e17bfa09830b8`; bytes: 3119.
- [crates--fern-0.7.1--LICENSE](tools/package/native-licences/ffmpeg-toolchain/crates--fern-0.7.1--LICENSE); SHA-256: `618bcda011fe31b4710082efc2785b51da642e236ed99fc1b5e34229836c915e`; bytes: 1059.
- [crates--crc32fast-1.5.3--LICENSE-MIT](tools/package/native-licences/ffmpeg-toolchain/crates--crc32fast-1.5.3--LICENSE-MIT); SHA-256: `61d383b05b87d78f94d2937e2580cce47226d17823c0430fbcad09596537efcf`; bytes: 1097.
- [crates--string_cache-0.10.0--LICENSE-MIT](tools/package/native-licences/ffmpeg-toolchain/crates--string_cache-0.10.0--LICENSE-MIT); SHA-256: `62065228e42caebca7e7d7db1204cbb867033de5982ca4009928915e4095f3a3`; bytes: 1067.
- [glib--LICENSES--MPL-1.1.txt](tools/package/native-licences/ffmpeg-components/glib--LICENSES--MPL-1.1.txt); SHA-256: `6214f8b1300bb9f37b16ebc146f8f61af0187e0025042ff95c8b3030744a8795`; bytes: 23669.
- [rust-lang-rust--LICENSE-APACHE](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--LICENSE-APACHE); SHA-256: `62c7a1e35f56406896d7aa7ca52d0cc0d272ac022b5d2796e7d6905db8a3636a`; bytes: 9723.
- [mingw--mingw-w64-libraries--winpthreads--COPYING](tools/package/native-licences/ffmpeg-components/mingw--mingw-w64-libraries--winpthreads--COPYING); SHA-256: `63263614cdd29f2f93cba85e992f041b31f9fc7b4033692f31269489a8a1b177`; bytes: 2883.
- [openal--LICENSE-pffft](tools/package/native-licences/ffmpeg-components/openal--LICENSE-pffft); SHA-256: `64056328b3e7bc104e24ef96accc1a7abead156f0c02d1b87c97e3f3a28030de`; bytes: 1669.
- [crates--log-0.4.34--LICENSE-MIT](tools/package/native-licences/ffmpeg-toolchain/crates--log-0.4.34--LICENSE-MIT); SHA-256: `6485b8ed310d3f0340bf1ad1f47645069ce4069dcc6bb46c7d5c6faf41de1fdb`; bytes: 1071.
- [aom--PATENTS](tools/package/native-licences/ffmpeg-components/aom--PATENTS); SHA-256: `661fb8e504744e95587b556b94a58343448300606a41bea8c7a9b97125696e61`; bytes: 5701.
- [lv2--LICENSES--0BSD.txt](tools/package/native-licences/ffmpeg-components/lv2--LICENSES--0BSD.txt); SHA-256: `66461c6911980791fa5dd6a97e455a91fdcb1313db01a3c451fce04da8c85256`; bytes: 661.
- [crates--futures-channel-0.3.34--LICENSE-MIT](tools/package/native-licences/ffmpeg-toolchain/crates--futures-channel-0.3.34--LICENSE-MIT); SHA-256: `6652c868f35dfe5e8ef636810a4e576b9d663f3a17fb0f5613ad73583e1b88fd`; bytes: 1094.
- [spdx--text--MPL-2.0.txt](tools/package/native-licences/ffmpeg-toolchain/spdx--text--MPL-2.0.txt); SHA-256: `66a3107d5ad6a058aab753eaac2047ccb2ed0e39465dd0fe5844da3e300d5172`; bytes: 16727.
- [cairo--COPYING](tools/package/native-licences/ffmpeg-components/cairo--COPYING); SHA-256: `67228a9f7c5f9b67c58f556f1be178f62da4d9e2e6285318d8c74d567255abdf`; bytes: 1576.
- [fftw3--doc--license.texi](tools/package/native-licences/ffmpeg-components/fftw3--doc--license.texi); SHA-256: `68f733830a3b4dbf66815ca54b5637015517848c5f32f38f1ea2057782161a77`; bytes: 1842.
- [crates--wide-1.7.1--LICENSE-MIT.txt](tools/package/native-licences/ffmpeg-toolchain/crates--wide-1.7.1--LICENSE-MIT.txt); SHA-256: `69c62cda6938d510467c134dc0b5c83fb9c8ca847b9cd9d9d2fe9ab427c82100`; bytes: 1078.
- [openmpt--include--minimp3--LICENSE](tools/package/native-licences/ffmpeg-components/openmpt--include--minimp3--LICENSE); SHA-256: `6a1ee543e5282cd9061881edf462e6fdab181f328da71fc2c9a6950a80e94d01`; bytes: 6556.
- [avisynth--distrib--docs--english--source--avisynthdoc--license.rst](tools/package/native-licences/ffmpeg-components/avisynth--distrib--docs--english--source--avisynthdoc--license.rst); SHA-256: `6a52c5ef39b34ffc93f7391b4257a84d0a30f147b1b9b3273df0e7bfc9a039cf`; bytes: 11872.
- [spirv-headers--LICENSES--MIT.txt](tools/package/native-licences/ffmpeg-components/spirv-headers--LICENSES--MIT.txt); SHA-256: `6d7c9e9d7d12c8d3753bdb24417b84819ba4d6c2f025c37948113d86dc81eef9`; bytes: 1087.
- [lcms2--LICENSE](tools/package/native-licences/ffmpeg-components/lcms2--LICENSE); SHA-256: `6dbd60437f8ef91d8de1f08ad75882547fd4931bfcc3566a0735f28db1484d31`; bytes: 1080.
- [ffnvcodec--include--ffnvcodec--dynlink_loader.h](tools/package/native-licences/ffmpeg-components/ffnvcodec--include--ffnvcodec--dynlink_loader.h); SHA-256: `6dcf1ede1f38e91467fb8c06fa39894b8447f199446d6a4f008b083d7d0db9bf`; bytes: 28821.
- [openmpt--include--unrar--license.txt](tools/package/native-licences/ffmpeg-components/openmpt--include--unrar--license.txt); SHA-256: `6ecc1687808b7d66b24f874755abfed7464d9751ed0001cd4e8e5d9bf397ff8a`; bytes: 1976.
- [crates--anstream-0.6.19--LICENSE-MIT](tools/package/native-licences/ffmpeg-toolchain/crates--anstream-0.6.19--LICENSE-MIT); SHA-256: `6efb0476a1cc085077ed49357026d8c173bf33017278ef440f222fb9cbcb66e6`; bytes: 1062.
- [ffnvcodec--include--ffnvcodec--dynlink_loader.h-L1-26.txt](tools/package/native-licences/ffmpeg-components/ffnvcodec--include--ffnvcodec--dynlink_loader.h-L1-26.txt); SHA-256: `6f0d5ad2609c6fda3e0fb07fa286e7b46c2ea7b87ab12d926ab7a82c69ffe09d`; bytes: 1175.
- [crates--crossbeam-0.8.4--LICENSE-APACHE](tools/package/native-licences/ffmpeg-toolchain/crates--crossbeam-0.8.4--LICENSE-APACHE); SHA-256: `6f712474a3e3be1386d2d0c29449850ea788da64d35cff0fc8799acf741e9ecd`; bytes: 10852.
- [cairo--perf--COPYING](tools/package/native-licences/ffmpeg-components/cairo--perf--COPYING); SHA-256: `6f93b45ea874706058ae35bc02df79c3f9daf00948672eea8394cc25d1327d49`; bytes: 229.
- [xxhash--LICENSE](tools/package/native-licences/ffmpeg-components/xxhash--LICENSE); SHA-256: `6ffedbc0f7878612d2b23589f1ff2ab15633e1df7963a5d9fc750ec5500c7e7a`; bytes: 1389.
- [aom--third_party--x86inc--LICENSE](tools/package/native-licences/ffmpeg-components/aom--third_party--x86inc--LICENSE); SHA-256: `719d8fa235f2068e0ae6d6a7dceb0a7720d7840f0f0ebed29957989e6ded3cd8`; bytes: 936.
- [vidstab--LICENSE](tools/package/native-licences/ffmpeg-components/vidstab--LICENSE); SHA-256: `71c1072d2c2597bbe25f7defc01f9082f4bae9b54ba73a8c5c7ca423fef92e8d`; bytes: 603.
- [ffnvcodec-sdk13.0--include--ffnvcodec--nvEncodeAPI.h-L1-26.txt](tools/package/native-licences/ffmpeg-components/ffnvcodec-sdk13.0--include--ffnvcodec--nvEncodeAPI.h-L1-26.txt); SHA-256: `72b60be67644d841bfd54a042875b5846294d357040dd7ac8e38bde20d9e8f97`; bytes: 1199.
- [openjpeg--thirdparty--libpng--LICENSE](tools/package/native-licences/ffmpeg-components/openjpeg--thirdparty--libpng--LICENSE); SHA-256: `7317e078e2d3b5d7ba5a6159e650945153262b44b76f6700f8e9edb261c5143e`; bytes: 5345.
- [openmpt--include--rtaudio--LICENSE](tools/package/native-licences/ffmpeg-components/openmpt--include--rtaudio--LICENSE); SHA-256: `73eb32613a621c134b33fbe3c661562dcf5f81f0558af13d483fc241eb21be7b`; bytes: 1360.
- [crates--either-1.15.0--LICENSE-MIT](tools/package/native-licences/ffmpeg-toolchain/crates--either-1.15.0--LICENSE-MIT); SHA-256: `7576269ea71f767b99297934c0b2367532690f8c4badc695edf8e04ab6a1e545`; bytes: 1043.
- [vvenc--thirdparty--simde--COPYING](tools/package/native-licences/ffmpeg-components/vvenc--thirdparty--simde--COPYING); SHA-256: `75ce0a8c5a7bff42fbd6f8f3b469b518132132c4f4948fb8d02b1ccb5d0df9d8`; bytes: 1077.
- [zimg--COPYING](tools/package/native-licences/ffmpeg-components/zimg--COPYING); SHA-256: `7637386b5f81e8a719ca336233149005e5fa28b5e6054ea7b67de49355b0ad40`; bytes: 484.
- [crates--core_detect-1.0.0--LICENSE-APACHE](tools/package/native-licences/ffmpeg-toolchain/crates--core_detect-1.0.0--LICENSE-APACHE); SHA-256: `769f80b5bcb42ed0af4e4d2fd74e1ac9bf843cb80c5a29219d1ef3544428a6bb`; bytes: 10846.
- [crates--gif-0.14.2--LICENSE-MIT](tools/package/native-licences/ffmpeg-toolchain/crates--gif-0.14.2--LICENSE-MIT); SHA-256: `77257f3d2181236b1aee78920238062ae64efe13c5d858b2db126e79c9e1b14f`; bytes: 1071.
- [openmpt--include--flac--COPYING.Xiph](tools/package/native-licences/ffmpeg-components/openmpt--include--flac--COPYING.Xiph); SHA-256: `7866ee98760fc1f0156b4fe6bf530257e02be487ab3fd94e2b63799dd32d6b2c`; bytes: 1509.
- [glslang--LICENSES--BSD-2-Clause.txt](tools/package/native-licences/ffmpeg-components/glslang--LICENSES--BSD-2-Clause.txt); SHA-256: `789daa57a2ebb49cfc3e67cd1a1f994d5dc221138a8c3cd1934b2ed47b86d356`; bytes: 1245.
- [crates--matrixmultiply-0.3.11--LICENSE-MIT](tools/package/native-licences/ffmpeg-toolchain/crates--matrixmultiply-0.3.11--LICENSE-MIT); SHA-256: `792d075c7bad6dac258a44e799eb64cbf465e24d9932d27669be08c5ec957e27`; bytes: 1159.
- [freetype--src--bdf--README](tools/package/native-licences/ffmpeg-components/freetype--src--bdf--README); SHA-256: `7984455e7e5a9faba3797c8bf095fbe10cc846316b7320aff8c58402e22b82fe`; bytes: 5972.
- [crates--miniz_oxide-0.9.1--LICENSE-MIT.md](tools/package/native-licences/ffmpeg-toolchain/crates--miniz_oxide-0.9.1--LICENSE-MIT.md); SHA-256: `799e9ca9d179295ef372f25d3769cdda7d25bb2668add6a6a1e22d1e4c678b8d`; bytes: 1212.
- [crates--bitstream-io-4.2.0--LICENSE-MIT](tools/package/native-licences/ffmpeg-toolchain/crates--bitstream-io-4.2.0--LICENSE-MIT); SHA-256: `7a65c85c057a5538fdd8215b7aa2f3e0353f3b07c3e00bb409070b2b81375895`; bytes: 1062.
- [openapv--LICENSE](tools/package/native-licences/ffmpeg-components/openapv--LICENSE); SHA-256: `7ad8e53c0c3e24e7ba64dbcad5e7706108f3dc67cf6515ef761adac0a39dab25`; bytes: 1503.
- [rav1e--PATENTS](tools/package/native-licences/ffmpeg-components/rav1e--PATENTS); SHA-256: `7b14a70c194b19dbd0625e7eac839a63200f67484521ce5e8d8244b127e8907a`; bytes: 5702.
- [crates--gimli-0.34.0--LICENSE-MIT](tools/package/native-licences/ffmpeg-toolchain/crates--gimli-0.34.0--LICENSE-MIT); SHA-256: `7b63ecd5f1902af1b63729947373683c32745c16a10e8e6292e2e2dcd7e90ae0`; bytes: 1071.
- [sratom--LICENSES--0BSD.txt](tools/package/native-licences/ffmpeg-components/sratom--LICENSES--0BSD.txt); SHA-256: `7be8d0a9263cdc6ee30484b086606c231df81e227ae7a42ad4e04bf0c7213fd2`; bytes: 661.
- [openmpt--include--r8brain--LICENSE](tools/package/native-licences/ffmpeg-components/openmpt--include--r8brain--LICENSE); SHA-256: `7c5a4a097ede04a72f3fd444cfe9c788433f46c2b539b152de8921521eeac877`; bytes: 1076.
- [crates--precomputed-hash-0.1.1--LICENSE](tools/package/native-licences/ffmpeg-toolchain/crates--precomputed-hash-0.1.1--LICENSE); SHA-256: `7ca6700600dfa9c9497bf5556365067daa802c871ea78239f129309c7a2048f7`; bytes: 1078.
- [sdl--src--hidapi--LICENSE.txt](tools/package/native-licences/ffmpeg-components/sdl--src--hidapi--LICENSE.txt); SHA-256: `7d3b087c34f35d4d538e3bcddd1ff8f66e92f9ef336881999482800ddf840913`; bytes: 530.
- [openssl--LICENSE.txt](tools/package/native-licences/ffmpeg-components/openssl--LICENSE.txt); SHA-256: `7d5450cb2d142651b8afa315b5f238efc805dad827d91ba367d8516bc9d49e7a`; bytes: 10175.
- [crates--memchr-2.8.3--UNLICENSE](tools/package/native-licences/ffmpeg-toolchain/crates--memchr-2.8.3--UNLICENSE); SHA-256: `7e12e5df4bae12cb21581ba157ced20e1986a0508dd10d0e8a4ab9a4cf94e85c`; bytes: 1211.
- [glib--LICENSES--AFL-2.0.txt](tools/package/native-licences/ffmpeg-components/glib--LICENSES--AFL-2.0.txt); SHA-256: `7ecc7db84298adb05d2cf10339c63a5315a1c5c270a68d97d7d40a53b508ccde`; bytes: 8987.
- [libopus--LICENSE_PLEASE_READ.txt](tools/package/native-licences/ffmpeg-components/libopus--LICENSE_PLEASE_READ.txt); SHA-256: `7efb4989e0cd1b256229bdf2f09300c5d14e35db0e7476bfb87fac243498273d`; bytes: 703.
- [openmpt--include--rtmidi--LICENSE](tools/package/native-licences/ffmpeg-components/openmpt--include--rtmidi--LICENSE); SHA-256: `7fa091d9c1aa492ebfcafa9f919d27bbce61e4f048ece2dfc3b7f93181e9e364`; bytes: 1349.
- [openjpeg--src--bin--wx--OPJViewer--source--license.txt](tools/package/native-licences/ffmpeg-components/openjpeg--src--bin--wx--OPJViewer--source--license.txt); SHA-256: `8081c33f6953950dcf424aa844714658b73ada0fcaea16e4487f5fa07ef0960d`; bytes: 1683.
- [crates--minimal-lexical-0.2.1--LICENSE-APACHE](tools/package/native-licences/ffmpeg-toolchain/crates--minimal-lexical-0.2.1--LICENSE-APACHE); SHA-256: `8173d5c29b4f956d532781d2b86e4e30f83e6b7878dce18c919451d6ba707c90`; bytes: 10850.
- [gmp--COPYINGv2](tools/package/native-licences/ffmpeg-components/gmp--COPYINGv2); SHA-256: `8177f97513213526df2cf6184d8ff986c675afb514d4e68a404010521b880643`; bytes: 18092.
- [libvpx--LICENSE](tools/package/native-licences/ffmpeg-components/libvpx--LICENSE); SHA-256: `8267348d5af1262c11d1a08de2f5afc77457755f1ac658627dd9acf71011d615`; bytes: 1537.
- [crates--encoding_rs-0.8.42--LICENSE-WHATWG](tools/package/native-licences/ffmpeg-toolchain/crates--encoding_rs-0.8.42--LICENSE-WHATWG); SHA-256: `838118388fe5c2e7f1dbbaeed13e1c7f3ebf88be91319c7c1d77c18e987d1a50`; bytes: 1501.
- [crates--zerocopy-0.8.63--LICENSE-BSD](tools/package/native-licences/ffmpeg-toolchain/crates--zerocopy-0.8.63--LICENSE-BSD); SHA-256: `83c1763356e822adde0a2cae748d938a73fdc263849ccff6b27776dff213bd32`; bytes: 1275.
- [libjxl--LICENSE](tools/package/native-licences/ffmpeg-components/libjxl--LICENSE); SHA-256: `8405932022a556380c2d8c272eff154a923feb197233f348ce5f7334fb0a5ede`; bytes: 1508.
- [libtheora--COPYING](tools/package/native-licences/ffmpeg-components/libtheora--COPYING); SHA-256: `8417fad7da775735564e209484a2e011e0fa201e94f01fdbee6e4977e478e6fc`; bytes: 1470.
- [crates--bytemuck-1.25.2--LICENSE-ZLIB](tools/package/native-licences/ffmpeg-toolchain/crates--bytemuck-1.25.2--LICENSE-ZLIB); SHA-256: `84b34dd7608f7fb9b17bd588a6bf392bf7de504e2716f024a77d89f1b145a151`; bytes: 851.
- [crates--core_detect-1.0.0--LICENSE-MIT](tools/package/native-licences/ffmpeg-toolchain/crates--core_detect-1.0.0--LICENSE-MIT); SHA-256: `8569ebf6bf52937b961d9c9c934d8400a2bb6b09651a9afacbb3fc18fe5c09b1`; bytes: 1076.
- [crates--bitreader-0.3.11--LICENSE-MIT](tools/package/native-licences/ffmpeg-toolchain/crates--bitreader-0.3.11--LICENSE-MIT); SHA-256: `8583712ee2b062ff3d4d6d3e16f19ff0f92bc3a0a4beeec11a81ef00146fbd4f`; bytes: 1055.
- [crates--adler2-2.0.1--LICENSE-0BSD](tools/package/native-licences/ffmpeg-toolchain/crates--adler2-2.0.1--LICENSE-0BSD); SHA-256: `861399f8c21c042b110517e76dc6b63a2b334276c8cf17412fc3c8908ca8dc17`; bytes: 665.
- [vvenc--thirdparty--nlohmann_json--LICENSE.MIT](tools/package/native-licences/ffmpeg-components/vvenc--thirdparty--nlohmann_json--LICENSE.MIT); SHA-256: `86b998c792894ccb911a1cb7994f7a9652894e7a094c0b5e45be2f553f45cf14`; bytes: 1076.
- [mingw-std-threads--LICENSE](tools/package/native-licences/ffmpeg-components/mingw-std-threads--LICENSE); SHA-256: `86c148320eb0acc26607ed347e0fde9f49a236d0ec5291d36dc6a7e0e1d26b9f`; bytes: 1296.
- [crates--markup5ever-0.39.0--LICENSE-MIT](tools/package/native-licences/ffmpeg-toolchain/crates--markup5ever-0.39.0--LICENSE-MIT); SHA-256: `86dd7f026f916daf7511e39951ad8ea8cf55a8db67ae64060dacf829761c18f3`; bytes: 1076.
- [ffnvcodec--include--ffnvcodec--nvEncodeAPI.h](tools/package/native-licences/ffmpeg-components/ffnvcodec--include--ffnvcodec--nvEncodeAPI.h); SHA-256: `8776fddcb8febc6aec4d73989b1f21831eb30306bc583da55b4bf0c14a1dc228`; bytes: 313554.
- [mingw--DISCLAIMER.PD](tools/package/native-licences/ffmpeg-components/mingw--DISCLAIMER.PD); SHA-256: `87f33608570312a0f2a9745edcb2527275df813b13982e8c3b3f893d88a4141a`; bytes: 454.
- [vvenc--LICENSE.txt](tools/package/native-licences/ffmpeg-components/vvenc--LICENSE.txt); SHA-256: `88330a2cc59b9dd90674f8759900bc9c06e9efc8799dadda067609addefb49d1`; bytes: 1768.
- [libpng--LICENSES--MIT-0.txt](tools/package/native-licences/ffmpeg-components/libpng--LICENSES--MIT-0.txt); SHA-256: `8876cdca96eb380d16d5ea32bf4529d85e87dedc7765ae2861a9bec7f34acbed`; bytes: 878.
- [libxml2--list.c](tools/package/native-licences/ffmpeg-components/libxml2--list.c); SHA-256: `8a04740bfd8a37f3006bfc0404aa31429e56ef991cddcd47707ce2a9b1d98506`; bytes: 15193.
- [crates--derive_more-2.1.1--LICENSE](tools/package/native-licences/ffmpeg-toolchain/crates--derive_more-2.1.1--LICENSE); SHA-256: `8a35369f3ca263b3c62fbb5032947e53b6bfebc6c8a4d1bb982de1c069f6fba5`; bytes: 1080.
- [fftw3--COPYRIGHT](tools/package/native-licences/ffmpeg-components/fftw3--COPYRIGHT); SHA-256: `8a74b35d541d93fdf58a22a3d3baa48ae3edbf6d715edfeb6457c21968ae43ac`; bytes: 844.
- [crates--adler2-2.0.1--LICENSE-APACHE](tools/package/native-licences/ffmpeg-toolchain/crates--adler2-2.0.1--LICENSE-APACHE); SHA-256: `8ada45cd9f843acf64e4722ae262c622a2b3b3007c7310ef36ac1061a30f6adb`; bytes: 10860.
- [opencore-amr--LICENSE](tools/package/native-licences/ffmpeg-components/opencore-amr--LICENSE); SHA-256: `8b3f1762349248d444ab9acbafe73941254e36e1064954da56bb9ddbd5873ddb`; bytes: 10271.
- [crates--idna_adapter-1.2.2--LICENSE-MIT](tools/package/native-licences/ffmpeg-toolchain/crates--idna_adapter-1.2.2--LICENSE-MIT); SHA-256: `8b43ce8accd61e9d370b5ca9e9c4f953279b5c239926c62315b40e24df51b726`; bytes: 1062.
- [lcms2--utils--jpgicc--LICENSE_iccjpeg](tools/package/native-licences/ffmpeg-components/lcms2--utils--jpgicc--LICENSE_iccjpeg); SHA-256: `8baac37d14eed89b82ffcb041677dd701164eb5cc0f26e165fe47eb11afa0dca`; bytes: 3234.
- [crates--slab-0.4.12--LICENSE](tools/package/native-licences/ffmpeg-toolchain/crates--slab-0.4.12--LICENSE); SHA-256: `8ce0830173fdac609dfb4ea603fdc002c2f4af0dc9b1a005653f5da9cf534b18`; bytes: 1055.
- [gcc--COPYING3](tools/package/native-licences/ffmpeg-toolchain/gcc--COPYING3); SHA-256: `8ceb4b9ee5adedde47b31e975c1d90c73ad27b6b165a1dcd80c7c545eb65b903`; bytes: 35147.
- [crates--cairo-rs-0.22.9--LICENSE](tools/package/native-licences/ffmpeg-toolchain/crates--cairo-rs-0.22.9--LICENSE); SHA-256: `8cf56d10131ce201cf69ab74b111d3ebac1acca3833d7efb39ae357224b70edb`; bytes: 1024.
- [vulkan-loader--LICENSE](tools/package/native-licences/ffmpeg-components/vulkan-loader--LICENSE); SHA-256: `8d4d279343d72e5b9e06bbe38c1ad8660fa8eabc217164a5b482ddf4ab0dba9d`; bytes: 1074.
- [openmpt--include--premake--binmodules--luasocket--LICENSE](tools/package/native-licences/ffmpeg-components/openmpt--include--premake--binmodules--luasocket--LICENSE); SHA-256: `8e8c6314d9e78fe452ee355167f2c40cfbee8207e14dcb5ddd4a2655cb5c6aad`; bytes: 1080.
- [crates--dav1d-0.11.1--LICENSE](tools/package/native-licences/ffmpeg-toolchain/crates--dav1d-0.11.1--LICENSE); SHA-256: `8eb4fb5a6505da473ee195f326007c8c7e28357e3e6a11e293ce2a480384030c`; bytes: 1069.
- [ffnvcodec--include--ffnvcodec--nvEncodeAPI.h-L1-26.txt](tools/package/native-licences/ffmpeg-components/ffnvcodec--include--ffnvcodec--nvEncodeAPI.h-L1-26.txt); SHA-256: `8f115901902ad05ce3a1ba48ae15393a1853ac0a3e7835ebe986cc80e1039b19`; bytes: 1199.
- [spirv-cross--LICENSES--MIT.txt](tools/package/native-licences/ffmpeg-components/spirv-cross--LICENSES--MIT.txt); SHA-256: `8f25018489d6fe0dec34a352314c38dc146247b7de65735790f4398a92afa84b`; bytes: 1108.
- [gme--gme--ext--LICENSE](tools/package/native-licences/ffmpeg-components/gme--gme--ext--LICENSE); SHA-256: `8fb093f26ed0d78c8ca033bbec7063ac5b34c5d2475e6bd121d03ccfaaf2355f`; bytes: 1089.
- [openmpt--include--pugixml--LICENSE.md](tools/package/native-licences/ffmpeg-components/openmpt--include--pugixml--LICENSE.md); SHA-256: `90974fbb120e966b452654eaae3ba6ee55f3647db3b28918a7649733ee99da97`; bytes: 1079.
- [crates--moxcms-0.8.1--LICENSE-APACHE.md](tools/package/native-licences/ffmpeg-toolchain/crates--moxcms-0.8.1--LICENSE-APACHE.md); SHA-256: `90bf2d659c43045111b65c733ab2a6d4cbcb422a098368c8c58a9ba3db4ed0c5`; bytes: 11348.
- [lv2--LICENSES--MIT.txt](tools/package/native-licences/ffmpeg-components/lv2--LICENSES--MIT.txt); SHA-256: `91276db973f25602d1aa43491f59cbc84cb88e6f151e1d0cc82a755563ce0195`; bytes: 1023.
- [libjxl--PATENTS](tools/package/native-licences/ffmpeg-components/libjxl--PATENTS); SHA-256: `91915f8ae056a68a3c5bdf05d9f6f78bb6903e27a8ca3a8434c9e4ac87300575`; bytes: 1333.
- [openmpt--include--ancient--LICENSE](tools/package/native-licences/ffmpeg-components/openmpt--include--ancient--LICENSE); SHA-256: `92b1bae3691d85f84908a3f3eaf3a46ddadd603b2bf90f9e787177adceb9cc77`; bytes: 1323.
- [openmpt--include--opusenc--COPYING](tools/package/native-licences/ffmpeg-components/openmpt--include--opusenc--COPYING); SHA-256: `93b17ab56b8230127fea532be0dcb4e6d71e66ab5e8ce5d6ae8785d7288b164f`; bytes: 1522.
- [x265--source--dynamicHDR10--json11--LICENSE.txt](tools/package/native-licences/ffmpeg-components/x265--source--dynamicHDR10--json11--LICENSE.txt); SHA-256: `950e288a2548cb33f6a90d23958806b0803f510ab17c600d661619a73ae3a6c8`; bytes: 1057.
- [vulkan-headers--LICENSE.md](tools/package/native-licences/ffmpeg-components/vulkan-headers--LICENSE.md); SHA-256: `95ad366d23fadf701d355bc45fb8b82ae2d700239471d35d41286ac3b08ff903`; bytes: 495.
- [crates--rustc-hash-2.1.3--LICENSE-APACHE](tools/package/native-licences/ffmpeg-toolchain/crates--rustc-hash-2.1.3--LICENSE-APACHE); SHA-256: `95bd3988beee069fa2848f648dab43cc6e0b2add2ad6bcb17360caf749802bcc`; bytes: 9722.
- [gcc--libstdc++-v3--include--bits--stl_vector.h-L39-48.txt](tools/package/native-licences/ffmpeg-toolchain/gcc--libstdc++-v3--include--bits--stl_vector.h-L39-48.txt); SHA-256: `962c14eeb311aaa3eb6b509e220bebbd58fe0a9647931e9d0c672075c6a4bdb7`; bytes: 547.
- [aom--third_party--googletest--src--LICENSE](tools/package/native-licences/ffmpeg-components/aom--third_party--googletest--src--LICENSE); SHA-256: `9702de7e4117a8e2b20dafab11ffda58c198aede066406496bef670d40a22138`; bytes: 1475.
- [davs2--COPYING](tools/package/native-licences/ffmpeg-components/davs2--COPYING); SHA-256: `971f09fd8dedc915472df12845fb7c653563689672fb1a658e28004887ba4a07`; bytes: 18121.
- [libsamplerate--docs--license.md](tools/package/native-licences/ffmpeg-components/libsamplerate--docs--license.md); SHA-256: `9722032e4b5684f0ecd399480183a9029623636add1e9515621defaf8dbcf3ed`; bytes: 377.
- [crates--equator-0.4.2--LICENSE](tools/package/native-licences/ffmpeg-toolchain/crates--equator-0.4.2--LICENSE); SHA-256: `97d3424e347e8fa236806725ce9837bb453d4dfc9ce1d4733fd6023a8038000a`; bytes: 1062.
- [openssl--external--perl--Text-Template-1.56--LICENSE](tools/package/native-licences/ffmpeg-components/openssl--external--perl--Text-Template-1.56--LICENSE); SHA-256: `9837f05336ef3cbacb6a96e1672a0426d81ad01191f214b8d48e22ca62338181`; bytes: 18412.
- [mingw--COPYING](tools/package/native-licences/ffmpeg-components/mingw--COPYING); SHA-256: `99a69660981156c21336fdb5661f89341b013c94e4bf9e1c7467b4745718397f`; bytes: 2326.
- [mbedtls--LICENSE](tools/package/native-licences/ffmpeg-components/mbedtls--LICENSE); SHA-256: `9b405ef4c89342f5eae1dd828882f931747f71001cfba7d114801039b52ad09b`; bytes: 29852.
- [crates--zerocopy-0.8.63--LICENSE-APACHE](tools/package/native-licences/ffmpeg-toolchain/crates--zerocopy-0.8.63--LICENSE-APACHE); SHA-256: `9d185ac6703c4b0453974c0d85e9eee43e6941009296bb1f5eb0b54e2329e9f3`; bytes: 11350.
- [gcc--COPYING.RUNTIME](tools/package/native-licences/ffmpeg-toolchain/gcc--COPYING.RUNTIME); SHA-256: `9d6b43ce4d8de0c878bf16b54d8e7a10d9bd42b75178153e3af6a815bdc90f74`; bytes: 3324.
- [gcc--libstdc++-v3--src--c++17--ryu--d2s.c-L1-16.txt](tools/package/native-licences/ffmpeg-toolchain/gcc--libstdc++-v3--src--c++17--ryu--d2s.c-L1-16.txt); SHA-256: `9d9e6a10dd8395e18688b61ef492c862560f1ef590135f33bbed392d1695c552`; bytes: 652.
- [crates--bytemuck-1.25.2--LICENSE-MIT](tools/package/native-licences/ffmpeg-toolchain/crates--bytemuck-1.25.2--LICENSE-MIT); SHA-256: `9df9ba60a11af705f2e451b53762686e615d86f76b169cf075c3237730dbd7e2`; bytes: 1110.
- [spirv-headers--LICENSES--CC-BY-4.0.txt](tools/package/native-licences/ffmpeg-components/spirv-headers--LICENSES--CC-BY-4.0.txt); SHA-256: `9e5f1b3c610b9c2da5c313bf81d577a7d1acec686bdb0384edefa6df0f90cd94`; bytes: 18656.
- [cairo--COPYING-LGPL-2.1](tools/package/native-licences/ffmpeg-components/cairo--COPYING-LGPL-2.1); SHA-256: `9e9e8608c4cdda51a78cc3a385f4ec9a2e4c96d5ecad74ac8bca5fca3e563b7d`; bytes: 26533.
- [openmpt--include--cryptopp--License.txt](tools/package/native-licences/ffmpeg-components/openmpt--include--cryptopp--License.txt); SHA-256: `9f3af322ff503edfa605f8559a704b6e2f0ea78227841917a3729ec0fbeb42f4`; bytes: 3948.
- [openmpt--include--pthread-win32--docs--COPYING.FSF.md](tools/package/native-licences/ffmpeg-components/openmpt--include--pthread-win32--docs--COPYING.FSF.md); SHA-256: `a190dc9c8043755d90f8b0a75fa66b9e42d4af4c980bf5ddc633f0124db3cee7`; bytes: 26430.
- [glib--LICENSES--CC0-1.0.txt](tools/package/native-licences/ffmpeg-components/glib--LICENSES--CC0-1.0.txt); SHA-256: `a2010f343487d3f7618affe54f789f5487602331c0a8d03f49e9a7c547cf0499`; bytes: 7048.
- [chromaprint--src--3rdparty--kissfft--COPYING](tools/package/native-licences/ffmpeg-components/chromaprint--src--3rdparty--kissfft--COPYING); SHA-256: `a2840585f8411be8e6826a31ef15ae65c950bd74a2437a73b013398a934ad0c6`; bytes: 246.
- [rust-lang-rust--library--stdarch--LICENSE-APACHE](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--stdarch--LICENSE-APACHE); SHA-256: `a60eea817514531668d7e00765731449fe14d059d3249e0bc93b36de45f759f2`; bytes: 10847.
- [openjpeg--LICENSE](tools/package/native-licences/ffmpeg-components/openjpeg--LICENSE); SHA-256: `a6af136f3e15038a666b61f376612a07d9a4e48cb7c01adbf3e33b3f14ab49b6`; bytes: 2112.
- [vmaf--LICENSE](tools/package/native-licences/ffmpeg-components/vmaf--LICENSE); SHA-256: `a6fdb51d02b9dfe198e55534bb8047fe6d756eda117f4ff83de98f92c1952710`; bytes: 2833.
- [crates--typenum-1.20.1--LICENSE-MIT](tools/package/native-licences/ffmpeg-toolchain/crates--typenum-1.20.1--LICENSE-MIT); SHA-256: `a825bd853ab71619a4923d7b4311221427848070ff44d990da39b0b274c1683f`; bytes: 1083.
- [gmp--COPYING.LESSERv3](tools/package/native-licences/ffmpeg-components/gmp--COPYING.LESSERv3); SHA-256: `a853c2ffec17057872340eee242ae4d96cbf2b520ae27d903e1b2fef1a5f9d1c`; bytes: 7639.
- [crates--libc-0.2.172--LICENSE-MIT](tools/package/native-licences/ffmpeg-toolchain/crates--libc-0.2.172--LICENSE-MIT); SHA-256: `a8d47ff51ca256f56a8932dba07660672dbfe3004257ca8de708aac1415937a1`; bytes: 1076.
- [lv2--LICENSES--W3C-20150513.txt](tools/package/native-licences/ffmpeg-components/lv2--LICENSES--W3C-20150513.txt); SHA-256: `a9aace21e4e1d68bed3ec1b2fa47ad7d277255f8a70ec3a2638f783911d0515d`; bytes: 1820.
- [spdx--text--GPL-2.0-or-later.txt](tools/package/native-licences/ffmpeg-components/spdx--text--GPL-2.0-or-later.txt); SHA-256: `aaf135472f81c5b4a0dca9367e5bb5e9750032b5bebe5442b36e4c0a47430df3`; bytes: 17337.
- [rust-lang-rust--library--compiler-builtins--LICENSE.txt](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--compiler-builtins--LICENSE.txt); SHA-256: `ab6eec6caf0fa5775e411c7a8bc6a45c4ef2956b0980b157ab74fc5cd62a928b`; bytes: 15078.
- [crates--av1-grain-0.2.4--LICENSE](tools/package/native-licences/ffmpeg-toolchain/crates--av1-grain-0.2.4--LICENSE); SHA-256: `acc9e236b0011c638714a16f5634fa5bcd3be111182e237c3049db700c3521e2`; bytes: 1332.
- [serd--COPYING](tools/package/native-licences/ffmpeg-components/serd--COPYING); SHA-256: `ae223adebe7cc1ee0716e0f926d1ecc8e42c6e4da7e1d7418c9c07fae244bbde`; bytes: 751.
- [mingw--mingw-w64-libraries--libmangle--COPYING](tools/package/native-licences/ffmpeg-components/mingw--mingw-w64-libraries--libmangle--COPYING); SHA-256: `ae7a4090983e6ea0780c60c454016fd5e93b414b0de26ad041608ec66fbb54bb`; bytes: 1109.
- [spdx--text--MIT.txt](tools/package/native-licences/ffmpeg-toolchain/spdx--text--MIT.txt); SHA-256: `b05785f9f18e6716bab63424b11454513b9943a222595b70411009202fc592b5`; bytes: 1078.
- [crates--crossbeam-channel-0.5.15--LICENSE-THIRD-PARTY](tools/package/native-licences/ffmpeg-toolchain/crates--crossbeam-channel-0.5.15--LICENSE-THIRD-PARTY); SHA-256: `b16db96b93b1d7cf7bea533f572091ec6bca3234fbe0a83038be772ff391a44c`; bytes: 33447.
- [glib--docs--reference--COPYING](tools/package/native-licences/ffmpeg-components/glib--docs--reference--COPYING); SHA-256: `b1ec1d0e5947f81e815d8771f7d4d90671a94bb10a42dc687fb566de461a57aa`; bytes: 1698.
- [glslang--LICENSES--Apache-2.0.txt](tools/package/native-licences/ffmpeg-components/glslang--LICENSES--Apache-2.0.txt); SHA-256: `b22c5c23f3d598370ef51d7e539d5d5074207344fd86e41433f413e116f6a4f7`; bytes: 10715.
- [lcevcdec--licenses--conan-center-index--LICENSE.txt](tools/package/native-licences/ffmpeg-components/lcevcdec--licenses--conan-center-index--LICENSE.txt); SHA-256: `b35b9e39a7900cbd38190afff863f5a4eb2f04c8f9ceaff7afdb0523185f57c9`; bytes: 1065.
- [crates--data-url-0.3.2--LICENSE-MIT](tools/package/native-licences/ffmpeg-toolchain/crates--data-url-0.3.2--LICENSE-MIT); SHA-256: `b38f11f6096706e6de553dabe2a7ed142d59b6fa8c97e290c67496154745cdd5`; bytes: 1072.
- [libbluray--COPYING](tools/package/native-licences/ffmpeg-components/libbluray--COPYING); SHA-256: `b3aa400aca6d2ba1f0bd03bd98d03d1fe7489a3bbb26969d72016360af8a5c9d`; bytes: 24478.
- [rubberband--src--ext--speex--COPYING](tools/package/native-licences/ffmpeg-components/rubberband--src--ext--speex--COPYING); SHA-256: `b3da65c2cff5522b5a22438afb1fa99873e6567a2aebb17b198c58b15b09d5f3`; bytes: 1774.
- [crates--winapi-0.3.9--LICENSE-APACHE](tools/package/native-licences/ffmpeg-toolchain/crates--winapi-0.3.9--LICENSE-APACHE); SHA-256: `b40930bbcf80744c86c46a12bc9da056641d722716c378f5659b9e555ef833e1`; bytes: 11357.
- [shaderc--third_party--LICENSE.glslang](tools/package/native-licences/ffmpeg-components/shaderc--third_party--LICENSE.glslang); SHA-256: `b5a00e94f058edc87e05978329b55730d8689abe61205d9018443d03de4f07da`; bytes: 8280.
- [openal--LICENSE.BSD-3-Clause.txt](tools/package/native-licences/ffmpeg-components/openal--LICENSE.BSD-3-Clause.txt); SHA-256: `b5a08cf98996dd83aa906a72c163600f6cb17a65ce546a553815a1267abd43ff`; bytes: 1652.
- [vapoursynth--COPYING.LESSER](tools/package/native-licences/ffmpeg-components/vapoursynth--COPYING.LESSER); SHA-256: `b634ab5640e258563c536e658cad87080553df6f34f62269a21d554844e58bfe`; bytes: 26526.
- [libpng--contrib--gregbook--LICENSE](tools/package/native-licences/ffmpeg-components/libpng--contrib--gregbook--LICENSE); SHA-256: `b6a03c1803eb58ffb1f1278d5c7d4096c4c116e66dce8a7553e8c77d163c3438`; bytes: 2373.
- [rust-lang-rust--LICENSE-MIT](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--LICENSE-MIT); SHA-256: `b71bd43a069ca0641a9ecfe585ca7b3c53b5cc1608f8b68321168698e28b5ea1`; bytes: 1068.
- [glib--LICENSES--MIT.txt](tools/package/native-licences/ffmpeg-components/glib--LICENSES--MIT.txt); SHA-256: `b85dcd3e453d05982552c52b5fc9e0bdd6d23c6f8e844b984a88af32570b0cc0`; bytes: 1078.
- [spirv-cross--LICENSES--CC-BY-4.0.txt](tools/package/native-licences/ffmpeg-components/spirv-cross--LICENSES--CC-BY-4.0.txt); SHA-256: `b89aeb7c2a164a0576786dd2a8b57f2fb628b23981f0a06bd77e2f99a9befa0f`; bytes: 16814.
- [avisynth--avs_core--include--avisynth_c.h](tools/package/native-licences/ffmpeg-components/avisynth--avs_core--include--avisynth_c.h); SHA-256: `b8ae46ec8757ce6c836f4103e03bbcfc3f82d5d32b1971357e6f9545a9b73043`; bytes: 86340.
- [librist--COPYING](tools/package/native-licences/ffmpeg-components/librist--COPYING); SHA-256: `b9841591a3452ee30033d8e3586c7b1244a0b2fc1dc6cb04576957c313cb2792`; bytes: 1319.
- [harfbuzz--COPYING](tools/package/native-licences/ffmpeg-components/harfbuzz--COPYING); SHA-256: `ba8f810f2455c2f08e2d56bb49b72f37fcf68f1f4fade38977cfd7372050ad64`; bytes: 1971.
- [crates--terminal_size-0.4.2--LICENSE-MIT](tools/package/native-licences/ffmpeg-toolchain/crates--terminal_size-0.4.2--LICENSE-MIT); SHA-256: `bc8dcbbd559a61b8a8c0c89d5c3e15d0dc47c6fae94e78ac428d6a7b7da3c4f9`; bytes: 1072.
- [freetype--LICENSE.TXT](tools/package/native-licences/ffmpeg-components/freetype--LICENSE.TXT); SHA-256: `bd36c8b474855fa294c2ec5c184544478ef3720aad37d65a6296a4f264fd2d3b`; bytes: 2149.
- [libpng--LICENSE.md](tools/package/native-licences/ffmpeg-components/libpng--LICENSE.md); SHA-256: `bdb0a645ea18c60507d0368379b1ac5474b92255fcc2d115e07486a7672ba526`; bytes: 5345.
- [ffnvcodec-sdk11.1--include--ffnvcodec--nvEncodeAPI.h](tools/package/native-licences/ffmpeg-components/ffnvcodec-sdk11.1--include--ffnvcodec--nvEncodeAPI.h); SHA-256: `be0c29a41ae3260fd016a9001fd959e747bac93ad21411759736abba4ffdea86`; bytes: 241580.
- [gcc--libstdc++-v3--include--bits--stl_relops.h-L38-47.txt](tools/package/native-licences/ffmpeg-toolchain/gcc--libstdc++-v3--include--bits--stl_relops.h-L38-47.txt); SHA-256: `bf024cb21bafda72ef7ea7370fa298dbff5b03eaba8596e05dcc82a2fee08f6c`; bytes: 528.
- [onevpl--LICENSE](tools/package/native-licences/ffmpeg-components/onevpl--LICENSE); SHA-256: `bf1cfac2e2792b6e1e995ce103d70796aecaf2ec7e4c5fe5474f7acec7b4a677`; bytes: 1074.
- [crates--aligned-vec-0.6.4--LICENSE](tools/package/native-licences/ffmpeg-toolchain/crates--aligned-vec-0.6.4--LICENSE); SHA-256: `bf5a93d1014429b43e01c57d45bea928748fbf37d059306145a1a0a91aec2014`; bytes: 1062.
- [openmpt--include--lhasa--COPYING.md](tools/package/native-licences/ffmpeg-components/openmpt--include--lhasa--COPYING.md); SHA-256: `bf7b055c63205cfc1fea175ea7638f7e7f237bab3eabf2a9fd2bb5c8872edefb`; bytes: 752.
- [lcevcdec--licenses--nlohmann_json--LICENSE.MIT](tools/package/native-licences/ffmpeg-components/lcevcdec--licenses--nlohmann_json--LICENSE.MIT); SHA-256: `c0d068392ea65358b798b8c165103560f06e9e3b38c4ab4e2d8810a7b931af86`; bytes: 1075.
- [svtav1--third_party--safestringlib--LICENSE](tools/package/native-licences/ffmpeg-components/svtav1--third_party--safestringlib--LICENSE); SHA-256: `c0f99a208799ca20c9ccf31a30533d49334eb458dca5a3d14f9afe3e884e5d7d`; bytes: 2247.
- [crates--windows-sys-0.59.0--license-apache-2.0](tools/package/native-licences/ffmpeg-toolchain/crates--windows-sys-0.59.0--license-apache-2.0); SHA-256: `c16f8dcf1a368b83be78d826ea23de4079fe1b4469a0ab9ee20563f37ff3d44b`; bytes: 11351.
- [openmpt--include--mpg123--COPYING](tools/package/native-licences/ffmpeg-components/openmpt--include--mpg123--COPYING); SHA-256: `c22482728a634a8dfdb4ff72a96d4c1ed64cd8f3e79335c401751ac591609366`; bytes: 40718.
- [crates--windows-sys-0.59.0--license-mit](tools/package/native-licences/ffmpeg-toolchain/crates--windows-sys-0.59.0--license-mit); SHA-256: `c2cfccb812fe482101a8f04597dfc5a9991a6b2748266c47ac91b6a5aae15383`; bytes: 1141.
- [crates--utf8_iter-1.0.4--COPYRIGHT](tools/package/native-licences/ffmpeg-toolchain/crates--utf8_iter-1.0.4--COPYRIGHT); SHA-256: `c30152c94a6d75e021adbc52b3a52470366a46edb917e17deae3259251af244c`; bytes: 1742.
- [freetype--docs--GPLv2.TXT](tools/package/native-licences/ffmpeg-components/freetype--docs--GPLv2.TXT); SHA-256: `c4120c6752c910c299e3bd9cb3a46ff262c268303ca2069b61f92f10a5656c18`; bytes: 17994.
- [crates--safe_arch-1.2.0--LICENSE-ZLIB.md](tools/package/native-licences/ffmpeg-toolchain/crates--safe_arch-1.2.0--LICENSE-ZLIB.md); SHA-256: `c43b9a9b1387ed53d2c49263838261129a010e280e3a174a792242c3e2c98db9`; bytes: 851.
- [crates--byte-slice-cast-1.2.3--LICENSE](tools/package/native-licences/ffmpeg-toolchain/crates--byte-slice-cast-1.2.3--LICENSE); SHA-256: `c524732311819f888ce57b1b56148feaa6e9b1705fcb158e7e5d71554ccf39ed`; bytes: 1114.
- [lcms2--plugins--fast_float--COPYING.GPL3](tools/package/native-licences/ffmpeg-components/lcms2--plugins--fast_float--COPYING.GPL3); SHA-256: `c53a65c2fd561c87eaabf1072ef5dcab8653042bc15308465f52413585eb6271`; bytes: 35146.
- [chromaprint--src--3rdparty--kissfft--LICENSES--Unlicense](tools/package/native-licences/ffmpeg-components/chromaprint--src--3rdparty--kissfft--LICENSES--Unlicense); SHA-256: `c543dab3c100d8741a83b02f397746b1e10fc0046f30b942f308191a68e99407`; bytes: 1521.
- [svtav1--LICENSE-BSD2.md](tools/package/native-licences/ffmpeg-components/svtav1--LICENSE-BSD2.md); SHA-256: `c582fcbeb9cf972a60d298bfaf41dc5adff2dd14208946edcb9bb56a281e8438`; bytes: 1316.
- [crates--anstream-0.6.19--LICENSE-APACHE](tools/package/native-licences/ffmpeg-toolchain/crates--anstream-0.6.19--LICENSE-APACHE); SHA-256: `c6596eb7be8581c18be736c846fb9173b69eccf6ef94c5135893ec56bd92ba08`; bytes: 11358.
- [pcre2--cmake--COPYING-CMAKE-SCRIPTS](tools/package/native-licences/ffmpeg-components/pcre2--cmake--COPYING-CMAKE-SCRIPTS); SHA-256: `c666ec2313dba24523ccad88f4c04ea4b24fad6545263a35b1d4ab2b08efe50a`; bytes: 1326.
- [crates--zune-core-0.5.3--LICENSE-APACHE](tools/package/native-licences/ffmpeg-toolchain/crates--zune-core-0.5.3--LICENSE-APACHE); SHA-256: `c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4`; bytes: 11357.
- [openjpeg--thirdparty--liblcms2--COPYING](tools/package/native-licences/ffmpeg-components/openjpeg--thirdparty--liblcms2--COPYING); SHA-256: `c725daac91a9259ce5e195683c0eeb797d345035c36ac5ba114c9fa80e11639a`; bytes: 1078.
- [crates--fdeflate-0.3.7--LICENSE-MIT](tools/package/native-licences/ffmpeg-toolchain/crates--fdeflate-0.3.7--LICENSE-MIT); SHA-256: `c77a4cf9da729987d0fe7ccd811e3bd27393914ddf3d23467c18cc22954513b3`; bytes: 1036.
- [libva--COPYING](tools/package/native-licences/ffmpeg-components/libva--COPYING); SHA-256: `c86a782ee845b52472dae9b9d79fb915d333628ac0efe49cdce63644814931de`; bytes: 1130.
- [crates--siphasher-1.0.4--COPYING](tools/package/native-licences/ffmpeg-toolchain/crates--siphasher-1.0.4--COPYING); SHA-256: `c962ee4d1d05ddc138b202b2540219ebc57893fcf97b364852094a9a94ce1365`; bytes: 281.
- [crates--as-slice-0.2.1--LICENSE-MIT](tools/package/native-licences/ffmpeg-toolchain/crates--as-slice-0.2.1--LICENSE-MIT); SHA-256: `c986bcdb83103d4ddf58aeb7b5302359782e54dc4eea14a0cc27c62dcbd50729`; bytes: 1058.
- [crates--lock_api-0.4.14--LICENSE-MIT](tools/package/native-licences/ffmpeg-toolchain/crates--lock_api-0.4.14--LICENSE-MIT); SHA-256: `c9a75f18b9ab2927829a208fc6aa2cf4e63b8420887ba29cdb265d6619ae82d5`; bytes: 1071.
- [openmpt--src--mpt--LICENSE.BSL-1.0.txt](tools/package/native-licences/ffmpeg-components/openmpt--src--mpt--LICENSE.BSL-1.0.txt); SHA-256: `c9bff75738922193e67fa726fa225535870d2aa1059f91452c411736284ad566`; bytes: 1338.
- [libzmq--external--sha1--license.txt](tools/package/native-licences/ffmpeg-components/libzmq--external--sha1--license.txt); SHA-256: `cb1a4e594fc67ecde3e6d704b94d6ac4385a6027d0605702c675d182f186eeb6`; bytes: 1516.
- [lcevcdec--licenses--FFmpeg--LICENSE.md](tools/package/native-licences/ffmpeg-components/lcevcdec--licenses--FFmpeg--LICENSE.md); SHA-256: `cb48bf09a11f5fb576cddb0431c8f5ed0a60157a9ec942adffc13907cbe083f2`; bytes: 4376.
- [libvpx--PATENTS](tools/package/native-licences/ffmpeg-components/libvpx--PATENTS); SHA-256: `cc3273e0694ea5896145e0677699b53471b03ea43021ddc50e7923fbb9f5023c`; bytes: 1436.
- [glslang--LICENSES--AML-glslang.txt](tools/package/native-licences/ffmpeg-components/glslang--LICENSES--AML-glslang.txt); SHA-256: `cc8ea571129dbee2997e52a54d1f715f8b0159a22f28f985a9b2b31708a48620`; bytes: 2373.
- [crates--winapi-0.3.9--LICENSE-MIT](tools/package/native-licences/ffmpeg-toolchain/crates--winapi-0.3.9--LICENSE-MIT); SHA-256: `ce7bc3499fee93d5022ef430d5e4201e79a6d9154f3974e42f41349f0569e09b`; bytes: 1073.
- [openmpt--src--mpt--LICENSE.BSD-3-Clause.txt](tools/package/native-licences/ffmpeg-components/openmpt--src--mpt--LICENSE.BSD-3-Clause.txt); SHA-256: `ceabc562c8cfb3af0d51e94182947c23bde6c18274e2b21585bdde22d2031e9d`; bytes: 1596.
- [crates--nalgebra-0.35.0--LICENSE](tools/package/native-licences/ffmpeg-toolchain/crates--nalgebra-0.35.0--LICENSE); SHA-256: `ceacfa4d7fa67df64ab09a56fe248c50a3bfc9bc00374d69bd74ad763b14b89c`; bytes: 11347.
- [rubberband--COPYING](tools/package/native-licences/ffmpeg-components/rubberband--COPYING); SHA-256: `cedd4c1885d75991bf1077cc6e33359103cf04fbc996f20d30ab043d5fc5fcc5`; bytes: 30260.
- [lcevcdec--licenses--gradle--LICENSE](tools/package/native-licences/ffmpeg-components/lcevcdec--licenses--gradle--LICENSE); SHA-256: `cf234c4188d773406f640bf89be680d9288f40ff96901c70d643fcea96ad46df`; bytes: 23645.
- [harfbuzz--perf--texts--COPYING](tools/package/native-licences/ffmpeg-components/harfbuzz--perf--texts--COPYING); SHA-256: `cf977e70247d5fa9d44955e4d8ed23b503c31f78570f62136756278c2cfcb3c3`; bytes: 1289.
- [rust-lang-rust--library--portable-simd--LICENSE-APACHE](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--portable-simd--LICENSE-APACHE); SHA-256: `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`; bytes: 11358.
- [opencore-amr--opencore--NOTICE](tools/package/native-licences/ffmpeg-components/opencore-amr--opencore--NOTICE); SHA-256: `d106802b5e406073c1d10fbe9f638234c6973ebce37df71773179642085eb489`; bytes: 12498.
- [crates--zune-core-0.5.3--LICENSE-ZLIB](tools/package/native-licences/ffmpeg-toolchain/crates--zune-core-0.5.3--LICENSE-ZLIB); SHA-256: `d201d14804d3bcd3b944147173175e4abfbd838b7c8069b6bd3452496bf13e6c`; bytes: 859.
- [pango--COPYING](tools/package/native-licences/ffmpeg-components/pango--COPYING); SHA-256: `d245807f90032872d1438d741ed21e2490e1175dc8aa3afa5ddb6c8e529b58e5`; bytes: 25292.
- [aom--third_party--highway--LICENSE-BSD3](tools/package/native-licences/ffmpeg-components/aom--third_party--highway--LICENSE-BSD3); SHA-256: `d25e82e26acd42ca3ccc9993622631163425b869b9e16284226d534cff6470f2`; bytes: 1515.
- [libogg--COPYING](tools/package/native-licences/ffmpeg-components/libogg--COPYING); SHA-256: `d2ab5758336489da61c12cc5bb757da5339c4ae9001f9bb0562b4370249af814`; bytes: 1466.
- [gme--license.txt](tools/package/native-licences/ffmpeg-components/gme--license.txt); SHA-256: `d2efc89fbb7533572a472d34e07964951810a3a4f8d3159ecc2dcaa1452c5c26`; bytes: 26938.
- [crates--zune-core-0.5.3--LICENSE-MIT](tools/package/native-licences/ffmpeg-toolchain/crates--zune-core-0.5.3--LICENSE-MIT); SHA-256: `d30047bca3b516639339a3c279bb84c3483124fb5a9dafe3c75056a85090e745`; bytes: 1073.
- [ffnvcodec-sdk11.1--include--ffnvcodec--nvEncodeAPI.h-L1-26.txt](tools/package/native-licences/ffmpeg-components/ffnvcodec-sdk11.1--include--ffnvcodec--nvEncodeAPI.h-L1-26.txt); SHA-256: `d513d306639f4511a54494dbed295f7a1234d4ad55ca48ac9662f4ad543d6fc3`; bytes: 1199.
- [crates--wide-1.7.1--LICENSE-APACHE.txt](tools/package/native-licences/ffmpeg-toolchain/crates--wide-1.7.1--LICENSE-APACHE.txt); SHA-256: `d64ac6ba60c7352115244dcfcb46c24f934603dd92e64835beafe7631c485abc`; bytes: 11352.
- [libxml2--result--html-tokenizer--NOTICE](tools/package/native-licences/ffmpeg-components/libxml2--result--html-tokenizer--NOTICE); SHA-256: `d6a2cb265a0a249a234b89eeffa7f316ebe5bff546672a0a2b1a861dd2238460`; bytes: 1270.
- [libdvdread--COPYING](tools/package/native-licences/ffmpeg-components/libdvdread--COPYING); SHA-256: `d6cb0e9e560f51085556949a84af12b79a00f10ab8b66c752537faf7cd665572`; bytes: 18097.
- [libvpx--third_party--nalloc--LICENSE](tools/package/native-licences/ffmpeg-components/libvpx--third_party--nalloc--LICENSE); SHA-256: `d7dd0396ec46975e1bf9093680068ef301bc0ed204603e623a6f7073ab922ab1`; bytes: 1069.
- [openal--COPYING](tools/package/native-licences/ffmpeg-components/openal--COPYING); SHA-256: `d808ce217e5b611854da622b57ec29fe545584c48bc5352fae72a4b6e5074a15`; bytes: 23330.
- [x265--COPYING](tools/package/native-licences/ffmpeg-components/x265--COPYING); SHA-256: `d8afb1bcc7a2cfc603683b168d6987ef0a48e59e0da3693bf55c5d33b67e2b49`; bytes: 18120.
- [amf--Thirdparty--amd--AmdDxExt--LICENSE.txt](tools/package/native-licences/ffmpeg-components/amf--Thirdparty--amd--AmdDxExt--LICENSE.txt); SHA-256: `d8b1b7b1757e8b44ac9cd55cc41736523dd355523900af5f7c0187b485ac62c7`; bytes: 1096.
- [crates--encode_unicode-1.0.0--LICENSE-MIT](tools/package/native-licences/ffmpeg-toolchain/crates--encode_unicode-1.0.0--LICENSE-MIT); SHA-256: `da23be69ad3ccf7a5823d62152efcd2b15de9482a5014fcb1b02844662d86abd`; bytes: 1022.
- [libaribb24--COPYING](tools/package/native-licences/ffmpeg-components/libaribb24--COPYING); SHA-256: `da7eabb7bafdf7d3ae5e9f223aa5bdc1eece45ac569dc21b3b037520b4464768`; bytes: 7651.
- [crates--cairo-rs-0.22.9--COPYRIGHT](tools/package/native-licences/ffmpeg-toolchain/crates--cairo-rs-0.22.9--COPYRIGHT); SHA-256: `dae402989de65164815b7e2b6bc2b9576285434c3785934c8b6ece0fa055960d`; bytes: 651.
- [sdl--visualtest--COPYING.txt](tools/package/native-licences/ffmpeg-components/sdl--visualtest--COPYING.txt); SHA-256: `dae65ccf728227eff8e10194437078a5628047b9f55d796039688e7ca8e3aa4e`; bytes: 947.
- [crates--typenum-1.20.1--LICENSE](tools/package/native-licences/ffmpeg-toolchain/crates--typenum-1.20.1--LICENSE); SHA-256: `db11fec9946737df39ca3898d9cd8c10ec6f6c3a884a6802b0ad0b81b4e8f23a`; bytes: 17.
- [crates--minimal-lexical-0.2.1--LICENSE.md](tools/package/native-licences/ffmpeg-toolchain/crates--minimal-lexical-0.2.1--LICENSE.md); SHA-256: `dbe1fff0fb1314b6af94f161511406275cf01c5a32441fbf24528a57a051d599`; bytes: 2003.
- [libudfread--COPYING](tools/package/native-licences/ffmpeg-components/libudfread--COPYING); SHA-256: `dc626520dcd53a22f727af3ee42c770e56c97a64fe3adb063799d8ab032fe551`; bytes: 26530.
- [soxr--LICENCE](tools/package/native-licences/ffmpeg-components/soxr--LICENCE); SHA-256: `dc98676341fdcd29d9f279c9679d6a75288785b174ded8d1b2e316c366166135`; bytes: 1024.
- [mingw--mingw-w64-crt--profile--COPYING](tools/package/native-licences/ffmpeg-components/mingw--mingw-w64-crt--profile--COPYING); SHA-256: `dcc100d4161cc0b7177545ab6e47216f84857cda3843847c792a25289852dcaa`; bytes: 18007.
- [openh264--LICENSE](tools/package/native-licences/ffmpeg-components/openh264--LICENSE); SHA-256: `dd5c1c9668512530fa5a96e4c29ac4033d70a7eeb0eed7a42fddb6dd794ebdbb`; bytes: 1295.
- [dav1d--COPYING](tools/package/native-licences/ffmpeg-components/dav1d--COPYING); SHA-256: `dd92c3c2247c5651606fc23a5e2d6a1ebc5ace9a3e49cbde0e12f05ad1cb1ee5`; bytes: 1317.
- [serd--LICENSES--BSD-3-Clause.txt](tools/package/native-licences/ffmpeg-components/serd--LICENSES--BSD-3-Clause.txt); SHA-256: `de3b5841bb0f65f13d96328006e025f63f117c564b268886b43602d05ce763aa`; bytes: 1425.
- [ffnvcodec-sdk13.0--include--ffnvcodec--dynlink_loader.h](tools/package/native-licences/ffmpeg-components/ffnvcodec-sdk13.0--include--ffnvcodec--dynlink_loader.h); SHA-256: `dfbee3396c3fa92bff8a47ca600a698dea9f7bbad84a77343762fea362c35dd0`; bytes: 24460.
- [crates--language-tags-0.3.2--LICENSE](tools/package/native-licences/ffmpeg-toolchain/crates--language-tags-0.3.2--LICENSE); SHA-256: `e03e58ea9205f51989b7a50f450051b24e6516cc1f0b920222dcda992072be99`; bytes: 1051.
- [gnulib--doc--licenses-texi.texi](tools/package/native-licences/ffmpeg-components/gnulib--doc--licenses-texi.texi); SHA-256: `e2978abebf7cbcae3ee0c8794e660dd7b8a1508b1b347357fd235e5c83347436`; bytes: 2953.
- [zlib--LICENSE](tools/package/native-licences/ffmpeg-components/zlib--LICENSE); SHA-256: `e32ff4e00d9d94930537635291da39e7e612703334bf6fde8c7f1686fe8a45a2`; bytes: 1002.
- [glib--LICENSES--LLVM-exception.txt](tools/package/native-licences/ffmpeg-components/glib--LICENSES--LLVM-exception.txt); SHA-256: `e34c58338bd89d43e709e226610d8f32b3e3c47f4ad9a99a8dc1d4ac7842488e`; bytes: 919.
- [gnulib--doc--COPYING.LESSERv3](tools/package/native-licences/ffmpeg-components/gnulib--doc--COPYING.LESSERv3); SHA-256: `e3a994d82e644b03a792a930f574002658412f62407f5fee083f2555c5f23118`; bytes: 7652.
- [crates--bytemuck-1.25.2--LICENSE-APACHE](tools/package/native-licences/ffmpeg-toolchain/crates--bytemuck-1.25.2--LICENSE-APACHE); SHA-256: `e3ba223bb1423f0aad8c3dfce0fe3148db48926d41e6fbc3afbbf5ff9e1c89cb`; bytes: 10398.
- [crates--utf8parse-0.2.2--LICENSE-MIT](tools/package/native-licences/ffmpeg-toolchain/crates--utf8parse-0.2.2--LICENSE-MIT); SHA-256: `e4c9b06fa850cb9b540a5e400e9f6394cf15efcf4098144de477d1d3dae10150`; bytes: 1052.
- [kvazaar--src--threadwrapper--LICENSE](tools/package/native-licences/ffmpeg-components/kvazaar--src--threadwrapper--LICENSE); SHA-256: `e4c9f82e9970cded92135cdc88f8a2f8e35b6d2fdb5fd879ea713cadfd6fbac3`; bytes: 731.
- [crates--safe_arch-1.2.0--LICENSE-MIT.md](tools/package/native-licences/ffmpeg-toolchain/crates--safe_arch-1.2.0--LICENSE-MIT.md); SHA-256: `e57011537d230b14e790f6666dc00816f7b371ebbd7da8a12491e51086fec278`; bytes: 1110.
- [gmp--COPYINGv3](tools/package/native-licences/ffmpeg-components/gmp--COPYINGv3); SHA-256: `e6037104443f9a7829b2aa7c5370d0789a7bda3ca65a0b904cdc0c2e285d9195`; bytes: 35150.
- [libmp3lame--COPYING](tools/package/native-licences/ffmpeg-components/libmp3lame--COPYING); SHA-256: `e64f9c5a18f56828c10a575df13ade641aa3af4512a7afe6c411256943b57aaf`; bytes: 25281.
- [libffi--LICENSE-BUILDTOOLS](tools/package/native-licences/ffmpeg-components/libffi--LICENSE-BUILDTOOLS); SHA-256: `e67978cd18816c0cb7d29aaaacde7b7447402c2fb321a051698890a8eaedda94`; bytes: 18698.
- [openmpt--include--premake--LICENSE.txt](tools/package/native-licences/ffmpeg-components/openmpt--include--premake--LICENSE.txt); SHA-256: `e95a86849e468c3db4611acee90c788c6d5a5b4ba8cf50c27024dd880e17c66d`; bytes: 1534.
- [crates--addr2line-0.27.1--LICENSE-MIT](tools/package/native-licences/ffmpeg-toolchain/crates--addr2line-0.27.1--LICENSE-MIT); SHA-256: `e99d88d232bf57d70f0fb87f6b496d44b6653f99f8a63d250a54c61ea4bcde40`; bytes: 1069.
- [crates--static_assertions-1.1.0--LICENSE-MIT](tools/package/native-licences/ffmpeg-toolchain/crates--static_assertions-1.1.0--LICENSE-MIT); SHA-256: `ea084a2373ebc1f0902c09266e7bf25a05ab3814c1805bb017ffa7308f90c061`; bytes: 1072.
- [spirv-headers--LICENSE](tools/package/native-licences/ffmpeg-components/spirv-headers--LICENSE); SHA-256: `ea43b1de38a6f90c488800d66dec1ed671e68cda530266bc96951fb5b6307613`; bytes: 23503.
- [libxml2--dict.c-L1-17.txt](tools/package/native-licences/ffmpeg-components/libxml2--dict.c-L1-17.txt); SHA-256: `ea9e97f88bf4ef8ad1142e12d0e6da003968420aa38094f74b9b51206675438a`; bytes: 701.
- [crates--png-0.18.1--LICENSE-MIT](tools/package/native-licences/ffmpeg-toolchain/crates--png-0.18.1--LICENSE-MIT); SHA-256: `eaf40297c75da471f7cda1f3458e8d91b4b2ec866e609527a13acfa93b638652`; bytes: 1048.
- [rust-lang-rust--library--portable-simd--LICENSE-MIT](tools/package/native-licences/ffmpeg-toolchain/rust-lang-rust--library--portable-simd--LICENSE-MIT); SHA-256: `eb07d497d26e6d68fbc76e793f5e5c9cfa197df2a580e47383569c287a55edf9`; bytes: 1071.
- [amf--LICENSE.txt](tools/package/native-licences/ffmpeg-components/amf--LICENSE.txt); SHA-256: `eb297397aaa455b5668ab67d216b83828466152dab123fa92384c6ec16b74170`; bytes: 1747.
- [libvorbis--COPYING](tools/package/native-licences/ffmpeg-components/libvorbis--COPYING); SHA-256: `ec1815db59fcd302846df949d7424876cb2e2dc5ed1606c5fb0b36787b1cf43a`; bytes: 1470.
- [openmpt--include--portaudio--LICENSE.txt](tools/package/native-licences/ffmpeg-components/openmpt--include--portaudio--LICENSE.txt); SHA-256: `ec52a1952d701f94e5135719a47376da4ee0b4a0201f1cafb49f61db6480ac3d`; bytes: 3524.
- [libjxl--debian--copyright](tools/package/native-licences/ffmpeg-components/libjxl--debian--copyright); SHA-256: `ec6f5bc1043fba8ffa648157b5beee8915865a54f25c5f3201b0e910cd09ebde`; bytes: 10405.
- [zix--LICENSES--0BSD.txt](tools/package/native-licences/ffmpeg-components/zix--LICENSES--0BSD.txt); SHA-256: `ed2b2a2319139765407c37b7a1a082e88f9b3667392b29f59b1e6c2f4c497087`; bytes: 661.
- [gnulib--doc--COPYINGv2](tools/package/native-licences/ffmpeg-components/gnulib--doc--COPYINGv2); SHA-256: `edaef632cbb643e4e7a221717a6c441a4c1a7c918e6e4d56debc3d8739b233f6`; bytes: 17984.
- [openmpt--include--SignalsmithStretch--SignalsmithStretch--LICENSE.txt](tools/package/native-licences/ffmpeg-components/openmpt--include--SignalsmithStretch--SignalsmithStretch--LICENSE.txt); SHA-256: `ee2ef82481ffb445ecdd4b3a4c1f82c0cddb2da8fe39d8e8dc384fffb3e7f06f`; bytes: 1093.
- [openmpt--include--ancient--LICENSE.bzip2](tools/package/native-licences/ffmpeg-components/openmpt--include--ancient--LICENSE.bzip2); SHA-256: `eeaa743b773d4fd56f5955fbf7da0ee2fb2082cd4efa7e9d4af95204907a23a4`; bytes: 1945.
- [sord--LICENSES--ISC.txt](tools/package/native-licences/ffmpeg-components/sord--LICENSES--ISC.txt); SHA-256: `f04f124b8814edb03cd64fa82d38cc1c1aa32195fabd33c196b02968e466ba32`; bytes: 751.
- [crates--core2-0.4.0--LICENSE-MIT](tools/package/native-licences/ffmpeg-toolchain/crates--core2-0.4.0--LICENSE-MIT); SHA-256: `f21c3bfdc47749b5912eb55f0661b2b8fd9696b3e09e7d97a1fc78fb52c3eb1b`; bytes: 1085.
- [soxr--COPYING.LGPL](tools/package/native-licences/ffmpeg-components/soxr--COPYING.LGPL); SHA-256: `f2f118b9029ec1871b953639ecc46651b2fc7b62e295e6cf3ef2ac4c9a058b33`; bytes: 26432.
- [crates--icu_collections-2.4.0--LICENSE](tools/package/native-licences/ffmpeg-toolchain/crates--icu_collections-2.4.0--LICENSE); SHA-256: `f367c1b8e1aa262435251e442901da4607b4650e0e63a026f5044473ecfb90f2`; bytes: 2195.
- [mingw--COPYING.MinGW-w64--COPYING.MinGW-w64.txt](tools/package/native-licences/ffmpeg-components/mingw--COPYING.MinGW-w64--COPYING.MinGW-w64.txt); SHA-256: `f38e6194bd3bfa1b654f118e5acefe0aead437bbe669eee43957ccc65a7127f1`; bytes: 5905.
- [gcc--libstdc++-v3--include--bits--stl_algo.h-L27-36.txt](tools/package/native-licences/ffmpeg-toolchain/gcc--libstdc++-v3--include--bits--stl_algo.h-L27-36.txt); SHA-256: `f4d6042457d55120a13de7adf78d1becc0790ce198b5abcba917b4e52806953e`; bytes: 537.
- [gnulib--modules--COPYING](tools/package/native-licences/ffmpeg-components/gnulib--modules--COPYING); SHA-256: `f530fec34a348cd8ad9cab66d0672f40406b07c3a4b995a2a5f31c483a9221d7`; bytes: 420.
- [lv2--LICENSES--CC-BY-4.0.txt](tools/package/native-licences/ffmpeg-components/lv2--LICENSES--CC-BY-4.0.txt); SHA-256: `f5b745ef98087f531e719ee8ca6a96809444573ecc7173c6fa68eaad39b3cc3f`; bytes: 18658.
- [avisynth--avs_core--include--avisynth_c.h-L1-35.txt](tools/package/native-licences/ffmpeg-components/avisynth--avs_core--include--avisynth_c.h-L1-35.txt); SHA-256: `f606ca417e07423b05eeed755db9caa41b1877e07d368f84a4f34d43a06a1ae9`; bytes: 1823.
- [lv2--LICENSES--CC-BY-1.0.txt](tools/package/native-licences/ffmpeg-components/lv2--LICENSES--CC-BY-1.0.txt); SHA-256: `f6f4064295ea3adf266856073eeec20da5a15e8d0c7912947e0d73993ef620a3`; bytes: 11875.
- [crates--new_debug_unreachable-1.0.6--LICENSE-MIT](tools/package/native-licences/ffmpeg-toolchain/crates--new_debug_unreachable-1.0.6--LICENSE-MIT); SHA-256: `f7715d38a3fa1b4ac97c5729740752505a39cb92ee83ab5b102aeb5eaa7cdea4`; bytes: 1057.
- [sdl--src--video--yuv2rgb--LICENSE](tools/package/native-licences/ffmpeg-components/sdl--src--video--yuv2rgb--LICENSE); SHA-256: `f7d74004cc75778cae46c5f0139f244d67c07ef64cf51937e8272352197dcb18`; bytes: 1480.
- [libass--COPYING](tools/package/native-licences/ffmpeg-components/libass--COPYING); SHA-256: `f7e30699d02798351e7f839e3d3bfeb29ce65e44efa7735c225464c4fd7dfe9c`; bytes: 755.
- [lv2--LICENSES--W3C-19980720.txt](tools/package/native-licences/ffmpeg-components/lv2--LICENSES--W3C-19980720.txt); SHA-256: `f864e27c1dd0529e0ec865df09a5908df15a9371c1bd12b12563aec5c5e848aa`; bytes: 2532.
- [crates--siphasher-1.0.4--LICENSE-MIT](tools/package/native-licences/ffmpeg-toolchain/crates--siphasher-1.0.4--LICENSE-MIT); SHA-256: `f9c4c77baa3828004ee54b8a4f2db2e88ed44a6237a493965bf551fac0fcb62d`; bytes: 1023.
- [glib--LICENSES--LGPL-2.1-only.txt](tools/package/native-licences/ffmpeg-components/glib--LICENSES--LGPL-2.1-only.txt); SHA-256: `fa6f36630bb1e0c571d34b2bbdf188d08495c9dbf58f28cac112f303fc1f58fb`; bytes: 25967.
- [mingw--mingw-w64-libraries--winstorecompat--COPYING](tools/package/native-licences/ffmpeg-components/mingw--mingw-w64-libraries--winstorecompat--COPYING); SHA-256: `fa7368d1f93d890c173177475d8ec7aff265a7d08f1f364d66f74d138978ce36`; bytes: 1099.
- [crates--cssparser-0.37.0--LICENSE](tools/package/native-licences/ffmpeg-toolchain/crates--cssparser-0.37.0--LICENSE); SHA-256: `fab3dd6bdab226f1c08630b1dd917e11fcb4ec5e1e020e2c16f83a0a13863e85`; bytes: 16726.
- [pixman--COPYING](tools/package/native-licences/ffmpeg-components/pixman--COPYING); SHA-256: `fac9270f0987b96ff4533fca3548c633e02083cbba4a0172a3b149b2e4019793`; bytes: 2087.
- [glib--LICENSES--LicenseRef-old-glib-tests.txt](tools/package/native-licences/ffmpeg-components/glib--LICENSES--LicenseRef-old-glib-tests.txt); SHA-256: `fb261b2d5dbe76c4850f90da763210bc385e52428df6bbfd7b06295ac8a32914`; bytes: 841.
- [sdl--src--hidapi--LICENSE-orig.txt](tools/package/native-licences/ffmpeg-components/sdl--src--hidapi--LICENSE-orig.txt); SHA-256: `fb5436aa63d1b71a8dfbf74ecaf1a5b4e1ec4df7f80074d11fec99284f69ca5f`; bytes: 264.
- [crates--scopeguard-1.2.0--LICENSE-MIT](tools/package/native-licences/ffmpeg-toolchain/crates--scopeguard-1.2.0--LICENSE-MIT); SHA-256: `fb77f0a9c53e473abe5103c8632ef9f0f2874d4fb3f17cb2d8c661aab9cee9d7`; bytes: 1097.
- [spirv-cross--LICENSES--LicenseRef-KhronosFreeUse.txt](tools/package/native-licences/ffmpeg-components/spirv-cross--LICENSES--LicenseRef-KhronosFreeUse.txt); SHA-256: `fbeaca472f4f70e276dd1106ca5097435967a22ad6c1d8200aef7ad9f70aaf3f`; bytes: 1305.
- [zlib--contrib--minizip--LICENSE.Info-Zip](tools/package/native-licences/ffmpeg-components/zlib--contrib--minizip--LICENSE.Info-Zip); SHA-256: `fc686023047ce5ce3a18a9b8a777156f0e475929d3de06bac279f3c025d2b2ca`; bytes: 3509.
- [crates--tinyvec-1.13.3--LICENSE-MIT.md](tools/package/native-licences/ffmpeg-toolchain/crates--tinyvec-1.13.3--LICENSE-MIT.md); SHA-256: `fd80a26fbb3f644af1fa994134446702932968519797227e07a1368dea80f0bc`; bytes: 1023.
- [crates--hashbrown-0.17.1--LICENSE-MIT](tools/package/native-licences/ffmpeg-toolchain/crates--hashbrown-0.17.1--LICENSE-MIT); SHA-256: `ff8f68cb076caf8cefe7a6430d4ac086ce6af2ca8ce2c4e5a2004d4552ef52a2`; bytes: 1060.
