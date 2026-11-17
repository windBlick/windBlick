import type { LatLon } from '../types'

const R = 6371008.8 // mean Earth radius in metres
const toRad = (d: number) => (d * Math.PI) / 180
const toDeg = (r: number) => (r * 180) / Math.PI

/** Great-circle distance in metres. */
export function distance(a: LatLon, b: LatLon): number {
  const dLat = toRad(b.lat - a.lat)
  const dLon = toRad(b.lon - a.lon)
  const h =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(a.lat)) * Math.cos(toRad(b.lat)) * Math.sin(dLon / 2) ** 2
  return 2 * R * Math.asin(Math.sqrt(h))
}

/** Initial bearing from a to b in degrees (0–360, clockwise from north). */
export function bearing(a: LatLon, b: LatLon): number {
  const φ1 = toRad(a.lat)
  const φ2 = toRad(b.lat)
  const Δλ = toRad(b.lon - a.lon)
  const y = Math.sin(Δλ) * Math.cos(φ2)
  const x = Math.cos(φ1) * Math.sin(φ2) - Math.sin(φ1) * Math.cos(φ2) * Math.cos(Δλ)
  return (toDeg(Math.atan2(y, x)) + 360) % 360
}

/** Point reached from `start` after `meters` along `bearingDeg`. */
export function destination(start: LatLon, bearingDeg: number, meters: number): LatLon {
  const δ = meters / R
  const θ = toRad(bearingDeg)
  const φ1 = toRad(start.lat)
  const λ1 = toRad(start.lon)
  const φ2 = Math.asin(Math.sin(φ1) * Math.cos(δ) + Math.cos(φ1) * Math.sin(δ) * Math.cos(θ))
  const λ2 =
    λ1 + Math.atan2(Math.sin(θ) * Math.sin(δ) * Math.cos(φ1), Math.cos(δ) - Math.sin(φ1) * Math.sin(φ2))
  return { lat: toDeg(φ2), lon: ((toDeg(λ2) + 540) % 360) - 180 }
}

/** Signed difference a - b in degrees, normalised to (-180, 180]. */
export function angleDiff(a: number, b: number): number {
  let d = (a - b) % 360
  if (d > 180) d -= 360
  if (d <= -180) d += 360
  return d
}

/** Parse "51.0603, 6.2187" into a LatLon, or null if invalid. */
export function parseLatLon(text: string): LatLon | null {
  const parts = text.split(/[,;\s]+/).filter(Boolean).map(Number)
  if (parts.length !== 2 || parts.some((n) => !Number.isFinite(n))) return null
  const [lat, lon] = parts as [number, number]
  if (Math.abs(lat) > 90 || Math.abs(lon) > 180) return null
  return { lat, lon }
}

export function formatLatLon(p: LatLon, digits = 4): string {
  return `${p.lat.toFixed(digits)}, ${p.lon.toFixed(digits)}`
}
