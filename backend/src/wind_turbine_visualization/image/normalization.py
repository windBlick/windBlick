"""Decode uploaded rasters and normalize EXIF orientation.

Pure domain logic: no FastAPI, no file paths. Operates on in-memory bytes
so it is deterministic and unit-testable.
"""

from dataclasses import dataclass
from io import BytesIO

from PIL import Image, ImageOps, UnidentifiedImageError

from wind_turbine_visualization.image.errors import InvalidImage, UnsupportedImageType

SUPPORTED_MIME_TYPES = frozenset({"image/jpeg", "image/png"})
MAX_DECODED_PIXELS = 24_000_000  # contract draft resource limit


@dataclass(frozen=True)
class NormalizedImage:
    """An upright raster plus the dimensions of that normalized frame."""

    image: Image.Image
    width_px: int
    height_px: int


def load_normalized_image(data: bytes, declared_mime_type: str) -> NormalizedImage:
    """Decode bytes, apply EXIF orientation once, and report dimensions.

    Args:
        data: Raw uploaded image bytes.
        declared_mime_type: Client-declared content type of the image part.

    Returns:
        The orientation-normalized image and its width/height in pixels.

    Raises:
        UnsupportedImageType: declared_mime_type is not JPEG or PNG.
        InvalidImage: bytes cannot be decoded or exceed the pixel limit.
    """
    if declared_mime_type not in SUPPORTED_MIME_TYPES:
        raise UnsupportedImageType(declared_mime_type)
    try:
        with Image.open(BytesIO(data)) as raw:
            raw.verify()  # cheap structural check
        with Image.open(BytesIO(data)) as reopened:
            if reopened.width * reopened.height > MAX_DECODED_PIXELS:
                raise InvalidImage("decoded pixel count exceeds limit")
            upright = ImageOps.exif_transpose(reopened)  # swaps W/H if rotated 90/270
            upright.load()
    except (UnidentifiedImageError, OSError) as exc:
        raise InvalidImage("image bytes could not be decoded") from exc
    return NormalizedImage(upright, upright.width, upright.height)
