/**
 * Transport types for the visualization API, mirroring docs/api-contract.md
 * (v0.1 draft) and docs/api/visualization-request.schema.json.
 *
 * Field names stay snake_case exactly as on the wire. Keep this file in sync
 * with the contract; UI-only models live in ./index.ts.
 *
 * Conventions (from the contract):
 * - Coordinates: WGS84, named keys longitude_deg / latitude_deg.
 * - Elevations: metres above NHN in DHHN2016 ("DHHN2016_NHN").
 * - Angles: degrees; heading clockwise from true north.
 * - Pixels: origin top-left of the backend-normalized image, x right, y down.
 */

export const API_VERSION = '0.1' as const
export const VISUALIZATIONS_PATH = '/api/v0/visualizations'

export type ElevationSource = 'survey' | 'user_input' | 'fixture' | 'backend_model'

export interface Elevation {
  value_m: number
  datum: 'DHHN2016_NHN'
  source: ElevationSource
  uncertainty_m?: number
}

export interface Coordinates {
  longitude_deg: number
  latitude_deg: number
}

export interface Position extends Coordinates {
  elevation: Elevation
}

/* ---------- Request ---------- */

export interface CameraElevationOverride {
  value_m?: number
  datum?: 'DHHN2016_NHN'
  source?: ElevationSource | 'exif'
  uncertainty_m?: number
}

export interface CameraPositionOverride {
  longitude_deg?: number
  latitude_deg?: number
  elevation?: CameraElevationOverride
}

export interface OrientationOverrides {
  heading_deg?: number
  pitch_deg?: number
  roll_deg?: number
  north_reference?: 'true'
}

export type IntrinsicsOverrides =
  | { kind?: 'horizontal_fov'; horizontal_fov_deg?: number }
  | { kind?: 'physical_focal_length'; focal_length_mm?: number; sensor_width_mm?: number; sensor_height_mm?: number }
  | { kind?: 'calibrated'; fx_px?: number; fy_px?: number; cx_px?: number; cy_px?: number }

export interface CameraOverrides {
  position?: CameraPositionOverride
  orientation?: OrientationOverrides
  intrinsics?: IntrinsicsOverrides
}

export type TurbineStatus = 'operating' | 'approved'

export const WFS_FEATURE_TYPES = {
  operating: 'erneuerbare_energien_wfs:Windenergieinbetrieb',
  approved: 'erneuerbare_energien_wfs:Windenergiegehnemigt',
} as const satisfies Record<TurbineStatus, string>

export interface TurbineSource {
  dataset: 'nrw_renewable_energies_wfs'
  feature_type: (typeof WFS_FEATURE_TYPES)[TurbineStatus]
  feature_id: string
  retrieved_at: string
  raw_status: string
  unit_id?: string
  data_as_of?: string
}

export interface Turbine {
  id: string
  name?: string
  position: Position
  hub_height_m: number
  rotor_diameter_m: number
  turbine_type?: string
  status: TurbineStatus
  source: TurbineSource
}

export type ProvenanceSource = 'exif' | 'device_sensor' | 'user_input' | 'wfs' | 'fixture' | 'derived'

export interface FieldProvenance {
  source: ProvenanceSource
  observed_at?: string
  note?: string
}

export interface VisualizationParameters {
  api_version: typeof API_VERSION
  image?: { width_px?: number; height_px?: number; orientation?: 'normalized'; captured_at?: string }
  camera?: CameraOverrides
  turbines: Turbine[]
  /** JSON Pointer (into the parameters) → provenance. */
  provenance?: Record<string, FieldProvenance>
  reference_points?: []
}

/* ---------- Success response ---------- */

export interface PixelPoint {
  x_px: number
  y_px: number
}

export interface CameraUsed {
  position: Position
  orientation: { heading_deg: number; pitch_deg: number; roll_deg: number }
  intrinsics: { fx_px: number; fy_px: number; cx_px: number; cy_px: number }
}

export interface CameraValueSource {
  source: 'override' | 'exif' | 'derived'
  input_paths?: string[]
  exif_tags?: string[]
}

export type TurbineOutcome = 'drawn' | 'outside_frame' | 'behind_camera'

export interface TurbineResult {
  id: string
  label: string
  status: TurbineStatus
  source: TurbineSource
  outcome: TurbineOutcome
  style: { color_hex: string; category: 'uniform' | TurbineStatus }
  projected_hub_px?: PixelPoint
}

export interface ApiWarning {
  code: string
  message: string
  path?: string
  turbine_id?: string
}

export interface VisualizationResponse {
  api_version: typeof API_VERSION
  request_id: string
  image: { mime_type: 'image/png'; encoding: 'base64'; data: string; width_px: number; height_px: number }
  camera_used: CameraUsed
  /** JSON Pointer into camera_used → where the effective value came from. */
  camera_value_sources: Record<string, CameraValueSource>
  turbines: TurbineResult[]
  warnings: ApiWarning[]
  calibration: { applied: false }
}

/* ---------- Error response (RFC 9457 Problem Details) ---------- */

export interface ValidationErrorEntry {
  /** JSON Pointer into the parameters; absent for multipart errors. */
  path?: string
  part?: 'image' | 'parameters'
  code: string
  message: string
}

export interface ProblemDetails {
  type: string
  title: string
  status: number
  detail: string
  request_id: string
  code: string
  errors: ValidationErrorEntry[]
}
