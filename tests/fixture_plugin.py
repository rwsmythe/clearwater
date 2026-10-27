"""Pytest fixtures that give Phase 3 tests the shared samples (WP2.3 item 6).

Loaded by the one ``pytest_plugins`` statement in ``tests/conftest.py``. The statement is
``["fixture_plugin"] if Path(__file__).with_name("fixture_plugin.py").is_file() else []`` and not
the bare list because the WP-T1 guard tests (``tests/test_conftest_guard.py``) copy
``conftest.py`` alone into a miniature repository, where a bare
``pytest_plugins = ["fixture_plugin"]`` makes pytest fail to start.

- ``fixture_manifest``: the parsed, validated ``tests/fixtures/manifest.json``.
- ``sample``: a callable ``sample(sample_id) -> Path``. A committed sample is returned from
  ``tests/fixtures``. A generated one (the AD-14 flicker clip, too large to commit) is returned
  from ``work/fixtures/generated`` (the working-folder cache), generated first when it is absent
  or stale, and its decoded frames are hashed against the manifest before it is handed out; a
  mismatch after regeneration fails the test. If ``work/`` cannot be written the clip is made
  under pytest's basetemp instead. FFmpeg being absent skips the test with a reason.
- ``sample_entry``: a callable ``sample_entry(sample_id) -> dict`` giving the manifest entry.
- ``sample_ids``: a callable ``sample_ids(group=None) -> list[str]``.
- ``ffmpeg_tools``: skips the test with a reason when ``ffmpeg``/``ffprobe`` are not on the PATH.

Nothing here reads the footage folder or any local configuration.
"""

from __future__ import annotations

import json
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from fixtures import flicker, generate, manifest, video

REPO_ROOT = Path(__file__).resolve().parent.parent
"""The repository root (this file is ``tests/fixture_plugin.py``)."""

FIXTURES_DIR = REPO_ROOT / "tests" / "fixtures"
"""The committed samples and ``manifest.json``."""

GENERATED_DIR = REPO_ROOT / "work" / "fixtures" / "generated"
"""The cache of generated samples (``work/`` is the gitignored working folder)."""

SKIP_NO_FFMPEG = "ffmpeg and ffprobe are not on the PATH (needed to generate or probe video)"
"""The skip reason when FFmpeg is absent."""


def load_manifest(root: Path = FIXTURES_DIR) -> dict[str, Any]:
    """Load and validate the manifest of a fixtures folder.

    Args:
        root: The folder holding ``manifest.json``.

    Returns:
        The manifest.

    Raises:
        pytest.fail.Exception: The manifest is missing, unparseable or invalid.
    """
    try:
        data = json.loads((root / "manifest.json").read_text(encoding="ascii"))
    except (OSError, ValueError) as error:
        pytest.fail(f"cannot read {root / 'manifest.json'}: {error}", pytrace=False)
    problems = manifest.validate(data)
    if problems:
        pytest.fail("fixtures manifest is invalid: " + "; ".join(problems), pytrace=False)
    result: dict[str, Any] = data
    return result


def writable_dir(path: Path) -> bool:
    """Return True when ``path`` exists (or can be made) and a file can be written in it.

    ``mkdir(exist_ok=True)`` succeeds on a read-only folder, so a probe file is written and
    removed as well.
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=path):
            pass
    except OSError:
        return False
    return True


def verify_generated(entry: dict[str, Any], path: Path) -> str | None:
    """Check a generated sample's stream identity and decoded frames against the manifest.

    The identity is the container, codec, pixel format, size, frame rates, time base, the hash
    of the packet pts list and ffprobe's complaints (:data:`flicker.STREAM_IDENTITY`), plus the
    packet durations against the declared rate (:func:`flicker.identity_problems`); the frames
    are the decoded frame count and their SHA-256. The same frames remuxed at another rate fail
    the first check.

    Args:
        entry: The sample's manifest entry (the flicker clip).
        path: The file to check.

    Returns:
        None when the clip is the manifest's clip; otherwise what is wrong.
    """
    if not path.is_file():
        return f"{path} does not exist"
    design = entry["facts"]["design"]
    recorded = entry["facts"]["stream"]
    try:
        differ = flicker.identity_problems(path, recorded)
    except (video.GenerationError, KeyError, StopIteration, ValueError, ZeroDivisionError) as error:
        return f"{path.name}: cannot probe the stream ({error!r})"
    if differ:
        return f"{path.name}: " + "; ".join(differ)
    try:
        count, digest = flicker.decode_sha256(path)
    except video.GenerationError as error:
        return str(error)
    if count != design["frames"] or digest != design["frames_rgb24_sha256"]:
        return (
            f"{path.name}: {count} frames decode to {digest}, "
            f"the manifest has {design['frames']} frames and {design['frames_rgb24_sha256']}"
        )
    return None


class SampleProvider:
    """Hands out sample files from a manifest, generating the large ones on demand.

    Attributes:
        manifest: The validated manifest.
        fixtures_dir: Where the committed samples are.
        generated_dir: Where generated samples are cached.
        scratch: Makes a throwaway folder for the committed side of a regeneration.
    """

    def __init__(
        self,
        data: dict[str, Any],
        fixtures_dir: Path,
        generated_dir: Path,
        scratch: Callable[[], Path],
    ) -> None:
        """Index the manifest."""
        self.manifest = data
        self.fixtures_dir = fixtures_dir
        self.generated_dir = generated_dir
        self.scratch = scratch
        self._by_id = {item["id"]: item for item in data["samples"]}
        self._ready: dict[str, Path] = {}

    def entry(self, sample_id: str) -> dict[str, Any]:
        """Return the manifest entry of a sample, failing the test when there is none."""
        if sample_id not in self._by_id:
            pytest.fail(f"no sample {sample_id!r} in the fixtures manifest", pytrace=False)
        entry: dict[str, Any] = self._by_id[sample_id]
        return entry

    def ids(self, group: str | None = None) -> list[str]:
        """Return the ids of a group, or of every sample."""
        return [
            item["id"]
            for item in self.manifest["samples"]
            if group is None or item["group"] == group
        ]

    def path(self, sample_id: str) -> Path:
        """Return the file of a sample.

        A committed sample is returned as it is. A generated sample is verified on its first use
        in the session, a cache hit included (stream identity and decoded frames against the
        manifest), and regenerated into the cache when absent or stale.

        Args:
            sample_id: The manifest id.

        Returns:
            The file.

        Raises:
            pytest.skip.Exception: The sample must be generated or probed and FFmpeg is absent.
            pytest.fail.Exception: A committed file is missing, or a regenerated one still does
                not match the manifest.
        """
        if sample_id in self._ready:
            return self._ready[sample_id]
        entry = self.entry(sample_id)
        if entry["storage"] == "committed":
            path = self.fixtures_dir / entry["path"]
            if not path.is_file():
                pytest.fail(f"committed sample {sample_id!r} is missing: {path}", pytrace=False)
        else:
            if not video.tools_available():
                pytest.skip(SKIP_NO_FFMPEG)
            path = self.generated_dir / entry["path"]
            if verify_generated(entry, path) is not None:
                generate.generate(self.scratch(), self.generated_dir, [entry["group"]])
                problem = verify_generated(entry, path)
                if problem is not None:
                    pytest.fail(
                        f"regenerated sample {sample_id!r} does not match the manifest: {problem}",
                        pytrace=False,
                    )
        self._ready[sample_id] = path
        return path


@pytest.fixture(scope="session")
def fixture_manifest() -> dict[str, Any]:
    """The validated fixtures manifest."""
    return load_manifest()


@pytest.fixture(scope="session")
def ffmpeg_tools() -> None:
    """Skip the requesting test when FFmpeg is not available."""
    if not video.tools_available():
        pytest.skip(SKIP_NO_FFMPEG)


@pytest.fixture(scope="session")
def sample_provider(
    fixture_manifest: dict[str, Any], tmp_path_factory: pytest.TempPathFactory
) -> SampleProvider:
    """The session's :class:`SampleProvider` (cache in ``work/``, basetemp if that fails)."""
    cache = GENERATED_DIR
    if not writable_dir(cache):
        cache = tmp_path_factory.getbasetemp() / "fixtures-generated"
    return SampleProvider(
        fixture_manifest,
        FIXTURES_DIR,
        cache,
        lambda: tmp_path_factory.mktemp("fixtures-committed"),
    )


@pytest.fixture(scope="session")
def sample(sample_provider: SampleProvider) -> Callable[[str], Path]:
    """Return ``sample(sample_id) -> Path``: the file of a sample, generated when needed."""
    return sample_provider.path


@pytest.fixture(scope="session")
def sample_entry(sample_provider: SampleProvider) -> Callable[[str], dict[str, Any]]:
    """Return ``sample_entry(sample_id)``: the manifest entry of a sample."""
    return sample_provider.entry


@pytest.fixture(scope="session")
def sample_ids(sample_provider: SampleProvider) -> Callable[..., list[str]]:
    """Return ``sample_ids(group=None)``: the ids of a group (or of every sample)."""
    return sample_provider.ids
