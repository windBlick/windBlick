"""Draw schematic turbine geometry on a normalized photograph."""

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from PIL import Image, ImageDraw

from wind_turbine_visualization.camera.projection import CameraProjection
from wind_turbine_visualization.geo.coordinates import LocalFrame, ProjectedPosition
from wind_turbine_visualization.rendering.turbine_geometry import (
    Point3D,
    TurbineGeometry,
)

OVERLAY_COLOR_HEX = "#2563EB"


@dataclass(frozen=True, kw_only=True)
class TurbinePlacement:
    """Schematic geometry and the surveyed or supplied position of its tower base."""

    base: ProjectedPosition
    geometry: TurbineGeometry


@dataclass(frozen=True)
class TurbineRenderResult:
    """Draw outcome and projected hub in subpixel raster coordinates, if available."""

    outcome: Literal["drawn", "outside_frame", "behind_camera"]
    projected_hub_px: tuple[float, float] | None


@dataclass(frozen=True)
class OverlayResult:
    """Composite image and per-turbine results in the original input order."""

    image: Image.Image
    turbines: tuple[TurbineRenderResult, ...]


def _offset(base: Point3D, point: Point3D) -> Point3D:
    base_east, base_north, base_up = base
    east, north, up = point
    return base_east + east, base_north + north, base_up + up


def render_turbine_overlay(
    photo: Image.Image,
    *,
    local_frame: LocalFrame,
    camera: CameraProjection,
    turbines: Sequence[TurbinePlacement],
) -> OverlayResult:
    """Draw towers and three-blade rotors on a normalized image copy.

    Use the optical-centre frame and intrinsics for this exact raster. Apply
    the geometry's default north-facing rotor plane and draw farther bases
    first, preserving input order for ties. The result omits source metadata.
    Raise ValueError if the raster size does not match the intrinsics.
    """
    if photo.size != camera.image_size:
        raise ValueError("Photo size must match the camera intrinsics")

    rendered = photo.convert("RGBA" if photo.has_transparency_data else "RGB")
    rendered.info.clear()
    draw = ImageDraw.Draw(rendered)
    bases = [local_frame.to_local(turbine.base) for turbine in turbines]
    draw_order = sorted(
        range(len(turbines)), key=lambda index: math.hypot(*bases[index]), reverse=True
    )
    results: dict[int, TurbineRenderResult] = {}

    for index in draw_order:
        base = bases[index]
        geometry = turbines[index].geometry
        hub_px = camera.project(_offset(base, geometry.hub_position))
        segments = (geometry.tower_segment(), *geometry.blade_segments())
        drawn = False
        in_front = False
        for start, end in segments:
            camera_start = camera.to_camera(_offset(base, start))
            camera_end = camera.to_camera(_offset(base, end))
            in_front |= camera_start[2] > 0 or camera_end[2] > 0
            pixels = camera.clip_and_project_segment(camera_start, camera_end)
            if pixels is not None:
                draw.line(
                    [(round(x), round(y)) for x, y in pixels],
                    fill=OVERLAY_COLOR_HEX,
                    width=2,
                )
                drawn = True

        results[index] = TurbineRenderResult(
            "drawn" if drawn else "outside_frame" if in_front else "behind_camera",
            hub_px,
        )

    return OverlayResult(
        rendered, tuple(results[index] for index in range(len(turbines)))
    )
