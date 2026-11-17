<template>
  <div class="ill" aria-hidden="true">
    <svg class="ill__map" viewBox="0 0 320 220">
      <rect width="320" height="220" fill="#eef0ea" />
      <path d="M200 0 H320 V140 Q260 130 220 160 Q190 180 200 220 H140 Q150 120 200 0Z" fill="#e2ebdc" />
      <g stroke="#ffffff" stroke-width="12" fill="none" stroke-linecap="round">
        <path d="M0 80 Q120 90 320 50" />
        <path d="M70 0 Q110 110 160 220" />
        <path d="M0 175 Q130 110 320 160" />
      </g>
      <g fill="#dfe2db">
        <rect x="116" y="22" width="24" height="30" rx="3" />
        <rect x="250" y="25" width="46" height="22" rx="3" />
        <rect x="255" y="72" width="30" height="18" rx="3" />
        <rect x="26" y="130" width="40" height="26" rx="3" />
        <rect x="190" y="170" width="24" height="32" rx="3" />
      </g>
      <text x="12" y="106" font-size="9" fill="#7b8478">Lindenstraße</text>
      <text x="222" y="196" font-size="9" fill="#7b8478">Stadtpark</text>
      <path class="ill__cone" d="M100 162 L150 52 L232 98 Z" fill="var(--green-300)" opacity="0.45" />
      <line x1="100" y1="162" x2="180" y2="78" stroke="var(--green-900)" stroke-width="1.5" />
      <circle cx="100" cy="162" r="5" fill="var(--green-900)" stroke="#fff" stroke-width="2" />
      <g class="ill__pin" transform="translate(180 78)">
        <path d="M0 0 C-14 -16 -16 -22 -16 -28 A16 16 0 0 1 16 -28 C16 -22 14 -16 0 0Z" fill="var(--green-900)" />
        <g stroke="#fff" stroke-width="1.8" stroke-linecap="round" transform="translate(0 -28)">
          <line x1="0" y1="0" x2="0" y2="-9" /><line x1="0" y1="0" x2="8" y2="4" /><line x1="0" y1="0" x2="-8" y2="4" />
        </g>
      </g>
      <rect x="10" y="12" width="20" height="20" rx="4" fill="#fff" />
      <text x="16" y="26" font-size="10" font-weight="700" fill="var(--ink-900)">N</text>
    </svg>
    <div class="ill__panel">
      <strong>Turbine dimensions</strong>
      <small>Adjust your planned turbine.</small>
      <div class="ill__field"><span>Hub height:</span><b>160 m</b></div>
      <div class="ill__field"><span>Rotor diameter:</span><b>130 m</b></div>
    </div>
  </div>
</template>

<style scoped>
.ill {
  display: grid;
  grid-template-columns: 1.45fr 1fr;
  width: 100%;
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  text-align: left;
}
.ill__map {
  display: block;
  width: 100%;
  height: 100%;
}
.ill__pin {
  animation: bob 2.4s ease-in-out infinite;
}
.ill__panel {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 24px 18px;
  border-left: 1px solid var(--border);
}
.ill__panel strong {
  font-size: 13px;
  font-weight: 600;
}
.ill__panel small {
  font-size: 10px;
  color: var(--ink-700);
  margin-bottom: 12px;
}
.ill__field {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 10px;
  padding: 10px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 13px;
}
.ill__field span {
  font-size: 10px;
  color: var(--ink-700);
}
@keyframes bob {
  0%,
  100% {
    transform: translate(180px, 78px);
  }
  50% {
    transform: translate(180px, 72px);
  }
}
@media (max-width: 600px) {
  .ill {
    grid-template-columns: 1fr;
  }
  .ill__panel {
    border-left: 0;
    border-top: 1px solid var(--border);
  }
}
</style>
