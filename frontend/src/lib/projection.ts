import type { PreviewRequest, PreviewResponse, Point2D, TurbineOutline } from '../types'
import { angleDiff, bearing, distance } from './geo'

/**
 * Geometric projection of turbines into the photo.
 *
 * Simple pinhole camera over flat terrain:
 *  - the camera sits `cameraHeight` m above the ground at (lat, lon)
 *  - it looks along `azimuth`, tilted by `pitch`, with horizontal FOV `fov`
 *  - each turbine stands on the same ground level; its rotor faces the camera
 *
 * This is a stand-in for the backend's preview endpoint (or the final
 * client-side implementation, depending on the API contract).
 */

const toRad = (d: number) => (d * Math.PI) / 180

interface Vec3 {
  east: number
  north: number
  up: number
}

export function computePreview(req: PreviewRequest): PreviewResponse {
  const { camera, image, cameraHeight, turbines } = req
  const W = image.width
  const H = image.height
  const f = W / 2 / Math.tan(toRad(camera.fov) / 2) // focal length in px
  const az = toRad(camera.azimuth)
  const pitch = toRad(camera.pitch)

  /** Project a point (metres, relative to the camera's ground position) to pixels. */
  const project = (p: Vec3): Point2D | null => {
    // rotate world → camera yaw frame
    const forward = p.north * Math.cos(az) + p.east * Math.sin(az)
    const right = p.east * Math.cos(az) - p.north * Math.sin(az)
    const up = p.up - cameraHeight
    // apply pitch
    const fwd = forward * Math.cos(pitch) + up * Math.sin(pitch)
    const upP = up * Math.cos(pitch) - forward * Math.sin(pitch)
    if (fwd <= 1) return null // behind or at the camera
    return [W / 2 + (f * right) / fwd, H / 2 - (f * upP) / fwd]
  }

  const outlines: TurbineOutline[] = []
  let outOfView = 0

  for (const t of turbines) {
    const d = distance(camera, t)
    const b = bearing(camera, t)
    const rel = angleDiff(b, camera.azimuth)
    const base: Vec3 = {
      east: d * Math.sin(toRad(b)),
      north: d * Math.cos(toRad(b)),
      up: 0,
    }
    const R = t.rotorDiameter / 2
    const inHorizontalFov = Math.abs(rel) <= camera.fov / 2 + toDegApprox(R, d)

    // unit vector pointing "sideways" (perpendicular to the line of sight)
    const side = { east: Math.cos(toRad(b)), north: -Math.sin(toRad(b)) }
    const at = (lateral: number, up: number): Vec3 => ({
      east: base.east + side.east * lateral,
      north: base.north + side.north * lateral,
      up,
    })

    const towerBaseW = Math.max(4, t.hubHeight * 0.035)
    const towerTopW = towerBaseW * 0.55
    const towerPts = [
      at(-towerBaseW / 2, 0),
      at(towerBaseW / 2, 0),
      at(towerTopW / 2, t.hubHeight),
      at(-towerTopW / 2, t.hubHeight),
    ].map(project)

    const hubP = project(at(0, t.hubHeight))
    const hubEdge = project(at(towerTopW * 0.9, t.hubHeight))

    const blades: Point2D[][] = []
    const rootW = Math.max(2.5, R * 0.06)
    for (const angleDeg of [0, 120, 240]) {
      const a = toRad(angleDeg)
      // direction in the rotor plane: x = sideways, y = up (0° = straight up)
      const dx = Math.sin(a)
      const dy = Math.cos(a)
      const nx = Math.cos(a) // normal for blade width
      const ny = -Math.sin(a)
      const pts = [
        at(nx * (rootW / 2), t.hubHeight + ny * (rootW / 2)),
        at(dx * R * 0.25 + nx * rootW * 0.75, t.hubHeight + dy * R * 0.25 + ny * rootW * 0.75),
        at(dx * R, t.hubHeight + dy * R),
        at(-nx * (rootW / 2), t.hubHeight - ny * (rootW / 2)),
      ].map(project)
      if (pts.every(Boolean)) blades.push(pts as Point2D[])
    }

    const valid = towerPts.every(Boolean) && hubP && hubEdge
    const inView = Boolean(valid && inHorizontalFov)
    if (!inView) outOfView++

    const tower = valid ? (towerPts as Point2D[]) : []
    const baseCenter: Point2D = valid
      ? [(tower[0]![0] + tower[1]![0]) / 2, (tower[0]![1] + tower[1]![1]) / 2]
      : [0, 0]

    outlines.push({
      turbineId: t.id,
      label: t.label,
      inView,
      distanceMeters: d,
      tower,
      blades: valid ? blades : [],
      hub: {
        center: hubP ?? [0, 0],
        radius: hubP && hubEdge ? Math.max(2, Math.hypot(hubEdge[0] - hubP[0], hubEdge[1] - hubP[1])) : 0,
      },
      labelAnchor: baseCenter,
    })
  }

  return { outlines, outOfViewCount: outOfView, totalCount: turbines.length }
}

/** Approximate angular half-width (deg) of an object of radius r at distance d. */
function toDegApprox(r: number, d: number): number {
  return (Math.atan2(r, Math.max(d, 1)) * 180) / Math.PI
}
