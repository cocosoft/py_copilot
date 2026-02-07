import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  // 加载环境变量
  const env = loadEnv(mode, process.cwd(), '');
  
  // 使用环境变量中的API地址，如果没有则使用默认值
  const apiBaseUrl = env.VITE_API_BASE_URL || 'http://127.0.0.1:8007';
  
  return {
    plugins: [react()],
    server: {
      proxy: {
        '/api': {
            target: 'http://localhost:8007',
            changeOrigin: true,
            secure: false,
            timeout: 30000, // 增加超时时间到30秒，适合长连接
            configure: (proxy, options) => {
              // 禁用代理缓冲，确保流式响应能正确传递
              options.onProxyReq = (proxyReq, req, res) => {
                console.log('📤 Sending Request to Target:', req.method, req.url, '→', 'http://localhost:8007' + req.url);
                // 添加调试头
                proxyReq.setHeader('X-Proxy-Request', 'true');
              };
              
              options.onProxyRes = (proxyRes, req, res) => {
                console.log('📥 Received Response from Target:', proxyRes.statusCode, req.url);
                // 添加调试头
                res.setHeader('X-Proxy-Response', 'true');
                // 确保流式响应头正确传递
                if (proxyRes.headers['content-type'] === 'text/event-stream') {
                  console.log('🔄 Streaming response detected');
                  res.setHeader('Content-Type', 'text/event-stream');
                  res.setHeader('Cache-Control', 'no-cache');
                  res.setHeader('Connection', 'keep-alive');
                  res.setHeader('X-Accel-Buffering', 'no'); // 禁用代理缓冲
                }
              };
              
              options.onError = (err, req, res) => {
                console.error('🚨 Proxy Error:', err);
                console.error('🚨 Error details:', JSON.stringify(err, null, 2));
                // 如果连接被重置，可能是目标服务器未启动或端口错误
                if (err.code === 'ECONNRESET') {
                  console.error('🚨 Connection reset by peer - check if backend server is running and accessible');
                } else if (err.code === 'ECONNREFUSED') {
                  console.error('🚨 Connection refused - check if backend server is running on port:', 'http://localhost:8007');
                }
                // 确保响应被发送，避免客户端等待超时
                res.writeHead(500, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ error: 'Proxy error', details: err.message }));
              };
            }
          },
        '/logos': {
            target: 'http://localhost:8007',
            changeOrigin: true,
            secure: false,
            configure: (proxy, options) => {
              proxy.on('error', (err, req, res) => {
                console.log('proxy error', err);
              });
              proxy.on('proxyReq', (proxyReq, req, res) => {
                console.log('Sending Request to the Target:', req.method, req.url);
              });
              proxy.on('proxyRes', (proxyRes, req, res) => {
                console.log('Received Response from the Target:', proxyRes.statusCode, req.url);
              });
            }
          }
      }
    }
  }
})