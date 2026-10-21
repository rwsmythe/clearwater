"""The parameter schemas of the two correction methods and their resolution (spec 6.7, IF-3).

One schema per method (D16): ``c3`` has no ``alpha``, ``blue_compensation`` or gain caps (D49 by
construction), ``ancuti2018`` no ``kappa``, ``lambda_`` or ``c3_*``. Basic holds the controls of
spec 6.7's Basic list; every other parameter is Advanced (D17), ``laplacian_fraction`` included
(DR-13). The names are the prototype ``Params`` fields plus ``blend_with_original``; every
default is AD-8's (the prototype ``Params()``), stated here once. The neutral values are
``Params.neutral()`` for the six V9 controls and the default elsewhere.

Every number has a finite minimum and maximum (inclusive, IF-9), so a slider can show it and
every value inside the bounds is one the steps can use on any image from 1 x 1 to 48 MP: each
spatial sigma is positive and its radius far inside the core's bound, and no product of
controls leaves the float32 range. ``blend_with_original`` is the user-facing percentage
(0 = fully corrected, 100 = the original; CHARC ruling on WP3.4 and WP3.17); the method divides
it by 100.

Validation (DR-19, X-4): :func:`resolve_parameters` fills the defaults of a partial set,
refuses an unknown name, checks the set with IF-9 ``validate_parameter_set`` and then the one
relation bounds cannot say (``normalisation_low < normalisation_high``). The first problem is
one ValueError naming the parameter, raised before any array work.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Any, Literal

from clearwater.interfaces.method import Parameter
from clearwater.interfaces.parameters import ParameterSet, validate_parameter_set

_CHECKED_AT = datetime(2000, 1, 1, tzinfo=UTC)
"""The ``created`` stamp of the transient parameter set built only to run IF-9's check."""


def _float(
    name: str,
    default: float,
    minimum: float,
    maximum: float,
    panel: Literal["basic", "advanced"],
    label: str,
    help_: str,
    *,
    neutral: float | None = None,
    nullable: bool = False,
) -> Parameter:
    """Build a ``float`` parameter; ``neutral`` defaults to ``default``."""
    return Parameter(
        name=name,
        type="float",
        default=default,
        minimum=minimum,
        maximum=maximum,
        choices=None,
        panel=panel,
        label=label,
        help=help_,
        neutral=default if neutral is None else neutral,
        nullable=nullable,
    )


# -- the parameters, each defined once ---------------------------------------------------------

_ALPHA = _float(
    "alpha",
    1.0,
    0.0,
    2.0,
    "basic",
    "Compensation strength",
    "Ancuti 2018 compensation strength alpha for red (and blue); 1 is the paper's value, "
    "0 compensates nothing.",
    neutral=0.0,
)
_C3_STRENGTH = _float(
    "c3_strength",
    1.0,
    0.0,
    2.0,
    "basic",
    "Compensation strength",
    "3C compensation strength: scales kappa and lambda together; 1 keeps the paper's values, "
    "0 compensates nothing.",
    neutral=0.0,
)
_BLUE_COMPENSATION = Parameter(
    name="blue_compensation",
    type="bool",
    default=False,
    minimum=None,
    maximum=None,
    choices=None,
    panel="basic",
    label="Blue compensation",
    help="Ancuti 2018: compensate the blue channel as well as red (off by default).",
    neutral=False,
)
_WHITE_BALANCE_STRENGTH = _float(
    "white_balance_strength",
    1.0,
    0.0,
    1.0,
    "basic",
    "White balance strength",
    "Gray-world white balance: 1 applies the full gray-world gains, 0 none.",
    neutral=0.0,
)
_SHARPEN_STRENGTH = _float(
    "sharpen_strength",
    1.0,
    0.0,
    2.0,
    "basic",
    "Sharpening strength",
    "Strength of the sharpened fusion input: 1 is the paper's, 0 is no sharpening.",
    neutral=0.0,
)
_BLEND_WITH_ORIGINAL = _float(
    "blend_with_original",
    0.0,
    0.0,
    100.0,
    "basic",
    "Blend with original (%)",
    "Mix the original back in: 0 % is fully corrected, 100 % is the original.",
    neutral=0.0,
)
_RED_GAIN_CAP = _float(
    "red_gain_cap",
    2.0,
    0.0,
    10.0,
    "advanced",
    "Red gain cap",
    "Ancuti 2018: the mean amount added to red may not exceed this multiple of the red mean; "
    "off removes the cap.",
    nullable=True,
)
_BLUE_GAIN_CAP = _float(
    "blue_gain_cap",
    2.0,
    0.0,
    10.0,
    "advanced",
    "Blue gain cap",
    "Ancuti 2018: the mean amount added to blue may not exceed this multiple of the blue mean; "
    "off removes the cap.",
    nullable=True,
)
_KAPPA = _float(
    "kappa",
    1.0,
    0.0,
    3.0,
    "advanced",
    "Kappa (red-green)",
    "3C strength on the red-green (Cr) channel; paper value 1.0.",
)
_LAMBDA = _float(
    "lambda_",
    0.7,
    0.0,
    3.0,
    "advanced",
    "Lambda (blue-yellow)",
    "3C strength on the blue-yellow (Cb) channel; paper value 0.7.",
)
_MAX_WHITE_BALANCE_GAIN = _float(
    "max_white_balance_gain",
    3.0,
    1.0,
    10.0,
    "advanced",
    "Maximum white balance gain",
    "Upper limit on every white-balance gain, applied after the strength.",
)
_GAMMA = _float(
    "gamma",
    1.5,
    0.1,
    4.0,
    "advanced",
    "Gamma",
    "Exponent of the gamma fusion input (input 1); 1 leaves it unchanged.",
    neutral=1.0,
)
_PYRAMID_MIN_LEVEL_SIZE = Parameter(
    name="pyramid_min_level_size",
    type="int",
    default=16,
    minimum=1,
    maximum=256,
    choices=None,
    panel="advanced",
    label="Pyramid minimum level size",
    help="Smallest short side, in pixels, of the coarsest fusion pyramid level.",
    neutral=16,
)
_C3_KERNEL_FRACTION = _float(
    "c3_kernel_fraction",
    0.05,
    0.005,
    0.25,
    "advanced",
    "3C local mean size",
    "Size of the 3C local colour mean, as a fraction of the image's short side.",
)
_C3_MASK_THRESHOLD = _float(
    "c3_mask_threshold",
    0.85,
    0.0,
    1.0,
    "advanced",
    "3C highlight threshold",
    "Pixels brighter than this (mean of R, G, B) are left uncompensated by 3C.",
)
_C3_MASK_SMOOTH_FRACTION = _float(
    "c3_mask_smooth_fraction",
    0.01,
    0.001,
    0.1,
    "advanced",
    "3C mask smoothing",
    "Softening of the 3C highlight mask, as a fraction of the image's short side.",
)
_SHARPEN_BLUR_FRACTION = _float(
    "sharpen_blur_fraction",
    0.005,
    0.0005,
    0.05,
    "advanced",
    "Sharpening blur size",
    "Blur of the sharpened fusion input's unsharp mask, as a fraction of the short side.",
)
_NORMALISATION_LOW = _float(
    "normalisation_low",
    0.5,
    0.0,
    100.0,
    "advanced",
    "Stretch low percentile",
    "Lower percentile of the sharpened input's histogram stretch; below the high percentile.",
)
_NORMALISATION_HIGH = _float(
    "normalisation_high",
    99.5,
    0.0,
    100.0,
    "advanced",
    "Stretch high percentile",
    "Upper percentile of the sharpened input's histogram stretch; above the low percentile.",
)
_LAPLACIAN_FRACTION = _float(
    "laplacian_fraction",
    0.001,
    0.0001,
    0.02,
    "advanced",
    "Contrast weight scale",
    "Scale of the Laplacian contrast weight, as a fraction of the image's short side.",
)
_SALIENCY_BLUR_FRACTION = _float(
    "saliency_blur_fraction",
    0.003,
    0.0005,
    0.05,
    "advanced",
    "Saliency blur size",
    "Blur of the saliency weight, as a fraction of the image's short side.",
)
_WEIGHT_DELTA = _float(
    "weight_delta",
    0.1,
    0.001,
    1.0,
    "advanced",
    "Weight regularisation",
    "Regularisation added to each fusion weight before normalising; paper value 0.1.",
)

# The parameters both methods share after compensation, in schema order.
_SHARED_BASIC = (_WHITE_BALANCE_STRENGTH, _SHARPEN_STRENGTH, _BLEND_WITH_ORIGINAL)
_SHARED_ADVANCED_6_7 = (_MAX_WHITE_BALANCE_GAIN, _GAMMA, _PYRAMID_MIN_LEVEL_SIZE)
_SHARED_REST = (
    _SHARPEN_BLUR_FRACTION,
    _NORMALISATION_LOW,
    _NORMALISATION_HIGH,
    _LAPLACIAN_FRACTION,
    _SALIENCY_BLUR_FRACTION,
    _WEIGHT_DELTA,
)

C3_PARAMETERS: tuple[Parameter, ...] = (
    _C3_STRENGTH,
    *_SHARED_BASIC,
    _KAPPA,
    _LAMBDA,
    *_SHARED_ADVANCED_6_7,
    _C3_KERNEL_FRACTION,
    _C3_MASK_THRESHOLD,
    _C3_MASK_SMOOTH_FRACTION,
    *_SHARED_REST,
)
"""The ``c3`` schema: Basic in spec 6.7 order, then Advanced in 6.7 order, then the rest."""

ANCUTI2018_PARAMETERS: tuple[Parameter, ...] = (
    _ALPHA,
    _BLUE_COMPENSATION,
    *_SHARED_BASIC,
    _RED_GAIN_CAP,
    _BLUE_GAIN_CAP,
    *_SHARED_ADVANCED_6_7,
    *_SHARED_REST,
)
"""The ``ancuti2018`` schema, in the same order; the caps are nullable (D52, D100, AD-26)."""


def resolve_parameters(
    method_id: str, parameters: Sequence[Parameter], params: Mapping[str, Any]
) -> dict[str, Any]:
    """Return the full, checked parameter values of one call (DR-19 at method level).

    A missing name takes its default (IF-9: a set may be partial); a ``float`` given as an
    ``int`` becomes a ``float``. The first problem raises.

    Args:
        method_id: The method id, for the IF-9 check and the messages.
        parameters: The method's schema.
        params: The supplied values.

    Returns:
        Parameter name -> value, one entry per schema parameter.

    Raises:
        ValueError: An unknown name, a value of the wrong type, not finite, outside its
            bounds, or ``normalisation_low`` not below ``normalisation_high``; one error naming
            the parameter.
    """
    supplied = dict(params)
    problems = validate_parameter_set(
        ParameterSet(
            method=method_id, parameters=supplied, created=_CHECKED_AT, app_version="check"
        ),
        method_id,
        parameters,
    )
    if problems:
        raise ValueError(f"{method_id}: {problems[0].message}")
    values: dict[str, Any] = {}
    for parameter in parameters:
        value = supplied.get(parameter.name, parameter.default)
        if parameter.type == "float" and value is not None:
            value = float(value)
        values[parameter.name] = value
    low, high = values["normalisation_low"], values["normalisation_high"]
    if not low < high:
        raise ValueError(
            f"{method_id}: normalisation_low={low!r} must be below normalisation_high={high!r}"
        )
    return values
