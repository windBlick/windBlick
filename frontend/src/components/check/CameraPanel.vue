<script setup lang="ts">
import { ref, watch } from 'vue'
import AppIcon from '../AppIcon.vue'
import type { CameraPose } from '../../types'
import { formatLatLon, parseLatLon } from '../../lib/geo'

const props = defineProps<{ camera: CameraPose; gpsDetected: boolean; compassDetected: boolean }>()
const emit = defineEmits<{ update: [patch: Partial<CameraPose>]; loadSample: [] }>()

const latLonText = ref(formatLatLon(props.camera))
const latLonInvalid = ref(false)
watch(
  () => [props.camera.lat, props.camera.lon],
  () => {
    latLonText.value = formatLatLon(props.camera)
    latLonInvalid.value = false
  },
)

function commitLatLon() {
  const p = parseLatLon(latLonText.value)
  latLonInvalid.value = !p
  if (p) emit('update', p)
}

function commitNumber(key: 'azimuth' | 'pitch' | 'fov', e: Event, min: number, max: number) {
  const v = Number((e.target as HTMLInputElement).value)
  if (!Number.isFinite(v)) return
  let clamped = Math.min(max, Math.max(min, v))
  if (key === 'azimuth') clamped = ((clamped % 360) + 360) % 360
  emit('update', { [key]: clamped })
}
</script>

<template>
  <section class="card panel">
    <header class="panel__head">
      <h2>Camera &amp; Perspective</h2>
      <button type="button" class="link" @click="emit('loadSample')">Load sample</button>
    </header>

    <span v-if="gpsDetected && compassDetected" class="badge badge-success">
      GPS &amp; Compass detected <AppIcon name="check" :size="12" />
    </span>
    <span v-else-if="gpsDetected" class="badge badge-warning">
      <AppIcon name="warning" :size="13" /> GPS found, no compass — check the azimuth
    </span>
    <span v-else class="badge badge-warning">
      <AppIcon name="warning" :size="13" /> No location data — drag the camera pin on the map
    </span>

    <div class="grid">
      <label>
        <span class="field-label">Lat / Lon</span>
        <input
          v-model="latLonText"
          class="input"
          inputmode="decimal"
          :aria-invalid="latLonInvalid"
          @change="commitLatLon"
          @keydown.enter="commitLatLon"
        />
      </label>
      <label>
        <span class="field-label">Azimuth (°)</span>
        <input
          class="input"
          type="number"
          step="1"
          min="0"
          max="359"
          :value="Math.round(camera.azimuth)"
          @change="commitNumber('azimuth', $event, -360, 720)"
        />
      </label>
      <label>
        <span class="field-label">Pitch (°)</span>
        <input
          class="input"
          type="number"
          step="0.5"
          min="-30"
          max="30"
          :value="camera.pitch"
          @change="commitNumber('pitch', $event, -30, 30)"
        />
      </label>
      <label>
        <span class="field-label">FOV (°)</span>
        <input
          class="input"
          type="number"
          step="1"
          min="10"
          max="120"
          :value="camera.fov"
          @change="commitNumber('fov', $event, 10, 120)"
        />
      </label>
    </div>
  </section>
</template>

<style scoped>
.panel {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.panel__head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}
.panel__head h2 {
  font-size: 18px;
  font-weight: 600;
}
.panel .badge {
  align-self: flex-start;
}
.link {
  border: 0;
  background: none;
  padding: 0;
  font-size: 12px;
  font-weight: 500;
  color: var(--green-900);
  text-decoration: underline;
  cursor: pointer;
}
.grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px 16px;
}
</style>
