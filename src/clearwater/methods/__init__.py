"""Correction methods (architecture sections 2 and 3, plan 8.1).

WP3.2 adds the compensation and white-balance steps, WP3.3 the fusion inputs, weights and
blend; WP3.4 assembles them into ``methods.ancuti_fusion``, which provides the IF-3
``CorrectionMethod`` instances ``c3`` and ``ancuti2018`` with their schemas
(``methods.schema``), and owns this file from then on. Array work goes through the IF-2 backend
of :mod:`clearwater.core`; this package imports nothing from ``clearwater.io``,
``clearwater.jobs`` or ``clearwater.gui``.
"""

from __future__ import annotations

from clearwater.interfaces.method import CorrectionMethod

from .ancuti_fusion import AncutiFusionMethod


def available_methods() -> dict[str, CorrectionMethod]:
    """Return the registered methods by id, the default first (D16).

    ``"c3"`` (the default) then ``"ancuti2018"``; Ancuti 2018 with blue compensation is
    ``ancuti2018`` with ``blue_compensation=True``, not an id. Each call returns new instances.

    Returns:
        Method id -> method.
    """
    return {"c3": AncutiFusionMethod("c3"), "ancuti2018": AncutiFusionMethod("ancuti2018")}


__all__ = ["AncutiFusionMethod", "available_methods"]
