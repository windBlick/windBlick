"""Prepare a rendering request and serialize the result for the API."""

from base64 import b64encode
from io import BytesIO

from pyproj.exceptions import ProjError

from wind_turbine_visualization.api.camera_resolution import resolve_camera
from wind_turbine_visualization.api.multipart import VisualizationUpload
from wind_turbine_visualization.api.parameters import (
    VERSION,
    VisualizationParameters,
    parse_parameters,
)
from wind_turbine_visualization.api.problems import (
    VisualizationProblem,
    invalid_parameter,
)
from wind_turbine_visualization.geo.coordinates import LocalFrame, ProjectedPosition
from wind_turbine_visualization.image import (
    InvalidImage,
    PixelLimitExceeded,
    UnsupportedImageType,
    load_normalized_image,
)
from wind_turbine_visualization.image.normalization import NormalizedImage
from wind_turbine_visualization.rendering.overlay import (
    OVERLAY_COLOR_HEX,
    TurbinePlacement,
    render_turbine_overlay,
)
from wind_turbine_visualization.rendering.turbine_geometry import TurbineGeometry

MAX_PNG_BYTES = 40 * 1024 * 1024


class _PngBuffer(BytesIO):
    def write(self, data: bytes) -> int:
        if self.tell() + len(data) > MAX_PNG_BYTES:
            raise VisualizationProblem(
                503,
                "OUTPUT_LIMIT_EXCEEDED",
                "The output PNG is too large. Try a smaller photo.",
            )
        return super().write(data)


def _load_image(upload: VisualizationUpload) -> NormalizedImage:
    try:
        return load_normalized_image(upload.image, upload.mime_type)
    except UnsupportedImageType as exc:
        raise VisualizationProblem(415, exc.code, str(exc), part="image") from exc
    except PixelLimitExceeded as exc:
        raise VisualizationProblem(413, exc.code, str(exc), part="image") from exc
    except InvalidImage as exc:
        raise VisualizationProblem(422, exc.code, str(exc), part="image") from exc


def _check_image(parameters: VisualizationParameters, image: NormalizedImage) -> None:
    if parameters.image.orientation == "normalized" and image.original_orientation != 1:
        raise invalid_parameter(
            "/image/orientation",
            "The original EXIF orientation requires image normalization.",
            code="IMAGE_NOT_NORMALIZED",
        )
    for field in ("width_px", "height_px"):
        claimed = getattr(parameters.image, field)
        if claimed is not None and claimed != getattr(image, field):
            raise invalid_parameter(
                f"/image/{field}",
                "The asserted dimension does not match the normalized image.",
                code="IMAGE_DIMENSION_MISMATCH",
            )


def render_visualization(
    upload: VisualizationUpload, request_id: str
) -> dict[str, object]:
    """Validate the upload and return a rendered PNG with diagnostics."""
    parameters = parse_parameters(upload.parameters)
    image = _load_image(upload)
    with image.image:
        _check_image(parameters, image)
        camera = resolve_camera(parameters.camera, image)
        try:
            local_frame = LocalFrame(camera.position)
        except (ProjError, ValueError) as exc:
            raise invalid_parameter(
                "/camera/position",
                "Camera position cannot define a local frame in EPSG:25832.",
            ) from exc
        placements = [
            TurbinePlacement(
                base=ProjectedPosition(
                    easting_m=turbine.position.easting_m,
                    northing_m=turbine.position.northing_m,
                    elevation_m=turbine.position.elevation.value_m,
                ),
                geometry=TurbineGeometry(
                    hub_height_meters=turbine.hub_height_m,
                    rotor_diameter_meters=turbine.rotor_diameter_m,
                ),
            )
            for turbine in parameters.turbines
        ]
        overlay = render_turbine_overlay(
            image.image,
            local_frame=local_frame,
            camera=camera.projection,
            turbines=placements,
        )
        with overlay.image, _PngBuffer() as buffer:
            overlay.image.save(buffer, format="PNG")
            encoded = b64encode(buffer.getbuffer()).decode("ascii")

    warnings = [
        {
            "code": "PINHOLE_APPROXIMATION",
            "message": "The projection assumes a distortion-free pinhole camera.",
        },
        {
            "code": "SCHEMATIC_ROTOR_ORIENTATION",
            "message": "The rotor facing and blade positions are schematic.",
        },
    ]
    outcome_warnings = {
        "outside_frame": (
            "TURBINE_OUTSIDE_FRAME",
            "Turbine geometry is outside the photo.",
        ),
        "behind_camera": (
            "TURBINE_BEHIND_CAMERA",
            "Turbine geometry is behind the camera.",
        ),
    }
    turbines = []
    for index, (turbine, result) in enumerate(
        zip(parameters.turbines, overlay.turbines, strict=True)
    ):
        description = {
            "id": turbine.id,
            "label": turbine.name or f"Turbine {index + 1}",
            "status": turbine.status,
            "source": turbine.source.model_dump(exclude_none=True),
            "outcome": result.outcome,
            "style": {"color_hex": OVERLAY_COLOR_HEX, "category": "uniform"},
        }
        if result.projected_hub_px is not None:
            x, y = result.projected_hub_px
            description["projected_hub_px"] = {"x_px": x, "y_px": y}
        turbines.append(description)
        if result.outcome in outcome_warnings:
            code, message = outcome_warnings[result.outcome]
            warnings.append(
                {
                    "code": code,
                    "message": message,
                    "path": f"/turbines/{index}",
                    "turbine_id": turbine.id,
                }
            )
    if all(result.outcome != "drawn" for result in overlay.turbines):
        warnings.append(
            {
                "code": "NO_TURBINES_DRAWN",
                "message": "No selected turbines intersect the photo.",
            }
        )

    return {
        "api_version": VERSION,
        "request_id": request_id,
        "image": {
            "mime_type": "image/png",
            "encoding": "base64",
            "data": encoded,
            "width_px": image.width_px,
            "height_px": image.height_px,
        },
        "camera_used": camera.used,
        "camera_value_sources": camera.sources,
        "turbines": turbines,
        "warnings": warnings,
        "calibration": {"applied": False},
    }
