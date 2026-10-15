"""The parameter set of the reference pipeline prototype.

Every control of spec section 6.7 is a field of :class:`Params`, together with the open
values of spec section 14.1 that the pipeline needs. Each field's source is named in the
class docstring: a value from one of the two reference papers (spec section 6.1), a value
fixed by the spec, or a WP1.1 choice recorded with its reasoning in
``docs/reports/wp1.1-open-values.md``.

Every spatial parameter is a fraction of the image's short side (spec section 6.6, D56);
:func:`prototype.pipeline.spatial_sigma` turns it into pixels.
"""

from __future__ import annotations

import dataclasses
import math
from dataclasses import dataclass
from typing import Literal

Method = Literal["ancuti2018", "c3"]
METHODS: tuple[Method, ...] = ("ancuti2018", "c3")


@dataclass(frozen=True)
class Params:
    """All parameters of one run of the pipeline, with their defaults.

    The constructor validates every field and raises :class:`ValueError` on a value the
    pipeline cannot use.

    Attributes:
        method: Channel compensation method (spec 6.2 step 1, 6.7 Basic). Default
            ``"ancuti2018"``: WP1.1 choice, see open-values report.
        alpha: Ancuti 2018 compensation strength (spec 6.3.1). Paper value 1.0.
        blue_compensation: Ancuti 2018 blue compensation on/off (spec 6.3.1: off by
            default). Spec value False.
        red_gain_cap: Ancuti 2018 red gain cap: the mean added amount may not exceed this
            multiple of the original red mean (spec 6.3.1, D50, D100); ``None`` disables
            the cap. Default 2.0: WP1.1 choice, see open-values report.
        blue_gain_cap: The same cap for the blue channel (D52); ``None`` disables it.
            Default 2.0: WP1.1 choice, see open-values report.
        kappa: 3C strength on Cr, the paper's red-green (a*) channel (spec 6.3.2). Paper
            value 1.0.
        lambda_: 3C strength on Cb, the paper's blue-yellow (b*) channel (spec 6.3.2).
            Paper value 0.7.
        c3_strength: Basic 3C slider; multiplies ``kappa`` and ``lambda_`` together
            (spec 6.3.2, D48). Spec value 1.0 (the paper's ratio unchanged).
        c3_kernel_fraction: Sigma of the 3C Gaussian local mean G{} as a fraction of the
            short side (spec 6.3.2, 6.6). Default 0.05: WP1.1 choice, see open-values
            report.
        c3_mask_threshold: Mean(R, G, B) above which the 3C mask M is 0 (spec 6.3.2). Spec
            value 0.85.
        c3_mask_smooth_fraction: Sigma of the Gaussian that smooths the 3C mask, as a
            fraction of the short side (spec 6.3.2, 6.6). Default 0.01: WP1.1 choice, see
            open-values report.
        white_balance_strength: Gray-world strength, 1.0 = full gray-world gains, 0.0 =
            none (spec 6.2 step 2, 6.7 Basic). Default 1.0 (the paper's full gray world);
            the interpolation rule is a WP1.1 choice, see open-values report.
        max_white_balance_gain: Upper clamp on every white-balance gain (spec 6.2, D99);
            at least 1, so that it never lowers a gain of 1.
            Default 3.0: WP1.1 choice, see open-values report.
        gamma: Exponent of fusion input 1, ``I ** gamma`` (spec 6.2 step 3). Default 1.5:
            WP1.1 choice (the paper gives no value), see open-values report.
        sharpen_strength: Fusion input 2 strength; 1.0 = the paper's
            ``(I + N{I - G*I}) / 2``, 0.0 = ``I`` (spec 6.2 step 3, 6.7 Basic). Default 1.0
            (paper); the interpolation rule is a WP1.1 choice, see open-values report.
        sharpen_blur_fraction: Sigma of the sharpening Gaussian G as a fraction of the
            short side (spec 6.2, 6.6). Default 0.005: WP1.1 choice, see open-values
            report.
        normalisation_low: Lower percentile (0-100) of the histogram stretch N{} bounds,
            over all pixels and channels of the whole image (spec 6.2, 14.1). Default 0.5:
            WP1.1 choice, see open-values report.
        normalisation_high: Upper percentile of the same stretch. Default 99.5: WP1.1
            choice, see open-values report.
        laplacian_fraction: Sigma of the Laplacian-of-Gaussian of the Laplacian contrast
            weight, as a fraction of the short side (spec 6.6). Default 0.001: WP1.1
            choice, see open-values report.
        saliency_blur_fraction: Sigma of the Gaussian blur of the Achanta saliency weight,
            as a fraction of the short side (spec 6.6). Default 0.003: WP1.1 choice, see
            open-values report.
        weight_delta: Weight regularisation delta of the normalisation
            ``(W_k + delta) / (sum W_k + K * delta)`` (spec 6.2 step 4). Paper value 0.1.
        pyramid_min_level_size: Minimum short side, in pixels, of the coarsest pyramid
            level; sets the pyramid depth (spec 6.6). Default 16: WP1.1 choice, see
            open-values report.
        blend_with_original: Final linear blend with the input image; 0.0 = fully
            corrected, 1.0 = the original (spec 6.7 Basic, 14.1). Default 0.0; the
            direction is a WP1.1 choice recorded for V9, see open-values report.
    """

    method: Method = "ancuti2018"
    alpha: float = 1.0
    blue_compensation: bool = False
    red_gain_cap: float | None = 2.0
    blue_gain_cap: float | None = 2.0
    kappa: float = 1.0
    lambda_: float = 0.7
    c3_strength: float = 1.0
    c3_kernel_fraction: float = 0.05
    c3_mask_threshold: float = 0.85
    c3_mask_smooth_fraction: float = 0.01
    white_balance_strength: float = 1.0
    max_white_balance_gain: float = 3.0
    gamma: float = 1.5
    sharpen_strength: float = 1.0
    sharpen_blur_fraction: float = 0.005
    normalisation_low: float = 0.5
    normalisation_high: float = 99.5
    laplacian_fraction: float = 0.001
    saliency_blur_fraction: float = 0.003
    weight_delta: float = 0.1
    pyramid_min_level_size: int = 16
    blend_with_original: float = 0.0

    def __post_init__(self) -> None:
        """Validate every field.

        Raises:
            ValueError: A field is outside the range the pipeline accepts.
        """
        if self.method not in METHODS:
            raise ValueError(f"method must be one of {', '.join(METHODS)}, got {self.method!r}")
        for name, value in dataclasses.asdict(self).items():
            if isinstance(value, float) and not math.isfinite(value):
                raise ValueError(f"{name} must be finite, got {value}")
        non_negative = (
            "alpha",
            "kappa",
            "lambda_",
            "c3_strength",
            "white_balance_strength",
            "sharpen_strength",
        )
        for name in non_negative:
            if getattr(self, name) < 0.0:
                raise ValueError(f"{name} must be >= 0, got {getattr(self, name)}")
        for name in ("red_gain_cap", "blue_gain_cap"):
            cap = getattr(self, name)
            if cap is not None and (not math.isfinite(cap) or cap < 0.0):
                raise ValueError(f"{name} must be >= 0 or None, got {cap}")
        positive = (
            "c3_kernel_fraction",
            "c3_mask_smooth_fraction",
            "gamma",
            "sharpen_blur_fraction",
            "laplacian_fraction",
            "saliency_blur_fraction",
            "weight_delta",
        )
        for name in positive:
            if getattr(self, name) <= 0.0:
                raise ValueError(f"{name} must be > 0, got {getattr(self, name)}")
        if self.max_white_balance_gain < 1.0:
            # A maximum below 1 would lower every gain, so strength 0 would not be "none".
            raise ValueError(
                f"max_white_balance_gain must be >= 1, got {self.max_white_balance_gain}"
            )
        if not 0.0 <= self.normalisation_low < self.normalisation_high <= 100.0:
            raise ValueError(
                "normalisation percentiles must satisfy 0 <= low < high <= 100, got "
                f"{self.normalisation_low} and {self.normalisation_high}"
            )
        if isinstance(self.pyramid_min_level_size, bool) or self.pyramid_min_level_size < 1:
            raise ValueError(
                f"pyramid_min_level_size must be an integer >= 1, got {self.pyramid_min_level_size}"
            )
        if not 0.0 <= self.blend_with_original <= 1.0:
            raise ValueError(
                f"blend_with_original must be in [0, 1], got {self.blend_with_original}"
            )

    @classmethod
    def neutral(cls) -> Params:
        """Return the parameter set under which the pipeline is as close to identity as it gets.

        Compensation strength 0 (``alpha`` and ``c3_strength``), white-balance strength 0,
        gamma 1 and sharpening 0 make each step an identity, so the two fusion inputs are
        the same image, and fusing two identical inputs reconstructs that image whatever
        the weights. The blend stays at 0.0 (fully corrected), so the identity comes from
        the steps themselves, not from blending back to the original. The method stays
        the default; ``dataclasses.replace(Params.neutral(), method="c3")`` is neutral
        too. How close to identity the result is (floating-point round-off only) is
        measured in the open-values report.

        Returns:
            The neutral parameter set (V9).
        """
        return cls(
            alpha=0.0,
            c3_strength=0.0,
            white_balance_strength=0.0,
            gamma=1.0,
            sharpen_strength=0.0,
            blend_with_original=0.0,
        )
