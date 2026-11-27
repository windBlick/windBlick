"""HTTP-level tests for the image upload endpoint.

Exercises the multipart upload, orientation normalization, and the
contract error mapping (413 / 415 / 422) through the FastAPI app. Images are
generated in memory so no private photos or EXIF are committed.
"""

from io import BytesIO

import pytest
from PIL import Image

from wind_turbine_visualization.api.routes import visualizations
from wind_turbine_visualization.image import normalization

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
        files={"image": ("photo.png", b"\x89PNG\r\n\x1a\n", "image/png")},
    )

    assert response.status_code == 422
    assert response.json()["code"] == "INVALID_IMAGE"


@pytest.mark.parametrize("actual_format", ["JPEG", "TIFF"])
def test_upload_checks_actual_format(client, actual_format):
    """A valid raster sent as the wrong type is rejected."""
    buffer = BytesIO()
    Image.new("RGB", (3, 2)).save(buffer, format=actual_format)
    response = client.post(
        "/api/v0/visualizations",
        files={"image": ("photo.png", buffer.getvalue(), "image/png")},
    )
    assert response.status_code == 415
    assert response.json()["code"] == "UNSUPPORTED_IMAGE_TYPE"


def test_upload_rejects_animated_png(client):
    """APNG is not a supported still image."""
    buffer = BytesIO()
    first = Image.new("RGB", (3, 2), "red")
    second = Image.new("RGB", (3, 2), "blue")
    first.save(buffer, format="PNG", save_all=True, append_images=[second])
    response = client.post(
        "/api/v0/visualizations",
        files={"image": ("photo.png", buffer.getvalue(), "image/png")},
    )
    assert response.status_code == 415
    assert response.json()["code"] == "UNSUPPORTED_IMAGE_TYPE"


def test_upload_rejects_invalid_orientation(client):
    """An undefined EXIF orientation yields a client error."""
    response = client.post(
        "/api/v0/visualizations",
        files={
            "image": ("photo.jpg", _jpeg_bytes_with_orientation(4, 2, 9), "image/jpeg")
        },
    )
    assert response.status_code == 422
    assert response.json()["code"] == "INVALID_IMAGE"


def test_upload_image_byte_limit(client, monkeypatch):
    """A file at the limit is accepted and one byte over is rejected."""
    data = _png_bytes(3, 2)
    monkeypatch.setattr(visualizations, "MAX_IMAGE_BYTES", len(data))
    accepted = client.post(
        "/api/v0/visualizations", files={"image": ("photo.png", data, "image/png")}
    )
    rejected = client.post(
        "/api/v0/visualizations",
        files={"image": ("photo.png", data + b"0", "image/png")},
    )
    assert accepted.status_code == 200
    assert rejected.status_code == 413
    assert rejected.json()["code"] == "IMAGE_TOO_LARGE"


def test_upload_request_limit_counts_body_before_parsing(client, monkeypatch):
    """Reject the entire multipart body even without a length header."""
    monkeypatch.setattr(visualizations, "MAX_REQUEST_BYTES", 32)
    response = client.post(
        "/api/v0/visualizations",
        headers={"Content-Type": "multipart/form-data; boundary=upload"},
        content=iter(
            [b"--upload\r\n", b'Content-Disposition: form-data; name="image"\r\n']
        ),
    )
    assert "content-length" not in response.request.headers
    assert response.status_code == 413
    assert response.json()["code"] == "REQUEST_TOO_LARGE"


@pytest.mark.parametrize("pillow_limit", [False, True])
def test_upload_pixel_limit(client, monkeypatch, pillow_limit):
    """The project's and Pillow's pixel limits both return 413."""
    if pillow_limit:
        monkeypatch.setattr(Image, "MAX_IMAGE_PIXELS", 2)
    else:
        monkeypatch.setattr(normalization, "MAX_DECODED_PIXELS", 5)
    response = client.post(
        "/api/v0/visualizations",
        files={"image": ("photo.png", _png_bytes(3, 2), "image/png")},
    )
    assert response.status_code == 413
    assert response.json()["code"] == "PIXEL_LIMIT_EXCEEDED"


def test_missing_image_part_is_rejected(client):
    """Omitting the image part is a validation error."""
    response = client.post("/api/v0/visualizations")

    assert response.status_code == 422
