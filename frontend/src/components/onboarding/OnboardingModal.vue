<script setup>
import { ref } from 'vue'

defineProps({
  isOpen: { type: Boolean, required: true },
})

const emit = defineEmits(['close'])
const activeSlide = ref(0)

const slides = [
  {
    badge: 'Welcome to WindBlick',
    title: 'Visualize planned wind turbines in real landscapes',
    description:
      'See how approved or operating wind turbines in North Rhine-Westphalia look from any viewpoint before or after construction.',
    icon: '🌬️',
  },
  {
    badge: 'Step 1 of 3',
    title: 'Upload an original landscape photo',
    description:
      'Choose a clear outdoor photo taken with your phone or camera. Original files preserve GPS and compass metadata for accurate alignment.',
    icon: '📷',
  },
  {
    badge: 'Step 2 of 3',
    title: 'Verify camera direction & select turbines',
    description:
      'Check or adjust your viewing direction on the map, select turbines from the NRW dataset, and verify their hub height and rotor diameter.',
    icon: '🧭',
  },
  {
    badge: 'Step 3 of 3',
    title: 'Compare original and simulated views',
    description:
      'Use the interactive before-and-after slider to inspect the geometric projection and download your visualization.',
    icon: '✨',
  },
]

function closeModal() {
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
    <div class="w-full max-w-lg rounded-2xl border border-slate-200 bg-white p-6 shadow-xl">
      <div class="flex items-center justify-between">
        <span class="rounded-full bg-[#9FD3B0]/35 px-3 py-1 text-xs font-semibold text-[#14532D]">
          {{ slides[activeSlide].badge }}
        </span>
        <button
          type="button"
          class="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
          @click="closeModal"
        >
          ✕
        </button>
      </div>

      <div class="my-6 text-center">
        <div class="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-[#9FD3B0]/25 text-3xl">
          {{ slides[activeSlide].icon }}
        </div>
        <h2 class="text-xl font-bold text-slate-900">{{ slides[activeSlide].title }}</h2>
        <p class="mt-2.5 text-sm leading-relaxed text-slate-600">
          {{ slides[activeSlide].description }}
        </p>
      </div>

      <!-- Slide-Punkte -->
      <div class="mb-6 flex justify-center gap-2">
        <button
          v-for="(_, idx) in slides"
          :key="idx"
          type="button"
          class="h-2 rounded-full transition-all"
          :class="idx === activeSlide ? 'w-6 bg-[#14532D]' : 'w-2 bg-slate-300'"
          @click="activeSlide = idx"
        />
      </div>

      <!-- Navigation -->
      <div class="flex items-center justify-between border-t border-slate-100 pt-4">
        <button
          v-if="activeSlide > 0"
          type="button"
          class="rounded-xl px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100"
          @click="activeSlide--"
        >
          ← Back
        </button>
        <button
          v-else
          type="button"
          class="rounded-xl px-4 py-2 text-sm font-medium text-slate-400 hover:text-slate-600"
          @click="closeModal"
        >
          Skip
        </button>

        <button
          v-if="activeSlide < slides.length - 1"
          type="button"
          class="rounded-xl bg-[#14532D] px-5 py-2 text-sm font-semibold text-white hover:bg-[#14532D]/90"
          @click="activeSlide++"
        >
          Next →
        </button>
        <button
          v-else
          type="button"
          class="rounded-xl bg-[#14532D] px-5 py-2 text-sm font-semibold text-white hover:bg-[#14532D]/90"
          @click="closeModal"
        >
          Get started
        </button>
      </div>
    </div>
  </div>
</template>