import type { PhotoInfo, Point2D, TurbineOutline } from '../types'

/**
 * Render the photo with turbine outlines into a JPG and trigger a download.
 * Done in the browser; swap for a backend endpoint if the contract provides one.
 */
export async function downloadPreviewImage(photo: PhotoInfo, outlines: TurbineOutline[]) {
  const img = new Image()
  img.src = photo.url
  await img.decode()

  const canvas = document.createElement('canvas')
  canvas.width = photo.width
  canvas.height = photo.height
  const ctx = canvas.getContext('2d')!
  ctx.drawImage(img, 0, 0, photo.width, photo.height)

  const lw = Math.max(2, photo.width / 600)
  const poly = (pts: Point2D[]) => {
    ctx.beginPath()
    pts.forEach(([x, y], i) => (i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)))
    ctx.closePath()
    ctx.fill()
    ctx.stroke()
  }

  const visible = outlines.filter((x) => x.inView).sort((a, b) => b.distanceMeters - a.distanceMeters)
  for (const o of visible) {
    ctx.fillStyle = 'rgba(255,255,255,0.82)'
    ctx.strokeStyle = '#17513a'
    ctx.lineWidth = lw
    ctx.lineJoin = 'round'
    poly(o.tower)
    o.blades.forEach(poly)
    ctx.beginPath()
    ctx.arc(o.hub.center[0], o.hub.center[1], o.hub.radius, 0, Math.PI * 2)
    ctx.fill()
    ctx.stroke()

    const fs = Math.round(photo.height * 0.026)
    ctx.font = `600 ${fs}px Inter, system-ui, sans-serif`
    const tw = ctx.measureText(o.label).width
    const [ax, ay] = o.labelAnchor
    const pad = fs * 0.5
    const y = ay + photo.height * 0.012
    ctx.fillStyle = '#17513a'
    ctx.fillRect(ax - tw / 2 - pad, y, tw + pad * 2, fs * 1.5)
    ctx.fillStyle = '#fff'
    ctx.textBaseline = 'middle'
    ctx.textAlign = 'center'
    ctx.fillText(o.label, ax, y + fs * 0.78)
  }

  // footer disclaimer
  const fs = Math.round(photo.height * 0.018)
  ctx.font = `500 ${fs}px Inter, system-ui, sans-serif`
  ctx.textAlign = 'left'
  ctx.textBaseline = 'bottom'
  ctx.fillStyle = 'rgba(0,0,0,0.45)'
  ctx.fillRect(0, photo.height - fs * 2, photo.width, fs * 2)
  ctx.fillStyle = '#fff'
  ctx.fillText('WindBlick · Geometric approximation only – not an official visualization', fs, photo.height - fs * 0.5)

  const blob = await new Promise<Blob | null>((r) => canvas.toBlob(r, 'image/jpeg', 0.92))
  if (!blob) throw new Error('Export failed')
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = `windblick-${photo.name.replace(/\.[^.]+$/, '')}.jpg`
  a.click()
  setTimeout(() => URL.revokeObjectURL(a.href), 1000)
}
