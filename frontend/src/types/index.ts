/**
 * Domain types for WindBlick.
 *
 * The API-facing types (ExistingTurbine*, PreviewRequest, PreviewResponse) are
 * PROVISIONAL: they are our best guess until the backend API contract arrives.
 * When it does, update them here and in src/api/ — the views should not change.
 */

export interface LatLon {
  lat: number
  lon: number
}

/** Camera pose read from the photo's EXIF data or entered by the user. */
export interface CameraPose extends LatLon {
  /** Viewing direction in degrees clockwise from north (0–360). */
  azimuth: number
  /** Camera tilt in degrees; positive = looking up. */
  pitch: number
  /** Horizontal field of view in degrees. */
  fov: number
}

/** A turbine the user placed on the map. */
export interface PlannedTurbine extends LatLon {
  id: string
  /** Display label, e.g. "WT 01". */
  label: string
  /** Hub height above ground in metres. */
  hubHeight: number
  /** Rotor diameter in metres. */
  rotorDiameter: number
}

export interface PhotoInfo {
  file: File | null
  /** Object URL or static URL usable as <img src>. */
  url: string
  name: string
  width: number
  height: number
}

/** What we could read from the photo's metadata. */
export interface PhotoMetadata {
  gps: LatLon | null
  /** Compass direction (EXIF GPSImgDirection), if present. */
  azimuth: number | null
  /** Horizontal FOV derived from the 35 mm-equivalent focal length, if present. */
  fov: number | null
}

/* ---------- Provisional API types ---------- */

export interface BBox {
  west: number
  south: number
  east: number
  north: number
}

/** Existing turbine from the NRW dataset (GeoJSON Feature, EPSG:4326). */
export interface ExistingTurbineProperties {
  id: string
  name?: string
  hubHeight?: number
  rotorDiameter?: number
  status?: 'operating' | 'approved' | 'planned'
}

export interface ExistingTurbineFeature {
  type: 'Feature'
  geometry: { type: 'Point'; coordinates: [number, number] }
  properties: ExistingTurbineProperties
}

export interface ExistingTurbineCollection {
  type: 'FeatureCollection'
  features: ExistingTurbineFeature[]
}

export interface PreviewRequest {
  image: { width: number; height: number }
  camera: CameraPose
  /** Eye height above ground in metres. */
  cameraHeight: number
  turbines: PlannedTurbine[]
}

export type Point2D = [number, number]

/** Turbine outline in image pixel coordinates (origin top-left). */
export interface TurbineOutline {
  turbineId: string
  label: string
  inView: boolean
  distanceMeters: number
  /** Polygon for the tower. */
  tower: Point2D[]
  /** One polygon per blade. */
  blades: Point2D[][]
  hub: { center: Point2D; radius: number }
  /** Where to anchor the label (below the tower base). */
  labelAnchor: Point2D
}

export interface PreviewResponse {
  outlines: TurbineOutline[]
  outOfViewCount: number
  totalCount: number
}
