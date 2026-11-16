<script setup>
import { ref, computed } from 'vue'

// ============================================================================
// Props & Emits
// ============================================================================
const props = defineProps({
  photoFile: {
    type: Object,
    default: null
  },
  photoPreviewUrl: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['file-selected', 'clear-file', 'open-tips', 'next-step'])

// ============================================================================
// Component State & Validation Constants
// ============================================================================
const MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024 // 20 MB
const ALLOWED_MIME_TYPES = ['image/jpeg']
const ALLOWED_EXTENSIONS = ['.jpg', '.jpeg']

const fileInputRef = ref(null)
const isDragging = ref(false)
const errorMessage = ref('')

const formattedFileSize = computed(() => {
  if (!props.photoFile?.size) return ''
  const sizeInMb = props.photoFile.size / (1024 * 1024)
  return `${sizeInMb.toFixed(2)} MB`
})

// ============================================================================
// File Selection, Drag & Drop, and Validation Handlers
// ============================================================================
function triggerFileInput() {
  errorMessage.value = ''
  fileInputRef.value?.click()
}

function handleInputChange(event) {
  const file = event.target.files?.[0]
  if (file) {
    validateAndEmit(file)
  }
  // Reset input value so selecting the same file again still triggers @change
  event.target.value = ''
}

function handleDragOver() {
  isDragging.value = true
}

function handleDragLeave() {
  isDragging.value = false
}

function handleDrop(event) {
  isDragging.value = false
  const file = event.dataTransfer?.files?.[0]
  if (file) {
    validateAndEmit(file)
  }
}

function validateAndEmit(file) {
  errorMessage.value = ''

  const fileNameLower = file.name.toLowerCase()
  const hasValidExtension = ALLOWED_EXTENSIONS.some((ext) => fileNameLower.endsWith(ext))
  const hasValidMime = ALLOWED_MIME_TYPES.includes(file.type)

  if (!hasValidMime && !hasValidExtension) {
    errorMessage.value = 'Invalid file format. For this prototype, please upload an original JPG or JPEG photo.'
    return
  }

  if (file.size > MAX_FILE_SIZE_BYTES) {
    errorMessage.value = 'File is too large. Please select a photo smaller than 20 MB.'
    return
  }

  emit('file-selected', file)
}

function handleRemovePhoto() {
  errorMessage.value = ''
  emit('clear-file')
}
</script>

<template>
  <div class="mx-auto w-full max-w-[680px]">
    <!-- Hidden Native File Input -->
    <input
      ref="fileInputRef"
      type="file"
      accept=".jpg,.jpeg,image/jpeg"
      class="hidden"
      @change="handleInputChange"
    />

    <!-- ======================================================================
         STATE 1: Empty Dropzone (Matches Figma Upload Card)
         ====================================================================== -->
    <div
      v-if="!photoPreviewUrl"
      class="rounded-2xl border-2 border-dashed bg-white px-8 py-10 transition-colors"
      :class="
        isDragging
          ? 'border-[#14532D] bg-[#9FD3B0]/15'
          : 'border-slate-300 hover:border-slate-400'
      "
      @dragover.prevent="handleDragOver"
      @dragleave.prevent="handleDragLeave"
      @drop.prevent="handleDrop"
    >
      <!-- Centered Upload Icon, Heading & Primary Button -->
      <div class="flex flex-col items-center text-center">
        <!-- Upload Tray Icon -->
        <svg
          class="h-7 w-7 text-blue-600"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.8"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2M12 4v11m0-11L8 8m4-4l4 4"
          />
        </svg>

        <h2 class="mt-4 text-2xl font-bold tracking-tight text-slate-900">
          Drop your photo here
        </h2>

        <p class="mt-2.5 text-sm text-slate-500">
          or
        </p>

        <button
          type="button"
          class="mt-3 rounded-xl bg-[#14532D] px-6 py-2.5 text-sm font-semibold text-white shadow-xs transition hover:bg-[#14532D]/90"
          @click="triggerFileInput"
        >
          Select photo
        </button>
      </div>

      <!-- Validation Error Alert (Only shown on invalid file type or size) -->
      <div
        v-if="errorMessage"
        role="alert"
        class="mt-6 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
      >
        {{ errorMessage }}
      </div>

      <!-- Left-Aligned File Requirements Note -->
      <div class="mt-7 space-y-2 text-left text-sm text-slate-600">
        <p>Use the original file with saved location data.</p>
        <p>For this prototype: JPG or JPEG</p>
      </div>

      <!-- Centered Help Trigger Button -->
      <div class="mt-7 flex justify-center">
        <button
          type="button"
          class="rounded-xl border border-[#9FD3B0] bg-white px-5 py-2.5 text-sm font-medium text-slate-800 transition hover:bg-[#9FD3B0]/15"
          @click="$emit('open-tips')"
        >
          Which photos are suitable?
        </button>
      </div>
    </div>

    <!-- ======================================================================
         STATE 2: Photo Selected (Preview, File Metadata & Next Step Action)
         ====================================================================== -->
    <div
      v-else
      class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"
    >
      <!-- Image Preview Container -->
      <div class="overflow-hidden rounded-xl border border-slate-200 bg-slate-50">
        <img
          :src="photoPreviewUrl"
          :alt="photoFile?.name || 'Uploaded landscape preview'"
          class="mx-auto max-h-[340px] w-full object-contain"
        />
      </div>

      <!-- File Info & Remove Action -->
      <div class="mt-4 flex flex-wrap items-center justify-between gap-3 rounded-xl bg-slate-50 px-4 py-3">
        <div class="min-w-0">
          <p class="truncate text-sm font-semibold text-slate-900">
            {{ photoFile?.name }}
          </p>
          <p class="text-xs text-slate-500">
            {{ formattedFileSize }} · Original EXIF metadata preserved
          </p>
        </div>

        <button
          type="button"
          class="shrink-0 rounded-lg px-3 py-1.5 text-sm font-medium text-red-600 transition hover:bg-red-50"
          @click="handleRemovePhoto"
        >
          Remove photo
        </button>
      </div>

      <!-- Card Footer Actions -->
      <div class="mt-6 flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 pt-4">
        <button
          type="button"
          class="rounded-xl border border-[#9FD3B0] bg-white px-4 py-2.5 text-sm font-medium text-slate-800 transition hover:bg-[#9FD3B0]/15"
          @click="$emit('open-tips')"
        >
          Which photos are suitable?
        </button>

        <button
          type="button"
          class="inline-flex items-center gap-1.5 rounded-xl bg-[#14532D] px-6 py-2.5 text-sm font-semibold text-white transition hover:bg-[#14532D]/90"
          @click="$emit('next-step')"
        >
          <span>Next: Place turbines</span>
          <svg class="h-4 w-4" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4 10h12m-4-4l4 4-4 4" />
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>