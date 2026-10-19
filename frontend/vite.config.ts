import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// 화면은 /api 로만 API를 부른다. API 주소는 여기 한 곳에서 지정한다.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
