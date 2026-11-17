<script setup lang="ts">
import type { Point2D, TurbineOutline } from '../../types'

defineProps<{ width: number; height: number; outlines: TurbineOutline[] }>()

const pts = (p: Point2D[]) => p.map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(' ')
</script>

<template>
  <svg class="overlay" :viewBox="`0 0 ${width} ${height}`" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
    <!-- far → near, so nearer turbines and their labels are drawn on top -->
    <g
      v-for="o in outlines.filter((x) => x.inView).sort((a, b) => b.distanceMeters - a.distanceMeters)"
      :key="o.turbineId"
      class="turbine"
    >
      <polygon :points="pts(o.tower)" />
      <polygon v-for="(b, i) in o.blades" :key="i" :points="pts(b)" />
      <circle :cx="o.hub.center[0]" :cy="o.hub.center[1]" :r="o.hub.radius" />
      <foreignObject
        :x="o.labelAnchor[0] - 100"
        :y="o.labelAnchor[1] + height * 0.012"
        width="200"
        :height="height * 0.06"
      >
        <div class="label" :style="{ fontSize: `${height * 0.026}px` }">{{ o.label }}</div>
      </foreignObject>
    </g>
  </svg>
</template>

<style scoped>
.overlay {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}
.turbine polygon,
.turbine circle {
  fill: rgba(255, 255, 255, 0.82);
  stroke: var(--green-900);
  stroke-width: 2.5;
  vector-effect: non-scaling-stroke;
  stroke-linejoin: round;
}
.label {
  width: max-content;
  margin: 0 auto;
  padding: 0.25em 0.6em;
  border-radius: 0.25em;
  background: var(--green-900);
  color: #fff;
  font-weight: 600;
  line-height: 1.2;
}
</style>
