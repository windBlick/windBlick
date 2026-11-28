"""Interpret EXIF camera values that have a supported frame and unit."""

import math
import struct
from dataclasses import dataclass
from numbers import Real

from PIL import ExifTags, Image

GPS = ExifTags.GPS
TAG = ExifTags.Base


@dataclass(frozen=True)
class ExifValue:
    """One usable EXIF-derived value and the names of the tags it used."""

    value: float
    tags: tuple[str, ...]


@dataclass(frozen=True)
class CameraExif:
    """Optional supported values in camera conventions and the normalized raster."""

    longitude_deg: ExifValue | None = None
    latitude_deg: ExifValue | None = None
    heading_deg: ExifValue | None = None
    focal_length_mm: ExifValue | None = None
    sensor_width_mm: ExifValue | None = None
    sensor_height_mm: ExifValue | None = None


def _ifd(exif: Image.Exif, group: ExifTags.IFD) -> dict[int, object]:
    try:
        return exif.get_ifd(group)
    except (
        OSError,
        ValueError,
        TypeError,
        KeyError,
        IndexError,
        OverflowError,
        struct.error,
    ):
        return {}


def _number(value: object) -> float | None:
    if isinstance(value, Real) and not isinstance(value, bool):
        try:
            numeric = float(value)
        except (OverflowError, ValueError, ZeroDivisionError):
            return None
        if math.isfinite(numeric):
            return numeric
    return None


def _text(value: object) -> str | None:
    if isinstance(value, bytes):
        value = value.decode("ascii", errors="replace")
    return value.strip("\x00 ").upper() if isinstance(value, str) else None


def _coordinate(
    fields: dict[int, object],
    tag: ExifTags.GPS,
    ref: ExifTags.GPS,
    *,
    limit: int,
    positive: str,
    negative: str,
) -> ExifValue | None:
    datum = _text(fields.get(GPS.GPSMapDatum))
    if GPS.GPSMapDatum in fields and datum not in ("WGS-84", "WGS 84", "WGS84"):
        return None
    direction = _text(fields.get(ref))
    triplet = fields.get(tag)
    if (
        direction not in (positive, negative)
        or not isinstance(triplet, tuple)
        or len(triplet) != 3
    ):
        return None
    degrees, minutes, seconds = map(_number, triplet)
    if (
        degrees is None
        or minutes is None
        or seconds is None
        or not (0 <= degrees <= limit and 0 <= minutes < 60 and 0 <= seconds < 60)
    ):
        return None
    absolute = degrees + minutes / 60 + seconds / 3600
    if absolute > limit:
        return None
    tags = (tag.name, ref.name)
    if GPS.GPSMapDatum in fields:
        tags += ("GPSMapDatum",)
    return ExifValue(absolute if direction == positive else -absolute, tags)


def _effective_extents(
    fields: dict[int, object], size: tuple[int, int], orientation: int
) -> tuple[ExifValue | None, ExifValue | None]:
    declared_size = fields.get(TAG.ExifImageWidth), fields.get(TAG.ExifImageHeight)
    if declared_size != size:
        return None, None
    zoom = _number(fields.get(TAG.DigitalZoomRatio, 0))
    if zoom is None or zoom < 0 or zoom > 1:
        return None, None
    resolution_unit = _number(fields.get(TAG.FocalPlaneResolutionUnit))
    units_mm = {2: 25.4, 3: 10.0}
    if resolution_unit not in units_mm:
        return None, None

    extents: list[ExifValue | None] = []
    for dimension, dimension_tag, resolution_tag in zip(
        size,
        (TAG.ExifImageWidth, TAG.ExifImageHeight),
        (TAG.FocalPlaneXResolution, TAG.FocalPlaneYResolution),
        strict=True,
    ):
        density = _number(fields.get(resolution_tag))
        if density is None or density <= 0:
            extents.append(None)
            continue
        extent = dimension / density * units_mm[resolution_unit]
        tags = (
            "PixelXDimension"
            if dimension_tag == TAG.ExifImageWidth
            else "PixelYDimension",
            resolution_tag.name,
            "FocalPlaneResolutionUnit",
        )
        if orientation >= 5:
            tags += ("Orientation",)
        if TAG.DigitalZoomRatio in fields:
            tags += ("DigitalZoomRatio",)
        extents.append(ExifValue(extent, tags) if 0 < extent < math.inf else None)
    return (extents[1], extents[0]) if orientation >= 5 else (extents[0], extents[1])


def read_camera_exif(
    exif: Image.Exif, *, size: tuple[int, int], orientation: int
) -> CameraExif:
    """Read camera tags before the corresponding image orientation is applied."""
    gps = _ifd(exif, ExifTags.IFD.GPSInfo)
    camera = _ifd(exif, ExifTags.IFD.Exif)
    heading = _number(gps.get(GPS.GPSImgDirection))
    focal = _number(camera.get(TAG.FocalLength))
    width, height = _effective_extents(camera, size, orientation)
    heading_value = (
        ExifValue(heading, ("GPSImgDirection", "GPSImgDirectionRef"))
        if orientation == 1
        and _text(gps.get(GPS.GPSImgDirectionRef)) == "T"
        and heading is not None
        and 0 <= heading < 360
        else None
    )
    return CameraExif(
        longitude_deg=_coordinate(
            gps,
            GPS.GPSLongitude,
            GPS.GPSLongitudeRef,
            limit=180,
            positive="E",
            negative="W",
        ),
        latitude_deg=_coordinate(
            gps,
            GPS.GPSLatitude,
            GPS.GPSLatitudeRef,
            limit=90,
            positive="N",
            negative="S",
        ),
        heading_deg=heading_value,
        focal_length_mm=ExifValue(focal, ("FocalLength",))
        if focal is not None and focal > 0
        else None,
        sensor_width_mm=width,
        sensor_height_mm=height,
    )
