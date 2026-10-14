"""Shared pytest configuration: skip footage-marked tests when no footage is configured."""

from __future__ import annotations

import pytest

from local_config import footage_available


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if footage_available():
        return
    skip = pytest.mark.skip(
        reason="footage folder not configured; copy clearwater.local.example.toml "
        "to clearwater.local.toml and set footage_path"
    )
    for item in items:
        if "footage" in item.keywords:
            item.add_marker(skip)
