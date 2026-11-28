# Camera and coordinate conventions

Reference for the windBlick v0.1 prototype. The [API contract](api-contract.md) defines the payload and error codes. These conventions define what the values mean and how to project a 3D point onto the photo. [Issue #13](https://github.com/windBlick/windBlick/issues/13)

## Coordinates and heights

| Frame | Axes and units |
| --- | --- |
| API turbine and map positions | EPSG:25832 with named `easting_m` and `northing_m` fields. |
| API camera input | EPSG:25832 or WGS 84 decimal degrees (`longitude_deg`, `latitude_deg`). The resolved camera is in EPSG:25832. |
| Absolute elevation | DHHN2016 normal height above NHN, in metres (`EPSG:7837`, API label `DHHN2016_NHN`). Camera elevation is the optical centre. Turbine elevation is the base at ground level. |
| Backend working CRS | ETRS89 / UTM zone 32N (`EPSG:25832`), with easting and northing in metres. |
| Local world | Right-handed frame at the optical centre. `E`, `N`, `U` are metres east, true north and up relative to that origin. |
| Camera | Right-handed frame at the optical centre. `Xc` points image-right, `Yc` image-down and `Zc` forward along the optical axis. |
| Image | The centre of the top-left pixel is `(0, 0)`. `x` increases rightward and `y` downward. Coordinates can be fractional. All dimensions and coordinates refer to the backend-normalized raster. |

Transform geographic camera coordinates and usable EXIF GPS from `EPSG:4326` into `EPSG:25832` with explicit longitude/latitude input and easting/northing output order. Use already projected positions directly. Read the declared CRS and axis order for each data source. The [windPRO examples](../example_image/example_visualizations/README.md) already use `EPSG:25832`. Data in `EPSG:32632` use the WGS 84 datum and must be transformed before combining with ETRS89 coordinates.

Subtract the camera's UTM coordinates from each point to obtain `dE`, `dN`. Rotate these offsets from grid north to true north at the camera. Let `a` be the clockwise grid bearing of true north, the negative of `Proj.get_factors(...).meridian_convergence` at the camera's ETRS89 longitude/latitude. Convert `a` from degrees to radians for these formulas. [pyproj projection factors](https://pyproj4.github.io/pyproj/stable/api/proj.html#pyproj.Proj.get_factors)

```text
E = dE * cos(a) - dN * sin(a)
N = dE * sin(a) + dN * cos(a)
```

Use UTM grid metres as a local scale approximation in the prototype. Add the turbine's model offsets to its base in the resulting local frame. The heading remains referenced to true north.

Use `U = H_point - H_camera`. Heights must share the vertical datum before subtraction. For example, a base at 100 m NHN and a hub height of 150 m give a hub at 250 m NHN. With the camera at 110 m NHN, the hub has `U = 140 m`. Camera height above the ground can be added to the ground elevation at the camera only if both values refer to that location. Treat raw EXIF or GNSS height with unknown reference as unresolved. The local model approximates the vertical with NHN differences and omits Earth curvature in that component. [BKG height reference](https://bkg.bund.de/themen/geodaesie/referenzsysteme/nationale-referenzsysteme)

## Camera orientation

| Field | Range | Sign and reference |
| --- | --- | --- |
| `heading_deg` | `[0°, 360°)` | Optical-axis bearing clockwise from **true north**. North 0°, east 90°, south 180°, west 270°. |
| `pitch_deg` | `(-90°, 90°)` | Angle of the optical axis above the local horizontal. Positive aims up. At vertical pitch, heading is undefined. |
| `roll_deg` | `[-180°, 180°)` | Rotation about the optical axis. Positive rotates the camera's right axis toward its zero-roll down axis. |

Convert heading `h`, pitch `p` and roll `r` to radians for trigonometry. The following vectors are expressed in local world coordinates. Dot products convert the camera-relative world point `P = (E, N, U)` to camera coordinates.

```text
forward = (sin(h)*cos(p), cos(h)*cos(p), sin(p))
right0  = (cos(h), -sin(h), 0)
down0   = (sin(h)*sin(p), cos(h)*sin(p), -cos(p))
right   = cos(r)*right0 + sin(r)*down0
down    = -sin(r)*right0 + cos(r)*down0
(Xc, Yc, Zc) = (dot(P, right), dot(P, down), dot(P, forward))
```

The rotor-facing azimuth is a separate input to the schematic turbine geometry. It describes the rotor plane's normal in the local model.

## Intrinsics and projection

Use a pinhole model with zero skew and no distortion correction. With normalized raster width `W` and height `H`, take calibrated `fx`, `fy`, `cx`, `cy` in pixels when provided. For the other variants use `cx = (W - 1)/2` and `cy = (H - 1)/2`.

- **Horizontal field of view:** `fx = fy = W / (2 * tan(horizontal_fov / 2))`, with the angle in radians. This assumes square pixels.
- **Physical focal length:** `fx = focal_length_mm * W / sensor_width_mm` and `fy = focal_length_mm * H / sensor_height_mm`. The effective sensor extent must match the final crop and orientation. A 35 mm equivalent or focal length alone is insufficient for this variant.
- **Projection:** for `Zc > 0`, `x = cx + fx * Xc / Zc`, `y = cy + fy * Yc / Zc`. Retain subpixel coordinates through projection. A point with `Zc <= 0` has no projected pixel. A valid projected point outside the raster can still be used for clipping a segment that crosses the image edge. [OpenCV pinhole model](https://docs.opencv.org/4.x/d9/d0c/group__calib3d.html)

## Image orientation and inputs

- Upload the original image. The backend applies EXIF rotation or reflection once. Preview clicks, projection, intrinsics and future reference points use the same upright raster. Convert preview clicks from CSS coordinates using the displayed image rectangle and scale, accounting for letterboxing and the pixel-centre convention.
- Normalize metadata from the source to the final image frame before using it. A 90° raster rotation swaps dimensions. A reflection cannot be represented by a roll alone. EXIF `Orientation` defines pixel layout. It supplies neither pitch nor roll.
- Explicit camera fields override usable EXIF per field. Unknown required measurements after resolution return `CAMERA_PARAMETERS_UNRESOLVED`. A magnetic heading needs a verified conversion. Browser `alpha`, `beta`, `gamma` require a device-to-optical-frame conversion that accounts for the lens, screen orientation and mirroring. [W3C device orientation](https://www.w3.org/TR/orientation-event/)

## Checks for implementation

Near Münster (`7.62° E`, `51.96° N`), true north has grid bearing about `+1.087°`. A point 100 m due north should have `E` near zero and `N` near 100 m after the rotation.

In a 101 × 101 raster with `fx = fy = 100` and `cx = cy = 50`, a level north-facing camera projects local points `(E, N, U)` as follows:

| Local point (m) | Expected pixel or outcome |
| --- | --- |
| `(0, 100, 0)` | `(50, 50)` |
| `(10, 100, 0)` | `(60, 50)` |
| `(0, 100, 10)` | `(50, 40)` |
| `(0, -100, 0)` or `(0, 0, 0)` | No pixel |

With `roll = +90°`, `(10, 100, 0)` moves to `(50, 40)`. With `heading = 90°` and zero pitch and roll, `(100, -10, 0)` projects to `(60, 50)`. Positive pitch moves a point on the level horizon down in the image. Use the normalized raster for a portrait-image regression as well. Coordinate conversion and projection implementation belong to [#21](https://github.com/windBlick/windBlick/issues/21) and [#22](https://github.com/windBlick/windBlick/issues/22).
