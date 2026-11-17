<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import AppIcon from '../AppIcon.vue'
import {
  motionSensorNote,
  phoneSettings,
  recommendedFootnote,
  recommendedValues,
  sensorNote,
  suitablePhotos,
  transferTips,
} from '../../content/photoTips'

/**
 * Pop-up card explaining suitable photos, phone camera settings and
 * recommended camera values (issue #47).
 */
export type TipsTab = 'photos' | 'settings' | 'values'

const props = withDefaults(defineProps<{ initialTab?: TipsTab }>(), { initialTab: 'photos' })
const emit = defineEmits<{ close: [] }>()

const tabs: { id: TipsTab; label: string }[] = [
  { id: 'photos', label: 'Suitable photos' },
  { id: 'settings', label: 'Phone settings' },
  { id: 'values', label: 'Recommended values' },
]
const tab = ref<TipsTab>(props.initialTab)

// Preselect the visitor's platform when it is obvious; both stay one click away.
const os = ref<'ios' | 'android'>(/iPhone|iPad|iPod|Macintosh/i.test(navigator.userAgent) ? 'ios' : 'android')

const dialog = ref<HTMLElement | null>(null)

function onKey(e: KeyboardEvent) {
  if (e.key === 'Escape') emit('close')
}

function onTabKey(e: KeyboardEvent, i: number) {
  const dir = e.key === 'ArrowRight' ? 1 : e.key === 'ArrowLeft' ? -1 : 0
  if (!dir) return
  e.preventDefault()
  const next = tabs[(i + dir + tabs.length) % tabs.length]!
  tab.value = next.id
  nextTick(() => document.getElementById(`tips-tab-${next.id}`)?.focus())
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
    <div class="backdrop" @click.self="emit('close')">
      <div ref="dialog" class="modal" role="dialog" aria-modal="true" aria-labelledby="tips-title" tabindex="-1">
        <header class="modal__head">
          <h2 id="tips-title">Photos &amp; camera settings</h2>
          <button type="button" class="close" aria-label="Close" @click="emit('close')">
            <AppIcon name="close" :size="20" />
          </button>
        </header>

        <div class="tabs" role="tablist" aria-label="Topics">
          <button
            v-for="(t, i) in tabs"
            :id="`tips-tab-${t.id}`"
            :key="t.id"
            type="button"
            role="tab"
            class="tab"
            :class="{ 'tab--active': tab === t.id }"
            :aria-selected="tab === t.id"
            :aria-controls="`tips-panel-${t.id}`"
            :tabindex="tab === t.id ? 0 : -1"
            @click="tab = t.id"
            @keydown="onTabKey($event, i)"
          >
            {{ t.label }}
          </button>
        </div>

        <div class="modal__body">
          <!-- 1. Suitable photos -->
          <section v-if="tab === 'photos'" id="tips-panel-photos" role="tabpanel" aria-labelledby="tips-tab-photos">
            <p class="lead">{{ suitablePhotos.intro }}</p>
            <ul class="checklist">
              <li v-for="item in suitablePhotos.items" :key="item.text" :class="item.ok ? 'is-ok' : 'is-bad'">
                <span class="mark" aria-hidden="true">{{ item.ok ? '✓' : '✕' }}</span>
                <span><span class="visually-hidden">{{ item.ok ? 'Suitable: ' : 'Not suitable: ' }}</span>{{ item.text }}</span>
              </li>
            </ul>
            <h3>Getting the original file onto your computer</h3>
            <ul class="plain">
              <li v-for="t in transferTips" :key="t">{{ t }}</li>
            </ul>
            <p class="note"><AppIcon name="info" :size="16" /> {{ suitablePhotos.check }}</p>
          </section>

          <!-- 2. Phone settings -->
          <section v-else-if="tab === 'settings'" id="tips-panel-settings" role="tabpanel" aria-labelledby="tips-tab-settings">
            <p class="lead">{{ sensorNote }}</p>
            <div class="os" role="radiogroup" aria-label="Phone type">
              <button type="button" role="radio" :aria-checked="os === 'ios'" :class="{ 'os--active': os === 'ios' }" @click="os = 'ios'">
                iPhone (iOS)
              </button>
              <button
                type="button"
                role="radio"
                :aria-checked="os === 'android'"
                :class="{ 'os--active': os === 'android' }"
                @click="os = 'android'"
              >
                Android
              </button>
            </div>
            <ol class="steps">
              <li v-for="s in phoneSettings[os]" :key="s.title">
                <strong>{{ s.title }}</strong>
                <span class="path">{{ s.path }}</span>
                <span class="why">{{ s.why }}</span>
              </li>
            </ol>
            <p class="note">
              <AppIcon name="info" :size="16" />
              <span><strong>{{ motionSensorNote.title }}:</strong> {{ motionSensorNote.text }}</span>
            </p>
          </section>

          <!-- 3. Recommended values -->
          <section v-else id="tips-panel-values" role="tabpanel" aria-labelledby="tips-tab-values">
            <p class="lead">If a value cannot be read from your photo, start with these and adjust after the first preview.</p>
            <table class="values">
              <thead>
                <tr>
                  <th scope="col">Value</th>
                  <th scope="col">Recommended</th>
                  <th scope="col">Why</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="v in recommendedValues" :key="v.name">
                  <th scope="row">{{ v.name }}</th>
                  <td class="values__value">{{ v.value }}</td>
                  <td class="values__note">{{ v.note }}</td>
                </tr>
              </tbody>
            </table>
            <p class="note"><AppIcon name="info" :size="16" /> {{ recommendedFootnote }}</p>
          </section>
        </div>

        <footer class="modal__foot">
          <button type="button" class="btn btn-primary" @click="emit('close')">Got it</button>
        </footer>
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
  /* minmax(0, 1fr): never let wide content (tabs, tables) push the card past the screen */
  grid-template-columns: minmax(0, 1fr);
  place-items: center;
  padding: 16px;
  background: rgba(100, 110, 130, 0.45);
  animation: fade-in 0.2s ease;
}
.modal {
  display: flex;
  flex-direction: column;
  width: min(720px, 100%);
  max-height: calc(100vh - 32px);
  background: var(--surface);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-modal);
  animation: pop-in 0.25s cubic-bezier(0.2, 0.9, 0.3, 1.2);
}
.modal:focus {
  outline: none;
}
/* only the body scrolls; header, tabs and footer keep their natural height */
.modal__head,
.tabs,
.modal__foot {
  flex: none;
}
.modal__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px 28px 8px;
}
.modal__head h2 {
  font-size: 22px;
  font-weight: 700;
}
.close {
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
.close:hover {
  background: var(--surface-muted);
  color: var(--ink-900);
}
.tabs {
  display: flex;
  gap: 4px;
  padding: 8px 28px 0;
  border-bottom: 1px solid var(--border);
  overflow-x: auto;
}
.tab {
  padding: 10px 14px;
  border: 0;
  border-bottom: 3px solid transparent;
  background: none;
  font-size: 14px;
  font-weight: 500;
  color: var(--ink-500);
  white-space: nowrap;
  cursor: pointer;
}
.tab:hover {
  color: var(--ink-900);
}
.tab--active {
  color: var(--green-900);
  border-bottom-color: var(--green-900);
  font-weight: 600;
}
.tab:focus-visible {
  outline: 3px solid var(--green-300);
  outline-offset: -3px;
}
.modal__body {
  padding: 20px 28px;
  overflow-y: auto;
  font-size: 14px;
  line-height: 1.55;
  color: var(--ink-700);
}
.modal__body h3 {
  margin: 20px 0 8px;
  font-size: 15px;
  font-weight: 600;
  color: var(--ink-900);
}
.lead {
  margin-bottom: 16px;
  color: var(--ink-700);
}
.checklist,
.plain,
.steps {
  margin: 0;
  padding: 0;
}
.checklist {
  list-style: none;
  display: grid;
  gap: 8px;
}
.checklist li {
  display: flex;
  gap: 10px;
  align-items: flex-start;
}
.mark {
  flex: none;
  display: grid;
  place-items: center;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  font-size: 12px;
  font-weight: 700;
}
.is-ok .mark {
  background: var(--green-100);
  color: var(--green-900);
}
.is-bad .mark {
  background: #fde8e6;
  color: var(--danger);
}
.plain {
  padding-left: 20px;
}
.plain li + li {
  margin-top: 4px;
}
.note {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  margin-top: 16px;
  padding: 12px 14px;
  border-radius: var(--radius);
  background: var(--surface-muted);
  font-size: 13px;
}
.note svg {
  flex: none;
  margin-top: 2px;
  color: var(--green-900);
}
.os {
  display: inline-flex;
  padding: 3px;
  margin-bottom: 16px;
  border-radius: var(--radius);
  background: var(--surface-muted);
  border: 1px solid var(--border);
}
.os button {
  padding: 6px 16px;
  border: 0;
  border-radius: var(--radius-sm);
  background: none;
  font-size: 13px;
  font-weight: 500;
  color: var(--ink-700);
  cursor: pointer;
}
.os .os--active {
  background: var(--surface);
  color: var(--green-900);
  font-weight: 600;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.08);
}
.steps {
  list-style: none;
  counter-reset: step;
  display: grid;
  gap: 12px;
}
.steps li {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding-left: 36px;
  counter-increment: step;
}
.steps li::before {
  content: counter(step);
  position: absolute;
  left: 0;
  top: 0;
  display: grid;
  place-items: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--green-900);
  color: #fff;
  font-size: 12px;
  font-weight: 600;
}
.steps strong {
  color: var(--ink-900);
}
.path {
  font-size: 13px;
  color: var(--ink-900);
  background: var(--green-50);
  border-radius: var(--radius-sm);
  padding: 4px 8px;
  align-self: flex-start;
}
.why {
  font-size: 12px;
  color: var(--ink-500);
}
.values {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.values th,
.values td {
  padding: 10px 8px;
  border-bottom: 1px solid var(--border);
  text-align: left;
  vertical-align: top;
}
.values thead th {
  font-size: 12px;
  font-weight: 500;
  color: var(--ink-500);
}
.values tbody th {
  font-weight: 600;
  color: var(--ink-900);
  white-space: nowrap;
}
.values__value {
  font-weight: 600;
  color: var(--green-900);
  white-space: nowrap;
}
.values__note {
  color: var(--ink-700);
}
.modal__foot {
  display: flex;
  justify-content: flex-end;
  padding: 16px 28px 20px;
  border-top: 1px solid var(--border);
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
  .modal__head,
  .tabs,
  .modal__body,
  .modal__foot {
    padding-left: 16px;
    padding-right: 16px;
  }
  .tabs {
    gap: 0;
    scrollbar-width: none;
  }
  .tab {
    flex: 1;
    padding: 10px 4px;
    font-size: 13px;
    white-space: normal;
    line-height: 1.25;
  }
  .values,
  .values tbody {
    display: block;
  }
  .values thead {
    display: none;
  }
  .values tr {
    display: grid;
    min-width: 0;
    padding: 8px 0;
    border-bottom: 1px solid var(--border);
  }
  .values th,
  .values td {
    padding: 2px 0;
    border: 0;
    white-space: normal;
  }
}
</style>
