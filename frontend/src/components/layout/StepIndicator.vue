<script setup>
defineProps({
  currentStep: {
    type: Number,
    required: true,
  },
})

const steps = [
  { number: 1, label: '1. Upload photo' },
  { number: 2, label: '2. Check photo' },
  { number: 3, label: '3. View preview' },
]
</script>

<template>
  <nav aria-label="Progress" class="border-b border-slate-200 bg-slate-50">
    <ol class="mx-auto grid max-w-6xl grid-cols-3 gap-4 px-6 py-6">
      <li v-for="step in steps" :key="step.number" class="flex min-w-0 items-center gap-3">
        <span
          class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-base font-semibold text-white"
          :class="currentStep === step.number ? 'bg-[#14532D]' : 'bg-[#9FD3B0]'"
        >
          {{ step.number }}
        </span>
        <span
          class="whitespace-nowrap text-base sm:text-lg"
          :class="currentStep === step.number ? 'font-semibold text-[#182230]' : 'text-slate-600'"
        >
          {{ step.label }}
        </span>
      </li>
    </ol>
  </nav>
</template>