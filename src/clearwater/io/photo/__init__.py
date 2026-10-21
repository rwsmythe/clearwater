"""Photo input and output (WP3.6): HEIC, JPEG, PNG and TIFF in, PNG out (IF-6).

``PhotoReadError`` is what a failed read raises, with a ``kind`` of ``"unsupported"`` or
``"unreadable"``.
"""

from __future__ import annotations

from clearwater.io.photo.errors import PhotoErrorKind, PhotoReadError

__all__ = ["PhotoErrorKind", "PhotoReadError"]
