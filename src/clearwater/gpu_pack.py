"""The GPU pack loader: CuPy and the CUDA wheels from a per-user folder (WP6.1, AD-33).

A packaged (frozen) Clearwater never bundles CuPy or the NVIDIA wheels (the owner's D-C
amendment; spec N14). They may instead be installed, once, into a per-user folder, the *GPU
pack*::

    <pack root>/<stamp>/manifest.json
    <pack root>/<stamp>/site-packages/      cupy/, cupyx/, cuda/, nvidia/, *.dist-info/

:func:`pack_root` names the root for this platform. The stamp (:data:`STAMP`, for example
``14.2.0-cu12``) is the locked ``cupy-cuda12x`` version plus the CUDA major version.

At start-up, before anything imports ``cupy``, :func:`activate` checks the pack's manifest
against the lock (:data:`LOCKED_DISTRIBUTIONS`) and, when it passes, puts its
``site-packages`` at the front of ``sys.path``. On Windows it also adds each
``site-packages/nvidia/*/bin`` folder to the DLL search path (``os.add_dll_directory``), because
CuPy's library finder does not search ``sys.path`` for the CUDA DLLs, and it puts the
``site-packages`` folder first in ``site.PREFIXES`` (:func:`add_site_prefix`), because
``cuda.pathfinder`` looks for the CUDA headers through ``site.getsitepackages()`` (F-F; on a
future Linux leg the spelling would be ``lib/python3.12/site-packages`` under the prefix, not
handled here). It logs one line:
``gpu pack <stamp>: loaded``, ``absent`` or ``rejected: <reason>``. An absent or rejected
pack changes nothing: the backend probe then reports the CPU path exactly as 1.0.0 does.

The loader only acts in a frozen build (``sys.frozen``); a source install takes CuPy from its
own environment (the ``gpu`` extra). It never writes, creates or deletes anything: the pack
folder is read-only to it. It imports only the standard library, so it can run first.

The check guards against a partial, corrupt, wrong-version or wrong-platform install, not
against a local attacker who can already write the user's own folder. At every start-up it
runs the CHEAP check (:func:`check_pack`, CHARC's ruling at Reviewer A r2): the manifest
matches the lock; each distribution's ``RECORD`` file has the manifest's sha256; each
distribution's ``WHEEL`` tags fit the running platform; every file a ``RECORD`` lists exists
with the size that ``RECORD`` gives; and ``site-packages`` holds no top-level entry that no
``RECORD`` owns (so nothing unlisted, a ``.pth`` file or a second ``numpy`` say, can shadow
the bundle). It hashes no file but the ``RECORD`` files. Hashing every file is the
installer's job, once, at install time (:func:`pack_problems` with ``full=True``, which the
build script's ``--verify`` runs on a pack filled by hand); the full check also walks every
file under ``site-packages`` and fails on any that no ``RECORD`` row names, ``__pycache__``
included (CHARC's Q2 ruling; the start-up check stays top-level).
"""

from __future__ import annotations

import base64
import csv
import hashlib
import io
import json
import logging
import os
import re
import stat
import sys
import sysconfig
import warnings
from collections.abc import Generator, Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Literal

_LOG = logging.getLogger(__name__)

Outcome = Literal["loaded", "absent", "rejected"]
"""What the loader found: a valid pack, no pack, or a pack that failed a check."""

MANIFEST_NAME = "manifest.json"
"""The manifest's file name inside ``<pack root>/<stamp>/``."""

SITE_PACKAGES_NAME = "site-packages"
"""The folder inside ``<pack root>/<stamp>/`` that goes on ``sys.path``."""

MANIFEST_FORMAT = 1
"""The manifest format this loader reads."""

PACK_FOLDER_NAME = "gpu-pack"
"""The pack root's last folder name, inside the application's data folder."""

WINDOWS_APP_FOLDER = "Clearwater"
"""The application's folder name under ``%LOCALAPPDATA%`` (as ``config.paths`` names it)."""

POSIX_APP_FOLDER = "clearwater"
"""The application's folder name under ``$XDG_DATA_HOME`` (as ``config.paths`` names it)."""

CUPY_DISTRIBUTION = "cupy-cuda12x"
"""The CuPy distribution whose locked version (and CUDA major) names the stamp."""


@dataclass(frozen=True)
class LockedDistribution:
    """One distribution of the pack, at its ``uv.lock`` version, with the lock's wheels.

    Attributes:
        name: The distribution name as the lock spells it (``nvidia-cublas-cu12``).
        version: The locked version.
        wheels: Locked (file name, sha256 hex, URL, size in bytes) rows.
    """

    name: str
    version: str
    wheels: tuple[tuple[str, str, str, int], ...]

    @property
    def dist_info_name(self) -> str:
        """The installed metadata folder: ``<escaped name>-<version>.dist-info``."""
        return f"{re.sub(r'[-_.]+', '_', self.name)}-{self.version}.dist-info"


LOCKED_DISTRIBUTIONS: tuple[LockedDistribution, ...] = (
    LockedDistribution(
        "cupy-cuda12x",
        "14.2.0",
        (
            (
                "cupy_cuda12x-14.2.0-cp312-cp312-manylinux2014_aarch64.whl",
                "b74340aa7271f0f081f77e2e5107bac75af19b86df29213db7ada90e14428efe",
                "https://files.pythonhosted.org/packages/d3/8c/5fe3f6719c2d4560c79c62ef6d9b7d6c34d145879ddc0c1a41f8153ad0a6/cupy_cuda12x-14.2.0-cp312-cp312-manylinux2014_aarch64.whl",
                147490427,
            ),
            (
                "cupy_cuda12x-14.2.0-cp312-cp312-manylinux2014_x86_64.whl",
                "f82141761f2c81905d49387464ae29438887956d99063381c93a1d5d1b7d32e8",
                "https://files.pythonhosted.org/packages/7c/5b/65124de2dbaf2e85109f611a41947e39acd6dd938751c04b4c4d7bf6fc82/cupy_cuda12x-14.2.0-cp312-cp312-manylinux2014_x86_64.whl",
                136111459,
            ),
            (
                "cupy_cuda12x-14.2.0-cp312-cp312-win_amd64.whl",
                "c9571d3b5f2e65758137e210f7fb3c3b34767f0af6b6ca04035a244b6141ee12",
                "https://files.pythonhosted.org/packages/e9/18/ddea819204701024bef7fa748730702245d803847c841b737723b94fd091/cupy_cuda12x-14.2.0-cp312-cp312-win_amd64.whl",
                98780018,
            ),
        ),
    ),
    LockedDistribution(
        "cuda-pathfinder",
        "1.8.3",
        (
            (
                "cuda_pathfinder-1.8.3-py3-none-any.whl",
                "e29e59829c297a7a5233bd9cc71094fc5bddbd076951482670178f9eade39b1f",
                "https://files.pythonhosted.org/packages/b9/fb/f8e1890428f9f590b4beebd63b068aac1ce32a3331510c847b9f9a78f261/cuda_pathfinder-1.8.3-py3-none-any.whl",
                62561,
            ),
        ),
    ),
    LockedDistribution(
        "cuda-toolkit",
        "12.9.2.0",
        (
            (
                "cuda_toolkit-12.9.2.0-py2.py3-none-any.whl",
                "b54b8f2fd4200090b44843d48fc5411198e8b3e47a3db56e2518ab588c0ef1e0",
                "https://files.pythonhosted.org/packages/51/7e/f61db087382a2114a93abc0b38f7872f86f2c7c36839da7f9403c9044b47/cuda_toolkit-12.9.2.0-py2.py3-none-any.whl",
                2431,
            ),
        ),
    ),
    LockedDistribution(
        "nvidia-cublas-cu12",
        "12.9.2.10",
        (
            (
                "nvidia_cublas_cu12-12.9.2.10-py3-none-manylinux_2_27_aarch64.whl",
                "5572131a59c3eebeeb1c4c8144f772d49372c20124916e072a0e3fc30df421d5",
                "https://files.pythonhosted.org/packages/f7/a2/c96163a0fff1839c0c9548bbdeae7b853b867009e33b9b9264adc238b1cf/nvidia_cublas_cu12-12.9.2.10-py3-none-manylinux_2_27_aarch64.whl",
                575012079,
            ),
            (
                "nvidia_cublas_cu12-12.9.2.10-py3-none-manylinux_2_27_x86_64.whl",
                "e4f53a8ca8c5d6e8c492d0d0a3d565ecb59a751b19cfdaa4f6da0ab2104c1702",
                "https://files.pythonhosted.org/packages/cb/c0/0a517bfe63ccd3b92eb254d264e28fca3c7cab75d07daea315250fb1bf73/nvidia_cublas_cu12-12.9.2.10-py3-none-manylinux_2_27_x86_64.whl",
                581240110,
            ),
            (
                "nvidia_cublas_cu12-12.9.2.10-py3-none-win_amd64.whl",
                "623f43027d40d44ceadf0043f002bd25cf353e8f13ce90b9a87057019f560661",
                "https://files.pythonhosted.org/packages/20/e2/fc9a0e985249d873150276d5afb02e39a66817fedbf1a385724393e505ed/nvidia_cublas_cu12-12.9.2.10-py3-none-win_amd64.whl",
                553162896,
            ),
        ),
    ),
    LockedDistribution(
        "nvidia-cuda-nvrtc-cu12",
        "12.9.86",
        (
            (
                "nvidia_cuda_nvrtc_cu12-12.9.86-py3-none-manylinux2010_x86_64.manylinux_2_12_x86_64.whl",
                "210cf05005a447e29214e9ce50851e83fc5f4358df8b453155d5e1918094dcb4",
                "https://files.pythonhosted.org/packages/b8/85/e4af82cc9202023862090bfca4ea827d533329e925c758f0cde964cb54b7/nvidia_cuda_nvrtc_cu12-12.9.86-py3-none-manylinux2010_x86_64.manylinux_2_12_x86_64.whl",
                89568129,
            ),
            (
                "nvidia_cuda_nvrtc_cu12-12.9.86-py3-none-manylinux2014_aarch64.manylinux_2_17_aarch64.whl",
                "096d4de6bda726415dfaf3198d4f5c522b8e70139c97feef5cd2ca6d4cd9cead",
                "https://files.pythonhosted.org/packages/64/eb/c2295044b8f3b3b08860e2f6a912b702fc92568a167259df5dddb78f325e/nvidia_cuda_nvrtc_cu12-12.9.86-py3-none-manylinux2014_aarch64.manylinux_2_17_aarch64.whl",
                44528905,
            ),
            (
                "nvidia_cuda_nvrtc_cu12-12.9.86-py3-none-win_amd64.whl",
                "72972ebdcf504d69462d3bcd67e7b81edd25d0fb85a2c46d3ea3517666636349",
                "https://files.pythonhosted.org/packages/52/de/823919be3b9d0ccbf1f784035423c5f18f4267fb0123558d58b813c6ec86/nvidia_cuda_nvrtc_cu12-12.9.86-py3-none-win_amd64.whl",
                76408187,
            ),
        ),
    ),
    LockedDistribution(
        "nvidia-cuda-runtime-cu12",
        "12.9.79",
        (
            (
                "nvidia_cuda_runtime_cu12-12.9.79-py3-none-manylinux2014_aarch64.manylinux_2_17_aarch64.whl",
                "83469a846206f2a733db0c42e223589ab62fd2fabac4432d2f8802de4bded0a4",
                "https://files.pythonhosted.org/packages/bc/e0/0279bd94539fda525e0c8538db29b72a5a8495b0c12173113471d28bce78/nvidia_cuda_runtime_cu12-12.9.79-py3-none-manylinux2014_aarch64.manylinux_2_17_aarch64.whl",
                3515012,
            ),
            (
                "nvidia_cuda_runtime_cu12-12.9.79-py3-none-manylinux2014_x86_64.manylinux_2_17_x86_64.whl",
                "25bba2dfb01d48a9b59ca474a1ac43c6ebf7011f1b0b8cc44f54eb6ac48a96c3",
                "https://files.pythonhosted.org/packages/bc/46/a92db19b8309581092a3add7e6fceb4c301a3fd233969856a8cbf042cd3c/nvidia_cuda_runtime_cu12-12.9.79-py3-none-manylinux2014_x86_64.manylinux_2_17_x86_64.whl",
                3493179,
            ),
            (
                "nvidia_cuda_runtime_cu12-12.9.79-py3-none-win_amd64.whl",
                "8e018af8fa02363876860388bd10ccb89eb9ab8fb0aa749aaf58430a9f7c4891",
                "https://files.pythonhosted.org/packages/59/df/e7c3a360be4f7b93cee39271b792669baeb3846c58a4df6dfcf187a7ffab/nvidia_cuda_runtime_cu12-12.9.79-py3-none-win_amd64.whl",
                3591604,
            ),
        ),
    ),
    LockedDistribution(
        "nvidia-cufft-cu12",
        "11.4.1.4",
        (
            (
                "nvidia_cufft_cu12-11.4.1.4-py3-none-manylinux2014_aarch64.manylinux_2_17_aarch64.whl",
                "1a28c9b12260a1aa7a8fd12f5ebd82d027963d635ba82ff39a1acfa7c4c0fbcf",
                "https://files.pythonhosted.org/packages/9b/2b/76445b0af890da61b501fde30650a1a4bd910607261b209cccb5235d3daa/nvidia_cufft_cu12-11.4.1.4-py3-none-manylinux2014_aarch64.manylinux_2_17_aarch64.whl",
                200822453,
            ),
            (
                "nvidia_cufft_cu12-11.4.1.4-py3-none-manylinux2014_x86_64.manylinux_2_17_x86_64.whl",
                "c67884f2a7d276b4b80eb56a79322a95df592ae5e765cf1243693365ccab4e28",
                "https://files.pythonhosted.org/packages/95/f4/61e6996dd20481ee834f57a8e9dca28b1869366a135e0d42e2aa8493bdd4/nvidia_cufft_cu12-11.4.1.4-py3-none-manylinux2014_x86_64.manylinux_2_17_x86_64.whl",
                200877592,
            ),
            (
                "nvidia_cufft_cu12-11.4.1.4-py3-none-win_amd64.whl",
                "8e5bfaac795e93f80611f807d42844e8e27e340e0cde270dcb6c65386d795b80",
                "https://files.pythonhosted.org/packages/20/ee/29955203338515b940bd4f60ffdbc073428f25ef9bfbce44c9a066aedc5c/nvidia_cufft_cu12-11.4.1.4-py3-none-win_amd64.whl",
                200067309,
            ),
        ),
    ),
    LockedDistribution(
        "nvidia-curand-cu12",
        "10.3.10.19",
        (
            (
                "nvidia_curand_cu12-10.3.10.19-py3-none-manylinux_2_27_aarch64.whl",
                "de663377feb1697e1d30ed587b07d5721fdd6d2015c738d7528a6002a6134d37",
                "https://files.pythonhosted.org/packages/14/1c/2a45afc614d99558d4a773fa740d8bb5471c8398eeed925fc0fcba020173/nvidia_curand_cu12-10.3.10.19-py3-none-manylinux_2_27_aarch64.whl",
                68292066,
            ),
            (
                "nvidia_curand_cu12-10.3.10.19-py3-none-manylinux_2_27_x86_64.whl",
                "49b274db4780d421bd2ccd362e1415c13887c53c214f0d4b761752b8f9f6aa1e",
                "https://files.pythonhosted.org/packages/31/44/193a0e171750ca9f8320626e8a1f2381e4077a65e69e2fb9708bd479e34a/nvidia_curand_cu12-10.3.10.19-py3-none-manylinux_2_27_x86_64.whl",
                68295626,
            ),
            (
                "nvidia_curand_cu12-10.3.10.19-py3-none-win_amd64.whl",
                "e8129e6ac40dc123bd948e33d3e11b4aa617d87a583fa2f21b3210e90c743cde",
                "https://files.pythonhosted.org/packages/e5/98/1bd66fd09cbe1a5920cb36ba87029d511db7cca93979e635fd431ad3b6c0/nvidia_curand_cu12-10.3.10.19-py3-none-win_amd64.whl",
                68774847,
            ),
        ),
    ),
    LockedDistribution(
        "nvidia-cusolver-cu12",
        "11.7.5.82",
        (
            (
                "nvidia_cusolver_cu12-11.7.5.82-py3-none-manylinux_2_27_aarch64.whl",
                "62efa83e4ace59a4c734d052bb72158e888aa7b770e1a5f601682f16fe5b4fd2",
                "https://files.pythonhosted.org/packages/03/99/686ff9bf3a82a531c62b1a5c614476e8dfa24a9d89067aeedf3592ee4538/nvidia_cusolver_cu12-11.7.5.82-py3-none-manylinux_2_27_aarch64.whl",
                337869834,
            ),
            (
                "nvidia_cusolver_cu12-11.7.5.82-py3-none-manylinux_2_27_x86_64.whl",
                "15da72d1340d29b5b3cf3fd100e3cd53421dde36002eda6ed93811af63c40d88",
                "https://files.pythonhosted.org/packages/33/40/79b0c64d44d6c166c0964ec1d803d067f4a145cca23e23925fd351d0e642/nvidia_cusolver_cu12-11.7.5.82-py3-none-manylinux_2_27_x86_64.whl",
                338117415,
            ),
            (
                "nvidia_cusolver_cu12-11.7.5.82-py3-none-win_amd64.whl",
                "77666337237716783c6269a658dea310195cddbd80a5b2919b1ba8735cec8efd",
                "https://files.pythonhosted.org/packages/32/5d/feb7f86b809f89b14193beffebe24cf2e4bf7af08372ab8cdd34d19a65a0/nvidia_cusolver_cu12-11.7.5.82-py3-none-win_amd64.whl",
                326215953,
            ),
        ),
    ),
    LockedDistribution(
        "nvidia-cusparse-cu12",
        "12.5.10.65",
        (
            (
                "nvidia_cusparse_cu12-12.5.10.65-py3-none-manylinux2014_aarch64.manylinux_2_17_aarch64.whl",
                "221c73e7482dd93eda44e65ce567c031c07e2f93f6fa0ecd3ba876a195023e83",
                "https://files.pythonhosted.org/packages/5e/6f/8710fbd17cdd1d0fc3fea7d36d5b65ce1933611c31e1861da330206b253a/nvidia_cusparse_cu12-12.5.10.65-py3-none-manylinux2014_aarch64.manylinux_2_17_aarch64.whl",
                366359408,
            ),
            (
                "nvidia_cusparse_cu12-12.5.10.65-py3-none-manylinux2014_x86_64.manylinux_2_17_x86_64.whl",
                "73060ce019ac064a057267c585bf1fd5a353734151f87472ff02b2c5c9984e78",
                "https://files.pythonhosted.org/packages/12/46/b0fd4b04f86577921feb97d8e2cf028afe04f614d17fb5013de9282c9216/nvidia_cusparse_cu12-12.5.10.65-py3-none-manylinux2014_x86_64.manylinux_2_17_x86_64.whl",
                366465088,
            ),
            (
                "nvidia_cusparse_cu12-12.5.10.65-py3-none-win_amd64.whl",
                "9e487468a22a1eaf1fbd1d2035936a905feb79c4ce5c2f67626764ee4f90227c",
                "https://files.pythonhosted.org/packages/73/ef/063500c25670fbd1cbb0cd3eb7c8a061585b53adb4dd8bf3492bb49b0df3/nvidia_cusparse_cu12-12.5.10.65-py3-none-win_amd64.whl",
                362504719,
            ),
        ),
    ),
    LockedDistribution(
        "nvidia-nvjitlink-cu12",
        "12.9.86",
        (
            (
                "nvidia_nvjitlink_cu12-12.9.86-py3-none-manylinux2010_x86_64.manylinux_2_12_x86_64.whl",
                "e3f1171dbdc83c5932a45f0f4c99180a70de9bd2718c1ab77d14104f6d7147f9",
                "https://files.pythonhosted.org/packages/46/0c/c75bbfb967457a0b7670b8ad267bfc4fffdf341c074e0a80db06c24ccfd4/nvidia_nvjitlink_cu12-12.9.86-py3-none-manylinux2010_x86_64.manylinux_2_12_x86_64.whl",
                39748338,
            ),
            (
                "nvidia_nvjitlink_cu12-12.9.86-py3-none-manylinux2014_aarch64.manylinux_2_17_aarch64.whl",
                "994a05ef08ef4b0b299829cde613a424382aff7efb08a7172c1fa616cc3af2ca",
                "https://files.pythonhosted.org/packages/97/bc/2dcba8e70cf3115b400fef54f213bcd6715a3195eba000f8330f11e40c45/nvidia_nvjitlink_cu12-12.9.86-py3-none-manylinux2014_aarch64.manylinux_2_17_aarch64.whl",
                39514880,
            ),
            (
                "nvidia_nvjitlink_cu12-12.9.86-py3-none-win_amd64.whl",
                "cc6fcec260ca843c10e34c936921a1c426b351753587fdd638e8cff7b16bb9db",
                "https://files.pythonhosted.org/packages/dd/7e/2eecb277d8a98184d881fb98a738363fd4f14577a4d2d7f8264266e82623/nvidia_nvjitlink_cu12-12.9.86-py3-none-win_amd64.whl",
                35584936,
            ),
        ),
    ),
)
"""The pack's eleven distributions, copied from ``uv.lock`` (a test keeps them equal).

``numpy`` is not here: the pack uses the bundle's own (CuPy 14.2.0 needs ``>=2.0,<2.6``).
"""


def stamp_for(distribution: str, version: str) -> str:
    """Return the pack stamp for a CuPy distribution and version.

    Args:
        distribution: The CuPy distribution name, for example ``cupy-cuda12x``.
        version: Its version, for example ``14.2.0``.

    Returns:
        ``<version>-cu<CUDA major>``, for example ``14.2.0-cu12``.

    Raises:
        ValueError: The name carries no ``cuda<major>x`` part.
    """
    match = re.fullmatch(r"cupy-cuda(\d+)x", distribution)
    if match is None:
        raise ValueError(f"not a CUDA CuPy distribution: {distribution!r}")
    return f"{version}-cu{match.group(1)}"


def _locked_cupy_version() -> str:
    """Return the locked ``cupy-cuda12x`` version from :data:`LOCKED_DISTRIBUTIONS`."""
    for locked in LOCKED_DISTRIBUTIONS:
        if locked.name == CUPY_DISTRIBUTION:
            return locked.version
    raise LookupError(f"{CUPY_DISTRIBUTION} is not in LOCKED_DISTRIBUTIONS")


STAMP = stamp_for(CUPY_DISTRIBUTION, _locked_cupy_version())
"""This build's pack stamp (``14.2.0-cu12``): the only pack folder the loader reads."""


def _absolute(environ: Mapping[str, str], name: str) -> Path | None:
    """Return the variable as an absolute path, or None when unset, empty or relative."""
    value = environ.get(name, "")
    if not value:
        return None
    path = Path(value)
    return path if path.is_absolute() else None


def pack_root(
    *,
    environ: Mapping[str, str] | None = None,
    platform: str | None = None,
    home: Path | None = None,
) -> Path | None:
    """Return the folder that holds the GPU packs on this platform. Creates nothing.

    - Windows: ``%LOCALAPPDATA%/Clearwater/gpu-pack`` (``<home>/AppData/Local`` when the
      variable is unset, empty or relative);
    - macOS: None (no CUDA there; the loader does nothing);
    - Linux and any other platform: ``$XDG_DATA_HOME/clearwater/gpu-pack``
      (``<home>/.local/share`` when the variable is unset, empty or relative).

    Args:
        environ: The environment to read; ``os.environ`` when None.
        platform: A ``sys.platform`` value; the running one when None.
        home: The home folder used by the fallbacks; ``Path.home()`` when None.

    Returns:
        The pack root, or None on macOS.
    """
    env = os.environ if environ is None else environ
    kind = sys.platform if platform is None else platform
    if kind == "darwin":
        return None
    if kind == "win32":
        local = _absolute(env, "LOCALAPPDATA")
        if local is None:
            local = (Path.home() if home is None else home) / "AppData" / "Local"
        return local / WINDOWS_APP_FOLDER / PACK_FOLDER_NAME
    data = _absolute(env, "XDG_DATA_HOME")
    if data is None:
        data = (Path.home() if home is None else home) / ".local" / "share"
    return data / POSIX_APP_FOLDER / PACK_FOLDER_NAME


def _file_digest(path: Path | str) -> bytes:
    """Return a file's raw sha256 digest, reading it in 1 MiB blocks.

    Args:
        path: The file.

    Returns:
        The 32-byte digest.

    Raises:
        OSError: The file cannot be read.
    """
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.digest()


def file_sha256(path: Path) -> str:
    """Return a file's sha256 as lower-case hex.

    Args:
        path: The file.

    Returns:
        The digest.

    Raises:
        OSError: The file cannot be read.
    """
    return _file_digest(path).hex()


def record_hash(digest: bytes) -> str:
    """Return a sha256 digest in ``RECORD``'s form: ``sha256=`` + urlsafe base64, no padding.

    Args:
        digest: The raw digest.

    Returns:
        For example ``sha256=47DEQpj8HBSa-_TImW-5JCeuQeRkm5NMpJWZG3hSuFU`` (an empty file).
    """
    return "sha256=" + base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


@dataclass(frozen=True)
class RecordRow:
    """One row of a distribution's ``RECORD`` file.

    Attributes:
        path: The file, relative to ``site-packages``, with ``/`` separators.
        hash: ``<algorithm>=<urlsafe base64>``, or ``""`` (the ``RECORD`` file's own row).
        size: The size in bytes, or None when the row gives none.
    """

    path: str
    hash: str
    size: int | None


_RECORD_SIZE = re.compile(r"[0-9]{1,20}")
"""A ``RECORD`` size: ASCII digits, at most 20 (any real file size; Reviewer A r3 #4)."""

_RECORD_HASH = re.compile(r"[A-Za-z0-9]{1,16}=[A-Za-z0-9_-]{1,128}")
"""A ``RECORD`` hash: ``<algorithm>=<urlsafe base64, no padding>``."""


def _component_problem(component: str) -> str | None:
    """Return why one ``RECORD`` path component is not allowed, or None (A r3 #4, #5).

    Refused: an empty or ``.`` component, ``..``, an alternate data stream or drive (``:``),
    and a component ending in ``.`` or a space (Windows resolves ``a.py.`` and ``a.py `` to
    ``a.py``).
    """
    if component in ("", "."):
        return "an empty or '.' part"
    if component == "..":
        return "a '..' part"
    if ":" in component:
        return "a ':' (a drive or an alternate data stream)"
    if component.endswith((".", " ")):
        return "a part ending in '.' or a space"
    return None


def parse_record(text: str) -> list[RecordRow] | str:
    """Parse a ``RECORD`` file's text (CSV rows ``path,hash,size``), validating each row first.

    Every row is checked before it is used (Reviewer A r3 #4, #5): three fields, no NUL in
    any, a non-empty path, a hash that is empty or ``<algorithm>=<base64>``, a size that is
    empty or at most 20 ASCII digits; then the path's parts (split at ``/`` and the backslash): none
    absolute, none with a drive, ``..``, ``:``, an empty or ``.`` part, or a trailing ``.`` or
    space. So a malformed ``RECORD`` is a rejection reason, never an exception.

    Args:
        text: The file's text.

    Returns:
        The rows, or the reason the text is malformed: ``RECORD malformed: row <n>: <what>``,
        ``RECORD row outside site-packages: <path>`` (absolute, a drive, or ``..``) or
        ``RECORD row path not allowed (<what>): <path>``.
    """
    rows: list[RecordRow] = []
    reader = csv.reader(io.StringIO(text, newline=""))
    number = 0
    while True:
        number += 1
        try:
            fields = next(reader)
        except StopIteration:
            return rows
        except csv.Error:
            return f"RECORD malformed: row {number}: not CSV"
        if not fields:
            continue
        if len(fields) != 3:
            return f"RECORD malformed: row {number}: not 3 fields"
        if any("\x00" in field for field in fields):
            return f"RECORD malformed: row {number}: a NUL character"
        path, digest, size = fields
        if not path:
            return f"RECORD malformed: row {number}: an empty path"
        if digest and not _RECORD_HASH.fullmatch(digest):
            return f"RECORD malformed: row {number}: a hash not of the form algorithm=base64"
        if size and not _RECORD_SIZE.fullmatch(size):
            return f"RECORD malformed: row {number}: a size not of 1-20 digits"
        posix, windows = PurePosixPath(path), PureWindowsPath(path)
        if posix.is_absolute() or windows.drive or windows.root or ".." in windows.parts:
            return f"RECORD row outside site-packages: {_safe(path)}"
        for component in re.split(r"[/\\]", path):
            problem = _component_problem(component)
            if problem is not None:
                return f"RECORD row path not allowed ({problem}): {_safe(path)}"
        rows.append(RecordRow(path, digest, int(size) if size else None))


def platform_tags() -> tuple[str, str]:
    """Return the running interpreter's tag and platform tag, as wheel tags spell them.

    Returns:
        For example ``("cp312", "win_amd64")`` or ``("cp312", "linux_x86_64")``.
    """
    version = f"{sys.version_info.major}{sys.version_info.minor}"
    prefix = "cp" if sys.implementation.name == "cpython" else sys.implementation.name[:2]
    platform = re.sub(r"[-.]", "_", sysconfig.get_platform()).lower()
    return f"{prefix}{version}", platform


_MANYLINUX = re.compile(r"manylinux(?:1|2010|2014|_\d+_\d+)_(?P<arch>\w+)")
"""A ``manylinux`` platform tag; the glibc version it names is not compared."""


def tag_fits(tag: str, interpreter: str, platform: str) -> bool:
    """Return whether one wheel tag (``python-abi-platform``) can run here.

    The python part fits when it is the interpreter's tag (``cp312``), ``py3`` or ``py312``
    (the same major and minor); the ABI part when it is ``none``, the interpreter's tag or
    ``abi3``; the platform part when it is ``any``, the running platform tag, or, on Linux, a
    ``manylinux`` tag for the same machine (its glibc version is not compared). A compressed
    tag set (``py2.py3``) fits when any of its tags does.

    Args:
        tag: The tag, for example ``cp312-cp312-win_amd64``.
        interpreter: The interpreter's tag (:func:`platform_tags`).
        platform: The running platform tag (:func:`platform_tags`).

    Returns:
        True when the tag fits.
    """
    parts = tag.split("-")
    if len(parts) != 3:
        return False
    major = interpreter[2:3]
    pythons = {interpreter, f"py{major}", f"py{interpreter[2:]}"}
    abis = {"none", interpreter} | ({"abi3"} if interpreter.startswith("cp") else set())
    pys, abi_set, plats = (part.split(".") for part in parts)

    def platform_fits(plat: str) -> bool:
        if plat in ("any", platform):
            return True
        match = _MANYLINUX.fullmatch(plat)
        return match is not None and platform == f"linux_{match.group('arch')}"

    return (
        any(p in pythons for p in pys)
        and any(a in abis for a in abi_set)
        and any(platform_fits(p) for p in plats)
    )


@dataclass(frozen=True)
class PackStatus:
    """What the loader found and did.

    Attributes:
        stamp: The stamp looked for (:data:`STAMP`).
        outcome: ``"loaded"``, ``"absent"`` or ``"rejected"``.
        reason: Why a pack was rejected; None otherwise.
        site_packages: The folder put on ``sys.path`` when loaded; None otherwise.
        dll_directories: The folders added to the DLL search path (Windows, when loaded).
    """

    stamp: str
    outcome: Outcome
    reason: str | None = None
    site_packages: Path | None = None
    dll_directories: tuple[Path, ...] = ()

    @property
    def line(self) -> str:
        """The one log line: ``gpu pack <stamp>: loaded`` / ``absent`` / ``rejected: <why>``."""
        if self.outcome == "rejected":
            return f"gpu pack {self.stamp}: rejected: {self.reason}"
        return f"gpu pack {self.stamp}: {self.outcome}"


_CONTROL_CHARACTER = re.compile(r"[\x00-\x1f\x7f]")
"""An ASCII control character (newline, tab, carriage return and the rest)."""


def _safe(value: object) -> str:
    """Return a value from the manifest as short one-line ASCII text for a reason.

    Non-ASCII characters and ASCII control characters (newline, tab, carriage return and the
    rest) become backslash escapes (``e`` with an acute accent as backslash-``xe9``, a newline
    as backslash-``x0a``), so a reason is always one printable log line (at most 80
    characters of the value; Reviewer A r2 #12).
    """
    text = value if isinstance(value, str) else repr(value)
    ascii_text = text.encode("ascii", "backslashreplace").decode("ascii")
    one_line = _CONTROL_CHARACTER.sub(lambda m: f"\\x{ord(m.group()):02x}", ascii_text)
    return one_line[:80]


def _manifest_entries(document: object) -> list[dict[str, str]] | str:
    """Return the manifest's distribution entries, or the reason it is malformed.

    Args:
        document: The parsed manifest.

    Returns:
        The entries (each a mapping of string fields), or a rejection reason.
    """
    if not isinstance(document, dict):
        return "manifest malformed: not an object"
    found = document.get("format")
    if type(found) is not int or found != MANIFEST_FORMAT:
        return f"manifest format {_safe(found)}, expected {MANIFEST_FORMAT}"
    if document.get("stamp") != STAMP:
        return f"manifest stamp {_safe(repr(document.get('stamp')))}, expected {STAMP!r}"
    raw = document.get("distributions")
    if not isinstance(raw, list):
        return "manifest malformed: no distributions list"
    fields = ("name", "version", "wheel", "wheel_sha256", "record_sha256")
    entries: list[dict[str, str]] = []
    for item in raw:
        if not isinstance(item, dict) or not all(isinstance(item.get(f), str) for f in fields):
            return "manifest malformed: a distribution entry lacks a string field"
        entries.append({f: str(item[f]) for f in fields})
    return entries


def check_pack(folder: Path) -> str | None:
    """Run the cheap check on one pack folder (``<pack root>/<stamp>``). Reads only.

    This is :func:`pack_problems` without file hashing, stopped at its first problem: the
    check every start-up runs. A file-system error on any check (an existence or type check
    included) is a rejection, never an exception out of start-up.

    Args:
        folder: The pack folder.

    Returns:
        None when the pack passes, else the first failed check as a short ASCII reason.
    """
    try:
        return next(pack_problems(folder), None)
    except Exception as error:  # start-up must never fail on a pack (A r3 #4)
        return f"pack check failed: {_safe(type(error).__name__)}"


def pack_problems(
    folder: Path,
    *,
    full: bool = False,
    tags: tuple[str, str] | None = None,
    manifest: object = None,
) -> Iterator[str]:
    """Yield every problem :func:`_pack_problems` finds; any exception ends it as one problem.

    A file-system error becomes ``pack unreadable: <type>`` and any other exception (a
    malformed ``RECORD`` that the row validation did not foresee, say)
    ``pack check failed: <type>``, so neither start-up (:func:`check_pack`) nor ``--verify``
    is ever stopped by an exception (Reviewer A r3 #4).

    Args:
        folder: The pack folder.
        full: Also hash every listed file.
        tags: The (interpreter, platform) tags to fit; :func:`platform_tags` when None.
        manifest: In-memory manifest for staging verification; None reads the disk file.

    Yields:
        Each problem as a short ASCII reason, in check order.
    """
    try:
        yield from _pack_problems(folder, full=full, tags=tags, manifest=manifest)
    except OSError as error:
        yield f"pack unreadable: {_safe(type(error).__name__)}"
    except Exception as error:  # a rejection, never an escape (A r3 #4)
        yield f"pack check failed: {_safe(type(error).__name__)}"


def _pack_problems(
    folder: Path,
    *,
    full: bool = False,
    tags: tuple[str, str] | None = None,
    manifest: object = None,
) -> Iterator[str]:
    """Yield every way one pack folder differs from the lock and from its ``RECORD`` files.

    The checks, in order:

    1. ``manifest.json`` parses, its format is :data:`MANIFEST_FORMAT` and its stamp is
       :data:`STAMP`; ``site-packages`` exists; the distributions are exactly
       :data:`LOCKED_DISTRIBUTIONS` (each failure here ends the walk).
    2. For each distribution (ruling (d), then (c), then (a)): its locked version, one of its
       locked wheels with that wheel's sha256, the installed ``RECORD`` file with the
       manifest's sha256; its ``WHEEL`` file's ``Tag:`` lines, of which at least one must fit
       the running platform (:func:`tag_fits`); and each ``RECORD`` row (:func:`parse_record`)
       naming a regular file that exists with the row's size. A row without a size (the
       ``RECORD`` file's own) is checked for existence only.
    3. Ruling (b): every top-level entry of ``site-packages`` is owned, that is, it is the
       first path component of some row of the eleven ``RECORD`` files (compared as the
       platform compares file names, so case-insensitively on Windows). Skipped when a
       ``RECORD`` could not be read, since ownership is then unknown.

    With ``full`` each row's file is also hashed and compared with the row's ``sha256``, and a
    row without a hash (other than the ``RECORD`` file's own) is a problem, and so is every file
    under ``site-packages`` that no row names (:func:`_unlisted_files`; Q2): the install-time
    check (``tools/package/build.py --verify``). Without it no file but the ``RECORD`` files is
    read.

    Args:
        folder: The pack folder.
        full: Also hash every listed file.
        tags: The (interpreter, platform) tags to fit; :func:`platform_tags` when None.
        manifest: In-memory manifest, or None to read the disk file.

    Yields:
        Each problem as a short ASCII reason, in check order.

    Raises:
        OSError: A file-system error on a structural check (the manifest, ``site-packages``,
            a ``RECORD`` existence check, the ``site-packages`` listing). A listed file that
            cannot be examined is yielded as a problem instead.
    """
    document = manifest
    if manifest is None:
        path = folder / MANIFEST_NAME
        if not path.is_file():
            yield f"no {MANIFEST_NAME}"
            return
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, ValueError) as error:
            yield f"{MANIFEST_NAME} unreadable: {type(error).__name__}"
            return
    entries = _manifest_entries(document)
    if isinstance(entries, str):
        yield entries
        return
    site = folder / SITE_PACKAGES_NAME
    if not site.is_dir():
        yield f"no {SITE_PACKAGES_NAME} folder"
        return
    expected = {locked.name: locked for locked in LOCKED_DISTRIBUTIONS}
    seen: set[str] = set()
    for entry in entries:
        name = entry["name"]
        if name not in expected:
            yield f"unexpected distribution {_safe(name)}"
            return
        if name in seen:
            yield f"duplicate distribution {name}"
            return
        seen.add(name)
    missing = sorted(set(expected) - seen)
    if missing:
        yield f"missing distribution {missing[0]}"
        return
    interpreter, platform = platform_tags() if tags is None else tags
    owned: set[str] = set()
    listed: set[str] = set()
    every_record_read = True
    for entry in entries:
        locked = expected[entry["name"]]
        if entry["version"] != locked.version:
            yield f"{locked.name} version {_safe(entry['version'])}, expected {locked.version}"
        if (entry["wheel"], entry["wheel_sha256"].lower()) not in {
            (wheel, digest) for wheel, digest, _url, _size in locked.wheels
        }:
            wheel = _safe(entry["wheel"])
            yield f"{locked.name} wheel {wheel} with that sha256 is not in the lock"
        rows = yield from _record_problems(site, locked, entry["record_sha256"])
        if rows is None:
            every_record_read = False
            continue
        yield from _wheel_tag_problems(site, locked, interpreter, platform)
        for row in rows:
            owned.add(os.path.normcase(PurePosixPath(row.path).parts[0]))
            listed.add(_listed_key(row.path))
            yield from _row_problems(site, locked, row, full=full)
    if every_record_read:
        with os.scandir(site) as listing:
            names = sorted(item.name for item in listing)
        for name in names:
            if os.path.normcase(name) not in owned:
                yield f"unlisted entry in site-packages: {_safe(name)}"
        if full:
            yield from _unlisted_files(site, owned, listed)


def _listed_key(path: str) -> str:
    """Return a ``RECORD`` path (or a walked one, ``/``-joined) in its comparison form."""
    return os.path.normcase("/".join(part for part in re.split(r"[/\\]", path) if part))


def _is_link_or_reparse(info: os.stat_result) -> bool:
    """Return whether an lstat result identifies any link or Windows reparse tag."""
    if sys.platform == "win32":
        return stat.S_ISLNK(info.st_mode) or bool(
            info.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT
        )
    else:
        return stat.S_ISLNK(info.st_mode)


def _unlisted_files(site: Path, owned: set[str], listed: set[str]) -> Iterator[str]:
    """Yield every file under ``site-packages`` that no ``RECORD`` row names (the full check).

    CHARC's Q2 ruling: no exclusions (``__pycache__`` included). A top-level entry that no
    ``RECORD`` owns is already reported by the ownership check, so its files are not repeated.

    Raises:
        OSError: A folder cannot be listed (``os.walk`` reports it).
    """

    def fail(error: OSError) -> None:
        raise error

    for top, folders, files in os.walk(site, onerror=fail):
        folders.sort()
        relative = Path(top).relative_to(site).parts
        for name in list(folders):
            if _is_link_or_reparse(os.lstat(Path(top) / name)):
                path = "/".join([*relative, name])
                yield f"link or reparse point in site-packages: {_safe(path)}"
                folders.remove(name)
        if relative and os.path.normcase(relative[0]) not in owned:
            folders[:] = []
            continue
        for name in sorted(files):
            if not relative and os.path.normcase(name) not in owned:
                continue
            path = "/".join([*relative, name])
            if _listed_key(path) not in listed:
                yield f"unlisted file in site-packages: {_safe(path)}"


def _record_problems(
    site: Path, locked: LockedDistribution, record_sha256: str
) -> Generator[str, None, list[RecordRow] | None]:
    """Check one distribution's ``RECORD`` file and return its rows.

    Args:
        site: The pack's ``site-packages``.
        locked: The distribution.
        record_sha256: The sha256 hex the manifest records for the file.

    Yields:
        A missing, unreadable, mismatched or malformed ``RECORD``.

    Returns:
        The rows, or None when the file is missing, unreadable or malformed.

    Raises:
        OSError: The existence check itself fails.
    """
    record = site / locked.dist_info_name / "RECORD"
    if not record.is_file():
        yield f"{locked.name} RECORD missing"
        return None
    try:
        data = record.read_bytes()
    except OSError as error:
        yield f"{locked.name} RECORD unreadable: {type(error).__name__}"
        return None
    if hashlib.sha256(data).hexdigest() != record_sha256.lower():
        yield f"{locked.name} RECORD sha256 mismatch"
    try:
        rows = parse_record(data.decode("utf-8"))
    except UnicodeDecodeError:
        rows = "RECORD malformed: not UTF-8"
    if isinstance(rows, str):
        yield f"{locked.name} {rows}"
        return None
    return rows


def _wheel_tag_problems(
    site: Path, locked: LockedDistribution, interpreter: str, platform: str
) -> Iterator[str]:
    """Check that one distribution's ``WHEEL`` file names a tag for this platform (ruling (c)).

    Args:
        site: The pack's ``site-packages``.
        locked: The distribution.
        interpreter: The interpreter's tag.
        platform: The running platform tag.

    Yields:
        A missing or unreadable ``WHEEL`` file, one with no ``Tag:`` line, or one whose tags
        do not fit.
    """
    wheel = site / locked.dist_info_name / "WHEEL"
    try:
        text = wheel.read_text(encoding="utf-8")
    except FileNotFoundError:
        yield f"{locked.name} WHEEL missing"
        return
    except (OSError, UnicodeDecodeError) as error:
        yield f"{locked.name} WHEEL unreadable: {type(error).__name__}"
        return
    tags = sorted(
        line.split(":", 1)[1].strip() for line in text.splitlines() if line.startswith("Tag:")
    )
    if not tags:
        yield f"{locked.name} WHEEL has no Tag line"
    elif not any(tag_fits(tag, interpreter, platform) for tag in tags):
        yield f"{locked.name} wheel tag {_safe(','.join(tags))} is not for {platform}"


def _row_problems(
    site: Path, locked: LockedDistribution, row: RecordRow, *, full: bool
) -> Iterator[str]:
    """Check one ``RECORD`` row against the file it names (ruling (a); with ``full``, its hash).

    Args:
        site: The pack's ``site-packages``.
        locked: The distribution the row belongs to.
        row: The row.
        full: Also hash the file and compare it with the row's ``sha256``.

    Yields:
        A missing, unreadable or non-regular file, a size mismatch and, with ``full``, a
        missing, non-sha256 or mismatched hash.
    """
    name = f"{locked.name} file {_safe(row.path)}"
    path = os.path.join(site, *PurePosixPath(row.path).parts)
    try:
        info = os.lstat(path) if full else os.stat(path)
    except (FileNotFoundError, NotADirectoryError):
        yield f"{name} missing"
        return
    except OSError as error:
        yield f"{name} unreadable: {type(error).__name__}"
        return
    if full and _is_link_or_reparse(info):
        yield f"{name} is a link or reparse point"
        return
    if not stat.S_ISREG(info.st_mode):
        yield f"{name} is not a file"
        return
    if row.size is not None and info.st_size != row.size:
        yield f"{name} size {info.st_size}, RECORD says {row.size}"
    if not full:
        return
    own_record = os.path.normcase(row.path) == os.path.normcase(f"{locked.dist_info_name}/RECORD")
    if not row.hash:
        if not own_record:
            yield f"{name} has no hash in RECORD"
        return
    algorithm, _, _value = row.hash.partition("=")
    if algorithm != "sha256":
        yield f"{name} hash {_safe(algorithm)}, expected sha256"
        return
    try:
        actual = record_hash(_file_digest(path))
    except OSError as error:
        yield f"{name} unreadable: {type(error).__name__}"
        return
    if actual != row.hash:
        yield f"{name} sha256 mismatch"


_DLL_HANDLES: list[object] = []
"""The ``os.add_dll_directory`` handles, kept for the process's life (closing one removes it)."""


def _add_dll_directories(site: Path) -> tuple[Path, ...] | str:
    """On Windows, add each ``site/nvidia/*/bin`` folder to the DLL search path.

    Args:
        site: The pack's ``site-packages`` folder.

    Returns:
        The folders added (none on other platforms), or a rejection reason when they cannot
        be listed or one cannot be added (the ones already added are removed again).
    """
    nvidia = site / "nvidia"
    try:  # os.scandir, not Path.glob: glob swallows an access error (Reviewer A r3 #7)
        if nvidia.is_dir():
            with os.scandir(nvidia) as listing:
                names = sorted(item.name for item in listing)
            folders = tuple(nvidia / n / "bin" for n in names if (nvidia / n / "bin").is_dir())
        else:
            folders = ()
    except OSError as error:
        return f"DLL folders unreadable: {type(error).__name__}"
    if sys.platform == "win32":
        added: list[object] = []
        for folder in folders:
            try:
                added.append(os.add_dll_directory(str(folder)))
            except OSError as error:
                for handle in added:
                    close = getattr(handle, "close", None)
                    if callable(close):
                        close()
                return f"DLL folder nvidia/{_safe(folder.parent.name)}/bin: {type(error).__name__}"
        _DLL_HANDLES.extend(added)
        return folders
    else:
        return ()


def _load_folder(folder: Path) -> PackStatus:
    """Check one existing pack folder and, when it passes, load it.

    Args:
        folder: ``<pack root>/<stamp>``.

    Returns:
        A ``loaded`` or ``rejected`` status.
    """
    reason = check_pack(folder)
    if reason is not None:
        return PackStatus(STAMP, "rejected", reason=reason)
    site = folder / SITE_PACKAGES_NAME
    dlls = _add_dll_directories(site)
    if isinstance(dlls, str):
        return PackStatus(STAMP, "rejected", reason=dlls)
    entry = str(site)
    if entry not in sys.path:
        sys.path.insert(0, entry)
    return PackStatus(STAMP, "loaded", site_packages=site, dll_directories=dlls)


def _find_and_load(folder: Path) -> PackStatus:
    """Load ``<pack root>/<stamp>`` when it is a folder; absent when it is not.

    Args:
        folder: ``<pack root>/<stamp>``.

    Returns:
        ``absent``, ``loaded`` or ``rejected`` (also when the folder cannot even be looked at:
        a file-system error is a rejection, never an exception out of start-up).
    """
    try:
        present = folder.is_dir()
    except OSError as error:
        return PackStatus(STAMP, "rejected", reason=f"pack unreadable: {type(error).__name__}")
    return _load_folder(folder) if present else PackStatus(STAMP, "absent")


def load(root: Path | None) -> PackStatus:
    """Look for this build's pack under ``root``, load it when it passes, and log one line.

    Loading = ``site-packages`` at the front of ``sys.path`` (once) and, on Windows, the
    ``nvidia/*/bin`` DLL folders. Absent or rejected = nothing changes. Never writes.

    Args:
        root: The pack root (:func:`pack_root`; tests pass a folder under ``tmp_path``), or
            None when the platform has no pack.

    Returns:
        The status (its :attr:`PackStatus.line` is the line logged).
    """
    status = PackStatus(STAMP, "absent") if root is None else _find_and_load(root / STAMP)
    _LOG.info("%s", status.line)
    return status


def activate() -> PackStatus | None:
    """Load the pack from :func:`pack_root` in a frozen build; do nothing otherwise (D4).

    Call it before anything imports ``cupy`` (``clearwater.__main__`` does, on its worker,
    ``-m`` and GUI branches). A named ``-m`` target activates the pack BEFORE it is judged (an
    absent or rejected pack, or a module not from the pack, is refused after this call); ``-c``,
    the multiprocessing flags, ``-m`` without a module name and a failed worker stdin isolation
    are refused before it.

    Returns:
        The status in a frozen build; None in a source run (nothing checked, nothing logged).
    """
    if not getattr(sys, "frozen", False):
        return None
    warnings.filterwarnings(
        "ignore", message="CUDA path could not be detected.*", category=UserWarning
    )
    status = load(pack_root())
    if status.outcome == "loaded" and status.site_packages is not None:
        add_site_prefix(status.site_packages)
    return status


def add_site_prefix(site_packages: Path) -> bool:
    """Put the pack's ``site-packages`` folder FIRST in ``site.PREFIXES`` (CHARC's F-F ruling).

    ``cuda.pathfinder`` finds the CUDA headers (and its wheel libraries) through
    ``site.getsitepackages()``, not ``sys.path``, so a frozen process that only has the pack on
    ``sys.path`` never finds the pack's ``nvidia/*/include``. On Windows ``getsitepackages()``
    lists each prefix ``P`` as ``P`` and ``P/Lib/site-packages``, so with the folder itself as
    the first prefix its first entry is exactly ``<pack>/site-packages`` (the second does not
    exist and is harmless). The FOLDER is inserted, never ``<pack>``. ``site`` is the bundled
    module: importing it in a frozen build runs nothing (``no_site``), and
    ``site.ENABLE_USER_SITE`` and ``sys.path`` are not changed here. On a future Linux leg the
    prefix spelling would differ (``getsitepackages()`` appends ``lib/python3.12/site-packages``
    there); it is not handled here.

    Never twice, in any spelling (Reviewer A r4 #2): EVERY existing entry naming the same folder
    (compared by ``os.path.normcase(os.path.normpath(...))``: case, a forward slash or a
    backslash, a trailing separator) is removed, and the one canonical ``str(site_packages)``
    is put first; the other prefixes keep their order. The list object itself is kept (changed
    in place).

    Called by :func:`activate` only, so only in a frozen build, after the ``sys.path``
    insertion; a source run never touches ``site.PREFIXES`` (1.0.0).

    Args:
        site_packages: The loaded pack's ``site-packages`` folder.

    Returns:
        True when ``site.PREFIXES`` changed; False when the canonical entry was already first
        and the only one naming the folder.
    """
    import site

    entry = str(site_packages)
    key = _prefix_key(entry)
    wanted = [entry, *(prefix for prefix in site.PREFIXES if _prefix_key(prefix) != key)]
    if wanted == site.PREFIXES:
        return False
    site.PREFIXES[:] = wanted
    return True


def _prefix_key(prefix: str) -> str:
    """Return a ``site.PREFIXES`` entry in the form two spellings of one folder share."""
    return os.path.normcase(os.path.normpath(prefix))


def _inside(path: str, folder: str) -> bool:
    """Return True when ``path`` lies in ``folder`` (both resolved, compared case-folded)."""
    try:
        resolved = os.path.normcase(os.path.realpath(path))
        common = os.path.commonpath([resolved, folder])
    except (OSError, ValueError):  # another drive, an empty or unresolvable path
        return False
    return common == folder


def module_from_pack(module: str, site_packages: Path) -> bool:
    """Return True when ``module``'s top-level package resolves from the pack's folder.

    The frozen entry runs ``-m <module>`` only for such a module (CHARC's F-D ruling): a
    library inside the pack (``cuda.pathfinder``'s canary probe) re-enters the executable as
    ``sys.executable -m <its module>``. The top-level name is resolved with
    :func:`importlib.util.find_spec` against the CURRENT ``sys.path`` and import hooks, so a
    name that exists both in the bundle and in the pack is judged by whichever comes first
    (the loaded pack is first on ``sys.path``). The spec's locations are its ``origin`` (when
    it is a file location) and every entry of ``submodule_search_locations`` (every portion of
    a namespace package such as ``cuda``); ALL of them must lie inside ``site_packages``,
    compared after ``os.path.realpath`` and ``os.path.normcase``. A built-in or frozen module,
    a name that does not resolve, or a malformed name (empty, relative) is not from the pack.
    Finding the spec of a top-level name executes none of its code.

    Args:
        module: The dotted module name given to ``-m``.
        site_packages: The loaded pack's ``site-packages`` (:attr:`PackStatus.site_packages`).

    Returns:
        True when every location of the top-level package lies inside ``site_packages``.
    """
    import importlib.util

    top = module.split(".", 1)[0]
    if not top or not top.isidentifier():
        return False
    try:
        spec = importlib.util.find_spec(top)
    except (ImportError, ValueError):
        return False
    if spec is None:
        return False
    locations = list(spec.submodule_search_locations or ())
    if spec.has_location and spec.origin:
        locations.append(spec.origin)
    try:
        folder = os.path.normcase(os.path.realpath(site_packages))
    except OSError:
        return False
    return bool(locations) and all(_inside(str(path), folder) for path in locations)
