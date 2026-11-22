import { createRouter, createWebHistory } from 'vue-router'
import UploadView from '../views/UploadView.vue'
import { useSessionStore } from '../stores/session'

export const steps = [
  { name: 'upload', label: 'Select photo' },
  { name: 'check', label: 'Check photo' },
  { name: 'preview', label: 'View preview' },
] as const

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'upload', component: UploadView },
    {
      path: '/check',
      name: 'check',
      component: () => import('../views/CheckView.vue'),
      meta: { needsPhoto: true },
    },
    {
      path: '/preview',
      name: 'preview',
      component: () => import('../views/PreviewView.vue'),
      meta: { needsPhoto: true },
    },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
  scrollBehavior: () => ({ top: 0 }),
})

router.beforeEach((to) => {
  const session = useSessionStore()
  if (to.meta.needsPhoto && !session.hasPhoto) return { name: 'upload' }
  if (to.name === 'preview' && !session.result) return { name: 'check' }
})

export default router
