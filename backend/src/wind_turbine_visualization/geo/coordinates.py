"""Project WGS84 locations and form a local frame at the camera."""

import math
from dataclasses import dataclass
from functools import cache
from typing import Self

from pyproj import Proj, Transformer

WORKING_CRS = "EPSG:25832"


@cache
def _wgs84_to_utm() -> Transformer:
    return Transformer.from_crs("EPSG:4326", WORKING_CRS, always_xy=True)


@dataclass(frozen=True, kw_only=True)
class ProjectedPosition:
    """Absolute position in EPSG:25832 metres and DHHN2016/NHN elevation."""

    easting_m: float
    northing_m: float
    elevation_m: float

    def __post_init__(self) -> None:
        if not all(
            math.isfinite(value)
            for value in (self.easting_m, self.northing_m, self.elevation_m)
        ):
            raise ValueError("Easting, northing and elevation must be finite")

    @classmethod
    def from_wgs84(
        cls, *, longitude_deg: float, latitude_deg: float, elevation_m: float
    ) -> Self:
        """Project WGS84 longitude/latitude in degrees to EPSG:25832.

        Pass an already resolved DHHN2016/NHN elevation in metres.
        Raise ValueError for invalid coordinates or a non-finite elevation,
        or pyproj.exceptions.ProjError if the horizontal transform fails.
        """
        if not -180 <= longitude_deg <= 180 or not -90 <= latitude_deg <= 90:
            raise ValueError("Invalid WGS84 longitude or latitude")
        easting, northing = _wgs84_to_utm().transform(
            longitude_deg, latitude_deg, errcheck=True
        )
        return cls(easting_m=easting, northing_m=northing, elevation_m=elevation_m)


class LocalFrame:
    """True-east, true-north and up axes centred on the camera optical centre."""

    def __init__(self, camera: ProjectedPosition) -> None:
        """Find true north at the camera in EPSG:25832.

        Raise pyproj.exceptions.ProjError for a failed inverse projection.
        """
        self._camera = camera
        utm = Proj(WORKING_CRS)
        longitude, latitude = utm(
            camera.easting_m, camera.northing_m, inverse=True, errcheck=True
        )
        convergence = utm.get_factors(
            longitude, latitude, errcheck=True
        ).meridian_convergence
        # PROJ gives grid north relative to true north, so reverse the angle.
        angle = math.radians(-convergence)
        self._cos = math.cos(angle)
        self._sin = math.sin(angle)

    def to_local(self, target: ProjectedPosition) -> tuple[float, float, float]:
        """Return the camera-relative (east, true north, up) offset in metres."""
        grid_east = target.easting_m - self._camera.easting_m
        grid_north = target.northing_m - self._camera.northing_m
        # shortcut: grid metres and flat heights until long-range accuracy is needed.
        return (
            grid_east * self._cos - grid_north * self._sin,
            grid_east * self._sin + grid_north * self._cos,
            target.elevation_m - self._camera.elevation_m,
        )
