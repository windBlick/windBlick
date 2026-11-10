# windBlick — Initial API contract (v0.1 draft)

## 1. Responsibilities and design decisions

The frontend sends the image and explicit, individually editable parameters. It may obtain those parameters from EXIF, browser sensors, manual input, or a prepared fixture. User corrections replace the relevant values before submission. The backend validates the submitted values and uses them as the effective calculation inputs; it does not recover missing camera parameters from EXIF or overwrite explicit values with image metadata.

This separates capture from rendering and supports future in-browser capture with sensor observations that never become image metadata. “Individual parameters” means independent JSON fields in one complete request, not one HTTP request per field. Each rendering request is self-contained; omitted fields do not inherit values from a previous request.

| Component | Responsibility |
| --- | --- |
| Frontend | Decode metadata where useful; normalize the image; convert device orientation to the contract's camera convention; allow manual camera corrections; select NRW WFS turbines; construct the request and show results/errors. |
| Python backend | Independently validate all inputs; decode image pixels and verify dimensions; transform coordinates; project/render all selected turbines; return diagnostics. No camera-metadata inference. |
| WFS integration adapter | Read the fixed NRW service, convert source strings/geometry into typed records, and preserve provenance/status. The adapter may run client-side or behind an approved backend proxy; that deployment choice is separate from the rendering contract. |
| Future calibration backend | Resolve reference-point surface heights from a DSM, check quality/coverage, and estimate pose. The frontend sends matched image pixels and map coordinates, not DSM heights. |

Status is carried for neutral interpretation and possible status-based rendering colours. It also distinguishes the use cases of visualizing approved projects and comparing existing turbines against real photographs. Colour must not imply approval or opposition to wind power.

## 2. Transport

**Proposed endpoint:** `POST /api/v0/visualizations`, synchronous.

Send `multipart/form-data` with exactly these two parts:

| Part | Required | Content type | Contents |
| --- | --- | --- | --- |
| `image` | Yes | `image/jpeg` or `image/png` | One normalized, non-animated raster image; binary bytes, not base64. |
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
| `Elevation` | `{value_m, datum, source, uncertainty_m?}`. v0.1 uses absolute height above NHN in DHHN2016: `datum: "DHHN2016_NHN"`. `source` is `survey`, `user_input`, `fixture`, or `backend_model`. Optional uncertainty is a nonnegative number in metres. |
| `Position` | `Coordinates` plus required `elevation: Elevation`. |
| `PixelPoint` | `{x_px, y_px}`, finite subpixel coordinates in the submitted normalized image. |
| `FieldProvenance` | `{source, observed_at?, note?}`. Source: `exif`, `device_sensor`, `user_input`, `wfs`, `fixture`, or `derived`. |

Unknown optional values are omitted, not sent as empty strings or `null`. Zero is a real number, never a missing-value marker. Turbine status is required and accepts only `operating` or `approved`. Missing, unknown, and unsupported statuses are validation errors; there is no fallback status. Unexpected fields are rejected in requests to catch spelling mistakes; clients ignore additional response fields. Breaking changes require a new contract version. `api_version` must equal `"0.1"`.

GPS latitude/longitude does **not** establish camera elevation. The camera's elevation is the optical centre's absolute elevation; a turbine's elevation is its base elevation, not its hub height. All elevations must be in the same datum before subtraction. Browser/GPS ellipsoidal altitude cannot simply be labelled NHN. v0.1 requires explicit fixture/manual/surveyed elevations in the agreed datum and rejects other datums. Later backend terrain lookup can supply base elevation and camera height offsets without changing the meaning of these values. The frontend is not required to implement terrain or DSM lookup.

## 4. Request fields

R = required for a rendering request; O = optional; C = conditionally required for the selected variant.

### Root and image

| Field | Type | Required | Meaning / validation |
| --- | --- | --- | --- |
| `api_version` | String literal | R | `"0.1"`. |
| `image` | ImageDescription | R | Describes the uploaded binary image. |
| `camera` | Camera | R | Effective camera parameters used for rendering. |
| `turbines` | Turbine[] | R | 1–100 complete turbine records. Input order also defines fallback numbering. |
| `provenance` | Map of JSON Pointer → FieldProvenance | O | Origin of selected parameter values, e.g. `/camera/orientation/heading_deg`. Pointers must resolve to submitted parameters outside `provenance` itself. No duplicate copy of raw personal metadata. |
| `reference_points` | ReferencePoint[] | O, reserved | Omit or send `[]` in v0.1. Nonempty input returns `FEATURE_NOT_SUPPORTED`; never silently ignore it. |
| `image.width_px` | Positive integer | R | Decoded width after orientation/cropping/resizing. |
| `image.height_px` | Positive integer | R | Decoded height after orientation/cropping/resizing. |
| `image.orientation` | String literal | R | `"normalized"`. |
| `image.captured_at` | Timestamp | O | Actual photo capture time, if known. Do not substitute upload time. |

**Normalization:** The frontend uploads the image exactly as shown for marking/comparison: upright, not mirrored, with EXIF orientation absent or 1. All cropping/rotation/resizing must already be applied. The backend checks the declared dimensions against the decoded raster and rejects conflicting orientation metadata instead of silently rotating again. Reading structural orientation for validation is distinct from extracting camera parameters. Do not transmit unnecessary EXIF GPS/device data.

Pixel centres use origin `(0, 0)` at the top-left, x rightwards and y downwards. Valid reference-point centres satisfy `0 <= x_px <= width_px - 1` and `0 <= y_px <= height_px - 1`. Projection results may fall outside these bounds. Intrinsics and reference points always belong to this exact normalized raster, not the preview's CSS dimensions.

### Camera position and orientation

| Field | Type | Required | Meaning / validation |
| --- | --- | --- | --- |
| `camera.position` | Position | R | Optical-centre longitude, latitude, and absolute elevation. |
| `camera.orientation.heading_deg` | Number | R | Camera viewing azimuth, clockwise from true north: `0 <= h < 360`. North 0, east 90, south 180, west 270. |
| `camera.orientation.pitch_deg` | Number | R | Optical-axis elevation angle, positive upwards; v0.1 accepts `-90 < p < 90`. |
| `camera.orientation.roll_deg` | Number | R | Camera rotation around its viewing axis; `-180 <= r < 180`. Exact axis convention below. |
| `camera.orientation.north_reference` | String literal | R | `"true"`. Magnetic or arbitrary-relative headings must be converted or manually replaced before submission. |
| `camera.intrinsics` | Intrinsics union | R | Exactly one of the three variants below. |

Missing pitch or roll is an error. A user may explicitly assume zero, with `user_input` provenance and a note; the backend must not make that assumption invisibly. The same applies to heading and elevation.

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

### Camera intrinsics: choose exactly one variant

A physical focal length alone is insufficient to determine image scale. The following variants make the missing information explicit.

| `kind` | Fields | Required | Interpretation |
| --- | --- | --- | --- |
| `horizontal_fov` | `horizontal_fov_deg`: Number | C | Effective horizontal field of view of the submitted image, strictly between 0° and 180°. Assumes square pixels and a centred principal point. |
| `physical_focal_length` | `focal_length_mm`, `sensor_width_mm`, `sensor_height_mm`: positive Numbers | C, all three | Actual focal length and effective sensor extent represented by the submitted raster, in its final orientation and crop. |
| `calibrated` | `fx_px`, `fy_px`: positive Numbers; `cx_px`, `cy_px`: Numbers | C, all four | Intrinsics already expressed for the submitted raster. Principal point must lie within the image in v0.1. |

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
| `image_point` | PixelPoint | Yes | Click in the submitted normalized photograph. |
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

Nonempty points are rejected in v0.1. Before enabling them in a later version, define the solver, parameters to refine, minimum/degenerate configurations, quality criteria, DSM failure semantics, and a calibration-result schema with resolved heights, residuals, and accepted/rejected point IDs. Do not make manual camera inputs optional merely because this reserved field exists.

## 7. Request example and browser submission

[request-example.json](api/request-example.json) is a complete two-turbine parameters example. Coordinates, dimensions, camera values, and feature IDs are **illustrative**, not verified demo measurements or real WFS IDs. It must accompany an actual normalized 1200 × 800 image. Use real, checked WFS records for acceptance.

```js
// normalizedImageBlob and parameters are prepared by the frontend.
const form = new FormData();
form.append("image", normalizedImageBlob, "photo.jpg");
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

The request schema is [visualization-request.schema.json](api/visualization-request.schema.json), JSON Schema 2020-12. It validates the JSON part, not image bytes, CRS transforms, provider authenticity, or all cross-field constraints. The schema enforces the two supported source layers and their matching status values. Enforce field/provenance bounds, uniqueness, image-size agreement, and resource limits separately.

## 8. Successful response

Return `200 OK` with `Cache-Control: no-store`. v0.1 returns the PNG inline as base64 so that image and diagnostics arrive together without server-side result storage. This adds approximately one third to the encoded image size; a binary/temporary-URL response can be considered later if measurements justify it.

| Field | Type | Meaning |
| --- | --- | --- |
| `api_version` | `"0.1"` | Contract version. |
| `request_id` | String | Opaque server-generated correlation ID. |
| `image` | Object | `mime_type: "image/png"`, `encoding: "base64"`, `data` (base64 without a data-URL prefix), `width_px`, `height_px`. Output uses the submitted raster dimensions. |
| `camera_used` | Object | Effective `position` and `orientation` plus normalized `intrinsics: {fx_px, fy_px, cx_px, cy_px}`. No silent camera correction in v0.1. |
| `turbines` | TurbineResult[] | One result per requested turbine, in request order. |
| `warnings` | Warning[] | Always present, possibly empty; no warning-as-success replacement for invalid required inputs. |
| `calibration` | Object | `{ "applied": false }` in v0.1. |

`TurbineResult` contains `id`, `label` (name or fallback), `status` (the submitted `operating` or `approved` string), `source` (submitted provenance), `outcome`, `style`, and optional `projected_hub_px: PixelPoint`. Outcomes: `drawn` (including partial clipping), `outside_frame`, `behind_camera`. Projection coordinates can be outside image bounds; omit the projected hub if it is not projectable. Draw order is deterministic: farther turbines first, ties by request order; this is graphical layering, not terrain/building visibility analysis. For geometry crossing the camera plane, clip safely or report an explicit rendering limitation; never divide by zero or mirror geometry behind the camera.

`style` contains the effective `color_hex` (`#RRGGBB`) and `category` (`uniform`, `operating`, or `approved`). An example initial uniform style is `{"color_hex":"#2563EB","category":"uniform"}`; a future palette can reuse the submitted status field without changing the request.

`Warning` is `{code, message, path?, turbine_id?}`; `path` is a JSON Pointer into `parameters`. Example codes: `PINHOLE_APPROXIMATION`, `SCHEMATIC_ROTOR_ORIENTATION`, `TURBINE_OUTSIDE_FRAME`, `TURBINE_BEHIND_CAMERA`, `NO_TURBINES_DRAWN`. Human-readable messages are not stable identifiers.

If valid turbines are all outside the image/behind the camera, return the normalized photo as PNG, all outcomes, and `NO_TURBINES_DRAWN`. If an internal geometry/rendering failure occurs, return an error, not a misleading successful unchanged image. Validation is atomic: one invalid record rejects the whole request; do not silently omit it.

## 9. Errors and validation

Use [RFC 9457 Problem Details](https://www.rfc-editor.org/rfc/rfc9457.html). Each error response contains `type`, `title`, `status`, `detail`, `request_id`, a stable application `code`, and `errors` (possibly empty). Validation entries contain `path`, `code`, `message`. Paths address the JSON parameters object; use `part: "image"` or `part: "parameters"` for multipart errors instead of a JSON pointer.

| HTTP status | Application codes / examples |
| --- | --- |
| 400 | `INVALID_MULTIPART`, `INVALID_JSON`, `DUPLICATE_PART`. |
| 413 | `IMAGE_TOO_LARGE`, `PIXEL_LIMIT_EXCEEDED`, `PARAMETERS_TOO_LARGE`, `TURBINE_LIMIT_EXCEEDED`. |
| 415 | `UNSUPPORTED_IMAGE_TYPE` or wrong request/part media type. |
| 422 | `VALIDATION_ERROR` (including missing/unsupported turbine status, unsupported source layer, or a status/layer mismatch), `INVALID_IMAGE`, `IMAGE_DIMENSION_MISMATCH`, `IMAGE_NOT_NORMALIZED`, `UNSUPPORTED_VERTICAL_DATUM`, `UNSUPPORTED_API_VERSION`, `FEATURE_NOT_SUPPORTED`. |
| 500 | `INTERNAL_ERROR` for unexpected backend failures; no traceback or payload echo. |
| 503 | `RENDER_CAPACITY_EXCEEDED` or `OUTPUT_LIMIT_EXCEEDED`; explain retry/reduction without exposing internals. |

Check explicit version/reserved-feature/limit cases before generic schema validation so their codes stay predictable. Do not report JSON Schema's `maxItems: 0` error for a nonempty `reference_points` array as if calibration were merely malformed; report `FEATURE_NOT_SUPPORTED`. The renderer has no live WFS dependency once normalized records are submitted, so WFS retrieval errors belong to the source adapter.

```json
{
  "type": "about:blank",
  "title": "Unprocessable Content",
  "status": 422,
  "detail": "A required camera parameter is missing.",
  "request_id": "example-request-id",
  "code": "VALIDATION_ERROR",
  "errors": [
    {
      "path": "/camera/orientation/heading_deg",
      "code": "REQUIRED",
      "message": "Provide a true-north heading in degrees."
    }
  ]
}
```

Use safe image decoding and temporary resource cleanup. Do not log photos, precise locations, or full parameters. Treat names/status text as untrusted display text. No arbitrary remote URL/file reads, server-side commands, or trust in client-provided limits. CORS/HTTPS/deployment controls follow the deployment decision, not client request fields.

### Technical references

- [Multipart form-data, RFC 7578](https://www.rfc-editor.org/rfc/rfc7578.html): binary image and separate JSON part.
- [OpenCV camera calibration and projection](https://docs.opencv.org/4.x/d9/d0c/group__calib3d.html): intrinsics and pixel-based projection.
- [W3C Device Orientation and Motion](https://www.w3.org/TR/orientation-event/): device-coordinate conventions; capture support must be checked per device.
- [NRW Renewable Energies WFS](https://www.wfs.nrw.de/umwelt/erneuerbare_energien_wfs?SERVICE=WFS&REQUEST=GetCapabilities): source feature types; adapter mapping was inspected live as described above.
- [Problem Details, RFC 9457](https://www.rfc-editor.org/rfc/rfc9457.html): structured HTTP errors.
