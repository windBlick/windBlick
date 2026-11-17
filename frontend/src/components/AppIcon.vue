<script setup lang="ts">
/** Small inline icon set (stroke icons, 24×24 grid). */
export type IconName =
  | 'upload'
  | 'info'
  | 'warning'
  | 'trash'
  | 'arrow-left'
  | 'arrow-right'
  | 'download'
  | 'close'
  | 'camera'
  | 'check'
  | 'chevrons'
  | 'turbine'
  | 'cursor'

withDefaults(defineProps<{ name: IconName; size?: number }>(), { size: 18 })
</script>

<template>
  <svg
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.8"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
    focusable="false"
  >
    <template v-if="name === 'upload'">
      <path d="M12 15V4" />
      <path d="m7.5 8.5 4.5-4.5 4.5 4.5" />
      <path d="M4 15v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3" />
    </template>
    <template v-else-if="name === 'info'">
      <circle cx="12" cy="12" r="9" />
      <path d="M12 11v5" />
      <path d="M12 7.5h.01" />
    </template>
    <template v-else-if="name === 'warning'">
      <path d="M10.3 3.9 2.6 17.5A2 2 0 0 0 4.3 20.5h15.4a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z" />
      <path d="M12 9v4.5" />
      <path d="M12 17h.01" />
    </template>
    <template v-else-if="name === 'trash'">
      <path d="M4 7h16" />
      <path d="M9 7V4.5h6V7" />
      <path d="M6.5 7l1 13h9l1-13" />
      <path d="M10 11v6M14 11v6" />
    </template>
    <template v-else-if="name === 'arrow-left'">
      <path d="M19 12H5" />
      <path d="m11 6-6 6 6 6" />
    </template>
    <template v-else-if="name === 'arrow-right'">
      <path d="M5 12h14" />
      <path d="m13 6 6 6-6 6" />
    </template>
    <template v-else-if="name === 'download'">
      <path d="M12 4v11" />
      <path d="m7.5 10.5 4.5 4.5 4.5-4.5" />
      <path d="M4 20h16" />
    </template>
    <template v-else-if="name === 'close'">
      <path d="M6 6l12 12M18 6 6 18" />
    </template>
    <template v-else-if="name === 'camera'">
      <path d="M4 8.5A1.5 1.5 0 0 1 5.5 7H8l1.5-2h5L16 7h2.5A1.5 1.5 0 0 1 20 8.5v9a1.5 1.5 0 0 1-1.5 1.5h-13A1.5 1.5 0 0 1 4 17.5Z" />
      <circle cx="12" cy="13" r="3.2" />
    </template>
    <template v-else-if="name === 'check'">
      <path d="m5 12.5 4.5 4.5L19 7.5" />
    </template>
    <template v-else-if="name === 'chevrons'">
      <path d="m9 7-5 5 5 5" />
      <path d="m15 7 5 5-5 5" />
    </template>
    <template v-else-if="name === 'turbine'">
      <path d="M12 12v9" />
      <path d="M12 12 12 3" />
      <path d="M12 12l7.8 4.5" />
      <path d="M12 12l-7.8 4.5" />
      <circle cx="12" cy="12" r="1.3" fill="currentColor" />
    </template>
    <template v-else-if="name === 'cursor'">
      <path d="M5 5l6 15 2.2-6.3L19.5 11.5Z" />
    </template>
  </svg>
</template>
