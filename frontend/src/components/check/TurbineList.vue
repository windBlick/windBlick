<script setup lang="ts">
import AppIcon from '../AppIcon.vue'
import type { Turbine } from '../../types'
import { distance } from '../../lib/geo'

/**
 * Selected turbines. Dimensions are read-only: they come from the WFS record
 * and are submitted unchanged (contract §4).
 */
const props = defineProps<{
  turbines: Turbine[]
  camera: { lat: number | null; lon: number | null }
  fieldErrors: Record<string, string>
}>()
const emit = defineEmits<{ remove: [id: string] }>()

const away = (t: Turbine) => {
  if (props.camera.lat === null || props.camera.lon === null) return null
  const m = distance({ lat: props.camera.lat, lon: props.camera.lon }, { lat: t.position.latitude_deg, lon: t.position.longitude_deg })
  return m >= 1000 ? `${(m / 1000).toFixed(2)} km away` : `${Math.round(m)} m away`
}

const errorsFor = (i: number) =>
  Object.entries(props.fieldErrors)
    .filter(([path]) => path.startsWith(`/turbines/${i}/`) || path === `/turbines/${i}`)
    .map(([, msg]) => msg)
</script>

<template>
  <section class="card panel">
    <h2>Wind Turbines ({{ turbines.length }})</h2>

    <p v-if="!turbines.length" class="empty">
      No turbines selected yet. Click a turbine marker on the map to add it.
      <span v-if="fieldErrors['/turbines']" class="field-error">{{ fieldErrors['/turbines'] }}</span>
    </p>

    <TransitionGroup name="list" tag="ul" class="list">
      <li v-for="(t, i) in turbines" :key="t.id" class="item">
        <div class="item__head">
          <span class="item__label">{{ t.name ?? `Turbine ${i + 1}` }}</span>
          <span class="status" :class="`status--${t.status}`">{{ t.status === 'operating' ? 'Operating' : 'Approved' }}</span>
          <button type="button" class="item__del" :aria-label="`Remove ${t.name ?? `Turbine ${i + 1}`}`" @click="emit('remove', t.id)">
            <AppIcon name="trash" :size="16" />
          </button>
        </div>
        <dl class="item__facts">
          <div><dt>Hub height</dt><dd>{{ t.hub_height_m }} m</dd></div>
          <div><dt>Rotor diameter</dt><dd>{{ t.rotor_diameter_m }} m</dd></div>
          <div><dt>Total height</dt><dd>{{ t.hub_height_m + t.rotor_diameter_m / 2 }} m</dd></div>
        </dl>
        <p class="item__meta">
          <span v-if="t.turbine_type">{{ t.turbine_type }} · </span>
          <span v-if="away(t)">{{ away(t) }} · </span>
          <span>Source: NRW register</span>
        </p>
        <p v-for="msg in errorsFor(i)" :key="msg" class="field-error">{{ msg }}</p>
      </li>
    </TransitionGroup>
  </section>
</template>

<style scoped>
.panel {
  padding: 20px;
}
.panel h2 {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 14px;
}
.empty {
  font-size: 14px;
  line-height: 1.5;
  color: var(--ink-500);
  padding: 16px;
  border: 1px dashed var(--border-strong);
  border-radius: var(--radius);
  text-align: center;
}
.list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.item {
  padding: 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--surface-muted);
}
.item__head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}
.item__label {
  font-size: 13px;
  font-weight: 600;
  color: var(--green-900);
}
.status {
  padding: 2px 8px;
  border-radius: 999px;
  border: 1px solid #5f6b66;
  font-size: 11px;
  font-weight: 500;
  color: #3f4844;
}
.status--approved {
  border-style: dashed;
}
.item__del {
  margin-left: auto;
  display: grid;
  place-items: center;
  width: 28px;
  height: 28px;
  border: 0;
  border-radius: var(--radius-sm);
  background: none;
  color: var(--ink-500);
  cursor: pointer;
}
.item__del:hover {
  background: #fde8e6;
  color: var(--danger);
}
.item__facts {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  margin: 0;
}
.item__facts div {
  padding: 6px 8px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
}
.item__facts dt {
  font-size: 11px;
  color: var(--ink-500);
}
.item__facts dd {
  margin: 2px 0 0;
  font-size: 13px;
  font-weight: 500;
}
.item__meta {
  margin-top: 8px;
  font-size: 11px;
  color: var(--ink-500);
}
.field-error {
  display: block;
  margin-top: 6px;
  font-size: 12px;
  color: var(--danger);
}
.list-enter-active,
.list-leave-active {
  transition: opacity 0.2s, transform 0.2s;
}
.list-enter-from,
.list-leave-to {
  opacity: 0;
  transform: translateX(12px);
}
</style>
