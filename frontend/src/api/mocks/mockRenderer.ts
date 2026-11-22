import type { CameraUsed, PixelPoint, Turbine, TurbineOutcome } from '../../types/contract'

/**
 * MOCK ONLY — stands in for the backend renderer so the UI can be developed
 * before POST /api/v0/visualizations exists. Per AGENTS.md, authoritative
 * geometry belongs in the Python backend; delete this with the mock.
 *
 * Follows the camera conventions of docs/api-contract.md §4:
 * local east/north/up frame, heading/pitch/roll in degrees, camera axes
 * x right / y down / z forward, x = fx·Xc/Zc + cx, y = fy·Yc/Zc + cy.
 * Simplifications: equirectangular local frame (fine for a few km), schematic
 * rotor facing the camera, no terrain, no occlusion, no lens distortion.
 */

type Vec3 = [number, number, number]

const EARTH_RADIUS_M = 6371008.8
const toRad = (deg: number) => (deg * Math.PI) / 180
const dot = (a: Vec3, b: Vec3) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
const add = (a: Vec3, b: Vec3): Vec3 => [a[0] + b[0], a[1] + b[1], a[2] + b[2]]
const scale = (a: Vec3, s: number): Vec3 => [a[0] * s, a[1] * s, a[2] * s]

export interface RenderedTurbine {
  id: string
  label: string
  outcome: TurbineOutcome
  projectedHub?: PixelPoint
  distanceMeters: number
}

export const MOCK_STYLE_COLOR = '#17513A'

/** Draw the photo with schematic turbine outlines; returns per-turbine outcomes in request order. */
export function renderTurbines(
  ctx: CanvasRenderingContext2D,
  width: number,
  height: number,
  camera: CameraUsed,
  turbines: Turbine[],
  labels: string[],
): RenderedTurbine[] {
  const h = toRad(camera.orientation.heading_deg)
  const p = toRad(camera.orientation.pitch_deg)
  const r = toRad(camera.orientation.roll_deg)
  const forward: Vec3 = [Math.sin(h) * Math.cos(p), Math.cos(h) * Math.cos(p), Math.sin(p)]
  const right0: Vec3 = [Math.cos(h), -Math.sin(h), 0]
  const down0: Vec3 = [Math.sin(h) * Math.sin(p), Math.cos(h) * Math.sin(p), -Math.cos(p)]
  const right = add(scale(right0, Math.cos(r)), scale(down0, Math.sin(r)))
  const down = add(scale(right0, -Math.sin(r)), scale(down0, Math.cos(r)))
  const { fx_px: fx, fy_px: fy, cx_px: cx, cy_px: cy } = camera.intrinsics
  const cam = camera.position

  /** World point (ENU metres relative to the camera's optical centre) → camera frame. */
  const toCamera = (d: Vec3): Vec3 => [dot(d, right), dot(d, down), dot(d, forward)]
  const project = ([xc, yc, zc]: Vec3): [number, number] => [(fx * xc) / zc + cx, (fy * yc) / zc + cy]

  const results: RenderedTurbine[] = turbines.map((t, i) => {
    const east = toRad(t.position.longitude_deg - cam.longitude_deg) * EARTH_RADIUS_M * Math.cos(toRad(cam.latitude_deg))
    const north = toRad(t.position.latitude_deg - cam.latitude_deg) * EARTH_RADIUS_M
    const baseUp = t.position.elevation.value_m - cam.elevation.value_m
    const distanceMeters = Math.hypot(east, north)
    // Horizontal unit vector perpendicular to the line of sight (schematic rotor plane).
    const side: Vec3 = distanceMeters > 0 ? [north / distanceMeters, -east / distanceMeters, 0] : [1, 0, 0]
    const at = (lateral: number, up: number): Vec3 => [east + side[0] * lateral, north + side[1] * lateral, baseUp + up]

    const hubCam = toCamera(at(0, t.hub_height_m))
    const label = labels[i]!
    if (hubCam[2] <= 1) return { id: t.id, label, outcome: 'behind_camera', distanceMeters }

    const projectedHub = project(hubCam)
    const R = t.rotor_diameter_m / 2
    const extentPx = (Math.max(t.hub_height_m, R) * fx) / hubCam[2]
    const inFrame =
      projectedHub[0] + extentPx >= 0 &&
      projectedHub[0] - extentPx <= width &&
      projectedHub[1] - extentPx <= height &&
      projectedHub[1] + extentPx * 2 >= 0
    return {
      id: t.id,
      label,
      outcome: inFrame ? 'drawn' : 'outside_frame',
      projectedHub: { x_px: projectedHub[0], y_px: projectedHub[1] },
      distanceMeters,
    }
  })

  // Farther turbines first (contract §8); ties keep request order.
  const order = results
    .map((res, i) => ({ res, t: turbines[i]!, i }))
    .filter(({ res }) => res.outcome === 'drawn')
    .sort((a, b) => b.res.distanceMeters - a.res.distanceMeters || a.i - b.i)

  ctx.lineJoin = 'round'
  ctx.lineWidth = Math.max(2, width / 600)
  for (const { res, t } of order) {
    const east = toRad(t.position.longitude_deg - cam.longitude_deg) * EARTH_RADIUS_M * Math.cos(toRad(cam.latitude_deg))
    const north = toRad(t.position.latitude_deg - cam.latitude_deg) * EARTH_RADIUS_M
    const baseUp = t.position.elevation.value_m - cam.elevation.value_m
    const d = res.distanceMeters || 1
    const side: Vec3 = [north / d, -east / d, 0]
    const at = (lateral: number, up: number): Vec3 => [east + side[0] * lateral, north + side[1] * lateral, baseUp + up]
    const pts = (list: Vec3[]) => {
      const cams = list.map(toCamera)
      return cams.every((c) => c[2] > 1) ? cams.map(project) : null
    }
    const polygon = (list: Vec3[]) => {
      const p2 = pts(list)
      if (!p2) return
      ctx.beginPath()
      p2.forEach(([x, y], k) => (k ? ctx.lineTo(x, y) : ctx.moveTo(x, y)))
      ctx.closePath()
      ctx.fill()
      ctx.stroke()
    }

    ctx.fillStyle = 'rgba(255,255,255,0.82)'
    ctx.strokeStyle = MOCK_STYLE_COLOR
    const R = t.rotor_diameter_m / 2
    const towerBase = Math.max(4, t.hub_height_m * 0.035)
    const towerTop = towerBase * 0.55
    polygon([at(-towerBase / 2, 0), at(towerBase / 2, 0), at(towerTop / 2, t.hub_height_m), at(-towerTop / 2, t.hub_height_m)])

    const rootW = Math.max(2.5, R * 0.06)
    for (const angleDeg of [0, 120, 240]) {
      const a = toRad(angleDeg)
      const [dx, dy, nx, ny] = [Math.sin(a), Math.cos(a), Math.cos(a), -Math.sin(a)]
      polygon([
        at(nx * (rootW / 2), t.hub_height_m + ny * (rootW / 2)),
        at(dx * R * 0.25 + nx * rootW * 0.75, t.hub_height_m + dy * R * 0.25 + ny * rootW * 0.75),
        at(dx * R, t.hub_height_m + dy * R),
        at(-nx * (rootW / 2), t.hub_height_m - ny * (rootW / 2)),
      ])
    }

    const hub = pts([at(0, t.hub_height_m), at(towerTop, t.hub_height_m)])
    if (hub) {
      ctx.beginPath()
      ctx.arc(hub[0]![0], hub[0]![1], Math.max(2, Math.hypot(hub[1]![0] - hub[0]![0], hub[1]![1] - hub[0]![1])), 0, Math.PI * 2)
      ctx.fill()
      ctx.stroke()
    }

    const base = pts([at(0, 0)])
    if (base) {
      const fs = Math.round(height * 0.026)
      ctx.font = `600 ${fs}px Inter, system-ui, sans-serif`
      const tw = ctx.measureText(res.label).width
      const [bx, by] = base[0]!
      const y = by + height * 0.012
      ctx.fillStyle = MOCK_STYLE_COLOR
      ctx.fillRect(bx - tw / 2 - fs * 0.5, y, tw + fs, fs * 1.5)
      ctx.fillStyle = '#fff'
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      ctx.fillText(res.label, bx, y + fs * 0.78)
    }
  }

  return results
}
