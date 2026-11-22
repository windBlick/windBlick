<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, useId } from 'vue'

/**
 * WindBlick logo with rotating turbine blades.
 * Artwork from windblick-logo-animated.svg, inlined so it uses the page font
 * and gets unique ids (the logo can appear twice: header + intro pop-up).
 */
withDefaults(defineProps<{ size?: 'sm' | 'lg' }>(), { size: 'sm' })

const uid = useId()
const ids = { iris: `${uid}-iris`, fill: `${uid}-fill`, blade: `${uid}-blade` }

// Respect the OS "reduce motion" setting
const animate = ref(true)
let mq: MediaQueryList | null = null
const sync = () => (animate.value = !mq?.matches)
onMounted(() => {
  mq = window.matchMedia('(prefers-reduced-motion: reduce)')
  sync()
  mq.addEventListener('change', sync)
})
onBeforeUnmount(() => mq?.removeEventListener('change', sync))
</script>

<template>
  <svg
    class="logo"
    :class="`logo--${size}`"
    viewBox="0 0 1060 360"
    role="img"
    aria-label="WindBlick Visualization"
  >
    <defs>
      <clipPath :id="ids.iris">
        <circle cx="256" cy="256" r="100" />
      </clipPath>
      <radialGradient :id="ids.fill" cx="50%" cy="40%" r="65%">
        <stop offset="0%" stop-color="#F1F8F3" />
        <stop offset="100%" stop-color="#D3EBDB" />
      </radialGradient>
      <g :id="ids.blade">
        <path d="M -9 -14 C -14 -52 -8 -90 1 -110 C 6 -84 11 -50 9 -14 Z" />
      </g>
    </defs>

    <g transform="translate(20 0) scale(0.703)">
      <path
        d="M 28 256 Q 256 8 484 256 Q 256 504 28 256 Z"
        fill="#FFFFFF"
        stroke="#14532D"
        stroke-width="22"
        stroke-linejoin="round"
      />
      <circle cx="256" cy="256" r="100" :fill="`url(#${ids.fill})`" />
      <g :clip-path="`url(#${ids.iris})`">
        <path d="M 140 312 Q 200 292 262 306 T 400 300 L 400 400 L 140 400 Z" fill="#9FD3B0" />
        <path d="M 140 334 Q 220 318 300 332 T 400 328 L 400 400 L 140 400 Z" fill="#5FAE7C" />
      </g>
      <circle cx="256" cy="256" r="100" fill="none" stroke="#1E7A46" stroke-width="10" />
      <g transform="translate(256 251) scale(0.84)" fill="#14532D">
        <g>
          <animateTransform
            v-if="animate"
            attributeName="transform"
            type="rotate"
            from="0"
            to="360"
            dur="5s"
            repeatCount="indefinite"
          />
          <use :href="`#${ids.blade}`" />
          <use :href="`#${ids.blade}`" transform="rotate(120)" />
          <use :href="`#${ids.blade}`" transform="rotate(240)" />
        </g>
        <circle r="17" />
        <circle r="6" fill="#FFFFFF" />
      </g>
    </g>

    <text x="400" y="212" class="logo__name" font-size="120" letter-spacing="-2">
      <tspan font-weight="700" fill="#14532D">Wind</tspan><tspan font-weight="400" fill="#1E7A46">Blick</tspan>
    </text>
    <text x="404" y="262" class="logo__tag" font-size="30" font-weight="500" letter-spacing="6" fill="#5FAE7C">
      VISUALIZATION
    </text>
  </svg>
</template>

<style scoped>
.logo {
  display: block;
  width: auto;
  overflow: visible;
}
.logo text {
  font-family: var(--font);
}
.logo--sm {
  height: 64px;
}
@media (max-width: 720px) {
  .logo--sm {
    height: 52px;
  }
}
.logo--lg {
  height: 120px;
  max-width: 100%;
}
</style>
