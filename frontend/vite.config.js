import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  // 加载环境变量（加载所有以 VITE_ 开头的环境变量）
  const env = loadEnv(mode, process.cwd(), 'VITE_');

  // 直接硬编码后端地址
    const apiBaseUrl = 'http://localhost:8000'
  
  return {
    plugins: [react()],
    build: {
      rollupOptions: {
        output: {
          manualChunks: {
            // React核心库
            'react-vendor': ['react', 'react-dom', 'react-router-dom'],
            // UI库
            'ui-vendor': ['framer-motion', 'reactflow'],
            // 工具库
            'utils-vendor': ['axios', 'classnames'],
            // 图表和可视化
            'charts-vendor': ['d3'],
            // PDF处理
            'pdf-vendor': ['pdfjs-dist'],
            // Markdown渲染
            'markdown-vendor': [
              'react-markdown',
              'remark-gfm',
              'remark-math',
              'rehype-katex',
              'react-syntax-highlighter'
            ],
            // 状态管理
            'state-vendor': ['zustand', '@tanstack/react-query'],
            // 虚拟滚动
            'virtual-vendor': ['@tanstack/react-virtual'],
          }
        }
      },
      chunkSizeWarningLimit: 1000
    },
    server: {
      port: 3000,
      host: '127.0.0.1',  // 强制使用 IPv4，避免 IPv6 连接问题
      proxy: {
        '/api': {
            target: apiBaseUrl,
            changeOrigin: true,
            secure: false,
            timeout: 300000, // 增加超时时间到5分钟，支持批量文件上传
            ws: true, // 启用 WebSocket 代理
            configure: (proxy, options) => {
              // 禁用代理缓冲，确保流式响应能正确传递
              options.onProxyReq = (proxyReq, req, res) => {
                // 添加调试头
                proxyReq.setHeader('X-Proxy-Request', 'true');
              };
              
              options.onProxyRes = (proxyRes, req, res) => {
                // 添加调试头
                res.setHeader('X-Proxy-Response', 'true');
                // 确保流式响应头正确传递
                if (proxyRes.headers['content-type'] === 'text/event-stream') {
                  res.setHeader('Content-Type', 'text/event-stream');
                  res.setHeader('Cache-Control', 'no-cache');
                  res.setHeader('Connection', 'keep-alive');
                  res.setHeader('X-Accel-Buffering', 'no'); // 禁用代理缓冲
                }
              };
              
              options.onError = (err, req, res) => {
                // 确保响应被发送，避免客户端等待超时
                res.writeHead(500, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ error: 'Proxy error', details: err.message }));
              };
            }
          },
        '/logos': {
            target: apiBaseUrl,
            changeOrigin: true,
            secure: false,
            ws: true
          },
        '/categories': {
            target: apiBaseUrl,
            changeOrigin: true,
            secure: false,
            ws: true
          },
        '/capabilities': {
            target: apiBaseUrl,
            changeOrigin: true,
            secure: false,
            ws: true
          }
      }
    }
  }
})