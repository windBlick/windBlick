import type { ExistingTurbineCollection } from '../../types'

/** Fake existing turbines around Hückelhoven (NRW) for the "NRW Turbines" layer. */
const points: Array<[number, number, string, number, number]> = [
  [6.2412, 51.0521, 'NRW-0142', 135, 115],
  [6.2486, 51.0489, 'NRW-0143', 135, 115],
  [6.2551, 51.0533, 'NRW-0144', 149, 138],
  [6.1981, 51.0712, 'NRW-0211', 120, 101],
  [6.2032, 51.0751, 'NRW-0212', 120, 101],
  [6.2689, 51.0644, 'NRW-0305', 164, 149],
  [6.1874, 51.0446, 'NRW-0377', 99, 82],
  [6.2304, 51.0821, 'NRW-0402', 141, 131],
]

export const mockNrwTurbines: ExistingTurbineCollection = {
  type: 'FeatureCollection',
  features: points.map(([lon, lat, id, hubHeight, rotorDiameter]) => ({
    type: 'Feature',
    geometry: { type: 'Point', coordinates: [lon, lat] },
    properties: { id, hubHeight, rotorDiameter, status: 'operating' },
  })),
}
