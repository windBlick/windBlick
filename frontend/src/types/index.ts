/**
 * UI-side models. Wire formats live in ./contract.ts.
 */
export type * from './contract'

export interface LatLon {
  lat: number
  lon: number
}

export interface BBox {
  west: number
  south: number
  east: number
  north: number
}

/** The photo the user selected. `file` is uploaded unchanged (EXIF preserved). */
export interface PhotoInfo {
  file: File
  url: string
  name: string
  /** Size as displayed by the browser (after its own EXIF orientation handling). */
  width: number
  height: number
}

/**
 * Camera values the user set explicitly. `null` means "not overridden":
 * the backend resolves that value from the photo's EXIF data instead.
 */
export interface CameraOverrideForm {
  latitude: number | null
  longitude: number | null
  /** Optical-centre elevation in metres above NHN (DHHN2016). */
  elevationM: number | null
  headingDeg: number | null
  pitchDeg: number | null
  rollDeg: number | null
  horizontalFovDeg: number | null
}

export type CameraField = keyof CameraOverrideForm

/**
 * What the browser could read from the photo, for display and map centring
 * only. The backend does its own authoritative EXIF resolution.
 */
export interface ExifHints {
  position: LatLon | null
  /** Image direction in degrees, with its north reference if present. */
  heading: { value: number; reference: 'true' | 'magnetic' | 'unknown' } | null
  /** GPS altitude in metres — datum unknown, so never sent as an override. */
  gpsAltitudeM: number | null
  focalLength35mm: number | null
}
