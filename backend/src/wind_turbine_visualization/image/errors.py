"""Domain errors for image decoding and normalization.

Framework-free: the API layer maps these to HTTP responses. Carrying a
machine-readable ``code`` keeps the contract's status codes in one place.
"""


class ImageError(Exception):
    """Base class for image-handling domain errors."""

    code: str


class UnsupportedImageType(ImageError):
    """Raised when the upload is not a supported JPEG or PNG."""

    code = "UNSUPPORTED_IMAGE_TYPE"  # contract: HTTP 415

    def __init__(self) -> None:
        super().__init__(
            "Upload a JPEG or a non-animated PNG with the matching media type."
        )


class InvalidImage(ImageError):
    """Raised when bytes cannot be decoded or orientation is invalid."""

    code = "INVALID_IMAGE"  # contract: HTTP 422

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


class PixelLimitExceeded(ImageError):
    """Raised when the image exceeds the allowed pixel count."""

    code = "PIXEL_LIMIT_EXCEEDED"
