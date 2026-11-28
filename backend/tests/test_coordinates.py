"""Tests for the EPSG:25832 and camera-relative coordinate frames."""

import math

import pytest
from pyproj import Geod

from wind_turbine_visualization.geo.coordinates import LocalFrame, ProjectedPosition


def test_wgs84_central_meridian_uses_longitude_first():
    """UTM 32N has a false easting of 500 km at longitude 9 degrees."""
    position = ProjectedPosition.from_wgs84(
        longitude_deg=9.0, latitude_deg=52.0, elevation_m=85.0
    )

    assert position.easting_m == pytest.approx(500_000, abs=0.01)
    assert position.northing_m == pytest.approx(5_761_038.212, abs=0.02)
    assert position.elevation_m == 85.0


@pytest.mark.parametrize(
    ("camera_longitude", "bearing_deg", "expected_offset"),
    [
        (7.62, 0, (0.0, 100.0, 40.0)),
        (7.62, 90, (100.0, 0.0, 40.0)),
        (10.38, 0, (0.0, 100.0, 40.0)),
        (10.38, 90, (100.0, 0.0, 40.0)),
    ],
)
def test_local_axes_follow_true_north_on_both_sides_of_utm_meridian(
    camera_longitude, bearing_deg, expected_offset
):
    """Check true bearings using geodesics independent of the UTM rotation."""
    camera_latitude = 51.96
    longitude, latitude, _ = Geod(ellps="WGS84").fwd(
        camera_longitude, camera_latitude, bearing_deg, 100.0
    )
    camera = ProjectedPosition.from_wgs84(
        longitude_deg=camera_longitude, latitude_deg=camera_latitude, elevation_m=60.0
    )
    target = ProjectedPosition.from_wgs84(
        longitude_deg=longitude, latitude_deg=latitude, elevation_m=100.0
    )

    # Allow 0.1 m for the UTM grid scale approximation over 100 m.
    assert LocalFrame(camera).to_local(target) == pytest.approx(
        expected_offset, abs=0.1
    )


def test_projected_positions_preserve_negative_height_difference():
    """An object directly below the optical centre has zero horizontal offset."""
    camera = ProjectedPosition(easting_m=500_000, northing_m=5_761_038, elevation_m=110)
    base = ProjectedPosition(easting_m=500_000, northing_m=5_761_038, elevation_m=100)

    assert LocalFrame(camera).to_local(base) == (0, 0, -10)


@pytest.mark.parametrize(("lon", "lat"), [(181, 52), (7, 91), (math.nan, 52)])
def test_invalid_geographic_positions_are_rejected(lon, lat):
    """Reject values outside the geographic coordinate ranges."""
    with pytest.raises(ValueError, match="longitude or latitude"):
        ProjectedPosition.from_wgs84(longitude_deg=lon, latitude_deg=lat, elevation_m=0)


def test_nonfinite_height_is_rejected():
    """The local frame requires a resolved, finite DHHN2016/NHN height."""
    with pytest.raises(ValueError, match="elevation must be finite"):
        ProjectedPosition(easting_m=500_000, northing_m=5_761_038, elevation_m=math.nan)
