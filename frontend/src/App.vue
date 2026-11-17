<script setup lang="ts">
import { onMounted, ref } from 'vue'
import AppHeader from './components/AppHeader.vue'
import AppFooter from './components/AppFooter.vue'
import StepIndicator from './components/StepIndicator.vue'
import IntroModal from './components/intro/IntroModal.vue'

const INTRO_KEY = 'windblick.introHidden'
const introOpen = ref(false)

onMounted(() => {
  let hidden = false
  try {
    hidden = localStorage.getItem(INTRO_KEY) === '1'
  } catch {
    /* storage unavailable */
  }
  introOpen.value = !hidden
})

function onIntroClose(dontShowAgain: boolean) {
  introOpen.value = false
  try {
    if (dontShowAgain) localStorage.setItem(INTRO_KEY, '1')
  } catch {
    /* storage unavailable */
  }
}
</script>

<template>
  <AppHeader @how-it-works="introOpen = true" />
  <main class="page">
    <StepIndicator />
    <RouterView v-slot="{ Component }">
      <Transition name="fade" mode="out-in">
        <component :is="Component" />
      </Transition>
    </RouterView>
  </main>
  <AppFooter />
  <IntroModal v-if="introOpen" @close="onIntroClose" />
</template>

<style>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
}
.fade-enter-from {
  opacity: 0;
  transform: translateY(6px);
}
.fade-leave-to {
  opacity: 0;
}
</style>
