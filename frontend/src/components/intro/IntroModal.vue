<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import AppIcon from '../AppIcon.vue'
import WindBlickLogo from '../WindBlickLogo.vue'
import IllustrationUpload from './IllustrationUpload.vue'
import IllustrationPlace from './IllustrationPlace.vue'
import IllustrationCompare from './IllustrationCompare.vue'

const emit = defineEmits<{ close: [dontShowAgain: boolean] }>()

const cards = [
  {
    title: 'Visualize planned wind turbines',
    text: 'WindBlick helps you understand the scale of planned wind turbines from your own perspective.',
  },
  {
    title: '1. Upload an original smartphone photo',
    text: 'To calculate the exact perspective, WindBlick reads the hidden GPS location and compass data inside your original JPG file—avoid images sent via WhatsApp.',
  },
  {
    title: '2. Place turbines & set dimensions',
    text: 'Click on the map to set the planned turbine location, verify your viewing direction, and enter hub height and rotor size.',
  },
  {
    title: '3. Compare before and after',
    text: 'Drag the slider to compare your original view with the calculated turbine outlines. Foreground trees or buildings may still obstruct the real view.',
  },
]

const index = ref(0)
const direction = ref<'next' | 'prev'>('next')
const dontShowAgain = ref(false)
const isLast = computed(() => index.value === cards.length - 1)
const dialog = ref<HTMLElement | null>(null)

function go(i: number) {
  direction.value = i > index.value ? 'next' : 'prev'
  index.value = Math.max(0, Math.min(cards.length - 1, i))
}
const close = () => emit('close', dontShowAgain.value)

function onKey(e: KeyboardEvent) {
  if (e.key === 'Escape') close()
  else if (e.key === 'ArrowRight' && !isLast.value) go(index.value + 1)
  else if (e.key === 'ArrowLeft' && index.value > 0) go(index.value - 1)
}

onMounted(async () => {
  document.addEventListener('keydown', onKey)
  document.body.style.overflow = 'hidden'
  await nextTick()
  dialog.value?.focus()
})
onBeforeUnmount(() => {
  document.removeEventListener('keydown', onKey)
  document.body.style.overflow = ''
})
</script>

<template>
  <Teleport to="body">
    <div class="backdrop" @click.self="close">
      <div
        ref="dialog"
        class="modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="intro-title"
        tabindex="-1"
      >
        <button type="button" class="modal__close" aria-label="Close intro" @click="close">
          <AppIcon name="close" :size="20" />
        </button>

        <div class="modal__body">
          <Transition :name="`slide-${direction}`" mode="out-in">
            <div :key="index" class="slide">
              <div class="slide__visual">
                <WindBlickLogo v-if="index === 0" size="lg" />
                <IllustrationUpload v-else-if="index === 1" />
                <IllustrationPlace v-else-if="index === 2" />
                <IllustrationCompare v-else />
              </div>
              <h2 id="intro-title" class="slide__title">{{ cards[index]!.title }}</h2>
              <p class="slide__text">{{ cards[index]!.text }}</p>
              <div v-if="index === 0" class="slide__note">
                <AppIcon name="info" :size="16" />
                <span>Note: This tool provides a geometric orientation, not a photorealistic visualization.</span>
              </div>
            </div>
          </Transition>
        </div>

        <div class="modal__footer">
          <label v-if="isLast" class="dont-show">
            <input v-model="dontShowAgain" type="checkbox" />
            Don’t show again
          </label>
          <button v-else type="button" class="btn btn-ghost" @click="close">Skip intro</button>

          <div class="dots" role="tablist" aria-label="Intro steps">
            <button
              v-for="(_, i) in cards"
              :key="i"
              type="button"
              class="dot"
              :class="{ 'dot--active': i === index }"
              role="tab"
              :aria-selected="i === index"
              :aria-label="`Step ${i + 1} of ${cards.length}`"
              @click="go(i)"
            />
          </div>

          <div class="modal__actions">
            <button v-if="index > 0" type="button" class="btn btn-secondary" @click="go(index - 1)">Back</button>
            <button v-if="!isLast" type="button" class="btn btn-primary" @click="go(index + 1)">
              Next <AppIcon name="arrow-right" :size="16" />
            </button>
            <button v-else type="button" class="btn btn-primary" @click="close">Start upload</button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.backdrop {
  position: fixed;
  inset: 0;
  z-index: 2000;
  display: grid;
  place-items: center;
  padding: 16px;
  background: rgba(100, 110, 130, 0.45);
  animation: fade-in 0.2s ease;
}
.modal {
  position: relative;
  width: min(640px, 100%);
  height: min(600px, calc(100vh - 32px));
  max-height: calc(100vh - 32px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--surface);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-modal);
  animation: pop-in 0.25s cubic-bezier(0.2, 0.9, 0.3, 1.2);
}
.modal:focus {
  outline: none;
}
.modal__close {
  position: absolute;
  top: 18px;
  right: 18px;
  z-index: 1;
  display: grid;
  place-items: center;
  width: 32px;
  height: 32px;
  border: 0;
  border-radius: 50%;
  background: transparent;
  color: var(--ink-500);
  cursor: pointer;
}
.modal__close:hover {
  background: var(--surface-muted);
  color: var(--ink-900);
}
.modal__body {
  flex: 1;
  min-height: 0;
  padding: 48px 40px 24px;
  overflow-y: auto;
}
.slide {
  text-align: center;
}
.slide__visual {
  display: flex;
  justify-content: center;
  min-height: 220px;
  align-items: center;
}
.slide__title {
  margin-top: 28px;
  font-size: 27px;
  font-weight: 700;
  letter-spacing: -0.01em;
}
.slide__text {
  margin: 16px auto 0;
  max-width: 520px;
  font-size: 16px;
  line-height: 1.55;
  color: var(--ink-700);
}
.slide__note {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  margin-top: 32px;
  padding: 18px 20px;
  border-radius: var(--radius);
  background: var(--surface-muted);
  text-align: left;
  font-size: 14px;
  line-height: 1.55;
  color: var(--ink-700);
}
.slide__note svg {
  flex: none;
  margin-top: 2px;
  color: var(--green-900);
}
.modal__footer {
  flex: none;
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  gap: 16px;
  padding: 20px 40px 22px;
  border-top: 1px solid var(--border);
}
.modal__footer > :first-child {
  justify-self: start;
}
.modal__actions {
  justify-self: end;
  display: flex;
  gap: 12px;
}
.dont-show {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  color: var(--ink-700);
  cursor: pointer;
}
.dont-show input {
  width: 16px;
  height: 16px;
  accent-color: var(--green-900);
}
.dots {
  display: flex;
  gap: 4px;
}
.dot {
  width: 16px;
  height: 16px;
  padding: 0;
  border: 0;
  background: transparent;
  cursor: pointer;
  position: relative;
}
.dot::after {
  content: '';
  position: absolute;
  inset: 5px;
  border-radius: 50%;
  background: var(--green-300);
  transition: background-color 0.2s, transform 0.2s;
}
.dot--active::after {
  background: var(--green-900);
  transform: scale(1.15);
}

.slide-next-enter-active,
.slide-next-leave-active,
.slide-prev-enter-active,
.slide-prev-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.slide-next-enter-from,
.slide-prev-leave-to {
  opacity: 0;
  transform: translateX(24px);
}
.slide-next-leave-to,
.slide-prev-enter-from {
  opacity: 0;
  transform: translateX(-24px);
}

@keyframes fade-in {
  from {
    opacity: 0;
  }
}
@keyframes pop-in {
  from {
    opacity: 0;
    transform: translateY(12px) scale(0.98);
  }
}

@media (max-width: 600px) {
  .modal__body {
    padding: 48px 20px 16px;
  }
  .modal__footer {
    grid-template-columns: 1fr auto;
    padding: 16px 20px;
  }
  .dots {
    grid-column: 1 / -1;
    grid-row: 1;
    justify-self: center;
  }
  .slide__title {
    font-size: 22px;
  }
}
</style>
