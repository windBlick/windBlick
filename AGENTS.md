# Project instructions: Wind Turbine Visualization

This file is the single source of truth for shared AI coding-agent instructions in this repository. Follow it when reading, designing, implementing, testing, or reviewing code. Prefer explicit team decisions and the existing codebase over assumptions. If a decision is still open, document the trade-off instead of inventing a convention.

## 1. Mission and scope

We are a five-person university team building a geospatial application for the *Geoinformatics in Society* master's module at the University of Münster.

**Goal:** Help citizens understand the **real-world dimensions and approximate visual presence** of existing or planned wind turbines from a familiar viewpoint (for example, a home or garden). Users provide an existing photograph or take a new one, select turbines and their real-world locations/dimensions, and obtain a geometrically informed visualization.

- Focus on intuitive scale, approximate placement/visibility, reproducibility, and transparent assumptions **rather than photorealism**.
- The application must be neutral: neither promote nor oppose wind power. Do not distort turbine sizes or imply accuracy the data cannot support.
- The primary users are non-experts, with particular interest in homeowners around ages 40-60. Initial evaluation may recruit at least five relevant participants from the team's personal networks.
- The application is **desktop-first**, but photo capture on a smartphone should be possible where practical. It must also work with an uploaded photo.
- The local context includes Münster and its surroundings; do not hard-code the geographic scope to one municipality. Prefer appropriately licensed open geodata (turbine locations/technical parameters, orthophotos, terrain/surface models) and document data quality.
- Out of scope for the initial MVP: shadow-flicker or noise studies, legal compliance assessments, fully automatic photorealistic compositing, and guaranteed object occlusion or line-of-sight visibility.

## 2. Architecture and boundaries

Use a clear separation of responsibilities:

**Frontend (web):** HTML, CSS, and modern JavaScript (ES modules) by default. Focus on accessible, understandable user journeys: upload/capture photo, select turbines on a map, associate reference points, inspect/edit results, and explain uncertainty. Browser-specific permission and sensor handling belongs here. Do not implement authoritative geometry/calibration algorithms in the frontend.

**Optional frontend framework:** [Open Pioneer Trails](https://open-pioneer.dev/trails-docs/Introduction/) is a possible choice, **not a requirement**. This is its official name. It is a client-side web application framework based on React, with a package-based architecture, Vite tooling, JavaScript/TypeScript support, and Web Component delivery. Adopting it would introduce corresponding frontend structure and tooling; decide this explicitly as a team rather than treating it as a drop-in script. It does not determine the Python backend framework or change the API boundary.

**Backend:** Python with an HTTP API. The API framework is **not decided yet**; keep the architecture framework-agnostic until the team chooses one. The backend owns request validation, coordinate transformations, camera geometry, reference-point calibration, turbine model geometry, image projection/composition, and any implemented visibility/occlusion calculations. Keep these operations in testable Python modules, independent of framework-specific request/response handling. Thin API adapters validate and translate transport data, invoke domain functions, and map results or domain errors to the agreed responses.

Use mature Python geospatial, image-processing, and computer-vision packages instead of reimplementing established functionality. Candidates include pyproj for CRS transformations, Rasterio for raster/elevation data, Shapely or GeoPandas where vector processing is needed, NumPy/SciPy for numerical work, OpenCV for camera geometry and calibration, and Pillow for image handling/composition. Select only packages needed for the agreed approach; check their assumptions, licenses, supported Python versions, and native dependencies. Library availability does not remove the need to validate coordinate conventions, height references, or calibration quality.

**API boundary:** Frontend and backend communicate only through a documented API, not by importing each other's implementation modules. The exact endpoints and schemas are **not decided yet**. Agree on and document the request/response contract before implementing dependent features. Anticipated inputs include a photograph, optional camera/sensor metadata, turbine locations/dimensions, and matched image/map reference points; outputs may include a visualization and calibration diagnostics. Do not invent endpoints, required fields, or response formats as established facts. Define serializable transport models separately from internal Python models; do not expose framework objects, NumPy arrays, or geospatial library objects directly as the contract. Specify image-coordinate mapping, CRS, axis order, units, height references, optional/missing values, and validation errors consistently for both sides.

**Deployment:** A continuously available backend is possible but not a commitment. Keep hosting-dependent logic and configuration separate from domain logic; never hard-code server URLs or credentials. Use an isolated Python environment and declare the supported Python version, dependencies, and tool configuration in `backend/pyproject.toml`. Agree on a reproducible dependency-locking approach and document any required native libraries or transformation grids. Choose production serving and process management only after the API framework and hosting target are agreed; frontend build tooling is separate from the backend runtime.

Keep architecture documentation in `docs/` aligned with the Python module boundaries, processing/data flow, selected library responsibilities, API contract, optional frontend framework decision, and deployment assumptions. Record unresolved choices as unresolved rather than presenting suggested packages, commands, or services as already adopted.

Suggested initial layout (adapt to existing files after team agreement):

```text
frontend/                           Browser UI, camera/sensor capture, map and point selection
backend/pyproject.toml               Python metadata, dependencies, tool configuration
backend/src/wind_turbine_visualization/
  __init__.py                       Python package entry
  api/                              HTTP adapters, validation, error handling; framework TBD
  geo/                              CRS, elevation, geospatial data handling
  camera/                           Camera intrinsics, orientation, projection
  calibration/                      Reference-point matching and pose estimation
  rendering/                        Turbine geometry and image composition
backend/tests/                      Python unit and integration tests
docs/                               Architecture, API contract, decisions, evaluation
```

Avoid adding frontend frameworks, GIS engines, image-processing libraries, databases, or cloud services without a concrete need and team agreement. Prefer an appropriate established Python package over a custom implementation when functionality is needed. The Python API framework, adoption of Open Pioneer Trails or another frontend framework, specific rendering libraries, persistent storage, and the deployment target remain open decisions. If Open Pioneer Trails is chosen, adapt the internal frontend layout to its conventions while retaining the backend boundary.

## 3. Geospatial and camera correctness (critical)

- Always document **coordinate reference system (CRS), axis order, units, and vertical datum** at each geospatial boundary. WGS84 latitude/longitude is suitable for exchange, **not** for direct planar meter calculations. Convert to an appropriate local metric system before measuring or projecting. Avoid silently mixing ETRS89/UTM, WGS84/UTM, or different elevation references.
- Use **meters** for world distances, turbine heights, and rotor diameters. State explicitly whether angles are in radians or degrees. Convert units at system boundaries; do not guess.
- Define and consistently apply the camera and image coordinate conventions, including device axes, screen rotation, optical axis, pixel origin, image orientation, and whether image coordinates refer to the original or transformed image. Image pixels typically use origin at the top left, `x` rightward, `y` downward.
- Separate **camera intrinsics** (focal length/field of view, principal point, lens distortion/cropping) from **camera extrinsics** (position and orientation). Phone sensor values are approximate starting estimates, not ground truth. Never assume browser APIs reliably expose the precise photo focal length, true-north heading, or complete camera pose.
- Account for image EXIF orientation, cropping/resizing, possible digital stabilization, and changing camera lenses. Preserve a mapping between displayed image coordinates and the image coordinates used by the backend.
- Keep turbine parameters physically meaningful: geographic position, terrain/base elevation, hub height, rotor diameter, and, if relevant, rotor/nacelle orientation. Overall turbine height is normally hub height plus rotor radius; do not confuse these measures.
- Keep calibration, geometric projection, occlusion estimation, and final rendering conceptually distinct. A plausible-looking composite is not proof of geometric correctness.
- If reliable height data, camera calibration, or occlusion information is missing, return or display a clearly qualified approximation rather than silently guessing.

### Image-to-map reference-point calibration

Our key technical focus is matching **the same physical 3D feature** between a photograph and an overhead map/orthophoto to refine the camera pose.

- Each correspondence consists of an **image pixel** and the **real-world 3D location of exactly that visible feature**. A 2D map click alone does not establish a reliable elevation.
- Explain this clearly in the UI. Good potential examples: an identifiable roof corner/ridge point visible in both views, or a distinct driveway/pavement corner on the ground. The point must correspond to the **same physical height** in both representations.
- Invalid example: selecting front-door steps or ground level on the map but the roof corner in the photo. Likewise, selecting a tree trunk/base in one view and the canopy top in the other is not a valid match.
- A digital terrain model (DTM/DGM) gives ground height; a digital surface model (DSM/DOM) may approximate the height of roofs/vegetation. Neither guarantees the exact height of an arbitrarily clicked feature, especially at roof edges, narrow objects, or tree crowns. Treat uncertainty and data resolution explicitly.
- Provide UI guidance and validation for ambiguous matches. Prefer recognizable, stable landmarks; trees may move and vary seasonally. Offer zoom, correction, removal, and retry of point pairs.
- The number and spatial distribution of points needed depend on which camera parameters are known or fixed. Do not claim that any fixed number of points always determines a unique, accurate pose. Detect insufficient/degenerate configurations and expose calibration errors or confidence indicators.
- Keep the original sensor-based estimate available for comparison with the calibrated result when useful.

## 4. Browser camera, GPS, and orientation data

Browser support varies by device, operating system, browser, permissions, and HTTPS availability. Implement capability detection and graceful fallback rather than making sensor access mandatory.

- Use `navigator.mediaDevices.getUserMedia()` for a live camera stream where supported; request the rear-facing camera when suitable. A file input with optional `capture` is a simpler alternative but its behavior varies, and switching to a native camera may prevent synchronized sensor sampling.
- Use `navigator.geolocation` for optional position and reported accuracy. Geolocation altitude may be missing or inaccurate; it must not be silently treated as surveyed ground or camera height.
- Read orientation via `deviceorientation` / `deviceorientationabsolute` when supported, checking whether orientation is absolute. On platforms that expose `DeviceOrientationEvent.requestPermission()`, request access in response to an explicit user action.
- `alpha`, `beta`, and `gamma` describe device-axis rotations, **not automatically the camera's compass bearing, pitch, and roll**. Account for screen orientation and camera-facing direction. Absolute/true-north heading is not uniformly available; browser-specific compass fields are non-standard.
- Request permissions only when needed, explain why, and handle denial, `null` readings, unavailable hardware, and desktop browsers. Camera and sensor APIs generally require a secure context (HTTPS or a supported localhost context); a phone visiting an HTTP page on a LAN IP is not equivalent to localhost.
- For in-app capture, collect timestamps and the latest available sensor samples around the actual frame acquisition. Do not claim perfect synchronization. For uploaded photos, treat relevant EXIF fields as optional, not guaranteed.
- Start with a short real-device proof of concept (at least Android Chrome and iOS Safari if available) before relying on any particular compass or camera capability.

## 5. Coding standards

- Write code, identifiers, comments, Python docstrings, JSDoc, logs, and technical documentation **in English**. User-facing text should be clear to the chosen audience; keep it separate from code and ready for localization.
- Use **Python for the backend** and modern **JavaScript with ES modules** for the frontend by default. Add Python type annotations to public functions and shared data models. Do not introduce TypeScript or adopt Open Pioneer Trails or another frontend framework without a team decision.
- Prefer small, cohesive, testable functions and modules. Keep geometry functions pure and deterministic where possible. Avoid unnecessary abstractions, hidden global state, duplicated calculations, and magic constants.
- Use descriptive names: Python `camera_position`, `reference_point_elevation_meters`, `rotor_diameter_meters`; JavaScript `cameraPosition`, `referencePointElevationMeters`, `rotorDiameterMeters`. Avoid `p`, `h`, or `d` where meaning is ambiguous.
- In Python, use `snake_case` for variables/functions and module names, `PascalCase` for classes, and `UPPER_SNAKE_CASE` for genuine constants. In JavaScript, use `camelCase` for variables/functions, `PascalCase` for classes, and `UPPER_SNAKE_CASE` for genuine constants. Prefer consistent `kebab-case` frontend file names if the repository has no existing convention; follow framework conventions if one is adopted.
- Add **Python docstrings** to public backend functions/interfaces and nontrivial geometric or numerical algorithms; retain **JSDoc** for exported JavaScript functions and public interfaces. Specify parameters, return types, units, coordinate frames, important assumptions, and possible errors. Use type annotations for Python types and docstrings for their semantics. Use concise English comments to explain *why*, especially for non-obvious math; do not restate every line.
- In JavaScript, use `const` by default, `let` when reassignment is required, `async`/`await` for async code, and explicit error handling. Avoid silent catch blocks and unhandled promise rejections. In Python, handle expected exceptions explicitly, use context managers for resources, and avoid swallowed exceptions or mutable global request state. Keep module imports free of server startup and processing side effects. Choose concurrency based on the selected framework and measured workload; declaring a function async does not make CPU-heavy processing non-blocking.
- Choose consistent formatter/linter configurations for each language (for example, Ruff for Python and Prettier/ESLint for JavaScript) and run them consistently; do not introduce incompatible duplicate style rules. Keep Python tool configuration in `backend/pyproject.toml` and document the agreed checks.
- Keep secrets and environment-dependent values out of source control; use documented environment variables and a safe example configuration.
- If existing code differs from these preferences, maintain consistency and propose a deliberate migration instead of mixing styles.

JavaScript JSDoc example (illustrative, not an API contract or a reason to move authoritative geometry into the frontend):

```js
/**
 * Returns the elevation angle from an observer to a target.
 * @param {number} horizontalDistanceMeters - Positive horizontal distance.
 * @param {number} heightDifferenceMeters - Target elevation minus observer elevation.
 * @returns {number} Elevation angle in radians.
 */
function calculateElevationAngle(horizontalDistanceMeters, heightDifferenceMeters) {
  return Math.atan2(heightDifferenceMeters, horizontalDistanceMeters);
}
```

## 6. Quality, testing, and security

- **Backend tests are expected**, especially for coordinate transforms, camera projection, turbine dimensions, calibration, and handling of incomplete or invalid metadata. Prefer **pytest** initially unless the repository adopts another Python test runner. Test domain modules without a running HTTP server; add framework-specific API integration tests once the framework is chosen. Define the concrete test setup and coverage priorities as a team.
- Test geometry with hand-checkable synthetic cases and explicit numeric tolerances. Include cases for degree/radian mix-ups, axis/order errors, different image orientations, terrain/elevation differences, insufficient reference points, and invalid/degenerate calibration setups.
- Add API-level tests for validation, error responses, and upload handling after agreeing on the contract. No network access or live external geodata should be necessary for deterministic unit tests. Exercise the selected Python libraries with small local fixtures and known expected results; do not replace the entire calculation pipeline with mocks. Keep any live-data integration tests separate.
- Add regression fixtures from synthetic or consented images when available. Avoid committing private photographs, identifying EXIF metadata, or precise home locations without authorization.
- Treat uploaded images and metadata as untrusted. Validate size, type, decoded image dimensions, input ranges, and point arrays; guard against resource exhaustion and unsafe file access. Configure decoding and processing limits, use controlled temporary paths, and clean up resources on success and failure. Do not turn user input into shell commands or arbitrary server-side file/URL access. Return actionable errors without leaking server internals.
- Treat location and photographs as sensitive user data. Minimize storage and logging, explain uploads, and do not retain original photos or precise locations by default without an explicit product decision and user consent.
- Record open-data provenance, CRS, resolution, dates, and licenses. Respect map/imagery attribution and usage conditions.
- Run the agreed Python tests and checks in CI using the documented Python version and reproducible dependencies, including required native geospatial components. Keep frontend checks separate and appropriate to the chosen frontend stack. Review dependency security updates; keep debug servers and tracebacks out of public production responses, configure HTTPS and allowed origins for deployment, and enforce processing limits. Authentication, storage, and background workers remain explicit product/architecture decisions.
- Do not mark estimated turbine visibility as confirmed when vegetation/buildings have not been modeled reliably. Make limitations visible to the user.

## 7. Usability and evaluation

- Prioritize a guided, comprehensible workflow over feature count. Avoid specialized GIS jargon in the UI without explanation.
- Show exactly what users need to click in **both views** (photo and overhead map). Make the physical-height requirement clear using examples and immediate feedback.
- Provide loading/progress/error states, undo or edit paths, manual correction when sensor data is missing, and obvious before/after comparison.
- Do not portray the result as a legally authoritative visual-impact study or a fully photorealistic prediction.
- Keep the tool suitable for evaluation with at least five non-expert participants; track task completion, usability feedback, and (where reference imagery exists) geometric errors separately.

## 8. Agent workflow and collaboration

1. Before changing code, inspect the relevant repository files, current issue, and agreed documentation. Do not assume that the suggested folders or scripts already exist.
2. For nontrivial work, briefly outline the approach, dependencies, assumptions, and any API or geospatial implications. Ask for a decision when a change affects a shared contract or open architecture choice.
3. Keep changes scoped to the assigned GitHub Issue; use a feature branch and a pull request instead of pushing directly to `main`. Do not overwrite unrelated work.
4. For contract changes, coordinate frontend/backend expectations and update the agreed API documentation and tests together. Do not silently break consumers.
5. Write or update appropriate tests and documentation. Discover actual backend setup and check commands from `backend/pyproject.toml`, the README, and CI configuration; discover frontend commands from its chosen tooling and documentation. Once pytest is configured, `python -m pytest` from `backend/` is a possible test command, not proof that the test setup already exists. Do not assume an API server start command before the framework is chosen. Do not report tests, linting, or builds as passed unless they were run.
6. In your final implementation summary, state what changed, what was tested, any remaining limitations, and any relevant assumptions or decisions still pending.
7. Update this file only when a team-level convention or architecture decision has actually been agreed. Keep it concise and free of temporary task-specific instructions.

**Priority:** Correct dimensions and coordinate handling > transparent limitations > understandable user experience > optional rendering polish.
