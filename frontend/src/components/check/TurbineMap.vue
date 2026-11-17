<script setup lang="ts">
import L from 'leaflet'
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import type { CameraPose, LatLon, PlannedTurbine } from '../../types'
import { destination, distance } from '../../lib/geo'
import { getExistingTurbines } from '../../api/turbines'

const props = defineProps<{ camera: CameraPose; turbines: PlannedTurbine[] }>()
const emit = defineEmits<{
  addTurbine: [pos: LatLon]
  moveTurbine: [id: string, pos: LatLon]
  moveCamera: [pos: LatLon]
}>()

const el = ref<HTMLDivElement | null>(null)
const showNrw = ref(true)
const nrwLoading = ref(false)

let map: L.Map | null = null
let coneLayer: L.LayerGroup | null = null
let cameraMarker: L.Marker | null = null
const turbineMarkers = new Map<string, L.Marker>()
let nrwLayer: L.LayerGroup | null = null

const turbineSvg = `<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round"><path d="M12 12V3M12 12l7.8 4.5M12 12l-7.8 4.5M12 12v9"/></svg>`
const cameraSvg = `<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="#fff" stroke-width="1.8" stroke-linejoin="round"><path d="M4 8.5A1.5 1.5 0 0 1 5.5 7H8l1.5-2h5L16 7h2.5A1.5 1.5 0 0 1 20 8.5v9a1.5 1.5 0 0 1-1.5 1.5h-13A1.5 1.5 0 0 1 4 17.5Z"/><circle cx="12" cy="13" r="3.2"/></svg>`

const turbineIcon = (label: string) =>
  L.divIcon({
    className: 'wb-marker',
    html: `<div class="wb-turbine"><span class="wb-turbine__dot">${turbineSvg}</span><span class="wb-label">${label}</span></div>`,
    iconSize: [48, 72],
    iconAnchor: [24, 24],
  })

const cameraIcon = L.divIcon({
  className: 'wb-marker',
  html: `<div class="wb-camera">${cameraSvg}</div>`,
  iconSize: [40, 50],
  iconAnchor: [20, 50],
})

const nrwIcon = L.divIcon({
  className: 'wb-marker',
  html: `<div class="wb-nrw" title="Existing turbine">${turbineSvg}</div>`,
  iconSize: [22, 22],
  iconAnchor: [11, 11],
})

function coneRadius(): number {
  const far = Math.max(0, ...props.turbines.map((t) => distance(props.camera, t)))
  return Math.max(1200, far * 1.2)
}

function drawCone() {
  if (!map) return
  coneLayer?.remove()
  const { camera } = props
  const r = coneRadius()
  const pts: L.LatLngExpression[] = [[camera.lat, camera.lon]]
  const steps = 24
  for (let i = 0; i <= steps; i++) {
    const b = camera.azimuth - camera.fov / 2 + (camera.fov * i) / steps
    const p = destination(camera, b, r)
    pts.push([p.lat, p.lon])
  }
  const centre = destination(camera, camera.azimuth, r)
  coneLayer = L.layerGroup([
    L.polygon(pts, {
      color: '#2f7d57',
      weight: 1,
      dashArray: '4 4',
      fillColor: '#7cc39a',
      fillOpacity: 0.28,
      interactive: false,
    }),
    L.polyline(
      [
        [camera.lat, camera.lon],
        [centre.lat, centre.lon],
      ],
      { color: '#17513a', weight: 1.5, dashArray: '5 6', interactive: false },
    ),
  ]).addTo(map)
}

function drawCamera() {
  if (!map) return
  const ll: L.LatLngExpression = [props.camera.lat, props.camera.lon]
  if (!cameraMarker) {
    cameraMarker = L.marker(ll, { icon: cameraIcon, draggable: true, zIndexOffset: 1000, title: 'Camera position' })
      .on('dragend', (e) => {
        const p = (e.target as L.Marker).getLatLng()
        emit('moveCamera', { lat: p.lat, lon: p.lng })
      })
      .addTo(map)
  } else {
    cameraMarker.setLatLng(ll)
  }
}

function drawTurbines() {
  if (!map) return
  const ids = new Set(props.turbines.map((t) => t.id))
  for (const [id, m] of turbineMarkers) {
    if (!ids.has(id)) {
      m.remove()
      turbineMarkers.delete(id)
    }
  }
  for (const t of props.turbines) {
    const existing = turbineMarkers.get(t.id)
    if (existing) {
      existing.setLatLng([t.lat, t.lon])
      continue
    }
    const m = L.marker([t.lat, t.lon], { icon: turbineIcon(t.label), draggable: true, title: t.label })
      .on('dragend', (e) => {
        const p = (e.target as L.Marker).getLatLng()
        emit('moveTurbine', t.id, { lat: p.lat, lon: p.lng })
      })
      .addTo(map)
    turbineMarkers.set(t.id, m)
  }
}

async function loadNrw() {
  if (!map) return
  if (!showNrw.value) {
    nrwLayer?.clearLayers()
    return
  }
  const b = map.getBounds()
  nrwLoading.value = true
  try {
    const data = await getExistingTurbines({
      west: b.getWest(),
      south: b.getSouth(),
      east: b.getEast(),
      north: b.getNorth(),
    })
    if (!showNrw.value) return
    nrwLayer?.clearLayers()
    for (const f of data.features) {
      const [lon, lat] = f.geometry.coordinates
      const p = f.properties
      L.marker([lat, lon], { icon: nrwIcon, keyboard: false })
        .bindTooltip(
          `${p.name ?? p.id}${p.hubHeight ? ` · ${p.hubHeight} m hub` : ''}${p.rotorDiameter ? ` · ⌀ ${p.rotorDiameter} m` : ''}`,
          { direction: 'top', offset: [0, -10] },
        )
        .addTo(nrwLayer!)
    }
  } catch {
    /* layer is optional; fail quietly */
  } finally {
    nrwLoading.value = false
  }
}

function fitAll() {
  if (!map) return
  const pts: L.LatLngExpression[] = [[props.camera.lat, props.camera.lon], ...props.turbines.map((t) => [t.lat, t.lon] as [number, number])]
  if (pts.length === 1) map.setView(pts[0]!, 15)
  else map.fitBounds(L.latLngBounds(pts), { padding: [80, 80], maxZoom: 16 })
}

onMounted(() => {
  map = L.map(el.value!, { zoomControl: true, attributionControl: true }).setView([props.camera.lat, props.camera.lon], 15)
  // Swap for the project's own basemap (e.g. a WMS from the backend) once known
  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    className: 'wb-basemap',
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  }).addTo(map)
  L.control.scale({ imperial: false, position: 'bottomright' }).addTo(map)
  nrwLayer = L.layerGroup().addTo(map)

  map.on('click', (e: L.LeafletMouseEvent) => emit('addTurbine', { lat: e.latlng.lat, lon: e.latlng.lng }))
  map.on('moveend', loadNrw)

  drawCamera()
  drawTurbines()
  drawCone()
  fitAll()
  loadNrw()
})

onBeforeUnmount(() => {
  map?.remove()
  map = null
})

watch(
  () => [props.camera.lat, props.camera.lon, props.camera.azimuth, props.camera.fov],
  () => {
    drawCamera()
    drawCone()
  },
)
watch(
  () => props.turbines.map((t) => `${t.id}:${t.lat}:${t.lon}`).join('|'),
  () => {
    drawTurbines()
    drawCone()
  },
)
watch(showNrw, loadNrw)

defineExpose({ fitAll })
</script>

<template>
  <div class="map-wrap">
    <div ref="el" class="map" role="application" aria-label="Map: click to place a turbine" />
    <label class="toggle">
      <input v-model="showNrw" type="checkbox" role="switch" />
      <span class="toggle__track" aria-hidden="true"><span class="toggle__thumb" /></span>
      NRW Turbines
    </label>
    <div class="hint"><span class="hint__dot" />Click map to place turbine</div>
  </div>
</template>

<style scoped>
.map-wrap {
  position: relative;
  height: 100%;
  min-height: 440px;
  border-radius: var(--radius-lg);
  overflow: hidden;
}
.map {
  position: absolute;
  inset: 0;
  background: #eef0ea;
  cursor: crosshair;
}
.toggle {
  position: absolute;
  top: 16px;
  right: 16px;
  z-index: 500;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 8px 16px 8px 12px;
  border-radius: 999px;
  background: #fff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
}
.toggle input {
  position: absolute;
  opacity: 0;
}
.toggle__track {
  position: relative;
  width: 30px;
  height: 16px;
  border-radius: 999px;
  background: var(--border-strong);
  transition: background-color 0.15s;
}
.toggle__thumb {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #fff;
  transition: transform 0.15s;
}
.toggle input:checked + .toggle__track {
  background: var(--green-900);
}
.toggle input:checked + .toggle__track .toggle__thumb {
  transform: translateX(14px);
}
.toggle input:focus-visible + .toggle__track {
  outline: 3px solid var(--green-300);
  outline-offset: 2px;
}
.hint {
  position: absolute;
  left: 16px;
  bottom: 16px;
  z-index: 500;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 8px 16px;
  border-radius: var(--radius-sm);
  background: #fff;
  font-size: 12px;
  color: var(--ink-700);
  pointer-events: none;
}
.hint__dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--green-900);
}
</style>

<style>
/* Leaflet marker HTML is created outside Vue's scope */
.wb-marker {
  background: none;
  border: 0;
}
.wb-turbine {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}
.wb-turbine__dot {
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: var(--green-900);
  border: 3px solid #fff;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
  transition: transform 0.15s;
}
.wb-turbine:hover .wb-turbine__dot {
  transform: scale(1.06);
}
.wb-label {
  padding: 3px 10px;
  border-radius: 4px;
  background: #fff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12);
  font: 600 12px var(--font);
  color: var(--green-900);
  white-space: nowrap;
}
.wb-camera {
  display: grid;
  place-items: center;
  width: 40px;
  height: 40px;
  border-radius: 50% 50% 50% 0;
  transform: rotate(-45deg);
  background: var(--green-900);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.25);
}
.wb-camera svg {
  transform: rotate(45deg);
}
.wb-nrw {
  display: grid;
  place-items: center;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #8a9690;
  border: 2px solid #fff;
}
.wb-nrw svg {
  width: 13px;
  height: 13px;
}
.leaflet-container {
  font-family: var(--font);
}
/* muted basemap so markers and the view cone stand out, like the design */
.wb-basemap {
  filter: saturate(0.35) brightness(1.04) contrast(0.9);
}
</style>
