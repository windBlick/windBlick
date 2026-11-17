<script setup lang="ts">
import { computed, nextTick, ref } from 'vue'
import { useRouter } from 'vue-router'
import AppIcon from '../components/AppIcon.vue'
import TurbineMap from '../components/check/TurbineMap.vue'
import CameraPanel from '../components/check/CameraPanel.vue'
import TurbineList from '../components/check/TurbineList.vue'
import { CAMERA_FIELD_PATHS, useSessionStore } from '../stores/session'
import { SAMPLE_CAMERA } from '../lib/sample'

const session = useSessionStore()
const router = useRouter()
const map = ref<InstanceType<typeof TurbineMap> | null>(null)

// While the turbine layer is demo data, centre on it when the photo has no location.
const fallbackCenter = { lat: SAMPLE_CAMERA.latitude!, lon: SAMPLE_CAMERA.longitude! }

/** Errors not shown next to a specific field. */
const generalErrors = computed(() => {
  const shownPaths = new Set<string>([...Object.values(CAMERA_FIELD_PATHS), '/camera/intrinsics', '/turbines'])
  return (session.problem?.problem.errors ?? []).filter(
    (e) => !e.path || !(shownPaths.has(e.path) || /^\/turbines\/\d+/.test(e.path)),
  )
})

const bannerTitle = computed(() => {
  switch (session.problem?.code) {
    case 'CAMERA_PARAMETERS_UNRESOLVED':
      return 'Some camera values are missing'
    case 'VALIDATION_ERROR':
      return 'Some values need checking'
    case 'NETWORK_ERROR':
      return 'Server not reachable'
    default:
      return 'The preview could not be generated'
  }
})

async function loadSample() {
  await session.loadSample()
  await nextTick()
  map.value?.fitAll()
}

async function generate() {
  if (await session.generate()) router.push({ name: 'preview' })
}
</script>

<template>
  <section>
    <h1 class="page-title">Check perspective &amp; place turbines</h1>
    <p class="page-lead">
      Verify your camera location and viewing direction, select turbines on the map, and check their hub height and
      rotor diameter.
    </p>

    <div class="layout">
      <div class="card map-card">
        <TurbineMap
          ref="map"
          :camera="session.mapCamera"
          :selected="session.turbines"
          :fallback-center="session.exif?.position ?? fallbackCenter"
          @toggle-turbine="session.toggleTurbine"
          @move-camera="
            (p) => {
              session.setOverride('latitude', Number(p.lat.toFixed(6)))
              session.setOverride('longitude', Number(p.lon.toFixed(6)))
            }
          "
        />
      </div>
      <div class="side">
        <CameraPanel
          :overrides="session.overrides"
          :exif="session.exif"
          :field-errors="session.fieldErrors"
          :photo-size="session.photo"
          @update="session.setOverride"
          @load-sample="loadSample"
        />
        <TurbineList
          :turbines="session.turbines"
          :camera="session.mapCamera"
          :field-errors="session.fieldErrors"
          @remove="session.removeTurbine"
        />
      </div>
    </div>

    <div v-if="session.problem" class="banner" role="alert">
      <AppIcon name="warning" :size="18" />
      <div>
        <strong>{{ bannerTitle }}</strong>
        <p>{{ session.problem.message }}</p>
        <ul v-if="generalErrors.length">
          <li v-for="e in generalErrors" :key="(e.path ?? e.part ?? '') + e.code">{{ e.message }}</li>
        </ul>
        <p v-if="session.problem.code === 'CAMERA_PARAMETERS_UNRESOLVED'" class="banner__hint">
          The highlighted fields could not be read from the photo. Please fill them in above.
        </p>
      </div>
    </div>

    <div class="actions">
      <RouterLink to="/" class="btn btn-secondary btn-lg"><AppIcon name="arrow-left" :size="16" /> Back</RouterLink>
      <button
        type="button"
        class="btn btn-primary btn-lg"
        :disabled="!session.canGenerate || session.loading"
        :title="session.canGenerate ? undefined : 'Select at least one turbine on the map'"
        @click="generate"
      >
        {{ session.loading ? 'Generating…' : 'Generate preview' }}
        <AppIcon v-if="!session.loading" name="arrow-right" :size="16" />
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
  min-height: 520px;
}
.side {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.banner {
  display: flex;
  gap: 12px;
  margin-top: 20px;
  padding: 14px 16px;
  border-radius: var(--radius);
  background: #fdecea;
  color: #7a1f17;
  font-size: 14px;
  line-height: 1.5;
}
.banner svg {
  flex: none;
  margin-top: 2px;
}
.banner ul {
  margin: 6px 0 0;
  padding-left: 18px;
}
.banner__hint {
  margin-top: 4px;
}
.actions {
  display: flex;
  justify-content: space-between;
  margin-top: 20px;
}
@media (max-width: 960px) {
  .layout {
    grid-template-columns: 1fr;
  }
}
</style>
