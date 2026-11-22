<script setup lang="ts">
import WindBlickLogo from './WindBlickLogo.vue'

defineEmits<{ howItWorks: [] }>()
</script>

<template>
  <header class="header">
    <div class="page header__inner">
      <RouterLink to="/" class="header__brand" aria-label="WindBlick home">
        <WindBlickLogo />
      </RouterLink>
      <span class="header__divider" aria-hidden="true" />
      <span class="header__subtitle">Geometric wind turbine preview</span>
      <button type="button" class="btn btn-primary header__cta" @click="$emit('howItWorks')">
        How it works
      </button>
    </div>
  </header>
</template>

<style scoped>
.header {
  background: var(--surface);
  border-bottom: 1px solid var(--border);
}
.header__inner {
  display: flex;
  align-items: center;
  gap: 24px;
  height: 72px;
}
.header__brand {
  text-decoration: none;
  display: flex;
}
.header__divider {
  width: 1px;
  height: 24px;
  background: var(--border-strong);
}
.header__subtitle {
  font-size: 16px;
  color: var(--ink-700);
}
.header__cta {
  margin-left: auto;
}
@media (max-width: 720px) {
  .header__divider,
  .header__subtitle {
    display: none;
  }
  .header__cta {
    height: 38px;
    padding: 0 14px;
    font-size: 14px;
  }
}
</style>
