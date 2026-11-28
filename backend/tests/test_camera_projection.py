"""Tests for optics, camera orientation and projection to image pixels."""

import math

import pytest
from pyproj import Geod

from wind_turbine_visualization.camera.projection import (
    CameraIntrinsics,
    CameraProjection,
)
from wind_turbine_visualization.geo.coordinates import LocalFrame, ProjectedPosition


@pytest.fixture
def intrinsics() -> CameraIntrinsics:
    """Use calibrated intrinsics with a 100 px focal length and centre at (50, 50)."""
    return CameraIntrinsics(
        width_px=101, height_px=101, fx_px=100, fy_px=100, cx_px=50, cy_px=50
    )


@pytest.mark.parametrize(
    ("point", "expected_pixel"),
    [
        ((0, 100, 0), (50, 50)),
        ((10, 100, 0), (60, 50)),
        ((0, 100, 10), (50, 40)),
        ((10, 200, 0), (55, 50)),
        ((0, -100, 0), None),
        ((0, 0, 0), None),
        ((10, 0, 5), None),
        ((100, 100, 0), (150, 50)),
    ],
)
def test_level_north_facing_camera_projects_local_axes(
    intrinsics, point, expected_pixel
):
    """Check signs, perspective scale, camera-plane rejection and clipping inputs."""
    camera = CameraProjection(
        heading_deg=0, pitch_deg=0, roll_deg=0, intrinsics=intrinsics
    )

    assert camera.project(point) == expected_pixel


@pytest.mark.parametrize(
    ("heading", "pitch", "roll", "point", "expected_pixel"),
    [
        (90, 0, 0, (100, -10, 0), (60, 50)),
        (0, 45, 0, (0, 100, 0), (50, 150)),
        (0, 0, 90, (10, 100, 0), (50, 40)),
        (0, 0, -180, (10, 100, 0), (40, 50)),
    ],
)
def test_camera_orientation_signs(
    intrinsics, heading, pitch, roll, point, expected_pixel
):
    """Verify the API convention for all three rotation angles."""
    camera = CameraProjection(
        heading_deg=heading, pitch_deg=pitch, roll_deg=roll, intrinsics=intrinsics
    )

    assert camera.project(point) == pytest.approx(expected_pixel)


def test_horizontal_fov_uses_normalized_portrait_width():
    """A 90 degree horizontal FOV gives focal length equal to half the width."""
    intrinsics = CameraIntrinsics.from_horizontal_fov(
        width_px=800, height_px=1200, horizontal_fov_deg=90
    )

    assert (intrinsics.fx_px, intrinsics.fy_px) == pytest.approx((400, 400))
    assert (intrinsics.cx_px, intrinsics.cy_px) == (399.5, 599.5)


def test_physical_focal_length_accounts_for_each_effective_sensor_extent():
    """Use independent focal lengths for the two image axes."""
    intrinsics = CameraIntrinsics.from_physical_focal_length(
        width_px=800,
        height_px=1200,
        focal_length_mm=4,
        sensor_width_mm=4,
        sensor_height_mm=8,
    )

    assert (intrinsics.fx_px, intrinsics.fy_px) == (800, 600)
    assert (intrinsics.cx_px, intrinsics.cy_px) == (399.5, 599.5)


@pytest.mark.parametrize("fov_deg", [0, 180, math.nan])
def test_invalid_fov_is_rejected(fov_deg):
    """Only a finite horizontal FOV inside (0, 180) describes a pinhole."""
    with pytest.raises(ValueError, match="Horizontal FOV"):
        CameraIntrinsics.from_horizontal_fov(
            width_px=800, height_px=1200, horizontal_fov_deg=fov_deg
        )


@pytest.mark.parametrize(
    ("heading", "pitch", "roll", "field"),
    [(360, 0, 0, "Heading"), (0, 90, 0, "Pitch"), (0, 0, 180, "Roll")],
)
def test_invalid_angles_fail_before_projection(intrinsics, heading, pitch, roll, field):
    """Reject the excluded upper angle boundary before building the camera frame."""
    with pytest.raises(ValueError, match=field):
        CameraProjection(
            heading_deg=heading, pitch_deg=pitch, roll_deg=roll, intrinsics=intrinsics
        )


def test_geographic_position_to_hub_pixel(intrinsics):
    """A hub 100 m north and 10 m above the camera projects above image centre."""
    lon, lat = 7.62, 51.96
    camera_position = ProjectedPosition.from_wgs84(
        longitude_deg=lon, latitude_deg=lat, elevation_m=70
    )
    base_lon, base_lat, _ = Geod(ellps="WGS84").fwd(lon, lat, 0, 100)
    hub = ProjectedPosition.from_wgs84(
        longitude_deg=base_lon, latitude_deg=base_lat, elevation_m=80
    )
    local_hub = LocalFrame(camera_position).to_local(hub)
    camera = CameraProjection(
        heading_deg=0, pitch_deg=0, roll_deg=0, intrinsics=intrinsics
    )

    assert camera.project(local_hub) == pytest.approx((50, 40), abs=0.01)
