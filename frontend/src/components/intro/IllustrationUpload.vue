<script setup lang="ts">
import AppIcon from '../AppIcon.vue'
</script>

<template>
  <div class="ill" aria-hidden="true">
    <div class="ill__drop">
      <div class="ill__copy">
        <strong>Drop your original photo here</strong>
        <small>JPG · GPS location &amp; compass data</small>
        <span class="btn btn-primary ill__btn">Select photo</span>
      </div>
      <div class="ill__file">
        <span class="ill__jpg">JPG</span>
        <div>
          <div class="ill__name">IMG_2026.JPG</div>
          <span class="badge badge-success ill__badge">GPS &amp; Compass <AppIcon name="check" :size="12" /></span>
        </div>
        <AppIcon class="ill__cursor" name="cursor" :size="20" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.ill {
  width: 100%;
  padding: 24px 24px 0;
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  background: var(--surface-muted);
  overflow: hidden;
}
.ill__drop {
  position: relative;
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 28px 24px 40px;
  border: 1.5px dashed var(--border-strong);
  border-bottom: 0;
  border-radius: var(--radius) var(--radius) 0 0;
  background: var(--surface);
  text-align: left;
}
.ill__copy {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.ill__copy strong {
  font-size: 18px;
}
.ill__copy small {
  font-size: 12px;
  color: var(--ink-700);
}
.ill__btn {
  align-self: flex-start;
  margin-top: 16px;
  height: 42px;
  font-size: 14px;
  pointer-events: none;
}
.ill__file {
  position: relative;
  align-self: flex-end;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 18px 20px;
  background: var(--surface);
  border-radius: var(--radius-lg);
  box-shadow: 0 10px 30px rgba(17, 24, 39, 0.12);
  transform: rotate(-4deg) translateX(8px);
  animation: drop-in 2.8s ease-in-out infinite;
}
.ill__jpg {
  display: grid;
  place-items: center;
  width: 36px;
  height: 44px;
  border: 1px solid var(--border);
  border-radius: 6px;
  font-size: 10px;
  font-weight: 700;
  color: var(--green-900);
}
.ill__name {
  font-size: 15px;
  font-weight: 500;
  margin-bottom: 8px;
}
.ill__badge {
  border-radius: 999px;
}
.ill__cursor {
  position: absolute;
  right: 6px;
  bottom: -6px;
  transform: rotate(-90deg);
  color: var(--ink-900);
}
@keyframes drop-in {
  0%,
  100% {
    transform: rotate(-4deg) translate(8px, 0);
  }
  50% {
    transform: rotate(-3deg) translate(4px, -6px);
  }
}
@media (max-width: 600px) {
  .ill__drop {
    flex-direction: column;
  }
}
</style>
