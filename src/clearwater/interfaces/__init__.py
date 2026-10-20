"""The frozen interfaces IF-1 to IF-10 (architecture section 3, AD-20).

Types, protocols and one function signature with no behaviour, plus in-memory stubs in
:mod:`clearwater.interfaces.stubs` so later packages can build and test before their
dependencies exist. This package imports nothing from ``core``, ``methods``, ``io``, ``jobs``,
``gui`` or any GPU, video, imaging or GUI library (plan section 8.1). After the WP2.2 accept an
interface changes only by a CHARC decision logged in ``docs/decisions.md``.

======  ==========================================  ==============
IF      Contents                                    Module
======  ==========================================  ==============
IF-1    ``ColorDescription``, ``Image``, ``Frame``  ``image``
IF-2    ``ArrayBackend``, ``select_backend``        ``backend``
IF-3    ``Parameter``, ``Stage``, ``CorrectionMethod``  ``method``
IF-4    ``StatisticsStore``                         ``statistics``
IF-5    ``VideoSource``, ``VideoSink``, ``ProbeResult``  ``video``
IF-6    ``PhotoSource``, ``PhotoSink``              ``photo``
IF-7    ``CacheKey``, ``ProxyCache``                ``cache``
IF-8    ``Progress``, ``JobResult``                 ``jobs``
IF-9    ``ParameterSet``                            ``parameters``
IF-10   ``Settings``                                ``settings``
======  ==========================================  ==============
"""

from __future__ import annotations

from .backend import ArrayBackend, select_backend
from .cache import CacheEntry, CacheKey, ProxyCache
from .image import Array, ColorDescription, Frame, Image
from .jobs import JobResult, Progress
from .method import CorrectionMethod, Parameter, ParameterValue, Stage, Statistics
from .parameters import (
    FORMAT_VERSION,
    FormatError,
    ParameterProblem,
    ParameterSet,
    ProblemKind,
    UnsupportedFormatVersionError,
    validate_parameter_set,
)
from .photo import PhotoMetadata, PhotoSink, PhotoSource
from .settings import (
    DEFAULT_CACHE_LIMIT_BYTES,
    DEFAULT_OUTPUT_SUFFIX,
    DEFAULT_PNG_BIT_DEPTH,
    DEFAULT_QUALITY_LEVEL,
    DEFAULT_VIDEO_ENCODER,
    Settings,
)
from .statistics import StatisticsStore
from .video import (
    AudioStreamInfo,
    DataStreamInfo,
    EditEntry,
    EncoderCapability,
    Fault,
    FaultKind,
    GoProInfo,
    ProbeResult,
    SinkReport,
    VideoSink,
    VideoSource,
    VideoStreamInfo,
)

__all__ = [
    "DEFAULT_CACHE_LIMIT_BYTES",
    "DEFAULT_OUTPUT_SUFFIX",
    "DEFAULT_PNG_BIT_DEPTH",
    "DEFAULT_QUALITY_LEVEL",
    "DEFAULT_VIDEO_ENCODER",
    "FORMAT_VERSION",
    "Array",
    "ArrayBackend",
    "AudioStreamInfo",
    "CacheEntry",
    "CacheKey",
    "ColorDescription",
    "CorrectionMethod",
    "DataStreamInfo",
    "EditEntry",
    "EncoderCapability",
    "Fault",
    "FaultKind",
    "FormatError",
    "Frame",
    "GoProInfo",
    "Image",
    "JobResult",
    "Parameter",
    "ParameterProblem",
    "ParameterSet",
    "ParameterValue",
    "PhotoMetadata",
    "PhotoSink",
    "PhotoSource",
    "ProbeResult",
    "ProblemKind",
    "Progress",
    "ProxyCache",
    "Settings",
    "SinkReport",
    "Stage",
    "Statistics",
    "StatisticsStore",
    "UnsupportedFormatVersionError",
    "VideoSink",
    "VideoSource",
    "VideoStreamInfo",
    "select_backend",
    "validate_parameter_set",
]
