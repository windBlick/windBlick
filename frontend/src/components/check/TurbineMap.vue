<script setup lang="ts">
import L from 'leaflet'
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import type { LatLon, Turbine } from '../../types'
import { destination, distance } from '../../lib/geo'
import { TURBINE_SOURCE_IS_DEMO, getTurbinesInBbox } from '../../api/turbineSource'

/**
 * Map for step 2: camera position + view cone, and selection of turbines from
 * the NRW WFS layer. Turbines are not placed freely: the API contract only
 * accepts complete WFS records (docs/api-contract.md §4).
 */
const props = defineProps<{
  camera: { lat: number | null; lon: number | null; headingDeg: number | null; fovDeg: number | null }
  selected: Turbine[]
  fallbackCenter: LatLon
}>()
const emit = defineEmits<{ toggleTurbine: [t: Turbine]; moveCamera: [pos: LatLon] }>()

const el = ref<HTMLDivElement | null>(null)
const showLayer = ref(true)
const hint = ref<string | null>(null)
let hintTimer: number | undefined

let map: L.Map | null = null
let coneLayer: L.LayerGroup | null = null
let cameraMarker: L.Marker | null = null
let turbineLayer: L.LayerGroup | null = null
let available: Turbine[] = []

const turbineSvg = `<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M12 12V3M12 12l7.8 4.5M12 12l-7.8 4.5M12 12v9"/></svg>`
const cameraSvg = `<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="#fff" stroke-width="1.8" stroke-linejoin="round"><path d="M4 8.5A1.5 1.5 0 0 1 5.5 7H8l1.5-2h5L16 7h2.5A1.5 1.5 0 0 1 20 8.5v9a1.5 1.5 0 0 1-1.5 1.5h-13A1.5 1.5 0 0 1 4 17.5Z"/><circle cx="12" cy="13" r="3.2"/></svg>`

const escapeHtml = (s: string) => s.replace(/[&<>"']/g, (c) => `&#${c.charCodeAt(0)};`)
const labelOf = (t: Turbine) => {
  const i = props.selected.findIndex((s) => s.id === t.id)
  return t.name ?? `Turbine ${i + 1}`
}

const cameraIcon = L.divIcon({
  className: 'wb-marker',
  html: `<div class="wb-camera">${cameraSvg}</div>`,
  iconSize: [40, 50],
  iconAnchor: [20, 50],
})

function flash(text: string) {
  hint.value = text
  window.clearTimeout(hintTimer)
  hintTimer = window.setTimeout(() => (hint.value = null), 4000)
}

function drawCamera() {
  if (!map) return
  const { lat, lon } = props.camera
  if (lat === null || lon === null) {
    cameraMarker?.remove()
    cameraMarker = null
    return
  }
  if (!cameraMarker) {
    cameraMarker = L.marker([lat, lon], { icon: cameraIcon, draggable: true, zIndexOffset: 1000, title: 'Camera position (drag to move)' })
      .on('dragend', (e) => {
        const p = (e.target as L.Marker).getLatLng()
        emit('moveCamera', { lat: p.lat, lon: p.lng })
      })
      .addTo(map)
  } else {
    cameraMarker.setLatLng([lat, lon])
  }
}

function drawCone() {
  if (!map) return
  coneLayer?.remove()
  coneLayer = null
  const { lat, lon, headingDeg, fovDeg } = props.camera
  if (lat === null || lon === null || headingDeg === null) return
  const cam = { lat, lon }
  const far = Math.max(0, ...props.selected.map((t) => distance(cam, { lat: t.position.latitude_deg, lon: t.position.longitude_deg })))
  const r = Math.max(1200, far * 1.2)
  const centre = destination(cam, headingDeg, r)
  const layers: L.Layer[] = [
    L.polyline([[lat, lon], [centre.lat, centre.lon]], { color: '#17513a', weight: 1.5, dashArray: '5 6', interactive: false }),
  ]
  if (fovDeg !== null) {
    const pts: L.LatLngExpression[] = [[lat, lon]]
    for (let i = 0; i <= 24; i++) {
      const p = destination(cam, headingDeg - fovDeg / 2 + (fovDeg * i) / 24, r)
      pts.push([p.lat, p.lon])
    }
    layers.unshift(
      L.polygon(pts, { color: '#2f7d57', weight: 1, dashArray: '4 4', fillColor: '#7cc39a', fillOpacity: 0.28, interactive: false }),
    )
  }
  coneLayer = L.layerGroup(layers).addTo(map)
}

function drawTurbines() {
  if (!map || !turbineLayer) return
  turbineLayer.clearLayers()
  const selectedIds = new Set(props.selected.map((t) => t.id))
  // Selected turbines stay visible even when the layer is hidden or out of view.
  const pool = new Map<string, Turbine>()
  if (showLayer.value) for (const t of available) pool.set(t.id, t)
  for (const t of props.selected) pool.set(t.id, t)

  for (const t of pool.values()) {
    const isSelected = selectedIds.has(t.id)
    const statusText = t.status === 'operating' ? 'Operating' : 'Approved'
    const html = isSelected
      ? `<div class="wb-turbine"><span class="wb-turbine__dot">${turbineSvg}</span><span class="wb-label">${escapeHtml(labelOf(t))}</span></div>`
      : `<div class="wb-wfs wb-wfs--${t.status}" aria-label="${statusText} turbine">${turbineSvg}</div>`
    const icon = L.divIcon({
      className: 'wb-marker',
      html,
      iconSize: isSelected ? [48, 72] : [26, 26],
      iconAnchor: isSelected ? [24, 24] : [13, 13],
    })
    L.marker([t.position.latitude_deg, t.position.longitude_deg], { icon, riseOnHover: true, keyboard: true })
      .bindTooltip(
        `<strong>${escapeHtml(t.name ?? 'Unnamed turbine')}</strong><br>${statusText} · hub ${t.hub_height_m} m · rotor ⌀ ${t.rotor_diameter_m} m<br><em>${isSelected ? 'Click to remove' : 'Click to select'}</em>`,
        { direction: 'top', offset: [0, isSelected ? -26 : -12] },
      )
      .on('click', () => emit('toggleTurbine', t))
      .addTo(turbineLayer)
  }
}

async function loadTurbines() {
  if (!map) return
  const b = map.getBounds()
  try {
    available = await getTurbinesInBbox({ west: b.getWest(), south: b.getSouth(), east: b.getEast(), north: b.getNorth() })
  } catch (err) {
    console.warn('Turbine layer could not be loaded', err)
    available = []
    flash('The turbine layer could not be loaded.')
  }
  drawTurbines()
}

function fitAll() {
  if (!map) return
  const pts: [number, number][] = props.selected.map((t) => [t.position.latitude_deg, t.position.longitude_deg])
  if (props.camera.lat !== null && props.camera.lon !== null) pts.push([props.camera.lat, props.camera.lon])
  if (pts.length === 0) map.setView([props.fallbackCenter.lat, props.fallbackCenter.lon], 13)
  else if (pts.length === 1) map.setView(pts[0]!, 14)
  else map.fitBounds(L.latLngBounds(pts), { padding: [80, 80], maxZoom: 16 })
}

onMounted(() => {
  map = L.map(el.value!).setView([props.fallbackCenter.lat, props.fallbackCenter.lon], 13)
  // Swap for the project's own basemap (e.g. a WMS) once agreed.
  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    className: 'wb-basemap',
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  }).addTo(map)
  L.control.scale({ imperial: false, position: 'bottomright' }).addTo(map)
  turbineLayer = L.layerGroup().addTo(map)

  map.on('click', (e: L.LeafletMouseEvent) => {
    if (props.camera.lat === null || props.camera.lon === null) {
      emit('moveCamera', { lat: e.latlng.lat, lon: e.latlng.lng })
      flash('Camera position set. Drag the camera pin to adjust it.')
    } else {
      flash('Turbines come from the NRW register — click a turbine marker to select it.')
    }
  })
  map.on('moveend', loadTurbines)

  fitAll()
  drawCamera()
  drawCone()
  loadTurbines()
})

onBeforeUnmount(() => {
  window.clearTimeout(hintTimer)
  map?.remove()
  map = null
})

watch(
  () => [props.camera.lat, props.camera.lon, props.camera.headingDeg, props.camera.fovDeg],
  () => {
    drawCamera()
    drawCone()
  },
)
watch(
  () => props.selected.map((t) => t.id).join('|'),
  () => {
    drawTurbines()
    drawCone()
  },
)
watch(showLayer, drawTurbines)

defineExpose({ fitAll })
</script>

<template>
  <div class="map-wrap">
    <div ref="el" class="map" role="application" aria-label="Map: select turbines and set the camera position" />

    <div class="top">
      <span v-if="TURBINE_SOURCE_IS_DEMO" class="demo" title="The real NRW WFS adapter is not connected yet">Demo turbine data</span>
      <label class="toggle">
        <input v-model="showLayer" type="checkbox" role="switch" />
        <span class="toggle__track" aria-hidden="true"><span class="toggle__thumb" /></span>
        NRW Turbines
      </label>
    </div>

    <div class="legend" aria-label="Legend">
      <span><i class="wb-wfs wb-wfs--operating" />Operating</span>
      <span><i class="wb-wfs wb-wfs--approved" />Approved</span>
    </div>

    <div class="hint" role="status">
      <span class="hint__dot" />
      {{
        hint ??
        (camera.lat === null ? 'Click the map where the photo was taken' : 'Click a turbine marker to select it')
      }}
    </div>
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
}
.top {
  position: absolute;
  top: 16px;
  right: 16px;
  z-index: 500;
  display: flex;
  gap: 8px;
  align-items: center;
}
.demo {
  padding: 6px 10px;
  border-radius: 999px;
  background: var(--warning-bg);
  color: var(--warning-ink);
  font-size: 12px;
  font-weight: 600;
}
.toggle {
  position: relative;
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
.legend {
  position: absolute;
  top: 60px;
  right: 16px;
  z-index: 500;
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 8px 12px;
  border-radius: var(--radius-sm);
  background: rgba(255, 255, 255, 0.95);
  font-size: 12px;
  color: var(--ink-700);
}
.legend span {
  display: flex;
  align-items: center;
  gap: 8px;
}
.legend i {
  width: 14px !important;
  height: 14px !important;
}
.hint {
  position: absolute;
  left: 16px;
  bottom: 16px;
  z-index: 500;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  max-width: calc(100% - 140px);
  padding: 8px 16px;
  border-radius: var(--radius-sm);
  background: #fff;
  font-size: 12px;
  color: var(--ink-700);
  pointer-events: none;
}
.hint__dot {
  flex: none;
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
  cursor: pointer;
}
.wb-turbine__dot {
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: var(--green-900);
  color: #fff;
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
/* Unselected WFS turbines: neutral grey; status shown by shape (filled vs outlined), plus legend text */
.wb-wfs {
  display: grid;
  place-items: center;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  border: 2px solid #5f6b66;
  cursor: pointer;
  transition: transform 0.15s;
}
.wb-wfs svg {
  width: 14px;
  height: 14px;
}
.wb-wfs:hover {
  transform: scale(1.15);
}
.wb-wfs--operating {
  background: #5f6b66;
  color: #fff;
}
.wb-wfs--approved {
  background: #fff;
  color: #5f6b66;
  border-style: dashed;
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
.leaflet-container {
  font-family: var(--font);
}
.wb-basemap {
  filter: saturate(0.35) brightness(1.04) contrast(0.9);
}
</style>
