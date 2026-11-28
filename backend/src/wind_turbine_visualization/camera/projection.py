"""Zero-skew pinhole camera model for a normalized image raster."""

import math
from dataclasses import dataclass
from typing import Self


@dataclass(frozen=True, kw_only=True)
class CameraIntrinsics:
    """Raster size, focal lengths (fx/fy) and principal point (cx/cy), in pixels."""

    width_px: int
    height_px: int
    fx_px: float
    fy_px: float
    cx_px: float
    cy_px: float

    def __post_init__(self) -> None:
        if any(
            type(size) is not int or size < 1
            for size in (self.width_px, self.height_px)
        ):
            raise ValueError("Raster dimensions must be positive integers")
        if not all(math.isfinite(f) and f > 0 for f in (self.fx_px, self.fy_px)):
            raise ValueError("Focal lengths must be positive and finite")
        if not (
            0 <= self.cx_px <= self.width_px - 1
            and 0 <= self.cy_px <= self.height_px - 1
        ):
            raise ValueError("The principal point must lie inside the raster")

    @classmethod
    def from_horizontal_fov(
        cls, *, width_px: int, height_px: int, horizontal_fov_deg: float
    ) -> Self:
        """Use horizontal FOV in degrees for the final raster, with square pixels.

        Raise ValueError for an invalid raster or field of view outside (0, 180).
        """
        if not 0 < horizontal_fov_deg < 180:
            raise ValueError("Horizontal FOV must be between 0 and 180 degrees")
        half_fov = math.radians(horizontal_fov_deg) / 2
        if half_fov == 0:
            raise ValueError("Horizontal FOV is too small to represent in radians")
        focal_px = width_px / (2 * math.tan(half_fov))
        return cls(
            width_px=width_px,
            height_px=height_px,
            fx_px=focal_px,
            fy_px=focal_px,
            cx_px=(width_px - 1) / 2,
            cy_px=(height_px - 1) / 2,
        )

    @classmethod
    def from_physical_focal_length(
        cls,
        *,
        width_px: int,
        height_px: int,
        focal_length_mm: float,
        sensor_width_mm: float,
        sensor_height_mm: float,
    ) -> Self:
        """Use physical focal length and effective sensor extents in millimetres.

        The extents must match the final raster's crop and orientation.
        Raise ValueError for invalid dimensions or focal length.
        """
        if not all(
            math.isfinite(value) and value > 0
            for value in (focal_length_mm, sensor_width_mm, sensor_height_mm)
        ):
            raise ValueError(
                "Physical focal length and sensor extents must be positive"
            )
        return cls(
            width_px=width_px,
            height_px=height_px,
            fx_px=focal_length_mm / sensor_width_mm * width_px,
            fy_px=focal_length_mm / sensor_height_mm * height_px,
            cx_px=(width_px - 1) / 2,
            cy_px=(height_px - 1) / 2,
        )


class CameraProjection:
    """Project camera-relative east/north/up points onto the normalized raster."""

    def __init__(
        self,
        *,
        heading_deg: float,
        pitch_deg: float,
        roll_deg: float,
        intrinsics: CameraIntrinsics,
    ) -> None:
        """Build a fixed camera orientation using degrees.

        Heading is clockwise from true north. Pitch is positive above the horizon.
        Positive roll turns image-right toward image-down around the optical axis.
        Raise ValueError for an angle outside the contract's range.
        """
        if not 0 <= heading_deg < 360:
            raise ValueError("Heading must be in [0, 360) degrees")
        if not -90 < pitch_deg < 90:
            raise ValueError("Pitch must be in (-90, 90) degrees")
        if not -180 <= roll_deg < 180:
            raise ValueError("Roll must be in [-180, 180) degrees")

        heading = math.radians(heading_deg)
        pitch = math.radians(pitch_deg)
        roll = math.radians(roll_deg)
        sin_heading, cos_heading = math.sin(heading), math.cos(heading)
        sin_pitch, cos_pitch = math.sin(pitch), math.cos(pitch)
        sin_roll, cos_roll = math.sin(roll), math.cos(roll)

        self._forward = (
            sin_heading * cos_pitch,
            cos_heading * cos_pitch,
            sin_pitch,
        )
        right_at_zero_roll = (cos_heading, -sin_heading, 0.0)
        down_at_zero_roll = (
            sin_heading * sin_pitch,
            cos_heading * sin_pitch,
            -cos_pitch,
        )
        unrolled_axes = tuple(zip(right_at_zero_roll, down_at_zero_roll, strict=True))
        self._right = tuple(
            cos_roll * right + sin_roll * down for right, down in unrolled_axes
        )
        self._down = tuple(
            -sin_roll * right + cos_roll * down for right, down in unrolled_axes
        )
        self._intrinsics = intrinsics

    def to_camera(
        self, point_enu_m: tuple[float, float, float]
    ) -> tuple[float, float, float]:
        """Rotate an east/north/up point in metres to right/down/forward metres.

        Raise ValueError if the input point contains a non-finite coordinate.
        """
        if not all(math.isfinite(value) for value in point_enu_m):
            raise ValueError("Local point coordinates must be finite")
        return (
            math.sumprod(point_enu_m, self._right),
            math.sumprod(point_enu_m, self._down),
            math.sumprod(point_enu_m, self._forward),
        )

    def project(
        self, point_enu_m: tuple[float, float, float]
    ) -> tuple[float, float] | None:
        """Return subpixel (x, y), or None at or behind the camera plane.

        Pixels outside the raster are returned for clipping by the caller.
        Raise ValueError for a non-finite point or projection.
        """
        right, down, depth = self.to_camera(point_enu_m)
        if depth <= 0:
            return None
        intrinsics = self._intrinsics
        x_px = intrinsics.cx_px + intrinsics.fx_px * (right / depth)
        y_px = intrinsics.cy_px + intrinsics.fy_px * (down / depth)
        if not math.isfinite(x_px) or not math.isfinite(y_px):
            raise ValueError("Projected pixel coordinates must be finite")
        return x_px, y_px
