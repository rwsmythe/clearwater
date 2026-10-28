"""WP3.21, CHARC ruling (A): no test inherits an earlier test's cuFFT plans.

The FFT Gaussian keeps its plans in the calling thread's plan cache until
``CupyBackend.release_fft_plans``; ``tests/conftest.py``'s autouse fixture calls it after each
test. The two tests below run in file order on pytest's thread: the first leaves plans behind,
the second finds none. Without the fixture the second fails (the suite-level face: the prototype
bench's reserved-pool ratio after ``test_methods_assembly_v8.py``). Run alone, the second passes
trivially.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pytest

from clearwater.core import backend_for


def _gpu() -> Any:
    try:
        return backend_for("cuda:0")
    except Exception as error:  # no CuPy or no device
        pytest.skip(f"no GPU backend: {error}")


@pytest.mark.gpu
def test_a_test_may_leave_fft_plans_in_its_thread() -> None:
    gpu = _gpu()
    a = gpu.asarray(np.zeros((1080, 1920), dtype=np.float32))
    gpu.gaussian_blur(a, 54.0)  # the FFT route: plans cached on this thread
    assert gpu.xp.fft.config.get_plan_cache().get_curr_size() > 0


@pytest.mark.gpu
def test_the_next_test_starts_without_them() -> None:
    cache = _gpu().xp.fft.config.get_plan_cache()
    assert cache.get_curr_size() == 0 and cache.get_curr_memsize() == 0
