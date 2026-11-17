<script setup lang="ts">
import { computed } from 'vue'
import AppIcon from '../components/AppIcon.vue'
import CompareSlider from '../components/preview/CompareSlider.vue'
import { useSessionStore } from '../stores/session'
import { resultImageUrl } from '../api/visualizations'
import type { CameraValueSource } from '../types'

const session = useSessionStore()
const res = computed(() => session.result!)
const renderedUrl = computed(() => resultImageUrl(res.value))

/** Turbines not drawn in the photo (outside the frame or behind the camera). */
const notDrawn = computed(() => res.value.turbines.filter((t) => t.outcome !== 'drawn'))

const warning = computed(() => {
  const n = notDrawn.value.length
  const total = res.value.turbines.length
  if (n === 0) return null
  if (n === total) return 'None of the selected turbines is within this photo’s field of view.'
  return `Note: ${n} of ${total} selected turbines ${n === 1 ? 'is' : 'are'} outside your camera’s field of view.`
})

/** Warnings worth showing as text (outcome-related ones are summarised above). */
const otherWarnings = computed(() =>
  res.value.warnings.filter(
    (w) => !['TURBINE_OUTSIDE_FRAME', 'TURBINE_BEHIND_CAMERA', 'NO_TURBINES_DRAWN', 'PINHOLE_APPROXIMATION', 'SCHEMATIC_ROTOR_ORIENTATION'].includes(w.code),
  ),
)

const sourceLabel = (s: CameraValueSource | undefined) =>
  s?.source === 'exif' ? 'from photo' : s?.source === 'override' ? 'entered' : s?.source === 'derived' ? 'calculated' : '—'

const cameraRows = computed(() => {
  const c = res.value.camera_used
  const src = res.value.camera_value_sources
  const hfov = (2 * Math.atan(res.value.image.width_px / (2 * c.intrinsics.fx_px)) * 180) / Math.PI
  return [
    { label: 'Position', value: `${c.position.latitude_deg.toFixed(5)}, ${c.position.longitude_deg.toFixed(5)}`, source: sourceLabel(src['/position/latitude_deg']) },
    { label: 'Elevation', value: `${c.position.elevation.value_m.toFixed(1)} m NHN`, source: sourceLabel(src['/position/elevation/value_m']) },
    { label: 'Heading', value: `${c.orientation.heading_deg.toFixed(1)}°`, source: sourceLabel(src['/orientation/heading_deg']) },
    { label: 'Pitch / roll', value: `${c.orientation.pitch_deg.toFixed(1)}° / ${c.orientation.roll_deg.toFixed(1)}°`, source: sourceLabel(src['/orientation/pitch_deg']) },
    { label: 'Field of view', value: `${hfov.toFixed(1)}°`, source: sourceLabel(src['/intrinsics/fx_px']) },
  ]
})

function download() {
  const a = document.createElement('a')
  a.href = renderedUrl.value
  a.download = `windblick-${(session.photo?.name ?? 'preview').replace(/\.[^.]+$/, '')}.png`
  a.click()
}
</script>

<template>
  <section>
    <h1 class="page-title">Compare your simulated view</h1>
    <p class="page-lead">
      Drag the slider to compare your original photo with the calculated wind turbine outlines, or go back to adjust
      positions and dimensions.
    </p>

    <div class="card panel">
      <div v-if="warning" class="warning" role="status">
        <AppIcon name="warning" :size="18" />
        <span>
          {{ warning }}
          <template v-if="notDrawn.length">({{ notDrawn.map((t) => t.label).join(', ') }})</template>
        </span>
      </div>

      <CompareSlider
        v-if="session.photo"
        :original-url="session.photo.url"
        :rendered-url="renderedUrl"
        :width="res.image.width_px"
        :height="res.image.height_px"
      />

      <p class="note">
        <AppIcon name="info" :size="16" />
        Geometric approximation only. Rotor orientation is schematic, and foreground trees, terrain, or buildings may
        still obstruct the real view.
      </p>
      <p v-for="w in otherWarnings" :key="w.code + (w.turbine_id ?? '')" class="note">
        <AppIcon name="info" :size="16" /> {{ w.message }}
      </p>

      <details class="used">
        <summary>Camera values used for this preview</summary>
        <table>
          <tbody>
            <tr v-for="row in cameraRows" :key="row.label">
              <th scope="row">{{ row.label }}</th>
              <td>{{ row.value }}</td>
              <td class="used__src">{{ row.source }}</td>
            </tr>
          </tbody>
        </table>
      </details>

      <div class="actions">
        <RouterLink to="/check" class="btn btn-secondary"><AppIcon name="arrow-left" :size="16" /> Adjust turbines</RouterLink>
        <button type="button" class="btn" disabled title="Coming soon">Calibrate horizon (coming soon)</button>
        <button type="button" class="btn btn-primary actions__download" @click="download">
          <AppIcon name="download" :size="18" /> Download image
        </button>
      </div>
    </div>
  </section>
</template>

<style scoped>
.panel {
  margin-top: 28px;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.warning {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: var(--radius);
  background: var(--warning-bg);
  color: var(--warning-ink);
  font-size: 13px;
  font-weight: 500;
}
.warning svg {
  flex: none;
}
.note {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-radius: var(--radius);
  background: var(--surface-muted);
  font-size: 12px;
  color: var(--ink-700);
}
.note svg {
  flex: none;
}
.used {
  font-size: 13px;
  color: var(--ink-700);
}
.used summary {
  cursor: pointer;
  font-weight: 500;
  padding: 4px 0;
}
.used table {
  margin-top: 8px;
  border-collapse: collapse;
}
.used th,
.used td {
  padding: 4px 16px 4px 0;
  text-align: left;
}
.used th {
  font-weight: 500;
}
.used__src {
  color: var(--ink-500);
}
.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 4px;
}
.actions__download {
  margin-left: auto;
}
</style>
