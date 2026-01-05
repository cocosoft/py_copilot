import { defineConfig } from 'cypress';

export default defineConfig({
  e2e: {
    baseUrl: 'http://localhost:3000', // 本地开发环境URL
    viewportWidth: 1280,
    viewportHeight: 720,
    defaultCommandTimeout: 10000, // 10秒超时
    video: true,
    screenshotsFolder: 'cypress/screenshots',
    videosFolder: 'cypress/videos',
    supportFile: 'cypress/support/e2e.js',
    specPattern: 'cypress/e2e/**/*.cy.{js,jsx,ts,tsx}',
    setupNodeEvents(on, config) {
      // 配置Node事件处理程序
      // 例如: 注册任务
      on('task', {
        log(message) {
          console.log(message);
          return null;
        }
      });
      
      return config;
    },
  },
  env: {
    apiUrl: 'http://localhost:8000/api/v1', // 后端API URL
    desktopAppUrl: 'http://localhost:4000', // 桌面应用URL (如果有)
  },
});