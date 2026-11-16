<script setup>
import { ref } from 'vue'
import AppHeader from '@/components/layout/AppHeader.vue'
import StepIndicator from '@/components/layout/StepIndicator.vue'
import OnboardingModal from '@/components/onboarding/OnboardingModal.vue'

// --- UI & Navigation State ---
const currentStep = ref(1)
const showOnboarding = ref(false)
const showPhotoTips = ref(false)
const isLoading = ref(false)

// --- Step 1: Foto State ---
const photoFile = ref(null)
const photoPreviewUrl = ref('')

// --- Step 2: Kamera-Overrides & Turbinen State ---
const camera = ref({
  latitude_deg: '',
  longitude_deg: '',
  elevation_m: '',
  heading_deg: '',
  pitch_deg: '',
  roll_deg: '',
  horizontal_fov_deg: ''
})
const turbines = ref([])

// --- Step 3: Ergebnis State ---
const simulatedImageUrl = ref('/dummy.png')

// --- Hilfsfunktionen für den Test-Flow ---
function handleDummyUpload(event) {
  const file = event.target.files?.[0]
  if (!file) return
  if (photoPreviewUrl.value) URL.revokeObjectURL(photoPreviewUrl.value)
  photoFile.value = file
  photoPreviewUrl.value = URL.createObjectURL(file)
}

function clearPhoto() {
  if (photoPreviewUrl.value) URL.revokeObjectURL(photoPreviewUrl.value)
  photoFile.value = null
  photoPreviewUrl.value = ''
}

function runMockPreview() {
  isLoading.value = true
  setTimeout(() => {
    isLoading.value = false
    currentStep.value = 3
  }, 600)
}
</script>

<template>
  <div class="min-h-screen bg-[#F8FAFC] text-slate-900">
    <!-- Header & Fortschrittsbalken -->
    <AppHeader @open-onboarding="showOnboarding = true" />
    <StepIndicator :current-step="currentStep" />

    <!-- Onboarding Modal -->
    <OnboardingModal
      :is-open="showOnboarding"
      @close="showOnboarding = false"
    />

    <!-- Hauptbereich -->
    <main class="mx-auto max-w-6xl px-4 pb-16 sm:px-6">
      
      <!-- SCHRITT 1: Platzhalter bis PhotoDropzone.vue steht -->
      <section v-if="currentStep === 1" class="mx-auto max-w-2xl">
        <div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 class="text-lg font-semibold text-slate-900">Step 1: Upload landscape photo</h2>
          <p class="mt-1 text-sm text-slate-600">
            Platzhalter-Card für <code class="rounded bg-slate-100 px-1.5 py-0.5 text-xs">PhotoDropzone.vue</code>.
          </p>

          <div class="mt-5 rounded-xl border-2 border-dashed border-slate-300 bg-slate-50 p-6 text-center">
            <input
              type="file"
              accept="image/jpeg,image/png"
              class="mx-auto block text-sm text-slate-600 file:mr-4 file:rounded-xl file:border-0 file:bg-[#9FD3B0]/40 file:px-4 file:py-2 file:text-sm file:font-semibold file:text-[#14532D] hover:file:bg-[#9FD3B0]/60"
              @change="handleDummyUpload"
            />
            <img
              v-if="photoPreviewUrl"
              :src="photoPreviewUrl"
              alt="Preview"
              class="mx-auto mt-4 max-h-48 rounded-xl object-contain"
            />
          </div>

          <div class="mt-6 flex items-center justify-between">
            <button
              v-if="photoFile"
              type="button"
              class="text-sm font-medium text-slate-500 hover:text-slate-800"
              @click="clearPhoto"
            >
              Remove photo
            </button>
            <span v-else />

            <button
              type="button"
              class="rounded-xl bg-[#14532D] px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-[#14532D]/90"
              @click="currentStep = 2"
            >
              Next: Place turbines →
            </button>
          </div>
        </div>
      </section>

      <!-- SCHRITT 2: 12-Spalten-Raster für Karte & Formulare -->
      <section v-else-if="currentStep === 2" class="space-y-6">
        <div class="grid grid-cols-1 items-start gap-6 lg:grid-cols-12">
          <!-- Linke Spalte (7/12): Platzhalter für TurbineMap.vue -->
          <div class="min-w-0 lg:col-span-7">
            <div class="flex h-[480px] flex-col items-center justify-center rounded-2xl border border-slate-200 bg-white p-6 text-center shadow-sm">
              <p class="font-semibold text-slate-800">Map Placeholder (TurbineMap.vue)</p>
              <p class="mt-1 text-sm text-slate-500">Hier kommt als Nächstes die Leaflet-Karte rein.</p>
            </div>
          </div>

          <!-- Rechte Spalte (5/12): Platzhalter für ManualCameraForm & TurbineForm -->
          <div class="min-w-0 space-y-4 lg:col-span-5">
            <div class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <p class="font-semibold text-slate-800">Camera & Perspective (ManualCameraForm.vue)</p>
              <p class="mt-1 text-sm text-slate-500">Optionale Kamera-Overrides (EXIF-Fallback).</p>
            </div>

            <div class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <p class="font-semibold text-slate-800">Wind Turbines (TurbineForm.vue)</p>
              <p class="mt-1 text-sm text-slate-500">Liste der platzierten Windräder.</p>
            </div>
          </div>
        </div>

        <!-- Feste Aktionsleiste unten -->
        <div class="flex items-center justify-between border-t border-slate-200 pt-4">
          <button
            type="button"
            class="rounded-xl bg-[#9FD3B0]/35 px-5 py-2.5 text-sm font-semibold text-[#14532D] transition hover:bg-[#9FD3B0]/50"
            @click="currentStep = 1"
          >
            ← Back
          </button>

          <button
            type="button"
            :disabled="isLoading"
            class="rounded-xl bg-[#14532D] px-6 py-2.5 text-sm font-semibold text-white transition hover:bg-[#14532D]/90 disabled:opacity-50"
            @click="runMockPreview"
          >
            {{ isLoading ? 'Generating...' : 'Generate preview →' }}
          </button>
        </div>
      </section>

      <!-- SCHRITT 3: Platzhalter für ComparisonSlider.vue -->
      <section v-else-if="currentStep === 3" class="mx-auto max-w-4xl">
        <div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 class="text-lg font-semibold text-slate-900">Step 3: Comparison Preview</h2>
          <p class="mt-1 text-sm text-slate-600">
            Platzhalter für <code class="rounded bg-slate-100 px-1.5 py-0.5 text-xs">ComparisonSlider.vue</code>.
          </p>

          <div class="mt-4 overflow-hidden rounded-xl border border-slate-200 bg-slate-100">
            <img
              :src="photoPreviewUrl || simulatedImageUrl"
              alt="Result preview"
              class="mx-auto max-h-[420px] w-full object-contain"
            />
          </div>

          <div class="mt-6 flex items-center justify-between">
            <button
              type="button"
              class="rounded-xl bg-[#9FD3B0]/35 px-5 py-2.5 text-sm font-semibold text-[#14532D] transition hover:bg-[#9FD3B0]/50"
              @click="currentStep = 2"
            >
              ← Adjust turbines
            </button>
          </div>
        </div>
      </section>

    </main>
  </div>
</template>