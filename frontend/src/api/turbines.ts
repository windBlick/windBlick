import type { BBox, ExistingTurbineCollection } from '../types'
import { USE_MOCKS, mockDelay, request } from './client'
import { mockNrwTurbines } from './mocks/nrwTurbines'

/**
 * Existing NRW wind turbines inside a bounding box (GeoJSON, EPSG:4326).
 * PROVISIONAL endpoint — replace with the one from the API contract.
 */
export async function getExistingTurbines(bbox: BBox): Promise<ExistingTurbineCollection> {
  if (USE_MOCKS) {
    await mockDelay(250)
    return {
      ...mockNrwTurbines,
      features: mockNrwTurbines.features.filter(({ geometry: { coordinates: [lon, lat] } }) => {
        return lon >= bbox.west && lon <= bbox.east && lat >= bbox.south && lat <= bbox.north
      }),
    }
  }
  const q = `${bbox.west},${bbox.south},${bbox.east},${bbox.north}`
  return request<ExistingTurbineCollection>(`/turbines?bbox=${encodeURIComponent(q)}`)
}
