<script setup>
defineEmits(['open-onboarding'])
</script>

<template>
  <header class="border-b border-slate-200 bg-white">
    <div class="mx-auto flex h-[70px] max-w-6xl items-center justify-between px-6">
      <div class="flex min-w-0 items-center gap-6">
        <img src="/logo.svg" alt="WindBlick" class="h-14 w-auto shrink-0" />
        <p class="hidden border-l border-slate-200 pl-6 text-slate-600 sm:block">
          Geometric wind turbine preview
        </p>
      </div>

      <button
        type="button"
        class="rounded-xl bg-[#14532D] px-5 py-3 text-sm font-semibold text-white hover:bg-[#14532D]/90"
        @click="$emit('open-onboarding')"
      >
        How it works
      </button>
    </div>
  </header>
</template>
