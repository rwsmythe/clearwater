"""The photo read error (WP3.6, X-B2): what the shell catches to show a G10 message."""

from __future__ import annotations

from typing import Literal

PhotoErrorKind = Literal["unsupported", "unreadable"]


class PhotoReadError(Exception):
    """A photo cannot be read: it is unsupported or unreadable.

    "Untagged" is not an error: it is ``ColorDescription.assumed`` on the result.

    Attributes:
        kind: ``"unsupported"`` (ProRAW or DNG, CMYK, an interlaced 16-bit PNG, a TIFF
            compression that is not decoded, an unknown format) or ``"unreadable"`` (missing,
            truncated or corrupt, spec 5.4).
    """

    def __init__(self, kind: PhotoErrorKind, message: str) -> None:
        """Store the kind and the user-readable message.

        Args:
            kind: The reason class.
            message: A message the GUI can show (G10), naming the file. Characters outside ASCII
                (a file name in another script) are written as backslash escapes so the message
                is safe on the Windows console.
        """
        super().__init__(message.encode("ascii", "backslashreplace").decode("ascii"))
        self.kind: PhotoErrorKind = kind
