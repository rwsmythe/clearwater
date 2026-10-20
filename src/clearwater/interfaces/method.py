"""IF-3: the correction method protocol, its parameters and its statistic stages.

Everything above the correction core reaches a method only through
:class:`CorrectionMethod` (spec 10.1). ``methods.ancuti_fusion`` registers ``c3`` (stages
``white_balance``, ``fusion``) and ``ancuti2018`` (``compensation``, ``white_balance``,
``fusion``), with ``ancuti2018-blue`` as ``ancuti2018`` with ``blue_compensation=True``
(AD-6, AD-8).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal, Protocol, runtime_checkable

from numpy.typing import NDArray

from .image import Image

type ParameterValue = bool | int | float | str | None
"""The value of one method parameter: its default, its neutral value, or a user setting.

``None`` appears only for a parameter that can be switched off
(for example a gain cap, D100); enum values are ``str``.
"""

type Statistics = Mapping[str, NDArray[Any]]
"""Per stage: statistic name -> small float array (for example shape ``(3,)`` for means)."""


@dataclass(frozen=True)
class Parameter:
    """One user-visible parameter of a method (IF-3).

    Attributes:
        name: The parameter name, the key in a parameter set (IF-9).
        type: ``"float"``, ``"int"``, ``"bool"`` or ``"enum"``.
        default: The default value.
        minimum: Lower bound for ``float`` and ``int``; None when unbounded.
        maximum: Upper bound for ``float`` and ``int``; None when unbounded.
        choices: The allowed values of an ``enum``; None otherwise.
        panel: ``"basic"`` or ``"advanced"``.
        label: The GUI label.
        help: The GUI help text.
        neutral: The value that makes the method an identity (V9).
    """

    name: str
    type: Literal["float", "int", "bool", "enum"]
    default: ParameterValue
    minimum: float | None
    maximum: float | None
    choices: tuple[str, ...] | None
    panel: Literal["basic", "advanced"]
    label: str
    help: str
    neutral: ParameterValue


@dataclass(frozen=True)
class Stage:
    """One analysis stage of a method (IF-3, AD-6).

    Attributes:
        name: ``"compensation"``, ``"white_balance"`` or ``"fusion"``.
        statistics: The statistic names the stage produces, for example ``("means", "alpha")``.
        smoothed: The subset of ``statistics`` that is smoothed over time.
        depends_on_parameters: The parameters whose change invalidates the stage.
        depends_on_stages: The earlier stages whose results the stage consumes.
        source_only: True when the stage depends on the source file alone and is cacheable
            with the proxies (D113).
    """

    name: str
    statistics: tuple[str, ...]
    smoothed: tuple[str, ...]
    depends_on_parameters: tuple[str, ...]
    depends_on_stages: tuple[str, ...]
    source_only: bool


@runtime_checkable
class CorrectionMethod(Protocol):
    """A correction method: staged whole-frame analysis plus a render step (IF-3).

    Optional context inputs (D61) are keyword-only extras on ``analyze`` and ``render`` in a
    future version.

    Attributes:
        id: ``"ancuti2018"`` or ``"c3"`` (c3 is the default, D16).
        label: The GUI label.
        parameters: The method's parameters.
        stages: The ordered statistic stages; one stage is valid (D98).
    """

    id: str
    label: str
    parameters: tuple[Parameter, ...]
    stages: tuple[Stage, ...]

    def analyze(
        self,
        stage: str,
        image: Image,
        params: Mapping[str, Any],
        earlier: Mapping[str, Statistics],
    ) -> Statistics:
        """Measure one stage's statistics on ``image`` (the analysis proxy).

        Args:
            stage: The stage name.
            image: The image to measure.
            params: The parameter values.
            earlier: The (smoothed) statistics of the earlier stages, by stage name.

        Returns:
            The raw statistics of the stage.
        """
        ...

    def render(
        self,
        image: Image,
        params: Mapping[str, Any],
        statistics: Mapping[str, Statistics],
    ) -> Image:
        """Correct ``image`` with the given statistics; refuses a missing stage.

        Args:
            image: The image to correct.
            params: The parameter values.
            statistics: The statistics of every stage, by stage name.

        Returns:
            The corrected image.
        """
        ...

    def closed_form(
        self,
        stage: str,
        params: Mapping[str, Any],
        earlier: Mapping[str, Statistics],
        measured: Statistics,
    ) -> Statistics | None:
        """Update a stage's statistics from parameters alone, without touching the proxy.

        Args:
            stage: The stage name.
            params: The parameter values.
            earlier: The statistics of the earlier stages, by stage name.
            measured: The statistics measured for the stage.

        Returns:
            The updated statistics, or None when the stage has no closed form (AD-7).
        """
        ...
