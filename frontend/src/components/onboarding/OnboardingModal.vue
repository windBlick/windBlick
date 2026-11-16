<script setup>
import { ref, computed, watch } from 'vue'

// ============================================================================
// Props & Emits
// ============================================================================
const props = defineProps({
  isOpen: {
    type: Boolean,
    required: true
  }
})

const emit = defineEmits(['close'])

// ============================================================================
// Component State
// ============================================================================
const activeSlide = ref(0)
const transitionName = ref('slide-next')
const dontShowAgain = ref(false)

// Fallback to /logo.png if /logo.svg is not present in public/
const logoUrl = ref('/logo.svg')
function handleLogoError() {
  if (logoUrl.value !== '/logo.png') {
    logoUrl.value = '/logo.png'
  }
}

// ============================================================================
// Slide Content Configuration (Slides 1–4)
// Replace /dummy.png with final exported assets once ready
// ============================================================================
const slides = [
  // Slide 1: Introduction & Accuracy Note
  {
    type: 'intro',
    title: 'Visualize planned wind turbines',
    description:
      'WindBlick helps you understand the scale of planned wind turbines from your own perspective.',
    note:
      'Note: This tool provides a geometric orientation, not a photorealistic visualization.'
  },
  // Slide 2: Step 1 — Photo Upload
  {
    type: 'step',
    image: '/dummy.png',
    title: '1. Upload an original smartphone photo',
    description:
      'To calculate the exact perspective, WindBlick reads the hidden GPS location and compass data inside your original JPG file—avoid images sent via WhatsApp.'
  },
  // Slide 3: Step 2 — Map & Turbine Placement
  {
    type: 'step',
    image: '/dummy.png',
    title: '2. Place turbines & set dimensions',
    description:
      'Click on the map to set the planned turbine location, verify your viewing direction, and enter hub height and rotor size.'
  },
  // Slide 4: Step 3 — Before/After Comparison
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

// ============================================================================
// Navigation & Modal Lifecycle
// ============================================================================
watch(
  () => props.isOpen,
  (open) => {
    if (open) {
      transitionName.value = 'slide-next'
      activeSlide.value = 0
    }
  }
)

function goToSlide(index) {
  if (index === activeSlide.value || index < 0 || index >= slides.length) return
  transitionName.value = index > activeSlide.value ? 'slide-next' : 'slide-prev'
  activeSlide.value = index
}

function nextSlide() {
  if (!isLastSlide.value) {
    goToSlide(activeSlide.value + 1)
  } else {
    closeModal()
  }
}

function prevSlide() {
  if (activeSlide.value > 0) {
    goToSlide(activeSlide.value - 1)
  }
}

function closeModal() {
  if (dontShowAgain.value) {
    localStorage.setItem('windblick_hide_onboarding', 'true')
  }
  emit('close')
}
</script>

<template>
  <!-- Modal Backdrop Overlay -->
  <Transition name="modal">
    <div
      v-if="isOpen"
      class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4 backdrop-blur-xs"
      @click.self="closeModal"
    >
      <!-- Fixed Modal Card Container (640px x 560px) -->
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="onboarding-title"
        class="modal-card flex h-[560px] w-full max-w-[640px] flex-col overflow-hidden rounded-2xl bg-white shadow-2xl"
      >
        <!-- 1. Header Bar (Close Button) -->
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

        <!-- 2. Animated Slide Content Area -->
        <div class="relative flex-1 overflow-hidden px-10">
          <Transition :name="transitionName" mode="out-in">
            <div :key="activeSlide" class="flex h-full flex-col">
              <!-- SLIDE 1: Intro Layout (Logo, Title, Description, Disclaimer Box) -->
              <template v-if="currentSlide.type === 'intro'">
                <div class="flex h-[155px] shrink-0 items-center justify-center">
                  <img
                    :src="logoUrl"
                    alt="WindBlick Visualization"
                    class="h-40 w-auto object-contain"
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

              <!-- SLIDES 2–4: Step Layout (Preview Image, Title, Description) -->
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
          </Transition>
        </div>

        <!-- 3. Footer Navigation Bar -->
        <div class="grid h-[76px] shrink-0 grid-cols-3 items-center border-t border-slate-100 px-9">
          <!-- Footer Left: "Skip intro" (Slides 1–3) / "Don't show again" Checkbox (Slide 4) -->
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

          <!-- Footer Center: Slide Progress Dots -->
          <div class="flex items-center gap-2 justify-self-center">
            <button
              v-for="(_, index) in slides"
              :key="index"
              type="button"
              :aria-label="`Go to slide ${index + 1}`"
              class="h-2 rounded-full transition-all duration-200"
              :class="
                activeSlide === index
                  ? 'w-5 bg-[#14532D]'
                  : 'w-2 bg-[#9FD3B0] hover:bg-[#14532D]/50'
              "
              @click="goToSlide(index)"
            />
          </div>

          <!-- Footer Right: "Back" & "Next" / "Start upload" Buttons -->
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
  </Transition>
</template>

<style scoped>
/* Forward slide transition (Next): current leaves left, next enters from right */
.slide-next-enter-active,
.slide-prev-enter-active {
  transition: opacity 0.22s cubic-bezier(0.22, 1, 0.36, 1),
    transform 0.22s cubic-bezier(0.22, 1, 0.36, 1);
}

.slide-next-leave-active,
.slide-prev-leave-active {
  transition: opacity 0.16s ease-in, transform 0.16s ease-in;
}

.slide-next-enter-from {
  opacity: 0;
  transform: translateX(28px);
}
.slide-next-leave-to {
  opacity: 0;
  transform: translateX(-28px);
}

/* Backward slide transition (Back): current leaves right, previous enters from left */
.slide-prev-enter-from {
  opacity: 0;
  transform: translateX(-28px);
}
.slide-prev-leave-to {
  opacity: 0;
  transform: translateX(28px);
}

/* Modal backdrop & card open/close animation */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}
.modal-enter-active .modal-card,
.modal-leave-active .modal-card {
  transition: transform 0.2s cubic-bezier(0.22, 1, 0.36, 1), opacity 0.2s ease;
}
.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
.modal-enter-from .modal-card,
.modal-leave-to .modal-card {
  opacity: 0;
  transform: scale(0.96) translateY(8px);
}
</style>