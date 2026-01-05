const { app } = require('electron');
const path = require('path');

// 引入所有管理器
const WindowManager = require('./src/window-manager');
const MenuManager = require('./src/menu-manager');
const SystemTray = require('./src/system-tray');
const UpdateManager = require('./src/updater');
const IPCManager = require('./src/ipc-manager');
const AppConfig = require('./src/app-config');

class ElectronApp {
  constructor() {
    this.isDev = process.env.NODE_ENV === 'development';
    this.windowManager = null;
    this.menuManager = null;
    this.systemTray = null;
    this.updateManager = null;
    this.ipcManager = null;

    // 应用配置
    this.config = AppConfig;

    // 应用环境变量配置
    this.config.applyEnvironmentConfig();

    // 验证配置
    this.validateConfig();

    // 初始化应用
    this.init();
  }

  /**
   * 验证配置
   */
  validateConfig() {
    const errors = this.config.validate();
    if (errors.length > 0) {
      console.error('配置验证失败:', errors);
      if (!this.isDev) {
        // 生产模式下退出应用
        app.quit();
      }
    }
  }

  /**
   * 初始化应用
   */
  init() {
    // 设置应用单例锁
    this.setupAppLock();

    // 等待应用准备就绪
    app.whenReady().then(() => {
      this.initializeManagers();
      this.setupAppEvents();
    });

    // 处理命令行参数
    this.handleCommandLine();
  }

  /**
   * 设置应用单例锁
   */
  setupAppLock() {
    const gotTheLock = app.requestSingleInstanceLock();

    if (!gotTheLock) {
      // 另一个实例正在运行，退出当前实例
      app.quit();
    } else {
      app.on('second-instance', () => {
        // 当运行第二个实例时，聚焦到主窗口
        if (this.windowManager && this.windowManager.getMainWindow()) {
          const mainWindow = this.windowManager.getMainWindow();
          if (mainWindow.isMinimized()) mainWindow.restore();
          mainWindow.focus();
        }
      });
    }
  }

  /**
   * 初始化所有管理器
   */
  initializeManagers() {
    try {
      // 初始化窗口管理器
      this.windowManager = new WindowManager();
      this.windowManager.createMainWindow();

      // 初始化菜单管理器
      this.menuManager = new MenuManager(this.windowManager);

      // 初始化IPC管理器
      this.ipcManager = new IPCManager(this.windowManager);
      this.ipcManager.setupIPCHandlers(require('electron').ipcMain);

      // 初始化系统托盘（非开发模式）
      if (!this.isDev) {
        this.systemTray = new SystemTray(this.windowManager);
      }

      // 初始化更新管理器（非开发模式）
      if (!this.isDev) {
        this.updateManager = new UpdateManager(this.windowManager);
      }

      console.log('所有管理器初始化完成');
    } catch (error) {
      console.error('管理器初始化失败:', error);
      app.quit();
    }
  }

  /**
   * 设置应用事件监听
   */
  setupAppEvents() {
    // 应用激活事件
    app.on('activate', () => {
      if (this.windowManager && this.windowManager.getAllWindows().length === 0) {
        this.windowManager.createMainWindow();
      }
    });

    // 所有窗口关闭事件
    app.on('window-all-closed', () => {
      // macOS 应用通常在用户明确退出前保持活跃
      if (process.platform !== 'darwin') {
        this.cleanup();
        app.quit();
      }
    });

    // 应用即将退出事件
    app.on('will-quit', (event) => {
      event.preventDefault();
      this.cleanup();
      app.exit(0);
    });

    // 安全策略违规事件
    app.on('web-contents-created', (event, contents) => {
      contents.on('new-window', (event, navigationUrl) => {
        event.preventDefault();
        const { shell } = require('electron');
        shell.openExternal(navigationUrl);
      });

      contents.on('will-navigate', (event, navigationUrl) => {
        const parsedUrl = new URL(navigationUrl);
        if (parsedUrl.origin !== 'http://localhost:5173' && 
            parsedUrl.origin !== `http://localhost:${this.config.get('dev.port')}`) {
          event.preventDefault();
        }
      });
    });

    // 处理文件打开事件
    app.on('open-file', (event, filePath) => {
      event.preventDefault();
      if (this.windowManager && this.windowManager.getMainWindow()) {
        const mainWindow = this.windowManager.getMainWindow();
        mainWindow.show();
        mainWindow.webContents.send('open-file', filePath);
      }
    });

    // 处理URL打开事件
    app.on('open-url', (event, url) => {
      event.preventDefault();
      if (this.windowManager && this.windowManager.getMainWindow()) {
        const mainWindow = this.windowManager.getMainWindow();
        mainWindow.show();
        mainWindow.webContents.send('open-url', url);
      }
    });
  }

  /**
   * 处理命令行参数
   */
  handleCommandLine() {
    // 设置用户代理
    const userAgent = this.config.get('network.userAgent');
    if (userAgent) {
      app.userAgent = userAgent;
    }

    // 处理开发模式特定设置
    if (this.isDev) {
      // 开发模式下启用热重载
      require('electron-reload')(__dirname, {
        electron: path.join(__dirname, '..', 'node_modules', '.bin', 'electron'),
        hardResetMethod: 'exit'
      });

      // 安装React Developer Tools
      if (process.env.ELECTRON_ENABLE_DEV_TOOLS !== 'false') {
        const { default: installExtension, REACT_DEVELOPER_TOOLS, REDUX_DEVTOOLS } = 
          require('electron-devtools-installer');
        
        installExtension(REACT_DEVELOPER_TOOLS)
          .then((name) => console.log(`已安装扩展: ${name}`))
          .catch((err) => console.log('扩展安装失败:', err));
      }
    }
  }

  /**
   * 清理资源
   */
  cleanup() {
    console.log('正在清理应用资源...');

    try {
      // 清理更新管理器
      if (this.updateManager) {
        this.updateManager.cleanup();
        this.updateManager = null;
      }

      // 清理系统托盘
      if (this.systemTray) {
        this.systemTray.cleanup();
        this.systemTray = null;
      }

      // 清理IPC管理器
      if (this.ipcManager) {
        this.ipcManager.cleanup();
        this.ipcManager = null;
      }

      // 清理窗口管理器
      if (this.windowManager) {
        this.windowManager.cleanup();
        this.windowManager = null;
      }

      // 清理菜单管理器
      this.menuManager = null;

      console.log('应用资源清理完成');
    } catch (error) {
      console.error('清理资源时出错:', error);
    }
  }

  /**
   * 获取主窗口
   */
  getMainWindow() {
    return this.windowManager ? this.windowManager.getMainWindow() : null;
  }

  /**
   * 获取应用配置
   */
  getConfig() {
    return this.config;
  }

  /**
   * 显示关于对话框
   */
  showAboutDialog() {
    const { dialog } = require('electron');
    const mainWindow = this.getMainWindow();
    
    if (mainWindow) {
      dialog.showMessageBox(mainWindow, {
        type: 'info',
        title: '关于 Py Copilot',
        message: 'Py Copilot',
        detail: `版本: ${this.config.get('app.version')}\n构建: ${this.config.get('app.buildNumber')}\n\n一个功能强大的AI助手桌面应用程序。\n\n© 2025 Py Copilot Team`,
        buttons: ['确定'],
        icon: path.join(__dirname, '../frontend/public/app-logo.png')
      });
    }
  }

  /**
   * 重启应用
   */
  restart() {
    app.relaunch();
    app.exit(0);
  }
}

// 创建应用实例
const electronApp = new ElectronApp();

// 导出应用实例（用于调试）
if (this.isDev) {
  global.electronApp = electronApp;
}