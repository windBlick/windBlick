import type { BBox, Turbine } from '../types'
import { wfsFixture } from './mocks/wfsFixture'

/**
 * Turbine source adapter (docs/api-contract.md §5).
 *
 * Returns normalized, contract-shaped records for the NRW renewable-energies
 * WFS layers (operating + approved) inside a bounding box (WGS84).
 *
 * NOT IMPLEMENTED YET: the real WFS request (GetFeature, CRS/axis-order
 * conversion, string parsing of nabenhoehe_m / durchmesser_m) and a source of
 * turbine base elevation, which the WFS does not provide. Until then this
 * returns the demo fixture, and the UI labels the layer as demo data.
 */
export const TURBINE_SOURCE_IS_DEMO = true

export async function getTurbinesInBbox(bbox: BBox): Promise<Turbine[]> {
  await new Promise((r) => setTimeout(r, 200))
  return wfsFixture.filter(({ position: { longitude_deg: lon, latitude_deg: lat } }) => {
    return lon >= bbox.west && lon <= bbox.east && lat >= bbox.south && lat <= bbox.north
  })
}
