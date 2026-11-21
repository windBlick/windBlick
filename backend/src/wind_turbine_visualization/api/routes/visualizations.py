"""Upload endpoint for the visualization pipeline.

B1 scope: accept the multipart ``image`` part, normalize EXIF orientation,
and report the normalized image dimensions. Camera-parameter resolution,
turbine rendering, and the final PNG response are added by later issues;
until then this route returns the normalized dimensions as an interim
diagnostic so the upload and rejection behaviour is reachable over HTTP.

Only this layer imports FastAPI. All decoding logic lives in the
framework-free ``wind_turbine_visualization.image`` package.
"""

from fastapi import APIRouter, UploadFile
from fastapi.responses import JSONResponse

from wind_turbine_visualization.image import (
    InvalidImage,
    UnsupportedImageType,
    load_normalized_image,
)

router = APIRouter(prefix="/api/v0", tags=["visualizations"])

MAX_IMAGE_BYTES = 20 * 1024 * 1024  # 20 MiB, contract draft resource limit


def _problem(status_code: int, code: str, detail: str) -> JSONResponse:
    """Build an RFC 9457 ``application/problem+json`` error response.

    Args:
        status_code: HTTP status code.
        code: Stable application error code from the API contract.
        detail: Human-readable, non-sensitive explanation.

    Returns:
        A JSON response using the ``application/problem+json`` media type.
    """
    return JSONResponse(
        status_code=status_code,
        media_type="application/problem+json",
        content={
            "type": "about:blank",
            "title": code.replace("_", " ").title(),
            "status": status_code,
            "code": code,
            "detail": detail,
            "errors": [],
        },
    )


@router.post("/visualizations")
async def create_visualization(image: UploadFile) -> JSONResponse:
    """Accept an uploaded image and return its normalized dimensions.

    Args:
        image: The multipart ``image`` part (JPEG or PNG).

    Returns:
        ``200`` with the orientation-normalized width/height on success, or a
        problem response: ``413`` if too large, ``415`` for an unsupported
        media type, ``422`` if the bytes cannot be decoded.
    """
    data = await image.read()
    if len(data) > MAX_IMAGE_BYTES:
        return _problem(
            413, "IMAGE_TOO_LARGE", "Image exceeds the 20 MiB upload limit."
        )
    try:
        result = load_normalized_image(data, image.content_type or "")
    except UnsupportedImageType as exc:
        return _problem(415, exc.code, str(exc))
    except InvalidImage as exc:
        return _problem(422, exc.code, str(exc))
    return JSONResponse(
        status_code=200,
        content={
            "image": {
                "width_px": result.width_px,
                "height_px": result.height_px,
            }
        },
    )
