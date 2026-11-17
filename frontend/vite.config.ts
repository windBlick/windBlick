import vue from '@vitejs/plugin-vue'
import { defineConfig, loadEnv } from 'vite'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  return {
    plugins: [vue()],
    server: {
      // Forward /api to the FastAPI dev server so requests stay same-origin (no CORS setup needed).
      proxy: {
        '/api': { target: env.VITE_BACKEND_URL || 'http://localhost:8000', changeOrigin: true },
      },
    },
  }
})
