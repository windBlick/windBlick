<script setup lang="ts">
import { ref } from 'vue'
import AppIcon from '../AppIcon.vue'

/**
 * Before/after comparison: the original photo on the left, the backend-rendered
 * image on the right. Both are shown upright (the browser and the backend each
 * apply the EXIF orientation once), so they line up pixel for pixel.
 */
defineProps<{ originalUrl: string; renderedUrl: string; width: number; height: number }>()

const pos = ref(50)
const frame = ref<HTMLDivElement | null>(null)
let dragging = false

function setFromEvent(e: PointerEvent) {
  const r = frame.value!.getBoundingClientRect()
  pos.value = Math.min(100, Math.max(0, ((e.clientX - r.left) / r.width) * 100))
}
function onDown(e: PointerEvent) {
  dragging = true
  frame.value!.setPointerCapture(e.pointerId)
  setFromEvent(e)
}
function onMove(e: PointerEvent) {
  if (dragging) setFromEvent(e)
}
function onUp() {
  dragging = false
}
function onKey(e: KeyboardEvent) {
  const step = e.shiftKey ? 10 : 2
  if (e.key === 'ArrowLeft') pos.value = Math.max(0, pos.value - step)
  else if (e.key === 'ArrowRight') pos.value = Math.min(100, pos.value + step)
  else if (e.key === 'Home') pos.value = 0
  else if (e.key === 'End') pos.value = 100
  else return
  e.preventDefault()
}
</script>

<template>
  <div
    ref="frame"
    class="frame"
    :style="{
      '--pos': `${pos}%`,
      aspectRatio: `${width} / ${height}`,
      width: `min(100%, calc(75vh * ${width} / ${height}))`,
    }"
    @pointerdown="onDown"
    @pointermove="onMove"
    @pointerup="onUp"
    @pointercancel="onUp"
  >
    <img class="photo" :src="originalUrl" alt="Your original photo" draggable="false" />
    <img class="photo after" :src="renderedUrl" alt="Photo with calculated turbine outlines" draggable="false" />

    <span class="tag tag--l">Original</span>
    <span class="tag tag--r">Simulated view</span>

    <div class="divider" aria-hidden="true" />
    <button
      type="button"
      class="handle"
      role="slider"
      aria-label="Compare original and simulated view"
      aria-valuemin="0"
      aria-valuemax="100"
      :aria-valuenow="Math.round(pos)"
      @keydown="onKey"
    >
      <AppIcon name="chevrons" :size="18" />
    </button>
  </div>
</template>

<style scoped>
.frame {
  position: relative;
  margin-inline: auto;
  border-radius: var(--radius-lg);
  overflow: hidden;
  cursor: ew-resize;
  touch-action: none;
  user-select: none;
  background: #dfe5dc;
}
.photo {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: contain;
  display: block;
}
.after {
  clip-path: inset(0 0 0 var(--pos));
}
.tag {
  position: absolute;
  top: 16px;
  padding: 6px 14px;
  border-radius: 999px;
  background: #fff;
  font-size: 12px;
  font-weight: 600;
  pointer-events: none;
}
.tag--l {
  left: 16px;
}
.tag--r {
  right: 16px;
}
.divider {
  position: absolute;
  top: 0;
  bottom: 0;
  left: var(--pos);
  width: 2px;
  background: #fff;
  transform: translateX(-1px);
  pointer-events: none;
}
.handle {
  position: absolute;
  top: 50%;
  left: var(--pos);
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  padding: 0;
  border-radius: 50%;
  border: 3px solid #fff;
  background: var(--green-900);
  color: #fff;
  transform: translate(-50%, -50%);
  cursor: ew-resize;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25);
}
.handle:focus-visible {
  outline: 3px solid var(--green-300);
  outline-offset: 2px;
}
</style>
