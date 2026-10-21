"""Photo input and output (WP3.6): HEIC, JPEG, PNG and TIFF in, PNG out (IF-6).

``PhotoReader`` satisfies ``PhotoSource`` and ``PhotoWriter`` satisfies ``PhotoSink``;
``read_photo`` and ``write_photo`` are the same on default instances. ``PhotoReadError`` is what a
failed read raises, with a ``kind`` of ``"unsupported"`` or ``"unreadable"``. The caller opens
``SafeWrite`` and passes its temporary path to the writer; this package imports nothing from
``clearwater.jobs``.
"""

from __future__ import annotations

from clearwater.io.photo.errors import PhotoErrorKind, PhotoReadError
from clearwater.io.photo.reader import PhotoReader, read_photo
from clearwater.io.photo.writer import PhotoWriter, write_photo

__all__ = [
    "PhotoErrorKind",
    "PhotoReadError",
    "PhotoReader",
    "PhotoWriter",
    "read_photo",
    "write_photo",
]
