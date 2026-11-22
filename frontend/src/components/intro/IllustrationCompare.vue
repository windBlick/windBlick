<script setup lang="ts">
import AppIcon from '../AppIcon.vue'
</script>

<template>
  <div class="ill" aria-hidden="true">
    <img src="/sample/example_preview_intro_original.JPG" alt="" />
    <div class="ill__after">
      <img src="/sample/example_preview_intro_edited.png" alt="" />
    </div>
    <span class="ill__tag ill__tag--l">Original</span>
    <span class="ill__tag ill__tag--r">Edited preview</span>
    <div class="ill__handle"><AppIcon name="chevrons" :size="16" /></div>
  </div>
</template>

<style scoped>
.ill {
  --pos: 50%;
  position: relative;
  width: min(100%, 460px);
  aspect-ratio: 1160 / 768;
  border-radius: var(--radius-lg);
  overflow: hidden;
  animation: sweep 5s ease-in-out infinite;
}
.ill img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.ill__after {
  position: absolute;
  inset: 0;
  clip-path: inset(0 0 0 var(--pos));
}
.ill__tag {
  padding: 3px 7px;
  border-radius: 4px;
  background: #fff;
  font-size: 10px;
  font-weight: 600;
  color: var(--green-900);
}
.ill__tag {
  position: absolute;
  top: 12px;
  color: var(--ink-900);
}
.ill__tag--l {
  left: 12px;
}
.ill__tag--r {
  right: 12px;
}
.ill__handle {
  position: absolute;
  top: 50%;
  left: var(--pos);
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: #fff;
  border: 2px solid var(--green-900);
  color: var(--green-900);
  transform: translate(-50%, -50%);
}
.ill__handle::before {
  content: '';
  position: absolute;
  left: 50%;
  top: -200px;
  bottom: -200px;
  width: 2px;
  background: #fff;
  z-index: -1;
}
@property --pos {
  syntax: '<percentage>';
  inherits: true;
  initial-value: 50%;
}
@keyframes sweep {
  0%,
  100% {
    --pos: 50%;
  }
  35% {
    --pos: 30%;
  }
  70% {
    --pos: 68%;
  }
}
</style>
