"""Domain errors for image decoding and normalization.

Framework-free: the API layer maps these to HTTP responses. Carrying a
machine-readable ``code`` keeps the contract's status codes in one place.
"""


class ImageError(Exception):
    """Base class for image-handling domain errors."""

    code: str


class UnsupportedImageType(ImageError):
    """Raised when the declared media type is not JPEG or PNG."""

    code = "UNSUPPORTED_IMAGE_TYPE"  # contract: HTTP 415

    def __init__(self, declared_mime_type: str) -> None:
        self.declared_mime_type = declared_mime_type
        super().__init__(f"unsupported image type: {declared_mime_type!r}")


class InvalidImage(ImageError):
    """Raised when bytes cannot be decoded or exceed resource limits."""

    code = "INVALID_IMAGE"  # contract: HTTP 422

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)
