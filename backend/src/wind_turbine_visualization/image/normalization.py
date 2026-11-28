"""Decode uploaded rasters and normalize EXIF orientation.

Pure domain logic: no FastAPI, no file paths. Operates on in-memory bytes
so it is deterministic and unit-testable.
"""

from dataclasses import dataclass, field
from io import BytesIO

from PIL import ExifTags, Image, ImageOps

from wind_turbine_visualization.image.camera_exif import CameraExif, read_camera_exif
from wind_turbine_visualization.image.errors import (
    InvalidImage,
    PixelLimitExceeded,
    UnsupportedImageType,
)

SUPPORTED_FORMATS = {
    "image/jpeg": ("JPEG", b"\xff\xd8"),
    "image/png": ("PNG", b"\x89PNG\r\n\x1a\n"),
}
MAX_DECODED_PIXELS = 24_000_000  # contract draft resource limit


@dataclass(frozen=True)
class NormalizedImage:
    """An upright raster plus the dimensions of that normalized frame."""

    image: Image.Image
    width_px: int
    height_px: int
    original_orientation: int = 1
    camera_exif: CameraExif = field(default_factory=CameraExif)


def load_normalized_image(data: bytes, declared_mime_type: str) -> NormalizedImage:
    """Decode bytes, apply EXIF orientation once, and report dimensions.

    Args:
        data: Raw uploaded image bytes.
        declared_mime_type: Client-declared content type of the image part.

    Returns:
        The orientation-normalized image and its width/height in pixels.

    Raises:
        UnsupportedImageType: format is unsupported or disagrees with the media type.
        PixelLimitExceeded: the image exceeds the pixel limit.
        InvalidImage: bytes cannot be decoded or orientation is invalid.
    """
    format_spec = SUPPORTED_FORMATS.get(declared_mime_type)
    if format_spec is None or not data.startswith(format_spec[1]):
        raise UnsupportedImageType()
    format_name, _ = format_spec

    try:
        # The JPEG decoder also accepts the primary raster in JPEG/MPO photos.
        with Image.open(BytesIO(data), formats=(format_name,)) as raw:
            if raw.width * raw.height > MAX_DECODED_PIXELS:
                raise PixelLimitExceeded("Image exceeds the decoded pixel limit.")
            if raw.get_format_mimetype() == "image/apng":
                raise UnsupportedImageType()
            raw.verify()
        with Image.open(BytesIO(data), formats=(format_name,)) as reopened:
            exif = reopened.getexif()
            orientation = exif.get(ExifTags.Base.Orientation, 1)
            if type(orientation) is not int or not 1 <= orientation <= 8:
                raise InvalidImage("Invalid EXIF image orientation.")
            camera_exif = read_camera_exif(
                exif, size=reopened.size, orientation=orientation
            )
            upright = ImageOps.exif_transpose(reopened)
    except (Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise PixelLimitExceeded("Image exceeds the decoded pixel limit.") from exc
    except (OSError, SyntaxError, ValueError) as exc:
        raise InvalidImage("Image bytes could not be decoded.") from exc
    return NormalizedImage(
        upright, upright.width, upright.height, orientation, camera_exif
    )
