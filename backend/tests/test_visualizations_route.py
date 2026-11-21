"""HTTP-level tests for the image upload endpoint.

Exercises the multipart upload, orientation normalization, and the
contract error mapping (415 / 422) through the FastAPI app. Images are
generated in memory so no private photos or EXIF are committed.
"""

from io import BytesIO

from PIL import Image

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


def test_upload_png_returns_dimensions(client):
    """A valid PNG returns 200 with its normalized dimensions."""
    response = client.post(
        "/api/v0/visualizations",
        files={"image": ("photo.png", _png_bytes(30, 20), "image/png")},
    )

    assert response.status_code == 200
    assert response.json() == {"image": {"width_px": 30, "height_px": 20}}


def test_upload_jpeg_orientation_6_swaps_dimensions(client):
    """Orientation 6 swaps width/height in the normalized response."""
    data = _jpeg_bytes_with_orientation(40, 10, orientation=6)

    response = client.post(
        "/api/v0/visualizations",
        files={"image": ("photo.jpg", data, "image/jpeg")},
    )

    assert response.status_code == 200
    assert response.json() == {"image": {"width_px": 10, "height_px": 40}}


def test_upload_unsupported_type_returns_415(client):
    """An unsupported media type is intercepted with 415."""
    response = client.post(
        "/api/v0/visualizations",
        files={"image": ("clip.gif", b"ignored", "image/gif")},
    )

    assert response.status_code == 415
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["code"] == "UNSUPPORTED_IMAGE_TYPE"


def test_upload_undecodable_bytes_returns_422(client):
    """Bytes that are not a real image are rejected with 422."""
    response = client.post(
        "/api/v0/visualizations",
        files={"image": ("photo.png", b"not an image", "image/png")},
    )

    assert response.status_code == 422
    assert response.json()["code"] == "INVALID_IMAGE"


def test_missing_image_part_is_rejected(client):
    """Omitting the image part is a validation error."""
    response = client.post("/api/v0/visualizations")

    assert response.status_code == 422
