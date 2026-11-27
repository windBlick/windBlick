"""Tests for image decoding and EXIF-orientation normalization.

All fixtures are generated in memory with Pillow so the tests are
deterministic and no private photos or EXIF are committed.
"""

from io import BytesIO

import pytest
from PIL import ExifTags, Image

from wind_turbine_visualization.image import (
    InvalidImage,
    UnsupportedImageType,
    load_normalized_image,
)

EXIF_ORIENTATION_TAG = 274  # standard EXIF Orientation tag id


def _png_bytes(width_px: int, height_px: int) -> bytes:
    """Return PNG bytes of a solid image with the given dimensions."""
    image = Image.new("RGB", (width_px, height_px), color=(120, 120, 120))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _jpeg_bytes_with_orientation(
    width_px: int, height_px: int, orientation: int
) -> bytes:
    """Return JPEG bytes tagged with the given EXIF orientation value."""
    image = Image.new("RGB", (width_px, height_px), color=(200, 100, 50))
    exif = image.getexif()
    exif[EXIF_ORIENTATION_TAG] = orientation
    buffer = BytesIO()
    image.save(buffer, format="JPEG", exif=exif)
    return buffer.getvalue()


def test_png_reports_correct_dimensions():
    """A PNG with no orientation is returned at its stored size."""
    result = load_normalized_image(_png_bytes(30, 20), "image/png")

    assert result.width_px == 30
    assert result.height_px == 20


def test_jpeg_orientation_6_swaps_dimensions():
    """Orientation 6 (rotate 90 deg) swaps width and height after normalization."""
    data = _jpeg_bytes_with_orientation(40, 10, orientation=6)

    result = load_normalized_image(data, "image/jpeg")

    assert result.width_px == 10
    assert result.height_px == 40


@pytest.mark.parametrize(
    ("orientation", "size", "red_corner"),
    [(2, (3, 2), (2, 0)), (6, (2, 3), (1, 0))],
)
def test_orientation_moves_pixels(orientation, size, red_corner):
    """The image is mirrored or rotated in the expected direction."""
    image = Image.new("RGB", (3, 2))
    image.putpixel((0, 0), (255, 0, 0))
    exif = image.getexif()
    exif[ExifTags.Base.Orientation] = orientation
    buffer = BytesIO()
    image.save(buffer, format="PNG", exif=exif)

    result = load_normalized_image(buffer.getvalue(), "image/png")

    assert result.image.size == size
    assert result.image.getpixel(red_corner) == (255, 0, 0)
    assert ExifTags.Base.Orientation not in result.image.getexif()


def test_unsupported_media_type_is_rejected():
    """A declared type outside JPEG/PNG raises UnsupportedImageType."""
    with pytest.raises(UnsupportedImageType):
        load_normalized_image(b"ignored", "image/gif")


def test_undecodable_bytes_raise_invalid_image():
    """Bytes that are not a real image raise InvalidImage."""
    with pytest.raises(InvalidImage):
        load_normalized_image(b"\x89PNG\r\n\x1a\n", "image/png")
