<script setup lang="ts">
import AppIcon from '../AppIcon.vue'
import type { CameraPose, PlannedTurbine } from '../../types'
import { distance } from '../../lib/geo'

defineProps<{ turbines: PlannedTurbine[]; camera: CameraPose }>()
const emit = defineEmits<{
  update: [id: string, patch: Partial<PlannedTurbine>]
  remove: [id: string]
}>()

function commit(id: string, key: 'hubHeight' | 'rotorDiameter', e: Event) {
  const v = Number((e.target as HTMLInputElement).value)
  if (Number.isFinite(v) && v > 0) emit('update', id, { [key]: Math.min(400, v) })
}

const km = (m: number) => (m >= 1000 ? `${(m / 1000).toFixed(2)} km` : `${Math.round(m)} m`)
</script>

<template>
  <section class="card panel">
    <h2>Wind Turbines ({{ turbines.length }})</h2>

    <p v-if="!turbines.length" class="empty">No turbines yet. Click on the map to place the first one.</p>

    <TransitionGroup name="list" tag="ul" class="list">
      <li v-for="t in turbines" :key="t.id" class="item">
        <div class="item__head">
          <span class="item__label">{{ t.label }}</span>
          <span class="item__dist">{{ km(distance(camera, t)) }} away</span>
          <button type="button" class="item__del" :aria-label="`Remove ${t.label}`" @click="emit('remove', t.id)">
            <AppIcon name="trash" :size="16" />
          </button>
        </div>
        <div class="item__fields">
          <label>
            <span class="field-label">Hub height (m)</span>
            <input class="input" type="number" min="1" max="400" :value="t.hubHeight" @change="commit(t.id, 'hubHeight', $event)" />
          </label>
          <label>
            <span class="field-label">Rotor diameter (m)</span>
            <input
              class="input"
              type="number"
              min="1"
              max="400"
              :value="t.rotorDiameter"
              @change="commit(t.id, 'rotorDiameter', $event)"
            />
          </label>
        </div>
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
  margin-bottom: 10px;
}
.item__label {
  font-size: 13px;
  font-weight: 600;
  color: var(--green-900);
}
.item__dist {
  font-size: 12px;
  color: var(--ink-500);
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
.item__fields {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
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
