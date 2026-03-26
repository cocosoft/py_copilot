import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import { visualizer } from 'rollup-plugin-visualizer'
import { resolve } from 'path'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  // 加载环境变量（加载所有以 VITE_ 开头的环境变量）
  const env = loadEnv(mode, process.cwd(), 'VITE_');

  // 直接硬编码后端地址
    const apiBaseUrl = 'http://localhost:8020'
  
  return {
    plugins: [
      react({
        // 启用Fast Refresh
        fastRefresh: true,
        // 优化Babel配置
        babel: {
          // 启用自动运行时
          plugins: ['@babel/plugin-transform-runtime']
        }
      }),
      // 构建分析工具
      visualizer({
        open: false,
        filename: 'dist/stats.html',
        gzipSize: true,
        brotliSize: true
      })
    ],
    resolve: {
      // 别名配置
      alias: {
        '@': resolve(__dirname, 'src'),
        '@components': resolve(__dirname, 'src/components'),
        '@pages': resolve(__dirname, 'src/pages'),
        '@services': resolve(__dirname, 'src/services'),
        '@utils': resolve(__dirname, 'src/utils'),
        '@stores': resolve(__dirname, 'src/stores'),
        '@hooks': resolve(__dirname, 'src/hooks'),
        '@assets': resolve(__dirname, 'src/assets'),
        '@contexts': resolve(__dirname, 'src/contexts')
      }
    },
    build: {
      // 构建优化
      minify: 'terser',
      terserOptions: {
        compress: {
          drop_console: mode === 'production',
          drop_debugger: mode === 'production'
        }
      },
      // 启用CSS代码分割
      cssCodeSplit: true,
      // 生成sourcemap
      sourcemap: mode !== 'production',
      // 预加载
      preload: true,
      // 输出目录
      outDir: 'dist',
      // 静态资源目录
      assetsDir: 'assets',
      // 资产文件名哈希
      assetsInlineLimit: 4096, // 4kb以下内联
      // 分块策略
      rollupOptions: {
        output: {
          // 哈希命名
          entryFileNames: 'assets/js/[name].[hash].js',
          chunkFileNames: 'assets/js/[name].[hash].js',
          assetFileNames: 'assets/[ext]/[name].[hash].[ext]',
          // 代码分割策略
          manualChunks: (id) => {
            // 第三方依赖
            if (id.includes('node_modules')) {
              if (id.includes('react') || id.includes('react-dom')) {
                return 'react-vendor';
              } else if (id.includes('framer-motion') || id.includes('reactflow')) {
                return 'ui-vendor';
              } else if (id.includes('axios') || id.includes('classnames')) {
                return 'utils-vendor';
              } else if (id.includes('d3')) {
                return 'charts-vendor';
              } else if (id.includes('pdfjs-dist')) {
                return 'pdf-vendor';
              } else if (id.includes('react-markdown') || id.includes('remark') || id.includes('rehype')) {
                return 'markdown-vendor';
              } else if (id.includes('zustand') || id.includes('@tanstack')) {
                return 'state-vendor';
              } else if (id.includes('i18next')) {
                return 'i18n-vendor';
              } else if (id.includes('react-icons')) {
                return 'icons-vendor';
              }
            }
          }
        },
        // 优化
        plugins: [
          // 树摇
          {
            name: 'tree-shaking',
            transform(code, id) {
              // 移除未使用的代码
              return code;
            }
          }
        ]
      },
      chunkSizeWarningLimit: 1000,
      // 启用持久化缓存
      cacheDir: 'node_modules/.vite'
    },
    server: {
      port: 3000,
      host: '127.0.0.1',  // 强制使用 IPv4，避免 IPv6 连接问题
      // 开发服务器优化
      hmr: {
        // 启用热模块替换
        enabled: true,
        // 热更新路径
        path: '/__hmr',
        // 延迟时间
        timeout: 30000
      },
      // 文件监听
      watch: {
        // 监听文件变化
        usePolling: true,
        // 忽略的文件
        ignored: ['node_modules', 'dist', '*.log'],
        // 防抖时间
        interval: 100,
        // 深度
        depth: 5
      },
      // 优化
      optimizeDeps: {
        // 预构建依赖
        include: [
          'react',
          'react-dom',
          'react-router-dom',
          'axios',
          'zustand',
          'classnames'
        ],
        // 禁用依赖扫描
        disabled: false
      },
      // 预加载
      preTransformRequests: true,
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