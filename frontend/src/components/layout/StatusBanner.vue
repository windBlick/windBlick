<script setup>
import { computed, useSlots } from 'vue'

// ============================================================================
// Props & Emits
// ============================================================================
const props = defineProps({
  variant: {
    type: String,
    default: 'error',
    validator: (value) => ['error', 'warning', 'info'].includes(value)
  },
  title: {
    type: String,
    default: ''
  },
  message: {
    type: String,
    default: ''
  },
  // Accepts plain strings or objects like { path, code, message }
  items: {
    type: Array,
    default: () => []
  },
  dismissible: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['dismiss'])
const slots = useSlots()

// ============================================================================
// Computed Visibility & Variant Styles
// ============================================================================
const hasContent = computed(() => {
  return Boolean(
    props.title ||
      props.message ||
      (props.items && props.items.length > 0) ||
      slots.default
  )
})

const styles = computed(() => {
  switch (props.variant) {
    case 'warning':
      return {
        container: 'border-amber-200 bg-amber-50 text-amber-950',
        icon: 'text-amber-600',
        badge: 'bg-amber-100 text-amber-800',
        closeButton: 'text-amber-700 hover:bg-amber-100'
      }
    case 'info':
      return {
        container: 'border-[#9FD3B0] bg-[#9FD3B0]/20 text-[#14532D]',
        icon: 'text-[#14532D]',
        badge: 'bg-[#9FD3B0]/40 text-[#14532D]',
        closeButton: 'text-[#14532D] hover:bg-[#9FD3B0]/35'
      }
    case 'error':
    default:
      return {
        container: 'border-red-200 bg-red-50 text-red-950',
        icon: 'text-red-600',
        badge: 'bg-red-100 text-red-800',
        closeButton: 'text-red-700 hover:bg-red-100'
      }
  }
})
</script>

<template>
  <!-- Render only when at least one message, title, item, or slot is present -->
  <div
    v-if="hasContent"
    :role="variant === 'error' ? 'alert' : 'status'"
    class="flex w-full items-start gap-3.5 rounded-2xl border p-4 shadow-sm"
    :class="styles.container"
  >
    <!-- 1. Left Status Icon -->
    <div class="mt-0.5 shrink-0" :class="styles.icon">
      <!-- Error Icon -->
      <svg
        v-if="variant === 'error'"
        class="h-5 w-5"
        viewBox="0 0 20 20"
        fill="none"
        stroke="currentColor"
        stroke-width="1.8"
      >
        <circle cx="10" cy="10" r="8" />
        <path stroke-linecap="round" d="M10 6.5v4.5M10 13.5h.01" />
      </svg>

      <!-- Warning Icon -->
      <svg
        v-else-if="variant === 'warning'"
        class="h-5 w-5"
        viewBox="0 0 20 20"
        fill="none"
        stroke="currentColor"
        stroke-width="1.8"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          d="M10 3L2.5 16.5h15L10 3z"
        />
        <path stroke-linecap="round" d="M10 8.5v3.5M10 14.2h.01" />
      </svg>

      <!-- Info / Success Icon -->
      <svg
        v-else
        class="h-5 w-5"
        viewBox="0 0 20 20"
        fill="none"
        stroke="currentColor"
        stroke-width="1.8"
      >
        <circle cx="10" cy="10" r="8" />
        <path stroke-linecap="round" d="M10 9v4.5M10 6.5h.01" />
      </svg>
    </div>

    <!-- 2. Main Message & Optional Detail List -->
    <div class="min-w-0 flex-1 text-sm">
      <p v-if="title" class="font-semibold leading-snug">
        {{ title }}
      </p>

      <p
        v-if="message"
        class="leading-relaxed opacity-90"
        :class="{ 'mt-1': title }"
      >
        {{ message }}
      </p>

      <!-- Optional List of Validation Errors or Backend Warnings -->
      <ul
        v-if="items && items.length > 0"
        class="space-y-1.5"
        :class="{ 'mt-2.5': title || message }"
      >
        <li
          v-for="(item, index) in items"
          :key="index"
          class="flex flex-wrap items-baseline gap-2 leading-snug"
        >
          <template v-if="typeof item === 'string'">
            <span>• {{ item }}</span>
          </template>

          <template v-else>
            <code
              v-if="item.path || item.code"
              class="rounded-md px-1.5 py-0.5 text-xs font-semibold"
              :class="styles.badge"
            >
              {{ item.path || item.code }}
            </code>
            <span>{{ item.message }}</span>
          </template>
        </li>
      </ul>

      <!-- Optional Custom Slot Content -->
      <div v-if="$slots.default" :class="{ 'mt-2': title || message || items.length }">
        <slot />
      </div>
    </div>

    <!-- 3. Optional Dismiss Button -->
    <button
      v-if="dismissible"
      type="button"
      aria-label="Dismiss notification"
      class="-mr-1 -mt-1 shrink-0 rounded-lg p-1.5 transition"
      :class="styles.closeButton"
      @click="$emit('dismiss')"
    >
      <svg class="h-4 w-4" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8">
        <path stroke-linecap="round" stroke-linejoin="round" d="M5 5l10 10M15 5L5 15" />
      </svg>
    </button>
  </div>
</template>