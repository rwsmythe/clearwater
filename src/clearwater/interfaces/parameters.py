"""IF-9: the parameter set, its JSON form and its method-schema validation.

The JSON follows AD-13: ``format_version``, ``method``, ``parameters``, ``created``,
``app_version``; the provenance sidecar (D90) adds ``source`` (path, size, mtime, probe summary)
and ``settings`` (encoder, quality, bit depth, device). Only format version 1 exists; any other
is refused by name. No file I/O lives here.
"""

from __future__ import annotations

import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal, NoReturn

from .method import Parameter, ParameterValue

FORMAT_VERSION = 1
"""The only parameter-set format version this module reads and writes (AD-13)."""

_KEYS = ("format_version", "method", "parameters", "created", "app_version")
_PROVENANCE_KEYS = ("source", "settings")


class FormatError(ValueError):
    """A serialised parameter set or settings document is malformed."""


class UnsupportedFormatVersionError(FormatError):
    """A serialised document carries a ``format_version`` other than 1."""


def _reject_constant(name: str) -> NoReturn:
    """Refuse the JSON constants ``NaN``, ``Infinity`` and ``-Infinity``."""
    raise FormatError(f"non-finite number {name} is not valid JSON here")


def _parse_float(text: str) -> float:
    """Parse a JSON float, refusing one that overflows to infinity (for example ``1e400``)."""
    value = float(text)
    if not math.isfinite(value):
        raise FormatError(f"non-finite number {text} is not valid JSON here")
    return value


def loads_object(text: str) -> dict[str, Any]:
    """Parse JSON text that must hold one object, refusing non-finite numbers.

    Args:
        text: The JSON text.

    Returns:
        The parsed object.

    Raises:
        FormatError: The text is not valid JSON, holds non-finite numbers, or is not an object.
    """
    try:
        data = json.loads(text, parse_constant=_reject_constant, parse_float=_parse_float)
    except json.JSONDecodeError as error:
        raise FormatError(f"not valid JSON: {error}") from error
    if not isinstance(data, dict):
        raise FormatError(f"expected a JSON object, got {type(data).__name__}")
    return data


def check_format_version(data: Mapping[str, Any]) -> None:
    """Check a decoded document's ``format_version``.

    Args:
        data: The decoded document.

    Raises:
        UnsupportedFormatVersionError: The version is absent, not an integer, or not 1.
    """
    version = data.get("format_version")
    if isinstance(version, bool) or not isinstance(version, int) or version != FORMAT_VERSION:
        raise UnsupportedFormatVersionError(
            f"format_version {version!r} is not supported (only {FORMAT_VERSION})"
        )


def _is_value(value: object) -> bool:
    """Whether ``value`` is a legal :data:`ParameterValue`."""
    return value is None or isinstance(value, bool | int | float | str)


@dataclass(frozen=True)
class ParameterSet:
    """A method's parameter values, as stored in presets and provenance (IF-9; AD-13).

    Attributes:
        method: The method id (IF-3), for example ``"c3"``.
        parameters: Parameter name -> value. Values are JSON-native (bool, int, float, str,
            None); a set may be partial.
        created: When the set was created: a timezone-aware datetime, written and read in UTC.
            Serialised as ISO-8601.
        app_version: The Clearwater version that wrote the set.
        source: Provenance only: the source file's path, size, mtime and a probe summary, as
            JSON-native values; None for a preset.
        settings: Provenance only: encoder, quality, bit depth and device, as JSON-native
            values; None for a preset.
    """

    method: str
    parameters: Mapping[str, ParameterValue]
    created: datetime
    app_version: str
    source: Mapping[str, Any] | None = None
    settings: Mapping[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return the AD-13 object (JSON-native values), with provenance keys when set.

        Raises:
            ValueError: ``created`` is not timezone-aware.
        """
        if self.created.tzinfo is None:
            raise ValueError("created must be timezone-aware")
        data: dict[str, Any] = {
            "format_version": FORMAT_VERSION,
            "method": self.method,
            "parameters": dict(self.parameters),
            "created": self.created.astimezone(UTC).isoformat(),
            "app_version": self.app_version,
        }
        if self.source is not None:
            data["source"] = dict(self.source)
        if self.settings is not None:
            data["settings"] = dict(self.settings)
        return data

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ParameterSet:
        """Build a set from a decoded AD-13 object.

        Args:
            data: The decoded object.

        Returns:
            The parameter set.

        Raises:
            UnsupportedFormatVersionError: ``format_version`` is not 1.
            FormatError: A key is missing, unknown, or has the wrong type.
        """
        check_format_version(data)
        unknown = sorted(set(data) - set(_KEYS) - set(_PROVENANCE_KEYS))
        if unknown:
            raise FormatError(f"unknown keys: {', '.join(unknown)}")
        missing = [key for key in _KEYS if key not in data]
        if missing:
            raise FormatError(f"missing keys: {', '.join(missing)}")
        method, parameters, created, app_version = (
            data["method"],
            data["parameters"],
            data["created"],
            data["app_version"],
        )
        if not isinstance(method, str):
            raise FormatError("method must be a string")
        if not isinstance(app_version, str):
            raise FormatError("app_version must be a string")
        if not isinstance(parameters, dict) or not all(
            isinstance(k, str) and _is_value(v) for k, v in parameters.items()
        ):
            raise FormatError("parameters must map names to bool, int, float, str or null")
        if not isinstance(created, str):
            raise FormatError("created must be an ISO-8601 string")
        try:
            created_at = datetime.fromisoformat(created)
        except ValueError as error:
            raise FormatError(f"created is not ISO-8601: {created!r}") from error
        if created_at.tzinfo is None:
            raise FormatError(f"created has no timezone: {created!r}")
        created_at = created_at.astimezone(UTC)
        extras: dict[str, Mapping[str, Any] | None] = {}
        for key in _PROVENANCE_KEYS:
            value = data.get(key)
            if value is not None and not isinstance(value, dict):
                raise FormatError(f"{key} must be an object")
            extras[key] = value
        return cls(
            method=method,
            parameters=parameters,
            created=created_at,
            app_version=app_version,
            source=extras["source"],
            settings=extras["settings"],
        )

    def to_json(self) -> str:
        """Return the set as AD-13 JSON text (UTF-8 safe, indented).

        Returns:
            The JSON text.

        Raises:
            ValueError: A value is a non-finite float, or ``created`` is not timezone-aware.
        """
        return json.dumps(self.to_dict(), indent=2, allow_nan=False)

    @classmethod
    def from_json(cls, text: str) -> ParameterSet:
        """Parse AD-13 JSON text.

        Args:
            text: The JSON text.

        Returns:
            The parameter set; ``from_json(s.to_json()) == s``.

        Raises:
            UnsupportedFormatVersionError: ``format_version`` is not 1.
            FormatError: The text is not a valid parameter set.
        """
        return cls.from_dict(loads_object(text))


type ProblemKind = Literal[
    "method_mismatch",
    "unknown_name",
    "wrong_type",
    "not_finite",
    "below_minimum",
    "above_maximum",
    "not_a_choice",
]
"""The kinds of problem :func:`validate_parameter_set` reports."""


@dataclass(frozen=True)
class ParameterProblem:
    """One way a parameter set disagrees with a method's schema (IF-9).

    Attributes:
        kind: The kind of problem.
        name: The parameter name concerned, or None for ``"method_mismatch"``.
        message: A user-readable description.
    """

    kind: ProblemKind
    name: str | None
    message: str


def _type_problem(parameter: Parameter, value: ParameterValue) -> str | None:
    """Return why ``value`` is not of the parameter's declared type, or None when it is."""
    if value is None:
        return None if parameter.default is None else "null is not allowed"
    if parameter.type == "bool":
        ok = isinstance(value, bool)
    elif parameter.type == "int":
        ok = isinstance(value, int) and not isinstance(value, bool)
    elif parameter.type == "float":
        ok = isinstance(value, int | float) and not isinstance(value, bool)
    else:
        ok = isinstance(value, str)
    return None if ok else f"expected {parameter.type}, got {type(value).__name__}"


def validate_parameter_set(
    parameter_set: ParameterSet, method_id: str, parameters: Sequence[Parameter]
) -> list[ParameterProblem]:
    """Check a parameter set against a method's schema (IF-9 method-schema validation).

    Checks the method id, unknown names, each value's type, ``float``/``int`` minimum and
    maximum (inclusive), and ``enum`` choices. A ``float`` parameter accepts an ``int`` (a
    hand-written preset may say ``1``); a ``bool`` is never a number.
    A parameter missing from the set is not a problem: sets may be partial and the method default
    applies.

    Args:
        parameter_set: The set to check.
        method_id: The id of the method whose schema applies (``CorrectionMethod.id``).
        parameters: The method's parameters (``CorrectionMethod.parameters``).

    Returns:
        The problems found, in a stable order; empty when the set is valid.
    """
    problems: list[ParameterProblem] = []
    if parameter_set.method != method_id:
        problems.append(
            ParameterProblem(
                "method_mismatch",
                None,
                f"parameter set is for method {parameter_set.method!r}, not {method_id!r}",
            )
        )
    schema = {parameter.name: parameter for parameter in parameters}
    for name, value in parameter_set.parameters.items():
        parameter = schema.get(name)
        if parameter is None:
            problems.append(ParameterProblem("unknown_name", name, f"unknown parameter {name!r}"))
            continue
        reason = _type_problem(parameter, value)
        if reason is not None:
            problems.append(ParameterProblem("wrong_type", name, f"{name}: {reason}"))
            continue
        if value is None:
            continue
        if parameter.type in ("float", "int"):
            assert isinstance(value, int | float)  # narrowed by _type_problem
            if isinstance(value, float) and not math.isfinite(value):
                problems.append(ParameterProblem("not_finite", name, f"{name}: {value!r}"))
            elif parameter.minimum is not None and value < parameter.minimum:
                problems.append(
                    ParameterProblem(
                        "below_minimum", name, f"{name}: {value!r} < minimum {parameter.minimum!r}"
                    )
                )
            elif parameter.maximum is not None and value > parameter.maximum:
                problems.append(
                    ParameterProblem(
                        "above_maximum", name, f"{name}: {value!r} > maximum {parameter.maximum!r}"
                    )
                )
        elif parameter.type == "enum" and value not in (parameter.choices or ()):
            problems.append(
                ParameterProblem(
                    "not_a_choice", name, f"{name}: {value!r} not in {parameter.choices!r}"
                )
            )
    return problems
