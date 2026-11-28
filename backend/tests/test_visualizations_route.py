"""Test the visualization API through HTTP and the real line renderer."""

import base64
import json
from collections.abc import Callable
from copy import deepcopy
from io import BytesIO
from typing import Any

import pytest
from fastapi.testclient import TestClient
from PIL import ExifTags, Image
from PIL.TiffImagePlugin import IFDRational

from wind_turbine_visualization.api import multipart, visualization
from wind_turbine_visualization.api.routes import visualizations
from wind_turbine_visualization.geo.coordinates import ProjectedPosition
from wind_turbine_visualization.image import normalization

URL = "/api/v0/visualizations"
PNG_TYPE = "image/png"
JPEG_TYPE = "image/jpeg"
RASTER_SIZE = (101, 101)
Parameters = dict[str, Any]


@pytest.fixture
def parameters() -> Parameters:
    return {
        "api_version": "0.1",
        "camera": {
            "position": {
                "easting_m": 500_000,
                "northing_m": 5_761_000,
                "elevation": {"value_m": 75},
            },
            "orientation": {"heading_deg": 0, "pitch_deg": 0, "roll_deg": 0},
            "intrinsics": {"fx_px": 100, "fy_px": 100, "cx_px": 50, "cy_px": 50},
        },
        "turbines": [
            {
                "id": "test-turbine",
                "position": {
                    "easting_m": 500_000,
                    "northing_m": 5_761_100,
                    "elevation": {
                        "value_m": 75,
                        "datum": "DHHN2016_NHN",
                        "source": "fixture",
                    },
                },
                "hub_height_m": 30,
                "rotor_diameter_m": 20,
                "status": "operating",
                "source": {
                    "dataset": "nrw_renewable_energies_wfs",
                    "feature_type": "erneuerbare_energien_wfs:Windenergieinbetrieb",
                    "feature_id": "Windenergieinbetrieb.fixture",
                    "retrieved_at": "2026-11-19T08:00:00Z",
                    "raw_status": "In Betrieb",
                },
            }
        ],
    }


def _raster(
    size: tuple[int, int] = RASTER_SIZE,
    *,
    fmt: str = "PNG",
    exif: Image.Exif | None = None,
) -> bytes:
    with Image.new("RGB", size, "white") as image, BytesIO() as buffer:
        image.save(buffer, format=fmt, **({"exif": exif} if exif is not None else {}))
        return buffer.getvalue()


def _parts(
    parameters: Parameters | bytes,
    image: bytes | None = None,
    mime_type: str = PNG_TYPE,
) -> list[tuple[str, tuple[str | None, bytes, str]]]:
    return [
        ("image", ("photo", _raster() if image is None else image, mime_type)),
        (
            "parameters",
            (
                None,
                json.dumps(parameters).encode()
                if isinstance(parameters, dict)
                else parameters,
                "application/json",
            ),
        ),
    ]


def _jpeg_with_camera_exif(
    *, orientation: int = 1, north_reference: str = "T", datum: str | None = "WGS-84"
) -> bytes:
    size = (100, 80)
    exif = Image.Exif()
    exif[ExifTags.Base.Orientation] = orientation
    exif[ExifTags.Base.ImageDescription] = "Private fixture metadata"
    gps = {
        ExifTags.GPS.GPSLongitudeRef: "E",
        ExifTags.GPS.GPSLongitude: (IFDRational(9), IFDRational(0), IFDRational(0)),
        ExifTags.GPS.GPSLatitudeRef: "N",
        ExifTags.GPS.GPSLatitude: (IFDRational(52), IFDRational(0), IFDRational(0)),
        ExifTags.GPS.GPSImgDirectionRef: north_reference,
        ExifTags.GPS.GPSImgDirection: IFDRational(17),
        ExifTags.GPS.GPSAltitudeRef: b"\0",
        ExifTags.GPS.GPSAltitude: IFDRational(11333, 100),
    }
    if datum is not None:
        gps[ExifTags.GPS.GPSMapDatum] = datum
    exif[ExifTags.IFD.GPSInfo] = gps
    exif[ExifTags.IFD.Exif] = {
        ExifTags.Base.FocalLength: IFDRational(10),
        ExifTags.Base.ExifImageWidth: size[0],
        ExifTags.Base.ExifImageHeight: size[1],
        ExifTags.Base.FocalPlaneXResolution: IFDRational(200),
        ExifTags.Base.FocalPlaneYResolution: IFDRational(400),
        ExifTags.Base.FocalPlaneResolutionUnit: 3,
    }
    return _raster(size, fmt="JPEG", exif=exif)


def test_upload_renders_png_with_style_and_effective_camera(
    client: TestClient, parameters: Parameters
) -> None:
    response = client.post(URL, files=_parts(parameters))
    assert response.status_code == 200, response.json()
    assert response.headers["cache-control"] == "no-store"
    data = response.json()
    assert data["api_version"] == "0.1" and data["request_id"]
    assert data["calibration"] == {"applied": False}
    assert (
        data["image"]["mime_type"] == PNG_TYPE and data["image"]["encoding"] == "base64"
    )
    assert (data["image"]["width_px"], data["image"]["height_px"]) == RASTER_SIZE
    with Image.open(
        BytesIO(base64.b64decode(data["image"]["data"], validate=True))
    ) as image:
        assert image.format == "PNG" and image.size == RASTER_SIZE
        assert image.getpixel((50, 20)) == (37, 99, 235)
        assert image.getpixel((0, 0)) == (255, 255, 255)
        assert not image.getexif()
    turbine = data["turbines"][0]
    assert turbine["outcome"] == "drawn"
    assert turbine["projected_hub_px"] == {"x_px": 50, "y_px": 20}
    assert turbine["label"] == "Turbine 1"
    assert turbine["style"] == {"category": "uniform", "color_hex": "#2563EB"}
    assert data["camera_used"]["position"]["elevation"]["datum"] == "DHHN2016_NHN"
    assert data["camera_value_sources"]["/orientation/roll_deg"] == {
        "source": "override",
        "input_paths": ["/camera/orientation/roll_deg"],
    }


def test_offscreen_turbines_are_reported_in_request_order(
    client: TestClient, parameters: Parameters
) -> None:
    behind = parameters["turbines"][0]
    behind["position"]["northing_m"] = 5_760_900
    outside = deepcopy(behind)
    outside["id"] = "outside"
    outside["source"]["feature_id"] = "fixture-outside"
    outside["position"].update(easting_m=500_300, northing_m=5_761_100)
    parameters["turbines"].append(outside)
    response = client.post(URL, files=_parts(parameters))
    assert response.status_code == 200
    data = response.json()
    assert [t["outcome"] for t in data["turbines"]] == [
        "behind_camera",
        "outside_frame",
    ]
    assert "projected_hub_px" not in data["turbines"][0]
    assert data["turbines"][1]["projected_hub_px"]["x_px"] == pytest.approx(350)
    assert {warning["code"] for warning in data["warnings"]} >= {
        "TURBINE_BEHIND_CAMERA",
        "TURBINE_OUTSIDE_FRAME",
        "NO_TURBINES_DRAWN",
    }


@pytest.mark.parametrize(
    "position_override", [{"longitude_deg": 9.001}, {"easting_m": 500_100}, {}]
)
def test_merges_exif_and_partial_camera_overrides(
    client: TestClient, parameters: Parameters, position_override: Parameters
) -> None:
    parameters["camera"] = {
        "position": {"elevation": {"value_m": 75}, **position_override},
        "orientation": {"pitch_deg": 0, "roll_deg": 0},
        "intrinsics": {"focal_length_mm": 6},
    }
    response = client.post(
        URL, files=_parts(parameters, _jpeg_with_camera_exif(), JPEG_TYPE)
    )
    assert response.status_code == 200, response.json()
    data = response.json()
    camera, sources = data["camera_used"], data["camera_value_sources"]
    point = ProjectedPosition.from_wgs84(
        latitude_deg=52,
        longitude_deg=position_override.get("longitude_deg", 9),
        elevation_m=75,
    )
    assert camera["position"]["easting_m"] == pytest.approx(
        position_override.get("easting_m", point.easting_m)
    )
    assert camera["position"]["northing_m"] == pytest.approx(point.northing_m)
    assert camera["orientation"]["heading_deg"] == 17
    assert camera["orientation"]["pitch_deg"] == 0
    assert camera["intrinsics"] == {
        "fx_px": 120,
        "fy_px": 240,
        "cx_px": 49.5,
        "cy_px": 39.5,
    }
    assert sources["/position/easting_m"]["source"] == (
        "override" if "easting_m" in position_override else "derived"
    )
    assert "GPSLatitude" in sources["/position/northing_m"]["exif_tags"]
    assert sources["/orientation/heading_deg"]["source"] == "exif"
    assert sources["/intrinsics/fx_px"]["input_paths"] == [
        "/camera/intrinsics/focal_length_mm"
    ]
    assert "FocalPlaneXResolution" in sources["/intrinsics/fx_px"]["exif_tags"]
    assert "FocalLength" not in sources["/intrinsics/fx_px"]["exif_tags"]
    with Image.open(BytesIO(base64.b64decode(data["image"]["data"]))) as image:
        assert not image.getexif()


@pytest.mark.parametrize("orientation", [5, 6])
def test_rotated_and_reflected_photo_uses_normalized_exif_intrinsics(
    client: TestClient, parameters: Parameters, orientation: int
) -> None:
    parameters["camera"]["intrinsics"] = {}
    parameters["image"] = {"width_px": 80, "height_px": 100}
    image = _jpeg_with_camera_exif(orientation=orientation)
    response = client.post(URL, files=_parts(parameters, image, JPEG_TYPE))
    assert response.status_code == 200, response.json()
    data = response.json()
    assert (data["image"]["width_px"], data["image"]["height_px"]) == (80, 100)
    assert data["camera_used"]["intrinsics"] == {
        "fx_px": 400,
        "fy_px": 200,
        "cx_px": 39.5,
        "cy_px": 49.5,
    }
    assert (
        "Orientation" in data["camera_value_sources"]["/intrinsics/fx_px"]["exif_tags"]
    )
    parameters["image"]["orientation"] = "normalized"
    assert (
        client.post(URL, files=_parts(parameters, image, JPEG_TYPE)).json()["code"]
        == "IMAGE_NOT_NORMALIZED"
    )


def test_zero_heading_overrides_nonzero_exif_and_null_is_invalid(
    client: TestClient, parameters: Parameters
) -> None:
    image = _jpeg_with_camera_exif()
    response = client.post(URL, files=_parts(parameters, image, JPEG_TYPE))
    assert response.status_code == 200
    assert response.json()["camera_used"]["orientation"]["heading_deg"] == 0
    assert (
        response.json()["camera_value_sources"]["/orientation/heading_deg"]["source"]
        == "override"
    )
    parameters["camera"]["orientation"]["heading_deg"] = None
    invalid = client.post(URL, files=_parts(parameters, image, JPEG_TYPE))
    assert invalid.status_code == 422
    assert invalid.json()["errors"][0]["path"] == "/camera/orientation/heading_deg"


@pytest.mark.parametrize(
    "camera", [None, {}, {"intrinsics": {}, "position": {}, "orientation": {}}]
)
def test_unusable_exif_reports_all_unresolved_fields(
    client: TestClient, parameters: Parameters, camera: Parameters | None
) -> None:
    parameters.pop("camera")
    if camera is not None:
        parameters["camera"] = camera
    response = client.post(
        URL,
        files=_parts(
            parameters,
            _jpeg_with_camera_exif(north_reference="M", datum="ED50"),
            JPEG_TYPE,
        ),
    )
    assert response.status_code == 422
    assert response.json()["code"] == "CAMERA_PARAMETERS_UNRESOLVED"
    assert {item["path"] for item in response.json()["errors"]} == {
        "/camera/position/longitude_deg",
        "/camera/position/latitude_deg",
        "/camera/position/elevation/value_m",
        "/camera/orientation/heading_deg",
        "/camera/orientation/pitch_deg",
        "/camera/orientation/roll_deg",
    }


def _change(document: Parameters, path: str, value: Any) -> None:
    parents = path.split("/")
    current = document
    for key in parents[:-1]:
        current = current[int(key) if isinstance(current, list) else key]
    current[parents[-1]] = value


@pytest.mark.parametrize(
    ("path", "value", "status", "code"),
    [
        ("api_version", "9.0", 422, "UNSUPPORTED_API_VERSION"),
        ("reference_points", [{}], 422, "FEATURE_NOT_SUPPORTED"),
        ("image", {"width_px": 30}, 422, "IMAGE_DIMENSION_MISMATCH"),
        ("camera/orientation/heading_deg", None, 422, "VALIDATION_ERROR"),
        ("camera/orientation/pitch_deg", "0", 422, "VALIDATION_ERROR"),
        ("camera/orientation/roll_deg", False, 422, "VALIDATION_ERROR"),
        ("camera/position/longitude_deg", 9, 422, "VALIDATION_ERROR"),
        ("camera/position/elevation/datum", "WGS84", 422, "UNSUPPORTED_VERTICAL_DATUM"),
        ("camera/intrinsics/focal_length_mm", 10, 422, "VALIDATION_ERROR"),
        ("camera/intrinsics/cx_px", 101, 422, "VALIDATION_ERROR"),
        ("turbines/0/position/latitude_deg", 52, 422, "VALIDATION_ERROR"),
        ("turbines/0/hub_height_m", 500, 422, "VALIDATION_ERROR"),
        ("turbines/0/rotor_diameter_m", 0, 422, "VALIDATION_ERROR"),
        ("turbines/0/status", "approved", 422, "VALIDATION_ERROR"),
        (
            "turbines/0/source/retrieved_at",
            "2026-11-19T08:00:00+00:99",
            422,
            "VALIDATION_ERROR",
        ),
        (
            "provenance",
            {"/camera/missing": {"source": "fixture"}},
            422,
            "VALIDATION_ERROR",
        ),
    ],
)
def test_rejects_invalid_parameters(
    client: TestClient,
    parameters: Parameters,
    path: str,
    value: Any,
    status: int,
    code: str,
) -> None:
    _change(parameters, path, value)
    response = client.post(URL, files=_parts(parameters))
    assert response.status_code == status and response.json()["code"] == code
    assert response.json()["request_id"]


def test_rejects_duplicate_records_and_too_many_turbines(
    client: TestClient, parameters: Parameters
) -> None:
    record = parameters["turbines"][0]
    parameters["turbines"] = [record] * 101
    limited = client.post(URL, files=_parts(parameters))
    assert (
        limited.status_code == 413
        and limited.json()["code"] == "TURBINE_LIMIT_EXCEEDED"
    )
    duplicate = deepcopy(record)
    duplicate["id"] = "duplicate-feature"
    parameters["turbines"] = [record, duplicate]
    rejected = client.post(URL, files=_parts(parameters))
    assert rejected.status_code == 422
    assert rejected.json()["errors"][0]["path"] == "/turbines/1/source/feature_id"
    duplicate["id"] = record["id"]
    assert (
        client.post(URL, files=_parts(parameters)).json()["errors"][0]["path"]
        == "/turbines/1/id"
    )


@pytest.mark.parametrize(
    "raw", [b"[] trailing", b'{"x":1,"x":2}', b'{"x":NaN}', b"\xff"]
)
def test_rejects_invalid_json(client: TestClient, raw: bytes) -> None:
    response = client.post(URL, files=_parts(raw))
    assert response.status_code == 400 and response.json()["code"] == "INVALID_JSON"
    assert response.json()["part"] == "parameters"


def test_requires_exactly_the_two_documented_parts(
    client: TestClient, parameters: Parameters
) -> None:
    image, params = _parts(parameters)
    for files, code in (
        ([image], "INVALID_MULTIPART"),
        ([params], "INVALID_MULTIPART"),
        ([image, params, params], "DUPLICATE_PART"),
        ([image, image, params], "DUPLICATE_PART"),
        ([image, params, ("extra", image[1])], "INVALID_MULTIPART"),
        (
            [image, ("parameters", ("params.txt", b"{}", "text/plain"))],
            "INVALID_MULTIPART",
        ),
    ):
        response = client.post(URL, files=files)
        assert response.status_code == 400 and response.json()["code"] == code
        assert response.headers["content-type"].startswith("application/problem+json")
    assert client.post(URL).status_code == 400


def test_rejects_truncated_multipart(client: TestClient) -> None:
    response = client.post(
        URL,
        headers={"Content-Type": "multipart/form-data; boundary=upload"},
        content=(
            b'--upload\r\nContent-Disposition: form-data; name="image"\r\n'
            b"Content-Type: image/png\r\n\r\n"
        ),
    )
    assert (
        response.status_code == 400 and response.json()["code"] == "INVALID_MULTIPART"
    )


@pytest.mark.parametrize(
    ("data", "mime", "status", "code"),
    [
        (lambda: b"ignored", "image/gif", 415, "UNSUPPORTED_IMAGE_TYPE"),
        (lambda: b"\x89PNG\r\n\x1a\n", PNG_TYPE, 422, "INVALID_IMAGE"),
        (lambda: _raster(fmt="JPEG"), PNG_TYPE, 415, "UNSUPPORTED_IMAGE_TYPE"),
        (lambda: _raster(fmt="TIFF"), PNG_TYPE, 415, "UNSUPPORTED_IMAGE_TYPE"),
        (
            lambda: _jpeg_with_camera_exif(orientation=9),
            JPEG_TYPE,
            422,
            "INVALID_IMAGE",
        ),
    ],
)
def test_upload_errors(
    client: TestClient,
    parameters: Parameters,
    data: Callable[[], bytes],
    mime: str,
    status: int,
    code: str,
) -> None:
    response = client.post(URL, files=_parts(parameters, data(), mime))
    assert response.status_code == status and response.json()["code"] == code
    assert response.json()["part"] == "image"


def test_upload_rejects_animated_png(
    client: TestClient, parameters: Parameters
) -> None:
    with BytesIO() as buffer:
        first = Image.new("RGB", (3, 2), "red")
        second = Image.new("RGB", (3, 2), "blue")
        first.save(buffer, format="PNG", save_all=True, append_images=[second])
        response = client.post(URL, files=_parts(parameters, buffer.getvalue()))
    assert (
        response.status_code == 415
        and response.json()["code"] == "UNSUPPORTED_IMAGE_TYPE"
    )


@pytest.mark.parametrize("pillow_limit", [False, True])
def test_upload_pixel_limit(
    client: TestClient,
    parameters: Parameters,
    monkeypatch: pytest.MonkeyPatch,
    pillow_limit: bool,
) -> None:
    if pillow_limit:
        monkeypatch.setattr(Image, "MAX_IMAGE_PIXELS", 2)
    else:
        monkeypatch.setattr(normalization, "MAX_DECODED_PIXELS", 5)
    response = client.post(URL, files=_parts(parameters, _raster((3, 2))))
    assert (
        response.status_code == 413
        and response.json()["code"] == "PIXEL_LIMIT_EXCEEDED"
    )


def test_upload_and_output_byte_limits(
    client: TestClient, parameters: Parameters, monkeypatch: pytest.MonkeyPatch
) -> None:
    data = _raster()
    monkeypatch.setattr(multipart, "MAX_IMAGE_BYTES", len(data))
    assert client.post(URL, files=_parts(parameters, data)).status_code == 200
    rejected = client.post(URL, files=_parts(parameters, data + b"0"))
    assert rejected.status_code == 413 and rejected.json()["code"] == "IMAGE_TOO_LARGE"
    with monkeypatch.context() as scoped:
        scoped.setattr(multipart, "MAX_PARAMETERS_BYTES", 20)
        rejected = client.post(URL, files=_parts(parameters, data))
        assert (
            rejected.status_code == 413
            and rejected.json()["code"] == "PARAMETERS_TOO_LARGE"
        )
    monkeypatch.setattr(visualization, "MAX_PNG_BYTES", 20)
    rejected = client.post(URL, files=_parts(parameters, data))
    assert (
        rejected.status_code == 503
        and rejected.json()["code"] == "OUTPUT_LIMIT_EXCEEDED"
    )


def test_upload_request_limit_counts_stream_without_content_length(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(multipart, "MAX_REQUEST_BYTES", 32)
    response = client.post(
        URL,
        headers={"Content-Type": "multipart/form-data; boundary=upload"},
        content=iter(
            [b"--upload\r\n", b'Content-Disposition: form-data; name="image"\r\n']
        ),
    )
    assert "content-length" not in response.request.headers
    assert (
        response.status_code == 413 and response.json()["code"] == "REQUEST_TOO_LARGE"
    )


def test_render_capacity_is_released(
    client: TestClient, parameters: Parameters
) -> None:
    slots = visualizations.RENDER_SLOTS
    assert slots.acquire(blocking=False) and slots.acquire(blocking=False)
    try:
        response = client.post(URL, files=_parts(parameters))
        assert response.status_code == 503
        assert response.json()["code"] == "RENDER_CAPACITY_EXCEEDED"
    finally:
        slots.release()
        slots.release()
    assert client.post(URL, files=_parts(parameters)).status_code == 200
