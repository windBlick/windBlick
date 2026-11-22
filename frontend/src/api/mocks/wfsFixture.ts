import type { Turbine, TurbineStatus } from '../../types/contract'
import { WFS_FEATURE_TYPES } from '../../types/contract'

/**
 * DEMO DATA ONLY — illustrative turbine records in the contract's normalized
 * WFS shape (docs/api-contract.md §4–5). Positions, dimensions, elevations and
 * feature IDs are made up; they are not real NRW WFS records. Base elevations
 * are marked `source: "fixture"` because the WFS itself has no base elevation.
 */
const RETRIEVED_AT = '2026-11-17T09:00:00Z'

type Row = [id: string, lat: number, lon: number, status: TurbineStatus, hub: number, rotor: number, baseElev: number, name?: string, type?: string]

const rows: Row[] = [
  ['fixture-op-101', 51.0521, 6.2412, 'operating', 135, 115, 88.0, 'WEA Ratheim 1', 'Enercon E-115'],
  ['fixture-op-102', 51.0489, 6.2486, 'operating', 135, 115, 87.5, 'WEA Ratheim 2', 'Enercon E-115'],
  ['fixture-ap-103', 51.0533, 6.2551, 'approved', 149, 138, 89.0, 'Windpark Hilfarth A', 'Nordex N133'],
  ['fixture-ap-104', 51.0498, 6.2302, 'approved', 160, 130, 86.0, 'Windpark Hilfarth B'],
  ['fixture-op-211', 51.0712, 6.1981, 'operating', 120, 101, 94.0, undefined, 'Vestas V100'],
  ['fixture-op-212', 51.0751, 6.2032, 'operating', 120, 101, 95.5],
  ['fixture-ap-305', 51.0644, 6.2689, 'approved', 164, 149, 91.0, 'Windpark Doveren'],
  ['fixture-op-377', 51.0446, 6.1874, 'operating', 99, 82, 84.0],
]

export const wfsFixture: Turbine[] = rows.map(([featureId, lat, lon, status, hub, rotor, elev, name, type]) => ({
  id: `turbine-${featureId}`,
  ...(name ? { name } : {}),
  position: {
    longitude_deg: lon,
    latitude_deg: lat,
    elevation: { value_m: elev, datum: 'DHHN2016_NHN', source: 'fixture' },
  },
  hub_height_m: hub,
  rotor_diameter_m: rotor,
  ...(type ? { turbine_type: type } : {}),
  status,
  source: {
    dataset: 'nrw_renewable_energies_wfs',
    feature_type: WFS_FEATURE_TYPES[status],
    feature_id: featureId,
    retrieved_at: RETRIEVED_AT,
    raw_status: status === 'operating' ? 'Windenergie - inbetrieb' : 'Windenergie - genehmigt',
  },
}))
