<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import AppIcon from '../components/AppIcon.vue'
import CompareSlider from '../components/preview/CompareSlider.vue'
import { useSessionStore } from '../stores/session'
import { downloadPreviewImage } from '../lib/exportImage'

const session = useSessionStore()
const downloading = ref(false)
const downloadError = ref<string | null>(null)

onMounted(() => {
  // e.g. after a reload or when turbines changed since the last calculation
  if (!session.preview && !session.previewLoading) session.runPreview()
})

const warning = computed(() => {
  const p = session.preview
  if (!p || p.outOfViewCount === 0) return null
  const one = p.outOfViewCount === 1
  return `Note: ${p.outOfViewCount} of ${p.totalCount} selected turbines ${one ? 'is' : 'are'} outside your camera’s field of view.`
})

async function download() {
  if (!session.photo || !session.preview) return
  downloading.value = true
  downloadError.value = null
  try {
    await downloadPreviewImage(session.photo, session.preview.outlines)
  } catch {
    downloadError.value = 'The image could not be exported.'
  } finally {
    downloading.value = false
  }
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
        {{ warning }}
      </div>

      <div v-if="session.previewLoading || !session.preview" class="loading">Calculating turbine outlines…</div>
      <CompareSlider v-else-if="session.photo" :photo="session.photo" :outlines="session.preview.outlines" />

      <p class="note">
        <AppIcon name="info" :size="16" />
        Geometric approximation only. Foreground trees, terrain, or buildings may still obstruct the real view.
      </p>

      <p v-if="downloadError" class="error" role="alert">{{ downloadError }}</p>

      <div class="actions">
        <RouterLink to="/check" class="btn btn-secondary"><AppIcon name="arrow-left" :size="16" /> Adjust turbines</RouterLink>
        <button type="button" class="btn" disabled title="Coming soon">Calibrate horizon (coming soon)</button>
        <button
          type="button"
          class="btn btn-primary actions__download"
          :disabled="!session.preview || downloading"
          @click="download"
        >
          <AppIcon name="download" :size="18" /> {{ downloading ? 'Preparing…' : 'Download image' }}
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
.loading {
  display: grid;
  place-items: center;
  aspect-ratio: 16 / 10;
  border-radius: var(--radius-lg);
  background: var(--surface-muted);
  color: var(--ink-500);
  animation: pulse 1.2s ease-in-out infinite;
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
.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 4px;
}
.actions__download {
  margin-left: auto;
}
.error {
  color: var(--danger);
  font-size: 14px;
}
@keyframes pulse {
  50% {
    opacity: 0.6;
  }
}
</style>
