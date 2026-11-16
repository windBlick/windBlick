<script setup>
// ============================================================================
// Props
// ============================================================================
const props = defineProps({
  currentStep: {
    type: Number,
    required: true,
    validator: (val) => [1, 2, 3].includes(val)
  }
})

// ============================================================================
// Step Definitions
// ============================================================================
const steps = [
  { number: 1, title: 'Upload photo', subtitle: 'Original JPG with EXIF' },
  { number: 2, title: 'Place turbines', subtitle: 'Map & dimensions' },
  { number: 3, title: 'Compare view', subtitle: 'Before & after preview' }
]

function getStepState(stepNumber) {
  if (stepNumber < props.currentStep) return 'completed'
  if (stepNumber === props.currentStep) return 'active'
  return 'upcoming'
}
</script>

<template>
  <nav aria-label="Workflow progress" class="border-b border-slate-200/80 bg-white">
    <div class="mx-auto max-w-6xl px-4 py-4 sm:px-6 sm:py-5">
      <!-- Mobile: stacked vertically (flex-col) | Desktop (sm+): horizontal row -->
      <ol class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between sm:gap-4">
        <li
          v-for="(step, index) in steps"
          :key="step.number"
          class="relative flex items-center gap-3.5 sm:flex-1"
        >
          <!-- Step Number / Checkmark Circle -->
          <div
            class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-sm font-bold transition-colors"
            :class="{
              'bg-[#14532D] text-white': getStepState(step.number) === 'active',
              'bg-[#9FD3B0]/45 text-[#14532D]': getStepState(step.number) === 'completed',
              'border border-slate-300 bg-slate-50 text-slate-400':
                getStepState(step.number) === 'upcoming'
            }"
          >
            <!-- Checkmark for completed steps -->
            <svg
              v-if="getStepState(step.number) === 'completed'"
              class="h-4 w-4"
              viewBox="0 0 20 20"
              fill="none"
              stroke="currentColor"
              stroke-width="2.5"
            >
              <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 10.5l3.5 3.5 7.5-7.5" />
            </svg>
            <span v-else>{{ step.number }}</span>
          </div>

          <!-- Step Label & Subtitle -->
          <div class="min-w-0">
            <p
              class="text-sm font-semibold leading-tight"
              :class="
                getStepState(step.number) === 'upcoming' ? 'text-slate-400' : 'text-slate-900'
              "
            >
              {{ step.title }}
            </p>
            <p class="mt-0.5 text-xs text-slate-500">
              {{ step.subtitle }}
            </p>
          </div>

          <!-- Horizontal Connector Line (Desktop only) -->
          <div
            v-if="index < steps.length - 1"
            aria-hidden="true"
            class="ml-2 hidden h-0.5 flex-1 rounded-full sm:block"
            :class="
              step.number < currentStep ? 'bg-[#14532D]' : 'bg-slate-200'
            "
          />
        </li>
      </ol>
    </div>
  </nav>
</template>