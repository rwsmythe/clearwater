"""Correction methods (architecture sections 2 and 3, plan 8.1).

WP3.2 adds the compensation and white-balance steps, WP3.3 the fusion inputs, weights and
blend; WP3.4 assembles them into ``methods.ancuti_fusion``, which registers the IF-3
``CorrectionMethod`` instances, and owns this file from then on. Array work goes through the
IF-2 backend of :mod:`clearwater.core`; this package imports nothing from ``clearwater.io``,
``clearwater.jobs`` or ``clearwater.gui``.
"""
