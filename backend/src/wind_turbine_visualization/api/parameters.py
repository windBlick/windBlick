"""Validate the visualization contract's JSON parameters independently of HTTP."""

import json
from datetime import datetime
from typing import Annotated, Literal, Self

from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    StringConstraints,
    ValidationError,
    field_validator,
    model_validator,
)
from pydantic_core import PydanticCustomError

from wind_turbine_visualization.api.problems import (
    FieldError,
    VisualizationProblem,
    invalid_parameter,
    pointer,
)

VERSION = "0.1"
MAX_TURBINES = 100
VERTICAL_DATUM = "DHHN2016_NHN"
OPERATING_LAYER = "erneuerbare_energien_wfs:Windenergieinbetrieb"
APPROVED_LAYER = "erneuerbare_energien_wfs:Windenergiegehnemigt"
STATUS_BY_LAYER = {OPERATING_LAYER: "operating", APPROVED_LAYER: "approved"}

Number = Annotated[float, Field(strict=True, allow_inf_nan=False)]
Positive = Annotated[Number, Field(gt=0)]
Nonnegative = Annotated[Number, Field(ge=0)]
Id = Annotated[str, StringConstraints(min_length=1, max_length=128)]
FeatureText = Annotated[str, StringConstraints(min_length=1, max_length=256)]
Name = Annotated[str, StringConstraints(min_length=1, max_length=200)]
ElevationSource = Literal["survey", "user_input", "fixture", "backend_model"]

POSITION_FIELDS = {"easting_m", "northing_m"}
GEOGRAPHIC_FIELDS = {"longitude_deg", "latitude_deg"}
INTRINSIC_FIELDS = {
    "horizontal_fov": ("horizontal_fov_deg",),
    "physical_focal_length": ("focal_length_mm", "sensor_width_mm", "sensor_height_mm"),
    "calibrated": ("fx_px", "fy_px", "cx_px", "cy_px"),
}


def _validate_timestamp(value: str) -> str:
    datetime.fromisoformat(value.upper())
    return value


Timestamp = Annotated[
    str,
    StringConstraints(
        pattern=(
            r"^[0-9]{4}-[0-9]{2}-[0-9]{2}[Tt][0-9]{2}:[0-9]{2}:[0-9]{2}"
            r"(\.[0-9]+)?([Zz]|[+-](0[0-9]|1[0-9]|2[0-3]):[0-5][0-9])$"
        ),
    ),
    AfterValidator(_validate_timestamp),
]


def _validate_datum(value: object) -> object:
    if value != VERTICAL_DATUM:
        raise PydanticCustomError(
            "unsupported_vertical_datum", "Use DHHN2016_NHN elevation."
        )
    return value


Datum = Annotated[Literal["DHHN2016_NHN"], BeforeValidator(_validate_datum)]


class _ParametersModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    @field_validator("*", mode="before")
    @classmethod
    def _reject_null(cls, value: object) -> object:
        if value is None:
            raise ValueError("Omit an unavailable value instead of sending null.")
        return value


class ImageAssertions(_ParametersModel):
    """Optional assertions about the orientation-normalized upload."""

    width_px: Annotated[int, Field(gt=0)] | None = None
    height_px: Annotated[int, Field(gt=0)] | None = None
    orientation: Literal["normalized"] | None = None
    captured_at: Timestamp | None = None


class CameraElevationOverride(_ParametersModel):
    """An optional explicit optical-centre elevation above NHN."""

    value_m: Number | None = None
    datum: Datum = VERTICAL_DATUM
    source: ElevationSource | Literal["exif"] = "user_input"
    uncertainty_m: Nonnegative | None = None


class CameraPositionOverride(_ParametersModel):
    """Partial EPSG:25832 or WGS84 camera coordinates and elevation."""

    easting_m: Number | None = None
    northing_m: Number | None = None
    longitude_deg: Annotated[Number, Field(ge=-180, le=180)] | None = None
    latitude_deg: Annotated[Number, Field(ge=-90, le=90)] | None = None
    elevation: CameraElevationOverride = Field(default_factory=CameraElevationOverride)

    @model_validator(mode="after")
    def _one_coordinate_system(self) -> Self:
        if (
            self.model_fields_set & POSITION_FIELDS
            and self.model_fields_set & GEOGRAPHIC_FIELDS
        ):
            raise ValueError("Use either projected or geographic camera coordinates.")
        return self


class OrientationOverrides(_ParametersModel):
    """Independent camera orientation overrides in degrees."""

    heading_deg: Annotated[Number, Field(ge=0, lt=360)] | None = None
    pitch_deg: Annotated[Number, Field(gt=-90, lt=90)] | None = None
    roll_deg: Annotated[Number, Field(ge=-180, lt=180)] | None = None
    north_reference: Literal["true"] = "true"


class IntrinsicsOverrides(_ParametersModel):
    """Partial values from one intrinsic family for the normalized raster."""

    kind: Literal["horizontal_fov", "physical_focal_length", "calibrated"] | None = None
    horizontal_fov_deg: Annotated[Number, Field(gt=0, lt=180)] | None = None
    focal_length_mm: Positive | None = None
    sensor_width_mm: Positive | None = None
    sensor_height_mm: Positive | None = None
    fx_px: Positive | None = None
    fy_px: Positive | None = None
    cx_px: Nonnegative | None = None
    cy_px: Nonnegative | None = None

    @property
    def family(self) -> str:
        """Return the selected family, defaulting to physical EXIF inputs."""
        if self.kind is not None:
            return self.kind
        return next(
            (
                kind
                for kind, fields in INTRINSIC_FIELDS.items()
                if self.model_fields_set.intersection(fields)
            ),
            "physical_focal_length",
        )

    @model_validator(mode="after")
    def _one_intrinsic_family(self) -> Self:
        if self.model_fields_set - {"kind", *INTRINSIC_FIELDS[self.family]}:
            raise ValueError("Supply values from only one camera intrinsic family.")
        return self


class CameraOverrides(_ParametersModel):
    """Explicit values override EXIF independently by field."""

    position: CameraPositionOverride = Field(default_factory=CameraPositionOverride)
    orientation: OrientationOverrides = Field(default_factory=OrientationOverrides)
    intrinsics: IntrinsicsOverrides = Field(default_factory=IntrinsicsOverrides)


class BaseElevation(_ParametersModel):
    """Absolute tower base elevation above NHN."""

    value_m: Number
    datum: Datum
    source: ElevationSource
    uncertainty_m: Nonnegative | None = None


class TurbinePosition(_ParametersModel):
    """EPSG:25832 tower base coordinates with DHHN2016 elevation."""

    easting_m: Number
    northing_m: Number
    elevation: BaseElevation


class TurbineSource(_ParametersModel):
    """Snapshot of the NRW WFS record's identifying metadata."""

    dataset: Literal["nrw_renewable_energies_wfs"]
    feature_type: Literal[
        "erneuerbare_energien_wfs:Windenergieinbetrieb",
        "erneuerbare_energien_wfs:Windenergiegehnemigt",
    ]
    feature_id: FeatureText
    retrieved_at: Timestamp
    raw_status: FeatureText
    unit_id: Id | None = None
    data_as_of: Id | None = None


class Turbine(_ParametersModel):
    """One turbine snapshot and the dimensions used for its schematic rendering."""

    id: Id
    name: Name | None = None
    position: TurbinePosition
    hub_height_m: Annotated[Number, Field(gt=0, lt=500)]
    rotor_diameter_m: Annotated[Number, Field(gt=0, lt=500)]
    turbine_type: Name | None = None
    status: Literal["operating", "approved"]
    source: TurbineSource


class Provenance(_ParametersModel):
    """Client-supplied origin information about a parameter."""

    source: Literal["exif", "device_sensor", "user_input", "wfs", "fixture", "derived"]
    observed_at: Timestamp | None = None
    note: Annotated[str, StringConstraints(min_length=1, max_length=500)] | None = None


class VisualizationParameters(_ParametersModel):
    """The transport model for one v0.1 visualization request."""

    api_version: Literal["0.1"]
    image: ImageAssertions = Field(default_factory=ImageAssertions)
    camera: CameraOverrides = Field(default_factory=CameraOverrides)
    turbines: Annotated[list[Turbine], Field(min_length=1, max_length=MAX_TURBINES)]
    provenance: Annotated[dict[str, Provenance], Field(max_length=256)] = Field(
        default_factory=dict
    )
    reference_points: Annotated[list[object], Field(max_length=0)] = Field(
        default_factory=list
    )


def _unique_properties(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON property")
        result[key] = value
    return result


def _non_json_number(_: str) -> None:
    raise ValueError("Nonstandard JSON number")


def _has_pointer(document: dict[str, object], path: str) -> bool:
    if not path.startswith("/"):
        return False
    parts = [part.replace("~1", "/").replace("~0", "~") for part in path[1:].split("/")]
    if parts[0] == "provenance" or pointer(parts) != path:
        return False
    current: object = document
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        elif (
            isinstance(current, list)
            and part.isascii()
            and part.isdecimal()
            and (part == "0" or not part.startswith("0"))
            and len(part) <= len(str(len(current)))
            and int(part) < len(current)
        ):
            current = current[int(part)]
        else:
            return False
    return True


def parse_parameters(raw: bytes) -> VisualizationParameters:
    """Read strict JSON, validate the schema, and check cross-record constraints."""
    try:
        document = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_unique_properties,
            parse_constant=_non_json_number,
        )
        # Reject unpaired UTF-16 escapes before paths or names reach the JSON response.
        json.dumps(document, ensure_ascii=False).encode("utf-8")
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise VisualizationProblem(
            400,
            "INVALID_JSON",
            "Parameters must be valid UTF-8 JSON with unique keys.",
            part="parameters",
        ) from exc

    if isinstance(document, dict):
        if "api_version" in document and document["api_version"] != VERSION:
            raise invalid_parameter(
                "/api_version",
                f"Use version {VERSION}.",
                code="UNSUPPORTED_API_VERSION",
            )
        if (
            isinstance(document.get("reference_points"), list)
            and document["reference_points"]
        ):
            raise invalid_parameter(
                "/reference_points",
                "Reference-point calibration is unavailable in v0.1.",
                code="FEATURE_NOT_SUPPORTED",
            )
        if (
            isinstance(document.get("turbines"), list)
            and len(document["turbines"]) > MAX_TURBINES
        ):
            raise VisualizationProblem(
                413,
                "TURBINE_LIMIT_EXCEEDED",
                f"Provide at most {MAX_TURBINES} turbines.",
            )

    try:
        parameters = VisualizationParameters.model_validate(document)
    except ValidationError as exc:
        errors: list[FieldError] = [
            {
                "path": pointer(error["loc"]),
                "code": error["type"].upper(),
                "message": error["msg"],
            }
            for error in exc.errors(
                include_input=False, include_context=False, include_url=False
            )
        ]
        code = (
            "UNSUPPORTED_VERTICAL_DATUM"
            if any(error["code"] == "UNSUPPORTED_VERTICAL_DATUM" for error in errors)
            else "VALIDATION_ERROR"
        )
        raise VisualizationProblem(
            422, code, "Check the visualization parameters.", errors=errors
        ) from exc

    ids: set[str] = set()
    features: set[tuple[str, str]] = set()
    for index, turbine in enumerate(parameters.turbines):
        prefix = f"/turbines/{index}"
        feature = (turbine.source.feature_type, turbine.source.feature_id)
        if turbine.status != STATUS_BY_LAYER[feature[0]]:
            raise invalid_parameter(
                f"{prefix}/status", "Status must match the selected WFS layer."
            )
        if turbine.id in ids:
            raise invalid_parameter(f"{prefix}/id", "Turbine IDs must be unique.")
        if feature in features:
            raise invalid_parameter(
                f"{prefix}/source/feature_id", "Select each WFS feature only once."
            )
        ids.add(turbine.id)
        features.add(feature)
    for path in parameters.provenance:
        if not _has_pointer(document, path):
            raise invalid_parameter(
                pointer(("provenance", path)),
                "Provenance must point to a submitted parameter.",
            )
    return parameters
