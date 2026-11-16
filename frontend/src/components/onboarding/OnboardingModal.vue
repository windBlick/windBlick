<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  isOpen: {
    type: Boolean,
    required: true
  }
})

const emit = defineEmits(['close'])

const activeSlide = ref(0)
const dontShowAgain = ref(false)

// Falls euer Logo in public/ als logo.png statt logo.svg liegt, greift der Fallback automatisch
const logoUrl = ref('/logo.svg')
function handleLogoError() {
  if (logoUrl.value !== '/logo.png') {
    logoUrl.value = '/logo.jpg'
  }
}

const slides = [
  {
    type: 'intro',
    title: 'Visualize planned wind turbines',
    description:
      'WindBlick helps you understand the scale of planned wind turbines from your own perspective.',
    note:
      'Note: This tool provides a geometric orientation, not a photorealistic visualization.'
  },
  {
    type: 'step',
    image: '/dummy.png',
    title: '1. Upload an original smartphone photo',
    description:
      'To calculate the exact perspective, WindBlick reads the hidden GPS location and compass data inside your original JPG file—avoid images sent via WhatsApp.'
  },
  {
    type: 'step',
    image: '/dummy.png',
    title: '2. Place turbines & set dimensions',
    description:
      'Click on the map to set the planned turbine location, verify your viewing direction, and enter hub height and rotor size.'
  },
  {
    type: 'step',
    image: '/dummy.png',
    title: '3. Compare before and after',
    description:
      'Drag the slider to compare your original view with the calculated turbine outlines. Foreground trees or buildings may still obstruct the real view.'
  }
]

const currentSlide = computed(() => slides[activeSlide.value])
const isLastSlide = computed(() => activeSlide.value === slides.length - 1)

watch(
  () => props.isOpen,
  (open) => {
    if (open) {
      activeSlide.value = 0
    }
  }
)

function nextSlide() {
  if (!isLastSlide.value) {
    activeSlide.value++
  } else {
    closeModal()
  }
}

function prevSlide() {
  if (activeSlide.value > 0) {
    activeSlide.value--
  }
}

function closeModal() {
  if (dontShowAgain.value) {
    localStorage.setItem('windblick_hide_onboarding', 'true')
  }
  activeSlide.value = 0
  emit('close')
}
</script>

<template>
  <div
    v-if="isOpen"
    class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4 backdrop-blur-xs"
    @click.self="closeModal"
  >
    <!-- Card-Scale 640px x 560px -->
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="onboarding-title"
      class="flex h-[560px] w-full max-w-[640px] flex-col overflow-hidden rounded-2xl bg-white shadow-2xl"
    >
      <div class="flex h-12 shrink-0 items-center justify-end px-5 pt-2">
        <button
          type="button"
          aria-label="Close onboarding"
          class="rounded-lg p-1.5 text-slate-400 transition hover:bg-slate-100 hover:text-slate-600"
          @click="closeModal"
        >
          <svg class="h-5 w-5" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8">
            <path stroke-linecap="round" stroke-linejoin="round" d="M5 5l10 10M15 5L5 15" />
          </svg>
        </button>
      </div>


      <div class="flex flex-1 flex-col overflow-hidden px-10">
        <!-- SLIDE 1: Logo + Titel + Info-Box -->
        <template v-if="currentSlide.type === 'intro'">
          <div class="flex h-[155px] shrink-0 items-center justify-center">
            <img
              :src="logoUrl"
              alt="WindBlick Visualization"
              class="h-36 w-auto object-contain"
              @error="handleLogoError"
            />
          </div>

          <h2
            id="onboarding-title"
            class="mt-2 text-center text-[25px] font-bold tracking-tight text-slate-900"
          >
            {{ currentSlide.title }}
          </h2>

          <p class="mx-auto mt-3 max-w-[440px] text-center text-[15px] leading-relaxed text-slate-500">
            {{ currentSlide.description }}
          </p>

          <div class="mt-7 flex items-center gap-3.5 rounded-xl bg-slate-50 px-5 py-4 text-left">
            <svg
              class="h-5 w-5 shrink-0 text-[#14532D]"
              viewBox="0 0 20 20"
              fill="none"
              stroke="currentColor"
              stroke-width="1.8"
            >
              <circle cx="10" cy="10" r="8" />
              <path stroke-linecap="round" d="M10 9v4.5M10 6.5h.01" />
            </svg>
            <p class="text-[13.5px] leading-snug text-slate-600">
              {{ currentSlide.note }}
            </p>
          </div>
        </template>

        <template v-else>
          <div class="h-[225px] w-full shrink-0 overflow-hidden rounded-xl border border-slate-200 bg-slate-50">
            <img
              :src="currentSlide.image"
              :alt="currentSlide.title"
              class="h-full w-full object-cover"
            />
          </div>

          <h2
            id="onboarding-title"
            class="mt-7 text-center text-[25px] font-bold tracking-tight text-slate-900"
          >
            {{ currentSlide.title }}
          </h2>

          <p class="mx-auto mt-3 max-w-[460px] text-center text-[15px] leading-relaxed text-slate-500">
            {{ currentSlide.description }}
          </p>
        </template>
      </div>

     
      <div class="grid h-[76px] shrink-0 grid-cols-3 items-center border-t border-slate-100 px-9">
        <div class="justify-self-start">
          <button
            v-if="!isLastSlide"
            type="button"
            class="text-sm font-medium text-slate-600 transition hover:text-slate-900"
            @click="closeModal"
          >
            Skip intro
          </button>

          <label
            v-else
            class="flex cursor-pointer items-center gap-2.5 text-sm font-medium text-slate-600 select-none"
          >
            <input
              v-model="dontShowAgain"
              type="checkbox"
              class="h-4 w-4 rounded border-slate-300 accent-[#14532D]"
            />
            <span>Don't show again</span>
          </label>
        </div>

        <div class="flex items-center gap-2 justify-self-center">
          <button
            v-for="(_, index) in slides"
            :key="index"
            type="button"
            :aria-label="`Go to slide ${index + 1}`"
            class="h-2 w-2 rounded-full transition-colors"
            :class="activeSlide === index ? 'bg-[#14532D]' : 'bg-[#9FD3B0] hover:bg-[#14532D]/50'"
            @click="activeSlide = index"
          />
        </div>

        <div class="flex items-center gap-2.5 justify-self-end">
          <button
            v-if="activeSlide > 0"
            type="button"
            class="rounded-xl bg-[#E3F1E8] px-5 py-2.5 text-sm font-semibold text-[#14532D] transition hover:bg-[#9FD3B0]/60"
            @click="prevSlide"
          >
            Back
          </button>

          <button
            type="button"
            class="inline-flex items-center gap-1.5 rounded-xl bg-[#14532D] px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-[#14532D]/90"
            @click="nextSlide"
          >
            <span>{{ isLastSlide ? 'Start upload' : 'Next' }}</span>
            <svg
              v-if="!isLastSlide"
              class="h-4 w-4"
              viewBox="0 0 20 20"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <path stroke-linecap="round" stroke-linejoin="round" d="M4 10h12m-4-4l4 4-4 4" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>