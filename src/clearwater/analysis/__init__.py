"""Video analysis (WP3.11): decode pass, staged statistics, smoothing over pts, recompute.

Plan 8.1: "Decode pass, staged statistics, smoothing, recompute". Everything this package needs
is injected (method, backend, cache, frame source); it depends only on the standard library,
NumPy and :mod:`clearwater.interfaces`, never on the GUI, jobs, io, cache or methods packages.
"""

from __future__ import annotations

from .engine import CANCELLED, AnalysisEngine, AnalysisSnapshot, Phase
from .proxy import (
    PROXY_SHORT_SIDE,
    AnalysisDeviceBackend,
    block_mean,
    frame_block_mean,
    frame_pixels_for_proxy,
    frame_pixels_on_host,
    make_proxy,
    proxy_factor,
    proxy_image,
    quantise,
)
from .smoothing import (
    DEFAULT_KIND,
    DEFAULT_WINDOW_S,
    GAUSSIAN_FALLOFF,
    KINDS,
    MEDIAN_WINDOW_S,
    STEP_AWARE_KINDS,
    exact_window,
    half_window_ticks,
    reach,
    smooth_series,
)
from .store import AnalysisStore, SchemaMismatchError, schema_hash, shaping_parameters

__all__ = [
    "CANCELLED",
    "DEFAULT_KIND",
    "DEFAULT_WINDOW_S",
    "GAUSSIAN_FALLOFF",
    "KINDS",
    "MEDIAN_WINDOW_S",
    "PROXY_SHORT_SIDE",
    "STEP_AWARE_KINDS",
    "AnalysisDeviceBackend",
    "AnalysisEngine",
    "AnalysisSnapshot",
    "AnalysisStore",
    "Phase",
    "SchemaMismatchError",
    "block_mean",
    "exact_window",
    "frame_block_mean",
    "frame_pixels_for_proxy",
    "frame_pixels_on_host",
    "half_window_ticks",
    "make_proxy",
    "proxy_factor",
    "proxy_image",
    "quantise",
    "reach",
    "schema_hash",
    "shaping_parameters",
    "smooth_series",
]
