"""Tests of WP1.4b: the default method flip, the noise estimator, the grid and the runner."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from prototype import run
from prototype.params import Params

# --- the default flip (spec v0.5.3 D16) ----------------------------------------------------------


def test_the_default_method_is_c3() -> None:
    assert Params().method == "c3"
    assert Params.neutral().method == "c3"


def test_run_without_a_method_follows_the_params_default(tmp_path: Path) -> None:
    source = tmp_path / "scene.png"
    rng = np.random.default_rng(0)
    Image.fromarray((rng.random((32, 48, 3)) * 255).astype(np.uint8)).save(source)
    out = tmp_path / "out"
    assert run.main(["--in", str(source), "--out", str(out)]) == 0
    assert sorted(path.name for path in out.iterdir()) == ["scene-c3.png"]


def test_run_help_names_c3_as_the_default_and_lists_the_options(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit):
        run.main(["--help"])
    text = " ".join(capsys.readouterr().out.split())
    assert "compensation method (default c3; ancuti2018, or ancuti2018 with --blue)" in text
    assert "(ancuti2018-blue)" in text
    assert "defaults to the :class:`Params` default, ``c3``" in (run.__doc__ or "")
