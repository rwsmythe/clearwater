"""WP4.1 task 4: the shell on ``default_engines()`` opens a real photo with the real method.

``default_engines()`` takes its photo reader and methods from the composition root, so a WP2.3
still opens through ``clearwater.io.photo`` and previews with ``c3`` (the default, D16); under
``force_cpu`` the status bar shows ``Device: CPU: forced`` (AD-9). Headless on ``offscreen``.
"""

# The shared fixture ``make_window`` is imported from gui_support and used as a parameter.
# ruff: noqa: F401, F811

from __future__ import annotations

import numpy as np
import pytest

from clearwater.gui.engines import default_engines
from clearwater.interfaces import Settings
from clearwater.io.photo import PhotoReader
from gui_support import make_window, open_and_wait, presenter_of, wait_idle

pytestmark = pytest.mark.gui


@pytest.mark.parametrize("sample_id", ["jpeg-gradient-srgb", "heic-ad24-both", "png16-lowred-srgb"])
def test_a_still_opens_through_default_engines(make_window, qtbot, sample, sample_id) -> None:
    engines = default_engines()
    assert list(engines.methods) == ["c3", "ancuti2018"]
    window = make_window(engines)
    window.session.set_settings(Settings(force_cpu=True))
    path = sample(sample_id)
    open_and_wait(qtbot, window, path)
    wait_idle(qtbot, window)
    assert window.file_label.text() == path.name
    assert window.size_label.text() == "96 x 64"
    assert window.device_label.text() == "Device: CPU: forced"
    assert presenter_of(window).of("refusal") == [] and presenter_of(window).of("error") == []
    shown = window.session.current_image()
    assert shown is not None
    expected, _ = PhotoReader().read(path)
    assert np.array_equal(np.asarray(shown.pixels), expected.pixels)  # the real reader's image
