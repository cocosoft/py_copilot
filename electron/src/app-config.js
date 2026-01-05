/**
 * 应用配置文件
 */
const path = require('path');

class AppConfig {
  constructor() {
    this.config = {
      // 应用基本信息
      app: {
        name: 'Py Copilot',
        version: require('../package.json').version,
        buildNumber: process.env.BUILD_NUMBER || '1',
        isDev: process.env.NODE_ENV === 'development',
        isProduction: process.env.NODE_ENV === 'production'
      },

      // 窗口配置
      window: {
        defaultWidth: 1400,
        defaultHeight: 900,
        minWidth: 800,
        minHeight: 600,
        maxWidth: 2560,
        maxHeight: 1440,
        resizable: true,
        center: true,
        show: false, // 先不显示，等加载完成后再显示
        frame: true,
        titleBarStyle: process.platform === 'darwin' ? 'hiddenInset' : 'default',
        backgroundColor: '#ffffff'
      },

      // 安全配置
      security: {
        nodeIntegration: false,
        contextIsolation: true,
        enableRemoteModule: false,
        webSecurity: true,
        allowRunningInsecureContent: false,
        experimentalFeatures: false
      },

      // 文件系统配置
      fileSystem: {
        userDataPath: null, // 将在初始化时设置
        tempPath: null,     // 将在初始化时设置
        documentsPath: null, // 将在初始化时设置
        downloadPath: null,  // 将在初始化时设置
        maxFileSize: 50 * 1024 * 1024, // 50MB
        allowedFileTypes: [
          '.txt', '.md', '.json', '.csv', '.xml', '.yaml', '.yml',
          '.py', '.js', '.ts', '.jsx', '.tsx', '.html', '.css',
          '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
          '.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp'
        ]
      },

      // 网络配置
      network: {
        timeout: 30000, // 30秒
        maxRetries: 3,
        retryDelay: 1000, // 1秒
        userAgent: 'PyCopilot/1.0.0',
        enableProxy: false,
        proxyUrl: null
      },

      // 更新配置
      update: {
        enabled: !process.env.NODE_ENV === 'development',
        checkInterval: 6 * 60 * 60 * 1000, // 6小时
        autoDownload: false,
        autoInstall: true,
        serverUrl: null, // 将在初始化时设置
        channel: 'stable' // stable, beta, alpha
      },

      // 日志配置
      logging: {
        level: process.env.NODE_ENV === 'development' ? 'debug' : 'info',
        maxFileSize: 10 * 1024 * 1024, // 10MB
        maxFiles: 5,
        enableConsole: process.env.NODE_ENV === 'development',
        enableFile: true,
        logPath: null // 将在初始化时设置
      },

      // 性能配置
      performance: {
        enableHardwareAcceleration: true,
        enableVSync: true,
        maxMemoryUsage: 512 * 1024 * 1024, // 512MB
        gcInterval: 5 * 60 * 1000, // 5分钟
        cacheSize: 100 * 1024 * 1024 // 100MB
      },

      // 托盘配置
      tray: {
        enabled: !process.env.NODE_ENV === 'development',
        showNotifications: true,
        minimizeToTray: true,
        closeToTray: true,
        iconPath: null // 将在初始化时设置
      },

      // 开发者配置
      dev: {
        enabled: process.env.NODE_ENV === 'development',
        enableDevTools: true,
        enableDebugMode: false,
        enableHotReload: true,
        autoOpenDevTools: false,
        port: 3000
      }
    };

    this.initializePaths();
  }

  /**
   * 初始化路径配置
   */
  initializePaths() {
    const { app } = require('electron');
    const os = require('os');

    // 设置用户数据路径
    this.config.fileSystem.userDataPath = app.getPath('userData');
    this.config.fileSystem.tempPath = app.getPath('temp');
    this.config.fileSystem.documentsPath = app.getPath('documents');
    this.config.fileSystem.downloadPath = app.getPath('downloads');

    // 设置日志路径
    this.config.logging.logPath = path.join(this.config.fileSystem.userDataPath, 'logs');

    // 设置托盘图标路径
    this.config.tray.iconPath = path.join(__dirname, '../icons/tray-icon.png');

    // 设置更新服务器URL（根据环境）
    if (this.config.app.isDev) {
      this.config.update.serverUrl = 'https://api.github.com/repos/your-username/py-copilot-desktop/releases';
    } else {
      this.config.update.serverUrl = 'https://releases.pycopilot.com';
    }
  }

  /**
   * 获取配置值
   */
  get(path) {
    return this.getNestedValue(this.config, path);
  }

  /**
   * 设置配置值
   */
  set(path, value) {
    this.setNestedValue(this.config, path, value);
  }

  /**
   * 获取嵌套属性值
   */
  getNestedValue(obj, path) {
    return path.split('.').reduce((current, key) => current && current[key], obj);
  }

  /**
   * 设置嵌套属性值
   */
  setNestedValue(obj, path, value) {
    const keys = path.split('.');
    const lastKey = keys.pop();
    const target = keys.reduce((current, key) => {
      if (!current[key]) current[key] = {};
      return current[key];
    }, obj);
    target[lastKey] = value;
  }

  /**
   * 获取应用配置
   */
  getAppConfig() {
    return this.config.app;
  }

  /**
   * 获取窗口配置
   */
  getWindowConfig() {
    return this.config.window;
  }

  /**
   * 获取安全配置
   */
  getSecurityConfig() {
    return this.config.security;
  }

  /**
   * 获取文件系统配置
   */
  getFileSystemConfig() {
    return this.config.fileSystem;
  }

  /**
   * 获取网络配置
   */
  getNetworkConfig() {
    return this.config.network;
  }

  /**
   * 获取更新配置
   */
  getUpdateConfig() {
    return this.config.update;
  }

  /**
   * 获取日志配置
   */
  getLoggingConfig() {
    return this.config.logging;
  }

  /**
   * 获取性能配置
   */
  getPerformanceConfig() {
    return this.config.performance;
  }

  /**
   * 获取托盘配置
   */
  getTrayConfig() {
    return this.config.tray;
  }

  /**
   * 获取开发者配置
   */
  getDevConfig() {
    return this.config.dev;
  }

  /**
   * 验证配置
   */
  validate() {
    const errors = [];

    // 验证必需的配置
    if (!this.config.app.name) {
      errors.push('应用名称不能为空');
    }

    if (!this.config.app.version) {
      errors.push('应用版本不能为空');
    }

    // 验证窗口配置
    if (this.config.window.defaultWidth < this.config.window.minWidth) {
      errors.push('默认宽度不能小于最小宽度');
    }

    if (this.config.window.defaultHeight < this.config.window.minHeight) {
      errors.push('默认高度不能小于最小高度');
    }

    // 验证文件系统配置
    if (!this.config.fileSystem.userDataPath) {
      errors.push('用户数据路径未设置');
    }

    return errors;
  }

  /**
   * 导出配置
   */
  export() {
    return JSON.parse(JSON.stringify(this.config));
  }

  /**
   * 从对象导入配置
   */
  import(configObject) {
    if (typeof configObject === 'object' && configObject !== null) {
      this.config = { ...this.config, ...configObject };
      this.initializePaths();
    }
  }

  /**
   * 重置为默认配置
   */
  reset() {
    this.initializePaths();
  }

  /**
   * 获取环境变量配置
   */
  getEnvironmentConfig() {
    const envConfig = {};

    // 从环境变量获取配置覆盖
    if (process.env.PY_COPILOT_WINDOW_WIDTH) {
      envConfig.window = envConfig.window || {};
      envConfig.window.defaultWidth = parseInt(process.env.PY_COPILOT_WINDOW_WIDTH);
    }

    if (process.env.PY_COPILOT_WINDOW_HEIGHT) {
      envConfig.window = envConfig.window || {};
      envConfig.window.defaultHeight = parseInt(process.env.PY_COPILOT_WINDOW_HEIGHT);
    }

    if (process.env.PY_COPILOT_LOG_LEVEL) {
      envConfig.logging = envConfig.logging || {};
      envConfig.logging.level = process.env.PY_COPILOT_LOG_LEVEL;
    }

    if (process.env.PY_COPILOT_UPDATE_SERVER) {
      envConfig.update = envConfig.update || {};
      envConfig.update.serverUrl = process.env.PY_COPILOT_UPDATE_SERVER;
    }

    return envConfig;
  }

  /**
   * 应用环境变量配置
   */
  applyEnvironmentConfig() {
    const envConfig = this.getEnvironmentConfig();
    this.import(envConfig);
  }
}

// 导出单例实例
const appConfig = new AppConfig();

module.exports = appConfig;