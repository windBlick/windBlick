<script setup>
import { ref, reactive } from 'vue'
import AppHeader from '@/components/layout/AppHeader.vue'
import StepIndicator from '@/components/layout/StepIndicator.vue'
import OnboardingModal from '@/components/onboarding/OnboardingModal.vue'
import PhotoDropzone from '@/components/step1-upload/PhotoDropzone.vue'
import PhotoTipsModal from '@/components/step1-upload/PhotoTipsModal.vue'

const currentStep = ref(1)
const showOnboarding = ref(false)
const showPhotoTips = ref(false)

const photoFile = ref(null)
const photoPreviewUrl = ref('')

const cameraForm = reactive({
  latitude_deg: '',
  longitude_deg: '',
  elevation_m: '',
  heading_deg: '',
  pitch_deg: '',
  roll_deg: '',
  horizontal_fov_deg: '',
})

const turbines = ref([])
const resultImageUrl = ref('')
const backendWarnings = ref([])

function onFileSelected(file) {
  if (photoPreviewUrl.value) URL.revokeObjectURL(photoPreviewUrl.value)
  photoFile.value = file
  photoPreviewUrl.value = URL.createObjectURL(file)
}

function onClearFile() {
  if (photoPreviewUrl.value) URL.revokeObjectURL(photoPreviewUrl.value)
  photoFile.value = null
  photoPreviewUrl.value = ''
}
</script>

<template>
  <div class="min-h-screen bg-[#F8FAFC] text-slate-900">
    <AppHeader @open-onboarding="showOnboarding = true" />
    <StepIndicator :current-step="currentStep" />

    <main class="mx-auto max-w-6xl px-6 pb-16">
      <PhotoDropzone
        v-if="currentStep === 1"
        :photo-file="photoFile"
        :photo-preview-url="photoPreviewUrl"
        @file-selected="onFileSelected"
        @clear-file="onClearFile"
        @open-tips="showPhotoTips = true"
        @next-step="currentStep = 2"
      />

      <div v-else-if="currentStep === 2" class="rounded-2xl border border-slate-200 bg-white p-8 text-center shadow-sm">
        <p class="font-semibold text-[#14532D]">Step 2 ready to plug in ({{ photoFile?.name }})</p>
        <button
          type="button"
          class="mt-4 rounded-xl bg-[#9FD3B0]/35 px-4 py-2 text-sm font-semibold text-[#14532D]"
          @click="currentStep = 1"
        >
          ← Back
        </button>
      </div>
    </main>

    <OnboardingModal :is-open="showOnboarding" @close="showOnboarding = false" />
    <PhotoTipsModal :is-open="showPhotoTips" @close="showPhotoTips = false" />
  </div>
</template>