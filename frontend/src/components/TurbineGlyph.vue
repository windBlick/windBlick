<script setup lang="ts">
/** Decorative turbine outline used in illustrations (not geometrically projected). */
withDefaults(defineProps<{ height?: number; color?: string }>(), { height: 120, color: 'var(--green-900)' })
</script>

<template>
  <svg :height="height" :width="height * 0.75" viewBox="0 0 90 120" aria-hidden="true">
    <g fill="rgba(255,255,255,0.85)" :stroke="color" stroke-width="1.6" stroke-linejoin="round">
      <path d="M43 40 L47 40 L49 118 L41 118 Z" />
      <path d="M45 40 L43 36 L45 2 L47 36 Z" />
      <path d="M45 40 L48 38 L84 56 L46 44 Z" />
      <path d="M45 40 L42 38 L6 56 L44 44 Z" />
      <circle cx="45" cy="40" r="3" />
    </g>
  </svg>
</template>
