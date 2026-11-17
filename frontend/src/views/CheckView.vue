<script setup lang="ts">
import { nextTick, ref } from 'vue'
import { useRouter } from 'vue-router'
import AppIcon from '../components/AppIcon.vue'
import TurbineMap from '../components/check/TurbineMap.vue'
import CameraPanel from '../components/check/CameraPanel.vue'
import TurbineList from '../components/check/TurbineList.vue'
import { useSessionStore } from '../stores/session'

const session = useSessionStore()
const router = useRouter()
const map = ref<InstanceType<typeof TurbineMap> | null>(null)

async function loadSample() {
  await session.loadSample()
  await nextTick()
  map.value?.fitAll()
}

async function generate() {
  await session.runPreview()
  if (!session.previewError) router.push({ name: 'preview' })
}
</script>

<template>
  <section>
    <h1 class="page-title">Check perspective &amp; place turbines</h1>
    <p class="page-lead">
      Verify your camera location and viewing direction, select turbine positions on the map, and enter their hub
      height and rotor diameter.
    </p>

    <div class="layout">
      <div class="card map-card">
        <TurbineMap
          ref="map"
          :camera="session.camera"
          :turbines="session.turbines"
          @add-turbine="session.addTurbine"
          @move-turbine="(id, p) => session.updateTurbine(id, p)"
          @move-camera="session.updateCamera"
        />
      </div>
      <div class="side">
        <CameraPanel
          :camera="session.camera"
          :gps-detected="session.gpsDetected"
          :compass-detected="session.compassDetected"
          @update="session.updateCamera"
          @load-sample="loadSample"
        />
        <TurbineList
          :turbines="session.turbines"
          :camera="session.camera"
          @update="session.updateTurbine"
          @remove="session.removeTurbine"
        />
      </div>
    </div>

    <p v-if="session.previewError" class="error" role="alert">{{ session.previewError }}</p>

    <div class="actions">
      <RouterLink to="/" class="btn btn-secondary btn-lg"><AppIcon name="arrow-left" :size="16" /> Back</RouterLink>
      <button
        type="button"
        class="btn btn-primary btn-lg"
        :disabled="!session.canGenerate || session.previewLoading"
        :title="session.canGenerate ? undefined : 'Place at least one turbine on the map'"
        @click="generate"
      >
        {{ session.previewLoading ? 'Calculating…' : 'Generate preview' }}
        <AppIcon v-if="!session.previewLoading" name="arrow-right" :size="16" />
      </button>
    </div>
  </section>
</template>

<style scoped>
.layout {
  display: grid;
  grid-template-columns: minmax(0, 1.5fr) minmax(320px, 1fr);
  gap: 24px;
  margin-top: 28px;
  align-items: stretch;
}
.map-card {
  padding: 14px;
  min-height: 470px;
}
.side {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.actions {
  display: flex;
  justify-content: space-between;
  margin-top: 20px;
}
.error {
  margin-top: 16px;
  color: var(--danger);
}
@media (max-width: 960px) {
  .layout {
    grid-template-columns: 1fr;
  }
}
</style>
