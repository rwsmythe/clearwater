"""WP3.17 Basic and Advanced parameter panels (G3, D16, D17, D49, D52; DR-44 (b)).

Test methods declared here carry every IF-3 parameter type and the D49 shape (``c3`` has no caps,
``ancuti2018`` has them); one test imports the real schemas read-only to show one control each.
"""

# The shared fixture ``make_window`` is imported from gui_support and used as a parameter.
# ruff: noqa: F401, F811

from __future__ import annotations

import contextlib
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest
from PySide6.QtWidgets import QDoubleSpinBox, QLabel, QSpinBox

import gui_support
from clearwater.config import new_parameter_set
from clearwater.gui import Message, stub_engines
from clearwater.gui import parameter_panels as pp
from clearwater.gui.parameter_panels import (
    AdvancedPanel,
    BasicPanel,
    ParameterRow,
    float_decimals,
    float_step,
    install_parameter_panels,
)
from clearwater.interfaces import Parameter, ParameterSet
from gui_support import (
    ONE_STAGE,
    make_window,
    open_and_wait,
    photo_engines,
    presenter_of,
    wait_idle,
)

pytestmark = pytest.mark.gui


def param(
    name: str,
    type_: Any,
    default: Any,
    lo: float | None = None,
    hi: float | None = None,
    panel: Any = "basic",
    *,
    choices: tuple[str, ...] | None = None,
    nullable: bool = False,
    help_: str | None = None,
) -> Parameter:
    """A test parameter whose label is ``L-<name>`` and help ``H-<name>``."""
    return Parameter(
        name, type_, default, lo, hi, choices, panel, f"L-{name}",
        help_ if help_ is not None else f"H-{name}", default, nullable,
    )  # fmt: skip


ALL_TYPES = (
    param("gain", "float", 1.0, 0.0, 2.0),
    param("count", "int", 16, 1, 256),
    param("flag", "bool", False),
    param("mode", "enum", "b", choices=("a", "b", "c")),
    param("fine", "float", 0.001, 0.0001, 0.02, "advanced"),
    param("free_f", "float", 3.0, None, None, "advanced"),
    param("half_f", "float", 1.0, 0.0, None, "advanced"),
    param("free_i", "int", 7, None, None, "advanced"),
    param("cap", "float", 2.0, 0.0, 10.0, "advanced", nullable=True),
    param("opt_flag", "bool", False, None, None, "advanced", nullable=True),
    param("low", "float", 0.5, 0.0, 100.0, "advanced"),
    param("high", "float", 99.5, 0.0, 100.0, "advanced"),
)

C3_SHAPE = (
    param("white_balance_strength", "float", 1.0, 0.0, 1.0),
    param("kappa", "float", 1.0, 0.0, 3.0, "advanced"),
    param("big", "float", 1.0, 0.0, 5.0),
    param("level", "float", 0.5, 0.0, 1.0, "advanced"),
)
ANCUTI_SHAPE = (
    param("white_balance_strength", "float", 1.0, 0.0, 1.0),
    param("big", "float", 1.0, 0.0, 2.0),
    param("red_gain_cap", "float", 2.0, 0.0, 10.0, "advanced", nullable=True),
    param("blue_gain_cap", "float", 2.0, 0.0, 10.0, "advanced", nullable=True),
)


class SchemaMethod:
    """A test method with a given schema; ``render`` refuses ``low >= high`` when it has both."""

    def __init__(self, method_id: str, parameters: tuple[Parameter, ...], label: str = "") -> None:
        self.id = method_id
        self.label = label or f"Method {method_id}"
        self.parameters = parameters
        self.stages = ONE_STAGE

    def analyze(self, stage: str, image: Any, params: Mapping[str, Any], earlier: Any) -> Any:
        import numpy as np

        return {"mean": np.asarray(image.pixels).mean(axis=(0, 1))}

    def render(self, image: Any, params: Mapping[str, Any], statistics: Any) -> Any:
        low, high = params.get("low"), params.get("high")
        if low is not None and high is not None and not low < high:
            raise ValueError(f"low={low!r} must be below high={high!r}")
        return image

    def closed_form(self, stage: str, params: Any, earlier: Any, measured: Any) -> Any:
        return None


class NoDialogs:
    """Dialogs for a window that never uses the Presets panel."""

    def ask_name(self, title: str, initial: str) -> str | None:
        raise AssertionError("no dialog expected")

    def confirm(self, text: str) -> bool:
        raise AssertionError("no dialog expected")

    def open_file(self) -> Path | None:
        raise AssertionError("no dialog expected")

    def save_file(self, initial_name: str) -> Path | None:
        raise AssertionError("no dialog expected")


def two_methods() -> dict[str, Any]:
    """``c3`` first, then ``ancuti2018`` (D16, D49)."""
    return {
        "c3": SchemaMethod("c3", C3_SHAPE, "C3"),
        "ancuti2018": SchemaMethod("ancuti2018", ANCUTI_SHAPE, "Ancuti 2018"),
    }


def build(make_window, methods: Mapping[str, Any] | None = None):
    """A window with the panels installed; returns ``(window, basic, advanced)``."""
    window = make_window(stub_engines(methods=methods or {"all": SchemaMethod("all", ALL_TYPES)}))
    install_parameter_panels(window, dialogs=NoDialogs())
    basic = window.findChildren(BasicPanel)[0]
    advanced = window.findChildren(AdvancedPanel)[0]
    return window, basic, advanced


def changes(window) -> list[ParameterSet]:
    """Record every ``parameters_changed`` of the window."""
    seen: list[ParameterSet] = []
    window.session.parameters_changed.connect(seen.append)
    return seen


# Generation.


def test_one_control_per_parameter_in_its_own_panel_only(make_window) -> None:
    _, basic, advanced = build(make_window)
    assert list(basic.controls()) == ["gain", "count", "flag", "mode"]
    assert list(advanced.controls()) == [
        "fine", "free_f", "half_f", "free_i", "cap", "opt_flag", "low", "high",
    ]  # fmt: skip
    names = [p.name for p in ALL_TYPES]
    assert sorted(list(basic.controls()) + list(advanced.controls())) == sorted(names)


def test_label_and_tool_tip_come_from_the_schema(make_window) -> None:
    _, basic, advanced = build(make_window)
    for panel in (basic, advanced):
        for name, row in panel.controls().items():
            assert row.label.text() == f"L-{name}"
            assert row.label.toolTip() == f"H-{name}"
            assert row.toolTip() == f"H-{name}"
            for widget in (row.spin, row.slider, row.check, row.combo, row.on_box):
                if widget is not None:
                    assert widget.toolTip() == f"H-{name}"


def test_widget_kinds_follow_the_parameter_types(make_window) -> None:
    _, basic, advanced = build(make_window)
    rows = {**basic.controls(), **advanced.controls()}
    assert isinstance(rows["gain"].spin, QDoubleSpinBox) and rows["gain"].slider is not None
    assert isinstance(rows["count"].spin, QSpinBox) and rows["count"].slider is not None
    assert rows["flag"].check is not None and rows["flag"].spin is None
    assert rows["mode"].combo is not None
    assert [rows["mode"].combo.itemText(i) for i in range(3)] == ["a", "b", "c"]
    assert rows["free_f"].spin is not None and rows["free_f"].slider is None
    assert rows["half_f"].slider is None and rows["free_i"].slider is None
    assert rows["cap"].on_box is not None and rows["cap"].slider is not None
    assert rows["opt_flag"].on_box is not None and rows["opt_flag"].check is not None
    assert rows["gain"].on_box is None
    for row in rows.values():
        if row.spin is not None:
            assert not row.spin.keyboardTracking()


def test_empty_advanced_panel_shows_one_line(make_window) -> None:
    only_basic = (param("x", "float", 0.5, 0.0, 1.0),)
    _, basic, advanced = build(make_window, {"m": SchemaMethod("m", only_basic)})
    assert advanced.controls() == {}
    texts = [label.text() for label in advanced.findChildren(QLabel)]
    assert texts == ["This method has no advanced parameters."]
    assert list(basic.controls()) == ["x"]


def test_selector_lists_methods_in_mapping_order_and_selects_the_session_method(
    make_window,
) -> None:
    window, basic, _ = build(make_window, two_methods())
    selector = basic.selector
    assert [selector.itemText(i) for i in range(selector.count())] == ["C3", "Ancuti 2018"]
    assert [selector.itemData(i) for i in range(selector.count())] == ["c3", "ancuti2018"]
    assert selector.currentData() == window.session.parameters().method == "c3"


def test_the_real_schemas_get_one_control_per_parameter(make_window) -> None:
    # The only import of clearwater.methods in this package, read-only and in a test (the
    # dependency rule scans src/clearwater/gui).
    from clearwater.methods.schema import ANCUTI2018_PARAMETERS, C3_PARAMETERS

    methods = {
        "c3": SchemaMethod("c3", C3_PARAMETERS),
        "ancuti2018": SchemaMethod("ancuti2018", ANCUTI2018_PARAMETERS),
    }
    window, basic, advanced = build(make_window, methods)
    for method_id, schema in (("c3", C3_PARAMETERS), ("ancuti2018", ANCUTI2018_PARAMETERS)):
        if window.session.parameters().method != method_id:
            basic.selector.setCurrentIndex(basic.selector.findData(method_id))
        shown_basic, shown_advanced = list(basic.controls()), list(advanced.controls())
        assert shown_basic == [p.name for p in schema if p.panel == "basic"]
        assert shown_advanced == [p.name for p in schema if p.panel == "advanced"]
        rows = {**basic.controls(), **advanced.controls()}
        for parameter in schema:
            row = rows[parameter.name]
            assert row.label.text() == parameter.label
            assert row.shown() == parameter.default
            if parameter.type == "float":
                assert isinstance(row.spin, QDoubleSpinBox) and row.slider is not None
                assert row.spin.minimum() == parameter.minimum
                assert row.spin.maximum() == parameter.maximum
                assert row.spin.value() == pytest.approx(parameter.default)
            elif parameter.type == "int":
                assert isinstance(row.spin, QSpinBox) and row.slider is not None
            else:
                assert row.check is not None
            assert (row.on_box is not None) == parameter.nullable
    # blend_with_original is shown as declared: 0..100, nothing special-cased.
    blend = basic.controls().get("blend_with_original") or None
    if blend is None:
        basic.selector.setCurrentIndex(0)
        blend = basic.controls()["blend_with_original"]
    assert blend.label.text() == "Blend with original (%)"
    assert blend.spin is not None and blend.spin.maximum() == 100.0


# Ranges.


def test_float_decimals_step_and_slider_mapping(make_window) -> None:
    _, basic, advanced = build(make_window)
    gain = basic.controls()["gain"]
    assert gain.spin.minimum() == 0.0 and gain.spin.maximum() == 2.0
    assert gain.spin.decimals() == 3 and gain.spin.singleStep() == pytest.approx(0.01)
    assert gain.slider.minimum() == 0 and gain.slider.maximum() == pp.SLIDER_STEPS
    assert gain.slider.value() == 500 and gain.spin.value() == 1.0
    fine = advanced.controls()["fine"]
    assert fine.spin.decimals() >= 5  # 0.0001 and 0.001 must be exact
    assert fine.spin.value() == pytest.approx(0.001)
    low = advanced.controls()["low"]
    assert low.spin.decimals() == 2 and low.spin.singleStep() == pytest.approx(1.0)
    assert float_decimals(param("x", "float", 0.123456, 0.0, 1.0)) == 6
    assert float_step(param("x", "float", 1.0, 0.0, 100.0), 2) == pytest.approx(1.0)


def test_int_range_and_slider(make_window) -> None:
    _, basic, advanced = build(make_window)
    count = basic.controls()["count"]
    assert (count.spin.minimum(), count.spin.maximum()) == (1, 256)
    assert (count.slider.minimum(), count.slider.maximum()) == (1, 256)
    assert count.spin.value() == count.slider.value() == 16
    free = advanced.controls()["free_i"]
    assert free.slider is None and free.spin.value() == 7
    assert free.spin.minimum() < -(10**9) and free.spin.maximum() > 10**9


def test_one_sided_and_unbounded_floats_use_the_display_limit(make_window) -> None:
    _, _, advanced = build(make_window)
    half = advanced.controls()["half_f"]
    assert half.spin.minimum() == 0.0 and half.spin.maximum() == 1.0e9
    free = advanced.controls()["free_f"]
    assert (free.spin.minimum(), free.spin.maximum()) == (-1.0e9, 1.0e9)
    assert free.spin.decimals() >= 3 and free.spin.singleStep() == pytest.approx(0.1)


def test_no_committed_value_is_outside_the_schema(make_window) -> None:
    window, basic, _ = build(make_window)
    seen = changes(window)
    gain = basic.controls()["gain"]
    gain.slider.setValue(gain.slider.maximum())
    gain.slider.setValue(gain.slider.minimum())
    gain.spin.setValue(50.0)  # Qt clamps to the spin box range
    gain.spin.setValue(-50.0)
    for parameters in seen:
        assert 0.0 <= parameters.parameters["gain"] <= 2.0
    values = [p.parameters["gain"] for p in seen]
    assert values[0] == 2.0 and 0.0 in values
    count = basic.controls()["count"]
    count.spin.setValue(10**6)
    assert window.session.parameters().parameters["count"] == 256


# Live editing.


def test_an_edit_commits_once_with_exactly_the_edited_name_added(make_window) -> None:
    window, basic, _ = build(make_window)
    seen = changes(window)
    before = window.session.parameters()
    basic.controls()["gain"].spin.setValue(1.25)
    assert len(seen) == 1
    assert dict(seen[0].parameters) == {"gain": 1.25}  # the set stays partial (IF-9)
    assert seen[0].method == before.method
    assert seen[0].created == before.created and seen[0].app_version == before.app_version
    basic.controls()["flag"].check.setChecked(True)
    assert len(seen) == 2
    assert dict(seen[1].parameters) == {"gain": 1.25, "flag": True}
    assert type(seen[0].parameters["gain"]) is float


def test_a_slider_drag_commits_every_value(make_window) -> None:
    window, basic, _ = build(make_window)
    seen = changes(window)
    gain = basic.controls()["gain"]
    for position in (510, 520, 530, 540):
        gain.slider.setValue(position)
    assert [p.parameters["gain"] for p in seen] == pytest.approx([1.02, 1.04, 1.06, 1.08])
    assert gain.slider.value() == 540  # the echo does not move the slider
    count = basic.controls()["count"]
    count.slider.setValue(20)
    count.slider.setValue(21)
    assert [p.parameters["count"] for p in seen[-2:]] == [20, 21]
    assert type(seen[-1].parameters["count"]) is int
    assert count.spin.value() == 21


def test_a_typed_value_moves_the_slider(make_window) -> None:
    _, basic, _ = build(make_window)
    gain = basic.controls()["gain"]
    gain.spin.setValue(0.5)
    assert gain.slider.value() == 250


def _assert_external_update_does_not_commit(make_window) -> None:
    window, basic, advanced = build(make_window)
    seen = changes(window)
    window.session.set_parameters(
        new_parameter_set(
            "all", {"gain": 0.4, "count": 99, "flag": True, "mode": "c", "cap": None, "low": 10.0}
        )
    )
    assert len(seen) == 1, "the panels committed in answer to an external change"
    rows = {**basic.controls(), **advanced.controls()}
    assert rows["gain"].spin.value() == pytest.approx(0.4)
    assert rows["gain"].slider.value() == 200
    assert rows["count"].spin.value() == rows["count"].slider.value() == 99
    assert rows["flag"].check.isChecked() and rows["mode"].combo.currentText() == "c"
    assert not rows["cap"].on_box.isChecked() and not rows["cap"].spin.isEnabled()
    assert rows["low"].spin.value() == 10.0
    assert rows["fine"].spin.value() == pytest.approx(0.001)  # not named: the default


def test_an_external_set_parameters_updates_the_widgets_without_re_emitting(make_window) -> None:
    _assert_external_update_does_not_commit(make_window)


def test_planted_programmatic_update_that_re_emits_fails(make_window, monkeypatch) -> None:
    class NoBlocker:
        def __init__(self, widget: Any) -> None:
            pass

        def __enter__(self) -> None:
            return None

        def __exit__(self, *exc: Any) -> None:
            return None

    monkeypatch.setattr(pp, "QSignalBlocker", NoBlocker)
    with pytest.raises(AssertionError, match="external change"):
        _assert_external_update_does_not_commit(make_window)


def test_nullable_unchecked_is_none_and_checking_restores_the_value(make_window) -> None:
    window, _, advanced = build(make_window)
    seen = changes(window)
    cap = advanced.controls()["cap"]
    assert cap.on_box.isChecked() and cap.spin.isEnabled() and cap.shown() == 2.0
    cap.spin.setValue(4.0)
    cap.on_box.setChecked(False)
    assert seen[-1].parameters["cap"] is None
    assert not cap.spin.isEnabled() and not cap.slider.isEnabled() and cap.shown() is None
    cap.on_box.setChecked(True)
    assert seen[-1].parameters["cap"] == 4.0 and cap.spin.isEnabled()
    opt = advanced.controls()["opt_flag"]
    opt.on_box.setChecked(False)
    assert seen[-1].parameters["opt_flag"] is None and not opt.check.isEnabled()
    opt.on_box.setChecked(True)
    assert seen[-1].parameters["opt_flag"] is False


def test_a_none_default_gets_an_on_box_without_the_nullable_flag(make_window) -> None:
    schema = (param("limit", "float", None, 0.0, 5.0),)
    window, basic, _ = build(make_window, {"m": SchemaMethod("m", schema)})
    row = basic.controls()["limit"]
    assert row.on_box is not None and not row.on_box.isChecked() and row.shown() is None
    row.on_box.setChecked(True)
    assert window.session.parameters().parameters["limit"] == 0.0  # the minimum, no default


def test_enum_edit_commits_the_choice(make_window) -> None:
    window, basic, _ = build(make_window)
    seen = changes(window)
    basic.controls()["mode"].combo.setCurrentIndex(2)
    assert seen[-1].parameters["mode"] == "c"


# D49 and the method switch.


def test_switching_the_method_removes_and_restores_the_cap_controls(make_window) -> None:
    window, basic, advanced = build(make_window, two_methods())
    assert "red_gain_cap" not in advanced.controls() and "kappa" in advanced.controls()
    basic.selector.setCurrentIndex(basic.selector.findData("ancuti2018"))
    assert window.session.parameters().method == "ancuti2018"
    assert list(advanced.controls()) == ["red_gain_cap", "blue_gain_cap"]
    assert "kappa" not in advanced.controls()
    assert advanced.findChildren(ParameterRow) == list(advanced.controls().values())
    assert list(basic.controls()) == ["white_balance_strength", "big"]
    basic.selector.setCurrentIndex(basic.selector.findData("c3"))
    assert list(advanced.controls()) == ["kappa", "level"]
    assert advanced.findChildren(ParameterRow) == list(advanced.controls().values())


def _assert_switch_carries_only_valid_values(make_window) -> None:
    window, basic, advanced = build(make_window, two_methods())
    window.session.set_parameters(
        new_parameter_set(
            "c3", {"white_balance_strength": 0.3, "kappa": 2.5, "big": 4.0, "level": 0.2}
        )
    )
    basic.selector.setCurrentIndex(basic.selector.findData("ancuti2018"))
    carried = dict(window.session.parameters().parameters)
    # white_balance_strength exists in both; kappa and level do not; big = 4.0 > the new maximum 2.
    assert carried == {"white_balance_strength": 0.3}, carried
    assert basic.controls()["big"].shown() == 1.0  # the new method's default
    basic.selector.setCurrentIndex(basic.selector.findData("c3"))
    assert dict(window.session.parameters().parameters) == {"white_balance_strength": 0.3}
    assert basic.controls()["white_balance_strength"].shown() == pytest.approx(0.3)
    assert advanced.controls()["kappa"].shown() == 1.0


def test_the_switch_carries_over_only_values_valid_for_the_new_method(make_window) -> None:
    _assert_switch_carries_only_valid_values(make_window)


def test_planted_switch_without_validation_fails(make_window, monkeypatch) -> None:
    monkeypatch.setattr(pp, "validate_parameter_set", lambda *args, **kwargs: [])
    with pytest.raises(AssertionError, match="big"):
        _assert_switch_carries_only_valid_values(make_window)


def test_the_switch_creates_a_fresh_stamped_set(make_window) -> None:
    window, basic, _ = build(make_window, two_methods())
    before = window.session.parameters()
    basic.selector.setCurrentIndex(1)
    after = window.session.parameters()
    assert after.method == "ancuti2018" and after.created >= before.created


def test_an_external_method_change_rebuilds_both_panels_and_re_points_the_selector(
    make_window,
) -> None:
    window, basic, advanced = build(make_window, two_methods())
    seen = changes(window)
    window.session.set_parameters(new_parameter_set("ancuti2018", {"red_gain_cap": None}))
    assert len(seen) == 1  # the rebuild and the selector did not commit
    assert basic.selector.currentData() == "ancuti2018"
    assert list(advanced.controls()) == ["red_gain_cap", "blue_gain_cap"]
    assert advanced.controls()["red_gain_cap"].shown() is None
    assert advanced.controls()["blue_gain_cap"].shown() == 2.0


# Messages (DR-44 (b)).


def test_a_refused_set_becomes_an_error_with_the_panels_owner_cleared_by_the_next_success(
    make_window, monkeypatch
) -> None:
    window, basic, _ = build(make_window)
    presenter = presenter_of(window)
    presenter.present(Message("error", "preview broke", owner="shell.preview"))
    real = window.session.set_parameters
    monkeypatch.setattr(
        window.session, "set_parameters", lambda ps: (_ for _ in ()).throw(ValueError("no way"))
    )
    basic.controls()["gain"].spin.setValue(0.1)
    errors = [m for m in presenter.messages if m.owner == "parameters"]
    assert len(errors) == 1 and "no way" in errors[0].text and errors[0].severity == "error"
    monkeypatch.setattr(window.session, "set_parameters", real)
    basic.controls()["gain"].spin.setValue(0.2)
    assert [m for m in presenter.messages if m.owner == "parameters"] == []
    assert [m.text for m in presenter.messages] == ["preview broke"]  # another owner's survives


def test_a_relation_between_two_parameters_reaches_the_user_as_the_preview_error(
    make_window, qtbot
) -> None:
    # The schema cannot say low < high; the panel commits the value (the schema allows it) and
    # the method's render refuses the pair: the shell presents that as its own preview error.
    window = make_window(
        photo_engines(
            {Path("p.png"): gui_support.image(40, 60)},
            methods={"all": SchemaMethod("all", ALL_TYPES)},
        )
    )
    install_parameter_panels(window, dialogs=NoDialogs())
    advanced = window.findChildren(AdvancedPanel)[0]
    open_and_wait(qtbot, window, Path("p.png"))
    presenter = presenter_of(window)
    assert presenter.of("error") == []
    advanced.controls()["low"].spin.setValue(99.8)  # above high = 99.5
    wait_idle(qtbot, window)
    errors = presenter.of("error")
    assert [e.owner for e in errors] == ["shell.preview"]
    assert "must be below" in errors[0].text
    assert dict(window.session.parameters().parameters) == {"low": 99.8}  # committed, not undone
    advanced.controls()["low"].spin.setValue(1.0)
    wait_idle(qtbot, window)
    assert presenter.of("error") == []


def test_every_message_this_module_presents_has_an_owner(make_window, monkeypatch) -> None:
    window, basic, _ = build(make_window)
    presenter = presenter_of(window)
    monkeypatch.setattr(
        window.session, "set_parameters", lambda ps: (_ for _ in ()).throw(ValueError("x"))
    )
    basic.controls()["gain"].spin.setValue(0.1)
    assert presenter.messages and all(m.owner == "parameters" for m in presenter.messages)


# Round-1 regressions (Reviewer A, findings 4 and 6).


def test_int_bounds_beyond_the_spin_box_limit_are_clamped_both_ways(make_window) -> None:
    schema = (
        param("high", "int", 3_500_000_000, 3_000_000_000, 4_000_000_000),
        param("low", "int", -3_500_000_000, -4_000_000_000, -3_000_000_000),
    )
    _, basic, _ = build(make_window, {"m": SchemaMethod("m", schema)})
    for row in basic.controls().values():
        assert -(2**31 - 1) <= row.spin.minimum() <= row.spin.maximum() <= 2**31 - 1


def test_a_refused_edit_puts_the_session_value_back_in_the_control(
    make_window, monkeypatch
) -> None:
    window, basic, _ = build(make_window)
    monkeypatch.setattr(
        window.session, "set_parameters", lambda ps: (_ for _ in ()).throw(ValueError("no"))
    )
    gain = basic.controls()["gain"]
    gain.spin.setValue(0.1)
    assert gain.spin.value() == 1.0 and gain.slider.value() == 500 and gain.shown() == 1.0
    mode = basic.controls()["mode"]
    mode.combo.setCurrentIndex(2)
    assert mode.combo.currentText() == "b"


# Round-1 Reviewer B remediation.


def test_a_float_range_below_the_old_six_decimals_keeps_its_bounds_and_default(
    make_window,
) -> None:
    schema = (param("tiny", "float", 1.5e-7, 1e-7, 2e-7),)
    window, basic, _ = build(make_window, {"m": SchemaMethod("m", schema)})
    row = basic.controls()["tiny"]
    assert row.spin.minimum() == 1e-7 and row.spin.maximum() == 2e-7
    assert row.spin.value() == pytest.approx(1.5e-7, abs=1e-12)
    assert row.slider is not None and row.shown() == pytest.approx(1.5e-7, abs=1e-12)
    seen = changes(window)
    row.slider.setValue(row.slider.maximum())
    row.slider.setValue(row.slider.minimum())
    row.spin.setValue(2e-7)
    values = [p.parameters["tiny"] for p in seen]
    assert values[0] == 2e-7 and values[-1] == 2e-7  # the maximum is reachable
    assert all(1e-7 <= v <= 2e-7 for v in values) and 1e-7 in values


def test_a_range_too_narrow_to_resolve_gets_a_spin_box_alone_at_full_precision(
    make_window,
) -> None:
    hi = 1.0 + 1e-14
    schema = (param("narrow", "float", 1.0, 1.0, hi),)
    window, basic, _ = build(make_window, {"m": SchemaMethod("m", schema)})
    row = basic.controls()["narrow"]
    assert row.slider is None and row.spin.decimals() == 14
    assert float_decimals(schema[0]) == 14
    row.spin.setValue(hi)
    assert 1.0 <= window.session.parameters().parameters["narrow"] <= hi


def _assert_one_visible_row_per_parameter(make_window) -> None:
    _, basic, advanced = build(make_window)
    for panel, kind in ((basic, "basic"), (advanced, "advanced")):
        shown = [
            row.parameter.name for row in panel.findChildren(ParameterRow) if row.isVisibleTo(panel)
        ]
        assert shown == [p.name for p in ALL_TYPES if p.panel == kind], f"{kind}: {shown}"


def test_each_panel_shows_exactly_one_visible_row_per_parameter(make_window) -> None:
    _assert_one_visible_row_per_parameter(make_window)


def test_planted_basic_panel_that_adds_every_row_twice_fails(make_window, monkeypatch) -> None:
    original = pp.BasicPanel._rebuild

    def doubled(self: BasicPanel, method: Any) -> None:
        original(self, method)
        form = self._host.layout()
        for row in list(self._rows.values()):
            twin = ParameterRow(row.parameter, row.shown(), self._commit, self._host)
            form.addRow(twin.label, twin)

    monkeypatch.setattr(pp.BasicPanel, "_rebuild", doubled)
    with pytest.raises(AssertionError, match="basic"):
        _assert_one_visible_row_per_parameter(make_window)


# Round-2 Reviewer B adjudication (items 1, 2, 4).


@pytest.mark.parametrize(("lo", "hi"), [(0.0, 5e-324), (-1e308, 1e308)])
def test_extreme_finite_float_ranges_build_and_commit_inside_their_bounds(
    make_window, lo, hi
) -> None:
    schema = (param("extreme", "float", lo, lo, hi),)
    assert pp.float_has_slider(schema[0]) is False and float_decimals(schema[0]) >= 2
    window, basic, _ = build(make_window, {"m": SchemaMethod("m", schema)})
    row = basic.controls()["extreme"]
    assert row.slider is None
    seen = changes(window)
    row.spin.setValue(hi)
    row.spin.setValue(lo / 2)
    row.spin.setValue(hi / 3)
    assert all(lo <= p.parameters["extreme"] <= hi for p in seen)


def test_the_slider_ends_map_exactly_to_the_bounds(make_window) -> None:
    lo, hi = -424.66669714012824, -47.19110516014397
    schema = (param("odd", "float", -200.0, lo, hi),)
    window, basic, _ = build(make_window, {"m": SchemaMethod("m", schema)})
    row = basic.controls()["odd"]
    seen = changes(window)
    row.slider.setValue(pp.SLIDER_STEPS)
    row.slider.setValue(0)
    assert [p.parameters["odd"] for p in seen] == [hi, lo]


def test_a_successful_edit_in_the_other_panel_clears_the_shared_owners_error(
    make_window, monkeypatch
) -> None:
    window, basic, advanced = build(make_window)
    presenter = presenter_of(window)
    real = window.session.set_parameters
    monkeypatch.setattr(
        window.session, "set_parameters", lambda ps: (_ for _ in ()).throw(ValueError("no"))
    )
    basic.controls()["gain"].spin.setValue(0.1)
    assert [m.owner for m in presenter.messages] == ["parameters"]
    monkeypatch.setattr(window.session, "set_parameters", real)
    advanced.controls()["free_f"].spin.setValue(4.0)
    assert presenter.messages == []
