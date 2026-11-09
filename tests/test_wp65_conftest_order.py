"""WP6.5 QA fix: the conftest's GPU release runs AFTER the test's own patches are undone.

``tests/conftest.py``'s autouse ``_release_fft_plans`` registers a finalizer that reads
``clearwater.core.backend._probe_gpu.cache_info()`` once ``cupy`` is loaded. Teardown is
last-in, first-out, so that finalizer must be registered BEFORE the test's ``monkeypatch``
is set up; otherwise it runs while a test's replacement of ``_probe_gpu`` is still in place
(the regression at ``00e18e71``: ``_posix_home_redirect`` requested ``monkeypatch`` and so set
it up first, and ``test_portability_cpu_selection[P23]``'s lambda probe raised
``AttributeError`` at teardown whenever ``cupy`` was already imported).

Each class holds ONE test and a class-scoped sentinel fixture. Class scope sets the sentinel
up before every function-scoped fixture and tears it down after them, so its after-``yield``
check sees what the release did. Each sentinel installs ``cupy`` in ``sys.modules`` (a bare
stand-in module unless the real one is already loaded; nothing is imported and no device is
touched) so the release cannot return early.

- ``TestReleaseRunsAfterTheMonkeypatchUndo``: the sentinel installs a WITNESS probe; the test
  replaces it with a TRIPWIRE through its ``monkeypatch``. In the right order the undo puts
  the witness back and the release reads the witness's ``cache_info`` exactly once; in the
  wrong order the release reaches the tripwire, which raises.
- ``TestReleaseSkipsAProbeWithoutCacheInfo``: the sentinel installs a plain function as the
  probe (what a test's lambda looks like). The release must return without calling it and
  without raising (the ``getattr`` guard).
"""

from __future__ import annotations

import sys
import types
from collections.abc import Iterator
from typing import NamedTuple

import pytest

from clearwater.core import backend as core_backend


class _CacheInfo(NamedTuple):
    """The one field of ``functools`` cache info the release reads."""

    currsize: int


class _Witness:
    """A probe stand-in with ``cache_info``: counts reads and reports "never probed"."""

    def __init__(self) -> None:
        """Start with no reads."""
        self.reads = 0

    def __call__(self) -> tuple[None, str]:
        """Fail: the release must not probe after reading ``currsize == 0``."""
        raise AssertionError("the release probed the witness")

    def cache_info(self) -> _CacheInfo:
        """Record the read and report an empty cache."""
        self.reads += 1
        return _CacheInfo(currsize=0)


class _Tripwire:
    """The test's replacement probe; any use by the release means the order is wrong."""

    def __call__(self) -> tuple[None, str]:
        """Fail on a probe."""
        raise AssertionError("_release_fft_plans probed the test's patched _probe_gpu")

    def cache_info(self) -> _CacheInfo:
        """Fail on a read: the release ran before the test's monkeypatch undo."""
        raise AssertionError(
            "_release_fft_plans ran before the test's monkeypatch undo "
            "(it read the test's patched _probe_gpu)"
        )


def _install(patch: pytest.MonkeyPatch, probe: object) -> None:
    """Install ``probe`` as ``_probe_gpu`` and make sure ``cupy`` is in ``sys.modules``."""
    patch.setattr(core_backend, "_probe_gpu", probe)
    if "cupy" not in sys.modules:
        patch.setitem(sys.modules, "cupy", types.ModuleType("cupy"))


class TestReleaseRunsAfterTheMonkeypatchUndo:
    """The release's finalizer runs after the test's ``monkeypatch`` is undone."""

    @pytest.fixture(scope="class")
    def witness(self) -> Iterator[_Witness]:
        """Install the witness for the class; after the test, require exactly one read."""
        witness = _Witness()
        with pytest.MonkeyPatch.context() as patch:
            _install(patch, witness)
            yield witness
            assert witness.reads == 1, (
                f"the release read the restored probe {witness.reads} times, expected 1 "
                "(it ran before the monkeypatch undo, or not at all)"
            )

    def test_the_tests_patch_is_undone_before_the_release(
        self, witness: _Witness, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Replace the witness with a tripwire; teardown must undo it before the release."""
        tripwire = _Tripwire()
        monkeypatch.setattr(core_backend, "_probe_gpu", tripwire)
        assert core_backend._probe_gpu is tripwire
        assert witness.reads == 0


class TestReleaseSkipsAProbeWithoutCacheInfo:
    """The release returns, without probing, when ``_probe_gpu`` has no ``cache_info``."""

    @pytest.fixture(scope="class")
    def plain_probe_calls(self) -> Iterator[list[int]]:
        """Install a plain-function probe for the class; after the test, require no call."""
        calls: list[int] = []

        def plain_probe() -> tuple[None, str]:
            calls.append(1)
            return None, "plain probe"

        with pytest.MonkeyPatch.context() as patch:
            _install(patch, plain_probe)
            yield calls
            assert calls == [], "the release called a probe that has no cache_info"

    def test_a_replaced_probe_is_left_alone(self, plain_probe_calls: list[int]) -> None:
        """The probe in place at teardown is a plain function (no ``cache_info``)."""
        assert not hasattr(core_backend._probe_gpu, "cache_info")
        assert plain_probe_calls == []
