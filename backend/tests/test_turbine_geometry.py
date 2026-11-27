"""Tests for the schematic turbine geometry."""

import math

import pytest

from wind_turbine_visualization.rendering import (
    InvalidTurbineGeometry,
    TurbineGeometry,
)

TOLERANCE = 1e-9
HALF_SQRT3 = math.sqrt(3) / 2


def test_derived_heights_distinguish_hub_and_total_height():
    """Hub 100 m and rotor 120 m give a 160 m tip and 40 m clearance."""
    turbine = TurbineGeometry(hub_height_meters=100.0, rotor_diameter_meters=120.0)

    assert turbine.rotor_radius_meters == 60.0
    assert turbine.total_height_meters == 160.0
    assert turbine.blade_tip_clearance_meters == 40.0


def test_tower_runs_from_base_to_hub():
    """The tower is a vertical segment from the origin to the hub."""
    turbine = TurbineGeometry(hub_height_meters=100.0, rotor_diameter_meters=120.0)

    assert turbine.tower_segment() == ((0.0, 0.0, 0.0), (0.0, 0.0, 100.0))


def test_blades_facing_north_lie_in_x_z_plane():
    """Facing north: one blade up, two at 120 degrees, all in the x-z plane."""
    turbine = TurbineGeometry(hub_height_meters=100.0, rotor_diameter_meters=120.0)

    tips = [tip for _, tip in turbine.blade_segments()]

    expected_tips = [
        (0.0, 0.0, 160.0),
        (60.0 * HALF_SQRT3, 0.0, 70.0),
        (-60.0 * HALF_SQRT3, 0.0, 70.0),
    ]
    for tip, expected in zip(tips, expected_tips, strict=True):
        assert tip == pytest.approx(expected, abs=TOLERANCE)


def test_blades_facing_east_lie_in_y_z_plane():
    """Rotating the facing azimuth by 90 degrees moves the rotor to y-z."""
    turbine = TurbineGeometry(hub_height_meters=100.0, rotor_diameter_meters=120.0)

    tips = [tip for _, tip in turbine.blade_segments(rotor_facing_azimuth_degrees=90.0)]

    for x_meters, _, _ in tips:
        assert x_meters == pytest.approx(0.0, abs=TOLERANCE)
    assert tips[1][1] == pytest.approx(-60.0 * HALF_SQRT3, abs=TOLERANCE)


@pytest.mark.parametrize(
    "azimuth_degrees", [0.0, 37.0, 90.0, 215.0, math.nextafter(360.0, 0.0)]
)
def test_every_blade_has_rotor_radius_length(azimuth_degrees):
    """Blade length equals the rotor radius for any facing direction."""
    turbine = TurbineGeometry(hub_height_meters=80.0, rotor_diameter_meters=100.0)

    for hub, tip in turbine.blade_segments(azimuth_degrees):
        assert math.dist(hub, tip) == pytest.approx(50.0, abs=TOLERANCE)


@pytest.mark.parametrize(
    "azimuth_degrees", [-0.1, 360.0, 360.1, math.nan, math.inf, -math.inf]
)
def test_azimuth_outside_allowed_range_is_rejected(azimuth_degrees):
    """Reject angles outside the compass range and non-finite angles."""
    turbine = TurbineGeometry(hub_height_meters=100.0, rotor_diameter_meters=120.0)

    with pytest.raises(ValueError, match="rotor_facing_azimuth_degrees"):
        turbine.blade_segments(azimuth_degrees)


@pytest.mark.parametrize("bad_value", [0.0, -1.0, 500.0, 500.1, math.nan, math.inf])
@pytest.mark.parametrize("field", ["hub_height_meters", "rotor_diameter_meters"])
def test_dimension_outside_allowed_range_is_rejected(field, bad_value):
    """Out-of-range and non-finite dimensions raise with the field name."""
    dimensions = {"hub_height_meters": 100.0, "rotor_diameter_meters": 120.0}
    dimensions[field] = bad_value

    with pytest.raises(InvalidTurbineGeometry) as error:
        TurbineGeometry(**dimensions)

    assert error.value.field == field
    assert error.value.code == "VALIDATION_ERROR"
    assert "less than 500 m" in str(error.value)


def test_dimensions_just_below_500_m_are_accepted():
    """Both dimensions can reach the largest float below the upper bound."""
    dimension = math.nextafter(500.0, 0.0)
    turbine = TurbineGeometry(
        hub_height_meters=dimension, rotor_diameter_meters=dimension
    )

    assert turbine.hub_height_meters == dimension
    assert turbine.rotor_diameter_meters == dimension
