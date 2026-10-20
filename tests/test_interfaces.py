"""WP2.2: the frozen interface types, IF-9 and IF-10 serialisation, validation, dependency rule."""

from __future__ import annotations

import dataclasses
import importlib
import inspect
import pkgutil
import subprocess
import sys
from collections.abc import Callable
from datetime import UTC, datetime
from fractions import Fraction
from pathlib import Path
from typing import Any

import numpy as np
import pytest

import clearwater.interfaces as interfaces
from clearwater.interfaces import (
    CacheKey,
    ColorDescription,
    Frame,
    Image,
    Parameter,
    ParameterProblem,
    ParameterSet,
    Settings,
    UnsupportedFormatVersionError,
    validate_parameter_set,
)
from clearwater.interfaces.parameters import FormatError

CREATED = datetime(2026, 10, 20, 12, 30, 15, 123456, tzinfo=UTC)


def _color() -> ColorDescription:
    return ColorDescription("bt709", "bt709", "bt709", "limited", 8, False, None)


def _image() -> Image:
    return Image(np.zeros((2, 2, 3), np.float32), "cpu", _color(), False)


def _frame() -> Frame:
    return Frame(
        np.zeros((2, 2, 3), np.float32),
        "cpu",
        _color(),
        False,
        pts=Fraction(1, 30),
        pts_ticks=1,
        time_base=Fraction(1, 30),
        index=0,
    )


def _interface_dataclasses() -> list[type]:
    """Every dataclass defined in a clearwater.interfaces module (not the stubs)."""
    found: dict[str, type] = {}
    for info in pkgutil.iter_modules(interfaces.__path__):
        if info.name == "stubs":
            continue
        module = importlib.import_module(f"clearwater.interfaces.{info.name}")
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if dataclasses.is_dataclass(obj) and obj.__module__ == module.__name__:
                found[obj.__qualname__] = obj
    return list(found.values())


def assert_frozen(cls: type) -> None:
    """Fail by name when a dataclass is not frozen."""
    params = getattr(cls, "__dataclass_params__", None)
    assert params is not None and params.frozen, f"{cls.__name__} is not a frozen dataclass"


def test_every_interface_dataclass_is_frozen() -> None:
    classes = _interface_dataclasses()
    names = {cls.__name__ for cls in classes}
    # section 3 names, plus the nine ruled types, plus the IF-9/IF-10 additions.
    assert {
        "ColorDescription",
        "Image",
        "Frame",
        "Parameter",
        "Stage",
        "ProbeResult",
        "EncoderCapability",
        "CacheKey",
        "JobResult",
        "ParameterSet",
        "Settings",
        "VideoStreamInfo",
        "AudioStreamInfo",
        "DataStreamInfo",
        "EditEntry",
        "Fault",
        "GoProInfo",
        "PhotoMetadata",
        "CacheEntry",
        "SinkReport",
        "ParameterProblem",
    } <= names
    for cls in classes:
        assert_frozen(cls)


def test_planted_non_frozen_dataclass_fails_by_name() -> None:
    @dataclasses.dataclass
    class Mutable:
        x: int

    with pytest.raises(AssertionError, match="Mutable is not a frozen dataclass"):
        assert_frozen(Mutable)


def test_assignment_raises_frozen_instance_error() -> None:
    parameter = Parameter("a", "int", 1, 0, 2, None, "basic", "A", "help", 0)
    instances: list[Any] = [
        _color(),
        _image(),
        _frame(),
        parameter,
        CacheKey(1, 2, 3),
        ParameterSet("c3", {}, CREATED, "0.0.0"),
        Settings(png_bit_depth=16, video_encoder="e", quality_level="q"),
    ]
    for instance in instances:
        field = dataclasses.fields(instance)[0].name
        with pytest.raises(dataclasses.FrozenInstanceError):
            setattr(instance, field, None)


def test_frame_is_an_image() -> None:
    frame = _frame()
    assert isinstance(frame, Image)
    assert issubclass(Frame, Image)
    assert [f.name for f in dataclasses.fields(Frame)][:4] == [
        "pixels",
        "device",
        "color",
        "orientation_applied",
    ]


# --- IF-9 ------------------------------------------------------------------------------------

PARAMS = (
    Parameter("strength", "float", 1.0, 0.0, 2.0, None, "basic", "S", "h", 0.0),
    Parameter("levels", "int", 4, 1, 8, None, "advanced", "L", "h", 1),
    Parameter("on", "bool", False, None, None, None, "basic", "O", "h", False),
    Parameter("mode", "enum", "a", None, None, ("a", "b"), "basic", "M", "h", "a"),
    Parameter("cap", "float", None, 0.0, None, None, "advanced", "C", "h", None),
)


def test_parameter_nullable_is_the_last_defaulted_field() -> None:
    fields = dataclasses.fields(Parameter)
    assert fields[-1].name == "nullable" and fields[-1].default is False
    assert Parameter("a", "int", 1, 0, 2, None, "basic", "A", "h", 0).nullable is False


def test_null_is_legal_where_nullable_or_default_is_none() -> None:
    gain_cap = Parameter(
        "red_gain_cap", "float", 2.0, 0.0, None, None, "advanced", "R", "h", 2.0, True
    )
    plain = Parameter("gamma", "float", 1.5, 0.0, None, None, "advanced", "G", "h", 1.0)
    ok = _set({"red_gain_cap": None})
    assert validate_parameter_set(ok, "c3", (gain_cap,)) == []
    assert _kinds(validate_parameter_set(_set({"gamma": None}), "c3", (plain,))) == ["wrong_type"]
    assert _kinds(validate_parameter_set(_set({"red_gain_cap": None}), "c3", (plain,))) == [
        "unknown_name"
    ]


def _set(parameters: dict[str, Any], method: str = "c3") -> ParameterSet:
    return ParameterSet(method, parameters, CREATED, "0.1.0")


def test_parameter_set_round_trip_exact() -> None:
    original = _set(
        {"strength": 0.1 + 0.2, "levels": 4, "on": True, "mode": "b", "cap": None, "g": 1e-300}
    )
    again = ParameterSet.from_json(original.to_json())
    assert again == original
    assert again.parameters["strength"] == 0.1 + 0.2
    # == cannot tell True from 1 or 1 from 1.0: compare the exact types too.
    assert {k: type(v) for k, v in again.parameters.items()} == {
        k: type(v) for k, v in original.parameters.items()
    }
    assert type(again.parameters["on"]) is bool
    assert type(again.parameters["levels"]) is int
    assert again.parameters["cap"] is None
    assert type(_set({"x": 1.0}).from_json(_set({"x": 1.0}).to_json()).parameters["x"]) is float
    assert again.created == CREATED
    assert again.to_dict()["created"] == "2026-10-20T12:30:15.123456+00:00"


def test_parameter_set_json_is_the_ad13_object() -> None:
    data = _set({"a": 1}).to_dict()
    assert list(data) == ["format_version", "method", "parameters", "created", "app_version"]
    assert data["format_version"] == 1


def test_provenance_round_trip() -> None:
    original = ParameterSet(
        "c3",
        {"strength": 1.0},
        CREATED,
        "0.1.0",
        source={"path": "a.mp4", "size": 12, "mtime_ns": 5, "probe": {"fps": 29.97, "vfr": False}},
        settings={"encoder": "x", "quality": "q", "bit_depth": 10, "device": "cpu"},
    )
    data = original.to_dict()
    assert "source" in data and "settings" in data
    assert ParameterSet.from_json(original.to_json()) == original
    assert "source" not in _set({}).to_dict()


def test_format_version_other_than_one_is_refused_by_name() -> None:
    data = _set({}).to_dict()
    data["format_version"] = 2
    import json

    with pytest.raises(UnsupportedFormatVersionError, match="format_version 2"):
        ParameterSet.from_json(json.dumps(data))
    with pytest.raises(UnsupportedFormatVersionError):
        ParameterSet.from_json(json.dumps({"method": "c3"}))


@pytest.mark.parametrize(
    "text",
    ["not json", "[]", '{"format_version": 1}', '{"parameters": {"a": NaN}, "format_version": 1}'],
)
def test_malformed_parameter_json_is_a_format_error(text: str) -> None:
    with pytest.raises(FormatError):
        ParameterSet.from_json(text)


def test_overflowing_float_spelling_is_refused_on_read() -> None:
    text = _set({"a": 1.0}).to_json().replace("1.0", "1e400")
    with pytest.raises(FormatError, match="1e400"):
        ParameterSet.from_json(text)


def test_huge_integer_round_trips_and_validates_without_raising() -> None:
    huge = 10**400
    again = ParameterSet.from_json(_set({"levels": huge}).to_json())
    assert again.parameters["levels"] == huge
    assert _kinds(validate_parameter_set(again, "c3", PARAMS)) == ["above_maximum"]
    assert _kinds(validate_parameter_set(_set({"strength": -(10**400)}), "c3", PARAMS)) == [
        "below_minimum"
    ]


def test_non_finite_float_is_not_serialised() -> None:
    with pytest.raises(ValueError, match="Out of range"):
        _set({"a": float("nan")}).to_json()


def _kinds(problems: list[ParameterProblem]) -> list[str]:
    return [problem.kind for problem in problems]


def test_valid_set_has_no_problems() -> None:
    ok = _set({"strength": 2.0, "levels": 1, "on": True, "mode": "b", "cap": 0.5})
    assert validate_parameter_set(ok, "c3", PARAMS) == []
    assert validate_parameter_set(_set({}), "c3", PARAMS) == []  # a partial set is valid


VALIDATION_CASES: list[tuple[str, dict[str, Any], str]] = [
    ("unknown_name", {"nope": 1}, "nope"),
    ("wrong_type", {"levels": 2.5}, "levels"),
    ("wrong_type", {"levels": True}, "levels"),
    ("wrong_type", {"on": 1}, "on"),
    ("wrong_type", {"mode": 3}, "mode"),
    ("wrong_type", {"strength": "1"}, "strength"),
    ("wrong_type", {"strength": None}, "strength"),
    ("not_finite", {"strength": float("inf")}, "strength"),
    ("below_minimum", {"strength": -0.1}, "strength"),
    ("above_maximum", {"levels": 9}, "levels"),
    ("not_a_choice", {"mode": "c"}, "mode"),
]


@pytest.mark.parametrize(("kind", "values", "name"), VALIDATION_CASES)
def test_validation_catches_each_problem_kind(kind: str, values: dict[str, Any], name: str) -> None:
    problems = validate_parameter_set(_set(values), "c3", PARAMS)
    assert _kinds(problems) == [kind]
    assert problems[0].name == name


def test_validation_catches_a_wrong_method() -> None:
    problems = validate_parameter_set(_set({}, method="ancuti2018"), "c3", PARAMS)
    assert _kinds(problems) == ["method_mismatch"]
    assert problems[0].name is None


def test_validation_reports_every_problem() -> None:
    problems = validate_parameter_set(_set({"nope": 1, "levels": 99, "mode": "z"}), "x", PARAMS)
    assert sorted(_kinds(problems)) == [
        "above_maximum",
        "method_mismatch",
        "not_a_choice",
        "unknown_name",
    ]


def test_every_problem_kind_is_covered_by_the_cases() -> None:
    covered = {kind for kind, _, _ in VALIDATION_CASES} | {"method_mismatch"}
    assert covered == set(interfaces.ProblemKind.__value__.__args__)  # type: ignore[attr-defined]


def _misses(validator: Callable[..., list[ParameterProblem]]) -> list[str]:
    """The kinds a validator fails to report on the standard cases, by name."""
    return [
        kind
        for kind, values, _ in VALIDATION_CASES
        if kind not in _kinds(validator(_set(values), "c3", PARAMS))
    ]


def test_planted_validation_miss_fails_by_name() -> None:
    assert _misses(validate_parameter_set) == []

    def no_range(
        parameter_set: ParameterSet, method_id: str, parameters: Any
    ) -> list[ParameterProblem]:
        kept = [
            problem
            for problem in validate_parameter_set(parameter_set, method_id, parameters)
            if problem.kind not in ("below_minimum", "above_maximum")
        ]
        return kept

    assert set(_misses(no_range)) == {"below_minimum", "above_maximum"}


# --- IF-10 -----------------------------------------------------------------------------------


def test_settings_defaults_come_from_their_clauses() -> None:
    s = Settings(png_bit_depth=16, video_encoder="e", quality_level="q")
    assert s.output_folder is None  # D34
    assert s.output_suffix == "_corrected"  # D36
    assert s.ten_bit_for_eight_bit is False  # D76
    assert s.provenance is True  # D91
    assert s.cache_limit_bytes == 20 * 10**9  # D71, SI gigabytes
    assert s.force_cpu is False  # AD-9
    assert s.last_parameters is None


def test_settings_defaults_ruled_at_round_1() -> None:
    s = Settings()
    assert (s.png_bit_depth, s.video_encoder, s.quality_level) == (16, "auto", "standard")
    with pytest.raises(TypeError):
        Settings(16)  # type: ignore[misc]  # kw_only


def test_created_is_timezone_aware_utc() -> None:
    from datetime import timedelta, timezone

    local = datetime(2026, 10, 20, 8, 0, tzinfo=timezone(timedelta(hours=-4)))
    again = ParameterSet.from_json(_set({}).__class__("c3", {}, local, "v").to_json())
    assert again.created == local and again.created.utcoffset() == timedelta(0)
    assert '"created": "2026-10-20T12:00:00+00:00"' in ParameterSet("c3", {}, local, "v").to_json()
    with pytest.raises(ValueError, match="timezone"):
        ParameterSet("c3", {}, datetime(2026, 1, 1), "v").to_json()
    data = _set({}).to_dict()
    data["created"] = "2026-01-01T00:00:00"
    with pytest.raises(FormatError, match="timezone"):
        ParameterSet.from_dict(data)


def test_settings_round_trip_exact() -> None:
    original = Settings(
        output_folder=Path("C:/out") / "x",
        output_suffix="_cw",
        png_bit_depth=8,
        video_encoder="hevc_nvenc",
        quality_level="standard",
        ten_bit_for_eight_bit=True,
        provenance=False,
        cache_limit_bytes=123456789,
        force_cpu=True,
        last_parameters=_set({"strength": 0.3, "cap": None}),
    )
    assert Settings.from_json(original.to_json()) == original
    plain = Settings(png_bit_depth=16, video_encoder="e", quality_level="q")
    assert Settings.from_json(plain.to_json()) == plain


def test_settings_format_version_and_shape_errors() -> None:
    import json

    data = json.loads(Settings(png_bit_depth=16, video_encoder="e", quality_level="q").to_json())
    for broken, error in (
        ({**data, "format_version": 2}, UnsupportedFormatVersionError),
        ({**data, "force_cpu": "yes"}, FormatError),
        ({**data, "png_bit_depth": True}, FormatError),
        ({**data, "extra": 1}, FormatError),
        ({k: v for k, v in data.items() if k != "provenance"}, FormatError),
    ):
        with pytest.raises(error):
            Settings.from_json(json.dumps(broken))


# --- dependency rule (plan 8.1) --------------------------------------------------------------


def test_interfaces_import_nothing_forbidden() -> None:
    code = (
        "import sys, clearwater.interfaces, clearwater.interfaces.stubs\n"
        "bad = [m for m in sys.modules if m.split('.')[0] in "
        "('cupy', 'av', 'PIL', 'PySide6', 'scipy', 'pillow_heif')"
        " or (m.startswith('clearwater.') and not m.startswith('clearwater.interfaces'))]\n"
        "print('BAD', sorted(bad))\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True, timeout=120
    )
    assert result.stdout.strip() == "BAD []", result.stdout + result.stderr


def test_module_layout_is_one_module_per_interface() -> None:
    names = {info.name for info in pkgutil.iter_modules(interfaces.__path__)}
    assert names == {
        "image",
        "backend",
        "method",
        "statistics",
        "video",
        "photo",
        "cache",
        "jobs",
        "parameters",
        "settings",
        "stubs",
    }


def test_select_backend_signature_and_interface_level_behaviour() -> None:
    signature = inspect.signature(interfaces.select_backend)
    assert list(signature.parameters) == ["settings", "height", "width", "method_id"]
    with pytest.raises(NotImplementedError, match=r"WP3\.1"):
        interfaces.select_backend(
            Settings(png_bit_depth=16, video_encoder="e", quality_level="q"), 1, 1, "c3"
        )
