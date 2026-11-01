"""Pure, no-subprocess validation of the WP5.1 acceptance function addresses.

Import test modules and inspect functions without requesting their fixtures or
running their tests. Parameterized function addresses stand for all instances;
the final three-leg gate separately verifies expanded collection identity.
"""

from __future__ import annotations

import importlib
import inspect
import re
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path

import pytest

from acceptance_support import ACCEPTANCE_NODES, ACCEPTANCE_NON_NODE_REASONS, assert_names_only


def _assert_matrix(nodes: Mapping[str, Sequence[str]], reasons: Mapping[str, str]) -> None:
    tests_dir = Path(__file__).resolve().parent
    expected = {*(f"V{number}" for number in range(1, 19)), "N10", "D91"}
    assert set(nodes) == expected, "acceptance matrix must cover V1-V18, N10 and D91"
    assert set(reasons) == {key for key, addresses in nodes.items() if not addresses}, (
        "each acceptance row without an automated node needs its own reason"
    )
    assert all(reason.strip() for reason in reasons.values()), "empty non-node reason"
    for acceptance_id, addresses in nodes.items():
        assert len(set(addresses)) == len(addresses), f"duplicate node for {acceptance_id}"
        for address in addresses:
            message = f"stale acceptance node for {acceptance_id}: {address}"
            match = re.fullmatch(r"tests/(test_\w+)\.py::(test_\w+)", address)
            assert match is not None, message
            module_name, function_name = match.groups()
            try:
                module = importlib.import_module(module_name)
            except ModuleNotFoundError as exc:
                raise AssertionError(message) from exc
            module_file = getattr(module, "__file__", None)
            assert (
                module_file is not None
                and Path(module_file).resolve() == tests_dir / f"{module_name}.py"
            ), f"{message}: module file differs from the referenced test file"
            function = getattr(module, function_name, None)
            assert inspect.isfunction(function), message
            assert function.__module__ == module.__name__, message
            assert getattr(function, "__test__", True) is not False, message
            for marker in getattr(function, "pytestmark", ()):
                assert marker.name not in ("skip", "xfail"), (
                    f"{message}: unconditional skip/xfail mark {marker.name}"
                )


def test_acceptance_matrix_references_existing_test_functions(
    record_property: Callable[[str, object], None],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Require valid function addresses and an explicit reason for every empty row."""
    _assert_matrix(ACCEPTANCE_NODES, ACCEPTANCE_NON_NODE_REASONS)
    record_property("acceptance_ids", list(ACCEPTANCE_NODES))
    record_property("function_addresses", sum(map(len, ACCEPTANCE_NODES.values())))
    record_property("non_node_reasons", ACCEPTANCE_NON_NODE_REASONS)
    stale = "tests/test_v51_traceability.py::test_planted_stale_acceptance_node"
    wrong = {**ACCEPTANCE_NODES, "V1": (*ACCEPTANCE_NODES["V1"], stale)}
    with pytest.raises(AssertionError, match=re.escape(stale)):
        _assert_matrix(wrong, ACCEPTANCE_NON_NODE_REASONS)
    record_property("mutation_probe", f"stale node rejected by name: {stale}")
    module = importlib.import_module("test_methods_compensation")
    with monkeypatch.context() as patch:
        patch.setattr(module, "__file__", str(tmp_path / "test_methods_compensation.py"))
        with pytest.raises(
            AssertionError, match="module file differs from the referenced test file"
        ):
            _assert_matrix(ACCEPTANCE_NODES, ACCEPTANCE_NON_NODE_REASONS)
    record_property(
        "module_file_mutation_probe", "same-name module from a different folder rejected"
    )
    function_name = "test_ancuti_chain_matches_prototype"
    function = getattr(module, function_name)
    address = f"tests/test_methods_compensation.py::{function_name}"
    for marker in (
        pytest.mark.skip(reason="planted skip"),
        pytest.mark.xfail(reason="planted xfail"),
    ):
        with monkeypatch.context() as patch:
            patch.setattr(
                function, "pytestmark", [*getattr(function, "pytestmark", ()), marker.mark]
            )
            with pytest.raises(AssertionError, match=re.escape(address)):
                _assert_matrix(ACCEPTANCE_NODES, ACCEPTANCE_NON_NODE_REASONS)
    with monkeypatch.context() as patch:
        patch.setattr(function, "pytestmark", [pytest.mark.skipif(False, reason="available").mark])
        _assert_matrix(ACCEPTANCE_NODES, ACCEPTANCE_NON_NODE_REASONS)
    record_property("skip_mark_mutation_probe", "unconditional skip/xfail rejected by node name")
    for spelling in (r"video\hevc8.mp4", "fixtures/video/x.mp4"):
        for surface in (
            {"provenance": {"source": spelling}},
            {"source": spelling},
            f"Writing {spelling}",
        ):
            with pytest.raises(AssertionError, match="path leaked"):
                assert_names_only(surface)
    assert_names_only(["hevc8.mp4", "[1/40] Writing photo.png", "BT.709/limited"])
    record_property("relative_path_mutation_probe", "backslash and slash file paths rejected")
