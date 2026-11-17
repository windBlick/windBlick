<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import AppIcon from '../components/AppIcon.vue'
import PhotoTipsModal from '../components/tips/PhotoTipsModal.vue'
import { useSessionStore } from '../stores/session'

const session = useSessionStore()
const router = useRouter()

const fileInput = ref<HTMLInputElement | null>(null)
const dragging = ref(false)
const loading = ref(false)
const error = ref<string | null>(null)
const showHelp = ref(false)

// Accepted by POST /api/v0/visualizations (docs/api-contract.md §2)
const ACCEPTED = ['image/jpeg', 'image/png']
const MAX_BYTES = 20 * 1024 * 1024

async function handleFile(file: File | undefined) {
  if (!file) return
  error.value = null
  if (!ACCEPTED.includes(file.type)) {
    error.value = 'Please choose a JPG or PNG file.'
    return
  }
  if (file.size > MAX_BYTES) {
    error.value = 'This photo is larger than 20 MB. Please choose a smaller file.'
    return
  }
  loading.value = true
  try {
    await session.loadPhoto(file)
    router.push({ name: 'check' })
  } catch {
    error.value = 'This photo could not be read. Please try another file.'
  } finally {
    loading.value = false
  }
}

function onDrop(e: DragEvent) {
  dragging.value = false
  handleFile(e.dataTransfer?.files[0])
}

function onPick(e: Event) {
  const input = e.target as HTMLInputElement
  handleFile(input.files?.[0])
  input.value = ''
}

async function useSample() {
  await session.loadSample()
  router.push({ name: 'check' })
}
</script>

<template>
  <section>
    <h1 class="page-title">Where would planned wind turbines appear in your photo?</h1>
    <p class="page-lead">
      Upload a photo of your surroundings. The application shows the calculated position and size of planned wind
      turbines as outlines.
    </p>

    <div class="layout">
      <div
        class="drop"
        :class="{ 'drop--active': dragging, 'drop--loading': loading }"
        @dragenter.prevent="dragging = true"
        @dragover.prevent="dragging = true"
        @dragleave.prevent="dragging = false"
        @drop.prevent="onDrop"
      >
        <AppIcon class="drop__icon" name="upload" :size="32" />
        <h2 class="drop__title">{{ loading ? 'Reading photo…' : 'Drop your photo here' }}</h2>
        <p class="drop__or">or</p>
        <button type="button" class="btn btn-primary" :disabled="loading" @click="fileInput?.click()">
          Select photo
        </button>
        <input
          ref="fileInput"
          class="visually-hidden"
          type="file"
          accept=".jpg,.jpeg,.png,image/jpeg,image/png"
          @change="onPick"
        />

        <p v-if="error" class="drop__error" role="alert">{{ error }}</p>

        <div class="drop__hints">
          <p>Use the original file with saved location data.</p>
          <p>JPG or PNG, up to 20 MB</p>
        </div>

        <button type="button" class="btn btn-outline" aria-haspopup="dialog" @click="showHelp = true">
          Which photos are suitable?
        </button>

        <button type="button" class="drop__sample" @click="useSample">No photo at hand? Try a sample photo</button>
      </div>

      <aside class="card example">
        <h2 class="example__title">Example of a geometric preview</h2>
        <div class="example__img">
          <img src="/sample/landscape.svg" alt="Sample landscape with two turbine markers" />
          <span class="pin pin--1"><span class="pin__head">i</span><span class="pin__label">WT 01</span></span>
          <span class="pin pin--2"><span class="pin__head">i</span><span class="pin__label">WT 02</span></span>
        </div>
        <p class="example__note">
          Not a photorealistic visualization. Buildings and trees may obstruct the actual view.
        </p>
      </aside>
    </div>

    <p class="privacy">Location data is used to determine where the photo was taken.</p>
    <a class="privacy__link" href="#" @click.prevent>Data processing</a>
    <PhotoTipsModal v-if="showHelp" @close="showHelp = false" />
  </section>
</template>

<style scoped>
.layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 352px;
  gap: 24px;
  margin-top: 28px;
}
.drop {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 44px 48px 48px;
  border: 2px dashed var(--border-strong);
  border-radius: var(--radius-lg);
  background: var(--surface);
  text-align: center;
  transition: border-color 0.15s, background-color 0.15s;
}
.drop--active {
  border-color: var(--green-600);
  background: var(--green-50);
}
.drop--loading {
  opacity: 0.75;
}
.drop__icon {
  color: var(--info-blue);
}
.drop__title {
  margin-top: 20px;
  font-size: 24px;
  font-weight: 600;
}
.drop__or {
  margin: 20px 0 16px;
  font-size: 17px;
  color: var(--ink-700);
}
.drop__error {
  margin-top: 16px;
  color: var(--danger);
  font-size: 14px;
}
.drop__hints {
  align-self: stretch;
  margin: 32px 0 24px;
  text-align: left;
  font-size: 16px;
  line-height: 2;
  color: var(--ink-700);
}
.drop__sample {
  margin-top: 20px;
  border: 0;
  background: none;
  color: var(--green-800);
  font-size: 14px;
  text-decoration: underline;
  cursor: pointer;
}
.example {
  padding: 24px;
  align-self: start;
}
.example__title {
  font-size: 20px;
  font-weight: 600;
  line-height: 1.5;
}
.example__img {
  position: relative;
  margin-top: 16px;
  aspect-ratio: 304 / 202;
  border-radius: var(--radius-sm);
  overflow: hidden;
}
.example__img img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.pin {
  position: absolute;
  bottom: 14%;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.pin::before {
  content: '';
  order: 1;
  width: 4px;
  height: 64px;
  background: #fff;
  border: 1px solid var(--ink-700);
}
.pin__head {
  order: 0;
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  border-radius: 50%;
  border: 2px solid var(--ink-700);
  background: rgba(255, 255, 255, 0.85);
  font-weight: 700;
  font-size: 14px;
}
.pin__label {
  order: 2;
  padding: 2px 8px;
  border-radius: 3px;
  background: #fff;
  font-size: 15px;
  font-weight: 600;
}
.pin--1 {
  left: 18%;
}
.pin--2 {
  left: 48%;
  bottom: 10%;
}
.pin--2 .pin__head {
  width: 46px;
  height: 46px;
  border-color: var(--info-blue);
  color: var(--info-blue);
}
.pin--2::before {
  height: 74px;
  border-color: var(--info-blue);
}
.pin--2 .pin__label {
  background: var(--info-blue);
  color: #fff;
}
.example__note {
  margin-top: 24px;
  font-size: 16px;
  line-height: 1.5;
  color: var(--ink-700);
}
.privacy {
  margin-top: 32px;
  font-size: 16px;
  color: var(--ink-700);
}
.privacy__link {
  display: inline-block;
  margin-top: 16px;
  font-size: 16px;
}
@media (max-width: 900px) {
  .layout {
    grid-template-columns: 1fr;
  }
  .drop {
    padding: 32px 20px;
  }
  .page-title {
    font-size: 26px;
  }
}
</style>
