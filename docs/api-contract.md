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
2. Read supported EXIF and normalize usable values to their documented units, coordinate frames, and image orientation. Resolve the camera's horizontal position using the rules in Section 4. Use a maintained metadata/image library, not a custom binary EXIF parser. Unsupported, ambiguous, or malformed camera tags are unavailable values, not guessed measurements.
3. Merge at individual field level: supplied values win. Omitting `camera`, sending `{}`, or omitting a nested object supplies no overrides for that object. For example, supplying only `camera.orientation.heading_deg` leaves pitch and roll eligible for EXIF fallback. No previous request, browser sensor, device database, terrain service, or numeric default supplies missing camera measurements.
4. Validate the resolved camera before projection. Rendering still needs a complete position, orientation, and usable intrinsics. If EXIF cannot fill an omitted value, return `422 CAMERA_PARAMETERS_UNRESOLVED` with all unresolved field paths and actionable reasons. Optional request fields do not make the underlying geometry optional.
5. Return `camera_used` and `camera_value_sources` on success. Explicit overrides are never silently replaced by EXIF or calibration. No automatic calibration is enabled in v0.1.

Coordinate/frame labels are contract conventions, not estimated measurements: explicit angles use degrees and true north; explicit camera elevation values use DHHN2016 NHN. Omitting such labels does not permit relabelling raw EXIF as compliant data.

### Supported EXIF interpretation and limits

| Target | Backend rule |
| --- | --- |
| Longitude / latitude | Decode `GPSLongitude`, `GPSLatitude` and their hemisphere references. An absent `GPSMapDatum` is interpreted as WGS84 for these GPS fields. Explicit WGS84 labels are accepted. Other labels require overrides. Convert the resulting pair to EPSG:25832. |
| Heading | Use `GPSImgDirection` in degrees with `GPSImgDirectionRef = T` on an upright original (EXIF orientation absent or 1). Other cases, including magnetic directions and images requiring rotation or reflection, need an explicit true-north heading in the normalized image frame. |
| Pitch / roll | Supply explicit values in degrees. Device-specific pose tags are outside the supported set. |
| Camera elevation | Supply explicit optical-centre elevation in DHHN2016 NHN. `GPSAltitude` and `GPSAltitudeRef` alone are insufficient to establish that datum. |
| Intrinsics | Use `FocalLength` in mm where valid. Per-axis effective sensor extents can be derived from the matching `PixelXDimension`/`PixelYDimension`, `FocalPlaneXResolution`/`FocalPlaneYResolution`, and explicit `FocalPlaneResolutionUnit` (inch or centimetre). The declared dimensions must match the stored raster and the digital zoom tag must be absent, 0, or 1. The effective extents swap when the orientation swaps axes. Use overrides for unresolved values. |

The current tag set needs explicit pitch, roll and camera elevation. An EXIF-only request is valid JSON and returns field errors for measurements that remain unresolved. Malformed camera tags do not prevent rendering when valid overrides supply all affected measurements. Unsafe or unreadable images fail image validation. [CIPA EXIF tag reference](https://www.cipa.jp/std/documents/e/DC-008-2012_E_C.pdf)

## 2. Transport

`POST /api/v0/visualizations` returns the render synchronously.

Send `multipart/form-data` with exactly these two parts:

| Part | Required | Content type | Contents |
| --- | --- | --- | --- |
| `image` | Yes | `image/jpeg` or `image/png` | One non-animated original raster image, preserving available EXIF; binary bytes, not base64. The declared media type must match the bytes. For a JPEG with an auxiliary MPO frame, use the primary raster. The backend normalizes orientation. |
| `parameters` | Yes | `application/json` | UTF-8 JSON object described below. |

Reject duplicate/missing parts and additional image files. In a browser, let `FormData` generate the multipart boundary; do not set the outer `Content-Type` manually. Successful responses use `application/json`; errors use `application/problem+json`.

The endpoint limits the total request body to 22 MiB including multipart overhead,
the image to 20 MiB and 24 million decoded pixels, the JSON part to 1 MiB, the turbine
list to 100 and the encoded PNG to 40 MiB before base64. Each server process allows
two concurrent renders. A busy process returns `RENDER_CAPACITY_EXCEEDED`.

## 3. Shared types and general rules

| Type | Definition |
| --- | --- |
| `Id` | Nonempty string, at most 128 characters; unique within its request collection. |
| `Number` | Finite JSON number. Numeric strings, `NaN`, and infinity are invalid. |
| `Timestamp` | RFC 3339 date-time with explicit UTC offset, preferably `Z`. |
| `ProjectedCoordinates` | `{easting_m, northing_m}` in ETRS89 / UTM zone 32N (EPSG:25832). Both values are metres. Used for turbines, future map points, and the effective camera position. |
| `CameraGeographicCoordinates` | Camera input only. WGS84 (EPSG:4326) `{longitude_deg, latitude_deg}` in decimal degrees. Longitude −180…180, latitude −90…90. |
| `Elevation` | `{value_m, datum, source, uncertainty_m?}`. v0.1 uses absolute height above NHN in DHHN2016: `datum: "DHHN2016_NHN"`. `source` is `survey`, `user_input`, `fixture`, or `backend_model` for turbine inputs; camera overrides and resolved camera elevations also allow `exif`. Optional uncertainty is a nonnegative number in metres. |
| `Position` | `ProjectedCoordinates` plus required `elevation: Elevation`; used for turbines and the fully resolved camera. Camera elevation in the response may also have `source: "exif"`. |
| `CameraPositionOverride` | Optional horizontal camera fields from one coordinate system, plus optional `elevation`. The backend fills omissions from usable EXIF in the same coordinate system before returning an effective EPSG:25832 position. |
| `PixelPoint` | `{x_px, y_px}`, finite subpixel coordinates in the backend-normalized image. |
| `FieldProvenance` | `{source, observed_at?, note?}`. Source: `exif`, `device_sensor`, `user_input`, `wfs`, `fixture`, or `derived`. |

Unknown optional values are omitted, not sent as empty strings or `null`. Zero is a real number, never a missing-value marker. Turbine status is required and accepts only `operating` or `approved`. Missing, unknown, and unsupported statuses are validation errors; there is no fallback status. Unexpected fields are rejected in requests to catch spelling mistakes; clients ignore additional response fields. Breaking changes to an adopted contract require a new version. This coordinate change revises the in-development v0.1 draft. Update clients that send geographic turbine positions or read geographic coordinates from the effective camera position. `api_version` must equal `"0.1"`.

EPSG:25832 is the horizontal CRS for additional spatial input and for backend calculations. Only the camera position input also accepts WGS84 fields. The field names identify the CRS, so no separate CRS field is sent. The [camera conventions](camera-conventions.md#coordinates-and-heights) define the conversion to the camera-relative frame and its alignment with true north.

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
| `camera.position` | CameraPositionOverride | O | Partial optical-centre position. Choose EPSG:25832 or WGS84 for its horizontal fields. |
| `camera.position.easting_m`, `camera.position.northing_m` | Number | O | Easting and northing in metres (EPSG:25832). Each overrides the corresponding projected axis. |
| `camera.position.longitude_deg` | Number | O | WGS84 longitude, −180…180. Overrides only longitude. |
| `camera.position.latitude_deg` | Number | O | WGS84 latitude, −90…90. Overrides only latitude. |
| `camera.position.elevation` | CameraElevationOverride | O | Optional `value_m`, `datum`, `source`, `uncertainty_m`. An explicit `value_m` is in DHHN2016 NHN; omitted `datum` means that contract convention and omitted `source` means `user_input`. With no value override, EXIF height must independently establish its datum; supplied labels cannot relabel it. |
| `camera.orientation` | OrientationOverrides | O | Partial orientation object; `{}` means no orientation overrides. |
| `camera.orientation.heading_deg` | Number | O | Camera viewing azimuth, clockwise from true north: `0 <= h < 360`. North 0, east 90, south 180, west 270. |
| `camera.orientation.pitch_deg` | Number | O | Optical-axis elevation angle, positive upwards; `-90 < p < 90`. |
| `camera.orientation.roll_deg` | Number | O | Camera rotation around its viewing axis; `-180 <= r < 180`. Exact axis convention below. |
| `camera.orientation.north_reference` | String literal | O | `"true"`; this convention also applies to explicit headings when omitted. It does not override a magnetic EXIF reference. |
| `camera.intrinsics` | IntrinsicsOverrides | O | Partial values from one variant below; every member, including `kind`, is optional. |

**Horizontal camera resolution.** Reject a `camera.position` containing both projected and geographic fields with `422 VALIDATION_ERROR`. If the request supplies WGS84 fields, complete any missing axis from usable WGS84 EXIF, then project the resolved pair once to EPSG:25832. If it supplies projected fields, use those values directly. When one projected axis is missing, project a complete usable EXIF GPS pair first and take the missing axis from that result. With no horizontal override, project the complete usable EXIF pair. If an axis is still missing, return `CAMERA_PARAMETERS_UNRESOLVED`. Elevation is resolved independently.

Missing pitch, roll, heading, or elevation in the request is allowed. Missing measurements after EXIF resolution are errors. A user may explicitly assume zero for an angle, with `user_input` provenance and a note; the backend must not make that assumption invisibly. Uncertainty/source metadata for an overridden measurement must not be inherited from the displaced EXIF measurement. A supplied source/uncertainty describes the effective value but does not certify its correctness.

**Device-to-camera conversion:** Browser `alpha/beta/gamma` are device-axis rotations, not contract heading/pitch/roll. A capture adapter must account for the selected front/rear lens, display orientation, mirroring, and image normalization, then convert the resulting optical frame. There is no universally correct `heading = alpha` shortcut. Retain observation timestamps in provenance when available; unavailable true north requires manual orientation. Validate the adapter with known directions/tilts on real devices. This conversion does not move the backend's world-to-image projection into the frontend. See the [W3C orientation model](https://www.w3.org/TR/orientation-event/).

See [camera orientation](camera-conventions.md#camera-orientation) for the camera axes, rotation equations and the link between true north and the local world frame.

### Camera intrinsics: optional overrides within one variant

A physical focal length alone is insufficient to determine image scale. All fields below are optional overrides. A complete variant must be resolved before rendering. Select the variant with optional `kind`; without it, infer the variant from supplied member names (which are disjoint). With no intrinsic overrides, attempt the physical-focal-length variant from EXIF. Do not combine incompatible variants. Within the selected variant, fill omitted members only from usable EXIF and documented conversions; a missing member is not a schema error, but may remain unresolved at runtime. For example, `{"focal_length_mm": 6}` overrides focal length and still requires usable EXIF sensor extents or further overrides.

| `kind` | Fields | Request requirement | Interpretation |
| --- | --- | --- | --- |
| `horizontal_fov` | `horizontal_fov_deg`: Number | O | Effective horizontal field of view of the submitted image, strictly between 0° and 180°. Assumes square pixels and a centred principal point. |
| `physical_focal_length` | `focal_length_mm`, `sensor_width_mm`, `sensor_height_mm`: positive Numbers | O, each field | Actual focal length and effective sensor extent represented by the submitted raster, in its final orientation and crop. |
| `calibrated` | `fx_px`, `fy_px`: positive Numbers; `cx_px`, `cy_px`: Numbers | O, each field | Intrinsics already expressed for the submitted raster. Principal point must lie within the image in v0.1. |

Do not send fields from multiple variants. See [intrinsics and projection](camera-conventions.md#intrinsics-and-projection) for the focal-length conversion, principal point, and pinhole projection. Portrait rotation, crop, resizing, digital zoom, and stabilization can change effective intrinsics. Convert 35 mm equivalent focal length only with a justified convention and known crop or request a usable FOV. Never infer sensor size from a filename or device label.

The backend reports the v0.1 pinhole approximation. Strongly distorted images may be unsuitable. Supporting distortion coefficients requires a named model and an agreed contract revision.

### Turbine

| Field within `turbines[]` | Type | Required | Meaning / validation |
| --- | --- | --- | --- |
| `id` | Id | R | Request identifier for results, errors, and UI selection. Unique within the request. |
| `name` | String, 1–200 chars | O | Human-readable source name; output label falls back to `Turbine 1`, `Turbine 2`, etc. by input order. Names need not be unique. |
| `position` | Position | R | Required `easting_m` and `northing_m` in EPSG:25832, plus explicit base elevation. The WFS hub height is not base elevation. |
| `hub_height_m` | Number in `(0, 500)` | R | Hub centre above the turbine base in metres. |
| `rotor_diameter_m` | Number in `(0, 500)` | R | Rotor diameter in metres. |
| `turbine_type` | String, 1–200 chars | O | Manufacturer/model/type description if present. Not required by the schematic geometry. |
| `status` | Enum (string) | R | `operating` or `approved`, derived from the selected WFS layer. `approved` does not establish the current construction state. |
| `source` | TurbineSource | R | Provenance described below. |

`TurbineSource` fields: required `dataset: "nrw_renewable_energies_wfs"`, `feature_type` (one of the two supported full WFS layer names listed below), `feature_id` (string), `retrieved_at` (Timestamp), and `raw_status` (source status/layer label). Optional `unit_id` stores the source unit number and `data_as_of` preserves the source data-date text. `feature_type + feature_id` identifies the WFS record; reject repeated selection of that pair within one request.

The frontend submits a complete normalized snapshot of each selected record. The renderer validates it but does not re-query WFS by ID, fetch a client-supplied URL, or silently replace values. This makes a rendering reproducible. It does not certify client-supplied data as authentic. Normal product use takes dimensions from the selected WFS record; the contract's explicit values do not imply free turbine placement or a new dimension-editing UI.

An out-of-range or missing dimension rejects the request with a field-specific error. A missing name or turbine type is allowed. The schematic rotor faces true north with one blade pointing up. The response warns that rotor orientation and blade positions are schematic.

## 5. NRW WFS adapter: verified source mapping

Checked on 9 November 2026 using [GetCapabilities](https://www.wfs.nrw.de/umwelt/erneuerbare_energien_wfs?SERVICE=WFS&REQUEST=GetCapabilities), DescribeFeatureType for the operating/approved layers, and one sample feature from each. This establishes schema and sample behaviour, not completeness of every record.

| Source | Contract target / rule |
| --- | --- |
| `msGeometry` | `position.easting_m` and `position.northing_m` in EPSG:25832. Read the geometry CRS and axis order. Map an already compatible tuple directly and transform other source CRSs at the adapter boundary. Base elevation needs a separate source. |
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
| `map_position` | ProjectedCoordinates | Yes | The same physical feature identified in the overhead image, in EPSG:25832. |
| `map_source` | String | Optional | Orthophoto/source identifier for provenance, not a URL to fetch blindly. |
| `map_date` | String | Optional | Source date/version if known. |

Illustrative future entry:

```json
{
  "id": "anchor-1",
  "image_point": {"x_px": 410.5, "y_px": 380.25},
  "map_position": {"easting_m": 397971.486, "northing_m": 5774330.976},
  "map_source": "documented-orthophoto-layer",
  "map_date": "2026"
}
```

There is intentionally no frontend `elevation` field for reference points. The future backend obtains surface elevations from a DSM and records dataset, vertical datum, sampling method, resolution, and coverage/NoData checks. A roof point must use the roof surface, not DTM ground height; sampling at edges and vegetation needs uncertainty checks. A 2D coordinate plus a DSM sample does not guarantee that the clicked physical feature was identified correctly.

Nonempty points are rejected in v0.1. Before enabling them in a later version, define the solver, parameters to refine, minimum/degenerate configurations, quality criteria, DSM failure semantics, and a calibration-result schema with resolved heights, residuals, and accepted/rejected point IDs. Optional camera overrides and EXIF fallback are independent of this reserved field; unresolved camera values remain errors until an explicitly supported calibration workflow exists.

## 7. Request example and browser submission

[request-example.json](api/request-example.json) supplies complete camera overrides with WGS84 position input and two turbines in EPSG:25832. It requires a photo with normalized size 1200 × 800. [request-exif-example.json](api/request-exif-example.json) omits `camera` entirely. [request-partial-override-example.json](api/request-partial-override-example.json) supplies explicit easting, heading, focal length, pitch, roll and optical-centre elevation. It demonstrates fallback for northing and effective sensor extents. These examples use illustrative coordinates, dimensions, camera values and feature IDs.

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
| `camera_used` | Object | Effective `position` (`easting_m`, `northing_m` in EPSG:25832 and elevation in DHHN2016/NHN) and `orientation` plus normalized `intrinsics: {fx_px, fy_px, cx_px, cy_px}`. Contains the complete values after EXIF resolution and explicit overrides, not merely the submitted fields. |
| `camera_value_sources` | Object | JSON Pointer into `camera_used` → `{source, input_paths?, exif_tags?}`. `source` is `override`, `exif`, or `derived`. Record each effective numeric camera value. Projected axes calculated from geographic or EXIF inputs use `derived` and identify the input fields and/or EXIF tags. An explicit projected axis retains `override`. `input_paths` is an optional array of JSON Pointers into the submitted parameters; `exif_tags` is an optional array of used tag names. Derived intrinsics identify the supplied fields and/or tags used; image-centre defaults come from normalized raster dimensions and the stated pinhole model. Tag names only, never a full raw EXIF dump. Client provenance is supplementary, not a replacement for backend resolution provenance. |
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
| 413 | `REQUEST_TOO_LARGE`, `IMAGE_TOO_LARGE`, `PIXEL_LIMIT_EXCEEDED`, `PARAMETERS_TOO_LARGE`, `TURBINE_LIMIT_EXCEEDED`. |
| 415 | `UNSUPPORTED_IMAGE_TYPE` for an unsupported image signature, mismatched image media type, or animated PNG. A file with a matching JPEG/PNG signature that fails decoding returns `INVALID_IMAGE`. |
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

- Require both EPSG:25832 axes for each turbine and reject geographic fields there. Verify both camera input representations resolve to the same projected position and reject requests mixing coordinate systems inside the camera position.
- An omitted `camera` and empty camera or nested objects produce identical EXIF resolution and field errors for the same fixture.
- Partial longitude/latitude/orientation/intrinsics overrides replace only supplied values; explicit zero is preserved. Full overrides work without camera EXIF.
- Invalid/null overrides fail validation even if EXIF could supply valid alternatives. Unknown fields and mixed intrinsic variants remain invalid.
- Missing, malformed, unsupported, or ambiguous EXIF produces field-specific unresolved errors when needed, never guessed pitch/roll, sensor size, or height datum. All unresolved fields are reported together.
- Validate EXIF coordinates, north references, height references, and intrinsic conversions using small local fixtures with known expected values. No device database or network dependency is required.
- Rotated/reflected photos normalize exactly once; compare preview/output dimensions, projected locations, and effective intrinsics/pose in the same frame. Optional incorrect image assertions fail.
- Verify `camera_used` and `camera_value_sources` reflect precedence and conversions, and output images/logs do not expose raw EXIF. WFS status/layer and turbine-dimension checks remain unchanged.

The backend HTTP tests use in-memory photographs and assert real rendered pixels,
EXIF fallback and provenance, validation errors and byte limits.

### Technical references

- [Multipart form-data, RFC 7578](https://www.rfc-editor.org/rfc/rfc7578.html): binary image and separate JSON part.
- [OpenCV camera calibration and projection](https://docs.opencv.org/4.x/d9/d0c/group__calib3d.html): intrinsics and pixel-based projection.
- [W3C Device Orientation and Motion](https://www.w3.org/TR/orientation-event/): device-coordinate conventions; capture support must be checked per device.
- [NRW Renewable Energies WFS](https://www.wfs.nrw.de/umwelt/erneuerbare_energien_wfs?SERVICE=WFS&REQUEST=GetCapabilities): source feature types; adapter mapping was inspected live as described above.
- [Problem Details, RFC 9457](https://www.rfc-editor.org/rfc/rfc9457.html): structured HTTP errors.
