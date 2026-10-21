"""Tests of the photo read error (WP3.6, X-B2): the name and shape the shell catches."""

from __future__ import annotations

import pytest

from clearwater.io.photo import PhotoReadError


@pytest.mark.parametrize("kind", ["unsupported", "unreadable"])
def test_the_error_carries_its_kind_and_message(kind: str) -> None:
    error = PhotoReadError(kind, "a.dng is not supported")  # type: ignore[arg-type]
    assert error.kind == kind
    assert str(error) == "a.dng is not supported"
    assert isinstance(error, Exception)


def test_the_error_is_raised_and_caught_by_name() -> None:
    with pytest.raises(PhotoReadError) as caught:
        raise PhotoReadError("unreadable", "x.jpg is truncated")
    assert caught.value.kind == "unreadable"
