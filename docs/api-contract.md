# windBlick — Initial API contract (v0.1 draft)

## 1. Responsibilities and design decisions

The frontend sends the original image, selected turbines, and optional camera overrides. The backend extracts camera metadata from the uploaded image's EXIF by default. Every camera value may be omitted from the request: a supplied value takes precedence over EXIF for that field; an omitted value is resolved only from usable EXIF, including documented conversions. The frontend does not need to parse or rewrite EXIF. Browser sensors, manual input, and prepared fixtures can supply explicit overrides through the same JSON fields.

This separates capture from rendering and supports future in-browser capture with sensor observations that never become image metadata. “Individual parameters” means independent JSON fields in one complete request, not one HTTP request per field. Each rendering request is self-contained; omitted fields do not inherit values from a previous request.

| Component | Responsibility |
| --- | --- |
| Frontend | Preview and upload the original image with EXIF preserved; allow optional camera corrections; convert any explicitly supplied device readings to the contract convention; select NRW WFS turbines; show results and field-specific errors. |
| Python backend | Decode and normalize image orientation; extract and normalize supported EXIF; apply explicit camera overrides per field; validate the resolved camera; transform coordinates and render; return effective values and their origins. Keep metadata resolution separate from projection. |
| WFS integration adapter | Read the fixed NRW service, convert source strings/geometry into typed records, and preserve provenance/status. The adapter may run client-side or behind an approved backend proxy; that deployment choice is separate from the rendering contract. |
| Future calibration backend | Resolve reference-point surface heights from a DSM, check quality/coverage, and estimate pose. The frontend sends matched image pixels and map coordinates, not DSM heights. |

Status is carried for neutral interpretation and possible status-based rendering colours. It also distinguishes the use cases of visualizing approved projects and comparing existing turbines against real photographs. Colour must not imply approval or opposition to wind power.

### Camera resolution: explicit value, then EXIF

1. Validate every supplied camera field, including nested values. An invalid override returns `422 VALIDATION_ERROR`; do not fall back to EXIF to hide the error. Omission means fallback; `null`, empty strings, and nonfinite numbers are invalid. Zero is an explicit value.
2. Read supported EXIF and normalize usable values to the contract's units, coordinate frames, and image orientation. Use a maintained metadata/image library, not a custom binary EXIF parser. Unsupported, ambiguous, or malformed camera tags are unavailable values, not guessed measurements.
3. Merge at individual field level: supplied values win. Omitting `camera`, sending `{}`, or omitting a nested object supplies no overrides for that object. For example, supplying only `camera.orientation.heading_deg` leaves pitch and roll eligible for EXIF fallback. No previous request, browser sensor, device database, terrain service, or numeric default supplies missing camera measurements.
4. Validate the resolved camera before projection. Rendering still needs a complete position, orientation, and usable intrinsics. If EXIF cannot fill an omitted value, return `422 CAMERA_PARAMETERS_UNRESOLVED` with all unresolved field paths and actionable reasons. Optional request fields do not make the underlying geometry optional.
5. Return `camera_used` and `camera_value_sources` on success. Explicit overrides are never silently replaced by EXIF or calibration. No automatic calibration is enabled in v0.1.

Coordinate/frame labels are contract conventions, not estimated measurements: explicit angles use degrees and true north; explicit camera elevation values use DHHN2016 NHN. Omitting such labels does not permit relabelling raw EXIF as compliant data.

### Supported EXIF interpretation and limits

| Target | Backend rule |
| --- | --- |
| Longitude / latitude | Decode EXIF GPS coordinates and hemisphere references, validate the declared horizontal datum, and convert to WGS84 if supported. An absent/ambiguous datum needs a documented supported interpretation; otherwise report the coordinate as unresolved. |
| Heading | Accept a supported image-direction field only with a known north reference and camera-axis meaning. Magnetic direction requires a documented conversion; without one, request an explicit true-north override. Travel direction is not viewing direction. |
| Pitch / roll | Accept only supported tags with documented axes/signs and a tested conversion to the normalized image frame. EXIF image orientation is not a measurement of pitch or roll. Missing values never default to zero. Device-specific tag support remains an implementation decision to document with fixtures. |
| Camera elevation | Resolve only when the source height reference and conversion to DHHN2016 NHN are known. A generic GPS altitude must not be assumed to have this datum. If conversion is unavailable, request an explicit elevation value. No DSM/terrain lookup is introduced. |
| Intrinsics | Decode actual focal length and any reliably usable effective sensor extent for the final raster. Focal length alone, a device name, or an unexplained 35 mm equivalent does not establish complete intrinsics. Missing or ambiguous components require overrides. |

EXIF-only requests are valid inputs but do not promise successful rendering for arbitrary photos. The supported tag/conversion matrix must be recorded during implementation; until a conversion is supported, return unresolved fields. Malformed camera tags do not prevent rendering when valid overrides supply all affected measurements; unsafe/unreadable images still fail image validation.

## 2. Transport

**Proposed endpoint:** `POST /api/v0/visualizations`, synchronous.

Send `multipart/form-data` with exactly these two parts:

| Part | Required | Content type | Contents |
| --- | --- | --- | --- |
| `image` | Yes | `image/jpeg` or `image/png` | One non-animated original raster image, preserving available EXIF; binary bytes, not base64. The backend normalizes orientation. |
| `parameters` | Yes | `application/json` | UTF-8 JSON object described below. |

Reject duplicate/missing parts and additional image files. In a browser, let `FormData` generate the multipart boundary; do not set the outer `Content-Type` manually. Successful responses use `application/json`; errors use `application/problem+json`.

Proposed initial limits for team review: 20 MiB image file, 24 million decoded pixels, 1 MiB JSON part, 100 turbines, and 40 MiB encoded output PNG before base64. These are resource limits, not a single-turbine product design. Enforce limits before expensive work where possible; do not truncate arrays. Revisit the values with representative photos before implementation. No jobs, persistent photo store, or result-download endpoint are introduced in v0.1.

## 3. Shared types and general rules

| Type | Definition |
| --- | --- |
| `Id` | Nonempty string, at most 128 characters; unique within its request collection. |
| `Number` | Finite JSON number. Numeric strings, `NaN`, and infinity are invalid. |
| `Timestamp` | RFC 3339 date-time with explicit UTC offset, preferably `Z`. |
| `Coordinates` | `{longitude_deg, latitude_deg}` in WGS84 horizontal coordinates; longitude −180…180, latitude −90…90. Named keys avoid positional axis ambiguity. |
| `Elevation` | `{value_m, datum, source, uncertainty_m?}`. v0.1 uses absolute height above NHN in DHHN2016: `datum: "DHHN2016_NHN"`. `source` is `survey`, `user_input`, `fixture`, or `backend_model` for turbine inputs; camera overrides and resolved camera elevations also allow `exif`. Optional uncertainty is a nonnegative number in metres. |
| `Position` | `Coordinates` plus required `elevation: Elevation`; used for turbines and the fully resolved camera. |
| `CameraPositionOverride` | Optional `longitude_deg`, `latitude_deg`, and `elevation` with optional members. Missing measurements use EXIF; supplied values must satisfy the same numeric bounds as `Position`. |
| `PixelPoint` | `{x_px, y_px}`, finite subpixel coordinates in the backend-normalized image. |
| `FieldProvenance` | `{source, observed_at?, note?}`. Source: `exif`, `device_sensor`, `user_input`, `wfs`, `fixture`, or `derived`. |

Unknown optional values are omitted, not sent as empty strings or `null`. Zero is a real number, never a missing-value marker. Turbine status is required and accepts only `operating` or `approved`. Missing, unknown, and unsupported statuses are validation errors; there is no fallback status. Unexpected fields are rejected in requests to catch spelling mistakes; clients ignore additional response fields. Breaking changes to an adopted contract require a new version. This EXIF/override decision revises the unimplemented v0.1 draft in place; consumers must review the new upload and resolution semantics before implementation. `api_version` must equal `"0.1"`.

GPS latitude/longitude does **not** establish camera elevation. The camera's elevation is the optical centre's absolute elevation; a turbine's elevation is its base elevation, not its hub height. All elevations must be in the same datum before subtraction. Browser/GPS ellipsoidal altitude cannot simply be labelled NHN. The resolved camera and explicit turbine elevations must use the agreed datum. Camera elevation may be omitted in the request, but unusable or ambiguous EXIF height requires an explicit override; unsupported explicit datums are rejected. Later backend terrain lookup can supply base elevation and camera height offsets without changing the meaning of these values. The frontend is not required to implement terrain or DSM lookup.

## 4. Request fields

R = required in the JSON request; O = optional in the request. All camera fields are O. The backend separately requires a complete resolved camera after EXIF fallback. Intrinsics variants describe complete resolved inputs, not mandatory request fields.

### Root and image

| Field | Type | Required | Meaning / validation |
| --- | --- | --- | --- |
| `api_version` | String literal | R | `"0.1"`. |
| `image` | ImageDescription | O | Optional assertions about the backend-normalized image; the binary multipart image is still required. |
| `camera` | CameraOverrides | O | Partial, independently editable camera overrides; omitted or `{}` means EXIF only. |
| `turbines` | Turbine[] | R | 1–100 complete turbine records. Input order also defines fallback numbering. |
| `provenance` | Map of JSON Pointer → FieldProvenance | O | Origin of selected parameter values, e.g. `/camera/orientation/heading_deg`. Pointers must resolve to submitted parameters outside `provenance` itself. No duplicate copy of raw personal metadata. |
| `reference_points` | ReferencePoint[] | O, reserved | Omit or send `[]` in v0.1. Nonempty input returns `FEATURE_NOT_SUPPORTED`; never silently ignore it. |
| `image.width_px` | Positive integer | O | Expected width after backend EXIF orientation normalization; verify against decoded pixels. |
| `image.height_px` | Positive integer | O | Expected height after backend EXIF orientation normalization. |
| `image.orientation` | String literal | O | `"normalized"` asserts that uploaded pixels are already upright and EXIF orientation is absent or 1. Omit for original photos. |
| `image.captured_at` | Timestamp | O | Actual photo capture time, if known. Do not substitute upload time. |

**Normalization:** Upload the original file by default; do not re-encode it merely to preview it or write corrections into EXIF. The backend reads metadata before applying EXIF rotation/reflection exactly once, then renders in the upright image frame. For example, a 1200 × 800 stored raster rotated by 90° produces an 800 × 1200 normalized raster. Optional dimension assertions describe that normalized result. An explicit `image.orientation: "normalized"` assertion conflicting with EXIF returns `IMAGE_NOT_NORMALIZED`. Missing orientation means identity; malformed/unsupported structural orientation returns `INVALID_IMAGE`. Preview, camera overrides, and future reference points must use the same normalized frame. EXIF-derived pose and intrinsics must be transformed into that frame together with the pixels.

Cropping/resizing/re-encoding is not required for the MVP. If a client nevertheless submits an edited raster, it must remove stale camera tags and supply affected effective parameters, retaining only metadata that still applies. Missing values cannot be reconstructed from stripped EXIF. Do not copy private EXIF into the output PNG or logs; retain original uploads only for request processing. A suitable established orientation operation is documented by [Pillow ImageOps.exif_transpose](https://pillow.readthedocs.io/en/stable/reference/ImageOps.html#PIL.ImageOps.exif_transpose).

Pixel centres use origin `(0, 0)` at the top-left, x rightwards and y downwards. Valid reference-point centres satisfy `0 <= x_px <= width_px - 1` and `0 <= y_px <= height_px - 1`. Projection results may fall outside these bounds. Intrinsics and reference points always belong to this exact backend-normalized raster, not the preview's CSS dimensions.

### Camera position and orientation

| Field | Type | Required | Meaning / validation |
| --- | --- | --- | --- |
| `camera.position` | CameraPositionOverride | O | Partial optical-centre position; never replaces turbine positions. |
| `camera.position.longitude_deg` | Number | O | WGS84 longitude, −180…180. Overrides only longitude. |
| `camera.position.latitude_deg` | Number | O | WGS84 latitude, −90…90. Overrides only latitude. |
| `camera.position.elevation` | CameraElevationOverride | O | Optional `value_m`, `datum`, `source`, `uncertainty_m`. An explicit `value_m` is in DHHN2016 NHN; omitted `datum` means that contract convention and omitted `source` means `user_input`. With no value override, EXIF height must independently establish its datum; supplied labels cannot relabel it. |
| `camera.orientation` | OrientationOverrides | O | Partial orientation object; `{}` means no orientation overrides. |
| `camera.orientation.heading_deg` | Number | O | Camera viewing azimuth, clockwise from true north: `0 <= h < 360`. North 0, east 90, south 180, west 270. |
| `camera.orientation.pitch_deg` | Number | O | Optical-axis elevation angle, positive upwards; `-90 < p < 90`. |
| `camera.orientation.roll_deg` | Number | O | Camera rotation around its viewing axis; `-180 <= r < 180`. Exact axis convention below. |
| `camera.orientation.north_reference` | String literal | O | `"true"`; this convention also applies to explicit headings when omitted. It does not override a magnetic EXIF reference. |
| `camera.intrinsics` | IntrinsicsOverrides | O | Partial values from one variant below; every member, including `kind`, is optional. |

Missing pitch, roll, heading, or elevation in the request is allowed. Missing measurements after EXIF resolution are errors. A user may explicitly assume zero for an angle, with `user_input` provenance and a note; the backend must not make that assumption invisibly. Uncertainty/source metadata for an overridden measurement must not be inherited from the displaced EXIF measurement. A supplied source/uncertainty describes the effective value but does not certify its correctness.

**Device-to-camera conversion:** Browser `alpha/beta/gamma` are device-axis rotations, not contract heading/pitch/roll. A capture adapter must account for the selected front/rear lens, display orientation, mirroring, and image normalization, then convert the resulting optical frame. There is no universally correct `heading = alpha` shortcut. Retain observation timestamps in provenance when available; unavailable true north requires manual orientation. Validate the adapter with known directions/tilts on real devices. This conversion does not move the backend's world-to-image projection into the frontend. See the [W3C orientation model](https://www.w3.org/TR/orientation-event/).

To make the proposed roll convention reproducible, use a local east/north/up frame. After converting degrees to radians:

```text
forward = (sin(h)*cos(p), cos(h)*cos(p), sin(p))
right0  = (cos(h), -sin(h), 0)
down0   = (sin(h)*sin(p), cos(h)*sin(p), -cos(p))

right = cos(r)*right0 + sin(r)*down0
down  = -sin(r)*right0 + cos(r)*down0

(Xc, Yc, Zc) = (dot(delta, right), dot(delta, down), dot(delta, forward))
```

Positive roll rotates the camera's right axis towards its zero-roll down axis. Camera axes are x right, y down, z forward. For a level north-facing camera, east projects right and increasing elevation projects up. For a level east-facing camera, south projects right. True north and projected-grid north must not be silently equated; account for grid convergence if using a projected work frame. Final CRS/height transformation implementation is coordinated in [#13](https://github.com/windBlick/windBlick/issues/13).

### Camera intrinsics: optional overrides within one variant

A physical focal length alone is insufficient to determine image scale. All fields below are optional overrides. A complete variant must be resolved before rendering. Select the variant with optional `kind`; without it, infer the variant from supplied member names (which are disjoint). With no intrinsic overrides, attempt the physical-focal-length variant from EXIF. Do not combine incompatible variants. Within the selected variant, fill omitted members only from usable EXIF and documented conversions; a missing member is not a schema error, but may remain unresolved at runtime. For example, `{"focal_length_mm": 6}` overrides focal length and still requires usable EXIF sensor extents or further overrides.

| `kind` | Fields | Request requirement | Interpretation |
| --- | --- | --- | --- |
| `horizontal_fov` | `horizontal_fov_deg`: Number | O | Effective horizontal field of view of the submitted image, strictly between 0° and 180°. Assumes square pixels and a centred principal point. |
| `physical_focal_length` | `focal_length_mm`, `sensor_width_mm`, `sensor_height_mm`: positive Numbers | O, each field | Actual focal length and effective sensor extent represented by the submitted raster, in its final orientation and crop. |
| `calibrated` | `fx_px`, `fy_px`: positive Numbers; `cx_px`, `cy_px`: Numbers | O, each field | Intrinsics already expressed for the submitted raster. Principal point must lie within the image in v0.1. |

Do not send fields from multiple variants. With image width W and height H:

- Horizontal FOV: `fx = W / (2 * tan(horizontal_fov / 2))`; `fy = fx`.
- Physical focal length: `fx = focal_length_mm * W / sensor_width_mm`; `fy = focal_length_mm * H / sensor_height_mm`.
- Both uncalibrated variants use `cx = (W - 1) / 2` and `cy = (H - 1) / 2`.
- Projection for `Zc > 0`: `x = fx * Xc / Zc + cx`, `y = fy * Yc / Zc + cy`.

Portrait rotation, crop, resizing, digital zoom, and stabilization can change the effective values. “35 mm equivalent focal length” is not interchangeable with physical focal length; convert only with an explicit justified convention and known crop, or request a usable FOV. Never supply a guessed phone sensor size based only on a filename/device label.

v0.1 uses a pinhole model without lens-distortion correction or skew. The backend reports this as an approximation; ultra-wide/distorted images may be unsuitable. Supporting distortion coefficients later requires a named model and agreed revision. Background for focal lengths in pixels and resizing: [OpenCV camera model](https://docs.opencv.org/4.x/d9/d0c/group__calib3d.html).

### Turbine

| Field within `turbines[]` | Type | Required | Meaning / validation |
| --- | --- | --- | --- |
| `id` | Id | R | Request identifier for results, errors, and UI selection. Unique within the request. |
| `name` | String, 1–200 chars | O | Human-readable source name; output label falls back to `Turbine 1`, `Turbine 2`, etc. by input order. Names need not be unique. |
| `position` | Position | R | Source coordinates plus explicit base elevation. The WFS hub height is not base elevation. |
| `hub_height_m` | Positive Number | R | Hub centre above the turbine base. |
| `rotor_diameter_m` | Positive Number | R | Rotor diameter, not radius or total height. |
| `turbine_type` | String, 1–200 chars | O | Manufacturer/model/type description if present. Not required by the schematic geometry. |
| `status` | Enum (string) | R | `operating` or `approved`, derived from the selected WFS layer. `approved` does not establish the current construction state. |
| `source` | TurbineSource | R | Provenance described below. |

`TurbineSource` fields: required `dataset: "nrw_renewable_energies_wfs"`, `feature_type` (one of the two supported full WFS layer names listed below), `feature_id` (string), `retrieved_at` (Timestamp), and `raw_status` (source status/layer label). Optional `unit_id` stores the source unit number and `data_as_of` preserves the source data-date text. `feature_type + feature_id` identifies the WFS record; reject repeated selection of that pair within one request.

The frontend submits a complete normalized snapshot of each selected record. The renderer validates it but does not re-query WFS by ID, fetch a client-supplied URL, or silently replace values. This makes a rendering reproducible. It does not certify client-supplied data as authentic. Normal product use takes dimensions from the selected WFS record; the contract's explicit values do not imply free turbine placement or a new dimension-editing UI.

A nonpositive or missing dimension rejects the request with a field-specific error. A missing name/type is allowed. Unrealistic-but-positive dimensions require explicit domain plausibility rules when those are agreed; source-data mistakes must not be presented as verified measurements. Rotor yaw/phase are not available in v0.1: use a documented schematic convention, return a warning, and do not promise real blade-position or rotor-span agreement.

## 5. NRW WFS adapter: verified source mapping

Checked on 9 November 2026 using [GetCapabilities](https://www.wfs.nrw.de/umwelt/erneuerbare_energien_wfs?SERVICE=WFS&REQUEST=GetCapabilities), DescribeFeatureType for the operating/approved layers, and one sample feature from each. This establishes schema and sample behaviour, not completeness of every record.

| Source | Contract target / rule |
| --- | --- |
| `msGeometry` | `position.longitude_deg/latitude_deg` after CRS and axis-order conversion; do not assume raw GML coordinates are longitude/latitude. Base elevation needs a separate source. |
| `nabenhoehe_m` | `hub_height_m`. Source schema declares a string; parse and validate explicitly. |
| `durchmesser_m` | `rotor_diameter_m`; likewise parse the source string. |
| `name_einheit` | Optional `name`; omit empty text. |
| `anlagentyp` | Optional `turbine_type`; omit empty text. |
| `einheitennummer` | Optional `source.unit_id`. Preserve feature identity separately. |
| `stand` | Optional `source.data_as_of`. This is not the planning status. |
| Feature identifier / layer | `source.feature_id` and `source.feature_type`; preserve provider identity rather than generating a display name as an ID. |
| `Windenergieinbetrieb` | `status: "operating"`. |
| `Windenergiegehnemigt` | `status: "approved"`. Preserve this exact service spelling; it does not prove whether construction has started or finished. |
| `Windenergiestillgelegt` | Outside the current selection/rendering scope. Do not submit these records; the API rejects this feature type. |

The full feature-type names use prefix `erneuerbare_energien_wfs:`. The inspected capabilities expose these three wind layers, but the application accepts only the operating and approved layers. It does not accept decommissioned, unknown, planned, or applied-for records. The adapter filters unsupported records before submission; the API independently validates the status and source layer. Fields in the inspected source schemas are optional, and sample features contain empty text.

A possible later extension is to integrate planned, not-yet-approved turbines from the Marktstammdatenregister (MaStR). This requires checking actual data availability, defining a source adapter and provenance, and agreeing a versioned contract extension. It is not an implemented source, accepted status, or current API requirement.

Use a single `status` string throughout requests and turbine results. It expresses the selected source category rather than two independently inferred lifecycle dimensions. For optional status-based colours, use that same value as the display category. A future colour palette needs a legend and redundant text labels; colours must not change dimensions or projection. The response reports the actual style used. Uniform colouring remains valid for the initial renderer.

## 6. Future reference points

The reserved `ReferencePoint` type is:

| Field | Type | Required when supported | Meaning |
| --- | --- | --- | --- |
| `id` | Id | Yes | Stable pairing and diagnostics identifier. |
| `image_point` | PixelPoint | Yes | Click in the backend-normalized photograph, using the matching preview coordinate frame. |
| `map_position` | Coordinates | Yes | The same physical feature identified in the overhead image, converted to WGS84. |
| `map_source` | String | Optional | Orthophoto/source identifier for provenance, not a URL to fetch blindly. |
| `map_date` | String | Optional | Source date/version if known. |

Illustrative future entry:

```json
{
  "id": "anchor-1",
  "image_point": {"x_px": 410.5, "y_px": 380.25},
  "map_position": {"longitude_deg": 7.5101, "latitude_deg": 52.1101},
  "map_source": "documented-orthophoto-layer",
  "map_date": "2026"
}
```

There is intentionally no frontend `elevation` field for reference points. The future backend obtains surface elevations from a DSM and records dataset, vertical datum, sampling method, resolution, and coverage/NoData checks. A roof point must use the roof surface, not DTM ground height; sampling at edges and vegetation needs uncertainty checks. A 2D coordinate plus a DSM sample does not guarantee that the clicked physical feature was identified correctly.

Nonempty points are rejected in v0.1. Before enabling them in a later version, define the solver, parameters to refine, minimum/degenerate configurations, quality criteria, DSM failure semantics, and a calibration-result schema with resolved heights, residuals, and accepted/rejected point IDs. Optional camera overrides and EXIF fallback are independent of this reserved field; unresolved camera values remain errors until an explicitly supported calibration workflow exists.

## 7. Request example and browser submission

[request-example.json](api/request-example.json) supplies complete explicit camera overrides for a two-turbine request. [request-exif-example.json](api/request-exif-example.json) omits `camera` entirely. [request-partial-override-example.json](api/request-partial-override-example.json) overrides only heading and focal length, demonstrating leaf-level fallback. All examples validate as request JSON; EXIF-only and partial examples render only if the accompanying image supplies the remaining usable camera values. Coordinates, dimensions, camera values, and feature IDs are **illustrative**, not verified demo measurements or real WFS IDs. The full-override example must accompany a photo whose backend-normalized size is 1200 × 800; the other examples let the backend determine dimensions. Use real, checked WFS records for acceptance.

```js
// originalImageFile is the selected File, with its EXIF preserved.
// parameters contains turbines and any optional camera overrides.
const form = new FormData();
form.append("image", originalImageFile, originalImageFile.name);
form.append(
  "parameters",
  new Blob([JSON.stringify(parameters)], { type: "application/json" }),
  "parameters.json"
);

const response = await fetch("/api/v0/visualizations", {
  method: "POST",
  headers: { Accept: "application/json, application/problem+json" },
  body: form
});
const result = await response.json();
if (!response.ok) {
  // Associate result.errors entries with UI fields via their JSON pointers.
  throw result;
}
// The renderer's result contains base64 output, warnings, and turbine outcomes.
```

The request schema is [visualization-request.schema.json](api/visualization-request.schema.json), JSON Schema 2020-12. It validates the JSON part, not image bytes, CRS transforms, provider authenticity, or all cross-field constraints. The schema enforces the two supported source layers and their matching status values. The schema accepts absent/partial camera objects; it cannot establish EXIF availability or final camera completeness. Enforce metadata resolution, effective-value bounds, provenance bounds, uniqueness, normalized image-size agreement, and resource limits separately.

## 8. Successful response

Return `200 OK` with `Cache-Control: no-store`. v0.1 returns the PNG inline as base64 so that image and diagnostics arrive together without server-side result storage. This adds approximately one third to the encoded image size; a binary/temporary-URL response can be considered later if measurements justify it.

| Field | Type | Meaning |
| --- | --- | --- |
| `api_version` | `"0.1"` | Contract version. |
| `request_id` | String | Opaque server-generated correlation ID. |
| `image` | Object | `mime_type: "image/png"`, `encoding: "base64"`, `data` (base64 without a data-URL prefix), `width_px`, `height_px`. Output uses the backend-normalized raster dimensions, which may swap after EXIF orientation handling. |
| `camera_used` | Object | Effective `position` and `orientation` plus normalized `intrinsics: {fx_px, fy_px, cx_px, cy_px}`. Contains the complete values after EXIF resolution and explicit overrides, not merely the submitted fields. |
| `camera_value_sources` | Object | JSON Pointer into `camera_used` → `{source, input_paths?, exif_tags?}`. `source` is `override`, `exif`, or `derived`. Record each effective numeric camera value. `input_paths` is an optional array of JSON Pointers into the submitted parameters; `exif_tags` is an optional array of used tag names. Derived intrinsics identify the supplied fields and/or tags used; image-centre defaults come from normalized raster dimensions and the stated pinhole model. Tag names only, never a full raw EXIF dump. Client provenance is supplementary, not a replacement for backend resolution provenance. |
| `turbines` | TurbineResult[] | One result per requested turbine, in request order. |
| `warnings` | Warning[] | Always present, possibly empty; no warning-as-success replacement for invalid required inputs. |
| `calibration` | Object | `{ "applied": false }` in v0.1. |

`TurbineResult` contains `id`, `label` (name or fallback), `status` (the submitted `operating` or `approved` string), `source` (submitted provenance), `outcome`, `style`, and optional `projected_hub_px: PixelPoint`. Outcomes: `drawn` (including partial clipping), `outside_frame`, `behind_camera`. Projection coordinates can be outside image bounds; omit the projected hub if it is not projectable. Draw order is deterministic: farther turbines first, ties by request order; this is graphical layering, not terrain/building visibility analysis. For geometry crossing the camera plane, clip safely or report an explicit rendering limitation; never divide by zero or mirror geometry behind the camera.

`style` contains the effective `color_hex` (`#RRGGBB`) and `category` (`uniform`, `operating`, or `approved`). An example initial uniform style is `{"color_hex":"#2563EB","category":"uniform"}`; a future palette can reuse the submitted status field without changing the request.

`Warning` is `{code, message, path?, turbine_id?}`; `path` is a JSON Pointer into `parameters`. Example codes: `PINHOLE_APPROXIMATION`, `SCHEMATIC_ROTOR_ORIENTATION`, `TURBINE_OUTSIDE_FRAME`, `TURBINE_BEHIND_CAMERA`, `NO_TURBINES_DRAWN`. Human-readable messages are not stable identifiers.

If valid turbines are all outside the image/behind the camera, return the normalized photo as PNG, all outcomes, and `NO_TURBINES_DRAWN`. If an internal geometry/rendering failure occurs, return an error, not a misleading successful unchanged image. Validation is atomic: one invalid record rejects the whole request; do not silently omit it.

## 9. Errors and validation

Use [RFC 9457 Problem Details](https://www.rfc-editor.org/rfc/rfc9457.html). Each error response contains `type`, `title`, `status`, `detail`, `request_id`, a stable application `code`, and `errors` (possibly empty). Validation entries contain `path`, `code`, `message`. Paths address fields in the JSON parameters model, including omitted camera fields that could not be resolved; use `part: "image"` or `part: "parameters"` for multipart errors instead of a JSON pointer.

| HTTP status | Application codes / examples |
| --- | --- |
| 400 | `INVALID_MULTIPART`, `INVALID_JSON`, `DUPLICATE_PART`. |
| 413 | `IMAGE_TOO_LARGE`, `PIXEL_LIMIT_EXCEEDED`, `PARAMETERS_TOO_LARGE`, `TURBINE_LIMIT_EXCEEDED`. |
| 415 | `UNSUPPORTED_IMAGE_TYPE` or wrong request/part media type. |
| 422 | `VALIDATION_ERROR` (including missing/unsupported turbine status, unsupported source layer, or a status/layer mismatch), `CAMERA_PARAMETERS_UNRESOLVED`, `INVALID_IMAGE`, `IMAGE_DIMENSION_MISMATCH`, `IMAGE_NOT_NORMALIZED`, `UNSUPPORTED_VERTICAL_DATUM`, `UNSUPPORTED_API_VERSION`, `FEATURE_NOT_SUPPORTED`. |
| 500 | `INTERNAL_ERROR` for unexpected backend failures; no traceback or payload echo. |
| 503 | `RENDER_CAPACITY_EXCEEDED` or `OUTPUT_LIMIT_EXCEEDED`; explain retry/reduction without exposing internals. |

Check explicit version/reserved-feature/limit cases before generic schema validation so their codes stay predictable. Do not report JSON Schema's `maxItems: 0` error for a nonempty `reference_points` array as if calibration were merely malformed; report `FEATURE_NOT_SUPPORTED`. The renderer has no live WFS dependency once normalized records are submitted, so WFS retrieval errors belong to the source adapter.

```json
{
  "type": "about:blank",
  "title": "Unprocessable Content",
  "status": 422,
  "detail": "Camera parameters could not be resolved from overrides and EXIF.",
  "request_id": "example-request-id",
  "code": "CAMERA_PARAMETERS_UNRESOLVED",
  "errors": [
    {
      "path": "/camera/orientation/heading_deg",
      "code": "EXIF_MISSING_OR_UNUSABLE",
      "message": "No heading override or usable EXIF image direction. Provide a true-north heading in degrees."
    }
  ]
}
```

Use safe image decoding and temporary resource cleanup. Do not log photos, precise locations, or full parameters. Treat names/status text as untrusted display text. No arbitrary remote URL/file reads, server-side commands, or trust in client-provided limits. CORS/HTTPS/deployment controls follow the deployment decision, not client request fields.

### Contract verification required for implementation

- EXIF-only input, an omitted `camera`, and empty camera/nested objects produce the same resolved result for the same supported fixture.
- Partial longitude/latitude/orientation/intrinsics overrides replace only supplied values; explicit zero is preserved. Full overrides work without camera EXIF.
- Invalid/null overrides fail validation even if EXIF could supply valid alternatives. Unknown fields and mixed intrinsic variants remain invalid.
- Missing, malformed, unsupported, or ambiguous EXIF produces field-specific unresolved errors when needed, never guessed pitch/roll, sensor size, or height datum. All unresolved fields are reported together.
- Validate EXIF coordinates, north references, height references, and intrinsic conversions using small local fixtures with known expected values. No device database or network dependency is required.
- Rotated/reflected photos normalize exactly once; compare preview/output dimensions, projected locations, and effective intrinsics/pose in the same frame. Optional incorrect image assertions fail.
- Verify `camera_used` and `camera_value_sources` reflect precedence and conversions, and output images/logs do not expose raw EXIF. WFS status/layer and turbine-dimension checks remain unchanged.

These are acceptance requirements for the future backend, not claims of implemented tests. The current repository contains documentation and request schemas only.

### Technical references

- [Multipart form-data, RFC 7578](https://www.rfc-editor.org/rfc/rfc7578.html): binary image and separate JSON part.
- [OpenCV camera calibration and projection](https://docs.opencv.org/4.x/d9/d0c/group__calib3d.html): intrinsics and pixel-based projection.
- [W3C Device Orientation and Motion](https://www.w3.org/TR/orientation-event/): device-coordinate conventions; capture support must be checked per device.
- [NRW Renewable Energies WFS](https://www.wfs.nrw.de/umwelt/erneuerbare_energien_wfs?SERVICE=WFS&REQUEST=GetCapabilities): source feature types; adapter mapping was inspected live as described above.
- [Problem Details, RFC 9457](https://www.rfc-editor.org/rfc/rfc9457.html): structured HTTP errors.
