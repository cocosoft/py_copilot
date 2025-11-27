import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // 将所有以/api开头的请求转发到后端服务器
      '/api': {
        target: 'http://localhost:8000', // 后端实际运行在8000端口
        changeOrigin: true,
        secure: false,
      }
    }
  }
})