"""Merge camera overrides with usable EXIF and track their origins."""

from dataclasses import dataclass
from typing import Literal, TypedDict

from pyproj.exceptions import ProjError

from wind_turbine_visualization.api.parameters import (
    INTRINSIC_FIELDS,
    POSITION_FIELDS,
    CameraOverrides,
    CameraPositionOverride,
    IntrinsicsOverrides,
)
from wind_turbine_visualization.api.problems import (
    FieldError,
    VisualizationProblem,
    invalid_parameter,
)
from wind_turbine_visualization.camera.projection import (
    CameraIntrinsics,
    CameraProjection,
)
from wind_turbine_visualization.geo.coordinates import ProjectedPosition
from wind_turbine_visualization.image.camera_exif import CameraExif, ExifValue
from wind_turbine_visualization.image.normalization import NormalizedImage

POSITION = "/camera/position"
ORIENTATION = "/camera/orientation"
INTRINSICS = "/camera/intrinsics"


class ValueSource(TypedDict, total=False):
    """Source of one effective numeric value in the response."""

    source: Literal["override", "exif", "derived"]
    input_paths: list[str]
    exif_tags: list[str]


@dataclass(frozen=True)
class _Value:
    number: float
    origin: ValueSource


@dataclass(frozen=True)
class ResolvedCamera:
    """Camera objects for rendering, plus the effective response values."""

    position: ProjectedPosition
    projection: CameraProjection
    used: dict[str, object]
    sources: dict[str, ValueSource]


def _derived(*inputs: _Value) -> ValueSource:
    result: ValueSource = {"source": "derived"}
    for key in ("input_paths", "exif_tags"):
        values = list(
            dict.fromkeys(
                item for field in inputs for item in field.origin.get(key, [])
            )
        )
        if values:
            result[key] = values
    return result


def _resolve(
    path: str,
    override: float | None,
    exif: ExifValue | None,
    missing: list[FieldError],
    hint: str,
) -> _Value | None:
    if override is not None:
        return _Value(override, {"source": "override", "input_paths": [path]})
    if exif is not None:
        return _from_exif(exif)
    missing.append({"path": path, "code": "EXIF_MISSING_OR_UNUSABLE", "message": hint})
    return None


def _from_exif(exif: ExifValue) -> _Value:
    return _Value(exif.value, {"source": "exif", "exif_tags": list(exif.tags)})


def _project_gps(longitude: _Value, latitude: _Value) -> dict[str, _Value]:
    try:
        point = ProjectedPosition.from_wgs84(
            longitude_deg=longitude.number, latitude_deg=latitude.number, elevation_m=0
        )
    except (ProjError, ValueError) as exc:
        raise invalid_parameter(
            POSITION, "Camera coordinates could not be projected to EPSG:25832."
        ) from exc
    origin = _derived(longitude, latitude)
    return {
        "easting_m": _Value(point.easting_m, origin),
        "northing_m": _Value(point.northing_m, origin),
    }


def _resolve_horizontal(
    position: CameraPositionOverride, exif: CameraExif, missing: list[FieldError]
) -> dict[str, _Value]:
    if position.model_fields_set & POSITION_FIELDS:
        from_exif: dict[str, _Value] = {}
        if (
            (position.easting_m is None or position.northing_m is None)
            and exif.longitude_deg
            and exif.latitude_deg
        ):
            from_exif = _project_gps(
                _from_exif(exif.longitude_deg), _from_exif(exif.latitude_deg)
            )
        result: dict[str, _Value] = {}
        for axis in ("easting_m", "northing_m"):
            override = getattr(position, axis)
            value = from_exif.get(axis) if override is None else None
            if value is None:
                value = _resolve(
                    f"{POSITION}/{axis}",
                    override,
                    None,
                    missing,
                    "Provide this EPSG:25832 axis or usable GPS coordinates.",
                )
            if value is not None:
                result[axis] = value
        return result

    longitude = _resolve(
        f"{POSITION}/longitude_deg",
        position.longitude_deg,
        exif.longitude_deg,
        missing,
        "Provide a camera longitude in WGS84 or supply both projected axes.",
    )
    latitude = _resolve(
        f"{POSITION}/latitude_deg",
        position.latitude_deg,
        exif.latitude_deg,
        missing,
        "Provide a camera latitude in WGS84 or supply both projected axes.",
    )
    return _project_gps(longitude, latitude) if longitude and latitude else {}


def _resolve_intrinsics(
    overrides: IntrinsicsOverrides, image: NormalizedImage, missing: list[FieldError]
) -> tuple[CameraIntrinsics | None, dict[str, ValueSource]]:
    width, height = image.width_px, image.height_px
    for axis, size in (("cx_px", width), ("cy_px", height)):
        value = getattr(overrides, axis)
        if value is not None and value > size - 1:
            raise invalid_parameter(
                f"{INTRINSICS}/{axis}",
                "The principal point must be inside the normalized image.",
            )

    family = overrides.family
    fields = INTRINSIC_FIELDS[family]
    values: dict[str, _Value] = {}
    for field in fields:
        value = _resolve(
            f"{INTRINSICS}/{field}",
            getattr(overrides, field),
            getattr(image.camera_exif, field, None),
            missing,
            f"Provide {field} or choose a complete intrinsic variant.",
        )
        if value is not None:
            values[field] = value
    if len(values) != len(fields):
        return None, {}

    numbers = {field: value.number for field, value in values.items()}
    raster = {"width_px": width, "height_px": height}
    try:
        if family == "calibrated":
            return CameraIntrinsics(**raster, **numbers), {
                key: value.origin for key, value in values.items()
            }
        if family == "horizontal_fov":
            intrinsics = CameraIntrinsics.from_horizontal_fov(**raster, **numbers)
            x_source = y_source = _derived(values["horizontal_fov_deg"])
        else:
            intrinsics = CameraIntrinsics.from_physical_focal_length(
                **raster, **numbers
            )
            focal = values["focal_length_mm"]
            x_source = _derived(focal, values["sensor_width_mm"])
            y_source = _derived(focal, values["sensor_height_mm"])
    except (ValueError, OverflowError, ZeroDivisionError) as exc:
        raise invalid_parameter(
            INTRINSICS, "These values cannot describe usable camera intrinsics."
        ) from exc
    return intrinsics, {
        "fx_px": x_source,
        "fy_px": y_source,
        "cx_px": {"source": "derived"},
        "cy_px": {"source": "derived"},
    }


def resolve_camera(
    overrides: CameraOverrides, image: NormalizedImage
) -> ResolvedCamera:
    """Resolve every required camera value or report all missing values."""
    missing: list[FieldError] = []
    horizontal = _resolve_horizontal(overrides.position, image.camera_exif, missing)
    elevation_override = overrides.position.elevation
    elevation = _resolve(
        f"{POSITION}/elevation/value_m",
        elevation_override.value_m,
        None,
        missing,
        "Provide the optical-centre elevation in DHHN2016 NHN. "
        "Raw GPS altitude does not establish this datum.",
    )
    angles = {}
    for field, hint in (
        ("heading_deg", "Provide a true-north heading or usable EXIF image direction."),
        ("pitch_deg", "Provide the camera pitch in degrees, positive upwards."),
        ("roll_deg", "Provide the camera roll in degrees."),
    ):
        value = _resolve(
            f"{ORIENTATION}/{field}",
            getattr(overrides.orientation, field),
            getattr(image.camera_exif, field, None),
            missing,
            hint,
        )
        if value is not None:
            angles[field] = value
    intrinsics, intrinsic_origins = _resolve_intrinsics(
        overrides.intrinsics, image, missing
    )
    if missing:
        raise VisualizationProblem(
            422,
            "CAMERA_PARAMETERS_UNRESOLVED",
            "Camera parameters could not be resolved from overrides and EXIF.",
            errors=missing,
        )
    assert elevation is not None and intrinsics is not None

    coordinates = {axis: value.number for axis, value in horizontal.items()}
    orientation = {field: value.number for field, value in angles.items()}
    position = ProjectedPosition(**coordinates, elevation_m=elevation.number)
    projection = CameraProjection(**orientation, intrinsics=intrinsics)
    used = {
        "position": {
            **coordinates,
            "elevation": elevation_override.model_dump(exclude_none=True),
        },
        "orientation": {**orientation, "north_reference": "true"},
        "intrinsics": {name: getattr(intrinsics, name) for name in intrinsic_origins},
    }
    sources = {
        **{f"/position/{axis}": value.origin for axis, value in horizontal.items()},
        "/position/elevation/value_m": elevation.origin,
        **{f"/orientation/{field}": value.origin for field, value in angles.items()},
        **{
            f"/intrinsics/{field}": origin
            for field, origin in intrinsic_origins.items()
        },
    }
    if elevation_override.uncertainty_m is not None:
        sources["/position/elevation/uncertainty_m"] = {
            "source": "override",
            "input_paths": [f"{POSITION}/elevation/uncertainty_m"],
        }
    return ResolvedCamera(position, projection, used, sources)
