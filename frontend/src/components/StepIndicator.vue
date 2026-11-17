<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { steps } from '../router'

const route = useRoute()
const current = computed(() => steps.findIndex((s) => s.name === route.name))
</script>

<template>
  <nav class="steps" aria-label="Progress">
    <ol>
      <li
        v-for="(step, i) in steps"
        :key="step.name"
        class="step"
        :class="{ 'step--active': i === current, 'step--done': i < current }"
        :aria-current="i === current ? 'step' : undefined"
      >
        <span class="step__dot">{{ i + 1 }}</span>
        <span class="step__label">{{ i + 1 }}. {{ step.label }}</span>
      </li>
    </ol>
  </nav>
</template>

<style scoped>
.steps ol {
  list-style: none;
  margin: 0;
  padding: 24px 0;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}
.step {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 18px;
  color: var(--ink-700);
}
.step__dot {
  flex: none;
  display: grid;
  place-items: center;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--green-300);
  color: #fff;
  font-size: 16px;
  font-weight: 500;
  transition: background-color 0.2s;
}
.step--active {
  color: var(--ink-900);
  font-weight: 600;
}
.step--active .step__dot {
  background: var(--green-900);
}
@media (max-width: 720px) {
  .step__label {
    font-size: 14px;
  }
  .step:not(.step--active) .step__label {
    display: none;
  }
  .step__dot {
    width: 32px;
    height: 32px;
    font-size: 14px;
  }
}
</style>
