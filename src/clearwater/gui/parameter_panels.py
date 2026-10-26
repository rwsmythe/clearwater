"""The Basic and Advanced parameter panels (WP3.17, G3, D17, D49, D52).

Both panels are generated from the selected method's IF-3 parameter schema alone, so the GUI stays
method-agnostic (spec 10.1): a ``float`` or ``int`` is a spin box (plus a slider when both bounds
are set), a ``bool`` a check box, an ``enum`` a combo box, and a ``nullable`` parameter (or one
whose default is None) gets a leading "On" check box whose unchecked state is None (a disabled gain
cap, D52). A user edit is committed at once through ``Session.set_parameters`` (the preview is
latest-wins, so a slider drag commits every value); a change that comes from outside the panel
(a loaded preset, another panel) updates the widgets with their signals blocked, so a programmatic
change never commits. The Basic panel starts with the method selector; switching the method
rebuilds both panels from the new method's schema, so the controls of the old method (the gain
caps of ``ancuti2018``, D49) are gone.

Only the schema's own range is ever committed: a spin box is limited to ``[minimum, maximum]``
and a committed number is clamped to it. A relation between two parameters (such as
``normalisation_low < normalisation_high``) is not part of the schema, so the panels cannot see
it: the method refuses such a pair when it renders and the shell presents that as its preview
error (``shell.preview``). Every message these panels present carries the owner
:data:`OWNER_PARAMETERS`.
"""

from __future__ import annotations

import dataclasses
import math
from collections.abc import Callable
from contextlib import ExitStack
from functools import partial
from typing import Literal

from PySide6.QtCore import QSignalBlocker, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from clearwater.config import new_parameter_set
from clearwater.interfaces import (
    CorrectionMethod,
    Parameter,
    ParameterSet,
    ParameterValue,
    validate_parameter_set,
)

from .contract import Area, Message, ShellContext, ShellWindow
from .messages import ascii_text
from .preset_panel import PresetDialogs, preset_panel

OWNER_PARAMETERS = "parameters"
"""The :attr:`Message.owner` of every message these panels present."""

SLIDER_STEPS = 1000
"""The number of steps of a float slider (position 0 is the minimum, this is the maximum)."""

_FLOAT_LIMIT = 1.0e9
"""The display limit of a float with no bound on one side."""

_INT_LIMIT = 2**31 - 1
"""The limit of a ``QSpinBox`` (and so of an int with no bound on one side)."""

_MIN_DECIMALS = 2
_MAX_DECIMALS = 6
_NONE = object()
"""A value no parameter can have: ``_shown`` before the first :meth:`ParameterRow.show`."""


def _digits(number: float | None) -> int:
    """Return how many decimals (at most 6) ``number`` needs to be shown exactly."""
    if number is None:
        return 0
    text = f"{float(number):.{_MAX_DECIMALS}f}".rstrip("0")
    return len(text.split(".")[1]) if "." in text else 0


def float_decimals(parameter: Parameter) -> int:
    """Return the spin box decimals of a ``float`` parameter.

    With both bounds: enough decimals that the slider's 1000 steps are distinct values, and enough
    to show the default and both bounds exactly. With fewer bounds: enough for the default.
    Always between 2 and 6 (3 and 6 when unbounded).

    Args:
        parameter: A ``float`` parameter.

    Returns:
        The number of decimals.
    """
    default = parameter.default if isinstance(parameter.default, int | float) else None
    lo, hi = parameter.minimum, parameter.maximum
    if lo is not None and hi is not None and hi > lo:
        need = math.ceil(-math.log10((hi - lo) / SLIDER_STEPS))
        decimals = max(need, _digits(default), _digits(lo), _digits(hi), _MIN_DECIMALS)
    else:
        decimals = max(3, _digits(default), _digits(lo), _digits(hi))
    return min(decimals, _MAX_DECIMALS)


def float_step(parameter: Parameter, decimals: int) -> float:
    """Return the spin box single step of a ``float`` parameter.

    With both bounds: a power of ten near 1/100 of the span. Otherwise a power of ten one below
    the default's magnitude (0.1 for a zero or missing default). Never below one unit of the
    last decimal.

    Args:
        parameter: A ``float`` parameter.
        decimals: The decimals chosen by :func:`float_decimals`.

    Returns:
        The step.
    """
    lo, hi = parameter.minimum, parameter.maximum
    if lo is not None and hi is not None and hi > lo:
        step = 10.0 ** round(math.log10((hi - lo) / 100))
    elif isinstance(parameter.default, int | float) and parameter.default != 0:
        step = 10.0 ** (math.floor(math.log10(abs(parameter.default))) - 1)
    else:
        step = 0.1
    return max(step, 10.0**-decimals)


def _fallback(parameter: Parameter) -> ParameterValue:
    """Return what a value widget shows while the parameter is None (its default, else a floor)."""
    if parameter.default is not None:
        return parameter.default
    if parameter.type == "bool":
        return False
    if parameter.type == "enum":
        return parameter.choices[0] if parameter.choices else None
    if parameter.minimum is not None:
        return parameter.minimum if parameter.type == "float" else math.ceil(parameter.minimum)
    return 0.0 if parameter.type == "float" else 0


class ParameterRow(QWidget):
    """The widgets of one parameter: a label and a field (a QWidget holding the controls).

    Attributes:
        parameter: The schema entry.
        label: The row's label widget (text and tool tip from the schema).
        on_box: The leading "On" check box of a nullable parameter, else None.
        spin: The ``QDoubleSpinBox`` / ``QSpinBox`` of a number, else None.
        slider: The slider of a number with both bounds, else None.
        check: The check box of a ``bool``, else None.
        combo: The combo box of an ``enum``, else None.
    """

    def __init__(
        self,
        parameter: Parameter,
        value: ParameterValue,
        commit: Callable[[str, ParameterValue], None],
        parent: QWidget | None = None,
    ) -> None:
        """Create the row showing ``value``.

        Args:
            parameter: The schema entry.
            value: The value to show now (None = off, for a nullable parameter).
            commit: Called as ``commit(name, value)`` when the user changes the value.
            parent: The Qt parent.
        """
        super().__init__(parent)
        self.parameter = parameter
        self._commit = commit
        self._shown: object = _NONE
        self._nullable = parameter.nullable or parameter.default is None
        self.label = QLabel(parameter.label)
        self.on_box: QCheckBox | None = None
        self.spin: QDoubleSpinBox | QSpinBox | None = None
        self.slider: QSlider | None = None
        self.check: QCheckBox | None = None
        self.combo: QComboBox | None = None
        self._value_widgets: list[QWidget] = []
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        if self._nullable:
            self.on_box = QCheckBox("On")
            layout.addWidget(self.on_box)
            self.on_box.toggled.connect(self._on_toggled)
        if parameter.type == "float":
            self._build_float(layout)
        elif parameter.type == "int":
            self._build_int(layout)
        elif parameter.type == "bool":
            self.check = QCheckBox()
            self.check.toggled.connect(self._on_check)
            layout.addWidget(self.check)
            self._value_widgets.append(self.check)
        else:
            self._build_enum(layout)
        for widget in (
            self.label,
            self,
            *self._value_widgets,
            *([self.on_box] if self.on_box else []),
        ):
            widget.setToolTip(parameter.help)
        self._set_widgets(_fallback(parameter))
        self.show_value(value)

    # Construction.

    def _build_float(self, layout: QHBoxLayout) -> None:
        """Add the spin box (and the slider when both bounds are set) of a ``float``."""
        parameter = self.parameter
        lo, hi = parameter.minimum, parameter.maximum
        spin = QDoubleSpinBox()
        spin.setKeyboardTracking(False)
        decimals = float_decimals(parameter)
        spin.setDecimals(decimals)
        spin.setRange(-_FLOAT_LIMIT if lo is None else lo, _FLOAT_LIMIT if hi is None else hi)
        spin.setSingleStep(float_step(parameter, decimals))
        spin.valueChanged.connect(self._on_spin)
        self.spin = spin
        layout.addWidget(spin)
        self._value_widgets.append(spin)
        if lo is not None and hi is not None and hi > lo:
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(0, SLIDER_STEPS)
            slider.setSingleStep(1)
            slider.setPageStep(SLIDER_STEPS // 20)
            slider.valueChanged.connect(self._on_slider)
            self.slider = slider
            layout.addWidget(slider, 1)
            self._value_widgets.append(slider)

    def _build_int(self, layout: QHBoxLayout) -> None:
        """Add the spin box (and the slider when both bounds are set) of an ``int``."""
        parameter = self.parameter
        lo = (
            -_INT_LIMIT
            if parameter.minimum is None
            else min(_INT_LIMIT, max(-_INT_LIMIT, math.ceil(parameter.minimum)))
        )
        hi = (
            _INT_LIMIT
            if parameter.maximum is None
            else max(-_INT_LIMIT, min(_INT_LIMIT, math.floor(parameter.maximum)))
        )
        spin = QSpinBox()
        spin.setKeyboardTracking(False)
        spin.setRange(lo, hi)
        spin.setSingleStep(1)
        spin.valueChanged.connect(self._on_spin)
        self.spin = spin
        layout.addWidget(spin)
        self._value_widgets.append(spin)
        if parameter.minimum is not None and parameter.maximum is not None and hi > lo:
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(lo, hi)
            slider.setSingleStep(1)
            slider.setPageStep(max(1, (hi - lo) // 10))
            slider.valueChanged.connect(self._on_slider)
            self.slider = slider
            layout.addWidget(slider, 1)
            self._value_widgets.append(slider)

    def _build_enum(self, layout: QHBoxLayout) -> None:
        """Add the combo box of an ``enum``."""
        combo = QComboBox()
        choices = self.parameter.choices or ()
        combo.addItems(list(choices))
        combo.setEnabled(bool(choices))
        combo.currentIndexChanged.connect(self._on_combo)
        self.combo = combo
        layout.addWidget(combo)
        self._value_widgets.append(combo)

    # What the user does.

    def _emit(self, value: ParameterValue) -> None:
        """Remember ``value`` as shown and commit it."""
        self._shown = value
        self._commit(self.parameter.name, value)

    def _clamped(self, number: float) -> float | int:
        """Return ``number`` limited to the schema's range, as the parameter's type."""
        parameter = self.parameter
        if parameter.minimum is not None:
            number = max(number, parameter.minimum)
        if parameter.maximum is not None:
            number = min(number, parameter.maximum)
        return int(number) if parameter.type == "int" else float(number)

    def _on_spin(self, number: float) -> None:
        """A number was entered: move the slider to it and commit."""
        self._sync_slider(number)
        self._emit(self._clamped(number))

    def _on_slider(self, position: int) -> None:
        """The slider moved: show its value in the spin box (rounded there) and commit."""
        spin = self.spin
        assert spin is not None
        with QSignalBlocker(spin):
            self._set_spin(self._slider_value(position))
        self._emit(self._clamped(spin.value()))

    def _on_check(self, checked: bool) -> None:
        """The ``bool`` check box was toggled."""
        self._emit(bool(checked))

    def _on_combo(self, index: int) -> None:
        """Another ``enum`` choice was picked."""
        if index >= 0 and self.combo is not None:
            self._emit(self.combo.itemText(index))

    def _on_toggled(self, checked: bool) -> None:
        """The "On" box was toggled: None when off, else the value widgets' value."""
        for widget in self._value_widgets:
            widget.setEnabled(checked)
        self._emit(self._widget_value() if checked else None)

    # Mapping between the slider and the value.

    def _slider_value(self, position: int) -> float:
        """Return the value at slider ``position``."""
        if self.parameter.type == "int":
            return float(position)
        lo, hi = self.parameter.minimum, self.parameter.maximum
        assert lo is not None and hi is not None
        return lo + position * (hi - lo) / SLIDER_STEPS

    def _slider_position(self, number: float) -> int:
        """Return the slider position nearest to ``number``."""
        if self.parameter.type == "int":
            return round(number)
        lo, hi = self.parameter.minimum, self.parameter.maximum
        assert lo is not None and hi is not None
        return round((number - lo) / (hi - lo) * SLIDER_STEPS)

    def _sync_slider(self, number: float) -> None:
        """Put the slider at ``number`` without a signal."""
        if self.slider is not None:
            with QSignalBlocker(self.slider):
                position = self._slider_position(number)
                self.slider.setValue(
                    max(self.slider.minimum(), min(self.slider.maximum(), position))
                )

    # What the program does.

    def _set_spin(self, number: float) -> None:
        """Show ``number`` in the spin box (rounded to its decimals or to a whole number)."""
        spin = self.spin
        if isinstance(spin, QDoubleSpinBox):
            spin.setValue(float(number))
        elif spin is not None:
            spin.setValue(max(spin.minimum(), min(spin.maximum(), round(number))))

    def _widget_value(self) -> ParameterValue:
        """Return the value the value widgets hold (even while they are disabled)."""
        if self.spin is not None:
            return self._clamped(self.spin.value())
        if self.check is not None:
            return self.check.isChecked()
        if self.combo is not None and self.combo.count():
            return self.combo.currentText()
        return self.parameter.default

    def _set_widgets(self, value: ParameterValue) -> None:
        """Show ``value`` in the value widgets with their signals blocked; None is ignored."""
        with ExitStack() as stack:
            for widget in self._value_widgets:
                stack.enter_context(QSignalBlocker(widget))
            if value is None:
                return
            if (
                self.spin is not None
                and isinstance(value, int | float)
                and not isinstance(value, bool)
            ):
                self._set_spin(value)
                self._sync_slider(value)
            elif self.check is not None and isinstance(value, bool):
                self.check.setChecked(value)
            elif self.combo is not None and isinstance(value, str):
                index = self.combo.findText(value)
                if index >= 0:
                    self.combo.setCurrentIndex(index)

    def show_value(self, value: ParameterValue) -> None:
        """Show ``value`` without committing it (a change that came from outside the panel).

        Does nothing when ``value`` is already what the row shows, so the value a user just
        committed, coming back through ``parameters_changed``, does not move the widget.

        Args:
            value: The value (None = off, for a nullable parameter).
        """
        if type(value) is type(self._shown) and value == self._shown:
            return
        self._shown = value
        if self.on_box is not None:
            with QSignalBlocker(self.on_box):
                self.on_box.setChecked(value is not None)
        enabled = value is not None or self.on_box is None
        for widget in self._value_widgets:
            widget.setEnabled(enabled)
        if self.combo is not None and not self.combo.count():
            self.combo.setEnabled(False)
        self._set_widgets(value)

    def shown(self) -> ParameterValue:
        """Return the value the row shows now (None = off)."""
        if self.on_box is not None and not self.on_box.isChecked():
            return None
        return self._widget_value()


class _ParameterForm(QWidget):
    """The common part of the Basic and Advanced panels: the rows of one panel."""

    def __init__(self, context: ShellContext, panel: Literal["basic", "advanced"]) -> None:
        """Create the panel and build its rows from the session's method."""
        super().__init__()
        self._context = context
        self._session = context.session
        self._panel = panel
        self._method_id: str | None = None
        self._rows: dict[str, ParameterRow] = {}
        self._presented = False
        self._layout = QVBoxLayout(self)
        self._header = QVBoxLayout()
        self._layout.addLayout(self._header)
        self._host = QWidget()
        self._layout.addWidget(self._host)
        self._layout.addStretch(1)
        self._add_header()
        self._rebuild(self._session.method())
        self._session.parameters_changed.connect(self._on_parameters_changed)

    def _add_header(self) -> None:
        """Add the widgets above the rows (the Basic panel's method selector)."""

    def _update_header(self, parameters: ParameterSet) -> None:
        """Re-point the header widgets at ``parameters``."""

    def controls(self) -> dict[str, ParameterRow]:
        """Return the rows by parameter name, in declaration order (for tests and WP4.3)."""
        return dict(self._rows)

    def _rebuild(self, method: CorrectionMethod) -> None:
        """Replace every row by the rows of ``method``'s parameters of this panel."""
        old = self._host
        self._layout.removeWidget(old)
        old.setParent(None)
        old.deleteLater()
        self._host = QWidget()
        self._layout.insertWidget(self._layout.count() - 1, self._host)
        form = QFormLayout(self._host)
        form.setContentsMargins(0, 0, 0, 0)
        self._rows = {}
        self._method_id = method.id
        values = self._session.parameters().parameters
        for parameter in method.parameters:
            if parameter.panel != self._panel:
                continue
            row = ParameterRow(
                parameter, values.get(parameter.name, parameter.default), self._commit, self._host
            )
            self._rows[parameter.name] = row
            form.addRow(row.label, row)
        if not self._rows:
            form.addRow(QLabel(f"This method has no {self._panel} parameters."))

    def _on_parameters_changed(self, parameters: ParameterSet) -> None:
        """Rebuild when the method changed, else show the new values; never commits."""
        self._update_header(parameters)
        method = self._session.method()
        if method.id != self._method_id:
            self._rebuild(method)
            return
        for name, row in self._rows.items():
            row.show_value(parameters.parameters.get(name, row.parameter.default))

    def _commit(self, name: str, value: ParameterValue) -> None:
        """Set one parameter on the session, keeping every other name as it is."""
        current = self._session.parameters()
        self._apply(dataclasses.replace(current, parameters={**current.parameters, name: value}))

    def _apply(self, parameters: ParameterSet) -> None:
        """Give the session ``parameters``; a refusal becomes an error message."""
        try:
            self._session.set_parameters(parameters)
        except ValueError as error:
            self._presented = True
            self._context.messages.present(
                Message(
                    "error",
                    ascii_text(f"The parameters were not changed: {error}"),
                    owner=OWNER_PARAMETERS,
                )
            )
        else:
            if self._presented:
                self._presented = False
                self._context.messages.clear("error", owner=OWNER_PARAMETERS)


class BasicPanel(_ParameterForm):
    """The Basic panel: the method selector and the method's Basic parameters (G3, D16)."""

    def __init__(self, context: ShellContext) -> None:
        """Create the panel.

        Args:
            context: The shell context.
        """
        self.selector: QComboBox
        super().__init__(context, "basic")

    def _add_header(self) -> None:
        """Add the method selector, listing the methods in ``engines.methods`` order."""
        self.selector = QComboBox()
        for method_id, method in self._context.engines.methods.items():
            self.selector.addItem(method.label, method_id)
        self._update_header(self._session.parameters())
        self.selector.currentIndexChanged.connect(self._on_selected)
        form = QFormLayout()
        form.addRow("Method", self.selector)
        self._header.addLayout(form)

    def _update_header(self, parameters: ParameterSet) -> None:
        """Point the selector at ``parameters.method`` without a signal."""
        index = self.selector.findData(parameters.method)
        if index >= 0 and index != self.selector.currentIndex():
            with QSignalBlocker(self.selector):
                self.selector.setCurrentIndex(index)

    def _on_selected(self, index: int) -> None:
        """Switch the method, carrying over each value that is valid for the new schema."""
        method_id = self.selector.itemData(index)
        current = self._session.parameters()
        if method_id is None or method_id == current.method:
            return
        schema = self._context.engines.methods[method_id].parameters
        carried: dict[str, ParameterValue] = {}
        for name, value in current.parameters.items():
            probe = ParameterSet(method_id, {name: value}, current.created, current.app_version)
            problems = validate_parameter_set(probe, method_id, schema)
            if not any(problem.name == name for problem in problems):
                carried[name] = value
        self._apply(new_parameter_set(method_id, carried))


class AdvancedPanel(_ParameterForm):
    """The Advanced panel: the method's Advanced parameters (D17)."""

    def __init__(self, context: ShellContext) -> None:
        """Create the panel.

        Args:
            context: The shell context.
        """
        super().__init__(context, "advanced")


def basic_panel(context: ShellContext) -> QWidget:
    """Build the Basic panel (a :data:`~clearwater.gui.contract.PanelFactory`).

    Args:
        context: The shell context.

    Returns:
        The :class:`BasicPanel`.
    """
    return BasicPanel(context)


def advanced_panel(context: ShellContext) -> QWidget:
    """Build the Advanced panel (a :data:`~clearwater.gui.contract.PanelFactory`).

    Args:
        context: The shell context.

    Returns:
        The :class:`AdvancedPanel`.
    """
    return AdvancedPanel(context)


def install_parameter_panels(window: ShellWindow, *, dialogs: PresetDialogs | None = None) -> None:
    """Attach the Basic, Advanced and Presets panels in ``Area.PARAMETERS`` (WP4.3 calls this).

    Args:
        window: The main window.
        dialogs: The dialogs of the Presets panel; the Qt dialogs when None (tests pass a fake).
    """
    window.attach(Area.PARAMETERS, basic_panel, title="Basic")
    window.attach(Area.PARAMETERS, advanced_panel, title="Advanced")
    window.attach(Area.PARAMETERS, partial(preset_panel, dialogs=dialogs), title="Presets")
