<script setup lang="ts">
import { computed } from 'vue'
import AppIcon from '../AppIcon.vue'
import type { CameraField, CameraOverrideForm, ExifHints } from '../../types'
import { CAMERA_FIELD_PATHS } from '../../stores/session'

/**
 * Camera values. An empty field is NOT sent: the backend then takes that value
 * from the photo's EXIF data, or reports it as unresolved (contract §1).
 */
const props = defineProps<{
  overrides: CameraOverrideForm
  exif: ExifHints | null
  fieldErrors: Record<string, string>
}>()
const emit = defineEmits<{ update: [field: CameraField, value: number | null]; loadSample: [] }>()

interface FieldDef {
  key: CameraField
  label: string
  unit: string
  step: number
  min?: number
  max?: number
  help?: string
}

const fields: FieldDef[] = [
  { key: 'latitude', label: 'Latitude', unit: '°', step: 0.0001, min: -90, max: 90 },
  { key: 'longitude', label: 'Longitude', unit: '°', step: 0.0001, min: -180, max: 180 },
  {
    key: 'elevationM',
    label: 'Camera elevation',
    unit: 'm NHN',
    step: 0.1,
    help: 'Height of the camera above sea level (NHN), e.g. ground height + 1.6 m when standing.',
  },
  { key: 'headingDeg', label: 'Heading', unit: '°', step: 1, min: 0, max: 359.9, help: 'Viewing direction, clockwise from true north (90 = east).' },
  { key: 'pitchDeg', label: 'Pitch', unit: '°', step: 0.5, min: -89, max: 89, help: 'Tilt up (+) or down (−). 0 = level.' },
  { key: 'rollDeg', label: 'Roll', unit: '°', step: 0.5, min: -180, max: 179.9, help: 'Sideways tilt. 0 = level.' },
  { key: 'horizontalFovDeg', label: 'Field of view', unit: '°', step: 1, min: 1, max: 179, help: 'Horizontal angle the photo covers. Typical phone main camera: 65–75°.' },
]

/** Placeholder text: what the photo provides, if anything (preview only). */
const placeholder = computed<Record<CameraField, string>>(() => {
  const e = props.exif
  const h = e?.heading
  return {
    latitude: e?.position ? `${e.position.lat.toFixed(5)} (from photo)` : 'Required',
    longitude: e?.position ? `${e.position.lon.toFixed(5)} (from photo)` : 'Required',
    elevationM: 'Required',
    headingDeg: h?.reference === 'true' ? `${Math.round(h.value)} (from photo)` : 'Required',
    pitchDeg: 'Required',
    rollDeg: 'Required',
    horizontalFovDeg: 'Required',
  }
})

const notes = computed(() => {
  const e = props.exif
  const list: string[] = []
  if (e?.heading && e.heading.reference !== 'true') {
    list.push(`The photo has a ${e.heading.reference} compass direction (${Math.round(e.heading.value)}°), which cannot be used as a true-north heading.`)
  }
  if (e?.gpsAltitudeM !== null && e?.gpsAltitudeM !== undefined) {
    list.push(`The photo's GPS altitude is ${Math.round(e.gpsAltitudeM)} m, but its height reference is unknown — check before entering it.`)
  }
  if (e?.focalLength35mm) {
    list.push(`35 mm-equivalent focal length ${e.focalLength35mm} mm (≈ ${Math.round((2 * Math.atan(36 / (2 * e.focalLength35mm)) * 180) / Math.PI)}° if uncropped).`)
  }
  return list
})

const detected = computed(() => {
  const e = props.exif
  return { gps: !!e?.position, compass: e?.heading?.reference === 'true' }
})

function onInput(key: CameraField, e: Event) {
  const raw = (e.target as HTMLInputElement).value.trim()
  if (raw === '') return emit('update', key, null)
  const v = Number(raw)
  if (Number.isFinite(v)) emit('update', key, v)
}
</script>

<template>
  <section class="card panel">
    <header class="panel__head">
      <h2>Camera &amp; Perspective</h2>
      <button type="button" class="link" @click="emit('loadSample')">Load sample</button>
    </header>

    <span v-if="detected.gps && detected.compass" class="badge badge-success">
      GPS &amp; Compass detected <AppIcon name="check" :size="12" />
    </span>
    <span v-else-if="detected.gps" class="badge badge-warning">
      <AppIcon name="warning" :size="13" /> GPS found, no true-north heading
    </span>
    <span v-else class="badge badge-warning"><AppIcon name="warning" :size="13" /> No location data in photo</span>

    <p class="panel__intro">Empty fields are taken from the photo where possible. Values you enter replace the photo’s values.</p>

    <div class="grid">
      <label v-for="f in fields" :key="f.key" class="field" :title="f.help">
        <span class="field-label">{{ f.label }} <span class="unit">({{ f.unit }})</span></span>
        <input
          class="input"
          type="number"
          inputmode="decimal"
          :step="f.step"
          :min="f.min"
          :max="f.max"
          :value="overrides[f.key] ?? ''"
          :placeholder="placeholder[f.key]"
          :aria-invalid="
            !!fieldErrors[CAMERA_FIELD_PATHS[f.key]] || (f.key === 'horizontalFovDeg' && !!fieldErrors['/camera/intrinsics'])
          "
          :aria-describedby="fieldErrors[CAMERA_FIELD_PATHS[f.key]] ? `err-${f.key}` : undefined"
          @change="onInput(f.key, $event)"
        />
        <span v-if="fieldErrors[CAMERA_FIELD_PATHS[f.key]]" :id="`err-${f.key}`" class="field-error">
          {{ fieldErrors[CAMERA_FIELD_PATHS[f.key]] }}
        </span>
      </label>
    </div>

    <p v-if="fieldErrors['/camera/intrinsics']" class="field-error">{{ fieldErrors['/camera/intrinsics'] }}</p>

    <ul v-if="notes.length" class="notes">
      <li v-for="n in notes" :key="n"><AppIcon name="info" :size="14" /> {{ n }}</li>
    </ul>
  </section>
</template>

<style scoped>
.panel {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
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
.panel__intro {
  font-size: 12px;
  line-height: 1.5;
  color: var(--ink-500);
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
.unit {
  color: var(--ink-400);
}
.input::placeholder {
  color: var(--ink-400);
}
.field-error {
  display: block;
  margin-top: 4px;
  font-size: 11px;
  line-height: 1.4;
  color: var(--danger);
}
.notes {
  list-style: none;
  margin: 0;
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  background: var(--surface-muted);
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 12px;
  line-height: 1.45;
  color: var(--ink-700);
}
.notes li {
  display: flex;
  gap: 8px;
}
.notes svg {
  flex: none;
  margin-top: 2px;
}
</style>
