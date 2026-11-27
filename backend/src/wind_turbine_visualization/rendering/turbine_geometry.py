"""Simplified parametric wind turbine geometry.

Pure domain logic: no FastAPI, no image libraries, no projection. The model
describes a schematic turbine in a local frame so later steps (camera
projection, overlay rendering) can consume it independently.

Local turbine frame: the origin is the tower base on the ground, +x points
east, +y north, and +z up, all in meters. Heights are measured above the
tower base, not above a vertical datum; the base elevation belongs to the
turbine position in the API contract.

The rotor is a schematic three-blade star in one vertical plane. The
contract provides no real yaw or blade phase, so the orientation is a
documented convention, not a statement about the real turbine.
"""

import math
from dataclasses import dataclass

from wind_turbine_visualization.rendering.errors import InvalidTurbineGeometry

Point3D = tuple[float, float, float]
Segment3D = tuple[Point3D, Point3D]

BLADE_COUNT = 3
BLADE_SPACING_DEGREES = 360.0 / BLADE_COUNT


@dataclass(frozen=True)
class TurbineGeometry:
    """Dimensions that define a schematic turbine.

    Attributes:
        hub_height_meters: Height of the hub centre above the tower base.
        rotor_diameter_meters: Diameter of the rotor circle, not its radius
            and not the total turbine height.

    Raises:
        InvalidTurbineGeometry: If a dimension is outside (0, 500) meters.
    """

    hub_height_meters: float
    rotor_diameter_meters: float

    def __post_init__(self) -> None:
        for field, value in (
            ("hub_height_meters", self.hub_height_meters),
            ("rotor_diameter_meters", self.rotor_diameter_meters),
        ):
            if not 0 < value < 500:
                raise InvalidTurbineGeometry(field, value)

    @property
    def rotor_radius_meters(self) -> float:
        """Blade length from hub centre to blade tip, in meters."""
        return self.rotor_diameter_meters / 2

    @property
    def total_height_meters(self) -> float:
        """Height of the highest blade tip above the tower base, in meters."""
        return self.hub_height_meters + self.rotor_radius_meters

    @property
    def blade_tip_clearance_meters(self) -> float:
        """Lowest possible blade-tip height above the tower base, in meters.

        Negative means the rotor circle would reach below the base, which
        usually points to a source-data error. It is reported, not rejected,
        because the contract defines no plausibility rules yet.
        """
        return self.hub_height_meters - self.rotor_radius_meters

    @property
    def hub_position(self) -> Point3D:
        """Hub centre in the local turbine frame, in meters."""
        return (0.0, 0.0, self.hub_height_meters)

    def tower_segment(self) -> Segment3D:
        """Return the tower as a vertical segment from base to hub."""
        return ((0.0, 0.0, 0.0), self.hub_position)

    def blade_segments(
        self, rotor_facing_azimuth_degrees: float = 0.0
    ) -> tuple[Segment3D, ...]:
        """Return the blades as segments from the hub centre to each tip.

        The first blade points straight up; the others follow at 120 degree
        steps within the rotor plane.

        Args:
            rotor_facing_azimuth_degrees: Compass direction the rotor plane
                faces (its normal), in degrees clockwise from north, in
                [0, 360). The default is north, with blades in the x-z plane.

        Returns:
            One ``(hub, tip)`` segment per blade, in local-frame meters.

        Raises:
            ValueError: If the facing azimuth is outside [0, 360).
        """
        if not 0 <= rotor_facing_azimuth_degrees < 360:
            raise ValueError("rotor_facing_azimuth_degrees must be in [0, 360)")
        azimuth_radians = math.radians(rotor_facing_azimuth_degrees)
        # Horizontal in-plane direction: the rotor normal turned 90 degrees.
        in_plane_east = math.cos(azimuth_radians)
        in_plane_north = -math.sin(azimuth_radians)
        hub_x, hub_y, hub_z = self.hub_position

        segments = []
        for blade_index in range(BLADE_COUNT):
            blade_angle = math.radians(blade_index * BLADE_SPACING_DEGREES)
            horizontal_offset = self.rotor_radius_meters * math.sin(blade_angle)
            vertical_offset = self.rotor_radius_meters * math.cos(blade_angle)
            tip = (
                hub_x + horizontal_offset * in_plane_east,
                hub_y + horizontal_offset * in_plane_north,
                hub_z + vertical_offset,
            )
            segments.append((self.hub_position, tip))
        return tuple(segments)
