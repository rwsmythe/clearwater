"""DR-32: refuse non-string mapping keys before a document is written or after it is read.

``json.dumps`` silently turns an ``int`` key into a string (the round trip then changes) and
fails late on a ``float('nan')`` key. IF-9 (frozen) checks values but not keys, so the config
boundary checks them on every entry point (WP3.15; DR-32), and WP3.14 calls
:func:`check_string_keys` on a provenance object before it is embedded.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from clearwater.interfaces import FormatError, ParameterSet


def check_string_keys(value: object, where: str = "value") -> None:
    """Refuse a non-string mapping key at any depth of a JSON-bound value.

    Descends through mappings, lists and tuples. A reference cycle is refused as well, since it
    cannot be serialised.

    Args:
        value: The value to check.
        where: The location used in messages (for example ``"parameters"``).

    Raises:
        FormatError: A mapping anywhere inside ``value`` has a key that is not a ``str``
            (``int``, ``float`` including NaN, ``bool``, ``None``, ...), or ``value`` contains
            itself. The message names the path and the key's type.
    """
    _walk(value, where, set())


def check_parameter_set_keys(parameter_set: ParameterSet, where: str = "parameter set") -> None:
    """Apply :func:`check_string_keys` to the mappings of a parameter set.

    Args:
        parameter_set: The set; ``parameters``, ``source`` and ``settings`` are checked.
        where: The location prefix used in messages.

    Raises:
        FormatError: A mapping key anywhere in those three fields is not a ``str``.
    """
    check_string_keys(parameter_set.parameters, f"{where}.parameters")
    if parameter_set.source is not None:
        check_string_keys(parameter_set.source, f"{where}.source")
    if parameter_set.settings is not None:
        check_string_keys(parameter_set.settings, f"{where}.settings")


def _walk(value: Any, where: str, active: set[int]) -> None:
    """Check one value; ``active`` holds the ids of the containers on the current path."""
    if isinstance(value, Mapping):
        _enter(value, where, active)
        try:
            for key, item in value.items():
                if not isinstance(key, str):
                    raise FormatError(
                        f"non-string key {key!r} ({type(key).__name__}) in the mapping at {where}"
                    )
                _walk(item, f"{where}.{key}", active)
        finally:
            active.discard(id(value))
    elif isinstance(value, list | tuple):
        _enter(value, where, active)
        try:
            for index, item in enumerate(value):
                _walk(item, f"{where}[{index}]", active)
        finally:
            active.discard(id(value))


def _enter(container: object, where: str, active: set[int]) -> None:
    """Record a container on the current path, refusing a reference cycle."""
    if id(container) in active:
        raise FormatError(f"reference cycle at {where}")
    active.add(id(container))
