"""Checks for rendering camera-projected turbine geometry to a raster."""

from io import BytesIO

import pytest
from PIL import Image

from wind_turbine_visualization.camera.projection import (
    CameraIntrinsics,
    CameraProjection,
)
from wind_turbine_visualization.geo.coordinates import LocalFrame, ProjectedPosition
from wind_turbine_visualization.rendering.overlay import (
    TurbinePlacement,
    render_turbine_overlay,
)
from wind_turbine_visualization.rendering.turbine_geometry import (
    Point3D,
    TurbineGeometry,
)

BLUE = (37, 99, 235)
RASTER_SIZE = (101, 101)


@pytest.fixture
def camera() -> CameraProjection:
    return CameraProjection(
        heading_deg=0,
        pitch_deg=0,
        roll_deg=0,
        intrinsics=CameraIntrinsics(
            width_px=101, height_px=101, fx_px=100, fy_px=100, cx_px=50, cy_px=50
        ),
    )


@pytest.fixture
def local_frame() -> LocalFrame:
    # Easting 500,000 m lies on the central meridian, with zero convergence.
    return LocalFrame(
        ProjectedPosition(easting_m=500_000, northing_m=5_761_000, elevation_m=75)
    )


def placement(
    *, east_m: float = 0, north_m: float = 100, up_m: float = 0
) -> TurbinePlacement:
    return TurbinePlacement(
        base=ProjectedPosition(
            easting_m=500_000 + east_m,
            northing_m=5_761_000 + north_m,
            elevation_m=75 + up_m,
        ),
        geometry=TurbineGeometry(hub_height_meters=30, rotor_diameter_meters=20),
    )


def test_render_tower_and_three_blades_on_photo_copy(
    camera: CameraProjection, local_frame: LocalFrame
) -> None:
    photo = Image.new("RGB", RASTER_SIZE, "white")
    exif = photo.getexif()
    exif[270] = "Synthetic fixture"
    photo.info["exif"] = exif.tobytes()
    original_pixels = photo.tobytes()

    result = render_turbine_overlay(
        photo, camera=camera, local_frame=local_frame, turbines=[placement()]
    )

    assert result.turbines[0].outcome == "drawn"
    assert result.turbines[0].projected_hub_px == pytest.approx((50, 20))
    assert result.image.size == photo.size
    for pixel in [(50, 50), (50, 20), (50, 10), (59, 25), (41, 25)]:
        assert result.image.getpixel(pixel) == BLUE
    assert result.image.getpixel((0, 0)) == (255, 255, 255)
    assert photo.tobytes() == original_pixels
    assert photo.getexif()[270] == "Synthetic fixture"

    with BytesIO() as png:
        result.image.save(png, format="PNG")
        png.seek(0)
        with Image.open(png) as decoded:
            assert decoded.format == "PNG"
            assert not decoded.getexif()
            assert decoded.tobytes() == result.image.tobytes()


def test_partly_visible_turbine_is_drawn_to_the_image_edge(
    camera: CameraProjection, local_frame: LocalFrame
) -> None:
    result = render_turbine_overlay(
        Image.new("RGB", RASTER_SIZE, "white"),
        camera=camera,
        local_frame=local_frame,
        turbines=[placement(up_m=-60)],
    )

    assert result.turbines[0].outcome == "drawn"
    assert result.turbines[0].projected_hub_px == pytest.approx((50, 80))
    assert result.image.getpixel((50, 100)) == BLUE


def test_invisible_turbines_leave_pixels_intact_and_keep_input_order(
    camera: CameraProjection, local_frame: LocalFrame
) -> None:
    photo = Image.new("RGBA", RASTER_SIZE, (255, 255, 255, 127))
    result = render_turbine_overlay(
        photo,
        camera=camera,
        local_frame=local_frame,
        turbines=[placement(north_m=-100), placement(east_m=300)],
    )

    behind, outside = result.turbines
    assert behind.outcome == "behind_camera"
    assert behind.projected_hub_px is None
    assert outside.outcome == "outside_frame"
    assert outside.projected_hub_px == pytest.approx((350, 20))
    assert result.image.mode == "RGBA"
    assert result.image.tobytes() == photo.tobytes()


def test_rejects_intrinsics_for_a_different_raster(
    camera: CameraProjection, local_frame: LocalFrame
) -> None:
    with pytest.raises(ValueError, match="Photo size must match"):
        render_turbine_overlay(
            Image.new("RGB", (99, 101)),
            camera=camera,
            local_frame=local_frame,
            turbines=[placement()],
        )


@pytest.mark.parametrize(
    ("start", "end", "expected_start", "expected_end"),
    [
        ((-100, 0, 100), (100, 0, 100), (0, 50), (100, 50)),
        ((0, 1, -1), (0, 0, 10), (50, 100), (50, 50)),
        ((0, 0, 0), (0, 0, 10), (50, 50), (50, 50)),
    ],
)
def test_clip_segment_before_perspective_division(
    camera: CameraProjection,
    start: Point3D,
    end: Point3D,
    expected_start: tuple[int, int],
    expected_end: tuple[int, int],
) -> None:
    pixels = camera.clip_and_project_segment(start, end)
    assert pixels is not None
    assert pixels[0] == pytest.approx(expected_start)
    assert pixels[1] == pytest.approx(expected_end)
    reversed_pixels = camera.clip_and_project_segment(end, start)
    assert reversed_pixels is not None
    assert reversed_pixels[0] == pytest.approx(expected_end)
    assert reversed_pixels[1] == pytest.approx(expected_start)
