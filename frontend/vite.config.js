import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  // 加载环境变量
  const env = loadEnv(mode, process.cwd(), '');
  
  // 使用环境变量中的API地址，如果没有则使用默认值
  const apiBaseUrl = env.VITE_API_BASE_URL || 'http://localhost:8001';
  
  return {
    plugins: [react()],
    server: {
      proxy: {
        '/api': {
            target: apiBaseUrl,
            changeOrigin: true,
            secure: false
          }
      }
    }
  }
})