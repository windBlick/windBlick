<script setup>
import { ref } from 'vue'
import AppHeader from '@/components/layout/AppHeader.vue'
import StepIndicator from '@/components/layout/StepIndicator.vue'
import StatusBanner from '@/components/layout/StatusBanner.vue'
import OnboardingModal from '@/components/onboarding/OnboardingModal.vue'
import PhotoDropzone from '@/components/step1-upload/PhotoDropzone.vue'
import ExamplePreview from '@/components/step1-upload/ExamplePreview.vue'

// ============================================================================
// UI & Workflow Navigation State
// ============================================================================
const currentStep = ref(1)
const showOnboarding = ref(false)
const showPhotoTips = ref(false)
const isLoading = ref(false)

// ============================================================================
// Global Error & Simulation Warning State (for StatusBanner.vue)
// ============================================================================
const errorTitle = ref('')
const errorMessage = ref('')
const validationErrors = ref([])
const warnings = ref([])

function clearError() {
  errorTitle.value = ''
  errorMessage.value = ''
  validationErrors.value = []
}

function goToStep(step) {
  clearError()
  currentStep.value = step
}

// ============================================================================
// Step 1: Photo Upload State
// ============================================================================
const photoFile = ref(null)
const photoPreviewUrl = ref('')

// ============================================================================
// Step 2: Camera Overrides & Turbines State
// ============================================================================
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

// ============================================================================
// Step 3: Simulation Result State (Mock until API contract is finalized)
// ============================================================================
const simulatedImageUrl = ref('/dummy.png')

// ============================================================================
// Step 1 Handlers (File Selection & Cleanup)
// ============================================================================
function handleFileSelected(file) {
  if (!file) return
  clearError()
  if (photoPreviewUrl.value) {
    URL.revokeObjectURL(photoPreviewUrl.value)
  }
  photoFile.value = file
  photoPreviewUrl.value = URL.createObjectURL(file)
}

function clearPhoto() {
  clearError()
  if (photoPreviewUrl.value) {
    URL.revokeObjectURL(photoPreviewUrl.value)
  }
  photoFile.value = null
  photoPreviewUrl.value = ''
}

// ============================================================================
// Step 2 -> Step 3 Mock Simulation Handler
// ============================================================================
function runMockPreview() {
  clearError()
  warnings.value = []
  isLoading.value = true

  setTimeout(() => {
    isLoading.value = false
    currentStep.value = 3
  }, 600)
}
</script>

<template>
  <div class="min-h-screen bg-[#F8FAFC] text-slate-900">
    <!-- Top Navigation & 3-Step Progress Bar -->
    <AppHeader @open-onboarding="showOnboarding = true" />
    <StepIndicator :current-step="currentStep" />

    <!-- Onboarding Modal (4 Slides) -->
    <OnboardingModal
      :is-open="showOnboarding"
      @close="showOnboarding = false"
    />

    <!-- Temporary Placeholder Modal until PhotoTipsModal.vue is created -->
    <div
      v-if="showPhotoTips"
      class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4 backdrop-blur-xs"
      @click.self="showPhotoTips = false"
    >
      <div class="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl">
        <div class="flex items-center justify-between">
          <h3 class="text-lg font-bold text-slate-900">Which photos are suitable?</h3>
          <button
            type="button"
            class="rounded-lg p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
            @click="showPhotoTips = false"
          >
            ✕
          </button>
        </div>
        <p class="mt-3 text-sm leading-relaxed text-slate-600">
          Placeholder for <code class="rounded bg-slate-100 px-1.5 py-0.5 text-xs">PhotoTipsModal.vue</code>.
          Use original smartphone JPG photos with intact GPS and compass metadata.
        </p>
        <div class="mt-5 flex justify-end">
          <button
            type="button"
            class="rounded-xl bg-[#14532D] px-4 py-2 text-sm font-semibold text-white"
            @click="showPhotoTips = false"
          >
            Got it
          </button>
        </div>
      </div>
    </div>

    <!-- Main Workflow Area -->
    <main class="mx-auto max-w-6xl px-4 pt-8 pb-16 sm:px-6">
      <!-- 1. Global Error Banner (shown above any active step when an error occurs) -->
      <div v-if="errorMessage || validationErrors.length > 0" class="mb-6">
        <StatusBanner
          variant="error"
          :title="errorTitle || 'Could not process request'"
          :message="errorMessage"
          :items="validationErrors"
          dismissible
          @dismiss="clearError"
        />
      </div>

      <!-- ====================================================================
           STEP 1: Photo Upload Dropzone & Side-by-Side Example Preview
           ==================================================================== -->
      <section v-if="currentStep === 1">
        <div class="grid grid-cols-1 items-stretch gap-6 lg:grid-cols-12">
          <!-- Left Column (7/12): PhotoDropzone -->
          <div class="min-w-0 lg:col-span-7">
            <PhotoDropzone
              :photo-file="photoFile"
              :photo-preview-url="photoPreviewUrl"
              @file-selected="handleFileSelected"
              @clear-file="clearPhoto"
              @open-tips="showPhotoTips = true"
              @next-step="goToStep(2)"
            />
          </div>

          <!-- Right Column (5/12): ExamplePreview (equal height) -->
          <div class="min-w-0 lg:col-span-5">
            <ExamplePreview />
          </div>
        </div>
      </section>

      <!-- ====================================================================
           STEP 2: Map & Turbine Placement (Placeholders for Step 2 Cards)
           ==================================================================== -->
      <section v-else-if="currentStep === 2" class="space-y-6">
        <div class="grid grid-cols-1 items-start gap-6 lg:grid-cols-12">
          <!-- Left Column (7/12): Map Placeholder -->
          <div class="min-w-0 lg:col-span-7">
            <div class="flex h-[480px] flex-col items-center justify-center rounded-2xl border border-slate-200 bg-white p-6 text-center shadow-sm">
              <p class="font-semibold text-slate-800">Map Placeholder (TurbineMap.vue)</p>
              <p class="mt-1 text-sm text-slate-500">Leaflet map and field-of-view cone will go here.</p>
            </div>
          </div>

          <!-- Right Column (5/12): Camera & Turbines Form Placeholders -->
          <div class="min-w-0 space-y-4 lg:col-span-5">
            <div class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <p class="font-semibold text-slate-800">Camera & Perspective (ManualCameraForm.vue)</p>
              <p class="mt-1 text-sm text-slate-500">Optional camera overrides (EXIF fallback).</p>
            </div>

            <div class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <p class="font-semibold text-slate-800">Wind Turbines (TurbineForm.vue)</p>
              <p class="mt-1 text-sm text-slate-500">List of placed wind turbines.</p>
            </div>
          </div>
        </div>

        <!-- Bottom Action Bar -->
        <div class="flex items-center justify-between border-t border-slate-200 pt-4">
          <button
            type="button"
            class="rounded-xl bg-[#9FD3B0]/35 px-5 py-2.5 text-sm font-semibold text-[#14532D] transition hover:bg-[#9FD3B0]/50"
            @click="goToStep(1)"
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

      <!-- ====================================================================
           STEP 3: Result Comparison (Placeholder for ComparisonSlider.vue)
           ==================================================================== -->
      <section v-else-if="currentStep === 3" class="mx-auto max-w-4xl space-y-6">
        <!-- 2. Simulation Warnings Banner (e.g. turbines outside camera frame) -->
        <StatusBanner
          v-if="warnings.length > 0"
          variant="warning"
          title="Simulation notes"
          :items="warnings"
        />

        <div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 class="text-lg font-semibold text-slate-900">Step 3: Comparison Preview</h2>
          <p class="mt-1 text-sm text-slate-600">
            Placeholder for <code class="rounded bg-slate-100 px-1.5 py-0.5 text-xs">ComparisonSlider.vue</code>.
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
              @click="goToStep(2)"
            >
              ← Adjust turbines
            </button>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>