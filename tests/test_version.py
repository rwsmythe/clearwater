"""Release version synchronization and real-export provenance checks (WP5.5, D91)."""

from __future__ import annotations

import json
import tomllib
from importlib.metadata import version
from pathlib import Path

from PIL import Image

import clearwater
from clearwater.app import composition
from clearwater.config import new_parameter_set
from clearwater.interfaces import Settings
from clearwater.interfaces.stubs import StubProgress
from clearwater.jobs.export_seam import ExportRequest


def test_release_version_is_1_1_0() -> None:
    """Pin the release advertised by the application to the approved version."""
    assert clearwater.__version__ == "1.1.0"


def test_release_version_matches_project_and_installed_metadata() -> None:
    """Catch a version bump that leaves project or installed metadata behind."""
    project = Path(__file__).resolve().parents[1] / "pyproject.toml"
    data = tomllib.loads(project.read_text(encoding="utf-8"))
    assert clearwater.__version__ == data["project"]["version"] == version("clearwater")


def test_photo_export_records_the_application_version(sample, tmp_path: Path) -> None:
    """Exercise the composition root's version wiring into PNG provenance.

    Args:
        sample: The shipped-fixture provider, copying the source under the test root.
        tmp_path: The isolated folder for the exported PNG.
    """
    out = tmp_path / "out"
    out.mkdir()
    request = ExportRequest(
        sample("jpeg-gradient-srgb"),
        "photo",
        new_parameter_set("c3", {}),
        Settings(output_folder=out, force_cpu=True, provenance=True),
    )
    result = composition.export_jobs().job(request)(StubProgress())
    assert result.ok, result.failure
    with Image.open(result.outputs[0]) as image:
        record = json.loads(image.info["clearwater-provenance"])
    assert record["app_version"] == clearwater.__version__
